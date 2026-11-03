# Cody — Native Graphics Phase B: Proven R1/P1 Expansion (Build 0404)

## Result

Build 0404 extends the accepted Build-0403 native frame architecture only to
the two additional semantic subsets whose complete runtime key and graphics
contract are proven: the Round-1 cave block and the burst/impact child. The
complete five-ROM family passed the canonical, gameplay-entry, palette, frame,
and artifact-family gates. Visual/gameplay acceptance remains Tighe's test.

Accepted input baseline: **Build 0403**.

## Readiness and exact coverage

| Semantic usage | Phase-B status | Native selectors | Fallback / unknown | Effective bank | Pattern identity | Residency |
|---|---|---|---|---|---|---|
| player | NATIVE_PARTIAL | 75 body selectors × none/sword/axe/hammer × 2 orientations = 600 | fire sword: 150 explicit UNRESOLVED; out-of-range selectors | proven | direct finalized vi | existing shared transient |
| cave block | NATIVE_COMPLETE for exact tuple | state `0x1E`, base `0x0179`, anim `0x70`, compositor `0`, both orientations = 2 | every other base-`0x0179` semantic | `0x3C` | Level B direct finalized vi | scene/family resident working set |
| burst / impact child | NATIVE_COMPLETE for exact tuples | state `0x0F`, base `0x0275`, anim `0x9E/0x9F/0xA0`, compositor `0`, both orientations = 6 | inherited-base branch and every other selector | `0x30` | Level B offline-finalized variant vi | shared transient |
| flying demon | PALETTE_COMPLETE_FRAME_PARTIAL | none | all selectors; full body/wings selector binding unresolved | `0x35` | unresolved | accepted fallback |
| lizardman | GRAPHICS_KNOWN_SELECTOR_UNKNOWN | none | all selectors | `0x36` | unresolved | accepted fallback |
| valkyrie | GRAPHICS_KNOWN_SELECTOR_UNKNOWN | none | all selectors | `0x32` | unresolved | accepted fallback |
| chimera | GRAPHICS_KNOWN_SELECTOR_UNKNOWN | none | all selectors | `0x34` | unresolved | accepted fallback |
| four-armed insect | GRAPHICS_KNOWN_SELECTOR_UNKNOWN | none | all selectors | `0x3A` | unresolved | accepted fallback |
| small bat | GRAPHICS_KNOWN_SELECTOR_UNKNOWN | none | all selectors | `0x3E` | unresolved | accepted fallback |
| large bat | GRAPHICS_KNOWN_SELECTOR_UNKNOWN | none | all selectors | `0x3E` | unresolved | accepted fallback |

Machine-readable authority for this build is
`build/pc090oj_frame_table.coverage.json`; the generated human summary is
`build/pc090oj_frame_table.report.txt`.

## Semantic key and dispatch cut

The generic native key is the exact retained tuple:

```
(actor+0x05 state,
 actor+0x1E base tile,
 actor+0x01 animation selector,
 actor+0x38 compositor selector,
 effective bank,
 original three-field orientation predicate)
```

This deliberately does not treat `actor+0x38` or the base tile as unique actor
identity. In particular, `0x0179` is reused by another actor route; requiring
the proven cave-block state `0x1E` prevents that reuse from being claimed by the
Round-1 cave-block entry. Burst entries likewise require child state `0x0F`.
Actor attribute-bit-6 overrides and every unlisted tuple retain the exact
Build-0403 interpreter path.

The semantic cut remains above PC090OJ execution: retained arcade state selects
the frame; a native hit emits final Genesis semantic pieces directly. There is
no PC090OJ object-RAM record or chip-tail emulation. A miss falls through to the
accepted direct-native generic compositor; gameplay, AI, collision, movement,
spawn/despawn, and animation selection remain arcade-owned.

## Compiler and independent verifier

`precompute_pc090oj_frame_table.py` now governs player and generic frames in one
artifact family. It validates the H16 burst evidence and the canonical actor
graphics manifest, expands the exact general-compositor programs, precomputes
piece order, geometry, orientation, attributes, and finalized identities, and
appends the eight generic records after the unchanged player payload prefix.

Generated facts:

- player index: 4,500 bytes; 600 native and 150 UNRESOLVED;
- player frame-table prefix: unchanged 18,220 bytes;
- generic index: 96 bytes; eight exact native entries;
- combined frame table: 18,840 bytes; 406 deduplicated payloads;
- generalized residency file: `P9RS` version 2, 758 records;
- cave pieces: 4 per orientation;
- burst pieces: 8, 9, and 10 per orientation.

The independent verifier re-expands the authoritative ROM programs rather than
trusting generator output. It checks each semantic tuple, actor-state
discriminator, program address, piece order/count, signed geometry,
orientation, source code, effective-bank low nibble, canonical `(code,bank)` to
vi result, attributes, size, flags, and exact residency set.

Results:

- Layer 1 `verify_reindexed_pc090oj.py`: **PASS** — 916 requirements, 793
  unique codes, 123 variants, zero mismatches, zero incomplete entries, zero
  stray writes, and all 344 Rastan base codes retained.
- Layer 2 `verify_pc090oj_frame_table.py`: **PASS** — 600 player native, eight
  generic native, 150 player UNRESOLVED.

## Finalized vi, opacity, and residency

Cave-block pieces are non-divergent and carry their final direct code/vi.
Burst pieces are palette-divergent and carry the offline-finalized
`0x2000 | vi` residency identity produced by the canonical Palette Composer
variant index. No palette decision is duplicated in the frame compiler.

The canonical variant generator now also emits the inverse
`pc090oj_variant_source_code[vi]`. The common finalizer uses that source code
only for the existing blank/opaque-bounding-box test, while preserving the
pre-finalized vi for residency and DMA. This prevents finalized vi zero from
being mistaken for blank code zero and preserves source-art opacity geometry.

After that adapter, every new piece uses the accepted Build-0403 O(1) two-level
reverse residency lookup. There is no slot scan and no second allocator. The
existing reservation/eviction behavior, emit-on-miss behavior, and bounded
12-entry tile-DMA worklist are unchanged. The largest newly compiled frame has
10 distinct requirements, within that transaction bound.

## Protected Build-0403 behavior

- the 600 player-native keys and their index are unchanged;
- the first 18,220 frame-table bytes remain the player payload;
- all 150 fire-sword keys remain explicit UNRESOLVED fallback;
- player FRONT/BODY lanes and weapon-anchor publication are unchanged;
- secondary/legs and all generic UNRESOLVED paths retain fallback;
- palette policy and `specs/palette_decisions.json` are unchanged;
- IRQ6, scheduling, controller sampling, watchdog/IPL, and the shelved
  Build-0401 ownership design are untouched.

## Gates and artifacts

- assembler/linker/boot guards: PASS;
- canonical ROM gate: PASS;
- gameplay-entry gate: PASS (`240/240` post-entry frames, player control
  observed);
- address errors: 0;
- bus errors: 0;
- illegal instructions: 0;
- crash-handler entries: 0;
- normal Genesis NTSC MAME trace: 1,798 frames, no unmapped-memory report;
- VDP ownership: PASS structurally — new producer code only appends through the
  accepted native queue/finalizer/publication path; no scheduling or direct VDP
  ownership was added;
- complete canonical/`_d`/`_s`/`_do`/`_c` family gate: PASS.

The pre-existing Phase-1 seven-epoch target warning remains unchanged. Its
target-epoch proof passed; no PC080SN/epoch code was changed by Phase B.

Build 0404 artifacts (all 1,793,720 bytes):

| Artifact | SHA-256 |
|---|---|
| `rastan_direct_video_test_build_0404.bin` | `5f6585292a60ef3ded5c6a34337eec9137eaa3cae36b9d4dda0fd20d786a3d49` |
| `rastan_direct_video_test_build_0404_c.bin` | `334f3b8bac3ab8c5243895361981337937b2034ee027424fd28b82f2dc4094b1` |
| `rastan_direct_video_test_build_0404_d.bin` | `18e709da3c5ef9236686f069ed6d2960c4e699ecac88b99f1e6d904715b715c7` |
| `rastan_direct_video_test_build_0404_do.bin` | `40db366fcb31a20079689cdce804ada8dac249edd541b8255d87b6fda2782537` |
| `rastan_direct_video_test_build_0404_s.bin` | `9bb0b621ede1a100c2f4bc9c98835448f56640dc528afa13f271f7e401a89eac` |

## Source changes

- `apps/rastan-direct/Makefile`
- `apps/rastan-direct/src/pc090oj_assets.s`
- `apps/rastan-direct/src/pc090oj_hooks.s`
- `tools/graphics_editor/gen_reindexed_pc090oj.py`
- `tools/translation/precompute_pc090oj_frame_table.py`
- `tools/translation/verify_pc090oj_frame_table.py`

Tighe must validate ordinary Round-1 play, cave-block rendering/destruction,
burst effects, player/weapons including fire-sword fallback, other fallback
actors, scrolling/transitions, sprite flips/palettes/pattern coherence, and
absence of crashes. Phase C must not begin until Tighe explicitly accepts
Build 0404.
