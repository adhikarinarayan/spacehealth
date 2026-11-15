/** Deliberately authored UI fixtures. This is not the model simulator or its output. */
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { readFileSync, mkdirSync, writeFileSync } from 'node:fs';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { fileSchemas, type Indicator } from '../src/contracts/index';
const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
const dashboard=resolve(root,'dashboard');
const yamlPath=resolve(root,'research/cards.yaml');
const sourceCards=JSON.parse(execFileSync(resolve(root,'model/.venv/bin/python'),['-c','import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1]))["cards"]))',yamlPath],{encoding:'utf8'}));
const uiCopy=JSON.parse(execFileSync(resolve(root,'model/.venv/bin/python'),['-c','import json,sys,yaml; print(json.dumps(yaml.safe_load(open(sys.argv[1]))))',resolve(root,'research/ui_copy.yaml')],{encoding:'utf8'}));
writeFileSync(resolve(dashboard,'src/data/ui-copy.json'),JSON.stringify(uiCopy,null,2)+'\n');
const words:Record<string,string>={signals:'Resting heart rate and skin-temperature deviation',days:'2',symptoms:'fatigue',hours:'5.2',nights:'2',debt_h:'9.0',rate_text:'',dose_today:'1.84',partial_text:' (illustrative mock total)',mission_dose:'350.7',career_text:'; career total unknown',pct:'not determined',career_unknown_text:'Career total unknown. '};
// Expand source templates with visibly illustrative UI context; never author medical instructions.
function expand(s:string):string{return s.replace(/\{([^}]+)\}/g,(_,key)=>{if(!(key in words))throw new Error(`Unknown card placeholder ${key}`);return words[key];});}
const cards=fileSchemas.cards.parse({schemaVersion:'0.2.0',source:'research/cards.yaml',cards:sourceCards.map((c:Record<string,unknown>)=>Object.fromEntries(Object.entries(c).map(([k,v])=>[k,typeof v==='string'?expand(v):Array.isArray(v)?v.map(x=>typeof x==='string'?expand(x):x):v])))});
// symptom-escalation has its own matching mock symptom context.
const symptomCard=cards.cards.find(c=>c.id==='symptom-escalation')!;
symptomCard.why=expand(sourceCards.find((c:{id:string})=>c.id==='symptom-escalation').why.replace('{symptoms}','chest_pain'));
const baseline={rhr_bpm:61,hrv_rmssd_ms:48,skin_temp_delta_c:0,sleep_hours:7};
const days=[...Array.from({length:14},(_,i)=>i-14),...Array.from({length:180},(_,i)=>i+1)];
const crew=['C1','C2','C3','C4'].map((crewId,i)=>({crewId,label:['Alex','Sam','Jordan','Riley'][i],prior_career_dose_msv:i===0?120:null}));
const readings=crew.flatMap(({crewId},index)=>days.map(missionDay=>{
 const phase=(missionDay+index)*.8;
 const gap=crewId==='C4'&&missionDay>=120&&missionDay<=124;
 const shifted=crewId==='C2'&&missionDay>=40&&missionDay<=46;
 const short=crewId==='C3'&&missionDay>=95&&missionDay<=101;
 return {crewId,missionDay,rhr_bpm:gap?null:baseline.rhr_bpm+index+Math.sin(phase)+(shifted?7:0),hrv_rmssd_ms:gap?null:baseline.hrv_rmssd_ms+index+2*Math.sin(phase)-(shifted?8:0),skin_temp_delta_c:gap?null:.06*Math.sin(phase)+(shifted?.6:0),sleep_hours:gap?null:short?5.2:7+.15*Math.sin(phase),symptoms:crewId==='C1'&&missionDay===30?['chest_pain']:shifted&&missionDay>=42?['fatigue']:[],checkin_completed:true,daily_dose_msv:1.84,dose_coverage:1,provenance:{rhr_bpm:'synthetic',hrv_rmssd_ms:'synthetic',skin_temp_delta_c:'synthetic',sleep_hours:'synthetic',symptoms:'synthetic',daily_dose_msv:'synthetic'}};
}));
const mission=fileSchemas.mission.parse({schemaVersion:'0.2.0',simulated:true,generator:'MOCK UI fixtures — not model output',seed:0,createdAt:'2026-11-14T00:00:00Z',missionProfile:{id:'mars_transit_v1',label:'Mars transit (simulated)',durationDays:180,gcr_background_msv_day:1.84,comms_one_way_delay_min:{min:0,max:20},blackouts:[{startDay:150,endDay:160}],spe_event_timing_source:'UI mock; no space-weather prediction'},crew,readings,radiationEvents:crew.map(c=>({crewId:c.crewId,missionDay:72,timeHoursFromDayStart:6,spe_warning:true,dose_rate_msv_h:.7})),truth:[{scenarioId:'S2',crewId:'C2',moduleId:'physiological_change',onsetDay:40,symptomDay:42,endDay:46,description:'Authored physiological UI sequence'},{scenarioId:'S3',crewId:'C1',moduleId:'radiation',onsetDay:72,symptomDay:null,endDay:72,description:'Authored radiation warning UI sequence'},{scenarioId:'S4',crewId:'C3',moduleId:'sleep_alertness',onsetDay:95,symptomDay:null,endDay:101,description:'Authored sleep UI sequence'},{scenarioId:'N2',crewId:'C4',moduleId:null,onsetDay:120,symptomDay:null,endDay:124,description:'Authored missing-data UI sequence'}]});
const moduleIds=['sleep_alertness','physiological_change','radiation'] as const;
const signalLists={sleep_alertness:['sleep_hours'],physiological_change:['rhr_bpm','hrv_rmssd_ms','skin_temp_delta_c'],radiation:['dose_rate_msv_h']} as const;
const units={rhr_bpm:'bpm',hrv_rmssd_ms:'ms',skin_temp_delta_c:'°C deviation',sleep_hours:'h',dose_rate_msv_h:'mSv/h'};
const indicators:Indicator[]=mission.readings.filter(r=>r.missionDay>0).flatMap(r=>moduleIds.map(moduleId=>{
 let status:Indicator['status']='nominal',cardId:string|undefined;
 if(r.crewId==='C4'&&r.missionDay>=120&&r.missionDay<=124&&moduleId!=='radiation')status='unknown';
 if(r.crewId==='C2'&&r.missionDay>=40&&r.missionDay<=46&&moduleId==='physiological_change'){status=r.missionDay>=42?'act':'watch';cardId=status==='watch'?'physiological-change':'physiological-change-act';}
 if(moduleId==='radiation'&&r.missionDay===72){status='act';cardId='radiation-spe-procedure';}
 if(r.crewId==='C3'&&r.missionDay>=96&&r.missionDay<=101&&moduleId==='sleep_alertness'){status=r.missionDay>=99?'act':'watch';cardId=status==='act'?'sleep-debt':'sleep-short';}
 if(r.crewId==='C1'&&r.missionDay===30&&moduleId==='physiological_change'){status='act';cardId='symptom-escalation';}
 const card=cards.cards.find(c=>c.id===cardId);
 const evidence=signalLists[moduleId].map(signalId=>{
  const value=signalId==='dose_rate_msv_h'?(r.missionDay===72?.7:1.84/24):r[signalId];
  const normal=signalId==='dose_rate_msv_h'?1.84/24:baseline[signalId];
  return {signalId,value,unit:units[signalId],baseline:normal,...(signalId!=='dose_rate_msv_h'?{direction:signalId==='hrv_rmssd_ms'||signalId==='sleep_hours'?'down' as const:'up' as const}:{}),...(value===null?{}:{z:(value-normal)/(signalId==='rhr_bpm'?1.5:signalId==='hrv_rmssd_ms'?5:signalId==='sleep_hours'?.3:.1)})};
 });
 return {crewId:r.crewId,missionDay:r.missionDay,moduleId,status,dataQuality:status==='unknown'?'missing':'valid',reason:status==='unknown'?'Mock: wearable measurements are missing.':card?card.why:'Mock: no authored change for this module today.',evidence,...(cardId?{cardId}:{}),sourceIds:card?.source_ids??[],assumptionIds:['UI-MOCK',...(card?.assumption_ids??[])]};
}));
const serialize=(v:unknown)=>JSON.stringify(v,null,2)+'\n';
const hash=(s:string)=>createHash('sha256').update(s).digest('hex');
const indicatorsFile=fileSchemas.indicators.parse({schemaVersion:'0.2.0',simulated:true,modelId:'UI-MOCK-NOT-MODEL',configHash:hash(readFileSync(yamlPath,'utf8')),missionFile:hash(serialize(mission)),indicators});
const validation=fileSchemas.validation.parse({schemaVersion:'0.2.0',simulated:true,modelId:'UI-MOCK-NOT-MODEL',configHash:indicatorsFile.configHash,seedSet:'dev',results:mission.truth.map(t=>{
 const rows=indicators.filter(i=>i.crewId===t.crewId&&i.moduleId===t.moduleId&&i.missionDay>=(t.onsetDay??1));
 const watch=rows.find(i=>i.status==='watch')?.missionDay??null,act=rows.find(i=>i.status==='act')?.missionDay??null;
 const first=watch===null?act:act===null?watch:Math.min(watch,act);
 return {scenarioId:t.scenarioId,crewId:t.crewId,moduleId:t.moduleId,passed:true,passRule:'Authored UI fixture sequence only; not a detector result',onsetDay:t.onsetDay,symptomDay:t.symptomDay,firstWatchDay:watch,firstActDay:act,delayVsOnsetDays:first!==null&&t.onsetDay!==null?first-t.onsetDay:null,delayVsSymptomDays:first!==null&&t.symptomDay!==null?first-t.symptomDay:null,routineFalseAlerts:0,evaluableCrewDays:180,falseAlertsPer100CrewDays:0,unknownDays:t.scenarioId==='N2'?5:0,notes:'MOCK UI fixture — illustrative values, not measured validation'};
})});
mkdirSync(resolve(dashboard,'public/demo'),{recursive:true});
for(const [name,value] of Object.entries({mission,indicators:indicatorsFile,validation,cards}))writeFileSync(resolve(dashboard,`public/demo/${name}.json`),serialize(value));
console.log(`Validated UI mock: ${mission.readings.length} readings, ${indicators.length} indicators; card text from research/cards.yaml.`);
