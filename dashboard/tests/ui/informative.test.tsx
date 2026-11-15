// @vitest-environment jsdom
import React from 'react';
import { afterEach,beforeEach,describe,expect,it,vi } from 'vitest';
import { cleanup,render,screen,within,fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { readFileSync,readdirSync } from 'node:fs';
import { resolve } from 'node:path';
import { App } from '../../src/App';
import { PanelIntro } from '../../src/components/PanelIntro';
import { MissionHeader } from '../../src/components/MissionHeader';
import { RadiationBudget } from '../../src/components/RadiationBudget';
import { Sparkline } from '../../src/components/Sparkline';
import { parseBundle } from '../../src/data/load';
import { radiationBudget,timelineEntries } from '../../src/data/mission';
import { uiText,panelKeys } from '../../src/data/ui';
import type { Indicator } from '../../src/contracts';
import type { ActionEntry } from '../../src/components/ActionCard';
const folder=resolve(import.meta.dirname,'../../public/demo');
const raw=Object.fromEntries(['mission','indicators','validation','cards'].map(k=>[k,JSON.parse(readFileSync(resolve(folder,k+'.json'),'utf8'))]));
const bundle=parseBundle(raw,'demo');
vi.mock('recharts',()=>({ResponsiveContainer:({children}:{children:React.ReactNode})=><div>{children}</div>,ComposedChart:()=> <div/>,Line:()=>null,ReferenceArea:()=>null,ReferenceLine:()=>null,CartesianGrid:()=>null,XAxis:()=>null,YAxis:()=>null,Tooltip:()=>null}));
beforeEach(()=>{window.history.replaceState({},'','/?data=demo');localStorage.clear();});
afterEach(()=>{cleanup();vi.restoreAllMocks();});
function tinyMission(){const reading=bundle.mission.readings[0];return {...bundle.mission,crew:[{...bundle.mission.crew[0],prior_career_dose_msv:null}],missionProfile:{...bundle.mission.missionProfile,gcr_background_msv_day:2},readings:[{...reading,crewId:'C1',missionDay:1,daily_dose_msv:2,dose_coverage:1},{...reading,crewId:'C1',missionDay:2,daily_dose_msv:3,dose_coverage:1}]};}
describe('informative dashboard',()=>{
 it('covers every research panel key with title and explanatory source copy',()=>{
  expect(panelKeys).toEqual(['mission_header','radiation_budget','today_tiles','attention_cards','detail','crew_grid','timeline','replay','validation']);
  for(const key of panelKeys){const page=render(<PanelIntro panel={key} values={{day:42,duration:180,rate:1.84}}/>);expect(within(page.container).getByRole('heading',{name:uiText(`panels.${key}.title`)})).toBeTruthy();expect(within(page.container).getByText(uiText(`panels.${key}.what_for`))).toBeTruthy();page.unmount();}
 });
 it('places the panel intros in all corresponding views and Detail',async()=>{
  const user=userEvent.setup();const page=render(<App initialData={bundle}/>);
  const seen=new Set<string>();const collect=()=>page.container.querySelectorAll('[data-panel]').forEach(node=>seen.add(node.getAttribute('data-panel')!));
  collect();await user.click(screen.getByRole('button',{name:'Physiological change detail'}));await screen.findByRole('button',{name:'Close detail'});collect();
  for(const name of ['Crew','Log','Replay + Validation']){await user.click(screen.getByRole('button',{name,exact:true}));collect();}
  expect([...seen].sort()).toEqual([...panelKeys].sort());
 });
 it('shows help on first visit and remembers explicit collapsed preference',async()=>{
  const user=userEvent.setup();const page=render(<PanelIntro panel="detail"/>);
  const toggle=screen.getByRole('button',{name:'How to read this'});expect(toggle.getAttribute('aria-expanded')).toBe('true');
  await user.click(toggle);expect(toggle.getAttribute('aria-expanded')).toBe('false');page.unmount();
  render(<PanelIntro panel="detail"/>);expect(screen.getByRole('button',{name:'How to read this'}).getAttribute('aria-expanded')).toBe('false');
 });
 it('keeps help usable if localStorage is blocked',async()=>{
  vi.spyOn(Storage.prototype,'getItem').mockImplementation(()=>{throw new Error('blocked');});vi.spyOn(Storage.prototype,'setItem').mockImplementation(()=>{throw new Error('blocked');});
  const user=userEvent.setup();render(<PanelIntro panel="detail"/>);await user.click(screen.getByRole('button',{name:'How to read this'}));expect(screen.getByRole('button').getAttribute('aria-expanded')).toBe('false');
 });
 it('computes mission projection without inventing an unknown career dose',()=>{
  const result=radiationBudget(tinyMission(),'C1',2);expect(result).toEqual({missionDose:5,projectedMission:361,prior:null,careerDose:null,projectedCareer:null,partial:false});
  const mission=tinyMission();mission.crew[0].prior_career_dose_msv=120 as never;
  expect(radiationBudget(mission,'C1',2).projectedCareer).toBe(481);
 });
 it('renders unknown prior as unknown copy, never zero prior',()=>{
  render(<RadiationBudget mission={tinyMission()} crewId="C1" day={2}/>);
  expect(screen.getByText(uiText('panels.radiation_budget.career_unknown'))).toBeTruthy();
  const field=screen.getByText('Prior career').parentElement!;expect(field.textContent).toContain('Unknown');expect(field.textContent).not.toContain('0');
 });
 it('marks partial coverage and skips missing dose rather than imputing it',()=>{
  const mission=tinyMission();mission.readings[0].daily_dose_msv=null as never;mission.readings[1].dose_coverage=.5;
  expect(radiationBudget(mission,'C1',2).missionDose).toBe(3);expect(radiationBudget(mission,'C1',2).partial).toBe(true);
  render(<RadiationBudget mission={mission} crewId="C1" day={2}/>);expect(screen.getByText('Mission so far · partial')).toBeTruthy();
 });
 it('reads profile duration, illustrative comms and simulated blackout state',()=>{
  render(<MissionHeader mission={bundle.mission} day={155}/>);expect(screen.getByText('155 / 180')).toBeTruthy();expect(screen.getByText('(illustrative)')).toBeTruthy();expect(screen.getByText(uiText('panels.mission_header.blackout_active'))).toBeTruthy();
  cleanup();render(<MissionHeader mission={{...bundle.mission,missionProfile:{...bundle.mission.missionProfile,blackouts:[]}}} day={42}/>);expect(screen.getByText('none simulated')).toBeTruthy();
 });
 it('has unknown crew cells and opens the selected crew detail with the keyboard',async()=>{
  const user=userEvent.setup();window.history.replaceState({},'','/?view=crew&day=122');render(<App initialData={bundle}/>);
  const cell=screen.getByRole('button',{name:'C4 Physiological change detail'});expect(cell.textContent).toContain('No reliable data');expect(cell.textContent).not.toContain('Nominal');
  cell.focus();await user.keyboard('{Enter}');await screen.findByRole('button',{name:'Close detail'});
  expect((screen.getByRole('combobox',{name:'Crew'}) as HTMLSelectElement).value).toBe('C4');expect(screen.getByRole('region',{name:'Module detail'}).textContent).toContain('No reliable data');
 });
 it('calculates transitions once per actual state change and labels ground actions queued',()=>{
  const base=bundle.indicators.indicators[0];
  const rows=[{...base,crewId:'C2',moduleId:'physiological_change',missionDay:1,status:'nominal'},{...base,crewId:'C2',moduleId:'physiological_change',missionDay:2,status:'watch'},{...base,crewId:'C2',moduleId:'physiological_change',missionDay:3,status:'watch'},{...base,crewId:'C2',moduleId:'physiological_change',missionDay:4,status:'nominal'}] as Indicator[];
  const action:ActionEntry={id:'one',crewId:'C2',day:3,cardId:'mock',action:'Queue message to ground',time:'2026-11-14T00:00:00Z'};
  const entries=timelineEntries(rows,{...bundle.mission,radiationEvents:[]},[action]);
  expect(entries.map(e=>e.day)).toEqual([4,3,2]);expect(entries[2].label).toContain('Nominal → Watch');expect(entries[0].label).toContain('Watch → Nominal');expect(entries[1].label).toContain('queued');expect(entries[1].label).not.toMatch(/sent|delivered/i);
 });
 it('filters log by module/all-crew and jumps to a transition day',async()=>{
  const user=userEvent.setup();window.history.replaceState({},'','/?view=log&crew=C2');render(<App initialData={bundle}/>);
  fireEvent.change(screen.getByRole('combobox',{name:'Log module'}),{target:{value:'physiological_change'}});
  const row=screen.getByRole('button',{name:/Day 40 · C2 · Physiological change: Nominal → Watch/});await user.click(row);
  expect((screen.getByRole('spinbutton',{name:'Mission day'}) as HTMLInputElement).value).toBe('40');expect(screen.getByRole('button',{name:'Physiological change detail'})).toBeTruthy();
 });
 it('keeps sparkline missing values as separate paths rather than zero points',()=>{
  const page=render(<Sparkline mission={bundle.mission} crewId="C4" day={124} signalId="rhr_bpm"/>);
  expect(page.container.querySelectorAll('circle')).toHaveLength(2);
 });
 it('uses the supplied help copy, retains unknown-key fallback and excludes medical prose from components',()=>{
  render(<PanelIntro panel="attention_cards"/>);
  expect(screen.getByText(uiText('panels.attention_cards.how_to_read'))).toBeTruthy();
  expect(uiText('panels.fake_panel.fake_key')).toBe('panels.fake_panel.fake_key');
  for(const key of ['actions.recorded','panels.mission_header.blackout_active','panels.mission_header.blackout_inactive','panels.attention_cards.how_to_read','panels.attention_cards.empty','panels.detail.chart_legend','panels.detail.no_action','panels.timeline.empty','panels.validation.mock_note','states.load_error','states.indicator_unavailable'])expect(uiText(key,{time:'04:02 (day 42)'})).not.toBe(key);
  const folder=resolve(import.meta.dirname,'../../src/components');for(const name of readdirSync(folder).filter(n=>n.endsWith('.tsx')))expect(readFileSync(resolve(folder,name),'utf8')).not.toMatch(/infection|diagnos/i);
 });
});
