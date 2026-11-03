# Build 235 First Text Handoff Fix

## 1) Change Made
- Fixed only the title text dispatch remap at `arcade_pc 0x03BB48` so runtime `0x03BD5E` no longer targets `0x2027C0`.
- File changed: `specs/startup_title_remap.json`.
- Replacement bytes changed:
  - before: `4eb9002027c04e75`
  - after: `4eb900202a4c4e75`
- Built/tested artifact: `dist/Rastan_235.bin` (mode 1 runtime).

## 2) Exact Before vs After Target
- Before:
  - `0x03BD5E: jsr 0x2027C0 ; rts`
- After:
  - `0x03BD5E: jsr 0x202A4C ; rts`
- Static proof (`dist/Rastan_235.bin`):
  - bytes at `0x03BD5E`: `4e b9 00 20 2a 4c 4e 75`

## 3) Execution Proof
Probe: `/tmp/first_graphics_break_trace.lua` with START injection (frame 20/23), 20s run on `dist/Rastan_235.bin`.

- `HIT pc=03BD5E count=1` (executed)
- `HIT pc=2027C0 count=0` (no longer live target from this dispatch)
- `HIT pc=202A4C count=1` (new dispatch target hit)
- `HIT pc=20034C count=0` (producer not reached in this build with this target)

Relevant log: `/tmp/first_graphics_break_trace.txt`

## 4) Plane Write Proof
From the same run and `/tmp/title_forward_probe.txt`:

- Producer-plane hooks remain inactive:
  - `tile_a_200000=0`
  - `tile_b_2001A6=0`
- VDP traffic is active, but not via the expected title text producer chain:
  - `vdp_data_writes=19584`
  - `vdp_ctrl_writes=13611`
  - top VDP data PCs: `0x200B98`, `0x200AB4`, `0x202D80...`

## 5) Visible Result
Visible text requirement is **NOT MET** for this single fix in current build state.

Hard evidence:
- `/tmp/text_cell_scan.txt`: `nonspace_cells=0/256` in text-shadow window.
- `/tmp/title_forward_probe.txt`: first 16 sampled cells all `glyph=0020` (space).
- `0x20034C` is not reached in this target path (`count=0`), and plane writer hooks remain zero.

Classification: **no readable/non-space title text proven visible**.

## 6) Remaining Issues
- `0x03BD5E` retargeting to `0x202A4C` is in place, but current runtime path does not reach `0x20034C`.
- Expected plane producer hooks (`0x200000`, `0x2001A6`) remain inactive.
- Therefore the required end condition (visible non-space title text) is still blocked after this single dispatch change.
