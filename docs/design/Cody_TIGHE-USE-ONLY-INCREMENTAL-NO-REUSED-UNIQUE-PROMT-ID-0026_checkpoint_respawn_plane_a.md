# PROMPT-ID-0026 — Plane A checkpoint-respawn correction (Build 0517)

## Result and semantic boundary

Build 0517 is a runnable candidate. It corrects the lifecycle hole that left the native Plane A
ring empty after a retained death/checkpoint restore. The semantic cut remains:

`retained checkpoint/record/camera decision -> offline final-native record map -> active package -> camera-derived 64x32 Genesis ring -> staged VDP publication`

The retired tail is PC080SN C-window/name RAM, chip-address translation, and full-map projection.
There is no C-window shadow, runtime descriptor walk, runtime pixel conversion, checkpoint-specific
image, rope special case, guessed camera coordinate, fallback renderer, NOP, or RTS bypass.

## Confirmed cause and retained call sequence

The reported “segment 4” checkpoint is arcade progression record `$000B` (11), selector 0—not raw
record 4. Durable natural-play evidence records FG X/Y near `$0137/$0189` and player X/Y
`$009E/$003F`; these values are evidence only and do not occur in the correction.

The retained lifecycle is:

1. Death/transition teardown at arcade `$056440` legitimately clears native staged planes and scroll.
2. The normal restore at `$055F26` writes the saved checkpoint record to `A5+$013E`; the alternate
   path at `$056014` writes the decremented saved record.
3. Each restored write is preserved, then a proper shift replacement calls
   `genesistan_plane_a_checkpoint_restore_arm`, which sets one byte
   `fg_checkpoint_scroll_reseed_pending`.
4. Retained code rebuilds gameplay state and installs the authoritative camera tuple at `$0504FA`.
5. The existing post-camera replacement at `$050538` calls
   `genesistan_plane_a_scene_scroll_reseed_native` while presentation is held.
6. The helper consumes the checkpoint pending byte once, selects the live `A5+$013E` record and
   `fg_boundary_active_package`, derives visible top from live `A5+$10B0`, stages exactly 32 rows x
   64 final Genesis name words, marks all Plane A rows dirty, and leaves Plane B ownership alone.
7. The established VBlank path publishes the dirty ring before display release.

Build 0515 returned at step 5 because only `fg_scene_scroll_reseed_pending` was recognized. Its
six-record scene-fill artifact had entries only for 0, 16, 22, 23, 39, and 45. Record 11 was
therefore not a legal source for that entry-only path even though retained collision and rope state
were correct. Later incremental row/column publication gradually hid the empty-initial-ring symptom.

Scene entry and checkpoint ownership remain disjoint: scene pending wins and clears checkpoint
pending; scene entry owns A+B, while checkpoint reseed owns A only. Ordinary scrolling arms neither.

## Generalized all-record data and package selection

`compile_pc080sn_genesis.py` produces complete final-native maps for all 46 records plus four required
overlap-package alternatives (50 maps total). A verbatim artifact was 410,152 bytes and pushed the
ROM beyond the Genesis 4 MiB window. It is retained as build-time verification input but is not linked.
The linked `record_native_row_maps.bin` deduplicates complete 128-byte final-native rows offline:

- 50 maps x 64 16-bit row IDs;
- 1,638 unique final-native rows;
- 216,616 total bytes, SHA-256 `96ea1dbb3f9358163eacf1107aa4f6017d17e49288829ba97caa99a689b60116`.

Runtime work is still bounded row selection plus direct final-word copies. It performs no source-code,
attribute, palette, descriptor, or PC080SN interpretation.

For record `$000B`, stable package 3 and overlap runtime package 10 are distinct. The generated table
selects package 10 when `fg_boundary_active_package==10`; it does not blindly select the stable map.
The rope source at logical column 46 is Plane A, source attribute `$0005`, with source codes
`$025B`, `$025E`, then `$0260-$0263` repeated. Under package 10 those codes resolve to slots
`$0429,$0473,$046A,$0474,$0470,$046D`, producing final name words
`$6429,$6473,$646A,$6474,$6470,$646D`. The live `$0189` evidence yields logical top row 15 via the
same `((-Y+8)&$1ff)>>3` rule; physical placement is always `logical_row&31`.

## Files corrected

- `apps/rastan-direct/src/tilemap_hooks.s`: checkpoint arm helper, all-record/package selection,
  live-camera row projection, compact row lookup, Plane-A-only ownership.
- `apps/rastan-direct/src/fg_tile_cache.s`: one-byte checkpoint reseed pending state.
- `specs/rastan_direct_remap.json`: size-changing replacements at `$055F26/$056014`, preserving the
  displaced restore instruction before calling the native arm helper.
- `tools/translation/compile_pc080sn_genesis.py`: all-record final-native maps and offline row-deduped
  runtime representation.
- `tools/translation/verify_plane_a_scene_fill_maps.py`: independent 46-record/package expansion,
  compressed/uncompressed equality, every cell, and every nine-bit Y-origin projection.
- `apps/rastan-direct/Makefile`: generated-asset dependencies and exact canonical/full-HUD coverage
  deltas (`$40000`/`$38000`).
- `tools/mame/scripts/final_life_zero_input_regression.lua`: durable staged-ring appearance captures
  from legitimate zero-input death/respawn lifecycles (begun in PROMPT-ID-0024 and retained here).

No palette-decision ID changed. `Test.json` remains source identity
`86505de8a7566e0a13a083bf6b3715fa61eb9242102091aadb589d7583cde9fb`; reconstructed World Rev 1
`maincpu.bin` is `4f30b9e7aa946aa33d20e125a1726ff094f9615980107d0842efe1721cf32063`.

## Verification

Static/exhaustive gate:

- 204,800 checkpoint cells checked across all 46 records and all package alternatives;
- all 204,800 compressed cells equal the independent full-map oracle;
- 23,552 checkpoint record/Y-origin projections cover all 512 nine-bit Y origins per record;
- 24,576 scene-entry Plane A cells and 3,072 scene-entry origin projections pass;
- 12,288 Plane B cells and 16,384 selector-1/2 pan cells pass;
- collision remains outside the visual helper.

Build and bounded Genesis NTSC runtime:

- canonical gate: PASS; boot guard: PASS; gameplay-entry gate: PASS;
- Phase-1 package/epoch gate: PASS for records 0, 3, 4, 5, 11, and 13;
- record 11 selects runtime package 10, 608 required patterns, full Plane A LUT PASS, full fixed Plane B
  LUT PASS, no exception, valid SP;
- mandatory 30-second MAME trace completed at
  `states/traces/rastan_direct_video_test_build_0517_mame_30s_20261028_203316`;
- legitimate zero-input final-life route PASS at 3,587 frames with three deaths, two visible respawns,
  zero unsafe visible frames and zero unsafe display-on writes;
- the two captured rebuilt record-1 rings are byte-identical, SHA-256
  `3e1da614a44c2759001505305d5b354e3a403fa22febacd694c590224f4403c8`;
- each observed checkpoint presentation moves from HOLD/READY at frame 1197/2009 to display ON at
  frame 1198/2010, so the one-time 4 KiB staging plus normal publication completes inside the held
  presentation interval;
- no per-frame path was added: the pending byte is consumed once; ordinary row/column publishers and
  VBlank data volume are unchanged.

The record-11 package fixture is bounded and uses the production package installer; it does not fake
a checkpoint by writing expected map/camera/player state. It proves package/LUT residency, not the
complete natural record-11 death lifecycle.

### Evidence boundary

Automated Build 0517 evidence does **not** include a natural gameplay traversal to the record-11
checkpoint or a terminal actual-VRAM dump at that checkpoint. Therefore staged-versus-VDP equality,
immediate rope visibility, surrounding scenery, subsequent bidirectional scroll, and rope interaction
at that exact checkpoint remain Tighe's gameplay acceptance tests. The same boundary applies to later
R1-S2 chain interaction; the generated S1-2 ROM preserves the established selector-1 implementation
but this task did not automate a long castle ascent. These tests are not reported as PASS.

## Candidate artifacts

- Canonical Build 0517:
  `dist/rastan-direct/rastan_direct_video_test_build_0517.bin`
  - SHA-256 `4848935bd926bcbcb1a4d6a8a277ccec9d88582148702e3a1c5938922607d57e`
  - 3,727,032 bytes
- R1-S2 start derivative (same parent number; no counter consumption):
  `dist/rastan-direct/rastan_direct_video_test_build_0517_S1-2.bin`
  - SHA-256 `3ae2e9df649410cd98ed9c2059c0eb287485b9093c5b0f4b0e314fe4c9f99d11`
  - 3,727,032 bytes
- The complete canonical `_d`, `_s`, `_do`, `_c`, `_full_hud`, and `_invincible` family passes the
  Makefile variant-set verifier.

Build 0516 was consumed during the rejected >4 MiB verbatim-map attempt and failed canonical/epoch
gates; it is deliberately not a candidate. Counter and consumed ledger end at 517. Build 0517 is an
automated-gate-passing candidate only. Acceptance belongs to Tighe.
