# Grounding of simulation numbers and alert rules (R2)

Owner: Claude · Requested by Narayan (R2, Sat 17:58) · Updated Sat 2026-11-14 18:25 CST
Status per number: **GROUNDED** (value from a source we hold, page/table given) · **DIRECTION-GROUNDED** (sign from sources, size is ours) · **NOT PUBLIC → configurable** · **ASSUMPTION**.

## 1. S2 physiological change (illness-like pattern)

| Quantity | Value used | Status | Evidence (local file) |
|---|---|---|---|
| Resting HR rise during affected interval | **median +5.6 bpm** (dev seeds); holdout samples per-person shift from **IQR 3.1–8.6 bpm** | **GROUNDED** | Mishra2020 Supp. Table 14 (`papers/Mishra2020_SupplementaryTables.xlsx`, sheet `SuppTable14_Fig4d_DeltaRHR`): 44 participants, 7,410 hourly ΔHR windows in significant RHR-Diff intervals around COVID-19; per-participant median ΔHR: median 5.6, p25 3.1, p75 8.6 bpm (computed by Claude, script in this file's appendix) |
| Onset before symptoms | physiology from day 40, symptoms day 42 (2 days) | **GROUNDED (plausible range)** | Alavi2022: NightSignal alerts started 3 and 10 d before symptom onset in examples; Mishra2020: 22 of 25 detected cases at/before symptom onset |
| HRV (RMSSD) change | decrease; size **−0.5 to −1.0 × person's own preflight SD** | **DIRECTION-GROUNDED** | Natarajan2020 (npj Digit Med): RMSSD decreased, HR & respiration elevated around symptom onset (Fig. 2, values only graphical); Mason2022: HRV decreases around diagnosis |
| Skin temperature change | increase; size **+0.5 to +1.0 × person's own preflight SD**, clearer in sleep | **DIRECTION-GROUNDED** | Mason2022: dermal temperature increases around symptom/diagnosis, "more readily apparent during periods of sleep"; Smarr2020: illness-associated peripheral temperature elevations detectable by wearables |
| Normal within-person RHR variability | day-to-day SD ≈ 1–2 bpm; occasional week with ≥10 bpm swing | **GROUNDED** | Quer2020 (PLoS One): individual RHR stable; 20% had ≥1 week with ≥10 bpm fluctuation; Alavi2022 Ext. Data: overnight-RHR median range ≈3 bpm over 3 months, SD of medians 0.8 |
| Between-person RHR baselines | 48–68 bpm for crew (fit adults) | **GROUNDED (within population range)** | Quer2020: mean daily RHR 65 bpm, range 40–109 across individuals |

**Design consequence:** HRV and temperature shifts are expressed in units of each person's own variability rather than invented absolute numbers. This is honest (the papers report them only relative to baseline/graphically) and matches how the detector works. Their size range is swept in the holdout so results do not depend on our choice.

## 2. Sleep

| Quantity / rule | Value | Status | Evidence |
|---|---|---|---|
| In-flight sleep, typical | 6.0–6.1 h (ISS/Shuttle actigraphy) | **GROUNDED** | NASA HRP Sleep Evidence Report 2016, Table 1 (Barger 2014 rows); FlynnEvans2016: ISS 6.4 ± 1.2 h aligned, 5.4 ± 1.4 h misaligned |
| S4 restricted sleep | ≈5.0–5.4 h for 7 nights | **GROUNDED (observed in flight)** | FlynnEvans2016 misaligned mean 5.4 h; NASA report: "many crew members reported sleeping fewer than five hours on some nights" (Santy 1988) |
| Watch rule: consecutive short nights vs own baseline | 2 nights | **DIRECTION-GROUNDED** | NASA Sleep Evidence Report 2016: "with each day of inappropriately short sleep, cognitive performance worsens" (Belenky 2003; Van Dongen 2003) |
| Why sleep alone never gives a confident "you are impaired" | — | **GROUNDED** | Same report: subjective sleepiness "increases only modestly and then reaches a plateau" while performance keeps degrading → people misjudge impairment; we have no validated alertness measure in v1 |
| Act rule: **7-night extra wakefulness vs own preflight baseline ≥ 8.16 h** | 8.16 h | **GROUNDED magnitude; application relative to baseline = decision R3** | VanDongen2003: PVT lapses near-linear in cumulative wakefulness in excess of 15.84 h/day (s.e. 0.73 h); 1 night total sleep deprivation = 24 − 15.84 = 8.16 h excess; ≤6 h/night × 14 d ≈ up to 2 nights TSD; sleepiness ratings barely changed. Belenky2003: 5-h group lapses increased, performance did not fully recover after 3 recovery nights. Watson2015: adults should sleep ≥7 h regularly |
| Absolute Van Dongen debt | info only | **GROUNDED** | Typical in-flight sleep (≈6 h) would accumulate 8.16 h excess in ≈4 days for most crew — shown as context, not as a status, to avoid constant alerts |

## 3. Radiation

| Quantity / rule | Value | Status | Evidence |
|---|---|---|---|
| Background dose rate (Mars transit) | 1.84 ± 0.33 mSv/day | **GROUNDED** | Zeitlin2013 |
| S3 storm dose (behind spacecraft shielding) | **19.5 mSv over ~9 days**, front-loaded; holdout ×0.2 (≈4 mSv, Jan-2012 event) to ×5 (larger event) | **GROUNDED** (dev); holdout scaling = assumption | Zeitlin2013 Table 1: Jan 23–29: 4.0 mSv; Mar 7–15: 19.5 mSv; May 17–18: 1.2 mSv; cruise SEP total 24.7 mSv (5.4% of 466 mSv) |
| SPE warning timing | multiple onsets over hours–days | **GROUNDED** | DONKI SEP events (Sep-2017, Oct-2021, May-2024, Oct-2024 windows); Zeitlin2013: "at least two events seen in the 7 to 9 March time frame" |
| `spe_warning` ⇒ act immediately | rule | **GROUNDED** | OCHMO-TB-020: event determination and timely reporting "to alert crew to seek shelter" |
| Dose-rate trigger without warning | **two tiers: caution (watch) and shelter-recommended (act)** on onboard dose rate | **STRUCTURE GROUNDED; NUMBERS NOT PUBLIC → configurable** | NASA Artemis II page: "first threshold signals a caution…higher threshold triggers a recommendation for the crew to take shelter"; HERA seminar 2025: minute-wise dose rate for SPE warning, "return to shelter after dose rate above threshold". Demo values must be labelled "placeholder, mission-specific". |
| Budget watch | **replace "50 %" rule** with projection: watch if `prior_career (if known) + mission dose so far + remaining days × background ≥ 600 mSv` | **GROUNDED** (600 mSv [V1 4030]; rate Zeitlin2013) | Hassler2014: 2 × 180-day transit ≈ 662 ± 108 mSv — exceeds 600 mSv on transit alone |
| 250 mSv | never an alert trigger | **GROUNDED** | NASA-STD-3001 V1C [V1 4031] is a vehicle design requirement |

## 4. Downloads
All received (Van Dongen 2003, Belenky 2003, Watson 2015 — Sat 18:45). Nothing outstanding.

## Appendix — Mishra Table 14 computation
Parsed `xl/worksheets/sheet14` of the supplementary xlsx with the Python standard library (zipfile + regex), grouped Delta HR by ParticipantID, took per-participant medians, reported quantiles. Codex will re-implement this as a tested script in the D9 task.
