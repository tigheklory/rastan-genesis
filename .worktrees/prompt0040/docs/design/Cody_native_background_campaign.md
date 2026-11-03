# Cody Native Background Campaign

## Current status

Build 0415 is **HARDWARE VISUAL REJECTED**. Its 40x28 viewport-local producer
model removed required logical maintenance.

Build 0416 is also **HARDWARE VISUAL REJECTED**. Its 41x29 fine-scroll `+1`
correction was valid but incomplete: under the surviving moving-source runtime,
the full 64-row/64-column logical state, N/N+32 handling, segment rebase, and
trailing retention remain correctness requirements (KF-072).

Build 0417 restores the accepted full-span logical coordinate model across
selector0, selector1/2, pan rows, and independent Plane-B directional/package
production. It keeps the safe physical improvements: accessor seam, row/column
dirty masks, per-column gather, and 32-word DMA with destination autoincrement
128. The verifier now requires both broken 0415 and broken 0416 to fail and the
full-span model to pass initial seed, N/N+32, source-rebase, trailing-retention,
Plane-B context, projection, and DMA contracts.

Build 0417 is pending separate Tighe real-hardware visual and performance
assessment. `_do` black bands are intentional IRQ6-overrun instrumentation and
must not be classified as Layer-A/Layer-B corruption. Do not begin BG-B or
later background phases until rendered scenery is accepted independently of
the overrun signal.

## Remaining phases

- BG-B: fuse collision and name production into one descriptor traversal while
  preserving accepted Build 0417 output exactly. Expected row/map range: 45–60K best,
  approximately 75K conservative.
- BG-C: replace the private accessor macro bodies with O(1) generated
  Genesis-native Plane-A, Plane-B, collision, and dynamic-override records.
  Expected row/map range: 8–15K.

Phase D, Phase E, Build-0401 ownership work, and H25 remain out of scope.
