"use strict";

const CACHE="crafty-learning-v2";
const FILES=[
 "./assets/crafty-master.webp",
 "./index.html",
 "./style.css",
 "./app.js",
 "./data.json",
 "./manifest.json"
];

self.addEventListener("install",event=>{
 event.waitUntil(
  caches.open(CACHE).then(
   cache=>cache.addAll(FILES)
  )
 );
});

self.addEventListener("activate",event=>{
 event.waitUntil(
  caches.keys().then(keys=>Promise.all(
   keys.filter(
    key=>key.startsWith("crafty-learning-")
    &&key!==CACHE
   ).map(key=>caches.delete(key))
  ))
 );
});

self.addEventListener("fetch",event=>{
 const url=new URL(event.request.url);

 if(event.request.method!=="GET")return;
 if(url.origin!==self.location.origin)return;

 const allowed=FILES.some(
  file=>new URL(
   file,self.registration.scope
  ).href===url.href
 );

 if(!allowed)return;

 event.respondWith(
  caches.match(event.request).then(
   cached=>cached||fetch(event.request)
  )
 );
});
