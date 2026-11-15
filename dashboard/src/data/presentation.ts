import type { Indicator } from '../contracts';
import type { Mission } from './load';
export const moduleNames={sleep_alertness:'Sleep / alertness',physiological_change:'Physiological change',radiation:'Radiation'};
export const statusNames={nominal:'Nominal',watch:'Watch',act:'Act',unknown:'No reliable data'};
export const statusIcons={nominal:'○',watch:'△',act:'!',unknown:'?'};
export function selectCards(indicators:Indicator[]):Indicator[]{
 const actionable=indicators.filter(i=>(i.status==='watch'||i.status==='act')&&i.cardId);
 const radiation=actionable.filter(i=>i.moduleId==='radiation'&&i.status==='act');
 const symptoms=actionable.filter(i=>i.cardId==='symptom-escalation'&&!radiation.includes(i));
 const critical=new Set([...radiation,...symptoms]);
 return [...radiation,...symptoms,...actionable.filter(i=>!critical.has(i)).slice(0,3)];
}
export function median(values:number[]):number|null{
 if(!values.length)return null;const x=[...values].sort((a,b)=>a-b),middle=Math.floor(x.length/2);
 return x.length%2?x[middle]:(x[middle-1]+x[middle])/2;
}
export function trendData(mission:Mission,crewId:string,day:number,signalId:string){
 const rows=mission.readings.filter(r=>r.crewId===crewId&&r.missionDay<0);
 const values=rows.map(r=>(r as unknown as Record<string,unknown>)[signalId]).filter((v):v is number=>typeof v==='number'&&Number.isFinite(v));
 const center=median(values),mad=center===null?null:median(values.map(v=>Math.abs(v-center)));
 const scale=mad===null?null:1.4826*mad;
 const byDay=new Map(mission.readings.filter(r=>r.crewId===crewId).map(r=>[r.missionDay,r]));
 return {center,scale,points:Array.from({length:Math.min(day,21)},(_,index)=>{
  const d=Math.max(1,day-20)+index;
  const reading=byDay.get(d);
  const rates=mission.radiationEvents.filter(e=>e.crewId===crewId&&e.missionDay===d).map(e=>e.dose_rate_msv_h).filter((v):v is number=>v!==null);
  const value=signalId==='dose_rate_msv_h'?(rates.length?Math.max(...rates):null):reading?(reading as unknown as Record<string,unknown>)[signalId]:null;
  return {day:d,value:typeof value==='number'&&Number.isFinite(value)?value:null};
 })};
}
