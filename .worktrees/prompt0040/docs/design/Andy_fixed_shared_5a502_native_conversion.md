# Andy — Fixed/Shared 0x05A502 Native Conversion (ANALYSIS; NO BUILD)

**Agent:** Andy · **Baseline:** current tree after Build 0285 · **Status:** analysis complete; **NO numbered
build** — the implementation gate is not satisfiable this session (native-ownership gate unproven + runtime
validation unavailable). Labels: **PROVEN / HYPOTHESIS / DISPROVEN**.

## BASELINE
Current forward tree after Build 0285 (counter 285). 0283 accepted, 0284 rejected/preserved, 0285 current
candidate. No rollback.

## ORIGINAL 0x05A502 SEMANTICS — **PROVEN: the "GAME OVER" text producer**
Arcade 0x05A502 (runtime 0x05A5F6) emits a **fixed 8-glyph sprite text = "GAME OVER"**:
- Codes 0x37,0x38,0x3F,0x40,0x41,0x42,0x43,0x44 = **G,A,M,E,O,V,E,R** (verified by rendering the tiles).
- Layout: word0=0 (palette nibble 0, no flip), Y=d1, X=0x60,0x70,0x80,0x90,0xB0,0xC0,0xD0,0xE0 ("GAME" then a
  +0x20 gap then "OVER"). Records 83–90 (object-RAM offsets 0x298 and 0x2B0).
- Y = d1: `movew 0x10C200,d0; btst #5,d0` → bit5 set ⇒ Y=**0x180 (parked/hidden)**, bit5 clear ⇒ Y=**0x70
  (visible)**. i.e. a blink/visibility state.
- Caller: arcade 0x05104E (`jsr 0x5A502`) in the **gameplay** main sprite-build loop, gated `a5@0x34 == 0`.
- Records 83–90 are hardware slots, **not** semantic identity — the semantic identity is "GAME OVER text".

## PC090OJ HARDWARE CUT POINT — **PROVEN**
State logic (0x5A502–0x5A51A: read 0x10C200 bit5 → Y=d1; X start=0x60) is semantic. The PC090OJ-specific output
begins at the two destination immediates:
- **0x05A51E** `movea.l #0x00D00298,a0` (records 83–85) → runtime 0x05A612 (patched_site).
- **0x05A554** `movea.l #0x00D002B0,a0` (records 86–90) → runtime 0x05A648 (patched_site).
Everything after each is `move.w`/`(a0)+` record packing. Cut is immediately before 0x05A51E.

## 0x05A51E / 0x05A554 DESTINATION ANALYSIS — **PROVEN**
Currently declared as `opcode_replace[115]` (0x05A51E `207C00D00298` → `207C{pc090oj_object_ram+0x298}`) and
`[116]` (0x05A554 `207C00D002B0` → `207C{pc090oj_object_ram+0x2B0}`). They redirect the arcade's raw 0xD00298/
0xD002B0 writes into the transitional `pc090oj_object_ram`, which the frontend scanner renders. On native
conversion both become dead **for this family** (no other caller uses these two literals).

## NATIVE OWNERSHIP — candidate, **NOT fully proven**
The established frontend fixed-text mechanism is `native_frontend_hud_emit` / `.Lnq_title_labels` →
`.Lnq_emit_entry` (direct SAT emit at VBlank in `.Lnq_frontend_object_scan`). GAME OVER is a fixed frontend
glyph row and belongs to the SAME direct-emit ownership. A native `.Lnq_gameover_emit` gated on the game-over
state, emitting the 8 glyphs via `.Lnq_emit_entry`, is the intended shape.

## BLOCKERS (why NO build this session)
1. **Broken state read (PROVEN):** the postpatched producer reads **absolute 0x10C200 = cart ROM** (built ROM
   byte 0x10C200 = **0xDFFD**, bit5 **SET** ⇒ Y=**0x180 parked**), not the intended WRAM `a5@0x200` = 0x00FF0200.
   Reason: `wram_immediate_relocation.enabled = false` (KF-044, gated off because enabling it regresses the
   0x10D1B2 pre-spawn progression). ⇒ **On Genesis the GAME OVER text is currently always-parked / never
   displayed.** A faithful native conversion would reproduce "never displayed" (pointless); a *correct* one must
   read the WRAM state — a behaviour change with real risk that cannot be validated here.
2. **Scene/gate unproven (HYPOTHESIS):** records 83–90 are produced by the **gameplay** main loop (scene 1,
   0x5104E), but scene 1's `.Lnq_gameplay` does **not** scan object_ram — the render only occurs in a frontend
   scene (`.Lnq_frontend_object_scan`). The exact game-over scene value and whether `a5@0x34 == 0` is
   game-over-specific among frontend scenes are **not proven**; a wrong gate would show GAME OVER in the wrong
   scene or consume SAT slots.
3. **No runtime validation:** controlled Genesis-NTSC MAME could not be driven this session (the build's own
   make-invoked smoke works, but direct/background `mame genesis` invocations produced no output). Part-7
   validation (pieces appear/correct code/X/Y/flip/palette/order/lifecycle/no-stale) cannot be performed.

Per the IMPLEMENTATION GATE ("native ownership: PROVEN", "bounded validation: PASS"), these are not met, so no
numbered build is produced.

## IMPLEMENTATION (designed, NOT applied)
When the blockers are resolved: (a) add `.Lnq_gameover_emit` (fixed `{code,X}` table for the 8 glyphs) reading
the WRAM game-over state (a5@0x200 bit5 → Y; game-over-scene gate) and emitting via `.Lnq_emit_entry`; call it in
`.Lnq_frontend_object_scan` after `native_frontend_hud_emit`. (b) Spec: retire 0x5A502's object-RAM output and
remove `opcode_replace[115]/[116]`. (c) Keep `pc090oj_object_ram`, scanner, decoder (other families still use
them).

## DEAD PC090OJ OUTPUT
After conversion (once implemented): records 83–90 no longer live for this family; the two destination patches
(0x05A51E/0x05A554) become dead and are removed. Generic scanner/decoder remain (other families).

## VALIDATION
Not performed (blocker 3). Static proof of semantics complete; native-path proof pending blockers 1–2.

## DOCUMENTATION UPDATES
Pending build; not applied this session beyond this report (no premature ledger edits since no conversion
landed).

## REMAINING PC090OJ DEBT (retirement order, unchanged)
1. 0x05A502 GAME OVER (this unit — blocked, see above); 2. transient copy/clear family; 3. transient decay
family; 4. setup/priority + legacy park/fill maintenance; 5. final frontend compatibility infrastructure.
