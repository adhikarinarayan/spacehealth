import { useState } from 'react';
import type { Bundle } from '../data/load';
import type { Indicator } from '../contracts';
import type { ActionEntry } from './ActionCard';
import { timelineEntries } from '../data/mission';
import { moduleNames } from '../data/presentation';
import { uiText } from '../data/ui';
import { PanelIntro } from './PanelIntro';
export function Timeline({bundle,crewId,actions,onJump}:{bundle:Bundle;crewId:string;actions:ActionEntry[];onJump:(day:number,crew:string,moduleId:Indicator['moduleId']|null)=>void}){
 const [all,setAll]=useState(false),[module,setModule]=useState('all');
 const entries=timelineEntries(bundle.indicators.indicators,bundle.mission,actions).filter(e=>(all||e.crewId===crewId)&&(module==='all'||e.moduleId===module));
 return <section className="timeline panel" aria-label="Mission log"><PanelIntro panel="timeline"/><div className="log-filters"><label><input type="checkbox" checked={all} onChange={e=>setAll(e.target.checked)}/> All crew</label><label>Module<select aria-label="Log module" value={module} onChange={e=>setModule(e.target.value)}><option value="all">All modules</option>{Object.entries(moduleNames).map(([id,name])=><option key={id} value={id}>{name}</option>)}</select></label></div>{entries.length?<ol className="timeline-list">{entries.map(entry=><li key={entry.id}><button onClick={()=>onJump(entry.day,entry.crewId,entry.moduleId)}><span className={`log-dot log-${entry.kind}`} aria-hidden="true"/><span>{entry.label}</span><span aria-hidden="true">↗</span></button></li>)}</ol>:<p className="empty">{uiText('panels.timeline.empty')}</p>}</section>;
}
