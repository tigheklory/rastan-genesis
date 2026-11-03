# Cody Coin Pulse and Start Bit Fix

## Executive Summary
Implemented a surgical runtime input correction in `rastan_direct_update_inputs`.
Genesis A remains coin, but now generates a one-frame active-low pulse on system bit 5 only on a new press.
Genesis Start remains start, and now drives the correct active-low system start bit (bit 3 for P1, bit 4 for P2 while held).
No automatic coin insertion was added.

## Root Cause Reference
- `docs/design/Andy_rastan_credit_start_flow_diagnosis.md`
- `docs/design/Cody_tc0040ioc_verification_and_full_implementation.md`

## Old Incorrect Coin/Start Behavior
- `genesistan_shadow_input_390007` was forced to `0xFF` every frame.
- Coin edge detector path on bit 5 never received `1->0` transitions from user input.
- Start signaling from Genesis Start was being pushed into joystick shadow bit 7, which is not the identified system start bit path.

## Exact New Coin Pulse Behavior
- Coin remains mapped to Genesis A (P1 A button).
- New per-frame edge logic tracks previous P1 A state.
- On a new press (`prev=0`, `current=1`), system byte bit 5 is driven low for exactly one frame.
- On held A (`prev=1`, `current=1`), no repeated low on bit 5 is emitted.
- On release (`prev=1`, `current=0`), state resets to allow the next new-press pulse.

## Exact New Start Bit Behavior
- Start remains mapped to Genesis Start.
- While P1 Start is held, system byte bit 3 (`genesistan_shadow_input_390007`) is driven active-low.
- While P2 Start is held, system byte bit 4 is driven active-low.
- Start no longer modifies joystick shadow bit 7 in this routine.

## Exact Files Modified
- `apps/rastan-direct/src/main_68k.s`
- `docs/design/Cody_coin_pulse_and_start_bit_fix.md`
- `AGENTS_LOG.md`

## State-Tracking Mechanism Used
- Added one persistent byte in `.bss`:
  - `prev_coin_p1_a_pressed`
- Semantics:
  - `0` = not pressed previous frame
  - `1` = pressed previous frame
- Updated each frame in `rastan_direct_update_inputs` after pulse decision.

## Permanent vs Temporary Classification
- `prev_coin_p1_a_pressed`: `PERMANENT`
- Coin pulse/start bit routing logic in `rastan_direct_update_inputs`: `PERMANENT`

## Scaffolding Inventory
- No temporary, diagnostic, or bring-up-only scaffolding added.

## Removal / Revert Plan
- No planned removal. This is required runtime input behavior.
- Revert method if needed: restore previous `rastan_direct_update_inputs` block and remove `prev_coin_p1_a_pressed` from `.bss`.

## Verification Performed
- Built ROM successfully:
  - `make -C apps/rastan-direct`
- Verified code-path behavior in assembly logic:
  - A not pressed => no coin pulse on bit 5.
  - New A press => exactly one-frame bit 5 low pulse.
  - A held => no repeated bit 5 low.
  - P1 Start held => bit 3 low.
  - P2 Start held => bit 4 low.
  - Unrelated system bits default high unless explicitly driven.

## Build Artifact Path
- Canonical latest ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Numbered artifact generated in this build: `dist/rastan-direct/rastan_direct_video_test_build_0005.bin`

## Backward Compatibility Impact
- Preserves user-facing mapping:
  - A = coin
  - Start = start
- No spec/patcher/DIP/linker/VDP/runtime-render pipeline changes.

## Risks / Known Limitations
- Runtime gameplay progression, credit increment cadence, and full attract-to-game transition still require emulator verification.

## Final Verdict
Coin input now follows edge-triggered pulse behavior required by arcade credit logic while preserving manual A-button coin mapping.
Start now drives the correct active-low system start bits.
This is a scoped runtime input fix with no unrelated system redesign.
