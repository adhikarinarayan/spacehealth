# TASK-004 — fixed-parameter development comparison complete

Acceptance passed: `cd model && .venv/bin/python -m pytest -q tests/test_detectors.py && .venv/bin/python -m spacehealth_model.compare --seeds 0 1 2 --out reports/stage1/`.

Observed: **58 tests passed in 3.86 s**; comparison exited 0 and emitted 24 candidate×seed rows. Only development seeds 0/1/2 were run. M1's original S2 acceptance test and implementation were not edited.

## Results (synthetic-scenario results)

# Stage-1 development comparison — synthetic-scenario results

Fixed supplied parameters; seeds 0, 1, 2 only. Kept means eligible for next-stage review, not selected, validated or clinically useful. M1 original failing S2 test is unchanged.

| Candidate | S2 by day 42 | Median first watch (detected windows only) | N1 watch days | N1 acts | False alerts / evaluable crew-days | Alerts /100 | Verdict / reason |
| --- | --- | --- | --- | --- | --- | --- | --- |
| M0 | 0/3 | none | 0 | 0 | 0/2112 | 0.000 | discarded: S2 missed by symptom day in 3/3 seeds |
| M1 | 0/3 | none | 0 | 0 | 0/2112 | 0.000 | discarded: S2 missed by symptom day in 3/3 seeds |
| M1b | 1/3 | 43 | 2 | 0 | 2/2112 | 0.095 | discarded: S2 missed by symptom day in 2/3 seeds |
| M2 | 3/3 | 42 | 10 | 0 | 272/2112 | 12.879 | kept for next-stage review: no mechanical discard criterion triggered |
| M3 | 3/3 | 42 | 10 | 0 | 20/2112 | 0.947 | kept for next-stage review: no mechanical discard criterion triggered |
| M4 | 1/3 | 43 | 3 | 0 | 3/2112 | 0.142 | discarded: S2 missed by symptom day in 2/3 seeds |
| M5 | 2/3 | 42 | 2 | 0 | 2/1587 | 0.126 | kept for next-stage review: no mechanical discard criterion triggered |
| M6 | 0/3 | none | 0 | 0 | 3/1587 | 0.189 | discarded: S2 missed by symptom day in 3/3 seeds |

False-alert numerator counts flagged days (not episodes); denominator is evaluable days outside C2 days 40–50, all four crew. N1 windows are 60/61/110 ±2 days. Smaller denominators for methods needing all three signals reflect C4 insufficient HRV baseline, not fewer false alerts by design.

S2 first watch/act are searched in days 40–48; flags before onset are false alerts rather than detections. Missing windows are reported as no detection, never assigned delay zero.

M0/M2/M3/M4 need RHR and its valid fixed baseline. M1 reuses the original ≥2-signal evaluator. M1b additionally needs at least one usable corroborating signal today; corroboration on either of the two RHR-shift nights qualifies. M5/M6 need all three usable current values and at least min_valid_days complete preflight vectors; C4 HRV has only 8, so these methods return unknown throughout C4 except any overriding red-flag symptom.

CuSum nominal-day reset means three consecutive days whose statistic has not crossed h; reset occurs after the third day is evaluated. Missing/implausible input resets recurrence/persistence; gaps are not treated as zero readings. EWMA starts at zero and uses the supplied steady-state bound (no warm-up correction).

Mahalanobis uses fitted preflight mean in robust-z space and Ledoit–Wolf precision, one-sided RHR gate, χ² quantile as supplied. IsolationForest uses raw preflight vectors, fixed estimator parameters, training-score percentile and no online refit. Numerical feature deviations for these two methods are descriptive, not feature attribution or a statement of independent corroboration.

Red-flag symptom act is shared and overrides unavailable inputs. Only M1 retains its original strong-change act rule. Skipped check-ins are explicitly not collected. No winner chosen, parameters tuned, real data used or holdout evaluated.

Config hash: `c14ac9f66a9196ed2fd1e87a75f8331d63d7c68aaf7015d44a7acd4e040e654e`.

## Implementation and files

Created only TASK-004-fenced code: detectors/candidates.py, evaluate/metrics.py, compare.py, configs/stage1.yaml, tests/test_detectors.py and reports/stage1/*. Existing simulator, fixed baseline, physiological module and config loader are imported read-only. Appended one experiment row per candidate to EXPERIMENT_LOG.md. No other module/UI/contract files edited for this task; no new packages or commit.

Outputs: results.csv / results.json, summary.md / summary.json, daily_seed{0,1,2}.json, s2_overlay_seed{0,1,2}.png and run_manifest.json. The manifest preserves exact input YAML, config hash, dependency versions and code hashes. Seed-0 overlay was visually inspected.

## Tests and interpretation

- Hand-series trigger/persistence tests for every candidate, no-future-leakage/prefix equivalence, determinism, unavailable-input unknown handling, required baseline insufficiency, red-flag override, explicit skipped check-ins, M1b threshold strictness, M4 yellow info-only, CuSum reset and Mahalanobis RHR gate.
- IsolationForest does not necessarily assign an extreme out-of-support point a score lower than its training-score first percentile. Its threshold/persistence trigger test uses a deterministic scoring test double; an additional real-estimator test independently computes the training percentile and current scores with sklearn and verifies agreement. Comparison runs use the real estimator, unchanged defaults.
- No model-selection winner chosen. M2/M3/M5 are mechanically retained; this is not an endorsement. M2's prolonged watch states are visible as high false-alert-day counts. M5's lower rate has a smaller evaluable denominator because C4's HRV baseline is insufficient, so coverage must be considered alongside false alerts.
- M5/M6 explanations report numerical feature deviations and scores, not causal feature attribution. They meet the brief's descriptive signal/value criterion; explanation usefulness still needs owner review.
- Undefined implementation choices: CuSum resets after three consecutive pre-threshold (nominal) evaluations, not three negative-z readings; missing inputs reset accumulators/persistence. EWMA uses zero initialization and the supplied steady-state bound. Mahalanobis centers on preflight fitted mean in robust-z space. No retrospective online training or baseline updates.
- S2 first watch is measured in days 40–48; the median includes any watch in that window, even later than the required symptom day. Detection rate separately enforces day 42. Pre-onset alerts cannot count as early detection. No-detection delays remain null.

## Next decisions

Narayan selects which candidate(s) advance after reviewing coverage, misses and false-alert tradeoffs. No parameters were tuned and no holdout seeds were touched. The original M1 failed S2 check remains an expected, visible research finding.
