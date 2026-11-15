# TASK-011 — production freeze, both holdouts and real export complete

## What worked / what failed

Production uses fixed M3 EWMA (lambda 0.2, sigma 3). M5 is explicit info-only (agree/disagree/not evaluable), never a status gate. Original M1 remains unchanged behind its historical detector wrapper; its miss is now a passing documented-miss regression, rather than the production S2 test.

Holdout synthetic outcomes (20 seeds × 3 scales × 2 noise models): **S2 75/120 by day 42; 45 misses. S4 78/120 by day 97; 42 misses.** S1 isolated quiet runs had no acts; all per-crew DONKI onset checks passed; N1 act count was zero; N2 missing/check-in checks all passed. Failures are retained prominently, not tuned away. These are not clinical outcomes.

# Frozen holdout — synthetic-scenario results

## What worked / what failed

All failures are retained; no clinical-validation claim. Thresholds/configuration were frozen before this one run.

| Scenario | Passed | Failed |
| --- | --- | --- |
| S1 | 480/480 | 0 |
| S2 | 75/120 | 45 |
| S3 | 480/480 | 0 |
| S4 | 78/120 | 42 |
| N1 | 120/120 | 0 |
| N2 | 120/120 | 0 |

| Module | False days / episodes | Evaluable crew-days | Days/100 [95% CI] | Episodes/100 [95% CI] |
| --- | --- | --- | --- | --- |
| physiological_change | 1920 / 720 | 84480 | 2.273 [1.5021306818181819, 3.302645596590908] | 0.852 [0.6107954545454546, 1.1434659090909092] |
| sleep_alertness | 438 / 369 | 84717 | 0.517 [0.3576487252124646, 0.6941874467170679] | 0.436 [0.30809547418372407, 0.5736543909348442] |
| radiation | 0 / 0 | 78720 | 0.000 [0.0, 0.0] | 0.000 [0.0, 0.0] |

N1 act days: 0.
S2 seed-block detection-rate CI95: [0.45, 0.775].
Isolated S1 quiet missions: 40 unique seed/noise cases (reused across three irrelevant effect scales); 0 act indicators.

Coverage per crew/module and per-variant outcomes are in summary.json; first watch/act and delays for every case/scenario are in results.csv/json. Unknown days are never counted as evaluable. Bootstrap resamples seed blocks, preserving correlated noise/scale variants. Counts are flagged days and contiguous episodes, not clinical outcomes.

M3 is the sole physiological status detector; M5 agreement is info-only. N1 watch costs remain in false-alert accounting. S3 is checked at each exact verified DONKI onset. S4 pass means watch-level or higher by day 97; act timing is reported, not forced.

S1/S3 have per-crew rows, and S1 repeated factor rows are labelled reuse; do not interpret 480 rows as 480 independent missions. No rerun or tuning followed these observations.

## Freeze and recovery chronology (both runs preserved)

1. Before the first holdout: 143 development tests green. Frozen SHA256 `9662bf1d498a9a729daf84c2dc73c92fcc7c0cd1943764ceaf886251b5289492`; FREEZE.md/json in reports/holdout/. The first 120-case run completed, with all case files, results and COMPLETE artifact hashes retained.
2. Release CLI then hit a metadata-only `KeyError: inputSources` after the four validated JSON files had already been written. This was not treated as a successful command. No scientific failure was suppressed and no thresholds were changed.
3. Preserved the original frozen YAML and loader source in reports/holdout/frozen_v1.original.yaml and frozen_loader.original.py.txt. Fixed input snapshot propagation and labelled output path, and added a full development-seed CLI regression. **144 tests green** before the second freeze.
4. New SHA256 `03632b3d13fbcc888a5bed3511939694989ed8a72c9e594c230035279bc2d7e0`; explicitly labelled **holdout-2**, with its own FREEZE.md/json and all 120 cases under reports/holdout/holdout-2/. Only metadata/version/report-directory changed; scientific parameters, seeds, scales, noise and release example did not.
5. The second scientific summary is **identical to the first apart from the config hash**; results.csv/json hashes also match. This is a labelled recovery repeat, not independent confirmation. No rerun or tuning followed holdout-2.

The runner refuses changed frozen config/code/data, or a second start after STARTED. Completed invocations verify hashes and reuse results, rather than re-evaluate. A cached-invocation check exited 0 with "Reusing completed holdout; no second evaluation." The task's original --out reports/holdout/ command follows the configured labelled directory.

## Acceptance / artifacts

```text
python -m pytest -q
144 passed in 32.44s

python -m spacehealth_model.compare --stage holdout --config configs/frozen_v1.yaml --out reports/holdout/
120 cases completed in holdout-2; subsequent invocation reused cached results, exit 0

python -m spacehealth_model.run --config configs/frozen_v1.yaml --seed 1000 --out out/release/
exit 0
```

Release is the **preselected** seed 1000 / Gaussian / effect scale 0.8, not chosen after viewing results. mission.json, indicators.json, validation.json (`seedSet: holdout`, recorded matching-case outcomes) and cards.json all validate against the shared schemas. model/out/release/MANIFEST.json records their hashes, frozen hash, protocol seeds and selected case. Hashes were independently rechecked and match. Data was not copied into the dashboard.

Artifacts: both holdout directories' summary.md/json, results.csv/json, individual case files, FREEZE records and COMPLETE records; original frozen config/loader; model/out/release/ four JSON files + MANIFEST.json; experiment log and REQUIREMENTS append.

## Implementation / fence

Edited only authorized production physiological/export/run/evaluation/compare code, frozen_v1.yaml, model tests and holdout artifacts; appended EXPERIMENT_LOG.md and REQUIREMENTS.md. No changes to read-only detectors, simulator, baseline, research, contracts or dashboard in this task. No new packages or commit.

The legacy `evaluate` function remains M1 because the read-only historical detector imports it. Export explicitly calls `evaluate_production`; M3/M5 are imported unchanged. Batch preparation computes causal series once per crew. Radiation output is cached by full relevant dose/event/policy content (not by seed or expected result), sharing identical streams without changing calculations; existing direct-module/intraday tests verify behavior.

The freeze captures all detector/baseline/sleep/radiation parameters, structured simulator defaults, research snapshots and protocol. Release and holdout bootstrap use seed blocks, keeping correlated noise/scale variants together. Coverage is per crew/module; M5 info availability is separately reported (C4's insufficient HRV baseline is explicit). Quiet missions are 40 unique seed/noise cases reused across irrelevant effect scales; per-crew repeated rows are not independent missions.

## Limits and review notes

- S2/S4 misses and routine false-alert days/episodes are part of the result. No clinical validation or universal threshold claim.
- M5 numerical deviations describe agreement, not causal attribution. It cannot turn a primary unknown into nominal or upgrade to act.
- Runtime status reasons fill the frozen card templates; cards.json preserves the source templates. UI integration/interpolation is a later task.
- Frozen scenario pass text contains an older S4 no-PVT parenthetical; the implemented criterion applies Narayan's later R3/D17 sleep-debt approval. No research prose was silently rewritten.
- The holdout-2 recovery is solely an export-metadata repair and is reported alongside the original. Current config/code hashes must remain unchanged if reusing its artifacts.

TASK-011 reported before TASK-010 starts. Next: original SVG/CSS dashboard theme only.
