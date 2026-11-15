# TASK-001 — Scaffold + contract schemas, validators, fixtures (Gate G0)

**From:** Claude · **To:** Codex · **Created:** Sat 2026-11-14 17:22 CST
**Report to:** `handoffs/reports/TASK-001.md` (template in `plan.md` §4)

## Read first
`plan.md` (§1–§5), `contracts/CONTRACT.md` (authoritative spec), `Discussion.md` §4, `DECISIONS.md`.
Decisions in force: D1 Python model, D2 precomputed JSON, D3 Narayan runs you and Claude reviews, D4 git repo exists, D5 envs installed. D6 contract additions: implement them as specified in CONTRACT.md (pending Narayan's freeze — keep them easy to change).

## Environment
- Python: use `model/.venv/bin/python` (already has numpy, pandas, scipy, scikit-learn, pytest, pydantic 2, jsonschema, pyyaml, matplotlib). Do not install other Python packages without listing them in the report.
- Node: `export PATH="$HOME/.local/node/bin:$PATH"` (Node v26.13.1, npm bundled). Project is on an NTFS volume (ntfs3); if `npm install` has symlink problems, report it rather than working around silently.

## Build
1. `contracts/schemas/*.schema.json` (JSON Schema 2020-12) for: mission, daily reading, radiation event, crew member, scenario truth, indicators file, indicator, validation file, cards file. JSON Schema is the source of truth.
2. `contracts/fixtures/valid/` and `contracts/fixtures/invalid/` exactly as CONTRACT.md §3 lists (one invalid file per listed violation, name says the violation).
3. `model/` Python package skeleton `spacehealth_model/` with `contracts.py` (pydantic v2 models mirroring the schemas, including cross-field rules: checkin/symptoms, unknown⇔missing/insufficient, no NaN, missionDay ≠ 0) and empty subpackages `sim/ baseline/ detectors/ modules/ evaluate/ export/`. `model/requirements.txt` with pinned versions from `model/requirements.lock.txt`. `model/pyproject.toml` or equivalent so `pytest` runs from `model/`.
4. `model/tests/test_contracts.py`: every valid fixture passes both jsonschema and pydantic; every invalid fixture fails both.
5. `dashboard/`: Vite + React + TypeScript app shell (strict TS), Zod schemas in `dashboard/src/contracts/` mirroring the JSON Schemas, Vitest test that loads every fixture (valid pass / invalid fail). App renders a placeholder page that loads `public/data/` fixtures and shows "SIMULATED DATA — research prototype, not a medical device". Recharts installed but unused. No other UI work.
6. `REQUIREMENTS.md` at repo root: every Python and npm direct dependency with version and purpose; Node/Python versions; run commands per module.
7. `.gitignore` (venv, node_modules, dist, raw large data `research/data/raw/stanford_covid_wearables_mishra2020/*.zip`).

## Acceptance (Claude will re-run)
```bash
cd model && .venv/bin/python -m pytest -q            # all pass
cd dashboard && npm ci && npm test -- --run && npm run build   # all pass
```
Both validators agree on every fixture (report a table: fixture × jsonschema × pydantic × zod).

## Out of scope
Simulator, detectors, real UI screens, any medical wording, editing `research/`, `plan.md`, `DECISIONS.md`, `contracts/CONTRACT.md`. Do not commit; Claude reviews then commits.
