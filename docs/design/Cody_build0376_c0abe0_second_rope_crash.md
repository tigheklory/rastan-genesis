# Cody — Build 0376 second-rope `C0ABE0` crash

**Status:** implemented and statically closed; the exact Round-1/Sub-round-2 second-rope climb
still requires Tighe's BlastEm 1.0 validation.

## A. Scope, baseline, and numbering

The user-visible baseline is Build 0374. Build 0375 had already been produced and consumed by the
rejected Phase-2 residency-preinstall experiment before this urgent task began, so it was neither
overwritten nor reused. The next Makefile-owned artifact is Build 0376 (`375 -> 376`). The three
residency-preinstall source changes unique to rejected Build 0375 were removed; the accepted/
observed Build-0374 Phase-2 package extension remains.

This task changes only two bounded PC080SN producer routes capable of raw C-window publication:
the newly reported collision-surface visual tail and the historically proven sibling directional
dispatcher. Rope logic, collision classification, Phase-2 package ordering, palettes, actors,
sprites, and the parked missing-block issue were not investigated.

## B. User debugger evidence

BlastEm 1.0 stopped Build 0374 during the second-rope vertical climb at final PC `0x0005A3F8`,
`move.l D0,(A1)+`. The reported post-increment `A1=0x00C0ABE4` proves the attempted destination
was `0x00C0ABE0`; `D0=0x000025C7` and `A0=0x00FF33F0` exactly match the retained routine's
constant and collision-cell input. The VDP used Plane A at `0xE000`, Plane B at `0xC000`, and
64 KiB VRAM; `0xC0ABE0` was a 68000 memory destination, not a VDP command or VRAM address.

## C. Current Build-0374 PC mapping and semantic function

Build 0374 final PC `0x5A3F8` maps to original arcade PC `0x05A34E`, the second of four
`move.l D0,(A1)+` instructions in `collision_map_surface_mark_5a2ee`. Its caller is the retained
per-player-update surface postprocessor at original `0x05A29C`, which scans 16 collision cells and
calls `0x05A2EE` when collision word bit 7 is set.

Before the visual tail, `0x05A2EE` performs the gameplay-owned work:

- writes four collision words with value 1 starting at `A0`;
- visits four cells at `A0-0x280` and preserves their low byte while adding `0x3400`;
- then converts `A0` back into a PC080SN Layer-A address and writes four visual cells `0x25C7`.

The semantic cut is original PC `0x05A334`: all collision semantics remain copied and executable;
only the chip-specific address conversion and raw four-cell publication below that boundary are
retired.

## D. Exact `A1` formation

Build 0374 had already rebased the collision-map base from arcade `0x0010DE00` to Genesis WRAM
`0x00FF1E00`. The visual tail did:

```text
A1 = 0x00C08000 + 2 * (A0 - 0x00FF1E00)
   = 0x00C08000 + 2 * (0x00FF33F0 - 0x00FF1E00)
   = 0x00C08000 + 2 * 0x15F0
   = 0x00C08000 + 0x2BE0
   = 0x00C0ABE0
```

`A0-0xFF1E00=0x15F0` is collision word index `0x0AF8`. Doubling converts the two-byte collision
cell spacing to the four-byte PC080SN name-cell spacing, yielding raw C-window cell index `0x0AF8`
(64-wide row 43, column 56). The four long writes target columns 56..59. This is an arcade
PC080SN RAM pointer. It is not a Genesis staging pointer and not a legal direct Genesis VDP port.

## E. Historical `C0ABE0` and Build-0303 comparison

The root class is **related, but the immediate producer is different**.

Build 0303 redirected the gameplay call at original `0x05109C` away from
`0x055AD6 -> 0x055B28/0x055B32/0x055B3C/0x055BB6 -> 0x055C4A` and into
`genesistan_pc080sn_directional_dispatch_native`. That helper preserved the retained direction,
camera, descriptor, and progression decisions while publishing the selected Plane-B column via
Genesis staging and the residency LUT.

Build 0304 removed that redirect as a regression-isolation experiment. Build 0305 subsequently
proved the regression was instead a stale shifted pass-table immediate at original `0x0503CE`;
Build 0306 fixed that pointer. The Build-0303 dispatcher redirect was never restored, leaving the
copied directional family reachable again through original `0x05109C`.

The Build-0374 fault, however, did not execute that historical family. Original `0x05A334` is an
independent Layer-A surface-marker tail that constructs the same `0xC0ABE0` address from the live
collision cell. Build 0168 had rebased its collision-buffer subtraction at `0x05A336`, but had not
retired the following raw PC080SN address construction or stores.

## F. Bounded sibling-producer audit

| Producer | Build-0376 classification | Reason |
|---|---|---|
| `0x055AD6` dispatcher | RETIRED from gameplay caller | original `0x05109C` now calls the native dispatcher |
| `0x055B28` bit-0 arm | NATIVE | gate and `A5+0x10B0 -> A5+0x10EE` semantics exist in the helper |
| `0x055B32` bit-1 arm | NATIVE | sibling gate/copy exists in the helper |
| `0x055B3C` forward edge | NATIVE | accumulator, progression, and staged Plane-B column publication retained |
| `0x055BB6` reverse edge | NATIVE | reverse accumulator/progression retained |
| `0x055C4A` shared tail | RETIRED from this dispatcher | descriptor/source decisions are realized natively; raw loop is unreachable from `0x05109C` |
| `0x055C5E` separate strip entry | NATIVE (pre-existing) | existing replacement jumps to `genesistan_hook_itempage_strip_blit` |
| `0x05A334` Layer-A surface visual tail | NATIVE | complete raw tail replaced by four-cell Plane-A staging helper |

Thus no raw PC080SN writer remains live in either the reported surface-marker producer or the
bounded historical directional family.

## G. Root cause and fix

The first faulting divergence was not VDP configuration. It was retained arcade chip execution:
the copied surface postprocessor correctly recognized a collision surface, then its untranslated
visual tail used the relocated Genesis collision pointer to reconstruct an original PC080SN
C-window address and executed a normal 68000 store there.

The shift replacement at original `0x05A334` replaces all 34 bytes through the original return
with `jsr genesistan_collision_surface_mark_visual_native; rts`. The helper derives the identical
logical Layer-A cell from `A0`, supplies code/attribute longword `0x000025C7`, and asks the existing
native Plane-A fill producer to resolve the LUT slot, write four staged name words, and dirty the
bounded row. It preserves `A0` and `D1` and leaves `D0=0x25C7`, matching the meaningful original
tail result. It creates no fake C-window memory, address clamp, ignored write, NOP, or inert RTS.

The old overlapping `0x05A336` address-rebase replacement was removed because its entire
chip-specific converter is now below the native semantic cut. The original `0x05109C` call is
again redirected to the already-established native directional dispatcher. Build 0305's proven
pass-table correction remains intact.

Tile code `0x25C7` is now a declared build-time requirement in all six stable Round-1 packages and
both transition packages. It resolves to stable slot 735 in every package. Stable-package exact
pattern counts are `[283,334,640,584,640,283]`, below the 676-slot cap; transition packages are
395 and 479 patterns. There is no runtime cache, blank fallback, or stage/rope special case.

## H. Static and runtime validation

Final canonical Build-0376 mapping/disassembly proves:

- original `0x05A334` -> final `0x05A3DE`: `jsr 0x070AFA; rts`;
- the preceding collision mutations at final `0x05A398..0x05A3DC` remain intact;
- helper `0x070AFA` computes the same cell identity, stages four `0x25C7` cells, and returns;
- original `0x05109C` -> final `0x0512A8`: `jsr 0x070B22`, the native dispatcher;
- the Build-0374 rebased raw surface-tail byte sequence occurs zero times in the canonical ROM;
- the four raw `0x25C7` `move.l` sequence occurs zero times;
- the old copied directional call target sequence occurs zero times;
- compiler and transition-retention gates pass, with zero package misses/collisions in their
  bounded proofs.

The canonical gate and Genesis-driver NTSC MAME gameplay-entry gate pass. The entry gate reports
zero address errors, bus errors, illegal instructions, and crash-handler entries. The mandatory
30-second Genesis MAME trace completed 1,798 frames with no unique unmapped address. These routes
do not reproduce the second-rope climb, so they do not replace the required BlastEm test.

The known legacy “seven-epoch” gate still reports failure because it targets the superseded epoch
model; the Makefile preserves and labels that result as it did for Builds 0374/0375. The current
transition-retention gate passes.

## I. Build and artifacts

- Produced build: **0376**
- Counter: `375 -> 376`
- Canonical opcode-replacement sites: 229
- Canonical Genesis coverage: `0x1A3EB8` bytes
- Canonical ROM: `dist/rastan-direct/rastan_direct_video_test_build_0376.bin`
- SHA-256: `79541c3a67f022b5bf4f91914e75d67fa47d4f4581e5e3574ed4310749a887cd`
- Size: 1,719,992 bytes

| Variant | SHA-256 | Size |
|---|---|---:|
| `_d` | `b868ca83c4f68f016781b87346ebf48564abff98136cefb16da886f5b0fe8a32` | 1,719,992 |
| `_s` | `2c1b8b888399468a54132d3fc377c83fbb47620127387ebac7414b9863b216c2` | 1,724,088 |
| `_do` | `a73c5943d45ca6fbc9420623f2add64cd5137f93482e1ddc56048bf5b86450c7` | 1,719,992 |
| `_c` | `5e83edc782c36f6870c790f4a14065c03c7582b1384a4f7331b601fb7c6bce16` | 1,724,088 |

The score diagnostic now crosses one additional aligned helper-coverage page; its recipe records
the mechanical `+0x1000` variant delta, like the existing `_c` contract. The complete same-number
variant-set gate passes.

Production inputs changed:

- `specs/rastan_direct_remap.json`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/fg_tile_cache.s` (revert of rejected 0375-only ordering text)
- `tools/translation/compile_pc080sn_genesis.py`
- `apps/rastan-direct/Makefile` (score-variant aligned-coverage declaration)
- this report and `AGENTS_LOG.md`

Generated manifests, address maps, disassembly, residency packages, artifacts, and trace outputs
were regenerated by the normal pipeline.

## J. Deferred issues and user validation

No claim is made about the deferred Build-0374 visual observations: isolated Phase-1 cells, early
bridge/castle switching, Sub-round-2 Layer-A palette, floor-spear anchoring, Phase-2 initial fill,
or either parked rope-exit block. None was investigated here.

Tighe must test canonical Build 0376 in BlastEm 1.0 at the exact second-rope climb and confirm:

1. no `C0ABE0` or other unmapped write occurs during vertical/castle scrolling;
2. the affected terrain publication remains visible rather than being suppressed;
3. Plane A and the major Build-0374 Phase-1 improvement remain present;
4. bridge, rope, and waterfall transition behavior has not regressed.

Second-rope result: **USER MUST VERIFY**. STOP after delivery; no Phase-2 residency-ordering work
was resumed.
