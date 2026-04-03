# Build 314 — Vertical Crop / Row-Bias Experiment

## 1. Executive Summary

Build 314 removes the carried-over 4-row vertical bias from the PC080SN WRAM buffer write path. The previous mapping skipped arcade rows 0-3 and wrote row 4 to buffer position 0. This experiment maps arcade rows directly: buffer row = arcade row, buffer col = arcade col.

## 2. Exact Row-Bias Change Made

In all three PC080SN buffer-writing functions, removed:

1. The `cmpi.w #4, %d0` / `blo .skip_write` guard (row < 4 skip)
2. The `subi.w #4, %d0` instruction (4-row offset subtraction)

The `lsl.w #7, %d0` (row * 128) and `add.w col, %d0; add.w col, %d0` (+ col * 2) remain unchanged.

Also added: mode4 gate in `genesistan_pc080sn_commit_planes` — commit only fires when `arcade_mode4 >= 2` (prevents overwriting nametables with zeros during attract mode).

## 3. Old Mapping vs New Mapping

### Old (Build 313)

| Arcade Row | Buffer Row | Buffer Offset |
|------------|------------|---------------|
| 0          | SKIPPED    | (no write)    |
| 1          | SKIPPED    | (no write)    |
| 2          | SKIPPED    | (no write)    |
| 3          | SKIPPED    | (no write)    |
| 4          | 0          | 0             |
| 5          | 1          | 128           |
| ...        | ...        | ...           |
| 31         | 27         | 3456          |

Buffer rows 0-3 always zero (BSS init). Arcade rows 0-3 discarded.

### New (Build 314)

| Arcade Row | Buffer Row | Buffer Offset |
|------------|------------|---------------|
| 0          | 0          | 0             |
| 1          | 1          | 128           |
| 2          | 2          | 256           |
| 3          | 3          | 384           |
| 4          | 4          | 512           |
| ...        | ...        | ...           |
| 31         | 31         | 3968          |

All arcade rows written to buffer. No rows skipped or offset.

## 4. Why This Was Tested

The 4-row bias was carried over from the direct-VDP-write path (Build 312 and earlier) without independent verification. The assumption was that arcade rows 0-3 mapped to Genesis VRAM rows above the visible area. This experiment tests whether that assumption was visually correct by removing it and observing the result.

## 5. Build 314 Verification

| Check | Result |
|-------|--------|
| Assembly compiled | YES |
| Link succeeded | YES |
| ROM produced | `dist/Rastan_314.bin` (3,799,266 bytes) |
| Postpatch applied | YES (19 warnings, pre-existing address shifts) |

## 6. Runtime Verification

### MAME Headless Trace (1499 frames, -video none)

| Metric | Result |
|--------|--------|
| Frames completed | 1499 |
| Exceptions | NONE |
| Hang | NO |
| Crash | NO |

Note: Symbol addresses shifted due to code size change (fewer instructions). This is expected and does not affect runtime behavior.

## 7. What This Experiment Can and Cannot Prove

### Can prove (with user visual verification):
- Whether arcade rows 0-3 contain visible tile data
- Whether the 4-row offset was displacing tiles incorrectly
- Whether removing the bias changes the rolling/dot pattern

### Cannot prove (headless only):
- Visual correctness of the tilemap display
- Whether scroll alignment improves
- Whether the 240-to-224 vertical crop is fully solved

**Visual verification: USER MUST VERIFY**

## 8. Files Modified

| File | Change |
|------|--------|
| `apps/rastan/src/startup_trampoline.s` | Removed row<4 skip + (row-4) bias from 3 functions; added mode4 gate to commit |
