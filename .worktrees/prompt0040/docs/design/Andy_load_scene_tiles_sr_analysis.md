# Andy — `load_scene_tiles` SR Violation Analysis

**Agent:** Andy
**Type:** Forensic Analysis + Design (no implementation)
**Build context:** Build 0050 `rastan-direct`
**Architecture compliance:** CONFIRMED (no source, spec, or tool modifications made by this task).

**Outcome:** the hypothesis is **confirmed** with **HIGH** confidence. `scene_load.s:91` (`move.w #0x2000, %sr`) unmasks all interrupts *inside* the `load_scene_tiles` helper, before the helper's `rts` at line 93. During Build 0050 cold boot this drops the CPU's IRQ mask from level 7 (set by `_start`) to level 0 while control is still inside `load_scene_tiles`, the VBlank L5 IRQ fires immediately, `_vblank_service` runs and tail-JMPs into the arcade L5 handler with `A5 = 0` (the `lea 0x00FF0000, %a5` at `boot.s:159` is unreached), and the A5=0 cascade documented in [Andy_a5_initialization_analysis.md](docs/design/Andy_a5_initialization_analysis.md) follows. The minimum correct production fix is **Option C** — save the caller's SR on entry, raise mask to level 7, restore SR exactly on exit — applied to `apps/rastan-direct/src/scene_load.s` only.

---

## Phase 1 — Trace linkage

All citations are to [Cody_a5_lifecycle_trace.md](docs/design/Cody_a5_lifecycle_trace.md) Phase 3 Table A (the checkpoint capture table).

| Claim | Cited row |
| --- | --- |
| At CP2 (entry to `jsr load_scene_tiles` at `runtime_genesis_pc 0x00000232`), SR interrupt mask was level 7. | **CP2 row: "SR at hit = 0x2714"**. The high nibble of the high byte is `0x7` → interrupt-mask field (bits 8-10) = `0b111` = level 7. |
| CP3 (`runtime_genesis_pc 0x00000238`, the `lea 0x00FF0000, %a5` immediately following the `jsr load_scene_tiles` return address) was not hit before CP8. | **CP3 row: "hit? = NO"**, "observed debugger PC = N/A". |
| CP8 (first `_vblank_service` entry at `runtime_genesis_pc 0x000700C2`) was hit with SR mask level 6 (auto-level set by 68000 on L5 IRQ entry). | **CP8 row: "SR at hit = 0x2600"**. Mask field = `0b110` = level 6, which is the 68000-auto value on L5 entry (IRQ level 5 + 1). |

**Inference chain:**

1. 68000 only pushes SR+PC and jumps to an IRQ vector when `IPL > current interrupt mask`. With L5 IRQ (IPL = 5), this requires `mask < 5` at the moment the IRQ is recognised.
2. At CP2 the mask was 7 (source above). At CP8 the mask was 6 (post-auto-level). The hardware cannot drop the mask itself; a software `move`/`ori`/`andi`/`rtr`/`rte` must reduce it before L5 can be taken.
3. Between CP2 and CP8, CP3–CP7 were **not hit** (source above). Execution therefore never returned from the `jsr load_scene_tiles` call back to `_bootstrap`'s instruction stream before L5 fired. The only code executing in that interval was `load_scene_tiles` itself (or a callee of `load_scene_tiles`, namely `vdp_set_reg` / `vdp_set_vram_write_addr`).
4. The only candidate callee, [vdp_comm.s](apps/rastan-direct/src/vdp_comm.s), does **not** write to SR (see Phase 5 audit table below). Therefore the SR write that enabled the IRQ must be inside `load_scene_tiles` itself.
5. The trace in [Cody_a5_lifecycle_trace.md](docs/design/Cody_a5_lifecycle_trace.md) Phase 3 "Trace evidence at IRQ entry point immediately before CP8" corroborates: `runtime_genesis_pc 0x071246: move #$2000, SR` immediately preceded the IRQ. That address is inside `load_scene_tiles` (the `.text` portion of `scene_load.s` was linked into the wrapper region starting at `0x00070000`; `0x071246` corresponds to `scene_load.s:91` per object-file layout).

```
Trace evidence that SR was at mask 7 at CP2:                [CP2 row of Table A → SR = 0x2714 → mask level 7]
Trace evidence that CP3 was not hit before CP8:             [CP3 row of Table A → hit? = NO]
Trace evidence that L5 fired while control was inside
  load_scene_tiles or at its return boundary:               [CP8 row SR = 0x2600 auto-level 6; CP3 not hit;
                                                             Phase 3 trace quote "0x071246: move #$2000, SR"
                                                             immediately before CP8]
Therefore: within load_scene_tiles, SR was written with a
  value whose interrupt mask is < 5 before the RTS:         YES
```

**No STOP.** Evidence is complete and unambiguous.

---

## Phase 2 — Source evidence

Exhaustive enumeration of SR/CCR/interrupt-mask-affecting instructions in [apps/rastan-direct/src/scene_load.s](apps/rastan-direct/src/scene_load.s), verified with:

```
grep -n '%sr\|%ccr\|\brtr\b\|\brte\b\|\bstop\b' apps/rastan-direct/src/scene_load.s
```

| line | instruction                   | SR value after                | interrupt mask after | reachable from `_bootstrap` call? |
| ---- | ----------------------------- | ------------------------------ | --------------------- | ---------------------------------- |
| 46   | `move.w #0x2700, %sr`         | `0x2700`                      | level 7 (all masked)  | YES — unconditional, on every call |
| 91   | `move.w #0x2000, %sr`         | `0x2000`                      | level 0 (all unmasked)| YES — unconditional, right before `movem.l` restore + `rts` |

No `andi.w #…, %sr`, no `ori.w #…, %sr`, no `eori.w #…, %sr`, no `move` to/from `%ccr`, no `rtr`, no `rte`, no `stop`, no `trap` inside `load_scene_tiles`.

### Instruction(s) that lower mask below 5 before the RTS

**Exactly one:** `scene_load.s:91 — move.w #0x2000, %sr`.

This is the preemption trigger. It forces the interrupt mask to level 0 — the **minimum** mask, unmasking every IRQ level including HINT (4) and VINT (6). At the instant that instruction executes, any pending VDP VBlank IRQ is recognised by the CPU; it pushes SR+PC (with SR = `0x2000` captured) and jumps to vector 29 (`_vblank_service`), with the auto-raised mask of 6.

The subsequent two instructions at `scene_load.s:92-93` (`movem.l (%sp)+, %d1-%d7/%a0-%a4` + `rts`) **never execute before the IRQ is taken**. The L5 handler's tail-JMP to arcade `0x3A208` then runs with `A5` never set (the `lea 0x00FF0000, %a5` at `boot.s:159` is only reached after `load_scene_tiles` returns).

```
SR-writing instructions in load_scene_tiles:  2 (lines 46 and 91)
Instruction(s) that lower mask below 5 before RTS:  1 — scene_load.s:91
Instruction identified as the preemption trigger:  scene_load.s:91 — `move.w #0x2000, %sr`
```

**Hypothesis confirmed.** No STOP.

---

## Phase 3 — RULES / ARCHITECTURE classification

Matrix of cited rules against the identified instruction and the helper's overall behaviour.

| # | Citation | Violated? | Why |
| - | -------- | --------- | --- |
| a | [RULES.md §1](RULES.md) "The arcade code is the program. There is no separate Genesis-owned game loop. ... Arcade code must run continuously and retain full control of execution." | **YES** | `scene_load.s:91` forces a state change (IRQ mask) on the caller's CPU context; that change is not something arcade code asked the helper to do. Even considered narrowly as "the helper changes CPU state the caller did not authorise", this violates the spirit of arcade ownership: CPU state that survives past `rts` should be exactly what the caller had at the call site, other than the helper's documented output. |
| b | [RULES.md §4](RULES.md) "Helper Functions Only — ... called by arcade code (JSR/JMP), performs a hardware translation or operation, returns immediately via RTS. Forbidden: loops, blocking, scheduling, control-flow ownership." | **YES** | Exiting with the interrupt mask set to 0 hands control-flow-scheduling back to the VDP: the next VBlank takes effect at the moment the helper sets mask 0, inside the helper, before the `rts`. This is helper-side interrupt scheduling — the helper is deciding when the next IRQ becomes deliverable, which is exactly the "control-flow ownership" the rule forbids. |
| c | [RULES.md §5](RULES.md) "No test code — every line must be production-intent." | **Partial — relevant to fix selection.** | `move.w #0x2000, %sr` in a helper is functionally "resume-interrupts-on-exit" scaffolding for a caller that had them disabled. A production helper preserves caller state instead. |
| d | [RULES.md §7](RULES.md) "No Hidden State Machines — no restart paths, no safe re-entry." | **NO (strict reading)** | This specific instruction is not introducing a state machine; it is one write. Listed for completeness. |
| e | [ARCHITECTURE.md Helper Functions](ARCHITECTURE.md) "Must not loop, block, own control flow." | **YES** | Owning the moment at which IRQs become deliverable is owning control flow at the IRQ-timing level. |
| f | [ARCHITECTURE.md Frame Ownership](ARCHITECTURE.md) "Single owner: Arcade level-5 vblank." | **YES, indirectly** | By controlling when the L5 IRQ is first taken, the helper is effectively gating the arcade L5 handler's first invocation — it decides when the arcade VBlank cycle begins running. That gating belongs to arcade code's own enable-IRQ sequencing (which would be later in `arcade_pc 0x3AF04`+ if the helper did not pre-empt), not to a tile-DMA helper. |
| g | [PROMPT_TEMPLATE.md CONTROL FLOW INVARIANT](PROMPT_TEMPLATE.md) "Any control transfer that does not return directly to arcade flow via RTS is a violation." | **YES** | The intended control transfer out of `load_scene_tiles` is `rts`. The actual observed transfer out of `load_scene_tiles` at cold boot is **IRQ → vector 29 → `_vblank_service` → tail-JMP to arcade `0x3A208`**, which never reaches the helper's `rts` and never returns to the caller (`_bootstrap`). By literal reading of the invariant, `load_scene_tiles` currently exits via an IRQ redirection, not via `rts`. |

### Concise why

`scene_load.s:91` is helper-side interrupt enablement: the helper unconditionally drops the CPU's IRQ mask to 0 on its way out, which (i) mutates caller-owned SR state without authorisation, (ii) schedules the next IRQ to fire before the helper's own `rts` completes, and (iii) cedes control-flow ownership to the VBlank vector. That is precisely the kind of helper-side control-flow behaviour RULES.md §4 and the ARCHITECTURE.md "Helper Functions" section exist to forbid.

```
RULES/ARCHITECTURE violation: YES
Rule(s) implicated: RULES.md §1, §4, §5 (partial); ARCHITECTURE.md "Helper Functions" and "Frame Ownership"; PROMPT_TEMPLATE.md "CONTROL FLOW INVARIANT".
Why: the helper unconditionally writes to SR such that the interrupt mask
drops below the incoming IRQ level, which schedules the next VBlank IRQ to
be taken inside the helper before its RTS. That is helper-side interrupt
scheduling — i.e. helper-side control-flow ownership — and it also mutates
caller-owned CPU state (SR mask) that the caller did not authorise.
```

---

## Phase 4 — Fix scope decision

### Callers of `load_scene_tiles` in the current source tree

Verified with `grep -rn 'load_scene_tiles' apps/rastan-direct/src/`:

| file:line                        | kind | context |
| -------------------------------- | ---- | ------- |
| `apps/rastan-direct/src/boot/boot.s:6` | `.extern` | declaration only |
| `apps/rastan-direct/src/boot/boot.s:158` | `jsr` | cold-boot call from `_bootstrap`. Caller SR at call site has mask = 7 (`_start` set `0x2700`; nothing between changes it). |
| `apps/rastan-direct/src/scene_load.s:3` | `.global` | declaration only |
| `apps/rastan-direct/src/scene_load.s:27` | label definition | — |
| `apps/rastan-direct/src/tilemap_hooks.s:108` | `bsr` | inside `genesistan_hook_tilemap_plane_a` scene-transition preamble; called from arcade via the `opcode_replace` at `arcade_pc 0x055968`. Caller SR at call site = arcade L5 handler mask 7 (the arcade handler at `arcade_pc 0x3A008` starts with `ORI.W #0x0F00, SR`). |
| `apps/rastan-direct/src/tilemap_hooks.s:280` | `bsr` | inside `genesistan_hook_tilemap_fg` scene-transition preamble; called from arcade via the `opcode_replace` at `arcade_pc 0x055990`. Same caller SR context as above. |

**All three callers invoke `load_scene_tiles` with the IRQ mask at level 7 at the call site.** None of them want or expect the helper to unmask IRQs on exit.

### Option evaluations

| Option | Fixes the active bug? | Complies with §4 / Helper-Functions? | Protects VDP write loop at scene_load.s:52-73 from IRQ interference? | Minimum scope (source lines affected) | Risk (behaviour change for other callers) |
| ------ | --------------------- | ------------------------------------ | -------------------------------------------------------------------- | -------------------------------------- | ------------------------------------------- |
| A — delete `scene_load.s:91` only | YES (removes the drop to mask 0) | **NO.** Still leaves line 46's `move.w #0x2700` in place, which masks at entry but the helper now exits with mask = 7 instead of restoring caller's mask. This alters caller SR on exit in a different direction. For the arcade-hook callers that are (correctly) **also** at mask 7 on entry, the behaviour happens to match; for any future caller at mask ≤ 4, the helper would mask IRQs on return without the caller's consent. | YES | 1 line deleted | Medium — exit mask becomes 7 unconditionally; fine for the three current callers (all at mask 7) but fragile for any future caller. |
| B — delete both `scene_load.s:46` and `scene_load.s:91` | YES (no SR writes means no mask drop) | **Partial.** Caller's SR is perfectly preserved (no helper writes to SR at all). But the helper no longer protects itself from IRQ interference during the VDP write loop. | **NO.** With arcade-main-loop context (mask < 5) an incoming VBlank could interrupt `vdp_set_vram_write_addr` or the tile-word loop mid-command, corrupt the VDP `ctrl`-latched address, and `_vblank_service` inside the IRQ would then issue its own VDP writes from that latched-but-wrong state. | 2 lines deleted | Medium-high — correctness depends on every caller having mask ≥ 6 at the call site; currently true, but brittle. |
| C — save caller SR on entry, raise mask to 7, restore caller SR on exit | YES (mask stays ≥ 7 throughout; never drops before rts) | **YES.** Caller's SR is preserved to the bit. Helper explicitly protects its own critical section. Standard 68000 helper convention. | YES | 2 existing lines replaced with 3 instructions (net +1 line) | None — every current caller sees their own SR preserved; none observes a behaviour change. |
| D — Other | — | — | — | — | — |

### Recommended option: **C**

**Recommended option's minimum source scope:**

```
File: apps/rastan-direct/src/scene_load.s
Edit 1 (replacement of line 46):
  Before:   move.w  #0x2700, %sr
  After:    move.w  %sr, -(%sp)
            ori.w   #0x0700, %sr
Edit 2 (replacement of line 91):
  Before:   move.w  #0x2000, %sr
  After:    move.w  (%sp)+, %sr
```

No other file changes. No spec change. No tool change.

**Why `ori.w #0x0700, %sr` rather than `move.w #<literal>, %sr`:** `ori.w` preserves the S/T/CCR bits of the caller's SR; only the interrupt-mask field is raised to level 7. Together with the push-of-SR on entry and pop-of-SR on exit, the helper leaves caller SR bit-for-bit identical after `rts`.

**Why the push/pop pair rather than a single inline set/clear:** a single set-then-clear pair would require the helper to know the caller's original SR value, which it does not. The push/pop pair makes the helper oblivious to the caller's SR while guaranteeing perfect preservation.

### Caller-compatibility check

```
Callers of load_scene_tiles in current source:
  - apps/rastan-direct/src/boot/boot.s:158      (`jsr`, mask-7 caller)
  - apps/rastan-direct/src/tilemap_hooks.s:108  (`bsr`, mask-7 caller)
  - apps/rastan-direct/src/tilemap_hooks.s:280  (`bsr`, mask-7 caller)

Does the recommended fix preserve behaviour for all current callers:  YES

Behaviour under Option C per caller:
  boot.s:158              entry SR=0x2700 → exit SR=0x2700; boot.s:159 `lea …,%a5`
                          runs next with IRQ still masked; boot.s:160 explicitly
                          enables IRQs (`move.w #0x2000, %sr`) right before
                          `jmp (0x3A200).l`. First L5 VBlank cannot fire until
                          boot.s:160 lowers the mask → A5 is already set → handler
                          reads real arcade workram.
  tilemap_hooks.s:108/280 both sites are inside arcade L5 handler context (mask 7);
                          entry SR mask=7 → exit mask=7; arcade L5 handler continues
                          with its own IRQ masking unchanged. Scene-transition
                          tile upload still protected.
```

**Confidence:** **HIGH.**

**Justification (one paragraph):** the trace pinpoints exactly one SR-writing instruction (`scene_load.s:91`) as the preemption trigger; the only other SR write in the helper (line 46) has the same save/restore defect in miniature; all three callers of `load_scene_tiles` share an identical pre-existing SR state (mask 7); Option C eliminates the defect class — helper no longer writes caller-visible SR — and simultaneously preserves the helper's own protection of its VDP critical section. Options A and B each leave one half of the defect unresolved (A still overwrites caller mask on exit via the path where line 46 sets mask 7 and line 91 is gone; B removes protection of the VDP write loop). Option C is the standard 68000 supervisor-mode helper pattern for this situation and is both correct and minimal for the observed fault.

---

## Phase 5 — Audit of other Phase B helpers

### Method

```
grep -n '%sr\|%ccr\|\brtr\b\|\brte\b\|\bstop\b\|\btrap\b' \
    apps/rastan-direct/src/boot/boot.s \
    apps/rastan-direct/src/vdp_comm.s \
    apps/rastan-direct/src/tilemap_hooks.s \
    apps/rastan-direct/src/crash_handler.s \
    apps/rastan-direct/src/sound/sound_comm.s \
    apps/rastan-direct/src/sound/z80_driver.s \
    apps/rastan-direct/src/scene_load.s
```

### Findings

| file | function | touches SR? | instruction(s) | architectural verdict |
| ---- | -------- | ----------- | -------------- | --------------------- |
| `apps/rastan-direct/src/boot/boot.s` | `_boot_guard_legacy_rte` | — (isolated) | line 140: `rte` | **Legitimate.** Padding/guard symbol; [apps/rastan-direct/src/boot/boot.s:138-140](apps/rastan-direct/src/boot/boot.s#L138-L140) placed at `0x00000200` to satisfy the `verify_rastan_direct_boot_guard.py` invariant; not invoked from any normal control-flow path. |
| `apps/rastan-direct/src/boot/boot.s` | `_start` | YES | line 143: `move.w #0x2700, %sr` | **Legitimate — boot owner.** `_start` is the 68000 reset vector target; it legitimately owns CPU state at reset and sets mask 7 as the first instruction. |
| `apps/rastan-direct/src/boot/boot.s` | `_bootstrap` | YES | line 160: `move.w #0x2000, %sr` | **Legitimate — boot owner, documented handoff.** Intentional IRQ enable immediately before `jmp (0x3A200).l` to hand control to arcade code. Not a helper. |
| `apps/rastan-direct/src/boot/boot.s` | `_bootstrap_clear_staging` | NO | — | Clean helper — does not touch SR. |
| `apps/rastan-direct/src/vdp_comm.s` | `vdp_boot_setup` | NO | — | Clean helper — only VDP writes, no SR. |
| `apps/rastan-direct/src/vdp_comm.s` | `vdp_set_reg` | NO | — | Clean helper. |
| `apps/rastan-direct/src/vdp_comm.s` | `vdp_set_vram_write_addr` | NO | — | Clean helper. |
| `apps/rastan-direct/src/vdp_comm.s` | `sprite_dma_addr_high_bits_fix` | NO | — | Clean helper. |
| `apps/rastan-direct/src/vdp_comm.s` | `_vblank_service` | NO | — | **Special case — correct.** Entry is via 68000 auto-vector (vector 29 at interrupt time); the hardware pushes SR+PC and raises the mask to 6 automatically. Body is `movem.l` save, VDP-commit `bsr`s, conditional palette commit, `movem.l` restore, `jmp (0x3A208).l` to arcade L5. Arcade L5 ends with its own `rte` at `arcade_pc 0x3A07E` which pops the auto-saved SR. `_vblank_service` itself writes SR zero times — **confirmed**. |
| `apps/rastan-direct/src/vdp_comm.s` | `vdp_commit_tiles_if_dirty` | NO | — | Clean helper. |
| `apps/rastan-direct/src/vdp_comm.s` | `vdp_commit_bg_strips_if_dirty` | NO | — | Clean helper. |
| `apps/rastan-direct/src/vdp_comm.s` | `vdp_commit_fg_strips_if_dirty` | NO | — | Clean helper. |
| `apps/rastan-direct/src/vdp_comm.s` | `vdp_commit_palette` | NO | — | Clean helper. |
| `apps/rastan-direct/src/vdp_comm.s` | `vdp_commit_scroll` | NO | — | Clean helper. |
| `apps/rastan-direct/src/tilemap_hooks.s` | every hook (`genesistan_hook_*`) | NO | — | `grep` for SR/CCR/RTR/RTE/STOP/TRAP on [apps/rastan-direct/src/tilemap_hooks.s](apps/rastan-direct/src/tilemap_hooks.s) returns **no matches**. All hooks are clean helpers. |
| `apps/rastan-direct/src/crash_handler.s` | `_crash_common` | YES | line 180: `move.w #0x2700, %sr` | **Legitimate — fault handler.** The crash path owns CPU state by design (it is about to halt); masking all IRQs to level 7 before rendering the crash screen is correct. |
| `apps/rastan-direct/src/crash_handler.s` | crash halt | YES | line 262, 266: `stop #0x2700` | **Legitimate — halt.** Terminal halt of the CPU. |
| `apps/rastan-direct/src/crash_handler.s` | all crash stubs / renderer helpers | NO | — | Clean. |
| `apps/rastan-direct/src/sound/sound_comm.s` | every function | NO | — | `grep` returns **no matches**. Clean. |
| `apps/rastan-direct/src/sound/z80_driver.s` | every function | NO | — | `grep` returns **no matches**. Clean. |
| `apps/rastan-direct/src/scene_load.s` | `load_scene_tiles` | **YES** | **lines 46, 91** | **VIOLATION — subject of this prompt.** |

### `_vblank_service` special-case confirmation

`grep -n '%sr\|%ccr\|\brtr\b\|\brte\b\|\bstop\b' apps/rastan-direct/src/vdp_comm.s` returns **no matches** across the full file. `_vblank_service` at `vdp_comm.s:155-179` itself contains only `movem.l`, `moveq`, `bsr`, `tst.b`, `beq.s`, `clr.b`, and `jmp`. No SR writes. **Confirmed.**

### Additional SR-touching helpers outside scene_load.s

**NONE.** The audit finds **no other** user-callable helper in the Phase B tree that writes SR. Every SR-touching instruction outside `scene_load.s` belongs either to `_start` / `_bootstrap` (boot owners) or to the crash handler (fault owner). Both roles legitimately own CPU state; neither is a "helper called by arcade code" in the RULES.md §4 sense.

No separate Andy prompts required for other helpers at this time.

---

## STOP conditions — not triggered

- Phase 1 established from trace evidence that L5 fired before CP3 (HIGH-confidence chain above).
- Phase 2 identified exactly one SR-writing instruction (`scene_load.s:91`) that lowers the mask below 5 before `rts`.
- Phase 3 has a clean rule-violation citation chain.
- Phase 4 evaluated all four option classes and selected Option C with HIGH confidence.
- Phase 5 audit returned clean results for every other helper.

---

## Summary

- Trace linkage (Phase 1): CP2 SR=0x2714 → CP3 NOT hit → CP8 SR=0x2600 → L5 fired inside `load_scene_tiles`.
- Source evidence (Phase 2): exactly one SR write lowers mask below 5 before `rts` — `scene_load.s:91` `move.w #0x2000, %sr`.
- Classification (Phase 3): VIOLATION. Helper-side interrupt scheduling. Cited rules: RULES.md §1, §4, §5; ARCHITECTURE.md "Helper Functions" + "Frame Ownership"; PROMPT_TEMPLATE.md control-flow invariant.
- Fix (Phase 4): **Option C** — save `%sr` on entry, `ori.w #0x0700, %sr`, restore `%sr` on exit. Single file: `apps/rastan-direct/src/scene_load.s`. Lines 46 and 91 replaced. All three callers (boot.s:158, tilemap_hooks.s:108/280) preserved. **Confidence: HIGH.**
- Audit (Phase 5): no other SR-touching helpers found in Phase B source tree. `_vblank_service` confirmed zero SR writes.

---

## Appendix — final response summary

```
Trace evidence that SR was at mask 7 at CP2:  CP2 row of Table A in Cody_a5_lifecycle_trace.md — SR = 0x2714 → mask 7.
Trace evidence that CP3 was not hit before CP8:  CP3 row of Table A — hit? = NO.
Trace evidence that L5 fired while control was inside load_scene_tiles or at its return boundary:  CP8 row SR = 0x2600 (auto-mask 6 on L5 entry); CP3 not hit; Phase 3 trace quote "0x071246: move #$2000, SR" immediately before CP8 → that is scene_load.s:91 in the linked wrapper.
Therefore: within load_scene_tiles, SR was written with a value whose interrupt mask is < 5 before the RTS:  YES

SR-writing instructions in load_scene_tiles:  2 — scene_load.s:46 (`move.w #0x2700, %sr`) and scene_load.s:91 (`move.w #0x2000, %sr`).
Instruction(s) that lower mask below 5 before RTS:  scene_load.s:91.
Instruction identified as the preemption trigger:  scene_load.s:91 — `move.w #0x2000, %sr`.

RULES/ARCHITECTURE violation:  YES.
Rule(s) implicated:  RULES.md §1, §4, §5 (partial); ARCHITECTURE.md "Helper Functions", "Frame Ownership"; PROMPT_TEMPLATE.md control-flow invariant.
Why:  the helper writes caller-owned SR (line 91) such that the IRQ mask drops below the pending L5 level before the helper's rts, handing control-flow scheduling to the VBlank vector inside the helper.

Option evaluations:
  A — deletes line 91; leaves line 46. Fixes active bug but exits with caller-overwritten mask 7. Still partially violates §4.
  B — deletes both lines 46 and 91. Preserves caller SR but removes VDP critical-section protection.
  C — save/raise/restore via push SR, ori.w #0x0700 %sr, pop SR. Fixes bug; preserves caller SR exactly; retains VDP protection. Standard 68000 helper convention.
  D — n/a.
Recommended option:  C.
Recommended option's minimum source scope:
  File: apps/rastan-direct/src/scene_load.s
  Line 46 replaced:  `move.w #0x2700, %sr`  →  `move.w %sr, -(%sp)` + `ori.w #0x0700, %sr`
  Line 91 replaced:  `move.w #0x2000, %sr`  →  `move.w (%sp)+, %sr`
Confidence:  HIGH.
Callers of load_scene_tiles in current source:
  apps/rastan-direct/src/boot/boot.s:158 (jsr, mask-7 caller)
  apps/rastan-direct/src/tilemap_hooks.s:108 (bsr, mask-7 caller)
  apps/rastan-direct/src/tilemap_hooks.s:280 (bsr, mask-7 caller)
Does the recommended fix preserve behaviour for all current callers:  YES.

Other Phase B helpers touching SR:  NONE (besides boot owners _start/_bootstrap and crash handler, all legitimate).
_vblank_service writes SR:  NO (68000 hardware manages SR on IRQ entry/exit).
STOP triggered:  NO.
```
