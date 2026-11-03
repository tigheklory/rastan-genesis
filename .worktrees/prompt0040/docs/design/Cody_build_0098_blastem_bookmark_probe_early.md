# Cody - Build 0098 BlastEm Early Bookmark Probe + Static HV Audit

**Date:** 2026-06-25  
**Type:** Bookmark probe + static audit only  
**Baseline ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0097.bin`  
**Baseline SHA256:** `b8e16f7c670dc8225584679b88d5a4ea71efb0dc5938d38420fca524ec71db72`  
**Probe ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0098.bin`  
**Probe SHA256:** `b751a5ad897eca5671eb4f2824a9e83d4a553baf09b9a644902f9e4fb1b5effc`  
**Scope:** Existing bookmark/helper mechanism only. No HV fix, no sanitizer, no Build 0097 display-origin change, no title-graphics change, no OPEN-015 work.

## Phase 0

Classification: **EXTENDING** (OPEN-017 / OPEN-005; OPEN-001 context only). Required priors loaded: `RULES.md`, `ARCHITECTURE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest `AGENTS_LOG.md`, existing bookmark-helper docs/source, `docs/design/Cody_blastem_hv_counter_write_diagnostic.md`, `docs/design/Cody_build_0097_display_origin_bias_impl.md`, and Build 54-era HV notes (`docs/design/Cody_build54_hvc_writer_search.md`, `docs/design/Andy_build54_hvc_writer_root_cause.md`, `docs/design/Cody_build54_hvc_actual_writer_trace.md`).

Architecture compliance: **PASS**. The arcade code remains the program; Genesis code remains helper/hardware service. This task added only a diagnostic bookmark activator through the existing `bookmarks_v2` mechanism.

Address-mapping discipline: **PASS**. Arcade-to-Genesis correlations below use `build/rastan-direct/address_map.json`. Arithmetic offsets are not used as proof.

## SGDK / Build 54-Era Clues Reviewed

Concrete carryover only:

- Build 54 literal scan found only `0xC00008` **reads**, not writes; Build 0097 repeats that pattern.
- Build 54 `0x000590` low-ROM RAM-test candidate was ruled false because the Genesis `preserved_vectors` segment replaces that low arcade range; the same architectural boundary remains relevant.
- Build 54 `0x03AD44` and `0x0561B6..0x0561D4` scary postincrement/fill patterns were ruled safe when intercepted by their helpers. Build 0097 still maps those paths through helper replacements.
- Build 54 MAME watchpoint timeout did not capture the BlastEm-style fatal, so MAME silence is treated as non-decisive.

## Literal `0x00C00008` Audit

Build 0097 contains exactly two executable literal `0x00C00008` references, and both are reads from the HV counter into `audit_guard_vcount`:

```asm
7186c: 33f9 00c0 0008 00ff 678c  movew 0x00c00008,0x00ff678c
71bc6: 33f9 00c0 0008 00ff 678c  movew 0x00c00008,0x00ff678c
```

Source sites:

- `apps/rastan-direct/src/pc090oj_hooks.s:420`
- `apps/rastan-direct/src/pc090oj_hooks.s:804`

Classification: **reads-only**. No literal direct write to `0x00C00008` was found.

## Computed / Base+Offset Write Candidate Audit

The audit searched for direct and computed access patterns into the VDP/HV block `0x00C00000..0x00C0001F`, including literal writes, VDP-base address-register setup, `8(Ax)` writes, indexed/displaced writes, and known arcade postincrement fill loops.

### Candidate Pattern 1 - Native direct VDP port writes

Machine scan found absolute writes only to canonical VDP data/control ports:

- Data port `0x00C00000`: boot/crash writes, `_vblank_service` commits, scroll data writes, tile upload path.
- Control port `0x00C00004`: boot/crash register writes, `vdp_set_reg`, `vdp_set_vram_write_addr`, scroll/CRAM commands.

No absolute writes to offsets `0x08..0x1F` were found.

### Candidate Pattern 2 - Native address-register VDP writes

Base-register VDP writers found:

- `0x71CB4`: `%a3 = 0x00C00004`; writes `(%a3)` only (sprite tile DMA setup)
- `0x71D22`: `%a3 = 0x00C00004`; writes `(%a3)` only (SAT DMA setup)
- `0x71DC0`: `%a3 = 0x00C00004`; writes `(%a3)` only (DMA self-test setup)
- `0x71E3E`: `%a4 = 0x00C00000`; reads `(%a4)` for DMA self-test readback, not a write to `8(%a4)`

No `8(%a3)` / `8(%a4)` VDP-base write was found.

### Candidate Pattern 3 - Destination displacement `@(8)` writes

The disassembly contains many `@(8)` destination writes, but inspected relevant helper-region sites resolve to WRAM/staged structures, not VDP base addresses. The current Build 0097 equivalents of the prior Build 54 helper-region examples are:

- `0x71596: movew %d3,%a0@(8)` with `%a0` based at WRAM staged sprite descriptor storage.
- `0x71AF0: movew %d3,%a0@(8)` with `%a0` based at WRAM staged sprite descriptor storage.

Classification: **false candidates** for HV writes.

### Candidate Pattern 4 - Original arcade `0x03AD44` fill primitive

Original arcade runtime evidence shows the `0x03AD44` fill primitive can write PC080SN tilemap addresses such as `0x00C00008` / `0x00C0000A`.

`build/rastan-direct/address_map.json` maps this exact arcade site to a patched Genesis site:

- Arcade `0x03AD44..0x03AD4C`
- Genesis `0x03AF44..0x03AF4C`
- Replacement bytes: `4EB9{genesistan_hook_3ad44_dispatch}4E75`

The Build 0097 ROM bytes at `0x03AF44` are:

```text
4eb9000717d84e75
```

`genesistan_hook_3ad44_dispatch` classifies `%a0`:

- `0x00C00000..0x00C0FFFF` -> tilemap branch into staging helpers
- `0x00D00000..0x00D007FF` -> PC090OJ branch into staged sprite helpers
- anything else -> audit guard path, which reads `0x00C00008` and halts

Bypass risk for the known `0x03AD44` path: **NO** from current static evidence. The known arcade PC080SN `0xC00008` fill is intercepted and routed to staging.

### Candidate Pattern 5 - `0x0561B6..0x0561D4` C-window clear loop

`address_map.json` maps arcade `0x0561B6..0x0561D4` to Genesis `0x0563B6..0x0563D4` as a patched site calling `genesistan_hook_cwindow_clear`. The raw arcade loop does not execute in Build 0097.

Bypass risk for this known clear loop: **NO** from current static evidence.

## Static Audit Result

Computed-write candidate sites reviewed: **YES**.

Unresolved computed write to `0x00C00008`: **NO**.

Candidate list summary:

| Candidate | Result |
|---|---|
| Native absolute VDP writes | canonical `0xC00000`/`0xC00004` only; no offset-8 write |
| Native `%a3=VDP_CTRL` writers | write `(%a3)` only; no `8(%a3)` |
| Native `%a4=VDP_DATA` DMA self-test readback | reads `(%a4)`; no write to `8(%a4)` |
| Destination `@(8)` helper writes | WRAM/staged sprite descriptors; false HV candidates |
| Arcade `0x03AD44` PC080SN fill | safely intercepted by `genesistan_hook_3ad44_dispatch` |
| Arcade `0x0561B6` C-window clear | safely intercepted by `genesistan_hook_cwindow_clear` |

Caveat: static audit cannot exclude a runtime-corrupted address register, emulator-specific strictness on an HV read, or a computed write whose base is loaded from data and not visible in simple literal/base setup patterns. This is why the BlastEm bookmark bisection is needed.

## Bookmark Probe Site

Chosen target: `runtime_genesis_pc 0x00070000` (`vdp_boot_setup`).

Rationale:

- The prompt's reset-near suggestion (`0x000202` / `_start`, `0x000226` / `_bootstrap`) is below the `bookmarks_v2` safety floor; the postpatcher rejects bookmark targets `< 0x400`.
- `0x00070000` is the earliest understood native startup helper label reached by `_bootstrap` (`jsr vdp_boot_setup`) and occurs before the first VDP boot-register write.
- This gives a clean first boundary: if BlastEm reaches the bookmark, reset/vector/header and `_start/_bootstrap` executed far enough to enter `vdp_boot_setup`; if the HV fatal happens first, the failure is earlier than `0x70000`.

Canonical Build 0097 bytes:

```text
0x00070000 before: 7000720461000078
```

Probe Build 0098 bytes:

```text
0x00070000 after:  4ef900071eb44e71
0x00071EB4 helper: 60fe
```

`0x00071EB4` resolves to `genesistan_diag_bookmark` in Build 0098.

## Build

Command run once:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **PASS**.

Artifacts:

- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0098.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `b751a5ad897eca5671eb4f2824a9e83d4a553baf09b9a644902f9e4fb1b5effc`
- Bookmark metadata folder: `dist/rastan-direct/bookmarks/build_0098_pc_0x00070000/`
- Release trace: `states/traces/rastan_direct_video_test_build_0098_mame_30s_20260625_091844/`
- Active bookmark state: `build/rastan-direct/active_bookmark_baseline.json`, cycle `BM-008`, pre-insert counter `97`

The release trace is consistent with an early park: no VDP-port live writes were reported in the standard summary window. This is not the decision evidence; the decision evidence is Tighe's BlastEm run.

## User Test Instructions

Run this ROM in BlastEm:

```text
dist/rastan-direct/rastan_direct_video_test_build_0098.bin
```

Report exactly:

1. Does BlastEm still show the same fatal first, before any stable park/freeze?
2. If a fatal appears, what is the exact BlastEm text?
3. If no fatal appears, does it park/freeze immediately in a stable black/early-boot state?

Expected visible marker if bookmark fires: **immediate helper park before VDP setup**. This likely appears as a stable black/frozen early boot screen rather than game/title output. If a debugger is available, PC should sit at or oscillate inside `genesistan_diag_bookmark` (`0x00071EB4`, bytes `60 FE`).

## Bisection Interpretation

- **Bookmark fires / no HV fatal first:** BlastEm reached `0x00070000`; the offending HV access is later. Next recommended probe: move later within boot, first just after `vdp_boot_setup`, then around bootstrap handoff, then VBlank and the high-priority audit-guard read region (`0x7186C` / `0x71BC6`).
- **HV fatal appears before bookmark:** the failure is earlier than `0x00070000`, inside reset/vector/header/`_start`/early `_bootstrap` before `vdp_boot_setup`. Because `bookmarks_v2` cannot target below `0x400`, the next evidence step should be non-bookmark BlastEm debugger/screenshot evidence for the low startup path rather than a speculative fix.

## Non-Actions

- HV write fix: NO
- Catch-all illegal-port sanitizer: NO
- Broad VDP rewrite: NO
- Build 0097 display-origin logic changed: NO, except diagnostic bookmark activator in Build 0098 ROM
- OPEN-015 work: NO
- Title graphics / Start crash work: NO
- Issues opened/closed: NO

## Rule 10 / STOP

Build 0098 is diagnostic-only. The immediate next ROM-producing task must revert BM-008 unless Tighe explicitly directs otherwise.

STOP triggered: **NO** for this task. The probe was produced successfully. Implementation of any HV fix remains blocked pending Tighe's BlastEm result.
