# Cody - Build Pipeline Address Space Audit (Investigation Only)

```text
[Andy/Cody - Investigation, build pipeline address space audit]

disassembly files found:
- /home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt: arcade
  evidence: tools/disasm_maincpu.sh:10-18 disassembles build/regions/maincpu.bin; tools/build_rastan_regions.py:175-183 creates build/regions/maincpu.bin from arcade maincpu ROM set.
- pre-patch Genesis ROM disassembly file: NONE
  evidence: find build dist apps -type f '*disasm*.txt' returned only build/maincpu.disasm.txt.
- post-patch Genesis ROM disassembly file: NONE
  evidence: same find result above; no disasm generation step in apps/rastan/Makefile or apps/rastan-direct/Makefile.

postpatch_startup_rom.py outputs besides binary:
- manifest JSON at user-supplied --manifest path
  evidence: tools/translation/postpatch_startup_rom.py:25, 582, 1339.
- relocation map JSON at <manifest_dir>/startup_common_relocations.json
  evidence: tools/translation/postpatch_startup_rom.py:583, 1338.
- operand relocation report text at /home/tighe/projects/rastan-genesis/dist/operand_relocation_report.txt
  evidence: tools/translation/postpatch_startup_rom.py:1074-1092.
- NONE additional file outputs provable from this script beyond the three above plus in-place ROM write
  evidence: all write_text/write_bytes call sites in tools/translation/postpatch_startup_rom.py.

pre-patch binary step:
- exists: YES
  evidence: apps/rastan/Makefile:52-58 builds out/rom.bin then patches it; apps/rastan-direct/Makefile:68-73 creates .prepatch.bin then patches copied output.
- name: make -f $(GDK)/makefile.gen release|debug (rastan app) and m68k-elf-objcopy (rastan-direct)
  evidence: apps/rastan/Makefile:52,132; apps/rastan-direct/Makefile:68-69.
- output location: /home/tighe/projects/rastan-genesis/apps/rastan/out/rom.bin; /home/tighe/projects/rastan-genesis/apps/rastan-direct/out/rastan_direct_video_test.prepatch.bin
  evidence: apps/rastan/Makefile:56; apps/rastan-direct/Makefile:40,68-69.

patch_maincpu.py output:
- binary: YES / /home/tighe/projects/rastan-genesis/build/rastan/maincpu_patched.bin (also emits /home/tighe/projects/rastan-genesis/build/rastan/startup_common_slice.bin)
  evidence: tools/translation/patch_maincpu.py:150-152,160-162,238-241.
- disassembly: NO / NONE
  evidence: tools/translation/patch_maincpu.py has no objdump/disasm output path; only binary + JSON manifest writes (238-240,265-267).

post-patch Genesis ROM disassembly:
- exists: NO
  evidence: only disasm producer is tools/disasm_maincpu.sh:10-18 for arcade build/regions/maincpu.bin; no post-patch ROM disasm target in apps/rastan/Makefile or apps/rastan-direct/Makefile.

specs/ json files found:
- /home/tighe/projects/rastan-genesis/specs/audio_rules.json
- /home/tighe/projects/rastan-genesis/specs/debug_bus.json
- /home/tighe/projects/rastan-genesis/specs/extraction_manifest.json
- /home/tighe/projects/rastan-genesis/specs/fixups.json
- /home/tighe/projects/rastan-genesis/specs/gfx_rules.json
- /home/tighe/projects/rastan-genesis/specs/layout.json
- /home/tighe/projects/rastan-genesis/specs/objects.json
- /home/tighe/projects/rastan-genesis/specs/rastan_direct_remap.json
- /home/tighe/projects/rastan-genesis/specs/refactor_rules.json
- /home/tighe/projects/rastan-genesis/specs/relocations.json
- /home/tighe/projects/rastan-genesis/specs/runtime_config.json
- /home/tighe/projects/rastan-genesis/specs/startup_title_remap.json
- /home/tighe/projects/rastan-genesis/specs/subsystem_modes.json
- /home/tighe/projects/rastan-genesis/specs/symbols.json
- /home/tighe/projects/rastan-genesis/specs/validation_rules.json
- /home/tighe/projects/rastan-genesis/specs/variants.json
  evidence: rg --files specs -g '*.json'.

opcode_replace JSON fields (per file):
- audio_rules.json: fields=NONE; Genesis offset recorded=NO
  evidence: no "opcode_replace" key found for this file in scripted inspection.
- debug_bus.json: fields=NONE; Genesis offset recorded=NO
- extraction_manifest.json: fields=NONE; Genesis offset recorded=NO
- fixups.json: fields=NONE; Genesis offset recorded=NO
- gfx_rules.json: fields=NONE; Genesis offset recorded=NO
- layout.json: fields=NONE; Genesis offset recorded=NO
- objects.json: fields=NONE; Genesis offset recorded=NO
- rastan_direct_remap.json: fields=arcade_pc, note, original_bytes, replacement_bytes; Genesis offset recorded=NO
  evidence: specs/rastan_direct_remap.json:103-109 and field-union inspection output.
- refactor_rules.json: fields=NONE; Genesis offset recorded=NO
- relocations.json: fields=NONE; Genesis offset recorded=NO
- runtime_config.json: fields=NONE; Genesis offset recorded=NO
- startup_title_remap.json: fields=arcade_pc, note, original_bytes, replacement_bytes; Genesis offset recorded=NO
  evidence: specs/startup_title_remap.json:1007-1013 and field-union inspection output.
- subsystem_modes.json: fields=NONE; Genesis offset recorded=NO
- symbols.json: fields=NONE; Genesis offset recorded=NO
- validation_rules.json: fields=NONE; Genesis offset recorded=NO
- variants.json: fields=NONE; Genesis offset recorded=NO

Evidence for opcode_replace presence/absence:
- key present only in specs/rastan_direct_remap.json:103 and specs/startup_title_remap.json:1007 (rg -n '"opcode_replace"' specs/*.json).
- all per-file opcode_replace field lists from direct JSON parse; no opcode_replace field named rom_pc or other Genesis ROM offset field.
```
