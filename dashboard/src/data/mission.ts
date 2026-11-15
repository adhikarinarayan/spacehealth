import type { Mission } from './load';
import type { Indicator } from '../contracts';
import type { ActionEntry } from '../components/ActionCard';
import { moduleNames,statusNames } from './presentation';
import { queuedMessage } from '../copy';
export const CAREER_LIMIT_MSV=600;
export function radiationBudget(mission:Mission,crewId:string,day:number){
 const crew=mission.crew.find(c=>c.crewId===crewId);
 const map=new Map(mission.readings.filter(r=>r.crewId===crewId&&r.missionDay>0&&r.missionDay<=day).map(r=>[r.missionDay,r]));
 let missionDose=0,partial=false;
 for(let d=1;d<=day;d++){const r=map.get(d);if(r?.daily_dose_msv!==null&&r?.daily_dose_msv!==undefined)missionDose+=r.daily_dose_msv;else partial=true;if(r?.dose_coverage===null||r?.dose_coverage===undefined||r.dose_coverage<1)partial=true;}
 const projectedMission=missionDose+Math.max(0,mission.missionProfile.durationDays-day)*mission.missionProfile.gcr_background_msv_day;
 const prior=crew?.prior_career_dose_msv??null;
 return {missionDose,projectedMission,prior,careerDose:prior===null?null:prior+missionDose,projectedCareer:prior===null?null:prior+projectedMission,partial};
}
export type TimelineEntry={id:string;day:number;crewId:string;moduleId:Indicator['moduleId']|null;kind:'transition'|'warning'|'action';label:string;time:number};
export function timelineEntries(indicators:Indicator[],mission:Mission,actions:ActionEntry[]):TimelineEntry[]{
 const result:TimelineEntry[]=[];const previous=new Map<string,Indicator>();
 for(const indicator of [...indicators].sort((a,b)=>a.missionDay-b.missionDay||a.crewId.localeCompare(b.crewId)||a.moduleId.localeCompare(b.moduleId))){
  const key=`${indicator.crewId}/${indicator.moduleId}`,before=previous.get(key);
  if(before&&before.status!==indicator.status)result.push({id:`transition/${key}/${indicator.missionDay}`,day:indicator.missionDay,crewId:indicator.crewId,moduleId:indicator.moduleId,kind:'transition',time:0,label:`Day ${indicator.missionDay} · ${indicator.crewId} · ${moduleNames[indicator.moduleId]}: ${statusNames[before.status]} → ${statusNames[indicator.status]}`});
  previous.set(key,indicator);
 }
 const warningState=new Map<string,boolean>();
 for(const event of [...mission.radiationEvents].sort((a,b)=>a.missionDay-b.missionDay||a.timeHoursFromDayStart-b.timeHoursFromDayStart)){
  if(event.spe_warning&&!warningState.get(event.crewId))result.push({id:`warning/${event.crewId}/${event.missionDay}/${event.timeHoursFromDayStart}`,day:event.missionDay,crewId:event.crewId,moduleId:'radiation',kind:'warning',time:event.timeHoursFromDayStart,label:`Day ${event.missionDay} · ${event.crewId} · SPE warning · ${event.timeHoursFromDayStart.toFixed(2)} h`});
  warningState.set(event.crewId,event.spe_warning);
 }
 for(const action of actions){const moduleId=indicators.find(i=>i.crewId===action.crewId&&i.missionDay===action.day&&i.cardId===action.cardId)?.moduleId??null;result.push({id:`action/${action.id}`,day:action.day,crewId:action.crewId,moduleId,kind:'action',time:24+(Number.isNaN(Date.parse(action.time))?0:Date.parse(action.time)/86400000),label:`Day ${action.day} · ${action.crewId} · ${action.action==='Queue message to ground'?queuedMessage:action.action}`});}
 return result.sort((a,b)=>b.day-a.day||b.time-a.time||a.id.localeCompare(b.id));
}
