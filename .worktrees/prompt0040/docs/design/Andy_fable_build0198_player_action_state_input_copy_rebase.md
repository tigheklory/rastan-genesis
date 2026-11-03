# Andy/Fable — Build 0198: Player Action-State Input-Copy Rebase — RASTAN IS CONTROLLABLE

**Date:** 2026-07-17
**Type:** Bounded fix (+29 opcode_replace) + validation + Build 0199/192 comparison.
**Produced:** **Build 0198 (256, main)** `65abbcb721dbb6d5b16df0379fd8f094dfc732510d1a584082ad64377105ef8b`; **Build 0199 (192, comparison)** `bc592c5f68653ee70cde750d33730a66ba8425b55aca0a6bdb720fe7a0648ffe`; both 1,582,876, counters 198/199, GATE_PASS. Rolling dist = 0198/256; Makefile default 256.

## The complete dispatch-chain root cause (finishing the 0196 investigation)
1. The mode field **A5+0x10E8 is the player ACTION state** (0=idle, 1=walking, 2=jump, 3=fall, 8=death), not a spawn gate. Arcade sets mode=1 via ~0x5265E/0x5270C exactly while Right is held; `A5+0x13A` (init 0x3000) is **HP** (0x517E6: HP==0 → mode=8 death).
2. The master routine reads the input latch once per frame (0x5102E, rebased in Build 0158) and **copies it to the per-frame input variable A5+0x137A** (`0x51034 movew %d0,%a5@(4986)`) — a5-relative, works on Genesis (verified live: Right→0xF7 in 0xFF137A).
3. **THE BUG:** the ENTIRE player action state machine reads that variable via raw literal **`movew 0x10D37A,%d0` — 29 sites, ALL RAW** (0x514A4, 0x514C4, 0x514D8, 0x515B6, 0x51600, 0x51728, 0x51C5A, 0x51CA0, 0x51CE0, 0x51E2E, 0x51EDA, 0x51EEE, 0x51F1E, 0x51F2E, 0x520CA, 0x52108, 0x52144, 0x5217C, 0x521B8, 0x52200, 0x5223E, 0x52286, 0x522C4, 0x52304, 0x52332, 0x5236A, 0x523D6, 0x5249A, 0x52A1A) — including the gatekeeper heads 0x515B6/0x51600 and every walk/jump/attack handler. On Genesis raw 0x10D37A = ROM constant **0xEEEE** (phantom frozen input) → the action state machine never saw the joystick → mode stayed 0 → no walking, no camera scroll, no progression. (The 0x51090 `jsr 0x52732` question from the prior task is moot: that jsr is dead code in this flow on both machines; the real control flow is the 0x5132A-dispatched action handlers reading A5+0x137A.)
4. The input-read family is now COMPLETE: 11× latch 0x10C016 (Builds 0158+0196) + 29× per-frame copy 0x10D37A (this build) = 40 rebased reader sites.

## Fix
+29 `opcode_replace`: `30390010D37A` → `303900FF137A` (byte-neutral 6→6, KF-042/KF-057 class). opcode_replace count 162→191 (spec expectations + both CANONICAL constants paired; manifest/address_map regenerated). ROM-verified: **29/29 rebased, 0 raw** (and 11/11 latch sites).

## Control validation (Build 0198, MAME) — THE BREAKTHROUGH
| Phase | copy@FF137A | mode@FF10E8 | result |
|---|---|---|---|
| idle | 0x00FF | 0 (idle) | standing |
| HOLD RIGHT | 0x00F7 | **1 (walking)** | **scrollX 0x0000→0x01AA→0x01D6 — camera scrolls, Rastan walks!** |
| HOLD LEFT | 0x00FB | 1 | walking |
| PRESS C (jump) | 0x00DF | **2 (jump)** | jump state entered |
| PRESS B (attack) | 0x00EF | 2 | responds |
| after descent | — | 3 (fall) | **scrollY 0x0149→0x01D8 — he jumped down the cliff; vertical camera follows** |

Substate A5+0x1364 animates (0↔1↔2 walk cycle). Matches the arcade mode semantics exactly (arcade: mode=1 during the same right-held window). **Screenshots (states/traces/dispatch0198/snap98/): Rastan walking mid-screen with the world scrolled — first build in project history with player control and camera progression.** Enemies: not yet spawning in the sampled window (progression triggers now advance with scroll; enemy evaluation is the natural next task on a now-live game).

## Build 0199 / 192 comparison
Same source, `make release PC090OJ_MIRROR_RECORDS=192`. Control identical (mode=1 walking, scrollX 0→0x117); Rastan complete (no 128-style waist cutoff; screenshot snap99/); represented=17; rate 0.674 vs 0198's 0.607 in the same scrolling scenario (heavier than static since FG/BG stream new columns while walking). 192 remains visually safe.

## Validation summary (both builds)
GATE_PASS; title/READY render; gameplay reached; TC0140SYT fix present (0x3F2A4=0280fffffffe); 0192 gates + 0193 fast path in source; 0196 latch rebases 11/11; 0198 copy rebases 29/29; BG/FG/palette correct while scrolling (new terrain streams in correctly); no new lock/crash. Makefile default 256; rolling dist=0198; artifacts 0195(rejected diag)/0196/0197/0198/0199 all preserved.

## Not touched
Collision internals, enemies, black bars, 60 Hz, PC080SN/PC090OJ rendering, mirror default, Builds 0175/0178/0180/0192/0193/0194 — all intact.
