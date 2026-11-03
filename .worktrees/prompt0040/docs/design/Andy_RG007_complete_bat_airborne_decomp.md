# Andy — RG-007: Complete Bat / Airborne Arcade C Decompilation

**PROMPT RG-007** · **Agent:** Andy (Opus) · **Date:** 2026-10-21 · **Type:** original-arcade static
analysis / Ghidra-raw 68000 reconciliation / existing-C-decomp completion. **No production Genesis ASM /
ROM / build-number / HUD / audio / Palette Composer change.** Baseline Build 0466 untouched; clean tree
at start (preserved Cody + audio/palette work). Finishes the two RG-006 gaps plus the dependent
functions the bat chain needs. All C fidelity reconciled against `build/maincpu.disasm.txt` /
`build/regions/maincpu.bin`.

## Summary of completion

| Function | Prev status | Final status | Where |
|---|---|---|---|
| **0x473B8** airborne engine (states 1,2,0D,0E) | PARTIAL (anim tail) | **COMPLETE** | `rastan_actor_behavior.c` |
| **0x41CFA** per-state config loader | STUB | **COMPLETE** | `rastan_actor_behavior.c` + table in `rastan_actor_tables.c` |
| **0x4205C** camera-relative tracking (dependency) | undocumented | **COMPLETE (new)** | `rastan_actor_behavior.c` |
| **0x4736A** airborne ground/landing probe (dependency) | undocumented | **COMPLETE (new)** | `rastan_actor_behavior.c` |
| **0x41D26** per-state config data table | — | **COMPLETE (new)** | `rastan_actor_tables.c` |
| 0x4734A anim-rate pre-step | COMPLETE (RG-006) | COMPLETE | unchanged |

## 0x473B8 — COMPLETE (airborne engine)

Entry/dispatch: reached from state dispatch 0x40BAA for **states 1, 2, 0x0D, 0x0E**. Structure
(reconciled 0x473B8-0x47660):
1. **Init (first frame, +0x07==0):** `0x41CFA` loads the per-state config; then by family +0x3E seeds the
   flap duration +0x08 (family 1 → 4; **family 0x0A bats → `(+0x2E ? 2 : 7)`**) and runs the 0x4734A
   anim-rate pre-step.
2. **Core:** `0x3CEB0` (shared anim/motion). Clears +0x20 bit 0.
3. **Active pursuit + turn-around — ONLY states 1/2 (SKIPPED for 0x0D/0x0E):** `0x4205C` computes the
   camera-relative |distance| (A5+0x234) and target facing (A5+0x236); if in range (<0x68) and facing ≠
   +0x02 it flags a turn (+0x20 bit 0); a turn-timer state machine on +0x747 (0/1/2) with +0x740/+0x741/
   +0x746 performs the retarget/cooldown; at the turn window (distance in [0x30,0x34)) it **toggles state
   +0x05 ^= 3 (1↔2) and facing +0x02 ^= 1** and returns.
4. **Shared tail (ALL states incl. 0x0D/0x0E):** `0x4736A` ground/landing probe, then the **per-family
   8-way directional animation-frame selection** into +0x01.

- **States 0x0D semantics:** a **passive airborne sub-state** — it bypasses the active horizontal-pursuit
  / turn-around block (3) entirely (neither tracks the player nor flips facing) and runs only the shared
  core + landing probe + directional anim tail. Not init, not attack, not death. (Neutral: "passive
  airborne, non-pursuing.")
- **States 0x0E semantics:** same class as 0x0D (both skip the pursuit block via the single
  `state != 0x0D && state != 0x0E` guard at 0x47414); its distinct config record (0x41D26[0x0E] =
  `{0x03,0x30,...}`, flap dur 3) gives a different flap/animation seed than 0x0D (`{0x02,0x14,...}`).
- **Actor fields read:** +0x05 state, +0x07 init, +0x3E family, +0x02 facing, +0x16 X, +0x2E sub-mode,
  +0x740/+0x741/+0x746/+0x747 turn-timer, A5+0x234/0x236/0x200 globals.
- **Actor fields written:** +0x08 flap dur, +0x0A/+0x0B anim counters, +0x01 anim, +0x02 facing (toggle),
  +0x05 state (toggle), +0x20 bit0, +0x2B, +0x39 (via 0x4736A), +0x740/+0x741/+0x746/+0x747.
- **Animation/frame effects:** per-family selector. Family 0 → table 0x474EE +23; family 1 → flap counter
  +0x0A/+0x0B → table 0x47530 +35; **bat family 0x0A (0x4762E) → anim = `0x2D + direction`** where
  direction = `(A5+0x200 & 0x70)>>4` when +0x2E==0 (frames 0x2D-0x34) or `8 + ((A5+0x200 & 0x38)>>3)` when
  +0x2E≠0 (frames 0x35-0x3C). Orientation/mirroring is carried downstream by the facing +0x02 (and the
  Genesis VDP H-flip — RG-006), not by separate pixels.
- **Transitions:** turn-around toggles state 1↔2; landing (0x4736A) → state 0x0F (death/impact).
- **C:** `actor_flying_engine_473b8` (rewritten COMPLETE).

## 0x41CFA — COMPLETE (per-state config loader)

- **Index:** `state (+0x05) << 3` (× 8) into the table at ROM **0x41D26** (`lsl.w #3,%d0; lea 0x41D26`).
- **Table 0x41D26:** 8-byte records; 16 states captured (0x00-0x0F) in
  `g_airborne_state_config_41d26[16][8]`. **Byte → actor offset** (from the move.b stream 0x41D02-0x41D20):
  `[0]→+0x08 (anim dur), [1]→+0x0D, [2]→+0x0E, [3]→+0x0F, [4]→+0x10, [5]→+0x11, [6]→+0x13, [7]→+0x02`.
  No sign extension (all `move.b`); straight-line copy, no conditional branches; `rts`.
- **Callers:** the airborne engine 0x473B8 init (d0 = state). **Bat relationship:** bats enter airborne at
  state 1 (record `{0x02,0x17,0x01,0x01,0x04,0x04,0x01,0x01}` → flap dur 2) / state 2
  (`{0x02,0x33,...}`); the toggle path also uses 0x0D/0x0E records. This is where each airborne state's
  flap/motion parameters are seeded.
- **C:** `actor_airborne_config_load_41cfa` + `g_airborne_state_config_41d26`.

## Dependent functions newly decompiled

- **0x4205C `actor_airborne_camera_track_4205c`** (0x4205C-0x4208A): `d2 = ((cameraCenter A5+0x10BE +96)
  &0x1FF) - ((actorX +0x16 +96)&0x1FF)`; if `d2<0` → A5+0x236=1, `d2=-d2`; else A5+0x236=0; **A5+0x234 =
  |d2|**. Supplies the pursuit distance + target facing to 0x473B8.
- **0x4736A `actor_airborne_ground_probe_4736a`** (0x4736A-0x473B6): gated to active flight (returns if
  +0x07 set or state ≥ 0x0D); probes the collision grid 4px below (X +0x16, Y +0x1A+4 via 0x53A2E); air
  below → +0x74F++, solid below → +0x74F=0; after **≥3 consecutive solid frames** sets +0x39=1 and calls
  0x447F0 → state 0x0F — the bat's **land-on-ground → specialized death/impact** transition.

## SMALL BAT complete chain (base 0x0268, family/pool 0x0B, 1 piece, bank 0x36)

- Creation: marker/scripted spawn (map-driven `selector_08_1c / 0x0559B2→0x41180`) + batch creator
  0x4CD50 (swarms). **COMPLETE.**
- Initialization: 0x473B8 init → **0x41CFA** config (state 1/2 record) + family-0x0A flap seed + 0x4734A.
  **COMPLETE.**
- AI/state: dispatch 0x40BAA → 0x473B8 (states 1,2 pursuit; 0x0D/0x0E passive). **COMPLETE.**
- Movement: 0x3CEB0 motion core + 0x4205C tracking + turn-around toggle. **COMPLETE.**
- Animation: 0x473B8 bat branch 0x4762E → anim 0x2D + direction (+0x2E mode). **COMPLETE.**
- Orientation: facing +0x02 (toggled on turn) → downstream Genesis VDP H-flip (RG-006). **COMPLETE.**
- Frame selection: direct anim code into +0x01. **COMPLETE.**
- Render semantic output: PC090OJ 1-piece (native frame record; RG-006). **COMPLETE.**
- Damage: enemy one-hit via collision (0x449B4/0x44804 → state 0x0F). **COMPLETE.**
- Death: 0x42ABC bat branch (type 10/11 → base 0x0275 anim 0xA8, one frame) → retire 0x4092E; also
  land-death via 0x4736A→0x447F0. **COMPLETE.**
- Despawn: 0x4092E retire. **COMPLETE.**
- **Remaining STUB/PARTIAL dependency: NONE. Status: COMPLETE.**

## LARGE BAT complete chain (base 0x03F6, family/pool 0x0A, 2 pieces, bank 0x36)

Identical chain to Small Bat (same engine/config/anim/death); differs only in base (0x03F6), the config/
anim records (template `{0x03F6,0x01,0xB6,0x0002,0x0002}` → 2 pieces), and the +0x2E sub-mode seed. All
functions **COMPLETE**. **Remaining STUB/PARTIAL dependency: NONE. Status: COMPLETE.**

## Bat call-graph completeness (bounded)

Verified every function in the bat behavior/animation/presentation chain has coverage status COMPLETE:
0x4CD50, 0x45342, 0x40BAA, 0x473B8, 0x3CEB0, 0x41CFA, 0x4734A, 0x4205C, 0x4736A, 0x42ABC, 0x4092E,
0x44804, 0x447F0, 0x53A2E, 0x42E38. **No unresolved STUB/PARTIAL remains on the bat path.** (The
0x44804 row's "PARTIAL" is in the Ghidra-export-presence column, not the reconstruction-status column,
which is COMPLETE.)

## Files changed

- `analysis/decompilation/c/rastan_actor_behavior.c` — `actor_flying_engine_473b8` completed;
  `actor_airborne_config_load_41cfa`, `actor_airborne_camera_track_4205c`,
  `actor_airborne_ground_probe_4736a` added.
- `analysis/decompilation/c/rastan_actor_tables.c` — `g_airborne_state_config_41d26[16][8]` (0x41D26).
- `analysis/decompilation/c/function_coverage.csv` — 0x473B8 PARTIAL→COMPLETE; 0x41CFA STUB→COMPLETE;
  added 0x4205C, 0x4736A, 0x41D26.
- Research docs: this file; `Andy_RG006_flying_enemy_flip_and_hud_efficiency_research.md` status note.
- **Production files changed: NONE.** No ROM, no build number, no HUD/audio/palette/remap change.

## Unresolved

None on the bat / airborne path. (The per-family anim selectors for non-bat families 2-9 at
0x47536-0x4762E are the shared chain; they are outside the bat path and were not required, but the bat
family 0x0A selector is fully recovered.)
