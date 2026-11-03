# Cody Direct FUR Generation Report

## 1. Executive Summary
Implemented a direct automated VGM-to-Furnace generation pipeline using extracted YM2151 events and local Furnace serializer logic from the `vgm2fur` source tree. Generated 9 source-specific `.fur` modules, plus per-track extracted event artifacts and validation reports.

## 2. Available Evidence for `.fur` Generation
- Inventory report: `audio/rastan_music_dump/conversion_attempts/fur_generation_inventory.md`
- Local serializer source: `audio/rastan_music_dump/tools/vgm2fur/vgm2fur/furnace/module.py`
- Local instrument serialization source: `audio/rastan_music_dump/tools/vgm2fur/vgm2fur/furnace/instruments.py`
- Existing `.fur` artifacts used for structural comparison: `audio/rastan_music_dump/converted_fur/*.fur`

## 3. Minimum `.fur` Structure Findings
- Minimum structure report: `audio/rastan_music_dump/conversion_attempts/fur_minimum_structure_report.md`
- Required elements validated in generated outputs: zlib container, Furnace signature, INFO chunk, PATN chunks, INS2 instruments, ADIR directories.

## 4. VGM Event Extraction Results
- Extracted event artifacts directory: `audio/rastan_music_dump/conversion_attempts/extracted_events/`
- Per-track artifacts: JSON interval list, CSV interval table, CSV YM2151 register-write timeline.
- Interval counts ranged from 2 to 1720 depending on track.

## 5. `.fur` Generation Method
1. Parse each `.vgm` command stream and track YM2151 keycode/key-on behavior.
2. Convert note intervals to row positions using 735 samples/row (60 Hz).
3. Map YM2151 channels to Furnace channels (`fm1`..`fm6`, `psg1`, `psg2`).
4. Add placeholder instruments (FM + PSG).
5. Build module via local Furnace serializer (`furnace.Module.build()`).

## 6. Produced `.fur` Artifacts
- Output directory: `audio/rastan_music_dump/generated_fur/`
- Files generated: 9
  - `audio/rastan_music_dump/generated_fur/01 - Credit.fur` (size 339, hash `ea1d1cef5671f9307679bf87b32653136c42ce4c72425c3ef2f70c80d9134167`)
  - `audio/rastan_music_dump/generated_fur/02 - Broken The Promises (Opening).fur` (size 794, hash `71385e9c4a7215be3368417e231f8c9ba1f9b96e10b6a6263a2f8f5c95fcf8e6`)
  - `audio/rastan_music_dump/generated_fur/03 - Aggressive World (Scene 1).fur` (size 3358, hash `acb6603cc54a55473a908f0f57fb521352d4063d4f11f6a6da8620734d341dce`)
  - `audio/rastan_music_dump/generated_fur/04 - Bad Bible (Name Regist).fur` (size 545, hash `07849d7cd361626c6749353c1f72dd8ba8384a9da30c04cb07caa75fcad0bbbb`)
  - `audio/rastan_music_dump/generated_fur/05 - Re-In-Carnation (Scene 2).fur` (size 5514, hash `5b2813c6ad8f006edfbd4f196bdcafdbeff2a0f5124bb103e86d5b3b173b536e`)
  - `audio/rastan_music_dump/generated_fur/06 - The Devil Boss Carnival (Scene 3 Boss).fur` (size 2076, hash `f46be97c8c63a3a40df6b1d28f2bea541c8923cfe665cbc17f77a567f5a43500`)
  - `audio/rastan_music_dump/generated_fur/07 - Scene Clear.fur` (size 888, hash `d9236471060ffc5dcee780120eb2dbb111e7843377b835373383800e7ce1dc1c`)
  - `audio/rastan_music_dump/generated_fur/08 - Final Destroy (Scene 3 Round 6 Boss).fur` (size 4953, hash `bbcb8a5e822a03941787bb7ec0683b3398953ce05cbba15cdd70415c82d1991d`)
  - `audio/rastan_music_dump/generated_fur/09 - The Man Of Saga (Ending).fur` (size 3789, hash `58288618a596e5bae910dd86b4d0f2b45a70be0ad444114c6f85425da3cf44e8`)

## 7. Validation Results
- Validation report: `audio/rastan_music_dump/conversion_attempts/generated_fur_validation_report.md`
- Exists + non-empty: 9 / 9
- Zlib + Furnace signature checks: 9 / 9
- PATN present: 9 / 9
- Source differentiation (unique hashes): 9

## 8. Per-Track Success / Failure
| Track | Source VGM | Events JSON | Generated FUR | Status | Reason |
| --- | --- | --- | --- | --- | --- |
| 01 - Credit | audio/rastan_music_dump/converted_vgm/01 - Credit.vgm | audio/rastan_music_dump/conversion_attempts/extracted_events/01 - Credit_events.json | audio/rastan_music_dump/generated_fur/01 - Credit.fur | SUCCESS | Module generated and passed structural sanity checks |
| 02 - Broken The Promises (Opening) | audio/rastan_music_dump/converted_vgm/02 - Broken The Promises (Opening).vgm | audio/rastan_music_dump/conversion_attempts/extracted_events/02 - Broken The Promises (Opening)_events.json | audio/rastan_music_dump/generated_fur/02 - Broken The Promises (Opening).fur | SUCCESS | Module generated and passed structural sanity checks |
| 03 - Aggressive World (Scene 1) | audio/rastan_music_dump/converted_vgm/03 - Aggressive World (Scene 1).vgm | audio/rastan_music_dump/conversion_attempts/extracted_events/03 - Aggressive World (Scene 1)_events.json | audio/rastan_music_dump/generated_fur/03 - Aggressive World (Scene 1).fur | SUCCESS | Module generated and passed structural sanity checks |
| 04 - Bad Bible (Name Regist) | audio/rastan_music_dump/converted_vgm/04 - Bad Bible (Name Regist).vgm | audio/rastan_music_dump/conversion_attempts/extracted_events/04 - Bad Bible (Name Regist)_events.json | audio/rastan_music_dump/generated_fur/04 - Bad Bible (Name Regist).fur | SUCCESS | Module generated and passed structural sanity checks |
| 05 - Re-In-Carnation (Scene 2) | audio/rastan_music_dump/converted_vgm/05 - Re-In-Carnation (Scene 2).vgm | audio/rastan_music_dump/conversion_attempts/extracted_events/05 - Re-In-Carnation (Scene 2)_events.json | audio/rastan_music_dump/generated_fur/05 - Re-In-Carnation (Scene 2).fur | SUCCESS | Module generated and passed structural sanity checks |
| 06 - The Devil Boss Carnival (Scene 3 Boss) | audio/rastan_music_dump/converted_vgm/06 - The Devil Boss Carnival (Scene 3 Boss).vgm | audio/rastan_music_dump/conversion_attempts/extracted_events/06 - The Devil Boss Carnival (Scene 3 Boss)_events.json | audio/rastan_music_dump/generated_fur/06 - The Devil Boss Carnival (Scene 3 Boss).fur | SUCCESS | Module generated and passed structural sanity checks |
| 07 - Scene Clear | audio/rastan_music_dump/converted_vgm/07 - Scene Clear.vgm | audio/rastan_music_dump/conversion_attempts/extracted_events/07 - Scene Clear_events.json | audio/rastan_music_dump/generated_fur/07 - Scene Clear.fur | SUCCESS | Module generated and passed structural sanity checks |
| 08 - Final Destroy (Scene 3 Round 6 Boss) | audio/rastan_music_dump/converted_vgm/08 - Final Destroy (Scene 3 Round 6 Boss).vgm | audio/rastan_music_dump/conversion_attempts/extracted_events/08 - Final Destroy (Scene 3 Round 6 Boss)_events.json | audio/rastan_music_dump/generated_fur/08 - Final Destroy (Scene 3 Round 6 Boss).fur | SUCCESS | Module generated and passed structural sanity checks |
| 09 - The Man Of Saga (Ending) | audio/rastan_music_dump/converted_vgm/09 - The Man Of Saga (Ending).vgm | audio/rastan_music_dump/conversion_attempts/extracted_events/09 - The Man Of Saga (Ending)_events.json | audio/rastan_music_dump/generated_fur/09 - The Man Of Saga (Ending).fur | SUCCESS | Module generated and passed structural sanity checks |

## 9. Exact Blockers
- No local Furnace headless CLI/binary was available to perform direct open/load verification in this environment.
- Structural file validation was used as the highest practical non-interactive validation method.

## 10. Single Final Status
PARTIAL_SUCCESS

## 11. Final Verdict
Direct automated `.fur` generation from Rastan `.vgm` dumps was implemented and produced source-specific, structurally plausible Furnace modules plus machine-readable event extraction artifacts for all tracks.
