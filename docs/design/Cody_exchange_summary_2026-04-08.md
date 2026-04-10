# Cody Exchange Summary (2026-04-08)

## Summary
This exchange shifted from implementation prompts to strict analysis-only reporting based on emulator/hardware recordings. The requested constraint was explicit: no code changes, only findings.

## Scope and Constraints Confirmed
- Analysis-only requested.
- No runtime/source modifications requested for the strict-analysis step.
- Focus was on observed behavior across Exodus, BlastEm, and real Genesis output.

## User-Provided Evidence and Reports
- `states/screenshots/video_test_2026-04-07.mp4`
- `states/screenshots/[Cody - Implementation, FG row0 bring-up stripe removal] Recording 2026-04-07 130152.mp4`
- `states/screenshots/[Cody - Implementation, remove FG full-plane commit] Recording 2026-04-07 140108.mp4`
- `states/screenshots/First Build Recording 2026-04-07 203452.mp4`
- Additional user report: BlastEm recording (`Recording 2026-04-08 123800.mp4`) showing behavior matching real hardware.

## Reported Runtime Behavior
- Buttons currently do nothing.
- In Exodus, checkerboard behavior differs from BlastEm/real Genesis.
- In Exodus, background/checkerboard appears to animate and blue noise moves up/down.
- In BlastEm and on real Genesis, video output matches each other more closely and does not show the same Exodus-only motion pattern.
- User requested attention to PC behavior visible in Exodus recording as part of strict analysis context.

## Technical Findings Captured During Strict Analysis Context
- Current diagnosis focus remained on pipeline/runtime behavior differences, not on adding new fixes in this step.
- Cross-emulator discrepancy was treated as significant evidence that emulator-specific handling may be exposing behavior not representative of hardware output.
- Input non-responsiveness remained an open runtime issue requiring subsequent targeted investigation.

## Outcome of This Exchange
- No code changes were performed as requested for the strict-analysis step.
- Findings were captured as evidence for follow-up debugging priorities:
  1. Input path verification (why button events are not affecting runtime state).
  2. PC/control-flow correlation in Exodus when divergence appears.
  3. Hardware-aligned validation priority using BlastEm + real Genesis as primary behavioral reference.
