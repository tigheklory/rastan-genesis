# Cody Build 55 Palette Translation Implementation (Revised Option D)

## Scope
- Build context: rastan-direct Build 0054 -> Build 0055
- Design inputs: `docs/design/Andy_build55_palette_translation_design.md`, `docs/design/Andy_build55_palette_045dae_redesign.md`
- Phase A read-only prechecks completed before edits.

## Phase A Precheck Gates

### §A.1 `0x59AD4` register-contract gate
- Result: GREEN (confirmed).
- Source: `docs/design/Cody_build55_palette_phase_a_block.md` (prior 0/30 dependent callers) + current disassembly caller list still present at `build/maincpu.disasm.txt` (`0x511BC..0x5A4B0` calls to `0x59AD4`).

### §A.2 `0x045DB8` swap span-safety gate
- Target span: `arcade_pc 0x045DB8..0x045DBD`.
- Bytes at site: `4EB90003A2D0` in arcade disasm (`build/maincpu.disasm.txt`, line block around `0x45DB8`).
- External branch targets into interior (`0x45DB9..0x45DBD`): NONE (no matching targets found in disassembly search).
- Post-call instruction: `0x45DBE addqw #1,%a5@(568)` followed by `0x45DC2 rts`.
- Result: GREEN.

### §A.3 `0x3A2D0` contract + sibling `0x045DE4` safety gate
#### §A.3.a `0x3A2D0` contract
- Disassembly (`build/maincpu.disasm.txt`):
  - `0x3A2D0: movew %a0@+,%a1@+`
  - `0x3A2D2: subqw #1,%d0`
  - `0x3A2D4: bnes 0x3A2D0`
  - `0x3A2D6: rts`
- Proven contract: generic word copy loop; inputs `%a0` source, `%a1` destination, `%d0` word count.

#### §A.3.b caller expectations after `0x045DB8`
- Disassembly (`0x45DBE..0x45DC2`): only `addqw #1,%a5@(568)` then `rts`.
- No post-call read dependency on `%a0/%a1/%d0` before return.

#### §A.3.c sibling `0x045DE4` safety
- Disassembly (`0x45DE4..0x45DF8`) still performs `lea 0x200600,%a1` + `jsr 0x3A2D0`.
- Project mapping notes classify `0x200000` probe writes as unmapped/no Genesis equivalent (`specs/rastan_direct_remap.json` entries for `0x03AEBC` and `0x03AEE0` notes: "unmapped on Genesis").
- Existing sibling path remained live and no boot-time bus-error was observed in Build 55 30s MAME headless run.
- Result: SAFE-IGNORED.

#### §A.3.d combined
- Result: GREEN.

### §A.4 combined gate decision
- Result: PROCEED.

## Phase B Implementation

### §B.1 New helper file
- Added: `apps/rastan-direct/src/palette_hooks.s`
- Added helpers:
  - `genesistan_palette_hook_59ad4`
  - `genesistan_palette_hook_03ab00`
  - `genesistan_palette_hook_45dae`
- Helper 1 preconditions proven from `build/maincpu.disasm.txt` (`0x59AD4..0x59B18`).
- Helper 2 preconditions proven from `build/maincpu.disasm.txt` (`0x03AB00 movew #1023,0x200022`) + local palette format evidence (`docs/design/Cody_build55_mame_palette_format_evidence.md`).
- Helper 3 preconditions proven from `build/maincpu.disasm.txt` (`0x45DA4..0x45DB8` setup and `0x3A2D0` copy contract).

### §B.2 Makefile update
- Updated: `apps/rastan-direct/Makefile`
- Added object + assemble rule for `out/palette_hooks.o`.

### §B.3 Spec updates
- Updated: `specs/rastan_direct_remap.json`
- Added required symbols:
  - `genesistan_palette_hook_59ad4`
  - `genesistan_palette_hook_03ab00`
  - `genesistan_palette_hook_45dae`
- Added opcode_replace entries:
  - `arcade_pc 0x059AD4` (function-body replacement)
  - `arcade_pc 0x03AB00` (single instruction replacement)
  - `arcade_pc 0x045DB8` (revised Option D 6-byte JSR swap)
- Updated expectations count:
  - `opcode_replace_count: 90 -> 93`
- Naming consistency check: PASS (no mixed `3ab00/03ab00` or `45dae/045dae` variants in helpers/spec/symbols).

### §B.4 / §B.5 Postpatch invariant measure + update
- First postpatch failure observed:
  - expected `total_genesis_bytes_covered=0x17C974`, `count=90`
  - got `total_genesis_bytes_covered=0x17CA60`, `count=93`
- Updated invariant in `tools/translation/postpatch_startup_rom.py` to measured values:
  - `0x17C974 -> 0x17CA60`
  - `90 -> 93`

### §B.6 Rebuild + gates
- Rebuild status: PASS.
- Boot guard: PASS (`verify_rastan_direct_boot_guard.py` pre/post patch).
- Symbol resolution: PASS (`apps/rastan-direct/out/symbol.txt` includes all 3 new hook symbols).
- Numbered artifact produced: `dist/rastan-direct/rastan_direct_video_test_build_0055.bin`.

### §B.7 Runtime checks
- Headless MAME 30s run completed.
- Runtime flags probe:
  - `pc090oj_dma_test_fired_flag=0x0000`
  - `pc090oj_dma_test_mismatch_offset=0x0000`
  - `pc090oj_dma_test_expected_word=0x0000`
  - `pc090oj_dma_test_actual_word=0x0000`
  - `pc090oj_dma_test_heartbeat=0x00`
  - Interpretation per source (`apps/rastan-direct/src/pc090oj_hooks.s`): no VRAM self-test failure trap triggered.
- Palette staging probe (headless):
  - at frame 1700: `staged_writes=64`, `dirty_writes=2`, `nonzero=0`
  - This is consistent with bootstrap clear activity and does not prove runtime palette population.
- CRAM visual confirmation (title-screen color correctness): NOT VERIFIED in this headless pass.

### §B.8 Invariant preservation
1. No Genesis-side lifecycle introduced: YES
2. Helpers RTS-return: YES
3. No memory shadowing introduced: YES (writes only to existing staging + dirty flag)
4. No scaffolding in source/spec implementation path: YES
5. v3.1 closures preserved: YES (no related entries changed)
6. v3.2 dispatch contract preserved: YES (no dispatch helper edits)
7. opcode_replace at `0x3AF04` preserved: YES (entry remains)
8. `_bootstrap` closure preserved: YES (`jmp 0x3A200` present in postpatch disasm)
9. `_vblank_service` closure preserved: YES (`jmp 0x3A208` present in postpatch disasm)
10. D6 fix patches preserved: YES (`apps/rastan-direct/src/pc090oj_hooks.s` loop-counter save/restore around `bsr .Lpc090oj_emit_slot` still present in `_3b930` and `_54810`)

## Integrity Checklist
- §A.1 gate: GREEN
- §A.2 gate: GREEN
- §A.3 gate: GREEN
- §A.4 combined: PROCEED
- §B.1 helpers created: YES
- §B.2 Makefile updated: YES
- §B.3 spec count/symbols/entries updated: YES
- §B.4 measured invariant captured: YES (`0x17CA60`, `93`)
- §B.5 invariant updated to measured value: YES
- §B.6 build and symbol gates: PASS
- §B.7 CRAM visual correctness confirmation: NOT VERIFIED (headless-only evidence)
- §B.8 invariants preserved: 10/10
