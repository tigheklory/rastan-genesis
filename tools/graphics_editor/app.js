"use strict";
let O=null,POL=null,TAB="objects",U=null,SRC=null,CMP=null,TGT=null,DIRTY=false,UNDO=[],REDO=[];
let GROUP=new Set(),ACTIVE=0,SOLUTION=null;
const $=s=>document.querySelector(s),el=(t,c,x)=>{const e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e;};
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
 renderList();renderTarget();
 $('#foot').textContent=`${O.usages.length} source usages · ${O.objects.length} objects · ${O.palettes.length} palettes · exact-dup palette groups ${Object.keys(O.exact_duplicate_palette_groups).length} · Genesis 4×16`;
}
function pushUndo(){UNDO.push(JSON.stringify(POL));if(UNDO.length>50)UNDO.shift();REDO=[];}
function undo(){if(!UNDO.length)return;REDO.push(JSON.stringify(POL));POL=JSON.parse(UNDO.pop());afterChange(true);}
function redo(){if(!REDO.length)return;UNDO.push(JSON.stringify(POL));POL=JSON.parse(REDO.pop());afterChange(true);}
function afterChange(noUndo){DIRTY=true;$('#dirty').textContent='● unsaved';renderTarget();renderSource();validate();}
async function maybeSwitch(pid){if(DIRTY&&!confirm('Discard unsaved changes?')){$('#profile').value=POL.profile_id;return;}loadProfile(pid);}
async function loadProfile(pid){POL=await j('/api/policy?p='+encodeURIComponent(pid));if(!POL.target_palette_lines)POL.target_palette_lines=[...Array(4)].map(()=>Array(16).fill(null));if(!POL.usage_palette_mappings)POL.usage_palette_mappings={};DIRTY=false;$('#dirty').textContent='';$('#profile').value=pid;$('#pstatus').textContent=POL.immutable?'immutable baseline — Create editable profile to edit':('editable · parent '+(POL.parent||'—'));$('#save').disabled=!!POL.immutable;renderTarget();renderSource();validate();}
function branch(){const base=($('#newprofile').value||'').trim().replace(/[^a-z0-9_\-]/gi,'_');if(!base)return alert('type a profile name first');POL={profile_id:base,display_name:base,parent:POL.profile_id,immutable:false,schema:'v0.2',target_palette_lines:JSON.parse(JSON.stringify(POL.target_palette_lines)),usage_palette_mappings:JSON.parse(JSON.stringify(POL.usage_palette_mappings)),object_labels:{}};const o=el('option',null,base);o.value=base;$('#profile').appendChild(o);$('#profile').value=base;$('#save').disabled=false;DIRTY=true;$('#dirty').textContent='● unsaved';$('#pstatus').textContent='editable (unsaved) · parent '+POL.parent;validate();}
async function save(){if(POL.immutable)return alert('Baseline is immutable. Click "Create editable profile" first.');const r=await j('/api/policy',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(POL)});if(r.ok){DIRTY=false;$('#dirty').textContent='saved';}else alert(r.error);}

function statusOf(o){const s=(o.status||o.category||'UNKNOWN')+'';if(/PROVEN/i.test(s))return'PROVEN';if(/PARTIAL|CAPTURED|pending/i.test(s))return'PARTIAL';if(/NOT REACHABLE|OTHER/i.test(s))return'OTHER';return'UNKNOWN';}
function renderList(){const L=$('#list');L.innerHTML='';
 if(TAB==='objects'){
  const gb=el('div','groupbar');gb.appendChild(el('span','dim','Shared Palette Group: '+GROUP.size+' '));
  if(GROUP.size>=1){mkbtn(gb,'Derive Shared Palette',()=>solveGroup(false,'delta_e'));const lb=mkbtn(gb,'Derive Luminance/Hue Palette',()=>solveGroup(false,'luminance_hue'));lb.title='Prioritizes preserving perceptual brightness (OKLab L), then chooses hues between compatible source colors.';mkbtn(gb,'Compare Solvers',()=>compareSolvers());mkbtn(gb,'Clear',()=>{GROUP.clear();renderList();});}
  L.appendChild(gb);
  // group usages by object_id -> ONE palette-domain row (preview frames are representations, not consumers)
  const doms={};O.usages.forEach(u=>{(doms[u.object_id]=doms[u.object_id]||[]).push(u);});
  Object.entries(doms).forEach(([oid,reps])=>{const u0=reps[0];const dname=u0.display_name.split(' (')[0];
   const r=el('div','row');const ck=el('input');ck.type='checkbox';
   const inGroup=reps.some(x=>GROUP.has(x.usage_id));ck.checked=inGroup;
   ck.onclick=e=>{e.stopPropagation();reps.forEach(x=>{if(ck.checked)GROUP.add(x.usage_id);else GROUP.delete(x.usage_id);});renderList();};
   r.appendChild(ck);r.appendChild(el('span',null,' '+dname+' '));r.appendChild(el('span','badge PROVEN',u0.n_used+'c'));
   if(reps.length>1)r.appendChild(el('span','badge OTHER',reps.length+' frames'));
   r.onclick=()=>{document.querySelectorAll('#list .row').forEach(x=>x.classList.remove('sel'));r.classList.add('sel');selectUsage(u0);};
   if(U&&U.object_id===oid)r.classList.add('sel');L.appendChild(r);
   // frame selector for multi-representation domains (preview only)
   if(reps.length>1&&U&&U.object_id===oid){const fr=el('div','framesel');reps.forEach(x=>{const fb=el('button','mini'+(U.usage_id===x.usage_id?' on':''),x.display_name.replace(/.*\(/,'').replace(')',''));fb.onclick=ev=>{ev.stopPropagation();selectUsage(x);};fr.appendChild(fb);});L.appendChild(fr);}
  });
  O.objects.filter(o=>statusOf(o)!=='PROVEN').forEach(o=>{const r=el('div','row');r.appendChild(el('span',null,(o.display_name||o.id)+' '));r.appendChild(el('span','badge '+statusOf(o),statusOf(o)));r.onclick=()=>{document.querySelectorAll('#list .row').forEach(x=>x.classList.remove('sel'));r.classList.add('sel');U=null;$('#srccolors').innerHTML='';$('#maptable').innerHTML='';$('#previews').innerHTML='<div class="dim">NO PROVEN GRAPHICS PREVIEW AVAILABLE for '+(o.display_name||o.id)+'</div>';};L.appendChild(r);});}
 if(TAB==='contexts')O.contexts.forEach(c=>{const r=el('div','row',c.display||c.id);r.onclick=()=>{ctxFit(c);};L.appendChild(r);});
 if(TAB==='palettes')O.palettes.forEach(p=>{const dup=Object.values(O.exact_duplicate_palette_groups).some(g=>g.includes(p.palette_id));const r=el('div','row');r.appendChild(el('span',null,p.palette_id.replace('palette:','')+' '));if(dup)r.appendChild(el('span','badge OTHER','lossless-share'));r.onclick=()=>showPaletteResource(p);L.appendChild(r);});}

function selectUsage(u){U=u;SRC=null;CMP=null;const m=POL.usage_palette_mappings[u.usage_id];if(m&&m.line!=null)ACTIVE=m.line;renderTarget();renderSource();renderPreviews();}
function swBox(rgb,cls){const s=el('div','sw'+(cls?' '+cls:''));s.style.background=rgb?`rgb(${rgb.join(',')})`:'#20202a';return s;}

function renderSource(){const S=$('#srccolors');S.innerHTML='';if(!U){S.innerHTML='<div class="dim">Select an object (left) to see the colors it actually uses.</div>';return;}
 $('#srchdr').textContent='ARCADE SOURCE — '+U.display_name+' (bank '+U.sprite_bank+', '+U.n_used+' used colors)';
 // primary actions bar
 const bar=el('div','actbar');
 mkbtn(bar,'Auto-fill Object',()=>autoFill());mkbtn(bar,'Recommend Line',()=>recommendLine());
 mkbtn(bar,'Reset Mapping',()=>{pushUndo();delete POL.usage_palette_mappings[U.usage_id];afterChange();});
 S.appendChild(bar);S.appendChild(el('div','dim','Drag a color onto a Genesis entry (right) — or click a color, then a target entry. Click two colors to Compare.'));
 const grid=el('div','apal');
 U.used_colors.forEach(c=>{const cell=el('div','ccell');const sw=swBox(c.arcade_rgb8);sw.draggable=true;if(SRC&&SRC.src_index===c.src_index)sw.classList.add('picked');sw.title=`src idx ${c.src_index} ${c.hex} · ${c.pixel_count}px · Genesis ${c.genesis_cram}`;
  sw.ondragstart=e=>{SRC=c;e.dataTransfer.setData('text/plain','src');};
  sw.onclick=()=>{if(SRC&&CMP===null&&SRC.src_index!==c.src_index&&window._cmpMode){compareTool(SRC,c);window._cmpMode=false;}else{SRC=c;renderSource();showColorProps(c);if(TGT){/* click-to-map */}}};
  cell.appendChild(sw);cell.appendChild(el('span',null,'i'+c.src_index));
  const m=(POL.usage_palette_mappings[U.usage_id]||{}).index_map||{};if(m[c.src_index]!=null)cell.appendChild(el('span','tag','→L'+POL.usage_palette_mappings[U.usage_id].line+':'+m[c.src_index]));
  grid.appendChild(cell);});
 S.appendChild(grid);renderMapTable();renderPreviews();
}
function mkbtn(p,t,f){const b=el('button','act',t);b.onclick=f;p.appendChild(b);return b;}
function bestCramFor(rgb){/* nearest legal CRAM by ΔE00 */let best=null;for(let R=0;R<8;R++)for(let G=0;G<8;G++)for(let B=0;B<8;B++){const t=[LV[R],LV[G],LV[B]];const d=deltaE00(rgb,t);if(!best||d<best.d)best={cram:'0x'+(((B<<9)|(G<<5)|(R<<1))>>>0).toString(16).padStart(4,'0').toUpperCase(),d,rgb:t};}return best;}
function lineFit(line){/* for U on `line`: exact/natural shares, new entries, MRD ok */let shares=0,neu=0;const used={};POL.target_palette_lines[line].forEach((c,i)=>{if(c!=null)used[c]=i;});
 U.used_colors.forEach(c=>{const cram=bestCramFor(c.arcade_rgb8).cram;if(used[cram]!=null)shares++;else neu++;});
 return {line,shares,neu,fits:neu<= (15-POL.target_palette_lines[line].filter((x,k)=>x!=null&&k!==0).length)};}
function recommendLine(){const ranks=[0,1,2,3].map(lineFit).sort((a,b)=>(b.shares-a.shares)||(a.neu-b.neu));const P=$('#props');P.innerHTML='';
 P.appendChild(txt('RECOMMEND LINE for '+U.display_name));ranks.forEach((r,i)=>{const v=el('div','vitem '+(r.fits?(i===0?'PASS':'WARN'):'ERROR'),`Line ${r.line}: ${r.shares} share + ${r.neu} new ${r.fits?'':'— does not fit'}`);P.appendChild(v);});
 const b=el('button',null,'Auto-fill on Line '+ranks[0].line);b.onclick=()=>autoFill(ranks[0].line);P.appendChild(b);}
function autoFill(line){if(POL.immutable)return alert('Create an editable profile first.');
 if(line==null){line=[0,1,2,3].map(lineFit).sort((a,b)=>(b.shares-a.shares)||(a.neu-b.neu))[0].line;}
 pushUndo();const m=POL.usage_palette_mappings[U.usage_id]={line,index_map:{}};const L=POL.target_palette_lines[line];
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
 const m=POL.usage_palette_mappings[U.usage_id]||(POL.usage_palette_mappings[U.usage_id]={line,index_map:{}});
 if(m.line!==line){if(Object.keys(m.index_map).length&&!confirm('Move this usage\'s mappings to line '+line+'?'))return;m.line=line;}
 for(const[si,ti]of Object.entries(m.index_map)){if(+ti===index&&+si!==SRC.src_index){const pair=U.mrd_pairs.some(([a,b])=>(a===+si&&b===SRC.src_index)||(b===+si&&a===SRC.src_index));if(pair)return alert('Cannot share: Must Stay Distinct — src i'+SRC.src_index+' and i'+si+' both appear in '+U.display_name+'.');}}
 pushUndo();m.index_map[SRC.src_index]=index;
 if(POL.target_palette_lines[line][index]==null)POL.target_palette_lines[line][index]=bestCramFor(SRC.arcade_rgb8).cram;
 $('#status').textContent=`${U.display_name} i${SRC.src_index} → L${line}:${index} (${POL.target_palette_lines[line][index]})`;afterChange();showTarget();}

function renderMapTable(){const T=$('#maptable');T.innerHTML='';if(!U)return;const map=(POL.usage_palette_mappings[U.usage_id]||{});const im=map.index_map||{};
 const head=el('div','maprow mono');head.innerHTML='<b>Source</b><b>Arcade</b><b>Mapped To</b><b>Target color</b><b></b>';T.appendChild(head);
 U.used_colors.forEach(c=>{const r=el('div','maprow mono');const ti=im[c.src_index];const tcram=ti!=null?POL.target_palette_lines[map.line][ti]:null;const trgb=cramToRGB(tcram);
  r.appendChild(el('span',null,'i'+c.src_index));const a=el('span');a.appendChild(swBox(c.arcade_rgb8));a.appendChild(el('span',null,' '+c.hex));r.appendChild(a);
  r.appendChild(el('span',null,ti!=null?('L'+map.line+':'+ti):'—'));const t=el('span');if(trgb){t.appendChild(swBox(trgb));t.appendChild(el('span',null,' '+tcram));}else t.textContent='—';r.appendChild(t);
  const rm=el('span');if(ti!=null){const b=el('button','mini','unmap');b.onclick=()=>{pushUndo();delete im[c.src_index];afterChange();};rm.appendChild(b);}r.appendChild(rm);T.appendChild(r);});}

function renderTarget(){const G=$('#genlines');G.innerHTML='';for(let line=0;line<4;line++){const row=el('div','line'+(line===ACTIVE?' activeline':''));const lb=el('span','lbl'+(line===ACTIVE?' on':''),'LINE '+line+(line===ACTIVE?' ▸':''));lb.style.cursor='pointer';lb.onclick=()=>{ACTIVE=line;renderTarget();if(SRC)showColorProps(SRC);};row.appendChild(lb);
  const clc=SRC?closestInLine(SRC,line):null;
 for(let i=0;i<16;i++){const cram=POL.target_palette_lines[line][i];const rgb=cramToRGB(cram);const s=el('div','sw'+(i===0?' tp':''));if(rgb&&i!==0)s.style.background=`rgb(${rgb.join(',')})`;
  if(TGT&&TGT.line===line&&TGT.index===i)s.classList.add('picked');
   let dtip='';if(clc&&cram){const de=deltaE00(SRC.arcade_rgb8,cramToRGB(cram));dtip=' Δ'+de.toFixed(1);
     if(clc.absolute&&clc.absolute.index===i){s.classList.add((clc.legal&&clc.legal.index===i)?'nearestlegal':'nearestforbid');}
     else if(clc.legal&&clc.legal.index===i)s.classList.add('nearestlegal');}
   s.title=`L${line}:${i} ${cram||'(empty)'}${dtip}`;s.onclick=()=>{TGT={line,index:i};ACTIVE=line;renderTarget();showTarget();if(SRC&&U){mapWithAuto(line,i);}};
   s.ondragover=e=>{e.preventDefault();s.classList.add(cram?'dropshare':'dropok');};s.ondragleave=()=>{s.classList.remove('dropok','dropshare');};
   s.ondrop=e=>{e.preventDefault();s.classList.remove('dropok','dropshare');TGT={line,index:i};mapWithAuto(line,i);};row.appendChild(s);}
 G.appendChild(row);}}
function showTarget(){const P=$('#props');P.innerHTML='';if(!TGT)return;const cram=POL.target_palette_lines[TGT.line][TGT.index];const rgb=cramToRGB(cram)||[40,40,50];
 P.appendChild(txt(`GENESIS TARGET  L${TGT.line} : ${TGT.index}\nCRAM: ${cram||'(empty)'}\nRGB approx: ${rgb.join(', ')}`));
 if(TGT.index===0){P.appendChild(el('div','vitem WARN','Index 0 is transparent/background-reserved.'));}
 // Genesis color picker (R/G/B levels 0-7)
 const pk=el('div','picker');['R','G','B'].forEach((ch,ci)=>{const w=cram?parseInt(cram):0;const cur=(w>>(1+ci*4))&7;const lab=el('label',null,ch+' ');const inp=el('input');inp.type='range';inp.min=0;inp.max=7;inp.value=cur;inp.oninput=()=>{const levels=[0,1,2].map(k=>k===ci?+inp.value:((cram?parseInt(cram):0)>>(1+k*4))&7);const nc='0x'+(((levels[2]<<9)|(levels[1]<<5)|(levels[0]<<1))>>>0).toString(16).padStart(4,'0').toUpperCase();pushUndo();POL.target_palette_lines[TGT.line][TGT.index]=nc;afterChange();showTarget();};lab.appendChild(inp);pk.appendChild(lab);});P.appendChild(pk);
 // map selected source here
 if(U&&SRC){const b=el('button',null,`Map "${U.display_name}" src i${SRC.src_index} → L${TGT.line}:${TGT.index}`);b.onclick=()=>mapSrcToTarget();P.appendChild(b);}
 else P.appendChild(el('div','dim','Select a source color (center) to map it here.'));
 // show sources mapped here
 const users=sourcesAt(TGT.line,TGT.index);if(users.length){P.appendChild(el('div','vitem PASS','Sources mapped here: '+users.map(u=>u.name+' i'+u.si).join(', ')));}
 const cl=el('button','mini','clear entry');cl.onclick=()=>{pushUndo();POL.target_palette_lines[TGT.line][TGT.index]=null;Object.values(POL.usage_palette_mappings).forEach(m=>{if(m.line===TGT.line)for(const k in m.index_map)if(m.index_map[k]===TGT.index)delete m.index_map[k];});afterChange();};P.appendChild(cl);}
function sourcesAt(line,index){const out=[];for(const[uid,m]of Object.entries(POL.usage_palette_mappings)){if(m.line!==line)continue;for(const[si,ti]of Object.entries(m.index_map||{}))if(+ti===index){const u=O.usages.find(x=>x.usage_id===uid);out.push({name:u?u.display_name:uid,si});}}return out;}

function mapSrcToTarget(){if(POL.immutable)return alert('Create an editable profile first.');const uid=U.usage_id;const m=POL.usage_palette_mappings[uid]||(POL.usage_palette_mappings[uid]={line:TGT.line,index_map:{}});
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
 const map=POL.usage_palette_mappings[U.usage_id];const pal=[[0,0,0]];for(let i=1;i<16;i++)pal[i]=[60,60,72];
 U.used_colors.forEach(c=>{let rgb=c.genesis_rgb8;if(map&&map.index_map[c.src_index]!=null){const cr=POL.target_palette_lines[map.line][map.index_map[c.src_index]];const g=cramToRGB(cr);if(g)rgb=g;}pal[c.src_index]=rgb;});
 const t=el('div','pv');t.appendChild(el('div','pvh','GENESIS TARGET (same geometry, mapped colors)'));
 const i2=new Image();i2.className='pimg';i2.onload=()=>sizeImg(i2);i2.src=`/api/render?usage=${uid}&target=${encodeURIComponent(JSON.stringify(pal))}${b}`;t.appendChild(i2);P.appendChild(t);}

function ctxFit(c){const seg=O.coexistence.layer_a_active_banks_per_segment||{};let maxA=0;Object.values(seg).forEach(a=>maxA=Math.max(maxA,a.length));
 const P=$('#props');P.innerHTML='';P.appendChild(txt(`CONTEXT: ${c.display||c.id}\nTARGET PALETTE FIT\nLines used: ${POL.target_palette_lines.filter(l=>l.some(x=>x!=null)).length} / 4\n`+POL.target_palette_lines.map((l,i)=>`  Line ${i}: ${l.filter((x,k)=>x!=null&&k!==0).length} / 15 entries`).join('\n')+`\nmax simultaneous Layer-A banks (real): ${maxA} + 1 Layer-B\nUNKNOWN objects: ${O.objects.filter(o=>statusOf(o)!=='PROVEN').length}`));}
function showPaletteResource(p){const P=$('#props');P.innerHTML='';const dg=Object.values(O.exact_duplicate_palette_groups).find(g=>g.includes(p.palette_id));
 P.appendChild(txt(`PALETTE RESOURCE ${p.palette_id}\nselector ${p.arcade_selector} · domain ${p.domain}\ncontent_id ${p.content_id}`));
 if(dg)P.appendChild(el('div','vitem PASS','LOSSLESS SHARING OPPORTUNITY — identical content: '+dg.join(', ')));}

function closestInLine(c,line){/* nearest populated entry by ΔE00; nearest LEGAL (no MRD conflict for current usage U) */
 let abs=null,legal=null;const L=POL.target_palette_lines[line];
 for(let i=1;i<16;i++){const cram=L[i];if(cram==null)continue;const de=deltaE00(c.arcade_rgb8,cramToRGB(cram));
  if(abs===null||de<abs.de)abs={index:i,de};
  // legal if mapping c here won't collide with an MRD partner of c already mapped here (same usage U)
  let ok=true;if(U){const m=POL.usage_palette_mappings[U.usage_id];if(m&&m.line===line){for(const[si,ti]of Object.entries(m.index_map)){if(+ti===i&&+si!==c.src_index&&U.mrd_pairs.some(([a,b])=>(a===+si&&b===c.src_index)||(b===+si&&a===c.src_index))){ok=false;break;}}}}
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
 [0,1,2,3].forEach(line=>{const b=el('button',null,'Apply to Line '+line);b.onclick=()=>applySolution(sol,line);P.appendChild(b);});
 // preview each object with proposed palette
 const PV=$('#previews');PV.innerHTML='';PV.appendChild(el('div','pvh','SHARED PALETTE — per-object preview (arcade left / proposed right)'));
 GROUP.forEach(uid=>{const u=O.usages.find(x=>x.usage_id===uid);if(!u)return;const pal=proposedPal(sol,u);
  const wrap=el('div','pv');wrap.appendChild(el('div','pvh',u.display_name));
  const a=new Image();a.className='pimg';a.style.height='90px';a.src='/api/render?usage='+encodeURIComponent(uid);wrap.appendChild(a);
  const g=new Image();g.className='pimg';g.style.height='90px';g.src='/api/render?usage='+encodeURIComponent(uid)+'&target='+encodeURIComponent(JSON.stringify(pal));wrap.appendChild(g);PV.appendChild(wrap);});}
function proposedPal(sol,u){const pal=[[0,0,0]];for(let i=1;i<16;i++)pal[i]=[50,50,60];
 sol.entries.forEach(e=>{e.members.forEach(m=>{if(m.usage_id===u.usage_id)pal[m.src_index]=cramToRGB(e.cram);});});return pal;}
function applySolution(sol,line){if(POL.immutable)return alert('Create an editable profile first.');pushUndo();
 // one Undo transaction: set target line entries + remap each group usage
 sol.entries.forEach(e=>{POL.target_palette_lines[line][e.target_index]=e.cram;});
 GROUP.forEach(uid=>{const m=POL.usage_palette_mappings[uid]={line,index_map:{}};sol.entries.forEach(e=>e.members.forEach(mm=>{if(mm.usage_id===uid)m.index_map[mm.src_index]=e.target_index;}));});
 GROUP.forEach(uid=>{if(POL.usage_palette_mappings[uid])POL.usage_palette_mappings[uid].solver=sol.solver;});ACTIVE=line;$('#status').textContent='applied '+(sol.solver||'')+' shared palette → Line '+line+' ('+GROUP.size+' objects, 1 undo)';afterChange();}
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
function solveGroupShow(sol){SOLUTION=sol;const P=$('#props');P.innerHTML='';P.appendChild(txt('Selected proposal: '+sol.solver+' · entries '+sol.entries_used));[0,1,2,3].forEach(line=>{const b=el('button',null,'Apply to Line '+line);b.onclick=()=>applySolution(sol,line);P.appendChild(b);});}
function txt(s){return el('div','mono',s);}
function validate(){const V=$('#valid');V.innerHTML='';let err=0;
 // MRD violations across all usages
 let mrdV=0;for(const[uid,m]of Object.entries(POL.usage_palette_mappings)){const u=O.usages.find(x=>x.usage_id===uid);if(!u)continue;for(const[a,b]of u.mrd_pairs){if(m.index_map[a]!=null&&m.index_map[a]===m.index_map[b])mrdV++;}}
 if(mrdV){V.appendChild(el('div','vitem ERROR',`MRD violations (internal detail merged): ${mrdV}`));err++;}else V.appendChild(el('div','vitem PASS','MRD: 0 internal-detail merges'));
 const linesUsed=POL.target_palette_lines.filter(l=>l.some(x=>x!=null)).length;
 V.appendChild(el('div','vitem '+(linesUsed<=4?'PASS':'ERROR'),`target lines used: ${linesUsed}/4`));
 POL.target_palette_lines.forEach((l,i)=>{const n=l.filter((x,k)=>x!=null&&k!==0).length;if(n>15){V.appendChild(el('div','vitem ERROR',`Line ${i}: ${n}/15 nontransparent (overflow)`));err++;}});
 const maps=Object.keys(POL.usage_palette_mappings).length;V.appendChild(el('div','vitem '+(err?'ERROR':'PASS'),`usages mapped: ${maps} · errors: ${err}`));}
boot();
