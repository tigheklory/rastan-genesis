# Player Movement Regression Diagnostic Checkpoint After Build 0278

## Stop State

- This is a documentation-only checkpoint requested after Build 0278.
- Build 0279 is **not authorized** and was not prepared, built, or numbered.
- No production, specification, translation-tool, generated-data, ROM, or counter change was made for this checkpoint.
- Current production counter: `278` (`build/rastan-direct/build_counter.txt`).
- The current working tree is intentionally preserved in place.
- The accepted comparison baseline remains Build 0273.
- Builds 0274 through 0278 are consumed diagnostic artifacts. They are not accepted fixes for the movement/ground regression.

## Artifact Ledger

| Build | Role | SHA-256 | Size | Result |
|---|---|---|---:|---|
| 0273 | Accepted comparison baseline | `a9c8a609774e48c38c3e5c740a3e04f7b74675a896dc0a36d2529846ea5363b8` | 1,591,836 | Player lands and enters stable ground state. |
| 0274 | Native PLAYER_BODY/FRONT migration | `4ead3b77da5bba008e5a0f18459135d856121f673c6fc772ead7b104876231e1` | 1,590,924 | Rejected: player falls through/does not establish ground state. |
| 0275 | Register-contract diagnostic correction | `2579d3f3ef9e1c3bd85be7f4bc7061aa2c2877dd047fa18b78de653dc8a93766` | 1,590,924 | Introduced register clobbers corrected; landing still fails. |
| 0276 | Shifted immediate/reference diagnostic correction | `61b53c980b0ee4fbc9d58200b1bcfc20fc260c2875f311cf3f5bfbba218d230b` | 1,590,924 | Additional relocation defects corrected; landing still fails. |
| 0277 | Replacement-entry target relocation correction | `4e4000318dfc86ea58eed243c5bb3901102025a6bcdc38b8083230719ff10149` | 1,590,924 | Branch-to-replacement-start defect corrected and gated; landing still fails. |
| 0278 | BODY mode-7 D2-result correction | `69665cbeff89d470f0c096333c5fd53b5054a20df7ba59e0394f7dd2a393287d` | 1,590,924 | Mode-7 `D2=0` contract restored; landing still fails. |

All six numbered ROMs exist under `dist/rastan-direct/`. No numbered artifact was deleted or overwritten during this investigation.

## Required Architecture Boundary

The Build 0274 objective remains valid even though its runtime result is rejected:

- Retained semantic cut: original arcade PLAYER_BODY and PLAYER_FRONT state/mapping decisions.
- Intended native realization: final Genesis PLAYER_BODY/PLAYER_FRONT queue entries consumed by the one native SAT finalizer.
- Retired chip tail: player tuple output at `a5+0x11B2` / `a5+0x0170`, tuple scanning/decoding, and tuple-to-SAT projection.
- Forbidden recovery: restoring the retired tuple path, adding a second player renderer, forcing player state, or bypassing collision/ground logic.

No diagnostic build restored the retired tuple path.

## Build-by-Build Proof

### Build 0274: Regression Introduction Boundary

Build 0274 moved PLAYER_BODY and PLAYER_FRONT production to native main-loop staging. It:

- reset native player lanes at the retained main-loop semantic boundary around `arcade_pc 0x05105A`;
- retained FRONT state/mapping decisions rooted at `arcade_pc 0x059F92`;
- retained BODY state/mapping decisions rooted at `arcade_pc 0x0540CC`;
- replaced the corresponding PC090OJ tuple stores with native queue realization;
- removed the VBlank tuple consumer `native_stage_player_blocks_41f5e`;
- preserved the existing native VBlank finalizer as the sole SAT/VDP owner;
- replaced tuple-zero anchor transport with direct semantic maintenance of `a5+0x129A` and `a5+0x129C`.

**PROVEN:** Build 0274 is the first artifact in this sequence that fails to establish the accepted landing/ground trajectory.

**PROVEN:** `a5+0x129A` and `a5+0x129C` are auxiliary sprite anchors. Their known readers position auxiliary sprite pieces; no identified reader feeds ground contact, slope classification, collision addressing, camera movement, or player physics.

**PROVEN:** The original tuple-zero blank value clears these anchors, so direct native clear/publish preserves their established semantic values.

### Build 0275: Producer Register Contract

The inline native realization used `D1`, `D3`, `D4`, and `D6` as rendering temporaries. The original producer boundaries did not expose all of those clobbers to their callers.

Build 0275 added introduced-only preservation:

- FRONT preserves `D1/D3/D4/D6`.
- BODY preserves `D3/D4/D6` at normal and inactive exits.

**PROVEN:** Build 0274 violated retained caller register contracts.

**PROVEN:** Correcting those violations did not restore landing. Therefore those clobbers were real defects but were not the complete cause of the movement/ground regression.

The draft report `docs/design/Cody_build0275_player_ground_movement_regression_fix.md` records the then-current register hypothesis. Its claim of a complete root cause is superseded by Builds 0275-0278 and this checkpoint.

### Build 0276: Shifted Absolute/Immediate References

Build 0276 extended shift-table handling for relocated long references embedded in copied instructions and replacement guards, including recognized `MOVE.L #imm32,d16(An)` and `CMPI.L #imm32,d16(An)` forms. It also made long-reference guard adjustment explicit for original versus already-relocated operands.

**PROVEN:** The Build 0274 reflow exposed relocation coverage defects that required correction.

**PROVEN:** The corrected relocation handling passed its build/canonical checks but did not restore landing. Those relocation defects were not the complete movement root cause.

### Build 0277: Reference to a Replacement Start

The generic shift computation previously included a replacement's own delta when a branch/reference targeted the first byte of that replacement. At `arcade_pc 0x051DF8`, the branch targets semantic entry `arcade_pc 0x051E00`, which is also the start of a shrinking replacement. The incorrect zero displacement could decode as `BRA.W` and consume the following opcode as an extension word.

Build 0277:

- introduced a target mapping based on shifts strictly before the target;
- repaired branch, absolute-long, pointer-table, and jump-table target relocation at replacement starts;
- added a canonical invariant for the `0x051DF8 -> 0x051E00` player auxiliary-entry branch.

**PROVEN:** The replacement-start relocation was mechanically wrong before Build 0277.

**PROVEN:** Correcting it did not restore landing. It was not the complete movement root cause.

### Build 0278: BODY Mode-7 Result Contract

The original BODY mode-7 clear tail leaves `D2=0`. The native retired-tail replacement initially returned with a stale/nonzero `D2` value.

Build 0278 explicitly restored the original `D2=0` result while preserving native player output and keeping the tuple path retired.

**PROVEN:** The earlier native mode-7 path violated the retained result contract.

**PROVEN:** Build 0278 now reaches the relevant state with `D2=0`, but the player still does not land. The mode-7 D2 defect was not the complete movement root cause.

## Current Runtime Comparison

### Accepted Build 0273

The deterministic comparison shows:

- the player begins the intro fall at the expected mode-3/Y trajectory;
- `a5+0x10B0` changes from `0x0000` to `0x01FF` around external frame 394;
- it then progresses by approximately `-3` per update (`0x01FF`, `0x01FC`, and onward to approximately `0x0149` by frame 476);
- the collision sample address advances through the staged collision field rather than remaining at one zero cell;
- at approximately frame 477, collision code `0x0001` is observed at the relevant sample and the player reaches mode `0`, Y `0x0070`, with `a5+0x10CE=0x0004`.

### Diagnostic Build 0278

The same comparison shows:

- the initial intro-fall state starts consistently with the accepted build;
- `a5+0x10B0` remains `0x0000` across the corresponding transition window;
- the sampled collision source remains at `Genesis-WRAM 0xFF268C` with value `0x0000` instead of advancing through the staged collision field;
- the player reaches/passes Y `0x0070` but does not establish the accepted ground state;
- mode remains/re-enters `3`, `a5+0x10CE` remains `0`, and the fall continues.

### Meaning of `a5+0x10B0`

**PROVEN:** Native collision code uses `a5+0x10B0` as a foreground/playfield vertical origin in its collision address calculation. It is not merely a visual VDP scroll value.

**PROVEN:** The immediate first collision divergence is therefore upstream of the ground-code classifier: Build 0278 samples the wrong collision cell because the origin used to address collision data did not progress as it did in Build 0273.

**PROVEN:** The ground classifier is capable of producing the accepted result when supplied the accepted collision code; the observed failure is not evidence that code `0x0001` itself is misclassified.

**PROVEN:** Runtime mappings from the current `address_map.json` place the relevant vertical update families at:

- `arcade_pc 0x055704 -> runtime_genesis_pc 0x0558BA` (patched site);
- `arcade_pc 0x055790 -> runtime_genesis_pc 0x055946` (patched site);
- nearby retained continuations include `runtime_genesis_pc 0x0558C2`, `0x0558CE`, `0x05594E`, and `0x05595A`.

The accepted `0x01FF` then `-3` sequence is consistent with the original vertical-origin update semantics, but the exact missing control edge has not yet been identified.

## Scheduling and Runtime-Cost Evidence

**PROVEN:** Build 0278 spends a much larger share of sampled external frames inside native actor expansion and native SAT finalization than Build 0273.

Representative current runtime locations include:

- `runtime_genesis_pc 0x072A5E`: `native_stage_dispatch_45dfa`;
- `runtime_genesis_pc 0x072AD8`: common actor expansion;
- `runtime_genesis_pc 0x0731F4`: gameplay native SAT finalizer entry;
- addresses around `runtime_genesis_pc 0x072C6A`: immediately after the common actor routine's balanced return, also observable as prefetched PC state.

**PROVEN:** Sampled Build 0278 PCs cluster heavily in actor expansion/finalization, while Build 0273 samples intermix those helpers with broader retained gameplay execution.

**PROVEN:** `pc090oj_sat_frame_ready` is observed becoming ready only roughly once per eight external frames in the affected Build 0278 window. This is consistent with an overlong or infrequently completed sprite frame, not with one completed native SAT frame per external video frame.

**PROVEN:** The sampled native PLAYER_BODY count is approximately 12 in both accepted Build 0273 and diagnostic Build 0278 during the intro. A simple increase in final player entry count has not been demonstrated.

**PROVEN:** Stack samples, including `-nodrc` runs, remain in expected nested bands. No monotonic stack leak was found. The sampled `0x072C6A` state does not by itself prove execution of inline data or a bad return.

**PROVEN:** The current actor expansion performs bounded scans of the retained actor families and the finalizer performs lane visibility/residency/SAT work. These paths are computationally substantial.

## Proven Negative Results

- Restoring introduced-only FRONT/BODY registers does not restore landing.
- Correcting shifted long/immediate references does not restore landing.
- Correcting references that target replacement starts does not restore landing.
- Restoring the original BODY mode-7 `D2=0` result does not restore landing.
- The direct `a5+0x129A/0x129C` anchor maintenance is not connected by known xrefs to collision or physics.
- No stack leak has been observed.
- No evidence supports patching the ground classifier, forcing mode 0, seeding `a5+0x10B0`, or restoring the retired tuple path.

## Hypotheses, Not Yet Proven

The following are working hypotheses only:

1. **Main-loop/VBlank scheduling starvation.** The native sprite work may keep the CPU in actor expansion/finalization long enough that the retained vertical-origin producer does not run at the accepted cadence.
2. **Lifecycle ordering or duplicate finalization.** The interaction among main-loop player-lane reset/staging, `native_sprite_frame_begin`, Genesis `vdp_prepare_sprites`, arcade VBlank hooks, and `pc090oj_native_emit_pass` may cause extra or badly ordered native work.
3. **Higher producer-call frequency.** One or more native BODY/FRONT producer helpers may execute more frequently than intended even though the final BODY count is not larger.
4. **A remaining reflow/control-flow defect.** A branch or call not covered by the corrections through Build 0278 may prevent the `0x10B0` update path from being reached.
5. **Runtime cost rather than logical reachability.** The correct `0x10B0` path may remain reachable but complete too infrequently relative to external frames.

None of these hypotheses is sufficient to authorize a production change.

## Exact Unresolved Root-Cause Boundary

The first established state divergence is:

> Build 0273 advances `a5+0x10B0` through the intro transition and consequently samples advancing collision cells; Build 0278 leaves `a5+0x10B0=0`, so collision sampling remains on zero data and the player never receives the accepted landing classification.

The unresolved boundary is one level earlier:

> It is not yet proven whether Build 0278 fails to reach the retained `0x10B0` producer, reaches it with a different branch/gate/state, or reaches it too infrequently because native sprite preparation/finalization occupies multiple external frames.

The next valid diagnostic, if separately authorized, is a focused accepted-versus-candidate event-order/count trace at the main-loop player reset/staging entries, native frame begin, actor dispatch, finalizer entry/exit, and the two mapped `0x10B0` update families. It must identify the first differing control event before any Build 0279 implementation is considered.

## Reusable Evidence

Primary comparison directory:

`states/traces/build0274_player_ground_movement_compare_20260810/`

Most relevant artifacts:

- `genesis0273_collision_origin.csv`
- `genesis0273_collision_origin_events.log`
- `genesis0278_collision_origin.csv`
- `genesis0278_collision_origin_events.log`
- `genesis0273_contact.csv`
- `genesis0273_contact_events.log`
- `genesis0276_contact.csv`
- `genesis0276_contact_events.log`
- `genesis0277_contact.csv`
- `genesis0277_contact_events.log`
- `genesis0278_contact.csv`
- `genesis0278_contact_events.log`
- `genesis0273_regs.csv`
- `genesis0273_regs_events.log`
- `genesis0277_regs.csv`
- `genesis0277_regs_events.log`
- `genesis0273_sprite_counts.csv`
- `genesis0273_sprite_counts_events.log`
- `genesis0278_sprite_counts.csv`
- `genesis0278_sprite_counts_events.log`
- `genesis0278_sprite_dma.csv`
- `genesis0278_sprite_dma_events.log`
- `genesis0273_stack_origin.csv`
- `genesis0273_stack_origin_events.log`
- `genesis0278_stack_origin.csv`
- `genesis0278_stack_origin_events.log`
- `genesis0273_nodrc_stack_origin.csv`
- `genesis0273_nodrc_stack_origin_events.log`
- `genesis0278_nodrc_stack_origin.csv`
- `genesis0278_nodrc_stack_origin_events.log`
- full/timeline captures for arcade, Build 0273, Build 0274, and Build 0275 in the same directory.

Reusable harness:

`states/traces/build0200_jump_fall_pending_move/jump_compare.lua`

The harness currently includes the expanded state/register/stack/origin sampling used by this investigation. Both the harness and trace directory are ignored by `.gitignore` through the repository-wide `states/` rule; their absence from `git status` does not mean they are absent from the workspace.

Supporting documents:

- `docs/design/Cody_build0274_native_player_body_front_retirement.md`
- `docs/design/Cody_build0275_player_ground_movement_regression_fix.md` (superseded diagnostic draft)
- `docs/design/Andy_workram_block_sprites_family_provenance.md`
- `docs/design/Andy_build0273_arcade_hud_pc090oj_tail_retirement.md`

## Current Modified-File Inventory

This is the complete `git status --short` inventory immediately before this checkpoint was created. It records workspace state, not ownership; several entries predate this diagnostic sequence or are unrelated work and must not be reverted implicitly.

Tracked modifications:

- `AGENTS.md`
- `AGENTS_LOG.md`
- `CLAUDE.md`
- `KNOWN_FINDINGS.md`
- `RULES.md`
- `apps/rastan-direct/out/palette_hooks.o`
- `apps/rastan-direct/out/pc090oj_config.inc`
- `apps/rastan-direct/out/pc090oj_hooks.o`
- `apps/rastan-direct/out/rastan_direct_video_test.elf`
- `apps/rastan-direct/out/symbol.txt`
- `apps/rastan-direct/out/vdp_comm.o`
- `apps/rastan-direct/src/pc090oj_hooks.s`
- `build/genesis_postpatch.disasm.txt`
- `build/mame/home/genesistrace/genesis_exec_trace.log`
- `build/rastan-direct/address_map.json`
- `build/rastan-direct/build_counter.txt`
- `build/rastan-direct/rastan_direct_patch_manifest.json`
- `build/rastan-direct/startup_common_relocations.json`
- `build/rom_inventory.json`
- `docs/design/Andy_arcade_hud_pc090oj_tail_retirement_handoff.md`
- `error.log`
- `specs/rastan_direct_remap.json`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/shift_table_patcher.py`
- `tools/translation/verify_canonical_rom.py`

Untracked files present before this checkpoint:

- `debugcmd_tmp.cmd`
- `docs/design/Andy_build0273_arcade_hud_pc090oj_tail_retirement.md`
- `docs/design/Andy_workram_block_sprites_family_provenance.md`
- `docs/design/Cody_build0274_native_player_body_front_retirement.md`
- `docs/design/Cody_build0275_player_ground_movement_regression_fix.md`

Ignored but task-relevant workspace files:

- `states/traces/build0200_jump_fall_pending_move/jump_compare.lua`
- `states/traces/build0274_player_ground_movement_compare_20260810/` and all captures listed above.

This checkpoint adds only:

- `docs/design/Cody_player_movement_regression_diagnostic_checkpoint_after_build0278.md`

## Checkpoint Conclusion

- The visible movement/ground regression remains unresolved after Build 0278.
- The collision-origin divergence at `a5+0x10B0` is proven and is the current narrow investigation boundary.
- Several independent contract and relocation defects found in Builds 0274-0278 were real, but none alone restored landing.
- Scheduling/native sprite runtime cost is a strong working hypothesis, not a proven root cause.
- No fix is authorized from this evidence alone.
- Build 0279 is not authorized.
- Counter remains `278`.
