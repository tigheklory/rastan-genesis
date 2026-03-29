# System-Wide Sprite Visibility Bring-Up Plan

## 1. Purpose

The assembly commit path (`genesistan_sprite_commit_asm`) is active and fires every vblank.
VDP VRAM at 0xF800 is nonzero — Block-A coordinates are reaching the SAT correctly. Sprites
are not visible. This plan identifies the root cause and defines the one implementation slice
that will produce visible pixels for the full Block-A stream.

---

## 2. Chosen Bring-Up Slice (Option A — tile visibility bring-up)

**Choice: Option A — write a known solid-color tile pattern to a fixed VRAM address and
override all SAT tile indices to point to that address.**

### Why not Option B (palette bring-up)?

PAL0 in CRAM is already nonzero and visible. `restore_launcher_vdp_state()` is called at
launch (main.c line 1764) before `frontend_live_handoff_active = TRUE` is set. It loads
`rastan_active_dip_palette` into PAL0: entry 0 = 0x0000 (transparent), entries 1–15 =
0x0EE0 (bright yellow-green). The assembly commit uses `ori.w #0x8000` which sets priority
bit only; palette select bits remain 00, so all sprite SAT entries reference PAL0. PAL0 has
visible colors. Palette is not the blocker.

### Why Option A?

`genesistan_render_sprites_vdp()` — now dead code from the vblank path — contained the only
tile upload path: `VDP_loadTileData(frontend_runtime_sprite_tile_buffer, FRONTEND_RUNTIME_SPRITE_TILE_BASE, unique_count * 4, DMA)`. That path no longer fires. The assembly commit uses
`addi.w #0x0400, %d1` as a hardcoded tile base, targeting VRAM tile index 0x07CA (and
neighbors) for Block-A entries. Those VRAM tile slots contain no valid tile data — they hold
whatever residual or garbage state was left from the last C helper execution. No sprite tile
upload happens in the live vblank path today.

The root cause is **missing tile data in VRAM** at the indices referenced by the SAT entries
the assembly commit writes.

### Minimal fix for Option A

Write a known solid-color 8x8 tile pattern (32 bytes, all pixels index 1 of PAL0 = 0x0EE0)
to VRAM tile index 1 (a safe non-system tile slot). Override the tile index written to all
SAT entries in `genesistan_sprite_commit_asm` to tile 1 for this bring-up slice only. All
SAT entries in the Block-A stream will then reference the same known-populated tile and render
as solid 16x16 blocks at their correct screen positions.

---

## 3. Why This Slice Is Next

SAT positions are correct: y=0x00E8+0x80=0x0168 (~y=232 screen), x=0x0010+0x80=0x0090
(~x=16 screen). The VDP will scan those SAT entries every frame and attempt to render sprites
at those coordinates. With no valid tile data at the referenced VRAM index, the VDP renders
nothing (or garbage if the slot holds residual data from a prior build).

Fixing palette now has no impact: PAL0 is already loaded with visible colors (0x0EE0,
yellow-green) at entries 1–15. Any single pixel at palette index 1–15 from PAL0 will be
bright and visible.

Fixing tiles is the only remaining gate: put any nonzero pattern at tile 1, point all SAT
tile_attr fields at tile 1, and the sprites will appear as solid colored blocks at the
coordinates Block-A already provides. This is a one-step proof that the full pipeline
(Block-A → assembly SAT commit → VDP → visible pixel) is operational end to end.

---

## 4. System-Wide Behavior Rule

All sprite SAT entries built from the Block-A stream will reference VRAM tile index 1 (a
known solid-color test tile loaded at startup). The tile index override applies to all 18
Block-A entries (0xE0FF11FE) processed by `genesistan_sprite_commit_asm` on every vblank.
No entry-specific exception. No logo-specific or entry-0-specific path.

The solid-color tile is loaded once at title screen initialization (in or immediately after
`genesistan_sync_title_vdp_layout`) via a 32-byte CPU write to VDP VRAM tile slot 1.

---

## 5. Implementation Boundary

### Files that GAIN responsibility

**`apps/rastan/src/main.c`** — in or immediately after `genesistan_sync_title_vdp_layout()`:

- Add a 32-byte CPU write to VDP VRAM tile slot 1 (VRAM address 0x0020 = tile 1 * 32 bytes):
  write a pattern of 0x1111 repeated (all pixels = palette index 1 = bright yellow-green from
  PAL0). This is a one-time init write, not a per-frame write.
- Location: called from the same launch path that calls `genesistan_sync_title_vdp_layout()`
  at line 1773.

**`apps/rastan/src/startup_trampoline.s`** — in `genesistan_sprite_commit_asm`:

- Replace the current tile index computation:
  `andi.w #0x3FFF, %d1` / `addi.w #0x0400, %d1` / `ori.w #0x8000, %d1`
  with a hardcoded load of tile index 1 with priority:
  `move.w #0x8001, %d1`
  This applies to every entry in the Block-A loop — no conditional, no per-entry branch.

### Files that LOSE responsibility

None. No files are demoted or disabled in this slice.

### Files left UNTOUCHED

- All `specs/` JSON patch files — no opcode_replace or shift_replacement changes
- Block-A producer at genesis 0x05A2B4 — unchanged
- Block-A WRAM locations (0xE0FF11FE, 0xE0FF01BC) — unchanged
- Exception handlers (`z_qr_exception.c`, `z_qr_exception_handlers.s`) — unchanged
- `startup_bridge.c` — unchanged
- SGDK initialization, `genesistan_sync_title_vdp_layout` structure — unchanged
- Tilemap / scroll code — unchanged
- Palette / CRAM — unchanged (PAL0 already has visible colors from launcher state)
- `genesistan_render_sprites_vdp()` body in `main.c` — remains dead code, not removed

---

## 6. Success Criteria (system-wide, numbered)

These criteria apply to the full Block-A stream, not to any individual entry or sprite.

1. At least 3 sprites from the live Block-A stream have visible solid-color pixels on screen
   simultaneously — confirmed by visual inspection or frame capture at frame 700.

2. VDP VRAM tile slot 1 (address 0x0020) contains nonzero pattern bytes — confirmed by VDP
   VRAM read: `vdp.spaces['videoram']:read_u16(0x0020)` returns nonzero (expect 0x1111).

3. All SAT entries at 0xF800 that originate from Block-A have tile_attr field == 0x8001 —
   confirmed by reading the SAT region: `vdp.spaces['videoram']:read_u16(0xF804)` for the
   third word of each 8-byte entry should equal 0x8001 for all non-sentinel entries.

4. `genesistan_sprite_commit_asm` fires every vblank and processes all 18 Block-A entries —
   confirmed by existing probe: assembly commit hit count equals arcade tick count (~791 hits
   per 791-vblank run).

---

## 7. Out-of-Scope Items

- Title-logo-specific handling — no per-entry special cases
- Entry-0-specific handling — rule applies to all entries equally
- Full PC080SN tilemap conversion
- Final arcade palette correctness — PAL0 test palette is retained; no arcade CRAM translation
- Final tile residency / cache design — `frontend_runtime_tile_for_code`, tile LRU cache, and
  tile DMA pipeline are not touched in this slice
- Full sprite size decoding — size remains hardcoded 0x0500 (2x2)
- Flipscreen fidelity — no flipscreen transform in this slice
- Animation correctness — tile cycling deferred; all entries use tile 1 for this slice
- Sprite link chain correctness — sequential link remains
- ROM/spec patch changes — no JSON spec file changes
- Block-B entries (0xE0FF01BC, 4 entries) — the current assembly only processes Block-A;
  Block-B extension is deferred
- `load_arcade_palette()` integration — not called in this slice
- `refresh_frontend_sprite_palettes()` — not called in this slice
- Gameplay state sprite pipeline (states 2–4) — title state only

---

## 8. Final Recommendation

Tile data is the only remaining gate to visible sprite pixels. PAL0 already contains visible
colors (0x0EE0 at entries 1–15) from the launcher palette loaded at `restore_launcher_vdp_state()`. The assembly commit runs correctly and writes real coordinates to the SAT every vblank.
The only missing piece is nonzero tile data at the VRAM index all SAT entries reference.

Write tile 1 once at startup, override all SAT tile_attr fields to 0x8001 in the assembly
loop, and all Block-A entries that pass the sentinel check will render as solid yellow-green
blocks at their correct on-screen positions. This is the cheapest possible confirmation that
the full pipeline is live and system-wide.

The next step is a system-wide sprite visibility bring-up slice that applies to the full current Block-A stream, not to any single sprite instance.
