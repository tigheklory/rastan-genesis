import struct
d=open('build/regions/maincpu.bin','rb').read()
def w(a): return struct.unpack('>H', d[a:a+2])[0]
def b(a): return d[a]

FAM_VAR0=0x45502   # 8-byte records, word@0=base
FAM_VARN=0x45562
BOSS=[0x454ba,0x454d2,0x454ea]  # by variant selector (0,3,else) - see 0x45494
SCHED=0x4a104
ENDS=[0x16,0x2d,0x44,0x5b,0x72,0x89]

def round_of(x):
    for i,e in enumerate(ENDS):
        if x<=e: return i+1
    return 6

def fam_base(family,variant):
    if family==2:
        # boss: table by variant nibble via 0x45494 (0->454ba,3->454d2,else 454ea), index variant*8
        # NOTE 0x45494 uses a4+0x38 (comp) as selector d0, then variant*8 index. Approx: use variant.
        tbl=BOSS[0]
        return ('boss', w(tbl+ (variant&0xff)*8))
    tbl=FAM_VAR0 if variant==0 else FAM_VARN
    return ('fam', w(tbl+family*8))

# decode all 0x13e 1..0x89
print("0x13e rnd blk | slot: class fam cv(comp/var) f36 timer f34  -> base")
prev_blk=None
rows={}
for x in range(1,0x8a):
    rnd=round_of(x)
    blk=(x-rnd)>>1
    off=SCHED+blk*40
    slots=[]
    for s in range(5):
        rec=d[off+s*8:off+s*8+8]
        cls,fam,cv,f36=rec[0],rec[1],rec[2],rec[3]
        timer=struct.unpack('>H',rec[4:6])[0]; f34=struct.unpack('>H',rec[6:8])[0]
        comp=cv&0xf; var=cv>>4
        kind,base=fam_base(fam,var)
        slots.append((cls,fam,comp,var,f36,timer,f34,kind,base))
    rows[x]=(rnd,blk,slots)

# print per round, unique family set per 0x13e
for rnd in range(1,7):
    print("\n===== ROUND %d ====="%rnd)
    xs=[x for x in rows if rows[x][0]==rnd]
    for x in xs:
        _,blk,slots=rows[x]
        fams=set()
        for (cls,fam,comp,var,f36,timer,f34,kind,base) in slots:
            fams.add((fam,var,comp,base))
        fs=' '.join('f%d/v%d/c%d=0x%04X'%(fam,var,comp,base) for (fam,var,comp,base) in sorted(fams))
        print(" 0x%02X blk%02d: %s"%(x,blk,fs))
