# Cody - Build 0106 PC080SN Scroll-RAM Clear C-lite Implementation

**Date:** 2026-06-25
**Type:** Implementation + evidence
**Build:** 0106
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0106.bin`
**SHA256:** `ad894a86029738d8ab0b933b1acc55c2c6de06b5cc2d0e6535f121af28326d4e`
**Scope:** Implement the Build 0105 C-lite design for PC080SN per-line scroll-RAM clears. No bookmark cycle. No HV sanitizer. No VDP rewrite. No `0x3B392` producer fix. No OPEN-015 work.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: `RULES.md`, `ARCHITECTURE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest `AGENTS_LOG.md`, and `docs/design/Andy_build_0105_hv_counter_root_cause_fix_design.md`.

Open issues touched: OPEN-017 active; OPEN-005 and OPEN-001 context only; OPEN-015 not touched. No CONFIRMED/STRONG contradiction detected.

The active design is Andy's Candidate C-lite revision: route the two PC080SN scroll-RAM raw-fill call sites through the existing `0x3AF44` dispatch, and add named input-preserving scroll-RAM translation stubs rather than relying on a silent range-gate absorb.

## Implementation

### Call-site reroutes

Added two `opcode_replace` entries in `specs/rastan_direct_remap.json`:

| Runtime PC | Arcade PC | Before | After | Meaning |
|---|---|---|---|---|
| `0x03B15E` | `0x03AF5E` | `6100FDDC` | `6100FDE4` | BG scroll-RAM clear calls `0x3AF44` dispatch instead of raw `0x3AF3C` |
| `0x03B16E` | `0x03AF6E` | `6100FDCC` | `6100FDD4` | FG scroll-RAM clear calls `0x3AF44` dispatch instead of raw `0x3AF3C` |

Generated ROM verification:

```text
03B15E: 6100fde4
03B16E: 6100fdd4
03AF3C: 30c0534166fa4e75
03AB9E: 6100039c
03AF44: 4eb9000717ec4e75
```

`0x3AF3C` remains the raw arcade-copy word-fill primitive. The WRAM caller at `0x3AB9E` still calls/reaches `0x3AF3C`.

### Named scroll-RAM handlers

Added exported helpers in `apps/rastan-direct/src/tilemap_hooks.s`:

- `genesistan_hook_pc080sn_bg_scroll_fill`
- `genesistan_hook_pc080sn_fg_scroll_fill`

Both handlers save/restore registers and do not raw-write PC080SN/VDP mirror space. They are named semantic homes for PC080SN per-line scroll RAM under the current KF-015 full-plane scroll model, with comments identifying future translation options: Genesis HSCROLL table or uniform per-line scroll reduction to staged full-plane scroll.

Symbol verification:

```text
000713de T genesistan_hook_pc080sn_bg_scroll_fill
000713e8 T genesistan_hook_pc080sn_fg_scroll_fill
000717ec T genesistan_hook_3ad44_dispatch
```

Generated handler bodies:

```asm
713de: 48e7 fffe       moveml %d0-%fp,%sp@-
713e2: 4cdf 7fff       moveml %sp@+,%d0-%fp
713e6: 4e75            rts
713e8: 48e7 fffe       moveml %d0-%fp,%sp@-
713ec: 4cdf 7fff       moveml %sp@+,%d0-%fp
```

### Explicit 4-way dispatch split

Revised `genesistan_hook_3ad44_dispatch` in `apps/rastan-direct/src/pc090oj_hooks.s` so the tilemap branch is explicit:

- `[0x00C00000,0x00C04000)` -> `genesistan_hook_tilemap_bg_fill`
- `[0x00C04000,0x00C08000)` -> `genesistan_hook_pc080sn_bg_scroll_fill`
- `[0x00C08000,0x00C0C000)` -> `genesistan_hook_tilemap_fg_fill`
- `[0x00C0C000,0x00C10000)` -> `genesistan_hook_pc080sn_fg_scroll_fill`

Generated dispatch evidence:

```asm
717ec: moveml %d0-%fp,%sp@-
717f0: movel %a0,%d2
...
7185a: cmpil #0x00c04000,%d2
71860: bcs 0x7187a        ; BG names -> 0x70588
71862: cmpil #0x00c08000,%d2
71868: bcs 0x71882        ; BG scroll -> 0x713de
7186a: cmpil #0x00c0c000,%d2
71870: bcs 0x7188a        ; FG names -> 0x7065e
71872: bsrw 0x713e8       ; FG scroll
7187a: bsrw 0x70588       ; BG names
71882: bsrw 0x713de       ; BG scroll
7188a: bsrw 0x7065e       ; FG names
```

The dispatch copies `A0` to `D2` for range classification; `A0/D0/D1` are not destroyed before the named scroll handlers are called.

## Build Verification

Release command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Final result: **PASS**.

- Numbered build: `0106`
- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0106.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `ad894a86029738d8ab0b933b1acc55c2c6de06b5cc2d0e6535f121af28326d4e`
- Rolling vs numbered: byte-identical (`cmp=0`)
- MAME trace produced by release: `states/traces/rastan_direct_video_test_build_0106_mame_30s_20260625_215031/`
- Boot guard: PASS before and after postpatch
- Gate: `GATE_PASS`
- Build counter after release: `106`

Manifest/gate values:

```text
expectations.opcode_replace_count = 98
patch_counts.opcode_replace_and_rom_opcode_replace = 98
postpatch_expected_opcode_replace_sites = 98
postpatch_expected_total_genesis_bytes_covered = 0x17CD68
bookmarks_v2_count = 0
bookmarks_v2_applied = []
```

Invariant changes:

- `opcode_replace`: `96 -> 98`
- `total_genesis_bytes_covered`: `0x17CD28 -> 0x17CD68`
- Mechanical helper/dispatch growth: `+0x40`

`build/rastan-direct/active_bookmark_baseline.json` is absent after the build. No bookmark is active.

## Address-Map Verification

`build/rastan-direct/address_map.json` regenerated and records:

- `0x03B15E..0x03B162` as an `opcode_replace` patched site for arcade `0x03AF5E`, replacement `6100fde4`, shift delta `0`.
- `0x03B16E..0x03B172` as an `opcode_replace` patched site for arcade `0x03AF6E`, replacement `6100fdd4`, shift delta `0`.
- `0x03AF3C` remains inside an `arcade_copy` segment mapping arcade `0x03AD3C`.
- `0x03AF44` remains an `opcode_replace` patched site mapping arcade `0x03AD44`, now calling relocated dispatch `0x717EC`.
- New helper symbols are in the `genesis_only` wrapper segment ending at `0x17CD68`.

## Validation Gaps

BlastEm validation was requested but could not be executed in this workspace: neither `blastem` nor `blastem.exe` is available on `PATH`, and no bundled BlastEm executable was found under `tools/` or `apps/`.

Pending external BlastEm check for Tighe:

- Run Build 0106 in BlastEm.
- Expected: no fatal during the `0x3B152` `0xC04000` clear or the `0x3B16E` `0xC0C000` clear.
- If a new fatal appears, capture the exact BlastEm message, current instruction/PC, and recent path. Andy predicts the next exposure may be the inline producer around `0x3B392` raw `0xC093xx` writes; if so, record it as the expected next exposure, not a failure of this scroll-clear fix.

## KNOWN_FINDINGS Impact

Option A for this task: `KNOWN_FINDINGS.md` was not edited. Andy provided a KF proposal, but this prompt's authorization was conditional; I left canonicalization pending explicit Tighe/Claude/Chad approval rather than silently adding a new durable finding.

## Open / Closed Issues Impact

- Open issues touched: OPEN-017, OPEN-005 context, OPEN-001 context.
- Closed issues touched: NONE.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: `0x3B392` inline producer raw-write routing, real per-line scroll implementation, BlastEm external runtime validation, OPEN-015.

## STOP

STOP triggered: **NO** for implementation/build/static verification. BlastEm validation remains pending because the tool is unavailable in this workspace.
