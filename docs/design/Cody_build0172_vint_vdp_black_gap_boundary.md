# Cody - Build 0172 VINT / VDP Commit Black-Gap Boundary

**Date:** 2026-07-14
**Type:** Analysis-first runtime evidence + static boundary review. No source/spec/tool/Makefile/ROM/invariant changes. No build.
**Artifact tested:** Build 0171 candidate, `dist/rastan-direct/rastan_direct_video_test_build_0171.bin`
**SHA256:** `819a2131a7643135b46c6faaaf00153ac95c37fae2ed357659fed74075d45ab9`
**Size / counter:** `1,581,848` bytes / `171`
**Trace path:** `states/traces/build0172_vint_vdp_black_gap_boundary_20260714_221622/`

## Phase 0

Classification: **EXTENDING**. This extends OPEN-017 / OPEN-001 graphics-runtime diagnosis after the Build 0171 tall-BG rolling projection candidate.

Relevant priors preserved:

- KF-010: PC080SN BG maps to Genesis Plane B; FG maps to Plane A.
- KF-011: arcade VBlank owns progression; Genesis `_vblank_service` is hardware-service and tail-jumps to `runtime_genesis_pc 0x0003A208`.
- KF-015: vertical scroll convention is `-raw + 8`; Build 0171 uses gameplay BG residual pixel scroll after rolling tall-BG projection.
- KF-038: long PC080SN BG rows can alias under a 32-row model; Build 0170/0171 introduced the gameplay tall-BG representation/projection for the Stage 1 strip family.
- OPEN-003: MAME VDP readback can be inconclusive/divergent and must not be treated as screen truth by itself.
- OPEN-017: real hardware / gameplay visual symptoms remain open.

Rediscovery-hazard findings touched: KF-010, KF-011, KF-015, KF-038. No contradiction detected.

Architecture compliance: **CONFIRMED**. Arcade code remains the program. No Genesis-owned lifecycle, no diagnostic ROM, no second renderer, no source change, and no staging/commit behavior modification was introduced.

## User Correction Recorded

Tighe's correction is recorded as the controlling premise for this task:

- The black horizontal band should not be treated as missing ground tile data unless rendered-frame VDP evidence proves that.
- The prior Build 0172 no-build trace already showed sampled visible floor/playfield BG cells matched original arcade intent through the Genesis LUT and staging in steady Build 0171 frames.
- The live question is therefore: why is a black band rendered despite apparently correct staged/projected BG data?

The crouch/down-held and ineffective input observations are recorded but intentionally deferred. They are not patched here.

## Arcade Comparison Correction

The previous trace did compare against original arcade state for the sampled cells: original arcade PC080SN BG/FG page data was sampled at matching post-landing state/scroll positions, then Build 0171 staged BG/tall-BG cells were compared through `genesistan_pc080sn_tile_vram_lut` at frames `820` and `1400`. That comparison established that the selected BG floor/playfield cells were present and correctly mapped in Build 0171 staging.

What it did **not** prove: that the actual rendered Genesis Plane B pixels/VRAM/CRAM at the black-band rows matched the staged buffers. The MAME `:gen_vdp` readback in that harness returned all zero and was explicitly recorded as inconclusive.

## Rendered Frame Anchor

Existing Build 0171 screenshot reviewed:

- `states/traces/build0171_tall_bg_projection_rowbase_20260714_200031/build0171_frame_1081.png`

A pixel scan of that screenshot found a fully black horizontal band across all 320 pixels at screen rows `112..146` inclusive. This is the visual anchor used here for the black-band symptom.

## Static VBlank / Commit Path

Generated disassembly and source show the Build 0171 `_vblank_service` order:

```text
0x700C2  _vblank_service entry / save regs
0x700C6  rastan_direct_update_inputs
0x700CA  vdp_prepare_sprites
0x700D2  VDP reg1 = 0x34 DISPLAY_OFF, VINT enabled
0x70112  vdp_commit_tiles_if_dirty
0x7013C  vdp_project_bg_tall_if_dirty
0x701BA  vdp_commit_bg_strips_if_dirty
0x71A6E  vdp_commit_fg_narrow_strips -> vdp_commit_fg_strips_if_dirty
0x72442  vdp_commit_sprites_vram
0x700EE  VDP reg1 = 0x74 DISPLAY_ON, VINT enabled
0x70256  optional vdp_commit_palette
0x70276  vdp_commit_scroll
0x70108  restore regs
0x7010C  jmp 0x3A208 arcade VBlank
0x3A27E  arcade VBlank final RTE
```

Important static observations:

- Display is turned back on at `0x700EE` **before** optional palette commit and scroll commit.
- Gameplay tall-BG projection at `0x7013C` writes 32 visible rows into `staged_bg_buffer` and sets `bg_row_dirty=0xffffffff` when the projection row base changes or `bg_tall_dirty` is set.
- Plane B full-row commit at `0x701BA` writes dirty rows to VRAM Plane B and clears dirty bits as rows complete.
- Plane A full-row commit at `0x70208` does the same for FG rows, after narrow-FG commits.
- Sprite tile DMA and SAT DMA run before display-on through `vdp_commit_sprites_vram`.
- Scroll commits after display-on; for gameplay BG Y, only residual `& 0x0007` is committed because tall-BG projection owns tile-row selection.

## Runtime Evidence Collected

### Lua / VDP-port monitor

Trace files:

- `vint_vdp_black_gap_trace.lua`
- `vint_vdp_black_gap_events.csv`
- `vint_vdp_black_gap_frames.csv`
- `vint_vdp_black_gap_summary.log`

The run exited `0` and reached gameplay state `2/3/0`, `scene=0x01`.

Representative frame samples from `vint_vdp_black_gap_frames.csv`:

| frame | state | scene | player_y | camera_y | scroll_y_bg | reg1 writes | VDP data writes |
|---:|---|---|---|---|---|---:|---:|
| `571` | `0002/0003/0000` | `0x01` | `0x0050` | `0x0000` | `0x0000` | `0` | `0` |
| `751` | `0002/0003/0000` | `0x01` | `0x0070` | `0x0163` | `0x0167` | `0` | `0` |
| `820` | `0002/0003/0000` | `0x01` | `0x0070` | `0x0149` | `0x0149` | `0` | `0` |
| `1081` | `0002/0003/0000` | `0x01` | `0x0070` | `0x0149` | `0x0149` | `0` | `0` |
| `1400` | `0002/0003/0000` | `0x01` | `0x0070` | `0x0149` | `0x0149` | `0` | `0` |

Across frames `571..1450`, the VDP-port monitor recorded:

- `reg1_writes`: `0` every frame.
- `display_off`: `0` every frame.
- `display_on`: `0` every frame.
- `reg1_vint_disabled`: `0` every frame.
- VDP data-write columns: `0` in the sampled gameplay frames.

The only captured Mode-2 reg1 writes were earlier startup/frontend writes: `0x8134`, `0x8134`, `0x8174`, `0x8134`, `0x8174`. All preserve VINT-enable bit 5.

### Execute-tap limitation

The Lua harness attempted to install execute taps for `_vblank_service`, BG/FG/sprite/palette/scroll commit PCs, and arcade VBlank entry/RTE. In this MAME environment, every execute tap failed with:

```text
attempt to call a nil value (method 'install_execute_tap')
```

A native debugger command-file attempt was also made. `-debugger qt` failed due lack of display (`qt.qpa.xcb: could not connect to display :0`). `-debugger none` exited cleanly but did not emit `trace/tracelog` output, so it did not provide breakpoint PC hits.

Therefore, this task does **not** have reliable PC-execution timing for `0x700C2 -> 0x70108 -> 0x3A208 -> 0x3A27E` in the black-band gameplay window.

## Assessment Against Required Causes

Classification: **I - More evidence needed**.

Evidence-supported narrowing:

- The black band is real in the rendered screenshot (`rows 112..146` fully black at frame `1081`).
- The prior arcade-vs-Genesis staging trace already proved the sampled main floor/playfield BG cells are present/mapped/staged in Build 0171 steady frames.
- The available VDP-port monitor sees no gameplay-window reg1/data writes while game state reaches and remains in gameplay `2/3/0`; this points toward a VINT/VDP-service or instrumentation boundary, not a tile-source/staging boundary.
- No captured VDP reg1 write clears VINT-enable bit 5.

Not proven:

- Exact VINT entry/exit cadence.
- Whether `_vblank_service` is missed/masked, overlong, or executing but not captured by this MAME path.
- Whether display-off spans visible scanlines.
- Whether Plane B VRAM contains the expected rows at the exact black-band render frame.
- Whether another layer/window/SAT masks the band black.
- Whether pattern/CRAM data render black despite correct nametable words.

## Required Result Fields

- **Black-band frame sampled:** Existing Build 0171 frame `1081`; screenshot rows `112..146` are all black.
- **VINT timing result:** Inconclusive. Lua execute taps unavailable; native debugger trace unavailable headlessly. VDP-port monitor suggests no gameplay-window commit writes, but exact VINT PC cadence is not proven.
- **Display-off timing result:** Inconclusive. No gameplay-window reg1 writes were captured; startup/frontend reg1 writes preserve VINT enable.
- **Plane B commit result:** Inconclusive for rendered VRAM. Static path is present; prior staging data is correct; current monitor did not capture gameplay Plane B data writes.
- **Plane A commit result:** Inconclusive for rendered VRAM. Static path is present; prior sparse-FG incompleteness remains secondary.
- **DMA budget result:** Not proven. No cycle timing or VBlank duration was captured.
- **Sprite DMA/SAT result:** Static path runs before display-on if VBlank service enters. Runtime commit timing was not captured.
- **Palette/scroll commit result:** Static path runs after display-on. Runtime timing was not captured; this remains a plausible ordering/timing suspect but not proven.
- **Dirty-row result:** Prior steady trace showed dirty flags clear after commit. Current execute timing could not prove per-frame dirty processing.
- **Projection/scroll frame-phase result:** Build 0171 prior trace had one frame-boundary caveat at frame `751`; steady frames `820/1400` matched staging. Not enough to explain persistent black rows `112..146`.
- **Window/mask/register result:** Not proven. Requires reliable VDP register/window/layer capture from the exact rendered frame.
- **Rendered-frame correlation:** Partial only: screenshot rows identified; staged-vs-rendered VRAM correlation remains blocked by VDP readback/execute-trace limitations.
- **First proven black-band cause:** None. The first proven boundary is a VINT/VDP observability/commit-cadence gap: game state reaches gameplay while this harness sees no gameplay VDP port writes, but exact cause is not safely placeable.

## STOP / Next Proof Blocker

STOP for implementation/build. Build 0172 is **not** produced.

Exact remaining proof blocker:

1. Need a reliable PC-execution trace for `0x700C2`, `0x700D2`, `0x7013C`, `0x701BA`, `0x71A6E`, `0x70208`, `0x72442`, `0x700EE`, `0x70256`, `0x70276`, `0x70108`, `0x3A208`, and `0x3A27E` across the exact black-band gameplay window.
2. Need reliable rendered-frame VDP correlation for screenshot rows `112..146`: Plane B nametable, Plane B pattern bytes for the referenced slots, CRAM line(s), Plane A/window/SAT overlap, and display/window registers.
3. If MAME remains unable to provide that evidence, use Exodus/BlastEm debug windows or an explicitly diagnostic, reverted-only probe. Do not ship a source change from the current partial trace.

## Build / Issue Impact

- Build produced: **NO**.
- Diagnostic ROM produced: **NO**.
- Accepted build changed: **NO**.
- Artifact tested: Build 0171 candidate ROM only.
- Source/spec/tool/Makefile/ROM/invariant changes: **NO**.
- OPEN_ISSUES impact: OPEN-017 updated; OPEN-001 and OPEN-003 context.
- KNOWN_FINDINGS impact: **Option A - no new finding indexed**. No durable mechanism is proven yet.
