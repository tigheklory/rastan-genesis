# Andy — Transient Copy/Clear (0x056114 / 0x056440) Native Conversion (ANALYSIS; NO BUILD)

**Agent:** Andy · **Baseline:** current tree after Build 0285 (counter 285) · **Status:** analysis complete;
**NO numbered build** — native-ownership mechanism + runtime validation not established this session. Labels:
**PROVEN / HYPOTHESIS / DISPROVEN**.

## BASELINE
Current forward tree after Build 0285. No rollback. All ROMs 0280–0285 preserved. 0x05A502 GAME OVER stays
OPEN/BLOCKED (out of scope). 0x05607C transient decay stays untouched (next unit).

## ORIGINAL 0x056114 SEMANTICS — **PROVEN: treasure/item transient sprite copy**
`0x056114` is a generic 4-word-tuple copy loop: `move.w a0@,d0 ; cmpi #-1,d0 ; beq end ; [copy word0,Y,code,X
(a0)+→(a1)+] ; loop`. It copies a ROM tuple stream (A0) to a destination (A1) until a 0xFFFF terminator.
- Callers set the source and dest: **0x05604C** → source **0x56226** (17 tuples), **0x056076** → source
  **0x562B0** (3 tuples); both dest **0xD00170** (object_ram; runtime hook `genesistan_pc090oj_hook_copy_56114`,
  patched_site 0x561EE). 0x05604C also saves the end-dest to a5@0x141C.
- The tuples are **treasure/item pickup sprites** (verified by rendering the codes): chalices/goblets, gems/
  jewels, a shield, a mace, a spear (codes 0x50D–0x516 nibble 3; 0xA5A–0xA70 nibble 0). word0 attr 0x0003/0x0000
  (no flip). Y spans 64–476 (several on-screen near the top, most parked below the 224 viewport). X ≈ 8–56.
- These are NOT "records 64–67"; that is only the old hardware slot. (Note: the arcade dest is 0xD00170 =
  object_ram record 46; the audit's "64–71" numbering differs — the semantic identity is treasure/item sprites,
  not a slot range.)

## ORIGINAL 0x056440 SEMANTICS — **PROVEN: the item clear/retire**
`0x056440`: `a1=0xD00000+0x170 ; movew #9,d0 ; movew #8,d1 ; bsr 0x5648A (fill) ; bsr 0x561A0`. It clears/parks
the item records at **0xD00170** (the same range the copy fills). It is the LIFECYCLE retirement of the items.

## COPY / CLEAR SEMANTIC RELATIONSHIP — **PROVEN**
Both operate on the **same** object_ram region 0xD00170. They are two phases of ONE sequence driven by the
state machine **a5@0x13AA** (5034): state 2 (via 0x5602C) sets up/copies the items; states 3–7 animate/wait
(state 4 runs 0x5607C — the separate decay, NOT this task); **state 8 (0x55F0E) calls 0x056440 to clear**, then
transitions to 255. So 0x056440 retires state owned by the same item sequence, not a distinct group. Records
"68–71" are hardware/lifecycle maintenance for the same family, not a second semantic object.

## PC090OJ CUT POINTS — **PROVEN**
- Copy: the semantic is the ROM tuple stream (0x56226/0x562B0) and the state-machine activation; the PC090OJ-
  specific part is writing them to the object_ram dest (A1=0xD00170) via the `(a1)+` stores. Cut = redirect the
  output from object_ram to native emission.
- Clear: the semantic is "items retire"; the PC090OJ-specific part is parking object_ram records. Cut = "stop
  contributing native pieces" instead of parking.

## NATIVE OWNERSHIP — candidate, **NOT fully established (blocker)**
By priority these treasure/item sprites are frontend/effect pieces. The established frontend direct-emit path is
`native_frontend_hud_emit` → `.Lnq_emit_entry`, invoked in `.Lnq_frontend_object_scan`. A native
`.Lnq_transient_items_emit` reading the item state (source ptr + active flag set by the converted copy, cleared
by the converted clear) and emitting the tuples via `.Lnq_emit_entry` is the intended shape.

## BLOCKERS (why NO build this session)
1. **Frontend native-commit mechanism not established (same as GAME OVER):** these items render only via the
   frontend **object-RAM scanner** (scene != 1). The native LANES (HUD/MIDDLE/FRONT_EFFECT…) are committed by
   `.Lnq_gameplay` (scene 1) — NOT by `.Lnq_frontend_object_scan`. Converting to "direct native" therefore
   requires a frontend-direct emitter (like `native_frontend_hud_emit`) plus a small Genesis-only item-state
   (active flag + source ptr). Whether this is the accepted mechanism (vs. the task's "use the established
   native tuple emission path" without any new frontend state) is **not settled**; a wrong choice risks the
   forbidden "new virtual transient table."
2. **Complex sequenced lifecycle (HYPOTHESIS):** the items belong to an 11+-state machine (a5@0x13AA). The copy
   uses two sources at the same dest (0x56226 then 0x562B0) whose exact accumulation/overwrite timing across
   states is not fully proven; a native emitter must reproduce it precisely.
3. **No runtime validation:** controlled Genesis-NTSC MAME could not be driven this session (build's own
   make-invoked smoke works; direct `mame genesis` invocations produce no output). The treasure/bonus state is
   also not trivially reachable by controlled input, so Part-9 validation (correct pieces/art/X/Y/flip/palette/
   order/retire/no-stale) cannot be confirmed.

Per the IMPLEMENTATION GATE ("native ownership: PROVEN", "bounded validation: PASS", STOP if unresolved), these
are not met, so no numbered build is produced.

## IMPLEMENTATION (designed, NOT applied)
When the frontend-commit mechanism is decided and validation is available: (a) add Genesis-only
`transient_items_active` + `transient_items_src`; (b) convert 0x056114 to set src+active instead of the object_
ram copy (spec shift_replacement, keep the ROM source and terminator scan); (c) convert 0x056440 to clear active
instead of parking; (d) add `.Lnq_transient_items_emit` in `.Lnq_frontend_object_scan` that, if active, walks the
source stream and emits each tuple via `.Lnq_emit_entry`; (e) remove the copy/park helpers (0x561A0/0x5648A
tail) only if xref-proven dead for this family. Keep pc090oj_object_ram/scanner/decoder (other families).

## DEAD COMPATIBILITY OUTPUT
Pending implementation. After conversion: object_ram 0xD00170 range no longer live for this family; the copy hook
(`genesistan_pc090oj_hook_copy_56114`) and the park hook (`genesistan_pc090oj_hook_zero_fill_56440`) become dead
for this family. Generic scanner/decoder remain (other families). 0x05607C untouched.

## VALIDATION
Not performed (blocker 3). Semantics/state-machine mapped statically; native-path proof pending blockers 1–2.

## DOCUMENTATION UPDATES
No ledger edits (no conversion landed); this report is the durable record.

## REMAINING PC090OJ DEBT (order)
1. Transient copy/clear 0x056114/0x056440 (this unit — analysis done, blocked on frontend-commit mechanism +
   validation); 2. transient decay 0x05607C; 3. setup/priority + legacy park/fill maintenance; 4. 0x05A502 GAME
   OVER (blocked on its WRAM state gate); 5. final frontend compatibility infrastructure.
