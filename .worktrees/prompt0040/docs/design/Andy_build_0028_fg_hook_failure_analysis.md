# Andy — Build 0028 FG Hook Failure Analysis

**Build context:** rastan-direct, Build 0028  
**Stated crash:** write to 0xC09EA0 (FG VRAM range)  
**Exodus symptom:** VDP AdvanceProcessorState called out of order + black VDP window  
**Analysis date:** 2026-04-13

---

## TASK 1 — FG Hook Execution Verification

**FG hook execution: NO**  
**Call count: 0**  
**First occurrence PC: never**  
**Last occurrence PC: never**

### Proof

The dispatcher at arcade PC 0x55948 (Genesis PC 0x55B48) selects BG or FG path:

```asm
55948: cmpiw #0, %a5@(4264)    ; A5@(0x10A8) = 0xFF10A8 on Genesis
5594e: bnes 0x5595a             ; if != 0 → call FG producer at 0x55990
55950: bsrw 0x55968             ; if == 0 → call BG producer at 0x55968  ← always taken
```

A5 = 0xFF0000 on Genesis, so A5@(0x10A8) = 0xFF10A8 (Genesis WRAM).

The arcade code that WRITES the layer selector uses ABSOLUTE addressing, not A5-relative:

```asm
; From 0x558F8:
558f8: movew %d0, 0x10d0a8      ; absolute write → 0x10D0A8 (Genesis ROM space)
; From 0x55940:
55940: movew %d0, 0x10d0a8      ; absolute write → 0x10D0A8 (Genesis ROM space)
```

On the ARCADE, A5 = 0x10C000, so A5@(0x10A8) = 0x10D0A8. The absolute writes hit the same
address. On GENESIS with A5 = 0xFF0000, A5@(0x10A8) = 0xFF10A8 (WRAM). The absolute writes
still target 0x10D0A8 — which is Genesis ROM space (0x10D0A8 < 0x400000). Writes to Genesis
ROM are silently ignored.

**Result:** 0xFF10A8 is initialized to 0 by BSS and is never updated. The layer selector is
permanently 0. The dispatcher always calls the BG producer. The FG hook at 0x55990 is dead
code for the entire run.

The FG hook patch at 0x055990 is correctly installed and would work if called, but the
dispatcher routing condition is never satisfied.

---

## TASK 2 — Crash Write Identification

**Crash write PC: arcade 0x561CC, Genesis 0x563CC**  
**Instruction: `movel %d0, %a0@+`**  
**D0 = 0x00000020**  
**A0 = 0xC09EA0 (at iteration 1960 of the fill loop)**

### Proof

The function at arcade PC 0x561A0 (Genesis PC 0x563A0) is a "PC080SN reset" function that
directly fills both C-windows with 0x20. Full disassembly:

```asm
; Genesis 0x563A0 (arcade 0x561A0):
561a0: clrw %a5@(4270)           ; A5@(0x10AE) = 0       ← OK: writes WRAM
561a4: clrw %a5@(4272)           ; A5@(0x10B0) = 0       ← OK
561a8: clrw %a5@(4332)           ; A5@(0x10EC) = 0       ← OK
561ac: clrw %a5@(4334)           ; A5@(0x10EE) = 0       ← OK
561b0: jsr 0x55ab4               ; ← writes to 0xC20000/0xC40000 directly (secondary issue)
561b6: movew #4096, %d1          ; loop count
561ba: movel #32 (0x20), %d0     ; fill value
561c0: moveal #0xC08000, %a0     ; FG C-window base ← NOT intercepted
561c6: moveal #0xC00000, %a1     ; BG C-window base ← NOT intercepted
561cc: movel %d0, %a0@+          ; ← WRITES to FG C-window starting at 0xC08000
561ce: movel %d0, %a1@+          ; ← WRITES to BG C-window starting at 0xC00000
561d0: subqw #1, %d1
561d2: bnes 0x561cc               ; loop 4096 times
561d4: rts
```

Crash address calculation:
```
A0_start = 0xC08000
bytes_per_iter = 4
iters_before_crash = (0xC09EA0 - 0xC08000) / 4 = 0x1EA0 / 4 = 0x7A8 = 1960
A0 at iter 1961 = 0xC08000 + 1960 × 4 = 0xC09EA0   ← BlastEm freeze point
```

Register state at crash write:
- A0 = 0xC09EA0
- D0 = 0x00000020
- D1 = 4096 - 1960 = 2136 (remaining iterations)
- A1 = 0xC01EA0 (BG side, 1960 iterations ahead of 0xC00000)

The BG write (A1) at the same iteration is to 0xC01EA0 (still in VDP address range). The WRITE
to 0xC00000 itself (the very first BG iteration) lands at the VDP DATA port — this corrupts VRAM
with 0x20202020 fill data and triggers the Exodus "VDP AdvanceProcessorState called out of order"
error (tight-loop writes to VDP data port without honouring VDP timing state machine).

### This write is NOT intercepted by either hook
- `genesistan_hook_tilemap_plane_a` (BG): intercepts calls to 0x55968 (strip producer path only)
- `genesistan_hook_tilemap_fg` (FG): intercepts calls to 0x55990 (strip producer path only)
- The function at 0x561A0 uses absolute addresses and a direct fill loop — bypasses both hooks entirely

---

## TASK 3 — Patch Effectiveness

**[X] Case C — Multiple FG writers exist**

The FG strip producer at 0x55990 is ONE of at least two code paths that write to the FG
C-window. The Build 0028 patch at 0x55990 is correct for the strip producer path, but the
direct init/fill function at 0x561A0 is a separate, unhooked writer.

The fill function at 0x561A0 is called from at least four locations:
```
55e22: bsrw 0x561a0
55f64: bsrw 0x561a0
55fca: bsrw 0x561a0
56458: bsrw 0x561a0
```

These are all in the scene state machine / frontend init area. The function is invoked during
scene initialization, not through the strip producer dispatch flow.

There is also a separate issue (Case A for the FG strip producer path): the FG producer at
0x55990 is never called due to the layer selector mismatch described in Task 1. The hook is
not "ineffective" — it is simply never reached.

---

## TASK 4 — FG Workram Offset Validation

**DEST_FG = 0x10A4: CONFIRMED CORRECT**

Verified directly from the FG producer entry at 0x55990:
```asm
55990: moveal %a5@(4260), %a0    ; 4260 decimal = 0x10A4
```
With A5 = 0xFF0000 on Genesis: accesses 0xFF10A4 = `ARCADE_FIX_DEST_FG`. ✓

**DESC_FG_LIST = 0x1000 (A5-relative): CANNOT BE VALIDATED — FG PRODUCER NEVER RUNS**

The FG producer references its descriptor list via absolute addresses:
```asm
55996: moveal #1101952 (0x10D080), %a1
5599c: moveal #1101888 (0x10D040), %a3
```
These are absolute (not A5-relative). They are NOT populated on Genesis (writes to 0x10D040/
0x10D080 from the descriptor-table-build code go to ROM space and are silently ignored). The
`ARCADE_PC080SN_DESC_FG_LIST_OFFSET = 0x1000` used in the hook maps to 0xFF1000 (WRAM), which
is never populated by arcade code. Since the FG producer is never called, this mismatch does
not affect the current crash, but it will produce incorrect FG tile content when the FG producer
path is eventually activated.

**STRIP_INDEX_FG = 0x10CA: CONFIRMED CORRECT**

Verified at 0x55A2A inside the FG row writer:
```asm
55a2a: movew %a5@(4298), %d7    ; 4298 decimal = 0x10CA
```
Both BG and FG share the same strip index field. ✓

---

## TASK 5 — Video Correlation

**BG status: corrupt — VRAM fill by 0x20 data written via VDP data port**  
**FG status: corrupt — out-of-order VDP writes from 0xC08000+**  
**First visible corruption frame: ~662**

### Frame-by-frame evidence

- **Frames 1–77**: Black VDP window. Genesis boot + arcade init executing. No tile writes yet.
- **Frame 78**: Small pink pixel visible — game has passed init, arcade tick running. VDP has
  received some setup writes from `_VINT_handler` (confirmed by `vdp_ports_live first_frame=0`).
- **Frames ~230+**: VDP window still black/uninitialised from tile perspective.
- **Frame 662**: State change visible — VDP image shows:
  - Upper portion: noise pattern (random tile data) — this is the fill loop writing 0x20202020
    to 0xC00000 (VDP data port), which corrupts the tile data section of VRAM
  - Lower portion: intact green checkerboard — from `init_staging_state` init pattern (tiles
    0x0001/0x0002 at `staged_bg_buffer`, committed to VRAM_PLANE_B_BASE before the fill)
  - The boundary between noise and checkerboard corresponds to how many VRAM cells were
    overwritten by the fill loop before Exodus began asserting
- **Frame 686+**: Same corrupted state repeating — Exodus continues after logging errors but
  VRAM/display state is degraded

### Trace timing correlation

MAME trace (separate run): The arcade tick entry fires at frame ~390. The fill function at
0x561A0 is called from scene init paths, likely within the first few arcade tick calls. On
Exodus, this would correspond to the first ~1-2 seconds of genesis_tick execution — consistent
with the crash appearing around frame 660-680 of the 30fps video (~22 seconds in).

---

## TASK 6 — Scroll Validation

**Scroll redirect patches: APPLIED CORRECTLY**

From Cody's ROM verification:
```
0x03ADBA: 42 B9 00 FF 40 2C  → CLR.W staged_scroll_y_bg (0xFF402C)
0x03ADC0: 42 B9 00 FF 40 28  → CLR.W staged_scroll_x_bg (0xFF4028)
0x03B298: 42 B9 00 FF 40 2C  → same
0x03B29E: 42 B9 00 FF 40 28  → same
```

These are correct. The CLR.W init paths now zero `staged_scroll_y_bg` and `staged_scroll_x_bg`
in WRAM rather than writing to PC080SN hardware. `vdp_commit_scroll` runs each VINT and writes
the staged values (0,0) to VDP. Scroll is stuck at 0,0 but this is not a crash condition.

**Unresolved scroll write path:**

The function at 0x55AB4, called from 0x561B0 (the init reset function), writes directly to
0xC20000 and 0xC40000 via absolute move instructions:
```asm
55ab4: movew %a5@(0x10EE), 0xC20000    ; direct PC080SN yscroll write
55abc: movew %a5@(0x10EC), 0xC40000    ; direct PC080SN xscroll write
55ac4: movew %a5@(0x10B0), 0xC20002
55acc: movew %a5@(0x10AE), 0xC40002
```

These values were just cleared to 0 (lines 561A0–561AC), so the writes are `MOVE.W #0, 0xC20000`
etc. On Genesis, 0xC20000 is in the VDP address range. Whether this crashes depends on the
emulator. This is a secondary issue subordinate to the fill loop crash.

---

## TASK 7 — Root Cause

```
Root Cause Type: [X] Multiple FG producers (unpatched path)
```

**Root Cause Explanation:**

The function at arcade PC 0x561A0 is a "PC080SN C-window reset" routine called during scene
initialization. It directly fills both the FG C-window (0xC08000–0xC0BFFF) and BG C-window
(0xC00000–0xC03FFF) with the constant 0x00000020 using a 4096-iteration longword fill loop.
This function uses absolute addresses, not the strip producer dispatch path, and is completely
outside the scope of both the BG and FG strip producer hooks.

On Genesis, 0xC00000 is the VDP data port and 0xC08000+ is beyond the valid VDP register space.
The fill loop sends 4096 consecutive longword writes to the VDP data port (BG side) and to an
invalid VDP offset (FG side). Exodus throws "VDP AdvanceProcessorState called out of order"
from the tight-loop VDP data port writes. BlastEm freezes at the FG write to 0xC09EA0 (the
1961st FG iteration).

The FG strip producer hook at 0x55990 was correctly patched and would work if called, but it
is never invoked because the layer selector at A5@(0x10A8) = 0xFF10A8 is permanently 0 on
Genesis (arcade absolute writes to 0x10D0A8 miss the Genesis WRAM location). This is a
secondary issue that causes FG layer content to always be absent, but it is not the crash cause.

---

## TASK 8 — Exact Fix Plan

**Add one opcode_replace entry to NOP the C-window fill loop.**

```json
{
  "arcade_pc": "0x0561B6",
  "original_bytes": "323C1000203C000000207C00C08000227C00C0000020C022C0534166F8",
  "replacement_bytes": "4E714E714E714E714E714E714E714E714E714E714E714E714E714E714E71",
  "note": "Suppress PC080SN C-window direct fill loop (0x561B6–0x561D2). Fills 0xC08000 (FG) and 0xC00000 (BG) with 0x00000020 in a tight loop — crashes Genesis VDP. NOP 30 bytes (15 NOPs), preserving A5-relative scroll field clears above and RTS below."
}
```

**Byte breakdown of original_bytes (30 bytes, all unaffected by relocation):**
```
32 3C 10 00          MOVE.W #0x1000, D1           (4 bytes)
20 3C 00 00 00 20    MOVE.L #0x20, D0             (6 bytes)
20 7C 00 C0 80 00    MOVEA.L #0xC08000, A0        (6 bytes — target > 0x60000, not relocated)
22 7C 00 C0 00 00    MOVEA.L #0xC00000, A1        (6 bytes — target > 0x60000, not relocated)
20 C0                MOVE.L D0, (A0)+             (2 bytes)
22 C0                MOVE.L D0, (A1)+             (2 bytes)
53 41                SUBQ.W #1, D1               (2 bytes)
66 F8                BNE.S -8                     (2 bytes)
                     Total: 30 bytes = 15 NOPs
```

**opcode_replace_count: 44 → 45**

**Note on the JSR to 0x55AB4 at 0x561B0:**

The JSR at 0x561B0 calls a scroll hardware write function that targets 0xC20000/0xC40000.
These writes use the just-cleared zero values and may or may not crash depending on emulator.
If a second crash is observed after the fill loop is suppressed, add a second NOP patch for the
JSR at 0x561B0. This cannot be determined until Build 0029 is tested.

**Note on FG layer content (separate from the crash):**

Even after the fill loop is suppressed, the FG strip producer (0x55990) will still never be
called because A5@(0x10A8) = 0xFF10A8 is never set via A5-relative addressing. The FG layer
will remain empty. A5@(0x10A8) is updated by arcade code using absolute address 0x10D0A8
(ROM space on Genesis — silently ignored). Fixing this requires either:
- Adding an A5-relative write to 0xFF10A8 from Genesis-side code (based on game state), or
- Patching the specific absolute-write sites that set 0x10D0A8 to instead write to 0xFF10A8

This is deferred — fix the crash first, evaluate FG routing after.

---

## Summary

| Task | Finding |
|------|---------|
| FG hook execution | NEVER called (layer selector A5@(0x10A8) always 0) |
| Crash write PC | 0x563CC (Genesis) — fill loop `movel d0, a0@+`, A0=0xC09EA0 |
| Root cause | Unhooked direct C-window fill at 0x561A0/0x561C0 |
| FG offsets | DEST_FG=0x10A4 correct; DESC access via absolute addrs (secondary issue) |
| BG status | Corrupt — VRAM fill at VDP data port from 0xC00000 writes |
| FG status | Corrupt — out-of-order VDP write from 0xC08000+ writes |
| First corruption frame | ~662 |
| Scroll redirect | Correct — CLR.W redirected to staged_scroll_* in WRAM |
| Scroll stuck at 0,0 | Yes — no non-zero scroll writes intercepted yet (expected) |
| Multiple writers detected | YES — 0x55990 (strip producer, hooked) + 0x561C0 (init fill, NOT hooked) |
