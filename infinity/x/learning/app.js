"use strict";

const $=id=>document.getElementById(id);

let data,token,state;
let moduleName="academies";
let busy=false;

function pathway(){
 return $("pathway").value;
}

function messages(){
 return data.languages[$("language").value];
}

function element(tag,text){
 const node=document.createElement(tag);
 node.textContent=text;
 return node;
}

async function api(path,body){
 const options={
  cache:"no-store",
  headers:{"X-Crafty-Session":token}
 };

 if(body!==undefined){
  options.method="POST";
  options.headers["Content-Type"]="application/json";
  options.body=JSON.stringify(body);
 }

 const response=await fetch("/api/"+path,options);

 if(!response.ok){
  throw Error("Local operation unavailable");
 }

 return response.json();
}

async function refresh(){
 state=await api(
  "progress?pathway="+encodeURIComponent(pathway())
 );
 render();
}

async function perform(action){
 if(busy)return;

 busy=true;

 try{
  await action();
  await refresh();
  $("status").textContent=messages().complete;
 }catch{
  $("status").textContent=
   "Action unavailable. Check your resources or local connection.";
 }finally{
  busy=false;
 }
}

function renderWorld(){

 $("virtual-panel").hidden=moduleName!=="worlds";

 const resources=$("virtual-resources");
 resources.replaceChildren();

 for(const name of [
  "learning","energy","resources",
  "community","environment"
 ]){
  resources.append(
   element("p",name+": "+state.virtualLife[name]+"/100")
  );
 }

 const actions=$("virtual-actions");
 actions.replaceChildren();

 for(const action of [
  "GARDEN","LEARNING_CENTRE","RECYCLE",
  "REST","INVENT","COMMUNITY_HELP","CONSERVE"
 ]){
  const button=element(
   "button",action.replaceAll("_"," ")
  );

  button.onclick=()=>perform(()=>api(
   "decide",{pathway:pathway(),action}
  ));

  actions.append(button);
 }
}

function render(){

 const t=messages();

 document.documentElement.lang=$("language").value;

 for(const key of [
  "welcome","privacy","rest","choose"
 ]){
  $(key).textContent=t[key];
 }

 $("progress").textContent=
  state.count+" of 46 activities recorded";

 $("meter").max=46;
 $("meter").value=state.count;

 const completed=new Set(state.completed);

 const levels=new Map(
  state.heroes.map(
   hero=>[hero.challenge,hero.difficulty]
  )
 );

 document.querySelectorAll("[data-module]")
 .forEach(button=>{
  button.setAttribute(
   "aria-pressed",
   String(button.dataset.module===moduleName)
  );
 });

 renderWorld();

 const query=$("search").value.toLowerCase();

 const items=data[moduleName].filter(item=>
  item.level===pathway() &&
  (
   (item.academy||item.hero||item.world)
   +" "+item.activity
  ).toLowerCase().includes(query)
 );

 const container=$("activities");
 container.replaceChildren();

 for(const item of items){

  const card=element("article","");
  card.className="activity";

  card.append(
   element("h2",item.academy||item.hero||item.world),
   element("p",item.activity),
   element("p",item.reflection||t.reflect),
   element("p",t.help)
  );

  const hero=moduleName==="superheroes";
  const level=levels.get(item.id)||0;
  const finished=hero?level===3:completed.has(item.id);

  const button=element(
   "button",
   finished?t.complete:
   hero?"Record level "+(level+1)+" tried":
   "Record activity tried"
  );

  button.disabled=finished;

  button.onclick=()=>perform(()=>api(
   "complete",{
    pathway:pathway(),
    mission:item.id,
    difficulty:hero?level+1:1
   }
  ));

  card.append(button);
  container.append(card);
 }

 if(!items.length){
  container.append(
   element("p","No matching activities.")
  );
 }
}

async function start(){

 const response=await fetch("data.json");

 if(!response.ok)throw Error("Catalogue unavailable");

 data=await response.json();

 const session=await fetch(
  "/api/session",{cache:"no-store"}
 );

 if(!session.ok)throw Error("Session unavailable");

 token=(await session.json()).token;

 $("pathway").onchange=()=>{
  refresh().catch(()=>{
   $("status").textContent="Progress unavailable";
  });
 };

 $("language").onchange=render;
 $("search").oninput=render;

 document.querySelectorAll("[data-module]")
 .forEach(button=>{
  button.onclick=()=>{
   moduleName=button.dataset.module;
   render();
  };
 });

 $("reset").onclick=()=>{
  if(!confirm("Clear selected pathway progress?"))return;

  perform(()=>api(
   "reset",{pathway:pathway()}
  ));
 };


 if("serviceWorker" in navigator){
  navigator.serviceWorker.register("./sw.js")
   .catch(()=>{
    $("status").textContent=
     "Offline installation unavailable.";
   });
 }

 await refresh();
}

start().catch(()=>{
 $("status").textContent=
  "Start the Crafty local backend and reload.";
});
