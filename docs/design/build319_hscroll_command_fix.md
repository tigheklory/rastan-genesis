# Build 319 — HScroll VDP Command Address Fix

## 1. Executive Summary

Build 319 fixes a confirmed bug in `genesistan_scroll_commit_vdp()` where the HScroll table write targeted VRAM address 0xFC00 instead of the intended 0xF000. The VDP command constant was changed from 0x7C000003 to 0x70000003. This is a single-constant correction — no other logic changed.

## 2. Confirmed Prior Bug

VDP register 13 is set to 0x3C in `force_clean_vram_init()` (main.c:2076), which places the HScroll table at VRAM 0xF000. However, the scroll commit function wrote HScroll data using VDP command 0x7C000003, which decodes to VRAM address 0xFC00. The VDP read HScroll from 0xF000 (all zeros from VRAM clear) while the actual scroll values were written to 0xFC00 (unused region). Horizontal scroll was effectively always zero.

## 3. Exact Code Change

**File**: `apps/rastan/src/main.c`, function `genesistan_scroll_commit_vdp()`, line 1766

**Before**:
```c
*ctrl32 = 0x7C000003;          /* VDP cmd: VRAM write addr 0xF000 */
```

**After**:
```c
*ctrl32 = 0x70000003;          /* VDP cmd: VRAM write addr 0xF000 */
```

No other changes. Function structure, staged scroll writes, and VSRAM path are all preserved.

## 4. Old vs New VDP Command Decode

Genesis VDP VRAM write command format: `0x40000000 | ((addr & 0x3FFF) << 16) | ((addr >> 14) & 0x03)`

| | Command | A[13:0] | A[15:14] | Effective Address |
|-|---------|---------|----------|-------------------|
| **Old** | 0x7C000003 | 0x3C00 | 0x03 | **0xFC00** |
| **New** | 0x70000003 | 0x3000 | 0x03 | **0xF000** |

Verification: `0x40000000 | ((0xF000 & 0x3FFF) << 16) | ((0xF000 >> 14) & 0x03)` = `0x40000000 | (0x3000 << 16) | 0x03` = `0x40000000 | 0x30000000 | 0x03` = **0x70000003**. Correct.

## 5. Reg 13 Base vs HScroll Commit Address Match

| Item | Value |
|------|-------|
| VDP Register 13 | 0x3C → HScroll base = 0xF000 |
| HScroll commit address (after fix) | 0xF000 |
| **Match** | **YES** |

## 6. Build 319 Verification

### Structural
- Build succeeded: **YES**
- ROM: `dist/Rastan_319.bin` (3,932,160 bytes)
- Exceptions introduced: **NO** (same warnings as prior builds)

### Scroll Command Correction
- Old command: 0x7C000003
- New command: 0x70000003
- Old effective address: 0xFC00
- New effective address: 0xF000
- Matches reg 13 base after fix: **YES**

## 7. Visual Verification Status

**USER MUST VERIFY.** The fix corrects the HScroll write address so horizontal scroll values now reach the VDP. Visual behavior may change — horizontal scrolling should now work where it was previously stuck at zero.

## 8. Final Verdict

Single-constant bug fix. HScroll data now written to the correct VRAM address (0xF000) matching VDP register 13. No other logic changed.
