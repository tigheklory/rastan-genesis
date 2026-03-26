1) Purpose
- Remove the rejected Build 227 title-prep shim route and replace it with direct in-path title-prep ownership bytes, then validate mode-1 runtime behavior and shim-crash-path removal.

2) Rejected Shim Path Removed
- Removed active shim detours:
  - `0x03AF5E -> JMP 0x202C2C`
  - `0x03B076 -> JMP 0x202C3C`
- Removed shim bridge symbols/functions:
  - `genesistan_title_prep_sprite_bridge`
  - `genesistan_title_prep_tile_text_bridge`
  - `genesistan_title_prep_sprite_buffers`
  - `genesistan_title_prep_tile_text_buffers`
- File-level removal:
  - `apps/rastan/src/startup_trampoline.s`
  - `apps/rastan/src/main.c`
  - `specs/startup_title_remap.json` (`required_symbols` no longer requires title-prep bridge symbols)

3) Direct Final-State Ownership Implemented
- Direct in-path sprite-prep ownership (`arcade_pc 0x03AD4C`, relocated runtime `0x03AF5E`):
  - `move.w #0x0024,d1`
  - `lea 0xE0FF11FE,a0`
  - `move.l #0x00000000,d0`
  - `bsr 0x03AF56` (longword fill primitive)
  - `move.w #0x0008,d1`
  - `lea 0xE0FF01BC,a0`
  - `move.l #0x00000000,d0`
  - `bsr 0x03AF56`
  - `rts`
- Direct in-path title text/tile staging prep (`arcade_pc 0x03AE64`, relocated runtime `0x03B076`):
  - `lea 0xE0FFC84C,a0`
  - `move.w #0x0800,d1`
  - `moveq #0x20,d0`
  - `bsr 0x03AF56`
  - repeated second pass to same target
  - `rts`
- Active disassembly proof in final ROM (`dist/Rastan_228.bin`) confirms both routines are now direct and contain no bridge JMP.

4) Shift Table / Relocation Updates
- Opcode replacement regions changed:
  - `0x03AD4C` replacement bytes changed from shim `JMP` block to direct in-path fill sequence.
  - `0x03AE64` replacement bytes changed from shim `JMP` block to direct in-path fill sequence.
- Shift/relocation pipeline rerun results:
  - `shift_table_patcher: 22 replacement(s), 6 jump-table fix(es), 7194 branch fix(es), 608 abs-long fix(es)`
- No new shift-table insertion entries were required because replacement lengths remained compatible with existing relocation flow.
- Stale-target proof for shim addresses:
  - no `0x202C2C`/`0x202C3C` references remain in source/spec/symbol paths.

5) Crash Path Verification
- Shim-specific path check target:
  - reported rejected-path crash around `PC 0x200B7A/0x200B7C` with `A1=0x000000FF`, caller including `0x03ADD2`.
- Verification results:
  - static: no active jump from title-prep routines to shim addresses remains.
  - runtime (bounded, 25s, mode-1): trace contains no `0x200B7A`, `0x200B7C`, or `0x03ADD2` markers.
- Conclusion: shim-specific crash path is not observed after shim removal.

6) Runtime Result
- Build/run mode: `RASTAN_EXCEPTION_DUMPER_MODE=1`.
- Mode proof:
  - `_Rastan_EX_*` handler symbols present.
  - text dumper format strings present.
  - QR strings absent.
- Runtime trace (MAME Genesis, 25s, no throttle):
  - execution remains in early exception-loop region (`PC` sampled around `0x21159C..0x2115A8`).
  - no observed entry into frontend/title traced ranges.
- Classification: `NEW_EARLIER_BLOCKER_EXPOSED`.

7) Remaining Gaps
- Although shim-specific title-prep detours are removed, runtime remains trapped in an early exception-loop path before title/frontend execution.
- Direct title-prep ownership changes are in place but cannot yet manifest on-screen until the earlier blocker is cleared.

8) Conclusion
- The rejected shim approach was removed and replaced with direct in-path opcode ownership at title-prep points.
- Shift/relocation remained coherent after direct replacement updates.
- The shim-specific crash path is no longer observed; however, a separate earlier exception-loop blocker still prevents title-state execution.
