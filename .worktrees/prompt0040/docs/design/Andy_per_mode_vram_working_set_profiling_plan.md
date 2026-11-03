# Andy — Per-Mode VRAM Working Set Profiling Plan

## 1. Executive Summary

The question under review is whether bulk-preloading all PC080SN tiles at boot exhausts VRAM headroom needed for PC090OJ sprite tile streaming. The VRAM math, computed from confirmed file sizes and known tile counts, answers the question definitively:

- PC080SN bulk preload occupies slots 0–1342 (42.0 KB of the 48.0 KB tile region).
- After bulk preload, slots 1343–1535 remain: 192 eight-by-eight slots = 48 sixteen-by-sixteen sprite cells.
- The confirmed worst-case concurrent sprite working set is 18 unique 16×16 cells (Block-A = 18 codes from AGENTS_LOG), requiring 72 eight-by-eight VRAM slots (2.25 KB).
- 48 available cells minus 18 worst-case cells = 30 cells headroom. Budget passes.

The bulk preload strategy is not wrong in absolute VRAM terms. However, it carries two conditions that are not yet implemented in rastan-direct: (1) the sprite tile base address must be 1343, not 1024 (1024–1342 is occupied by PC080SN tiles after bulk preload), and (2) no per-mode profiling of the actual PC080SN working set has been performed. The SGDK-version's scene-scoped model knows each mode's actual tile set; rastan-direct's bulk approach assumes all 1,067 tiles must coexist at all times — which may be correct but has not been measured.

The profiling plan defined in this document will resolve the open empirical question: does any individual game mode actually need all 1,067 PC080SN tile slots simultaneously, or is the per-mode working set substantially smaller? If per-mode sets are smaller, mode-scoped preload would free ~20 KB of tile VRAM that could serve as a larger sprite streaming buffer or eliminate the sprite base address constraint entirely.

The single root concern is the unmeasured per-mode PC080SN working set: the bulk preload may permanently occupy VRAM that no single mode ever uses simultaneously, limiting sprite streaming headroom to 192 slots when larger reserves may be achievable with minimal scene-scoped discipline.

---

## 2. Inputs Audited

| File | Status | Key Facts Extracted |
|------|--------|-------------------|
| `docs/design/Andy_graphics_pipeline_break_diagnosis.md` | Read in full | LUT has 2,326 nonzero entries mapping to 1,067 unique slots 20–1342; no tile pixel data in VRAM |
| `docs/design/Andy_pc080sn_tile_preload_system_design.md` | Read in full | Bulk preload chosen; 1,067 tiles × 32 bytes = 33.3 KB; VRAM headroom stated as 14.9 KB (before sprite consideration) |
| `docs/design/final_block_write_and_scene_scoped_tile_loading_architecture.md` | Read in full | Scene model: Title/Attract 823 slots, Gameplay 817, End-Round 1,055; pool was 1,164 slots (20–1023 + 1,280–1,439); this used SGDK, not rastan-direct |
| `docs/design/final_block_write_and_scene_scoped_tile_loading_architecture_amendment.md` | Read in full | Assembly range-check optimization for scene detection; scene A0 ranges defined |
| `docs/design/rainbow_islands_vs_rastan_vdp_vram_buffering_comparative_trace.md` | Read in full | Rainbow Islands used scene-scoped preload driven by mode transitions; sprites DMA'd from SAT staging |
| `apps/rastan-direct/src/main_68k.s` | Read for hook points | `genesistan_hook_tilemap_plane_a` writes VRAM slots via `genesistan_pc080sn_tile_vram_lut`; `bg_row_dirty` bitmask tracks dirty rows |
| `apps/rastan/src/main.c` | Read for sprite layout | `FRONTEND_RUNTIME_SPRITE_TILE_BASE = 1024`; `genesistan_sprite_tile_lut[18]`; `PC090OJ_CELL_COUNT = 524288 / 128 = 4096` |
| `build/pc080sn_tile_vram_lut.bin` | Analyzed (Python) | 16,384 u16 entries; 2,326 nonzero; 1,067 unique slots; min slot = 20; max slot = 1,342 |
| `build/regions/pc090oj.bin` | Size checked | 524,288 bytes = 4,096 unique 16×16 sprite cells = 16,384 eight-by-eight tiles |
| `AGENTS_LOG.md` | Searched for VRAM budget, PC090OJ, working set | Block-A = 18 entries; Block-B = 4 entries; sprite tile LUT covers 18 unique codes; sprite VRAM at 1024+ in SGDK; 480 sprite slot init loop confirmed |

---

## 3. Mode / Scene Model

Rastan has three distinct visual contexts, each with a distinct PC080SN tile working set. These are established by the SGDK version's scene manifest and confirmed by disassembly of the arcade state machine.

| Scene ID | Name | Block-Write Source Addresses | Strip Builder Active | Notes |
|----------|------|------------------------------|---------------------|-------|
| 0 | Title / Attract | `0x5A7DA`–`0x5B0B2` (5 tables) | No | Includes attract cycling: insert coin, stage intro, game over panels |
| 1 | Gameplay | `0x56A22`–`0x570C2` (6 stage HUDs, one per stage) | Yes | Gameplay scrolling; strip builder fires per-frame during active play |
| 2 | End-Round | `0x5822A`–`0x59614` (quadrant fill + animation frames) | Yes (during transition) | Stage clear sequence; animated sprite overlays from PC090OJ |

Distinct visual sub-modes that are NOT separate tile sets:
- Attract cycling (insert coin / game over / stage intro) uses source addresses all within Title/Attract range. Same scene ID.
- Stage 1–6 use different block-write source tables but these are within the Gameplay source range.

The SGDK version's validated scene tile counts are the best available estimate for per-mode working set until profiling is run on rastan-direct:
- Title/Attract: 781 block tiles + 42 text glyphs = 823 unique tiles
- Gameplay: 492 block tiles + 289 strip tiles + 42 text = 817 unique tiles
- End-Round: 727 block tiles + 289 strip tiles + 42 text = 1,055 unique tiles

These three sets are NOT identical. Cross-scene reuse exists but has not been quantified for the rastan-direct version. The global union (1,067 unique slots in the current LUT) is the current rastan-direct assumption.

---

## 4. PC080SN Profiling Target

### What Must Be Measured

For each of the three scene buckets, measure: how many unique VRAM slots are actually written by `genesistan_hook_tilemap_plane_a` during a full traversal of that scene?

### Specific Targets

| Metric | Value to Determine |
|--------|-------------------|
| Per-scene unique slot count | How many of the 1,067 LUT-assigned slots are referenced in each mode |
| Cross-scene slot overlap | Which slots appear in multiple scenes (these must be retained in any mode-scoped scheme) |
| Scene-exclusive slots | Slots used only in one scene (candidates for reuse if mode-scoped preload is adopted) |
| Whether any single mode uses all 1,067 slots | If yes, bulk preload is unavoidable; if no, mode-scoped is feasible |

### Estimated Per-Mode Working Set (from SGDK data, rastan-direct unverified)

| Scene | Estimated Unique PC080SN Tiles | Fraction of 1,067 |
|-------|--------------------------------|-------------------|
| Title/Attract | ~780–820 | ~75% |
| Gameplay | ~820–840 | ~77–79% |
| End-Round | ~1,000–1,060 | ~94–99% |

No single scene uses all 1,067 tiles based on the SGDK data. End-Round is the most demanding at ~99% of the global set. If this holds in rastan-direct, mode-scoped preload would yield only minimal savings (~7 slots in End-Round). The profiling run will confirm or refute this.

---

## 5. PC090OJ Profiling Target

### File Facts

| Fact | Value | Source |
|------|-------|--------|
| pc090oj.bin size | 524,288 bytes | `wc -c build/regions/pc090oj.bin` |
| Total 16×16 sprite cells in ROM | 4,096 | 524,288 ÷ 128 bytes/cell |
| Total 8×8 tiles in ROM | 16,384 | 524,288 ÷ 32 bytes/tile |
| Each 16×16 cell | 128 bytes = 4 VRAM slots (8×8 tiles) | PC090OJ format: four 8×8 planes per cell |

### Worst-Case Concurrent Working Set

| Metric | Value | Source |
|--------|-------|--------|
| Block-A sprite entries per frame | 18 | AGENTS_LOG: `genesistan_sprite_tile_lut[18]`, Block-A confirmed |
| Block-B sprite entries per frame | 4 | AGENTS_LOG: explicit |
| Maximum active sprite instances | 22 | Block-A + Block-B |
| Confirmed max unique 16×16 codes per frame | 18 | `genesistan_sprite_tile_lut[18]` in main.c is the dedup structure |
| Conservative worst-case (boss + enemies) | 32 | Estimated — not yet measured at runtime |
| VRAM slots for 18 unique cells | 72 | 18 × 4 |
| VRAM slots for 32 unique cells | 128 | 32 × 4 |

The confirmed in-code limit of 18 unique tiles per frame is the primary design constraint. The 32-cell figure is a conservative over-estimate to guard against undiscovered sprite combinations in boss fights.

### What Must Be Measured

1. Maximum unique 16×16 sprite cell codes observed simultaneously across all game modes (title, gameplay stages 1–6, boss fights, end-round).
2. Whether any game mode uses more than 18 unique codes per frame (which would indicate the LUT is undersized).
3. Total unique PC090OJ cell codes across the entire game (subset of 4,096) — establishes whether a permanent "all sprite tiles" preload is feasible.

---

## 6. Profiling Method

### PC080SN Per-Mode Profiling

**Hook point:** `genesistan_hook_tilemap_plane_a` in `apps/rastan-direct/src/main_68k.s`.

This hook already reads each arcade tile index and looks it up in `genesistan_pc080sn_tile_vram_lut` to get the VRAM slot. The exact instruction at the lookup is:

```asm
move.w  0(%a2,%d3.w), %d3    ; a2 = genesistan_pc080sn_tile_vram_lut
```

**Instrumentation mechanism:** A 1,535-bit WRAM bitmask (`genesistan_tile_slot_observed[192 bytes]`) can be inserted into the BSS. At the lookup point, after reading `%d3` (the VRAM slot), set bit `%d3` in the bitmask. After a full scene traversal (one complete pass through all visible tilemap regions), count the set bits in the bitmask.

**Mode separation:** Read the arcade state machine mode register at A5+0 (game mode) and A5+2 (sub-mode) at the entry of the hook to partition observations by scene. Three separate bitmasks (one per scene bucket) allow per-scene unique slot counts to be computed offline.

**Output artifact:** A 3 × 192-byte = 576-byte WRAM dump captured via emulator memory inspection, or a serial log if a debug output channel exists. The dump directly encodes which VRAM slots were accessed in each mode.

**Minimum observation window:** One complete traversal of the visible tilemap (all 32 rows × 64 columns = 2,048 tiles) per scene, repeated across at least one full attract cycle for Title/Attract and at least one stage of gameplay plus one boss fight for Gameplay and End-Round.

### PC090OJ Per-Mode Profiling

**Hook point:** The sprite tile prepare function (`genesistan_sprite_tile_prepare` / `init_arcade_tile_vram` equivalent for sprites).

At the point where a PC090OJ cell code is looked up, record the code in a 4,096-bit WRAM bitmask (`genesistan_sprite_cell_observed[512 bytes]`).

Separately, maintain a per-frame peak counter tracking how many unique codes appeared in a single frame (to confirm or revise the 18-unique-cell assumption).

**Output artifact:** 512-byte WRAM dump encoding all observed PC090OJ cell codes across all game modes. Peak per-frame unique count (u16 in WRAM).

### What Cody Must Instrument (summary for prompt author)

The profiling requires exactly two instrumentation additions to `main_68k.s`:

1. After the `move.w 0(%a2,%d3.w), %d3` LUT lookup in `genesistan_hook_tilemap_plane_a`: add a bit-set operation against `genesistan_tile_slot_observed_[scene_id]` using `%d3` as the bit index.

2. In the sprite tile DMA path: add a bit-set against `genesistan_sprite_cell_observed` using the sprite cell code as the bit index; update `genesistan_sprite_peak_unique` if current frame count exceeds stored peak.

Both additions are non-destructive observational writes. Neither changes any VRAM, nametable, or SAT state.

---

## 7. VRAM Budget Decision Rule

### VRAM Layout Reference

| Region | Address Range | Size | Slots |
|--------|---------------|------|-------|
| Tile VRAM (usable) | 0x0020–0xBFFF | 49,120 bytes = 48.0 KB | 1,535 |
| Plane B nametable | 0xC000–0xDFFF | 8 KB | — |
| Plane A nametable | 0xE000–0xF7FF | 6 KB | — |
| SAT | 0xF800–0xFBFF | 1 KB | — |
| HScroll table | 0xFC00–0xFFFF | 1 KB | — |

### Decision Rule

Let:
- **T_mode** = maximum unique PC080SN tile slots required by any single game mode (measured by profiler)
- **S_peak** = maximum unique PC090OJ 16×16 cells required simultaneously in any frame (measured by profiler, expressed as 8×8 VRAM slots: S_peak_slots = S_peak × 4)
- **VRAM_tile_total** = 1,535 slots

**PASS condition (bulk preload is safe):**

```
T_mode + S_peak_slots ≤ 1,535
```

Using confirmed numbers: T_mode = 1,067 (bulk preload uses all modes' union), S_peak_slots = 18 × 4 = 72.

```
1,067 + 72 = 1,139 ≤ 1,535   →   PASS, margin = 396 slots (12.7 KB)
```

**BUT**: Bulk preload places PC080SN tiles in slots 0–1342. Sprites cannot occupy slots 0–1342 after bulk preload. So the effective constraint is:

```
Sprite slots used ≤ 1,535 − 1,342 = 193
S_peak_slots ≤ 193
72 ≤ 193   →   PASS, margin = 121 slots (3.9 KB)
```

Stress-tested at 32 unique cells: `128 ≤ 193` → PASS, margin = 65 slots.

**FAIL condition (mode-scoped preload required):**

```
S_peak_slots > 193
```

This would require approximately 49+ unique 16×16 sprite cells on screen simultaneously (49 × 4 = 196 > 193). Based on Rastan's sprite architecture (22 max instances, 18 max unique codes per frame), this condition is very unlikely to be reached in practice.

**Decision rule applied to current confirmed numbers:** Bulk preload is SAFE. The constraint is not VRAM exhaustion but the sprite base address conflict: sprite tiles MUST be placed at slots 1343+ (not 1024+) if bulk PC080SN preload is in use.

---

## 8. Expected Final-Architecture Direction

### Selected: Option A — Bulk Preload All PC080SN Tiles at Boot

**Justification with numbers:**

| Factor | Value | Conclusion |
|--------|-------|-----------|
| PC080SN bulk preload VRAM cost | 1,342 slots × 32 B = 42.0 KB | Fits in 48.0 KB tile region |
| Remaining VRAM after bulk preload | 193 slots = 6.2 KB | Available for sprites |
| Worst-case sprite VRAM (18 cells) | 72 slots = 2.25 KB | 72 < 193: PASS |
| Stress-test sprite VRAM (32 cells) | 128 slots = 4.1 KB | 128 < 193: PASS |
| Margin at 18 cells | 121 slots = 3.9 KB | Adequate |
| Margin at 32 cells | 65 slots = 2.1 KB | Adequate |

**Conditions for Option A to be correct:**

1. The sprite tile base address in the rastan-direct sprite pipeline MUST be set to 1343 (not 1024). Slots 1024–1342 are occupied by PC080SN tile data after bulk preload. Writing sprite tiles to slot 1024 would corrupt PC080SN tile data already loaded there.

2. The profiling run must confirm that worst-case concurrent unique sprite cells do not exceed 48. If any game mode requires more than 48 unique cells simultaneously, Option B (mode-scoped preload freeing VRAM slots below 1343) would be required.

**Option B (mode-scoped) would only become necessary if:**
- Profiling finds worst-case sprite working set > 48 unique cells, OR
- Profiling finds a single mode's PC080SN working set is substantially smaller than 1,067 (e.g., End-Round uses only 500 tiles, not 1,055), enabling VRAM savings that make architectural sense.

Based on the SGDK data, neither condition is likely. End-Round uses ~1,055 tiles — close to the global maximum of 1,067. Savings from mode-scoped preload would be at most 12 slots (~384 bytes), which is not architecturally significant.

---

## 9. Rainbow Islands Validation

Rainbow Islands Genesis used mode-scoped tile preload (scene-scoped DMA at scene entry) rather than global preload at boot. This choice was driven by a specific condition: the SGDK version of Rastan identified 2,272 unique PC080SN tiles across all scenes — exceeding the available 1,164-slot VRAM pool by 1,108 tiles. A global preload was impossible because the tile set did not fit. Mode-scoped preload was the only valid option for that version.

The rastan-direct version operates under different constraints:
- The current LUT has 1,067 unique slots (not 2,272).
- The VRAM pool is 1,535 slots (not 1,164 — the 1,164 figure in the SGDK docs excluded the 1,024–1,279 sprite range from the PC080SN pool).
- 1,067 ≤ 1,535: global preload fits with 468 slots to spare.

Therefore, the rastan-direct version does NOT need to follow the Rainbow Islands / SGDK model of mode-scoped preload. The reason Rainbow Islands Genesis used scene-scoped preload was VRAM overflow, not architectural preference. That overflow does not exist in rastan-direct.

What this project should take from Rainbow Islands is the general principle: tile pixel data must be in VRAM before the nametable references it. The scene-scoped triggering mechanism is one way to achieve this; init-time bulk preload is another equally valid way when the tile set fits. For rastan-direct, bulk preload is simpler and sufficient.

---

## 10. Single Root Concern

The bulk PC080SN preload places 1,067 tiles into slots 0–1342, forcing sprite tiles into slots 1343–1535 (192 slots = 48 cells), and this constraint has not been validated against the actual worst-case concurrent PC090OJ sprite working set because no runtime profiling of per-mode tile and sprite usage has been performed on the rastan-direct wrapper.

---

## 11. Single Next Correction

Instrument `genesistan_hook_tilemap_plane_a` to record which VRAM slots are written per scene bucket using a 1,535-bit WRAM bitmask (`genesistan_tile_slot_observed`, 3 × 192 bytes, one per scene), and simultaneously record the peak unique PC090OJ cell code count per frame in a `genesistan_sprite_peak_unique` WRAM variable, then run one complete attract cycle + one stage of gameplay + one end-round to capture the profiling data and verify the VRAM budget math against actual runtime behavior.

---

## 12. What Must Not Be Changed Yet

- `genesistan_hook_tilemap_plane_a` — nametable translation logic is correct; only observational instrumentation may be added
- `genesistan_pc080sn_tile_vram_lut` and its `.incbin` directive — LUT is correct and must not be regenerated until profiling confirms the per-mode working sets
- `staged_bg_buffer` / `vdp_commit_bg_strips_if_dirty` — nametable staging and commit path is correct
- `_VINT_handler` structure — display-disable bracketing and commit order must not change
- `vdp_commit_tiles_if_dirty` — synthetic tile upload for slots 1–3 must remain (scheduled for later removal)
- `init_staging_state` internal logic — must not change; only the call site gains the `init_arcade_tile_vram` call
- All 34 `opcode_replace` entries in `specs/rastan_direct_remap.json`
- `rom_absolute_call_relocation` configuration
- A5 initialization to 0xFF0000
- `VRAM_TILE_BASE = 0x00000020` constant
- All existing build outputs in `build/`
- The patcher (`postpatch_startup_rom.py`)
- **Step 6 checkerboard removal must NOT happen yet** — the synthetic tile infrastructure (slots 1–3, `tile_init_words`, `staged_tile_words`) must remain until the full tile preload pipeline is verified working
- The sprite pipeline base address (1024 in SGDK version) must NOT be ported to rastan-direct until profiling confirms the safe base address in the context of the bulk PC080SN preload

---

## 13. Final Verdict

Bulk-preloading all 1,067 PC080SN tiles at boot is arithmetically safe: it occupies 42.0 KB of the 48.0 KB tile VRAM region, leaving 193 eight-by-eight slots (6.2 KB, 48 sixteen-by-sixteen sprite cells) for PC090OJ sprite tile streaming. The confirmed worst-case sprite working set is 18 unique 16×16 cells (72 eight-by-eight slots), well within the 193-slot limit with 121 slots of margin. Even a generous 32-cell estimate passes with 65 slots of margin.

The architecture direction is Option A: bulk preload all PC080SN tiles at init. Mode-scoped preload is not required because (unlike the SGDK version which faced overflow at 2,272 tiles vs. 1,164 slots) the rastan-direct tile set of 1,067 fits comfortably in the 1,535-slot tile VRAM region.

One critical implementation constraint emerges from the math: the sprite tile base address for rastan-direct's sprite pipeline must be slot 1343 or higher, not 1024. Slots 1024–1342 are occupied by PC080SN tile data after bulk preload. Any sprite pipeline implementation that writes to slots below 1343 will corrupt the PC080SN tile graphics. This constraint is not a reason to abandon bulk preload — it is a design parameter that must be stated explicitly in the sprite pipeline design.

The open empirical question (does any single mode actually need all 1,067 PC080SN slots?) should be answered by the profiling instrumentation defined in Section 6 before committing to the final architecture. If the profiling reveals that End-Round uses 1,055 of 1,067 tiles (as the SGDK data suggests), bulk preload is definitively justified. If it reveals a smaller per-mode working set (e.g., 700 tiles), mode-scoped preload becomes attractive as it would free ~367 slots for a larger sprite streaming buffer.
