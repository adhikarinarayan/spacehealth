"""Warning/provisional rate policy and explicitly incomplete dose accounting."""
import math
from ..sim.radiation import integrate_day

def evaluate(readings,events,crew_id,day,config,*,prior_career_dose_msv=None,as_of_hour=None):
    if day<1:raise ValueError('Radiation evaluation requires a mission day')
    if as_of_hour is not None and not 0<=as_of_hour<24:raise ValueError('Intraday time must be in [0,24)')
    policy=config['stage']['radiation']
    if policy['placeholder'] is not True:raise ValueError('Dose-rate thresholds must remain explicitly provisional')
    rows={r['missionDay']:r for r in readings if r['crewId']==crew_id and 1<=r['missionDay']<=day}
    samples=sorted((e for e in events if e['crewId']==crew_id and 1<=e['missionDay']<=day and (e['missionDay']<day or as_of_hour is None or e['timeHoursFromDayStart']<=as_of_hour)),key=lambda e:(e['missionDay'],e['timeHoursFromDayStart']))
    current=[e for e in samples if e['missionDay']==day]
    latest=current[-1] if current else None
    rate=latest['dose_rate_msv_h'] if latest else None
    last_warning=next((i for i in range(len(samples)-1,-1,-1) if samples[i]['spe_warning']),None)
    warning=False;clear_day=None
    if last_warning is not None:
        clear=next((e for e in samples[last_warning+1:] if not e['spe_warning']),None)
        clear_day=clear['missionDay'] if clear else None
        warning=clear is None or day<=clear_day+1
    if as_of_hour is not None:
        today_dose,coverage=integrate_day(current)
    else:
        today_dose=rows.get(day,{}).get('daily_dose_msv');coverage=rows.get(day,{}).get('dose_coverage')
    observed=0.;partial=False;missing=False
    for d in range(1,day+1):
        dose,cov=(today_dose,coverage) if d==day else (rows.get(d,{}).get('daily_dose_msv'),rows.get(d,{}).get('dose_coverage'))
        if dose is None:missing=True
        else:observed+=dose
        if cov is None or cov<1:partial=True
    background=config['signals']['daily_dose_msv']['sim_background']
    duration=config['scenarios']['mission']['mission_days'][1]
    remaining=duration-day+(1-as_of_hour/24 if as_of_hour is not None else 0)
    projection=observed+remaining*background
    career_projection=projection+prior_career_dose_msv if prior_career_dose_msv is not None else None
    limit=config['signals']['prior_career_dose_msv']['career_limit']
    budget=(career_projection if career_projection is not None else projection)>=limit
    act_rate=rate is not None and rate>=policy['shelter_act_msv_h']
    watch_rate=rate is not None and rate>=policy['caution_watch_msv_h']
    status='nominal';card=None;reason='No configured radiation rule triggered.'
    if warning or act_rate:status='act';card='radiation-spe-procedure'
    elif watch_rate or budget:status='watch';card='radiation-budget'
    elif missing or latest is None or rate is None:status='unknown'
    quality='missing' if status=='unknown' else 'suspect' if partial or missing or rate is None else 'valid'
    if warning:
        reason=config['cards'][card]['why'].format(rate_text=f' (observed dose rate {rate:.4f} mSv/h)' if rate is not None else '')
        if clear_day is not None:reason+=f' Warning cleared on day {clear_day}; one-day procedure hold remains active.'
    elif act_rate or watch_rate:
        reason=f'Dose rate {rate:.4f} mSv/h exceeds a placeholder threshold (mission-specific values not public).'
    elif budget:
        c=config['cards'][card]
        career_text=f'; prior career dose {prior_career_dose_msv:.2f} mSv' if prior_career_dose_msv is not None else '; career total unknown'
        reason=c['why'].format(mission_dose=f'{observed:.2f}',career_text=career_text,pct=f'{100*((observed+prior_career_dose_msv) if prior_career_dose_msv is not None else observed)/limit:.1f}')
        reason+=f' Projected total at mission end {(career_projection if career_projection is not None else projection):.2f} mSv.'
    elif status=='unknown':reason='Radiation readings or dose history are missing; no reliable complete assessment.'
    if (act_rate or watch_rate) and 'placeholder threshold' not in reason:reason+=' Dose rate also crosses a placeholder threshold (mission-specific values not public).'
    if prior_career_dose_msv is None:reason+=' '+config['rules']['radiation']['career_unknown']
    if partial or missing:reason+=' Partial dose coverage: observed totals are incomplete, not a complete exposure history.'
    evidence=[{'signalId':'spe_warning','value':latest['spe_warning'] if latest else None}, {'signalId':'dose_rate_msv_h','value':rate,'unit':'mSv/h'},
              {'signalId':'daily_dose_msv','value':today_dose,'unit':f'mSv today; coverage {coverage if coverage is not None else "unknown"}'},
              {'signalId':'daily_dose_msv','value':observed,'unit':'mSv observed mission dose (partial)' if partial or missing else 'mSv mission dose'},
              {'signalId':'daily_dose_msv','value':projection,'unit':'mSv projected mission dose; partial inputs' if partial or missing else 'mSv projected mission dose'},
              {'signalId':'prior_career_dose_msv','value':prior_career_dose_msv,'unit':'mSv prior career dose'}]
    result={'crewId':crew_id,'missionDay':day,'moduleId':'radiation','status':status,'dataQuality':quality,'reason':reason,'evidence':evidence,'sourceIds':['NASA-STD-3001-V1C','Zeitlin2013'],'assumptionIds':['A8']}
    if card:result['cardId']=card
    return result
