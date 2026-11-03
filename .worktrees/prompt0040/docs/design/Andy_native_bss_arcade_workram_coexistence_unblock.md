# Native BSS / Arcade WorkRAM Coexistence Unblock — STOPPED (founding premise refuted)

**Agent:** Andy · **Date:** 2026-09-03 · **Status:** STOPPED before any placement change. The premise that
OPT-003 shifts native BSS into arcade workram is **false** (measurement artifact). OPT-003 does **not**
move BSS; its epoch-1 gate failure is real but caused by a **code/rodata layout shift**, root cause still
open. No WRAM-ownership change made (fixing a non-existent problem would be wrong).
**Corrects:** [Andy_build0341_opt003_completion_and_epoch_gate_robustness.md](Andy_build0341_opt003_completion_and_epoch_gate_robustness.md) §6 and the Build-0340 doc — their "native BSS −8 shift → arcade-workram collision" conclusion is **withdrawn**.

---

## 1. Phase 0
- **Classification: EXTENDING** (intended). **Contradiction: CONFIRMED/STRONG** → STOP. The task's founding
  evidence ("`fg_boundary_active_lut` 0xFF6190 → 0xFF6188, −8 BSS shift caused by OPT-003") is disproven.
- Prior: `project_arcade_workram_overlap` remains a real latent concern in general, but it is **not** what
  OPT-003 trips.

## 2. Build-0341 evidence — what was actually right vs wrong
- **Right:** OPT-003 palette output identical (512 combinations, 0 mismatches). Reference passes the seven
  -epoch gate; OPT-003 fails epoch 1 (Plane-A code 0x034C, expected slot 0x04E0, actual 0x0000). Reproduced.
- **Wrong:** the −8 "BSS shift." The Build-0341 comparison used `symbols_ref0341.txt` captured after a
  `make all`, whose **last** sub-build is the score-variant (`RASTAN_DIAG_SCORE_METRIC=1`), so that symbol
  map contains the ~6-byte diagnostic BSS (`diag_servicing_peak`+`diag_score_bcd`) at the start of `.bss`,
  which pushes every later BSS symbol down. It was compared against a plain **release** OPT-003 symbol map
  (no diag BSS). The −6/−8 deltas are the **diag-config difference**, not OPT-003.

## 3. Complete WRAM ownership map (relevant extract)
Linker (`apps/rastan-direct/link.ld`): `.bss 0xFF4000 (NOLOAD)` — native BSS pinned at a fixed base 0xFF4000.
Absolute arcade-domain symbols are defined below it (e.g. `EXPECTED_A5_BASE`=0xFF0000,
`ARCADE_WORKRAM_A5_BASE` anchor written to ROM 0x10C000). Native BSS spans ~0xFF4000..0xFFC06E.

## 4. Matched-config proof — OPT-003 does NOT move BSS
Rebuilt **both** reference (OPT-003 reverted) and OPT-003 as the **same release config** (`make
out/symbol.txt`) and diffed the 0xFF (BSS) symbols:

    BSS delta distribution (opt-ref), matched release config: {0: 138}
    shifted BSS symbols: 0
    fg_boundary_active_lut: ref=0xFF6188 opt=0xFF6188  (delta 0)
    staged_sprite_sat:      ref=0xFFB228 opt=0xFFB228  (delta 0)

**Every native BSS symbol is identical.** There is no BSS shift and therefore no new arcade-workram
collision. `fg_boundary_active_lut` is at 0xFF6188 in both.

## 5. What OPT-003 DOES change — code/rodata layout only
Matched-config code-symbol diff (0x07xxxx):

    fg_boundary_install:        0x0726A2 -> 0x0726A2  (delta 0, unshifted, BEFORE pc090oj_hooks)
    palette_route_lookup:       0x072AF8 -> 0x072AF8  (delta 0)
    pc090oj_native_emit_pass:   0x07361A -> 0x07360C  (delta -14, inside pc090oj_hooks: palsel shrank)
    fg_boundary_packages:       0x0741F0 -> 0x0741E0  (delta -16)
    pc090oj_palsel_lut:         (new rodata, +512B; downstream rodata +496)

So OPT-003 perturbs the ROM `.text`/`.rodata` layout (palsel is ~14 bytes shorter; a 512-byte LUT is added),
shifting some native symbols. BSS is untouched.

## 6. Real, deterministic failure (config-matched, drift-safe)
Standalone epoch-1 case, `SURVIVAL_FRAMES=8` (drift-safe: `active_record` stays 3), each ROM with its own
matching symbols:
- **Reference:** `result=PASS`, `full_plane_a_lut=PASS`.
- **OPT-003:** `result=FAIL`, `full_plane_a_lut=FAIL`, `index=308 code=034C expected=04E0 actual=0000`.

Because BSS is identical and the failure persists across 8 stable frames, it is **neither** a BSS collision
**nor** pure sampling timing. It is a genuine runtime divergence tied to the code/rodata layout shift.

## 7. Root cause — OPEN (narrowed, not proven)
Candidate: OPT-003's native-symbol layout shift (notably `fg_boundary_packages` −16) is not being fully
accounted for somewhere between the installer's source data and the runtime `active_lut` population — e.g.
a native-address-as-data or a patch reference to a shifted symbol that resolves stale, so one installer
entry (code 0x034C→0x04E0) is never written. Native→native refs (linker) and arcade→native refs
(symbol.txt at patch time) are normally both correct, so the exact broken path is not yet identified. This
needs a targeted diagnostic (below), **not** a BSS/workram change.

## 8. Why NO placement change was made
The task's fix (reserve/pin native BSS disjoint from arcade workram) addresses a shift that **does not
occur**. Native BSS is already pinned at 0xFF4000 and is byte-stable under OPT-003. Implementing a WRAM
-ownership change here would be fixing a non-problem and could destabilize a currently-correct layout.
Prohibited-list items (padding, hardcoding, suppressing the arcade writer, weakening the gate) are likewise
inapplicable and were not done.

## 9. Recommended next diagnostic (for Tighe's decision)
Cheap, decisive, non-destructive:
1. **Append-only LUT test:** place `pc090oj_palsel_lut` so it does **not** shift any existing symbol (own
   object linked last, or a dedicated trailing section). Rebuild + gate. If OPT-003 then PASSES, the failure
   is caused by *shifting existing native symbols*, and the fix is either a stable-layout placement or
   declaring the missing relocation/reference class in the postpatcher — **not** BSS.
2. If it still fails, dump `active_lut[0x034C]` (WRAM 0xFF6188+0x698) frame-by-frame from the installer to
   see whether it is never written vs written-then-clobbered, and compare `fg_boundary_packages` bytes
   between the two ROMs.

## 10. OPT-003 state
Restored and intact in the working tree (include + LUT palsel). Palette equivalence unchanged (512, 0
mismatches). No runtime scan. Still **blocked** — not by BSS, by the open code-layout root cause.

## 11. Builds / counter
No numbered build produced by this task (all ROMs were scratch reconstructions via prepatch+postpatch).
Counter unchanged at **341**. Ledger unchanged. Gate lua restored to original (unmodified).

## 12. Deferred VRAM reclaim (preserved, NOT started)
Unchanged: 0xD000–0xDFFF (128 slots) + unused Window 0xF000–0xF7FF (64 slots) ≈ 192 pattern slots to
enlarge the Layer-A pool and cut loaning; SAT cannot use it (80-sprite cap). Still the next major perf task
after OPT-003 is unblocked.

## 13. STOP state
STOP condition 7 (CONFIRMED contradiction of the task premise) and Phase-0 contradiction rule. The
native-BSS ↔ arcade-workram fix has no basis for OPT-003. Handed back to Tighe with the corrected evidence
and the append-only-LUT diagnostic as the recommended real next step.
