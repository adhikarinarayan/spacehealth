import type { Mission } from '../data/load';
import type { Indicator } from '../contracts';
export function missionProgress(day:number,duration:number){return Math.max(0,Math.min(1,day/duration));}
export function commsState(profile:Mission['missionProfile'],day:number){
 const progress=profile.durationDays<=1?1:Math.max(0,Math.min(1,(day-1)/(profile.durationDays-1)));
 const {min,max}=profile.comms_one_way_delay_min;
 return {minutes:Math.round(min+(max-min)*progress),blackout:profile.blackouts.some(b=>b.startDay<=day&&day<=b.endDay)};
}
export function stormActive(indicators:Indicator[],crewId:string,day:number){return indicators.some(i=>i.crewId===crewId&&i.missionDay===day&&i.moduleId==='radiation'&&(i.status==='act'||i.evidence.some(e=>e.signalId==='spe_warning'&&e.value===true)));}
export function shipTime(hour:number){const minutes=Math.min(1439,Math.max(0,Math.floor(hour*60+1e-7)));return `${String(Math.floor(minutes/60)).padStart(2,'0')}:${String(minutes%60).padStart(2,'0')}`;}
