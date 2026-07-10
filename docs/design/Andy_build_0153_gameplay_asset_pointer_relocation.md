# Andy — Build 0153: Relocate the Gameplay Scene-Asset Embedded Pointer-Table Family

**Agent:** Andy (temporary implementation/runtime-evidence role). **Type:** implementation + verification.
**Baseline:** `rastan-direct-proposal` @ `7f3c5fb` (Build 0152 accepted, `454add2`). Build 0152 ROM
`3d805331815588576a3fdeef732a7b094f3c15997b66c76830827adfc2f35214`, counter 152.
**Evidence dir:** `states/traces/build_0153_gameplay_asset_pointer_relocation/`.

## Outcome
**Implemented (bounded embedded-pointer relocation).** The complete, structurally-bounded family of gameplay
scene-asset **embedded** pointer tables consumed by the gameplay scene loader `R_c` (arcade `0x059DE8`) and its
adjacent sub-loaders is now relocated by the existing JSON-driven `absolute_long_pointer_tables` mechanism. The Stage 1
outside **palette source now resolves to copied data and reaches staged/committed CRAM** (the "black + one pink entry"
result is gone). The BG/tile and layout pointer sources are also corrected. The **first gameplay frame remains
incomplete** — the visible BG tilemap does not yet render — which is the separately-identified next boundary.

## Root cause (settled, from `Andy_gameplay_init_control_flow_divergence.md`)
The gameplay loaders build their asset source pointers from **absolute longwords embedded in data tables**. The
post-patch `rom_absolute_call_relocation` rewrites absolute longwords only when they are **instruction operands**
(0x207C, 0x4EB9, …), so these embedded-data pointers stayed at their original arcade addresses → the loaders read
arcade-offset data (mostly zeros). This is the KF-028 / OPEN-016 class; the existing `absolute_long_pointer_tables`
declaration already handles it for the title glyph table.

## The complete relocated family (3 tables; enumerated from R_c + sub-loaders)
All three are in the gameplay scene-loader segment (arcade `0x059B1A..0x059F5E`), entry_size 4, pointer-field offset 0,
copied-ROM mapping `+0x200` (whole-maincpu copy; byte-neutral `opcode_replace` ⇒ no net shift). The other three
sub-loaders (`0x5a01e/0x5a036/0x5a050`) index **word/byte** count tables, not pointers, and are correctly left alone.

| # | arcade table | Genesis table | entries | consumer (Genesis) | asset role | index / selector |
|---|---|---|---|---|---|---|
| 1 | `0x059EC8` | `0x05A0C8` | 6 | `0x05A06C` (R_c sub-loader) → palette hook | per-stage **palette** source | stage `a5@0x118` × 4 |
| 2 | `0x059C9A` | `0x059E9A` | 6 | `0x059E64` (`movea.l #0x059E9A,a3`) | per-stage **PC080SN BG/tile pattern** source | stage |
| 3 | `0x059F1E` | `0x05A11E` | 4 | `0x05A0E0` (`movea.l #0x05A11E,a0`) | per-substage **layout/scroll descriptor** source | `a5@0x1D & 0x0C` |

**Bounds proof:** each entry count is the first non-ROM-pointer longword after the table (palette entry[6] = code
`0x4240102D`; BG/tile entry[6] = code `0x41F90010`; layout entry[4] = data `0x00100020`, out of the source window),
matched to the loader index expression. Every declared entry is a genuine 24-bit `0x0004xxxx`/`0x0005xxxx` ROM
pointer; no zero/sentinel/RAM/hardware/index/already-relocated entries. False positives excluded: `0x05A0BC` is a
word count-table (`0x0001…`), `0x05A1E6+` are `0x30FC/0x4E75` code bytes.

## Before/after pointer inventory (each `+0x200`)
- **Palette `0x05A0C8`:** `0x5DB4E→0x5DD4E, 0x5DC4E→0x5DE4E, 0x5DD4E→0x5DF4E, 0x5DE4E→0x5E04E, 0x5DF4E→0x5E14E,
  0x5E04E→0x5E24E`. Stage 1 (entry[0]): `0x5DB4E` (= `0000 0000 …`, blank) → `0x5DD4E` (= `0000 0357 0457 0547 …`,
  real palette).
- **BG/tile `0x059E9A`:** `0x4EAF6→0x4ECF6, 0x4EEF8→0x4F0F8, 0x4F15A→0x4F35A, 0x4F51C→0x4F71C, 0x4F85E→0x4FA5E,
  0x4FA80→0x4FC80`. Stage 1 (entry[0]): `0x4EAF6` (= code `6004 303c …`) → `0x4ECF6` (= gfx `0000 0fff 0f00 0875 …`).
- **Layout `0x05A11E`:** `0x59F2E→0x5A12E, 0x59F3A→0x5A13A, 0x59F46→0x5A146, 0x59F52→0x5A152`. Entry[0] relocated
  data = `0010 0020 0040 0060 0080 9999`.

## JSON declarations (source of truth)
`specs/rastan_direct_remap.json` → `absolute_long_pointer_tables`: added 3 entries (arcade `0x059EC8`, `0x059C9A`,
`0x059F1E`). Each uses the existing schema (`table_address`, `entry_count`, `entry_size_bytes`, `note`) — **no schema
extension or tool change was needed** (the mechanism already relocates each in-window entry by the copy delta and
skips out-of-window entries). No manual byte patch, no heuristic ROM scan, no Python address list.

### JSON `note` audit
| file | declaration (table_address) | note present | one-line summary |
|---|---|---|---|
| `specs/rastan_direct_remap.json` | `0x059EC8` | yes | Build 0153/KF-028/OPEN-016/OPEN-017 per-stage palette table, consumer 0x5A06C→palette hook, bounds/stride/evidence |
| `specs/rastan_direct_remap.json` | `0x059C9A` | yes | Build 0153/… per-stage PC080SN BG/tile pattern table, consumer 0x059E64, unrelocated=code→relocated=gfx proof |
| `specs/rastan_direct_remap.json` | `0x059F1E` | yes | Build 0153/… per-substage layout table, consumer 0x05A0E0 (a5@0x1D&0x0C), 4 entries |
Existing `0x03BB7C` note preserved unchanged.

## Validation
### Static
- All 3 tables relocated exactly `+0x200`; table bases unchanged; entry counts exact; no double-relocation.
- ROM diff vs Build 0152 = **only** the 3 tables' pointer bytes + the ROM checksum byte; size unchanged (1,580,392).
- Address-map: `gaps = []`, `overlaps = []`, `total_genesis_bytes_covered = 0x181D68`, `opcode_replace = 134`
  (unchanged — no opcode added). GATE_PASS; boot guard PASS; 30-s trace clean (`fg_cwindow_live = 0`, `reg_c50000_live
  = 0`).
### Runtime (gameplay, state 2/3/0)
- **Palette proof:** `genesistan_palette_hook_59ad4` now receives **A0 = `0x0005DD4E`** (the relocated Stage 1 source;
  was `0x0005DB4E`). Staged palette nonzero words **1 → 16**; staged line 2 = `0000 0642 0644 0644 0646 0644 0868 0668
  066a 068c 068e 0aac 0e00 0aee 0e80 0cc0` (converted Stage 1 outside colours); committed via the existing VBlank
  path. The "black + one pink entry" symptom is gone.
- No manual forcing: `load_scene_tiles(1)` was **not** called, scene ID was **not** forced, the palette was **not**
  hand-loaded, state was **not** advanced.
### Frontend regression (Build 0151/0152 intact)
- No-credit title `0/1/0`, HIGH SCORE source `0xFF0142 = 00 27 31` (273100). BEST 5 (attract `2/0/0`): `1ST 273100 3
  COB · 2ND 257200 3 THS · 3RD 197800 3 YAG · 4TH 125400 2 TKG · 5TH 112000 2 YTN`. Item screen reached (`2/2/6`). The
  relocated tables are gameplay-only, so title/coined title/story/BEST 5/PC090OJ clipping/frontend palette are
  unaffected. Build 0152 `0xC08C62` routing intact (`fg_cwindow_live = 0`).

## First downstream boundary (next task, not this build)
The visible BG does not render: at gameplay `genesistan_current_scene_id` is still `0` and `scene_a0_lo` stays the
title range `0x0005A7DA`, so `load_scene_tiles(1)` does not fire and the Stage 1 BG **tile patterns are not loaded into
VRAM**, and the BG **tilemap cells** are not populated. The BG/tile *sources* (table `0x059C9A`) are now correct; the
next boundary is the gameplay BG tile-pattern load + tilemap population + scroll path (a separate, non-pointer concern).

## Build 0153
- **ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0153.bin`
- **SHA256:** `ee232cbdda4880a56c51f7be26ff6bb07f811dbad8d7987e600e61af33c5707a`
- **Size:** 1,580,392 B. Counter 153. Builds 0142–0152 not overwritten.
- **Files changed:** `specs/rastan_direct_remap.json` (3 pointer-table declarations); regenerated
  `build/rastan-direct/*` (address_map, patch_manifest), `build/rom_inventory.json`, disasm; this doc; `AGENTS_LOG.md`,
  `OPEN_ISSUES.md`.

## Architecture-compliance statement
CONFIRMED. The fix is expressed entirely as declarative source-JSON `absolute_long_pointer_tables` entries relocated
by the existing post-patch mechanism — no new loader, palette system, tilemap renderer, or commit path; no manual byte
patch, heuristic scan, scene special-casing, forced scene ID, or hand-loaded palette; instruction-operand relocation
unchanged. Real-hardware / BlastEm / Exodus validation NOT CLAIMED.

## Open issue impact
- **OPEN-017 (ROM does not run on real hardware / gameplay):** advanced — the gameplay scene-asset embedded-pointer
  relocation gap is closed for the complete proven table family; the Stage 1 outside palette now resolves and reaches
  CRAM. Next boundary: gameplay BG tile-pattern load / tilemap population. Not closed; no duplicate.

## Deferred (unless directly caused by the same relocated table family)
Stale `2731`/`2UP` records, PC090OJ clear/lifecycle, item-scroll sequencing, sprite-slot ownership, the raw writer
`0x03D04C`, gameplay BG tilemap/scroll rendering, controls, collision, audio, credit positioning, and copyright-region
differences were not touched.
