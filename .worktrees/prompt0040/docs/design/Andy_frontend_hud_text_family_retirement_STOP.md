# Frontend HUD/Text PC090OJ Family Retirement — STOP (0x3B802 does not own its digit positions)

**Agent:** Andy · No build. No source/spec/object/ROM changed. Counter 265. Phase 0: EXTENDING (OPEN-024/OPEN-006).

## The concrete contradiction (not "shared across screens")
The task names the family as **0x3B802 (score/HUD digits, 10 callers)** + **0x5A098 (status, 1 caller)**. Code
proof from the current tree:
- **0x3B802 writes only Y+code**: `.Lhook_3b802_emit` writes record `+2/+3` (Y) and `+4` (code) via
  `.Lpc090oj_mirror_write_*`. It writes **no `+6` (X) and no `+0` (attr)** (verified: no `adda.w #6/#0,%a1`, no
  `(%a1)` store in the hook). Its 10-entry record table carries only {count, Y, dest-record, BCD-source} — **no
  X**.
- The score records' **X and attr are set by separate arcade positioning code**, not by 0x3B802 and not by
  `workram_block_sprites` (which writes the *player* blocks: records 0–21 from `a5+0x11B2`/`a5+0x170`, not the
  score records 27/33/42).

Therefore **0x3B802 does not own the position/attribute of the digits it produces** — it only refreshes the
dynamic Y+code of records that another producer positions in PC090OJ object RAM.

**Why this prevents a producer-owned, record-free conversion of the family:** a native `0x3B802` emitter would
have to supply each digit's X/attr, but the producer never computes them. The only sources are (a) the arcade
positioning code / records the task forbids depending on, or (b) per-frontend-state hard-coded layouts — which
0x3B802 does not own and which the task explicitly forbids ("no per-screen final sprite tables", "one
production implementation for this semantic family"). The Build 0265 title works precisely because it supplies
its **own** hard-coded title layout; that cannot be generalized to the other 9 callers from 0x3B802's inputs,
because those inputs contain no positions. Replacing the *entire* named family without PC090OJ positioning state
is thus impossible in this unit. This is the task's sanctioned STOP: "a concrete semantic contradiction that
prevents replacing this entire producer family without PC090OJ state."

## What IS separable (path forward, no guessing required)
- **0x5A098 is self-contained**: it computes X (`d4` step 0x10), Y (`0xE8`), code (`0x3CA+d0`), attr — full
  sprite params — and emits via `.Lpc090oj_emit_slot`. It can be retired as **its own** producer unit (redirect
  its emit to a native lane the relevant finalizer drains). It should be a separate task from 0x3B802.
- **0x3B802** can only be retired record-free by first converting the **arcade score-record positioning
  producer** (which owns X/attr) — i.e., that positioning producer is the real retirement prerequisite, and it
  is out of this task's declared scope (preserve list adjacent). The title 0x3B802 use is already native (0265).

## Recommended re-scope (either is a clean build)
1. Retire **0x5A098** alone (self-contained, 1 caller) — clean producer-owned native conversion; or
2. First identify + convert the **score-record positioning producer** so 0x3B802's digits have a native
   position owner, then retire 0x3B802 across all callers.

Bundling 0x3B802 with 0x5A098 as one convertible unit is the part that is contradicted, because only 0x5A098
owns its output.
