"""Evaluation-only replay: real timing, assumed dose and Mars mapping."""
import argparse
import copy
import json
import math
from pathlib import Path
import tempfile
from ..config import ROOT
from ..data_sources import donki
from ..sim.generate import generate_mission
from ..sim.radiation import sample_times,integrate_day
from ..modules.radiation import evaluate
from ..export.files import select_cards
from .frozen import read_frozen

WORDING='real NASA DONKI SEP onset timing (observed near Earth); dose and Mars-transit mapping are simulation assumptions'
WINDOWS={'2017-09':'2017-08-15_2017-10-10','2021-10':'2021-10-01_2021-11-25','2024-05':'2024-05-01_2024-06-25','2024-10':'2024-10-01_2024-11-25'}
EXPECTED={'2017-09':['09-05 00:30','09-06 23:45','09-10 16:25'],'2021-10':['10-28 16:35','11-03 20:55'],'2024-05':['05-10 13:35','05-11 02:10','05-13 14:00','06-08 02:25'],'2024-10':['10-09 03:50','10-26 18:05','11-21 18:45']}

def load_window(window):
    name='SEP_'+WINDOWS[window]+'.json';key='data/raw/nasa_donki_sep/'+name
    expected=next(line.split()[0] for line in donki.CHECKSUMS.read_text().splitlines() if line.split(maxsplit=1)[-1].lstrip('*')==key)
    # Read-only adapter pins a 2017 manifest key. Alias each original source
    # manifest digest to that key; adapter still verifies the actual file bytes.
    with tempfile.TemporaryDirectory() as temporary:
        manifest=Path(temporary)/'checksums';manifest.write_text(expected+'  '+donki.KEY+'\n')
        events,digest=donki.load_events(ROOT/'research'/key,manifest)
    start,end=WINDOWS[window].split('_')
    episodes=donki.goes_episodes(events,selection={'window_start_utc':start+'T00:00:00Z','window_end_exclusive_utc':end+'T00:00:00Z','group_hours':6})
    return donki.map_episodes(episodes,first_day=60),digest

def independent_dose(rows):
    return sum((b['timeHoursFromDayStart']-a['timeHoursFromDayStart'])*(a['dose_rate_msv_h']+b['dose_rate_msv_h'])/2 for a,b in zip(rows,rows[1:]) if a['dose_rate_msv_h'] is not None and b['dose_rate_msv_h'] is not None)

def profile(mapped,config):
    p=config['stage']['simulation']['S3'];rise=p['rise_hours'];decay=p['decay_hours'];duration=p['duration_days']*24
    starts=[(m['missionDay']-1)*24+m['timeHoursFromDayStart'] for m in mapped]
    def shape(t):return 0. if t<0 or t>=duration else t/rise if t<rise else math.exp(-(t-rise)/decay)
    grid={}
    for day in range(1,181):
        base=(day-1)*24;active=any(base+24>s and base<s+duration for s in starts)
        times=set(sample_times(config['stage']['sampling']['event_interval_hours' if active else 'background_interval_hours']))
        for s in starts:
            for boundary in (s,s+rise,s+rise+decay,s+duration):
                if 0<=boundary-base<24:times.add(boundary-base)
        grid[day]=sorted(times)
    areas=[sum(integrate_day([{'timeHoursFromDayStart':t,'dose_rate_msv_h':shape((d-1)*24+t-s)} for t in times])[0] or 0 for d,times in grid.items()) for s in starts]
    background=config['signals']['daily_dose_msv']['sim_background']/24;byday={}
    for day,times in grid.items():
        byday[day]=[{'missionDay':day,'timeHoursFromDayStart':t,'dose_rate_msv_h':background+sum(shape((day-1)*24+t-s)*19.5/len(starts)/a for s,a in zip(starts,areas)), 'spe_warning':any(0<=(day-1)*24+t-s<rise+decay for s in starts)} for t in times]
    return byday,starts

def merge(intervals):
    result=[]
    for a,b in intervals:
        if result and a<=result[-1][1]:result[-1][1]=max(b,result[-1][1])
        else:result.append([a,b])
    return result

def run_window(window,config=None,quiet=None):
    config=config or read_frozen()[0];quiet=quiet or generate_mission(0,config,[])
    mapped,digest=load_window(window);byday,starts=profile(mapped,config);samples=[e for rows in byday.values() for e in rows]
    daily={d:integrate_day(rows) for d,rows in byday.items()}
    mission=copy.deepcopy(quiet)
    for row in mission['readings']:
        if row['missionDay']>0:row['daily_dose_msv'],row['dose_coverage']=daily[row['missionDay']]
    mission['radiationEvents']=[dict(e,crewId=c['crewId']) for c in mission['crew'] for e in samples]
    p=config['stage']['simulation']['S3'];warning_hours=p['rise_hours']+p['decay_hours']
    intervals=merge([[s,s+warning_hours] for s in starts])
    held=merge([[a,(math.floor(b/24)+2)*24] for a,b in intervals])
    absolute=lambda e:(e['missionDay']-1)*24+e['timeHoursFromDayStart']
    checks={k:True for k in ('immediate_act','renewal_hold','clears','dose','no_rate_act_outside','critical_card_first_uncapped')}
    daily_error=max(abs(independent_dose(rows)-daily[d][0]) for d,rows in byday.items())
    total=sum(v[0] for v in daily.values());independent=sum(independent_dose(rows) for rows in byday.values())
    injected=total-180*config['signals']['daily_dose_msv']['sim_background'];cumulative_error=0.;onsets=[];clears=[];probes=0
    outside=[e for e in samples if not any(a<=absolute(e)<b for a,b in held)]
    policy=config['stage']['radiation'];checks['no_rate_act_outside']=not any(e['dose_rate_msv_h']>=policy['shelter_act_msv_h'] for e in outside)
    watches=[e for e in outside if policy['caution_watch_msv_h']<=e['dose_rate_msv_h']<policy['shelter_act_msv_h']]
    for crew in mission['crew']:
        cid=crew['crewId'];readings=[r for r in mission['readings'] if r['crewId']==cid];events=[e for e in mission['radiationEvents'] if e['crewId']==cid]
        def at(t):
            day=math.floor(t/24)+1
            return evaluate(readings,events,cid,day,config,as_of_hour=t-(day-1)*24)
        for m,start in zip(mapped,starts):
            first=next(e for e in samples if absolute(e)>=start);result=at(absolute(first));checks['immediate_act'] &= result['status']=='act'
            onsets.append({'crewId':cid,'onsetUtc':m['onsetUtc'],'missionDay':first['missionDay'],'hour':first['timeHoursFromDayStart'],'status':result['status']})
            routine=[{'moduleId':'sleep','status':'watch','cardId':'evaluation-routine'} for _ in range(8)];cards=select_cards(routine+[result],config)
            checks['critical_card_first_uncapped'] &= bool(cards) and cards[0] is result and len(cards)==1+min(8,config['rules']['card_cap']['routine_max'])
        for a,b in held:
            for e in samples:
                if a<=absolute(e)<b:
                    checks['renewal_hold'] &= at(absolute(e))['status']=='act';probes+=1
            result=at(b);checks['clears'] &= result['status']!='act';clears.append({'crewId':cid,'missionDay':int(b//24)+1,'hour':0,'status':result['status']})
        final=evaluate(readings,events,cid,180,config)
        observed=next(e['value'] for e in final['evidence'] if e.get('unit')=='mSv mission dose');cumulative_error=max(cumulative_error,abs(observed-independent))
        partial=copy.deepcopy(byday[60]);partial[len(partial)//2]['dose_rate_msv_h']=None;dose,coverage=integrate_day(partial)
        partial_result=evaluate([dict(r,daily_dose_msv=dose,dose_coverage=coverage) if r['missionDay']==60 else r for r in readings], [e for e in events if e['missionDay']!=60]+[dict(e,crewId=cid) for e in partial],cid,60,config)
        checks['dose'] &= coverage<1 and abs(dose-independent_dose(partial))<1e-6 and partial_result['dataQuality']=='suspect' and 'Partial dose coverage' in partial_result['reason']
    checks['dose'] &= daily_error<1e-6 and cumulative_error<1e-6 and abs(injected-19.5)<1e-6
    return {'window':window,'sourceSha256':digest,'mappedEpisodes':mapped,'surveyMatches':[m['onsetUtc'][5:16].replace('T',' ') for m in mapped]==EXPECTED[window], 'checks':checks,'onsetActSamples':onsets,'clearSamples':clears,'warningIntervalsMissionHours':intervals,'holdIntervalsMissionHours':held,'rawWarningHours':sum(b-a for a,b in intervals),'actHoldHours':sum(b-a for a,b in held),'holdSampleProbesAllCrew':probes,'dose':{'injectedMsv':injected,'totalMissionMsv':total,'dailyMaxError':daily_error,'cumulativeMaxError':cumulative_error,'partialCoverageChecked':True},'outsideWarningAndHoldRateWatchSamplesPerCrew':len(watches),'outsideWarningAndHoldRateWatchDaysPerCrew':len({e['missionDay'] for e in watches})},samples

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,default=Path('reports/donki_replay'));args=parser.parse_args();args.out.mkdir(parents=True,exist_ok=True)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    config,_,digest=read_frozen();quiet=generate_mission(0,config,[]);results=[]
    for window in WINDOWS:
        result,samples=run_window(window,config,quiet);results.append(result)
        x=[e['missionDay']+e['timeHoursFromDayStart']/24 for e in samples]
        fig,axes=plt.subplots(2,1,figsize=(11,5),sharex=True)
        axes[0].step(x,[int(e['spe_warning']) for e in samples],where='post',label='Raw warning')
        for a,b in result['holdIntervalsMissionHours']:axes[0].axvspan(a/24+1,b/24+1,alpha=.15,color='orange')
        axes[0].set_ylabel('Warning / act hold');axes[0].set_yticks([0,1]);axes[0].legend(loc='upper right')
        axes[1].plot(x,[e['dose_rate_msv_h'] for e in samples]);axes[1].set_ylabel('Assumed mSv/h');axes[1].set_xlabel('Mission day (UTC retained)')
        for key,color in [('caution_watch_msv_h','orange'),('shelter_act_msv_h','red')]:axes[1].axhline(config['stage']['radiation'][key],ls=':',color=color,label='Provisional '+key)
        axes[1].legend();axes[1].set_xlim(59,max(e['missionDay'] for e in result['mappedEpisodes'])+11)
        fig.suptitle(window+' · NASA timing; simulated dose / transit mapping');fig.tight_layout();fig.savefig(args.out/(window+'.png'),dpi=150);plt.close(fig)
    (args.out/'results.json').write_text(json.dumps({'wording':WORDING,'frozenConfigSha256':digest,'seed':0,'crewCount':4,'totalExtraDoseMsvPerWindow':19.5,'results':results},indent=2,allow_nan=False)+'\n')
    lines=['# DONKI radiation robustness replay','',WORDING+'.','','| Window | UTC onsets | Act samples (all crew) | Immediate | Renewal/hold | Clear | Dose | No outside rate act | Card | Warning / act hours | Extra mSv |','|---|---|---|---|---|---|---|---|---|---|---|']
    for r in results:
        cells=[r['window'],', '.join(m['onsetUtc'] for m in r['mappedEpisodes']),', '.join(f"D{m['missionDay']} {m['hour']:.4f}h" for m in r['onsetActSamples'] if m['crewId']=='C1')]+['PASS' if v else 'FAIL' for v in r['checks'].values()]+[f"{r['rawWarningHours']:.3f} / {r['actHoldHours']:.3f}",f"{r['dose']['injectedMsv']:.9f}"]
        lines.append('| '+' | '.join(cells)+' |')
    lines+=['','- All onsets flag immediately for all crew. Every retained sample throughout warning and hold is probed. May 2024 renews an already-active warning; orange plot shading includes procedure hold.', '- Dose is independently integrated daily and cumulatively, including missing-sample coverage. The assumed 19.5 mSv per window is split equally among episodes; NASA supplies timing only.', '- Outside warning plus procedure hold, provisional rate watches per crew (samples / distinct days): '+'; '.join(f"{r['window']}: {r['outsideWarningAndHoldRateWatchSamplesPerCrew']} / {r['outsideWarningAndHoldRateWatchDaysPerCrew']}" for r in results)+'. Survey differences: '+str([r['window'] for r in results if not r['surveyMatches']])+'.','','Checksum adapter note: a temporary manifest aliases each original research/checksums.sha256 source digest to the read-only adapter’s fixed 2017 key; actual source bytes are still verified. Source data and original checksum manifests remain unchanged.']
    (args.out/'summary.md').write_text('\n'.join(lines)+'\n');print(json.dumps({r['window']:r['checks'] for r in results},indent=2))
    if not all(all(r['checks'].values()) for r in results):raise SystemExit(1)

if __name__=='__main__':main()
