# Cody - Build 0241 Native Selector-0 Plane A Column Tail Implementation

**Agent:** Cody  
**Date:** 2026-07-28  
**Task:** Implement native selector-0 Plane A column tail only.  
**Accepted baseline:** Build 0235, `dist/rastan-direct/rastan_direct_video_test_build_0235.bin`, SHA-256 `9aff0b11fb9a2151186ef0c03654fdd968d630a3cab45801be85de6f62571ad5`.  
**Rejected preserved prior:** Build 0240.  
**Candidate produced:** Build 0241, `dist/rastan-direct/rastan_direct_video_test_build_0241.bin`, SHA-256 `42fdc60d988c2bb2753ac0cf1b2033103c13a7e5402e0bb272ef3377aff74c47`, size `1588432`, counter `241`.  
**Acceptance result:** REJECTED / STOP. Build 0241 enters the exception handler before selector-0 publication and therefore does not validate the helper at runtime. Build 0241 is preserved and must not be deleted or overwritten.

---

## Phase 0 Baseline

**Architecture:** Confirmed. The arcade program remains authoritative. The new helper is an opcode-replacement target called from arcade flow and returns to the next arcade instruction. It does not claim Genesis-owned gameplay control.

**Relevant priors:**
- `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`: highest safe semantic cut, complete chip-tail replacement, no chip-shaped final architecture.
- `docs/design/Andy_plane_a_selector0_logical_coordinate_proof.md`: selector-0 logical coordinates are proven C08000-free for original arcade runtime, 0 mismatches over 205 publications.
- `docs/design/Andy_plane_a_semantic_cut_contract.md`: Build 0240 failed because helper code clobbered live caller registers; register preservation is mandatory for helpers called inside arcade loops.
- `docs/design/Cody_plane_a_selector0_chip_tail_retirement_audit.md`: selector-0 tail can be replaced only if the native helper avoids old PC080SN destination state and preserves arcade ring progression.

**Task classification:** EXTENDING native PC080SN Plane A migration.

**Open/Closed issues touched:** OPEN-001 / PC080SN gameplay rendering migration context. No issue closed.

**Contradiction of CONFIRMED/STRONG finding:** NONE. The runtime failure is before the selector-0 helper executes, so it does not contradict Andy's selector-0 coordinate proof.

---

## Build 0240 Preservation and Build 0235 Restore

Before implementation, Build 0240 rejection evidence was preserved under:

`states/traces/build0240_rejection_selector0_restore_20260728_141302/`

Preserved evidence includes:
- `source_snapshot_0240/`
- `build0235_to_build0240_production.diff`
- `build0235_to_build0240_production.diffstat`
- `post_restore_vs_build0235_diff_names.txt` (empty, verifying restored production paths matched Build 0235 before the new implementation)

The implementation proceeded from the restored Build 0235 production source plus the new selector-0 changes described below.

---

## Implementation

### Native Helper

Added `genesistan_hook_tilemap_plane_a_selector0_native` in `apps/rastan-direct/src/tilemap_hooks.s`.

Static source location:
- global declaration: `apps/rastan-direct/src/tilemap_hooks.s:4`
- selector-0 helper: `apps/rastan-direct/src/tilemap_hooks.s:117`

The helper:
- saves and restores `d0-d7/a0-a6`;
- computes selector-0 logical column from `a5+0x10CC` and `a5+0x10CA`;
- computes logical row as `segment * 4 + cell`;
- writes collision to Genesis-WRAM equivalent of arcade `0x10DE00`, using `0x1E00(a5,offset)`;
- checks resident Plane A row using `staged_scroll_y_fg` and the proven resident-window formula;
- writes final Genesis Plane A cells to `staged_fg_buffer` only when resident;
- marks `fg_row_dirty` for resident rows;
- returns to arcade flow.

Implemented formula:

```text
logical_column = ((a5+0x10CC) * 4 + (a5+0x10CA)) & 63
logical_row    = segment * 4 + cell
collision_addr = 0xFF1E00 + ((logical_row * 64 + logical_column) * 2)
native_y       = (-PlaneA_scroll_y + 8) & 0x01FF
logical_top    = (native_y >> 3) & 63
delta          = (logical_row - logical_top) & 63
resident       = delta < 32
physical_row   = logical_row & 31
physical_col   = logical_column & 63
```

### Opcode Replacement

Added required symbol and shift replacement in `specs/rastan_direct_remap.json`:

```json
{
  "arcade_pc": "0x055950",
  "original_bytes": "61000016",
  "replacement_bytes": "4eb9{symbol:genesistan_hook_tilemap_plane_a_selector0_native}",
  "note": "Build 0241: selector-0 Plane A producer cut. Replace the strip-A BSR with a native helper and return to 0x055954 so arcade ring-counter progression remains authoritative."
}
```

Static postpatch proof from `build/rastan-direct/address_map.json` and `build/genesis_postpatch.disasm.txt`:

```text
arcade_pc 0x055950 -> runtime_genesis_pc 0x055B50
runtime_genesis_pc 0x055B50: jsr 0x000704A4
runtime_genesis_pc 0x055B56: addq.w #1,0x10CA(a5)
```

Because the replacement is 6 bytes replacing a 4-byte `bsr`, the postpatch return address is `runtime_genesis_pc 0x055B56`, corresponding to the shifted continuation for `arcade_pc 0x055954`. The old selector-0 tail remains in ROM as historical code/data but is no longer called from the patched selector-0 dispatch site.

### Tooling Adjustments

`tools/translation/postpatch_startup_rom.py` was updated so validation of shifted original bytes can account for embedded word-aligned absolute-long references inside function-body expected bytes, including `JSR/JMP/LEA/MOVEA.L #imm,An` forms.

Canonical coverage constants were updated to the generated Build 0241 coverage value `0x183CD0` in:
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

This allowed the Build 0241 artifact to pass the release gates, but the later runtime failure means this candidate is not accepted.

---

## Static Verification

**Forbidden selector-0 final-helper dependencies:** no helper references were found to:
- `a5+0x10A0`
- `0x00C08000` / `C08000`
- `genesistan_stage_fg_src_column`
- `genesistan_stage_bg_collision_column`
- `fg_tall`
- `projector`
- direct `VDP_DATA` / `0x00C00000` writes

**VDP ownership:** the helper writes staging/dirty state only. It does not write VDP directly.

**Register discipline:** the helper saves/restores `d0-d7/a0-a6`, addressing the Build 0240 clobber class.

**Build gate:** Build 0241 reported `GATE_PASS` and produced the numbered artifact.

---

## Runtime Validation

Runtime evidence is preserved under:

`states/traces/build0241_selector0_native_runtime_20260728_143245/`

### Build 0235 Control

`build0235_selector0_summary.txt`:

```text
label=build0235
frames=5000
final_state=0002/0003/0000
left_224=true first=1
reached_230=true first=339
```

Build 0235 reaches gameplay state `2/3/0` under the same harness.

### Build 0241 Candidate

`build0241_selector0_summary.txt`:

```text
label=build0241
frames=5000
final_state=0000/0000/0000
left_224=true first=1
reached_230=false first=nil
selector0_publications=0
native_collision_writes=0
native_fg_stage_writes=0
legacy_sel0_collision_writes=0
```

Build 0241 does not reach gameplay. It records zero selector-0 publications, zero native collision writes, zero native FG staging writes, and zero legacy selector-0 collision writes. Therefore the native helper did not receive a runtime validation opportunity.

Minimal no-input sanity trace:

```text
frame,pc,state
1,0002EA,0000/0000/0000
60,0005C0,0000/0000/0000
120,0005C0,0000/0000/0000
240,0005C0,0000/0000/0000
500,0005C0,0000/0000/0000
1000,0005C0,0000/0000/0000
```

Early PC trace shows the candidate entering the exception handler path before normal state progression:

```text
33,070E58,2700,0000/0000/0000,...
34,000670,2704,0000/0000/0000,...
35,00066C,2704,0000/0000/0000,...
36,000A64,2708,0000/0000/0000,...
37,000B4C,2704,0000/0000/0000,...
38,0005C0,2700,0000/0000/0000,...
```

Exception probe shows `exflag=01`, `excode=03` by frame 34. This supports an early exception before selector-0 publication. The sampled PCs at `0x000670`, `0x000A64`, `0x000B4C`, and `0x0005C0/0x0005C2` are exception formatting/handler locations, not a proven root fault PC. The exact pre-exception faulting instruction remains unresolved.

---

## Verdict

Build 0241 is a preserved rejected implementation candidate.

What is proven:
- The selector-0 helper was implemented and statically routed at the intended arcade dispatch site.
- The helper avoids the forbidden PC080SN destination state and direct VDP writes.
- Build 0241 produces a numbered ROM and passes static release gates.
- Runtime validation fails before selector-0 publication.

What is not proven:
- The helper is not runtime-validated in gameplay.
- The precise root cause of the early Build 0241 exception is not proven.
- Build 0241 is not an accepted successor to Build 0235.

**STOP triggered:** YES, for acceptance. The candidate fails before the target code path can execute, and no bounded repair was proven within this task.

**Next boundary:** Either restore Build 0235 production source before a new attempt, or prove and repair the early Build 0241 exception before consuming Build 0242. Do not treat Build 0241 as accepted.

---

## Open / Closed Issues Impact

- Open issues touched: OPEN-001 / native PC080SN gameplay rendering migration context.
- New issues opened: none.
- Issues closed: none.
- Issues intentionally deferred: selector-1/2 Plane A rows, Plane B, rope/post-rope scene loading, PC090OJ, collision/player-state work.

## KNOWN_FINDINGS Impact

**Option A - No new finding to index.** The implementation candidate failed before runtime exercising the new selector-0 helper, so this does not establish a durable new gameplay/rendering finding.


---

## Build 0242 Recovery - Byte-Neutral Selector-0 Route

**Date:** 2026-07-28  
**Accepted production baseline restored before implementation:** Build 0235, `dist/rastan-direct/rastan_direct_video_test_build_0235.bin`, SHA-256 `9aff0b11fb9a2151186ef0c03654fdd968d630a3cab45801be85de6f62571ad5`.  
**Rejected preserved prior:** Build 0241, `dist/rastan-direct/rastan_direct_video_test_build_0241.bin`, SHA-256 `42fdc60d988c2bb2753ac0cf1b2033103c13a7e5402e0bb272ef3377aff74c47`.  
**Candidate produced:** Build 0242, `dist/rastan-direct/rastan_direct_video_test_build_0242.bin`, SHA-256 `823c3ab0021111265070063beb01083a0665decce894933ff1375915132932c2`, size `1588432`, counter `242`.  
**Acceptance result:** REJECTED / STOP. Build 0242 passes static build gates but fails the focused runtime acceptance gate before selector-0 publication.

### Recovery From Build 0241

Build 0241 source state was preserved under:

`states/traces/build0241_recovery_byte_neutral_selector0_20260728_162347/source_snapshot_0241/`

The production source was restored from the Build 0235 source checkpoint (`bad1499`) before applying the byte-neutral implementation. Restored production paths included:

- `apps/rastan-direct/src/boot/boot.s`
- `apps/rastan-direct/src/tilemap_hooks.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/Makefile`
- `specs/rastan_direct_remap.json`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

The Build 0241 broad shifted-expected-byte validation change was removed. `maybe_shift_abs_long_expected_bytes` is back to the narrow Build 0235 behavior: it only accepts a single 6-byte absolute-long `JSR`, `JMP`, or `LEA` operand adjustment. It does not scan larger opcode bodies and does not accept `MOVEA.L #imm,An` as a shifted-expected-byte convenience.

Production diff artifacts are preserved under:

- `states/traces/build0241_recovery_byte_neutral_selector0_20260728_162347/build0235_to_build0242_production.diff`
- `states/traces/build0241_recovery_byte_neutral_selector0_20260728_162347/build0235_to_build0242_production.diffstat`
- `states/traces/build0241_recovery_byte_neutral_selector0_20260728_162347/static_checks.txt`

### Byte-Neutral Route

The Build 0242 route follows the corrected byte-neutral plan:

- The original copied-program `BSR.W` at `arcade_pc 0x055950` is retained.
- No `shift_replacement` exists in `specs/rastan_direct_remap.json`.
- The opcode replacement is at `arcade_pc 0x055968`, not `arcade_pc 0x055950`.
- The `arcade_pc 0x055968` replacement is equal-length: original span `38` bytes, replacement span `38` bytes.
- The replacement starts with absolute `JMP genesistan_hook_tilemap_plane_a_selector0_native` (`4EF9`) and pads the rest of the original span with neutral words.
- The helper returns by `RTS`, so the original `BSR.W` call at `arcade_pc 0x055950` resumes at the original continuation `arcade_pc 0x055954`.

Address-map and ROM-byte proof:

```text
arcade_pc 0x055950 -> runtime_genesis_pc 0x055B50
runtime_genesis_pc 0x055B50: 61000016...

arcade_pc 0x055968 -> runtime_genesis_pc 0x055B68
runtime_genesis_pc 0x055B68: 4EF9000704A44E71...

helper symbol genesistan_hook_tilemap_plane_a_selector0_native -> runtime_genesis_pc 0x000704A4
runtime_genesis_pc 0x000704A4: 48E7FFFE9EFC00104BF900FF0000...
```

The existing selector-1/selector-2 route at `arcade_pc 0x055990` remains unchanged and still routes to the pre-existing shared Plane A path.

### Helper Contract

The helper contract is the same native selector-0 contract intended by Build 0241, but now reached through the byte-neutral route:

- Saves/restores `d0-d7/a0-a6` with one outer `movem` pair.
- Does not read `a5+0x10A0`.
- Does not use `0x00C08000` or any PC080SN-shaped destination address as final state.
- Uses semantic selector state at `a5+0x10CA` and `a5+0x10CC`.
- Processes 16 segments x 4 cells.
- Writes all 64 logical collision rows to the collision buffer.
- Writes final Plane A words only for resident rows into `staged_fg_buffer`.
- Marks `fg_row_dirty` for resident rows.
- Performs staging/dirty work only and does not write the VDP directly.

### Build Verification

Build 0242 produced successfully and reported `GATE_PASS`.

```text
ROM: dist/rastan-direct/rastan_direct_video_test_build_0242.bin
SHA-256: 823c3ab0021111265070063beb01083a0665decce894933ff1375915132932c2
size: 1588432
counter: 242
rolling artifact SHA matches numbered artifact: YES
opcode_replace count: 216
canonical coverage: 0x183CD0
```

The canonical coverage value changed from Build 0235's `0x183CD8` to `0x183CD0` even though the copied arcade program was not shifted by the selector-0 route. The opcode-replacement count remained `216`. The coverage constants were updated only after the pre-artifact gate reported the new same-length replacement coalescing result.

The automatic no-input MAME smoke trace generated by the release build is preserved at:

`states/traces/rastan_direct_video_test_build_0242_mame_30s_20260728_162933/`

Its summary reports 1798 frames and no unmapped `0xC50000` or live FG C-window summary hits.

### Focused Runtime Validation

Focused runtime validation is preserved under:

`states/traces/build0241_recovery_byte_neutral_selector0_20260728_162347/runtime_build0242/`

Summary:

```text
label=build0242
frames=5000
final_state=0002/0002/0004
left_224=true first=1
reached_230=false first=nil
min_10aa=0000 current_10aa=003D
selector0_publications=0
native_collision_writes=0
native_fg_stage_writes=0
legacy_sel0_collision_writes=0
candidate_unexpected_old_sel0=0
mismatch_col=0 mismatch_row=0 short_pubs=0
```

Frame samples show the candidate reaches state `2/2/4`, then remains in the exception-handler/display path with sampled PC `runtime_genesis_pc 0x0005C0` from frame 480 onward. `a5+0x10AA` remains at `0x003D`. The trace never observes selector-0 publication, native helper collision writes, native helper FG staging writes, or legacy selector-0 collision writes.

### Verdict

Build 0242 is preserved and rejected.

Proven:

- Build 0241 source and artifact evidence were preserved.
- Production source was restored to the Build 0235 state before the byte-neutral implementation.
- The Build 0241 `shift_replacement` route was removed.
- The Build 0241 broad expected-byte validation change was removed.
- The byte-neutral route is statically correct: `arcade_pc 0x055950` retains the original `BSR.W`, and `arcade_pc 0x055968` contains an equal-length `JMP` to the native helper.
- Build 0242 passed static release gates and produced the numbered ROM.

Not proven:

- The native selector-0 helper was not runtime-validated in gameplay.
- The exact faulting instruction that leads to the frame-480 `runtime_genesis_pc 0x0005C0` exception-handler samples is not proven.
- Build 0242 is not an accepted successor to Build 0235.

**STOP triggered:** YES. The runtime acceptance gate failed, and no bounded follow-up fix was proven in this task. Build 0242 is preserved as a rejected candidate; no Build 0243 was produced.

### Open / Closed Issues Impact

- Open issues touched: OPEN-001 (PC080SN gameplay rendering migration), OPEN-002 context only.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: selector-1/selector-2 migration, Plane B migration, PC090OJ, collision semantics beyond selector-0 staging, root cause of the Build 0242 exception-handler state.

### KNOWN_FINDINGS Impact

Option A - No new finding to index. This task produced a rejected implementation candidate and a routing/static verification result, but the helper did not execute at runtime and no durable new system-behavior fact was established.
