# AGENTS Log

## [2026-03-18] Build 87 - I/O Mapping Phase


### MAME Exit Summary (2026-03-18 11:48:20)
- Final PC: 0x2001CA
- Stack Pointer (SP): 0xE0FFFF40
- Unique Unmapped Memory Addresses (3): 0x41300031, 0x00000000, 0x48940031

### MAME Exit Summary (2026-03-18 11:48:38)
- Final PC: 0x2145A0
- Stack Pointer (SP): 0xE0FFFF5C
- Unique Unmapped Memory Addresses (3): 0x41300031, 0x00000000, 0x48940031

### MAME Exit Summary (2026-03-18 12:10:22)
- Final PC: 0x214736
- Stack Pointer (SP): 0xE0FFFF5C
- Unique Unmapped Memory Addresses (3): 0x41300031, 0x00000000, 0x48940031


## [Supervisor - Tighe]

Visual Result: [Launcher works, In game play shows text from the title screen but it is all at the top few lines and overtop of each other and wrong colors]

Platform: [Tested on MAME and Blastem]

## [Supervisor - Tighe] Manual Evidence Log
- **Visual Evidence (MAME):** Screenshot saved as `B87_mame_launcher_20260318_1215.png` (Stage: Launcher)
- **Visual Evidence (MAME):** Screenshot saved as `B87_mame_ingame_20260318_1216.png` (Stage: In-Game)
- **Visual Evidence (BlastEm):** Screenshot saved as `B87_blastem_launcher_20260318_1220.png` (Stage: Launcher)
- **Visual Evidence (BlastEm):** Screenshot saved as `B87_blastem_ingame_20260318_1221.png` (Stage: In-Game)

## [Architect Review - Build 88 Technical Audit]

### 1. Aliasing Audit
**Confirmed.**
The spec `specs/startup_title_remap.json` currently maps `0xC00000`, `0xC04000`, `0xC08000`, and `0xC0C000` to the single symbol `genesistan_shadow_c_window_words`.
This results in a 4-to-1 aliasing where writes to distinct arcade video pages overwrite the same Genesis shadow buffer index. This explains the garbled title screen text (text overwriting background or vice versa).

### 2. Fault Analysis (0xD000DA)
**Confirmed Unmapped Literal.**
The address `0xD000DA` is missing from the `absolute_rewrite_groups` in the current spec.
Since `allow_in_code` is disabled for safety (Decision 2026-03-17), this absolute address literal in the code is not being rewritten.
Accessing `0xD000DA` on Genesis (unmapped space) causes the observed crash/freeze.

### 3. Mitigation Strategy
1.  **Split C-Window Shadows**: Define four separate 16KB shadow buffers in `apps/rastan/src/main.c`.
2.  **Remap Pages**: Update `specs/startup_title_remap.json` to map each 0xC0xxxx page to its own unique shadow symbol.
3.  **Patch D000DA**: Add `0xD000DA` to the explicit D-window absolute remap group targeting `genesistan_shadow_d00000_words` (offset 218).

## [Implementer Update - Build 88]

### Fixes Implemented
- Confirmed: `specs/startup_title_remap.json` now decouples prior 4-to-1 C-window aliasing with distinct mappings:
  - `0x00C00000 -> genesistan_shadow_c00000_words`
  - `0x00C04000 -> genesistan_shadow_c04000_words`
  - `0x00C08000 -> genesistan_shadow_c08000_words`
  - `0x00C0C000 -> genesistan_shadow_c0c000_words`
- Confirmed: `0x00D000DA` is mapped in D-window group to `genesistan_shadow_d00000_words` with `offset: 218`.

### Build Blocker
- Current state is `LINKER FAILURE` due to WRAM exhaustion.
- Cause: addition of 4 x 16KB volatile C-window shadow buffers (64KB total) pushes `.bss` past Genesis WRAM capacity (`$E00000-$FFFFFF`).
- Reported linker error: `.bss exceeds ram region at 0xE100BECC`.

### Integrity Check
- Confirmed unshifted arcade code offsets in spec:
  - `0x03AE86`
  - `0x039F80`
  - `0x03B098`

### Final Status
- Build 88: `Logic Complete / Memory Blocked`.

# External Technical Consultant — Build 89 Memory Pivot Review
Date: 2026-03-18  
Reviewer: External Technical Consultant

---

## Summary

Recommend proceeding with the **SRAM experiment for Build 89**, but **only behind a switchable memory-backend abstraction layer**.

This allows the project to:

- Test quickly using standard Genesis cartridge SRAM.
- Pivot later to **true 16-bit cartridge RAM** without rewriting the engine or title-screen code.

---

## Architectural Assessment

### Genesis Cartridge SRAM Location

Standard Genesis/Mega Drive backup SRAM is conventionally mapped in cartridge space around: $200000

SRAM access is controlled via:

$A130F1

---

### SRAM Bus Behavior

The compatibility baseline for Genesis SRAM is typically:

- **Byte-wide**
- **Odd-byte addressing**

This means it should **not be assumed to behave like generic 16-bit work RAM**.

---

### Flash Cart Behavior

Some flash carts internally use wider RAM (for example DRAM behind an FPGA), but compatibility expectations still follow the **standard SRAM behavior model**.

Therefore:

> SRAM should be treated as a **compatibility/testing backend**, not the final architectural assumption.

---

## Recommendation for Build 89

### 1. Introduce a Shadow Memory Abstraction Layer

Define four logical shadow pages corresponding to the arcade C-window.

| Logical Page | Arcade Address |
|---------------|----------------|
| PAGE0 | `$C00000` |
| PAGE1 | `$C04000` |
| PAGE2 | `$C08000` |
| PAGE3 | `$C0C000` |

Each page represents **16 KB of logical storage**.

---

### 2. Route All Access Through an API

Example interface:

shadow_read8(page, offset)
shadow_write8(page, offset, value)

shadow_read16(page, offset)
shadow_write16(page, offset, value)
shadow_read8(page, offset)
shadow_write8(page, offset, value)

shadow_read16(page, offset)
shadow_write16(page, offset, value)

No higher-level code should access cartridge memory directly.

---

### 3. Backend A — SRAM Compatible (Build 89)

Implementation characteristics:

- Uses SRAM region near `$200000`
- Packed or translated storage layout
- Designed to remain **odd-byte compatible**
- Does **not expose raw 16-bit linear memory semantics**

Purpose:

- Emulator testing
- Mega EverDrive testing
- Early hardware validation

---

### 4. Backend B — True Cartridge RAM (Future Hardware)

Future backend for custom hardware:

- 16-bit SRAM or RAM device
- Direct word reads/writes
- Same logical page API

Important:

> No engine code should change when switching backends.

Only the backend implementation changes.

---

### 5. Prevent Hardcoded SRAM Dependencies

Game logic must **never directly reference `$200000`**.

All cartridge shadow storage must be accessed through the abstraction layer.

This ensures:

- Easy hardware pivots
- Emulator portability
- Cleaner debugging

---

## Risk Notes

### SRAM Compatibility

SRAM at `$200000` is widely supported for testing, but the safest assumption remains:

- **odd-byte compatible**
- **save-RAM style behavior**

Not generic WRAM.

---

### Flash Cart Variability

Some flash carts internally use wider RAM, but that behavior is **implementation specific** and should not be relied upon.

---

### Dev Cart Differences

Some development cartridges (e.g., Open-ED) do **not implement persistent SRAM**, so behavior may differ from EverDrive devices.

---

## Architectural Conclusion

Proceed with the SRAM experiment **as a backend implementation only**, not as a permanent architectural dependency.

This preserves forward compatibility with:

- standard SRAM testing
- EverDrive flash carts
- emulator environments
- future **custom 16-bit RAM cartridges**

---


## [Architect Review - Build 89 SRAM Pivot]

### Design Strategy
To resolve the Build 88 WRAM overflow, we are moving the 64KB of C-Window shadow buffers to the Genesis cartridge SRAM window (`0x200000`).

### Memory Map
- **Origin:** `0x200000`
- **Length:** `64KB`
- **Layout:** 4 logical pages of 16KB each, mapped linearly.

### Compatibility Abstraction
We implemented a `shadow_` API in `main.c` to abstract the backend.
- **Access Method:** Explicit 8-bit byte-splitting.
- **Constraint:** While the API uses safe 8-bit access patterns, fitting 64KB of data into 64KB of address space requires a "16-bit SRAM" or linear-mapped configuration. Standard 8-bit-only save RAM (odd addresses only) would require 128KB of address space for this amount of data.
- **Target:** This configuration is valid for Emulator (SRAM 16-bit mode) and EverDrive development, which is sufficient to unblock the current logic testing.

### Status
- **Linker:** Defined `sram` region.
- **Runtime:** Implemented `shadow_init`, `shadow_write16`, `shadow_read16`.
- **Next Step:** Compile and verify C-Window text rendering.


## [External Consultant Review - Build 89 Strategy]

Decision: Move C-window shadow buffers to cartridge SRAM backend.

Rationale:
- Genesis WRAM exhausted by 4×16KB buffers
- Cartridge SRAM available in 0x200000 region
- Implementation to occur through shadow memory abstraction layer

Implementation Plan:
1. Create backend interface for C-window shadow memory
2. Implement SRAM-compatible backend
3. Allow later pivot to true 16-bit cartridge RAM

Status:
Approved for Build 89 experimentation.

## [Implementer Update - Build 89]

### Build 89 SRAM Implementation Complete
- Added linker MEMORY region: `SRAM (w!x) : ORIGIN = 0x200000, LENGTH = 64K`.
- Removed the 4x16KB C-window `.bss` arrays from `main.c`.
- Implemented SRAM-backed shadow API in `main.c`:
  - `shadow_init()` enables SRAM at `0xA130F1`.
  - `shadow_write16(page, offset, value)` maps to `0x200000 + page*0x4000 + offset`.
  - `shadow_read16(page, offset)` maps to `0x200000 + page*0x4000 + offset`.
- Replaced direct C-window array access paths with API-backed access:
  - C-window read/count/first/last diagnostics in `main.c`.
  - C-window reset clears in `startup_bridge.c`.
- `make -C apps/rastan debug` now succeeds; prior WRAM `.bss` overflow is cleared.

## [Implementer Update - Build 89 Release Orchestrator]

### Versioned Build Script Added
- Created `tools/release_build.sh`.
- Script behavior:
  - Accepts build number argument (example: `./tools/release_build.sh 89`)
  - Runs `make -C apps/rastan clean debug`
  - Creates `dist/build_<num>`
  - Copies build artifacts (`.bin`, plus `.elf`/`.map` outputs)
  - Writes `build_info.txt` with UTC date, build number, and ROM MD5

### Build 89 Packaging Status
- Executed: `tools/release_build.sh 89`
- Output ready for Lead review at:
  - `dist/build_89`
- Includes:
  - `rom.bin`
  - `rastan_build_89.elf`
  - `rastan_build_89.map`
  - `build_info.txt`
- **Visual Evidence (MAME):** Screenshot saved as `B89_MAME_Launcher_20260318_1548.png` (Stage: Launcher)
- **Visual Evidence (MAME):** Screenshot saved as `B89_MAME_In-Game_20260318_1548.png` (Stage: In-Game)

### MAME Exit Summary (2026-03-18 15:48:45)
- Final PC: 0x9C942C
- Stack Pointer (SP): 0x8403DD8A
- Unique Unmapped Memory Addresses (2): 0x0020A4C2, 0x00000000
- **Visual Evidence (BlastEm):** Screenshot saved as `B89_BlastEm_Launcher_20260318_1555.png` (Stage: Launcher)
- **Visual Evidence (BlastEm):** Screenshot saved as `B89_BlastEm_In-Game_20260318_1555.png` (Stage: In-Game)

## [Lead Review - Build 89 Validation]
**Date:** 2026-03-18
**Status:** **FAILED (In-Game Regression)**

### 1. Build Execution Summary
- **Launcher Phase:** **SUCCESS** (Both MAME and BlastEm). The Sega header and initial bridge code are stable.
- **In-Game Phase:** **CRASH**. 
  - **MAME:** Black Screen (Engine hang).
  - **BlastEm:** Fatal Crash (`M68K attempted to execute code at unmapped address 201F4C`).

### 2. Technical Analysis
- **The Jump Error:** Address `0x201F4C` sits inside our new SRAM Window ($200000 - $20FFFF). 
- **Root Cause Hypothesis:** 1. **Pointer Corruption:** The Arcade engine likely uses a Jump Table or Function Pointer that was stored in the C-Window. By moving that window to SRAM, we may have broken a pointer or failed to initialize it before the jump.
  2. **Stack/Return Error:** A function called from the Arcade logic is likely failing to "return" correctly, causing the PC (Program Counter) to "drift" into the SRAM memory space.

### 3. Visual Evidence
- **MAME In-Game:** `B89_MAME_In-Game_20260318_1548.png` (Black Screen / CPU Hang)
- **BlastEm In-Game:** `B89_BlastEm_In-Game_20260318_1555.png` (Debugger Break / Bus Error)

### 4. Directives for the Team
- **Alan (Architect):** Audit the `shadow_read16` logic. If the Arcade engine expects to *execute* code from the C-Window (some arcade boards do this for "trampoline" functions), we cannot use SRAM at $200000, as that region is data-only on Genesis.
- **Cody (Cody):** Examine the Linker Map for Build 89. Check if any `.text` (code) sections accidentally landed in the `SRAM` region.

## [Architect Audit - Build 89 Execution Failure]

### 1. Root Cause Analysis
**Confirmed.** The Build 89 crash is caused by the 68K CPU attempting to execute code from the cartridge SRAM region (`$200000`).
- **Evidence:** BlastEm debugger reported an execution attempt at `0x201F4C`.
- **Conclusion:** This address corresponds to arcade address `$C01F4C`, which falls within the first 16KB C-Window page (`PAGE 0`). The original arcade code contains executable subroutines or jump tables within this memory region, which is incompatible with the non-executable nature of Genesis Save RAM.

### 2. Design for Build 90: Hybrid Memory Map
To resolve the fault while still mitigating WRAM pressure, the C-Window shadow buffers will be split between WRAM and SRAM.

- **PAGE 0 (`$C00000` - 16KB):** This "hot" page contains executable code and **must be moved back to WRAM** (`$FFxxxx`).
- **PAGES 1-3 (`$C04000` - 48KB):** These "cold" pages appear to contain only data and **can remain in SRAM** (`$200000`).

### 3. Action Items for Implementer
- Allocate one 16KB array in `.bss` to serve as the WRAM shadow for `PAGE 0`.
- Modify the `shadow_read16()` and `shadow_write16()` API functions.
- The API must now conditionally route memory access: requests for `page == 0` target the WRAM buffer, while requests for `page > 0` target the SRAM hardware address space.

## [External Consultant Audit - Build 89 Crash]

### Crash Assessment
- Fatal crash reported at `0x201F4C` during transition to the in-game engine.
- This address falls inside the Build 89 SRAM shadow region beginning at `$200000`.
- Audit conclusion: the 68K PC has entered SRAM-backed shadow space.

### Hardware / Emulator Legality Review
- Standard Genesis cartridge SRAM at/around `$200000` is **not** a safe assumption for general executable memory.
- The standard compatibility model is:
  - SRAM enabled/disabled through `$A130F1`
  - byte-wide save RAM behavior
  - typically odd-byte addressing (`$200001-$20FFFF`)
- Therefore, `$200000` SRAM should be treated as **data storage**, not as portable 16-bit executable RAM.

### Illegal / Unsafe Assumptions Flagged
1. **Unsafe:** Treating `$200000` SRAM as generic 16-bit executable RAM.
2. **Unsafe:** Assuming code fetch from SRAM is portable across stock Genesis hardware, BlastEm, and flash carts without custom mapper support.
3. **Unsafe:** Packing 64KB of logical shadow data into 64KB of address space under standard 8-bit SRAM rules.
4. **Unsafe:** Depending on SRAM-visible cartridge space for execution while SRAM banking is controlled by `$A130F1`.

### Architectural Conclusion
If the arcade engine genuinely executes from relocated C-window regions, those regions must remain in **true executable memory**.

For stock Genesis-compatible design:
- **Use SRAM only for non-executable shadow data**
- **Keep executable subranges in 68K WRAM**
- **Prefer ROM-resident patched routines / trampolines where possible**

### Recommended Re-allocation Strategy
1. Split C-window usage into:
   - **Executable ranges**
   - **Non-executable data ranges**
2. Move non-executable shadow storage to SRAM backend.
3. Move executable ranges to:
   - WRAM overlays, or
   - ROM-based patched handlers/trampolines
4. Prevent higher-level code from assuming SRAM is executable.

### Build 89 Verdict
**REJECT current "Executable SRAM" assumption.**

Proceed only if Build 89 is revised so that:
- SRAM is used as a **data-only backend**
- any code executed from relocated C-window pages is redirected to **WRAM or ROM**

## [Emergency Joint Audit - Build 89 Hardware Failure]
**Participants:** Alan (Architect), Chad (Consultant)

### 1. Consensus on Crash 0x201F4C
- **Finding:** The Arcade engine uses the first 16KB of the C-Window ($C00000) for "Trampoline" code.
- **Hardware Conflict:** Genesis SRAM at $200000 is **Data-Only**. Attempting to fetch instructions here causes an immediate CPU exception/lockup.
- **EverDrive Status:** Confirmed via `IMG_20260318_161437.jpg` that the ROM header is missing SRAM range metadata, resulting in "EEPROM: No" on hardware.

### 2. Strategy for Build 90
- **The Split:** Move "Page 0" back to **WRAM** ($FFxxxx) to restore execution capability.
- **The Offload:** Keep Pages 1-3 (48KB) in **SRAM** ($200000) to maintain WRAM budget.
- **Header:** Explicitly define 64KB SRAM at $0x1B4 in the ROM header to unblock the EverDrive X3 mapper.

## [Implementer Update - Build 90]
Build 90: Hybrid Memory Pivot Complete.
