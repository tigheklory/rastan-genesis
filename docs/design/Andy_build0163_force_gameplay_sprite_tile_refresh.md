# Andy — Build 0163: Force Gameplay Sprite Tile Refresh (controlled experiment) — VISUAL-TEST CANDIDATE

## 1. Baseline
HEAD 9cea9e8, working candidate Build 0162 (`7bcb3179…`, counter 162, opcode_replace 137, coverage 0x1820AC).
Accepted build remains 0160 pending Tighe visual acceptance.

## 2. Residency/worklist decision + chosen variant
`.Lpc090oj_worklist_set` (d0=slot, d1=code): when `code == sprite_tile_resident_code[slot]` it CANCELS/skips
the tile-DMA worklist entry (residency cache — assumes the pattern is already in VRAM). Only the "differ" path
queues a DMA. **Variant A** chosen: gate the residency early-out to the gameplay scene — during gameplay, take
the "differ" (queue) path unconditionally, so every represented gameplay slot requeues its tile DMA each
interval. Gameplay-gated (`genesistan_current_scene_id == 1`); title/frontend residency behavior unchanged.

## 3. Exact source change (`pc090oj_hooks.s` only; no opcode_replace)
- Added `.extern genesistan_current_scene_id` + `.equ PC090OJ_SCENE_GAMEPLAY_ID, 1`.
- In `.Lpc090oj_worklist_set`, before `cmp.w %d3,%d1`: `cmpi.b #PC090OJ_SCENE_GAMEPLAY_ID,
  genesistan_current_scene_id; beq.s .Lwls_differ` — forces requeue during gameplay. Uses the existing worklist
  format, source calc (`rastan_pc090oj + (code&0xFFF)*128`), dest (`SPRITE_TILE_BASE + slot*4`), and VBlank
  tile-DMA commit. SAT placement / decode / palette / collision untouched. Coverage 0x1820AC->0x1820B8 (+0xC,
  paired-updated); opcode_replace stays 137.

## 4. Validation (Build 0162 vs 0163; deterministic)
- **tile DMA (the experiment): Build 0162 peak tile_dma_count=0, 0/21 gameplay frames** — 0162 queues ZERO
  gameplay sprite tile DMA (residency cache blocks ALL refresh). **Build 0163 peak=6, 12/21 frames** — forced
  requeue re-DMAs the 6 represented gameplay slots each frame prepare runs. Experiment mechanism CONFIRMED active.
- GATE_PASS; boot guard PASS. ROM SHA `6f6efa750a004e5f74d365eb0d43119e7e88456ae44abc477237af93725171c5`, size 1,581,240, counter 163.
- Title F=100: represented=15 (intact); palette L0=15 L2=15 (intact).
- Gameplay F=560: represented=6; selector a5@0x10A8=0x0000; staged_bg=2048; staged_fg=2016; command 0x00FF;
  palette lines L0=15 L1=14 L2=15 L3=15 (all populated, Build 0161/0162 preserved). collision WRAM empty.
- Reachable SAT chain UNCHANGED vs 0162 (s0,6,7,8,13,14; slot-keyed tiles 0x400+) — expected: this forces tile
  DMA, not SAT representation. (At F=560 the represented set is 6 slots; records 64/65 belong to a different
  stable-gameplay frame per Cody's facts.)
- Determinism: two identical runs.

## 5. Interpretation
The experiment PROVES a durable fact regardless of the visual result: **Build 0162 performs ZERO gameplay sprite
tile DMA (tile_dma_count=0 across gameplay) — the residency cache reports all codes resident and skips every
refresh.** So if the gameplay sprite VRAM tiles are stale/wrong, Build 0162 never corrects them. Build 0163
forces the refresh (6 DMAs/frame). Whether this makes gameplay sprites appear correctly is a **VDP-visible VRAM
question** that headless MAME cannot read (invalid readback) — **Tighe must visually verify**. If 0163 improves
gameplay sprites -> residency/stale-VRAM was the blocker; if not -> residency is NOT the blocker and the next
target is sprite graphics source/layout/format or final VDP composition.

## 6. Open/Closed + KF + Architecture
OPEN-017: Build 0163 is a VISUAL-TEST candidate (SHA `6f6efa750a004e5f74d365eb0d43119e7e88456ae44abc477237af93725171c5`, counter 163, preserved). Accepted stays 0160.
Proven: 0162 does zero gameplay sprite tile DMA; 0163 forces per-frame refresh of represented gameplay slots.
KNOWN_FINDINGS: durable fact — the PC090OJ residency cache blocks ALL gameplay sprite tile DMA in 0162
(tile_dma_count=0); recorded pending the visual result. Architecture: single bounded pc090oj_hooks.s change,
gameplay-gated; no opcode_replace, no forced sprites/SAT/tiles, no second renderer, no VINT/collision/palette/
FG_SRC/selector change; all candidate ROMs preserved. Arcade is the reference.
