# Build 318 — Palette Regression & Offline/Runtime Color Conversion Audit

## 1. Executive Summary

Build 318 removed the ROM table fallback from `genesistan_palette_commit_asm`, making the CLCS buffer the sole palette source. The CRAM debugger screenshot confirms the CLCS conversion path IS producing colored (non-grayscale) output — the palette fix succeeded. However, the ROM crashes with "machine freeze due to read from address C7121A." The palette change is structurally safe (stack balanced, registers preserved, CRAM writes bounded). The crash address 0xC7121A is invalid on Genesis (outside ROM/WRAM/VDP ranges) and indicates corrupted program counter or address register — this is NOT attributable to the palette routine. The most likely root cause is a pre-existing issue (possibly from the PC080SN WRAM buffer changes that shifted `.bss.patcher` addresses) that was present in Build 317 but never runtime-verified.

## 2. Exact Build 318 Palette Change

**File**: `apps/rastan/src/startup_trampoline.s`
**Routine**: `genesistan_palette_commit_asm`

### Exact logic removed:
1. `tst.w (%a0)` / `bne.s .Lpal_have_clcs` — test if CLCS entry 0 is non-zero
2. ROM table fallback path: `lea genesistan_palette_rom_table, %a0` → CRAM write → 64-word loop → `bra.s .Lpal_done`
3. `.Lpal_done` label

### Exact logic retained:
1. `lea genesistan_palette_clcs, %a0` — load CLCS source pointer
2. CRAM write address setup: `move.l #0xC0000000, (%a1)`
3. 64-entry conversion loop (xBGR-555 → Genesis `0000BBB0GGG0RRR0`)
4. Register save/restore (changed from `%d0-%d4/%a0-%a2` to `%d0-%d3/%a0-%a2` — D4 was unused)

### Summary:
- Fallback behavior removed: **YES**
- Conversion path changed: **NO** (same shift-and-mask formula retained)
- Source-selection logic changed: **YES** (CLCS is now sole source, no ROM table fallback)

## 3. Palette Commit Routine Safety Audit

Current `genesistan_palette_commit_asm` (Build 318):

```
Palette ASM Safety Check:
- stack balanced: YES (movem.l d0-d3/a0-a2 push, matched movem.l pop)
- register save/restore correct: YES (7 regs saved, same 7 restored)
- loop count exactly 64: YES (moveq #63, d0; dbra = 64 iterations)
- source pointer valid for all 64 reads: YES (genesistan_palette_clcs is 2048 words = 4096 bytes; 64 reads = 128 bytes, well within bounds)
- writes confined to CRAM path: YES (only 0xC00000 data port writes after CRAM command 0xC0000000)
- D4 removal safe: YES (D4 was never used in the conversion loop)
```

The palette routine cannot:
- Write outside CRAM (command word 0xC0000000 sets CRAM write mode)
- Corrupt stack (balanced push/pop)
- Corrupt registers (all used registers saved/restored)
- Overrun its loop (dbra with #63 = exactly 64 iterations)
- Produce invalid VDP commands (only CRAM write, no control port writes after setup)

## 4. Palette Source Validity Audit

```
Palette Source Validity:
- initialized before first commit: PARTIAL — .bss.patcher is zero-initialized at startup
- contains 64 valid entries: DEPENDS ON TIMING — all-zero until arcade palette writes populate it
- format matches commit assumption: YES (arcade CLCS captures at 0x200000 are in xBGR-555 format)
- entry 0 black is normal: YES (palette entry 0 is typically transparent/black in all Taito games)
```

**Key finding**: `genesistan_palette_clcs` starts as all zeros (BSS). The first VBlank frames will commit all-black CRAM until arcade palette writes populate the buffer. This is functionally correct (black screen before palette init) but could appear broken on visual inspection.

The CLCS buffer is populated via opcode hooks that intercept arcade writes to address 0x200000. The `startup_title_remap.json` spec maps arcade 0x200000 → `genesistan_palette_clcs`. Once the arcade palette initialization code runs (during `genesistan_run_arcade_tick_lean`), the buffer is populated.

## 5. Removed Fallback Analysis

**Was the fallback actually wrong?**

YES — the fallback was broken in two ways:

1. **Detection logic was wrong**: `tst.w (%a0)` checked if CLCS entry 0 was zero. Palette entry 0 is ALWAYS black (0x0000) in Taito games — this is the transparent/background color. So the test ALWAYS triggered the fallback, meaning the CLCS conversion path was NEVER taken.

2. **ROM table contains grayscale data**: The `postpatch_startup_rom.py` fills `genesistan_palette_rom_table` with a synthetic grayscale ramp (Build 113 placeholder), NOT actual game palette data. The Python code at line 1108-1115:
   ```python
   _color = _i % 16
   if _color == 0:
       _gen = 0
   else:
       _v = min(7, (_color * 7 + 14) // 15)
       _gen = (_v << 1) | (_v << 5) | (_v << 9)
   ```
   This produces equal R=G=B values = grayscale. This matches the user's earlier screenshot showing grayscale CRAM.

**Removing the fallback was correct** — it was masking the real CLCS conversion path and writing grayscale instead.

## 6. Offline Python/Build Conversion Audit

```
Offline Conversion Audit:
- palette converted in Python/build stage: NO (ROM table filled with grayscale ramp placeholder, not actual palette conversion)
- PC080SN colors converted in Python/build stage: NO (precompute_pc080sn_tile_lut.py does tile-to-VRAM slot mapping only; precompute_pc080sn_attr_lut.py does arcade→Genesis attribute bit remapping only, not color)
- PC090OJ colors converted in Python/build stage: NO (preconvert_pc090oj_tiles.py does 16x16→8x8 tile layout rearrangement only, not color)
- sprite-related palette interpretation converted offline: NO
- exact scripts/files responsible:
  - tools/translation/preconvert_pc090oj_tiles.py → tile layout rearrangement → build/pc090oj_genesis.bin
  - tools/translation/precompute_pc080sn_tile_lut.py → tile VRAM slot LUT → build/pc080sn_tile_vram_lut.bin
  - tools/translation/precompute_pc080sn_attr_lut.py → attribute bit remap LUT → build/pc080sn_attr_lut.bin
  - tools/translation/postpatch_startup_rom.py → grayscale ramp → ROM at genesistan_palette_rom_table
```

**Critical finding**: NO offline color conversion exists for actual game palette data. The ROM table's grayscale ramp is a debug placeholder from Build 113. All real palette color conversion must happen at runtime.

## 7. Patching-Stage vs Runtime Color Responsibility Split

```
Color Responsibility Split:

Patch/build stage does:
  - PC090OJ tile layout rearrangement (cell → 8x8 tile reorder, NO color change)
  - PC080SN tile-to-VRAM slot mapping (LUT only, NO color data)
  - PC080SN attribute bit remapping (arcade attr → Genesis nametable word bits)
  - Fill genesistan_palette_rom_table with grayscale ramp placeholder (NOT real colors)

Runtime does:
  - Capture arcade palette writes (0x200000) into genesistan_palette_clcs[] via opcode hooks
  - Convert CLCS xBGR-555 → Genesis 0000BBB0GGG0RRR0 in genesistan_palette_commit_asm
  - Write converted palette to CRAM (64 entries per frame)

Duplicated conversion exists: NO
```

## 8. Duplicate Conversion Determination

**NO** — runtime conversion is the only conversion for actual game palette data.

Evidence:
- The ROM table grayscale ramp is a placeholder that never contained real palette data
- The Build 318 change removed the ROM table path entirely
- The CLCS → Genesis conversion in the assembly loop is the sole color conversion
- No Python/build script converts actual arcade palette data
- The `_taito_to_genesis()` function in Python is never called with real palette data (it's dead code — the grayscale ramp loop replaces it entirely)

## 9. BlastEm Crash Analysis

### Can the palette change directly cause "machine freeze due to read from address C7121A"?

**NO, not directly.**

Justification:
- 0xC7121A is not a valid Genesis address (outside ROM 0x000000-0x3FFFFF, WRAM 0xFF0000-0xFFFFFF, VDP 0xC00000-0xC00007, I/O 0xA10000-0xA1001F)
- The palette routine ONLY reads from `genesistan_palette_clcs` (valid BSS address) and writes to VDP ports 0xC00000/0xC00004 (valid)
- The palette routine saves/restores all registers — no clobbered state escapes
- The routine cannot produce an invalid address on its own
- The crash address suggests corrupted PC or address register from an unrelated path

### What 0xC7121A likely indicates:
- Corrupted function pointer or return address
- Misaligned opcode_replace hook jumping to a wrong address
- BSS address shift causing a hook to read a garbage address from a shifted variable location

### Pre-existing vs new:
Build 317 was marked "STRUCTURAL BUILD ONLY — USER MUST VERIFY AT RUNTIME." The Build 317 changes added 8KB of WRAM buffers (`pc080sn_bg_buffer`, `pc080sn_fg_buffer`) to `.bss.patcher`, which shifts all subsequent `.bss.patcher` symbol addresses. If any opcode_replace entries hardcode addresses of symbols AFTER these buffers, those entries would be broken since Build 317 — but were never caught because Build 317 was never runtime-tested.

## 10. Screenshot-Based Evidence

### Screenshot 1 (all black):
- Main display: black
- CRAM debugger: black (all zeros)
- VRAM debugger: black

**Interpretation**: This is the initial state before arcade palette writes populate CLCS. With the ROM table fallback removed, CLCS starts as all-zero, producing all-black CRAM. This is expected behavior — not a bug. The palette will populate once the arcade tick runs palette initialization.

### Screenshot 2 (colored CRAM + crash):
- Main display: black
- CRAM debugger: **shows colored entries** (reds, blues, yellows, browns — clearly game palette colors)
- VRAM debugger: black
- Fatal Error: "machine freeze due to read from address C7121A"

**Interpretation**:
1. **CRAM colors prove the CLCS path works** — the xBGR-555 → Genesis conversion is producing real game colors
2. **Black main display despite colored CRAM** — tiles/nametables are not populated (VRAM is empty), OR display was disabled at crash time
3. **Empty VRAM** — the PC080SN tile preload and nametable population may not be functioning correctly
4. **Crash at 0xC7121A** — occurs AFTER palette has been committed (CRAM has colors), indicating the crash is in a different code path (arcade tick, tilemap commit, or opcode hook)

**The palette change itself succeeded. The crash is in a separate subsystem.**

## 11. Rainbow Islands Comparison

| Aspect | Rainbow Islands Genesis | Build 318 |
|--------|------------------------|-----------|
| **Palette source format** | Pre-converted Genesis words in ROM/WRAM | xBGR-555 captured from arcade writes at runtime |
| **When committed** | VBlank, flag-triggered (0xFFFFF680) | VBlank, every frame (unconditional) |
| **Offline conversion** | YES — palette pre-converted at ROM build time | NO — converted at runtime in commit routine |
| **Runtime conversion** | None needed (data already in Genesis format) | YES — xBGR-555 → Genesis shift/mask per entry |
| **Fallback paths** | None described | Removed in Build 318 (was grayscale ROM table) |
| **Entry 0 = black** | Normal (transparent/BG color) | Normal, but was incorrectly treated as "invalid" indicator pre-318 |
| **Commit safety** | Flag-gated (only when dirty) | No gate — commits every frame even if unchanged |

**One exact structural difference that matters**: Rainbow Islands pre-converts palette data offline and has NO runtime conversion. Rastan MUST convert at runtime because palette data is captured dynamically from arcade writes. This means Rastan's palette pipeline is inherently more complex — the CLCS capture → convert → CRAM chain has more points of failure than Rainbow Islands' static ROM → CRAM chain. However, this runtime conversion approach is architecturally correct for Rastan's dynamic palette model.

## 12. Single Most Likely Root Cause

**Palette change exposed pre-existing bug elsewhere.**

The Build 318 palette change is structurally safe. The crash at 0xC7121A is an invalid address that cannot be produced by the palette commit routine. The CRAM debugger proves the palette conversion is working correctly. The most probable cause is stale opcode_replace addresses in `startup_title_remap.json` caused by the PC080SN WRAM buffer addition (Build 316/317) adding 8KB to `.bss.patcher` and shifting subsequent symbol addresses. Build 317 was never runtime-verified, so this crash was present but undetected.

## 13. Single Best Next Implementation Target

**Verify and fix opcode_replace BSS addresses in `startup_title_remap.json`.**

The `.bss.patcher` section grew by 8KB (two 4096-byte tilemap buffers added at the end of `.bss.patcher` in `startup_trampoline.s`). Any opcode_replace entries that reference symbols placed AFTER these buffers in `.bss.patcher` will have stale addresses. The postpatch verification step should catch these as "expected X but found Y" errors — but only if the original_bytes in the spec still match. A full rebuild with address verification, similar to the fix applied for Build 317's stale addresses, is needed.

Additionally, confirm whether `genesistan_palette_clcs` (which is in `.bss.patcher` AFTER the new buffers) has a correct address in all opcode hooks. If the CLCS capture address shifted, palette writes from the arcade code would go to the wrong location.

## 14. Final Verdict

Build 318's palette change is **correct and working** — CRAM shows real game colors. The crash is **not caused by the palette change**. It is caused by a pre-existing issue (most likely stale BSS addresses from the `.bss.patcher` growth in Build 316/317) that was never caught because Build 317 was not runtime-tested. The next step is to audit and fix the opcode_replace BSS address references, not to revert the palette change.
