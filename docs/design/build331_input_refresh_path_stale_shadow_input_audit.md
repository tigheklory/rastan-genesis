# Build 331 Input Refresh Path / Stale Shadow Input Audit

## 1. Executive Summary
The Plane A debug overlay is reading the expected shadow input bytes (`0x390001` and `0x390007` mirrors), and the arcade VBlank path does call `genesistan_refresh_arcade_inputs()` each frame. However, that function reads SGDK's cached joystick state via `JOY_readJoypad()`, and the custom arcade VBlank path bypasses SGDK's normal VBlank dispatcher that performs `JOY_update()`. Result: the overlay is refreshed from a stale upstream cache, so values can remain stuck (for example `I:FFF7`, `K:------S-`) even while mode words advance.

## 2. Exact Overlay Input Source
Overlay input source identified: YES.

File: `apps/rastan/src/main.c`.
Function: `genesistan_debug_fg_proof()`.

Exact source variables:
- `input_p1 = genesistan_shadow_input_390001`
- `input_sys = genesistan_shadow_input_390007`
- `input_raw = ((u16)input_p1 << 8) | input_sys` (rendered as `I:XXXX`)

`K:UDLR12SC` bit mapping (active-low decode in overlay):
- `U` -> `input_p1 bit0 == 0`
- `D` -> `input_p1 bit1 == 0`
- `L` -> `input_p1 bit2 == 0`
- `R` -> `input_p1 bit3 == 0`
- `1` -> `input_p1 bit4 == 0`
- `2` -> `input_p1 bit5 == 0`
- `S` -> `input_sys bit3 == 0`
- `C` -> `input_sys bit0 == 0`

## 3. Where Shadow Input Bytes Are Supposed to Be Updated
Shadow input refresh path identified: YES.

File: `apps/rastan/src/startup_bridge.c`.
Function: `genesistan_refresh_arcade_inputs()`.

Expected update behavior:
- Reads controller state with:
  - `JOY_readJoypad(JOY_1)`
  - `JOY_readJoypad(JOY_2)`
- Rebuilds active-low arcade shadow bytes:
  - `genesistan_shadow_input_390001 = build_player_input_byte(p1_state)`
  - `genesistan_shadow_input_390003 = build_player_input_byte(p2_state)`
  - `genesistan_shadow_input_390005 = build_aux_input_byte(p1_state)`
  - `genesistan_shadow_input_390007 = build_system_input_byte(p1_state, p2_state)`

When it runs:
- Called from `_VINT_arcade_mode` in `apps/rastan/src/boot/sega.s`.
- Intended cadence: per-frame arcade VBlank path.

## 4. Is Shadow Input Refresh Active in Current Runtime Path
Shadow input refresh active in current runtime path: PARTIAL.

Why PARTIAL:
- YES: `genesistan_refresh_arcade_inputs()` is called each arcade VBlank (`_VINT_arcade_mode`).
- NO (upstream): it depends on `JOY_readJoypad()` values, and SGDK `JOY_readJoypad()` returns cached `joyState[]`.
- SGDK refreshes `joyState[]` in `JOY_update()`, which is normally called by `SYS_doVBlankProcess()`.
- Current arcade VBlank path explicitly bypasses SGDK dispatch, so that normal `JOY_update()` path is not guaranteed to run in the active ownership path.

## 5. Best Explanation of `I:FFF7` and `K:------S-`
- `I:FFF7` decodes to `input_p1=0xFF`, `input_sys=0xF7`.
- With active-low semantics, `0xF7` means system bit3 is low, i.e. Start1 pressed.
- `K:------S-` is exactly consistent with that decode:
  - UDLR12 all not pressed (`-`),
  - `S` shown pressed,
  - `C` not pressed.

Most likely meaning in this runtime:
- stale cached system-byte value with Start1 latched low in SGDK joy cache, not a live per-frame hardware poll reflected into the overlay.

## 6. Single Root Cause
`INPUT_REFRESH_EXISTS_BUT_NOT_CALLED_IN_ACTIVE_VBLANK/TICK_PATH`

Specific interpretation for this project state:
- shadow-byte refresh function is called, but the authoritative SGDK joy-cache refresh (`JOY_update`) is not in the active arcade VBlank ownership flow that feeds those reads.

## 7. Single Next Implementation Target
Patch the active arcade VBlank input path so upstream joystick cache is refreshed every frame before shadow-byte packing (single site target: `_VINT_arcade_mode` -> ensure `JOY_update()` happens before `genesistan_refresh_arcade_inputs()` reads `JOY_readJoypad()`).

## 8. Final Verdict
Mode words advancing while overlay input remains stuck is best explained by a stale upstream joystick cache, not by overlay decode errors. The overlay is reading the right shadow bytes, but those bytes are reconstructed from non-fresh SGDK input state in the current arcade ownership path.
