# Arcade-Owned Graphics Replacement Design

## 1. Executive Summary

The current VBlank path has **confirmed duplicate ownership** across all three major graphics systems: scroll, palette, and sprites. Each system has both a C-side path in the VBlank callback AND an opcode-replace or assembly path that fires during the arcade tick within the same frame. This creates per-frame register contention — the same hardware registers (VDP scroll, CRAM, SAT) are written by two competing owners every frame.

The design eliminates all C-side graphics paths from the VBlank callback, leaving only the arcade-tick-driven opcode hooks and assembly routines as the single owners. Five C functions are removed from the per-frame path. The VBlank callback becomes logic-only (inputs, arcade tick, workram sanitize) with no direct graphics writes.

## 2. Confirmed Duplicate/Conflicting Ownership

### A. Scroll — DUPLICATE: YES

**Path 1 (opcode hook, during arcade tick):**
- `genesistan_scroll_from_workram_vdp()` is the replacement target for **10 opcode_replace entries**:
  - 0x03ABBA, 0x03ABC0 (legacy scroll clear)
  - 0x03B098, 0x03B09E (startup scroll clear)
  - 0x055AB4, 0x055ABC, 0x055AC4, 0x055ACC (runtime PC080SN scroll writes, shift_replacements)
  - 0x00016A, 0x000170 (boot scroll setup, shift_replacements)
- These execute during `genesistan_run_original_frontend_tick()` whenever the arcade code reaches a scroll write site.

**Path 2 (C, post-tick in VBlank callback):**
- `sync_arcade_scroll_to_vdp()` → `genesistan_scroll_from_workram_vdp()` at main.c:2116
- Calls the **exact same function** a second time after the arcade tick has already called it via opcode hooks.

**Conflict:** VDP scroll registers (BG_A H/V, BG_B H/V) are written at least twice per frame. If the arcade tick's scroll writes set values that are then overwritten by the C path reading stale or intermediate workram values, the result is flicker or jitter — the display briefly shows one scroll position then snaps to another.

**Resolution:** Remove `sync_arcade_scroll_to_vdp()` from the VBlank callback. The opcode hooks are the correct single owner.

### B. Palette — DUPLICATE: YES

**Path 1 (arcade write, captured to CLCS buffer):**
- The arcade palette converter at 0x059AD4 writes converted palette values to address 0x200000, which is rewritten to `genesistan_palette_clcs` by the absolute_rewrite system.
- This fires during `genesistan_run_original_frontend_tick()` whenever the arcade code runs its palette path.

**Path 2 (C, post-tick, `load_arcade_palette()`):**
- Scans `genesistan_palette_clcs` for the first non-zero 64-entry block.
- Overwrites ALL 64 CRAM entries via DMA.

**Path 3 (C, post-tick, `refresh_frontend_sprite_palettes()`):**
- Re-applies all 64 CRAM entries per-color using PAL_setColor.
- Exists because `load_arcade_palette()` clobbers sprite palette lines.

**Conflict:** CRAM is written 2-3 times per frame. `load_arcade_palette()` uses a scanning heuristic that may select the wrong 64-color block. Then `refresh_frontend_sprite_palettes()` overwrites palette lines again. The arcade's own palette capture is authoritative but is being overridden by C code that second-guesses which block to use.

**Resolution:** Replace both C palette functions with a single assembly routine that reads the palette CLCS buffer directly and writes only the relevant CRAM entries. No scanning heuristic — use the known 64-entry capture window (offset 0 in `genesistan_palette_clcs`).

### C. Sprites — DUPLICATE: YES (TRIPLE)

**Path 1 (opcode hook, during arcade tick):**
- `genesistan_render_sprites_vdp()` at main.c:1773 is called via `genesistan_render_sprites_vdp_bridge` (opcode_replace at 0x03A8E4).
- Does: tile DMA to VRAM, SAT attribute writes via SGDK, palette bank mapping.

**Path 2 (C, post-tick, `genesistan_sprite_tile_prepare()`):**
- Reads the same Block-A (0xE0FF11FE) sprite entries.
- DMAs tile data to VRAM for up to 18 unique codes.
- Builds LUT tables.

**Path 3 (ASM, post-tick, `genesistan_sprite_commit_asm()`):**
- Reads Block-A and the LUTs from Path 2.
- Writes SAT entries to VDP data port at VRAM 0xF800.

**Conflict:** Sprite tile data is DMA'd twice (Path 1 + Path 2) to potentially different VRAM regions. SAT is written twice (Path 1 + Path 3) with potentially different attribute values. The two pipelines read the same source data but build independent state, creating torn frames where some sprites use Path 1's tiles and others use Path 3's tiles.

**Resolution:** Keep only the opcode-hook path (Path 1: `genesistan_render_sprites_vdp_bridge`). Remove both C/ASM post-tick paths. The opcode hook runs at the correct arcade timing and builds a complete, coherent sprite frame.

### D. Tilemap/Text — NO DUPLICATE

The text writers (`genesistan_hook_text_writer_3bb48_impl`, `genesistan_hook_text_writer_3c3fe`) and bulk tilemap commit (`genesistan_bulk_tilemap_commit`) are called only from opcode_replace hooks during the arcade tick. No competing C path writes to the same nametable addresses post-tick.

**Status:** Single ownership. No change needed.

## 3. Per-System Final Ownership Model

### A. Palette

| Aspect | Design |
|--------|--------|
| **Owner** | New assembly routine `genesistan_palette_commit_asm`, called once from VBlank callback post-tick |
| **Source** | `genesistan_palette_clcs[0..63]` — the first 64 entries, which is the authoritative capture window |
| **Conversion** | CLCS xRGB-444 → Genesis 0BBB0GGG0RRR0 in assembly |
| **Target** | CRAM via VDP data port (set VDP write address to CRAM 0x0000, stream 64 words) |
| **Partial updates** | Not needed — the capture window always contains the full 64-entry palette state |
| **Fallback** | If all 64 entries are zero (no palette captured yet), write from `genesistan_palette_rom_table` |
| **Eliminated** | `load_arcade_palette()` (removed), `refresh_frontend_sprite_palettes()` (removed) |
| **No full-CRAM overwrite heuristic** | Confirmed — reads exactly entries 0-63 from CLCS, no scanning |

### B. Scroll

| Aspect | Design |
|--------|--------|
| **Owner** | Opcode hooks only — the 10 existing `genesistan_scroll_from_workram_vdp` replacements |
| **Execution** | During arcade tick via `genesistan_run_original_frontend_tick()` |
| **Eliminated** | `sync_arcade_scroll_to_vdp()` (removed from VBlank callback) |
| **Single path** | Confirmed — scroll registers written only from opcode hooks |

### C. Sprite System

| Aspect | Design |
|--------|--------|
| **Tile upload owner** | `genesistan_render_sprites_vdp()` via opcode_replace bridge at 0x03A8E4 |
| **SAT commit owner** | `genesistan_render_sprites_vdp()` via opcode_replace bridge at 0x03A8E4 |
| **Palette** | Handled by the unified palette commit (palette lines are set correctly by CLCS capture) |
| **Eliminated** | `genesistan_sprite_tile_prepare()` (removed), `genesistan_sprite_commit_asm()` (removed from VBlank callback) |
| **Consolidation** | The opcode-hook path is already a complete sprite pipeline (tile DMA + SAT write). Post-tick C/ASM paths are redundant and are fully removed. |

### D. Tilemap / Text

| Aspect | Design |
|--------|--------|
| **Owner** | Existing opcode hooks: `genesistan_hook_text_writer_3bb48`, `genesistan_hook_text_writer_3c3fe`, `genesistan_bulk_tilemap_commit`, `genesistan_asm_tilemap_commit_bg/fg`, `genesistan_hook_tilemap_plane_a/b` |
| **No competing C path** | Confirmed |
| **Change** | None needed |

## 4. C Functions To Remove/Bypass

| Function | Action | Reason |
|----------|--------|--------|
| `load_arcade_palette()` | **REMOVE** from VBlank callback | Replaced by `genesistan_palette_commit_asm` |
| `sync_arcade_scroll_to_vdp()` | **REMOVE** from VBlank callback | Duplicate of opcode hooks that already fire during arcade tick |
| `genesistan_sprite_tile_prepare()` | **REMOVE** from VBlank callback | Duplicate of `genesistan_render_sprites_vdp` opcode hook |
| `refresh_frontend_sprite_palettes()` | **REMOVE** from VBlank callback | Compensatory — exists only because `load_arcade_palette` clobbers palette. With unified palette commit, no longer needed. |
| `genesistan_sprite_commit_asm()` | **REMOVE** from VBlank callback | Duplicate SAT commit — `genesistan_render_sprites_vdp` already writes SAT |

**VBlank callback after changes:**
```c
static void genesistan_frontend_live_vint_handoff(void)
{
    if (!frontend_live_handoff_active || (current_screen != SCREEN_FRONTEND_LIVE))
        return;

    genesistan_refresh_arcade_inputs();        /* logic: input shadow regs */
    genesistan_run_original_frontend_tick();    /* arcade tick: all graphics via opcode hooks */
    sanitize_arcade_workram();                  /* logic: stability sanitize */
    genesistan_palette_commit_asm();            /* NEW: single palette owner, assembly */
}
```

Only 4 calls remain. Three are logic/state. One is the new assembly palette commit (the only graphics write that cannot be handled by an opcode hook, because the arcade palette write goes to CLCS capture RAM, not directly to CRAM — a final CLCS→CRAM transfer is needed).

## 5. Assembly/Opcode Replacement Plan

### 5.1 New: `genesistan_palette_commit_asm` (Assembly)

**Location:** `startup_trampoline.s`, new function
**Called from:** VBlank callback, after arcade tick
**Inputs:** `genesistan_palette_clcs` (64 × u16), `genesistan_palette_rom_table` (64 × u16 fallback)
**Output:** CRAM entries 0-63

**Algorithm:**
1. Check if `genesistan_palette_clcs[0]` is non-zero (palette captured)
2. If not captured, use `genesistan_palette_rom_table` as source
3. Set VDP write address to CRAM offset 0 (`move.l #0xC0000000, (0xC00004)`)
4. Loop 64 entries:
   - Read u16 from source
   - Convert: `genesis = ((raw >> 1) & 0x000E) | ((raw >> 2) & 0x00E0) | ((raw >> 3) & 0x0E00)`
   - Write to VDP data port
5. Return

**Why assembly:** Runs inside VBlank. Must be fast. Conversion is bit-shift-heavy — perfect for 68000 assembly. No SGDK API calls needed.

### 5.2 Existing: Scroll (No Change)

Already fully owned by opcode hooks. Just remove the C duplicate call.

### 5.3 Existing: Sprites (No Change to Hook)

`genesistan_render_sprites_vdp_bridge` at 0x03A8E4 is already the complete sprite pipeline. Just remove the C/ASM post-tick duplicates.

### 5.4 Existing: Tilemap/Text (No Change)

Already fully owned by opcode hooks.

## 6. Comparison to Rainbow Islands / Cadash Approach

### Rainbow Islands Pattern

From the analysis document:
- **Arcade:** CPU writes chip-mapped windows (PC080SN at 0xC00000, PC090OJ at 0xD00000, palette at 0x200000). Graphics hardware renders from those windows.
- **Genesis:** Direct VDP port ownership. Helper routines compute VDP command targets and stream words. WRAM staging then upload to VDP.
- **Key pattern:** "Intent-to-owner mapping" — each arcade chip-window write intent is translated to exactly one Genesis VDP output primitive. No duplication.

**Rastan alignment:** This design follows the same pattern. Each arcade write intent (scroll, palette, sprite, tilemap) maps to exactly one Genesis output path:
- Scroll writes → opcode hooks → `genesistan_scroll_from_workram_vdp()` → VDP scroll registers
- Palette writes → opcode rewrite to CLCS capture → `genesistan_palette_commit_asm()` → CRAM
- Sprite writes → opcode hook → `genesistan_render_sprites_vdp_bridge` → VRAM + SAT
- Tilemap writes → opcode hooks → assembly commit routines → VDP nametable

### Cadash Pattern

From the analysis document:
- **Key lesson:** "Formalize a small set of shared VDP output primitives (command-setup, tile/plane stream write, SAT emit, CRAM load, scroll write, clear/fill) and map arcade intents to those primitives with explicit producer→consumer ownership validation."
- **Anti-pattern:** "Do not regress into per-screen fake rendering hacks instead of intent-based translation."

**Rastan alignment:** The current C-side `load_arcade_palette()` with its block-scanning heuristic is exactly the "per-screen fake rendering hack" Cadash warns against. It doesn't translate arcade intent — it scans a buffer and guesses. The replacement (`genesistan_palette_commit_asm`) is a proper VDP output primitive that receives the arcade's authoritative palette capture and streams it to CRAM.

### What Both Ports Prove

Both Rainbow Islands and Cadash Genesis ports use:
1. **Single owner per VDP resource** — no register is written by two systems
2. **No C-side polling/scanning of shared buffers** — producers write, consumers transfer
3. **Assembly or direct VDP sequences** for all hot-path graphics operations
4. **WRAM staging → VDP transfer** model, not scan-and-overwrite

This design achieves all four properties.

## 7. No-Duplicate-Ownership Verification

| VDP Resource | Writer After Design | Duplicate? |
|-------------|---------------------|------------|
| Scroll H BG_A | `genesistan_scroll_from_workram_vdp()` via opcode hooks only | NO — C path removed |
| Scroll V BG_A | Same | NO |
| Scroll H BG_B | Same | NO |
| Scroll V BG_B | Same | NO |
| CRAM entries 0-63 | `genesistan_palette_commit_asm()` once per frame | NO — both C palette functions removed |
| VRAM sprite tiles | `genesistan_render_sprites_vdp()` via opcode hook only | NO — C tile prepare removed |
| SAT (0xF800) | `genesistan_render_sprites_vdp()` via opcode hook only | NO — ASM sprite commit removed |
| Nametable BG_A | Opcode hooks (text writers + bulk_tilemap_commit + tilemap_fg) | NO — no competing path |
| Nametable BG_B | Opcode hooks (tilemap_bg + bulk_tilemap_commit) | NO — no competing path |
| VDP display registers | One-shot init only (`restore_launcher_vdp_state`, `sync_title_vdp_layout`) | NO — no per-frame contention |

**Verification: PASS — no VDP resource has two writers per frame.**

## 8. Final Design Verdict

The root cause of flicker, vertical noise, and unstable rendering is **confirmed duplicate ownership** across all three major graphics systems:

- **Scroll:** Written twice per frame (opcode hooks + C callback). Causes jitter.
- **Palette:** Written 2-3 times per frame (CLCS capture + C scan-overwrite + C sprite palette re-apply). Causes wrong colors and invisible text.
- **Sprites:** Tile DMA'd twice, SAT written twice (opcode hook + C prepare + ASM commit). Causes torn/flickering sprites.

The fix is architectural: **remove all 5 C-owned per-frame graphics functions** from the VBlank callback, leaving only:
1. Input refresh (logic)
2. Arcade tick (all graphics via existing opcode hooks)
3. Workram sanitize (logic)
4. New `genesistan_palette_commit_asm` (single CLCS→CRAM transfer)

This achieves the Rainbow Islands / Cadash pattern: one owner per VDP resource, arcade-driven execution flow, assembly output primitives, no C-side rendering heuristics.
