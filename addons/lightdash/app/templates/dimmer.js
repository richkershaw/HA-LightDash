<script>
(function(){
if(window.__ldLevelWired)return;window.__ldLevelWired=true;
var _curEid="",_curBri=0,_lastBri=100,_lpTimer=null,_acTimer=null,_drag=false;

function M(){return document.getElementById("dimmer-modal")}
function track(){return document.getElementById("dimmer-track")}
function fill(){return document.getElementById("dimmer-fill")}
function pct(){return document.getElementById("dimmer-pct")}
function nameEl(){return document.getElementById("dimmer-name")}
function iconEl(){return document.getElementById("dimmer-icon")}
function leftEl(){return document.getElementById("dimmer-left")}

function isFan(eid){return eid.indexOf("fan.")===0}

function setBri(v){
v=Math.max(0,Math.min(100,Math.round(v)));
_curBri=v;
if(pct())pct().textContent=v+"%";
if(fill())fill().style.height=v+"%";
if(fill()){
if(isFan(_curEid)){fill().style.background="#78b4c8"}
else{
var r=Math.round(221-(221-246)*v/100);
var g=Math.round(221-(221-195)*v/100);
var b=Math.round(221-(221-68)*v/100);
fill().style.background="rgb("+r+","+g+","+b+")";
}
}
}

function sendBri(){
if(!_curEid)return;
var svc,data;
if(isFan(_curEid)){svc="fan.set_percentage";data={percentage:_curBri}}
else{svc="light.turn_on";data={brightness_pct:_curBri}}
navigator.sendBeacon("$action_url",JSON.stringify({entity_id:_curEid,action:"call-service",service:svc,data:data}));
}

function showDimmer(eid,ename,ebri,isOn,iconSvg,favVals){
if(!M())return;
_curEid=eid;
if(nameEl())nameEl().textContent=ename||"";
var b;
if(isFan(eid)){b=isOn?Math.max(0,Math.min(100,Math.round(ebri||0))):0}
else{b=isOn?Math.max(0,Math.min(100,Math.round((ebri||0)/255*100))):0}
if(isOn)_lastBri=b||100;
if(iconSvg&&iconEl()){iconEl().innerHTML=iconSvg;iconEl().style.display=""}
else if(iconEl()){iconEl().innerHTML="";iconEl().style.display="none"}
setBri(b);
$auto_close_timer
M().style.display="";
var le=leftEl();
if(le){
le.innerHTML="";
if(favVals){favVals.split(",").forEach(function(v){var btn=document.createElement("button");btn.textContent=v+"%";btn.className="dimmer-fav-btn";btn.addEventListener("click",function(){setBri(parseInt(v));sendBri();$auto_close_reset});le.appendChild(btn)})}
}
}

function hideDimmer(){if(M())M().style.display="none";_curEid=""}

function dragY(y){
var tr=track();if(!tr)return;
var rect=tr.getBoundingClientRect();
setBri(Math.round((1-(y-rect.top)/rect.height)*100));
}

document.addEventListener("click",function(e){
var t=e.target;
if(!t||!t.closest)return;
if(t.closest("#dimmer-close-btn")){$auto_close_reset;hideDimmer();return}
if(t===M()){$auto_close_reset;hideDimmer();return}
if(t.closest(".dimmer-fav-btn"))return;
if(t.closest("#dimmer-icon")){
if(!_curEid)return;
var isOn=_curBri>0;
if(isFan(_curEid)){
if(isOn){navigator.sendBeacon("$action_url",JSON.stringify({entity_id:_curEid,action:"call-service",service:"fan.turn_off"}));setBri(0)}
else{var fb=_lastBri||100;navigator.sendBeacon("$action_url",JSON.stringify({entity_id:_curEid,action:"call-service",service:"fan.turn_on",data:{percentage:fb}}));setBri(fb)}
}else{
if(isOn){navigator.sendBeacon("$action_url",JSON.stringify({entity_id:_curEid,action:"call-service",service:"light.turn_off"}));setBri(0)}
else{var lb=_lastBri||100;navigator.sendBeacon("$action_url",JSON.stringify({entity_id:_curEid,action:"call-service",service:"light.turn_on",data:{brightness_pct:lb}}));setBri(lb)}
}
return;
}
},true);

document.addEventListener("mousedown",function(e){
var tr=track();
if(tr&&e.target&&tr.contains(e.target)){_drag=true;dragY(e.clientY);$auto_close_reset}
},true);

document.addEventListener("touchstart",function(e){
var tr=track();
if(tr&&e.target&&tr.contains(e.target)){_drag=true;dragY(e.touches[0].clientY);$auto_close_reset}
},true);

document.addEventListener("mousemove",function(e){if(_drag){e.preventDefault();dragY(e.clientY)}},true);
document.addEventListener("touchmove",function(e){if(_drag){e.preventDefault();dragY(e.touches[0].clientY)}},true);
document.addEventListener("mouseup",function(e){if(_drag){_drag=false;sendBri();$auto_close_reset}},true);
document.addEventListener("touchend",function(e){if(_drag){_drag=false;sendBri();$auto_close_reset}},true);

function longPressStart(e){
if(!M())return;
var row=e.target.closest?e.target.closest(".tile-card[data-light-entity],.entity-row[data-light-entity],.tile-card[data-fan-entity],.entity-row[data-fan-entity]"):null;
if(!row)return;
var eid=row.getAttribute("data-light-entity")||row.getAttribute("data-fan-entity");
var favVals=row.getAttribute("data-fav-vals")||"";
_lpTimer=setTimeout(function(){
var ename=(row.querySelector(".tile-name")||row.querySelector(".entity-name")||{}).textContent||"";
var iconEl2=row.querySelector(".tile-icon svg,.entity-icon svg");
var iconSvg=iconEl2?iconEl2.outerHTML:"";
fetch("$state_api_url"+encodeURIComponent(eid)).then(function(r){return r.json()}).then(function(d){
if(d&&!d.error){
var isOn=d.state==="on";
var ebri=(d.attributes&&(isFan(eid)?d.attributes.percentage:d.attributes.brightness))||0;
showDimmer(eid,ename,ebri,isOn,iconSvg,favVals);
}else{showDimmer(eid,ename,0,false,iconSvg,favVals)}
}).catch(function(){showDimmer(eid,ename,0,false,iconSvg,favVals)});
var blocker=function(ev){ev.preventDefault();ev.stopPropagation();document.removeEventListener("click",blocker,true)};
document.addEventListener("click",blocker,true);
},500);
}

function longPressCancel(){if(_lpTimer){clearTimeout(_lpTimer);_lpTimer=null}}

document.addEventListener("mousedown",longPressStart,true);
document.addEventListener("touchstart",longPressStart,true);
document.addEventListener("mousemove",longPressCancel,true);
document.addEventListener("mouseup",longPressCancel,true);
document.addEventListener("touchmove",longPressCancel,true);
document.addEventListener("touchend",longPressCancel,true);
})();
</script>
