# Cody Build 55 Palette Bank Mapping Evidence

## Scope
Read-only mechanical evidence package for Build 55 palette bank mapping inputs.

Artifacts read:
- `build/maincpu.disasm.txt`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan/src/main.c`
- `tools/translation/postpatch_startup_rom.py`
- `specs/rastan_direct_remap.json`
- `build/rastan-direct/address_map.json`
- `build/pc080sn_attr_lut.bin`
- `docs/design/Cody_build55_palette_fix_shape_evidence.md`

## §1.1 0x59AD4 Conversion Formula Expansion

### 0x59AD4 body (verbatim excerpt)
From `build/maincpu.disasm.txt`:
- `59ad4: c2fc 0020  muluw #32,%d1`
- `59ad8: d0c1       addaw %d1,%a0`
- `59ada: eb48       lslw #5,%d0`
- `59ade: 227c 0020 0000  moveal #2097152,%a1`
- `59ae4: d2c0       addaw %d0,%a1`
- `59ae6: 3218       movew %a0@+,%d1`
- `59ae8: 0c41 ffff  cmpiw #-1,%d1`
- `59aec: 671e       beqs 0x59b0c`
- `59aee: 3401       movew %d1,%d2`
- `59af0: 3601       movew %d1,%d3`
- `59af2: 0241 0f00  andiw #3840,%d1`
- `59af6: ee49       lsrw #7,%d1`
- `59af8: 0242 00f0  andiw #240,%d2`
- `59afc: e54a       lslw #2,%d2`
- `59afe: 0243 000f  andiw #15,%d3`
- `59b02: e14b       lslw #8,%d3`
- `59b04: e74b       lslw #3,%d3`
- `59b06: d641       addw %d1,%d3`
- `59b08: d642       addw %d2,%d3`
- `59b0a: 3283       movew %d3,%a1@`
- `59b0c: 0c46 000f  cmpiw #15,%d6`
- `59b12: 5246       addqw #1,%d6`
- `59b14: 5489       addql #2,%a1`
- `59b16: 60ce       bras 0x59ae6`
- `59b18: 4e75       rts`

### Bit-field form
Let `raw = input_word`.

Address setup:
- `src_ptr = a0_in + (d1_in * 32)` (`muluw #32,%d1`, `addaw %d1,%a0`)
- `dst_ptr = 0x200000 + (d0_in * 32)` (`lslw #5,%d0`, `moveal #0x200000,%a1`, `addaw %d0,%a1`)

Per entry conversion (16 entries total, controlled by `%d6` 0..15):
- `part_a = (raw & 0x0F00) >> 7`
- `part_b = (raw & 0x00F0) << 2`
- `part_c = (raw & 0x000F) << 11`
- `out = part_a | part_b | part_c`

Sentinel handling:
- If `raw == 0xFFFF`, conversion/write path is skipped (`beqs 0x59b0c`), then pointer advance logic continues.

Input/output bit positions from the instruction sequence:
- `out[14:11] = raw[3:0]`
- `out[9:6]   = raw[7:4]`
- `out[4:1]   = raw[11:8]`
- `out[15], out[10], out[5], out[0] = 0`

### Project CLCS conversion references
From `apps/rastan/src/main.c:1020-1024`:
- `((raw >> 1) & 0x000E) | ((raw >> 2) & 0x00E0) | ((raw >> 3) & 0x0E00)`

From `tools/translation/postpatch_startup_rom.py:1547-1551`:
- `r3 = ((src >> 8) & 0xF) >> 1`
- `g3 = ((src >> 4) & 0xF) >> 1`
- `b3 = (src & 0xF) >> 1`
- `return (r3 << 1) | (g3 << 5) | (b3 << 9)`

### MATCH/DIFFER/EQUIVALENT classification
- `0x59AD4` vs project CLCS expression (`main.c:1020`): **DIFFER**
- `0x59AD4` vs `_taito_to_genesis` (`postpatch_startup_rom.py:1547`): **DIFFER**
- `0x59AD4` vs `convert_clcs_to_genesis` (`main.c:1020`): **DIFFER**

Sample inputs and outputs (project-local computation):

| input raw | out by 0x59AD4 | out by CLCS / `_taito_to_genesis` |
|---|---:|---:|
| `0x0000` | `0x0000` | `0x0000` |
| `0x0FFF` | `0x7BDE` | `0x00EE` |
| `0x0FF8` | `0x43DE` | `0x00EC` |
| `0x0EC0` | `0x031C` | `0x00A0` |
| `0x0C90` | `0x0258` | `0x0028` |
| `0x0A70` | `0x01D4` | `0x0088` |
| `0x0850` | `0x0150` | `0x0008` |
| `0x0530` | `0x00CA` | `0x0048` |

## §1.2 Tilemap Palette-Bank Consumption

### Attribute-to-LUT index extraction sites
Repeated extraction blocks in `apps/rastan-direct/src/tilemap_hooks.s`:
- BG hook block: lines `142-164`
- FG hook block: lines `314-336`
- BG fill block: lines `414-439`
- Translator helper: lines `577-604`

Observed extraction sequence pattern:
- base: `idx = attr & 0x0003`
- plus three single-bit extracts from shifted high-byte positions:
  - `... lsr ... andi #1; lsl #2; or`
  - `... lsr ... andi #1; lsl #3; or`
  - `... lsr ... andi #1; lsl #4; or`
- then `idx *= 2` and lookup: `move.w 0(%a3,%idx.w), ...`

LUT source:
- `lea genesistan_pc080sn_attr_lut, %a3` at lines `116`, `288`, `403`, `1574`.
- `build/pc080sn_attr_lut.bin` dump has 32 entries (64 bytes), values:
  - `0000 2000 4000 6000 ... 7800`
  - `8000 a000 c000 e000 ... f800`

### Consumed-bank evidence statement
- Tilemap path computes a 5-bit LUT index and reads entry `0..31` from `genesistan_pc080sn_attr_lut`.
- Consumed banks (tilemap evidence): **`0..31`** (index domain from 5-bit construction; no narrower mask after index build).
- Genesis line mapping evidence: LUT entries already carry packed VDP attribute bits (including palette-line bits in the tile attribute word), then are OR'd into staged tile words (`or.w ...` then store to staged buffers).

## §1.3 Sprite Palette-Bank Consumption

### Palette-line synthesis in emit path
From `apps/rastan-direct/src/pc090oj_hooks.s` lines `128-136`:
- `move.w %d1,%d6`
- `andi.w #0x000F,%d6`
- `or.w %d7,%d6`
- `lsr.w #4,%d6`
- `andi.w #0x0003,%d6`
- `lsl.w #8,%d6`
- `lsl.w #5,%d6`
- `or.w %d6,%d5`

`%d7` producers in sprite hooks (multiple sites):
- e.g. lines `190-192`, `250-252`, `288-290`, `425-427`, `700-702`, `716-718`
- pattern: `move.w 10*2(%a5),%d7; andi.w #0x00E0,%d7; lsr.w #1,%d7`

### Consumed-bank evidence statement
- Sprite helper path does not read direct `0x200000 + bank*0x20` palette-bank addresses.
- It computes a 2-bit palette line (`0..3`) from `%d1` low nibble + `%d7`-derived bits, then writes those bits into SAT word2.
- Consumed banks (sprite evidence): **UNKNOWN** as direct arcade bank IDs; **observed output line domain is `0..3`**.

## §1.4 Bypass Writer Mechanical Classification

### Site A — arcade_pc `0x000264`
- Original instruction: `41f9 0020 0000  lea 0x200000,%a0` (`build/maincpu.disasm.txt:188`), then write loop at `0x27c..0x29c`.
- Surrounding context: local boot/probe-style routine in low-address area (`0x264..0x2a4`) called from `0x104` (`bsrw 0x264`, line 89).
- Existing opcode_replace coverage: **NO** (no `arcade_pc: 0x000264` in `specs/rastan_direct_remap.json`).
- Reachable after `_bootstrap`: **NO** (address-map preserved vectors occupy `genesis 0x000000..0x001108`; first arcade copy begins at `arcade_start 0x000F08`, `address_map.json:22-35`).
- Target palette address: starts at `0x200000` via `%a0`, postincrement writes across sequential words.
- Target palette bank (D0-equivalent): **UNKNOWN** (loop advances sequentially until `0xFFFF` table sentinel; no explicit bank register argument).
- Touches bank consumed by current renderer (§1.2/§1.3): **UNKNOWN** (sequential span length not bounded in current evidence block).

### Site B — arcade_pc `0x03AB00`
- Original instruction: `33fc 03ff 0020 0022  movew #1023,0x200022` (`build/maincpu.disasm.txt:73730-73731`).
- Surrounding context: branch target from `0x3AA9C` (`bras 0x3ab00`, line 73701) inside startup/title-state routine.
- Existing opcode_replace coverage: **NO** (no entry for `0x03AB00` in spec).
- Reachable after `_bootstrap`: **YES** (direct branch in copied arcade code; also in copied range including `arcade_end_exclusive 0x03AB96`, `address_map.json:334-340`).
- Target palette address: absolute `0x200022`.
- Target palette bank (D0-equivalent): offset `0x22` from base `0x200000` (bank-size unit in `0x59AD4` is `0x20` bytes) => bank index `1`.
- Touches bank consumed by current renderer (§1.2/§1.3): **YES** (bank `1` is within tilemap-consumed `0..31`).

### Site C — arcade_pc `0x03AEB6` / `0x03AEDA`
- Original instructions:
  - `0x03AEB6: 3239 0020 0000  movew 0x200000,%d1`
  - `0x03AEDA: 3239 0020 0000  movew 0x200000,%d1`
  (`build/maincpu.disasm.txt:73995, 74004`)
- Surrounding context: two 8192-iteration loops with paired write-backs:
  - `0x03AEBC: 33c1 0020 0000  movew %d1,0x200000`
  - `0x03AEE0: 33c1 0020 0000  movew %d1,0x200000`
- Existing opcode_replace coverage:
  - for requested read PCs `0x03AEB6/0x03AEDA`: **NO**
  - paired write-backs are covered: `0x03AEBC` and `0x03AEE0` are patched to NOP in spec (`rastan_direct_remap.json:379-383`, `397-400`; also `address_map.json:816-886`).
- Reachable after `_bootstrap`: **YES** (`arcade_pc 0x3A000` branches to `0x3AE86`, line 72945; loops include both PCs).
- Target palette address: absolute `0x200000` (paired writes target same absolute).
- Target palette bank (D0-equivalent): bank index `0`.
- Touches bank consumed by current renderer (§1.2/§1.3): **YES** (bank `0` is within tilemap-consumed `0..31`).

### Site D — arcade_pc `0x045DAE` / `0x045DE4`
- Original instructions:
  - `0x45dae: 43f9 0020 0000  lea 0x200000,%a1`
  - `0x45de4: 43f9 0020 0600  lea 0x200600,%a1`
  (`build/maincpu.disasm.txt:88358, 88375`)
- Surrounding context:
  - both routines compute `d0 = (counter-1) * 0x80`, add to `%a1`, set `d0=#64`, and `jsr 0x3a2d0` copy.
  - caller path: `0x41f36: bsrw 0x45d72` (line 83784), and `0x45d72` calls the two routines (`88341-88343`).
- Existing opcode_replace coverage: **NO** for `0x45DAE/0x45DE4` themselves.
  - nearest replacement is at `0x45DFA` (function-body replacement entry; `specs/rastan_direct_remap.json:619-622`, `address_map.json:1587-1597`).
- Reachable after `_bootstrap`: **YES** (in copied arcade range `0x04530C..0x045DFA`, `address_map.json:1577-1583`; direct call chain from `0x41f36`).
- Target palette address:
  - branch 1: `0x200000 + (idx * 0x80)`, `idx` bounded by `cmpiw #8` (`45d86..45d8a`)
  - branch 2: `0x200600 + (idx * 0x80)`, `idx` bounded by `cmpiw #8` (`45dce..45dd2`)
- Target palette bank (D0-equivalent, using 0x20-byte bank units from `0x59AD4`):
  - `0x45DAE` path touches banks `0..31` (8 blocks * 4 banks/block)
  - `0x45DE4` path touches banks `48..79` (8 blocks * 4 banks/block, base bank 48)
- Touches bank consumed by current renderer (§1.2/§1.3):
  - `0x45DAE` path: **YES** (overlaps `0..31`)
  - `0x45DE4` path: **NO** relative to tilemap-consumed `0..31`; sprite direct bank-ID mapping is UNKNOWN.

## §1.5 Andy-Readiness Check (Mechanical)
- §1.1 conversion match/differ/equivalent classified: **YES**
- §1.2 tilemap bank consumption documented: **YES**
- §1.3 sprite bank consumption documented: **PARTIAL_UNKNOWN** (2-bit line mapping present; direct arcade bank-ID mapping unknown from current helper code)
- §1.4 bypass writers fully classified: **YES** (all required fields populated; UNKNOWN fields explicitly marked)

Readiness: **READY**

## Phase 2 Integrity
- §1.1 conversion formula expanded: YES
- §1.1 comparisons classified: YES
- §1.1 sample inputs provided: YES
- §1.2 tilemap palette-bank consumption documented: YES
- §1.3 sprite palette-bank consumption documented: PARTIAL
- §1.4 bypass writers classified with required fields: 5/5
- §1.5 Andy readiness: READY
- All findings cited from artifacts: YES
- Design recommendations performed: NONE
- Hypotheses generated: NONE
- External sources used: NO
- Source/spec/tool modifications: NO
