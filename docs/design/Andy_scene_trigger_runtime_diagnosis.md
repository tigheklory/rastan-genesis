# Andy — Scene Trigger Runtime Diagnosis

## 1. Executive Summary

Step 2 produced no visible change because it is **working exactly as designed but has no observable effect yet**: for the Title/attract scene currently executing, the fast path matches on every hook invocation, `load_scene_tiles` is never called from the hook (only from boot), VRAM tile content is unchanged, and the visual state is entirely governed by the pre-existing staging/commit system. The checkerboard persistence is a separate pre-existing condition unrelated to the trigger wiring.

One latent bug was identified in the slow path that will corrupt `staged_bg_buffer` writes on the first actual scene transition.

---

## 2. Task 1 — Trigger Preamble Execution Path

**Hook executing:** The hook is patched into the arcade ROM via `rom_absolute_call_relocation`. The arcade ROM calls the PC080SN tilemap function during its tick, and the patcher redirects that call to `genesistan_hook_tilemap_plane_a`. The BlastEm VRAM viewer showing real arcade tile data in the top rows of Plane B confirms the hook is executing and writing to `staged_bg_buffer`.

**Preamble executing:** The preamble at `.Lscene_preamble_fast_path` (lines 224–262) sits inside the hook's valid-destination path. It is reached every frame that the dest-pointer validation at lines 203–214 passes. The preamble is NOT reached on calls that take `.Lbg_hook_dest_invalid` (lines 314–318), but those calls also skip the descriptor loop entirely, so the preamble miss is inconsequential.

- hook executing: **YES**
- preamble executing: **YES**

---

## 3. Task 2 — Fast Path Dominance

At boot, `load_scene_tiles(0)` sets:
- `genesistan_scene_a0_lo = 0x0005A7DA`
- `genesistan_scene_a0_hi = 0x0005B0B2`

The arcade is in the Title/attract loop. The PC080SN source addresses (`%a0`) it passes to the hook are in the range `0x5A7DA–0x5B0B2` — the Title scene's source address window, as defined by `genesistan_scene_a0_ranges` entry 0. After masking to 24 bits (line 226: `andi.l #0x00FFFFFF, %d0`), every `%a0` value produced by the Title scene falls within `[genesistan_scene_a0_lo, genesistan_scene_a0_hi]`.

Therefore:
- `cmp.l genesistan_scene_a0_lo, %d0` → not below lower bound
- `cmp.l genesistan_scene_a0_hi, %d0` → not above upper bound
- `bra.s .Lscene_preamble_done` taken every time

**The fast path is taken on every hook invocation during Title scene playback.** The slow path is never reached. `load_scene_tiles` is never called from the hook. VRAM content is unchanged from the boot preload.

- fast path always taken: **YES**

---

## 4. Task 3 — Slow Path Reachability

The slow path fires when `%a0` (masked to 24 bits) falls outside `[genesistan_scene_a0_lo, genesistan_scene_a0_hi]`. This requires a source address outside the Title range — i.e., an actual scene transition to Gameplay (`0x56A22–0x570C2`) or End-Round (`0x5822A–0x59614`). No such transition has occurred during the observed Title sequence.

- slow path reachable: **YES** (on scene transitions — but none have occurred)

---

## 5. Task 4 — `load_scene_tiles` Call Frequency

`load_scene_tiles` is called:
1. Once at boot from `main_68k` (line 60: `bsr load_scene_tiles` with `%d0=0`)
2. Never again during the observed Title scene playback (fast path always taken)

- call behavior: **once at boot only**

---

## 6. Task 5 — Tileset Difference Between Scenes

The three scene manifests are generated from static analysis of the arcade ROM's distinct tile-reference windows and confirmed by binary inspection (841 / 829 / 1,067 pairs, with 779 slots aliased across scenes). The VRAM Pattern Viewer with Palette Line 1 shows recognizable Rastan title screen graphics: character set (digits, letters), hero sprite, background tile variants, platform tiles. These are visually distinct from Gameplay tiles (which include stage backgrounds, enemy sprites, terrain) and End-Round tiles.

- scenes visually distinct: **YES**

---

## 7. Task 6 — Hook Output Effectiveness

The BlastEm VRAM Debugger screenshot confirms that the top rows of the Plane B nametable contain real arcade tile references (rendered as colorful tile graphics rather than the solid-color checkerboard synthetic tiles). This is direct evidence that the hook IS writing valid nametable entries into `staged_bg_buffer` and those rows ARE being committed to Plane B.

The hook's nametable write path (lines 317–331):
- reads tile index from arcade WRAM tile table via `(%a4)` (line 318)
- masks to 14 bits: `andi.w #0x3FFF, %d3` (line 319)
- multiplies by 2 for LUT byte offset: `add.w %d3, %d3` (line 320)
- looks up VRAM slot: `move.w 0(%a2,%d3.w), %d3` where `%a2 = genesistan_pc080sn_tile_vram_lut` (line 321)
- ORs attribute bits from `genesistan_pc080sn_attr_lut`: `or.w (%sp), %d3` (line 322)
- writes combined nametable entry to `staged_bg_buffer`: `move.w %d3, 0(%a6,%d0.w)` (line 328)
- sets row dirty bit: `bset %d1, %d0` + `move.l %d0, bg_row_dirty` (lines 330–331)

For the Title scene, LUT slots 20–860 are populated. The hook produces valid non-zero nametable entries.

- hook produces meaningful tile indices: **YES**

---

## 8. Task 7 — Checkerboard Persistence

`init_staging_state` (lines 580–595) fills all 32 rows × 64 columns of `staged_bg_buffer` with alternating tile-1 / tile-2 references and sets `bg_row_dirty = 0xFFFFFFFF`. On the first VBlank, `vdp_commit_bg_strips_if_dirty` commits all 32 rows of this checkerboard pattern to Plane B.

The hook updates rows incrementally: it processes 16 descriptor iterations per call, each writing 4 rows at the specific row/column position indicated by the current dest-pointer position. The arcade's PC080SN controller updates only the rows that are "active" in the current frame's tile window. For the Title screen attract cycle, only a subset of the 32 rows are actively updated per tick — specifically the rows visible in the top portion of the screen (character set, title graphics). The bottom rows (background fill area) may update less frequently or not at all if the arcade's attract animation doesn't redraw them every frame.

The BlastEm VRAM viewer confirms this: the top portion of Plane B shows real arcade tile data, the lower rows still show the checkerboard fill from the initial commit. Full Plane B convergence to arcade tile data has not completed.

- checkerboard still dominating: **YES** (lower rows not yet overwritten by hook)

---

## 9. Task 8 — BG Commit Path

`vdp_commit_bg_strips_if_dirty` is called every VBlank from `_VINT_handler` (line 84). The hook sets `bg_row_dirty` bits at line 330–331 for each row written. The commit function reads these bits (line 337: `move.l bg_row_dirty, %d6`) and commits each dirty row to `VRAM_PLANE_B_BASE`. The BlastEm VRAM viewer showing arcade tile data in the top rows of Plane B is direct evidence this path is working.

- BG commit occurring: **YES**

---

## 10. Task 9 — Exact Current Behavior Explanation

**Why VRAM contains correct tile graphics:**
`load_scene_tiles(0)` ran at boot (after the register-clobber fix verified in Andy_verify_load_scene_tiles_fix.md). It iterated all 841 Title scene manifest pairs and uploaded each tile from `genesistan_pc080sn_tile_rom` to the assigned VRAM slot. The VRAM Pattern Viewer confirms slots 20–860 contain real PC080SN Title tile data.

**Why the screen still shows checkerboard:**
`init_staging_state` filled all 32 rows of `staged_bg_buffer` with tile-1/tile-2 (checkerboard) entries and set all dirty bits. The first VBlank committed all 32 rows of checkerboard to Plane B. The hook then began writing real arcade tile entries into `staged_bg_buffer` row-by-row as the arcade's attract animation progresses. Only the rows the arcade is actively updating per tick get replaced. The bottom rows of Plane B, which the Title attract animation does not update every frame, still contain the initial checkerboard entries. Full convergence to arcade tile output for all 32 rows has not completed.

**Why Step 2 produced no visible change:**
Step 2 inserted a scene-detection preamble that fires `load_scene_tiles` on scene transitions. During the Title scene, the fast path matches on every hook call — `load_scene_tiles` is never called from the hook. VRAM tile content is identical to what was loaded at boot. The trigger is correct and dormant. It will only produce a visible effect when the game transitions to a different scene. No such transition has occurred during the observed playback.

---

## 11. Task 10 — Root Cause

**Root cause: The fast path always matches during Title scene playback, making the Step 2 trigger dormant. No scene transition has occurred, so `load_scene_tiles` has only been called once (at boot). Step 2 is architecturally correct but has no observable effect until the first scene transition (Title → Gameplay).**

---

## 12. Task 11 — Next Required Fix

**Latent slow-path register clobber that will corrupt `staged_bg_buffer` on first scene transition.**

In the slow path (lines 238–253), `moveq #0, %d1` is used to initialize the scene-index counter. But `%d1` was set to the row index (0–31) by the destination-validation block at lines 216–219 and is required by the descriptor loop at lines 324–334 (`move.w %d1, %d0` → row addressing + `bset %d1, %d0` → dirty-bit marking). The scan loop also writes `%d2` via `move.l (%a1)+, %d2` (line 241), destroying the column index computed at lines 220–222.

The descriptor loop at `.Lscene_preamble_done` does NOT reinitialize `%d1` or `%d2` — it uses whatever values are in those registers. After any slow-path execution (match or no-match), `%d1 = 2` (last scene index checked) and `%d2 = last hi value from table scan = 0x00059614`. The descriptor loop then writes all nametable entries to wrong `staged_bg_buffer` positions (row 2, column 0x59614 >> 1 = invalid) and sets wrong dirty bits.

**Fix:** Save and restore `%d1` and `%d2` around the slow-path scan, or use different scratch registers (`%d3`/`%d4` are safe since they are reloaded before use in the descriptor loop). The minimal fix is to use `%d3` as the scene counter and `%d4`/`%d5` for the range loads in the scan loop instead of `%d1`/`%d2`.

This bug must be fixed before the first scene transition. It will not manifest during Title-only playback.

---

## 13. Final Result

Step 2 is architecturally correct. The trigger is dormant during Title scene playback because the fast path always matches. VRAM has correct Title tiles. Checkerboard persistence is a pre-existing convergence issue unrelated to the trigger. The single blocking latent bug is the slow-path register clobber (`%d1`/`%d2`) which will corrupt staged_bg_buffer writes on the first scene transition.
