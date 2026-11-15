"""Fixed-parameter stage-1 candidates. These are synthetic experiment detectors."""
from dataclasses import dataclass, field
from typing import Literal
import math
import numpy as np
from scipy.stats import chi2
from sklearn.covariance import LedoitWolf
from sklearn.ensemble import IsolationForest
from ..baseline.fixed import usable
from ..modules.physiological import evaluate as m1_evaluate

@dataclass(frozen=True)
class DayResult:
    missionDay: int
    status: Literal['nominal','watch','act','unknown']
    evidence: list[dict]
    reason_key: str
    reason: str
    metrics: dict = field(default_factory=dict)

class Detector:
    def __init__(self, candidate):
        if candidate not in ('M0','M1','M1b','M2','M3','M4','M5','M6'):
            raise ValueError(f'Unknown candidate: {candidate}')
        self.candidate = candidate

    def detect(self, readings_for_one_crew, baseline, cfg):
        """Calendar days, locked preflight training, state reset on missing/suspect inputs.

        M0/M2/M3/M4: valid RHR + usable RHR baseline.
        M1: original at-least-two evaluable signals.
        M1b: valid RHR and at least one evaluable corroborating signal today.
        M5/M6: all three current signals and >= min_valid_days complete preflight rows.
        Red-flag symptoms override every candidate's unknown/watch/nominal state.
        """
        research = cfg['research']; stage = cfg['stage1']; params = stage[self.candidate]
        crew_ids={r['crewId'] for r in readings_for_one_crew}
        if len(crew_ids)!=1:raise ValueError('detect requires exactly one crew')
        crew_id=next(iter(crew_ids))
        by_day={r['missionDay']:r for r in readings_for_one_crew}
        if len(by_day)!=len(readings_for_one_crew):raise ValueError('Duplicate crew/day readings')
        if not any(d>0 for d in by_day):return []
        if stage['missing_state_policy']!='reset':raise ValueError('Unsupported missing-state policy')
        signals=stage['signals']
        def signal_evidence(row):
            out=[]
            for signal in signals:
                b=baseline[signal];v=row.get(signal) if row else None
                valid=b.quality=='valid' and usable(v,research['signals'][signal])
                e={'signalId':signal,'value':v,'unit':research['signals'][signal]['unit'],'evaluable':valid}
                if b.quality=='valid':e['baseline']=b.center
                if valid:e.update(z=(v-b.center)/b.scale,delta=v-b.center)
                out.append(e)
            return out
        def available(e):return {x['signalId']:x for x in e if x['evaluable']}
        # Fit once, using ONLY complete, plausible preflight vectors.
        estimator=None;threshold=None
        if self.candidate in ('M5','M6'):
            low,high=research['scenarios']['mission']['preflight_days']
            training=[r for r in readings_for_one_crew if low<=r['missionDay']<=high and len(available(signal_evidence(r)))==len(signals)]
            if len(training)>=research['rules']['baseline']['min_valid_days']:
                if self.candidate=='M5':
                    x=np.array([[(r[s]-baseline[s].center)/baseline[s].scale for s in signals] for r in training])
                    estimator=LedoitWolf(assume_centered=params['assume_centered']).fit(x)
                    threshold=float(chi2.ppf(params['quantile'],len(signals)))
                else:
                    x=np.array([[r[s] for s in signals] for r in training])
                    estimator=IsolationForest(**{k:params[k] for k in ('n_estimators','random_state','max_samples','contamination','n_jobs')}).fit(x)
                    threshold=float(np.percentile(estimator.score_samples(x),params['percentile']))
        out=[];run=0;cusum=0.0;ewma=0.0;nominal_days=0;window=[]
        for d in range(stage['mission_days'][0],max(day for day in by_day if day>0)+1):
            row=by_day.get(d);evidence=signal_evidence(row);a=available(evidence)
            collected=bool(row and row['checkin_completed'])
            symptoms=row['symptoms'] if collected else []
            red=[s for s in symptoms if s in research['rules']['physiological_change']['symptom_only']['red_flag']]
            if self.candidate=='M1':
                result=m1_evaluate(readings_for_one_crew,crew_id,d,research,baseline)
                out.append(DayResult(d,result['status'],result['evidence'],'M1_'+result['status'],result['reason']))
                continue
            enough='rhr_bpm' in a
            if self.candidate=='M1b':enough=enough and any(s in a for s in signals if s!='rhr_bpm')
            if self.candidate in ('M5','M6'):enough=len(a)==len(signals) and estimator is not None
            metrics={};watch=False;reason_key='nominal'
            if not enough:
                status='unknown';reason_key='unknown_inputs'
                run=0;cusum=ewma=0.0;nominal_days=0;window=[]
            else:
                z=a['rhr_bpm']['z'];rhr=a['rhr_bpm']['value']
                if self.candidate=='M0':
                    run=run+1 if rhr>=params['rhr_bpm'] else 0
                    watch=run>=params['consecutive_days'];metrics={'threshold_bpm':params['rhr_bpm'],'consecutive':run}
                elif self.candidate=='M1b':
                    corroboration=any((-a[s]['z'] if s=='hrv_rmssd_ms' else a[s]['z'])>params['corroborating_z'] for s in ('hrv_rmssd_ms','skin_temp_delta_c') if s in a)
                    window.append((z>params['rhr_z'],corroboration));window=window[-params['consecutive_days']:]
                    watch=len(window)==params['consecutive_days'] and all(x[0] for x in window) and any(x[1] for x in window)
                    metrics={'rhr_threshold_z':params['rhr_z'],'corroborating_threshold_z':params['corroborating_z'],'window_days':len(window),'corroborated':any(x[1] for x in window)}
                elif self.candidate=='M2':
                    cusum=max(0.0,cusum+z-params['k']);watch=cusum>params['h']
                    metrics={'cusum':cusum,'threshold':params['h']}
                    nominal_days=0 if watch else nominal_days+1
                    if nominal_days>=params['nominal_reset_days']:
                        cusum=0.0;nominal_days=0;metrics['reset_after_today']=True
                elif self.candidate=='M3':
                    lam=params['lambda'];ewma=lam*z+(1-lam)*ewma
                    control=params['control_sigma']*math.sqrt(lam/(2-lam))
                    watch=ewma>control;metrics={'ewma':ewma,'threshold':control}
                elif self.candidate=='M4':
                    delta=a['rhr_bpm']['delta'];run=run+1 if delta>=params['watch_delta_bpm'] else 0
                    watch=run>=params['consecutive_days']
                    metrics={'delta_bpm':delta,'threshold_delta_bpm':params['watch_delta_bpm'],'consecutive':run,'yellow_info_only':delta>=params['yellow_delta_bpm']}
                elif self.candidate=='M5':
                    vector=np.array([a[s]['z'] for s in signals]);delta=vector-estimator.location_
                    distance=float(delta@estimator.precision_@delta)
                    run=run+1 if z>0 and distance>threshold else 0
                    watch=run>=params['consecutive_days'];metrics={'distance_squared':distance,'threshold':threshold,'consecutive':run}
                elif self.candidate=='M6':
                    score=float(estimator.score_samples(np.array([[a[s]['value'] for s in signals]]))[0])
                    run=run+1 if score<threshold else 0
                    watch=run>=params['consecutive_days'];metrics={'score':score,'threshold':threshold,'consecutive':run}
                status='watch' if watch else 'nominal';reason_key='watch_'+self.candidate if watch else 'nominal'
            if red:status='act';reason_key='red_flag_symptom'
            details=[]
            for e in evidence:
                if e['evaluable']:
                    details.append(f"{e['signalId']}={e['value']:.3f} {e['unit']}; baseline={e['baseline']:.3f}; delta={e['delta']:+.3f}; z={e['z']:+.3f}")
                else:details.append(f"{e['signalId']}: missing, implausible or baseline insufficient")
            reason=self.candidate+' / '+reason_key+'; '+' | '.join(details)
            if metrics:reason+='; statistic='+str(metrics)
            if red:reason+='; reported red-flag symptoms: '+', '.join(red)
            reason+='; '+('symptom check-in not collected' if not collected else 'symptoms logged: '+', '.join(symptoms) if symptoms else 'no symptoms reported')
            if 'rhr_bpm' in a and 'hrv_rmssd_ms' in a:reason+='; RHR and HRV share a wearable source; deviations are not independent confirmations'
            if self.candidate in ('M5','M6'):reason+='; feature deviations are descriptive, not causal attribution'
            out.append(DayResult(d,status,evidence,reason_key,reason,metrics))
        return out

def get_detector(candidate):
    return Detector(candidate)
