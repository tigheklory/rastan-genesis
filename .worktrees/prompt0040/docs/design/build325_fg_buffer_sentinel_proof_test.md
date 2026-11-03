# Build 325 — FG Buffer Sentinel Proof Test

## 1. Executive Summary

Build 325 adds a single temporary sentinel write (`move.w #0xFFFF, pc080sn_fg_buffer`) before `genesistan_run_arcade_tick_lean` in `_VINT_arcade_mode`. This writes 0xFFFF to FG buffer cell (x=0, y=0) every frame before the arcade tick runs. If the value survives to the plane commit, the arcade tick does NOT wipe the FG buffer — and the empty Plane A problem is purely a failure of attract-mode hooks to produce content. If the value is gone after the tick, the arcade tick is overwriting the buffer.

## 2. Prior Confirmed No-SGDK-Interference Finding

Per `docs/design/build323_full_vblank_dispatch_sgdk_influence_audit.md`:

- `arcade_vblank_active` gate completely bypasses SGDK VBlank processing
- Only 4 custom functions write to VDP in arcade VBlank
- No competing VDP writers, no SGDK interference
- The empty Plane A problem is internal to the arcade tick pipeline

## 3. Exact Sentinel Write Added

**File**: `apps/rastan/src/boot/sega.s`, `_VINT_arcade_mode` (after display-OFF write, before arcade tick)

**Instruction added**:
```asm
move.w  #0xFFFF, pc080sn_fg_buffer
```

**Location in VBlank sequence**:
```
move.w  #0x8134, 0x00C00004     /* display OFF */
move.w  #0xFFFF, pc080sn_fg_buffer   ← SENTINEL HERE
jsr     genesistan_run_arcade_tick_lean
jsr     sanitize_arcade_workram
jsr     genesistan_pc080sn_commit_planes  ← sentinel either survives or doesn't
```

**Sentinel details**:

| Property | Value |
|----------|-------|
| Sentinel value | `0xFFFF` |
| Meaning as nametable word | priority=1, palette=3, vflip=1, hflip=1, tile=0x7FF |
| FG buffer index | 0 |
| FG buffer byte offset | 0 |
| Screen position | x=0, y=0 (top-left cell of Plane A) |

## 4. Why This Is a Proof Test Only

Two hypotheses for the empty Plane A:

1. **Arcade tick wipes the FG buffer** — some code inside `genesistan_run_arcade_tick_lean` clears or overwrites the buffer with zeros before the commit
2. **No attract-mode writer produces content** — the buffer starts empty and nothing writes non-zero values during attract mode

The sentinel distinguishes between them:
- If `pc080sn_fg_buffer[0]` == 0xFFFF in the plane viewer → hypothesis 2 (buffer not wiped; content simply never written)
- If `pc080sn_fg_buffer[0]` == 0x0000 in the plane viewer → hypothesis 1 (arcade tick wiped the buffer)

## 5. Non-Goals (No Other FG Writer Changes)

| Component | Changed? |
|-----------|----------|
| `sega.s` sentinel write | YES (this build) |
| `rastan_draw_tile_xy()` | NO |
| `text_writer_ptr_to_xy()` | NO |
| Text writer hooks | NO |
| `genesistan_bulk_tilemap_commit` | NO |
| `genesistan_pc080sn_commit_planes` | NO |
| Any other function | NO |

The visibility filter disable (Build 324) is still present in `text_writer_ptr_to_xy()`.

## 6. Build 325 Verification

### Structural
- Build succeeded: **YES**
- ROM: `dist/Rastan_325.bin` (3,932,160 bytes)
- Exceptions introduced: **NO** (same 5 pre-existing warnings)

### Sentinel behavior
- Sentinel value: **0xFFFF**
- FG buffer index: **0**
- Screen position: **(x=0, y=0)**
- Write placed before arcade tick: **YES**
- No other FG writer changed: **YES**

## 7. Visual Verification Status

**USER MUST VERIFY.** In Plane A viewer (VRAM 0xE000):
- If top-left cell (x=0, y=0) shows any non-zero nametable entry → sentinel survived → arcade tick does NOT wipe FG buffer
- If top-left cell is zero/empty → sentinel was overwritten → arcade tick wipes the buffer

## 8. Crash Verification Status

**USER MUST VERIFY.** A single `move.w` to a BSS buffer before the arcade tick is architecturally safe. No new memory access patterns.

## 9. Final Verdict

Sentinel proof test. Single write to FG buffer[0] = 0xFFFF before every arcade tick. User observes Plane A viewer to determine which hypothesis is correct.
