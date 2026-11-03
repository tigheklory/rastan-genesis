# Cody - Stage 1 FG Progression Restoration and Build 0215/256

**Date:** 2026-07-19
**Type:** Targeted implementation + numbered build + evidence
**Branch / HEAD baseline:** `rastan-direct-proposal`, HEAD `5668c6e` per prompt baseline
**Accepted baseline:** Build 0213/256, `dist/rastan-direct/rastan_direct_video_test_build_0213.bin`, SHA256 `4cb766d5866dd2950e8b177c961549e3819bc98c5ecbddd56c2f6d3050d6316b`
**Comparison-only build:** Build 0214/192, SHA256 `1c51a28e453a7f628a8691490ecb96f875b309ba8801fc5b6833b03b04ffac96`, preserved but not used as gameplay baseline
**Produced build:** Build 0215/256, `dist/rastan-direct/rastan_direct_video_test_build_0215.bin`, SHA256 `10e5307fae240ae418b31b66df0cabe267785a3cd5e68d08f69a21e7b740e99d`
**Scope:** Restore Stage 1 gameplay FG source progression without touching PC090OJ, BG, collision, scroll, palette, sprite semantics, black-band handling, or unrelated visual issues. No existing numbered build was deleted or overwritten.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded from `KNOWN_FINDINGS.md`: KF-038 (long PC080SN row-depth/tall staging family), KF-040 (gameplay raw BG/FG column writers are dynamically dead on Genesis; live output is routed through helper paths), KF-041 (Stage 1 runtime gameplay tile/LUT source model), KF-039/KF-036 (mapped work-RAM and explicit rebasing discipline), KF-010 (BG/FG staging and plane mapping), KF-011/KF-013 (VBlank ownership), and KF-067/KF-066 as regression context for lizards/HUD/palette. HIGH rediscovery-hazard findings touched: KF-038, KF-040, KF-041, KF-039. No contradiction of a CONFIRMED/STRONG finding was detected.

Open issues touched: OPEN-017 (primary gameplay bring-up), OPEN-001 and OPEN-024 as visual/sprite context. Closed issues touched: none. No issue was opened or closed.

Architecture compliance: **CONFIRMED**. The arcade code remains the program. The change is a Genesis helper translation at an existing gameplay FG staging boundary, returning to arcade flow and preserving the staging -> VBlank commit model.

## Recovered State

Build 0213/256 is the gameplay baseline for this task. Build 0214/192 is preserved but intentionally not used as the gameplay baseline because the mirror-record cap is a comparison artifact and can drop lizard records. The initial rolling ROM before this task matched Build 0214; Build 0215 became the rolling ROM only after the successful release.

Pre-task build counter: `214`. Post-task build counter: `215`.

## Original Arcade FG Progression Path

The Stage 1 gameplay foreground progression is owned by the arcade PC080SN source-table timeline:

- `arcade_pc 0x0502CC`: initializes the source pointer family as `SRC[seg] = 0x1691C + seg*0x22C0 + stage*0x40`.
- `arcade_pc 0x0558C6/0x0558C8`: advances source pointers by `+4` as columns/pages progress.
- `arcade_pc 0x055904`: rebuilds runtime block pointers from the source table.
- `arcade_pc 0x0559B2`: consumes the rebuilt block pointer plus `colidx = a5@0x10CA` and row offset.

The relevant mapped Genesis WRAM tables are:

- Source pointer table: `Genesis_WRAM 0x00FF1000`
- Rebuilt block pointer table: `Genesis_WRAM 0x00FF1040`
- Copied word/attr table: `Genesis_WRAM 0x00FF1080`

## JSON Mapping Evidence

All arcade-to-Genesis code addresses below were checked through `build/rastan-direct/address_map.json` segment ranges:

| Arcade address | Genesis/runtime address | Map class |
|---|---:|---|
| `arcade_pc 0x0502CC` | `runtime_genesis_pc 0x0504CC` | `arcade_copy` |
| `arcade_pc 0x0558C6` | `runtime_genesis_pc 0x055AC6` | `arcade_copy` |
| `arcade_pc 0x0558C8` | `runtime_genesis_pc 0x055AC8` | `patched_site`, `0x0010D000 -> 0x00FF1000` |
| `arcade_pc 0x055904` | `runtime_genesis_pc 0x055B04` | `patched_site`, descriptor rebuild hook |
| `arcade_pc 0x05590A` | `runtime_genesis_pc 0x055B0A` | `patched_site`, `0x0010D040 -> 0x00FF1040` |
| `arcade_pc 0x055910` | `runtime_genesis_pc 0x055B10` | `patched_site`, `0x0010D080 -> 0x00FF1080` |
| `arcade_pc 0x055968` | `runtime_genesis_pc 0x055B68` | `patched_site` |
| `arcade_pc 0x055990` | `runtime_genesis_pc 0x055B90` | `patched_site`, live Stage 1 FG helper boundary note |
| `arcade_pc 0x0559B2` | `runtime_genesis_pc 0x055BB2` | `arcade_copy` |

No address in this table is used as proof by manual `+0x200` arithmetic.

## Genesis Build 0213 Path

Build 0213 already maintained the relocated runtime tables. A scripted right-held MAME trace shows `src0` advancing through `Genesis_WRAM 0x00FF1000`, for example:

- Frame `329`: `src0=0x00016920`, `ptr0=0x00001200`
- Frame `1600`: `src0=0x00016988`, `ptr15=0x00002224`
- Frame `1800`: `src0=0x00016994`, `ptr15=0x00002224`

However, the pre-0215 `genesistan_stage_fg_src_column` did not consume those rebuilt pointer tables. It recomputed a static source from the folded destination-derived group, so once the destination wrapped/folded inside the Genesis-visible C-window, earlier foreground/floor source groups were replayed.

## First Proven Divergence

The first implementation divergence is inside `genesistan_stage_fg_src_column`: the helper selected foreground source data from a recomputed `FG_SRC_BASE_GEN + group*4` model instead of the arcade-owned rebuilt pointer table at `Genesis_WRAM 0x00FF1040` plus `a5@0x10CA`.

This is a source-progression bug in the helper, not a VBlank commit bug, not a tile-cache/palette issue, not a PC090OJ issue, and not a Build 0214 mirror-count artifact.

## Implementation Boundary

The only source behavior changed was `apps/rastan-direct/src/tilemap_hooks.s`, inside `genesistan_stage_fg_src_column`.

The helper now:

- Uses `a5@0x10A0` only for the destination column, folded into `HW_ADDRESS 0x00C08000` as before.
- Uses `a5@0x10CA & 3` as the source column index.
- Reads `PC080SN_DESC_REBUILD_PTR_TABLE = Genesis_WRAM 0x00FF1040` for each segment.
- Validates rebuilt pointers in `[0x00000200, 0x00060000)` before dereference.
- Preserves the existing 64-row tall FG backing route through `genesistan_hook_tilemap_fg_fill_tall` and the normal VBlank projection/commit path.

No source/spec/Makefile/PC090OJ/BG/collision/palette/scroll code was intentionally changed for behavior. The canonical opcode coverage invariant was updated after the postpatch gate reported the mechanical new coverage value.

## Build Attempts

The release target was invoked three times in this task:

- Attempt 1 stopped before numbered artifact production at link time because the new helper used `.Lfgc_done` before the label existed. The counter remained `214`; no Build 0215 artifact was produced.
- Attempt 2 stopped before numbered artifact production at the postpatch invariant gate. Observed coverage was `0x182AFC` with opcode_replace count `215`. The counter remained `214`; no Build 0215 artifact was produced.
- Attempt 3 passed with the corrected source and paired canonical invariant values.

Final release command:

```bash
source tools/setup_env.sh && PC090OJ_MIRROR_RECORDS=256 RASTAN_GAMEPLAY_HUD_SPRITES=0 make -C apps/rastan-direct release
```

Final result:

- Canonical gate: `GATE_PASS`
- Counter: `214 -> 215`
- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0215.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `10e5307fae240ae418b31b66df0cabe267785a3cd5e68d08f69a21e7b740e99d`
- Size: `1,583,868` bytes
- Rolling/numbered `cmp`: byte-identical
- Config proof: generated `apps/rastan-direct/out/pc090oj_config.inc` records `PC090OJ_MIRROR_RECORDS=256` and `RASTAN_GAMEPLAY_HUD_SPRITES=0`.

## Evidence Artifacts

Primary evidence directory:

`states/traces/build0215_fg_progression_restoration_20260719_153538/`

Key files:

- `build0215_build_info.txt`
- `reduced_findings.md`
- `build0213_fg_progression_right_table_probe.csv`
- `build0215_fg_progression_right_table_probe.csv`
- `build0213_fg_progression_column_hash_probe.csv`
- `build0215_fg_progression_column_hash_probe.csv`
- `build0213_snapshots.csv`
- `build0215_snapshots.csv`
- `snaps_build0213/build0213_f429.png`
- `snaps_build0213/build0213_f1000.png`
- `snaps_build0213/build0213_f1400.png`
- `snaps_build0213/build0213_f1800.png`
- `snaps_build0215/build0215_f429.png`
- `snaps_build0215/build0215_f1000.png`
- `snaps_build0215/build0215_f1400.png`
- `snaps_build0215/build0215_f1800.png`

## Before/After Runtime Evidence

The table-progression trace confirms both builds reach Stage 1 and both have live arcade-owned source-table progression:

| Frame | Build | State | Dest | Strip `10CA` | Page `10CC` | `src0` | `ptr0` | `ptr15` | Tall nonzero | FG nonzero |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 329 | 0213 | `2/2/4` | `C0C00C` | `0000` | `0001` | `00016920` | `00001200` | `00002248` | 192 | 12 |
| 329 | 0215 | `2/2/4` | `C0C00C` | `0000` | `0001` | `00016920` | `00001200` | `00002248` | 192 | 12 |
| 1000 | 0213 | `2/3/0` | `C08100` | `0000` | `0000` | `0001695C` | `00001200` | `00002248` | 4032 | 2016 |
| 1000 | 0215 | `2/3/0` | `C08100` | `0000` | `0000` | `0001695C` | `00001200` | `00002248` | 4032 | 2016 |
| 1800 | 0213 | `2/3/0` | `C0C0E4` | `0002` | `000E` | `00016994` | `00001200` | `00002224` | 4096 | 2048 |
| 1800 | 0215 | `2/3/0` | `C0C0E0` | `0001` | `000E` | `00016994` | `00001200` | `00002224` | 4096 | 2048 |

Scripted absolute-frame hash comparison:

| Frame | Build 0213 tall hash | Build 0215 tall hash | Interpretation |
|---:|---:|---:|---|
| 429 | `57C2A48D` | `57C2A48D` | Pre-boundary content identical. |
| 1000 | `57C2A48D` | `57C2A48D` | Still identical before the progression-sensitive divergence. |
| 1400 | `FDB0232D` | `13A282C5` | Post-boundary content diverges. |
| 1800 | `FDB0232D` | `D8767E3A` | Build 0215 no longer reuses the same Build 0213 source result. |

Because the scripted runs are not lockstep after gameplay movement begins, these hashes prove helper-state divergence from the same scripted input window, not full arcade visual equivalence.

## Screenshot Observations

MAME snapshots were captured at frames `429`, `1000`, `1400`, and `1800` for both Build 0213 and Build 0215.

Observed comparison:

- Frame `429`: Build 0213 and Build 0215 remain visually equivalent at the first repeated-foreground boundary marker.
- Frame `1400`: Build 0213 shows a repeated wall/pillar-like foreground artifact near the player/lizard area; Build 0215 shows a different progression with the lizard and player visible and without that same replayed artifact.
- Frame `1800`: Build 0213 retains a repeated brown floor/foreground pattern; Build 0215 shows different lower content instead of simple replay.

Residual issue: Build 0215 still has gray/wrong lower-block content and is not visually arcade-correct. This task restores the source-progression boundary; it does not solve the remaining terrain/palette/scroll/black-band boundaries.

## Regression Notes

The scripted gameplay trace reaches Stage 1, scrolls, and shows Rastan plus at least one lizard in the Build 0215 snapshots. This is a smoke-level visual regression check only. It is not a dedicated lizard combat/damage, splat/item, bat, collision, or Nomad acceptance pass.

No existing numbered builds `0207..0214` were deleted, overwritten, or reused.

## Open / Closed Issues Impact

- Open issues touched: OPEN-017 (primary), OPEN-001 and OPEN-024 as context.
- New issues opened: none.
- Issues closed: none.
- Issues intentionally deferred: gray/wrong lower-block content, black display band, lizard combat/damage, splat/item palettes/scroll, bat palette, record 132, collision-map row-base/player retune, broader terrain visual correctness.

## KNOWN_FINDINGS Impact

Option C: KF-038 updated to record the Build 0215 Stage 1 FG horizontal/source-table progression mechanism and evidence. The finding remains OPEN because broader PC080SN terrain correctness and row-depth/projection issues are not fully closed.

## STOP

STOP triggered: **NO** for the final task outcome. Two earlier release attempts stopped before numbered artifact production, but the final corrected release passed and produced Build 0215.
