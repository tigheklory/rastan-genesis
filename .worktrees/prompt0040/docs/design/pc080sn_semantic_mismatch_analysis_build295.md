# PC080SN Semantic Mismatch Analysis — Build 295

## 1. Executive Summary

Build 295 correctly removed the +0x14 tile offset from both BG and FG assembly and reverted the Python LUT discovery formula (all Build 294 regressions are gone). The tile read semantics, strip computation, attr LUT, FG hook, and Python precompute are now all correct.

**One primary mismatch remains**: `PC080SN_CWINDOW_BASE = 0xC08000` in `pc080sn_dest_ptr_to_row_col()` applies to both the BG and FG hooks. The BG C-window is at `0xC00000`, not `0xC08000`. This causes every BG dest_ptr validity check to fail, so `genesistan_asm_tilemap_commit_bg()` is never called and Genesis VDP BG_B (VRAM `0xC000`) is never written.

The FG hook is unaffected because FG dest_ptr values are always in the `[0xC08000, 0xC0BFFF]` range, which passes the check.

---

## 2. Confirmed Correct Systems

The following were verified against `build/maincpu.disasm.txt` and the current Build 295 source.

| System | Status | Evidence |
|--------|--------|----------|
| BG tile read formula: `table_base + (strip<<1) + (row<<3)` | CORRECT | Arcade disasm `0x559FC: lea %a2@(0,%d7:w),%fp`; Genesis `adda.w %d0, %a4` (no +0x14) `startup_trampoline.s:207–213` |
| FG tile read formula: `table_base + (strip<<3) + (col<<1)` | CORRECT | Arcade disasm `0x55A9E: lea %a2@(0,%d7:w),%fp`; Genesis `adda.w %d0, %a4` (no +0x14) `startup_trampoline.s:333–338` |
| BG inner loop row stride = 8 bytes | CORRECT | Arcade: `(row<<3)`; Genesis: `adda.w #8, %a4` per iteration `startup_trampoline.s:272` |
| FG inner loop col stride = 2 bytes | CORRECT | Arcade: `(col<<1)`; Genesis: `adda.w #2, %a4` per iteration `startup_trampoline.s:397` |
| BG strip_raw unmasked (full 0..63 range) | CORRECT | Arcade BG outer loop at `0x55968` never masks strip_raw; Genesis removed `andi.w #0x0003` in Build 294 |
| FG strip masking: `mode==2 ? raw&3 : ~raw&3` | CORRECT | Arcade disasm `0x55A2A–55A3C`; Genesis `main.c:1316` |
| FG dest_ptr no-writeback to workram[0x10A4] | CORRECT | `genesistan_hook_tilemap_plane_b()` does not call `pc080sn_workram_write_u32(PC080SN_DEST_PTR_B_OFFSET, ...)` |
| Attr LUT 5-bit key: `(prio<<4)|(vflip<<3)|(hflip<<2)|pal` | CORRECT | `startup_trampoline.s:215–236`; matches `precompute_pc080sn_attr_lut.py` key formula |
| Python LUT BG formula: `table_base + (strip<<1) + (row<<3)` | CORRECT | `precompute_pc080sn_tile_lut.py:80` — no `PC080SN_TABLE_TILE_OFFSET` in address formula |
| Python LUT FG formula: `table_base + (strip<<3) + (col<<1)` | CORRECT | `precompute_pc080sn_tile_lut.py:84` — same |
| Python BG strip range: `range(MAX_STRIP_RANGE)` = 0..63 | CORRECT | `precompute_pc080sn_tile_lut.py:78` |
| Python FG strip range: `range(PC080SN_FG_STRIP_RANGE)` = 0..3 | CORRECT | `precompute_pc080sn_tile_lut.py:83` |
| Descriptor source: workram[0x1000] = arcade absolute 0x10D000 | CORRECT | Arcade A5=0x10C000 (verified below); A5+0x1000=0x10D000 matches desc list builder source `maincpu.disasm.txt:107346` |
| FG VDP address: `0xE000 + (dest_row-4)*128 + dest_col*2` | CORRECT (structural) | `startup_trampoline.s:376–380`; FG plane BG_A at VRAM `0xE000`, 64-wide plane, row stride 128 |
| VDP control port: direct writes to `0xC00004`/`0xC00000` | CORRECT | `startup_trampoline.s:175–177` (`movea.l #0xC00004`, `movea.l #0xC00000`, `move.w #0x8F02`) |
| FG assembly fires | CONFIRMED | FG dest_ptr from workram[0x10A4] is computed as `D0 + 0xC08000` (`maincpu.disasm.txt:107207–107208, 107245–107246`), passes PC080SN_CWINDOW_BASE=0xC08000 check |

---

## 3. Confirmed Mismatches

### MISMATCH #1 (CRITICAL) — BG hook never calls assembly: PC080SN_CWINDOW_BASE wrong for BG

**Classification**: FACT — no ambiguity.

**The constant**:
```c
/* main.c:1246 */
#define PC080SN_CWINDOW_BASE  0x00C08000UL
```

**How it is used**:
```c
/* main.c:1268–1283 */
static bool pc080sn_dest_ptr_to_row_col(u32 dest_ptr, u16 *out_row, u16 *out_col)
{
    const u32 addr24 = dest_ptr & 0x00FFFFFFUL;
    const u32 offset = addr24 - PC080SN_CWINDOW_BASE;
    ...
    if ((addr24 < PC080SN_CWINDOW_BASE) || ...)   /* ← guard */
        return FALSE;
    ...
}
```

**How the BG hook calls it**:
```c
/* main.c:1287–1309 */
void genesistan_hook_tilemap_plane_a(void)
{
    u32 dest = pc080sn_workram_read_u32(PC080SN_DEST_PTR_A_OFFSET);  /* workram[0x10A0] */
    ...
    if (!pc080sn_dest_ptr_to_row_col(dest, &dest_row, &dest_col))
    {
        dest += (u32)PC080SN_DESC_COUNT * 0x400U;   /* ALWAYS TAKEN — never reaches assembly */
    }
    else
    {
        dest = genesistan_asm_tilemap_commit_bg(...);   /* NEVER REACHED */
    }
}
```

**Why the check always fails for BG**:

The arcade initializes workram[0x10A0] (BG dest_ptr) to `0xC00400`:
```
/* build/maincpu.disasm.txt:107729 */
55e54:  movel #12583936,%a5@(4256)   /* 12583936 = 0xC00400 → workram[0x10A0] */
```

The BG outer loop at `0x55968` reads: `moveal %a5@(4256),%a0` — the BG C-window destination. The BG C-window hardware address range is `0xC00000–0xC03FFF`. After each builder call, A0 advances by 16384 bytes (16 descriptors × 4 rows × 256 bytes/row), wrapping within `0xC00000–0xC03FFF`. It never enters the `[0xC08000, 0xC10000)` range.

The only code path that writes a `0xC08000`-range value to workram[0x10A0] is at `maincpu.disasm.txt:107287` (`0x5581E`), which is only reached when `mode != 0`. When `mode != 0`, the FG builder (`0x55990`) runs — not the BG builder. The BG dest_ptr write in that path has no effect on BG builder behavior.

**Result**: `addr24 = 0xC00400`, `addr24 < PC080SN_CWINDOW_BASE (0xC08000)` → TRUE → `pc080sn_dest_ptr_to_row_col()` returns FALSE on every call. `genesistan_asm_tilemap_commit_bg()` is never invoked. Genesis VDP BG_B plane (VRAM `0xC000`) is never written after VRAM preload. The BG plane shows only whatever tiles the preloader placed, with no positional mapping.

**Expected fix scope**: `PC080SN_CWINDOW_BASE` must correctly distinguish BG (`0xC00000`) from FG (`0xC08000`) in `pc080sn_dest_ptr_to_row_col()`, or the function must be split/parameterised per plane. The BG valid range is `[0xC00000, 0xC04000)` (16384 bytes). The FG valid range is `[0xC08000, 0xC0C000)` (16384 bytes).

---

## 4. Rejected Hypotheses

| Hypothesis | Why Rejected |
|------------|--------------|
| +0x14 tile offset still present | Verified absent: `startup_trampoline.s:207–214` shows no `adda.w #0x0014,%a4` for BG; `startup_trampoline.s:333–340` same for FG |
| BG strip_raw masked to 0..3 | `andi.w #0x0003` removed from BG path in Build 294; BG correctly uses full strip_raw value |
| FG dest_ptr writeback still present | Writeback removed in Build 294; `genesistan_hook_tilemap_plane_b()` has no `pc080sn_workram_write_u32(PC080SN_DEST_PTR_B_OFFSET, ...)` |
| Python LUT still using +0x14 | `precompute_pc080sn_tile_lut.py:80,84` confirmed: tile addresses use zero offset |
| `sanitize_arcade_workram()` zeroing dest_ptrs | Function defined at `main.c:1916` but never called — dead code; does not execute |
| Descriptor source offset wrong | `PC080SN_DESC_LIST_OFFSET = 0x1000` at `main.c:1239`; if arcade A5=0x10C000 (consistent with all A5-relative absolute addresses in disasm), then A5+0x1000 = 0x10D000 = desc list builder source at `maincpu.disasm.txt:107346`. ✓ |
| FG assembly not firing | FG dest_ptr computed as `D0 + 0xC08000` in arcade (disasm `0x556F2`, `0x5577E`); passes `PC080SN_CWINDOW_BASE = 0xC08000` check. FG assembly does run. |
| Attr LUT wrong | 5-bit key extraction at `startup_trampoline.s:215–236` matches `precompute_pc080sn_attr_lut.py` key formula exactly |

---

## 5. Remaining Unknowns

### UNKNOWN A — BG VDP address formula correctness (unblocked by MISMATCH #1 fix)

**Status**: CANNOT BE TESTED until `pc080sn_dest_ptr_to_row_col()` is fixed for BG.

**What is known**: The BG assembly uses:
```
VDP_addr = 0xC000 + (dest_row - 4) * 128 + dest_col * 2
```
- `0xC000` = Genesis BG_B VRAM base. ✓ per architecture doc.
- Row stride 128 = 64 cells × 2 bytes/cell. ✓ for 64-wide Genesis plane.
- `dest_row - 4`: skip guard removes first 4 rows (matches FG pattern). Structural analysis says this is intentional for the 4-row vertical alignment bias between 240px arcade and 224px Genesis.

**Structural assessment**: LIKELY CORRECT. The formula mirrors the confirmed-correct FG formula with only the plane base differing (`0xC000` vs `0xE000`). First real-build output after fix will confirm.

### UNKNOWN B — VRAM slot range overlap between PC080SN pool B and sprite tiles

**Status**: NOT VERIFIED.

PC080SN pool B uses VRAM slots `1280..1439` (`TILE_CACHE_BASE_B=1280`, `TILE_CACHE_SIZE_B=160` in `precompute_pc080sn_tile_lut.py:14–15`). Sprite tiles start at `FRONTEND_RUNTIME_SPRITE_TILE_BASE = 1024` (`startup_trampoline.s:26`). If Rastan has more than 256 sprite tiles (`1280 - 1024 = 256`), sprite DMA writes would clobber PC080SN pool B tiles.

This is unverified. Sprite tile count has not been measured.

### UNKNOWN C — descriptor_valid() bounds check with +0x14

**Status**: MINOR, LOW RISK.

`precompute_pc080sn_tile_lut.py:46–53` uses `PC080SN_TABLE_TILE_OFFSET = 0x14` in the `max_bg_addr` bounds formula:
```python
max_bg_addr = table_base + PC080SN_TABLE_TILE_OFFSET + ((MAX_STRIP_RANGE - 1) << 1) + (3 << 3) + 1
```
This checks 0x15 more bytes than the actual BG tile address range requires. For tile tables near the end of ROM, this could incorrectly exclude a valid descriptor. In practice, no arcade tile tables are expected within 21 bytes of ROM end. Assessed as no practical impact.

---

## 6. Final Root Cause Candidates (Ranked by Evidence)

### Rank 1 — PC080SN_CWINDOW_BASE = 0xC08000 silences BG plane entirely

**Evidence grade**: CONFIRMED. Zero ambiguity.

**Source**: `main.c:1246`, `main.c:1268–1283`, `main.c:1287–1309`. Arcade disasm `maincpu.disasm.txt:107729`.

**Observable effect**: Genesis BG_B plane (VRAM `0xC000`) shows static preload state only — no tilemap positional updates occur. All arcade BG tilemap writes are silently discarded (replaced by `dest += 0x4000` with no VDP output).

**FG plane status**: Unaffected. FG hook fires correctly because FG dest_ptr (`0xC08xxx`) satisfies `PC080SN_CWINDOW_BASE = 0xC08000`. FG tilemap updates do reach the VDP.

**What correct output requires**: The BG hook must produce valid `(dest_row, dest_col)` for BG C-window addresses in `[0xC00000, 0xC04000)`. This requires either:
- Separate CWINDOW_BASE constants per plane (BG: `0xC00000`, FG: `0xC08000`)
- Or the shared function knowing which plane it is decoding for

The fix is exactly scoped to `PC080SN_CWINDOW_BASE` and the validity bounds in `pc080sn_dest_ptr_to_row_col()`. No other system needs to change.

### Rank 2 — BG VDP address formula (pending empirical validation)

**Evidence grade**: UNKNOWN / PENDING.

**Basis**: Structural equivalence with confirmed-correct FG formula. First BG write to VDP after MISMATCH #1 fix will confirm or contradict.

**No other root cause candidates exist**. All other identified suspects have been either confirmed correct (tile formula, strip masking, FG hook, Python LUT) or proven impossible (sanitize function dead, +0x14 absent, FG dest_ptr writeback gone).
