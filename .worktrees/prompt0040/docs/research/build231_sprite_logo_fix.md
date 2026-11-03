# Build 231 Sprite/Logo Producer Fix

## 1) Change Made
- Corrected the live title/logo producer ownership path used by `0x03AAF2 -> 0x05A174` so it no longer writes only to legacy buffers.
- File changed: `specs/startup_title_remap.json`.
- Direct opcode-path replacements added:
  - `arcade_pc 0x059F62`: `movea.l #0xE0FF4094,a0` -> `movea.l #0xE0FF11B2,a0`
  - `arcade_pc 0x059F76`: `movea.l #0x0010C170,a0` -> `movea.l #0xE0FF0170,a0`
- Build artifact: `dist/Rastan_231.bin` (built with `RASTAN_EXCEPTION_DUMPER_MODE=1`).

## 2) Exact Producer Output Before vs After
- Before (Build 230):
  - `0x05A174` outputs targeted legacy buffers:
    - `0xFF4094` clear/fill region
    - `0x10C170` descriptor write region
- After (Build 231):
  - `0x05A174` outputs target active renderer ownership buffers:
    - `0xFF11B2` (active descriptor block A)
    - `0xFF0170` (active descriptor block B)
- Disassembly proof (`dist/Rastan_231.bin`, `0x05A174` block):
  - `0x05A178: movea.l #0xE0FF11B2,a0`
  - `0x05A18C: movea.l #0xE0FF0170,a0`

## 3) Execution Proof
Started-path probe: START injected (press frame 20/release frame 23), 20s run.

- `0x03AAF2` hit count: `1`
- `0x05A174` hit count: `1`
- `0x20060C` (`genesistan_render_sprites_vdp`) hit count: `294`

Result: title-logo callsite executes, producer executes, renderer remains active.

## 4) Active Descriptor Population Proof
Ownership/read-write evidence from `/tmp/build231_sprite_probe.txt`:

- Legacy targets:
  - `0xFF4094`: `reads=0`, `writes=0`
  - `0x10C170`: `reads=0`, `writes=0`
- Active targets:
  - `0xFF11B2`: `reads=41088`, `writes=138`
  - `0xFF0170`: `reads=4704`, `writes=34`

Nonzero counts (first 20s after START):
- `0xFF11B2`: `0/144` nonzero bytes
- `0xFF0170`: `4/32` nonzero bytes

Interpretation:
- Producer ownership no longer strands output only in legacy buffers.
- Active descriptors are now the live write/read targets, but block A content is still effectively clear-only in this window.

## 5) Visual Result Description
- Classification: **no change**.
- Reason: despite corrected producer ownership addresses, active block A remains all-zero in the sampled window, so meaningful logo/sprite payload still does not appear.

## 6) Remaining Issues
- Active descriptor block A (`0xFF11B2`) is heavily consumed by renderer but remains `0/144` nonzero in the 20s started-path window.
- Block B (`0xFF0170`) is only minimally populated (`4/32` nonzero), insufficient for full title/logo composition.
- Next blocker is now descriptor-content generation/format in the live title sprite producer chain, not ownership address routing.
