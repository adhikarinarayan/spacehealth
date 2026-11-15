# TASK-020 — Port the PR #1 dashboard design (orrery + glass styling), our own effects (D27)

**From:** Claude · **To:** Codex · **Report to:** `handoffs/reports/TASK-020.md`
Source of the design: local git branch `pr-1` (PR #1 by abhishek572003). Read files with `git show pr-1:<path>`. **Do not merge or cherry-pick the branch.**

## Narayan's decision (D27)
Take **only the dashboard design** from the PR; everything else is ours.

## Take from the PR (adapt onto current `main`)
- `dashboard/src/cosmos/SolarHero.tsx` — the orrery (planets by real orbital periods, Earth→Mars craft arc, comms link, day scrubber). **All visible text must come from `research/ui_copy.yaml` → `theme.orrery.*`** (already added by Claude): title, lead (with `{minutes}`), stat labels, blackout texts, scrub label, caption, aria (with `{pct}`, `{day}`). The delay value must stay labelled illustrative.
- `dashboard/src/cosmos/cosmos.css` — glass panels, segmented nav, typography, stronger Watch/Act emphasis. Keep it scoped to the dark display only.
- Instrument Serif fonts (`dashboard/public/fonts/instrument-serif*.woff2` + `Instrument-Serif-LICENSE.txt`, SIL OFL) — extract from `pr-1` with `git show pr-1:… > file` (binary-safe: use `git cat-file blob`).
- Dark token tweaks in `tokens.css` only if they still pass the existing AA contrast test.

## Do NOT take
- Anything under `dashboard/src/vendor/reactbits/` (MIT + Commons Clause — cannot be redistributed in our Apache-2.0 repo). No React Bits code, no `@ts-nocheck`.
- Any change to the mission switch labels/tag, self-care box, data loading, contracts, model or research.

## Build ourselves (replacing React Bits)
- **Starfield:** keep our existing `SpaceBackdrop` (no WebGL).
- **Tile glow:** CSS-only spotlight (radial-gradient that follows a CSS variable set on pointermove, static under reduced motion).
- **Headline shine:** CSS-only subtle gradient text, static under reduced motion.

## Fix the PR's bugs (with tests that click)
1. **Light display toggle** must switch and persist both ways (save and read the same value; default = dark), and the light display must not be overridden by cosmos styles.
2. **Mission switch** (Showcase / Blind test) must remain clickable and switch data — nothing may overlay or intercept the header controls (check z-index / pointer-events of orrery, glass layers, backdrop).

## File fence
`dashboard/src/**` (not `src/contracts/**`), `dashboard/public/fonts/**`, `dashboard/tests/ui/**`, `.github/workflows/tests/pages.test.mjs` (font count only), `README.md` (credits only: "Dashboard design (orrery, glass styling) adapted from a contribution by @abhishek572003; Instrument Serif under SIL OFL 1.1"). No new npm packages. No commit, no AI attribution lines.

## Acceptance (Claude re-runs)
```bash
export PATH="$HOME/.local/node/bin:$PATH"; cd dashboard
npx tsx scripts/make-demo.ts && npm test -- --run && npm run build
cd ../model && .venv/bin/python -m pytest -q
```
All existing tests (88 dashboard, 168 model) plus new ones pass; `grep -r "reactbits\|ts-nocheck" dashboard/src` returns nothing. Report: what was taken, what was rebuilt, the two bug fixes and their tests.
