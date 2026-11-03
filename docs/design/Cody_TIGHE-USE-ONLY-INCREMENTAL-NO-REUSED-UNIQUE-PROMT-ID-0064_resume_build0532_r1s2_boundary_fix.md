# Build 0532 R1-S2 partial-record boundary correction — resumed result

Date: 2026-11-03

Assignment: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0064`

Historical assignment resumed: PROMT-ID-0063 (consumed; not reused)

Candidate: Build 0532, pending Tighe's gameplay acceptance

## Resume state

PROMT-ID-0063 had already established the arcade ordering, corrected production source, added the
first deterministic oracle, committed source as
`566e9c63e5254be6179a0948a34958c20959c68c`, and started Build 0532. The resumed process found the
Makefile run completed successfully: counter/ledger 0532, seven configured family members present,
canonical/gameplay-entry/Round-1 epoch/mandatory Genesis NTSC trace gates complete. It did not
rebuild or consume 0533.

The Build 0532 artifacts were written at 10:47–10:48, before later concurrent PROMT-ID-0069 commits.
Their ROM-producing tracked source is exactly `566e9c63e5254be6179a0948a34958c20959c68c`.

## Semantic cut

The preserved cut is:

`retained arcade publish/preserve decision -> final Genesis Plane-A resident words`

The retired tail remains PC080SN C08000/name-RAM row walking and writes below the retained semantic
producers. `staged_fg_buffer` remains the sole 64x32 final-native Plane-A image. The correction adds
no 64-row shadow, backing map, PC080SN emulation, graphics duplicate, coordinate exception, or
jump-specific behavior.

## Defect A — record 16 to 17

### Observed

With only the required first three chain jumps, Tighe saw one wrong 8-pixel row: lower-record window
graphics remained where the top brick row should be. The surrounding record-17 projection was
correct.

### Proven first divergence

Original `$055948` invokes the row producer using the old `A5+0x10CA/0x10CC` strip/group cursor,
increments `0x10CA`, and only then performs the group/record rollover. The stored front is therefore
the **next row to author**, not the last row authored.

At selector-1 front 0:

- requested logical row: 63;
- Genesis physical row: 31 (`63 & 31`);
- correct owner/source: completed record 16, selector 0;
- expected contents: generated/original record-16 logical row 63 (top brick row);
- Build 0531 actual selection: incoming record-17 selector-1 pan row 63;
- incorrect decision: the inclusive `logical >= 63-front` current-record test;
- producer responsible for correction: `.Lplane_a_publish_logical_row_native` no-publication alias
  materializer.

The generated record-16 row and record-17 row differ, so the oracle is discriminating. This is one
row because Build 0531 expanded the current-owned range by exactly one row at the live front.

### Correction

`apps/rastan-direct/src/tilemap_hooks.s:1460-1490` now treats the cursor as next-to-author:

- selector 1 current-owned range: `[64-front, 63]`, empty at front 0;
- selector 2 current-owned range: `[0, front-1]`, empty at front 0.

The boundary row remains predecessor-owned until ordinary `$055A14` publication actually authors
it. Immediately afterward, the first authored row selects the current immutable pan-row asset.

## Defect B — record 21

### Observed

Tighe reproduced the larger corruption around the bottom of record 21 with both minimal and
aggressive jumping. Jump cadence is therefore not a primary renderer cause.

### Proven

Record 21 uses the same selector-1 producer, next-to-author cursor, alias materializer, and erroneous
Build-0531 inclusive boundary condition. At front 0 the equivalent first boundary is logical 63 /
physical 31: retained record 20 is correct, while Build 0531 could prematurely select record-21 pan
row 63. For every later front, the one invalid row is `63-front`. Generated record-20 and record-21
rows differ at all 64 tested boundaries. Repeated N/N+32 reuse and reversal can therefore install
several independently wrong record-21 boundary rows over time; it is not one bad row expanding by
copy.

The deterministic regression exercises all 64 record-20/21 partial fronts, both logical aliases,
three repeated crossings, immediate reversal, the predecessor boundary row, and the adjacent first
current-authored row using the actual production native/pan assets.

### Not proven from existing captures

The existing Build-0529/0530/0531 evidence does not contain a Build-0531 first-bad-write capture at
record 21. It therefore proves that the same defect exists and can accumulate there, but not that
every pixel in Tighe's larger record-21 screenshot has no second cause. Disposition:
**PARTIALLY explained by the same root cause; Build 0532 corrects the proven mechanism.** Tighe's
minimal/aggressive Build-0532 run will determine whether another record-21 defect remains. No new
trace is requested before that direct gameplay check.

## Build-0531 improvement preserved

At captured front 21, exclusive selector-1 ownership is rows 43–63. Previously proven current rows
44–46 therefore remain current-record 17 rows. Their aliases 12–14 remain predecessor-owned. The
correction changes only boundary row 42 at that front and does not undo Build 0530 provenance or
Build 0531's genuine current-row rematerialization.

## Deterministic verification

`tools/translation/verify_bg_a_incremental_background.py:388-549` verifies:

- all 64 selector-1 and selector-2 fronts and all 64 logical rows;
- front 0 logical 63 / physical 31 predecessor retention for records 16/17 and 20/21;
- actual 64-word `record_native_maps.bin` predecessor rows against actual `pan_row_maps.bin`
  current rows;
- the first legitimately authored current row with no extra predecessor retention;
- Build-0531-protected record-17 rows 44–46 at front 21;
- N/N+32 alias materialization, both traversal directions, immediate reversal, and three repeated
  crossings per boundary;
- record-21 boundary behavior across all fronts.

The expanded verifier passes. Follow-up regression-only commit:
`54591d124c2a017f0b4099dbedf5a3e9516151c3`. This commit postdates the ROM and changes no production
assembly; the ROM-producing source remains `566e9c63`.

## Automated validation

Build 0532 passed:

- 68000 assembly;
- full-span Plane-A coherence and the updated deterministic boundary oracle;
- selector-0 and selector-1/2 runtime equivalence;
- scene/checkpoint/pan/native-map and predecessor coverage;
- collision/visual separation;
- boot guard and canonical `GATE_PASS`;
- gameplay-entry gate (`build0532_gameplay_entry_gate_20261103_104721`);
- all Round-1 epoch/package cases (`build0532_phase1_epoch_gate_20261103_104724`);
- mandatory 30-second Genesis NTSC trace
  (`rastan_direct_video_test_build_0532_mame_30s_20261103_104733`);
- complete configured seven-ROM family;
- normal and invincible R1-S2 functional starts at frame 412, stage `$0010`, record `$0011`,
  package 5, 2048 nonzero words on both planes, and zero Plane-A/Plane-B map misses.

These results verify the implementation and startup contracts; they do not constitute gameplay
acceptance.

## Candidate artifacts

All files are 3,792,568 bytes.

| Artifact | SHA-256 |
|---|---|
| `dist/rastan-direct/rastan_direct_video_test_build_0532.bin` | `1682b5409010e4da850d8bc24ebac2877253e5ee8ad5d3e043df36b4fafd6838` |
| `dist/rastan-direct/rastan_direct_video_test_build_0532_d.bin` | `9fcd56e4e02afc77f0a9bd97424b3fd70d0d57836879fe861a908670c0da71ed` |
| `dist/rastan-direct/rastan_direct_video_test_build_0532_s.bin` | `37f64e546ffe8203a57cd8061eebf36d75dababfdd8c95f7f73d22da619364aa` |
| `dist/rastan-direct/rastan_direct_video_test_build_0532_do.bin` | `eb320c22d36811d2030f1dc793d57c66cd850da8f31d0b90de2bdff90b63eec5` |
| `dist/rastan-direct/rastan_direct_video_test_build_0532_c.bin` | `372ce5de2b7ba191cc2aa89e268fcff2e16ea3cb26aff7929b3b9eb332c674bf` |
| `dist/rastan-direct/rastan_direct_video_test_build_0532_full_hud.bin` | `a27d92c3b6f535dc608ab76745498ed22899cb1e697f145b2350172bf9ce7c3a` |
| `dist/rastan-direct/rastan_direct_video_test_build_0532_invincible.bin` | `7316d9e213aad42948b041bf5f2e1426992377ce944ae9aadbf89876063d13fe` |
| `dist/rastan-direct/rastan_direct_video_test_build_0532_S1-2.bin` | `536ebf66d537804e2330e302681a1acf20307aa6fb7d574d606554be1523fae6` |
| `dist/rastan-direct/rastan_direct_video_test_build_0532_invincible_S1-2.bin` | `adf3eb18b633f547e21b129ad026c59862a7f921734db9155fe2294c57917879` |

## Tighe gameplay check

Use `dist/rastan-direct/rastan_direct_video_test_build_0532_invincible_S1-2.bin`.

1. Minimal first-three-chain jumps: confirm the single wrong row at 16→17 is replaced by the top
   brick row and surrounding record-17 rows remain correct.
2. Reach record 21 with minimal jumping and inspect its bottom/upward scroll region.
3. Repeat aggressive jump-assisted ascent plus reversals; confirm the earlier Build-0531 route stays
   fixed and report whether any record-21 corruption remains.

Build 0532 is a candidate, not accepted.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0064`
