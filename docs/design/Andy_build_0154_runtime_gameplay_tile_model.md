# Andy — Build 0154: Re-model the PC080SN Tile Pipeline Around the Runtime Gameplay Producer

**Agent:** Andy (temporary implementation/runtime-evidence role). **Type:** implementation + verification.
**Baseline:** `rastan-direct-proposal` @ `4028017` (Build 0153 accepted, `9aa1a58`). Build 0153 ROM
`ee232cbd…`, counter 153. **Evidence dir:** `states/traces/build_0154_runtime_gameplay_tile_model/`.

## Outcome
**Outcome F — complete bounded implementation.** The generator now models the actual runtime gameplay BG
producer; the global ROM-resident LUT and gameplay manifest cover all runtime Stage 1 codes; a producer-source
scene selector calls `load_scene_tiles(1)` naturally; and **Stage 1 outside now renders** (rocky terrain,
`ROUND 1 / READY !`) with the Build 0153 palette, frontend intact.

## Decoded descriptor format (Phase 1)
The live producer (general PC080SN strip producer, arcade `0x055C5E` → Genesis hook
`genesistan_hook_itempage_strip_blit 0x716CA`) walks a **6-byte descriptor table** at arcade `0x3951C`
(Genesis `0x3971C`):

| field | offset | width | meaning |
|---|---|---|---|
| attr | +0 | word | `0x0002` — PC080SN attr/palette word ORed into the high half of each cell |
| source | +2 | long | arcade tile-column block pointer (`0x0000D11C` family) |

Proven from arcade disassembly + `genesistan_hook_itempage_strip_populate` (`move.w (a4)`, `movea.l 2(a4),a2`)
and runtime taps (`arc_sel2.txt`: walker `0xFF10FC` = `0x0003951C`, strip source `0xFF1100` = `0xD11C→0xD91C→
0xF11C`). The table is **56 entries** (`0x3951C..0x3966C`). Each source is a **16-column × 64-row** block; the
producer reads `code = word@(src + row*32 + col*2)`, `tile = word & 0x3FFF` (high 2 bits always 0 in Stage 1).

## Complete Stage 1 source inventory (Phase 2/3)
Five distinct 0x800-byte blocks in `[0xD11C, 0xF91C)` (arcade), step `0x800`:
`0xD11C, 0xD91C, 0xE11C, 0xE91C, 0xF11C`. Derived **structurally** by `collect_runtime_gameplay_sources`
(walk the descriptor table, collect distinct sources) — no code list is embedded.
- **Distinct required codes:** 854, range `0x04A6..0x07FB`.
- **Pattern validity:** all 854 have non-blank patterns in `build/regions/pc080sn.bin`; 0 blank, 0 out-of-range,
  854 distinct patterns (no dedup needed).
- **Related producer scenes:** the same producer/hook/`0xFF1100` slot is the item-page path (KF-032); it is
  distinguished by its source pointer (item-page sources lie outside `[0xD31C,0xFB1C)`), so the scene selector
  fires only for gameplay. The old `0x5635E` 12-byte block model (codes `0x00AD…`) is proven unused by this
  producer and is reclassified out of authoritative gameplay ownership (retained in-source for reference).

## Old vs new gameplay source model (Phase 4)
- **Old (removed from gameplay ownership):** `GAMEPLAY_TABLE_START=0x5635E` 12-byte block descriptors + the
  general `strip_tiles` discovery — modeled a source the runtime never reads (KF-041).
- **New (authoritative):** `collect_runtime_gameplay_sources` reads descriptor table `0x3951C` → 5 blocks →
  16×64 codes. Gameplay scene set = these 854 tiles ∪ HUD `text_tiles`.

## Generator changes (Phase 5/6)
`tools/translation/precompute_pc080sn_tile_lut.py`:
- Added `RUNTIME_GAMEPLAY_*` constants + `collect_runtime_gameplay_sources()` (bounded, deterministic walk).
- `collect_block_write_sources` uses the runtime collector for gameplay instead of the `0x5635E` table.
- `main()` gameplay scene set = `block_scene_tiles[GAMEPLAY] | text_tiles` (dropped the unrelated `strip_tiles`
  from gameplay to fit the VRAM budget; `strip_tiles` remains in end-round which uses that model).
- LUT architecture **unchanged**: one ROM-resident global `arcade_code → VRAM_slot` LUT + per-scene manifests.
  No scene-specific LUT, no active-LUT pointer, no RAM LUT. `assign_scene_aware_slots` (existing) does the
  deterministic, conflict-free, scene-exclusive slot reuse.

## VRAM budget & coverage (Phase 5/6)
- Slot budget = `[0..1004) + [1344..1504)` = **1164 slots**. Peak scene usage = **1067** (end-round) ≤ 1164.
  Gameplay = 914 tiles.
- **LUT coverage of runtime Stage 1 codes: 854/854 (was 1/854).** Gameplay manifest: 914 pairs, every runtime
  code present, every manifest slot == its LUT slot, no intra-scene slot conflicts.
- **Scene-exclusive slot reuse:** title(0..844), gameplay(0..913), end-round(0..1406) overlap slots because the
  scenes are mutually exclusive; each scene's manifest loads the correct pattern before use.
- **Determinism:** two clean generator runs → byte-identical LUT + all three manifests (hashes match).

## Producer-source scene selector (Phase 7)
`apps/rastan-direct/src/tilemap_hooks.s` — a preamble added to `genesistan_hook_itempage_strip_blit`:
```
if strip_source ∈ [GAMEPLAY_STRIP_SRC_LO=0xD31C, GAMEPLAY_STRIP_SRC_HI=0xFB1C)
   and genesistan_current_scene_id != 1:
       load_scene_tiles(1)          ; existing lifecycle: display-off, DMA patterns, set scene id/ranges
```
- Keyed on the **producer-owned source pointer** (the relocated Stage 1 tile-column family), **not** the master
  state. No `state == 2/3/0` test, no unconditional scene-1 select. Item-page/other sources keep their scene.
- Reuses `load_scene_tiles` + `genesistan_current_scene_id`; no second loader/renderer/commit path.
- **Register/CCR:** `load_scene_tiles` preserves `d1-d7/a0-a4`; the preamble clobbers only `d0/a3`, both
  reloaded by the hook body immediately after. `d1` is stack-saved at hook entry as before.

## Canonical invariant (paired update)
The preamble grows the genesis-only hook section by `+0x180` bytes:
`CANONICAL_TOTAL_GENESIS_BYTES_COVERED 0x181D68 → 0x181EE8` in **both**
`tools/translation/postpatch_startup_rom.py` and `tools/translation/verify_canonical_rom.py` (with audit
comments). No new `opcode_replace` site (count stays 134); the `0x055C5E` spec note is extended (documentation).

## Runtime validation (Build 0154, Genesis MAME, state 2/3/0)
- **Scene selected naturally:** `genesistan_current_scene_id = 1`, `scene_a0_lo = 0x00056A22`.
- **`load_scene_tiles(1)` ran** through its display-off/DMA/display-on lifecycle; Stage 1 patterns resident.
- **BG staging nonuniform:** `staged_bg_buffer` 2048/2048 nonzero, **277 distinct** cell values (was uniform
  `0x4000`); cells are real tile indices + priority (`41F6 41F7 41F8 …`). Representative code→slot: `0x04A6→0x1F6`
  (LUT), staged `0x41F6`. Committed via the existing dirty/VBlank path (unchanged).
- **Stage 1 outside renders:** `snaps/gen0154_gameplay_600.png` — rocky terrain + `ROUND 1 / READY !`.
- **Palette:** Build 0153 Stage 1 palette intact (staged + committed).
- **Determinism:** two clean MAME boots → identical scene id / staged distinct-count / cells.
- **Frontend intact:** title (RASTAN/sword/HIGH SCORE 273100), story + BEST 5
  (273100/257200/197800/125400/112000, rounds 3/3/3/2/2, COB/THS/YAG/TKG/YTN), item page (all item rows +
  sprites). `snaps/front_title_90.png`, `front_520.png`, `front_700.png`.
- **Build 0153/0152 intact:** pointer relocations and `0xC08C62` routing unchanged (no edits to those paths).

## Build 0154
- **ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0154.bin`
- **SHA256:** `69bd306e1998e892f5fbf451d17e5657d82f7565cacc7c462d2c5b02b3fabfd8`
- **Size:** 1,580,776 B. Counter 154. Builds 0142–0153 not overwritten. Reproducible (rebuild → identical SHA).
- **Gate:** GATE_PASS; boot guard PASS; 30-s trace clean; address-map `gaps=[]`, `overlaps=[]`,
  covered `0x181EE8`, `opcode_replace=134`.

## First downstream boundary
The BG plane renders but is not yet pixel-perfect versus the arcade (the upper wall/pillar band and exact
column-to-source mapping may need the full 56-entry descriptor column ordering + FG-plane/scroll refinement);
gameplay sprites (player/enemies), scroll follow, controls, collision, and audio remain the next boundaries.
These are separate from the tile-model/scene-selection scope of this build.

## Architecture-compliance statement
CONFIRMED. Reused the existing global ROM-resident LUT, per-scene manifests, `load_scene_tiles` lifecycle,
`bg_fill` staging, dirty state, and VBlank commit. No scene-specific LUT, RAM LUT, active-LUT pointer, second
renderer/loader/commit path, forced scene ID, `state==2/3/0` test, hardcoded cells, or manual code list. Gameplay
codes derived structurally from the ROM descriptor. Build 0153 relocation and Build 0152 `0xC08C62` routing
untouched; the raw writer `0x03D04C` untouched.

## Open issue impact
- **OPEN-017:** advanced — the gameplay BG now renders through the natural producer → scene-select →
  `load_scene_tiles(1)` → global-LUT → staging → commit path; the KF-041 preload/LUT source-model mismatch is
  resolved for Stage 1 outside. Not closed (sprites/scroll/controls/audio + pixel-accuracy remain). No duplicate.
