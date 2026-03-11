# Video Reference Notes

This project can use short local videos as reference anchors for:

- startup flow
- attract/title transitions
- stage-entry behavior
- player animation timing
- hardware-harness debug output

## Current clip

Source:

- `video/VID_20260311_173918.mp4`

Derived artifacts:

- `build/video_frames/frame_01.png` through `frame_12.png`
- `build/video_frames/contact_sheet.png`

What this clip shows:

- `BlastEm` running the current `arcade-compat-harness`
- the on-screen debug HUD
- shadow player position changing over a short interval

What it does **not** show:

- arcade cabinet gameplay
- title/credit/start transition
- player drop-in sequence
- real Rastan sprite selection

So this clip is useful as a harness regression reference, not as an arcade
behavior oracle.
