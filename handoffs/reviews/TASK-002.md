# Review — TASK-002 · Verdict: **PASS (code)** · **S2 scenario MISS = research/rule finding, not a code defect**

Reviewer: Claude · Sat 2026-11-14 ~19:00 CST

## Re-run by Claude
- `model: pytest -q` → 46 passed, 1 failed (`test_s2_flag_by_symptom_day`, expected given the finding below)
- `model: python -m spacehealth_model.run --seed 0 --out out/` → exports valid
- `dashboard: npm test -- --run` → 20 passed; `npm run build` → OK

## What is right
- Contract v0.2.0 (missionProfile) in all three validators + negative fixture.
- Research YAML loaded at runtime, inputs hashed and snapshotted per run — good reproducibility.
- Detector receives no scenario truth; no-future-leakage test; no silent zero; missing → unknown (N2 days 120–124 unknown; skipped check-ins recorded as not collected).
- N1: 0 watch / 0 act. S1-type routine false alerts: 0 / 706 evaluable crew-days.
- Radiation: mission dose 350.7 mSv = 180 × 1.84 + 19.5 ✓; independent SciPy integration agrees within 1e-6; null intervals not zero-filled; prior career stays unknown.
- Honest handling of the miss: no threshold tuning, no seed search, no xfail. Exactly the behaviour we want.

## Finding F8 — S2 miss is a rule/evidence mismatch (Claude's rule, A7)
Chart `model/reports/s2_seed0.png`: RHR exceeds the band days 41–46; skin temp only days 40–41; HRV never. Rule requires ≥2 signals at |z| > 2 on 2 consecutive days. Grounded HRV/temperature effects are 0.5–1.0 own-SD (grounding.md §1), i.e. below z = 2 by construction → the rule can rarely fire.
Literature: Mishra2020 (RHR-Diff), Alavi2022 (NightSignal = overnight RHR only, 80% sensitivity) treat **RHR as the primary signal**; HRV/temperature are weaker, corroborating signals. Discussion §2.3 asks for "sustained changes in at least two available signals" — that requirement and the evidence conflict unless the second signal has a lower bar.
**Decision needed (Narayan)** — see DECISIONS.md D11.

## Accepted implementation conventions (logged, may revisit)
2-day linear ramp + 2-day recovery; HRV/temp effect drawn once per crew × preflight SD (ddof=1); persistence = strict ">" and signal identities may differ across the 2 days; red-flag symptom overrides missing signals with `suspect` quality; radiation: hourly background, 15-min event samples, linear 2 h rise, exponential decay (24 h), truncated ~9 d, normalised to 19.5 mSv; day-end sample at nextafter(24, 0); delay 0–20 min illustrative, blackouts none simulated (A12).

## Minor
- Skin-temperature simulated noise looks large relative to the grounded effect; revisit only via evidence (Mason2022 nightly variability), not to make S2 pass.
- `createdAt` makes full-file hashes vary between runs — fine; config/input hashes are stable.
