# Frozen M3 — real civilian wearable sanity check

**Separate from astronaut simulations. No tuning, parameter search or clinical-validation claim.**

Run complete: **True**. Verified input SHA256 values and frozen config SHA256 are in metrics.json. Started 2026-11-15T19:53:13.703772+00:00.

## Cohort and exclusions

Table 3: 47 rows, 32 Category COVID-19, 30 with a valid listed symptom date, 32 COVID rows with a standard HR member. Available standard archive HR records: 120 (118 distinct base IDs).

COVID evaluable: **21**; no-reported-illness candidates: 73, evaluable: **64**. Processed 105 selected participant records; excluded 20. Reasons:

- first 14 calendar nights end after symptom day -7: 5
- fewer than 10 valid baseline nights among first 14 calendar nights: 4
- COVID category without valid symptom date: 2
- fewer than 14 valid baseline nights for no-reported-illness control: 9

All participant-level eligibility decisions, baseline dates/counts/scales, coverage and denominators are retained in results.csv. Non-COVID illness participants are excluded from the control cohort by membership in either supplementary table.

## Detection (participant bootstrap 95% CI)

| Metric | Detected / evaluable | Percent [95% CI] |
|---|---|---|
| Watch in day −7…+7 | 13 / 21 | 61.90 [38.10, 80.95] |
| Watch at/before day 0 within −7…0 | 8 / 21 | 38.10 [19.05, 57.14] |

First watch day distribution within the primary window (detected cases only): -7: 2, -6: 1, -2: 3, +0: 2, +1: 3, +2: 1, +5: 1.

Detection-window coverage: 276 valid nights out of 315 possible participant-window nights. Missing nights are never replaced by zero or a healthy status. Baseline eligibility alone defines the evaluable cohort; an absent follow-up window would be counted as not detected and exposed in the coverage column.

## Watch episode costs

| Group / period | Participants with exposure | Episodes / evaluable person-nights | Episodes per 100 nights [95% CI] |
|---|---|---|---|
| COVID: after baseline, before day −7 | 21 | 15 / 515 | 2.91 [1.23, 4.70] |
| No reported illness: all post-baseline | 64 | 91 / 3675 | 2.48 [1.73, 3.28] |

Bootstrap: 5000 resamples of participants, fixed RNG seed 20261115; false-alert intervals resample whole participant episode/exposure pairs. Unknown nights break episodes and are excluded from person-night denominators. These are watch costs, not adjudicated clinical false positives.

## Fixed protocol and causal use

Overnight RHR uses 00:00–06:59 file-local minutes with explicitly zero steps in that minute and the preceding ten minutes, requiring at least 60 distinct qualifying minutes. Missing step bins do not imply rest. Duplicate HR minutes are averaged, duplicate step minutes take the maximum; no missing-night imputation is used.

For COVID cases the first 14 calendar nights of the record are the only baseline candidate, with at least 10 plausible nights, ending no later than relative day −7. Controls use their first 14 valid nights. Baseline fitting calls the existing frozen median/MAD/min-scale code. Detection starts the next calendar night, calls unchanged M3 with the exact frozen parameters, and resets on missing nights. No future measurements or symptom dates enter the detector. Synthetic tests compare prefixes against full-record results.

Multiple symptom dates: the **first listed valid timestamp in the original cell order** is used, not a date selected by outcome and not a sorted/earliest-date search. Some cells list multiple illness dates out of chronological order; attribution to a particular illness is uncertain. Baseline dates, follow-up dates and labels are consistently PHI-shifted. Earlier illness episodes are not retrospectively removed from the fixed baseline or pre-onset watch-cost window.

## Comparison with published studies

Mishra et al. (2020) reported physiological alterations in 26/32 COVID cases, detection at or before symptom onset in 22/25 cases with symptom information using offline methods, and 63% detectable before symptom onset with their real-time two-tier RHR alerting. Our frozen EWMA, eligibility, first-date rule, −7…+7 window and fixed baseline differ. Our estimates above are a sanity check on an existing untuned detector, **not a replication**, a clinical sensitivity estimate, or evidence of astronaut illness detection.

Alavi et al. (2022), Methods, “NightSignal” / “Data pre-processing”, supports averaging resting HR overnight (24:00–07:00) after zero-step filtering. The ten-minute inactivity mask and ≥60-minute eligibility rule are the TASK-016 protocol; they are not claimed as an exact Alavi replication. Unlike Alavi’s described missing-night interpolation, this evaluation performs no interpolation.

Sources: [Mishra 2020](https://doi.org/10.1038/s41551-020-00640-6); [Alavi 2022](https://doi.org/10.1038/s41591-021-01593-2). Local checksum-verified supplementary workbook and archive supplied by the project; methods checked against the local paper texts.

## Limitations

- Civilian participants on Earth during the COVID-19 era, Fitbit-derived HR, shifted dates, small selected cohort; no astronaut, microgravity or clinical deployment inference.
- Symptoms and other illnesses are self-reported; no entry in either table does not establish health. Other infections, medication, activity, stress and prior illness can explain watches.
- Overnight availability and fixed baseline restrictions create selection effects. Missing nights reset EWMA; a watch already active before day −7 can count inside the primary window.
- Minimum 1.5 bpm scale and all detector parameters come unchanged from the frozen simulator model. A successful example plot is selected only for illustration, never for a headline denominator.
- No tuning or parameter search was performed on these data. Aggregate confidence intervals describe participant resampling of this cohort, not transportability.

Example: example.png (lexicographically first detected participant).
