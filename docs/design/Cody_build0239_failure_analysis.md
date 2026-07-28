# Cody - Build 0239 Failure Analysis and Build 0235 Production Restore

> **HISTORICAL BUILD REPORT (banner added 2026-07-28):** This is preserved build/failure evidence. Its facts (builds, SHAs, results) are **unchanged**. The graphics architecture it describes is governed and, where it conflicts, **superseded** by the canonical `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md` (and `RULES.md` §11). Read the policy before using this as an architecture reference.


**Date:** 2026-07-27  
**Type:** Rejection analysis / production-source restoration only  
**Rejected build:** `dist/rastan-direct/rastan_direct_video_test_build_0239.bin`  
**Rejected SHA256:** `f1d6075c801f8a0326084edec79c2850decc26f8569abc2a7eb1328b8677813b`  
**Accepted baseline restored:** Build 0235, SHA256 `9aff0b11fb9a2151186ef0c03654fdd968d630a3cab45801be85de6f62571ad5`  
**Counter:** `239` retained. Build 0239 is consumed and preserved.  
**Scope:** No implementation correction, no build, no counter advance, no ROM deletion.

## Result

Build 0239 is rejected. Its ROM, generated build evidence, trace, implementation document, and production-source diff were preserved. The production source paths changed by Build 0239 were restored to the accepted Build 0235 state.

## Preserved Build 0239 Evidence

- Rejected ROM: `dist/rastan-direct/rastan_direct_video_test_build_0239.bin`
- Rejected ROM SHA256: `f1d6075c801f8a0326084edec79c2850decc26f8569abc2a7eb1328b8677813b`
- Automatic trace: `states/traces/rastan_direct_video_test_build_0239_mame_30s_20260727_212759/`
- Implementation result doc: `docs/design/Cody_pc080sn_native_ym7101_implementation_result.md`
- Rejection/restore evidence directory: `states/traces/build0239_rejection_baseline_restore_20260727_220828/`
- Full Build-0235-to-0239 production diff: `states/traces/build0239_rejection_baseline_restore_20260727_220828/build0235_to_build0239_production.diff`
- Diffstat: `states/traces/build0239_rejection_baseline_restore_20260727_220828/build0235_to_build0239_production.diffstat`
- Rejected 0239 source snapshot: `states/traces/build0239_rejection_baseline_restore_20260727_220828/source_snapshot_0239/`

No numbered ROM artifacts were deleted or overwritten.

## Build 0239 Files Changed

Production-source diff recorded from Build 0235 state to rejected Build 0239 state:

```text
apps/rastan-direct/src/boot/boot.s         |   2 +
apps/rastan-direct/src/tilemap_hooks.s     | 267 +++++++++++++++++++++++++++--
apps/rastan-direct/src/vdp_comm.s          |  21 +--
tools/translation/postpatch_startup_rom.py |   4 +-
tools/translation/verify_canonical_rom.py  |   4 +-
5 files changed, 267 insertions(+), 31 deletions(-)
```

Generated/build artifacts also remained dirty from producing Build 0239, including `apps/rastan-direct/out/*`, `build/genesis_postpatch.disasm.txt`, `build/rastan-direct/address_map.json`, `build/rastan-direct/rastan_direct_patch_manifest.json`, `build/rastan-direct/startup_common_relocations.json`, `build/rom_inventory.json`, and the MAME trace copy under `build/mame/home/genesistrace/`. These were preserved as Build 0239 evidence and were not treated as production source for this restore.

## Exact Production Diff

The exact production diff is preserved verbatim at:

`states/traces/build0239_rejection_baseline_restore_20260727_220828/build0235_to_build0239_production.diff`

High-level content of that diff:

- `apps/rastan-direct/src/vdp_comm.s`
  - Removed live VBlank calls to `vdp_project_bg_tall_if_dirty` and `vdp_project_fg_tall_if_dirty`.
  - Added a live VBlank call to new `vdp_commit_bg_narrow_strips`.
  - Kept `vdp_commit_fg_narrow_strips` live.
  - Changed gameplay vertical scroll from residual `& 0x0007` to full native `& 0x01FF` for both planes.
  - Added `bg_narrow_desc_table` and `bg_narrow_desc_count` globals/storage.
- `apps/rastan-direct/src/tilemap_hooks.s`
  - Retargeted `genesistan_stage_fg_src_column` from tall-buffer publishing to resident-window narrow-descriptor publishing.
  - Added helper `.Lpc080sn_convert_cell_to_d3`.
  - Retargeted gameplay-classified `genesistan_hook_itempage_strip_blit`/BG strip output into a new native BG narrow path.
  - Added `vdp_commit_bg_narrow_strips`.
  - Changed C-window clear bookkeeping to clear narrow descriptor counts and mark BG tall dirty.
- `apps/rastan-direct/src/boot/boot.s`
  - Added bootstrap clearing for `bg_narrow_desc_count`.
- Canonical gate scripts
  - Updated total Genesis covered bytes from `0x183CD8` to `0x183D90` for Build 0239 helper growth.

## Legacy Scene-Fill / Projector Contradiction

Build 0239 disabled both tall projectors in VBlank while retaining legacy scene-fill ownership for the frontend and setup-like PC080SN paths. That left Plane A and Plane B incomplete because the retained scene-fill and clear paths still produced or invalidated content through the legacy tall-buffer model, but VBlank no longer projected those tall buffers to YM7101 nametables.

The contradiction was specifically:

- Legacy scene-fill and clear code still expected `vdp_project_bg_tall_if_dirty` and `vdp_project_fg_tall_if_dirty` to publish full/tall buffered state.
- Build 0239 removed those projectors from the live VBlank chain.
- The new narrow paths only emitted descriptors when movement/strip producers ran.
- Therefore, static/full-page scene state and transition clear state were not coherently published to Plane A/Plane B.

This is why Build 0239 could pass mechanical build gates while still being visually incoherent.

## Why Columns Appeared Incrementally During Movement

The new Build 0239 narrow paths were producer-triggered rather than full resident-window seeded. During movement, gameplay strip producers reached the retargeted Plane A/Plane B paths, wrote some resident rows into the 32-row staging buffers, and enqueued narrow descriptors. VBlank then committed those descriptors.

That means columns could appear incrementally as the camera/player movement caused more strip producer activity. However, there was no proven initial resident-window fill covering the whole visible 32-row YM7101 window after scene setup. Movement-driven strips were therefore additive/partial, not a replacement for the missing full projection contract.

## Likely READY-Screen Debris Cause

The likely READY-screen debris mechanism is stale nametable state plus mismatched clear/fill ownership:

- READY and transition screens rely on legacy clear/scene-fill behavior.
- Build 0239 left those legacy producers intact but removed the VBlank tall projectors that made their buffered clears/fills visible.
- C-window clear/tall-dirty state could be updated without a corresponding Plane A/Plane B nametable overwrite.
- Full native VSRAM values could also reveal previously written rows instead of the old residual 8-pixel projection window.

So the debris is most likely not a new tile decode failure. It is the visible result of stale YM7101 nametable cells surviving a transition because the legacy clear/fill producer contract and the live VBlank publication contract no longer matched.

## Inherited Helpers Audited

Relevant helpers inherited from older code and involved in, or adjacent to, Build 0239:

- `genesistan_stage_fg_src_column`
  - Older contract: replay Stage 1 FG through rebuilt pointer table into the gameplay-only tall FG backing helper.
  - Build 0239 changed it to resident-window direct staging and narrow enqueue.
- `genesistan_hook_tilemap_fg_fill_tall`
  - Older contract: tall FG staging plus dirty/projector ownership.
  - In Build 0239 it was bypassed by the retargeted FG path, but other legacy expectations remained.
- `genesistan_hook_tilemap_bg_fill_tall`
  - Older contract: tall BG staging plus dirty/projector ownership.
  - Build 0239 bypassed it for gameplay-classified BG strip output, but legacy scene-fill/transition compatibility still depended on the tall model.
- `vdp_project_bg_tall_if_dirty`
  - Older contract: project tall BG backing into visible 32-row staging/VDP commit path.
  - Build 0239 left the helper defined but removed the live VBlank call.
- `vdp_project_fg_tall_if_dirty`
  - Older contract: project tall FG backing into visible 32-row staging/VDP commit path.
  - Build 0239 left the helper defined but removed the live VBlank call.
- `vdp_commit_fg_narrow_strips`
  - Older contract: commit already-enqueued FG narrow descriptors.
  - It did not by itself prove full native resident-window ownership.
- `vdp_commit_bg_strips_if_dirty`
  - Older contract: commit legacy BG strip dirty rows.
  - It was retained alongside new BG narrow commits, creating mixed publication ownership.
- `genesistan_hook_itempage_strip_blit`
  - Older contract: item/stage strip blit through 32-row or tall BG helper depending on classification.
  - Build 0239 retargeted gameplay-classified sources to native BG narrow output.
- `genesistan_hook_tilemap_bg_fill` / `genesistan_hook_tilemap_fg_fill`
  - Older contract: legacy 32-row staging/dirty row path for non-gameplay/front-end producers.
- `genesistan_hook_cwindow_clear`
  - Older contract: clear staging/tall state and mark dirty for later projection/commit.
  - Build 0239 changed some bookkeeping but removed the projector publication path that made tall clears visible.

## Helpers Lacking a Proven Native Contract

The following inherited helpers or converted usages lacked a proven native contract sufficient to replace the tall/projector architecture:

- `genesistan_stage_fg_src_column` lacked proof that its converted resident-window output seeded all required Plane A rows at scene start and across selector variants.
- `genesistan_hook_itempage_strip_blit` / the BG strip path lacked proof that gameplay-classified Plane B output seeded all required Plane B rows and replaced the old BG tall projector across scene setup and movement.
- `vdp_commit_fg_narrow_strips` and new `vdp_commit_bg_narrow_strips` committed descriptor queues but did not establish ownership of full resident-window population.
- `genesistan_hook_cwindow_clear` lacked a proven native clear publication contract once the tall projectors were disabled.
- `vdp_commit_bg_strips_if_dirty` remained a legacy row-dirty committer and was not a coherent native replacement for the removed BG projector.
- `vdp_project_bg_tall_if_dirty` and `vdp_project_fg_tall_if_dirty` remained valid legacy helpers but were no longer live in VBlank, so any producer still relying on them became visually incomplete.

## Production Files Restored

The following production files were restored to the accepted Build 0235 state:

- `apps/rastan-direct/src/boot/boot.s`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

`apps/rastan-direct/Makefile` and `specs/` had no Build 0239 production-source diff and did not require restoration.

## Build 0235 Production Source Restore Proof

Post-restore production diff check:

```text
git diff --name-only -- apps/rastan-direct/src apps/rastan-direct/Makefile specs tools/translation/postpatch_startup_rom.py tools/translation/verify_canonical_rom.py
```

Result: no output. The preserved proof file is zero bytes:

`states/traces/build0239_rejection_baseline_restore_20260727_220828/post_restore_production_diff_names.txt`

Per-file SHA256 checks against `HEAD` after restoration:

```text
apps/rastan-direct/src/boot/boot.s                       c392cb96c2b817a18796b01ba11220b41d9f6d852a7c12369269ed5f17545f89
apps/rastan-direct/src/tilemap_hooks.s                   e7e4bf1f257951f6690a3a839fd4d7204d8d64329f7e985f150eb828378edd20
apps/rastan-direct/src/vdp_comm.s                        03410a8f75891f34e914632f416131b80bf17b42c7a2eb6e888ce1778845e4b6
tools/translation/postpatch_startup_rom.py               ab5a6b32da2dd1f2bfb709535114ef01d69bad5fc3ae66ddbdff45732d5ee6b3
tools/translation/verify_canonical_rom.py                4e1970b874aeab0270e6dbbe295879d6632fa812a907b12925ee4c5aa2f4b2dd
```

Each file's workspace SHA matched the corresponding `HEAD:<path>` SHA.

## Numbered Artifact Preservation Proof

```text
rastan_direct_video_test_build_0235.bin 1588440 bytes
rastan_direct_video_test_build_0236.bin 1588488 bytes
rastan_direct_video_test_build_0237.bin 1588440 bytes
rastan_direct_video_test_build_0238.bin 1588456 bytes
rastan_direct_video_test_build_0239.bin 1588624 bytes
```

Build 0239 remains preserved and rejected. Build 0235 remains the accepted production baseline. Counter remains `239`. No ROM was built.

## STOP Status

STOP triggered: NO. Build 0239 evidence was preserved, Build 0235 production source was unambiguous, and no numbered artifact was deleted or overwritten.
