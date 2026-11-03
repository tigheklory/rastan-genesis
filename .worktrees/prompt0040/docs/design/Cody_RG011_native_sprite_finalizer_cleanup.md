# RG-011 Native Sprite Finalizer Cleanup Audit

**Date:** 2026-10-21  
**Scope:** Phase 1 proof and conditional implementation gate  
**Accepted baseline:** Build 0472  
**Result:** hypothesis disproved on the accepted source; no production change and no Build 0473

## Baseline and policy boundary

The accepted artifact remains
`dist/rastan-direct/rastan_direct_video_test_build_0472.bin`, SHA-256
`5b855e163a572c3a511a76470199c9cb13324f6ea0739bbd0f6834b80092dc7a`,
produced by source `4d5aadb0e92387617594404f9e757597c87517a3`. The current production
source, remap spec, and translation tools have no difference from that exact source. The immutable
`accepted/build-0472` tag also peels to that commit, and the build counter remains 472.

The governing semantic cut is retained arcade actor/frame/position/flip/palette/visibility/order
state -> generated native frame record -> final Genesis SAT. The already removed chip-specific tail
is the PC090OJ descriptor/piece interpreter, object-RAM production and mirror, object scan, and
decoder. RG-011 removes no additional tail because its proposed duplicated derivation is absent.
The generated Level-A universal records and dynamic tile-residency directory remain below the cut:
the former is a compact transitional coverage format for retained actor semantics, while the latter
is Genesis-native VRAM allocation rather than PC090OJ emulation. Gameplay has no PC090OJ object-RAM
mirror or scanner.

## Original meaning and current native path

Canonical Ghidra exports establish the original master-render flow:
`0x041DAE` and `0x045DFA` call `0x03D054`, which enters the old shape-expansion tail including the
default `0x03C950` path. The current generated address map maps those master sites to patched sites
`0x041FAA` and `0x045FF6`. Current gameplay instead enters
`native_stage_dispatch_41dae` / `native_stage_dispatch_45dfa`, then
`.Lnative_emit_actor_common`.

On a generated Level-B hit, `.Lnative_generic_frame_try` consumes a generated 4,096-byte base LUT,
one ten-byte usage descriptor, and an eight-byte frame index. Each six-byte piece is
`{dx, dy, finalized_key}`; actor X/Y and the generated frame attribute produce the final eight-byte
semantic queue record `{attr, Y, key, X}`. Compact death and universal generated paths converge on
the same queue and finalizer.

`.Lnq_emit_lane` loads each queue record and calls `.Lnq_emit_entry_cached`. The finalizer then:

1. normalizes one direct source code or performs one finalized-variant source lookup;
2. validates blank/source identity only for the genuinely dynamic Level-A form;
3. constructs one `pc090oj_opaque_bbox + source_code * 16` pointer;
4. applies live X/Y wrap, global flip, Genesis origin, and exact oriented opaque clipping;
5. resolves any genuinely dynamic palette variant;
6. resolves the late-bound physical VRAM cell through the O(1) reverse-residency directory,
   allocating and queuing tile DMA on a miss; and
7. writes final SAT Y/link/attribute/tile/palette/X words in lane order.

VBlank commits the bounded tile-DMA worklist before publishing the finished double-buffered SAT.

## Phase 1 hypothesis result

**Duplicate bbox/source derivation confirmed: NO.**

The decisive current-source comment at `.Lnq_identity_validated` says that Build 0409 reconstructed
the same source a second time. Build 0410 already changed the finalizer to keep the opaque-bounds
pointer live across coordinate geometry. Inspection of every path from `.Lnq_entry_ctrl_ready` to
`.Lnq_bbox_source_ready` confirms one source normalization/lookup and one pointer construction. No
second mask/shift/table reconstruction exists below geometry.

The current operation is therefore **MIXED**, not legacy residue:

- generated direct or variant source identity and piece offsets are earlier-known static native
  information and are already carried in compact records;
- absolute bounds, visibility, global flip, current palette context where applicable, physical VRAM
  slot, DMA miss state, SAT link/order, and final coordinates are late-bound presentation facts.

Adding a bbox field to every compact piece would duplicate the existing source identity or widen the
six/eight/ten-byte record families merely to avoid a single source lookup on the finalized-variant
case. It would not remove the four bbox reads, coordinate additions, viewport tests, residency, DMA,
or SAT construction. No bounded memory/performance case justifies that representation change.

## Memory, semantics, and equivalence

No replacement was made:

- bytes added per record: 0;
- ROM impact: 0 bytes;
- WRAM impact: 0 bytes;
- VRAM impact: 0 bytes;
- gameplay/collision semantics changed: no;
- sprite ordering, clipping, palette selection, residency, and DMA behavior changed: no.

Static equivalence checks passed:

- `verify_pc090oj_frame_table.py`: 1,200 player, 416 secondary-player, 38 generic, 1,898 universal
  general, 24 universal specialized, and 60 compact-death native cases; zero player unresolved;
- independent opaque-bbox rebuild: 65,536 bytes / 4,096 records, byte-identical, SHA-256
  `17ece6e96088b6ba9daeeece587209e462df4d4153a7471a9171983368016783`;
- 123 generated `pc090oj_variant_source_code` entries exactly match all 123 `vi` entries in
  `build/regions/pc090oj_variant_index.json`, and none is blank;
- production source/spec/tool tree matches exact Build 0472 source `4d5aadb0...`.

## Performance accounting

The Build 0472 per-piece path performs one source normalization (the finalized-variant case adds one
bounded u16 lookup), one bbox pointer construction, orientation extraction, four bbox byte reads,
four coordinate additions, four viewport comparisons/branches, and separate O(1) residency plus SAT
work. Because RG-011 makes no candidate change, candidate work is identical and calculated savings
are exactly zero for 1, 3, 8, 16, and 32 pieces.

Historical measurement is retained only as context, not projected as a Build 0472 cycle claim:

- Build 0359 measured the complete bbox block at 0.496 physical line per normal hit, down from
  0.535; finalizer slope was 3.018 lines/emitted entry, finalizer median 91.041 lines, and full-chain
  median 285.410 lines.
- Build 0410 measured 46,502.94 cycles/update after removing the duplicated Build 0409 source work,
  down 7,305.54 cycles/update (13.58%) from Build 0409. That change included generated-identity
  improvements and is not evidence for a remaining duplicate.
- Accepted Build 0472's established rope result remains 795/795/795, median 13,267.083 ms. RG-011 did
  not rerun it because there is no candidate ROM.

## Build decision

Build 0473 was not justified and was not consumed. No Makefile target, ROM build, MAME gameplay,
trace, or hardware-acceptance request was initiated. Build 0472 remains the accepted baseline.
