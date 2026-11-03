# Cody Build 0026 HW Write NOP Patch Report

## Summary
Build 0026 applies exactly two scoped corrections:
1. Added four equal-length NOP opcode patches to suppress arcade-only absolute hardware writes.
2. Corrected factory-default DIP-derived values in `init_staging_state` (four value changes, with A5@(48)=1 preserved unchanged).

## Preconditions verified
- `opcode_replace_count` was `35` before edits.
- No existing patches for `0x03ADFE`, `0x03AE06`, `0x03AE16`, `0x03AE1E`.
- Pre-edit ROM bytes matched required originals:
  - `0x03AFFE`: `33FC000000C50000`
  - `0x03B006`: `33FC000100D01BFE`
  - `0x03B016`: `33FC000100C50000`
  - `0x03B01E`: `33FC000000D01BFE`
- Factory-default block in `init_staging_state` contained expected pre-fix values:
  - `A5@(24)=0x00FF`
  - `A5@(28)=0x00FF`
  - `A5@(46)=3`
  - `A5@(48)=1`
  - `A5@(50)=2`

## Four hardware writes identified
- Arcade PC `0x03ADFE`: `MOVE.W #0, 0xC50000`
- Arcade PC `0x03AE06`: `MOVE.W #1, 0xD01BFE`
- Arcade PC `0x03AE16`: `MOVE.W #1, 0xC50000`
- Arcade PC `0x03AE1E`: `MOVE.W #0, 0xD01BFE`

## Four NOP patches added
Added four `opcode_replace` entries in `specs/rastan_direct_remap.json`:
- `0x03ADFE`: `33FC000000C50000` -> `4E714E714E714E71`
- `0x03AE06`: `33FC000100D01BFE` -> `4E714E714E714E71`
- `0x03AE16`: `33FC000100C50000` -> `4E714E714E714E71`
- `0x03AE1E`: `33FC000000D01BFE` -> `4E714E714E714E71`

## Software mirror preserved (with verification method)
Verified by post-build ROM byte inspection that mirror writes remain intact and unpatched:
- At ROM `0x03AFFA`: leading bytes `42 6D 00 1E` (`CLR.W 0x001E(%a5)`) still present.
- At ROM `0x03B010`: leading bytes `3B 7C 00 01 00 1E` (`MOVE.W #1,0x001E(%a5)`) still present.

Method: direct `xxd` byte checks on `apps/rastan-direct/dist/rastan_direct_video_test.bin`.

## Factory defaults corrected (before/after)
In `apps/rastan-direct/src/main_68k.s` (`init_staging_state` factory block):
- `A5@(24)` `0x0018(%a0)`: `#0x00FF` -> `#0x0001`
- `A5@(28)` `0x001C(%a0)`: `#0x00FF` -> `#0x0000`
- `A5@(46)` `0x002E(%a0)`: `#3` -> `#0`
- `A5@(50)` `0x0032(%a0)`: `#2` -> `#0`
- `A5@(48)` `0x0030(%a0)`: remained `#1` (unchanged, confirmed)

## Build result
Command:
- `source tools/setup_env.sh && make -C apps/rastan-direct`

Result:
- Build passed.
- Numbered artifact produced: `dist/rastan-direct/rastan_direct_video_test_build_0026.bin`.

## ROM verification
Post-build bytes (Genesis offsets):
- `0x03AFFE`: `4E714E714E714E71`
- `0x03B006`: `4E714E714E714E71`
- `0x03B016`: `4E714E714E714E71`
- `0x03B01E`: `4E714E714E714E71`

## Trace results
Command:
- `timeout 120s tools/mame/run_genesis_trace_wsl.sh apps/rastan-direct/dist/rastan_direct_video_test.bin -video none -sound none -nothrottle -seconds_to_run 30`

From `build/mame/home/genesistrace/genesis_exec_summary.txt`:
- `reg_c50000_live count=0`
- `title_init_block@000200 count=0`

## Final outcome
- Four arcade-only hardware writes are now suppressed by exact-size NOP replacements.
- Required software mirror writes at `A5@(0x1E)` remain intact.
- Factory-default DIP-derived values are corrected to match DIP injection behavior.
- Build and ROM byte verification passed.
- Trace confirms `reg_c50000_live=0`; `title_init_block@000200` remained `0` in this 30-second run.
