import hashlib
import json
import sys
import pytest
from spacehealth_model.config import ROOT
from spacehealth_model.evaluate.frozen import read_frozen,DEFAULT
from spacehealth_model.evaluate.holdout import variant_config,verify_freeze
from spacehealth_model.export.files import make_indicators,export_files
from spacehealth_model.export.release import save_release
from spacehealth_model.sim.generate import generate_mission

@pytest.fixture(scope='module')
def illustrative():
    config,document,_=read_frozen();verify_freeze(DEFAULT,ROOT/document['holdout']['report_directory'])
    variant={'noise':'gaussian','effect_scale':.8}
    config=variant_config(config,document['holdout'],1002,.8,'gaussian')
    mission=generate_mission(1002,config);indicators=make_indicators(mission,config)
    return config,document,variant,mission,indicators

def test_status_timings_equal_recorded_holdout_case(illustrative):
    config,document,_,mission,indicators=illustrative
    case=json.loads((ROOT/document['holdout']['report_directory']/'case_gaussian_1002_0.8.json').read_text())
    assert config['stage']['simulation']['S2']['rhr_delta_bpm']==case['rhr_delta_bpm']
    for recorded in case['scenarios']:
        sid=recorded['scenarioId'];window=None
        if sid in ('S2','S4'):window=[config['scenarios']['scenarios'][sid]['onsetDay'],config['scenarios']['scenarios'][sid]['endDay']]
        elif sid=='S3':window=[recorded['onsetDay'],87]
        elif sid=='N2':window=[config['stage']['simulation']['N2']['wearable_gap_days'][0],config['stage']['simulation']['N2']['skipped_checkin_days'][1]]
        rows=[i for i in indicators['indicators'] if i['crewId']==recorded['crewId'] and i['moduleId']==recorded['moduleId'] and (window is None or window[0]<=i['missionDay']<=window[1])]
        for status,key in [('watch','firstWatchDay'),('act','firstActDay')]:
            assert next((i['missionDay'] for i in rows if i['status']==status),None)==recorded[key],(sid,recorded['crewId'],key)
    assert next(i['missionDay'] for i in indicators['indicators'] if i['crewId']=='C2' and i['moduleId']=='physiological_change' and i['status']=='watch')==41
    sleep=[i for i in indicators['indicators'] if i['crewId']=='C3' and i['moduleId']=='sleep_alertness']
    assert next(i['missionDay'] for i in sleep if i['status']=='watch')==96
    assert next(i['missionDay'] for i in sleep if i['status']=='act')==99

def test_export_disclosure_hashes_and_release_preservation(illustrative,tmp_path):
    config,document,variant,mission,indicators=illustrative
    canonical=ROOT/'model/out/release/MANIFEST.json';before=canonical.read_bytes()
    export_files(mission,indicators,tmp_path)
    save_release(tmp_path,config,document,1002,illustrative=True,variant=variant)
    manifest=json.loads((tmp_path/'MANIFEST.json').read_text())
    assert manifest['case']=='illustrative' and manifest['selectedAfterHoldout'] is True and manifest['seed']==1002
    assert 'lowest qualifying' in manifest['selectionRule']
    for name,digest in manifest['files'].items():assert hashlib.sha256((tmp_path/name).read_bytes()).hexdigest()==digest
    case=json.loads((ROOT/document['holdout']['report_directory']/'case_gaussian_1002_0.8.json').read_text())
    assert json.loads((tmp_path/'validation.json').read_text())['results']==case['scenarios']
    assert canonical.read_bytes()==before

@pytest.mark.parametrize('args',[['--illustrative','--seed','5'],['--illustrative','--seed','1002','--release'],['--illustrative','--seed','1002','--scenarios','S2'],['--illustrative','--seed','1002','--effect-scale','1.2'],['--seed','1002','--noise','gaussian']])
def test_invalid_cli_modes_refused_before_output(args,monkeypatch,tmp_path):
    from spacehealth_model.run import main
    monkeypatch.setattr(sys,'argv',['run',*args,'--out',str(tmp_path/'untouched')])
    with pytest.raises(SystemExit) as error:main()
    assert error.value.code==2 and not (tmp_path/'untouched').exists()

def test_cli_verifies_freeze_before_writing(monkeypatch,tmp_path):
    from spacehealth_model.run import main
    from spacehealth_model.evaluate import holdout
    def reject(*args):raise ValueError('freeze rejected')
    monkeypatch.setattr(holdout,'verify_freeze',reject)
    monkeypatch.setattr(sys,'argv',['run','--illustrative','--seed','1002','--out',str(tmp_path/'untouched')])
    with pytest.raises(ValueError,match='freeze rejected'):main()
    assert not (tmp_path/'untouched').exists()
