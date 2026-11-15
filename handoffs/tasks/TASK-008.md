# TASK-008 — Dashboard fixes after copy update (small)

**From:** Claude · **To:** Codex · **Created:** Sat 2026-11-14 ~20:15 CST
**Report to:** `handoffs/reports/TASK-008.md` · **May run in parallel with TASK-007** (model only).

## Context
Claude added the 11 missing keys to `research/ui_copy.yaml` (see `handoffs/reviews/TASK-004-005-006.md`). After `npx tsx scripts/make-demo.ts`, 3 UI tests fail.

## File fence
`dashboard/src/**` (not `src/contracts/**`), `dashboard/scripts/**`, `dashboard/tests/ui/**`, `dashboard/public/demo/**`. Nothing else.

## Fix
1. `actions.recorded` currently renders "{time}" literally and appends ": Done". Substitute `{time}` with the recorded local time (HH:MM, mission day) and show the action label as a separate element before the sentence, e.g. "Done — Action recorded on this device at 14:02 (day 42). …".
2. Update the two tests that asserted missing-key display: assert instead that these strings come from ui-copy.json (by key lookup, not hard-coded prose), and keep a generic test that an unknown key still renders as its key name (use a fake key).
3. Use `blackout_active` / `blackout_inactive`, `attention_cards.empty`, `detail.chart_legend`, `detail.no_action`, `timeline.empty`, `validation.mock_note`, `states.load_error`, `states.indicator_unavailable` wherever the component previously showed the key.

## Acceptance (Claude re-runs)
```bash
export PATH="$HOME/.local/node/bin:$PATH"; cd dashboard
npx tsx scripts/make-demo.ts && npm test -- --run && npm run build
```
All pass. No commit.
