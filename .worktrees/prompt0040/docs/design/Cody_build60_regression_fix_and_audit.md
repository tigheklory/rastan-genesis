# Cody Build 60 Regression Fix and Audit

## Scope

This task implements the Build 60 regression fix identified in `docs/design/Cody_build60_regression_forensics.md` and performs an `.incbin` dependency audit for other assembly objects.

- Fix target: `apps/rastan-direct/Makefile` dependency rule for `scene_load.o`
- Build target: `dist/rastan-direct/rastan_direct_video_test_build_0061.bin`
- No LUT/preload regeneration tool run in this task
- No source edits outside Makefile

## Root Cause (from forensics)

Build 60 linked a stale `apps/rastan-direct/out/scene_load.o`. `scene_load.s` uses `.incbin` for generated artifacts, but `scene_load.o` depended only on `scene_load.s` itself, so Make did not reassemble when embedded blob inputs changed.

## Makefile Fix Applied

Updated `scene_load.o` rule to include all `.incbin` inputs from `scene_load.s`:

- `$(ROOT)/build/pc080sn_tile_vram_lut.bin`
- `$(ROOT)/build/pc080sn_attr_lut.bin`
- `$(ROOT)/build/regions/pc080sn.bin`
- `$(ROOT)/build/pc080sn_scene_preload_title.bin`
- `$(ROOT)/build/pc080sn_scene_preload_gameplay.bin`
- `$(ROOT)/build/pc080sn_scene_preload_endround.bin`

Then removed stale object `apps/rastan-direct/out/scene_load.o` and rebuilt.

## `.incbin` Audit Findings (Phase 2)

Files using `.incbin` in `apps/rastan-direct/src/`:

1. `src/scene_load.s`
- `.incbin` inputs: six files listed above
- Previous dependency hole: YES (fixed in this task)
- Classification: **B** (mandatory fix). Evidence: stale object had been linked in Build 60 and embedded wrong LUT/preload bytes.

2. `src/pc090oj_assets.s`
- `.incbin` inputs:
  - `../../build/pc090oj_genesis.bin`
  - `../../build/pc090oj_slot_lut.bin`
- Makefile dependencies present: YES (`$(PC090OJ_PRECONV) $(PC090OJ_SLOT_LUT)`)
- Dependency hole: NO
- Classification: N/A

Result: no additional dependency holes found in `.s` files using `.incbin`.

## Build 61 Result

- Build artifact: `dist/rastan-direct/rastan_direct_video_test_build_0061.bin`
- ROM SHA256: `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`
- Build output reported: `numbered build artifact: ../../dist/rastan-direct/rastan_direct_video_test_build_0061.bin`

## Postpatcher Invariant Verification

- Build succeeded running `postpatch_startup_rom.py` with no invariant failure.
- Invariant check in source remains:
  - `total_genesis_bytes_covered == 0x17CAEC`
  - `opcode_replace patched_site count == 94`
  - file: `tools/translation/postpatch_startup_rom.py:1757-1763`
- Manifest count check confirms `"kind": "opcode_replace"` occurs **94** times in `build/rastan-direct/rastan_direct_patch_manifest.json`.

## Embedded Region Verification (Build 61)

Symbol-derived Build 61 offsets (`apps/rastan-direct/out/symbol.txt`):

- `genesistan_pc080sn_tile_vram_lut` at `0x0F1EC0`
- `genesistan_pc080sn_attr_lut` at `0x0F9EC0`
- `genesistan_scene_preload_title` at `0x179F00`
- `genesistan_scene_preload_gameplay` at `0x17AC26`
- `genesistan_scene_preload_endround` at `0x17B91C`
- `genesistan_pc080sn_tile_rom` at `0x0F9F00`

### Build 61 vs generated artifact SHAs

- LUT (`32768` bytes): `ca9c3dcf1aa3624c3660aa3b7443625433341941955c2c3f7c5956f44f5d3e92` (match)
- Attr LUT (`64` bytes): `2614c7b4c5ba7716fa6cc985f65ad2832c029956243d5570da52975d230fba3b` (match)
- Title preload (`3366` bytes): `e0a814f2638c638e2ec710a91bc88e2603af6ea95afbcd3fb34203c5002fe52f` (match)
- Gameplay preload (`3318` bytes): `462c428c771428682e1be618dd2b72c54136c49a665fe4b09e1f935d6a7cdb6c` (match)
- Endround preload (`4270` bytes): `690835b85f60451935a325db066a10139f946125b354c3f100412149ef730acc` (match)
- Tile ROM (`524288` bytes): `a33372eb4f768136cbb5311125e65da7587d31bb1d91a72d32775d22eb44059b` (match)

### Build 61 vs Build 59 baseline

Using expected helper-era offset adjustment (`Build 59 offset = Build 61 offset - 0x4`), all six embedded regions above hash-identical between `0059` and `0061`.

## Helper Preservation

- Symbol: `genesistan_diag_bookmark`
- Address: `0x00071C78`
- Bytes in Build 61 at `0x00071C78`: `60 FE`
- SHA256 over 2-byte helper sequence: `20825b3611f3c2bbcf2a401045fa74256f8b549d4d509834eb8d928861d9fecb` (canonical baseline, preserved)

## Outcome

The Build 60 regression mechanism (stale `scene_load.o` linkage) is resolved for Build 61 by explicit `.incbin` dependencies plus forced object rebuild. Build 61 embeds the same post-CLOSED-007 LUT/preload content as Build 59 and preserves the diagnostic helper.

## OPEN-010 Link

This task opens `OPEN-010` to track systematic `.incbin` dependency completeness and build determinism gate work before bookmark cycles resume.
