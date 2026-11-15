import type { Indicator } from '../contracts';
import type { Bundle,Cards } from './load';
import { uiText } from './ui';
export function contextualCard(card:Cards['cards'][number],indicator:Indicator,bundle:Bundle):Cards['cards'][number]{
 const reading=bundle.mission.readings.find(r=>r.crewId===indicator.crewId&&r.missionDay===indicator.missionDay);
 const get=(id:string,unit:string)=>indicator.evidence.find(e=>e.signalId===id&&e.unit?.includes(unit))?.value;
 const dose=get('daily_dose_msv','mSv today'),missionDose=get('daily_dose_msv','mSv mission')??get('daily_dose_msv','mSv observed');
 const values:Record<string,string|number>={signals:indicator.evidence.map(e=>e.signalId).join(', '),days:indicator.evidence.find(e=>e.persistenceDays!==undefined)?.persistenceDays??'—',symptoms:reading?.symptoms.join(', ')||'—',hours:reading?.sleep_hours??'—',nights:indicator.evidence.find(e=>e.persistenceDays!==undefined)?.persistenceDays??'—',debt_h:String(get('sleep_hours','relative debt')??'—'),rate_text:'',dose_today:typeof dose==='number'?dose.toFixed(2):'—',partial_text:indicator.dataQuality==='valid'?'':` (${indicator.dataQuality})`,mission_dose:typeof missionDose==='number'?missionDose.toFixed(2):'—',career_text:'',pct:'—',career_unknown_text:uiText('panels.radiation_budget.career_unknown')+' '};
 const fill=(text:string)=>text.replace(/\{([^}]+)\}/g,(_,key)=>String(values[key]??'—'));
 return {...card,why:indicator.reason,uncertainty:fill(card.uncertainty),do_now:card.do_now.map(fill),recheck:fill(card.recheck),onboard_escalation:fill(card.onboard_escalation),ground_escalation:fill(card.ground_escalation)};
}
