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
from compositor_vm import ActorRenderState, SpecialCompositorProgram, visible_pieces
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

def render_vm(base, anim, pal, table=0, scale=4):
    try:
        sat=visible_pieces(ActorRenderState(base, anim, table))
    except SpecialCompositorProgram:
        return None
    if not sat: return None
    def s9(value):
        value &= 0x1ff
        return value - 0x200 if value & 0x100 else value
    pcs=[(p.tile & 0x1fff, s9(p.x), s9(p.y), p.hflip, p.vflip) for p in sat]
    xs=[p[1] for p in pcs]; ys=[p[2] for p in pcs]; ox,oy=min(xs),min(ys)
    W=max(xs)-ox+16; H=max(ys)-oy+16
    img=Image.new('RGBA',(W,H),(0,0,0,0))
    for tile,x,y,fh,fv in pcs:
        t=dec(tile)
        for yy in range(16):
            for xx in range(16):
                idx=t[15-yy if fv else yy][15-xx if fh else xx]
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
    elif ps.get('kind')=='materialized_fam2':
        pal,pidx=rom_field_palette(ps['round'], ps['nibble'])
        sw=f'<div class="palbank part">line 0x{ps["nibble"]:X} · fam-2 (0x456EC) · round-{ps["round"]} representative · ROUND PENDING</div>'
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
    if method=='raw':
        return render_raw(a['render']['base'], cols=8, rows=5), sw   # RAW TILE EVIDENCE (not composited)
    return None, sw

def _bmap(v):
    return {'PROVEN':'ok','COMPOSER_PROVEN':'ok','STATIC_DECOMPILED':'ok','VM_LEGAL':'ok','PROPOSED':'part','PARTIAL':'part',
            'PROVISIONAL':'part','RAW_TILE_ONLY':'pend','PENDING':'pend','UNRESOLVED':'pend'}.get(v,'pend')

def badges(a):
    """OBJECT (technical) and NAME (human) are shown SEPARATELY so a lexicon label
    never reads as a proven arcade identity."""
    ns=a['name_status']; fr=a['frame_status']; pal=a['palette_status']; cat=a['category']
    # technical object: proven for every real base we have; controller = architecture
    if cat=='CONTROLLER':
        objb='<span class="b sp">CONTROLLER (not a sprite)</span>'
    else:
        objb='<span class="b ok">OBJECT PROVEN</span>'
    nameb=f'<span class="b {_bmap(ns)}">NAME {ns}</span>'
    # round
    rp=a.get('round_presence') or []
    if cat=='CONTROLLER': roundb=''
    elif rp: roundb='<span class="b ok">ROUND PROVEN</span>'
    else: roundb='<span class="b pend">ROUND PENDING</span>'
    frtxt={'COMPOSER_PROVEN':'FRAME PROVEN','PROVISIONAL':'FRAME PROVISIONAL','VM_LEGAL':'FRAME LEGAL (VM)',
           'RAW_TILE_ONLY':'RAW TILE ONLY','PENDING':'FRAME PENDING'}.get(fr,'FRAME '+fr)
    palb=f'<span class="b {_bmap(pal)}">PALETTE {pal}</span>' if cat!='CONTROLLER' else ''
    return objb+nameb+roundb+f'<span class="b {_bmap(fr)}">{frtxt}</span>'+palb

def card(a, rnd, extra_class=''):
    img,sw=render_actor(a, rnd)
    israw=(a.get('render') or {}).get('method')=='raw'
    if img:
        if israw:
            prov='<div class="provtag rawtag">RAW TILE EVIDENCE · not composited</div>'
        else:
            prov='' if a['frame_provenance']=='COMPOSER_PROVEN' else f'<div class="provtag">{a["frame_provenance"].replace("_"," ").lower()}</div>'
        frame=f'<div class="frame {"raw" if israw else ""}">{prov}<img src="{img}"></div>'
    else:
        frame=f'<div class="frame pend"><b>FRAME PENDING</b><br><span>{a.get("unresolved_reason","")}</span></div>'
    route=a.get('materialization_route')
    routerow=(f'<dt>Route</dt><dd class="mono">marker {route.get("marker","—")} → state {route.get("state","—")} → {route.get("handler","—")}</dd>'
              if route else '')
    return f'''<article class="card {extra_class}">{frame}<div class="body">
      <div class="bar">{badges(a)}</div><h4>{a['semantic_name']}</h4><p class="desc">{a['description']}</p>
      <dl><dt>Base</dt><dd class="mono">{a['base_graphics']}</dd><dt>Spawn</dt><dd>{a['spawn_route']}</dd>
      {routerow}<dt>Frame src</dt><dd class="mono">{a['frame_source']}</dd></dl>{sw}</div></article>'''

def boss_card(a):
    rn=a.get('render',{}); rnd=a['round_presence'][0]; ver=rn.get('verified')
    nib=rn.get('palette',{}).get('nibble',0xF)
    pal,pidx=rom_field_palette(rnd, nib)
    img=render_vm(rn['base'], rn['anim'], pal, rn.get('compositor_table',1)) if rn.get('method')=='vm' else None
    if img:
        tag='body frame + palette · MAME-verified (Cody)' if ver else 'body frame = ROM init-anim · UNVERIFIED'
        frame=f'<div class="frame"><div class="provtag">{tag}</div><img src="{img}"></div>'
        sw=(f'<div class="palbank {"ok" if ver else "part"}">boss line 0x{nib:X} · pool {pidx} · ROM per-round{" (Cody-verified)" if ver else " · line inferred"}</div>'
            '<div class="sw">'+''.join(f'<i style="background:rgb({r},{g},{b})"></i>' for r,g,b in pal)+'</div>')
    else:
        frame=f'<div class="frame pend"><b>BODY FRAME PENDING</b><br><span>{a.get("unresolved_reason","")}</span></div>'; sw=''
    fb='ok' if ver else 'part'
    bar=(f'<span class="b ok">BODY PROVEN</span><span class="b ok">ROUND PROVEN</span>'
         f'<span class="b ok">TYPE 0x{a.get("boss_body_record_type",0):02X}</span>'
         f'<span class="b {fb}">{"FRAME VERIFIED" if ver else "FRAME STATIC"}</span>'
         f'<span class="b {fb}">{"PALETTE VERIFIED" if ver else "PALETTE line-inferred"}</span>')
    return f'''<article class="card boss">{frame}
      <div class="body"><div class="bar">{bar}</div>
      <h4>{a['semantic_name']}</h4><p class="desc">{a['description']}</p>
      <dl><dt>Body base</dt><dd class="mono">{a['base_graphics']}</dd>
      <dt>Record type</dt><dd class="mono">{a.get("boss_body_record_type")} (0x45592→0x4543E)</dd>
      <dt>Compositor</dt><dd class="mono">{a.get("boss_compositor")}</dd>
      <dt>Slot</dt><dd class="mono">{a.get("boss_body_slot")}</dd>
      <dt>Trigger</dt><dd class="mono">{a.get("boss_trigger")}</dd>
      <dt>Components</dt><dd>{a.get("boss_components")}</dd></dl>{sw}</div></article>'''

# ---- assemble from manifest (actors[] is the SOLE semantic actor source of truth) ----
actors=M['actors']; scripted=M.get('scripted_routes',[])
field=[a for a in actors if a['category']=='ENEMY_FIELD']
materialized=[a for a in actors if a['category']=='ENEMY_MATERIALIZED']
controllers=[a for a in actors if a['category']=='CONTROLLER']
scripted_actors=[a for a in actors if a['category']=='ENEMY_SCRIPTED']
unresolved=[a for a in actors if a['category']=='UNRESOLVED']
bosses={a['round_presence'][0]:a for a in actors if a['category']=='BOSS'}
def field_in_round(r): return [a for a in field if r in a.get('round_presence',[])]

def gallery(title, sub, lst, rnd=None, intro=''):
    if not lst: return ''
    cards="".join(card(a,rnd) for a in lst)
    introhtml=f'<div class="statusbox part">{intro}</div>' if intro else ''
    return f'<section class="round"><h2>{title} <span>{sub}</span></h2>{introhtml}<div class="grid">{cards}</div></section>'

# master galleries (before the per-round sections) — driven ENTIRELY by actors[]
gal_field=gallery("Field / Sub-Round-1 Actor Gallery", f"({len(field)} field-schedule enemies · 0x4A104)",
                  sorted(field,key=lambda a:a['base_graphics']))
gal_mat=gallery("Materialized / Marker-Driven Actor Gallery",
                f"({len(materialized)} H5/H6 materialized + {len(controllers)} controller)",
                sorted(materialized,key=lambda a:a['base_graphics'])+controllers,
                intro="Actors the marker/hunter system (0x41180 → 0x41362 → 0x40BAA state handlers) materializes in the later / sub-round-2 part of a round. <b>H10 assembled legal arcade frames</b> for all 12 via the proven render dispatch (0x3D054 → 0x3C902); colours use the family-2 palette line (0x45684 → 0x456EC) at a <b>round-representative</b> instance (exact round PENDING). Human identity + exact round remain PENDING. 0x033E is the hidden controller (not a sprite Rastan fights).")
gal_scripted=gallery("Scripted / Special Actor Gallery", f"({len(scripted_actors)} scripted-encounter actors)",
                     scripted_actors)
boss_gallery_cards="".join(boss_card(bosses[r]) for r in range(1,7) if r in bosses)
gal_boss=(f'<section class="round"><h2>Bosses — Six Distinct Body Actors <span>(0x45330→0x4449E→0x444E0→0x45592)</span></h2>'
          f'<div class="statusbox ok">Real per-round boss <b>bodies</b> (bases 0x061D/0x0753/0x082C/0x07BF/0x0988/0x0B35). The old 0x033E "boss composite" model is deprecated and quarantined in the manifest. R1 &amp; R5 frames/palettes are MAME-verified; R2/R3/R4/R6 show the static ROM init-anim frame (line-inferred palette).</div>'
          f'<div class="grid">{boss_gallery_cards}</div></section>')

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
PP=M.get('phase_partition',{}).get('rounds',{})
BASENAME={a['base_graphics']:a['semantic_name'] for a in actors}
def phase_section(r):
    d=PP.get(str(r))
    if not d: return ''
    def lst(fs): return ", ".join(f'<span class="mono">{bs}</span> {BASENAME.get(bs,"")}'.strip() for bs in fs) or '<span class="muted">none</span>'
    # SUB-ROUND 2: static schedule-proven content (code, not MAME). family-2 = 0x033E spawner mechanism.
    sp=d.get('subround2_family2_spawners',[]); dh=d.get('subround2_direct_hostile_bases',[])
    s2win=d.get('subround2_13E_static', d.get('castle_13E','?'))
    sp_html=", ".join(f'<span class="mono">{x}</span>' for x in sp) or '<span class="muted">none</span>'
    dh_html=", ".join(f'<span class="mono">{x}</span>' for x in dh) or '<span class="muted">none</span>'
    conf=d.get('castle_confirmed_MAME')
    corro=('<div class="muted" style="margin-top:4px"><i>Corroboration (MAME, not authority):</i> '
           +", ".join(f'<span class="mono">{c}</span>' for c in conf)+'</div>') if conf else ''
    cas=(f'<span class="ok"><b>Schedule (0x4A104) content — STATIC:</b> family-2 spawners {sp_html}'
         f' &nbsp;<i>(base 0x033E route mechanism, anim 0x93)</i>; direct hostile bases {dh_html}.</span>'
         f'<div class="pend" style="margin-top:4px">Char-spawned identities (0x41180 <span class="mono">+0x03≠0</span>, target char <span class="mono">+0x0D</span> ∈ 0x45–0x7b) PENDING per-scene map-marker decode. SUB-ROUND-2 ROSTER PARTIAL.</div>{corro}')
    return (f'<div class="phaserow">'
            f'<div class="pbox"><b>SUB-ROUND 1 · 0x13E {d["outdoor_13E"]}</b><span class="ok">0x4A104 field schedule: {lst(d["phase1_field"])}</span></div>'
            f'<div class="pbox"><b>SUB-ROUND 2 · 0x13E {s2win}</b>{cas}</div>'
            f'</div>')
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
    _p2=M.get("scene_phase_state_machine",{}).get("phase2_starts_PROVEN_H11",{}).get(f"R{r}","(pending)")
    matnote=(f'<div class="statusbox part"><b>Phase-2 (castle) start — PROVEN (H11):</b> <span class="mono">{_p2}</span> '
             f'(section kind from 0x50EE0/0x50F6B). The marker-driven actors that appear in this castle section are not yet '
             f'individually round-pinned — see the <b>Materialized / Marker-Driven Actor Gallery</b> above for the {len(materialized)} '
             f'materialized bases (H5/H6). Per-scene marker→actor enumeration is the open H11 blocker (A5+0x10D000 collision-record populator).</div>')
    rounds_html+=f'''<section class="round"><div class="rhead"><h2>Round {r}</h2><span class="rmeta mono">A5+0x13E {per[str(r)]["r13E"]}</span></div>
      <h3 class="grp">Sub-Round 1 — Field roster <span>(0x4A104 schedule, PROVEN for round)</span></h3><div class="grid">{cards}</div>
      <h3 class="grp">Sub-Round 2 — Materialized &amp; Scripted <span>(boundary code-derived: round ends 0x502AC; R1 0x7E door 0x0F→0x10 proven)</span></h3>
      {matnote}
      {phase_section(r)}
      {bankrow(r)}
      <h4 class="grp">Scripted encounters <span>(scene-driven, A5+0x13E dispatch)</span></h4>{sctab}
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
    specs=[('0x061D',0x061D,0x00,1,15,'Round-1 boss record family','Record types 14/15. Static owner/update path 0x46BE0 and original-MAME Round-1 boss SAT capture. Round-1 boss BODY per table 0x444E0.'),
             ('0x0988',0x0988,0x82,5,15,'Round-5 boss record family','Record types 16/17. Type 16 creates five type-17 child records at 0x423B2; semantic boss name remains unassigned.')]
    for base,code,anim,rnd,nib,title,note in specs:
        pal,_=rom_field_palette(rnd,nib)
        img=render_vm(code,anim,pal,1)
        items.append(f'<article class="card"><div class="frame"><div class="provtag">legal arcade frame · compositor 1</div><img src="{img}"></div><div class="body"><div class="bar"><span class="b ok">SAT-MATCHED</span><span class="b ok">OWNER PATH PROVEN</span><span class="b pend">SEMANTIC NAME PENDING</span></div><h4>{title} <span class="mono">{base}</span></h4><p class="desc">{note}</p></div></article>')
    return ('<section class="round"><h2>Verified boss actor families — legal compositor frames</h2>'
            '<div class="statusbox ok"><b>Two bases earlier passes misclassified</b> (loaded via the <span class="mono">+0x06</span> record-type path through <span class="mono">0x4543e</span>/table <span class="mono">0x45592</span>). These frames use live original-arcade animation indices and compositor 1; piece order, tiles, flips, and relative coordinates match original SAT exactly.</div>'
            f'<div class="grid">{"".join(items)}</div></section>')

census_html=f"""<section class="round"><h2>Complete Actor Census — from ROM decompilation</h2>
<div class="statusbox ok"><b>{CEN.get('distinct_base_count','?')} distinct base-graphics actors</b> resolved statically from <span class="mono">maincpu.bin</span>. Field schedule <span class="mono">0x4A104</span> record byte1=<span class="mono">+0x3E</span> family, byte2 hi-nibble=<span class="mono">+0x752</span> variant → base via tables <span class="mono">0x45502</span> (var 0) / <span class="mono">0x45562</span> (var≠0) / boss <span class="mono">0x454ba</span>; plus every immediate write to <span class="mono">actor+0x1E</span> (code-spawned projectiles / sub-objects). <b>Semantic names are PROPOSED (lexicon) or PENDING — never invented.</b> Round columns show 0x13E position thirds (early/mid/<b>late≈phase 2/3</b>; exact door boundary still blocked).</div>
<div class="tblwrap"><table class="census"><tr><th>base</th><th>actor / name status</th><th>round · position (phase)</th><th>creation route (ROM)</th></tr>{census_rows()}</table></div></section>"""
dash_html="".join(f'<div class="dcell {c}"><span class="dk">{k}</span><span class="dv">{v}</span></div>' for k,v,c in M['dashboard'])
remain_html="".join(f'<li><span class="rs {("done" if s=="DONE" else "part" if s=="PARTIAL" else "ns")}">{s}</span> {t}</li>' for t,s in M['remaining'])

# ---- "What we now know" architecture summary (manifest-driven, synced through H9) ----
AS=M.get('architecture_status',{})
def _checklist(rows):
    mk={'done':'✓','part':'△','pend':'—'}
    return "".join(f'<li class="ck {c}"><span class="ckm">{mk.get(c,"—")}</span> {t}</li>' for t,c in rows)
arch_html=''
if AS:
    arch_html=(f'<section class="round"><h2>What we now know <span>(synced through {AS.get("_synced_through","H9")})</span></h2>'
      f'<div class="know"><div class="kcol"><h3 class="grp">Actor architecture</h3><ul class="checks">{_checklist(AS.get("actor_architecture",[]))}</ul></div>'
      f'<div class="kcol"><h3 class="grp">Visual reconstruction</h3><ul class="checks">{_checklist(AS.get("visual_reconstruction",[]))}</ul></div>'
      f'<div class="kcol"><h3 class="grp">Still open</h3><ul class="checks">'+"".join(f'<li class="ck pend"><span class="ckm">○</span> {t}</li>' for t in AS.get("still_open",[]))+'</ul></div></div></section>')

# ---- Items / power-ups / pickups (manifest-driven, H9-accurate) ----
IT=M.get('items_system',{})
def items_section():
    if not IT:
        return ''
    scls={'OPEN':'pend','0 STATICALLY PROVEN':'pend'}
    def cls(s): return 'pend' if ('OPEN' in s or s.startswith('0 ')) else ('ok' if 'PROVEN' in s and 'partial' not in s.lower() else 'part')
    cards="".join(
      f'<div class="itemcat {cls(c["status"])}"><div class="itk">{c["kind"]}</div>'
      f'<div class="its">{c["status"]}</div><p>{c["detail"]}</p></div>' for c in IT.get('categories',[]))
    return (f'<section class="round"><h2>Items / Power-ups / Pickups</h2>'
      f'<div class="statusbox part"><b>{IT.get("status","PARTIAL")}.</b> The item system is now partially decompiled: the enemy kill path is proven, but the enemy-death→item link is not. No item cards are shown because <b>no droppable item actor is statically proven</b> — this section makes the missing work visible rather than fabricating it.</div>'
      f'<div class="itemgrid">{cards}</div></section>')

def consistency_check():
    """Fail generation if the manifest/report would contradict itself (integrity guard)."""
    errs=[]
    if 'bosses' in M:
        errs.append("top-level 'bosses' (0x033E model) is still an active manifest key")
    for a in actors:
        b=a['base_graphics'].upper()
        if a['category']=='BOSS' and b in ('0X033E','033E'):
            errs.append(f"BOSS actor still uses 0x033E as body ({a.get('technical_id')})")
        if a['category']=='BOSS' and 'NOT reconstructed' in (a.get('unresolved_reason') or ''):
            errs.append(f"BOSS {a['base_graphics']} unresolved_reason still denies reconstruction")
    prm=M.get('per_round_boss_body_map',{}).get('rounds',{})
    for r,ba in bosses.items():
        mb=prm.get(str(r),{}).get('body_base')
        if mb and mb.upper()!=ba['base_graphics'].upper():
            errs.append(f"R{r} boss base disagreement: actors[]={ba['base_graphics']} vs map={mb}")
    for k,v,c in M['dashboard']:
        if 'NOT REIMPLEMENTED' in str(v).upper():
            errs.append(f"dashboard compositor row still says NOT REIMPLEMENTED ({k})")
    for a in materialized+controllers:
        if a['frame_status'] in ('COMPOSER_PROVEN','PROVEN'):
            errs.append(f"materialized/controller {a['base_graphics']} over-claims FRAME {a['frame_status']}")
    # name/identity: new badges separate OBJECT (proven) from NAME (status); ensure no field actor
    # claims a PROVEN human name while its own description flags it lexicon/PROPOSED.
    for a in field:
        if a['name_status']=='PROVEN' and ('PROPOSED' in a.get('description','') or 'lexicon' in a.get('description','').lower()):
            errs.append(f"field {a['base_graphics']} name_status=PROVEN but description says lexicon/PROPOSED")
    if errs:
        raise SystemExit("BESTIARY CONSISTENCY FAIL:\n  - "+"\n  - ".join(errs))
    print("consistency_check: PASS")
consistency_check()

def unresolved_gallery():
    cards="".join(card(a,None) for a in unresolved)
    return (f'<section class="round"><h2>Unresolved Actor Gallery <span>({len(unresolved)} visible objects lacking a confident identity)</span></h2>'
            f'<div class="statusbox pend"><b>Visible technical objects whose semantic role/identity is not yet proven.</b> RAW TILE thumbnails are labelled as such — never presented as a legal composited sprite. The full 45-row technical list is in the appendix census.</div>'
            f'<div class="grid">{cards}</div></section>')
def projectiles_section():
    return ('<section class="round"><h2>Projectiles / Effects</h2>'
      '<div class="statusbox part"><b>PARTIAL.</b> The genuine thrown/projectile actor is the marker <span class="mono">\'I\'</span> route → <b>record type 1</b>, graphics copied from the <span class="mono">A5+0x588</span> template (identity PENDING). Base <span class="mono">0x09EA</span> is <b>not</b> a single projectile — it is a shared marker-chain <b>transform</b> base (see the Materialized gallery). Impact/explosion is state <span class="mono">0x0F</span> via <span class="mono">0x447F0</span> (sfx 0x10). No standalone projectile sprite is legal-frame proven yet.</div></section>')

APPENDIX_HEADER='<section class="round"><h2>Technical / Decompilation Appendix</h2><p class="muted">Full technical census + phase-mechanism evidence. The visual game cast is above; this section is the raw decompilation reference.</p></section>'

STYLE=(ROOT/'tools/graphics_optimizer/bestiary_style.css').read_text()
doc=f'''<title>Rastan Bestiary</title>{STYLE}
<header class="hero"><div class="in"><div class="kicker">Rastan · Original Arcade · Living Decompilation Status</div>
<h1>Rastan Actor Bestiary &amp; Status</h1>
<p class="sub">A living view of the static arcade decompilation, generated <b>entirely from the authoritative manifest</b> (rastan_actor_graphics_manifest.json). Rounds &amp; field rosters are ROM-proven; palettes are decoded per-round from the arcade ROM. Every card shows independent IDENTITY / FRAME / PALETTE confidence. Provisional images (from the legacy lexicon/Composer captures) are labelled as such; nothing unproven is presented as authoritative.</p>
<h2 class="dash-h">Arcade Actor Decompilation Status</h2><div class="dash">{dash_html}</div></div></header>
<div class="wrap">{arch_html}
{gal_field}
{gal_mat}
{gal_scripted}
{gal_boss}
{rounds_html}
{projectiles_section()}
<section class="round"><h2>Hazards / Obstacles</h2><div class="statusbox part"><b>PARTIAL — map-marker routes not fully decoded.</b> From map collision markers (0x559B2 → 0x41180); only marker 0x48 (class 0x70) is graphics-proven. No hazard cards until static identity is proven (old JSON names are not authoritative).</div></section>
{items_section()}
{unresolved_gallery()}
{APPENDIX_HEADER}
{census_html}
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
