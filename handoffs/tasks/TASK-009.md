# TASK-009 — S3 replays real NASA DONKI solar-particle-event timing (D15)

**From:** Claude · **To:** Codex · **Created:** Sat 2026-11-14 ~20:35 CST
**Report to:** `handoffs/reports/TASK-009.md`
**Status: APPROVED by Narayan (D15, Sat ~20:40).**
**Run AFTER TASK-007 in the same pane** (TASK-007's Stage-2 run uses the simulator; do not change it underneath). May run alongside TASK-008 (dashboard).
`research/scenarios.yaml` S3 and assumption A3b have been updated to match this task.

## Why
Audit F10: the downloaded NASA DONKI file is not read by any code — "DONKI" is only a label in `configs/stage0.yaml`. Our NASA-data claim must be backed by code that uses the file.

## Read first
`research/scenarios.yaml` S3, `research/assumptions.md` A3, `research/data/DATA_INVENTORY.md`, `research/checksums.sha256`, `handoffs/reports/TASK-005.md`, `DECISIONS.md` D15/F10.

## File fence
Edit/create: `model/spacehealth_model/sim/**`, `model/spacehealth_model/data_sources/**` (new), `model/configs/stage0.yaml`, `model/tests/test_donki.py` (new), and only the S3 timing assertions in `model/tests/test_sleep_radiation.py` / `model/tests/test_stage0.py`. Read-only: `research/**` (incl. the raw DONKI JSON — never modify it), detectors, modules, evaluate, contracts, dashboard.

## Build
1. `data_sources/donki.py`: load `research/data/raw/nasa_donki_sep/SEP_2017-08-15_2017-10-10.json`; verify its sha256 against `research/checksums.sha256` (fail loudly on mismatch); parse events (sepID, eventTime UTC, instruments).
2. Select **GOES** instrument onsets in the 2017-09-04..2017-09-11 window (expected: 09-05T00:30Z, 09-06T23:45Z, 09-10T16:25Z, 09-10T16:45Z). Group onsets less than 6 h apart into one episode (→ 3 episodes). Keep the earliest onset per episode.
3. Map onto the mission: first episode onset → mission day 72 at its UTC time-of-day; preserve offsets between episodes exactly (→ ~day 72 00:30, ~day 73 23:45, ~day 77 16:25).
4. Dose: each episode = warning `spe_warning=true` from its onset + dose-rate pulse (existing rise/decay shape); the 3 episodes share the 19.5 mSv total equally (A3b); warning clears per existing TASK-005 logic. Background unchanged.
5. Provenance: `missionProfile.spe_event_timing_source` = "NASA DONKI SEP (CCMC) — GOES onsets 2017-09-05/06/10, observed near Earth; timing replayed, dose from Zeitlin2013 Table 1; file sha256 <hash>". Add the same into the run report JSON.
6. Keep a config switch `s3_timing: donki | synthetic` (default donki) so the old synthetic shape is still testable.

## Tests (`tests/test_donki.py` + updated S3 assertions)
- Checksum verified; tampered copy (in a tmp dir) fails.
- Exactly 3 episodes with the expected UTC onsets; mapped days/hours as above.
- S3 radiation act begins at the first episode sample (day 72 00:30) for all crew, and a new act/warning starts at each later onset.
- Integrated event dose = 19.5 mSv within 1e-6; mission total = 180 × 1.84 + 19.5.
- `synthetic` switch reproduces the previous behaviour.

## Acceptance (Claude re-runs)
```bash
cd model && .venv/bin/python -m pytest -q && .venv/bin/python -m spacehealth_model.run --seed 0 --out out/
```
Only `test_s2_flag_by_symptom_day` may fail. Report: the three mapped onsets, act start per crew, and the provenance string.

## Out of scope
Physiological detectors, Stage-2 rerun, dashboard. No commit.
