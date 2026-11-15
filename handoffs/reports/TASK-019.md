# TASK-019 — Complete

## Changes

- Renamed the switch to **Mission**, with **Showcase mission — shows every feature** and **Blind test mission — fixed before results**. Values remain `illustrative` / `preselected`; URL and switching logic are unchanged. Widened the selector's maximum width for the longer labels.
- Replaced the visible technical tag with **Simulated data · settings locked before testing · mission no. <seed>**. The tag retains the exact modelId only in its title tooltip.
- Added a reusable SelfCare component immediately after each full ActionCard article, including urgent cards. It reads heading, disclaimer, steps and sources directly from generated ui-copy.json. The neutral panel opens by default; collapsing hides only the steps and sources. Heading and disclaimer remain visible.
- Missing/unknown card IDs render nothing. Native buttons expose aria-expanded/aria-controls. Action-card content, checklist and action buttons stay before the general guidance; attention-card ordering/capping logic is untouched.
- Regenerated the complete ui-copy.json using the existing make-demo.ts generator. It already copies the whole YAML, so no generator code change was necessary. The new seven-card self_care block, rewritten mission notes and blackout text match the read-only research/ui_copy.yaml exactly.

## Verification

- Required `npx tsx scripts/make-demo.ts`: passed (776 readings, 2,160 mock indicators). Used the permitted local IPC access needed by tsx.
- `npm test -- --run`: **88 passed** across seven test files.
- `npm run build`: passed, including all 34 precached files and existing built-path/service-worker checks. Final cache version: `spacehealth-bfc3de9fc25ab61c2c55`.
- Tests cover all seven IDs: physiological-change, physiological-change-act, symptom-escalation, sleep-short, sleep-debt, radiation-spe-procedure and radiation-budget. They check exact source steps/sources, default expansion, collapse/reopen behavior, persistent disclaimer, placement after the card, urgent action ordering, prohibited-word restrictions and absence for unknown IDs.
- Mission tests check new labels, unchanged option values/URL behavior, the plain tag and modelId tooltip. Existing case-switching and action-history tests remain green.
- Generated JSON compared equal to the complete YAML. Before/after SHA256 checks for **59 protected files** match, including research/ui_copy.yaml, model source, contract JSON files and the existing Pages build test.

Edits are confined to dashboard/src (excluding contracts), dashboard/tests/ui and this report. No new packages, model/research/contract edits, commit, push or deployment. Other modified research/docs files were already present at task start and were left untouched. Browser visual verification was not performed.
