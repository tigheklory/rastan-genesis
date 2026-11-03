# Andy — Build 0321 Full (code,bank) Layer-A — PROVEN CAPACITY STOP (epoch 4 > 484)

**Type:** implementation/verification. EXTENDING. No new build produced (proven STOP #3). Line 2 protected.

## 1-3. Baseline + visual oracle + deferment
Build 0320 = routing-revert baseline (Build-0316 colors). Tighe supplied segment 0-3 visual targets
(seg0 brown exterior; seg1-2 dark purple/mauve cave; seg3 cyan/teal water). Vertical-scroll issue is
explicitly DEFERRED / out of scope (no changes made).

## 4-6. Frozen policy + the 64-code bug
Frozen SHA deb696452d7456b3... 1576 usages, 1314 codes, 64 multi-map codes, 1576 (code,bank) keys, 0
conflicts, 0 missing indices. Build 0316/0320 use one dominant pattern per code -> wrong colors for the
non-dominant bank's cells (proven: code 0x308 bank 0x01C cells get bank 0x01A's pattern).

## 7. The blocker — all 64 codes need WITHIN-EPOCH (code,bank) variants
The boundary architecture is code->slot per epoch, enforced by a hard gate
(compile_pc080sn_genesis.py:420 "logical code changes physical identity inside epoch"). Analysis of the
frozen policy: **all 64 multi-map codes have within-epoch conflicts (103 (epoch,code) pairs needing >1
different final pattern)** — most in epoch 4 (record 11). So none are resolvable by the code->slot model;
each needs a runtime name-word remap keyed by the cell's source bank + its own variant slot.

## 8. PROVEN CAPACITY STOP (task STOP condition #3)
Counting the UNIQUE final (code,bank) target patterns actually required per epoch vs the hard Plane-A
capacity of 484:

| epoch | records | faithful (code,bank) unique patterns | baseline (0316 dominant) | vs 484 |
|---|---|---|---|---|
| 0 | 0,1,2 | 281 | 282 | ok |
| 1 | 3 | 364 | 333 | ok |
| 2 | 4-9 | 441 | 444 | ok |
| 3 | 10 | 392 | 368 | ok |
| **4** | **11** | **531** | **483** | **OVER 484 by 47** |
| 5 | 12,13,14 | 431 | 433 | ok |
| 6 | 15 | 338 | 349 | ok |

**Epoch 4 (segment 11) needs 531 distinct Layer-A target patterns; Plane-A has 484 slots.** The faithful
(code,bank) policy for segment 11 cannot fit without either merging variants (= dominant maps, forbidden by
this task) or dropping patterns (forbidden, zero-drop required). This is a genuine, proven technical STOP
(#3), not an implementation-effort issue: no zero-drop faithful allocation exists at 484 for epoch 4.

## Why segment 11 overflows
Segment 11 uses several source codes (incl. 0x308/0x309/0x30A...) under BOTH banks 0x01A and 0x01C in the
same epoch; reindexing splits patterns that shared raw bytes, raising the epoch's distinct-pattern count
from 483 (already near cap) to 531.

## Tighe's decision required (options)
1. Reduce distinct (code,bank) variants in segment 11 in the editor (consolidate some Layer-A mappings so
   the segment fits <=484 distinct target patterns).
2. Accept a bounded dominant/merge for the ~47 overflow variants in epoch 4 only (documented visual
   compromise) while the other segments are fully faithful.
3. Split epoch 4 / segment 11 into finer residency epochs (a boundary-architecture change) so each fits 484.
4. Some other authored reduction.

Once the epoch-4 demand is <=484 by one of these, the (code,bank) target asset + runtime bank-keyed variant
selector (design in Andy_build0320_...md) can be implemented and built.

## Not changed
No build produced (0320 stands). Raw pc080sn.bin, Layer B, Line 2, Rastan routing, vertical scroll: all
untouched. compile_pc080sn_genesis:420 one-pattern-per-code-per-epoch gate NOT weakened.

## USER MUST VERIFY / DECIDE
Choose an option above for segment 11's 531>484 overflow; then I implement the full (code,bank) pipeline and
build it. Segments 0,1,2,3,5,6 all fit 484 faithfully and would render the correct editor colors.
