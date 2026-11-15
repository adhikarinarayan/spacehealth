# SpaceHealth data contract — v0.1.1 **FROZEN** (Narayan, Sat 2026-11-14 17:58) · v0.2 = §4 missionProfile (approved via D10, lands in TASK-002)

Owner of this spec: Claude · Schemas/validators: Codex · Freeze: Narayan
Base: Discussion.md §4 (exact field names kept). Additions marked **[D6]** were accepted by Narayan (D6, Sat 17:40).
Any change after freeze = one task updating spec + schemas + fixtures + model + dashboard + tests together, logged in `DECISIONS.md`.

## 0. Conventions
- JSON, UTF-8. `schemaVersion: "0.1.0"` on every top-level file.
- `missionDay`: integer, −14…−1 preflight, 1…180 mission. **No day 0.**
- Missing numeric = `null`. Never `0`, never omitted for required keys. `NaN`/`Infinity` invalid.
- Units are in the field name (`_bpm`, `_ms`, `_c`, `_msv`, `_msv_h`); no unit conversion anywhere downstream.
- All demo data carries `simulated: true` at file level.

## 1. Enumerations
```text
Status   = nominal | watch | act | unknown
Quality  = valid | missing | insufficient | suspect
ModuleId = sleep_alertness | physiological_change | radiation
Provenance [D6] = sensor | manual | synthetic | calculated
Symptom  = fever | sore_throat | cough | congestion | fatigue | headache | muscle_ache |
           shortness_of_breath | chest_pain | fainting | vision_change | nausea | rash | other
```
Which symptoms escalate (and how) is **not** in the contract; it lives in `research/rules.yaml`.

## 2. Files the model writes / the dashboard reads

### 2.1 `mission.json`
```ts
{
  schemaVersion: "0.1.0", simulated: true, generator: string, seed: number, createdAt: string /*ISO*/,
  crew: CrewMember[], readings: DailyReading[], radiationEvents: RadiationEvent[],
  truth: ScenarioTruth[]          // [D6] dashboard shows only in Replay/Validation
}
CrewMember = { crewId: string /* "C1".."C4" */, label: string, prior_career_dose_msv: number | null /* [D6] null = unknown, never 0 */ }
```

### 2.2 `DailyReading` (one per crewId × missionDay)
Discussion §4 fields, unchanged:
`crewId, missionDay, rhr_bpm, hrv_rmssd_ms, skin_temp_delta_c, sleep_hours, symptoms: Symptom[], daily_dose_msv, mood_1to5?, stress_1to5?, pvt_mean_rt_ms?, pvt_lapses?`
Added:
- `checkin_completed: boolean` **[D6]** — `false` ⇒ `symptoms` must be `[]` and means "not collected"; `true` + `[]` ⇒ "reported none".
- `dose_coverage: number | null` **[D6]** — fraction (0–1) of the day covered by dose samples; `< 1` ⇒ daily dose is partial and must be shown as such.
- `provenance: Partial<Record<SignalId, Provenance>>` **[D6]**.
**Values:** the schema accepts any *finite* number (or `null`) for numeric signals — no physiological range limits in the schema. Plausibility ranges live in `research/signals.yaml`; the model applies them and reports implausible inputs through `Indicator.dataQuality = "suspect"`. Integers required for `mood_1to5`, `stress_1to5` (1–5) and `pvt_lapses` (≥ 0); `daily_dose_msv` ≥ 0; `dose_coverage` 0–1. (v0.1.1 clarification)
**Optional signals** (`mood_1to5`, `stress_1to5`, `pvt_mean_rt_ms`, `pvt_lapses`): key may be omitted **or** `null`; both mean "not collected". Same rule in JSON Schema, pydantic and Zod. (v0.1.1)

### 2.3 `RadiationEvent` (time-stamped; does not wait for end of day)
Discussion §4 exactly: `crewId, missionDay, timeHoursFromDayStart (0 ≤ t < 24), spe_warning: boolean, dose_rate_msv_h: number | null`.
Daily dose is derived from these samples by the documented integration rule (research A8); mission cumulative dose = sum of daily doses (never independently randomized).

### 2.4 `ScenarioTruth` [D6]
`{ scenarioId: "S1".."S4"|"N1"|"N2", crewId, moduleId: ModuleId | null, onsetDay: number | null, symptomDay: number | null, endDay: number | null, description: string }`

### 2.5 `indicators.json`
```ts
{ schemaVersion, simulated: true, modelId: string, configHash: string, missionFile: string /*sha256*/, indicators: Indicator[] }
Indicator = Discussion §4 exactly:
  crewId, missionDay, moduleId, status, dataQuality, reason, evidence[], cardId?, sourceIds[], assumptionIds[]
Evidence  = { signalId, value, unit?, baseline? } + optional: z?: number, persistenceDays?: number, direction?: "up"|"down"
```
Rules: exactly one Indicator per crewId × missionDay(≥1) × moduleId — enforced in the pydantic and Zod file-level validators and tested; JSON Schema documents it only in `description` (no custom keywords). `dataQuality: insufficient` also covers an unusable baseline (too few valid preflight days). (v0.1.1) `status: unknown` ⇔ `dataQuality ∈ {missing, insufficient}` or unusable baseline. `reason` is plain language built from templates in `research/cards.yaml` / `rules.yaml` — never contains "infection detected" or any diagnosis.

### 2.6 `validation.json`
```ts
{ schemaVersion, simulated: true, modelId, configHash, seedSet: "dev" | "holdout", results: ValidationResult[] }
ValidationResult = { scenarioId, crewId, moduleId, passed: boolean, passRule: string,
  onsetDay, symptomDay, firstWatchDay, firstActDay, delayVsOnsetDays, delayVsSymptomDays,
  routineFalseAlerts, evaluableCrewDays, falseAlertsPer100CrewDays, unknownDays, notes: string }
```

### 2.7 `cards.json` (exported from `research/cards.yaml`; dashboard renders verbatim)
Envelope: `{ schemaVersion, source: "research/cards.yaml", cards: Card[] }` (cards are text, not simulated data — no `simulated` flag). (v0.1.1)
Discussion §2.4: `id, status, heading, why, uncertainty, do_now: string[], recheck, onboard_escalation, ground_escalation, source_ids, assumption_ids`.

## 3. Fixtures (Codex creates, both sides test)
**Naming (v0.1.1):** `<kind>--<violation>.json`, `kind` ∈ {mission, indicators, validation, cards}. Every fixture is a complete top-level file of that kind. One shared manifest `fixtures/manifest.json` lists each fixture, its kind and expected result; both test suites read it.
`fixtures/valid/`: minimal 1-crew × (14+10)-day mission; full indicators incl. each status; validation file; cards.
`fixtures/invalid/`: missing required key, missionDay 0, unknown signal ID, symptoms non-empty with `checkin_completed: false`, `status: nominal` with `dataQuality: missing`, NaN.

## 4. Queued for v0.2 (TASK-002) — DO NOT IMPLEMENT IN TASK-001-fix1
`mission.json` gains `missionProfile` (D10, Mars-class transit):
```ts
missionProfile = { id: "mars_transit_v1", label: string, durationDays: 180,
  gcr_background_msv_day: number /* evidence: NASA-STD-3001 V1 Rev C p.45–46 */,
  comms_one_way_delay_min: { min: number, max: number },
  blackouts: Array<{ startDay: number, endDay: number }>,
  spe_event_timing_source: string /* e.g. "DONKI SEP 2017-09-10, observed near Earth" */ }
```
