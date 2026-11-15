import { describe, it, expect } from 'vitest';
import { readdirSync, readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { fileSchemas } from '../src/contracts';
const root=resolve(import.meta.dirname,'../../contracts/fixtures');
type Entry={path:string;kind:keyof typeof fileSchemas;expected:boolean};
const manifest:Entry[]=JSON.parse(readFileSync(resolve(root,'manifest.json'),'utf8'));
const load=(path:string)=>JSON.parse(readFileSync(resolve(root,path),'utf8'));
describe('shared JSON contract fixtures',()=>{
 for(const entry of manifest)it(entry.path,()=>{
  let accepted=false;
  try{accepted=fileSchemas[entry.kind].safeParse(load(entry.path)).success;}catch{accepted=false;}
  expect(accepted).toBe(entry.expected);
 });
 it('manifest covers every fixture',()=>{
  const files=['valid','invalid'].flatMap(folder=>readdirSync(resolve(root,folder)).filter(n=>n.endsWith('.json')).map(n=>`${folder}/${n}`));
  expect(manifest.map(e=>e.path).sort()).toEqual(files.sort());
 });
 it('rejects duplicate indicator keys',()=>{
  const data=load('valid/indicators--minimal.json');data.indicators.push(data.indicators[0]);
  expect(fileSchemas.indicators.safeParse(data).success).toBe(false);
 });
 for(const bad of [NaN,Infinity,-Infinity])it(`rejects in-memory ${bad}`,()=>{
  const data=load('valid/mission--minimal.json');data.readings[0].rhr_bpm=bad;
  expect(fileSchemas.mission.safeParse(data).success).toBe(false);
 });
 it('public release data passes the same shared contracts',()=>{
  for(const kind of ['mission','indicators','validation','cards'] as const)expect(fileSchemas[kind].safeParse(JSON.parse(readFileSync(resolve(import.meta.dirname,`../public/data/${kind}.json`),'utf8'))).success).toBe(true);
 });
});
