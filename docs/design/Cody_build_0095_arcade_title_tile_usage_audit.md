# Cody - Build 0095 Arcade Title Tile-Usage Audit

**Date:** 2026-06-23  
**Type:** Original arcade title-art tile usage audit + Build 0095 comparison  
**Arcade romset/driver:** MAME `rastan` / `Rastan (World Rev 1)`  
**Genesis comparison build:** Build 0095, `dist/rastan-direct/rastan_direct_video_test_build_0095.bin`, SHA `273508a23ddd7b37e10e7ba4a7355f78e95bbe539ba3145b4e844b59ace53ef6`  
**Scope:** Documentation/evidence only. No source/spec/tool/Makefile/ROM/invariant changes. No Genesis build. No implementation. OPEN-015 not touched.

## Phase 0

Classification: **EXTENDING** (OPEN-001). Loaded priors: `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest `AGENTS_LOG.md`, `docs/design/Andy_build_0095_taito_logo_producer_attribution.md`, `docs/design/Cody_original_arcade_attract_page_replacement_runtime.md`, and `docs/design/Cody_build_0095_3ad44_dispatch_fg_bg_split.md`.

Relevant priors respected: KF-010, KF-011, KF-013, KF-014, KF-028, KF-029, KF-030, KF-031. OPEN-016 is context; OPEN-015 remains do-not-touch. No contradiction detected.

## Evidence Artifacts

- Original arcade trace: `states/traces/original_arcade_title_tile_usage_audit_20260623_223832/`
- Build 0095 trace: `states/traces/build_0095_title_art_tile_usage_audit_20260623_223322/`
- Reduced tile-set artifact: `states/traces/build_0095_title_art_tile_usage_audit_20260623_223322/title_tile_usage_audit.json`
- Audit script output source: `tools/audit_vram_tile_usage.py`
- Original maincpu source image: `build/regions/maincpu.bin`, variant `world_rev1`, assembled from `roms/rastan.zip`

## Arcade Runtime Facts

The original arcade title handler reaches the initial title-art path:

```text
EVENT TITLE_HANDLER_03AA54_ENTRY ... s0=0000 s2=0000 s4=0001 cnt=0000
EVENT TITLE_BLOCK_05A38E_ENTRY ...
EVENT TITLE_HANDLER_03AA88_BEFORE_KICK ... s0=0000 s2=0001 s4=0000 cnt=0000
```

The static arcade path is:

```asm
03AA54: jsr 0x05A356
05A356: lea 0x05A6FA,%a0 ; jsr 0x059AD4 ; bsrw 0x05A38E ; rts
05A38E: movea.l #0x00C00328,%a1
05A394: lea 0x05B0B2,%a0
05A39A: move.w #28,%d0
05A39E: move.w #20,%d1
05A3A2: move.w #1,%d2
05A3A6: bsrw 0x05A4DE
05A4DE: block copy: write attr word, then tile word, row stride 0x100
```

The original arcade debugger dump proves the PC080SN BG region starting at `0x00C00328` matches source table `0x05B0B2` exactly for all `28x20` cells: **0 mismatches**. The dumped PC080SN FG and PC090OJ sprite RAM were captured, but the complete title-logo/wordmark/sword source table is the PC080SN BG block above. PC090OJ is not the source path for these enumerated title-art elements.

## Arcade Source Table And Layer

Authoritative title-art source:

| Element | Source | Destination | Layer/path | Notes |
|---|---|---|---|---|
| Complete title-art block | `maincpu 0x05B0B2`, `28x20` | `0x00C00328` | PC080SN BG C-window | Runtime dump matches source table exactly |
| Red TAITO logo | geometry-derived rows `18..19`, cols `13..14` inside `0x05B0B2` | same block | PC080SN BG | `4` unique nonblank tile codes |
| Sword | geometry-derived center corridor cols `13..16`, rows `0..19` inside `0x05B0B2` | same block | PC080SN BG | Source table is composed art; sword overlaps center-logo area |
| RASTAN wordmark | geometry-derived rows `2..12` inside `0x05B0B2` | same block | PC080SN BG | Full band includes central sword overlap; conservative wordmark-only approximation excludes cols `13..16` |

Important limitation: the original table is a single composed PC080SN art block. It does not label semantic sub-elements. The per-element sets below are geometry-derived for audit/diff purposes; the authoritative source set for implementation coverage is the full `0x05B0B2` table.

## Arcade Tile-Code Sets

Full `0x05B0B2` title-art block: `174` unique nonblank codes, range `0x21B6..0x2570`. The full set is in `title_tile_usage_audit.json` under `full_title_0x5B0B2_28x20`.

Red TAITO logo set, rows `18..19`, cols `13..14`:

```text
0x22CB 0x22CC 0x22CD 0x22CE
```

Sword center-corridor set, cols `13..16`, rows `0..19` (`44` unique nonblank):

```text
0x21B6 0x21B7 0x21C2 0x21C3 0x2253 0x225A 0x22CB 0x22CC
0x22CD 0x22CE 0x24CB 0x24CC 0x24CF 0x24D0 0x24D6 0x24D7
0x24D8 0x24E7 0x24E8 0x24E9 0x24EA 0x2500 0x2501 0x2502
0x2503 0x2515 0x2516 0x2517 0x2518 0x2528 0x2529 0x252A
0x252B 0x253E 0x253F 0x2540 0x2541 0x2555 0x2556 0x2557
0x2558 0x2562 0x2563 0x2569
```

RASTAN wordmark full band, rows `2..12`, all cols, includes center sword overlap: `166` unique nonblank codes, range `0x21C2..0x2570`. Conservative RASTAN-only approximation excluding center sword corridor cols `13..16`: `130` unique nonblank codes. Both sets are recorded in `title_tile_usage_audit.json`.

## Genesis Build 0095 Comparison

Address mapping authority: the Genesis equivalents in this section were re-checked against `build/rastan-direct/address_map.json`, segment `171` (`arcade_copy`, `arcade_start=0x05A28A`, `arcade_end_exclusive=0x060000`, `genesis_start=0x05A48A`, `genesis_end_exclusive=0x060200`). The confirmed JSON mappings are `arcade 0x05A38E -> Genesis 0x05A58E`, `arcade 0x05A4DE -> Genesis 0x05A6DE`, and `arcade table 0x05B0B2 -> Genesis table 0x05B2B2`. The matching `+0x200` offset is descriptive for this segment only, not used as mapping authority.

Build 0095 source/runtime mapping for the same title block:

```asm
03AC54: jsr 0x05A556
05A556: ... bsrw 0x05A58E ; rts
05A58E: movea.l #0x00C00328,%a1
05A594: lea 0x05B2B2,%a0      ; JSON-mapped source table equivalent of arcade 0x05B0B2
05A59A: move.w #28,%d0
05A59E: move.w #20,%d1
05A5A2: move.w #1,%d2
05A5A6: bsrw 0x05A6DE
05A6DE: original-style block copy loop remains visible in produced disassembly
```

Build 0095 trace events:

```text
EVENT TITLE_HANDLER_3AC54_ENTRY ... s0=0000 s2=0000 s4=0001 cnt=0000
EVENT TITLE_BLOCK_5A58E_ENTRY ...
EVENT TITLE_BLOCK_5A58E_DONE ...
EVENT TITLE_HANDLER_3AC88_BEFORE_KICK ... s0=0000 s2=0001 s4=0000 cnt=0000 fg_dirty=15800000 bg_dirty=00000000
```

Staging watchpoint reduction from the Build 0095 trace:

| Staging buffer | Total writes | Nonzero data/post writes | Writer PCs | Interpretation |
|---|---:|---:|---|---|
| BG `0xFF401A..0xFF501A` | `8044` | `0` | startup zeroing `0x0002B8`, BG fill clear `0x07062C` | No title-art BG cells staged |
| FG `0xFF501A..0xFF601A` | `8131` | `78` | startup zeroing `0x0002C8`, FG fill clear `0x070702`, glyph/text `0x07086E` | FG text path alive; not the BG title-art block |

At `0x3AC88`, `bg_dirty=0x00000000`; therefore the `0x5A58E -> 0x5A6DE` title-art block did not mark Plane B rows dirty and did not stage the complete PC080SN BG title-art cells.

## Preload / LUT Status

From `build/pc080sn_scene_preload_title.bin` and `build/pc080sn_tile_vram_lut.bin`:

| Element/set | Unique nonblank tile codes | Present in title preload | Assigned in LUT | Actual Genesis VRAM independently dumped? | Nametable/staging status |
|---|---:|---:|---:|---|---|
| Full `0x05B0B2` title block | `174` | `174/174` | `174/174` | Not independently dumped in this task | Not staged/dirty via title block |
| Red TAITO logo geometry | `4` | `4/4` | `4/4` | Not independently dumped | Not staged/dirty via title block |
| Sword center corridor | `44` | `44/44` | `44/44` | Not independently dumped | Not staged/dirty via title block |
| RASTAN wordmark band | `166` | `166/166` | `166/166` | Not independently dumped | Not staged/dirty via title block |

The user-supplied VDP Pattern Viewer shows some title-looking patterns, but this audit does not use the viewer as arcade intent. The direct preload/LUT check is stronger for the A/B fork: every tile code required by the arcade `0x05B0B2` title block is present in the Build 0095 title preload and assigned a LUT slot.

## A/B Fork Resolution

| Element | Fork result | Evidence |
|---|---|---|
| Red TAITO logo | **B** | Arcade tile codes `0x22CB..0x22CE` are preloaded and LUT-assigned; Build 0095 title block executes but produces no BG staging/dirty output |
| RASTAN wordmark | **B** | Wordmark-band tile codes are preloaded and LUT-assigned; corresponding PC080SN BG block cells are not staged/dirty |
| Sword | **B** | Center-corridor tile codes are preloaded and LUT-assigned; corresponding PC080SN BG block cells are not staged/dirty |
| Full title-art block | **B** | All `174` nonblank codes from `0x05B0B2` are preloaded and LUT-assigned; observed runtime failure is cell placement/staging, not pattern availability |

Therefore the missing complete title art is **not** explained by missing title preload/LUT coverage in Build 0095. The current failure is that the PC080SN BG block-copy producer path does not feed Genesis BG staging / dirty rows for this title block.

This supersedes the earlier working hypothesis in `docs/design/Andy_build_0095_taito_logo_producer_attribution.md` that incomplete title tile-pattern preload was the root cause. The preload/LUT hypothesis was reasonable from the viewer symptom, but the arcade-first tile audit resolves the fork as **B**.

## Audit-The-Audit Result

`tools/audit_vram_tile_usage.py` explicitly includes all relevant hardcoded title/attract ranges:

```python
"Title screen (0x5B0B2, 28x20)":       (0x5B0B2, 28 * 20),
"Insert coin (0x5AC72, 12x10)":         (0x5AC72, 12 * 10),
"Game over/continue (0x5AF62, 12x14)":  (0x5AF62, 12 * 14),
"Stage intro/boss (0x5AD62, 16x16)":    (0x5AD62, 16 * 16),
"Possible dead code (0x5A7DA, 28x21)":  (0x5A7DA, 28 * 21),
```

`tools/translation/precompute_pc080sn_tile_lut.py` also includes the title static block source:

```python
(0x5B0B2, 28, 20, "title_logo")
```

Coverage assessment: **no undercount for the TAITO / RASTAN / sword title-art source proven in this task.** The full arcade title art comes from `0x05B0B2`, and that range is already covered. No additional source ranges are required for these elements.

Important boundary of this result: the audit script validates title tile-code preload/LUT coverage. It does not prove that the runtime block-copy path stages/dirty-marks the corresponding nametable cells. Build 0095 is failing on that latter runtime translation side.

## Recommended Fix Class

Recommended class: **B - producer/translation coverage for PC080SN BG block-copy cells**, not A/preload completion.

Concrete next investigation/fix locus:

- Arcade source producer: `0x05A38E -> 0x05A4DE`, title table `0x05B0B2`, destination `0x00C00328`, `28x20`.
- Build 0095 runtime equivalent: `0x05A58E -> 0x05A6DE`, source table `0x05B2B2`, destination `0x00C00328`, `28x20`.
- Observed issue: this path executes but does not create BG staging writes or `bg_dirty` rows.

Before editing, reconcile the produced-disassembly/spec mismatch carefully: `specs/startup_title_remap.json` contains an opcode-replace entry for arcade `0x05A4DE`, but Build 0095 produced disassembly and runtime evidence show the title block path reaching an original-style relocated copy loop at `0x05A6DE` with no BG staging effect. The implementation task should start by proving why that replacement is not covering this runtime path, then repair the block-copy translation so the arcade BG title-art cells become staged Plane B cells with correct dirty rows.

Do **not** extend `pc080sn_scene_preload_title.bin` as the first fix; the required `0x05B0B2` codes are already covered.

## VRAM Budget

Budget status: **fits for the audited title-art source.** The full `0x05B0B2` title block requires `174` unique nonblank tile codes, all already present in the Build 0095 title preload. The broader title scene preload has `842` tile/slot pairs and the LUT has `2325` assigned nonzero entries; the audited title block itself is comfortably within the title-scene slot budget.

## Safe-To-Implement Assessment

Safe to implement a targeted follow-up: **YES, for the B-class block-copy staging/dirty path**, after the implementation task first proves the current `0x05A4DE` opcode-replace coverage mismatch against the produced Build 0095 ROM.

Further trace needed: actual Genesis VRAM pattern dump is optional for this specific fork because preload/LUT presence and missing BG staging already resolve A vs B. A VRAM dump may still be useful as visual corroboration, but it is not the blocker.

## Open / Closed Issues Impact

- Open issues touched: OPEN-001 (active; missing complete title art now resolved as B-class cell/staging issue, not title preload gap), OPEN-016 (context), OPEN-015 (not touched).
- Closed issues touched: NONE.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: throne, Start/C/A exception, OPEN-015 crash-handler defects, BlastEm/Nomad/HV-counter, implementation.

## KNOWN_FINDINGS Impact

Option A for this task: no `KNOWN_FINDINGS.md` edit performed. Candidate future refinement if Tighe/Chad Sr. want it: Build 0095 proves the complete arcade title-art table `0x05B0B2` is already covered by title preload/LUT; the missing TAITO/RASTAN/sword output is a PC080SN BG block-copy staging/dirty translation gap.

## STOP

STOP triggered: **NO**. The arcade source/layer was established, the Build 0095 A/B fork was resolved per element as B, and the audit script does not undercount the proven arcade title-art source.
