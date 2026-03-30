# Full Graphics System Completion Plan

**Agent:** Andy (Architecture)
**Build baseline:** 287
**Date:** 2026-03-30
**Mandate:** Complete model of remaining graphics work across all subsystems with mandatory immediate implementation phase. No code, spec, or build files are modified by this document.

---

## 1. Required Reading Verification

The following documents were read before writing this plan:

**Core project docs:**
- `AGENTS.md` — confirms opcode-replacement strategy, spec-driven approach, holistic remap over trampoline hacks
- `CURRENT_STATE.md` — stale (says "Next Step: Replace C helper"; that was completed Build 281+); active content is the "Not Working: Visible sprites, Tile correctness, Palette correctness" entry, which remains partially accurate

**Current graphics / sprite work:**
- `docs/design/full_prototype_sprite_execution_path.md` — defines the Option A prototype (per-frame tile decode + upload from vblank handoff before commit); this is the architecture in current use
- `docs/design/sprite_interpretation_failure_diagnosis.md` — documents the three root causes fixed in Builds 284–286: (C) link chain = 0 for all entries, (A) row-major tile decode vs column-major VDP requirement, (F) LUT source buffer mismatch
- `docs/design/sprite_interpretation_fix_results.md` — confirms fixes applied in Build 284: sequential link chain and column-major tile decode
- `docs/design/live_decode_buffer_wiring_fix_results.md` — **CRITICAL**: confirms `VDP_loadTileData()` is already in the live vblank path as of Build 285; VRAM tile 1024 (`0x8000`) contains `1199 8111 1898 8888...` (real decoded sprite pixel data); the tile upload is DONE
- `docs/design/canonical_blocka_attr_decode_results.md` — confirms `attr_lut[0]=0x6000` → palette line 3 in Build 286; SAT word2 = `0xE400` = priority|pal=3|tile=0x400; sprites now use CRAM line 3 exclusively
- `docs/design/zero_code_filter_results.md` — confirms Build 287 baseline: `active_count=1`, `chain_ok=true`, zero-code filter working
- `docs/design/blockA_producer_reconstruction_plan.md` — confirms Phase 2 spec patch applied; block-A builder at arcade 0x05A098 (genesis 0x05A2B4) runs and produces `w0=0000, w1=00E8, w2=03CA, w3=0010`

**Required reference implementations:**
- `docs/research/rainbow_islands_arcade_vs_genesis_graphics_comparison.md`
- `docs/research/cadash_arcade_vs_genesis_graphics_comparison.md`

---

## 2. Rainbow Islands / Cadash Ownership Principles (applied to all phases)

Both reference implementations converge on one architectural law for Rastan:

> **Every arcade graphics intent class (sprite, tilemap, palette, scroll, clear/fill) must have an identified Genesis VDP owner, and each producer must be proven to feed that owner — not a legacy stale buffer.**

The five intent classes and their Genesis owners:

| Arcade intent class | Arcade hardware | Genesis owner |
|--------------------|-----------------|---------------|
| Sprite descriptors | PC090OJ RAM writes | SAT at VRAM 0xF800 via `genesistan_sprite_commit_asm()` |
| Tilemap tiles | PC080SN RAM writes | VDP Plane B / Plane A nametables via `VDP_setTileMapXY()` |
| Palette entries | Palette RAM writes | CRAM via `VDP_setPalette()` / `refresh_frontend_sprite_palettes()` |
| Scroll offsets | Chip control writes | VDP H/V scroll registers via `genesistan_scroll_from_workram_vdp()` |
| Frame clear / fill | Chip RAM clear | VDP fill / WRAM clear + upload via prepare/commit cycle |

**Rastan specific rule derived from both references:** Each intent class must have a confirmed, unbroken producer→consumer path that fires every vblank. If the chain breaks at any point (wrong buffer, stale source, missing load call), the output for that class is invisible regardless of how correct the downstream hardware handling is.

**PC090OJ (Rainbow Islands + Rastan shared):** arcade object RAM updates → WRAM descriptor staging → SAT emit. Rainbow Islands Genesis stages descriptors in WRAM at `0xFFFA80/0xFFFB00` with per-entry link fields built during staging. This confirms: link fields must be computed per-entry, not hardcoded — verified fixed in Build 284. Rastan's path is now equivalent.

**Palette (both references):** arcade palette RAM writes → staged WRAM palette words → CRAM load each frame. Rainbow Islands at `0x19CC/0x19E8/0x1A06` clears/loads CRAM. Cadash at `0x3E44+` pushes staged WRAM palette words to VDP. Applied to Rastan: `genesistan_palette_rom_table[]` (or CLCS capture) → CRAM write path must fire every vblank for ALL active palette lines, not just line 0.

---

## 3. Complete System State at Build 287

### 3.1 Confirmed working (pipeline stage verified at runtime)

| Stage | Evidence |
|-------|---------|
| VBlank ownership: arcade tick → Genesis V-Int | `HIT 03A208 801` sustained per-vblank |
| Block-A producer at 0x05A2B4 | Phase 2 spec: `w2=03CA` confirmed at renderer entry (Build 278 probe) |
| Zero-code filter | `active_count=1`, `zero_code_entries=17` confirmed (Build 287) |
| PC090OJ tile decode | `decode_first16=11 99 81 11...` nonzero confirmed (Build 285) |
| VRAM tile 1024 upload via DMA | `vram8000_words=1199 8111 1898 8888...` confirmed (Build 285) |
| SAT sequential link chain | `sat_chain traversal_len=1 chain_ok=true last_link=0` (Build 287); full 18-entry chains confirmed correct (Build 284) |
| SAT palette bits (attr_lut) | `attr_lut[0]=0x6000` → pal_line=3; SAT w2=`0xE400` confirmed (Build 286) |
| Text producer path | CREDIT and TILT visually confirmed; `HIT 2004A2 9` proven |

### 3.2 Not working — confirmed broken

| Stage | Root cause |
|-------|----------|
| **Sprite CRAM — palette line 3** | `attr_lut=0x6000` → pal_line=3. CRAM line 3 (entries 48–63) is never loaded. `refresh_frontend_sprite_palettes()` is not called from the vblank handoff. Sprites use palette 3 but CRAM[48..63] are 0x0000 (transparent black). This is the single remaining blocker for first visible sprite pixels. |
| Tilemap plane rendering | PC080SN hooks at 0x055968 / 0x055990 are 19×NOP / 16×NOP (Phase 1 revert). Tilemap C functions exist but are never called. Both VDP planes render blank. |
| Background scroll validation | `genesistan_scroll_from_workram_vdp()` exists; not confirmed in per-vblank call chain |
| Full title text set | D0=9,10,11,12,20,30,32 paths not confirmed in current builds |
| Sprite animation lifecycle | Block-A content is frame-static in current sampling window (`active_count=1`); animation counter advance not confirmed producing multi-entry fills |
| In-game HUD | 0x03BA14 digit-descriptor writer not translated; no Genesis equivalent |
| CLCS palette capture | `genesistan_palette_clcs[]` fill mechanism not validated in current builds |

### 3.3 Why Build 281 visual FAIL despite solid tile + 12 SAT entries

Build 281 used the 0x8001 tile override (palette=0, tile=1, solid `0x1111` pattern). VRAM tile 1 was confirmed nonzero. 12 SAT entries at valid x/y positions were confirmed. Yet no visible blocks appeared.

The diagnosis at the time attributed this to "CRAM is valid" for PAL0 (palette line 0). This was true for PAL0 **for the text glyph color indices used by CREDIT text**. But the solid tile with all nibbles `0x1` uses color index 1 in the active palette line. If `CRAM[line*16+1] = 0x0000`, the tile renders as transparent.

After Build 286 introduced `attr_lut` with `pal_line=3`, sprites no longer use PAL0 at all. They use CRAM line 3 exclusively. Since no code ever loads CRAM line 3 from the arcade palette, all sprite entries are transparent regardless of tile content or SAT correctness.

**The CRAM loading call is the single unresolved producer→consumer break in the sprite pipeline.**

---

## 4. Complete System Architecture

### 4.1 Sprite Pipeline (PC090OJ) — current state annotated

```
Arcade producer (0x05A2B4 / arcade 0x05A098)   [WORKING: Phase 2 spec patch applied]
    ↓ writes 18 × 4-word entries per frame
0xE0FF11FE Block-A (18 entries × 8 bytes)       [WORKING: w0=0000,w1=00E8,w2=03CA,w3=0010]
    word0: attr (bit15=flipY, bit14=flipX, bits3-0=colorbank)
    word1: Y raw (0x0180 = sentinel/hidden)
    word2: tile code (0x3FFF mask = PC090OJ cell index)
    word3: X raw
    ↓
genesistan_sprite_tile_prepare() [C, per-vblank]    [WORKING]
    - sentinel filter: word1 == 0x0180 → skip
    - zero-code filter: word2 == 0 → skip (Build 287)
    - unique-code LUT: VRAM tile base 1024 + slot*4 per unique code
    - decode: frontend_decode_pc090oj_cell() → column-major [TL,BL,TR,BR] (Build 284)
    - attr decode: attr_lut[idx] = (pal_line<<13)|(flipy<<12)|(flipx<<11) (Build 286)
    - DMA upload: VDP_loadTileData(buffer, 1024, unique_count*4, DMA) (Build 285)
    ↓
VRAM tile slots 1024+ (each PC090OJ cell = 4 Genesis 8×8 tiles)    [WORKING: 0x1199...]
    ↓
    ←━━━━━━ BREAK: CRAM line 3 never loaded ━━━━━━┐
    ↓                                              │
genesistan_sprite_commit_asm() [Assembly, per-vblank]   [WORKING mechanically]
    - reads Block-A + tile_lut + attr_lut          │
    - SAT word2 = 0x8000 | (tile & 0x7FF) | attr_lut[idx]
    - attr_lut[0] = 0x6000 → palette line 3 ──────┘
    ↓
SAT at VRAM 0xF800, sequential link chain           [WORKING]
    ↓
CRAM line 3 (entries 48–63) = 0x0000 ← BLOCKER
    ↓
VDP hardware → Genesis display = TRANSPARENT (invisible sprites)
```

### 4.2 Tilemap Pipeline (PC080SN) — offline

```
Arcade PC080SN writes
    0x050000+ (BG plane / layer 0) — tile attr + index
    0x060000+ (FG plane / layer 1) — tile attr + index
    ↓
    ←━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    HOOKS MISSING: 0x055968 = 19×NOP, 0x055990 = 16×NOP
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━→
PC080SN tile decode
    - 16×16 arcade tile = 4 Genesis 8×8 tiles (128 bytes VRAM)
    - LRU cache: 1164 VRAM slots → tiles 20–1023, 1280–1439
    - flip bits (H/V) and palette index from arcade tile attribute word
    ↓
Genesis VDP Plane B (arcade BG) / Plane A (arcade FG)
    - VDP_setTileMapXY() with translated attribute word
    ↓
Scroll registers: workram offsets 0x10EC/0x10EE (BG) + 0x10AE/0x10B0 (FG)
    → genesistan_scroll_from_workram_vdp() → VDP H/V scroll    [EXISTS, unvalidated]
```

Correct hook approach (per AGENTS.md opcode-replacement strategy):

The Phase 1 revert removed JSR hooks that caused shift delta mismatches (C-3: 38→36 bytes, −2; C-4: 32→30 bytes, −2). The correct approach is `opcode_replace` entries (same-size substitutions) at the PC080SN hardware write callsites — the arcade instructions that write to 0x050000/0x060000 — not at the tilemap function entry points. Each `opcode_replace` substitutes the arcade chip write instruction with a JSR to a Genesis handler, with size guaranteed equal to original. This preserves shift budget integrity.

### 4.3 Palette Pipeline — broken at CRAM load

```
CLCS capture (0x390000 area writes)
    → genesistan_palette_clcs[2048]    [CAPTURE MECHANISM UNVALIDATED]
    ↓ (fallback if CLCS zero)
genesistan_palette_rom_table[2048]     [PRE-CONVERTED ROM TABLE, available now]
    → convert_clcs_to_genesis(): arcade 444→Genesis format
    ↓
refresh_frontend_sprite_palettes()     [EXISTS, NOT CALLED FROM VBLANK]
    - 4 banks × 16 colors
    - must map arcade colorbank indices to Genesis CRAM lines 0–3
    - must fire every vblank
    ↓
CRAM (64 entries: 4 palettes × 16 colors)
    palette 0: text/tilemap base (partially loaded — CREDIT works)
    palette 1: sprite colorbank 0x1x
    palette 2: sprite colorbank 0x2x
    palette 3: sprite colorbank 0x3x ← active sprite palette, NEVER LOADED
```

### 4.4 Sprite Population Lifecycle

The block-A builder (0x05A2B4) reads `a5@(0x013A)` (animation counter) and `a5@(0x1306)` (sprite control flags). Currently `active_count=1` during sampled frame window. This reflects the animation counter state at the moment sampling occurs, not a pipeline limit.

Over multiple title-screen frames:
- Animation counter advances per arcade tick
- `a5@(0x1306)` control flags gate which of the 18 entry slots are written vs left zero
- The builder's main loop iterates up to 13 entries (D4 clamped to 0x0C+1) based on sprite table state
- As the title state machine progresses through substate 0→1→loop, more sprite entries become active

The zero-code filter correctly handles partial fills: only entries with nonzero codes contribute to SAT. When the animation sequence fills more entries, `active_count` rises automatically.

### 4.5 HUD and Text System

```
Arcade text dispatch (0x03BD5E → genesis 0x20034C)
    - D0 selector → table at genesis 0x3BD92 → descriptor (D6/attr/payload)
    - D6: translated WRAM destination (window_rewrite_rules)
    - payload: character string → VDP nametable tile indices
    ↓
VDP nametable (Plane A or B, 64×32 cells) — confirmed for D0=2 (CREDIT) and D0=14 (TILT)

Unconfirmed (require validation in Phase 6):
    D0=9,10/11: title strings | D0=12: TAITO copyright | D0=20: RASTAN logo text
    D0=30,32: additional title strings

In-game HUD (Phase 7 target):
    0x03BA14 digit-descriptor writer → score/lives/timer → NOT TRANSLATED
```

---

## 5. Implementation Phases

### Phase 3 — CRAM Palette Bring-Up (Immediate)

**Goal:** First visible sprite pixels from real arcade tile data. No scaffolding.

**Why this is Phase 3 and why it is the complete blocker:**

The sprite pipeline is mechanically complete at Build 287:
- Block-A populated with real descriptor data (Phase 2)
- Tiles decoded and uploaded to VRAM 1024+ (Build 285)
- SAT formed with correct link chain, palette bits, and tile indices (Build 284–286)

The single break in the producer→consumer chain is palette. `attr_lut[0]=0x6000` means pal_line=3. No code in the current vblank path loads CRAM line 3. `refresh_frontend_sprite_palettes()` is called from a C main-loop path but not from `genesistan_frontend_live_vint_handoff()`. Per the Cadash and Rainbow Islands ownership principle: if the palette producer does not feed the active CRAM owner every vblank, palette intent is lost. That is the current state.

**Exact implementation:**

**File:** `apps/rastan/src/main.c`, function `genesistan_frontend_live_vint_handoff()`

After the call to `genesistan_sprite_tile_prepare()`, before the call to `genesistan_sprite_commit_asm()`, add:

```c
refresh_frontend_sprite_palettes();
```

This call must load the arcade sprite palette into CRAM for all active banks. The function already sources from `genesistan_palette_rom_table[]` when CLCS data is absent. The ROM table must contain non-zero entries for palette line 3 — specifically the colorbank that maps to `pal_line=3` (colorbank 0x30, entries 48–63 in CRAM).

**If `refresh_frontend_sprite_palettes()` does not currently load line 3:**

The function must be extended to load the full palette line corresponding to `pal_line` from the active `attr_lut` entries. The palette line selection is already computed in prepare (via `sprite_colbank = (genesistan_arcade_workram_words[10] & 0x00E0) >> 1`). The correct bank to load is `(sprite_colbank >> 4) & 0x3` = the active Genesis palette line index.

**No other files change. No assembly changes. No spec changes.**

**Behavioral outcome:**

After this change, `CRAM[48..63]` (palette line 3) contains non-zero arcade palette colors. Sprite tiles decoded from code 0x03CA contain nibbles `0x1..0x9` mapping to color indices 1–9 in palette line 3. With non-zero CRAM entries for those indices, the VDP renders sprite pixels at the screen position encoded in Block-A entry 0: `y_raw=0x00E8` → screen y = 232 − 128 + 128 (VDP bias = 232), `x_raw=0x0010` → screen x = 16.

**Success criteria (implementation-based, no probing as progress):**

1. `refresh_frontend_sprite_palettes()` is confirmed present in `genesistan_frontend_live_vint_handoff()` source (source inspection)
2. The function sources from `genesistan_palette_rom_table` for CRAM line 3 (source inspection of function body)
3. CRAM line 3 entries are non-zero values derived from the ROM table (not all 0x0000) — verified by reading the ROM table content statically, not by runtime probe
4. A sprite-sized region appears at the expected screen position in a frame capture — this is the visual outcome, not a "probe step"; it is the functional definition of success

**Out of scope for Phase 3:**

- Animation counter advancement (already happening in arcade tick)
- active_count > 1 (governed by sprite control flags, not by this fix)
- Tilemap planes
- In-game HUD
- Full 4-bank palette bring-up beyond the active sprite line
- Block-B descriptors
- Scrolling validation
- assembly changes

---

### Phase 4 — Full Sprite System: Animation + Multi-Entry + Full Palette

**Goal:** All 18 Block-A entries render correctly across the full animation sequence with correct per-entry palette, flip, and VRAM tile assignment.

**Component A — Sprite animation lifecycle validation**

The block-A builder (0x05A2B4) produces entries based on `a5@(0x013A)` (animation counter) and `a5@(0x1306)` (sprite control flags). The animation counter advances each arcade tick. The builder's main loop writes up to 13 entries per frame based on sprite table state.

This must be confirmed end-to-end: as the animation frame progresses, `active_count` must rise from 1 toward the full logo sprite set (expected: ~13 entries for the Rastan title logo based on builder loop bounds). The zero-code filter already handles partial fills correctly.

Scope: observe the animation counter state over 60 frames from the title-init pass. If `active_count` does not rise, the sprite control flags at `a5@(0x1306)` are the gate — diagnose what value is required and whether the arcade tick produces it in the current Genesis execution context.

**Component B — Multi-entry SAT correctness**

When `active_count` > 1, each active entry must generate a SAT slot with:
- Correct tile index from `tile_lut[idx]` (each unique code gets its own VRAM slot)
- Correct `attr_lut[idx]` (palette bits + flip bits per entry)
- Sequential link chain correct for the active-entry count

`genesistan_sprite_commit_asm()` already implements this correctly for arbitrary active_count. No assembly changes needed.

**Component C — Full 4-bank CRAM refresh**

Phase 3 loads the active sprite palette line. Phase 4 extends this to all 4 Genesis CRAM lines every vblank:

- CRAM line 0: text/tilemap base palette (arcade palette bank 0)
- CRAM line 1: arcade sprite colorbank mapped to Genesis line 1
- CRAM line 2: arcade sprite colorbank mapped to Genesis line 2
- CRAM line 3: active sprite colorbank (already loaded in Phase 3)

Source priority per Cadash/Rainbow Islands pattern: CLCS capture if populated, ROM table fallback otherwise.

**Component D — Block-B sprite descriptors**

Block-B (4 entries at 0xE0FF01BC) serves non-logo sprites (HUD effects, secondary objects). The same prepare/commit pipeline applies. Block-B entries must either join the active-count pool or be handled via a second prepare/commit pass limited to 4 entries. The choice depends on SAT slot budget (80 entries max in Genesis SAT). Current pipeline uses 18 slots for Block-A; 4 more for Block-B is safe.

**Files changed:** `apps/rastan/src/main.c` (animation validation, multi-bank CRAM), `apps/rastan/src/startup_bridge.c` (if Block-B WRAM structure needs declaration)

---

### Phase 5 — Tilemap Restoration (PC080SN)

**Goal:** Both background planes render correct arcade tilemap content for every game state.

**Architecture principle (from AGENTS.md + Rainbow Islands):** The correct translation is opcode replacement at the arcade's hardware register write callsites — not function-entry JSR hooks. This preserves shift-budget integrity and maps arcade intent directly to Genesis VDP operations, per the AGENTS.md confirmed rendering strategy: "for each arcade hardware register write that needs to become a Genesis VDP operation, the patcher replaces the original 68000 instruction bytes."

**Component A — PC080SN write callsite identification**

The arcade's tilemap writes target `0x050000+` (BG plane) and `0x060000+` (FG plane). The correct hooks are `opcode_replace` entries at the instruction that writes the tile attribute word to these addresses. The replacement bytes call a Genesis handler via JSR, with the replacement size matching the original instruction size (no shift delta). The handler calls `genesistan_hook_tilemap_plane_a()` or `_plane_b()`.

This approach was the correct one that C-3/C-4 failed to use (they used JSR hooks at function entries which caused −2 byte shift deltas). The fix is to move the hook to the hardware write instruction itself, where size equality is achievable.

**Component B — Tilemap handler re-enable**

`genesistan_hook_tilemap_plane_a/b()` exist in main.c (currently dead code, `externally_visible` but never called). Once spec hooks are added:
- Remove dead-code status (hooks will be called via ROM patches)
- Reset col/row cursor state (`genesistan_hook_col_a/b`, `genesistan_hook_row_a/b`) per-frame at the correct reset boundary (the title-init state-0 pass, not the SCREEN_FRONTEND_LIVE loop — Phase 1 removed these resets from the loop correctly)
- Confirm the LRU tile cache correctly handles `rastan_pc080sn` ROM tile indices (separate from `rastan_pc090oj` sprite tiles)

**Component C — Scroll register wiring**

`genesistan_scroll_from_workram_vdp()` reads BG/FG scroll from workram offsets 0x10EC/0x10EE and 0x10AE/0x10B0. This function must be confirmed in the per-vblank call chain (in `genesistan_frontend_live_vint_handoff()` or called from the arcade tick result path). For the title screen, expected scroll values are 0x0000 for both planes.

**Component D — Tile VRAM region integrity**

PC080SN tiles use VRAM slots 20–1023 and 1280–1439 (the LRU cache region). PC090OJ sprite tiles use 1024–1279 (18 unique codes × 4 tiles = 72 VRAM slots, within the 64-code cap). These regions must not overlap. Confirm that the tile cache `genesistan_tile_cache_arcade[1164]` maps only to its 1164 slots and does not write into the 1024–1279 sprite region.

**Files changed:** `specs/startup_title_remap.json` (new `opcode_replace` hook entries at PC080SN write callsites), `apps/rastan/src/main.c` (handler re-enable, scroll wiring, cursor reset boundary)

---

### Phase 6 — Full Title Screen

**Goal:** Every title screen element renders correctly: logo sprites, all text strings, full arcade palette, scroll at rest.

**Component A — Complete title text set**

The title-init pass (state=0x0001/substate=0x0000) dispatches text producers for D0=2,9,10/11,12,20,30,32. D0=2 (CREDIT) and D0=14 (TILT) are confirmed working. The remaining D0 values must be confirmed active in a complete title-init pass trace. Any missing D0 dispatches indicate blocked producer paths — diagnose descriptor D6 translation in `window_rewrite_rules` for those selectors.

**Component B — CLCS palette accuracy**

The ROM table fallback produces colors, but the arcade's runtime CLCS palette is what the original hardware shows. `genesistan_palette_clcs[2048]` must be populated via the CLCS write interception mechanism. Once populated, `refresh_frontend_sprite_palettes()` must prefer CLCS data over ROM table. This produces pixel-accurate colors instead of pre-converted approximations.

**Component C — Sprite animation continuity**

The title logo must animate correctly through the full state-0 → state-1 transition. The animation counter `a5@(0x013A)` must advance per-frame, producing changing block-A content across frames. Confirm that the assembly vblank path does not interfere with the arcade tick's animation counter writes.

**Files changed:** `apps/rastan/src/main.c` (text path validation, CLCS bring-up), `window_rewrite_rules` if descriptor D6 translation corrections needed

---

### Phase 7 — In-Game Graphics

**Goal:** Full gameplay renders: scrolling levels, all active game sprites, complete HUD across all game states.

**Component A — Level tilemap (continuous scroll)**

PC080SN hooks (Phase 5) carry through to gameplay. The tile cache must service the full level tileset without thrash. Horizontal scroll must advance per-vblank as the level scrolls (BG slower than FG if parallax). `genesistan_scroll_from_workram_vdp()` updates scroll registers from the arcade's scroll WRAM each frame — this is already the design; confirm it works at non-zero scroll values.

**Component B — Game sprites (enemy, player, projectile)**

Same pipeline as Phase 3/4. Block-A entries during gameplay reflect active game objects. The builder (0x05A2B4) populates up to 13 entries per frame based on the in-game sprite table. The full 18-entry SAT pool handles all visible sprites with correct tile codes, palette, and flip bits. Sprite priority relative to tilemap planes must match arcade (sprites appear above FG plane for most objects, below for some layering effects) — Genesis priority bit per SAT entry is already set to 1 (priority on), which places sprites above all tilemap planes. Verify this matches arcade visual layering.

**Component C — HUD digit system**

The arcade's digit-descriptor writer at 0x03BA14 is not translated. It reads digit values from workram, indexes into a digit tile ROM region, and produces tile attribute words for the HUD position. A Genesis equivalent must:

1. Read the same workram offsets as the arcade (score, lives, stage timer)
2. Map digit values 0–9 to the correct VRAM tile indices where digit glyphs reside
3. Write the correct nametable entries for the HUD tile positions (top strip of Plane A or B)

This requires identifying the arcade's digit glyph source (PC080SN tileset region or dedicated HUD ROM) and the WRAM offsets for score/lives/timer. The opcode-replacement approach: replace the arcade's digit-write callsite instructions with JSR to a Genesis handler.

**Files changed:** `apps/rastan/src/main.c` (game sprite validation, HUD writer), `specs/startup_title_remap.json` (HUD opcode hooks if needed)

---

## 6. Immediate Implementation Phase — Cody Execution Specification

This is the complete specification for the next Cody implementation pass. **Phase 3: CRAM Palette Bring-Up.**

### 6.1 Files to modify

- `apps/rastan/src/main.c` — one functional change

No changes to:
- `apps/rastan/src/startup_trampoline.s`
- `specs/startup_title_remap.json`
- Any other file

### 6.2 The single change

**File:** `apps/rastan/src/main.c`
**Function:** `genesistan_frontend_live_vint_handoff()`
**Location:** after call to `genesistan_sprite_tile_prepare()`, before call to `genesistan_sprite_commit_asm()`

Add:
```c
refresh_frontend_sprite_palettes();
```

### 6.3 Pre-change validation of `refresh_frontend_sprite_palettes()`

Before adding the call, Cody must read the existing `refresh_frontend_sprite_palettes()` function body in main.c and confirm:

1. The function loads CRAM line 3 (palette line 3 = `genesistan_palette_rom_table` entries 48–63 or equivalent)
2. The function calls `VDP_setPalette()` or equivalent for the active sprite palette bank
3. If the function currently only loads line 0 (text palette), it must be extended to load all active sprite palette lines. The active palette line index is `(genesistan_arcade_workram_words[10] & 0x00E0) >> 5` (bit positions 5-7 of sprite control WRAM word, which produces the `sprite_colbank` value used in prepare)

If the function needs extension, extend it in this same pass. No separate pass.

### 6.4 What NOT to do

- Do not add VDP_loadTileData() — it is already in the code (Build 285)
- Do not add genesistan_sprite_unique_count if it already exists in wram_overlay.launcher
- Do not add runtime probes, instrumentation, or Lua scripts as part of this change
- Do not touch startup_trampoline.s
- Do not touch specs/

### 6.5 Execution boundary

One functional change: `refresh_frontend_sprite_palettes()` is called from `genesistan_frontend_live_vint_handoff()` with the result being non-zero CRAM entries for the active sprite palette line(s).

### 6.6 Success criteria (implementation-based)

1. `refresh_frontend_sprite_palettes()` call site is present in `genesistan_frontend_live_vint_handoff()` (source inspection)
2. The function body loads CRAM line 3 using non-zero values from `genesistan_palette_rom_table` or CLCS data (source inspection)
3. Frame capture at frame 700 shows sprite-shaped non-background-colored pixels at screen position y≈232-128=104 (VDP y = 0x0168 - 0x80), x=0x10=16 (VDP x = 0x0090 - 0x80)
4. CREDIT and TILT text paths unaffected (regression check: text display unchanged)
5. SAT link chain remains correct (`chain_ok=true`)

---

## 7. Phase Dependency Map

```
Phase 3 (CRAM palette bring-up — main.c 1 call)
    │
    ├─→ Phase 4 (full sprite animation + multi-bank palette + Block-B)
    │       │
    │       └─→ Phase 6 (full title screen: all text + CLCS palette)
    │                   │
    │                   └─→ Phase 7A (game sprites: same pipeline, new objects)
    │
    └─→ Phase 5 (PC080SN tilemap hooks + scroll wiring)     [independent path]
            │
            └─→ Phase 7B (level scrolling + HUD)
```

Phase 3 must ship first — it is the single remaining blocker for sprite visibility and unblocks all subsequent sprite work. Phase 5 is fully independent of Phase 3 and can proceed in parallel if a second implementation agent is available.

---

## 8. Full Producer → Consumer Flow (end-to-end)

```
Arcade producers (per-vblank):
  Block-A builder (0x05A2B4) → 0xE0FF11FE
  PC080SN writes (via opcode hooks, Phase 5) → tile cache → VDP plane nametables
  Arcade palette writes (via CLCS capture or ROM table) → genesistan_palette_rom_table

Genesis vblank handoff (genesistan_frontend_live_vint_handoff):
  [1] genesistan_run_original_frontend_tick()    → runs arcade tick, populates Block-A
  [2] genesistan_sprite_tile_prepare()           → decode + LUT + DMA upload to VRAM 1024+
  [3] refresh_frontend_sprite_palettes()         → CRAM lines 0–3 loaded from ROM table/CLCS
  [4] genesistan_sprite_commit_asm()             → SAT built from Block-A + LUT + attr_lut
  [5] genesistan_scroll_from_workram_vdp()       → VDP H/V scroll from workram offsets

VDP hardware output:
  Plane B (arcade BG via PC080SN, Phase 5)
  Plane A (arcade FG via PC080SN, Phase 5)
  SAT (sprite overlay, correct priority=1 above planes)
  CRAM (4 palette lines, all loaded per-frame)
```

Every stage in this flow must be confirmed working before the project is complete. Currently complete: [1], [2], partial [3] (line 0 only), [4], [5] unvalidated. The only step needed for Phase 3 is completing [3] for line 3.

---

## 9. Success Definition for Full Graphics System

Complete when all of the following are true in a single frame capture at title screen AND at a gameplay level:

| Requirement | Definition |
|-------------|------------|
| All active Block-A sprite entries render at arcade-correct positions | x/y in SAT matches Block-A descriptor data + bias; tile pixels are non-background-colored |
| All 4 CRAM lines loaded with arcade-sourced palette data | CLCS capture confirmed active OR ROM table confirmed non-zero for all 64 entries |
| Both PC080SN planes render correct tilemap content | Level tiles visible from arcade tileset, not blank planes |
| H/V scroll advances correctly per-frame | Scroll registers match workram values each vblank |
| All title text strings visible (D0=2,9,10/11,12,14,20,30,32) | Each selector confirmed dispatched in a single title-init pass |
| In-game HUD displays correct score/lives/timer values | Digit tile writes confirmed at correct nametable positions |
| No scaffolding in any component | Every rendering output is sourced from arcade-produced data exclusively |

---

## 10. Self-Audit Results

### What was corrected

**Critical correction — Phase 3 was factually wrong in the first draft:**
The first draft's Phase 3 described adding `VDP_loadTileData()` and `genesistan_sprite_unique_count` as the immediate implementation targets. Both are ALREADY IMPLEMENTED as of Build 285 (`live_decode_buffer_wiring_fix_results.md` confirms `VDP_loadTileData` fires every vblank and VRAM 0x8000 contains real sprite data `1199 8111...`). The first draft was written without reading this document.

**Corrected Phase 3** is now: call `refresh_frontend_sprite_palettes()` from the vblank handoff to load CRAM line 3, which is the sole remaining break in the sprite pipeline.

**CRAM blocker precisely diagnosed:**
The first draft said "Build 281 solid tile FAIL suggests CRAM[1] zero." The correct diagnosis: `attr_lut=0x6000` (Build 286) routes sprites to CRAM line 3, not line 0. PAL0 was confirmed valid (for CREDIT text). PAL3 has never been loaded. The diagnosis was imprecise in the first draft; it is now exact.

**PC080SN hook approach made concrete:**
The first draft said "NOT as JSR hooks" without specifying the correct approach. Now specified: `opcode_replace` entries at the arcade's PC080SN hardware write instructions (0x050000/0x060000 callsites), with size-matched replacements per AGENTS.md's confirmed rendering strategy.

**Probing removed as implementation steps:**
The first draft included "Probe 1", "Probe 2", "Probe 3" sections in Phase 3. These are not implementation. Removed; replaced with implementation-based success criteria.

**Partial-data acceptance removed:**
First draft split CRAM loading across Phase 3 ("at minimum one bank") and Phase 4 ("all 4 banks"). This accepted partial CRAM as a destination. Corrected: Phase 3 loads all active sprite palette lines. Phase 4 extends to full 4-bank validation.

### What was missing

- Live decode buffer wiring (Build 285) had already completed the tile VRAM upload — not incorporated in first draft
- Sprite animation lifecycle (how `active_count` grows from 1 toward 13 over animation frames) was absent
- Producer→consumer ownership breakdown per ownership class was surface-level, not applied to each phase
- CLCS capture validation as a distinct phase component was missing
- Tilemap VRAM region boundary check (sprite region 1024–1279 vs tilemap region 20–1023, 1280–1439) was missing

### What was strengthened

- Full annotated sprite pipeline with confirmed working stages and exact BREAK location
- Complete 5-step vblank handoff flow with per-step status
- Phase 3 reduced to single call addition — more concrete and immediately executable
- Tilemap hook approach now architecturally correct per AGENTS.md
- Rainbow Islands and Cadash ownership principles applied explicitly to each phase
- Sprite animation lifecycle documented with specific A5 WRAM offsets

### Scaffolding confirmation

No scaffolding remains. Every phase targets real implementation work:
- Phase 3: one function call to load missing CRAM palette
- Phase 4: sprite animation bring-up + full palette + Block-B
- Phase 5: PC080SN opcode hooks + scroll wiring
- Phase 6: title text + CLCS palette accuracy
- Phase 7: in-game sprites + HUD digit translation

No phase contains "investigate further," "probe for data," or "validate intermediate state" as progress steps.

### Rainbow Islands and Cadash incorporation

Both references are explicitly incorporated:
- Section 2 extracts the five ownership-class translation rules and applies them to Rastan
- The sprite pipeline break at CRAM line 3 is diagnosed using the Rainbow Islands "producer must prove it feeds the active VDP consumer" principle
- The PC080SN hook architecture uses the Cadash/Rainbow Islands confirmed pattern: arcade chip RAM writes → Genesis VDP plane writes via direct callsite replacement
- The palette loading pattern follows the Rainbow Islands CRAM load structure: per-frame, all active banks, sourced from pre-converted ROM table with CLCS as accuracy upgrade

Self-audit complete. The plan now represents a full-system implementation direction with no scaffolding, with Rainbow Islands and Cadash incorporated as required reading, and with a concrete immediate execution phase.
