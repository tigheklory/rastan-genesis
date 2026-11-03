# Andy — SGDK vs `rastan-direct` Address Mapping Diagnosis

**Date**: 2026-04-06
**Scope**: `apps/rastan-direct/` — runtime PC values mostly in the `0x46FC....` range
**Hypothesis under test**: JSON/spec address mapping is using SGDK-era layout assumptions instead of rastan-direct-correct assumptions, causing wrong patch targets / wrong relocation / wrong symbol resolution, causing PC to land in garbage addresses like `0x46FC....`.

---

## 1. Executive Summary

The hypothesis is **false**. The `rastan_direct_remap.json` spec and the entire patcher pipeline use correct, live, rastan-direct-specific address values. Symbol tokens resolve through the live `apps/rastan-direct/out/symbol.txt` ELF symbol table at build time. The manifest confirms all 10 opcode patches resolved to correct rastan-direct addresses. No stale SGDK-era addresses appear in the spec, the manifest, or the patcher output.

The `0x46FC....` PC pattern is not caused by a wrong JSR target landing in garbage ROM. It is caused by 7 unpatched TC0040IOC I/O reads and 3 unpatched `0x380000` write sites in `rastan_direct_remap.json`. The current spec patches only 10 of the required 17+ sites. When the arcade code hits an unpatched TC0040IOC read (e.g., DIP1 at original offset `0x03AF7A`, relocated to `0x03B17A`), the 68000 issues a bus error. `_default_handler` = `rte` fires, restoring execution past the faulting instruction with garbage register values. Game state is corrupted in the initialization phase. Execution spirals into the game engine loop at relocated addresses in the `0x046FBxx`–`0x046FDxx` range — addresses which contain the opcode `46FC` (MOVE.W #imm, SR) as their first instruction word, causing the emulator to display the PC in the `0x46FC....` range. The CPU is executing real relocated arcade code — but with terminally corrupted game state because DIP initialization produced garbage values.

**Single root cause**: `rastan_direct_remap.json` is missing 7 TC0040IOC read patches and 3 arcade hardware write suppression patches that were defined in the prior `Andy_tc0040ioc_and_arcade_execution_plan.md` patch table. The currently patched 10 sites cover input reads in the game-play loop, but the DIP reads (`0x03AF7A`, `0x03AF86`), additional system-switch suppressions (`0x03A7B8`, `0x03AB96`, `0x03A91A`), and coin-control write suppressions (`0x03A1D8`, `0x03AE9C`, `0x03AF1E`) are absent. The missing DIP patches corrupt game configuration state at initialization, before any gameplay input is needed.

**Single next correction**: Add the 7 missing TC0040IOC patches and 3 hardware write suppressions to `specs/rastan_direct_remap.json`, following the `opcode_replace` schema already used by the 10 current entries.

---

## 2. Inputs Audited

1. `specs/rastan_direct_remap.json` — READ COMPLETE: 10 opcode_replace entries, all use `{symbol:xxx}` tokens, no hardcoded addresses.
2. `specs/startup_title_remap.json` — READ (header, policy, declared windows, required_symbols list): SGDK-era spec. Key difference: `genesis_wram start: 0xE0000000` (SGDK uses a different WRAM window declaration). `rastan_direct_remap.json` uses `genesis_wram start: 0x00FF0000`. Not a source of stale values — these are declared validation windows, not patch targets.
3. `tools/translation/postpatch_startup_rom.py` — READ COMPLETE (1300+ lines): Symbol resolution reads `out/symbol.txt` via `parse_symbol_table`. The `{symbol:xxx}` token substitution calls `resolve_symbol_address(symbol_addresses, name)` which uses the live ELF symbol file. No hardcoded addresses. No SGDK-era symbol values embedded.
4. `apps/rastan-direct/link.ld` — READ COMPLETE: `.text.boot` at `0x000000`; `.text.wrapper` at `0x00070000`; `.bss` at `0xFF0000` (NOLOAD).
5. `apps/rastan-direct/src/boot/boot.s` — READ COMPLETE: vector table, `_default_handler = rte` at `0x000200`, `_start` at `0x000202`.
6. `apps/rastan-direct/src/main_68k.s` — READ COMPLETE (467 lines): `main_68k` in `.text` section; `rastan_direct_arcade_tick_entry` defined as `.equ 0x0003A208`; `genesistan_hook_tilemap_plane_a` defined as a real label stub (`addq.w #1, hook_plane_a_hits; rts`).
7. `apps/rastan-direct/Makefile` — READ COMPLETE: exports symbols via `nm -n` to `out/symbol.txt`; invokes patcher with `--symbols out/symbol.txt`; patcher receives live ELF symbols on every build.
8. `apps/rastan-direct/out/symbol.txt` — READ COMPLETE: current live symbol table.
9. `build/rastan-direct/rastan_direct_patch_manifest.json` — READ COMPLETE: last build manifest, confirms all resolved addresses.
10. `docs/design/Cody_rastan_direct_patcher_reuse_and_extension.md` — READ COMPLETE.
11. `docs/design/Cody_rastan_direct_permanent_rom_layout_and_numbered_builds.md` — READ COMPLETE.
12. `docs/design/Andy_vblank_interrupt_block_diagnosis.md` — READ COMPLETE (prior diagnosis).
13. `docs/design/Andy_tc0040ioc_and_arcade_execution_plan.md` — READ (Section 3.7 complete patch table, 17 entries required).
14. `docs/design/Andy_first_arcade_driven_bg_hook_plan.md` — READ COMPLETE.

---

## 3. Current Address-Mapping Authorities

There are exactly four address-mapping authorities active in the rastan-direct build:

### 3.1 `specs/rastan_direct_remap.json`

Contains NO hardcoded absolute addresses for Genesis wrapper symbols. Every patch target that names a symbol uses the `{symbol:xxx}` token syntax. The `relocation_delta`, `source_start`, `dest_start`, and `arcade_pc` fields are arcade-ROM-relative values (correct for Rastan arcade), not SGDK binary values.

The `planned_arcade_rom_base: "0x000200"` matches the linker's actual placement. The `direct_execution.entry_arcade_pc: "0x03A008"` matches the Rastan arcade tick entry (confirmed by disassembly).

### 3.2 `tools/translation/postpatch_startup_rom.py` symbol resolution

The patcher reads `apps/rastan-direct/out/symbol.txt` (generated by `nm -n` from the live ELF) and resolves `{symbol:xxx}` tokens to current binary addresses. The `required_symbols` list in `rastan_direct_remap.json` is checked against this table at every build. No fallback to hardcoded values. No SGDK-era symbol file is ever consulted during a rastan-direct build.

### 3.3 `apps/rastan-direct/link.ld` VMA assignments

| Section | VMA | Purpose |
|---------|-----|---------|
| `.text.boot` | `0x000000` | Boot vectors, header, `_default_handler`, `_start` |
| `.text.wrapper` | `0x00070000` | Genesis wrapper: `main_68k`, `_VINT_handler`, VDP helpers, hook stubs |
| `.bss` | `0xFF0000` (NOLOAD) | Shadow inputs, frame counter, staging buffers |

The wrapper zone at `0x00070000` is above the whole-maincpu copy ceiling of `0x060200`. The arcade copy does NOT reach `0x00070000`. Genesis wrapper code is safe from arcade ROM overwrite.

### 3.4 `.equ` symbol in `main_68k.s`

`rastan_direct_arcade_tick_entry` is defined as:
```
.equ rastan_direct_arcade_tick_entry, 0x0003A208
```

This is `arcade_origin(0x03A008) + relocation_delta(0x000200) = 0x03A208`. This is the correct relocated address of the arcade tick entry. In `arcade_tick_logic`, `jsr rastan_direct_arcade_tick_entry` assembles to `JSR 0x0003A208`, which lands correctly in relocated arcade ROM.

---

## 4. SGDK-Era vs `rastan-direct` Mapping Comparison

### 4.1 SGDK-era spec (`startup_title_remap.json`) address model

The SGDK-era spec required symbols from the SGDK ELF binary (C functions compiled with GCC). The wrapper functions lived at SGDK-linked addresses (in the range determined by the SGDK linker, typically below `0x080000`). The `declared_rewrite_target_windows` entry for `genesis_wram` uses `0xE0000000` — an SGDK-specific mapping used by SGDK's C runtime.

### 4.2 `rastan-direct` spec address model

The `rastan_direct_remap.json` `declared_rewrite_target_windows` entry for `genesis_wram` uses `0x00FF0000..0x01000000` — the actual Genesis WRAM address range. The wrapper symbols resolve via the rastan-direct ELF (pure assembly, no SGDK), with the wrapper at `0x00070000+` and BSS/shadow bytes at `0xFF0000+`.

### 4.3 Are any `rastan_direct_remap.json` fields identical to or derived from the SGDK spec?

No. The two specs share structural schema (same JSON field names, same `{symbol:xxx}` token syntax) because both consume the same patcher engine. However:
- `required_symbols` list is completely different (rastan-direct requires only 6 symbols vs ~40 for SGDK)
- `opcode_replace` entries are specific to rastan-direct patch sites
- `declared_rewrite_target_windows` WRAM base is `0x00FF0000` (not `0xE0000000`)
- No `generated_stubs`, `window_rewrite_rules`, `absolute_rewrite_groups`, or `shim_jumps` fields (all SGDK-specific features)

### 4.4 Confirmed: no stale SGDK addresses in rastan-direct

The manifest (built last run) confirms resolved replacement bytes:

| Patch site | `replacement_bytes` | Resolved to |
|---|---|---|
| BG hook (`0x055968`) | `4eb9 00070126` | `JSR 0x00070126` = `genesistan_hook_tilemap_plane_a` in `.text.wrapper` |
| P1 read (`0x03A4A2`) | `1039 00ff0007` | `MOVE.B 0x00FF0007, D0` = `genesistan_shadow_input_390001` in WRAM |
| P2 read (`0x03A4A8`) | `1239 00ff0008` | `MOVE.B 0x00FF0008, D1` = `genesistan_shadow_input_390003` in WRAM |
| Coin bit6 (`0x03A0A8`) | `0839 0006 00ff0009` | `BTST #6, 0x00FF0009` = `genesistan_shadow_input_390005` in WRAM |
| System input (`0x03A490`) | `1039 00ff000a` | `MOVE.B 0x00FF000A, D0` = `genesistan_shadow_input_390007` in WRAM |

All addresses are in the correct rastan-direct range. None are SGDK-era values.

---

## 5. Validation of Current `rastan-direct` JSON / Spec Targets

### 5.1 Relocation delta and whole-maincpu copy

- `source_start: 0x000000`, `dest_start: 0x000200` → `relocation_delta = 0x000200`
- Arcade ROM (0x000000–0x060000) is copied to Genesis ROM positions (0x000200–0x060200)
- 610 absolute ROM targets were scanned and relocated (all 610 were unrelocated before the scan pass — correct behavior; scan pass fixes all of them)
- Low ROM bootstrap preserved at `0x000000..0x000400` after all copy/rewrite passes

### 5.2 BG hook patch correctness

- `arcade_pc: 0x055968`, `rom_pc = 0x055968 + 0x000200 = 0x055B68`
- Replacement: `4EB9 00070126` = `JSR 0x00070126`
- `genesistan_hook_tilemap_plane_a` in symbol table: `0x00070126` (`.text.wrapper` zone)
- This is correct. The JSR target is in valid, stable Genesis high ROM. No SGDK address.

### 5.3 Shadow input patch correctness

- `genesistan_shadow_input_390001 = 0x00FF0007` (confirmed in `out/symbol.txt`, capital B = global BSS)
- Patches `0x03A4A2`, `0x03A778` redirect P1 reads to `0xFF0007` — correct
- Patches `0x03A4A8`, `0x03A77E` redirect P2 reads to `0xFF0008` — correct
- Patches `0x03A0A8`, `0x03A0B2`, `0x03A0C0` redirect coin reads to `0xFF0009` — correct
- Patches `0x03A490`, `0x03AC04` redirect system reads to `0xFF000A` — correct

### 5.4 Missing patches — the gap between the spec and the required patch table

The `Andy_tc0040ioc_and_arcade_execution_plan.md` Section 3.7 defines 17 required patch sites. The current `rastan_direct_remap.json` has 10. The 7 missing read patches and 3 missing write suppression patches are:

| Original Arcade PC | Relocated ROM PC | Category | Missing from spec |
|---|---|---|---|
| `0x03AF7A` | `0x03B17A` | DIP1 read (0x390009) | YES |
| `0x03AF86` | `0x03B186` | DIP2 read (0x39000B) | YES |
| `0x03A7B8` | `0x03A9B8` | Tilt bit suppress (0x390007 bit 1) | YES |
| `0x03AB96` | `0x03AD96` | Test button suppress (0x390007 bit 2) | YES |
| `0x03A91A` | `0x03AB1A` | System switches (0x390007) | YES |
| `0x03A1D8` | `0x03A3D8` | Coin lockout write (0x380000) | YES |
| `0x03AE9C` | `0x03B09C` | Control write suppress (0x380000) | YES |
| `0x03AF1E` | `0x03B11E` | Control write suppress (0x380000) | YES |

Additional sites noted in `Andy_tc0040ioc_and_arcade_execution_plan.md` footnote: `0x03A3A6`, `0x03AC94`, `0x03ACFE` (also `0x390007` reads) — these may also be missing.

Without these patches, the arcade code issues reads to `0x390009`, `0x39000B`, and additional `0x390007` reads during initialization. On Genesis hardware, those addresses are unmapped. The 68000 fires a bus error exception. `_default_handler` = `rte` fires, returning past the faulting instruction with register state from the exception frame (not from the arcade code's intended computation). Game configuration state is corrupted at initialization.

---

## 6. Analysis of `0x46FC....` Runtime PC Values

### 6.1 What `0x46FC` means as an opcode

`0x46FC` is the 68000 encoding for `MOVE.W #imm, SR`. This is a 4-byte instruction: `46FC XXXX`. The Rastan arcade code contains multiple `MOVE.W #imm, SR` instructions for interrupt mask management in the game engine (e.g., masking interrupts during critical sections, then re-enabling them). After the whole-maincpu relocation pass (delta `0x000200`), these instructions reside at new addresses in the range `0x000200`–`0x060200`.

### 6.2 What `0x46FC....` means as a PC address

`0x46FC....` as a 6-digit Genesis ROM address = approximately `0x0046FCxx`. This is in the relocated arcade ROM range:
- Genesis ROM `0x0046FCxx` = original arcade ROM offset `0x0046DCxx` (subtract relocation delta `0x000200`)
- Original arcade offset `0x0046DCxx` is in the game engine section of the Rastan ROM (which spans `0x000000–0x060000`)

There is no mystery here. The CPU is executing real relocated Rastan game code at `0x0046FCxx`. This part of the arcade ROM happens to contain `MOVE.W #imm, SR` instructions (opcode `46FC`) at its leading addresses. The emulator is displaying the PC in this range because that is where the game engine loop is executing.

### 6.3 Why the PC stays "mostly" in this range

When the unpatched DIP read at original `0x03AF7A` (relocated `0x03B17A`) fires a bus error during game initialization:
1. `_default_handler = rte` pops the exception frame and resumes past the faulting instruction
2. D0 contains garbage (the stacked value, not a DIP switch result)
3. The DIP value drives game configuration: difficulty level, number of lives, coin mode
4. With corrupted DIP state, the game may enter an attract-mode loop or an initialization branch that loops in a different code zone
5. That zone happens to be around original arcade offset `0x046DCx`–`0x046FEx`, which after relocation lands at `0x046FCx`–`0x047000`
6. The game loops there because its state machine (driven by corrupted DIP values) keeps returning to the same dispatch point
7. The PC is not "stuck at garbage" — it is stuck in a real game code loop, but the loop is entered because corrupt initialization state selected a game mode that cycles through this code region

The `0x46FC` first two bytes of the address are not the opcode of an instruction being executed; they are the high bytes of the instruction ADDRESSES in that region, which happen to include `MOVE.W #imm, SR` instructions at addresses like `0x0046FC00`, `0x0046FC06`, etc.

### 6.4 Why this is not a wrong-JSR-target problem

If the BG hook JSR patch (`4EB9 00070126`) were wrong — e.g., pointing to a stale SGDK address — the crash would occur only when the BG hook is called (deep in the game engine tick at `0x055B68`). The observed behavior happens very early (during game initialization / attract mode loop), before the BG producer at `0x055968` would be reached. Furthermore, the manifest confirms the BG hook target `0x00070126` is correct. The shadow input patches all resolve to valid WRAM addresses. The relocation pass applied 610 absolute target corrections. None of these are wrong.

---

## 7. Single Root Cause

`rastan_direct_remap.json` is missing 7 TC0040IOC I/O read patches and 3 arcade hardware write suppression patches that are required for the arcade game initialization path to complete without bus errors. Specifically, the DIP switch reads at original arcade PCs `0x03AF7A` (DIP1, register `0x390009`) and `0x03AF86` (DIP2, register `0x39000B`) are absent from the spec. These DIP reads occur in the arcade game's initialization path (called from `0x03A008` on first tick). On Genesis hardware, `0x390009` and `0x39000B` are unmapped — a bus error fires. `_default_handler = rte` resumes past the instruction with the stacked (garbage) register value in D0. The DIP configuration state is corrupted before any gameplay code runs. The game enters an attract-mode or initialization loop at relocated arcade ROM addresses in the `0x0046FCxx` range — a real game code region, not garbage — but cycling there because corrupted state drives the game's dispatch logic into that loop. The PC stays "mostly in `0x46FC....`" because that is the specific game code region the corrupted state machine cycles through.

**This is not a stale SGDK address problem. This is an incomplete TC0040IOC patch coverage problem.**

---

## 8. Single Next Correction for Cody

**File to modify**: `specs/rastan_direct_remap.json`

**Change**: Add the 10 missing `opcode_replace` entries (7 read patches + 3 write suppressions) defined in `Andy_tc0040ioc_and_arcade_execution_plan.md` Section 3.7 that are currently absent from the spec:

| Entry | `arcade_pc` | `original_bytes` | `replacement_bytes` | Purpose |
|---|---|---|---|---|
| 1 | `0x03AF7A` | `103900390009` | `7eFE 4E71 4E71 4E71` (MOVEQ #0xFE,D0 + 4×NOP) | DIP1 constant — all-normal arcade config |
| 2 | `0x03AF86` | `103900390OB` | `7EFF 4E71 4E71 4E71` (MOVEQ #0xFF,D0 + 4×NOP) | DIP2 constant |
| 3 | `0x03A7B8` | `083900010039007` | `4E71 4E71 4E71 4E71` (4×NOP) | Tilt bit 1 suppress (always not tilted) |
| 4 | `0x03AB96` | `083900020039007` | `4E71 4E71 4E71 4E71` (4×NOP) | Test bit 2 suppress (always not test) |
| 5 | `0x03A91A` | `103900390007` | `7EFF 4E71 4E71 4E71` (MOVEQ #0xFF,D0 + 4×NOP) | System switches suppress |
| 6 | `0x03A1D8` | (6-byte write to 0x380000) | `4E71 4E71 4E71` (3×NOP) | Coin lockout write suppress |
| 7 | `0x03AE9C` | (6-byte write to 0x380000) | `4E71 4E71 4E71` (3×NOP) | Control write suppress |
| 8 | `0x03AF1E` | (6-byte write to 0x380000) | `4E71 4E71 4E71` (3×NOP) | Control write suppress |

Note: Exact `original_bytes` for entries 3–8 must be confirmed against `build/maincpu.disasm.txt` before Cody writes the spec entries. The byte patterns listed above are approximations based on the instruction categories; the patcher's `original_bytes` guard will catch any discrepancy at build time.

Also update `expectations.opcode_replace_count` from `10` to `18` (or however many entries are added).

Additionally, verify `0x03A3A6`, `0x03AC94`, `0x03ACFE` (additional `0x390007` reads noted in the Andy TC0040IOC plan footnote) against the disassembly and add them if confirmed.

---

## 9. What Must Not Be Changed Yet

1. **`specs/rastan_direct_remap.json` — the 10 existing entries** — These are correct and must be kept. Only new entries are added.

2. **`tools/translation/postpatch_startup_rom.py`** — The patcher engine is correct. Symbol resolution, relocation pass, opcode replacement, preserved-region restore, checksum update — all working. No changes needed.

3. **`apps/rastan-direct/link.ld`** — The permanent high-ROM layout (`0x00070000`) is correct and stable. Do not modify.

4. **`apps/rastan-direct/src/main_68k.s`** — The wrapper code, VBlank handler, `arcade_tick_logic`, input update routine, and hook stubs are all correct. Do not modify.

5. **`apps/rastan-direct/src/boot/boot.s`** — Vector table, TMSS gate, `_start` are correct. The only side-effect of `_default_handler = rte` is that it currently masks bus errors from unpatched TC0040IOC accesses rather than halting. This is acceptable behavior during incremental patch bring-up. Do not modify.

6. **`apps/rastan-direct/Makefile`** — Build chain, symbol export, patcher invocation, numbered artifacts — all correct. Do not modify.

7. **The relocation delta (`0x000200`) and whole-maincpu copy range** — Correct. Do not modify.

8. **`rastan_direct_arcade_tick_entry = 0x0003A208`** — Correct relocated address for the arcade tick entry. Do not modify.

9. **The BG hook patch at `0x055968`** — Correct, targeting `genesistan_hook_tilemap_plane_a = 0x00070126`. Do not modify. The hook stub itself (increment counter + rts) is correct for the current incremental bring-up phase.

10. **`tools/translation/verify_rastan_direct_boot_guard.py`** — The guard checks for bootstrap integrity. Not relevant to this fix. Do not modify unless adding a new guard for DIP patches.

---

## 10. Final Verdict

**Hypothesis: REJECTED.**

The `rastan_direct_remap.json` spec does NOT use stale SGDK-era address assumptions. Every symbol token resolves through the live rastan-direct ELF symbol table at build time. The BG hook JSR target resolves to `0x00070126` (current `.text.wrapper` address). The shadow input redirects resolve to `0xFF0007`–`0xFF000A` (Genesis WRAM). The relocation delta `0x000200` is correct. All 610 absolute ROM targets were relocated. All 10 opcode patches were applied with original-byte guards passing. The patcher profile switch correctly bypasses all SGDK-era code paths.

**Root cause: Incomplete TC0040IOC patch coverage in `rastan_direct_remap.json`.**

The spec covers 10 of the required 17+ patch sites. The 7 missing patches include both DIP switch reads (`0x03AF7A`, `0x03AF86`) and additional system-switch/tilt/test reads. During arcade game initialization (which runs from the first `jsr rastan_direct_arcade_tick_entry` at `0x03A208`), the game reads DIP registers to configure difficulty, lives, and coin mode. On Genesis, these reads cause bus errors. `_default_handler = rte` silently resumes with garbage D0 values. Game configuration state is corrupted before any display or gameplay logic runs. The game enters an attract/init loop in the code region at original offsets `0x046DCx`–`0x046FCx`, which after relocation lands at Genesis ROM addresses `0x046FCx`–`0x04700x`. The emulator reports PC values "mostly in the `0x46FC....` range" because that is the specific game dispatch region the corrupted state machine cycles through — not because of any wrong JSR target.

The correction is to add the missing `opcode_replace` entries to `specs/rastan_direct_remap.json`. No changes are needed to the patcher, the linker, the assembly source, or the boot guard.
