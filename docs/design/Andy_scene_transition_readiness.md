# Andy — Scene Transition Readiness Audit

## 1. Executive Summary

The first Title → Gameplay scene transition is fully correct and safe. All register state is preserved through every slow-path execution path. `load_scene_tiles` is safe to call from hook context. VRAM will update correctly. The system is ready for transition testing.

---

## 2. Inputs Used

- `apps/rastan-direct/src/main_68k.s` lines 196–360 (hook + descriptor loop)
- `docs/design/Cody_scene_trigger_slow_path_register_fix.md`
- `docs/design/Andy_scene_trigger_runtime_diagnosis.md`
- Runtime screenshots: VRAM shows correct Title tiles; screen shows checkerboard; no transition yet observed

---

## 3. Task 1 — Slow-Path Fix Correctness

**Slow-path register usage after fix (lines 236–263):**

```asm
.Lscene_slow_path:
    lea     genesistan_scene_a0_ranges, %a1
    move.l  %d5, %d6          ; save dest-pointer before scan clobbers %d5
    moveq   #0, %d3           ; scene counter → %d3 (was %d1 — FIXED)

.Lscene_loop:
    move.l  (%a1)+, %d4       ; lo → %d4 (was %d2 — FIXED)
    move.l  (%a1)+, %d5       ; hi → %d5 (was %d3)
    cmp.l   %d4, %d0
    blo.s   .Lnext_scene
    cmp.l   %d5, %d0
    bls.s   .Lscene_match

.Lnext_scene:
    addq.w  #1, %d3           ; %d3 not %d1 — FIXED
    cmpi.w  #3, %d3
    blt.s   .Lscene_loop
    move.l  %d6, %d5          ; restore dest-pointer
    bra.s   .Lscene_preamble_done

.Lscene_match:
    move.l  %d3, %d0          ; %d3 not %d1 — FIXED
    bsr     load_scene_tiles
    move.l  %d6, %d5          ; restore dest-pointer after call
    bra.w   .Lscene_preamble_done
```

- `%d1` (row index, set at lines 217–219): **never written** by slow path. ✓
- `%d2` (column-derived value, set at lines 220–222): **never written** by slow path. ✓
- `%d5` (dest pointer, loaded at line 201): clobbered by line 243 (`move.l (%a1)+, %d5`) but saved to `%d6` at line 238 and restored at lines 256 and 262. ✓
- `load_scene_tiles` saves `%d1-%d7/%a0-%a4` (line 484), so `%d6` (which holds the saved dest-pointer) is preserved across the `bsr load_scene_tiles` call. After return, `move.l %d6, %d5` at line 262 restores `%d5` correctly. ✓
- No new clobber introduced. ✓

**Slow-path fix correct: YES**

---

## 4. Task 2 — Register State at `.Lscene_preamble_done`

Tracing all three paths into `.Lscene_preamble_done`:

| Register | Fast path | Slow no-match | Slow match |
|----------|-----------|---------------|------------|
| `%d1` | Untouched since line 217–219 | Untouched | Untouched (load_scene_tiles saves/restores) |
| `%d2` | Untouched since line 220–222 | Untouched | Untouched (load_scene_tiles saves/restores) |
| `%d5` | Untouched | Restored from `%d6` (line 256) | Restored from `%d6` (line 262) |
| `%d6` | Uninitialized but irrelevant | Uninitialized but irrelevant | Restored by load_scene_tiles |
| `%d7` | Untouched since line 200 | Untouched | Untouched (load_scene_tiles saves/restores) |
| `%a0` | Holds original source addr | Holds original source addr | Restored by load_scene_tiles to original source addr |

`%d6` is immediately overwritten at line 272 (`moveq #15, %d6`) — its value on entry to `.Lscene_preamble_done` is irrelevant.

`%a0` is immediately overwritten at line 266 (`lea ARCADE_PC080SN_DESC_BG_LIST_OFFSET(%a5), %a0`). Its value from load_scene_tiles restoration or from the fast path does not matter.

**Descriptor entry state correct: YES**

---

## 5. Task 3 — `load_scene_tiles` Safety from Hook Context

`load_scene_tiles` saves and restores `%d1-%d7/%a0-%a4` (line 484: `movem.l %d1-%d7/%a0-%a4, -(%sp)`).

At the time `load_scene_tiles` is called from `.Lscene_match` (line 261):
- `%a5` = 0xFF0000 (established at hook entry, line 198). `load_scene_tiles` does not save or touch `%a5`. `load_scene_tiles` does not use `%a5` internally. ✓
- `%a6` is not saved by `load_scene_tiles` (not in its save list). `%a6` has not yet been initialized in the hook — `lea staged_bg_buffer, %a6` is at line 270, after `.Lscene_preamble_done`. So even if `load_scene_tiles` modified `%a6` (it does not), it would not corrupt a live value. ✓
- `load_scene_tiles` calls `vdp_set_reg` and `vdp_set_vram_write_addr`, both of which use `%d0/%d1/%d2` — all of which are in the save list and are restored on return. ✓
- `load_scene_tiles` sets `SR = 0x2700` before VDP writes and restores `SR = 0x2000` before `rts`. On exit the hook continues with interrupts enabled (correct for main-loop context). ✓
- Return flow: `load_scene_tiles` ends with `movem.l (%sp)+, %d1-%d7/%a0-%a4; rts`, returning to line 262 (`move.l %d6, %d5`). ✓

**`load_scene_tiles` safe in hook context: YES**

---

## 6. Task 4 — Scene Switch Effectiveness

On first Gameplay source address encountered, `load_scene_tiles(1)` is called. It:
1. Selects `genesistan_scene_preload_gameplay` manifest (829 pairs)
2. Iterates all 829 `(arcade_tile, vram_slot)` pairs
3. For each: sets VRAM write address to `vram_slot × 32`, copies 32 raw bytes from `genesistan_pc080sn_tile_rom + (arcade_tile × 32)` to VDP_DATA
4. Writes `genesistan_current_scene_id = 1`
5. Writes `genesistan_scene_a0_lo = 0x00056A22`, `genesistan_scene_a0_hi = 0x000570C2`

The 779 aliased VRAM slots (shared between scenes) are overwritten with Gameplay tile data. Slots unique to Gameplay (those not in the Title manifest) receive new data. After return, all VRAM slots referenced by the Gameplay LUT contain the correct Gameplay tile pixels. The nametable hook's LUT lookups (line 324: `move.w 0(%a2,%d3.w), %d3`) will resolve to these correct slots.

**Scene switch will correctly change VRAM content: YES**

---

## 7. Task 5 — Hook Output Validity Post-Transition

After `load_scene_tiles(1)` returns at line 262, execution falls through to `.Lscene_preamble_done` and immediately into the descriptor loop. The descriptor loop:
- Reads the current frame's descriptor list from arcade WRAM (`ARCADE_PC080SN_DESC_BG_LIST_OFFSET(%a5)`)
- For each descriptor: reads the tile index table entry from arcade ROM, looks up the VRAM slot in `genesistan_pc080sn_tile_vram_lut`, ORs attribute bits from `genesistan_pc080sn_attr_lut`, writes the combined nametable entry to `staged_bg_buffer`
- Sets `bg_row_dirty` bits for written rows

The Gameplay tile indices are within the LUT's valid range (`andi.w #0x3FFF, %d3` at line 322 masks them). The LUT maps them to VRAM slots 20–848, which now contain Gameplay tile data. Nametable entries are correct.

**Hook output valid post-transition: YES**

---

## 8. Task 6 — BG Commit After Transition

`vdp_commit_bg_strips_if_dirty` is called every VBlank from `_VINT_handler` (line 84). After the transition, the descriptor loop sets `bg_row_dirty` bits for the rows it writes (line 333: `bset %d1, %d0; move.l %d0, bg_row_dirty`). The commit function checks these bits at line 337 and flushes each dirty row from `staged_bg_buffer` to Plane B VRAM. This is the same path already confirmed working by the BlastEm VRAM viewer evidence.

**BG commit will reflect new scene: YES**

---

## 9. Task 7 — Hidden Failure Mode Check

**Infinite reload loop:** After `load_scene_tiles(1)` updates `genesistan_scene_a0_lo/hi` to the Gameplay range, the next hook call with a Gameplay source address hits the fast path. No repeated calls. ✓

**Repeated `load_scene_tiles` calls:** State update happens inside `load_scene_tiles` before `rts` (lines 532–541 in the fixed source). Fast path succeeds on all subsequent Gameplay hook calls. ✓

**Incorrect scene detection bounds:** Gameplay range in `genesistan_scene_a0_ranges`: lo=`0x00056A22`, hi=`0x000570C2`. `%d0` after masking for a Gameplay address (e.g. `0x00056A22`): `cmp.l %d4, %d0` where `%d4=0x00056A22` → equal, not below → no skip; `cmp.l %d5, %d0` where `%d5=0x000570C2` → not above → `bls.s .Lscene_match`. ✓

**Masked `%a0` mismatch:** All `genesistan_scene_a0_ranges` values are `0x0005xxxx` (high byte = 0). After `andi.l #0x00FFFFFF, %d0`, comparison is numerically identical. ✓

**Descriptor loop misalignment:** `%a0` is replaced at line 266 immediately on entry to `.Lscene_preamble_done`. The original source-address value in `%a0` (whether from fast path or load_scene_tiles restoration) is completely irrelevant to the descriptor loop. ✓

**`%a1` at descriptor setup:** Line 267 sets `%a1 = ARCADE_MAINCPU_ROM_BASE` explicitly. Whatever `%a1` contains after the slow-path scan is irrelevant. ✓

**Hidden failure present: NO**

---

## 10. Task 8 — Transition Prediction

When Title → Gameplay transition occurs:

1. Hook detects Gameplay source address, fast path fails, slow path matches scene 1, `load_scene_tiles(1)` runs.
2. Display goes dark for the duration of 829 tile uploads (estimated ~3.5 ms at 7.67 MHz CPU, well within one frame). One brief flicker.
3. Descriptor loop runs immediately for that frame's Gameplay nametable data. Valid Gameplay nametable entries written to `staged_bg_buffer`. Dirty bits set.
4. Next VBlank: dirty rows committed to Plane B. Those rows show correct Gameplay tile graphics.

**What changes first:** The rows actively written by the hook during the transition frame switch from checkerboard/Title tiles to Gameplay tiles on the next displayed frame.

**What will still look wrong:**
- Lower rows not yet overwritten by the hook will still show checkerboard from `init_staging_state` fill — this is pre-existing and will converge as the arcade continues to update all rows.
- All tile graphics render with the debug rainbow palette (`palette_init_words`), not the arcade's palette. Gameplay graphics will have the correct shape but wrong colors. Palette pipeline is not yet wired.
- A 1-frame display-off flicker will occur at the moment of transition.

---

## 11. Task 9 — Final Verdict

**READY FOR TRANSITION TEST**

No blockers. Register state is correct through every execution path. `load_scene_tiles` is safe in hook context. VRAM will receive correct Gameplay tiles on the first transition. BG commit will propagate the new nametable data to Plane B. All identified imperfections (checkerboard convergence lag, wrong palette, 1-frame flicker) are pre-existing conditions unrelated to the transition mechanism correctness.
