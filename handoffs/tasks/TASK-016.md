# TASK-016 — Real-data sanity check of the FROZEN detector on Stanford wearables (D9) — TIMEBOX 90 min

**From:** Claude · **To:** Codex (second pane) · **Created:** Sun 2026-11-15 ~13:55 CST
**Report to:** `handoffs/reports/TASK-016.md` · results `model/reports/realdata/`
**Runs IN PARALLEL with TASK-015** — respect the fence. If not done in 90 min: stop, report what works and what does not. Partial honest results are fine.

## Purpose
Break the circularity of simulator-only validation: run the **frozen M3 detector, unchanged** (configs/frozen_v1.yaml, same λ, limit, baseline rules) on real people's real illnesses and compare with Mishra 2020's own findings. **No tuning, no parameter search.** Civilian data; reported separately from astronaut-simulation results.

## Data (read-only, already downloaded and checksummed)
- `research/data/raw/stanford_covid_wearables_mishra2020/COVID-19-Wearables.zip` — read members directly from the zip (do not extract into research/). Files `COVID-19-Wearables/<ID>_hr.csv` (`user,datetime,heartrate`, ~1/min), `<ID>_steps.csv` (`user,datetime,steps`, 1/min), `<ID>_sleep.csv`. Dates are PHI-shifted but **consistently** between files and tables (Claude checked: symptom dates fall inside each participant's HR range).
- `research/papers/Mishra2020_SupplementaryTables.xlsx` — sheet `SuppTable3_Fig2a_COVID-19` (header row 4: `ParticipantID, Category, Symptom_dates, covid_diagnosis_dates, recovery_dates`; cells look like "[Timestamp('2026-07-14 …')]" or "[NaT]"); sheet `SuppTable4_Fig2a_Illnesses` for other illnesses. 47 rows in Table 3, 44 with HR files.
- Verify both files' sha256 against `research/checksums.sha256` before use.

## File fence
Create only: `model/spacehealth_model/realdata/**`, `model/tests/test_realdata.py`, `model/reports/realdata/**`; append `model/EXPERIMENT_LOG.md` and `REQUIREMENTS.md`. You may `pip install openpyxl` into `model/.venv` (record version). Import read-only: detectors (M3), baseline, frozen config loader. Do NOT touch export/, run.py, configs/, sim/, modules/, dashboard/, research/.

## Protocol (fixed now, before looking at results)
1. **Nightly RHR** per participant per night: mean HR over 00:00–06:59 (file-local time) using only minutes where steps in that minute and the previous 10 minutes are all 0; require ≥ 60 such minutes, else the night is missing (never 0). Cite Alavi 2022 overnight-RHR basis in the report.
2. **Cases:** Table 3 rows with Category COVID-19 and a valid symptom date (first date if several). Symptom onset = day 0.
3. **Baseline:** the first 14 nights of the record (≥ 10 valid, frozen min-scale rules) that end **no later than day −7** relative to symptom onset; cases without this are "not evaluable" (count them, give the reason).
4. **Run frozen M3** causally from the night after the baseline onward (no future data).
5. **Primary metric:** first watch in the window day −7 … +7 → detected; also report detected **at or before day 0**, and first-watch day distribution. **Secondary:** false-alert episodes per 100 person-nights before day −7 (after baseline) for cases; same metric for participants with **no** entry in Table 3 or Table 4 ("no reported illness"), using their first 14 valid nights as baseline (report N).
6. Bootstrap 95 % CI over participants (fixed RNG seed).
7. Compare in plain words with Mishra 2020 (paper: 26/32 COVID cases had physiological alterations; 22 of 25 with symptom info detected at/before symptom onset with offline methods; 63 % detectable before symptom onset in real time with their two-tier RHR alerting). State clearly that our method, window and baseline differ, so this is a sanity check, not a replication.

## Outputs
`model/reports/realdata/summary.md` (N available / evaluable / excluded with reasons; detection table with CIs; false-alert table; comparison paragraph; limitations: civilians, COVID-19 era, Fitbit-derived HR, shifted dates, small N), `results.csv`, one example PNG (a detected case: nightly RHR, baseline band, EWMA, symptom day), EXPERIMENT_LOG row.

## Tests (`tests/test_realdata.py`)
Nightly-RHR extraction on a tiny synthetic minute series (step masking, ≥ 60-minute rule, missing ≠ 0); date-cell parsing (Timestamp list, NaT); baseline-eligibility rule; detector called with frozen params (assert values equal frozen config); checksum verification.

## Acceptance (Claude re-runs)
```bash
cd model && .venv/bin/python -m pytest -q tests/test_realdata.py && .venv/bin/python -m spacehealth_model.realdata.run --out reports/realdata/
```
No commit.
