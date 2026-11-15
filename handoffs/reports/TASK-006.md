# TASK-006 — informative dashboard implemented; automated acceptance PASS

TASK-004 and TASK-005 were executed first at Narayan's direction; their separate reports are available. TASK-006 then resumed within its dashboard-only file fence.

## What changed

- Source-owned panel explanations for all nine panels: mission header, radiation budget, Today, attention cards, Detail, Crew overview, Mission log, Replay and Validation. Each renders title + what_for, plus an accessible How to read this button with aria-expanded/aria-controls. Help is expanded on first visit, otherwise collapsed unless explicitly remembered open; storage is wrapped in try/catch.
- scripts/make-demo.ts converts research/ui_copy.yaml to src/data/ui-copy.json alongside the existing card conversion. Explanations are rendered verbatim with data placeholder substitution. Missing copy is shown by key, as requested; no research file was edited.
- Mission header reads selected day/duration, profile label, illustrative one-way delay and blackout windows from missionProfile. Empty windows display none simulated rather than asserting none occur.
- Radiation budget performs display arithmetic only: sum observed days 1..selected day, skip null dose values, mark partial for missing days/null coverage/coverage<1, project the remaining mission background, and add career dose only when known. Unknown prior stays null and uses career_unknown copy. Bar includes received/projected portions, a marked 600 mSv limit, monospace values with units and source_note. Indicator status is not recomputed or changed.
- Crew view: four crew × three modules, status word/icon/colour, truncated reason with full title, ordinary keyboard-focusable buttons. Selection opens that crew/module's Detail and updates the crew selector.
- Log view: derived status transitions, warning onsets and recorded local actions; descending day/time order, selected/all crew and module filters, jump-to-day. Ground actions stay queued. Initial states are not invented transitions; unchanged days produce no transition row. Truth records are never consumed by the log.
- Seven-day tile sparklines for RHR, sleep hours and daily dose, with preflight baseline line and null gaps. No clinical rule is moved into the UI.
- Today/Crew/Log/Replay navigation, clearer panel hierarchy and larger status type. Narrow-screen CSS stacks crew cells and metric groups, wraps navigation and long key text; all grid tracks use minmax(0,1fr) where relevant.
- Demo adds the requested labelled mock blackout days 150–160 and C1 prior career dose 120 mSv; other priors remain null. Existing sleep-debt cards C3/day99–101 and authored mock transitions retained. No real model integration.

## Files / fence

Changed only dashboard/src/** (excluding src/contracts/**), dashboard/scripts/**, dashboard/public/demo/** and dashboard/tests/ui/** for TASK-006. Added PanelIntro, MissionHeader, RadiationBudget, CrewGrid, Timeline and Sparkline components; ui.ts / generated ui-copy.json / mission.ts data helpers; patched App, Detail, Validation and styles. Updated UI tests for Log placement and source-owned copy, preserving prior behavioral checks.

No package manifest/lock changes or new packages for TASK-006. No contracts, research, model, planning/decision files or REQUIREMENTS.md edits in this task. No commit, deployment, assistant/LLM, check-in or offline cache.

## Acceptance

```sh
export PATH="$HOME/.local/node/bin:$PATH"
cd dashboard
npx tsx scripts/make-demo.ts && npm test -- --run && npm run build
```

Final observed output:

```text
Validated UI mock: 776 readings, 2160 indicators; card text from research/cards.yaml.
Test Files  3 passed (3)
Tests  47 passed (47)
> tsc --noEmit && vite build
✓ 503 modules transformed.
dist/index.html                   0.44 kB │ gzip:   0.30 kB
dist/assets/index-kAL536mG.css   11.77 kB │ gzip:   3.04 kB
dist/assets/index-CqK1A3mi.js   339.70 kB │ gzip: 103.76 kB
dist/assets/Detail-nVwYNJFb.js  375.47 kB │ gzip: 107.81 kB
✓ built in 648ms
```

The 47 checks comprise existing contract/UI coverage and 13 new informative-view checks. New coverage includes panel-key coverage (keys, not prose snapshots), source titles/what_for, all actual view intros, first-visit/help persistence and blocked storage, unknown prior without zero imputation, partial-dose projection on a hand-computable fixture, blackout/profile labels, keyboard unknown-cell selection, transition computation and queued action wording, log filtering/jumps, sparkline gaps and no authored medical prose in components.

No TypeScript errors. Sandbox execution of the generator's Python child process failed with EPERM; the mandated npx tsx acceptance sequence succeeded with authorized execution outside the sandbox. No workaround or package addition used.

## Open questions: missing copy keys

The following requested/needed explanations are absent from research/ui_copy.yaml and are intentionally displayed as their key names. Claude should supply them; regeneration will pick them up without component prose edits.

- `panels.attention_cards.how_to_read`
- `panels.mission_header.blackout_active`
- `panels.mission_header.blackout_inactive`
- `panels.attention_cards.empty`
- `panels.detail.chart_legend`
- `panels.detail.no_action`
- `panels.timeline.empty`
- `panels.validation.mock_note`
- `states.load_error`
- `states.indicator_unavailable`
- `actions.recorded`

Existing task-specified fixed footer, mock banner, queued-message wording, status words, short field/control labels and data-derived transition labels remain. Model-authored reasons and generated action-card text are data, not new explanatory component prose.

## Views to review

From dashboard/, run `npm run dev` with Node on PATH, then use Vite's printed Local URL (normally http://127.0.0.1:5173):

- Today + mission/budget/sparklines: `/?data=demo&crew=C2&day=42`
- Detail: `/?data=demo&crew=C2&day=42&detail=1`
- Known career budget: `/?data=demo&crew=C1&day=72`
- Unknown crew cells: `/?data=demo&view=crew&day=122`
- Mission log: `/?data=demo&view=log&crew=C2&day=42`
- Replay + validation: `/?data=demo&view=replay&crew=C2&day=72`
- Mock blackout: `/?data=demo&crew=C2&day=155`

## Verification limits / interpretations

- No browser/390-pixel layout pass or screenshot is claimed. Installed Firefox Snap failed screenshot capture during TASK-003; that infrastructure was not repaired by this task. CSS stacks at 480/800px and DOM tests cover interaction/data, but jsdom does not prove rendered no-overflow. Owner browser review remains needed.
- Missing explanatory keys are visible by design per the brief, so wording polish is not complete until Claude supplies those strings. All provided nine titles and what_for entries are present.
- Budget totals from partial input are observed lower bounds, marked partial; projections inherit that uncertainty. Career values remain unknown when prior data is absent. This does not alter health/operational statuses.
- Log shows transitions available in the loaded mock mission, not injected truth. Transitions have day precision; warning samples have intraday time; local actions preserve recorded ordering. Jumping changes the selected crew/day and opens the relevant Detail.
- The demo generator remains an authored UI fixture. Mock validation is not evidence of model performance, and the mock banner remains on every demo view.

UI-copy source SHA256: `76939ab55b463675ffa5792ecc72f6a2699327c109978742dda367054529cdff`.
