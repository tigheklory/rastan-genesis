# Cody Build 0028 Scroll Redirect and FG Hook Report

## 1. Summary
Build 0028 implemented exactly two task groups:
- Replaced Build 0027 scroll NOP scaffolding with redirected `CLR.W abs.l` patches to Genesis staged BG scroll mirrors.
- Added missing FG strip hook path (producer identification, FG offsets, hook implementation, FG row-dirty commit, VINT wiring, and FG redirect patch).

## 2. Preconditions verified
- `opcode_replace_count` was `43` before changes.
- Scroll patch entries existed at `0x03ABBA`, `0x03ABC0`, `0x03B098`, `0x03B09E`.
- All four scroll entries were `4E714E714E71` before replacement.
- BG hook exists: `genesistan_hook_tilemap_plane_a` present.
- FG hook absent before implementation: `genesistan_hook_tilemap_fg` not present.

## 3. Scroll patch replacements
Replaced four entries in-place (same `arcade_pc`, same `original_bytes`, new redirected `replacement_bytes`):
- `0x03ABBA`: `42B9{symbol:staged_scroll_y_bg}`
- `0x03ABC0`: `42B9{symbol:staged_scroll_x_bg}`
- `0x03B098`: `42B9{symbol:staged_scroll_y_bg}`
- `0x03B09E`: `42B9{symbol:staged_scroll_x_bg}`

## 4. FG producer PC identification
FG strip producer identified in `build/maincpu.disasm.txt`:
- Producer entry PC: `0x055990`
- Original bytes (function body up to loop branch):
  - `206D10A47210227C0010D080267C0010D04024536100006E588B5489534166F2`
- Evidence:
  - Starts from `A5@(0x10A4)` destination
  - Uses shared descriptor tables at `0x10D080/0x10D040`
  - Calls FG row writer (`BSRW 0x55A14`)

## 5. FG offsets (DEST / DESC / STRIP INDEX)
Derived from A5-relative disassembly accesses:
- `ARCADE_PC080SN_DEST_FG_OFFSET = 0x10A4`
  - From `0x055990: moveal %a5@(0x10A4), %a0`
- `ARCADE_PC080SN_DESC_FG_LIST_OFFSET = 0x1000`
  - From absolute table base `0x10D080` relative to A5 base `0x10C000`
- `ARCADE_PC080SN_STRIP_INDEX_FG_OFFSET = 0x10CA`
  - From `0x55A2A`/`0x55A84: movew %a5@(0x10CA), %d7`

Verified relation to BG offsets:
- `DESC_FG_LIST` matches BG (`0x1000`)
- `STRIP_INDEX_FG` matches BG (`0x10CA`)
- `DEST_FG` differs from BG (`0x10A4` vs BG `0x10A0`)

## 6. FG hook implementation
Implemented new hook:
- `genesistan_hook_tilemap_fg`

Hook behavior mirrors BG hook structure, with FG substitutions:
- C-window base: `0x00C08000`
- destination offset: `ARCADE_PC080SN_DEST_FG_OFFSET`
- descriptor list: `ARCADE_PC080SN_DESC_FG_LIST_OFFSET`
- strip index: `ARCADE_PC080SN_STRIP_INDEX_FG_OFFSET`
- staged buffer: `staged_fg_buffer`
- dirty tracking: `fg_row_dirty`

Also declared all discovered FG offsets as `.equ` constants.

## 7. FG commit implementation
Added:
- `vdp_commit_fg_strips_if_dirty`

Behavior mirrors BG row commit logic, with FG substitutions:
- Source buffer: `staged_fg_buffer`
- Dirty mask: `fg_row_dirty`
- VRAM destination: `VRAM_PLANE_A_BASE`

## 8. VINT wiring
Updated `_VINT_handler` sequence to include:
- `bsr vdp_commit_fg_strips_if_dirty`

Inserted immediately after BG strip commit.

## 9. FG redirect patch
Added new opcode replacement:
- `arcade_pc: 0x055990`
- `original_bytes: 206D10A47210227C0010D080267C0010D04024536100006E588B5489534166F2`
- `replacement_bytes: 4eb9{symbol:genesistan_hook_tilemap_fg}4e714e714e714e714e714e714e714e714e714e714e714e714e71`

Also added required symbol entries for:
- `genesistan_hook_tilemap_fg`
- `staged_scroll_x_bg`
- `staged_scroll_y_bg`

`opcode_replace_count` updated from `43` to `44`.

## 10. Build result
Build command:
- `source tools/setup_env.sh && make -C apps/rastan-direct`

Result:
- PASS
- Numbered artifact produced:
  - `dist/rastan-direct/rastan_direct_video_test_build_0028.bin`

## 11. ROM verification
Verified post-build bytes:

Scroll redirects (Genesis offsets):
- `0x03ADBA`: `42 B9 00 FF 40 2C` (points to `staged_scroll_y_bg`)
- `0x03ADC0`: `42 B9 00 FF 40 28` (points to `staged_scroll_x_bg`)
- `0x03B298`: `42 B9 00 FF 40 2C`
- `0x03B29E`: `42 B9 00 FF 40 28`

FG hook redirect:
- `0x055B90` (arcade `0x055990` + `0x200`) starts with:
  - `4E B9 ...` (JSR abs.l to `genesistan_hook_tilemap_fg`)

## 12. MAME trace results
Trace command:
- `timeout 120s tools/mame/run_genesis_trace_wsl.sh apps/rastan-direct/dist/rastan_direct_video_test.bin -video none -sound none -nothrottle -seconds_to_run 30`

Saved trace directory:
- `states/traces/rastan_direct_video_test_build_0028_mame_30s_20260413_112440/`

Saved files (both present and non-empty):
- `states/traces/rastan_direct_video_test_build_0028_mame_30s_20260413_112440/genesis_exec_summary.txt`
- `states/traces/rastan_direct_video_test_build_0028_mame_30s_20260413_112440/genesis_exec_trace.log`

Required metrics from summary:
- `reg_c50000_live count = 0`
- `title_init_block@000200 count = 0`

Evidence FG crash path resolved:
- Trace completed full run window (`frames=1798` over ~29s reported by harness) with logs generated, indicating no early abort from the prior scroll `CLR.W` hardware-read freeze path.
