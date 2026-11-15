/* Versioned, scope-local, cache-first app assets. No background sync or network-first data. */
importScripts('./precache-manifest.js');
const version=self.__CACHE_VERSION;
const scope=self.registration.scope;
const paths=self.__PRECACHE.map(path=>new URL(path,scope).href);
const allowed=new Set(paths);
self.addEventListener('install',event=>{event.waitUntil(caches.open(version).then(cache=>cache.addAll(paths)).then(()=>self.skipWaiting()));});
self.addEventListener('activate',event=>{event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key.startsWith('spacehealth-')&&key!==version).map(key=>caches.delete(key)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',event=>{
 if(event.request.method!=='GET')return;
 const url=new URL(event.request.url);if(url.origin!==self.location.origin)return;
 const key=event.request.mode==='navigate'?new URL('index.html',scope).href:url.href;
 if(!allowed.has(key))return;
 event.respondWith(caches.open(version).then(async cache=>{
  const stored=await cache.match(key);if(stored)return stored;
  const response=await fetch(key);if(response.ok)await cache.put(key,response.clone());return response;
 }));
});
