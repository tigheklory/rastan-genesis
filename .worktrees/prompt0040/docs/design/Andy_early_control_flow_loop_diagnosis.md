# Andy — Early Control-Flow Loop Diagnosis

**Rastan-Genesis / apps/rastan-direct**
Analysis of PC loop between `0x000200` and `0x00038A`.

---

## 1. Executive Summary

The runtime symptom — PC bouncing between `0x000200` and `0x00038A`, arcade tick never
reached, screen blank — is caused by a single defect in the built binary: the boot-code
region of `dist/rastan_direct_video_test.bin` is stale. It contains a corrupted
`vdp_commit_bg` routine (an `ADDI.B` instruction at `0x00038A`) rather than the `BEQ.S`
that the current source produces. That `ADDI.B` writes to a Genesis ROM address (`0x00FFCC`,
sign-extended from abs.w), triggering a bus error on every VBlank. The exception vector for
bus error points to `0x000200` (`_default_handler = RTE`). `RTE` returns to `0x00038A`.
The same fault fires again. This is an infinite exception loop that prevents `frame_counter`
from ever incrementing, so the main loop never escapes `wait_vblank`, `arcade_tick_logic`
never runs, and `rastan_direct_arcade_tick_entry` (`0x0003A208`) is never reached.

**Root cause**: the patcher (`postpatch_startup_rom.py`) saves the first `0x400` bytes of
the ROM file on disk as `preserved_genesis_vectors` and restores them after the arcade-ROM
copy. When the ROM file on disk is a previously-patched binary (not a fresh `objcopy`
output), the patcher locks in the old boot code and overwrites the correct `objcopy` output
with stale bytes. The current ELF encodes `BEQ.S` at `0x38A` (confirmed by reading the ELF
directly). The current binary encodes `ADDI.B`. They differ.

**Single correction**: in `apps/rastan-direct/Makefile`, change the `$(BIN)` rule so that
`objcopy` is declared `.PHONY` or add a `make clean` guard such that `objcopy` always
regenerates the binary from the current ELF before the patcher reads it. Equivalently: run
`make -C apps/rastan-direct clean && make -C apps/rastan-direct` to break the stale-binary
cycle before any further runtime testing. The defect is in the **build pipeline**, not in
the source assembly or patch spec.

---

## 2. Inputs Audited

1. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s` — READ COMPLETE.
   55 lines. Exception vector table at `.org 0x000000`: all 64 vectors point to
   `_default_handler`. Reset vector points to `_start` (`0x000202`). VBlank vector
   (vec[30]) points to `_VINT_handler`. `_default_handler` at `.org 0x000200` = single
   `RTE` instruction.

2. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/main_68k.s` — READ COMPLETE.
   467 lines. Contains `main_68k`, `_VINT_handler`, `vdp_commit_bg`, `arcade_tick_logic`
   (which calls `JSR rastan_direct_arcade_tick_entry = 0x0003A208`). `vdp_commit_bg` uses
   `TST.B bg_dirty` followed by `BEQ.S .Lbg_done`. `bg_dirty` resolves to `0xFF0006` per
   current symbol table.

3. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/link.ld` — READ COMPLETE.
   `.text` starts at `0x000000` (`.text.boot` first, then `.text`, `.rodata`, `.data`). `.bss`
   at VMA `0xFF0000` (NOLOAD). No explicit placement for `.data` or arcade ROM in the linker
   script — the arcade ROM is injected post-build by the patcher.

4. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/Makefile` — READ COMPLETE.
   Build chain: assemble → link → `nm` (symbol.txt) → `objcopy` (dist binary) → patcher.
   Patcher invocation uses `--rom dist/rastan_direct_video_test.bin` (the in-place file),
   `--spec specs/rastan_direct_remap.json`, `--maincpu build/regions/maincpu.bin`.

5. `/home/tighe/projects/rastan-genesis/specs/rastan_direct_remap.json` — READ COMPLETE.
   `policy.current_copy_mode = whole_maincpu_relocated`. `whole_maincpu_copy`: source
   `0x000000..0x060000` → dest `0x000200`. `execute_from_relocated_base = true`.
   `relocation_delta = 0x000200`. 10 `opcode_replace` entries (TC0040IOC reads + BG hook).
   `rom_absolute_call_relocation` scans 19 opcodes for JSR/JMP/LEA abs.l targets.

6. `/home/tighe/projects/rastan-genesis/tools/translation/postpatch_startup_rom.py` — READ
   (lines 1–1050+). Key behavior:
   - Line 630: `rom_bytes = bytearray(rom_path.read_bytes())` — reads the `.bin` file.
   - Line 631: `preserved_genesis_vectors = bytes(rom_bytes[0x000000:0x000400])` — saves
     first `0x400` bytes from disk.
   - Lines 711–732: whole-maincpu copy writes arcade ROM to `rom_bytes[0x200..0x60200]`,
     overwriting `rom_bytes[0x200..0x3FF]` (the boot code region).
   - Line 744: `rom_bytes[0x000000:0x000400] = preserved_genesis_vectors` — restores saved
     bytes, putting boot code back. If the saved bytes came from a stale .bin, the stale
     boot code is locked in.

7. `/home/tighe/projects/rastan-genesis/docs/design/Andy_tc0040ioc_and_arcade_execution_plan.md`
   — READ (lines 1–100+). Confirmed: `ARCADE_ROM_BASE = 0x000200`. Direct execution model
   via relocated opcodes. Entry = `0x03A008 + 0x000200 = 0x3A208`. TC0040IOC patch sites
   confirmed wired to shadow symbols.

8. `/home/tighe/projects/rastan-genesis/docs/design/Cody_rastan_direct_patcher_reuse_and_extension.md`
   — READ COMPLETE. Confirmed: patcher profile `rastan_direct` added. `main_68k.s`
   compatibility symbols exported. 10 opcode replacements verified. Entry symbol address
   `0x0003A208` reported in manifest.

9. `/home/tighe/projects/rastan-genesis/docs/design/Cody_first_arcade_execution_bringup.md`
   — READ COMPLETE. `arcade_tick_logic` updated: `BSR rastan_direct_update_inputs` +
   `JSR rastan_direct_arcade_tick_entry`. `genesistan_hook_tilemap_plane_a` increments
   counter and returns. System tested as building; runtime verification user-side.

10. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/dist/rastan_direct_video_test.bin`
    — BINARY INSPECTION (Python). 524288 bytes. Arcade ROM embedded. Exception vectors read.
    Bytes at `0x000200`, `0x00038A`, `0x0003A208` inspected and decoded.

11. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/out/rastan_direct_video_test.elf`
    — PARSED (Python). `.text` section at ELF offset `0x2000`, VMA `0x000000`, size `0x868`.
    Bytes at ELF `.text + 0x384` read directly to verify source-compiled content.

12. `/home/tighe/projects/rastan-genesis/build/rastan-direct/rastan_direct_patch_manifest.json`
    — READ COMPLETE. Profile `rastan_direct`, 10 opcode replacements, entry symbol
    `0x0003A208`, whole-maincpu copy confirmed.

---

## 3. Exact Content at `0x000200`

**From the built binary** (confirmed by Python byte read):

```
[000200] = 4E
[000201] = 73
```

`0x4E73` = `RTE` (Return from Exception). This is `_default_handler` as assembled by
`boot.s` at `.org 0x000200`. It is NOT arcade ROM.

**From the vector table** (vector 2, bus error, at binary offset `0x0008`):
```
vec[2] @ 0x0008: 0x00000200
```

All exception vectors (bus error, address error, illegal instruction, etc., vectors 2–29,
31–63) point to `0x000200`. The reset vector (vec[1]) points to `0x000202` (`_start`).
VBlank (vec[30]) points to `0x000250` (`_VINT_handler`).

**Content at `0x000200` identified: YES — it is `_default_handler = RTE`.**

---

## 4. Exact Content at `0x00038A`

**Symbol table** (from `out/symbol.txt`, current build):
- `vdp_commit_bg` = `0x000384`
- `vdp_commit_tiles_if_dirty` = `0x00035A`
- `vdp_commit_palette` = `0x0003B6`

`0x00038A` is `6` bytes into `vdp_commit_bg` (the sixth byte after the label at `0x000384`).

**From the built binary:**
```
[000384] = 4A  \
[000385] = 39   |  TST.B abs.l (opcode 0x4A39)
[000386] = 00   |
[000387] = FF   |  address = 0x00FF0000 (frame_counter)
[000388] = 00   |
[000389] = 00  /
[00038A] = 04  \
[00038B] = 3A   }  ADDI.B #0, (abs.w) — opcode 0x043A
[00038C] = 61   |
[00038D] = 00   |  immediate word = 0x6100, byte = 0x00
[00038E] = FF   |
[00038F] = CC  /   abs.w address = 0xFFCC → sign-extended → 24-bit effective address = 0x00FFCC
```

`0x043A` decodes as `ADDI.B #0, abs.w`. The abs.w operand `0xFFCC` sign-extends to the
32-bit value `0xFFFFFFCC`. On the 68000's 24-bit address bus, the effective address used is
the lower 24 bits: `0x00FFCC`. On the Sega Genesis memory map, `0x00FFCC` is in ROM space
(`0x000000–0x3FFFFF`). Attempting to write to ROM via a read-modify-write cycle causes a
bus error on real hardware and on accurate emulators.

**From the ELF** (bytes at ELF `.text` section offset `0x384`, verified by Python ELF parse):
```
4A 39 00 FF 00 06   TST.B 0xFF0006   (bg_dirty — CORRECT per current source)
67 28               BEQ.S +40        (branch to .Lbg_done — CORRECT per current source)
61 00 FF CC         BSR.W vdp_commit_tiles_if_dirty
```

The **ELF has correct bytes** at `0x38A` (`0x6728` = `BEQ.S`). The **binary has wrong bytes**
at `0x38A` (`0x043A` = `ADDI.B`). The binary does not reflect the current ELF for the
boot-code region `0x000200..0x0003FF`.

**Content at `0x00038A` identified: YES — it is a stale `ADDI.B #0, 0x00FFCC` instruction
that writes to Genesis ROM space, triggering a bus error on every execution.**

---

## 5. Loop Trace and Control-Flow Diagnosis

**Step-by-step control flow producing the observed PC loop:**

1. Power-on reset: Genesis loads reset vector from `0x0004` → `0x000202` (`_start`).
2. `_start` disables interrupts, sets SP to `0xFF0000`, reads HW version, optionally
   writes TMSS, then `JSR main_68k` (to `0x22C`).
3. `main_68k` calls `vdp_boot_setup`, then `init_staging_state`, then enables interrupts
   with `MOVE.W #0x2000, SR` (IPL = 0 → VBlank allowed).
4. `main_68k` enters `wait_vblank` loop: reads `frame_counter`, spins until it changes.
5. **VBlank fires.** VBlank vector (vec[30], `0x0078`) = `0x000250` (`_VINT_handler`).
6. `_VINT_handler` saves registers, reads `VDP_CTRL`, sets display off, then calls
   `BSR vdp_commit_bg` (`0x262`: `6100 0120` → dest `0x384`).
7. `vdp_commit_bg` at `0x384`: executes `TST.B 0x00FF0000` (checks `frame_counter` low
   byte, not `bg_dirty`, because of the stale address). `frame_counter` = 0x0000 → low byte
   = 0x00 → Z-flag set. **But the next instruction at `0x38A` is `ADDI.B #0, 0x00FFCC`
   (not `BEQ.S`)**, so execution does NOT branch over it regardless of the Z-flag.
8. `ADDI.B #0, 0x00FFCC`: read-modify-write to `0x00FFCC` in Genesis ROM space.
   **Bus error fires.**
9. Bus error vector (vec[2], `0x0008`) = `0x000200` (`_default_handler` = `RTE`).
10. `RTE` pops saved PC (`0x00038A`) and SR from the exception stack frame, returns
    execution to `0x00038A`.
11. `ADDI.B` at `0x38A` executes again → bus error → `0x000200` → `RTE` → `0x38A`.
    **Infinite loop.**
12. `_VINT_handler` never completes. `frame_counter` is never incremented (the `ADDQ.W #1,
    frame_counter` at `0x284` is never reached).
13. `main_68k` `wait_vblank` loop never exits. `arcade_tick_logic` never runs.

**This is an infinite exception loop: ADDI.B at `0x38A` → bus error → `0x000200` (RTE) →
`0x38A` → bus error → `0x000200` → ... PC observed bouncing between exactly these two
addresses.**

---

## 6. Arcade Entry Reachability Analysis

**Can `0x0003A208` (`rastan_direct_arcade_tick_entry`) ever be reached? NO.**

`arcade_tick_logic` is called unconditionally from `.Lmain_loop` after `wait_vblank`
exits. `wait_vblank` exits only when `frame_counter` changes. `frame_counter` is
incremented only at `0x284` inside `_VINT_handler`, which is never reached because the
VBlank handler crashes at `0x38A` before it can complete. Therefore `frame_counter` stays
at `0x0000` forever, the `wait_vblank` loop never terminates, and `arcade_tick_logic` (and
its `JSR rastan_direct_arcade_tick_entry`) is never executed.

**Can `0x055B68` (relocated BG hook at `genesistan_hook_tilemap_plane_a`) ever be reached?
NO.**

The BG hook is invoked from within the arcade ROM tick path, which requires
`rastan_direct_arcade_tick_entry` to be reached first. Since that is not reached, the BG
hook is also not reached.

**Arcade tick (`0x0003A208`) reachable: NO.**
**BG hook (`0x055B68`) reachable: NO.**

---

## 7. Single Root Cause

The built binary `apps/rastan-direct/dist/rastan_direct_video_test.bin` contains stale
boot code at `0x000200..0x0003FF`. The instruction at `0x00038A` inside `vdp_commit_bg` is
`ADDI.B #0, 0x00FFCC` (opcode `0x043A`), not the `BEQ.S .Lbg_done` that the current
source produces. `0x00FFCC` is in Genesis ROM space; the read-modify-write triggers a bus
error on every VBlank. The bus error vector (`0x0008`) points to `0x000200`
(`_default_handler = RTE`). `RTE` returns to `0x00038A`. This repeats indefinitely.

The stale boot code entered the binary through the patcher's vector-preservation
mechanism. `postpatch_startup_rom.py` line 631 saves `rom_bytes[0x000000:0x000400]` from
the `.bin` file on disk as `preserved_genesis_vectors`, then at line 744 restores those
bytes after copying the arcade ROM. If the `.bin` file on disk is a previously-patched
output (not a fresh `objcopy` from the current ELF), the patcher locks in the old boot
code, overwriting the correct `objcopy` bytes that `objcopy` had just written. The current
ELF encodes `BEQ.S` at `0x38A` (verified by direct ELF parse). The current binary encodes
`ADDI.B`. The discrepancy proves the binary was not regenerated from the current ELF before
the patcher's last run.

---

## 8. Single Next Correction for Cody

**File**: `apps/rastan-direct/Makefile`

**Location**: the `$(BIN)` rule.

**Change**: Force `objcopy` to always regenerate the dist binary from the current ELF,
breaking the cycle where a previously-patched `.bin` is read as the basis for
`preserved_genesis_vectors`. The simplest and most robust fix is to declare the build as
requiring a forced clean build: run `make -C apps/rastan-direct clean` followed by
`make -C apps/rastan-direct` to produce a fresh `objcopy` binary before the patcher
reads it.

If a persistent structural fix is preferred: add a `FORCE` target or use `.PHONY` on the
`$(BIN)` rule in the Makefile to ensure `objcopy` always regenerates the `.bin` from ELF
before the patcher runs. An alternative in `postpatch_startup_rom.py` (for the
`rastan_direct` profile) is to derive `preserved_genesis_vectors` from a separate fresh
`objcopy` pass rather than from the `.bin` file being patched in-place.

**Immediate actionable step**: `make -C apps/rastan-direct clean && make -C apps/rastan-direct`.

After the rebuild, verify:
- Bytes at `0x38A` in the new binary = `67 28` (`BEQ.S +0x28`), NOT `04 3A`.
- Bytes at `0x386..0x389` = `00 FF 00 06` (address `bg_dirty = 0xFF0006`), NOT `00 FF 00 00`.

This is the only change needed to unblock the control-flow loop. It does not require
modifying source assembly, patch spec, or linker script.

---

## 9. What Must Not Be Changed Yet

The following are correct and must not be touched before the boot-code loop is fixed:

1. **`specs/rastan_direct_remap.json`** — The relocation delta (`0x000200`), whole-maincpu
   copy config, 10 opcode-replace entries (TC0040IOC shadows + BG hook), and
   `rom_absolute_call_relocation` scan are all verified correct by the manifest. Do not
   modify.

2. **`apps/rastan-direct/src/main_68k.s`** — Current source is correct. `arcade_tick_logic`
   calls `JSR rastan_direct_arcade_tick_entry` correctly. `vdp_commit_bg` uses `BEQ.S` to
   guard the dirty flag. Symbol exports are wired to patcher spec. Do not modify.

3. **`apps/rastan-direct/src/boot/boot.s`** — Exception vector table layout and
   `_default_handler` placement at `0x000200` are correct for Genesis bootstrap. Do not
   modify.

4. **`tools/translation/postpatch_startup_rom.py`** — The patcher code logic itself is not
   the defect; the defect is the stale `.bin` file the patcher reads as input. Do not
   modify the patcher until the clean-rebuild fix is verified.

5. **`apps/rastan-direct/link.ld`** — The linker layout (`.text` at `0x000000`, `.bss` at
   `0xFF0000`) is correct and matches the symbol table. Do not modify.

6. **All TC0040IOC opcode-replace patches in the ROM** — These are verified applied by the
   manifest (`opcode_replace_and_rom_opcode_replace = 10`). They are not the cause of the
   loop. Do not alter any patch sites.

7. **`rastan_direct_arcade_tick_entry = 0x0003A208`** — This address is correct (arcade
   src `0x03A008` + relocation `0x000200`). The entry point definition must not be changed.

---

## 10. Final Verdict

The PC loop between `0x000200` and `0x00038A` is an infinite bus-error exception loop
caused by a single stale instruction in the built binary. It has nothing to do with the
arcade ROM, the patch spec, the TC0040IOC stubs, the BG hook, or the arcade entry point.
The instruction at `0x00038A` is `ADDI.B #0, 0x00FFCC` (a write-to-ROM that triggers a
bus error) instead of the correct `BEQ.S` that the current source encodes. The VBlank
handler never completes, `frame_counter` never increments, the main loop never exits
`wait_vblank`, and `arcade_tick_logic` never runs. The arcade tick entry (`0x0003A208`)
and BG hook (`0x055B68`) are both unreachable under this condition.

The root cause is a stale-binary problem in the build pipeline: the patcher's
`preserved_genesis_vectors` restoration locked in old boot code from a previously-patched
`.bin`, overwriting the correct `objcopy` output. The single correction is a forced clean
rebuild of `apps/rastan-direct/`. No source files, no patch spec, and no linker script
require changes. The patcher, the spec, and the assembly source are all correct for the
next stage of execution.
