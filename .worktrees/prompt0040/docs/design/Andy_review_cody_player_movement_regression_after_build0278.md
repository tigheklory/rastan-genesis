# Independent Review — Cody's Build 0274–0278 Player Movement Regression

**Agent:** Andy · **Type:** analysis/architecture review (NO build, NO source/spec/tool change, counter stays
278) · **Accepted baseline:** Build 0273. Reviewed working tree = Cody's 0278 state.

## Bottom line (proven)
The movement/ground regression is **not** a player-sprite logic bug, a register-contract bug, or "native work
starving the loop." It is a **stale hardcoded hook continuation** exposed by Cody's `shift_replacements`:

> Cody's 62 `shift_replacements` moved the copied maincpu by −74 bytes at the 0x557xx region. The **pre-existing
> Build-0247 Plane-A vertical-scroll hooks** jmp back to **hardcoded runtime addresses**
> (`PLANE_A_PAN_UP_CONTINUATION=0x55998`, `PLANE_A_PAN_DOWN_CONTINUATION=0x5590C`, tilemap_hooks.s:142-143,
> 500/534) that were correct **before** the shift. After the shift those continuations live at **0x5594E /
> 0x558C2**, and `0x55998 / 0x5590C` now decode as **the wrong / a mid-instruction byte**. Both continuations are
> exactly the `move.w a5@(0x10B0),d1` vertical-origin code. So the Plane-A hooks jmp into garbage instead of the
> `a5@0x10B0` update — `a5@0x10B0` never progresses, collision sampling stays on the wrong cell, and the player
> falls through the floor.

Verified in the built ROM (`build/genesis_postpatch.disasm.txt`):
- `558ba: jmp 0x706fc` and `55946: jmp 0x706a4` — forward hook entries relocate correctly (symbol-resolved).
- `558c2: move.w a5@(0x10B0),d1` and `5594e: move.w a5@(0x10B0),d1` — the **real** continuations (arcade
  0x5570C / 0x55798) after the −74 shift.
- `55998: beq 0x559a2` (wrong instruction); **no instruction boundary at 0x5590C** (mid-instruction). These are
  the **stale** targets the hooks still jmp to.
- Address map: arcade `0x5570C -> 0x558C2`, arcade `0x55798 -> 0x5594E`; hooks hardcode `0x5590C / 0x55998`.

This is exactly the checkpoint's proven divergence (`a5@0x10B0` stays 0) — one level higher than the checkpoint
reached: the checkpoint saw the continuations at 0x558C2/0x5594E and 0x10B0 stuck, but did not connect that the
Plane-A hooks jmp to the *un-shifted* addresses.

## Review table
| Area/change | Cody's conclusion | Andy's finding | Classification | Keep/revert/revisit |
|---|---|---|---|---|
| Build 0274 architecture (main-loop native PLAYER_BODY/FRONT staging → VBlank commit) | correct objective, runtime rejected | architecture is SOUND; the *build mechanism* (shifts) broke unrelated hooks | correct | KEEP (architecture) |
| 0275 FRONT/BODY register preservation D1/D3/D4/D6 | root-cause candidate (later superseded) | REAL clobber defect, but FRONT is blank during the intro fall and BODY runs after movement — cannot cause the fall-physics regression | B (real bug, unrelated to this regression) | KEEP |
| 0276 shifted long/immediate reference relocation | required relocation correctness | REAL defect in shift handling; necessary *only because* the shift approach was chosen | A (correct given shifts) | KEEP-if-shifts, else moot |
| 0277 branch/reference to replacement-start | mechanically wrong before fix | REAL defect; same caveat | A (correct given shifts) | KEEP-if-shifts, else moot |
| 0278 BODY mode-7 `D2=0` restore | contract restored | REAL contract defect, unrelated to plane-A | B (real, unrelated) | KEEP |
| **Plane-A hook continuations 0x55998/0x5590C** | not identified | **THE root cause**: stale hardcoded jmp-back into shifted maincpu | E (defect, unaddressed) | **FIX before 0279** |
| Anchor scope-creep: `a5+0x129A/0x129C` direct publish, retire 0x0547C0 prologue, rewrite 0x051E00, 0x542E8 inactive clear | correct, physics-neutral | plausible but UNVERIFIED scope beyond the output-site cut; not the fall-physics cause (different addresses) | C/D (partial/unproven) | REVISIT (verify aux object; not required for the cut) |
| `shift_replacements` approach (62 sites, moves maincpu) | mechanism | fragile: moving the maincpu invalidates every hardcoded genesis-only→maincpu continuation; pipeline never relocates those | E (systemic gap) | RECONSIDER pipeline/approach |
| Scheduling/starvation (`sat_frame_ready` ~1/8 frames) | strong hypothesis | most likely a *downstream symptom* of executing garbage from the stale jmp; NOT shown independent | still hypothesis, disfavored | do not pursue as cause |

## 1. Build 0274 architectural review
The lifecycle Cody built is correct and matches the accepted design: `native_player_frame_begin` resets
PLAYER_BODY/FRONT once/frame before both producers (FRONT `jsr 0x59F92`@0x51060, BODY `jsr 0x540CC`@0x5151C —
both once/frame, FRONT before BODY, proven in the reused arcade debug.log); `native_sprite_frame_begin` keeps the
player lanes; the single `pc090oj_native_emit_pass` finalizer commits at VBlank; order preserved. No second
renderer, no VBlank rerun of 0x540CC, no tuple decoder. **The architecture did not cause the regression.** The
regression came from the *patching method* (variable-length shifts), not the sprite architecture.

## 2. 0275–0278 change audit
All four are **real defects Cody correctly found**, but each is either unrelated to the fall-physics failure
(0275, 0278) or is corrective plumbing made necessary only by the shift approach (0276, 0277). None touched the
Plane-A continuation. This is why "still broken" recurred four times: the fixes were orthogonal to the cause.

## 3. First proven causal divergence
The Plane-A no-publish hooks (arcade 0x55704/0x55790, native at 0x706fc/0x706a4) execute, then `jmp` to
`0x5590C`/`0x55998`. Post-shift those are wrong bytes; the intended `a5@0x10B0` continuations are at
0x558C2/0x5594E. This is the **first** control-flow divergence in the affected path — upstream of the collision
sampler and upstream of `a5+0x1266` state effects the earlier reports chased.

## 4. a5+0x10B0 producer / lifecycle
`a5@0x10B0` (0x10B0=4272) is read/updated in the Plane-A vertical continuations (arcade 0x5570C/0x55798 =
`move.w a5@(0x10B0),d1`). It is a foreground/playfield vertical origin (Build 0247 native Plane-A no-publish
routing) that also feeds collision addressing. Its progression depends on the hooks returning to those
continuations — which they no longer do.

## 5. Main-loop / VBlank / finalizer order
No ordering or duplicate-finalization defect was found to cause this. The finalizer runs in the 41dae/45dfa hooks
and frame-begin in 41f5e as in 0273; player lanes are main-loop-owned and preserved. The `~1/8` sprite cadence is
consistent with the CPU executing garbage after the stale jmp (cascading wrong paths), i.e. a **symptom**, not an
independent scheduling cause. It is NOT proven that native staging starves the loop.

## 6. Translation-pipeline changes that should remain
- 0276 shifted long/immediate relocation and 0277 replacement-start target mapping in `shift_table_patcher.py` /
  `postpatch_startup_rom.py` are genuine correctness fixes **for the shift mechanism** and should remain as long as
  `shift_replacements` are used.
- 0278 `D2=0` mode-7 restore and 0275 register preservation are genuine arcade-contract fixes; keep.

## 7. Changes that should be reconsidered
- **The `shift_replacements` design is the real hazard.** It relocates references *inside* the maincpu but there
  is **no pass that relocates genesis-only-section (hook) references that target the shifted maincpu region**.
  The Plane-A continuations are the confirmed casualty; any future hook that jmps into a shifted range would break
  the same way. Options, in order of robustness: (a) extend the postpatch to relocate genesis-only→maincpu
  targets by the shift table (make `PLANE_A_PAN_*_CONTINUATION` shift-aware, resolved from arcade addr + shift);
  (b) avoid moving the maincpu for these edits — use byte-neutral `jmp`-to-hook + hook-does-work + `jmp`-back
  patches (the established pattern) so layout never shifts; (c) as a last resort, hardcode the two continuations
  to 0x558C2/0x5594E (fragile — rebreaks on the next shift).
- **Anchor scope-creep** (0x129A/0x129C, 0x0547C0, 0x051E00) exceeded the "replace only the tuple-output
  realization" cut and is unverified; confirm the auxiliary object still renders before trusting it.

## 8. Actual root cause
**PROVEN.** Plane-A vertical-scroll hooks jmp to stale hardcoded continuations (0x5590C/0x55998) that Cody's
`shift_replacements` moved to 0x558C2/0x5594E, bypassing the `a5@0x10B0` update, so the player never lands. The
scheduling/starvation theory is NOT the root cause.

## 9. One next action before Build 0279
Because root cause is proven, the next action is a **targeted fix, not a hypothesis build**: make the Plane-A hook
continuations shift-aware (or, minimally, retarget them to the post-shift addresses 0x5594E/0x558C2) **and audit
every genesis-only hook/opcode_replace target that references arcade addresses > the first shift point (0x5105A)
for the same staleness**; then verify in Genesis-NTSC that `a5@0x10B0` advances (0x01FF then −3) and the player
lands. A Build 0279 that makes exactly that fix is justified; the six diagnostic ROMs (0274–0278) stay preserved.
EOF
echo "review written: $(wc -l < docs/design/Andy_review_cody_player_movement_regression_after_build0278.md) lines"
echo "no production/tool/spec change; counter: $(cat build/rastan-direct/build_counter.txt)"