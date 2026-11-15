import type { ReactNode,PointerEvent } from 'react';

export function Spot({children}:{children:ReactNode}){
 function move(event:PointerEvent<HTMLDivElement>){
  if(window.matchMedia?.('(prefers-reduced-motion: reduce)').matches)return;
  const box=event.currentTarget.getBoundingClientRect();
  event.currentTarget.style.setProperty('--spot-x',`${event.clientX-box.left}px`);
  event.currentTarget.style.setProperty('--spot-y',`${event.clientY-box.top}px`);
 }
 return <div className="spot" onPointerMove={move} onPointerLeave={event=>{event.currentTarget.style.removeProperty('--spot-x');event.currentTarget.style.removeProperty('--spot-y');}}>{children}</div>;
}

export function Shine({children}:{children:ReactNode}){return <span className="headline-shine">{children}</span>;}
