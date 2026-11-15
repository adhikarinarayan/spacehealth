# Model experiment log

## M1-STAGE0-SEED0 — synthetic, development only

State: executed; S2 acceptance FAILED; reviewer verdict pending.

Rationale: Stage 0 in research/model_candidates.md, M1 fixed preflight robust-z persistence; no candidate sweep. Research IDs: Li2017, Mishra2020, Alavi2022, Zeitlin2013; assumptions A1/A2/A3/A5/A6/A7/A8/A9/A11/A12. Signal noise and effect sizes are loaded from research YAML, not tuned to this result.

Seed: 0 (development); four crew, 14 preflight + 180 mission days. Gaussian independent signal noise; scenario effects/missingness as captured in reports/stage0_seed0_inputs.json. Correlated-sensor context is disclosed in explanations; the synthetic generator does not establish real-world joint covariance.

Config hash: `9b9a24ec60b8a1f0de1abb8d0ce21502eede71ed0c6aa6a9bf4d67a66408bfa0`.
Code version: uncommitted workspace; per-file SHA256 in reports/stage0_seed0.json. Runtime package versions are recorded there and in REQUIREMENTS.md.

Outcome: S2 first watch/act = none (missed required day 42); N1 watch/act = none; N2 unknown days 120–124. Routine false alerts outside S2 = 0/706 evaluable crewmember-days (0 per 100), accompanied by a missed event. Dose 350.7 mSv per crew; independent numerical integration verified. No clinical validation claim.

Artifacts: reports/stage0_seed0.json, reports/stage0_seed0_inputs.json, reports/stage0_seed0_cli.txt, reports/task002_pytest.txt, reports/s2_seed0.png, generated out/mission.json and out/indicators.json.

Decision: do not change effects, thresholds, seed or pass criterion to hide the miss. Await Claude/Narayan review; no accepted model-selection decision recorded. See ../handoffs/reports/TASK-002.md for provisional numerical interpretations.

## TASK-004 stage-1 fixed-default dev comparison

Config SHA256: `c14ac9f66a9196ed2fd1e87a75f8331d63d7c68aaf7015d44a7acd4e040e654e`. Dev seeds 0/1/2 only; source/input/code hashes and dependency versions: reports/stage1/run_manifest.json. No tuning, holdout, real-data evaluation or owner selection.

| Run | Candidate | S2 by 42 | False alert days / evaluable days | Alerts /100 | Mechanical verdict |
| --- | --- | --- | --- | --- | --- |
| T004-M0 | M0 | 0/3 | 0/2112 | 0.000 | discarded; S2 missed by symptom day in 3/3 seeds |
| T004-M1 | M1 | 0/3 | 0/2112 | 0.000 | discarded; S2 missed by symptom day in 3/3 seeds |
| T004-M1b | M1b | 1/3 | 2/2112 | 0.095 | discarded; S2 missed by symptom day in 2/3 seeds |
| T004-M2 | M2 | 3/3 | 272/2112 | 12.879 | kept for next-stage review; no discard criterion triggered |
| T004-M3 | M3 | 3/3 | 20/2112 | 0.947 | kept for next-stage review; no discard criterion triggered |
| T004-M4 | M4 | 1/3 | 3/2112 | 0.142 | discarded; S2 missed by symptom day in 2/3 seeds |
| T004-M5 | M5 | 2/3 | 2/1587 | 0.126 | kept for next-stage review; no discard criterion triggered |
| T004-M6 | M6 | 0/3 | 3/1587 | 0.189 | discarded; S2 missed by symptom day in 3/3 seeds |

Research rationale: TASK-004 / model_candidates.md; M1 baseline rule, M1b RHR-primary corroboration, Page CuSum, Lucas/Saccucci EWMA, Alavi fixed-baseline NightSignal-style, Ledoit–Wolf covariance and IsolationForest comparator. Gaussian synthetic noise, scenario effects and missingness unchanged from captured research YAML. Full outputs and overlays: reports/stage1/. All failures reported; owner review pending.

| T005-CORE-SEED0 | merged by Claude from handoffs/reports/TASK-005.md | seed 0 dev | M1 physiological + sleep/radiation policy rules | S3 act 72@06:00 all crew; S4 watch 96 / act 99; career-unknown handled; provisional rate tiers 0.1/0.5 mSv/h (placeholder) | hashes in model/reports/stage0_seed0.json | owner review pending |

## TASK-007 Stage 2 — fixed M3/M5, dev seeds 0–19

Config SHA256: `0a2b64c1cd95554dc0f8446da3e456da2fb94ff45aed51b84cdd2e91c3eaaadf`; complete input/code/version manifest: reports/stage2/run_manifest.json. Gaussian scenarios unchanged, old synthetic S3 timeline frozen before TASK-009; 10,000 seed-bootstrap samples RNG 0. No tuning/holdout or winner selection.

| Run | Candidate | S2 by42 | False days / episodes | Evaluable days | Coverage C4 | Outcome |
| --- | --- | --- | --- | --- | --- | --- |
| T007-M3 | M3 | 18/20 | 235 / 91 | 14080 | 0.972 | Results reported; owner selection pending |
| T007-M5 | M5 | 13/20 | 25 / 25 | 10580 | 0.000 | Results reported; owner selection pending |

Artifacts: reports/stage2/summary.md, results.csv, s2_first_watch_hist.png. Full suite at this boundary:112 passed/14 errors from pending DONKI syntax change, not suppressed; resolved next by TASK-009. Routine watches in N1 are costs under D14; all N1 acts zero.

## TASK-011 — D17 frozen production and holdout recovery

M3 decides; M5 information only. First freeze `9662bf1d498a9a729daf84c2dc73c92fcc7c0cd1943764ceaf886251b5289492`, 143 dev tests; original 120-case results retained in reports/holdout/. Release metadata inputSources bug found afterward; no numerical changes. Second freeze `03632b3d13fbcc888a5bed3511939694989ed8a72c9e594c230035279bc2d7e0`, 144 dev tests including full CLI; labelled holdout-2 in reports/holdout/holdout-2/. Same metrics, not independent confirmation.

| Run | Seeds / noise / scales | S2 by42 | S4 by97 | N1 act days | State |
| --- | --- | --- | --- | --- | --- |
| T011-holdout-1 | 1000–1019 / Gaussian + Student-t df4 / 0.6,0.8,1.2 | 75/120 | 78/120 | 0 | Original science complete; export metadata bug; preserved |
| T011-holdout-2 | Same; metadata-only repair | 75/120 | 78/120 | 0 | Complete, hashes verified; release exported |

Physiological false alerts 2.273 days / 0.852 episodes per100 evaluable crew-days (84480 denominator); sleep 0.517/0.436 (84717); radiation 0/0 (78720). Bootstrap95 intervals, coverage, per-case delays and failures in summary.json/results.csv. No tuning after holdout, no additional seeds, no clinical-validation claim. Config/code/data/version hashes in both FREEZE.json records. Owner review pending.

| T012-DONKI-robustness | Frozen seed 0, quiet four-crew mission; four checksum-verified NASA windows | All 24 operational checks pass; 12 grouped episodes / 48 crew-onsets; 19.5 mSv assumed per window | Evaluation only; no tuning or holdout rerun; reports/donki_replay/ |

Real NASA DONKI SEP onset timing (observed near Earth); dose and Mars-transit mapping are simulation assumptions. May 2024 overlapping onset renews the warning; independent dose and partial coverage checks pass. Full suite: 151 passed.

## T016 — Frozen M3 on real Stanford civilian wearables (2026-11-15)

| Protocol / cohort | Watch −7…+7 | Watch by day 0 (within −7…0) | Watch episode costs / 100 evaluable person-nights | State |
| --- | --- | --- | --- | --- |
| Checksum-verified Mishra workbook + Stanford ZIP; fixed nightly rest mask; unchanged frozen M3; first listed symptom date; 21 eligible COVID participants, 64 no-reported-illness controls | 13/21 = 61.90% [38.10, 80.95] | 8/21 = 38.10% [19.05, 57.14] | Cases before day −7: 15/515 = 2.91 [1.23, 4.70]; controls: 91/3675 = 2.48 [1.73, 3.28] | Complete within 90 min; no tuning or parameter search |

Participant bootstrap: 5,000 resamples, RNG seed 20261115. COVID exclusions: 2 without valid symptom dates, 5 whose first 14 calendar nights end too late, 4 with fewer than 10 valid baseline nights. Control exclusions: 9 with fewer than 14 valid baseline nights. Missing step bins and nights are never zero-filled; unknown resets M3. This is a separate civilian sanity check, not a replication, clinical validation, or astronaut performance claim. All inputs, fixed choices, denominators, CIs, first-watch distribution and limitations are in reports/realdata/{protocol.json,metrics.json,results.csv,summary.md}; example.png is the first detected case in participant-ID order. openpyxl 3.1.5 / et-xmlfile 2.0.0 added as explicitly allowed; versions recorded. Synthetic tests 9 passed; full suite 168 passed. Frozen config, detector, baseline, simulator, holdout and dashboard unchanged.
