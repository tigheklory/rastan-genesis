# Build 332 Arcade VBlank Joystick Cache Refresh Fix

## 1. Executive Summary
Build 332 adds a single input-refresh call in the active arcade VBlank path so SGDK joystick cache data is refreshed before shadow input packing. This targets the stale-overlay condition (`I:FFF7`, `K:------S-`) without re-enabling full SGDK VBlank processing.

## 2. Exact Active VBlank Site Modified
File: `apps/rastan/src/boot/sega.s`

Function/path: `_VINT_arcade_mode`

Change:
- Added `jsr JOY_update` immediately before `jsr genesistan_refresh_arcade_inputs`.

## 3. Why `JOY_update()` Was Needed
`genesistan_refresh_arcade_inputs()` reads controller state through `JOY_readJoypad()`, which returns SGDK cached joystick state. In the current active arcade VBlank ownership path, the normal SGDK VBlank dispatcher is bypassed, so cache refresh is not guaranteed unless explicitly invoked. Calling `JOY_update()` at `_VINT_arcade_mode` ensures fresh pad state is available each frame before shadow bytes are rebuilt.

## 4. What Was Intentionally Left Unchanged
- Palette logic unchanged.
- Tilemap/bulk tilemap logic unchanged.
- Sprite logic unchanged.
- Scroll logic unchanged.
- Mode/state/input overlay rendering unchanged.
- Launcher-side ownership behavior unchanged.

## 5. Why This Does Not Re-Enable Full SGDK VBlank Processing
The change invokes only `JOY_update()` directly. It does not call `SYS_doVBlankProcess()` and does not restore SGDK task dispatch, DMA flush path, palette fade path, callback chain, or audio chain.

## 6. Build Verification
- Build command: `source tools/setup_env.sh && make -C apps/rastan release`
- Result: success
- Release artifact: `dist/Rastan_332.bin`
- Warnings: no new warnings (same 5 pre-existing warnings)
- Errors: none

## 7. Expected Runtime Result
- `I:XXXX` should now reflect live input changes.
- `K:UDLR12SC` should now reflect live button presses.
- Existing mode/state overlay should remain intact.

## 8. Final Verdict
Build 332 applies the narrow joystick-cache refresh fix in the active arcade VBlank path and leaves broader SGDK VBlank ownership disabled.
