# Cody Video Exchange Summary — 2026-04-08

## Scope
This summary captures the exchange where runtime behavior was reported from video recordings and analyzed without code changes.

## User Reports
- `video_test_2026-04-07.mp4` was reported as output from the current build.
- Buttons were reported as having no effect at runtime.
- A second recording was provided: `Recording 2026-04-08 123800.mp4` (BlastEm).
- Additional note from user:
  - BlastEm video output matches real Genesis hardware.
  - Exodus does not show the checkerboard the same way and appears animated in a way not seen in BlastEm or on real hardware.

## Analysis Constraints Followed
- Strict analysis only.
- No code edits.
- No source modifications.

## Recordings Reviewed
- `states/screenshots/video_test_2026-04-07.mp4` (Exodus, ~3.43s)
- `states/screenshots/Recording 2026-04-08 123800.mp4` (BlastEm, ~17.66s)
- `states/screenshots/Recording 2026-04-08 123348.mp4` (Exodus with register pane visible)
- `states/screenshots/First Build Recording 2026-04-07 203452.mp4` (Exodus with register pane visible)

## Key Findings
### 1. Exodus PC values observed
From recordings that show Exodus CPU registers:
- In `First Build Recording 2026-04-07 203452.mp4`:
  - PC observed at `0x00000200`
  - PC observed at `0x0000038A`
- In `Recording 2026-04-08 123348.mp4`:
  - PC observed in `0x46FCxxxx / 0x46FDxxxx` range
  - Specific values observed: `0x46FCBCF0`, `0x46FD0282`

Note: `video_test_2026-04-07.mp4` does not display the CPU register pane, so PC is not visible in that clip.

### 2. Emulator output mismatch
- BlastEm clip shows square-checkerboard presentation and mostly stable behavior across sampled frames.
- Exodus clips show a different pattern style (dash/stripe-like) and significant frame-to-frame animation.
- This is consistent with the user’s note that BlastEm aligns with real hardware while Exodus does not in this scenario.

### 3. Input-effect observation
- The captured behavior remained in the checkerboard/debug-like state with no visible progression from button presses in the reviewed clips.
- This matches the user’s report that button input currently does nothing.

## Outcome
- Findings reported only.
- No code changes performed during this exchange.
