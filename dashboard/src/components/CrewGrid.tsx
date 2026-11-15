import type { Bundle } from '../data/load';
import type { Indicator } from '../contracts';
import { moduleNames } from '../data/presentation';
import { Status } from './Status';
import { CrewBadge } from '../theme/art';
import { PanelIntro } from './PanelIntro';
export function CrewGrid({bundle,day,onSelect}:{bundle:Bundle;day:number;onSelect:(crewId:string,moduleId:Indicator['moduleId'])=>void}){
 return <section className="crew-overview panel" aria-label="Crew overview"><PanelIntro panel="crew_grid" extraHelpKeys={['theme.crew_badge_note']}/><div className="crew-grid">{bundle.mission.crew.map(crew=><article className="crew-row" key={crew.crewId}><h3><CrewBadge crewId={crew.crewId}/>{crew.crewId} · {crew.label}</h3><div className="crew-cells">{(Object.keys(moduleNames) as Indicator['moduleId'][]).map(moduleId=>{const i=bundle.indicators.indicators.find(i=>i.crewId===crew.crewId&&i.missionDay===day&&i.moduleId===moduleId);return <button key={moduleId} className="crew-cell" aria-label={`${crew.crewId} ${moduleNames[moduleId]} detail`} onClick={()=>onSelect(crew.crewId,moduleId)}><span className="cell-module">{moduleNames[moduleId]}</span><Status status={i?.status??'unknown'}/><span className="truncate" title={i?.reason}>{i?.reason??'—'}</span></button>;})}</div></article>)}</div></section>;
}
