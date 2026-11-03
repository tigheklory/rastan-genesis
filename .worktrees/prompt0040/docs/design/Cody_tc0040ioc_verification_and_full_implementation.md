# Cody TC0040IOC Verification and Full Implementation

## Summary
Completed verification-first and implementation for TC0040IOC coverage in `rastan-direct`.
Verification confirmed DIP defaults, WRAM-based flip derivation model, and safe suppression of unsupported `0x380000` hardware writes on Genesis.
Implementation expanded spec-driven opcode replacements to full TC0040IOC coverage used by current disassembly and updated input shadow behavior to match active-low mapping requirements.

## Exact Files Modified
- `specs/rastan_direct_remap.json`
- `apps/rastan-direct/src/main_68k.s`
- `docs/design/Cody_tc0040ioc_verification_and_full_implementation.md`
- `AGENTS_LOG.md`

## Exact Symbols / Functions / Labels Added or Changed
- `rastan_direct_update_inputs` (`apps/rastan-direct/src/main_68k.s`)
  - Coin shadow behavior changed to be driven only by A-button state.
  - System shadow byte forced to `0xFF` each frame.
- `opcode_replace` entries extended in `specs/rastan_direct_remap.json`:
  - DIP constants: `0x03AF7A`, `0x03AF86`
  - Additional TC0040IOC/system read coverage: `0x03A7B8`, `0x03AB96`, `0x03A91A`, `0x03AC94`, `0x03ACFE`
  - Additional TC0040IOC/coin read coverage: `0x03ACB2`, `0x03ACBC`, `0x03AD1C`, `0x03AD26`
  - Unsupported `0x380000` write suppression: `0x03A1D8`, `0x03AE34`, `0x03AE9C`, `0x03AF1E`, `0x03EF28`, `0x03EF48`, `0x03EF8A`, `0x03EFAA`, `0x045306`
  - Existing shadow input redirects retained for: `0x03A4A2`, `0x03A4A8`, `0x03A778`, `0x03A77E`, `0x03A0A8`, `0x03A0B2`, `0x03A0C0`, `0x03A490`, `0x03AC04`
- `expectations.opcode_replace_count` updated from `10` to `30`.

## Permanent vs Temporary Classification
- `specs/rastan_direct_remap.json` TC0040IOC patch coverage expansion: `PERMANENT`
- `main_68k.s` input-shadow mapping adjustments for active-low/coin/system behavior: `PERMANENT`
- No temporary, diagnostic, or bring-up-only scaffolding added in this task.

## Scaffolding Inventory
- None added.

## Removal / Revert Plan
- No planned removal. This change set is required runtime mapping for Genesis-hosted direct execution.
- If rollback is needed, revert the added `opcode_replace` entries and restore prior `rastan_direct_update_inputs` coin/system logic.

## Build Artifact Path
- Canonical latest ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Numbered artifact produced by build: `dist/rastan-direct/rastan_direct_video_test_build_0003.bin`

## Verification Status
Verification phase (completed before implementation):
- DIP constants validated from project evidence and disassembly path requirements:
  - DIP1 default constant: `0xFE`
  - DIP2 default constant: `0xFF`
- Flip derivation model validated as WRAM-driven and not dependent on `0x380000` readback path.
- `0x380000` write suppression safety validated for Genesis target architecture.
- Address verification against disassembly completed; required TC0040IOC reads/writes patched at instruction boundaries.

Implementation verification:
- Full `make -C apps/rastan-direct clean && make -C apps/rastan-direct` succeeded.
- Patch manifest confirms `opcode_replace` applied count = `30` (matches expectation).
- Newly added DIP/system/`0x380000` entries all applied with resolved ROM patch sites.
- Boot guard passed for both prepatch and final ROM artifacts.

## Risks / Known Limitations
- Addresses `0x03A4AC` and `0x03A3A6` are not instruction-boundary TC0040IOC read opcodes in current disassembly; patching uses verified instruction-boundary sites instead.
- Runtime behavioral validation for startup progression, gameplay input feel, and loop stability remains emulator/hardware test dependent.
