# Data inventory

Owner: Claude · Selection: Narayan (decision D7) · Updated: Sat 2026-11-14 17:24 CST
Rule: raw files are never edited. Real data stays separate from synthetic mission fixtures.

| Dataset | Agency | Status | Local path | What it contains | Fitness for SpaceHealth | Recommendation |
|---|---|---|---|---|---|---|
| **DONKI SEP events** (CCMC Space Weather Database via api.nasa.gov) | NASA | ✅ downloaded (4 windows, 74 events) | `raw/nasa_donki_sep/SEP_<start>_<end>.json` | Real SEP event times + linked flares/CMEs/instruments: Sep 2017, Oct 2021, May 2024, Oct 2024 | Good: real timing/clustering of SPE warnings (multi-onset over hours) → S3 warning timeline realism. No dose values. | **Use** for S3 warning timing. Satisfies the "≥1 NASA data source" rule. |
| **NASA-STD-3001 Vol 1 Rev C** values | NASA | ✅ | `papers/` | Radiation limits, GCR design dose rates (1.3 / 1.5 mSv/day) | Good for simulator background dose + cumulative accounting | **Use** (evidence-backed numbers) |
| **MSL RAD** (PDS PPI `MSL-M-RAD-3-RDR-V1.0`) | NASA | ⚠️ available, not downloaded | — | Level-1A instrument records (ASCII), need calibration pipeline to reach dose rate | Real deep-space dose-rate profile incl. Sep-2017 SEP at Mars, but conversion is a multi-hour job; not on CDAWeb HAPI | **Skip for deadline**; use published rates (Zeitlin 2013 — NEED-USER) |
| **NASA OSDR Inspiration4** (OSD-569…575, 630, 687) | NASA | ⚠️ searched, not downloaded | — | Omics, microbiome, CBC; **no daily wearable HR/sleep/temp** | Not fit for wearable-signal ranges or validation | **Do not use** (cite only as context) |
| **Stanford COVID-19 wearables** (Mishra 2020) | Stanford (non-NASA) | ✅ downloaded (378 MB zip, sha256 52ca976e…f4; 281 files, 120 participants `*_hr.csv`, `*_steps.csv`, `*_sleep.csv`, 4 `*_longterm`) | `raw/stanford_covid_wearables_mishra2020/` | Per-participant minute HR + steps + sleep. **Symptom/diagnosis dates are NOT in the zip** — only in Mishra 2020 Supplementary Tables (NEED-USER) | Real-data sanity check of the physiological detector (RHR shift before symptoms); civilians, not astronauts | **Optional** real-data check, reported separately |
| NASA LSDA / astronaut medical data | NASA | ❌ not obtainable | — | Restricted (request-based, privacy) | — | Not pursued; this is why we simulate |
