"use strict";

const CACHE="crafty-learning-v3";

const FILES=[
 "./index.html",
 "./style.css",
 "./app.js",
 "./data.json",
 "./manifest.json",
 "./offline.html",
 "./offline.js",
 "./assets/crafty-master.webp",
 "./icons/crafty-192.png",
 "./icons/crafty-512.png",
 "./icons/crafty-maskable.png"
];

const ALLOWED=new Set(
 FILES.map(file=>new URL(
  file,self.registration.scope
 ).href)
);

self.addEventListener("install",event=>{
 event.waitUntil(
  caches.open(CACHE)
   .then(cache=>cache.addAll(FILES))
   .then(()=>self.skipWaiting())
 );
});

self.addEventListener("activate",event=>{
 event.waitUntil(
  caches.keys()
   .then(keys=>Promise.all(
    keys.filter(key=>
     key.startsWith("crafty-learning-") &&
     key!==CACHE
    ).map(key=>caches.delete(key))
   ))
   .then(()=>self.clients.claim())
 );
});

self.addEventListener("fetch",event=>{

 const request=event.request;
 const url=new URL(request.url);

 if(request.method!=="GET")return;

 if(url.origin!==self.location.origin)return;

 // Never cache private API responses.
 if(url.pathname.startsWith("/api/"))return;

 if(request.mode==="navigate"){

  event.respondWith(
   fetch(request).catch(()=>
    caches.match("./offline.html")
   )
  );

  return;
 }

 if(!ALLOWED.has(url.href))return;

 event.respondWith(
  caches.match(request)
   .then(cached=>cached||fetch(request))
 );
});
