"""Synthetic protocol tests; no participant data required."""
import copy
import hashlib
import math
import numpy as np
import pandas as pd
import pytest
from spacehealth_model.realdata.data import nightly_rhr,parse_dates,verify_checksum,base_id
from spacehealth_model.realdata.protocol import baseline_window,detect_frozen,episodes,bootstrap
from spacehealth_model.evaluate.frozen import read_frozen

def minutes(n=80):
    hr=pd.DataFrame({'datetime':pd.date_range('2026-01-02',periods=n,freq='min'),'heartrate':np.arange(n,dtype=float)+40})
    steps=pd.DataFrame({'datetime':pd.date_range('2026-01-01 23:50',periods=n+10,freq='min'),'steps':0.})
    return hr,steps

def test_mask_current_and_previous_ten_minutes():
    hr,steps=minutes();steps.loc[20,'steps']=1
    night=nightly_rhr(hr,steps).iloc[0]
    assert night.valid_rest_minutes==69
    assert night.rhr_bpm==pytest.approx(np.mean([40+i for i in range(80) if not 10<=i<=20]))

def test_sixty_minutes_required_missing_never_zero():
    hr,steps=minutes(60);assert nightly_rhr(hr,steps).iloc[0].valid_rest_minutes==60
    assert math.isfinite(nightly_rhr(hr,steps).iloc[0].rhr_bpm)
    hr,steps=minutes(59);assert pd.isna(nightly_rhr(hr,steps).iloc[0].rhr_bpm)
    hr,steps=minutes(70);steps=steps.drop(index=20)
    night=nightly_rhr(hr,steps).iloc[0]
    assert night.valid_rest_minutes==59 and pd.isna(night.rhr_bpm)
    steps['steps']=2;assert pd.isna(nightly_rhr(hr,steps).iloc[0].rhr_bpm)

def test_duplicates_do_not_inflate_minutes_calendar_gaps_remain_missing():
    hr,steps=minutes(59);assert nightly_rhr(pd.concat([hr,hr]),steps).iloc[0].valid_rest_minutes==59
    hr,steps=minutes(60);hr2=hr.copy();hr2.datetime+=pd.Timedelta(days=2);steps2=steps.copy();steps2.datetime+=pd.Timedelta(days=2)
    nights=nightly_rhr(pd.concat([hr,hr2]),pd.concat([steps,steps2]))
    assert len(nights)==3 and pd.isna(nights.iloc[1].rhr_bpm) and nights.iloc[1].valid_rest_minutes==0

def test_date_cells_safe_and_preserve_list_order():
    assert parse_dates("[Timestamp('2026-07-14 00:00:00'), Timestamp('2026-01-01 00:00:00')]")==[pd.Timestamp('2026-07-14'),pd.Timestamp('2026-01-01')]
    assert parse_dates('[NaT]')==[] and parse_dates(None)==[]
    assert parse_dates("__import__('os').system('no')")==[]
    assert base_id('AA0HAI1_Illness_1')==base_id('AA0HAI1_1')=='AA0HAI1'

def nights():return pd.DataFrame({'rhr_bpm':[60.]*40,'valid_rest_minutes':[120]*40},index=pd.date_range('2026-01-01',periods=40))

def test_baseline_fixed_first_fourteen_no_later_window_search():
    cfg=read_frozen()[0];data=nights();onset=pd.Timestamp('2026-01-21')
    selected,reason=baseline_window(data,cfg,onset);assert not reason and len(selected)==14
    assert selected.index[-1]==onset-pd.Timedelta(days=7)
    assert baseline_window(data,cfg,onset-pd.Timedelta(days=1))[0] is None
    data.iloc[:5,0]=np.nan;assert baseline_window(data,cfg,onset)[0] is None
    data.iloc[4,0]=60;assert baseline_window(data,cfg,onset)[0].rhr_bpm.count()==10
    selected,_=baseline_window(data,cfg,None);assert selected.rhr_bpm.count()==14 and selected.index[-1]==pd.Timestamp('2026-01-18')

def test_exact_frozen_detector_params_and_causality(monkeypatch):
    from spacehealth_model.realdata import protocol
    config,doc,_=read_frozen();data=nights();data.iloc[17:23,0]=70
    selected,_=baseline_window(data,config,pd.Timestamp('2026-01-21'))
    actual=protocol.get_detector;calls=[]
    def spy(name):
        detector=actual(name)
        class Wrapped:
            def detect(self,rows,baseline,context):
                assert name=='M3' and context['stage1']==doc['detectors']
                assert context['stage1']['M3']=={'lambda':.2,'control_sigma':3.}
                calls.append(context);return detector.detect(rows,baseline,context)
        return Wrapped()
    monkeypatch.setattr(protocol,'get_detector',spy)
    before=copy.deepcopy(config);full,baseline=detect_frozen(data,selected,config,'test')
    prefix,_=detect_frozen(data.iloc[:25],selected,config,'test')
    pd.testing.assert_frame_equal(full.loc[prefix.index],prefix)
    assert baseline.center==60 and baseline.scale==config['signals']['rhr_bpm']['min_scale']==1.5
    assert next(v for v in full.threshold if not pd.isna(v))==pytest.approx(1.)
    assert config==before and len(calls)==2

def test_missing_night_resets_state_and_episodes():
    cfg=read_frozen()[0];data=nights();data.iloc[14,0]=75;data.iloc[15,0]=np.nan
    selected,_=baseline_window(data,cfg,pd.Timestamp('2026-01-21'));result,_=detect_frozen(data,selected,cfg,'test')
    assert result.iloc[0].status=='watch' and result.iloc[1].status=='unknown' and result.iloc[2].ewma==0
    assert episodes(['watch','watch','unknown','watch','nominal','watch'])==3

def test_checksum_rejects_changes_and_missing_entries(tmp_path):
    source=tmp_path/'source';source.write_bytes(b'data');manifest=tmp_path/'sums';digest=hashlib.sha256(b'data').hexdigest();manifest.write_text(digest+'  input\n')
    assert verify_checksum(source,manifest,'input')==digest
    source.write_bytes(b'changed')
    with pytest.raises(ValueError,match='mismatch'):verify_checksum(source,manifest,'input')
    with pytest.raises(ValueError,match='entry missing'):verify_checksum(source,manifest,'absent')

def test_participant_bootstrap_deterministic():
    rows=[{'events':1,'nights':10},{'events':3,'nights':30}]
    result=bootstrap(rows,'events','nights');assert result==bootstrap(rows,'events','nights')
    assert result['estimate']==10 and result['ci95']==[10.,10.]
