// @vitest-environment jsdom
import React from 'react';
import { beforeEach,afterEach,describe,it,expect,vi } from 'vitest';
import { render,screen,cleanup,fireEvent,within,waitFor } from '@testing-library/react';
import { readFileSync,writeFileSync,mkdtempSync,copyFileSync,mkdirSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve } from 'node:path';
import { App } from '../../src/App';
import { parseBundle,loadData,firstWatchDay } from '../../src/data/load';
import { uiText,uiList } from '../../src/data/ui';
import { syncRelease,syncCases } from '../../scripts/sync-release';
const root=resolve(import.meta.dirname,'../../public/data');
const dataDir=resolve(root,'illustrative');
const raw=Object.fromEntries(['mission','indicators','validation','cards'].map(k=>[k,JSON.parse(readFileSync(resolve(dataDir,k+'.json'),'utf8'))]));
const bundle=parseBundle(raw,'data','illustrative');
const preselectedRaw=Object.fromEntries(['mission','indicators','validation','cards'].map(k=>[k,JSON.parse(readFileSync(resolve(root,'preselected',k+'.json'),'utf8'))]));
const preselected=parseBundle(preselectedRaw,'data','preselected');
function mockCases(){const fetcher=vi.fn(async(url:string)=>({ok:true,json:async()=>(url.includes('/preselected/')?preselectedRaw:raw)[url.split('/').pop()!.replace('.json','')]}));vi.stubGlobal('fetch',fetcher);return fetcher;}
vi.mock('recharts',()=>({ResponsiveContainer:({children}:{children:React.ReactNode})=><div>{children}</div>,ComposedChart:()=> <div/>,Line:()=>null,ReferenceArea:()=>null,ReferenceLine:()=>null,CartesianGrid:()=>null,XAxis:()=>null,YAxis:()=>null,Tooltip:()=>null}));
beforeEach(()=>{window.history.replaceState({},'','/');localStorage.clear();});
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
describe('frozen release integration',()=>{
 it('defaults to real simulated-release data and C2/day41',async()=>{
  const fetcher=vi.fn(async(url:string)=>({ok:true,json:async()=>raw[url.split('/').pop()!.replace('.json','')]}));vi.stubGlobal('fetch',fetcher);
  expect((await loadData('')).source).toBe('data');expect(fetcher.mock.calls.every(x=>x[0].startsWith('/data/illustrative/'))).toBe(true);
  render(<App initialData={bundle}/>);expect((screen.getByRole('spinbutton',{name:'Mission day'}) as HTMLInputElement).value).toBe('41');expect((screen.getByRole('combobox',{name:'Crew'}) as HTMLSelectElement).value).toBe('C2');
  expect(screen.getByText(uiText('panels.validation.illustrative_case_note'))).toBeTruthy();expect(screen.queryByText(/MOCK DATA for UI development/)).toBeNull();
 });
 it('loads the pre-selected case explicitly and derives different default days',async()=>{
  mockCases();expect((await loadData('?case=preselected')).mission.seed).toBe(1000);
  expect(firstWatchDay(bundle)).toBe(41);expect(firstWatchDay(preselected)).toBe(43);
  const changed={...bundle,indicators:{...bundle.indicators,indicators:bundle.indicators.indicators.map(i=>i.crewId==='C2'&&i.moduleId==='physiological_change'?{...i,status:i.missionDay===55?'watch' as const:'nominal' as const}:i)}};
  expect(firstWatchDay(changed)).toBe(55);
  await expect(loadData('?case=unknown')).rejects.toThrow('Unknown mission case');
  expect(()=>parseBundle(raw,'data','preselected')).toThrow('Mismatched mission case seed');
 });
 it('switches the live case, disclosure, first-watch day, URL and validation rows together',async()=>{
  mockCases();window.history.replaceState({},'','/?view=replay');render(<App initialData={bundle}/>);
  expect(screen.getByRole('combobox',{name:'Mission'}).getAttribute('disabled')).toBeNull();
  fireEvent.change(screen.getByRole('combobox',{name:'Mission'}),{target:{value:'preselected'}});
  await screen.findByText(uiText('panels.validation.preselected_case_note'));
  expect((screen.getByRole('spinbutton',{name:'Mission day'}) as HTMLInputElement).value).toBe('43');
  expect(window.location.search).toContain('case=preselected');expect(window.location.search).not.toContain('day=');
  const table=screen.getByRole('table');const s4=within(table).getByRole('rowheader',{name:'S4 / C3'}).closest('tr')!;
  expect(within(s4).getByText('Fail')).toBeTruthy();expect(screen.getByText(uiText('panels.validation.holdout_title'))).toBeTruthy();
  fireEvent.change(screen.getByRole('combobox',{name:'Mission'}),{target:{value:'illustrative'}});
  await screen.findByText(uiText('panels.validation.illustrative_case_note'));
  expect((screen.getByRole('spinbutton',{name:'Mission day'}) as HTMLInputElement).value).toBe('41');
  expect(within(within(screen.getByRole('table')).getByRole('rowheader',{name:'S4 / C3'}).closest('tr')!).getByText('Pass')).toBeTruthy();
 });
 it('preserves the shown case if the requested case fails to load',async()=>{
  vi.stubGlobal('fetch',vi.fn(async()=>({ok:false})));render(<App initialData={bundle}/>);
  fireEvent.change(screen.getByRole('combobox',{name:'Mission'}),{target:{value:'preselected'}});
  await screen.findByRole('alert');expect(screen.getByText(uiText('panels.validation.illustrative_case_note'))).toBeTruthy();
  expect((screen.getByRole('combobox',{name:'Mission'}) as HTMLSelectElement).value).toBe('illustrative');
 });
 it('isolates action logs when switching cases',async()=>{
  mockCases();localStorage.setItem('spacehealth-ui-actions-v1-illustrative',JSON.stringify([{id:'example',crewId:'C2',day:41,cardId:'example-card',action:'Illustrative action only',time:'2026-11-15T12:00:00Z'}]));
  window.history.replaceState({},'','/?view=log');render(<App initialData={bundle}/>);
  expect(screen.getByText(/Illustrative action only/)).toBeTruthy();
  fireEvent.change(screen.getByRole('combobox',{name:'Mission'}),{target:{value:'preselected'}});
  await screen.findByText(uiText('panels.validation.preselected_case_note'));expect(screen.queryByText(/Illustrative action only/)).toBeNull();
  expect(localStorage.getItem('spacehealth-ui-actions-v1-illustrative')).toContain('Illustrative action only');
 });
 it('verifies both case sources before copying either',()=>{
  const source=mkdtempSync(resolve(tmpdir(),'spacehealth-illustrative-')),dest=mkdtempSync(resolve(tmpdir(),'spacehealth-cases-'));
  for(const name of ['mission','indicators','validation','cards','MANIFEST'])copyFileSync(resolve(dataDir,name+'.json'),resolve(source,name+'.json'));
  writeFileSync(resolve(source,'cards.json'),readFileSync(resolve(source,'cards.json'),'utf8')+' ');
  expect(()=>syncCases(resolve(root,'preselected'),source,dest)).toThrow(/checksum mismatch/);
  expect(()=>readFileSync(resolve(dest,'preselected','mission.json'))).toThrow();
 });
 it('uses plain mission labels and tag while keeping technical model identity in a tooltip',()=>{
  render(<App initialData={bundle}/>);
  const selector=screen.getByRole('combobox',{name:'Mission'});
  expect(within(selector).getByRole('option',{name:'Showcase mission — shows every feature'}).getAttribute('value')).toBe('illustrative');
  expect(within(selector).getByRole('option',{name:'Blind test mission — fixed before results'}).getAttribute('value')).toBe('preselected');
  const tag=screen.getByText('Simulated data · settings locked before testing · mission no. 1002');
  expect(tag.getAttribute('title')).toBe(bundle.indicators.modelId);
  expect(tag.textContent).not.toContain(bundle.indicators.modelId);
  expect(tag.parentElement?.textContent).not.toContain(bundle.indicators.modelId);
 });
 it('renders plain indicator reason and M5 information without template braces',async()=>{
  const page=render(<App initialData={bundle}/>);fireEvent.click(screen.getByRole('button',{name:'Physiological change detail'}));await screen.findByRole('button',{name:'Close detail'});
  const detail=screen.getByRole('region',{name:'Module detail'});
  const indicator=bundle.indicators.indicators.find(i=>i.crewId==='C2'&&i.missionDay===41&&i.moduleId==='physiological_change')!;
  expect(within(detail).getAllByText(indicator.reason).length).toBeGreaterThanOrEqual(1);expect(detail.textContent).not.toMatch(/\{[a-z_]+\}/);expect(within(detail).getByText('multi-signal agreement')).toBeTruthy();expect(detail.textContent).toContain('information only');
  page.unmount();window.history.replaceState({},'','/?crew=C2&day=72');render(<App initialData={bundle}/>);fireEvent.click(screen.getByRole('button',{name:'Radiation detail'}));await screen.findByRole('button',{name:'Close detail'});expect(screen.getByRole('region',{name:'Module detail'}).textContent).not.toMatch(/\{[a-z_]+\}/);
 });
 it('renders every source-owned holdout line with release-case rows',()=>{
  window.history.replaceState({},'','/?view=replay');render(<App initialData={bundle}/>);
  expect(screen.getByText(uiText('panels.validation.holdout_title'))).toBeTruthy();for(const line of uiList('panels.validation.holdout_lines'))expect(screen.getByText(line)).toBeTruthy();expect(screen.getByText(uiText('panels.validation.holdout_note'))).toBeTruthy();
 });
 it('rejects a tampered release before copying any files',()=>{
  const source=mkdtempSync(resolve(tmpdir(),'spacehealth-sync-')),dest=mkdtempSync(resolve(tmpdir(),'spacehealth-dest-'));
  for(const name of ['mission','indicators','validation','cards','MANIFEST'])copyFileSync(resolve(dataDir,name+'.json'),resolve(source,name+'.json'));
  writeFileSync(resolve(dest,'sentinel.txt'),'unchanged');writeFileSync(resolve(source,'mission.json'),readFileSync(resolve(source,'mission.json'),'utf8')+' ');
  expect(()=>syncRelease(source,dest)).toThrow(/checksum mismatch/);expect(readFileSync(resolve(dest,'sentinel.txt'),'utf8')).toBe('unchanged');
 });
});
