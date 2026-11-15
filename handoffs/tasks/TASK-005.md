# TASK-005 — Sleep and radiation modules (Gate G2 core)

**From:** Claude · **To:** Codex · **Created:** Sat 2026-11-14 19:12 CST
**Report to:** `handoffs/reports/TASK-005.md`
**Can run in parallel with TASK-004** (detector comparison) — respect the fence.

## File fence
Create/edit ONLY: `model/spacehealth_model/modules/sleep.py`, `model/spacehealth_model/modules/radiation.py`, `model/spacehealth_model/run.py`, `model/spacehealth_model/export/**`, `model/configs/stage0.yaml` (add a `radiation:` and `sleep:` block only), `model/tests/test_sleep_radiation.py`, `REQUIREMENTS.md` (append only).
Do NOT touch `detectors/`, `evaluate/`, `compare.py`, `configs/stage1.yaml`, `EXPERIMENT_LOG.md` (put your log rows in the report — Claude merges them), `modules/physiological.py`, `sim/`, `research/`, `contracts/`, `dashboard/`.

## Read first
`research/rules.yaml` (sleep_alertness, radiation, card_cap), `research/cards.yaml` (sleep-short, sleep-debt, radiation-spe-procedure, radiation-budget), `research/grounding.md` §2–3, `research/scenarios.yaml` S3/S4/N2, `handoffs/reviews/TASK-002.md`, `DECISIONS.md` R3, F7.

## Sleep module (`sleep_alertness`)
- watch: `sleep_hours` z ≤ −2.0 on 2 consecutive nights vs fixed preflight baseline.
- act (R3, grounded VanDongen2003): sum over last 7 nights of max(0, baseline_median_sleep − sleep_hours) ≥ 8.16 h; requires ≥ 5 valid nights in the window, otherwise act cannot be evaluated (status from watch rule, quality `insufficient` if neither evaluable).
- Also compute absolute Van Dongen excess wakefulness Σ max(0, 8.16 − sleep_hours) over 7 nights → evidence item labelled info-only; never changes status.
- unknown: sleep missing today or baseline insufficient. Card ids: `sleep-short` (watch), `sleep-debt` (act).

## Radiation module (`radiation`)
- act immediately on any `spe_warning=true` sample, from that sample's day; remains act until the warning is cleared + 1 day. Card `radiation-spe-procedure`.
- two-tier dose-rate rule (F7): `caution_watch_msv_h` and `shelter_act_msv_h` in config, both marked `placeholder: true`; pick placeholder values and state them; the reason text must say "placeholder threshold (mission-specific values not public)".
- budget watch (grounded): prior_career (if known) + mission dose so far + remaining_days × background ≥ 600 mSv → watch, card `radiation-budget`. If prior career is null: compute mission-only projection and say career total unknown. With 1.84 mSv/day × 180 d ≈ 331 mSv this should NOT fire for unknown-career crew — that is correct; test it with a fixture crew whose prior career dose is 300 mSv.
- dose_coverage < 1 ⇒ quality `suspect`/partial wording; never present partial totals as complete.
- 250 mSv must not appear as a trigger anywhere (test).

## Card cap
Indicators file carries everything; but add a helper `select_cards(indicators_for_day)` returning ≤ 3 routine cards plus all never-capped ones (rules.yaml card_cap), radiation act first — with tests. (Dashboard will reuse the rule; this is the reference implementation.)

## Export
Replace the sleep/radiation "unknown placeholder" indicators with real ones. Keep everything schema-valid.

## Tests
S3: act on day 72 at the first warning sample's day (all crew); dose integration still matches; budget projection fixture; 250-mSv grep test. S4: watch by day 97 for C3; report whether act fires and on which day (do not force it). N2: sleep unknown on missing nights. Card cap with 5 routine + 1 radiation act.

## Acceptance (Claude re-runs)
```bash
cd model && .venv/bin/python -m pytest -q tests/test_sleep_radiation.py && .venv/bin/python -m spacehealth_model.run --seed 0 --out out/
```
Report: S3 first act day/time per crew; S4 C3 first watch/act day and 7-night debt values; placeholder values chosen.

## Out of scope
Physiological detectors (TASK-004), UI, holdout, real data. No commit.
