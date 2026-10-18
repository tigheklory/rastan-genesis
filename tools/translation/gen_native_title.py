#!/usr/bin/env python3
"""Generate the first title as a self-contained native Genesis package."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

PLANE_WORDS=64*32; TITLE_BLOCK=0x5B0B2; COLS=28; ROWS=20
BG_DEST=0xC00328; BG_BASE=0xC00000; FG_BASE=0xC08000
TEXT_TABLE=0x3BB7C; PALETTE=0x5A6FA; BLANK=0x20
TEXT_IDS=(2,30,32); ART_IDS=(18,19); INV_ID=29
ALIASES={0x21:0x2744,0x22:0x2745,0x27:0x2746,0x28:0x2747,
         0x29:0x2748,0x2C:0x2749,0x2D:0x274A,0x3F:0x274B}
SPRITE_BASE=1339; SPRITE_LIMIT=1536; SAT_DYNAMIC=18; SAT_TOTAL=29

def u16(b,o): return int.from_bytes(b[o:o+2],"big")
def u32(b,o): return int.from_bytes(b[o:o+4],"big")
def words(v): return b"".join((x&0xffff).to_bytes(2,"big") for x in v)
def akey(a): return (a&3)|(((a>>14)&1)<<2)|(((a>>15)&1)<<3)|(((a>>13)&1)<<4)
def template(b,s,n): return [(b[s+i*4],u16(b,s+i*4+2),b[s+i*4+1]) for i in range(n)]

def desc(b,i):
 p=u32(b,TEXT_TABLE+(i&0x7f)*4); d,a=u32(b,p),u16(b,p+4); p+=6; out=[]
 while b[p]: out.append(b[p]); p+=1
 return d,a,out

class Alloc:
 def __init__(self,rom,preload):
  used=set()
  for p in range(0,len(preload),4):
   if u16(preload,p)==0xffff: break
   used.add(u16(preload,p+2))
  self.free=iter(x for x in range(1,SPRITE_BASE) if x not in used)
  self.rom=rom; self.by_bytes={}; self.entries=[]
 def get(self,code):
  if code==BLANK: return 0
  raw=self.rom[(code&0x3fff)*32:(code&0x3fff)*32+32]
  if len(raw)!=32: raise ValueError(f"bad PC080SN code {code:#x}")
  if raw not in self.by_bytes:
   slot=next(self.free); self.by_bytes[raw]=slot; self.entries.append((slot,code,raw))
  return self.by_bytes[raw]

def package(entries):
 out=bytearray()
 for slot,_code,raw in entries: out+=slot.to_bytes(2,"big")+raw
 return bytes(out+b"\xff\xff")

def sat_record(index,y,x,tile,visible=True):
 sy=((y-8+0x80) if visible else 0)&0x1ff
 link=index+2 if index+1<SAT_TOTAL else 0
 return words([sy,0x0500|link,0xC000|tile,(x+0x80)&0x1ff])

def build(main,pc080,pc090,preload,attrs):
 al=Alloc(pc080,preload); bg=[0]*PLANE_WORDS; fg=[0]*PLANE_WORDS; cells=[]
 def put(dst,cell,code,attr,owner):
  slot=al.get(code); word=slot|u16(attrs,akey(attr)*2); dst[cell]=word
  cells.append(dict(owner=owner,cell=cell,source_code=f"0x{code:04X}",slot=slot,
                    attr=f"0x{attr:04X}",word=f"0x{word:04X}"))
 first=(BG_DEST-BG_BASE)//4
 for y in range(ROWS):
  for x in range(COLS): put(bg,first+y*64+x,u16(main,TITLE_BLOCK+2*(y*COLS+x)),1,"RASTAN_logo_sword")
 def apply(i,dst,art=False):
  dest,attr,codes=desc(main,i); cell=(dest-FG_BASE)//4
  if not 0<=cell<PLANE_WORDS: raise ValueError(f"title descriptor {i} outside Plane A")
  for raw in codes:
   code=raw if art else ALIASES.get(raw,raw)
   put(dst,cell,code,attr,"large_TAITO_art" if art else f"static_text_{i}"); cell+=1
 for i in TEXT_IDS: apply(i,fg)
 for i in ART_IDS: apply(i,fg,True)
 fgi=list(fg); apply(INV_ID,fgi)
 pal=[]
 for i in range(16):
  r=u16(main,PALETTE+i*2); xb=((r&0xf00)>>7)|((r&0xf0)<<2)|((r&15)<<11)
  pal.append(((((xb>>10)&31)>>2)<<9)|((((xb>>5)&31)>>2)<<5)|(((xb&31)>>2)<<1))

 mt=template(main,0x3B950,24); p1=template(main,0x3B9B0,9); p2=template(main,0x3B9D4,9)
 labels=sorted(mt[:5],key=lambda z:z[1])+p1[6:9]+p2[6:9]
 glyphs=[]
 for _y,_x,c in labels:
  if c not in glyphs:glyphs.append(c)
 for c in range(0x2a,0x34):
  if c not in glyphs:glyphs.append(c)
 slots={}; sentries=[]
 for i,c in enumerate(glyphs):
  s=SPRITE_BASE+i*4
  if s+4>SPRITE_LIMIT: raise ValueError("title sprite package exceeds sprite band")
  raw=pc090[c*128:c*128+128]; slots[c]=s
  for q in range(4): sentries.append((s+q,c,raw[q*32:(q+1)*32]))
 static=bytearray(80*8)
 for i,(y,x,c) in enumerate(labels): static[i*8:(i+1)*8]=sat_record(i,y,x,slots[c])
 positions=[(x,0) for x in range(8,0x38,8)]+[(x,0) for x in range(0xe8,0x118,8)]+[(x,0x10) for x in range(0x80,0xb0,8)]
 dynamic=bytearray()
 for i,(x,y) in enumerate(positions,len(labels)):
  hidden=sat_record(i,y,x,slots[0x2a],False); static[i*8:(i+1)*8]=hidden; dynamic+=hidden
  for d in range(10): dynamic+=sat_record(i,y,x,slots[0x2a+d],True)
 entries=al.entries+sentries
 legacy=sorted(mt[:5],key=lambda z:z[1])+mt[5:13]+[(y|0x100,x,c) for y,x,c in mt[14:17]]+p1[6:9]+p2[6:9]
 return dict(bg=bg,fg=fg,fg_invincible=fgi,palette=pal,pattern_package=package(entries),
             static_sat=bytes(static),dynamic_records=bytes(dynamic),plane_entries=al.entries,
             sprite_entries=sentries,sprite_slots=slots,labels=labels,legacy_labels=legacy,cells=cells)

def main():
 ap=argparse.ArgumentParser()
 for n in ("maincpu","pc080sn","pc090oj","title-preload","attr-lut","bg-output","fg-output",
           "fg-invincible-output","palette-output","pattern-output","sat-output","dynamic-output","frontend-labels-output","report"):
  ap.add_argument("--"+n,type=Path,required=True)
 a=ap.parse_args(); r=build(a.maincpu.read_bytes(),a.pc080sn.read_bytes(),a.pc090oj.read_bytes(),a.title_preload.read_bytes(),a.attr_lut.read_bytes())
 outs={a.bg_output:words(r["bg"]),a.fg_output:words(r["fg"]),a.fg_invincible_output:words(r["fg_invincible"]),
       a.palette_output:words(r["palette"]),a.pattern_output:r["pattern_package"],a.sat_output:r["static_sat"],a.dynamic_output:r["dynamic_records"]}
 for p,d in outs.items(): p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(d)
 lines=["/* Generated legacy later-frontend labels; title-active uses prebaked SAT. */"]
 lines += [f"    .word 0x{y:04X},0x{x:04X},0x{c:04X}" for y,x,c in r["legacy_labels"]]
 lines += ["    .word 0xFFFF,0x0000,0x0000"]
 a.frontend_labels_output.parent.mkdir(parents=True,exist_ok=True)
 a.frontend_labels_output.write_text("\n".join(lines)+"\n")
 report={"format":"rastan-native-title-v2","semantic_cut":"arcade 0x03AA54",
  "ownership":{"RASTAN_logo":"static_plane_b","sword":"static_plane_b","large_TAITO":"static_plane_a_art",
   "copyright":"static_plane_a","all_rights_reserved":"static_plane_a","credit_label":"static_plane_a",
   "1UP_label":"static_SAT","2UP_label":"static_SAT","HIGH_SCORE_label":"static_SAT",
   "P1_score":"dynamic_semantic_SAT","P2_score":"dynamic_semantic_SAT","high_score":"dynamic_semantic_SAT",
   "insert_coin_blink":"arcade_semantic_plane_owner"},
  "allocation":{"order":"first_use","dedupe":"exact_bytes","plane_unique":len(r["plane_entries"]),
   "sprite_glyphs":len(r["sprite_slots"]),"historical_slots_0349_034c_special":False},
  "static_sat_count":len(r["labels"]),"dynamic_digit_positions":SAT_DYNAMIC,"cells":r["cells"],
  "sprite_slots":{f"0x{k:02X}":v for k,v in r["sprite_slots"].items()},
  "sha256":{p.name:hashlib.sha256(d).hexdigest() for p,d in outs.items()}}
 a.report.parent.mkdir(parents=True,exist_ok=True); a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
if __name__=="__main__": main()
