import type { z } from 'zod';
import { fileSchemas } from '../contracts';
export type Mission=z.infer<typeof fileSchemas.mission>;
export type Cards=z.infer<typeof fileSchemas.cards>;
export type MissionCase='illustrative'|'preselected';
export type Bundle={mission:Mission;indicators:z.infer<typeof fileSchemas.indicators>;validation:z.infer<typeof fileSchemas.validation>;cards:Cards;source:'demo'|'data';missionCase?:MissionCase};
export function parseBundle(raw:Record<string,unknown>,source:Bundle['source'],missionCase?:MissionCase):Bundle{
 const result={mission:fileSchemas.mission.parse(raw.mission),indicators:fileSchemas.indicators.parse(raw.indicators),validation:fileSchemas.validation.parse(raw.validation),cards:fileSchemas.cards.parse(raw.cards),source,missionCase};
 if(result.indicators.modelId!==result.validation.modelId||result.indicators.configHash!==result.validation.configHash)throw new Error('Mismatched model report');
 if(missionCase&&result.mission.seed!==(missionCase==='illustrative'?1002:1000))throw new Error('Mismatched mission case seed');
 if(source==='data'&&!result.missionCase)result.missionCase=result.mission.seed===1002?'illustrative':'preselected';
 const crew=new Set(result.mission.crew.map(c=>c.crewId));
 const cardIds=new Set(result.cards.cards.map(c=>c.id));
 if(result.indicators.indicators.some(i=>!crew.has(i.crewId)||(i.cardId&&!cardIds.has(i.cardId))))throw new Error('Unlinked crew or action card');
 return result;
}
export function firstWatchDay(bundle:Bundle,crewId='C2'):number{
 const days=bundle.indicators.indicators.filter(i=>i.crewId===crewId&&i.moduleId==='physiological_change'&&i.status==='watch').map(i=>i.missionDay);
 return days.length?Math.min(...days):1;
}
export async function loadData(search=window.location.search):Promise<Bundle>{
 const params=new URLSearchParams(search),requested=params.get('data')??'data',missionCase=params.get('case')??'illustrative';
 if(requested!=='demo'&&requested!=='data')throw new Error('Unknown data source');
 if(missionCase!=='illustrative'&&missionCase!=='preselected')throw new Error('Unknown mission case');
 const folder=requested==='demo'?'demo':`data/${missionCase}`;
 const names=['mission','indicators','validation','cards'] as const;
 const rows=await Promise.all(names.map(async name=>{
  const response=await fetch(`${import.meta.env.BASE_URL}${folder}/${name}.json`);
  if(!response.ok)throw new Error(`Unable to load ${name}`);
  return [name,await response.json()] as const;
 }));
 return parseBundle(Object.fromEntries(rows),requested,requested==='data'?missionCase:undefined);
}
