# First Real Graphics Replacement Slice

## 1. Purpose

This document defines the single, concrete, first real migration slice that begins replacing
the temporary C helper renderer (`genesistan_render_sprites_vdp`) with an arcade-vblank-owned
graphics commit path. It is grounded in all prior design docs (Phase 1 per-vblank results,
opcode migration plan, SAT publish failure diagnosis) and validated against Rainbow Islands and
Cadash arcade-to-Genesis translation patterns.

This slice is Phase 2 of the opcode_vblank_sprite_migration_plan: split SAT DMA publish out
of the C helper into a dedicated vblank-owned commit function.

---

## 2. Current Helper Responsibility Split

The following table classifies every responsibility bucket of `genesistan_render_sprites_vdp`
(main.c lines 1538–1657), based on the architecture plan and migration plan.

| # | Bucket | Current Location | Classification |
|---|--------|-----------------|----------------|
| 1 | Block-A / Block-B descriptor scan | Lines 1572–1636: iterates `sprite_blocks[]`, reads 8 bytes per entry from WRAM offset 0x11B2 (18 entries) and 0x0170 (4 entries) | KEEP TEMPORARILY — scan loop is in the right place; moves to vblank commit in Phase 3 |
| 2 | Validity filtering | Lines 1594–1617: all-zero tuple guard, 0x0180 off-screen sentinel, tile_base < 0 skip, out-of-bounds bounds check | KEEP TEMPORARILY — correct filtering; migrates with scan in Phase 3 |
| 3 | Coordinate conversion | Lines 1596–1617: 9-bit sign-extend on x and y; SGDK `VDP_setSpriteFull` adds +128 internally | KEEP TEMPORARILY — will move with formation in Phase 3 |
| 4 | Flipscreen handling | Lines 1606–1612: reads `workram_words[15]`, transforms x/y and inverts flipx/flipy | KEEP TEMPORARILY — migrates with scan/formation in Phase 3 |
| 5 | Tile lookup / tile residency | Lines 1589, 1638–1649: `frontend_runtime_tile_for_code`; on miss, DMA tile into `frontend_runtime_sprite_tile_buffer` → VRAM | KEEP TEMPORARILY — Phase 1–2; MOVE TO OPCODE/ROM-SIDE in Phase 3 |
| 6 | SAT entry formation | Lines 1619–1623: `TILE_ATTR_FULL` + `VDP_setSpriteFull` writes to `vdpSpriteCache` | KEEP TEMPORARILY — will move to vblank commit in Phase 3 |
| 7 | SAT publish / DMA | Lines 1651–1655: `SYS_disableInts` + `refresh_frontend_sprite_palettes` + `VDP_updateSprites(sprite_count, DMA)` + `VDP_waitDMACompletion` + `SYS_enableInts` | **MOVE NOW** — Phase 2 target: extract DMA commit to `genesistan_vblank_sprite_commit()` |
| 8 | Palette interactions | Lines 1652: `refresh_frontend_sprite_palettes(palette_bank_map, palette_bank_count)` | DEFER TO LATER PHASE — palette system has its own phase; stays in helper until palette architecture finalized |

### Classification Notes

Bucket 7 (SAT publish / DMA) is the MOVE NOW target for this slice. It is the only bucket
changing hands. All other buckets stay in the helper temporarily and migrate in Phase 3.

The `refresh_frontend_sprite_palettes` call (bucket 8) lives inside the same `SYS_disableInts`
block as the DMA commit (lines 1651–1655). When the DMA commit moves out, palette refresh
stays in the helper. The palette call must remain in the helper body before the DMA call is
removed; the split preserves that ordering.

---

## 3. Chosen First Real Replacement Slice

**SINGLE CHOSEN SLICE: Extract `VDP_updateSprites(sprite_count, DMA)` + `VDP_waitDMACompletion()`
from `genesistan_render_sprites_vdp()` into a new function `genesistan_vblank_sprite_commit()`,
called unconditionally from `genesistan_frontend_live_vint_handoff()` after the helper.**

This is Phase 2 from the opcode_vblank_sprite_migration_plan, exactly as defined there.

### Justification

1. **Architecturally critical split**: The "data preparation" (scan, filter, formation, fill
   `vdpSpriteCache`) is decoupled from the "hardware commit" (DMA to VRAM). This is the core
   architectural boundary: producers populate a staging buffer; vblank commits it to hardware.
   The C helper retains the staging role temporarily; the commit role immediately moves to
   the correct owner.

2. **No dependency on unfinished systems**: This slice does not require a tile system redesign,
   a palette system overhaul, or any ROM patch changes. The same `vdpSpriteCache` that the
   helper fills is the input to the commit function.

3. **DMA timing correctness**: Once the DMA commit is in a dedicated vblank-owned function
   called from `genesistan_frontend_live_vint_handoff`, the commit fires at a controlled
   point after the arcade tick completes — not at whatever point inside the helper it happened
   to reach. The ordering is explicit and testable.

4. **Enables suppression of double-call**: Phase 2 migration plan identifies that the
   redundant arcade dispatch at 0x03AAF2 can be suppressed after the vblank-owned commit
   is in place. That suppression is a follow-on action, not part of this slice.

5. **Mirrors Rainbow Islands and Cadash patterns**: Both comparison cases confirm that
   SAT/sprite commit happens in an interrupt-owned frame context, after producers have
   staged data into WRAM buffers. This slice aligns Rastan with that confirmed pattern.

**No other slice is proposed. This is the only first slice.**

---

## 4. Implementation Boundary

### What Cody WILL modify

**File: `apps/rastan/src/main.c`**

Action 1 — Extract DMA commit from helper body:
- Remove the `VDP_updateSprites(sprite_count, DMA)` and `VDP_waitDMACompletion()` calls
  from inside `genesistan_render_sprites_vdp()` (currently at lines 1653–1654, inside the
  `SYS_disableInts` block at lines 1651–1655).
- The `SYS_disableInts` / `SYS_enableInts` bracket around the removed calls collapses;
  `refresh_frontend_sprite_palettes` still runs inside its own interrupt-safe context.
- The helper still fills `vdpSpriteCache` and sets `sprite_count` via the existing scan loop.
  The helper return does NOT publish to VDP.

Action 2 — Expose `sprite_count` to commit function:
- Promote `sprite_count` from local variable in `genesistan_render_sprites_vdp()` to a
  file-scope `static u16` (e.g., `static u16 genesistan_vblank_sprite_count = 0`), OR pass
  it via a dedicated accessor. The commit function must read the count that was set by the
  last helper invocation. The simplest approach is a static file-scope variable written by
  the helper and read by the commit function.

Action 3 — Add `genesistan_vblank_sprite_commit()`:
- New function, defined in `main.c`, within the `#if RASTAN_ENABLE_STARTUP_HOOK` guard.
- Body: `SYS_disableInts(); VDP_updateSprites(genesistan_vblank_sprite_count, DMA); VDP_waitDMACompletion(); SYS_enableInts();`
- This function owns DMA commit. It reads the staging count set by the helper. It writes
  to VDP VRAM at 0xF800 (the SAT table).
- Forward declaration added near existing `genesistan_render_sprites_vdp` forward declaration
  (around line 1463).

Action 4 — Insert call in vint_handoff:
- In `genesistan_frontend_live_vint_handoff()` (currently at line 1881), after the existing
  `genesistan_render_sprites_vdp()` call, add `genesistan_vblank_sprite_commit()`.
- The helper call populates `vdpSpriteCache` and sets the count. The commit call DMAs it.
- Both calls remain inside the `#if RASTAN_ENABLE_STARTUP_HOOK` guard.

### What Cody will NOT modify

- The Block-A scan loop and all validity filtering logic inside `genesistan_render_sprites_vdp`
- `VDP_setSpriteFull` call inside the helper (SAT entry formation stays in helper)
- `VDP_loadTileData` / tile DMA path inside the helper (tile cache stays in helper)
- `refresh_frontend_sprite_palettes` call inside the helper (palette stays in helper)
- ROM/spec patch files (`specs/startup_title_remap.json` or equivalent)
- WRAM buffer locations (Block-A at 0xE0FF11FE stays, `vdpSpriteCache` at 0xE0FF6DF0 stays)
- Tilemap, palette, or scroll code
- Exception handlers (`z_qr_exception.c`, `z_qr_exception_handlers.s`)
- SGDK initialization or VDP layout setup (`genesistan_sync_title_vdp_layout` untouched)
- The arcade dispatch path at 0x03AAF2 (double-call suppression is Phase 2 follow-on, not this slice)
- `startup_bridge.c`
- Any assembly trampoline files

### What the new function owns

- **Inputs**: `genesistan_vblank_sprite_count` (static count set by helper scan), `vdpSpriteCache`
  (already filled by `VDP_setSpriteFull` calls in the helper)
- **Outputs**: VDP VRAM at 0xF800 (SAT table) — populated via DMA
- **Mechanism**: `VDP_updateSprites(genesistan_vblank_sprite_count, DMA)` + `VDP_waitDMACompletion()`
  inside `SYS_disableInts` / `SYS_enableInts`

### What the helper loses

- The `VDP_updateSprites(sprite_count, DMA)` call is removed from `genesistan_render_sprites_vdp()`
- `VDP_waitDMACompletion()` (the one paired with VDP_updateSprites) is removed from the helper
- The helper still fills `vdpSpriteCache` but no longer publishes it to VDP

---

## 5. Arcade VBlank Owned Flow After Slice

The frame execution sequence after this slice is implemented:

```
genesistan_frontend_live_vint_handoff():
  Guard: frontend_live_handoff_active == TRUE AND current_screen == SCREEN_FRONTEND_LIVE

  1. genesistan_refresh_arcade_inputs()
     → updates input shadow for arcade polling

  2. genesistan_run_original_frontend_tick()
     → runs arcade level-5 handler natively at 0x03A208
     → includes Block-A producer at 0x03AAEC (fills 0xE0FF11FE)
     → includes renderer bridge at 0x03AAF2 (TEMPORARY — double-call, suppressed in Phase 2 follow-on)
     → returns after arcade RTE

  3. genesistan_render_sprites_vdp()
     → reads Block-A descriptor blocks (0xE0FF11FE, 0xE0FF01BC)
     → applies validity filters, tile lookup, coordinate conversion
     → calls VDP_setSpriteFull() per entry → fills vdpSpriteCache
     → loads tile data via VDP_loadTileData DMA if unique_count > 0
     → calls refresh_frontend_sprite_palettes()
     → writes genesistan_vblank_sprite_count = sprite_count
     → DOES NOT call VDP_updateSprites (removed from this function)

  4. genesistan_vblank_sprite_commit()         ← NEW: vblank-owned DMA commit
     → SYS_disableInts()
     → VDP_updateSprites(genesistan_vblank_sprite_count, DMA)
     → VDP_waitDMACompletion()
     → SYS_enableInts()
     → output: VDP VRAM 0xF800 populated with SAT entries

  return
```

### Inputs at step 4

- `vdpSpriteCache` (at WRAM 0xE0FF6DF0): filled by step 3 via `VDP_setSpriteFull` calls
- `genesistan_vblank_sprite_count`: set by step 3 at end of helper scan loop

### Outputs of step 4

- VDP VRAM 0xF800: contains valid SAT entries for all sprites formed in step 3

### Old helper behavior superseded

- `VDP_updateSprites(sprite_count, DMA)` no longer called from inside `genesistan_render_sprites_vdp()`
- SAT DMA timing is now determined by the vblank-owned commit point, not by wherever the helper exits

---

## 6. Success Criteria

All criteria are measurable by probe or static check:

1. **`genesistan_vblank_sprite_commit()` is called every vblank**: Probe tap at the commit
   function entry address shows hit count equal to the arcade tick hit count (expect ~791 hits
   in a 791-vblank run). Pass: `HIT genesistan_vblank_sprite_commit == HIT 03A208`.

2. **`VDP_updateSprites` no longer called from inside `genesistan_render_sprites_vdp`**:
   Static code check — search `main.c` for `VDP_updateSprites` callsites; the only callsite
   must be inside `genesistan_vblank_sprite_commit`, not inside `genesistan_render_sprites_vdp`.

3. **VDP VRAM at 0xF800 contains nonzero SAT entries each frame**: MAME probe — direct VDP
   read-port tap confirms `frame700_vdp_port_read_f800 != 0000 0000 0000 0000`. Expected
   value based on prior runs: `0168 0501 8400 0090` (Y=0x0168 for logo sprite).

4. **SAT DMA fires from the vblank-owned commit point**: DMA probe confirms `sat_dma_cmd_post_launch`
   count is sustained and that the DMA command fires after step 3 completes (not from an
   earlier point in the arcade tick dispatch).

5. **No regression from per-vblank call baseline (build 279)**: Visual output at frame 700
   is not worse than build 279. CREDIT text still visible. SAT staging nonzero (`sat_cache_nonzero_entries >= 19`).

---

## 7. Out-of-Scope Items

Cody MUST NOT touch any of the following in this slice:

- Full PC080SN tilemap conversion (plane A / plane B nametable DMA pipeline)
- Final palette correctness (palette system, dirty-flag DMA, CLCS capture)
- Full sprite size decoding (size field stays fixed at SPRITE_SIZE(2,2) for now)
- Scroll system (VSRAM updates, `genesistan_scroll_from_workram_vdp`)
- Final flipscreen fidelity (flipscreen path stays in helper, not validated here)
- Tile upload / cache redesign (tile loading stays in helper, `frontend_runtime_tile_for_code` untouched)
- Sprite link chain correctness (link field stays as sequential count-based chain)
- Animation frame cycling (Block-A builder and animation state untouched)
- Block-A scan / SAT formation logic (those stay in helper until Phase 3)
- ROM/spec patch changes (`specs/startup_title_remap.json`, any `.json` spec files)
- Suppression of redundant 0x03AAF2 arcade dispatch (that is Phase 2 follow-on, not this slice)
- Gameplay state sprite pipeline (states 2–4; title state only)
- Any exception handler code
- `startup_bridge.c` or any assembly trampoline

---

## 8. Rainbow Islands / Cadash Sanity Check

Both Rainbow Islands and Cadash Genesis translations confirm that SAT commit happens inside
interrupt-owned frame timing, not from main-loop or producer-side code: Rainbow Islands stages
sprite descriptors into WRAM buffers (around `0xFFFB00`) and then uploads them via VDP DMA
paths, while Cadash stages descriptors and commits via scripted VDP port sequences — both
operating within an interrupt or vblank-synchronized context, not from wherever the producer
happened to finish. Both translations maintain strict producer-to-staging-to-commit separation:
producers write to WRAM, a separate commit step (driven by the interrupt frame) transfers
staging to VDP hardware. The chosen slice — separating `vdpSpriteCache` formation (which stays
in the helper temporarily) from `VDP_updateSprites` DMA commit (which moves to the new
vblank-owned function) — directly replicates this confirmed pattern: the helper is the staging
writer, `genesistan_vblank_sprite_commit` is the interrupt-owned hardware commit, matching the
architecture both Taito translations demonstrate.

---

## 9. Final Recommendation

Phase 2 is the correct next slice. It is the smallest change that establishes the correct
architectural ownership boundary: vblank owns hardware commit; the helper owns staging. The
helper loses exactly one responsibility (DMA commit), gains exactly one (writing a shared
count variable), and the new function carries exactly one responsibility (DMA to VDP). No
new systems, no new ROM patches, no assembly changes. The implementation touches only `main.c`
and is fully reversible if a regression appears.

After this slice is validated, the follow-on action is suppressing the redundant 0x03AAF2
arcade dispatch to eliminate the double-call artifact. Phase 3 then moves the scan and
formation logic out of the helper entirely. Phase 4 retires the helper.

The next implementation step begins replacing the temporary C helper with an arcade-vblank-owned graphics path, using a single tightly scoped migration slice.
