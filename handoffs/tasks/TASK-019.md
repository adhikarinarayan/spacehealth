# TASK-019 — Plain-language mission names + self-care box (D24, D25, D26)

**From:** Claude · **To:** Codex · **Report to:** `handoffs/reports/TASK-019.md`

## File fence
`dashboard/src/**` (not `src/contracts/**`), `dashboard/scripts/**`, `dashboard/tests/ui/**`. Read-only: `research/ui_copy.yaml` (already updated by Claude), everything in `model/`, `contracts/`. No new packages. No commit. No AI attribution lines anywhere.

## 1. Mission switch names (D25)
In `dashboard/src/App.tsx`: label "Mission case" → "Mission"; option text "Illustrative (seed 1002)" → "Showcase mission — shows every feature"; "Pre-selected (seed 1000)" → "Blind test mission — fixed before results". Keep URL values `?case=illustrative` / `?case=preselected` and all logic unchanged.

## 2. Plain tag (D25)
The tag after the case note currently renders "<modelId> · seed <n> · simulated". Replace with "Simulated data · settings locked before testing · mission no. <seed>". Keep the exact modelId only as a `title` tooltip on that tag.

## 3. Self-care box (D24)
Under every rendered action card, show a visually separate, collapsible box (open by default) from `ui_copy.yaml → self_care`:
- heading = `self_care.heading`; then `self_care.disclaimer` (always visible, also when collapsed);
- the bullet list `self_care.cards[<card id>].steps`, then `sources` in small text.
- If a card id has no entry, render nothing (no empty box). Style it neutrally (not a status colour) so it is never confused with the card's own instructions.
- Must appear for urgent cards too, below the card, never above it, and never push the urgent card out of view order.

## 4. Copy regeneration
`npx tsx scripts/make-demo.ts` must carry the new `self_care` block and the rewritten notes / blackout text into `src/data/ui-copy.json`.

## Tests
- Switch shows the new option texts; URL values unchanged.
- Tag shows the plain text; modelId present only as title.
- Self-care box renders for each of the 7 card ids, always shows the disclaimer, never contains the words "dose", "mg", "tablet", "medication", "diagnos" (except inside the radiation card's "dosimeter"/"dose" wording — exclude radiation cards from the "dose" check), and renders after the card.
- No box for an unknown card id.

## Acceptance (Claude re-runs)
```bash
export PATH="$HOME/.local/node/bin:$PATH"; cd dashboard
npx tsx scripts/make-demo.ts && npm test -- --run && npm run build
```
