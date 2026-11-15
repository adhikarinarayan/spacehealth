# TASK-003 — Dashboard v0 on mock data (Gate G1, part 2) — runs IN PARALLEL with TASK-002

**From:** Claude · **To:** Codex (second session) · **Created:** Sat 2026-11-14 18:35 CST
**Report to:** `handoffs/reports/TASK-003.md` (+ screenshots in `handoffs/reports/TASK-003/`)

## ⚠️ File fence (another Codex session is doing TASK-002 right now)
You may create/edit ONLY:
- `dashboard/src/**` **except** `dashboard/src/contracts/**` (read-only: import types/schemas from it)
- `dashboard/tests/ui/**`, `dashboard/scripts/**`, `dashboard/public/demo/**`
- `dashboard/package.json` + `package-lock.json` (only to add the dev deps listed below)
- `REQUIREMENTS.md` — append a "Dashboard (TASK-003)" section at the very end only
Do NOT touch `contracts/`, `model/`, `research/`, `dashboard/src/contracts/`, `dashboard/public/data/`, `dashboard/tests/contracts.test.ts`, plan/decision files. If you need a contract change, STOP and write it under "Open questions".

## Read first
`Discussion.md` §1.3, §1.5, §2.4, §6; `contracts/CONTRACT.md`; `research/cards.yaml`; `research/rules.yaml` (card_cap); `plan.md` §6.3; `DECISIONS.md` D2, D10.

## Data
- Build a **demo mock** generator `dashboard/scripts/make-demo.ts` → `dashboard/public/demo/{mission,indicators,validation,cards}.json`: 4 crew × days −14..180, statuses placed to exercise every screen (S2-like physiological watch→act on C2 days 40–46; radiation act on day 72 for all; sleep watch C3 days 96–101; unknown days for C4 120–124; a red-flag symptom act). Every file must pass the Zod schemas in `dashboard/src/contracts`. Card text must be copied from `research/cards.yaml` (convert to cards.json shape), not invented.
- Mark the mock clearly: a banner "MOCK DATA for UI development — not model output". It is replaced by real model output at integration (D2).
- App loads data from one place (`src/data/load.ts`) with a switch `?data=demo|data` (default demo for now). Validate with Zod on load; on failure show an error screen, never partial data.

## Screens (v0 — function over polish)
1. **Today** (crew selector + mission-day selector):
   - Header: crew, mission day, profile "Mars transit (simulated)", comms note "ground replies may be delayed".
   - Three module tiles: `sleep_alertness`, `physiological_change`, `radiation`. Each: status word + icon + colour (never colour alone), one-line `reason`, `dataQuality` label.
   - "Needs attention": action cards for watch/act. **Max 3 routine cards; radiation act and red-flag symptom act are never capped and always on top** (rules.yaml card_cap). `unknown` is shown as "No reliable data" — never green.
2. **Detail + action card** (click a tile):
   - Chart (Recharts): last 21 days of each evidence signal, preflight median as a line + band (median ± scale), event markers. Missing values = gaps, never zero.
   - Evidence table: signal, value, unit, baseline, z, direction.
   - Card rendered verbatim from cards.json: heading, why, uncertainty, do_now checklist, recheck, onboard_escalation, ground_escalation, source/assumption IDs as chips.
   - Buttons: `Done`, `Recheck later`, `Contact onboard CMO`, `Queue message to ground`. They only record a local action log (in-memory + localStorage, wrapped in try/catch). Ground message shows "queued — reply may take up to ~40 min round trip or longer during blackout". **No button may claim a message was delivered.** A note under the log: "Recording an action does not mean it caused recovery."
3. **Replay + Validation**:
   - Play/pause, speed (1/5/20 days per second), scrub slider over days 1–180, crew switcher; Today + Detail follow the replay day.
   - Validation panel from validation.json: per scenario/crew — passed, onset, symptom, first watch/act, delays, false alerts per 100 crew-days (with denominator), unknown days. Header text: "Synthetic-scenario results — not clinical validation."
   - In Replay only, show `truth` markers (onset/symptom) — never on Today.

## Fixed copy (use exactly)
- Footer on every screen: "SpaceHealth is a research prototype. All data are simulated. It is not a medical device and does not diagnose."
- Status words: Nominal / Watch / Act / No reliable data.

## Design
Dark-first, calm; tokens file `src/styles/tokens.css` (colours, spacing, type scale) built first; one accent colour; status colours only for status; monospace for numbers; touch targets ≥ 44 px; works at 390 px width without horizontal scroll; keyboard-navigable; respects `prefers-color-scheme` (light theme can be basic).

## Allowed new dev dependencies
`@testing-library/react`, `@testing-library/user-event`, `jsdom` (+ `tsx` if needed to run the script). Nothing else without asking. Record versions in REQUIREMENTS.md.

## Tests (Vitest + Testing Library, in `dashboard/tests/ui/`)
- unknown never renders as Nominal; missing chart values are gaps (no 0 points).
- Card cap: with 5 routine + 1 radiation act, 3 routine + the radiation card show; radiation card first.
- Card text equals cards.json text (no hard-coded medical copy in components: grep test for "infection", "diagnos").
- Ground-message button shows "queued", never "sent/delivered".
- Replay to day 72 shows radiation Act.
- Demo files validate with Zod.

## Acceptance (Claude re-runs)
```bash
export PATH="$HOME/.local/node/bin:$PATH"; cd dashboard
npm ci && npx tsx scripts/make-demo.ts && npm test -- --run && npm run build
```
Plus screenshots (desktop 1280 px and phone 390 px) of: Today (C2 day 42), Detail+card (C2 day 42), Today (day 72), Replay+Validation, an unknown tile (C4 day 122). Use any headless method available; if none works, say so and list how Narayan can view (`npm run dev`).

## Out of scope
Real model data, offline/PWA caching (later task), check-in/PVT, mood, CMO crew grid, any edit outside the fence. No commit.
