# Build 0426 — Genesis-Native Sprite Path Optimization

Date: 2026-10-14  
Baseline: accepted Build 0425  
Scope: shared proven-native normal-gameplay frame-to-SAT producer only

## Result

Build 0426 replaces the 10-byte generic piece payload used by the proven
Level-B gameplay path with a compact, prevalidated 6-byte Genesis-native piece:

```text
{ s16 dx, s16 dy, u16 finalized_pattern_key }
```

The corresponding frame index is now:

```text
{ u32 piece_offset, u8 count, u8 native_status, u16 frame_attribute }
```

This is a shared-path change. Lizardman, Large Bat, Small Bat, cave, and burst
frames use the same mechanism; no actor-specific fast path was added. The
semantic cut remains arcade actor/frame selection followed by generated native
frame data, Genesis residency, native SAT construction, and VBlank publication.
The unresolved fallback and attract-mode compatibility code are unchanged.

## Before and after

Build 0425:

```text
actor semantic state
  -> O(1) native usage/frame selection
  -> 10-byte generated piece records
  -> for every piece:
       load/test static flags
       conditionally apply actor-Y adjustment
       load the same frame attribute
       retest the same actor attribute override
       call native_sprite_emit_fast
         validate an already-finalized identity
         reconstruct the queue append cursor from the count
         clip/capacity check and append
  -> shared residency/finalizer -> SAT
```

Build 0426:

```text
actor semantic state
  -> O(1) native usage/frame selection
  -> load/resolve the invariant frame attribute once
  -> select queue context and establish append cursor once
  -> 6-byte compact native pieces:
       add actor X/Y
       load finalized key
       hidden-Y and capacity checks
       append {attribute,Y,key,X}; advance count/cursor
  -> unchanged shared residency/finalizer -> SAT
```

The source implementation is at
`apps/rastan-direct/src/pc090oj_hooks.s:1033-1090`. The assembled loop is a
straight 6-byte walk: three piece loads, actor coordinate additions, the
existing hidden-Y and queue-end checks, four queue stores, count increment,
pointer advance, and loop branch. It no longer calls the generic per-piece
emitter.

## Work removed or hoisted

For every piece, the common direct path removes:

- static Y-adjust flag test/branch (the compiler proves it is absent);
- repeated attribute load and actor-override test;
- already-finalized identity validation;
- queue count-to-cursor reconstruction;
- per-piece `BSR`/`RTS` through `native_sprite_emit_fast`.

Depending on direct-key versus variant-key identity, 13–18 executed 68000
instructions leave the inner loop. Attribute selection/override and queue
cursor construction now occur once per frame.

The generator at
`tools/translation/precompute_pc090oj_frame_table.py:644-695` proves before
emission that each covered frame has one invariant attribute, fixed 16x16
pieces, no actor-Y-adjust flag, a valid direct or finalized-variant identity,
and a bounded residency worklist. It then writes only `dx`, `dy`, and finalized
key per piece. The compact payload contains 1,422 bytes (237 pieces); the 38
frame-index records occupy 304 bytes.

The following work remains dynamic because it is genuine Genesis/game state:

- actor base X/Y and the retained actor attribute override;
- hidden-Y clipping and queue capacity;
- queue/SAT order and count;
- current pattern residency, first-use upload reservation, replacement state,
  palette/priority realization, SAT links, and DMA publication.

Sonic 1 informed only the presentation shape: select a mapping/frame once and
make the bounded piece-to-SAT loop simple. Rastan's actor selection, geometry,
attributes, ordering, clipping, identity, residency, and publication contracts
remain authoritative.

## Semantic verification

The generator and independent verifiers compare every compact record against
the authoritative decoded arcade/native result. They prove all 38 common
generic records, both orientations, exact piece counts/order/coordinates,
frame attribute, finalized identity, fixed size, absence of Y adjustment,
dispatch routing, queue tuple order, clipping, and capacity behavior.

Results:

- player native records: 1,200; unresolved: 0;
- player secondary native records: 416;
- generic direct records: 38; all compact records verified;
- universal general native records: 1,898;
- universal specialized native records: 24;
- direct-dispatch usages: 5; fallback calls in the focused run: 0;
- canonical, gameplay-entry, boot, native-sprite, DMA-boundary, background,
  collision/visual, and five-ROM-family checks passed;
- the existing seven-epoch phase-1 gate still reports only epoch 0 proven and
  remains the same standing warning/failure; it did not block numbered output.

Automated semantic equivalence: **PASS**. Real Genesis acceptance remains
**USER MUST VERIFY**.

## Performance

The accepted Build-0425 controlled result is retained as the before baseline:

```text
quiet IRQ total:       72,593 cycles
one common enemy:      87,443 cycles
enemy delta:           14,850 cycles
```

The minimum comparable Build-0426 measurement is in
`states/traces/build0426_enemy_delta_record1/frame_timing_series.csv`:

```text
                         quiet       one enemy      delta
worker cycles            69,408       82,208        12,800
IRQ total cycles          72,957       85,757        12,800
publication cycles         3,257        3,257             0
renderable candidates          0            1
residency misses               0            0
pattern installs               0            0
DMA words                    320          320
PC080SN map cycles              0            0
```

The enemy delta falls by **2,050 cycles**, or **13.8047%**. Unchanged
publication, DMA, residency-miss, pattern-install, and background values place
the saving in the intended native gameplay sprite/dispatch work.

The established rope benchmark is deterministic across three trials:

```text
Build 0425: 817 frames / 13,634.222 ms
Build 0426: 806 frames / 13,450.653 ms
saving:      11 frames /    183.569 ms (1.346%)
arcade:     771 frames / 12,850.000 ms
```

Build 0426 remains 35 frames / 600.653 ms behind the arcade Silver Standard.

## Files changed for Build 0426

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/pc090oj_assets.s`
- `apps/rastan-direct/Makefile` (compact sprite artifact wiring only for this task)
- `tools/translation/precompute_pc090oj_frame_table.py`
- `tools/translation/verify_pc090oj_frame_table.py`
- `tools/translation/verify_pc090oj_direct_dispatch.py`
- generated `build/pc090oj_generic_frame_index.bin`
- generated `build/pc090oj_generic_piece_table.bin`

No Layer A/B logic, gameplay AI, collision, damage, movement, enemy timing,
sound, scheduler/IRQ ownership, fallback retirement, or attract cleanup was
changed. Phase D and Phase E were not started.

## Build artifacts

Complete 0426 family:

- `dist/rastan-direct/rastan_direct_video_test_build_0426.bin`
- `dist/rastan-direct/rastan_direct_video_test_build_0426_d.bin`
- `dist/rastan-direct/rastan_direct_video_test_build_0426_s.bin`
- `dist/rastan-direct/rastan_direct_video_test_build_0426_do.bin`
- `dist/rastan-direct/rastan_direct_video_test_build_0426_c.bin`

Canonical size: 2,698,936 bytes  
Canonical SHA-256:
`d174637016506e94b4c71c2673b8c8c83b152ae10f45196387e260646e871676`

### Build-counter disclosure

After the complete 0426 family had been produced, an attempt to refresh the
rolling canonical symbols invoked a Makefile target that also performs numbered
publication. It unintentionally consumed **0427** as a canonical rebuild of the
same source. The counter is therefore 427. The ledger and artifact are preserved;
no number was deleted, renamed, or reused. The requested deliverable remains the
complete Build 0426 family above.

## Hardware acceptance

**USER MUST VERIFY** on real Genesis: normal R1/P1 play, Lizardman, Large Bat,
Small Bat, player, rope/composite and item/effect rendering, palette,
orientation/flip, missing pieces, flicker/corruption, overall speed, and the
`0426_do` overrun comparison.

