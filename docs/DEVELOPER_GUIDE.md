# SpaceHealth — Developer Guide

*For a developer joining the project. Last updated Sunday 15 Nov 2026, ~14:10 CST.*

SpaceHealth is an **offline astronaut health self-monitoring prototype** for the NASA Space Apps Challenge 2026. It compares each crewmember's nightly measurements with **their own preflight normal**, flags sustained changes, explains why, and turns each flag into an action card. It **does not diagnose**, and all data shown is **simulated** (with real NASA solar-storm timing).

If you only read one other file, read **`DECISIONS.md`**: every scope, model and wording decision, with the reason.

---

## 1. The 2-minute picture

| | |
|---|---|
| **Mission profile** | Mars-class transit, 180 days, 4 crew (C1–C4), 14 preflight baseline days (−14…−1), mission days 1…180 |
| **Three modules** | `physiological_change` (resting HR, HRV, skin temp, symptoms) · `sleep_alertness` (sleep hours) · `radiation` (warnings, dose rate, dose) |
| **Statuses** | `nominal` · `watch` · `act` · `unknown` (missing data is **never** nominal) |
| **Detector** | **M3 = EWMA** on resting-HR deviation from the fixed preflight baseline (λ = 0.2, limit 1.0). M5 (Mahalanobis) is shown as *information only* |
| **Validation** | Seeded simulator with known truth → 8-method comparison on dev seeds → frozen config → **holdout run once** → four real NASA DONKI storm replays → real-data check on Stanford wearables (in progress) |
| **Stack** | Python 3.11 (model) · React + Vite + TypeScript + Zod + Recharts (dashboard) · JSON Schema contract |
| **Licence** | Apache-2.0 (`LICENSE`); bundled fonts Inter + IBM Plex Mono under SIL OFL 1.1 |

---

## 2. Architecture — three independent modules

```text
 research/  ──(YAML rules, cards, copy)──►  model/ (Python)  ──(JSON files)──►  dashboard/ (React)
                                                 │                                   │
                                                 └──────────── contracts/ ───────────┘
                         JSON Schema + pydantic + Zod validators + shared fixtures (frozen)
```

- **`research/`** holds evidence and *all* numbers and wording: `signals.yaml`, `scenarios.yaml`, `rules.yaml`, `cards.yaml` (action-card text), `ui_copy.yaml` (every panel explanation), `grounding.md`, `assumptions.md`, `sources.md`, raw data. Code reads these files; **no medical wording is hard-coded in components**.
- **`model/`** simulates missions, computes baselines and statuses, evaluates, and exports four JSON files.
- **`dashboard/`** is a static, offline web app that only *reads* those JSON files (no detection logic in the UI).
- **`contracts/`** is the only coupling. `CONTRACT.md` is the human spec (v0.2, frozen); `schemas/*.schema.json` is the source of truth; `fixtures/` + `manifest.json` are tested by **both** Python and TypeScript validators.

Each module is testable alone. A change to a field name means updating spec + schemas + fixtures + model + dashboard + tests together (and a `DECISIONS.md` entry).

---

## 3. Repository layout

```text
SpaceHealth/
├── README.md              (being written — TASK-017)
├── DECISIONS.md           decisions D0–D22, findings F1–F14, workflow rules
├── REQUIREMENTS.md        every dependency, version, purpose
├── LICENSE                Apache-2.0
├── contracts/             CONTRACT.md, schemas/, fixtures/
├── research/
│   ├── *.yaml, *.md       rules, scenarios, cards, UI copy, grounding, assumptions, sources
│   ├── checksums.sha256   SHA-256 of every paper and dataset
│   ├── papers/            (git-ignored — paywalled PDFs are not redistributed)
│   └── data/raw/          nasa_donki_sep/ (committed) · stanford_covid_wearables_mishra2020/ (zip git-ignored)
├── model/
│   ├── spacehealth_model/
│   │   ├── sim/           seeded mission generator, space_weather.py (DONKI replay)
│   │   ├── data_sources/  donki.py (checksum-verified loader)
│   │   ├── baseline/      fixed preflight median / MAD baseline
│   │   ├── detectors/     candidates M0–M6 (M1 kept for the record)
│   │   ├── modules/       physiological.py (production = M3), sleep.py, radiation.py
│   │   ├── evaluate/      stage-2, holdout, frozen-config checks, donki_replay
│   │   ├── export/        contract-valid JSON export, release/illustrative publishing
│   │   ├── realdata/      Stanford check (TASK-016, in progress)
│   │   ├── run.py         main CLI · compare.py  comparison/holdout CLI
│   ├── configs/           stage0/1/2.yaml, frozen_v1.yaml (LOCKED)
│   ├── reports/           stage1/, stage2/, holdout/ (+ holdout-2/), donki_replay/
│   ├── out/               generated: release/ (seed 1000), illustrative/ (seed 1002)  — git-ignored
│   ├── tests/             pytest
│   └── EXPERIMENT_LOG.md  every experiment run
├── dashboard/
│   ├── src/               App.tsx, components/, data/ (loading, copy), theme/, contracts/ (Zod), offline.ts
│   ├── public/data/       illustrative/ and preselected/ (synced from model, hash-verified), demo/ (mock)
│   ├── public/sw.js       hand-written service worker (offline)
│   ├── scripts/           sync-release.ts, make-demo.ts, offline-build.mjs, check-offline.mjs
│   └── tests/             contracts.test.ts, ui/*.test.tsx
├── handoffs/              tasks/ (briefs) → reports/ (Codex) → reviews/ (Claude) — full audit trail
└── docs/                  DEVELOPER_GUIDE.md (this file), OFFLINE_TEST.md, submission/, reports/ (PDFs, git-ignored)
```

---

## 4. Setup

**Prerequisites:** Python 3.11, Node.js ≥ 22 (project uses 26.13.1), git. Linux/macOS shell assumed.

```bash
git clone <repo-url> SpaceHealth && cd SpaceHealth

# Model (Python)
python3.11 -m venv model/.venv
model/.venv/bin/pip install -r model/requirements.txt

# Dashboard (Node)
cd dashboard && npm ci && cd ..
```

On the original machine Node lives in `~/.local/node`; run `export PATH="$HOME/.local/node/bin:$PATH"` first if `node` is not found.

**Optional data not in git:**
- Papers: fetch via the DOIs/URLs in `research/sources.md` into `research/papers/` (checksums in `research/checksums.sha256`). Not needed to run anything except a few research cross-checks.
- Stanford wearables zip (378 MB, needed only for the real-data check): download URL in `research/data/DATA_INVENTORY.md` → `research/data/raw/stanford_covid_wearables_mishra2020/COVID-19-Wearables.zip`. Also needs `research/papers/Mishra2020_SupplementaryTables.xlsx`.

---

## 5. Run it

### Just see the dashboard
```bash
cd dashboard
npm run sync:release      # copy hash-verified model output into public/data/
npm run dev               # open the printed URL, e.g. http://127.0.0.1:5173/
```
Useful URLs (append to the base URL):

| URL | Shows |
|---|---|
| `/` | Showcase mission (seed 1002), crew C2, day 41 — first illness flag |
| `/?case=preselected` | Blind test mission (seed 1000, fixed before results) — includes a late flag and a miss |
| `/?crew=C2&day=72` | Solar-storm alert band (real DONKI timing) |
| `/?crew=C3&day=99` | Sleep-debt `act` |
| `/?view=crew&day=41` · `/?view=log` · `/?view=replay` | Crew grid · Mission log · Replay + Validation |
| `/?data=demo` | Old UI mock (bannered MOCK) — not model output |

Production + offline: `npm run build && npm run preview`, then follow `docs/OFFLINE_TEST.md`.

### Model commands (from `model/`)
```bash
.venv/bin/python -m pytest -q                                   # full test suite

# Publish the official pre-selected holdout release (seed 1000) → out/release/
.venv/bin/python -m spacehealth_model.run --config configs/frozen_v1.yaml --seed 1000 --out out/release/ --release

# Export the disclosed illustrative demo case (seed 1002) → out/illustrative/
.venv/bin/python -m spacehealth_model.run --illustrative --seed 1002 --noise gaussian --effect-scale 0.8 --out out/illustrative/

# Development run on a dev seed (writes only to --out)
.venv/bin/python -m spacehealth_model.run --seed 0 --out out/dev/

# Detector comparisons (historical, dev seeds only)
.venv/bin/python -m spacehealth_model.compare --stage 1 --seeds 0 1 2 --out reports/stage1/
.venv/bin/python -m spacehealth_model.compare --stage 2 --seeds $(seq 0 19) --out reports/stage2/

# Holdout — already run; re-invoking verifies hashes and REUSES the stored result (it cannot run twice)
.venv/bin/python -m spacehealth_model.compare --stage holdout --config configs/frozen_v1.yaml --out reports/holdout/

# Radiation robustness on four real NASA DONKI storms
.venv/bin/python -m spacehealth_model.evaluate.donki_replay --out reports/donki_replay/

# Real-data check (TASK-016, when finished)
.venv/bin/python -m spacehealth_model.realdata.run --out reports/realdata/
```
Note: `run.py --help` still says "M1 physiological rules" in its description; production uses M3 (to be corrected).

### Dashboard commands (from `dashboard/`)
```bash
npm test               # Vitest: contract + UI + theme + offline tests
npm run build          # type-check, build, generate + check offline precache
npm run sync:release   # model/out/{illustrative,release} → public/data/{illustrative,preselected} with SHA-256 checks
npx tsx scripts/make-demo.ts   # regenerate the UI mock AND ui-copy.json / cards.json from research/*.yaml
```
After editing `research/cards.yaml` or `research/ui_copy.yaml`, run `make-demo.ts` so the dashboard picks up the new text.

---

## 6. How the science is wired

| Piece | Where | Key facts |
|---|---|---|
| Baseline | `baseline/` | median of valid preflight days; scale = max(1.4826·MAD, per-signal minimum); < 10 valid days → `unknown`; fixed all mission; no future data (tested) |
| Physiological | `modules/physiological.py`, `detectors/` | M3 EWMA watch; act = red-flag symptom (or watch + red flag); M5 info-only; plain-language reasons from `cards.yaml` |
| Sleep | `modules/sleep.py` | watch = sleep z ≤ −2 on 2 nights; act = 7-night debt vs own normal ≥ 8.16 h (Van Dongen 2003), ≥ 5 valid nights |
| Radiation | `modules/radiation.py` | act on any SPE warning sample immediately; trapezoid dose integration; projection vs 600 mSv; dose-rate tiers are labelled **placeholders** |
| NASA data | `data_sources/donki.py`, `sim/space_weather.py` | DONKI SEP JSON, SHA-256 verified, GOES onsets grouped < 6 h, Sep-2017 onsets → days 72 00:30, 73 23:45, 77 16:25 |
| Simulator | `sim/generate.py` + structured fields in `configs/stage0.yaml` | scenarios S1–S4, N1, N2; effect sizes grounded (`research/grounding.md`); no parsing of prose |

**Evidence labels** used everywhere: *grounded* (source + page/table) · *direction-only* · *placeholder* · *assumption*. Never add a number without one.

---

## 7. Results so far (synthetic-scenario results, not clinical validation)

- **Stage 2 (dev seeds 0–19):** M3 flagged the illness-like change by symptom day 18/20; M5 13/20 (blind for crew with short HRV baseline).
- **Holdout (frozen, run once, 40 unique cases):** illness flagged by symptom day **25/40 (62 %)**, within the illness period 39/40; sleep restriction 26/40; every DONKI onset → immediate act; exercise spikes never act; missing data always unknown; ≈ 1.5 physiological / 0.8 sleep false `watch` episodes per crewmember per mission. Details: `model/reports/holdout/holdout-2/summary.md`, `DECISIONS.md` F12.
- **Four real NASA storms:** 24/24 checks pass (`model/reports/donki_replay/summary.md`).
- **Demo case:** illustrative holdout seed 1002, chosen after testing by a fixed rule and disclosed on screen (D20).
- **Stanford real-data check:** running (TASK-016).

The scientific basis, model maths, limits and "claims we can / cannot make" are in the PDF report (shared separately) and in the README sections "How we validated it", "Limits" and "Future work".

---

## 8. Rules you must not break

1. **Do not edit `model/configs/frozen_v1.yaml`, detectors, sim, baseline or holdout artifacts.** The freeze check (`evaluate/science_scope.py`) will refuse runs, and any change invalidates the holdout. A real fix means a new freeze + a clearly labelled new holdout, logged in `DECISIONS.md`.
2. **Never tune on holdout seeds (1000–1019).** Dev seeds are 0–19.
3. **Missing ≠ zero ≠ nominal.** Missing values are `null`; status is `unknown`.
4. **No diagnosis wording** ("infection detected", "you have…") — tests enforce a forbidden-word list.
5. **Urgent cards** (radiation act, red-flag symptom) are never hidden by the 3-routine-card cap.
6. **Ground messages are "queued", never "sent/delivered".**
7. **All text from `research/*.yaml`.** Don't write medical or explanatory prose in components.
8. **Original art only** — no agency logos, mission patches or photos of real people.
9. `model/out/release/` is written **only** with `--release` (a test guards this; a past bug overwrote it).
10. **`research/checksums.sha256` is part of the locked dataset** (the DONKI loader verifies against it). Never edit it; add checksums for new sources to `research/checksums_additional.sha256`.

---

## 9. How work is organised

- **Narayan** decides scope, model choice, thresholds, datasets, publication.
- **Claude** (AI, non-coding) does research, grounding, specs, task briefs, reviews (re-runs every test), the decision log and documents.
- **Codex** (AI, coding) implements each brief.
- Loop: `handoffs/tasks/TASK-###.md` → Codex writes `handoffs/reports/TASK-###.md` → Claude writes `handoffs/reviews/…` → commit. Each brief has a **file fence**; when two Codex sessions run in parallel they must stay inside their fences.
- One decision log (`DECISIONS.md`), one experiment log (`model/EXPERIMENT_LOG.md`).

---

## 10. Status and what's next (deadline Sun 15 Nov, target 20:00 CST)

| Done | Next |
|---|---|
| Contract · simulator + DONKI · 3 modules · detector comparison · freeze + holdout · four-storm test · dashboard v1 + theme + offline + real output + illustrative case | **TASK-016** Stanford real-data check (running) → **TASK-017** README, CI, GitHub Pages → final dashboard touches → manual offline test → push to public GitHub → 30-s video → submission form |

Submission drafts (project page text, video script) are kept outside the public repository.

---

## 11. Gotchas

- The original working copy is on an NTFS (ntfs3) volume; everything works, but if you see odd permission/symlink issues on Linux, clone onto a native filesystem.
- Codex runs in a sandbox: `npm`/`pip` with network sometimes need approval in its pane.
- `dashboard/public/data/*.json` at the root of `data/` are compatibility copies of seed 1000; the app loads only `data/illustrative/` and `data/preselected/`.
- Headless-browser screenshots fire before data loads (you'll see "Loading mission files…"); review in a real browser.
- Holdout `results.csv` has 120 rows but only 40 unique cases (effect-scale factor does not affect M3/sleep; both noise models share the same 20 seeds).
