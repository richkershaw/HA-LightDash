<script>
(function(){
if(window.__ldCoverWired)return;window.__ldCoverWired=true;
var _curEid="",_curPos=0,_lpTimer=null,_acTimer=null,_drag=false;

function M(){return document.getElementById("cover-modal")}
function track(){return document.getElementById("cover-track")}
function fill(){return document.getElementById("cover-fill")}
function posEl(){return document.getElementById("cover-pos")}
function nameEl(){return document.getElementById("cover-name")}
function leftEl(){return document.getElementById("cover-left")}

function setPos(v){
v=Math.max(0,Math.min(100,Math.round(v)));
_curPos=v;
if(posEl())posEl().textContent=v+"%";
if(fill())fill().style.height=v+"%";
if(fill()){
var p=v/100;
var r=Math.round(120+120*p);
var g=Math.round(180+30*p);
var b=Math.round(200-80*p);
fill().style.background="rgb("+r+","+g+","+b+")";
}
}

function sendPos(){
if(!_curEid)return;
navigator.sendBeacon("$action_url",JSON.stringify({entity_id:_curEid,action:"call-service",service:"cover.set_cover_position",data:{position:_curPos}}));
}

function doCoverAction(svc){
if(!_curEid)return;
navigator.sendBeacon("$action_url",JSON.stringify({entity_id:_curEid,action:"call-service",service:svc}));
}

function showCover(eid,ename,epos,favVals){
if(!M())return;
_curEid=eid;
if(nameEl())nameEl().textContent=ename||"";
var p=epos!==null&&epos!==undefined?Math.max(0,Math.min(100,Math.round(epos))):50;
setPos(p);
$auto_close_timer
M().style.display="";
var le=leftEl();
if(le){
le.innerHTML="";
if(favVals){favVals.split(",").forEach(function(v){var btn=document.createElement("button");btn.textContent=v+"%";btn.className="cover-fav-btn";btn.addEventListener("click",function(){setPos(parseInt(v));sendPos();$auto_close_reset});le.appendChild(btn)})}
}
}

function hideCover(){if(M())M().style.display="none";_curEid=""}

function dragY(y){
var tr=track();if(!tr)return;
var rect=tr.getBoundingClientRect();
setPos(Math.round((1-(y-rect.top)/rect.height)*100));
}

document.addEventListener("click",function(e){
var t=e.target;
if(!t||!t.closest)return;
if(t.closest("#cover-close-btn")){$auto_close_reset;hideCover();return}
if(t===M()){$auto_close_reset;hideCover();return}
if(t.closest(".cover-fav-btn"))return;
if(t.closest("#cover-btn-up")){doCoverAction("cover.open_cover");setPos(100);return}
if(t.closest("#cover-btn-stop")){doCoverAction("cover.stop_cover");return}
if(t.closest("#cover-btn-down")){doCoverAction("cover.close_cover");setPos(0);return}
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
document.addEventListener("mouseup",function(e){if(_drag){_drag=false;sendPos();$auto_close_reset}},true);
document.addEventListener("touchend",function(e){if(_drag){_drag=false;sendPos();$auto_close_reset}},true);

function longPressStart(e){
if(!M())return;
var row=e.target.closest?e.target.closest(".tile-card[data-cover-entity],.entity-row[data-cover-entity]"):null;
if(!row)return;
var eid=row.getAttribute("data-cover-entity");
var favVals=row.getAttribute("data-fav-vals")||"";
_lpTimer=setTimeout(function(){
var ename=(row.querySelector(".tile-name")||row.querySelector(".entity-name")||{}).textContent||"";
fetch("$state_api_url"+encodeURIComponent(eid)).then(function(r){return r.json()}).then(function(d){
if(d&&!d.error){
var epos=(d.attributes&&d.attributes.current_position);
showCover(eid,ename,epos,favVals);
}else{showCover(eid,ename,50,favVals)}
}).catch(function(){showCover(eid,ename,50,favVals)});
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
