# Build 327 Runtime Contradiction Audit

## 1. Executive Summary
Build 327 does contain the documented Window-plane register fix (`0x9180`, `0x9280`). Those values are written after the earlier `VDP_setWindowOff()` writes and are not overwritten later in the active runtime path. The Window-plane theory therefore does not explain the unchanged visible result by itself. The most likely reason for no visible change is that the visible output at failure time is not being driven by Plane A.

## 2. Did Build 327 Actually Contain the Window Fix
YES.

Evidence:
- Source: `force_clean_vram_init()` writes
  - `*ctrl = 0x9180;` (reg17)
  - `*ctrl = 0x9280;` (reg18)
  in `apps/rastan/src/main.c`.
- Build artifact: `dist/Rastan_327.bin` differs from `dist/Rastan_326.bin` exactly at the expected bytes:
  - offset `0x215550`: `0x0091 -> 0x8091`
  - offset `0x215554`: `0x0092 -> 0x8092`
- Disassembly confirms `request_start_rastan` contains:
  - `movew #-28288,%a0@` (`0x9180`)
  - `movew #-28032,%a0@` (`0x9280`)

## 3. Were reg17/reg18 Overwritten Later
NO (not after `force_clean_vram_init()` in the active runtime path).

What was found:
- Earlier writes exist in `request_start_rastan` from `VDP_setWindowOff()` setup path:
  - `movew #-28160,%a2@` (`0x9200`)
  - `movew #-28416,%a2@` (`0x9100`)
- These occur before the forced-clean block.
- Later in the same function, forced-clean writes:
  - `0x9180`, `0x9280`
- After those writes, no later reg17/reg18 writes were found in:
  - `request_start_rastan` post-clean path,
  - `_VINT_arcade_mode` (`apps/rastan/src/boot/sega.s`),
  - `genesistan_pc080sn_commit_planes`, `genesistan_palette_commit_asm`, `genesistan_scroll_commit_vdp` call path.

## 4. Was the Window Theory Sufficient
Incorrect as the main cause.

The fix is present and not later reverted, yet the visible result did not materially change.

## 5. Actual Visible Screen Layer in Build 327
Sprites (primary visible source).

Given the reported black screen with rolling dots/garbled moving content, the dominant visible output is most consistent with sprite-layer activity, not a stable Plane A tilemap presentation.

## 6. Should Debug Text Have Been Visible If Fix Worked
YES.

`genesistan_debug_fg_proof()` writes `B:XXXX A:XXXX` into `pc080sn_fg_buffer` each VBlank, and `genesistan_pc080sn_commit_planes` then commits that FG buffer to Plane A before display-on. If Plane A were the active final render path after the Window fix, this text should have appeared on the actual game display.

## 7. Single Root Cause
`DISPLAY_OUTPUT_NOT_USING_PLANE_A`

## 8. Single Next Implementation Target
Force Plane A only display.

## 9. Final Verdict
Build 327 applied the Window register fix correctly, and reg17/reg18 are not overwritten later in the relevant runtime path. The unchanged runtime visuals indicate the main visible output path at failure time is not Plane A; therefore the Window fix alone could not produce the expected on-screen change.
