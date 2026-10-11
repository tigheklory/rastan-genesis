# Native Sprite Completion Campaign

**Agent:** Cody  
**Input baseline:** Build 0405  
**Current state:** Build 0413 lean-save tail optimization; human validation required

## Semantic cut

The retained actor state chooses `actor+0x38` compositor, `actor+0x01`
selector, orientation, and (for specialized modes) `actor+0x0B` subframe.
Python resolves the original descriptor syntax and emits Genesis-native frame
records. Genesis indexes those records and emits final native queue/SAT pieces;
it does not interpret PC090OJ records on a native hit.

The five selector-table boundaries are statically encoded by the first signed
descriptor offset: 253, 246, 131, 167, and 167 selector entries. The generator
uses signed `MOVE.W`/`ADDA.W` offsets. Bytes beyond those boundaries are not
selector entries. Three in-bound entries (`3/0x36`, `3/0x37`, `4/0x91`) select
a specialized nibble but contain long pointers outside arcade ROM/address
space; they are mechanically unreachable without crashing the original and
are classified `PROVEN_UNREACHABLE`.

## Player closure

- 75 body selectors × 8 variants × 2 orientations = **1,200 native keys**.
- Variants cover none, sword, axe, hammer, and all four fire-sword phases.
- Reachable player `UNRESOLVED`: **0**.
- The generated record retains weapon-anchor flags and accepted BODY lane and
  orientation behavior.

The fixed FRONT semantic producer now emits its four invariant pieces directly.
The primary BODY/weapon producer uses the 1,200-key generated table, and the
secondary/legs producer uses a separate 52-selector × four finite phase × two
orientation index (416 native keys). The three-record auxiliary producer is
also direct. None calls the retired `native_player_piece` tuple adapter.

## General compositor closure

The original dispatcher tests the specialized nibble only on the first
descriptor byte. Later control bytes are ordinary pieces regardless of their
high nibble. A visible stream may terminate with `0xFF`, or with the caller's
`D2` record ceiling. The generated Level-A payload therefore contains a
20-piece maximum prefix; runtime applies the original caller ceiling without
reading an arcade descriptor.

Current independently verified records:

- 38 exact Level-B semantic records;
- 1,898 universal general selector/orientation records;
- 24 specialized selector/orientation dispatch records;
- 682 bounded specialized-subframe index records;
- 638 unresolved dense-index slots, all statically `PROVEN_UNREACHABLE` (632
  out-of-table orientations plus six orientations for the three invalid-pointer
  entries);
- reachable generic/specialized `UNRESOLVED`: **0**.

## Nine specialized handler contracts

FU1 arcade write history proves that specialized handlers retain code and
attribute written one frame earlier by the general expander: attribute writer
`0x03C986`, code writer `0x03CA24`. Every structurally valid specialized
selector is paired with its immediately preceding general selector. Python
expands that predecessor and carries its code delta/attribute into the native
specialized frame. `0x05B512` is exactly `RTS`, so it contributes no hidden
coordinate transform.

All pieces are 16×16. Geometry is actor-relative; specialized handlers do not
run the general X-mirror branch, while retained piece flip state comes from the
orientation-specific predecessor frame.

| Mode | Arcade handler | Generated contract | Classification |
|---|---:|---|---|
| `10` | `0x03C830` | 4-byte subframe; family 0 creates two 5-record halves at X -8/-24, family 2 creates fixed+paired layout; zero parks; family-0 first records preserve the exact `A5+0x0118==3` / `A5+0x013E` code override | Level A |
| `20` | `0x03C7A4` | four fixed upper pieces plus six signed-Y pieces at X -8; `FF` parks | Level A (subframe) |
| `30` | `0x03C6DC` | nine signed-X bytes; first six use Y -48..32, last three Y -48; zero parks | Level A (subframe) |
| `50` | `0x03C4D2` | two four-piece columns (X 0/-16), signed Y plus actor+0x18; subframe `0x20` parks all | Level A (subframe) |
| `60` | `0x03C4D2` | two five-piece columns (X 0/-16), signed Y plus actor+0x18; subframe `0x20` parks all | Level A (subframe) |
| `90` | `0x03C75C` | one fixed (-8,-16) piece plus seven signed-Y pieces; `FF` parks | Level A (subframe) |
| `A0` | `0x03C550` | one signed-X byte places four pieces at +0/+16/+32/+48 | Level A (subframe) |
| `B0` | `0x03C636` | four signed-Y bytes and one of two precompiled layouts selected by `A5+0x0118==2 || 0x62<=A5+0x013E<0x64`; `FF` parks | Level A (subframe + one predicate) |
| `C0` | `0x03C586` | three signed-X bytes duplicated at Y 0/-16 with fixed pieces; selector 6 uses the alternate proven ordering; `FF` parks | Level A (subframe) |

Only genuinely dynamic inputs remain: actor X/Y/base/effective attribute state,
`actor+0x0B`, the `B0` predicate, and the `10` conditional code override.
Invariant descriptor parsing, geometry, order, and predecessor identities are
offline.

## Visual/contact convergence

`genesistan_native_contact_coords_51ab6` now attempts the same generated
general/special frame indexes as visual expansion and writes generated X/Y to
`A5+0x1134`. It preserves the legacy reconstruction only as a validation-time
miss path. This removes the former simplified `frame*3` specialized geometry
disagreement on every native hit.

## Mechanical status

- Generator: PASS.
- Independent player/general/special re-expansion: PASS.
- Player native keys: 1,200/1,200.
- Reachable generated unresolved: 0 statically.
- Machine-readable live-consumer inventory: 49 `NATIVE_COMPLETE`, 0
  `NATIVE_PARTIAL`.
- Assembler: PASS for modified PC090OJ objects.
- Lifetime validation counters added: player fallback, generic fallback,
  specialized hits, and player-piece adapter entries.

Generated campaign artifacts are `build/pc090oj_frame_table.bin`,
`build/pc090oj_frame_index.bin`, `build/pc090oj_generic_frame_index.bin`,
`build/pc090oj_universal_frame_index.bin`,
`build/pc090oj_special_frame_index.bin`,
`build/pc090oj_generic_base_lut.bin`,
`build/pc090oj_generic_usage_table.bin`,
`build/pc090oj_frame_residency.bin`, and
`build/pc090oj_frame_table.coverage.json`. The live-consumer inventory is
`analysis/actor_decompilation/native_sprite_completion_manifest.tsv`.

Build 0406 is the first numbered campaign ROM. It is a deliberate
human-validation boundary, not a zero-fallback completion claim. Its canonical
ROM gate and gameplay-entry gate pass with address/bus/illegal/crash-handler
counts `0/0/0/0`; the normal 1,798-frame MAME trace reports no unmapped memory
addresses. The existing phase-one seven-epoch automated route remains a labeled
`FAIL` warning and no PC080SN behavior was changed by this campaign.

The exported lifetime counters in Build 0406 are:

| Counter | WRAM address |
|---|---:|
| player generated-table fallback | `0xFFBED8` |
| generic generated-table fallback | `0xFFBEDA` |
| specialized generated-frame hits | `0xFFBEDC` |
| retained player-piece adapter entries | `0xFFBEDE` |

The mandatory automated trace is a boot/gameplay-entry sanity check, not the
full-game counter suite. Therefore no zero-fallback runtime result is claimed
from it.

## Build 0407 closeout

The last live adapter caller was mechanically captured at return address
`0x05483E`, the call at original arcade `0x054742` inside the distinct
`0x0546A8` `A5+0x1246` secondary/legs compositor. All 36 sampled entries came
from that one site, four calls per active update. It was not FRONT or the
three-record auxiliary path. Python now resolves its `0x05C466` table, finite
`A5+0x1308` phases, and both orientations into 416 native records. H24 selector
51 was corrected to the arcade's sticky-zero termination semantics rather than
advancing past the zero into `0x140C`.

The fixed FRONT and three-record auxiliary producers were converted to direct
native pieces. Runtime proof then reported player fallback `0`, generic
fallback `0`, and player adapter `0`. The accepted Build-0406 specialized route
recorded 27,204 generated specialized hits; a Build-0407 candidate route
recorded 28,236. The final completion manifest has 49 `NATIVE_COMPLETE`, zero
`NATIVE_PARTIAL`, and zero reachable `UNRESOLVED` consumers.

The obsolete `native_player_piece` implementation and its eight dead remap
references are removed. The dead native general descriptor/piece-stream parser
is also physically removed. Whole-producer opcode cuts make the copied original
player compositors unreachable, while their ROM data remains valid offline
generator evidence. Genesis runtime arcade descriptor parsing and piece-stream
parsing are both zero.

The first pure-native optimization selects the semantic lane once per generated
frame and appends each prevalidated four-word tuple without eleven-register
save/restore or repeated lane dispatch. The build gate verifies all six lane
contexts, visibility filters, bounds/count behavior, D1/D2/D3/D4 tuple order,
and continued use of the shared residency/worklist/SAT finalizer. Full timing
and artifact results are in
`docs/design/Cody_build0407_native_sprite_performance_optimization.md`.

Build 0407 is mechanically complete but still requires Tighe's visual/gameplay
acceptance. Burst first-frame palette and the historical Segment-1 player
glitch remain outside this task as directed.

## Build 0408 variable-count regression correction

Tighe rejected Build 0407 after observing whole missing pieces on Lizardman and
the Four-Armed enemy; Build 0406 is the visual golden reference. Generated
records, variable-count iteration, fast enqueue, queue counts, finalizer input,
and representative SAT output all reconcile. The first exclusive divergence
was the retained caller register contract: the Level-B and universal wrappers
returned with `A3/A6` clobbered by the once-per-frame queue context. Build 0406
preserved both through its old per-piece helper.

Build 0408 preserves `A3/A6` once at each generic frame boundary while retaining
the single variable-count emitter, fast enqueue, and once-per-frame lane
selection. The full rack-advance closeout completes 18 subrounds with zero
player/generic fallback, zero adapter entries, and no crash. The corrected
timing route retains the 0407 performance gain. Full proof and hashes are in
`docs/design/Cody_build0408_variable_count_native_sprite_fix.md`. Tighe visual,
gameplay, and performance acceptance remains required.

## Build 0409 displayed-enemy queue-bound correction

Tighe's real-gameplay rejection of Build 0408 exposed a second fast-context
defect. At the first captured Lizardman disappearance, the generated reader
visits all eight records, but the back-enemy queue begins at count 13 and stops
at count 15. Runtime proof showed `A2-A3=0x75`: the numeric-displacement `LEA`
used to construct the nominal 99-record end had been encoded with a later-CPU
full/index extension that the Genesis 68000 interpreted as a brief D0-indexed
address. Only two Lizardman records reached the published VDP SAT; the separate
front-effect lane continued to show the impact graphic.

Build 0409 gives all six queues exact linker end labels adjacent to their
allocations and makes the verifier enforce those labels and spans. The same
semantic frame reaches a back-enemy count of 17 and publishes both complete
eight-piece Lizardman bodies. The framebuffer shows body and impact together;
the scanline load remains below VDP limits. The A3/A6 fix, variable-count
emitter, fast enqueue, once-per-frame context, precomputed tables, zero-fallback
architecture, and performance gain are retained. Four-Armed shares the same
corrected back-enemy context, but final real-gameplay visual acceptance remains
Tighe's test. Full proof is in
`docs/design/Cody_build0409_displayed_enemy_sprite_loss_fix.md`.

## Build 0410 shared-finalizer optimization

Build 0409's full shared finalizer measured 53,808.48 cycles per completed
worker update, 70.60% of the graphics subtotal. Build 0410 adds an explicit
`x1000 | source_code` transport marker to the existing generated piece
record for player, secondary, and exact Level-B identities already proven by
Python. The common finalizer consumes those identities without repeating blank
validation or dynamic variant selection, and retains the opaque-bounds pointer
instead of reconstructing the source. Unmarked universal records retain the
complete dynamic Level-A path.

The finalizer falls to 46,502.94 cycles/update (-13.58%) and 1,334.21
cycles/piece (-18.08%). The whole-worker route remains above budget at
146,980.39 worker and 152,267.67 IRQ cycles/update, so no second optimization
was made. A bounded regression frame reaches back-enemy count 43 and publishes
both visible Lizardman bodies completely with their separate impact effect.
Four-Armed real-gameplay visual acceptance remains Tighe's test. Full evidence,
gates, metrics, and Build 0410 hashes are in
`docs/design/Cody_build0410_native_finalizer_performance_optimization.md`.

## Build 0411 one-frame-average worker milestone

Build 0411 first optimizes the measured SAT construction path: the resident
slot stays in a register, V/H bits are formed together, invariant palette-line
fragments come from a four-word table, and redundant masks/stack traffic are
removed. SAT cost falls from 9,808.69 to 7,220.27 cycles/update without moving
screen coordinates, palette selection, residency, links, or ordering offline.

Because the worker was still above budget after that change, the next measured
target replaced the repeated 49-call residency first-free scan with an exact
ascending byte/bit scan. It returns the same lowest free slot and retains the
existing reservation, eviction, reverse-index, DMA-worklist, and staged-frame
semantics. The scan falls from 4,317.19 to 522.23 cycles/update on the final
route.

The established 1,200-frame GENESIS NTSC route now averages 126,786.39 worker
cycles, 1,222.61 below the 128,009-cycle frame budget, with 0.9033 completed
workers/rendered frame. IRQ average remains above budget at 131,589.13.
Displayed-SAT proof retains complete 8+10-piece Lizardman bodies with the
independent impact effect and `back_enemy=38`; Four-Armed remains a human
visual test. Full Build 0411 evidence, metrics, gates, and hashes are in
`docs/design/Cody_build0411_native_worker_one_frame_optimization.md`.

## Build 0412 complete-IRQ-average milestone

Build 0412 promotes the finite, statically nonblank P1 HUD glyph set to the
existing direct-identity contract, selects its semantic lane once, and uses the
verified fast queue emitter. Leading-zero visibility is resolved at the HUD
producer instead of by queuing off-screen cells, and only fixed visible HUD
coordinates carry a bounds-proven marker. Dynamic Level-A identity and all
actor/player/effect clipping, residency, DMA, and SAT work remain runtime-owned.

The finalizer falls from 38,572.31 to 32,408.16 cycles per completed update. On
the 1,200-frame route, worker average is 120,467.68 and complete IRQ average is
125,442.49, crossing below the 128,009-cycle budget with a 2,566.51-cycle
margin. The route completes the same 1,084 workers as Build 0411 under a heavier
average sprite load; IRQ-over-budget improves from 34.1% to 29.0%, while
workers/rendered remains 0.9033.

Canonical/gameplay-entry/VDP-ownership and generated-table/dispatch/queue gates
pass. The `_c` closeout reports zero fallback/adapter/crash but its MODE-driven
automation did not complete all 18 subrounds on 0412, so full-game coverage is
not claimed. Full evidence and hashes are in
`docs/design/Cody_build0412_hardware_grounded_native_performance.md`.

## Build 0413 lean-save tail optimization

Tail partitioning proved the largest Build-0412 spikes come from the retained
`0x51210 -> 0x055650 -> 0x0556CE` scroll chain and its PC080SN-derived
strip/map tail. That subsystem remained out of scope. Build 0413 instead
removes redundant nested register saves from the private generated-actor probe
chain: the two stage dispatchers retain their full `D0-D7/A0-A6` external
contract, while the common wrapper preserves only loop-live `D5/A1` and a
hardened verifier locks probe/helper `A4/A5` non-clobber, single-caller, and
stack-balance invariants.

The fixed route completes 1,092 workers (0.9100/rendered frame) instead of
1,084 (0.9033), with 108 rather than 116 frames lacking a worker. At equal
emitted-piece load, median worker cost improves 3.3%–11.0% across the 20–49
piece bands. The raw 1,200-frame aggregate is not uniformly lower because the
faster ROM reaches a denser later state; worst worker cost nevertheless falls
from 319,882 to 309,574 and graphics p95 from 93,636 to 90,372.

The MODE closeout now paces input using actual completed workers and uses a
state-progress watchdog. Build 0413 `_c` restores all 18-subround coverage with
zero player/generic fallback, zero adapter, and zero crash. Full metrics,
verifier proof, tooling diagnosis, and hashes are in
`docs/design/Cody_build0413_native_tail_performance_optimization.md`.
