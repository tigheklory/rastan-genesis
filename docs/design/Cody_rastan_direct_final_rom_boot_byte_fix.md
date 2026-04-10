# Cody rastan-direct final ROM boot-byte fix

## 1. Executive Summary
The final `rastan-direct` ROM corruption at `0x00038A` was fixed by correcting the patcher ordering for the `rastan_direct` profile and adding a mandatory postpatch guard on the final artifact. The final ROM now preserves `67 28` at `0x00038A`, and the build fails hard on the known bad `04 3A` signature.

## 2. Root Cause Reference
Reference: `docs/design/Andy_early_control_flow_loop_diagnosis.md`.

Andy established that `0x00038A` must be `67 28` and that `04 3A` causes the early exception loop.

## 3. Exact Reintroduction Point of Bad Bytes
Bad bytes were reintroduced during `tools/translation/postpatch_startup_rom.py` in the `rastan_direct` flow because:
- preserved boot/vector bytes (`0x000000..0x0003FF`) were restored too early
- later rewrite passes (specifically `rom_absolute_call_relocation`) still mutated bytes in the overlapped boot region
- this changed `0x00038A` from `67 28` to `04 3A` in the final patched ROM.

Single exact reintroduction point: **postpatch rewrite passes running after early vector restore in `postpatch_startup_rom.py` for `rastan_direct`**.

## 4. Exact Fix Implemented
Implemented one fix strategy:
- In `postpatch_startup_rom.py`, for `rastan_direct` profile only, defer restoration of preserved bytes `0x000000..0x0003FF` until after rewrite passes and immediately before checksum/write.

Behavior now:
- non-`rastan_direct` profiles keep prior timing
- `rastan_direct` restores preserved boot bytes last, so rewrite passes cannot re-corrupt them.

Additionally:
- Makefile now runs boot-byte verifier on final ROM after patching.

## 5. Exact Files Modified
- `tools/translation/postpatch_startup_rom.py`
- `apps/rastan-direct/Makefile`
- `docs/design/Cody_rastan_direct_final_rom_boot_byte_fix.md`
- `AGENTS_LOG.md`

## 6. Final-ROM Postpatch Guard Design
Guard tool: `tools/translation/verify_rastan_direct_boot_guard.py`

Automatic checks now in normal build path:
1. prepatch guard: verifies fresh prepatch bin has `0x00038A = 67 28`
2. postpatch guard: verifies final ROM has `0x00038A = 67 28`

Hard failures:
- explicit fail on `0x00038A = 04 3A`
- fail on any non-`67 28` mismatch.

## 7. Verification Performed
1. Clean build:
- `source tools/setup_env.sh && make -C apps/rastan-direct clean && make -C apps/rastan-direct`
- prepatch guard PASS
- postpatch guard PASS
- final ROM produced.

2. Byte verification (exact values):
- `xxd -g1 -l 16 -s 0x38A apps/rastan-direct/out/rastan_direct_video_test.prepatch.bin`
  - `0000038a: 67 28 61 00 ff cc ...`
- `xxd -g1 -l 16 -s 0x38A apps/rastan-direct/dist/rastan_direct_video_test.bin`
  - `0000038a: 67 28 61 00 ff cc ...`

3. Repeat build without manual clean:
- `source tools/setup_env.sh && make -C apps/rastan-direct`
- target up-to-date, no rebuild errors
- final ROM bytes remain `67 28` at `0x38A`.

4. Known bad-byte rejection test:
- forced synthetic `04 3A` at `0x38A` in a temp ROM
- verifier exits non-zero with explicit stale-signature failure.

## 8. Backward Compatibility Impact
- Existing patcher lineage preserved (`postpatch_startup_rom.py` remains authoritative).
- No patcher replacement or alternate patch flow added.
- Non-`rastan_direct` behavior remains unchanged for vector-restore timing.

## 9. Risks / Known Limitations
- Guard currently asserts a fixed invariant at `0x00038A` for this bring-up stage. If intentional boot-code changes alter that location, guard expectation must be updated with that intentional change.

## 10. Final Verdict
The final-ROM corruption path is fixed. `apps/rastan-direct/dist/rastan_direct_video_test.bin` now preserves correct boot bytes at `0x00038A`, and build-time postpatch guarding prevents recurrence of the `04 3A` bad-byte case.

## 11. Permanent vs Temporary Classification
- PERMANENT:
  - deferred preserved-byte restore for `rastan_direct` in `postpatch_startup_rom.py`
  - postpatch final-ROM guard call in `apps/rastan-direct/Makefile`
- TEMPORARY: none
- DIAGNOSTIC: none
- BRINGUP_ONLY: none

## 12. Scaffolding Inventory
- No new temporary scaffolding added.

## 13. Removal / Revert Plan
- No revert planned. This is a permanent build correctness safeguard.
