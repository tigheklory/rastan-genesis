# First Non-C Graphics Migration Slice

## 1. Purpose

This document defines the first migration slice that moves a real graphics responsibility out
of the temporary C helper (`genesistan_render_sprites_vdp`) and into an assembly-owned,
non-C path. It is Phase 3 of the opcode_vblank_sprite_migration_plan: the moment the C helper
ceases to own SAT formation and VDP writes, replaced by a new assembly routine that reads
Block-A WRAM directly and writes SAT entries directly to the VDP data port.

Context: Phase 1 (unconditional vblank call) and Phase 2 (DMA split into
`genesistan_vblank_sprite_commit`) are both DONE. The C helper still owns everything except
the final DMA commit step. This slice takes the scan, coordinate conversion, and direct VDP
write out of C and into assembly, bypassing `vdpSpriteCache` and `VDP_setSpriteFull` entirely.

---

## 2. Chosen First Non-C Slice

**Option A: New assembly routine `genesistan_sprite_commit_asm` that reads Block-A WRAM
descriptors directly and writes SAT entries directly to the VDP data port.**

### Exact definition

A new assembly routine is added to `startup_trampoline.s` (or a new `.s` file in
`apps/rastan/src/`). The routine:

1. Reads sprite count from a WRAM variable set by the C-side Block-A scan (or computes it
   by scanning for the all-zero sentinel at 0xE0FF11FE).
2. Loops over Block-A entries at 0xE0FF11FE (18 entries) and 0xE0FF01BC (4 entries).
3. Converts each entry to Genesis SAT format in 68000 assembly arithmetic:
   - `SAT.Y = word1 + 0x80` (y_raw + 128, direct add — no C function involved)
   - `SAT.tile_attr = (tile_base_constant) | (word2 & 0x3FFF)` (tile index stubbed to fixed
     VRAM base + arcade tile code, temporarily; hardcoded palette 0, priority 1)
   - `SAT.X = word3 + 0x80` (x_raw + 128)
   - `SAT.size_link = 0x0500 | link` (2×2 hardcoded size + link = next entry)
4. Writes each 8-byte SAT entry directly to the VDP data port at 0xC00000 after setting the
   VDP write address to VRAM 0xF800 via the VDP control port at 0xC00004.
5. Skips all-zero entries (the 4-word all-zero sentinel check, matching the existing C guard).
6. Skips entries with y_raw == 0x0180 (off-screen sentinel).

This routine is called from `genesistan_frontend_live_vint_handoff()` in place of
`genesistan_render_sprites_vdp()`. The C helper is no longer called from the vblank path.

### Justification for Option A over B and C

Option A is chosen because:

- It is **genuinely non-C**: 68000 assembly reads WRAM, writes VDP — no C function, no SGDK
  sprite API, no `vdpSpriteCache` involvement for SAT commit.
- It uses the **already-proven WRAM structure** (Block-A at 0xE0FF11FE, confirmed correct since
  Phase 2, entry0 = `0000 00E8 03CA 0010`). No new intermediate format is required.
- It **bypasses SGDK's vdpSpriteCache entirely** — `VDP_setSpriteFull` is not called, the
  cache is not touched for this path. This removes the SGDK staging dependency from the sprite
  commit path.
- It is **implementable now** without tile system redesign, palette system, or ROM patch
  changes. Tile lookup is stubbed (arcade tile N maps to VRAM tile N + fixed base), which is
  sufficient to prove the assembly path produces valid VDP SAT output.
- It is the **direct path to final architecture**: the eventual fully-opcode-replaced path will
  also read WRAM descriptors and write VDP SAT in non-C code. This slice is structurally
  identical to that final state, just with stubs for tile/palette/size.
- Option B (ROM-side hook extension) requires ROM patch changes and is higher scope.
- Option C (trampoline-based writer called from C) is only marginally different from the
  current state — the C helper still owns the scan. Option A fully removes the C helper from
  the hot path.

**Option A is the first non-C migration slice. Only one slice is defined here.**

---

## 3. Responsibility Shift

### Moves NOW to assembly

- **SAT formation**: Block-A WRAM word layout → Genesis SAT 4-word layout, in 68000 assembly
  arithmetic (add 0x80, mask tile code, OR size+link constant)
- **SAT direct VDP write**: assembly writes 4 words per sprite to VDP data port (0xC00000)
  after setting VRAM write address 0xF800 via VDP control port (0xC00004) — no SGDK involved
- **Coordinate conversion**: `y + 0x80` and `x + 0x80` done with `add.w #0x80, dn` in
  assembly — no C sign-extension helper, no `VDP_setSpriteFull` internal +128
- **Sentinel filtering**: all-zero tuple check and y==0x0180 check in assembly branch logic

### Stays temporary (still handled by existing code or not yet migrated)

- **Tile lookup / residency**: stubbed — assembly uses a hardcoded VRAM tile base constant
  (`FRONTEND_RUNTIME_SPRITE_TILE_BASE`) ORed with the tile code from word2; no cache miss
  resolution; tiles must already be present in VRAM from prior C helper runs or scene init
- **Palette selection**: hardcoded palette 0, priority 1 in assembly (`tile_attr |= 0x6000`
  style constant) — no `frontend_palette_line_for_bank` call
- **Sprite size**: hardcoded 2×2 (`0x0500` in SAT size+link word) — no size decoding
- **Flipscreen**: deferred — not implemented in the assembly routine in this slice
- **Link chain correctness**: sequential link (entry N links to entry N+1, last = 0) —
  correct for title-state sprite count

### Fully bypassed by the new assembly path

- `vdpSpriteCache` (SGDK's internal SAT staging buffer at 0xE0FF6DF0) — not written by this
  path; SAT goes directly to VDP VRAM via hardware DMA setup then CPU port writes, or via
  direct VDP write-command sequence
- `VDP_setSpriteFull()` — not called; assembly writes SAT words directly
- `VDP_updateSprites()` — not called; assembly writes SAT entries directly to VRAM
- `genesistan_vblank_sprite_commit()` — not called from the new hot path (can be left in
  place as dead code or removed as a follow-on)
- `genesistan_render_sprites_vdp()` — not called from the vblank handoff after this slice

---

## 4. Implementation Boundary

### Files that GAIN responsibility

**`apps/rastan/src/startup_trampoline.s`** (or new `apps/rastan/src/sprite_commit_asm.s`):

- New exported symbol: `genesistan_sprite_commit_asm`
- Declared `.globl genesistan_sprite_commit_asm`
- Entry: reads sprite count (scan Block-A for all-zero sentinel or use a shared WRAM count
  variable written by the C vblank path)
- Register setup: saves d0-d7/a0-a6 on stack (or at minimum d0-d3/a0-a1), restores on exit
- VDP address setup: writes VRAM write command for address 0xF800 to 0xC00004
  - Command word: `(0x4000 | ((0xF800 & 0x3FFF) << 2) | ((0xF800 >> 14) & 3))` pre-encoded
    as a 32-bit constant: `0x7800E000` (VRAM write to 0xF800, no auto-increment issues —
    or use SGDK-compatible write command encoding)
- Per-entry loop:
  - Load word1 (y_raw) from (a0) — check == 0x0180 → skip
  - Load word0 + word1 + word2 + word3 — check all-zero → skip
  - word2: AND with 0x3FFF, ADD tile_base_constant → tile index
  - Build tile_attr: `OR.W #0x6000, tile_index` (palette 0, priority 1, no flip — stubs)
  - Build Y: `ADD.W #0x80, y_raw` → SAT Y word
  - Build X: `ADD.W #0x80, x_raw` → SAT X word
  - Build size+link: `MOVE.W #0x0500, dn` then OR link index
  - Write 4 words to VDP data port (0xC00000): Y, size+link, tile_attr, X
  - Advance A0 by 8 bytes
  - Increment sprite counter; check against limit (22 or 80)
- After Block-A loop, run Block-B loop (4 entries at 0xE0FF01BC), same logic
- RTS

**`apps/rastan/src/main.c`**:

- Forward declaration added: `void genesistan_sprite_commit_asm(void);`
- In `genesistan_frontend_live_vint_handoff()`: replace the `genesistan_render_sprites_vdp()`
  call with `genesistan_sprite_commit_asm()` — single call substitution

### Files that LOSE responsibility

**`apps/rastan/src/main.c`**:

- `genesistan_render_sprites_vdp()` is **no longer called** from `genesistan_frontend_live_vint_handoff()` — it is removed from the vblank path
- `genesistan_render_sprites_vdp()` function body remains in the file as dead code initially
  (Phase 4 cleanup removes it entirely); it must not be called from the hot path
- `genesistan_vblank_sprite_commit()` is also no longer called from the vblank handoff (the
  assembly routine writes VDP directly; no separate DMA commit step needed)

### Files left UNTOUCHED

- All `specs/` JSON patch files — no opcode_replace or shift_replacement changes
- Tilemap, palette, scroll code in `main.c`
- Exception handlers (`z_qr_exception.c`, `z_qr_exception_handlers.s`)
- `startup_bridge.c`
- Block-A producer at genesis 0x05A2B4 — already working, unchanged
- Block-A WRAM locations (0xE0FF11FE stays, 0xE0FF01BC stays)
- SGDK initialization, VDP layout setup (`genesistan_sync_title_vdp_layout` untouched)
- The arcade dispatch path at 0x03AAF2 — not touched in this slice
- `vdpSpriteCache` symbol — left in WRAM, just not written by this path

---

## 5. New VBlank-Owned Flow

Ordered execution sequence after this slice is implemented:

```
genesistan_frontend_live_vint_handoff():
  Guard: frontend_live_handoff_active == TRUE AND current_screen == SCREEN_FRONTEND_LIVE

  1. genesistan_refresh_arcade_inputs()
     - updates input shadow for arcade input polling path

  2. genesistan_run_original_frontend_tick()
     - runs arcade level-5 handler natively at 0x03A208
     - includes Block-A producer at 0x03AAEC (fills 0xE0FF11FE — 18 entries)
     - includes renderer bridge at 0x03AAF2 (calls into dead C helper path -- present but
       no longer the authoritative sprite path; may be suppressed as Phase 2 follow-on)
     - returns after arcade RTE

  3. genesistan_sprite_commit_asm()          <- NEW: assembly reads Block-A -> writes SAT
     - sets VDP write address to VRAM 0xF800 via control port
     - iterates Block-A at 0xE0FF11FE (18 entries) and Block-B at 0xE0FF01BC (4 entries)
     - per entry: skip sentinel, convert coords (+0x80), stub tile+palette attr, write 4
       words to VDP data port (0xC00000)
     - output: VDP VRAM 0xF800 contains SAT entries from direct CPU writes
     - bypasses vdpSpriteCache, VDP_setSpriteFull, VDP_updateSprites entirely

  [genesistan_render_sprites_vdp() NOT CALLED from vblank handoff]
  [genesistan_vblank_sprite_commit() NOT CALLED from vblank handoff]

  return
```

### Inputs to step 3

- Block-A at 0xE0FF11FE: 18 × 8-byte entries, filled by producer in step 2
- Block-B at 0xE0FF01BC: 4 × 8-byte entries, filled by producer in step 2
- Tile base constant: `FRONTEND_RUNTIME_SPRITE_TILE_BASE` (compile-time constant from main.c,
  used as immediate in assembly tile-attr formation)

### Outputs of step 3

- VDP VRAM 0xF800: SAT table populated with up to 22 entries (18 Block-A + 4 Block-B) via
  direct CPU writes to VDP data port — no SGDK DMA path involved for this step

---

## 6. Success Criteria

All criteria are measurable by probe, static check, or direct VRAM inspection:

1. `genesistan_render_sprites_vdp()` is NOT called from `genesistan_frontend_live_vint_handoff()`
   — static code check: search `main.c` for the call site; it must not exist in the vblank
   handoff body after this slice.

2. `genesistan_sprite_commit_asm` IS called every vblank — MAME probe tap at the assembly
   routine entry address shows hit count equal to arcade tick hit count (expect ~791 hits in
   a 791-vblank run): `HIT genesistan_sprite_commit_asm == HIT 03A208`.

3. VDP VRAM 0xF800 contains nonzero SAT entries at frame 700 — direct VDP VRAM read via MAME
   `vdp.spaces['videoram']:read_u16(0xF800)` returns nonzero. Expected Y field for logo sprite:
   `0x0168` (y_raw=0x00E8 + 0x80 = 0x0168). Pass if `frame700_vdp_port_read_f800 != 0000`.

4. `vdpSpriteCache` at WRAM 0xE0FF6DF0 is NOT updated each frame by the new hot path — confirm
   the first 8 bytes at 0xE0FF6DF0 remain stale (whatever value the last C helper call left)
   and are not being refreshed. This confirms SGDK's cache is bypassed.

5. Visible sprite pixels appear on screen — any nonzero pixel row in the sprite plane confirms
   the full pipeline (Block-A → assembly SAT writer → VDP VRAM → VDP scanline scan) is
   operational end to end. Tiles may be wrong (stub tile base), palette may be wrong (hardcoded
   palette 0), but position should be in range and pixels should be non-transparent.

---

## 7. Out-of-Scope Items

Cody MUST NOT touch any of the following in this slice:

- Full PC080SN tilemap conversion (plane A / plane B nametable DMA pipeline)
- Final palette correctness — palette stays hardcoded (palette 0, priority 1) in the assembly
  stub; `frontend_palette_line_for_bank` is NOT called from assembly
- Full sprite size decoding — size stays fixed at 0x0500 (2×2 hardcoded) in the assembly stub
- Scroll system (`genesistan_scroll_from_workram_vdp`, VSRAM updates)
- Final flipscreen fidelity — flipscreen transform is NOT implemented in this slice
- Tile upload / cache redesign — `frontend_runtime_tile_for_code` and tile DMA stay in the
  C helper body (which is now dead code from the vblank path); tile VRAM residency is assumed
  from prior scene init
- Sprite link chain correctness beyond sequential count-based chain
- Animation frame cycling — Block-A builder and animation state untouched
- Block-A WRAM locations — 0xE0FF11FE and 0xE0FF01BC stay exactly as they are
- ROM/spec patch changes — no `specs/startup_title_remap.json` or any `.json` spec file changes
- Suppression of the redundant 0x03AAF2 arcade dispatch — that is a separate follow-on action
- Gameplay state sprite pipeline (states 2–4) — title state is the only validation target
- Any exception handler code — `z_qr_exception.c`, `z_qr_exception_handlers.s` untouched
- `startup_bridge.c` — untouched
- SGDK initialization — untouched
- The `genesistan_render_sprites_vdp()` function body in `main.c` — leave it in place as dead
  code; do not delete it in this slice (Phase 4 cleanup)
- `genesistan_vblank_sprite_commit()` — leave it in place; simply remove its call from the
  vblank handoff (or it can remain if the handoff is restructured, but it must not fire for
  SAT commit when the assembly path is active)

---

## 8. Rainbow Islands / Cadash Sanity Check

Both Rainbow Islands and Cadash confirm that SAT commit in arcade-to-Genesis translations
operates in an interrupt/vblank-synchronized, hardware-writing context — not from a C function
holding a staging buffer. Rainbow Islands stages sprite descriptors into WRAM regions around
`0xFFFB00` and commits them to VDP via DMA register sequences driven from interrupt-owned
timing; Cadash stages descriptor/script data and emits sprite words through VDP control and
data port sequences (`movel %d0, 0xC00004; movew %d1, 0xC00000`) inside scripted output
routines that are themselves called from the interrupt frame. Both cases confirm strict
producer-to-staging-to-commit separation where the commit step talks directly to VDP hardware.
The chosen slice — assembly routine reads Block-A WRAM, converts arithmetic directly in
registers, and writes SAT words to 0xC00000 after setting the VDP address to 0xF800 via
0xC00004 — is precisely this pattern: the arcade vblank-owned call directly commits hardware
without a C intermediary, matching both Taito translations' confirmed architecture.

---

## 9. Final Recommendation

Option A is the correct and only first non-C slice. It is the smallest change that establishes
a genuinely non-C, assembly-owned SAT commit path: the new routine reads the already-proven
Block-A WRAM structure, performs all necessary arithmetic in registers, and writes directly to
the VDP hardware, bypassing SGDK's `vdpSpriteCache`, `VDP_setSpriteFull`, and
`VDP_updateSprites` entirely. The C helper (`genesistan_render_sprites_vdp`) is removed from
the vblank call path in the same change. Tile lookup, palette, and size are stubbed
temporarily; these are sufficient to produce visible SAT output and prove the assembly path
is operational. The implementation touches only `startup_trampoline.s` (or a new `.s` file)
and the vblank handoff call site in `main.c`.

After this slice is validated, the follow-on actions are: (a) suppressing the redundant
0x03AAF2 arcade dispatch, (b) adding real tile residency lookup to the assembly routine
(Phase 3 full), and (c) retiring the C helper body entirely (Phase 4).

The next implementation step meaningfully reduces dependency on the temporary C helper by moving a real graphics responsibility into the arcade-vblank-owned non-C path.
