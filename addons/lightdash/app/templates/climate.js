<script>
(function(){
if(window.__ldClimateWired)return;window.__ldClimateWired=true;
var _curEid="",_curTemp=0,_lpTimer=null,_acTimer=null;

function M(){return document.getElementById("climate-modal")}
function nameEl(){return document.getElementById("climate-name")}
function curEl(){return document.getElementById("climate-current-temp")}
function targetEl(){return document.getElementById("climate-target-temp")}
function modesEl(){return document.getElementById("climate-modes")}

var MODE_LABELS={off:"Off",heat:"Heat",cool:"Cool",heat_cool:"Auto H/C",auto:"Auto",dry:"Dry",fan_only:"Fan Only"};
var DEFAULT_MODES=["off","heat","cool","heat_cool","auto","dry","fan_only"];

function fmtT(t){return t==null||isNaN(t)?"--°":Math.round(t*2)/2+"°"}

function setTarget(t){
if(t==null)return;
_curTemp=Math.round(t*2)/2;
if(targetEl())targetEl().textContent=fmtT(_curTemp);
}

function sendTarget(){
if(!_curEid)return;
navigator.sendBeacon("$action_url",JSON.stringify({entity_id:_curEid,action:"call-service",service:"climate.set_temperature",data:{temperature:_curTemp}}));
}

function setMode(mode){
if(!_curEid)return;
navigator.sendBeacon("$action_url",JSON.stringify({entity_id:_curEid,action:"call-service",service:"climate.set_hvac_mode",data:{hvac_mode:mode}}));
var btns=modesEl().querySelectorAll(".climate-mode-btn");
for(var i=0;i<btns.length;i++){btns[i].classList.toggle("active",btns[i].getAttribute("data-mode")===mode)}
}

function showClimate(eid,ename,cur,target,modes,activeMode){
if(!M())return;
_curEid=eid;
if(nameEl())nameEl().textContent=ename||"";
if(curEl())curEl().textContent=fmtT(cur);
setTarget(target!=null?target:(cur!=null?cur:20));
var list=modes&&modes.length?modes:DEFAULT_MODES;
var me=modesEl();
if(me){
me.innerHTML="";
for(var i=0;i<list.length;i++){
var mode=list[i];
var btn=document.createElement("button");
btn.textContent=MODE_LABELS[mode]||mode;
btn.className="climate-mode-btn";
btn.setAttribute("data-mode",mode);
if(mode===activeMode)btn.classList.add("active");
btn.addEventListener("click",function(){setMode(this.getAttribute("data-mode"))});
me.appendChild(btn);
}
}
$auto_close_timer
M().style.display="";
}

function hideClimate(){if(M())M().style.display="none";_curEid=""}

document.addEventListener("click",function(e){
var t=e.target;
if(!t||!t.closest)return;
if(t.closest("#climate-close-btn")){$auto_close_reset;hideClimate();return}
if(t===M()){$auto_close_reset;hideClimate();return}
if(t.closest("#climate-temp-down")){setTarget(_curTemp-0.5);sendTarget();$auto_close_reset;return}
if(t.closest("#climate-temp-up")){setTarget(_curTemp+0.5);sendTarget();$auto_close_reset;return}
if(t.closest(".climate-mode-btn")){$auto_close_reset;return}
},true);

function longPressStart(e){
if(!M())return;
var row=e.target.closest?e.target.closest(".tile-card[data-climate-entity],.entity-row[data-climate-entity]"):null;
if(!row)return;
var eid=row.getAttribute("data-climate-entity");
_lpTimer=setTimeout(function(){
var ename=(row.querySelector(".tile-name")||row.querySelector(".entity-name")||{}).textContent||"";
fetch("$state_api_url"+encodeURIComponent(eid)).then(function(r){return r.json()}).then(function(d){
if(d&&!d.error){
var a=d.attributes||{};
var cur=a.current_temperature;
var target=a.temperature;
if(target==null&&a.target_temp_high!=null&&a.target_temp_low!=null){target=(a.target_temp_high+a.target_temp_low)/2}
showClimate(eid,ename,cur,target,a.hvac_modes,d.state);
}else{showClimate(eid,ename,null,20,null,"")}
}).catch(function(){showClimate(eid,ename,null,20,null,"")});
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
