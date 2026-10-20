#!/usr/bin/env python3
"""Generate the title-specific native Genesis plane/palette package."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

PLANE_WORDS=64*32; TITLE_BLOCK=0x5B0B2; COLS=28; ROWS=20
BG_DEST=0xC00328; BG_BASE=0xC00000; FG_BASE=0xC08000
TEXT_TABLE=0x3BB7C; PALETTE=0x5A6FA; BLANK=0x20
FRONTEND_LINE0=0x4EAF6; FRONTEND_LINE1=0x4EB16; FRONTEND_LINE2=0x4FE62
TEXT_IDS=(2,30,32); ART_IDS=(18,19); INV_ID=29
SPRITE_BASE=1339
ALIASES={0x21:0x2744,0x22:0x2745,0x27:0x2746,0x28:0x2747,
         0x29:0x2748,0x2C:0x2749,0x2D:0x274A,0x3F:0x274B}

def u16(b,o): return int.from_bytes(b[o:o+2],"big")
def u32(b,o): return int.from_bytes(b[o:o+4],"big")
def words(v): return b"".join((x&0xffff).to_bytes(2,"big") for x in v)
def akey(a): return (a&3)|(((a>>14)&1)<<2)|(((a>>15)&1)<<3)|(((a>>13)&1)<<4)

def palette_word(raw):
 xb=((raw&0xf00)>>7)|((raw&0xf0)<<2)|((raw&15)<<11)
 return ((((xb>>10)&31)>>2)<<9)|((((xb>>5)&31)>>2)<<5)|(((xb&31)>>2)<<1)

def palette_line(main, address):
 return [palette_word(u16(main,address+i*2)) for i in range(16)]

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

def build(main,pc080,preload,attrs):
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
 pal=palette_line(main,PALETTE)
 # Original cold-start frontend ownership: physical bank 0 is the frontend
 # plane/HUD line, physical bank 1 is its companion plane line, and physical
 # bank 48 is the shared frontend sprite line.  Line 3 is intentionally empty
 # until a retained frontend producer (for example item bank 0x33) authors it.
 frontend_palette=(palette_line(main,FRONTEND_LINE0)+
                   palette_line(main,FRONTEND_LINE1)+
                   palette_line(main,FRONTEND_LINE2)+[0]*16)

 return dict(bg=bg,fg=fg,fg_invincible=fgi,palette=pal,frontend_palette=frontend_palette,
             pattern_package=package(al.entries),plane_entries=al.entries,cells=cells)

def main():
 ap=argparse.ArgumentParser()
 for n in ("maincpu","pc080sn","title-preload","attr-lut","bg-output","fg-output",
           "fg-invincible-output","palette-output","frontend-palette-output",
           "pattern-output","report"):
  ap.add_argument("--"+n,type=Path,required=True)
 a=ap.parse_args(); r=build(a.maincpu.read_bytes(),a.pc080sn.read_bytes(),a.title_preload.read_bytes(),a.attr_lut.read_bytes())
 outs={a.bg_output:words(r["bg"]),a.fg_output:words(r["fg"]),a.fg_invincible_output:words(r["fg_invincible"]),
       a.palette_output:words(r["palette"]),a.frontend_palette_output:words(r["frontend_palette"]),
       a.pattern_output:r["pattern_package"]}
 for p,d in outs.items(): p.parent.mkdir(parents=True,exist_ok=True); p.write_bytes(d)
 report={"format":"rastan-native-title-v3","semantic_cut":"arcade 0x03AA54",
  "ownership":{"RASTAN_logo":"static_plane_b","sword":"static_plane_b","large_TAITO":"static_plane_a_art",
   "copyright":"static_plane_a","all_rights_reserved":"static_plane_a","credit_label":"static_plane_a",
   "shared_HUD":"genesistan_native_hud_package","insert_coin_blink":"arcade_semantic_plane_owner"},
  "allocation":{"order":"first_use","dedupe":"exact_bytes","plane_unique":len(r["plane_entries"]),
   "sprite_glyphs":0,"historical_slots_0349_034c_special":False},
  "frontend_palette":{"line0_source":"0x04EAF6","line1_source":"0x04EB16",
   "line2_source":"0x04FE62","line3_source":"semantic empty until frontend producer"},
  "cells":r["cells"],
  "sha256":{p.name:hashlib.sha256(d).hexdigest() for p,d in outs.items()}}
 a.report.parent.mkdir(parents=True,exist_ok=True); a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
if __name__=="__main__": main()
