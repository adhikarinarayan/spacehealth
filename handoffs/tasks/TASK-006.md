# TASK-006 — Dashboard v1: informative views (Narayan feedback round 1)

**From:** Claude · **To:** Codex · **Created:** Sat 2026-11-14 ~19:45 CST
**Report to:** `handoffs/reports/TASK-006.md`
**May run in parallel with TASK-004 / TASK-005** (model only) — respect the fence.

## Narayan's feedback on v0
"It looks basic and is not very informative." He wants: (1) every panel to say what it is for, (2) a mission header with radiation budget, (3) a crew overview grid, (4) a mission timeline/log. An "ask a question" assistant is explicitly **later** (no LLM now — DECISIONS D12).

## File fence
Edit/create ONLY: `dashboard/src/**` except `dashboard/src/contracts/**`; `dashboard/scripts/**`; `dashboard/public/demo/**`; `dashboard/tests/ui/**`. Read-only: `research/ui_copy.yaml`, `research/cards.yaml`, contracts. No new npm packages (ask first).

## Copy
All explanatory text comes from **`research/ui_copy.yaml`**, rendered verbatim (convert at build/generation time the same way cards.yaml is converted; keep the conversion in `scripts/`). Do not write new explanatory or medical sentences in components; if a needed string is missing, list it under Open questions and show the key name.

## Features
1. **Panel explanations:** every panel (header, radiation budget, Today tiles, attention cards, detail, crew grid, timeline, replay, validation) shows its `title` and a one-line `what_for`; an accessible "How to read this" toggle (button + `aria-expanded`) reveals `how_to_read`. Collapsed by default except on first visit (remember in localStorage, try/catch).
2. **Mission header:** day X / durationDays from `missionProfile`; profile label; comms one-way delay shown as the profile range with "(illustrative)"; blackout status for the day ("none simulated" if the list is empty — never claim none occur).
3. **Radiation budget bar:** mission dose so far = sum of `daily_dose_msv` for days 1..day (skip null, show "partial" if any day has `dose_coverage < 1` or null); projection = so-far + remaining days × `gcr_background_msv_day`; career = + `prior_career_dose_msv` only if not null, else show `career_unknown` copy. Scale to 600 mSv with a marked limit line; numbers in monospace with units; `source_note` beneath. This is display arithmetic only — status still comes from indicators.
4. **Crew overview grid:** 4 crew × 3 modules for the selected day; each cell = status word + icon (never colour alone) + one-line reason truncated; keyboard-selectable; selecting opens that crew's Detail for that module. Add it as a top-level view next to Today and Replay.
5. **Mission timeline / log:** derived from indicators: for the selected crew (toggle: all crew), list status transitions (e.g. "Day 40 · C2 · Physiological change: Nominal → Watch"), radiation warnings, and recorded local actions (with "queued" for ground messages). Newest first, filter by module, jump-to-day on click. Show truth markers only when in Replay.
6. **Tiles:** add a 7-day sparkline of the tile's main signal (RHR for physiological, sleep hours, daily dose) with the baseline line, plus the existing reason. Missing days are gaps.
7. **Visual polish:** clear page layout with a left/top nav (Today · Crew · Log · Replay & Validation), consistent card spacing, larger status typography, visible section hierarchy. Keep dark-first tokens; ensure 390 px width works (stack vertically) and no horizontal scroll.

## Demo data
Extend `scripts/make-demo.ts` so the mock has: missionProfile with a blackout window (e.g. days 150–160, labelled mock), one crew with a known prior career dose (e.g. C1 = 120 mSv) and others null, and enough transitions to make the log meaningful. Keep the MOCK banner.

## Tests (add to `tests/ui/`)
- Every panel renders title + what_for from ui_copy (snapshot of keys, not prose).
- Budget: null prior → career-unknown copy, never "0"; partial coverage → "partial" label; projection arithmetic on a tiny fixture.
- Crew grid: unknown cell never renders Nominal; keyboard navigation opens Detail.
- Timeline: transitions computed correctly on a tiny fixture; ground actions say "queued".
- No component file contains the words "infection" or "diagnos" (except the shared footer string).

## Acceptance (Claude re-runs)
```bash
export PATH="$HOME/.local/node/bin:$PATH"; cd dashboard
npx tsx scripts/make-demo.ts && npm test -- --run && npm run build
```
Report: list of views/URLs to open, any missing copy keys, any open questions.

## Out of scope
LLM/assistant, check-in form, offline caching (later task), real model data integration. No commit.
