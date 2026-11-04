# Build 0534 — R1-S2 Visible Plane-A Edge and Green-Knight Rope Palette

**Agent:** Cody  
**Date:** 2026-11-04  
**Status:** Build 0534 is a gameplay-test candidate. It is not accepted until Tighe verifies it.  
**Baseline disposition:** Build 0533 is rejected for R1-S2 Plane-A gameplay because its 32-row residency assumption caused a broad regression above the formerly isolated bad row.

## Outcome

Build 0534 removes the Build-0533 Plane-A regression and corrects the missing rope-animation coverage for the existing Round-1 green sword-knight palette decision.

The Plane-A correction does not suppress ordinary arcade selector-1/2 authoring. Those writes, including the four-row offscreen prefetch margin around the 28-row NTSC display, again stage their native rows normally. When such an ordinary call also crosses a camera row before the retained no-publication hook can run, the native path materializes only the newly visible Plane-A edge row. Plane B is not republished by this correction.

The palette correction does not change Tighe's approved mapping. It expands the production consumer to the complete source-selected normal and rope animation domain for actor base `$033E`, so the knight no longer falls back to un-reindexed graphics merely because it changes to rope mode.

## Why Build 0533 made the scenery worse

Build 0533 interpreted all 32 physical Plane-A rows as the visible camera window. Genesis NTSC displays 28 tile rows; the other four physical rows are a valid offscreen prefetch margin. Build 0533 consequently suppressed legitimate selector-1/2 rows outside its assumed 32-row window and reconstructed later rows through the pan-row path. That destroyed the producer history which the original arcade retains and explains why many rows above the old isolated fault became wrong.

Re-reduction of Tighe's Build-0532 minimal-jump trace at marker frame 2106, FG Y `$0021`, record 17, selector 1, front 5 proves only one visible mismatch when the actual 28-row display is used:

- physical row 0 should contain logical row 0, but retained logical row 32 from record 16;
- the formerly reported physical-row-27/logical-row-59 mismatch is outside the visible 28-row interval and is legitimate prefetch state, not visible corruption.

Therefore Build 0534 restores ordinary prefetch authoring and addresses only the visible row that can enter before the no-publication path runs.

## Plane-A implementation

The correction is in `genesistan_hook_tilemap_plane_a_selector12_native` in `apps/rastan-direct/src/tilemap_hooks.s`:

- The ordinary selector-1/2 semantic authoring event again stages its complete physical row and records its provenance, including offscreen prefetch rows.
- The pre-step and projected post-step visible tops are retained.
- If selector 1 crosses a display row, the newly entering top row is published through the existing native row publisher.
- If selector 2 crosses a display row, the newly entering bottom row at `top + 27` is published.
- Initial 64-row scene reconstruction retains its existing bounded projection behavior.
- Collision authoring remains complete.
- Plane B is untouched.

This uses the existing staged Plane-A buffer, per-physical-row provenance, dirty-row publication, and native row assets. It adds no shadow tilemap, full-scene backing map, duplicate graphics buffer, row-number special case, or input/jump special case.

### Semantic boundary

The retained semantic decision is the arcade selector's decision to author a logical row and the camera transition that makes an edge row visible. The retired chip tail remains the PC080SN C08000/name-RAM execution below that decision. Build 0534 emits final Genesis Plane-A name words through the existing native publisher; it does not restore a PC080SN device or its 64-row RAM.

No additional legacy chip path is removed by this corrective build. Transitional staged/provenance state already used by the native Plane-A implementation remains; broader removal is outside this task.

## Green sword-knight rope palette

Affected Palette Decision ID: `PAL-PC090OJ-R1S2-GREEN-SWORD-KNIGHT-001` (`decided`). The decision and its index mapping are unchanged.

Original arcade routine `$04684E` proves that the family-2 actor's displayed animation domain changes with `actor+$3E`:

- normal mode (`actor+$3E == 2`) uses `$93`, `$94`, `$95`, and `$96`;
- rope mode (`actor+$3E == 8`) uses base `$4D` plus table offsets `{0,$09,$0A,$0B,$0C,$0D}`, producing `$4D,$56,$57,$58,$59,$5A`.

The prior generator covered the normal codes plus unrelated ranked frames, but omitted the rope programs. `tools/graphics_editor/gen_reindexed_pc090oj.py` and the Palette Composer consumer now use the exact domain:

`$93,$94,$95,$96,$4D,$56,$57,$58,$59,$5A`

The offline generator resolves those programs through the existing compositor and reindexes their final Genesis pattern cells under Tighe's approved object usage. No PC090OJ object-RAM mirror, runtime palette heuristic, or sprite-device emulation is added.

### Semantic boundary

The retained semantics are the actor base, mode, and arcade-selected animation program. The chip-specific PC090OJ pattern/palette realization remains removed: the build-time consumer emits the final Genesis pattern variants consumed by the existing native SAT path.

## Source changes

- `apps/rastan-direct/src/tilemap_hooks.s`
- `tools/translation/verify_bg_a_incremental_background.py`
- `tools/diagnostics/reduce_r1s2_build0532_remaining_trace.py`
- `tools/graphics_editor/gen_reindexed_pc090oj.py`
- `tools/graphics_editor/server.py`
- `tools/graphics_editor/verify_green_knight.py`
- `tools/graphics_editor/verify_reindexed_pc090oj.py`

Source commit: `0a61245403911d3da8291a978d384fb621cd500a` (`Fix visible Plane A edge and knight rope palette`).

## Verification

Static/source verification:

- Updated Build-0532 trace reducer: `implicated_rows=1`; only physical row 0 is a visible mismatch at the marker.
- Native incremental Plane-A verifier: PASS.
- Selector-1/2 segment verifier: PASS.
- Green-knight verifier: all 15 checks PASS, including exact normal-plus-rope animation coverage and unchanged `Test.json`.
- Reindexed PC090OJ verifier: 984 requirements, 857 unique codes, 127 variant cells, 0 mismatches, 0 incomplete mappings, 0 stray variants; `$04684E` normal-plus-rope domain 54/54 cells covered exactly.
- Palette profile SHA-256 remained `24914ababc7fab52aac8258dd1f9f7b3d5df230b81421c03d9ce68d1526135ae`.
- Python syntax checks for all changed Python consumers/verifiers: PASS.

Build and runtime verification:

- Canonical gate: PASS.
- Patch manifest: 228 expected opcode-replacement sites; expected Genesis coverage `$39DEB8`.
- Gameplay-entry verification: PASS.
- Six Round-1 epoch/package cases: PASS.
- Mandatory 30-second **GENESIS NTSC MAME** trace: PASS at `states/traces/rastan_direct_video_test_build_0534_mame_30s_20261104_123112`.
- Normal and invincible R1-S2 functional starts under **GENESIS NTSC MAME**: PASS at frame 412, stage `$0010`, record `$0011`, package 5, complete Plane A/B, and zero map misses.
- Complete configured ROM family and invincibility contract: PASS.

These automated results establish build integrity and the targeted source contracts. They are not gameplay acceptance.

## ROMs

Counter and consumed ledger advanced from 0533 to 0534. All Build-0534 artifacts are preserved and are 3,792,568 bytes.

Primary gameplay artifacts:

| Purpose | Path | SHA-256 |
|---|---|---|
| Normal game | `dist/rastan-direct/rastan_direct_video_test_build_0534.bin` | `a8daaf58694a70a1f70ae4711698601a2fccaff96aa7affa2bc67f84e3334068` |
| R1-S2 direct start | `dist/rastan-direct/rastan_direct_video_test_build_0534_S1-2.bin` | `70f9f668e2c3355dd436e4398333e18cdd5f2d0c611a23977cd0ec3194b055dd` |
| Invincible R1-S2 direct start | `dist/rastan-direct/rastan_direct_video_test_build_0534_invincible_S1-2.bin` | `6a0006af4b7d112a32a12f368398fda02be83385cd12668a2beaab8d24ecd9a0` |

Other preserved family artifacts:

| Suffix | SHA-256 |
|---|---|
| `_c` | `cd7662527c5cbbf74be212444bd0101bfdf45101ee96f82a9ab862c8c60dd78f` |
| `_d` | `61ef54427da4b8955193771d879b679f90d9f56d75314dfa913ee02111fb0eae` |
| `_do` | `be86a9c781776c9ede0001a37e3735861808901a65acf479f05b034da5ae2fcc` |
| `_full_hud` | `0c89caf2576ed20bb3a50736f06130f1b3a25224cb6c0e68331a04859b448e8c` |
| `_invincible` | `ce4eb455b82072b222727e87cdd179c3f9c193c6c3f97a084ea9f7ec94345348` |
| `_s` | `1f8f9459d889bc98e01ed3c1c8dee95c61b88edf138d9447754b4feb7e5691be` |

## USER MUST VERIFY

Use `rastan_direct_video_test_build_0534_invincible_S1-2.bin` and check all of the following in one or more fresh runs:

1. Climb normally through records 16, 17, and 21 and confirm the former isolated 8-pixel stale strip is gone.
2. Aggressively jump-climb the chains through the same records and inspect the entire region above the former bad row; Build 0533's many-row regression must not recur.
3. Reverse vertical direction around row crossings and confirm already displayed scenery remains stable.
4. Observe the green sword knights during ordinary movement and while they climb a rope. Their approved green palette must remain consistent in both modes.
5. Report the first incorrect screen position if any defect remains. A trace is not requested unless gameplay still shows a defect.

Build 0534 remains a candidate until this gameplay verification is complete. No claim is made that later-record or predecessor-only corruption is fixed beyond what the implementation and tests establish.

