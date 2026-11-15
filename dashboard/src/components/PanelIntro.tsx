import { useEffect,useId,useState } from 'react';
import { uiText } from '../data/ui';
export function PanelIntro({panel,values={},extraHelpKeys=[]}:{panel:string;values?:Record<string,string|number>;extraHelpKeys?:string[]}){
 const storageKey=`spacehealth-panel-help-${panel}`;const id=useId();
 const [open,setOpen]=useState(()=>{try{const saved=localStorage.getItem(storageKey);return saved===null||saved==='open';}catch{return true;}});
 useEffect(()=>{try{if(localStorage.getItem(storageKey)===null)localStorage.setItem(storageKey,'seen');}catch{/* Help still works without persistence. */}},[storageKey]);
 function toggle(){setOpen(x=>{const next=!x;try{localStorage.setItem(storageKey,next?'open':'closed');}catch{/* In-memory preference. */}return next;});}
 return <div className="panel-intro" data-panel={panel}><div className="section-head"><h2>{uiText(`panels.${panel}.title`,values)}</h2><button className="help-toggle" aria-expanded={open} aria-controls={id} onClick={toggle}>How to read this</button></div><p>{uiText(`panels.${panel}.what_for`,values)}</p>{open&&<p id={id} className="panel-help">{uiText(`panels.${panel}.how_to_read`,values)}{extraHelpKeys.map(key=><span className="extra-help" key={key}> {uiText(key,values)}</span>)}</p>}</div>;
}
