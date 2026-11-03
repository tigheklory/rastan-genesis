# Build 230 Text Dispatch Fix

## 1) Change Made
- Corrected only the title text dispatch remap target for the active dispatcher entry at arcade `0x03BB48` (runtime callsite observed at `0x03BD5E`).
- File changed: `specs/startup_title_remap.json`.
- Single replacement-byte change:
  - before: `4eb9002027b84e75` (`jsr 0x2027B8; rts`)
  - after: `4eb9002027c04e75` (`jsr 0x2027C0; rts`)

## 2) Exact Remap Before vs After
- Before (Build 229):
  - `0x03BD5E: jsr 0x2027B8`
  - `0x2027B8: move.b d0,0xE0FF4863 ; rts` (non-producer stub)
- After (Build 230):
  - `0x03BD5E: jsr 0x2027C0`
  - `0x2027C0: movel a5,-(sp) ; jsr 0x20034C ; movea.l (sp)+,a5 ; rts`

Disassembly proof (Build 230):
- `0x03BD5E` bytes: `4eb9002027c04e75`
- `0x2027B8` remains present as a stub, but no longer used by the title dispatch path.

## 3) Execution Proof
Runtime probe: started-path, START injected (frame 20 press / frame 23 release), 20s window, `RASTAN_EXCEPTION_DUMPER_MODE=1`.

- `0x03BD5E` (`title_dispatch_03BD5E`): `count=9`
- `0x2027B8` (`stub_2027B8`): `count=0`
- `0x2027C0` (`wrapper_2027C0`): `count=5`
- `0x20034C` (`writer_20034C`): `count=5`
- `0x200000` (`tilemap_a_200000`): `count=0`
- `0x2001A6` (`tilemap_b_2001A6`): `count=0`

Result: live title path executes `0x03BD5E` and now reaches `0x2027C0 -> 0x20034C`; old stub `0x2027B8` is not active in this path.

## 4) Text Producer Activation Proof
- Producer execution is now present:
  - `hit_20034c=5`
  - partial secondary path activity remains: `hit_200de2=2`
- VDP writes are confirmed active in the same started run:
  - total `0xC00000` writes: `33182`
  - total `0xC00004` writes: `24350`
- Observed VDP writer PCs include:
  - data: `0x2009E4=1862`, `0x200AB4=4704`, `0x200B98=12250`, `0x202D80=1402`
  - control: `0x2009DE=1862`, `0x200AAE=4704`, `0x200B92=12250`, `0x202D58=623`

Notes:
- `0x20034C` now executes from live title callsites.
- Tilemap hook entries `0x200000/0x2001A6` still do not execute in this 20s window.

## 5) Visual Result Description
- Classification: **partial title text appears** (execution-backed).
- Basis:
  - text dispatch no longer terminates in the non-producer stub,
  - live title path now reaches the real text writer (`0x20034C`),
  - but broader title composition remains incomplete because tilemap hook paths (`0x200000`, `0x2001A6`) are still inactive in this window.
- Direct screenshot capture was not produced in this headless probe pass.

## 6) Remaining Issues
- Tilemap producer hooks remain inactive in the observed window:
  - `0x200000 = 0`
  - `0x2001A6 = 0`
- Sprite descriptor backing remains near-empty:
  - block A (`0xFF11B2`): `0/144` nonzero bytes
  - block B (`0xFF0170`): `3/32` nonzero bytes
- Next blocker is downstream of text dispatch fix and outside this narrowly scoped remap correction.
