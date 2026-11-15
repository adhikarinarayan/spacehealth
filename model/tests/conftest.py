from pathlib import Path
import pytest
@pytest.fixture(scope='session',autouse=True)
def release_manifest_is_unchanged_by_test_suite():
    path=Path(__file__).resolve().parents[1]/'out/release/MANIFEST.json'
    before=path.read_bytes() if path.exists() else None
    yield
    assert (path.read_bytes() if path.exists() else None)==before,'Tests changed the canonical release manifest'
