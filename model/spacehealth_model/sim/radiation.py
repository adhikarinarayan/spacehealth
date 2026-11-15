"""Within-day trapezoids, never fill a null sample with zero."""
import math
import numpy as np

def integrate_day(samples):
    ordered = sorted(samples, key=lambda e:e['timeHoursFromDayStart'])
    times = [e['timeHoursFromDayStart'] for e in ordered]
    if len(times) != len(set(times)):
        raise ValueError('Duplicate radiation timestamps')
    if any(not math.isfinite(t) or not 0 <= t < 24 for t in times):
        raise ValueError('Invalid radiation timestamp')
    dose = hours = 0.0
    for a,b in zip(ordered,ordered[1:]):
        va,vb = a['dose_rate_msv_h'],b['dose_rate_msv_h']
        if va is None or vb is None:
            continue
        if not all(math.isfinite(v) and v >= 0 for v in (va,vb)):
            raise ValueError('Invalid radiation rate')
        dt=b['timeHoursFromDayStart']-a['timeHoursFromDayStart']
        dose += dt*(va+vb)/2
        hours += dt
    # nextafter(24,0) represents the right boundary within one floating-point ULP.
    # Normalize only that numerical full-day boundary; real gaps remain partial.
    coverage = hours/24
    if times and times[0] == 0 and times[-1] == math.nextafter(24.0,0.0) and abs(hours-24) <= math.ulp(24.0):
        coverage = 1.0
    return (dose if hours else None), coverage

def dose_total(readings):
    values=[r['daily_dose_msv'] for r in readings if r['missionDay']>0]
    return {'observed_mission_dose_msv':sum(v for v in values if v is not None),
            'complete':all(r['daily_dose_msv'] is not None and math.isclose(r['dose_coverage'] or 0,1,abs_tol=1e-12) for r in readings if r['missionDay']>0)}

def sample_times(step):
    if not math.isfinite(step) or step <= 0:
        raise ValueError('Sample interval must be positive')
    return [*np.arange(0,24,step).tolist(), float(np.nextafter(24.0,0.0))]
