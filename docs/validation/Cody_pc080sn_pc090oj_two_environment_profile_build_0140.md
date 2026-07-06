# Cody - PC080SN/PC090OJ Two-Environment Logical-Operation Profiling Gate

**Date:** 2026-07-06  
**Type:** Runtime evidence correction / bounded trace analysis only  
**Build under test:** Build 0140, `dist/rastan-direct/rastan_direct_video_test_build_0140.bin`  
**Build SHA256:** `f6e63eb3e3a6d5e82caf9e151ef2eb1c23418633ee7118adad51f1c2081a135c`  
**Correction outcome:** **A - New Build 0140 Genesis capture completed with contributor-level DISPLAY_OFF accounting and direct Build 0140 PC090OJ measurements.**

## Scope

This correction pass is evidence only. No source, spec, tool, Makefile, ROM, invariant, numbered build, VBlank/DISPLAY pipeline, bookmark, DISPLAY_ON/OFF ordering, frame model, or permanent diagnostic/scaffolding changes were made.

This report was amended in place. It supersedes the earlier over-strong Genesis-side conclusions in this file. The original-arcade portion was not rerun in this correction task.

Allowed artifacts created for this correction pass:

- `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/capture_build0140_decomp.lua`
- `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/build0140_decomp_debug.cmd`
- `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/run_capture.sh`
- `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/native_debug_trace.log`
- `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/lua_events.log`
- `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/build0140_decomp_analysis.json`
- `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/build0140_decomp_analysis.md`
- `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/screenshots/`

Previous evidence retained as background only:

- `states/traces/pc080sn_pc090oj_two_environment_profile_build_0140_20260706_124546/`
- `states/traces/fg_vertical_strip_narrow_commit_build_0140_autonomous_20260705_154323/`

## Phase 0

Mandatory architecture documents were read before the correction capture:

- `RULES.md`
- `ARCHITECTURE.md`
- `AGENTS_LOG.md` latest relevant tail

Relevant priors loaded:

- Build 0140 FG narrow-commit validation: `docs/validation/Cody_fg_vertical_strip_narrow_commit_build_0140_runtime.md`
- Original arcade PC080SN operation census: `docs/design/Cody_pc080sn_operation_census.md`
- Original arcade PC080SN trace: `states/traces/pc080sn_operation_census_20260704_132001/`
- PC090OJ candidate-bitset evidence: `docs/design/Cody_build0136_pc090oj_candidate_bitset.md`
- PC090OJ DISPLAY_OFF split evidence: `docs/design/Cody_build0138_pc090oj_displayoff_split.md`

No contradiction with the arcade-program / Genesis-helper architecture was found.

## Build Verification

Build 0140 SHA was verified from disk in the prior profiling pass and remains the build under test:

```text
f6e63eb3e3a6d5e82caf9e151ef2eb1c23418633ee7118adad51f1c2081a135c  dist/rastan-direct/rastan_direct_video_test_build_0140.bin
```

## Address Mapping Discipline

All arcade-to-Genesis correlations in this report use `build/rastan-direct/address_map.json`. No arithmetic offset is used as authority.

Genesis-only runtime addresses measured in the correction trace are labeled `runtime_genesis_pc` and are not mapped back to arcade code:

| Address | Space | Mapping result |
|---|---|---|
| `0x0700C2` | `runtime_genesis_pc` | `genesis_only`, `_vblank_service` |
| `0x0700CE` | `runtime_genesis_pc` | `genesis_only`, DISPLAY_OFF setup call site |
| `0x0700E6` | `runtime_genesis_pc` | `genesis_only`, DISPLAY_ON setup call site |
| `0x071708` | `runtime_genesis_pc` | `genesis_only`, `vdp_commit_fg_narrow_strips` |
| `0x072112` | `runtime_genesis_pc` | `genesis_only`, `vdp_prepare_sprites` |
| `0x072124` | `runtime_genesis_pc` | `genesis_only`, `vdp_commit_sprites_vram` |
| `0x072168` | `runtime_genesis_pc` | `genesis_only`, PC090OJ object/candidate scan |
| `0x072312` | `runtime_genesis_pc` | `genesis_only`, SAT link-chain construction |
| `0x072380` | `runtime_genesis_pc` | `genesis_only`, sprite tile DMA/residency loop |
| `0x072442` | `runtime_genesis_pc` | `genesis_only`, SAT DMA setup/trigger |

## Corrected Genesis Build 0140 Evidence

Primary correction evidence source:

- Trace directory: `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/`
- Native debugger trace: `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/native_debug_trace.log`
- Lua event log: `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/lua_events.log`
- Reduced evidence: `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/build0140_decomp_analysis.md`
- Reduced JSON: `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/build0140_decomp_analysis.json`
- Screenshot contact sheet: `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/screenshots/contact_sheet.png`

The autonomous run completed through Lua frame `2401` and parsed `2245` native VBlank entries. It captured title/frontend, story/frontend, and stable item-description frontend states. It did not produce a separate high-score state before the autonomous run ended; that is a capture coverage limitation, not a runtime contradiction.

Important correction versus the previous version of this report:

- The previous Build 0140 Genesis evidence was **not** sufficient to call the full Genesis side complete because it leaned too heavily on the older FG narrow trace and older PC090OJ counts.
- The previous "Branch A strongest combined support" statement is **withdrawn**.
- The previous implication that one selected FG descriptor proves the first optimization target is **withdrawn**.
- Build 0136/0138 PC090OJ counts remain useful historical context, but they are **not** relabeled as direct Build 0140 runtime measurements.
- This correction pass does **not** rank or select Branch A/B/C/D.

## Representative Screenshots
| Lua frame | Native frame used for costs | State | Screenshot | Reason |
|---:|---:|---|---|---|
| 180 | 100 | `0/1/0` | `screenshots/frame_00180_early_frontend.png` | full title/frontend frame after state 0/1/0 stabilized |
| 480 | 250 | `0/1/2` | `screenshots/frame_00480_coin_prompt_window.png` | story/text frontend frame after state 0/1/2 page visible |
| 960 | 960 | `2/2/6` | `screenshots/frame_00960_story_or_item_candidate.png` | stable item-description frontend frame with PC090OJ active count 0x20 |

## Boundary Cycles And Sum Checks

| Native frame | State | DISPLAY_OFF cycle | DISPLAY_ON cycle | Total interval cycles | Sum of Table A contributors | Unattributed cycles | Unattributed % |
|---:|---|---:|---:|---:|---:|---:|---:|
| 100 | `0/1/0` | 19260355 | 19276705 | 16350 | 16350 | 34 | 0.21 |
| 250 | `0/1/2` | 40125275 | 40141625 | 16350 | 16350 | 34 | 0.21 |
| 960 | `2/2/6` | 134602155 | 134618703 | 16548 | 16548 | 34 | 0.21 |

## Contributor Runtime PC Ranges

| Contributor | Entry runtime_genesis_pc | Exit / return runtime_genesis_pc | Notes |
|---|---|---|---|
| VDP/display control setup after DISPLAY_OFF | 0x0700CE | 0x0700D6 | includes register-1 DISPLAY_OFF setup/write call |
| tile-pattern/tile commit | 0x0700D6 / 0x07010E | 0x0700DA / 0x070136 | no useful transfer in selected frames; zero CPU data words |
| BG broad presentation | 0x0700DA / 0x070138 | 0x0700DE / 0x070184 | no dirty BG rows in selected frames |
| FG narrow descriptor presentation | 0x0700DE / 0x071708 | 0x07177A / 0x070186 | routine entered; descriptor count zero in selected frames |
| FG broad presentation | 0x070186 | 0x0701D2 / 0x0700E2 | no dirty FG rows in selected frames |
| sprite-pattern residency checks | 0x072124 / 0x072380 | 0x072442 | 80-slot descriptor/residency scan; no sprite tile DMA triggers in selected frames |
| sprite-pattern DMA setup/transfer/wait | 0x0723C6 | 0x072436 | zero calls in selected frames |
| SAT DMA setup/transfer/wait | 0x072442 | 0x0724D2 | one SAT DMA per selected frame |
| other sprite commit work | 0x0724D2 | 0x0700E6 | dirty cleanup plus sprite commit call/return/control glue |
| final display-control work before DISPLAY_ON | 0x0700E6 | 0x0700EE | register-1 DISPLAY_ON setup/write call |

## Evidence File Sizes

| File | Bytes |
|---|---:|
| `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/native_debug_trace.log` | 744037379 |
| `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/lua_events.log` | 68472 |
| `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/build0140_decomp_analysis.json` | 18008 |
| `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/build0140_decomp_analysis.md` | 7362 |
| `states/traces/build0140_genesis_displayoff_pc090oj_decomp_20260706_131738/screenshots/` frame PNGs | 10 files |

## Table A - DISPLAY_OFF Decomposition
| Native frame | State | Contributor | Calls | Exclusive cycles | Inclusive cycles | CPU VDP words | DMA operations | DMA words | Interval % | Classification |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|---|
| 100 | `0/1/0` | VDP/display control setup after DISPLAY_OFF | 1 | 96 | 96 | 1 | 0 | 0 | 0.59 | VDP control |
| 100 | `0/1/0` | tile-pattern/tile commit | 1 | 60 | 60 | 0 | 0 | 0 | 0.37 | CPU-driven VDP transfer |
| 100 | `0/1/0` | BG broad presentation | 1 | 64 | 64 | 0 | 0 | 0 | 0.39 | CPU-driven VDP transfer |
| 100 | `0/1/0` | FG narrow descriptor presentation | 1 | 296 | 296 | 0 | 0 | 0 | 1.81 | CPU-driven VDP transfer |
| 100 | `0/1/0` | FG broad presentation | 1 | 30 | 30 | 0 | 0 | 0 | 0.18 | CPU-driven VDP transfer |
| 100 | `0/1/0` | sprite-pattern residency checks inside commit | 1 | 11088 | 11088 | 0 | 0 | 0 | 67.82 | CPU computation |
| 100 | `0/1/0` | sprite-pattern DMA setup/transfer/wait CPU-visible cost | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | VDP DMA setup/wait |
| 100 | `0/1/0` | SAT DMA setup/transfer/wait CPU-visible cost | 1 | 458 | 458 | 0 | 1 | 92 | 2.8 | VDP DMA setup/wait |
| 100 | `0/1/0` | other sprite commit work | 1 | 4128 | 4128 | 0 | 0 | 0 | 25.25 | CPU computation |
| 100 | `0/1/0` | final display-control work before DISPLAY_ON | 1 | 96 | 96 | 1 | 0 | 0 | 0.59 | VDP control |
| 100 | `0/1/0` | unattributed overhead | 0 | 34 | 34 | 0 | 0 | 0 | 0.21 | mixed |
| 250 | `0/1/2` | VDP/display control setup after DISPLAY_OFF | 1 | 96 | 96 | 1 | 0 | 0 | 0.59 | VDP control |
| 250 | `0/1/2` | tile-pattern/tile commit | 1 | 60 | 60 | 0 | 0 | 0 | 0.37 | CPU-driven VDP transfer |
| 250 | `0/1/2` | BG broad presentation | 1 | 64 | 64 | 0 | 0 | 0 | 0.39 | CPU-driven VDP transfer |
| 250 | `0/1/2` | FG narrow descriptor presentation | 1 | 296 | 296 | 0 | 0 | 0 | 1.81 | CPU-driven VDP transfer |
| 250 | `0/1/2` | FG broad presentation | 1 | 30 | 30 | 0 | 0 | 0 | 0.18 | CPU-driven VDP transfer |
| 250 | `0/1/2` | sprite-pattern residency checks inside commit | 1 | 11088 | 11088 | 0 | 0 | 0 | 67.82 | CPU computation |
| 250 | `0/1/2` | sprite-pattern DMA setup/transfer/wait CPU-visible cost | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | VDP DMA setup/wait |
| 250 | `0/1/2` | SAT DMA setup/transfer/wait CPU-visible cost | 1 | 458 | 458 | 0 | 1 | 92 | 2.8 | VDP DMA setup/wait |
| 250 | `0/1/2` | other sprite commit work | 1 | 4128 | 4128 | 0 | 0 | 0 | 25.25 | CPU computation |
| 250 | `0/1/2` | final display-control work before DISPLAY_ON | 1 | 96 | 96 | 1 | 0 | 0 | 0.59 | VDP control |
| 250 | `0/1/2` | unattributed overhead | 0 | 34 | 34 | 0 | 0 | 0 | 0.21 | mixed |
| 960 | `2/2/6` | VDP/display control setup after DISPLAY_OFF | 1 | 96 | 96 | 1 | 0 | 0 | 0.58 | VDP control |
| 960 | `2/2/6` | tile-pattern/tile commit | 1 | 60 | 60 | 0 | 0 | 0 | 0.36 | CPU-driven VDP transfer |
| 960 | `2/2/6` | BG broad presentation | 1 | 64 | 64 | 0 | 0 | 0 | 0.39 | CPU-driven VDP transfer |
| 960 | `2/2/6` | FG narrow descriptor presentation | 1 | 296 | 296 | 0 | 0 | 0 | 1.79 | CPU-driven VDP transfer |
| 960 | `2/2/6` | FG broad presentation | 1 | 30 | 30 | 0 | 0 | 0 | 0.18 | CPU-driven VDP transfer |
| 960 | `2/2/6` | sprite-pattern residency checks inside commit | 1 | 11286 | 11286 | 0 | 0 | 0 | 68.2 | CPU computation |
| 960 | `2/2/6` | sprite-pattern DMA setup/transfer/wait CPU-visible cost | 0 | 0 | 0 | 0 | 0 | 0 | 0.0 | VDP DMA setup/wait |
| 960 | `2/2/6` | SAT DMA setup/transfer/wait CPU-visible cost | 1 | 458 | 458 | 0 | 1 | 128 | 2.77 | VDP DMA setup/wait |
| 960 | `2/2/6` | other sprite commit work | 1 | 4128 | 4128 | 0 | 0 | 0 | 24.95 | CPU computation |
| 960 | `2/2/6` | final display-control work before DISPLAY_ON | 1 | 96 | 96 | 1 | 0 | 0 | 0.58 | VDP control |
| 960 | `2/2/6` | unattributed overhead | 0 | 34 | 34 | 0 | 0 | 0 | 0.21 | mixed |

## Table B - PC080SN Presentation
| Native frame | State | Family/path | Semantic ops | Dirty rows/descriptors | Logical slots | CPU VDP words | DMA words | Cycles | Amplification |
|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| 100 | `0/1/0` | BG broad row commit | 0 | 0 | 0 | 0 | 0 | 64 | 0 |
| 100 | `0/1/0` | FG narrow descriptor commit | 0 | 0 | 0 | 0 | 0 | 296 | 0 |
| 100 | `0/1/0` | FG broad row commit | 0 | 0 | 0 | 0 | 0 | 30 | 0 |
| 250 | `0/1/2` | BG broad row commit | 0 | 0 | 0 | 0 | 0 | 64 | 0 |
| 250 | `0/1/2` | FG narrow descriptor commit | 0 | 0 | 0 | 0 | 0 | 296 | 0 |
| 250 | `0/1/2` | FG broad row commit | 0 | 0 | 0 | 0 | 0 | 30 | 0 |
| 960 | `2/2/6` | BG broad row commit | 0 | 0 | 0 | 0 | 0 | 64 | 0 |
| 960 | `2/2/6` | FG narrow descriptor commit | 0 | 0 | 0 | 0 | 0 | 296 | 0 |
| 960 | `2/2/6` | FG broad row commit | 0 | 0 | 0 | 0 | 0 | 30 | 0 |

## Table C - PC090OJ Activity
| Native frame | State | Producer writes | Unique records written | Position writes | Tile/attribute writes | Activations | Deactivations | Persistent candidates scanned | Decoded records | Drawables emitted | Active sprites | SAT shifts | Tile-DMA words | SAT-DMA words |
|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | `0/1/0` | 0 | 0 | 0 | 0 | 23 | 0 | 42 | 42 | 23 | 23 | 22 | 0 | 92 |
| 250 | `0/1/2` | 0 | 0 | 0 | 0 | 23 | 0 | 42 | 42 | 23 | 23 | 22 | 0 | 92 |
| 960 | `2/2/6` | 0 | 0 | 0 | 0 | 32 | 0 | 38 | 38 | 32 | 32 | 31 | 0 | 128 |
| Lua `66` | producer burst | 338 | 86 | 169 | 169 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a | n/a |

## Table D - PC090OJ CPU Costs
| Native frame | State | Candidate traversal cycles | Decode/conversion cycles | Drawable emission cycles | SAT packing cycles | Link construction cycles | Total pre-DISPLAY_OFF sprite cycles | Inside-DISPLAY_OFF sprite cycles |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 100 | `0/1/0` | 31626 | 12562 | 2162 | 0 | 12814 | 77276 | 15674 |
| 250 | `0/1/2` | 31626 | 12562 | 2162 | 0 | 12814 | 77276 | 15674 |
| 960 | `2/2/6` | 38722 | 12300 | 3008 | 0 | 13804 | 85946 | 15872 |

## Notes
- Native frame numbers are derived from `EV VBLANK_ENTRY` ordinals in the MAME debugger trace. Lua frame numbers are the autonomous screenshot frame counter.
- PC090OJ producer writes occurred as a burst before the representative stable frames; stable selected frames primarily measure scan/link/DMA presentation cost.
- FG narrow descriptor presentation was zero in these selected frames (`FG_NARROW_CPU_WORD=0`), so these frames do not support selecting the FG narrow path as first target by themselves.

## Original Arcade Evidence Status

The original-arcade evidence from the earlier PC080SN operation census remains background evidence only:

- `docs/design/Cody_pc080sn_operation_census.md`
- `states/traces/pc080sn_operation_census_20260704_132001/pc080sn_segmented_census.md`

That capture covered frontend/startup, partial manual Stage 1 gameplay, and post-gameplay attract. It still supports the existence and rough frequency of PC080SN operation families, but it does not satisfy the stricter two-environment gate by itself.

The stricter original-arcade readback-watchpoint portion remains blocked by the same named dependency:

```text
No deterministic original-arcade Stage 1 replay/save-state artifact was available, so the stricter original-arcade readback-watchpoint pass on 0xC08000/0xC00000/0xD00000/0x200000 could not be rerun without manual input and without changing capture conditions.
```

This correction task intentionally did not solve that original-arcade dependency.

## Branch Evidence Correction

No Branch A/B/C/D implementation ranking is selected from this corrected report.

Corrected interpretation:

- Build 0140 Genesis DISPLAY_OFF cost is now directly decomposed for representative frontend frames.
- In the selected representative frames, PC080SN broad/narrow CPU VDP presentation writes are idle (`0` CPU VDP data words), while PC090OJ scan/link/SAT presentation remains active.
- PC090OJ object producer writes are directly observed in Build 0140 as an early producer burst (`338` writes across `86` records at Lua frame `66`), not as a continuous per-frame producer write cost in the selected stable frames.
- PC090OJ pre-DISPLAY_OFF scan/decode/link work is measured directly in Build 0140 and remains outside the DISPLAY_OFF interval.
- PC090OJ inside-DISPLAY_OFF cost is dominated by sprite-pattern residency checks and sprite cleanup/SAT work in the selected frames, with SAT DMA words matching active sprite counts (`23 -> 92 words`, `32 -> 128 words`).
- The selected frames do not prove FG narrow presentation is the dominant or first replacement target; FG narrow descriptor presentation had zero logical slots/data words in these selected samples.

## Outcome Determination

**Correction Outcome A** is selected for the correction task:

```text
New Build 0140 Genesis capture completed with contributor-level DISPLAY_OFF accounting and direct Build 0140 PC090OJ measurements.
```

The broader two-environment profiling gate remains incomplete because the original-arcade deterministic replay/readback-watchpoint dependency was not solved here.

This report therefore records corrected Genesis-side evidence, not a final cross-environment implementation target.

## Recommendation

No implementation is recommended from this corrected gate alone.

If another profiling pass is authorized, the narrowest useful follow-up is to solve the original-arcade deterministic replay/save-state dependency, then rerun the stricter readback-watchpoint pass for the same operation families. Without that, implementation ranking should remain provisional.

## Open / Closed Issues Impact

- OPEN-001: context; graphics/performance/rendering evidence, no status change.
- OPEN-016 and related PC080SN text/strip work: context only.
- PC090OJ sprite work: context only.
- New issues opened: none.
- Issues closed: none.

## KNOWN_FINDINGS Impact

Option A - no `KNOWN_FINDINGS.md` update. This correction pass records measurement-level profiling evidence and withdraws over-strong branch-ranking language; it does not establish a new durable mechanism.

## STOP Status

STOP triggered: **NO**.

Genesis correction capture completed. The original-arcade replay/readback-watchpoint dependency remains outstanding and explicitly limits the broader two-environment gate.
