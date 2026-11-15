# TASK-007 — Stage-2 run complete; pre-TASK-009 suite compatibility issue recorded

## Work / fence

Implemented stage-2 evaluation in evaluate/stage2.py, extended compare.py with --stage 2, copied unchanged M3/M5 parameters into configs/stage2.yaml, added evaluation tests in test_detectors.py, and replaced only the obsolete placeholder assertion in test_stage0.py. Forbidden wording remains checked, and real sleep/radiation indicator coverage and schema validity are checked. test_s2_flag_by_symptom_day was not changed.

No detector/module/simulator/baseline/research/contract/dashboard edits. No tuning, winner selection, holdout seeds or commit.

## Commands and results

`cd model && .venv/bin/python -m pytest -q` → **112 passed, 14 fixture errors**. All fixture errors are the same queued TASK-009 compatibility issue: research/scenarios.yaml S3 already contains DONKI wording; the read-only old simulator expects `t=HH:` and cannot parse it. Captured output: model/reports/stage2/pytest.txt. Full-suite acceptance is therefore not claimed at this boundary. TASK-009, explicitly next, updates that parser; it must leave only the known M1 S2 failure.

`cd model && .venv/bin/python -m spacehealth_model.compare --stage 2 --seeds $(seq 0 19) --out reports/stage2/` → **exit 0**, 40 candidate×seed rows, fixed development seeds 0–19. Comparison explicitly uses the captured old synthetic S3 timeline from frozen reports/stage2/pre_donki_inputs.json so this run occurs before the DONKI simulator change, as requested. Source research bytes and effective timeline override are both recorded in run_manifest.json. No raw research file was changed.

The development run was repeated once to point its config at the immutable copied snapshot instead of the live stage-0 report, ensuring TASK-009 cannot later invalidate its provenance. Parameters/data realization were unchanged; no output was used for tuning.

## Synthetic results

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

## Outputs and reproducibility

model/reports/stage2/: results.csv, results.json, summary.md/json, s2_first_watch_hist.png, run_manifest.json, pre_donki_inputs.json, pytest.txt. One experiment-log row per candidate appended. No new packages.

Bootstrap: 10,000 seed-level resamples, numpy RNG seed 0, percentile 95% intervals. False-alert rate resamples numerator/denominator together. False episodes are contiguous watch/act days; unknowns, calendar gaps and the excluded S2 window break episodes. Coverage uses all 180 days per crew; false-alert denominators additionally exclude C2 days 40–50. No-detection delays are null, never zero.

Radiation outside-S3 count is a shared ancillary check, not a separate candidate performance metric. Zero cautions outside S3 reflects this simulator's fixed, noiseless background rate; it does not validate a 0.1 mSv/h threshold for real dosimeters.

## Next

Report written before TASK-009 starts. Proceed to approved DONKI parsing change, then re-run the full suite. Owner selects candidates; this report makes no winner recommendation.
