# Cody Build 0252 Runtime Legacy Hot-Path Retirement Audit

## Baseline
- Accepted input build: Build 0251.
- Build 0251 ROM: `dist/rastan-direct/rastan_direct_video_test_build_0251.bin`.
- Build 0251 SHA-256: `985889dee869892a8f023f60103366a3debf3e2c3732bb727aa6a66d16022d7b`.
- Build 0251 counter: `251`.
- Build 0251 context: native gameplay PC090OJ path restored Rastan `PLAYER_BODY` queue lifetime by moving `native_sprite_frame_begin` to the 0x41F5E player-body hook before any gameplay sprite producer queues are consumed.
- Current task classification: focused runtime legacy hot-path retirement audit plus one bounded cleanup.

## Phase 0 Statement
- Architecture rule applied: arcade semantic decisions remain the program; Genesis code is a helper/opcode-replacement/native VDP/SAT realization only.
- Native replacement policy applied: final PC080SN/PC090OJ work must cut before chip-specific tails and must not rely on virtual chip RAM, generic chip-address projection, or C-window/object-RAM mirrors as the final rendering architecture.
- Relevant known findings: KF-066 (bank 0x36 line-0 carrier path), KF-068 (native replacement policy / full video-surface direction), KF-069 (object table is still arcade persistent object state, not a final PC090OJ mirror), KF-071/KF-072 (N2 display-on/native plane ownership corrections).
- Rediscovery hazards touched: legacy PC080SN tall projectors, old PC090OJ compatibility emitter, native gameplay sprite lifecycle.
- Open issues touched: OPEN-017 and OPEN-024-adjacent rendering/performance architecture.
- Closed issues touched: none.
- Contradiction of confirmed or strong finding: none.

## Files And Evidence Inspected
- `RULES.md`, `ARCHITECTURE.md`, `AGENTS.md`, `AGENTS_LOG.md` latest relevant entries.
- `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`.
- `docs/design/Andy_build0249_shared_native_sprite_emitter_contract.md`.
- `docs/design/Cody_build0251_rastan_player_body_visibility_fix.md`.
- `apps/rastan-direct/src/vdp_comm.s`.
- `apps/rastan-direct/src/pc090oj_hooks.s`.
- `apps/rastan-direct/out/symbol.txt`.
- `build/rastan-direct/rastan_direct_patch_manifest.json`.
- Runtime evidence directory: `states/traces/build0251_runtime_legacy_hotpath_retirement_20260803_181746/`.
- Build 0252 release smoke trace: `states/traces/rastan_direct_video_test_build_0252_mame_30s_20260803_182204/`.

## Current Visual Baseline
- User/task baseline: post-Build 0250/0251 native gameplay sprite build where Rastan renders again.
- Prior Build 0251 proof: `PLAYER_BODY` is queued before finalization and reaches the finalizer; old gameplay PC090OJ scanner/decoder/fill/copy path was not re-enabled.
- User visual verification remains required for Build 0252: Rastan visible in gameplay/SAT, lizard men visible, hurry-up bats visible, axe item visible, no duplicate Rastan, no stale bat corpse regression, and frontend/title/throne still render.

## Audited PC090OJ Paths

| Path | Runtime Genesis PC / Symbol | Classification | Build 0252 Action |
| --- | --- | --- | --- |
| Gameplay 0x41DAE dispatcher | `0x072C38 genesistan_pc090oj_hook_target_41dae` | native gameplay dispatcher; required | unchanged |
| Gameplay 0x41F5E player-body hook | `0x072C62 genesistan_pc090oj_hook_target_41f5e` | native player-body producer; required | unchanged |
| Gameplay 0x45DFA dispatcher | `0x072C7C genesistan_pc090oj_hook_target_45dfa` | native gameplay dispatcher; required | unchanged |
| Native queue clear | `0x072C96 native_sprite_frame_begin` | required once per gameplay frame before producer queueing | unchanged |
| Native semantic sprite enqueue | `0x072CC2 native_sprite_emit` | required native queue producer | unchanged |
| Native player block producer | `0x072DA6 native_stage_player_blocks_41f5e` | required for Rastan body/front elements | unchanged |
| Native finalizer | `0x07367C pc090oj_native_emit_pass` | required SAT producer for gameplay | unchanged |
| Legacy emitter | `0x073A90 pc090oj_legacy_emit_pass` | retained for non-gameplay/frontend compatibility only | unchanged |

Observation-only wording: `pc090oj_legacy_emit_pass` remains linked and can still be used by non-gameplay paths. In inspected source, gameplay dispatch enters `pc090oj_native_emit_pass` when `genesistan_current_scene_id == 1`; only non-gameplay falls through to `pc090oj_legacy_emit_pass`. Build 0252 did not modify this code.

## Audited PC080SN Paths

| Path | Runtime Genesis PC / Symbol | Classification | Build 0252 Action |
| --- | --- | --- | --- |
| `_vblank_service` | `0x0700C2` region, source lines 183-222 | VBlank owner of VDP commits | modified narrowly |
| Legacy BG tall projector | `0x070138 vdp_project_bg_tall_if_dirty` | transitional non-gameplay projector; gameplay body already skipped by scene guard | gameplay call bypassed at call site |
| Legacy FG tall projector | `0x0701B8 vdp_project_fg_tall_if_dirty` | transitional non-gameplay projector; gameplay body already skipped by scene guard | gameplay call bypassed at call site |
| BG strip commit | `0x0702A8 vdp_commit_bg_strips_if_dirty` | active VBlank BG row DMA commit | preserved in both branches |
| FG narrow commit | `0x0726AC vdp_commit_fg_narrow_strips` | active VBlank FG narrow-row commit | preserved in both branches |
| Native Plane A selector-0 | `0x070532 genesistan_hook_tilemap_plane_a_selector0_native` | native Plane A producer | unchanged |
| Native Plane A selector-1/2 | `0x070664 genesistan_hook_tilemap_plane_a_selector12_native` | native Plane A producer | unchanged |
| Plane B gameplay hook | `0x070B9C genesistan_hook_tilemap_plane_a` | current gameplay Plane B/native path area by symbol/source context | unchanged |

## Runtime Trace Evidence
- Trace directory: `states/traces/build0251_runtime_legacy_hotpath_retirement_20260803_181746/`.
- `legacy_hotpath_frames.tsv` recorded 2400 external frames.
- Gameplay scene coverage: 2085 frames with `genesistan_current_scene_id == 1`, from frame 316 through frame 2400.
- Gameplay state observed: state `2/3/0` from frame 370 onward in frame samples.
- Gameplay frame samples include PCs inside native/VDP code ranges, including `0x072CC8`, `0x072DA6`, `0x072EA8`, `0x0738F2`, `0x073954`, and `0x073D22`.
- Exact instruction-read taps counted early non-gameplay hits for the transitional projectors and legacy PC090OJ emitter, but under-counted later gameplay helper execution despite frame samples landing in those ranges. This trace is therefore used for scene/time coverage and sampled PC reachability, not as sole proof that a runtime path was absent.
- The cleanup is not based on an inferred zero counter. It is based on existing source control flow: both tall projector callees already return immediately when `genesistan_current_scene_id == 1`; Build 0252 hoists that already-existing gameplay skip to the VBlank call site while preserving the active commit calls.

## Retired Hot Path
- Retired/bypassed path: gameplay-scene calls from `_vblank_service` to `vdp_project_bg_tall_if_dirty` and `vdp_project_fg_tall_if_dirty`.
- Exact source boundary: `apps/rastan-direct/src/vdp_comm.s` in `_vblank_service`, after `vdp_commit_tiles_if_dirty` and before `vdp_commit_fg_narrow_strips`.
- New gameplay behavior:
  - If `genesistan_current_scene_id == 1`, skip the two legacy tall projector calls.
  - Still call `vdp_commit_bg_strips_if_dirty`.
  - Still call `vdp_commit_fg_narrow_strips`.
  - Still call sprite VRAM, palette reassertion, palette commit, scroll commit, and arcade VBlank tail jump exactly after that point.
- Non-gameplay behavior: call order remains `vdp_project_bg_tall_if_dirty`, `vdp_commit_bg_strips_if_dirty`, `vdp_project_fg_tall_if_dirty`.

## Why This Is Safe
- `vdp_project_bg_tall_if_dirty` already begins with `cmpi.b #1, genesistan_current_scene_id` followed by a branch to return in gameplay.
- `vdp_project_fg_tall_if_dirty` already begins with the same gameplay return guard.
- Therefore the skipped calls had no gameplay body side effects before Build 0252.
- `vdp_commit_bg_strips_if_dirty` remains active in gameplay, so dirty native BG rows can still reach VRAM.
- `vdp_commit_fg_narrow_strips` remains active in gameplay, so native/narrow Plane A updates remain committed.
- No PC090OJ source path was changed.
- No palette, CRAM, collision, rope, scroll, player state, audio, or frontend logic was changed.

## Rejected Candidate Retirements
- Do not remove `pc090oj_object_ram`: KF-069 says the object table is still arcade persistent object state, not merely final renderer mirror state.
- Do not bypass `pc090oj_legacy_emit_pass` globally: frontend/non-gameplay compatibility still needs it until those semantic cuts are converted.
- Do not remove `vdp_project_bg_tall_if_dirty` or `vdp_project_fg_tall_if_dirty` globally: they remain transitional non-gameplay helpers.
- Do not alter native sprite finalizer ordering: Build 0251 just fixed Rastan `PLAYER_BODY` lifecycle.

## Build 0252 Implementation
- File changed: `apps/rastan-direct/src/vdp_comm.s`.
- Functional change: add a scene-1 call-site gate in `_vblank_service` around the legacy tall projector calls.
- Canonical invariant update: `tools/translation/postpatch_startup_rom.py` and `tools/translation/verify_canonical_rom.py` updated from `0x184C8C` to `0x184C9C` to account for the 16-byte call-site gate growth.
- Opcode replacement count: unchanged at `218`.
- Manifest expectation after build: `postpatch_expected_opcode_replace_sites=218`, `postpatch_expected_total_genesis_bytes_covered=0x184C9C`.

## Build 0252 Verification
- Build command: `make -C apps/rastan-direct release RASTAN_GAMEPLAY_HUD_SPRITES=2`.
- Result: `GATE_PASS`.
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0252.bin`.
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`.
- SHA-256: `5f1457bcebd1f77e496de0cce54de6de5e41ad9846073d50d55e6e6debece948` for both numbered and rolling artifacts.
- Size: `1592476` bytes for both numbered and rolling artifacts.
- Counter: `252`.
- Standard MAME release trace: `states/traces/rastan_direct_video_test_build_0252_mame_30s_20260803_182204/`.
- Trace summary: `frames=1798`; `vdp_ports_live count=47197`; no unique unmapped memory addresses; final PC `0x073DAC`; SP `0x00FEFF7C`.
- Numbered artifacts preserved: no numbered ROM was deleted or overwritten.

## Open/Closed Issues Impact
- Open issues touched: OPEN-017, OPEN-024-adjacent native rendering/performance cleanup.
- New issues opened: none.
- Issues closed: none.
- Issues intentionally deferred: full removal of non-gameplay legacy projector paths and non-gameplay PC090OJ compatibility emitter.

## KNOWN_FINDINGS Impact
- Option A: no new finding to index.
- This build applies existing native-replacement direction from KF-068/KF-069/KF-071/KF-072 and does not contradict any indexed finding.

## User Verification Scope
- Verify Build 0252 in BlastEm/Exodus/Nomad if desired.
- Confirm Rastan is still visible in gameplay and present in VDP Sprite Viewer/SAT.
- Confirm lizard men, hurry-up bats, and axe item remain visible.
- Confirm no duplicate Rastan and no stale bat corpse regression.
- Confirm frontend/title/throne still render.
- Watch for any speed/visual regression from the VBlank call-site change.

## STOP Status
- STOP triggered: NO.
- Exact cleanup boundary is established and bounded.
- Build produced: YES, exactly Build 0252.
