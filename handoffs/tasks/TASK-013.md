# TASK-013 — Integration: real model output in the dashboard + offline mode (Gate G3)

**From:** Claude · **To:** Codex · **Created:** Sun 2026-11-15 ~13:20 CST
**Report to:** `handoffs/reports/TASK-013.md`
**Run AFTER TASK-010** (both touch the dashboard). Highest priority after TASK-010.

## Read first
`handoffs/reviews/TASK-011.md`, `DECISIONS.md` F12, `research/ui_copy.yaml` (`panels.validation.holdout_*`, `release_case_note`), `contracts/CONTRACT.md`, `model/out/release/MANIFEST.json`.

## Part A — model fixes (do NOT change detection results)
1. **Release side effect (bug found in review):** `export/release.py::save_release` always copies outputs into `model/out/release/` regardless of `--out`, so any run — including the pytest dev-seed CLI test — overwrites the real release. Copy into `model/out/release/` **only** when an explicit `--release` flag is given (and only for the frozen release case). Tests must write only to `tmp_path`; also stop tests/CLI dev runs from overwriting `model/reports/stage0_*` unless asked. Add a regression test: running the suite leaves `model/out/release/MANIFEST.json` unchanged.
2. **User-facing reason text:** reasons currently contain debug strings (e.g. "…for 1 nights in a row. M3 / watch_M3; rhr_bpm=62.863 bpm; baseline=…"). Make `reason` plain language from the cards/ui templates only, with correct singular/plural ("1 night", "2 nights"); move numeric detail into `evidence` items (value, unit, baseline, z, direction) and the M5 info item. Nominal reason: short neutral text (e.g. "Within your usual range."). Forbidden-words test stays.
3. These are presentation/export changes. If `verify_freeze` hashes export code, scope the freeze check to scientific code (detectors, modules' decision logic, sim, baseline, frozen config) and say exactly what you changed; detection outputs (statuses per crew-day) for seed 1000 must be **byte-identical** before/after — add a test comparing statuses.
4. Regenerate the release: `python -m spacehealth_model.run --config configs/frozen_v1.yaml --seed 1000 --out out/release/ --release`.

## Part B — dashboard uses the real output
1. `dashboard/scripts/sync-release.ts` (npm script `sync:release`): copies `model/out/release/{mission,indicators,validation,cards}.json` into `dashboard/public/data/`, verifying each sha256 against `MANIFEST.json` (fail loudly), and writes `public/data/MANIFEST.json`.
2. Default data source becomes the real release (`?data=data` default); the mock stays available at `?data=demo` with its MOCK banner. With real data show a small "Simulated mission · frozen model M3-frozen-v1 · holdout case seed 1000" label (from `release_case_note`) instead of the mock banner.
3. Action-card "why": show the indicator's plain `reason`; never render raw `{placeholder}` braces from card templates (test).
4. Detail evidence table shows the new evidence items, including M5 "multi-signal agreement" labelled *information only*.
5. Validation view: render `holdout_title`, each `holdout_lines` item and `holdout_note` from ui-copy, then the release-case rows from validation.json. Keep "Synthetic-scenario results — not clinical validation".
6. Replay/Today default to C2, day 41 (first real flag in the release case) when no URL params.

## Part C — offline mode
1. Hand-written service worker (`public/sw.js`, no new packages): precache the built app shell, hashed assets (generate the list at build time via a small Vite plugin/script) and `public/data/*.json`; cache-first for these, network-first for nothing else; versioned cache name; old caches deleted on activate. Register only in production builds.
2. Web app manifest (`public/manifest.webmanifest`) with an original simple icon (inline-generated PNG/SVG, no external art).
3. Tests: SW precache list includes every built asset and data file; registration skipped in dev/test.
4. Write `docs/OFFLINE_TEST.md` with exact manual steps for Narayan: `npm run build && npm run preview`, open once, DevTools → Network → Offline (or turn off Wi-Fi), reload, check Today/Detail/Replay/Validation; record browser + result.

## Acceptance (Claude re-runs)
```bash
cd model && .venv/bin/python -m pytest -q && .venv/bin/python -m spacehealth_model.run --config configs/frozen_v1.yaml --seed 1000 --out out/release/ --release
export PATH="$HOME/.local/node/bin:$PATH"; cd ../dashboard
npm run sync:release && npx tsx scripts/make-demo.ts && npm test -- --run && npm run build
```
Report: status-identity check result, sample before/after reason strings, list of precached files, and anything Narayan must do manually.

## Out of scope
New detection logic, retuning, theme changes beyond what integration needs, deployment (next task). No commit.
