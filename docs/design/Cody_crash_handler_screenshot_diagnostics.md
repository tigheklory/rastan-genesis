# Crash Handler Rebuild for Screenshot-Only Playtest Diagnostics (Build 0289)

**Baseline:** current tree after Build 0287. **No rollback**; every numbered ROM preserved. Labels:
**PROVEN / HYPOTHESIS / DISPROVEN**. Candidate: **Build 0289** (Build 0288 is an identical-handler intermediate,
also preserved — an extra number was consumed by a redundant `make release`; both carry this rebuild).

## SCREENSHOT-FIRST REQUIREMENT
The on-screen report is the PRIMARY diagnostic artifact: Tighe plays normally, an exception occurs, he screenshots
the screen and hands it to an agent. No debugger / trace / watchpoint / WRAM capture is assumed. The screen must be
self-sufficient for first-pass diagnosis; the WRAM crash record (0x00FF6800+) is supplemental only.

## OLD HANDLER DEFECTS (all PROVEN by reading the prior source)
- **D0 destroyed in the stub:** every vector stub did `moveq #<vec>,%d0; bra _crash_common`, so the ORIGINAL
  fault-time D0 was gone before the common body ran (displayed D0 was the vector number).
- **D1-D5/A0/A1 destroyed in the common body:** `_crash_common` did `move.l %sp,%a0`, `move.w 0(%a0),%d5`,
  `move.l 2(%a0),%d4`, `move.w 6(%a0),%d3`, `move.w 8(%a0),%d1`, `move.l 10(%a0),%d2`,
  `lea .Lmarker(%pc),%a1` — all BEFORE storing the "crash" registers, so displayed D0-D5/A0/A1 were handler values.
- **Ambiguous "FAULT PC":** the value is a stacked RUNTIME Genesis PC, mislabeled as if it were an arcade PC.
- **Fake FRAME:** `clr.w CRASH_FRAME_COUNTER` then displayed FRAME (always 0).
- **Incomplete VDP reset:** only Plane A was cleared; Plane B / Window / SAT / H-scroll / V-scroll were inherited
  from the crashed game, so old graphics and scrolling could contaminate the screenshot.
- **Stale hard-coded footer** `BUILD 0038`.
- **Low-value fields** (ARCADE_DEST_BG/FG, BG/FG_ROW_DIRTY, PALETTE/TILES_DIRTY) crowded the screen.

## EXCEPTION ENTRY / ORIGINAL REGISTER CAPTURE
**PROVEN.** New contract: each stub writes ONLY the vector number to WRAM (`move.w #<vec>, CRASH_EXCEPTION_TYPE` —
immediate → memory, no register touched) and `bra.w _crash_common`. `_crash_common`'s FIRST data action is the
re-entry guard (memory `tst.b`, no register) then `movem.l %d0-%d7/%a0-%a6, CRASH_D0` (memory destination does not
alter registers). Therefore ALL 15 original registers are snapshotted intact before any reuse. The exception-frame
SSP (`%sp`) is saved to CRASH_FRAME_SP and `%usp` to CRASH_USP before switching to a private handler stack. Only
after the snapshot does the handler use registers to decode the frame and render.

**Controlled validation (PROVEN, `-video none` Genesis-NTSC MAME, illegal @ 0x00FF9000 with sentinels):**
EXC=4, STACKED_SR=2700, STACKED_PC=00FF9000, FRAME_SP=00FEFF64, D0=DEAD0000, D1=D1D1D1D1 … D7=D7D7D7D7,
A0=A0A0A000 … A4=A4A4A4A4, A5=00FF0000, A6=A6A6A6A6, A5_VALID=1, game-state GS_00..GS_200 = 0002/0003/0001/0000/00A5
— every field matches the pre-set values exactly. The old handler would have shown D0=vector and clobbered
D1-D5/A0/A1. Evidence: `states/traces/build0289_crash_handler_validation/controlled_illegal_register_capture.txt`.

## 68000 EXCEPTION FRAME MODEL
**PROVEN** against the Motorola 68000 contract (VBR=0):
- **Normal (group 1/2)** exceptions: `+0` SR (word), `+2` PC (long).
- **Bus error / Address error (group 0, vectors 2/3)** on the 68000: `+0` access/status word (R/W, I/N, FC),
  `+2` access (fault) address (long), `+6` instruction register (word), `+8` SR (word), `+10` PC (long).
The prior source's offsets happened to match this; they were re-derived, not assumed. The handler decodes SR/PC for
both frame shapes and, for vectors 2/3, also stores FAULT ADDRESS, ACCESS word, and instruction register. The raw
exception-frame SP is retained (CRASH_FRAME_SP) and a small raw stack window is drawn so a future diagnosis can
re-inspect the frame words.

## GEN PC / ARC PC REPORTING
**PROVEN.** The stacked PC is displayed as **GEN PC** (exact runtime Genesis PC) — never presented as an arcade
address. A **SOURCE** token classifies GEN PC by the current `address_map.json` region boundaries (read at build
time, not arithmetic): `< 0x00117E` → GENONLY (vectors/boot); `0x00117E..0x0600F4` → ARCADE (arcade-copied
maincpu); `0x0600F4..0x184A34` → GENONLY (native helper/wrapper); else → UNKNOWN. **ARC PC is never fabricated:**
it is shown as `--------` with the note `MAP OFFLINE`, because exact arcade translation requires the per-segment
shift table (530 segments + shift deltas) — too much to binary-search safely inside a handler that runs when memory
may already be corrupt. Tighe/an agent resolves the exact arcade PC offline from the GEN PC + `address_map.json`.
**Validation:** a handler-equivalent classifier re-run on the captured GEN PC (0x00FFFF3C) returned UNKNOWN,
matching the on-screen SRC token. This is the task's explicitly-permitted minimum ("exact GEN PC clearly labelled")
plus a safe region classification.

## GAME-STATE CAPTURE
**PROVEN.** The retained game-flow words are captured only when A5 is the expected WRAM base (0x00FF0000): the
handler compares CRASH_A5 and, if equal, reads `a5+0x00/0x02/0x04/0x34/0x200` and sets CRASH_A5_VALID=1; the screen
then shows `+00/+02/+04/+34/+200`. If A5 is not the base, it shows `STATE: A5 INVALID (SEE A5 REG)` and never
dereferences A5 — the raw A5 remains visible in the register block. Validated: with A5=0x00FF0000 pre-seeded, the
five state words were captured and A5_VALID=1.

## SCREEN INFORMATION PRIORITIES
Row layout (H40, ~28 rows), highest-value first: title + auto BUILD; exception name + VECTOR; GEN PC + SRC;
ARC PC placeholder + MAP OFFLINE; SR; FAULT + ACCESS (vectors 2/3 only); D0-D7; A0-A6; FRAME SP + USP; STATE
(+00/+02/+04/+34/+200 or A5 INVALID); a small raw STACK window from FRAME SP (skipped with "SP OUT OF WRAM RANGE"
if SP is not in WRAM); HALTED. The old low-value/fake fields (ARCADE_DEST_*, *_DIRTY, FRAME counter) are **removed**.

## VDP CLEAN-ROOM INITIALIZATION
**PROVEN (screenshot).** Order: mask interrupts (SR=0x2700) → **display OFF** (reg1=0x8104) → program the crash
layout registers → zero all scroll → clear all layers → clear SAT → init CRAM → upload font → draw report →
**display ON** (reg1=0x8144, VINT still off: static screen). No game VBlank / SAT staging / PC090OJ / PC080SN /
tilemap staging / DMA worklists / H-scroll / VSRAM staging / scene state is used — the handler owns the VDP directly
because the render system itself may be what failed. Screenshot evidence:
`states/traces/build0289_crash_handler_validation/crash_screen.png` (clean black field, white text, all fields
legible, no game sprites/tiles/scroll).

## HORIZONTAL / VERTICAL SCROLL RESET
**PROVEN.** VSRAM is explicitly zeroed (40 words via VSRAM write), and the H-scroll table at VRAM 0xFC00 is zeroed
across the screen. Reg11 selects full-screen H+V scroll so both planes read entry 0 (= 0). The crash screen cannot
inherit gameplay scrolling.

## PLANE A / PLANE B / WINDOW / SAT CLEAR
**PROVEN.** Plane A (0xE000), Plane B (0xC000) and Window (0xF000) name tables are each filled (2048 cells) with a
blank cell (font space tile 0x400). The SAT (0xF800) is fully zeroed (all sprites Y=0/off-screen, link 0). Window
registers 17/18 are set to 0 (window disabled) in addition to clearing its table. No stale sprite/plane/window
content can survive.

## AUTOMATIC BUILD NUMBER
**PROVEN.** The Makefile generates `out/crash_build.inc` (`crash_build_number_str: .asciz "NNNN"`) from the SAME
counter the numbering stage uses (`next = last-consumed + 1`), included by `crash_handler.s`; `vdp_comm.o` depends on
it. No hard-coded build number remains. Verified: the generated include for this candidate is `"0289"` and matches
the numbered artifact `rastan_direct_video_test_build_0289.bin`.

## SUPPLEMENTAL WRAM RECORD
The record at 0x00FF6800 (active flag, vector, SR, GEN PC, frame SP, USP, D0-D7/A0-A6, fault addr, access word,
instruction reg, game-state, A5-valid) is retained for emulator/debugger use, but **nothing on the screen depends
on retrieving it** — every first-pass field is drawn on-screen. Re-entry guard keeps the FIRST report if the handler
itself faults.

## CONTROLLED EXCEPTION VALIDATION
**PASS.** Method: Genesis-NTSC MAME (`genesis`), controlled ILLEGAL (0x4AFC) at 0x00FF9000 with pre-set sentinel
D0-D7/A0-A6/SR/PC and pre-seeded game state. `-video none` run read the WRAM record directly (rendering not
involved) and confirmed exact capture of all registers, EXC type, stacked PC, stacked SR, frame SP, and game-state
(above). A video run produced the screenshot proving the clean-room render. (Note: forcing CPU state mid-frame under
MAME's video path can interleave a second injection-induced fault, so the AUTHORITATIVE register proof is the
`-video none` direct-memory read; on real hardware there is a single fault and screen == record.) The temporary
injection is a MAME Lua test harness only — no controlled-crash path exists in the ROM. Final visual acceptance
(readability on Tighe's display) is deferred to Tighe per the task.

## CURRENT ITEM-PAGE CRASH — DEFERRED
The Build 0287 scrolling-item-page crash (after the HIGH SCORE screen) is **out of scope** and was neither
diagnosed nor fixed. This task only rebuilt the handler so the NEXT screenshot of that crash is diagnostic. It
remains **OPEN**. When Tighe reproduces it, the screenshot's GEN PC + SRC + registers + STATE tuple will drive the
next debugging task.
