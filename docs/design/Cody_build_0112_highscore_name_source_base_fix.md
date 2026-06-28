# Cody - Build 0112 High-Score NAME Source-Base Fix

**Date:** 2026-06-28  
**Type:** Implementation + evidence  
**Build:** 0112  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0112.bin`  
**ROM SHA256:** `024241b2378dba68102637c368bc92d5edc41b2b30776363a96144146dfe215d`  
**Scope:** Fix only the high-score NAME producer source base in `genesistan_hook_highscore_fg_producer`. No high-score seeding, no score/round changes, no descriptor/LUT/routing redesign, no bookmark cycle, no OPEN-015 work.

## Phase 0

Classification: **EXTENDING**. Continued from the Build 0111 high-score NAME source audit, which classified the Build 0111 helper source base as wrong: the hook read from literal `0x0010C068 + src_off`, producing reads at `0x0010C1BF..0x0010C1CD`, instead of the mapped arcade work-RAM source window at Genesis WRAM `0x00FF0157..0x00FF0165`.

Relevant priors loaded from the current log/context: KF-032 raw-write class / high-score producer routing, OPEN-018, OPEN-001, and OPEN-015 as context only. No source outside the requested hook was intentionally modified.

## Source Change

In `apps/rastan-direct/src/tilemap_hooks.s`, changed only the high-score producer source-base constant:

```asm
-    .equ ARCADE_HIGHSCORE_SOURCE_BASE,       0x0010C068
+    .equ ARCADE_HIGHSCORE_SOURCE_BASE,       0x00FF0000
```

The hook still uses the descriptor table source offsets unchanged. Therefore descriptor `src_off = 0x0157` resolves to `0x00FF0157`, not to `0x0010C1BF` and not to `0x0010C000 + 0x68 + src_off`.

## Build Result

Release command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **PASS**.

- Build number: `0112`
- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0112.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `024241b2378dba68102637c368bc92d5edc41b2b30776363a96144146dfe215d`
- Numbered vs rolling `cmp`: byte-identical
- Canonical gate: `GATE_PASS`
- Release trace: `states/traces/rastan_direct_video_test_build_0112_mame_30s_20260628_120921/`

Canonical invariants were unchanged:

- `opcode_replace`: `103`
- `total_genesis_bytes_covered`: `0x17CE4C`

## Static Verification

Generated symbols and disassembly confirm the intended source base:

- `apps/rastan-direct/out/symbol.txt`: `00ff0000 a ARCADE_HIGHSCORE_SOURCE_BASE`
- `apps/rastan-direct/out/symbol.txt`: `000707a0 T genesistan_hook_highscore_fg_producer`
- `build/genesis_postpatch.disasm.txt`: `0x03C5FE: jsr 0x707a0`
- `build/genesis_postpatch.disasm.txt`: `0x707CA: addal #0x00FF0000,%a2`

Address-map correlation still identifies the patched site as `runtime_genesis_pc 0x03C5FE` for `arcade_pc 0x03C3FE`.

## Runtime Evidence

Primary focused trace:

- `states/traces/build_0112_highscore_name_source_base_fix_20260628_121213/`
- Command file: `highscore_name_source_base_fix.cmd`
- Raw trace: `native_debug_trace.log`

Tail/dump corroboration trace:

- `states/traces/build_0112_highscore_name_source_base_fix_dump_20260628_121401/`
- Command file: `highscore_name_source_base_fix_dump.cmd`
- Raw trace: `native_debug_trace.log`
- FG dump: `staged_fg_tail.bin`

### Source Reads

At high-score init, the mapped source window already contains the original NAME initials:

```text
0x00FF0157..0x00FF0165 = 43 4F 42 / 54 48 53 / 59 41 47 / 54 4B 47 / 59 54 4E
                         C  O  B   T  H  S   Y  A  G   T  K  G   Y  T  N
```

Runtime hook stage calls read exactly that mapped WRAM sequence:

| idx | source | bytes | text |
|---:|---|---|---|
| 0 | `0x00FF0157..0x00FF0159` | `43 4F 42` | `COB` |
| 1 | `0x00FF015A..0x00FF015C` | `54 48 53` | `THS` |
| 2 | `0x00FF015D..0x00FF015F` | `59 41 47` | `YAG` |
| 3 | `0x00FF0160..0x00FF0162` | `54 4B 47` | `TKG` |
| 4 | `0x00FF0163..0x00FF0165` | `59 54 4E` | `YTN` |

The bad old source read watchpoint on `0x0010C1BF..0x0010C1CD` fired **0** times. No runtime evidence supports continued reads from `0x0010C068` or the old shifted source window.

### Staging Writes

The high-score NAME producer made five calls to `0x03C5FE` and fifteen hook stage calls. The old raw body writer breakpoints did not fire:

- `0x03C62A`: `0` hits
- `0x03C646`: `0` hits
- `0x03C64A`: `0` hits

Tail staged NAME cells:

| idx | staged addresses | final words |
|---:|---|---|
| 0 | `0x00FF59D4/59D6/59D8` | `0019 0025 0018` |
| 1 | `0x00FF5AD4/5AD6/5AD8` | `0029 001E 0028` |
| 2 | `0x00FF5BD4/5BD6/5BD8` | `002D 0017 001D` |
| 3 | `0x00FF5CD4/5CD6/5CD8` | `0029 0021 001D` |
| 4 | `0x00FF5DD4/5DD6/5DD8` | `002D 0029 0024` |

These are nonzero staged cells derived from the mapped NAME initials through the existing tilemap FG fill path. This corrects the Build 0111 source-base error; it does **not** seed or alter the high-score table.

## Visual / Smoke Notes

The release MAME 30s trace completed and reported no live FG C-window raw writes (`fg_cwindow_live count=0`).

A BlastEm debug-mode smoke attempt was launched for Build 0112, but the GUI/debug invocation did not return cleanly through the shell timeout and was interrupted/cleaned up. No BlastEm evidence is claimed from that attempt. The MAME focused trace is the authoritative runtime evidence for this task.

The earlier expectation that the fixed source would be visually blank is **not supported** by the focused MAME trace: at the high-score pass, mapped WRAM contains `COB/THS/YAG/TKG/YTN`, and the hook stages nonzero NAME cells. If a separate visual run appears blank, that is downstream of this source-base fix and should be investigated separately.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-018: advanced by implementation evidence; not closed.
- OPEN-001: context only.
- OPEN-015: not touched.
- KNOWN_FINDINGS: no update made in this task.

## STOP

STOP triggered: **NO**.
