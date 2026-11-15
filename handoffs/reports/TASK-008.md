# TASK-008 — dashboard copy/time fixes complete

Status: automated acceptance PASS. No commit. This session owned TASK-008 only; TASK-007/TASK-009 were left to the parallel model session per Narayan's latest instruction.

## Built / changed files

- `dashboard/src/data/actions.ts`: formats a recorded ISO instant in the device's local 24-hour `HH:MM` time plus its recorded mission day, e.g. `04:02 (day 42)`.
- `dashboard/src/App.tsx`: substitutes that value into `uiText('actions.recorded', { time: ... })`. Renders the action label in a separate strong element **before** the source-owned sentence. Ground actions also retain the existing queued message; no delivered/sent claim is added. The notice retains the recorded day even if the selection changes afterward.
- `dashboard/tests/ui/dashboard.test.tsx`: source-key-based action-copy assertions, explicit persisted-time/day regression, separate action-label assertion and zero-padded local-time formatting check. Storage-unavailable behavior remains tested without dependence on a wall-clock minute boundary.
- `dashboard/tests/ui/informative.test.tsx`: replaces former missing-key expectations with actual source-key lookups for blackout/help copy; verifies all 11 supplied keys resolve; retains an unknown-key fallback check using `panels.fake_panel.fake_key`.

Ran the demo generator to refresh `ui-copy.json` and the mock bundle. Those generated files already matched the new source content, so they produced no additional diff at completion.

All requested copy consumers already call `uiText` for blackout_active/inactive, attention_cards.empty, detail.chart_legend/no_action, timeline.empty, validation.mock_note, states.load_error and states.indicator_unavailable. Their newly supplied strings now render through the regenerated source artifact; no component prose was invented.

## Acceptance and observed output

```sh
export PATH="$HOME/.local/node/bin:$PATH"
cd dashboard
npx tsx scripts/make-demo.ts && npm test -- --run && npm run build
```

```text
Validated UI mock: 776 readings, 2160 indicators; card text from research/cards.yaml.
Test Files  3 passed (3)
Tests  49 passed (49)
> tsc --noEmit && vite build
✓ 504 modules transformed.
dist/index.html                   0.44 kB │ gzip:   0.30 kB
dist/assets/index-kAL536mG.css   11.77 kB │ gzip:   3.04 kB
dist/assets/index-BT13IjE8.js   341.51 kB │ gzip: 104.39 kB
dist/assets/Detail-B8blHLzD.js  375.47 kB │ gzip: 107.82 kB
✓ built in 786ms
```

After removing a possible minute-boundary race from a test and adding all-key resolution assertions, tests were rerun: **49 passed in 2.91 s**. Production source remained unchanged; the build also passed on the intervening rerun (993 ms). No TypeScript errors.

The existing generator required authorized execution outside the sandbox for tsx/Python execution; it succeeded. Some sandboxed npm invocations printed stream-fd warnings but exited successfully. No dependency or permission workaround was added.

## Review

From `dashboard/`, run `npm run dev` with Node on PATH, then open:

- `/?data=demo&crew=C2&day=42&detail=1`: click Done/Recheck/CMO/Ground; verify the separate label and substituted local time/day.
- `/?data=demo&crew=C2&day=155`: source-owned active blackout text.
- `/?data=demo&crew=C2&day=42`: inactive blackout text and updated panel help.

No new packages, model/research/contracts/requirements edits, real-data integration, deployment or commit. No browser layout/screenshot verification claimed for this small fix. No unresolved copy keys among the 11 supplied entries; fake unknown-key behavior is preserved.
