# Cody - Build 0171 Tall BG Projection / Row-Base Candidate

**Date:** 2026-07-14
**Type:** Implementation + build + bounded runtime validation
**Baseline:** Build 0170 candidate, `dist/rastan-direct/rastan_direct_video_test_build_0170.bin`, SHA256 `562ef83673deaf47d28adbcad2ab5457ea974ed7eff778c2f471d5e8ca3a18d5`, size `1,581,820`, counter `170`
**Produced:** Build 0171, `dist/rastan-direct/rastan_direct_video_test_build_0171.bin`, SHA256 `819a2131a7643135b46c6faaaf00153ac95c37fae2ed357659fed74075d45ab9`, size `1,581,848`, counter `171`
**Scope:** One bounded PC080SN BG tall-buffer projection fix. No input, collision, PC090OJ, D00298, Exodus, READY/header, continue/game-over, or broad VBlank work.

## Phase 0

Classification: **EXTENDING**. This task extends the Stage 1 PC080SN BG long-row thread under OPEN-017 / OPEN-001 and KF-038.

Relevant priors loaded:

- KF-038: Stage 1 gameplay item-strip BG uses a 64-row PC080SN BG column; 32-row staging aliases row+32 over earlier rows.
- KF-040/KF-041: Stage 1 BG is produced through the item-page strip hook and runtime gameplay source family, not through the static raw writers or old block-source model.
- KF-015 / Build 0166 vertical scroll convention: Genesis BG/FG VSRAM uses `-raw + VDP_DISPLAY_ORIGIN_Y_BIAS`.
- OPEN-017: real hardware, gameplay terrain, input/control, collision, sprites, VBlank/rolling-bar, and other gameplay issues remain open.

Rediscovery-hazard HIGH touched: KF-038, KF-040, KF-041. No contradiction detected.

Architecture compliance: **CONFIRMED**. The arcade producer still creates the state; Genesis helper code preserves that state in staging and projects it through the existing VBlank commit path. No bypass, hardcoded terrain, player-state forcing, collision patch, second renderer, or Genesis-owned gameplay flow was added.

## Build 0170 Visual Observations Recorded

Tighe's Build 0170 BlastEm video observations are preserved as the input symptom set:

- Title, prompt, story/start, and `ROUND 1 / READY !` are visible.
- Stage 1 enters gameplay.
- Sky/cloud tiles are now visibly fixed or much improved.
- Mountains / vertical terrain that were previously closer are now wrong.
- Expected ground/floor is still missing where Rastan should stand.
- Rastan walks forward automatically with zero user input.
- Directional/jump/attack input still appears ineffective.
- At one point Rastan falls to a lower level, then keeps walking.
- At the point where the sky palette changes to violet/purple, which also happens in arcade, Rastan resets to the beginning of the stage and the palette resets too.
- Real Genesis hardware result for Build 0170 still needs verification unless Tighe reports otherwise.
- Exodus remains deferred as a gameplay verifier because it locks earlier at the scene palette change.

## Static Diagnosis

Build 0170's `vdp_project_bg_tall_if_dirty` used the Build 0166 scroll convention only to choose one 32-row half of the 64-row tall buffer:

```asm
row_selector = ((-staged_scroll_y_bg + 8) & 0x01ff) >> 3
base = row_selector & 0x0020
copy 2048 words from staged_bg_tall_buffer + base*64*2
```

That can preserve sampled anchors in one scroll window, but it cannot represent an arbitrary rolling PC080SN 64-row visible window. It is therefore consistent with Build 0170 improving sky/clouds while displacing mountains/terrain and missing expected ground later.

The tall fill helper itself is 64 columns by 64 rows: it derives column with `& 0x3f`, row with `>> 6` then `& 0x3f`, and writes `staged_bg_tall_buffer + row*128 + col*2`. The remaining defect was the projection window, not the tall backing layout.

## Implementation

Changed [vdp_comm.s](/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/vdp_comm.s) only for the implementation logic.

`vdp_project_bg_tall_if_dirty` now computes a rolling tile-row base:

```text
full_vscroll = (-staged_scroll_y_bg + VDP_DISPLAY_ORIGIN_Y_BIAS) & 0x01ff
projection_row_base = (full_vscroll >> 3) & 0x3f
visible_tall_row = (projection_row_base + visible_row) & 0x3f
```

It copies 32 visible rows, 64 words per row, from `staged_bg_tall_buffer[visible_tall_row]` into `staged_bg_buffer[visible_row]`. It tracks `bg_tall_project_base` and reprojects when either the row base changes or `bg_tall_dirty` is set, then marks all BG rows dirty for the normal Plane-B commit.

`vdp_commit_scroll` now keeps the full Build 0166 sign/bias convention for non-gameplay scenes, but in gameplay scene `genesistan_current_scene_id == 1` it commits only the pixel-subrow residual for BG Y VSRAM:

```text
committed_bg_y = (-staged_scroll_y_bg + 8) & 0x0007
```

This makes projection own tile-row selection while VDP VSRAM owns only the 0..7 pixel offset. That avoids double-applying the tile-row portion of vertical scroll after projection.

Non-gameplay title/story/high-score behavior remains guarded by `genesistan_current_scene_id != 1` and keeps the legacy 32-row path.

## Build Verification

Release command run:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

First release invocation assembled successfully and stopped on the expected canonical mechanical coverage mismatch:

```text
expected total_genesis_bytes_covered=0x1822FC, got 0x182318; opcode_replace count=151
```

Updated only the canonical coverage constants in:

- [postpatch_startup_rom.py](/home/tighe/projects/rastan-genesis/tools/translation/postpatch_startup_rom.py)
- [verify_canonical_rom.py](/home/tighe/projects/rastan-genesis/tools/translation/verify_canonical_rom.py)

Second release invocation passed:

- Boot guard: PASS
- Canonical gate: `GATE_PASS`
- `opcode_replace` count: `151` unchanged
- `total_genesis_bytes_covered`: `0x1822FC -> 0x182318`
- Numbered artifact: `dist/rastan-direct/rastan_direct_video_test_build_0171.bin`
- Rolling artifact: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Numbered/rolling SHA256: `819a2131a7643135b46c6faaaf00153ac95c37fae2ed357659fed74075d45ab9`
- Size: `1,581,848` bytes
- Counter: `171`

## Static Verification

Generated disassembly confirms:

- `vdp_project_bg_tall_if_dirty = runtime_genesis_pc 0x0007013C`.
- It computes `(-staged_scroll_y_bg + 8) & 0x01ff`, shifts by 3, masks with `0x003f`, and stores the result in `bg_tall_project_base`.
- It loops 32 rows; each row computes `(base + visible_row) & 0x003f`, shifts by 7 bytes, copies 64 words, then marks `bg_row_dirty = 0xffffffff`.
- `vdp_commit_scroll = runtime_genesis_pc 0x00070276` keeps the existing `-raw + 8` logic and applies `andi.w #0x0007` only when `genesistan_current_scene_id == 1`.

Key symbols:

- `staged_bg_buffer = 0x00FF40A2`
- `staged_bg_tall_buffer = 0x00FF50A2`
- `bg_tall_dirty = 0x00FF4006`
- `bg_tall_project_base = 0x00FF4008`
- `genesistan_current_scene_id = 0x00FF9478`

## Runtime Validation

Trace directory:

`states/traces/build0171_tall_bg_projection_rowbase_20260714_200031/`

Primary files:

- `trace_build0171_rowbase.lua`
- `build0171_rowbase_samples.csv`
- `build0171_rowbase_summary.log`
- `build0171_frame_0571.png`
- `build0171_frame_0751.png`
- `build0171_frame_1081.png`
- `build0171_frame_1600.png`
- `build0171_frame_2200.png`
- Build 0170 comparison under `build0170_compare/`

The trace auto-inserted coin/start, sampled through frame 2420, and exited with status `0`.

### Build 0170 vs Build 0171 rolling-row check

The same sampler compares each selected `staged_bg_buffer` cell against the tall-buffer row that should be projected by the rolling base formula.

- Build 0170 comparison: `24 / 204` sampled cells matched; `180 / 204` did not.
- Build 0171: `192 / 204` sampled cells matched; `12 / 204` did not.
- All Build 0171 mismatches were at frame `751`, where the post-frame sampled scroll value implied row base `0x14` while `bg_tall_project_base` still recorded `0x13`.

The frame-751 mismatch is treated as a sampling/timing caveat rather than proof of a steady projection failure: the trace samples at MAME `frame_done`, after the arcade VBlank body can prepare next-frame scroll state, while projection/commit happen earlier in the Genesis VBlank service. By frame `820` and all later sampled frames, projected rows match the rolling tall-buffer row base again.

### Frame 571

State: `2/3/0`, scene `1`, raw BG Y scroll `0x0000`, full vscroll `0x008`, row base `0x01`, residual `0`, project base `0x0001`.

Result: all sampled rows match the corresponding tall-buffer rows. Screenshot shows coherent sky/clouds, left wall, and lower-right mountain/terrain. Expected ground/floor under Rastan is still not present.

### Frame 751

State: `2/3/0`, scene `1`, raw BG Y scroll `0x0167`, full vscroll `0x0A1`, sampled row base `0x14`, residual `1`, project base `0x0013`.

Result: 12 sampled rows mismatch the post-frame row-base calculation. Screenshot nevertheless shows a coherent mountain band across the visible window, which is a major improvement over the Build 0170 half-select behavior. This is recorded as a likely frame-boundary/timing artifact requiring caution, not a reason to broaden the fix.

### Frame 1081

State: `2/3/0`, scene `1`, raw BG Y scroll `0x0149`, full vscroll `0x0BF`, row base `0x17`, residual `7`, project base `0x0017`.

Result: all sampled rows match the corresponding tall-buffer rows. Screenshot shows coherent sky/mountains, but also a black horizontal gap/band and missing usable ground/floor; the player is down near the lower-left area.

### Later frames

Frames `1600`, `1800`, `2000`, `2200`, `2400`, and final `2420` remain at row base `0x17`, residual `7`, project base `0x0017`, with sampled rows matching. Screenshots at `1600` and `2200` continue showing coherent mountains but retain the black horizontal gap and no proven correct ground/floor.

The scripted MAME trace did not reproduce the violet/purple sky palette transition or stage reset seen in Tighe's Build 0170 BlastEm video. That observation remains user-reported Build 0170 visual evidence and is not resolved by this trace.

## Results By Region

Sky region: **improved / preserved.** The sky/cloud region remains coherent in Build 0171 screenshots and row-base samples.

Mountain / vertical terrain region: **materially improved.** Build 0171 replaces Build 0170's 0/32 half selection with a rolling row base and visually restores coherent mountain bands at frames 751+.

Ground/floor region: **still unresolved.** The expected ground/floor where Rastan should stand is still not proven present. The visible black horizontal band suggests a remaining visible-window/content/plane issue outside this exact projection-row fix.

Left wall / vertical terrain: **present and coherent enough for this pass.** The left wall remains visible through sampled gameplay frames.

## Gameplay / Control Notes

Rastan remains visible in MAME screenshots. The scripted validation used only coin/start input; no directional/jump/attack control validation was attempted. The prior Build 0170 user observation remains: automatic forward walking with zero user input and ineffective directional/jump/attack are still open until a dedicated input/control trace says otherwise.

The trace did not observe mode `0x0008` in the sampled window. Real Genesis hardware ground-contact/freeze behavior still requires Tighe verification for Build 0171.

## Classification

Implementation classification: **bounded projection fix**.

Build 0171 proves that Build 0170's remaining terrain-row problem was primarily the half-buffer projection model: Build 0170 could preserve selected anchors while still projecting the wrong visible window over time. Build 0171 corrects that to a rolling 64-row projection with residual-only VSRAM in gameplay scene 1.

This does **not** close OPEN-017 or OPEN-001. The black horizontal band / missing ground/floor, automatic movement, input/control, collision byte-equivalence, real Genesis hardware behavior, sprite/READY/header, D00298, Exodus, and continue/game-over issues remain deferred.

## OPEN / CLOSED Issues Impact

- Open issues touched: OPEN-017, OPEN-001 context.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: input/control, collision byte-equivalence, real Genesis hardware freeze/contact behavior, PC090OJ/READY/header sprites, VBlank/rolling bar/slowdown, D00298, Exodus, continue/game-over, and records `132..134`.

## KNOWN_FINDINGS Impact

Option C: KF-038 should be refined with Build 0171 evidence. The durable mechanism is that long/tall Stage 1 PC080SN BG content needs a rolling 64-row visible projection, not merely a 0/32 half-select.

## STOP

STOP triggered: **NO**. Build 0171 was produced and validated as a bounded projection candidate. Acceptance remains pending Tighe visual/hardware testing.
