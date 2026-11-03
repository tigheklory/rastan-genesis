#!/usr/bin/env python3
"""Independent static verifier for the generated native title package."""
import argparse, importlib.util, json
from pathlib import Path

def u16(b,o): return int.from_bytes(b[o:o+2],"big")
def load(path):
 s=importlib.util.spec_from_file_location("native_title_generator",path)
 if not s or not s.loader: raise SystemExit("cannot load title generator")
 m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m

def main():
 ap=argparse.ArgumentParser()
 for n in ("generator","maincpu","pc080sn","title-preload","attr-lut","bg","fg","fg-invincible",
           "palette","frontend-palette","patterns","report","spec","title-source"):
  ap.add_argument("--"+n,type=Path,required=True)
 a=ap.parse_args(); g=load(a.generator)
 main=a.maincpu.read_bytes(); pc080=a.pc080sn.read_bytes()
 r=g.build(main,pc080,a.title_preload.read_bytes(),a.attr_lut.read_bytes())
 expected={a.bg:g.words(r["bg"]),a.fg:g.words(r["fg"]),a.fg_invincible:g.words(r["fg_invincible"]),
           a.palette:g.words(r["palette"]),a.frontend_palette:g.words(r["frontend_palette"]),
           a.patterns:r["pattern_package"]}
 for p,want in expected.items():
  if p.read_bytes()!=want: raise SystemExit(f"native title output mismatch: {p}")

 package=a.patterns.read_bytes(); slots={}; p=0
 while u16(package,p)!=0xffff:
  slot=u16(package,p); raw=package[p+2:p+34]
  if slot in slots and slots[slot]!=raw: raise SystemExit(f"conflicting title slot {slot}")
  slots[slot]=raw; p+=34
 if p+2!=len(package): raise SystemExit("malformed title pattern package")
 if any(not 1<=s<1536 for s in slots): raise SystemExit("title pattern outside legal VRAM")

 report=json.loads(a.report.read_text())
 if report.get("format")!="rastan-native-title-v3": raise SystemExit("wrong title report format")
 if report["allocation"].get("historical_slots_0349_034c_special") is not False:
  raise SystemExit("historical TAITO slot workaround remains authoritative")
 for cell in report["cells"]:
  slot=cell["slot"]; code=int(cell["source_code"],16)
  if slot==0:
   if code!=0x20: raise SystemExit("nonblank title cell references blank slot")
  elif slots.get(slot)!=pc080[(code&0x3fff)*32:(code&0x3fff)*32+32]:
   raise SystemExit(f"pattern-byte mismatch owner={cell['owner']} cell={cell['cell']} code={code:#x} slot={slot}")
  plane=(a.bg.read_bytes() if cell["owner"]=="RASTAN_logo_sword" else
         a.fg_invincible.read_bytes() if cell["owner"]=="static_text_29" else a.fg.read_bytes())
  if u16(plane,cell["cell"]*2)!=int(cell["word"],16): raise SystemExit("title name-word/location mismatch")
 taito=[x for x in report["cells"] if x["owner"]=="large_TAITO_art"]
 if len(taito)!=20: raise SystemExit(f"incomplete TAITO art: {len(taito)} cells")

 src=a.title_source.read_text()
 required=("native_title_patterns","genesistan_hud_activate_frontend")
 if any(x not in src for x in required): raise SystemExit("title runtime missing generated package/semantic score source")
 forbidden=("native_title_static_sat","native_title_dynamic_records","genesistan_title_prepare_dynamic",
            "genesistan_title_sat_needs_update","pc090oj_native_emit_pass","0x0349","0x034A","0x034B","0x034C")
 if any(x in src for x in forbidden): raise SystemExit("obsolete title runtime dependency remains")

 spec=json.loads(a.spec.read_text()); cuts=[x for x in spec.get("shift_replacements",[]) if x.get("arcade_pc","").lower()=="0x03bb48"]
 if len(cuts)!=1 or cuts[0].get("operand_arcade_target","").lower()!="0x03bb7c" or not cuts[0].get("relocate_after_shift"):
  raise SystemExit("0x03BB7C glyph table is not shift-relocated semantically")
 print(f"NATIVE_TITLE_VERIFY_PASS cells={len(report['cells'])} taito={len(taito)} plane_patterns={len(slots)} shared_hud=external")
if __name__=="__main__": main()
