# TASK-016 — Complete

Completed the fixed real-data check within the 90-minute timebox. No tuning, parameter search, detector/configuration changes, holdout rerun, dashboard edits or commits.

## Results

| Metric | Result | Participant bootstrap 95% CI |
| --- | --- | --- |
| Frozen M3 watch in symptom-relative days −7…+7 | **13/21 (61.90%)** | 38.10–80.95% |
| Watch at/before day 0 within −7…0 | **8/21 (38.10%)** | 19.05–57.14% |
| Cases: watch episodes after baseline, before day −7 | **15/515 evaluable person-nights = 2.91 per 100** | 1.23–4.70 |
| No reported illness: post-baseline watch episodes | **91/3675 = 2.48 per 100** | 1.73–3.28 |

Table 3 has 47 rows: 32 COVID-19, 30 with a listed valid symptom date, all 32 with HR files. **21 cases evaluable**; 11 excluded (2 missing symptom dates, 5 first-14-night windows ending too late, 4 with fewer than 10 valid baseline nights). Of **73** no-reported-illness candidates, **64** are evaluable; 9 have fewer than 14 valid nights. The archive has 120 standard HR records representing 118 base IDs. Repeated illness-file IDs are excluded from controls using the base-ID membership of either supplementary table.

First watch distribution within −7…+7: −7:2, −6:1, −2:3, 0:2, +1:3, +2:1, +5:1. Primary-window coverage is 276/315 possible nights. Participant bootstrap uses 5,000 resamples, fixed seed 20261115; rate intervals resample whole episode/exposure pairs. These are watch episode costs, not adjudicated clinical false positives.

## Implementation and fixed choices

- Both input files are verified against research/checksums.sha256 before analysis. ZIP members are read directly; nothing is extracted into research/.
- Nightly mean HR uses file-local 00:00–06:59, with explicitly zero steps at that minute and all previous ten minute bins, and at least 60 qualifying distinct HR minutes. Missing steps fail the mask; missing nights remain missing. Duplicate HR minutes are averaged, duplicate step minutes use the maximum.
- COVID baseline is the **first 14 calendar nights**, including missing/partial initial nights, at least 10 plausible values, ending no later than symptom day −7. No later window is searched. Controls use the **first 14 valid nights**, with detection only after their final baseline date.
- **Multiple symptom dates use the first listed valid timestamp in original cell order**, as fixed before outcome analysis in protocol.json. Several lists are not chronological; no date was selected by detector success. This handling and uncertain illness attribution are disclosed prominently in the summary. Earlier reported illnesses are not retrospectively removed from the baseline or watch-cost window.
- Existing baseline fitting and M3 are imported read-only. Frozen λ=0.2, control_sigma=3 (limit 1), median/MAD and minimum 1.5 bpm scale are unchanged. Missing nights reset M3. No HRV, temperature or symptom inputs are fabricated. Causal prefix tests match full-record prefixes exactly.
- Optional openpyxl **3.1.5** and dependency et-xmlfile **2.0.0** were installed in model/.venv and recorded in REQUIREMENTS.md and metrics.json. Other dependencies were unchanged.

## Outputs

All under `model/reports/realdata/`:

- `summary.md`: cohorts, exclusions, detection and watch-cost tables with CIs, comparison with Mishra 2020, Alavi 2022 overnight-method citation and limitations.
- `results.csv`: all 105 selected participant records, including exclusions, baseline details and coverage.
- `protocol.json`: fixed choices and verified input/config hashes recorded before outcome analysis.
- `metrics.json`: machine-readable aggregate results, distribution, CIs, versions and completion state.
- `example.png`: A0NVTRV, lexicographically first detected participant, first watch day +1; observed nightly RHR, fixed baseline band, frozen EWMA, symptom day. Example selection does not affect headline denominators.
- `independent_night_audit.json`: standard-library CSV audit of 2023-10-28 for the same participant, explicit eleven-minute step lookups without pandas rolling/grouping. Both implementations select 224 minutes; mean HR differs by only 2.84e−14 bpm.

EXPERIMENT_LOG.md appended. Input SHA256 values:

- ZIP: `52ca976e6c08daa0cf34b6b82f4fc69b8894c1eef66e598efa40197df4e380f4`
- Workbook: `cf89b4b7e6209905d48adce5c4a56d76ea661e4ebd7b439636df46adc5c198ec`
- Frozen config: `03632b3d13fbcc888a5bed3511939694989ed8a72c9e594c230035279bc2d7e0`

## Validation and interpretation

Required synthetic tests **9 passed**; exact real-data CLI completed all 105 selected records; full model suite **168 passed**, confirmed with exit 0. Before/after hashes of **322 protected source/config/holdout/dashboard files** match exactly; existing release-manifest regression remains green.

Mishra's 26/32 physiological alterations, 22/25 at/before-onset offline detections, and 63% before-onset real-time result used different methods, baselines, windows and cohorts. This is an untuned **civilian, COVID-era, Fitbit-derived, shifted-date, small-N sanity check**, not a replication, clinical sensitivity estimate, or evidence of astronaut illness detection. No illness-table entry does not prove a participant was healthy. Full limitations are retained in the summary.

TASK-017 was inspected but no files for it were edited; it remains separate work.
