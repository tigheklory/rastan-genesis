# Cody rastan-direct stale bin pipeline fix

## 1. Executive Summary
The `rastan-direct` build pipeline was corrected so the patcher no longer consumes an ambiguous in-place ROM artifact. A fresh prepatch binary is now always generated from the current ELF (`objcopy` output), verified by a hard boot-byte guard at `0x00038A`, then copied to the final ROM path for patching. A hard automatic failsafe now stops the build if the known bad stale signature (`0x043A`) appears before patching.

## 2. Root Cause Reference (Andy report)
Reference: `docs/design/Andy_early_control_flow_loop_diagnosis.md`.

Andy identified a stale-binary loop in which preserved boot/vector bytes could come from a previously patched `.bin`, reintroducing bad boot code at `0x00038A`.

## 3. Existing Broken Artifact Flow
Previous flow in `apps/rastan-direct/Makefile`:
1. `objcopy` wrote directly to `dist/rastan_direct_video_test.bin`
2. patcher read and rewrote that same file in-place

That combined prepatch input and postpatch output into one artifact path. It was not explicit/auditable which bytes were the fresh ELF-derived source versus the patched result.

## 4. Exact Fix Implemented
A dedicated prepatch artifact was introduced:
- Fresh prepatch binary: `apps/rastan-direct/out/rastan_direct_video_test.prepatch.bin`
- Final patched ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`

Updated flow:
1. Link ELF
2. `objcopy` ELF -> prepatch bin (`out/*.prepatch.bin`)
3. Run hard boot guard verifier on prepatch bin
4. Copy prepatch bin -> final dist ROM path
5. Run existing patcher on final ROM path

This guarantees patcher input is freshly regenerated from current ELF whenever the target rebuilds.

## 5. Exact Files Modified
- `apps/rastan-direct/Makefile`
- `tools/translation/verify_rastan_direct_boot_guard.py` (new)

No runtime/gameplay source files were modified.

## 6. Failsafe Design
Failsafe entrypoint:
- `tools/translation/verify_rastan_direct_boot_guard.py`

Checks performed before patching:
- reads prepatch ROM bytes
- validates byte pair at `0x00038A` equals `67 28` (`BEQ.S`)
- explicitly rejects known bad stale signature `04 3A` (`ADDI.B`)
- fails build with a hard non-zero exit on mismatch

Makefile integration:
- `$(BIN)` target invokes verifier on `$(PREPATCH_BIN)` before invoking `postpatch_startup_rom.py`.

## 7. Verification Performed
1. Clean build verification:
- ran `source tools/setup_env.sh && make -C apps/rastan-direct clean && make -C apps/rastan-direct`
- result: PASS
- verifier output: `rastan-direct boot guard PASS: 0x00038A=6728 (BEQ.S)`
- final ROM produced.

2. Repeat build without manual clean:
- ran `source tools/setup_env.sh && make -C apps/rastan-direct`
- result: PASS (`Nothing to be done for 'all'`).

3. Known stale-byte case rejection:
- created a synthetic bad prepatch binary by forcing bytes at `0x00038A` to `04 3A`
- ran verifier on that file
- result: FAIL with explicit stale-signature error and exit code 1.

## 8. Backward Compatibility Impact
- Existing patcher lineage is preserved (`tools/translation/postpatch_startup_rom.py` remains authoritative).
- `rastan-direct` patch profile and spec flow remain unchanged.
- No startup-title branch patcher replacement or flow fork was introduced.

## 9. Risks / Known Limitations
- The hard failsafe currently checks a fixed boot offset (`0x00038A`) and expected bytes (`0x6728`). If boot layout changes intentionally in future, the guard must be updated accordingly.
- This task addresses artifact freshness and prepatch validation only; it does not change runtime logic.

## 10. Final Verdict
The build pipeline now has explicit prepatch/postpatch artifact ownership, stale `.bin` reuse in the patch input path is eliminated, and an automatic hard failsafe prevents the known bad boot-byte case from silently passing into patching.

## 11. Permanent vs Temporary Classification
- PERMANENT:
  - `apps/rastan-direct/Makefile` prepatch artifact flow (`PREPATCH_BIN`) and guarded patch step.
  - `tools/translation/verify_rastan_direct_boot_guard.py` hard boot-byte verifier.
- TEMPORARY: none
- DIAGNOSTIC: none
- BRINGUP_ONLY: none

## 12. Scaffolding Inventory
- No temporary scaffolding was added.

## 13. Removal / Revert Plan
- No removal planned. This is a permanent build-safety correction.
- If architecture intentionally changes boot bytes at `0x00038A`, update the verifier expected bytes in `verify_rastan_direct_boot_guard.py` as part of that intentional change.

## 14. Build Artifact Path
- `apps/rastan-direct/dist/rastan_direct_video_test.bin`

## 15. Verification Status
- clean build: PASS
- repeat build without clean: PASS
- stale signature hard-fail test: PASS
