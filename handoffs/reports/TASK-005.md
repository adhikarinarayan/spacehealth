# TASK-005 — sleep/radiation core implemented; acceptance PASS

## Commands and observed results

`cd model && .venv/bin/python -m pytest -q tests/test_sleep_radiation.py && .venv/bin/python -m spacehealth_model.run --seed 0 --out out/`

15 passed in 8.98 s; CLI exited 0; mission.json and indicators.json validate against Pydantic + JSON Schema before export. Physiological M1 is unchanged (its S2 finding remains a miss).

## Seed-0 synthetic-scenario results

- S3 first operational act: **day 72, hour 6.0 (06:00), C1/C2/C3/C4**. Intraday evaluation uses only samples available by the supplied time, not end-of-day dose. Test at 05:59-equivalent has no act; the warning sample triggers immediately.
- S4 C3 first watch **day 96**, first act **day 99** (sleep-debt). Relative debt on days 95–101:

| Day | Observed relative 7-night debt (h) |
| --- | --- |
| 95 | 3.047279 |
| 96 | 4.487309 |
| 97 | 6.287683 |
| 98 | 7.982220 |
| 99 | 8.516330 |
| 100 | 10.292541 |
| 101 | 11.992252 |

- N2 simulator gaps currently remove RHR/HRV/temp, not sleep. Missing-sleep behavior was tested by nulling those nights in a copied fixture; every missing sleep night returns unknown. The simulator was not changed to force that outcome.
- Daily and mission integration implementation remains untouched; mission observed dose remains 350.7 mSv per crew. Earlier independent integration tests remain in the existing stage-0 suite; this task adds schema/intraday-prefix checks.

## Placeholder values

In stage0.yaml, radiation.caution_watch_msv_h = **0.1**, shelter_act_msv_h = **0.5**, placeholder = true. These are engineering demonstration values, not public NASA mission thresholds. Any rate-triggered reason includes exactly "placeholder threshold (mission-specific values not public)". Warning acts do not depend on these thresholds. There is no vehicle design-reference dose used as an event trigger; the dedicated source check passes.

## Changes within fence

- modules/sleep.py: runtime research-rule parsing; fixed preflight baseline; two-night watch; observed relative seven-night debt with >=5 valid nights for act; absolute excess-wakefulness evidence labelled info-only; missing/insufficient unknown; partial windows explicit.
- modules/radiation.py: sample-time warning state, clear+one-calendar-day hold, provisional rate tiers, known/unknown-career projection to the supplied career limit, observed cumulative dose and explicit partial coverage. Positive operational warnings can act despite uncertain dosimetry; data quality is suspect.
- export/files.py: replaces unimplemented sleep/radiation placeholders; adds reference select_cards helper preserving urgent radiation and symptom cards outside the three-routine-card cap. Export modelId M1-core-prototype (physiology remains M1).
- run.py: core S3/S4 results and policy settings, no false unimplemented-module claim; export CLI and reproducibility records retained.
- configs/stage0.yaml: appended only radiation/sleep blocks. tests/test_sleep_radiation.py: 15 checks. REQUIREMENTS.md: appended TASK-005 section. No new packages or commit.

No detectors/evaluate/compare/stage1 config, physiological module, simulator, research, contracts, dashboard or experiment-log edits for TASK-005.

## Interpretations / limits for review

- Warning clearance is the first false sample after the most recent true sample; hold lasts through the end of the following calendar day. Dose-rate-only states use the latest available sample, not the day's peak.
- Partial current coverage yields suspect quality and incomplete observed totals; missing dose history without an operational/rate/budget trigger yields unknown. Projections from partial observations are labelled as using partial inputs, never complete exposure estimates.
- Intraday projection includes the remaining fraction of the current day. End-of-day projection is exactly observed mission dose + remaining days × background. Known prior career adds only when supplied; test prior 300 mSv projects 631.2 mSv and watches. Unknown prior does not become zero or trigger the default mission-only ~331 mSv projection.
- Sleep uses the immediately preceding nights, including preflight nights for the first mission days (no day 0). A valid two-night watch can be evaluated when the seven-night act window has fewer than five observations. If neither is evaluable, status is unknown. Missing nights do not contribute invented zero debt.
- The closed SignalId enum has no separate debt/cumulative-dose identifiers. Derived evidence therefore reuses sleep_hours/daily_dose_msv with explicit unit/context labels; no schema was changed. Future UI integration should key evidence rows by index/context, not signalId alone.
- Rate-only follow-up reuses existing radiation card IDs; its indicator reason states the rate excursion, not an invented space-weather warning. Card wording should be reviewed before real UI integration.
- The existing stage-0 test asserting sleep/radiation are unimplemented placeholders is now obsolete. It was not edited because it lies outside this task's fence. Full-suite green is not claimed; the original M1 S2 acceptance failure is also unchanged.

## Log row for Claude to merge (EXPERIMENT_LOG.md unchanged)

T005-CORE-SEED0 · seed 0 dev · M1 physiological + sleep/radiation policy rules · S3 72@06:00 all crew; S4 watch 96 / act 99; career-unknown handled; provisional rate tiers 0.1/0.5 mSv/h · input/code/version hashes in model/reports/stage0_seed0.json and _inputs.json · owner review pending; no clinical-validation or winner claim.

TASK-004 comparison artifacts remain separate and retain the exact prior config snapshot. This run appends no experiment-log rows per the file fence.
