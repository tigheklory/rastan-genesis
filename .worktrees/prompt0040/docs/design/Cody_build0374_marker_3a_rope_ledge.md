# Cody — Build 0374 marker `0x3A` rope-ledge hypothesis

**Date:** 2026-09-24  
**Agent/task:** Cody — decode marker `0x3A` at the human-marked rope-side ledge  
**Baseline:** Build 0373  
**Build produced:** **None**  
**Production changes:** **None**  
**Disposition:** hypothesis falsified; stopped before implementation

## Result

Marker `0x3A` does **not** materialize the missing rope-side ledge. It is a map marker consumed by
the existing scheduled-actor state machine. It activates or retargets an already allocated field
actor; it does not allocate a distinct ledge object, select a ledge actor family, write Plane-A
terrain, or register the special-solid contract at arcade `0x041BEE`.

At the human arcade marker, `A5+0x013E = 3`. The field schedule for that progression contains
family 0/base `0x004B` (Lizardman) and family 3/base `0x02E8`. Marker `0x3A` does not encode which
of those scheduled records encounters it. The existing human trace did not dump actor records, so
it cannot supply a defensible record address/slot or live actor X/Y at frame 1845. Inventing those
values from the screenshot would violate the evidence requirement.

The original static route proves enough to falsify the ledge hypothesis, triggering the task's
explicit stop rule. No Build 0374 ROM was produced.

## Tooling and evidence discipline

Existing project tools reused:

- canonical Ghidra exports in `analysis/ghidra/rastan_arcade/exports/`;
- reconstructed original arcade ROM `build/regions/maincpu.bin`;
- `tools/analysis/decode_field_schedule.py` and its existing actor-system reports;
- generated `build/rastan-direct/address_map.json`;
- preserved Build-0373 ROM;
- existing ORIGINAL ARCADE and GENESIS NTSC human `USER_MARK` traces.

New tooling created: **None**.

Why new tooling was necessary: **Not applicable**. No new trace, route, or instrumentation was
created.

Runtime platforms represented by the reused evidence:

- ORIGINAL ARCADE MAME human marker at frame 1845;
- GENESIS NTSC MAME Build 0373 human marker at frame 1948.

## Exact marker `0x3A` semantics

The marker is the high byte of the collision-map word. `0x3A00` therefore means marker `0x3A`
with low-byte terrain collision/property `0x00`.

### Floor-follower path (`actor+0x03 == 0`)

At arcade `0x041180`, the scheduled actor scans the live collision grid through `0x053A2E`.
The candidate high byte is read at `0x041294..0x041296`.

For `D0.b = 0x3A`:

1. it is not excluded marker `0x34`;
2. it is at least `0x31`;
3. for a floor follower it is below `0x3D`, so `0x0412B0..0x0412B4` accepts it;
4. the actor state is seeded from its existing scheduled class (`actor+0x05 = actor+0x04 + 1`);
5. `0x041336` special-cases `0x3A` by leaving `D3=0`, hence
   `actor+0x16 = A5+0x0216` with no adjacent-cell ±8 adjustment;
6. `actor+0x1A = A5+0x0218`;
7. `0x040A06` and `0x040BAA` continue the already allocated scheduled actor's state machine.

`0x3A` is absent from the `0x040A86` floor transition table. It therefore does not select a new
actor family or a special ledge state. Its explicit meaning in `0x041336` is the zero-X-offset
marker case.

### Existing-target path (`actor+0x03 != 0`)

If an existing actor's requested marker at `actor+0x0D` matches `0x3A`, `0x041064` returns the
matched collision pointer and `0x041192` branches to `0x041362`. The comparator dispatch sends
values below `0x45` to `0x041A48`. That route:

- requires `D0.b == actor+0x0D`;
- sets `actor+0x05 = 0x1D`;
- computes position through `0x041ADA`;
- sets `actor+0x01 = 0x75`;
- updates the already allocated actor's state-specific byte through `0x045418`;
- resumes the normal `0x040BAA` state machine.

It still does not allocate a new record, change `actor+0x3E`, choose a new base at `actor+0x1E`,
write terrain graphics, or call `0x041BEE`.

## Actor family and base at progression 3

The schedule installer at `0x04A086` owns family/base selection before marker consumption:

- schedule byte 1 -> `actor+0x3E` family;
- `0x04544E` resolves that family through the family table;
- marker `0x3A` later positions/advances the existing record.

For progression 3, decoded schedule block 1 contains five records:

| Slot | Class (`+0x04`) | Family (`+0x3E`) | Base (`+0x1E`) | Initial marker-path state |
|---:|---:|---:|---:|---:|
| 0 | `0x01` | `0x03` | `0x02E8` | `0x02` |
| 1 | `0x01` | `0x00` | `0x004B` | `0x02` |
| 2 | `0x01` | `0x03` | `0x02E8` | `0x02` |
| 3 | `0x00` | `0x00` | `0x004B` | `0x01` |
| 4 | `0x01` | `0x00` | `0x004B` | `0x02` |

Family 0/base `0x004B` is the statically established Lizardman family. Family 3/base `0x02E8`
is another scheduled hostile family. No ledge/platform family is selected by `0x3A`.

The exact actor record that consumed the four repeated `0x3A` cells earlier in the playthrough
cannot be recovered from the bounded human TSV: it logged player/camera/map state but no actor
slots or instruction-level consumption event. This limitation does not weaken the semantic
falsification: every possible progression-3 consumer is an already scheduled hostile record.

## Human marker evidence

At ORIGINAL ARCADE `USER_MARK` frame 1845:

- progression is `A5+0x013E = 0x0003`;
- the exact same-world block is rows 36–39, columns 48–51;
- its row-38 collision words are four copies of `0x3A00`;
- the low collision byte is zero;
- the visual source half independently contains the block's sixteen tile words.

The marker remains in collision-map data after consumption; its presence at the marker frame is
not an actor-liveness flag. The human trace contains no actor dump, so this report does not claim
a particular live slot, X/Y, compositor, or retirement event from that TSV.

## No special-solid registration

The special-solid registration helper at arcade `0x041BEE` has exactly one static caller,
`0x041BE6`. That call belongs to the `0x041BCA` materialization route reached by marker classes
`0x4F..0x51` in the `0x041362` classifier.

Marker `0x3A` sorts below `0x45` and routes to `0x041A48`, not `0x041BCA`. Neither its
floor-follower path nor its existing-target path calls `0x041BEE` or writes the special-solid
registration table at `A5+0x1280/A5+0x1282`.

Therefore `0x3A` cannot explain why the arcade player stands on the ledge. The standability must
come from a different semantic contract, outside this explicitly bounded hypothesis.

## Genesis Build-0373 comparison

The human Genesis trace proves that the same block retains `0x3A00` in the live collision grid.
The current generated address map proves these relevant routes remain copied arcade code:

| Arcade PC | Build-0373 runtime Genesis PC | Status |
|---:|---:|---|
| `0x041064` | `0x041264` | copied marker finder |
| `0x041180` | `0x041380` | copied spawn/activation state machine |
| `0x041336` | `0x041536` | copied `0x3A` position rule |
| `0x041362` | `0x041562` | copied classifier |
| `0x040A06` | `0x040C06` | copied state transition helper |
| `0x040BAA` | `0x040DAA` | copied behavior dispatcher |
| `0x053A2E` | `0x053B4A` | copied collision lookup with WRAM-base relocation |

The only production replacements inside the marker scan loop are the already accepted general
collision-buffer boundary relocations:

- arcade `0x0412CC`: upper bound `0x0010FE00 -> 0x00FF3E00`;
- arcade `0x0412E8`: lower bound `0x0010DE00 -> 0x00FF1E00`.

Those changes preserve the arcade scan over relocated Genesis WRAM. There is no `0x3A` dispatch
replacement, marker-specific bypass, early retirement, or alternate object route in Build 0373.

Thus Genesis category A applies to the actual semantic contract: it sees `0x3A` and retains the
same generic scheduled-hostile materialization path. There is no arcade ledge object for Genesis
to be missing, wrong, or retiring.

## Why the hypothesis cannot explain both symptoms

- **Missing graphics:** `0x3A` does not write Plane A or select the sixteen visual tile words.
  The block's graphics are owned by the independent metatile visual half.
- **Missing support:** `0x3A` has low collision byte `0x00` and never reaches special-solid
  registration. Its consumer is the hostile actor scheduler.

The same marker therefore cannot be the semantic owner of either the protruding terrain art or
its player-support contract.

## Stop disposition

- Hypothesis: **FALSIFIED**
- Concrete Genesis divergence in marker `0x3A` materialization: **NONE PROVEN**
- Manual graphics injection: **NO**
- Manual collision injection: **NO**
- Production changes: **NONE**
- Build 0374: **NOT BUILT**
- SHA-256: **Not applicable**
- BlastEm validation: **Not applicable; no ROM produced**
- STOP: **YES**, per the directive's marker-hypothesis stop rule

