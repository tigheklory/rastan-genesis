# Cody Round-1 Phase-1 Plane-A Independent Pattern Audit

## Status and blind-review boundary

- Task type: independent static research / clean-room verification.
- Production baseline observed: Build 0309; counter 309.
- Production source changed: NO.
- ROM built: NO.
- Build 0310 consumed: NO.
- `docs/design/Andy_build0310_smart_plane_a_retention_review.md` read: NO.
- Andy Build-0310 numeric/count artifacts read: NO.
- Pre-existing `analysis/round1_phase1_plane_a/` artifacts read: NO.
- Current compiler collectors used to define the source set: NO.
- Blind result frozen before compiler comparison: YES.

The numeric conclusions in sections 1-12 were frozen with
`analysis/cody_round1_phase1_plane_a_independent/blind_freeze.sha256` before the
current Genesis compiler was inspected. Any later compiler comparison is kept in
a separate section and does not redefine the arcade source set.

## 1. Original inputs and independent tooling

Original-region inputs:

| Input | Size | SHA-256 |
|---|---:|---|
| `build/regions/maincpu.bin` | 393216 bytes | `4f30b9e7aa946aa33d20e125a1726ff094f9615980107d0842efe1721cf32063` |
| `build/regions/pc080sn.bin` | 524288 bytes | `a33372eb4f768136cbb5311125e65da7587d31bb1d91a72d32775d22eb44059b` |

The clean-room reconstructor is
`tools/audit_round1_phase1_plane_a.py`. It imports no Genesis compiler or tile
collector. It reads original big-endian arcade map structures, follows the
original descriptor format, decodes packed-MSB 8x8x4 PC080SN graphics directly,
and hashes the resulting 32 pixel bytes.

Mandatory reverse-engineering references inspected were the Ghidra project at
`tools/ghidra/rastan_project/rastan_arcade_ref.gpr`, its project data, and the
independent exports under `analysis/ghidra/rastan_arcade/exports/`. Relevant
original arcade PCs include `0x050248`, `0x0502CC`, `0x0503E4`, `0x0557BA`,
`0x055948`, `0x055968`, `0x0559B2`, and `0x055AB4`.

The PC080SN format and draw-order checks were independently cross-checked against
official MAME `rastan.cpp` and `pc080sn.cpp`: 64x64 tilemaps; tile code
`word1 & 0x3FFF`; color `attr & 0x01FF`; horizontal/vertical flip in attribute
bits 14/15; no tile-priority field in the tile-info decode; tilemap 1 transparent
over opaque tilemap 0.

## 2. Arcade layer to Genesis Plane A

Neutral arcade layer: **PC080SN tilemap 1 at HW address `0x00C08000`**.

Independent proof:

1. Original arcade gameplay trigger `arcade_pc 0x0557BA` is the selector-0
   horizontal publisher path.
2. Dispatcher `arcade_pc 0x055948` selects strip-A publisher `0x055968` for
   selector 0; cell producer `0x0559B2` consumes the 4x4 descriptors.
3. Its destination cursor is formed from `0x00C08000`, and its scroll state is
   committed by the original PC080SN path.
4. Official MAME draws tilemap 0 opaque, then transparent tilemap 1, then sprites.
5. This full-rate foreground/playfield ownership corresponds to the port's
   Genesis Plane A semantic layer; tilemap 0 corresponds to Plane B.

Result: original arcade PC080SN tilemap 1 maps to Genesis Plane A.

## 3. Round-1 Phase-1 bounds

The bounds come from original progression tables, not Genesis package membership:

- Stage-to-segment LUT: arcade ROM/data `0x05073A`.
- Segment-to-selector-stream offset LUT: `0x050EE0`.
- Selector stream: `0x050F6B`.
- Round-1 Phase-1 segment records: **0 through 15 inclusive**.
- Segment 15 is selector 0 followed by event byte `0x04`.
- Segment 16 is the first post-event target and begins Round-1 castle/fortress
  Phase 2; later Round-1 vertical/castle records and the boss phase are excluded.
- World columns: **0 through 1023 inclusive**.
- World-X: **0 through 8191 pixels inclusive**.

All Phase-1 records use selector 0. The scene fill publishes all 64 rows and each
subsequent horizontal strip publisher emits the complete 64-row column. Therefore
the legal publication range is rows **0 through 63**. With fixed Phase-1 vertical
scroll and the original visible area `y=8..247`, rows **1 through 30** are currently
visible; rows 0 and 31-63 are still legally published ring contents.

## 4. Original map reconstruction

The 16 tilemap-1 strip-source bases are:

`0x1691C, 0x18BDC, 0x1AE9C, 0x1D15C, 0x1F41C, 0x216DC, 0x2399C, 0x25C5C,
0x27F1C, 0x2A1DC, 0x2C49C, 0x2E75C, 0x30A1C, 0x32CDC, 0x34F9C, 0x3725C`.

Each table contributes one 4-row band. A segment occupies `0x40` bytes in each
table: 16 entries of `{attr16, descriptor_pointer16}`. Each descriptor's first
32 bytes are a row-major 4x4 tile-word block. The reconstruction expands all 16
entries across all 16 row bands for every Phase-1 segment, yielding exactly one
64x64-cell map per segment.

Classification:

| Category | Cells/codes | Treatment |
|---|---:|---|
| A, currently visible map-referenced | 30,720 cells | Counted |
| B, legally publishable but offscreen | 34,816 cells | Counted |
| C, source-table present but unreferenced | 0 codes | Excluded |
| D, outside Phase-1 segments | 3,128 distinct physical patterns not in Phase 1 | Excluded |
| E, outside legal Phase-1 rows | 0 codes | Excluded |
| F, zero-pointer/padding/sentinel cells | 0 cells | Excluded |

The D count scans every non-Phase-1 segment 16-138 in the same 139-entry arcade
source tables. It does not expand the Phase-1 source set.

## 5. Map and column results

- Total legal Plane-A map cell references (A+B): **65,536**.
- Unique arcade tile codes: **1,316**.
- Machine-readable cell map:
  `analysis/cody_round1_phase1_plane_a_independent/map_usage.csv`.
- Column map:
  `analysis/cody_round1_phase1_plane_a_independent/column_usage.csv`.

`column_usage.csv` contains all 1,024 world columns, their 8-pixel world-X span,
segment, 64 legal cells, unique logical codes, and unique exact physical patterns.

## 6. Physical bitmap counts

Direct packed-MSB decoding of each referenced code produced:

- **Unique exact 32-byte physical patterns: 1,315.**
- **Unique flip-normalized physical classes: 1,246.**
- Exact duplicate logical-code excess: **1**.
- Potential pattern slots saved by H/V/HV flip reuse: **69**.
- Exact physical groups used with more than one attribute word: **199**.
- Additional attribute variants beyond one per physical group: **265**.
- Physical groups used with more than one palette index: **199**.
- Priority aliases: **0**; PC080SN tile-info has no decoded priority field here.

Pixel identity is intentionally independent of palette, priority, H flip, V flip,
and placement. Those remain name-table semantics and do not create new 32-byte
physical patterns.

## 7. Pattern lifetimes and simultaneous set

`physical_patterns.csv` records first/last world column and every disjoint use
interval for each exact physical pattern. A pattern may have many gaps; first/last
alone is not treated as continuous residency proof.

The PC080SN tilemap is a 64-column ring. For every contiguous 64-world-column
window, the audit unions the exact patterns in all 64 legal rows:

- Full Phase-1 vocabulary: **1,315** exact patterns.
- Maximum simultaneously present in one legal 64-column ring window: **603**.
- Maximum window: columns **684-747**.

Thus full-phase vocabulary and simultaneous map requirement are not equivalent.

## 8. Descriptive source-bank families

The four groups below are neutral stage-LUT/source-bank checkpoints, not claims
that a visual environment changes exactly at each boundary. Pattern counts may
overlap between groups.

| Family | Segments | World columns | Exact patterns |
|---|---|---|---:|
| `outside_source_bank_0` | 0-3 | 0-255 | 582 |
| `outside_source_bank_1` | 4-7 | 256-511 | 387 |
| `outside_source_bank_2` | 8-11 | 512-767 | 757 |
| `outside_source_bank_3` | 12-15 | 768-1023 | 752 |

The map previews show the opening terrain, smaller cave-like/vertical structures,
the narrow bridge, later exterior terrain, and the fortress approach. They also
show why environmental labels must not be inferred merely from four-segment
checkpoint groupings.

## 9. Brick bridge check

The deck-only bridge is independently located at:

- Segments: **9 and 10**.
- World columns: **608-637**.
- World-X: **4864-5103 pixels**.
- Exact Plane-A physical patterns: **30**.
- Shared with earlier Phase-1 columns: **15**.
- First introduced at the bridge relative to earlier columns: **15**.
- Also present in Round-1 castle data: **1**.

Approach slopes and landing terrain are outside this deck-only count. No separate
residency event is inferred from the bridge's shape.

## 10. Atlases and frozen artifacts

| Artifact | Path |
|---|---|
| Exact atlas | `analysis/cody_round1_phase1_plane_a_independent/exact_patterns_atlas.png` |
| Flip-normalized atlas | `analysis/cody_round1_phase1_plane_a_independent/flip_normalized_patterns_atlas.png` |
| Cell map | `analysis/cody_round1_phase1_plane_a_independent/map_usage.csv` |
| Physical patterns | `analysis/cody_round1_phase1_plane_a_independent/physical_patterns.csv` |
| Column usage | `analysis/cody_round1_phase1_plane_a_independent/column_usage.csv` |
| Independent summary | `analysis/cody_round1_phase1_plane_a_independent/independent_summary.json` |
| Freeze manifest | `analysis/cody_round1_phase1_plane_a_independent/blind_freeze.sha256` |

The exact atlas has one independently decoded tile per exact physical hash. The
second atlas has one representative per H/V/HV equivalence class. Images are
diagnostic outputs only and are not compiler inputs.

## 11. Blind artifact hashes

The authoritative full list is in `blind_freeze.sha256`:

| Artifact | SHA-256 |
|---|---|
| `map_usage.csv` | `a17c9b6f89e5a983efe23ae8cd3e2932363670ae1e944ccec78573d8b64565c6` |
| `physical_patterns.csv` | `b2920f20ae43e634de82903fd0c3728b874ec20c71ec2416cd57607f3a79a590` |
| `column_usage.csv` | `1599e80e681d21643538335d19e26ca220e1890e1ac6a6d9d7311572ab0a96cf` |
| `exact_patterns_atlas.png` | `0d5312d8ea494b96adb7cdaf3403dcf6845c5f5b956f07887216249184838e70` |
| `flip_normalized_patterns_atlas.png` | `2941023d1f73242ccb6f502430379c389d46de6e1ef0c6be515952f6f2310a8c` |
| `independent_summary.json` | `e649eb97cc0d3459ef0ab487831ac71301c4f9e557a79c00b086beeaba46a6c5` |

## 12. Frozen independent conclusion

The complete Round-1 Phase-1 Plane-A vocabulary does **not** fit in 1,315 pattern
slots if the available Plane-A capacity is lower than that. The actual 64-column
ring never needs more than 603 exact patterns simultaneously, and each neutral
four-segment source bank independently uses at most 757. This supports a coarse
semantic residency model if the independently verified free Genesis capacity is
at least 757; it does not by itself require future-aware or per-column retention.

**Frozen primary verdict before compiler inspection: B. Full vocabulary does not
fit as one set, but a coarse semantic residency model fits, subject to the later
hard-owner capacity check.**

## 13. Current compiler comparison

This comparison was performed only after the section 11 artifact hashes were
written and reverified. The reproducible post-freeze comparison is:

- `analysis/cody_round1_phase1_plane_a_independent/postfreeze_compiler_compare.py`
- `analysis/cody_round1_phase1_plane_a_independent/postfreeze_compiler_comparison.json`

### Process disclosure

After the blind artifacts were frozen, a command intended to inspect the latest
repository log tail exposed Andy Build-0310 numeric entries. This violated the
instruction not to read those entries. It happened after the independent CSVs,
atlases, summary, hashes, and sections 1-12 had been made durable. No frozen
number was changed, and none of the exposed numbers was used for this comparison;
the values below were recomputed directly from current source and original ROM
data. At freeze time, no Andy Build-0310 numeric result was known.

### Source-set comparison

The current collector at
`tools/translation/precompute_pc080sn_tile_lut.py:342` walks, for each selected
record, 16 source banks x 16 descriptor groups x 4 columns x 4 rows. This is the
same complete 64x64 legal map traversal independently reconstructed for records
0-15. It does not add unused entries, off-map columns, or illegal rows within a
selected record.

The boundary compiler selects all 23 Round-1 records 0-22
(`tools/translation/compile_pc080sn_genesis.py:100` and `:301`), not only Phase 1.
Its aggregate source set is therefore broader than the Phase-1 question:

| Set/category | Exact physical patterns |
|---|---:|
| Independent Round-1 Phase-1, records 0-15 | 1,315 |
| Current compiler aggregate, records 0-22 | 1,855 |
| Current compiler records 0-15 subset | 1,315 |
| Compiler-only wrong-phase records 16-22 | 540 |
| Other compiler-only categories | 0 |
| Independently required but compiler-missing | 0 |

The current compiler aggregate also contains 1,856 logical tile codes. Its
records 0-15 exact-pattern subset matches the independent Phase-1 set exactly.
Thus the compiler is not missing Phase-1 material; its aggregate input crosses
the Phase-1 boundary by design. Calling all 1,855 patterns a Phase-1 requirement
would be an over-count, while using the compiler as a whole-Round-1 source set is
not itself disproven by this audit.

The allocator uses exact 32-byte blobs as its physical unit
(`compile_pc080sn_genesis.py:307-326` and `:341-365`). It therefore does not
allocate duplicate physical patterns for the one logical-code alias.

Compiler comparison answers:

| Question | Result |
|---|---|
| Over-scans source-table members inside records 0-15 | NO |
| Over-scans Phase-1 columns | NO |
| Over-scans legal Phase-1 rows | NO |
| Crosses the Phase-1 boundary | YES, records 16-22 |
| Creates duplicate physical bit-pattern allocations | NO |
| Exact aggregate match to Phase 1 | NO |
| Exact records-0-15 subset match | YES |

## 14. Independently checked Genesis capacity

The current generated boundary report and compiler constants establish this hard
gameplay allocation:

| Owner | Pattern slots | Count |
|---|---|---:|
| Blank | 0 | 1 |
| Fixed Plane B | 1-854 | 854 |
| Plane A | 855-1338 | 484 |
| Native sprite cells | 1339-1534 | 196 patterns / 49 16x16 cells |
| Spare remainder | 1535 | 1 |

This calculation uses the actual generated 854-pattern Plane-B allocation, not
an older nominal reserve or visually blank-looking VRAM. The effective Plane-A
capacity is therefore **484 exact patterns**.

Capacity results:

| Plane-A requirement | Patterns | Fits 484? |
|---|---:|---|
| Full Phase-1 exact vocabulary | 1,315 | NO |
| Full Phase-1 flip-normalized vocabulary | 1,246 | NO |
| Largest neutral four-segment source bank | 757 | NO |
| Largest complete 64-column legal ring | 603 | NO |
| Largest 40-column visible view | 483 | YES, by 1 |
| Largest 41-column sub-tile-scrolled view | 483 | YES, by 1 |

Full-phase or four-segment coarse residency is therefore not sufficient under
the current hard owners. A complete 64-column name-table ring also cannot have
every referenced identity resident simultaneously. However, the actual visible
40/41-column envelope fits exactly within the A allocation. The simplest model
supported by these measurements is bounded compiler-generated streaming aligned
with the original arcade strip publisher and visible-column lifetime, retaining
exact patterns while referenced and preparing entering-column patterns before
their name words become visible. This is not a recommendation for a general
runtime LRU, Belady policy, or per-frame software chip cache.

## 15. Final architecture verdict

The frozen pre-capacity verdict in section 12 was **B, conditional on the hard
owner check**. The measured 484-slot capacity is below both the 757-pattern
coarse-family maximum and the 603-pattern full-ring maximum. The final verdict is
therefore:

- **C:** real bounded streaming/retention is required.
- **D:** the current compiler aggregate over-counts the Phase-1 question by 540
  wrong-phase patterns, although its records-0-15 subset is exact.

No Build 0310 implementation should begin from this audit alone. A follow-up
implementation contract must define the native strip-publication cut, entering
column preload timing, slot/name-word coherence, and fail-closed capacity proof
without changing Plane B, collision, or scrolling semantics.
