# [Cody — Build 54 Locate Writer to 0xC00008]

## Scope
- Task type: read-only evidence extraction.
- Target address: `0x00C00008` (and mirrors `0x00C0000A`, `0x00C0000C`, `0x00C0000E`).
- Artifacts used:
  - `build/genesis_postpatch.disasm.txt`
  - `build/maincpu.disasm.txt`
  - `apps/rastan-direct/src/*.s`
  - `specs/rastan_direct_remap.json`
  - `build/rastan-direct/address_map.json`
  - `apps/rastan-direct/out/symbol.txt`
  - `docs/design/Cody_exodus_frame_extraction_build_54_11_16.md`

## §1.1 — Direct writes to 0x00C00008 in postpatch disassembly
Search command evidence:
- `rg -n -i "c00008|c0000a|c0000c|c0000e|00c00008|00c0000a|00c0000c|00c0000e" build/genesis_postpatch.disasm.txt`

Matches found (literal `0xC00008` accesses):
1. `build/genesis_postpatch.disasm.txt:124291`
   - `714be: 33f9 00c0 0008  movew 0xc00008,0xff678c`
   - Access type: READ from `0x00C00008`.
   - Owning symbol: `genesistan_hook_3ad44_dispatch` (`apps/rastan-direct/out/symbol.txt`, `00071438 T`).
2. `build/genesis_postpatch.disasm.txt:124568`
   - `71818: 33f9 00c0 0008  movew 0xc00008,0xff678c`
   - Access type: READ from `0x00C00008`.
   - Owning symbol: `genesistan_pc090oj_hook_audit_guard` (`apps/rastan-direct/out/symbol.txt`, `000717f8 T`).

Direct write matches to `0x00C00008/0x0A/0x0C/0x0E`: `NONE`.

## §1.2 — Indirect writes via base+offset in postpatch disassembly
Search and inspection evidence:
- Searched destination-offset forms and inspected write contexts.
- Inspected `a0@(8)` write sites in postpatch helper region.

Observed `@(8)` destination writes in relevant helper region:
1. `build/genesis_postpatch.disasm.txt:124055`
   - `711f6: 3143 0008  movew %d3,%a0@(8)`
   - Register setup chain in same block:
     - `711d2: lea 0xff6384,%a0`
     - `711d8: addal %d6,%a0`
   - Effective target region: `0x00FFxxxx` (WRAM-backed structure), not `0x00C00008`.
   - Owning symbol: `.Lpc090oj_emit_slot` body within `rastan_direct_update_inputs` / PC090OJ helper region.
2. `build/genesis_postpatch.disasm.txt:124499`
   - `71742: 3143 0008  movew %d3,%a0@(8)`
   - Register setup chain in same block:
     - `71712: lea 0xff6384,%a0`
     - `71718: addal %d1,%a0`
   - Effective target region: `0x00FFxxxx`, not `0x00C00008`.
   - Owning symbol: `genesistan_pc090oj_hook_sprite_decay_5607c` neighborhood (`000716ee T`).

Postpatch base+offset write candidates resolving to `0x00C00008`: `NONE`.

## §1.3 — Indirect writes via direct pointer (e.g., `(%aN)` with `A?=0xC00008`) in postpatch disassembly
Search evidence:
- Searched for `lea/moveal` setup of `0x00C00008` into address registers and `%aN@` destination writes.

Results:
- `moveal/lea` of `0x00C00008` into an address register: `NONE`.
- `%aN@` destination write with address-register setup chain ending at `0x00C00008`: `NONE`.

Postpatch direct-pointer write candidates to `0x00C00008`: `NONE`.

## §1.4 — Direct/indirect `0x00C00008` writer patterns in arcade ROM disassembly (pre-patch)
Search evidence:
- Literal search for `0xC00008/0xC0000A/0xC0000C/0xC0000E` in `build/maincpu.disasm.txt` returned no direct literal matches.
- Indirect writer-pattern inspection produced these relevant entries:

1. `build/maincpu.disasm.txt:73893`
   - `3ad44: 20c0  movel %d0,%a0@+`
   - Caller context with `A0=0xC00000`:
     - `build/maincpu.disasm.txt:74023` `3af2c: lea 0xc00000,%a0`
     - `build/maincpu.disasm.txt:74026` `3af38: bsrw 0x3ad44`
   - Opcode-replace coverage at writer site (`arcade_pc 0x03AD44`): `YES`
     - `specs/rastan_direct_remap.json:307` (`"arcade_pc": "0x03AD44"`)
     - `replacement_bytes: "4EB9{symbol:genesistan_hook_3ad44_dispatch}4E75"`
   - Address-map mapping for patched site:
     - `build/rastan-direct/address_map.json` segment
       - `arcade_start: 0x03AD44` -> `genesis_start: 0x03AF44`
       - (`build/rastan-direct/address_map.json` near lines shown in section containing the patched site).

2. `build/maincpu.disasm.txt:407`
   - `590: 30c0  movew %d0,%a0@+`
   - Caller context with `A0=0xC00000`:
     - `build/maincpu.disasm.txt:390` `54a: lea 0xc00000,%a0`
     - `build/maincpu.disasm.txt:398` `556: bsrw 0x57c`
   - Opcode-replace coverage at writer site (`arcade_pc 0x000590`): `NO` (no matching `arcade_pc` entry in `specs/rastan_direct_remap.json`).
   - Address-map coverage note:
     - `build/rastan-direct/address_map.json` declares `arcade_source_start: 0x000F08`; this writer site is below that range.

3. `build/maincpu.disasm.txt:107990`
   - `561cc: 20c0  movel %d0,%a0@+`
   - `build/maincpu.disasm.txt:107991`
   - `561ce: 22c0  movel %d0,%a1@+`
   - Caller setup in same block:
     - `build/maincpu.disasm.txt:107940` `561c0: moveal #0xc08000,%a0`
     - `build/maincpu.disasm.txt:107941` `561c6: moveal #0xc00000,%a1`
   - Opcode-replace coverage at site range:
     - `build/rastan-direct/address_map.json` marks `arcade_start: 0x0561B6`..`0x0561D4` as `kind: patched_site`, `origin: opcode_replace`.
     - Replacement bytes there: `4eb90007106c...` (hook redirection).

Literal direct-write matches to `0x00C00008` in arcade disassembly: `NONE`.
Indirect/postincrement patterns that can touch `0x00C00008`: listed above.

## §1.5 — Source-level search for `0xC00008` references
Search command evidence:
- `rg -n -i "c00008|c0000a|c0000c|c0000e|hv_counter|hvc|vdp_hv" apps/rastan-direct/src/*.s`

Matches:
1. `apps/rastan-direct/src/pc090oj_hooks.s:414`
   - `move.w  0x00C00008, audit_guard_vcount`
   - Context (`apps/rastan-direct/src/pc090oj_hooks.s:409-416`): audit snapshot path, then read of `0x00C00008` and halt flag write.
   - Reference type: code operand, READ.
2. `apps/rastan-direct/src/pc090oj_hooks.s:798`
   - `move.w  0x00C00008, audit_guard_vcount`
   - Context (`apps/rastan-direct/src/pc090oj_hooks.s:793-800`): audit snapshot path, then read of `0x00C00008` and fired-flag write.
   - Reference type: code operand, READ.

Additional VDP constant references in `.s` (for context):
- `VDP_DATA = 0x00C00000`, `VDP_CTRL = 0x00C00004` in:
  - `apps/rastan-direct/src/vdp_comm.s`
  - `apps/rastan-direct/src/pc090oj_hooks.s`
  - `apps/rastan-direct/src/scene_load.s`

Source-level literal writes to `0x00C00008`: `NONE`.

## §1.6 — Port Monitor cross-check against §1.1–§1.3
Artifact:
- `docs/design/Cody_exodus_frame_extraction_build_54_11_16.md`

Observed panel configuration (documented in extraction):
- Port Monitor checkboxes listed as checked:
  - Status Register Read
  - Data Port Read
  - HV Counter Read
  - Control Port Write
  - Data Port Write

Representative visible rows in extraction window (frame 100 excerpt):
- `CP Write | 0x8174 | ... | Main 68000`
- `DP Write | 0x0000 | ... | Main 68000`
- `CP Write | 0x0010 | ... | Main 68000`
- `CP Write | 0x4000 | ... | Main 68000`

Visible row targeting `0x00C00008` in the documented extraction rows (frames 30-150): `NO`.

## Phase 2 — Integrity
- §1.1 direct postpatch writes search: YES; matches: 2 literal accesses, writes: 0.
- §1.2 base+offset postpatch writes search: YES; candidates resolving to `0x00C00008`: 0.
- §1.3 direct-pointer postpatch writes search: YES; candidates resolving to `0x00C00008`: 0.
- §1.4 arcade ROM writes search: YES; literal direct `0x00C00008` matches: 0; indirect postincrement candidates listed.
- §1.5 source-level search: YES; literal `0x00C00008` refs: 2 (both reads).
- §1.6 Port Monitor cross-check: YES.
- All values and addresses were cited from artifacts.
- Analysis/diagnosis/hypotheses/recommendations: NONE in this document.
