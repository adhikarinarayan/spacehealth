"""Load research at runtime; fail explicitly if a prose rule cannot be interpreted."""
from pathlib import Path
from hashlib import sha256
import re
import yaml
ROOT = Path(__file__).resolve().parents[2]
RESEARCH = ROOT / 'research'

def numbers(text):
    return [float(x) for x in re.findall(r'[-+]?\d+(?:\.\d+)?', str(text))]

def load_config():
    paths = [RESEARCH / f'{name}.yaml' for name in ('signals','scenarios','rules','cards')]
    paths.append(ROOT / 'model/configs/stage0.yaml')
    raw = [p.read_bytes() for p in paths]
    signals, scenarios, rules, cards, stage = [yaml.safe_load(b) for b in raw]
    phys = rules['physiological_change']
    watch = re.fullmatch(r'≥(\d+) signals shifted on each of (\d+) consecutive days', phys['watch'])
    strong = re.fullmatch(r'≥(\d+) signals with z beyond ±([\d.]+) on (\d+) consecutive days', phys['act'][1])
    if watch is None or strong is None:
        raise ValueError('Unsupported physiological rule wording; request a structured rule specification')
    return {
        'signals': signals['signals'], 'scenarios': scenarios, 'rules': rules,
        'cards': {c['id']: c for c in cards['cards']}, 'stage': stage,
        'watch_count': int(watch[1]), 'watch_days': int(watch[2]),
        'watch_z': float(re.search(r'±([\d.]+)',phys['shifted_day'])[1]),
        'act_count': int(strong[1]), 'act_z': float(strong[2]), 'act_days': int(strong[3]),
        'mad_factor': float(re.search(r'([\d.]+)\s*\*\s*MAD',rules['baseline']['scale'])[1]),
        'configHash': sha256(b'\0'.join(raw)).hexdigest(),
        'inputSources': {str(p.relative_to(ROOT)): {'sha256':sha256(b).hexdigest(),'text':b.decode()} for p,b in zip(paths,raw)},
    }
