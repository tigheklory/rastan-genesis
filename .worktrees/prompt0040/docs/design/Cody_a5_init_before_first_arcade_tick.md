# Cody — A5 Init Before First Arcade Tick

## 1. Executive Summary
A single initialization line was added in `init_staging_state` to establish `A5 = 0xFF0000` before the first arcade tick executes. This restores the required arcade invariant for A5-relative work RAM access in the current wrapper flow.

## 2. Root Cause Reference
Root cause reference: `docs/design/Andy_arcade_state_producer_nonprogression_diagnosis.md`.

## 3. Why the Existing `0x03AF04` Patch Was Not Sufficient
The existing spec patch at arcade PC `0x03AF04` is correct but located in arcade init code. The current Genesis wrapper calls the per-frame arcade tick entry directly and bypasses that init path, so the patched instruction is not executed before runtime logic starts.

## 4. New A5 Initialization Behavior
Added one line in wrapper initialization:
- `lea 0x00FF0000, %a5`

This runs once during `init_staging_state`, before the main loop and before the first `jsr rastan_direct_arcade_tick_entry`.

## 5. Exact File / Location Modified
- File: `apps/rastan-direct/src/main_68k.s`
- Function: `init_staging_state`
- Placement: first instruction in function body, before frame/tick init writes

## 6. Verification Performed
1. Confirmed line presence in `init_staging_state`.
2. Ran full build: `make -C apps/rastan-direct`.
3. Confirmed build success and ROM artifact production.
4. Confirmed existing `0x03AF04` remap patch remains present in spec and generated patch manifest.

## 7. Backward Compatibility Impact
No changes to patcher behavior, remap semantics, hook semantics, VBlank flow, or input mapping were made in this fix. The change is limited to wrapper-side one-time register initialization.

## 8. Risks / Known Limitations
This fix establishes a valid A5 base before first tick, but visible output progression still depends on broader runtime state progression and producer paths outside this single-line scope.

## 9. Final Verdict
The wrapper now establishes `A5 = 0xFF0000` before first arcade tick while preserving the existing `0x03AF04` patch, addressing the specific non-progression root cause identified in the diagnosis.
