# Stage-2 full development comparison — synthetic results

Fixed stage-1 parameters; 20 dev seeds; no winner selected. Bootstrap resamples seeds, not individual correlated crew-days.

| Candidate | S2 by day42 | Detection 95% CI | First watch mean [range] | N1 watch / act days | False days / episodes | Evaluable days | Days /100 [95% CI] | Episodes /100 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| M3 | 18/20 | [0.75, 1.0] | 41.4 [40, 43] | 61 / 0 | 235 / 91 | 14080 | 1.669 [1.101, 2.308] | 0.646 |
| M5 | 13/20 | [0.45, 0.85] | 42.421052631578945 [41, 46] | 16 / 0 | 25 / 25 | 10580 | 0.236 [0.170, 0.312] | 0.236 |

- First-watch/delay summaries exclude misses; misses remain explicitly counted in detection rates. Full distributions, first-act data and per-seed mean/range metrics are in summary.json and results.csv.
- N1 watches are a reported cost under D14; act counts must remain zero. Unknown days split episodes. Excluded C2 days 40–50 also split runs; a post-window continuation counts as a new routine episode.
- Coverage per crew is reported separately in summary.json: a smaller evaluable denominator is not evidence of better specificity. Complete-vector M5 cannot evaluate C4 when its HRV baseline is insufficient.
- Radiation placeholder caution days outside S3 days 72–81: 0 / 13600 evaluable crew-days. Counted once per seed; the same result is attached to both candidate rows, not summed across candidates.
- Research YAML had already advanced to DONKI timing before this task; the captured pre-TASK-009 timeline is explicitly frozen for this pre-change run. No detector/simulator changes, tuning, holdout or winner recommendation.
