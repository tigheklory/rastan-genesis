# Cody - Frontend GAME OVER / High-Score Semantic Model

**Task:** static/Ghidra semantic analysis only  
**Tree:** current forward tree containing Build 0286 changes  
**Counter:** 286  
**Build produced:** NO  
**Implementation changes:** NONE

Address labels in this report are explicit. `arcade_pc` identifies original arcade
code. `runtime_genesis_pc` identifies current translated-ROM code. All correlations
were derived from `build/rastan-direct/address_map.json`; no arithmetic relocation was
used as mapping authority.

## BUILD0286 USER EVIDENCE

**PROVEN (authoritative user observation):** Build 0286 boots and ordinary gameplay
works substantially into Stage 1. Its new direct-native eight-glyph `GAME OVER` row
appears over the HIGH SCORE TABLE. The following frontend transition reaches the
Genesis exception handler.

**PROVEN:** This falsifies the Build 0286 ownership test
`a5+0x34 == 0 && bit5(a5+0x200) == 0`. Those two fields can describe a visible
`0x05A502` row, but they do not identify one unique frontend screen.

**DISPROVEN:** The large row on the high-score screen is not evidence that the
high-score state itself is GAME OVER. It is an ownership-gate defect in the current
native emitter.

## FRONTEND GAME-FLOW STATE MACHINE

The original arcade's primary dispatcher at `arcade_pc 0x0003A008`
(`runtime_genesis_pc 0x0003A208`) dispatches on `word(a5+0x00)`:

| `a5+0x00` | Original owner | Relevant dispatcher |
|---:|---|---|
| 0 | title/history/high-score attract frontend | `arcade_pc 0x0003A9FE` / `runtime_genesis_pc 0x0003ABFE` |
| 1 | credit/start/player-selection frontend | `arcade_pc 0x0003A8AC` / current JSON-mapped arcade-copy path |
| 2 | gameplay/session umbrella, including terminal flow | `arcade_pc 0x0003A15A` / `runtime_genesis_pc 0x0003A35A` |
| 3 | separate special branch | `arcade_pc 0x0003AB6E` |

Within outer state 2, `arcade_pc 0x0003A15A` dispatches on `word(a5+0x02)`:

| `a5+0x02` | Meaning |
|---:|---|
| 0 | gameplay-area reset/clear |
| 1 | reset sequencing placeholder |
| 2 | round/item/start setup |
| 3 | active gameplay or attract-demo gameplay |
| 4 | terminal death / continue / GAME OVER flow |

The terminal dispatcher at `arcade_pc 0x0003A196`
(`runtime_genesis_pc 0x0003A396`) dispatches `word(a5+0x04)` as follows:

| `a5+0x04` | Semantic state | Entry/exit behavior |
|---:|---|---|
| 0 | terminal-flow initialization | `arcade_pc 0x03A1C4` initializes terminal state and writes 1. |
| 1 | terminal wait / cleanup selection | `0x03A200` advances to 2; human sessions retain terminal processing. |
| 2 | cleanup / qualification branch | `0x03A2D8`; no-human sessions reset `(a5+0,+2,+4)` to zero, human sessions advance to 9. |
| 9 | high-score qualification/name-entry submachine | Its completion writes 3. |
| 3 | CONTINUE setup decision | `0x03A304`; eligible sessions create the continue display and write 8, otherwise write 4. |
| 8 | CONTINUE countdown/input | `0x03A478`; accepted credit resets `(+2,+4)` to restart, expiry writes 4. Actual BCD credits are at `a5+0x12`. |
| 4 | per-player post-continue GAME OVER setup | `0x03A39A`; tracks completed players in `a5+0x3A`; writes 5 once both are complete. |
| 5 | shared terminal GAME OVER setup | `0x03A420`; emits text IDs `0xBA` and `8`, sets timer 160, then writes 6. |
| 6 | shared terminal GAME OVER dwell/exit | `0x03A450`; chooses outer state 0 when credits are zero or state 1 when credits remain, clears the human-session latch, then resets `(+2,+4)`. |
| 7 | player-alternation return | Returns to the terminal outer sequence. |

**PROVEN:** Terminal phase 4 is entered by original writers including
`arcade_pc 0x051992`, `0x0527B4`, and `0x0577F6`, which write `a5+0x02 = 4`
and reset `a5+0x04` for the terminal dispatcher.

**PROVEN:** The original human terminal GAME OVER screen is not owned by
`arcade_pc 0x05A502`. It is set up at `(a5+0,a5+2,a5+4) = (2,4,5)` and is
displayed/dwelled after that setup changes the tuple to `(2,4,6)`. Its original
screen producer is the terminal text path at `arcade_pc 0x03A420`.

The attract/high-score frontend under outer state 0 uses `a5+0x02` and
`a5+0x04` separately:

| State tuple | Screen/action | Exit |
|---|---|---|
| `(0,0,0)` | frontend clear/init | writes `a5+4=1` |
| `(0,0,1)` | title setup | writes `(a5+2,a5+4)=(1,0)`, timer 208 |
| `(0,1,0)` | second frontend clear/init | writes `a5+4=1` |
| `(0,1,1)` | history/BEST-5 setup | writes `a5+4=2`, timer 160 |
| `(0,1,2)` | HIGH SCORE TABLE setup | `arcade_pc 0x03AB00`; writes `(a5+0,a5+2,a5+4)=(2,0,0)` at `0x03AB48` |
| `(0,2,*)` | item-page frontend | calls `0x05A474`, then returns to `(0,0,0)` after its dwell |

## a5+0x34 SEMANTIC IDENTITY

**PROVEN:** `word(a5+0x34)` is an **active human game/session latch**. It is not
the credit count and is not a GAME OVER state ID.

- Paid/start selection writes it to 1 at `arcade_pc 0x0003A984`.
- Terminal exit clears it at `arcade_pc 0x0003A460`.
- Actual BCD credits are independently stored at `a5+0x12`, incremented by the
  coin paths and tested/decremented by CONTINUE state 8.
- Original active-game code uses `a5+0x34 == 0` to select no-human/demo behavior.

**DISPROVEN:** `a5+0x34 == 0` does not mean "terminal GAME OVER active." During
a human terminal GAME OVER, the latch remains nonzero through setup/dwell and is
cleared only by terminal exit state 6.

For the large row produced by `arcade_pc 0x05A502`, `a5+0x34` is zero because
the caller invokes that producer only in no-human attract/demo gameplay. This is
distinct from the human terminal GAME OVER screen.

## a5+0x200 SEMANTIC IDENTITY

**PROVEN:** `word(a5+0x200)` is the first word of the gameplay work block and is
used as a gameplay frame/phase tick.

- Gameplay reset clears it at `arcade_pc 0x0003A582` and `0x0003A696`.
- Active gameplay nested state 0 increments it once per update at
  `arcade_pc 0x0003A7B0`.
- `arcade_pc 0x05A502` uses bit 5 as its 32-frame visible/hidden phase.

**PROVEN:** The high-score setup path does not increment or otherwise own this
counter. While the table is displayed, the value merely remains from prior state
until the high-score exit enters gameplay reset and clears the gameplay block at
`arcade_pc 0x03A582`. Therefore high score can happen to observe bit 5 clear; it
is not running a high-score-specific blink counter.

## WHY HIGH SCORE PASSES THE BUILD0286 GAME-OVER GATE

**PROVEN:** Terminal exit state 6 clears `a5+0x34` at `arcade_pc 0x03A460`.
No title/history/high-score state sets it again; only a later paid start at
`arcade_pc 0x03A984` does so. Therefore `a5+0x34 == 0` is expected during the
HIGH SCORE TABLE.

**PROVEN:** The current `.Lnq_gameover_emit` is invoked from the broad
`.Lnq_frontend_object_scan` path for non-gameplay scenes. It tests only
`Genesis-WRAM 0x00FF0034` and bit 5 of `Genesis-WRAM 0x00FF0200`. It does not
test the original outer/sub/nested state tuple. When the retained gameplay tick
happens to have bit 5 clear, high score satisfies both tests and receives the
eight-glyph row.

**DISPROVEN:** A Genesis scene ID plus these two fields is not an adequate
substitute for original game-flow ownership.

## EXACT GAME-OVER OWNERSHIP STATE

There are two distinct contracts which must not be conflated:

1. **PROVEN terminal human GAME OVER ownership:** setup tuple `(2,4,5)`, followed
   immediately by visible/dwell tuple `(2,4,6)`. This path is owned by
   `arcade_pc 0x03A420..0x03A470` and the terminal text producer.
2. **PROVEN `0x05A502` large-row call ownership:** active no-human gameplay only.
   `arcade_pc 0x03A79C` is reached under `(a5+0,a5+2)=(2,3)`; nested state 0
   calls the gameplay chain at `0x03A7B4`, nested state 1 calls it at `0x03A836`,
   and `arcade_pc 0x051046` calls `0x05A502` only when `a5+0x34 == 0`.

Thus the retained semantic state immediately above the retired producer is:

```text
a5+0x00 == 2
a5+0x02 == 3
a5+0x04 == 0 or 1
a5+0x34 == 0
```

The visibility condition remains `bit5(a5+0x200) == 0`.

## EXACT DIRECT-NATIVE GAME-OVER GATE

For a faithful direct-native replacement of **original producer
`arcade_pc 0x05A502`**, the gate is:

```text
IF word(a5+0x00) == 2
AND word(a5+0x02) == 3
AND (word(a5+0x04) == 0 OR word(a5+0x04) == 1)
AND word(a5+0x34) == 0
AND (word(a5+0x200) & 0x0020) == 0
THEN emit the eight native GAME OVER pieces
ELSE emit nothing
```

This gate excludes CONTINUE `(2,4,3/8)`, terminal human GAME OVER
`(2,4,5/6)`, HIGH SCORE `(0,1,2)`, title/history outer state 0, and paid-start
outer state 1. It retains the original no-human active-game call context.

**PROVEN:** The missing ownership information is available in retained original
state immediately above the call (`arcade_pc 0x051046`) and in its active-game
dispatcher. PC090OJ persistence is not required.

**Implementation distinction:** If a future task separately converts the human
terminal GAME OVER text screen, it must cut at `arcade_pc 0x03A420` and use the
terminal `(2,4,5/6)` contract. It must not repurpose `0x05A502` as that screen.

## HIGH-SCORE EXIT STATE

**PROVEN:** HIGH SCORE setup is entered at `(0,1,2)`. At
`arcade_pc 0x0003AB48` (`runtime_genesis_pc 0x0003AD48`) it writes:

```text
a5+0x00 = 2
a5+0x02 = 0
a5+0x04 = 0
```

The next main dispatch therefore enters gameplay/session reset, not another
high-score substate:

1. `arcade_pc 0x03A15A` / `runtime_genesis_pc 0x03A35A` selects phase 0.
2. `arcade_pc 0x03A566` / `runtime_genesis_pc 0x03A766` selects nested reset 0.
3. `arcade_pc 0x03A582` / `runtime_genesis_pc 0x03A782` clears the gameplay
   block beginning at `a5+0x200`, calls the plane/scroll clear sequence, and
   advances nested reset to 1.
4. `arcade_pc 0x03A5A4` / `runtime_genesis_pc 0x03A7A4` clears PC090OJ state and
   advances nested reset to 2.
5. `arcade_pc 0x03A5AA` / `runtime_genesis_pc 0x03A7AA` writes
   `a5+0x02=2`, `a5+0x04=0`.
6. `arcade_pc 0x03A5BC` / `runtime_genesis_pc 0x03A7BC` begins the normal
   round/item/start sequence. Because `a5+0x34` remains zero, this is the
   no-human/attract-gameplay route. Its eventual terminal path returns to outer
   frontend state 0; a credit can instead select the paid-start frontend.

## CURRENT GENESIS POST-HIGHSCORE DIVERGENCE

**PROVEN:** The high-score exit state writes at `runtime_genesis_pc 0x03AD48`
and the reset dispatch/state writes listed above remain exact `arcade_copy`
segments in the current JSON map. The high-score literal palette write at
`arcade_pc 0x03AB00` is already replaced at `runtime_genesis_pc 0x03AD00`, but
that replacement occurs during high-score setup and its helper returns to the
intact setup tail.

**PROVEN:** The first translated boundary reached **after** the `0x03AB48` exit
is the shared long-fill routine:

- original `arcade_pc 0x03AE5A` maps exactly to copied
  `runtime_genesis_pc 0x03B05A`;
- its plane clear reaches original `arcade_pc 0x03AD44` at current
  `runtime_genesis_pc 0x03AF44`;
- that site is an `address_map.json` `patched_site` calling
  `genesistan_hook_3ad44_dispatch` at Genesis-only
  `runtime_genesis_pc 0x00072CC8`.

The calls supply `HW_ADDRESS 0x00C00100` and `0x00C08100`. Both satisfy the
helper's proven PC080SN range `[0x00C00000,0x00C10000)`, so neither reaches its
out-of-range audit halt. The following reset-state call supplies PC090OJ ranges
`0x00D00000` and `0x00D00170`, both inside the helper's accepted object interval
`[0x00D00000,0x00D00800)`. The state jump tables and branch targets in this
immediate sequence remain copied and in range.

**HYPOTHESIS:** The exception occurs in or after one of the translated hardware
helpers reached by this reset/start sequence. Static reachability alone does not
identify which dynamic helper invocation or later instruction faults.

**DISPROVEN:** The current evidence does not prove that the new GAME OVER
emitter itself causes the exception. It also does not prove an invalid
high-score exit state or an invalid immediate jump-table target.

**Exact unresolved boundary:** the exception vector and first stacked
`runtime_genesis_pc` for the post-high-score failure are not preserved in the
provided static evidence. Consequently no honest `arcade_pc` fault attribution
can yet be made.

## EXCEPTION-HANDLER ADDRESS ACCOUNTING

**PROVEN:** `apps/rastan-direct/src/crash_handler.s` stores and displays the
68000 exception frame without converting it to arcade address space:

- standard frames: SR from `0(sp)`, stacked PC from `2(sp)`;
- bus/address-error frames: access word from `0(sp)`, fault address from
  `2(sp)`, SR from `8(sp)`, stacked PC from `10(sp)`;
- only vectors 2/3 display `CRASH_FAULT_ADDRESS` separately.

The displayed `FAULT PC` is therefore a stacked **runtime Genesis PC**, not an
`arcade_pc`, and it must be classified/mapped through `address_map.json`. It is
not adjusted by a fixed relocation. Depending on vector semantics it may also
be a stacked continuation/resume context rather than a complete statement of
the data access which failed.

The diagnostic register presentation has an additional bounded bookkeeping
defect: `_crash_common` uses D0-D5 while parsing the frame and only then stores
the displayed D0-D5 values, so those displayed registers are handler-clobbered,
not the original fault-time values. The footer also remains the stale literal
`BUILD 0038`.

**PROVEN:** The screen is not trustworthy as an arcade-address attribution or
as a complete fault-time register record. The mechanically captured stacked PC
can still be useful if the vector and raw crash record are preserved.

One future narrow observation is sufficient: on the first post-high-score
exception, preserve one crash-record snapshot containing
`CRASH_EXCEPTION_TYPE` (`Genesis-WRAM 0x00FF6802`), `CRASH_STACKED_PC`
(`0x00FF6806`), `CRASH_FAULT_ADDRESS` (`0x00FF6854`, relevant for vector 2/3),
and the contemporaneous state tuple at `Genesis-WRAM 0x00FF0000/+2/+4`.

## BUILD0286 ITEM-CONVERSION INDEPENDENCE

**PROVEN:** The Build 0286 transient-item family is independent of the GAME OVER
ownership defect:

- `arcade_pc 0x056114` -> exact current patched site
  `runtime_genesis_pc 0x0561EE`: latches the caller-selected ROM tuple stream,
  marks `transient_items_active`, and resets its scroll.
- `arcade_pc 0x05607C` -> `runtime_genesis_pc 0x056156`: advances the independent
  item scroll at the original cadence and preserves the original
  `a5+0x10AE/a5+0x10B0` side effects.
- `arcade_pc 0x056440` -> `runtime_genesis_pc 0x05651A`: ends the transient
  family by clearing its active flag.

These helpers neither read nor write `a5+0x00`, `a5+0x02`, `a5+0x04`,
`a5+0x34`, or `a5+0x200`. The direct emitter consumes only the independent
`transient_items_*` state and the retained tuple stream. The item page is a
separate frontend branch, and the item conversion does not select the
high-score exit dispatcher or terminal GAME OVER states.

**DISPROVEN:** The GAME OVER overlay defect is not a reason to roll back the
transient-item conversion.

## IMPLEMENTATION CONTRACT FOR ANDY

1. Remove `.Lnq_gameover_emit` from the broad non-gameplay
   `.Lnq_frontend_object_scan` ownership boundary.
2. Keep original `arcade_pc 0x05A502` retired; do not restore PC090OJ object-RAM
   persistence.
3. Invoke the direct-native eight-piece emitter exactly once from the native
   gameplay finalization path only when retained original state is
   `(a5+0,a5+2)=(2,3)`, `a5+4` is 0 or 1, `a5+0x34` is 0, and bit 5 of
   `a5+0x200` is clear.
4. Do not use a Genesis-only scene ID as the ownership proof.
5. Do not alter or roll back the independent transient-item helpers.
6. Do not patch the post-high-score exception until the single crash-record
   observation above identifies the exact current faulting path. Then map any
   copied/patched PC through `address_map.json`; label Genesis-only helper PCs
   as such rather than inventing an arcade counterpart.
7. If the human terminal GAME OVER screen is later converted, use the separate
   semantic cut at `arcade_pc 0x03A420` and terminal states `(2,4,5/6)`.

**PROVEN architecture compliance:** This contract retains original arcade
semantic state, emits native SAT pieces directly, and does not require a
PC090OJ mirror, scanner, or persistent chip-shaped lifecycle.
