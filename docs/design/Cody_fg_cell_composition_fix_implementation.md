# Cody - FG Cell-Composition Fix Implementation STOP

**Date:** 2026-06-22  
**Type:** Implementation + verification attempt, STOP at invariant gate  
**Build context:** Build 0092 -> next sequential build, `rastan-direct`  
**Scope:** Approved Option B caller-preserve fix for F4 only. No diagnostic ROM. No bookmark cycle. No runtime probing after STOP. No Start/C/A, OPEN-015, BG, sprites, palette, scroll, or general graphics work.

## Phase 0

Relevant priors from `KNOWN_FINDINGS.md`:
- KF-004 (`runtime_genesis_pc` equals ROM file offset) — CONFIRMED; applies to helper/runtime addresses.
- KF-006 (`identity_offset = 0x200`) — CONFIRMED; applies to source/runtime cross-reference.
- KF-010 (FG -> Plane A) — STRONG; applies because the shared helper writes FG staging.
- KF-011 (arcade Level-5 VBlank owns progression) — STRONG; respected because this task changes only an arcade-called helper.
- KF-013 (text producer dispatch inside VBlank handler) — STRONG; applies to the affected title/text producer path.
- KF-028 (input shim / title text / OPEN-016 arc) — CONFIRMED/STRONG; applies because this implements the approved fix for the Build 0092 zero-cell mechanism.

Rediscovery Hazard HIGH findings touched: KF-004, KF-011, KF-028. No contradiction detected.

Deferred-appendix entries relevant: none.

Task classification: **EXTENDING** — implements the approved Option B fix for the proven F4 mechanism under KF-028 / OPEN-016.

Open/Closed issues touched: OPEN-016 active, OPEN-001 active, OPEN-015 context only. Closed issues read for context; none reopened.

Architecture compliance: **CONFIRMED**. The attempted fix is a production register-preservation change inside an arcade-called helper.

## Diff Applied

Exactly the approved Option B source change was applied in `apps/rastan-direct/src/tilemap_hooks.s`:

```asm
.Ltw_compose_d1_from_d0_d2:
    move.w  %d0, %d7
    andi.w  #0x3FFF, %d7
    add.w   %d7, %d7
    move.w  0(%a3,%d7.w), %d7

    move.w  %d2, %d1
    andi.w  #0x01FF, %d1
    move.w  %d1, %d2
    move.w  %d7, -(%sp)
    bsr     .Ltw_translate_attr

    move.w  (%sp)+, %d1
    or.w    %d2, %d1
    rts
```

No store/range/offset code was touched. No caller setup was touched. `.Ltw_translate_attr` internals were not touched.

Gate constants were updated from `0x17CB58` to the pre-authorized `0x17CB5A` in:
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

## Instruction-Size Check

`move.w %d7,%d1` and `move.w (%sp)+,%d1` are both 2-byte instructions in the assembled helper. The inserted `move.w %d7,-(%sp)` is 2 bytes. Source-level intended delta: `+2` bytes.

Failed-build ELF static evidence confirms the instructions landed at the intended site:

```asm
707c6: 3e00            movew %d0,%d7
707c8: 0247 3fff       andiw #16383,%d7
707cc: de47            addw %d7,%d7
707ce: 3e33 7000       movew %a3@(0,%d7:w),%d7
707d2: 3202            movew %d2,%d1
707d4: 0241 01ff       andiw #511,%d1
707d8: 3401            movew %d1,%d2
707da: 3f07            movew %d7,%sp@-
707dc: 6100 ff74       bsrw 70752
707e0: 321f            movew %sp@+,%d1
707e2: 8242            orw %d2,%d1
707e4: 4e75            rts
```

The downstream helper body shifted in the assembled ELF (`.Ltw_store_d1_at_a2` begins at `0x707E6` instead of prior `0x707E4`), consistent with the inserted 2-byte instruction in native helper code.

## Build Invocation

Pre-build counters:
- `build/rastan-direct/build_counter.txt`: `92`
- `dist/release_counter.txt`: `350`

Command run exactly once:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **STOP before numbered artifact production**.

Failure:

```text
RuntimeError: Build 0029 invariant failure: expected total_genesis_bytes_covered=0x17CB5A and opcode_replace patched_site count=95; got total_genesis_bytes_covered=0x17CB58 opcode_replace patched_site count=95. build_context=canonical.
```

Post-build counters:
- `build/rastan-direct/build_counter.txt`: `92` unchanged
- `dist/release_counter.txt`: `350` unchanged

Artifacts:
- Numbered Build 0093 ROM: not produced
- Rolling `apps/rastan-direct/dist/rastan_direct_video_test.bin`: deleted by Make failure behavior

## Invariant Reconciliation

Authorized invariant expectation: `0x17CB58 -> 0x17CB5A`, opcode_replace count `95` unchanged.

Observed postpatch gate values: `total_genesis_bytes_covered=0x17CB58`, opcode_replace count `95`.

STOP reason: the measured guarded coverage did **not** move by the authorized `+2`. This violates the prompt's invariant pre-authorization condition, even though the failed-build ELF shows the inserted native helper instruction landed at the intended site.

No workaround was attempted. The build was not rerun.

## Address Map / Relocation Guard

Fresh `address_map.json` was not regenerated because postpatch stopped at the invariant gate before successful artifact production. Existing `build/rastan-direct/address_map.json` remains from the prior successful Build 0092 timestamp and is not valid evidence for this attempted build.

Relocation guard result: **not verified due STOP**.

## Runtime Verification

Not performed. No ROM artifact was produced.

Required runtime checks remain pending:
- `0x3ACAE` / `0x3ACB6` producer execution regression
- `0x70794` store regression with `%a6=0x00FF501A`
- nonzero `%d1` title-text cells
- no new crash/address-error

## Open / Closed Issues Impact

Open issues touched: OPEN-016 (active; approved Option B attempted but stopped at invariant gate), OPEN-001 (active graphics context), OPEN-015 (context only). New issues opened: none. Issues closed: none.

Intentionally deferred: Start/C/A crash, OPEN-015 crash-handler defects, BG producer path, `0x3ACEA`, sprites/palette/scroll/general graphics, broader unhooked-writer survey, runtime verification.

## KNOWN_FINDINGS Impact

**Option A - No new finding to index.** Rationale: F4 remains the proven mechanism; this task stopped at build invariant verification before producing new runtime evidence.

## STOP

STOP triggered: **YES**. The single authorized build reported `total_genesis_bytes_covered=0x17CB58`, not the authorized `0x17CB5A`. No Build 0093 artifact exists from this task.
