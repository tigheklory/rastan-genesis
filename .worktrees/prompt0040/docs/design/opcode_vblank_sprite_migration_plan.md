# Opcode/VBlank Sprite Migration Plan

## 1. Purpose

This document defines the forward migration path that moves sprite commit responsibility from
the temporary C helper (`genesistan_render_sprites_vdp`) into an arcade-vblank-owned,
opcode/ROM-side path. It covers the current helper's responsibilities, the target end state,
the chosen first migration slice, the exact vblank adaptation mechanism, opcode-side work
status, the ordered phase plan, and what is explicitly out of scope for the first slice.

This plan is grounded in the diagnoses in `sat_publish_failure_diagnosis.md`,
`vblank_graphics_architecture_plan.md`, and the runtime probe results from builds 271–278.

---

## 2. Current Helper Responsibilities

The table below classifies every responsibility bucket of `genesistan_render_sprites_vdp`
(main.c:1538–1657).

| # | Bucket | Description | Classification |
|---|--------|-------------|----------------|
| 1 | Block-A / Block-B descriptor scan | Iterates `sprite_blocks[]` table: WRAM offset 0x11B2 (18 entries) + 0x0170 (4 entries); reads 8 bytes per entry | KEEP TEMPORARILY — scan loop is simple and in the right place; will move to vblank commit in Phase 3 |
| 2 | Validity filtering | Zero-tuple guard (`data==0 && y_raw==0 && code==0 && x_raw==0` → sentinel); 0x0180 off-screen sentinel; tile_base < 0 skip; out-of-bounds skip | KEEP TEMPORARILY — correct filtering logic; migrates with scan in Phase 3 |
| 3 | Coordinate conversion | `x_raw & 0x01FF` sign-extend; `if > 0x140 subtract 0x0200`; SGDK `VDP_setSpriteFull` adds +128 internally | MOVE TO ARCADE VBLANK COMMIT — simple arithmetic; belongs in the vblank-owned SAT formation step |
| 4 | Tile lookup / tile residency | `frontend_runtime_tile_for_code(code, &unique_count)` checks tile cache; on miss, loads tile data from ROM into `frontend_runtime_sprite_tile_buffer`, DMAed below | KEEP TEMPORARILY for Phase 1–2; MOVE TO OPCODE/ROM-SIDE in Phase 3 (cache miss resolution belongs before SAT formation) |
| 5 | SAT entry formation | `TILE_ATTR_FULL(palette_line, priority, flipy, flipx, tile_base)` builds tile_attr; `VDP_setSpriteFull(sprite_count, x, y, SPRITE_SIZE(2,2), tile_attr, link)` writes to `vdpSpriteCache` | MOVE TO ARCADE VBLANK COMMIT — this is the core commit step; belongs in vblank-owned routine, not C helper |
| 6 | SAT publish / DMA | `VDP_updateSprites(sprite_count, DMA)` + `VDP_waitDMACompletion()` — immediate DMA from `vdpSpriteCache` → VRAM 0xF800 | MOVE TO ARCADE VBLANK COMMIT — DMA publish is explicitly vblank-owned in the architecture plan; first structural migration target (Phase 2) |
| 7 | Palette interactions | `frontend_palette_line_for_bank` maps color bank to palette line; `refresh_frontend_sprite_palettes` syncs CRAM if banks changed | DEFER TO LATER PHASE — palette system is its own phase; keep in helper until palette architecture is finalized |
| 8 | Flipscreen handling | Reads `genesistan_arcade_workram_words[15]`; transforms `x = 320 - x - 16`, `y = 256 - y - 16`, inverts flipx/flipy | KEEP TEMPORARILY — correct logic; migrates with scan/formation in Phase 3 |

### Block-A Format Sufficiency

Block-A format at 0xE0FF11FE: `word0=attr/flags`, `word1=y_raw`, `word2=tile_code`, `word3=x_raw`.

Genesis SAT needs: `Y+128`, `size+link`, `tile_attr`, `X+128`.

The coordinate transform (+128 via SGDK) and tile_attr construction are simple enough to
perform in vblank commit without a new intermediate format. **Block-A IS a sufficient
intermediate format for Phase 1 and Phase 2. No normalization layer is needed.**

---

## 3. Target End State

### What opcode/ROM-side logic produces

The block-A builder at genesis 0x05A2B4 (arcade 0x05A098) reads animation state and writes
8-byte descriptor tuples into WRAM at offsets 0x11B2 (18 entries) and 0x0170 (4 entries).
Format per entry: `word0=attr/flags`, `word1=y_raw`, `word2=tile_code&0x3FFF`, `word3=x_raw`.
This runs inside the arcade vblank's per-state dispatch (0x03AAEC in the title state handler).

### What WRAM buffers hold

The two Block-A descriptor blocks remain at their current WRAM locations:
- 0xE0FF11B2 (offset 0x11B2), 18 entries × 8 bytes = 144 bytes
- 0xE0FF0170 (offset 0x0170), 4 entries × 8 bytes = 32 bytes

No new normalized buffer is introduced. Block-A is the canonical intermediate format.

### What arcade vblank commit does

After `genesistan_run_original_frontend_tick()` returns (which completes the arcade state
machine including all block-A producers), a vblank-owned commit routine:
1. Scans Block-A entries at 0xE0FF11B2 and 0xE0FF0170
2. Applies validity filters (zero-tuple sentinel, 0x0180 off-screen, out-of-bounds)
3. Resolves tile cache for each valid code (cache miss: DMA tile from ROM → VRAM slot)
4. Builds SAT entry: coordinate conversion (+128), SPRITE_SIZE(2,2), tile_attr, link chain
5. Writes SAT entries to `vdpSpriteCache` (or directly to a Genesis SAT staging buffer)
6. DMAs staging buffer → VDP VRAM 0xF800 (`VDP_updateSprites` or equivalent)
7. Waits for DMA completion

This commit routine is called unconditionally every V-INT from `genesistan_frontend_live_vint_handoff`,
regardless of which arcade state is active.

### What C helper code no longer exists

In the final state:
- `genesistan_render_sprites_vdp()` does not exist
- `render_frontend_sprite_layer()` does not exist
- The renderer bridge trampoline at 0x03AAF2 → 0x202B80 is not the sprite commit path
- No C function owns SAT formation or SAT DMA; all of it is driven by the vblank commit step

---

## 4. First Migration Slice

**Chosen: Option A — Move the CALL POINT from arcade-state-dependent dispatch to unconditional vblank hook.**

Rationale: Option A is the minimal structural change that ensures SAT DMA fires every frame.
The C helper (`genesistan_render_sprites_vdp`) keeps all its current logic intact; the only
change is WHERE it is called. This directly fixes the diagnosed failure (791 vblanks, 2 renderer
calls) without introducing any new systems, new assembly routines, or new split of the helper.

Option B (move SAT formation to assembly) and Option C (split DMA publish out of helper) both
require new code to be written before any rendering improvement is visible. Option A produces
visible sprite pixels immediately and creates a stable baseline for the subsequent structural
splits.

**Option A is the first migration slice. Only one first slice is defined here.**

The two-step breakdown:
1. **Step A1 (Phase 1 — immediate)**: Add an unconditional call to `genesistan_render_sprites_vdp()`
   inside `genesistan_frontend_live_vint_handoff()`, after `genesistan_run_original_frontend_tick()`
   returns. This is a C code change only. No ROM patch needed for this step.
2. **Step A2 (Phase 2 — structural)**: Split SAT publish (DMA) out of the helper into a
   standalone vblank-owned function. The helper retains scan + formation logic; the DMA call
   (`VDP_updateSprites` + `VDP_waitDMACompletion`) moves to a dedicated commit function called
   from the same vblank hook, after the helper populates `vdpSpriteCache`.

---

## 5. Arcade VBlank Adaptation

### Entry point function

`genesistan_frontend_live_vint_handoff` — defined in main.c at line 1881.

This is the SGDK V-INT callback registered via `SYS_setVIntCallback(genesistan_frontend_live_vint_handoff)`
at main.c:1766. It fires every V-INT during SCREEN_FRONTEND_LIVE.

### Current body (lines 1881–1893)

```
genesistan_frontend_live_vint_handoff()
  guard: !frontend_live_handoff_active || current_screen != SCREEN_FRONTEND_LIVE → return
  genesistan_refresh_arcade_inputs();
  genesistan_run_original_frontend_tick();
  [return]
```

### Exact insertion point

After `genesistan_run_original_frontend_tick()` returns, before the closing brace of the
`#if RASTAN_ENABLE_STARTUP_HOOK` block. This ensures:
- The arcade state machine (including all block-A producers at 0x03AAEC) has already run
- The block-A WRAM descriptor blocks contain fresh data for the current frame
- The SAT DMA fires unconditionally, every frame, regardless of arcade state

### What the call does

```c
genesistan_render_sprites_vdp();
```

This unconditional call invokes the full helper: block scan, validity filter, tile cache
resolve, VDP_setSpriteFull loop, tile DMA, VDP_updateSprites(DMA), VDP_waitDMACompletion.
SAT DMA fires to VRAM 0xF800 every V-INT for the lifetime of SCREEN_FRONTEND_LIVE.

### Mechanism

This is a **C code change only**. No ROM patch, no opcode_replace, no shift_replacement entry,
no trampoline modification. The change is confined to `genesistan_frontend_live_vint_handoff`
in main.c.

### Guard

The existing guard `!frontend_live_handoff_active || (current_screen != SCREEN_FRONTEND_LIVE)`
already ensures the renderer only runs during the correct phase. No additional guard is needed
around the inserted call.

---

## 6. Opcode/ROM-Side Changes Needed

### Done (already in place)

| Item | Status | Location |
|------|--------|----------|
| Phase 2 patch: `shift_replacement` at arcade_pc=0x059F90 restores block-A builder callsite | DONE | specs/startup_title_remap.json |
| Block-A builder at genesis 0x05A2B4 (arcade 0x05A098) populates WRAM tuples correctly | DONE — confirmed by runtime probe (entry0=0000 00E8 03CA 0010) | ROM code |
| Renderer bridge trampoline at genesis 0x202B80 → `genesistan_render_sprites_vdp_bridge` | DONE | startup_trampoline.s |
| `VDP_setSpriteListAddress(0xF800)` in `genesistan_sync_title_vdp_layout` sets SAT base | DONE — confirmed VDP reg5=0x7C | main.c:1401 |
| Order fix: producer at 0x03AAEC fires before renderer at 0x03AAF2 in title init cluster | DONE — ORDER FIX PATCH B confirmed | specs/startup_title_remap.json |

### Pending (not yet done)

| Item | Required for Phase | Notes |
|------|--------------------|-------|
| Remove/bypass renderer dispatch at 0x03AAF2 once vblank-owned commit is unconditional | Phase 2 | Once vint_handoff calls renderer unconditionally, 0x03AAF2 dispatch is redundant; keeping it causes double-call in title init states. Must be suppressed. |
| Move SAT formation (scan + VDP_setSpriteFull loop) to assembly trampoline or native routine | Phase 3 | Replaces C helper scan logic with ROM-side or trampoline code; removes C dependency |
| Tile cache integration with vblank commit (cache miss DMA ordering before SAT DMA) | Phase 3 | Already exists in helper; must be preserved when migrating to vblank-owned commit |
| Full Block-A producer coverage for gameplay states (state 2–4 dispatch paths) | Phase 3+ | Title state (state=1) is the current focus; gameplay states have separate producers |

### Block-A producer sufficiency

The block-A builder at 0x05A2B4 is sufficient as-is for Phase 1. It produces correct tuples
confirmed by probe data. No additional producer calls need translation for Phase 1.

The existing Block-A 4-word format is sufficient. No new normalized format is needed.

---

## 7. Phase Order

### Phase 1 — IMMEDIATE: Unconditional Vblank Call

**Objective**: SAT DMA fires every frame; visible sprite pixels on screen.

**Code area**: `genesistan_frontend_live_vint_handoff()` in main.c.

**Change**: Add `genesistan_render_sprites_vdp()` call after `genesistan_run_original_frontend_tick()`.
C code change only. No ROM patches.

**Success criterion**: VRAM 0xF800 contains nonzero sprite entries at frame 700 (not just at
frames 1–2). Logo sprite pixels visible in screenshot. Probe: `HIT 2005C4` count equals
`HIT 03A208` count (renderer fires every vblank).

---

### Phase 2 — STRUCTURAL: Split SAT Publish to Vblank-Owned Function

**Objective**: SAT DMA commit is vblank-owned and not coupled to the C helper's timing or
internal state. Decouples scan/formation from publish.

**Code area**: New `genesistan_vblank_sat_commit()` function in main.c; called from
`genesistan_frontend_live_vint_handoff()` as a second step after the (now reduced) helper.

**Change**: Extract `VDP_updateSprites(sprite_count, DMA)` + `VDP_waitDMACompletion()` from
`genesistan_render_sprites_vdp()` into a standalone `genesistan_vblank_sat_commit()`.
The helper populates `vdpSpriteCache` and sets a `sprite_count` variable accessible to the
commit function. The commit function DMAs the buffer unconditionally each frame.
Suppress the redundant 0x03AAF2 arcade dispatch to avoid double-call.

**Success criterion**: Sprite pipeline works correctly across all arcade states, not just the
states that previously dispatched via 0x03AAF2. `VDP_updateSprites` is no longer inside the
C renderer body.

---

### Phase 3 — MIGRATION: Move Block-A Scan + SAT Formation Out of C Helper

**Objective**: C helper no longer needed for sprite pipeline. Scan, validity filter, coordinate
conversion, tile lookup, and SAT formation move to an assembly trampoline or ROM-side routine
called from vblank commit.

**Code area**: New assembly routine in startup_trampoline.s (or equivalent); called from
`genesistan_frontend_live_vint_handoff()` in place of C helper call.

**Change**: Replace `genesistan_render_sprites_vdp()` call in vint_handoff with a call to the
new assembly routine. The routine reads Block-A descriptor blocks directly, applies validity
checks, resolves tile cache, forms SAT entries, and hands off to the Phase 2 commit function.
`genesistan_render_sprites_vdp()` becomes unused.

**Success criterion**: `genesistan_render_sprites_vdp()` is not called anywhere in the active
sprite pipeline path. Probe: sprite pipeline still works; no regression from Phase 2 baseline.

---

### Phase 4 — CLEANUP: Retire C Helper and Scaffolding

**Objective**: Clean production architecture. No temporary C helper renderer in sprite path.

**Code area**: main.c — remove `genesistan_render_sprites_vdp`, `render_frontend_sprite_layer`,
`genesistan_hook_frontend_sprite_sat_refresh`, `refresh_frontend_sprite_palettes` (if palette
system supersedes it), and all associated static state. Remove renderer bridge trampoline
at 0x03AAF2 → 0x202B80 if still present.

**Change**: Delete or `#if 0` guard all of the above. Confirm no remaining callers. Verify
build passes and sprite pipeline still functions without C helper.

**Success criterion**: `genesistan_render_sprites_vdp` does not exist in the compiled binary.
Sprite pipeline output is identical to Phase 3 baseline.

---

## 8. Out-of-Scope for First Slice (Phase 1)

The following are explicitly NOT in Phase 1:

- Full PC080SN tilemap conversion (plane A / plane B nametable DMA pipeline)
- Final palette correctness (palette system, dirty-flag DMA, CLCS capture)
- Full sprite size decoding (all sizes; Phase 1 is fixed at SPRITE_SIZE(2,2) = 16×16)
- Scroll system (VSRAM updates from WRAM scroll words)
- Full flipscreen fidelity (flipscreen path exists but is not a Phase 1 validation target)
- Tile upload system correctness (tiles present in VRAM; Phase 1 accepts whatever `frontend_runtime_tile_for_code` produces)
- Multi-sprite link field correctness (link chain terminates at last entry; complex chains not validated)
- Animation system (sprite cycling, frame data sequencing beyond what block-A already produces)
- Gameplay state sprite pipeline (states 2–4; Phase 1 target is title state only)
- Suppression of redundant 0x03AAF2 arcade dispatch (double-call exists in Phase 1; suppression is a Phase 2 task)
- Refactoring of `SYS_disableInts`/`SYS_enableInts` wrappers inside the helper

---

## 9. Final Recommendation

Phase 1 is a single C code change: add `genesistan_render_sprites_vdp()` unconditionally
inside `genesistan_frontend_live_vint_handoff()` after `genesistan_run_original_frontend_tick()`
returns. This is the minimal change that converts the sprite pipeline from a 2-per-791-frame
failure to a sustained per-frame DMA path. All other responsibilities remain in the helper
temporarily; no new systems are required; no ROM patches are required.

Phase 2 then decouples the DMA publish step from the C helper, making SAT commit a first-class
vblank-owned operation. Phases 3 and 4 complete the migration and remove C scaffolding.

The next implementation step migrates sprite commit responsibility out of the temporary C helper and into an arcade-vblank-owned opcode/ROM-side path.
