import { useEffect,useState } from 'react';
export function DisplayToggle(){
 const [light,setLight]=useState(()=>{try{return localStorage.getItem('spacehealth-display')==='light';}catch{return false;}});
 useEffect(()=>{document.documentElement.dataset.display=light?'light':'dark';try{localStorage.setItem('spacehealth-display',light?'light':'dark');}catch{/* Switching remains available without storage. */}},[light]);
 return <button className="display-toggle" aria-pressed={light} onClick={()=>setLight(v=>!v)}><svg viewBox="0 0 24 24" aria-hidden="true">{light?<><circle cx="12" cy="12" r="4" fill="currentColor"/><path d="M12 1v3m0 16v3M1 12h3m16 0h3M4 4l2 2m12 12 2 2M4 20l2-2M18 6l2-2" fill="none" stroke="currentColor" strokeWidth="1.6"/></>:<path d="M19 15.5A8 8 0 0 1 8.5 5 8 8 0 1 0 19 15.5Z" fill="none" stroke="currentColor" strokeWidth="1.7"/>}</svg>Light display</button>;
}
