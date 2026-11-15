// @vitest-environment jsdom
import React from 'react';
import { afterEach,beforeEach,describe,expect,it,vi } from 'vitest';
import { act,cleanup,render,screen,fireEvent,waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { readFileSync,readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { App } from '../../src/App';
import { ActionCard } from '../../src/components/ActionCard';
import { parseBundle,loadData } from '../../src/data/load';
import { selectCards,trendData } from '../../src/data/presentation';
import { footer } from '../../src/copy';
import { uiText } from '../../src/data/ui';
import { formatRecordedTime } from '../../src/data/actions';
import type { Indicator } from '../../src/contracts';
const demo=resolve(import.meta.dirname,'../../public/demo');
const raw=Object.fromEntries(['mission','indicators','validation','cards'].map(name=>[name,JSON.parse(readFileSync(resolve(demo,`${name}.json`),'utf8'))]));
const bundle=parseBundle(raw,'demo');
vi.mock('recharts',()=>({ResponsiveContainer:({children}:{children:React.ReactNode})=><div>{children}</div>,ComposedChart:()=> <div data-testid="chart"/>,Line:()=>null,ReferenceArea:()=>null,ReferenceLine:()=>null,CartesianGrid:()=>null,XAxis:()=>null,YAxis:()=>null,Tooltip:()=>null}));
beforeEach(()=>{window.history.replaceState({},'','/?data=demo&day=42');localStorage.clear();});
afterEach(()=>{cleanup();vi.unstubAllGlobals();vi.restoreAllMocks();});
describe('dashboard v0',()=>{
 it('validates all mock files and uses sleep-debt on C3 days 99–101',()=>{
  expect(bundle.mission.readings).toHaveLength(776);
  for(const d of [99,100,101])expect(bundle.indicators.indicators.find(i=>i.crewId==='C3'&&i.missionDay===d&&i.moduleId==='sleep_alertness')?.cardId).toBe('sleep-debt');
 });
 it('never labels an unknown tile Nominal',()=>{
  window.history.replaceState({},'','/?crew=C4&day=122');render(<App initialData={bundle}/>);
  const tile=screen.getByRole('button',{name:'Physiological change detail'});
  expect(tile.textContent).toContain('No reliable data');expect(tile.textContent).not.toContain('Nominal');
 });
 it('keeps missing chart values as gaps',()=>{
  expect(trendData(bundle.mission,'C4',124,'rhr_bpm').points.filter(p=>p.day>=120).map(p=>p.value)).toEqual([null,null,null,null,null]);
 });
 it('caps five routine cards but always puts critical cards first',()=>{
  const source=bundle.indicators.indicators.find(i=>i.cardId==='physiological-change')!;
  const routine=Array.from({length:5},(_,i)=>({...source,crewId:`fixture-${i}`})) as Indicator[];
  const radiation={...source,moduleId:'radiation',status:'act',cardId:'radiation-spe-procedure'} as Indicator;
  const symptom={...source,status:'act',cardId:'symptom-escalation'} as Indicator;
  expect(selectCards([...routine,radiation])).toEqual([radiation,...routine.slice(0,3)]);
  expect(selectCards([...routine,symptom,radiation])).toEqual([radiation,symptom,...routine.slice(0,3)]);
 });
 it('renders medical card text exactly from cards.json',()=>{
  const card=bundle.cards.cards.find(c=>c.id==='sleep-debt')!;render(<ActionCard card={card} onAction={()=>{}}/>);
  for(const text of [card.heading,card.why,card.uncertainty,...card.do_now,card.recheck,card.onboard_escalation,card.ground_escalation])expect(screen.getByText(text)).toBeTruthy();
 });
 it('queues ground messages locally and preserves records across remount',async()=>{
  const user=userEvent.setup();const page=render(<App initialData={bundle}/>);
  await user.click(screen.getByRole('button',{name:'Physiological change detail'}));await user.click(await screen.findByRole('button',{name:'Queue message to ground'}));
  expect(screen.getByRole('status').textContent).toContain('queued');expect(screen.getByRole('status').textContent).not.toMatch(/sent|delivered/i);
  expect(JSON.parse(localStorage.getItem('spacehealth-ui-actions-v1')!)[0].action).toBe('Queue message to ground');
  page.unmount();render(<App initialData={bundle}/>);await user.click(screen.getByRole('button',{name:'Log',exact:true}));expect(screen.getByText(/queued — reply/)).toBeTruthy();
 });
 it('shows radiation Act on replay day 72',async()=>{
  const user=userEvent.setup();render(<App initialData={bundle}/>);await user.click(screen.getByRole('button',{name:'Replay + Validation'}));
  fireEvent.change(screen.getByRole('slider',{name:'Replay day'}),{target:{value:'72'}});
  expect(screen.getByRole('button',{name:'Radiation detail'}).textContent).toContain('Act');
  expect(screen.getByRole('heading',{name:'Validation (simulated)'})).toBeTruthy();
 });
 it('plays at the chosen speed and pauses without advancing',()=>{
  vi.useFakeTimers();
  try{
   render(<App initialData={bundle}/>);
   fireEvent.click(screen.getByRole('button',{name:'Replay + Validation'}));
   fireEvent.change(screen.getByRole('combobox',{name:'Replay speed'}),{target:{value:'20'}});
   fireEvent.click(screen.getByRole('button',{name:'Play',exact:true}));
   act(()=>{vi.advanceTimersByTime(100);});
   expect((screen.getByRole('spinbutton',{name:'Mission day'}) as HTMLInputElement).value).toBe('44');
   fireEvent.click(screen.getByRole('button',{name:'Pause'}));act(()=>{vi.advanceTimersByTime(500);});
   expect((screen.getByRole('spinbutton',{name:'Mission day'}) as HTMLInputElement).value).toBe('44');
  }finally{vi.useRealTimers();}
 });
 it('shows truth markers only in Replay',async()=>{
  const user=userEvent.setup();render(<App initialData={bundle}/>);expect(screen.queryByText('Replay-only scenario markers')).toBeNull();
  await user.click(screen.getByRole('button',{name:'Replay + Validation'}));expect(screen.getByText('Replay-only scenario markers')).toBeTruthy();
  await user.click(screen.getByRole('button',{name:'Today'}));expect(screen.queryByText('Replay-only scenario markers')).toBeNull();
 });
 it('records in memory when localStorage is unavailable',async()=>{
  const user=userEvent.setup();vi.spyOn(Storage.prototype,'setItem').mockImplementation(()=>{throw new Error('blocked');});render(<App initialData={bundle}/>);
  await user.click(screen.getByRole('button',{name:'Physiological change detail'}));await user.click(await screen.findByRole('button',{name:'Done',exact:true}));
  const notice=screen.getByRole('status');
  expect(notice.querySelector('strong')?.textContent).toBe('Done');
  for(const part of uiText('actions.recorded',{time:'__TIME__'}).split('__TIME__'))expect(notice.textContent).toContain(part);
  expect(notice.textContent).not.toContain('{time}');
 });
 it('substitutes the persisted action time/day and keeps its label separate',async()=>{
  const user=userEvent.setup();render(<App initialData={bundle}/>);
  await user.click(screen.getByRole('button',{name:'Physiological change detail'}));
  await user.click(await screen.findByRole('button',{name:'Done',exact:true}));
  const entry=JSON.parse(localStorage.getItem('spacehealth-ui-actions-v1')!)[0];
  const notice=screen.getByRole('status');
  expect(notice.querySelector('strong')?.textContent).toBe(entry.action);
  expect(notice.querySelector('span')?.textContent).toBe(uiText('actions.recorded',{time:formatRecordedTime(entry)}));
  expect(notice.textContent).not.toMatch(/\{time\}|actions\.recorded/);
  fireEvent.change(screen.getByRole('spinbutton',{name:'Mission day'}),{target:{value:'43'}});
  expect(notice.textContent).toContain('(day 42)');
 });
 it('formats a recorded instant as local zero-padded hours and minutes',()=>{
  const local=new Date(2026,10,14,4,2,59);
  expect(formatRecordedTime({time:local.toISOString(),day:42})).toBe('04:02 (day 42)');
 });
 it('rejects malformed files without rendering partial indicators',async()=>{
  vi.stubGlobal('fetch',vi.fn(async (url:string)=>({ok:true,json:async()=>url.includes('cards.json')?{invalid:true}:raw[url.split('/').pop()!.replace('.json','')]})));render(<App/>);
  await waitFor(()=>expect(screen.getByRole('heading',{name:'Mission data could not be loaded'})).toBeTruthy());expect(screen.queryByRole('button',{name:'Physiological change detail'})).toBeNull();
 });
 it('rejects mixed model results before rendering',()=>{
  const mixed=structuredClone(raw) as Record<string,any>;
  mixed.validation.modelId='another-model';
  expect(()=>parseBundle(mixed,'data')).toThrow('Mismatched model report');
 });
 it('loads the explicit data path without silently switching to mock',async()=>{
  const release=Object.fromEntries(['mission','indicators','validation','cards'].map(name=>[name,JSON.parse(readFileSync(resolve(import.meta.dirname,`../../public/data/illustrative/${name}.json`),'utf8'))]));
  const mocked=vi.fn(async (url:string)=>({ok:true,json:async()=>release[url.split('/').pop()!.replace('.json','')]}));vi.stubGlobal('fetch',mocked);
  const loaded=await loadData('?data=data');expect(loaded.source).toBe('data');expect(loaded.mission.seed).toBe(1002);expect(mocked.mock.calls.every(call=>call[0].startsWith('/data/illustrative/'))).toBe(true);
 });
 it('keeps authored medical copy out of components and includes the required footer',()=>{
  const dir=resolve(import.meta.dirname,'../../src/components');for(const name of readdirSync(dir).filter(n=>n.endsWith('.tsx')))expect(readFileSync(resolve(dir,name),'utf8')).not.toMatch(/infection|diagnos/i);
  render(<App initialData={bundle}/>);expect(screen.getByText(footer)).toBeTruthy();
 });
});
