# Andy — Build 0158: Stage 1 Command-Source Rebase (0x05102E / 0x0010C016)

## 1. Phase 0 / baseline
branch `rastan-direct-proposal`, HEAD `b900387` (Cody 0158 docs committed; accepted Build 0157 ROM SHA
`725c36a2...` intact), counter 157, clean. Task class: **EXTENDING** (KF-036/KF-039 raw work-RAM literal rebase).
KNOWN_FINDINGS touched: KF-039 (arcade WRAM base `0x0010C000` -> Genesis `0x00FF0000`), KF-036 (item-page
descriptor WRAM rebase -- same rebase class). No CONFIRMED/STRONG contradiction. OPEN issues: OPEN-017.

## 2. State-causality proof -- classification **A**
`0x05122E: move.w 0x0010C016,%d0` then `0x051234: move.w %d0,a5@0x137A` (a5=0x00FF0000 => dest 0x00FF137A).
The absolute literal `0x0010C016` is not an instruction-operand shape the postpatch relocates, so it is copied
verbatim; on Genesis that literal is a **ROM** address.
- **Arcade:** at PC `0x051038`, `a5@0x137A <- 0x00FF`, and `WRAM[0x10C016] = 0x00FF`.
- **Genesis 0157 (before):** at PC `0x051238`, `a5@0x137A <- 0x5553`, `ROM[0x10C016] = 0x5553`, but
  **`WRAM[0x00FF0016] = 0x00FF`** (correct, matches arcade).
Classification **A**: the correct value exists at mapped WRAM `0x00FF0016`, but the copied reader loads the raw
ROM literal `0x0010C016`.

## 3. Source value proof: arcade `0x0010C016`
`WRAM[0x10C016] = 0x00FF` at command time (`states/traces/build_0158_command_source/arc_cmd.txt`) -- the correct
Stage 1 command source; the arcade store writes it verbatim to `a5+0x137A`.

## 4. Source value proof: Genesis `0x00FF0016`
`WRAM[0x00FF0016] = 0x00FF` at the command-copy moment (`gen_cmd.txt`, F=535+). Writer identified: runtime
`0x03A99A` (arcade `0x03A79A`) writes `0x00FF` at command time (`gen_writer.txt`; earlier `0x03A7B0` writes
`0xFFFF` at F=194). The value is correctly present in mapped work RAM.

## 5. Bad raw Genesis value proof: `0x0010C016`
Genesis `ROM[0x10C016] = 0x5553` (static ROM read + runtime), exactly the bad value stored to `a5@0x137A`
before the fix. (`ROM[0x10C014..0x10C01A] = 9355 5553 9553 9953`.)

## 6. Exact change
Byte-neutral `opcode_replace` at arcade `0x05102E`: `30390010C016 -> 303900FF0016`
(`move.w 0x0010C016,%d0 -> move.w 0x00FF0016,%d0`; opcode `0x3039` preserved). Only the reader's absolute
operand is rebased via KF-039 (`0x0010C000 -> 0x00FF0000`). No NOP, no destination patch, no forced value, no
seed, no fallback, no ROM-wide rebase. Original bytes validated against arcade maincpu `0x5102E`.

## 7. Command before/after
| | reader operand | a5@0x137A value |
|---|---|---|
| Build 0157 | 0x0010C016 (ROM=0x5553) | **0x5553** |
| Build 0158 | 0x00FF0016 (WRAM=0x00FF) | **0x00FF** (matches arcade) |
Disasm after: `0x5122E: move.w 0xFF0016,%d0`. Runtime: `a5@0x137A <- 0x00FF` at F=535+ (bad 0x5553 gone).

## 8. Drop/landing before/after
Out of scope to re-derive (Cody: Genesis lands at Y=0x0070; falling itself is not the bug). This build corrects
the internal command source `a5@0x137A` only; Y/landing/collision/floor untouched.

## 9. Visible result
No visible change at the sampled gameplay frame: Stage 1 FG/BG terrain renders, but no persistent player sprite
-- Rastan still dies almost instantly (deferred control-flow/fall; the active sprite window precedes the
plane-paint window, per Build 0157). **Build 0158 is an internal state fix, not a visible gameplay fix.**

## 10. Regression results
`a5@0x137A=0x00FF`; frontend sprites intact (title `represented=15`); Build 0157 sprites intact
(`max_represented=11`); Build 0155 FG intact (`staged_fg=2020`); Build 0154 BG intact (`staged_bg=2048`);
Build 0156 C08C66 route intact (`0x3D24C=jsr 0x708C8`); Build 0152 C08C62 route intact (`0x3A92A=jsr 0x70894`).
GATE_PASS; boot guard PASS; trace clean; address-map `gaps=[]`, `overlaps=[]`, covered `0x182070`,
`opcode_replace=136`; two clean MAME boots deterministic. Byte-neutral (size 1,581,168 = Build 0157).

## 11. Open/Closed Issues Impact
OPEN-017 advanced (Stage 1 command source rebased; internal command state now tracks arcade). No new issue,
none closed. Deferred: player death/fall/collision, Y/landing, scroll, camera, continue/game-over, D00298,
Exodus, audio.

## 12. KNOWN_FINDINGS impact
Option A -- no new finding indexed. Single-site instance of the already-indexed KF-036/KF-039 raw work-RAM
literal rebase class (documented here + in the spec note); no new durable rule.

## 13. Architecture compliance
CONFIRMED. Byte-neutral operand rebase through the declarative spec `opcode_replace` pipeline (original-bytes
validated); arcade program stays the source of truth; no NOP/RTS, no destination patch, no forced value/seed,
no fallback logic, no second renderer/commit path, no unrelated systems. Builds 0152/0154/0155/0156/0157
untouched.
