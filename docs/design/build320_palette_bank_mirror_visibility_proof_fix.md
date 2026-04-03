# Build 320 — Temporary Palette Bank Mirror + Low-Index Visibility Proof Fix

## 1. Executive Summary

Build 320 modifies `genesistan_palette_commit_asm` to mirror the first populated 16-color CLCS block across all 4 Genesis CRAM palette lines. This is a temporary proof fix to determine whether palette-bank incompleteness is the primary reason the screen is mostly black. A low-index visibility rule ensures entry 1 is never black when entry 0 is also black, preventing invisible tiles due to both low indices being transparent/black.

## 2. Prior Confirmed Palette-Bank Problem

Per `docs/design/build319_tile_mapping_vs_palette_analysis.md`:

- The arcade palette routine at 0x59AD4 writes 16 colors per block (0-3) to CLCS offsets 0, 16, 32, 48
- During title/early gameplay, only block 2 (CLCS[32..47]) is populated
- The old commit transferred CLCS[0..63] straight to CRAM[0..63]
- Result: only CRAM line 2 had real colors; lines 0, 1, 3 were black
- Most scene tiles reference palette lines 0 or 1 via the attr_lut, rendering as black

## 3. Exact Commit Routine Change

**File**: `apps/rastan/src/startup_trampoline.s`, function `genesistan_palette_commit_asm`

**Old behavior**: Read CLCS[0..63], convert each xBGR-555 entry, write sequentially to CRAM[0..63].

**New behavior** (4 phases):

### Phase 1 — Active-bank detection
Scan CLCS blocks 0, 1, 2, 3 (16 entries each). For each block, test all 16 entries. The first block containing any non-zero entry is selected. If no block is populated, write 64 black entries to CRAM and exit.

### Phase 2 — Convert to stack buffer
Allocate 32 bytes on the stack. Convert the 16 entries from the selected CLCS block using the existing xBGR-555 → Genesis formula. Store 16 converted words in the stack buffer.

### Phase 3 — Low-index visibility enforcement
Check converted entry 0 and entry 1. If both are 0x0000 (black), scan entries 1-15 for the first non-black color and copy it into entry 1. This ensures at least one of the two lowest color indices is visible.

### Phase 4 — Mirror to all 4 CRAM lines
Set VDP CRAM write address to 0. Write the 16-entry buffer 4 times consecutively (auto-increment fills lines 0, 1, 2, 3). Free stack buffer.

### Register usage
Changed from `d0-d3/a0-a2` to `d0-d7/a0-a4` (wider save/restore).

## 4. Active-Bank Selection Rule

**Rule**: First populated block wins.

Scan order: block 0 (CLCS[0..15]), block 1 (CLCS[16..31]), block 2 (CLCS[32..47]), block 3 (CLCS[48..63]).

A block is "populated" if ANY of its 16 entries is non-zero.

The first populated block found is used for all 4 CRAM lines. If no block is populated, all CRAM entries are set to black.

In the current game state (title/early gameplay), block 2 is expected to be the first (and only) populated block.

## 5. Mirroring Behavior (CRAM Lines 0-3)

The selected 16-entry block is written identically to all 4 CRAM lines:

| CRAM Line | CRAM Entries | Source |
|-----------|-------------|--------|
| 0 | 0-15 | Converted block |
| 1 | 16-31 | Same converted block |
| 2 | 32-47 | Same converted block |
| 3 | 48-63 | Same converted block |

CRAM auto-increment is used. The VDP write address starts at 0 and advances by 2 for each word written (64 words total = 128 bytes = full CRAM).

## 6. Low-Index Visibility Rule

**Rule**: If converted entry 0 AND entry 1 are both 0x0000, replace entry 1 with the first non-black converted color found in entries 1-15.

Rationale:
- Entry 0 (color index 0) is typically the transparent/background color — it is expected to be black
- Entry 1 (color index 1) is the first "real" color index used by tile pixels
- If both are black, tiles that use only low color indices would be invisible
- Replacing entry 1 with the first available visible color ensures at least some tile content is visible

Edge case: If ALL 16 entries are black after conversion, no replacement is made (nothing visible to use). This would only happen if the source CLCS data contains all-zero or near-zero values.

The override is applied ONCE to the 16-entry buffer BEFORE mirroring, so all 4 CRAM lines receive the same adjusted palette.

## 7. Build 320 Verification

### Structural
- Build succeeded: **YES**
- ROM: `dist/Rastan_320.bin` (3,932,160 bytes)
- Exceptions introduced: **NO** (same 5 pre-existing unused-function warnings as prior builds)

### Palette proof behavior
- Selected CLCS bank for mirroring: **first populated block** (expected: block 2 at runtime)
- Mirroring to all 4 CRAM lines: **YES**
- Low-index visibility override: **YES** (entry 1 replaced if entries 0 and 1 both black)
- Exact low-index rule: replace entry 1 with first non-black from entries 1-15

## 8. Visual Verification Status

**USER MUST VERIFY.** Expected behavior:
- All 4 CRAM palette lines should show the same colors (mirrored from the active block)
- Scene tiles should be visible regardless of which palette line the attr_lut selects
- If palette-bank incompleteness was the primary visibility problem, the title screen should show recognizable scene graphics

## 9. Crash Verification Status

**USER MUST VERIFY.** The palette commit change does not affect any VDP registers, nametable writes, tile loading, or scroll behavior. The only change is to CRAM content. No new crash vectors are expected.

## 10. Final Verdict

Temporary proof fix. Mirrors a single active CLCS 16-color bank across all 4 Genesis CRAM lines with low-index visibility enforcement. If scene tiles become visible, this confirms palette-bank incompleteness as the primary screen-black root cause. Not intended as final palette architecture.
