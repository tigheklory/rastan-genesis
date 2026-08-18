# Crash-Screen Values Fix + Build0288 "Gameplay Regression" Investigation (Build 0290)

**Baseline:** current tree after Build 0289. **No rollback**; Builds 0287/0288/0289 preserved. Candidate: **Build
0290**. Labels: **PROVEN / HYPOTHESIS / DISPROVEN**.

## USER EVIDENCE
- **0287:** gameplay starts normally; HIGH SCORE correct; scrolling ITEM PAGE crashes (dates from the Build0286
  transient-item conversion).
- **0288/0289:** same item-page crash; the crash screen is clean/readable; user reports gameplay "locks/freezes on
  game start."
The user asserts two separate boundaries: gameplay-start regression 0287→0288, and item-page crash pre0286→0286.

## PROVEN NUMERIC DISPLAY BUG
**PROVEN.** The Build0289 on-screen numeric renderer printed each hex field's own cursor address, not the captured
value. `crash_put_hex{32,16,8}_at` did `bsr crash_set_cursor; bsr crash_put_hexN_inline`, but `crash_set_cursor`
uses **D2** for the Plane-A VRAM address math — and D2 is the value to print. So the value was overwritten by the
cursor address before formatting. The user's screenshot proves it arithmetically:
- GEN PC `0x00000190` = row3,col8 = (3×0x80)+(8×2).
- D0 `0x00000406` = row8,col3; D1 `0x00000420` = row8,col16.
- FRAME SP `0x00000712` = row14,col9; USP `0x00000730` = row14,col24.
- VECTOR `46` = low byte of row2,col35 cursor (0x146).
**Fix:** save/restore D2 around `crash_set_cursor` in all three `_at` wrappers. Audited every other output helper:
`crash_puts_at` reloads D2 from the string after positioning (unaffected); `crash_put_hex32_inline` in the stack
dump loads D2 *after* `crash_set_cursor` (unaffected); `crash_render_source` reads the real PC into D2 and
classifies *before* calling `crash_puts_at` (unaffected). Only the three `_at` wrappers were defective.

## SCREENSHOT FIELD TRUSTWORTHINESS
**PROVEN.** In the Build0289 screenshot only the **text** fields were trustworthy, because they never carried a
value through D2 across `crash_set_cursor`:
- Exception NAME (`ILLEGAL INSTR`): **trustworthy** — from `crash_get_exception_name` table lookup (D0), printed via
  `crash_puts_at`.
- SRC token (`GENONLY`/`UNKNOWN`): **trustworthy** — `crash_render_source` classifies the REAL `CRASH_STACKED_PC`
  before printing the string.
Everything numeric — GEN PC, VECTOR, SR, D0-D7, A0-A6, FRAME SP, USP, STATE — was a **display artifact** in 0289 and
must not be used as crash evidence.

## BUILD-NUMBER CLIPPING
**PROVEN + FIXED.** The 4-digit build string was placed at column 39 of an H40 (40-column) screen, leaving room for
one character (`BUILD 0`). Moved "BUILD " to col 30 and the number to col 36 (cols 36-39). Validated: Build 0290's
screen shows the full **BUILD 0290**. The automatic generation mechanism (`crash_build.inc` from the numbering
counter) is unchanged.

## SCREEN VS WRAM CONTROLLED VALIDATION
**PASS (SCREEN == RECORD).** Controlled ILLEGAL (0x4AFC) at 0x00FF9000 with pre-set sentinels, Build 0290,
Genesis-NTSC MAME. The WRAM record and the rendered screenshot were captured in the same run and compared
field-by-field:

| Field | WRAM record | Screen | Match |
|---|---|---|---|
| VECTOR | 04 | 04 | ✓ |
| GEN PC | 00FF9000 | 00FF9000 | ✓ |
| SR | 2700 | 2700 | ✓ |
| D0..D7 | DEAD0000,D1D1D1D1,…,D7D7D7D7 | identical | ✓ |
| A0..A6 | A0A0A000,…,00FF0000,A6A6A6A6 | identical | ✓ |
| FRAME SP / USP | 00FEFF64 / 00000000 | identical | ✓ |
| STATE +00/02/04/34/200 | 0002/0003/0001/0000/00A5 | identical | ✓ |
| SRC | (0xFF9000 > ROM end) | UNKNOWN | ✓ |
| BUILD | 0290 | 0290 | ✓ |

Evidence: `states/traces/build0290_crash_screen_value_validation/` (wram_record.txt + crash_screen_matches_record.png).

## BUILD0287 VS BUILD0288 GENERATED DIFF
**PROVEN.** Byte diff of the preserved ROMs (0287 vs 0289; 0288≡0289 handler): the ONLY differing regions are
`0x000000-0x0000FF` (vector table), `0x00018E-0x00018F` (ROM header checksum), and `0x0003A4-0x00124F`
(boot/crash-handler code). **The arcade-copy region (0x00117E-0x0600F4) and the genesis-only region
(0x0600F4-0x184A34) are byte-identical.** Boot code `0x202-0x3A4`, the reset entry, initial SSP (0x00FF0000), and the
VINT vector (0x000700C2) are all identical. Change classification: (A) intended crash-handler/vector code — the
crash stubs moved, so their vector entries were regenerated; (B) intended crash font/data — inside the handler; (C)
build-number data — `crash_build.inc`; (D) relocation — the reserved-vector default target moved 0x440→0x4DC; (E)
**UNEXPECTED gameplay change: NONE.**

## GENESIS-ONLY ADDRESS / RELOCATION AUDIT
**PROVEN.** Because the genesis-only region is byte-identical between 0287 and 0289, no genesis-only symbol moved and
no copied/patched/genesis operand referencing genesis-only code changed. (The crash-handler growth was absorbed
within the boot object without shifting the arcade-copy or genesis-only regions; total ROM size is identical at
1,591,860 = 0x184A34.) No stale/mis-relocated reference exists.

## VECTOR / BOOT AUDIT
**PROVEN.** SSP (0x00FF0000) and RESET (0x00000202) unchanged; VINT/IRQ6 (0x000700C2) unchanged. The changed
exception vectors (bus/addr/illegal/…/TRAP) and reserved/HINT/EXT vectors point to crash stubs / `_crash_stub_other`
that merely moved (0x440→0x4DC) but are **semantically identical** (both decode to the same halting stub:
`move.w #63,CRASH_EXCEPTION_TYPE; bra _crash_common` in 0289 vs `moveq #63,d0; bra _crash_common` in 0287). No normal
boot/interrupt behavior changed. No vector overlap or displaced fixed-address structure.

## MAKEFILE BUILD-NUMBER AUDIT
**PROVEN.** The `crash_build.inc` rule only writes the 4-digit build string (`next = last-consumed + 1`, matching the
numbering stage) and is a prerequisite of `vdp_comm.o` only. It does not alter `RASTAN_GAMEPLAY_HUD_SPRITES` (built
=2 throughout), does not reorder patch generation, and does not affect any gameplay object. Not causal.

## GAMEPLAY-START REGRESSION ROOT CAUSE
**DISPROVEN as a Build0288 regression.** There is no 0287→0288 gameplay-code change (byte-identical). The single
68000-illegal instruction in all executable genesis-only code is `tst.l %a5` (`0x4A8D`) at runtime **0x073212**,
inside `.Lnq_transient_items_emit` (`pc090oj_native_emit_pass+0x90`), added by the **Build0286** transient-item
conversion (`tst.l transient_items_source_ptr`). `tst` with an address-register operand is a 68020+ instruction and
faults as **ILLEGAL** on the Genesis 68000. (Every other `4A8x`/`4Aax` in the image is legal `tst.l Dn` /
`tst.l (d16,An)` or asset/WRAM data mis-disassembled.)
- **PROVEN empirically:** driving Build0289 in Genesis-NTSC MAME reaches this crash at frame 610 in attract (scene 0)
  at GEN PC 0x073212, in BOTH 0287 and 0289 (identical).
- **PROVEN by neutralization:** a throwaway ROM with only `0x073212` `4A8D→200D` (`move.l %a5,%d0`, legal, identical
  Z-flag) runs **1500 frames with NO crash** and advances into the demo/gameplay umbrella (outer state 0x0002),
  proving gameplay itself is healthy and the illegal `tst.l %a5` is the SOLE crash.
So the perceived "0288 gameplay-start freeze" is the SAME pre-existing Build0286 `tst.l %a5` crash. The Build0288
crash-handler rewrite only changed how a crash LOOKS: the old handler cleared just Plane A and printed cursor-address
"values", leaving game graphics on-screen so a halt looked like a running-but-stuck game; the new handler renders a
clean `HALTED`, making the same crash obvious.

## FORWARD FIX
- **Applied (Part A):** the D2-preserving fix in the three `_at` wrappers and the build-number column move. Validated
  SCREEN == RECORD (above). This is the actionable, in-scope fix and is what makes future crash screenshots
  trustworthy.
- **NOT applied (Part B):** the `tst.l %a5` correction. It is the Build0286 transient-item / item-page crash, which
  this task **explicitly forbids fixing** ("Do NOT fix the item-page crash"; "Do not modify the Build0286
  transient-item family"). It is therefore deferred, not applied — the transient-item family is byte-for-byte
  unchanged in Build 0290 (`0x073212` still `4A8D`). The exact ready fix when authorized is byte-neutral:
  `0x4A8D` (`tst.l %a5`) → `0x200D` (`move.l %a5,%d0`), preserving the Z-flag semantics; source line
  `apps/rastan-direct/src/pc090oj_hooks.s:1547` `tst.l %a5` → `move.l %a5,%d0`.
**Note on the two-boundary model:** the evidence shows the "gameplay-start freeze" and the "item-page crash" are the
SAME single instruction (`tst.l %a5`, Build0286), not two separate regressions. With the corrected crash screen,
Tighe's next reproduction will display GEN PC `0x00073212` + SRC `GENONLY`, confirming this directly.

## ITEM-PAGE CRASH — STILL OPEN
The `tst.l %a5` crash (0x073212, Build0286) remains **OPEN** and untouched. The corrected crash screen (Build 0290)
now identifies it precisely on the next reproduction.

## DOCUMENTATION UPDATES
KNOWN_FINDINGS / CLOSED_ISSUES / GRAPHICS_STATUS / OPEN_ISSUES updated: numeric-renderer D2-clobber (fixed, screen==
record proven); Build0289 screenshot numeric values were INVALID; only NAME/SRC were trustworthy; build-number
clipping fixed; the 0287→0288 gameplay "regression" is DISPROVEN as a code change (byte-identical) and is the
pre-existing Build0286 `tst.l %a5` item-page crash; no Build0286 item conversion rollback occurred.
