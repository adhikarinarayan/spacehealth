# TASK-010 — deep-space dashboard theme complete

Status: automated acceptance PASS. Executed after TASK-011 was finished and reported, per Narayan's revised order. No commit.

## Built

- Original inline SVG/CSS artwork only: a seeded static 150-star field, faint nebula gradients, Earth glyph, rust-toned Mars with subtle surface features, spacecraft and four distinct geometric C1–C4 badges. No logos, patches, downloaded imagery/fonts or runtime external asset URLs.
- Earth→Mars trajectory in the top-right header, with marker at day/durationDays. Replay/mission-day changes update its position. The source-owned illustrative-navigation note appears in Mission status's How-to-read text.
- Comms mini-link interpolates the configured one-way minimum→maximum over days 1→duration, rounded and labelled illustrative via theme.comms_link. Inside a mock blackout, it is dashed/greyed with a link-down icon and theme.comms_blackout copy.
- Full-width storm band for the selected crew/day when radiation is act or its evidence contains an active warning. Icon + title/body/note use source theme keys and the act token. It is in normal document flow and never overlays or suppresses attention cards; existing uncapped urgent ordering is unchanged.
- Crew badges in the selector and Crew grid; native select options remain normal accessible text. The crew-badge note is in the grid's How-to-read help.
- Ship clock uses the daily source string unless an existing intraday radiation event is selected in Replay (or the time query parameter matches a sample). The sample selector changes the header clock; changing crew/day drops stale intraday context. No new data or clock-driven detection rule.
- Solid token surfaces behind every text region, plus dark-first/light theme support. Light mode has a plain background and hides the star field. Narrow-screen rules stack the header, preserve a one-line trajectory, wrap badges/controls and keep panels within their container.
- Only one subtle animation type: 8-second spacecraft-marker opacity beacon (.82–1). It is omitted when reduced motion is requested (also omitted conservatively without matchMedia), and CSS independently disables animation/transition under prefers-reduced-motion: reduce. Stars and planets are static.

## Files / fence

Added dashboard/src/theme/{art.tsx,context.ts,MissionTheme.tsx,theme.css}; patched App, main.tsx, PanelIntro, MissionHeader, CrewGrid and token borders; added tests/ui/theme.test.tsx. Ran the existing demo generator to refresh source copy/demo artifacts. No src/contracts edits, model/research/contract/package/requirements changes, real-data integration, deployment or commit in TASK-010. No new npm packages.

## Acceptance

```sh
export PATH="$HOME/.local/node/bin:$PATH"
cd dashboard
npx tsx scripts/make-demo.ts && npm test -- --run && npm run build
```

```text
Validated UI mock: 776 readings, 2160 indicators; card text from research/cards.yaml.
Test Files  4 passed (4)
Tests  61 passed (61)
> tsc --noEmit && vite build
✓ 508 modules transformed.
dist/index.html                   0.44 kB │ gzip:   0.29 kB
dist/assets/index-wU2ooIxo.css   15.05 kB │ gzip:   3.82 kB
dist/assets/index-AteGalQv.js   349.78 kB │ gzip: 107.20 kB
dist/assets/Detail-D7RrlCHp.js  375.47 kB │ gzip: 107.81 kB
✓ built in 477ms
```

No TypeScript errors. All prior 49 dashboard checks still pass; 12 theme checks cover deterministic stars, reduced motion, day/duration position, comms endpoints/blackout, storm act/warning and quiet states, unchanged urgent card visibility, badge shapes, event clock/day reset, all theme copy keys/help placement and absence of image/external-URL theme resources.

## Contrast evidence

Tests compute WCAG relative luminance/contrast from the actual dark/light CSS tokens, including 3-digit hex expansion. The reference black/white ratio is checked as 21:1.

| Tested pairs | Dark minimum | Light minimum | Required |
| --- | --- | --- | --- |
| Text/muted/accent/status foregrounds on bg/surface/surface-2 | 7.18:1 | 5.21:1 | 4.5:1 |
| Control/icon boundary on those surfaces | 3.37:1 | 3.70:1 | 3:1 |

Primary button foreground/background is also checked at >=4.5:1. Borders were adjusted to meet the boundary test. Low-contrast decorative stars and planet features convey no status; their adjacent data remains on opaque surfaces. Status words/icons remain present independently of colour.

## Views to check

From dashboard/ run `npm run dev` with Node on PATH and open Vite's printed Local URL (normally http://127.0.0.1:5173):

- C2 day42: `/?data=demo&crew=C2&day=42`
- Storm mode, any crew: `/?data=demo&crew=C2&day=72`
- Blackout: `/?data=demo&crew=C2&day=155`
- Crew grid: `/?data=demo&view=crew&day=122`
- Replay + selected ship clock: `/?data=demo&view=replay&crew=C2&day=72&time=6`

Check these at desktop and 390px width, in dark/light mode and with reduced motion. The current dataset is still clearly labelled UI mock, not the new frozen model export; its authored day72 sample is 06:00. TASK-009's verified 00:30/23:45/16:25 timing is in the model release and is not silently substituted into this UI task. The supplied storm note describes the project timing source; it does not turn mock rows into model results.

## Limits

No browser screenshot or rendered 390px no-overflow claim: Firefox Snap capture was unavailable earlier. DOM/interaction tests and explicit responsive CSS passed, but visual owner review remains needed. No offline caching or real-model dashboard integration was added. No missing theme keys; all new theme sentences use research/ui_copy.yaml via the existing generator and uiText placeholder substitution.
