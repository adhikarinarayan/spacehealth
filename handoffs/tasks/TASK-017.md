# TASK-017 — README, CI and GitHub Pages deploy setup (Gate G4)

**From:** Claude · **To:** Codex · **Created:** Sun 2026-11-15 ~13:58 CST
**Report to:** `handoffs/reports/TASK-017.md` · **Run AFTER TASK-015** (pane 1). May overlap TASK-016 (fence).

## File fence
Create/edit: `README.md` (root), `model/spacehealth_model/run.py` (help text only), `.github/workflows/**`, `dashboard/vite.config.*`, `dashboard/package.json` scripts only, `dashboard/public/sw.js` / precache generation only if the base path requires it, `CITATION.cff`, `.gitignore`. Read-only: everything else, including the root `LICENSE` (Apache-2.0, added by Claude per D22). Do not push, create repos or deploy — Narayan does outward-facing steps.

## README.md (root)
Order:
1. Title, one-line description, badges placeholder (CI), and the disclaimer box: "Research prototype · simulated data · not a medical device · does not diagnose".
2. **Live demo / video** — `[[deploy URL]]`, `[[video URL]]` placeholders.
3. **Quick start (3 steps)**: prerequisites (Python 3.11, Node ≥ 22 — note the project used 26.13.1), model: venv + `pip install -r model/requirements.txt` + run commands (release, illustrative, holdout reuse, DONKI replay, real-data check if present); dashboard: `npm ci`, `npm run sync:release`, `npm run dev` / `npm run build && npm run preview`; tests for both.
4. **Insert `the README science section source` verbatim** (it is Claude-owned; do not edit its text).
5. **Repository layout** (research / model / dashboard / contracts / handoffs / docs) and the module-independence idea in 5 lines.
6. **Reproducibility**: frozen config hash, MANIFEST hashes, seeds, how to verify (`sha256sum`), papers not redistributed (fetch via DOIs in research/sources.md), Stanford zip not committed (download URL from DATA_INVENTORY).
7. **Credits & licences**: all direct dependencies from REQUIREMENTS.md with licences; bundled fonts Inter and IBM Plex Mono (SIL OFL 1.1, licence files in dashboard/public/fonts); NASA DONKI/CCMC acknowledgement; all original artwork.
8. **License**: Apache License 2.0 (see `LICENSE`); third-party fonts remain under SIL OFL 1.1; NASA data used under NASA's open-data terms.

## Small fix
- `model/spacehealth_model/run.py` argparse description still says "M1 physiological rules"; production uses frozen M3 (+ M5 info-only). Fix the help text only (allowed edit; presentation code outside the science freeze scope) and keep the full suite green.
- Real-data command for the README: `python -m spacehealth_model.realdata.run --out reports/realdata/` (needs the Stanford zip + supplementary xlsx; skip in CI).

## CI and deploy
- `.github/workflows/ci.yml`: on push/PR — Python 3.11 job (`pip install -r model/requirements.txt`, `pytest -q` in model/) and Node job (`npm ci`, `npm test -- --run`, `npm run build` in dashboard/). The Stanford zip and papers are absent in CI: tests that need them must skip with a clear reason, not fail.
- `.github/workflows/pages.yml`: build the dashboard and deploy `dashboard/dist` to GitHub Pages (official `actions/upload-pages-artifact` + `actions/deploy-pages`). Vite `base` must work under `https://<user>.github.io/<repo>/` (use a `BASE_PATH` env with default `/`); service worker scope and precache URLs must respect the base — add a test.
- `CITATION.cff` with title, team placeholder, date, repo URL placeholder.

## Acceptance (Claude re-runs)
```bash
cd model && .venv/bin/python -m pytest -q
export PATH="$HOME/.local/node/bin:$PATH"; cd ../dashboard && npm ci && npm test -- --run && npm run build && BASE_PATH=/spacehealth/ npm run build
```
Report the exact steps Narayan must do on GitHub (create public repo, push, enable Pages from Actions). No commit.
