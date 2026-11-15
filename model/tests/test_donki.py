import copy
from datetime import timedelta
from pathlib import Path
import pytest
from spacehealth_model.config import load_config
from spacehealth_model.data_sources.donki import DEFAULT,load_events,goes_episodes,map_episodes,timing
from spacehealth_model.sim.generate import generate_mission
from spacehealth_model.modules.radiation import evaluate
from spacehealth_model.sim.radiation import dose_total

@pytest.fixture(scope='module')
def config():return load_config()
@pytest.fixture(scope='module')
def mission(config):return generate_mission(0,config)

def test_verified_checksum_and_tamper_detection(tmp_path):
    events,digest=load_events();assert len(events)>0
    assert digest=='73758df3e43c2cda3c64c0350728aad4a926eba6a15396f0296969b1c63bf227'
    path=tmp_path/'tampered.json';path.write_bytes(DEFAULT.read_bytes()+b' ')
    with pytest.raises(ValueError,match='checksum mismatch'):load_events(path)

def test_exact_goes_onsets_and_mapping():
    events,_=load_events();episodes=goes_episodes(events)
    assert [e.onset.isoformat() for e in episodes]==['2017-09-05T00:30:00+00:00','2017-09-06T23:45:00+00:00','2017-09-10T16:25:00+00:00']
    assert [len(e.events) for e in episodes]==[1,1,2]
    mapped=map_episodes(episodes)
    assert [m['missionDay'] for m in mapped]==[72,73,77]
    assert [m['timeHoursFromDayStart'] for m in mapped]==pytest.approx([.5,23.75,16+25/60])
    for episode,point in zip(episodes,mapped):
        seconds=((point['missionDay']-72)*24+point['timeHoursFromDayStart']-.5)*3600
        assert seconds==pytest.approx((episode.onset-episodes[0].onset).total_seconds())

def test_grouping_boundary_is_strictly_under_six_hours():
    from spacehealth_model.data_sources.donki import Event
    events,_=load_events();one=next(e for e in events if e.eventTime.day==5)
    later=Event('boundary',one.eventTime+timedelta(hours=6),('GOES13 test',))
    assert len(goes_episodes([one,later]))==2

def test_all_three_warning_samples_act_for_every_crew(mission,config):
    mapped,source=timing();assert mission['missionProfile']['spe_event_timing_source']==source
    assert 'observed near Earth' in source and 'sha256' in source
    for crew in mission['crew']:
        for onset in mapped:
            day,hour=onset['missionDay'],onset['timeHoursFromDayStart']
            candidates=[e for e in mission['radiationEvents'] if e['crewId']==crew['crewId'] and e['missionDay']==day and abs(e['timeHoursFromDayStart']-hour)<1e-9]
            assert len(candidates)==1 and candidates[0]['spe_warning']
            result=evaluate(mission['readings'],mission['radiationEvents'],crew['crewId'],day,config,as_of_hour=candidates[0]['timeHoursFromDayStart'])
            assert result['status']=='act'
        first=next(e for e in mission['radiationEvents'] if e['crewId']==crew['crewId'] and e['spe_warning'])
        assert (first['missionDay'],first['timeHoursFromDayStart'])==(72,.5)

def test_dose_total_unchanged(mission,config):
    target=float(config['scenarios']['scenarios']['S3']['event_total_dose_msv'].split()[0])
    background=config['signals']['daily_dose_msv']['sim_background']
    for crew in mission['crew']:
        rows=[r for r in mission['readings'] if r['crewId']==crew['crewId'] and r['missionDay']>0]
        total=dose_total(rows)['observed_mission_dose_msv']
        assert total==pytest.approx(180*background+target,abs=1e-6)

def test_synthetic_switch_retains_old_onset_and_single_pulse(config):
    cfg=copy.deepcopy(config);cfg['stage']['s3_timing']='synthetic'
    mission=generate_mission(0,cfg)
    events=[e for e in mission['radiationEvents'] if e['crewId']=='C1']
    assert next((e['missionDay'],e['timeHoursFromDayStart']) for e in events if e['spe_warning'])==(72,6)
    onsets=[];before=False
    for e in events:
        if e['spe_warning'] and not before:onsets.append(e)
        before=e['spe_warning']
    assert len(onsets)==1
    rows=[r for r in mission['readings'] if r['crewId']=='C1' and r['missionDay']>0]
    assert dose_total(rows)['observed_mission_dose_msv']==pytest.approx(350.7,abs=1e-6)

def test_scenario_prose_is_not_an_executable_input(config):
    cfg=copy.deepcopy(config)
    for scenario in cfg['scenarios']['scenarios'].values():
        scenario['timeline']='This prose is deliberately not parseable.'
        scenario['what']='A narrative without any numeric values.'
        scenario['event_total_dose_msv']='Narrative only.'
        scenario['effects']={'description':'Narrative only.'}
    before=generate_mission(0,config);after=generate_mission(0,cfg)
    assert after['readings']==before['readings']
    assert after['radiationEvents']==before['radiationEvents']

def test_structured_effect_and_noise_configuration(config):
    cfg=copy.deepcopy(config);cfg['stage']['simulation']['S2']['rhr_delta_bpm']=0
    original=generate_mission(0,config);changed=generate_mission(0,cfg)
    before=next(r for r in original['readings'] if r['crewId']=='C2' and r['missionDay']==42)
    after=next(r for r in changed['readings'] if r['crewId']=='C2' and r['missionDay']==42)
    assert before['rhr_bpm']-after['rhr_bpm']==pytest.approx(5.6)
    cfg['stage']['simulation']['noise']['distribution']='student_t'
    first=generate_mission(0,cfg);second=generate_mission(0,cfg)
    assert first['readings']==second['readings']
