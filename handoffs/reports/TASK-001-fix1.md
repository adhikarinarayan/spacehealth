# TASK-001-fix1 — reconciliation complete; ready for Claude review

## Built

Reconciled the v0.1.1 contract implementation into nine JSON Schemas, one Pydantic mirror, one Zod mirror and one test suite per language. Tests read the shared manifest rather than deriving schema names from violation filenames. Duplicate dashboard source test removed. JSON Schema uses only standard keywords; composite-key uniqueness is documented there and enforced/tested in Pydantic and Zod.

Signal values accept finite implausible numbers for later model quality checks; optional signals allow omission or null. Cards use schemaVersion/source/cards with no simulated flag. Unknown status and missing/insufficient quality agree in all validators. A skipped check-in cannot contain reported symptoms. Strict JSON parsing rejects NaN; Pydantic/Zod additionally reject non-finite in-memory values. Public data copies match the four minimal valid fixtures.

## Files changed

- contracts/schemas/: clarified numeric signals, cards envelope and standard-only uniqueness description.
- contracts/fixtures/: shared manifest, normalized fixture names and finite/optional-null regression cases reconciled with the existing work.
- model/spacehealth_model/contracts.py: v0.1.1 mirror and optional-nonnull field handling.
- model/tests/test_contracts.py: manifest-driven agreement, schema well-formedness, manifest coverage, uniqueness and non-finite tests.
- dashboard/src/contracts/index.ts: finite signals, partial provenance records and cards envelope.
- dashboard/tests/contracts.test.ts: manifest-driven agreement, coverage, public fixture parity, uniqueness and non-finite tests.
- dashboard/src/contracts/contracts.test.ts: removed duplicate suite.
- REQUIREMENTS.md: runtime versions, all pinned Python snapshot entries, direct npm dependency versions/purposes and run commands.

App shell, package metadata and strict app-only TypeScript build configuration retained from the reconciled scaffold. No research, medical rules, simulator, detector, real UI screens or commit added. Historical drafts and protected planning/spec files were not edited in this fix.

## Commands and observed output

Runtime: Python 3.11.9, Node v26.13.1, npm 11.20.0.

`model/.venv/bin/python -m pytest -q model/tests`

```text
27 passed in 0.39s
```

`cd dashboard && npm ci --cache /tmp/spacehealth-npm-cache`

```text
added 85 packages, and audited 86 packages in 4s
found 0 vulnerabilities
```

This is a clean npm ci installation from the pinned lockfile. Initial sandboxed attempt encountered EAI_AGAIN registry failures and was interrupted; the authorized network retry succeeded. No NTFS symlink workaround was used.

`cd dashboard && npm test -- --run`

```text
Test Files  1 passed (1)
Tests  19 passed (19)
```

`cd dashboard && npm run build`

```text
> tsc --noEmit && vite build
vite v8.3.8 building client environment for production...
✓ 111 modules transformed.
dist/index.html                   0.44 kB │ gzip:  0.30 kB
dist/assets/index-BWlJDYaV.css    0.25 kB │ gzip:  0.20 kB
dist/assets/index-B8t4280N.js   315.23 kB │ gzip: 95.96 kB
✓ built in 635ms
```

No TypeScript errors. npm printed sandbox stream-fd warnings on some invocations, but the successful test/build commands exited 0.

## Fixture agreement

All rows below are exercised by both passing suites. JSON Schema column includes strict JSON parsing before schema validation: NaN is deliberately malformed JSON and is rejected at parsing.

| Fixture | JSON Schema | Pydantic | Zod | Expected |
| --- | --- | --- | --- | --- |
| valid/cards--minimal.json | accept | accept | accept | accept |
| valid/indicators--minimal.json | accept | accept | accept | accept |
| valid/mission--minimal.json | accept | accept | accept | accept |
| valid/validation--minimal.json | accept | accept | accept | accept |
| invalid/mission--missing-required-key.json | reject | reject | reject | reject |
| invalid/mission--day-zero.json | reject | reject | reject | reject |
| invalid/mission--unknown-signal-id.json | reject | reject | reject | reject |
| invalid/mission--skipped-checkin-with-symptoms.json | reject | reject | reject | reject |
| invalid/mission--nan.json | reject | reject | reject | reject |
| invalid/indicators--nominal-missing.json | reject | reject | reject | reject |
| invalid/indicators--unknown-valid.json | reject | reject | reject | reject |
| valid/mission--implausible-finite.json | accept | accept | accept | accept |
| valid/mission--optional-null.json | accept | accept | accept | accept |

Composite-key duplicates are separate Pydantic/Zod tests because standard JSON Schema cannot express that invariant. No custom JSON Schema extension is used.

## Dependencies and limits

No new Python packages or new npm direct dependencies added in this fix. Existing exact npm pins and lockfile are consistent and successfully installed by npm ci. See REQUIREMENTS.md for the full inventory.

No browser smoke test, screenshot, offline test, public deployment or scientific validation claimed. G0 owner review/contract freeze remains Claude/Narayan's step; this report records coding acceptance checks only. Cards remain contract placeholders. Future Pydantic JSON export should use exclude_unset=True to preserve omitted optional non-null evidence fields rather than serializing their internal None defaults.
