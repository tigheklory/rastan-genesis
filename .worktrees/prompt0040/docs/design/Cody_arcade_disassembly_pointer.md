# Cody Arcade Disassembly Pointer

## 1) Primary arcade disassembly location(s)
- `build/maincpu.disasm.txt`
  - Type: text disassembly listing (GNU `m68k-elf-objdump` output from raw binary)
  - Approx size: 122,241 lines
  - Coverage: `0x000000..0x05FFFF` (tail shows `Address 0x60000 is out of bounds`)
- `build/regions/maincpu.bin`
  - Type: raw arcade maincpu binary region
  - Approx size: 393,216 bytes (`0x60000`)
  - Coverage: binary region used to generate `build/maincpu.disasm.txt`

## 2) Decoded level
- `build/maincpu.disasm.txt`: **Decoded instructions, no labels** (flat linear decode; no function names/symbol table labels).
- `docs/reverse-engineering/*.md` (index/reference set): **Decoded with partial labels** (address-anchored manual reference notes, not a full symbolized disassembly).

## 3) Arcade entry point / reset vectors
- In `build/maincpu.disasm.txt` at `0x000000`/`0x000004`:
  - Reset SP vector value: `0x0010DE00`
  - Reset PC vector value: `0x0003A000`
- `_bootstrap`-equivalent label is not present in the raw disassembly file; use literal reset target address `0x0003A000`.
- Additional early vectors in the first vector-table block include repeated targets at `0x0003A004` and `0x0003A008` (literal-address form; unlabeled).

## 4) Function boundaries and labels
- `build/maincpu.disasm.txt`: **No — flat decode.**
  - No explicit function-start markers (e.g., `sub_xxxx`) and no symbolic labels beyond section marker (`<.data>`).
- `docs/reverse-engineering/*.md`: **Yes — partial.**
  - Provides manually documented routine/range boundaries by address, but not a complete symbolized function map for the full binary.

## 5) Related arcade-trace or reference artifacts
- `tools/disasm_maincpu.sh` — generator script for `build/maincpu.disasm.txt` from `build/regions/maincpu.bin`.
- `tools/show_disasm_range.py` — address-slice helper for `build/maincpu.disasm.txt`.
- `docs/reverse-engineering/disassembly_index.md` — navigation index for arcade disassembly work.
- `docs/reverse-engineering/disassembly_reference.md` — curated address/routine reference notes.
- `docs/reverse-engineering/disassembly_coverage.md` — range-by-range coverage status.
- `docs/reference/mame/rastan/src/mame/taito/rastan.cpp` (plus `pc080sn*`, `pc090oj*`, `taitoio*`) — pinned MAME source snapshot used as arcade hardware/driver reference.

## 6) Known gaps / caveats
- The primary disassembly file is a linear objdump of a raw binary, so vectors/data/jump tables appear in instruction form and require manual interpretation.
- Function boundaries and labels are not embedded in `build/maincpu.disasm.txt`; boundary identification relies on manual/reference docs.
- Multiple disassembly artifacts exist in `build/` (`maincpu`, `genesis_postpatch`, `rainbow_islands_*`); for arcade Rastan maincpu analysis, `build/maincpu.disasm.txt` + `build/regions/maincpu.bin` is the primary pair.
