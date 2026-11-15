import { CartesianGrid, ComposedChart, Line, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import type { Indicator } from '../contracts';
import type { Bundle } from '../data/load';
import { moduleNames, trendData } from '../data/presentation';
import { Status } from './Status';
import { ActionCard } from './ActionCard';
import { PanelIntro } from './PanelIntro';
import { contextualCard } from '../data/card';
import { uiText } from '../data/ui';
export function Detail({bundle,indicator,replay,onAction,onClose}:{bundle:Bundle;indicator:Indicator;replay:boolean;onAction:(action:string)=>void;onClose:()=>void}){
 const template=bundle.cards.cards.find(c=>c.id===indicator.cardId);
 const card=template?contextualCard(template,indicator,bundle):undefined;
 return <section className="detail-panel" aria-label="Module detail"><PanelIntro panel="detail"/><div className="section-head"><div><p className="eyebrow">DETAIL / DAY {indicator.missionDay}</p><h2>{moduleNames[indicator.moduleId]}</h2></div><button onClick={onClose}>Close detail</button></div><Status status={indicator.status}/><p>{indicator.reason}</p><p className="muted">Data quality: {indicator.dataQuality}</p>
 <div className="charts">{indicator.evidence.filter((e,index)=>!e.unit?.includes('info-only')&&(typeof e.value==='number'||e.value===null)&&indicator.evidence.findIndex(other=>other.signalId===e.signalId)===index).map((e,index)=>{
  const trend=trendData(bundle.mission,indicator.crewId,indicator.missionDay,e.signalId);
  const markers=replay?bundle.mission.truth.filter(t=>t.crewId===indicator.crewId&&t.moduleId===indicator.moduleId):[];
  return <figure key={`${e.signalId}/${index}`}><figcaption>{e.signalId} <span>{e.unit}</span></figcaption><div className="chart" role="img" aria-label={`${e.signalId} trend; missing measurements are gaps`}><ResponsiveContainer width="100%" height={190} minWidth={0}><ComposedChart data={trend.points} margin={{left:0,right:16,top:12,bottom:4}}><CartesianGrid stroke="var(--line)" strokeDasharray="3 4"/><XAxis dataKey="day" type="number" domain={['dataMin','dataMax']} tick={{fill:'var(--muted)',fontSize:11}}/><YAxis domain={['auto','auto']} width={46} tick={{fill:'var(--muted)',fontSize:11}}/><Tooltip contentStyle={{background:'var(--surface)',borderColor:'var(--line)',color:'var(--text)'}}/>{trend.center!==null&&trend.scale!==null&&<ReferenceArea y1={trend.center-trend.scale} y2={trend.center+trend.scale} fill="var(--chart)" fillOpacity={.08}/>}{trend.center!==null&&<ReferenceLine y={trend.center} stroke="var(--muted)" strokeDasharray="4 4"/>}<Line dataKey="value" type="linear" connectNulls={false} stroke="var(--chart)" strokeWidth={2} dot={false} isAnimationActive={false}/>{markers.flatMap(t=>[t.onsetDay&&<ReferenceLine key={`${t.scenarioId}-onset`} x={t.onsetDay} stroke="var(--watch)" label="onset"/>,t.symptomDay&&<ReferenceLine key={`${t.scenarioId}-symptom`} x={t.symptomDay} stroke="var(--act)" label="symptoms"/>])}</ComposedChart></ResponsiveContainer></div><p className="chart-note">{uiText('panels.detail.chart_legend')}</p></figure>;
 })}</div>
 <div className="table-wrap"><table><caption>Evidence for this day</caption><thead><tr>{['Signal','Value','Unit','Baseline','z','Direction'].map(h=><th key={h}>{h}</th>)}</tr></thead><tbody>{indicator.evidence.map((e,index)=><tr key={`${e.signalId}/${index}`}><th scope="row">{e.unit?.includes('multi-signal agreement')?'multi-signal agreement':e.signalId}</th><td>{e.value===null?'Missing':typeof e.value==='number'?e.value.toFixed(2):String(e.value)}</td><td>{e.unit?.startsWith('info-only')?`information only · ${e.unit}`:e.unit??'—'}</td><td>{e.baseline?.toFixed(2)??'—'}</td><td>{e.z?.toFixed(2)??'—'}</td><td>{e.direction??'—'}</td></tr>)}</tbody></table></div>
 {card?<ActionCard key={`${indicator.crewId}/${indicator.missionDay}/${card.id}`} card={card} onAction={onAction}/>:<p className="empty">{uiText('panels.detail.no_action')}</p>}</section>;
}
