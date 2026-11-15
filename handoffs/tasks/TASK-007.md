# TASK-007 — Stage-2 full development run: M3 vs M5 (D13, D14) + test housekeeping

**From:** Claude · **To:** Codex · **Created:** Sat 2026-11-14 ~20:15 CST
**Report to:** `handoffs/reports/TASK-007.md` · results `model/reports/stage2/`
**May run in parallel with TASK-008** (dashboard only).

## Read first
`handoffs/reviews/TASK-004-005-006.md`, `model/reports/stage1/summary.md`, `research/model_candidates.md` (Stage 2), `research/scenarios.yaml` (N1 pass changed by D14), `DECISIONS.md` D13, D14, F9.

## File fence
Edit/create: `model/spacehealth_model/evaluate/**`, `model/spacehealth_model/compare.py`, `model/configs/stage2.yaml`, `model/reports/stage2/**`, `model/tests/test_detectors.py`, `model/tests/test_stage0.py` (only the obsolete test below), append `model/EXPERIMENT_LOG.md`. Read-only: detectors, modules, sim, baseline, research, contracts. Do not touch dashboard.

## 1. Housekeeping
`test_forbidden_words_and_placeholder_modules` is obsolete (sleep/radiation are now real). Keep its forbidden-words assertion for all modules; replace the "non-physiological must be unknown" assertion with checks that sleep/radiation indicators exist for every crew × day and are schema-valid. Do **not** touch `test_s2_flag_by_symptom_day`.

## 2. Stage-2 run (dev seeds 0–19 ONLY; seeds ≥ 1000 forbidden)
Candidates M3 and M5 with the **same fixed parameters as Stage 1** (configs/stage1.yaml values copied into stage2.yaml; no tuning in this task). Full 4-crew mission, all scenarios on.
Per candidate, aggregate over 20 seeds (report mean and range / counts):
- S2: detected by day 42 (k/20); first watch day distribution; first act day; delay vs onset and vs symptom.
- N1 (D14): act count (must be 0); watch days (reported cost).
- N2: correct unknown on gap days; **coverage** = evaluable crew-days / total crew-days per crew (M5 loses C4).
- Routine false alerts: days and **episodes** (contiguous watch runs) per 100 evaluable crew-days, with denominators.
- Bootstrap 95% CI over seeds for S2 detection rate and false-alert rate (numpy, fixed RNG seed).
Also from the TASK-005 radiation module on the same 20 seeds: number of `caution` (rate-tier watch) days outside S3 (days 72–81) — the 0.1 mSv/h placeholder may be too close to the 0.077 mSv/h background.

## 3. Outputs
`model/reports/stage2/summary.md` (one table + 3–5 plain-language bullets, no recommendation of a winner), `results.csv`, `summary.json`, `s2_first_watch_hist.png` (M3 vs M5), `run_manifest.json` (hashes). One EXPERIMENT_LOG row per candidate.

## Acceptance (Claude re-runs)
```bash
cd model && .venv/bin/python -m pytest -q && .venv/bin/python -m spacehealth_model.compare --stage 2 --seeds $(seq 0 19) --out reports/stage2/
```
Full suite: only `test_s2_flag_by_symptom_day` may fail.

## Out of scope
Choosing the winner (Narayan), tuning, holdout, real data, UI. No commit.
