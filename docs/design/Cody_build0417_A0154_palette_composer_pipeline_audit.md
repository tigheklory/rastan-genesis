# Cody Build 0417 — A-0154 Palette Composer Pipeline Audit

## Scope and result

This is a read-only audit of the Stage-1 Layer-A path for segment 11, map cell
X44/Y38:

- arcade tile code: `0x0117`
- physical pattern: `A-0154`
- primary logical usage: `LA-0092`, source bank `0x003`
- secondary logical usage: `LA-0543`, source bank `0x005`

No production source, palette profile, generated binary, or ROM was modified.
No build was run and no build number was consumed.

The bounded result is that Build 0417 **does consume the frozen Palette Composer
mapping for this tile**. The expected mapped tile is identical, pixel for pixel,
to the generated Layer-A tile, the complete generated 512 KiB Layer-A region is
identical to the region embedded in Build 0417, and the generated package mapping
selects that pattern with Genesis palette line 3. Neither the source nor generated
tile contains pixel index zero. The reported visual defect is therefore not
explained by a missing profile update, a generator mismatch, multi-palette collapse,
ROM packaging, or the statically selected name word.

Runtime VRAM/CRAM was not captured in this review, so the remaining boundary is the
runtime publication state, not the offline Composer pipeline.

## 1. Exact Composer profile state

Production reads the context-scoped mappings at:

```text
context_policies
  context:gameplay.r01.p01
    plane_usage_palette_mappings
```

The unrelated top-level `plane_usage_palette_mappings["LA-0092"]` is an older
empty entry (`line: 0`, empty `index_map`) and is **not** the value selected by
the Layer-A generator. The production generator explicitly indexes the R1/P1
context object.

The current `Test.json` and the frozen Build-0400 snapshot contain the same
context mappings:

| Usage | Source bank | Target line | Source → target |
|---|---:|---:|---|
| `LA-0092` | `0x003` | 3 | `4→7, 5→6, 6→11, 7→8, 8→9` |
| `LA-0543` | `0x005` | 3 | `4→7, 5→6, 6→11, 7→8, 8→9` |

No used source index maps to Genesis index zero. The two authored maps are
byte-for-byte/semantically identical.

The target Line-3 CRAM words in the same profile are:

```text
0000 028C 044C 0026 0004 0002 0424 0624
0402 0202 0200 0422 0440 0660 0AA6 0884
```

They are also present verbatim as `editor_layera_palette` in
`apps/rastan-direct/src/palette_hooks.s`.

## 2. Baseline versus Test

`baseline_current` is synthesized by `default_profile()` in
`tools/graphics_editor/server.py`. It has no `LA-0092` or `LA-0543` mapping,
no target line assignment, and an empty context policy. Consequently, if supplied
to `gen_reindexed_region.py`, these usages would be skipped and the source nibbles
would remain identity-mapped:

```text
4→4, 5→5, 6→6, 7→7, 8→8
```

The editable Test profile differs by assigning both usages to Line 3 and applying
the five explicit remaps above. That Test override reaches production; Build 0417
does not contain the baseline/identity realization.

## 3. Source tile decode

`plane_a_uses.json` identifies both logical usages as tile `0x0117`, source byte
address `0x0022E0`, and physical SHA-256
`87de5f48973d611de5fae662f633e55ea327bdcbf37719d577b5d19ca55d2ea3`.
The raw 32 bytes in `build/regions/pc080sn.bin` are:

```text
66686778688887778855887755558876
55558776555587765544587655445877
```

Decoded high-nibble first, the 8×8 source matrix is:

```text
6 6 6 8 6 7 7 8
6 8 8 8 8 7 7 7
8 8 5 5 8 8 7 7
5 5 5 5 8 8 7 6
5 5 5 5 8 7 7 6
5 5 5 5 8 7 7 6
5 5 4 4 5 8 7 6
5 5 4 4 5 8 7 7
```

Pixel counts:

| Index | Count |
|---:|---:|
| 0 | 0 |
| 4 | 4 |
| 5 | 20 |
| 6 | 9 |
| 7 | 15 |
| 8 | 16 |
| all others | 0 |

The Palette Composer UI summary `{4,5,6,7,8}` and five used colors is correct.

## 4. Exact production dataflow

The Layer-A path is:

1. `analysis/graphics_optimizer/editor_policy/Test.json` is frozen as
   `build/rastan-direct/build0400/Test.snapshot.json`.
2. `apps/rastan-direct/Makefile` defines that snapshot as
   `EDITOR_LAYERA_SNAPSHOT` and invokes
   `tools/graphics_editor/gen_reindexed_region.py`.
3. `gen_reindexed_region.py:main()` reads:
   - the frozen profile;
   - `analysis/graphics_optimizer/round1_phase1/plane_a_uses.json`;
   - `build/regions/pc080sn.bin`.
4. It selects
   `context_policies["context:gameplay.r01.p01"]`
   `['plane_usage_palette_mappings']`, resolves `LA-NNNN` by the usage-list
   index, groups each authored map by `tile_code`, and chooses the most frequent
   map for each physical code.
5. It applies that map to each nonzero nibble and writes
   `build/regions/pc080sn_editor_layera.bin`.
6. `tools/translation/compile_pc080sn_genesis.py --boundary-experiment` consumes
   that reindexed region. `build_boundary_experiment()` uses the exact 32-byte
   tile blob as the physical allocation identity, builds code→slot and upload
   pairs, and writes `build/pc080sn_boundary/boundary_packages.bin`.
7. `apps/rastan-direct/src/scene_load.s` includes the complete reindexed region at
   `genesistan_pc080sn_tile_rom`; `apps/rastan-direct/src/fg_tile_cache.s` includes
   the package binary at `fg_boundary_packages`.
8. The package installer loads a representative arcade code, multiplies it by
   32, addresses `genesistan_pc080sn_tile_rom`, and DMA-copies 16 words to the
   generated VRAM slot.
9. `resolve_plane_a_cell` reads code `0x0117`, calls `fg_cache_resolve`, combines
   the resolved slot with `.Lplane_a_native_attr_from_word`, and stages the final
   Genesis name word.

The separate `compile_editor_layera.py` creates a per-usage proof manifest, but
it is not the production region generator. The production generator is
`gen_reindexed_region.py`.

## 5. Build-0417 profile and artifact proof

Build 0417's Makefile input is the frozen snapshot:

```text
build/rastan-direct/build0400/Test.snapshot.json
SHA-256 02d0122a7d9ea91040f24350d299772f7f37196957eaa7e9b2f627bd9e47e250
```

The current editable profile is byte-identical:

```text
analysis/graphics_optimizer/editor_policy/Test.json
SHA-256 02d0122a7d9ea91040f24350d299772f7f37196957eaa7e9b2f627bd9e47e250
```

Thus the current Test profile and the profile consumed by the production rule are
the same (`profile_id: Test`, manifest revision 30). The snapshot filename says
Build 0400 because that is when this frozen revision became the production input;
it is still the explicit Build-0417 dependency.

Generated region:

```text
build/regions/pc080sn_editor_layera.bin
size    524288 bytes
SHA-256 9c7ceddae22b34c6a31904c5d9caa8410d672cf4d4ffea774387bda4acec6964
```

Build-0417 ROM proof:

```text
dist/rastan-direct/rastan_direct_video_test_build_0417.bin
SHA-256 36f8300bedc077c9b3af99c83c1b0fc9d2623e2acfa4541e7cea86f8d78b4835

genesistan_pc080sn_tile_rom = ROM 0x0015DD08
ROM[0x0015DD08 : 0x001DDD08] == pc080sn_editor_layera.bin
full 524288-byte equality: YES
```

The package artifact is also included exactly:

```text
build/pc080sn_boundary/boundary_packages.bin
size    62272 bytes
SHA-256 c70e90cb6a2f70eb81de25842eb8b05ad8c7395eaa6d3970944693fafc529471

fg_boundary_packages = ROM 0x00074ECC
full 62272-byte equality: YES
```

## 6. Multi-palette representation

`A-0154` has exactly these two R1/P1 logical usages in the census:

| Usage | Bank | Total cells | Authored map |
|---|---:|---:|---|
| `LA-0092` | `0x003` | 304 | `4→7,5→6,6→11,7→8,8→9` |
| `LA-0543` | `0x005` | 24 | `4→7,5→6,6→11,7→8,8→9` |

Production emits one code-indexed pattern, not separate `(code,bank)` variants.
That general representation can collapse a bank-dependent multi-palette tile,
as the generator's own header documents. It is **not a defect for A-0154**:
both authored maps and target lines are identical, so the two usages legally share
one reindexed Genesis pattern. The generator's map counter has one unique map with
count 2; there is no competing realization to collapse.

## 7. Expected Composer tile versus generated tile

Applying the Test map to the source matrix gives:

```text
11 11 11  9 11  8  8  9
11  9  9  9  9  8  8  8
 9  9  6  6  9  9  8  8
 6  6  6  6  9  9  8 11
 6  6  6  6  9  8  8 11
 6  6  6  6  9  8  8 11
 6  6  7  7  6  9  8 11
 6  6  7  7  6  9  8  8
```

The generated bytes at code `0x0117` are:

```text
bbb9b889b9999888996699886666998b
6666988b6666988b6677698b66776988
SHA-256 f6a269928459e3df8af38584cd285448a0e16019ffe690dc7c82f3abeb7ca389
```

Generated pixel counts:

| Genesis index | Count |
|---:|---:|
| 0 | 0 |
| 6 | 20 |
| 7 | 4 |
| 8 | 15 |
| 9 | 16 |
| 11 | 9 |
| all others | 0 |

Expected-versus-generated comparison: **64/64 pixels match; 0 mismatches**.
No source index produced a zero texel.

## 8. Segment-11 occurrence and name-word proof

Reconstructing the complete segment-11 64×64 Layer-A map through the same
descriptor tables used by the editor gives 49 A-0154 occurrences:

- 43 cells are `LA-0092`, bank `0x003`;
- 6 cells are `LA-0543`, bank `0x005`.

The target X44/Y38 cell is:

```text
entry address     0x02A4C8
descriptor cell  0x003298
attribute        0x0003
tile code        0x0117
usage            LA-0092
physical         A-0154
H/V flip         none / none
```

Segment 11 initially selects generated transition package 8 and hands off to
stable package 3. Both packages map code `0x0117` to decimal slot 1128
(`0x0468`) with the same 32 pattern bytes. `.Lplane_a_native_attr_from_word`
forces authored R1/P1 Layer A to Line 3 (`0x6000`) and adds no H/V bits for
attribute `0x0003`. No priority bit is added.

Therefore the statically generated final name word is:

```text
pattern  0x0468
palette  line 3
H flip   0
V flip   0
priority 0
word     0x6468
```

All 49 segment-11 cells resolve to the same generated 32-byte pattern. The
offline data path therefore follows physical A-0154, not `LA-0092` specifically;
the bank-5 cells are not assigned a distinct pattern because none is required by
their identical authored map.

## 9. MRD contract

The source tile has five used indices, so its complete pairwise MRD set has
`C(5,2) = 10` pairs. Test maps those five indices injectively to
`{7,6,11,8,9}`. The Composer validation therefore correctly reports zero MRD
merges.

Production preserves the same five distinct indices in the generated tile, with
counts corresponding exactly to the source. No later offline deduplication
collapses pixel indices: allocation deduplicates only identical complete 32-byte
patterns.

## 10. Palette-decision registry

`specs/palette_decisions.json` has no entry containing `LA-0092`, `LA-0543`,
`A-0154`, `0x0117`/`0x117`, or the Stage-1 purple-rock description. Therefore:

- Composer/Test authoring exists and is consumed;
- there is **no canonical Palette Decision ID** for this tile;
- consistency status is `NO REGISTRY ENTRY`, not a proven conflict.

Any future palette-authoring change must add/update the canonical registry in the
same task rather than creating another mapping authority.

## 11. Build 0414–0417 history

The complete embedded 512 KiB Layer-A region is byte-identical in all four ROMs,
despite moving as linked code size changed:

| Build | Region ROM base | Region SHA-256 | `0x0117` tile SHA-256 |
|---:|---:|---|---|
| 0414 | `0x0015DBF0` | `9c7ceddae22b34c6a31904c5d9caa8410d672cf4d4ffea774387bda4acec6964` | `f6a269928459e3df8af38584cd285448a0e16019ffe690dc7c82f3abeb7ca389` |
| 0415 | `0x0015DD78` | same | same |
| 0416 | `0x0015DD78` | same | same |
| 0417 | `0x0015DD08` | same | same |

The complete `boundary_packages.bin` is also byte-identical in 0414–0417,
appearing respectively at ROM offsets `0x074DB4`, `0x074F3C`, `0x074F3C`, and
`0x074ECC`. Thus neither the A-0154 mapping nor its generated pattern changed in
0417. This is not a pattern regression introduced by the Build-0417 full-span
background repair.

## 12. Failure classification and remaining boundary

Primary classification: **H — NONE OF ABOVE / OTHER**.

Evidence against the proposed pipeline failure classes:

- **A, wrong tile identity:** X44/Y38 statically resolves to code `0x0117`,
  A-0154, and slot `0x0468`.
- **B, Composer/index-map error:** no zero target, no MRD merge, and no mismatch
  is established by this audit. Visual fidelity of the chosen colors is a
  separate decision and currently has no registry entry.
- **C, build ignores current profile:** frozen snapshot and current Test are
  byte-identical, and the ROM contains the mapped realization.
- **D, variant collapse:** there is one shared pattern, but both usage maps are
  identical, so sharing is legal.
- **E, generator mismatch:** 64/64 pixels match.
- **F, ROM packaging error:** the entire generated region and package artifact
  match the ROM byte-for-byte. Runtime VRAM remains untested.
- **G, name-word/palette-line error:** the static resolved word is `0x6468`,
  selecting slot `0x0468` and Line 3 with no flips/priority.

The next bounded action, if requested, is a single runtime check at the reported
visible occurrence: compare VRAM slot `0x0468` against the proven 32 bytes, CRAM
Line 3 against `editor_layera_palette`, and the live Plane-A name word against
`0x6468`. That would distinguish runtime upload/publication/CRAM state from a
misidentified visual source without changing production data.

## Audit disposition

- Production modified: **NO**
- Palette profile modified: **NO**
- ROM built: **NO**
- Build number consumed: **NO**
- ROM matches generated offline Layer-A payload: **YES**
- ROM matches runtime VRAM: **NOT TESTED**

