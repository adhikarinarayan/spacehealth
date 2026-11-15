# TASK-011 — Freeze M3 (+M5 info), wire into the real export, run the holdout ONCE (D17)

**From:** Claude · **To:** Codex · **Created:** Sun 2026-11-15
**Report to:** `handoffs/reports/TASK-011.md` · results `model/reports/holdout/`
**Run AFTER TASK-009** (holdout must use the final DONKI simulator). Model-only; may run alongside TASK-010 (dashboard).

## Read first
`DECISIONS.md` D13–D17, F8–F11; `handoffs/reviews/TASK-007.md`; `model/reports/stage2/summary.md`; `research/rules.yaml`; `research/assumptions.md` A11; `research/grounding.md` §1; `research/cards.yaml`.

## File fence
Edit/create: `model/spacehealth_model/modules/physiological.py`, `model/spacehealth_model/export/**`, `model/spacehealth_model/run.py`, `model/spacehealth_model/evaluate/**`, `model/spacehealth_model/compare.py`, `model/configs/frozen_v1.yaml` (new), `model/reports/holdout/**`, `model/tests/**`, append `model/EXPERIMENT_LOG.md`, append `REQUIREMENTS.md`. Read-only: detectors (import M3/M5 as-is), sim, baseline, research, contracts. No dashboard edits.

## 1. Production physiological module (D17)
- `watch` = M3 exactly as in Stage 2 (same parameters, copied into `configs/frozen_v1.yaml`).
- `act` = shared act layer (red-flag symptom; watch + red-flag symptom). M1's strong-change act rule is retired with M1.
- Evidence adds an **info-only** item "multi-signal agreement" from M5 (agree / disagree / not evaluable — never omitted silently, never changes status). Reason text from cards.yaml templates; forbidden words still enforced.
- `unknown` rules as M3 (RHR missing or RHR baseline insufficient).
- M1 stays in `detectors/` for the record. Rewrite `test_s2_flag_by_symptom_day` to test the production module; add `test_m1_documented_miss` that asserts M1 still misses S2 on seed 0 (keeps F8 visible and honest).

## 2. Freeze
Write `configs/frozen_v1.yaml` (all detector, sleep, radiation, baseline parameters) and record its SHA-256 in `model/reports/holdout/FREEZE.md` **before** running the holdout. The holdout run must refuse to start if the config hash differs.

## 3. Holdout (run ONCE; report everything)
Per A11: seeds 1000–1019; S2 RHR effect per-person U(3.1, 8.6) bpm (grounding §1) and HRV/temp effect sizes × {0.6, 0.8, 1.2}; Gaussian noise run + one Student-t (df = 4) noise run. Full system (physiological M3 + M5 info, sleep, radiation with DONKI S3).
Report per scenario S1–S4, N1, N2: pass/fail vs `research/scenarios.yaml` pass rules, detection delays (onset/symptom), false alerts days and episodes per 100 crew-days with bootstrap 95% CI, coverage per crew, N1 act count (must be 0), S3 act at each DONKI onset, S4 watch/act days. Include failures prominently. No re-runs after seeing results (if a bug is found, fix it, re-freeze with a new hash, and label the second run "holdout-2" — both reported).

## 4. Real export for the dashboard
`run.py --config configs/frozen_v1.yaml --seed 1000 --out out/` writes contract-valid `mission.json`, `indicators.json`, **`validation.json`** (holdout results in the contract shape, `seedSet: "holdout"`), and `cards.json` (from research/cards.yaml). Also copy them to `model/out/release/` with a `MANIFEST.json` (hashes, config hash, seeds). Do not copy into the dashboard (integration task).

## Acceptance (Claude re-runs)
```bash
cd model && .venv/bin/python -m pytest -q \
  && .venv/bin/python -m spacehealth_model.compare --stage holdout --config configs/frozen_v1.yaml --out reports/holdout/ \
  && .venv/bin/python -m spacehealth_model.run --config configs/frozen_v1.yaml --seed 1000 --out out/release/
```
Full suite green. Holdout summary in `reports/holdout/summary.md` with a plain-language "what worked / what failed" section and no clinical claims.

## Out of scope
Tuning after the holdout, dashboard integration, real-data check (D9), UI. No commit.
