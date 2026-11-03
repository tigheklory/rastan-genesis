# Cody — PC080SN Readback Bypass

## 1. Executive Summary
Implemented a surgical bypass for three arcade PC080SN readback sites that attempt to read from `0xC08000–0xC0BFFF` on Genesis. These reads are invalid on Genesis and trigger failures (including the observed `C09E87` crash). The bypass replaces each read/branch sequence with a direct branch to the not-equal path and NOP fill.

## 2. Read Site Summary
Patched readback sites:
- `0x03A47E`
- `0x03A552`
- `0x03AC54` (crash site for `0xC09E87`)

All three are CMPI-driven control checks (CCR/branch flow only) and do not store readback values for downstream computation.

## 3. Patch Implementation
Added exactly 3 `opcode_replace` entries in `specs/rastan_direct_remap.json`:
- `0x03A47E` → replacement `60104e714e714e714e714e714e714e714e71`
- `0x03A552` → replacement `60104e714e714e714e714e714e714e714e71`
- `0x03AC54` → replacement `60124e714e714e714e714e714e714e714e71`

Updated `opcode_replace_count` from `31` to `34`.

## 4. Validation of Instruction Sizes
The patcher enforces equal original/replacement byte lengths. Each replacement is 18 bytes. Each corresponding `original_bytes` window was validated and set to the same 18-byte span at each site so replacement is size-preserving and patch application succeeds.

## 5. Why No Shadow Is Required
These patches bypass illegal readback control checks directly. No emulation path, no shadow buffer, and no new runtime abstraction are required for this step.

## 6. Verification Plan
- Build `rastan-direct` and confirm patcher applies all three entries.
- Confirm manifest contains all three opcode replacements at expected arcade PCs.
- Runtime verification in BlastEm: confirm no freeze at `C09E87` and progression past the prior crash region.

## 7. Final Result
Spec-level readback bypass is in place for the three identified illegal read sites, with count and manifest alignment confirmed after successful build.
