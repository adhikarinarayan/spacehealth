"""Contract-valid recorded validation and source cards for a deterministic release."""
import json
from hashlib import sha256
from pathlib import Path
from ..config import ROOT
from ..evaluate.frozen import read_frozen
from .files import encode,validate_file

def auxiliary_files(config,document,seed,*,variant=None):
    protocol=document['holdout'];validation={'schemaVersion':'0.2.0','simulated':True,'modelId':'M3-frozen-v1','configHash':config['configHash'],'seedSet':'dev','results':[]}
    if seed in protocol['seeds']:
        directory=ROOT/protocol.get('report_directory','model/reports/holdout')
        complete=json.loads((directory/'COMPLETE.json').read_text())
        if complete['configHash']!=config['configHash']:raise ValueError('Release does not match the recorded holdout')
        variant=variant or protocol['release_case'];case=json.loads((directory/f"case_{variant['noise']}_{seed}_{variant['effect_scale']}.json").read_text())
        validation['seedSet']='holdout';validation['results']=case['scenarios']
    cards={'schemaVersion':'0.2.0','source':'research/cards.yaml','cards':list(config['cards'].values())}
    validate_file('validation',validation);validate_file('cards',cards)
    return validation,cards

def save_release(out,config,document,seed,*,release=False,illustrative=False,variant=None):
    if release and illustrative:raise ValueError('Release and illustrative modes are mutually exclusive')
    if illustrative and seed not in document['holdout']['seeds']:raise ValueError('Illustrative seed must be in the frozen holdout seed list')
    if illustrative:
        variant=variant or {'noise':'gaussian','effect_scale':0.8}
        if seed!=1002 or variant!={'noise':'gaussian','effect_scale':0.8}:raise ValueError('Illustrative export requires the approved seed 1002 variant')
    out=Path(out)
    if out.resolve()==(ROOT/'model/out/illustrative').resolve() and not illustrative:raise ValueError('Illustrative output requires explicit --illustrative')
    canonical=ROOT/'model/out/release'
    if out.resolve()==canonical.resolve() and not release:raise ValueError('Canonical release requires explicit --release')
    if release and seed!=document['holdout']['seeds'][0]:raise ValueError('Release is restricted to the frozen preselected seed')
    validation,cards=auxiliary_files(config,document,seed,variant=variant)
    (out/'validation.json').write_bytes(encode(validation));(out/'cards.json').write_bytes(encode(cards))
    if not release and not illustrative:return
    release=out if illustrative else canonical;release.mkdir(parents=True,exist_ok=True)
    hashes={}
    for name in ('mission','indicators','validation','cards'):
        data=(out/f'{name}.json').read_bytes()
        if out.resolve()!=release.resolve():(release/f'{name}.json').write_bytes(data)
        hashes[f'{name}.json']=sha256(data).hexdigest()
    manifest={'configHash':config['configHash'],'seed':seed,'files':hashes,'model':'M3-frozen-v1','m5':'info-only','holdout_seeds':document['holdout']['seeds'],'release_case':document['holdout']['release_case'] if seed in document['holdout']['seeds'] else 'development'}
    if illustrative:manifest.update(case='illustrative',selectedAfterHoldout=True,selectionRule=ILLUSTRATIVE_SELECTION_RULE,release_case=variant)
    (release/'MANIFEST.json').write_bytes(encode(manifest))

ILLUSTRATIVE_SELECTION_RULE = ('Gaussian noise, effect scale 0.8 (same as the pre-selected case); S2 first watch = day 41 (typical, not the best day 40); S4 watch by day 97 and sleep-debt act reached; all other scenarios pass; choose the lowest qualifying holdout seed (1002).')
