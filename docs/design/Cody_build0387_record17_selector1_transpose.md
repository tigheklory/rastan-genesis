# Cody — Build 0387 Record-17 Selector-1 Transpose Correction

**Agent/task:** Cody — third-chain record-17 selector-1 source-coordinate audit and general native
resolver correction. **Baseline:** Build 0386. **Produced:** Build 0387. **Status:** canonical and
mechanical gates pass; natural third-chain traversal requires Tighe's gameplay validation.

## Human trace and record identity

The existing bounded user-controlled GENESIS NTSC MAME trace was reused. Tighe pressed `M` just
after attaching to the third chain. The capture is complete (`USER_MARK` frame 3090, 720 following
frames) and identifies:

| Field | Marked value |
|---|---:|
| progression `A5+0x013E` | `0x0011` |
| runtime stream pointer `A5+0x10C6` | `0x00051183` |
| selector `A5+0x10A8` | `0x0001` |
| strip/group | `0 / 0` |
| player state / X / Y | `4 / 0x0121 / 0x0040` |
| foreground X/Y fields logged by the trace | `0x015F / 0x01DA` |

The current Build-0386 address map maps runtime `0x51183` to original arcade `0x50F7D`
(`identity_offset=0x206` in that segment). Original byte `0x50F7D=1`. This is therefore the exact
record-17, selector-1 vertical stream—not the old mixed selector-0 automated state. The capture
keeps that pointer and selector throughout. Climb input advances scroll `0x01DA -> 0x01FF -> 0x0000
-> 0x0028`; strip/group advances `0/0 -> 2/1`; Rastan remains attached in state 4 at the stop.

## Original arcade transform

Original `0x055990/0x055A14` iterates descriptor-table index `k=0..15` and cell `i=0..3`.
For selector 1:

```text
q = (~strip) & 3
world_row    = group*4 + q
world_column = k*4 + i

raw_row      = world_column
raw_column   = world_row

descriptor  = live_source_table[k]
cell_offset = q*8 + i*2
```

Thus the raw grid is transposed exactly once into world space, with selector-1's within-metatile
row inversion. Selector 2 uses `q=strip&3` but the same swapped table/cursor axes.

## First divergence

The native selector-1/2 producer correctly formed `world_row` and `world_column`, then passed them
to `resolve_plane_a_cell` and `resolve_plane_a_collision_cell`. Both resolvers applied the
selector-0 source equation:

```text
descriptor = live_source_table[world_row >> 2]
           + X-ring-delta(world_column >> 2)
```

For selector 1/2 the arcade equation is instead:

```text
descriptor = live_source_table[world_column >> 2]
           + Y-ring-delta(world_row >> 2)
```

The within-metatile offset was already correct. The first broken semantic contract was therefore
the descriptor table axis and cursor-delta axis: the raw→world transpose was missing at descriptor
selection. Plane-A visuals and gameplay collision agreed with one another only because both called
the same wrong horizontal formula.

### Bounded upper-exit proof

Using the human trace's live source table at group 1, the 5×8 corridor rows 59..63 / columns 54..61
contains 40 cells. The old native formula chose a different descriptor coordinate for 28; seven
resolved tile words differed. Collision values happened to match in this narrow sample, which
explains why the earlier value-only head-cell proof did not reveal the axis error.

Representative head cell at world `(63,58)`:

| Path | Descriptor | Record | visual source/value | collision source/value |
|---|---:|---:|---:|---:|
| arcade selector-1 transform | `0x0353D8` | `0x3A2C` | `0x003A44 / 0x0817` | `0x003A4E / 0x0001` |
| old Genesis horizontal formula | `0x037694` | `0x3A08` | `0x003A20 / 0x0814` | `0x003A2A / 0x0001` |

The identical final collision property is coincidental; source-coordinate equality fails. Across
the complete 64×64 marked ring epoch, the old formula differs in 3,844 descriptor coordinates,
2,942 visual tile values, and 1,535 collision values.

## Exactly-once path audit

| Path | Input | Transform before Build 0387 | Build-0387 result |
|---|---|---|---|
| selector-1/2 producer | retained selector/group/strip | creates world row/column and inversion | unchanged |
| Plane-A resolver | WORLD/RING | incorrectly reuses selector-0 row-table/X-cursor formula | column-table/Y-cursor; transpose completed once |
| collision publisher | WORLD/RING | same incorrect selector-0 formula | calls the same corrected descriptor selector |
| row/column streamer | retained edge event | destination row/column correct | unchanged |
| live/ring descriptor selection | live `A5+0x1000` pointers | unwraps on X for every selector | X for selector 0; Y for selectors 1/2 |
| player collision lookup | published 64×64 collision ring | no transform; consumes final ring cell | unchanged |

Missing transpose before fix: **YES, at descriptor selection.** Double transpose: **NO.**

## Fix

`apps/rastan-direct/src/tilemap_hooks.s` now has one shared descriptor-selection helper used by
both `resolve_plane_a_cell` and `resolve_plane_a_collision_cell`:

- selector 0 preserves the existing table-by-world-Y and cursor-by-world-X contract, including
  resident-column ring unwrapping for row publication;
- selector 1/2 indexes the live table by world-X, applies cursor delta along world-Y, and unwraps
  not-yet-published cells according to selector 1's `3,2,1,0` or selector 2's `0,1,2,3` order.

No record, stage, chain, coordinate, collision-property, or MODE special case was added. The
semantic cut remains retained arcade map selector/source state → final Genesis Plane-A staging and
final Genesis gameplay collision ring. No PC080SN shadow, C-window authority, or gameplay rewrite
was introduced.

## Build and validation

- Build counter: `386 -> 387`
- Opcode replacements: `231` (unchanged)
- Canonical coverage: `0x1A9EB8` (unchanged)
- Canonical ROM: `dist/rastan-direct/rastan_direct_video_test_build_0387.bin`
- Canonical SHA-256: `db33a09915695d7020538848c51e2c58716c5571c4eabf33e804badc56b1c46b`
- Canonical size: `1,744,568` bytes
- `_c` SHA-256: `b7ff58823125505a6f6e3c9ab558c3e8b354cfd2bb293a7703caca96c9bfa12b`
- `_c` size: `1,748,664` bytes
- `_d`: `36f5bde01a9a34254456d1cc206d97d37559a0e651ab5656a794433b3191888a`
- `_s`: `8276d4a7b75e10eba3c4e89524c5a86a5528353b53a5c468e577e47de3c3c146`
- `_do`: `e4e36e0f6604ec3289c7842a3cd070350110ccb53bf993bb986d644a5fab6ecb`
- Complete five-variant family: **PASS**
- Boot guard, canonical gate, gameplay-entry gate, transition-retention gate: **PASS**
- Seven-epoch gate: **FAIL, pre-existing recent-baseline condition; artifact preserved**
- GENESIS NTSC MAME standard 30-second trace: 1,798 frames, no unmapped writes reported by the
  generated summary; final PC `0x073BA6`, unique unmapped addresses none.

Existing project tools reused: current address map/disassembly, original arcade disassembly/Ghidra
exports, Build-0378 corridor evidence, and the bounded Build-0386_c human trace.

New tooling created: **NONE**. The source-coordinate matrix was calculated directly from the retained
trace source table and original ROM data.

Legacy intentionally remaining: original arcade map progression, descriptor producers, scroll and
player collision consumers; native final staging/collision publishers remain required. No legacy
chip tail was newly removed; this task corrects the already-native semantic resolver.

## USER MUST VERIFY

Using Build `0387_c` in BlastEm or GENESIS NTSC MAME:

1. press MODE once after Round 1 begins to enter Phase 2;
2. verify the selector-1 fortress shaft/terrain is composed correctly;
3. reach, attach to, and climb the third chain;
4. verify Rastan enters the arcade-intended upper route instead of falling to the lower section;
5. continue natural gameplay beyond the transition;
6. confirm ordinary horizontal terrain, collision, ropes, water death, weapons, and Build-0386
   Flying Demon behavior are not regressed.

Natural third-chain traversal: **USER TEST REQUIRED**. STOP status: production correction built and
mechanically validated; acceptance remains with Tighe.
