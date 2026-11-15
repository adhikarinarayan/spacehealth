# TASK-009 — verified NASA timing and structured simulator config complete

## Results / acceptance

Full `pytest -q`: **133 passed, 1 failed** in 22.19 s. The sole failure is the unchanged `test_s2_flag_by_symptom_day` (historical M1 miss). All 14 TASK-007 fixture errors are resolved. No failures skipped or xfailed.

`python -m spacehealth_model.run --seed 0 --out out/` → exit 0; schema-valid mission/indicator exports. Stage-2 was not rerun after this simulator change.

## Real data read and provenance

The simulator now reads the local NASA DONKI SEP JSON, verifies SHA256 against research/checksums.sha256, parses UTC-aware events/instruments, selects GOES onsets in the configured window and groups events strictly less than six hours apart. The raw file is read-only. Tampered-copy rejection is tested.

Mapped episodes:

| NASA UTC onset | Mission day / hour |
| --- | --- |
| 2017-09-05 00:30 | 72 / 00:30 |
| 2017-09-06 23:45 | 73 / 23:45 |
| 2017-09-10 16:25 (includes 16:45 channel) | 77 / 16:25 |

Offsets between episodes are preserved; exact onset samples are added to the grid instead of rounding to a 15-minute boundary. All four crew act at the first warning sample, day 72 00:30; each later episode has a new true warning sample and acts. The second episode can occur during the earlier episode's procedure hold, so a new warning need not imply a fresh act-state transition.

Each pulse is independently normalized to one third of the 19.5 mSv extra dose (A3b); combined mission total = 180 × 1.84 + 19.5 = **350.7 mSv** per crew, tested within 1e-6. Dose values remain simulated, not DONKI measurements. The synthetic timing switch retains the previous single day-72 06:00 pulse and dose total.

Exact provenance string:

> NASA DONKI SEP (CCMC) — GOES onsets 2017-09-05/06/10, observed near Earth; timing replayed, dose from Zeitlin2013 Table 1; file sha256 73758df3e43c2cda3c64c0350728aad4a926eba6a15396f0296969b1c63bf227

It is in missionProfile.spe_event_timing_source and the run-report JSON companion `handoffs/reports/TASK-009.json`; the configured source is also captured in the run input snapshot. The main CLI summary schema was not edited because run.py is outside this task's fence.

## Structured configuration addition requested by Narayan

No simulator code parses numeric scenario values from prose anymore. Structured research fields supply onsetDay/symptomDay/endDay/crew/module IDs; stage0.yaml supplies structured S2 effect magnitudes/ranges/symptom categories, S4 sleep range, N1 spike range/days, N2 missingness windows/count, pulse duration/dose/shape, DONKI selection/grouping and synthetic timing. Values mirror the supplied research/accepted implementation conventions; narratives remain readable descriptions only.

Added a regression that replaces all scenario timeline/effects/what/dose prose with unparseable narrative and confirms measurements and radiation samples are unchanged. A second test proves structured effect changes actually change the simulator. Structured noise supports the default Gaussian and variance-normalized Student-t df4 in preparation for the read-only simulator required by TASK-011; Gaussian seeded outputs retain their existing behavior apart from the intended S3 timing change.

## Files and fence

Only sim/generate.py, sim/space_weather.py, data_sources/__init__.py + donki.py, configs/stage0.yaml, tests/test_donki.py and S3 timing assertions in tests/test_stage0.py / test_sleep_radiation.py. No research/raw data, detector, module, evaluation, contract or dashboard edits. No new packages or commit.

The additional tests cover checksum/tampering, UTC/grouping boundaries, exact mapping, all-crew immediate acts, dose invariance, synthetic switch, prose independence and structured effects/noise determinism. Existing independent integration tests continue passing.

## Handoff

TASK-009 reported before TASK-011 begins. TASK-007's run remains archived with its pre-DONKI simulator/config hashes and no post-change rerun. Next is TASK-011 (D17 production freeze and one holdout), then TASK-010 as Narayan requested.
