# Cody - TEMP Sprite/SAT Suppression Black Cover Test

**Date:** 2026-07-01  
**Type:** User-approved temporary diagnostic implementation + evidence + immediate revert verification  
**Baseline:** Build 0124, `dist/rastan-direct/rastan_direct_video_test_build_0124.bin`, SHA256 `f5935113ef4ab8ea231d4e31764b96a36c8bd2fe246846a2ca929facdfccd921`  
**Temporary build:** Build 0125, `dist/rastan-direct/rastan_direct_video_test_build_0125.bin`, SHA256 `34ec3a7e60a067f67b00e1b5763834571595c541aeba49672dc81f9fe228154e`  
**Revert build:** Build 0126, `dist/rastan-direct/rastan_direct_video_test_build_0126.bin`, SHA256 `f5935113ef4ab8ea231d4e31764b96a36c8bd2fe246846a2ca929facdfccd921`  
**Evidence directory:** `states/traces/temp_sprite_sat_suppression_black_cover_test_20260701_210430/`

## Phase 0

Relevant priors loaded: `RULES.md`, `ARCHITECTURE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest `AGENTS_LOG.md`, `docs/design/Cody_build0124_final_composite_black_cover_attribution.md`, `docs/design/Cody_pc090oj_blank_bitset_unmapped_guard_implementation.md`, `docs/design/Cody_pc090oj_object_ram_phase1_implementation.md`, `docs/design/Cody_build0123_pc090oj_transparent_pen_black_overdraw_evidence.md`, `docs/design/Andy_pc090oj_object_ram_to_genesis_sat_architecture.md`, and `docs/design/Andy_build0120_window_plane_coverage_design.md`.

High-rediscovery hazards: KF-011 frame ownership, KF-021 staged-vs-true-SAT hazard, KF-026 PC090OJ coverage hazard, KF-032 raw hardware write routing, KF-036 mapped-base discipline. No contradiction was detected.

Task classification: **EXTENDING OPEN-001 / OPEN-024** with a **user-approved temporary diagnostic exception**. This was not a production fix and not canonical behavior.

Open/Closed pre-check: OPEN-001 and OPEN-024 primary; OPEN-023 Window context; OPEN-006 sprite palette context; OPEN-015 not touched. No issue opened or closed.

Architecture exception scope: the prompt explicitly authorized one temporary scaffolding-like diagnostic build, equivalent in discipline to a bookmark cycle, provided it was immediately reverted and byte-identity-proven. No NOP/RTS bypass was used.

Address mapping discipline: `build/rastan-direct/address_map.json` loaded. No arcade-to-Genesis arithmetic offset was used as proof. Relevant mapped raw-copy examples are listed in Raw Writer Check.

ROM determinism / stamping: the release Makefile applies the sequential build number to the copied artifact filename after canonical verification; the ROM header strings are fixed (`RDVD00000000`, fixed copyright/date text) and no per-build number/date/version byte was identified in the image. The byte-identical Build 0126-vs-0124 proof below confirms the revert hash gate was possible and passed.

## Temporary Patch Plan

File: `apps/rastan-direct/src/pc090oj_hooks.s`.

Function: `vdp_commit_sprites`.

Before temporary patch:

```asm
vdp_commit_sprites:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    bsr     .Lvcs_mirror_scan
    bsr     .Lvcs_link_chain_build
    bsr     .Lvcs_tile_dma
    bsr     .Lvcs_sat_dma
    bsr     .Lvcs_clear_dirty
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts
```

Temporary Build 0125 behavior:

```asm
vdp_commit_sprites:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    /* TEMP DIAGNOSTIC ONLY - sprite/SAT suppression test - remove after evidence */
    bsr     .Lvcs_clear_generated_sprite_state
    bsr     .Lvcs_sat_dma
    bsr     .Lvcs_clear_dirty
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts
```

The patch prevented visible SAT emission by clearing all 80 staged SAT entries and all 80 staged descriptor entries, skipped mirror scan/link/tile DMA, and still performed the full 640-byte SAT DMA to `VRAM address 0xF800` through `.Lvcs_sat_dma`.

Why Plane A/B continued: `_vblank_service` still called `vdp_commit_tiles_if_dirty`, `vdp_commit_bg_strips_if_dirty`, `vdp_commit_fg_strips_if_dirty`, palette commit, scroll commit, and display off/on unchanged. Only the internal behavior of `vdp_commit_sprites` changed.

Why stale SAT could not remain visible in this test: the existing `.Lvcs_sat_dma` path was preserved and fed by a cleared `staged_sprite_sat`, so the hardware SAT was overwritten with an empty 80-entry table instead of leaving prior VRAM SAT contents intact.

A temporary invariant adjustment was also required for Build 0125 only: `total_genesis_bytes_covered` changed from `0x17D400` to `0x17D3F8` because the temporary helper body was 8 bytes shorter. This invariant adjustment was reverted before Build 0126.

## Temporary Build 0125

Initial release attempt stopped before numbering at the invariant gate:

```text
expected total_genesis_bytes_covered=0x17D400 and opcode_replace patched_site count=133;
got total_genesis_bytes_covered=0x17D3F8 opcode_replace patched_site count=133
```

After temporarily adjusting the invariant to `0x17D3F8`, the release passed.

- Build produced: YES, Build 0125
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0125.bin`
- SHA256: `34ec3a7e60a067f67b00e1b5763834571595c541aeba49672dc81f9fe228154e`
- Size: `1,561,592` bytes
- Rolling ROM SHA matched Build 0125 at that time
- `GATE_PASS`
- `opcode_replace` patched-site count: `133`
- total covered bytes: `0x17D3F8`
- Temporary files changed: `apps/rastan-direct/src/pc090oj_hooks.s`, `tools/translation/postpatch_startup_rom.py`, `tools/translation/verify_canonical_rom.py`

## Visual Result

Baseline Build 0124 visual anchor from prior evidence:

- `states/traces/build_0124_final_composite_black_cover_attribution_20260701_170732/video_frames/video_frame_282_covered.png` shows the story page black-covered at source video frame 282.
- `states/traces/build_0124_final_composite_black_cover_attribution_20260701_170732/video_frames/video_frame_283_reveal.png` shows the page revealed at frame 283.

Build 0125 temporary suppression visual evidence:

- `states/traces/temp_sprite_sat_suppression_black_cover_test_20260701_210430/build0125_frame_282.png`
- `states/traces/temp_sprite_sat_suppression_black_cover_test_20260701_210430/build0125_frame_283.png`
- `states/traces/temp_sprite_sat_suppression_black_cover_test_20260701_210430/build0125_frame_289.png`
- `states/traces/temp_sprite_sat_suppression_black_cover_test_20260701_210430/build0125_frame_369.png`
- Contact sheet: `states/traces/temp_sprite_sat_suppression_black_cover_test_20260701_210430/build0124_vs_build0125_visual_contact.png`

Visual observation: Build 0125 frame 282 shows the story page visible/uncovered while preserving visible Plane A/B content (`INSERT COIN(S)`, story text, king/figure artwork). The Build 0124 baseline frame 282 showed the black cover at the same frame anchor. Under forced-empty SAT, the black cover disappears.

Classification from visual evidence: **sprite/SAT output is strongly implicated** in the Build 0124 final-composite black cover. This is a diagnostic attribution only; it is not a permanent fix.

## Runtime Evidence

Capture script: `states/traces/temp_sprite_sat_suppression_black_cover_test_20260701_210430/build0125_sat_suppression_capture.lua`.

Runtime log: `states/traces/temp_sprite_sat_suppression_black_cover_test_20260701_210430/build0125_capture.log`.

Reduced JSON: `states/traces/temp_sprite_sat_suppression_black_cover_test_20260701_210430/build0125_runtime_summary.json`.

MAME Genesis-driver captures were taken at frames 282, 283, 289, and 369.

| Frame | BG nonzero words | FG nonzero words | staged SAT nonzero | staged desc nonzero | true VDP SAT nonzero | true VDP SAT = staged SAT | PC090OJ object nonzero | decoded | drawable | emitted |
|---:|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|
| 282 | 168 | 146 | 0 | 0 | 0 | YES | 480 | 0 | 0 | 0 |
| 283 | 168 | 146 | 0 | 0 | 0 | YES | 480 | 0 | 0 | 0 |
| 289 | 168 | 146 | 0 | 0 | 0 | YES | 480 | 0 | 0 | 0 |
| 369 | 168 | 146 | 0 | 0 | 0 | YES | 480 | 0 | 0 | 0 |

All captured `staged_sprite_sat` and `true_vdp_sat_f800` dumps have SHA256 `9e132485d5107211de325a45e7917cbe3e4b5b9cde3e4ee91d7d2102317759ee`, the all-zero 640-byte SAT hash. The VDP SAT dump path was available and succeeded for this test (`vram_available=true`, `vdp_sat_dump=true`).

Interpretation: Plane A/B staging remained active and nonzero; PC090OJ object RAM remained nonzero; the temporary patch suppressed generated SAT/descriptor output and overwrote true VDP SAT with cleared entries. The disappearing black cover therefore depends on Genesis SAT output, not on disabling the whole VDP pipeline.

## Raw Writer Check

Static source/disassembly scan results:

- Known explicit `VRAM address 0xF800` SAT DMA setup is inside `.Lvcs_sat_dma` (`apps/rastan-direct/src/pc090oj_hooks.s`, runtime helper region). It writes a full 640-byte SAT from `staged_sprite_sat` to VDP SAT.
- Other direct VDP port writes in source are boot/crash/setup/Plane A/B/palette/scroll/tile/sprite helper paths (`vdp_comm.s`, `scene_load.s`, `crash_handler.s`, `pc090oj_hooks.s`). No separate explicit source writer to `VRAM address 0xF800..0xFA7F` outside the sprite commit helper was identified.
- Raw copied PC090OJ-address producers remain in the ROM and are tracked separately. Address-map examples:
  - `runtime_genesis_pc 0x0512C8` maps via `address_map.json` segment 173, kind `arcade_copy`, to `arcade_pc 0x0510C8`.
  - `runtime_genesis_pc 0x052CA2` maps via segment 187, kind `arcade_copy`, to `arcade_pc 0x052AA2`.
  - `runtime_genesis_pc 0x05A702/0x05A71E/0x05A724` map via segment 234, kind `arcade_copy`, to `arcade_pc 0x05A502/0x05A51E/0x05A524`.
  - The routed dispatcher at `runtime_genesis_pc 0x03AF44` maps via segment 59, kind `patched_site`, to `arcade_pc 0x03AD44`.

Answers:

1. Known raw VDP data writes to SAT VRAM outside sprite commit: **none identified statically**.
2. Raw VDP control/data writes that could target SAT after forced clear: **possible in principle if a later raw VDP-port writer exists with the VDP address latch targeting SAT, but no specific post-clear SAT-targeting writer was proven in this pass**.
3. PC090OJ raw writes still bypassing mirror/directly reaching VDP/SAT: **copied PC090OJ-address writer clusters remain as static risks**, but this test did not prove they wrote after the forced empty SAT DMA in the captured window.
4. If the black cover had remained with forced-empty SAT, a later raw writer could still have explained it; because the cover disappeared and true VDP SAT was zero at captured frames, the immediate black-cover symptom is strongly tied to the normal sprite/SAT output path.
5. Best proving watchpoint: runtime write watchpoints on `HW_ADDRESS 0x00C00000..0x00C00007` plus `HW_ADDRESS 0x00D00000..0x00D007FF`, logging frame, PC, VDP control/data values, and whether the write occurs after `.Lvcs_sat_dma` in the same VBlank.

## Immediate Revert

After Build 0125 evidence capture, the temporary source patch and temporary invariant constants were removed immediately.

Post-revert source checks:

- `apps/rastan-direct/src/pc090oj_hooks.s` restored `vdp_commit_sprites` to `mirror_scan -> link_chain_build -> tile_dma -> sat_dma -> clear_dirty`.
- `tools/translation/postpatch_startup_rom.py` restored `CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x17D400`.
- `tools/translation/verify_canonical_rom.py` restored `CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x17D400`.
- Search for `TEMP DIAGNOSTIC ONLY` and `17D3F8` in those files returned no hits.

Option B was not used. The revert was completed in the same task.

## Revert Build 0126

- Build produced: YES, Build 0126
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0126.bin`
- SHA256: `f5935113ef4ab8ea231d4e31764b96a36c8bd2fe246846a2ca929facdfccd921`
- Size: `1,561,600` bytes
- Rolling ROM SHA matched Build 0126 after the revert
- `GATE_PASS`
- `opcode_replace` patched-site count: `133`
- total covered bytes: `0x17D400`
- invariant changes remaining: none

## Byte-Identical Revert Verification

| Build | Path | SHA256 | Size |
|---:|---|---|---:|
| 0124 | `dist/rastan-direct/rastan_direct_video_test_build_0124.bin` | `f5935113ef4ab8ea231d4e31764b96a36c8bd2fe246846a2ca929facdfccd921` | `1,561,600` |
| 0125 | `dist/rastan-direct/rastan_direct_video_test_build_0125.bin` | `34ec3a7e60a067f67b00e1b5763834571595c541aeba49672dc81f9fe228154e` | `1,561,592` |
| 0126 | `dist/rastan-direct/rastan_direct_video_test_build_0126.bin` | `f5935113ef4ab8ea231d4e31764b96a36c8bd2fe246846a2ca929facdfccd921` | `1,561,600` |

`cmp -s dist/rastan-direct/rastan_direct_video_test_build_0124.bin dist/rastan-direct/rastan_direct_video_test_build_0126.bin` returned status `0`.

Verdict: **PASS.** Build 0126 is byte-identical to Build 0124. The temporary diagnostic patch left zero ROM residue.

All three ROMs are preserved:

- `dist/rastan-direct/rastan_direct_video_test_build_0124.bin`
- `dist/rastan-direct/rastan_direct_video_test_build_0125.bin`
- `dist/rastan-direct/rastan_direct_video_test_build_0126.bin`

Sequential naming confirmed: `0124 -> 0125 -> 0126`, no suffixes.

## Classification

Final classification: **sprite/SAT output is strongly implicated in the Build 0124 final-composite black cover**.

Confidence: HIGH for the bounded diagnostic conclusion because the visual cover disappeared when SAT was forcibly cleared/DMAed, while Plane A/B staging and visible text/art remained active.

What this proves:

- The Build 0124 black cover is dependent on Genesis sprite/SAT output or the normal sprite commit product.
- Writing an empty SAT removes the cover in the captured story/high-score window.
- The cover is not caused by globally disabled Plane A/B, palette, scroll, or display commits, because those remained active enough to show the story page in Build 0125.
- The temporary patch was fully reverted and Build 0126 is byte-identical to Build 0124.

What this does not prove:

- It is not a permanent fix.
- It does not identify which PC090OJ object, descriptor, raw writer, SAT link field, tile DMA, priority field, or coordinate decode creates the cover.
- It does not close OPEN-024 or OPEN-001.
- It does not eliminate all raw PC090OJ bypass risks.

Recommended next target: a non-suppression evidence pass on canonical Build 0126/0124 behavior that logs the SAT-producing path before the cover frame: PC090OJ object entries -> descriptor emission -> link chain -> true VDP SAT, plus VDP-port watchpoints for post-SAT-DMA raw writers.

## Open / Closed Issues Impact

- Open issues touched: OPEN-001 (graphics incomplete / black cover attribution), OPEN-024 (PC090OJ sprite/SAT subsystem), OPEN-023 context only, OPEN-006 context only.
- Closed issues touched: none.
- New issues opened: none.
- Issues closed: none.
- Issues intentionally deferred: actual sprite/SAT fix, identifying the specific offending sprite/path, D00298, Window, Plane A/B rewrite, OPEN-015.

## KNOWN_FINDINGS Impact

Option A: no `KNOWN_FINDINGS.md` update in this task. This is a temporary diagnostic attribution with a clean revert, not yet a durable mechanism-level root cause.

## STOP Status

STOP triggered: **NO**.
