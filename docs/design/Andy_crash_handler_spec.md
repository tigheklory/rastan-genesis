# Andy — First-Fault Crash Handler Design Spec (Build 0038)

**Status:** SPEC COMPLETE. Ready for Cody. Zero design decisions remaining.

---

## Phase 1 — Current Failure Mode

### What `_default_handler` does today

`apps/rastan-direct/src/boot/boot.s:38–39`:
```asm
_default_handler:
    rte
```

Single `rte` instruction. Returns to the faulting instruction, which
re-faults immediately, producing an infinite exception–RTE–exception
loop.

### Which vectors currently point to `_default_handler`

From `boot.s:12–19`:

```asm
.rept 28
.long _default_handler    ; vectors 2–29 (28 entries)
.endr
.long _VINT_handler       ; vector 30 (VBlank, 0x78)
.long _default_handler    ; vector 31 (external IRQ level 7)
.rept 32
.long _default_handler    ; vectors 32–63 (TRAP 0–15 + unassigned)
.endr
```

Total: **60 vectors** point to `_default_handler` (vectors 2–29, 31,
32–63). Only vector 30 (`_VINT_handler`) is different.

### Why `rte` causes cascading corruption

Proven from Build 36 IMG_03→IMG_04 transition
(`Andy_early_title_control_flow_audit.md`):

1. First fault fires (unhooked hardware write to unmapped address)
2. CPU pushes exception frame to stack: SR + PC (6 bytes for standard,
   14 bytes for bus/address error)
3. CPU vectors to `_default_handler` at 0x000200
4. `rte` pops SR + PC → returns to faulting instruction
5. Same instruction re-faults immediately → pushes another frame
6. Each cycle: stack grows by 6–14 bytes; SSP decreases monotonically
7. Observed SSP progression: `0xFC3C62 → 0xFB49FC → 0xF9E69E →
   0xF8AC1A` — ~60K consumed per captured frame
8. Corrupted register values (A1=`0x50205743`) leak into VDP writes
9. Stack underflows into non-WRAM space; return addresses become
   corrupted → PC escapes to `0x50205759` → irreversible failure

---

## Phase 2 — Exception Coverage

Every vector currently routing to `_default_handler` in `boot.s` MUST
be replaced with a crash stub. Missing ANY vector is a design failure.

### Vectors requiring crash stubs (all 60)

| Vec | Offset | Name | Stub label |
|----:|-------:|------|------------|
| 2 | 0x08 | Bus error | `_crash_stub_bus_error` |
| 3 | 0x0C | Address error | `_crash_stub_address_error` |
| 4 | 0x10 | Illegal instruction | `_crash_stub_illegal` |
| 5 | 0x14 | Zero divide | `_crash_stub_zero_divide` |
| 6 | 0x18 | CHK | `_crash_stub_chk` |
| 7 | 0x1C | TRAPV | `_crash_stub_trapv` |
| 8 | 0x20 | Privilege violation | `_crash_stub_privilege` |
| 9 | 0x24 | Trace | `_crash_stub_trace` |
| 10 | 0x28 | Line 1010 | `_crash_stub_line_a` |
| 11 | 0x2C | Line 1111 | `_crash_stub_line_f` |
| 12–14 | 0x30–0x38 | Reserved | `_crash_stub_reserved_NN` (3 stubs) |
| 15 | 0x3C | Uninitialized IRQ | `_crash_stub_uninit_irq` |
| 16–23 | 0x40–0x5C | Reserved | `_crash_stub_reserved_NN` (8 stubs) |
| 24 | 0x60 | Spurious IRQ | `_crash_stub_spurious` |
| 25 | 0x64 | IRQ level 1 | `_crash_stub_irq1` |
| 26 | 0x68 | IRQ level 2 | `_crash_stub_irq2` |
| 27 | 0x6C | IRQ level 3 | `_crash_stub_irq3` |
| 28 | 0x70 | IRQ level 4 (H-blank) | `_crash_stub_irq4` |
| 29 | 0x74 | IRQ level 5 | `_crash_stub_irq5` |
| 30 | 0x78 | IRQ level 6 (V-blank) | **`_VINT_handler`** — NOT replaced |
| 31 | 0x7C | IRQ level 7 (NMI) | `_crash_stub_irq7` |
| 32–47 | 0x80–0xBC | TRAP #0–#15 | `_crash_stub_trap_NN` (16 stubs) |
| 48–63 | 0xC0–0xFC | Unassigned | `_crash_stub_unassigned_NN` (16 stubs) |

**Simplification for implementation:** vectors 12–23 (reserved),
48–63 (unassigned), and IRQ levels 1–5 can share a single
`_crash_stub_other` stub that loads a generic vector ID. Only the
diagnostically important vectors (2–11, 24, 31, TRAP 0–15) need
unique stubs. This reduces the unique-stub count from 60 to ~30
while still covering every vector.

Cody's choice: either all-unique stubs (maximum diagnostic precision)
or grouped stubs for low-value vectors. Andy recommends all-unique for
vectors 2–11 and TRAP #0–#15, grouped for the rest. **Total unique
stubs: 28 minimum.**

---

## Phase 3 — Handler Entry Design

### Per-vector stub pattern

```asm
_crash_stub_bus_error:
    moveq   #2, %d0
    bra.w   _crash_common

_crash_stub_address_error:
    moveq   #3, %d0
    bra.w   _crash_common

_crash_stub_illegal:
    moveq   #4, %d0
    bra.w   _crash_common
; ... etc for every covered vector
```

**Why `moveq` + `bra.w`:**
- `moveq` does NOT modify the stack or any address register. It writes
  only D0 (2-byte opcode).
- `bra.w` does NOT push a return address (unlike `bsr`). Stack remains
  untouched.
- The exception frame at SP is preserved exactly as the CPU left it.
- No WRAM writes occur in the stub. The vector number is passed to
  `_crash_common` via D0 and written to WRAM only AFTER the lockout
  check passes. This guarantees that a re-entrant fault in the stub
  itself cannot corrupt the crash record.

**D0 sacrifice:** D0 is intentionally clobbered by the stub to carry
the vector number. The fault-time value of D0 is NOT captured anywhere.
`CRASH_D0` in the crash record will contain the vector number, not the
register's value at the time of the fault. All other registers
(D1–D7, A0–A6) reflect fault-time state. This is an accepted
trade-off: vector identification is more valuable than one data
register's pre-fault content.

### Common handler prologue

```asm
_crash_common:
    move.w  #0x2700, %sr           ; 1. mask all interrupts
    move.l  %sp, %a0               ; 2. preserve frame pointer BEFORE any SP change
    tst.b   CRASH_ACTIVE_FLAG      ; 3. check lockout
    bne.s   .Lminimal_halt         ; 4. already crashing — halt immediately
    move.b  #1, CRASH_ACTIVE_FLAG  ; 5. set lockout — BEFORE any WRAM writes
    move.b  %d0, CRASH_EXCEPTION_TYPE  ; 6. NOW safe to write vector id to WRAM
    ; ... Phase 4 frame decode, Phase 5 WRAM store, Phase 7 render ...
.Lminimal_halt:
    stop    #0x2700
    bra.s   .Lminimal_halt
```

### Halt sequence

```asm
.Lcrash_halt:
    stop    #0x2700
    bra.s   .Lcrash_halt
```

`stop #0x2700` halts the CPU until an interrupt arrives. With SR =
0x2700 (all interrupts masked), no interrupt can wake it. The `bra.s`
is a safety net in case an NMI (level 7, which cannot be masked)
fires.

---

## Phase 4 — Exception Frame Decoding

**All reads via `%a0` (copied from `%sp` at entry).**

### Standard frame (vectors 4–11, TRAP, etc.)

```asm
; %a0 = SP at exception entry
move.w  0(%a0), %d1     ; stacked SR
move.l  2(%a0), %d2     ; stacked PC (address of faulting instruction)
```

Frame size: 6 bytes. SP after exception entry = pre-exception SP − 6.

### Bus error / address error extended frame (vectors 2–3, 68000 ONLY)

```asm
; %a0 = SP at exception entry
;   +0: additional info word (R/W, I/N, function code) — unreliable on 68000
;   +2: access address (longword) — RELIABLE
;   +6: instruction register (word) — unreliable on 68000
;   +8: stacked SR (word)
;  +10: stacked PC (longword) — RELIABLE
```

**IMPORTANT: 68000 bus/address error frame layout differs from the
standard frame.** The SR and PC are at DIFFERENT offsets.

```asm
; Bus/address error frame decode:
move.w  0(%a0), %d5      ; access type / function code (unreliable)
move.l  2(%a0), %d4      ; access address (reliable — the fault address)
move.w  6(%a0), %d3      ; instruction register (unreliable)
move.w  8(%a0), %d1      ; stacked SR
move.l  10(%a0), %d2     ; stacked PC
```

Frame size: 14 bytes.

### Runtime frame-type selection (explicit branch on D0)

The handler branches on the vector number still in D0 at this point
(D0 has not been clobbered since the stub wrote it and the prologue
preserved it through the lockout sequence):

```asm
    ; D0 = vector number (from stub, still live)
    ; A0 = original SP (exception frame pointer)

    cmpi.b  #3, %d0
    bhi.s   .Lstandard_frame       ; vectors > 3 → standard 6-byte frame

    ; Bus error (2) or address error (3) — extended 14-byte frame:
    move.w  0(%a0), %d5            ; access type / FC (unreliable on 68000)
    move.l  2(%a0), %d4            ; access address (RELIABLE)
    move.w  6(%a0), %d3            ; instruction register (unreliable)
    move.w  8(%a0), %d1            ; stacked SR
    move.l  10(%a0), %d2           ; stacked PC
    move.l  %d4, CRASH_FAULT_ADDRESS
    move.w  %d5, CRASH_ACCESS_TYPE
    move.w  %d1, CRASH_STACKED_SR
    move.l  %d2, CRASH_STACKED_PC
    bra.s   .Lframe_done

.Lstandard_frame:
    ; All other exceptions — standard 6-byte frame:
    move.w  0(%a0), %d1            ; stacked SR
    move.l  2(%a0), %d2            ; stacked PC
    move.w  %d1, CRASH_STACKED_SR
    move.l  %d2, CRASH_STACKED_PC
    ; CRASH_FAULT_ADDRESS and CRASH_ACCESS_TYPE left as 0 (not applicable)

.Lframe_done:
    ; Frame decode complete — proceed to register saves
```

The branch uses `cmpi.b #3, %d0` / `bhi.s` because vector numbers 2
and 3 (bus error and address error) are the ONLY vectors with the
extended frame. All other vector numbers (4–63) use the standard frame.
The branch tests D0 directly — NOT `CRASH_EXCEPTION_TYPE` in WRAM —
because D0 is still live and an absolute-address read would be slower
and unnecessary.

**Reliability note:** On 68000 (not 68010+), the function-code word
at `+0` and the instruction register at `+6` may contain
implementation-defined garbage. The access address at `+2` IS reliable.
The crash record stores all fields but flags `+0` and `+6` as
unreliable.

---

## Phase 5 — WRAM Crash Record Layout

### Base address

**`CRASH_RECORD_BASE = 0x00FF6800`**

Justification:
- BSS starts at `0xFF4000` (link.ld), ends at approximately
  `0xFF6108` (BSS contents: ~8456 bytes of staging buffers + state).
- `0xFF6800` is `0x6F8` bytes above BSS end — clear margin.
- Well below WRAM top at `0xFFFFFF`.
- Does not overlap arcade workram (`0xFF0000–0xFF3FFF`) or BSS
  (`0xFF4000–0xFF6108`).
- Total record size: `0x6C` bytes (108), fitting within a single
  256-byte page.

### Field definitions

```asm
.equ CRASH_RECORD_BASE,       0x00FF6800

.equ CRASH_ACTIVE_FLAG,       0x00FF6800          ; byte — lockout (instruction 3/4)
    ; padding byte at +1
.equ CRASH_EXCEPTION_TYPE,    0x00FF6802          ; byte — vector number (written by stub)
    ; padding byte at +3
.equ CRASH_STACKED_SR,        0x00FF6804          ; word
.equ CRASH_STACKED_PC,        0x00FF6806          ; longword
.equ CRASH_PC_AT_HANDLER,     0x00FF680A          ; longword — A0 copy of SP at entry
.equ CRASH_SP_AT_ENTRY,       0x00FF680E          ; longword — original SP value
.equ CRASH_USP,               0x00FF6812          ; longword
.equ CRASH_D0,                0x00FF6816          ; longword
.equ CRASH_D1,                0x00FF681A          ; longword
.equ CRASH_D2,                0x00FF681E          ; longword
.equ CRASH_D3,                0x00FF6822          ; longword
.equ CRASH_D4,                0x00FF6826          ; longword
.equ CRASH_D5,                0x00FF682A          ; longword
.equ CRASH_D6,                0x00FF682E          ; longword
.equ CRASH_D7,                0x00FF6832          ; longword
.equ CRASH_A0,                0x00FF6836          ; longword
.equ CRASH_A1,                0x00FF683A          ; longword
.equ CRASH_A2,                0x00FF683E          ; longword
.equ CRASH_A3,                0x00FF6842          ; longword
.equ CRASH_A4,                0x00FF6846          ; longword
.equ CRASH_A5,                0x00FF684A          ; longword
.equ CRASH_A6,                0x00FF684E          ; longword
.equ CRASH_FRAME_COUNTER,     0x00FF6852          ; word

.equ CRASH_FAULT_ADDRESS,     0x00FF6854          ; longword (bus/addr error only)
.equ CRASH_ACCESS_TYPE,       0x00FF6858          ; word (bus/addr error only)

.equ CRASH_ARCADE_DEST_BG,    0x00FF685A          ; longword
.equ CRASH_ARCADE_DEST_FG,    0x00FF685E          ; longword
.equ CRASH_BG_ROW_DIRTY,      0x00FF6862          ; longword
.equ CRASH_FG_ROW_DIRTY,      0x00FF6866          ; longword
.equ CRASH_PALETTE_DIRTY,     0x00FF686A          ; byte
.equ CRASH_TILES_DIRTY,       0x00FF686B          ; byte

.equ CRASH_RECORD_SIZE,       0x6C                ; 108 bytes total
```

**Alignment validation:** all longword fields (`_PC`, `_SP_AT_ENTRY`,
`_USP`, `_D0`–`_D7`, `_A0`–`_A6`, `_FAULT_ADDRESS`, `_DEST_BG`,
`_DEST_FG`, `_DIRTY` fields) are at even addresses. ✓

---

## Phase 6 — First-Fault Lockout

Lockout is set as **instruction 5** in `_crash_common` (after the
lockout CHECK at instructions 3–4):

```asm
_crash_common:
    move.w  #0x2700, %sr           ; 1
    move.l  %sp, %a0               ; 2
    tst.b   CRASH_ACTIVE_FLAG      ; 3 — check
    bne.s   .Lminimal_halt         ; 4 — halt if already active
    move.b  #1, CRASH_ACTIVE_FLAG  ; 5 — set lockout
    move.b  %d0, CRASH_EXCEPTION_TYPE  ; 6 — write vector id (D0 from stub)
```

The stub passes the vector number via D0 — no WRAM write occurs before
the lockout check. The lockout flag is set before any other WRAM writes,
register saves, or VDP access.

Minimal halt path:
```asm
.Lminimal_halt:
    stop    #0x2700
    bra.s   .Lminimal_halt
```

This path: no WRAM writes, no VDP writes, no subroutine calls. Only
`stop` + `bra.s`.

---

## Phase 7 — Safe Rendering Strategy

### VDP reinit sequence

Before any crash screen rendering, establish a known-good VDP state.
All writes are direct to `VDP_CTRL` (`0xC00004`):

```asm
; Minimal VDP reinit for crash screen
move.w  #0x8004, VDP_CTRL          ; reg 0: H-int off
move.w  #0x8134, VDP_CTRL          ; reg 1: display ON, V-int OFF, DMA off
move.w  #0x8238, VDP_CTRL          ; reg 2: Plane A at 0xE000
move.w  #0x833C, VDP_CTRL          ; reg 3: Window at 0xF000
move.w  #0x8406, VDP_CTRL          ; reg 4: Plane B at 0xC000
move.w  #0x857C, VDP_CTRL          ; reg 5: SAT at 0xF800
move.w  #0x8700, VDP_CTRL          ; reg 7: BG color = palette 0 entry 0
move.w  #0x8A00, VDP_CTRL          ; reg 10: H-int every 0 lines (disabled above)
move.w  #0x8B00, VDP_CTRL          ; reg 11: full-screen scroll
move.w  #0x8C81, VDP_CTRL          ; reg 12: H40 mode (40 columns)
move.w  #0x8D3F, VDP_CTRL          ; reg 13: H-scroll at 0xFC00
move.w  #0x8F02, VDP_CTRL          ; reg 15: auto-increment 2
move.w  #0x9001, VDP_CTRL          ; reg 16: plane size 64×32
```

V-int is **disabled** (`0x8134` bit 5 = 0) — the crash screen must
not be interrupted by VBlank.

### Safe SP before renderer

After all register saves and frame capture are complete, and before
entering the crash screen renderer (which uses subroutine calls for
hex formatting and string output):

```asm
    lea     0x00FFFF00, %sp        ; set crash-safe stack pointer
```

`0x00FFFF00` is confirmed conflict-free:
- CRASH_RECORD_BASE at `0xFF6800`–`0xFF686B` (108 bytes) — no overlap.
- BSS at `0xFF4000`–`0xFF6108` — no overlap.
- Arcade workram at `0xFF0000`–`0xFF3FFF` — no overlap.
- Stack grows DOWN from `0xFFFF00` into `0xFFFExx` — well within the
  64KB WRAM range (`0xFF0000–0xFFFFFF`), above all allocated regions.

The crash renderer requires minimal stack depth (one or two levels of
`bsr` for hex formatting helpers). 256 bytes of stack space
(`0xFFFF00` down to `0xFFFE00`) is more than sufficient.

**Updated full execution order:**

```
 1. move.w  #0x2700, %sr
 2. move.l  %sp, %a0
 3. tst.b   CRASH_ACTIVE_FLAG
 4. bne.s   .Lminimal_halt
 5. move.b  #1, CRASH_ACTIVE_FLAG
 6. move.b  %d0, CRASH_EXCEPTION_TYPE
 7. read exception frame via %a0 (branch on D0 for frame type)
 8. store frame data to WRAM crash record
 9. store registers D1-D7, A0-A6 to WRAM (individual move.l)
10. store A0 (original SP) to CRASH_SP_AT_ENTRY
11. move usp,%a1 / move.l %a1, CRASH_USP
12. store project-specific state to WRAM
13. lea 0x00FFFF00, %sp          ← safe SP set HERE
14. VDP reinit (14 register writes)
15. CRAM palette write (2 entries)
16. upload crash font tiles to VRAM
17. write nametable entries for crash screen
18. halt forever
```

### Tile source: embedded 1bpp crash font

The crash handler embeds a minimal 1bpp ASCII font directly in its
`.rodata` section. This is the ONLY font path — there is no fallback
to PC080SN scene tiles or any existing VRAM content. The embedded font
is independent of the normal rendering pipeline and guaranteed to work
regardless of VRAM state at crash time.

Font: 96 printable ASCII characters (`0x20`–`0x7F`), 8 bytes per
character (1 bit per pixel, 8×8). Total: **768 bytes** in ROM.

### Font expansion: inline direct-to-VRAM

For each character tile being uploaded to VRAM, the crash renderer
reads the 1bpp font data one byte at a time and expands it inline to
a 4bpp Genesis tile row, writing directly to `VDP_DATA` without any
intermediate RAM buffer.

Each 1bpp byte (8 pixels) becomes one 32-bit word (8 nibbles):

```asm
; Expand one 1bpp font byte to one 4bpp tile row and write to VDP.
; Input:  D0.b = 1bpp font byte (bit 7 = leftmost pixel)
; Output: one move.l to VDP_DATA
; Uses:   D1 (result longword), D2 (bit counter), D3 (scratch)

    moveq   #0, %d1                ; clear result
    moveq   #7, %d2                ; 8 bits to process
.Lexpand_bit:
    lsl.l   #4, %d1                ; shift result left one nibble
    btst    %d2, %d0               ; test current bit
    beq.s   .Lbit_zero
    ori.b   #1, %d1                ; set nibble to 1 (CRAM entry 1 = white)
.Lbit_zero:
    dbra    %d2, .Lexpand_bit
    move.l  %d1, VDP_DATA          ; write one 4bpp tile row directly to VRAM
```

This loop runs 8 times per font byte, producing one `move.l` per row.
Each 8×8 character tile requires 8 iterations of the outer (byte)
loop, producing 8 × `move.l` = 32 bytes per tile. Total per character:
8 byte-reads + 64 bit-tests + 8 VDP writes. No RAM scratch buffer.

### VRAM crash font base

Crash font tiles are written to **VRAM address `0x8000`** (tile index
1024). This is above the scene-preload tile range which uses
`TILE_CACHE_BASE_A = 20` through `TILE_CACHE_BASE_A + 1004 = 1023`
and `TILE_CACHE_BASE_B = 1280` through `1439`. Tile index 1024 falls
in the gap between cache A (max 1023) and cache B (min 1280). **No
conflict with scene preload.**

VRAM address calculation: tile 1024 × 32 bytes/tile = `0x8000`.

Before uploading, set VDP write address to `0x8000`:
```asm
    move.l  #0x40000002, VDP_CTRL   ; VRAM write to 0x8000
                                    ; (cmd = 0x40000000 | (0x8000 << 16 & 0x3FFF0000) | (0x8000 >> 14 & 3))
```

The exact VDP command longword for VRAM write at address `A`:
```
cmd = 0x40000000 | ((A & 0x3FFF) << 16) | ((A >> 14) & 3)
```

For `A = 0x8000`:
```
cmd = 0x40000000 | ((0x8000 & 0x3FFF) << 16) | ((0x8000 >> 14) & 3)
    = 0x40000000 | (0x0000 << 16) | (2)
    = 0x40000002
```

### Nametable target

The crash screen writes to **Plane A at VRAM `0xE000`** (the same
plane used by the normal FG rendering pipeline). Justification:
- Plane A is drawn on top of Plane B by default (when priority bits
  are equal). The crash screen sets priority = 1 on all its tiles,
  ensuring it overlays any existing content on either plane.
- Using Plane A avoids needing to reconfigure the VDP plane base
  registers — Plane A is already at `0xE000` from `vdp_boot_setup`
  and from the VDP reinit sequence above.

Nametable entry for each character: tile index = `1024 + (ascii - 0x20)`,
palette line 0, priority 1:
```
nametable_word = 0x8000 | (1024 + char_offset)
               = 0x8400 + char_offset
```

The `0x8000` bit sets priority = 1. Tile indices `1024`–`1119`
(96 characters).

VDP command for VRAM write to Plane A nametable at `0xE000`:
```asm
    move.l  #0x60000003, VDP_CTRL   ; VRAM write to 0xE000
```

### Palette

The crash renderer writes a 2-entry crash palette directly to CRAM:
```asm
; Set CRAM write address to palette line 0
move.l  #0xC0000000, VDP_CTRL
move.w  #0x0000, VDP_DATA          ; entry 0: black
move.w  #0x0EEE, VDP_DATA          ; entry 1: white
```

### Fallback

If tile rendering fails (VDP access produces a bus error during the
crash handler → hits lockout → minimal halt), the CRAM write above
still sets entry 0 = black. The screen shows solid black with no text.
This is the absolute minimum fallback: a black screen that has stopped
crashing.

---

## Phase 8 — Crash Screen Layout

H40 mode: 40 columns × 28 rows.

```
Row  0: ==== RASTAN CRASH ==========================
Row  1: EXCEPTION: [name]          VECTOR: [nn]
Row  2: FAULT PC:  [xxxxxxxx]      SR: [xxxx]
Row  3: FAULT ADDR:[xxxxxxxx]      (bus/addr only)
Row  4: ============================================
Row  5: D0:[xxxxxxxx] D1:[xxxxxxxx] D2:[xxxxxxxx]
Row  6: D3:[xxxxxxxx] D4:[xxxxxxxx] D5:[xxxxxxxx]
Row  7: D6:[xxxxxxxx] D7:[xxxxxxxx]
Row  8: A0:[xxxxxxxx] A1:[xxxxxxxx] A2:[xxxxxxxx]
Row  9: A3:[xxxxxxxx] A4:[xxxxxxxx] A5:[xxxxxxxx]
Row 10: A6:[xxxxxxxx] SP:[xxxxxxxx] USP:[xxxxxxxx]
Row 11: ============================================
Row 12: DEST_BG:[xxxxxxxx] DEST_FG:[xxxxxxxx]
Row 13: BG_DIRTY:[xxxxxxxx] FG_DIRTY:[xxxxxxxx]
Row 14: PAL_D:[xx] TILE_D:[xx] FRAME:[xxxx]
Row 15: ============================================
Row 16: STACK DUMP:
Row 17: [xxxxxxxx xxxxxxxx xxxxxxxx xxxxxxxx]
Row 18: [xxxxxxxx xxxxxxxx xxxxxxxx xxxxxxxx]
Row 19: [xxxxxxxx xxxxxxxx xxxxxxxx xxxxxxxx]
Row 20: [xxxxxxxx xxxxxxxx xxxxxxxx xxxxxxxx]
Row 21: ============================================
Row 27: HALTED -- BUILD 0038
```

- Palette line: 0 (crash renderer initializes it directly).
- Priority: 1 (high priority so crash screen overlays any existing
  plane content).
- Backtrace: **stack dump only** — raw 16 longwords from SP. No
  heuristic frame-pointer scan. The 68000 provides no guaranteed frame
  pointers, and the translation engine's synthetic exception frames
  make heuristic scanning unreliable.

---

## Phase 9 — Final Required Judgments

**Q1: What exact data should be captured on every exception?**

Stacked SR, stacked PC, vector number, SP at entry, USP, all 15
general registers (D0–D7, A0–A6), frame counter, project-specific
state (DEST_BG, DEST_FG, BG_ROW_DIRTY, FG_ROW_DIRTY, PALETTE_DIRTY,
TILES_DIRTY), and 16 longwords of raw stack dump.

**Q2: What extra data for bus/address error?**

Fault access address (reliable on 68000, at exception frame +2) and
access type word (unreliable on 68000, at frame +0). Both stored;
access type flagged as implementation-defined.

**Q3: Safest crash screen rendering approach?**

Embed a minimal 1bpp ASCII font (768 bytes) directly in the crash
handler. Expand to 4bpp at render time. Write directly to VRAM via
VDP_DATA port. No dependency on existing VRAM, staging buffers, DMA,
or VBlank. Fallback: if VDP access fails, CRAM entry 0 = black →
solid black screen (stopped crashing).

**Q4: Where should the crash record live?**

`CRASH_RECORD_BASE = 0x00FF6800`. Confirmed safe: BSS ends at
~0xFF6108 (link.ld BSS at 0xFF4000 + ~8456 bytes of staging buffers);
arcade workram at 0xFF0000–0xFF3FFF. The crash record at 0xFF6800 has
~0x6F8 bytes of margin above BSS and does not overlap any runtime
allocation.

**Q5: What replaces `_default_handler: rte`?**

Every vector currently pointing to `_default_handler` (60 vectors)
gets a per-vector crash stub that loads the vector number into D0 via
`moveq #N, %d0` and branches to `_crash_common` via `bra.w`. The stub
does NOT write to WRAM — the vector number is written to WRAM only
after the lockout check passes inside `_crash_common`.
`_default_handler: rte` is removed entirely. The `_crash_common`
handler captures state, renders a diagnostic screen, and halts forever.
Never RTEs.

**Q6: Register save approach?**

Individual `move.l` instructions directly to the crash record fields.
No `movem.l` to a temporary area. D0 contains the vector number (not
the fault-time D0 — that value is sacrificed). D1–D7 and A0–A6 are
saved at fault-time values. SP is captured separately from `%a0`
(the preserved frame pointer). USP is captured via
`move %usp, %a1` / `move.l %a1, CRASH_USP`.

```asm
    ; D0 = vector number (sacrifice — fault-time D0 is lost)
    move.l  %d0, CRASH_D0         ; stores vector number, not original D0
    move.l  %d1, CRASH_D1
    move.l  %d2, CRASH_D2
    move.l  %d3, CRASH_D3
    move.l  %d4, CRASH_D4
    move.l  %d5, CRASH_D5
    move.l  %d6, CRASH_D6
    move.l  %d7, CRASH_D7
    move.l  %a0, CRASH_SP_AT_ENTRY ; A0 = original SP from step 2
    move.l  %a1, CRASH_A1
    move.l  %a2, CRASH_A2
    move.l  %a3, CRASH_A3
    move.l  %a4, CRASH_A4
    move.l  %a5, CRASH_A5
    move.l  %a6, CRASH_A6
```

Note: A0 at this point is the ORIGINAL SP (saved in step 2), not the
fault-time A0. The fault-time A0 is NOT captured because A0 was
overwritten by `move.l %sp, %a0` in the common handler prologue. This
is a known limitation. If the fault-time A0 is needed, the stub would
need to save it before `_crash_common` — but this would require
modifying the stack (violating the "no stack modification before frame
read" rule). Andy accepts this trade-off: SP at entry is more valuable
than A0 at fault time for diagnostic purposes.
