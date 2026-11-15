# TASK-004 — Stage-1 toy comparison of physiological detectors (D11)

**From:** Claude · **To:** Codex · **Created:** Sat 2026-11-14 19:10 CST
**Report to:** `handoffs/reports/TASK-004.md` · Results to `model/reports/stage1/`
**Can run in parallel with TASK-005** (sleep + radiation modules) — respect the fence.

## Why
TASK-002 seed 0 missed S2 (finding F8): the M1 rule needs ≥2 signals at z>2, but grounded HRV/temperature shifts are 0.5–1 own-SD. Narayan chose (D11) to compare research-based candidates on **dev seeds only**, then pick and freeze before holdout. Read `research/model_candidates.md`, `research/grounding.md`, `handoffs/reviews/TASK-002.md`.

## File fence
Create/edit ONLY: `model/spacehealth_model/detectors/**`, `model/spacehealth_model/evaluate/**`, `model/spacehealth_model/compare.py`, `model/configs/stage1.yaml`, `model/tests/test_detectors.py`, `model/reports/stage1/**`, and **append** to `model/EXPERIMENT_LOG.md`.
Import (do not modify) `sim/`, `baseline/`, `modules/physiological.py`, `config.py`. Do not touch `run.py`, `export/`, `modules/sleep.py`, `modules/radiation.py` (TASK-005 owns them), `research/`, `contracts/`, `dashboard/`.

## Common interface
`detect(readings_for_one_crew, baseline, cfg) -> list[DayResult(missionDay, status ∈ {nominal,watch,act,unknown}, evidence, reason_key)]`. Uses only days ≤ d for day d. Missing current inputs → `unknown` per the candidate's own needs (state it). The **act layer is shared by all candidates**: red-flag symptom ⇒ act; watch AND any red-flag symptom ⇒ act (rules.yaml). Candidates differ only in how they produce `watch` (and the M1 strong-change act rule stays M1-specific).

## Candidates (all parameters in `configs/stage1.yaml`; values below are literature defaults — do NOT tune them in this task)
| ID | Watch rule | Source |
|---|---|---|
| M0 | `rhr_bpm` ≥ 75 bpm on 2 consecutive nights (population: Quer2020 mean 65 + 10 bpm) | comparator |
| M1 | current rules.yaml (≥2 signals beyond z 2.0 on 2 consecutive days) — reuse `modules/physiological.py` | Discussion §1.4 |
| M1b | RHR z > 2.0 on 2 consecutive nights **AND** on at least one of those nights ≥1 of {hrv down, temp up} beyond z 1.0 in the expected direction | Mishra2020/Alavi2022 (RHR primary) + Discussion "≥2 signals" with tiered bar |
| M2 | One-sided CuSum on RHR z: S_d = max(0, S_{d−1} + z_d − k), k = 0.5, watch when S_d > h = 4; reset to 0 after 3 consecutive nominal days | Page 1954; Mishra2020/Alavi2022 online CuSum |
| M3 | EWMA on RHR z: E_d = λ z_d + (1−λ) E_{d−1}, λ = 0.2; watch when E_d > 3·sqrt(λ/(2−λ)) | Lucas & Saccucci 1990 |
| M4 | NightSignal-style: watch when `rhr_bpm` ≥ preflight median + 4 bpm on 2 consecutive nights (Alavi2022 red rule; **fixed** preflight median instead of streaming median, per D-fixed baseline). Also record Alavi "yellow" (≥ +3 bpm single night) as info only | Alavi2022 Methods + Ext. Data Fig. 3 |
| M5 | Mahalanobis distance of today's (rhr, hrv, temp) robust-z vector, covariance from preflight z-vectors with Ledoit–Wolf shrinkage (sklearn); one-sided: only count if RHR z > 0; watch when D² > χ²₃(0.99) on 2 consecutive days | Ledoit & Wolf 2004 |
| M6 | IsolationForest (sklearn, random_state fixed) trained on preflight (rhr, hrv, temp); watch when anomaly score below the preflight 1st percentile on 2 consecutive days | Liu et al. 2008 |
Missing handling: RHR-only methods → unknown if rhr missing or rhr baseline insufficient. Multi-signal methods → state exactly.

## Runs (dev seeds only: 0, 1, 2 — NEVER seeds ≥ 1000)
Use the existing simulator. For each seed: full 4-crew mission (S1 background for all, S2 on C2, N1 on C1, N2 on C4; S3/S4 enabled but irrelevant here).
Per candidate × seed record:
- **S2 (C2):** first watch day, first act day, detected by day 42 (y/n), delay vs onset 40 and vs symptom 42, days flagged 40–48.
- **N1 (C1 days 60, 61, 110 ± 2):** any watch / any act.
- **N2 (C4):** days 120–124 must be unknown; skipped check-in days 130–131 must not read as "no symptoms".
- **Routine false alerts:** watch/act days outside S2 window (C2 days 40–50) across all 4 crew ÷ evaluable crew-days × 100, with denominator.
- **Explanation available:** can the candidate name which signal(s) and by how much? (y/n + example reason string).

## Discard rule (from model_candidates.md, apply mechanically and log)
Discard if: S2 missed by day 42 in ≥ 2/3 seeds, OR any act in N1, OR non-unknown on N2 gap days, OR no per-signal explanation.

## Outputs
- `model/reports/stage1/results.csv` (one row per candidate × seed) and `summary.md` (table per candidate: S2 detect rate, median first-watch day, N1 watches, false alerts /100 crew-days, kept/discarded + reason).
- `model/reports/stage1/s2_overlay_seed{0,1,2}.png`: C2 days 30–58 RHR/HRV/temp with each candidate's watch days marked.
- One `EXPERIMENT_LOG.md` row per candidate (config hash, seeds, metrics, verdict).
- Tests: each detector on tiny hand-made series (known trigger day), no-future-leakage, unknown on missing, determinism.

## Acceptance (Claude re-runs)
```bash
cd model && .venv/bin/python -m pytest -q tests/test_detectors.py && .venv/bin/python -m spacehealth_model.compare --seeds 0 1 2 --out reports/stage1/
```
The existing `test_s2_flag_by_symptom_day` (M1) may still fail — do not change it.

## Out of scope
Choosing the winner (Narayan decides), tuning parameters, holdout seeds, real data (D9), UI. No commit.
