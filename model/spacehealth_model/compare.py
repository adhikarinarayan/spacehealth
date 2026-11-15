"""TASK-004 Stage-1 comparison, frozen defaults and development seeds 0/1/2 only."""
import argparse
import csv
import hashlib
import importlib.metadata
import json
import os
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import yaml
from .config import load_config, ROOT
from .baseline.fixed import fit_baselines
from .sim.generate import generate_mission
from .detectors.candidates import get_detector
from .evaluate.metrics import CANDIDATES,candidate_metrics,summarize

def load_stage1():
    research=load_config()
    path=ROOT/'model/configs/stage1.yaml';raw=path.read_bytes()
    stage=yaml.safe_load(raw)
    return {'research':research,'stage1':stage,'configHash':hashlib.sha256((research['configHash']+'\0').encode()+raw).hexdigest(),'stage1Source':raw.decode()}

def _json(path,value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')

def plot_overlay(mission,by_candidate,cfg,seed,path):
    os.environ.setdefault('MPLCONFIGDIR','/tmp/spacehealth-matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    r=cfg['research'];s2=r['scenarios']['scenarios']['S2']
    rows=[row for row in mission['readings'] if row['crewId']==s2['crew']]
    baselines=fit_baselines(rows,s2['crew'],r)
    fig,axes=plt.subplots(4,1,figsize=(13,10),sharex=True,gridspec_kw={'height_ratios':[1,1,1,1.8]})
    labels={'rhr_bpm':'Resting HR (bpm)','hrv_rmssd_ms':'RMSSD (ms)','skin_temp_delta_c':'Skin temperature\ndeviation (°C)'}
    for ax,signal in zip(axes,cfg['stage1']['signals']):
        b=baselines[signal]
        ax.plot([row['missionDay'] for row in rows],[row[signal] for row in rows],lw=1,color='#277a89')
        ax.axhline(b.center,color='black',lw=.8)
        ax.axhspan(b.center-b.scale,b.center+b.scale,color='gray',alpha=.12)
        ax.set_ylabel(labels[signal])
    for index,candidate in enumerate(CANDIDATES):
        results=[x for x in by_candidate[candidate][s2['crew']] if 30<=x.missionDay<=58]
        watch=[x.missionDay for x in results if x.status=='watch'];act=[x.missionDay for x in results if x.status=='act']
        axes[3].scatter(watch,[index]*len(watch),marker='s',s=30,color='#bd8624')
        axes[3].scatter(act,[index]*len(act),marker='^',s=40,color='#bd423e')
    axes[3].set_yticks(range(len(CANDIDATES)),CANDIDATES);axes[3].invert_yaxis()
    axes[3].set_ylabel('Watch ■ / Act ▲');axes[3].set_xlabel('Mission day')
    for ax in axes:
        ax.set_xlim(30,58);ax.axvline(s2['onsetDay'],color='orange',ls='--',lw=.9)
        ax.axvline(s2['symptomDay'],color='red',ls=':',lw=.9);ax.grid(alpha=.12)
    fig.suptitle(f'SIMULATED DATA — stage-1 dev seed {seed}; fixed parameters, no clinical validation\nDashed: injected onset; dotted: simulated symptom day; bands: ±1 robust scale')
    fig.tight_layout();fig.savefig(path,dpi=150);plt.close(fig)

def run_comparison(seeds,out):
    cfg=load_stage1();allowed=cfg['stage1']['allowed_seeds']
    if sorted(seeds)!=allowed or len(set(seeds))!=len(allowed):
        raise ValueError(f'This task accepts exactly development seeds {allowed}; no holdout or seed search')
    out=Path(out);out.mkdir(parents=True,exist_ok=True)
    started=datetime.now(timezone.utc).isoformat();rows=[]
    for seed in seeds:
        mission=generate_mission(seed,cfg['research'])
        by_candidate={candidate:{} for candidate in CANDIDATES}
        for crew in mission['crew']:
            crew_id=crew['crewId'];readings=[r for r in mission['readings'] if r['crewId']==crew_id]
            baseline=fit_baselines(readings,crew_id,cfg['research'])
            for candidate in CANDIDATES:
                by_candidate[candidate][crew_id]=get_detector(candidate).detect(readings,baseline,cfg)
        for candidate in CANDIDATES:rows.append(candidate_metrics(candidate,seed,by_candidate[candidate],cfg))
        _json(out/f'daily_seed{seed}.json',{candidate:{crew:[asdict(r) for r in values] for crew,values in crews.items()} for candidate,crews in by_candidate.items()})
        plot_overlay(mission,by_candidate,cfg,seed,out/f's2_overlay_seed{seed}.png')
    summary=summarize(rows,cfg)
    with (out/'results.csv').open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(rows[0]));writer.writeheader()
        for row in rows:writer.writerow({k:json.dumps(v) if isinstance(v,(list,dict)) else v for k,v in row.items()})
    _json(out/'results.json',rows);_json(out/'summary.json',summary)
    lines=['# Stage-1 development comparison — synthetic-scenario results','','Fixed supplied parameters; seeds 0, 1, 2 only. Kept means eligible for next-stage review, not selected, validated or clinically useful. M1 original failing S2 test is unchanged.','','| Candidate | S2 by day 42 | Median first watch (detected windows only) | N1 watch days | N1 acts | False alerts / evaluable crew-days | Alerts /100 | Verdict / reason |','| --- | --- | --- | --- | --- | --- | --- | --- |']
    for s in summary:
        lines.append(f"| {s['candidate']} | {s['detected']}/{s['runs']} | {s['median_first_watch_day'] if s['median_first_watch_day'] is not None else 'none'} | {s['n1_watches']} | {s['n1_acts']} | {s['false_alerts']}/{s['evaluable_crew_days']} | {s['false_alerts_per100_crew_days']:.3f} | {s['verdict']}: {'; '.join(s['discard_reasons']) or 'no mechanical discard criterion triggered'} |")
    lines+=['','False-alert numerator counts flagged days (not episodes); denominator is evaluable days outside C2 days 40–50, all four crew. N1 windows are 60/61/110 ±2 days. Smaller denominators for methods needing all three signals reflect C4 insufficient HRV baseline, not fewer false alerts by design.','','S2 first watch/act are searched in days 40–48; flags before onset are false alerts rather than detections. Missing windows are reported as no detection, never assigned delay zero.','','M0/M2/M3/M4 need RHR and its valid fixed baseline. M1 reuses the original ≥2-signal evaluator. M1b additionally needs at least one usable corroborating signal today; corroboration on either of the two RHR-shift nights qualifies. M5/M6 need all three usable current values and at least min_valid_days complete preflight vectors; C4 HRV has only 8, so these methods return unknown throughout C4 except any overriding red-flag symptom.','','CuSum nominal-day reset means three consecutive days whose statistic has not crossed h; reset occurs after the third day is evaluated. Missing/implausible input resets recurrence/persistence; gaps are not treated as zero readings. EWMA starts at zero and uses the supplied steady-state bound (no warm-up correction).','','Mahalanobis uses fitted preflight mean in robust-z space and Ledoit–Wolf precision, one-sided RHR gate, χ² quantile as supplied. IsolationForest uses raw preflight vectors, fixed estimator parameters, training-score percentile and no online refit. Numerical feature deviations for these two methods are descriptive, not feature attribution or a statement of independent corroboration.','','Red-flag symptom act is shared and overrides unavailable inputs. Only M1 retains its original strong-change act rule. Skipped check-ins are explicitly not collected. No winner chosen, parameters tuned, real data used or holdout evaluated.','',f"Config hash: `{cfg['configHash']}`."]
    (out/'summary.md').write_text('\n'.join(lines)+'\n')
    code_paths=[ROOT/'model/spacehealth_model/compare.py',*sorted((ROOT/'model/spacehealth_model/detectors').glob('*.py')),*sorted((ROOT/'model/spacehealth_model/evaluate').glob('*.py')),ROOT/'model/spacehealth_model/sim/generate.py',ROOT/'model/spacehealth_model/baseline/fixed.py',ROOT/'model/spacehealth_model/modules/physiological.py',ROOT/'model/spacehealth_model/config.py']
    meta={'startedAt':started,'finishedAt':datetime.now(timezone.utc).isoformat(),'label':'development synthetic-scenario comparison','seeds':seeds,'configHash':cfg['configHash'],
          'stage1Source':cfg['stage1Source'],'researchInputs':cfg['research']['inputSources'],
          'codeHashes':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in code_paths},
          'versions':{name:importlib.metadata.version(name) for name in ['numpy','scipy','scikit-learn','PyYAML','matplotlib']}}
    _json(out/'run_manifest.json',meta)
    return summary

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--stage',choices=['1','2','holdout'],default='1')
    parser.add_argument('--config',type=Path)
    parser.add_argument('--seeds',type=int,nargs='+',default=[0,1,2]);parser.add_argument('--out',type=Path,default=Path('reports/stage1'))
    args=parser.parse_args()
    if args.stage=='holdout':
        from .evaluate.holdout import run_holdout
        from .evaluate.frozen import DEFAULT
        print(json.dumps(run_holdout(args.config or DEFAULT,args.out),indent=2));return
    if args.stage=='2':
        from .evaluate.stage2 import run_stage2
        print(json.dumps(run_stage2(args.seeds,args.out),indent=2));return
    for result in run_comparison(args.seeds,args.out):print(f"{result['candidate']}: {result['detected']}/{result['runs']} detected; {result['verdict']}; false alerts {result['false_alerts_per100_crew_days']:.3f}/100")
if __name__=='__main__':main()
