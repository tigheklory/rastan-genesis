# Andy — Locate Intended Call Site for Input-Poll Shim 0x710ca, Build 0077

**Author:** Andy
**Date:** 2026-06-14
**Build:** 0077 (canonical baseline SHA `72f9f33dac332d7fb6294799f936714cc4aa4c320f63baf35000adabc0c7e7cc`)
**Scope:** STATIC analysis only, bounded to the call site for `0x710ca` (`rastan_direct_update_inputs`). Documentation-only. No source/spec/tool/Makefile/ROM modifications. No bookmark cycle. No implementation/instrument design.

Genesis runtime PC = ROM file offset (KF-004); arcade-source = Genesis − 0x200 (KF-006).

---

## Phase 0 — Baseline statement

**Classification:** EXTENDING KF-028. **Phase 0 STOP:** not triggered; no CONFIRMED/STRONG contradiction.

**Relevant priors:** KF-003 (chain; HIGH), KF-004 (runtime PC = ROM offset; HIGH), KF-008 (WRAM split), KF-011 (frame ownership: arcade Level-5 VBlank owns progression, Genesis VBlank servicing-only; HIGH), KF-013 (text dispatch inside VBlank handler), KF-022 (TC0040IOC active-low), KF-028 (input mirror `0xff60fc..0xff6100` unpopulated; shim `0x710ca` unreferenced; HIGH). HIGH-hazard touched: KF-003, KF-004, KF-011, KF-028. None contradicted.

**Open issues touched:** OPEN-001, OPEN-004 (context only; no status change).

---

## §0 — Smallest proven statement

**Proven prior:** KF-028 — `0x710ca` has zero direct references; the shim, if invoked, writes the correct active-low bit-2 idle value; the arcade has no software shim (hardware provides values); Genesis lacks the TC0040IOC hardware; KF-011 frame ownership.

**NOT proven:** that the shim was ever called in any prior build; that the correct call site is uniquely determined by static analysis; that a regression specifically dropped a `jsr 0x710ca`; that `_vblank_service` is the intended invocation point (candidate, established below).

---

## Phase 1 — Arcade input-polling architecture

Full-file grep of TC0040IOC ports (`0x390001/3/5/7/9/b`) in `build/maincpu.disasm.txt` shows reads **scattered inline at consumer sites**, not clustered in a dedicated routine:
- `0x124`, `0x3a6`, `0x3f4`, `0x438`, `0x47c`, `0x48e`, `0x5cc`, `0x5f6`, `0x612`, `0x644` (early/boot), and in the VBlank/state region `0x3a0a8`, `0x3a490`, `0x3a4a2`, `0x3a4a8`, `0x3a778`, `0x3a7b8`, `0x3a91a`, `0x3ab96`, `0x3ac04`, `0x3ac94`, `0x3acb2`, `0x3acfe`, `0x3ad1c`, `0x3af7a`, `0x3af86`.

**There is no arcade "controller-poll" routine.** Each consumer reads the hardware port directly (e.g. `0x3a490: moveb 0x390007,%d0` then `andib`/`btst` inline). **STATICALLY_PROVEN.**

**Consequence:** the Genesis shim `0x710ca` has **no arcade counterpart routine**. It is a Genesis-*introduced* consolidation: poll the controllers once, write the WRAM shadows (`genesistan_shadow_input_390001..390007`), and let the translated inline reads read the shadows instead of nonexistent hardware. Therefore the shim's call site is **not** derivable as "arcade `jsr X` → Genesis `jsr X+0x200`"; there was never an arcade call to translate. **INFERRED (from the inline-read architecture).**

---

## Phase 2 — Genesis per-frame path: symbol identity and candidates

**Symbol table (`apps/rastan-direct/out/symbol.txt`) resolves the actors — STATICALLY_PROVEN:**
- `000710ca T rastan_direct_update_inputs` — the shim is the exported function `rastan_direct_update_inputs` (`tilemap_hooks.s:1598`).
- `00ff60fc B genesistan_shadow_input_390001`, `00ff60fd …390003`, `00ff60fe …390005`, `00ff60ff B genesistan_shadow_input_390007` — confirming `0xff60ff` is the shadow of arcade port `0x390007` (and the gate at `0x3ad96` reads `genesistan_shadow_input_390007`).

**Caller search — STATICALLY_PROVEN:** `rastan_direct_update_inputs` appears in source only twice: the `.global` export (`tilemap_hooks.s:17`) and the label definition (`tilemap_hooks.s:1598`). **No `jsr`/`bsr`/`jmp` to it in any source file**, matching KF-028's disassembly-level result. The function is implemented and exported but never invoked.

**The per-frame service is `_vblank_service`** (`vdp_comm.s:156`), installed in the Level-6 vector (`boot.s:92 .long _vblank_service`), = runtime `0x700c2`. Its body (`vdp_comm.s:156-181`):
```
_vblank_service:
  movem.l %d0-%d7/%a0-%a6,-(%sp)        ; save all
  vdp_set_reg MODE2 DISPLAY_OFF
  bsr vdp_commit_tiles_if_dirty
  bsr vdp_commit_bg_strips_if_dirty
  bsr vdp_commit_fg_strips_if_dirty
  bsr vdp_commit_sprites
  (palette dirty? bsr vdp_commit_palette)
  bsr vdp_commit_scroll
  vdp_set_reg MODE2 DISPLAY_ON
  movem.l (%sp)+,%d0-%d7/%a0-%a6        ; restore all
  jmp (0x00003A208).l                  ; hand off to ARCADE VBlank handler
```
This matches the disassembled `0x700c2` chain exactly (commits → display on → `jmp 0x3a208`). The arcade VBlank handler reached by line 181 is what consumes the input shadows (gate `0x3ad96` + state-handler reads). **STATICALLY_PROVEN.**

**Candidate evaluation:**
- **`_vblank_service` (`0x700c2`)** — runs every VBlank immediately before handing to the arcade handler that consumes the shadows. Natural and correct site. No input call present; no NOP/padding/stub gap in the sequence.
- The `0x70100 jmp 0x3a208` handoff is the last instruction; any input refresh must precede it.
- The arcade VBlank handler entry `0x3a208`/prologue — could host the call, but it is arcade-translated code; the shim is Genesis-native, so the Genesis service is the architecturally appropriate host (KF-011 servicing-only).
- No arcade poll routine exists (Phase 1), so there is no `X+0x200` Genesis location to audit.

**Register-safety note (supporting):** `rastan_direct_update_inputs` clobbers `d0-d7`/address regs and does not save them itself, but `_vblank_service` already brackets its body with `movem.l %d0-%d7/%a0-%a6` save/restore (lines 157/180). A call placed inside that bracket is register-safe. **STATICALLY_PROVEN.**

---

## Phase 3 — Dropped-vs-never-wired analysis

**Indicators present for NEVER-WIRED:**
- The shim is a Genesis architectural addition with **no arcade counterpart call** to translate (Phase 1).
- `rastan_direct_update_inputs` is `.global`-exported (intent to be called from another translation unit) yet has **zero callers in any source file** (Phase 2).
- `_vblank_service` is a **clean, complete sequence** — every instruction has a purpose; there is **no NOP sled, padding, or stub call** where a `bsr rastan_direct_update_inputs` would have been removed.
- Signature matches "implemented and exported but never wired into the frame path" (incomplete port), not "call removed leaving a hole" (regression).

**Indicators for DROPPED:** none structurally. The `.global` export shows *intent* to call, which is equally consistent with never-finished wiring.

**Determination: NEVER-WIRED.** **INFERRED (strongly supported).** Caveat: git history was not consulted (out of static-analysis scope); a `git blame`/log on `vdp_comm.s` and `tilemap_hooks.s` could fully exclude a removed caller. Static evidence (no hole, `.global` with no caller, no arcade counterpart) strongly favors never-wired.

---

## Phase 4 — Outcome classification

### Outcome: **B — Never-wired location identified.**

**Recommended call site:** `bsr rastan_direct_update_inputs` inside **`_vblank_service`** (`vdp_comm.s`), placed **at the top of the service body — immediately after the `movem.l … -(%sp)` save at line 157, before the display-off / commit sequence** (Genesis runtime: within `0x700c2`, before the `0x70100 jmp 0x3a208`). Any point before line 181 is functionally sufficient; the top is cleanest (inputs refreshed first, inside the existing register-save bracket).

**Architectural justification (INFERRED):**
- `_vblank_service` is the per-frame Genesis servicing entry (Level-6 vector, `boot.s:92`) and runs every VBlank immediately before `jmp 0x3a208` hands control to the arcade VBlank handler.
- That arcade handler is the consumer of the input shadows — the state-3 gate reads `genesistan_shadow_input_390007` (`0xff60ff`) at `0x3ad96`, and other state handlers read the sibling shadows — all dispatched from the handler reached at line 181.
- Refreshing the shadows at the top of `_vblank_service` guarantees valid input state before consumption, each frame, consistent with KF-011 (Genesis VBlank is servicing-only; this is hardware-input servicing, not gameplay logic).

**Why never-wired (not dropped):** no structural drop indicator; `.global` export with no caller in any unit; no arcade counterpart call. (INFERRED; git history would confirm.)

**Recommended Cody fix SCOPE (recommendation only — Andy does not draft code):** add a single `bsr rastan_direct_update_inputs` at the top of `_vblank_service` in `vdp_comm.s`. This wires the existing, correct shim into the per-frame path; no change to the shim itself. After the fix, re-run a reachability check on `0x0003ABFE` (title dispatcher) to confirm the master state stays 0 and the title path is reached. Targets OPEN-004; likely unblocks OPEN-001 downstream.

---

## Phase 5 — KNOWN_FINDINGS impact

**Option C — proposed minimal refinement to KF-028** (Cody applies after Tighe ack; Andy does not edit `KNOWN_FINDINGS.md`). KF-028 already canonizes "the mirror is unpopulated until the `0x710ca` shim is wired in"; this task completes that pointer with the intended caller. Proposed addition to KF-028 **Use as prior**:

> The shim is `rastan_direct_update_inputs` (`tilemap_hooks.s:1598`), `.global`-exported but called by nothing. Its intended caller is the per-frame Genesis VBlank service `_vblank_service` (`vdp_comm.s:156`, runtime `0x700c2`), before its `jmp 0x3a208` handoff to the arcade VBlank handler that consumes the shadows. The arcade has no controller-poll routine (inline port reads), so the shim has no arcade-counterpart call site — its absence is a never-wired Genesis-side gap, not a translated-routine regression.

Justification: the intended call site is non-obvious (requires knowing the shim has no arcade counterpart and that consumption happens in the arcade handler reached from `_vblank_service`); recording it prevents a future agent re-deriving this. No new mechanism beyond KF-028 — hence a refinement, not a new entry.

---

## Recommended next task

Cody implementation (recommendation): **add `bsr rastan_direct_update_inputs` at the top of `_vblank_service` (`vdp_comm.s`, after the `movem.l` save)**, then rebuild and re-run a reachability check on `0x0003ABFE`. If the title dispatcher is now reached (master state stays 0), the input-mirror wiring gap is confirmed fixed and OPEN-004 progresses. Optionally precede with a one-line `git log`/`blame` check on `vdp_comm.s` to confirm never-wired vs dropped (low effort, completes Phase 3).

---

## Open / Closed Issues Impact

- Open issues touched: OPEN-001, OPEN-004 (context; fix site for the input-mirror gap localized; no status change pending implementation + verification).
- Closed issues touched: NONE. New issues opened: NONE. Issues closed: NONE. Deferred: NONE.

## STOP triggered

NO.
