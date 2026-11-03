# Andy — Build 0159: Life-Loss / Death-Controller Owner (Analysis Only, No Build)

## 1. Phase 0 / baseline
branch `rastan-direct-proposal`, HEAD `c0db8a2`, clean. Accepted Build 0158 ROM
`2bf5a06fd5d8ea759c4a9c1c82ce00c34257f338bcaee42d64de9093f17e23ab`, counter 158. **No source edit, no build.**
KNOWN_FINDINGS touched: KF-039 (A5 WRAM mapping). No CONFIRMED/STRONG contradiction. OPEN issue: OPEN-017.

## 2. Trace method
Same coin->start route on both images (Build 0158 cart / arcade `rastan`), logged on state-word change and on
writes to player mode `a5+0x10E8`, state `0xFF0002`, and floor/contact fields. Evidence:
`states/traces/build_0159_life_loss/`.

## 3. Genesis life-loss timeline (Build 0158)
2/2/6->2/2/7->2/2/4->2/2/5 (setup) -> **2/3/0 at F=533** (gameplay, Y drops 0x30->0x70, lands) ->
**mode 0x0003 -> 0x0008 at F=698** (rel 165, Y=0x0070, scrY=0x014B) -> **s2<-4 (2/3/0->2/4/0) at F=845** ->
2/4/1 -> 2/0/0 -> 2/0/1 -> 2/2/0..2/2/7 (setup again) -> 2/3/0 again. Repeats. Life fields
`a5+0x1394`=0x00FF and `a5+0x13AA`=0x0001 **never decrement**; `credits` field never changes.

## 4. Arcade comparison
**The arcade runs the identical cycle** under the same route: 2/3/0 at F=307 -> **2/4/0 at F=895** -> 2/4/1 ->
2/0/0 -> 2/2/x setup -> 2/3/0 again at F=1028. Arcade also reaches player mode=0x0008 at the 2/4/0 transition;
its life fields (0x00FF/0x0001) also never decrement. **Difference is duration:** arcade 2/3/0 lasts ~588
frames, Genesis ~313 frames -- the Genesis ends gameplay ~275 frames sooner.

## 5. First life-loss/death/continue-driving field
Player **mode `a5+0x10E8` = 0x0008** is the field that drives the gameplay-end: once set, the stage controller
writes `0xFF0002 <- 4` (2/3/0 -> 2/4/0) at PC `0x051B98` (arcade `0x051998`), starting the setup/respawn cycle.
The named "life" words (`0x1394`/`0x13AA`) and `credits` are NOT the burned counter in the traced window (they
are static) -- the cycling itself is the life/respawn loop, and it is arcade-faithful.

## 6. Writer PC
`mode <- 0x0008` is written at runtime **`0x05400C`** (arcade `0x053E0C`), inside an arcade_copy handler at
`0x054000` that also sets contact bit 9 (`a5+0x10CE`). Proven by write-tap (F=698). The `s2<-4` writer is
`0x051B98` (arcade `0x051998`), arcade_copy.

## 7. Source condition
The `0x054000` handler is reached by a **floor/collision map dispatch** at `0x053FA6`:
`d0 = *(a0); d0 &= 0x7F; if d0 == 8 -> bra 0x054000` (three `bra 0x54000` sites: `0x53E10`, `0x53EE2`,
`0x53FB4`). I.e. the mode=0x0008 (gameplay-end) branch fires when the **floor/map value under the player,
`*(a0) & 0x7F == 8`** (a specific tile/collision type). Both machines eventually see this value; on the Genesis
the player reads it ~275 frames earlier. The **source of the floor-map value `a0` (why it yields type 8 earlier
on Genesis) is NOT proven and lies in the floor/collision map** -- explicitly out of scope for this task.

## 8. Relationship to terminal mode 0x0008
The prior analysis' "terminal mode 0x0008" IS this event: the floor-type-8 dispatch writes mode=0x0008, which
the stage controller then converts to the 2/4/0 transition. Arcade reaches the same mode=0x0008 but ~275 frames
later.

## 9. Relationship to BG vertical scroll 0x00FF409A
Context only: `staged_scroll_y_bg` animates 0x01EC -> ~0x0147 during 2/3/0 and is at 0x014B when mode=0x0008 is
written (F=698). The floor-map pointer `a0` is plausibly indexed by camera/scroll state, so the extra Genesis
vertical scroll is a candidate upstream cause of the early floor-type-8 read -- **unproven, and scroll is
deferred**.

## 10. State-causality answers
1. First field indicating progression: player **mode `a5+0x10E8` = 0x0008** (then `0xFF0002 <- 4`).
2. Writer PC: **`0x05400C`** (arcade `0x053E0C`); stage-advance `0x051B98`.
3. Cause of the write: **floor/collision map value `*(a0) & 0x7F == 8`** (dispatch at `0x053FA6`).
4. Life-loss triggered by: a **floor/collision-map tile-type condition** (type 8) -- NOT enemy hit, NOT a plain
   timer, NOT offscreen-camera directly, NOT missing-sprite. It is the same handler the arcade uses; the Genesis
   just reaches the type-8 floor value earlier.
5. BG vertical scroll relative to trigger: the extra scroll animates **before** the mode=0x0008 write (present
   from ~rel 30, mode=8 at rel 165) and is a candidate index into the floor map -- **unproven**.
6. Arcade same path: **YES** -- identical handler and cycle, only ~275 frames later.
7. Build 0159 boundary proven: **NO** (source of the floor-type-8 value is collision/floor-map + scroll, out of
   scope; only the writer + immediate condition are proven).

## 11. Readiness classification: **C** (with a strong **D** aspect)
**C** -- the writer PC (`0x05400C`) and the immediate condition (floor/collision map `*(a0)&0x7F==8`) are
proven, but the **source condition** (why the Genesis floor map yields type 8 ~275 frames earlier) is **not
proven** and lies in the floor/collision map + camera-scroll, which are out of scope. **D aspect:** the
2/3/0 -> 2/4/0 -> setup -> 2/3/0 cycle and the mode=0x0008 handler are **arcade-faithful** (the arcade runs the
identical cycle; the named life words never decrement) -- so this is **not** a Genesis-specific life-counter
defect; it is an earlier-firing floor/collision condition. **Not ready for a bounded Build 0159 in the
life-loss domain.**

## 12. Exact next implementation boundary if ready
Not ready. The actionable next step leaves this task's scope: prove the source of the floor-map pointer `a0` at
`0x053FA6`/`0x054000` and why `*(a0)&0x7F==8` fires ~275 frames early on Genesis -- i.e. the floor/collision
map population and/or the camera/scroll index feeding it (both deferred: collision + broad scroll). Do NOT patch
the arcade_copy handler `0x05400C` (it is faithful).

## 13. Open/Closed Issues Impact
OPEN-017 advanced: the "burns lives / reaches continue" behavior is root-caused to the floor/collision-map
type-8 dispatch (writer `0x05400C`, condition `*(a0)&0x7F==8`) firing ~275 frames early on Genesis; the cycle
itself is arcade-faithful (life words static). Source lies in floor/collision map + camera scroll (deferred).
No new issue, none closed.

## 14. KNOWN_FINDINGS impact
Option A -- no new finding indexed (runtime timeline + one proven writer/condition; the durable owner is the
floor-map source, which is unproven).

## 15. Architecture compliance
CONFIRMED. Analysis only -- no source, build, or spec/tool edits; runtime evidence via MAME taps and static
disasm; arcade program remains the reference. No rendering/sprite/collision/scroll/continue/game-over/D00298/
Exodus/audio changes.
