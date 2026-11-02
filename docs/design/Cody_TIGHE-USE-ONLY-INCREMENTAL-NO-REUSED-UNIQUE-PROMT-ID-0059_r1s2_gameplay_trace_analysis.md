# Build 0529 R1-S2 gameplay trace analysis

Date: 2026-11-02

Agent: Cody

Assignment: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0059`

Production baseline: Build 0528; diagnostic capture: Build 0529

## Result

The remaining corruption is not a separate jump renderer and is not supported as a missed VBlank
DMA. It is a semantic error in the Build 0528 Plane A **no-publication** replacement.

The original arcade arms at `$055704` and `$055790` change camera bookkeeping and Y scroll without
writing PC080SN name RAM. The already-resident physical ring row remains exactly as it was. The
Genesis hooks instead reconstruct and overwrite all 64 words of every entering physical row. At
`tilemap_hooks.s:1407-1450`, a nonzero current selector and zero completed selector always select
the preceding selector-0 revolution. That decision is row-blind: it does not ask whether ordinary
selector-1 publication has already replaced this physical row with current-record contents.

The gameplay traces prove that this blanket predecessor choice destroys current rows. For example,
in the aggressive run, ordinary selector-1 publication first writes current record 17 rows 44, 45,
and 46. The no-publication path later rewrites the same physical rows 12, 13, and 14 with different
predecessor hashes. The first two markers at 2192 and 2379 observe those rows after the overwrite.
The same sequence repeats at record 17 rows 12-14 and record 21 rows 35-42 and 60-62.

This explains why Build 0528 is mostly correct and why aggressive climbing reveals more failures:
Build 0528 corrected the record used by many predecessor rows, but still substitutes a generated
row for a semantic no-write. Faster movement and reversals cause more no-publication crossings after
ordinary publication, creating more chances to overwrite a valid current row. Normal and mixed
play also enter the same path, so jumping is neither necessary nor a distinct cause.

Several sparse markers occur while predecessor contents are legitimately required and therefore do
not reduce to the already-current-row case. They still originate in the same destructive
reconstruction path, but this capture does not contain the pre-write resident/VRAM row words needed
to identify the first wrong cell. The bounded conclusion is therefore:

1. the architectural root cause is confirmed: a source no-publication operation is implemented as
   a destructive full-row reconstruction;
2. one concrete selection failure within that architecture is confirmed: already-current rows are
   overwritten as predecessor rows;
3. the exact cell/source error in the predecessor-selector-0 rows seen by the sparse normal markers
   is not recoverable from these hashes alone.

No production source, trace, ROM, or generated asset was changed during this diagnosis.

## Trace inventory and validity

The active captures are:

| Condition | Directory | Total trace frames | Markers |
|---|---|---:|---|
| Aggressive jump-assisted | `states/traces/r1s2_rope_build_0529/jump` | 9,726 | 2192, 2379, 2769, 2896, 6405, 6586, 6813, 7390, 7405, 7570, 7656, 8116 |
| Mixed | `states/traces/r1s2_rope_build_0529/normal_mixed_20261102_165047` | 8,893 | 1731, 1986, 2366, 2459, 6374 |
| Minimal jumping | `states/traces/r1s2_rope_build_0529/normal` | 8,971 | 1993, 6484 |

All three metadata files identify the same diagnostic ROM, SHA-256
`f47d3ed5c91e5e7a424de8f71e7f5622fbd8a71fbbf4a98e693992bbd8421e4a`.
The input is manual, the trace declares no WRAM writes, and exact path entries are debugger execution
breakpoints. The two original unmarked captures remain archived under
`states/traces/r1s2_rope_build_0529_first_20261102_164300` and were not modified.

The report uses the marker as an observation time, not an origin. Every marker was searched at least
120 frames backward; persistent cases were extended hundreds of frames to their last relevant row
write. Split row chunks were reconstructed with the trace's documented order-sensitive recurrence
`H = H*65599 + word + column (mod 2^32)`.

## Comparator lead and three-condition comparison

`comparison.md` pairs repeated states by occurrence order using
`fg_y/record/selector/completed_selector/strip/group/entering_logical_rows`. It does not include
player position or movement intent, so it is useful for locating equivalent semantic samples but is
not a causal alignment.

Its earliest reported difference, aggressive frame 749 versus normal frame 787, has identical
record 17, selector 1, completed selector 0, strip/group 0, no entering row, no staged write, and no
dirty row. Only `total_vlines` and the final V-counter samples differ (6 versus 7 lines). Both execute
`FG_COMMIT>SCROLL_COMMIT`. This is timing variation, not the scenery corruption.

The meaningful comparison is by record, logical/physical row, and writer history:

- Equivalent no-publication rows have identical hashes across movement styles. Examples include
  record-17 logical rows 44-46 (`2E41754F`, `5E85E216`, `A55C3DE9`) and record-21 logical rows 1-7.
  Input does not make the Python asset or resolver nondeterministic.
- Aggressive play reaches more direction changes and repeated crossings. It therefore executes more
  destructive row reconstructions after ordinary current-row publication.
- Wall contact, facing, and jump state never appear in `.Lplane_a_publish_logical_row_native`'s
  source choice. Their demonstrated effect is cadence, not a different row-selection rule.
- No marker window shows a later unrelated Plane A producer replacing the identified pan rows.
- The same no-publication writer PC, `$070FC2`, occurs in all three runs.

## Marked windows and originating updates

The table groups markers which observe one persistent defect. `P` is the 32-row Genesis physical
row; logical rows are the 64-row arcade coordinates. Frame ranges include split staging chunks.

| Condition / marker(s) | Earliest relevant write history | Finding |
|---|---|---|
| Aggressive 2192, 2379 | Current record-17 L44/L45/L46 were staged by the ordinary selector-1 writer at 1775-1776, 1771-1772, and 1768-1769. Pan-down rewrote P14 at 1990-1991, P13 at 1994-1995, and P12 at 2029-2030. | Confirmed current-to-predecessor destructive overwrite; the second marker is the same persistent defect. |
| Aggressive 2769, 2896 | Current record-17 L12-L14 were staged at 2484-2489. Pan-up rewrote P14/P13/P12 at 2673-2674, 2678-2679, and 2686-2687. | Confirmed repeat of the same error; marker delay is 82-222 frames. |
| Aggressive 6405 | Record-21 predecessor reconstruction progresses through P0-P1 across 6117-6282; the marker's visible top is 63. | Same no-publication writer and deterministic predecessor rows; exact wrong cell is bounded because the capture has no pre-write resident row image. |
| Aggressive 6586, 6813 | Current record-21 L60-L62 were staged at 6286-6292. Pan-up rewrote P30/P29/P28 at 6497-6498, 6502-6503, and 6511-6512. | Confirmed destructive overwrite; the latter marker sees the same rows roughly 300 frames later. |
| Aggressive 7390, 7405, 7570, 7656 | Current record-21 L35-L42 occupy P3-P10 by 6706-7133. Pan-down rewrites P10..P3 at 7277-7322. | Confirmed one persistent eight-row corruption cluster, not four independent faults. |
| Aggressive 8116 | Record 22, selector 6, visible top 1. No new `$070FC2` visible-row write occurs in the preceding 600 frames. | Not assignable to a new row write. It may be persistence/physical-row aliasing across the record transition; exact origin is unproven. |
| Mixed 1731, 1986 | Record-17 predecessor rows P2/P1 complete at 1601-1607; earlier predecessor rows were staged in the same descent. | Same reconstruction path; not an already-current-row overwrite. Both markers can observe one persistent defect. Exact wrong cell is not captured. |
| Mixed 2366, 2459 | Current record-17 L44-L46 already exist; pan-up/down rewrites P14/P13/P12 at 2063-2069 and 2271-2291. | Confirmed current-to-predecessor overwrite; the hashes match the aggressive run despite different timing. |
| Mixed 6374 | Record-21 predecessor sequence completes P4-P1 at 6199-6214 after the longer P31..P5 sequence. | Same reconstruction path; exact predecessor-cell mismatch is bounded. |
| Minimal 1993 | Record-17 predecessor descent writes P24..P1 at 1404-1814. At the marker, visible top is 53, so those generated rows remain in the displayed 32-row window. | Same path without aggressive jumping. No trace evidence identifies a separate jump cause; exact wrong predecessor cell is bounded. |
| Minimal 6484 | Record-21 predecessor descent writes P0..P1 at 5999-6387. | Same path without aggressive jumping; exact wrong predecessor cell is bounded. |

Representative confirmed content substitutions are:

| Record / logical row | Ordinary current hash | Later no-publication predecessor hash | Physical row |
|---|---:|---:|---:|
| 17 / 44 | `DACFC3EC` | `2E41754F` | 12 |
| 17 / 45 | `1455A5FE` | `5E85E216` | 13 |
| 17 / 46 | `753F8C6F` | `A55C3DE9` | 14 |
| 17 / 12 | `E30C302B` | `CC9C8DAB` | 12 |
| 17 / 13 | `C2EA740F` | `B005C791` | 13 |
| 17 / 14 | `9615797B` | `E7B13175` | 14 |
| 21 / 60 | `68862F2B` | `F78C9F9D` | 28 |
| 21 / 61 | `6816070F` | `3B256D05` | 29 |
| 21 / 62 | `DB5D887B` | `50EE7F45` | 30 |

The trace records physical rows and hashes, while the logical row is recovered from the exact
selector call and its group/strip state. The trace frame containing the final write may show the
already-advanced strip, so using only that final sample would be off by one row.

## Arcade versus Genesis source

The canonical Ghidra export proves the original no-publication arms:

- `$055704`: load `A5+$10DA`; `$055708`: add it to `A5+$10BA`; control continues at `$05570C`.
- `$055790`: load `A5+$10DA`; `$055794`: subtract it from `A5+$10BA`; `$055798` begins the scroll-Y
  store tail.

Neither arm calls the ordinary row author at `$055A14`; therefore neither changes name RAM. The
physical row's generation is whatever prior ordinary publication and record history left resident.

Genesis differs at these exact locations:

- `apps/rastan-direct/src/tilemap_hooks.s:945-1013` derives entering rows and calls a native row
  publisher for each crossing.
- `tilemap_hooks.s:1391-1401` maps every logical row to `logical&31`.
- `tilemap_hooks.s:1407-1450` chooses one content source for the entire row. In the R1-S2 state
  `(selector=1, completed_selector=0)`, every row takes
  `.Lplane_a_row_previous_selector0`, regardless of whether selector 1 has already published it.
- `tilemap_hooks.s:1497-1502` overwrites all 64 staged words; `:1554-1558` marks the physical row
  dirty. Thus this is an actual publication, not bookkeeping equivalent to the arcade no-write.

The source comment at `:1409-1413` assumes the entering row is still the completed record. The
trace disproves that assumption after ordinary selector-1 progress: the ring is mixed by physical
row, and some entering rows already hold the current record.

## Publication and workload findings

A dynamic predecessor row often spans two trace frames because the resolver is expensive. That is
not evidence of partial publication: `fg_row_dirty` is set only after the complete 64-word loop at
`tilemap_hooks.s:1554-1558`. VBlank snapshots a dirty row and DMAs all 64 words before clearing its
bit (`vdp_comm.s:323-354`). Plane A publication precedes scroll commit in
`dma.s:81-92`.

The V-counter sequence is sampled into host frame buckets, and long helpers can cross VBlanks; a
bucket can consequently contain the tail of one VBlank and the start of another. Modulo values such
as 257-261 are wrap artifacts, not 261-line Plane A DMAs. In the representative failing states the
ordered execution remains `FG_COMMIT>SCROLL_COMMIT`, and no required dirty bit is shown skipped.
The captures therefore do not support VBlank overrun, incomplete row DMA, or scroll-before-row as
the root cause.

## Offline rows and bounded missing evidence

There is no evidence that Python emits input-dependent or intermittently wrong data. Reconstructed
full hashes for the same record/logical row repeat across aggressive, mixed, and minimal play. The
existing exhaustive gates check the generated rows against their declared formulas.

Those gates do not validate the runtime question the arcade actually poses: *what exact generation
is currently resident in this physical ring row?* A correct predecessor asset can still be wrong to
publish over an already-current row. For the sparse predecessor-only markers, the capture has only
the replacement hash, not the exact pre-write VDP row or a per-cell arcade ring oracle. Therefore it
cannot distinguish a wrong previous-revolution pointer from an insufficient retained-row model at
cell granularity. No new trace is required to correct the confirmed current-row overwrite; that
missing field matters only if predecessor-only corruption remains afterward.

## Minimal recommended correction

Preserve the semantic cut: arcade semantic decision to publish a row -> native Plane A row, and
remove the chip-specific tail. Correct only the no-publication contract:

1. Do not blanket-copy a predecessor row when the target physical row is already the exact retained
   resident row. In particular, selector-1/2 progress must distinguish rows already published for
   the current record from rows still retained from the completed record.
2. Ensure scene/record initialization materializes the exact 32 native resident rows, and have every
   ordinary full-row publication update that same final native resident buffer. A semantic
   no-publication step should then preserve it and change only scroll/visibility, matching arcade.
3. If initialization cannot yet guarantee all 32 rows, use explicit per-physical-row generation
   validity and materialize only a missing row. Do not infer the whole ring generation solely from
   `(current selector, completed selector, record)`.

The smallest first implementation test is the confirmed sequence: current record-17 L44-L46 must
retain their ordinary hashes across the later pan-down crossing. Then repeat L12-L14 and record-21
L60-L62/L35-L42. Preserve all Build 0528 improvements and do not change movement, collision,
palettes, audio, sprites, checkpoints, or offline row assets to mask the fault.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0059`
