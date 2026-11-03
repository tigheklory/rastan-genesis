# Andy — Missing "GH" in HIGH SCORE Header (Focused Analysis, Outcome A)

**Agent:** Andy. **Type:** Focused analysis / runtime evidence. **No source, no ROM, no build number.**
**Baseline:** `rastan-direct-proposal` @ `a2d048516833c44bf60dbdcaed76e0a963a3d6f7`; accepted ROM
`dist/rastan-direct/rastan_direct_video_test_build_0145.bin` = `b5c903a942b669e869b5b2d4ed4448f96d402707e3dcda946afabe2eb4dd23f7`.
**Evidence dir:** `states/traces/missing_gh_high_score_header/`.

## Outcome
**Outcome A — exact producer and divergence proven.** The Genesis header shows `HI SCORE` instead of `HIGH SCORE`
because the Genesis helper `genesistan_pc090oj_hook_target_3b902` (arcade replacement for `arcade_pc 0x03B902`)
fills PC090OJ mirror records **0 through 4** with `(word0=0, Y=0, code=1, X=0)`, whereas the authoritative arcade
`0x03B902` writes records **17 through 21** (`HW_ADDRESS 0x00D00088`). The Genesis helper's record base/range is
wrong (base 0 instead of base 17), so it overwrites record 4 — the `GH` glyph that the `0x03B930` producer had
already correctly placed — after the correct descriptor was written. Records 5–8 (`HI`/` S`/`CO`/`RE`) lie outside
the 0–4 range and survive, yielding exactly `HI` + gap + ` SCORE`.

## Settled prior evidence (not re-derived)
Header composed of two-character PC090OJ sprites: rec 5 `0x3A`="HI", **rec 4 `0x3B`="GH"**, rec 6 `0x3C`=" S",
rec 7 `0x3D`="CO", rec 8 `0x3E`="RE". First final-state divergence = record 4. Arcade record 4 =
`word0 0, Y 0, code 0x3B, X 0x88`; Genesis mirror record 4 = `word0 0, Y 0, code 0x0001, X 0x0000`. Record 4 is
represented on SAT slot 0 and faithfully rendered — the renderer is drawing the wrong mirror descriptor (not a
representation/SAT/palette/pattern failure). Records 5–8 match the arcade.

## 1. Destructive emit call (captured)
Breakpoint at the emit-helper entry `runtime_genesis_pc 0x00071976`, condition `d0 == 4`, one hit
(`states/traces/missing_gh_high_score_header/emit4_trace.log`):
```
EMIT4  ra=0x00071B14  d0=0x0004 d1=0x0000 d2=0x0000 d3=0x0001 d4=0x0000
       rec4_before_call = 0000 0000 003B 0088   (= the correct GH descriptor)   state 0/0/0
```
The helper stores `d1→word0, d2→Y, d3→code, d4→X`, so this call writes record 4 = `(0,0,1,0)`, overwriting the GH
descriptor that was present immediately before the call.

## 2. Exact return address and caller instruction
`ra = 0x00071B14`. Disassembly (`build/genesis_postpatch.disasm.txt`):
```
71b02: 7000            moveq #0,%d0                 ; record index = 0
71b04: 3401            move.w %d1,%d2               ; fill-loop body start
71b06: 7200            moveq #0,%d1
71b08: 7601            moveq #1,%d3                 ; code = 1
71b0a: 7800            moveq #0,%d4                 ; X = 0
...
71b10: 6100 fe64       bsr.w 0x71976                ; -> emit_slot
71b14: 5240            addq.w #1,%d0                ; <- return address (caller instruction)
71b16: 0c40 0005       cmpi.w #5,%d0
71b1a: 65e8            bcs.s 0x71b04                ; loop while d0 < 5  (records 0,1,2,3,4)
```
`0x71B14` is inside the fill loop of `genesistan_pc090oj_hook_target_3b902` (entry `0x71AE0`).

## 3. Genesis producer/helper responsible
- **Symbol:** `genesistan_pc090oj_hook_target_3b902`
- **runtime_genesis_pc:** entry `0x00071AE0`; destructive call site `0x00071B10` (returns `0x00071B14`)
- **genesis_rom_offset:** `0x03BB02` (`address_map.json`: patched_site, `arcade_start 0x03B902`, `origin opcode_replace`)
- **arcade_pc:** `0x03B902`
- **patch-manifest classification:** PC090OJ "Strategy A" function-body replacement; note states "Helper emits SAT
  slots 0..4," intercepting 8 callers (`0x03A20E/0x03A264/0x03A640/0x03A6C4/0x03A820/0x03B8E8/0x03B8F0/0x03A8E0`).
- **Loop/record logic:** fill path (`d1!=0`) loops `d0 = 0..4` (`cmpi.w #5,%d0; bcs`), each iteration calling
  `emit_slot` with `d1=0, d3=1 (code 1), d4=0 (X 0)`; the clear path (`d1==0`) likewise loops records 0..4.
- **Why `(0,0,1,0)` for record 4:** it is iteration `d0==4` of the fixed 0..4 fill with hardcoded `code=1, X=0`.
- **Records 0–4 all affected:** yes — the loop writes records 0,1,2,3,4. Record 4 is the only one holding a visible
  HIGH-SCORE glyph (GH); records 5–8 (HI/ S/CO/RE) are outside the range and unaffected, which is exactly why the
  visible result is `HI SCORE`.

## 4/6. Arcade record-4 write sequence (`HW_ADDRESS 0x00D00020`, watchpoint)
`states/traces/missing_gh_high_score_header/arc_rec4_trace.log` — every title-init write, in order:
```
pc=0x0003AD48  word0=0x0000 Y=0x0100 code=0x0000 X=0x0100     (clear/init, code 0)
pc=0x0003B936  word0=0x0000
pc=0x0003B93C  Y=0x0000
pc=0x0003B942  code=0x003B                                    (GH)
pc=0x0003B94C  X=0x0088
```
Final arcade record 4 = `0000 0000 003B 0088` (GH). **The arcade never writes code 1 to record 4** — the only writes
to the code word `0x00D00024` are `0x0000` (clear) and `0x003B` (GH, from the `0x03B930` producer). The GH write is
last and survives.

Arcade `0x03B902` target confirmed at `HW_ADDRESS 0x00D00088` (record 17): watchpoint on `0xD00088`
(`arc_rec17_trace.log`) shows the `0x03B902` fill instruction `pc=0x0003B91E` writing `0x0001` to `0xD0008A`
(record 17, Y byte). The arcade original bytes for `0x03B902` begin `43F9 00D00088` (`lea 0x00D00088,%a1`) and loop
`move.b %d1,2(%a1); addq.l #8,%a1` ×5 → records 17–21. It does not address record 4.

## 7. Genesis record-4 write sequence (`WRAM_ADDRESS 0x00FF69D0`, watchpoint)
```
1. boot/initial clear
2. correct GH copied:            0000 0000 003B 0088   (from the 0x03B930-equivalent producer)
3. genesistan_pc090oj_hook_target_3b902 fill overwrites:  0000 0000 0001 0000   (code 1, X 0)  <-- FINAL
```

## 8. First exact arcade-vs-Genesis divergence
The Genesis `genesistan_pc090oj_hook_target_3b902` writes `pc090oj_object_ram` records **0–4** (mirror base
`0x00FF69B0`, i.e. arcade `0xD00000` base). The authoritative arcade `0x03B902` writes records **17–21**
(`HW_ADDRESS 0x00D00088`). The divergence is a **wrong record base/range** (cause #1 / #5): the helper routes the
arcade `0x03B902` operation to records 0–4 instead of 17–21, so it writes record 4 — an address the arcade
`0x03B902` never touches — clobbering the GH descriptor. (Secondarily, the helper emits a full `code=1` descriptor,
while the arcade `0x03B902` fill writes only byte 2 (Y) of records 17–21; but the GH loss is caused by the record
range alone, since any write to record 4 destroys GH.)

## 9. Why the correct GH descriptor is lost
Ordering within the frame: the `0x03B930`-equivalent producer correctly writes GH (`code 0x3B, X 0x88`) into mirror
record 4; then `genesistan_pc090oj_hook_target_3b902`'s fill loop, which iterates records 0–4, runs afterward and
overwrites record 4 with `(0,0,1,0)`. In the arcade the analogous fill targets records 17–21, so GH in record 4 is
never disturbed and the last write to record 4 remains GH.

## 10. Smallest implementation boundary (do not implement here)
`genesistan_pc090oj_hook_target_3b902` in `apps/rastan-direct/src/pc090oj_hooks.s` — the fill loop
(`.Lhook_3b902_fill_loop`) and clear loop (`.Lhook_3b902_clear_loop`) record range. They must target the arcade's
actual records (17–21, `HW_ADDRESS 0x00D00088`) rather than records 0–4, so record 4 (and the other HIGH-SCORE
records) is no longer clobbered. **Classification: copied-record / producer correction (wrong record range).** The
exact retargeting (records 17–21, or otherwise not overwriting records the arcade `0x03B902` does not write) and any
interaction with the `pc090oj_workram_block_sprites` family (records 0–21) is for the implementation task, not this
analysis.

## Files changed
None (analysis only). Documentation: this report; `AGENTS_LOG.md`; `OPEN_ISSUES.md`. Evidence:
`states/traces/missing_gh_high_score_header/` (`emit4_trace.log`, `arc_rec4_trace.log`, `arc_rec17_trace.log`,
`wp_trace.log`, `arc_title.bin`, `gen_title.bin`, snapshots). **Build produced: NO. ROM produced: NO.**

## OPEN_ISSUES impact
- **OPEN-024 (PC090OJ sprite subsystem incomplete):** materially advanced — one concrete title/header PC090OJ mirror
  defect is now root-caused: `genesistan_pc090oj_hook_target_3b902` writes records 0–4 instead of the arcade's
  17–21 (`0xD00088`), clobbering the HIGH-SCORE "GH" glyph in record 4. Documented next action: correct the helper's
  record range. Not closed.
- **OPEN-001 (title/attract graphics incomplete):** the missing "GH" in HIGH SCORE now has a proven cause (above),
  a PC090OJ producer record-range error, not a plane/tile/palette defect. Not closed.
- No issue closed; no duplicate opened.

## Architecture-compliance statement
CONFIRMED. Evidence gathered only via MAME debugger breakpoints/watchpoints, memory dumps, screenshots, source, and
disassembly. No production source, no diagnostic instrumentation, no new tooling, no ROM, no build number, no
temporary rendering path or state machine. Arcade code remained the execution owner throughout.

## Scope statement
Palette work (Builds 0143–0145), the separate state-dependent missing "UP" in "2UP", score values / extra zeros,
other header records, item-screen content, general sprite positioning, PC080SN, gameplay, audio, scrolling, and
real-hardware behavior were not investigated. Downstream paths (pattern DMA, SAT geometry, palette, final render)
were excluded by the proven mirror clobber and not inspected further.
