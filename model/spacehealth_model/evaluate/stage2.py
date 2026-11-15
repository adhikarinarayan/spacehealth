"""Full development comparison; no parameter tuning, selection or holdout."""
import copy
import csv
from datetime import datetime,timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import numpy as np
import yaml
from ..config import ROOT,load_config
from ..baseline.fixed import fit_baselines
from ..detectors.candidates import get_detector
from ..sim.generate import generate_mission
from ..modules.radiation import evaluate as radiation
from .metrics import candidate_metrics

def load_stage2():
    path=ROOT/'model/configs/stage2.yaml';raw=path.read_bytes();stage=yaml.safe_load(raw)
    previous=yaml.safe_load((ROOT/'model/configs/stage1.yaml').read_text())
    for name in stage['candidates']:
        if stage[name]!=previous[name]:raise ValueError('Stage-2 detector parameters differ from stage 1')
    research=load_config()
    # Research was advanced to TASK-009 before its code. Stage 2 must use old timing.
    snapshot=ROOT/stage['synthetic_snapshot']
    captured=json.loads(snapshot.read_text())
    old=yaml.safe_load(captured['research/scenarios.yaml']['text'])['scenarios']['S3']['timeline']
    research=copy.deepcopy(research);research['scenarios']['scenarios']['S3']['timeline']=old
    stage1={**previous,**stage}
    return {'research':research,'stage1':stage1,'stage2':stage,'configHash':hashlib.sha256(raw+json.dumps(research,sort_keys=True).encode()).hexdigest(),'stage2Source':raw.decode(),'timelineOverride':old,'snapshotHash':hashlib.sha256(snapshot.read_bytes()).hexdigest()}

def episode_count(rows):
    count=0;last=None
    for r in sorted(rows,key=lambda x:x.missionDay):
        flagged=r.status in ('watch','act')
        if flagged and (last is None or last.missionDay!=r.missionDay-1 or last.status not in ('watch','act')):count+=1
        last=r
    return count

def bootstrap_ci(rows,key,numerator=None,denominator=None,*,samples=10000,seed=0):
    rng=np.random.default_rng(seed);idx=rng.integers(0,len(rows),size=(samples,len(rows)))
    if numerator:
        nums=np.array([r[numerator] for r in rows],float);dens=np.array([r[denominator] for r in rows],float)
        values=100*nums[idx].sum(axis=1)/dens[idx].sum(axis=1)
    else:values=np.array([r[key] for r in rows],float)[idx].mean(axis=1)
    return np.quantile(values,[.025,.975]).tolist()

def run_stage2(seeds,out):
    cfg=load_stage2();stage=cfg['stage2'];allowed=list(range(stage['seed_min'],stage['seed_max']+1))
    if sorted(seeds)!=allowed or len(seeds)!=len(allowed):raise ValueError('Stage 2 requires exactly dev seeds 0–19; holdout/seed search forbidden')
    out=Path(out);out.mkdir(parents=True,exist_ok=True);rows=[];start=datetime.now(timezone.utc).isoformat()
    for seed in seeds:
        mission=generate_mission(seed,cfg['research']);results={c:{} for c in stage['candidates']}
        for crew in mission['crew']:
            cid=crew['crewId'];data=[r for r in mission['readings'] if r['crewId']==cid];baseline=fit_baselines(data,cid,cfg['research'])
            for c in results:results[c][cid]=get_detector(c).detect(data,baseline,cfg)
        caution=0;rad_evaluable=0
        excluded=stage['radiation_exclude_days']
        for crew in mission['crew']:
            for day in range(1,181):
                if excluded[0]<=day<=excluded[1]:continue
                item=radiation(mission['readings'],mission['radiationEvents'],crew['crewId'],day,cfg['research'],prior_career_dose_msv=crew['prior_career_dose_msv'])
                if item['status']!='unknown':rad_evaluable+=1
                if item['status']=='watch' and 'placeholder threshold' in item['reason']:caution+=1
        for candidate,by_crew in results.items():
            metric=candidate_metrics(candidate,seed,by_crew,cfg)
            metric['routine_false_episodes']=sum(episode_count([r for r in values if not (cid=='C2' and 40<=r.missionDay<=50)]) for cid,values in by_crew.items())
            metric['false_episodes_per100_crew_days']=100*metric['routine_false_episodes']/metric['evaluable_crew_days']
            metric['coverage']={cid:{'evaluable':sum(r.status!='unknown' for r in values),'total':len(values)} for cid,values in by_crew.items()}
            metric['radiation_caution_days_outside_s3']=caution;metric['radiation_evaluable_days_outside_s3']=rad_evaluable
            rows.append(metric)
        print(f'Stage 2 seed {seed} complete',flush=True)
    summary={}
    for candidate in stage['candidates']:
        selected=[r for r in rows if r['candidate']==candidate]
        def dist(key):
            vals=[r[key] for r in selected if r[key] is not None]
            return {'values':vals,'count':len(vals),'mean':float(np.mean(vals)) if vals else None,'min':min(vals) if vals else None,'max':max(vals) if vals else None}
        denom=sum(r['evaluable_crew_days'] for r in selected);alerts=sum(r['routine_false_alerts'] for r in selected);episodes=sum(r['routine_false_episodes'] for r in selected)
        coverage={cid:{'evaluable':sum(r['coverage'][cid]['evaluable'] for r in selected),'total':sum(r['coverage'][cid]['total'] for r in selected)} for cid in selected[0]['coverage']}
        for v in coverage.values():v['fraction']=v['evaluable']/v['total']
        summary[candidate]={'seeds':len(selected),'s2_detected':sum(r['s2_detected_by_day42'] for r in selected),'detection_rate_ci95':bootstrap_ci(selected,'s2_detected_by_day42',samples=stage['bootstrap']['samples'],seed=stage['bootstrap']['seed']),
            'first_watch':dist('s2_first_watch_day'),'first_act':dist('s2_first_act_day'),'delay_onset':dist('s2_delay_vs_onset_days'),'delay_symptom':dist('s2_delay_vs_symptom_days'),
            'n1_act_days':sum(len(r['n1_act_days']) for r in selected),'n1_watch_days':sum(len(r['n1_watch_days']) for r in selected),'n1_watch_days_per_seed':dist_count(selected,'n1_watch_days'),
            'n2_gap_all_unknown':all(r['n2_gap_all_unknown'] for r in selected),'coverage':coverage,'false_alert_days':alerts,'false_alert_episodes':episodes,'evaluable_crew_days':denom,
            'false_days_per100':100*alerts/denom,'false_episodes_per100':100*episodes/denom,
            'false_day_rate_ci95':bootstrap_ci(selected,None,'routine_false_alerts','evaluable_crew_days',samples=stage['bootstrap']['samples'],seed=stage['bootstrap']['seed']),
            'false_days_per_seed':dist('routine_false_alerts'),'false_episodes_per_seed':dist('routine_false_episodes'),
            'radiation_caution_days_outside_s3':sum(r['radiation_caution_days_outside_s3'] for r in selected),'radiation_evaluable_days_outside_s3':sum(r['radiation_evaluable_days_outside_s3'] for r in selected)}
    def dump(name,v):(out/name).write_text(json.dumps(v,indent=2,allow_nan=False)+'\n')
    dump('results.json',rows);dump('summary.json',summary)
    with (out/'results.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader()
        for row in rows:writer.writerow({k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in row.items()})
    lines=['# Stage-2 full development comparison — synthetic results','','Fixed stage-1 parameters; 20 dev seeds; no winner selected. Bootstrap resamples seeds, not individual correlated crew-days.','','| Candidate | S2 by day42 | Detection 95% CI | First watch mean [range] | N1 watch / act days | False days / episodes | Evaluable days | Days /100 [95% CI] | Episodes /100 |','| --- | --- | --- | --- | --- | --- | --- | --- | --- |']
    for c,s in summary.items():
        w=s['first_watch'];ci=s['false_day_rate_ci95']
        lines.append(f"| {c} | {s['s2_detected']}/20 | {s['detection_rate_ci95']} | {w['mean']} [{w['min']}, {w['max']}] | {s['n1_watch_days']} / {s['n1_act_days']} | {s['false_alert_days']} / {s['false_alert_episodes']} | {s['evaluable_crew_days']} | {s['false_days_per100']:.3f} [{ci[0]:.3f}, {ci[1]:.3f}] | {s['false_episodes_per100']:.3f} |")
    lines+=['','- First-watch/delay summaries exclude misses; misses remain explicitly counted in detection rates. Full distributions, first-act data and per-seed mean/range metrics are in summary.json and results.csv.',
            '- N1 watches are a reported cost under D14; act counts must remain zero. Unknown days split episodes. Excluded C2 days 40–50 also split runs; a post-window continuation counts as a new routine episode.',
            '- Coverage per crew is reported separately in summary.json: a smaller evaluable denominator is not evidence of better specificity. Complete-vector M5 cannot evaluate C4 when its HRV baseline is insufficient.',
            f"- Radiation placeholder caution days outside S3 days 72–81: {next(iter(summary.values()))['radiation_caution_days_outside_s3']} / {next(iter(summary.values()))['radiation_evaluable_days_outside_s3']} evaluable crew-days. Counted once per seed; the same result is attached to both candidate rows, not summed across candidates.",
            '- Research YAML had already advanced to DONKI timing before this task; the captured pre-TASK-009 timeline is explicitly frozen for this pre-change run. No detector/simulator changes, tuning, holdout or winner recommendation.']
    (out/'summary.md').write_text('\n'.join(lines)+'\n')
    os.environ.setdefault('MPLCONFIGDIR','/tmp/spacehealth-matplotlib');import matplotlib;matplotlib.use('Agg');import matplotlib.pyplot as plt
    fig,axes=plt.subplots(1,2,figsize=(10,4),sharey=True)
    for ax,(candidate,s) in zip(axes,summary.items()):
        ax.hist(s['first_watch']['values'],bins=np.arange(39.5,49.5,1),color='#357c8a',rwidth=.8);ax.axvline(42,color='orange',ls='--');ax.set_title(f"{candidate}; {20-s['first_watch']['count']} no watch in S2");ax.set_xlabel('First watch day')
    axes[0].set_ylabel('Dev seeds');fig.suptitle('SIMULATED Stage 2 — no clinical validation');fig.tight_layout();fig.savefig(out/'s2_first_watch_hist.png',dpi=150);plt.close(fig)
    dump('run_manifest.json',{'startedAt':start,'finishedAt':datetime.now(timezone.utc).isoformat(),'seeds':seeds,'configHash':cfg['configHash'],'stage2Source':cfg['stage2Source'],'inputSources':cfg['research']['inputSources'],'timelineOverride':cfg['timelineOverride'],'snapshotHash':cfg['snapshotHash'],
        'codeHashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted((ROOT/'model/spacehealth_model').rglob('*.py'))},'versions':{p:importlib.metadata.version(p) for p in ['numpy','scipy','scikit-learn','PyYAML','matplotlib']}})
    return summary

def dist_count(rows,key):
    values=[len(r[key]) for r in rows];return {'mean':float(np.mean(values)),'min':min(values),'max':max(values)}
