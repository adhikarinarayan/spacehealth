import { readdirSync,readFileSync,writeFileSync } from 'node:fs';
import { resolve,relative } from 'node:path';
import { createHash } from 'node:crypto';
export function allFiles(directory){return readdirSync(directory,{withFileTypes:true}).flatMap(entry=>entry.isDirectory()?allFiles(resolve(directory,entry.name)):[resolve(directory,entry.name)]);}
export function writePrecache(directory){
 const existing=allFiles(directory).filter(p=>relative(directory,p)!=='precache-manifest.js').sort();
 const hash=createHash('sha256');for(const path of existing){hash.update(relative(directory,path));hash.update(readFileSync(path));}
 const paths=[...existing.map(p=>relative(directory,p).split('\\').join('/')),'precache-manifest.js'].sort();
 const version=`spacehealth-${hash.digest('hex').slice(0,20)}`;
 writeFileSync(resolve(directory,'precache-manifest.js'),`self.__PRECACHE = ${JSON.stringify(paths)};\nself.__CACHE_VERSION = ${JSON.stringify(version)};\n`);
 return {paths,version};
}
