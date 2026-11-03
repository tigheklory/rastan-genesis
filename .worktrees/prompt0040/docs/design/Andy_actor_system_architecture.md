# Rastan Arcade Actor / Enemy System — Architecture (for the Genesis port)

**Static decompilation of `build/regions/maincpu.bin` + Ghidra
(`analysis/ghidra/rastan_arcade/exports/decompiler_export.c`). No Genesis/ROM/build; counter
360. No MAME was used in this pass.** This document explains **how the game creates and drives
actors** so the behavior can be reimplemented natively.

Terminology: each round has **SUB-ROUND 1**, **SUB-ROUND 2**, and **BOSS / SUB-ROUND 3**.
Sub-rounds are defined by game progression state (`A5+0x13E`), **not** by scenery. The scenery of
a sub-round 2 varies (exterior, stone interior, cave); scenery alone proves nothing about which
sub-round it is. The labels "outdoor" and "castle" are avoided as semantic definitions.

`A5 = 0x10C000` (arcade work RAM). A5-relative offsets map to absolute `0x10Cxxx/0x10Dxxx`.

## 1. Actor storage

Actors are `0x40`-byte records in A5 blocks of 9 slots (stride 0x40). Blocks referenced by the
writers: `A5+0x2C8`, `A5+0x508`, `A5+0x5C8`, `A5+0x748`, `A5+0x8C8` (KF-060/062). The scroll pass
`0x406a4` advances live ones; render is `0x41DAE` (normal) / `0x45DFA` (boss mode, `A5+0x2A2==2`).

### Key fields (proven)
| off | meaning |
|---|---|
| +0x00 | active |
| +0x01 | current animation / compositor-program index (live) |
| +0x02 | facing |
| +0x03 | **spawner mode** — 0 = floor-marker follower path; ≠0 = char-targeted spawner path (`0x41180`); set to 1 at `0x41044`/`0x4524e` |
| +0x04 | class / update selector (from schedule); seeds initial state `+0x05 = +0x04 + 1` |
| +0x05 | behavior/state index (drives `0x40baa` jump table at `0x40bc2`) |
| +0x06 | record type (for the `0x4543E` loader) |
| +0x0D | **target marker character** (0x31–0x41 floor / 0x45–0x7b letter), from config `0x41d08` |
| +0x16 / +0x1A | X / Y |
| +0x1E | base graphics tile code |
| +0x26 | schedule-slot index this actor occupies (refill bookkeeping, `0x49f30`) |
| +0x27 | palette attribute (`0x40 | nibble`) |
| +0x38 | compositor selector |
| +0x3E | family |
| +0x752 (A4-parallel) | per-slot variant nibble (NOT inside the 0x40 record) |

## 2. Base graphics — three resolution paths (`0x4544E`)

1. **Family + variant** (`0x4544E`): if `+0x3E == 2` → **family-2 path** (see §4b); else
   base = `0x45502[family*8]` (variant 0) or `0x45562[family*8]` (variant≠0); 8-byte records,
   word@0 → `+0x1E`, byte@3 → `+0x01` (anim), etc.
2. **Record type** (`0x4543E`): base = `0x45592[(+0x06) − 8]`, 8-byte records (bats, special
   enemies, boss bodies via `0x444E0[round]`).
3. **Direct** — `movew #base,+0x1E` in a specific state handler (e.g. armored men `0x0A73`/`0x0A5A`
   comp 2; the state handlers at `0x40DE2/0x40E9C/0x40F82/0x40FAC` set bases `0x0275/0x00F4/0x0DAB/
   0x09EA` and re-target `+0x0D`).

**Family → base (proven; matches `corrected_semantic_families.json`):**
f0=`0x004B` (Lizardman), f1=`0x00D0`, f3=`0x02E8`, f4=`0x0420`, f5=`0x01CB`, f6=`0x03B3`,
f7=`0x043A`, f8=`0x0241`, f9=`0x06E2`, f10=`0x0889`, f11=`0x0400`. **f2 = family-2 route
(`0x033E`).**

Palette (`0x45684`): family≠2 → nibble from `0x45722[(round-1)*12 + family]` (or `0x4576a` when
boss-mode `A5+0x2A2`); family==2 → boss palette `0x456EC`.

## 3. Render pipeline
`+0x38` → `0x3D054` selects one of five compositor programs → VM `0x3C902` expands the
`+0x01`-indexed piece program into SAT (tile = `+0x1E ± piece`, coords from `+0x16/+0x1A`, palette
`+0x27`). Palette loaded per round by `0x3BA20`.

## 4. Enemy creation systems (what the CODE proves)

The systems below are **mechanisms**. None is universally tied to a particular sub-round or
scenery; reachability per sub-round is a function of `A5+0x13E` gating and the map marker set.

### 4a. Field schedule `0x4A104` (installer `0x4A086`, consumer `0x4A0D8`/`0x40A1E`)
The **primary spawn source across ALL sub-rounds.** Indexed by `block = (0x13E − round) >> 1`;
each block is **40 bytes = 5 refillable 8-byte slots**. `0x49f30` finds the next free slot
(tracking occupied slots by `+0x26`, only counting actors with `+0x03==0`); `0x4A086` installs
one slot into a free actor in block `A5+0x4C8`.

**8-byte slot record → actor fields (proven at `0x4A086`):**
`[b0=class (+0x04), b1=family (+0x3E), b2 = (lo nibble → +0x38 comp, hi nibble → +0x752 variant),
b3 (+0x36), word b4:b5 → +0x1C timer (bit0 stripped as a flag → +0x2A), word b6:b7 → +0x34]`.
Then `0x4544E` resolves base and `0x45684` resolves palette. `+0x1A` is preset to `0x180`
(off-screen) so the actor is latent until its trigger.

The installed class byte seeds `+0x05 = class + 1` when the floor-follower path activates
(`0x41180`), which then drives `0x40baa`.

### 4b. Family-2 route (`0x033E`) — the sub-round-2 spawner mechanism
Family-2 slots resolve through `0x45494`: selector = `+0x38` compositor → table `0x454ba`
(comp 0), `0x454d2` (comp 3), `0x454ea` (else), indexed by `+0x752` variant. All in-range entries
carry **base `0x033E`, anim `0x93`** (verified). These family-2 actors are the mechanism by which
sub-round-2 hostiles are produced; their **variant advances per round-group** (v0 R1, v1 R4-ish,
v2 R5-6), selecting a different sub-round-2 enemy set. The `0x033E` actor's own semantic identity
(whether it is itself a visible enemy or a child-spawner) is **UNRESOLVED** — see §6.

### 4c. Ground-marker walker / char-targeted spawner (`0x41180`)
An actor whose update is the marker state machine:
- **`+0x03 == 0` (floor follower):** `0x41064` scans the collision grid `0x10DE00` (via `0x53a2e`)
  for a cell whose **HIGH byte of the collision word** is in `0x31..0x3c` (not `0x34`); on a hit it
  sets `+0x05 = +0x04 + 1`, then `0x40a06`/table `0x40a86` transitions `+0x05` and `0x41336`→
  `0x41d08` reads config `0x41d26` into `+0x0D` (next target char) etc.
- **`+0x03 != 0` (char-targeted):** scans for its own `+0x0D` target character (`0x45..0x7b`);
  on a hit the large dispatch in `0x41180` sets `+0x05` (state), `+0x01` (anim), `+0x16/+0x1A`
  (position) and calls the per-enemy init — **heavily gated on `A5+0x13E`** (dozens of per-value
  branches; boss-arm triggers at specific `0x13E`).

`0x40a86` is a 4-byte-record table `(cur_state, marker_char, new_state, terminator=0xFF)`. Floor
markers `0x31..0x41` → states `0x03..0x0e`; `0x34` flips walk direction; `0x3e..0x41` are
turn-around waypoints.

### 4d. Scripted / record-type (`0x45342`, `0x4543E`) and child/direct
`+0x06` record-type spawns via `0x45592` (bats, boss bodies `0x444E0[round]`); boss children
(`0x423B2/0x423F4`) and projectiles set `+0x1E` directly.

## 5. Sub-round structure (proven)
Round-end boundaries (`0x502AC`, words): **{0x16, 0x2D, 0x44, 0x5B, 0x72, 0x89}** — `A5+0x1360:=1`
and the round counter `A5+0x118` advances there. Sub-round-1→2 within a round is data-driven by a
collision tile of type `0x7E` → `A5+0x10E8:=7` → screen wipe → scene reload (proven mechanism,
KF scene map memory). The precise sub-round-2 entry `0x13E` per round is corroborated by the field
schedule (§4a): the schedule flips from mixed roaming families to a **family-2 (`0x033E`)
dominated region** at the sub-round-2 boundary. Code-derived sub-round-2 windows:

| Round | sub-round-2 `0x13E` | boss boundary |
|---|---|---|
| 1 | 0x11–0x16 | 0x16 |
| 2 | 0x28–0x2D | 0x2D |
| 3 | 0x3F–0x44 | 0x44 |
| 4 | 0x56–0x5B | 0x5B |
| 5 | 0x6D–0x72 | 0x72 |
| 6 | 0x7E–0x89 | 0x89 |

(These match the earlier MAME-cheat values within ±1–2 and are now grounded in the schedule data.)

## 6. Exact remaining static blockers (next targets)
1. **Per-scene letter-marker set.** The char-targeted enemies (`0x45..0x7b`) that materialize in a
   sub-round-2 depend on which letter markers are embedded in that scene's map-column collision
   data. Chain to decode: `A5+0x13E → 0x507C5[0x13E] = scene index → 0x3951C + scene*12 descriptor
   → column-layout long → column-record format loaded by `0x56128`/`0x561A0` → collision field
   `@(0x14 + row*8 + col*2)` (or `@0x22` when `@0x20==0xFF`) built into `0x10DE00` by
   `0x559B2`/`0x55A14` → HIGH byte = marker char`. Decoding the column-record format yields each
   sub-round-2 scene's exact marker set → exact char-spawned roster.
2. **`0x033E` family-2 semantic role.** Decode the `0x033E` actor update routine + compositor
   program (anim `0x93`) to determine whether `0x033E` is itself a visible sub-round-2 enemy or a
   child-spawner that emits the visible enemies (armored men, wizards, bats).
