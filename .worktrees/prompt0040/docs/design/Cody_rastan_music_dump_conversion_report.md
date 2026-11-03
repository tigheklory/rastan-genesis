# Cody Rastan Music Dump Conversion Report

## 1. Executive Summary
Processed `audio/rastan_music_dump` end-to-end: inventoried source `.vgz`, decompressed all files to `.vgm`, validated headers/chips/loop metadata, and produced practical intermediate conversion artifacts as per-track event timelines and YM2151 register-write CSV dumps.

Results:
- Source files inventoried: 9
- `.vgz` decompressed to `.vgm`: 9/9
- Valid VGM files: 9/9
- YM2151 present in VGM header: 9/9
- Parsed command streams: 9/9 with zero parse errors
- Practical intermediate artifacts produced: YES (`events.csv`, `ym2151_writes.csv`, per-track JSON summaries)

## 2. Source File Inventory
Created:
- `audio/rastan_music_dump/manifest_before_conversion.md`

Inventory findings:
- All source files are `.vgz`
- All source files have gzip magic (`1F 8B`)
- Duplicate check by full SHA-256 hash found no duplicates

## 3. Decompression Results
Output directory created:
- `audio/rastan_music_dump/converted_vgm/`

Decompression result:
- 9 source `.vgz` files decompressed
- 9 output `.vgm` files created
- No decompression failures

Output files:
- `audio/rastan_music_dump/converted_vgm/01 - Credit.vgm`
- `audio/rastan_music_dump/converted_vgm/02 - Broken The Promises (Opening).vgm`
- `audio/rastan_music_dump/converted_vgm/03 - Aggressive World (Scene 1).vgm`
- `audio/rastan_music_dump/converted_vgm/04 - Bad Bible (Name Regist).vgm`
- `audio/rastan_music_dump/converted_vgm/05 - Re-In-Carnation (Scene 2).vgm`
- `audio/rastan_music_dump/converted_vgm/06 - The Devil Boss Carnival (Scene 3 Boss).vgm`
- `audio/rastan_music_dump/converted_vgm/07 - Scene Clear.vgm`
- `audio/rastan_music_dump/converted_vgm/08 - Final Destroy (Scene 3 Round 6 Boss).vgm`
- `audio/rastan_music_dump/converted_vgm/09 - The Man Of Saga (Ending).vgm`

## 4. VGM Validation Results
Created:
- `audio/rastan_music_dump/vgm_validation_report.md`

Validation summary:
- Valid VGM magic/header: 9/9
- YM2151 present in VGM header clocks: 9/9
- Loop present: 5/9 tracks
- Command-stream parse completed: 9/9, parse errors: 0
- Observed command-stream chip writes: YM2151 only (`0x54` commands) plus wait/end opcodes

## 5. Tool Availability
Tool availability was captured with exact command outputs.

Available locally:
- `gzip` (`/usr/bin/gzip`)
- `python3` (`/usr/bin/python3`)

Not available locally:
- `vgm2txt`
- `vgmtool`
- `vgm2fur`

Availability log:
- `audio/rastan_music_dump/conversion_attempts/tool_availability.log`

`std282/vgm2fur` usability in this environment: NO

Exact attempted commands and outcomes:
- `vgm2fur --help` → `/bin/bash: line 1: vgm2fur: command not found`
- `python3 -m vgm2fur --help` → `/usr/bin/python3: No module named vgm2fur`

Attempt logs:
- `audio/rastan_music_dump/conversion_attempts/tool_attempt_vgm2fur.log`
- `audio/rastan_music_dump/conversion_attempts/tool_attempt_python_module_vgm2fur.log`

## 6. Conversion Attempts Performed
Because dedicated local VGM conversion tools were unavailable, the practical conversion path used was:
1. Decompress `.vgz` to `.vgm`
2. Parse VGM command stream and timing
3. Emit per-track intermediate artifacts:
- Full event timeline CSV (`*_events.csv`)
- YM2151-only write timeline CSV (`*_ym2151_writes.csv`)
- Per-track parse/count summary JSON (`*_conversion_summary.json`)

Created manifest:
- `audio/rastan_music_dump/conversion_attempts/conversion_attempt_manifest.md`

Created machine summary:
- `audio/rastan_music_dump/conversion_attempts/pipeline_summary.json`

## 7. Produced Artifacts
Required files:
- `audio/rastan_music_dump/manifest_before_conversion.md`
- `audio/rastan_music_dump/vgm_validation_report.md`
- `docs/design/Cody_rastan_music_dump_conversion_report.md`

Produced conversion artifacts:
- 9 `.vgm` files in `audio/rastan_music_dump/converted_vgm/`
- 9 `*_events.csv` files in `audio/rastan_music_dump/conversion_attempts/`
- 9 `*_ym2151_writes.csv` files in `audio/rastan_music_dump/conversion_attempts/`
- 9 `*_conversion_summary.json` files in `audio/rastan_music_dump/conversion_attempts/`
- Tool logs and manifests in `audio/rastan_music_dump/conversion_attempts/`

## 8. Failures / Blockers
Blocked conversion targets:
- No local `vgm2fur` binary
- No local `vgm2fur` Python module
- No local `vgm2txt`/`vgmtool` utilities

Concrete effect:
- Direct conversion to Furnace `.fur` or equivalent tracker project was not possible in this environment.

## 9. Single Next-Step Recommendation
`USE_TEXT_OR_EVENT_DUMPS_AS_DRIVER_INPUT_REFERENCE`

## 10. Final Verdict
Practical pipeline execution succeeded for inventory, decompression, validation, and intermediate extraction. Direct tracker-conversion toolchain was unavailable, so usable intermediate command/timeline artifacts were produced instead and are ready for driver-reference or reauthoring workflows.
