import copy
from pathlib import Path
import pytest
from spacehealth_model.config import load_config
from spacehealth_model.sim.generate import generate_mission
from spacehealth_model.baseline.fixed import fit_baselines
from spacehealth_model.modules.sleep import evaluate as sleep
from spacehealth_model.modules.radiation import evaluate as radiation
from spacehealth_model.export.files import make_indicators,select_cards,validate_file

@pytest.fixture(scope='module')
def config():return load_config()
@pytest.fixture(scope='module')
def mission(config):return generate_mission(0,config)
@pytest.fixture(scope='module')
def indicators(mission,config):return make_indicators(mission,config)

def test_s3_first_warning_is_immediate_for_every_crew(mission,config):
    for c in mission['crew']:
        crew=c['crewId']
        before=radiation(mission['readings'],mission['radiationEvents'],crew,72,config,as_of_hour=.49)
        at=radiation(mission['readings'],mission['radiationEvents'],crew,72,config,as_of_hour=.5)
        assert before['status']!='act'
        assert at['status']=='act' and at['cardId']=='radiation-spe-procedure'
        assert next(e for e in at['evidence'] if e['signalId']=='daily_dose_msv')['value'] < next(r for r in mission['readings'] if r['crewId']==crew and r['missionDay']==72)['daily_dose_msv']

def test_warning_holds_through_day_after_clear(config):
    events=[{'crewId':'C1','missionDay':1,'timeHoursFromDayStart':6.,'spe_warning':True,'dose_rate_msv_h':.01},{'crewId':'C1','missionDay':2,'timeHoursFromDayStart':0.,'spe_warning':False,'dose_rate_msv_h':.01},{'crewId':'C1','missionDay':3,'timeHoursFromDayStart':0.,'spe_warning':False,'dose_rate_msv_h':.01},{'crewId':'C1','missionDay':4,'timeHoursFromDayStart':0.,'spe_warning':False,'dose_rate_msv_h':.01}]
    rows=[{'crewId':'C1','missionDay':d,'daily_dose_msv':1.,'dose_coverage':1.} for d in range(1,5)]
    assert radiation(rows,events,'C1',3,config)['status']=='act'
    assert radiation(rows,events,'C1',4,config)['status']=='nominal'

def test_radiation_budget_projection_known_and_unknown(config):
    events=[{'crewId':'C1','missionDay':1,'timeHoursFromDayStart':1.,'spe_warning':False,'dose_rate_msv_h':.01}]
    rows=[{'crewId':'C1','missionDay':1,'daily_dose_msv':1.84,'dose_coverage':1.}]
    unknown=radiation(rows,events,'C1',1,config)
    known=radiation(rows,events,'C1',1,config,prior_career_dose_msv=300.)
    assert unknown['status']=='nominal' and 'career total unknown' in unknown['reason']
    assert known['status']=='watch' and known['cardId']=='radiation-budget'
    assert '631.20' in known['reason']

def test_partial_and_missing_dose_not_complete(config):
    events=[{'crewId':'C1','missionDay':1,'timeHoursFromDayStart':1.,'spe_warning':False,'dose_rate_msv_h':.01}]
    rows=[{'crewId':'C1','missionDay':1,'daily_dose_msv':.5,'dose_coverage':.5}]
    result=radiation(rows,events,'C1',1,config)
    assert result['dataQuality']=='suspect' and 'Partial' in result['reason']
    rows[0]['daily_dose_msv']=None
    assert radiation(rows,events,'C1',1,config)['status']=='unknown'

def test_rate_tiers_are_explicit_placeholders(config):
    rows=[{'crewId':'C1','missionDay':1,'daily_dose_msv':1.84,'dose_coverage':1.}]
    for level,state in [('caution_watch_msv_h','watch'),('shelter_act_msv_h','act')]:
        events=[{'crewId':'C1','missionDay':1,'timeHoursFromDayStart':1.,'spe_warning':False,'dose_rate_msv_h':config['stage']['radiation'][level]}]
        result=radiation(rows,events,'C1',1,config)
        assert result['status']==state
        assert 'placeholder threshold (mission-specific values not public)' in result['reason']

def test_no_design_reference_event_as_trigger():
    source=Path(__file__).resolve().parents[1]/'spacehealth_model/modules/radiation.py'
    assert '250' not in source.read_text()

def test_s4_watch_by_day97(mission,indicators):
    flags=[i for i in indicators['indicators'] if i['crewId']=='C3' and i['moduleId']=='sleep_alertness' and 95<=i['missionDay']<=101 and i['status'] in ('watch','act')]
    assert flags and flags[0]['missionDay']<=97

def test_sleep_unknown_on_missing_nights(mission,config):
    rows=copy.deepcopy(mission['readings'])
    for r in rows:
        if r['crewId']=='C4' and 120<=r['missionDay']<=124:r['sleep_hours']=None
    for d in range(120,125):assert sleep(rows,'C4',d,config)['status']=='unknown'

def simple_sleep(values):
    rows=[{'crewId':'C1','missionDay':d,'rhr_bpm':60.,'hrv_rmssd_ms':50.,'skin_temp_delta_c':0.,'sleep_hours':7.,'checkin_completed':True,'symptoms':[]} for d in range(-14,0)]
    return rows+[{**rows[0],'missionDay':d,'sleep_hours':v} for d,v in enumerate(values,1)]

def test_sleep_relative_debt_and_info_only_absolute(config):
    rows=simple_sleep([5.]*7)
    result=sleep(rows,'C1',7,config)
    assert result['status']=='act' and result['cardId']=='sleep-debt'
    relative=next(e for e in result['evidence'] if 'relative debt' in e.get('unit',''))
    assert relative['value']==14.
    normal_rows=simple_sleep([6.]*7)
    for row in normal_rows:
        if row['missionDay']<0:row['sleep_hours']=6.
    normal=sleep(normal_rows,'C1',7,config)
    absolute=next(e for e in normal['evidence'] if 'info-only' in e.get('unit',''))
    assert absolute['value']>8.16 and normal['status']=='nominal'

def test_sleep_insufficient_window_can_watch_but_cannot_act(config):
    rows=simple_sleep([None,None,None,None,4.,4.,4.])
    result=sleep(rows,'C1',7,config)
    assert result['status']=='watch'
    assert result['dataQuality']=='suspect'
    assert 'Partial' in result['reason']

def test_sleep_missing_persistence_and_debt_both_unknown(config):
    rows=simple_sleep([None,None,None,None,None,None,4.])
    assert sleep(rows,'C1',7,config)['status']=='unknown'

def test_sleep_baseline_insufficient(config):
    rows=simple_sleep([5.]*7)[6:]
    assert sleep(rows,'C1',7,config)['status']=='unknown'

def test_reference_card_cap(config):
    template={'crewId':'C1','missionDay':72,'moduleId':'sleep_alertness','status':'watch','cardId':'sleep-short'}
    routine=[dict(template,crewId=f'C{i}') for i in range(5)]
    rad=dict(template,moduleId='radiation',status='act',cardId='radiation-spe-procedure')
    symptom=dict(template,moduleId='physiological_change',status='act',cardId='symptom-escalation')
    assert select_cards([*routine,rad],config)==[rad,*routine[:3]]
    assert select_cards([*routine,symptom,rad],config)==[rad,symptom,*routine[:3]]

def test_export_has_real_sleep_radiation_not_placeholders(mission,indicators):
    validate_file('mission',mission);validate_file('indicators',indicators)
    assert not any(i['reason']=='module not implemented yet' for i in indicators['indicators'])

def test_modules_no_future_leakage(mission,config):
    rows=copy.deepcopy(mission['readings']);events=copy.deepcopy(mission['radiationEvents'])
    before=sleep(rows,'C3',97,config),radiation(rows,events,'C1',72,config,as_of_hour=.5)
    for r in rows:
        if r['missionDay']>97:r['sleep_hours']=None
        if r['missionDay']>=72:r['daily_dose_msv']=999.
    for e in events:
        if e['missionDay']>72 or e['missionDay']==72 and e['timeHoursFromDayStart']>.5:e.update(spe_warning=True,dose_rate_msv_h=999.)
    assert before==(sleep(rows,'C3',97,config),radiation(rows,events,'C1',72,config,as_of_hour=.5))
