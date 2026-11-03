# Rastan Arcade Actor State Machine — Decompilation

**Static decompilation of `build/regions/maincpu.bin` + Ghidra exports. No MAME, no Genesis, no
build; counter 360.** This is the deep decompilation of the actor behavior dispatch and the
family-2 / base-0x033E lifecycle. Live Ghidra headless is not installed in the repo
(`tools/ghidra/*.gpr` projects exist but no `analyzeHeadless`), so this document is the exact
change-list / semantic model to fold into the Ghidra project; offline decoders are durable under
`tools/analysis/` and evidence under `analysis/actor_subround2/`.

Terminology: SUB-ROUND 1 / 2 / BOSS (progression `A5+0x13E`), never "castle". `A5 = 0x10C000`.

---

## CHECKPOINT A — `0x40BAA` complete state dispatch

`0x40BAA` (`FUN_00040baa`) is the actor behavior dispatch. It is invoked with the current actor
in `A4`. Mechanism (decompiled at `0x40BAA`):

```
40baa clrw d0 / moveb a4@(5),d0     ; d0 = state = actor+0x05
40bb0 addw d0,d0                    ; d0 = state*2
40bb2 lea 0x40bc2,a0 / addaw d0,a0  ; a0 = 0x40bc2 + state*2
40bb8 movew a0@,d0                  ; d0 = signed 16-bit table entry
40bba lea 0x40bc2,a0 / addaw d0,a0  ; a0 = 0x40bc2 + entry  (self-relative)
40bc0 jmp a0@
```

Jump table at **`0x40bc2`**, 35 entries (state 0x00..0x22), decoder
`tools/analysis/decode_40baa_jumptable.py`, output `analysis/actor_subround2/40baa_state_dispatch.txt`:

| state | handler | semantic |
|---|---|---|
| 0x00 | `0x41180` | **latent scanner / hunter** (see below); the state every schedule/spawned actor starts in |
| 0x01, 0x02 | `0x41CF4`→`jmp 0x473b8` | **FLYING-enemy update** (common) |
| 0x03–0x0C, 0x12 | `0x41CEE`→`jmp 0x47140` | **WALKING-enemy update** (common) |
| 0x0D, 0x0E | `0x41CF4`→`jmp 0x473b8` | flying update (turn-around waypoint states) |
| 0x0F | `0x40CCC` | **ARMORED MAN** (base 0x0A73 sword → 0x0A5A ball-and-chain; comp 2; family 0x0C) |
| 0x10 | `0x40C08` | anim-table param setup (`0x40C0E`), sub-behavior |
| 0x11 | `0x41CEA`→`braw 0x4684e` | state-0x11 handler |
| 0x13,0x14 | `0x40E4C`→`0x4375c` | specific enemy update A |
| 0x15 | `0x40E50`→`0x43840` | specific enemy update |
| 0x16 | `0x40E54`→`0x43ae6` | specific enemy update |
| 0x17 | `0x40E58`→`0x43f88` | specific enemy update |
| 0x18 | `0x40E5C`→`0x44082` | specific enemy update (shared with 0x1C) |
| 0x19 | `0x40E60`→`0x4396a` | specific enemy update |
| 0x1A | `0x40E64`→`0x43b32` | specific enemy update |
| 0x1B | `0x40E68`→`0x43ecc` | specific enemy update |
| 0x1C | `0x40E70`→`0x44082` | (shared with 0x18) |
| 0x1D, 0x21 | `0x40E6C`/`0x40E88`→`0x4415a` | specific enemy update |
| 0x1E | `0x40E88` | marker-recheck (`0x40E74`) + `0x13E` gate → `0x4103A` |
| 0x1F | `0x40EDA` | specific |
| 0x20 | `0x40EDE` | specific |
| 0x22 | `0x40E48`→`0x43636` | specific enemy update |

**Input requirements / mutations per handler class:**
- `0x47140` (walking) / `0x473b8` (flying): the common enemy-update engines. They read
  `+0x16/+0x1A` (X/Y), `+0x01` (anim), `+0x05` (state), the collision map, and drive motion; they
  do NOT re-resolve identity (base stays as set by the materializing handler). These are the
  update routines for the floor-marker-spawned enemies (states 0x03–0x0E).
- `0x40CCC` (state 0x0F): fully decompiled below — mutates `+0x1E`, `+0x38`, `+0x3E`, `+0x01`,
  `+0x09`, `+0x08` in place; can call child-register `0x40C62`; transforms family at `+0x08≥10`.
- `0x40E48..0x40EDE` (states 0x13–0x22): each `braw`s to a dedicated per-enemy update routine in
  `0x43636..0x4415a`. These are the individually-behaving materialized enemies (the CHECKPOINT-H
  family-update targets).

---

## CHECKPOINT B — `0x033E` / family-2 complete lifecycle (the key result)

**`0x033E` is a self-transforming SCANNER/HUNTER actor identity, NOT a visible enemy and NOT a
child-spawner-of-second-actors. It reuses the SAME ActorRecord and mutates its own identity in
place when its target map marker is found.** Proven end to end:

1. **Creation.** The field schedule (`0x4A104`, installer `0x4A086`) installs a family-2 slot:
   `+0x3E=2`, base resolved by `0x4544E`→`0x45494`→`0x454ba/d2/ea[variant]` = **`0x1E`=0x033E**,
   anim `0x93`, and `+0x1A` preset to **0x180 (off-screen hidden-Y marker)**. Initial `+0x05`
   (state) = 0 (actor slot clear). So a fresh family-2 actor is off-screen and in **state 0**.
2. **State 0 → `0x41180`** (the scanner). Two modes on `+0x03`:
   - `+0x03 == 0` — **floor-follower/navigator**: `0x41064` scans collision grid `0x10DE00` for a
     cell whose HIGH byte ∈ `0x31..0x3c` (not 0x34); on a hit `0x40a06`/table `0x40a86` transitions
     `+0x05`, and `0x41336`→`0x41d08` loads config `0x41d26[...]` into `+0x0D` (next target char).
     The floor markers are navigation/waypoints (turn, spawn-point), NOT enemies themselves.
   - `+0x03 != 0` — **char-hunter**: `0x41064` scans the grid for a cell whose HIGH byte equals its
     own `+0x0D` target char (`0x45..0x7b`, ASCII letters); on a hit the large `0x41180` dispatch
     sets `+0x05` to the enemy state, `+0x01` anim, `+0x16/+0x1A` position, and calls the enemy
     init. **`0x4103E` is the routine that CREATES a child char-hunter** (`+0x00=1 active,
     +0x03=1 hunter, +0x04=1, +0x1C=1 timer, +0x1A=0x180 off-screen`) — this is the only "spawn a
     second actor" step; it produces a latent off-screen hunter, not a visible enemy.
3. **Materialization (in-place identity mutation).** When the hunter finds its letter marker, the
   assigned state's handler rewrites the SAME record's identity. Example — state 0x0F armored man
   (`0x40CCC`, fully decompiled):
   ```
   40ccc tstb a4@(3)               ; hunter?
   40cd0 bne 0x40e0e               ; a4@3!=0 alt anim path (+ sound #23 at 0x40e2a)
   40cd4 tstb a4@(57)/bne 0x40dd8  ; a4+0x39 set -> base 0x0275 sub-path (0x40de2)
   40ce4 bclr #6,a4@(39)           ; +0x27 palette attr bit6
   40cea moveb #2,a4@(56)          ; +0x38 = compositor 2
   40cf0 movew #0x0a73,a4@(30)     ; +0x1E = 0x0A73  (ARMORED MAN, sword)
   40cf6 moveb #3,a4@(9)           ; +0x09 timer
   40cfc addqb #1,a4@(8)           ; +0x08 anim frame
   40d00 cmpib #4,a4@(8)/beq..bsr 0x40c62   ; register/candidate at frame 4
   40d0c cmpib #10,a4@(8)/bcc 0x40d32        ; at frame >=10 -> TRANSFORM
   40d14.. moveb table[+0x08]+11 -> a4@(1)   ; anim from 0x40dce
   ; transform block 0x40d32:
   40d4c moveb #12,a4@(62)         ; +0x3E = family 0x0C
   40dac movew #0x0a5a,a4@(30)     ; +0x1E = 0x0A5A (ball-and-chain armored variant)
   ```
   So one family-2 actor becomes the armored man (0x0A73), then its own record transforms to the
   ball-and-chain variant (0x0A5A) — the two R1 sub-round-2 armored-man varieties are one actor
   family self-mutating, not two spawns. `+0x39` selects a base-0x0275 sub-behavior; `+0x03!=0`
   selects an alternate anim with a sound cue.

**Consequences (answers the prompt's §5/§13 questions):**
- Does 0x033E render as a hostile? **No** — while it holds base 0x033E it is at Y=0x180
  (off-screen); it is never composited as itself.
- Controller or transform? **In-place transform** of the same ActorRecord (`+0x1E/+0x3E/+0x38/
  +0x01/+0x05` rewritten). The only separate allocation is the latent child hunter via `0x4103E`.
- Differs by compositor / variant / round / `0x13E` / marker? **Yes**: the family-2
  `(comp,variant)` selects the boss-family sub-table (`0x454ba/d2/ea`) and the variant advances per
  round-group; the found marker char selects the target state; `0x13E` gates specific transitions
  (dozens of per-value branches in `0x41180`); `+0x39`/`+0x03` select sub-behaviors.

---

## Remaining checkpoints (next targets)
- **C — DONE** (allocator/initializer architecture): see
  `docs/design/Andy_actor_allocation_initialization_decompilation.md` — 5 actor blocks, 7 `+0x00`
  activation writers, `0x49F30` occupancy scanner, `0x4A086` schedule installer, `0x4103E` child
  hunter, `0x45342` paired demon, `0x423B2/F4` boss components, `0x45330/0x4449E` boss trigger,
  `0x4543E`/`0x4544E` templates, and the new `0x4CD50` batch-swarm creator; retirement/reuse model;
  creator→state→`0x40BAA` graph.
- **D** — marker semantics table (floor `0x31–0x41` via `0x40a86`; letter `0x45–0x7b` via `0x41180`;
  hazard markers `0x3A`/`0x3D`).
- **E** — scene/map/collision descriptor format (`0x3951C`, `0x559B2/0x55A14`, `0x10DE00`).
- **F** — section/progression state machine (`0x13E/0x1242/0x1243/0x1386/0x138A/0x1394/0x10E8/0x1360`).
- **G** — section→actor reachability.
- **H** — family update routines (`0x43636..0x4415a`, `0x47140/0x473b8`) → behavioral class per family.

---
## C SOURCE BACKFILL
The A/B dispatch + lifecycle decompilation is preserved as auditable C under
`analysis/decompilation/c/` (`rastan_actor_dispatch.c` = 0x40BAA/0x40E74/0x41064; `raw/00040baa.c`
etc.). NOTE: `0x41180` is now **COMPLETE** — CHECKPOINT H6 hand-lifted the full state-0/
materialization dispatch (28 routes at `0x41362`), the per-branch position arithmetic, and the
`+0x0E` collision-cell-address semantics into `rastan_actor_materialization.c` + `raw/00041180.c`
(see `docs/design/Andy_h6_marker_materialization_decompilation.md`). The Ghidra export snapshot is
retained only as the historical cross-check.
See `analysis/decompilation/c/README.md` and `function_coverage.csv`.
