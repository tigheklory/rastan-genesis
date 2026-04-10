# Cody — A5 WRAM Base Redirect

## 1. Executive Summary
A single `opcode_replace` patch was added at arcade PC `0x03AF04` to redirect `A5` base initialization from `0x10C000` to `0xFF0000`. This redirects all subsequent A5-relative arcade workram writes from Genesis ROM space into Genesis WRAM.

## 2. Root Cause Reference
Root cause reference: `docs/design/Andy_pc080sn_wram_write_path_diagnosis.md`.

## 3. Old Incorrect A5 Base Behavior
Old instruction at `0x03AF04`:
- `lea 0x10C000, %a5`

On Genesis, A5-relative targets such as descriptor list writes (`A5+0x1000`) resolved into `0x10D000+`, which is ROM space, so writes were discarded.

## 4. New Redirected A5 Base Behavior
New patched instruction at `0x03AF04`:
- `lea 0xFF0000, %a5`

This redirects A5-relative writes to Genesis WRAM, including:
- `A5+0x10A0 -> 0xFF10A0`
- `A5+0x10CA -> 0xFF10CA`
- `A5+0x1000..0x103C -> 0xFF1000..0xFF103C`

## 5. Exact Spec Entry Added
Added to `specs/rastan_direct_remap.json`:
- `arcade_pc`: `0x03AF04`
- `original_bytes`: `4BF90010C000`
- `replacement_bytes`: `4BF900FF0000`
- note describing A5 base redirect to WRAM.

## 6. Exact Files Modified
- `specs/rastan_direct_remap.json`
- `docs/design/Cody_a5_wram_base_redirect.md`
- `AGENTS_LOG.md`

## 7. Verification Performed
1. Verified disassembly and bytes at source site:
   - `build/maincpu.disasm.txt` shows `0x03AF04: lea 0x10c000,%a5`
   - `xxd -g1 -l 6 -s 0x03AF04 build/regions/maincpu.bin` confirms `4b f9 00 10 c0 00`
2. Built `rastan-direct` successfully.
3. Verified manifest contains patch entry at `arcade_pc: 0x03AF04`.
4. Verified spec expectation count matches actual opcode_replace count (`31`).

## 8. Backward Compatibility Impact
This change is scoped to `rastan-direct` remap spec only. It does not modify SGDK branch runtime code paths.

## 9. Risks / Known Limitations
The patch redirects all A5-relative arcade workram accesses to WRAM as intended, but runtime visual correctness still depends on subsequent state production/consumption paths that are outside this single-fix scope.

## 10. Final Verdict
The single required redirect was implemented exactly at `0x03AF04` with verified original bytes and successful manifest/build validation, enabling A5-relative arcade workram writes to target Genesis WRAM instead of ROM.
