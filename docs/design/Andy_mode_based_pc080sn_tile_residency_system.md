# Andy — Mode-Based PC080SN Tile Residency System

## 1. Executive Summary

The current PC080SN LUT is scene-aliased: 779 of the 1,067 occupied VRAM slots map to different arcade tile indices in different game scenes. A one-time global preload can hold only one tile per aliased slot, so mode transitions produce wrong-tile rendering for every slot that another scene mapped differently. Global preload is not merely inefficient — it is a deterministic correctness failure.

The correct architecture is mode-based tile residency: at every mode change, clear the existing scene's tiles from VRAM and upload the new scene's manifest before the first visible frame of that mode. Three scene manifests already exist on disk (`build/pc080sn_scene_preload_title.bin`, `_gameplay.bin`, `_endround.bin`); they encode the exact (arcade_tile, vram_slot) pairs needed per scene. The SGDK-version port (`apps/rastan/src/main.c`) already implements this architecture via `genesistan_preload_scene_tiles` and `genesistan_bulk_preload_check`.

The minimal first implementation for `apps/rastan-direct` is Option A (full reload on mode change): embed the three scene manifests in the Genesis ROM, embed `pc080sn.bin`, and implement a `load_scene_tiles` function in `main_68k.s` that clears the tile region, iterates the correct manifest, and uploads raw tile bytes from `genesistan_pc080sn_tile_rom` to the VDP before the first arcade tick of each scene. The checkerboard scaffolding, sprite system, VBlank structure, and LUT generator are not to be changed.

---

## 2. Inputs Audited

| File | Key Facts Extracted |
|------|---------------------|
| `docs/design/Cody_independent_vram_budget_verification.md` | 779 multi-tile slot collisions across scene manifests; global preload leaves wrong tile per colliding slot on mode transition; mode-based loading is the required architecture |
| `docs/design/Andy_graphics_pipeline_break_diagnosis.md` | pc080sn.bin absent from Genesis ROM; no tile upload function exists; LUT maps to slots 20–1342; nametable hook is correct |
| `docs/design/Andy_pc080sn_tile_preload_system_design.md` | Bulk preload of 1,067 tiles proposed; format is VDP-native, no conversion needed; SGDK reference uses scene-scoped DMA at scene entry; `.incbin` pattern confirmed correct |
| `docs/design/Andy_per_mode_vram_working_set_profiling_plan.md` | Title: 841 tiles, max slot 860; Gameplay: 829 tiles, max slot 848; End-Round: 1,067 tiles, max slot 1342; three distinct scene buckets defined |
| `docs/design/Andy_arcade_vs_genesis_profiling_correction.md` | Per-mode working set data is already complete from arcade ROM static analysis; Genesis-side profiling deferred |
| `AGENTS_LOG.md` | Scene-scoped loading confirmed REQUIRED by independent audit; `genesistan_preload_scene_tiles` / `genesistan_bulk_preload_check` implemented in apps/rastan; 779 slot collisions confirmed; scene source address ranges fully disjoint |
| `apps/rastan/src/main.c` lines 1452–1651 | `genesistan_scene_manifest_for_id`, `genesistan_preload_scene_tiles`, `genesistan_bulk_preload_check` — complete reference implementation |
| `apps/rastan-direct/src/main_68k.s` | Current state: LUT `.incbin`'d; no tile ROM included; no upload function; `init_staging_state` writes checkerboard to `staged_bg_buffer`; call site is `vdp_boot_setup` then `init_staging_state` |
| `tools/translation/precompute_pc080sn_tile_lut.py` | Three scene IDs (0=Title, 1=Gameplay, 2=End-Round); slot pools TILE_CACHE_BASE_A=20 / TILE_CACHE_SIZE_A=1004, TILE_CACHE_BASE_B=1280 / TILE_CACHE_SIZE_B=160 |
| `build/pc080sn_scene_preload_*.bin` (measured) | Title: 841 pairs, max slot 860; Gameplay: 829 pairs, max slot 848; End-Round: 1,067 pairs, max slot 1342 |
| `docs/design/rainbow_islands_vs_rastan_vdp_vram_buffering_comparative_trace.md` | Rainbow Islands Genesis: staged two-phase commit; VBlank disables display, DMAs WRAM to VRAM, re-enables display; scene-scoped tile loading at scene transition |
| `docs/design/Cody_rastan_vs_rainbow_tilemap_mismatch.md` | Rainbow Islands: producer sets destination before VBlank consumption; Rastan SGDK version uses hook-based scene detection inline on tilemap call |

---

## 3. Residency Buckets Required by the Data

The arcade game has exactly three distinct visual contexts, each with a distinct PC080SN tile manifest. These are established by the arcade ROM static analysis performed by `precompute_pc080sn_tile_lut.py` and confirmed by the independent verification.

| Bucket ID | Name | Source Address Range | Manifest File | Pair Count | Max VRAM Slot |
|-----------|------|----------------------|---------------|------------|---------------|
| 0 | Title / Attract | `0x5A7DA`–`0x5B0B2` | `pc080sn_scene_preload_title.bin` | 841 | 860 |
| 1 | Gameplay | `0x56A22`–`0x570C2` | `pc080sn_scene_preload_gameplay.bin` | 829 | 848 |
| 2 | End-Round | `0x5822A`–`0x59614` | `pc080sn_scene_preload_endround.bin` | 1,067 | 1,342 |

The three source address ranges are fully disjoint (confirmed by AGENTS_LOG entry for the scene-scoped tile loading architecture amendment). This property enables reliable runtime scene detection by range-checking the A0 block-write source address.

Sub-modes that do NOT constitute separate buckets:
- Attract cycling (insert coin / game over / stage intro) — uses source addresses within the Title bucket range; same bucket.
- Stage 1–6 — different block-write tables but all within the Gameplay bucket range; same bucket.
- Boss fights — within Gameplay bucket range.

There are exactly three residency buckets. No additional manifests exist in the build directory.

---

## 4. Why Global Preload Is Incorrect

### Scene Aliasing Defined

The LUT is built with scene-aware slot assignment. It uses two VRAM slot pools (Pool A: slots 20–1023, Pool B: slots 1280–1439). When two tiles from different scenes never appear simultaneously, the LUT assigns them the same VRAM slot. This cross-scene slot reuse is intentional and is what allows 2,272 unique arcade tile indices (across all three scenes) to be mapped to only 1,067 occupied VRAM slots.

The consequence: a given VRAM slot may map to tile index X in the Title manifest and tile index Y in the Gameplay manifest, where X ≠ Y. The slot is aliased.

### The Verification Finding

`Cody_independent_vram_budget_verification.md` Task 6 states the exact failure:

> 779 slots map to multiple different tiles across scene manifests. A one-time global preload leaves only one tile resident per colliding slot. Mode transitions then render wrong graphics for the other scene's tile IDs.

Of the 1,067 occupied slots, 779 are multi-scene: they hold different tile data depending on which scene is active. Only 288 slots (1,067 − 779) are guaranteed to contain the same tile data in all scenes that use them.

### Why This Is a Correctness Failure, Not Just a Memory Issue

Global preload means: at init, iterate the LUT and upload one tile per slot. For each aliased slot, the upload writes the tile corresponding to one scene's arcade tile index. After the upload, the slot contains that one scene's tile data and nothing else.

When the game transitions to a different scene — say from Title to Gameplay — the arcade nametable begins referencing tile indices whose LUT-assigned slot is one of the 779 aliased slots. The slot still contains the Title scene's tile data. The VDP renders the wrong pixels for those positions. This is visible graphical corruption on every frame of the new scene, for every position that references an aliased slot.

This is not a budget problem, not an optimization problem, and not a timing problem. It is a correctness problem: the preloaded data is wrong for the active scene. The only correct fix is to upload the new scene's tiles before the new scene renders its first frame.

### Why the LUT Cannot Be Changed to Fix This

The aliasing is inherent to the cross-scene slot reuse design. To eliminate aliasing, each scene would need its own non-overlapping slot range. That would require 841 + 829 + 1,067 = 2,737 slots for all three scenes to coexist — more than the 1,535 total available slots. The scene-aliased LUT is not a design error; it is the only possible design that fits all three scenes' tile sets within the VRAM budget. The LUT is correct by design. Global preload is incorrect by design.

---

## 5. Mode-Based Tile Residency System Design

### Design Choice: Option A — Full Reload on Mode Change

**Selected design: Option A.**

On mode change: clear the current scene's tile region in VRAM, then upload the new scene's manifest (all (arcade_tile, vram_slot) pairs) before the first visible frame of the new mode.

Option B (incremental diff) is rejected. Incremental diff requires tracking which slots the old scene used and which the new scene uses, computing the symmetric difference, and uploading only changed slots. This adds complexity for no gain: the manifests are small (largest is 1,067 pairs × 4 bytes = 4,268 bytes), the upload is fast (1,067 tiles × 32 bytes = 34,144 bytes of data, well within one display-off window at 7.67 MHz), and the logic for diff computation introduces edge cases with aliased slots that are not worth the risk at this phase.

**Justification for Option A:**
- Simple: one function, one clear+upload loop, no diff state.
- Correct: every slot in the new scene's manifest gets fresh tile data.
- Fast enough: 1,067 × 32 = 34,144 bytes synchronous CPU write completes in well under one frame at 7.67 MHz.
- Brief blank period during mode change is explicitly accepted per user.

### Data Source

The data source driving residency is the per-scene manifest files: `pc080sn_scene_preload_title.bin`, `pc080sn_scene_preload_gameplay.bin`, `pc080sn_scene_preload_endround.bin`. These are embedded in the Genesis ROM via `.incbin` directives in `main_68k.s` `.rodata` section, labeled `genesistan_scene_preload_title`, `genesistan_scene_preload_gameplay`, `genesistan_scene_preload_endround`. The PC080SN tile ROM is embedded via `.incbin "../../build/regions/pc080sn.bin"` labeled `genesistan_pc080sn_tile_rom`.

Each manifest is a sequence of `(u16 arcade_tile, u16 vram_slot)` pairs, big-endian, terminated by `u16 0xFFFF` as the arcade_tile field.

### What Happens on Mode Change

1. Display is disabled (VDP register 1 bit 6 cleared).
2. The tile VRAM region is cleared: VRAM slots 20–1342 (bytes 0x0280–0xA7E0) are zeroed by writing zeros to VDP data port in a counted loop.
3. The manifest for the new scene is iterated: for each `(arcade_tile, vram_slot)` pair (stopping at sentinel `0xFFFF`): set VDP write address to `vram_slot << 5`, copy 16 words (32 bytes) from `genesistan_pc080sn_tile_rom + (arcade_tile << 5)` to VDP data port.
4. Display is re-enabled.
5. The first arcade tick for the new mode is permitted to run.

### Residency Representation

WRAM holds:
- `genesistan_current_scene_id` (u8): 0=Title, 1=Gameplay, 2=End-Round, 0xFF=uninitialized.
- `genesistan_scene_a0_lo` (u32): lower bound of current scene's source address range.
- `genesistan_scene_a0_hi` (u32): upper bound of current scene's source address range.

These mirror the SGDK implementation exactly (the SGDK version uses the same three WRAM fields).

---

## 6. Mode Transition Trigger

Mode transitions are detected by the block-write hook at `genesistan_hook_tilemap_plane_a`. The hook is invoked on every PC080SN block-write call with A0 pointing to the arcade ROM source address of the tile data. The source address ranges for the three scenes are fully disjoint:

| Scene | Source Address Range |
|-------|----------------------|
| Title | `0x5A7DA`–`0x5B0B2` |
| Gameplay | `0x56A22`–`0x570C2` |
| End-Round | `0x5822A`–`0x59614` |

On each hook invocation:
1. Compare A0 against `genesistan_scene_a0_lo` and `genesistan_scene_a0_hi`.
2. If A0 is within the current scene's range: no mode change, proceed with tile translation.
3. If A0 is outside the current scene's range: determine the new scene ID by comparing A0 against the three known ranges; call `load_scene_tiles(new_scene_id)`; update `genesistan_current_scene_id`, `genesistan_scene_a0_lo`, `genesistan_scene_a0_hi`.

This detection approach is derived directly from the SGDK version's `genesistan_bulk_preload_check` / `genesistan_bulk_preload_check` range-check logic. The assembly optimization (compare A0 against stored lo/hi before calling C) from the SGDK amendment is the correct common-path implementation.

For the first scene at boot: `genesistan_current_scene_id = 0xFF` (uninitialized sentinel). The first hook invocation always triggers a load. Alternatively, `load_scene_tiles(SCENE_TITLE)` can be called directly from the boot sequence before the arcade tick begins — this is the preferred first-implementation approach since the game always starts with the Title scene.

---

## 7. Upload Timing and Visibility Rules

**Rule: all tile VRAM writes occur with display disabled.**

The upload sequence (clear + manifest iteration + write) runs with:
- VDP register 1 bit 6 cleared (display off) — prevents partial tile data from appearing during upload.
- Interrupts masked (SR = 0x2700) — prevents VBlank from firing and attempting a nametable commit while VRAM tile data is in an intermediate state.
- All VRAM writes synchronous CPU writes (no DMA) — no DMA completion wait needed; writes complete before the next instruction.

After the upload completes:
- Display is re-enabled (VDP register 1 bit 6 set).
- Interrupts are unmasked.
- The first nametable commit for the new scene may proceed.

**Acceptable brief blank period:** During the upload, the display is disabled and the screen shows the background color. For the initial implementation targeting the Title scene, this occurs once at boot before the first frame is displayed. For subsequent scene transitions (Title → Gameplay → End-Round), the blank period occurs at the transition. This is acceptable per the stated project constraint ("a brief black/loading period during mode transitions is acceptable").

**Upload time estimate:** End-Round (largest scene) = 1,067 tiles × 32 bytes = 34,144 bytes. At 7.67 MHz with one word write per 2 cycles, this is approximately 34,144 / 2 × 2 / 7,670,000 ≈ 4.5 ms. This is within one VBlank window (approximately 4.7 ms at 60 Hz) with marginal headroom. If this proves too slow in practice, the clear step (zeroing 49,120 bytes) can be eliminated — cleared tiles become transparent (zero data), and slots not written by the new manifest are harmless transparent tiles.

---

## 8. VRAM Partition Design

Based on the actual manifest data (confirmed by direct binary inspection of the three manifest files):

| VRAM Region | Slots | Bytes | Content |
|-------------|-------|-------|---------|
| Slot 0 | 0 | 0x0000 | Blank/transparent tile (zero-initialized, never written) |
| Slots 1–3 | 1–3 | 0x0020–0x007F | Synthetic tiles: solid-1, solid-2, checkerboard-3 (from `tile_init_words`; scaffolding, retained until removal is explicitly scheduled) |
| Slots 4–19 | 4–19 | 0x0080–0x027F | Unused / padding between synthetic tiles and PC080SN range |
| Slots 20–1342 | 20–1342 | 0x0280–0xA7E0 | PC080SN BG tiles — current scene's manifest (mode-dependent) |
| — | — | — | Note: End-Round uses slots 20–1342 (max slot 1342); Title uses slots 20–860; Gameplay uses slots 20–848 |
| Slots 1343–1535 | 1343–1535 | 0xA7E0–0xBFE0 | Available for PC090OJ sprite tiles (193 slots = 48 sixteen-by-sixteen cells) |

**N (max slot used by largest manifest) = 1342** (End-Round scene, confirmed by binary inspection).

The PC090OJ sprite tile base address must be slot 1343 or higher in any future sprite tile upload implementation. This is a hard constraint derived from the mode-based residency design: uploading sprite tiles below slot 1343 would corrupt PC080SN tile data in the scene's manifest.

Slots 4–19 are unused dead space between the synthetic tile region and the PC080SN region. They can be reclaimed for future use or left as a guard gap.

---

## 9. Minimal First Implementation

### Target Scene

The first target is the **Title/Attract scene** (scene 0, manifest `pc080sn_scene_preload_title.bin`, 841 pairs, max slot 860).

Rationale: the game always starts in Title/Attract mode; this scene is always the first to be displayed after boot; implementing it correctly proves the upload mechanism works before addressing transitions.

### What Cody Implements

**Step 1: Embed tile ROM and manifests in `apps/rastan-direct/src/main_68k.s`.**

In the `.rodata` section, after the existing `genesistan_pc080sn_attr_lut` `.incbin`:

```asm
    .align 2
genesistan_pc080sn_tile_rom:
    .incbin "../../build/regions/pc080sn.bin"

    .align 2
genesistan_scene_preload_title:
    .incbin "../../build/pc080sn_scene_preload_title.bin"
genesistan_scene_preload_title_end:

    .align 2
genesistan_scene_preload_gameplay:
    .incbin "../../build/pc080sn_scene_preload_gameplay.bin"
genesistan_scene_preload_gameplay_end:

    .align 2
genesistan_scene_preload_endround:
    .incbin "../../build/pc080sn_scene_preload_endround.bin"
genesistan_scene_preload_endround_end:
```

**Step 2: Add WRAM residency state to `.bss`.**

```asm
genesistan_current_scene_id:
    .byte 0xFF
    .align 2
genesistan_scene_a0_lo:
    .long 0
genesistan_scene_a0_hi:
    .long 0
```

**Step 3: Implement `load_scene_tiles` function in `main_68k.s`.**

Function signature: takes scene_id in `%d0`.
1. Branch to manifest base pointer based on scene_id (0=title, 1=gameplay, 2=endround).
2. Disable display: write VDP register 1 with display-off value via `vdp_set_reg`.
3. Iterate manifest: read `(arcade_tile u16, vram_slot u16)` pairs; stop at `0xFFFF` sentinel.
4. For each pair: compute VRAM address = `vram_slot << 5`; call `vdp_set_vram_write_addr`; compute source = `genesistan_pc080sn_tile_rom + (arcade_tile << 5)`; write 16 words to `VDP_DATA`.
5. Re-enable display.
6. Store scene_id to `genesistan_current_scene_id`.
7. Store scene A0 bounds to `genesistan_scene_a0_lo`/`genesistan_scene_a0_hi` (look up from a static 3-entry table of (lo, hi) pairs in `.rodata`).
8. `rts`.

**Step 4: Add call site in `main_68k`.**

Between `vdp_boot_setup` and `init_staging_state`:

```asm
main_68k:
    move.w  #0x2700, %sr
    bsr     vdp_boot_setup
    moveq   #0, %d0          ; scene_id = SCENE_TITLE
    bsr     load_scene_tiles
    bsr     init_staging_state
    move.w  #0x2000, %sr
    ...
```

**Step 5 (future, not first implementation): Wire `load_scene_tiles` to the block-write hook.**

In `genesistan_hook_tilemap_plane_a`, after the A0 range check, detect out-of-range source address and call `load_scene_tiles` with the appropriate scene_id. This step is deferred until the Title scene upload is verified visually.

### Files Modified

- `apps/rastan-direct/src/main_68k.s` — only file that changes.
- No other files are modified (no Makefile changes, no spec changes, no patcher changes, no LUT regeneration).

### Verification Gate

After implementation, emulator VRAM inspection should show:
- VRAM slots 20–860: non-zero tile pixel data (Title tiles loaded).
- VRAM slots 861–1342: zero (not used by Title manifest; either cleared or zero from boot).
- VRAM slots 1–3: synthetic tile data (unchanged).

Display output should show Title screen graphics instead of the checkerboard pattern.

---

## 10. Rainbow Islands Residency Model

### Evidence from `apps/rastan/src/main.c`

The SGDK port (`apps/rastan`) implements a complete scene-scoped tile residency model:

**`genesistan_preload_scene_tiles(u8 scene_id)`** (line 1592):
- Calls `genesistan_scene_manifest_for_id(scene_id, &manifest, &manifest_end)` to locate the correct manifest.
- Iterates `(u16 arcade_tile, u16 vram_slot)` pairs at 4-byte stride, stopping at sentinel `0xFFFF`.
- For each pair: calls `VDP_loadTileData(rastan_pc080sn + arcade_tile*32, vram_slot, 1, DMA)`.
- After the loop: `VDP_waitDMACompletion()`.
- Stores `genesistan_current_scene_id`, `genesistan_scene_a0_lo`, `genesistan_scene_a0_hi`.

**`genesistan_bulk_preload_check(u32 source_addr)`** (line 1634):
- Maps `source_addr` to a scene_id via `genesistan_scene_id_from_source_addr`.
- Returns early if `scene_id == genesistan_current_scene_id` and `source_addr` is within the stored lo/hi bounds.
- Otherwise calls `genesistan_preload_scene_tiles(mapped_scene_id)`.

**Boot-time call** (line 2252):
- `genesistan_preload_scene_tiles(GENESISTAN_SCENE_TITLE)` is called explicitly at scene setup, after `VDP_clearPlane` and `genesistan_sync_title_vdp_layout()`, before the first arcade tick is activated.

**Pattern summary:**
1. Offline tool generates per-scene manifests.
2. Manifests are embedded in the Genesis ROM as labeled ROM arrays.
3. At boot, the Title scene is preloaded explicitly.
4. On subsequent scene transitions, the block-write hook detects the new source address, maps it to a scene ID, and calls the preload function if the scene has changed.
5. No global all-tile preload. No LRU cache. No deferred/lazy loading. Scene-scoped, explicit, deterministic.

### Evidence from AGENTS_LOG

The AGENTS_LOG contains explicit confirmation that scene-scoped loading is REQUIRED and that global static assignment is REJECTED:

> "VRAM budget: SAFE WITH MANAGEMENT (scene-scoped loading required) — 2272 total unique tiles across all sources; 1164 VRAM slots; global static assignment overflows by 1108"

> "scene-scoped loading: REQUIRED — per-scene budgets all fit within 1164 slots: Title/Attract 1110, Gameplay 817, End-Round 1055"

For `rastan-direct` (with 1,535 available slots vs the SGDK version's 1,164), the VRAM overflow condition is different, but the correctness requirement (scene aliasing) is identical.

### Evidence from Rainbow Islands Comparative Trace

`rainbow_islands_vs_rastan_vdp_vram_buffering_comparative_trace.md` documents that Rainbow Islands Genesis uses staged two-phase commit: game logic populates WRAM staging buffers, VBlank disables display, DMAs staged data to VDP, re-enables display. The tile loading follows the same scene-change detection pattern: tiles are loaded into VRAM before the scene's nametable data is committed to VDP.

---

## 11. Reusable and Non-Reusable Rainbow Islands Elements

### Reusable (Architecture Principles)

| Element | Why Reusable |
|---------|-------------|
| Scene-scoped tile preload at mode entry | The core architectural principle: tile data must be in VRAM before the nametable references it; scenes define distinct tile sets; load per scene. Applies identically to rastan-direct. |
| Manifest format: `(u16 arcade_tile, u16 vram_slot)` pairs terminated by `0xFFFF` | Already in use in both SGDK and rastan-direct build artifacts. Binary format is hardware-independent. |
| Scene detection by source address range comparison | The A0 range-check approach (compare block-write source address against stored lo/hi bounds, call preload only on range miss) is architecture-neutral and translates directly to 68000 assembly. |
| Display-disable bracketing around VRAM writes | VDP requires display off during bulk tile data writes to prevent tearing. Direct mapping to `vdp_set_reg` calls already present in rastan-direct. |
| Per-scene lo/hi bound table | Three-entry static table of (lo, hi) pairs per scene. Replicated directly in `main_68k.s` rodata. |
| `genesistan_current_scene_id` / scene bounds state | Three WRAM variables for residency tracking. Direct translation from SGDK C globals to assembly BSS. |

### Non-Reusable (SGDK-Specific or C-Specific)

| Element | Why Not Reusable |
|---------|-----------------|
| `VDP_loadTileData` SGDK API call | SGDK C API. rastan-direct uses direct VDP register writes via `vdp_set_vram_write_addr` + `VDP_DATA` word writes. The mechanism is equivalent; the API is not. |
| `VDP_waitDMACompletion()` | SGDK DMA queue management. rastan-direct does not use DMA for tile uploads (synchronous CPU writes). Not applicable. |
| `genesistan_scene_manifest_for_id` C function | SGDK C switch statement returning manifest pointers. In rastan-direct this is a 3-entry branch table in assembly. Same logic, different implementation language. |
| `genesistan_scene_id_from_source_addr` C function | Iterates the `pc080sn_source_scene_map.bin` binary map. In rastan-direct, the simpler assembly approach is a 6-comparison range check against three hardcoded (lo, hi) pairs in rodata (one per scene). The source-scene map binary file is not needed. |
| `genesistan_scene_bounds_from_map` C function | Reads from `pc080sn_source_scene_map.bin`. Same simplification: hardcoded bounds table in assembly rodata. |
| C struct / pointer arithmetic for manifest iteration | C `const u8 *manifest` pointer with `text_writer_read_be16` helper. In assembly: `%a0` register advancing +4 per iteration, direct `move.w` reads. Trivial translation. |
| All SGDK-specific includes, types, and DMA modes | Not present in rastan-direct. |

---

## 12. Rainbow-Derived Design Rules for Rastan-Direct

1. **Tile pixel data must be resident in VRAM before the nametable references it.** No nametable commit may fire for a scene's tiles until those tiles have been uploaded from the PC080SN tile ROM.

2. **Scene manifests are the authority.** The manifest files (`pc080sn_scene_preload_*.bin`) encode the exact (arcade_tile, vram_slot) pairs needed per scene. The global LUT (`pc080sn_tile_vram_lut.bin`) is used by the nametable hook at translation time; the manifests are used by the loader at scene entry time. Both must agree on slot assignments (they do, by construction).

3. **One full reload per scene transition.** On every mode change, upload the new scene's complete manifest. No incremental diff. No partial update. The manifest is small enough that full reload is always fast enough.

4. **Display must be disabled during the upload.** No partial tile data may be visible. The VDP data port receives writes that must be hidden from the display until the full upload is complete.

5. **Scene identity is tracked in WRAM.** `genesistan_current_scene_id`, `genesistan_scene_a0_lo`, `genesistan_scene_a0_hi` encode the currently-loaded scene. These three variables gate the scene-change detection in the block-write hook.

6. **Scene detection uses source address range, not game state register.** The block-write hook receives A0 (PC080SN source address in arcade ROM). Comparing A0 against per-scene lo/hi bounds is the correct detection mechanism. It is O(1), reliable, and does not require reading arcade WRAM state machine registers.

7. **Boot must load the Title scene before the first arcade tick.** `load_scene_tiles(SCENE_TITLE)` is called between `vdp_boot_setup` and `init_staging_state`. The arcade game always starts in Title mode.

8. **Synthetic tiles (slots 1–3) and PC080SN tiles (slots 20–1342) do not overlap.** The existing `vdp_commit_tiles_if_dirty` mechanism for the checkerboard scaffolding writes to slots 1–3 only and is not affected by the scene loader writing to slots 20–1342.

---

## 13. Single Root Cause

The PC080SN tile VRAM LUT is scene-aliased — 779 of 1,067 occupied slots map to different arcade tile indices in different game scenes — so loading tile data for any one scene populates those aliased slots with tile data that is wrong for every other scene, making the one-time global preload proposed in `Andy_pc080sn_tile_preload_system_design.md` a deterministic correctness failure across scene transitions.

---

## 14. Single Next Correction

Cody must implement mode-based tile loading for `apps/rastan-direct`: embed `pc080sn.bin` and the three scene preload manifests in `main_68k.s` rodata via `.incbin` directives, add `genesistan_current_scene_id` / `genesistan_scene_a0_lo` / `genesistan_scene_a0_hi` to BSS, implement `load_scene_tiles` as a 68000 assembly function that iterates the manifest for the given scene_id and writes raw tile bytes (16 words per tile) to VDP with display disabled, then call `load_scene_tiles` with scene_id=0 (Title) from `main_68k` between `vdp_boot_setup` and `init_staging_state`.

---

## 15. What Must Not Be Changed Yet

- **Checkerboard scaffolding** — `tile_init_words`, `staged_tile_words`, `vdp_commit_tiles_if_dirty`, `init_staging_state` internal logic. The checkerboard fill of `staged_bg_buffer` and the synthetic tile upload remain in place. Removal is a separate future step, not part of this correction.
- **Sprite system** — no sprite tile upload, no sprite pipeline, no PC090OJ changes of any kind.
- **LUT replacement** — `genesistan_pc080sn_tile_vram_lut` and its `.incbin` directive must not be regenerated or changed. The LUT is correct and is used by the nametable hook.
- **VBlank redesign** — `_VINT_handler` structure, display-disable bracketing, commit order must not change.
- **Hook redesign** — `genesistan_hook_tilemap_plane_a` translation logic must not change. Only the scene-change detection and preload call site are added.
- **Patcher** — `postpatch_startup_rom.py` must not be modified.
- **Makefile** — no build system changes.
- **All 34 `opcode_replace` entries** in `specs/rastan_direct_remap.json`.
- **`rom_absolute_call_relocation` configuration**.
- **A5 initialization to `0xFF0000`**.
- **`VRAM_TILE_BASE = 0x00000020` constant**.
- **`pc080sn_source_scene_map.bin`** — not required for the first implementation; the hardcoded bounds table in assembly rodata is sufficient.
- **Per-mode profiling instrumentation** — WRAM bitmask profiling (`genesistan_tile_slot_observed`) must not be added; it was superseded by the correction in `Andy_arcade_vs_genesis_profiling_correction.md`.

---

## 16. Final Verdict

The global preload strategy specified in `Andy_pc080sn_tile_preload_system_design.md` is a correctness trap. Cody's independent verification confirmed it with a specific number: 779 of 1,067 occupied VRAM slots are aliased across scenes. Loading those slots once at boot cannot be correct for all scenes — exactly one scene gets the right tile data per aliased slot, and all others get wrong data.

The correct architecture is already proven and implemented in `apps/rastan/src/main.c`: scene-scoped tile loading, triggered at mode transitions, using the per-scene manifest files generated by `precompute_pc080sn_tile_lut.py`. The manifests already exist on disk. The tile ROM is already on disk. The LUT slot assignments are already correct.

The only work required for `apps/rastan-direct` is to translate the SGDK C implementation into 68000 assembly in `main_68k.s`: embed the tile ROM and three manifests via `.incbin`, implement one `load_scene_tiles` function, and call it for the Title scene at boot. This is a single-file change. No architectural redesign. No new tools. No new manifests. The data is ready; the pipeline is ready; only the loader is missing.
