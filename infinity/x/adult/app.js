"use strict";

async function start(){
 const responses=await Promise.all([
  fetch("catalogue.json"),
  fetch("services.json")
 ]);

 if(responses.some(r=>!r.ok)){
  throw Error("Catalogue unavailable");
 }

 const [catalogue,services]=await Promise.all(
  responses.map(r=>r.json())
 );

 const products=catalogue.products;
 const select=document.getElementById("product");

 for(const service of services.services){
  const p=document.createElement("p");
  p.textContent=service.id.replaceAll("_"," ");
  document.getElementById("services").append(p);
 }

 for(const product of products){
  const option=document.createElement("option");
  option.value=product.id;
  option.textContent=product.id.replaceAll("_"," ");
  select.append(option);
 }

 function selected(){
  return products.find(p=>p.id===select.value);
 }

 function price(){
  return new Intl.NumberFormat("en-ZA",{
   style:"currency",currency:"ZAR"
  }).format(selected().priceCents/100);
 }

 function render(){
  document.getElementById("price").textContent=
   "Illustrative price: "+price();
  document.getElementById("result").textContent="";
 }

 select.addEventListener("change",render);

 document.getElementById("draft")
 .addEventListener("click",()=>{
  document.getElementById("result").textContent=
   "Simulated quote: "+price()+
   ". No order or payment created.";
 });

 render();
}

start().catch(()=>{
 document.getElementById("result").textContent=
  "Catalogue unavailable.";
});
