from dataclasses import dataclass
import math
import numpy as np

@dataclass(frozen=True)
class Baseline:
    center: float | None
    scale: float | None
    count: int
    quality: str

def usable(value, spec):
    return value is not None and math.isfinite(value) and spec['plausible'][0] <= value <= spec['plausible'][1]

def fit_baselines(readings, crew_id, config):
    result = {}
    low, high = config['scenarios']['mission']['preflight_days']
    for signal, spec in config['signals'].items():
        if 'min_scale' not in spec:
            continue
        values = [r[signal] for r in readings if r['crewId'] == crew_id and low <= r['missionDay'] <= high and usable(r.get(signal), spec)]
        count = len(values)
        if count < config['rules']['baseline']['min_valid_days']:
            result[signal] = Baseline(None, None, count, 'insufficient')
            continue
        center = float(np.median(values))
        scale = max(config['mad_factor'] * float(np.median(np.abs(np.array(values)-center))), spec['min_scale'])
        result[signal] = Baseline(center, scale, count, 'valid')
    return result
