import hashlib,json
from pathlib import Path
import pytest
from spacehealth_model.config import ROOT
from spacehealth_model.evaluate.frozen import read_frozen
from spacehealth_model.evaluate.holdout import variant_config,verify_freeze
from spacehealth_model.sim.generate import generate_mission
from spacehealth_model.export.files import make_indicators,encode
from spacehealth_model.export.release import save_release

def test_seed1000_statuses_are_byte_identical_and_reasons_are_plain():
    cfg,doc,_=read_frozen();case=doc['holdout']['release_case'];cfg=variant_config(cfg,doc['holdout'],1000,case['effect_scale'],case['noise'])
    mission=generate_mission(1000,cfg);out=make_indicators(mission,cfg)
    statuses=encode([[i['crewId'],i['missionDay'],i['moduleId'],i['status']] for i in out['indicators']])
    before=(ROOT/'model/tests/fixtures/release_statuses_seed1000.json').read_bytes()
    assert statuses==before
    for i in out['indicators']:
        if i['moduleId']=='physiological_change':
            assert 'M3 /' not in i['reason'] and 'statistic=' not in i['reason'] and '1 nights' not in i['reason']
    verify_freeze(ROOT/'model/configs/frozen_v1.yaml',ROOT/doc['holdout']['report_directory'])

def test_no_implicit_release_copy_and_only_frozen_seed_may_release(tmp_path):
    cfg,doc,_=read_frozen()
    save_release(tmp_path,cfg,doc,0)
    assert (tmp_path/'cards.json').exists()
    with pytest.raises(ValueError,match='preselected'):save_release(tmp_path,cfg,doc,0,release=True)
    with pytest.raises(ValueError,match='explicit'):save_release(ROOT/'model/out/release',cfg,doc,0)
