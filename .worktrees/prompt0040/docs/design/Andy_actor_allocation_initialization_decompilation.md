# Rastan Arcade Actor Allocation / Initialization — Decompilation (CHECKPOINT C)

**Static decompilation of `build/regions/maincpu.bin` + Ghidra exports. No MAME, no Genesis, no
build; counter 360.** Manifest and bestiary intentionally NOT touched (per task). Evidence:
`analysis/actor_decompilation/allocator_inventory.txt`, decoders under `tools/analysis/`. Live
Ghidra headless is absent in the repo → this is the exact change-list/model for later import.
`A5 = 0x10C000`. Terminology SUB-ROUND 1/2/BOSS.

---

## 1. Actor storage blocks (each record = 0x40 bytes)

Derived from the render/expand pass `0x41DAE` (normal) and `0x45DFA` (boss-mode), and from the
creators. **These are distinct fixed-function pools, not one array.**

| Block | A5 off | slots | dest PC090OJ record (0x41DAE) | expand d2/slot | role / creator |
|---|---|---|---|---|---|
| `0x2C8` | 712 | 9 | 140.. | 10 (19 for slot 8) | **field-schedule / ground-enemy pool** (lizards). Scanned by `0x49F30`; installed by `0x4A086` (base slot A5+0x4C8 scanning **down** to 0x2C8). |
| `0x508` | 1288 | 2 | 57.. | 13 | **Flying Demon** two-component (`0x45342` fixed slots 0x508/0x548). |
| `0x5C8` | 1480 | ~6 | 96.. | 4 | **boss components** (`0x423B2` fills 5). |
| `0x748` | 1864 | ~11 | 46.. | 1 | single-sprite actors; **`0x4CD50` batch-creates** here; `0x457B6` scripted. |
| `0x8C8` | 2248 | — | (boss-mode) | — | boss/special (`0x45DFA` render iterates 0x5C8/0x748/0x8C8). |

The whole region `A5+0x2C8 …` is zeroed wholesale at scene/round reset (`0x3A67A` fills 1567 words,
`0x3A804` fills 1023 words) via the propagating fill `0x3A2D0`.

## 2. Every `+0x00` activation writer (completeness basis)

`moveb #1, rec+0`: **`0x4103E`** (A4), **`0x423C4`** (A4), **`0x45248`** (A4), **`0x453A8`** (A4,
`0x453A2`), **`0x45CFC`** (A4), **`0x4A0BA`** (A4, inside `0x4A086`), **`0x4CD50`** (A2). Plus the
wholesale scene clears (`0x3A67A`/`0x3A804`) and single-retire clear `0x427B2`. No other `+0x00`
activation form (via `st`/`move dN`) exists in the actor range.

## 3. `0x49F30` — occupancy scanner / free-slot finder (block 0x2C8)

Not an allocator; an **occupancy scan** feeding the schedule. Clears `A5+0x214` (iter), `A5+0x29A`
(occupied count), `A5+0xC52` (per-slot-owner bitmap, longword), sets `A5+0xC56 = 0xFF` (result =
"no free"). Walks the 9 records of block 0x2C8 (`A5+0x2C8`, +0x40 each); for each **active**
(`+0x00!=0`) **and floor-follower** (`+0x03==0`) record it marks the schedule-slot it occupies:
`A5+(0xC52 + rec+0x26) = 1`, and increments `A5+0x29A`. `+0x26` is therefore the **schedule-slot
id** (0..4) an actor owns. Returns via `A5+0xC56` the first schedule slot NOT owned by any live
actor (else stays 0xFF). This is how the 5-entry schedule refills: a freed `+0x26` slot becomes
available for a new latent actor → small schedule → long enemy stream over a sub-round.

## 4. `0x4A086` — field-schedule installer (block 0x2C8)

8-byte `ActorScheduleEntry_0x08` → new ActorRecord (called from `0x4A07A`/`0x4A100`; the free actor
slot is found by scanning block 0x2C8 down from A5+0x4C8 for `+0x00==0`):

| entry byte | actor field | meaning |
|---|---|---|
| b0 | `+0x04` | class / update selector |
| b1 | `+0x3E` | family |
| b2 lo nibble | `+0x38` | compositor |
| b2 hi nibble | `+0x752` (A4-parallel) | variant |
| b3 | `+0x36` | field36 |
| w4 (bit0 stripped → `+0x2A`=1) | `+0x1C` | countdown timer |
| w6 | `+0x34` | field34 |

Then: `+0x00 = 1`, `+0x1A = 0x180` (off-screen Y), `0x4544E` (base/graphics template), `0x45684`
(palette). **NOT written (rely on the slot being pre-cleared): `+0x05`(=0 → state 0 scanner),
`+0x03`(=0 → floor-follower mode), `+0x0D`(target char), `+0x16`(X), `+0x02`(facing), etc.** This
matters for Genesis: a stale slot would carry a wrong state/mode.

## 5. `0x4103E` — child-hunter allocator

Jump-table/computed-reached (0 direct callers; entered from the marker-spawn table at `0x41000`).
Creates a latent hunter in the current A4 slot: `+0x00=1`, **`+0x03=1` (hunter mode)**, `+0x04=1`,
`+0x1C=1` (timer), `+0x20=1`, `+0x1A=0x180` (off-screen). The target marker char `+0x0D` is set by
the config loader `0x41D08` (from table `0x41D26`) before/around this. Reachable behavior: state 0
→ `0x41180` which, with `+0x03!=0`, hunts its `+0x0D` letter marker. Parent→child link is implicit
(same block, config-driven), not a stored pointer.

## 6. `0x45342` — paired Flying-Demon initializer (17 scripted callers)

Fixed slots (NOT a free search): guards on `A5+0x548`; sets record type `+0x06` of both slots
(`A5+0x50E`, `A5+0x54E`) to **8 or 9** by variant `A5+0xC5A`; sets flags `A5+0x52F|=0x80`,
`A5+0x56F|=0x80`; calls `0x453A2` (activate) twice. `0x453A2`: `+0x1C=1, +0x00=1, +0x05=3 (state 3
→ 0x47140 walking-update), +0x1A=0x180, 0x4543E`. So the two block-0x508 records (0x508, 0x548) are
one two-component actor (the Flying Demon, records 57–82; cf OPEN-027, base family via record type
8/9). 17 callers = the scripted-encounter dispatchers across rounds (`0x458C8/0x45970/0x45FAC/…`).

## 7. `0x45330 → 0x4449E` — boss record-type trigger

`0x45330` bsr `0x4449E` (clears `A5+0x13AC`, selects boss record type via `0x444E0[round-1]` →
`0x4543E`/`0x45592`). Generic mechanism = record-type actor creation; the boss-specific part is the
per-round `0x444E0` table (record types {0E,13,14,15,10,17}).

## 8. `0x4543E` — record-type template loader (`RecordTypeActorTemplate_0x08`)

`base_ptr = 0x45592 + (rec+0x06 − 8)*8`. Fields: `word@0 → +0x1E` (base graphics),
`byte@2 → +0x3A`, `byte@3 → +0x01` (anim), `word@4 → +0x28`, `word@6 → +0x2C`. Then `0x453D6`
(difficulty tuning of +0x28/+0x29 by `A5+0x2F`). Legal record type ≥ 8 (index = type−8). Used by
scripted/paired/boss creators (§6, §7, `0x45B18`, `0x45CE0`, `0x4BBCA`, `0x423B2`).

## 9. `0x4544E` — family template (`FamilyActorTemplate_0x08`, same 8-byte layout)

`+0x3E==2` → `0x454BA`(comp0)/`0x454D2`(comp3)/`0x454EA`(else) indexed by `+0x752`variant*8; else
`0x45502`(var0)/`0x45562`(var≠0) indexed by `+0x3E`*8. Same field writes as §8
(`+0x1E/+0x3A/+0x01/+0x28/+0x2C`) then `0x453D6`. **base `0x033E` is simply the family-2 template's
`+0x1E`** — the hidden-scanner graphics identity, off-screen at Y=0x180 (CHECKPOINT B). It is a
creation-template value, not a special init semantic; the runtime scanner role comes from state 0 /
`0x41180`, and the record self-transforms its `+0x1E` on materialization.

## 10. `0x423B2` / `0x423F4` — boss multi-component creators

`0x423B2` (called from boss dispatcher `0x42376`): block `0x5C8`, loop slots 0..4 (5 components):
`+0x21 = component index (0..4)`, `+0x00=1`, `+0x38=1` (comp1), `+0x05=0x11` (state 0x11 → 0x4684e),
`+0x06=0x11` (record type 17), `0x4543E`. `0x423F4` (from `0x42364`): same into `A5+0x648`.
`+0x21` is the **component/sibling index** (parent/child link); the update `0x42380` iterates the 5
and syncs facing (`+0x02`) + calls `0x43458` with index+13. These are specific boss helpers, not a
generic child constructor.

## 11. Additional allocator discovered — `0x4CD50` (batch/swarm creator)

A2-based free-slot batch creator into block `0x748` (up to 11 slots, `dbf d4=10`): per free slot
sets `+0x00=1`, position `+0x16/+0x1A` from an `a0` coord stream + base `d0/d1`, home `+0x14/+0x18`
from an `a1` stream, `+0x01=0xED` anim, **`+0x1E=0x0D56`** (base 3414), `+0x05=0x0B` (state 0x0B →
0x47140 walking), `+0x06=0x16` (record type 22), `+0x08=2`, `+0x07=1`, `+0x09=1`, `+0x38=1` (comp1);
count `d2`. Reached via computed branch (0 direct callers). This is an 8th creation route not in the
prior four-system taxonomy — a **direct group-spawn** of base-0x0D56 actors.

## 12. Retirement / reuse model

- **Individual off-screen despawn** (`0x427B2`): `clrb +0x00` when the actor has scrolled off
  (`+0x24` flag set, X outside range); only `+0x00` cleared → other fields **stale**. Reusable by
  allocators that scan `+0x00==0`, which is why every allocator must fully re-init (§4 caveat).
- **Scene/round reset** (`0x3A67A` / `0x3A804`): entire actor region zeroed via `0x3A2D0` fill.
- **Schedule refill** (§3): freeing a `+0x26` slot lets `0x4A086` install a new latent actor.
- Death → the state handlers drive a death anim then clear (state-machine-owned; effects/projectiles
  are separate short-lived records in blocks 0x748/0x5C8).

ALLOCATE → INITIALIZE (template) → +0x00=1 (ACTIVE, state 0 or 3 or 0x11) → 0x40BAA update →
off-screen/death clears +0x00 → slot REUSABLE.

## 13. Creator → initial state → `0x40BAA` graph

| creator | block | initial `+0x05` | 0x40BAA handler | graphics path |
|---|---|---|---|---|
| `0x4A086` field schedule | 0x2C8 | 0 | `0x41180` scanner (→ transforms) | family (`0x4544E`) |
| `0x4103E` child hunter | (A4) | 0 | `0x41180` hunter (→ transforms) | inherited family; handler rewrites +0x1E |
| `0x45342` paired demon | 0x508 | 3 | `0x47140` walking | record type 8/9 (`0x4543E`) |
| `0x423B2/F4` boss comps | 0x5C8/0x648 | 0x11 | `0x4684e` | record type 0x11 (`0x4543E`) |
| `0x45B18` boss body | 0x6xx/0x9xx | 3 | `0x47140` | record type by round (`0x4543E`) |
| `0x45CE0/0x45CFC` scripted | fixed | 3 | `0x47140` | record type 0x0C (`0x4543E`) |
| `0x4CD50` batch swarm | 0x748 | 0x0B | `0x47140` | direct `+0x1E=0x0D56` |
| `0x45330→0x4449E` boss trigger | — | (via record type) | — | `0x444E0[round]` → `0x4543E` |

## 14. Unresolved / next
- `0x4CD50` caller(s) and its coord-stream sources (`a0`/`a1`) — computed-reached; owner not yet
  pinned (which enemy/round batch-spawns base 0x0D56).
- `+0x08`/`+0x09`/`+0x28`/`+0x29` exact semantics across handlers (frame/HP/timers) — partially
  proven (anim frame, difficulty).
- Full record-type table `0x45592` enumeration (all types 8..N) and family tables `0x45502`/`0x45562`
  enumeration → CHECKPOINT H (behavioral identity).
