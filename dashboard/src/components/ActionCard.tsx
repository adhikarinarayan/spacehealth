import { useState } from 'react';
import { SelfCare } from './SelfCare';
import type { Cards } from '../data/load';
export type ActionEntry={id:string;crewId:string;day:number;cardId:string;action:string;time:string};
export function ActionCard({card,onAction}:{card:Cards['cards'][number];onAction:(action:string)=>void}){
 const [checks,setChecks]=useState<string[]>([]);
 return <><article className="action-card" aria-label={card.heading}><p className="eyebrow">FOLLOW-UP / {card.status.toUpperCase()}</p><h3>{card.heading}</h3><p>{card.why}</p><p className="uncertainty">{card.uncertainty}</p><div className="checklist">{card.do_now.map((step,index)=><label key={index}><input type="checkbox" checked={checks.includes(step)} onChange={()=>setChecks(old=>old.includes(step)?old.filter(s=>s!==step):[...old,step])}/><span>{step}</span></label>)}</div><dl><dt>Recheck</dt><dd>{card.recheck}</dd><dt>Onboard</dt><dd>{card.onboard_escalation}</dd><dt>Ground</dt><dd>{card.ground_escalation}</dd></dl><div className="chips">{[...card.source_ids,...card.assumption_ids].map(id=><span key={id}>{id}</span>)}</div><div className="actions">{['Done','Recheck later','Contact onboard CMO','Queue message to ground'].map(action=><button key={action} onClick={()=>onAction(action)}>{action}</button>)}</div></article><SelfCare cardId={card.id}/></>;
}
