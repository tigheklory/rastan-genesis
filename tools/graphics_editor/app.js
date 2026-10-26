"use strict";
let O=null,POL=null,TAB="objects",U=null,SRC=null,CMP=null,TGT=null,DIRTY=false,UNDO=[],REDO=[];
let GROUP=new Set(),ACTIVE=0,SOLUTION=null;
let FCAT='fullbody';   // active frame-browser category for the selected multi-frame object
// ---- CRAM Line-2 (Layer B / arcade controlled) protection ----
const reservedLines=()=>((POL&&POL.reserved_lines)||[2]);
const isProtected=l=>reservedLines().includes(l);
const editableLines=()=>[0,1,2,3].filter(l=>!isProtected(l));
function guardProtected(line){if(isProtected(line)){$('#status').textContent='LINE '+line+' is protected (Layer B / arcade controlled) — not editable';alert('LINE '+line+' is the accepted Layer-B / arcade-controlled palette (Build 0313) and is PROTECTED. The editor cannot modify it. Use Lines 0, 1 or 3.');return true;}return false;}
// ---- context editing scope + inheritance ----
let SCOPE='context:gameplay.r01.p01';
const ctxById=id=>(O&&O.contexts||[]).find(c=>c.id===id);
function ctxChain(id){const out=[];let c=ctxById(id);while(c){out.unshift(c);c=c.parent?ctxById(c.parent):null;}return out;}
function ctxName(id){const c=ctxById(id);return c?(c.display||c.id):id;}
function scopeSegment(){const m=/segment_(\d+)$/.exec(SCOPE);return m?+m[1]:null;}
function ctxPolicies(){if(!POL.context_policies)POL.context_policies={};return POL.context_policies;}
// effective CRAM for (line,i) at active SCOPE: base default overlaid by ancestor->scope context overrides
function effEntry(line,i){let cram=POL.target_palette_lines[line]?POL.target_palette_lines[line][i]:null,owner='default';
 const cp=ctxPolicies();ctxChain(SCOPE).forEach(c=>{const t=cp[c.id]&&cp[c.id].tpl&&cp[c.id].tpl[line];if(t&&t[i]!==undefined){cram=t[i];owner=c.id;}});
 return {cram,owner,local:owner===SCOPE};}
const tcram=(line,i)=>effEntry(line,i).cram;
// Effective CRAM including the read-only arcade Layer-B palette for the protected line (Line 2): a tile
// may REUSE (map onto) an existing Layer-B color, so its rendered/exported color must resolve from the
// Layer-B display palette, not the (always-null) Line-2 base.
function effCramAt(line,i){
 if(isProtected(line)){const l2d=POL.line2_display&&POL.line2_display.cram;return (POL.target_palette_lines[line]||[])[i]||(l2d?l2d[i]:null);}
 return tcram(line,i);}
// PROMPT-ID isolation: a target color authored while a scene is active belongs to THAT scene, not the
// shared base. setTgt writes the active scope's override; effLine is the scope's effective 16-entry line.
// (Without this, Layer-A color tools wrote the base and one subround's palette leaked into another.)
function setTgt(line,i,cram){tplSetAt(SCOPE,line,i,cram);}
function effLine(line){const a=[];for(let i=0;i<16;i++)a[i]=effEntry(line,i).cram;return a;}
function setEntry(line,i,cram){if(guardProtected(line))return false;const cp=ctxPolicies();
 (cp[SCOPE]=cp[SCOPE]||{tpl:{}});cp[SCOPE].tpl=cp[SCOPE].tpl||{};cp[SCOPE].tpl[line]=cp[SCOPE].tpl[line]||{};
 const created=cp[SCOPE].tpl[line][i]===undefined;cp[SCOPE].tpl[line][i]=cram;
 if(created)$('#status').textContent='LOCAL OVERRIDE CREATED · '+ctxName(SCOPE)+' · L'+line+':'+i;return true;}
function resetEntry(line,i){const cp=ctxPolicies();if(cp[SCOPE]&&cp[SCOPE].tpl&&cp[SCOPE].tpl[line]){delete cp[SCOPE].tpl[line][i];}}
// ---- phase context + effective Layer-A mapping resolution ----
// PROMPT-ID-0009: resolve the Auto-map DESTINATION safely. A scene-specific scope
// (PAL-R*-S*-PLANEA-*) maps to ITS OWN context + per-subround corpus — never a phase fallback.
// A genuine phase node (…rNN.pNN) maps phase-wide on the R1/P1 corpus. Anything else = no target
// (we NEVER silently fall back to context:gameplay.r01.p01 for an unrecognized scope).
function automapContext(){
 const c=ctxById(SCOPE);if(!c)return null;
 if(/^PAL-/.test(SCOPE))return {id:SCOPE,scene:SCOPE,kind:'scene'};
 for(const x of ctxChain(SCOPE).slice().reverse()){if(/\.p\d+$/.test(x.id))return {id:x.id,scene:null,kind:'phase'};}
 return null;}
function ctxPlaneMaps(cid){const cp=ctxPolicies();cp[cid]=cp[cid]||{};cp[cid].plane_usage_palette_mappings=cp[cid].plane_usage_palette_mappings||{};return cp[cid].plane_usage_palette_mappings;}
function effPlaneMapping(uid){let m=(POL.plane_usage_palette_mappings||{})[uid],owner='global';
 (POL.context_policies?ctxChain(SCOPE):[]).forEach(c=>{const t=(POL.context_policies[c.id]||{}).plane_usage_palette_mappings;if(t&&t[uid]){m=t[uid];owner=c.id;}});
 return m?{m,owner,local:owner===SCOPE}:null;}
function setPlaneMapping(uid,mapping){ // manual edits write at the active scope (context if one is active, else global base)
 if(SCOPE&&ctxById(SCOPE)){ctxPlaneMaps(SCOPE)[uid]=mapping;}else{(POL.plane_usage_palette_mappings=POL.plane_usage_palette_mappings||{})[uid]=mapping;}}
function delPlaneMapping(uid){if(SCOPE&&ctxById(SCOPE)){const t=(ctxPolicies()[SCOPE]||{}).plane_usage_palette_mappings;if(t)delete t[uid];}delete (POL.plane_usage_palette_mappings||{})[uid];}
const planeMap=uid=>{const e=effPlaneMapping(uid);return e?e.m:null;};
function renderScopeBar(){const b=$('#scopebar');if(!b)return;const seg=scopeSegment();
 const nlocal=(()=>{const c=(POL&&POL.context_policies||{})[SCOPE];let n=0;if(c&&c.tpl)Object.values(c.tpl).forEach(l=>n+=Object.keys(l).length);return n;})();
 b.innerHTML='EDITING SCOPE: <b>'+ctxName(SCOPE).toUpperCase()+'</b> <span class="cid">'+SCOPE+'</span>'+(seg!=null?' · segment '+seg:'')+' · local overrides: '+nlocal;
 b.title='All palette color edits apply to this context. Child contexts inherit unless overridden.';}
const $=s=>document.querySelector(s),el=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e;};
// Palette-mapping key: all frames of one object (e.g. every Rastan torso/leg/full-body frame) share
// ONE map_key, so a single palette mapping covers every frame. Enemies fall back to their usage_id.
const MK=u=>(u&&(u.map_key||u.usage_id));
const usageByMapKey=k=>O.usages.find(x=>MK(x)===k);
const j=async(u,o)=>(await fetch(u,o)).json();
const LV=[0,36,73,109,146,182,219,255];
const cramToRGB=w=>{if(w==null)return null;w=parseInt(w);const R=(w>>1)&7,G=(w>>5)&7,B=(w>>9)&7;return[LV[R],LV[G],LV[B]];};
const rgbToCram=([r,g,b])=>{const q=c=>Math.max(0,Math.min(7,Math.round(c/255*7)));return"0x"+(((q(b)<<9)|(q(g)<<5)|(q(r)<<1))>>>0).toString(16).padStart(4,'0').toUpperCase();};
const hex=c=>'#'+c.map(v=>v.toString(16).padStart(2,'0')).join('').toUpperCase();

// ---- color math: sRGB->Lab, ΔE00, OKLab ----
function rgb2lab([r,g,b]){r/=255;g/=255;b/=255;const f=c=>c>0.04045?((c+0.055)/1.055)**2.4:c/12.92;r=f(r);g=f(g);b=f(b);
 let X=r*0.4124+g*0.3576+b*0.1805,Y=r*0.2126+g*0.7152+b*0.0722,Z=r*0.0193+g*0.1192+b*0.9505;X/=0.95047;Z/=1.08883;
 const g2=t=>t>0.008856?Math.cbrt(t):7.787*t+16/116;const fx=g2(X),fy=g2(Y),fz=g2(Z);return[116*fy-16,500*(fx-fy),200*(fy-fz)];}
function deltaE00(rgbA,rgbB){const[L1,a1,b1]=rgb2lab(rgbA),[L2,a2,b2]=rgb2lab(rgbB);
 const C1=Math.hypot(a1,b1),C2=Math.hypot(a2,b2),Cb=(C1+C2)/2;const G=0.5*(1-Math.sqrt(Cb**7/(Cb**7+25**7)));
 const a1p=a1*(1+G),a2p=a2*(1+G),C1p=Math.hypot(a1p,b1),C2p=Math.hypot(a2p,b2);
 const h=(x,y)=>{let t=Math.atan2(y,x)*180/Math.PI;return t<0?t+360:t;};const h1=h(a1p,b1),h2=h(a2p,b2);
 const dLp=L2-L1,dCp=C2p-C1p;let dhp=0;if(C1p*C2p!==0){dhp=h2-h1;if(dhp>180)dhp-=360;else if(dhp<-180)dhp+=360;}
 const dHp=2*Math.sqrt(C1p*C2p)*Math.sin(dhp*Math.PI/360);
 const Lbp=(L1+L2)/2,Cbp=(C1p+C2p)/2;let hbp=h1+h2;if(C1p*C2p!==0){if(Math.abs(h1-h2)>180)hbp+=(h1+h2<360?360:-360);}hbp/=2;
 const T=1-0.17*Math.cos((hbp-30)*Math.PI/180)+0.24*Math.cos(2*hbp*Math.PI/180)+0.32*Math.cos((3*hbp+6)*Math.PI/180)-0.20*Math.cos((4*hbp-63)*Math.PI/180);
 const dTh=30*Math.exp(-(((hbp-275)/25)**2)),Rc=2*Math.sqrt(Cbp**7/(Cbp**7+25**7));
 const Sl=1+(0.015*(Lbp-50)**2)/Math.sqrt(20+(Lbp-50)**2),Sc=1+0.045*Cbp,Sh=1+0.015*Cbp*T,Rt=-Math.sin(2*dTh*Math.PI/180)*Rc;
 return Math.sqrt((dLp/Sl)**2+(dCp/Sc)**2+(dHp/Sh)**2+Rt*(dCp/Sc)*(dHp/Sh));}
function oklab([r,g,b]){r/=255;g/=255;b/=255;const f=c=>c>0.04045?((c+0.055)/1.055)**2.4:c/12.92;r=f(r);g=f(g);b=f(b);
 const l=Math.cbrt(0.4122*r+0.5363*g+0.0514*b),m=Math.cbrt(0.2119*r+0.6807*g+0.1074*b),s=Math.cbrt(0.0883*r+0.2817*g+0.6300*b);
 const L=0.2104*l+0.7936*m-0.0040*s,A=1.9779*l-2.4285*m+0.4505*s,B=0.0259*l+0.7828*m-0.8087*s;return[L,A,B,Math.hypot(A,B),(Math.atan2(B,A)*180/Math.PI+360)%360];}

async function boot(){
 O=await j('/api/oracle');const man=await j('/api/profiles');const sel=$('#profile');sel.innerHTML='';
 (man.profiles||[{profile_id:'baseline_current',display_name:'Baseline (immutable)'}]).forEach(p=>{const o=el('option',null,p.display_name||p.profile_id);o.value=p.profile_id;sel.appendChild(o);});
 await loadProfile('baseline_current');
 document.querySelectorAll('.tabs button').forEach(b=>b.onclick=()=>{TAB=b.dataset.t;document.querySelectorAll('.tabs button').forEach(x=>x.classList.toggle('on',x===b));renderList();});
 sel.onchange=()=>maybeSwitch(sel.value);
 $('#save').onclick=save;$('#reload').onclick=()=>loadProfile($('#profile').value);$('#branch').onclick=branch;
 $('#help').onclick=()=>$('#helpbox').classList.toggle('hide');$('#undo').onclick=undo;$('#redo').onclick=redo;
 window._CENTERHTML=$('#center').innerHTML;
 renderScopeBar();renderList();renderTarget();
 $('#foot').textContent=`${O.usages.length} sprite usages · ${O.objects.length} objects · ${O.palettes.length} palettes · Layer A: click the tab · Genesis 4×16 (Line 2 protected)`;
}
function ensureCenter(){if(window._layerActive){$('#center').innerHTML=window._CENTERHTML;window._layerActive=false;}}
function pushUndo(){UNDO.push(JSON.stringify(POL));if(UNDO.length>50)UNDO.shift();REDO=[];}
function undo(){if(!UNDO.length)return;REDO.push(JSON.stringify(POL));POL=JSON.parse(UNDO.pop());afterChange(true);}
function redo(){if(!REDO.length)return;UNDO.push(JSON.stringify(POL));POL=JSON.parse(REDO.pop());afterChange(true);}
function afterChange(noUndo){DIRTY=true;$('#dirty').textContent='● unsaved';renderScopeBar();renderTarget();renderSource();validate();}
async function maybeSwitch(pid){if(DIRTY&&!confirm('Discard unsaved changes?')){$('#profile').value=POL.profile_id;return;}loadProfile(pid);}
async function loadProfile(pid){POL=await j('/api/policy?p='+encodeURIComponent(pid));if(!POL.target_palette_lines)POL.target_palette_lines=[...Array(4)].map(()=>Array(16).fill(null));if(!POL.usage_palette_mappings)POL.usage_palette_mappings={};if(!POL.plane_usage_palette_mappings)POL.plane_usage_palette_mappings={};if(!POL.context_policies)POL.context_policies={};if(!POL.reserved_lines)POL.reserved_lines=[2];DIRTY=false;renderScopeBar();$('#dirty').textContent='';$('#profile').value=pid;$('#pstatus').textContent=POL.immutable?'immutable baseline — Create editable profile to edit':('editable · parent '+(POL.parent||'—'));$('#save').disabled=!!POL.immutable;renderTarget();renderSource();validate();}
function branch(){const base=($('#newprofile').value||'').trim().replace(/[^a-z0-9_\-]/gi,'_');if(!base)return alert('type a profile name first');POL={profile_id:base,display_name:base,parent:POL.profile_id,immutable:false,schema:'v0.4',target_palette_lines:JSON.parse(JSON.stringify(POL.target_palette_lines)),usage_palette_mappings:JSON.parse(JSON.stringify(POL.usage_palette_mappings)),plane_usage_palette_mappings:JSON.parse(JSON.stringify(POL.plane_usage_palette_mappings||{})),context_policies:JSON.parse(JSON.stringify(POL.context_policies||{})),reserved_lines:[2],line_owners:POL.line_owners,object_labels:{}};const o=el('option',null,base);o.value=base;$('#profile').appendChild(o);$('#profile').value=base;$('#save').disabled=false;DIRTY=true;$('#dirty').textContent='● unsaved';$('#pstatus').textContent='editable (unsaved) · parent '+POL.parent;validate();}
async function save(){if(POL.immutable)return alert('Baseline is immutable. Click "Create editable profile" first.');const r=await j('/api/policy',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(POL)});if(r.ok){DIRTY=false;$('#dirty').textContent='saved';}else alert(r.error);}

function statusOf(o){const s=(o.status||o.category||'UNKNOWN')+'';if(/PROVEN/i.test(s))return'PROVEN';if(/PARTIAL|CAPTURED|pending/i.test(s))return'PARTIAL';if(/NOT REACHABLE|OTHER/i.test(s))return'OTHER';return'UNKNOWN';}
function renderList(){const L=$('#list');L.innerHTML='';
 if(TAB==='layera'){window._layerActive=true;return renderLayerA(L);}
 ensureCenter();
 if(TAB==='objects'){
  const gb=el('div','groupbar');gb.appendChild(el('span','dim','Shared Palette Group: '+GROUP.size+' '));
  if(GROUP.size>=1){mkbtn(gb,'Derive Shared Palette',()=>solveGroup(false,'delta_e'));const lb=mkbtn(gb,'Derive Luminance/Hue Palette',()=>solveGroup(false,'luminance_hue'));lb.title='Prioritizes preserving perceptual brightness (OKLab L), then chooses hues between compatible source colors.';mkbtn(gb,'Compare Solvers',()=>compareSolvers());mkbtn(gb,'Clear',()=>{GROUP.clear();renderList();});}
  L.appendChild(gb);
  // PROMPT-ID-0006 Req 4: honest per-scene sprite coverage — never present R1/P1 enemies as another
  // scene's roster without disclosure. Lazy-fetch + re-render (renderList is sync).
  if(ACTIVE_SCENE){
   const cov=SPR_COV[ACTIVE_SCENE];
   if(cov===undefined){SPR_COV[ACTIVE_SCENE]=null;j('/api/scene_sprite_coverage?scene='+encodeURIComponent(ACTIVE_SCENE)).then(c=>{SPR_COV[ACTIVE_SCENE]=c||null;if(TAB==='objects')renderList();}).catch(()=>{});}
   else if(cov&&cov.coverage_status&&cov.coverage_status!=='PROVEN_COMPLETE'){
    const nb=el('div','warn');nb.style.cssText='border:1px solid #a86;background:#1c1710;color:#d9c9a0;padding:6px 8px;margin:4px 0;font-size:12px;border-radius:4px;';
    nb.textContent=ACTIVE_SCENE+' — sprite coverage: '+cov.coverage_status+'. '+(cov.substitution_warning||'')+' '+(cov.note||'');
    L.appendChild(nb);
    if(Array.isArray(cov.roster)&&cov.roster.length){const rl=el('div','dim');rl.style.cssText='margin:2px 0 6px;font-size:11px;';rl.textContent='known for this scene: '+cov.roster.join(', ');L.appendChild(rl);}
   }
  }
  // group usages by object_id -> ONE palette-domain row (preview frames are representations, not consumers)
  const doms={};O.usages.forEach(u=>{(doms[u.object_id]=doms[u.object_id]||[]).push(u);});
  Object.entries(doms).forEach(([oid,reps])=>{const u0=reps[0];const dname=u0.display_name.split(' (')[0];
   const r=el('div','row');const ck=el('input');ck.type='checkbox';
   // group checkbox adds ONE representative per object (all frames share one palette mapping)
   const inGroup=GROUP.has(u0.usage_id);ck.checked=inGroup;
   ck.onclick=e=>{e.stopPropagation();if(ck.checked)GROUP.add(u0.usage_id);else GROUP.delete(u0.usage_id);renderList();};
   r.appendChild(ck);r.appendChild(el('span',null,' '+dname+' '));r.appendChild(el('span','badge PROVEN',u0.n_used+'c'));
   // accurate inventory badge (Rastan: categories; others: N frames)
   const pc=u0.player_counts;
   if(pc)r.appendChild(el('span','badge OTHER',pc.fullbody+' pairs · '+pc.torso+' torso · '+pc.legs+' legs'));
   else if(reps.length>1)r.appendChild(el('span','badge OTHER',reps.length+' frames'));
   r.onclick=()=>{document.querySelectorAll('#list .row').forEach(x=>x.classList.remove('sel'));r.classList.add('sel');if(!(U&&U.object_id===oid))selectUsage(reps[0]);renderList();};
   if(U&&U.object_id===oid)r.classList.add('sel');L.appendChild(r);
   // FRAME BROWSER for the selected multi-frame object (shared palette mapping; preview follows frame)
   if(reps.length>1&&U&&U.object_id===oid)L.appendChild(renderFrameBrowser(reps));
  });
  O.objects.filter(o=>statusOf(o)!=='PROVEN').forEach(o=>{const r=el('div','row');r.appendChild(el('span',null,(o.display_name||o.id)+' '));r.appendChild(el('span','badge '+statusOf(o),statusOf(o)));r.onclick=()=>{document.querySelectorAll('#list .row').forEach(x=>x.classList.remove('sel'));r.classList.add('sel');U=null;$('#srccolors').innerHTML='';$('#maptable').innerHTML='';$('#previews').innerHTML='<div class="dim">NO PROVEN GRAPHICS PREVIEW AVAILABLE for '+(o.display_name||o.id)+'</div>';};L.appendChild(r);});}
 if(TAB==='contexts'){L.appendChild(el('div','dim','Click a context = set the active EDITING SCOPE. Children inherit unless overridden.'));
  const depth=id=>ctxChain(id).length-1;
  O.contexts.forEach(c=>{const r=el('div','row'+(c.id===SCOPE?' sel':''));r.style.paddingLeft=(6+depth(c.id)*12)+'px';
   r.appendChild(el('span',null,(c.display||c.id)));const cov=ctxCoverage(c);r.appendChild(el('span','badge '+(cov==='COMPLETE'?'PROVEN':cov==='PARTIAL'?'PARTIAL':'UNKNOWN'),cov));
   r.onclick=()=>{selectContext(c.id);};L.appendChild(r);});}
 if(TAB==='palettes')O.palettes.forEach(p=>{const dup=Object.values(O.exact_duplicate_palette_groups).some(g=>g.includes(p.palette_id));const r=el('div','row');r.appendChild(el('span',null,p.palette_id.replace('palette:','')+' '));if(dup)r.appendChild(el('span','badge OTHER','lossless-share'));r.onclick=()=>showPaletteResource(p);L.appendChild(r);});}

// Frame browser: category selector + Prev/Next + dropdown over one object's frames. All frames share
// ONE palette mapping (MK); selecting a frame only changes the previewed artwork, never the mapping.
const FBLBL={fullbody:'Valid Full-Body Pairings',torso:'Torso Frames',legs:'Leg Frames',diagnostic:'Palette Coverage (diagnostic)',weapon:'Weapon Frames',complete:'Complete Corpus (all cells)',composite:'Composite',frames:'Frames',hazard:'Hazard Composite',effect:'Effect Forms'};
function renderFrameBrowser(reps){
 const order=['fullbody','torso','legs','weapon','hazard','effect','composite','complete','frames','diagnostic'];const cats=[];
 order.forEach(c=>{const its=reps.filter(x=>x.frame_category===c).sort((a,b)=>(a.frame_order||0)-(b.frame_order||0));if(its.length)cats.push([c,its]);});
 if(!cats.length)cats.push(['frames',reps]);
 let cur=FCAT;if(!cats.some(([c])=>c===cur))cur=(U&&U.frame_category)||cats[0][0];FCAT=cur;
 const items=(cats.find(([c])=>c===cur)||cats[0])[1];
 const wrap=el('div','framebrowser');
 const catbar=el('div','fbcat');
 cats.forEach(([c,its])=>{const b=el('button','mini'+(c===cur?' on':''),(FBLBL[c]||c)+' ('+its.length+')');
  b.title=(c==='diagnostic')?'internal validation view — the union of every player cell; not a game pose':((FBLBL[c]||c)+' — '+its.length);
  b.onclick=ev=>{ev.stopPropagation();FCAT=c;selectUsage(its[0]);renderList();};catbar.appendChild(b);});
 wrap.appendChild(catbar);
 let idx=items.findIndex(x=>x.usage_id===(U&&U.usage_id));if(idx<0)idx=0;
 const nav=el('div','fbnav');
 const prev=el('button','mini','◀ Prev');prev.disabled=idx<=0;prev.onclick=ev=>{ev.stopPropagation();selectUsage(items[idx-1]);renderList();};
 nav.appendChild(prev);nav.appendChild(el('span','fbpos',(idx+1)+' / '+items.length));
 const next=el('button','mini','Next ▶');next.disabled=idx>=items.length-1;next.onclick=ev=>{ev.stopPropagation();selectUsage(items[idx+1]);renderList();};
 nav.appendChild(next);
 const sel=el('select','fbsel');items.forEach((x,i)=>{const o=el('option',null,x.frame_label||x.display_name);o.value=i;if(i===idx)o.selected=true;sel.appendChild(o);});
 sel.onchange=ev=>{ev.stopPropagation();selectUsage(items[+sel.value]);renderList();};sel.onclick=ev=>ev.stopPropagation();
 nav.appendChild(sel);wrap.appendChild(nav);
 return wrap;
}
function selectUsage(u){U=u;SRC=null;CMP=null;const m=POL.usage_palette_mappings[MK(u)];if(m&&m.line!=null)ACTIVE=m.line;renderTarget();renderSource();renderPreviews();}
function swBox(rgb,cls){const s=el('div','sw'+(cls?' '+cls:''));s.style.background=rgb?`rgb(${rgb.join(',')})`:'#20202a';return s;}

function renderSource(){const S=$('#srccolors');S.innerHTML='';if(!U){S.innerHTML='<div class="dim">Select an object (left) to see the colors it actually uses.</div>';return;}
 $('#srchdr').textContent='ARCADE SOURCE — '+U.display_name+' (bank '+U.sprite_bank+', '+U.n_used+' used colors)';
 // primary actions bar
 const bar=el('div','actbar');
 mkbtn(bar,'Auto-fill Object',()=>autoFill());mkbtn(bar,'Recommend Line',()=>recommendLine());
 mkbtn(bar,'Reset Mapping',()=>{pushUndo();delete POL.usage_palette_mappings[MK(U)];afterChange();});
 S.appendChild(bar);S.appendChild(el('div','dim','Drag a color onto a Genesis entry (right) — or click a color, then a target entry. Click two colors to Compare.'));
 const grid=el('div','apal');
 U.used_colors.forEach(c=>{const cell=el('div','ccell');const sw=swBox(c.arcade_rgb8);sw.draggable=true;if(SRC&&SRC.src_index===c.src_index)sw.classList.add('picked');sw.title=`src idx ${c.src_index} ${c.hex} · ${c.pixel_count}px · Genesis ${c.genesis_cram}`;
  sw.ondragstart=e=>{SRC=c;e.dataTransfer.setData('text/plain','src');};
  sw.onclick=()=>{if(SRC&&CMP===null&&SRC.src_index!==c.src_index&&window._cmpMode){compareTool(SRC,c);window._cmpMode=false;}else{SRC=c;renderSource();showColorProps(c);if(TGT){/* click-to-map */}}};
  cell.appendChild(sw);cell.appendChild(el('span',null,'i'+c.src_index));
  const m=(POL.usage_palette_mappings[MK(U)]||{}).index_map||{};if(m[c.src_index]!=null)cell.appendChild(el('span','tag','→L'+POL.usage_palette_mappings[MK(U)].line+':'+m[c.src_index]));
  grid.appendChild(cell);});
 S.appendChild(grid);renderMapTable();renderPreviews();
}
function mkbtn(p,t,f){const b=el('button','act',t);b.onclick=f;p.appendChild(b);return b;}
function bestCramFor(rgb){/* nearest legal CRAM by ΔE00 */let best=null;for(let R=0;R<8;R++)for(let G=0;G<8;G++)for(let B=0;B<8;B++){const t=[LV[R],LV[G],LV[B]];const d=deltaE00(rgb,t);if(!best||d<best.d)best={cram:'0x'+(((B<<9)|(G<<5)|(R<<1))>>>0).toString(16).padStart(4,'0').toUpperCase(),d,rgb:t};}return best;}
function lineFit(line){/* for U on `line`: exact/natural shares, new entries, MRD ok */let shares=0,neu=0;const used={};POL.target_palette_lines[line].forEach((c,i)=>{if(c!=null)used[c]=i;});
 U.used_colors.forEach(c=>{const cram=bestCramFor(c.arcade_rgb8).cram;if(used[cram]!=null)shares++;else neu++;});
 return {line,shares,neu,fits:neu<= (15-POL.target_palette_lines[line].filter((x,k)=>x!=null&&k!==0).length)};}
function recommendLine(){const ranks=editableLines().map(lineFit).sort((a,b)=>(b.shares-a.shares)||(a.neu-b.neu));const P=$('#props');P.innerHTML='';
 P.appendChild(txt('RECOMMEND LINE for '+U.display_name));ranks.forEach((r,i)=>{const v=el('div','vitem '+(r.fits?(i===0?'PASS':'WARN'):'ERROR'),`Line ${r.line}: ${r.shares} share + ${r.neu} new ${r.fits?'':'— does not fit'}`);P.appendChild(v);});
 const b=el('button',null,'Auto-fill on Line '+ranks[0].line);b.onclick=()=>autoFill(ranks[0].line);P.appendChild(b);}
function autoFill(line){if(POL.immutable)return alert('Create an editable profile first.');
 if(line==null){line=editableLines().map(lineFit).sort((a,b)=>(b.shares-a.shares)||(a.neu-b.neu))[0].line;}
 if(guardProtected(line))return;
 pushUndo();const m=POL.usage_palette_mappings[MK(U)]={line,index_map:{}};const L=POL.target_palette_lines[line];
 // used->distinct target entries; detail-preserving: never map two used colors to one entry; resolve natural collisions
 const taken={};L.forEach((c,i)=>{if(c!=null)taken[c]=i;});
 let next=1;const nextFree=()=>{while(next<16&&L[next]!=null)next++;return next<16?next:-1;};
 U.used_colors.forEach(c=>{let cram=bestCramFor(c.arcade_rgb8).cram;
   // detail-preserving collision: if that cram already used by ANOTHER src in this fill, nudge to next-best distinct legal
   if(Object.values(m.index_map).some(ti=>L[ti]===cram)){cram=nudgeDistinct(c.arcade_rgb8,new Set(Object.values(m.index_map).map(ti=>L[ti])));}
   let ti=Object.entries(taken).find(([cr])=>cr===cram); if(ti)ti=+ti[1];
   if(ti==null||ti===false){ti=nextFree();if(ti<0){$('#status').textContent='line full';return;}L[ti]=cram;taken[cram]=ti;}
   m.index_map[c.src_index]=ti;});
 $('#status').textContent=`Auto-filled ${U.display_name} → Line ${line} (${Object.keys(m.index_map).length} colors, detail preserved)`;afterChange();}
function nudgeDistinct(rgb,taken){let best=null;for(let R=0;R<8;R++)for(let G=0;G<8;G++)for(let B=0;B<8;B++){const cram='0x'+(((B<<9)|(G<<5)|(R<<1))>>>0).toString(16).padStart(4,'0').toUpperCase();if(taken.has(cram))continue;const d=deltaE00(rgb,[LV[R],LV[G],LV[B]]);if(!best||d<best.d)best={cram,d};}return best?best.cram:bestCramFor(rgb).cram;}
function findSimilar(c){const P=$('#props');P.innerHTML='';P.appendChild(txt('SIMILAR COLORS to '+c.hex+' ('+U.display_name+' i'+c.src_index+')'));
 const rows=[];O.usages.forEach(u=>{u.used_colors.forEach(o=>{if(u.usage_id===U.usage_id&&o.src_index===c.src_index)return;const de=deltaE00(c.arcade_rgb8,o.arcade_rgb8);rows.push({u,o,de,sameNat:o.genesis_cram===c.genesis_cram,exact:o.hex===c.hex,diffObj:u.usage_id!==U.usage_id});});});
 rows.sort((a,b)=>a.de-b.de);const T=el('div','simtab');
 rows.slice(0,14).forEach(r=>{const row=el('div','maprow');const sw=swBox(r.o.arcade_rgb8);sw.style.display='inline-block';row.appendChild(sw);
  row.appendChild(el('span',null,r.u.display_name+' i'+r.o.src_index));row.appendChild(el('span',null,r.o.hex));
  row.appendChild(el('span',null,'ΔE '+r.de.toFixed(2)+(r.exact?' EXACT':r.sameNat?' =nat':'')));row.appendChild(el('span',r.diffObj?'':'dim',r.diffObj?'cross-obj':'same'));T.appendChild(row);});
 P.appendChild(T);}
function showColorProps(c){const P=$('#props');const lab=rgb2lab(c.arcade_rgb8),ok=oklab(c.arcade_rgb8);
 P.innerHTML='';P.appendChild(txt(`SOURCE COLOR (src idx ${c.src_index})\narcade RGB: ${c.arcade_rgb8.join(', ')}\nhex: ${c.hex}\npixels used: ${c.pixel_count}\nnatural Genesis: ${c.genesis_cram} rgb(${c.genesis_rgb8.join(',')})\nLab: ${lab.map(x=>x.toFixed(1)).join(', ')}\nOKLab: ${ok.slice(0,3).map(x=>x.toFixed(3)).join(', ')}\nOKLCH: L${ok[0].toFixed(3)} C${ok[3].toFixed(3)} H${ok[4].toFixed(0)}`));
 // AUTO closest-ΔE in ACTIVE line (Part 4)
 const cl=closestInLine(c,ACTIVE);
 if(cl.absolute){const legalSame=cl.legal&&cl.legal.index===cl.absolute.index;
  const dL=a=>Math.abs(oklab(c.arcade_rgb8)[0]-oklab(cramToRGB(POL.target_palette_lines[ACTIVE][a.index]))[0]).toFixed(3);
  const box=el('div','vitem '+(legalSame?'PASS':'ERROR'));box.innerHTML=`CLOSEST ΔE in LINE ${ACTIVE}: L${ACTIVE}:${cl.absolute.index} ΔE00 ${cl.absolute.de.toFixed(2)} · ΔL ${dL(cl.absolute)}`+(legalSame?'':' — FORBIDDEN (Must Stay Distinct)');P.appendChild(box);
  // optional closest-by-lightness
  let bl=null;const LL=POL.target_palette_lines[ACTIVE];for(let i=1;i<16;i++){if(LL[i]==null)continue;const d=Math.abs(oklab(c.arcade_rgb8)[0]-oklab(cramToRGB(LL[i]))[0]);if(bl===null||d<bl.d)bl={i,d};}
  if(bl)P.appendChild(el('div','vitem WARN',`CLOSEST LIGHTNESS: L${ACTIVE}:${bl.i} ΔL ${bl.d.toFixed(3)}`));
  if(!legalSame&&cl.legal){P.appendChild(el('div','vitem PASS',`CLOSEST LEGAL: L${ACTIVE}:${cl.legal.index} ΔE00 ${cl.legal.de.toFixed(2)}`));}
  const tgtEntry=cl.legal||cl.absolute;mkbtn(P,'Map to Closest Legal (L'+ACTIVE+':'+tgtEntry.index+')',()=>{SRC=c;TGT={line:ACTIVE,index:tgtEntry.index};renderTarget();mapWithAuto(ACTIVE,tgtEntry.index);});
 } else {P.appendChild(el('div','vitem WARN','No existing target colors in LINE '+ACTIVE+'.'));mkbtn(P,'Add Natural Genesis Color (free entry)',()=>{const fi=POL.target_palette_lines[ACTIVE].findIndex((x,k)=>x==null&&k!==0);if(fi<0)return alert('line full');SRC=c;TGT={line:ACTIVE,index:fi};mapWithAuto(ACTIVE,fi);});}
 const info=el('div','vitem WARN','Drag this color to a Genesis entry, or click a target entry to map. Find Matches = global corpus search.');P.appendChild(info);
 mkbtn(P,'Find Matches (global corpus)',()=>findSimilar(c));
 mkbtn(P,'Compare (pick another color next)',()=>{window._cmpMode=true;$('#status').textContent='compare mode: click another source color';});}
function mapWithAuto(line,index){/* map SRC to target line/index; auto best legal color if empty; MRD-checked */
 if(!U||!SRC)return;if(POL.immutable)return alert('Create an editable profile first.');
 // Line 2 (protected): colors are arcade-controlled and NOT editable, but an EXISTING Line-2 color
 // may be REUSED. Allow mapping onto an occupied index; refuse creating a new color here.
 const prot=isProtected(line);
 if(prot){
   const l2d=POL.line2_display&&POL.line2_display.cram?POL.line2_display.cram:null;
   const have=(POL.target_palette_lines[line]||[])[index]||(l2d?l2d[index]:null);
   if(index===0||!have){
     $('#status').textContent='LINE '+line+' index '+index+' has no arcade color — Line 2 colors are not editable, so pick an index that already shows a color.';
     return alert('LINE '+line+' (Layer B / arcade) is read-only. You can REUSE one of its existing colors, but you cannot create a new color on an empty index. Choose an index that already has a color.');
   }
   if(animatedIndices(line).includes(index) && !confirm('L'+line+':'+index+' is the ANIMATED sky/time-of-day color (it changes across Round 1). Reusing it means this object will shift color with the sky. Use it anyway?'))return;
 }
 const m=POL.usage_palette_mappings[MK(U)]||(POL.usage_palette_mappings[MK(U)]={line,index_map:{}});
 if(m.line!==line){if(Object.keys(m.index_map).length&&!confirm('Move this usage\'s mappings to line '+line+'?'))return;m.line=line;}
 for(const[si,ti]of Object.entries(m.index_map)){if(+ti===index&&+si!==SRC.src_index){const pair=U.mrd_pairs.some(([a,b])=>(a===+si&&b===SRC.src_index)||(b===+si&&a===SRC.src_index));if(pair)return alert('Cannot share: Must Stay Distinct — src i'+SRC.src_index+' and i'+si+' both appear in '+U.display_name+'.');}}
 pushUndo();m.index_map[SRC.src_index]=index;
 if(!prot&&POL.target_palette_lines[line][index]==null)POL.target_palette_lines[line][index]=bestCramFor(SRC.arcade_rgb8).cram;
 $('#status').textContent=`${U.display_name} i${SRC.src_index} → L${line}:${index} (${POL.target_palette_lines[line][index]})`+(prot?' [reusing Layer-B color]':'');afterChange();showTarget();}
/* Line-2 animated (sky/time-of-day) indices to flag as "avoid". Profile-driven; empty until identified.
 * Set via line_owners["2"].animated_indices = [..] or reserved_line_animated = {2:[..]} in the profile. */
function animatedIndices(line){const o=((POL&&POL.line_owners)||{})[line+'']||{};
 return o.animated_indices||((POL&&POL.reserved_line_animated)||{})[line+'']||[];}

function renderMapTable(){const T=$('#maptable');T.innerHTML='';if(!U)return;const map=(POL.usage_palette_mappings[MK(U)]||{});const im=map.index_map||{};
 const head=el('div','maprow mono');head.innerHTML='<b>Source</b><b>Arcade</b><b>Mapped To</b><b>Target color</b><b></b>';T.appendChild(head);
 U.used_colors.forEach(c=>{const r=el('div','maprow mono');const ti=im[c.src_index];const tcram=ti!=null?POL.target_palette_lines[map.line][ti]:null;const trgb=cramToRGB(tcram);
  r.appendChild(el('span',null,'i'+c.src_index));const a=el('span');a.appendChild(swBox(c.arcade_rgb8));a.appendChild(el('span',null,' '+c.hex));r.appendChild(a);
  r.appendChild(el('span',null,ti!=null?('L'+map.line+':'+ti):'—'));const t=el('span');if(trgb){t.appendChild(swBox(trgb));t.appendChild(el('span',null,' '+tcram));}else t.textContent='—';r.appendChild(t);
  const rm=el('span');if(ti!=null){const b=el('button','mini','unmap');b.onclick=()=>{pushUndo();delete im[c.src_index];afterChange();};rm.appendChild(b);}r.appendChild(rm);T.appendChild(r);});}

function renderTarget(){const G=$('#genlines');G.innerHTML='';if(!POL)return;
 // capacity banner: only editable lines count
 const ed=editableLines();const bn=el('div','vitem WARN');bn.innerHTML='AVAILABLE FOR LAYER A + SPRITES: Lines '+ed.join(', ')+' · <b>Line 2 = LAYER B (arcade controlled) PROTECTED</b> · capacity '+(ed.length*15)+' entries ('+ed.length+'×15)';G.appendChild(bn);
 for(let line=0;line<4;line++){const prot=isProtected(line);const row=el('div','line'+(line===ACTIVE&&!prot?' activeline':'')+(prot?' protline':''));
  const lb=el('span','lbl'+(line===ACTIVE&&!prot?' on':''),prot?('L'+line+' 🔒'):('LINE '+line+(line===ACTIVE?' ▸':'')));lb.style.cursor='pointer';
  lb.title=prot?'LINE '+line+' — LAYER B — ARCADE CONTROLLED — PROTECTED':'';
  lb.onclick=()=>{ACTIVE=line;renderTarget();if(TAB==='layera')renderLayerA($('#list'));if(prot)showProtected(line);else if(SRC)showColorProps(SRC);};row.appendChild(lb);
  const clc=(SRC&&!prot)?closestInLine(SRC,line):null;
  // current object's existing target assignments on this line (for the "assigned to index" tags)
  const curMap=U?(POL.usage_palette_mappings[MK(U)]||{}):{};const curRev={};
  if(curMap.line===line){for(const[si,ti] of Object.entries(curMap.index_map||{}))curRev[ti]=si;}
  const anim=animatedIndices(line);
  // index-number label (+ object source-index tag + animated marker) for every target swatch
  const decorate=(s,i,cram)=>{s.appendChild(el('span','idx'+(cram&&i!==0?'':' empty'),''+i));
    if(curRev[i]!=null&&i!==0){s.classList.add('objassigned');s.appendChild(el('span','objtag','i'+curRev[i]));}
    if(anim.includes(i)){s.classList.add('animidx');s.appendChild(el('span','anim','⚡'));}};
 const l2disp=(prot&&POL.line2_display&&POL.line2_display.cram)?POL.line2_display.cram:null;
 for(let i=0;i<16;i++){const eff=prot?{cram:((POL.target_palette_lines[line]||[])[i])||(l2disp?l2disp[i]:null),owner:'layer_b',local:false}:effEntry(line,i);const cram=eff.cram;const rgb=cramToRGB(cram);const s=el('div','sw'+(i===0?' tp':'')+(prot?' protsw':''));if(rgb&&i!==0)s.style.background=`rgb(${rgb.join(',')})`;
  if(prot){const usable=cram&&i!==0;decorate(s,i,cram);
    s.title=usable?`L${line}:${i} ${cram} — Layer B color (read-only, reusable)${anim.includes(i)?' · ANIMATED sky — avoid':''}`:`L${line}:${i} — Layer B protected (empty/read-only)`;
    if(usable)s.classList.add('protusable');
    s.onclick=()=>{ACTIVE=line;
      if(window._laMode&&LAUSAGE&&LASRC){if(usable)laMapColor(line,i);else{TGT={line,index:i};renderTarget();showProtected(line);}return;}
      if(usable&&SRC&&U){TGT={line,index:i};renderTarget();mapWithAuto(line,i);}else{TGT={line,index:i};renderTarget();showProtected(line);}};
    row.appendChild(s);continue;}
  decorate(s,i,cram);
  if(cram&&i!==0&&eff.local)s.classList.add('localov');else if(cram&&i!==0&&eff.owner!=='default')s.classList.add('inherov');
  if(TGT&&TGT.line===line&&TGT.index===i)s.classList.add('picked');
   let dtip='';if(clc&&cram){const de=deltaE00(SRC.arcade_rgb8,cramToRGB(cram));dtip=' Δ'+de.toFixed(1);
     if(clc.absolute&&clc.absolute.index===i){s.classList.add((clc.legal&&clc.legal.index===i)?'nearestlegal':'nearestforbid');}
     else if(clc.legal&&clc.legal.index===i)s.classList.add('nearestlegal');}
   s.title=`L${line}:${i} ${cram||'(empty)'}${eff.owner!=='default'?' ['+(eff.local?'LOCAL '+ctxName(SCOPE):'inherited '+ctxName(eff.owner))+']':''}${dtip}`;s.onclick=()=>{if(window._laMode&&LAUSAGE&&LASRC){laMapColor(line,i);return;}TGT={line,index:i};ACTIVE=line;renderTarget();showTarget();if(SRC&&U){mapWithAuto(line,i);}};
   s.ondragover=e=>{e.preventDefault();s.classList.add(cram?'dropshare':'dropok');};s.ondragleave=()=>{s.classList.remove('dropok','dropshare');};
   s.ondrop=e=>{e.preventDefault();s.classList.remove('dropok','dropshare');if(guardProtected(line))return;TGT={line,index:i};mapWithAuto(line,i);};row.appendChild(s);}
 G.appendChild(row);}}
function showProtected(line){const P=$('#props');P.innerHTML='';const o=((POL.line_owners||{})[line+''])||{};
 P.appendChild(txt('LINE '+line+' — LAYER B — ARCADE CONTROLLED — PROTECTED\n\nThis line is owned by the accepted Layer-B time-of-day palette path in Build 0313 and is excluded from editor optimization.\n\nOwner: '+(o.owner||'layer_b')+'\nControl: '+(o.control||'arcade')+'\nEditable: NO\nOptimizer target: NO\n\nIt changes across Round 1 (sky/time-of-day). Tighe accepted the current Layer-B result — the editor only inspects it, never edits it.'));
 P.appendChild(el('div','vitem PASS','Read-only. No sliders · no mapping · no clear · no Apply for this line.'));}
function showTarget(){const P=$('#props');P.innerHTML='';if(!TGT)return;if(isProtected(TGT.line)){return showProtected(TGT.line);}
 const eff=effEntry(TGT.line,TGT.index);const cram=eff.cram;const rgb=cramToRGB(cram)||[40,40,50];
 const srcinfo=eff.owner==='default'?'profile default (global)':(eff.local?'LOCAL OVERRIDE · '+ctxName(SCOPE):'inherited from '+ctxName(eff.owner));
 P.appendChild(txt(`GENESIS TARGET  L${TGT.line} : ${TGT.index}\nCRAM: ${cram||'(empty)'}\nRGB approx: ${rgb.join(', ')}\nEffective: ${srcinfo}\nEditing scope: ${ctxName(SCOPE)}`));
 P.appendChild(el('div','vitem '+(eff.local?'PASS':eff.owner!=='default'?'WARN':'PASS'),eff.local?'LOCAL to '+ctxName(SCOPE):eff.owner!=='default'?'INHERITED FROM '+ctxName(eff.owner)+' (edit to create a local override)':'Global profile default'));
 if(TGT.index===0){P.appendChild(el('div','vitem WARN','Index 0 is transparent/background-reserved.'));}
 const applyCram=nc=>{pushUndo();setEntry(TGT.line,TGT.index,nc);afterChange();showTarget();};
 // precise per-channel ±1 Genesis controls + snapping slider (levels 0..7)
 const pk=el('div','picker');['R','G','B'].forEach((ch,ci)=>{const lvl=()=>((tcram(TGT.line,TGT.index)?parseInt(tcram(TGT.line,TGT.index)):0)>>(1+ci*4))&7;
  const setLvl=v=>{v=Math.max(0,Math.min(7,v));const levels=[0,1,2].map(k=>k===ci?v:((tcram(TGT.line,TGT.index)?parseInt(tcram(TGT.line,TGT.index)):0)>>(1+k*4))&7);applyCram('0x'+(((levels[2]<<9)|(levels[1]<<5)|(levels[0]<<1))>>>0).toString(16).padStart(4,'0').toUpperCase());};
  const box=el('div','chanrow');box.appendChild(el('span','chlbl',ch));
  const minus=el('button','mini','−');minus.disabled=lvl()<=0;minus.onclick=()=>setLvl(lvl()-1);box.appendChild(minus);
  box.appendChild(el('span','chlvl',lvl()+' / 7'));
  const plus=el('button','mini','+');plus.disabled=lvl()>=7;plus.onclick=()=>setLvl(lvl()+1);box.appendChild(plus);
  const inp=el('input');inp.type='range';inp.min=0;inp.max=7;inp.step=1;inp.value=lvl();inp.oninput=()=>setLvl(+inp.value);box.appendChild(inp);
  pk.appendChild(box);});P.appendChild(pk);
 // reset local override for this entry
 if(eff.local){mkbtn(P,'Reset Context Override (→ inherited)',()=>{pushUndo();resetEntry(TGT.line,TGT.index);afterChange();showTarget();});}
 if(U&&SRC){const b=el('button',null,`Map "${U.display_name}" src i${SRC.src_index} → L${TGT.line}:${TGT.index}`);b.onclick=()=>mapSrcToTarget();P.appendChild(b);}
 else P.appendChild(el('div','dim','Select a source color to map it here. Color edits above apply to the active context scope.'));
 const users=sourcesAt(TGT.line,TGT.index);if(users.length){P.appendChild(el('div','vitem PASS','Sources mapped here: '+users.map(u=>u.name+' i'+u.si).join(', ')));}
 const cl=el('button','mini','clear entry (base)');cl.onclick=()=>{pushUndo();POL.target_palette_lines[TGT.line][TGT.index]=null;Object.values(POL.usage_palette_mappings).forEach(m=>{if(m.line===TGT.line)for(const k in m.index_map)if(m.index_map[k]===TGT.index)delete m.index_map[k];});afterChange();};P.appendChild(cl);}
function sourcesAt(line,index){const out=[];for(const[uid,m]of Object.entries(POL.usage_palette_mappings)){if(m.line!==line)continue;for(const[si,ti]of Object.entries(m.index_map||{}))if(+ti===index){const u=usageByMapKey(uid)||O.usages.find(x=>x.usage_id===uid);out.push({name:u?u.display_name:uid,si});}}return out;}

function mapSrcToTarget(){if(POL.immutable)return alert('Create an editable profile first.');if(guardProtected(TGT.line))return;const uid=MK(U);const m=POL.usage_palette_mappings[uid]||(POL.usage_palette_mappings[uid]={line:TGT.line,index_map:{}});
 if(m.line!==TGT.line){if(Object.keys(m.index_map).length&&!confirm('This usage was mapped to line '+m.line+'. Move all its mappings to line '+TGT.line+'?'))return;m.line=TGT.line;}
 // MRD check: does any already-mapped src of THIS usage that must stay distinct from SRC share this target index?
 for(const[si,ti]of Object.entries(m.index_map)){if(+ti===TGT.index&&+si!==SRC.src_index){const pair=U.mrd_pairs.some(([a,b])=>(a===+si&&b===SRC.src_index)||(b===+si&&a===SRC.src_index));if(pair){$('#status').textContent='';return alert('MERGE FORBIDDEN — internal detail would be lost: src i'+SRC.src_index+' and src i'+si+' both appear in '+U.display_name+' and must stay distinct.');}}}
 pushUndo();m.index_map[SRC.src_index]=TGT.index;
 if(POL.target_palette_lines[TGT.line][TGT.index]==null)POL.target_palette_lines[TGT.line][TGT.index]=SRC.genesis_cram;
 $('#status').textContent=`${U.display_name} i${SRC.src_index} → L${TGT.line}:${TGT.index}`;afterChange();showTarget();}

function compareTool(a,b){if(!a){$('#status').textContent='pick a first source color';return;}CMP=b;const de=deltaE00(a.arcade_rgb8,b.arcade_rgb8);
 const sameNat=a.genesis_cram===b.genesis_cram;const mrd=U.mrd_pairs.some(([x,y])=>(x===a.src_index&&y===b.src_index)||(y===a.src_index&&x===b.src_index));
 const P=$('#props');P.innerHTML='';P.appendChild(txt(`COMPARE\nA: ${U.display_name} i${a.src_index} ${a.hex} (nat ${a.genesis_cram})\nB: ${U.display_name} i${b.src_index} ${b.hex} (nat ${b.genesis_cram})\nΔE00(A,B): ${de.toFixed(2)}\nsame natural Genesis: ${sameNat?'YES':'NO'}`));
 if(mrd){P.appendChild(el('div','vitem ERROR','MERGE FORBIDDEN — these both appear in '+U.display_name+' (internal detail). Keep distinct.'));return;}
 if(sameNat)P.appendChild(el('div','vitem PASS','ZERO-ADDITIONAL-LOSS SHARING CANDIDATE (same natural Genesis color).'));
 else P.appendChild(el('div','vitem WARN','No MRD edge → may share a target. Choose a compromise:'));
 const comp=bestCompromise(a.arcade_rgb8,b.arcade_rgb8);
 [['Keep A quant',a.genesis_cram],['Keep B quant',b.genesis_cram],['Best legal compromise',comp.cram]].forEach(([lbl,cram])=>{const rgb=cramToRGB(cram);const b2=el('button',null,lbl+' '+cram);b2.onclick=()=>{if(!TGT)return alert('Pick a target entry first (right).');pushUndo();POL.target_palette_lines[TGT.line][TGT.index]=cram;afterChange();showTarget();};const s=swBox(rgb);s.style.display='inline-block';s.style.verticalAlign='middle';const wrap=el('div');wrap.appendChild(b2);wrap.appendChild(s);P.appendChild(wrap);});
 P.appendChild(txt(`compromise ΔE00(A)=${comp.dA.toFixed(2)} ΔE00(B)=${comp.dB.toFixed(2)} worst=${comp.worst.toFixed(2)} (minimizes worst-case)`));}
function bestCompromise(a,b){let best=null;for(let R=0;R<8;R++)for(let G=0;G<8;G++)for(let B=0;B<8;B++){const rgb=[LV[R],LV[G],LV[B]];const dA=deltaE00(a,rgb),dB=deltaE00(b,rgb),worst=Math.max(dA,dB);if(!best||worst<best.worst)best={cram:'0x'+(((B<<9)|(G<<5)|(R<<1))>>>0).toString(16).padStart(4,'0').toUpperCase(),dA,dB,worst};}return best;}

let ZOOM=(function(){try{return +localStorage.getItem('rz_zoom')||4;}catch(e){return 4;}})();
let SHOWB=false;
function setZoom(z){ZOOM=z;try{localStorage.setItem('rz_zoom',z);}catch(e){}renderPreviews();}
async function renderPreviews(){const P=$('#previews');P.innerHTML='';if(!U)return;
 const uid=encodeURIComponent(U.usage_id),bw=U.bounds[0];
 // zoom bar
 const zb=el('div','zoombar');zb.appendChild(el('span','dim','zoom: '));
 [['Fit','fit'],['1×',1],['2×',2],['4×',4],['8×',8]].forEach(([lbl,z])=>{const b=el('button','mini'+(z===ZOOM?' on':''),lbl);b.onclick=()=>setZoom(z==='fit'?'fit':z);zb.appendChild(b);});
 const bm=el('button','mini','−');bm.onclick=()=>setZoom(Math.max(1,(ZOOM==='fit'?4:ZOOM)-1));zb.appendChild(bm);
 const bp=el('button','mini','+');bp.onclick=()=>setZoom((ZOOM==='fit'?4:ZOOM)+1);zb.appendChild(bp);
 const cb=el('label','dim');const ck=el('input');ck.type='checkbox';ck.checked=SHOWB;ck.onchange=()=>{SHOWB=ck.checked;renderPreviews();};cb.appendChild(ck);cb.appendChild(el('span',null,' piece boundaries'));zb.appendChild(cb);
 const zlab=el('span','dim','  '+U.preview_type+' · '+U.n_pieces+' pieces · bank '+U.sprite_bank);zb.appendChild(zlab);
 P.appendChild(zb);
 const b=SHOWB?'&boundaries=1':'';const AVAIL=300;
 // uniform integer scale from the ACTUAL native PNG dims (source & target are identical geometry)
 function sizeImg(img){const nW=img.naturalWidth,nH=img.naturalHeight;let Z=ZOOM;
   if(Z==='fit'){Z=Math.max(1,Math.floor(Math.min(AVAIL/nW,AVAIL/nH)));}
   img.style.width=(nW*Z)+'px';img.style.height=(nH*Z)+'px';  // BOTH dims, same scalar
   zlab.textContent=`  zoom: ${ZOOM==='fit'?'Fit('+Z+'×)':Z+'×'} · display ${nW*Z}×${nH*Z}px · source ${nW}×${nH}px · ${U.preview_type} · ${U.n_pieces} pieces`;}
 const s=el('div','pv');s.appendChild(el('div','pvh',(U.composite_proven?'TRUE ARCADE COMPOSITE':'PROVEN CELL SHEET — NOT COMPOSITE')));
 const i1=new Image();i1.className='pimg';i1.onload=()=>sizeImg(i1);i1.src=`/api/render?usage=${uid}${b}`;s.appendChild(i1);P.appendChild(s);
 const map=POL.usage_palette_mappings[MK(U)];const pal=[[0,0,0]];for(let i=1;i<16;i++)pal[i]=[60,60,72];
 U.used_colors.forEach(c=>{let rgb=c.genesis_rgb8;if(map&&map.index_map[c.src_index]!=null){const cr=tcram(map.line,map.index_map[c.src_index]);const g=cramToRGB(cr);if(g)rgb=g;}pal[c.src_index]=rgb;});
 const t=el('div','pv');t.appendChild(el('div','pvh','GENESIS TARGET (same geometry, mapped colors) — click a pixel to pick its CRAM entry'));
 const i2=new Image();i2.className='pimg pickable';i2.onload=()=>sizeImg(i2);i2.src=`/api/render?usage=${uid}&target=${encodeURIComponent(JSON.stringify(pal))}${b}`;
 i2.onclick=e=>spritePixelPick(e,i2);t.appendChild(i2);P.appendChild(t);}
let _HIT={};
async function spritePixelPick(e,img){if(!U)return;const rc=img.getBoundingClientRect();
 const nx=Math.floor((e.clientX-rc.left)/rc.width*img.naturalWidth),ny=Math.floor((e.clientY-rc.top)/rc.height*img.naturalHeight);
 if(!_HIT[U.usage_id])_HIT[U.usage_id]=await j('/api/hitmap?usage='+encodeURIComponent(U.usage_id));
 const hm=_HIT[U.usage_id];if(nx<0||ny<0||nx>=hm.w||ny>=hm.h)return;const vi=hm.idx[ny*hm.w+nx];
 if(!vi){$('#status').textContent='Transparent pixel — no palette entry';return;}
 const map=POL.usage_palette_mappings[MK(U)];SRC=(U.used_colors.find(c=>c.src_index===vi))||SRC;
 if(map&&map.index_map[vi]!=null){TGT={line:map.line,index:map.index_map[vi]};ACTIVE=map.line;renderTarget();showTarget();$('#status').textContent=`picked ${U.display_name} src i${vi} → L${map.line}:${map.index_map[vi]}`;}
 else{renderSource();$('#status').textContent=`clicked ${U.display_name} src i${vi} (unmapped) — selected as source color`;}}

function ctxCoverage(c){return /r01\.p01/.test(c.id)||c.id==='context:gameplay.r01.p01'?'COMPLETE':/r01(\.|$)|gameplay$|^context:game$/.test(c.id)?'PARTIAL':'UNKNOWN';}
function selectContext(id){SCOPE=id;renderScopeBar();renderList();renderContextInfo(id);renderTarget();
 const seg=scopeSegment();$('#status').textContent='editing scope → '+ctxName(id)+(seg!=null?' (segment '+seg+')':'');}
function renderContextInfo(id){const c=ctxById(id);if(!c)return;const P=$('#props');P.innerHTML='';
 const cp=(POL.context_policies||{})[id];let nlocal=0;if(cp&&cp.tpl)Object.values(cp.tpl).forEach(l=>nlocal+=Object.keys(l).length);
 const cov=ctxCoverage(c);const seg=scopeSegment();
 P.appendChild(txt(`CONTEXT\nName: ${c.display||c.id}\nStable ID: ${c.id}\nParent: ${c.parent||'—'}\nEditing scope: ACTIVE\nSource coverage: ${cov}\nPalette evidence: ${cov}\nEditable policy: YES\nInherits from: ${ctxChain(id).slice(0,-1).map(x=>x.display).join(' → ')||'(root)'}\nLocal overrides: ${nlocal}`));
 if(cov==='UNKNOWN')P.appendChild(el('div','vitem WARN','CORPUS INCOMPLETE / NOT YET PROVEN FOR THIS CONTEXT — R1/P1 evidence is not authoritative here.'));
 if(seg!=null)mkbtn(P,'Open Segment '+seg+' map (Layer A)',()=>{TAB='layera';document.querySelectorAll('.tabs button').forEach(x=>x.classList.toggle('on',x.dataset.t==='layera'));LAVIEW='map';LAMAPSEG=seg;renderList();});
 if(nlocal)mkbtn(P,'Reset local overrides ('+nlocal+')',()=>{pushUndo();delete POL.context_policies[id];afterChange();renderContextInfo(id);});
 mkbtn(P,'Create full local copy (Lines 0/1/3)',()=>{pushUndo();const cp=ctxPolicies();cp[id]=cp[id]||{tpl:{}};editableLines().forEach(l=>{cp[id].tpl[l]=cp[id].tpl[l]||{};for(let i=1;i<16;i++){const v=effEntry(l,i).cram;if(v!=null)cp[id].tpl[l][i]=v;}});afterChange();renderContextInfo(id);});}
function ctxFit(c){const seg=O.coexistence.layer_a_active_banks_per_segment||{};let maxA=0;Object.values(seg).forEach(a=>maxA=Math.max(maxA,a.length));
 const P=$('#props');P.innerHTML='';P.appendChild(txt(`CONTEXT: ${c.display||c.id}\nTARGET PALETTE FIT\nLines used: ${POL.target_palette_lines.filter(l=>l.some(x=>x!=null)).length} / 4\n`+POL.target_palette_lines.map((l,i)=>`  Line ${i}: ${l.filter((x,k)=>x!=null&&k!==0).length} / 15 entries`).join('\n')+`\nmax simultaneous Layer-A banks (real): ${maxA} + 1 Layer-B\nUNKNOWN objects: ${O.objects.filter(o=>statusOf(o)!=='PROVEN').length}`));}
function showPaletteResource(p){const P=$('#props');P.innerHTML='';const dg=Object.values(O.exact_duplicate_palette_groups).find(g=>g.includes(p.palette_id));
 P.appendChild(txt(`PALETTE RESOURCE ${p.palette_id}\nselector ${p.arcade_selector} · domain ${p.domain}\ncontent_id ${p.content_id}`));
 if(dg)P.appendChild(el('div','vitem PASS','LOSSLESS SHARING OPPORTUNITY — identical content: '+dg.join(', ')));}

function closestInLine(c,line){/* nearest populated entry by ΔE00; nearest LEGAL (no MRD conflict for current usage U) */
 let abs=null,legal=null;
 for(let i=1;i<16;i++){const cram=tcram(line,i);if(cram==null)continue;const de=deltaE00(c.arcade_rgb8,cramToRGB(cram));
  if(abs===null||de<abs.de)abs={index:i,de};
  // legal if mapping c here won't collide with an MRD partner of c already mapped here (same usage U)
  let ok=true;if(U){const m=POL.usage_palette_mappings[MK(U)];if(m&&m.line===line){for(const[si,ti]of Object.entries(m.index_map)){if(+ti===i&&+si!==c.src_index&&U.mrd_pairs.some(([a,b])=>(a===+si&&b===c.src_index)||(b===+si&&a===c.src_index))){ok=false;break;}}}}
  if(ok&&(legal===null||de<legal.de))legal={index:i,de};}
 return {absolute:abs,legal};}
async function solveGroup(fitActive,mode){if(!GROUP.size)return alert('check 1+ objects');$('#status').textContent='solving…';
 const sol=await j('/api/solve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({usage_ids:[...GROUP],mode:mode||'delta_e'})});
 SOLUTION=sol;const P=$('#props');P.innerHTML='';
 const nm=sol.solver==='luminance_hue'?'LUMINANCE/HUE':'ΔE PERCEPTUAL';
 const maxdL=Math.max(...sol.entries.flatMap(e=>e.members.map(m=>m.dL)),0);
 const maxSpread=Math.max(...sol.entries.map(e=>e.hue_spread||0),0);
 const nd=(sol.palette_domains||[]).length,nr=(sol.preview_representations||[]).length;
 P.appendChild(txt(`${nm} SHARED PALETTE\nPalette domains selected: ${nd}${nr>nd?'  (preview representations: '+nr+')':''}\nsolver: ${sol.solver}\nfeasible in one line: ${sol.feasible?'YES':'NO'}\none-line capacity: ${sol.one_line_capacity||15}\nsafe entries required: ${sol.safe_entries_required||sol.entries_used}\ncross-object shared entries: ${sol.entries.filter(e=>e.members.length>1).length}\nworst ΔL (OKLab): ${maxdL.toFixed(4)}\nMRD violations: 0 (guaranteed)${sol.settings?'\nhue-limit '+sol.settings.hue_limit+'° · ΔE-limit '+sol.settings.de_limit+' · hue-tol ±'+sol.settings.hue_tol+'°':''}`));
 if(!sol.feasible){P.appendChild(el('div','vitem ERROR',`NO ACCEPTABLE ONE-LINE SOLUTION — needs ${sol.safe_entries_required} hue-safe entries (capacity ${sol.one_line_capacity}). All shown clusters are hue-safe; no colors were destroyed to force a fit.`));}
 // per-object quality (Part 10 + imbalance warning)
 const worsts=Object.entries(sol.per_object).map(([u,m])=>{const nm=(O.usages.find(x=>x.usage_id===u)||{}).display_name||u;return {nm,w:m.worst_de,wm:m.wmean_de};});
 worsts.forEach(o=>P.appendChild(el('div','vitem '+(o.w<=3?'PASS':o.w<=8?'WARN':'ERROR'),`${o.nm}: worst ΔE ${o.w} · wmean ${o.wm}`)));
 const mx=Math.max(...worsts.map(o=>o.w)),mn=Math.min(...worsts.map(o=>o.w));if(mx-mn>4)P.appendChild(el('div','vitem ERROR','QUALITY IMBALANCE — one object degraded much more than others.'));
 if(!sol.feasible){P.appendChild(el('div','vitem ERROR','Cannot fit one line without losing internal detail. (Two-line split = future.)'));return;}
 editableLines().forEach(line=>{const b=el('button',null,'Apply to Line '+line);b.onclick=()=>applySolution(sol,line);P.appendChild(b);});
 // preview each object with proposed palette
 const PV=$('#previews');PV.innerHTML='';PV.appendChild(el('div','pvh','SHARED PALETTE — per-object preview (arcade left / proposed right)'));
 GROUP.forEach(uid=>{const u=O.usages.find(x=>x.usage_id===uid);if(!u)return;const pal=proposedPal(sol,u);
  const wrap=el('div','pv');wrap.appendChild(el('div','pvh',u.display_name));
  const a=new Image();a.className='pimg';a.style.height='90px';a.src='/api/render?usage='+encodeURIComponent(uid);wrap.appendChild(a);
  const g=new Image();g.className='pimg';g.style.height='90px';g.src='/api/render?usage='+encodeURIComponent(uid)+'&target='+encodeURIComponent(JSON.stringify(pal));wrap.appendChild(g);PV.appendChild(wrap);});}
function proposedPal(sol,u){const pal=[[0,0,0]];for(let i=1;i<16;i++)pal[i]=[50,50,60];
 sol.entries.forEach(e=>{e.members.forEach(m=>{if(m.usage_id===u.usage_id)pal[m.src_index]=cramToRGB(e.cram);});});return pal;}
function applySolution(sol,line){if(POL.immutable)return alert('Create an editable profile first.');if(guardProtected(line))return;pushUndo();
 // one Undo transaction: set target line entries + remap each group usage
 sol.entries.forEach(e=>{POL.target_palette_lines[line][e.target_index]=e.cram;});
 GROUP.forEach(uid=>{const u=O.usages.find(x=>x.usage_id===uid);const k=MK(u)||uid;const m=POL.usage_palette_mappings[k]={line,index_map:{}};sol.entries.forEach(e=>e.members.forEach(mm=>{if(mm.usage_id===uid)m.index_map[mm.src_index]=e.target_index;}));POL.usage_palette_mappings[k].solver=sol.solver;});
 ACTIVE=line;$('#status').textContent='applied '+(sol.solver||'')+' shared palette → Line '+line+' ('+GROUP.size+' objects, 1 undo)';afterChange();}
async function compareSolvers(){if(!GROUP.size)return alert('check 1+ objects');$('#status').textContent='comparing solvers…';
 const ids=[...GROUP];
 const de=await j('/api/solve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({usage_ids:ids,mode:'delta_e'})});
 const lh=await j('/api/solve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({usage_ids:ids,mode:'luminance_hue'})});
 const mx=(s,k)=>Math.max(...s.entries.flatMap(e=>e.members.map(m=>m[k])),0);
 const mean=(s,k)=>{const a=s.entries.flatMap(e=>e.members.map(m=>m[k]));return a.reduce((x,y)=>x+y,0)/a.length;};
 const P=$('#props');P.innerHTML='';
 P.appendChild(txt(`COMPARE SOLVERS (${GROUP.size} objects)\n\n           ΔE SHARED   LUMINANCE/HUE\nentries    ${de.entries_used}          ${lh.entries_used}\nworst ΔE   ${mx(de,'de').toFixed(2)}       ${mx(lh,'de').toFixed(2)}\nmean ΔE    ${mean(de,'de').toFixed(2)}       ${mean(lh,'de').toFixed(2)}\nworst ΔL   ${mx(de,'dL').toFixed(4)}     ${mx(lh,'dL').toFixed(4)}\nmean ΔL    ${mean(de,'dL').toFixed(4)}     ${mean(lh,'dL').toFixed(4)}`));
 P.appendChild(el('div','vitem PASS','Luminance/Hue trades ΔE for better lightness (ΔL). Neither is universally better — compare the previews.'));
 mkbtn(P,'Use ΔE proposal',()=>{SOLUTION=de;solveGroupShow(de);});mkbtn(P,'Use Luminance/Hue proposal',()=>{SOLUTION=lh;solveGroupShow(lh);});
 // 3-column previews: arcade | ΔE | L/H
 const PV=$('#previews');PV.innerHTML='';PV.appendChild(el('div','pvh','ARCADE  |  ΔE SHARED  |  LUMINANCE/HUE'));
 ids.forEach(uid=>{const u=O.usages.find(x=>x.usage_id===uid);if(!u)return;const row=el('div','pv');row.appendChild(el('div','pvh',u.display_name));
  [['',null],['ΔE',de],['L/H',lh]].forEach(([lbl,sol])=>{const im=new Image();im.className='pimg';im.style.height='84px';
   im.src=sol?('/api/render?usage='+encodeURIComponent(uid)+'&target='+encodeURIComponent(JSON.stringify(proposedPal(sol,u)))):('/api/render?usage='+encodeURIComponent(uid));row.appendChild(im);});PV.appendChild(row);});
 $('#status').textContent='solver comparison ready';}
function solveGroupShow(sol){SOLUTION=sol;const P=$('#props');P.innerHTML='';P.appendChild(txt('Selected proposal: '+sol.solver+' · entries '+sol.entries_used));editableLines().forEach(line=>{const b=el('button',null,'Apply to Line '+line);b.onclick=()=>applySolution(sol,line);P.appendChild(b);});}
function txt(s){return el('div','mono',s);}
function validate(){const V=$('#valid');V.innerHTML='';let err=0;
 // MRD violations across all usages
 let mrdV=0;for(const[uid,m]of Object.entries(POL.usage_palette_mappings)){const u=usageByMapKey(uid)||O.usages.find(x=>x.usage_id===uid);if(!u)continue;for(const[a,b]of u.mrd_pairs){if(m.index_map[a]!=null&&m.index_map[a]===m.index_map[b])mrdV++;}}
 if(mrdV){V.appendChild(el('div','vitem ERROR',`MRD violations (internal detail merged): ${mrdV}`));err++;}else V.appendChild(el('div','vitem PASS','MRD: 0 internal-detail merges'));
 const linesUsed=POL.target_palette_lines.filter(l=>l.some(x=>x!=null)).length;
 V.appendChild(el('div','vitem '+(linesUsed<=4?'PASS':'ERROR'),`target lines used: ${linesUsed}/4`));
 POL.target_palette_lines.forEach((l,i)=>{const n=l.filter((x,k)=>x!=null&&k!==0).length;if(n>15){V.appendChild(el('div','vitem ERROR',`Line ${i}: ${n}/15 nontransparent (overflow)`));err++;}});
 const maps=Object.keys(POL.usage_palette_mappings).length;V.appendChild(el('div','vitem '+(err?'ERROR':'PASS'),`usages mapped: ${maps} · errors: ${err}`));}
// ================= LAYER A workspace =================
let LA=null,LAP=new Set(),LADET=null,LAUSAGE=null,LAZOOM=4,LAPAGE=0,LASRC=null;
let ACTIVE_SCENE=null,LA_SCENE=undefined,SCENE_RECORDS=null,PR_EV=undefined,SPR_COV={};
function sceneQS(pfx){return ACTIVE_SCENE?(pfx+'scene='+encodeURIComponent(ACTIVE_SCENE)):'';}
let LAVIEW='library',LAMAPSEG=null,LAMAP=null,LAMAPZOOM=1,LAMAPMODE='arcade',LAMAPGRID=false,LAMAPSEL=null;
const LAFILT={q:'',seg:'',bank:'',pal:'',map:'',anim:''};
const LAPP=200;
window.loadSubroundScene=function(sceneKey,records){ACTIVE_SCENE=sceneKey||null;SCENE_RECORDS=(records&&records.length===2)?records:null;
 // Set the editing SCOPE to the scene's INDEPENDENT context so Genesis Lines 0/1/3 author per subround.
 // PROMPT-ID-0009: a real subround selection NEVER falls back to r01.p01 (that leaked R1-S2 edits into
 // R1-S1). Only the explicit R1-S1 outdoor scene authors on the r01.p01 phase node; every other scene
 // authors on its OWN scene-key context (isolated), and deselecting returns to r01.p01.
 if(sceneKey){SCOPE=(sceneKey==='PAL-R1-S1-PLANEA-OUTDOOR')?'context:gameplay.r01.p01':sceneKey;}
 else{SCOPE='context:gameplay.r01.p01';}
 LA=null;LAMAP=null;LADET=null;LAUSAGE=null;LAP.clear();LAMAPSEG=SCENE_RECORDS?SCENE_RECORDS[0]:0;LAVIEW='map';TAB='layera';document.querySelectorAll('.tabs button').forEach(x=>x.classList.toggle('on',x.dataset.t==='layera'));renderScopeBar();renderTarget();renderList();};
async function renderLayerA(L){
 if(!LA||LA_SCENE!==ACTIVE_SCENE){L.innerHTML='<div class="dim">Loading Layer-A corpus…</div>';LA=await j('/api/layera'+sceneQS('?'));LA_SCENE=ACTIVE_SCENE;}
 if(!POL.plane_usage_palette_mappings)POL.plane_usage_palette_mappings={};
 L.innerHTML='';const c=LA.counts;
 // PROMPT-ID-0006 Req 1: honest per-round palette disclosure for R2+ scenes (no "verified" claim).
 const _m=(ACTIVE_SCENE||'').match(/^PAL-R(\d+)-/);
 if(_m&&(+_m[1])>=2){
  if(PR_EV===undefined){PR_EV=null;try{PR_EV=await j('/api/per_round_evidence');}catch(e){PR_EV=null;}}
  const nb=el('div','warn');nb.style.cssText='border:1px solid #a86;background:#1c1710;color:#d9c9a0;padding:6px 8px;margin:4px 0;font-size:12px;border-radius:4px;';
  nb.textContent='Round '+_m[1]+': arcade colors are derived from the PROVEN round-independent base (0x4EAF6). '
   +'A genuine Round-2+ live capture could not be reproduced, so a per-round reload of these banks is '
   +'UNCONFIRMED — colors are not fabricated and not claimed verified. See per_round_palette_evidence.json.';
  L.appendChild(nb);
 }
 // Segment Map | Tile Library view toggle; auto-open the scope's segment on entry
 const seg=scopeSegment();if(seg!=null&&LAMAPSEG==null){LAMAPSEG=seg;LAVIEW='map';}
 const vt=el('div','groupbar');['map','library'].forEach(v=>{const b=el('button','mini'+(LAVIEW===v?' on':''),v==='map'?'Segment Map':'Tile Library');b.onclick=()=>{LAVIEW=v;renderLayerA($('#list'));};vt.appendChild(b);});L.appendChild(vt);
 if(LAVIEW==='map'){const ms=el('div','line');ms.appendChild(el('span','lbl','Segment'));const s=el('select');{const _r=SCENE_RECORDS||[0,15];for(let i=_r[0];i<=_r[1];i++)s.appendChild(new Option((ACTIVE_SCENE?'record ':'segment ')+i,i));}s.value=(LAMAPSEG!=null?LAMAPSEG:(SCENE_RECORDS?SCENE_RECORDS[0]:(seg!=null?seg:0)));s.onchange=()=>{LAMAPSEG=+s.value;LAMAP=null;renderSegMap();};ms.appendChild(s);L.appendChild(ms);
  const mv=el('div','zoombar');['arcade','genesis'].forEach(m=>{const b=el('button','mini'+(LAMAPMODE===m?' on':''),m==='arcade'?'Arcade':'Genesis');b.onclick=()=>{LAMAPMODE=m;renderSegMap();};mv.appendChild(b);});L.appendChild(mv);
  const zz=el('div','zoombar');zz.appendChild(el('span','dim','map zoom '));[1,2,4].forEach(z=>{const b=el('button','mini'+(LAMAPZOOM===z?' on':''),z+'×');b.onclick=()=>{LAMAPZOOM=z;renderSegMap();};zz.appendChild(b);});
   const gl=el('label','dim');const gk=el('input');gk.type='checkbox';gk.checked=LAMAPGRID;gk.onchange=()=>{LAMAPGRID=gk.checked;renderSegMap();};gl.appendChild(gk);gl.appendChild(el('span',null,' tile boundaries'));zz.appendChild(gl);L.appendChild(zz);}
 L.appendChild(txt(`LAYER A CORPUS\nphysical patterns: ${c.physical_patterns}\nlogical usages: ${c.logical_usages}\npalette banks: ${c.palette_banks}\nmulti-palette: ${c.multi_palette_patterns}`));
 // scene/phase auto-map to the active editable line (existing colors only) — PROMPT-ID-0009
 const ph=automapContext();const canPhase=ph&&!isProtected(ACTIVE)&&editableLines().includes(ACTIVE);
 const isScene=ph&&ph.kind==='scene';const amName=ph?ctxName(ph.id):'';
 const pbar=el('div','groupbar');
 const pbtn=el('button','act',(isScene?'Auto-map Current Scene':'Auto-map Phase')+' → Line '+ACTIVE);pbtn.disabled=!canPhase;
 pbtn.title=canPhase?('Map ALL Layer-A usages in '+amName+(isScene?' ['+ph.id+']':'')+' to the existing colors on Line '+ACTIVE):(isProtected(ACTIVE)?'Line 2 is protected — pick Line 0/1/3':(ph?'Select an editable Genesis line (0/1/3) first':'No safe auto-map scope for this selection'));
 pbtn.onclick=()=>phaseAutoMap(ph,ACTIVE);pbar.appendChild(pbtn);
 pbar.appendChild(el('div','dim',canPhase?(amName+(isScene?' ['+ph.id+']':'')+' · Line '+ACTIVE+' · existing colors only'):'Pick an editable line (click LINE 0/1/3 label at right)'));
 L.appendChild(pbar);
 // PROMPT-ID-0010: one-click whole-scene derive — closest Genesis palette for EVERY usage across all
 // banks, packed into Lines 0/1/3, then mapped. No per-usage checkbox hunting.
 const dbar=el('div','groupbar');
 const canDerive=ph&&!isProtected(ACTIVE)&&editableLines().includes(ACTIVE);
 const l2reuse=ph&&isProtected(ACTIVE)&&POL.line2_display&&POL.line2_display.cram;   // Line 2 = reuse Layer B
 const canAny=canDerive||l2reuse;
 const dbtn=el('button','act',l2reuse?('Map Scene → Line '+ACTIVE+' (reuse Layer B)'):('Derive Scene Palette → Line '+ACTIVE));dbtn.disabled=!canAny;
 dbtn.title=canAny?(l2reuse?('Bulk-map the remaining Plane-A banks onto Line 2\'s EXISTING Layer-B colors — reuse only, never changes Line 2, MRD-safe'):('Derive the closest Genesis palette for the ENTIRE '+amName+' tileset onto Line '+ACTIVE+' (banks that do not fit 15 colors are reported, never merged)')):(ph?'Select a Genesis line (0/1/3, or 2 to reuse Layer B) at right first':'Open a subround scene first');
 dbtn.onclick=()=>deriveScenePalette(ACTIVE);dbar.appendChild(dbtn);
 dbar.appendChild(el('div','dim',canAny?(l2reuse?('remaining banks → Line 2 (reuse Layer B) · one Undo · '+amName):('whole tileset → Line '+ACTIVE+' · one Undo · scoped to '+amName)):'Pick a line (click LINE 0/1/3, or 2 to reuse Layer B, at right)'));
 L.appendChild(dbar);
 // Clear the active line (colors + mappings) at this scope — isolated from other subrounds.
 const cbar=el('div','groupbar');
 const cbtn=el('button','mini','Clear Line '+ACTIVE);cbtn.disabled=isProtected(ACTIVE)||!editableLines().includes(ACTIVE);
 cbtn.title=isProtected(ACTIVE)?'Line 2 is protected':('Remove ALL colors + mappings on Line '+ACTIVE+' at '+ctxName(SCOPE)+' (other subrounds keep theirs)');
 cbtn.onclick=()=>clearLine(ACTIVE);cbar.appendChild(cbtn);
 cbar.appendChild(el('div','dim',isProtected(ACTIVE)?'Line 2 protected':('empties Line '+ACTIVE+' at '+ctxName(SCOPE)+' · one Undo')));
 L.appendChild(cbar);
 // Move ONLY the filtered bank to the active line (overrides its current mapping). Use the Bank filter
 // below to pick the bank (e.g. the flame bank), then move it to Line 2 (reuse) or Line 0/1/3.
 if(ph&&LAFILT.bank){
  const bbar=el('div','groupbar');
  const bbtn=el('button','mini','Move Bank '+LAFILT.bank+' → Line '+ACTIVE+(l2reuse?' (reuse)':''));
  bbtn.disabled=!canAny;
  bbtn.title=canAny?('Remap ONLY bank '+LAFILT.bank+'\'s tiles to Line '+ACTIVE+' — moves them off whatever line they are on now'):'Pick a line (0/1/3, or 2 to reuse Layer B) first';
  bbtn.onclick=()=>deriveScenePalette(ACTIVE,LAFILT.bank);bbar.appendChild(bbtn);
  bbar.appendChild(el('div','dim','moves bank '+LAFILT.bank+' → Line '+ACTIVE+' · overrides its current line · one Undo'));
  L.appendChild(bbar);
 }
 const q=el('input');q.placeholder='search id / code / hash / usage';q.value=LAFILT.q;q.style.width='96%';q.oninput=()=>{LAFILT.q=q.value;LAPAGE=0;renderLAGrid();};L.appendChild(q);
 const mk=(lbl,key,opts)=>{const w=el('div','line');w.appendChild(el('span','lbl',lbl));const s=el('select');s.appendChild(new Option('(all)',''));opts.forEach(o=>s.appendChild(new Option(o[1],o[0])));s.value=LAFILT[key];s.onchange=()=>{LAFILT[key]=s.value;LAPAGE=0;renderLAGrid();};w.appendChild(s);L.appendChild(w);};
 mk('Segment','seg',(()=>{const _r=SCENE_RECORDS||[0,15],o=[];for(let i=_r[0];i<=_r[1];i++)o.push([''+i,(ACTIVE_SCENE?'rec ':'seg ')+i]);return o;})());
 mk('Bank','bank',LA.bank_ids.map(b=>[b,b]));
 mk('Pal use','pal',[['single','single-palette'],['multi','multi-palette']]);
 mk('Mapping','map',[['unmapped','unmapped'],['partial','partial'],['mapped','mapped']]);
 mk('Variation','anim',[['STATIC','static'],['MULTI-PALETTE','multi-palette'],['UNKNOWN','unknown']]);
 const gb=el('div','groupbar');gb.appendChild(el('span','dim','Layer-A group: '+LAP.size+' '));
 if(LAP.size>=1){mkbtn(gb,'Derive Shared Palette',()=>solveLA('delta_e'));mkbtn(gb,'Derive Luminance/Hue',()=>solveLA('luminance_hue'));mkbtn(gb,'Clear',()=>{LAP.clear();renderLayerA($('#list'));});}
 L.appendChild(gb);
 const zb=el('div','zoombar');zb.appendChild(el('span','dim','tile zoom '));[4,8,16,32].forEach(z=>{const b=el('button','mini'+(z===LAZOOM?' on':''),z+'×');b.onclick=()=>{LAZOOM=z;renderLAGrid();};zb.appendChild(b);});L.appendChild(zb);
 renderTarget();
 if(LAVIEW==='map')renderSegMap();
 else if(LADET)renderLADetail();else renderLAGrid();
}
async function renderSegMap(){const seg=(LAMAPSEG!=null?LAMAPSEG:scopeSegment()||0);const C=$('#center');
 if(!LAMAP||LAMAP.seg!==seg||LAMAP._scene!==ACTIVE_SCENE){C.innerHTML='<div class="dim">Assembling record '+seg+' map from arcade data…</div>';LAMAP=await j('/api/layera_map?seg='+seg+sceneQS('&'));LAMAP._scene=ACTIVE_SCENE;}
 C.innerHTML='';const head=el('div','labar');head.appendChild(el('b',null,`${ACTIVE_SCENE?ACTIVE_SCENE+' ':'R1/P1 '}record ${seg} — ${LAMAPMODE} map`));
 head.appendChild(el('span','dim',`  complete ${LAMAP.cols}×${LAMAP.rows} backing tilemap · nonblank ${LAMAP.nonblank_cells} · resolved ${LAMAP.resolved} · blank ${LAMAP.blank_cells} · unresolved ${LAMAP.unresolved}`));C.appendChild(head);
 const Z=LAMAPZOOM,W=LAMAP.cols*8*Z,H=LAMAP.nrows*8*Z;const cv=el('canvas');cv.width=W;cv.height=H;cv.className='segcanvas';C.appendChild(cv);
 const ctx=cv.getContext('2d');const img=ctx.createImageData(LAMAP.cols*8,LAMAP.nrows*8);const D=img.data;
 const put=(x,y,rgb)=>{const o=(y*LAMAP.cols*8+x)*4;D[o]=rgb[0];D[o+1]=rgb[1];D[o+2]=rgb[2];D[o+3]=255;};
 LAMAP.cells.forEach(cell=>{const px=LAMAP.tiles[cell.code+'']||LAMAP.tiles[String(cell.code)];if(!px)return;
  const bankcols=LA.banks[cell.bank];const gen=(LAMAPMODE==='genesis'&&cell.uid)?laGenPalByUsage(cell.uid,cell.bank):null;
  for(let ty=0;ty<8;ty++)for(let tx=0;tx<8;tx++){const sx=cell.hf?7-tx:tx,sy=cell.vf?7-ty:ty;const v=px[sy*8+sx];
   let rgb;if(v===0)rgb=[24,24,30];else if(gen)rgb=gen[v]||[60,60,72];else rgb=(bankcols&&bankcols[v])||[255,0,255];
   put(cell.c*8+tx,cell.r*8+ty,rgb);}});
 // scale up nearest-neighbor into the canvas
 const tmp=document.createElement('canvas');tmp.width=LAMAP.cols*8;tmp.height=LAMAP.nrows*8;tmp.getContext('2d').putImageData(img,0,0);
 ctx.imageSmoothingEnabled=false;ctx.drawImage(tmp,0,0,W,H);
 if(LAMAPGRID){ctx.strokeStyle='rgba(120,120,150,.4)';for(let x=0;x<=LAMAP.cols;x++){ctx.beginPath();ctx.moveTo(x*8*Z,0);ctx.lineTo(x*8*Z,H);ctx.stroke();}for(let y=0;y<=LAMAP.nrows;y++){ctx.beginPath();ctx.moveTo(0,y*8*Z);ctx.lineTo(W,y*8*Z);ctx.stroke();}}
 if(LAMAP.visible_viewport){ctx.strokeStyle='rgba(120,200,255,.55)';ctx.lineWidth=2;ctx.strokeRect(0,LAMAP.visible_viewport.row0*8*Z,W,LAMAP.visible_viewport.nrows*8*Z);}
 if(LAMAPSEL){ctx.strokeStyle='#ffcf6b';ctx.lineWidth=2;ctx.strokeRect(LAMAPSEL.c*8*Z,LAMAPSEL.r*8*Z,8*Z,8*Z);}
 const cellAt=e=>{const rc=cv.getBoundingClientRect();const cx=Math.floor((e.clientX-rc.left)/(8*Z)),cy=Math.floor((e.clientY-rc.top)/(8*Z));return LAMAP.cells.find(k=>k.c===cx&&k.r===cy)||null;};
 cv.onmousemove=e=>{const k=cellAt(e);const t=$('#status');if(k)t.textContent=`seg ${seg} cell X${k.c} Y${k.r} · ${k.pid||'?'} · ${k.uid||'UNMAPPED'} · code 0x${k.code.toString(16).toUpperCase()} · bank ${k.bank} · flip ${k.hf}${k.vf}`;};
 cv.onclick=e=>{const k=cellAt(e);if(!k)return;LAMAPSEL=k;mapInspect(k,seg);if(!k.uid)return;
  // pixel-pick in genesis mode: resolve clicked pixel -> source index -> target entry
  if(LAMAPMODE==='genesis'){const rc=cv.getBoundingClientRect();const lx=Math.floor(((e.clientX-rc.left)/(Z))-k.c*8),ly=Math.floor(((e.clientY-rc.top)/(Z))-k.r*8);const px=LAMAP.tiles[k.code+''];const sx=k.hf?7-lx:lx,sy=k.vf?7-ly:ly;const vi=px?px[sy*8+sx]:0;if(vi){pickLayerTarget(k.uid,vi);}}
  openLAPatternUsage(k.pid,k.uid);};
 // occurrence count for the selected physical pattern
 if(LAMAPSEL){const occ=LAMAP.cells.filter(k=>k.pid===LAMAPSEL.pid).length;const info=el('div','vitem PASS',`Selected ${LAMAPSEL.pid} · this physical pattern occurs ${occ} time(s) in segment ${seg}.`);C.appendChild(info);}
 C.appendChild(el('div','dim','Click a tile: opens its exact logical usage + palette variant. In Genesis mode, clicking a pixel also selects its target CRAM entry. Line 2 stays protected.'));}
async function phaseAutoMap(ph,line){
 if(!ph)return alert('No safe auto-map scope is active for this selection. Open a subround scene or a phase context first.');
 if(POL.immutable)return alert('Create an editable profile first.');if(guardProtected(line))return;
 const destId=ph.id, reqScene=ph.scene||null, isScene=ph.kind==='scene', label=ctxName(destId)+(isScene?' ['+destId+']':'');
 // effective target colors for this line at the DESTINATION scope (restore SCOPE immediately — no side effect)
 const savedScope=SCOPE;SCOPE=destId;const cols=[null];for(let i=1;i<16;i++)cols[i]=tcram(line,i);SCOPE=savedScope;
 const npop=cols.filter((x,i)=>i>0&&x).length;
 if(!npop)return alert('Line '+line+' has no populated colors. Author the palette on that line first.');
 // snapshot the scene identity so an async result can never be applied to a DIFFERENT scene (Req 3)
 const reqScope=SCOPE, reqActive=ACTIVE_SCENE;
 $('#status').textContent='auto-mapping '+label+'…';
 let res;
 try{res=await j('/api/phase_automap',{method:'POST',headers:{'Content-Type':'application/json'},
   body:JSON.stringify({line,target_colors:cols,scene:reqScene})});}
 catch(e){$('#status').textContent='';return alert('auto-map request failed: '+e);}
 if(res.error){$('#status').textContent='';return alert(res.error);}
 // STALE guard: the selected scene/scope changed while we waited — discard, change nothing.
 if(SCOPE!==reqScope||ACTIVE_SCENE!==reqActive){$('#status').textContent='auto-map discarded (selection changed)';return;}
 // IDENTITY guard: server must echo the exact scene we asked for (null == R1/P1 phase corpus).
 if((res.scene||null)!==reqScene){$('#status').textContent='';return alert('Auto-map scene mismatch (asked '+reqScene+', got '+(res.scene||'null')+') — NO changes applied.');}
 // classify proposals against EXISTING mappings at the destination context (fill unmapped first).
 const existing=(ctxPolicies()[destId]||{}).plane_usage_palette_mappings||{};
 const fresh=[],repl=[];
 (res.proposals||[]).forEach(p=>{if(p.blocked)return;const nm={line:p.line,index_map:p.index_map};const prev=existing[p.usage_id];
   if(!prev)fresh.push([p.usage_id,nm]);else if(JSON.stringify(prev)!==JSON.stringify(nm))repl.push([p.usage_id,nm]);});
 const msg=(isScene?'Auto-map Current Scene':'Auto-map Phase')+': '+label+'\n'
  +'Genesis Line '+line+'\n'
  +'Layer-A usages considered: '+res.summary.considered+'\n'
  +'new mappings proposed: '+fresh.length+'\n'
  +'existing mappings that would change: '+repl.length+'\n'
  +'blocked (need more colors than Line '+line+' has): '+res.summary.blocked+'\n'
  +'Target CRAM colors will NOT change. One Undo operation.\n\nApply the '+fresh.length+' NEW mapping(s)?';
 if(!confirm(msg)){$('#status').textContent='auto-map canceled (no changes)';return;}
 // ONE undo transaction; write ONLY the destination context's plane mappings (Req 2/6).
 pushUndo();const dest=ctxPlaneMaps(destId);fresh.forEach(([uid,nm])=>dest[uid]=nm);
 let repApplied=0;
 if(repl.length&&confirm(repl.length+' EXISTING mapping(s) in '+label+' would be replaced. Replace them too?')){
   repl.forEach(([uid,nm])=>dest[uid]=nm);repApplied=repl.length;}
 afterChange();
 PHASE_RESULT={ph:destId,scene:reqScene,label,line,res,nw:fresh.length,rep:repApplied,skipped:repl.length-repApplied};renderPhaseResult();
 $('#status').textContent='auto-map done: '+fresh.length+' new, '+repApplied+' replaced, '+res.summary.blocked+' blocked';}
// PROMPT-ID-0010: write a CRAM into a SPECIFIC context's per-scene override (tpl), so each subround's
// derived palette is isolated and never clobbers another scene's base colors.
function tplSetAt(cid,line,i,cram){const cp=ctxPolicies();cp[cid]=cp[cid]||{};cp[cid].tpl=cp[cid].tpl||{};cp[cid].tpl[line]=cp[cid].tpl[line]||{};cp[cid].tpl[line][i]=cram;}
async function deriveScenePalette(line,onlyBank){
 const ctx=automapContext();
 if(!ctx)return alert('Open a subround scene (or a phase context) first.');
 if(POL.immutable)return alert('Create an editable profile first.');
 if(line==null)line=ACTIVE;
 // Line 2 = REUSE mode: map remaining banks onto existing Layer-B colors (never author). Otherwise 0/1/3.
 const reuse=isProtected(line);
 if(!reuse&&guardProtected(line))return;
 if(reuse&&!(POL.line2_display&&POL.line2_display.cram))return alert('No Layer-B palette is loaded for Line '+line+', so there is nothing to reuse.');
 if(!reuse&&!editableLines().includes(line))return alert('Pick an editable Genesis line (0, 1 or 3) at right first.');
 const destId=ctx.id, reqScene=ctx.scene||null, reqScope=SCOPE, reqActive=ACTIVE_SCENE, label=ctxName(destId)+(ctx.kind==='scene'?' ['+destId+']':'');
 $('#status').textContent=(onlyBank?'mapping bank '+onlyBank+' → Line ':(reuse?'mapping remaining banks → Line ':'deriving scene palette for '+label+' → Line '))+line+'…';
 // Whole-scene incremental: skip usages already mapped so their banks aren't re-derived. only_bank mode
 // remaps JUST that bank (ignores skip) so you can MOVE it from its current line to the chosen one.
 const skip=onlyBank?[]:Object.keys((ctxPolicies()[destId]||{}).plane_usage_palette_mappings||{});
 let res;
 try{res=await j('/api/scene_palette',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scene:reqScene,lines:[line],skip_usages:skip,only_bank:onlyBank||null})});}
 catch(e){$('#status').textContent='';return alert('derive failed: '+e);}
 if(res.error){$('#status').textContent='';return alert(res.error);}
 // stale + identity guards (never apply a result to a different scene than we asked for)
 if(SCOPE!==reqScope||ACTIVE_SCENE!==reqActive){$('#status').textContent='derive discarded (selection changed)';return;}
 if((res.scene||null)!==reqScene){$('#status').textContent='';return alert('Derive scene mismatch — NO changes applied.');}
 const s=res.summary, fill=(s.line_fill[String(line)]||0);
 // would any EXISTING effective color on this line change at this scope?
 const savedScope=SCOPE;SCOPE=destId;let changed=0;
 (res.lines[String(line)]||[]).forEach((cc,i)=>{if(i>0&&cc!=null){const cur=tcram(line,i);if(cur!=null&&cur!==cc)changed++;}});
 SCOPE=savedScope;
 const msg=(onlyBank?'MOVE bank '+onlyBank+' → Line '+line+(reuse?' (reuse Layer B)':'')+': '+label+'\n'
    +'remaps ONLY bank '+onlyBank+'\'s tiles to Line '+line+' (overrides their current line).\n'
   :reuse?'Map remaining banks → Line '+line+' (REUSE Layer B): '+label+'\n'
    +'maps each remaining Plane-A tile onto Line 2\'s EXISTING arcade colors (never changes Line 2).\n'
   :'Derive Scene Palette: '+label+'\ntarget: Genesis Line '+line+'\n')
  +(s.banks_already_placed?('banks already placed on other lines (kept): '+s.banks_already_placed+'\n'):'')
  +'remaining banks '+(reuse?'mapped':'that fit')+' this line: '+s.banks_placed+'/'+s.banks_total+(reuse?'':'  (too big for one line: '+s.banks_blocked+')')+'\n'
  +'usages mapped this pass: '+s.usages_mapped+'  (still unmapped: '+s.usages_blocked+')\n'
  +(reuse?'Line 2 colors are NOT changed. MRD-safe (no merges). ':'colors written to Line '+line+': '+fill+'/15\n'
    +(changed?('WARNING: '+changed+' existing color(s) on Line '+line+' will be overwritten.\n'):''))
  +'Scoped ONLY to '+label+'. One Undo.\n'
  +(s.usages_blocked?'Tiles needing >15 distinct colors stay UNMAPPED.\n':'')
  +'\nProceed?';
 if(!confirm(msg)){$('#status').textContent=(reuse?'map':'derive')+' canceled (no changes)';return;}
 pushUndo();
 // colors -> per-scene override on the chosen line (authoring lines 0/1/3 only; Line 2 is reuse-mapping, no colors)
 if(!reuse)(res.lines[String(line)]||[]).forEach((cc,i)=>{if(i>0&&cc!=null)tplSetAt(destId,line,i,cc);});
 // mappings -> the destination context's plane map
 const dest=ctxPlaneMaps(destId);Object.entries(res.mappings).forEach(([uid,m])=>{dest[uid]={line:m.line,index_map:m.index_map};});
 afterChange();
 PHASE_RESULT=null;const P=$('#props');P.innerHTML='';
 P.appendChild(txt((reuse?'MAP → LINE '+line+' (REUSE LAYER B)':'DERIVE SCENE PALETTE → LINE '+line)+' — '+label
   +'\nalready placed (other lines): '+s.banks_already_placed+' banks\nremaining banks '+(reuse?'mapped':'fit this line')+': '+s.banks_placed+'/'+s.banks_total
   +'\nusages mapped this pass: '+s.usages_mapped+'\nstill unmapped: '+s.usages_blocked
   +(reuse?'\nLine 2 colors: UNCHANGED (reuse only)':'\ncolors on Line '+line+': '+fill+'/15\ncolors written to: per-scene override ('+destId+')')));
 if(s.usages_blocked)P.appendChild(el('div','vitem WARN',s.usages_blocked+' usage(s) need >15 distinct colors — still UNMAPPED.'));
 else P.appendChild(el('div','vitem PASS',(reuse?'All remaining tiles mapped onto Line 2 (Layer B unchanged).':'All remaining banks placed on Line '+line+'.')+' Isolated to '+destId+'.'));
 $('#status').textContent=(reuse?'mapped → Line ':'scene palette derived → Line ')+line+': '+s.usages_mapped+' usages, '+s.usages_blocked+' blocked';}
// Blank `line` at the ACTIVE scope ONLY. Removes this scope's own color overrides for the line and,
// for any color still showing (inherited from the SHARED BASE), writes a null override at this scope so
// the line reads blank HERE without ever clearing the shared base (which other subrounds inherit — the
// base-clear was what wiped R1-S1 when clearing R1-S2). Removes only THIS scope's own plane mappings on
// the line; the shared base and other scopes are never touched. Line 2 protected.
function clearLine(line){
 if(POL.immutable)return alert('Create an editable profile first.');
 if(guardProtected(line))return;
 const cp=ctxPolicies();
 const savedScope=SCOPE;   // measure what's effective on this line at THIS scope
 let effN=0;for(let i=1;i<16;i++)if(tcram(line,i)!=null)effN++;
 const scopePlane=(cp[SCOPE]&&cp[SCOPE].plane_usage_palette_mappings)||{};
 const planeN=Object.values(scopePlane).filter(m=>m&&m.line===line).length;
 if(!effN&&!planeN)return alert('Line '+line+' is already empty at '+ctxName(SCOPE)+'.');
 if(!confirm('Clear Genesis Line '+line+' at '+ctxName(SCOPE)+' ONLY?\n'
   +'colors blanked at this scope: '+effN+'\nthis scope\'s Layer-A mappings removed: '+planeN
   +'\nThe shared base and every OTHER subround are left untouched. Line 2 is never affected. One Undo.'))return;
 pushUndo();
 // drop this scope's own overrides, then shadow any base/inherited color with a null override here
 if(cp[SCOPE]&&cp[SCOPE].tpl)delete cp[SCOPE].tpl[line];
 for(let i=1;i<16;i++){if(tcram(line,i)!=null)tplSetAt(SCOPE,line,i,null);}
 // remove only THIS scope's plane mappings on the line (shared global/sprite maps are left alone)
 Object.keys(scopePlane).forEach(k=>{if(scopePlane[k]&&scopePlane[k].line===line)delete scopePlane[k];});
 afterChange();if(TAB==='layera')renderLayerA($('#list'));else renderList();
 $('#status').textContent='cleared Line '+line+' at '+ctxName(SCOPE)+' (base + other subrounds untouched)';}
let PHASE_RESULT=null;
function renderPhaseResult(){const R=PHASE_RESULT;if(!R)return;const P=$('#props');P.innerHTML='';const s=R.res.summary;
 const kind=R.scene?'SCENE AUTO-MAP':'PHASE AUTO-MAP';
 P.appendChild(txt(`${kind} — ${R.label||ctxName(R.ph)} → LINE ${R.line}\nscene identity: ${R.scene||'(R1/P1 phase corpus)'}\nlogical usages considered: ${s.considered}\nnew mappings: ${R.nw}\nreplaced: ${R.rep}${R.skipped?`  (declined: ${R.skipped})`:''}\nblocked: ${s.blocked}\npopulated target colors: ${s.populated_targets}\nMRD violations: 0 (injective per usage)\nmean ΔE: ${s.mean_de}\nworst ΔE: ${s.worst_de}\ntarget colors modified: NO`));
 if(s.blocked)P.appendChild(el('div','vitem WARN',s.blocked+' usage(s) BLOCKED — need more distinct colors than Line '+R.line+' has populated (not merged).'));
 P.appendChild(el('div','vitem PASS','Target palette unchanged. Mappings stored ONLY at '+R.ph+'; other scenes untouched.'));
 const wb=el('button','act','Show worst matches ('+R.res.worst.length+')');wb.onclick=()=>{const box=el('div');R.res.worst.forEach(w=>{const r=el('div','maprow');r.style.cursor='pointer';r.appendChild(el('span',null,w.usage_id));r.appendChild(el('span',null,w.pattern_id));r.appendChild(el('span',null,'worst ΔE '+w.worst_de));r.appendChild(el('span','dim','mean '+w.mean_de));r.onclick=()=>openLAPatternUsage(w.pattern_id,w.usage_id);box.appendChild(r);});P.appendChild(box);};P.appendChild(wb);}
function mapInspect(k,seg){const P=$('#props');P.innerHTML='';const occ=LAMAP.cells.filter(c=>c.pid===k.pid).length;
 P.appendChild(txt(`MAP TILE INSPECTOR\nsegment: ${seg} (record ${seg})\nmap x/y: ${k.c} / ${k.r}\ntile code: 0x${k.code.toString(16).toUpperCase()}\nphysical pattern: ${k.pid||'—'}\nlogical usage: ${k.uid||'UNRESOLVED'}\nraw attr word: ${k.attr}\npalette selector: attr & 0x1ff = ${k.bank}\neffective palette bank: ${k.bank}\ndescriptor entry addr: ${k.entry}\ntile-word addr: ${k.descr}\nflip: h${k.hf} v${k.vf}\noccurrences in segment: ${occ}\npalette authority: ORIGINAL ARCADE palette RAM 0x200000 (KF-788 validated)`));
 if(k.uid)mkbtn(P,'Open usage '+k.uid,()=>openLAPatternUsage(k.pid,k.uid));}
function laGenPalByUsage(uid,bankId){const mm=planeMap(uid);if(!mm)return null;const bank=LA.banks[bankId];if(!bank)return null;
 const pal=bank.map(x=>x.slice());   // start from arcade bank; overlay this usage's context-effective mapping
 Object.entries(mm.index_map||{}).forEach(([si,ti])=>{const g=cramToRGB(effCramAt(mm.line,ti));if(g)pal[+si]=g;});return pal;}
async function openLAPatternUsage(pid,uid){LADET=await j('/api/layera_pattern?pid='+pid+sceneQS('&'));LAUSAGE=(LADET.usages.find(x=>x.usage_id===uid))||LADET.usages[0]||null;LASRC=null;
 // jump to library detail so the full editor is available
 LAVIEW='library';renderLayerA($('#list'));}
function pickLayerTarget(uid,srcIndex){const mm=planeMap(uid);if(!mm||mm.index_map[srcIndex]==null){$('#status').textContent='pixel src i'+srcIndex+' is not mapped yet (map it in the tile detail).';return;}
 TGT={line:mm.line,index:mm.index_map[srcIndex]};ACTIVE=mm.line;renderTarget();showTarget();$('#status').textContent='picked target L'+mm.line+':'+mm.index_map[srcIndex]+' (Layer-A src i'+srcIndex+')';}
function laFiltered(){return LA.patterns.filter(p=>{
 if(LAFILT.seg!==''&&!p.segments.includes(+LAFILT.seg))return false;
 if(LAFILT.bank!==''&&!p.palette_banks.includes(LAFILT.bank))return false;
 if(LAFILT.pal==='single'&&p.multi_palette)return false;
 if(LAFILT.pal==='multi'&&!p.multi_palette)return false;
 if(LAFILT.anim!==''&&p.animation_status!==LAFILT.anim)return false;
 if(LAFILT.map!==''&&laMapStatus(p)!==LAFILT.map)return false;
 const s=LAFILT.q.trim().toLowerCase();
 if(s){const hay=(p.pattern_id+' '+p.rep_tile_code+' 0x'+p.rep_tile_code.toString(16)+' '+p.pattern_hash+' '+p.usage_ids.join(' ')+' '+p.palette_banks.join(' ')).toLowerCase();if(!hay.includes(s))return false;}
 return true;});}
function laMapStatus(p){const mapped=p.usage_ids.filter(u=>{const m=planeMap(u);return m&&Object.keys(m.index_map||{}).length;}).length;return mapped===0?'unmapped':mapped===p.usage_ids.length?'mapped':'partial';}
function renderLAGrid(){LADET=null;const C=$('#center');C.innerHTML='';
 const all=laFiltered();const pages=Math.max(1,Math.ceil(all.length/LAPP));LAPAGE=Math.min(LAPAGE,pages-1);
 const head=el('div','labar');head.appendChild(el('b',null,`Layer A — ${all.length} patterns`));head.appendChild(el('span','dim',`  (of ${LA.counts.physical_patterns}) · page ${LAPAGE+1}/${pages}`));
 const prev=el('button','mini','‹ prev');prev.onclick=()=>{if(LAPAGE>0){LAPAGE--;renderLAGrid();}};const next=el('button','mini','next ›');next.onclick=()=>{if(LAPAGE<pages-1){LAPAGE++;renderLAGrid();}};
 head.appendChild(prev);head.appendChild(next);C.appendChild(head);
 const grid=el('div','laGrid');
 all.slice(LAPAGE*LAPP,(LAPAGE+1)*LAPP).forEach(p=>{const card=el('div','laCard');
  const im=new Image();im.className='pimg';im.loading='lazy';im.width=8*LAZOOM;im.height=8*LAZOOM;im.src=`/api/render_tile?code=${p.rep_tile_code}&bank=${p.palette_banks[0]}&z=${LAZOOM}`+sceneQS('&');card.appendChild(im);
  card.appendChild(el('div','laId',p.pattern_id));card.appendChild(el('div','dim',p.n_uses+'u · '+p.n_palettes+'p'+(p.multi_palette?' ✳':'')));
  card.onclick=()=>openLAPattern(p.pattern_id);grid.appendChild(card);});
 C.appendChild(grid);}
async function openLAPattern(pid){LADET=await j('/api/layera_pattern?pid='+pid+sceneQS('&'));LAUSAGE=LADET.usages[0]||null;LASRC=null;renderLADetail();}
function renderLADetail(){const C=$('#center');C.innerHTML='';const p=LADET.pattern;
 const back=el('button','mini','‹ back to grid');back.onclick=()=>renderLAGrid();C.appendChild(back);
 C.appendChild(txt(`PHYSICAL PATTERN ${p.pattern_id}${p.multi_palette?'   [MULTI-PALETTE]':''}\ntile code(s): ${p.tile_codes.map(x=>'0x'+x.toString(16).toUpperCase()).join(', ')}\ncontent hash: ${p.pattern_hash.slice(0,24)}…\nused indices: ${p.used_indices.join(', ')} (${p.n_colors} colors)\nsegments: ${p.segments.join(', ')}\nbanks: ${p.palette_banks.join(', ')} · uses: ${p.n_uses} · status: ${p.animation_status}`));
 // palette variants side by side (same geometry, different colors)
 const vh=el('h3',null,'PALETTE VARIANTS — same physical tile, different source palettes');C.appendChild(vh);
 const vwrap=el('div','laVariants');
 p.palette_banks.forEach(b=>{const box=el('div','pv');box.appendChild(el('div','pvh','Palette '+b));
  const pal=JSON.stringify(LA.banks[b]);const im=new Image();im.className='pimg';im.width=8*16;im.height=8*16;im.src=`/api/render_tile?code=${p.rep_tile_code}&pal=${encodeURIComponent(pal)}&z=16`;box.appendChild(im);vwrap.appendChild(box);});
 C.appendChild(vwrap);
 // logical usages
 C.appendChild(el('h3',null,'LOGICAL USAGES ('+LADET.usages.length+')'));
 const ut=el('div');LADET.usages.forEach(u=>{const r=el('div','row'+(LAUSAGE&&LAUSAGE.usage_id===u.usage_id?' sel':''));
  const ck=el('input');ck.type='checkbox';ck.checked=LAP.has(u.usage_id);ck.onclick=e=>{e.stopPropagation();if(ck.checked)LAP.add(u.usage_id);else LAP.delete(u.usage_id);renderLayerA($('#list'));};
  r.appendChild(ck);r.appendChild(el('span',null,` ${u.usage_id} · bank ${u.palette_bank} · seg ${u.segments.join('/')} · ${u.n_colors}c · flip ${u.flip}`));
  r.onclick=()=>{LAUSAGE=u;LASRC=null;renderLADetail();};ut.appendChild(r);});
 C.appendChild(ut);
 if(LAUSAGE)renderLAUsage();}
function laGenPal(u){const pal=[[0,0,0]];for(let i=1;i<16;i++)pal[i]=[60,60,72];const mm=planeMap(u.usage_id);
 u.used_colors.forEach(c=>{let rgb=c.genesis_rgb8;if(mm&&mm.index_map[c.src_index]!=null){const g=cramToRGB(effCramAt(mm.line,mm.index_map[c.src_index]));if(g)rgb=g;}pal[c.src_index]=rgb;});return pal;}
function renderLAUsage(){const C=$('#center');const u=LAUSAGE;
 C.appendChild(el('h3',null,'SELECTED USAGE '+u.usage_id+' — Arcade source vs Genesis target'));
 const pv=el('div','laVariants');
 const a=el('div','pv');a.appendChild(el('div','pvh','ARCADE SOURCE (bank '+u.palette_bank+')'));const ia=new Image();ia.className='pimg';ia.width=ia.height=8*20;ia.src=`/api/render_tile?code=${u.tile_code}&bank=${u.palette_bank}&z=20`+sceneQS('&');a.appendChild(ia);pv.appendChild(a);
 const g=el('div','pv');g.appendChild(el('div','pvh','GENESIS TARGET (mapped colors) — click a pixel to pick its CRAM entry'));const ig=new Image();ig.className='pimg pickable';ig.width=ig.height=8*20;ig.src=`/api/render_tile?code=${u.tile_code}&pal=${encodeURIComponent(JSON.stringify(laGenPal(u)))}&z=20`;
 ig.onclick=e=>{const rc=ig.getBoundingClientRect();const nx=Math.floor((e.clientX-rc.left)/rc.width*8),ny=Math.floor((e.clientY-rc.top)/rc.height*8);const px=(LADET&&LADET.pixels)||[];const vi=px[ny*8+nx];if(!vi){$('#status').textContent='Transparent pixel — no palette entry';return;}const mm=planeMap(u.usage_id);const c=u.used_colors.find(x=>x.src_index===vi);if(c){LASRC=c;renderLADetail();laFindMatch(c);}if(mm&&mm.index_map[vi]!=null){TGT={line:mm.line,index:mm.index_map[vi]};ACTIVE=mm.line;renderTarget();showTarget();$('#status').textContent=`picked src i${vi} → L${mm.line}:${mm.index_map[vi]}`;}else $('#status').textContent=`clicked src i${vi} (unmapped) — selected as source`;};g.appendChild(ig);pv.appendChild(g);
 C.appendChild(pv);
 // used-color chips (click to select, then click an editable target entry to map)
 const bar=el('div','actbar');mkbtn(bar,'Auto-fill Tile',()=>autoFillTile());
 editableLines().forEach(l=>mkbtn(bar,'Copy Used Colors → L'+l,()=>copyUsedColors(l)));
 mkbtn(bar,'Reset Mapping',()=>{pushUndo();delPlaneMapping(u.usage_id);afterChange();renderLADetail();});
 C.appendChild(bar);C.appendChild(el('div','dim','Click a used color, then click an entry on an editable line (0/1/3) to map it. Line 2 is protected.'));
 const grid=el('div','apal');const mm=planeMap(u.usage_id)||{};
 u.used_colors.forEach(c=>{const cell=el('div','ccell');const sw=swBox(c.arcade_rgb8);if(LASRC&&LASRC.src_index===c.src_index)sw.classList.add('picked');
  sw.title=`src i${c.src_index} ${c.hex} · Genesis ${c.genesis_cram}`;sw.onclick=()=>{LASRC=c;window._laMode=true;$('#status').textContent='pick an editable Genesis entry (Line 0/1/3) to map i'+c.src_index;renderLADetail();laFindMatch(c);};
  cell.appendChild(sw);cell.appendChild(el('span',null,'i'+c.src_index));const im=(mm.index_map||{});if(im[c.src_index]!=null)cell.appendChild(el('span','tag','→L'+mm.line+':'+im[c.src_index]));grid.appendChild(cell);});
 C.appendChild(grid);
 // mapping provenance
 const em=effPlaneMapping(u.usage_id);
 if(em){const prov=em.owner==='global'?'global base':(em.local?'LOCAL · '+ctxName(SCOPE):'INHERITED FROM '+ctxName(em.owner));
  C.appendChild(el('div','vitem '+(em.owner==='global'?'PASS':em.local?'PASS':'WARN'),'MAPPING: '+prov+' → Line '+em.m.line));}
 else C.appendChild(el('div','vitem WARN','MAPPING: none yet (map manually, or run Auto-map Phase).'));
 // MRD reminder
 C.appendChild(el('div','vitem WARN','TILE MRD: '+u.mrd_pairs.length+' distinct-color pairs must stay distinct (never merge two used colors to one target).'));}
function laFindMatch(c){const P=$('#props');P.innerHTML='';P.appendChild(txt('LAYER-A COLOR i'+c.src_index+' '+c.hex+'\nnatural Genesis '+c.genesis_cram));
 // cross-reference across Layer A (same segment coexistence) + sprites
 const rows=[];(O.usages||[]).forEach(su=>su.used_colors.forEach(o=>{const de=deltaE00(c.arcade_rgb8,o.arcade_rgb8);rows.push({src:'sprite',nm:su.display_name,i:o.src_index,de,rgb:o.arcade_rgb8,nat:o.genesis_cram===c.genesis_cram});}));
 (LADET.usages||[]).forEach(pu=>pu.used_colors.forEach(o=>{if(pu.usage_id===LAUSAGE.usage_id&&o.src_index===c.src_index)return;const de=deltaE00(c.arcade_rgb8,o.arcade_rgb8);rows.push({src:'layerA',nm:pu.usage_id,i:o.src_index,de,rgb:o.arcade_rgb8,nat:o.genesis_cram===c.genesis_cram});}));
 rows.sort((a,b)=>a.de-b.de);const T=el('div','simtab');
 rows.slice(0,12).forEach(r=>{const dL=Math.abs(oklab(c.arcade_rgb8)[0]-oklab(r.rgb)[0]);const row=el('div','maprow');const sw=swBox(r.rgb);sw.style.display='inline-block';row.appendChild(sw);row.appendChild(el('span',null,r.src+' '+r.nm+' i'+r.i));row.appendChild(el('span',null,'ΔE '+r.de.toFixed(2)));row.appendChild(el('span',null,'ΔL '+dL.toFixed(3)+(r.nat?' =nat':'')));T.appendChild(row);});
 P.appendChild(el('div','vitem PASS','CROSS-REFERENCE (Layer A + sprites) — Layer B is informational only; protected Line 2 is never a target.'));P.appendChild(T);}
function laMapColor(line,index){const u=LAUSAGE,c=LASRC;if(!u||!c)return;if(POL.immutable)return alert('Create an editable profile first.');
 // Line 2 (Layer B, protected): colors are arcade-controlled and NOT editable, but an EXISTING Line-2
 // color may be REUSED by a Plane-A tile (map onto an occupied index; never create/overwrite a color).
 const prot=isProtected(line);
 if(prot){
   const l2d=POL.line2_display&&POL.line2_display.cram?POL.line2_display.cram:null;
   const have=(POL.target_palette_lines[line]||[])[index]||(l2d?l2d[index]:null);
   if(index===0||!have){$('#status').textContent='Line '+line+' index '+index+' has no arcade color — reuse an occupied Line-2 entry.';
     return alert('LINE '+line+' (Layer B / arcade) is read-only. You can REUSE one of its existing colors, but not create a new color on an empty index.');}
   if(animatedIndices(line).includes(index) && !confirm('L'+line+':'+index+' is the ANIMATED sky/time-of-day color (it changes across Round 1). Reuse it anyway?'))return;
 }
 const cur=planeMap(u.usage_id);let m={line,index_map:Object.assign({},(cur&&cur.line===line?cur.index_map:{}))};
 for(const[si,ti]of Object.entries(m.index_map)){if(+ti===index&&+si!==c.src_index&&u.mrd_pairs.some(([a,b])=>(a===+si&&b===c.src_index)||(b===+si&&a===c.src_index)))return alert('TILE MRD: i'+c.src_index+' and i'+si+' both appear in this tile and must stay distinct.');}
 pushUndo();m.index_map[c.src_index]=index;setPlaneMapping(u.usage_id,m);
 if(!prot&&tcram(line,index)==null)setTgt(line,index,bestCramFor(c.arcade_rgb8).cram);   // never author Line 2
 window._laMode=false;LASRC=null;$('#status').textContent=`${u.usage_id} i${c.src_index} → L${line}:${index}`+(prot?' [reused Layer-B color]':'')+` (scope ${ctxName(SCOPE)})`;afterChange();renderLADetail();}
function autoFillTile(line){const u=LAUSAGE;if(!u)return;if(POL.immutable)return alert('Create an editable profile first.');
 if(line==null)line=editableLines()[0];if(guardProtected(line))return;
 pushUndo();const m={line,index_map:{}};setPlaneMapping(u.usage_id,m);const L=effLine(line);
 const taken={};L.forEach((c,i)=>{if(c!=null)taken[c]=i;});let next=1;const nextFree=()=>{while(next<16&&L[next]!=null)next++;return next<16?next:-1;};
 u.used_colors.forEach(c=>{let cram=bestCramFor(c.arcade_rgb8).cram;
  if(Object.values(m.index_map).some(ti=>L[ti]===cram))cram=nudgeDistinct(c.arcade_rgb8,new Set(Object.values(m.index_map).map(ti=>L[ti])));
  let ti=taken[cram];if(ti==null){ti=nextFree();if(ti<0){$('#status').textContent='Line '+line+' full';return;}L[ti]=cram;taken[cram]=ti;setTgt(line,ti,cram);}m.index_map[c.src_index]=ti;});
 $('#status').textContent=`Auto-filled ${u.usage_id} → Line ${line} (${Object.keys(m.index_map).length} colors, detail preserved)`;afterChange();renderLADetail();}
function copyUsedColors(line){const u=LAUSAGE;if(!u)return;if(guardProtected(line))return;autoFillTile(line);}
async function solveLA(mode){if(!LAP.size)return alert('check 1+ Layer-A usages');$('#status').textContent='solving…';
 // PROMPT-ID-0009: LA source corpus follows the active scene (null unless a PAL-* scene is open).
 const scn=/^PAL-/.test(ACTIVE_SCENE||'')?ACTIVE_SCENE:null;
 const sol=await j('/api/solve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({usage_ids:[...LAP],mode,scene:scn})});
 SOLUTION=sol;const P=$('#props');P.innerHTML='';const nm=sol.solver==='luminance_hue'?'LUMINANCE/HUE':'ΔE PERCEPTUAL';
 P.appendChild(txt(`${nm} SHARED PALETTE (Layer A)\ndomains: ${(sol.palette_domains||[]).length}\nfeasible in one line: ${sol.feasible?'YES':'NO'}\nsafe entries required: ${sol.safe_entries_required||sol.entries_used} / capacity ${sol.one_line_capacity||15}\nMRD violations: 0 (guaranteed)`));
 if(!sol.feasible)P.appendChild(el('div','vitem ERROR',`NO ACCEPTABLE ONE-LINE SOLUTION — needs ${sol.safe_entries_required} hue-safe entries. No colors destroyed to force a fit.`));
 editableLines().forEach(line=>{const b=el('button',null,'Apply to Line '+line);b.onclick=()=>applyLASolution(sol,line);P.appendChild(b);});}
function applyLASolution(sol,line){if(guardProtected(line))return;if(POL.immutable)return alert('Create an editable profile first.');pushUndo();
 sol.entries.forEach(e=>{setTgt(line,e.target_index,e.cram);});
 LAP.forEach(uid=>{const m={line,index_map:{}};setPlaneMapping(uid,m);sol.entries.forEach(e=>e.members.forEach(mm=>{if(mm.usage_id===uid)m.index_map[mm.src_index]=e.target_index;}));});
 ACTIVE=line;$('#status').textContent='applied Layer-A '+(sol.solver||'')+' shared palette → Line '+line;afterChange();if(LADET)renderLADetail();}

boot();
