# Build 327 Runtime Contradiction + BlastEm Crash Audit

## 1. Executive Summary
Build 327 does contain the Window disable fix (`0x9180`, `0x9280`) and those values are not overwritten later in the active post-handoff path. The Window-plane explanation is therefore not sufficient as the primary explanation for the observed runtime behavior. The recurring BlastEm freeze at `C7121A` is most consistent with an unmapped 68k read caused by a bad pointer generated during the arcade tick path, and that crash path is the dominant blocker.

## 2. Did Build 327 Actually Contain the Window Fix
YES.

Evidence:
- `dist/Rastan_327.bin` and `apps/rastan/out/rom.bin` are identical (same SHA1).
- Disassembly of `request_start_rastan` shows:
  - `movew #-28288,%a0@` (`0x9180`)
  - `movew #-28032,%a0@` (`0x9280`)
- Binary diff vs Build 326 shows expected byte changes at:
  - `0x215550`: `0x0091 -> 0x8091`
  - `0x215554`: `0x0092 -> 0x8092`

## 3. Were reg17/reg18 Overwritten Later
NO.

Findings:
- Earlier writes exist in `request_start_rastan` (`0x9200`, `0x9100`) from the SGDK setup path.
- The forced-clean writes (`0x9180`, `0x9280`) occur later in the same function.
- After `force_clean_vram_init()`, no later reg17/reg18 writes are present in:
  - `request_start_rastan` post-clean flow,
  - `_VINT_arcade_mode` in `apps/rastan/src/boot/sega.s`,
  - `genesistan_pc080sn_commit_planes`, `genesistan_palette_commit_asm`, or `genesistan_scroll_commit_vdp`.

## 4. Was the Window Theory Sufficient
Incorrect as the main cause.

The fix is present and persists, but runtime behavior remained effectively unchanged and still reaches the crash.

## 5. Actual Visible Screen Layer in Build 327
Sprites.

The observed black screen with rolling/garbled moving elements is most consistent with sprite-layer activity being what remains visible.

## 6. Should Debug Text Have Been Visible If Fix Worked
YES.

`genesistan_debug_fg_proof()` writes `B:XXXX A:XXXX` into `pc080sn_fg_buffer`, and `genesistan_pc080sn_commit_planes` publishes that FG buffer to Plane A each VBlank. If the display path were correctly presenting Plane A, this debug text should appear on the actual screen.

## 7. Meaning of Crash Address `C7121A`
`0xC7121A` is interpreted as an invalid/unmapped 68k read target in this runtime context.

Most likely interpretation:
- It is not a valid ROM/WRAM target and not a normal VDP port access pattern.
- It matches a corrupted/bad pointer pattern in the `0xCxxxxx` family rather than a legitimate translated data fetch.
- The current sanitizer does not prevent this case:
  - `sanitize_arcade_workram()` only scrubs values where `(v & 0x00FF0000) == 0x00C00000` (only `0xC0xxxx`),
  - and it runs **after** `genesistan_run_arcade_tick_lean`, so a bad read inside the tick can crash first.

## 8. Single Most Likely Crash Source
`BAD_POINTER_FROM_ARCADE_TICK`

## 9. Single Root Cause
`CRASH_PATH_DOMINATES_BEFORE_VISIBLE_FIX_CAN_BE_OBSERVED`

## 10. Single Next Implementation Target
Instrument the code path that produces the `C7121A` read.

## 11. Final Verdict
Build 327 includes and retains the Window disable fix, so the contradiction is not caused by missing or reverted reg17/reg18 values. The recurring freeze at `C7121A` is the dominant failure and is most likely caused by a bad pointer generated during arcade tick execution, which occurs before current sanitization can prevent it.
