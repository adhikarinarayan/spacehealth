# TASK-018 — Complete (Vercel hosting and CI cleanup)

- Added `dashboard/vercel.json` with exactly `installCommand: npm ci`, `buildCommand: npm run build`, and `outputDirectory: dist`.
- Confirmed `MPLCONFIGDIR` is in the pytest step environment, not the model job environment. No additional changes to ci.yml were made.
- `.github/workflows/pages.yml` remains deleted. Kept `.github/workflows/tests/pages.test.mjs` and all BASE_PATH support in dashboard/vite.config.ts unchanged.
- Replaced README's GitHub Pages deployment instructions with a short Deployment (Vercel) section: Root Directory dashboard; install npm ci; build npm run build; output dist; Node 22.x. Preserved the Live demo line exactly, all science content, and all text outside the hosting section.
- Existing netlify.toml from the previous request was left untouched.

Both requested commands completed with exit 0. Local build verification used the installed Node 26.13.1; the documented Vercel project setting is Node 22.x. No commit, push or deployment.

## Model verification output

Command: `cd model && .venv/bin/python -m pytest -q`

```text
........................................................................ [ 42%]
........................................................................ [ 85%]
........................                                                 [100%]
168 passed in 56.66s
```

## Dashboard verification output

Commands: `export PATH="$HOME/.local/node/bin:$PATH"; cd dashboard && npm run build` (from repository root).

```text

> spacehealth-dashboard@0.1.0 build
> tsc --noEmit && vite build && node scripts/check-offline.mjs && npm run test:pages

vite v8.3.8 building client environment for production...
transforming...
✓ 512 modules transformed.
rendering chunks...
computing gzip size...
dist/index.html                   0.53 kB │ gzip:   0.34 kB
dist/assets/index-Dn33IcOu.css   28.82 kB │ gzip:   6.43 kB
dist/assets/index-BrFb7n0S.js   356.81 kB │ gzip: 109.33 kB
dist/assets/Detail-Diy9nopP.js  376.83 kB │ gzip: 108.32 kB

✓ built in 886ms
Offline manifest verified: 34 files; spacehealth-a1ca20257b15f9771d4b

> spacehealth-dashboard@0.1.0 test:pages
> node --test ../.github/workflows/tests/pages.test.mjs

✔ ../.github/workflows/tests/pages.test.mjs (150.065923ms)
ℹ tests 1
ℹ suites 0
ℹ pass 1
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 163.443165
```
