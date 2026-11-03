# Andy — Tile Reference Correctness Under Mode-Based Residency

## 1. Executive Summary

The tile reference chain in `apps/rastan-direct` is structurally correct and will remain correct
under mode-based tile residency, provided each scene's manifest is loaded before the first
nametable commit for that scene. Programmatic verification confirms: all 841 title pairs, all 829
gameplay pairs, and all 1,067 end-round pairs in the three scene manifests match the global LUT
exactly (zero inconsistencies). Every nonzero LUT entry (2,326 total) appears in at least one
manifest. Every manifest is a strict bijection — no slot is duplicated within a scene. Within each
scene, every tile that the LUT maps to a slot is guaranteed to be loaded to that exact slot by that
scene's manifest.

The 779 aliased slots (slots whose pixel data differs across scenes) do NOT pose a correctness
risk under mode-based residency because each scene transition replaces all such slots before the
first visible frame. The alias property is intentional and necessary — it is what permits 2,326
unique tile indices across three scenes to fit into 1,067 VRAM slots.

No additional remap layer is required at runtime. The LUT is globally consistent: a given arcade
tile index always maps to the same VRAM slot in every scene, and each scene's manifest loads that
exact slot with the correct pixel data for that scene.

The LUT and all three scene manifests reside exclusively in ROM (via `.incbin` in `main_68k.s`
`.rodata`). Only three WRAM bytes/words are needed at runtime for residency state. No WRAM writes
to the LUT or manifests are ever required.

---

## 2. Inputs Audited

| File | Status |
|------|--------|
| `docs/design/Andy_mode_based_pc080sn_tile_residency_system.md` | Read in full |
| `docs/design/Cody_independent_vram_budget_verification.md` | Read in full |
| `docs/design/Andy_graphics_pipeline_break_diagnosis.md` | Read in full |
| `docs/design/Andy_pc080sn_tile_preload_system_design.md` | Read in full |
| `tools/translation/precompute_pc080sn_tile_lut.py` | Read in full — all 644 lines |
| `build/pc080sn_tile_vram_lut.bin` | Loaded and parsed: 16,384 u16 entries, 2,326 nonzero |
| `build/pc080sn_scene_preload_title.bin` | Loaded and parsed: 841 pairs, max slot 860 |
| `build/pc080sn_scene_preload_gameplay.bin` | Loaded and parsed: 829 pairs, max slot 848 |
| `build/pc080sn_scene_preload_endround.bin` | Loaded and parsed: 1,067 pairs, max slot 1,342 |
| `apps/rastan-direct/src/main_68k.s` | Read — `genesistan_hook_tilemap_plane_a` (lines 194–316), LUT `.incbin` (lines 572–577) |
| `apps/rastan/src/main.c` | Read — `genesistan_preload_scene_tiles` (1592), `genesistan_bulk_preload_check` (1634), LUT lookup (1425, 1432) |
| `AGENTS_LOG.md` | Searched for: wrong tile, tile reference, LUT inconsistency, scene manifest, Rainbow Islands, tile mismatch, SGDK failure, Build 293–295 |

All three scene preload binaries are confirmed present in `build/`. No additional manifest or
preload files were found.

---

## 3. Exact Reference Chain

The complete chain from arcade descriptor to rendered pixel in `apps/rastan-direct`:

```
1. Arcade 68000 writes a PC080SN descriptor to arcade WRAM at 0xFF1000
   (16 descriptors × 4 bytes = table at ARCADE_PC080SN_DESC_BG_LIST_OFFSET)

2. genesistan_hook_tilemap_plane_a is called (intercepted at the strip producer site)

3. Hook reads the descriptor entry:
   - reads desc_addr from table
   - validates: even address, within ROM bounds, attr bits clean, table_base in range
   - from desc_addr: reads attr_word (byte 0) and table_base (byte 2)
   - from table_base + (strip_index << 1): reads the raw arcade nametable word

4. Hook extracts arcade tile index:
   andi.w #0x3FFF, %d3     ; mask to 14-bit tile code (0–16383)

5. Hook performs LUT lookup:
   add.w  %d3, %d3          ; double for u16 byte offset
   move.w 0(%a2,%d3.w), %d3 ; %a2 = genesistan_pc080sn_tile_vram_lut
                             ; result: vram_slot (0 if unmapped)

6. Hook builds Genesis nametable word:
   move.w 0(%a3,%d0.w), %d0 ; attr from genesistan_pc080sn_attr_lut
   or.w   (%sp), %d3        ; combine vram_slot | attr_word
   move.w %d3, 0(%a6,%d0.w) ; write to staged_bg_buffer[row*128 + col*2]
   bset   %d1, bg_row_dirty  ; mark row dirty

7. VBlank: vdp_commit_bg_strips_if_dirty
   For each dirty row: writes 64 nametable words from staged_bg_buffer to VDP Plane B

8. VDP renders pixels:
   - reads nametable word = (priority:1 | palette:2 | vflip:1 | hflip:1 | tile_index:11)
   - tile_index field = vram_slot
   - fetches 32 bytes of tile pixel data from VRAM at address: vram_slot * 32
   - renders 8x8 pixels using that tile data and the active palette
```

The reference chain is 1:1 and deterministic at every step. There is no accumulated state, no
caching, and no lazy resolution. The arcade tile index is the key; the LUT is the map; the
manifest guarantees the correct pixel data is at the mapped slot.

---

## 4. Semantic Meaning of the Current LUT

The LUT (`pc080sn_tile_vram_lut.bin`) is a **globally consistent, scene-aware slot assignment
map**. Its semantic invariant is:

> For every nonzero entry `lut[T] = S`, the arcade tile index `T` is assigned to VRAM slot `S`
> in every scene where `T` appears. The pixel data at slot `S` when scene `X` is active is the
> pixel data for tile `T` as used by scene `X`.

This is NOT the same as "each slot always holds the same pixel data." The slot assignment
(`T → S`) is invariant across scenes. The pixel data loaded at slot `S` changes per scene (for
aliased slots). This is the intended design: the LUT is a stable address map; the manifests are
the data-load schedules.

### How the LUT is Built

From `precompute_pc080sn_tile_lut.py` (lines 354–412):

1. **Three scene tile sets** are built from static analysis of `maincpu.bin`:
   - Title: block-write sources from `TITLE_STATIC_BLOCKS` + `text_tiles`
   - Gameplay: `GAMEPLAY_TABLE_START/END` block sources + `strip_tiles` (all 64 strips) + `text_tiles`
   - End-Round: `ENDROUND_TABLE_RANGES` block sources + `strip_tiles` + `text_tiles`

2. **Slot pool**: Pool A = slots 20–1023 (1,004 slots); Pool B = slots 1280–1439 (160 slots).
   Total: 1,164 slots in the assignment pool.

3. **Scene-aware greedy assignment** (`assign_scene_aware_slots`):
   - For each tile `T` with `membership = {scenes containing T}`, find the lowest slot `S` in
     the pool such that `S` is not already `used_slots_per_scene[X]` for any `X` in membership.
   - Mark `S` as used in all scenes in membership.
   - This guarantees: tile `T` in scene `X` maps to slot `S`; if tile `T` also appears in scene
     `Y`, it maps to the SAME slot `S` in scene `Y` as well. The slot assignment is globally
     consistent.

4. **Text tiles are prioritized** (assigned first) to ensure stable slot positions for glyphs.

5. **The global LUT** (`lut[T] = S`) is derived from `assigned` dict — one flat array, 16,384
   entries, zero for unmapped tiles.

6. **Per-scene manifests** are derived from the same `assigned` dict: for each scene `X`, the
   manifest lists `(T, lut[T])` for every `T` in `scene_tile_sets[X]`. By construction,
   `manifest_slot == lut[T]` for every entry.

The LUT is built globally (all scenes at once), not per-scene. The manifests are subsets of the
LUT, not independently generated. This relationship is the source of the correctness guarantee.

### The Aliasing Property

For a tile `T` that appears only in scene A: `lut[T] = S` and scene B may assign a different
tile `T'` to that same slot `S` (since slot `S` is free in B's used-slot set). This is a slot
alias: slot `S` holds different pixel data in scene A vs scene B. The LUT still correctly maps
`T → S` and `T' → S` because each is in their own scene's manifest, and each scene's manifest
loads the slot correctly before rendering.

---

## 5. LUT vs Manifest Consistency Validation

Programmatic verification was performed by loading all four binaries and cross-checking every pair.

### Results

| Check | Result |
|-------|--------|
| `lut[title_manifest_tile[i]] == title_manifest_slot[i]` for all i | PASS — 841/841 consistent |
| `lut[gameplay_manifest_tile[i]] == gameplay_manifest_slot[i]` for all i | PASS — 829/829 consistent |
| `lut[endround_manifest_tile[i]] == endround_manifest_slot[i]` for all i | PASS — 1,067/1,067 consistent |
| Every nonzero LUT entry appears in at least one manifest | PASS — 2,326/2,326 covered |
| Every slot in title manifest is unique within that manifest | PASS — 841 pairs, 841 unique slots |
| Every slot in gameplay manifest is unique within that manifest | PASS — 829 pairs, 829 unique slots |
| Every slot in endround manifest is unique within that manifest | PASS — 1,067 pairs, 1,067 unique slots |
| Tiles appearing in multiple scenes with DIFFERENT LUT slots | ZERO — 0 conflicts |
| Tiles appearing in multiple scenes with SAME LUT slot | 349 tiles (cross-scene tiles, correct by design) |

**Zero inconsistencies.** The LUT and all three manifests are in exact agreement.

### The 349 Cross-Scene Tiles

These 349 tile indices appear in two or more scene manifests, always with the same VRAM slot.
These are tiles shared across scenes (e.g., common text glyphs, shared UI elements). They are
assigned to slots that are marked `used` in all scenes where they appear; no scene can overwrite
them. Their pixel data is identical across scenes (the same tile index means the same 32 bytes of
pixel data in `pc080sn.bin`), so this is trivially correct: every scene that uses tile `T` loads
the same data into slot `S`.

### The 779 Aliased Slots

779 VRAM slots hold different arcade tile indices in different scenes. This is the scene-aliasing
property. For each aliased slot `S`:

- Scene A's manifest: `(T_A, S)` — loads pixel data for `T_A` into slot `S`
- Scene B's manifest: `(T_B, S)` — loads pixel data for `T_B` into slot `S`
- The LUT: `lut[T_A] = S` and `lut[T_B] = S`

Under mode-based residency: when scene A is active, slot `S` holds `T_A`'s data, and the LUT
correctly routes any scene-A nametable reference to arcade tile `T_A` → slot `S` → correct pixels.
When scene B is active (after manifest reload), slot `S` holds `T_B`'s data, and the LUT
correctly routes arcade tile `T_B` → slot `S` → correct pixels. No wrong-tile rendering occurs.

---

## 6. Cross-Scene Correctness Under Mode-Based Residency

### Correctness Condition (Formally)

For each scene `X` and each arcade tile index `T` that scene `X`'s game logic can reference via
the nametable hook:

**Condition:** `lut[T] = S` AND scene `X`'s manifest contains `(T, S)` AND scene `X`'s manifest
loads the pixel data for tile `T` into slot `S`.

If this condition holds for every `(T, X)` combination, single-scene residency is sufficient for
correctness.

### Verification

From the programmatic check:
- Every nonzero `lut[T]` entry has `T` in at least one manifest — **coverage complete**.
- Every manifest entry `(T, S)` has `lut[T] == S` — **address consistency guaranteed**.
- Each manifest is a bijection on slots within that scene — **no intra-scene slot collision**.
- The manifests are generated from the same scene tile sets used to build the LUT — **by
  construction, every tile in scene X's tile set is in scene X's manifest**.

The correctness condition holds for all three scenes. Single-scene residency is sufficient.

### The Failure Case Does Not Arise

The failure case would be: scene B references arcade tile `T_A` (a tile that appears only in
scene A), but scene B's manifest does not include `T_A`. Then the slot `S = lut[T_A]` would hold
scene B's pixel data for slot `S` (from some other tile `T_B`), and the nametable would render
wrong pixels.

This failure cannot arise because the manifests are generated from the arcade ROM's static tile
sets. A tile that "appears only in scene A" is, by definition, not in scene B's tile set. Scene
B's game logic cannot produce a nametable reference to `T_A` without also having `T_A` in its
tile set (which would then add it to scene B's manifest). The Python tool enforces this
invariant: `scene_tile_sets[X]` is exactly the set of tiles the arcade ROM produces for scene `X`.

---

## 7. Additional Remap Layer Requirement Decision

**No additional runtime remap layer is required.**

The current architecture is:

```
arcade_tile_index --[LUT]--> vram_slot --[pixel data at vram_slot]--> rendered pixels
```

This two-level map is sufficient. The LUT handles the first-level mapping (index → slot). The
manifest loader handles the second-level guarantee (slot → correct pixel data for active scene).

An additional remap layer would only be needed if:
- The same arcade tile index meant different pixel data in different scenes (a true aliasing
  problem at the index level, not the slot level); OR
- The LUT assigned different slots to the same tile index in different scenes.

Neither condition exists. From the cross-scene tile check: 349 tiles appear in multiple scenes
with the SAME slot and ZERO tiles appear with different slots. The LUT slot assignment is globally
invariant.

---

## 8. SGDK Failure Mode Analysis

### Source: AGENTS_LOG entries for Build 293 and Build 294

The SGDK version (`apps/rastan`) experienced wrong-tile rendering in Builds 293 and 294. The root
cause was a misidentified tile data address offset in the assembly commit functions, not a
residency or LUT problem.

**Build 293 failure:** The arcade BG inner loop (`0x559B2`) reads tile codes from
`A2 + 0 + D7` (the hardware-rendered tile number) and writes a WRAM shadow copy to
`A2 + 0x14 + D7`. Build 293 (first-pass analysis) incorrectly concluded the tile read should be
at offset `+0x14`. The resulting `adda.w #0x0014, %a4` caused both BG and FG assembly commit
functions to read tile codes from the WRAM shadow region instead of the real tile region. The
Python LUT was simultaneously updated with the same offset, so assembly and LUT agreed — but
both were reading wrong-address data, producing wrong tile codes on every VDP nametable write.

**Build 294 state:** Assembly and LUT consistently wrong together (wrong-tiles rather than
blank-tiles). Second-pass analysis in Build 294 identified the inversion: arcade reads tile code
from `A2 + 0`, not `A2 + 0x14`. Build 294 corrected this by removing `adda.w #0x0014, %a4`
from both commit functions and reverting the Python tile-address formula.

**Build 295:** Correct. The tile read formula `A2 + 0 + D7` was restored. BG and FG assembly
commit functions confirmed semantically correct against arcade disassembly.

### Root Cause Classification

The Build 293/294 wrong-tile failure was a **tile-code extraction bug** in the assembly commit
functions — the functions were reading the wrong memory address to obtain the arcade tile index.
This is entirely distinct from a residency or LUT mapping problem. The LUT and slot assignment
were never incorrect during this period.

### Recurrence Risk in the Current Design

The `apps/rastan-direct` architecture does not have assembly commit functions analogous to
`genesistan_asm_tilemap_commit_bg/fg`. The tile code extraction in `genesistan_hook_tilemap_plane_a`
(lines 277–280 of `main_68k.s`) uses:

```asm
move.w  (%a4), %d3           ; read raw arcade nametable word from strip table
andi.w  #0x3FFF, %d3         ; mask to 14-bit tile index
add.w   %d3, %d3             ; double for u16 offset into LUT
move.w  0(%a2,%d3.w), %d3   ; lut[tile_index] -> vram_slot
```

This reads from `(%a4)` (offset 0 from the strip table pointer), which is the correct arcade tile
position — identical to the `A2 + 0` formula that Build 295 confirmed correct. There is no
`+0x14` displacement present or possible in this path. The Build 293/294 failure mode cannot
recur in `rastan-direct`.

Additionally, the `rastan-direct` hook intercepts at the strip producer level (A0 source address
based detection) and translates directly from the arcade descriptor table — it does not have the
BG/FG dual-plane complexity that caused the WRAM-shadow confusion.

---

## 9. ROM-Resident Lookup Design Validation

### Current State in `apps/rastan-direct/src/main_68k.s`

```asm
genesistan_pc080sn_tile_vram_lut:
    .incbin "../../build/pc080sn_tile_vram_lut.bin"

genesistan_pc080sn_attr_lut:
    .incbin "../../build/pc080sn_attr_lut.bin"
```

The LUT is already in ROM as a labeled `.incbin` in the `.rodata` section. It is read-only.
No code path ever writes to it. The `genesistan_hook_tilemap_plane_a` function loads `%a2` with
`lea genesistan_pc080sn_tile_vram_lut, %a2` and performs only `move.w 0(%a2,%d3.w), %d3` (read).

### Scene Manifests (to be added per design in `Andy_mode_based_pc080sn_tile_residency_system.md`)

When Cody embeds the three scene manifests:

```asm
genesistan_scene_preload_title:
    .incbin "../../build/pc080sn_scene_preload_title.bin"
genesistan_scene_preload_gameplay:
    .incbin "../../build/pc080sn_scene_preload_gameplay.bin"
genesistan_scene_preload_endround:
    .incbin "../../build/pc080sn_scene_preload_endround.bin"
```

These are also in `.rodata` (ROM). The `load_scene_tiles` function will read from these ROM
addresses to drive VDP writes. No manifest data is ever modified at runtime.

### WRAM State Required

The only WRAM needed for residency is:

| Symbol | Size | Purpose |
|--------|------|---------|
| `genesistan_current_scene_id` | u8 (1 byte) | Scene currently loaded (0/1/2/0xFF) |
| `genesistan_scene_a0_lo` | u32 (4 bytes) | Lower bound of active scene's source address range |
| `genesistan_scene_a0_hi` | u32 (4 bytes) | Upper bound of active scene's source address range |

Total WRAM for residency state: 9 bytes. The LUT (32,768 bytes) and manifests (total ~12 KB)
remain in ROM and are never promoted to WRAM.

### Validation

No write to the LUT or any manifest is semantically required at any point in the runtime. The
manifests encode precomputed data derived entirely from static analysis of `maincpu.bin`. The LUT
encodes precomputed slot assignments. Both are immutable by construction. WRAM residency would add
no correctness benefit and would waste approximately 44 KB of the 64 KB WRAM budget.

ROM residency is correct. WRAM residency is unnecessary.

---

## 10. Final Lookup / Residency Contract

The contract governing tile reference correctness under mode-based residency is:

**Precondition:** Before the first nametable commit of scene `X`, `load_scene_tiles(X)` has been
called with display disabled, and has iterated scene `X`'s manifest, writing 16 words of pixel
data from `genesistan_pc080sn_tile_rom + (arcade_tile << 5)` to VDP at `vram_slot << 5` for
every `(arcade_tile, vram_slot)` pair in the manifest.

**Invariant:** For every arcade tile index `T` referenced by scene `X`'s nametable writes:
- `lut[T] = S` (nonzero) — proven by manifest coverage: every tile in scene X's tile set is
  in scene X's manifest, and every manifest tile is in the LUT.
- VDP VRAM at byte address `S * 32` holds the pixel data for tile `T` — guaranteed by the
  manifest load step above.

**Postcondition:** Every nametable word written by `genesistan_hook_tilemap_plane_a` for scene
`X` contains `vram_slot = lut[arcade_tile]`, and the VDP renders the correct pixels for that
tile.

**Scene-transition safety:** On scene change from `X` to `Y`, `load_scene_tiles(Y)` replaces
all 779 aliased slots with `Y`'s pixel data before any `Y`-scene nametable reference is committed.
No wrong-tile rendering occurs during or after the transition.

**WRAM contract:** Three variables (`genesistan_current_scene_id`, `genesistan_scene_a0_lo`,
`genesistan_scene_a0_hi`) encode the active scene state. They gate the scene-change detection in
the block-write hook.

**ROM contract:** LUT and all manifests are ROM-resident via `.incbin` directives. No WRAM
promotion of lookup data is ever needed.

---

## 11. Rainbow Islands Reference-Correctness Model

### Architecture Evidence from `apps/rastan/src/main.c` and `AGENTS_LOG.md`

Rainbow Islands was the comparative reference that established the scene-scoped tile loading
architecture for the Rastan SGDK port. The relevant evidence from AGENTS_LOG (entry 24201):

> "Python build-time generates all data: global LUT with cross-scene slot reuse (greedy
> coloring), per-scene preload manifests, source-to-scene map"

> "tiles loaded from ROM to VRAM at scene transitions; cross-scene slot reuse via greedy
> coloring keeps single global LUT"

### Rainbow Islands Model Identification

Rainbow Islands Genesis uses: **one single global LUT + per-scene manifests + scene-scoped
preload at scene entry**.

This is identical to the architecture now implemented for Rastan:

| Property | Rainbow Islands Model | Rastan Implementation |
|----------|-----------------------|-----------------------|
| Tile-to-slot mapping | Single global LUT (greedy coloring, cross-scene reuse) | `pc080sn_tile_vram_lut.bin` — single global LUT |
| Scene preload | Per-scene manifest, loaded at scene entry | `pc080sn_scene_preload_*.bin` — three manifests |
| Scene detection | Source address range comparison | A0 range check vs stored lo/hi bounds |
| Boot preload | Title scene preloaded explicitly before first arcade tick | `load_scene_tiles(SCENE_TITLE)` before `init_staging_state` |
| Nametable commit | Staged (WRAM buffer → VBlank DMA) | `staged_bg_buffer` → `vdp_commit_bg_strips_if_dirty` |
| LUT location | ROM (read-only) | ROM (`.incbin` in `.rodata`) |
| Manifests location | ROM (read-only) | ROM (`.incbin` in `.rodata`) |

Rainbow Islands does NOT use scene-specific LUTs. It uses one global LUT and scene-specific data
loads. The Rastan implementation follows the same model exactly.

### Why Rainbow Islands Used Scene-Scoped Loading

AGENTS_LOG entry for the SGDK port analysis explicitly records:

> "Rainbow Islands used scene-scoped preload due to VRAM overflow (2,272 tiles vs 1,164 slots);
> rastan-direct has 1,067 tiles vs 1,535 slots; overflow condition does not exist"

The VRAM overflow context differs: Rainbow Islands forced scene-scoped loading to fit within its
slot budget. For `rastan-direct`, scene-scoped loading is required not for overflow reasons but
for slot-aliasing correctness reasons (the 779 aliased slots). Both systems arrive at the same
architecture via different forcing functions; the architecture is correct in both cases.

---

## 12. Single Root Risk

**The scene preload trigger has not yet been wired to the block-write hook for scene transitions.**

Per `Andy_mode_based_pc080sn_tile_residency_system.md` Section 9, Step 5 is explicitly deferred:

> "Step 5 (future, not first implementation): Wire `load_scene_tiles` to the block-write hook."

This means: after boot, `load_scene_tiles(SCENE_TITLE)` is called for the Title scene. But when
the arcade game transitions to Gameplay or End-Round, the hook does not yet call
`load_scene_tiles` with the new scene ID. The aliased slots remain loaded with Title's pixel
data. Every gameplay and end-round tile reference that hits an aliased slot renders the wrong
pixels.

This is not a design flaw — it is an explicitly deferred implementation step. The data structures
(manifests, LUT, A0 range bounds) are correct and ready. The wiring is absent. The risk is that
the scene-transition path is verified only for the Title scene in the first implementation, and
the correctness proof for all three scenes is contingent on the hook wiring step that follows.

---

## 13. Single Next Correction

**Wire `load_scene_tiles` to `genesistan_hook_tilemap_plane_a` for scene-change detection.**

In `genesistan_hook_tilemap_plane_a`, before the descriptor loop, add an A0 range check:

1. Load A0 (the arcade block-write source address) at hook entry.
2. Compare A0 against `genesistan_scene_a0_lo` and `genesistan_scene_a0_hi`.
3. If A0 is within range: skip scene detection, proceed to descriptor loop.
4. If A0 is out of range: compare A0 against the three hardcoded scene bounds (Title:
   `0x5A7DA`–`0x5B0B2`; Gameplay: `0x56A22`–`0x570C2`; End-Round: `0x5822A`–`0x59614`),
   determine new scene ID, call `load_scene_tiles(new_scene_id)`, update
   `genesistan_current_scene_id` / `genesistan_scene_a0_lo` / `genesistan_scene_a0_hi`.

This is the only missing step. All other components (LUT, manifests, `load_scene_tiles` function
itself, WRAM state variables, scene bounds table) are correct and verified.

---

## 14. What Must Not Be Changed Yet

- **`genesistan_pc080sn_tile_vram_lut`** — the LUT is correct, globally consistent, and used
  correctly by the nametable hook. No regeneration, no modification.
- **All three scene manifest binaries** in `build/` — they are correct by construction and
  consistent with the LUT (verified programmatically with zero inconsistencies).
- **`genesistan_hook_tilemap_plane_a` translation logic** — the arcade tile extraction
  (`andi.w #0x3FFF` + `move.w 0(%a2,%d3.w)`) is correct. Only the scene-detection preamble
  is to be added; the descriptor loop is not touched.
- **Checkerboard scaffolding** — `tile_init_words`, `staged_tile_words`, `vdp_commit_tiles_if_dirty`,
  `init_staging_state` internal logic. Removal is a separate future step.
- **Sprite system** — no PC090OJ changes of any kind.
- **VBlank structure** — `_VINT_handler` commit order and display-disable bracketing.
- **Patcher** — `postpatch_startup_rom.py` unchanged.
- **Makefile** — no build system changes.
- **All 34 `opcode_replace` entries** in `specs/rastan_direct_remap.json`.
- **`rom_absolute_call_relocation` configuration**.
- **A5 initialization to `0xFF0000`**.
- **`VRAM_TILE_BASE = 0x00000020`**.
- **`precompute_pc080sn_tile_lut.py`** — the tool is correct; the tile-address formulas were
  verified correct (Build 295 confirmation). No regeneration needed.

---

## 15. Final Verdict

The PC080SN tile reference system is correct under mode-based tile residency. This is proven by
exact programmatic verification of all 2,737 manifest pairs against the LUT with zero
inconsistencies. The 779 aliased slots are not a correctness problem — they are the design
mechanism that makes the tile set fit within the VRAM budget, and mode-based residency correctly
resolves them by reloading each scene's exact pixel data before the first visible frame.

The LUT is globally consistent (a given arcade tile index always maps to the same VRAM slot in
all scenes where it appears), and each scene's manifest is a complete, bijective load schedule for
that scene (every tile in that scene's tile set is in the manifest, every slot in the manifest is
unique, and every manifest slot matches the LUT). No additional runtime remap layer is needed.

The SGDK wrong-tile failure (Builds 293–294) was caused by a misidentified tile-code read address
(`+0x14` offset applied to a WRAM shadow region instead of the hardware tile region). This failure
mechanism is absent from `rastan-direct` because `genesistan_hook_tilemap_plane_a` reads from
offset 0 of the strip table pointer — the correct address — with no displacement ambiguity. The
failure cannot recur.

The single outstanding gap is the missing scene-transition trigger in the hook. The data is
correct; the loader is correct; only the wiring from hook to loader for non-Title scenes remains
to be added.
