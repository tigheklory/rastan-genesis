# Andy/Fable — Build 0196 Player-Control Input Rebase (256) + Build 0197 Mirror-192 Comparison

**Date:** 2026-07-17
**Type:** Bounded input-layer fix (+10 opcode_replace) + two config builds + state-causality trace of the remaining control blocker.
**Produced:** Build 0196 (256) `2d155d2de3cfd1eaeca905d60fd6eb68ffa10c3cf798320807e9e8f318f0b72b`, Build 0197 (192) `386fe4f51618727eb23d773182505a29665c4fd792ea893dae5d8729239a3c5c`; both 1,582,876, counters 196/197, GATE_PASS, deterministic.

## Build 0195 / 128 rejection recorded
Tighe (BlastEm): near-full speed, reduced black bar, but **Rastan cut off at the waist / lower player sprites missing**; no enemies; uncontrollable. → 0195/128 preserved as timing diagnostic, **rejected as gameplay candidate**. Main build returns to 256; 192 is the new reduced comparison. Mirror-count clarification: PC090OJ mirror records are **8-byte records** — 192 records = 1,536 bytes of mirror space; this is unrelated to the Genesis 80-hardware-sprite limit (SAT capacity), which stays 80.

## Primary control classification — **C** at the read layer (fixed), with **E** remaining
**C (proven & fixed):** input IS sampled and written, but the arcade player-control code read a DIFFERENT address — raw literal `0x10C016` (= ROM on Genesis, constant 0xEFFF = active-low "nothing pressed") instead of the real latch at mapped `0xFF0016`.
**E (remaining, out of this task's scope):** with the reads fixed, control is still blocked because the player-control routine (arcade 0x52732) is **never dispatched** — the gameplay state machine skips its `jsr` (frozen-progression root, same as missing enemies).

## Input chain (full state-causality, proven)
1. **Genesis pad → shadows:** `rastan_direct_update_inputs` (tilemap_hooks.s, runs every VBlank service) writes active-low shadows `genesistan_shadow_input_390001/03/05/07` (0xFFA1A8..AB). P1 byte = Genesis TH-high read | 0xC0: bit0=Up, 1=Down, 2=Left, 3=Right, 4=B(=arcade button1/attack), 5=C(=button2/jump) — a 1:1 match to the arcade P1 port layout. Coin=A (390005), Start (390007) synthesized. Values verified: idle 0xFF, Right 0xF7, Left 0xFB, C 0xDF.
2. **Shadows → arcade latch:** arcade 0x3A772 (runtime 0x3A972; port reads at 0x3A4A2/0x3A778 ARE redirected in the ROM to `moveb shadow_390001` = `103900FFA1A8`) stores the held-input word at **A5+0x16 = 0xFF0016**, gated by A5+0x34 != 0 (measured = 1 in gameplay). Latch verified live: Right→0x00F7, Left→0x00FB, C→0x00DF.
3. **Latch → control readers (THE BUG):** eleven arcade sites read the latch as raw absolute `movew 0x10C016,%d0`. Build 0158 rebased ONE (0x5102E, the command source). The other **TEN** — `0x5277A` (btst #5 jump dispatch), `0x527D4/0x527E4/0x527F4/0x52804` (input branches), `0x528CA` (down, btst #1), `0x528DA` (up, #0), `0x528EA` (left, #2), `0x528FA` (right, #3), `0x52BC8` — still read ROM `0x10C016` = **0xEFFF, low byte 0xFF = "nothing pressed" forever**. KF-042/KF-044 raw-WRAM-literal class.

## Fix (Build 0196/0197)
+10 `opcode_replace` entries: `30390010C016` → `303900FF0016` at the ten arcade PCs (byte-neutral 6→6, the exact Build 0158 pattern). opcode_replace count 152→162 (spec expectations + both CANONICAL constants paired; manifest/address_map regenerated). Verified in both ROMs: all 11 sites rebased, 0 raw. Safety: with no buttons held the latch low byte = 0xFF = identical behavior to the old ROM constant, so the idle path is unchanged — zero regression risk; pressed inputs now actually reach the dispatch **when it runs**.

## Remaining blocker (traced, not fixed here — next boundary)
With the reads fixed, holding Right/Left/C still doesn't move Rastan because the ten readers **never execute**: the sole caller of the player-control routine is arcade **0x51090 `jsr 0x52732`**, and the master gameplay routine's default flow at **0x5108C `braw 0x51096` unconditionally skips that jsr**; the preceding gatekeeper `jsr 0x5132A` (player-state machine, A5+0x10E8-driven, → 0x51514 region) is what should route execution into 0x51090, and it never does. The master routine itself runs (the 0x5102E command read fires 437×/trace) — the freeze is specifically the player-state dispatch, consistent with KF-044 (player spawn state never completes). ZERO-hit proof on all reader/handler PCs (head "hits" were m68k prefetch artifacts of an adjacent routine, per the project's known +4/+6 tap caveat). **Next bounded task: why the 0x5132A/A5+0x10E8 state machine never activates the 0x51090 player-control call** — this is the same root as missing enemies and frozen scroll.

## Validation
| Check | 0196 / 256 | 0197 / 192 |
|---|---|---|
| GATE_PASS / SHA | ✓ `2d155d2d…` | ✓ `386fe4f5…` |
| generated config | 256 | 192 |
| opcode_replace count | 162 | 162 |
| TC0140SYT fix @0x3F2A4 | `0280fffffffe` ✓ | `0280fffffffe` ✓ |
| 0193 family-apply / 0192 gates | present ✓ | present ✓ |
| input rebase (11 sites) | all rebased ✓ | all rebased ✓ |
| title / READY | render ✓ | render ✓ |
| gameplay reached | ✓ | ✓ |
| Rastan | LEFT, **complete** (no waist cutoff) ✓ | LEFT, **complete** ✓ |
| BG/FG/palette | correct ✓ | correct ✓ |
| represented / SAT / player slots | 17 / 17 / 9 | 17 / 17 / 9 (identical composition) |
| VINT rate | 0.771 | **0.831** |
| control (left/right/jump move player) | **not yet** — blocked by the un-dispatched player routine (E) | same |
| 80-style corruption | none | none |

**192 safety result:** visually safe in MAME — records 120..137 preserved with 54-record margin above the 122 floor; player SAT composition identical to 256; rate bonus (0.831 vs 0.771). BlastEm lower-body check (the 0195/128 failure mode) pending Tighe.

## Not touched
Collision, enemies, scroll, black bars, 60 Hz, PC080SN/PC090OJ rendering (except the config variants), Builds 0175/0178/0180/0192/0193/0194 — all intact. Makefile default remains 256. 0195 preserved as rejected diagnostic.
