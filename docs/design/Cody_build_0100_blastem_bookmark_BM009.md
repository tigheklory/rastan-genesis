# Cody - Build 0099 BM-008 Revert + Build 0100 BM-009 BlastEm Bookmark Probe

**Date:** 2026-06-25  
**Type:** Bookmark cycle: revert BM-008, then insert BM-009  
**Scope:** Two sequential ROM-producing builds only. No HV fix, no sanitizer, no VDP rewrite, no display-origin/title changes, no OPEN-015 work.

## Phase 0

Classification: **EXTENDING** (OPEN-017 / OPEN-005; OPEN-001 context only). Required priors loaded: `RULES.md` Rule 10, `ARCHITECTURE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest `AGENTS_LOG.md`, `docs/design/Cody_build_0098_blastem_bookmark_probe_early.md`, `docs/design/Cody_blastem_hv_counter_write_diagnostic.md`, `docs/design/Andy_diagnostic_bookmark_helper_design.md`, `docs/design/Andy_diagnostic_bookmark_postpatch_invariant_design.md`, and `docs/design/Cody_diagnostic_bookmark_postpatch_invariant_implementation.md`.

Confirmed user evidence: Build 0098 in BlastEm hit BM-008 and parked at `genesistan_diag_bookmark` (`0x00071EB4`, `bra #-2`) with no HV fatal first. Therefore the BlastEm HV-counter crash is later than `runtime_genesis_pc 0x00070000`.

Architecture compliance: **PASS**. This task uses only the existing bookmark mechanism. The arcade program remains the program; Genesis code remains helper/hardware service.

Address-mapping discipline: **PASS**. BM-009 target `0x0007186C` is in `build/rastan-direct/address_map.json` as a `genesis_only` wrapper segment, not arcade-copy code. The relevant arcade-correlated `0x03AD44` path remains the JSON-recorded `patched_site` from arcade `0x03AD44..0x03AD4C` to Genesis `0x03AF44..0x03AF4C`.

## Build 1 - BM-008 Revert Only

Command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release BOOKMARK_REVERT=BM-008
```

Result: **PASS**.

- Build: `0099`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0099.bin`
- SHA256: `b8e16f7c670dc8225584679b88d5a4ea71efb0dc5938d38420fca524ec71db72`
- Baseline Build 0097 SHA256: `b8e16f7c670dc8225584679b88d5a4ea71efb0dc5938d38420fca524ec71db72`
- `cmp` against Build 0097: `0` / byte-identical
- Gate context: `authorized_revert`
- Active state file after revert: deleted (`build/rastan-direct/active_bookmark_baseline.json` absent)

Byte verification:

```text
0x00070000 restored: 7000720461000078
0x00071EB4 helper:  60fe
```

Interpretation: BM-008 is cleanly reverted. Build 0099 is canonical and byte-identical to Build 0097.

## Build 2 - BM-009 Insert Only

BM-009 starts from the clean Build 0099 canonical state.

Target: `runtime_genesis_pc 0x0007186C`.

Reason: this is the first instruction boundary of the first known executable `0x00C00008` access:

```asm
7186c: movew 0x00c00008,0x00ff678c ; audit_guard_vcount
```

The bookmark parks before this instruction executes. The instruction is 10 bytes, so the activator span is 10 bytes: `JMP_LONG_ABS` (6 bytes) plus two `4E71` NOPs.

Address-map segment for BM-009 target:

```json
{
  "genesis_start": "0x070000",
  "genesis_end_exclusive": "0x17CD28",
  "size_bytes": 1101096,
  "kind": "genesis_only",
  "tag": "wrapper"
}
```

No arcade equivalent is claimed for this native helper site.

Command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **PASS**.

- Build: `0100`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0100.bin`
- SHA256: `e5f7512a5064f0e85749c99901d653ca3104ab18b6021b076f9ee3f0d824a0ac`
- Active state file: present, cycle `BM-009`, pre-insert build counter `99`
- Helper resolved address: `0x00071EB4`

Activator/helper verification:

```text
0x0007186C before: 33f900c0000800ff678c
0x0007186C after:  4ef900071eb44e714e71
0x00071EB4 helper: 60fe
```

Production entry suspended: **NO**. The target is native `genesis_only` wrapper helper code, not an arcade `opcode_replace` production entry.

Diagnostic invariant status: **PASS** via gate diagnostic context. Current `bookmarks_v2` implementation applies the activator in the bookmark stage; opcode-replace manifest invariants remain canonical (`96`, `0x17CD28`) while §2.7 activator integrity verifies the bookmark bytes. BM-009 has `N=1` active bookmark and span `Σ=0x0A` for the bookmark stage.

## User HIT/MISS Instructions

Run this ROM in BlastEm:

```text
dist/rastan-direct/rastan_direct_video_test_build_0100.bin
```

Report exactly one of:

- **HIT:** clean park at helper `0x00071EB4`, shown as `bra #-2` / stable black screen / PC in helper loop, with no HV fatal first.
- **MISS:** HV fatal appears before the helper park. Please report the exact BlastEm fatal text.

Ignore `p/x $pc`; use the breakpoint-hit / disassembly PC line if BlastEm exposes it.

## HIT/MISS Interpretation

- **HIT:** execution reached just before `0x7186C` without crashing. The crash is at or after the audit-guard read. Next cycle should move the bookmark just past `0x7186C` to test whether that read itself triggers BlastEm.
- **MISS:** the crash is between `0x70000` and `0x7186C`. Next cycle should bisect that interval, with VBlank service entry as a midpoint suspect.

## Rule 10

Build 0100 is diagnostic-only. The immediate next ROM-producing task must revert BM-009 unless Tighe explicitly directs otherwise.

## Non-Actions

- HV fix/redirect/suppression: NO
- Illegal-port sanitizer: NO
- Display-origin/title changes: NO
- Exception/crash-screen work: NO
- OPEN-015 work: NO
- New diagnostic framework: NO
- Multiple active bookmarks: NO

## OPEN / KNOWN_FINDINGS Impact

- OPEN-017: active context, not closed.
- OPEN-005: HV-counter historical context, not closed.
- OPEN-001: context only.
- OPEN-015: not touched.
- KNOWN_FINDINGS impact: Option A - no update. This is still bisection evidence, not root-cause proof.

## STOP

STOP triggered: **NO**. Both sequential builds completed: Build 0099 revert-only and Build 0100 insert-only.
