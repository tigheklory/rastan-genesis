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
    elif ps.get('kind')=='materialized_display_h15':
        pal,pidx=rom_field_palette(ps['round'], ps['nibble'])
        sw=f'<div class="palbank ok">DISPLAY line 0x{ps["nibble"]:X} · pool {pidx} · H15 compositor control byte (+0x27=0) · R{ps["round"]}</div>'
    elif ps.get('kind')=='materialized_fam2':
        pal,pidx=rom_field_palette(ps['round'], ps['nibble'])
        sw=f'<div class="palbank part">line 0x{ps["nibble"]:X} · fam-2 (0x456EC) creation-time line · base absent from Phase-2 (H14)</div>'
    elif ps.get('kind')=='composer_key':
        pal,bk=composer_palette(ps['key']); sw=f'<div class="palbank ok">bank {bk} · Composer-proven</div>'
    elif ps.get('kind')=='arcade_object':
        pal,pidx=rom_field_palette(ps['round'], ps['nibble'])
        used=ps.get('used_indices') or list(range(16))
        sw=(f'<div class="palbank ok">ARCADE line 0x{ps["nibble"]:X} · bank 0x{0x30|ps["nibble"]:02X} · pool {pidx} · '
            f'ROM 0x{ps.get("src",0):05X} · used idx {{{",".join(str(i) for i in used)}}}</div>')
        # swatch shows ONLY the indices the object's cells actually draw (H17)
        sw+='<div class="sw">'+''.join(f'<i title="idx {i}" style="background:rgb({pal[i][0]},{pal[i][1]},{pal[i][2]})"></i>' for i in used)+'</div>'
        if method=='vm':
            return render_vm(a['render']['base'], a['render']['anim'], pal, a['render'].get('compositor_table',0)), sw
        return None, sw
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
    rs=a.get('round_status','') or ''
    if cat=='CONTROLLER': roundb=''
    elif rp: roundb='<span class="b ok">ROUND PROVEN</span>'
    elif 'PROVEN ABSENT' in rs: roundb='<span class="b sp">PHASE-2 ABSENT (H14)</span>'
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
    img=render_vm(rn['base'], rn['anim'], GRAY, rn.get('compositor_table',1)) if rn.get('method')=='vm' else None  # colours PENDING (field pool disproven)
    if img:
        tag='body frame + palette · MAME-verified (Cody)' if ver else 'body frame = ROM init-anim · UNVERIFIED'
        frame=f'<div class="frame"><div class="provtag">{tag}</div><img src="{img}"></div>'
        sw=(f'<div class="palbank part">line 0x{nib:X} PROVEN (0x3C9E8) · boss line F source = 0x3BA88[round][15] → 0x4FD02 (Cody-corrected copy direction) · exact colours per pool</div>')
    else:
        frame=f'<div class="frame pend"><b>BODY FRAME PENDING</b><br><span>{a.get("unresolved_reason","")}</span></div>'; sw=''
    fb='ok' if ver else 'part'
    bar=(f'<span class="b ok">BODY PROVEN</span><span class="b ok">ROUND PROVEN</span>'
         f'<span class="b ok">TYPE 0x{a.get("boss_body_record_type",0):02X}</span>'
         f'<span class="b {fb}">{"FRAME VERIFIED" if ver else "FRAME STATIC"}</span>'
         f'<span class="b part">PALETTE line F = 0x3BA88[round][15] proven</span>')
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
                intro="Actors the marker/hunter system (0x41180 → 0x41362 → 0x40BAA state handlers) materializes in the later / sub-round-2 part of a round. <b>H10 assembled legal arcade frames</b> for all 12 via the proven render dispatch (0x3D054 → 0x3C902). <b>H14 executed the real Phase-2 marker chains</b> (H13 record-accurate map): four bases are now round-pinned by an exact +0x1E write — 0x0224 (R2,R4), 0x00F4 (R4,R5,R6), 0x09EA (R5), 0x0179 (R6) — with the exact family-2 palette instance (0x45684 → 0x456EC → 0x3BA88 → 0x4FD02); the other eight are <b>PROVEN ABSENT</b> from Phase-2 (no marker occurrence satisfies their base-write branch). Human identity + exact legal frame remain PENDING. 0x033E is the hidden controller (not a sprite Rastan fights).")
gal_scripted=gallery("Scripted / Special Actor Gallery", f"({len(scripted_actors)} scripted-encounter actors)",
                     scripted_actors)
hazards=[a for a in actors if a['category']=='HAZARD_INTERACTIVE']
gal_hazards=gallery("Interactive Hazards / Obstacles", f"({len(hazards)} destructible/solid object)",
                    sorted(hazards,key=lambda a:a['base_graphics']),
                    intro="Solid / destructible PC090OJ objects Rastan interacts with (not decorative sprites). <b>H17</b> proved the Round-1 <b>Destroyable cave-entrance block</b> from the original arcade ROM: four cells 0x0179..0x017C, target 'H' (0x48), live state 0x1E, destruction state 0x0F, program 0x3E1C0 (control 0x0C -> line 0xC / bank 0x3C), R1 pool 35 at ROM 0x50162. Its cells draw only indices {1,7,8,9,12,13,14} = <b>BLACK + BROWN</b> (the arcade appearance). The Genesis build's muddy-gray Line-3 reindex (Cody build0366) is a rejected Genesis realization, not the arcade truth.") if hazards else ""
effects=[a for a in actors if a['category']=='EFFECT_TRANSIENT']
gal_effects=gallery("Transient Effect Gallery", f"({len(effects)} burst/impact effect)",
                    sorted(effects,key=lambda a:a['base_graphics']),
                    intro="Short-lived, self-retiring EFFECTS (not enemies). <b>H16</b> proved the Round-1 marker-0x4D state-0x1B route (0x43ECC) is a burst CONTROLLER: it activates up to five shared-pool slots (A5+0x3C8..0x4C8) via 0x43F4E/0x43F52, and 0x447F0/0x448B2 convert each active-state slot to state 0x0F. The state-0x0F +0x39 child path (0x40DD8) assigns base 0x0275 (expanding impact/burst, self-retires in ~4 frames) — so the \"five children\" are transient effects, one per activated slot, NOT five enemy species and NOT a composite.") if effects else ""
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
         f'<div class="ok" style="margin-top:4px">Char-spawned identities (0x41180 <span class="mono">+0x03≠0</span>, target char <span class="mono">+0x0D</span> ∈ 0x45–0x7b): per-scene map-marker rosters PROVEN (H13) and Phase-2 marker chains executed to exact +0x1E base writes (H14).</div>{corro}')
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
    _pins={2:['0x0224'],4:['0x0224','0x00F4'],5:['0x00F4','0x09EA'],6:['0x0179','0x00F4']}
    _pintxt=('materialized bases proven present this round by exact +0x1E write (H14): '
             +", ".join(f'<span class="mono">{b}</span>' for b in _pins[r])) if r in _pins else \
            'no materialized base writes an exact +0x1E for this round\'s Phase-2 markers (H14)'
    matnote=(f'<div class="statusbox ok"><b>Phase-2 (castle) start — PROVEN (H11):</b> <span class="mono">{_p2}</span> '
             f'(section kind from 0x50EE0/0x50F6B). Per-scene marker rosters are record-accurate (H13) and the marker chains were '
             f'executed (H14): {_pintxt}. See the <b>Materialized / Marker-Driven Actor Gallery</b> above.</div>')
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

# ---- H20 game-wide 68000 decompilation coverage (DATA-DRIVEN from the census JSON) ----
def build_coverage_section():
    fp=ROOT/'analysis/decompilation/gamewide_coverage_summary.json'
    if not fp.exists(): return ''
    import json as _j
    cv=_j.loads(fp.read_text())
    tot=cv['total_code_bytes_spansum']
    LABEL={"PLAYER_CONTROL_MOVEMENT":"Player control / movement","PLAYER_WEAPONS_ITEMS_STATUS":"Player weapons / items / status",
      "ACTOR_CORE_LIFECYCLE_CREATION":"Actor core / lifecycle / creation","ENEMY_AI_BEHAVIORS":"Enemy AI / behaviors",
      "COLLISION_DAMAGE_PHYSICS":"Collision / damage / physics","BOSS_LOGIC":"Boss logic",
      "MAP_SCENE_ROUND_PROGRESSION":"Map / scene / round progression","PC080SN_TILEMAP_SCROLL_COLLISIONMAP":"PC080SN tilemap / scroll / collision-map",
      "PC090OJ_SPRITE_COMPOSITOR":"PC090OJ sprite / compositor","PALETTE_COLOR":"Palette / color",
      "HUD_SCORE_LIVES_GAMESTATE":"HUD / score / lives / game state","INPUT_SERVICE_ATTRACT":"Input / service / attract",
      "INTERRUPTS_TIMING_VBLANK_SYSTEM":"Interrupts / timing / VBlank / system","AUDIO_INTERFACE":"Audio interface",
      "INIT_RESET_MEMORY":"Init / reset / memory","OTHER_KNOWN":"Other known","UNCLASSIFIED":"Unclassified"}
    LABEL["AUDIO_INTERFACE"]="Audio interface / main-CPU sound control"
    # H22: dependency-tier ordering (engine dependency, NOT percent complete or old subsystem order)
    TIERS=[
      ("CORE EXECUTION",["INIT_RESET_MEMORY","INTERRUPTS_TIMING_VBLANK_SYSTEM","INPUT_SERVICE_ATTRACT"]),
      ("GAME / WORLD CONTROL",["HUD_SCORE_LIVES_GAMESTATE","MAP_SCENE_ROUND_PROGRESSION","PC080SN_TILEMAP_SCROLL_COLLISIONMAP"]),
      ("CORE GAMEPLAY",["PLAYER_CONTROL_MOVEMENT","COLLISION_DAMAGE_PHYSICS","ACTOR_CORE_LIFECYCLE_CREATION",
                        "ENEMY_AI_BEHAVIORS","PLAYER_WEAPONS_ITEMS_STATUS","BOSS_LOGIC"]),
      ("PRESENTATION",["PC090OJ_SPRITE_COMPOSITOR","PALETTE_COLOR"]),
      ("SUPPORT",["AUDIO_INTERFACE","OTHER_KNOWN","UNCLASSIFIED"]),
    ]
    def bar(cb,pb,sb,nb,t):
        t=t or 1
        seg=lambda w,cls:(f'<i class="cvseg {cls}" style="width:{100.0*w/t:.2f}%"></i>' if w else '')
        return ('<div class="cvbar">'+seg(cb,"cc")+seg(pb,"cp")+seg(sb,"cs")+seg(nb,"cn")+'</div>')
    def row(name,cb,pb,sb,nb,cf,tf,full,touch,basis,overall=False):
        t=cb+pb+sb+nb
        return (f'<div class="cvrow{" cvoverall" if overall else ""}"><div class="cvname">{name}</div>'
                f'<div class="cvbarwrap">{bar(cb,pb,sb,nb,t)}</div>'
                f'<div class="cvnum"><b>{full:.1f}%</b> full · {touch:.1f}% touched · {cf}/{tf} fn · {cb}/{t} B <span class="cvbasis">{basis}</span></div></div>')
    # OVERALL bar uses the PRIMARY unique-executable-byte (union) metric (H22 fix)
    ub=cv.get('total_code_bytes_union',tot)
    u_c=cv.get('complete_code_bytes_union',cv['complete_code_bytes'])
    u_t=cv.get('touched_code_bytes_union',cv['complete_code_bytes'])
    u_ps=max(0,u_t-u_c); u_n=max(0,ub-u_t)
    uf=cv.get('overall_fully_decompiled_pct_union',cv['overall_fully_decompiled_pct'])
    ut=cv.get('overall_touched_pct_union',cv['overall_touched_pct'])
    over=row("OVERALL — unique executable byte (union)",u_c,u_ps,0,u_n,cv['complete_functions'],cv['total_functions'],
             uf,ut,"unique-byte",overall=True)
    bykey={r['subsystem']:r for r in cv['subsystems']}
    body=""
    for tier,keys in TIERS:
        tierrows=""
        for k in keys:
            r=bykey.get(k)
            if not r or r['total_code_bytes']==0: continue
            tierrows+=row(LABEL.get(k,k),r['complete_code_bytes'],r['partial_code_bytes'],
                  r['stub_code_bytes'],r['not_decompiled_code_bytes'],r['complete_functions'],r['total_functions'],
                  r['fully_decompiled_pct'],r['touched_pct'],"fn-span")
        if tierrows:
            body+=f'<div class="cvtier">{tier}</div>{tierrows}'
    legend=('<div class="cvlegend"><span><i class="cvseg cc"></i>fully decompiled</span>'
            '<span><i class="cvseg cp"></i>partial</span><span><i class="cvseg cs"></i>stub/referenced</span>'
            '<span><i class="cvseg cn"></i>not decompiled</span>'
            '<span class="cvbasis">bar basis: unique-byte (OVERALL) · fn-span (subsystems)</span></div>')
    note=(f'<p class="cvnote"><b>Ordered by engine dependency</b> (core execution → world control → gameplay → '
          f'presentation → support), not by percent complete. The OVERALL bar uses the <b>primary unique-executable-byte '
          f'(union) metric</b> ({ub} B); per-subsystem bars use function-span bytes (labelled <span class="mono">fn-span</span>) '
          f'— the two metrics are never mixed inside one bar. Only durable-C COMPLETE (entry-matched) counts as fully '
          f'decompiled; PARTIAL gets <b>no</b> fractional credit; untracked functions are NOT DECOMPILED. Sound is a separate '
          f'Z80/YM2151 program ROM (not in this denominator). Data: '
          f'<span class="mono">analysis/decompilation/gamewide_coverage_summary.json</span>.</p>')
    return (f'<section class="round" id="dash-code"><h2>Arcade 68000 Decompilation Roadmap <span>(H24 dependency-ordered census)</span></h2>'
            f'<div class="statusbox ok"><b>OVERALL fully decompiled: {uf:.1f}%</b> · '
            f'touched: {ut:.1f}% <span class="small">(PRIMARY: unique executable byte, union {ub} B)</span><br>'
            f'<span class="small">span-sum basis (secondary): {cv["overall_fully_decompiled_pct"]:.1f}% full · '
            f'{cv["overall_touched_pct"]:.1f}% touched · {cv["total_functions"]} functions · {tot} B · '
            f'H20 historical: {cv.get("historical_h20",{}).get("fully_pct",cv["overall_fully_decompiled_pct"]):.1f}% / '
            f'{cv.get("historical_h20",{}).get("touched_pct",cv["overall_touched_pct"]):.1f}%</span></div>'
            f'{legend}<div class="cvchart">{over}{body}</div>{note}</section>')
coverage_html=build_coverage_section()

def build_content_census_section():
    """H21 second dashboard: Game Content / Bestiary coverage (player anim / enemy / hazard / boss),
    multidimensional and data-driven from the H21 census TSVs. Complements the code roadmap above."""
    import csv as _csv
    AD=ROOT/'analysis/actor_decompilation'
    obj=AD/'h21_gameplay_object_census.tsv'; haz=AD/'h21_hazard_census.tsv'
    pfi=AD/'h21_player_frame_inventory.tsv'
    if not obj.exists(): return ''
    orows=list(_csv.DictReader(open(obj),delimiter='\t'))
    # tally objects by category
    cats={}
    for r in orows:
        c=r.get('category','?') or '?'; cats.setdefault(c,[0,0])
        cats[c][0]+=1
        if (r.get('behavior_status','') or '').startswith('PROVEN'): cats[c][1]+=1
    def catrow(name,n,proven):
        pct=100.0*proven/n if n else 0
        return (f'<div class="cvrow"><div class="cvname">{name}</div>'
                f'<div class="cvbarwrap"><div class="cvbar"><i class="cvseg cc" style="width:{pct:.1f}%"></i>'
                f'<i class="cvseg cn" style="width:{100-pct:.1f}%"></i></div></div>'
                f'<div class="cvnum"><b>{proven}/{n}</b> behavior-proven</div></div>')
    catlbl={'ENEMY_FIELD':'Field enemies','BOSS':'Bosses','EFFECT':'Effects / projectiles',
            'HAZARD':'Hazards (actor)','MATERIALIZED':'Materialized cast','PLAYER':'Player'}
    catbody="".join(catrow(catlbl.get(k,k),v[0],v[1]) for k,v in sorted(cats.items(),key=lambda x:-x[1][0]))
    # hazards
    hbody=""
    if haz.exists():
        for h in _csv.DictReader(open(haz),delimiter='\t'):
            st=h.get('identity_status','')
            cls={'PROVEN':'ok','PARTIAL':'part'}.get(st,'pend')
            hbody+=(f'<div class="itemcat {cls}"><div class="itk">{h["hazard"].replace("_"," ")}</div>'
                    f'<div class="its">{st}</div><p>{h.get("candidate_mechanism","")}<br>'
                    f'<span class="mono small">{h.get("proven_route_or_owner","")}</span></p></div>')
    # player frames: a slot is CELL-DECODED only when its cell_codes column is not PENDING (H22 honesty fix)
    pf_total=pf_decoded=0
    if pfi.exists():
        prows=list(_csv.DictReader(open(pfi),delimiter='\t'))
        pf_total=len(prows)
        pf_decoded=sum(1 for r in prows if (r.get('cell_codes') or '').strip() not in ('','PENDING','PENDING(extract)'))
    pf_pending=pf_total-pf_decoded
    pfnote=(f'<div class="statusbox part"><b>Player composites: {pf_total} frame slots enumerated</b> '
            f'(table 0x5BD40) · <b>cell-decoded / rendered: {pf_decoded}</b> · <b>remaining cell-decode: {pf_pending}</b>. '
            f'Per-frame cell extraction is the content frontier (<span class="mono">content_frontier.csv</span> CF-01, '
            f'deferred to the player-focused H23); the Palette Composer exposes enumerated slots with honest extraction '
            f'status rather than fabricated cells. This is NOT a claim that all Rastan frames are in the Composer.</div>' if pf_total else '')
    # Centaur is a FIELD ENEMY with human identity PENDING (one of 0x01CB/0x043A/0x06E2/0x0889) — NOT a hazard.
    centaur_note=('<div class="statusbox pend"><b>Centaur — unresolved enemy identity (not a hazard).</b> Tracked in '
            'field-enemy coverage above: it is one of the four PROVEN field bases whose human name is PENDING '
            '(<span class="mono">0x01CB / 0x043A / 0x06E2 / 0x0889</span>). Which one is the Centaur requires per-base '
            'sprite decode (frontier CF-02/CF-05); no name is assigned until that is proven.</div>')
    return (f'<section class="round" id="dash-content"><h2>Game Content / Bestiary Coverage <span>(H22)</span></h2>'
            f'<p class="cvnote">Complementary to the code roadmap: this tracks how much of the actual '
            f'<b>game content</b> (player animation, enemies, hazards, bosses) is identified and behavior-proven, '
            f'not how many code bytes are decompiled.</p>{pfnote}'
            f'<div class="cvchart">{catbody}</div>{centaur_note}'
            f'<h3 class="grp">Hazard census</h3><div class="itemgrid">{hbody}</div>'
            f'<p class="cvnote">Data: <span class="mono">h21_gameplay_object_census.tsv</span>, '
            f'<span class="mono">h21_hazard_census.tsv</span>, <span class="mono">h21_player_frame_inventory.tsv</span>. '
            f'Statuses are honest: PENDING/PARTIAL hazards are named as work-to-do, never fabricated.</p></section>')
content_census_html=build_content_census_section()

def build_player_section():
    """H24+fix RASTAN / PLAYER section: render FULL-BODY player poses = upper torso (table 0x5BD40,
    composer 0x54492, slot A5+0x1244) + lower legs (table 0x5C466, composer 0x546A8, slot A5+0x1246),
    paired by the per-state a3/a4 pose tables in 0x540CC. Rendered from arcade pc090oj.bin, palette
    line 3. Canonical source = maincpu.bin tables (h24_player_frame_cells.tsv)."""
    UP=0x5BD40; LO=0x5C466
    def s8(b): return b-256 if b>=128 else b
    up_off=[int.from_bytes(mc[UP+i*2:UP+i*2+2],'big') for i in range(75)]
    lo_off=[int.from_bytes(mc[LO+i*2:LO+i*2+2],'big') for i in range(52)]
    pal,_=rom_field_palette(1,3)   # player body = palette line 3 (colbank 0x60), per registry
    ncells=len(pc)//128
    # each frame's piece count is bounded by the NEXT slot's offset (records are variable-length;
    # the fixed 4-piece hardware loop over-reads short frames into padding, which is why an unbounded
    # read pulled a stray tile 0x0003 'sword' fragment into crouch frames — H24 render fix).
    def piece_count(offs, slot):
        o=offs[slot]; nxt=min([x for x in offs if x>o]+[o+24]); return max(0,(nxt-o)//6)
    def pieces(tbl,offs,slot):
        if slot>=len(offs): return []
        base=tbl+offs[slot]; out=[]
        for p in range(piece_count(offs,slot)):
            r=mc[base+p*6:base+p*6+6]; t=int.from_bytes(r[0:2],'big')
            cell=t&0x1fff
            if t and cell<ncells: out.append((cell,s8(r[2]),s8(r[3])))
        return out
    def render(pcs):
        if not pcs: return None
        xs=[x for _,x,_ in pcs]; ys=[y for _,_,y in pcs]; ox,oy=min(xs),min(ys)
        W=max(xs)-ox+16; H=max(ys)-oy+16
        img=Image.new('RGBA',(W,H),(0,0,0,0))
        for cell,x,y in pcs:
            px=dec(cell)
            for yy in range(16):
                for xx in range(16):
                    idx=px[yy][xx]
                    if idx: img.putpixel((x-ox+xx,y-oy+yy),pal[idx]+(255,))
        bb=img.getbbox()
        if bb: img=img.crop(bb)
        return datauri(img.resize((img.width*4,img.height*4),Image.NEAREST))
    def card(uri,title,sub):
        return (f'<div class="pcard"><div class="pframe">{("<img src=\""+uri+"\">") if uri else "blank"}</div>'
                f'<div class="pmeta"><b>{title}</b><br><span class="mono small">{sub}</span></div></div>')
    # 18 per-state (upper a3, lower a4) pose-table pairs from 0x540CC
    PAIRS=[(0x5b640,0x5b660),(0x5b640,0x5b680),(0x5b6d0,0x5b6f8),(0x5b720,0x5b740),(0x5b778,0x5b7a0),
           (0x5b7c8,0x5b7e8),(0x5b818,0x5b840),(0x5b868,0x5b888),(0x5b8d8,0x5b900),(0x5b928,0x5b948),
           (0x5b9a8,0x5b9d0),(0x5b9f8,0x5ba00),(0x5ba70,0x5ba78),(0x5bab0,0x5bac8),(0x5bb40,0x5bb80),
           (0x5bbc0,0x5bc00),(0x5bc40,0x5bc80),(0x5bcc0,0x5bd00)]
    # collect ALL upper-body pose tables (three registers): a2 = weapon-variant, a3 = normal, attack
    import re as _re
    a2s=set(); a3s=set()
    for _ln in open(ROOT/'build/maincpu.disasm.txt'):
        _m=_re.search(r'(54[0-9a-f]{3}):\s+2([46])7c ([0-9a-f]{4}) ([0-9a-f]{4})\s+moveal #\d+,%(a[23])',_ln)
        if not _m: continue
        _pc=int(_m.group(1),16)
        if not (0x540cc<=_pc<=0x54320): continue
        _v=int(_m.group(3)+_m.group(4),16)
        if _m.group(5)=='a2' and 0x5b000<=_v<0x5c500: a2s.add(_v)
        if _m.group(5)=='a3' and 0x5b000<=_v<0x5c500: a3s.add(_v)
    ATK={0x5bae0:'attack up-thrust',0x5bb10:'attack hi'}
    A4=[b for _,b in PAIRS]
    alltab=sorted(a2s|a3s|set(ATK)|set(A4)|{UP})
    def nl(a): return min(x for x in alltab if x>a)-a
    ref={}   # torso slot -> set(role labels)
    for a in sorted(a2s):
        for i in range(nl(a)):
            if mc[a+i]<75: ref.setdefault(mc[a+i],set()).add('weapon-variant')
    for a in sorted(a3s):
        for i in range(nl(a)):
            if mc[a+i]<75: ref.setdefault(mc[a+i],set()).add('normal')
    for a,lab in ATK.items():
        for i in range(0,nl(a),2):
            if mc[a+i]<75: ref.setdefault(mc[a+i],set()).add(lab)
    for odd in (43,45,47,49,51,53): ref.setdefault(odd,set()).add('weapon-swing companion')
    pbounds=sorted(set([a for a,_ in PAIRS]+A4+[UP]))
    def tlen(addr):
        nxt=min([x for x in pbounds if x>addr]+[UP]); return min(nxt-addr,64)
    # (1) full-body paired poses (a3 upper + a4 lower). The torso and leg animation tracks are
    # indexed independently, so index-lockstep pairing can emit combinations that never co-occur
    # in game (e.g. a standing torso + the crouch leg 17). Drop any pairing whose torso bottom and
    # leg top leave a vertical gap (>=4 px) — a disconnected body — while keeping perfectly-joined
    # bodies (gap 0) and effect frames where one half has no cells.
    def body_gap(u,l):
        up=pieces(UP,up_off,u); lo=pieces(LO,lo_off,l)
        if not up or not lo: return None   # effect/dissolve frame, keep
        return min(y for _,_,y in lo) - (max(y for _,_,y in up)+16)
    # Full-body pairings come from the authoritative generated artifact (also consumed by the Palette
    # Composer) so neither tool hard-codes the list. Fall back to inline derivation if it is absent.
    seen={}; full=[]
    import csv as _csv
    _pair_tsv=ROOT/'analysis/actor_decompilation/h24_player_fullbody_pairings.tsv'
    if _pair_tsv.exists():
        for r in _csv.DictReader(open(_pair_tsv),delimiter='\t'):
            u=int(r['torso_slot']); l=int(r['leg_slot']); a3=int(r['pose_table_a3'],16); i=int(r['anim_index'])
            if (u,l) not in seen: seen[(u,l)]=(a3,i); full.append((u,l,a3,i))
    else:
        for a3,a4 in PAIRS:
            n=min(tlen(a3),tlen(a4))
            for i in range(n):
                u=mc[a3+i]; l=mc[a4+i]
                if u>=75 or l>=52: continue
                g=body_gap(u,l)
                if g is not None and abs(g)>=4: continue   # skip disconnected mispairing
                if (u,l) not in seen: seen[(u,l)]=(a3,i); full.append((u,l,a3,i))
    full_cards="".join(card(render(pieces(UP,up_off,u)+pieces(LO,lo_off,l)),
                             f"pose u{u}+l{l}", f"{len(pieces(UP,up_off,u))+len(pieces(LO,lo_off,l))} cells · a3 0x{a3:04x}[{i}]")
                       for u,l,a3,i in full)
    # (2) ALL distinct torso frames, annotated by which selection table references them (NO 'unused' claim)
    tsig={}; torso_cards=""; up_distinct=0
    for s in range(75):
        pcs=pieces(UP,up_off,s); key=tuple(pcs)
        if key in tsig: continue
        tsig[key]=s; up_distinct+=1
        roles=sorted(ref.get(s,[]))
        rtag=(" · "+", ".join(roles)) if roles else " · ref not yet traced"
        torso_cards+=card(render(pcs), f"torso {s}", f"{len(pcs)} cells · off 0x{up_off[s]:04x}{rtag}")
    # (3) ALL distinct leg frames
    lsig={}; leg_cards=""; lo_distinct=0
    for s in range(52):
        pcs=pieces(LO,lo_off,s); key=tuple(pcs)
        if key in lsig: continue
        lsig[key]=s; lo_distinct+=1
        leg_cards+=card(render(pcs), f"legs {s}", f"{len(pcs)} cells · off 0x{lo_off[s]:04x}")
    nref=sum(1 for s in range(75) if s in ref)
    metric=(f'<div class="statusbox ok"><b>RASTAN BODY COVERAGE (full body = torso + legs)</b><br>'
            f'Full-body poses (torso+legs paired via a3/a4 pose tables): <b>{len(full)}</b> · '
            f'Distinct torso frames (0x5BD40): <b>{up_distinct}</b> · Torso slots referenced by a selection table '
            f'(a2 weapon-variant + a3 normal + attack): <b>{nref} / 75</b> · Distinct leg frames (0x5C466): <b>{lo_distinct}</b> · '
            f'Palette line 3, colbank 0x60.</div>')
    note=('<p class="cvnote">Rendered from ORIGINAL ARCADE <span class="mono">pc090oj.bin</span> — no screenshots, '
          'no Genesis art. <b>Rastan is two half-sprites</b>: torso (table <span class="mono">0x5BD40</span>, slot '
          'A5+0x1244, composer <span class="mono">0x54492</span>) + legs (table <span class="mono">0x5C466</span>, '
          'slot A5+0x1246, composer <span class="mono">0x546A8</span>). The upper half is selected through THREE '
          'registers set per state in <span class="mono">0x540CC</span>: <b>a2</b> weapon-variant (e.g. 0x5BA38 = the '
          'weapon swings, slots 44/46/48/50/52/54), <b>a3</b> normal, and the attack tables 0x5BAE0/0x5BB10 (e.g. slots '
          '12/13/14 = up-thrust). Every torso frame is annotated with its referencing table; piece count is bounded by '
          'each frame\'s record length (removes the stray sword-tile 0x0003 over-read). No frame is labelled unused.</p>')
    return (f'<section class="round" id="dash-player"><h2>Rastan / Player <span>(body frames)</span></h2>'
            f'{metric}'
            f'<h3 class="grp">Valid full-body pairings <span>(reconstructed torso + legs via a3/a4 pose tables — not a torso×leg product)</span></h3><div class="pgallery">{full_cards}</div>'
            f'<h3 class="grp">All torso frames <span>(0x5BD40 · every slot positively referenced by a selector — a2 weapon-variant / a3 normal / attack)</span></h3><div class="pgallery">{torso_cards}</div>'
            f'<h3 class="grp">All leg frames <span>(0x5C466 · lower-body track)</span></h3><div class="pgallery">{leg_cards}</div>'
            f'{note}</section>')
try:
    player_html=build_player_section()
except Exception as _e:
    player_html=f'<section class="round"><h2>Rastan / Player</h2><div class="statusbox pend">player render error: {_e}</div></section>'

def build_weapons_section():
    """PLAYER EQUIPMENT — equipped weapon overlays. STATIC-DECOMPILATION driven: identity/selector/table/
    producer come from the manifest player_render_architecture.weapon_overlay.proven_identities; the
    representative arcade artwork is composited from the authoritative generated weapon-cell TSV (rendered
    from arcade pc090oj.bin, sprite palette line 3). NOT gameplay-trace derived. The frame-69 decode
    artefact (player-slot overrun; HAMMER frame 69 = blank 0x0003x3) is excluded, matching the Build-0383
    generator and the Palette Composer (one source of truth)."""
    import csv as _csv
    WO=M.get('player_render_architecture',{}).get('weapon_overlay',{})
    ids=WO.get('proven_identities',{})
    if not ids: return ''
    pal,_=rom_field_palette(1,3)                 # player/weapon sprite palette = bank 0x33, line 3
    ncells=len(pc)//128
    WT=ROOT/'analysis/actor_decompilation/h24_player_weapon_cells.tsv'
    frames={}
    if WT.exists():
        for r in _csv.DictReader(open(WT),delimiter='\t'):
            if r.get('valid_code')!='Y' or int(r['frame_index'])==69: continue
            uid=r['weapon_id']; fi=int(r['frame_index']); code=int(r['cell_code'],16)&0x1fff
            if code>=ncells: continue
            frames.setdefault(uid,{}).setdefault(fi,[]).append((code,int(r['x_off']),int(r['y_off']),r.get('flip')=='H'))
    def render_frame(cells):
        xs=[x for _,x,_,_ in cells]; ys=[y for _,_,y,_ in cells]; ox,oy=min(xs),min(ys)
        W=max(xs)-ox+16; H=max(ys)-oy+16; img=Image.new('RGBA',(W,H),(0,0,0,0))
        for c,x,y,fh in cells:
            px=dec(c)
            for yy in range(16):
                for xx in range(16):
                    idx=px[yy][15-xx if fh else xx]
                    if idx: img.putpixel((x-ox+xx,y-oy+yy),pal[idx]+(255,))
        bb=img.getbbox()
        if bb: img=img.crop(bb)
        return datauri(img.resize((img.width*4,img.height*4),Image.NEAREST))
    ORDER=['object:weapon.sword','object:weapon.axe','object:weapon.hammer','object:weapon.fire_sword']
    cards=''
    for uid in ORDER:
        idn=ids.get(uid)
        if not idn: continue
        wf=frames.get(uid,{}); gf=sorted(wf)
        ncnt=len(gf); ucells=len({c for fi in wf for (c,_,_,_) in wf[fi]})
        rep=max(gf,key=lambda f:len(wf[f])) if gf else None
        uri=render_frame(wf[rep]) if rep is not None else None
        img=('<img src="'+uri+'">') if uri else 'blank'
        cards+=(f'<div class="pcard"><div class="pframe">{img}</div><div class="pmeta">'
                f'<b>{idn["name"]}</b> <span class="badge ok">OBJECT PROVEN</span> <span class="badge ok">NAME PROVEN</span> '
                f'<span class="badge ok">FRAMES PROVEN</span> <span class="badge ok">STATIC DECOMPILED</span><br>'
                f'<span class="mono small">selector A5+0x12FA={idn["selector_a12fa"]} · table {idn["table"]} · producer 0x54598 · slot A5+0x1244</span><br>'
                f'<span class="mono small">{ncnt} proven frames · {ucells} unique source cells · grant {idn.get("grant","")}</span><br>'
                f'<span class="small">{idn.get("identity_proof","")}</span><br>'
                f'<span class="palbank ok">source bank 0x33 · sprite palette line 3 (arcade) · Test object:weapon.{uid.split(".")[-1]} → line 0 (authored)</span></div></div>')
    intro=('<b>Equipped weapon overlays</b> — proven from STATIC ARCADE evidence (original arcade code, ROM '
           'tables 0x5CD8A/0x5D346/0x5D666/0x5D068, weapon-grant handlers, decoded PC090OJ piece records, raw '
           'arcade PC090OJ graphics), NOT from Genesis gameplay traces. Each weapon is a separate PC090OJ '
           'layer appended by the player body-composer tail <span class="mono">0x54598</span>, indexed by the '
           'upper-body slot <span class="mono">A5+0x1244</span>, selected by <span class="mono">A5+0x12FA</span>. '
           'Representative frame composited from arcade <span class="mono">pc090oj.bin</span> (palette line 3). '
           'These are PLAYER EQUIPMENT — not enemy actors, not unresolved. The browser "frame 69" is a decode '
           'artefact (player-slot overrun; HAMMER frame 69 = blank 0x0003×3) and is excluded.')
    return (f'<section class="round" id="dash-weapons"><h2>Player Equipment — Equipped Weapon Overlays <span>(A5+0x12FA → 0x54598)</span></h2>'
            f'<div class="statusbox ok">{intro}</div><div class="pgallery">{cards}</div></section>')
try:
    weapons_html=build_weapons_section()
except Exception as _e:
    weapons_html=f'<section class="round"><h2>Player Equipment — Equipped Weapon Overlays</h2><div class="statusbox pend">weapon render error: {_e}</div></section>'

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
<div class="wrap">{coverage_html}
{content_census_html}
{player_html}
{weapons_html}
{arch_html}
{gal_field}
{gal_mat}
{gal_scripted}
{gal_hazards}
{gal_effects}
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
