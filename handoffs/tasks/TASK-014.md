# TASK-014 — Theme follow-ups from Narayan (small)

**From:** Claude · **To:** Codex · **Created:** Sun 2026-11-15 ~13:40 CST
**Report to:** `handoffs/reports/TASK-014.md` · **Run AFTER TASK-013** (same dashboard files).

## Narayan's feedback on TASK-010
1. "Between Earth and Mars it created a star kind of thing — replace it with a small astronaut's helmet."
2. "I don't see any change in colour and background." Cause: TASK-010 spec hid the starfield in light mode (his OS is in light mode) and opaque bars cover most of the starfield. Not a Codex error.

## File fence
`dashboard/src/**` (not `src/contracts/**`), `dashboard/tests/ui/**`. No new packages. Keep all TASK-013 integration behaviour.

## Changes
1. **Helmet marker:** replace the spacecraft/star marker on the trajectory with an original, simple astronaut-helmet SVG (rounded shell, visor with a soft highlight, small neck ring; no faces, flags, agency logos or mission patches), ~28–32 px, `aria-hidden`; keep the existing subtle beacon (reduced-motion respected). Keep its accessible text label for the position.
2. **Space theme always on:** the deep-space dark theme is the default regardless of the OS colour scheme. Remove the light-mode `display:none` on the starfield. Provide an optional "Light display" toggle (button with `aria-pressed`, remembered in localStorage with try/catch) for bright environments; default = space dark.
3. **Let the space show:** page background = starfield + nebula; panels/cards stay solid (or ≥ 90 % opaque) surfaces for readability; header/nav/heading bars become transparent or translucent (≥ 85 % opaque behind text) so stars are visible around and between panels. Slightly richer nebula (deep indigo/teal, very low alpha) — still calm.
4. Re-run the contrast tests for the dark tokens over the panel surfaces; keep ≥ 4.5:1 text, ≥ 3:1 icons.

## Tests
Helmet SVG renders as the marker (no star/spacecraft path); starfield present when OS prefers light; light toggle switches and persists (and works with storage blocked); contrast tests pass.

## Acceptance (Claude re-runs)
```bash
export PATH="$HOME/.local/node/bin:$PATH"; cd dashboard
npx tsx scripts/make-demo.ts && npm test -- --run && npm run build
```
No commit.
