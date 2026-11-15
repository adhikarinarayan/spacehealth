import copy from './ui-copy.json';
export const panelKeys=Object.keys(copy.panels);
export function uiText(path:string,values:Record<string,string|number>={}):string{
 let current:unknown=copy;
 for(const key of path.split('.'))current=current&&typeof current==='object'?(current as Record<string,unknown>)[key]:undefined;
 if(typeof current!=='string')return path;
 return current.replace(/\{([^}]+)\}/g,(match,key)=>key in values?String(values[key]):match);
}

export function uiList(path:string):string[]{let current:unknown=copy;for(const key of path.split('.'))current=current&&typeof current==='object'?(current as Record<string,unknown>)[key]:undefined;return Array.isArray(current)&&current.every(x=>typeof x==='string')?current:[path];}
