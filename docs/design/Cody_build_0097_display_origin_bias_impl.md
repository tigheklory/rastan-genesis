# Cody - Build 0097 PC080SN Display-Origin Bias

**Date:** 2026-06-24
**Type:** Implementation + release build + visual evidence capture
**Build:** 0097
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0097.bin`
**ROM SHA256:** `b8e16f7c670dc8225584679b88d5a4ea71efb0dc5938d38420fca524ec71db72`
**Baseline:** Build 0096, SHA `c054107bc6dfccb45b1703a0896be9905f729b89d1e0b16a4677d30badfde51c`
**Scope:** Shared display-origin bias only. No producer, staging, cell-decode, block-copy, bottom-viewport, Start-crash, OPEN-015, or HV-counter work.

## Phase 0

Classification: **EXTENDING** (OPEN-001). Priors loaded from `RULES.md`, `ARCHITECTURE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest `AGENTS_LOG.md`, `docs/design/Andy_build_0096_placement_offset_attribution.md`, `docs/design/Cody_build_0096_visible_window_origin_correlation.md` including correction, `docs/design/Cody_build_0096_scroll_origin_trace.md`, and `docs/design/Cody_build_0096_title_bg_blockcopy_staging_impl.md`.

Architecture compliance: **CONFIRMED**. The arcade code remains the program. This change only updates the Genesis VDP hardware-service commit path to reproduce the arcade display-origin behavior.

## Pre-Declared Invariant Category

Category: small fixed-bias addition in the native `vdp_commit_scroll` helper.

Expected before editing:

| Invariant | Expected |
|---|---:|
| `opcode_replace` site count | unchanged at `96` |
| `total_genesis_bytes_covered` | native helper growth only |
| Producers/staging/cell decode/block-copy | unchanged |

Expected byte growth was `+0x14`: two X scroll words expand by `+6` bytes each, and two Y scroll words expand by `+4` bytes each.

## Sign Proof

The target visible result is fixed: move both planes **left 16 px** and **up 8 px** relative to Build 0096.

`apps/rastan-direct/src/vdp_comm.s` writes the committed values directly to the VDP scroll outputs:

- HScroll table at `VRAM_HSCROLL_BASE = 0xFC00`
- VSRAM offset command `0x40000010`
- Plane A/FG word first, Plane B/BG word second for both axes

Local SGDK reference confirms the wrappers write the caller-provided value directly to VDP:

- `tools/sgdk/src/vdp_bg.c:34-49`: `VDP_setHorizontalScroll()` writes `value` directly to the HScroll table.
- `tools/sgdk/src/vdp_bg.c:88-103`: `VDP_setVerticalScroll()` writes `value` directly to VSRAM.

Local SGDK map scrolling shows the direction convention for a viewport moving right/down:

- `tools/sgdk/src/map.c:239`: `VDP_setHorizontalScrollVSync(map->plane, -x)`.
- `tools/sgdk/src/map.c:266`: `VDP_setVerticalScrollVSync(map->plane, y)`.

Therefore:

| Desired visible motion | Committed VDP term |
|---|---:|
| content left 16 px | HScroll `-16` / `0xFFF0` |
| content up 8 px | VScroll `+8` / `0x0008` |

This preserves the prompt's arcade-intent target while using the signed values proven for this Genesis VDP commit path.

## Implementation

File changed: `apps/rastan-direct/src/vdp_comm.s`.

Exact site: `vdp_commit_scroll`.

The helper now reads each dynamic staged scroll word, applies a fixed display-origin bias, and writes the result to VDP:

```asm
move.w  staged_scroll_x_fg, %d0
subi.w  #VDP_DISPLAY_ORIGIN_X_BIAS, %d0
move.w  %d0, VDP_DATA
move.w  staged_scroll_x_bg, %d0
subi.w  #VDP_DISPLAY_ORIGIN_X_BIAS, %d0
move.w  %d0, VDP_DATA

move.l  #0x40000010, VDP_CTRL
move.w  staged_scroll_y_fg, %d0
addq.w  #VDP_DISPLAY_ORIGIN_Y_BIAS, %d0
move.w  %d0, VDP_DATA
move.w  staged_scroll_y_bg, %d0
addq.w  #VDP_DISPLAY_ORIGIN_Y_BIAS, %d0
move.w  %d0, VDP_DATA
```

Constants added:

```asm
.equ VDP_DISPLAY_ORIGIN_X_BIAS, 16
.equ VDP_DISPLAY_ORIGIN_Y_BIAS, 8
```

Dynamic scroll path is preserved: the staged scroll words are still read first and the fixed bias is additive.

## Build

Command run exactly once:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **PASS**.

Artifacts:

| Artifact | Path / value |
|---|---|
| Numbered ROM | `dist/rastan-direct/rastan_direct_video_test_build_0097.bin` |
| Rolling ROM | `apps/rastan-direct/dist/rastan_direct_video_test.bin` |
| SHA256 | `b8e16f7c670dc8225584679b88d5a4ea71efb0dc5938d38420fca524ec71db72` |
| Build 0096 SHA | `c054107bc6dfccb45b1703a0896be9905f729b89d1e0b16a4677d30badfde51c` |
| Byte-identical to Build 0096 | NO |
| Release trace | `states/traces/rastan_direct_video_test_build_0097_mame_30s_20260624_205325/` |

The release trace completed without a no-input crash in the 30-second window.

## Invariant Reconciliation

| Invariant | Build 0096 | Build 0097 | Result |
|---|---:|---:|---|
| `opcode_replace` count | `96` | `96` | unchanged |
| `total_genesis_bytes_covered` | `0x17CD14` | `0x17CD28` | `+0x14` |

Cause: exactly the native `vdp_commit_scroll` helper growth described above. No opcode replacement site was added or removed.

Manifest confirms:

```text
patch_counts {'opcode_replace_and_rom_opcode_replace': 96}
postpatch_expected_opcode_replace_sites 96
postpatch_expected_total_genesis_bytes_covered 0x17CD28
```

## Static Verification

Generated disassembly confirms the produced artifact contains the intended committed scroll values:

```asm
701fa: move.w 0xff4014,%d0      ; staged_scroll_x_fg
70200: subi.w #16,%d0
70204: move.w %d0,0xc00000      ; HScroll FG = dynamic - 16
7020a: move.w 0xff4012,%d0      ; staged_scroll_x_bg
70210: subi.w #16,%d0
70214: move.w %d0,0xc00000      ; HScroll BG = dynamic - 16
7021a: move.l #0x40000010,0xc00004
70224: move.w 0xff4018,%d0      ; staged_scroll_y_fg
7022a: addq.w #8,%d0
7022c: move.w %d0,0xc00000      ; VScroll FG = dynamic + 8
70232: move.w 0xff4016,%d0      ; staged_scroll_y_bg
70238: addq.w #8,%d0
7023a: move.w %d0,0xc00000      ; VScroll BG = dynamic + 8
```

For the title-state dynamic-zero case, the committed values are therefore:

| Plane | HScroll | VScroll |
|---|---:|---:|
| Plane A / FG | `0xFFF0` | `0x0008` |
| Plane B / BG | `0xFFF0` | `0x0008` |

H40/320 mode source remains unchanged: `vdp_boot_setup` still writes VDP Mode 4 register value `0x0081`. The MAME AVI capture path still reports `256x224`, which is the known capture artifact from the Build 0096 correction thread, not proof of a source-mode change.

## Visual Evidence

MAME capture artifacts:

- Build 0097 AVI: `states/screenshots/build_0097_display_origin_bias/build0097.avi`
- Build 0097 1 FPS frames: `states/screenshots/build_0097_display_origin_bias/frames/`
- Build 0097 contact sheet: `states/screenshots/build_0097_display_origin_bias/build0097_1fps_contact.png`
- Matched Build 0096 reference frame: `states/screenshots/build_0097_display_origin_bias/build0096_sec006_reference.png`
- Matched Build 0097 frame: `states/screenshots/build_0097_display_origin_bias/build0097_sec006.png`
- Before/after contact: `states/screenshots/build_0097_display_origin_bias/build0096_vs_build0097_sec006_contact.png`

Same-capture-path measurement at `sec006`:

| Frame | Non-black bbox |
|---|---|
| Build 0096 reference | `(50, 64, 255, 223)` |
| Build 0097 | `(34, 56, 255, 215)` |

Measured shift: left edge moved `-16 px`; top edge moved `-8 px`; bottom edge moved `-8 px`. This confirms a shared whole-plane display-origin shift under the same MAME capture path.

Visible no-input sequence in the Build 0097 contact sheet:

- Title art appears shifted left/up versus Build 0096 capture path.
- Plane B title art and Plane A text move together.
- `ALL RIGHTS RESERVED` is visible in the title frames.
- `CREDIT` remains out of scope / parked; no bottom-16px special casing was added.

## Non-Regression Checks

| Check | Result |
|---|---|
| FG clear replacement path touched | NO |
| BG title block-copy helper touched | NO |
| Producers touched | NO |
| Staging buffers/layout touched | NO |
| Cell decode touched | NO |
| Dynamic scroll replaced | NO - preserved and additive |
| No-input 30s release trace crash | NO crash observed |
| Known post-Start exception analyzed | NO - deferred |
| OPEN-015 crash handler work | NO |

## Validation Limits

The MAME AVI generated through the existing workflow still reports `256x224`; this is the known capture-path artifact documented after Build 0096. The source register path preserving H40 is static evidence; **USER MUST VERIFY** live emulator/video alignment against arcade reference in Exodus or the preferred MAME display path.

The sign was selected from static commit-path proof, not from iterative trial-and-error. The screenshot comparison confirms the selected sign in the same capture path, but the screenshot was not used to choose the sign.

## OPEN / KNOWN_FINDINGS Impact

OPEN-001 remains open and narrowed: Build 0097 now applies the shared PC080SN display-origin bias, but remaining parked visual threads still include red TAITO tile completeness, SCORE/HUD, CREDIT/bottom viewport policy, and the known post-Start exception.

OPEN-016 remains context only; no embedded data-pointer table survey was performed.

OPEN-015 remains untouched.

KNOWN_FINDINGS impact: Option C proposed. KF-015 should eventually note that the fixed vertical `+8` scroll-bias term derives from arcade `set_visarea(..., y=8..247)`, while the horizontal `-16` HScroll word derives from PC080SN `scrolldx = -16` and the Genesis VDP HScroll sign proof.

## STOP

STOP triggered: **NO**.
