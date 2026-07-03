# Andy — Build 0130 Graphics Timing Budget and Sprite Tile-DMA Confirmation (Static Analysis / Reclassification Only)

**Author:** Andy
**Date:** 2026-07-02
**Baseline:** Build 0130 (byte-identical to Build 0128), `dist/rastan-direct/rastan_direct_video_test_build_0130.bin`, SHA256 `79ec8a30c44f24b0b551e4a1ae7116de075264927fb5ff550148f25808f5bc6f`.
**Scope:** Static source analysis + existing-evidence reclassification. NO implementation, patch, ROM, rebuild, or diagnostic build. Genesis-only runtime/helper code labeled `runtime_genesis_pc`/Genesis-WRAM unless `address_map.json` proves an `arcade_pc` relationship. No arithmetic-offset proof. Labels: **[OBS]** verified this task; **[EVID]** Build 0129 ring evidence; **[INT]** interpretation.

> **BOTTOM LINE:**
> **Q1 (late display-on): SUPPORTED.** 15 of 17 sampled captures restore display *after* VBlank bit 3 has cleared (checkpoint 0x0A: bit3=1/shadow=0 → checkpoint 0x0B: bit3=0/shadow=1). The one clearly-good content frame (coin/start 371) is one of the only two that restored display *inside* VBlank. Exact scanline lateness is NOT measurable (no HV/VCounter field).
> **Q2 (sprite tile-DMA churn): CONFIRMED.** `.Lvcs_mirror_scan` clears the entire descriptor table — including offset-8 (old-tile) — before every scan, so the "tile-code-changed" comparison always sees old-tile=0. Every nonzero-tile sprite is treated as changed every frame → ~**1472 tile-DMA words/frame** at the title (23 emitted × 64), on top of a fixed **320-word SAT DMA/frame**.
> **Q3:** Steady-title display-off cost is dominated by (1) sprite tile-DMA churn, (2) the 256-entry mirror scan, (3) the fixed SAT DMA. `load_scene_tiles` is a *separate* transition-only display-off owner, not the steady rolling-slit.
> **Q4:** A=SUPPORTED, B=CONFIRMED, C=CONFIRMED (mechanism, transition-only), D=CONFIRMED (not urgent for timing). **Implementation NOT ready** — this is a confirmation pass; a design task must follow.

---

## == PHASE 0 ==

- **Relevant priors:** KF-021 (staged/true/linked SAT divergence — context), OPEN-001 (title/attract incomplete graphics), OPEN-024 (PC090OJ incomplete), OPEN-021 (score columns), OPEN-006 (sprite palette). Andy PC090OJ object-RAM-faithful + 3b930/3b802 designs (producer→mirror routing, landed in Build 0128 = 22/27). Cody Build 0129 VBlank ring diagnostic (reverted; Build 0130 byte-identical).
- **High-rediscovery hazards:** KF-021 HIGH (do not treat staged SAT as truth); "commit is inside VBlank" is NOT a full pass when display-*on* lands after VBlank end (the task's explicit warning — honored below).
- **Task classification:** STATIC ANALYSIS + EVIDENCE RECLASSIFICATION extending OPEN-001 / OPEN-024. No new root cause asserted as durable beyond what evidence supports.
- **Contradiction detected:** YES (partial). The Build 0129 report's own interpretation ("occasional bit-3-high after display-on interpreted as timing within the same VBlank … not an independent fault") is **reclassified** under the task's binary rule: the *dominant* case is bit3=0 at 0x0B → display restored after VBlank ended. The report under-weighted this; I re-weight it as SUPPORTED.
- **Open/Closed pre-check:** OPEN-001, OPEN-024 primary; OPEN-021/OPEN-006 context. Not closing any.
- **Build 0130 baseline verified:** YES — diagnostic doc records Build 0130 SHA256 `79ec8a30…f5bc6f`, byte-identical to Build 0128 (`cmp -s` = 0).
- **0129 diagnostic artifact located:** YES — `states/traces/build0129_vblank_status_ring_diagnostic_20260702_155842/` (17 captures, `vblank_status_ring_analysis.md/.json`).
- **address_map.json loaded:** YES (`_vblank_service`, handoff `0x3A208`, and the VBlank helpers are Genesis-native — no `arcade_pc` entry; producer hook arcade sites exist in the map but no arithmetic conversion is used here).
- **arithmetic offset used as proof:** NO.

---

## == Q1 LATE DISPLAY-ON ==

**Method:** For each of the 17 captures I use the concrete last-entry ring sample at checkpoint 0x0B (`after_display_on`) plus 0x0A/0x0C, per the task's binary rule. `_vblank_service` structure ([OBS] `vdp_comm.s:158-184`): 0x03 DISPLAY_OFF → 0x04 tiles → 0x05 BG → 0x06 FG → 0x07/0x08 sprites → 0x09 palette → 0x0A scroll → 0x0B DISPLAY_ON → 0x0C handoff `jmp 0x3A208`.

| Run | Frame | state a5@(0/2/4) | visual note | drawable | emitted | 0x0A bit3 | 0x0B bit3 | 0x0C bit3 | shadow 0x0A | shadow 0x0B | shadow 0x0C | classification |
|---|---:|---|---|---:|---:|:--:|:--:|:--:|:--:|:--:|:--:|---|
| coin/start | 340 | 0/1/2 | pre-coin story | 5 | 5 | 1 | **0** | 0 | 0 | 1 | 1 | **after VBlank ended** |
| coin/start | 371 | 1/0/0 | mostly-complete king frame | 23 | 23 | 1 | **1** | 1 | 0 | 1 | 1 | **inside VBlank** |
| coin/start | 411 | 1/1/0 | 1P/2P prompt | 19 | 19 | 1 | **0** | 0 | 0 | 1 | 1 | **after VBlank ended** |
| coin/start | 473 | 2/2/6 | start clear | 30 | 30 | 1 | **0** | 0 | 0 | 1 | 1 | **after VBlank ended** |
| coin/start | 474 | 2/2/6 | stale redraw | 30 | 30 | 1 | **0** | 0 | 0 | 1 | 1 | **after VBlank ended** |
| coin/start | 477 | 2/2/6 | second clear | 30 | 30 | 1 | **0** | 0 | 0 | 1 | 1 | **after VBlank ended** |
| coin/start | 534 | 2/2/7 | ROUND window | 32 | 32 | 1 | **0** | 0 | 0 | 1 | 1 | **after VBlank ended** |
| coin/start | 560 | 2/2/7 | post-ROUND | 32 | 32 | 1 | **1** | 1 | 0 | 1 | 1 | **inside VBlank** |
| coin/start | 620 | 2/2/7 | late coin | 32 | 32 | 1 | **0** | 0 | 0 | 1 | 1 | **after VBlank ended** |
| no input | 60 | 0/1/0 | sparse title fragments | 23 | 23 | 1 | **0** | 0 | 0 | 1 | 1 | **after VBlank ended** |
| no input | 120 | 0/1/0 | sparse title fragments | 23 | 23 | 1 | **0** | 0 | 0 | 1 | 1 | **after VBlank ended** |
| no input | 180 | 0/1/0 | mostly black | 23 | 23 | 1 | **0** | 0 | 0 | 1 | 1 | **after VBlank ended** |
| no input | 240 | 0/1/0 | mostly black/transition | 8 | 7 | 1 | **0** | 0 | 0 | 1 | 1 | **after VBlank ended** |
| no input | 282 | 0/1/2 | black-cover anchor | 9 | 8 | 1 | **0** | 0 | 0 | 1 | 1 | **after VBlank ended** |
| no input | 283 | 0/1/2 | post-anchor | 5 | 5 | 1 | **0** | 0 | 0 | 1 | 1 | **after VBlank ended** |
| no input | 289 | 0/1/2 | story fragments | 23 | 23 | 1 | **0** | 0 | 0 | 1 | 1 | **after VBlank ended** |
| no input | 369 | 0/1/2 | late sparse | 23 | 23 | 1 | **0** | 0 | 0 | 1 | 1 | **after VBlank ended** |

(Aggregate `bit3 by checkpoint` for most captures shows `after_display_on: [0,1]` — i.e. within the 1024-entry ring both occur across frames; the representative last-frame sample is tabulated above. The commit body 0x03–0x0A is bit3=1 in **every** capture: commit *runs* inside VBlank; it is the display-ON write at 0x0B that lands late.)

- **frames analyzed:** 17
- **display-on after VBlank ended:** 15
- **display-on inside VBlank:** 2 (coin/start 371, coin/start 560)
- **ambiguous/missing:** 0 (binary rule resolves all; aggregate shows minority of *other* frames in each ring land inside VBlank)
- **HV/scanline field present:** NO (diagnostic deliberately did not read `0x00C00008`)
- **exact lateness measurable:** NO — exact lateness in scanlines **cannot be calculated**. The one missing field a future diagnostic needs: **HV counter / VCounter (`HW 0x00C00008`) sampled at checkpoints 0x03, 0x0A, and 0x0B** (to convert bit3=0-at-0x0B into a scanline count).
- **visual correlation:** the single mostly-complete content frame (coin/start 371) is one of only two "inside VBlank" cases; every mostly-black / sparse no-input title frame is "after VBlank ended." This correlates but is **confounded** by content differences (drawable/emitted also differ). A bit3=0 at 0x0B means active scan has begun with display still off at the top → display-ON mid-frame reveals a horizontal band whose position rolls with commit-duration jitter — consistent with the observed "rolling horizontal slit through black."
- **classification:** **late display-enable is SUPPORTED** by existing Build 0129 data (majority of frames + good-frame correlation), NOT proven as sole cause (content confound; magnitude unmeasured).

**Q1 answers:** (1) 15 sampled frames restore display after VBlank ended. (2) 2 restore inside VBlank. (3) Yes — bad/sparse title frames correlate with late display-on (all 8 no-input samples are "after"). (4) Yes — the good coin/start 371 frame differs: it restored inside VBlank. (5) **SUPPORTED** (with HV magnitude still needed).

---

## == Q2 SPRITE TILE-DMA CHURN ==

All citations `apps/rastan-direct/src/pc090oj_hooks.s`.

1. **`vdp_commit_sprites` calls `.Lvcs_mirror_scan`?** YES — `bsr .Lvcs_mirror_scan` (line 921); full path `mirror_scan → link_chain_build → tile_dma → sat_dma → clear_dirty` (lines 919-927).
2. **`.Lvcs_mirror_scan` calls `.Lvcs_clear_generated_sprite_state` before scanning?** YES — first instruction `bsr .Lvcs_clear_generated_sprite_state` (line 947), before the 256-entry decode loop.
3. **`.Lvcs_clear_generated_sprite_state` clears `staged_sprite_descriptor_table`?** YES — zeroes the entire table (`80*12/2` words, lines 936-940), which **includes offset 8 (old-tile)** of every descriptor.
4. **`.Lpc090oj_emit_slot` reads descriptor offset 8 as old tile before writing new tile?** YES — `move.w 8(%a0),%d6  /* old tile for changed-flag */` (line 126); the new tile is written to `8(%a0)` afterward (line 132).
5. **Sets flag bit `0x0004` when new≠old?** YES — `move.w #0x8001,%d5; cmp.w %d3,%d6; beq .Lpc090oj_no_tile_change; ori.w #0x0004,%d5` (lines 147-150).
6. **`.Lvcs_tile_dma` gates on bit `0x0004`?** YES — `btst #2,%d1; beq .Lvcs_tile_next` (line 1131), after the valid-bit check (line 1129).
7. **If offset 8 is cleared before every scan, does every nonzero tile appear changed every frame?** YES — because the whole descriptor table (incl. offset 8) is wiped at scan start (line 947 → 936-940), the old-tile read at line 126 is **always 0**. For any sprite with a nonzero tile (`%d3 ≠ 0`), `cmp.w %d3,%d6` (d6=0) is never equal → the `0x0004` changed-bit is **set on every emit, every frame**. The old-tile optimization is fully defeated.
8. **Repeated sprite tile DMA:** **CONFIRMED.**

Additional:
- **tile-DMA words per changed sprite:** **64 words** (128 bytes = a 16×16 sprite's 4 tiles) — DMA length regs `0x9340`/`0x9400` (line 1150) and comment `/* length 64 words */` (line 1149); dest `(SPRITE_TILE_BASE + slot*4)*32` = 4 tiles/slot (line 1171-1188).
- **Build 0128 title emitted count (from Build 0129 ring):** **23** (`emitted=0x0017` in every no-input title capture) — consistent with the reported 22/27 target match.
- **worst-case title sprite tile-DMA words (all emitted treated as changed):** **23 × 64 = 1472 words/frame (2944 bytes)** — and per Q2.7 this worst case is the **actual steady case** at the title.
- **SAT DMA words per frame:** **320 words (640 bytes)**, **unconditional every frame** — `.Lvcs_sat_dma` length regs `0x9340`/`0x9401` (lines 1203-1204), = the full 80-entry SAT (80×8=640 B).
- **tile graphics preconverted?** YES — `pc090oj_assets.s` `.incbin "../../build/pc090oj_genesis.bin"` → `rastan_pc090oj` (line 4-5); `.Lvcs_tile_dma` DMAs straight from `rastan_pc090oj + tile*128` (lines 1137-1140). No per-frame pixel conversion; the churn is redundant **DMA**, not reconversion.
- **classification:** churn CONFIRMED; ~1472 (tiles) + 320 (SAT) = **~1792 words/frame** of sprite VDP DMA at the title, held under display-off. (No cache designed here per task constraint.)

---

## == Q3 BUDGET RANKING ==

Per-frame VDP cost and display-off ownership ([OBS] from `vdp_comm.s`, `pc090oj_hooks.s`, `scene_load.s`, `tilemap_hooks.s`):

| # | Contributor | words/frame (VDP) | cadence | outside VBlank? | holds display off? | steady-title vs transition |
|---|---|---|---|---|---|---|
| 4→ | **sprite tile DMA** (`.Lvcs_tile_dma`) | ~**1472** (23×64, churn) | every VBlank | no | YES (0x03–0x0B) | **steady-title (dominant)** |
| 5→ | **sprite mirror scan** (`.Lvcs_mirror_scan`) | 0 VDP; 256-entry **CPU** decode | every VBlank | no | YES | **steady-title (CPU-dominant)** |
| 7→ | **SAT DMA** (`.Lvcs_sat_dma`) | **320** (fixed) | every VBlank | no | YES | steady-title (fixed) |
| 3 | **FG strips** (`vdp_commit_fg_strips_if_dirty`) | 64 × dirty rows (≤2048) | if any `fg_row_dirty` | no | YES | transition-weighted |
| 2 | **BG strips** (`vdp_commit_bg_strips_if_dirty`) | 64 × dirty rows (≤2048) | if any `bg_row_dirty` | no | YES | transition-weighted |
| 1 | **tiles** (`vdp_commit_tiles_if_dirty`) | 48 | if `tiles_dirty` | no | YES | occasional |
| 8 | **palette** (`vdp_commit_palette`) | 64 | if `palette_dirty` | no | YES | occasional |
| 9 | **scroll** (`vdp_commit_scroll`) | 4 + 2 ctrl | every VBlank | no | YES | steady, negligible |
| 10 | **`load_scene_tiles`** | 16 × manifest pairs (VDP_DATA CPU copy) | **scene change only** | **YES (main-loop)** | **YES (own DISPLAY_OFF/ON)** | **transition-only, separate owner** |

- **ranked contributors (steady-title, display-off-holding):** 1) sprite tile-DMA churn ≈1472 w; 2) sprite mirror scan (256-entry CPU); 3) SAT DMA 320 w; 4) FG strips (dirty); 5) BG strips (dirty); 6) tiles 48 w; 7) palette 64 w; 8) scroll ~6 w.
- **steady-state title costs:** sprite tile DMA (churn), mirror scan, SAT DMA, scroll — all unconditional each VBlank.
- **transition-only costs:** BG/FG strip bursts (dirty rows spike on scene/clear), `load_scene_tiles` streaming, occasional tiles/palette.
- **display-off owners:** (a) `_vblank_service` holds display off across the whole commit block 0x03→0x0B (`vdp_comm.s:162-181`); (b) `load_scene_tiles` independently holds display off (`ori #0x0700,%sr`; DISPLAY_OFF; stream; DISPLAY_ON; restore SR — `scene_load.s:46-92`).
- **scene_load risk:** `load_scene_tiles` **can be and is invoked from tilemap producer hooks in arcade main-loop context, NOT from `_vblank_service`** — call sites `tilemap_hooks.s:136` (`.Lscene_match`, BG fill preamble) and `:308` (`.Lfg_scene_match`, FG fill preamble); the only `_vblank_service` wiring is the boot VINT vector (`boot.s:108`). When a producer fill first touches an A0 in a new scene's range, it triggers a mid-frame DISPLAY_OFF → tile stream → DISPLAY_ON with IRQs masked. **This is a separate transition/display-off mechanism, not the steady-title rolling-slit** (which is the per-VBlank late-display-on of Q1).

---

## == Q4 STRUCTURAL RISK ==

- **A. Late display-enable from `_vblank_service`:** **SUPPORTED.** 15/17 sampled frames restore display after VBlank bit3 clears; correlates with sparse/black title output; the one good frame restored inside VBlank. Not "confirmed" as sole root cause — magnitude (scanlines) unmeasured (no HV field) and content is a confound.
- **B. Repeated sprite tile-DMA churn:** **CONFIRMED.** Descriptor table incl. offset-8 old-tile is cleared before every scan → changed-bit set for every nonzero-tile sprite every frame → ~1472 tile-DMA words/frame at the title. Directly inflates the display-off window in (A).
- **C. `load_scene_tiles` mid-frame display-off risk:** **CONFIRMED** as a mechanism — own DISPLAY_OFF/ON + IRQ mask, invoked from BG/FG producer hooks in main-loop context (not VBlank). Scene-change/transition-only; distinct from the steady rolling-slit.
- **D. `.Lpc090oj_emit_slot` mixed producer/render responsibility:** **CONFIRMED.** `emit_slot` both (i) bridges into the canonical `pc090oj_object_ram` mirror when `pc090oj_scan_active==0` (producer path, lines 111-123) and (ii) writes `staged_sprite_descriptor_table` + `staged_sprite_sat` render state (lines 126-204). It is called both by legacy per-site producer hooks (`3b902`, `3ad84`, `54052`, `54810`, `5607c`, `56114`, `5a098`, …) **and** by the VBlank mirror scan itself (line 1037). Legacy producers therefore compute descriptor/SAT/changed-flag state that the next VBlank `.Lvcs_clear_generated_sprite_state` **wipes and recomputes** from the mirror — wasted, and a divergence risk against the prime directive that the mirror is canonical. **Urgent now? NO** — this waste occurs in main-loop (producer) time, not the display-off window, so it does not drive the Q1 timing symptom; it is structural debt to schedule under OPEN-024, not a blocker for the timing task.
- **E. Implementation readiness:** **implementation NOW? NO.** This is a confirmation/reclassification pass; the task forbids designing or implementing a fix. Churn (B) is confirmed and late-display (A) is supported, but the fix space (persistent sprite-tile cache; pulling DISPLAY_ON inside VBlank; splitting emit_slot) has not been designed, and (A)'s magnitude is unquantified.

**recommended next step (design/diagnostic, not implemented here):**
1. Cody diagnostic — re-add the ring **with HV/VCounter (`0x00C00008`)** at checkpoints 0x03/0x0A/0x0B to quantify display-on lateness in scanlines (the one missing Q1 field); temporary + revert + byte-identical, same discipline as Build 0129.
2. Andy design task — persistent sprite-tile-DMA cache (since B is confirmed): preserve the descriptor old-tile across frames instead of clearing it, so unchanged tiles skip DMA. **Do not** clear offset-8 in `.Lvcs_clear_generated_sprite_state` while keeping the changed-bit gate — but design first.
3. Separately scope the `emit_slot` producer/render split (Q4-D) under OPEN-024.

---

## Open / Closed Issues Impact

- **Open issues touched:** OPEN-001 (title/attract rolling-slit + late-display evidence; not closed), OPEN-024 (sprite tile-DMA churn confirmed + emit_slot mixed responsibility; not closed), OPEN-021/OPEN-006 (context only).
- **Closed issues touched:** NONE.
- **New issues opened:** NONE (recommend two tracked notes: **sprite tile-DMA churn — descriptor old-tile wiped every scan (Q2, CONFIRMED)**, and **`_vblank_service` late DISPLAY_ON after VBlank end (Q1, SUPPORTED, HV magnitude pending)**; `load_scene_tiles` mid-frame display-off is a documented mechanism under OPEN-001/transition).
- **Issues closed:** NONE.
- **Issues intentionally deferred:** the fix design for churn and late-display (separate design task); HV-magnitude diagnostic; `emit_slot` split; story black-cover root cause (KF-021 true-VDP-SAT capture).

## AGENTS_LOG updated
YES

## STOP status
NO — analysis complete; all four questions answered from existing Build 0130/0129 evidence; no implementation performed; exact display-on lateness flagged as needing an HV-counter field (does not block Q2/Q3/Q4).
