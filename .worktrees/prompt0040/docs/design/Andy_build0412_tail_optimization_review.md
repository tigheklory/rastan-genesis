# Build 0412 — Tail-Optimization Static Review (Andy)

**Date:** 2026-10-10 · **Type:** STATIC REVIEW ONLY. No production source edited, no ROM built, no
Cody working-tree file modified. No Phase D/E, no PC080SN changes. Baseline: Build 0412 (accepted
perf baseline: worker avg 120,467.68 / p95 223,752; IRQ avg 125,442.49 / p95 232,627; 29.0% IRQ
>128,009; 116 frames without a completed worker; 0.9033 workers/rendered frame).

Reviewed against Cody's working tree as it exists now (uncommitted). Independent of Cody's
conclusions.

---

## 1. Register-contract review (Cody's in-scope probe optimization)

**The change:** `.Lnative_emit_actor_common` (the common actor wrapper, `pc090oj_hooks.s:898`) now
preserves only `%d5/%a1` (`movem.l %d5/%a1,-(%sp)` at :909, restored :922) around the two generated
probes `.Lnative_generic_frame_try` (:948) and `.Lnative_universal_general_try` (:1076), instead of
the former nested full `d0-d7/a0-a6` save in the wrapper *and* each probe.

**Call graph (proven from source):**
- `.Lnative_emit_actor_common` — 7 callers, all inside `native_stage_dispatch_41dae` (:708,:718,:802,
  :822,:844) and `native_stage_dispatch_45dfa` (:854,:864).
- `.Lnative_generic_frame_try` — **exactly one** caller: `bsr` at :914 (inside the wrapper).
- `.Lnative_universal_general_try` — **exactly one** caller: `bsr` at :917 (inside the wrapper).
- Both probes call `native_sprite_fast_context` (:631) and `native_sprite_emit_fast` (:673); the
  generic probe also calls `.Lnative_mapping_branch_is_normal` (:1212).

**The real correctness invariant:** the stage dispatchers save the full `d0-d7/a0-a6` once at entry
(:701) and restore at exit, so the retained arcade caller's contract is intact regardless. Inside the
dispatcher **loop**, the only registers that must survive each `bsr .Lnative_emit_actor_common` are:
- **D5** — the `dbra` loop counter → saved/restored by the wrapper. ✅
- **A1** — loaded once before the loop; "legacy lane cursor used by skip paths" → saved/restored by
  the wrapper (conservative; in the 41dae/45dfa enemy bands A1 is largely a dead token, but a skip
  path can read it, so preserving it is required/safe). ✅
- **A4** — the actor pointer the caller advances with `adda.w #64,%a4` → **NOT saved by the wrapper**;
  it must be preserved by the probe chain *not writing it*.
- **A5** — the arcade WRAM frame base → **NOT saved**; must likewise never be written by the probes.

**Verified by reading every routine on the path:** neither `.Lnative_generic_frame_try` (:948-1067)
nor `.Lnative_universal_general_try` (:1076-1203) ever writes A4 or A5 — both only read `(%a4)` /
`(%a5)`. `native_sprite_fast_context` (:631) sets A2/A3/A6 and D0 only. `native_sprite_emit_fast`
(:673) clobbers D0/A1 and uses A2/A3/A6 as inputs — never touches A4/A5. `.Lnative_mapping_branch_is_normal`
(:1212) sets D0 only. All other clobbered registers (A0/A2/A3/A6, D0-D4/D6/D7) are dead between
dispatcher loop iterations (D2 is reloaded each iteration) and are restored by the dispatcher's outer
`movem` regardless.

**Stack balance:** the wrapper's two early exits (`beq .Lnea_ret` at :900/:902) occur *before* the
push and jump to `.Lnea_ret` (:930) which is *after* the pop (:922). Every post-save path flows
through the single `.Lnea_restore` pop. Balanced on all paths. The only `%sp` accesses in the whole
dispatch/probe region are the symmetric `movem` save/restores — no `NN(%sp)` offset read assumes the
old 60-byte frame.

**CCR:** the caller uses `dbra`/`adda` after the call (no reliance on CCR from inside the wrapper);
the wrapper's internal `tst.b %d0` tests the probe return it just set. No condition-code dependency
crosses the boundary.

**Verdict: SAFE.** The optimization is semantically correct for the current source. Its safety rests
entirely on the generated probe chain never writing A4/A5 — which is true now but is a *generated*
property the verifier must lock (see §2).

---

## 2. Verifier review — `tools/translation/verify_pc090oj_direct_dispatch.py`

**What it proves today (`verify_fast_enqueue`, lines 88-117):**
- Single-caller: `source.count("bsr     .Lnative_generic_frame_try")==1` and same for universal. ✅
- Wrapper preserves D5/A1: asserts both `movem.l %d5/%a1,-(%sp)` and the matching pop exist. ✅
- Stage dispatchers keep full `d0-d7/a0-a6` save+restore (both 41dae and 45dfa blocks). ✅
- No nested full save returned — **but only checks the `.Lnative_generic_frame_try` block** (:108-111).

**Gaps (false-negative risks — verifier can PASS an unsafe future regeneration):**

1. **It never proves the probes don't write A4/A5** — the actual correctness invariant. If a
   regenerated probe (or a change to `native_sprite_fast_context`/`native_sprite_emit_fast`) used A4
   or A5 as scratch, the verifier would PASS and the ROM would corrupt the actor loop. **Add:** assert
   no A4/A5 *destination* write in the generic probe, universal probe, `native_sprite_fast_context`,
   and `native_sprite_emit_fast` blocks — reject `,\s*%a4` / `,\s*%a5` as a destination, any `movea`/
   `lea ...,%a4|%a5`, and any `movem ... -(%sp)` list containing `a4`/`a5` that is not symmetrically
   restored before the block's `rts`.
2. **The "no nested full save" check covers only the generic probe, not the universal probe.** Extend
   the check to the `.Lnative_universal_general_try` block (and to `native_sprite_fast_context` /
   `native_sprite_emit_fast`).
3. **It doesn't prove the early-exit balance.** Assert both `beq.* .Lnea_ret` appear textually before
   `movem.l %d5/%a1,-(%sp)`, and `.Lnea_ret:` appears after `movem.l (%sp)+,%d5/%a1`, so a future edit
   can't push-then-early-exit past the pop.
4. **Single-caller is matched on exact `bsr` spelling/spacing.** A second call site via `jsr`,
   `bsr.w`, or different whitespace would be missed. **Add:** count all references to each probe label
   (any mnemonic) and assert they occur only inside the wrapper block.

**False-positive (over-strict) note:** the exact-string matches (`movem` spacing, `bsr` spacing) make
any benign whitespace reformat fail the build. That is fail-safe/conservative and acceptable, but it
means the verifier guards *formatting*, not *semantics* — which is exactly why gaps 1–4 matter: the
thing it should lock (A4/A5 non-clobber) is the thing it does not check.

---

## 3. Non-PC080SN tail boundary

Heavy-frame chain (arcade PCs): `0x51210` player/gameplay update → `0x055650` 4-direction scroll
dispatch → `0x055696 / 0x05572E / 0x0557BA / 0x055854` (per-direction; each calls `0x0406A4` and
`0x055948`) → `0x0556CE` scroll-step conditional + `0x055948` → `0x055968`→`0x0559B2` / `0x055990`→
`0x055A14` → **`0x70418 / 0x70552`** (Genesis-native PC080SN strip/map commit).

| Address | Responsibility |
|---|---|
| `0x51210` | player/gameplay main-update call (one of the 7 from the `0x4210E` dispatcher); its dominant internal cost is the scroll chain below |
| `0x0556CE` | scroll-step conditional inside the directional scroll routine `FUN_00055696`; gates the strip/map advance |
| `0x0559C8` | inside the `0x055948→0x0559B2/0x055A14` strip-build subtree feeding the native commit |
| `0x0406A4` | **actor-coordinate scroll compensation** — adds the camera scroll delta to every active actor's coordinates across three A5 arrays; **NOT** strip/map |
| `0x70418 / 0x70552` | Genesis-native PC080SN strip/map commit — **OUT OF SCOPE** |

**PC080SN boundary confirmed: YES.** The forbidden strip/map work is `0x0556CE → 0x055948 →
0x0559C8 → 0x70418/0x70552` (plane/C-window/VRAM). `0x0406A4` sits *next to* it (called by the same
directional routines) but is provably independent: it touches only A5 actor WRAM coordinates.

### `0x0406A4` — fully decompiled (the key in-scope finding)

`sVar1 = X scroll (A5+0x10D8)`, `sVar2 = Y scroll (A5+0x10DA)`, each sign-selected or **zeroed** by
the direction in `D2` (D2∈{0,1}→Y active, {2,3}→X active; non-matching axis set to 0). It then walks
three actor arrays applying the delta to live coordinates:
- `A5+0x2C8` × 9 records: `+0x16 (X) += sVar1`, `+0x1a (Y) += sVar2`; if `+0x03 != 0` also
  `+0x34/+0x742 += sVar1`, `+0x744 += sVar2`.
- `A5+0x508` × 9 records (active, state≠3, `+0x24==0`): `+0x34/+0x16 += sVar1`, `+0x1a += sVar2`; if
  `+0x27 & 0x80` also `+0x32 += sVar1`, `+0x30 += sVar2`.
- `A5+0x748` × 11 records: same shape.
- finally `A5+0x24e -= sVar1`.

It is called by all four directional scroll routines (`0x055696/72E/7BA/854`). **In any single
invocation at most one axis is non-zero; the other axis and all three unconditional array writes are
applied with the matching delta — but when the camera is stationary on that axis, the entire
~29-record walk mutates coordinates by `+0` (a provable no-op, since `A5+0x24e -= 0` too).**

**This is the top in-scope candidate (see §5).** It is pure coordinate propagation — independent of
scroll *semantics* (the scroll amount is an input, unchanged), map semantics, actor ordering,
gameplay timing (identical net coordinates), collision, and object behavior.

### Top 3 in-scope candidates adjacent to the forbidden work

1. **`FUN_000406a4` actor-coordinate scroll compensation — zero-delta early-out.**
   - *Semantic responsibility:* world-lock active actors to the scrolling camera.
   - *Independent of PC080SN:* touches only A5 actor WRAM; no plane/C-window/VRAM.
   - *Repeated work:* walks ~29 actor records; invoked from up to 4 directional routines, so the
     non-matching directions (and any stationary-camera frame) walk all records applying `+0`.
   - *Correctness risk:* **LOW** for a guarded early-out `if (sVar1==0 && sVar2==0) return;` — the
     body's only non-`+0` effect in that case is `A5+0x24e -= sVar1` which is also `-= 0`; every
     conditional per-record write adds `+0`. Net state provably identical. (MEDIUM only if the author
     instead tried to restructure the per-record conditionals.)
   - *Suitable for Cody after the current patch:* **YES** — small, bounded, no semantic change.
2. **The `0x4210E` 7-call dispatch glue — extend the lean-save contract.** Apply the same
   "dispatcher owns the full save once; inner helpers preserve only their loop-live registers"
   discipline Cody just proved for the probes to the remaining per-call register preservation around
   the seven `0x4210E` calls, where source shows redundant nested full saves. *Independent of
   PC080SN.* *Risk:* LOW-MEDIUM (needs the same per-call liveness proof as §1). *Heavy-frame
   relevance:* fixed per-frame, not actor-scaling → smaller than #1.
3. **Per-actor invariant hoist in the generic/universal probes.** The probes recompute the
   effective-bank mask from `pc090oj_sprite_ctrl_shadow` (`andi #0x00E0; lsr`) and re-read usage
   descriptors per actor; the sprite-ctrl-derived bank is frame-invariant and could be computed once
   per frame. *Independent of PC080SN.* *Risk:* MEDIUM (must prove the shadow can't change mid-frame
   within the dispatch). *Heavy-frame relevance:* scales with actor count. Propose only after #1.

**Do not touch** `0x0556CE/0x0559C8/0x70418/0x70552` (PC080SN strip/map) or `collision_map_surface_postprocess_5a29c`
(collision surface — excluded).

---

## 4. Build-0412 `_c` MODE closeout — tooling review

Tool: `tools/mame/scripts/native_sprite_fullgame_closeout.lua`. Build 0411 reached all 18 subrounds;
0412 reached only 4 before `MAX_FRAMES`, with `fallback 0 / adapter 0 / crash 0`.

**Root assumption (fragile):** the entire route is **display-frame driven**, not state/event driven.
- Movement: `t = gameplay_frames`, cadence `(t % 960) < 480` etc. (lines 193-197).
- MODE-press gate: `stable = frame - subround_changed_at >= dwell_frames`, `released = frame -
  last_mode_frame > 30`, `(frame % 20) < 10` — all in **display `frame`** (lines 200-204), and
  `subround_changed_at` is recorded in display `frame` (:180).
- Abort: `frame >= max_frames` (:218), `max_frames` default 18000 display frames.

In-game progress (reaching each subround boundary, walking to the scroll edge that triggers the next)
advances on **gameplay ticks**, not display frames. Build 0412 runs at **0.9033 workers/rendered
frame** with a heavy tail (29% of IRQs over budget, 116 frames with no completed worker), so the same
display-frame budget now yields fewer gameplay ticks → less in-game advance → the route exhausts
`max_frames` after ~4 subrounds. `fallback 0 / adapter 0 / crash 0` means the production ROM did not
fault, did not hit the native fallback, and showed no adapter anomaly — the game simply was not driven
far enough.

**Likely production regression:** NO (UNPROVEN as a regression; the clean fault counters point away
from one). **Likely tooling synchronization issue:** YES.

**Exact fragile assumption:** progression input and the dwell/stability/abort gating are keyed to
display-frame counts, which assume a fixed display-frame→gameplay-progress rate; the changed 0412
worker/tick cadence broke that, and the fixed 18000-display-frame cap expires before subround 18.

**Smallest tooling-only correction (does NOT alter the production ROM):** make progression
state/event-driven using signals the script already reads (`A_SUBROUND`, `A_PROGRESS`, `A_ROUND`):
1. Record `subround_changed_at` and compute `stable`/`released` in **`gameplay_frames`**, not display
   `frame`, so MODE presses pace to actual ticks (the movement path already uses `gameplay_frames`).
2. Replace the fixed `frame >= max_frames` abort with a **progress watchdog**: continue while
   `A_PROGRESS`/subround keep advancing; abort only after a long window with *no* `A_PROGRESS` change
   (plus a generous absolute safety ceiling). Budget the ceiling in gameplay ticks, not display
   frames.
3. Keep the coin/start window as-is (frontend is display-frame stable), but gate it on the frontend
   scene, which the script already detects.

This is the preferred state-driven approach the framework already supports.

---

## 5. Next recommended Cody target (after the current register-save patch)

**Routine:** `FUN_000406a4` — actor-coordinate scroll compensation — with a **zero-delta early-out**.

**Why:** ranked by *recoverable cycles in over-budget/heavy frames*, not average. It walks ~29 actor
records and is reachable from up to four directional scroll routines; stationary-axis / stationary-
camera frames apply the full walk as `+0`, and non-matching-direction invocations do the same. A
guarded `if (sVar1==0 && sVar2==0) return;` removes those walks with provably identical state. It is
the cleanest bounded win adjacent to the (forbidden) PC080SN scroll chain, and its cost scales with
active-actor count, which correlates with heavy frames.

**Heavy-frame relevance:** MEDIUM-HIGH (actor-count-scaling; largest when many actors are active but
the camera is momentarily still on an axis, and whenever ≥1 directional call has a zero delta).

**Correctness risk:** LOW for the guarded early-out (no semantic change: coordinates, `A5+0x24e`, and
every per-record conditional are all `+0` in the skipped case). Must preserve the exact structure for
the non-zero path.

**Requires PC080SN changes:** NO. **Requires Phase D/E:** NO.

**One thing to confirm first (static, cheap):** whether `0x055650` invokes all four directional
routines per frame or only the active one — this sets whether the early-out saves up to 3 redundant
full walks per frame (all-four dispatch) or only the stationary-camera frames (single dispatch).
Either way the win is real and the early-out is safe.

**Not chosen as #1 but queued:** the `0x4210E` 7-call dispatch-glue lean-save extension (§3 #2) and
the per-actor effective-bank hoist (§3 #3).

---

**IMPLEMENTATION PERFORMED: NO.** Review only; Cody's working tree untouched.
