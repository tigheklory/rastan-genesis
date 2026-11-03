# Round/Phase Progression Decompilation — 0x4A104 block mapping PROVEN

**Static arcade decompilation. No ROM, no Genesis, counter 359.** Continues
`Andy_4A104_spawn_schedule_semantic_correction.md`. Source: original arcade `build/regions/maincpu.bin`
+ existing Ghidra analysis. Original arcade PCs authoritative.

## A5+0x13E — GLOBAL progression counter (PROVEN)

`A5+0x13E` is a **single game-wide progression counter**, not per-round. Writers, decompiled:

| Writer | Function / role | Effect |
|---|---|---|
| 0x05025A | section (re)entry: `a1=ROM 0x5073A + A5@0x1242; A5@0x13E = a1.b` | **loads** the section-start value from ROM table 0x5073A, indexed by the section index A5@0x1242 |
| 0x0558FE | `FUN_000558e0` (map-segment advance; clears 0x10CC, bumps map ptr 0x10C6) | **increments by 1** each time the map crosses a segment (16-step) boundary — this is how progress accrues |
| 0x055F26 | scene/phase logic: `A5@0x13E = A5@0x13B8` | **restores** a phase-start value |
| 0x056014 | scene/phase logic: `A5@0x13E = A5@0x13B8 − 1` | phase-start restore, minus one |

It is **never reset to 0 per round** — it runs continuously 0x00 → 0x89 across the whole game.

## Round boundaries — ROM table 0x502AC (PROVEN)

The section logic at 0x50260 scans a word list at **0x502AC** = `0x16, 0x2D, 0x44, 0x5B, 0x72, 0x89,
0xFFFF` — the **six round boundaries in A5+0x13E**. So the rounds occupy contiguous 0x13E ranges:
R1 `0x00–0x16`, R2 `0x16–0x2D`, R3 `0x2D–0x44`, R4 `0x44–0x5B`, R5 `0x5B–0x72`, R6 `0x72–0x89`.
Each round spans ~0x17 (23) units of progression.

## A5+0x118 — round counter (PROVEN, from prior)

Round-transition routine 0x3A860–0x3A88E: `addqb #1,A5@0x118` (0x3A878), `cmpib #7` and cap the
companion 0x117 at 6 (0x3A880–88). 1–6.

## Why FUN_0004A0D8 subtracts A5+0x118

`block = (A5@0x13E − A5@0x118) >> 1`. Because 0x13E is global (0..0x89) and 0x118 is the round (1..6),
subtracting the round before the `>>1` **tiles each round's block window contiguously**: it removes one
block per round from the raw `0x13E>>1` mapping, so the six rounds' block ranges abut at shared
boundary blocks (10, 21, 32, 43, 54) rather than leaving gaps — and it compresses the whole 0..0x89
progression into exactly 66 blocks (0..65) instead of 0..68. The subtraction is a compaction/alignment
of the per-round windows, not a per-round reset.

## The 18-phase question — the arcade uses 6 rounds × {field, boss}, NOT 18

The **only** spawn boundaries in the progression are the six round boundaries (0x502AC). Within a round
the block index advances continuously with 0x13E; the **boss** occupies the tail blocks of each round
(the family-2 / base-0x033E seed path), fought as 0x13E crosses the round boundary. **There is no
outdoor-vs-castle spawn boundary** — outdoor ("Phase 1") and castle ("Phase 2") are *scene/map* state
(Plane data + the scene flags A5@0x1394/0x13B8), sharing the same continuous field spawn blocks. So the
arcade spawn schedule internally distinguishes **6 rounds × 2 spawn portions (field-enemies + boss) =
12 spawn contexts**, and the human "3 phases per round" maps to `field (outdoor+castle scenery) + boss`.
Forcing 18 independent spawn rosters would misrepresent the ROM.

## Proven per-round block map (verified against the boss data)

| Round | A5+0x118 | A5+0x13E range | block range | field blocks | boss blocks (family 2) |
|---|---|---|---|---|---|
| 1 | 1 | 0x00–0x16 | 0–10 | 0–7 | 8, 9, 10 |
| 2 | 2 | 0x16–0x2D | 10–21 | 11–18 | (10), 19–21 |
| 3 | 3 | 0x2D–0x44 | 21–32 | 22–29 | (21), 30–32 |
| 4 | 4 | 0x44–0x5B | 32–43 | 33–40 | (32), 41–43 |
| 5 | 5 | 0x5B–0x72 | 43–54 | 44–51 | (43), 52–54 |
| 6 | 6 | 0x72–0x89 | 54–65 | 55–61 | (54), 62–65 |

The family-2 (boss) blocks land **exactly** at each round's tail — an independent confirmation that
the 0x502AC boundaries + the index formula are correct. Boundary blocks (10/21/32/43/54) are the boss
block shared across the round transition. First record address of a block g = `0x4A104 + g*40`.

## Table extent (PROVEN — via max reachable index, not "byte looks valid")

Max round-6 0x13E = 0x88 → max block = `(0x88 − 6) >> 1 = 0x41 = 65`. So the table is **66 blocks
(0..65) × 40 bytes = 2640 bytes**, spanning **0x4A104 .. 0x4AB54**. Last legal record address =
`0x4A104 + 65*40 + 4*8 = 0x4AB44`. Data after 0x4AB54 is not addressed by this index.

## Per-round FIELD rosters (now PROVEN, not observed)

Union of +0x3E families over each round's non-boss blocks (all five records per block are proven
concurrent slots by `FUN_00049F30`):

- **R1:** Lizardman 0x004B, Chimera 0x00D0, Four-Armed Insect 0x02E8, Valkyrie 0x0241
- **R2:** + 0x0420, 0x0400
- **R3:** + 0x03B3
- **R4:** + 0x06E2, 0x0889 (0x0420 absent)
- **R5:** + 0x043A, 0x0420 (returns)
- **R6:** + 0x01CB (full late-game set)

R1's four are Composer-named/palette-proven; families 0x0420/01CB/03B3/043A/06E2/0889/0400 are
identity-proven (base code), names pending. Bosses all use base 0x033E (per-round differentiation via
variant/palette — a later task).

## Remaining unresolved progression semantics

- The exact outdoor→castle **scene** transition (A5@0x1394/0x13B8 + scene loader) — a *scene/map*
  boundary, not a spawn boundary; only needed to label field blocks outdoor vs castle.
- The finer per-segment table 0x5073A (per-map-segment 0x13E starts, indexed by A5@0x1242) is decoded
  as data but its full segment→scene labeling is not needed for the spawn roster.

## Next exact decompilation task

Decode the outdoor→castle **scene** transition (A5@0x1394 / 0x13B8 / scene loader around
0x55F00–0x56028) to label each round's field blocks as outdoor vs castle — the only remaining piece of
the human "3-phase" view. The spawn roster itself is now complete at round granularity.
