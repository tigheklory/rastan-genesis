# What must be decompiled to know ALL actors and palettes correctly

**Analysis only. No ROM, counter 359. The bestiary report is NOT updated (per Tighe).** This answers
*why* the report is incomplete/wrong and *exactly* what static decompilation fixes it.

## Root cause: the report is SWEEP-derived, not TABLE-derived

The whole-game lexicon (`analysis/enemy_sprite_lexicon/`) was built from a **runtime MAME actor
sweep** — it captured whatever sprite pieces and palette banks happened to be on screen at a *sampled
frame* per round. That is the single reason everything past a couple of R1 actors is unreliable:

- **Same-looking bosses across rounds** — all six boss rows were keyed to actor base `0x033E` and a
  *sampled frame* (`sample frame 2772 at round1_boss`, etc.). The per-round boss *selection and
  composite* were never decoded, so the renders are whatever the sweep grabbed, not the real distinct
  bosses.
- **"Dragon heads" / garbage composites** — a sampled frame captures a *partial or mixed* set of
  PC090OJ pieces (mid-animation, or another actor's pieces overlapping). Without decoding the actor's
  **mapping/composite table**, the "representative frame" is not a real, complete actor frame.
- **Colors wrong (even R1P1)** — I only had RGB for the **3 palette banks that were loaded in the one
  captured scene** (0x30/0x33/0x36). Every other actor fell back to grayscale — including R1P1 enemies
  whose banks are *known* (insect 0x3A, valkyrie 0x32, chimera 0x34, demon 0x35, bats 0x3E) but whose
  **palette RAM was never decoded**. That was my miss: the palette *data* is in ROM and can be
  decompiled; I leaned on a capture instead.

The fix is to replace the sweep with **static decompilation of four data systems**. All addresses
below are original arcade PCs, confirmed present in the Ghidra exports.

---

## 1. PALETTE SYSTEM — ALREADY DECOMPILED in the Palette editor tool (NOT a decompile task)

**Correction (Tighe):** this is already solved. The palette pool was reverse-engineered and validated
by the Palette editor tool. `analysis/graphics_optimizer/round1_phase1_corpus/enemy_palettes.json`
holds **PROVEN 16-color palettes** (raw 0RGB, converted xBGR555, and `mame_display_rgb8`) for all
seven Round-1 enemies — Lizardman 0x36, Four-Armed Insect 0x3A, Valkyrie 0x32, Chimera 0x34, Flying
Demon 0x35, Small Bat / Large Bat 0x3E — and documents the exact decode:

> round index table `0x3BA88 + (round-1)*0x20` → pool index → palette = pool `0x4FD02 + pool_index*0x20`
> (loader `FUN_0003ba20/56/64`); effective bank = emitted word0 nibble | colbank 0x30; validated vs
> KF-1214 (round-1 pool index 13 @ `0x4FEA2`, green Lizardman).

So the "decompile the palette pool" step is **done**. My bestiary rendered R1 enemies grayscale only
because I read the wrong file (`round1_phase1/palette_states.json`, a 3-bank capture) instead of the
tool's `enemy_palettes.json`. **My mistake, not a missing capability.**

**What remains for palettes is a script run, not RE:** `enemy_palettes.json` is Round-1 only. The
decode formula above is round-parameterized, so extending to Rounds 2–6 is running the *already
reverse-engineered* decode for each round (the tool's `gen_reindexed_pc090oj.py` path already does the
pool math) — feed each round number + the effective bank per actor. No new decompilation.

**Deliverable:** reuse `enemy_palettes.json` as-is for R1; run the documented pool decode for
Rounds 2–6 → `(round × effective bank) → 16 RGB`. This is tool work, not Ghidra work.

## 2. PER-ROUND/PHASE ROSTER — fixes "which actors appear where"

The true roster comes from the **per-stage spawn/map tables**, not observation.

Decompile:
- **Map collision-marker data per round** — consumed by `phase_collision_marker_publish` (0x559B2) →
  `actor_spawn_ground_and_activate_41180` (0x41180), indexed by **stage `A5+0x118`** + **progression
  `A5+0x13E`**. This is the "which marker → which family at which map position" data per round/phase.
- **Static seed tables** (48 records at ROM `0x454BA`, `mode2_variant_a` etc.) + selector
  **`FUN_0004544e` (0x4544E)** / table `0x45502` (+0x3E family) — the seed → actor-class/family map.
  `FUN_0004A086` (0x4A086) is the actor init that calls *both* 0x4544E (family) and 0x45684 (palette).

**Deliverable:** the authoritative actor-class list spawned in each of the 18 round/phase slots.

## 3. BOSS SYSTEM PER ROUND — fixes the identical/duplicated bosses

Decompile:
- **`FUN_00041F30` (0x41F30)** — the frame/boss render owner, called from the arcade VBlank vector
  target `vector_1d_target_03a008` (0x3A008); it dispatches boss record ownership, palette
  (`0x45D72`), `0x47004`, and render (`0x41DAE`). Follow it to the **per-round boss actor/class
  selection** (the +0x3E==2 boss path gated via **+0x752**), and find the **per-round boss
  definition/table** — the six rounds have distinct bosses, so there is per-round boss data, not one
  0x033E composite.

**Deliverable:** the distinct boss actor + its real composite for each of Rounds 1–6.

## 4. ACTOR ANIMATION → COMPOSITE → GRAPHICS CODES — fixes garbage frames, enumerates real ones

This is the largest effort and what removes the "mess": decode the actual frame data instead of
sampling.

Decompile:
- **Render family composite tables** `0x3D09E` / `0x4771C` / `0x3F0CE` / `0x040004` / `0x04002C`
  (selected by `actor_family0_render_3d054` @ 0x3D054, expanded by `actor_four_record_expand_3c902` @
  0x3C902 into `[control, signed_y, code_offset, signed_x]` quartets). Recover **full table contents +
  the index mechanism** (how an animation state maps to a composite entry).
- **Per-family update / state-machine routines** that set the animation/composite index — the
  still-unnamed actor update `FUN_`s reached from the actor dispatch loop. These define each actor's
  **legal frames**.

**Deliverable:** for every actor, every legal frame's exact piece list and PC090OJ graphics codes —
so composites are real and complete, and the graphics-code enumeration (currently `PENDING`) closes.

---

## Order & payoff

| Step | Fixes | Decompile? | Status |
|---|---|---|---|
| 1 Palettes | all colors, all rounds | **NO — already done in the tool** | R1 proven in `enemy_palettes.json`; R2–6 = run the documented pool decode (script) |
| 2 Spawn/roster tables | correct per-round/phase actor lists | yes (Ghidra) | needed |
| 3 Boss dispatch | 6 distinct bosses | yes (Ghidra, `0x41F30`) | needed |
| 4 Family composite tables + anim selectors | real frames, no garbage, code enumeration | yes (Ghidra) | needed, per family |

**The genuine decompilation gap is steps 2–4, not palettes.** Palettes are the tool's job and are
already reverse-engineered. Steps 2–3 fix the roster and the six distinct bosses; step 4 replaces the
sampled ("dragon-head") composites with each actor's real frames and closes graphics-code enumeration.
None of it needs a runtime sweep — it is static ROM/table decompilation, plus reusing the existing
palette tool output.

## RE-PROVEN palette-assignment path (2026-09-17) — corrects the Round-6 bug

Full path from `FUN_00045684` (called at spawn 0x4a0ce):
- family==2 (boss) → boss palette table `0x456EC` indexed `variant*18 + (round-1)*3 + compAdj`.
- else → normal table **`0x45722`** indexed **`(round-1)*12 + family`** (2D: 6 rounds × 12 families);
  if `A5+0x2A2 != 0`, alternate table `0x4576A` (same shape). Result nibble → `actor+0x27 |= 0x40|nibble`
  = the sprite's **palette LINE**.
- The nibble is **round-invariant** in practice (only R5/fam7 differs: 0x0F→0x02). So per-round color
  does NOT come from the line index.
- Per-round color comes from the **palette DATA** loaded per round by `FUN_0003BA20`: for line i,
  `pool_index = maincpu[0x3BA88 + (round-1)*32 + i]`, palette = `0x4FD02 + pool_index*32` (16 0RGB
  words; 0RGB→RGB8 via the loader's bit re-pack). Validated vs enemy_palettes.json for R1.

**Round-6 audit result:** the pool index DOES change per round for most families
(Lizardman fam0 pool 13 R1–R3 → 14 R4–R6; Chimera 18→19; Four-Armed 22→23; 0x0420 11→25; 0x03B3 11→26).
The report was wrong for later rounds **only because the bestiary rendered a pre-colored R1
`composer_png`** (baked colors) for Lizardman/Chimera/Four-Armed/Valkyrie, so every round showed R1
colors. Fixed: those with clean lexicon geometry now render `rom_geo` recolored by the per-round ROM
palette; Valkyrie (no geometry) is `LEGACY_PROVISIONAL` with a per-round swatch and its image labeled
"R1 reference — not multi-round proof". Manifest actors now carry `palette_instances` (per-round pool
index + swatch). 5/11 field actors have colors that change across rounds.

**Boss palette + frame:** boss line nibble = `0x456EC[(round-1)*3]` (var0/comp0): R1/R2 nibble 4
(pool 18, orange), R3–R6 nibble 0 (pool 11). Bosses render per-round from `round{N}_boss_composite`
geometry + per-round boss palette (6/6 frames, 6/6 palettes). Creation: 2-slot paired actor
A5+0x508/0x548 via `0x45342`; variant from `A5+0xC5A` (+0x06=8/9); base via `0x4543e`; family2/base
0x033E is the shared route, not the identity. R5/R6 anim override `+0x28:=4,+0x2C:=7` at `0x453c0`.
