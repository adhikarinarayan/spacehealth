# TASK-002 — implementation ready for review; S2 acceptance FAIL

## Result

M1 is implemented from the supplied research YAML without increasing effect sizes or reducing thresholds. Seed 0 produces **no physiological watch or act during S2 days 40–48**, so the required flag by day 42 fails. `test_s2_flag_by_symptom_day` remains an ordinary failing assertion. No xfail/skip, alternate seed search, model comparison or threshold tuning was used. G1 is not marked passed.

## Built / files

- Contract v0.2.0: missionProfile in JSON Schema, Pydantic and Zod; all top-level version constants and fixtures upgraded, missing-profile negative fixture added, public minimal fixtures refreshed. All prior contract checks remain, with v0.2 envelopes.
- model/spacehealth_model/config.py: runtime YAML loading; constrained interpretation of prose rules; hashes and exact input snapshots.
- model/configs/stage0.yaml: explicit provisional numerical/profile conventions not fully specified by research prose.
- sim/generate.py: independent seeded numpy streams; four crew × 194 days; S1/S2/S3/S4/N1/N2, scenario toggles, synthetic provenance, separate truth records.
- sim/radiation.py: within-day trapezoids, partial coverage and observed cumulative mission dose from daily values; null intervals are not filled with zero.
- baseline/fixed.py: plausible/finite preflight measurements only; fixed median/MAD; configured minimum scale and valid-day count.
- modules/physiological.py: directional multi-signal persistence, strong-change rule, red-flag override, current evaluability/quality, evidence and card-template reasons. Detector takes no scenario truth.
- export/files.py: Pydantic + standard local JSON Schema validation of both files before writing; SHA256 mission-file linkage; sleep/radiation are explicitly unknown, unimplemented placeholders.
- run.py: CLI, stage-0 synthetic report, input/code hashes, package versions and labelled S2 PNG.
- tests/test_stage0.py plus contract regression: hand arithmetic, zero MAD, insufficient/missing/suspect inputs, persistence/direction, severe symptom override, no future leakage, deterministic/toggled missions, independent SciPy integration, no silent imputation, negative controls, forbidden wording, schema-valid exports and the failing S2 target.
- REQUIREMENTS.md: appended TASK-002 commands/limits; no new packages. Generated model/out/ ignored; reports retained.

No research/plan/decision/spec edits or git commit. No TASK-003 UI changes.

## Commands / evidence

From model/:

```text
.venv/bin/python -m pytest -q
1 failed, 46 passed
FAILED tests/test_stage0.py::test_s2_flag_by_symptom_day
```

Complete captured output: `model/reports/task002_pytest.txt`.

The acceptance command chains pytest && CLI; since pytest fails, the CLI was run separately to produce inspectable failure evidence:

```text
.venv/bin/python -m spacehealth_model.run --seed 0 --out out/
exit 0: exported schema-valid mission.json and indicators.json
S2 passedBySymptomDay: false
```

CLI exit success means export succeeded, not the synthetic scenario passed. Full output: `model/reports/stage0_seed0_cli.txt`.

Dashboard checks after the contract update:

```text
npm test -- --run
Test Files  1 passed (1)
Tests  20 passed (20)

npm run build
> tsc --noEmit && vite build
✓ 111 modules transformed.
✓ built in 416ms
```

No TypeScript errors. Browser/offline verification remains outside TASK-002. Dashboard checks describe the TASK-002 contract shell at verification time; a separate TASK-003 UI writer may add subsequent tests/features.

## Seed-0 synthetic results

| Item | Observed |
| --- | --- |
| S2 onset / symptom / end | 40 / 42 / 48 |
| S2 first watch / first act in event window | none / none — acceptance miss |
| N1 C1 act / watch days | none / none |
| N2 C4 unknown days | 120, 121, 122, 123, 124 |
| N2 HRV valid preflight observations | 8; HRV baseline insufficient, two other signals can still support evaluation |
| N2 skipped symptom check-ins | days 130–131, explicitly described as not collected |
| Physiological status counts | 715 nominal, 0 watch, 0 act, 5 unknown |
| Routine false alerts outside S2 interval | 0 / 706 evaluable crewmember-days = 0 per 100 |
| S3 warning sample | day 72 at 06:00 |
| Daily / mission dose | independent integration agreement within 1e-6; mission 350.7 mSv per crew |
| Unimplemented sleep/radiation indicators | unknown / insufficient; no claims of detection |

The zero false-alert count is accompanied by a missed S2 event; it is not a claim of detector quality or clinical validity. Full-mission dose = 180 × 1.84 + 19.5; prior career dose remains unknown. Preflight dose is excluded from mission totals.

## Interpretations and unresolved spec points

1. **S2 threshold/effect mismatch:** revised HRV/temperature effects are 0.5–1.0 sample preflight SD, while two signals must exceed 2 robust scales on both consecutive days. RHR rises, but corroboration does not meet persistence in seed 0. Do not inflate effects to obtain a passing demo. Claude/Narayan should decide whether to retain this as a documented miss or revise a research-justified detector/scenario requirement.
2. **S2 timing shape:** research comments specify a two-day ramp and recovery by day 48, but not the recovery duration. Provisional linear two-day ramp + two-day recovery is explicit in stage0.yaml; day 48 has zero injected effect and no remaining injected symptoms. Both weaker SD-unit effects are drawn once per crew from the stated uniform range and multiplied by sample preflight SD (ddof=1). This is an implementation convention, not a verified physiological response.
3. **Persistence semantics:** 'beyond' means strictly > threshold in the configured direction; each day must meet the signal count, but the same two signal identities need not qualify on both days. A skipped symptom check-in is recorded as unknown symptom context; it does not erase evaluable wearable data. Red-flag symptoms override missing signals, with suspect data quality to retain the uncertainty.
4. **Radiation shape:** hourly background and quarter-hour event samples are provisional engineering choices. Linear rise over the stated ~2 h, exponential decay using the lower stated ~24–36 h timescale, truncated after the stated ~9 days; excess rates normalized once to the stated 19.5 mSv integrated event total. Warning active from day-72 06:00 through the chosen rise+decay span. No shelter benefit, radiation threshold or radiation detector implemented.
5. **Day boundary:** t must be <24, while full-day integration needs the right endpoint. The last sample is nextafter(24,0), representing the endpoint within one floating-point ULP. Only that full-day numerical boundary is normalized to coverage 1; genuine missing intervals remain partial. The raw trapezoid integral agrees with an independent implementation.
6. **Mission profile:** delay bounds 0–20 min are illustrative/unverified per A12; blackout windows are unspecified, so an empty list means none simulated, not proof that none occur. DONKI wording labels the near-Earth timing inspiration; no raw SEP-derived crew dosimetry or physical Earth-to-Mars event propagation is claimed. Preflight uses the same radiation sampling background as a simulator convention, but those days are excluded from mission-dose accounting.
7. **Text ownership:** watch/act explanations use cards.yaml templates. Neutral computational labels for nominal/unknown/missingness and correlation are implementation text because no templates are provided for those states. No medical procedure text invented. The forbidden-word filter applies to indicator reasons; source cards contain explicit uncertainty language and are not rewritten by this task.
8. **Version policy:** all active envelopes now require 0.2.0; previous fixture content/checks remain with updated envelopes. Backward loading of 0.1.0 files is not claimed.

## Artifacts and reproducibility

- `model/out/mission.json`, `model/out/indicators.json` (generated, ignored by Git)
- `model/reports/stage0_seed0.json` (metrics, config hash, code hashes, versions)
- `model/reports/stage0_seed0_inputs.json` (exact source bytes and hashes, including updated sleep-debt card)
- `model/reports/s2_seed0.png` (visually inspected; three signals, baseline threshold bands, event/symptom markers)
- `model/EXPERIMENT_LOG.md`

Repeated seed 0 yields identical measurements/events. createdAt is actual run time, so full file hashes change between runs. No holdout used. Source YAML may change later; the captured input snapshot identifies this run.

## TASK-003 steering from Narayan

Re-read research/cards.yaml before demo/cards generation. It now contains sleep-debt (act). C3 demo days 99–101 should use that card instead of a second sleep watch card; all other TASK-003 instructions remain. This TASK-002 session did not generate or edit TASK-003 demo data.

Run config SHA256: `9b9a24ec60b8a1f0de1abb8d0ce21502eede71ed0c6aa6a9bf4d67a66408bfa0`.
