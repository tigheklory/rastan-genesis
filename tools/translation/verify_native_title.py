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
 for n in ("generator","maincpu","pc080sn","pc090oj","title-preload","attr-lut","bg","fg","fg-invincible",
           "palette","patterns","static-sat","dynamic-records","report","spec","title-source"):
  ap.add_argument("--"+n,type=Path,required=True)
 a=ap.parse_args(); g=load(a.generator)
 main=a.maincpu.read_bytes(); pc080=a.pc080sn.read_bytes(); pc090=a.pc090oj.read_bytes()
 r=g.build(main,pc080,pc090,a.title_preload.read_bytes(),a.attr_lut.read_bytes())
 expected={a.bg:g.words(r["bg"]),a.fg:g.words(r["fg"]),a.fg_invincible:g.words(r["fg_invincible"]),
           a.palette:g.words(r["palette"]),a.patterns:r["pattern_package"],a.static_sat:r["static_sat"],
           a.dynamic_records:r["dynamic_records"]}
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
 if report.get("format")!="rastan-native-title-v2": raise SystemExit("wrong title report format")
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

 sat=a.static_sat.read_bytes()
 if len(sat)!=640 or report["static_sat_count"]!=11: raise SystemExit("wrong static SAT shape")
 seen=[]
 for i in range(29):
  link=u16(sat,i*8+2)&0x7f
  want=i+2 if i<28 else 0
  if link!=want: raise SystemExit(f"bad title SAT link {i}: {link} != {want}")
  tile=u16(sat,i*8+4)&0x7ff
  if tile not in slots: raise SystemExit(f"title SAT references missing pattern slot {tile}")
  seen.append((u16(sat,i*8),u16(sat,i*8+6),tile))
 if len(set(seen[:11]))!=11: raise SystemExit("duplicate/missing fixed title labels")
 dyn=a.dynamic_records.read_bytes()
 if len(dyn)!=18*11*8: raise SystemExit("wrong dynamic title record table size")
 for pos in range(18):
  for variant in range(11):
   rec=dyn[(pos*11+variant)*8:(pos*11+variant+1)*8]
   if (u16(rec,4)&0x7ff) not in slots: raise SystemExit("dynamic digit references missing pattern")
   if variant==0 and u16(rec,0)!=0: raise SystemExit("hidden dynamic record is visible")
 if dyn[0:88]==dyn[6*88:7*88]: raise SystemExit("P1 dynamic position duplicated as P2 position")

 src=a.title_source.read_text()
 required=("native_title_patterns","native_title_static_sat","native_title_dynamic_records",
           "0x00FF009E","0x00FF00DE","0x00FF011E","0x00FF0142")
 if any(x not in src for x in required): raise SystemExit("title runtime missing generated package/semantic score source")
 forbidden=("genesistan_title_sat_needs_update","pc090oj_native_emit_pass","0x0349","0x034A","0x034B","0x034C")
 if any(x in src for x in forbidden): raise SystemExit("obsolete title runtime dependency remains")

 spec=json.loads(a.spec.read_text()); cuts=[x for x in spec.get("shift_replacements",[]) if x.get("arcade_pc","").lower()=="0x03bb48"]
 if len(cuts)!=1 or cuts[0].get("operand_arcade_target","").lower()!="0x03bb7c" or not cuts[0].get("relocate_after_shift"):
  raise SystemExit("0x03BB7C glyph table is not shift-relocated semantically")
 print(f"NATIVE_TITLE_VERIFY_PASS cells={len(report['cells'])} taito={len(taito)} patterns={len(slots)} static_sat=11 dynamic=18x11")
if __name__=="__main__": main()
