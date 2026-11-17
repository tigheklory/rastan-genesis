# Genesis-Native Performance Optimization: Historical Synthesis, Bottleneck Theories, and Architectural Roadmap

**Date:** 2026-11-14  
**Type:** ARCHITECTURAL SYNTHESIS / ROADMAP (Read-only research and design; no ROM produced, no production code modified).  
**Target Audience:** Cody and Andy (Reference Guide for Genesis Performance Engineering).  
**Evidence Basis:** Exhaustive review of `/docs/design`, empirical MAME physical-beam profiling traces (Builds 0354–0356, 0411, 0414, 0425), historical rope-race benchmark ledgers (Builds 0282–0439), and commercial Mega Drive engine disassemblies (*Sonic 1*, *Rainbow Islands*, *Gunstar Heroes*, *Shinobi III*, *Thunder Force IV*, *Cadash*).

---

## 1. Executive Summary

Between Build 0282 (first benchmarked Genesis build) and Build 0428/0439, the Genesis port of *Rastan* underwent an extensive native optimization campaign. The canonical rope-race benchmark improved from **1,082 frames** down to **803 frames**, plateauing just **+32 frames (+4.15%)** above the arcade ground truth reference of **771 frames** (12,850 ms).

```
   1,100 ┼── B0282 (1,082 fr)
         │
   1,000 ┼────────────── B0407 (997 fr - pure-native sprite closeout)
         │                    B0411 (978 fr - SAT/bitset scan; worker < 128k avg)
     900 ┼───────────────────────── B0412 (949 fr - HUD fast queue)
         │                              B0419 (878 fr - fused visual+collision)
     800 ┼─────────────────────────────────── B0424 (817 fr) ── B0428 (803 fr plateau)
         │                                                      Arcade Reference (771 fr) ───
     700 ┴─────┴─────────────┴─────────────┴─────────────────┴───────────────────┴──
            Jul '26       Aug '26       Sep '26           Oct '26               Nov '26
```

However, real-hardware testing and frame-timing traces reveal that in dense combat scenes (e.g. cave section with multiple lizardmen, armored warriors, and flying bats) or during complex multi-directional scrolling, the Genesis version continues to experience **frame drops, effective frame-rate degradation down to ~40–45 Hz, and scanout overruns**.

The primary conclusion of this synthesis is:
1. **Graphics translation is already 80–95% Genesis-native.** Background metatiles and sprite piece expansion are no longer the primary architectural bottleneck.
2. **The single dominant bottleneck is structural scheduling:** *Rastan* executes the **entire gameplay worker, object simulation, physics, collision, and graphics staging inside the Level-6 VBlank Interrupt (IRQ6) at IPL7**.
3. **Decoupling the gameplay worker from IRQ6 into the mainline (Phase D / Phase E scheduling)** is the single highest-leverage architectural change available. It matches every high-performance commercial Genesis title and prevents over-budget frames from blocking VINT or tearing into active scanout.

---

## 2. Chronological Evolution of Performance Understanding

Understanding how the project's performance mental model evolved prevents repeating disproven hypotheses and shows why certain solutions were adopted:

| Era / Date | Milestone Builds | Prevailing Theory / Focus | Breakthrough / Empirical Finding | Document References |
|---|---|---|---|---|
| **Early Era**<br>(Spring–July 2026) | 0001–0282 | Emulate arcade chips via software mirrors; C-window shadows. | Huge memory footprint and massive execution overhead; rope race at 1,082 frames. | `startup_title_remap_plan.md` |
| **July 2026** | 0130–0193 | Tearing and black rolling band caused by VRAM/DMA bandwidth starvation. | Implemented `DISPLAY_OFF` blanking bands to hide overrun. Realized band straddles active scanout. | [Andy_deterministic_one_frame_presentation_pipeline_design.md](file:///home/tighe/projects/rastan-genesis/docs/design/Andy_deterministic_one_frame_presentation_pipeline_design.md) |
| **Late July 2026** | Policy Established | Software chip emulation is an architectural dead end. | **Tighe Imperative:** Cut at highest semantic boundary; direct Genesis VDP/SAT output. | [PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md](file:///home/tighe/projects/rastan-genesis/docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md) |
| **Sept 2026** | 0337–0359 | Joint Frame-Timing Investigation (Build 0356). | **Physical beam measurement in MAME:** VBlank publication is only **6.2 scanlines (1.85%)**; CPU continuation is **322.6 scanlines (1.23 frames)**. 74.3% Case C masked continuation. | [CODY_MEASUREMENTS.md](file:///home/tighe/projects/rastan-genesis/docs/design/joint_build0356_frame_timing_investigation/CODY_MEASUREMENTS.md), [Andy_build0359_performance_triage.md](file:///home/tighe/projects/rastan-genesis/docs/design/Andy_build0359_performance_triage.md) |
| **Early Oct 2026** | 0407–0413 | Native Sprite Assembly Blitz. | Hoisted SAT word generation; 6-byte used-bit scanning; HUD fast queue. Worker avg dropped to 126k cycles (<128k budget). | [Cody_build0407_native_sprite_performance_optimization.md](file:///home/tighe/projects/rastan-genesis/docs/design/Cody_build0407_native_sprite_performance_optimization.md), [Cody_build0411_native_worker_one_frame_optimization.md](file:///home/tighe/projects/rastan-genesis/docs/design/Cody_build0411_native_worker_one_frame_optimization.md) |
| **Mid Oct 2026** | 0419–0428 | Native Backgrounds & Compact Pieces. | 64-byte metatiles; 4-row/4-col segment hoists; 6-byte compact pieces (`{dx, dy, key}`). Rope race reached **803 frames**. | [Cody_build0426_genesis_native_sprite_optimization.md](file:///home/tighe/projects/rastan-genesis/docs/design/Cody_build0426_genesis_native_sprite_optimization.md), [Cody_build0428_rastan_player_genesis_native_optimization.md](file:///home/tighe/projects/rastan-genesis/docs/design/Cody_build0428_rastan_player_genesis_native_optimization.md) |
| **Mid Oct 2026** | Post-0425 Study | Reference Architecture Comparison. | Graphics are 80–95% native. **Structural defect isolated:** *Rastan* is the sole engine running the whole worker inside IRQ6. | [Andy_post0425_genesis_native_reference_architecture_study.md](file:///home/tighe/projects/rastan-genesis/docs/design/Andy_post0425_genesis_native_reference_architecture_study.md) |
| **Late Oct 2026** | 0439 | Background residency optimization. | Inlined and hoisted `fg_cache_resolve` in Plane-A selector 0. Accepted on real hardware. | [Cody_build0439_plane_a_horizontal_residency_optimization.md](file:///home/tighe/projects/rastan-genesis/docs/design/Cody_build0439_plane_a_horizontal_residency_optimization.md) |

---

## 3. Disproven Theories & Closed Paths (Do Not Re-Examine)

To conserve engineering effort and paid usage, the following hypotheses have been conclusively disproven by empirical evidence:

1. **"VBlank DMA Bandwidth is the Primary Bottleneck":**
   * *Status:* **DISPROVEN.**
   * *Evidence:* Physical beam measurements prove that `dma_publish_frame` takes a median of 6.2 scanlines (~3,028 beam dots) out of a 38-scanline VBlank window. SAT DMA (640 bytes) takes ~1 scanline. DMA transfer bandwidth is not causing the crawl.
2. **"Enemy Gameplay AI / Collision Logic is the Primary Cause of Combat Slowdown":**
   * *Status:* **DISPROVEN.**
   * *Evidence:* [Andy_build0425_enemy_load_cost_attribution.md](file:///home/tighe/projects/rastan-genesis/docs/design/Andy_build0425_enemy_load_cost_attribution.md) proved that of a +14,850 cycle delta per enemy, arcade AI, state machines, and collision account for only **15–35%** (~2,500 cycles). The remaining **65–85%** is native Genesis sprite presentation (dispatch, per-piece emit, residency lookup, and SAT appending). Nativizing arcade gameplay logic is prohibited and unnecessary.
3. **"Active Display DMA Corrupted A-0154 Tile Holes":**
   * *Status:* **DISPROVEN.**
   * *Evidence:* Proven in Build 0418 to be a 128-KiB VDP-DMA source-boundary straddle bug (KF-090). Fixed permanently by 32-byte-aligning the PC080SN tile corpus.
4. **"Background Translation is Slowing Down Horizontal Scrolling":**
   * *Status:* **CLOSED.**
   * *Evidence:* Build 0425 hardware verification proved that horizontal scrolling with no enemies present runs smoothly within the 128,009-cycle frame budget without black bars or tearing. Background translation per se is closed; only micro-hoisting remains.

---

## 4. Deep-Dive: The Dominant Bottleneck — Worker-Inside-IRQ6 Scheduling

### 4.1 The Mechanism of Failure

On NTSC Sega Genesis, one display frame consists of **262 scanlines** running at **59.92 Hz**, providing a budget of **128,009 CPU cycles per frame** (7,670,453 Hz ÷ 59.9227 Hz).

In the current execution pipeline (`apps/rastan-direct/src/vdp_comm.s` and `apps/rastan-direct/src/dma.s`):
```text
  Physical VINT (Level 6)
         │
         ▼
  _vblank_service (0x700C2)
         │
         ├── 1. rastan_direct_update_inputs
         ├── 2. vdp_prepare_sprites (guard/no-op in gameplay)
         ├── 3. dma_publish_frame (DMA commits frame N-1: SAT, VSRAM, Planes)  [~6 lines]
         │
         └── 4. tail jmp (0x3A208).l  ──> [Arcade VBlank Worker]
                     │
                     ├── oriw #$0F00, %sr  <── IPL RAISED TO 7 (ALL INTERRUPTS MASKED)
                     ├── Gameplay / Actor state machines / Physics
                     ├── Arcade collision detection
                     ├── Native sprite staging (native_stage_dispatch -> pc090oj_native_emit_pass)
                     └── Native tilemap updates (Plane A / Plane B staging)
                             │
                             ▼
                        RTE at 0x3A27E  ──> Returns to Mainline Spin Loop (0x3A1A8)
```

### 4.2 Why This Destroys Frame Pacing ("Case C Masked Continuation")

1. **Under Light Load (< 128,000 cycles):**
   The entire sequence finishes before scanline 262. `RTE` executes, restoring IPL 0. When the next VBlank arrives, the 68000 accepts the Level-6 interrupt immediately. The game runs at a solid 60 fps.
2. **Under Heavy Load (> 128,000 cycles):**
   When 3–4 enemies appear, or dense cave collision and scrolling coincide, execution takes 150,000–180,000 cycles (~300–370 scanlines).
   * Because IPL is locked at 7 (or 6), the CPU **continues executing into active scanout of the next frame**.
   * At scanline 262 (when the next physical VBlank begins), the VDP asserts IRQ6, but the CPU **cannot accept it** because IPL ≥ 6.
   * The VBlank window passes without a publication commit!
   * When the CPU finally reaches `RTE` at scanline 350, it drops IPL to 0. It *immediately* takes the pending IRQ6, beginning publication and the *next* worker hundreds of lines late.
   * **Result:** Effective frame rate drops from 60 Hz to ~40–45 Hz with severe judder, missed frames, and visible mid-screen tearing.

### 4.3 The Commercial Reference Standard

Every single high-performance commercial Genesis title inspected separates publication from production:

| Title | Production Location | Publication Location | Overload Behavior |
|---|---|---|---|
| **Sonic the Hedgehog** | Mainline (`MainGameLoop` @ `sonic.asm:428`) | Bounded VBlank (`VBlank_Levels` @ `:815`) | Clean 30 fps lag frame (`VBlank_Lag`); zero tearing |
| **Gunstar Heroes** | Mainline (IPL 0) | Bounded VBlank DMA queue | Slowdown, never display tear |
| **Rainbow Islands (Gen)** | Mainline (IPL 0) | Bounded VBlank (`0x0380–0x041A`) | Clean slowdown |
| **Shinobi III** | Mainline (IPL 0) | Bounded VBlank (SAT + stream) | Clean slowdown |
| **Rastan (Current)** | **Inside IRQ6 (IPL 7)** | **Inside IRQ6 (IPL 7)** | **Missed VINTs, Case C cascade, tearing** |

---

## 5. Prioritized Optimization Roadmap

### Priority 1: Architectural Decoupling (Phase D / Phase E Scheduling)
* **Goal:** Move the entire gameplay tick and native staging out of IRQ6 into the mainline, reserving IRQ6 strictly for bounded VDP publication.
* **Architecture:**
  1. **IRQ6 (`_vblank_service`):**
     * Check if `frame_ready` flag is set.
     * If set: Swap buffer pointers (`present_bank ^= 1`), invoke `dma_publish_frame` on the FRONT buffer (~6–8 scanlines), clear `frame_ready`, and execute `RTE` immediately.
     * If not set (lag frame): Skip publication (or commit scroll/SAT only), increment lag counter, and `RTE`.
  2. **Mainline:**
     * Runs in a standard loop at IPL 0.
     * Waits for VBlank pulse (or signals completion).
     * Executes arcade tick (`0x3A208`), object updates, collision, and native sprite/tilemap staging into the BACK buffer.
     * Sets `frame_ready = 1`.
* **Impact:** **Highest possible.** Completely eliminates Case C masked continuations. Converts over-budget frames into clean, tear-free 30 fps slowdown.

---

### Priority 2: Multi-Enemy Sprite Presentation Batching ([pc090oj_hooks.s](file:///home/tighe/projects/rastan-genesis/apps/rastan-direct/src/pc090oj_hooks.s))
* **Goal:** Reduce the +14,850 cycle penalty per active enemy by streamlining native piece enqueueing.
* **Key Interventions:**
  1. **Composite Actor Bounding-Box Screening:**
     * Currently, `.Lnq_emit_entry` (lines 1988–2330) performs viewport boundary testing and opaque-bbox calculations for *every individual piece* (~28 instructions + 4 byte reads per piece).
     * For multi-piece actors (e.g. 10–12 pieces per lizardman/knight), calculate the composite bounding box once at the actor level (`native_stage_dispatch_*`). If the entire actor is within screen margins `[0 ≤ X ≤ 256-width, 0 ≤ Y ≤ 224-height]`, bypass the per-piece viewport checks completely.
  2. **Direct Queue Burst Allocation:**
     * Replace repeated `bsr native_sprite_emit_fast` calls with direct cursor reservation: compute `count * 8`, advance the lane queue cursor once, and emit pieces using direct indexed offsets (`0(A0)`, `8(A0)`, `16(A0)`).
  3. **Complete Retirement of `.Lnative_emit_actor_common`:**
     * Expand offline frame coverage across Rounds 2–6 so that no active gameplay actor hits the legacy interpreter fallback.

---

### Priority 3: Universal Tilemap Residency Hoisting ([tilemap_hooks.s](file:///home/tighe/projects/rastan-genesis/apps/rastan-direct/src/tilemap_hooks.s))
* **Goal:** Extend the Build 0439 optimization across all remaining background rendering paths.
* **Key Interventions:**
  1. **Plane A Selector 1/2 Hoisting:**
     * Build 0439 inlined `fg_cache_resolve` in selector 0 by keeping the LUT base (`genesistan_pc080sn_tile_vram_lut`) in register `A2` and the limit in `D7`.
     * Apply this exact pattern to `.Lplane_a_publish_name_block4_native` (selector 1/2) and the vertical-row updating paths.
  2. **Plane B Visual Record Hoisting:**
     * In `.Lplane_b_publish_name_native`, hoist `genesistan_pc080sn_tile_vram_lut` outside the 16-column traversal loop, eliminating per-cell `bsr` calls.

---

### Priority 4: Coalesced Dirty Plane VDP DMA ([dma.s](file:///home/tighe/projects/rastan-genesis/apps/rastan-direct/src/dma.s))
* **Goal:** Reduce VDP command register setups during the VBlank publication window.
* **Key Intervention:**
  * When multi-column updates occur during scrolling, check if adjacent columns in `staged_fg_buffer` / `staged_bg_buffer` are contiguous. Coalesce adjacent 32-word column transfers into single larger DMA blocks rather than setting up VDP DMA registers per column.

---

### Priority 5: Bounding Copied Arcade Core Spikes (`0x05100A`)
* **Goal:** Flatten worst-case 172-scanline execution spikes in arcade logic.
* **Key Intervention:**
  * Use the canonical Ghidra project (`rastan_arcade_ref.gpr`) to reverse-engineer `0x051210` / `0x05100A` (master actor state/collision loop).
  * Determine if the routine performs quadratic all-to-all collision checks across empty/inactive actor slots.
  * If inactive slots are scanned unconditionally, introduce a declarative opcode replacement to skip inactive slots early without altering arcade collision results.

---

## 6. Implementation Checklist for Agents

When implementing any item from this roadmap, Andy and Cody must adhere to the following project constraints:

- [ ] **Preserve RULES.md Invariants:** Arcade code expresses intent; Genesis code executes intent. No Genesis-side gameplay redesign or AI alteration.
- [ ] **Evidence First:** Before modifying any routine, measure its baseline cycle count using host-side MAME Lua scripts or the established timing harness (`tools/mame/run_frame_timing_trace_wsl.sh`).
- [ ] **Shift-Table Reflow:** When replacing instructions in copied arcade code, use `shift_replacements` in `specs/rastan_direct_remap.json` if sizes change. Do not constrain replacements to equal-length hacks.
- [ ] **Standalone Report:** Every ROM-producing implementation task must produce a standalone Markdown report (`docs/design/<Agent>_buildNNNN_<name>.md`).
- [ ] **Sequential Numbering:** Consume the next Makefile-owned sequential build number. Never protect or overwrite numbered ROM artifacts.
