#!/usr/bin/env python3
"""Rastana registration templates — the alignment tool.

For every player frame this emits a high-res 'trace-over' guide that pins the three things a free-hand
image generator keeps getting wrong:
  * the FIXED WAIST SEAM (torso bottom = leg top, the stationary join),
  * the exact HAND / WEAPON-GRIP point (from the arcade weapon-overlay table, so an in-game sword
    lands in her hand),
  * Rastan's SILHOUETTE + cell grid + centre axis (so proportions match his frame 1:1).
Draw Rastana onto the template matching the grey silhouette, keep the waist on the cyan line, and put
her sword hand on the magenta cross — the result drops straight into the game's torso/leg + weapon
tables. Reads the arcade ROM (structure only); all output stays in this folder.
"""
import os,io,json
from PIL import Image, ImageDraw
ROOT=os.path.dirname(os.path.abspath(__file__)); OUT=os.path.join(ROOT,"registration"); os.makedirs(OUT,exist_ok=True)
MC=open(os.path.join(ROOT,"..","build","regions","maincpu.bin"),"rb").read()
PC=open(os.path.join(ROOT,"..","build","regions","pc090oj.bin"),"rb").read()
def p5(n): v=n*2; return (v<<3)|(v>>2)
pidx=MC[0x3BA88+3]; b=0x4FD02+pidx*32
PAL=[(p5((int.from_bytes(MC[b+i*2:b+i*2+2],'big')>>8)&0xF),p5((int.from_bytes(MC[b+i*2:b+i*2+2],'big')>>4)&0xF),
      p5(int.from_bytes(MC[b+i*2:b+i*2+2],'big')&0xF)) for i in range(16)]
def s8(x): return x-256 if x>=128 else x
def dec(code):
    px=[[0]*16 for _ in range(16)]; base=code*128
    for r in range(16):
        for c in range(8):
            by=PC[base+r*8+c]; px[r][c*2]=by>>4; px[r][c*2+1]=by&0xF
    return px
def offs(TBL,n): return [int.from_bytes(MC[TBL+i*2:TBL+i*2+2],'big') for i in range(n)]
UP,LO,WPN=0x5BD40,0x5C466,0x5CD8A
up_off,lo_off,wp_off=offs(UP,75),offs(LO,52),offs(WPN,75)
def cells(TBL,offlist,slot):
    o=offlist[slot]; srt=sorted(offlist); nx=min([x for x in srt if x>o]+[o+24]); n=(nx-o)//6
    base=TBL+o; out=[]
    for p in range(n):
        r=MC[base+p*6:base+p*6+6]; t=int.from_bytes(r[0:2],'big')
        if t&0x1fff: out.append((t&0x1fff,s8(r[2]),s8(r[3])))
    return out

# animation-tagged frame set (torso slot, leg slot, human label) — waist at y=0 for every one
FRAMES=[
 (0,0,"idle"),(28,18,"walk A"),(29,19,"walk B"),(30,20,"walk C"),
 (15,13,"climb / rope A"),(16,14,"climb / rope B"),(17,15,"climb / rope C"),(18,16,"climb / rope D"),
 (12,8,"up-thrust"),(13,8,"up-thrust B"),
 (6,6,"crouch guard"),(37,27,"jump"),(38,28,"overhead sword"),(44,34,"weapon swing"),
 (40,30,"death: dissolve A"),(41,31,"death: dissolve B"),(42,32,"death: dissolve C"),
 (70,42,"death: burn A"),(72,44,"death: burn B"),
]

SCALE=14
def build(u,l,label):
    body=cells(UP,up_off,u)+cells(LO,lo_off,l)
    sword=cells(WPN,wp_off,u) if u<len(wp_off) else []
    allc=body+sword
    xs=[x for _,x,_ in allc]; ys=[y for _,_,y in allc]
    ox,oy=min(xs+[-16]),min(ys+[-40]); ex,ey=max(xs+[16])+16,max(ys+[16])+16
    W=(ex-ox); H=(ey-oy)
    im=Image.new("RGBA",(W*SCALE,H*SCALE),(24,20,28,255))
    dr=ImageDraw.Draw(im)
    def gx(x): return (x-ox)*SCALE
    def gy(y): return (y-oy)*SCALE
    # cell grid (16px) faint
    for x in range(ox-(ox%16),ex+16,16): dr.line([(gx(x),0),(gx(x),H*SCALE)],fill=(255,255,255,18))
    for y in range(oy-(oy%16),ey+16,16): dr.line([(0,gy(y)),(W*SCALE,gy(y))],fill=(255,255,255,18))
    # body silhouette (light grey fill = the shape to match)
    for cell,x,y in body:
        t=dec(cell)
        for yy in range(16):
            for xx in range(16):
                if t[yy][xx]:
                    dr.rectangle([gx(x+xx),gy(y+yy),gx(x+xx)+SCALE-1,gy(y+yy)+SCALE-1],fill=(150,150,158,150))
    # sword guide (yellow outline of the weapon cells)
    for cell,x,y in sword:
        t=dec(cell)
        for yy in range(16):
            for xx in range(16):
                if t[yy][xx]:
                    dr.rectangle([gx(x+xx),gy(y+yy),gx(x+xx)+SCALE-1,gy(y+yy)+SCALE-1],outline=(240,210,40,220))
    # centre axis
    dr.line([(gx(0),0),(gx(0),H*SCALE)],fill=(90,150,240,150),width=2)
    # WAIST SEAM at y=0 (torso bottom / leg top) — the fixed join
    dr.line([(0,gy(0)),(W*SCALE,gy(0))],fill=(40,210,230,255),width=3)
    dr.text((6,gy(0)+4),"WAIST SEAM (fixed)",fill=(40,210,230,255))
    # HAND / weapon grip = sword hilt (largest-y sword cell) centre
    hand=None
    if sword:
        hilt=max(sword,key=lambda c:c[2]); hx=hilt[1]+8; hy=hilt[2]+14; hand=(hx,hy)
        cx,cy=gx(hx),gy(hy)
        dr.line([(cx-16,cy),(cx+16,cy)],fill=(240,50,160,255),width=3)
        dr.line([(cx,cy-16),(cx,cy+16)],fill=(240,50,160,255),width=3)
        dr.text((cx+8,cy+8),"HAND / weapon grip",fill=(240,50,160,255))
    dr.text((6,6),f"{label}   torso {u} + legs {l}",fill=(235,225,215,255))
    fn=f"reg_{label.replace('/','').replace(':','').replace(' ','_')}_u{u}_l{l}.png"
    im.save(os.path.join(OUT,fn))
    return dict(label=label,torso=u,legs=l,waist_y=0,
                hand_grip=hand, sword_cells=[(c,x,y) for c,x,y in sword],
                body_cell_count=len(body), bbox=[ox,oy,ex,ey])

def main():
    man=[build(u,l,lab) for u,l,lab in FRAMES]
    json.dump(man,open(os.path.join(ROOT,"registration_data.json"),"w"),indent=1)
    print("wrote",len(man),"registration templates ->",OUT)
if __name__=="__main__": main()
