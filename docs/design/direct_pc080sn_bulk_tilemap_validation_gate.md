# Direct PC080SN Bulk Tilemap — Validation Gate

## 1. Executive Summary

- The **no-buffer, direct-VDP-write design is VALID** for all identified callers. Every call to `0x5A4DE` writes a complete, self-contained rectangle. No caller depends on previous C-window contents. No partial accumulation across calls.
- The **tile LUT/preload coverage is CRITICALLY INSUFFICIENT**. Only 2 of 781 unique block-write tiles exist in the current LUT. 779 tiles are missing. Without extending the Python precompute, the hook would produce empty/zero-slot nametable entries — no visible tiles even with correct placement.
- The **caller catalog in the design doc contains two errors**: `0x5A474` does NOT call `0x5A4DE` (it calls `0x563A6`, a text renderer); `0x5A370` has no identified callers (likely dead code or jump-table-only access).
- **Additional tile sources exist** beyond the 5 tables audited: gameplay HUD (6 stage-specific tables), end-round quadrant writes (4 tables at 0x582xx–0x58Axx), and animation frame data (3 cycling tables). These must also be scanned for LUT coverage.
- **VRAM budget: SAFE WITH MANAGEMENT.** 2272 total unique tiles across all scenes cannot fit in 1164 slots simultaneously — global static assignment is impossible. Scene-scoped loading is required. Per-scene budgets validated: Title/Attract 1110, End-Round 1055, Gameplay 817 (all include block-write + strip builder + ~42 text glyphs). Title/Attract is tightest at 54 slots headroom. Sprites (slots 1024–1279) and SGDK font (slots 1440–1535) do NOT compete with the PC080SN cache.
- **Implementation gate: GO WITH PRECONDITIONS** — Python LUT must be extended with scene-aware slot assignment and per-scene preload manifests before the assembly hook is implemented.

---

## 2. Validation Scope

### Documents Read
1. `docs/design/direct_pc080sn_bulk_tilemap_translation_design.md`
2. `docs/design/title_screen_composition_audit.md`
3. `docs/design/build299_theory_vs_reality_reconciliation.md`
4. `docs/design/full_graphics_system_completion_plan.md`
5. `AGENTS_LOG.md`
6. `docs/research/rainbow_islands_arcade_vs_genesis_graphics_comparison.md`
7. `docs/research/cadash_arcade_vs_genesis_graphics_comparison.md`

### Source of Truth Examined
8. `build/maincpu.disasm.txt` — all 17 call sites of `0x5A4DE` traced, plus the routine itself
9. `apps/rastan/src/main.c` — existing tilemap/text/sprite hooks, tile cache
10. `apps/rastan/src/startup_trampoline.s` — existing assembly tilemap commit functions
11. `apps/rastan/src/startup_bridge.c` — LUT declarations, tile cache, shadow memory
12. `tools/translation/precompute_pc080sn_tile_lut.py` — current tile discovery: strip builder descriptor tables ONLY
13. `build/pc080sn_tile_vram_lut.bin` — 16384-entry LUT, 289 non-zero entries
14. `build/pc080sn_vram_preload.bin` — 289 tile→slot preload pairs
15. `build/pc080sn_unique_tile_count.txt` — reports 289
16. `build/regions/maincpu.bin` — arcade ROM, used for tile index extraction

---

## 3. Atomic vs Incremental Caller Audit

### The Routine: `0x5A4DE`

```
Inner loop (D0 iterations): write (D2, *A0++) to consecutive C-window cells
Outer loop (D1 iterations): advance dest by 256 bytes (= 1 C-window column)
```

Each call writes a D0×D1 rectangular block. The routine does NOT read from the destination. It does NOT depend on previous contents. Each call is self-contained.

### Per-Caller Classification

#### Scene-Setup Callers (One-Shot)

| Caller | Src ROM | Dest C-window | D0 (rows/col) | D1 (cols) | D2 | Context | Classification |
|--------|---------|---------------|---------------|-----------|----|---------|----|
| `0x5A38E` | `0x5B0B2` | `0xC00328` | 28 | 20 | 1 | Title screen logo+bg | **ATOMIC ONE-SHOT** |
| `0x5A370` | `0x5A7DA` | `0xC00320` | 28 | 21 | 1 | Alt title (no callers found) | **DEAD CODE** |
| `0x5A3AC` | `0x5AC72` | `0xC01240` | 12 | 10 | 1 | Insert coin attract | **ATOMIC ONE-SHOT** |
| `0x5A3DE` | `0x5AF62` | `0xC00E18` | 12 | 14 | 1 | Game over screen | **ATOMIC ONE-SHOT** |
| `0x5A410` | `0x5AF62` | `0xC00C3C` | 12 | 14 | 1 | Continue screen | **ATOMIC ONE-SHOT** |
| `0x5A442` | `0x5AD62` | `0xC00C38` | 16 | 16 | 1 | Stage intro / boss name | **ATOMIC ONE-SHOT** |

**FACT:** All 6 scene-setup callers fire once per state transition. None loop. None depend on previous tilemap contents. Each writes a complete rectangle. Safe for direct VDP translation.

#### Gameplay HUD Caller

| Caller | Src ROM | Dest C-window | D0 | D1 | D2 | Context | Classification |
|--------|---------|---------------|----|----|----|---------|----|
| `0x56356` | table-driven (`0x5635E`) | table-driven | table | table | 5 | Per-stage HUD | **ATOMIC ONE-SHOT** |

**FACT:** Called when `A5@(5034) == 10` (state 0x0A). State immediately advances to 11 after the call. Not per-frame. Each call writes a complete rectangle from the descriptor table indexed by current stage number. 6 stage entries identified:

| Stage | Src | Dest | Rows/Col | Cols |
|-------|-----|------|----------|------|
| 1 | `0x56A22` | `0xC00A28` | 14 | 16 |
| 2 | `0x56BE2` | `0xC00A28` | 12 | 16 |
| 3 | `0x56D62` | `0xC00A28` | 12 | 16 |
| 4 | `0x56EE2` | `0xC00628` | 12 | 20 |
| 5 | `0x570C2` | `0xC00A28` | 14 | 14 |
| 6 | `0x56A22` | `0xC00A28` | 14 | 16 |

Stage 6 reuses stage 1 source data. Stage 4 has unique dest and taller block.

#### End-Round Quadrant Init (One-Shot)

| Call Site | Table Addr | Src | Dest | Rows/Col | Cols | D2 | Classification |
|-----------|-----------|-----|------|----------|------|----|----|
| `0x57466` | `0x5816A` | `0x5822A` | `0xC00000` | 32 | 16 | 4 | **ATOMIC ONE-SHOT** |
| `0x57478` | `0x58176` | `0x5822A` | `0xC00080` | 32 | 16 | 4 | **ATOMIC ONE-SHOT** |
| `0x5748A` | `0x58182` | `0x5862A` | `0xC01000` | 32 | 16 | 5 | **ATOMIC ONE-SHOT** |
| `0x5749C` | `0x5818E` | `0x58A2A` | `0xC01080` | 32 | 16 | 5 | **ATOMIC ONE-SHOT** |
| `0x574B0` | `0x5819A` | `0x5919C` | `0xC09070` | 10 | 14 | 6 | **ATOMIC ONE-SHOT** |

**FACT:** Called from state 2 init of the end-round state machine (`0x5744E`/`0x574A4`). Fires once when entering state 2. The first 4 calls write 4 quadrants covering the full BG C-window (32×16 × 4 = 2048 cells total). The 5th writes to FG (`0xC09070` is in FG range `0xC08000+`).

#### End-Round Static Init (One-Shot)

| Call Site | Table Addr | Src | Dest | Rows/Col | Cols | D2 | Classification |
|-----------|-----------|-----|------|----------|------|----|----|
| `0x574C6` | `0x581CA` | (from table) | (from table) | table | table | 6 | **ATOMIC ONE-SHOT** |
| `0x574DC` | `0x581FA` | (from table) | (from table) | table | table | 6 | **ATOMIC ONE-SHOT** |

State 6 and state 8→9 transition respectively. One-time per state entry.

#### End-Round Recurring Animation Callers

| Call Site | Table Base | Frames | Period | Dest Same? | Classification |
|-----------|-----------|--------|--------|------------|-------|
| `0x5752A` | `0x581A6` | 3 | Every 10 frames | **YES** — all 3 write to `0xC09078`, 8×4 | **RECURRING OVERWRITE** |
| `0x5756A` | `0x581CA` | 4 | Every 28 frames | **YES** — all 4 write to `0xC09064`, 8×14 | **RECURRING OVERWRITE** |
| `0x575AA` | `0x581FA` | 3 | Every 26 frames | **PARTIAL** — frames 0-1: `0xC09050` 9×14; frame 2: `0xC08950` 9×21 | **RECURRING OVERWRITE (variable region)** |

**FACT — Recurring callers are safe for bufferless design because:**
1. Each call writes a COMPLETE rectangle (not a partial update)
2. Animation frames OVERWRITE the same destination region (no accumulation)
3. No caller reads back from the C-window
4. The VDP nametable itself serves as the persistent state — each new frame replaces the previous

**NOTE on `0x575AA` (table 0x581FA):** Frame 2 writes to a different dest with a larger region than frames 0-1. This is still safe — each individual call is atomic and self-contained. The handler translates whatever the registers specify, regardless of what was previously written. The taller frame 2 region extends upward to cover additional cells, effectively "revealing" more content. On the next cycle, frames 0-1 will overwrite the overlapping cells with their content, leaving the non-overlapping cells from frame 2 untouched until frame 2 fires again. This is the intended animation behavior — it works the same way on arcade hardware.

### Caller NOT calling `0x5A4DE` (Design Doc Error)

**`0x5A474`** — Listed in the design doc as a caller. **FACT: It does NOT call `0x5A4DE`.** It calls `0x563A6` (character-by-character text renderer) in a loop driven by a table at `0x5A5AC`. This is a text rendering path, not a block tilemap copy. Must be removed from the caller catalog.

### Caller With No Identified Callers (Possible Dead Code)

**`0x5A370`** — Writes 28×21 from `0x5A7DA` to `0xC00320`. No BSR/JSR to `0x5A370` found anywhere in the disassembly. Either dead code or called via an indirect mechanism (jump table) not visible in linear disassembly scan. Classification: **UNKNOWN — treat as low priority.**

---

## 4. Bufferless Design Validation

### Question: Is the "no intermediate buffer" design VALID?

### Answer: **VALID**

### Justification

Every identified caller of `0x5A4DE` (17 call sites across 14 unique routines) satisfies ALL of the following:

1. **Complete rectangular write:** Each call writes D0×D1 cells to a rectangular C-window region. No call writes a partial region that must be completed by a subsequent call.

2. **No read-back dependency:** The routine (`0x5A4DE`) never reads from the destination. It writes `(attr, tile_index)` pairs from ROM source data. No caller depends on previous C-window contents.

3. **No cross-call accumulation:** No two callers write partial data to the SAME region expecting the combination to form the final output. Scene-setup callers write to non-overlapping regions. Animation callers overwrite the same region atomically.

4. **Self-contained register contract:** Each call receives all necessary parameters in D0/D1/D2/A0/A1. No hidden state, no global cursor, no multi-call protocol.

5. **Recurring callers are atomic overwrites:** The three animation callers (`0x57502`, `0x57542`, `0x57582`) fire periodically but each individual invocation writes a complete rectangle that fully replaces the previous frame's data at the same VDP addresses.

**Comparison with strip builder:** The existing strip builder hooks also write directly to VDP with no intermediate buffer. The block writer follows the identical pattern — same LUT lookups, same VDP port writes, same direct-commit model. The strip builder is proven working. The block writer uses the same architectural approach.

**Comparison with Rainbow Islands:** Rainbow Islands Genesis tilemap routines at `0x28D6`/`0x28FA`/`0x291E`/`0x2942` compute VDP plane destinations and stream directly to VDP data port `0xC00000` with no intermediate buffer. This validates the pattern.

### Edge Case: `0x575AA` Frame 2 Variable Region

Frame 2 of the animation at `0x575AA` writes to a different dest address and larger size than frames 0-1. This does NOT invalidate the bufferless design because:
- Each call is still atomic (complete rectangle)
- The handler doesn't need to know about previous calls
- The VDP nametable retains the previous write until overwritten

The cells written by frame 2 that are NOT overwritten by frames 0-1 will persist in VDP until the next frame 2 fires or the state machine advances. This is correct behavior — identical to how it works on the arcade's C-window RAM.

---

## 5. Tile LUT / Preload Coverage Audit

### Current LUT State

- **LUT size:** 16384 entries
- **Non-zero (assigned) entries:** 289
- **Source:** Strip builder descriptor tables only (scanned by `precompute_pc080sn_tile_lut.py:discover_descriptor_tables()`)

### Coverage Per Block-Write Source Table

| Table Address | Used By | Dimensions | Total Words | Unique Tiles | In LUT | Missing | Coverage |
|---------------|---------|-----------|-------------|-------------|--------|---------|----------|
| `0x5B0B2` | Title screen | 28×20 | 560 | 175 | 2 | **173** | 1.1% |
| `0x5A7DA` | Attract alt (dead?) | 28×21 | 588 | 283 | 1 | **282** | 0.4% |
| `0x5AC72` | Insert coin panel | 12×10 | 120 | 83 | 1 | **82** | 1.2% |
| `0x5AF62` | Game over / continue | 12×14 | 168 | 127 | 1 | **126** | 0.8% |
| `0x5AD62` | Stage intro / boss | 16×16 | 256 | 133 | 1 | **132** | 0.8% |
| **TOTAL** | | | 1692 | **781** | **2** | **779** | **0.3%** |

### VRAM Slot Budget — Validated Model

#### Genesis VRAM Tile Slot Layout (Proven)

| Range | Slots | Owner | Competes with PC080SN cache? |
|-------|-------|-------|------------------------------|
| 0–15 | 16 | SGDK system (reserved) | No |
| 16–19 | 4 | User tiles (DIP graphics) | No |
| 20–1023 | 1004 | **PC080SN tile cache A** | IS the cache |
| 1024–1279 | 256 | Sprite tiles (`FRONTEND_RUNTIME_SPRITE_TILE_BASE`) | **No** — separate range, loaded from PC090OJ ROM |
| 1280–1439 | 160 | **PC080SN tile cache B** | IS the cache |
| 1440–1535 | 96 | SGDK font (`TILE_FONT_INDEX`) | **No** — above cache range, launcher only |

**PC080SN tile cache budget: 1164 slots** (1004 + 160). Sprites and fonts do NOT reduce this.

**In-game text glyphs DO compete:** The text writer hooks (`0x3BB48`, `0x3C3FE`) call `tile_cache_get()` for each glyph, consuming PC080SN cache slots. Up to ~42 unique glyphs on screen at any time (A-Z, 0-9, punctuation).

#### Global Static Assignment: IMPOSSIBLE

| Category | Unique Tiles |
|----------|-------------|
| Strip builder | 289 |
| Title/Attract block-write | 781 |
| End-Round block-write | 727 |
| Gameplay block-write | 492 |
| All block-write combined | 1992 |
| **All tiles (block + strip)** | **2272** |
| 1164-slot budget | 1164 |
| **Overflow** | **1108** |

**FACT:** 2272 unique tiles across all sources. 1164 available slots. A single global LUT with unique slot per tile index is IMPOSSIBLE. Cross-scene overlap is negligible (1–4 tiles between any scene pair; 9 between all block-write and strip builder). The tiles are almost entirely disjoint across scenes.

#### Per-Scene Budget: ALL FIT (Validated)

Each scene's block-write tiles + strip builder tiles + ~42 text glyphs must fit in 1164:

| Scene | Block Tiles | + Strip (289) | − Overlap | + Text (~42) | = Total | Headroom | Status |
|-------|------------|--------------|-----------|-------------|---------|----------|--------|
| **Title/Attract** | 781 | +289 | −2 | +42 | **1110** | +54 | **OK** |
| **End-Round** | 727 | +289 | −3 | +42 | **1055** | +109 | **OK** |
| **Gameplay** | 492 | +289 | −6 | +42 | **817** | +347 | **OK** |

**Worst case: Title/Attract at 1110 / 1164 (54 slots headroom).** This is tight but sufficient.

#### Scene-Scoped Loading: REQUIRED

Since global static assignment overflows, the LUT must allow **cross-scene VRAM slot reuse**:

1. The Python precompute assigns VRAM slots **per-scene**, allowing the same slot to map to different tile indices in different scenes (since those tiles never coexist)
2. The LUT (`pc080sn_tile_vram_lut[16384]`) remains a single global ROM table — `lut[tile_A] = slot_50` and `lut[tile_B] = slot_50` is valid when tile_A and tile_B are never active in the same scene
3. At scene transitions, a preload function DMA's the new scene's tile graphics from ROM into the assigned VRAM slots, overwriting the previous scene's graphics
4. Within a scene, every tile index referenced by the active block-write callers maps to a slot containing the correct graphics

**This is the same model as the existing `genesistan_preload_pc080sn_title_frontend()`** — it already demonstrates scene-scoped tile loading. The extension is: multiple preload sets (title, end-round, gameplay), triggered at scene transitions.

#### Additional Source Tables (Now Audited)

All source tables have been scanned (including those previously listed as unaudited):

| Source | Unique Tiles | Scene | Included In Per-Scene Budget |
|--------|-------------|-------|------------------------------|
| Title screen (`0x5B0B2`) | 175 | Title/Attract | Yes |
| Attract alt (`0x5A7DA`) | 283 | Title/Attract | Yes |
| Insert coin (`0x5AC72`) | 83 | Title/Attract | Yes |
| Game over (`0x5AF62`) | 127 | Title/Attract | Yes |
| Stage intro (`0x5AD62`) | 133 | Title/Attract | Yes |
| End-round quads (`0x5822A`/`0x5862A`/`0x58A2A`) | included | End-Round | Yes |
| End-round FG overlay (`0x5819A`) | included | End-Round | Yes |
| Animation frames (`0x581A6`/`0x581CA`/`0x581FA`) | included | End-Round | Yes |
| Gameplay HUD (`0x5635E`, 6 entries) | 492 | Gameplay | Yes |

### Current LUT Verdict: **NO — critically insufficient**

The current LUT covers 0.3% of block-write tile needs (2 of 781 title/attract tiles). Implementation without LUT extension would produce empty VDP nametable entries (slot 0 = blank tile) for 99.7% of cells.

**Required fix:** Extend `precompute_pc080sn_tile_lut.py` to:
1. Scan all block-write source tables across all scenes
2. Assign VRAM slots with cross-scene reuse (same slot for tiles in different scenes)
3. Generate per-scene preload manifests for scene-transition tile loading

---

## 6. Current Build Symptom Reconciliation

### Observed Symptoms (Build 300)

| Symptom | Explained By | Classification |
|---------|-------------|----------------|
| **Missing RASTAN sword logo** | **BOTH:** (1) Block tilemap write at `0x5A38E` null-sunk → nametable entries never reach VDP. (2) Even if nametable entries were translated, 173 of 175 unique tile indices have no VRAM slot → blank tiles. | Missing tilemap translation + missing LUT coverage |
| **Missing TAITO logo** | **NOT a block-write issue.** TAITO text is rendered by FG text writer `0x3BB48`, which IS hooked and working since Build 300. If TAITO text is missing, it is a text writer issue (text ID routing), not a block-write issue. | Separate system — not in scope |
| **Brown/orange solid fill background** | **Missing tilemap translation.** Background fill tile `0x00AD` is part of the 28×20 block at `0x5B0B2`. With the block write null-sunk, no tiles populate the VDP plane. The solid color comes from the arcade palette now loaded to CRAM (Build 300 fix) applied to empty/default plane entries. | Missing tilemap translation |
| **No recognizable title composition in VRAM viewer** | **BOTH:** (1) No nametable entries → `tile_cache_get()` never called for block-write tiles → no tile graphics DMA'd to VRAM. (2) The 289 strip builder tiles in VRAM are irrelevant to the title screen — they serve the scrolling gameplay pipeline. | Missing tilemap translation + missing LUT coverage |
| **Scattered dots (sprites)** | **Separate issue.** Static title sprites from `0x3B8B0` go to shadow memory never read by sprite pipeline. A few per-frame sprite entries in workram produce small dots. | Sprite pipeline gap (not block-write related) |
| **Font glyphs visible in VRAM** | **Confirms text writer + tile cache work.** Font tiles are cached by `tile_cache_get()` via text writer hook. This proves the tile cache mechanism is functional — it simply never receives block-write tile requests. | Working system — validates cache mechanism |

### Root Cause Classification

| Root Cause | Symptoms Explained | Priority |
|-----------|-------------------|----------|
| **C-window null-sink blocks block-write nametable data** | No tilemap data reaches VDP for title screen, attract panels, game over, stage intros, gameplay HUD, end-round scenes | **PRIMARY** — the hook at `0x5A4DE` directly addresses this |
| **LUT has no VRAM slots for block-write tile indices** | Even with the hook, tiles would appear blank without LUT extension | **PREREQUISITE** — must be resolved before hook can produce visible output |
| **VRAM budget requires scene-scoped management** | 2272 total unique tiles cannot fit in 1164 slots simultaneously. Per-scene budgets fit: Title 1110, End-Round 1055, Gameplay 817 (all include strip + text). Title/Attract is tightest at 54 slots headroom. | **SAFE WITH MANAGEMENT** — scene-scoped VRAM loading required; global static assignment impossible |

---

## 7. Go / No-Go Decision

### **GO WITH PRECONDITIONS**

The core design (hook `0x5A4DE`, direct VDP writes, no buffer, assembly hot path) is validated as architecturally sound. All callers are safe for bufferless translation. The register contract is clean and consistent across all 17 call sites.

However, implementation MUST NOT proceed until:

### Precondition 1: Python LUT Extension (BLOCKING)

The `precompute_pc080sn_tile_lut.py` script must be extended to scan ALL block-write source tables:
- 5 scene-setup tables (`0x5B0B2`, `0x5A7DA`, `0x5AC72`, `0x5AF62`, `0x5AD62`)
- 6 gameplay HUD tables (from `0x5635E` descriptor entries)
- 3 end-round quadrant sources (`0x5822A`, `0x5862A`, `0x58A2A`)
- 1 end-round FG overlay source (`0x5919C`)
- 10 animation frame sources (from `0x581A6`, `0x581CA`, `0x581FA` descriptors)

The extended script must:
- Scan all source tables listed above
- Assign VRAM slots with cross-scene reuse (2272 total tiles into 1164 slots, reusing slots across scenes that never coexist)
- Generate per-scene preload manifests for scene-transition tile loading
- Report per-scene tile counts and confirm all fit within 1164

### Precondition 2: Scene-Scoped VRAM Loading (BLOCKING)

Global static assignment is impossible (2272 tiles, 1164 slots). Scene-scoped VRAM loading is required:
- The Python LUT must assign slots allowing cross-scene reuse
- A scene-transition preload function must DMA the new scene's tile graphics from ROM into VRAM at the assigned slots
- Per-scene budgets are validated: Title 1110, End-Round 1055, Gameplay 817 — all fit with headroom
- Title/Attract is the tightest scene at 54 slots headroom — this margin must be monitored if new block-write sources are discovered

### Precondition 3: Design Doc Corrections (NON-BLOCKING)

The design doc `direct_pc080sn_bulk_tilemap_translation_design.md` contains two factual errors that should be corrected:
1. **`0x5A474` is NOT a caller of `0x5A4DE`** — it calls `0x563A6` (text renderer). Remove from caller catalog.
2. **`0x5A370` has no identified callers** — mark as dead code / unresolved in caller catalog.

---

## 8. Confirmed Facts

1. **FACT:** All 17 call sites of `0x5A4DE` (6 BSR + 11 JSR) write complete, self-contained rectangles. No partial writes, no cross-call accumulation.
2. **FACT:** The routine at `0x5A4DE` never reads from the destination. Each call is write-only and independent.
3. **FACT:** Recurring animation callers (`0x57502`, `0x57542`, `0x57582`) overwrite the same VDP region each cycle. No buffer needed — VDP nametable is the persistent state.
4. **FACT:** The current LUT contains 289 assigned tiles. Block-write tables reference 781 unique tile indices, of which only 2 overlap with the LUT. 779 are missing.
5. **FACT:** 2272 total unique tiles across all sources. 1164 VRAM slots. Global static assignment overflows by 1108. Scene-scoped loading is mandatory.
6a. **FACT:** Per-scene budgets (block + strip + ~42 text glyphs): Title/Attract = 1110, End-Round = 1055, Gameplay = 817. All fit within 1164. Title/Attract has 54 slots headroom (tightest).
6b. **FACT:** Sprites occupy slots 1024–1279 (from PC090OJ ROM, loaded by `genesistan_sprite_tile_prepare()`). SGDK font occupies slots 1440–1535. Neither competes with the PC080SN tile cache (slots 20–1023 + 1280–1439).
6c. **FACT:** In-game text glyphs (~42 unique) are allocated via `tile_cache_get()` and DO consume PC080SN cache slots. Included in per-scene budgets above.
6. **FACT:** `0x5A474` does NOT call `0x5A4DE` — it calls `0x563A6`. This is a design doc error.
7. **FACT:** `0x5A370` has no BSR/JSR callers in the disassembly. Likely dead code.
8. **FACT:** The register contract (D0/D1/D2/A0/A1) is uniform across all call sites. One hook covers all callers.
9. **FACT:** The title screen failure is a compound of (a) null-sunk nametable writes AND (b) missing LUT/preload coverage. Both must be fixed for visible output.
10. **FACT:** Font glyphs in VRAM confirm `tile_cache_get()` works — the mechanism is sound, it simply never receives block-write tile references because those nametable entries are null-sunk before reaching the cache.

---

## 9. Rejected Assumptions

| Assumption from Design Doc | Verdict | Evidence |
|---------------------------|---------|----------|
| "`0x5A474` is a caller of `0x5A4DE`" | **REJECTED** | Disassembly shows `0x5A474` calls `0x563A6` in a loop, not `0x5A4DE`. |
| "Estimated 200–400 additional unique tiles" across block-write tables | **UNDERESTIMATE** | Actual count from 5 main tables alone: 779 unique, 779 missing. Additional tables (gameplay, end-round) will add more. |
| "`0x5A370` is 'Attract alternate scene'" with callers | **UNVERIFIED** | No direct callers found. May be dead code or indirect-only. |
| "VRAM slot budget: ample room for 200–400 additional tiles" | **WRONG on both counts** | Actual unique tile count: 2272 (not 200-400). Global static assignment overflows by 1108. Per-scene budgets DO fit (Title 1110, End-Round 1055, Gameplay 817) but require scene-scoped loading with cross-scene slot reuse. |

---

## 10. Remaining Unknowns

1. ~~**UNKNOWN:** Total unique tile count across all sources.~~ **RESOLVED:** 2272 unique tiles total. Per-scene: Title/Attract 781, End-Round 727, Gameplay 492. Strip builder 289. Cross-scene overlap negligible.

2. **UNKNOWN:** Whether `0x5A370` is truly dead code or accessed via an indirect jump table not visible in linear disassembly. Low priority — if it is called, the hook at `0x5A4DE` will handle it regardless.

3. **UNKNOWN:** Whether D2 attr values 4, 5, 6 (used by gameplay/end-round callers) map correctly through the existing `pc080sn_attr_lut[32]`. The 5-bit key extraction `(prio << 4) | (vflip << 3) | (hflip << 2) | pal` for D2=4 gives key 0 with pal=0 (bits 0-1 of 4 = 0b00) and prio=0 (bit 13 of 4 = 0). For D2=5: pal=1, prio=0, key=1. For D2=6: pal=2, prio=0, key=2. These are simple palette-only values. The attr LUT should handle them, but this should be verified against the generated `pc080sn_attr_lut_words.inc`.

4. **UNKNOWN:** Whether tiles in the 0x2xxx range (0x21B6–0x2570, heavily used by block-write tables) have valid graphics data in `pc080sn.bin`. These tile indices are within the 16384-tile ROM but have never been loaded. If the ROM data at those indices is blank/garbage, the issue is in the tile ROM content, not the LUT.
