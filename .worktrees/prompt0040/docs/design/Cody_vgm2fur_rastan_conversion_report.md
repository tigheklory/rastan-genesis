# Cody vgm2fur Rastan Conversion Report

## 1. Executive Summary
Executed a full automated VGZ/VGM-to-Furnace conversion attempt using `std282/vgm2fur` on all Rastan dumps. Tool acquisition and execution succeeded, `.fur` files were emitted for all sources, but artifact validation found all primary outputs were byte-identical across all tracks, so no source-specific valid conversions were produced.

## 2. Source Dump Inventory
- Source directory: `audio/rastan_music_dump`
- Source `.vgz` count: 9
- Inventory manifest: `audio/rastan_music_dump/manifest_for_fur_conversion.md`

## 3. VGZ -> VGM Decompression Results
- Output directory: `audio/rastan_music_dump/converted_vgm/`
- VGM files generated: 9 / 9
- Decompression status file: `audio/rastan_music_dump/conversion_attempts/fur_decompression_status.tsv`

## 4. `vgm2fur` Acquisition / Build Results
- Repository cloned: `audio/rastan_music_dump/tools/vgm2fur`
- Runtime check: `python3 -m vgm2fur --help` succeeded
- Build system requirement from repo: Python package (`pyproject.toml`), no native compile step required
- Commands used:
  - `git -C audio/rastan_music_dump/tools clone https://github.com/std282/vgm2fur.git`
  - `cd audio/rastan_music_dump/tools/vgm2fur && python3 -m vgm2fur --help`
  - `python3 -m vgm2fur <input.vgm> -o <output.fur>`
  - `python3 -m vgm2fur <input.vgm> -o <output.fur> --pattern-length=256 --row-duration=735 --playback-rate=60 --no-latch`
- Help output log: `audio/rastan_music_dump/conversion_attempts/vgm2fur_help.log`

## 5. Conversion Attempt Results
| Source VGZ | Source VGM | Output FUR | Status | Failure Step |
| --- | --- | --- | --- | --- |
| audio/rastan_music_dump/01 - Credit.vgz | audio/rastan_music_dump/converted_vgm/01 - Credit.vgm | audio/rastan_music_dump/converted_fur/01 - Credit.fur | FAILED | validation |
| audio/rastan_music_dump/02 - Broken The Promises (Opening).vgz | audio/rastan_music_dump/converted_vgm/02 - Broken The Promises (Opening).vgm | audio/rastan_music_dump/converted_fur/02 - Broken The Promises (Opening).fur | FAILED | validation |
| audio/rastan_music_dump/03 - Aggressive World (Scene 1).vgz | audio/rastan_music_dump/converted_vgm/03 - Aggressive World (Scene 1).vgm | audio/rastan_music_dump/converted_fur/03 - Aggressive World (Scene 1).fur | FAILED | validation |
| audio/rastan_music_dump/04 - Bad Bible (Name Regist).vgz | audio/rastan_music_dump/converted_vgm/04 - Bad Bible (Name Regist).vgm | audio/rastan_music_dump/converted_fur/04 - Bad Bible (Name Regist).fur | FAILED | validation |
| audio/rastan_music_dump/05 - Re-In-Carnation (Scene 2).vgz | audio/rastan_music_dump/converted_vgm/05 - Re-In-Carnation (Scene 2).vgm | audio/rastan_music_dump/converted_fur/05 - Re-In-Carnation (Scene 2).fur | FAILED | validation |
| audio/rastan_music_dump/06 - The Devil Boss Carnival (Scene 3 Boss).vgz | audio/rastan_music_dump/converted_vgm/06 - The Devil Boss Carnival (Scene 3 Boss).vgm | audio/rastan_music_dump/converted_fur/06 - The Devil Boss Carnival (Scene 3 Boss).fur | FAILED | validation |
| audio/rastan_music_dump/07 - Scene Clear.vgz | audio/rastan_music_dump/converted_vgm/07 - Scene Clear.vgm | audio/rastan_music_dump/converted_fur/07 - Scene Clear.fur | FAILED | validation |
| audio/rastan_music_dump/08 - Final Destroy (Scene 3 Round 6 Boss).vgz | audio/rastan_music_dump/converted_vgm/08 - Final Destroy (Scene 3 Round 6 Boss).vgm | audio/rastan_music_dump/converted_fur/08 - Final Destroy (Scene 3 Round 6 Boss).fur | FAILED | validation |
| audio/rastan_music_dump/09 - The Man Of Saga (Ending).vgz | audio/rastan_music_dump/converted_vgm/09 - The Man Of Saga (Ending).vgm | audio/rastan_music_dump/converted_fur/09 - The Man Of Saga (Ending).fur | FAILED | validation |

## 6. Produced `.fur` Artifacts
- Output directory: `audio/rastan_music_dump/converted_fur/`
- `.fur` files emitted by primary pass: 9
- Primary-pass output hash equality: ALL IDENTICAL (`cc69c098b94b4029ba0ec8dc5baac924fd094073274972f5a75a07c559d39b34`)
- Retry-with-options artifacts were also generated for adaptation testing (`*__retry_opts.fur`).

## 7. Validation of Produced `.fur` Files
Validation checks performed per file:
- file exists
- file size > 0
- zlib decompression succeeds
- decompressed stream contains `-Furnace module-` signature
- source-specificity check (hash diversity across different songs)

Validation outcome:
- Structural sanity checks passed for emitted files: 9 / 9
- Source-specificity check passed: NO
- Valid `.fur` conversions accepted: 0 / 9

## 8. Exact Per-File Failures / Blockers
- `01 - Credit.vgz` -> FAILED at `validation`: converter emitted source-identical output for all tracks (common sha256 cc69c098b94b4029ba0ec8dc5baac924fd094073274972f5a75a07c559d39b34); modules are not source-specific conversions (log: `audio/rastan_music_dump/conversion_attempts/vgm2fur_logs/01 - Credit__attempt1_vgm.log`)
- `02 - Broken The Promises (Opening).vgz` -> FAILED at `validation`: converter emitted source-identical output for all tracks (common sha256 cc69c098b94b4029ba0ec8dc5baac924fd094073274972f5a75a07c559d39b34); modules are not source-specific conversions (log: `audio/rastan_music_dump/conversion_attempts/vgm2fur_logs/02 - Broken The Promises (Opening)__attempt1_vgm.log`)
- `03 - Aggressive World (Scene 1).vgz` -> FAILED at `validation`: converter emitted source-identical output for all tracks (common sha256 cc69c098b94b4029ba0ec8dc5baac924fd094073274972f5a75a07c559d39b34); modules are not source-specific conversions (log: `audio/rastan_music_dump/conversion_attempts/vgm2fur_logs/03 - Aggressive World (Scene 1)__attempt1_vgm.log`)
- `04 - Bad Bible (Name Regist).vgz` -> FAILED at `validation`: converter emitted source-identical output for all tracks (common sha256 cc69c098b94b4029ba0ec8dc5baac924fd094073274972f5a75a07c559d39b34); modules are not source-specific conversions (log: `audio/rastan_music_dump/conversion_attempts/vgm2fur_logs/04 - Bad Bible (Name Regist)__attempt1_vgm.log`)
- `05 - Re-In-Carnation (Scene 2).vgz` -> FAILED at `validation`: converter emitted source-identical output for all tracks (common sha256 cc69c098b94b4029ba0ec8dc5baac924fd094073274972f5a75a07c559d39b34); modules are not source-specific conversions (log: `audio/rastan_music_dump/conversion_attempts/vgm2fur_logs/05 - Re-In-Carnation (Scene 2)__attempt1_vgm.log`)
- `06 - The Devil Boss Carnival (Scene 3 Boss).vgz` -> FAILED at `validation`: converter emitted source-identical output for all tracks (common sha256 cc69c098b94b4029ba0ec8dc5baac924fd094073274972f5a75a07c559d39b34); modules are not source-specific conversions (log: `audio/rastan_music_dump/conversion_attempts/vgm2fur_logs/06 - The Devil Boss Carnival (Scene 3 Boss)__attempt1_vgm.log`)
- `07 - Scene Clear.vgz` -> FAILED at `validation`: converter emitted source-identical output for all tracks (common sha256 cc69c098b94b4029ba0ec8dc5baac924fd094073274972f5a75a07c559d39b34); modules are not source-specific conversions (log: `audio/rastan_music_dump/conversion_attempts/vgm2fur_logs/07 - Scene Clear__attempt1_vgm.log`)
- `08 - Final Destroy (Scene 3 Round 6 Boss).vgz` -> FAILED at `validation`: converter emitted source-identical output for all tracks (common sha256 cc69c098b94b4029ba0ec8dc5baac924fd094073274972f5a75a07c559d39b34); modules are not source-specific conversions (log: `audio/rastan_music_dump/conversion_attempts/vgm2fur_logs/08 - Final Destroy (Scene 3 Round 6 Boss)__attempt1_vgm.log`)
- `09 - The Man Of Saga (Ending).vgz` -> FAILED at `validation`: converter emitted source-identical output for all tracks (common sha256 cc69c098b94b4029ba0ec8dc5baac924fd094073274972f5a75a07c559d39b34); modules are not source-specific conversions (log: `audio/rastan_music_dump/conversion_attempts/vgm2fur_logs/09 - The Man Of Saga (Ending)__attempt1_vgm.log`)

## 9. Single Final Status
FAILED_TO_PRODUCE_SOURCE_SPECIFIC_VALID_FUR

## 10. Final Verdict
`vgm2fur` runs and emits structurally plausible `.fur` containers, but all primary outputs are source-identical and therefore not valid track conversions for the Rastan dump set.
