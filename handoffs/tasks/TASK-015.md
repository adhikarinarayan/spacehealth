# TASK-015 — Illustrative demo case (holdout seed 1002), disclosed (D20)

**From:** Claude · **To:** Codex · **Created:** Sun 2026-11-15 ~13:50 CST
**Report to:** `handoffs/reports/TASK-015.md`

## Decision (Narayan, D20)
The dashboard and video show an **illustrative** holdout case, clearly disclosed. Selection rule (applied by Claude to `model/reports/holdout/holdout-2/results.csv`, recorded in DECISIONS D20): Gaussian noise, effect scale 0.8 (same as the pre-selected case), S2 first watch = day 41 (typical, not the best day 40), S4 watch by 97 and sleep-debt act reached, all other scenarios pass → lowest qualifying seed = **1002** (S2 watch 41; S4 watch 96, act 99).
The pre-selected seed-1000 release stays exactly as is and remains available.

## File fence
Model: `model/spacehealth_model/export/**`, `model/spacehealth_model/run.py`, `model/tests/**`, new output dir `model/out/illustrative/`. Dashboard: `dashboard/src/**` (not contracts), `dashboard/scripts/**`, `dashboard/tests/ui/**`, `dashboard/public/data*/**`. **Do not change** `configs/frozen_v1.yaml`, detectors, modules' decision logic, sim, baseline, holdout artifacts, research.

## Build
1. Model: add `run.py --illustrative --seed 1002 --noise gaussian --effect-scale 0.8 --out out/illustrative/` that uses the frozen config and the holdout variant builder **without** modifying the freeze; writes the four contract files + `MANIFEST.json` with `"case": "illustrative", "selectedAfterHoldout": true, "selectionRule": "<the rule above>", "seed": 1002`. Refuse any seed not in the holdout seed list. Verify freeze before export. Test: statuses for seed 1002 equal the holdout case file's per-scenario first watch/act days.
2. Dashboard: `sync:release` gains a second source → `public/data/illustrative/` (hash-verified) next to the existing seed-1000 files (move those to `public/data/preselected/`, keep hashes). Default dataset = illustrative; selector "Mission case: Illustrative (seed 1002) · Pre-selected (seed 1000)" in the header/replay bar; URL `?case=illustrative|preselected`.
3. Show `panels.validation.illustrative_case_note` (illustrative) or `preselected_case_note` (pre-selected) as a persistent label under the mission header, from ui-copy. Validation view shows the holdout aggregate copy for both, plus the selected case's rows.
4. Default view: illustrative case, crew C2, **day 41** (derive from data: first physiological watch of C2 in the loaded case, not hard-coded).
5. Offline precache includes both datasets.

## Acceptance (Claude re-runs)
```bash
cd model && .venv/bin/python -m pytest -q && .venv/bin/python -m spacehealth_model.run --illustrative --seed 1002 --noise gaussian --effect-scale 0.8 --out out/illustrative/
export PATH="$HOME/.local/node/bin:$PATH"; cd ../dashboard
npm run sync:release && npm test -- --run && npm run build
```
Report: first watch/act days per scenario for the exported seed 1002, and confirmation the seed-1000 release manifest is unchanged. No commit.
