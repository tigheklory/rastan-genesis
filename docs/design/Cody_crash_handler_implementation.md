# Cody Crash Handler Implementation (Build 0038 Context)

## Scope
Implemented first-fault crash handling per `docs/design/Andy_crash_handler_spec.md` using:
- `apps/rastan-direct/src/crash_handler.s` (new)
- `apps/rastan-direct/src/boot/boot.s` (vector table updates)
- `apps/rastan-direct/src/main_68k.s` (includes crash handler source)

## Vector Table Changes
- Replaced all exception destinations that were previously routed through `_default_handler` with crash stubs.
- Preserved vector 30 (`_VINT_handler`) unchanged.
- Stub strategy applied as requested:
  - unique stubs for vectors 2-11
  - unique stubs for TRAP vectors 32-47
  - grouped `_crash_stub_other` for remaining vectors routed to former default handler

Observed ROM vector destinations after build:
- Vector 30: `0x0007002A` (`_VINT_handler`)
- Vectors 2-11: unique crash stubs at `0x0000022A..0x00000260`
- Vector 31 and vectors 48-63: grouped stub at `0x000002C6`
- Vectors 32-47: unique trap stubs at `0x00000266..0x000002C0`
- No vector in 2-63 points to `0x00000200`

## `_default_handler: rte` Constraint Resolution
The project boot guard enforces opcode `4E73` at ROM address `0x000200`.

To satisfy both boot guard and crash-handler routing:
- removed `_default_handler` as an exception destination (no vectors point to `0x000200`)
- removed `_default_handler: rte` symbol usage from vector table
- retained required boot-guard legacy `rte` at `0x000200` as `_boot_guard_legacy_rte`

This keeps reset-vector invariants valid while ensuring exceptions no longer route to `rte`.

## Common Handler Execution Order
`_crash_common` implements:
1. `move.w #0x2700, %sr`
2. `move.l %sp, %a0`
3. lockout check (`CRASH_ACTIVE_FLAG`)
4. minimal halt path (`stop` + `bra`) on re-entry
5. set lockout flag
6. store exception type from D0
7. explicit frame decode branch on D0 (`<=3` bus/address path, else standard path)
8. frame field writes
9. individual register writes (no `movem`)
10. `lea 0x00FFFF00, %sp`
11. capture project-specific state
12. VDP reinit
13. crash screen render
14. halt forever

## Crash Record
Base: `CRASH_RECORD_BASE = 0x00FF6800`

Conflict/alignment checks:
- Highest BSS symbol observed: `0x00FF60B0` (`staged_tile_words`)
- Margin to crash base: `0x750` bytes
- All longword fields are on even addresses (validated)

## VDP Command Verification
Specified formula:
`cmd = 0x40000000 | ((A & 0x3FFF) << 16) | ((A >> 14) & 3)`

For `A = 0x8000`:
- `(A & 0x3FFF) = 0x0000`
- `(A >> 14) & 3 = 2`
- `cmd = 0x40000002`

Implemented command for crash font upload:
- `move.l #0x40000002, VDP_CTRL`

## Crash Font
- Embedded 1bpp ASCII 8x8 font in crash handler source
- Characters: 96 (`0x20..0x7F`)
- Size: 768 bytes
- Expansion loop writes directly to `VDP_DATA` (no RAM scratch buffer)

## Screen Layout
Implemented rows per spec intent:
- header/title rows
- exception/vector/PC/SR/fault address rows
- D0-D7 and A0-A6 + SP + USP rows
- project state rows (DEST_BG/DEST_FG/BG/FG dirty, palette/tile dirty, frame)
- stack dump (16 longwords)
- footer row: `HALTED -- BUILD 0038`

## Build Result
Command:
`source tools/setup_env.sh && make -C apps/rastan-direct -B release`

Result: PASS
- Numbered ROM produced by build system: `dist/rastan-direct/rastan_direct_video_test_build_0039.bin`
- Boot guard: PASS (reset vector and VINT validation)

## User Verification Targets
1. Trigger the known fault path (between prior Build 38 frames 0345-0360 window).
2. Confirm crash screen appears and remains static (no flicker/update loop).
3. Confirm vector number, PC, SR, and fault address are readable.
4. Confirm execution is halted (no continued corruption/stack drain behavior).

## Build 0039 Renderer Diagnosis and Build 0040 Fix

### PC mapping from reported loop addresses
- `0x00000404`: extension word in `_crash_common` safe-stack setup (`lea 0x00FFFF00,%sp` at `0x00000400`).
- `0x0000040C`: extension word of `bsrw crash_init_cram` (`0x0000040A`).
- `0x000008AA`: extension word in `crash_clear_plane_a` VDP command setup (`move.l #0x60000003, VDP_CTRL` at `0x000008A4`).
- `0x000008B2`: `move.w #1119,%d7` in `crash_clear_plane_a`.
- `0x000008B8`: extension word of `move.w %d0,VDP_DATA` (`0x000008B6`).

These addresses are inside crash-renderer setup/clear code and its immediate words.

### Loop termination validation
- `crash_clear_plane_a` loop (`.Lclear_loop`) is finite:
  - counter: `%d7`
  - init: `0x045F`
  - mutation: `dbra %d7,.Lclear_loop`
  - first five values: `0x045F -> 0x045E -> 0x045D -> 0x045C -> 0x045B`
  - terminates when `%d7` reaches `0xFFFF`.

### Confirmed renderer bug fixed in Build 0040
- Root cause: stack-dump column counter corruption in renderer.
- In `crash_render_screen`, `.Lstack_col_loop` uses `%d6` as the loop counter.
- `crash_put_hex32_inline` calls `crash_extract_top_nibble`.
- Pre-fix `crash_extract_top_nibble` used `%d6` as scratch, clobbering the caller's `%d6` counter.
- Result: `.Lstack_col_loop` counter was not monotonic; loop termination was non-deterministic.

### Code change
- File: `apps/rastan-direct/src/crash_handler.s`
- Function: `crash_extract_top_nibble`
- Change: scratch register switched from `%d6` to `%d3`, preserving `%d6` for outer loop control.

Pre-fix:
```asm
move.l  %d4, %d6
swap    %d6
lsr.w   #8, %d6
lsr.b   #4, %d6
move.b  %d6, %d2
```

Post-fix:
```asm
move.l  %d4, %d3
swap    %d3
lsr.w   #8, %d3
lsr.b   #4, %d3
move.b  %d3, %d2
```

This preserves loop counter integrity in `.Lstack_col_loop`.

## Build 0042 Final Renderer Fix Validation

### Additional root cause found after Build 0040

The postpatch pipeline was restoring only `0x000000..0x0003FF` in low ROM.
Crash-handler code/data lives beyond `0x000400` (through the embedded font),
so postpatch copy/patch passes were overwriting crash-handler bytes in the
final ROM image.

Evidence:
- Prepatch vs postpatch mismatch at crash-handler addresses before fix:
  - `0x000400..0x00042F`: different
  - `0x0008A0..0x0008CF`: different
- This directly matched observed PCs landing in extension-word addresses
  (`0x00000404/0x0000040C/0x000008AA/0x000008B2/0x000008B8`).

### Pipeline fix applied

- Added `genesistan_crash_handler_end` symbol at the end of
  `apps/rastan-direct/src/crash_handler.s`.
- Updated `tools/translation/postpatch_startup_rom.py` to preserve low ROM
  through `max(0x000400, genesistan_crash_handler_end)` for `rastan_direct`.
- Updated preserved-segment metadata (`preserved_low_rom_bootstrap` and
  `preserved_genesis_vector_table`) to use this dynamic end.

### Post-fix byte-level validation

After Build 0042:
- `0x0003F0..0x00042F`: prepatch == postpatch
- `0x0008A0..0x0008CF`: prepatch == postpatch
- In preserved low-ROM region, only checksum bytes differ (`0x00018E..0x00018F`).

### Runtime trace validation

Build 0042 automatic 30s trace:
- `states/traces/rastan_direct_video_test_build_0042_mame_30s_20260417_152543`
- `vdp_ports_live` writes continue through crash-render activity:
  - `last_frame=390`
  - `last_pc=0x000009DE` (inside crash character write path)
- No further live VDP writes after frame 390, consistent with renderer
  completion and halt loop.
