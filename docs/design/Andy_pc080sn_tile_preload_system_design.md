# Andy — PC080SN Tile Preload System Design

## 1. Executive Summary

The rastan-direct wrapper has a complete nametable translation pipeline (LUT, hook, staging, commit) but no tile pixel data in VRAM. The PC080SN tile ROM (`pc080sn.bin`, 524,288 bytes) is not embedded in the Genesis ROM image, and no function exists to upload its tile data to VRAM. The fix is two coupled steps: embed `pc080sn.bin` in the Genesis ROM, then implement a single init-time preload function that iterates the existing `genesistan_pc080sn_tile_vram_lut`, uploading each unique mapped tile to VRAM before the first arcade tick. No format conversion is needed — the SGDK launcher tile browser (Build 91+) confirmed that raw `pc080sn.bin` bytes are VDP-native and render correctly by direct DMA. The upload loop is the only new code required.

---

## 2. Inputs Audited

| File | Status |
|------|--------|
| `docs/design/Andy_graphics_pipeline_break_diagnosis.md` | Read in full |
| `apps/rastan-direct/src/main_68k.s` | Read in full |
| `apps/rastan-direct/Makefile` | Read in full |
| `apps/rastan-direct/link.ld` | Read in full |
| `apps/rastan/src/main.c` | Read — `genesistan_preload_scene_tiles`, all `VDP_loadTileData` call sites |
| `tools/translation/precompute_pc080sn_tile_lut.py` | Read in full |
| `tools/translation/postpatch_startup_rom.py` | Read in full |
| `specs/rastan_direct_remap.json` | Read — ROM layout section |
| `AGENTS_LOG.md` | Searched for preload, tile upload, VDP_loadTileData, pc080sn |
| `build/pc080sn_tile_vram_lut.bin` | Confirmed present (32,768 bytes), `.incbin`'d in main_68k.s |

### Format Contradiction Resolved

The previous diagnosis document (`Andy_graphics_pipeline_break_diagnosis.md`, section 6) incorrectly stated that PC080SN 4bpp format requires a planar-to-chunky conversion before uploading to Genesis VRAM. This is wrong. The AGENTS_LOG documents confirmation from the SGDK launcher's tile browser (Build 91+):

> "Both PC080SN ROM data and Genesis VDP tile data use 4bpp planar encoding. No pixel format conversion is needed. Raw ROM data can be DMA'd directly into VDP VRAM and renders correctly. CONFIRMED by launcher tile browser screenshots (Build 91+)."

The pre-confirmed facts for this design task also state: "pc080sn.bin format: 16,384 tiles × 32 bytes each, 4bpp chunky, already Genesis VDP compatible. NO conversion needed." **This design adopts the confirmed no-conversion fact.** The upload function writes raw bytes from `pc080sn.bin` directly to VRAM with no transformation.

---

## 3. SGDK Reference Pipeline

### `genesistan_preload_scene_tiles` in `apps/rastan/src/main.c`

**Function signature** (line 1592):
```c
void genesistan_preload_scene_tiles(u8 scene_id)
```

**Iteration mechanism:**

1. Calls `genesistan_scene_manifest_for_id(scene_id, &manifest, &manifest_end)` to locate the correct scene preload manifest in ROM.
2. Iterates the manifest in 4-byte steps: each entry is `u16 arcade_tile` + `u16 vram_slot`.
3. Terminates when `arcade_tile == 0xFFFF`.

**Arcade tile index → VRAM slot mapping:**

The mapping is explicit in the manifest: each `(arcade_tile, vram_slot)` pair is precomputed at build time by `precompute_pc080sn_tile_lut.py`. At runtime, the function reads `vram_slot` directly from the manifest — it does not perform any runtime LUT lookup. The manifest is a pre-filtered list: only tiles actually needed for the scene are present.

**`VDP_loadTileData` call** (line 1618–1623):
```c
VDP_loadTileData(
    (const u32 *)(rastan_pc080sn + ((u32)arcade_tile * 32U)),
    vram_slot,
    1U,
    DMA
);
```
- Source: `rastan_pc080sn` base + (`arcade_tile` × 32 bytes). No conversion. Raw bytes.
- Destination: `vram_slot` (SGDK tile index, not byte address — SGDK API converts internally).
- Count: 1 tile.
- Mode: DMA.
- After the loop: `VDP_waitDMACompletion()`.

**Timing:**

- `genesistan_preload_scene_tiles(GENESISTAN_SCENE_TITLE)` is called at line 2252 during screen/scene initialization, after `VDP_clearPlane` and `genesistan_sync_title_vdp_layout()`, before `genesistan_run_title_init_sequence()` activates the arcade VBlank.
- `genesistan_preload_scene_tiles(mapped_scene_id)` is called lazily from a scene-change detection hook when a new scene is entered. It is not called every frame — only when the `source_addr` + `scene_id` combination changes (lines 1641–1650).
- **Timing classification: scene-scoped init, before first arcade tick for that scene.**

**Summary of SGDK strategy:**
- Offline tool generates compact `(tile, slot)` pair manifests, one per scene.
- Each manifest is embedded in the Genesis ROM as a ROM table.
- At scene entry, the manifest is iterated once; each tile is DMA'd directly from `rastan_pc080sn` (itself embedded in the ROM as a large array) to its assigned VRAM slot.
- No format conversion. No caching. No lazy upload. One shot per scene.

---

## 4. Tile ROM Embedding Design

### Current ROM Layout (from `link.ld` + patcher analysis)

The linker script defines two placement regions:

| ROM Region | Start | Content |
|------------|-------|---------|
| `.text.boot` | 0x000000 | Genesis boot/vector table (512 bytes) |
| `.text.wrapper` | 0x070000 | Wrapper code + rodata + data |
| `.bss` | 0xFF0000 | BSS (NOLOAD, mapped to WRAM) |

The patcher (`postpatch_startup_rom.py`) copies `maincpu.bin` (393,216 bytes = 0x60000 bytes) into ROM at offset 0x000200–0x060200:
- `whole_maincpu_copy`: `source_start = 0x000000`, `source_end_exclusive = 0x060000`, `dest_start = 0x000200`
- Result: maincpu occupies ROM bytes 0x000200–0x060200.

The wrapper sits at 0x070000. The gap between 0x060200 and 0x06FFFF (approximately 64 KB) is unused ROM. The wrapper + rodata (code + LUT binaries) is small — well under 64 KB.

**Preserved region constraint:**
The only region the patcher preserves unconditionally is the Genesis vector table at 0x000000–0x0003FF. The patcher does not touch or scan anything above 0x060200 in the rastan_direct profile. There is no `preserved_region` that overlaps the area above 0x070000.

### ROM Size Baseline

`ROM_MIN_SIZE = 0x80000` (512 KB). The patcher calls `ensure_rom_size` which pads the ROM to at least 0x80000 if the ELF output is smaller. `pc080sn.bin` is 524,288 bytes = 0x80000 bytes. A ROM containing the wrapper (0x070000–~0x078000) plus `pc080sn.bin` appended immediately after the wrapper would require a final ROM of approximately 0x070000 + wrapper_size + 0x080000 ≈ 0x0F0000 bytes (960 KB), well within the 4 MB Genesis ROM address space.

### Embedding Mechanism: `.incbin` in `.rodata`

The correct mechanism is a labeled `.incbin` directive in `main_68k.s` within the existing `.rodata` section, placed after the existing LUT `.incbin` entries:

```asm
    .align 2
genesistan_pc080sn_tile_rom:
    .incbin "../../build/regions/pc080sn.bin"
```

This places the 524,288-byte tile ROM blob in the `.rodata` section starting at 0x070000 + (code + existing rodata size). The linker resolves `genesistan_pc080sn_tile_rom` to the ROM address of the first byte, which is exactly what the preload function needs as its source base pointer.

**Why `.incbin` and not patcher append:**

- The patcher operates on a pre-built binary and has no mechanism to append large data blobs at specific addresses. It writes maincpu data and applies opcode patches, but does not embed new data regions.
- `.incbin` in the assembler source is the correct, linker-managed approach: the label becomes a known address in the symbol table, the linker places it correctly, `m68k-elf-objcopy` emits it into the binary, and the address is available at assembly time in the preload function.
- The Makefile already builds `main_68k.o` from `main_68k.s` and links with `link.ld` — no Makefile changes are required for `.incbin` to work, provided the file path is correct relative to the assembler invocation directory (`apps/rastan-direct/src/` → `../../build/regions/pc080sn.bin` is the correct relative path, matching the existing LUT `.incbin` pattern).

**Patcher preserved-region safety:**

The patcher's `preserved_genesis_vectors` block covers only 0x000000–0x0003FF. The `whole_maincpu_copy` writes 0x000200–0x060200. The wrapper and its appended `pc080sn.bin` blob sit above 0x070000. There is no patcher write, scan, or preserved-region window that touches 0x070000 or above in the rastan_direct profile. **Safe placement confirmed.**

### Makefile Size Constraint Check

The Makefile has no explicit ROM size cap. The `ensure_rom_size` in the patcher guarantees a minimum of 0x80000 but does not impose a maximum. The Genesis hardware supports up to 4 MB ROMs without a mapper. A ROM of ~960 KB (0x0F0000) is well within that range. **No constraint violated.**

---

## 5. Preload Strategy Decision

**Decision: Bulk preload all 1,067 unique tiles at init (Option A).**

**Justification:**

1. **VRAM headroom is ample.** 1,067 tiles × 32 bytes = 34,144 bytes (33.3 KB). Available tile VRAM is 48 KB. Usage is 69% of budget; 14.9 KB remains free. There is no pressure to defer.

2. **Bring-up simplicity.** A single init-time loop with no scene tracking, no scene ID state, and no lazy trigger logic is the minimal working implementation. It eliminates one entire class of potential bugs (scene detection failing to fire, lazy load racing with the first nametable commit).

3. **The SGDK reference uses scene-scoped preload due to VRAM overflow in an earlier prototype.** The AGENTS_LOG explicitly records: "Full PC080SN preload (16384 tiles) is no longer attempted. VRAM overflow status: RESOLVED by tile cache streaming." The rastan-direct target has only 1,067 unique tiles — not 16,384. Overflow is not a concern. The scene-scoped design exists to solve a problem this target does not have.

4. **Timing is safe.** The init-time preload runs with the display off (called before the main loop and before interrupts that trigger `_VINT_handler`). All 1,067 × 32 = 34,144 bytes can be written synchronously without competing with any VBlank commit path.

**Rejected: Option B (scene-scoped preload).** Would require embedding and parsing the scene preload manifests, implementing scene-change detection, and adding scene ID state — all for no VRAM benefit given the tile count fits comfortably in bulk.

---

## 6. VRAM Upload Mechanism Design

### Function Name

`init_arcade_tile_vram`

### Call Site

Called from `main_68k`, between `vdp_boot_setup` and `init_staging_state`:

```
main_68k:
    move.w  #0x2700, %sr
    bsr     vdp_boot_setup
    bsr     init_arcade_tile_vram    ← new call
    bsr     init_staging_state
    move.w  #0x2000, %sr
    ...
```

This placement guarantees:
- VDP is initialized (registers set, display off) before any tile writes.
- Tile VRAM is populated before `init_staging_state` runs. `init_staging_state` sets `tiles_dirty = 1` and `bg_row_dirty = 0xFFFFFFFF`, which will cause `vdp_commit_tiles_if_dirty` and `vdp_commit_bg_strips_if_dirty` to fire on the first VBlank. Those commits reference VRAM slots; those slots must be populated before the first frame is displayed.
- Interrupts are disabled (`#0x2700`), so no VBlank fires during the upload.

**Runs before or after `vdp_boot_setup`:** After. `vdp_boot_setup` sets VDP_REG_AUTOINC = 2 (auto-increment by 2 per word write), which is required for the write loop. It also sets display off.

### Input Iteration Strategy

Iterate the `genesistan_pc080sn_tile_vram_lut` (16,384 u16 entries). For each entry at index `i`:
- Read `vram_slot = lut[i]` (big-endian u16).
- If `vram_slot == 0`, skip (tile is unmapped; slot 0 is the transparent/unused sentinel).
- Otherwise: compute VRAM byte address = `vram_slot * 32` (note: VRAM_TILE_BASE = 0x0020 is slot 1; slot N is at byte address `N * 32`).

**Deduplication:** The LUT assigns each unique arcade tile index to a unique VRAM slot. Multiple arcade tile indices may share the same VRAM slot only if they represent the same visual tile. In the LUT as generated, each nonzero slot appears at most once for each scene's unique tile set — but across all 16,384 entries, the same slot number could appear at multiple LUT positions if the same tile is referenced by multiple arcade tile indices. However, uploading the same slot twice with identical data has no correctness impact. For bring-up, **no deduplication is required.** The loop iterates all 16,384 entries; the total upload is bounded by the number of nonzero entries × 32 bytes. With 2,326 nonzero entries (confirmed by prior audit), the total write is 2,326 × 32 = 74,432 bytes — all synchronous CPU writes, completing in well under one frame at 7.67 MHz.

**Note on slot address formula:** `VRAM_TILE_BASE = 0x00000020` is the byte address of slot 1 (the first user tile). Slot N has byte address `N × 32`. For N = 1: `1 × 32 = 32 = 0x20`. The formula `vram_slot * 32` is correct and consistent with the existing `vdp_commit_tiles_if_dirty` which writes to `VRAM_TILE_BASE` for slot 1.

### Per-Tile Operation

For each tile with nonzero `vram_slot`:
1. Compute `vram_byte_addr = vram_slot * 32` (longword multiply or shift: `vram_slot << 5`).
2. Call `vdp_set_vram_write_addr` with `vram_byte_addr` in `%d0`.
3. Load source pointer: `pc080sn_base + (arcade_tile_index * 32)` = `genesistan_pc080sn_tile_rom + (i << 5)`.
4. Write 16 words (32 bytes) to `VDP_DATA` using a counted loop. The VDP auto-increment of 2 advances the VRAM address after each word write.

### Register Allocation Sketch (for Cody's reference, not prescriptive)

- `%a0`: pointer into `genesistan_pc080sn_tile_vram_lut` (advances +2 per entry)
- `%a1`: base of `genesistan_pc080sn_tile_rom`
- `%d6`: outer loop counter (16383 down to 0, dbra)
- `%d5`: current `vram_slot` read from LUT
- `%d0`: computed VRAM byte address for `vdp_set_vram_write_addr`
- `%a2`: source tile pointer (computed each iteration)
- `%d7`: inner word counter (15 down to 0, dbra)

### Display State

`vdp_boot_setup` sets `VDP_REG_MODE2 = VDP_MODE2_DISPLAY_OFF` (0x34). `init_arcade_tile_vram` runs with display still off. Interrupts are masked (`#0x2700`). No synchronization or display bracketing is needed inside the function.

---

## 7. `staged_tile_words` / `vdp_commit_tiles_if_dirty` Coexistence

### Current role of `vdp_commit_tiles_if_dirty`

It uploads the 3 synthetic tiles (slots 1–3, 48 words) from `staged_tile_words` to VRAM at `VRAM_TILE_BASE`. It fires once on the first VBlank (because `init_staging_state` sets `tiles_dirty = 1`), then `tiles_dirty` is never set again and subsequent calls are no-ops.

### After preload is added

`init_arcade_tile_vram` will have already written the real arcade tile data to slots 20–1342 before `init_staging_state` runs. On the first VBlank, `vdp_commit_tiles_if_dirty` will write the 3 synthetic tiles to slots 1–3. These slots (1–3) do not overlap with the arcade tile range (20–1342) assigned by the LUT. **No conflict.**

### Does `vdp_commit_tiles_if_dirty` still serve a purpose?

Yes, for now. Slots 1–3 are used by the `staged_bg_buffer` checkerboard initialization in `init_staging_state` (which writes nametable entries referencing tile 1 and tile 2). The synthetic tiles provide a visible debug pattern confirming the tile commit path functions. Removing the synthetic tile infrastructure is designated as a later cleanup step in the transition plan.

### Can both coexist without conflict?

Yes. The address ranges are disjoint:
- Synthetic tiles: VRAM 0x0020–0x007F (slots 1–3)
- Arcade tiles: VRAM 0x0280–0xA7E0 (slots 20–1342)

`vdp_commit_tiles_if_dirty` fires once and becomes inert. `init_arcade_tile_vram` runs once at init with display off. No shared state, no ordering dependency after the call sequence described in Section 6.

---

## 8. Rainbow Islands Alignment Validation

| Alignment Check | Design Verdict |
|-----------------|----------------|
| 1. Tile pixel data explicitly loaded into VRAM before being referenced | PASS. `init_arcade_tile_vram` runs before `init_staging_state` which sets `bg_row_dirty = 0xFFFFFFFF` and triggers the first nametable commit. Tiles are in VRAM before any nametable entry is rendered. |
| 2. No reliance on placeholder tiles after pipeline active | PASS. Arcade VRAM slots 20–1342 are populated with real tile data. The placeholder tiles (slots 1–3) remain in slots that are not referenced by the arcade nametable path. |
| 3. Clear separation: tile upload (pixel data) vs nametable updates (layout) | PASS. `init_arcade_tile_vram` writes only tile pixel data to VRAM. `vdp_commit_bg_strips_if_dirty` writes only nametable data. These are separate functions with no shared state. |
| 4. No hidden coupling between tile upload and nametable commit | PASS. `init_arcade_tile_vram` writes directly to VDP at init time. It does not set any dirty flags or touch `staged_bg_buffer`. `vdp_commit_bg_strips_if_dirty` is unaffected. |
| 5. Genesis VDP treated as explicit memory target | PASS. The design uses `vdp_set_vram_write_addr` (existing helper) and direct writes to `VDP_DATA`. No implicit state, no SGDK DMA queue, no abstraction. The VDP is addressed as a hardware memory target with explicit address-then-data writes. |

**All five alignment checks pass.**

---

## 9. Single Root Cause

The PC080SN tile pixel ROM (`pc080sn.bin`) is never embedded in the Genesis ROM binary and no code path exists to upload its tile data to VRAM, so every VRAM slot referenced by the nametable LUT (slots 20–1342) remains zero-initialized and the VDP renders transparent tiles for all arcade tile references.

---

## 10. Single Next Correction

Embed `pc080sn.bin` in `main_68k.s` via `.incbin "../../build/regions/pc080sn.bin"` in the `.rodata` section (labeled `genesistan_pc080sn_tile_rom`), then implement `init_arcade_tile_vram` as described in Section 6: a single init-time loop that iterates all 16,384 entries of `genesistan_pc080sn_tile_vram_lut`, and for each nonzero `vram_slot`, sets the VRAM write address to `vram_slot << 5` and copies 16 words (32 raw bytes) from `genesistan_pc080sn_tile_rom + (index << 5)` to `VDP_DATA`; then call `init_arcade_tile_vram` from `main_68k` between `vdp_boot_setup` and `init_staging_state`.

---

## 11. What Must Not Be Changed Yet

- All 34 `opcode_replace` entries in `specs/rastan_direct_remap.json`
- `genesistan_hook_tilemap_plane_a` — nametable translation is correct, no changes
- `genesistan_pc080sn_tile_vram_lut` and `genesistan_pc080sn_attr_lut` — LUT values and their `.incbin` directives are correct
- `staged_bg_buffer` / `vdp_commit_bg_strips_if_dirty` — nametable staging and commit path is correct
- `_VINT_handler` structure — display-disable bracketing and commit order are correct
- `vdp_commit_tiles_if_dirty` — synthetic tile upload for slots 1–3 must remain (removal is a future cleanup step)
- `staged_tile_words` and `tile_init_words` — synthetic tile data must remain until removal is explicitly scheduled
- `init_staging_state` internal logic — the checkerboard fill and dirty flag initialization must remain unchanged; only the call site in `main_68k` gains the new `init_arcade_tile_vram` call before it
- `rom_absolute_call_relocation` configuration in `specs/rastan_direct_remap.json`
- A5 initialization to 0xFF0000
- `VRAM_TILE_BASE = 0x00000020` constant
- All existing LUT generator outputs in `build/`
- The patcher (`postpatch_startup_rom.py`) — no changes required or permitted
- The Makefile — no changes required

---

## 12. Final Verdict

The tile preload system can be implemented as a single new function (`init_arcade_tile_vram`) plus one `.incbin` directive. No format conversion is needed. No scene manifests need to be embedded or parsed. No lazy loading mechanism is required. The LUT already in ROM contains all needed `(arcade_tile_index → vram_slot)` information; the preload function iterates it once at init time, writing raw tile bytes directly to VRAM. All alignment checks against the Rainbow Islands strategy pass. The rest of the pipeline (hook, staging, commit) is correct and must not be changed. The single correction in Section 10 is the complete actionable specification.
