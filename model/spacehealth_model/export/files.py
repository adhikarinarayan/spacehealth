"""Validate model envelopes with Pydantic and local JSON Schemas before writing."""
import json
import copy
from collections import OrderedDict
from hashlib import sha256
from pathlib import Path
from jsonschema import Draft202012Validator, FormatChecker
from referencing import Registry, Resource
from ..config import ROOT
from ..contracts import MODELS, strict_loads
from ..baseline.fixed import fit_baselines
from ..modules.physiological import evaluate_production,production_results
from ..modules.sleep import evaluate as evaluate_sleep
from ..modules.radiation import evaluate as evaluate_radiation

def encode(value):
    return (json.dumps(value,indent=2,allow_nan=False,sort_keys=True)+'\n').encode()

def validate_file(kind,value):
    # Strict round trip guarantees JSON finite-number semantics, including overflow.
    strict_loads(encode(value).decode())
    MODELS[kind].model_validate(value)
    schemas=ROOT/'contracts/schemas'
    registry=Registry().with_resources((d['$id'],Resource.from_contents(d)) for d in (json.loads(p.read_text()) for p in schemas.glob('*.json')))
    schema=json.loads((schemas/f'{kind}.schema.json').read_text())
    Draft202012Validator(schema,registry=registry,format_checker=FormatChecker()).validate(value)
    return value

_RADIATION_CACHE=OrderedDict()
def _radiation_series(readings,events,crew,config):
    # Pure input-content cache: identical dose streams/policy are shared across crew/scenarios.
    content={'readings':[(r['missionDay'],r.get('daily_dose_msv'),r.get('dose_coverage')) for r in readings],
             'events':[(e['missionDay'],e['timeHoursFromDayStart'],e['spe_warning'],e['dose_rate_msv_h']) for e in events],
             'prior':crew['prior_career_dose_msv'],'policy':config['stage']['radiation'],
             'background':config['signals']['daily_dose_msv']['sim_background'],
             'limit':config['signals']['prior_career_dose_msv']['career_limit'],'duration':config['scenarios']['mission']['mission_days']}
    key=sha256(encode(content)).hexdigest()
    if key not in _RADIATION_CACHE:
        low,high=config['scenarios']['mission']['mission_days']
        _RADIATION_CACHE[key]={d:evaluate_radiation(readings,events,crew['crewId'],d,config,prior_career_dose_msv=crew['prior_career_dose_msv']) for d in range(low,high+1)}
        if len(_RADIATION_CACHE)>32:_RADIATION_CACHE.popitem(last=False)
    return {d:{**copy.deepcopy(row),'crewId':crew['crewId']} for d,row in _RADIATION_CACHE[key].items()}

def make_indicators(mission,config):
    result=[]
    for crew in mission['crew']:
        cid=crew['crewId']
        crew_readings=[r for r in mission['readings'] if r['crewId']==cid]
        crew_events=[e for e in mission['radiationEvents'] if e['crewId']==cid]
        baseline=fit_baselines(crew_readings,cid,config)
        prepared=production_results(crew_readings,cid,config,baseline)
        radiation_rows=_radiation_series(crew_readings,crew_events,crew,config)
        first_day,last_day=config['scenarios']['mission']['mission_days']
        for day in range(first_day,last_day+1):
            result.append(evaluate_production(crew_readings,cid,day,config,baseline,prepared))
            result.append(evaluate_sleep(crew_readings,cid,day,config,baseline))
            result.append(radiation_rows[day])
    return {'schemaVersion':'0.2.0','simulated':True,'modelId':'M3-frozen-v1','configHash':config['configHash'],'missionFile':sha256(encode(mission)).hexdigest(),'indicators':result}

def export_files(mission,indicators,out):
    # Validate BOTH files before writing either output.
    for kind,value in [('mission',mission),('indicators',indicators)]:validate_file(kind,value)
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    for name,value in [('mission',mission),('indicators',indicators)]:
        temporary=out/f'.{name}.json.tmp'
        temporary.write_bytes(encode(value));temporary.replace(out/f'{name}.json')


def select_cards(indicators_for_day,config):
    actionable=[i for i in indicators_for_day if i['status'] in ('watch','act') and i.get('cardId')]
    radiation=[i for i in actionable if i['moduleId']=='radiation' and i['status']=='act']
    symptoms=[i for i in actionable if i.get('cardId')=='symptom-escalation' and i not in radiation]
    routine=[i for i in actionable if i not in radiation and i not in symptoms]
    return radiation+symptoms+routine[:config['rules']['card_cap']['routine_max']]
