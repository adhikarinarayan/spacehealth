from pathlib import Path
import json
import pytest
from jsonschema import Draft202012Validator, FormatChecker, ValidationError
from referencing import Registry, Resource
from pydantic import ValidationError as PydanticError
from spacehealth_model.contracts import MODELS, strict_loads
ROOT=Path(__file__).resolve().parents[2]
SCHEMAS=ROOT/'contracts'/'schemas'
registry=Registry().with_resources((json.loads(p.read_text())['$id'],Resource.from_contents(json.loads(p.read_text()))) for p in SCHEMAS.glob('*.json'))
MANIFEST=json.loads((ROOT/'contracts/fixtures/manifest.json').read_text())
@pytest.mark.parametrize('entry',MANIFEST,ids=lambda e:e['path'])
def test_fixture_agreement(entry):
    results={}
    for name in ['jsonschema','pydantic']:
        try:
            data=strict_loads((ROOT/'contracts/fixtures'/entry['path']).read_text())
            if name=='jsonschema':
                schema=json.loads((SCHEMAS/(entry['kind']+'.schema.json')).read_text())
                Draft202012Validator(schema,registry=registry,format_checker=FormatChecker()).validate(data)
            else: MODELS[entry['kind']].model_validate(data)
            results[name]=True
        except (ValueError,ValidationError): results[name]=False
    assert results=={'jsonschema':entry['expected'],'pydantic':entry['expected']}
@pytest.mark.parametrize('path',sorted(SCHEMAS.glob('*.json')),ids=lambda p:p.name)
def test_schema_well_formed(path):
    Draft202012Validator.check_schema(json.loads(path.read_text()))
def test_manifest_covers_all_fixtures():
    assert {e['path'] for e in MANIFEST}=={str(p.relative_to(ROOT/'contracts/fixtures')) for p in (ROOT/'contracts/fixtures').glob('*/*.json')}
def test_composite_key_uniqueness():
    data=strict_loads((ROOT/'contracts/fixtures/valid/indicators--minimal.json').read_text())
    data['indicators'].append(data['indicators'][0])
    with pytest.raises(PydanticError): MODELS['indicators'].model_validate(data)
@pytest.mark.parametrize('bad',[float('nan'),float('inf'),float('-inf')])
def test_nonfinite_in_memory(bad):
    data=strict_loads((ROOT/'contracts/fixtures/valid/mission--minimal.json').read_text())
    data['readings'][0]['rhr_bpm']=bad
    with pytest.raises(PydanticError): MODELS['mission'].model_validate(data)

def test_overflow_numeric_literal_is_rejected():
    with pytest.raises(ValueError): strict_loads('{"number":1e999}')
