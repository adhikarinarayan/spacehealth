import { createHash } from 'node:crypto';
import { readFileSync,writeFileSync,mkdirSync } from 'node:fs';
import { dirname,resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { fileSchemas } from '../src/contracts/index';
function verifiedRelease(source:string){
 const manifestBytes=readFileSync(resolve(source,'MANIFEST.json')),manifest=JSON.parse(manifestBytes.toString('utf8'));
 const names=['mission','indicators','validation','cards'] as const;
 const files=names.map(name=>{const filename=`${name}.json`,bytes=readFileSync(resolve(source,filename));const expected=manifest.files?.[filename];if(typeof expected!=='string'||createHash('sha256').update(bytes).digest('hex')!==expected)throw new Error(`Release checksum mismatch: ${filename}`);const value=fileSchemas[name].parse(JSON.parse(bytes.toString('utf8')));return {filename,bytes,value};});
 const values=Object.fromEntries(files.map(f=>[f.filename.replace('.json',''),f.value]));
 if(values.indicators.configHash!==manifest.configHash||values.validation.configHash!==manifest.configHash||values.validation.seedSet!=='holdout'||values.mission.seed!==manifest.seed)throw new Error('Release metadata mismatch');
 return {files,manifestBytes,manifest};
}
function writeRelease(release:ReturnType<typeof verifiedRelease>,destination:string){
 mkdirSync(destination,{recursive:true});for(const file of release.files)writeFileSync(resolve(destination,file.filename),file.bytes);
 writeFileSync(resolve(destination,'MANIFEST.json'),release.manifestBytes);
 return release.files.map(f=>f.filename);
}
export function syncRelease(source:string,destination:string){return writeRelease(verifiedRelease(source),destination);}
export function syncCases(preselectedSource:string,illustrativeSource:string,destination:string){
 // Validate BOTH datasets before writing either; a failure cannot mix case versions.
 const preselected=verifiedRelease(preselectedSource),illustrative=verifiedRelease(illustrativeSource);
 if(preselected.manifest.seed!==1000||illustrative.manifest.seed!==1002||illustrative.manifest.case!=='illustrative'||illustrative.manifest.selectedAfterHoldout!==true||typeof illustrative.manifest.selectionRule!=='string'||!illustrative.manifest.selectionRule.trim())throw new Error('Mission case disclosure metadata mismatch');
 if(preselected.manifest.configHash!==illustrative.manifest.configHash)throw new Error('Mission case frozen configs differ');
 writeRelease(preselected,resolve(destination,'preselected'));writeRelease(illustrative,resolve(destination,'illustrative'));
 // Keep existing root URLs compatible with contract consumers; app uses named cases.
 writeRelease(preselected,destination);
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
 const root=resolve(dirname(fileURLToPath(import.meta.url)),'../..');
 syncCases(resolve(root,'model/out/release'),resolve(root,'model/out/illustrative'),resolve(root,'dashboard/public/data'));
 console.log('Verified and copied illustrative seed 1002 and pre-selected seed 1000; original manifests preserved.');
}
