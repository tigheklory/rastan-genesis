# Outdoor / Castle Section Map — Background-Bank Decompilation

**Static arcade decompilation from `build/regions/maincpu.bin`. No ROM build, no Genesis, counter
0359.** This pins the actual static data that drives per-scene background/tileset changes and
maps it to the six rounds. It follows the scene-state work in
`Andy_scene_phase_state_machine.md` and continues the trace of `A5+0x1242`, `A5+0x10C6`,
`0x10D0A8`, and the section/map-loading logic.

## Headline result (and an honest correction to the premise)

The arcade program does **not** carry a clean per-round "outdoor flag / castle flag." What it
carries is a **per-scene background-tileset bank byte (`TT`)** in a scene-descriptor table. That
byte changes in contiguous blocks, and those block boundaries are the game's real, statically
provable background/scene changes. Mapping the blocks to rounds shows a **background-bank change
mid-round only in Rounds 3, 5 and 6**. Rounds 1, 2 and 4 stream a *single* background bank for
their entire playfield. So "the Outdoor→Castle boundary for all six rounds" is only expressible
from this table for R3/R5/R6; for R1/R2/R4 no mid-round bank change exists to pin. This is
reported as found, not forced into a symmetric six-row table.

## The proven data path (all static)

Progression counter `A5+0x13E` (global 0..0x89) selects everything:

```
A5+0x13E ──(byte table 0x507C5[0x13E])──► A5+0x1386   = scene index (0..0xA8)
A5+0x1386 ──(×12, + 0x3951C)────────────► A5+0x10FC   = ptr to 12-byte scene descriptor
```

Decompiled at `0x50248` (0x1242→0x13E + round-boundary detect), `0x50294` (0x13E→scene index),
and `0x502cc`/`0x503a0` (scene index→descriptor pointer).

### The 12-byte scene descriptor at `0x3951C`
Two identical-shape 6-byte sub-records (the two alternating background column patterns the
streamer composites):

```
offset:  0    1    2  3  4  5
bytes:  00   TT   00 hh ll 1c        (sub-record ×2)
        └────┬────┘ └────┬─────┘
     word 0x00TT      long 0x00hhll1c
```

- **`TT` (byte 1) = background-tileset bank.** Consumed at `0x55c7a`: the word `0x00TT` is
  streamed as tile data into the background column DMA (base tile word of the column). It is a
  genuine background-appearance discriminator: e.g. scene 0x00 (R1) and scene 0x54 (R4) share the
  **same** layout pointer `0x0000D11C` but differ in `TT` (02 vs 08) — same column layout, a
  different background bank. So `TT` is the visual "kind" of the scene; the long pointer is the
  column layout.
- **long `0x00hhll1c` = the background column-layout data pointer** for that scene (fed to the
  column builder at `0x55c5e`/`0x55c7a` via the `0x10D0FC`/`0x10D100` staging pointers).

The descriptor pointer is read only at `0x55c4a` (`movel A5+0x10FC,...`), i.e. it exists solely
to drive background column streaming — confirming `TT` is background graphics, not gameplay.

### Round boundaries (separate, proven)
`0x50248`→`0x50266`: `A5+0x1360 := 1` exactly when `A5+0x13E` equals a value in the ROM boundary
table `0x502AC = {0x16,0x2D,0x44,0x5B,0x72,0x89}`, else `0x1360 := 255`. `0x1360==1` is the
round-end / boss gate (it is one of the three conditions that set the scene-complete phase
`A5+0x10E8 := 16` at `0x5122a`). So a round **ends at** its boundary 0x13E (the boss position);
round N spans `(boundary[N-1] .. boundary[N]]`.

## Proven background-bank (`TT`) sequence per round

`TT` value → 0x13E ranges (round N = `(prev boundary .. boundary]`):

| Round | 0x13E range | Background-bank (`TT`) sequence | Macro change(s) |
|---|---|---|---|
| **1** | 0x00–0x16 | `TT02` throughout | **none** |
| **2** | 0x17–0x2D | `TT03` throughout | **none** |
| **3** | 0x2E–0x44 | `TT0A` (0x2E–0x35) → `TT09` (0x36–0x3D) → `09/0A` interleaved (0x3E–0x44) | **@0x36** |
| **4** | 0x45–0x5B | `TT08` throughout | **none** |
| **5** | 0x5C–0x72 | `TT01` (0x5C–0x6B) → `TT0B` (0x6C–0x71) → `TT0E` (0x72) | **@0x6C**, **@0x72** |
| **6** | 0x73–0x89 | `TT03`(+`04` interleave) (0x73–0x82) → `TT0D` (0x83–0x88) → `TT0F` (0x89) | **@0x83**, **@0x89** |

Notes, honestly qualified:
- The rapid `09/0A` (R3 tail) and `03/04` (R6) alternations are the two interleaved column
  patterns of the descriptor, i.e. a compositing detail — **not** per-column scene cuts. The
  macro transitions are the ones listed.
- `TT0E` (R5 @0x72) and `TT0F` (R6 @0x89) are **single-position banks that sit exactly on the
  round-end boundary** — i.e. dedicated **boss-arena background banks**, distinct from the field
  bank of their round. (R1/R2/R4 bosses at 0x16/0x2D/0x5B reuse the round's field bank; R3 boss
  at 0x44 sits in the interleaved `09/0A` tail.)
- Distinct background banks used game-wide: `01 02 03 04 08 09 0A 0B 0D 0E 0F` (11 banks).

## Outdoor→Castle interpretation (what is proven vs. what still needs one visual pass)

**Proven from the ROM:** the mid-round background-bank changes above are the game's real,
static scene/theme transitions:
- **R3:** field bank `TT0A` → `TT09` at **0x13E=0x36** (the one clean mid-round background change
  in R3).
- **R5:** `TT01` → `TT0B` at **0x6C**, then → boss bank `TT0E` at **0x72**.
- **R6:** `TT03/04` → `TT0D` at **0x83**, then → boss bank `TT0F` at **0x89**.
- **R1, R2, R4:** **no mid-round background-bank change** — one bank streams the whole playfield.

**Not decided by this table (must not be fabricated):**
1. *Which* bank is "outdoor" vs "castle" — the labels require one visual ground-truth capture at
   the listed 0x13E positions (ORIGINAL ARCADE MAME frame, or GENESIS NTSC candidate). This pass
   deliberately does not import runtime/sweep data to assign the names.
2. R1/R2/R4 interior areas, if the game shows any, are **not** expressed as a background-bank
   change here. They would be produced within the single bank by the column-layout data (the
   long pointer), or by the discrete screen-wipe transition (`A5+0x10E8==7` trigger at `0x3a7d2`,
   set by the scene director at `0x52066`/`0x527cc`/`0x53f0c`/`0x54038`), whose per-round 0x13E
   firing points were not pinned statically in this pass. That mechanism is the named remaining
   target, not a guess to publish.

## Relationship to the scripted encounters / bosses (cross-check)
The scripted-encounter dispatch is `A5+0x13E`-driven (`0x4AB5C`), and boss routes sit at
round-tail 0x13E values (R3 via 0x41, R5 via 0x71, R6 via 0x86 — see
`Andy_scripted_encounter_actor_identity_map.md`). Those tail positions fall inside the boss-bank
regions found here (R5 `TT0B/0E`, R6 `TT0D/0F`), which is consistent: the boss scripted encounter
fires while the background has already switched to the round's interior/boss bank.

## Tables (authoritative addresses)
| Address | Meaning |
|---|---|
| `0x502AC` | round-boundary values in `0x13E` = `{16,2D,44,5B,72,89, FFFF term}` |
| `0x507C5` | byte table `0x13E → scene index` (`A5+0x1386`), 0..0x8A |
| `0x5073A` | byte table `0x1242 → 0x13E` (master section index → progression) |
| `0x3951C` | 12-byte scene descriptors (two `[00 TT 00 hh ll 1c]` sub-records); `TT`=background bank, long=column-layout ptr |
| `0x50EE0` | byte table `0x13E → map-stream byte offset` (into `0x50F6B`); the scrolling column stream |
| `A5+0x1360` | =1 at exact round boundary (boss/round-end gate), else 255 |
| `A5+0x10E8` | scene-director micro-phase (scroll/stop/transition); ==7 and ==16 drive screen-wipe transitions at `0x3a7d2`/`0x3a83a` |

Consumers: `0x50248` (section→progression + boundary flag), `0x50294`/`0x502cc`/`0x503a0`
(scene index + descriptor pointer), `0x55c2e`/`0x55c4a`/`0x55c5e`/`0x55c7a` (background column
streamer that reads `TT` and the layout pointer).
