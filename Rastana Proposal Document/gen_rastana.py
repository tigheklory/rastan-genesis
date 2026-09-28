#!/usr/bin/env python3
"""Rastana Proposal — RESEARCH / CAPABILITY TEST (isolated; NOT part of the Rastan Genesis project).

Uses the USER-SUPPLIED 16-colour Rastana master (ref/rastana_master16.png) as the authority for the
palette and look. Additional poses are produced by re-skinning the real arcade Rastan sprite for each
pose, PALETTE-SWAPPED into the user's 16 colours, then adding Rastana's hair + top. Keeps arcade
quality (real musculature/limbs) and matches the user's master exactly on colour. Isolated to this
folder; writes nothing back into the project.
"""
import os,io,base64,json,collections
from PIL import Image
ROOT=os.path.dirname(os.path.abspath(__file__)); AS=os.path.join(ROOT,"assets"); os.makedirs(AS,exist_ok=True)
MC=open(os.path.join(ROOT,"..","build","regions","maincpu.bin"),"rb").read()
PC=open(os.path.join(ROOT,"..","build","regions","pc090oj.bin"),"rb").read()

# ---- Rastan palette line 3 (source colours of the ROM sprite) ----
def p5(n): v=n*2; return (v<<3)|(v>>2)
def rastan_pal():
    pidx=MC[0x3BA88+3]; b=0x4FD02+pidx*32
    return [(p5((int.from_bytes(MC[b+i*2:b+i*2+2],'big')>>8)&0xF),
             p5((int.from_bytes(MC[b+i*2:b+i*2+2],'big')>>4)&0xF),
             p5(int.from_bytes(MC[b+i*2:b+i*2+2],'big')&0xF)) for i in range(16)]
RPAL=rastan_pal()

# ---- user's 16-colour master palette (white = background -> transparent) ----
def master_palette():
    im=Image.open(os.path.join(ROOT,"ref","rastana_master16.png")).convert("RGBA")
    cols=collections.Counter()
    for y in range(im.size[1]):
        for x in range(im.size[0]):
            p=im.getpixel((x,y))
            if p[3]>0: cols[p[:3]]+=1
    order=[c for c,_ in cols.most_common()]
    bg=order[0]                      # most common = white background
    pal=[c for c in order if c!=bg]  # 15 sprite colours
    return im,bg,pal
MIM,BG,MPAL=master_palette()
def nearest(pal,rgb):
    return min(range(len(pal)),key=lambda i:sum((a-b)**2 for a,b in zip(pal[i],rgb)))
# map each Rastan-line3 colour to the closest user colour (palette swap)
R2M=[nearest(MPAL,RPAL[i]) for i in range(16)]
# role colours picked from the user's master by hue (for the added hair/top)
def by_role():
    def find(rgb): return nearest(MPAL,rgb)
    return dict(hair=find((185,58,11)), hair_sh=find((83,34,16)), hair_hi=find((216,118,21)),
               top=find((134,11,6)), top_sh=find((111,18,19)), gold=find((227,202,16)),
               skin=find((219,135,108)))
ROLE=by_role()

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
def grid(u,l):
    """Return a grid of USER-palette indices (-1 transparent) from a Rastan frame, palette-swapped."""
    pcs=pieces(UP,up_off,u)+pieces(LO,lo_off,l)
    xs=[x for _,x,_ in pcs]; ys=[y for _,_,y in pcs]; ox,oy=min(xs),min(ys)
    W=max(xs)-ox+16; Hh=max(ys)-oy+16; g=[[-1]*W for _ in range(Hh)]
    for cell,x,y in pcs:
        t=dec(cell)
        for yy in range(16):
            for xx in range(16):
                ri=t[yy][xx]
                if ri: g[y-oy+yy][x-ox+xx]=R2M[ri]     # Rastan idx -> user idx
    return g

SKINSET={ROLE['skin'], R2M[3], R2M[4], R2M[5]}
def extent(g,y):
    xs=[x for x,v in enumerate(g[y]) if v>=0]
    return (min(xs),max(xs)) if xs else None
def reskin(g):
    Hh=len(g); W=len(g[0])
    rows=[y for y in range(Hh) if any(v>=0 for v in g[y])]
    if not rows: return g
    top=rows[0]
    def at(x,y): return g[y][x] if (0<=x<W and 0<=y<Hh) else -2
    def st(x,y,c):
        if 0<=x<W and 0<=y<Hh: g[y][x]=c
    # flowing hair added only onto transparent pixels
    for i,y in enumerate(range(top+1,top+18)):
        e=extent(g,y)
        if not e: continue
        lx,rx=e; grow=1+i//3
        for k in range(1,grow+1):
            c=ROLE['hair_hi'] if (k==grow and i>=8 and i%3==0) else (ROLE['hair'] if k<grow else ROLE['hair_sh'])
            if at(lx-k,y)==-1: st(lx-k,y,c)
            if at(rx+k,y)==-1: st(rx+k,y,c)
    # red top across the first 2 skin-heavy rows below the head
    head_bottom=top+8; band=[]
    for y in range(head_bottom,head_bottom+7):
        e=extent(g,y)
        if not e: continue
        if sum(1 for x in range(e[0],e[1]+1) if g[y][x] in SKINSET)>=4: band.append(y)
        if len(band)>=2: break
    for j,y in enumerate(band):
        lx,rx=extent(g,y)
        for x in range(lx,rx+1):
            if g[y][x] in SKINSET: g[y][x]= ROLE['top_sh'] if x in (lx,rx) else ROLE['top']
    return g
def to_img(g,scale=6):
    Hh=len(g); W=len(g[0]); im=Image.new("RGBA",(W,Hh),(0,0,0,0))
    for y in range(Hh):
        for x in range(W):
            if g[y][x]>=0: im.putpixel((x,y),MPAL[g[y][x]]+(255,))
    bb=im.getbbox(); im=im.crop(bb) if bb else im
    return im.resize((im.width*scale,im.height*scale),Image.NEAREST)

POSES=[
 ("idle","Idle / stand",(0,0)),
 ("walk1","Walk A",(28,18)),
 ("walk2","Walk B",(29,19)),
 ("lunge","Guard lunge (your reference pose)",(15,13)),
 ("crouch","Crouch guard",(6,6)),
 ("jump","Jump",(37,27)),
 ("attack","Overhead sword",(38,28)),
 ("thrust","Upward thrust",(12,8)),
]
def main():
    man=[]
    for key,label,(u,l) in POSES:
        im=to_img(reskin(grid(u,l))); fn=f"rastana_{key}.png"; im.save(os.path.join(AS,fn))
        man.append(dict(key=key,label=label,file=fn,rastan_u=u,rastan_l=l))
    json.dump(man,open(os.path.join(ROOT,"frames.json"),"w"),indent=1)
    print("generated %d Rastana poses in the user's 16-colour palette"%len(man))
    print("Rastan->master colour map:",R2M)
if __name__=="__main__": main()
