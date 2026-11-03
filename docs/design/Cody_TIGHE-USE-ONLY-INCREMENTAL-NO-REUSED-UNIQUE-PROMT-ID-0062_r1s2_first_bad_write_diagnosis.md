# R1-S2 first-bad-write diagnosis and Build 0531 correction

Date: 2026-11-03

Agent: Cody

Assignment: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0062`

Baseline: Build 0530, unaccepted candidate

Corrected candidate: Build 0531, pending Tighe's gameplay acceptance

## Result

The paired manual traces prove the remaining Build 0530 defect. This was not an incorrect offline
row, incomplete DMA, skipped row, collision error, or jump-specific renderer. It was a source-
selection error during a genuine N/N+32 physical-row rematerialization.

Record 17 selector 1 had already authored logical rows 44-46 correctly. Reverse movement then
legitimately reused their shared 32-row physical slots for logical rows 12-14. When rows 46, 45,
and 44 entered again, Build 0530 correctly recognized that materialization was necessary, but
selected the completed selector-0 predecessor for all three rows. At the captured live front these
rows were already owned by the partially authored current selector-1 record. The first wrong store
was therefore deterministic; aggressive jump-climbing merely reached the reversal sequence more
readily.

Build 0531 corrects that decision without adding a map, buffer, hardware emulation layer, or
coordinate exception. It derives the current-authored row range from the existing selector and
strip/group front and selects the current record's existing immutable pan-row asset only for rows
inside that range. Rows not yet authored still use the completed predecessor path. Build 0530's
exact-owner preservation remains intact.

## Capture evidence

The completed captures are:

- Genesis Build 0530 invincible R1-S2:
  `states/traces/r1s2_first_bad_write_build_0530/genesis_20261103_150809/`;
- original arcade:
  `states/traces/r1s2_first_bad_write_build_0530/arcade_20261103_150902/`.

The Genesis trace contains 2,639 frames and 92 materialization chunks. Tighe marked the visible
failure at frame 2405. The arcade trace contains 2,979 frames; its marker is frame 2855. Both
captures reached record 17, selector 1. The arcade start used the established MAME stage-start
cheat; the installed `rastan.xml` writes the correct original main-CPU selector byte at `$05FF9F`.

### First incorrect Genesis write

The first incorrect store is the record-17 selector-1 rematerialization of logical row 46 into
physical row 14 at frame 2291:

- prior physical owner: logical row 14;
- requested owner: logical row 46;
- relationship: genuine N-32 alias, so suppressing the write would be wrong;
- selected branch: `SOURCE_PREVIOUS_SELECTOR0`;
- first cell expected native word: `$62EB`;
- first cell written: `$63F8`;
- materializer store PC reported by the write tap: `$07101A` (the preceding branch PC is
  `$071018` in Build 0530);
- correct record-17 row hash: `3958DFD0`;
- wrong final row hash: `5295BB26`;
- differing cells: 38 of 64.

The same error follows for row 45 at frame 2299 and row 44 at frame 2307:

| Logical / physical row | Correct record-17 hash | Wrong predecessor hash | Different cells |
|---|---:|---:|---:|
| 46 / 14 | `3958DFD0` | `5295BB26` | 38 |
| 45 / 13 | `D7B9883D` | `19008D79` | 38 |
| 44 / 12 | `164F1787` | `65F3431C` | 38 |

No later writer replaces these rows before the marker. At frame 2405 the visible top is logical
row 37, so rows 44-46 are on screen and carry the corruption Tighe marked.

### Complete ownership sequence

The trace establishes the row history rather than inferring it from the final screenshot:

1. Ordinary selector-1 publication authored current record-17 rows 46, 45, and 44 at frames
   1989, 1993, and 1996 and installed their logical-owner tags.
2. Reverse motion legitimately materialized logical aliases 14, 13, and 12 into physical rows
   14, 13, and 12 at frames 2087-2088, 2084-2085, and 2081-2082.
3. On the return, rows 46, 45, and 44 genuinely required new materialization.
4. Build 0530 treated current selector 1 plus completed selector 0 as globally predecessor-owned
   and rebuilt all three from selector 0.

This proves that a 32-byte physical-owner vector is necessary but not alone sufficient: after an
alias has reused a physical row, the requested logical row's source must also respect partial
current-record progress.

## Arcade and generated-row oracle

The original arcade `$055704/$055790` events perform no C08000 name-RAM write. Its retained row at
the equivalent record-17 selector-1 state is therefore the current selector-1 row.

The arcade marker's 16 KiB C08000 image and `marker_rows.tsv` were decoded with the established
PC080SN compiler/audit logic. For logical rows 44, 45, and 46:

- `reconstruct_segment(... record=17, selector=1)` matches the actual arcade marker row at all
  64 cells, with zero attribute or tile differences;
- `build/pc080sn_boundary/pan_row_maps.bin` record 17 matches the same converted native rows;
- the correct pre-materialization Genesis rows match those compiled record-17 rows exactly.

There is therefore no evidence that Python-generated rows are wrong. The offline assets, original
arcade resident contents, and the correctly authored Genesis rows all agree. Only runtime record
selection was wrong.

## Source correction

The semantic cut remains:

`retained arcade publish/preserve decision -> final Genesis Plane-A name words`

The retired tail remains PC080SN C08000 name-RAM authoring. `staged_fg_buffer` is still the sole
native 64x32 Plane-A image and `plane_a_resident_logical_rows` remains minimal per-physical-row
identity metadata.

The correction is in `apps/rastan-direct/src/tilemap_hooks.s:1458-1528` inside
`.Lplane_a_publish_logical_row_native`:

- compute `front = ((group & 15) * 4) + (strip & 3)` from existing retained state;
- selector 1 has currently authored `[63-front, 63]`;
- selector 2 has currently authored `[0, front]`;
- on a genuine alias miss inside that range, use the current record's precompiled pan row;
- otherwise preserve the existing completed-predecessor selection, including selector-0 previous-
  revolution reconstruction and selector-1/2 `record-1` assets.

At the captured front 21, selector 1 has authored rows 42-63. Rows 44-46 therefore select current
record 17, while rows 12-14 remain predecessor-owned. The rule is general and contains no stage,
record, row, screen-position, or graphical-feature hardcoding.

Source and verifier commit:

`244d219ff8fead00fdc84920be5ecdb89db00a45`

## Verification

`verify_bg_a_incremental_background.py` now checks:

- every selector-1 and selector-2 front from 0 through 63;
- all 64 logical rows at each front;
- current-versus-completed boundary selection in both directions;
- the exact captured record-17 sequence: current rows 46/45/44, alias reuse by 14/13/12, then
  current-record rematerialization;
- the existing exact-owner retention and genuine predecessor alias cases.

Build 0531 passed:

- assembly and full-span Plane-A coherence gates;
- selector-0 and selector-1/2 equivalence gates;
- scene-fill, pan-row, and predecessor-row asset checks;
- canonical `GATE_PASS`;
- gameplay-entry and Round-1 epoch/package gates;
- mandatory 30-second Genesis NTSC MAME trace;
- complete numbered variant-family verification;
- normal and invincible R1-S2 functional starts at frame 412 with stage `$0010`, record `$0011`,
  package 5, full Plane A/B population, and zero map misses.

These tests establish the source correction and normal initialization. They do not replace Tighe's
acceptance run using conventional and aggressive jump-assisted chain climbing.

## Build 0531 artifacts

All three requested artifacts are 3,792,568 bytes:

| Artifact | SHA-256 |
|---|---|
| `dist/rastan-direct/rastan_direct_video_test_build_0531.bin` | `d0161ef288d67d73b54bd9afc50a6d5adf0aace5676d9158a085decde0a3d568` |
| `dist/rastan-direct/rastan_direct_video_test_build_0531_S1-2.bin` | `ca6985bf52f2af3534d9647debe594ccf1d0a54ef50f8046a215d41d7531e953` |
| `dist/rastan-direct/rastan_direct_video_test_build_0531_invincible_S1-2.bin` | `9264ea27e548f40851beb5c3de434bbf7b37bc6bcc6648e4097d26ac4d3da2e7` |

The Makefile-owned counter and consumed ledger advanced from 0530 to 0531. Build 0531 is a test
candidate, not an accepted baseline.

## Remaining acceptance work

Tighe should use the invincible R1-S2 derivative to repeat the exact aggressive chain route that
corrupted Build 0530, including rapid jump-assisted ascent and direction reversals. Also verify one
ordinary climb. Report the first visible mismatch if any. Collision, traversal, Plane B, sprites,
palettes, audio, and checkpoints were not intentionally changed.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0062`
