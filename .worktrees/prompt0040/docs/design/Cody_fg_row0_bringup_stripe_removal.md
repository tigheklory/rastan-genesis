# Cody FG Row-0 Bring-Up Stripe Removal

## 1. Summary
This change removes the FG row-0 bring-up stripe write in `init_staging_state` so Plane A no longer contains the forced blue top-band source.

## 2. Root cause reference (Andy report)
Root cause reference: `docs/design/Andy_verify_fg_top_band_artifact.md`.

## 3. Exact file modified
- `apps/rastan-direct/src/main_68k.s`

## 4. Exact code removed or altered
Removed this block from `init_staging_state`:

- `lea     staged_fg_buffer, %a0`
- `move.w  #(64 - 1), %d7`
- `.Lfg_row0:`
- `move.w  #0x2003, (%a0)+`
- `dbra    %d7, .Lfg_row0`

## 5. Classification
- `BRINGUP_ONLY` (removed)

## 6. Why the stripe existed
The row-0 loop wrote `0x2003` into FG row 0 as a visible bring-up stripe.

## 7. Why it is now invalid
The stripe contaminates current video verification by introducing a periodic top-band artifact as FG Y scroll cycles.

## 8. Why removal is safe
`staged_fg_buffer` is already fully zeroed by the preceding `.Lfg_clear` loop, so deleting the row-0 overwrite keeps FG transparent without affecting other systems.

## 9. Verification expectations
- Blue top-band artifact should be gone.
- BG checkerboard should remain visible and stable.

## 10. Next-step impact (clean video baseline)
This removal restores a cleaner baseline for validating BG presentation and remaining raster behavior without FG bring-up contamination.
