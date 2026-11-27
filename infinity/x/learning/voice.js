"use strict";

(()=>{
 const $=id=>document.getElementById(id);

 const audio=$("crafty-audio");

 let index={};
 let catalogue={};
 let ready=false;
 let generation=0;

 const status=value=>{
  $("crafty-voice-status").textContent=value;
 };

 const lang=()=>$("language").value;

 const speed=()=>Number(
  $("crafty-speed").value
 );

 function stop(){
  generation++;
  audio.pause();
  audio.removeAttribute("src");
  audio.load();

  if("speechSynthesis" in window){
   speechSynthesis.cancel();
  }
 }

 function speakLocal(text,language){

  if(!("speechSynthesis" in window)){
   status(text);
   return;
  }

  const voice=speechSynthesis.getVoices().find(
   v=>v.localService===true &&
   v.lang.toLowerCase().split("-")[0]===language
  );

  if(!voice){
   status(text+" — Read aloud.");
   return;
  }

  const utterance=new SpeechSynthesisUtterance(text);

  utterance.voice=voice;
  utterance.lang=voice.lang;
  utterance.rate=speed();

  utterance.onerror=()=>{
   status("Local voice unavailable.");
  };

  speechSynthesis.speak(utterance);
 }

 async function speak(key){

  stop();

  if(!ready){
   status("Voice catalogue loading.");
   return;
  }

  const request=generation;
  const language=lang();
  const text=catalogue[language]?.[key];

  if(!text)return;

  status(text);

  const item=index[language+":"+key];

  if(item){

   audio.src=item.file;
   audio.playbackRate=speed();

   try{
    await audio.play();

    if(request!==generation)return;

    return;
   }catch{
    if(request!==generation)return;
   }
  }

  speakLocal(text,language);
 }

 $("crafty-speak").onclick=()=>{
  speak("welcome");
 };

 $("crafty-recall").onclick=()=>{
  speak("reflect");
 };

 $("crafty-stop").onclick=()=>{
  stop();
  status("Voice stopped.");
 };

 $("crafty-speed").onchange=()=>{
  audio.playbackRate=speed();
 };

 $("crafty-size").onchange=()=>{
  document.documentElement.style.fontSize=
   $("crafty-size").value+"%";
 };

 $("crafty-motion").onchange=()=>{
  document.documentElement.classList.toggle(
   "crafty-reduced-motion",
   $("crafty-motion").checked
  );
 };

 $("language").addEventListener("change",stop);

 document.addEventListener(
  "visibilitychange",
  ()=>{
   if(document.hidden)stop();
  }
 );

 function addNarration(){

  for(const card of document.querySelectorAll(
   "#activities article"
  )){

   if(card.querySelector(".crafty-read"))continue;

   const button=document.createElement("button");

   button.type="button";
   button.className="crafty-read";
   button.textContent="Read activity aloud";

   button.onclick=()=>{

    stop();

    const text=Array.from(
     card.querySelectorAll("h2,h3,p")
    ).map(node=>node.textContent).join(". ");

    speakLocal(text,"en");
   };

   card.append(button);
  }
 }

 new MutationObserver(addNarration).observe(
  $("activities"),
  {childList:true}
 );

 addNarration();

 Promise.all([
  fetch("voice-index.json").then(r=>{
   if(!r.ok)throw Error("Voice index");
   return r.json();
  }),
  fetch("voice-text.json").then(r=>{
   if(!r.ok)throw Error("Voice text");
   return r.json();
  })
 ]).then(([voices,text])=>{
  index=voices;
  catalogue=text;
  ready=true;
  status("Crafty's voice controls are ready.");
 }).catch(()=>{
  status("Voice catalogue unavailable.");
 });

})();
