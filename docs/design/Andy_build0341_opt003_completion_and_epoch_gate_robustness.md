> **CORRECTION (2026-09-03, later):** §6's root cause — "OPT-003 shifts native BSS by −8 bytes → arcade
> -workram collision" — is **WITHDRAWN**. It was a measurement artifact: the reference symbol map was
> captured from a score-variant build (diag BSS present) and compared against a release OPT-003 map. A
> matched-config diff shows **OPT-003 does not move BSS at all** (all 138 BSS symbols identical;
> `fg_boundary_active_lut`=0xFF6188 in both). The epoch-1 failure is real but caused by a **code/rodata
> layout shift**, not BSS. See [Andy_native_bss_arcade_workram_coexistence_unblock.md](Andy_native_bss_arcade_workram_coexistence_unblock.md).

# Build 0341 — OPT-003 Completion Attempt + Epoch-Gate Robustness Audit (STOPPED, new root cause)

**Agent:** Andy · **Date:** 2026-09-03 · **Status:** STOPPED — the "gate sampling fragility" hypothesis is
**refuted**; OPT-003 causes a real, deterministic native-BSS layout shift that breaks Plane-A LUT
installation. No OPT-003 numbered ROM published. Awaiting Tighe's decision.
**Prompt:** "ANDY — OPT-003 COMPLETION + SEVEN-EPOCH GATE ROBUSTNESS + NUMBERED TEST BUILD(S)".
**Supersedes the interpretation in** [Andy_build0340_opt003_prebaked_sprite_palette_line.md](Andy_build0340_opt003_prebaked_sprite_palette_line.md) §8.

---

## 1. Phase 0
- **Classification: EXTENDING** (harness robustness audit + completing the documented OPT-003; no new
  subsystem). Priors: OPT-003 state is authoritative in the Build-0340 design doc; KF-046/KF-066 route model.
- **Priors used:** `project_arcade_workram_overlap` (native BSS ↔ arcade A5 workram coexistence) — now
  directly implicated. No contradiction with documented OPT-003 palette equivalence (still 0 mismatches).
- **Rediscovery avoided:** did not re-derive the palette-route problem or re-run the equivalence proof.

## 2. Prior Build-0340 state (carried in)
- OPT-003 implemented + proven output-identical (512 combinations, 0 mismatches; 0x30/0x33/0x36/miss/frontend
  spot checks correct). Runtime linear scan removed; `palette_route_lookup` has 0 live callers.
- Build 0340 was consumed by a differential `make all` on the *non*-OPT-003 revert (disclosed).
- Build 0340 doc interpreted the epoch-1 gate failure as "single Plane-A cell sampling fragility." **This
  task set out to prove/fix that — and disproved it.**

## 3. Gate semantic-boundary analysis (Part A)
`tools/mame/scripts/build0310_epoch_gate.lua`: for each target epoch it force-injects the production
installer, then when `active_record==target && active_package==target && epoch_transitions>=1` it records
`install_frame` and asserts the full Plane-A code→slot LUT (`verify_maps`) and fixed Plane-B LUT. The
original code sampled `verify_maps()` **on `install_frame`** (the activation frame); `required_survival_frames`
(8) only gated *when the summary was written*, not a re-check. So the working hypothesis was: the active
code→slot LUT is filled incrementally and the assertion fires one frame early.

## 4. Harness change made — then reverted (Part B, and why)
- **Change tried:** move `verify_maps()`/`verify_fixed_b()` from `install_frame` to the settle point
  (after `frame - install_frame >= required_survival_frames`), i.e. assert "installation completed and
  published", not "at exactly frame N."
- **Result:** OPT-003 still FAILED identically (epoch 1, index 308, `actual=0000`).
- **200-frame probe:** ran the epoch-1 case standalone against the reconstructed OPT-003 ROM with
  `SURVIVAL_FRAMES=200` (sampled at install+200, external_frames=528): still `code 0x034C actual=0000`.
  **The entry never installs — it is not a settle-timing issue.**
- **Therefore the premise for the harness change is refuted, and the change was reverted.** The original
  gate was **correct**, not fragile: it truthfully reported that a required LUT entry is missing.

## 5. Reference still passes (Part C) — control
- Built the reference (OPT-003 reverted, all other working-tree state identical) with the (then-still-modified)
  gate → **PASSED all seven epochs**, published **Build 0341** (`dist/rastan-direct/rastan_direct_video_test_build_0341.bin`).
  Reference installs code 0x034C→slot 0x04E0 correctly. Counter → 341.
- **Conclusion proven:** OPT-003 is the differentiator. Reference PASS, OPT-003 FAIL, deterministic.

## 6. OPT-003 gate result — real divergence, root cause found (Part C)
- OPT-003 FAILs epoch 1: `full_plane_a_lut=FAIL index=308 code=034C expected=04E0 actual=0000`, and never
  installs even at 200-frame settle. All other gate metrics identical to reference.
- **Root cause — native symbol/BSS layout shift.** Comparing `out/symbol.txt` (reference 0341) vs OPT-003:
  | symbol | reference | OPT-003 | shift |
  |---|---|---|---|
  | `fg_boundary_active_lut` (WRAM/BSS) | 0xFF6190 | 0xFF6188 | −8 |
  | `fg_boundary_active_record` (BSS) | 0xFFB220 | 0xFFB218 | −8 |
  | `staged_sprite_sat` (BSS) | 0xFFB230 | 0xFFB228 | −8 |
  | `fg_boundary_install` (code) | 0x072706 | 0x0726A2 | −100 |
  | `fg_boundary_packages` (code/data) | 0x074290 | 0x0741E0 | −176 |
  | `pc090oj_palsel_lut` (rodata) | — | 0x0804F2 | (new) |
- OPT-003 adds a 512-byte `.rodata` LUT and changes `.Lnative_palsel`'s size; via the link/section layout
  this shifts native symbol addresses — including **native BSS by 8 bytes**.
- The native `fg_boundary_active_lut` at 0xFF6188 lies inside the arcade **A5 workram** window
  (A5=0xFF2200 → A5+0x3F88). This is exactly the documented **native-BSS ↔ arcade-workram coexistence
  fragility** (`project_arcade_workram_overlap`): the arcade program's hardcoded/A5-relative WRAM addresses
  are fixed, native BSS is linker-placed, and an 8-byte native-BSS shift broke the coexistence for one
  installer entry (code 0x034C never gets written). The palette LOGIC is unaffected (proven identical); the
  failure is the **binary layout perturbation**, not OPT-003's computation.
- **This is a latent project-wide fragility, not an OPT-003 palette defect.** Any optimization that changes
  native code/data size risks re-tripping it until the native-BSS-vs-arcade-workram layout is made robust
  (pin native BSS to a base that provably cannot collide with arcade workram — the deferred
  `project_arcade_workram_overlap` fix).

## 7. OPT-003 final runtime path (unchanged, restored in tree)
`scene_id + effective_bank → (scene&0x03)<<7 | (eb&0x7F) → move.b pc090oj_palsel_lut[idx] → line`. Effective
-bank computation preserved exactly; no linear scan; no dual execution; no fallback to `palette_route_lookup`;
palette policy unchanged.

## 8. Equivalence result (unchanged)
512 combinations, **0 mismatches**; spot checks 0x30→2, 0x33→0, 0x36→1, miss→3, frontend→3 all correct.

## 9. Numbered builds produced
- **0341 = reference control** (non-OPT-003; OPT-003 reverted). PASSED seven-epoch gate; published + ledgered.
  This is a disposable control artifact proving the gate correctly distinguishes the two paths — it is **not**
  an OPT-003 build.
- **No OPT-003 numbered ROM** (blocked by the real divergence; STOP condition 1 met).
- Counter = 341; 0340 (prior) and 0341 both non-OPT-003. Any OPT-003 candidate must be **0342+**.

## 10. Performance estimate/observation
Unchanged from Build 0340: labeled ESTIMATE only (~tens of cycles/piece → order 10³ cycles/frame at ~28
pieces), no measured value, no `_d` before/after (no OPT-003 numbered build). Not recorded as a production
saving.

## 11. USER MUST VERIFY
None applicable yet (no OPT-003 ROM to test). When a fixed OPT-003 build exists, verify: reaches R1/P1;
title/frontend, ROUND/READY, Rastan, Lizardman, water/dirt, waterfall, Layer B, sprites unchanged; not slower.

## 12. Deferred VRAM reclaim (preserved, NOT started)
Reclaim currently-unused Genesis VRAM to enlarge the Layer-A residency pool and reduce pattern DMA/loaning:
- `0xD000–0xDFFF` = 4 KB / 128 tile-slot gap between the Plane B and Plane A nametables (permanently unused);
- Window region `0xF000–0xF7FF` = 2 KB / 64 tile-slots (Window disabled; reg 17/18 = 0);
- ~6 KB / ~192 pattern slots total → Layer-A window ~484 → ~676 (+40%), fewer loans. SAT cannot use it
  (80-sprite hardware cap). Do lossless flip-normalization (10 tiles) and this reclaim before any lossy
  Layer-B merge. Major next performance task after OPT-003 is unblocked.

## 13. STOP state
- **Why:** OPT-003 fails the seven-epoch gate for a *real* reason (STOP condition 1: complete Plane-A state
  still wrong after a legitimate 200-frame boundary). The gate is correct; the harness change was reverted.
  The root cause is a native-BSS layout shift colliding with arcade workram — NOT a graphics defect (no
  graphics patch) and NOT gate weakening.
- **Decision required (Tighe):**
  1. **Unblock path:** fix the native-BSS ↔ arcade-workram fragility (pin native BSS to a collision-proof
     base — the deferred `project_arcade_workram_overlap` work) so size-changing optimizations are safe; then
     OPT-003 lands unchanged. This is the durable fix and unblocks the whole optimization program.
  2. **Or** a narrower interim: make OPT-003 not perturb the critical BSS layout (e.g. isolate/pad), but that
     only masks the fragility and will recur with the next optimization.
- **Not done:** no OPT-003 publish, no IMPLEMENTED claim, no counter rollback, gate restored to original.

## 14. Harness status
`build0310_epoch_gate.lua` restored to its original (install-frame) assertion. No net harness change.
