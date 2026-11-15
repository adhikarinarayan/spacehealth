import { useId,useState } from 'react';
import copy from '../data/ui-copy.json';

/** General source-owned guidance, separate from the action card's instructions. */
export function SelfCare({cardId}:{cardId:string}){
 const [open,setOpen]=useState(true);
 const id=useId(),headingId=`self-care-heading-${id}`,bodyId=`self-care-body-${id}`;
 const cards=copy.self_care.cards;
 const guidance=Object.entries(cards).find(([key])=>key===cardId)?.[1];
 if(!guidance)return null;
 return <section className="self-care" aria-labelledby={headingId}>
  <h4 id={headingId}><button type="button" aria-expanded={open} aria-controls={bodyId} onClick={()=>setOpen(value=>!value)}>{copy.self_care.heading}<svg viewBox="0 0 20 20" aria-hidden="true"><path d={open?'m5 12 5-5 5 5':'m5 8 5 5 5-5'} fill="none" stroke="currentColor" strokeWidth="1.5"/></svg></button></h4>
  <p className="self-care-disclaimer">{copy.self_care.disclaimer}</p>
  <div id={bodyId} hidden={!open}><ul>{guidance.steps.map((step,index)=><li key={index}>{step}</li>)}</ul><p className="self-care-sources">{guidance.sources}</p></div>
 </section>;
}
