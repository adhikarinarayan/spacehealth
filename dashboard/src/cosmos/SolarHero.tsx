import { useId,type CSSProperties } from 'react';
import type { Mission } from '../data/load';
import { commsState,missionProgress } from '../theme/context';
import { Shine } from './Effects';
import { uiText } from '../data/ui';

/*
 * Illustrative orrery. Planet angles follow real orbital periods; the craft follows a
 * Hohmann-style half ellipse from Earth's orbit to Mars' orbit across the mission length.
 * Radii are compressed for legibility, so this is a diagram, not an ephemeris.
 */
const C=300;
const AU=(au:number)=>70+(au-.39)*143.4;
const R={mercury:AU(.39),venus:AU(.72),earth:AU(1),mars:AU(1.52)};
const PERIOD={mercury:88,venus:225,earth:365.25,mars:687};
const DEPART=-0.32; // radians; the half-ellipse sweeps across the top of the frame, Earth (right) to Mars (left)
const TAU=Math.PI*2;
const pt=(r:number,a:number)=>({x:C+r*Math.cos(a),y:C-r*Math.sin(a)});
const f=(n:number)=>n.toFixed(1);

function seeded(seed:number){let s=seed;return()=>{s=(Math.imul(s,1664525)+1013904223)>>>0;return s/4294967296;};}
const belt=(()=>{const r=seeded(3141);return Array.from({length:140},()=>{const a=r()*TAU,d=258+r()*18;return {...pt(d,a),s:.4+r()*.9,o:.12+r()*.3};});})();
const ticks=Array.from({length:120},(_,i)=>{const a=i/120*TAU,long=i%10===0;const p1=pt(long?280:285,a),p2=pt(291,a);return {p1,p2,long};});

export function geometry(day:number,duration:number){
 const p=missionProgress(day,duration),r1=R.earth,r2=R.mars,a=(r1+r2)/2,e=(r2-r1)/(r2+r1);
 const orbit=(theta:number)=>a*(1-e*e)/(1+e*Math.cos(theta));
 const at=(prog:number)=>{const th=Math.PI*prog;return pt(orbit(th),DEPART+th);};
 const path=(from:number,to:number)=>{const n=72;let d='';for(let i=0;i<=n;i++){const q=at(from+(to-from)*i/n);d+=`${i?'L':'M'}${f(q.x)} ${f(q.y)}`;}return d;};
 const t=day-1,left=duration-day;
 return {
  progress:p,craft:at(p),depart:at(0),arrive:at(1),planned:path(0,1),flown:path(0,Math.max(p,.0001)),
  earth:pt(r1,DEPART+t*TAU/PERIOD.earth),
  mars:pt(r2,DEPART+Math.PI-left*TAU/PERIOD.mars),
  mercury:pt(R.mercury,1.1+t*TAU/PERIOD.mercury),
  venus:pt(R.venus,2.4+t*TAU/PERIOD.venus),
 };
}

export function SolarHero({mission,day,onDay}:{mission:Mission;day:number;onDay:(value:string)=>void}){
 const profile=mission.missionProfile,duration=profile.durationDays;
 const g=geometry(day,duration),comms=commsState(profile,day),id=useId().replace(/[^a-zA-Z0-9_-]/g,'');
 const pct=Math.round(g.progress*100);
 return <section className="solar-hero" aria-label={uiText('theme.orrery.title')}>
  <div className="solar-copy">
   <h2 className="solar-title"><Shine>{uiText('theme.orrery.title')}</Shine></h2>
   <p className="solar-lede">{uiText('theme.orrery.lead',{minutes:comms.minutes})}</p>
   <dl className="solar-stats">
    <div><dt>{uiText('theme.orrery.stat_day')}</dt><dd><span className="solar-num">{day}</span><small>/ {duration}</small></dd></div>
    <div><dt>{uiText('theme.orrery.stat_transit')}</dt><dd><span className="solar-num">{pct}</span><small>%</small></dd></div>
    <div className={comms.blackout?'is-down':undefined}><dt>{uiText('theme.orrery.stat_delay')}</dt><dd>{comms.blackout?<span className="solar-num solar-down">{uiText('theme.orrery.stat_blackout')}</span>:<><span className="solar-num">{comms.minutes}</span><small>{uiText('theme.orrery.stat_delay_unit')}</small></>}</dd></div>
   </dl>
   {(comms.blackout||!profile.blackouts.length)&&<p className="solar-link">{uiText(`theme.orrery.${comms.blackout?'blackout_now':'blackout_none'}`)}</p>}
   <label className="solar-scrub"><span>{uiText('theme.orrery.scrub_label')}</span><input aria-label={uiText('theme.orrery.scrub_label')} type="range" min="1" max={duration} value={day} onChange={e=>onDay(e.target.value)} style={{'--fill':`${g.progress*100}%`} as CSSProperties}/></label>
  </div>
  <figure className="solar-figure">
   <svg className="orrery" viewBox="0 0 600 600" role="img" aria-label={uiText('theme.orrery.aria',{pct,day})}>
    <defs>
     <radialGradient id={`${id}-sun`}><stop offset="0" stopColor="#fff6e0"/><stop offset=".35" stopColor="#ffc56b"/><stop offset=".7" stopColor="#f2843a" stopOpacity=".55"/><stop offset="1" stopColor="#f2843a" stopOpacity="0"/></radialGradient>
     <radialGradient id={`${id}-earth`} cx=".35" cy=".3"><stop offset="0" stopColor="#bfe6ff"/><stop offset=".45" stopColor="#3f8fcf"/><stop offset="1" stopColor="#123456"/></radialGradient>
     <radialGradient id={`${id}-mars`} cx=".35" cy=".3"><stop offset="0" stopColor="#ffc4a0"/><stop offset=".5" stopColor="#d0643a"/><stop offset="1" stopColor="#5a2414"/></radialGradient>
     <linearGradient id={`${id}-trail`} gradientUnits="userSpaceOnUse" x1={g.earth.x} y1={g.earth.y} x2={g.craft.x} y2={g.craft.y}><stop offset="0" stopColor="#f2a65a" stopOpacity=".15"/><stop offset="1" stopColor="#ffd9a8"/></linearGradient>
     <filter id={`${id}-glow`} x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="3"/></filter>
    </defs>
    <g className="orrery-ticks cosmos-motion">{ticks.map((t,i)=><line key={i} x1={f(t.p1.x)} y1={f(t.p1.y)} x2={f(t.p2.x)} y2={f(t.p2.y)} className={t.long?'tick-long':'tick'}/>)}</g>
    {Object.values(R).map(r=><circle key={r} cx={C} cy={C} r={r} className="orbit"/>)}
    <g className="belt">{belt.map((b,i)=><circle key={i} cx={f(b.x)} cy={f(b.y)} r={b.s} opacity={b.o}/>)}</g>
    <circle cx={C} cy={C} r="58" fill={`url(#${id}-sun)`} className="sun-corona cosmos-motion"/>
    <circle cx={C} cy={C} r="15" fill="#fff3d6"/>
    <path d={g.planned} className="transfer-planned"/>
    <path d={g.flown} className="transfer-flown" stroke={`url(#${id}-trail)`}/>
    <line x1={g.earth.x} y1={g.earth.y} x2={g.craft.x} y2={g.craft.y} className={comms.blackout?'comms-line down':'comms-line'}/>
    <circle cx={g.mercury.x} cy={g.mercury.y} r="3" fill="#a8a29a"/>
    <circle cx={g.venus.x} cy={g.venus.y} r="5" fill="#e8d3a8"/>
    <g className="body"><circle cx={g.earth.x} cy={g.earth.y} r="14" fill="#3f8fcf" opacity=".25" filter={`url(#${id}-glow)`}/><circle cx={g.earth.x} cy={g.earth.y} r="9" fill={`url(#${id}-earth)`}/></g>
    <g className="body"><circle cx={g.mars.x} cy={g.mars.y} r="13" fill="#d0643a" opacity=".22" filter={`url(#${id}-glow)`}/><circle cx={g.mars.x} cy={g.mars.y} r="7.5" fill={`url(#${id}-mars)`}/></g>
    <g className="waypoint"><circle cx={g.depart.x} cy={g.depart.y} r="3" /><circle cx={g.arrive.x} cy={g.arrive.y} r="3"/></g>
    <g className="craft"><circle cx={g.craft.x} cy={g.craft.y} r="16" className="craft-ping cosmos-motion"/><circle cx={g.craft.x} cy={g.craft.y} r="4.5" fill="#fff"/><circle cx={g.craft.x} cy={g.craft.y} r="9" fill="none" stroke="#f2a65a" strokeWidth="1.2"/></g>
   </svg>
   <figcaption>{uiText('theme.orrery.caption')}</figcaption>
  </figure>
 </section>;
}
