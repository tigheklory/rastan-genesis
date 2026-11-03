# Andy — Build 0092 Single VBlank Lifecycle Placement Audit

**Author:** Andy
**Date:** 2026-06-21
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0092.bin` (SHA `4cc782854a40ccf3333ec8ecbe40f71a7617201576c124b60b49e5008fdd20e2`)
**Scope:** Static analysis only. No source/spec/tool/Makefile/ROM modifications. No build. No runtime probing. No bookmark cycle. No fix. Bounded recommendation only.

Address labels (Rule 3): `runtime_genesis_pc` = patched-ROM offset / runtime PC; `HW` = hardware; `WRAM` = Genesis work RAM. Single-lifecycle framing throughout: one arcade-controlled VBlank lifecycle; the hardware interrupt is the physical source.

---

## Phase 0 — Baseline statement

**Relevant priors:** KF-028 (input shim / title-text; OPEN-016 Part 2 landed in Build 0092), KF-013 (text/producer dispatch runs inside the VBlank handler), KF-011 (arcade VBlank routine owns frame progression), KF-010 (FG→Plane A `0xE000`, BG→Plane B `0xC000`), KF-004/006 (PC↔offset, identity 0x200), KF-001 (watchdog — context, no VDP writes).

**Rediscovery-Hazard HIGH touched:** KF-028, KF-013, KF-011, KF-010 — none contradicted.

**Task classification:** EXTENDING (tests whether Cody's `0x70100` Layer-1 sample point is valid).

**Open/Closed issues touched:** OPEN-001 (active — missing title screen), OPEN-016 (active — may inform Part 3 direction), OPEN-015 (context).

**Contradiction detected:** NO.

**Architecture compliance:** CONFIRMED. Audit treats the lifecycle as single and arcade-controlled; classifies evidentially.

---

## Phase 1 — The single VBlank lifecycle (Build 0092)

Hardware Level-6 interrupt → vector at `.data` offset `0x78` = `0x000700C2` (`boot.s` installs `_vblank_service` on the Level-6 vector). The lifecycle, in execution order (`build/genesis_postpatch.disasm.txt`, `vdp_comm.s`):

| # | runtime_genesis_pc | Operation | Evidence |
|---|---|---|---|
| 1 | `0x700C2` | `movem.l %d0-%fp,-(%sp)` save | STATICALLY_PROVEN |
| 2 | `0x700C6` | `bsr 0x710CE` = `rastan_direct_update_inputs` (**input mirror update**, `0xff60xx`) | STATICALLY_PROVEN (KF-028) |
| 3 | `0x700CA-CE` | `vdp_set_reg` MODE2 **DISPLAY OFF** (`0x34`) | STATICALLY_PROVEN |
| 4 | `0x700CE→0x7010A` | `vdp_commit_tiles_if_dirty` (gated `tiles_dirty`) | STATICALLY_PROVEN |
| 5 | `0x700D2→0x70134` | `vdp_commit_bg_strips_if_dirty` (gated `bg_row_dirty`) | STATICALLY_PROVEN |
| 6 | `0x700D6→0x70182` | `vdp_commit_fg_strips_if_dirty` (gated `fg_row_dirty`) | STATICALLY_PROVEN |
| 7 | `0x700DA→0x719B4` | `vdp_commit_sprites` | STATICALLY_PROVEN |
| 8 | `0x700DE-EE` | `palette_dirty?` → `vdp_commit_palette`; `clr.b 0xff4000` | STATICALLY_PROVEN |
| 9 | `0x700F4→0x701F0` | `vdp_commit_scroll` | STATICALLY_PROVEN |
| 10 | `0x700F8-FC` | `vdp_set_reg` MODE2 **DISPLAY ON** (`0x74`) | STATICALLY_PROVEN |
| 11 | **`0x70100`** | `movem.l (%sp)+,%d0-%fp` restore | STATICALLY_PROVEN |
| 12 | `0x70104` | `jmp 0x3A208` → **arcade VBlank routine** | STATICALLY_PROVEN |
| 13 | `0x3A208…` | arcade VBlank body: SR mask, sub-calls, **master dispatch on `%a5@(0)` at `0x3A256`** → title sub-state handler (`0x3ABFE…`) → **title producers** (glyph renderer `0x3BD48` + hooks) write `staged_fg/bg_buffer` | STATICALLY_PROVEN (KF-013) |
| 14 | `0x3A27E` | `andiw #-3841,%sr`; `rte` (lifecycle ends) | STATICALLY_PROVEN |

**Key ordering fact (STATICALLY_PROVEN):** within one lifecycle, the **commits (steps 4-9) run BEFORE the arcade producers (step 13)**. This is the standard **deferred-commit** pattern: at VBlank start (display blanked), commit the staging populated by the *previous* lifecycle's producers, then run *this* lifecycle's producers to populate staging for the *next* commit. Input mirror update (step 2) correctly precedes the producer body (step 13), so the arcade code reads fresh input.

**Second key fact (STATICALLY_PROVEN):** the commit routines do **not** clear staging. `vdp_commit_bg/fg_strips_if_dirty` read `staged_bg/fg_buffer` into `VDP_DATA` and clear only the dirty flag (`bclr %d5,%d0` → `bg_row_dirty`/`fg_row_dirty`); they never zero the staged buffer. `vdp_commit_tiles_if_dirty` clears `tiles_dirty`, not `staged_tile_words`. So **staged content persists across frames** until a producer overwrites it.

---

## Phase 2 — Location of `0x70100` in the lifecycle

`0x70100` is step 11 — the register-restore immediately before `jmp 0x3A208` (Cody's description "end of `_vblank_service`, immediately before handoff to arcade VBlank at `0x3A208`" is **verified correct**). Relative to the lifecycle:
- **After** all commits (steps 4-9) and **after** the display-on toggle (step 10).
- **After** the dirty-flag clears performed by the commits.
- **Before** the arcade VBlank body (step 13) that runs **this** lifecycle's title producers.

So at `0x70100` of lifecycle N, the producers of lifecycle N have **not** run. Staging holds whatever lifecycle N-1's producers left — and because the commit does **not** clear staging (Phase 1), that content **persists** through lifecycle N's commit.

---

## At `0x70100`, should staged BG/FG content exist? — **YES (in steady state)**

In the stable no-input title state, every lifecycle's producers should write the same title cells. Producers run in step 13 of each lifecycle; their output persists in staging (commit doesn't clear it). Therefore at `0x70100` of any steady-state lifecycle, the **prior** lifecycle's producer output should still be present — non-empty — and identical to what this lifecycle's producers would write.

Cody observed **0 non-zero words** in both `staged_fg_buffer` and `staged_bg_buffer` across the steady window. Since (a) the commit does not clear staging and (b) any producer write from any prior frame would persist, persistent emptiness means **the title producers are not populating staging at all** (never wrote, or write-then-fail / write-outside-the-hooked-range). The dirty flags being clear at `0x70100` is the *expected* post-commit state and is **not** independent evidence either way.

---

## Phase 3 — Classification

### **Classification C — Current placement is semantically correct; the empty-buffer evidence implies real producer failure.**

- The commit placement is the legitimate **deferred-commit** pattern (commit prior frame's staging at VBlank start under display-off, then produce). Not "front-loaded wrongly."
- The input mirror update is correctly placed **before** the producer body (step 2 before step 13).
- Crucially, the commit does **not** clear staging, so `0x70100` validly reflects persisted producer output. In steady state it is a sound proxy for "did the producers populate staging."
- Therefore Cody's empty-buffer result at `0x70100` is **not** a sample-point/post-clear artifact — it is a valid indicator that the title producers leave staging empty. **Classification A is ruled out** (commit doesn't clear staging; no producer output is being silently wiped at the sample point). **Classification B** (mixed placement) is not indicated — input is already before producers, commit/dirty-clear after the prior frame's producers, consistent with deferred commit. **Classification D** is not needed — the lifecycle placement is fully determinable statically.

**Cody's Layer 1 conclusion validity: SUPPORTED.** "Title producers do not populate `staged_fg/bg_buffer`" stands, because the sample point captures persisted output and the commit does not clear staging.

---

## Phase 4 — Bounded recommendation

**Next task: producer trace (Classification C path), bounded to the title producer→staging path** in the arcade VBlank body (step 13). Determine why the title producers leave staging empty in Build 0092, checking, in order:
1. Is the title sub-state handler's producer path actually reached each lifecycle (master state `%a5@(0)==0` → `0x3ABFE` → the handler that calls the glyph renderer / BG-FG strip producers)?
2. When the glyph renderer hook (`genesistan_hook_glyph_renderer_3bd48`) and other FG/BG producers run, do they write into `staged_fg/bg_buffer`? Verify the Build 0092 OPEN-016 Part-2 fix actually established the helper's required base registers (`%a6=staged_fg_buffer`, `%a3`/`%a5` LUTs) so the staging write lands — this is the direct continuation of `Andy_build_0091_helper_crash_triage.md` (the crash is gone in 0092, but "no crash" ≠ "writes staging").
3. Do the producer destinations fall inside the hooked C-window ranges (BG `0xC00000-0xC03FFF`, FG `0xC08000-0xC0BFFF`) so the hooks accept and stage them, rather than being rejected as out-of-range or routed to an unhooked writer?

This preserves the single arcade-owned VBlank lifecycle and the deferred-commit architecture — no rewrite, no validation framework, no recurring diagnostic. It is a one-path trace from the title sub-state handler through the staging write.

(Out of scope, deferred: Start→C→A crash, OPEN-015, the `0x0003ACEA` one-shot writer, broader unhooked-writer survey.)

---

## KNOWN_FINDINGS impact

**Option C — proposed refinement** (do NOT update `KNOWN_FINDINGS.md` here; propose for Cody after Tighe ack). Refine KF-011/KF-013 to record the explicit single-lifecycle ordering and the persistence fact:

> The single arcade-controlled VBlank lifecycle (Build 0092): HW Level-6 → `_vblank_service` (`0x700C2`): input-mirror update → display-off → deferred commit of the *previous* lifecycle's staging (tiles/BG/FG/sprites/palette/scroll, each dirty-gated) → display-on → `jmp 0x3A208` → arcade VBlank body runs the title producers (master dispatch `0x3A256` → title handler → glyph renderer/hooks) which populate `staged_fg/bg_buffer` for the *next* commit → `rte`. Commits clear only dirty flags, never the staged buffers, so staged content persists across frames. Consequence: a post-commit/pre-producer sample (e.g. `0x70100`) validly reflects persisted producer output in steady state.

STRONG/CONFIRMED (every step proven from source/disasm). Cross-ref KF-028, KF-010.

---

## Open / Closed Issues Impact

- Open issues touched: OPEN-001 (active — missing title screen; root narrowed to producer→staging), OPEN-016 (active — producer/staging path is the live thread; not closed), OPEN-015 (context only).
- Closed issues touched: NONE. New issues opened: NONE. Issues closed: NONE.
- Intentionally deferred: Start→C→A crash, OPEN-015 crash-handler fix, `0x0003ACEA` writer.

## STOP triggered

NO.
