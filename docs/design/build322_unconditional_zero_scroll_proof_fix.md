# Build 322 — Unconditional Zero-Scroll Proof Fix

## 1. Executive Summary

Build 322 removes the Build 321 mode gate from `genesistan_scroll_commit_vdp()` and forces all four VDP scroll values (HScroll A, HScroll B, VScroll A, VScroll B) to zero unconditionally every frame. This eliminates scroll as a variable so we can determine whether the remaining on-screen motion is caused by scroll writes. Gameplay scroll is intentionally broken for this diagnostic build.

## 2. Prior Confirmed Scroll Write Path Finding

Per `docs/design/build321_title_attract_scroll_freeze_proof_fix.md` and subsequent investigation:

- Only one VDP scroll writer exists: `genesistan_scroll_commit_vdp()` in `apps/rastan/src/main.c`
- Exhaustive grep confirmed no assembly scroll write path to VDP HScroll or VSRAM
- 10 arcade scroll hooks all route through `genesistan_scroll_from_workram_vdp()`, which stages to WRAM only
- Build 321's mode gate (`workram_words[2] < 2`) failed because the attract-mode demo simulates gameplay, advancing `inner_step` to >= 2
- Text still moved on screen with the Build 321 conditional freeze active

## 3. Exact Code Change

**File**: `apps/rastan/src/main.c`, function `genesistan_scroll_commit_vdp()`

**Before (Build 321)**: Mode-gated scroll freeze using `workram_words[2] < 2`. Wrote staged values during gameplay, zero during title/attract.

**After (Build 322)**: Unconditional zero write. No mode variable read. No staged value reference in the commit path.

```c
void genesistan_scroll_commit_vdp(void)
{
    vu16 *const ctrl = (vu16 *)0xC00004;
    vu32 *const ctrl32 = (vu32 *)0xC00004;
    vu16 *const data = (vu16 *)0xC00000;

    *ctrl = 0x8F02;

    /* HScroll: VRAM 0xF000 — both planes zero */
    *ctrl32 = 0x70000003;
    *data = 0;
    *data = 0;

    /* VScroll: VSRAM offset 0 — both planes zero */
    *ctrl32 = 0x40000010;
    *data = 0;
    *data = 0;
}
```

Removed: `inner_step` variable, `title_attract` variable, all ternary expressions.

## 4. Why This Proof Fix Is Unconditional

Build 321 proved that a conditional gate based on `workram_words[2]` (inner step) does not cover all attract-mode phases. The attract-mode demo simulates gameplay, which advances the inner step value to >= 2, defeating the `< 2` condition.

Rather than search for the correct mode variable, this build eliminates the variable entirely. If text stops moving with unconditional zero scroll, the cause is confirmed as scroll. If text still moves, scroll is excluded and the cause is something else (e.g., nametable content changing, DMA, or a scroll path not yet identified).

## 5. Preserved Upstream Staging Behavior

The following are NOT modified:

| Component | Status |
|-----------|--------|
| `genesistan_scroll_from_workram_vdp()` | Unchanged — still reads workram, stages to WRAM |
| `staged_scroll_x_fg`, `staged_scroll_y_fg` | Unchanged — still written by staging function |
| `staged_scroll_x_bg`, `staged_scroll_y_bg` | Unchanged — still written by staging function |
| 10 scroll hook replacements in startup_title_remap.json | Unchanged |
| Workram offsets 0x10AE, 0x10B0, 0x10EC, 0x10EE | Still read by staging function |

The staged values are computed but never committed to VDP. This preserves the full scroll pipeline for easy restoration once the proof is complete.

## 6. Explicit Non-Goals (No Debug Overlay / No State Display)

This build does NOT include:

- Debug hex display of arcade state machine values
- On-screen text overlay of any kind
- Any new nametable buffer writes
- Any new VDP register changes beyond the existing scroll commit

The debug state display is a separate task for a future build.

## 7. Build 322 Verification

### Structural
- Build succeeded: **YES**
- ROM: `dist/Rastan_322.bin` (3,932,160 bytes)
- Exceptions introduced: **NO** (same 5 pre-existing unused-function warnings as prior builds)

### Scroll-proof behavior
- Final VDP scroll forced to zero unconditionally: **YES**
- Any mode gate used: **NO**
- Staged scroll path left intact upstream: **YES**
- Debug overlay/state display added: **NO**

## 8. Visual Verification Status

**USER MUST VERIFY.** Expected behavior:
- If scroll was the cause: all on-screen text/content should now be stationary
- If scroll was NOT the cause: content may still move (indicating a different mechanism)
- Screen still mostly black (nametable content issue unchanged)

## 9. Crash Verification Status

**USER MUST VERIFY.** The change simplifies the scroll commit (fewer reads, no conditionals). No new VDP register changes, no new memory access patterns.

## 10. Final Verdict

Unconditional proof fix. All VDP scroll forced to zero every frame with no conditions. If visible content becomes stationary, scroll is confirmed as the motion cause. If content still moves, a different mechanism is responsible and further investigation is needed.
