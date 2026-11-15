# TASK-010 — Dashboard theme: deep space, Mars transit, storm mode (D16)

**From:** Claude · **To:** Codex · **Created:** Sun 2026-11-15
**Report to:** `handoffs/reports/TASK-010.md`
**Run AFTER TASK-008 finishes** (same files). May run alongside model tasks (TASK-007/009).

## Narayan's request (D16)
Deep-space background, an original Mars icon at the top right, and: Earth→Mars trajectory bar, comms-delay link, solar-storm alert mode, crew badges + ship clock. Constraint from plan: "mission-control calm, not sci-fi chrome" — theme frames the data, never competes with it.

## File fence
`dashboard/src/**` (not `src/contracts/**`), `dashboard/scripts/**`, `dashboard/public/demo/**`, `dashboard/tests/ui/**`. No new npm packages. All new text from `research/ui_copy.yaml` → `theme.*` keys (regenerate via make-demo). Read-only: research, contracts, model.

## Hard rules
- **Original artwork only**, as inline SVG/CSS in the repo. No NASA/ESA/SpaceX logos, insignia, mission patches, photos of real people, or downloaded images/fonts at runtime (offline).
- **Readability first:** all text on solid or ≥ 90 % opaque panel surfaces; WCAG AA contrast (≥ 4.5:1 body, ≥ 3:1 large text/icons) in both dark and light themes — add a test that computes contrast for the token pairs used.
- **Motion:** any animation (twinkle, pulse) is subtle, ≤ 1 element type, and fully disabled under `prefers-reduced-motion: reduce`.
- Status meaning never by colour alone (existing rule).

## Build
1. **Deep-space background:** static procedural starfield (seeded, deterministic SVG or CSS radial gradients; ~150 tiny low-contrast stars + faint nebula gradient) behind the app shell only. Light theme: plain light background (no stars).
2. **Mars icon (top right of header):** original simple SVG planet (rust tones, a couple of subtle surface features), `aria-hidden`, with the trajectory bar ending at it.
3. **Earth→Mars trajectory bar (header):** small Earth glyph at left, Mars at right, a curved or straight dotted arc, spacecraft marker at `day/durationDays`; label `theme.trajectory_label`; `theme.trajectory_note` in the How-to-read text. Marker position updates with replay.
4. **Comms-delay link:** ship↔Earth mini-link with `theme.comms_link`; minutes = linear interpolation from missionProfile delay min→max over the mission days, rounded, labelled illustrative. During a blackout window: dashed/greyed link + `theme.comms_blackout` + a "link down" icon.
5. **Solar-storm alert mode:** whenever the selected crew/day has a radiation indicator with an active warning (or any radiation `act`), show a full-width header band with warning icon + `theme.storm_banner_title` + `storm_banner_body`; `storm_banner_note` as small text. Band uses the act status token plus text and icon. It must not cover or hide the attention cards; urgent card ordering unchanged.
6. **Crew badges + ship clock:** original geometric badges (initials C1–C4, distinct shapes not just colours) in the crew selector and crew grid; `theme.crew_badge_note` in crew grid How-to-read. Ship clock in header: `theme.ship_clock` when an intraday event time is selected (e.g. replay at a radiation sample), else `theme.ship_clock_daily`.
7. Keep everything working at 390 px: trajectory bar shrinks to a single line with marker; badges wrap.

## Tests
Contrast test (token pairs); reduced-motion disables animation classes; storm band appears on a fixture day with an active warning and not on a quiet day; comms link shows blackout copy inside a blackout window; trajectory marker position = day/duration; no `<img>`/external URL in theme components; all theme strings come from ui-copy keys.

## Acceptance (Claude re-runs)
```bash
export PATH="$HOME/.local/node/bin:$PATH"; cd dashboard
npx tsx scripts/make-demo.ts && npm test -- --run && npm run build
```
Report: list of views to check (C2 day 42; any crew day 72; day 155 blackout; crew grid; phone width).

## Out of scope
New data, model changes, LLM assistant. No commit.
