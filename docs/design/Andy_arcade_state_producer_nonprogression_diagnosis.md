# Andy — Arcade State Producer Non-Progression Diagnosis

**Date**: 2026-04-06
**Scope**: `apps/rastan-direct` — why A5 = 0xFFFFFFFF, why descriptor list stays zero, why inputs have no effect, why producer state never advances
**State at diagnosis**: A5 WRAM redirect patch added at 0x03AF04; build succeeds; A5 = 0xFFFFFFFF observed in Exodus; checkerboard unchanged

---

## 1. Executive Summary

The A5 WRAM redirect patch in `specs/rastan_direct_remap.json` at arcade PC `0x03AF04` is **syntactically correct** (`4BF900FF0000` = `lea 0xFF0000,%a5`). However, the instruction at `0x03AF04` is located inside the arcade's **one-time power-on initialization routine** (`0x3AE86`), which is only reachable via the arcade reset entry at `0x3A000`. The Genesis wrapper calls `rastan_direct_arcade_tick_entry` = `0x3A208` (= arcade `0x3A008` + relocation delta `0x000200`), which is the arcade's per-frame VBlank interrupt handler entry. This entry point **completely bypasses** the initialization path at `0x3A000` → `0x3AE86` → `0x3AF04`. The `lea` instruction at `0x03AF04` **never executes** during any Genesis boot or per-frame tick.

Because the `lea` never executes, A5 retains the value assigned by the Exodus emulator at power-on, which is `0xFFFFFFFF`. All A5-relative arcade reads and writes during game execution use `0xFFFFFFFF + offset` as the effective address. On the 68000's 24-bit address bus, these addresses resolve to ROM space (bytes 0–3 for small offsets). Writes to ROM are silently discarded by the Genesis bus. Reads return ROM content at the wrong addresses. The game's state-machine counters are written and immediately discarded; the game is stuck in the same sub-handler on every tick. No descriptor list entry is ever populated in WRAM. The BG hook never fires because the game never advances to game state 2 (attract mode). Inputs have no effect because the shadow input read addresses (A5 + fixed offsets) resolve to wrong locations.

**Single root cause**: The patched instruction at arcade `0x03AF04` (Genesis ROM `0x03B104`) is unreachable from the Genesis wrapper — the init path that contains it is never called. A5 is never set to `0xFF0000`.

**Single next correction**: Add `lea 0xFF0000, %a5` to `init_staging_state` in `apps/rastan-direct/src/main_68k.s` (runs once before the main loop) OR add it to `arcade_tick_logic` before the `jsr rastan_direct_arcade_tick_entry`. This sets A5 = `0xFF0000` in the Genesis WRAM base before the first arcade tick runs, replicating the effect the patched instruction would have had if the init path had been reached.

---

## 2. Inputs Audited

| Input | What was checked |
|-------|-----------------|
| `specs/rastan_direct_remap.json` | opcode_replace entry at `arcade_pc: 0x03AF04`; exact bytes |
| `build/rastan-direct/rastan_direct_patch_manifest.json` | manifest entry at `arcade_pc: 0x03AF04`; actual patched bytes; `rom_pc` value |
| `build/maincpu.disasm.txt` | full disassembly around `0x3AF04`, `0x3A000`, `0x3A008`, `0x3AE86`; all instructions that write to A5 register itself |
| `apps/rastan-direct/src/main_68k.s` | full source: `main_68k`, `init_staging_state`, `arcade_tick_logic`, `_VINT_handler`, `genesistan_hook_tilemap_plane_a` |
| `apps/rastan-direct/src/boot/boot.s` | vector table, `_start`, `_default_handler`, initial SSP/PC values |
| `docs/design/Andy_pc080sn_wram_write_path_diagnosis.md` | prior analysis confirming A5-relative write sites and root cause chain |
| `docs/design/Cody_a5_wram_base_redirect.md` | Cody's claimed implementation: bytes, files modified, verification performed |
| `docs/design/Andy_arcade_execution_reachability_vs_static_checkerboard.md` | prior PC range analysis; BG hook reachability |
| `dist/rastan-direct/rastan_direct_video_test_build_0008.bin` | verified bytes at `0x3A200`, `0x3A208`, `0x000000` vector table in actual built binary |

---

## 3. BG Producer Write-Site Analysis

### 3.1 A5 Register Set Point

The disassembly of `build/regions/maincpu.bin` contains exactly **one** instruction that assigns A5 to a base value:

| Arcade PC | Instruction | Genesis ROM PC (after +0x200) | Location in code |
|-----------|-------------|-------------------------------|-----------------|
| `0x03AF04` | `lea 0x10C000,%a5` (original) / `lea 0xFF0000,%a5` (patched) | `0x03B104` | Inside init routine `0x3AE86`, called ONLY from arcade reset entry `0x3A000` |

All other instructions that appear to write to A5 in the disassembly (`addaw`, `addal`, `subaw` at `0x3CE78`, `0x48536`, `0x4872A`, `0x4872E`, `0x48746`, `0x4874A`, `0x5CB78`, `0x5CD30`) are located in **data table regions** — their bytes are decoded as instructions by the disassembler but are not executed as code. The surrounding context in every case shows `.short` pseudoinstructions and irregular byte patterns characteristic of lookup tables, not subroutine prologues.

### 3.2 Descriptor List Write Sites (unchanged from prior diagnosis)

Sixteen descriptor list write instructions at arcade PCs `0x0502E4` through `0x050398` write `A5 + 0x1000` through `A5 + 0x103C`. With A5 = `0xFFFFFFFF`, these target `0xFFFFFFFF + 0x1000` = `0x00000FFF` (24-bit wrap: bit[23:0] of `0x100000FFF` = `0x000FFF`), which is in Genesis ROM space. All 16 writes are discarded.

### 3.3 dest_ptr and Strip Index Write Sites (unchanged)

All `A5 + 0x10A0` (BG dest_ptr), `A5 + 0x10A4` (FG dest_ptr), and `A5 + 0x10CA` (strip index) writes target ROM space when A5 = `0xFFFFFFFF`. All discarded.

---

## 4. Producer-State Write Reachability Analysis

### 4.1 The Patch Site is Unreachable from the Genesis Wrapper

The arcade binary structure around the relevant entry points:

```
Arcade ROM (before relocation)     Genesis ROM (after +0x200)
0x3A000: braw 0x3AE86              0x3A200: braw 0x3B086    <- INIT ENTRY (never called)
0x3A004: braw 0x3A080              0x3A204: braw 0x3A280    <- RESET MODE
0x3A008: oriw #0x0F00,%sr          0x3A208: oriw #0x0F00,%sr <- TICK ENTRY (called per frame)
  ...
0x3AE86: (init routine start)      0x3B086: (init routine)   <- only reached from 0x3A200
  ...
0x3AF04: lea 0x10C000,%a5 (patched)  0x3B104: lea 0xFF0000,%a5  <- NEVER REACHED
```

The Genesis wrapper entry point:
```
rastan_direct_arcade_tick_entry = 0x0003A208
```
(= arcade `0x3A008` + relocation delta `0x000200`)

The wrapper calls `0x3A208` directly. This enters the arcade's per-frame VBlank interrupt handler body. The initialization entry at `0x3A200` (= arcade `0x3A000`) is **never called** by any Genesis wrapper code.

### 4.2 Verification in Built Binary

The built binary `rastan_direct_video_test_build_0008.bin` confirms:
- `0x3A200`: `60 00 0E 84` = `braw 0x3B086` (the init entry; never called)
- `0x3A208`: `00 7C 0F 00` = `oriw #0x0F00,%sr` (the tick entry; called per frame)
- `0x000004..0x000007`: `00 00 02 02` = initial PC = `0x000202` = `_start`

`_start` calls `main_68k`, which calls `init_staging_state` then loops calling `arcade_tick_logic`. `arcade_tick_logic` calls `jsr rastan_direct_arcade_tick_entry` (`0x3A208`). There is no call to `0x3A200` anywhere in the Genesis wrapper code.

### 4.3 Patch Bytes Are Correct But Unreachable

The remap spec and manifest both contain the correct 6-byte replacement:

```
arcade_pc: 0x03AF04
original_bytes:    4BF90010C000  (lea 0x10C000,%a5)
replacement_bytes: 4BF900FF0000  (lea 0xFF0000,%a5)
```

The encoding `4BF9 00FF 0000` is the correct 68000 encoding for `lea 0xFF0000,%a5` (absolute long addressing, destination A5). The bytes are correct. The problem is not the encoding — it is that the instruction site is never executed.

---

## 5. Current State-Machine Loop Analysis

### 5.1 What the Tick Entry Does with A5 = 0xFFFFFFFF

At tick entry `0x3A208` (arcade `0x3A008`):
```
oriw #0x0F00,%sr              ; raise interrupt mask
clrw 0x350008                 ; hardware write (patched/ignored on Genesis)
movew %d0, 0x3C0000           ; VDP/hardware write
movew %a5@(2), %d0            ; READ game sub-state from A5+2
```

With A5 = `0xFFFFFFFF`:
- `%a5@(2)` = address `0xFFFFFFFF + 2` = `0x00000001` (24-bit address bus: `0xFFFFFFFF + 2 = 0x100000001` → lower 24 bits = `0x000001`)
- `0x000001` is an **odd byte address** for a word read → 68000 **Address Error exception**

### 5.2 Address Error and _default_handler

Genesis vector table entry for address error (vector 3) = `_default_handler = rte` at `0x000200`. The address error exception fires, `rte` pops the 6-byte exception frame, restoring PC to the instruction after the faulting `movew` and SR to the value at the time of the fault. Execution resumes past the faulting read with D0 holding whatever value it had before (garbage for game-state dispatch purposes).

### 5.3 Dispatch Outcome with Garbage D0

The subsequent dispatch logic reads `%a5@(0)` (main state) with A5 = `0xFFFFFFFF`. Address `0xFFFFFFFF + 0 = 0x00000000` → reads ROM[0..1] = `0x00FF` (high word of initial SSP `0x00FF0000` from the genesis header). Game main state = `0x00FF` = 255.

The dispatch reads the jump table with offset `255 * 2 = 510`. The table at `0x3A06C` has only 4 valid entries (8 bytes). Index 510 reads ROM beyond the table, getting some arbitrary byte from the arcade code. The `jmp %a0@` jumps to an arbitrary ROM address. This may execute some valid arcade subroutines that do A5-relative operations (all discarded), eventually returning through RTE/RTS back to the main loop.

### 5.4 State Never Advances

Within any state handler: writes such as `movew #1, %a5@(4)` (advance sub-sub-state) target address `0xFFFFFFFF + 4 = 0x00000003` (ROM, odd-aligned, address error → discarded). No state counter in WRAM is ever updated. The game replays the same control flow path on every frame. The PC snapshot at `0x46FD0894` (Exodus display) represents whatever code path the garbage-state dispatch happens to visit; it is within the relocated arcade ROM region but in a state-machine handler that never terminates cleanly.

---

## 6. Input Non-Effect Analysis

### 6.1 Shadow Input Read Path

Input shadow bytes live at Genesis WRAM addresses `0xFF0007`, `0xFF0009`, `0xFF000B` (etc.), patched from arcade I/O register reads. The relevant read for coin detection in the arcade tick is from `0x390007` (patched to the WRAM shadow).

### 6.2 Why Inputs Have No Effect

The arcade reads coin/start from the patched addresses, which correctly point to the WRAM shadow. The WRAM shadow is updated correctly by `rastan_direct_update_inputs` every frame. The reads themselves return the correct input values.

However, the input values are consumed via control flow like:
```
0x3AB96: btst #2, 0x390007   (patched to WRAM shadow)
0x3AB9E: bnes 0x3ABE0         (branch on coin bit)
```

If this branch is taken, it leads to a handler that does `movew #3, %a5@(0)` (transition to game state 3) — but this write targets `0x00000003` (ROM, odd address → address error, discarded). The state never transitions regardless of input. Even when inputs ARE read correctly, the resulting WRAM writes are discarded because A5 = `0xFFFFFFFF`.

**Inputs have no effect because A5 = `0xFFFFFFFF` causes all reactive state transitions (WRAM writes) to target ROM addresses, where they are silently discarded.**

---

## 7. Producer-State Status Analysis

### 7.1 Descriptor List

WRAM `0xFF1000`–`0xFF103F` (16 descriptor list entries) remains at the BSS-initialized value of `0x00000000` on every frame. The arcade's descriptor list population at `0x0502E4`–`0x050398` is never executed (requires game state 2, which is never reached), and even if executed, the writes would target ROM space with A5 = `0xFFFFFFFF`.

### 7.2 BG Hook

`genesistan_hook_tilemap_plane_a` is patched at arcade `0x055968` (Genesis `0x055B68`). This patch site is inside the BG strip producer call chain, reached via game state 2 → sub-state 2 → sub-sub-state 4 → `0x3A64C` → `jsr 0x4529C` → ... → `0x55948` dispatcher → `0x55950` `bsrw 0x55968`. Because the game never reaches state 2, the hook **never fires**. The `hook_plane_a_hits` counter in WRAM stays at `0`.

### 7.3 dest_ptr

`init_staging_state` writes `0x00C00000` to `ARCADE_FIX_DEST_BG` (`0xFF10A0`) and `0x00C08000` to `ARCADE_FIX_DEST_FG` (`0xFF10A4`). These writes are valid and WRAM-resident. However, the BG hook's dest_ptr range check (`0x00C00000 ≤ dest_ptr < 0x00C04000`) is never reached because the hook never fires. The arcade's own dest_ptr updates (A5 + `0x10A0`) target ROM space and are discarded.

**Producer-state status: the descriptor list is all-zero, the hook never fires, no tile data is ever staged.**

---

## 8. Root Cause

**The patched instruction at arcade `0x03AF04` (Genesis ROM `0x03B104`) is located inside the arcade's one-time power-on initialization routine (`0x3AE86`), which is only entered from the arcade's reset entry point (`0x3A000`, Genesis `0x3A200`). The Genesis wrapper calls the per-frame tick entry directly at `0x3A208` (arcade `0x3A008`), completely bypassing the initialization path. The `lea 0xFF0000,%a5` instruction never executes. A5 retains the Exodus power-on initial register value of `0xFFFFFFFF`. All A5-relative arcade reads and writes use `0xFFFFFFFF + offset` as the effective address; on the 68000's 24-bit bus, small positive offsets wrap to ROM addresses (0x00000N). Writes to ROM are silently discarded. Reads from ROM return arcade ROM data at wrong offsets, producing garbage game-state values. The game state machine is stuck: state-counter writes are discarded, sub-state never advances, game never reaches state 2 (attract mode), the BG hook never fires, the descriptor list in WRAM remains all-zero, and inputs have no effect because reactive WRAM writes are also discarded.**

The patch bytes in `rastan_direct_remap.json` are correct (`4BF900FF0000`). The bug is not the encoding. The bug is that the patch site (`0x03AF04`) is in dead code from the Genesis wrapper's perspective.

---

## 9. Single Next Correction

**Add `lea 0xFF0000, %a5` to `init_staging_state` in `apps/rastan-direct/src/main_68k.s`, immediately before the `clr.w frame_counter` at the start of the function body.**

This sets A5 to `0xFF0000` (Genesis WRAM base) before the first arcade tick is called. The effect is identical to what the patched instruction at `0x03AF04` would produce if the arcade init path were reached. With A5 = `0xFF0000`:

- All A5-relative game-state reads target WRAM (`0xFF0000+`), returning zero (WRAM BSS-cleared) on first tick — valid initial game state.
- All A5-relative game-state writes target WRAM — state counters advance correctly each frame.
- The game state machine progresses from state 0 → state 2 (attract mode) after the initialization sub-state sequence completes.
- Once in state 2, the BG hook fires at `0x055B68`.
- With descriptor list in WRAM populated by the arcade (when it runs the population code at `0x0502E4`–`0x050398` in state 2), the hook reads valid descriptor entries and stages tile data.

The existing patch at `0x03AF04` in `rastan_direct_remap.json` is **correct and must be kept** — it handles the case where the init path runs (e.g., if future development re-enables it) and is consistent with the design intent. The additional `lea` in `init_staging_state` is not a replacement but an additional guarantee.

**Note on absolute A5 writes**: The arcade init also contains absolute-address writes to `0x10D0A0` and `0x10D0A4` (hardcoded to the old arcade WRAM addresses). These writes also need patches in `rastan_direct_remap.json` to redirect them to `0xFF10A0` / `0xFF10A4`. Those patches are a **separate** follow-on item; fixing A5 initialization is the single blocking prerequisite.

---

## 10. What Must Not Be Changed Yet

| Item | Reason |
|------|--------|
| `specs/rastan_direct_remap.json` opcode_replace entry at `0x03AF04` | Correct bytes, correct target address — must be kept as-is |
| `genesistan_hook_tilemap_plane_a` implementation in `main_68k.s` | Already fully implemented; correct save/restore of A5 via `movem.l`; correct descriptor loop logic |
| `init_staging_state` writes to `ARCADE_FIX_DEST_BG` / `ARCADE_FIX_DEST_FG` | Correct; initializes `0xFF10A0` and `0xFF10A4` before arcade tick runs |
| BG hook patch at `arcade_pc: 0x055968` | Correct; verified in manifest at `rom_pc: 0x055B68` resolving to `genesistan_hook_tilemap_plane_a` |
| TC0040IOC / DIP shadow patches in `rastan_direct_remap.json` | All 31 opcode_replace entries are correct; do not modify |
| The relocation delta (`0x000200`) and whole-maincpu copy range | Verified correct in manifest; all 610 absolute ROM targets relocated |
| `_VINT_handler` implementation | Saves and restores all registers including A5 via `movem.l` — correct; must not change |

---

## 11. Final Verdict

| Question | Answer |
|----------|--------|
| BG producer write sites identified | YES — 16 desc list writes at `0x0502E4`–`0x050398`, all A5-relative |
| Producer-state write execution reachability analyzed | YES — unreachable because init path `0x3AE86` never runs |
| Current state-machine loop identified exactly | YES — stuck at garbage-state dispatch with A5 = `0xFFFFFFFF`; address errors on odd-address A5@(2) read; game never reaches state 2 |
| Input non-effect explained exactly | YES — reactive WRAM writes (`movew #N,%a5@(M)`) target ROM addresses; all discarded; state never transitions on input |
| Producer-state status determined exactly | YES — descriptor list all-zero; hook never fires; no tile data staged |
| Exact blocking condition identified | YES — A5 = `0xFFFFFFFF`; patched init instruction never executes because init path is bypassed |
| Single root cause | The patch at `0x03AF04` is in the unreachable arcade init path; Genesis wrapper calls per-frame tick `0x3A208` directly; `lea 0xFF0000,%a5` never executes; A5 = `0xFFFFFFFF` throughout all execution |
| Single next correction | Add `lea 0xFF0000, %a5` to `init_staging_state` in `main_68k.s` before the first arcade tick call |
| What-must-not-be-changed-yet defined | YES |
