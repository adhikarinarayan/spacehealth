"""Locked baseline eligibility, causal frozen M3 call and participant metrics."""
import numpy as np
import pandas as pd
from ..baseline.fixed import fit_baselines,usable
from ..detectors.candidates import get_detector

BOOTSTRAP_SEED=20261115
BOOTSTRAP_SAMPLES=5000

def baseline_window(nightly,config,onset=None):
    if nightly.empty:return None,'empty HR record'
    if onset is not None:
        if len(nightly)<14:return None,'record shorter than first 14 calendar nights'
        selected=nightly.iloc[:14]
        if selected.index[-1]>onset-pd.Timedelta(days=7):return None,'first 14 calendar nights end after symptom day -7'
        count=sum(usable(None if pd.isna(v) else float(v),config['signals']['rhr_bpm']) for v in selected.rhr_bpm)
        if count<config['rules']['baseline']['min_valid_days']:return None,'fewer than 10 valid baseline nights among first 14 calendar nights'
    else:
        selected=nightly[[usable(None if pd.isna(v) else float(v),config['signals']['rhr_bpm']) for v in nightly.rhr_bpm]].iloc[:14]
        if len(selected)<14:return None,'fewer than 14 valid baseline nights for no-reported-illness control'
    return selected,''

def detect_frozen(nightly,baseline,config,participant):
    end=baseline.index[-1]
    def row(day,value):return {'crewId':participant,'missionDay':day,'rhr_bpm':None if pd.isna(value) else float(value),'hrv_rmssd_ms':None,'skin_temp_delta_c':None,'sleep_hours':None,'checkin_completed':False,'symptoms':[]}
    training=[row(day,value) for day,value in zip(range(-14,0),baseline.rhr_bpm)]
    future=nightly.loc[nightly.index>end]
    rows=training+[row((date-end).days,value) for date,value in future.rhr_bpm.items()]
    fixed=fit_baselines(rows,participant,config)
    # Pass the original frozen parameter dictionary unchanged. No M5, symptoms,
    # HRV or temperature are invented from this RHR-only source.
    results=get_detector('M3').detect(rows,fixed,{'research':config,'stage1':config['_production']})
    data=[{'date':end+pd.Timedelta(days=r.missionDay),'status':r.status,'ewma':r.metrics.get('ewma',np.nan),'threshold':r.metrics.get('threshold',np.nan)} for r in results]
    frame=pd.DataFrame(data,columns=['date','status','ewma','threshold']).set_index('date')
    frame.index=pd.DatetimeIndex(frame.index)
    return frame,fixed['rhr_bpm']

def episodes(statuses):
    previous=False;count=0
    for status in statuses:
        flagged=status in ('watch','act')
        if flagged and not previous:count+=1
        previous=flagged
    return count

def participant_metrics(nightly,detected,onset=None):
    if onset is None:
        pre=detected;first=None;window_valid=None;early=None
    else:
        relative=(detected.index-onset).days;window=detected[(relative>=-7)&(relative<=7)]
        watches=window[window.status=='watch']
        first=int((watches.index[0]-onset).days) if len(watches) else None
        early=bool(len(watches) and first<=0);window_valid=int((window.status!='unknown').sum())
        pre=detected[relative<-7]
    evaluable=int((pre.status!='unknown').sum())
    return {'detected':first is not None if onset is not None else None,'detected_by_day0':early,'first_watch_relative_day':first,'detection_window_valid_nights':window_valid,
            'false_alert_episodes':episodes(pre.status),'false_alert_person_nights':evaluable,'false_alert_calendar_nights':len(pre),'false_watch_nights':int((pre.status=='watch').sum()),
            'false_alert_episodes_per100':100*episodes(pre.status)/evaluable if evaluable else None}

def bootstrap(rows,numerator,denominator=None):
    """Participant-block percentile CI; ratios use resampled summed person-nights."""
    if not rows:return {'estimate':None,'ci95':[None,None],'participants':0}
    a=np.array([float(r[numerator]) for r in rows]);b=np.array([float(r[denominator]) for r in rows]) if denominator else None
    rng=np.random.default_rng(BOOTSTRAP_SEED);indexes=rng.integers(0,len(rows),size=(BOOTSTRAP_SAMPLES,len(rows)))
    if b is None:estimate=float(a.mean());samples=a[indexes].mean(axis=1)
    else:
        if b.sum()==0:return {'estimate':None,'ci95':[None,None],'participants':len(rows)}
        estimate=float(100*a.sum()/b.sum());totals=b[indexes].sum(axis=1);sums=a[indexes].sum(axis=1)
        samples=100*sums[totals>0]/totals[totals>0]
    return {'estimate':estimate,'ci95':[float(x) for x in np.quantile(samples,[.025,.975])],'participants':len(rows)}
