# TASK-003 — dashboard v0 implemented; automated checks PASS, browser screenshots unavailable

## Built

- Clearly separated UI mock in dashboard/public/demo/ (776 readings; 2160 indicators; all four files validated by shared Zod schemas). Authored statuses and validation rows are explicitly mock UI fixtures, never TASK-002 detector results.
- Generator dashboard/scripts/make-demo.ts reads research/cards.yaml using the existing Python/PyYAML environment, expands source placeholders with illustrative UI context, and writes cards.json. Components render those generated card strings verbatim; they contain no authored medical instructions. Updated sleep-debt act card is used for C3 days 99–101; sleep-short watch is used days 96–98.
- Dark-first token system, basic light-theme support, responsive CSS, keyboard focus outlines, labelled controls and 44-pixel button targets.
- Today view: crew/day selectors; three module tiles; status word/icon/colour; data-quality labels; attention cards. Missing indicators use No reliable data, never a nominal fallback.
- Urgent radiation act and symptom-escalation cards bypass the three-routine-card limit, with radiation first.
- Lazy-loaded Detail view: Recharts trends for evidence signals, actual fixture preflight median and robust MAD band, null gaps, evidence table and source/assumption chips. Scenario truth markers appear only in Replay.
- Source action cards: why, uncertainty, steps/checklist, recheck, onboard and ground escalation. Done/Recheck/CMO/Ground buttons create local records only. Ground records say queued, never sent/delivered. Storage failures retain in-memory functionality. Records survive remount when localStorage is available.
- Replay: play/pause, 1/5/20 days per second, scrubber, shared crew/day state. Validation shows synthetic labels, event days, watch/act days, delays, false-alert rates with counts/denominators and unknown days.
- Single loader src/data/load.ts: ?data=demo|data, validates all envelopes before rendering, rejects unlinked crew/cards and mismatched model/config reports; invalid input renders an error screen without partial health statuses.
- Required footer and mock banner; no offline caching or model integration claims.

## Files changed

Within TASK-003 fence: dashboard/src/App.tsx, main.tsx, style.css, styles/tokens.css, copy.ts, data/{load,presentation}.ts, components/{Status,ActionCard,Detail,Validation}.tsx; dashboard/scripts/make-demo.ts; dashboard/tests/ui/dashboard.test.tsx; dashboard/public/demo/{mission,indicators,validation,cards}.json; dashboard/package.json and package-lock.json (approved dev dependencies only); appended Dashboard (TASK-003) to REQUIREMENTS.md.

Did not edit dashboard/src/contracts/, public/data/, contracts/, model/, research/, planning/decision files or the existing contract test. No commit or deployment.

## Acceptance commands and observed output

Clean sequence run from dashboard/ (cache redirected to writable /tmp):

```sh
export PATH="$HOME/.local/node/bin:$PATH"
npm ci --cache /tmp/spacehealth-npm-cache
npx tsx scripts/make-demo.ts
npm test -- --run
npm run build
```

```text
added 132 packages, and audited 133 packages in 4s
found 0 vulnerabilities
Validated UI mock: 776 readings, 2160 indicators; card text from research/cards.yaml.
Test Files  2 passed (2)
Tests  33 passed (33)
```

After adding the mixed-model bundle rejection check, final tests/build were rerun:

```text
Test Files  2 passed (2)
Tests  34 passed (34)
> tsc --noEmit && vite build
✓ 494 modules transformed.
dist/index.html                    0.44 kB │ gzip:   0.29 kB
dist/assets/index-huuouERp.css     7.71 kB │ gzip:   2.24 kB
dist/assets/index--wm7EptU.js    328.10 kB │ gzip: 100.17 kB
dist/assets/Detail-D2IclPTt.js   375.52 kB │ gzip: 107.95 kB
✓ built in 630ms
```

No TypeScript errors. The 34 checks are the existing 20 shared-contract checks plus 14 UI/data/interaction checks. Recharts is mocked in jsdom, which has no layout engine; chart data gaps are tested as data, not inferred from a DOM screenshot. Actual chart layout and narrow-screen behavior remain browser-review items.

The sandbox prevented local sockets for Vite/tsx; authorized runs outside it succeeded. npm emitted a notice that esbuild's postinstall was not auto-approved; tsx generation and builds nevertheless completed successfully. No approval bypass or symlink workaround was introduced.

## New dependencies

Only the four approved dev packages:

| Package | Installed version | Purpose |
| --- | --- | --- |
| @testing-library/react | 16.3.3 | UI render/assertions |
| @testing-library/user-event | 14.6.10 | Keyboard/pointer interaction tests |
| jsdom | 31.0.1 | Test DOM environment |
| tsx | 4.23.15 | TypeScript demo generator |

No new runtime or Python dependencies. The generator requires the already-installed model/.venv Python solely to read YAML, and does not run detectors.

## Screenshot attempts / limitation

Installed /usr/bin/firefox is a Snap launcher. Sandboxed headless capture failed because Snap needed writable runtime/profile directories outside the workspace. Authorized headless capture with a /tmp profile failed because Snap could not see the profile. Created a separate Snap-accessible spacehealth-qa profile, then retried capture into the Snap common directory. Firefox returned without producing the requested PNG. No screenshots are claimed or fabricated.

No other installed Chromium/headless automation tool was found, and no extra browser/automation dependency was installed beyond the allowed packages. The requested ten desktop/phone screenshots are therefore outstanding; screenshot and 390-pixel no-horizontal-overflow verification require a working browser. This is a verification limit, not a passing browser-QA claim.

## How Narayan/Claude can review

From dashboard/:

```sh
export PATH="$HOME/.local/node/bin:$PATH"
npm run dev
```

Open each at desktop width 1280 and mobile width 390:

- Today C2/day42: http://127.0.0.1:5173/?data=demo&crew=C2&day=42
- Detail + action: http://127.0.0.1:5173/?data=demo&crew=C2&day=42&detail=1
- Radiation day72: http://127.0.0.1:5173/?data=demo&crew=C2&day=72
- Replay + validation: http://127.0.0.1:5173/?data=demo&crew=C2&day=72&view=replay
- Unknown C4/day122: http://127.0.0.1:5173/?data=demo&crew=C4&day=122
- Updated sleep debt: http://127.0.0.1:5173/?data=demo&crew=C3&day=100

The temporary server used during this task is stopped at handoff. Port may differ if 5173 is occupied; use Vite's printed Local URL.

## Interpretation / open items

- Cards are source templates instantiated with fixed illustrative mock context, not recomputed clinical advice. Some amounts/timing text is representative across the authored mock sequence; final integration must use actual contextual model exports. No mock pass result should be used as a detector performance claim.
- Chart bands are calculated for display from fixture preflight median/MAD; no model detection rule is ported into the frontend. Scale-floor/quality metadata are not supplied by the current indicator contract, so the chart does not claim to reconstruct the detector's exact decision boundary.
- Persisted local actions record clicks only. CMO contact is not actually placed, and queued ground notes have no transport. Completing a checklist/action is not a recovery/outcome claim.
- TASK-002's physiological S2 miss is unchanged. TASK-003 intentionally authored watch/act transitions for UI exercises and labels them clearly.
- Ready for Claude's technical/wording review and Narayan's first UI feedback; no gate approval or browser sign-off presumed.

Cards source SHA256 at report time: `1139cc156ea17d100aa3462ffd52a39b60a08cbef6b3b2927c2fdaf7d2543e9d`.
