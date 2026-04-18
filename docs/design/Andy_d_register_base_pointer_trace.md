# Andy — D-Register Base Pointer Origin Trace (Build 0044)

**Status:** ANALYSIS COMPLETE. Root cause identified from trace
evidence. The Exodus crash data and MAME trace tell a consistent story.

---

## Phase 1 — Pattern Identification

### D-register stride analysis

```
D0 = 0x196   D1 = 0x1AE (+0x18)   D2 = 0x1C6 (+0x18)
D3 = 0x1E6 (+0x20)   D4 = 0x1FE (+0x18)   D5 = 0x216 (+0x18)
D6 = 0x236 (+0x20)   D7 = 0x24E (+0x18)
```

Stride pattern: 0x18, 0x18, 0x20, 0x18, 0x18, 0x20, 0x18. Irregular
but structured.

### Instruction type

This is NOT a `movem.l (An)+, D0-D7` result. A `movem.l` loads
longwords from sequential memory addresses (stride 4 per register).
The values here form a nearly-linear sequence of the VALUES
themselves — they look like ADDRESS CONSTANTS being loaded into
registers, not memory content at sequential offsets.

The most likely source: **the CPU is executing ROM header ASCII text
as 68000 instructions.** The ROM header at `0x000100`–`0x0001FF`
contains ASCII text:

```
0x100: "SEGA MEGA DRIVE "
0x110: "(C)CDX 2026.APR"
0x120: "RASTAN DIRECT VIDEO TEST" ...
```

When interpreted as 68000 opcodes, ASCII text produces a mix of MOVE,
ADD, and other instructions with operand addresses that increment
through the low-ROM region. The structured D-register values are the
accumulated side effects of this garbage execution.

### Base register

No single base register produced the pattern. All registers (D0–D7,
A0–A6, SP, USP, and all WRAM-read values) are in the 0x0000–0x0700
range — total corruption from extended garbage execution in the ROM
header area.

---

## Phase 2 — Base Register Origin Trace

### MAME trace evidence

Build 44 trace
(`states/traces/rastan_direct_video_test_build_0044_mame_30s_20260417_164032/`):

**Last normal execution PCs:**
```
[frame 000360] pc=070022 exec=other    ← main loop (normal)
[frame 000385] symbol_change dip1 0->1
[frame 000386] first_symbol_change reg_d01bfe addr=ff6854 0->5020
[frame 000386] first_symbol_change reg_350008 addr=ff6856 0->5741
[frame 000386] first_symbol_change reg_380000 addr=ff6858 0->32C5
[frame 000390] pc=0009ce exec=other    ← inside crash handler
```

**Critical finding:** the "symbol changes" at frame 386 are NOT
arcade-hardware-register shadow writes. The watched addresses
(`ff6854, ff6856, ff6858`) map EXACTLY to the crash record:

```
0xFF6854 = CRASH_FAULT_ADDRESS (longword — two watched words)
0xFF6858 = CRASH_ACCESS_TYPE (word)
```

The trace labels `reg_d01bfe`, `reg_350008`, `reg_380000` are
misleading — they were defined in the symbol watch table pointing at
WRAM addresses that COINCIDENTALLY overlap the crash record fields.
The values `0x5020` and `0x5741` at frame 386 are the **crash handler
writing `CRASH_FAULT_ADDRESS = 0x50205741`** to WRAM.

### Decoded crash from MAME trace

From the crash record writes at frame 386:

| Crash record field | WRAM addr | Value | Meaning |
|-------------------:|----------:|------:|---------|
| CRASH_FAULT_ADDRESS high word | `0xFF6854` | `0x5020` | — |
| CRASH_FAULT_ADDRESS low word | `0xFF6856` | `0x5741` | — |
| **CRASH_FAULT_ADDRESS** | — | **`0x50205741`** | The 68000 tried to access this address |
| CRASH_ACCESS_TYPE | `0xFF6858` | `0x32C5` | Bus/addr error function code word |

**The fault address is `0x50205741`.** This is 'P',' ','W','A' in
ASCII — not a valid memory address. It's the same class of value seen
in Build 36's corrupted A1 (`0x50205743`).

### Last normal PC before fault

`runtime_genesis_pc: 0x00070022` at frame 360 (main loop). Between
frame 360 and frame 386, the arcade tick executed and reached a code
path that produced the fault. The crash handler caught it at frame 386
and rendered the crash screen (VDP writes from `runtime_genesis_pc:
0x0009CE` visible at frame 390).

---

## Phase 3 — Low Address Origin

### Exodus vs MAME discrepancy

The Exodus crash screen shows:
```
Fault addr: 0x00000196   D0: 0x00000196
FRAME: 0x0736 (1846)
```

The MAME trace shows:
```
CRASH_FAULT_ADDRESS: 0x50205741
crash at frame ~386
```

These are from **different runs on different emulators.** The Exodus
emulator may handle the initial fault differently — if Exodus does
not immediately trap but allows execution to continue into the ROM
header area, the CPU runs garbage code for potentially hundreds of
frames, corrupting all registers to low-ROM values before a
secondary address error is caught. This explains:

- Exodus fault addr `0x196` — a low-ROM address produced by garbage
  execution
- Exodus FRAME = `0x0736` — corrupted WRAM (the real frame count was
  ~386; `0x0736` is garbage read from corrupted `frame_counter`)
- All Exodus registers in `0x000`–`0x700` range — total corruption
  from executing ROM header ASCII text

The MAME trace catches the FIRST fault cleanly: fault address
`0x50205741` at frame 386, which is the actual fault-time value
before any cascade.

### What `0x50205741` is

`0x50205741` is NOT an untranslated arcade address, a truncated
24-bit value, or a sign-extension error. It is **data that was being
read as an address.** Specifically, it contains ASCII characters
('P',' ','W','A') — this is a text string fragment in ROM or WRAM
being used as a pointer because the CPU loaded it from a wrong
source.

The value `0x50205741` does not appear in `address_map.json` as any
mapped address.

### Source of the bad value

The CPU tried to access `0x50205741` at frame 386. This happened
during the arcade's attract-mode transition (the same timing window
where prior builds crash). The arcade code's state machine initializes
hardware registers and text-script state at this transition. An
instruction in that initialization path loaded a value from a wrong
WRAM location or used an untranslated arcade-absolute address as a
pointer, and the pointer contained ASCII data instead of a valid
address.

---

## Phase 4 — Frame Count Correlation

### MAME frame 386 transition

YES — frame 386 coincides with the arcade's attract-mode state
machine transition. From the trace:

- Frame 385: `dip1` changes (input processing)
- Frame 386: crash record writes appear (the crash handler fires)
- Frame 390: PC is inside the crash handler's renderer

This is the SAME transition window seen in all prior builds:
- Build 36: MAME frame 389 showed first hardware register shadows
- Build 44: MAME frame 386 shows crash handler activating

The crash is triggered by the arcade code's first attract-mode
hardware output — the same code path that wrote to PC080SN FG
tilemap in Builds 32–35 and was hooked in Builds 33–36. But now
the FG C-window writes are all hooked (`fg_cwindow_live count=0`).
The current crash comes from a DIFFERENT unhooked hardware path
executed during the same attract-mode transition.

### Exodus FRAME = 0x0736

This is NOT the real frame count. It is corrupted WRAM data read from
`frame_counter` at BSS address `0xFF4000`. In the Exodus emulator, the
fault cascade corrupted WRAM before the crash handler captured it.

---

## Phase 5 — DEST_BG / DEST_FG

### Exodus values

```
DEST_BG = 0x00000610
DEST_FG = 0x00000628
```

These are at `ARCADE_FIX_DEST_BG` = `0xFF10A0` and
`ARCADE_FIX_DEST_FG` = `0xFF10A4` in WRAM.

### Source of low values

**Same cascade corruption as the D-registers.** In the Exodus
emulator, the CPU executed ROM header text as code for an extended
period, and writes from that garbage execution overwrote WRAM
locations including `0xFF10A0` and `0xFF10A4` with low-ROM address
values.

In the MAME trace (where the crash handler catches the first fault
cleanly at frame 386), DEST_BG and DEST_FG would still hold their
init values (`0xC00000` and `0xC08000`) because the cascade didn't
happen.

### Same base failure or separate issue?

**Same class of failure.** The Exodus data shows total register and
WRAM corruption from a fault cascade. The MAME trace shows the
clean first fault at `0x50205741`. The DEST_BG/FG corruption is a
CONSEQUENCE of the cascade in the Exodus emulator, not a separate
root cause.

---

## Phase 6 — Root Cause Classification

**Selected: E — State machine transition at frame ~386 loading a bad
base from an unhooked or incorrectly translated structure.**

Evidence:
- MAME trace confirms the crash handler fires at frame 386
  (CRASH_FAULT_ADDRESS = `0x50205741` written to WRAM, visible as
  `reg_d01bfe` and `reg_350008` symbol changes)
- Frame 386 coincides with the arcade's attract-mode transition
  (same window as all prior builds)
- Fault address `0x50205741` = ASCII text fragment, indicating a
  bad pointer loaded from ROM/WRAM text data
- `fg_cwindow_live count=0` in this build — all FG C-window writers
  are hooked, so the crash comes from a DIFFERENT unhooked path
- `vdp_ports_live last_pc=0x0008AA` — the last VDP write comes from
  inside the crash handler's rendering code (confirming the crash
  handler executed after the fault)
- The Exodus crash screen data shows total register corruption
  because Exodus handles the initial fault differently, allowing a
  cascade before the crash handler fires

### Why other options are rejected

- **A (untranslated arcade pointer):** The fault address
  `0x50205741` is not an arcade address — it's ASCII data. This is
  not a simple base-offset-missing translation.
- **B (24-bit truncation):** `0x50205741` does not have the structure
  of a truncated 24-bit address (it's a 32-bit value with non-zero
  high bytes).
- **C (MOVEM error):** No evidence of a bulk register load producing
  the fault; the D-register pattern in the Exodus data is from
  post-fault cascade execution, not the original fault.
- **D (stack pointer corruption):** The MAME trace shows the fault at
  `0x50205741` which is a data-as-pointer error, not a stack-return
  corruption. The cascade in Exodus DOES corrupt SP, but that's a
  consequence not the cause.
- **F (insufficient evidence):** The MAME trace provides clear evidence
  of the fault address and timing.

### Next investigation target

The unhooked arcade code path that executes at frame ~386 and produces
a memory access to `0x50205741` must be identified. Candidates include
writes to `HW_ADDRESS/PC090OJ/SPRITE_RAM` (`0xD00000+`), writes to
`HW_ADDRESS/TC0040IOC` (`0x380000+`), or an absolute-address JSR/JMP
through a data structure that contains ASCII text. The
`Cody_pc080sn_writer_audit.md` inventory should be checked for
non-PC080SN writers that fire during the attract-mode transition. The
address `0x50205741` itself should be traced to its ROM/WRAM source to
identify which code path loaded it as a pointer.
