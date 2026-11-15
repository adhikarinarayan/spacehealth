import { readFileSync } from 'node:fs';
import { resolve,relative } from 'node:path';
import vm from 'node:vm';
import { allFiles } from './offline-build.mjs';
const dir=resolve('dist'),context={self:{}};vm.runInNewContext(readFileSync(resolve(dir,'precache-manifest.js'),'utf8'),context);
const actual=[...context.self.__PRECACHE].sort(),expected=allFiles(dir).map(p=>relative(dir,p).split('\\').join('/')).sort();
if(JSON.stringify(actual)!==JSON.stringify(expected))throw new Error('Offline precache does not cover every built file');
for(const missionCase of ['illustrative','preselected'])for(const name of ['mission','indicators','validation','cards','MANIFEST'])if(!actual.includes(`data/${missionCase}/${name}.json`))throw new Error('Offline release file missing');
console.log(`Offline manifest verified: ${actual.length} files; ${context.self.__CACHE_VERSION}`);
