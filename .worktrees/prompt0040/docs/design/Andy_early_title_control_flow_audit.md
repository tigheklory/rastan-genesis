# Andy — Early Title Control Flow + Exception Transition Audit (Build 0036)

**Status:** ANALYSIS COMPLETE. Root cause identified. Pre-exception and
transition phases fully characterized.

---

## Phase 1 — Control Flow Timeline

| Frame | PC | A1 | A4 | E000 state |
|-------|----|----|----|----|
| IMG_01 | `0x0007125C` | `0xFFFFFFFF` | `0xFFFFFFFF` | Partially populated: `0xFFFF 0xFFFF 0xFFFF 0xFFFF` (uninitialized VRAM) |
| IMG_02 | `0x00070022` | `0x0003B2FB` | `0xFFFFFFFF` | All zero: `0x0000 0x0000 0x0000 0x0000` |
| IMG_03 | `0x00070022` | `0x0003C0BC` | `0xFFFFFFFF` | All zero: `0x0000 0x0000 0x0000 0x0000` |

**Last normal frame:** IMG_03 (`runtime_genesis_pc: 0x00070022` — wrapper
main loop, between `main_68k` at `0x070000` and `_VINT_handler` at
`0x07002a`).

**First exception frame:** IMG_04 (`runtime_genesis_pc: 0x00000200` — the
default exception handler (RTE instruction) at the preserved-vectors
segment).

---

## Phase 2 — Plane A Population Before Exception

**Answer: NO — Plane A (`0xE000`) is NOT populated with title-phase tilemap
data before the exception.**

Evidence:
- IMG_01: `0xE000` shows `0xFFFF` values — this is uninitialized VRAM
  captured during boot before `init_staging_state` clears Plane A (the
  screenshot was taken mid-initialization at PC=`0x0007125C`, inside the
  boot setup flow).
- IMG_02: `0xE000` = all zero (`0x0000 0x0000 0x0000 0x0000`). The
  `init_staging_state` Plane A clear (writing 2048 zeros to VRAM
  `0xE000`) has completed. No FG strip commits have populated it.
- IMG_03: `0xE000` = all zero (unchanged from IMG_02). The arcade tick
  has been running (A1 changed from `0x0003B2FB` to `0x0003C0BC`), but
  no tilemap data has reached VRAM Plane A.

The Plane A nametable contains only zeros throughout the pre-exception
window. No title text, score numbers, or structured tilemap content is
present.

---

## Phase 3 — A1 Progression vs VRAM

**Answer: YES — A1 progresses while `0xE000` remains empty.**

| | A1 | E000 |
|-|------|------|
| IMG_02 | `0x0003B2FB` | all zero |
| IMG_03 | `0x0003C0BC` | all zero |

A1 advances by `0x0DC1` (3521 bytes) between IMG_02 and IMG_03. These
A1 values (`0x0003B2FB`, `0x0003C0BC`) are `genesis_rom_offset` values
inside the relocated arcade code region (the `arcade_copy` segment
`[0x03B2A4, 0x03F128)`) — they are NOT `HW_ADDRESS/PC080SN/FG_TILEMAP`
addresses. A1 at these snapshots reflects the arcade tick's use of A1
as a general-purpose register during execution, not as an FG tilemap
destination pointer.

A4 = `0xFFFFFFFF` in both frames. The text-script state system uses A4
as its state block pointer; `0xFFFFFFFF` means the text-script state
has NOT been initialized. This confirms: the arcade has not yet reached
the text-rendering phase of its attract-mode state machine.

---

## Phase 4 — Write Path Staging

**Active stage: NONE (destination never reached).**

Evidence:
- A1 holds code/data pointers (genesis_rom_offset values), NOT FG
  tilemap hardware addresses. No text-script handler has been called
  yet (A4 = `0xFFFFFFFF`).
- `0xE000` is all zero in both IMG_02 and IMG_03 — no VBlank FG strip
  commits have fired (because `fg_row_dirty` is zero — no hooks have
  written to `staged_fg_buffer`).
- The arcade state machine is in its initialization countdown. From the
  Build 36 MAME trace, the transition to attract-mode output (first
  hardware register symbol changes) occurs at MAME frame 389. IMG_02
  and IMG_03 are captured BEFORE this transition.

No part of the text-rendering write path (destination selection → staged
writes → VBlank commit) has activated. The system is in pre-text-phase
idle.

---

## Phase 5 — Root Cause (Pre-Exception, IMG_01–03 Only)

**Selected: A — Destination never reached.**

Evidence:
- A4 = `0xFFFFFFFF` in all three pre-exception frames (IMG_01, IMG_02,
  IMG_03). A4 is the text-script state pointer; `0xFFFFFFFF` means it
  was never initialized by the attract-mode state machine.
- No FG tilemap writes have been committed to `0xE000` (all zero in
  IMG_02 and IMG_03).
- A1 holds genesis_rom_offset code pointers, not FG hardware addresses.
- The arcade's initialization countdown has not completed — the state
  machine hasn't reached the point where text-script handlers fire.

The title screen is not displayed before the exception because **the
arcade code has not yet progressed to its text-rendering phase**. The
initialization countdown runs for hundreds of frames before the first
text output is produced. An exception (from an unhooked hardware write
path) kills execution before that transition occurs.

---

## Phase 6 — Transition Into Failure

### PC transition

- IMG_03: `runtime_genesis_pc: 0x00070022` (normal main loop).
- IMG_04: `runtime_genesis_pc: 0x00000200` (default exception handler — `RTE` at the preserved-vectors segment entry).

### A1 corruption onset

- IMG_03: A1 = `0x0003C0BC` (valid genesis_rom_offset in arcade code region).
- IMG_04: A1 = `0x50205743` (INVALID — not a valid address in any
  mapped region; the upper bytes `0x5020` and `0x5743` appear to be
  data/text artifacts from executing through corrupt memory).

**A1 corruption first appears at IMG_04** — the same frame where PC
jumps to the exception handler.

### First non-zero E000

- IMG_03: `0xE000` = all zero.
- IMG_04: `0xE000` = partially populated: `0x0000 0x0011 0x5020 0x5741`.

**First non-zero `0xE000` content appears at IMG_04** — coinciding with
the exception transition.

### First observable change

**The first observable change that coincides with execution leaving
normal flow is the simultaneous appearance of:**

1. PC = `0x00000200` (exception handler)
2. A1 = `0x50205743` (corrupted register)
3. Non-zero `0xE000` content (`0x0011 0x5020 0x5741` pattern)

These all appear together at IMG_04. No intermediate state between
"normal execution with zero E000" and "exception with corrupted A1
and populated E000" is captured.

---

## Phase 7 — Corruption Propagation

### Nametable values in `0xE000`

From IMG_05 nametable extraction (32 entries starting at `0xE00A`):

Repeating 4-entry pattern: `0x0000, 0x0011, 0x5020, 0x5741`.

Decoded:
- `0x0000`: tile_index=0x000, pal=0, no flip (blank tile)
- `0x0011`: tile_index=0x011, pal=0, no flip (tile 17)
- `0x5020`: tile_index=0x020, **Vflip=1**, **pal=2** (tile 32 with V-flip and palette 2)
- `0x5741`: tile_index=0x741, **Vflip=1**, **pal=2** (tile 1857 with V-flip and palette 2)

### Correlation with A1 = `0x50205743`

**YES — the nametable values are directly derived from the corrupted
A1 register value.**

A1 = `0x50205743`. Breaking this into 16-bit words:
- High word: `0x5020`
- Low word: `0x5743`

The nametable shows `0x5020` as a repeating entry. The value `0x5741`
(which appears in the nametable) is 2 less than `0x5743` (A1's low
word) — likely due to a word-aligned address variation or a prior
iteration's write.

The VDP Port Monitor from IMG_05 confirms direct writes of these
values:
```
DP Write: 0x0011
DP Write: 0x5020
CP Write: 0x5741
DP Write: 0x0011
DP Write: 0x5020
```

### VRAM writes reflect corrupted state

**YES.** The VDP data-port writes (`0x0011`, `0x5020`, `0x5741`) are
the exact values appearing in the `0xE000` nametable. These values
contain fragments of the corrupted A1 register (`0x50205743`). The VDP
port monitor shows these values being actively written during the
exception-loop state.

### Stack overflow confirmation

SSP progression across IMG_04–07:
- IMG_04: `0x00FC3C62`
- IMG_05: `0x00FB49FC`
- IMG_06: `0x00F9E69E`
- IMG_07: `0x00F8AC1A`

Each frame shows SSP decreasing by ~60K–80K bytes. The default
exception handler at `0x000200` is `RTE` (return from exception), which
pops SR+PC from the stack and returns to the faulting instruction. The
faulting instruction causes the same exception again, pushing SR+PC
back to the stack. This infinite exception-RTE loop consumes stack
space rapidly.

By IMG_07, PC has become `0x50205759` — the CPU is now executing from
the corrupted A1-like address range (stack overflow has corrupted the
return address on the stack). The system is in irreversible failure.

---

## Final Conclusion

The title screen is not displayed because the arcade state machine
never reaches its text-rendering phase before an unhooked hardware
write (outside the FG tilemap range) triggers an exception. The
exception handler (`RTE` at `runtime_genesis_pc: 0x000200`) creates an
infinite loop that corrupts registers (A1 = `0x50205743`), overflows
the stack (SSP decreasing by ~60K per captured frame), and leaks
corrupted register values into VDP writes (`0x5020`, `0x5741`
nametable entries derived from the corrupted A1). These garbage
nametable entries populate `0xE000` and produce the visible
structured-but-wrong tile patterns on screen.

The next investigation target is the unhooked hardware write that
triggers the initial exception — it occurs between IMG_03 (normal,
PC=`0x00070022`) and IMG_04 (exception, PC=`0x00000200`). Candidates
include writes to `HW_ADDRESS/PC090OJ/SPRITE_RAM` (`0xD00000+`),
`HW_ADDRESS/TC0040IOC` (`0x380000+`), or other unmapped arcade
hardware addresses. Identifying and hooking this write path would
allow execution to survive past the initialization countdown and
reach the text-rendering phase.
