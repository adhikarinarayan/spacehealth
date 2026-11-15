import { useEffect,useState } from 'react';
import type { Mission } from '../data/load';
import { uiText } from '../data/ui';
import { Earth,Mars,Helmet } from './art';
import { missionProgress,commsState,shipTime } from './context';
function useReducedMotion(){
 const [reduced,setReduced]=useState(()=>typeof window.matchMedia==='function'?window.matchMedia('(prefers-reduced-motion: reduce)').matches:true);
 useEffect(()=>{if(typeof window.matchMedia!=='function')return;const query=window.matchMedia('(prefers-reduced-motion: reduce)');const change=()=>setReduced(query.matches);change();query.addEventListener?.('change',change);return()=>query.removeEventListener?.('change',change);},[]);
 return reduced;
}
export function MissionTheme({mission,day,intradayHour=null}:{mission:Mission;day:number;intradayHour?:number|null}){
 const p=mission.missionProfile;const progress=missionProgress(day,p.durationDays),comms=commsState(p,day),reduced=useReducedMotion();
 return <div className="mission-theme"><div className="trajectory-label">{uiText('theme.trajectory_label',{day,duration:p.durationDays})}</div><div className="trajectory"><Earth/><div className="trajectory-track"><div className={`trajectory-marker${reduced?'':' theme-motion'}`} data-testid="trajectory-marker" data-progress={progress} style={{left:`${progress*100}%`}}><Helmet/></div></div><Mars/></div><div className={`comms-link${comms.blackout?' link-down':''}`}><svg viewBox="0 0 70 22" aria-hidden="true"><path d="M6 11h58" fill="none" stroke="currentColor" strokeWidth="1.5" strokeDasharray={comms.blackout?'4 5':'2 3'}/><path d="m10 6-5 5 5 5m50-10 5 5-5 5" fill="none" stroke="currentColor" strokeWidth="1.5"/>{comms.blackout&&<path d="m29 5 12 12m0-12L29 17" stroke="currentColor" strokeWidth="2"/>}</svg><span>{comms.blackout?uiText('theme.comms_blackout'):uiText('theme.comms_link',{minutes:comms.minutes})}</span></div><p className="ship-clock">{intradayHour===null?uiText('theme.ship_clock_daily',{day}):uiText('theme.ship_clock',{day,time:shipTime(intradayHour)})}</p></div>;
}
export function StormBand(){return <section className="storm-band" role="alert"><svg viewBox="0 0 32 32" aria-hidden="true"><path d="m16 3 14 25H2z" fill="none" stroke="currentColor" strokeWidth="2"/><path d="M16 11v8m0 3v2" stroke="currentColor" strokeWidth="2.5"/></svg><div><h2>{uiText('theme.storm_banner_title')}</h2><p>{uiText('theme.storm_banner_body')}</p><small>{uiText('theme.storm_banner_note')}</small></div></section>;}
