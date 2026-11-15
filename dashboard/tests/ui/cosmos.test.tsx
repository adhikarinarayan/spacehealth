// @vitest-environment jsdom
import React from 'react';
import { beforeEach,afterEach,describe,it,expect,vi } from 'vitest';
import { cleanup,render,screen,fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { App } from '../../src/App';
import { SolarHero,geometry } from '../../src/cosmos/SolarHero';
import { Spot } from '../../src/cosmos/Effects';
import { parseBundle } from '../../src/data/load';
import { uiText } from '../../src/data/ui';
import { commsState } from '../../src/theme/context';
const data=resolve(import.meta.dirname,'../../public/data');
function raw(missionCase:string){return Object.fromEntries(['mission','indicators','validation','cards'].map(name=>[name,JSON.parse(readFileSync(resolve(data,missionCase,name+'.json'),'utf8'))]));}
const showcase=raw('illustrative'),blind=raw('preselected'),bundle=parseBundle(showcase,'data','illustrative');
vi.mock('recharts',()=>({ResponsiveContainer:({children}:{children:React.ReactNode})=><div>{children}</div>,ComposedChart:()=> <div/>,Line:()=>null,ReferenceArea:()=>null,ReferenceLine:()=>null,CartesianGrid:()=>null,XAxis:()=>null,YAxis:()=>null,Tooltip:()=>null}));
beforeEach(()=>{localStorage.clear();delete document.documentElement.dataset.display;window.history.replaceState({},'','/');});
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
function matchMotion(reduced:boolean){vi.stubGlobal('matchMedia',()=>({matches:reduced,addEventListener:()=>{},removeEventListener:()=>{}}));}

describe('scoped solar-system presentation',()=>{
 it('uses the authored copy, illustrative delay and accessible diagram',()=>{
  render(<SolarHero mission={bundle.mission} day={41} onDay={()=>{}}/>);
  expect(screen.getByRole('heading',{name:uiText('theme.orrery.title')})).toBeTruthy();
  expect(screen.getByText(uiText('theme.orrery.lead',{minutes:commsState(bundle.mission.missionProfile,41).minutes}))).toBeTruthy();
  expect(screen.getByText(uiText('theme.orrery.stat_delay_unit'))).toBeTruthy();
  expect(screen.getByRole('img',{name:uiText('theme.orrery.aria',{pct:23,day:41})})).toBeTruthy();
  expect(screen.getByText(uiText('theme.orrery.caption'))).toBeTruthy();
  expect(screen.getByText(uiText('theme.orrery.blackout_none'))).toBeTruthy();
 });
 it('scrubs actual application day and diagram together',()=>{
  render(<App initialData={bundle}/>);
  fireEvent.change(screen.getByRole('slider',{name:uiText('theme.orrery.scrub_label')}),{target:{value:'90'}});
  expect((screen.getByRole('spinbutton',{name:'Mission day'}) as HTMLInputElement).value).toBe('90');
  expect(screen.getByRole('img',{name:uiText('theme.orrery.aria',{pct:50,day:90})})).toBeTruthy();
 });
 it('shows authored blackout copy when the mission profile says the link is down',()=>{
  const mission={...bundle.mission,missionProfile:{...bundle.mission.missionProfile,blackouts:[{startDay:40,endDay:45}]}};
  render(<SolarHero mission={mission} day={41} onDay={()=>{}}/>);
  expect(screen.getByText(uiText('theme.orrery.blackout_now'))).toBeTruthy();
  expect(screen.getByText(uiText('theme.orrery.stat_blackout'))).toBeTruthy();
  expect(screen.queryByText(uiText('theme.orrery.blackout_none'))).toBeNull();
 });
 it('keeps real-period planet motion and the craft arrival geometry',()=>{
  const start=geometry(1,1000);
  for(const [planet,period] of [['mercury',88],['venus',225],['earth',365.25],['mars',687]] as const){
   const end=geometry(1+period,1000);
   expect(end[planet].x).toBeCloseTo(start[planet].x,8);expect(end[planet].y).toBeCloseTo(start[planet].y,8);
  }
  expect(geometry(180,180).craft).toEqual(geometry(180,180).arrive);
 });
 it('clicks the light toggle both ways and reads the exact saved value on remount',async()=>{
  const user=userEvent.setup();let page=render(<App initialData={bundle}/>);
  expect(document.documentElement.dataset.display).toBe('dark');
  await user.click(screen.getByRole('button',{name:'Light display'}));
  expect(document.documentElement.dataset.display).toBe('light');expect(localStorage.getItem('spacehealth-display')).toBe('light');
  page.unmount();page=render(<App initialData={bundle}/>);
  expect(screen.getByRole('button',{name:'Light display'}).getAttribute('aria-pressed')).toBe('true');
  await user.click(screen.getByRole('button',{name:'Light display'}));
  expect(document.documentElement.dataset.display).toBe('dark');expect(localStorage.getItem('spacehealth-display')).toBe('dark');
  page.unmount();render(<App initialData={bundle}/>);
  expect(screen.getByRole('button',{name:'Light display'}).getAttribute('aria-pressed')).toBe('false');
 });
 for(const display of ['dark','light'])it(`clicks both mission choices with the orrery mounted in ${display}`,async()=>{
  localStorage.setItem('spacehealth-display',display);
  vi.stubGlobal('fetch',vi.fn(async(url:string)=>({ok:true,json:async()=>(url.includes('/preselected/')?blind:showcase)[url.split('/').pop()!.replace('.json','')]})));
  const user=userEvent.setup();render(<App initialData={bundle}/>);
  await user.click(screen.getByRole('combobox',{name:'Mission'}));
  await user.selectOptions(screen.getByRole('combobox',{name:'Mission'}),'preselected');
  await screen.findByText(uiText('panels.validation.preselected_case_note'));
  expect(window.location.search).toContain('case=preselected');
  expect((screen.getByRole('spinbutton',{name:'Mission day'}) as HTMLInputElement).value).toBe('43');
  await user.click(screen.getByRole('button',{name:'Light display'}));
  await user.selectOptions(screen.getByRole('combobox',{name:'Mission'}),'illustrative');
  await screen.findByText(uiText('panels.validation.illustrative_case_note'));
  expect(window.location.search).toContain('case=illustrative');
  expect((screen.getByRole('spinbutton',{name:'Mission day'}) as HTMLInputElement).value).toBe('41');
 });
 it('confines all glass rules to dark display and keeps decorative layers out of hit testing',()=>{
  const css=readFileSync(resolve(import.meta.dirname,'../../src/cosmos/cosmos.css'),'utf8').replace(/\/\*[\s\S]*?\*\//g,'');
  for(const m of css.matchAll(/([^{}]+)\{[^{}]*\}/g)){
   const selector=m[1].trim();if(selector==='to')continue;
   expect(selector.startsWith(':root[data-display="dark"]')||selector.startsWith(':root:not([data-display="light"])'),selector).toBe(true);
  }
  const layout=readFileSync(resolve(import.meta.dirname,'../../src/cosmos/solar.css'),'utf8');
  expect(layout).toContain('.header-controls{position:relative;z-index:3}');expect(layout).toContain('.masthead{z-index:2}');
  expect(layout).toContain('.solar-figure{margin:0;min-width:0;pointer-events:none}');
  expect(css).toContain('pointer-events:none');expect(css).toContain('animation:none');
 });
 it('moves the original CSS spotlight without blocking tile clicks and stays static for reduced motion',async()=>{
  matchMotion(false);const clicked=vi.fn();const page=render(<Spot><button onClick={clicked}>Tile</button></Spot>);
  const spot=page.container.firstElementChild as HTMLElement;
  vi.spyOn(spot,'getBoundingClientRect').mockReturnValue({left:10,top:20,width:200,height:100,right:210,bottom:120,x:10,y:20,toJSON:()=>{}});
  fireEvent(spot,new MouseEvent('pointermove',{bubbles:true,clientX:50,clientY:70}));
  expect(spot.style.getPropertyValue('--spot-x')).toBe('40px');expect(spot.style.getPropertyValue('--spot-y')).toBe('50px');
  await userEvent.click(screen.getByRole('button',{name:'Tile'}));expect(clicked).toHaveBeenCalledOnce();
  spot.style.removeProperty('--spot-x');spot.style.removeProperty('--spot-y');matchMotion(true);
  fireEvent(spot,new MouseEvent('pointermove',{bubbles:true,clientX:90,clientY:90}));
  expect(spot.style.getPropertyValue('--spot-x')).toBe('');expect(spot.style.getPropertyValue('--spot-y')).toBe('');
 });
});
