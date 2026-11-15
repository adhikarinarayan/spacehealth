# TASK-002 — Contract v0.2 + simulator + M1 physiological vertical slice (Gate G1, part 1)

**From:** Claude · **To:** Codex · **Created:** Sat 2026-11-14 17:56 CST
**Report to:** `handoffs/reports/TASK-002.md`

## Read first
`plan.md` §6.2, `contracts/CONTRACT.md` (incl. §4 v0.2 missionProfile), `research/signals.yaml`, `research/scenarios.yaml`, `research/rules.yaml`, `research/cards.yaml`, `research/assumptions.md`, `research/model_candidates.md` (Stage 0 only), `DECISIONS.md` (D6–D10).
Research YAML files are the **single source** of numbers and text: load them at runtime (pyyaml); do not copy numbers or card text into code.

## Build
1. **Contract v0.2:** add `missionProfile` to mission schema / pydantic / Zod + fixtures + manifest exactly as CONTRACT.md §4; bump `schemaVersion` to `"0.2.0"`; keep all v0.1.1 tests green.
2. **Simulator** `model/spacehealth_model/sim/`: seeded (numpy Generator) 4 crew × days −14..−1, 1..180, profile `mars_transit_v1` (GCR 1.84 mSv/day from signals.yaml). Implements S1 background for all crew + S2 (C2), S3 (all), S4 (C3), N1 (C1), N2 (C4) from scenarios.yaml. Radiation: time-stamped `RadiationEvent` samples (hourly background + denser during S3), daily dose by trapezoid integration, `dose_coverage`, cumulative = sum of daily. `provenance` = `synthetic` everywhere. Emits `ScenarioTruth`. Each scenario can also be toggled alone (for toy runs).
3. **Baseline** `baseline/`: fixed preflight median, scale = max(1.4826·MAD, min_scale), `insufficient` if < min_valid_days; never reads days after the evaluated day.
4. **M1 physiological_change module** `modules/physiological.py`: rules.yaml physiological_change exactly (2 signals × 2 days, act rules, red-flag symptoms, unknown rule). Reason text built from cards.yaml templates; must never contain any `forbidden_words`.
5. **Export** `export/`: `mission.json`, `indicators.json` (physiological_change only for now; sleep/radiation emit `unknown` with reason "module not implemented yet" — keep contract-valid), all validated against the schemas before writing. CLI: `python -m spacehealth_model.run --seed 0 --out model/out/`.
6. **Tests** (pytest): baseline hand-checked numbers, zero-MAD → min_scale, insufficient → unknown, missing never nominal, no future leakage (perturbing day d+1 doesn't change day d), integration matches an independent numeric integral, S2 watch/act by day 42 on seed 0 with correct evidence signals, N1 no act, N2 unknown on gap days, forbidden words absent.
7. A quick PNG `model/reports/s2_seed0.png` (C2 rhr/hrv/temp with baseline band, onset/symptom lines) for Narayan's realism check.

## Acceptance (Claude re-runs)
```bash
cd model && .venv/bin/python -m pytest -q && .venv/bin/python -m spacehealth_model.run --seed 0 --out out/
cd dashboard && npm test -- --run && npm run build
```
Report S2 first watch/act day, N1/N2 outcomes, and any rules.yaml ambiguity you had to interpret (do not silently choose — list it).

## Out of scope
Other candidates M0/M2–M6, sleep and radiation modules (next task), dashboard UI, editing `research/`, `plan.md`, `DECISIONS.md`, `CONTRACT.md`. No commit.
