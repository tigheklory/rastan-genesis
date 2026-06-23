# Cody - FG Cell-Composition Fix Build Follow-up

**Date:** 2026-06-22
**Type:** Implementation + verification follow-up after invariant-gate STOP
**Scope:** Keep the approved Option B source edit, correct the mistaken invariant expectation if the gate metric excludes semantic helper-growth accounting, build once, then verify relocation/runtime only if the produced ROM contains the fix. No source redesign. No `.Ltw_translate_attr` rewrite. No store/range/offset/caller changes. No bookmark cycle.

## Phase 0

Classification: **EXTENDING** (KF-028 / OPEN-016). Relevant priors loaded: KF-004, KF-006, KF-010, KF-011, KF-013, and KF-028. HIGH-hazard priors touched: KF-028 / KF-013 / KF-011 / KF-004. Open issues touched: OPEN-016 and OPEN-001; OPEN-015 context only. No CLOSED issue was reopened. Contradiction detected: **NO**.

Architecture compliance: CONFIRMED. The source edit remains a helper-local cell-composition preservation fix; no Genesis-owned loop, boot/init re-entry, scaffold, or gameplay scheduling was introduced.

## Gate Metric Definition

`total_genesis_bytes_covered` is the sum of finalized address-map segment sizes after overlays/padding, and the finalizer requires that sum to equal the final ROM byte length (`len(rom_bytes)`). In `rastan-direct`, the native helper area is represented as one `genesis_only` wrapper segment from `wrapper_start` to `len(rom_bytes)`, not as per-symbol helper spans. Therefore a helper-local instruction insertion is reflected in this metric only if it changes final ROM length; it is not a semantic count of native helper instructions. Cites: `tools/translation/postpatch_startup_rom.py:643-683`, `tools/translation/postpatch_startup_rom.py:1958-1974`, `tools/translation/postpatch_startup_rom.py:1979-2006`.

Conclusion: native-helper growth at `.Ltw_compose_d1_from_d0_d2` is not intended to force `total_genesis_bytes_covered` from `0x17CB58` to `0x17CB5A` unless the final ROM length changes. The prior pre-authorization was mistaken.

## Constant Correction

Reverted both canonical gate constants back to `0x17CB58` while leaving `CANONICAL_OPCODE_REPLACE_COUNT = 95` unchanged:

- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

The approved Option B source edit in `apps/rastan-direct/src/tilemap_hooks.s` was not changed.

## Build

Command run exactly once:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **GATE_PASS**, but relocation/static guard STOP fired after artifact production.

Produced artifact:

- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0093.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `4cc782854a40ccf3333ec8ecbe40f71a7617201576c124b60b49e5008fdd20e2`
- Build counter: `92 -> 93`
- `dist/release_counter.txt`: remained `350`

Invariant result:

- `total_genesis_bytes_covered = 0x17CB58`
- `opcode_replace patched_site count = 95`
- Address-map wrapper segment: `0x070000..0x17CB58`

## Relocation / Static Guard

STOP: the produced Build 0093 ROM is byte-identical to Build 0092 (`4cc78285...`) and does **not** contain the Option B instructions.

Disassembly of the produced ROM still shows the old sequence:

```asm
707d2: 3202            movew %d2,%d1
707d4: 0241 01ff       andiw #511,%d1
707d8: 3401            movew %d1,%d2
707da: 6100 ff76       bsrw 0x70752
707de: 3207            movew %d7,%d1
707e0: 8242            orw %d2,%d1
707e2: 4e75            rts
```

Expected Option B instructions (`move.w %d7,-(%sp)` / `move.w (%sp)+,%d1`) are absent from the produced ROM. Therefore the required `+2` helper-address shift and absolute-reference verification could not be verified in the produced artifact.

Local timestamp evidence shows `apps/rastan-direct/out/tilemap_hooks.o` was newer than `apps/rastan-direct/src/tilemap_hooks.s`, so the release invocation did not reassemble `tilemap_hooks.s` and linked a stale object. This is a build-dependency/stale-object condition; no second build was run because the task authorized only one release invocation.

## Runtime Verification

Runtime verification was **not run**. Because the produced ROM does not contain the source fix, title-entry tracing would only re-measure the old Build 0092 behavior (prior evidence: 258 `0x70794` stores, all `%d1=0x0000`).

Required after-fix check remains pending:

- Producer `0x3ACAE` / `0x3ACB6` executes.
- `0x70794` stores with `%a6=0x00FF501A` and in-buffer offsets.
- `%d1` at `0x70794` is nonzero for title text cells.
- No new crash.

## OPEN / KNOWN_FINDINGS Impact

OPEN-016 remains open. OPEN-001 remains open. OPEN-015 remains context only. No issue was opened or closed.

KNOWN_FINDINGS impact: Option A - no update. The task did not produce a ROM containing the fix and did not generate runtime evidence.

## STOP

STOP triggered: **YES** - relocation/static guard failed because Build 0093 is byte-identical to Build 0092 and does not contain the Option B source edit. Runtime verification was skipped as non-diagnostic.
