# Cody - tilemap_hooks Rebuild Dependency Fix + Build 0094 Verification

**Date:** 2026-06-22
**Type:** Build-integrity fix + implementation verification
**Build context:** after invalid Build 0093, `rastan-direct`
**Scope:** Fix the stale `.s -> .o` rebuild vulnerability that let the approved Option B source edit be omitted from Build 0093; keep the Option B source edit unchanged; build once; verify produced ROM statically and by title-entry runtime trace. No bookmark cycle. No graphics-system redesign. No Start/C/A or OPEN-015 work.

## Phase 0

Classification: **INFRASTRUCTURE** for the build-rule fix, with an **EXTENDING** verification tail for KF-028 / OPEN-016 F4. Relevant priors loaded: KF-004, KF-006, KF-010, KF-011, KF-013, KF-028. HIGH-hazard priors touched: KF-028, KF-013, KF-011, KF-004. Open issues touched: OPEN-016 and OPEN-001; OPEN-015 context only. CLOSED issue touched: CLOSED-008 as a recurrence/sibling-gap reference. Contradiction detected: **NO**.

Architecture compliance: CONFIRMED. The retained source fix remains helper-local cell composition (`.Ltw_compose_d1_from_d0_d2`) and does not add Genesis-owned control flow, boot/init re-entry, scaffolding, or gameplay scheduling.

## Build-Rule Cause

The explicit Makefile dependency for `out/tilemap_hooks.o` already named `src/tilemap_hooks.s`, so this was not the exact CLOSED-008 missing-prerequisite root. The failure was a sibling stale-object gap: the previous task restored/generated `apps/rastan-direct/out/tilemap_hooks.o` with an mtime newer than the edited `apps/rastan-direct/src/tilemap_hooks.s`, so Make's timestamp-based rule considered the object fresh and linked stale bytes. The canonical gate audits `.incbin` dependency completeness but does not validate ordinary `.s` source content against object content, so Build 0093 passed while byte-identical to Build 0092.

## Dependency Fix

Added a narrow assembler invalidation prerequisite in `apps/rastan-direct/Makefile`:

- Added `.PHONY: FORCE_ASM_REBUILD`.
- Added `FORCE_ASM_REBUILD` as a normal prerequisite to each assembled object rule.

This keeps the existing explicit dependencies and simply forces assembler objects to be regenerated during `release`, preventing a newer stale object from shadowing an edited source. It generalizes to sibling assembled sources without redesigning the build system.

## CLOSED-008 Routing

Routing decision: **sibling recurrence of CLOSED-008, not the same original missing `.incbin` prerequisite root**. I did not silently reopen CLOSED-008 and did not create a new OPEN issue because the build-integrity gap was fixed and verified in this task. If Tighe/Claude want issue-ledger tracking for the historical recurrence, the clean route is a CLOSED-008 addendum or a new linked issue only if additional unresolved stale-object cases remain.

## Build 0094

Command run exactly once:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **PASS**.

- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0094.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `558c88b39b359af7ee1f2cee1fa2318dde34b20ebfab7d25e25c0a18e0a819e2`
- Build counter: `93 -> 94`
- Invariant: `total_genesis_bytes_covered=0x17CB58`; opcode_replace patched-site count `95`

## Validity Gate

Build 0094 is **not** byte-identical to Build 0092/0093 (`4cc782854a40ccf3333ec8ecbe40f71a7617201576c124b60b49e5008fdd20e2`).

Produced disassembly contains Option B at the compose site:

```asm
707d2: 3202            movew %d2,%d1
707d4: 0241 01ff       andiw #511,%d1
707d8: 3401            movew %d1,%d2
707da: 3f07            movew %d7,%sp@-
707dc: 6100 ff74       bsrw 0x70752
707e0: 321f            movew %sp@+,%d1
707e2: 8242            orw %d2,%d1
707e4: 4e75            rts
```

Acceptance: **PASS**.

## Address Map / Relocation Guard

Address-map coverage remained canonical:

- `total_genesis_bytes_covered=0x17CB58`
- opcode_replace patched-site count `95`
- wrapper segment: `0x070000..0x17CB58`

The Option B insertion shifted downstream native helper addresses in the `0x70xxx` wrapper while leaving the shared store entry before the insertion unchanged:

- Range helper shifted to `0x707E6`; caller at `0x707C0` branches to `bsrw 0x707E6`.
- Glyph per-cell helper shifted from previous `0x70BC8` to `0x70BCA`; callers branch to `0x70BCA`.
- Shared store entry `0x707BC` remains before the insertion and existing callers still branch to `0x707BC`.

This verifies the produced ROM's internal branch references to shifted helper locations are coherent.

## Runtime Verification

Runtime trace directory: `states/traces/build_0094_title_producer_entry_window_trace_20260622_183218/`.

The debugger run produced the required event window; the outer shell timeout returned `124` after data capture, but MAME stdout reports the intended 29-second emulated window, and the release target's own 30-second trace completed normally. Crash-halt breakpoint count was `0`.

Reduced analysis:

- Producer `0x3ACAE`: `1` hit at frame `212`
- First render call `0x3ACB6`: `1` hit at frame `212`
- FG range gate `0x707E6`: `258` hits
- FG range accept `0x70818`: `258` hits
- FG store `0x70794`: `258` hits
- All `0x70794` stores had `%a6=0x00FF501A` and in-buffer offsets: `YES`
- Nonzero `%d1` stores: `213`
- Zero `%d1` stores: `45`
- Crash halt events: `0`

Before/after:

- Build 0092 prior: `258` stores, all `%d1=0x0000`
- Build 0094: `258` stores, `213` nonzero `%d1` values

The literal C/R/E/D/I ASCII bytes are visible at the range-gate source value (`d0=0x43/0x52/0x45/0x44/0x49`) before composition. At `0x70794`, `%d1` is already the composed Genesis cell/tile word, so the store values are nonzero tile/cell values such as `0x0019`, `0x0027`, `0x001B`, `0x001A`, `0x001F`, not raw ASCII.

## OPEN / KNOWN_FINDINGS Impact

OPEN-016 remains open: Build 0094 verifies the F4 zero-cell fix at runtime, but title/attract visual acceptance and broader deferred surveys remain. OPEN-001 remains open pending visible rendered title/game graphics. OPEN-015 remains context only.

KNOWN_FINDINGS impact: Option A. No new canonical finding was added; this task implemented and verified the already-diagnosed F4 mechanism.

## STOP

STOP triggered: **NO**.
