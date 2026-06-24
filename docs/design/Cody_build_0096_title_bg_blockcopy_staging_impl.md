# Cody - Build 0096 Title BG Block-Copy Staging Implementation

**Date:** 2026-06-24  
**Type:** Reconcile-then-implement / runtime verification  
**Build context:** Build 0095 -> Build 0096, `rastan-direct`  
**Build 0096 ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0096.bin`  
**Build 0096 SHA256:** `c054107bc6dfccb45b1703a0896be9905f729b89d1e0b16a4677d30badfde51c`  
**Scope:** Translate the confirmed title BG block-copy engine into Genesis BG staging. No preload/LUT, FG/glyph, sprite, palette, Start/C/A, OPEN-015, BlastEm/Nomad/HV-counter, or copyright-string work.

## Phase 0

Classification: **EXTENDING** for OPEN-001 / title-art rendering. Relevant priors loaded from `RULES.md`, `ARCHITECTURE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest `AGENTS_LOG.md`, and the required design docs:

- `docs/design/Cody_build_0095_title_bg_blockcopy_staging_diagnostic.md`
- `docs/design/Cody_build_0095_arcade_title_tile_usage_audit.md`
- `docs/design/Cody_build_0095_3ad44_dispatch_fg_bg_split.md`

No contradiction with CONFIRMED/STRONG priors was detected. The arcade code remains the program; the Genesis code added here is a hardware-service translation helper for an existing arcade PC080SN BG block-copy routine.

Address mapping discipline: all arcade-to-Genesis mappings used here are from `build/rastan-direct/address_map.json`, segment `171` (`arcade_copy`), not arithmetic offset proof. Segment `171` maps arcade `0x05A4DE` to Genesis runtime `0x05A6DE`, and arcade source table `0x05B0B2` to Genesis table `0x05B2B2`.

## Part 1 - Reconciliation Verdict

The large stylized red TAITO logo already being partially visible in Build 0095 is **not** evidence of a separate correct BG staging path. The required reconciliation is:

- Arcade intent is already established from original MAME runtime: the complete TAITO / RASTAN / sword title art is the PC080SN BG C-window block at arcade caller `0x05A38E`, block-copy routine `0x05A4DE`, source table `0x05B0B2`, destination `0x00C00328`, size `28x20`.
- Build 0095 runtime evidence showed `bg_dirty=0x00000000` at `0x3AC88` and no staged BG cells for this block, so the port was not committing the block through `staged_bg_buffer`.
- Build 0095 still contained the original block-copy bytes at mapped Genesis `0x05A6DE`, so the arcade routine was writing directly to PC080SN/Genesis-VDP-aliased addresses rather than to the Genesis staging pipeline.
- The user-supplied Build 0095 plane-viewer evidence had Plane A selected for the visible large red TAITO. That visual evidence does not establish a legitimate BG staging source and is consistent with raw/untracked/aliased VDP state or previous plane residue.

**Fix-safety classification:** **(iii) / (i)-leaning.** The `0x05B0B2` block remains the sole proven correct arcade source for the complete title-art block. Translating it into BG staging should stage and dirty the complete intended BG block rather than duplicate another proven BG source. The pre-implementation STOP condition was not triggered.

Visual caveat: this reconciliation is based on runtime/staging evidence and prior screenshots, not a new on-screen visual capture after the fix. The final no-duplication/overlap visual check remains **USER MUST VERIFY**.

## Implementation

### Spec Entry

Added one `opcode_replace` entry to `specs/rastan_direct_remap.json`:

- `arcade_pc`: `0x05A4DE`
- original bytes: `3800244932C232D85340`
- replacement: `JMP genesistan_hook_tilemap_bg_blockcopy` plus padding bytes inside the replacement span
- expected opcode replacement count: `95 -> 96`

This is a redirected production replacement for an existing arcade hardware block-copy routine. The padding is not the justification for the fix; the fix is the helper redirection and shift-table-managed opcode replacement.

### Helper

Added `genesistan_hook_tilemap_bg_blockcopy` to `apps/rastan-direct/src/tilemap_hooks.s` and exported it in the spec-required symbol list.

The helper preserves the original routine contract:

- input `%a1` = PC080SN destination
- input `%a0` = source tile table
- input `%d0` = width
- input `%d1` = height
- input `%d2` = attr word
- row stride = `0x100` in PC080SN address space
- consumes one source word per cell and advances destination by four bytes per cell
- advances to the next row using the original `0x100` PC080SN row stride

Genesis behavior:

- accepts BG C-window destinations in `0x00C00000..0x00C03FFF`
- translates destination to `staged_bg_buffer` offset
- composes the Genesis cell word through `genesistan_pc080sn_tile_vram_lut` and `genesistan_pc080sn_attr_lut`
- writes to `staged_bg_buffer`
- sets `bg_row_dirty` for each touched row

No legacy `genesistan_bulk_tilemap_commit` helper was imported.

## Invariant Reconciliation

Pre-declared category: one new helper plus one new opcode replacement site.

Static pre-build measurement:

- old `tilemap_hooks.o .text`: `0x10C6`
- new temporary assembled `.text`: `0x119A`
- helper growth: `+0xD4`
- opcode replacement count: `95 -> 96`
- total covered bytes: `0x17CC40 -> 0x17CD14`

Canonical invariant updates:

- `CANONICAL_OPCODE_REPLACE_COUNT = 96`
- `CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x17CD14`

Post-build manifest and map:

- `patch_counts.opcode_replace_and_rom_opcode_replace = 96`
- `postpatch_expected_opcode_replace_sites = 96`
- `postpatch_expected_total_genesis_bytes_covered = 0x17CD14`
- `address_map.segment_coverage.total_genesis_bytes_covered = 1559828` (`0x17CD14`)
- address-map gaps: none
- address-map overlaps: none

No out-of-category opcode replacement count change was observed.

## Build

Command run once:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **PASS**.

Build output:

- Build number: `0096`
- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0096.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `c054107bc6dfccb45b1703a0896be9905f729b89d1e0b16a4677d30badfde51c`
- Size: `1559828` bytes
- Prior Build 0095 SHA: `273508a23ddd7b37e10e7ba4a7355f78e95bbe539ba3145b4e844b59ace53ef6`
- Build 0096 is not byte-identical to Build 0095.
- Release trace artifact: `states/traces/rastan_direct_video_test_build_0096_mame_30s_20260624_110345/`

Static ROM verification:

- `build/genesis_postpatch.disasm.txt` maps Genesis `0x05A6DE` to `jmp 0x70720`.
- `apps/rastan-direct/out/symbol.txt` resolves `genesistan_hook_tilemap_bg_blockcopy = 0x00070720`.
- Build 0096 ROM bytes at `0x05A6DE` begin `4ef9000707204e714e71`, so the original block-copy loop no longer remains at the entry.

## Runtime Verification

Evidence directory:

- `states/traces/build_0096_title_bg_blockcopy_staging_validation_20260624_110646/`

Artifacts:

- `mame_title_bg_blockcopy_validation.cmd`
- `native_debug_trace.log`
- `bg_before_3ac54.bin`
- `bg_after_5a58e.bin`
- `bg_after_3ac88.bin`
- `fg_before_3ac54.bin`
- `fg_after_5a58e.bin`
- `fg_after_3ac88.bin`
- `bg_blockcopy_reduced_summary.json`

Debugger events proved the path:

```text
EVENT TITLE_BLOCK_5A58E_ENTRY ... bg_dirty=00000000
EVENT TITLE_BLOCK_ROUTINE_5A6DE_ENTRY ... a0=0005B2B2 a1=00C00328 d0=0000001C d1=00000014 d2=00000001
EVENT BG_BLOCKCOPY_HELPER_70720_ENTRY ... a0=0005B2B2 a1=00C00328 d0=0000001C d1=00000014 d2=00000001 bg_dirty=00000000
EVENT TITLE_BLOCK_5A58E_DONE ... a0=0005B712 a1=00C01728 d0=0000001C d1=00000000 d2=00000001 bg_dirty=007FFFF8
EVENT TITLE_HANDLER_3AC88_BEFORE_KICK ... fg_dirty=15800000 bg_dirty=007FFFF8
```

Reduced event counts:

- `BG_BLOCKCOPY_HELPER_70720_ENTRY`: `1`
- `BG_BLOCKCOPY_STORE_707BA`: `560`
- `BG_STAGING_WRITE` from helper PC `0x707BE`: `560`
- helper composed nonzero cell values: `560 / 560`
- helper unique composed values: `175`
- helper staged offsets: `0x0194..0x0B4A`

Parsed MAME dumps:

| Buffer snapshot | Nonzero words |
|---|---:|
| `bg_before_3ac54.bin` | `0 / 2048` |
| `bg_after_5a58e.bin` | `560 / 2048` |
| `bg_after_3ac88.bin` | `560 / 2048` |
| `fg_before_3ac54.bin` | `8 / 2048` |
| `fg_after_5a58e.bin` | `8 / 2048` |
| `fg_after_3ac88.bin` | `62 / 2048` |

Focused BG title-region parse (`0xFF401A + 0x0194` through `+0x0B4A`):

| Snapshot | Nonzero words | Unique words |
|---|---:|---:|
| before title block | `0` | `1` |
| after `0x05A58E` | `560` | `176` |
| at `0x3AC88` | `560` | `176` |

Runtime conclusion:

- New helper reached: **YES**.
- BG staging writes for destination `0x00C00328`: **YES**, exactly `560` stores for the `28x20` block.
- `bg_dirty` marked: **YES**, `0x00000000 -> 0x007FFFF8` by `0x05A58E` return and still `0x007FFFF8` at `0x3AC88`.
- The previous Build 0095 gap (`bg_dirty=0` at `0x3AC88`) is fixed for this title-art block.
- No crash was observed before the `0x3AC88` validation boundary; the normal release trace ran the 30s MAME workflow and produced `genesis_exec_summary.txt`.

Visual verification caveat:

- This runtime validation was headless/debugger-based and did not capture a new on-screen frame.
- Therefore, **USER MUST VERIFY** the final visual questions: whether the title art appears or materially advances on Plane B, whether RASTAN/sword are visible, and whether the large red TAITO logo is not duplicated/overlapped.
- The production-path evidence supports the expected visual improvement but does not replace manual/on-screen confirmation.

## Non-Regressions Checked

- FG clear/title-text staging remains active in the trace: `fg_dirty=0x15800000` at `0x3AC88`, and FG nonzero words increase from `8` before the title block to `62` by `0x3AC88`.
- This task did not modify FG/glyph code, input handling, crash handling, palette code, sprite code, preload/LUT code, or Start/C/A behavior.
- The known post-Start exception path was not investigated.

Visual non-regression status:

- FG clear non-regression: **runtime staging evidence YES**, visual confirmation still user-side.
- Title text intact: **runtime staging evidence YES**, visual confirmation still user-side.
- Large red TAITO not duplicated/overlapped: **not visually verified in this task**; **USER MUST VERIFY**.
- RASTAN/sword added: **not visually verified in this task**; **USER MUST VERIFY**.

## OPEN / CLOSED Issues Impact

- OPEN-001: touched; title-art BG block-copy staging gap fixed for the `0x05B0B2` / `0x00C00328` block, but do **not** close OPEN-001 on this evidence alone.
- OPEN-016: context only; no issue closure.
- OPEN-015: not touched.
- Closed issues touched: none.
- New issues opened: none.
- Issues closed: none.

## KNOWN_FINDINGS Impact

Option A - no `KNOWN_FINDINGS.md` update in this implementation task. The fix should be visually confirmed first; a later KF refinement can record the durable mechanism if the on-screen result matches the staged/dirty evidence.

## STOP Status

STOP triggered: **NO**.

Implementation is safely placeable from the production-path/staging perspective. Final visual success remains gated on Tighe's on-screen confirmation.
