"""Synthetic dose pulses driven by verified NASA timing or the legacy switch."""
import math
from .radiation import sample_times,integrate_day
from ..data_sources.donki import timing

def make_radiation(days,config,enabled):
    storm=config['scenarios']['scenarios']['S3'];stage=config['stage'];mode=stage['s3_timing']
    legacy=stage['s3_legacy'];pulse=stage['simulation']['S3'];rise=pulse['rise_hours'];decay=pulse['decay_hours']
    duration=pulse['duration_days']*24
    total=pulse['total_extra_dose_msv']
    if mode=='donki':mapped,source=timing(storm['onsetDay'],config=config)
    elif mode=='synthetic':
        mapped=[{'missionDay':storm['onsetDay'],'timeHoursFromDayStart':legacy['warning_hour']}]
        source='Synthetic S3 timing (legacy): day 72 06:00; dose from Zeitlin2013 Table 1'
    else:raise ValueError('s3_timing must be donki or synthetic')
    starts=[(m['missionDay']-1)*24+m['timeHoursFromDayStart'] for m in mapped] if enabled else []
    shape=lambda elapsed:0. if elapsed<0 or elapsed>=duration else elapsed/rise if elapsed<rise else math.exp(-(elapsed-rise)/decay)
    grid={}
    for d in days:
        active=any((d-1)*24+24>s and (d-1)*24<s+duration for s in starts)
        interval=stage['sampling']['event_interval_hours' if active else 'background_interval_hours']
        times=set(sample_times(interval))
        # Include exact real onsets and policy/rise/end boundaries, not rounded grid times.
        if mode=='donki':
            for start in starts:
                for boundary in (start,start+rise,start+rise+decay,start+duration):
                    t=boundary-(d-1)*24
                    if 0<=t<24:times.add(t)
        grid[d]=sorted(times)
    areas=[]
    for start in starts:
        areas.append(sum(integrate_day([{'timeHoursFromDayStart':t,'dose_rate_msv_h':shape((d-1)*24+t-start)} for t in times])[0] or 0 for d,times in grid.items()))
    if any(a<=0 for a in areas):raise ValueError('Pulse has no sampled dose support')
    background=config['signals']['daily_dose_msv']['sim_background']/24
    samples={};daily={}
    for d,times in grid.items():
        rows=[]
        for t in times:
            absolute=(d-1)*24+t
            extra=sum(shape(absolute-start)*total/len(starts)/area for start,area in zip(starts,areas))
            warning=any(0<=absolute-start<rise+decay for start in starts)
            rows.append({'timeHoursFromDayStart':t,'dose_rate_msv_h':background+extra,'spe_warning':warning})
        samples[d]=rows;daily[d]=integrate_day(rows)
    return samples,daily,source
