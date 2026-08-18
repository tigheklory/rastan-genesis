# Andy — Frontend Items + GAME OVER Native Conversion (Build 0286)

**Agent:** Andy · **Baseline:** current forward tree after Build 0285 (counter 285). **No rollback**; every
numbered ROM 0280–0286 preserved. Labels: **PROVEN / HYPOTHESIS / DISPROVEN**.

## BASELINE
Current tree after Build 0285. Preserved forward work (untouched): corrected player-aux direct-native conversion,
`RASTAN_GAMEPLAY_HUD_SPRITES=2`, native 0x5A098 status producer, Build0282 collision map, sword geometry/collision
fixes, A5+0x1338 correction, direct-native gameplay architecture. This unit converts two frontend PC090OJ
producer families to the established frontend-direct emission model and retires their object-RAM output.

## FRONTEND-DIRECT SEMANTIC OWNERSHIP
The approved model — `native_frontend_hud_emit` → `.Lnq_emit_entry` → Genesis SAT, invoked at the frontend
boundary in `.Lnq_frontend_object_scan` — is extended with two family-specific emitters:
`.Lnq_transient_items_emit` and `.Lnq_gameover_emit`. Both are called (frontend scenes only) immediately after
`native_frontend_hud_emit`, inside its existing `movem.l %a4-%a6` save bracket. Each emits pieces straight to the
native SAT through the **shared** `.Lnq_emit_entry`, which applies the *identical* coordinate/flip/viewport
transform as the retired object-RAM scanner (`.Lpc090oj_decode_record`), so native output reproduces the former
scan output exactly. **No new PC090OJ-shaped state** was introduced: no 8-byte records, no record numbers, no
generic sprite table, no scanner/decoder, no Y=0x180 park. The only added state is three small Genesis-only words
(see below). **PROVEN.**

## ITEM STATE MACHINE
The arcade item state machine `a5@0x13AA` (5034) is **preserved** — not replaced. **PROVEN** from the disasm:
state 2 (`0x55E5C`…) runs the copy setup (`0x5602C` → source A `0x56226`; a paired setup → source B `0x562B0`);
states 3–7 animate/wait; state 4 runs `0x5607C` (decay); state 8 runs `0x56440` (clear → 255). Only the
PC090OJ-specific *output/mutation* of each phase is replaced; the arcade progression is untouched.

## 0x056114 NATIVE CONVERSION
**PROVEN.** `0x056114` is a 4-word-tuple copy (`{word0/attr, Y, code, X}`, 0xFFFF-terminated on word0) from a ROM
stream (a0) to object RAM (a1). The arcade caller resolves a0 to the runtime source address via the shift-aware
relocation of its own `movea.l` (source A `0x56226`, source B `0x562B0`). The hook
`genesistan_pc090oj_hook_copy_56114` now **latches that live pointer** into `transient_items_source_ptr`, sets
`transient_items_active=1`, and clears `transient_items_scroll` — *no object-RAM write*. Rather than storing a
selector enum, we retain the caller's already-relocated live pointer (set fresh each copy), which the task permits
as non-fragile semantic state. `.Lnq_transient_items_emit` walks the stream and emits each tuple with the original
ordering / code-art / X / attr(word0) / flip / palette semantics preserved (passed unchanged to `.Lnq_emit_entry`),
honouring the original 0xFFFF terminator.

## 0x056440 NATIVE RETIREMENT
**PROVEN.** `0x056440` is the semantic end-of-life for the item family (formerly parked the object-RAM records).
The hook `genesistan_pc090oj_hook_zero_fill_56440` now sets `transient_items_active=0`; the emitter then
contributes no pieces. No parked-record emulation.

## 0x05607C DEPENDENCY / CONVERSION
**PROVEN — 0x05607C DEPENDS on the retired representation → converted in this candidate.** Its arcade loop
(`0x560B0–0x560D6`) iterated the item records (`0xD00170`…`a5@0x141C`), **decremented every record's Y by 1**, and
**blanked a record's code once its Y reached 16** — i.e. the whole item set scrolls up uniformly and each item
vanishes at Y≤16, throttled to every 4th frame (`a5@0x1392 & 3 == 0`). Because the decrement is uniform across all
records, that per-record mutation is exactly **one accumulated scroll offset**. The converted hook
`genesistan_pc090oj_hook_sprite_decay_5607c` now increments `transient_items_scroll` (same throttle) and
`.Lnq_transient_items_emit` applies it as `Y' = Y − scroll`, dropping any item at `Y' ≤ 16` — reproducing the
scroll + blank-at-16 semantics without any object-RAM/descriptor mutation. The two arcade side-effect clears
(`a5@0x10AE`, `a5@0x10B0`) are preserved verbatim. **After conversion there is no hidden dependency where a native
copy leaves 0x5607C mutating stale object RAM.** (Note — DISPROVEN as blockers, recorded for completeness: the
pre-existing hook already omitted the arcade's `a5@0x10EE` counter / `0x560DA` / `0x55AB4` palette-anim calls; that
omission predates this unit and is unchanged here — a separately-tracked item, not reintroduced.)

## GAME OVER SEMANTIC PERSISTENCE
**PROVEN.** The arcade producer `0x05A502` (records 83–90) is gated by its existing caller condition
(`0x05104E`, `jsr 0x5A502` gated `a5@0x34 == 0`) and re-emits every frame while game-over is active; the object-RAM
records are re-populated each frame (not a stale persistence). The native design therefore needs **no** persistent
Genesis latch and **no** invented scene gate: `.Lnq_gameover_emit` re-evaluates the arcade's own live conditions
each frame in the frontend scan. This is strictly faithful to the producer's own gate and has no
persistence/reset failure mode.

## GAME OVER STATE-SOURCE CORRECTION
**PROVEN — the broken absolute `0x10C200` cart-ROM read is removed.** The postpatched arcade producer read absolute
`0x10C200` (Genesis cart ROM = `0xDFFD`, bit5 set ⇒ always parked). `.Lnq_gameover_emit` instead reads the intended
WRAM fields at `a5 = 0xFF0000`: the game-over gate `a5@0x34` (absolute `0x00FF0034`; `0` = active — writers
`clr@0x3A460` / `#1@0x3A984`) and the visibility/blink bit `a5@0x200` **bit5** (absolute `0x00FF0200`; the arcade
`0x10C200` = arcade-a5(`0x10C000`)+0x200, so bit5 set ⇒ parked/hidden, clear ⇒ visible). This is a **local**
semantic correction; `wram_immediate_relocation` remains **disabled** (not enabled).

## GAME OVER DIRECT NATIVE OUTPUT
**PROVEN.** `.Lnq_gameover_emit`: if `a5@0x34 == 0` **and** `a5@0x200` bit5 clear, emit the eight glyphs from a
fixed `{X, code}` table — codes `0x37,0x38,0x3F,0x40,0x41,0x42,0x43,0x44` = G,A,M,E,O,V,E,R; X
`0x60,0x70,0x80,0x90,0xB0,0xC0,0xD0,0xE0`; attr(word0)=0 (palette line 0); Y=0x70 — the exact code/X/palette/order
the producer packed into records 83–90. Hidden ⇒ no pieces (no Y=0x180 park). Via `.Lnq_emit_entry`, no object-RAM
scanner/decoder dependency remains for this producer.

## DEAD PC090OJ OUTPUT
- Items: `0x056114` no longer writes object RAM; `0x056440` no longer parks records; `0x05607C` no longer mutates
  object RAM / `staged_sprite_descriptor_table`. The former `.Lpc090oj_emit_slot`/`.Lpc090oj_clear_slot` object-RAM
  writes for this family are gone.
- GAME OVER: producer `0x05A502` retired **byte-neutrally** (entry `clr.l d0` `0x4280` → `rts` `0x4E75`;
  `opcode_replace` count 227→228). Verified in the postpatched image: runtime `0x5A5F6 = 4E75`, the old broken
  `movew 0x10C200` now dead/unreachable at `0x5A5F8`. Records 83–90 are no longer produced.

## GAME OVER 0x5A51E / 0x5A554 DESTINATIONS
**RETAINED (dead) + WHY.** The paired `opcode_replace[115]/[116]` redirects (0x5A51E/0x5A554) are kept so the
now-unreachable tail's destination literals still resolve to `pc090oj_object_ram` (runtime `0x00FF7232`/`0x00FF724A`)
rather than leaving raw `0x00D002xx` literals in the image. **PROVEN:** grep of the postpatched disasm shows **0**
live `00D00298`/`00D002B0` occurrences, and both destinations resolve into `pc090oj_object_ram`. Removing them would
reintroduce raw VDP-range literals in dead code for no benefit; they emit nothing because the routine returns at its
first instruction.

## REMAINING PC090OJ CONSUMERS
Preserved by design (other families still use them): `pc090oj_object_ram`, the frontend object-RAM scanner
(`.Lnq_frontend_object_scan` loop), and the generic decoder (`.Lpc090oj_decode_record`) — still consumed by other
non-gameplay frontend producers (labels, status row `0x5A098`, credit/score retirement bookkeeping, and remaining
enemy/effect families not yet converted). Gameplay (scene 1) still emits native lanes only. No global deletion of the
scanner/decoder/object-RAM was performed (current dependency proof shows remaining consumers).

## BUILD / SMOKE
- **PROVEN.** `GATE_PASS`; numbered **Build 0286**.
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0286.bin`
- SHA-256: `db3e6957a09bed87da6d9c5120e15a69d3607fa5480f04abd07a589816bca4dd`
- Size: 1,591,960 bytes · Counter transition **285 → 286**.
- Canonical verification: **PASS** (`opcode_replace_count=228`, `total_genesis_bytes_covered=0x184A98`;
  `genesis_only_maincpu_ref_count=7` unchanged). Boot guard PASS (pre+post).
- Makefile-owned 30s Genesis-NTSC smoke: **PASS** (`Average speed: 951.46%`, no crash;
  `states/traces/rastan_direct_video_test_build_0286_mame_30s_20260816_210110`).
- Built with `RASTAN_GAMEPLAY_HUD_SPRITES=2` (0285 config preserved).
- Interactive validation: **DEFERRED TO TIGHE** (controlled interactive Genesis-NTSC MAME not drivable in-session;
  build's own smoke is the automated evidence).

## USER ACCEPTANCE ITEMS
- Ordinary gameplay remains intact (no frontend regression).
- Treasure/item presentation when the bonus/treasure sequence is naturally encountered: correct items, ordering,
  scroll-up, disappearance at the top, correct palette; **note** the dual-source (0x56226 / 0x562B0) case — the
  latch is last-source-wins; if the arcade interleaves the two at one dest, verify the shown set matches.
- GAME OVER presentation when naturally reached: the eight glyphs appear at the correct place, blink, and clear when
  play resumes; verify it does **not** appear spuriously in other frontend scenes (the live `a5@0x34==0 & bit5`
  gate is faithful to the arcade producer's own gate, but only Tighe's run confirms no cross-scene leak).
- No persistent/stale garbage frontend sprites.

## DOCUMENTATION UPDATES
KNOWN_FINDINGS.md, GRAPHICS_STATUS.md, OPEN_ISSUES.md updated (this build). CLOSED_ISSUES.md not marked closed for
the runtime-visible items pending Tighe's acceptance (mechanical retirement of the object-RAM output is recorded).
