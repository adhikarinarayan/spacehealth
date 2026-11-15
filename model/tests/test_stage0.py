import copy
import math
from collections import defaultdict
import numpy as np
import pytest
from scipy.integrate import trapezoid
from spacehealth_model.config import load_config
from spacehealth_model.baseline.fixed import fit_baselines
from spacehealth_model.sim.generate import generate_mission
from spacehealth_model.sim.radiation import integrate_day, dose_total
from spacehealth_model.modules.physiological import evaluate
from spacehealth_model.export.files import make_indicators, validate_file, encode
from spacehealth_model.run import summary

@pytest.fixture(scope='module')
def config():return load_config()
@pytest.fixture(scope='module')
def mission(config):return generate_mission(0,config)
@pytest.fixture(scope='module')
def indicators(mission,config):return make_indicators(mission,config)

def records(config,values=None):
    values=values if values is not None else [60.0]*14
    return [{'crewId':'C1','missionDay':d,'rhr_bpm':v,'hrv_rmssd_ms':50.0,'skin_temp_delta_c':0.0,'sleep_hours':7.0,'symptoms':[],'checkin_completed':True} for d,v in zip(range(-14,0),values)]

def test_hand_checked_baseline(config):
    b=fit_baselines(records(config,list(range(50,64))),'C1',config)['rhr_bpm']
    assert b.center==56.5
    assert b.scale==pytest.approx(5.1891)
    assert b.count==14

def test_zero_mad_floor(config):
    baselines=fit_baselines(records(config),'C1',config)
    for signal,b in baselines.items():assert b.scale==config['signals'][signal]['min_scale']

def test_insufficient_baseline(config):
    rows=records(config)[:config['rules']['baseline']['min_valid_days']-1]
    rows.append({**records(config)[0],'missionDay':1})
    assert evaluate(rows,'C1',1,config)['status']=='unknown'

def test_invalid_baseline_values_excluded(config):
    rows=records(config)
    for row in rows[:6]:row['rhr_bpm']=float('nan')
    assert fit_baselines(rows,'C1',config)['rhr_bpm'].quality=='insufficient'

def test_all_missing_never_nominal(config):
    rows=records(config)
    rows.append({**rows[0],'missionDay':1,'rhr_bpm':None,'hrv_rmssd_ms':None,'skin_temp_delta_c':None})
    result=evaluate(rows,'C1',1,config)
    assert (result['status'],result['dataQuality'])==('unknown','missing')

def test_plausibility_is_not_a_schema_health_threshold(config):
    rows=records(config)
    rows.append({**rows[0],'missionDay':1,'rhr_bpm':999})
    result=evaluate(rows,'C1',1,config)
    assert result['dataQuality']=='suspect'
    assert 'Implausible' in result['reason']

def test_persistence_and_direction_are_rule_driven(config):
    rows=records(config)
    for day in [1,2]:
        row={**rows[0],'missionDay':day}
        row.update(rhr_bpm=60+config['watch_z']*config['signals']['rhr_bpm']['min_scale']+0.1,
                   skin_temp_delta_c=config['watch_z']*config['signals']['skin_temp_delta_c']['min_scale']+0.01)
        rows.append(row)
    assert evaluate(rows,'C1',1,config)['status']=='nominal'
    result=evaluate(rows,'C1',2,config)
    assert result['status']=='watch'
    assert result['cardId']=='physiological-change'
    assert {e['signalId']:e.get('persistenceDays') for e in result['evidence']}['rhr_bpm']==2
    # A single changed signal, however large, is not the multivariate rule.
    for row in rows:
        if row['missionDay']>0:row['skin_temp_delta_c']=0;row['rhr_bpm']=150
    assert evaluate(rows,'C1',2,config)['status']=='nominal'

def test_strong_rule_and_red_symptom_override(config):
    rows=records(config)
    for day in [1,2]:rows.append({**rows[0],'missionDay':day,'rhr_bpm':70,'skin_temp_delta_c':1})
    assert evaluate(rows,'C1',2,config)['status']=='act'
    red=config['rules']['physiological_change']['symptom_only']['red_flag'][0]
    rows[-1].update(rhr_bpm=None,hrv_rmssd_ms=None,skin_temp_delta_c=None,symptoms=[red])
    result=evaluate(rows,'C1',2,config)
    assert result['status']=='act'
    assert result['cardId']=='symptom-escalation'
    assert result['dataQuality']=='suspect'

def test_no_future_leakage(mission,config):
    d=config['scenarios']['scenarios']['S2']['onsetDay']+1
    before=evaluate(mission['readings'],'C2',d,config)
    changed=copy.deepcopy(mission['readings'])
    for row in changed:
        if row['missionDay']>d:row.update(rhr_bpm=None,skin_temp_delta_c=999,hrv_rmssd_ms=None,symptoms=['fever'])
    assert evaluate(changed,'C2',d,config)==before

def test_simulation_shape_and_provenance(mission,config):
    assert len(mission['crew'])==4
    assert len(mission['readings'])==4*(14+180)
    assert len({(r['crewId'],r['missionDay']) for r in mission['readings']})==len(mission['readings'])
    assert {t['scenarioId'] for t in mission['truth']}==set(config['scenarios']['scenarios'])
    assert all(v=='synthetic' for r in mission['readings'] for v in r['provenance'].values())
    assert all(c['prior_career_dose_msv'] is None for c in mission['crew'])
    assert mission['missionProfile']['gcr_background_msv_day']==config['signals']['daily_dose_msv']['sim_background']

def test_deterministic_seed_and_scenario_toggle(mission,config):
    again=generate_mission(0,config)
    assert again['readings']==mission['readings']
    assert again['radiationEvents']==mission['radiationEvents']
    quiet=generate_mission(0,config,[])
    assert {t['scenarioId'] for t in quiet['truth']}=={'S1'}
    assert not any(e['spe_warning'] for e in quiet['radiationEvents'])
    assert not any(r['symptoms'] for r in quiet['readings'])
    before=lambda m:[r for r in m['readings'] if r['missionDay']<0 and r['crewId']!='C4']
    assert before(quiet)==before(mission)

def test_partial_dose_integration_and_no_imputation():
    rows=[{'timeHoursFromDayStart':t,'dose_rate_msv_h':v} for t,v in [(0,1),(1,3),(2,5),(3,None)]]
    dose,coverage=integrate_day(rows)
    assert dose==6 # analytic integral of (2*t+1) from 0 to 2
    assert coverage==pytest.approx(2/24)
    assert integrate_day([{'timeHoursFromDayStart':0,'dose_rate_msv_h':None}])==(None,0)

def test_dose_matches_independent_integral(mission,config):
    groups=defaultdict(list)
    for event in mission['radiationEvents']:
        if event['crewId']=='C1':groups[event['missionDay']].append(event)
    for r in mission['readings']:
        if r['crewId']!='C1':continue
        samples=groups[r['missionDay']]
        actual=float(trapezoid([e['dose_rate_msv_h'] for e in samples],[e['timeHoursFromDayStart'] for e in samples]))
        assert r['daily_dose_msv']==pytest.approx(actual,abs=1e-6)
    rows=[r for r in mission['readings'] if r['crewId']=='C1' and r['missionDay']>0]
    target=float(config['scenarios']['scenarios']['S3']['event_total_dose_msv'].split()[0])
    background=config['signals']['daily_dose_msv']['sim_background']
    assert dose_total(rows)['observed_mission_dose_msv']==pytest.approx(len(rows)*background+target,abs=1e-6)
    warning=next(e for e in mission['radiationEvents'] if e['spe_warning'])
    assert warning['missionDay']==config['scenarios']['scenarios']['S3']['onsetDay']
    assert warning['timeHoursFromDayStart']==.5

def test_n1_no_act(indicators,config):
    crew=config['scenarios']['scenarios']['N1']['crew']
    rows=[i for i in indicators['indicators'] if i['crewId']==crew and i['moduleId']=='physiological_change']
    assert not any(i['status']=='act' for i in rows)

def test_n2_unknown_and_skipped_checkin(mission,indicators,config):
    rows=[i for i in indicators['indicators'] if i['crewId']=='C4' and i['moduleId']=='physiological_change']
    for day in range(120,125):assert next(i for i in rows if i['missionDay']==day)['status']=='unknown'
    for day in [130,131]:assert 'check-in not collected' in next(i for i in rows if i['missionDay']==day)['reason']
    assert fit_baselines(mission['readings'],'C4',config)['hrv_rmssd_ms'].count==8

def test_forbidden_words_and_placeholder_modules(indicators,config):
    words=config['rules']['physiological_change']['forbidden_words']
    for i in indicators['indicators']:
        assert not any(word.lower() in i['reason'].lower() for word in words)
    from spacehealth_model.contracts import Indicator
    for module in ('sleep_alertness','radiation'):
        rows=[i for i in indicators['indicators'] if i['moduleId']==module]
        assert {(i['crewId'],i['missionDay']) for i in rows}=={(f'C{c}',d) for c in range(1,5) for d in range(1,181)}
        for row in rows:Indicator.model_validate(row)

def test_exports_validate_and_mission_hash_matches(mission,indicators):
    from hashlib import sha256
    validate_file('mission',mission);validate_file('indicators',indicators)
    assert indicators['missionFile']==sha256(encode(mission)).hexdigest()
    assert len(indicators['indicators'])==4*180*3

def test_s2_flag_by_symptom_day(mission,indicators,config):
    result=summary(mission,indicators,config)['S2']
    assert result['passedBySymptomDay'], f'Synthetic S2 acceptance miss with unchanged research values: {result}'
    event=config['scenarios']['scenarios']['S2']
    first=next(i for i in indicators['indicators'] if i['crewId']==event['crew'] and i['moduleId']=='physiological_change' and i['missionDay']==result['firstFlagDay'])
    assert {e['signalId'] for e in first['evidence']}==set(config['rules']['physiological_change']['signals'])
    assert all('direction' in e for e in first['evidence'] if 'info-only' not in e.get('unit',''))

def test_m1_documented_miss(mission,config):
    from spacehealth_model.detectors.candidates import get_detector
    from spacehealth_model.compare import load_stage1
    rows=[r for r in mission['readings'] if r['crewId']=='C2']
    cfg=load_stage1();baseline=fit_baselines(rows,'C2',config)
    results=get_detector('M1').detect(rows,baseline,cfg)
    assert not any(r.status in ('watch','act') for r in results if 40<=r.missionDay<=42)

def test_production_uses_m3_and_m5_info_never_changes_status(mission,config,indicators):
    from spacehealth_model.modules.physiological import production_results
    for crew in mission['crew']:
        rows=[r for r in mission['readings'] if r['crewId']==crew['crewId']]
        prepared=production_results(rows,crew['crewId'],config)
        output=[i for i in indicators['indicators'] if i['crewId']==crew['crewId'] and i['moduleId']=='physiological_change']
        for i in output:
            assert i['status']==prepared[0][i['missionDay']].status
            info=[e for e in i['evidence'] if 'multi-signal agreement' in e.get('unit','')]
            assert len(info)==1 and info[0]['value'] in ('agree','disagree','not evaluable')
