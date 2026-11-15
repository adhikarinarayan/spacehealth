# Assumptions log (Discussion §2.5)

Owner: Claude (draft) · Verify: Narayan/B · Every material number is labelled **evidence-backed**, **engineering assumption** or **unverified**.

| ID | Assumption | Value | Label | Support / reason | Used in |
|---|---|---|---|---|---|
| A1 | Simulated per-person baseline ranges & noise | see `signals.yaml` | engineering assumption (sleep range evidence-backed) | FlynnEvans2016 (sleep); Alavi2022 (RHR stability) | sim |
| A2 | S2 effect sizes | RHR +5.6 bpm (holdout 3.1–8.6); HRV −0.5–1.0 SD; temp +0.5–1.0 SD; symptoms day 42 | RHR **evidence-backed** (Mishra2020 Supp T14); HRV/temp **direction evidence-backed**, size assumption | grounding.md §1 | sim, S2 |
| A3 | S3 event dose | 19.5 mSv over ~9 days (holdout ×0.2/×1/×5) | **evidence-backed** (Zeitlin2013 Table 1); holdout scaling assumption | grounding.md §3 | sim, S3 |
| A3b | S3 dose split across DONKI onsets | 19.5 mSv shared equally by the 3 GOES-observed episodes (Sep 5, Sep 6, Sep 10 2017) | engineering assumption (DONKI gives timing, not dose) | D15 | sim, S3 |
| A4 | ~~Universal \|z\|≥2/3~~ | replaced by module rules | — | Discussion §1.3 | — |
| A5 | 14 preflight days | 14 | engineering assumption | Real missions have far more; demo constraint | sim, baseline |
| A6 | Min valid baseline days and per-signal min scale | 10 of 14; min_scale per `signals.yaml` | engineering assumption | Alavi2022: baseline stable after ~7 nights for >80% | baseline |
| A7 | Persistence and thresholds | 2 consecutive days, ≥2 signals, z ±2 watch / ±3 act; sleep z ≤ −2 × 2 nights; red-flag symptom list | engineering assumption | Tuned on dev seeds only; frozen before holdout | modules |
| A8 | Radiation integration & triggers | trapezoid integration; coverage = hours/24; two-tier dose-rate caution/shelter (**numbers not public → configurable placeholders**); budget watch by projection to 600 mSv | structure evidence-backed (NASA Artemis II, HERA); projection evidence-backed ([V1 4030], Zeitlin2013); integration = assumption | grounding.md §3 | radiation |
| A9 | Confounders & missing data | N1 exercise spikes; N2 gaps/short baseline/skipped check-ins | engineering assumption | Discussion §2.2 | sim, N1, N2 |
| A10 | Data sharing & escalation | demo shows everything to the user; CMO contact is a recorded action, ground message queued | engineering assumption | Discussion §1.5 | dashboard |
| A11 | Seeds & distributions | dev seeds 0–19; holdout seeds 1000–1019 + effect sizes ×{0.6, 0.8, 1.2}; Gaussian noise (Student-t in holdout robustness run) | engineering assumption | Discussion G3 | model eval |
| A12 | Mission profile | Mars-class transit, 180 d, GCR 1.84 mSv/day, one-way delay up to ~20 min (source TBD), blackout window TBD | evidence-backed dose (Zeitlin2013); delay unverified | D10 | sim, cards |
