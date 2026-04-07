# Summary
Applied the linker memory-map correction so `.bss` is linked into Genesis WRAM VMA space at `0xFF0000`.

# Exact File Modified
- `apps/rastan-direct/link.ld`

# Exact Linker-Script Change Made
- Changed:
  - `.bss (NOLOAD) :`
- To:
  - `.bss 0xFF0000 (NOLOAD) :`

# Classification
- PERMANENT

# Why the Old `.bss` Placement Broke Runtime State
With `.bss` resolving in ROM-space VMA, runtime writes to state variables (dirty flags, frame/tick counters, staging buffers) did not persist as writable RAM state. As a result, commit-path state gating and staging behavior could not function correctly.

# Why Mapping `.bss` to `0xFF0000` Fixes Dirty Flags and Staging Buffers
Mapping `.bss` VMA to Genesis WRAM places those variables in writable memory. Dirty flags and staging buffers now persist and update across frames, enabling intended runtime state transitions and commit gating.

# Scaffolding Inventory
- No new scaffolding added.

# Removal / Revert Plan
- No revert expected; this is required for correct runtime behavior.

# Build Artifact Path
- `apps/rastan-direct/dist/rastan_direct_video_test.bin`

# Verification Status
- Build produced: YES
- `.bss` symbols resolve to WRAM (`0xFF0000+`): YES
- Display output changed: USER MUST VERIFY
- CRAM debugger no longer empty: USER MUST VERIFY

# Risks / Known Limitations
- On-screen and CRAM debugger verification are user-side emulator checks and were not asserted in this headless build step.
