# Review — TASK-011 · Verdict: **PASS** — honest freeze and holdout; results weaker than development (expected)

Reviewer: Claude · Sun 2026-11-15 ~13:00
- `configs/frozen_v1.yaml` sha256 = `03632b3d…7e0` = FREEZE.md (holdout-2). Original freeze + run preserved; holdout-1 and holdout-2 summaries identical apart from hashes.
- `pytest -q` → 144 passed. Re-invoking the holdout reuses the completed run (cannot evaluate twice). Release MANIFEST hashes all match.
- Production: M3 decides watch; M5 info-only; M1 documented-miss regression test keeps F8 visible.
- Analysis by Claude (F12): effect-scale factor only scales HRV/temp, which M3 ignores, and sleep is unscaled → the 120 rows are 40 unique cases (and 20 unique RHR draws shared by both noise models). S2: 25/40 by day 42, 39/40 within the illness window; strong dose-response with injected RHR rise. S4: 11/40 never flagged — probable scenario-design cause (absolute 5.0–5.4 h restriction is shallow for crew whose baseline is near 6 h); to verify, not to retune.
- Note for the report: the pre-registered S2 metric (by symptom day) stays primary; "within illness window" is reported as secondary, not substituted.
- Open: TASK-012 (four DONKI storms) was ordered before TASK-010 — confirm it ran.
