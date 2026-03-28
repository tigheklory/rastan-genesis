# Build 236 First Descriptor Translation Fix

## 1) Exact translation change made
Tested ROM artifact: `dist/Rastan_236.bin` (mode-1 runtime probes).

Two locked-scope opcode-level replacements were applied on top of Build 235:
- Descriptor translation field for the first title text record:
  - `0x03BCBE`: `0B0B0F0C` -> `E0FFC84C`
- Title dispatch wrapper target preserved to proven semantic entry:
  - `0x03BD5E`: `4EB900202A4C4E75` -> `4EB9002027C04E75`

Static byte proof:
- `dist/Rastan_235.bin @0x03BCBE`: `0b 0b 0f 0c`
- `dist/Rastan_236.bin @0x03BCBE`: `e0 ff c8 4c`
- `dist/Rastan_235.bin @0x03BD5E`: `4e b9 00 20 2a 4c 4e 75`
- `dist/Rastan_236.bin @0x03BD5E`: `4e b9 00 20 27 c0 4e 75`

ROM checksums:
- `Rastan_235.bin`: `3a3ef75cd081b2c920a1efeb4ed17430`
- `Rastan_236.bin`: `b179e5b985dd2b348e075a04d1b31c58`

## 2) Why this is a translation, not a hack
- The changed field is the descriptor destination longword consumed by `0x20034C` as `D6` for destination-range gating.
- The update maps arcade descriptor destination semantics into the active Genesis text workram window (`0xE0FFC84C`), matching the proven compare contract at `0x2003EC`.
- No sprite path, state-seed logic, wrappers, shims, trampolines, or per-screen fake data were introduced.
- Replacement length is unchanged for the descriptor field (`4 bytes`), so relocation/shift behavior is preserved.

## 3) Execution proof
Probe: `/tmp/first_graphics_break_trace.lua` on `dist/Rastan_236.bin`, 20s started path.

- `HIT pc=03BD5E count=3`
- `HIT pc=2027C0 count=1`
- `HIT pc=202A4C count=0`
- `HIT pc=20034C count=1`

This proves required chain execution (`0x03BD5E -> 0x2027C0 -> 0x20034C`) on the tested artifact.

## 4) Rejection-site proof
Probe: `/tmp/text_record_branch_trace.lua` on `dist/Rastan_236.bin`, 20s run.

Relevant hits:
- `HIT 2003EC 156`
- `HIT 2003F0 156`
- `HIT 2004A2 156`

Interpretation:
- `0x2003EC` no longer rejects-all for this record because fall-through at `0x2003F0` is reached on each iteration.
- Productive producer write site `0x2004A2` is now reached (`156` hits).

## 5) Producer write proof
Probe: `/tmp/title_forward_probe.lua` and `/tmp/text_cell_scan.lua` on `dist/Rastan_236.bin`.

- `text_shadow writes=2357`, `nonzero_writes=1302`
- `text_shadow_window_nonzero_bytes=568/1024`
- `nonspace_cells=146/256`
- Sample non-space cells:
  - `cell=000 attr=1210 glyph=000D`
  - `cell=001 attr=1210 glyph=0018`
  - `cell=002 attr=1210 glyph=000B`

This confirms non-space text payload is produced after the descriptor translation change.

## 6) Visible result
Readable visible text is present on-screen in this tested run.

Evidence:
- Captured frame from `dist/Rastan_236.bin` video run: `docs/research/artifacts/build236_visible_text.png`
- The frame shows readable text strings (e.g., `PC`, `SR`, `A0`, `D0`) rendered on screen.

Classification: **VISIBLE_TEXT_PRESENT**.

## 7) Remaining issues
- Main title-plane hooks `0x200000/0x2001A6` still show `0` in this 20s window; active writes are currently seen via other producer paths (e.g., `0x200DE2` and producer-site `0x2004A2`).
- The run still reaches exception-screen output later; this pass intentionally did not widen scope into later crash handling.
- Full clean rebuild through default `postpatch_startup_rom.py` spec validation is still blocked by unrelated stale preimage mismatches in other opcode_replace entries; this pass validated behavior on exact tested artifact `dist/Rastan_236.bin`.
