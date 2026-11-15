// @vitest-environment jsdom
import React from 'react';
import { afterEach,beforeEach,describe,expect,it,vi } from 'vitest';
import { render,cleanup,screen,fireEvent,within } from '@testing-library/react';
import { readFileSync,readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { App } from '../../src/App';
import { SpaceBackdrop,makeStars,CrewBadge } from '../../src/theme/art';
import { MissionTheme } from '../../src/theme/MissionTheme';
import { missionProgress,commsState,stormActive } from '../../src/theme/context';
import { parseBundle } from '../../src/data/load';
import { uiText } from '../../src/data/ui';
const folder=resolve(import.meta.dirname,'../../public/demo');
const bundle=parseBundle(Object.fromEntries(['mission','indicators','validation','cards'].map(k=>[k,JSON.parse(readFileSync(resolve(folder,k+'.json'),'utf8'))])),'demo');
vi.mock('recharts',()=>({ResponsiveContainer:({children}:{children:React.ReactNode})=><div>{children}</div>,ComposedChart:()=> <div/>,Line:()=>null,ReferenceArea:()=>null,ReferenceLine:()=>null,CartesianGrid:()=>null,XAxis:()=>null,YAxis:()=>null,Tooltip:()=>null}));
beforeEach(()=>{window.history.replaceState({},'','/?data=demo');localStorage.clear();});
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
function luminance(hex:string){const raw=hex.replace('#','');const c=raw.length===3?[...raw].map(x=>x+x).join(''):raw;const rgb=[0,2,4].map(i=>parseInt(c.slice(i,i+2),16)/255).map(v=>v<=.04045?v/12.92:Math.pow((v+.055)/1.055,2.4));return .2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2];}
function contrast(a:string,b:string){const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
describe('original mission theme',()=>{
 it('meets AA for actual dark and light text/icon/control token pairs',()=>{
  expect(contrast('#000000','#ffffff')).toBe(21);expect(contrast('#ffffff','#ffffff')).toBe(1);
  const css=readFileSync(resolve(import.meta.dirname,'../../src/styles/tokens.css'),'utf8');
  const roots=[...css.matchAll(/:root(?:\[data-display="(?:dark|light)"\])?\{([^}]+)\}/g)];expect(roots).toHaveLength(2);
  for(const root of roots){
   const t=Object.fromEntries([...root[1].matchAll(/--([\w-]+):([^;}]+)/g)].map(x=>[x[1],x[2]]));
   for(const bg of ['bg','surface','surface-2']){
    for(const fg of ['text','muted','accent-ink','nominal','watch','act','unknown'])expect(contrast(t[fg],t[bg]),`${fg} on ${bg}`).toBeGreaterThanOrEqual(4.5);
    expect(contrast(t['control-line'],t[bg]),`control/icon boundary on ${bg}`).toBeGreaterThanOrEqual(3);
   }
   expect(contrast(t['on-accent'],t['button-accent']),'primary button').toBeGreaterThanOrEqual(4.5);
   expect(contrast(t.accent,t.surface),'wordmark on header').toBeGreaterThanOrEqual(4.5);
   expect(contrast(t.accent,t['surface-2']),'accent decoration / large metric').toBeGreaterThanOrEqual(3);
  }
 });
 it('keeps navigation selection and mission values live through the redesign',()=>{
  render(<App initialData={bundle}/>);
  expect(screen.getByRole('button',{name:'Today',exact:true}).getAttribute('aria-current')).toBe('page');
  fireEvent.click(screen.getByRole('button',{name:'Crew',exact:true}));
  expect(screen.getByRole('button',{name:'Crew',exact:true}).getAttribute('aria-current')).toBe('page');
  expect(screen.getByRole('button',{name:'Today',exact:true}).getAttribute('aria-current')).toBeNull();
  fireEvent.change(screen.getByRole('spinbutton',{name:'Mission day'}),{target:{value:'90'}});
  expect(screen.getByTestId('trajectory-marker').style.left).toBe('50%');
  expect(within(screen.getByRole('region',{name:'Mission status'})).getByText('90 / 180')).toBeTruthy();
  expect(screen.getByRole('link',{name:/SPACEHEALTH/}).getAttribute('href')).toBe('?data=demo');
 });
 it('generates exactly 150 deterministic decorative stars',()=>{
  expect(makeStars()).toEqual(makeStars());expect(makeStars(1)).not.toEqual(makeStars(2));
  const page=render(<SpaceBackdrop/>);expect(page.container.querySelectorAll('circle')).toHaveLength(150);
  expect(makeStars().every(s=>s.opacity<=.3&&s.x>=0&&s.x<1000&&s.y>=0&&s.y<1000)).toBe(true);
 });
 it('defaults to dark independently of OS preference',()=>{
  vi.stubGlobal('matchMedia',vi.fn(()=>({matches:true,addEventListener:vi.fn(),removeEventListener:vi.fn()})));
  const page=render(<App initialData={bundle}/>);expect(page.container.querySelector('.space-backdrop svg')).toBeTruthy();
  expect(document.documentElement.dataset.display).toBe('dark');
  const css=readFileSync(resolve(import.meta.dirname,'../../src/theme/theme.css'),'utf8');
  expect(css).not.toContain('prefers-color-scheme');expect(css).not.toContain('display:none');
  const control=readFileSync(resolve(import.meta.dirname,'../../src/styles/mission-control.css'),'utf8');expect(control).toContain('background:var(--surface)');expect(control).toContain('grid-template-columns:1fr');
 });
 it('renders a rounded original helmet instead of the old spacecraft',()=>{
  render(<MissionTheme mission={bundle.mission} day={72}/>);
  const marker=screen.getByTestId('trajectory-marker');expect(marker.querySelector('[data-art="helmet"][aria-hidden="true"]')).toBeTruthy();
  expect(marker.innerHTML).not.toContain('m16 3 5 11');expect(marker.querySelector('linearGradient')).toBeTruthy();expect(marker.querySelectorAll('rect[rx="3"]')).toHaveLength(2);
  expect(screen.getByText(uiText('theme.trajectory_label',{day:72,duration:180}))).toBeTruthy();
 });
 it('switches and remembers light display',()=>{
  const page=render(<App initialData={bundle}/>);const button=screen.getByRole('button',{name:'Light display'});
  expect(button.getAttribute('aria-pressed')).toBe('false');fireEvent.click(button);
  expect(document.documentElement.dataset.display).toBe('light');expect(localStorage.getItem('spacehealth-display')).toBe('light');
  page.unmount();render(<App initialData={bundle}/>);expect(screen.getByRole('button',{name:'Light display'}).getAttribute('aria-pressed')).toBe('true');
 });
 it('works when storage is blocked',()=>{
  const get=vi.spyOn(Storage.prototype,'getItem').mockImplementation(()=>{throw new Error('blocked');});
  const set=vi.spyOn(Storage.prototype,'setItem').mockImplementation(()=>{throw new Error('blocked');});
  render(<App initialData={bundle}/>);fireEvent.click(screen.getByRole('button',{name:'Light display'}));expect(document.documentElement.dataset.display).toBe('light');get.mockRestore();set.mockRestore();
 });
 it('disables the sole animation class when reduced motion is requested',()=>{
  vi.stubGlobal('matchMedia',vi.fn(()=>({matches:true,addEventListener:vi.fn(),removeEventListener:vi.fn()})));
  const page=render(<MissionTheme mission={bundle.mission} day={42}/>);
  expect(page.container.querySelector('.theme-motion')).toBeNull();
  const css=readFileSync(resolve(import.meta.dirname,'../../src/theme/theme.css'),'utf8');
  expect([...css.matchAll(/@keyframes /g)]).toHaveLength(1);
  expect(css).toContain('@media(prefers-reduced-motion:reduce){.theme-motion{animation:none!important;transition:none!important}}');
 });
 it('positions the trajectory at day/duration and updates after day changes',()=>{
  expect(missionProgress(72,180)).toBe(.4);
  const page=render(<MissionTheme mission={bundle.mission} day={72}/>);
  expect(screen.getByTestId('trajectory-marker').style.left).toBe('40%');
  page.rerender(<MissionTheme mission={bundle.mission} day={180}/>);
  expect(screen.getByTestId('trajectory-marker').style.left).toBe('100%');
 });
 it('interpolates comms range endpoints and shows blackout copy inside the window',()=>{
  const p=bundle.mission.missionProfile;
  expect(commsState(p,1).minutes).toBe(p.comms_one_way_delay_min.min);
  expect(commsState(p,180).minutes).toBe(p.comms_one_way_delay_min.max);
  const page=render(<MissionTheme mission={bundle.mission} day={155}/>);
  expect(screen.getByText(uiText('theme.comms_blackout'))).toBeTruthy();expect(page.container.querySelector('.link-down')).toBeTruthy();
 });
 it('shows storm mode on a radiation act day, never on a quiet day, without hiding its card',()=>{
  window.history.replaceState({},'','/?crew=C2&day=72');const page=render(<App initialData={bundle}/>);
  const band=screen.getByRole('alert');expect(within(band).getByText(uiText('theme.storm_banner_title'))).toBeTruthy();
  expect(within(band).getByText(uiText('theme.storm_banner_body'))).toBeTruthy();expect(within(band).getByText(uiText('theme.storm_banner_note'))).toBeTruthy();
  expect(screen.getByRole('button',{name:'Radiation detail'}).textContent).toContain('Act');
  expect(screen.getByRole('button',{name:/Solar particle event warning/})).toBeTruthy();
  page.unmount();window.history.replaceState({},'','/?crew=C2&day=42');render(<App initialData={bundle}/>);expect(screen.queryByRole('alert')).toBeNull();
 });
 it('also recognizes an explicit active warning evidence field',()=>{
  const source=bundle.indicators.indicators.find(i=>i.moduleId==='radiation')!;
  expect(stormActive([{...source,status:'nominal',evidence:[{signalId:'spe_warning',value:true}]}],source.crewId,source.missionDay)).toBe(true);
 });
 it('renders original geometric crew badges with distinct shapes',()=>{
  const page=render(<div>{['C1','C2','C3','C4'].map(c=><CrewBadge key={c} crewId={c}/>)}</div>);
  expect(new Set([...page.container.querySelectorAll('g')].map(g=>g.innerHTML)).size).toBe(4);
  expect([...page.container.querySelectorAll('text')].map(t=>t.textContent)).toEqual(['C1','C2','C3','C4']);
 });
 it('uses selected event time for the ship clock and returns to daily context on day change',()=>{
  window.history.replaceState({},'','/?crew=C2&day=72&view=replay');const page=render(<App initialData={bundle}/>);
  fireEvent.change(screen.getByRole('combobox',{name:'Ship time'}),{target:{value:'6'}});
  expect(within(page.container.querySelector('.mission-theme') as HTMLElement).getByText(uiText('theme.ship_clock',{day:72,time:'06:00'}))).toBeTruthy();
  fireEvent.change(screen.getByRole('spinbutton',{name:'Mission day'}),{target:{value:'73'}});
  expect(within(page.container.querySelector('.mission-theme') as HTMLElement).getByText(uiText('theme.ship_clock_daily',{day:73}))).toBeTruthy();
 });
 it('reads all new theme strings from the copy keys and places notes in help',()=>{
  const keys=['trajectory_label','trajectory_note','comms_link','comms_blackout','storm_banner_title','storm_banner_body','storm_banner_note','ship_clock','ship_clock_daily','crew_badge_note'];
  for(const key of keys)expect(uiText(`theme.${key}`,{day:42,duration:180,time:'06:00',minutes:5})).not.toBe(`theme.${key}`);
  render(<App initialData={bundle}/>);expect(screen.getByText(uiText('theme.trajectory_note'))).toBeTruthy();
  fireEvent.click(screen.getByRole('button',{name:'Crew',exact:true}));expect(screen.getByText(uiText('theme.crew_badge_note'))).toBeTruthy();
 });
 it('uses inline art only and has no runtime asset URLs in theme source',()=>{
  const dir=resolve(import.meta.dirname,'../../src/theme');
  for(const name of readdirSync(dir))expect(readFileSync(resolve(dir,name),'utf8')).not.toMatch(/<img|https?:\/\/|@import|\bfetch\(/i);
  const page=render(<App initialData={bundle}/>);expect(page.container.querySelector('img')).toBeNull();
 });
});
