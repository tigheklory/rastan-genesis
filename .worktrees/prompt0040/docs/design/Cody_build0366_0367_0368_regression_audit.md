# Cody — Builds 0366 / 0367 / 0368 Regression Audit

Date: 2026-09-22  
Scope: analysis only; no production edit, ROM, or build-number change  
Compared builds: **0366 / 0367 / 0368**, not 0336 / 0337 / 0338

## A. Exact 0366/0367/0368 artifacts

All three canonical artifacts are 1,719,992 bytes. The consumed-build ledger records all three as
produced on 2026-09-22, and `build/rastan-direct/build_counter.txt` remains `368`.

| Build | Canonical artifact | SHA-256 |
|---:|---|---|
| 0366 | `dist/rastan-direct/rastan_direct_video_test_build_0366.bin` | `d975695da68e9fa2092b90052a94f1fb440c928015530b7e7ba2613500f662e2` |
| 0367 | `dist/rastan-direct/rastan_direct_video_test_build_0367.bin` | `10e17efe76571205c89755e8f2472530cf3b4ab8f11b2b2075d8de7b85efaf61` |
| 0368 | `dist/rastan-direct/rastan_direct_video_test_build_0368.bin` | `c031aa60867801db3733e06486feb2c87e5842a46c7bc9f441b80cc2a527beb4` |

Historical per-build manifests/maps were not preserved separately. Exact ROM bytes, numbered
artifacts, reports, the ledger, current Build-0368 address map, original disassembly/Ghidra exports,
and existing/runtime traces are the evidence authorities used here.

## B. User-observed behavioral matrix

| Behavior | 0366 | 0367 | 0368 |
|---|---|---|---|
| Water death | address-error crash | fixed | fixed |
| Starting sword | normal | FIRE | normal |
| FIRE expiry | not applicable | never clears | normal-start trace only |
| Enemy kill leaves blocker | no | not separately reported | reported for some enemies |
| Cave damage | reasonably easy | difficult/pixel-sensitive | still difficult |
| Cave supports player | yes | yes | yes before destruction |
| Post-destruction floating | no | not separately reported | reported |
| Rope | acceptable | no reported regression | no reported regression |

The user-observed matrix is authoritative. Automated routes below establish causal state changes;
they do not supersede the user's exact interactive cave/enemy observations.

## C. 0366 -> 0367 semantic changes

The intended production semantic change was confined to the direct-native HUD/status producer.
At Genesis `0x73880`, the malformed eight-byte indexed/full-extension encoding was replaced by the
intended four-byte `move.w d0,20(a0)`. This fixes the water-death odd word write to `0xFFBC3F`.

No source-level sword, enemy, cave, special-solid, or collision rule was intentionally changed.
Representative retained player/weapon ranges compare byte-identically as recorded in the Build
0368 report. The important indirect consequence is layout, not a new weapon rule.

## D. 0366 -> 0367 layout/reflow effects

The native helper shrank by four bytes. The Makefile-owned shift/reflow pipeline consequently
relinked the later native/helper/asset suffix and repaired its address operands. A raw ROM `cmp`
reports 497,767 differing byte positions, dominated by the shifted high-ROM suffix and its repaired
references; that count is not 497,767 independent semantic changes.

The stale absolute operand at original arcade `0x54B1E` continued to name cartridge address
`0x0010D2C8`. The four-byte layout movement changed which ROM data happened to reside there:

| Build | Four false 8-byte records decoded at ROM `0x10D2C8` |
|---:|---|
| 0366 | `{0F0F,0F0F,0300,0300}`, `{0F0C,0F0C,0000,0000}`, `{0F0F,0F0F,0001,0001}`, `{0E0F,0E0F,0202,0000}` |
| 0367 | `{0300,0300,0F0C,0F0C}`, `{0000,0000,0F0F,0F0F}`, `{0001,0001,0E0F,0E0F}`, `{0202,0000,0F0F,0D0D}` |

The 0367 content is the 0366 content displaced by four bytes. This is the direct layout-to-behavior
link.

## E. Why FIRE SWORD appears in 0367 but not 0366

`0x54B1E..0x54BF4` treats each record as `{active.w,type/flags.w,X.w,Y.w}` and dispatches only
`active == 1`. In 0366 none of the four accidental ROM records has active word `1`. In 0367 the
third has exactly `{active=1,type=1}`. The unchanged retained dispatcher therefore calls `0x54EF2`,
clears `A5+0x1326`, and writes FIRE selector `4` to `A5+0x12FA`.

Existing Genesis NTSC evidence records selector `0 -> 1` at frame 407 and `1 -> 4` at frame 409:
`states/traces/build0368_weapon_state_build0367_genesis_20260922/weapon_state_trace.csv`.

Thus 0367 acquires FIRE because the HUD shrink changed the bytes under an already-stale pointer.
0366 does not because its accidental bytes contain no active record.

## F. Why FIRE SWORD remains active

The FIRE timer/expiry routine at `0x54DD2` is intact. The same false 0367 ROM record is scanned on
every update, so `0x54EF2` repeatedly re-grants FIRE and resets its timer before expiry can win.
Startup acquisition and non-expiry are therefore two consequences of one stale-read defect, not
two separate FIRE-state defects.

The absolute stores to `0x0010D296` are a different contract. They retire the player-attached
impact auxiliary, not the melee selector or FIRE timer. They do not explain 0367's FIRE persistence.

## G. Why cave damage becomes harder in 0367

The only proven relevant 0367 gameplay-state divergence before a cave hit is the permanent switch
from normal selector `1` to FIRE selector `4`. That changes both the visual mapping program
(`0x5CD8A -> 0x5D068`) and the gameplay contact table (`0x5C9EA -> 0x5CC7E`). All 55 decoded contact
entries differ; representative edges move by one pixel in each direction. Therefore the 0367
change is **FIRE SWORD geometry/timing**, not a changed cave rectangle or a reason to enlarge it.
The exact subjective severity is not quantifiable from the static rectangles alone.

## H. 0367 -> 0368 semantic change

A byte comparison has five differing byte positions: two checksum/header bytes, two operand bytes,
and one embedded build-number byte. The sole gameplay semantic change is the operand at original
arcade `0x54B1E`, runtime Genesis `0x54BB8`:

```text
LEA 0x0010D2C8,A0  ->  LEA 0x00FF12C8,A0
```

There is no general 0368 reflow. This relocation is semantically correct: it reconnects the
retained dispatcher to the producer's Genesis WRAM table.

## I. A5+0x12C8 real table semantics

`0x449B4` clears this table once per collision-manager frame and may repopulate it while scanning
the 29 records of the `A5+0x02C8` actor pool. It contains **four records of eight bytes**:

| Offset | Field |
|---:|---|
| `+0` | active word (`1` means dispatch) |
| `+2` | collision-derived type/flags word; low word values 0..3 are relevant here |
| `+4` | snapshot of actor X (`actor+0x16`) |
| `+6` | snapshot of actor Y (`actor+0x1A`) |

For the secondary melee pass, the source actor must be active, have nonzero state, have zero
hit-flash byte `+0x3D`, not be slot 9, and pass the pool-position/type/mode filters before overlap
against the player weapon box at `A5+0x1254`. A qualifying hit records at most four entries and
calls the existing reaction/animation progression.

Type selection at `0x4495A` is `0` by default. Actor `+0x06 == 12` yields type 1 when `+0x25==0`,
type 2 when `+0x25==3`, otherwise type 3. `0x54A2C` dispatches type 0 to `0x5506C`, types 1..3 to
the three melee grants, and types 4..13 to other player item/status effects.

This table is a transient collision-hit event list. It is not an actor pool, allocator, item actor,
support object, or persistent identity. Its X/Y are snapshots; type-0 consumer `0x5506C` does not
use them. Lifetime is one collision-manager frame unless rewritten.

## J. 0368 enemy-death impassable-object identity

The premise that the 0368 relocation creates a new world actor is disproven.

- Actor slot: no new slot; the source remains the struck `A5+0x02C8` actor.
- Event record: ordinarily type 0 for actors whose `actor+0x06 != 12`.
- Creator: `0x449B4/0x4495A` writes the transient record; `0x5506C` consumes it.
- X/Y: copied from the struck actor into the event, then discarded by type-0 dispatch.
- New mode/base/state: none; no actor is allocated, transformed, or recycled by this path.
- Collision classification: the resulting auxiliary is not scanned as an actor and does not write
  `A5+0x0242`.

What 0368 does newly create is persistent **player-attached auxiliary state**, not a world object:

```text
A5+0x1296 active = 1
A5+0x1298 phase  = advances to 0x0014, then sticks
A5+0x129E subtype = 4 in the measured normal-player state
anchor = player BODY anchor A5+0x129A/A5+0x129C
visual owner = 0x547C0/0x54810 -> native FRONT_EFFECT
```

A controlled, existing-harness-derived GENESIS NTSC A/B produced real type-0 hit records in both
0366 and 0368. In 0366 `A5+0x1296` stayed `0x00FF`. In 0368 the first event activated it, phase
advanced through `0x0014`, and active remained `1`. During those enemy-hit samples, `A5+0x0242`
remained inactive and `A5+0x1312/0x1320` remained `0x00FF`.

The lifecycle root cause is exact. The live general updater mapped at Genesis `0x51C80` contains
two still-unrebased terminal stores, original arcade `0x51A8C` and `0x51AA8`:

```asm
move.w #$00FF,$0010D296.l
```

They write cartridge ROM and cannot clear `A5+0x1296`. The already-documented replacements at
original `0x52B0E/0x52B2A` repair only a duplicate updater, not this live primary copy.

Consequently, the reported blocker cannot truthfully be assigned an actor slot, base, mode, or
special-solid classification: none exists on the newly live path. The proven 0368 regression is a
non-retiring player auxiliary. Whether the user's perceived former-location obstruction is a
movement consequence of that persistent player state or a second scenario-specific collision path
requires a trace of that exact enemy; the evidence rejects “new dropped item,” “recycled actor,”
and “new special-solid record” as explanations.

## K. 0368 floating-after-cave-destruction cause

For the retained special-solid path, the cave actor is the existing `A5+0x02C8` actor, target `H`,
base `0x0179`, mode 1, live state `0x1E`. Destruction state `0x0F` does not pass `0x444F8`.
`0x449B4` clears `A5+0x0242` at the start of every scan; when no actor qualifies, `0x54BF8`
clears `A5+0x13B2`, `A5+0x13B4`, `A5+0x1312`, and `A5+0x1320` to `0x00FF`. The record holds only
state/coordinates/extents, not an actor pointer that can survive slot reuse.

Therefore a cave actor changing to `0x0F` cannot, through this unchanged path, leave stale support.
The first new 0368 semantic after a successful cave hit is instead the same type-0 event activation
and failure to retire `A5+0x1296`. That is the only artifact-proven 0366/0368 divergence after the
hit. It does **not**, however, write player Y, vertical velocity, ground flags, cached floor Y,
`A5+0x0242`, or `A5+0x1312..0x1320`; static evidence therefore does not prove the complete physical
floating mechanism. A targeted cave-destruction runtime capture is required before naming stale
support or modifying collision. The audit result is: persistent auxiliary is the first divergence;
stale special-solid registration is disproven; final floating mechanism remains scenario-specific.

## L. Why cave hit difficulty remains in 0368

0368 restores selector 1, so permanent FIRE geometry cannot explain the continuing symptom. Before
the first cave overlap, 0366 and 0368 execute the same normal-sword contact and cave hurtbox code.
After the first successful hit, 0368 alone dispatches the real type-0 event and leaves the subtype-4
auxiliary permanently active because of `0x51A8C/0x51AA8`.

That is the first proven difference, but the auxiliary does not select the weapon contact table or
write `A5+0x1254`. Accordingly the remaining hit difficulty is **unresolved as a direct geometry
contract**. It must not be “fixed” by enlarging a hitbox. The next evidence pass must trace the exact
cave attempt across the first hit and correlate weapon-box coordinates, actor state, event state,
and player action state.

## M. Special-solid state/class qualification audit

The original classifier retained in all three builds is not state-only. Its full proven cave path is:

1. actor `+0x00` active;
2. actor `+0x05` state nonzero;
3. actor `+0x3D` hit-flash zero;
4. actor `+0x03` mode nonzero, entering `0x44548`;
5. target marker `actor+0x0D` transformed through the table at `0x44582`, with the `actor+0x38`
   variant/family path participating in selector acceptance;
6. target `H` selects rectangle index `0x52` (`{-20,+20,-16,+16}`);
7. `0x444F8` accepts state `{0x15,0x17,0x1B,0x1C,0x1E}`;
8. only then is the single `A5+0x0242` record written.

No Genesis replacement dropped this predicate: the original producer remains live. A raw state
number collision in an unrelated item/effect cannot create solidity without the preceding actor,
mode, target-marker, and rectangle-selection predicates. The 0368 event dispatcher allocates no
actor, so alternatives A/B/C from the task are rejected for this path. The player support record is
regenerated rather than identity-cached; persistent auxiliary state is separate.

## N. Relevant stale arcade-WRAM address contracts

| Arcade absolute | Intended object | 0366 | 0367 | 0368 | Status / consequence |
|---|---|---|---|---|---|
| `0x0010C242` | A5+`0x0242` special-solid record | reads `0xFF0242` | same | same | Correctly relocated in 0366; user-confirmed live cave support/release baseline. |
| `0x0010D2C8` | A5+`0x12C8` four-record secondary hit-event list | stale ROM, no active false record | stale ROM, false `{1,1}` grants FIRE | reads `0xFF12C8` | Correct 0368 relocation exposes real events. Reverting it would re-hide semantics and is not recommended. |
| `0x0010D296` at `0x52B0E/0x52B2A` | A5+`0x1296` auxiliary active retirement | rebased | rebased | rebased | Correct, but these are the duplicate updater's terminal stores. |
| `0x0010D296` at `0x51A8C/0x51AA8` (Genesis `0x51C98/0x51CB4`) | same active retirement in live primary updater | latent/dormant | latent; FIRE events do not invoke type 0 | exposed by real type-0 events | **Still stale.** Phase reaches terminal 12/20, store hits ROM, auxiliary never retires. |

## O. Root-cause timeline

```text
0366
  cave special-solid read correctly rebased; user-confirmed best gameplay baseline
  malformed native HUD store still crashes on water death
  A5+12C8 dispatcher still reads ROM, but accidental records are inactive
  live A5+1296 retirement stores are stale but dormant because type-0 events are not consumed

0367
  HUD store fixed; water death no longer crashes
  four-byte helper shrink changes ROM content under stale 0x10D2C8 pointer
  accidental {active=1,type=1} repeatedly grants FIRE and resets its timer
  FIRE contact table changes cave hit geometry/timing

0368
  0x10D2C8 -> 0xFF12C8 correctly restores real collision-hit event semantics
  normal starting sword returns
  real type-0 hits now activate A5+1296
  previously missed live retirement stores at 0x51A8C/0x51AA8 write ROM, so phase sticks at 0x14
  persistent player auxiliary is the first proven new state after enemy/cave hits
  no new actor or special-solid record is created; exact spatial blocker/floating mechanism still
  needs the user's scenario captured before any collision change
```

## P. Recommended recovery strategy

Recommendation only; nothing is implemented here.

1. Preserve the 0367 HUD correction, the 0366 special-solid rebase, and the 0368 `A5+0x12C8`
   relocation. None should be reverted to hide the next defect.
2. In the next authorized implementation, treat all four `0x10D296` terminal stores as one
   retained auxiliary-lifecycle contract. Repair the live primary pair at `0x51A8C/0x51AA8`
   declaratively and retain the already repaired duplicate pair.
3. Before claiming that fix closes ghost blocking or floating, capture the exact user enemy and cave
   destruction sequences in 0366 and the candidate. Record actor slots, `A5+0x12C8`, auxiliary
   phase, `A5+0x0242`, `A5+0x1312..0x1320`, player Y/vertical state, and weapon box coordinates.
4. If a world-space obstruction remains after correct auxiliary retirement, investigate it as a
   separate defect. Do not add actor-specific solidity, enlarge hitboxes, or revert the real table.

## Audit boundary

Production source modified: **NO**. ROM produced: **NO**. Counter changed: **NO (still 368)**.
The only repository deliverables are this report and the concise `AGENTS_LOG.md` audit entry.
