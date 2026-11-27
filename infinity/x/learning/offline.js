"use strict";

const $=id=>document.getElementById(id);

let catalogue;

function text(tag,value){
 const node=document.createElement(tag);
 node.textContent=value;
 return node;
}

function render(){

 const pathway=$("offline-pathway").value;
 const module=$("offline-module").value;
 const container=$("offline-activities");

 container.replaceChildren();

 const items=catalogue[module].filter(
  item=>item.level===pathway
 );

 for(const item of items){

  const card=document.createElement("article");
  card.className="activity";

  card.append(
   text("h2",item.academy||item.hero||item.world),
   text("p",item.activity),
   text("p",item.reflection||"Reflect on what you learned.")
  );

  container.append(card);
 }

 $("offline-status").textContent=
  items.length+" activities available offline";
}

fetch("data.json")
 .then(response=>{
  if(!response.ok)throw Error("Unavailable");
  return response.json();
 })
 .then(data=>{
  catalogue=data;
  $("offline-pathway").onchange=render;
  $("offline-module").onchange=render;
  render();
 })
 .catch(()=>{
  $("offline-status").textContent=
   "Connect to the local server to download learning activities.";
 });
