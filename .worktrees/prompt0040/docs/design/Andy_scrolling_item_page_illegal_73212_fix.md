# Scrolling Item Page — Illegal Instruction Fix at GEN PC 0x073212 (Build 0295)

**Baseline:** Build0294 (screenshot-first crash handler in high-ROM `.crash`; Tighe verified good gameplay and a
clean crash screen on the item page). **No rollback**; all numbered ROMs preserved. Labels: **PROVEN / HYPOTHESIS /
DISPROVEN**.

## USER CRASH EVIDENCE
Build0294 item-page crash screen (Tighe): `ILLEGAL INSTR / VECTOR 04 / GEN PC 00073212 / SRC GENONLY`.

## STATIC CRASH-SITE PROOF
**PROVEN.** Source `apps/rastan-direct/src/pc090oj_hooks.s:1547` — `tst.l %a5` inside `.Lnq_transient_items_emit`:
```
.Lnq_transient_items_emit:
    tst.w   transient_items_active
    beq     .Lti_done
    move.l  transient_items_source_ptr, %a5
    tst.l   %a5                       <-- illegal
    beq     .Lti_done
```
Generated disasm at runtime **0x073212**: `4a8d` (objdump: `.short 0x4a8d`), followed by `73214: 6700 002a beqw
0x73240` (= `.Lti_done`). `TST` with an address-register operand (mode 001) is a **68020+** instruction; on the
Genesis **68000** it is illegal → vector 4. Purpose: test whether the loaded transient-item source pointer in A5 is
zero and skip the emit loop if so. **Required condition: Z = (A5 == 0)** (the following `beq` skips when A5 is null).

## REGISTER-LIVENESS PROOF
**PROVEN — D0 is dead at this site**, so the byte-neutral `move.l %a5,%d0` (which sets Z=(A5==0) but writes D0) is
safe:
1. `.Lnq_transient_items_emit` has **exactly one caller** (`bsr` at pc090oj_hooks.s:2174, inside
   `.Lnq_frontend_object_scan`).
2. After that `bsr` (and the `movem.l (%sp)+,%a4-%a6` restore) the caller reaches `.Lnep_after_native_scores: moveq
   #0,%d6`, then the object-RAM loop, which **writes D0 (`move.w %d6,%d0`) before ever reading it** — D0 is not read
   across the call.
3. The function itself already does not preserve D0: its loop calls `.Lnq_emit_entry`, whose first instruction is
   `move.w %d3,%d0` — so D0 is clobbered on the loop path regardless.
Therefore no path or caller relies on D0 being preserved across this function; writing D0 here changes nothing.

## LEGAL 68000 REPLACEMENT
**Applied:** `tst.l %a5` → `move.l %a5, %d0`. Opcode `0x4A8D` → `0x200D` — **byte-neutral** (2 bytes → 2 bytes),
legal on the 68000, sets N/Z from A5 exactly as `tst.l %a5` would, does not alter A5, no stack use. This is the same
instruction the earlier diagnostic experiment used, now proven safe by the D0-liveness analysis above. No transient-
item semantics changed.

## GENERATED OPCODE VERIFICATION
**PROVEN.** After a clean rebuild the site remains at runtime **0x073212** (byte-neutral, so all following addresses
are unchanged): `73212: 200d movel %a5,%d0` then `73214: 6700 002a beqw 0x73240` (unchanged) and the item loop at
`73218` (unchanged). Invariants: `genesistan_crash_handler_end`=0x117E, `_vblank_service`=0x700C2,
`z80_driver_start`=0x18492C, `_crash_stub_bus_error`=0x185000 — all unchanged.

## BUILD0294 DIFFERENCE ACCOUNTING
**PROVEN.** 0294 vs 0295: same size (1,597,112), **total 5 differing bytes**:
- **0x073212–0x073213**: `4A 8D` → `20 0D` (the fix) — the only genesis_only/gameplay difference.
- **1 byte in the high `.crash` section**: the crash-screen build-number string (`0294`→`0295`).
- **2 bytes in the ROM header**: checksum.
No other normal-runtime difference. arcade_copy, gap, boot code, and the rest of genesis_only are byte-identical.

## ITEM-PAGE BOUNDED VALIDATION
**PASS.** Genesis-NTSC MAME attract run (42s / 2400 frames), watching `transient_items_active` (0xFF68B4) and the
crash flag:
- Build0294 (and 0287–0293) crashed at 0x073212 at ~frame 610 in attract.
- **Build0295: NO CRASH in 2400 frames**, with the transient-item family **active for 1791 frames** — i.e. the item
  page was reached and the repaired 0x073212 site executed repeatedly (the emit loop ran) **without faulting**. The
  attract loop continued past the item page with no different exception.
So: execution passes the repaired site (YES); the old VECTOR 04 @ 0x073212 no longer occurs (YES); the item page
continues/displays (YES); no different crash encountered. Evidence:
`states/traces/build0295_item_page_illegal_fix_validation/`.

## TRANSIENT-ITEM SEMANTIC SANITY CHECK
**PROVEN unchanged** (only the one instruction changed): active-flag gate (`tst.w transient_items_active`), source
pointer load (`transient_items_source_ptr`→A5), null-pointer skip (now via `move.l %a5,%d0; beq`), 0xFFFF terminator
(`cmpi.w #0xFFFF,%d1`), 8-byte stride (`addq.l #8,%a5`), Y-scroll transform (`sub.w transient_items_scroll,%d2`;
drop at `<=16`), and the source-A/B latch (set by the copy hook) are all intact. The 1791 active frames without a
secondary CPU fault confirm we did not mask the illegal opcode while creating another obvious fault.

## HIGH-ROM CRASH-HANDLER INVARIANTS
**PROVEN unchanged.** The screenshot-first handler stays entirely in the high `.crash` section; `.crash` placement,
`genesistan_crash_handler_end`=0x117E, arcade_copy start=0x117E, RESET, VINT, PC080SN, palettes, collision, map
rendering, and all other PC090OJ code are unchanged. No low-ROM growth.

## BUILD
- **GATE_PASS**; numbered **Build 0295**. ROM
  `dist/rastan-direct/rastan_direct_video_test_build_0295.bin`, SHA-256
  `0cb1779e8b9c24e57a774a75cd2e6f08ef9a4232f02ebe37f7ca125c59bb891a`, size 1,597,112, counter 294→295. All numbered
  ROMs preserved; no second release run.
- Canonical verifier: PASS (byte-neutral; coverage 0x185EB8 unchanged; opcode_replace 228). Boot guard PASS (pre+post).
- Makefile smoke: PASS (30s Genesis-NTSC, 979.99%, no crash).

## RESULT
The item-page illegal-instruction crash (`tst.l %a5` @ 0x073212) is fixed with a byte-neutral legal replacement; the
scrolling item page now runs the transient-item emit without faulting. Only the illegal-instruction issue is closed;
broader transient-item visual correctness (item art/palette/scroll appearance) is deferred to Tighe's interactive
look. Any separate first-fortress/second-rope issue was not touched.
