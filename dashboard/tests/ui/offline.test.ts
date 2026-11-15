// @vitest-environment node
import { describe,it,expect,vi,afterEach } from 'vitest';
import { mkdtempSync,mkdirSync,writeFileSync,readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { tmpdir } from 'node:os';
import vm from 'node:vm';
import { writePrecache,allFiles } from '../../scripts/offline-build.mjs';
import { shouldRegisterOffline,registerOffline } from '../../src/offline';
afterEach(()=>vi.unstubAllGlobals());
describe('production offline cache',()=>{
 it('generates a stable version and covers every asset/data file, including lazy chunks',()=>{
  const dir=mkdtempSync(resolve(tmpdir(),'spacehealth-precache-'));mkdirSync(resolve(dir,'assets'));mkdirSync(resolve(dir,'data'));for(const name of ['illustrative','preselected'])mkdirSync(resolve(dir,'data',name));
  for(const name of ['index.html','sw.js','assets/main.hash.js','assets/Detail.hash.js','assets/style.hash.css',...['illustrative','preselected'].flatMap(c=>['mission','indicators','validation','cards','MANIFEST'].map(n=>`data/${c}/${n}.json`))])writeFileSync(resolve(dir,name),'sample');
  const first=writePrecache(dir),second=writePrecache(dir);expect(first).toEqual(second);expect(first.paths).toContain('assets/Detail.hash.js');expect(first.paths).toContain('precache-manifest.js');expect(first.paths).toContain('data/illustrative/mission.json');expect(first.paths).toContain('data/preselected/mission.json');expect(first.paths).toHaveLength(allFiles(dir).length);
  writeFileSync(resolve(dir,'assets/main.hash.js'),'updated');expect(writePrecache(dir).version).not.toBe(first.version);
 });
 it('never registers in dev or test',async()=>{
  expect(shouldRegisterOffline(false,'development')).toBe(false);expect(shouldRegisterOffline(true,'test')).toBe(false);expect(shouldRegisterOffline(true,'production')).toBe(true);
  const register=vi.fn();vi.stubGlobal('navigator',{serviceWorker:{register}});await registerOffline();expect(register).not.toHaveBeenCalled();
 });
 it('preloads scoped URLs, deletes only old app caches, and serves cached navigation without network',async()=>{
  const listeners:Record<string,(event:any)=>void>={};const cache={addAll:vi.fn(async()=>{}),match:vi.fn(async()=>new Response('cached shell')),put:vi.fn(async()=>{})};const network=vi.fn(async()=>{throw new Error('offline');});
  const caches={open:vi.fn(async()=>cache),keys:vi.fn(async()=>['spacehealth-old','spacehealth-new','other-app']),delete:vi.fn(async()=>true)};
  const self={registration:{scope:'https://example.test/app/'},location:{origin:'https://example.test'},clients:{claim:vi.fn(async()=>{})},skipWaiting:vi.fn(async()=>{}),addEventListener:(name:string,fn:(event:any)=>void)=>{listeners[name]=fn;},__PRECACHE:['index.html','assets/main.js','data/mission.json'],__CACHE_VERSION:'spacehealth-new'};
  vm.runInNewContext(readFileSync(resolve(import.meta.dirname,'../../public/sw.js'),'utf8'),{self,caches,fetch:network,URL,Set,importScripts:()=>{}});
  let pending:Promise<any>=Promise.resolve();listeners.install({waitUntil:(p:Promise<any>)=>{pending=p;}});await pending;expect(cache.addAll).toHaveBeenCalledWith(['https://example.test/app/index.html','https://example.test/app/assets/main.js','https://example.test/app/data/mission.json']);
  listeners.activate({waitUntil:(p:Promise<any>)=>{pending=p;}});await pending;expect(caches.delete).toHaveBeenCalledExactlyOnceWith('spacehealth-old');
  listeners.fetch({request:{method:'GET',mode:'navigate',url:'https://example.test/app/?view=replay'},respondWith:(p:Promise<any>)=>{pending=p;}});expect(await (await pending).text()).toBe('cached shell');expect(network).not.toHaveBeenCalled();
 });
});
