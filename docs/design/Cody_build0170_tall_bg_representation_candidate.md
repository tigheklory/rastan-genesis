# Cody - Build 0170 Tall BG Representation / Visible-Window Projection Candidate

**Date:** 2026-07-14  
**Type:** Implementation + build + bounded runtime validation  
**Baseline:** Build 0169 `dist/rastan-direct/rastan_direct_video_test_build_0169.bin`, SHA `b8c87809fe84650b8c31b7b835469609034fca29cf43a4f2aeb669925acc1634`, counter `169`  
**Produced build:** Build 0170 `dist/rastan-direct/rastan_direct_video_test_build_0170.bin`  
**Build 0170 SHA256:** `562ef83673deaf47d28adbcad2ab5457ea974ed7eff778c2f471d5e8ca3a18d5`  
**Build 0170 size:** `1,581,820` bytes

## Phase 0

Classification: **EXTENDING** (OPEN-017 / KF-038 Stage 1 long-BG row alias). Read/applied: `RULES.md`, `ARCHITECTURE.md`, current `AGENTS_LOG.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, and the prior Build 0170 Stage 1 BG source/window trace evidence.

Relevant priors: KF-038 (long PC080SN BG rows alias in 32-row staging), KF-040/KF-041 (Stage 1 gameplay BG producer family and runtime tile model), KF-010 (BG -> Plane B staging/commit), KF-036/KF-039 (mapped work-RAM discipline), and OPEN-017 current gameplay visual/hardware context.

Architecture compliance: **CONFIRMED**. Arcade code remains the program. The implementation adds Genesis-side helper/staging representation for a proven PC080SN hardware-contract gap, returns to arcade flow, and reuses the existing staging -> VBlank commit -> VDP path. No player-state, collision, input, PC090OJ, D00298, Exodus, READY/header, continue/game-over, or broad VBlank rewrite was performed.

Contradiction detected: **NO**.

## Implementation Option Used

Implemented a gameplay-only version of **Option A/C**:

- Add a 64-row virtual BG backing buffer for the Stage 1 gameplay item-strip source family.
- Route only gameplay item-strip strips (`0x0000D31C <= source < 0x0000FB1C`) into the tall buffer.
- Keep non-gameplay strips on the existing 32-row `genesistan_hook_tilemap_bg_fill` path.
- During VBlank, when `genesistan_current_scene_id == 1`, project the currently selected 32-row half into the existing `staged_bg_buffer`, then let the existing `vdp_commit_bg_strips_if_dirty` copy Plane B rows to VRAM.

This avoids globally changing `genesistan_hook_tilemap_bg_fill` row mapping and avoids changing title/story/high-score/item-page 32-row behavior.

## Source Changes

### `apps/rastan-direct/src/tilemap_hooks.s`

Added `genesistan_hook_tilemap_bg_fill_tall`:

- Validates BG C-window destination `HW_ADDRESS 0x00C00000..0x00C03FFF`.
- Converts PC080SN code/attr through the same existing tile and attr LUTs as `genesistan_hook_tilemap_bg_fill`.
- Computes a 64-row row index with `row = ((dest - 0x00C00000) >> 2 >> 6) & 0x3F`.
- Stores into `staged_bg_tall_buffer` at `row64*128 + col*2`.
- Sets `bg_tall_dirty`.

Updated `genesistan_hook_itempage_strip_blit`:

- Saves/restores `%d6` in addition to `%d1`.
- Detects gameplay strip sources by the already-proven source family `[0x0000D31C, 0x0000FB1C)`.
- For gameplay sources, calls `genesistan_hook_tilemap_bg_fill_tall`.
- For all other sources, keeps calling `genesistan_hook_tilemap_bg_fill`.

Static disassembly anchors:

```asm
719c8: move.l  (%a3),%d0
719d0: cmp.l   #0x0000d31c,%d0
719d8: cmp.l   #0x0000fb1c,%d0
719e0: moveq   #1,%d6
71a28: tst.w   %d6
71a2c: bsr.w   0x708d6 ; genesistan_hook_tilemap_bg_fill_tall
71a32: bsr.w   0x70800 ; genesistan_hook_tilemap_bg_fill
```

### `apps/rastan-direct/src/vdp_comm.s`

Added `vdp_project_bg_tall_if_dirty` and called it before the normal BG row commit.

Projection rule:

```asm
move.w  staged_scroll_y_bg,%d0
neg.w   %d0
addq.w  #8,%d0
andi.w  #0x01ff,%d0
lsr.w   #3,%d0
andi.w  #0x0020,%d0
```

Interpretation: Build 0166's `-raw + 8` convention is used only to select the tall-map half (`0` or `32` rows). The Genesis VSRAM scroll commit still owns the fine row position. For the validated Stage 1 post-landing camera (`staged_scroll_y_bg = 0x0149`), the projection base is `0x0000`, so rows `0..31` project into the 32-row Plane-B staging buffer and rows `32..63` stay preserved in tall backing instead of alias-overwriting visible rows.

Static disassembly anchors:

```asm
700da: bsr.w 0x7013c ; vdp_project_bg_tall_if_dirty
7013c: cmp.b #1,0x00ff9478 ; genesistan_current_scene_id
7014a: move.w 0x00ff409e,%d0 ; staged_scroll_y_bg
7015a: and.w #0x0020,%d0
7017c: lea 0x00ff50a2,%a0 ; staged_bg_tall_buffer
7018c: lea 0x00ff40a2,%a1 ; staged_bg_buffer
7019c: move.l #0xffffffff,0x00ff4002 ; bg_row_dirty
```

### `apps/rastan-direct/src/boot/boot.s`

Extended `_bootstrap_clear_staging` to clear:

- `bg_tall_dirty`
- `bg_tall_project_base`
- all `4096` words of `staged_bg_tall_buffer`

## Symbols

Build 0170 symbol verification:

- `vdp_project_bg_tall_if_dirty = runtime_genesis_pc 0x0007013C`
- `genesistan_hook_tilemap_bg_fill_tall = runtime_genesis_pc 0x000708D6`
- `genesistan_hook_itempage_strip_blit = runtime_genesis_pc 0x000719BC`
- `bg_tall_dirty = Genesis-WRAM 0x00FF4006`
- `bg_tall_project_base = Genesis-WRAM 0x00FF4008`
- `staged_bg_buffer = Genesis-WRAM 0x00FF40A2`
- `staged_bg_tall_buffer = Genesis-WRAM 0x00FF50A2`
- `staged_fg_buffer = Genesis-WRAM 0x00FF70A2`
- `genesistan_current_scene_id = Genesis-WRAM 0x00FF9478`

## Build Result

Command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **PASS** after one expected invariant correction.

- First release attempt assembled/linked, then stopped at the canonical coverage gate: expected `0x1821A8`, observed `0x1822FC`, opcode_replace count unchanged `151`.
- Updated only canonical total coverage constants in `tools/translation/postpatch_startup_rom.py` and `tools/translation/verify_canonical_rom.py`.
- Second release passed: `GATE_PASS`, boot guard PASS.
- `opcode_replace` count stayed `151`.
- `total_genesis_bytes_covered`: `0x1821A8 -> 0x1822FC`.
- Numbered artifact: `dist/rastan-direct/rastan_direct_video_test_build_0170.bin`.
- Rolling artifact: `apps/rastan-direct/dist/rastan_direct_video_test.bin`.
- `cmp` rolling vs numbered: `0` (byte-identical).
- Release trace: `states/traces/rastan_direct_video_test_build_0170_mame_30s_20260714_193248/`.

## Runtime Validation

Trace directory:

`states/traces/build0170_tall_bg_validation_20260714_193346/`

Primary files:

- `validate_tall_bg.lua`
- `build0170_tall_bg_snapshots.csv`
- `postlanding_region_trace_build0170.lua`
- `genesis_zero_postlanding_regions.csv`
- `genesis_zero_events.log`

MAME exited cleanly (`exit_code=0`).

### Required Alias Anchors

At frame `820`, state is `2/3/0`, scene `1`, player `X=0x0020`, `Y=0x0070`, camera/scroll Y `0x0149`, and projection base `0x0000`.

| Anchor | Build 0169 failure | Build 0170 staged | Build 0170 tall backing | Result |
|---|---|---:|---:|---|
| `YELLOW_2_16` row 7 col 0 | row 39 alias overwrote `0x40D3` with `0x4281` | `0x40D3` | row 39 retained as `0x4281` | PASS |
| `BLACK_2_0` row 23 col 0 | row 55 alias overwrote raw `0x0602` slot with `0x425A` | `0x41C8` | row 55 retained as `0x425A` | PASS |
| `MOUNTAIN_8_9` row 0 col 6 | row 32 alias overwrote raw `0x04AC` slot with `0x422C` | `0x4073` | row 32 retained as `0x422C` | PASS |

The same six checks pass at frames `540`, `620`, `760`, `820`, `900`, and final frame `930` in `build0170_tall_bg_snapshots.csv`.

### Broader State Checks

From `genesis_zero_events.log`:

- Frame `820`: state `2/3/0`, player `0020/0070`, mode `0003`, flags `0004`, move `0000`.
- Camera/scroll at frame `820`: `cam=0000/0149`, `scroll_bg=0000/0149`, `scroll_fg=0000/0149`.
- Staging density at frame `820`: `bg_nz=2048`, `fg_nz=2048`.
- Collision sample at frame `820`: `coll_here=0000`.

Interpretation: the row-alias mechanism is fixed for the sampled Stage 1 post-landing BG terrain cells, and the Build 0166 vertical scroll sign convention remains present. This trace does not prove full visual acceptance on real Genesis hardware.

## Required Result Fields

- `YELLOW_2_16`: PASS, staged `0x40D3` retained.
- `BLACK_2_0`: PASS, staged `0x41C8` retained; not overwritten by row 55 `0x425A`.
- `MOUNTAIN_8_9`: PASS, staged `0x4073` retained; not overwritten by row 32 `0x422C`.
- Sky region result: sampled terrain cells now use the lower/visible half rather than row+32 aliases; full visual sky acceptance remains user/hardware verification.
- Ground/platform region result: required yellow/black terrain anchors pass; full platform visual acceptance remains user/hardware verification.
- Wall/mountain result: required mountain anchor passes; full wall/palette acceptance remains user/hardware verification.
- Vertical scroll result: scripted trace still reaches `cam_y/scroll_y_bg = 0x0149`; projection base remains `0`, matching the intended visible half for this opening window.
- Player fall/landing result: scripted trace reaches `Y=0x0070` and grounded flags by frame `820`.
- Auto-walk result: still present in scripted trace (`player_x` later advances: frame `900` `0x0028`, final `0x0037`), not fixed by this task.
- Input/control result: not addressed.
- Mode-8/death result: no mode-8 transition in this validation window; real Genesis ground-contact freeze remains user-reported/deferred.
- Real Genesis freeze note: not tested here; remains OPEN-017 context.

## Non-Regression / Scope Notes

- Non-gameplay 32-row screens are guarded because only the proven gameplay strip source family `[0xD31C,0xFB1C)` calls the tall helper; other item/story/high-score/title routes keep `genesistan_hook_tilemap_bg_fill` unchanged.
- The VBlank projection is additionally gated by `genesistan_current_scene_id == 1`, so stale tall backing is not projected during non-gameplay scenes.
- No PC090OJ code was modified.
- No collision-map logic was modified.
- No input/player state was modified.
- No D00298, Exodus, continue/game-over, READY/header, or broad VBlank rewrite was attempted.

## Open / Closed Issues Impact

- Open issues touched: OPEN-017, OPEN-001 context.
- New issues opened: NONE.
- Issues closed: NONE.
- Intentionally deferred: real Genesis freeze at ground contact, automatic movement/input, remaining collision byte-equivalence, full visual terrain acceptance, PC090OJ/READY/header sprites, VBlank/rolling bar/slowdown, continue/game-over, D00298, Exodus loop, records `132..134`.

## KNOWN_FINDINGS Impact

Option C: KF-038 updated with Build 0170 implementation/validation evidence. The original aliasing finding remains active for broader architectural follow-up, especially non-gameplay long-BG paths and later gameplay windows beyond the sampled opening.

## STOP

STOP triggered: **NO**.
