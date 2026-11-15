"""One-shot frozen protocol. Existing completed results are reused, never recomputed."""
import copy
import csv
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import numpy as np
from .frozen import read_frozen
from .stage2 import bootstrap_ci
from ..config import ROOT
from ..sim.generate import generate_mission
from ..data_sources.donki import timing
from ..modules.radiation import evaluate as radiation
from ..export.files import make_indicators,encode

MODULES=('physiological_change','sleep_alertness','radiation')

def verify_freeze(path,out):
    config,document,digest=read_frozen(path)
    frozen=json.loads((Path(out)/'FREEZE.json').read_text())
    if digest!=frozen['configHash']:raise ValueError('Frozen config hash differs; holdout refused')
    scope_path=ROOT/'model/reports/integration/SCIENCE_SCOPE.json'
    if frozen['codeHashes'] and scope_path.exists() and json.loads(scope_path.read_text())['configHash']==digest:
        from .science_scope import verify_scientific_scope
        verify_scientific_scope(frozen,json.loads(scope_path.read_text()))
    else:
        for relative,expected in frozen['codeHashes'].items():
            if hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()!=expected:raise ValueError(f'Frozen code changed: {relative}')
    for relative,expected in frozen.get('dataHashes',{}).items():
        if hashlib.sha256((ROOT/relative).read_bytes()).hexdigest()!=expected:raise ValueError(f'Frozen dataset changed: {relative}')
    return config,document,digest

def variant_config(config,protocol,seed,factor,noise):
    cfg=copy.deepcopy(config);rng=np.random.default_rng(seed)
    cfg['stage']['simulation']['S2']['rhr_delta_bpm']=float(rng.uniform(*protocol['rhr_delta_bpm_range']))
    for key in ('hrv_delta_sd_range','temperature_delta_sd_range'):
        cfg['stage']['simulation']['S2'][key]=[v*factor for v in config['stage']['simulation']['S2'][key]]
    cfg['stage']['simulation']['noise']={'distribution':noise,'student_t_df':protocol['student_t_df']}
    return cfg

def flagged_episodes(rows):
    total=0;previous=None
    for row in sorted(rows,key=lambda r:r['missionDay']):
        if row['status'] in ('watch','act') and (previous is None or previous['missionDay']!=row['missionDay']-1 or previous['status'] not in ('watch','act')):total+=1
        previous=row
    return total

def false_metrics(items,protocol,module):
    rule=protocol['exclusions'][module]
    eligible=[i for i in items if i['moduleId']==module and not ((rule['crew']=='all' or i['crewId']==rule['crew']) and rule['days'][0]<=i['missionDay']<=rule['days'][1])]
    evaluable=[i for i in eligible if i['status']!='unknown']
    days=sum(i['status'] in ('watch','act') for i in evaluable)
    episodes=sum(flagged_episodes([i for i in eligible if i['crewId']==cid]) for cid in ('C1','C2','C3','C4'))
    return {'false_days':days,'false_episodes':episodes,'evaluable_days':len(evaluable),'days_per100':100*days/len(evaluable) if evaluable else None,'episodes_per100':100*episodes/len(evaluable) if evaluable else None}

def scenario_results(mission,items,config,quiet_acts):
    scenarios=config['scenarios']['scenarios'];results=[]
    def add(sid,cid,module,passed,onset=None,symptom=None,window=None,notes=''):
        selected=[i for i in items if i['crewId']==cid and i['moduleId']==module and (window is None or window[0]<=i['missionDay']<=window[1])]
        watch=next((i['missionDay'] for i in selected if i['status']=='watch'),None);act=next((i['missionDay'] for i in selected if i['status']=='act'),None)
        first=min(x for x in (watch,act) if x is not None) if watch is not None or act is not None else None
        results.append({'scenarioId':sid,'crewId':cid,'moduleId':module,'passed':bool(passed),'passRule':scenarios[sid]['pass'],
          'onsetDay':onset,'symptomDay':symptom,'firstWatchDay':watch,'firstActDay':act,
          'delayVsOnsetDays':first-onset if first is not None and onset is not None else None,'delayVsSymptomDays':first-symptom if first is not None and symptom is not None else None,
          'routineFalseAlerts':0,'evaluableCrewDays':len([i for i in selected if i['status']!='unknown']),'falseAlertsPer100CrewDays':None,'unknownDays':sum(i['status']=='unknown' for i in selected),'notes':notes})
    for cid in ('C1','C2','C3','C4'):add('S1',cid,None,quiet_acts[cid]==0,notes=f'Isolated quiet mission: {quiet_acts[cid]} act indicators; false-watch costs reported separately.')
    s2=scenarios['S2'];window=[s2['onsetDay'],s2['endDay']]
    detected=any(i['crewId']==s2['crew'] and i['moduleId']=='physiological_change' and s2['onsetDay']<=i['missionDay']<=s2['symptomDay'] and i['status'] in ('watch','act') for i in items)
    add('S2',s2['crew'],'physiological_change',detected,s2['onsetDay'],s2['symptomDay'],window)
    mapped,_=timing(config=config)
    for cid in ('C1','C2','C3','C4'):
        rows=[r for r in mission['readings'] if r['crewId']==cid];events=[e for e in mission['radiationEvents'] if e['crewId']==cid]
        onset_results=[]
        total=sum(r['daily_dose_msv'] for r in rows if r['missionDay']>0 and r['daily_dose_msv'] is not None)
        expected=config['scenarios']['mission']['mission_days'][1]*config['signals']['daily_dose_msv']['sim_background']+config['stage']['simulation']['S3']['total_extra_dose_msv']
        dose_ok=abs(total-expected)<1e-6
        for onset in mapped:
            sample=next(e for e in events if e['missionDay']==onset['missionDay'] and abs(e['timeHoursFromDayStart']-onset['timeHoursFromDayStart'])<1e-9)
            item=radiation(rows,events,cid,sample['missionDay'],config,as_of_hour=sample['timeHoursFromDayStart'])
            onset_results.append(item['status']=='act')
        add('S3',cid,'radiation',all(onset_results) and dose_ok,mapped[0]['missionDay'],window=[mapped[0]['missionDay'],87],notes='DONKI onset act checks: '+str(onset_results)+f'; dose total verified: {dose_ok}')
    s4=scenarios['S4'];sleep=[i for i in items if i['crewId']==s4['crew'] and i['moduleId']=='sleep_alertness' and s4['onsetDay']<=i['missionDay']<=s4['endDay']]
    flag=next((i['missionDay'] for i in sleep if i['status'] in ('watch','act')),None)
    add('S4',s4['crew'],'sleep_alertness',flag is not None and flag<=s4['onsetDay']+2,s4['onsetDay'],window=[s4['onsetDay'],s4['endDay']])
    n1days=set(d+offset for d in config['stage']['simulation']['N1']['days'] for offset in range(-2,3))
    n1=[i for i in items if i['crewId']=='C1' and i['moduleId']=='physiological_change' and i['missionDay'] in n1days]
    add('N1','C1','physiological_change',not any(i['status']=='act' for i in n1),notes=f"Watch days (reported cost): {sum(i['status']=='watch' for i in n1)}; act days: {sum(i['status']=='act' for i in n1)}")
    lo,hi=config['stage']['simulation']['N2']['wearable_gap_days'];sklo,skhi=config['stage']['simulation']['N2']['skipped_checkin_days']
    n2={i['missionDay']:i for i in items if i['crewId']=='C4' and i['moduleId']=='physiological_change'}
    passed=all(n2[d]['status']=='unknown' for d in range(lo,hi+1)) and all('not collected' in n2[d]['reason'].lower() and 'no symptoms' not in n2[d]['reason'].lower() for d in range(sklo,skhi+1))
    add('N2','C4','physiological_change',passed,lo,window=[lo,skhi],notes='Wearable-gap unknown and skipped check-in semantics checked.')
    return results

def run_holdout(path,out):
    out=Path(out)
    _,initial_document,_=read_frozen(path)
    configured=ROOT/initial_document['holdout'].get('report_directory','model/reports/holdout')
    if out.resolve()==(ROOT/'model/reports/holdout').resolve() and configured.resolve()!=out.resolve():
        print(f'Using labelled holdout directory: {configured}',flush=True);out=configured
    config,document,digest=verify_freeze(path,out)
    if (out/'COMPLETE.json').exists():
        complete=json.loads((out/'COMPLETE.json').read_text())
        if complete['configHash']!=digest:raise ValueError('Completed holdout hash mismatch')
        for name,expected in complete['artifactHashes'].items():
            if hashlib.sha256((out/name).read_bytes()).hexdigest()!=expected:raise ValueError('Completed holdout artifacts changed; no re-evaluation allowed')
        print('Reusing completed holdout; no second evaluation.',flush=True)
        return json.loads((out/'summary.json').read_text())
    marker=out/'STARTED.json'
    with marker.open('x') as f:json.dump({'configHash':digest,'startedAt':datetime.now(timezone.utc).isoformat()},f)
    protocol=document['holdout'];cases=[];quiet_cache={}
    for noise in protocol['noise']:
        for seed in protocol['seeds']:
            for factor in protocol['effect_scales']:
                cfg=variant_config(config,protocol,seed,factor,noise)
                mission=generate_mission(seed,cfg);output=make_indicators(mission,cfg);items=output['indicators']
                quietkey=(seed,noise)
                if quietkey not in quiet_cache:
                    quiet=generate_mission(seed,cfg,[]);qi=make_indicators(quiet,cfg)['indicators']
                    quiet_cache[quietkey]={'acts':{cid:sum(i['crewId']==cid and i['status']=='act' for i in qi) for cid in ('C1','C2','C3','C4')},'metrics':{m:false_metrics(qi,{**protocol,'exclusions':{m:{'crew':'all','days':[-1,-1]} for m in MODULES}},m) for m in MODULES}}
                outcomes=scenario_results(mission,items,cfg,quiet_cache[quietkey]['acts'])
                metrics={m:false_metrics(items,protocol,m) for m in MODULES}
                for row in outcomes:
                    if row['moduleId']:
                        metric=metrics[row['moduleId']];row['routineFalseAlerts']=metric['false_days'];row['falseAlertsPer100CrewDays']=metric['days_per100'];row['evaluableCrewDays']=metric['evaluable_days']
                coverage={cid:{m:sum(i['status']!='unknown' for i in items if i['crewId']==cid and i['moduleId']==m)/180 for m in MODULES} for cid in ('C1','C2','C3','C4')}
                n1windows={d+o for d in cfg['stage']['simulation']['N1']['days'] for o in range(-2,3)}
                n1acts=sum(i['crewId']=='C1' and i['moduleId']=='physiological_change' and i['missionDay'] in n1windows and i['status']=='act' for i in items)
                info_coverage={cid:sum(next(e['value'] for e in i['evidence'] if 'multi-signal agreement' in e.get('unit',''))!='not evaluable' for i in items if i['crewId']==cid and i['moduleId']=='physiological_change')/180 for cid in ('C1','C2','C3','C4')}
                case={'m5_info_coverage':info_coverage,'n1_act_days':n1acts,'seed':seed,'noise':noise,'effect_scale':factor,'rhr_delta_bpm':cfg['stage']['simulation']['S2']['rhr_delta_bpm'],'scenarios':outcomes,'metrics':metrics,'coverage':coverage}
                cases.append(case)
                (out/f'case_{noise}_{seed}_{factor}.json').write_bytes(encode(case))
                print(f"Holdout {len(cases)}/{len(protocol['seeds'])*len(protocol['noise'])*len(protocol['effect_scales'])} complete: {noise} seed {seed}, factor {factor}",flush=True)
    summary={'configHash':digest,'cases':len(cases),'scenarios':{},'metrics':{},'quiet_unique_cases':len(quiet_cache),'quiet_act_indicators':sum(sum(v['acts'].values()) for v in quiet_cache.values())}
    for sid in ('S1','S2','S3','S4','N1','N2'):
        rows=[r for c in cases for r in c['scenarios'] if r['scenarioId']==sid]
        summary['scenarios'][sid]={'passed':sum(r['passed'] for r in rows),'total':len(rows),'failed':sum(not r['passed'] for r in rows)}
    # Bootstrap seed blocks, preserving six variants per seed (no pseudoreplication).
    for module in MODULES:
        blocks=[]
        for seed in protocol['seeds']:
            selected=[c['metrics'][module] for c in cases if c['seed']==seed]
            blocks.append({'false_days':sum(x['false_days'] for x in selected),'false_episodes':sum(x['false_episodes'] for x in selected),'evaluable_days':sum(x['evaluable_days'] for x in selected)})
        count=sum(b['false_days'] for b in blocks);denom=sum(b['evaluable_days'] for b in blocks);episodes=sum(b['false_episodes'] for b in blocks)
        summary['metrics'][module]={'false_days':count,'false_episodes':episodes,'evaluable_days':denom,'days_per100':100*count/denom,'episodes_per100':100*episodes/denom,
          'day_rate_ci95':bootstrap_ci(blocks,None,'false_days','evaluable_days',samples=protocol['bootstrap_samples'],seed=protocol['bootstrap_seed']),
          'episode_rate_ci95':bootstrap_ci(blocks,None,'false_episodes','evaluable_days',samples=protocol['bootstrap_samples'],seed=protocol['bootstrap_seed'])}
    detblocks=[{'detected':np.mean([r['passed'] for c in cases if c['seed']==seed for r in c['scenarios'] if r['scenarioId']=='S2'])} for seed in protocol['seeds']]
    summary['s2_detection_rate_ci95']=bootstrap_ci(detblocks,'detected',samples=protocol['bootstrap_samples'],seed=protocol['bootstrap_seed'])
    summary['n1_act_days']=sum(c['n1_act_days'] for c in cases)
    summary['quiet_metrics']={m:{k:sum(v['metrics'][m][k] for v in quiet_cache.values()) for k in ('false_days','false_episodes','evaluable_days')} for m in MODULES}
    summary['m5_info_coverage']={cid:{'min':min(c['m5_info_coverage'][cid] for c in cases),'mean':float(np.mean([c['m5_info_coverage'][cid] for c in cases]))} for cid in ('C1','C2','C3','C4')}
    summary['coverage']={cid:{module:{'min':min(c['coverage'][cid][module] for c in cases),'mean':float(np.mean([c['coverage'][cid][module] for c in cases]))} for module in MODULES} for cid in ('C1','C2','C3','C4')}
    summary['by_variant']={f'{noise}/{factor}':{sid:{'passed':sum(r['passed'] for c in cases if c['noise']==noise and c['effect_scale']==factor for r in c['scenarios'] if r['scenarioId']==sid),'total':sum(1 for c in cases if c['noise']==noise and c['effect_scale']==factor for r in c['scenarios'] if r['scenarioId']==sid)} for sid in ('S1','S2','S3','S4','N1','N2')} for noise in protocol['noise'] for factor in protocol['effect_scales']}
    (out/'summary.json').write_bytes(encode(summary));(out/'results.json').write_bytes(encode(cases))
    with (out/'results.csv').open('w',newline='') as f:
        fields=['seed','noise','effect_scale','scenarioId','crewId','moduleId','passed','firstWatchDay','firstActDay','delayVsOnsetDays','delayVsSymptomDays','unknownDays'];w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for c in cases:
            for r in c['scenarios']:w.writerow({k:({**c,**r}).get(k) for k in fields})
    lines=['# Frozen holdout — synthetic-scenario results','','## What worked / what failed','','All failures are retained; no clinical-validation claim. Thresholds/configuration were frozen before this one run.','','| Scenario | Passed | Failed |','| --- | --- | --- |']
    for sid,r in summary['scenarios'].items():lines.append(f"| {sid} | {r['passed']}/{r['total']} | {r['failed']} |")
    lines+=['','| Module | False days / episodes | Evaluable crew-days | Days/100 [95% CI] | Episodes/100 [95% CI] |','| --- | --- | --- | --- | --- |']
    for m,r in summary['metrics'].items():lines.append(f"| {m} | {r['false_days']} / {r['false_episodes']} | {r['evaluable_days']} | {r['days_per100']:.3f} {r['day_rate_ci95']} | {r['episodes_per100']:.3f} {r['episode_rate_ci95']} |")
    lines+=['',f"N1 act days: {summary['n1_act_days']}.",f"S2 seed-block detection-rate CI95: {summary['s2_detection_rate_ci95']}.",f"Isolated S1 quiet missions: {len(quiet_cache)} unique seed/noise cases (reused across three irrelevant effect scales); {summary['quiet_act_indicators']} act indicators.",'','Coverage per crew/module and per-variant outcomes are in summary.json; first watch/act and delays for every case/scenario are in results.csv/json. Unknown days are never counted as evaluable. Bootstrap resamples seed blocks, preserving correlated noise/scale variants. Counts are flagged days and contiguous episodes, not clinical outcomes.','', 'M3 is the sole physiological status detector; M5 agreement is info-only. N1 watch costs remain in false-alert accounting. S3 is checked at each exact verified DONKI onset. S4 pass means watch-level or higher by day 97; act timing is reported, not forced.','', 'S1/S3 have per-crew rows, and S1 repeated factor rows are labelled reuse; do not interpret 480 rows as 480 independent missions. No rerun or tuning followed these observations.']
    (out/'summary.md').write_text('\n'.join(lines)+'\n')
    (out/'COMPLETE.json').write_bytes(encode({'configHash':digest,'completedAt':datetime.now(timezone.utc).isoformat(),'cases':len(cases),'artifactHashes':{name:hashlib.sha256((out/name).read_bytes()).hexdigest() for name in ('summary.json','results.json','results.csv','summary.md')}}))
    return summary
