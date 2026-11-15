import copy
import math
import numpy as np
import pytest
from spacehealth_model.baseline.fixed import Baseline,fit_baselines
from spacehealth_model.compare import load_stage1,run_comparison
from spacehealth_model.detectors.candidates import get_detector
from spacehealth_model.evaluate.metrics import CANDIDATES,summarize,candidate_metrics

@pytest.fixture(scope='module')
def cfg():return load_stage1()

def baselines(cfg):
    return {'rhr_bpm':Baseline(60.,1.5,14,'valid'),'hrv_rmssd_ms':Baseline(50.,5.,14,'valid'),'skin_temp_delta_c':Baseline(0.,.1,14,'valid'),'sleep_hours':Baseline(7.,.3,14,'valid')}

def series(days=6):
    rows=[]
    for day in range(-14,0):
        rows.append({'crewId':'C1','missionDay':day,'rhr_bpm':60+math.sin(day),'hrv_rmssd_ms':50+math.cos(2*day),'skin_temp_delta_c':.05*math.sin(3*day),'sleep_hours':7.,'symptoms':[],'checkin_completed':True})
    for day in range(1,days+1):rows.append({'crewId':'C1','missionDay':day,'rhr_bpm':60.,'hrv_rmssd_ms':50.,'skin_temp_delta_c':0.,'sleep_hours':7.,'symptoms':[],'checkin_completed':True})
    return rows

@pytest.mark.parametrize('candidate,values,trigger,status',[
 ('M0',{'rhr_bpm':75.},2,'watch'),
 ('M1',{'rhr_bpm':66.,'skin_temp_delta_c':.4},2,'act'),
 ('M1b',{'rhr_bpm':66.,'hrv_rmssd_ms':44.},2,'watch'),
 ('M2',{'rhr_bpm':63.},3,'watch'),
 ('M3',{'rhr_bpm':63.},4,'watch'),
 ('M4',{'rhr_bpm':64.},2,'watch'),
 ('M5',{'rhr_bpm':120.,'hrv_rmssd_ms':10.,'skin_temp_delta_c':2.},2,'watch'),
])
def test_known_trigger_day(candidate,values,trigger,status,cfg):
    rows=series()
    for row in rows:
        if row['missionDay']>0:row.update(values)
    result=get_detector(candidate).detect(rows,baselines(cfg),cfg)
    assert next(r.missionDay for r in result if r.status in ('watch','act'))==trigger
    assert result[trigger-1].status==status

@pytest.mark.parametrize('candidate',CANDIDATES)
def test_no_future_leakage(candidate,cfg):
    rows=series()
    for row in rows:
        if row['missionDay']>0:row.update(rhr_bpm=66.,hrv_rmssd_ms=44.,skin_temp_delta_c=.3)
    before=get_detector(candidate).detect(rows,baselines(cfg),cfg)
    changed=copy.deepcopy(rows)
    for row in changed:
        if row['missionDay']>3:row.update(rhr_bpm=None,hrv_rmssd_ms=None,skin_temp_delta_c=None,symptoms=['fever'])
    after=get_detector(candidate).detect(changed,baselines(cfg),cfg)
    prefix=get_detector(candidate).detect([r for r in rows if r['missionDay']<=3],baselines(cfg),cfg)
    assert before[:3]==after[:3]==prefix

@pytest.mark.parametrize('candidate',CANDIDATES)
def test_missing_current_inputs_unknown_and_reset(candidate,cfg):
    rows=series()
    for row in rows:
        if row['missionDay']>0:row.update(rhr_bpm=66.,skin_temp_delta_c=.3)
        if row['missionDay']==2:row.update(rhr_bpm=None,hrv_rmssd_ms=None,skin_temp_delta_c=None)
    result=get_detector(candidate).detect(rows,baselines(cfg),cfg)
    assert result[1].status=='unknown'
    if candidate in ('M0','M1','M1b','M4','M5','M6'):assert result[2].status=='nominal'

@pytest.mark.parametrize('candidate',CANDIDATES)
def test_deterministic(candidate,cfg):
    rows=series();b=baselines(cfg)
    assert get_detector(candidate).detect(rows,b,cfg)==get_detector(candidate).detect(rows,b,cfg)

@pytest.mark.parametrize('candidate',CANDIDATES)
def test_red_flag_override_and_skipped_checkin(candidate,cfg):
    rows=series()
    for row in rows:
        if row['missionDay']==1:row.update(rhr_bpm=None,hrv_rmssd_ms=None,skin_temp_delta_c=None,symptoms=['chest_pain'])
        if row['missionDay']==2:row.update(checkin_completed=False,symptoms=[])
    result=get_detector(candidate).detect(rows,baselines(cfg),cfg)
    assert result[0].status=='act'
    assert 'not collected' in result[1].reason.lower()
    assert 'no symptoms' not in result[1].reason.lower()

@pytest.mark.parametrize('candidate',['M0','M1b','M2','M3','M4','M5','M6'])
def test_required_baseline_insufficient(candidate,cfg):
    b=baselines(cfg);b['rhr_bpm']=Baseline(None,None,8,'insufficient')
    assert all(r.status=='unknown' for r in get_detector(candidate).detect(series(),b,cfg))

def test_m1b_corroboration_on_either_night_and_strict_threshold(cfg):
    rows=series(2)
    rows[-2].update(rhr_bpm=64.,hrv_rmssd_ms=44.)
    rows[-1].update(rhr_bpm=64.)
    assert get_detector('M1b').detect(rows,baselines(cfg),cfg)[-1].status=='watch'
    rows[-1]['rhr_bpm']=63. # exactly z=2, not beyond
    assert get_detector('M1b').detect(rows,baselines(cfg),cfg)[-1].status=='nominal'

def test_m4_yellow_is_information_only(cfg):
    rows=series(2)
    for row in rows[-2:]:row['rhr_bpm']=63.
    result=get_detector('M4').detect(rows,baselines(cfg),cfg)
    assert all(r.status=='nominal' and r.metrics['yellow_info_only'] for r in result)

def test_m2_nominal_reset_convention(cfg):
    rows=series(4)
    for row in rows[-4:]:row['rhr_bpm']=61.5 # z=1, three pre-threshold days reset S
    result=get_detector('M2').detect(rows,baselines(cfg),cfg)
    assert [r.metrics['cusum'] for r in result]==[.5,1.,1.5,.5]
    assert result[2].metrics['reset_after_today']

def test_m5_rhr_positive_gate(cfg):
    rows=series(2)
    for row in rows[-2:]:row.update(rhr_bpm=55.,hrv_rmssd_ms=10.,skin_temp_delta_c=2.)
    assert all(r.status=='nominal' for r in get_detector('M5').detect(rows,baselines(cfg),cfg))

def test_m5_m6_insufficient_complete_preflight_vectors(cfg):
    rows=series()
    for row in rows[:6]:row['hrv_rmssd_ms']=None
    for candidate in ('M5','M6'):assert all(r.status=='unknown' for r in get_detector(candidate).detect(rows,baselines(cfg),cfg))

def test_discard_rule_is_mechanical(cfg):
    prototype={'candidate':'M0','s2_detected_by_day42':False,'n1_any_act':False,'n2_gap_all_unknown':True,'explanation_available':True,'evaluable_crew_days':100,'routine_false_alerts':0,'s2_first_watch_day':None,'n1_watch_days':[],'n1_act_days':[],'n2_skipped_checkins_explicit':True}
    rows=[dict(prototype,seed=i) for i in [0,1,2]]
    result=summarize(rows,cfg)[0]
    assert result['verdict']=='discarded'
    assert result['discard_reasons']==['S2 missed by symptom day in 3/3 seeds']
    for row in rows:row['s2_detected_by_day42']=True
    assert summarize(rows,cfg)[0]['verdict']=='kept for next-stage review'

@pytest.mark.parametrize('seeds',[[1000,1001,1002],[0,0,1],[0],[0,1,3]])
def test_cli_rejects_holdout_and_seed_search(seeds,tmp_path):
    with pytest.raises(ValueError,match='exactly development seeds'):run_comparison(seeds,tmp_path)

def test_m6_known_score_trigger_and_percentile_boundary(cfg,monkeypatch):
    # Controlled estimator isolates threshold/persistence logic from tree geometry.
    class Scores:
        def __init__(self,**kwargs): pass
        def fit(self,x):return self
        def score_samples(self,x):return np.where(x[:,0]>=100,-1.,-.5)
    monkeypatch.setattr('spacehealth_model.detectors.candidates.IsolationForest',Scores)
    rows=series(3)
    rows[-3]['rhr_bpm']=100.;rows[-2]['rhr_bpm']=100.
    result=get_detector('M6').detect(rows,baselines(cfg),cfg)
    assert [r.status for r in result]==['nominal','watch','nominal']
    assert result[0].metrics['threshold']==-.5

def test_m6_real_estimator_matches_independent_score_computation(cfg):
    from sklearn.ensemble import IsolationForest
    rows=series(2);b=baselines(cfg);params=cfg['stage1']['M6']
    rows[-2].update(rhr_bpm=120.,hrv_rmssd_ms=10.,skin_temp_delta_c=2.)
    rows[-1].update(rhr_bpm=120.,hrv_rmssd_ms=10.,skin_temp_delta_c=2.)
    signals=cfg['stage1']['signals']
    training=np.array([[r[s] for s in signals] for r in rows if r['missionDay']<0])
    model=IsolationForest(**{k:params[k] for k in ('n_estimators','random_state','max_samples','contamination','n_jobs')}).fit(training)
    threshold=float(np.percentile(model.score_samples(training),params['percentile']))
    score=float(model.score_samples(np.array([[rows[-1][s] for s in signals]]))[0])
    result=get_detector('M6').detect(rows,b,cfg)
    assert result[-1].metrics['threshold']==threshold
    assert result[-1].metrics['score']==score
    assert result[-1].status==('watch' if score<threshold else 'nominal')


def test_stage2_episode_count_breaks_on_unknown_and_calendar_gap():
    from spacehealth_model.detectors.candidates import DayResult
    from spacehealth_model.evaluate.stage2 import episode_count
    rows=[DayResult(d,status,[],'test','test') for d,status in [(1,'watch'),(2,'watch'),(3,'unknown'),(4,'watch'),(6,'watch'),(7,'nominal'),(8,'act')]]
    assert episode_count(rows)==4

def test_stage2_parameters_match_stage1_and_bootstrap_is_seed_deterministic():
    from spacehealth_model.evaluate.stage2 import load_stage2,bootstrap_ci
    from spacehealth_model.compare import load_stage1
    cfg=load_stage2();old=load_stage1()
    for c in cfg['stage2']['candidates']:assert cfg['stage1'][c]==old['stage1'][c]
    rows=[{'detected':True,'alerts':2,'days':100},{'detected':False,'alerts':0,'days':50}]
    assert bootstrap_ci(rows,'detected',samples=100,seed=0)==bootstrap_ci(rows,'detected',samples=100,seed=0)
    lo,hi=bootstrap_ci(rows,None,'alerts','days',samples=100,seed=0)
    assert lo==0 and hi==2

@pytest.mark.parametrize('seeds',[[1000],[0,1,2],list(range(19)),list(range(19))+[1000]])
def test_stage2_forbids_holdout_and_incomplete_dev_seed_sets(seeds,tmp_path):
    from spacehealth_model.evaluate.stage2 import run_stage2
    with pytest.raises(ValueError,match='exactly dev seeds'):run_stage2(seeds,tmp_path)
