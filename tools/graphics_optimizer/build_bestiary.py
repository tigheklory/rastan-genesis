#!/usr/bin/env python3
"""Regenerate the living Rastan actor bestiary / status report — MANIFEST-DRIVEN.

SEMANTIC SOURCE OF TRUTH: docs/design/rastan_actor_graphics_manifest.json (`actors`, `scripted_routes`,
`dashboard`, `remaining`, `authoritative_roster`). This generator holds NO independent actor/name/
palette/round registry. It only executes each actor's `render` spec and the ROM palette math.

AUTHORITATIVE inputs: original arcade maincpu.bin + pc090oj.bin, existing Ghidra static decompilation,
statically-proven ROM tables, and manifest fields backed by those (+ Palette Composer results the
manifest classifies proven).
SECONDARY / corroboration ONLY (never "authoritative static"): analysis/enemy_sprite_lexicon/
families.json + representative_pieces, Palette-Composer contact-sheet PNGs, runtime sweeps. These are
used only as *rendering inputs* for actors whose manifest `frame_provenance` marks them
LEGACY_PROVISIONAL / COMPOSER_PROVEN, and are labelled as such on the card.

REPORT MAINTENANCE RULE: after any actor-decompilation pass that changes identity / round / phase /
boss mapping / palette / frame / item-hazard classification, update the MANIFEST then re-run this and
republish the same artifact — in the same pass.
"""
import json, base64, io
from pathlib import Path
from PIL import Image
ROOT = Path(__file__).resolve().parents[2]
CS = ROOT/'analysis/graphics_optimizer/round1_phase1_corpus/contact_sheets'   # LEGACY/COMPOSER inputs
LEX = json.load(open(ROOT/'analysis/enemy_sprite_lexicon/families.json'))       # LEGACY geometry input
GEOM = {x['id']: x for x in LEX['families']}
EP = json.load(open(ROOT/'analysis/graphics_optimizer/round1_phase1_corpus/enemy_palettes.json'))['banks']  # Composer palettes
pc = (ROOT/'build/regions/pc090oj.bin').read_bytes()
mc = (ROOT/'build/regions/maincpu.bin').read_bytes()
M = json.load(open(ROOT/'docs/design/rastan_actor_graphics_manifest.json'))

# ---- ROM per-round palette (STATIC_DECOMPILED, validated) ----
def pal5(n): v=n*2; return (v<<3)|(v>>2)
def rom_field_palette(rnd, nibble):
    pidx = mc[0x3BA88 + (rnd-1)*32 + nibble]; b = 0x4FD02 + pidx*32
    cols=[(pal5((int.from_bytes(mc[b+i*2:b+i*2+2],'big')>>8)&0xF),
           pal5((int.from_bytes(mc[b+i*2:b+i*2+2],'big')>>4)&0xF),
           pal5(int.from_bytes(mc[b+i*2:b+i*2+2],'big')&0xF)) for i in range(16)]
    return cols, pidx
def composer_palette(key):
    return [tuple(int(c.lstrip('#')[i:i+2],16) for i in (0,2,4)) for c in EP[key]['mame_display_rgb8']], EP[key]['effective_sprite_bank']
GRAY=[(0,0,0)]+[(v,v,v) for v in (40,70,95,120,140,160,180,200,215,230,245,255,90,130,170)]

def dec(code):
    px=[[0]*16 for _ in range(16)]; b=code*128
    for r in range(16):
        for c in range(8):
            by=pc[b+r*8+c]; px[r][c*2]=by>>4; px[r][c*2+1]=by&0xF
    return px
def datauri(img):
    bio=io.BytesIO(); img.save(bio,'PNG'); return "data:image/png;base64,"+base64.b64encode(bio.getvalue()).decode()
def render_geo(geo_id, pal, scale=4):
    pcs=GEOM[geo_id]['representative_pieces']
    xs=[p['x'] for p in pcs]; ys=[p['y'] for p in pcs]; ox,oy=min(xs),min(ys)
    W=max(p['x'] for p in pcs)-ox+16; H=max(p['y'] for p in pcs)-oy+16
    img=Image.new('RGBA',(W,H),(0,0,0,0))
    for p in pcs:
        px=dec(p['code']); fh=p.get('flip_h'); fv=p.get('flip_v')
        for yy in range(16):
            for xx in range(16):
                idx=px[15-yy if fv else yy][15-xx if fh else xx]
                if idx:
                    X,Y=p['x']-ox+xx,p['y']-oy+yy
                    if 0<=X<W and 0<=Y<H: img.putpixel((X,Y),pal[idx]+(255,))
    bb=img.getbbox()
    if bb: img=img.crop(bb)
    return datauri(img.resize((img.width*scale,img.height*scale),Image.NEAREST))
def render_png(fn, scale=3):
    im=Image.open(CS/fn).convert('RGBA'); bg=im.getpixel((0,0)); d=list(im.getdata())
    im.putdata([(0,0,0,0) if abs(p[0]-bg[0])<10 and abs(p[1]-bg[1])<10 and abs(p[2]-bg[2])<10 else p for p in d])
    bb=im.getbbox()
    if bb: im=im.crop(bb)
    return datauri(im.resize((im.width*scale,im.height*scale),Image.NEAREST))

## ---- offline emulation of compositor VM 0x3C902 (general path, comp tables) ----
_VMTAB={0:0x3d09e,1:0x4771c,2:0x3f0ce,3:0x40004,4:0x4002c}
def _s8(v): return v-256 if v>=128 else v
def vm_pieces(base, anim, table=0):
    tab=_VMTAB[table]; a0=tab+int.from_bytes(mc[tab+anim*2:tab+anim*2+2],'big'); out=[]; n=20
    while n>0:
        ctrl=mc[a0]; a0+=1
        if ctrl==0xFF: break
        if ctrl&0xF0 not in (0x00,0x40,0x80,0x70): return None   # special op — not handled
        pf=1 if ctrl&0xF0==0x40 else 0
        b1=mc[a0]; b2=mc[a0+1]; b3=mc[a0+2]; a0+=3
        tile=(base-b2 if pf else base+b2)&0x3FFF
        out.append((tile, _s8(b3), _s8(b1), pf))   # (tile, x=coordB, y=coordA, hflip)  [validated on Lizardman]
        n-=1
    return out
def render_vm(base, anim, pal, table=0, scale=4):
    pcs=vm_pieces(base, anim, table)
    if not pcs: return None
    xs=[p[1] for p in pcs]; ys=[p[2] for p in pcs]; ox,oy=min(xs),min(ys)
    W=max(xs)-ox+16; H=max(ys)-oy+16
    img=Image.new('RGBA',(W,H),(0,0,0,0))
    for tile,x,y,pf in pcs:
        t=dec(tile)
        for yy in range(16):
            for xx in range(16):
                idx=t[yy][15-xx if pf else xx]
                if idx: img.putpixel((x-ox+xx,y-oy+yy),pal[idx]+(255,))
    bb=img.getbbox()
    if bb: img=img.crop(bb)
    return datauri(img.resize((img.width*scale,img.height*scale),Image.NEAREST))

def render_raw(base, cols=8, rows=6, pal=None, scale=3):
    """Raw pc090oj tile grid from base code — layout NOT composited (honest visual evidence)."""
    if pal is None: pal=GRAY
    W,H=cols*16,rows*16; img=Image.new('RGBA',(W,H),(0,0,0,0))
    for t in range(cols*rows):
        px=dec(base+t); tx,ty=(t%cols)*16,(t//cols)*16
        for y in range(16):
            for x in range(16):
                if px[y][x]: img.putpixel((tx+x,ty+y),pal[px[y][x]]+(255,))
    return datauri(img.resize((W*scale,H*scale),Image.NEAREST))

def render_actor(a, rnd):
    """Return (img_datauri_or_None, palette_swatch_html) per the manifest render spec."""
    spec=a.get('render',{}); method=spec.get('method','none'); pal=None; sw=''
    ps=spec.get('palette',{}) or {}
    if ps.get('kind')=='rom_field' and rnd:
        pal,pidx=rom_field_palette(rnd, ps['nibble'])
        sw=f'<div class="palbank ok">bank 0x{0x30|ps["nibble"]:02X} · pool {pidx} · ROM (per round)</div>'
    elif ps.get('kind')=='composer_key':
        pal,bk=composer_palette(ps['key']); sw=f'<div class="palbank ok">bank {bk} · Composer-proven</div>'
    if pal:
        sw+='<div class="sw">'+''.join(f'<i style="background:rgb({r},{g},{b})"></i>' for r,g,b in pal)+'</div>'
    else:
        sw='<div class="palpend">PALETTE PENDING</div>'
    if method=='vm':
        img=render_vm(a['render']['base'], a['render']['anim'], pal or GRAY, a['render'].get('compositor_table',0))
        return img, sw
    if method=='composer_png':
        return render_png(a['render']['png']), sw
    if method=='rom_geo':
        return render_geo(a['render']['geo_id'], pal or GRAY), sw
    if method=='geo_grayscale':
        return render_geo(a['render']['geo_id'], GRAY), sw   # provisional, no proven palette
    return None, sw

def badges(a):
    idn=a['name_status']; fr=a['frame_status']; pal=a['palette_status']
    def bmap(v):
        return {'PROVEN':'ok','COMPOSER_PROVEN':'ok','STATIC_DECOMPILED':'ok','PROPOSED':'part','PARTIAL':'part',
                'PROVISIONAL':'part','PENDING':'pend','UNRESOLVED':'pend'}.get(v,'pend')
    frtxt={'COMPOSER_PROVEN':'FRAME PROVEN','PROVISIONAL':'FRAME PROVISIONAL','PENDING':'FRAME PENDING'}.get(fr,'FRAME '+fr)
    php=a.get('phase_presence','')
    phb=('<span class="b part">PHASE position-based</span>' if 'position' in php else '<span class="b pend">PHASE PENDING</span>')
    return (f'<span class="b {bmap(idn)}">IDENTITY {idn}</span>'
            f'<span class="b ok">ROUND PROVEN</span>{phb}'
            f'<span class="b {bmap(fr)}">{frtxt}</span>'
            f'<span class="b {bmap(pal)}">PALETTE {pal}</span>')

def card(a, rnd, extra_class=''):
    img,sw=render_actor(a, rnd)
    if img:
        prov='' if a['frame_provenance']=='COMPOSER_PROVEN' else f'<div class="provtag">{a["frame_provenance"].replace("_"," ").lower()}</div>'
        frame=f'<div class="frame">{prov}<img src="{img}"></div>'
    else:
        frame=f'<div class="frame pend"><b>FRAME PENDING</b><br><span>{a.get("unresolved_reason","")}</span></div>'
    return f'''<article class="card {extra_class}">{frame}<div class="body">
      <div class="bar">{badges(a)}</div><h4>{a['semantic_name']}</h4><p class="desc">{a['description']}</p>
      <dl><dt>Base</dt><dd class="mono">{a['base_graphics']}</dd><dt>Spawn</dt><dd>{a['spawn_route']}</dd>
      <dt>Frame src</dt><dd class="mono">{a['frame_source']}</dd></dl>{sw}</div></article>'''

def boss_card(a):
    rn=a.get('render',{}); pl=a.get('palette',{})
    if rn.get('method')=='rom_geo_boss' and rn.get('geo_id') in GEOM and GEOM[rn['geo_id']].get('representative_pieces'):
        pal,pidx=rom_field_palette(rn['palette_round'], rn['palette_nibble'])
        img=render_geo(rn['geo_id'], pal)
        sw=(f'<div class="palbank ok">boss bank · nibble 0x{rn["palette_nibble"]:X} · pool {pidx} · ROM per-round</div>'
            '<div class="sw">'+''.join(f'<i style="background:rgb({r},{g},{b})"></i>' for r,g,b in pal)+'</div>')
        frame=f'<div class="frame"><div class="provtag">composite · per-round palette</div><img src="{img}"></div>'
        bar='<span class="b ok">ROUTE PROVEN</span><span class="b ok">ROUND PROVEN</span><span class="b ok">FRAME COMPOSITE</span><span class="b ok">PALETTE PER-ROUND</span><span class="b part">SEED/COMPONENTS PARTIAL</span>'
    else:
        frame=f'<div class="frame pend"><b>CLEAN BOSS FRAME PENDING</b><br><span>{a.get("unresolved_reason","")}</span></div>'
        sw=''; bar='<span class="b ok">ROUTE PROVEN</span><span class="b ok">ROUND PROVEN</span><span class="b part">SEED PARTIAL</span><span class="b pend">BODY PENDING</span><span class="b pend">PALETTE PENDING</span>'
    return f'''<article class="card boss">{frame}
      <div class="body"><div class="bar">{bar}</div>
      <h4>{a['semantic_name']}</h4><p class="desc">{a['description']}. <b>base 0x033E is the shared family-2 route, NOT the identity.</b> {a.get("creation","")} {a.get("anim_override","")}</p>
      <dl><dt>Base</dt><dd class="mono">{a['base_graphics']}</dd><dt>Path</dt><dd>{a['spawn_route']}</dd></dl>{sw}</div></article>'''

# ---- assemble from manifest ----
actors=M['actors']; scripted=M.get('scripted_routes',[])
by_cat=lambda c:[a for a in actors if a['category']==c]
field=[a for a in actors if a['category']=='ENEMY_FIELD']
bosses={a['round_presence'][0]:a for a in actors if a['category']=='BOSS'}
def field_in_round(r): return [a for a in field if r in a.get('round_presence',[])]

rounds_html=""
per=M['authoritative_roster']['per_round']
BBM=M['scene_phase_state_machine'].get('background_bank_scene_map',{})
BSEQ=BBM.get('per_round_bank_sequence',{})
def bankrow(r):
    b=BSEQ.get(f'R{r}')
    if not b: return ''
    mc=b['mid_round_change']
    cls='ok' if mc!='none' else 'pend'
    lbl=('PROVEN mid-round background change '+mc) if mc!='none' else 'single background bank (no static mid-round change)'
    return (f'<div class="phaserow"><div class="pbox"><b>Background banks (TT) — 0x13E {b["range"]}</b>'
            f'<span class="mono bankseq">{b["banks"]}</span>'
            f'<span class="{cls}">{lbl}</span></div></div>')
for r in range(1,7):
    cards="".join(card(a,r) for a in sorted(field_in_round(r), key=lambda a:a['actor_family_3e']))
    scr=[s for s in scripted if s['round']==r]
    if scr:
        def phcls(ph): return 'ok' if ph.startswith('BOSS') else 'pend'
        rows="".join(f'<tr><td class="mono">{s["route_pc"]}</td><td>{s["role"]}</td><td class="mono">{s["oneshot"]}</td><td>{s["identity"]}</td><td class="{phcls(s.get("phase",""))}">{s.get("phase","—")}</td></tr>' for s in scr)
        sctab=f'<table class="sc"><tr><th>route PC</th><th>role</th><th>one-shot</th><th>identity</th><th>phase (control-flow)</th></tr>{rows}</table>'
    else:
        sctab='<p class="muted">No individually-proven Round-'+str(r)+' scripted route yet (dispatch family identified).</p>'
    boss=boss_card(bosses[r]) if r in bosses else ''
    rounds_html+=f'''<section class="round"><div class="rhead"><h2>Round {r}</h2><span class="rmeta mono">A5+0x13E {per[str(r)]["r13E"]}</span></div>
      <h3 class="grp">Field roster — PROVEN for round <span>(0x4A104 schedule; spans the whole round — Phase-1/2 split blocked on door-tile 0x13E)</span></h3><div class="grid">{cards}</div>
      {bankrow(r)}
      <h3 class="grp">Scripted encounters <span>(scene-driven, A5+0x13E dispatch)</span></h3>{sctab}
      <h3 class="grp">Boss</h3><div class="grid">{boss}</div></section>'''

special_html="".join(card(a,None) for a in actors if a['category']=='ENEMY_SCRIPTED' or (a['category']=='UNRESOLVED'))
# ---- Complete ROM actor census (all distinct base graphics) ----
CEN=M.get('actor_census_from_rom',{})
def census_rows():
    out=[]
    for c in sorted(CEN.get('actors',[]),key=lambda c:c['base']):
        st=c['name_status']; cls={'PROVEN':'ok','PROPOSED':'part','PARTIAL':'part','PENDING':'pend'}.get(st,'pend')
        rp=c.get('round_presence')
        rptxt=" ".join("<span class='rp'>%s<i>%s</i></span>"%(k,"/".join(v)) for k,v in rp.items()) if rp else "<span class='muted'>code-spawned / scripted — round not pinned</span>"
        cre="; ".join(c['creation'])
        out.append(f"<tr><td class='mono'>{c['base']}</td><td><b>{c['name']}</b> <span class='b {cls}'>{st}</span></td><td class='pcell'>{rptxt}</td><td class='mono small'>{cre}</td></tr>")
    return "".join(out)
def newfound_section():
    items=[]
    specs=[('0x061D',0x061D,3,0,'CENTAUR — PROPOSED','Quadruped/horse-body tiles with upper torsos. Loaded via record-loader table 0x45592 rec6/7 (0x4543e, +0x06 path) — missed by earlier passes. Identity PROPOSED from tile shape + user report; not ROM-string-proven.'),
             ('0x0988',0x0988,3,0,'Serpent/Dragon — PROPOSED','Curved serpentine segments + head. Table 0x45592 rec8/9. PROPOSED.')]
    for base,code,rnd,nib,title,note in specs:
        pal,_=rom_field_palette(rnd,nib)
        img=render_raw(code,8,7,pal)
        items.append(f'<article class="card"><div class="frame"><div class="provtag">raw tiles · not composited</div><img src="{img}"></div><div class="body"><div class="bar"><span class="b part">IDENTITY PROPOSED</span><span class="b part">RAW TILES</span><span class="b pend">LAYOUT PENDING</span></div><h4>{title} <span class="mono">{base}</span></h4><p class="desc">{note}</p></div></article>')
    return ('<section class="round"><h2>Newly found actors — raw ROM tile evidence</h2>'
            '<div class="statusbox part"><b>Two bases earlier passes missed</b> (loaded via the <span class="mono">+0x06</span> record-type path through <span class="mono">0x4543e</span>/table <span class="mono">0x45592</span>, distinct from the family/variant tables). Shown as <b>raw pc090oj tiles</b> — the compositor <span class="mono">0x3C902</span> layout is not yet decoded, so tile arrangement is not final; this is honest sprite-content evidence, not a finished frame.</div>'
            f'<div class="grid">{"".join(items)}</div></section>')

census_html=newfound_section()+f"""<section class="round"><h2>Complete Actor Census — from ROM decompilation</h2>
<div class="statusbox ok"><b>{CEN.get('distinct_base_count','?')} distinct base-graphics actors</b> resolved statically from <span class="mono">maincpu.bin</span>. Field schedule <span class="mono">0x4A104</span> record byte1=<span class="mono">+0x3E</span> family, byte2 hi-nibble=<span class="mono">+0x752</span> variant → base via tables <span class="mono">0x45502</span> (var 0) / <span class="mono">0x45562</span> (var≠0) / boss <span class="mono">0x454ba</span>; plus every immediate write to <span class="mono">actor+0x1E</span> (code-spawned projectiles / sub-objects). <b>Semantic names are PROPOSED (lexicon) or PENDING — never invented.</b> Round columns show 0x13E position thirds (early/mid/<b>late≈phase 2/3</b>; exact door boundary still blocked).</div>
<div class="tblwrap"><table class="census"><tr><th>base</th><th>actor / name status</th><th>round · position (phase)</th><th>creation route (ROM)</th></tr>{census_rows()}</table></div></section>"""
dash_html="".join(f'<div class="dcell {c}"><span class="dk">{k}</span><span class="dv">{v}</span></div>' for k,v,c in M['dashboard'])
remain_html="".join(f'<li><span class="rs {("done" if s=="DONE" else "part" if s=="PARTIAL" else "ns")}">{s}</span> {t}</li>' for t,s in M['remaining'])

STYLE=(ROOT/'tools/graphics_optimizer/bestiary_style.css').read_text()
doc=f'''<title>Rastan Bestiary</title>{STYLE}
<header class="hero"><div class="in"><div class="kicker">Rastan · Original Arcade · Living Decompilation Status</div>
<h1>Rastan Actor Bestiary &amp; Status</h1>
<p class="sub">A living view of the static arcade decompilation, generated <b>entirely from the authoritative manifest</b> (rastan_actor_graphics_manifest.json). Rounds &amp; field rosters are ROM-proven; palettes are decoded per-round from the arcade ROM. Every card shows independent IDENTITY / FRAME / PALETTE confidence. Provisional images (from the legacy lexicon/Composer captures) are labelled as such; nothing unproven is presented as authoritative.</p>
<h2 class="dash-h">Arcade Actor Decompilation Status</h2><div class="dash">{dash_html}</div></div></header>
<div class="wrap">{census_html}
{rounds_html}
<section class="round"><h2>Special / Map-Driven Spawns</h2><p class="muted">Scene-/marker-triggered actors (not the field schedule). Identity/frame/palette shown per manifest provenance; unproven actors are labelled <span class="mono">Actor 0xXXXX</span> with PENDING status, never a guessed name or colour.</p><div class="grid">{special_html}</div></section>
<section class="round"><h2>Hazards / Obstacles</h2><div class="statusbox part"><b>PARTIAL — map-marker routes not fully decoded.</b> From map collision markers (0x559B2 → 0x41180); only marker 0x48 (class 0x70) is graphics-proven. No hazard cards until static identity is proven (old JSON names are not authoritative).</div></section>
<section class="round"><h2>Items / Power-ups / Pickups</h2><div class="statusbox pend"><b>SYSTEM NOT YET DECOMPILED.</b> The item/drop/pickup subsystem (death-drops, map pickups, pickup-collision, weapon changes via A5+0x138C) has not been located in the arcade code. Deliberately empty — not populated from memory or screenshots.</div></section>
<section class="round"><h2>Phase-1 → Phase-2 transition — MECHANISM PROVEN (control flow)</h2>
<div class="statusbox ok"><b>The mid-round phase transition is data-driven by a map-collision tile, not a scene table and not the background bank.</b> The player↔map probe (<span class="mono">player_ground_contact_probe_family_53b34</span> + horizontal probe <span class="mono">0x53e22–0x54050</span>) reads the collision grid at <span class="mono">0x10DE00</span> (= <span class="mono">A5+0x1E00</span>) via <span class="mono">0x53a2e</span>; tile type = <span class="mono">cell &amp; 0x7F</span>. <b>Tile type <span class="mono">0x7E</span> (126) = the door → <span class="mono">A5+0x10E8 := 7</span></b> (<span class="mono">0x53f0c</span>, <span class="mono">0x54038</span>); type 8 → <span class="mono">0x10E8:=8</span>. Consumed at <span class="mono">0x3a7d2</span> (saves <span class="mono">0x1242:=0x13E</span>, state 2, <span class="mono">0x0104:=1</span>) → screen-wipe (<span class="mono">0x1394</span>/<span class="mono">0x13aa</span>/<span class="mono">0x138a</span>) + actor-clear (<span class="mono">0x3a804</span>) + scene reload + <span class="mono">0x13E</span> restore. Round-complete is distinct: <span class="mono">0x10E8:=16</span> (<span class="mono">0x51250</span>) at a 0x502AC boundary.</div>
<div class="statusbox ok"><b>A5 = 0x10C000 (arcade base) — verified this pass.</b> Hence <span class="mono">0x10D000 = A5+0x1000</span> (16 map-column stream ptrs, <span class="mono">0x502cc</span>) and <span class="mono">0x10D0A8 = A5+0x10A8</span> = the section-kind, which is set from the <b>map-stream byte at ROM 0x50F6B</b> (indexed by 0x13E via 0x50EE0). That stream holds only <b>{0,1,2}</b>, so the director's <span class="mono">A5+0x10A8∈{{4,5,6}}</span> path (0x527cc) is <b>DEAD CODE</b> — the <span class="mono">0x7E</span> tile is the sole live wipe trigger.</div>
<div class="statusbox pend"><b>Exact blocker (not fabricated):</b> no code writes <span class="mono">0x7E</span> into the collision grid, so it is a <b>metatile-property value in the map data</b>. Enumerating per-round door <span class="mono">0x13E</span> needs the metatile→collision-property mapping + the per-round metatile-column source feeding collision-grid field <span class="mono">@(20)</span> — a full map-engine decode. <b>Boundary pinned: 0/6</b> (mechanism proven; positions blocked). No screenshot or TT-bank appearance is used as the phase authority.</div>
<h3 class="grp">Background-bank (TT) map — SUPPORTING evidence only <span>(not the phase-defining field)</span></h3>
<div class="statusbox part"><span class="mono">0x13E → 0x507C5 → scene index → 12-byte descriptor 0x3951C</span>; the <span class="mono">TT</span> byte is the background-tileset bank (streamed at <span class="mono">0x55c7a</span>). Mid-round bank change PROVEN only in <b>R3 (@0x36)</b>, <b>R5 (@0x6C, @0x72)</b>, <b>R6 (@0x83, @0x89)</b>; <b>R1/R2/R4 stream one bank</b> — which is exactly why a bank change cannot define the gameplay phase (R1/R2/R4 cross the phase within one bank). <span class="mono">TT0E</span>(R5)/<span class="mono">TT0F</span>(R6) are boss-arena banks. Detail: <span class="mono">Andy_outdoor_castle_section_map.md</span>, <span class="mono">Andy_scene_phase_state_machine.md</span>.</div></section>
<section class="round"><h2>What remains to complete this bestiary</h2><ol class="remain">{remain_html}</ol></section>
<footer>Generated from <span class="mono">rastan_actor_graphics_manifest.json</span> by <span class="mono">tools/graphics_optimizer/build_bestiary.py</span>. Authoritative: maincpu.bin, pc090oj.bin, Ghidra static decomp, ROM tables, manifest fields backed by those, Composer results classified proven. Secondary/corroboration only: families.json / representative_pieces / contact sheets / sweeps. Palettes ROM-decoded (0x3BA88→0x4FD02, validated). Boss composites deprecated pending clean reconstruction.</footer></div>'''
(ROOT/'docs/design/rastan_actor_bestiary.html').write_text(doc)
print(f"wrote {len(doc)} bytes; actors={len(actors)} field={len(field)} bosses={len(bosses)} scripted={len(scripted)}")
