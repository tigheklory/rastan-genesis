# Andy/Fable — N1 Native PC090OJ Sprite Pipeline (Builds 0219/0220 rejected, **Build 0221 = N1 candidate**)

**Date:** 2026-07-20 · **Evidence:** `states/traces/n1_native_pc090oj_sprite_pipeline_20260720_183229/` · **JSON used:** address_map.json `2fb9a49a…` / patch manifest `cb16570f…` (hashes in json_hashes.txt; no fixed offsets used)

## Builds
| Build | SHA256 (16) | Status |
|---|---|---|
| 0219 | `b8da764100386320` | **REJECTED** — `.Lpc090oj_decode_record` clobbers d5 (the emit cursor); SAT buffer overran into adjacent state. Preserved. |
| 0220 | `38d1bdcd4730bcab` | **REJECTED** — colbank display-latch staleness: the arcade sets sprite_ctrl AFTER its producers, so the mainline pass read colbank=0 and every sprite lost its palette line. Preserved. |
| **0221** | `60d14fb0f9294631…` (1,583,868, counter 221, GATE_PASS, cfg 256/HUD=0) | **N1 candidate** — full native pipeline working. Rolling ROM = 0221. |
opcode_replace unchanged **216** (source-only). Coverage 0x183408 → 0x182AFC (≈2.4 KB of compatibility code deleted from ROM).

## Architecture as implemented
**The chip-shaped mirror pipeline is gone.** What remains and what's new:
- **`pc090oj_object_ram` (256×8, fixed)** is retained NOT as a mirror but as the arcade program's own persistent slot-addressed object store: Ghidra + the current hook set prove incremental producers (score digits 0x3B802, sprite-update 0x54810, decay 0x5607C, copy 0x56114, zero-fill 0x56440, status 0x5A098, frontend writers) update rows in place across frames, exactly as they updated PC090OJ RAM. That is category-2 arcade state from the redesign doc — required by program semantics. **No mirror-size configuration remains** (fixed 256; PC090OJ_MIRROR_RECORDS is now inert).
- **One ascending emit pass** (`pc090oj_native_emit_pass`) walks the table once per frame → final-format Genesis SAT entries in a **double-buffered shadow SAT** (2×640 B, link order = ascending record order). Triggered at the END of the arcade's own gameplay sprite dispatcher (hook_target_41dae tail = mainline, per the design); frontend scenes use a VBlank fallback in `vdp_prepare_sprites`. Exactly-once via `pc090oj_sat_frame_ready`.
- **Implicit retirement:** rows blanked/cleared by arcade producers simply emit nothing next pass — validated live: Rastan killed all four lizards and their sprites vanished with zero stale entries (snapfin/0000).
- **First-80-wins in ascending record order** = PC090OJ paint priority (MAME pc090oj draws records descending, so record 0 is topmost; Genesis link order ascending reproduces it). Visual parity with 0218 layering confirmed (HUD/player/lizard).
- **Code-keyed residency:** 64 sets × 2 ways = 128 VRAM cells (tiles 1024–1535, 0x8000–0xBFFF), tag = sprite code. SAT position changes never re-upload. Misses enqueue into a bounded 8-entry queue (≤1 KB DMA/frame) and skip emission for one frame (pop-in); a queued upload lands in VBlank BEFORE the SAT DMA displays it. No stale unrelated artwork (tag set only after DMA).
- **Display-latch semantics (the 0220 lesson, now a durable rule):** sprite_ctrl colbank is resolved at COMMIT, not producer time — the emit pass stores each entry's bank nibble in a parallel 80-byte array; a ≤80-iteration VBlank fix-up applies the latched colbank through the Build-0210 palsel (48→2, 0x33→3, route-table 0x36→0, fallthrough). Ctrl flip remains decode-time (stable in normal play; noted residual).
- **VBlank:** pal-fixup + constant 640 B SAT DMA + ≤8×128 B pattern DMAs; the sprite commit moved AFTER DISPLAY_ON (the display-off bracket now exists only for the untouched N2 plane path). No record scanning in gameplay VBlank.
- **KF-067 −8 lizard alignment** preserved (applied to the engine-emitted rows in the direct-row block-0x2C8 stager — scratch/seed/flush deleted). Record-46-equivalent output preserved through its existing validated route (row 46 identity is a producer addressing constant, not renderer state). HUD suppression preserved (emit-pass skip of rows 0–45 in gameplay under the option).

## Retired (deleted from source, no live consumers — static gate PASS)
Mirror shadow (2 KB), candidate/waiting/used bitsets + helpers + full sweeps, representation/eviction engine (activate/evict/field-update/sync, rep/used/bmp scans), record→slot map, descriptor table (960 B), block-0x2C8 scratch+seed+flush (800 B + 2×99 copies/frame), shadow-compare, scene-transition candidate sweeps, slot-keyed residency, mirror-size dependency. Remaining references = exported symbol stubs only (grep-verified).

## Producer coverage (all writers audited)
Absolute writers (Ghidra hw_refs): init/clear 0x52A/0x3AD72, frontend 0x3B8B0/0x3B902/0x3B930/0x3B926/0x52AA2-family (3AD44 dispatch), gameplay 0x41DAE/0x41F5E/0x45DFA, ctrl 0x3ADD8/0x3AE28/0x3EEFA/0x3EF5C, per-record 0x3B802/0x54052/0x54810/0x5607C/0x56114/0x56440/0x5A098/0x59F5E/0x3AD84 — **all route to the object table through their existing hook contracts (writers unchanged, downstream native)**. Indirect composer 0x3D054→0x3D254: still the ROM's own data-driven engine, now writing table rows directly (covers every family/boss/stage by construction); its full native reimplementation is the N3 boundary. No unmapped writers observed (audit hook quiet).

## Validation (MAME; arcade authority + 0218 baseline)
Title ✓ (15 sprites, correct palettes) · story/READY ✓ (player L3) · Stage 1 ✓ · Rastan stand/walk/jump/attack ✓ (correct colors, position) · natural lizard population ✓ (4 complete green lizards, correct vertical position) · lizard kill + clean retirement ✓ (no stale sprites) · HUD suppressed in gameplay / present frontend ✓ · planes/terrain identical to 0218 (untouched) ✓ · no crashes/locks in all runs. **Not yet reproduced this session:** hurry-up bat swarm, flip scenes, attract full cycle → USER MUST VERIFY + progressive acceptance. Known residual: ~1.2 residency pop-in misses/frame under 4-lizard animation load (working set ≈ cache capacity).

## Resource before/after (0218 → 0221)
| Metric | 0218 (mirror) | 0221 (N1) |
|---|---|---|
| Sprite-infra WRAM | ≈9,350 B (+object 2 KB) | **3,792 B incl. the 2 KB arcade object table** (≈5.5 KB freed) |
| Full sprite scans/frame | 3 (2 KB compare + 256 candidates + represent) | **1** (single table pass, mainline in gameplay) |
| Whole-buffer copies/frame | 2 (seed 800 B + shadow 2 KB) | **0** |
| Sprite VBlank CPU | scans+represent+SAT rebuild+residency | pal-fixup ≤80 + DMAs |
| SAT DMA | variable, in display-off bracket | **constant 640 B, display ON** |
| Pattern DMA | slot-churn re-uploads | code-keyed, new codes only (≤1 KB/f) |
| Eviction/index flicker class | present (KF-051/0203-class) | **eliminated** (no eviction engine) |
| Mirror-size dependency | 256 required (KF-049/067) | **none** (fixed arcade table) |
| ROM code | — | −2.4 KB |
| Remaining physical limits | — | per-scanline 20-sprite (N3 merging), residency pop-in (N3 manifests) |

## USER MUST VERIFY (BlastEm / Exodus / Sega Nomad)
1. Title/attract/READY presentation; 2. Rastan colors/position/animation; 3. lizards complete, green, on-ground, killable; 4. HUD absent in gameplay, present where enabled; 5. hurry-up bat swarm renders + stays stable; 6. any sprite pop-in/flicker assessment vs 0218 (expect: eviction flicker gone; brief single-part pop-in possible under heavy animation); 7. no stale/garbage sprites after kills/deaths; 8. planes unchanged (cave defects remain, N2 scope).

## STOP status
NOT triggered — the central design finding held (no readback dependencies surfaced; every producer translated; the two numbered defects were concrete and corrected in sequence).
