# SpaceHealth requirements

Runtime observed: Python 3.11.9, Node.js v26.13.1, npm 11.20.0. Node is installed at `~/.local/node/bin`; prepend that directory to PATH. No new Python packages were installed for TASK-001-fix1.

## Python module

`model/requirements.txt` pins the provided environment snapshot, including transitive dependencies. `model/requirements.lock.txt` is the original installed snapshot. Core direct imports/planned libraries are identified below; remaining entries retain the existing environment for reproducibility.

| Package | Exact version | Purpose |
| --- | --- | --- |
| annotated-types | 0.8.0 | Pinned supporting dependency from the supplied environment |
| attrs | 26.1.0 | Pinned supporting dependency from the supplied environment |
| cloudpickle | 3.1.2 | Pinned supporting dependency from the supplied environment |
| contourpy | 1.3.3 | Pinned supporting dependency from the supplied environment |
| cycler | 0.12.1 | Pinned supporting dependency from the supplied environment |
| fonttools | 4.68.0 | Pinned supporting dependency from the supplied environment |
| iniconfig | 2.3.1 | Pinned supporting dependency from the supplied environment |
| joblib | 1.6.0 | Pinned supporting dependency from the supplied environment |
| jsonschema | 4.26.0 | JSON Schema validation |
| jsonschema-specifications | 2025.9.1 | Pinned supporting dependency from the supplied environment |
| kiwisolver | 1.5.1 | Pinned supporting dependency from the supplied environment |
| matplotlib | 3.11.2 | Experiment plots |
| narwhals | 2.28.0 | Pinned supporting dependency from the supplied environment |
| numpy | 2.4.6 | Numerical arrays |
| packaging | 26.3 | Pinned supporting dependency from the supplied environment |
| pandas | 3.1.1 | Data tables |
| pillow | 13.0.0 | Pinned supporting dependency from the supplied environment |
| pluggy | 1.7.0 | Pinned supporting dependency from the supplied environment |
| pydantic | 2.14.3 | Runtime contracts |
| pydantic_core | 2.50.4 | Pinned supporting dependency from the supplied environment |
| Pygments | 2.21.0 | Pinned supporting dependency from the supplied environment |
| pyparsing | 3.3.3 | Pinned supporting dependency from the supplied environment |
| pytest | 9.2.0 | Python tests |
| python-dateutil | 4.0.0 | Pinned supporting dependency from the supplied environment |
| PyYAML | 6.0.3 | Configuration parsing |
| referencing | 0.37.0 | Local schema reference registry |
| rpds-py | 2026.9.1 | Pinned supporting dependency from the supplied environment |
| scikit-learn | 1.9.1 | Future model comparisons |
| scipy | 1.17.1 | Scientific calculations |
| threadpoolctl | 3.8.0 | Pinned supporting dependency from the supplied environment |
| typing-inspection | 0.4.5 | Pinned supporting dependency from the supplied environment |
| typing_extensions | 4.16.0 | Pinned supporting dependency from the supplied environment |
| tzdata | 2026.6 | Pinned supporting dependency from the supplied environment |

## Dashboard

All direct npm dependencies are exact pins in `dashboard/package.json`. `package-lock.json` records their full dependency graph.

| Package | Exact version | Purpose |
| --- | --- | --- |
| react | 19.3.1 | UI components |
| react-dom | 19.3.1 | Browser rendering |
| recharts | 3.10.1 | Future trend charts; unused in G0 |
| zod | 4.6.7 | Runtime contracts |
| @types/node | 26.6.6 | Filesystem APIs in tests |
| @types/react | 19.3.0 | React types |
| @types/react-dom | 19.3.0 | Renderer types |
| typescript | 7.0.2 | Strict type checking |
| vite | 8.3.8 | Development and production builds |
| vitest | 5.1.0 | Contract tests |

## Commands

From the project root:

```sh
model/.venv/bin/python -m pytest -q model/tests
```

Or from `model/`:

```sh
.venv/bin/python -m pytest -q
```

From `dashboard/`:

```sh
export PATH="$HOME/.local/node/bin:$PATH"
npm ci
npm test -- --run
npm run build
npm run dev
```

The dashboard loads validated static fixtures from `public/data/`. Python and dashboard tests independently consume `contracts/fixtures/manifest.json`. JSON numeric constants NaN/Infinity are rejected at parsing; model and Zod validators also reject non-finite in-memory values. Composite-key uniqueness is enforced by Pydantic/Zod, not by custom JSON Schema extensions. No browser or offline QA has been performed at this scaffold stage.

## Model implementation (TASK-002)

No new packages. Uses the existing numpy Generator, PyYAML runtime research loading, SciPy independent integration test, Matplotlib PNG output, Pydantic and JSON Schema validation.

From `model/`:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m spacehealth_model.run --seed 0 --out out/
# Isolated synthetic scenario; S1 background remains enabled:
.venv/bin/python -m spacehealth_model.run --seed 0 --scenarios S2 --out out/s2/
```

CLI writes validated v0.2.0 mission/indicator files plus `reports/stage0_seed0.json`, an input snapshot and `reports/s2_seed0.png`. `createdAt` records actual run time, so complete mission file hashes differ between runs; seeded measurements/events are reproducible. `model/configs/stage0.yaml` documents provisional sampling/shape/profile conventions. The stage-0 run currently misses the supplied S2 acceptance target; see `handoffs/reports/TASK-002.md`. No model sweep or holdout evaluation is implemented.

## Dashboard (TASK-003)

Approved new development dependencies (installed exact versions from package-lock.json):

| Package | Version | Purpose |
| --- | --- | --- |
| @testing-library/react | 16.3.3 | UI rendering and interaction assertions |
| @testing-library/user-event | 14.6.10 | Keyboard/pointer interaction tests |
| jsdom | 31.0.1 | DOM environment for UI tests |
| tsx | 4.23.15 | TypeScript demo generator runner |

No new runtime packages. The generator reads `research/cards.yaml` via the existing `model/.venv/bin/python` + PyYAML; it does not install or modify Python dependencies.

From `dashboard/`:

```sh
export PATH="$HOME/.local/node/bin:$PATH"
npm ci
npx tsx scripts/make-demo.ts
npm test -- --run
npm run build
npm run dev
```

Default app source is `?data=demo`; `?data=data` loads `public/data/` without falling back to mock. All four envelopes validate before rendering. Mock card templates are expanded by the generator with illustrative context and rendered verbatim from its generated cards.json. No medical procedure copy is authored in components. This UI mock is not TASK-002 model output.

See `handoffs/reports/TASK-003.md` for test results, exact review URLs and the Firefox Snap screenshot limitation. Offline caching remains a later task.

## Model core (TASK-005)

No new packages. Sleep and radiation now replace export placeholders. From model/: `.venv/bin/python -m pytest -q tests/test_sleep_radiation.py` and `.venv/bin/python -m spacehealth_model.run --seed 0 --out out/`. Provisional dose-rate tiers live in configs/stage0.yaml and remain explicitly labelled placeholders. Derived evidence and missing/partial-input semantics are documented in handoffs/reports/TASK-005.md. The original M1 S2 failure and obsolete stage-0 placeholder assertion are not changed by this fenced task.

## Frozen model and holdout (TASK-011)

No additional packages. Production physiological status now uses the frozen M3 EWMA; M5 is explicit information only. The historical M1 evaluator remains available to the detector comparison and its documented-miss regression.

From `model/`:

```sh
.venv/bin/python -m pytest -q
.venv/bin/python -m spacehealth_model.compare --stage holdout --config configs/frozen_v1.yaml --out reports/holdout/
.venv/bin/python -m spacehealth_model.run --config configs/frozen_v1.yaml --seed 1000 --out out/release/
```

The first holdout is retained in `reports/holdout/`. A metadata-only release-writer bug required an explicitly labelled `reports/holdout/holdout-2/` and new freeze; numerical settings did not change. The compare command follows the configured report directory and reuses verified completed results instead of evaluating seeds again. Changed config/code/data or result hashes are rejected. See both FREEZE records and `handoffs/reports/TASK-011.md`.

The release case was preselected as seed 1000, Gaussian noise, effect scale 0.8. Four JSON envelopes are validated; `out/release/MANIFEST.json` records hashes, config hash and protocol seeds. No release data is copied to the dashboard in this task. Card templates are preserved from the frozen research snapshot; runtime action reasoning is in the indicators. Raw holdout outcomes include misses and false alerts; these are synthetic-scenario results, not clinical validation.

## Real civilian wearable check (TASK-016)

This optional evaluation adds **openpyxl 3.1.5** (MIT; direct XLSX reader) and its **et-xmlfile 2.0.0** dependency (MIT) to the existing model virtual environment. The task fence permits appending this document, not changing the frozen requirements snapshots.

```sh
cd model
.venv/bin/python -m pip install openpyxl==3.1.5 et-xmlfile==2.0.0
.venv/bin/python -m pytest -q tests/test_realdata.py
.venv/bin/python -m spacehealth_model.realdata.run --out reports/realdata/
```

The runner first verifies the Stanford ZIP and Mishra supplementary workbook against research/checksums.sha256, reads ZIP members directly, and writes only under the requested real-data report directory. Those source files must be available locally for the full run. The synthetic unit tests require neither file nor openpyxl. Fixed preprocessing, baseline eligibility, cohort selection, bootstrap settings and symptom-date handling are recorded before outcome analysis in reports/realdata/protocol.json. The frozen detector/configuration are imported read-only; no simulator, dashboard or holdout code is changed.
