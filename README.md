# SpaceHealth

Personal-baseline health monitoring and actionable guidance for a simulated Mars-transit crew.

[![CI](https://github.com/adhikarinarayan/spacehealth/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/adhikarinarayan/spacehealth/actions/workflows/ci.yml)

> **Research prototype · simulated data · not a medical device · does not diagnose**

## Team

Narayan Adhikari · Abhishek Sunil Tiwari · Shweta Sunil Tiwari — NASA Space Apps Challenge 2026

## Live demo / video

- Live demo: https://spacehealth-demo.vercel.app/ (offline-capable after first load)
- Walkthrough: 30-second video — link added at submission

## Quick start — three steps

### 1. Prepare Python and Node

Use Python **3.11** and Node **≥22.12.0** (Node 22 or newer; this project used **26.13.1**, npm 11.20.0). Run from the repository root unless a command changes directory. On the development machine, `export PATH="$HOME/.local/node/bin:$PATH"` enables Node.

```sh
python3.11 -m venv model/.venv
model/.venv/bin/python -m pip install -r model/requirements.txt
# Restore recorded, hash-verified exports on a clean clone; no holdout rerun:
model/.venv/bin/python .github/workflows/prepare_model_outputs.py
```

### 2. Reproduce the model and check its results

```sh
cd model
.venv/bin/python -m pytest -q
.venv/bin/python -m spacehealth_model.run --config configs/frozen_v1.yaml --seed 1000 --out out/release/ --release
.venv/bin/python -m spacehealth_model.run --illustrative --seed 1002 --noise gaussian --effect-scale 0.8 --out out/illustrative/
# Verifies and reuses the completed holdout; does not evaluate it again:
.venv/bin/python -m spacehealth_model.compare --stage holdout --config configs/frozen_v1.yaml --out reports/holdout/
.venv/bin/python -m spacehealth_model.evaluate.donki_replay --out reports/donki_replay/
cd ..
```

Optional real-data sanity check, after separately obtaining the Stanford ZIP and Mishra supplementary XLSX (see Reproducibility). Synthetic unit tests do not require these files or openpyxl; the full real-data command is skipped in CI because the inputs are not redistributed.

```sh
cd model
.venv/bin/python -m pip install openpyxl==3.1.5 et-xmlfile==2.0.0
.venv/bin/python -m spacehealth_model.realdata.run --out reports/realdata/
cd ..
```

### 3. Run the dashboard

```sh
cd dashboard
npm ci
npm run sync:release
npm test -- --run
npm run dev
# Or, stop the dev server and preview the production/offline build:
npm run build && npm run preview
```

Open the local URL printed by Vite. The default is the disclosed illustrative case, seed 1002; the header switches to the pre-selected seed 1000. Direct links use `?case=illustrative` or `?case=preselected`; `?data=demo` explicitly selects the UI-development mock. Production offline checks are documented in [docs/OFFLINE_TEST.md](docs/OFFLINE_TEST.md). The service worker is not registered by the development server.

For repository-path hosting, run `BASE_PATH=/spacehealth/ npm run build` from dashboard/. `BASE_PATH` defaults to `/` and must include leading/trailing slashes. The build checks shell/font URLs, worker registration/scope and offline loading of both cases at that base.


<!-- Claude-owned README sections. Codex inserts this file verbatim into README.md (between the setup and credits sections). [[…]] = fill from final results or remove. -->

## What SpaceHealth does

On the way to Mars a message to Earth can take up to ~20 minutes each way, so astronauts must notice health problems themselves. SpaceHealth compares each crewmember's nightly measurements with **their own preflight normal**, flags sustained changes, explains why, and turns each flag into a next step — involving the onboard crew medical officer first and queuing a message to the ground separately. Statuses are `nominal`, `watch`, `act`, or `unknown`; missing data is never shown as healthy. **It does not diagnose.**

| Module | Watch | Act | Main evidence |
|---|---|---|---|
| Physiological change | EWMA (λ = 0.2, limit 1.0) of resting-heart-rate deviation from the fixed preflight baseline | Red-flag symptom (fever, shortness of breath, chest pain, fainting, vision change) | Li 2017; Mishra 2020; Alavi 2022 |
| Sleep & alertness | Sleep ≤ −2 robust SD below own normal on 2 nights | 7-night sleep debt vs own normal ≥ 8.16 h (≈ one night without sleep) | Van Dongen 2003; Belenky 2003; NASA HRP sleep evidence report |
| Radiation | Projected mission + career dose ≥ 600 mSv; dose-rate caution tier (placeholder) | Any solar-particle-event warning, immediately; dose-rate shelter tier (placeholder) | NASA-STD-3001 Vol 1 Rev C; Zeitlin 2013; Hassler 2014 |

A three-signal Mahalanobis check is shown as *information only* ("multi-signal agreement"); it never changes a status.

### In flight vs. this prototype

- **In flight:** wearable signals (overnight resting heart rate, HRV, skin temperature, sleep), dosimeter readings and space-weather warnings would arrive automatically; the astronaut adds only a one-minute daily check-in (symptoms). Each morning SpaceHealth updates the three statuses against that person's preflight normal.
- **This prototype:** a complete simulated 180-day mission is computed in advance by the locked model and loaded into the dashboard, so it runs fully offline. *Today* shows exactly what the astronaut would have seen on any chosen day; *Replay* plays the mission forward. A live check-in form with on-device scoring is the first item of future work.

### How this maps to the challenge's health areas

| Area | v1 status | What it does / why not yet |
|---|---|---|
| Immune changes | Partly — early warning | Watches resting heart rate (primary), HRV, skin temperature and symptoms — the body's response while fighting something — and flags an illness-like change to check. Does not measure immune function or diagnose infection. |
| Cardiovascular | Partly | Tracks nightly resting heart rate and HRV and flags sustained shifts. Does not yet detect deconditioning (fainting on standing), which needs blood pressure or a stand-up test. |
| Bone health | Not yet | Needs bone-density measurement; an exercise log cannot measure it. Planned as a context module (see Future work). |
| Radiation | Yes | Real NASA DONKI storm timing, dose accounting, 600 mSv career-limit projection. |
| Sleep & alertness | Yes | Sleep vs own normal; 7-night sleep debt (Van Dongen 2003). |

## Evidence and data

Every number is labelled **grounded** (source + page/table), **direction-only**, **placeholder**, or **assumption** — see `research/grounding.md`, `research/assumptions.md`, `research/sources.md` (39 sources, SHA-256 checksums; paywalled PDFs are not redistributed).

- **NASA DONKI** (CCMC Space Weather Database, api.nasa.gov): the simulator reads the downloaded solar-energetic-particle event files (checksum-verified) and replays the real September 2017 GOES-observed onsets on mission days 72–77. Timing only — dose comes from Zeitlin 2013 and is split across onsets (assumption A3b); events were observed near Earth.
- **NASA-STD-3001 Vol 1 Rev C**: 600 mSv career limit; 250 mSv is a vehicle design requirement, **not** an alert trigger.
- **MSL RAD** (as published): Mars-cruise dose 1.84 ± 0.33 mSv/day; storm dose 19.5 mSv (Mar 2012).
- **Mishra 2020 supplementary tables**: illness resting-heart-rate rise, median +5.6 bpm (IQR 3.1–8.6), computed by us.
- **Stanford COVID-19 wearables** (Mishra 2020): real civilian Fitbit data used for a sanity check of the frozen detector (zip not redistributed; see `research/data/DATA_INVENTORY.md`).

## How we validated it

1. **Simulator with known truth** — 4 crew × (14 preflight + 180 mission) days; scenarios: quiet mission, illness-like change (day 40, symptoms day 42), real DONKI solar storm (day 72), sleep restriction (days 95–101), exercise spikes, missing data.
2. **Detector selection without tuning** — eight published methods, literature-default parameters, discard rules fixed in advance, development seeds only. EWMA (M3) chosen: 18/20 development runs flagged by symptom day.
3. **Frozen holdout, run once** (config SHA-256 `03632b3d…`): new seeds, illness effect drawn across the published range, heavier-tailed noise. 40 unique cases:
   - Illness-like change flagged **by symptom day in 25/40 (62 %)**, within the illness period in 39/40; strong dose–response (rises ≥ 6 bpm caught early, 3–4.5 bpm mostly 1–4 days late).
   - Sleep restriction flagged by day 97 in 26/40; 11 never flagged (restriction small relative to some crew's normal sleep).
   - Every DONKI solar-event onset → immediate `act`; exercise spikes never `act`; missing data always `unknown`.
   - Routine false alerts ≈ 1.5 physiological and 0.8 sleep `watch` episodes per crewmember per 180-day mission.
4. **Real NASA storm robustness** — four DONKI windows (2017-09, 2021-10, 2024-05, 2024-10; 12 onset episodes): 24/24 checks pass (immediate act at every onset, renewal during an active warning, clearing, exact dose).
5. **Real-data sanity check** — the frozen detector, unchanged, on real civilian Fitbit data (Stanford COVID-19 wearables, Mishra 2020), protocol fixed before looking at results. Of 21 evaluable COVID-19 cases, it raised `watch` within 7 days of symptom onset in **13 (62 %, 95 % CI 38–81 %)** and at or before onset in **8 (38 %)**. In 64 people with no reported illness it raised about **2.5 `watch` episodes per 100 nights** — at that rate a random 15-night window would contain an alert about 31 % of the time, so detection is roughly **twice chance**: a real but modest signal. Real-world false alerts were about three times the simulator's rate, so the simulated false-alert numbers are optimistic. This is a sanity check, not a replication of Mishra 2020 or a clinical sensitivity estimate (`model/reports/realdata/summary.md`).

The dashboard opens on the **showcase mission** (holdout seed 1002), chosen after testing by a fixed rule (typical success, not the best). The **blind test mission** (seed 1000), fixed before any results were seen, is one click away and shows a late illness flag and a missed sleep restriction.

## Limits — what we can and cannot claim

- Health performance is measured mainly on **our simulator**; effect sizes are grounded, but this is partly circular. Results are **synthetic-scenario results, not clinical validation**.
- On real civilian data the detector is weaker (≈ 2× chance) and noisier (≈ 3× the simulated false-alert rate) than in simulation; the simulator's noise model is optimistic.
- HRV and skin-temperature effect sizes are direction-only from the literature.
- Evidence comes largely from civilians on Earth; microgravity changes physiology.
- Radiation dose-rate tiers are placeholders (operational values are not public); warning-based `act` does not depend on them.
- 14-day baselines, no real astronaut data, no user testing with crews.
- **Not a medical device. Does not diagnose.** Recording an action is not evidence that it caused recovery.

## Future work — how to make detection stronger

The real-data check shows a real but modest signal (≈ 2× chance) with about three times the simulated false-alert rate. Both data and algorithm contribute; with 21 cases we cannot yet separate them. The next steps, in order, each with its own lock-then-test protocol so improvements stay honest:

1. **Live daily check-in with on-device scoring.** A one-minute symptom check-in and in-browser evaluation, so the app updates the moment data arrives instead of loading a pre-computed mission.
2. **Bone-health module.** Track exercise adherence and show mission-length bone-loss *context* from published ISS rates (about 1–1.5 % hip bone per month; Lang et al. 2004) — population context, not a personal prediction.
3. **Cardiovascular deconditioning.** A simple daily stand-up test (heart-rate rise on standing) plus blood pressure, to flag orthostatic risk before landing (Lee et al. 2015).
4. **Immune monitoring.** Periodic saliva viral-shedding checks alongside wearable signals, following NASA's astronaut studies (Rooney et al. 2019).
5. **Calibrate on real healthy noise.** Re-fit the noise floor and EWMA limit using only people with no reported illness (no illness labels involved), lock, then test on illness cases — instead of settings inherited from the simulator.
6. **Add activity context.** Normalise heart rate by steps (Mishra 2020, HROS) so exercise, travel and busy days are less often mistaken for change.
7. **Slowly adapting baseline with safeguards.** A streaming-median baseline (Alavi 2022, NightSignal) that updates only when the person is stable, so seasons and fitness changes do not accumulate as false alerts — without letting a developing problem become "normal".
8. **Use more signals when they exist.** Astronaut wearables (e.g. CSA Bio-Monitor) record HRV, skin temperature and respiration; the multi-signal check (currently information only) can become a corroborating input.
9. **Longer preflight baselines.** Real missions have months of preflight data, not 14 days; this makes each person's normal much more precise.
10. **More and better-labelled real data.** Larger cohorts with confirmed onset dates, analogue missions (e.g. HERA, Mars-520-style isolation studies), and eventually crew data under proper governance.
11. **Real operational inputs.** Replace placeholder radiation dose-rate tiers with mission-approved values, and connect to real dosimeter and space-weather feeds.
12. **Human factors.** Test the interface and action cards with crew-medical-officer trainees and astronaut-analogue crews.

## Use of AI tools

- **Claude (Anthropic)** was used to plan the code (research support, specifications and task briefs, review of each delivery) and for logging and documentation.
- **Codex (OpenAI)** wrote the code and tests from those plans.
- All decisions were made by the team and are recorded in `DECISIONS.md`; the task → report → review trail is in `handoffs/`. Code in this repository is AI-generated under the team's direction and review.

## Repository layout

| Directory | Contents |
|---|---|
| `research/` | Sources, grounding, assumptions, structured rules and checksum manifests |
| `model/` | Frozen detectors, simulator, exports, tests and evaluation reports |
| `dashboard/` | React/Vite app, local fonts, validated data and offline service worker |
| `contracts/` | Shared JSON schemas, valid/invalid fixtures and contract documentation |
| `handoffs/` | Task briefs, implementation reports and review trail |
| `docs/` | Design, offline testing, submission and supporting documentation |

The physiological, sleep/alertness and radiation modules evaluate independently.  
Each produces its own status, evidence, uncertainty and action-card reference.  
M3 decides physiological status; M5 agreement is information only.  
Radiation act cards remain first and outside the routine-card cap.  
The shared contracts connect model outputs to the dashboard without moving detection logic into the UI.

## Reproducibility

Frozen configuration: `model/configs/frozen_v1.yaml`, SHA256 **`03632b3d13fbcc888a5bed3511939694989ed8a72c9e594c230035279bc2d7e0`**. The holdout protocol uses seeds **1000–1019**, Gaussian and Student-t noise, effect scales **0.6, 0.8, 1.2**; variants of a seed are correlated, not independent new participants. Seed **1000**, Gaussian/0.8, was pre-selected. Seed **1002**, Gaussian/0.8, was selected after holdout under the disclosed rule stored in its manifest. Real-data bootstrap RNG seed is **20261115**.

Each `MANIFEST.json` records the four file hashes, seed, frozen-config hash and case metadata. The public copies are committed; `model/out/` is generated and ignored. Restore them with the helper in step 1, or regenerate with the CLI and sync. The original holdout and labelled metadata-repair holdout are retained, including their FREEZE/COMPLETE records; completed results are verified and reused, never silently rerun.

Recorded manifest hashes at this documentation update:

| Manifest | SHA256 |
|---|---|
| `dashboard/public/data/preselected/MANIFEST.json` | `b3a49dd7d0787c372b3b0bf9ba9e16248c9f2ea2c15b3c2744a0213f8aade1b6` |
| `dashboard/public/data/illustrative/MANIFEST.json` | `4bd849a1c53a0a90a8be77a176f4487cc0e4f9c44cd702080eb79963003b0526` |

Verify the local config, recorded manifests and individual case files from the root:

```sh
sha256sum model/configs/frozen_v1.yaml dashboard/public/data/{preselected,illustrative}/MANIFEST.json
model/.venv/bin/python - <<'VERIFY'
import hashlib, json
from pathlib import Path
for case in ("preselected", "illustrative"):
    folder = Path("dashboard/public/data") / case
    manifest = json.loads((folder / "MANIFEST.json").read_text())
    for name, expected in manifest["files"].items():
        actual = hashlib.sha256((folder / name).read_bytes()).hexdigest()
        assert actual == expected, (case, name)
    print(case, "verified", manifest["seed"])
VERIFY
```

Measurements and statuses are seeded; regenerated mission files include a new `createdAt`, so their full file hashes and manifest hashes can change. Always verify against the manifest produced with that export, not an older timestamped file. Frozen scientific-code checks and byte-identity tests protect detection behavior separately.

Papers are **not redistributed**. Obtain them through the DOIs in [research/sources.md](research/sources.md), respect their licences/access terms, and place optional source files at the filenames listed in `research/checksums.sha256`. The optional real-data check needs `research/papers/Mishra2020_SupplementaryTables.xlsx` as well as the ZIP. The ZIP is not committed; the [data inventory](research/data/DATA_INVENTORY.md) records its location. Its download is linked by the original [Mishra study’s Data availability statement](https://www.nature.com/articles/s41551-020-00640-6): [Stanford COVID-19-Wearables.zip](https://storage.googleapis.com/gbsc-gcp-project-ipop_public/COVID-19/COVID-19-Wearables.zip). Save it to `research/data/raw/stanford_covid_wearables_mishra2020/COVID-19-Wearables.zip` and verify both input hashes before running the analysis. The data inventory itself does not currently include the download URL.

### CI

CI runs Python 3.11 tests and Node 26.13.1 tests/builds on pushes and pull requests. It restores ignored model fixtures from the committed dashboard exports after hash verification; it does not rerun the frozen holdout or download private/optional papers and wearable inputs. Synthetic real-data protocol tests run normally without them.

### Deployment (Vercel)

Import the repository in Vercel and use these project settings:

| Setting | Value |
|---|---|
| Root Directory | `dashboard` |
| Install Command | `npm ci` |
| Build Command | `npm run build` |
| Output Directory | `dist` |
| Node.js Version | `22.x` |

`dashboard/vercel.json` records the install, build and output settings. Leave `BASE_PATH` unset for root hosting. After deployment, check both mission cases and follow [docs/OFFLINE_TEST.md](docs/OFFLINE_TEST.md).

## Credits & licences

Direct Python libraries used by the project (versions/purposes in [REQUIREMENTS.md](REQUIREMENTS.md); the full environment, including supporting dependencies, is pinned in `model/requirements.txt`):

| Dependency | Licence |
|---|---|
| NumPy | BSD-3-Clause; distribution includes separately licensed bundled components |
| SciPy | BSD-3-Clause; bundled components retain their licences |
| pandas | BSD-3-Clause |
| scikit-learn | BSD-3-Clause |
| PyYAML | MIT |
| Pydantic | MIT |
| jsonschema | MIT |
| referencing | MIT |
| Matplotlib | Matplotlib licence (PSF-based) |
| pytest | MIT |
| openpyxl (optional) | MIT |
| et-xmlfile (optional openpyxl dependency) | MIT |
| fonttools (local font preparation) | MIT |

Direct dashboard dependencies and development tools from REQUIREMENTS.md / package.json:

| Dependency | Licence |
|---|---|
| React, react-dom | MIT |
| Recharts | MIT |
| Zod | MIT |
| @types/node, @types/react, @types/react-dom | MIT |
| TypeScript | Apache-2.0 |
| Vite, Vitest | MIT |
| @testing-library/react, @testing-library/user-event | MIT |
| jsdom | MIT |
| tsx | MIT |

Bundled **Inter** and **IBM Plex Mono** font assets are local subsets under **SIL Open Font License 1.1**; notices are in [dashboard/public/fonts/Inter-LICENSE.txt](dashboard/public/fonts/Inter-LICENSE.txt) and [dashboard/public/fonts/IBM-Plex-LICENSE.txt](dashboard/public/fonts/IBM-Plex-LICENSE.txt). Supporting/transitive libraries and bundled components retain their own upstream notices; the table does not relicense them.

Acknowledgements: NASA **CCMC / DONKI** supplies the real near-Earth event onset timings; published NASA/MSL RAD work supplies cited context, not measured Mars-transit crew data. Stanford/Mishra study authors supply the optional civilian wearable dataset and supplementary metadata. Earth, Mars, the EVA helmet, orbital marks, landscape, badges and app icon are original SVG/CSS artwork created for this prototype; there are no agency logos or external photographs.

Dashboard design (orrery, glass styling) adapted from a contribution by @abhishek572003; Instrument Serif under SIL OFL 1.1.

## License

Code is licensed under the **Apache License 2.0**; see [LICENSE](LICENSE). Third-party fonts remain under **SIL OFL 1.1**. NASA data is used under NASA’s open-data terms, with source attribution; the code licence does not replace data, publication or dependency terms.
