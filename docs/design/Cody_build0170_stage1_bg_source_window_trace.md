# Cody - Build 0170 Stage 1 BG Source/Window Trace Candidate

**Date:** 2026-07-14
**Type:** Analysis-first runtime trace / implementation gate
**Baseline build inspected:** Build 0169
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0169.bin`
**SHA256:** `b8c87809fe84650b8c31b7b835469609034fca29cf43a4f2aeb669925acc1634`
**Scope:** Stage 1 post-landing BG terrain source/window/row trace only. No source/spec/tool/Makefile/ROM/invariant changes. No build. No PC090OJ, D00298, Exodus, READY/header, continue/game-over, input, broad VBlank, palette, or collision-fix work.

## Phase 0

Classification: **EXTENDING**. This task extends OPEN-017 / OPEN-001 gameplay graphics evidence and KF-038 long PC080SN BG-row aliasing. Relevant priors loaded: KF-038 (long BG rows alias in 32-row staging), KF-040 (Stage 1 BG painted by item-page strip path / raw column writers dynamically dead), KF-041 (Stage 1 tile preload/LUT source model), KF-042 (BG pass selector repaired), KF-010/KF-032 (PC080SN BG staging/commit model), OPEN-017, OPEN-001, OPEN-024 context.

Rediscovery Hazard HIGH findings touched: KF-038, KF-040, KF-041, KF-042. No contradiction detected.

Open issues touched: OPEN-017 and OPEN-001. OPEN-024 context only. No issues opened or closed. CLOSED issues touched: none.

Architecture compliance: **CONFIRMED**. Arcade code remains the program; this task only observed the translated Genesis helper/staging behavior and did not add scaffolding, alternate renderer, state forcing, or ROM changes.

## Evidence Inspected

Static / generated evidence:

- `apps/rastan-direct/src/tilemap_hooks.s`
- `build/genesis_postpatch.disasm.txt`
- `apps/rastan-direct/out/symbol.txt`
- `build/pc080sn_tile_vram_lut.bin`
- `dist/rastan-direct/rastan_direct_video_test_build_0169.bin`
- Prior terrain/input trace: `states/traces/build0169_postlanding_terrain_input_20260714_175544/`

New trace artifacts:

- Trace directory: `states/traces/build0170_stage1_bg_source_window_trace_20260714_182717/`
- Harness: `source_window_trace.lua`
- Transition sampler: `snapshot_transition.lua`
- Snapshots: `genesis_transition_snapshots.csv`
- Initial write/source event attempt: `genesis_bg_source_window_events.csv`
- All-write retry: `genesis_bg_allwrites_window.csv`

Note: this MAME run did not support `install_execute_tap` for the selected PCs (`EXEC_TAP_FAIL_*` rows in `genesis_bg_source_window_events.csv`). The decisive evidence therefore comes from staged-cell snapshots and source/destination slots, not execute taps.

## Prior Visible-Cell Baseline

The prior post-landing trace sampled Build 0169 at frame 820 with state `2/3/0`, player `X=0x0020`, player `Y=0x0070`, and camera/raw BG Y `0x0149`. The sampled arcade cells for the same visible window include:

| Sample | Plane col,row | Arcade BG code | Expected LUT slot |
|---|---:|---:|---:|
| `YELLOW_2_16` | `0,7` | `0x050C` | `0x00D3` |
| `BLACK_2_0` | `0,23` | `0x0602` | `0x01C8` |
| `MOUNTAIN_8_9` | `6,0` | `0x04AC` | `0x0073` |
| `YELLOW_24_20` | `22,11` | `0x055D` | `0x0123` |

At Build 0169 frame 820, those same staged BG cells instead held words such as `0x4281`, `0x425A`, `0x422C`, and `0x42EA`, indicating wrong Genesis tile slots for the visible terrain.

## Runtime Source / Window Timeline

The transition sampler shows the Stage 1 item strip path begins with the expected gameplay strip source and BG C-window destination:

| Frame | State | `a5@10A0` | item dest slot `0xFF10F8` | source slot `0xFF1100` | attr slot `0xFF1104` | Observation |
|---:|---|---:|---:|---:|---:|---|
| `476` | `2/2/4` | `0x00C0C000` | `0x00C00000` | `0x0000D31C` | `0x0002` | Before sampled cells populate |
| `477` | `2/2/4` | `0x00C0C000` | `0x00C00000` | `0x0000D31C` | `0x0002` | `YELLOW_2_16` becomes correct `0x40D3` |
| `478` | `2/2/4` | `0x00C0C004` | `0x00C00004` | `0x0000D31C` | `0x0002` | same cell is overwritten as `0x4281` |
| `483` | `2/2/4` | `0x00C0801C` | `0x00C0001C` | `0x0000D31C` | `0x0002` | `MOUNTAIN_8_9` becomes `0x422C` |
| `498` | `2/2/4` | `0x00C0C058` | `0x00C00058` | `0x0000DB1C` | `0x0002` | later gameplay strip block active |
| `536` | `2/2/4` | `0x00C0C0FC` | `0x00C000FC` | `0x0000F31C` | `0x0002` | sampled visible set now matches later wrong frame-820 values |
| `820` | `2/3/0` | `0x00C08100` | `0x00C00100` | `0x0000D31C` | `0x0002` | wrong terrain persists post-landing |

This proves the selected source family is the expected gameplay strip family (`0xD31C`, then `0xDB1C`, then `0xF31C`), not a missing gameplay tile residency and not an unrelated title/front-end source family.

## Exact Row-Alias Mechanism

`genesistan_hook_itempage_strip_blit` (`runtime_genesis_pc 0x71878`) reads one PC080SN BG column from the active source pointer and loops `64` rows:

```asm
move.w  0(%a2,%d1.w), %d0
or.l    %d7, %d0
moveq   #1, %d1
bsr     genesistan_hook_tilemap_bg_fill
adda.l  #0x00000100, %a0
addq.w  #1, %d2
cmpi.w  #64, %d2
```

The generic BG fill helper (`runtime_genesis_pc 0x7078C`, store at `0x70840`, post-write PC observed as `0x70844`) maps the PC080SN destination into the current 32-row Genesis BG staging buffer:

```asm
subi.l  #0x00C00000, %d2
lsr.l   #2, %d2
move.w  %d2, %d4
andi.w  #0x003F, %d4      ; col
move.w  %d2, %d5
lsr.w   #6, %d5
andi.w  #0x001F, %d5      ; row masked to 32 rows
move.w  %d3, 0(%a6,%d0.w)
```

Because the item strip writes `64` PC080SN rows but BG staging preserves only `32`, source/destination rows `32..63` alias onto rows `0..31` and overwrite the first half.

Concrete examples from Build 0169 ROM source and LUT:

| Visible cell | Source pointer | Correct row,col | Correct raw code | Correct slot/word | Later row,col | Later raw code | Later slot/word | Runtime result |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| `YELLOW_2_16` | `0xD31C` | `7,0` | `0x050C` | `0x00D3` / `0x40D3` | `39,0` | `0x06BB` | `0x0281` / `0x4281` | correct at frame `477`, overwritten by frame `478` |
| `BLACK_2_0` | `0xD31C` | `23,0` | `0x0602` | `0x01C8` / `0x41C8` | `55,0` | `0x0694` | `0x025A` / `0x425A` | final frame `820` word `0x425A` |
| `MOUNTAIN_8_9` | `0xD31C` | `0,6` | `0x04AC` | `0x0073` / `0x4073` | `32,6` | `0x0666` | `0x022C` / `0x422C` | final frame `820` word `0x422C` |

So the current translated runtime does not simply choose a lower wrong source window. It emits from the expected gameplay strip source, but the current 32-row staging representation allows the later half of the 64-row PC080SN column to overwrite the earlier half before the scrolled visible window samples it.

## Classification

**Classification: KF-038 gameplay generalization / 64-row PC080SN BG row alias.**

The first exact divergence is the representation boundary in `genesistan_hook_tilemap_bg_fill`: it collapses the long/tall PC080SN BG C-window column into `staged_bg_buffer` using `row & 0x1F`. The Stage 1 item-strip producer writes a 64-row BG column; rows `row+32` overwrite the row selected by the arcade visible window. The wrong visible terrain is therefore row-alias overwrite, not:

- missing PC080SN tile pattern residency;
- missing source-table relocation;
- wrong gameplay strip source family;
- FG/BG plane swap;
- palette-line mismatch;
- input handling;
- collision-map reader rebasing;
- PC090OJ or VBlank ownership.

## Build Gate Decision

Build 0170 was **not** produced.

The mechanism is proven, but the safe implementation boundary is not a narrow source-pointer or window-selection patch. A correct fix likely needs a design pass for a 64-row/tall PC080SN BG representation (or equivalent visible-window staging) for the gameplay/item-strip BG path, then a VBlank commit that selects the currently visible 32 Genesis rows according to scroll. A local one-line change to the generic 32-row row mask would risk regressing title/story/high-score screens, matching KF-038's prior warning.

## Recommended Smallest Implementation Boundary

Recommended next implementation design boundary:

1. Preserve arcade PC080SN BG C-window semantics for the gameplay item-strip path by keeping at least the 64-row source/destination distinction until visible-window selection.
2. Do not globally change `genesistan_hook_tilemap_bg_fill` row masking without deciding how title/story/high-score 32-row wrapping should remain stable.
3. Treat `genesistan_hook_itempage_strip_blit` + `genesistan_hook_tilemap_bg_fill` + `vdp_commit_bg_strips_if_dirty` as the minimum coherent design surface.
4. Validate with the same sampled cells: `YELLOW_2_16` must retain `0x40D3`/slot `0x00D3`, `BLACK_2_0` must retain the LUT slot for raw `0x0602`, and `MOUNTAIN_8_9` must retain the LUT slot for raw `0x04AC` after the 64-row strip completes.

## Required Correction to Prior Build Wording

Do not describe Build 0169 as a valid “walk right” or input-response result. Corrected wording:

- Build 0167 was more functional than 0168 in user testing and showed automatic movement/rightward behavior without input, but it was not a valid collision fix because mapped collision was empty and the player fell through.
- Build 0168 showed automatic walking-left animation after contact/landing, uncontrollable/sky-walking behavior; collision was populated but overcorrected/wrong production model.
- Build 0169 shows automatic walking-left with zero input; directional/jump/attack inputs were ineffective in the scripted trace; real Genesis freezes instantly at ground contact while BlastEm/MAME continue.

## Open / Closed Issues Impact

- Open issues touched: OPEN-017, OPEN-001.
- Context only: OPEN-024.
- New issues opened: none.
- Issues closed: none.
- Intentionally deferred: implementation of tall/virtual BG representation, collision byte-equivalence, real Genesis contact freeze, input/control, PC090OJ/READY/header, D00298, Exodus loop, continue/game-over, VBlank/rolling bar/slowdown.

## KNOWN_FINDINGS Impact

Option C: update KF-038. This task promotes the previously `POTENTIALLY_GENERAL` gameplay/demo portion of KF-038 to gameplay-proven evidence for Stage 1 item-strip BG. The item-description evidence remains valid; Build 0169 now proves the same long-row alias mechanism affects gameplay terrain.

## STOP Status

STOP triggered: **YES for implementation/build**. Exact mechanism is proven, but a safe Build 0170 fix is not bounded to a small source/window patch.
