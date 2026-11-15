import copy
from dataclasses import replace
import hashlib
import json
import pytest
from spacehealth_model.config import load_config
from spacehealth_model.evaluate.frozen import read_frozen
from spacehealth_model.evaluate.holdout import verify_freeze,variant_config
from spacehealth_model.modules.physiological import evaluate_production,production_results
from spacehealth_model.sim.generate import generate_mission

def test_freeze_hash_mismatch_refuses_before_running(tmp_path):
    path=tmp_path/'frozen.yaml'
    from spacehealth_model.evaluate.frozen import DEFAULT
    path.write_bytes(DEFAULT.read_bytes());digest=hashlib.sha256(path.read_bytes()).hexdigest()
    (tmp_path/'FREEZE.json').write_text(json.dumps({'configHash':digest,'codeHashes':{}}))
    verify_freeze(path,tmp_path)
    path.write_bytes(path.read_bytes()+b'\n')
    with pytest.raises(ValueError,match='hash differs'):verify_freeze(path,tmp_path)

def test_production_is_causal_and_m5_does_not_change_status():
    cfg,_,_=read_frozen();mission=generate_mission(0,cfg);rows=[r for r in mission['readings'] if r['crewId']=='C2']
    before=evaluate_production(rows,'C2',42,cfg)
    changed=copy.deepcopy(rows)
    for r in changed:
        if r['missionDay']>42:r.update(rhr_bpm=190,hrv_rmssd_ms=None,symptoms=['fever'])
    assert evaluate_production(changed,'C2',42,cfg)==before
    prepared=production_results(rows,'C2',cfg)
    modified=(prepared[0],{d:replace(r,status='unknown',metrics={}) for d,r in prepared[1].items()})
    output=evaluate_production(rows,'C2',42,cfg,prepared=modified)
    assert output['status']==before['status']
    assert output['evidence'][-1]['value']=='not evaluable'

def test_production_retires_strong_change_act_without_red_flag():
    cfg,_,_=read_frozen();mission=generate_mission(0,cfg)
    rows=[r for r in mission['readings'] if r['crewId']=='C1']
    for r in rows:
        if r['missionDay']>0:r.update(rhr_bpm=150.,skin_temp_delta_c=2.,symptoms=[])
    assert evaluate_production(rows,'C1',2,cfg)['status']=='watch'
    rows[-1]['symptoms']=['fever']
    assert evaluate_production(rows,'C1',180,cfg)['status']=='act'

def test_holdout_parameterization_on_dev_seed_only():
    cfg,doc,_=read_frozen();one=variant_config(cfg,doc['holdout'],0,.6,'student_t');two=variant_config(cfg,doc['holdout'],0,.6,'student_t')
    assert one==two
    assert 3.1<=one['stage']['simulation']['S2']['rhr_delta_bpm']<=8.6
    assert one['stage']['simulation']['noise']=={'distribution':'student_t','student_t_df':4}
    assert one['stage']['simulation']['S2']['hrv_delta_sd_range']==[.3,.6]
    assert cfg['stage']['simulation']['S2']['hrv_delta_sd_range']==[.5,1.]

def test_one_shot_pipeline_and_cached_reuse_on_dev_seed_only(tmp_path,monkeypatch):
    import yaml
    from spacehealth_model.evaluate import holdout
    _,document,_=read_frozen()
    document=copy.deepcopy(document)
    document['holdout'].update(seeds=[0],noise=['gaussian'],effect_scales=[.8],bootstrap_samples=100)
    path=tmp_path/'test_frozen.yaml';path.write_text(yaml.safe_dump(document))
    digest=hashlib.sha256(path.read_bytes()).hexdigest()
    (tmp_path/'FREEZE.json').write_text(json.dumps({'configHash':digest,'codeHashes':{}}))
    calls=[];actual=holdout.generate_mission
    def dev_only(seed,*args,**kwargs):
        assert seed==0
        calls.append(seed);return actual(seed,*args,**kwargs)
    monkeypatch.setattr(holdout,'generate_mission',dev_only)
    result=holdout.run_holdout(path,tmp_path)
    assert result['cases']==1
    assert result['scenarios']['S3']=={'passed':4,'total':4,'failed':0}
    count=len(calls)
    assert holdout.run_holdout(path,tmp_path)==result
    assert len(calls)==count
    (tmp_path/'summary.json').write_text('{}')
    with pytest.raises(ValueError,match='artifacts changed'):holdout.run_holdout(path,tmp_path)

def test_dev_validation_and_source_cards_are_contract_valid():
    from spacehealth_model.export.release import auxiliary_files
    config,doc,_=read_frozen()
    validation,cards=auxiliary_files(config,doc,0)
    assert validation['seedSet']=='dev' and validation['results']==[]
    assert {c['id'] for c in cards['cards']}==set(config['cards'])

def test_frozen_data_change_is_rejected(tmp_path):
    from spacehealth_model.evaluate.frozen import DEFAULT
    path=tmp_path/'frozen.yaml';path.write_bytes(DEFAULT.read_bytes())
    data=tmp_path/'source.json';data.write_text('[]')
    record={'configHash':hashlib.sha256(path.read_bytes()).hexdigest(),'codeHashes':{},'dataHashes':{str(data):hashlib.sha256(data.read_bytes()).hexdigest()}}
    (tmp_path/'FREEZE.json').write_text(json.dumps(record))
    verify_freeze(path,tmp_path)
    data.write_text('[1]')
    with pytest.raises(ValueError,match='dataset changed'):verify_freeze(path,tmp_path)

def test_frozen_loader_preserves_input_snapshot_and_full_cli_on_dev_seed(tmp_path):
    import subprocess,sys
    from spacehealth_model.evaluate.frozen import DEFAULT
    from spacehealth_model.config import ROOT
    config,document,_=read_frozen()
    assert config['inputSources']==document['sourceInputs']
    result=subprocess.run([sys.executable,'-m','spacehealth_model.run','--config',str(DEFAULT),'--seed','0','--out',str(tmp_path)],cwd=ROOT/'model',capture_output=True,text=True)
    assert result.returncode==0,result.stderr
    assert all((tmp_path/f'{name}.json').exists() for name in ('mission','indicators','validation','cards'))
