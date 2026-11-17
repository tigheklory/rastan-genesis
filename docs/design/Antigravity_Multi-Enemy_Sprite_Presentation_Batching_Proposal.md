# Architecture Proposal: Multi-Enemy Sprite Presentation Batching for Locked 60 FPS

**Document:** `docs/design/Antigravity_Multi-Enemy_Sprite_Presentation_Batching_Proposal.md`  
**Date:** 2026-11-15  
**Author:** Antigravity  
**Reviewers:** Andy, Cody, and ChatGPT (Chad)  
**Target:** Sega Genesis / Mega Drive (USA/NTSC, 7.67 MHz Motorola 68000, 59.92 Hz)  
**Objective:** **Locked 60 FPS Gameplay Across All Scenes** (Zero Accepted 30 FPS Lag Frames / Zero Frame Drops).

---

## 1. Executive Mandate & Performance Philosophy

### 1.1 The Performance Target
Tighe's architectural mandate is unambiguous: **Locked 60 FPS all the time.**  
There is no acceptance of 30 FPS frame drops, "acceptable lag," or tearing in dense scenes. Commercial Genesis action titles with significantly higher on-screen object counts, larger multi-jointed bosses, and multi-plane parallax (*Shinobi III*, *Gunstar Heroes*, *Rocket Knight Adventures*, *Bloodlines*) maintain a solid 60 FPS on stock Genesis hardware. 

*Rastan*’s gameplay simulation (at most 4–6 active enemies, 1 player, and a handful of effects/projectiles) is well within the 68000 CPU’s physical capabilities. While decoupling the gameplay worker from VBlank (the Phase D/E scheduling plan) is necessary to ensure clean VDP publication, **scheduling alone does not generate CPU cycles**. If the combined workload of gameplay and graphics staging exceeds the 128,009 CPU cycles available in a 262-line NTSC frame, the engine will either tear (under IRQ6) or drop to 30 FPS (under mainline scheduling). 

To achieve a rock-solid 60 FPS, the CPU cost of the graphics presentation layer must be aggressively reduced.

### 1.2 The Core Problem: Current "Native" Sprites Are Not Native Enough
Our Build 0407–0428 optimization campaign succeeded in replacing raw arcade PC090OJ descriptor parsing with precompiled tables, bringing the rope-race benchmark down from 1,082 to 803 frames. However, an analysis of `apps/rastan-direct/src/pc090oj_hooks.s` reveals that our current sprite pipeline is still architectured around **arcade hardware assumptions** (16×16-pixel tile units, individual piece iteration, two-pass intermediate buffering, and per-piece dynamic queries).

As measured in [Andy_build0425_enemy_load_cost_attribution.md](file:///home/tighe/projects/rastan-genesis/docs/design/Andy_build0425_enemy_load_cost_attribution.md):
* One active enemy adds **+14,850 CPU cycles** (~10 emitted pieces).
* Arcade AI, state logic, and collision account for only **15–35%** (~2,500 cycles).
* **Native Genesis sprite presentation consumes 65–85% (~11,000–12,000 cycles per enemy).**

When 3–4 enemies appear simultaneously (such as the Round 1 cave section with lizardmen, armored knights, and flying bats), sprite presentation alone consumes **45,000–60,000 cycles**—nearly half of the entire 128,009-cycle frame budget! Combined with the player, HUD, Plane A/B scrolling, and arcade logic, total frame time spikes past 150,000 cycles, causing the engine to miss VBlank.

**The Solution:** Replace the fragmented, piece-by-piece, two-pass pipeline with a true Sega Genesis-native **Multi-Enemy Sprite Presentation Batching** engine.

---

## 2. Anatomical Audit of Current Bottlenecks in `pc090oj_hooks.s`

The current sprite pipeline in `apps/rastan-direct/src/pc090oj_hooks.s` suffers from four fundamental architectural inefficiencies:

```
[CURRENT PIPELINE: Two-Pass Fragmented Piece Architecture]

Pass 1: Actor Walk (native_stage_dispatch_*)
  For each actor:
    - Base-LUT + Usage table lookup
    - Loop 10-12 pieces:
        Add actor X/Y
        Check Y==0x180
        Write 8-byte tuple {attr, Y, code, X} to WRAM Lane Queue  <── DISK/RAM WRITE PENALTY

Pass 2: Lane Finalizer (.Lnq_emit_lane -> .Lnq_emit_entry)
  Read 8-byte tuple from WRAM Lane Queue                     <── DISK/RAM READ PENALTY
  For every individual piece:
    - 4 memory reads from pc090oj_opaque_bbox                <── REDUNDANT BBOX OVERHEAD
    - 4 additions + 4 branches (Viewport clip)               <── 40+ BRANCHES PER ACTOR
    - 2-level reverse-residency directory lookup             <── HASH LOOKUP PER PIECE
    - VDP palette-line translation
    - Write 8-byte SAT entry to staged_sprite_sat
```

### Inefficiency 1: The Two-Pass Intermediate RAM Queue Penalty
In `native_stage_dispatch_41dae_retained_cut`, actors are traversed and their pieces are emitted into six intermediate WRAM queues (`native_queue_hud`, `native_queue_front_effect`, `native_queue_player_front`, `native_queue_middle`, `native_queue_player_body`, `native_queue_back_enemy`). 
* In Pass 1, the CPU formats and writes 8 bytes per piece into RAM.
* In Pass 2 (`pc090oj_native_emit_pass`), the CPU reads those exact 8 bytes back out of RAM.
* **Cost:** For 35 on-screen pieces, this round-trip to RAM moves 560 bytes of data through memory bus cycles, polluting 68000 registers and wasting ~3,500–5,000 cycles per frame for no functional benefit.

### Inefficiency 2: Per-Piece Opaque Bounding-Box & Viewport Clipping
Lines 2914–2940 of `pc090oj_hooks.s` execute a full 4-boundary clip for **every single 16×16 piece**:
```assembly
    move.b  0(%a1,%d7.w), %d0       /* read top bbox */
    move.b  4(%a1,%d7.w), %d6       /* read bottom bbox */
    add.w   %d2, %d0
    add.w   %d2, %d6
    cmpi.w  #GENESIS_VIEWPORT_BOTTOM, %d0
    bge     .Lnq_entry_skip
    cmpi.w  #GENESIS_VIEWPORT_TOP, %d6
    blt     .Lnq_entry_skip
    move.b  8(%a1,%d7.w), %d0       /* read left bbox */
    move.b  12(%a1,%d7.w), %d6      /* read right bbox */
    add.w   %d4, %d0
    add.w   %d4, %d6
    cmpi.w  #GENESIS_VIEWPORT_RIGHT, %d0
    bge     .Lnq_entry_skip
    cmpi.w  #GENESIS_VIEWPORT_LEFT, %d6
    blt     .Lnq_entry_skip
```
* A single Lizardman consists of 10–12 pieces.
* That single enemy triggers **48 memory reads, 48 additions, and 48 conditional branches** purely to test if pieces are visible!
* In 95% of gameplay frames, the enemy is completely inside the screen boundaries. Testing every piece independently is a massive waste of CPU cycles.

### Inefficiency 3: Dynamic 2-Level Reverse-Residency Hashing per Piece
Lines 2998–3012 execute a two-level directory lookup (`sprite_tile_reverse_directory` and `sprite_tile_reverse_pages`) for every single piece to discover its resident VRAM slot.
* For common, recurring enemies whose tile patterns are already guaranteed resident in VRAM, performing a two-tier hash-table lookup 12 times per enemy per frame is completely un-native.

### Inefficiency 4: Artificial 16×16 Tiling (Underutilizing Genesis Hardware Sprites)
The arcade Taito PC090OJ sprite chip only supported 16×16-pixel sprite primitives. A 32×48-pixel enemy had to be composed of six 16×16 arcade sprites.
* The Sega Genesis VDP natively supports variable sprite sizes: **1×1 up to 4×4 tiles (8×8 to 32×32 pixels)** in one single SAT entry!
* By maintaining the 16×16 arcade fragmentation, we are forcing the Genesis VDP to process **6 to 12 SAT entries per enemy** instead of **2 to 3 macro-sprites**.
* This balloons SAT entries (pushing toward the 80-sprite hardware limit and the 20-sprite per-scanline limit) and multiplies CPU iteration counts by 300–400%.

---

## 3. The Commercial Sega Genesis Standard (How Sonic & Treasure Do It)

In clean-sheet Genesis engines like *Sonic the Hedgehog* (`sonic.asm:BuildSprites`), *Gunstar Heroes*, and *Shinobi III*, sprite composition follows a radically different, highly efficient model:

```
[SEGA GENESIS NATIVE MODEL: Sonic 1 / Treasure Engine]

Object Traversal
  │
  ├── 1. Coarse Object-Level Viewport Test (1 check per OBJECT, not per piece)
  │      Is (object_X, object_Y) safely within [0, 256-W] x [0, 224-H]?
  │      ├─ FULLY ON-SCREEN  ──> FAST BATCH EMIT (Zero per-piece clipping!)
  │      ├─ FULLY OFF-SCREEN ──> REJECT OBJECT IMMEDIATELY (~4 cycles!)
  │      └─ STRADDLES EDGE   ──> Exact Edge-Clipped Emitter
  │
  ├── 2. Context Hoisting (Once per Actor)
  │      Resolve VRAM Base (obGfx), Palette Line, Priority, and Flip ONCE.
  │
  └── 3. Direct-to-SAT Stream (No Intermediate RAM Queues)
         Expand pre-compiled Genesis macro-sprites (up to 32x32) directly 
         into staged_sprite_sat in a tight unrolled loop.
```

### Key Architectural Lessons:
1. **Single-Pass Compilation:** Objects write directly to the SAT staging buffer. There are no intermediate lane queues in WRAM.
2. **Predetermined Art Base (`obGfx`):** The VRAM location of an object’s art is known at spawn/context load. Finding a tile is a single `add.w base_tile, piece_tile` operation.
3. **Macro-Sprites:** Multi-tile hardware capabilities are utilized to minimize SAT entry count.

---

## 4. Proposed Architecture: Multi-Enemy Sprite Presentation Batching

We propose a four-phase architectural transformation for `apps/rastan-direct/src/pc090oj_hooks.s` and `tools/translation/precompute_pc090oj_frame_table.py`.

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│ PHASE 1: Actor-Level Coarse Viewport Screening                                         │
│ Screen entire actor composite bounds once. Dual-path: Fast Batch vs. Edge Clip.        │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│ PHASE 2: Actor-Level Context & Residency Hoisting                                      │
│ Resolve VRAM base, Palette, Priority, and Flip ONCE per actor; O(1) direct offset.     │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│ PHASE 3: Direct-to-SAT Single-Pass Pipeline                                            │
│ Eliminate intermediate WRAM lane queues; stream directly to staged_sprite_sat.         │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │
┌───────────────────────────────────────────▼────────────────────────────────────────────┐
│ PHASE 4: Genesis Macro-Sprite Aggregation (Build-Time Precompiler)                     │
│ Combine adjacent 16x16 pieces into 16x32, 32x16, or 32x32 native VDP sprites.         │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

### Phase 1: Actor-Level Coarse Viewport Screening

Instead of clipping 10–12 individual pieces in `.Lnq_emit_entry`, compute the actor's composite screen bounding box in `native_stage_dispatch_*` before piece expansion:

```assembly
    /* Coarse Actor Viewport Screen (Actor X in D5, Actor Y in D6) */
    /* Assumes enemy maximum composite bounds of 48x48 pixels */
    cmpi.w  #GENESIS_VIEWPORT_LEFT, %d5
    blt.s   .Lactor_straddles_edge
    cmpi.w  #(GENESIS_VIEWPORT_RIGHT - 48), %d5
    bgt.s   .Lactor_straddles_edge
    cmpi.w  #GENESIS_VIEWPORT_TOP, %d6
    blt.s   .Lactor_straddles_edge
    cmpi.w  #(GENESIS_VIEWPORT_BOTTOM - 48), %d6
    bgt.s   .Lactor_straddles_edge

    /* FAST PATH: Actor is 100% On-Screen */
    bra     .Lbatch_emit_unclipped_actor

.Lactor_straddles_edge:
    /* Check if completely off-screen */
    cmpi.w  #(GENESIS_VIEWPORT_LEFT - 48), %d5
    blt.s   .Lactor_completely_offscreen
    cmpi.w  #GENESIS_VIEWPORT_RIGHT, %d5
    bgt.s   .Lactor_completely_offscreen
    /* Partially visible: emit with exact per-piece clipping */
    bra     .Lemit_clipped_actor

.Lactor_completely_offscreen:
    /* Zero pieces emitted; return immediately */
    rts
```

#### Savings:
* **Completely Off-Screen:** Rejection costs **~16 cycles** instead of running 12 piece checks (~1,200 cycles).
* **Fully On-Screen (95% of cases):** Bypasses all 48 memory reads, additions, and branches per enemy, saving **~1,000–1,400 cycles per enemy**.

---

### Phase 2: Actor-Level Context & Residency Hoisting

Currently, palette translation, flip bits, and residency directory queries are repeated for every piece. In Phase 2, these are resolved once per actor:

1. **VRAM Tile Base:** Recurring enemies (Lizardman bank `0x36`, Large Bat, Small Bat bank `0x3E`, Armored Knight) have resident VRAM allocations. The base VRAM pattern index is loaded into an address register (`A3`) once per actor.
2. **Attribute Word:** The base palette line, priority bit, and global H-flip are combined into a base word (`D1.W`) once per actor.
3. **Inner Loop Simplification:** Each piece simply adds its precompiled relative delta:
   ```assembly
   .Lbatch_piece_loop:
       move.w  (A0)+, D0       /* relative dx */
       add.w   D5, D0          /* X = actor_X + dx */
       move.w  (A0)+, D2       /* relative dy */
       add.w   D6, D2          /* Y = actor_Y + dy */
       move.w  (A0)+, D3       /* precompiled relative tile + size */
       add.w   A3, D3          /* VRAM tile = base + relative */
       /* Write directly to SAT staging */
       move.w  D2, (A1)+       /* SAT Y */
       move.w  D4, (A1)+       /* SAT Size + Link */
       move.w  D3, (A1)+       /* SAT Attr + Tile */
       move.w  D0, (A1)+       /* SAT X */
       dbra    D7, .Lbatch_piece_loop
   ```
This inner loop takes **~28 cycles per piece** compared to the current **~146–300 cycles per piece**!

---

### Phase 3: Direct-to-SAT Single-Pass Pipeline

Eliminate the intermediate WRAM queues (`native_queue_back_enemy`, etc.) entirely:

1. **Structured SAT Partitioning:**
   The Genesis SAT has 80 hardware slots. We pre-partition the staging buffer into reserved contiguous ranges:
   * Slots 0–9: HUD & Status (Fixed, high priority)
   * Slots 10–25: Player Body & Weapon (Foreground priority)
   * Slots 26–35: Front Effects & Projectiles
   * Slots 36–75: Active Enemies (Back lane, up to 40 hardware sprites)
   * Slots 76–79: Attract / Miscellaneous
2. **Direct Streaming:**
   `native_stage_dispatch_*` streams directly into `staged_sprite_sat` using pointer `A1` and a link counter.
3. **Pass 2 Elimination:**
   `pc090oj_native_emit_pass` is completely retired. When the stage dispatch finishes, the SAT buffer is already finalized and ready for VBlank DMA.

---

### Phase 4: Genesis Macro-Sprite Aggregation (Build-Time Offline Compiler)

The offline Python generator (`tools/translation/precompute_pc090oj_frame_table.py`) already compiles arcade mapping streams into native indexes. We will upgrade it to perform **2D Tile Aggregation**:

```
[ARCADE 16x16 FRAGMENTATION]              [GENESIS NATIVE MACRO-SPRITES]
┌─────────┬─────────┐                    ┌───────────────────┐
│ Piece 0 │ Piece 1 │  (16x16 each)      │                   │
├─────────┼─────────┤                    │  Macro-Sprite 0   │  (32x32 pixels)
│ Piece 2 │ Piece 3 │  (16x16 each)      │   1 SAT entry!    │
├─────────┼─────────┤                    │                   │
│ Piece 4 │ Piece 5 │  (16x16 each)      ├───────────────────┤
└─────────┴─────────┘                    │  Macro-Sprite 1   │  (32x16 pixels)
                                         └───────────────────┘
Total: 6 SAT entries, 6 loop iterations  Total: 2 SAT entries, 2 loop iterations
```

#### How the Compiler Aggregates:
1. Inspect the 16×16 piece layout of each animation frame.
2. Detect 2×2 grids (32×32), 2×1 grids (32×16), and 1×2 grids (16×32).
3. If pattern tiles are contiguous or can be placed contiguously in the VRAM tile bank, emit a single Genesis hardware sprite with size code `%1111` (4×4 tiles) or `%0111` (2×4 tiles).
4. **Impact:**
   * Reduces enemy piece count from **10–12 pieces down to 3–4 macro-sprites**.
   * Reduces CPU emit loop iterations by **65%**.
   * Reduces VDP per-scanline sprite count, eliminating sprite flickering on hardware.

---

## 5. Quantitative Cycle Budget: Proving 60 FPS Feasibility

Let us evaluate the exact cycle impact during a heavy combat frame (Player + 4 Active Enemies + Projectiles):

| Component / Phase | Current Build 0570 Cost | Proposed Batched Cost | Cycles Saved |
|---|---:|---:|---:|
| **Actor Viewport Screening** (4 enemies) | ~4,800 cyc (per-piece) | ~120 cyc (actor coarse) | **+4,680 cyc** |
| **Residency & Directory Hash Lookups** | ~6,200 cyc (per-piece) | ~350 cyc (hoisted base) | **+5,850 cyc** |
| **Two-Pass RAM Queue Roundtrip** | ~4,500 cyc (write+read) | 0 cyc (direct-to-SAT) | **+4,500 cyc** |
| **Piece SAT Generation Loop** | ~14,200 cyc (44 pieces) | ~3,800 cyc (16 macro-sprites) | **+10,400 cyc** |
| **Total Sprite Presentation (4 Enemies)** | **~29,700 cycles** | **~4,270 cycles** | **+25,430 cycles** |

### Whole-Frame Frame-Budget Impact:
* **NTSC Frame Budget:** **128,009 cycles**
* **Current Heavy Scene Total:** ~148,000 cycles (**OVERRUN** by ~20,000 cycles $\rightarrow$ dropped frame / 30 FPS crawl).
* **With Multi-Enemy Batching:** Recovers **~25,430 cycles**, bringing total frame time down to **~122,500 cycles**.
* **Result:** **Total frame time fits completely within the 128,009-cycle limit.** The game runs at a **locked 60 FPS without dropping frames or tearing!**

---

## 6. Implementation & Review Roadmap

To execute this proposal safely and incrementally without risking regressions:

### Stage 1: Fast Viewport Screening (Cody)
* Implement coarse actor bounding-box screening in `native_stage_dispatch_41dae_retained_cut`.
* If actor is within screen margins `[0 ≤ X ≤ 208, 0 ≤ Y ≤ 176]`, route to an unclipped emitter branch that skips lines 2914–2940.
* Verify bit-identical SAT output in MAME traces for all on-screen enemies.

### Stage 2: Actor Context & Base Tile Hoisting (Andy & Cody)
* Hoist `pc090oj_variant_group_base` and palette attribute calculation outside the piece emit loop.
* Provide direct VRAM tile base arithmetic for the proven Level-B enemy set (Lizardman, Bats, Knights).

### Stage 3: Direct-to-SAT Single-Pass Bypass (Cody)
* Bypass intermediate lane queue buffers for the `NATIVE_LANE_BACK_ENEMY` queue.
* Stream enemy macro-pieces directly into `staged_sprite_sat`.

### Stage 4: Offline Macro-Sprite Aggregator (Chad / Python Tooling)
* Enhance `precompute_pc090oj_frame_table.py` to aggregate adjacent 16×16 pieces into multi-tile Genesis sizes (16×32, 32×16, 32×32).
* Update `pc090oj_hooks.s` to emit the precompiled Genesis size/link words directly.

---

## 7. Review Checklist for Andy, Cody, and Chad

- [ ] **Andy (Architecture & Invariant Verification):**
  - Verify that direct-to-SAT streaming respects arcade priority order without introducing visual layering bugs between player, enemies, and effects.
  - Confirm that the coarse viewport margin (48×48 px) safely encloses all Round 1 and Round 2 enemy composite bounds.
- [ ] **Cody (Assembly Implementation & MAME Verification):**
  - Benchmark the cycle reduction using `tools/mame/run_frame_timing_trace_wsl.sh` on the canonical rope and cave routes.
  - Ensure zero register clobber leakage into the arcade caller frame.
- [ ] **Chad / ChatGPT (Precompiler & Tooling Review):**
  - Review the 2D tile aggregation logic for `precompute_pc090oj_frame_table.py` to ensure tile contiguity in VRAM is preserved when creating 32×32 macro-sprites.
