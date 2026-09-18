mc=open('build/regions/maincpu.bin','rb').read()
pc=open('build/regions/pc090oj.bin','rb').read()
def be16(a): return int.from_bytes(mc[a:a+2],'big')
def s8(v): return v-256 if v>=128 else v
TAB=0x3d09e
def prog_addr(anim): return TAB+be16(TAB+anim*2)
def run_general(base, anim, facing=0):
    """Emulate the general emit path of 0x3c902. Returns list of (tile,coordA,coordB,pieceflip)."""
    a0=prog_addr(anim); pieces=[]; d2=20
    while d2>0:
        ctrl=mc[a0]; a0+=1
        if ctrl==0xFF: break
        nib=ctrl&0xF0
        if nib not in (0x00,0x40,0x80,0x70):  # special op -> stop (not general)
            return None,ctrl
        pflip=1 if nib==0x40 else 0
        b1=mc[a0]; a0+=1           # coordA (+0x1A)
        b2=mc[a0]; a0+=1           # tile offset (+0x1E), negated if pflip
        tile=(base - b2) if pflip else (base + b2)
        b3=mc[a0]; a0+=1           # coordB (+0x16), negated if facing
        cB=s8(b3); 
        if facing: cB=-cB-16
        pieces.append((tile & 0xFFFF, s8(b1), cB, pflip))
        d2-=1
    return pieces,None
if __name__=='__main__':
    from PIL import Image
    def pal5(n): v=n*2; return (v<<3)|(v>>2)
    def rompal(rnd,nib):
        idx=mc[0x3BA88+(rnd-1)*32+nib];b=0x4FD02+idx*32
        return [(pal5((be16(b+i*2)>>8)&0xF),pal5((be16(b+i*2)>>4)&0xF),pal5(be16(b+i*2)&0xF)) for i in range(16)]
    def dec(code):
        px=[[0]*16 for _ in range(16)];b=(code&0x3FFF)*128
        for r in range(16):
            for c in range(8):
                by=pc[b+r*8+c];px[r][c*2]=by>>4;px[r][c*2+1]=by&0xF
        return px
    def draw(pieces,pal,swap=False,scale=4):
        # coordA vs coordB as (x,y)
        pts=[]
        for tile,cA,cB,pf in pieces:
            x,y=(cA,cB) if swap else (cB,cA)
            pts.append((tile,x,y,pf))
        xs=[p[1] for p in pts];ys=[p[2] for p in pts];ox,oy=min(xs),min(ys)
        W=max(xs)-ox+16;H=max(ys)-oy+16
        img=Image.new('RGB',(W,H),(30,30,40))
        for tile,x,y,pf in pts:
            t=dec(tile)
            for yy in range(16):
                for xx in range(16):
                    idx=t[yy][15-xx if pf else xx]
                    if idx: img.putpixel((x-ox+xx,y-oy+yy),pal[idx])
        return img.resize((W*scale,H*scale),Image.NEAREST)
    OUT='/tmp/claude-1000/-home-tighe-projects-rastan-genesis/569ff39d-2dc7-4bcc-a421-63fe96dde6bb/scratchpad/sheets/'
    for name,base,anim,rnd,nib in [('vm_lizard',0x4B,23,1,6),('vm_lizard_sw',0x4B,23,1,6)]:
        pieces,sp=run_general(base,anim)
        if pieces is None: print(name,"hit special op 0x%02X"%sp); continue
        draw(pieces,rompal(rnd,nib),swap='_sw' in name).save(OUT+name+'.png')
        print(name,"pieces=%d"%len(pieces),"tiles",[hex(p[0]) for p in pieces])
