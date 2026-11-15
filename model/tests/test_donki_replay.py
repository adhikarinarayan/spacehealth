import pytest
from spacehealth_model.evaluate.donki_replay import WINDOWS,run_window,load_window

@pytest.mark.parametrize('window',WINDOWS)
def test_real_onsets_operational_checks(window):
    result,_=run_window(window)
    assert result['surveyMatches'],result['mappedEpisodes']
    assert all(result['checks'].values()),result
    assert len(result['onsetActSamples'])==4*len(result['mappedEpisodes'])
    assert result['dose']['injectedMsv']==pytest.approx(19.5,abs=1e-6)
    assert result['dose']['dailyMaxError']<1e-6
    assert result['dose']['cumulativeMaxError']<1e-6
    assert result['holdSampleProbesAllCrew']>0
    if window=='2024-05':
        assert len(result['warningIntervalsMissionHours'])==3
        assert result['rawWarningHours']<26*len(result['mappedEpisodes'])

def test_checksum_adapter_rejects_modified_source(tmp_path,monkeypatch):
    from spacehealth_model.evaluate import donki_replay
    original=donki_replay.donki.load_events
    def tamper(path,manifest):
        target=tmp_path/'tampered.json';target.write_bytes(path.read_bytes()+b' ')
        return original(target,manifest)
    monkeypatch.setattr(donki_replay.donki,'load_events',tamper)
    with pytest.raises(ValueError,match='checksum mismatch'):load_window('2024-10')
