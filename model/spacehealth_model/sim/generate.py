"""Seeded synthetic missions; never use scenario truth inside a detector."""
from datetime import datetime, timezone
import math
import numpy as np
from .radiation import integrate_day, sample_times

def generate_mission(seed, config, enabled=None):
    sc = config['scenarios']['scenarios']
    enabled = set(sc) if enabled is None else set(enabled) | {'S1'}
    if enabled-set(sc): raise ValueError('Unknown scenario toggle')
    setup = config['scenarios']['mission']
    prelo,prehi = setup['preflight_days']; lo,hi = setup['mission_days']
    days = [*range(prelo,prehi+1),*range(lo,hi+1)]
    signals = config['signals']
    params = config['stage']['simulation']
    streams = np.random.SeedSequence(seed).spawn(len(setup['crew'])+1)
    effect_rng = np.random.default_rng(streams[-1])
    readings=[]; crew=[]
    for crew_id,stream in zip(setup['crew'],streams):
        rng=np.random.default_rng(stream)
        center={s:float(rng.uniform(*signals[s]['sim_person_baseline_range'])) for s in ('rhr_bpm','hrv_rmssd_ms','sleep_hours')}
        center['skin_temp_delta_c']=signals['skin_temp_delta_c']['sim_person_baseline']
        crew.append({'crewId':crew_id,'label':crew_id,'prior_career_dose_msv':None})
        for day in days:
            r={'crewId':crew_id,'missionDay':day,'symptoms':[],'checkin_completed':True,'daily_dose_msv':None,'dose_coverage':None}
            for signal in center:
                spec=signals[signal]
                sd=spec.get('sim_day_to_day_sd',center[signal]*spec.get('sim_day_to_day_cv',0))
                noise=params['noise']
                if noise['distribution']=='gaussian':value=rng.normal(center[signal],sd)
                elif noise['distribution']=='student_t':
                    df=noise['student_t_df']
                    if df<=2:raise ValueError('Student-t df must exceed 2 for SD scaling')
                    value=center[signal]+sd*rng.standard_t(df)/math.sqrt(df/(df-2))
                else:raise ValueError('Unsupported noise distribution')
                r[signal]=float(value)
            r['provenance']={s:'synthetic' for s in [*center,'symptoms','daily_dose_msv']}
            readings.append(r)
    if 'S2' in enabled:
        event=sc['S2']; own=[r for r in readings if r['crewId']==event['crew'] and r['missionDay']<0]
        effects={'rhr_bpm':params['S2']['rhr_delta_bpm']}
        for signal in ('hrv_rmssd_ms','skin_temp_delta_c'):
            sd=float(np.std([r[signal] for r in own],ddof=1))
            units=params['S2']['hrv_delta_sd_range' if signal=='hrv_rmssd_ms' else 'temperature_delta_sd_range']
            magnitude=effect_rng.uniform(*sorted(abs(x) for x in units))*sd
            effects[signal]=(-1 if signal=='hrv_rmssd_ms' else 1)*magnitude
        ramp=config['stage']['s2_shape']['ramp_days']; recovery=config['stage']['s2_shape']['recovery_days']
        for r in readings:
            d=r['missionDay']
            if r['crewId']!=event['crew'] or not event['onsetDay']<=d<=event['endDay']:continue
            factor=min(1.0,(d-event['onsetDay']+1)/ramp,max(0.0,(event['endDay']-d)/recovery))
            for signal,delta in effects.items():r[signal]+=float(delta)*factor
            if event['symptomDay']<=d<event['endDay']:r['symptoms']=list(params['S2']['symptoms'])
    if 'S4' in enabled:
        event=sc['S4']; low,high=params['S4']['sleep_hours_range']
        for r in readings:
            if r['crewId']==event['crew'] and event['onsetDay']<=r['missionDay']<=event['endDay']:
                r['sleep_hours']=float(effect_rng.uniform(min(low,high),max(low,high)))
    if 'N1' in enabled:
        event=sc['N1']; delta=params['N1']['rhr_delta_bpm_range']; selected=params['N1']['days']
        for r in readings:
            if r['crewId']==event['crew'] and r['missionDay'] in selected:
                r['rhr_bpm']+=float(effect_rng.uniform(float(delta[0]),float(delta[1])))
    if 'N2' in enabled:
        event=sc['N2']; valid_days=params['N2']['valid_preflight_hrv_days']
        gap=params['N2']['wearable_gap_days']; skip=params['N2']['skipped_checkin_days']
        preflight=[r for r in readings if r['crewId']==event['crew'] and r['missionDay']<0]
        for r in preflight[valid_days:]:r['hrv_rmssd_ms']=None
        for r in readings:
            if r['crewId']!=event['crew']:continue
            if gap[0]<=r['missionDay']<=gap[1]:
                for signal in config['rules']['physiological_change']['signals']:r[signal]=None
            if skip[0]<=r['missionDay']<=skip[1]:r['checkin_completed']=False;r['symptoms']=[]
    # Common radiation profile sampled separately for each day, then assigned to each crew.
    from .space_weather import make_radiation
    samples,daily,timing_source=make_radiation(days,config,'S3' in enabled)
    events=[]
    for r in readings:
        r['daily_dose_msv'],r['dose_coverage']=daily[r['missionDay']]
        events.extend({'crewId':r['crewId'],'missionDay':r['missionDay'],**sample} for sample in samples[r['missionDay']])
    truth=[]
    for sid in sorted(enabled):
        event=sc[sid]
        targets=setup['crew'] if event.get('crew','all')=='all' else [event['crew']]
        for crew_id in targets:
            truth.append({'scenarioId':sid,'crewId':crew_id,'moduleId':event.get('moduleId','physiological_change' if sid in ('N1','N2') else None), 'onsetDay':event.get('onsetDay'), 'symptomDay':event.get('symptomDay'), 'endDay':event.get('endDay'),'description':event.get('what',sid+' synthetic scenario')})
    p=config['stage']['profile']
    return {'schemaVersion':'0.2.0','simulated':True,'generator':'spacehealth-M1-stage0','seed':seed,
        'createdAt':datetime.now(timezone.utc).isoformat(),
        'missionProfile':{'id':setup['profile'],'label':p['label'],'durationDays':hi,'gcr_background_msv_day':signals['daily_dose_msv']['sim_background'],'comms_one_way_delay_min':p['comms_one_way_delay_min'],'blackouts':p['blackouts'],'spe_event_timing_source':timing_source},
        'crew':crew,'readings':readings,'radiationEvents':events,'truth':truth}
