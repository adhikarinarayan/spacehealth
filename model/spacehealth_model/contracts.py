"""Pydantic mirror of contracts/schemas; schema fixtures are the agreement tests."""
from typing import Annotated, Literal
from datetime import datetime
import math
from pydantic import BaseModel, ConfigDict, Field, AfterValidator, model_validator
import json

CrewId = Literal['C1','C2','C3','C4']
Status = Literal['nominal','watch','act','unknown']
Quality = Literal['valid','missing','insufficient','suspect']
ModuleId = Literal['sleep_alertness','physiological_change','radiation']
ScenarioId = Literal['S1','S2','S3','S4','N1','N2']
SignalId = Literal['rhr_bpm','hrv_rmssd_ms','skin_temp_delta_c','sleep_hours','symptoms','spe_warning','dose_rate_msv_h','daily_dose_msv','prior_career_dose_msv','pvt_mean_rt_ms','pvt_lapses','mood_1to5','stress_1to5','exercise_minutes','co2_ppm']
Provenance = Literal['sensor','manual','synthetic','calculated']
Symptom = Literal['fever','sore_throat','cough','congestion','fatigue','headache','muscle_ache','shortness_of_breath','chest_pain','fainting','vision_change','nausea','rash','other']
Text = Annotated[str, Field(min_length=1)]
Nonnegative = Annotated[float, Field(ge=0)]
MissionDay = Annotated[int, Field(ge=1,le=180)]
def day_check(v):
    if not (-14 <= v <= -1 or 1 <= v <= 180): raise ValueError('Invalid mission day')
    return v
Day = Annotated[int, AfterValidator(day_check)]
Hash = Annotated[str, Field(pattern=r'^[a-f0-9]{64}$')]
class Contract(BaseModel):
    @model_validator(mode='before')
    @classmethod
    def optional_nonnull(cls, value):
        if isinstance(value, dict):
            for key in ('unit','baseline','z','persistenceDays','direction','cardId'):
                if key in value and value[key] is None: raise ValueError(f'{key} may be omitted but not null')
        return value
    model_config = ConfigDict(extra='forbid', strict=True, allow_inf_nan=False)
class CrewMember(Contract):
    crewId: CrewId
    label: Text
    prior_career_dose_msv: Nonnegative | None
class DailyReading(Contract):
    crewId: CrewId
    missionDay: Day
    rhr_bpm: float | None
    hrv_rmssd_ms: float | None
    skin_temp_delta_c: float | None
    sleep_hours: float | None
    symptoms: list[Symptom]
    daily_dose_msv: Nonnegative | None
    mood_1to5: Annotated[int,Field(ge=1,le=5)] | None = None
    stress_1to5: Annotated[int,Field(ge=1,le=5)] | None = None
    pvt_mean_rt_ms: float | None = None
    pvt_lapses: Annotated[int,Field(ge=0)] | None = None
    checkin_completed: bool
    dose_coverage: Annotated[float,Field(ge=0,le=1)] | None
    provenance: dict[SignalId, Provenance]
    @model_validator(mode='after')
    def check_symptoms(self):
        if not self.checkin_completed and self.symptoms: raise ValueError('Skipped check-in has symptoms')
        return self
class RadiationEvent(Contract):
    crewId: CrewId
    missionDay: Day
    timeHoursFromDayStart: Annotated[float,Field(ge=0,lt=24)]
    spe_warning: bool
    dose_rate_msv_h: float | None
class ScenarioTruth(Contract):
    scenarioId: ScenarioId
    crewId: CrewId
    moduleId: ModuleId | None
    onsetDay: MissionDay | None
    symptomDay: MissionDay | None
    endDay: MissionDay | None
    description: Text
class Evidence(Contract):
    signalId: SignalId
    value: float | bool | str | None
    unit: Text | None = None
    baseline: float | None = None
    z: float | None = None
    persistenceDays: Annotated[int,Field(ge=0)] | None = None
    direction: Literal['up','down'] | None = None
class Indicator(Contract):
    crewId: CrewId
    missionDay: MissionDay
    moduleId: ModuleId
    status: Status
    dataQuality: Quality
    reason: Text
    evidence: list[Evidence]
    cardId: Text | None = None
    sourceIds: list[Text]
    assumptionIds: list[Text]
    @model_validator(mode='after')
    def check_status(self):
        if (self.status == 'unknown') != (self.dataQuality in ('missing','insufficient')): raise ValueError('Unknown/quality mismatch')
        if 'infection detected' in self.reason.lower(): raise ValueError('Diagnosis wording forbidden')
        return self
class Header(Contract):
    schemaVersion: Literal['0.2.0']
    simulated: Literal[True]
class CommsDelay(Contract):
    min: float
    max: float
class Blackout(Contract):
    startDay: MissionDay
    endDay: MissionDay
class MissionProfile(Contract):
    id: Literal['mars_transit_v1']
    label: Text
    durationDays: Literal[180]
    gcr_background_msv_day: float
    comms_one_way_delay_min: CommsDelay
    blackouts: list[Blackout]
    spe_event_timing_source: Text
class Mission(Header):
    missionProfile: MissionProfile
    generator: Text
    seed: int
    createdAt: Text
    crew: Annotated[list[CrewMember],Field(min_length=1)]
    readings: list[DailyReading]
    radiationEvents: list[RadiationEvent]
    truth: list[ScenarioTruth]
    @model_validator(mode='after')
    def check_date(self):
        dt=datetime.fromisoformat(self.createdAt.replace('Z','+00:00'))
        if dt.tzinfo is None: raise ValueError('Timestamp requires timezone')
        return self
class IndicatorsFile(Header):
    modelId: Text
    configHash: Hash
    missionFile: Hash
    indicators: list[Indicator]
    @model_validator(mode='after')
    def unique(self):
        keys=[(i.crewId,i.missionDay,i.moduleId) for i in self.indicators]
        if len(keys)!=len(set(keys)): raise ValueError('Duplicate indicator key')
        return self
class ValidationResult(Contract):
    scenarioId: ScenarioId
    crewId: CrewId
    moduleId: ModuleId | None
    passed: bool
    passRule: Text
    onsetDay: MissionDay | None
    symptomDay: MissionDay | None
    firstWatchDay: MissionDay | None
    firstActDay: MissionDay | None
    delayVsOnsetDays: int | None
    delayVsSymptomDays: int | None
    routineFalseAlerts: Annotated[int,Field(ge=0)]
    evaluableCrewDays: Annotated[int,Field(ge=0)]
    falseAlertsPer100CrewDays: Nonnegative | None
    unknownDays: Annotated[int,Field(ge=0)]
    notes: str
class ValidationFile(Header):
    modelId: Text
    configHash: Hash
    seedSet: Literal['dev','holdout']
    results: list[ValidationResult]
class Card(Contract):
    id: Text
    status: Status
    heading: Text
    why: Text
    uncertainty: Text
    do_now: list[Text]
    recheck: Text
    onboard_escalation: Text
    ground_escalation: Text
    source_ids: list[Text]
    assumption_ids: list[Text]
class CardsFile(Contract):
    schemaVersion: Literal['0.2.0']
    source: Literal['research/cards.yaml']
    cards: list[Card]
MODELS={'mission':Mission,'indicators':IndicatorsFile,'validation':ValidationFile,'cards':CardsFile}
def strict_loads(text):
    def reject(token): raise ValueError(f'Non-JSON numeric constant: {token}')
    def finite_float(token):
        value=float(token)
        if not math.isfinite(value): raise ValueError(f'Non-finite JSON number: {token}')
        return value
    return json.loads(text,parse_constant=reject,parse_float=finite_float)
