"""Run the three core modules with frozen M3 physiological rules and M5 information only; no tuning or holdout evaluation."""
import argparse
import json
import os
import hashlib
import importlib.metadata
from pathlib import Path
from .config import load_config, ROOT
from .sim.generate import generate_mission
from .sim.radiation import dose_total
from .export.files import make_indicators, export_files, encode

def summary(mission,indicators,config):
    phys=[i for i in indicators['indicators'] if i['moduleId']=='physiological_change']
    event=config['scenarios']['scenarios']['S2']
    s2=[i for i in phys if i['crewId']==event['crew'] and event['onsetDay']<=i['missionDay']<=event['endDay']]
    first=lambda state: next((i['missionDay'] for i in s2 if i['status'] in state),None)
    detected=first(('watch','act'))
    n1=config['scenarios']['scenarios']['N1']['crew'];n2=config['scenarios']['scenarios']['N2']['crew']
    quiet=[i for i in phys if i['status']!='unknown' and not (i['crewId']==event['crew'] and event['onsetDay']<=i['missionDay']<=event['endDay'])]
    false_alerts=sum(i['status'] in ('watch','act') for i in quiet)
    return {'label':'synthetic-scenario results; frozen M3 with M5 info-only','seed':mission['seed'],'configHash':config['configHash'],
        'S2':{'firstWatchDay':first(('watch',)),'firstActDay':first(('act',)),'firstFlagDay':detected,'passedBySymptomDay':detected is not None and detected<=event['symptomDay'],'onsetDay':event['onsetDay'],'symptomDay':event['symptomDay'],'endDay':event['endDay']},
        'N1':{'actDays':[i['missionDay'] for i in phys if i['crewId']==n1 and i['status']=='act'],'watchDays':[i['missionDay'] for i in phys if i['crewId']==n1 and i['status']=='watch']},
        'N2':{'unknownDays':[i['missionDay'] for i in phys if i['crewId']==n2 and i['status']=='unknown']},
        'dose':{c['crewId']:dose_total([r for r in mission['readings'] if r['crewId']==c['crewId']]) for c in mission['crew']},
        'statuses':{state:sum(i['status']==state for i in phys) for state in ('nominal','watch','act','unknown')},
        'routineFalseAlerts':false_alerts, 'evaluableQuietCrewDays':len(quiet),
        'falseAlertsPer100QuietCrewDays':100*false_alerts/len(quiet) if quiet else None,
        'notImplemented':[], 'core':core_summary(mission,indicators,config)}

def core_summary(mission,indicators,config):
    from .modules.radiation import evaluate as radiation
    s4=config['scenarios']['scenarios']['S4']
    sleep=[i for i in indicators['indicators'] if i['moduleId']=='sleep_alertness' and i['crewId']==s4['crew'] and s4['onsetDay']<=i['missionDay']<=s4['endDay']]
    first=lambda rows,status:next((i['missionDay'] for i in rows if i['status']==status),None)
    warnings={}
    for crew in mission['crew']:
        cid=crew['crewId'];s3=config['scenarios']['scenarios']['S3']['onsetDay']
        samples=sorted((e for e in mission['radiationEvents'] if e['crewId']==cid and e['missionDay']==s3),key=lambda e:e['timeHoursFromDayStart'])
        first_sample=next((e for e in samples if radiation(mission['readings'],mission['radiationEvents'],cid,s3,config,prior_career_dose_msv=crew['prior_career_dose_msv'],as_of_hour=e['timeHoursFromDayStart'])['status']=='act'),None)
        warnings[cid]={'firstActDay':first_sample['missionDay'] if first_sample else None,'firstActHour':first_sample['timeHoursFromDayStart'] if first_sample else None}
    return {'S3':warnings,'S4':{'firstWatchDay':first(sleep,'watch'),'firstActDay':first(sleep,'act'),'dailyRelativeDebtHours':{str(i['missionDay']):next(e['value'] for e in i['evidence'] if 'relative debt' in e.get('unit','')) for i in sleep}},'radiationPolicy':config['stage']['radiation']}

def plot_s2(mission,config,path):
    os.environ.setdefault('MPLCONFIGDIR','/tmp/spacehealth-matplotlib')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from .baseline.fixed import fit_baselines
    event=config['scenarios']['scenarios']['S2']
    rows=[r for r in mission['readings'] if r['crewId']==event['crew']]
    baseline=fit_baselines(rows,event['crew'],config)
    fig,axes=plt.subplots(3,1,figsize=(11,8),sharex=True)
    for ax,signal in zip(axes,config['rules']['physiological_change']['signals']):
        b=baseline[signal];x=[r['missionDay'] for r in rows];y=[r[signal] for r in rows]
        ax.plot(x,y,lw=0.9,label='Simulated reading')
        ax.axhline(b.center,color='black',lw=0.8,label='Fixed preflight median')
        ax.axhspan(b.center-config['watch_z']*b.scale,b.center+config['watch_z']*b.scale,color='gray',alpha=0.15,label='± watch threshold × robust scale')
        ax.axvline(event['onsetDay'],color='orange',linestyle='--',label='Injected change onset')
        ax.axvline(event['symptomDay'],color='red',linestyle=':',label='Simulated symptom onset')
        ax.set_ylabel({'rhr_bpm':'Resting HR (bpm)','hrv_rmssd_ms':'RMSSD (ms)','skin_temp_delta_c':'Skin temperature\ndeviation (°C)'}[signal])
        ax.set_xlim(event['onsetDay']-10,event['endDay']+10)
    axes[0].legend(fontsize=7,ncol=2);axes[-1].set_xlabel('Mission day')
    fig.suptitle(f'SIMULATED DATA — S2 / {event["crew"]} / seed {mission["seed"]}; not clinical validation')
    fig.tight_layout();path=Path(path);path.parent.mkdir(parents=True,exist_ok=True);fig.savefig(path,dpi=150);plt.close(fig)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=Path(__file__).resolve().parents[1]/'configs/frozen_v1.yaml')
    parser.add_argument('--seed',type=int,default=0)
    parser.add_argument('--out',type=Path,default=Path('out'))
    parser.add_argument('--release',action='store_true')
    parser.add_argument('--illustrative',action='store_true',help='Export the disclosed post-holdout illustrative case')
    parser.add_argument('--noise',choices=['gaussian','student_t'])
    parser.add_argument('--effect-scale',type=float)
    parser.add_argument('--reports',type=Path,help='Explicit directory for plots/input snapshots; omitted by default')
    parser.add_argument('--scenarios',nargs='*',help='Scenario IDs; omit for all, empty for quiet S1 only')
    args=parser.parse_args()
    from .evaluate.frozen import read_frozen
    config,frozen,config_hash=read_frozen(args.config)
    variant=frozen['holdout']['release_case']
    if args.illustrative:
        if args.seed not in frozen['holdout']['seeds']:parser.error('Illustrative seed must be in the frozen holdout seed list')
        if args.release or args.scenarios is not None:parser.error('--illustrative requires all scenarios and cannot be combined with --release')
        variant={'noise':args.noise or 'gaussian','effect_scale':args.effect_scale if args.effect_scale is not None else 0.8}
        if args.seed!=1002 or variant!={'noise':'gaussian','effect_scale':0.8}:parser.error('The approved illustrative case is seed 1002, Gaussian noise, effect scale 0.8')
        if args.out.resolve()==(ROOT/'model/out/release').resolve():parser.error('Illustrative export cannot overwrite the canonical release')
    elif args.noise is not None or args.effect_scale is not None:parser.error('--noise and --effect-scale require --illustrative')
    if args.seed in frozen['holdout']['seeds']:
        from .evaluate.holdout import variant_config,verify_freeze
        verify_freeze(args.config,ROOT/frozen['holdout'].get('report_directory','model/reports/holdout'))
        config=variant_config(config,frozen['holdout'],args.seed,variant['effect_scale'],variant['noise'])
    if args.out.resolve()==(ROOT/'model/out/illustrative').resolve() and not args.illustrative:parser.error('Illustrative output requires --illustrative')
    if args.out.resolve()==(ROOT/'model/out/release').resolve() and not args.release:parser.error('Canonical release requires --release')
    if args.release and (args.seed!=frozen['holdout']['seeds'][0] or args.scenarios is not None):parser.error('--release requires the preselected frozen case with all scenarios')
    mission=generate_mission(args.seed,config,args.scenarios)
    indicators=make_indicators(mission,config)
    export_files(mission,indicators,args.out)
    from .export.release import save_release
    save_release(args.out,config,frozen,args.seed,release=args.release,illustrative=args.illustrative,variant=variant)
    report=summary(mission,indicators,config)
    if args.reports is not None:
        path=args.reports;path.mkdir(parents=True,exist_ok=True)
        code_files=sorted((ROOT/'model/spacehealth_model').rglob('*.py'))
        report['codeHashes']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in code_files}
        report['dependencies']={name:importlib.metadata.version(name) for name in ['numpy','scipy','pydantic','jsonschema','PyYAML','matplotlib']}
        (path/f'stage0_seed{args.seed}_inputs.json').write_bytes(encode(config['inputSources']))
        (path/f'stage0_seed{args.seed}.json').write_bytes(encode(report))
        plot_s2(mission,config,path/f's2_seed{args.seed}.png')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
