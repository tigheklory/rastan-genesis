# 0x4A000–0x4C700 Scripted Actor Subsystem — decompilation

**Static arcade decompilation. No ROM/Genesis/bestiary/VM work, counter 359.** Discovery task: what
actor/spawn systems live in this previously un-analyzed region. Source: `maincpu.bin` linear sweep +
Ghidra exports. Original arcade PCs authoritative.

## What the region IS

A **scene-id-dispatched scripted-encounter subsystem** — the game's set-piece spawner (bosses +
scripted special enemies such as the Flying Demon). It is NOT a generic actor loader and NOT the field
schedule; it fires *specific* paired actors at *specific* progression scenes, once each.

**Top-level dispatch** (e.g. 0x4AB92+): a `cmpiw #scene_id, d0` chain on a progression **scene id**
`d0`, routing to per-scene handlers. Observed scene ids: `0x38, 0x3A, 0x3B, 0x3C, 0x3D, 0x40, 0x41,
0x58, 0x71, 0x86` (and more) → these are `A5+0x13E` progression positions spanning Rounds 2–6 (0x58≈R4,
0x71≈R5, 0x86≈R6 boundaries proven earlier). Each handler is further gated by the sub-progression
counter **`A5+0x10CC`** (compared to 1/3/9/10/13) and, for some, a map-collision check `jsr 0x45D10`.

**Per-encounter one-shot flags** occupy a contiguous block **A5+0x0208 … A5+0x026A** (~10 flags; the
Flying Demon's 0x0264/0x025A are part of this same block). Each handler sets its flag so the encounter
fires once. A **variant selector** `A5+0x0C5A` (0 or 1) is set immediately before the spawn.

## Creation primitives used (NOT new routes — the region drives the known ones)

- **Paired scripted spawn:** `jsr 0x45342` (`paired_actor_init`) — **12 sites** in-region → a two-slot
  paired actor (body+partner), variant via A5+0x0C5A → `paired_actor_activate 0x453A2`. Same primitive
  the Flying Demon uses (its 5 sites are in the adjacent 0x45Fxx dispatcher).
- **Direct scripted spawn:** `0x4BBCA` — sets fixed actor fields (X=0x140, Y=0x120, +0x38=1 compositor,
  +0x531=1) then `bsr 0x4543E` (record loader) + `bsr 0x45CFC` (activate). **1 site.**
So the region introduces **no new low-level creation primitive** — it is the scripted **trigger
layer** over `0x45342` and `0x4543E/0x45CFC`. That means the 7-route topology's *primitives* stand,
but the paired/scripted route is now shown to have a large scene-dispatched trigger table.

## Discovered scripted-encounter routes (OUTPUT — 13 in-region)

| site | scene id (d0) | 0x10CC gate | one-shot flag | variant 0xC5A | 0x45D10 gate | primitive | role |
|---|---|---|---|---|---|---|---|
| 0x4ABEC | 0x41 | <1 | A5+0x20A | 0 | — | 45342 | scripted paired encounter |
| 0x4ACE6 | 0x3B | — | A5+0x268 | 1 | — | 45342 | scripted paired encounter |
| 0x4ADC2 | — | <9 | A5+0x260 | 0 | — | 45342 | scripted paired encounter |
| 0x4B1EA | 0x58 | <1 | A5+0x26A | 0 | — | 45342 | scripted paired encounter |
| 0x4B20A | — | — | A5+0x208 | 1 | — | 45342 | scripted paired encounter |
| 0x4B31A | — | <10 | A5+0x262 | 1 | yes | 45342 | scripted paired encounter |
| 0x4BA48 | 0x71 | <1 | A5+0x208 | 0 | — | 45342 | scripted paired encounter |
| 0x4BB8E | — | <3 | A5+0x262 | 1 | yes | 45342 | scripted paired encounter |
| 0x4BCA8 | — | — | A5+0x25A | 0 | — | 45342 | scripted paired encounter |
| 0x4C440 | 0x86 | <13 | A5+0x208 | 1 | — | 45342 | scripted paired encounter |
| 0x4C4EA | 0x0C | — | A5+0x260 | 1 | — | 45342 | scripted paired encounter |
| 0x4C610 | — | <1 | A5+0x258 | 1 | — | 45342 | scripted paired encounter |
| 0x4BBCA | (called from 0x45FC2/0x45FFA) | — | — | — | — | 4543E+45CFC | direct scripted spawn (fixed pose, compositor 1) |

Plus the **5 Flying-Demon sites** (0x0458C8/0x045970/0x045FAC/0x045FE4/0x046124) in the adjacent
0x45xxx dispatcher use the same `0x45342` primitive → **~18 scripted-encounter triggers game-wide**.

**Actor identity per route:** all paired routes go through `0x45342`, which for the boss path
(+0x3E==2) selects `mode2_variant_a/b/c` (base **0x033E**) by variant, and for the demon path yields
base 0x0129. So these routes are **the round bosses + scripted special enemies (Flying Demon etc.)** —
multi-part paired actors. The exact base graphics per route requires tracing the seed each passes
(mode2 variant vs demon) and is **PARTIAL**: demon proven (0x0129); the others are boss-family 0x033E
variants (variant/seed-per-route not yet individually pinned).

## Item / power-up / drop system

**NOT found in this region.** 0x4A000–0x4C700 is a scripted-encounter (boss/special-enemy) subsystem;
no pickup/drop/power-up allocation or pickup-collision was located here. The item system remains
**UNRESOLVED / located elsewhere** (candidate: death-drop paths off the actor update functions).

## Ghidra change-list (headless unavailable — apply later)

Define functions/labels: `scripted_encounter_dispatch_4AB90` (scene-id chain);
`scripted_paired_encounter_<scene>` at each handler entry; `scripted_direct_spawn_4BBCA`;
data label `scripted_encounter_oneshot_flags` = A5+0x0208..0x026A; comment 0x45342 as the paired
scripted-actor primitive; annotate A5+0x0C5A as the scripted paired variant selector and A5+0x10CC as
the encounter sub-progression gate.

## Exhaustiveness

**NOT YET PROVEN EXHAUSTIVE.** Established: the region is a scene-dispatched scripted-encounter table;
12 in-region paired sites + 1 direct + 5 demon sites decoded with gating/flag/variant. Not yet done:
the full enumeration of every scene-id handler branch (some dispatch targets not traced to a site);
the exact per-route seed→base-graphics; the boss body/partner slot composition; and whether any
handler spawns a non-paired actor. The item/drop system is not here.
