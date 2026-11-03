# Cody Build 0029 Scroll Rewrite and C-Window Clear Hook Report

## 1. Summary
Build 0029 adds two targeted fixes in the shared crash path:
- Patch A rewrites scroll register writes at arcade `0x055AB4` from PC080SN hardware addresses to Genesis staged scroll variables.
- Patch B redirects the C-window fill loop at arcade `0x0561B6` to a new Genesis hook that fills staged BG/FG buffers with LUT-translated tile `0x0020` and marks all rows dirty.

No existing hooks, VINT logic, init staging logic, WRAM layout, or prior opcode entries were modified.

## 2. Preconditions verified
1. `opcode_replace_count` pre-edit was `44`.
2. `genesistan_hook_tilemap_fg` exists.
3. `fg_row_dirty` exists.
4. Build 0028 ROM @ `0x55CB4` (34 bytes) matched exactly:
   - `33 ED 10 EE 00 C2 00 00 33 ED 10 EC 00 C4 00 00`
   - `33 ED 10 B0 00 C2 00 02 33 ED 10 AE 00 C4 00 02`
   - `4E 75`
5. Build 0028 ROM @ `0x563B6` (30 bytes) matched exactly:
   - `32 3C 10 00 20 3C 00 00 00 20 20 7C 00 C0 80 00`
   - `22 7C 00 C0 00 00 20 C0 22 C0 53 41 66 F8`
6. Disassembly check for function `0x55AB4` confirms HW-write-only behavior:
   - `movew %a5@(4334),0xc20000`
   - `movew %a5@(4332),0xc40000`
   - `movew %a5@(4272),0xc20002`
   - `movew %a5@(4270),0xc40002`
   - `rts`
   - No branches/state mutation in that function body.

## 3. Scroll patch rewrite (Patch A)
Added new `opcode_replace` entry:
- `arcade_pc`: `0x055AB4`
- `original_bytes`: `33ED10EE00C2000033ED10EC00C4000033ED10B000C2000233ED10AE00C400024E75`
- `replacement_bytes`: `33ED10EE{symbol:staged_scroll_y_bg}33ED10EC{symbol:staged_scroll_x_bg}33ED10B0{symbol:staged_scroll_y_fg}33ED10AE{symbol:staged_scroll_x_fg}4E75`

This preserves opcode form, source displacements, and original RTS while redirecting destinations to staged scroll mirrors.

## 4. C-window clear hook implementation (Patch B target)
Added `.global`:
- `genesistan_hook_cwindow_clear`

Added function `genesistan_hook_cwindow_clear` immediately after `genesistan_hook_tilemap_bg_fill`.

Function behavior in strict order:
1. Translate tile index `0x0020` through `genesistan_pc080sn_tile_vram_lut`.
2. Translate attribute index `0` through `genesistan_pc080sn_attr_lut`.
3. Combine to one Genesis nametable word.
4. Fill `staged_bg_buffer` (2048 words).
5. Fill `staged_fg_buffer` (2048 words).
6. Set `bg_row_dirty = 0xFFFFFFFF`.
7. Set `fg_row_dirty = 0xFFFFFFFF`.

No scroll variables and no A5 scroll offsets are referenced in this hook.

## 5. C-window fill redirect patch (Patch B)
Added new `opcode_replace` entry:
- `arcade_pc`: `0x0561B6`
- `original_bytes`: `323C1000203C00000020207C00C08000227C00C0000020C022C0534166F8`
- `replacement_bytes`: `4EB9{symbol:genesistan_hook_cwindow_clear}4E714E714E714E714E714E714E714E714E714E714E714E71`

This is JSR + structural padding only.

## 6. Required symbol updates
Added to `required_symbols`:
- `genesistan_hook_cwindow_clear`
- `staged_scroll_y_fg`
- `staged_scroll_x_fg`

## 7. opcode_replace_count
Updated:
- `44 -> 46`

## 8. Build result
Command:
- `source tools/setup_env.sh && make -C apps/rastan-direct`

Result:
- PASS
- Numbered artifact generated: `dist/rastan-direct/rastan_direct_video_test_build_0029.bin`

## 9. ROM verification
### 9.1 Scroll patch bytes @ Genesis `0x55CB4` (34 bytes)
Observed:
- `33 ED 10 EE 00 FF 40 2C`
- `33 ED 10 EC 00 FF 40 28`
- `33 ED 10 B0 00 FF 40 2E`
- `33 ED 10 AE 00 FF 40 2A`
- `4E 75`

Matches expected opcodes/displacements with symbol-resolved WRAM destinations.

### 9.2 C-window redirect bytes @ Genesis `0x563B6` (30 bytes)
Observed:
- `4E B9 00 07 05 4E`
- followed by `4E 71` repeated through byte 29 (12 padding words)

### 9.3 Symbol table addresses (all 9)
From `apps/rastan-direct/out/symbol.txt`:
- `genesistan_hook_cwindow_clear = 0x0007054E`
- `staged_bg_buffer = 0x00FF4030`
- `staged_fg_buffer = 0x00FF5030`
- `bg_row_dirty = 0x00FF4006`
- `fg_row_dirty = 0x00FF400A`
- `staged_scroll_x_bg = 0x00FF4028`
- `staged_scroll_y_bg = 0x00FF402C`
- `staged_scroll_x_fg = 0x00FF402A`
- `staged_scroll_y_fg = 0x00FF402E`

WRAM validation:
- All `staged_*` and `*_dirty` symbols above are in `0xFF0000–0xFFFFFF`.

## 10. MAME trace results
Trace command:
- `timeout 120s tools/mame/run_genesis_trace_wsl.sh apps/rastan-direct/dist/rastan_direct_video_test.bin -video none -sound none -nothrottle -seconds_to_run 30`

Saved path:
- `states/traces/rastan_direct_video_test_build_0029_mame_30s_20260413_181500/`

Saved files:
- `states/traces/rastan_direct_video_test_build_0029_mame_30s_20260413_181500/genesis_exec_summary.txt`
- `states/traces/rastan_direct_video_test_build_0029_mame_30s_20260413_181500/genesis_exec_trace.log`

Summary metrics:
- `frames=1798`
- `reg_c50000_live count=0`
- `title_init_block@000200 count=0`

Trace completion:
- Completed full requested run window (no early termination indicated by harness output).
