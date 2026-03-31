# Architecture Amendment: Block-Write Hook Without Runtime C Call

## 1. Executive Summary

This amendment removes the per-invocation C function call from the `0x5A4DE` block-write hot path. The original architecture called `genesistan_bulk_preload_check(A0)` in C on every `0x5A4DE` invocation — typically harmless but architecturally impure, placing runtime scene-detection logic inside the assembly-owned VDP commit path.

**Answer to the question under review: YES (with qualification)**

Scene preload detection CAN be moved out of the per-call C path. The hot hook becomes assembly-owned with a 2-instruction range check on the common path. The C preload function fires only on actual scene transitions (once per transition, not per invocation).

**What changed:**
- Assembly entry performs a CMP.L range check against stored scene bounds (2 instructions, ~20 cycles)
- Common path (same scene): branch taken, no C call — pure assembly
- Rare path (scene change): C call fires, loads tiles, updates range bounds
- Per-invocation C overhead eliminated: ~300 cycles/call → ~20 cycles/call on common path

**What did NOT change:**
- `0x5A4DE` hook strategy (JMP to assembly)
- Scene-scoped tile loading model
- Global LUT with cross-scene slot reuse
- No buffer, no C-window emulation
- `tile_cache_get()` elimination
- Python build-time data generation
- Three scene categories and per-scene preload manifests

---

## 2. Question Under Review

> Can scene preload detection and triggering be moved OUT of `genesistan_bulk_tilemap_commit` and attached to a cleaner scene-entry boundary, while preserving the same scene-scoped tile loading model?

### Options Evaluated

| Option | Description | Verdict |
|--------|-------------|---------|
| A | Keep C call inside hook on every invocation | Rejected — unnecessary per-call overhead |
| B | Move preload entirely to explicit scene-entry spec patches | Rejected — requires 3 additional spec patches with trampoline assembly, fragile if a transition path is missed |
| C | Assembly range check in hook + rare C fallback on scene change only | **SELECTED** |

---

## 3. Candidate Preload Trigger Points

### 3a. Explicit Scene-Entry Addresses (Option B Candidates)

The arcade state machine has clean one-shot entry points for each scene:

| Address | Scene | What It Does | One-Shot | Before First 0x5A4DE | Unique |
|---------|-------|-------------|----------|----------------------|--------|
| `0x3AA40` | Title/Attract | VDP/scroll/palette/sprite init. State `A5@(0)=0, A5@(2)=0, A5@(4)=0`. Sets `A5@(4)=1`, next frame fires block-writes. | Yes | Yes (1 frame before) | Yes |
| `0x3A5E4` | Gameplay | Level init. Sound command, geometry setup, scene-command. State `A5@(0)=2, A5@(2)=2, A5@(4)=0`. | Yes | Yes (many frames before) | Yes |
| `0x55F58` | Gameplay | Pre-HUD init. Palette DMA + counter clear. Gameplay sub-SM state 9 → sets state 0x0A. | Yes | Yes (1 state before) | Yes |
| `0x5725A` | End-Round | End-round entry point. Sets `A5@(5034)=0x0E`, `A5@(5080)=1`, `A5@(5082)=2`. Fires when round==6 boss defeated. | Yes | Yes (1 frame before) | Yes |
| `0x577CA` | Return to Gameplay | End-round completion. Clears all SM flags, sets `A5@(2)=4`. | Yes | N/A (no immediate block-write) | Yes |

**Conclusion:** Clean trigger points exist for all three scenes. Option B is architecturally valid.

### 3b. Why Option B Was Rejected

Option B requires 3 additional spec patches at `0x3AA40`, `0x3A5E4`/`0x55F58`, and `0x5725A`. Each patch must:

1. Overwrite instructions at the target address with JMP to a trampoline
2. The trampoline must: save registers, call C preload, restore registers, execute the overwritten original instructions, JMP back

This is fragile for three reasons:
- Each patch must perfectly replicate the overwritten instructions (shift budget, alignment)
- If a scene transition path is missed (e.g., an indirect jump table path not visible in linear disassembly), tiles are silently wrong with no safety net
- 3 additional spec patches + 3 trampoline assembly routines = significant implementation complexity for Cody

The self-organizing property of the hook-internal check is valuable: no matter HOW the arcade code reaches `0x5A4DE`, the scene is detected correctly.

---

## 4. Validation of Hook-Internal Preload Logic

### Is `0x5A4DE` always the first reliable point where scene identity is known?

**No.** The explicit trigger points in Section 3a prove that scene identity is known well before `0x5A4DE` fires. The arcade state machine transitions through multiple init states before the first block-write.

### Can the hook become pure assembly-only commit?

**Yes, on the common path.** The source ROM addresses (A0) per scene occupy disjoint, non-overlapping ranges:

| Scene | A0 Source Range | Size |
|-------|----------------|------|
| Gameplay | `0x56A22`–`0x570C2` | 1.7KB |
| End-Round | `0x5822A`–`0x59614` | 5.1KB |
| Title/Attract | `0x5A7DA`–`0x5B0B2` | 2.3KB |

**Gap between Gameplay and End-Round:** `0x570C2` → `0x5822A` = 4,456 bytes
**Gap between End-Round and Title:** `0x59614` → `0x5A7DA` = 4,550 bytes

These gaps are large enough that a simple A0 range check in assembly distinguishes the current scene with zero ambiguity. Two CMP.L instructions + two conditional branches replace the entire C call on the common path.

### Are there any scene transitions that would become unsafe?

**No.** The range check is self-organizing — it works regardless of which state machine path led to the `0x5A4DE` call. If A0 falls outside the stored range, the C fallback fires. This catches:
- All known transitions (title→gameplay, gameplay→end-round, end-round→gameplay, game-over→title)
- Any unknown transition paths (indirect jump tables, attract mode cycling)

---

## 5. Final Trigger Strategy Decision

### **Option C: Assembly Range Check + Rare C Fallback**

```
genesistan_bulk_tilemap_commit:
    movem.l ...                           | save registers

    | Fast scene range check (assembly-only common path)
    cmp.l   genesistan_scene_a0_hi, %a0   | A0 > scene max?
    bhi.s   .scene_changed                 | yes → rare path
    cmp.l   genesistan_scene_a0_lo, %a0   | A0 < scene min?
    blo.s   .scene_changed                 | yes → rare path
    bra.s   .scene_ok                      | within range → skip C

.scene_changed:
    | Rare path: scene transition detected
    | Call C to identify scene and preload tiles (~once per transition)
    move.l  %a0, -(%sp)
    jsr     genesistan_bulk_preload_check
    addq.l  #4, %sp

.scene_ok:
    | Pure assembly VDP commit loop (unchanged from original architecture)
    | decode A1, attr lookup, column-major loop, VDP writes
    ...
    movem.l ...                           | restore registers
    rts
```

### Common Path (Same Scene)

| Instruction | Cycles |
|-------------|--------|
| `cmp.l genesistan_scene_a0_hi, %a0` | ~12 |
| `bhi.s .scene_changed` | ~8 (not taken) |
| `cmp.l genesistan_scene_a0_lo, %a0` | ~12 |
| `blo.s .scene_changed` | ~8 (not taken) |
| `bra.s .scene_ok` | ~10 |
| **Total** | **~50 cycles** |

vs. previous design: JSR to C + table scan (~25 entries) + RTS = **~300+ cycles per call**.

The end-round animation callers fire every 10/28/26 frames. At worst, the range check adds ~50 cycles every 10 frames during animation. Completely negligible.

### Rare Path (Scene Change)

Fires once per scene transition. The C function:
1. Scans `pc080sn_source_scene_map` to identify scene from A0
2. If scene changed: calls `genesistan_preload_scene_tiles(scene_id)` — DMA loads tiles
3. Updates `genesistan_scene_a0_lo` and `genesistan_scene_a0_hi` to the new scene's range bounds
4. Updates `genesistan_current_scene_id`

### Why This Is the Right Choice

| Property | Option A (original) | Option B (explicit hooks) | **Option C (selected)** |
|----------|-------------------|-------------------------|----------------------|
| Hot path purity | C call every invocation | Pure assembly | **~Pure assembly (2 CMP + 2 branch)** |
| Self-organizing | Yes | No — must enumerate all paths | **Yes** |
| Spec patches needed | 1 (0x5A4DE) | 4 (0x5A4DE + 3 entry points) | **1 (0x5A4DE)** |
| Implementation complexity | Low | High (3 trampolines) | **Low** |
| Safety if transition missed | Always safe | Silent tile corruption | **Always safe** |
| Per-call overhead | ~300 cycles | 0 cycles | **~50 cycles** |

---

## 6. Amended Runtime Ownership

### Updated Ownership Table

| Responsibility | Owner | Location | When |
|---------------|-------|----------|------|
| Tile/slot/scene data generation | **Python** | `precompute_pc080sn_tile_lut.py` | Build time |
| `0x5A4DE` replacement (VDP commit) | **Assembly** | `genesistan_bulk_tilemap_commit` in `startup_trampoline.s` | Every `0x5A4DE` call |
| Scene range check (fast path) | **Assembly** | Inline at `genesistan_bulk_tilemap_commit` entry | Every `0x5A4DE` call — 2 CMP.L + branches |
| Scene change detection (rare path) | **C** | `genesistan_bulk_preload_check()` in `main.c` | Only when A0 falls outside current scene's range (once per scene transition) |
| Scene tile DMA preload | **C** | `genesistan_preload_scene_tiles(scene_id)` in `main.c` | On scene change (rare) |
| Scene range bounds update | **C** | Inside `genesistan_bulk_preload_check()` | On scene change — updates `genesistan_scene_a0_lo/hi` |
| Strip builder VDP commit | **Assembly** | `genesistan_asm_tilemap_commit_bg/fg` (existing) | Per-frame during gameplay scrolling |
| Strip builder C dispatch | **C** | `genesistan_hook_tilemap_plane_a/b` (existing) | Per-frame during gameplay scrolling |
| Text writer tile lookup | **C** | `text_writer_build_tile_attr()` — uses `pc080sn_tile_vram_lut[]` | Per text character rendered |
| Scroll sync | **C** | `genesistan_scroll_from_workram_vdp()` (existing, unchanged) | Per V-Int |
| Initial boot preload | **C** | `genesistan_preload_scene_tiles(SCENE_TITLE)` | Once at game launch |

### What Changed From Original Architecture

| Item | Original | Amended |
|------|----------|---------|
| Assembly entry | `JSR genesistan_bulk_preload_check` (C call every time) | 2 × CMP.L range check; C call only on range miss |
| `genesistan_bulk_preload_check()` call frequency | Every `0x5A4DE` invocation | Only on scene transitions (~3-4 times per full game) |
| New RAM variables | `genesistan_current_scene_id` only | + `genesistan_scene_a0_lo` (u32) + `genesistan_scene_a0_hi` (u32) |
| Hot path classification | Assembly + C helper | **Assembly-only** (common path) |

### Functions Modified

| Function | Change |
|----------|--------|
| `genesistan_bulk_preload_check(u32 source_addr)` | Now also updates `genesistan_scene_a0_lo` and `genesistan_scene_a0_hi` when scene changes |

### New RAM Variables

| Variable | Type | Purpose | Set By |
|----------|------|---------|--------|
| `genesistan_scene_a0_lo` | `u32` | Lowest A0 source address in current scene | C: `genesistan_bulk_preload_check()` on scene change |
| `genesistan_scene_a0_hi` | `u32` | Highest A0 source address in current scene | C: same |
| `genesistan_current_scene_id` | `u8` | Current scene ID (0=Title, 1=Gameplay, 2=End-Round) | C: same |

Initial values set by boot preload (`genesistan_preload_scene_tiles(SCENE_TITLE)`):
- `genesistan_scene_a0_lo = 0x5A7DA` (Title/Attract minimum)
- `genesistan_scene_a0_hi = 0x5B0B2` (Title/Attract maximum)
- `genesistan_current_scene_id = 0`

### Build-Time Data: Source Scene Map Extended

`pc080sn_source_scene_map` gains per-scene range bounds. The C function reads these when a scene change is detected:

| Field | Format |
|-------|--------|
| Per-entry: `(u32 addr, u8 scene_id)` | Existing — used for A0→scene lookup |
| Per-scene summary: `(u8 scene_id, u32 lo, u32 hi)` | **New** — 3 entries, used to set range bounds after preload |

The Python precompute outputs both: the per-address lookup table (for identifying which scene an unknown A0 belongs to) and the per-scene range summary (for setting the assembly fast-path bounds).

---

## 7. Amended Implementation Order for Cody

### Step 1: Python — Extend `precompute_pc080sn_tile_lut.py`

**Unchanged from original architecture**, plus one addition:

- **New:** Compute per-scene A0 source address ranges (min/max) from the scanned source tables. Output as part of `pc080sn_source_scene_map.bin` or as a separate small table.

### Step 2: C — Scene Preload Infrastructure

**Mostly unchanged from original architecture**, with these modifications:

1. Add ROM declarations in `startup_bridge.c` for per-scene preload manifests, source-scene map, **and per-scene A0 range bounds**
2. Add RAM variables: `genesistan_scene_a0_lo`, `genesistan_scene_a0_hi`, `genesistan_current_scene_id`
3. Implement `genesistan_preload_scene_tiles(u8 scene_id)` — walks manifest, DMA-loads tiles
4. Implement `genesistan_bulk_preload_check(u32 source_addr)` — scene lookup, conditional preload, **updates range bounds on scene change**
5. Replace boot preload call with `genesistan_preload_scene_tiles(SCENE_TITLE)` — **must also initialize range bounds to Title scene values**
6. Modify text writer to use static LUT (unchanged)
7. Remove `tile_cache_get()` and related arrays (unchanged)

### Step 3: Spec Patch — Add `0x5A4DE` Hook

**Unchanged from original architecture.** Still one spec patch entry:
```json
{
  "address": "0x05A4DE",
  "original": "3800 2449 32c2 32d8 5340",
  "replacement": "jmp genesistan_bulk_tilemap_commit",
  "why": "replace PC080SN block-copy engine with direct VDP translation"
}
```

No additional spec patches needed. This is a key advantage over Option B.

### Step 4: Assembly — `genesistan_bulk_tilemap_commit`

**Modified from original architecture:**

```
genesistan_bulk_tilemap_commit:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    | === SCENE RANGE CHECK (assembly-only common path) ===
    cmp.l   genesistan_scene_a0_hi, %a0
    bhi.s   .Lscene_changed
    cmp.l   genesistan_scene_a0_lo, %a0
    blo.s   .Lscene_changed
    bra.s   .Lscene_ok

.Lscene_changed:
    move.l  %a0, -(%sp)
    jsr     genesistan_bulk_preload_check
    addq.l  #4, %sp

.Lscene_ok:
    | === A1 DECODE ===
    | (unchanged: decode A1 → plane base + starting row, col)

    | === ATTR LOOKUP ===
    | (unchanged: D2 → pc080sn_attr_lut[key] → attr_partial)

    | === COLUMN-MAJOR VDP WRITE LOOP ===
    | (unchanged: outer D1 columns, inner D0 rows, LUT lookup, VDP writes)

    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts
```

**Register plan:** Unchanged from original architecture (A0 source, A2 tile LUT, A3/A5 VDP ports, D0-D7 as documented). The range check uses A0 before the loop begins and does not consume any additional registers.

### Step 5: Integration Verification

**Unchanged from original architecture.** Same 7 verification points (title screen, attract mode, text, gameplay HUD, scrolling, end-round, scene transitions).

---

## 8. Final Architecture Amendment

### Updated System Overview

```
ARCADE CODE calls 0x5A4DE with D0/D1/D2/A0/A1
    |
spec patch: JMP genesistan_bulk_tilemap_commit (assembly)
    |
assembly entry: save registers
    |
assembly: CMP.L A0 against scene range bounds
    |
    +--[within range]---> skip to VDP commit (common path, ~50 cycles)
    |
    +--[outside range]--> JSR genesistan_bulk_preload_check (C)
                              look up scene from A0
                              if scene changed:
                                  preload tiles from ROM
                                  update range bounds
                              return
    |
assembly: decode A1 → plane (BG/FG) + starting (row, col)
    |
assembly: load attr_partial from pc080sn_attr_lut[key_from_D2]
    |
assembly: column-major nested loop:
    read tile_index from (A0)+
    vram_slot = pc080sn_tile_vram_lut[tile_index & 0x3FFF]
    tile_attr = attr_partial | vram_slot
    → VDP control port (0xC00004)
    → VDP data port (0xC00000)
    |
assembly: restore registers, RTS
    |
VDP nametable updated. Tile graphics already in VRAM from preload.
```

### Hot Path Purity Statement

`genesistan_bulk_tilemap_commit` is **assembly-only on the common path**. The two CMP.L instructions and conditional branches are pure 68000 assembly executed inline. No C function is called, no stack frame is created, no register-save/restore overhead beyond what the VDP loop already requires.

The C function `genesistan_bulk_preload_check()` fires only when A0 falls outside the stored scene range — this happens exactly once per scene transition (typically 3-4 times per full game playthrough). On the recurring animation callers that fire every 10/28/26 frames during end-round, the C function is never called because A0 remains within the end-round range.

### What Remains Unchanged From the Original Architecture

- Section 3 (Hook Point, Register Contract) — unchanged except assembly entry sequence
- Section 4 (Scene Model, Per-Scene VRAM Budget) — unchanged
- Section 5 (LUT / Slot Assignment Model) — unchanged
- Section 6 (Build-Time Outputs) — minor addition of per-scene range bounds
- Section 8 (Preload Trigger mechanism) — unchanged in concept, optimized in execution
- Section 9 (Strip-Builder Coexistence) — unchanged
- Section 10 (Text Glyph / Font Interaction) — unchanged
- Section 12 (Rejected Approaches) — unchanged
- All settled architectural decisions — unchanged

### Updated Final Diagram

```
BUILD TIME (Python):
  precompute_pc080sn_tile_lut.py
    ├── scan strip builder descriptor tables (existing)
    ├── scan block-write source tables (new)
    ├── scan text glyph tile tables (new)
    ├── scene-aware slot assignment with cross-scene reuse (new)
    ├── output: pc080sn_tile_vram_lut.bin (global, 32KB)
    ├── output: pc080sn_attr_lut.bin (unchanged, 64B)
    ├── output: pc080sn_scene_preload_title.bin (new)
    ├── output: pc080sn_scene_preload_gameplay.bin (new)
    ├── output: pc080sn_scene_preload_endround.bin (new)
    └── output: pc080sn_source_scene_map.bin (new, includes per-scene A0 range bounds)

RUNTIME:
  ┌───────────────────────────────────────────────────────┐
  │  0x5A4DE → JMP genesistan_bulk_tilemap_commit         │
  │            (assembly, startup_trampoline.s)            │
  │                                                        │
  │  1. CMP.L A0 vs scene range bounds (assembly)          │
  │     → within range: SKIP to step 2 (common path)      │
  │     → outside range: JSR preload_check (C, rare)       │
  │       → identify scene, preload tiles, update bounds   │
  │                                                        │
  │  2. Decode A1 → plane + (row, col)                     │
  │  3. D2 → pc080sn_attr_lut[key] → attr_partial          │
  │  4. Column-major loop:                                 │
  │       tile = (A0)+ & 0x3FFF                            │
  │       slot = pc080sn_tile_vram_lut[tile]                │
  │       tile_attr = attr_partial | slot                   │
  │       → VDP control port (0xC00004)                     │
  │       → VDP data port (0xC00000)                        │
  │  5. RTS                                                │
  └───────────────────────────────────────────────────────┘

COEXISTENCE (unchanged):
  Block writer:  0x5A4DE → genesistan_bulk_tilemap_commit (NEW)
  Strip builder: 0x55968 → genesistan_hook_tilemap_plane_a (EXISTING)
                 0x55990 → genesistan_hook_tilemap_plane_b (EXISTING)
  Text writer:   0x3BB48 → genesistan_hook_text_writer_3bb48 (EXISTING, modified)
  Palette:       0x59AD4 → genesistan_palette_clcs (EXISTING)
  Scroll:        genesistan_scroll_from_workram_vdp (EXISTING)
  Sprites:       genesistan_sprite_tile_prepare + commit_asm (EXISTING)

One hook. One assembly function. Two C functions (preload_check + preload_scene).
Zero per-call C overhead on common path. Self-organizing scene detection.
```
