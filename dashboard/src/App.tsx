import { SolarHero } from './cosmos/SolarHero';
import { Spot } from './cosmos/Effects';
import { DisplayToggle } from './theme/DisplayToggle';
import { lazy, Suspense, useEffect, useState } from 'react';
import type { Indicator } from './contracts';
import { loadData,firstWatchDay,type Bundle,type MissionCase } from './data/load';
import { moduleNames,selectCards } from './data/presentation';
import { footer,mockBanner,queuedMessage } from './copy';
import { SpaceBackdrop,CrewBadge,OrbitalMark,MarsHorizon } from './theme/art';
import { MissionTheme,StormBand } from './theme/MissionTheme';
import { stormActive,shipTime } from './theme/context';
import { Status } from './components/Status';
import { PanelIntro } from './components/PanelIntro';
import { MissionHeader } from './components/MissionHeader';
import { RadiationBudget } from './components/RadiationBudget';
import { CrewGrid } from './components/CrewGrid';
import { Timeline } from './components/Timeline';
import { Sparkline } from './components/Sparkline';
import { uiText } from './data/ui';
import { formatRecordedTime } from './data/actions';
const Detail=lazy(()=>import('./components/Detail').then(m=>({default:m.Detail})));
import { Validation } from './components/Validation';
import type { ActionEntry } from './components/ActionCard';
const storageKey='spacehealth-ui-actions-v1';
function actionKey(bundle?:Bundle){return bundle?.source==='demo'?storageKey:`${storageKey}-${bundle?.missionCase??'illustrative'}`;}
function readActions(bundle?:Bundle):ActionEntry[]{try{const raw=JSON.parse(localStorage.getItem(actionKey(bundle))??'[]');return Array.isArray(raw)?raw.filter(x=>x&&['id','crewId','cardId','action','time'].every(k=>typeof x[k]==='string')&&Number.isInteger(x.day)):[];}catch{return [];}}
export function App({initialData}:{initialData?:Bundle}){
 const [bundle,setBundle]=useState<Bundle|null>(initialData??null),[error,setError]=useState(false);
 const params=new URLSearchParams(window.location.search);
 const [crew,setCrew]=useState(params.get('crew')??'C2');
 const [day,setDay]=useState(()=>Math.min(180,Math.max(1,Math.trunc(Number(params.get('day')))||(initialData?firstWatchDay(initialData):1))));
 const [view,setView]=useState<'today'|'crew'|'log'|'replay'>(['crew','log','replay'].includes(params.get('view')??'')?params.get('view') as 'crew'|'log'|'replay':'today');
 const [selected,setSelected]=useState<Indicator['moduleId']|null>(params.get('detail')==='1'?'physiological_change':null);
 const [eventTime,setEventTime]=useState<{crew:string;day:number;hour:number}|null>(()=>params.has('time')?{crew:params.get('crew')??'C2',day:Math.trunc(Number(params.get('day')))||(initialData?firstWatchDay(initialData):1),hour:Number(params.get('time'))}:null);
 const [playing,setPlaying]=useState(false),[speed,setSpeed]=useState(1);
 const [actions,setActions]=useState<ActionEntry[]>(()=>readActions(initialData)),[notice,setNotice]=useState<{action:string;message:string;queued:boolean}|null>(null);
 const [loadingCase,setLoadingCase]=useState(false),[caseError,setCaseError]=useState('');
 useEffect(()=>{if(initialData)return;let active=true;loadData().then(data=>{if(active){setBundle(data);const startDay=Math.min(180,Math.max(1,Math.trunc(Number(params.get('day')))||firstWatchDay(data)));setDay(startDay);setActions(readActions(data));if(params.has('time'))setEventTime({crew:params.get('crew')??'C2',day:startDay,hour:Number(params.get('time'))});if(!data.mission.crew.some(c=>c.crewId===crew))setCrew(data.mission.crew[0].crewId);}}).catch(()=>{if(active)setError(true);});return()=>{active=false;};},[initialData]);
 async function changeCase(missionCase:MissionCase){
  setLoadingCase(true);setCaseError('');setPlaying(false);
  const next=new URLSearchParams(window.location.search);next.set('data','data');next.set('case',missionCase);next.delete('day');next.delete('time');next.delete('detail');
  try{const data=await loadData('?'+next.toString());setBundle(data);setDay(firstWatchDay(data));setCrew('C2');setSelected(null);setEventTime(null);setNotice(null);setActions(readActions(data));window.history.replaceState({},'','?'+next.toString());}catch{setCaseError('Unable to load the selected mission case. The current case is still shown.');}finally{setLoadingCase(false);}
 }
 useEffect(()=>{if(!playing||view!=='replay')return;const timer=setInterval(()=>setDay(d=>{if(d>=180){setPlaying(false);return 180;}return d+1;}),1000/speed);return()=>clearInterval(timer);},[playing,speed,view]);
 useEffect(()=>{if(!bundle)return;try{localStorage.setItem(actionKey(bundle),JSON.stringify(actions));}catch{/* In-memory record remains available if local persistence is blocked. */}},[actions,bundle?.missionCase,bundle?.source]);
 const changeDay=(value:string)=>{const n=Number(value);if(Number.isInteger(n)&&n>=1&&n<=180)setDay(n);};
 if(error)return <main><h1>Mission data could not be loaded</h1><p>{uiText('states.load_error')}</p><button onClick={()=>window.location.reload()}>Reload</button><footer>{footer}</footer></main>;
 if(!bundle)return <main><h1>SpaceHealth</h1><p role="status">Loading mission files…</p><footer>{footer}</footer></main>;
 const indicators=bundle.indicators.indicators.filter(i=>i.crewId===crew&&i.missionDay===day);
 const current=indicators.find(i=>i.moduleId===selected);
 const attention=selectCards(indicators);
 const times=[...new Set(bundle.mission.radiationEvents.filter(e=>e.crewId===crew&&e.missionDay===day).map(e=>e.timeHoursFromDayStart))].sort((a,b)=>a-b);
 const selectedTime=eventTime?.crew===crew&&eventTime.day===day&&times.includes(eventTime.hour)?eventTime.hour:null;
 function record(action:string){
  if(!current?.cardId)return;
  const entry={id:crypto.randomUUID(),crewId:crew,day,cardId:current.cardId,action,time:new Date().toISOString()};
  setActions(old=>[entry,...old]);setNotice({action,message:uiText('actions.recorded',{time:formatRecordedTime(entry)}),queued:action==='Queue message to ground'});
 }
 return <main><SpaceBackdrop/><header className="masthead"><a className="brand" href={bundle.source==='demo'?'?data=demo':`?case=${bundle.missionCase}`}><OrbitalMark/>SPACE<span>HEALTH</span><small>CREW SELF-MONITORING</small></a><div className="header-controls"><DisplayToggle/>{bundle.source==='data'&&<div className="case-toolbar"><label>Mission<select aria-label="Mission" value={bundle.missionCase} disabled={loadingCase} onChange={e=>void changeCase(e.target.value as MissionCase)}><option value="illustrative">Showcase mission — shows every feature</option><option value="preselected">Blind test mission — fixed before results</option></select></label>{loadingCase&&<span role="status">Loading mission case…</span>}{caseError&&<span role="alert">{caseError}</span>}</div>}</div><MissionTheme mission={bundle.mission} day={day} intradayHour={selectedTime}/></header>
 {stormActive(bundle.indicators.indicators,crew,day)&&<StormBand/>}
 {bundle.source==='demo'?<aside className="mock-banner">{mockBanner}</aside>:<aside className="mock-banner">{uiText(`panels.validation.${bundle.missionCase==='illustrative'?'illustrative_case_note':'preselected_case_note'}`)} <span title={bundle.indicators.modelId}>Simulated data · settings locked before testing · mission no. {bundle.mission.seed}</span></aside>}

 <SolarHero mission={bundle.mission} day={day} onDay={changeDay}/>
 <div className="nav-row"><nav aria-label="Views">{([{id:'today',label:'Today'},{id:'crew',label:'Crew'},{id:'log',label:'Log'},{id:'replay',label:'Replay + Validation'}] as const).map(tab=><button key={tab.id} className={view===tab.id?'active':''} aria-current={view===tab.id?'page':undefined} onClick={()=>{setView(tab.id);if(tab.id!=='replay')setPlaying(false);}}>{tab.label}</button>)}</nav></div>
 <MissionHeader mission={bundle.mission} day={day}/>
 <section className="page-heading"><MarsHorizon/><div><p className="eyebrow">PERSONAL MISSION OVERVIEW</p><h1>{view==='today'?uiText('panels.today_tiles.title'):view==='crew'?uiText('panels.crew_grid.title'):view==='log'?uiText('panels.timeline.title'):uiText('panels.replay.title')}</h1></div><div className="selectors"><div className="selector-crew"><CrewBadge crewId={crew}/><label>Crew<select aria-label="Crew" value={crew} onChange={e=>setCrew(e.target.value)}>{bundle.mission.crew.map(c=><option key={c.crewId} value={c.crewId}>{c.crewId} · {c.label}</option>)}</select></label></div><label>Mission day<input aria-label="Mission day" type="number" min="1" max="180" value={day} onChange={e=>changeDay(e.target.value)}/></label></div></section>
 <RadiationBudget mission={bundle.mission} crewId={crew} day={day}/>
 {view==='replay'&&<section className="replay-bar panel" aria-label="Mission replay"><PanelIntro panel="replay"/><button onClick={()=>setPlaying(p=>!p)}>{playing?'Pause':'Play'}</button><label>Speed<select aria-label="Replay speed" value={speed} onChange={e=>setSpeed(Number(e.target.value))}>{[1,5,20].map(s=><option key={s} value={s}>{s} day{s>1?'s':''}/second</option>)}</select></label><label className="scrubber">Day {day}<input aria-label="Replay day" type="range" min="1" max="180" value={day} onChange={e=>{setPlaying(false);changeDay(e.target.value);}}/></label><label className="time-selector">{uiText('theme.ship_clock_daily',{day})}<select aria-label="Ship time" value={selectedTime??'daily'} onChange={e=>setEventTime(e.target.value==='daily'?null:{crew,day,hour:Number(e.target.value)})}><option value="daily">{uiText('theme.ship_clock_daily',{day})}</option>{times.map(hour=><option key={hour} value={hour}>{uiText('theme.ship_clock',{day,time:shipTime(hour)})}</option>)}</select></label><div className="truth"><strong>Replay-only scenario markers</strong>{bundle.mission.truth.filter(t=>t.crewId===crew).map((t,index)=><span key={index}>{t.scenarioId}: onset {t.onsetDay??'—'} · symptoms {t.symptomDay??'—'}</span>)}</div></section>}
 {view==='crew'&&<CrewGrid bundle={bundle} day={day} onSelect={(cid,moduleId)=>{setCrew(cid);setSelected(moduleId);}}/>}
 {view==='log'&&<Timeline bundle={bundle} crewId={crew} actions={actions} onJump={(d,cid,moduleId)=>{setDay(d);setCrew(cid);setSelected(moduleId);setView('today');}}/>}
 {(view==='today'||view==='replay')&&<section className="today-panel panel"><PanelIntro panel="today_tiles"/><div className="module-grid" aria-label="Health modules">{(Object.keys(moduleNames) as Indicator['moduleId'][]).map(moduleId=>{
  const i=indicators.find(r=>r.moduleId===moduleId);
  return <Spot key={moduleId}><button className={`module-tile ${selected===moduleId?'selected':''}`} onClick={()=>setSelected(moduleId)} aria-label={`${moduleNames[moduleId]} detail`} aria-pressed={selected===moduleId}><Status status={i?.status??'unknown'}/><h3>{moduleNames[moduleId]}</h3><Sparkline mission={bundle.mission} crewId={crew} day={day} signalId={moduleId==='physiological_change'?'rhr_bpm':moduleId==='sleep_alertness'?'sleep_hours':'daily_dose_msv'}/><p>{i?.reason??uiText('states.indicator_unavailable')}</p><small>Data quality: {i?.dataQuality??'missing'} <span aria-hidden="true">↗</span></small></button></Spot>;
 })}</div></section>}
 {(view==='today'||view==='replay')&&<section className="attention panel"><PanelIntro panel="attention_cards"/>{attention.length?<div className="attention-list">{attention.map(i=>{
  const card=bundle.cards.cards.find(c=>c.id===i.cardId)!;
  return <button key={i.moduleId} className="attention-row" onClick={()=>setSelected(i.moduleId)}><Status status={i.status}/><span><strong>{card.heading}</strong><span>{i.reason}</span></span><span aria-hidden="true">↗</span></button>;
 })}</div>:<p className="empty">{uiText('panels.attention_cards.empty')}</p>}</section>}
 {current&&<Suspense fallback={<p role="status">Loading module detail…</p>}><Detail bundle={bundle} indicator={current} replay={view==='replay'} onAction={record} onClose={()=>setSelected(null)}/></Suspense>}
 <p role="status" className="notice">{notice&&<><strong>{notice.action}</strong>{' — '}<span>{notice.message}</span>{notice.queued&&<> {queuedMessage}</>}</>}</p>
 {view==='replay'&&<Validation bundle={bundle}/>}
 <footer>{footer}</footer></main>;
}
