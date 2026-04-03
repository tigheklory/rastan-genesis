# Build 330 Plane A Mode and Input Debug Overlay

## 1. Executive Summary
Build 330 extends the existing Plane A debug overlay by adding live mode/state words and live input state display, without changing gameplay or render flow behavior.

## 2. Existing Debug Overlay Left Intact
The existing lines remain unchanged and still render through `genesistan_debug_fg_proof()`:
- `B:XXXX A:XXXX`
- `P:XXXXXXXX`

## 3. Mode/State Source Used
Authoritative source: `genesistan_arcade_workram_words` state-machine words documented in startup initialization.
- `genesistan_arcade_workram_words[0]` (A5@(0), main state)
- `genesistan_arcade_workram_words[1]` (A5@(2), sub-state)
- `genesistan_arcade_workram_words[2]` (A5@(4), inner step)

Overlay format added:
- `M:XXXX XXXX XXXX`

## 4. Input Source Used
Authoritative source: existing arcade shadow input bytes updated by `genesistan_refresh_arcade_inputs()`.
- `genesistan_shadow_input_390001` (P1 directional/action byte, active-low)
- `genesistan_shadow_input_390007` (system byte including start/coin bits, active-low)

Overlay formats added:
- `I:XXXX` where value is `390001:390007` packed as one 16-bit hex value
- `K:UDLR12SC` live pressed summary (`-` when not pressed)

## 5. Overlay Format Added
Rows now rendered by the same existing Plane A debug text path:
- Row 1: `B:XXXX A:XXXX`
- Row 2: `P:XXXXXXXX`
- Row 3: `M:XXXX XXXX XXXX`
- Row 4: `I:XXXX`
- Row 5: `K:UDLR12SC`

## 6. Non-Goals
- No gameplay logic changes
- No tick logic changes
- No sprite suppression logic changes
- No sanitizer/pointer instrumentation changes
- No palette/scroll/VBlank flow changes
- No input remapping changes

## 7. Build Verification
Build command:

```bash
source tools/setup_env.sh
make -C apps/rastan release
```

Result:
- Build succeeded
- Artifact: `dist/Rastan_330.bin`
- No new errors
- No new warnings (same 5 pre-existing warnings)

## 8. Expected Runtime Result
- Existing debug text remains visible in Plane A viewer
- Mode/state line is visible and updates with runtime state
- Input line and key summary are visible and reflect live input changes

## 9. Final Verdict
Build 330 adds mode and live input telemetry to the existing Plane A debug overlay using the same established renderer path, with no behavior changes outside debug display.
