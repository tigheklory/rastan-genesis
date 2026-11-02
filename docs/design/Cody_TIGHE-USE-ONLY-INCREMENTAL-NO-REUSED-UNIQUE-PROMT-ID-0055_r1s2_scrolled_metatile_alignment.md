# R1-S2 scrolled Plane A metatile alignment — corrected diagnosis and Build 0528

Date: 2026-11-02

Assignment: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0055`

Reference: Build 0526. Rejected intermediate: Build 0527. Candidate: Build 0528, not accepted pending Tighe's gameplay test.

## Result

Build 0527 did not change the reported scene because its residency change affected the ordinary
`$055948/$055990/$055A14` row-publication path. The camera motion in Tighe's screenshots instead
takes the original program's no-publication arm at `$055704` or `$055790`: it changes foreground Y
without writing PC080SN name RAM. The arcade therefore exposes the completed record already retained
in the hardware ring.

Genesis recognized the no-publication event but selected row content with the current
`A5+$013E` record. Original `$0558E0` has already advanced that field to the next record and saved
the completed record's selector in `A5+$132C`. In the initial R1-S2 castle state, the ring contains
completed record 16 while `A5+$013E` names record 17. Genesis consequently substituted record 17
content as vertical motion exposed record 16. This is the demonstrated source-record error.

Build 0528 selects the completed predecessor. If its selector is 1 or 2, it copies the existing
final-native pan-row asset for `record-1`. If its selector is 0, it resolves the row from the live
source pointers one complete 16-entry revolution back. It adds no coordinate offset, scene special
case, map, buffer, translation layer, VRAM allocation, DMA, collision change, or gameplay change.

## Confirmed visual symptoms

- R1-S2 is correct before vertical scrolling.
- As vertical motion exposes additional scenery, the first chain appears about two metatiles left
  and the second about one metatile right.
- The correct graphical vocabulary exists and collision/traversal work.
- Build 0526 and then Build 0527 produced no visible correction to this symptom.

The opposite offsets are observations, not correction constants.

## Original arcade behavior

The foreground fields remain:

| Field | Hardware commit | Meaning |
|---|---|---|
| `A5+$10B0` | `$055AC4 -> $C20002` | foreground Y |
| `A5+$10AE` | `$055ACC -> $C40002` | foreground X |

PC080SN descriptors are 4x4 cells: a 32x32-pixel metatile. Sixteen descriptors produce one
64-cell row. The original scene fill consumes all 16 groups of record 16. At `$0558E0` it:

1. saves the completed selector from `A5+$10A8` to `A5+$132C`;
2. loads the next selector through the advanced record pointer;
3. increments `A5+$013E` from record 16 to record 17.

During subsequent camera motion, `$055696` with `A5+$10BA < $0100` (and the converse arm rooted at
`$05572E`) updates the camera accumulator and commits Y but does not call `$055948`, `$055990`, or
`$055A14`. No new name-RAM row is authored. The visible row must therefore come from the completed
record retained in the PC080SN ring.

The selector-1/2 transform itself remains source-equivalent: its sixteen descriptor pointer lanes
are destination column blocks, its four subcells remain contiguous columns, and selector direction
controls the source subrow/destination-row ordering. Static exhaustive checks continue to pass.

## Existing Genesis mismatch

`.Lplane_a_publish_logical_row_native` handles these no-publication camera steps. Before Build 0528,
when the current selector was nonzero it indexed `genesistan_plane_a_pan_row_maps` with current
`A5+$013E`. That is correct only if the current record is the content retained in the ring. After
`$0558E0`, it is already the next record.

This also explains why Build 0527 was unchanged. Build 0527 altered ordinary selector-1/2 calls to
`$055A14`; the failing route never makes that call. Its claim that the visible defect was an entering
row rejected against old scroll Y was therefore wrong. The Build 0527 ordinary-publication behavior
remains in the source, but it is neither relied on nor claimed here as the correction for Tighe's
reported defect.

## Representative source-derived mismatch

Static generated data for exposed rows 25 through 32 compares completed record 16 with incorrectly
selected record 17. Their differing cells per 64-cell row are respectively 53, 52, 53, 16, 16, 16,
17, and 55. That is a record/layout substitution, not a uniform X displacement.

For logical row 31:

| Columns | Intended retained record 16 | Existing wrong record 17 |
|---|---|---|
| 8..11 | descriptor `$3A90`; raw `$0824,$0825,$0826,$0827`; attr `$0009` | descriptor `$5534`; raw `$0824,$0825,$08F7,$0827`; attr `$000D` |
| 56..59 | descriptor `$4064`; raw `$0824,$0825,$08F7,$0827`; attr `$000D` | descriptor `$5034`; raw `$0824,$0825,$0826,$0827`; attr `$0009` |

The destination columns do not move. Different architectural features occur at different authored
columns in the two records, so replacing one whole record's row with another can make one feature
appear left and another right. That matches the visual constraint without an arbitrary global shift.

## Competing hypotheses

| Hypothesis | Finding |
|---|---|
| A. Stale physical N-32 row from a rejected ordinary publication | Rejected as the reported cause by Tighe's unchanged Build 0527 result and by the active no-publication control flow. |
| B. Wrong source columns/record | Proven: the retained record is 16 while Genesis indexed advanced record 17. |
| C. Wrong destination columns | Rejected: final columns remain `segment*4+subcell`; Build 0528 does not alter them. |
| D. Wrong selector transpose/reversal | Rejected by original loop structure and exhaustive selector static checks. |
| E. Mixed old/new generation | Yes as a consequence: retained record-16 geometry was being replaced by current record-17 row data. It is not a per-feature fault. |

## Minimal correction

Implementation source commit: `e667827c7ba776813e692d78b718887e10564fda`.

Changed production behavior in `apps/rastan-direct/src/tilemap_hooks.s`:

- inspect completed selector `A5+$132C` on a no-publication step;
- for completed selector 1/2, use the existing pan-row asset at `A5+$013E-1`;
- for completed selector 0, mark predecessor mode with the internal `$FFFF` reference sentinel and
  resolve each cell from live source pointers exactly 16 entries back;
- retain the existing dirty-row staging/publication and collision behavior.

Two existing static verifiers were extended. All 16 groups and all 64 columns prove that
`current_pointer_entry + (block-current_group-16) == block`, so the selector-0 path selects exactly
the preceding completed revolution. All 16,384 predecessor cells prove that every relevant current
package can reproduce its predecessor and that selector-1/2 predecessors have the exact existing
pan-row asset.

Build 0526's record-17 selector-1 to record-18 selector-0 mixed-ring suffix correction remains
present and unchanged.

## Architecture boundary

- **Semantic cut retained:** the original arcade decision to move foreground Y without publishing a
  row, which semantically retains the completed record/ring.
- **Chip tail removed:** PC080SN name-RAM retention and exposure below that decision are realized as
  final Genesis Plane A name words.
- **Compatibility intentionally remaining:** existing arcade-derived descriptor tables, final-native
  pan-row assets, staging buffer, dirty-row publisher, and collision grid remain. No legacy tail was
  removed in this narrow correction and no new PC080SN shadow/projection was added. Their existing
  retirement boundary is unchanged.

## Verification

No task-specific trace, automated gameplay traversal, save state, first-divergence capture, or new
diagnostic infrastructure was created. Original arcade evidence was static: the canonical Ghidra
export, original disassembly, descriptor data, and existing generated assets. The only runtime test
was the normal Makefile-mandated Genesis-driver MAME release trace.

Passed:

- assembler build of `tilemap_hooks.s`;
- incremental Plane A static verifier, including exhaustive predecessor pointer arithmetic;
- selector-1/2 gate: 128 destination cases, 1,869,856 source/attribute cases, 1,869,856 output cases,
  and 4,096 residency cases;
- scene/fill verifier: 24,576 scene cells, 204,800 checkpoint cells, 16,384 pan cells, 16,384
  no-publication predecessor cells, and 1,138,688 authored descriptor cells;
- subround derivative check: only selector `$DF` and direct-start audio command `$27` differ;
- boot guards, canonical gate, gameplay-entry gate, seven-epoch/package gate;
- required Genesis-driver MAME NTSC 30-second trace: 1,798 frames, final PC `$03B2C8`, SP
  `$00FEFFFC`, no unique unmapped addresses.

No original-arcade MAME, BlastEm, Exodus, or hardware runtime test was performed in this task.

## Build 0528 artifacts

Counter transition: 0527 -> 0528. Consumed ledger: `0528 PRODUCED`,
`canonical=PASS entry=PASS epoch=PASS`.

Canonical patch manifest: 228 opcode-replacement sites; expected Genesis bytes covered
`0x39DEB8`; coverage delta `0x50000`.

| Artifact | Size | SHA-256 |
|---|---:|---|
| `dist/rastan-direct/rastan_direct_video_test_build_0528.bin` | 3,792,568 | `d814e0fec605af60e29a044bc867c4d37591828921f8546720f4aeba7d6107c2` |
| `dist/rastan-direct/rastan_direct_video_test_build_0528_S1-2.bin` | 3,792,568 | `c4c6fbe2fbc1f684c344eecc0f9fd588b43301a82863bc4a206df02d5acfc82c` |

The source identity for both artifacts is implementation commit
`e667827c7ba776813e692d78b718887e10564fda`; `_S1-2` is the established same-number derivative.

## USER MUST VERIFY

Build 0528 remains a candidate. In the `_S1-2` ROM, Tighe must verify:

1. the initial R1-S2 screen remains unchanged;
2. climbing through exposed logical rows 25..32 keeps the first and second chains horizontally
   continuous instead of showing the reported opposite offsets;
3. downward and then upward camera motion restores the same architecture;
4. the record-17 selector-1 to record-18 selector-0 handoff remains coherent;
5. R1-S1 and R1-S2 checkpoint respawn, collision, traversal, Plane B, sprites, palettes,
   Re-In-Carnation audio, and boss entry remain unchanged.

Unresolved: static proof establishes the correct retained predecessor and the exact prior mismatch,
but only Tighe's actual route can accept the visible result. STOP status: **NO**. Candidate status is
not acceptance.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0055`
