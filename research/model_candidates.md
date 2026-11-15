# Model candidates & experiment protocol — DRAFT v0.1

Owner: Claude (design) · Implement/run: Codex · Select: Narayan
Scope: the **physiological_change** and **sleep_alertness** detectors. Radiation is rule + integration (tested for correctness, not compared).

## Use-case constraints (why these candidates)
1. Only ~14 preflight days → methods must work with small n (rules out covariance-heavy or trained ML without strong regularization).
2. Must explain "why flagged" in plain words → interpretable statistics preferred.
3. Offline, deterministic, runs in a browser later → lightweight.
4. Must return `unknown` on missing/insufficient data.
5. Alert fatigue matters → false alerts per 100 crew-days is a first-class metric.

## Candidates
| ID | Method | Literature basis | Expectation |
|---|---|---|---|
| M0 | Population thresholds (e.g. RHR > 80 bpm, sleep < 5 h) | Comparator | Misses individual shifts / false-alerts on high-baseline crew → shows value of personal baselines |
| M1 | Fixed-baseline robust z + persistence (rules.yaml) | Discussion §1.4; Li2017 personal baselines | Default; interpretable |
| M2 | One-sided CuSum on robust z | Page 1954; Mishra2020/Alavi2022 online CuSum (72% sensitivity in Alavi2022) | Better on slow drift; needs k/h tuning |
| M3 | EWMA chart on robust z | Lucas & Saccucci 1990 | Similar to CuSum, fewer parameters |
| M4 | NightSignal-style state machine: overnight RHR vs streaming-median baseline, yellow/red states by persistence | Alavi2022 (80% sensitivity, same false-signal rate as CuSum) | Strong real-world precedent; we use the **fixed** preflight median (no streaming update in v1) |
| M5 | Mahalanobis distance, Ledoit–Wolf shrinkage on preflight vectors | Ledoit & Wolf 2004; multivariate anomaly in wearables | Handles correlated signals; n=14 is a stress test |
| M6 | Isolation Forest on preflight | Liu et al. 2008 | Expected to be rejected (small n, weak explanation) — kept to document why |

## Protocol
- **Stage 0 — vertical slice:** M1 only, S2, seed 0, end-to-end export. Gate before any comparison.
- **Stage 1 — toy:** 1 crewmember; scenarios S2, N1, N2; dev seeds 0–2; all candidates. Discard a candidate if: misses S2 by day 42 in ≥2/3 seeds, OR raises any act in N1, OR outputs non-unknown on N2 missing days, OR cannot produce a per-signal explanation. Each discard logged with reason.
- **Stage 2 — full:** 4 crew × 194 days; S1–S4, N1, N2; dev seeds 0–19; survivors only. Tuning allowed here only.
- **Stage 3 — holdout:** freeze configs (hash), then seeds 1000–1019 and effect sizes ×0.6/0.8/1.2 and Student-t noise; run once; report everything incl. failures.
- **Stage 4 — optional real data (D9):** Mishra2020 Fitbit HR → nightly RHR; symptom dates from Supp. Table 3; report detection vs symptom onset for M1/M2/M4 and compare with the paper's own numbers. Civilian data; reported separately.

## Metrics (per candidate × scenario × seed)
Detected (y/n) · first watch day · first act day · delay vs onset · delay vs symptom · missed events · routine false alerts per 100 evaluable crew-days (with denominator) · unknown-day count · act in negative controls (must be 0) · explanation available (y/n).

## Selection rule (proposed for Narayan)
Among candidates passing all required checks on holdout: lowest false alerts per 100 crew-days, ties broken by earlier S2 detection, then simplicity/explainability. If a more complex method wins by a small margin, prefer M1/M4.
