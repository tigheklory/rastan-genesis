# Cody VGZ to MIDI Conversion Report

## 1. Executive Summary
All Rastan `.vgz` music dumps in `audio/rastan_music_dump` were processed through a reproducible pipeline:
1. Decompressed to `.vgm`
2. Converted to `.mid`
3. Validated for file existence, non-zero size, and note-event content

Final result: 9/9 `.vgz` files converted successfully to `.mid`.

## 2. Source File Count
- Source directory: `audio/rastan_music_dump`
- Source `.vgz` files found: 9

## 3. Successfully Decompressed Files
- Decompression output directory: `audio/rastan_music_dump/converted_vgm/`
- `.vgm` files generated: 9
- Files:
  - `01 - Credit.vgm`
  - `02 - Broken The Promises (Opening).vgm`
  - `03 - Aggressive World (Scene 1).vgm`
  - `04 - Bad Bible (Name Regist).vgm`
  - `05 - Re-In-Carnation (Scene 2).vgm`
  - `06 - The Devil Boss Carnival (Scene 3 Boss).vgm`
  - `07 - Scene Clear.vgm`
  - `08 - Final Destroy (Scene 3 Round 6 Boss).vgm`
  - `09 - The Man Of Saga (Ending).vgm`

## 4. Successfully Converted MIDI Files
- MIDI output directory: `audio/rastan_music_dump/converted_mid/`
- `.mid` files generated: 9
- Validation summary per file:
  - `01 - Credit.mid` (size 306, tracks 9, note events 4)
  - `02 - Broken The Promises (Opening).mid` (size 1287, tracks 9, note events 220)
  - `03 - Aggressive World (Scene 1).mid` (size 7619, tracks 9, note events 1704)
  - `04 - Bad Bible (Name Regist).mid` (size 726, tracks 9, note events 102)
  - `05 - Re-In-Carnation (Scene 2).mid` (size 9663, tracks 9, note events 2184)
  - `06 - The Devil Boss Carnival (Scene 3 Boss).mid` (size 6016, tracks 9, note events 1408)
  - `07 - Scene Clear.mid` (size 1393, tracks 9, note events 256)
  - `08 - Final Destroy (Scene 3 Round 6 Boss).mid` (size 14389, tracks 9, note events 3440)
  - `09 - The Man Of Saga (Ending).mid` (size 3955, tracks 9, note events 804)

## 5. Failed Files (if any)
None.

## 6. Tools Used
- `gzip` (decompression)
- `python3` (VGM parsing + MIDI generation + validation)

## 7. Conversion Method Used
Method used: custom Python conversion pipeline.
- Decompressed each `.vgz` to `.vgm`
- Parsed VGM command stream and timing
- Extracted YM2151 writes (`0x54` command)
- Interpreted key state using YM2151 key-on register writes (`addr 0x08`) and key-code registers
- Generated MIDI Type-1 output with 9 tracks (meta + 8 YM channels)
- Preserved timing via VGM sample clock to MIDI tick mapping

Run summary artifact:
- `audio/rastan_music_dump/conversion_attempts/vgz_to_midi_run_summary.json`

## 8. Notes on MIDI Quality (brief, factual)
- Timing is driven from VGM sample waits and preserved in MIDI ticks.
- Channel separation is 8 YM2151 channels mapped to 8 MIDI channel tracks.
- Note extraction is based on YM2151 key-on/key-off behavior and key-code interpretation.
- This output is a practical import intermediate, not a lossless reconstruction of FM patch behavior.

## 9. Final Status
Conversion pipeline completed successfully for all source dumps.
- VGZ processed: 9
- VGM generated: 9
- MIDI generated: 9
- Failures: NO
