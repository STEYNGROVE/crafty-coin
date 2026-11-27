"use strict";

function card(target,label,value,detail){
 const article=document.createElement("article");
 const title=document.createElement("p");
 const number=document.createElement("strong");
 const note=document.createElement("p");
 title.textContent=label;
 number.textContent=value;
 note.textContent=detail;
 article.append(title,number,note);
 document.getElementById(target).append(article);
}

async function start(){
 const response=await fetch("dashboard.json");
 if(!response.ok)throw Error("Report unavailable");
 const d=await response.json();

 card("metrics","Regression tests",d.regressionTests,"Local checkpoint");
 card("metrics","Recorded revenue","R0","Simulation only");
 card("metrics","Recorded expenditure","R0","No live transactions");
 card("metrics","Production readiness","NO-GO","Release blocked");

 for(const s of d.services){
  card("services",s.service,s.checkpoint,"Historical verification");
 }

 document.getElementById("status").textContent=
  "Snapshot generated: "+d.generatedAt;
}

start().catch(()=>{
 document.getElementById("status").textContent=
  "Intelligence report unavailable";
});
