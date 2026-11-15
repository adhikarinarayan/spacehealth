import type { Mission } from '../data/load';
import { trendData } from '../data/presentation';
export function Sparkline({mission,crewId,day,signalId}:{mission:Mission;crewId:string;day:number;signalId:string}){
 const data=trendData(mission,crewId,day,signalId),points=data.points.slice(-7);
 const values=points.map(p=>p.value).filter((v):v is number=>v!==null);
 if(data.center!==null)values.push(data.center);
 const min=values.length?Math.min(...values):0,max=values.length?Math.max(...values):1,range=max-min||1;
 const x=(i:number)=>8+i*(224/Math.max(1,points.length-1));const y=(v:number)=>56-(v-min)/range*44;
 let path='',previous=false;
 for(let i=0;i<points.length;i++){const p=points[i];if(p.value===null){previous=false;continue;}path+=`${previous?'L':'M'}${x(i)},${y(p.value)} `;previous=true;}
 return <svg className="sparkline" viewBox="0 0 240 68" role="img" aria-label={`${signalId} · 7 days`} preserveAspectRatio="none">{data.center!==null&&<line x1="8" x2="232" y1={y(data.center)} y2={y(data.center)} stroke="var(--muted)" strokeDasharray="3 4"/>}<path d={path} fill="none" stroke="var(--chart)" strokeWidth="2"/>{points.map((p,i)=>p.value===null?null:<circle key={p.day} cx={x(i)} cy={y(p.value)} r="2" fill="var(--chart)"/>)}</svg>;
}
