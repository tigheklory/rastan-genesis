# Cody Build 0254 Attract Mode Legacy Reachability Audit

## Baseline

- Accepted baseline: Build 0253
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0253.bin`
- Expected SHA-256: `3015974ec444e3be2d49f182a191dfb5a536dfb89b07d3e9ec84c9767f1e6155`
- Verified SHA-256: `3015974ec444e3be2d49f182a191dfb5a536dfb89b07d3e9ec84c9767f1e6155`
- Counter: `253`
- Build 0253 user verification: PASS for frontend/title/story/high-score, Rastan, lizard men, bats, and axe item.
- Known preexisting issue: BlastEm fatal write to `HW_ADDRESS 0x00D00298` when the attract gameplay demo starts.
- Build 0254 produced: NO
- Production source changed: NO

## Phase 0

Read in full before task-specific work:

- `RULES.md`
- `ARCHITECTURE.md`
- `PROMPT_TEMPLATE.md`
- `KNOWN_FINDINGS.md`
- `OPEN_ISSUES.md`
- `CLOSED_ISSUES.md`
- latest relevant `AGENTS_LOG.md` entries

Classification: EXTENDING, focused on OPEN-024/PC090OJ reachability and OPEN-001/PC080SN attract/frontend reachability, with OPEN-017 context for emulator/hardware behavior and OPEN-015 crash-data caution.

Contradiction of CONFIRMED or STRONG finding detected: NONE.

Architecture compliance: CONFIRMED. This was an audit-only pass. No production code, specs, Makefile, ROM, or counter state were changed. Arcade code remains the program; Genesis code remains helper/opcode replacement only.

## Files And Evidence Inspected

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/out/symbol.txt`
- `build/rastan-direct/address_map.json`
- `dist/rastan-direct/rastan_direct_video_test_build_0253.bin`
- `states/traces/build0254_attract_reachability_audit/`
- Prior D00298 evidence in `AGENTS_LOG.md` and existing design notes.

Trace artifact directory:

`states/traces/build0254_attract_reachability_audit/`

Trace files:

- `attract_reachability.lua`
- `events.tsv`
- `timeline.csv`
- `mame_stdout.log`
- `mame_stderr.log`
- `mame_exit_code.txt`
- `summary.txt` (empty; see trace limitation below)

## Runtime Trace Summary

Command used:

```bash
TRACE_DIR=states/traces/build0254_attract_reachability_audit MAX_FRAMES=9000 timeout 240s mame genesis -cart dist/rastan-direct/rastan_direct_video_test_build_0253.bin -video none -sound none -nothrottle -skip_gameinfo -autoboot_script states/traces/build0254_attract_reachability_audit/attract_reachability.lua
```

Result:

- MAME exit code: `0`
- External frame samples: `1..9000`
- MAME completed the bounded no-input attract run.
- The trace reached gameplay state `state0/state2/state4 = 0x0002/0x0003/0x0000` with `genesistan_current_scene_id = 1` by external frame `2700`.
- The trace stayed in gameplay scene/state through frame `9000`.
- `RAW_D00298_WRITE`: `0`
- raw `HW_ADDRESS 0x00D00000..0x00D007FF` PC090OJ writes: `0`
- `pc090oj_object_ram` writes: `90`, all observed at frame `2`, `runtime_genesis_pc 0x00000342`, zero-initialization range only.
- broad `0x00C00000..0x00C0FFFF` writes: `15`, all frame-0 VDP control-port initialization writes at `runtime_genesis_pc 0x0007008E`, `HW_ADDRESS 0x00C00004`.

Trace limitation:

- The MAME Lua memory read taps used for execution-PC observation did not fire for the inspected helper PCs in this run. Therefore runtime helper execution counters are not used as proof.
- The empty `summary.txt` is a trace finalization limitation, not evidence absence. The event and timeline files contain the useful bounded evidence.
- The `RAW_PC080SN_WRITE` label in the trace script is too broad for Genesis because `0x00C00004` is the YM7101/VDP control port. The observed frame-0 entries are VDP register writes, not PC080SN C-window tilemap writes.

Interpretation:

- MAME Genesis did not reproduce the BlastEm `D000298` fatal in this bounded no-input attract/demo run.
- This does not disprove the BlastEm crash. The static copied-code hazard remains present, and prior user evidence reported the BlastEm strict-target fatal at demo start.
- The runtime non-repro should be interpreted narrowly: MAME did not take the raw-D00298 path in this captured window.

## Attract Split Classification

### 1. Frontend / Title / Throne / Story / High-Score / Insert-Coin

PC090OJ classification: legacy frontend compatibility path still reachable and required.

Evidence:

- `genesistan_pc090oj_hook_target_41dae` checks `genesistan_current_scene_id`; when it is not gameplay scene `1`, it calls `pc090oj_workram_block_sprites` and returns.
- `genesistan_pc090oj_hook_target_41f5e` checks `genesistan_current_scene_id`; when it is not gameplay scene `1`, it calls `pc090oj_workram_block_sprites_41f5e` and returns.
- `genesistan_pc090oj_hook_target_45dfa` checks `genesistan_current_scene_id`; when it is not gameplay scene `1`, it calls `pc090oj_workram_block_sprites` and returns.
- `pc090oj_native_emit_pass` branches to `pc090oj_legacy_emit_pass` when `genesistan_current_scene_id != 1`.
- `vdp_prepare_sprites` calls `pc090oj_native_emit_pass` when no staged SAT frame is ready; for non-gameplay this reaches the legacy emit pass.
- `pc090oj_object_ram` is still a persistent slot-addressed arcade object store retained for compatibility; legacy frontend/non-gameplay output still depends on it.

Frontend PC090OJ path classification:

- `pc090oj_legacy_emit_pass`: reachable for non-gameplay/frontend.
- `pc090oj_native_emit_pass`: reachable as the common entry, but branches to legacy when scene is not gameplay.
- `pc090oj_object_ram`: still used by frontend/non-gameplay compatibility producers and legacy scan.
- `record_to_slot`, `represented_records`, `waiting_records`, `pc090oj_candidate_bitset`: retained exported legacy stubs/data; no inspected source path uses them for current frontend rendering.
- Frontend/title/throne sprite producers: still routed through the compatibility object-store/legacy-emitter path, not through the Build 0250 all-gameplay semantic lanes.

PC080SN classification: frontend compatibility/staging paths remain required.

Evidence:

- `_vblank_service` skips the legacy tall projectors only for gameplay scene `1`; for non-gameplay it still calls the exported `vdp_project_bg_tall_if_dirty` and `vdp_project_fg_tall_if_dirty` labels.
- After Build 0253 those projector labels are no-op stubs, while strip commit paths remain active.
- Frontend visible screens still depend on existing C-window/text/tilemap hooks and VBlank strip commits.
- `tilemap_hooks.s` retains C-window/text hooks including `genesistan_hook_cwindow_clear`, `genesistan_hook_text_writer_*`, `genesistan_hook_pc080sn_bg_scroll_fill`, `genesistan_hook_pc080sn_fg_scroll_fill`, and descriptor rebuild support.

Frontend PC080SN path classification:

- Native gameplay Plane A/B producers: not the frontend title/story/high-score ownership path.
- Old PC080SN compatibility/text/C-window staging: still reachable and required for visible frontend screens.
- Strip commit: still active.
- Legacy tall projector bodies: removed in Build 0253; exported stubs remain for non-gameplay call sites.
- Dead/unreached transitional PC080SN code: not removed in this task because frontend reachability has not been fully converted to native Plane A/B semantics.

### 2. Gameplay Demo Transition / Start

Runtime observation in MAME:

- No-input MAME run entered `state0/state2/state4 = 0x0002/0x0003/0x0000`, `genesistan_current_scene_id = 1`, at frame `2700`.
- No `HW_ADDRESS 0x00D00298` write was observed in MAME through frame `9000`.
- No raw `HW_ADDRESS 0x00D00000..0x00D007FF` write was observed in MAME through frame `9000`.

Static observation:

- The copied raw PC090OJ writer that targets `HW_ADDRESS 0x00D00298` remains present in Build 0253.
- Prior manual BlastEm evidence reports a strict-target fatal write to `D000298` at attract gameplay demo start.

Gameplay demo-start classification:

- Proven statically: a raw copied arcade PC090OJ routine can write `HW_ADDRESS 0x00D00298`.
- Proven dynamically in this pass: MAME did not execute the raw write in the bounded captured no-input run.
- Not proven dynamically in this pass: the exact scene/state at the BlastEm write moment.
- Best current classification: preexisting BlastEm strict-target exposure of a copied raw PC090OJ hardware routine during demo/start or downstream reset/bootstrap flow; dynamic route remains unresolved in this Build 0254 audit.

### 3. Gameplay Demo Once Scene 1 Begins

PC090OJ classification:

- In gameplay scene `1`, the Build 0250/0251 native semantic-lane path is the intended renderer.
- `pc090oj_native_emit_pass` takes `.Lnq_gameplay` and consumes native queues rather than branching to `pc090oj_legacy_emit_pass`.
- `genesistan_pc090oj_hook_target_41f5e` begins the native sprite frame and stages PLAYER_BODY.
- `genesistan_pc090oj_hook_target_41dae` and `genesistan_pc090oj_hook_target_45dfa` stage gameplay semantic lanes and finalize them through `pc090oj_native_emit_pass`.
- The old gameplay PC090OJ scanner/decoder path was not re-enabled or modified.

PC080SN classification:

- In gameplay scene `1`, `_vblank_service` skips the legacy tall-projector call pair.
- Plane B uses native producer/strip-commit ownership.
- Plane A uses native producer/narrow-strip ownership.
- `vdp_commit_bg_strips_if_dirty` and `vdp_commit_fg_narrow_strips` still run.
- The removed Build 0253 projector bodies are not needed for gameplay scene `1`.

## D000298 / D00298 Write Provenance

Address-space labels:

- `HW_ADDRESS 0x00D00298`: arcade PC090OJ object RAM address, illegal as a Genesis direct hardware write.
- `runtime_genesis_pc 0x0005A71E`: copied code instruction that loads the raw hardware address.
- `runtime_genesis_pc 0x0005A724`: first dangerous write through that pointer.
- `arcade_pc 0x0005A51E`: JSON-mapped arcade counterpart for `runtime_genesis_pc 0x0005A71E`.
- `arcade_pc 0x0005A524`: JSON-mapped arcade counterpart for `runtime_genesis_pc 0x0005A724`.
- `runtime_genesis_pc 0x0005124E`: only direct static caller found, `jsr 0x0005A702`.
- `arcade_pc 0x0005104E`: JSON-mapped arcade counterpart for `runtime_genesis_pc 0x0005124E`.

Address-map proof:

- `runtime_genesis_pc 0x0005124E` maps via `build/rastan-direct/address_map.json` segment `193`, kind `arcade_copy`, to `arcade_pc 0x0005104E`.
- `runtime_genesis_pc 0x0005A702`, `0x0005A71E`, `0x0005A724`, and `0x0005A754` map via `build/rastan-direct/address_map.json` segment `404`, kind `arcade_copy`, to `arcade_pc 0x0005A502`, `0x0005A51E`, `0x0005A524`, and `0x0005A554` respectively.
- No `+0x200` arithmetic is used as authority; mappings above are JSON-derived.

Static instruction decode around `runtime_genesis_pc 0x0005A702`:

```asm
runtime_genesis_pc 0x0005A702 / arcade_pc 0x0005A502: clr.l   d0
runtime_genesis_pc 0x0005A704 / arcade_pc 0x0005A504: move.w  0x0010C200,d0
runtime_genesis_pc 0x0005A70A / arcade_pc 0x0005A50A: btst    #5,d0
runtime_genesis_pc 0x0005A70E / arcade_pc 0x0005A50E: beq     0x0005A716
runtime_genesis_pc 0x0005A710 / arcade_pc 0x0005A510: move.w  #0x0180,d1
runtime_genesis_pc 0x0005A716 / arcade_pc 0x0005A516: move.w  #0x0070,d1
runtime_genesis_pc 0x0005A71C / arcade_pc 0x0005A51C: move.w  #0x0060,d0
runtime_genesis_pc 0x0005A71E / arcade_pc 0x0005A51E: movea.l #0x00D00298,a0
runtime_genesis_pc 0x0005A724 / arcade_pc 0x0005A524: move.w  #0x0000,(a0)+
runtime_genesis_pc 0x0005A728 / arcade_pc 0x0005A528: move.w  d1,(a0)+
runtime_genesis_pc 0x0005A72A / arcade_pc 0x0005A52A: move.w  #0x0037,(a0)+
runtime_genesis_pc 0x0005A72E / arcade_pc 0x0005A52E: move.w  d0,(a0)+
runtime_genesis_pc 0x0005A730 / arcade_pc 0x0005A530: addi.w  #0x0010,d0
```

The first write at `runtime_genesis_pc 0x0005A724` writes to `HW_ADDRESS 0x00D00298`. This is record offset `0x298` in the PC090OJ object-RAM address space, equivalent to raw PC090OJ record index `83` if interpreted as 8-byte records.

Static caller:

```asm
runtime_genesis_pc 0x0005124E / arcade_pc 0x0005104E: jsr 0x0005A702
```

Classification:

- D00298 is a raw arcade PC090OJ object-RAM write.
- It is not a mapped `pc090oj_object_ram` write; that table is located at `Genesis-WRAM 0x00FFAF9A` in this build.
- It is not native SAT output.
- It is not a tile-art, palette, CRAM, or PC080SN issue.
- It is not proven in this pass to be normal gameplay after scene `1` begins; MAME reached scene `1` without hitting it.

Why it writes D00298:

- Copied arcade code loads the raw hardware address literal `0x00D00298` into `%a0`, then performs a sequence of `(a0)+` word stores to build/update PC090OJ records.
- On arcade hardware this targets PC090OJ object RAM.
- On Genesis/BlastEm strict-target, `0x00D00298` is not a valid Genesis VDP/SAT destination and triggers the reported fatal.

Preexisting status:

- YES, preexisting. The same copied D00298-family routine and caller were documented in earlier Build 0120 evidence. Build 0253 did not introduce this literal or route.

## Precise Divergence And Fix Gate

First proven divergence:

- The production ROM still contains copied arcade PC090OJ code that directly targets raw `HW_ADDRESS 0x00D00298` instead of going through the native gameplay semantic lanes or a frontend-safe compatibility route.

What is not yet proven:

- The exact dynamic control path that reaches `runtime_genesis_pc 0x0005124E -> 0x0005A702 -> 0x0005A724` during the BlastEm attract demo-start crash.
- The exact scene/state at the write moment in BlastEm.
- Whether the route is demo-only, frontend-to-gameplay transition-specific, or a reset/bootstrap fallout path.
- Whether MAME misses it because the bounded no-input path differs, because MAME permits/ignores the write differently, or because the BlastEm run reaches a slightly different state/timing.

Fix made:

- NO.

Reason no Build 0254 was produced:

- The raw writer is isolated statically, but the dynamic route that triggers it during the BlastEm demo-start crash was not reproduced in MAME and is not yet pinned to a safe replacement boundary.
- Replacing or bypassing the routine without dynamic route proof risks changing frontend compatibility or demo/start behavior outside the authorized isolated fix.
- The correct next step is a narrower BlastEm-side stop/provenance capture at `runtime_genesis_pc 0x0005A71E` or `0x0005A724`, not a speculative patch.

## Required Classifications

Attract frontend PC090OJ path classification:

- Legacy compatibility path is still reachable and required.
- Frontend routes through `pc090oj_workram_block_sprites*`, `pc090oj_object_ram`, and `pc090oj_legacy_emit_pass` via `pc090oj_native_emit_pass` non-gameplay fallback.
- Native all-gameplay lanes are not the frontend/title/throne ownership path.

Attract frontend PC080SN path classification:

- Frontend remains on compatibility/text/C-window/staging plus strip-commit paths.
- Native gameplay Plane A/B producers are not the frontend ownership path.
- Build 0253 projector bodies are removed, but exported no-op stubs remain and frontend strip commits/text hooks remain live.

Gameplay demo-start path classification:

- MAME enters gameplay scene `1` without hitting D00298 in the bounded run.
- Static copied raw PC090OJ D00298 path remains present.
- BlastEm demo-start fatal remains a preexisting strict-target crash with unresolved dynamic route.

Gameplay demo scene-1 classification if reachable:

- PC090OJ: native semantic lanes/finalizer.
- PC080SN: native Plane A/B producers plus strip commits.
- Legacy projector bodies: not present/reachable.
- Old gameplay PC090OJ scanner/decoder path: not re-enabled.

## Open / Closed Issues Impact

Open issues touched:

- `OPEN-001` context: PC080SN attract/frontend versus gameplay rendering ownership.
- `OPEN-017` context: emulator/hardware behavior and existing deferred D00298 attract-demo issue.
- `OPEN-024`: PC090OJ sprite subsystem / legacy-vs-native reachability.
- `OPEN-015` context only: crash-screen/on-screen numeric data remains unreliable; this audit uses static ROM/address-map and trace-side evidence, not on-screen exception fields.

New issues opened: NONE.

Issues closed: NONE.

Issues intentionally deferred:

- BlastEm-side exact D00298 dynamic route capture.
- Frontend PC090OJ native replacement.
- Frontend PC080SN native replacement.
- Any deletion of frontend compatibility paths.
- Normal gameplay sprite lifecycle, Build 0251 PLAYER_BODY fix, Build 0253 projector removal, collision, rope/reset, input, palette/CRAM, audio, and broad cleanup.

## KNOWN_FINDINGS Impact

Option A: no new finding to index.

This report refines existing PC090OJ/native-replacement and raw-PC090OJ-write evidence, but does not establish a new durable mechanism beyond the already known D00298 raw copied-code hazard and the already known transitional frontend compatibility boundary.

## STOP Status

STOP triggered: YES, audit-only/no-build stop.

Reason:

- Required report was created.
- Build 0253 was preserved.
- No production source was changed.
- No Build 0254 ROM was produced.
- The D00298 raw writer is statically proven, but the BlastEm dynamic route is not pinned tightly enough for a safe implementation.
