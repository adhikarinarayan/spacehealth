# TASK-012 — Radiation robustness on four real NASA DONKI storm sequences (D18)

**From:** Claude · **To:** Codex · **Created:** Sun 2026-11-15
**Report to:** `handoffs/reports/TASK-012.md` · results `model/reports/donki_replay/`
**Run AFTER TASK-011.** Evaluation only — it must NOT change the frozen config (`configs/frozen_v1.yaml`) or the holdout results.

## Why
TASK-009 replays one real storm (Sep 2017) in S3. Narayan approved (D18) replaying **all four downloaded DONKI windows** as an extra robustness test of the radiation module on real event patterns. This tests operational behaviour (timing, re-triggering, dose bookkeeping), not health detection or real dose.

## Inputs (read-only; checksums verified via `data_sources/donki.py`)
`research/data/raw/nasa_donki_sep/SEP_*.json`. Expected GOES episodes (onsets < 6 h apart grouped), as surveyed by Claude:
| Window | GOES episodes (first onset UTC) |
|---|---|
| 2017-09 | 09-05 00:30, 09-06 23:45, 09-10 16:25 |
| 2021-10 | 10-28 16:35, 11-03 20:55 |
| 2024-05 | 05-10 13:35, **05-11 02:10 (12.5 h later, during an active warning)**, 05-13 14:00, 06-08 02:25 |
| 2024-10 | 10-09 03:50, 10-26 18:05, 11-21 18:45 |
If your parser finds different episodes, report the difference rather than forcing these.

## File fence
Create/edit: `model/spacehealth_model/evaluate/donki_replay.py`, `model/tests/test_donki_replay.py`, `model/reports/donki_replay/**`, append `model/EXPERIMENT_LOG.md`. Import read-only: `data_sources/donki.py`, `sim/**`, `modules/radiation.py`, frozen config. No other edits.

## Run
For each window separately: build a quiet 4-crew mission (frozen config, seed 0), replay that window's episodes with offsets preserved, first onset mapped to mission day 60 at its UTC time of day (all windows fit inside days 60–180). Dose per window: 19.5 mSv split equally across its episodes (same A3b convention — label clearly as assumption; DONKI provides timing only).

## Checks per window (pass/fail each)
1. `act` begins at the first sample at or after **every** episode onset, for all crew (no waiting for end of day).
2. An onset during an already-active warning extends/renews the warning; the warning never clears between two onsets less than the clear-hold apart.
3. After the last episode, status returns to non-act per the TASK-005 clear rule; no stuck alarms.
4. Daily and cumulative dose: independent integration matches within 1e-6; total injected = 19.5 mSv per window; partial coverage handled.
5. No `act` triggered by the placeholder rate tier outside episodes; report rate-tier watches.
6. Card selection: radiation act card always first and never capped.

## Outputs
`reports/donki_replay/summary.md` — one table (window × check → pass/fail, onsets, act start times, warning durations, dose) + 3 plain bullets; `results.json`; one timeline PNG per window (warning state + dose rate over the replayed days). EXPERIMENT_LOG row. Wording: "real NASA DONKI SEP onset timing (observed near Earth); dose and Mars-transit mapping are simulation assumptions".

## Acceptance (Claude re-runs)
```bash
cd model && .venv/bin/python -m pytest -q tests/test_donki_replay.py && .venv/bin/python -m spacehealth_model.evaluate.donki_replay --out reports/donki_replay/
```
Full suite stays green. No commit.
