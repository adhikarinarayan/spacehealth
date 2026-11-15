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
