# Semantically Valid Seven-Epoch Gate — Replacement Design and Blocker

**Author:** Andy · **Date:** 2026-09-07 · **Type:** Infrastructure / Validation
**Build produced:** NO. Baseline unchanged: counter=348. Canonical gate **left in place** (see §26 STOP).

---

## 1. Phase 0 baseline statement
- **Classification:** INFRASTRUCTURE (target = canonical validation methodology, not game behavior).
- **Relevant priors:** `Andy_pure_publisher_audit_palette_gating_and_opt003.md` §7 (OPT-003 = synthetic
  gate artifact, proven); `Andy_sonic1_vs_rainbow_islands_plane_ab_architecture_and_title_completion.md`;
  the natural-transition harness `tools/mame/scripts/opt003_natural_transition.lua`.
- **Rediscovery hazards (HIGH):** the seven-epoch gate is a KNOWN-INVALID synthetic injection; the
  arcade input field names differ on the Genesis machine (only `P1 Start`/`P1 A`..`P1 C`, no
  `Coin 1`/`1 Player Start`); do not treat the old gate's pass/fail on timing changes as truth.
- **Open issues touched:** the OPT-003 / publication-gate infrastructure thread (no numbered issue
  ID; tracked via the OPT-003 design docs).
- **Contradiction with a CONFIRMED/STRONG KF:** none.
- **KNOWN_FINDINGS impact:** Option A — no new finding to index (INFRASTRUCTURE).

## 2. Task classification
INFRASTRUCTURE. Expected KF result Option A (confirmed).

## 3. Relevant KF entries
No `KF-NNN` requires change. The durable facts live in the OPT-003 design docs.

## 4. Open/Closed issues touched
OPT-003 publication-gate thread (infrastructure). No graphics/perf issue closed.

## 5. Existing invalid gate behavior (`tools/mame/scripts/build0310_epoch_gate.lua` + `run_build0310_epoch_gate.sh`)
The runner drives 6 representative cases `record:epoch:package` = `0:0:0 3:1:5 4:2:6 5:2:2 11:3:3 13:4:4`.
For each, the lua:
1. drives inputs using **arcade field names** (`Coin 1`, `1 Player Start`) that **do not exist on the
   Genesis machine** → effectively no input → the **attract demo** auto-runs;
2. waits for `scene==1 && active_package==0 && eptrans>=1` (an **attract-residue** state, not a real
   player-entered gameplay state);
3. **injects** the transition: writes the target record to `a5+0x013E`, pushes the interrupted PC,
   and sets `PC=fg_boundary_install` — hijacking an **arbitrary mid-frame PC** and **skipping the
   real record-advance owner** (`fg_boundary_advance_segment`) and all intermediate records;
4. samples `verify_maps` / `verify_fixed_b` at `install_frame`, then holds `survival_frames=8`.

**Why invalid:** the injection begins the 0→target transition from an attract-residue LUT (measured:
it shows a stale `active_lut[0x034C]=0x0420` while package 0 is active, where a *freshly*-entered
gameplay shows `0`) and executes the installer from an arbitrary PC context. The resulting
`active_lut[0x034C]` reading is timing-fragile (flips on a single added/removed instruction) and does
**not** reproduce under a real arcade-owned transition.

## 6. Prior natural-transition evidence (proven this session)
`opt003_natural_transition.lua` drives **real** entry (`P1 Start` bursts) + scroll (`P1 Right` + jump/
attack) so the arcade's own `fg_boundary_advance_segment` (arcade 0x0558FE) advances the record:

| Timing | reached record 3 | `active_lut[0x034C]` | +24 frames | exceptions |
|---|---|---|---|---|
| Build 0348 (unconditional palette) | frame 5277 | **0x0420 CORRECT** | stable | 0 |
| palette-gated (score.bin) | frame 5276 | **0x0420 CORRECT** | stable | 0 |

Record→package chain confirmed: `0→0, 1→0, 2→0, 3→5, 4→6, 5→2` (deeper: 11→3, 13→4).
`FG_BOUNDARY_RESEED_MASK = 0` — so `fg_boundary_advance_segment` **always installs immediately**
(never defers), which simplifies sequential advancement.

## 7. Original arcade semantic transition owner
`fg_boundary_advance_segment` — the native replacement for arcade PC **0x0558FE**. It does
`addq.w #1, 0x013E(%a5)` (the real record increment) then calls `fg_boundary_install`. This is the
legitimate arcade-owned boundary; the record is advanced **only** here (plus scene reset).

## 8. Current address-map proof
Resolve at build time from `apps/rastan-direct/out/symbol.txt` (NOT a fixed +0x200): current values
observed — `fg_boundary_advance_segment` = 0x0007258C (palette-gated build) / 0x00072588 (0348);
`fg_boundary_active_record` = 0x00FFB218; `_active_package` = 0x00FFB21C; `_active_lut` = 0x00FF6188;
`_epoch_transitions` = 0x00FFB1EC; `genesistan_current_scene_id` = 0x00FFC068. **The gate must derive
these from the matching build's symbol.txt each run** (a ROM/symbol mismatch silently invalidates
both the reads and any hook target — a trap encountered during this task).

## 9. Legitimate transition preconditions
- `genesistan_current_scene_id == 1` (real gameplay, reached via `P1 Start`, not attract residue);
- epoch 0 installed cleanly (`active_package==0`, `eptrans>=1`), `active_lut[0x034C]==0` (fresh);
- A5 = Genesis WRAM base (0xFF0000..0xFFFFFF); valid SP;
- the installer runs interrupt-masked + display-off (atomic); the LUT is authoritative immediately
  after it returns and stays so until the next transition.

## 10. New gate architecture (DESIGN — not yet integrated; see §26)
Replace the injection with a **test hook at the real semantic boundary**, preferred order:
1. **Real entry:** `P1 Start` to enter true gameplay (clean epoch-0), NOT the attract demo.
2. **Real advance owner:** to reach target record R, invoke `fg_boundary_advance_segment`
   sequentially (0→1→…→R) from a safe frame boundary — the arcade's real record-advance routine,
   which increments the record and installs via the real path. This is **not** the forbidden
   `write-record + PC→fg_boundary_install`; it uses the real owner and the real sequential chain
   from a clean precondition (§9).
3. At each of the 6 target records, run the **retained** assertions: `verify_maps` (active LUT vs
   package map, incl. `0x034C` where the active package owns it), `verify_fixed_b`, slot validity,
   survival window, zero exceptions, SP/control-flow sanity.
4. Determinism: repeat each case N times; require identical results.

## 11. Exact files changed
Report only (this file + AGENTS_LOG pointer). **No** change to `build0310_epoch_gate.lua`,
`run_build0310_epoch_gate.sh`, the Makefile, or any source. Probe scripts used for investigation are
scratch-only (not committed).

## 12. Old-vs-new assertion matrix (design)
| Old check | New check | Retained? | Reason |
|---|---|---|---|
| record/package sequence | same, reached via real advance owner | **Retain** | still the core coverage |
| active package == expected | same, sampled after real install | **Retain** | |
| `verify_maps` (active LUT) | same, but from clean gameplay + real advance | **Retain (resampled)** | fixes the artifact source |
| `verify_fixed_b` | same | **Retain** | valid, unaffected |
| slot validity | same | **Retain** | valid |
| survival frames | same | **Retain** | |
| exceptions == 0 | same | **Retain** | |
| SP/control-flow | same | **Retain** | |
| **synthetic record write + PC→installer** | **removed** | **Removed** | the invalid injection — the whole point |
| **arcade-field-name input** (`Coin 1`/`1 Player Start`) | **replaced** with `P1 Start` | **Replaced** | those fields don't exist on the Genesis machine; they left the gate in attract-residue state |

**No meaningful validation coverage is dropped.** Only the invalid transition-injection and the
non-functional input driving are removed.

## 13–17. Seven-epoch / A-B / determinism / exception results
**NOT ESTABLISHED THIS TASK.** The natural transition is proven correct for record 3 on both timings
(§6). The full 6-record run through the new mechanism — including the deep records 11/13 — was **not**
completed: see §26.

## 18. Existing project tools reused
`tools/mame/scripts/opt003_natural_transition.lua`, `run_opt003_natural_wsl.sh`,
`build0310_epoch_gate.lua` (verify_maps/verify_fixed_b logic to be reused), the current runner and
Makefile invocation, `apps/rastan-direct/out/symbol.txt`.

## 19–20. New tooling created / why
Investigation-only scratch probes (advance-hook probe) — **not committed**, not durable. No new
repository tool was justified because the durable path is to extend `build0310_epoch_gate.lua` /
`opt003_natural_transition.lua`, which was not completed (§26).

## 21. Obsolete synthetic infrastructure removed
**None removed** — the synthetic gate remains the canonical gate because a proven replacement is not
yet ready. Removing it now (with no working replacement) would leave the build with no Layer-A
validation.

## 22. Canonical Makefile/build integration
**Not performed.** No integration on unproven ground.

## 23. Regressions checked
No code changed; baseline 0348 intact; counter unchanged.

## 24. Open/Closed Issues Impact
- Open touched: OPT-003 / publication-gate infrastructure — advanced (design + proof of the natural
  transition) but not resolved.
- Opened: none.
- Closed: none.
- Deferred: full canonical replacement, pending §26 blocker.

## 25. KNOWN_FINDINGS impact
Option A — no new finding to index. Rationale: INFRASTRUCTURE task; corrects validation methodology,
no new durable system-behavior fact.

## 26. STOP status — BLOCKER (honest)
**STOP: the semantically valid replacement is DESIGNED and partially proven, but a reliable,
deterministic harness that satisfies the task's mandatory success criteria was not achieved this
task.** Specifically unresolved:

1. **Deterministic headless entry into real gameplay.** The natural harness reached record 3 twice
   earlier, but three follow-up headless entry attempts this task failed to re-enter gameplay with
   the same input pattern — headless entry timing (title→story cutscene→gameplay, ~2600+ frames, and
   its interaction with `P1 Start` bursts vs held scroll input) is not yet reliably reproducible. A
   canonical gate must be deterministic; this is not yet demonstrated.
2. **`fg_boundary_advance_segment`-hook validity is UNPROVEN.** The design's deep-record coverage
   (records 11/13, which have no practical natural-scroll path) depends on invoking the real advance
   owner from a safe boundary reproducing natural behavior. I could not complete this proof (blocked
   by (1) and a ROM/symbol-mismatch trap). Until it is proven to yield the same LUT as natural
   progression, it cannot back the canonical gate.
3. **Both A/B cases + all 6 records + N-run determinism** — the mandatory acceptance matrix — cannot
   be asserted without (1) and (2).

Per the task's own constraints ("must become MORE valid, not weaker"; "prove determinism, a single
lucky run is insufficient"; A and B must both PASS), integrating an unproven or flaky mechanism as
the canonical release gate would violate those invariants and endanger the release pipeline. The
correct action is to leave the current gate in place and resolve (1)–(3) in a focused follow-up
before canonical integration.

**Recommended next steps (concrete):**
- Nail deterministic headless gameplay entry (or capture a MAME save state at clean epoch-0 and load
  it in the gate — a legitimate, deterministic external test setup).
- From that clean state, prove the `advance_segment` sequential-hook reproduces the natural record-3
  result (0x034C=0x0420) on both timings; then extend to records 4/5/11/13.
- Only then replace the injection in `build0310_epoch_gate.lua`, retire the synthetic path, and wire
  it into the Makefile — with the full A/B + determinism matrix as the acceptance evidence.

---

## CONTINUATION RESULT (2026-09-07) — deterministic-entry fixed; advance-hook DISPROVEN; hard STOP

### Deterministic entry — ROOT CAUSE FOUND (not flaky)
The previous "entry failures" were a probe bug, not a harness flaw. The entry-detection gate
required `fg_boundary_epoch_transitions >= 1`, but that counter **stays 0** in this scenario even at
scene 1 / record 3 / package 5 (it is cleared by `fg_cache_reset` at scene entry and does not
re-arm here). Natural progression itself is reliable and deterministic: with `P1 Start` bursts +
held `P1 Right`/jump/attack, the game enters gameplay at frame **2646** and the record advances
naturally 0→1→2→3 (package 0→0→0→5) via the real `fg_boundary_advance_segment` owner. **Fix:** detect
entry by `scene==1 && record!=0xFFFF`, not by the epoch-transition counter.

### Equivalence experiment (the linchpin) — advance-hook FAILS
Compared the complete record-3 Layer-A state reached two ways (palette-gated ROM, matching symbols):

| Field | NATURAL (scroll to rec 3) | HOOK (enter, stop, invoke advance_segment 0→3 from frame-done) |
|---|---|---|
| active record | 3 | **0xFFFF** (invalid; scene-reset signature) |
| active package | 5 | **0xFFFF** |
| active_lut[0x034C] | 0x0420 | 0x0420 |
| **active_lut checksum (codes 0..2047)** | **0x000D8193** | **0x00155C5A** (≠) |
| stability (+40 frames) | identical 0x000D8193 | drifts → record 15/pkg 4/0x0015A2D3 |
| exceptions | 0 | 0 |

**The complete LUT is NOT equivalent** (checksum mismatch) and the record/package go invalid. Invoking
`fg_boundary_advance_segment` from an external frame-done boundary corrupts the transition — the same
arbitrary-PC-context flaw as the old injection. Per the task's own rule, this is a hard STOP: the
hook must NOT be extrapolated to the deep records.

### Consequence
- **Natural progression is the only proven-valid mechanism** — deterministic and correct for the
  reachable records (0, and 3/package 5; 4/5 are a longer but plausible scroll).
- **Deep records 11 (pkg 3) and 13 (pkg 4) have no proven-valid runtime path.** Natural scroll to
  them is impractical/fragile (record 3 alone took ~5400 frames of scripted play + hazard
  survival); the accelerated hook is disproven.
- Therefore the FULL 6-record canonical replacement cannot be completed without either (a) a
  **proven-safe** call boundary for `advance_segment` (e.g., pausing precisely at the arcade
  main-loop entry `0x3A208` with a defined register state, then emulating a proper call/return —
  a deeper RE + experiment than the frame-done attempt), (b) an automatically-regenerated,
  same-ROM/same-SHA save-state captured after reaching each deep record once (still needs a deep
  play to reach them), or (c) a scoped decision to validate reachable records at runtime and deep
  records via static generated-package-data checks (weaker deep coverage — requires Tighe's call).

### STOP status (continuation)
**STOP.** The advance-hook equivalence FAILED (mandatory STOP condition). Deterministic entry is
solved and natural progression is proven valid+deterministic, but deep-record coverage (11/13) has
no proven-valid mechanism. The canonical gate is **left in place** (unchanged) rather than replaced
with a partial/weaker mechanism. Next decision is Tighe's: pursue the safe-boundary RE (a), the
same-ROM save-state route (b), or the scoped static-deep-record acceptance (c).

---

## CONTINUATION 2 (2026-09-07) — safe-boundary invocation PROVEN CLEAN, but survival FAILS for streamed-transition records → STOP

### Dependency closure (static)
`fg_boundary_advance_segment` (arcade 0x0558FE): `addq.w #1,0x013E(a5)` then `fg_boundary_install`.
`fg_boundary_install` saves/restores d0-d7/a0-a4, masks interrupts itself, reads the record, the
STATIC package table, and the current active_lut; writes active_lut + active_package/record; DMAs.
**Its only external precondition is A5 = 0x00FF0000.** active_lut is written only by the install.

### Safe invocation boundary (works)
Corrected the frame-done failure: **full CPU context save → force A5=0x00FF0000 → mask interrupts
(SR|=0x0700) → call via a spin-sentinel return (0x60FE at SP-0x200) → restore full context.** The
arcade never sees a corrupted context; only the WRAM record/LUT advance. No 0xFFFF reset (unlike the
frame-done hook).

### Transient install: PASS for ALL 6 records (deterministic)
Sweep 0→13, `verify_maps(target_package)` at each target, 3 consecutive byte-identical runs:

| record | package | verify_maps | map codes | exceptions | SP |
|---|---|---|---|---|---|
| 0 | 0 | PASS | 283 | 0 | valid |
| 3 | 5 | PASS | 395 | 0 | valid |
| 4 | 6 | PASS | 480 | 0 | valid |
| 5 | 2 | PASS | 642 | 0 | valid |
| 11 | 3 | PASS | 586 | 0 | valid |
| 13 | 4 | PASS | 650 | 0 | valid |

So the **installer correctly applies every package's map** when invoked via the safe boundary — the
deep records 11/13 are reachable and correct. The whole-LUT checksum differs from natural only in
codes outside the package map (handoff residue) — outside the gate's contract.

### Survival: FAILS for the streamed-transition records → the STOP
Integrating the safe-call into the actual canonical gate (which verifies at install_frame **plus a
survival window**, one frame after the install) exposed the real problem:

- record 0 (stable epoch): verify_maps PASS **and survives** → case PASS.
- record 3 (rope transition): verify_maps PASS in the install frame, but **one arcade frame later
  `active_lut[0x034C]` is cleared 0x0420 → 0000** → case FAIL.

Root cause: the safe-call advances the **record** but not the **camera/scroll**. That leaves the
game inconsistent (record=3, camera still at record-0's position); the arcade's per-frame logic
corrects it, clearing the transient install. Natural gameplay advances record **and** camera in
lockstep (the rope column-45 handoff `fg_boundary_transition_step`), so record-3's LUT is stable
(0x0420 — opt003 proved it stable). My standalone sweep "passed" only because it sampled in the
exact install frame, before the arcade ran — a transient, not a surviving state.

### Conclusion — option (a) is not viable for surviving validation of the transition records
For the streamed-transition records (3 = rope, 4 = waterfall), the record↔camera coupling is
**essential inter-record gameplay semantics**: a subroutine call that advances only the record
cannot produce a state that survives, because the arcade actively reconciles record vs camera. This
is the prompt's explicit STOP condition. The safe boundary is clean and the install is correct, but
"survives subsequent normal frames" cannot be met for these records without camera-coupled
progression (i.e., natural scrolling).

The synthetic canonical gate is **left in place, reverted, unchanged** (I will not ship a gate that
validates a one-frame transient).

### New decision needed (Tighe)
1. **Hybrid:** natural scroll for the early transition records 3/4 (both reachable by scroll — record
   3 proven), safe-call for the stable records IF they survive (confirm 5/11/13 survive the window;
   0 already does). Deep stable records (11/13) still lack a proven surviving path.
2. **Same-ROM save-states** captured after *natural* progression through each record (needs a deep
   scripted/assisted playthrough to reach 11/13 once; regenerated per build/SHA).
3. **Redefine the gate contract** to validate the installer's per-package map application at the
   install boundary (transient verify_maps, which PASSES for all 6) and drop the survival
   requirement for records whose steady state is camera-coupled — a policy change for Tighe.

### STOP status (continuation 2)
**STOP** — safe boundary proven clean and the install proven correct for all 6 records, but the
survival requirement cannot be met for the streamed-transition records via any subroutine call
(record/camera coupling is essential). Canonical gate unchanged. Awaiting Tighe's decision among the
options above.
