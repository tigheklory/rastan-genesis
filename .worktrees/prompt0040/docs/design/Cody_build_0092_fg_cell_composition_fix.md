# Cody - Build 0092 FG Cell-Composition Fix Liveness Audit

**Date:** 2026-06-22  
**Type:** Implementation-gated liveness audit / STOP report  
**Build context:** Build 0092 -> next sequential build, `rastan-direct`  
**Scope:** Fix exactly F4 (`.Ltw_translate_attr` clobbers tile-carrying `%d7`) only if a byte-neutral scratch-register substitution is proven safe. No source/spec/tool/Makefile/ROM/invariant changes were made. No build. No runtime probing. No bookmark cycle.

## Phase 0

Relevant priors from `KNOWN_FINDINGS.md`:
- KF-004 (`runtime_genesis_pc` equals ROM file offset) — CONFIRMED; applies to all cited helper/runtime addresses.
- KF-006 (`identity_offset = 0x200`) — CONFIRMED; applies to arcade/source cross-reference for runtime helper code.
- KF-010 (FG -> Plane A) — STRONG; applies because the shared helper writes FG staging for Plane A.
- KF-011 (arcade Level-5 VBlank owns progression) — STRONG; respected because this task concerns an arcade-called helper only.
- KF-013 (text producer dispatch inside VBlank handler) — STRONG; applies because the affected title/text producer path runs in that VBlank-owned lifecycle.
- KF-028 (input shim / title text / OPEN-016 arc) — CONFIRMED/STRONG; applies because this task extends the Build 0092 zero-cell finding in the title glyph/FG helper path.

Rediscovery Hazard HIGH findings touched:
- KF-004 — HIGH; canonical reading: runtime Genesis PC maps to ROM offset verbatim; this task respects that address model.
- KF-011 — HIGH; canonical reading: arcade VBlank owns frame progression and Genesis code is service/helper only; this task respects that by considering only helper-local register correctness.
- KF-028 — HIGH; canonical reading: the title-text arc has exposed sequential translation/helper defects; this task tests the latest shared FG composition defect.

Deferred-appendix entries relevant: none.

Task classification: **EXTENDING** — tests/refines KF-028 and OPEN-016 with a proposed fix for the proven F4 zero-cell mechanism.

Open/Closed issues touched:
- OPEN-001 — touched; visible graphics remain broken.
- OPEN-016 — touched; this is the active title-text/FG composition thread.
- OPEN-015 — context only; no crash-handler work.
- CLOSED issues — read for context; none reopened.

Contradiction of CONFIRMED or STRONG finding detected during Phase 0 read: **NONE**.

Architecture compliance: **CONFIRMED**. The considered fix is a register-preservation correction inside an arcade-called helper. No Genesis-owned lifecycle, scaffolding, diagnostic ROM, or alternate execution path is introduced.

## Phase A - Register-Liveness Audit

### A.1 Caller Inventory

`.Ltw_translate_attr` callers:
- Direct caller `genesistan_hook_text_writer_3c4d2` fast path at `tilemap_hooks.s:515`.
- Direct caller `genesistan_hook_text_writer_3c4d2` slow-path first half at `tilemap_hooks.s:549`.
- Direct caller `genesistan_hook_text_writer_3c4d2` slow-path second half at `tilemap_hooks.s:563`.
- Shared compose caller `.Ltw_compose_d1_from_d0_d2` at `tilemap_hooks.s:643`.

`.Ltw_compose_d1_from_d0_d2` callers:
- `.Ltw_store_from_components_at_a2` at `tilemap_hooks.s:630` only.

`.Ltw_store_from_components_at_a2` callers:
- `.Ltw_write_pair_same` at `tilemap_hooks.s:675` and `tilemap_hooks.s:678`.
- `genesistan_hook_text_writer_3c950` paths at `tilemap_hooks.s:732`, `743`, `772`, `785`.
- `genesistan_hook_number_renderer_3c2e2` paths at `tilemap_hooks.s:925`, `932`, `939`, `972`, `1003`.
- `genesistan_hook_glyph_renderer_3bd48.Lgr_store_cell` at `tilemap_hooks.s:1088`.
- `genesistan_hook_text_writer_3c586` direct sentinel path at `tilemap_hooks.s:1199`.
- `genesistan_hook_text_writer_3c636` direct sentinel path at `tilemap_hooks.s:1295`.
- `genesistan_hook_text_writer_3c6dc` direct zero path at `tilemap_hooks.s:1360`.
- `genesistan_hook_text_writer_3c75c` direct sentinel path at `tilemap_hooks.s:1428`.
- `genesistan_hook_text_writer_3c830` direct paths at `tilemap_hooks.s:1588`, `1597`, `1602`, `1612`.

`.Ltw_write_pair_same` callers:
- `genesistan_hook_text_writer_3c550` at `tilemap_hooks.s:1116`.
- `genesistan_hook_text_writer_3c586` at `tilemap_hooks.s:1209`, `1223`.
- `genesistan_hook_text_writer_3c636` at `tilemap_hooks.s:1305`, `1319`.
- `genesistan_hook_text_writer_3c6dc` at `tilemap_hooks.s:1369`.
- `genesistan_hook_text_writer_3c75c` at `tilemap_hooks.s:1437`, `1450`.
- `genesistan_hook_text_writer_3c7a4` at `tilemap_hooks.s:1490`.
- `genesistan_hook_text_writer_3c830` at `tilemap_hooks.s:1528`, `1534`.

No caller outside this inventory was found by `rg` in `apps/rastan-direct/src/tilemap_hooks.s`.

### A.2 Candidate Registers

Primary candidates considered: `%d3`, `%d4`. A full data-register table is included because the direct `.Ltw_translate_attr` callers make the candidate space tighter than the shared compose helper alone suggests.

| Register | Verdict | Reason |
|---|---|---|
| `%d0` | NOT-SAFE | Direct `genesistan_hook_text_writer_3c4d2` callers need `%d0` after `.Ltw_translate_attr` as the tile/LUT result (`move.w %d0,%d1` at lines 517, 550, 564). |
| `%d1` | NOT-SAFE | `.Ltw_translate_attr` uses `%d1` as the attr-index accumulator and returns with `%d2` loaded from the attr LUT; replacing scratch with `%d1` would destroy the in-progress index calculation. |
| `%d2` | NOT-SAFE | `%d2` is the raw attr input and attr-LUT output. It is the helper's required output consumed by `or.w %d2,%d1` in direct and compose callers. |
| `%d3` | NOT-SAFE | Direct `genesistan_hook_text_writer_3c4d2` slow path tests `%d3` after the attr call (`cmpi.b #0x50,%d3` at line 555). Many shared callers also use `%d3` as loop/state input across `.Ltw_write_pair_same` / `.Ltw_store_from_components_at_a2`. |
| `%d4` | NOT-SAFE | Direct `genesistan_hook_text_writer_3c4d2` slow path uses `%d4` as the loop/half counter after attr calls (`cmpi.w #4,%d4` at line 557; `addq.w #1,%d4` line 569; `cmpi.w #5,%d4` line 570). Shared callers also carry offsets/counters in `%d4` across helper calls. |
| `%d5` | NOT-SAFE | `%d5` is row state for `.Ltw_store_cell`; direct `3c4d2` computes `%d5` before attr calls and uses it in `.Ltw_store_cell`. |
| `%d6` | NOT-SAFE | `%d6` is column state for `.Ltw_store_cell`; direct `3c4d2` computes `%d6` before attr calls and uses it in `.Ltw_store_cell`. |
| `%d7` | NOT-SAFE | `%d7` is the tile-carrying register in `.Ltw_compose_d1_from_d0_d2`; using it as scratch is the proven defect. |

Address registers are not valid replacements for this byte-neutral Option A because the code requires data-register word shifts and OR operations.

### A.3 Inner Safety

Across runtime_genesis_pc `0x70752..0x7081E` / `tilemap_hooks.s:578..670`:
- `%d0` is tile/glyph input to compose and address/range scratch in store.
- `%d1` is the composed cell output and attr-index accumulator inside `.Ltw_translate_attr`.
- `%d2` is raw attr input, attr-LUT output, and store offset scratch.
- `%d5/%d6` are row/column values for `.Ltw_store_cell`.
- `%d7` is the tile value after `0x707CE`, then saved/restored by `.Ltw_store_d1_at_a2` only after composition.
- `%d3/%d4` do not appear in the inner helper range, but the inner range does not save them. If `.Ltw_translate_attr` clobbers either, that clobber is visible to callers.

Inner conclusion: `%d3` and `%d4` are not consumed by the inner helper, but they are not protected by it. Inner non-use alone is insufficient.

### A.4 Outer Safety

| Caller path | Save/restore / local liveness | `%d3` | `%d4` |
|---|---|---:|---:|
| Direct `3c4d2` fast path (`line 515`) | `%d4` set after call; `%d3` not tested on fast path before finish. | SAFE locally | SAFE locally |
| Direct `3c4d2` slow path (`line 549`) | Returns to `cmpi.b #0x50,%d3` and `cmpi.w #4,%d4`. | NOT-SAFE | NOT-SAFE |
| Direct `3c4d2` slow half1 (`line 563`) | Returns to `.Ltw_after_half1`, then increments/tests `%d4`; `%d3` remains loop state. | NOT-SAFE | NOT-SAFE |
| `.Ltw_write_pair_same` callers | No save inside `.Ltw_write_pair_same`; caller-local loop counters/offsets frequently live in `%d3/%d4`. | NOT-SAFE | NOT-SAFE |
| `genesistan_hook_glyph_renderer_3bd48.Lgr_store_cell` | Saves `%d0-%d7/%a2-%a6` around per-cell call; outer state restored. | SAFE for this caller | SAFE for this caller |
| `genesistan_hook_number_renderer_3c2e2` | Saves `%d0-%d7/%a0/%a2-%a6`; outer state restored, but local paths use `%d3/%d4` across calls before final restore. | NOT-SAFE generally | NOT-SAFE generally |
| Text writer hooks `_3c550`, `_3c586`, `_3c636`, `_3c6dc`, `_3c75c`, `_3c7a4`, `_3c830`, `_3c950` | Prologues generally save `%d1-%d7` or selected live regs for the arcade caller, but local loops use `%d3/%d4` across shared helper calls. | NOT-SAFE generally | NOT-SAFE generally |

Outer conclusion: no candidate data register is safe across the complete caller set. `%d3` and `%d4` are especially disqualified by the direct `genesistan_hook_text_writer_3c4d2` slow path, which has no local save around `.Ltw_translate_attr` and uses both registers after the call.

### A.5 Contract Check

The shared compose/store contract is:
- Inputs: `%d0` tile/glyph index, `%d2` raw attr word, `%a2` destination C-window address, `%a3` tile LUT base, `%a5` attr LUT base, `%a6` FG staging base.
- Internal required carry: `%d7` holds tile LUT result from `0x707CE` through `0x707DE`.
- Outputs: `%d1` composed cell before store; `%d2` attr LUT result before OR; store writes to `WRAM staged_fg_buffer` when accepted.

No replacement data register can be introduced inside `.Ltw_translate_attr` without violating either a direct caller's live value or the shared compose/store contract.

### A.6 Verdict

**NOT-SAFE.** No byte-neutral Option A scratch-register substitution is proven safe across all callers of `.Ltw_translate_attr` and the shared FG compose/store path. Per the task STOP condition, Option A was not implemented. Option B is proposed below only; it was not implemented.

## Phase B - Option A Implementation

Not performed. The liveness audit returned NOT-SAFE.

## Phase C - Option B Proposal Only

Proposed shape for a separately authorized task:

```asm
.Ltw_compose_d1_from_d0_d2:
    move.w  %d0, %d7
    andi.w  #0x3FFF, %d7
    add.w   %d7, %d7
    move.w  0(%a3,%d7.w), %d7

    move.w  %d2, %d1
    andi.w  #0x01FF, %d1
    move.w  %d1, %d2
    move.w  %d7, -(%sp)       ; proposed inserted preserve
    bsr     .Ltw_translate_attr

    move.w  (%sp)+, %d1       ; proposed replacement for move.w %d7,%d1
    or.w    %d2, %d1
    rts
```

Projected invariant impact:
- Expected instruction delta: `+2` bytes, because `move.w %d7,-(%sp)` is inserted and `move.w (%sp)+,%d1` replaces the existing same-size `move.w %d7,%d1`.
- Current checked-in canonical gate values are `CANONICAL_OPCODE_REPLACE_COUNT = 95` and `CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x17CB58` in both `tools/translation/postpatch_startup_rom.py` and `tools/translation/verify_canonical_rom.py`.
- Projected current-source-of-truth coverage after Option B would be `0x17CB5A`, with opcode_replace patched-site count remaining `95`.
- The prompt text references `0x17CAF0`; that value is stale relative to the current checked-in gates and prior Build 0092 artifact-production logs. If using that stale value as a purely textual baseline, the same `+2` projection would be `0x17CAF2`, but the build pipeline currently gates on `0x17CB58`.
- `address_map.json` would need regeneration and review because helper addresses after the insertion point in the `0x70xxx` helper region would shift by `+2` bytes. Absolute references into shifted helpers would need OPEN-016-class relocation verification.
- Guarded counts needing reconfirmation: opcode_replace patched-site count, total_genesis_bytes_covered, address_map segment coverage, helper symbol addresses, and all absolute helper references affected by the shift.

Option B was **not** implemented in this task.

## Phase D - Build

No build was run. The task stopped after Phase A NOT-SAFE.

## Phase E - Runtime Verification

Not applicable. No ROM was produced.

## Open / Closed Issues Impact

Open issues touched: OPEN-016 (active; this audit blocks byte-neutral F4 fix and proposes the next approved shape), OPEN-001 (active; graphics still fail), OPEN-015 (context only). New issues opened: none. Issues closed: none.

Intentionally deferred: Start/C/A crash, OPEN-015 crash-handler defects, BG producer path, `0x3ACEA`, sprites/palette/scroll/general graphics, broader unhooked-writer survey, Option B implementation.

## KNOWN_FINDINGS Impact

**Option A - No new finding to index.** Rationale: F4 is already proven by Andy/Cody evidence; this task adds an implementation-gating liveness result and proposes the approved-next-shape, but no new durable runtime behavior finding was produced.

## STOP

STOP triggered: **YES**. Phase A could not prove any safe byte-neutral scratch register. Per directive, implementation/build/runtime verification were not performed, and Option B awaits explicit Tighe/Chad Sr. approval.
