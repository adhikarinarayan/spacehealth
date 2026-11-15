# TASK-015 — Complete

The dashboard defaults to the disclosed illustrative holdout case (Gaussian, scale 0.8, seed 1002). The header Mission case selector switches to the pre-selected seed 1000 and back, updating the loaded mission, indicators, validation rows and persistent source-owned disclosure together. The aerospace redesign and EVA helmet are retained. No commits.

## Model export

Added `--illustrative --seed 1002 --noise gaussian --effect-scale 0.8 --out out/illustrative/`. This uses the frozen holdout variant builder and verifies the existing freeze before generating outputs. It writes the four contract files and a SHA256 manifest containing `case: illustrative`, `selectedAfterHoldout: true`, the full D20 selection rule, seed and variant. Only the approved seed/variant is allowed for illustrative exports; out-of-holdout seeds, alternate variants, scenario subsets, combined release/illustrative modes and overwriting the canonical release are refused. The illustrative output directory also requires explicit illustrative mode.

Validation rows are read from the existing recorded case, not a new holdout evaluation. Regression tests independently compare generated first watch/act days with that case's rows, using the same scenario windows. Scientific code, configuration and holdout artifacts remain untouched.

| Scenario / crew | First watch | First act | Recorded result |
| --- | --- | --- | --- |
| S1 / C1–C4 | none | none | Pass (isolated quiet control rows) |
| S2 / C2 | 41 | none | Pass |
| S3 / C1–C4 | none | 72 | Pass |
| S4 / C3 | 96 | 99 | Pass |
| N1 / C1 | 12 | none | Pass |
| N2 / C4 | none | none | Pass (missing-data semantics) |

The N1 row's first watch is over the complete C1 physiological series, as recorded by the original holdout; day 12 is not a claim about the later injected spike. Existing aggregate false-alert costs remain visible. S3 flags at the exact first onset sample, day 72 00:30.

## Dashboard and offline

- `?case=illustrative` is the default; `?case=preselected` loads seed 1000. `?data=demo` retains the explicitly labelled UI mock.
- Default C2 mission day is derived from the loaded indicators' first physiological watch: illustrative 41, pre-selected 43. Explicit URL day/time parameters still work.
- Both datasets use the aggregate holdout copy and their own recorded validation rows. Labels use `illustrative_case_note` / `preselected_case_note`, copied from the current read-only research source into ui-copy.json.
- Case switching stops replay and clears stale detail/time context. A load failure retains the displayed case with an error. Action histories are stored separately per real case; the legacy mock history remains available.
- Sync verifies both complete datasets before copying either and preserves manifest bytes. Named dataset locations are `public/data/illustrative/` and `public/data/preselected/`. Existing root seed-1000 files remain as compatibility copies for prior URLs and shared contract tests; the app loads only the named directories.
- Production precache contains both named datasets and all other built files: **34 files**, checked by the build. Browser offline verification remains a manual check under docs/OFFLINE_TEST.md.

## Verification

- Focused model tests: **8 passed**.
- Full model suite: **159 passed**.
- Exact illustrative CLI command: passed.
- `npm run sync:release`: passed for both sources.
- Dashboard tests: **77 passed** (default/source loading, data-derived day, bidirectional case switching and validation, failure retention, action isolation, checksum rejection and offline coverage included).
- `npm run build`: passed; final cache version `spacehealth-b71b32503245d4a7039c`.
- Both public datasets' four file hashes and manifest bytes match their model sources.
- **260 protected files unchanged** against a before-task SHA256 snapshot: original seed-1000 release manifest, frozen config and all original holdout files.
- Seed-1000 release manifest SHA256 remains `b3a49dd7d0787c372b3b0bf9ba9e16248c9f2ea2c15b3c2744a0213f8aade1b6`.

Edits stay within TASK-015's fence plus this requested report. TASK-016 files were not touched.
