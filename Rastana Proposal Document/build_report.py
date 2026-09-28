#!/usr/bin/env python3
"""Build the Rastana Proposal research report (self-contained HTML, images embedded as data URIs).
Isolated capability test — reads the arcade ROM only to match Rastan's palette/format; writes nothing
back into the project."""
import os,io,base64,json
from PIL import Image
ROOT=os.path.dirname(os.path.abspath(__file__))
AS=os.path.join(ROOT,"assets")
MC=open(os.path.join(ROOT,"..","build","regions","maincpu.bin"),"rb").read()
PC=open(os.path.join(ROOT,"..","build","regions","pc090oj.bin"),"rb").read()

def p5(n): v=n*2; return (v<<3)|(v>>2)
def pal_line3():
    pidx=MC[0x3BA88+3]; b=0x4FD02+pidx*32
    return [(p5((int.from_bytes(MC[b+i*2:b+i*2+2],'big')>>8)&0xF),
             p5((int.from_bytes(MC[b+i*2:b+i*2+2],'big')>>4)&0xF),
             p5(int.from_bytes(MC[b+i*2:b+i*2+2],'big')&0xF)) for i in range(16)]
PAL=pal_line3()
# user's 16-colour master palette (for the swatch): most-common colour is the white background
import collections as _c
_mim=Image.open(os.path.join(ROOT,"ref","rastana_master16.png")).convert("RGBA")
_cc=_c.Counter(_mim.getpixel((x,y))[:3] for y in range(_mim.size[1]) for x in range(_mim.size[0]) if _mim.getpixel((x,y))[3]>0)
_order=[c for c,_ in _cc.most_common()]; MPAL=[c for c in _order if c!=_order[0]]
def uri(im):
    b=io.BytesIO(); im.save(b,"PNG"); return "data:image/png;base64,"+base64.b64encode(b.getvalue()).decode()

# ---- render a real Rastan full-body frame (torso slot + leg slot) from the ROM ----
def s8(b): return b-256 if b>=128 else b
def dec(code):
    px=[[0]*16 for _ in range(16)]; base=code*128
    for r in range(16):
        for c in range(8):
            by=PC[base+r*8+c]; px[r][c*2]=by>>4; px[r][c*2+1]=by&0xF
    return px
UP=0x5BD40; LO=0x5C466
up_off=[int.from_bytes(MC[UP+i*2:UP+i*2+2],'big') for i in range(75)]
lo_off=[int.from_bytes(MC[LO+i*2:LO+i*2+2],'big') for i in range(52)]
def pieces(tbl,offs,slot):
    o=offs[slot]; srt=sorted(offs); nx=min([x for x in srt if x>o]+[o+24]); n=(nx-o)//6
    base=tbl+o; out=[]
    for p in range(n):
        r=MC[base+p*6:base+p*6+6]; t=int.from_bytes(r[0:2],'big')
        if t&0x1fff: out.append((t&0x1fff,s8(r[2]),s8(r[3])))
    return out
def rastan(u,l,scale=6):
    pcs=pieces(UP,up_off,u)+pieces(LO,lo_off,l)
    xs=[x for _,x,_ in pcs]; ys=[y for _,_,y in pcs]; ox,oy=min(xs),min(ys)
    im=Image.new("RGBA",(max(xs)-ox+16,max(ys)-oy+16),(0,0,0,0))
    for cell,x,y in pcs:
        t=dec(cell)
        for yy in range(16):
            for xx in range(16):
                idx=t[yy][xx]
                if idx: im.putpixel((x-ox+xx,y-oy+yy),PAL[idx]+(255,))
    bb=im.getbbox()
    if bb: im=im.crop(bb)
    return uri(im.resize((im.width*scale,im.height*scale),Image.NEAREST))

# Rastan reference full-body pose per Rastana pose (torso slot, leg slot), chosen to match the stance
RASTAN_MATCH={"idle":(0,0),"walk1":(28,18),"walk2":(29,19),"lunge":(15,13),
              "crouch":(6,6),"jump":(37,27),"attack":(38,28),"thrust":(12,8)}

frames=json.load(open(os.path.join(ROOT,"frames.json")))
def data_of(fn): return uri(Image.open(os.path.join(AS,fn)).convert("RGBA"))
def data_ref(fn):
    p=os.path.join(ROOT,"ref",fn); return uri(Image.open(p).convert("RGBA")) if os.path.exists(p) else ""
# user's original reference, upscaled crisp
def _crisp(fn,sc=5):
    im=Image.open(os.path.join(ROOT,"ref",fn)).convert("RGBA")
    px=im.load()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            if px[x,y][:3]==(255,255,255): px[x,y]=(0,0,0,0)   # white bg -> transparent
    return uri(im.resize((im.width*sc,im.height*sc),Image.NEAREST))
master_uri=_crisp("rastana_master16.png")

swatch="".join(f'<div class="sw"><i style="background:rgb{MPAL[i]}"></i><span>{i+1}</span></div>' for i in range(len(MPAL)))
cards=""
for fr in frames:
    r=RASTAN_MATCH.get(fr["key"])
    rimg=f'<img src="{rastan(*r)}" alt="rastan">' if r else '<span class="na">—</span>'
    cards+=(f'<figure class="pose"><figcaption>{fr["label"]}</figcaption>'
            f'<div class="cmp"><div class="col"><img src="{data_of(fr["file"])}" alt="rastana"><small>Rastana</small></div>'
            f'<div class="col"><div class="rr">{rimg}</div><small>Rastan (ROM)</small></div></div></figure>')

HTML=f"""<!doctype html><html lang=en><head><meta charset=utf8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Rastana Proposal</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="stylesheet"
 href="https://fonts.googleapis.com/css2?family=Cinzel:wght@600;800&family=Inter:wght@400;500;600&family=JetBrains+Mono&display=swap">
<style>
:root{{color-scheme:dark;--bg:#120d0b;--bg2:#1c1512;--card:#221813;--line:#3a2a22;--ink:#f0e5dd;
 --dim:#b7a598;--mut:#7d6a5e;--gold:#e7bb10;--red:#c23a1e;--blade:#c9c3be;--mono:'JetBrains Mono',monospace;}}
*{{box-sizing:border-box}}body{{margin:0;background:
 radial-gradient(120% 80% at 50% -10%,#241713,#120d0b);color:var(--ink);
 font-family:Inter,system-ui,sans-serif;line-height:1.55}}
.wrap{{max-width:1080px;margin:0 auto;padding:0 20px 90px}}
header{{padding:56px 20px 30px;border-bottom:1px solid var(--line);text-align:center}}
.kick{{font-family:var(--mono);letter-spacing:.32em;text-transform:uppercase;font-size:11px;color:var(--gold)}}
h1{{font-family:Cinzel,serif;font-weight:800;font-size:clamp(34px,7vw,60px);margin:.15em 0 .1em;
 background:linear-gradient(180deg,#f6d879,#c23a1e);-webkit-background-clip:text;background-clip:text;color:transparent;text-wrap:balance}}
.sub{{color:var(--dim);max-width:64ch;margin:.4em auto 0}}
h2{{font-family:Cinzel,serif;font-size:22px;margin:40px 0 6px;color:#f0d9a0}}
h2+.lead{{color:var(--dim);margin:0 0 14px;max-width:70ch}}
.panel{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:18px 20px}}
.callout{{border-left:3px solid var(--gold);background:#1d150f}}
.pal{{display:flex;flex-wrap:wrap;gap:8px;margin-top:10px}}
.sw{{display:flex;flex-direction:column;align-items:center;gap:3px;font-family:var(--mono);font-size:10px;color:var(--mut)}}
.sw i{{width:30px;height:30px;border-radius:5px;border:1px solid #0006;display:block}}
.grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(210px,1fr));gap:16px;margin-top:16px}}
.pose{{margin:0;background:var(--card);border:1px solid var(--line);border-radius:12px;overflow:hidden}}
.pose figcaption{{font-family:Cinzel,serif;font-size:13px;padding:9px 12px;border-bottom:1px solid var(--line);color:#f0d9a0}}
.cmp{{display:flex}}
.col{{flex:1;display:flex;flex-direction:column;align-items:center;gap:6px;padding:14px 8px;
 background:repeating-conic-gradient(#140f0d 0 25%,#1d1512 0 50%) 50%/16px 16px}}
.col:first-child{{border-right:1px dashed var(--line)}}
.col img{{image-rendering:pixelated;max-height:150px}}
.rr{{min-height:0}}.col small{{font-family:var(--mono);font-size:10px;color:var(--mut);letter-spacing:.05em}}
.na{{color:var(--mut)}}
.two{{display:grid;grid-template-columns:120px 1fr;gap:20px;align-items:start;margin-top:14px}}
.two img{{image-rendering:pixelated;width:100%;border:1px solid var(--line);border-radius:8px;background:#0d0a08}}
ul.spec{{margin:8px 0 0;padding-left:18px}}ul.spec li{{margin:4px 0;color:var(--dim)}}
code{{font-family:var(--mono);color:#f0d9a0;font-size:.92em}}
footer{{color:var(--mut);font-size:12px;border-top:1px solid var(--line);margin-top:50px;padding-top:16px;text-align:center}}
</style></head><body>
<header><div class="kick">Character Proposal · Bitmap Art Study</div>
<h1>Rastana</h1>
<p class="sub">A proposed heroine rendered under the exact technical constraints of the original
Taito&nbsp;Rastan arcade player sprite — same 16-colour palette, same 16&times;16-cell two-half
(torso&nbsp;+&nbsp;legs) construction. A research study in constrained pixel-art generation.</p></header>
<div class="wrap">

<section><h2>Your master</h2>
<p class="lead">You supplied Rastana already reduced to 16 colours. That is the authority for the whole
set — its palette and look are what every other pose is matched to.</p>
<div class="panel" style="text-align:center"><img src="{master_uri}" alt="Rastana master" style="image-rendering:pixelated;height:240px"><br><small style="font-family:var(--mono);color:var(--mut)">Rastana — your 16-colour master (guard lunge)</small></div>
<div class="panel callout" style="margin-top:14px"><b>Method for the rest of the set.</b> Rather than
draw new figures from scratch (which reads as crude), each additional pose <b>re-skins the real arcade
Rastan sprite</b> for that pose: his musculature, arms, legs, boots, wristband, belt and shading are
kept, and two edits inside the same palette make him Rastana — flowing red hair added behind the head
(index&nbsp;7) and a red armour top across the bare chest (index&nbsp;6/15). This keeps the frames at
arcade quality and guarantees <b>continuity</b> with both your master and Rastan's own proportions.</div></section>

<section><h2>Constraint 1 — Palette (your 16-colour master)</h2>
<p class="lead">Your fifteen sprite colours (white is the background). Every generated pose is palette-swapped
into exactly these, so the whole set is colour-consistent with your master.</p>
<div class="panel"><div class="pal">{swatch}</div></div></section>

<section><h2>Constraint 2 — Resolution &amp; construction</h2>
<div class="two"><img src="{data_of('rastana_lunge.png')}" alt="rastana lunge">
<div><ul class="spec">
<li>Figure canvas <code>32&times;48</code> px, built from <code>16&times;16</code> cells like the arcade sprite.</li>
<li><b>Two half-sprites</b>, exactly as Rastan: an upper <b>torso</b> (head + cuirass, cells at
y&nbsp;−32…−16) over a lower <b>legs</b> block (cells at y&nbsp;0…+16). The two halves compose at a
shared origin so they can animate independently — the same architecture proven in the Rastan sprite
engine (torso table <code>0x5BD40</code> / legs table <code>0x5C466</code>).</li>
<li>4bpp indexed colour; a 1-px dark outline is added around the silhouette for arcade readability.</li>
</ul></div></div></section>

<section><h2>Constraint 3 — Continuity across the pose set</h2>
<p class="lead">Each Rastana pose is shown beside the matching real Rastan frame rendered from the ROM,
so the correspondence in stance, scale and palette can be judged directly.</p>
<div class="grid">{cards}</div></section>

<section><h2>Honest assessment</h2>
<div class="panel"><ul class="spec">
<li><b>What works:</b> the palette and resolution constraints are met exactly; the character reads as a
consistent figure across all eight poses; the two-half torso/legs structure mirrors Rastan's, so these
frames would drop into the same compositor model.</li>
<li><b>What is rough:</b> this is procedural "constructed" pixel art — anatomy and shading are simpler
than hand-authored arcade art, motion arcs are approximate, and the sword/hand join is crude. A real
asset pass would refine silhouettes, add sub-pixel weight to the walk, and hand-tune each cell.</li>
<li><b>Next step if pursued:</b> lock the master torso + a leg-cycle, then hand-polish per cell at
1&times; zoom, keeping this generator as the blocking/continuity guide.</li>
</ul></div></section>

<footer>Rastana is an original proposed character. Research/capability study only — isolated from the
Rastan Genesis decompilation project. Palette &amp; Rastan reference frames rendered from the arcade ROM.</footer>
</div></body></html>"""
open(os.path.join(ROOT,"rastana_report.html"),"w").write(HTML)
print("wrote rastana_report.html (%d KB)"%(len(HTML)//1024))
