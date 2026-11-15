"""Restore ignored model outputs from committed, hash-verified dashboard exports.

No simulator, detector or holdout evaluation is run. Works on a clean checkout.
"""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def main():
    prepared=[]
    for case,target,seed in [('preselected','release',1000),('illustrative','illustrative',1002)]:
        source=ROOT/'dashboard/public/data'/case
        manifest_bytes=(source/'MANIFEST.json').read_bytes();manifest=json.loads(manifest_bytes)
        if manifest['seed']!=seed:raise ValueError(f'Wrong seed for {case}')
        files={name:(source/name).read_bytes() for name in ['mission.json','indicators.json','validation.json','cards.json']}
        for name,data in files.items():
            if hashlib.sha256(data).hexdigest()!=manifest['files'][name]:raise ValueError(f'Checksum mismatch: {case}/{name}')
        prepared.append((ROOT/'model/out'/target,files,manifest_bytes))
    for directory,files,manifest in prepared:
        directory.mkdir(parents=True,exist_ok=True)
        for name,data in files.items():(directory/name).write_bytes(data)
        (directory/'MANIFEST.json').write_bytes(manifest)
    print('Restored both recorded model exports; all source hashes verified. No holdout rerun.')

if __name__=='__main__':main()
