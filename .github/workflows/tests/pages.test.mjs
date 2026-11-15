// Built-output tests live inside TASK-017's fence; no dashboard source/test edits.
import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync,readdirSync,existsSync } from 'node:fs';
import { resolve } from 'node:path';
import vm from 'node:vm';
const base=process.env.BASE_PATH||'/',dist=resolve('dist');
const precache={self:{}};
vm.runInNewContext(readFileSync(resolve(dist,'precache-manifest.js'),'utf8'),precache);
const paths=Array.from(precache.self.__PRECACHE);

test('built shell and local fonts use the configured Pages base',()=>{
 const html=readFileSync(resolve(dist,'index.html'),'utf8');
 const urls=[...html.matchAll(/(?:src|href)="([^"]+)"/g)].map(m=>m[1]);
 assert.ok(urls.length>=3);
 for(const url of urls){assert.ok(url.startsWith(base),url);assert.ok(existsSync(resolve(dist,url.slice(base.length))),url);}
 const css=readdirSync(resolve(dist,'assets')).filter(n=>n.endsWith('.css')).map(n=>readFileSync(resolve(dist,'assets',n),'utf8')).join('\n');
 const fonts=[...css.matchAll(/url\(["']?([^\s)"']+\.woff2)["']?\)/g)].map(m=>m[1]);
 assert.equal(fonts.length,7);
 for(const url of fonts){assert.ok(url.startsWith(base+'fonts/'),url);assert.ok(existsSync(resolve(dist,url.slice(base.length))),url);}
});

test('production registration uses the configured worker URL and scope',()=>{
 const js=readdirSync(resolve(dist,'assets')).filter(n=>n.endsWith('.js')).map(n=>readFileSync(resolve(dist,'assets',n),'utf8')).join('\n');
 const registration=/navigator\.serviceWorker\.register\((["'`])([^"'`]+)\1,\{scope:(["'`])([^"'`]+)\3\}\)/.exec(js);
 assert.ok(registration,'production service-worker registration not found');
 assert.equal(registration[2],base+'sw.js');assert.equal(registration[4],base);
});

test('built worker precaches both datasets under its actual scope and serves offline navigation/data',async()=>{
 const scope='https://example.github.io'+base,origin=new URL(scope).origin;
 const urls=paths.map(p=>new URL(p,scope).href);
 for(const missionCase of ['illustrative','preselected'])for(const name of ['mission','indicators','validation','cards','MANIFEST'])assert.ok(urls.includes(scope+`data/${missionCase}/${name}.json`));
 const listeners={},loaded=[],requested=[];
 const cache={addAll:async values=>loaded.push(...values),match:async key=>{requested.push(key);return new Response('offline cached');},put:async()=>{}};
 const self={__PRECACHE:paths,__CACHE_VERSION:precache.self.__CACHE_VERSION,registration:{scope},location:{origin},skipWaiting:async()=>{},clients:{claim:async()=>{}},addEventListener:(type,callback)=>{listeners[type]=callback;}};
 let imported;
 vm.runInNewContext(readFileSync(resolve(dist,'sw.js'),'utf8'),{self,URL,Set,caches:{open:async()=>cache},importScripts:path=>{imported=new URL(path,scope+'sw.js').href;},fetch:()=>{throw new Error('unexpected network while offline');}});
 let pending;listeners.install({waitUntil:p=>{pending=p;}});await pending;
 assert.equal(imported,scope+'precache-manifest.js');assert.deepEqual(loaded,urls);assert.ok(loaded.every(url=>url.startsWith(scope)));
 for(const request of [{method:'GET',mode:'navigate',url:scope+'?case=preselected&view=replay'},{method:'GET',mode:'cors',url:scope+'data/illustrative/mission.json'}]){
  listeners.fetch({request,respondWith:p=>{pending=p;}});assert.equal(await (await pending).text(),'offline cached');
 }
 assert.deepEqual(requested,[scope+'index.html',scope+'data/illustrative/mission.json']);
});
