# TASK-001-fix1 — Consolidate TASK-001 work into one passing implementation

**From:** Claude · **To:** Codex · **Supersedes the open parts of:** TASK-001
**Report to:** `handoffs/reports/TASK-001-fix1.md`

## Context
TASK-001 left two partial implementations of the validators and tests on each side, and a few root-level draft files that do not match the agreed layout (moved by Claude to `docs/history/`, not part of the public repo).
`contracts/CONTRACT.md` is now **v0.1.1** and answers the ambiguities you raised: schema accepts any finite number (plausibility → model sets `suspect`); optional signals omitted-or-null; uniqueness enforced in pydantic/Zod not JSON Schema; `insufficient` covers unusable baseline; cards envelope defined; fixture naming `<kind>--<violation>.json` + `fixtures/manifest.json`.

## Do
1. Pick ONE implementation per side and delete the other: one `model/tests/test_contracts.py`, one Zod module `dashboard/src/contracts/index.ts`, one dashboard contract test file (`dashboard/tests/contracts.test.ts`; delete `dashboard/src/contracts/contracts.test.ts`). Exclude tests from the app `tsc` build or add `@types/node` properly — the build must type-check cleanly.
2. Bring schemas, pydantic, Zod and fixtures in line with CONTRACT.md v0.1.1. Rename fixtures to the new convention; write `contracts/fixtures/manifest.json`; both test suites iterate the manifest. Every invalid fixture listed in CONTRACT.md §3 exists and fails all three validators; every valid one passes all three.
3. `dashboard/public/data/` holds copies of the valid fixtures (or a copy script) — keep it consistent.
4. Reconcile `dashboard/package.json` and `package-lock.json`, then run `npm ci` from clean.
5. Write `REQUIREMENTS.md` (root): Python + Node versions, every direct dependency with exact version + purpose, run commands per module.
6. Replace the fixture-agreement section of the report with the table: fixture × jsonschema × pydantic × zod × expected.

## Acceptance (Claude re-runs)
```bash
export PATH="$HOME/.local/node/bin:$PATH"
cd model && .venv/bin/python -m pytest -q
cd dashboard && rm -rf node_modules && npm ci && npm test -- --run && npm run build
```
All green, zero TypeScript errors.

## Out of scope
New features, UI work, editing `research/`, `plan.md`, `DECISIONS.md`, `contracts/CONTRACT.md`, `docs/history/`. No git commit.
