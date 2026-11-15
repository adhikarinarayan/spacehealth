# TASK-020 — Complete

## Adapted from pr-1

Read the source using `git show pr-1:<path>`. No merge or cherry-pick.

- SolarHero SVG geometry: real-period Mercury/Venus/Earth/Mars motion, compressed orbital radii, deterministic belt/ticks, Earth-to-Mars transfer arc, craft marker, comms link and mission-day scrubber. The existing mission profile/day/communication calculations drive the display. The caption states that this is illustrative, not navigation.
- Dark glass styling, segmented navigation, Instrument Serif typography and stronger labelled Watch/Act treatments. Glass rules are explicitly scoped to dark display; shared orrery layout uses existing theme tokens so light display stays readable. Control borders retain the AA control token and glass surfaces use higher opacity for readability.
- Instrument Serif normal/italic WOFF2 files and SIL OFL licence were extracted binary-safely using `git cat-file blob`. All three extracted files match the branch blobs exactly.
- Dark palette adapted from the branch; the existing AA token checks pass. Light tokens are retained. README changes are limited to the requested contributor/font credit.

All orrery narrative, headings, stat labels, delay unit, blackout text, scrub label, caption and accessible diagram description come from the supplied theme.orrery copy. Decorative planet labels without source-copy keys were omitted. The delay remains explicitly labelled illustrative. Regenerated ui-copy.json from the read-only YAML.

## Built locally

- Kept the existing deterministic SVG SpaceBackdrop. No WebGL background or external effects library.
- Pointer-driven tile spotlight: a small original React pointer handler sets CSS position variables; the effect itself is a radial gradient. Decorative layers have pointer-events:none and cannot capture tile clicks. Reduced-motion preference prevents pointer updates and fixes the gradient at its centre.
- Headline shine: original, subtle CSS gradient text. Animation is disabled under reduced motion.

No restricted vendor files were copied, no type-check suppression was introduced, and no npm packages were added. Source scan for the two forbidden patterns returns no matches.

## Bug fixes and click tests

1. Light display defaults to dark. It reads and writes the same `spacehealth-display` key and the same `light`/`dark` strings. Tests click to light, remount, click back to dark, remount again, and verify both saved values/aria-pressed states. Blocked storage still works. Dark-only CSS scoping is checked independently.
2. Header controls remain above decorative layers: explicit masthead/control stacking, a local isolated orrery stacking context, and pointer-events:none on its decorative figure and background layers. Tests click/select both mission choices with the orrery mounted, starting in each display, then toggle display and switch back. Data, default day, disclosure and URL values update correctly.

Additional tests cover authored copy, illustrative delay, blackout state, scrubber-to-application day binding, orbital periods/arrival geometry, pointer position updates, reduced-motion behavior and actual tile-button clicks.

TASK-019 mission names/tag, self-care content/components, data loading and all contracts/model/research code remain unchanged. README credits-only change and protected file hashes were verified. The only Pages test edit is font count 5 → 7.

## Validation

- Required copy/demo generation: passed (776 readings, 2,160 mock indicators).
- Dashboard: **97 tests passed**, eight files (all prior 88 plus nine new tests).
- Production build: passed, including the font/base-path/worker checks and complete **37-file** offline manifest. Final cache version `spacehealth-b379f564d0598d960067`.
- Model: **168 tests passed**, exit 0.
- Forbidden-pattern source scan: no matches.
- No browser visual or physical hit-testing session was performed; interaction checks use the DOM test environment plus explicit stacking/pointer-event style assertions.

Edits stay within the task fence plus this report. No commit, push, merge, cherry-pick or deployment. The pre-existing changes to DECISIONS.md and research/ui_copy.yaml were left untouched.
