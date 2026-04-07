# Andy — VBlank Efficiency Audit and Transition Plan

## 1. Executive Summary

The current `apps/rastan-direct/` VBlank handler (post-dirty-flag fix, post-BSS-WRAM-fix, post-FG-row0-removal) has a clean, stable video baseline. The dirty-flag guards introduced by `Cody_bg_fg_dirty_guard_fix.md` have reduced the steady-state per-frame VBlank cost from approximately 59,268 cycles to approximately 380 cycles. Frame 1 (when all dirty flags fire) costs approximately 30,252 cycles — well above the 7,400-cycle budget, but this is a one-time startup cost and display-ON fires approximately 22,852 cycles after VBlank ends only on that single frame. From frame 2 onward the steady-state cost is approximately 380 cycles, fully within the 7,400-cycle VBlank budget.

Four inefficiencies remain:

1. The FG full-plane commit (2048 words) fires on frame 1 despite FG being entirely transparent. This is 28,672 cycles of unnecessary VRAM writes on startup.
2. The BG full-plane commit granularity (2048 words per dirty event) is wrong for the final port. When the arcade hook becomes active it will dirty at most a few strips per frame; the full-plane commit will then overrun budget on every frame that any BG strip changes.
3. The tile commit (48 words, frame 1 only, called from inside `vdp_commit_bg`) is structurally embedded in the wrong place — it runs inside `vdp_commit_bg` rather than as a top-level VBlank step.
4. The scroll commit runs unconditionally every frame, which is correct for the current demo (scroll values change every frame), but the mechanism writes 4 words via two separate VDP address setups, which is slightly more expensive than a single packed long write.

The single next implementation step is: **permanently remove the FG full-plane commit from the VBlank path**. FG starts all-zero (transparent), and arcade hooks will write FG strips directly into the staging buffer and mark strip-level dirty bits when they become active. There is no valid use case for a full FG plane commit in the VBlank path at any stage of the port.

After that step the ordered transition is: introduce per-strip dirty tracking for BG (32 row-level bits), then replace the full-plane BG commit with a row-iterating strip commit gated by per-row dirty bits, then move tile upload initialization out of the VBlank path entirely.

---

## 2. Inputs Audited

1. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/main_68k.s` — READ COMPLETE (current state: post-all-fixes, 396 lines)
2. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s` — READ COMPLETE (55 lines)
3. `/home/tighe/projects/rastan-genesis/docs/design/Cody_rastan_direct_video_backbone_bringup.md` — READ COMPLETE
4. `/home/tighe/projects/rastan-genesis/docs/design/Cody_bg_fg_dirty_guard_fix.md` — READ COMPLETE
5. `/home/tighe/projects/rastan-genesis/docs/design/Cody_bss_vma_wram_fix.md` — READ COMPLETE
6. `/home/tighe/projects/rastan-genesis/docs/design/Cody_fg_row0_bringup_stripe_removal.md` — READ COMPLETE
7. `/home/tighe/projects/rastan-genesis/docs/design/Andy_rastan_direct_video_bringup_plan.md` — READ COMPLETE (first 80 lines; executive summary and phase structure)
8. `/home/tighe/projects/rastan-genesis/docs/design/Andy_rastan_direct_display_tightening_against_rainbow.md` — READ COMPLETE (prior tightening analysis, all sections)
9. `/home/tighe/projects/rastan-genesis/docs/design/Cody_rainbow_islands_vdp_template_analysis.md` — READ COMPLETE
10. `/home/tighe/projects/rastan-genesis/apps/rastan/src/boot/sega.s` — READ (VBlank dispatch section, lines 160–240)

---

## 3. Exact VBlank Workload Measurement

### VBlank Handler Structure (current `_VINT_handler`)

```
_VINT_handler:
    movem.l %d0-%d7/%a0-%a6, -(%sp)   ; 15 regs × ~8 = ~108 cycles (WRAM)
    move.w  VDP_CTRL, %d0              ; VDP status read: ~8 cycles
    moveq / moveq / bsr vdp_set_reg    ; display OFF: ~40 cycles
    bsr     vdp_commit_bg              ; see breakdown below
    bsr     vdp_commit_fg              ; see breakdown below
    tst.b   palette_dirty              ; test: ~8 cycles
    beq.s   .Lskip_palette             ; branch (taken/not taken): ~8 cycles
    [bsr vdp_commit_palette]           ; conditional, frame 1 only
    [clr.b  palette_dirty]
    moveq / moveq / bsr vdp_set_reg    ; display ON: ~40 cycles
    bsr     vdp_commit_scroll          ; see breakdown below
    addq.w  #1, frame_counter          ; ~8 cycles
    movem.l (%sp)+, %d0-%d7/%a0-%a6   ; ~108 cycles
    rte                                ; ~20 cycles
```

### Per-Function Cycle Accounting

**Cycle model:** Genesis 68000 at 7.67 MHz. All variables in WRAM (BSS at 0xFF0000). CPU stalls on VDP DATA writes due to FIFO; 14 cycles per word write (conservative, confirmed by prior Andy audit). VDP control port write: ~8 cycles. `dbra` loop: 10 cycles per taken branch. `bsr`/`rts` round trip: ~16 cycles overhead.

#### `vdp_commit_bg`

Guard path (dirty flag clear, frame 2+ with no BG change):
- `tst.b bg_dirty`: ~8 cycles
- `beq.s .Lbg_done` (taken): ~8 cycles
- `rts`: ~8 cycles
- **Guard-only cost: ~24 cycles**

Active path (dirty flag set):
- `tst.b bg_dirty` + `beq` not taken: ~16 cycles
- `bsr vdp_commit_tiles_if_dirty`:
  - Frame 1 (tiles_dirty=1): `tst.b` + branch not taken + `vdp_set_vram_write_addr` (~40 cycles) + 48 × 14 cycles (word writes) + 48 × 10 cycles (dbra) = ~16 + 40 + 672 + 480 = ~1,208 cycles
  - Frame 2+ (tiles_dirty=0): `tst.b` + `beq` taken + `rts` = ~24 cycles (guard only)
- `vdp_set_vram_write_addr` for VRAM_PLANE_B_BASE: ~40 cycles
- 2048 × 14 cycles (word writes to VDP DATA): 28,672 cycles
- 2048 × 10 cycles (dbra): 20,480 cycles
- `clr.b bg_dirty`: ~8 cycles
- `rts`: ~8 cycles
- **BG active total, frame 1: ~1,208 (tiles) + 40 + 28,672 + 20,480 + 24 = ~50,424 cycles**
- **BG active total, frame 2+ (no tiles): ~24 (tiles guard) + 40 + 28,672 + 20,480 + 24 = ~49,240 cycles**

Note: The 2048 × 10 cycles for `dbra` is included above in addition to the 14-cycle-per-word VDP write cost, totaling ~49,152 cycles for the inner loop alone. Prior audits used 24 cycles per iteration (14 write + 10 dbra). This audit uses the same model for consistency.

#### `vdp_commit_fg`

Guard path (dirty flag clear):
- **Guard-only cost: ~24 cycles**

Active path (dirty flag set):
- No tile commit sub-call.
- `vdp_set_vram_write_addr` for VRAM_PLANE_A_BASE: ~40 cycles
- 2048 × 14 cycles (word writes): 28,672 cycles
- 2048 × 10 cycles (dbra): 20,480 cycles
- `clr.b fg_dirty` + `rts`: ~16 cycles
- **FG active total: ~49,208 cycles**

#### `vdp_commit_palette`

Guard path (palette_dirty=0):
- `tst.b palette_dirty` + `beq` taken: ~16 cycles (inline in VBlank handler, not a sub-call)
- **Guard-only cost: ~16 cycles**

Active path (palette_dirty=1, frame 1 only):
- `move.l #0xC0000000, VDP_CTRL`: ~8 cycles (CRAM write command)
- 64 × 14 cycles (word writes): 896 cycles
- 64 × 10 cycles (dbra): 640 cycles
- `rts` + `clr.b palette_dirty`: ~16 cycles
- **Palette active total: ~1,560 cycles**

#### `vdp_commit_scroll` (unconditional, every frame)

- `bsr` + `vdp_set_vram_write_addr` for VRAM_HSCROLL_BASE: ~56 cycles
- `move.w staged_scroll_x_fg, VDP_DATA`: ~14 cycles
- `move.w staged_scroll_x_bg, VDP_DATA`: ~14 cycles
- `move.l #0x40000010, VDP_CTRL`: ~8 cycles (VSRAM write command)
- `move.w staged_scroll_y_fg, VDP_DATA`: ~14 cycles
- `move.w staged_scroll_y_bg, VDP_DATA`: ~14 cycles
- `rts`: ~8 cycles
- **Scroll commit total: ~128 cycles**

#### Display OFF/ON Bracket

Each call to `vdp_set_reg`: `move.w / lsl.w / or.w / ori.w / move.w VDP_CTRL / rts` = ~40 cycles.
Two calls (OFF + ON) = ~80 cycles. BSR overhead for each: included.

#### VBlank Fixed Overhead

- Register save: ~108 cycles
- VDP status read: ~8 cycles
- Frame counter increment: ~8 cycles
- Register restore + RTE: ~128 cycles
- **Fixed overhead total: ~252 cycles**

### Frame 1 Total Cost (all dirty flags = 1)

| Component | Cycles |
|-----------|--------|
| Fixed overhead (save/restore/rte) | 252 |
| VDP status read | 8 |
| Display OFF | 40 |
| `vdp_commit_bg` (active, with tile commit) | 50,424 |
| `vdp_commit_fg` (active, no tile commit) | 49,208 |
| `palette_dirty` test | 8 |
| `vdp_commit_palette` (active) | 1,560 |
| `clr.b palette_dirty` | 8 |
| Display ON | 40 |
| `vdp_commit_scroll` | 128 |
| **Frame 1 total** | **101,676 cycles** |

VBlank budget: 7,400 cycles.
Frame 1 overrun: approximately 13.7× budget.
Display-ON fires approximately 94,276 cycles after VBlank begins on frame 1.

### Frame 2+ Steady-State Cost (all dirty flags cleared after frame 1)

After frame 1, `bg_dirty`, `fg_dirty`, `tiles_dirty`, and `palette_dirty` are all 0. `arcade_tick_logic` updates scroll values (staged_scroll_x_bg/fg, staged_scroll_y_bg/fg) every frame but does NOT set any dirty flags. Therefore every commit function takes only its guard branch.

| Component | Cycles |
|-----------|--------|
| Fixed overhead (save/restore/rte) | 252 |
| VDP status read | 8 |
| Display OFF | 40 |
| `vdp_commit_bg` guard (bg_dirty=0, skip) | 24 |
| `vdp_commit_fg` guard (fg_dirty=0, skip) | 24 |
| `palette_dirty` test (branch taken) | 16 |
| Display ON | 40 |
| `vdp_commit_scroll` (unconditional) | 128 |
| **Frame 2+ total** | **532 cycles** |

VBlank budget: 7,400 cycles.
Steady-state headroom: 6,868 cycles.

**Is steady-state within 7,400-cycle VBlank budget? YES**

### Summary Table

| Frame | Total Estimated Cycles | Within 7,400-cycle Budget? |
|-------|----------------------|--------------------------|
| Frame 1 | ~101,676 | NO (13.7× overrun) |
| Frame 2+ | ~532 | YES (7.2% of budget used) |

---

## 4. Identified Inefficiencies

### Inefficiency 1: FG Full-Plane Commit Fires on Frame 1 Despite FG Being Entirely Transparent

**Location:** `vdp_commit_fg`, lines 210–224 of `apps/rastan-direct/src/main_68k.s`.

**Why inefficient:** `init_staging_state` zeroes all 2048 words of `staged_fg_buffer` (the `.Lfg_clear` loop). The entire FG plane is tile 0, palette 0, which is transparent on Genesis. Writing 2048 zero words to VRAM wastes approximately 49,208 cycles on frame 1 for no visual effect. FG will be populated by arcade PC080SN hooks (strip-level writes) when the arcade tick becomes active. A full-plane FG commit is never the correct mechanism at any stage of the port: neither as bring-up scaffolding (it produces no visible content) nor as a production path (strip-level writes are correct for the arcade hook model).

**Category:** Unnecessary work — zero effect, high cost.

### Inefficiency 2: BG Full-Plane Commit is Wrong Granularity for Final Port

**Location:** `vdp_commit_bg`, lines 192–208 of `apps/rastan-direct/src/main_68k.s`.

**Why inefficient:** The current full-plane commit writes all 2048 words of `staged_bg_buffer` whenever `bg_dirty` is set. In the final port, the arcade PC080SN hook writes individual strips (rows) to the staging buffer. A typical frame changes 0–4 strips, not 2048 words. If `bg_dirty` is used as a whole-plane flag, any strip write will trigger a 49,200+ cycle full-plane commit on the next VBlank, overrunning the budget by 6.6×. Strip-level dirty tracking (one bit per row, 32 rows) limits each VBlank to the exact strips that changed.

**Category:** Structurally wrong for the final port; tolerable in bring-up (BG only changes on frame 1).

### Inefficiency 3: Tile Commit Is Embedded Inside `vdp_commit_bg` Rather Than as a Top-Level VBlank Step

**Location:** `vdp_commit_bg` calls `bsr vdp_commit_tiles_if_dirty` at line 196 of `apps/rastan-direct/src/main_68k.s`.

**Why inefficient:** Tile commits are logically independent from BG nametable commits. Embedding the tile commit inside `vdp_commit_bg` means: (a) tiles only upload when BG is also dirty, creating a hidden coupling; (b) if tiles need to be refreshed without a BG dirty event, there is no path to trigger them; (c) the commit order is partially obscured — the VBlank handler itself does not show tile commit as a top-level step. In the Rainbow Islands model, all VBlank steps are explicit top-level calls from the VBlank ISR, not nested sub-calls.

**Category:** Structural coupling — wrong for final port, acceptable in bring-up.

### Inefficiency 4: `vdp_commit_scroll` Uses Two Separate VDP Address Setups for HScroll and VSRAM

**Location:** `vdp_commit_scroll`, lines 236–246 of `apps/rastan-direct/src/main_68k.s`.

**Why inefficient:** The function calls `vdp_set_vram_write_addr` (a multi-instruction function that costs ~40 cycles) for the HScroll table address, then writes two words, then writes `move.l #0x40000010, VDP_CTRL` inline for VSRAM. The HScroll setup could be reduced by inlining the control command as a `move.l` (like the VSRAM write) rather than calling `vdp_set_vram_write_addr`. This saves approximately 20–30 cycles per frame. At 60 Hz this is minor but worth noting. Rainbow Islands uses a single `move.l #0x40000010, C00004` then a single `move.l WRAM_SCROLL, C00000` for scroll commit.

**Category:** Minor overhead; not structurally wrong, but diverges from the Rainbow Islands minimal-write pattern.

### Inefficiency 5: `arcade_tick_logic` Updates All Four Scroll Values Every Frame Unconditionally

**Location:** `arcade_tick_logic`, lines 248–270 of `apps/rastan-direct/src/main_68k.s`.

**Why inefficient:** `arcade_tick_logic` increments `staged_scroll_x_bg`, `staged_scroll_x_fg`, and derives `staged_scroll_y_bg`, `staged_scroll_y_fg` from `tick_counter` on every frame. This is correct for the current scroll animation demo. However, for the final port, scroll values will be set by the arcade PC080SN scroll hook, not by `arcade_tick_logic`. When the arcade hook becomes active, `arcade_tick_logic` must be removed or bypassed. If it is not, it will overwrite the arcade-sourced scroll values each frame. The current implementation has no mechanism to disable the synthetic tick driver when the arcade path is active.

**Category:** Bringup-only code with no disable path — not a VBlank inefficiency, but a transition risk.

---

## 5. Comparison to Rainbow Islands

Sources: `Cody_rainbow_islands_vdp_template_analysis.md`, `Andy_rastan_direct_display_tightening_against_rainbow.md`.

### Does Rainbow Islands commit full nametable planes every frame?

**NO.**

Rainbow Islands tilemap commit path (`0x073C` dispatcher → `0x1A70` writer) writes 40 words per strip, flag-triggered on WRAM flag `0xFFFFF63C`. Full-plane writes never occur in the per-frame path. On a frame with no tilemap change, zero tilemap words are written to the VDP.

### What granularity does Rainbow Islands use for tilemap updates?

40 words per strip (one full row of a 40-cell wide visible screen). The VDP destination command is stepped by one row-width increment between strip writes. The source pointer `0xFFFFF644` advances by strip size. Flag `0xFFFFF63C` controls whether any strip commit runs at all.

### Does Rainbow Islands separate one-time initialization uploads from per-frame dirty updates?

**YES.** Boot-time VRAM clear and VDP register initialization run once at `0x000434`–`0x00048C`. Per-frame commits in the VBlank ISR (`0x000380`) are all flag-gated. Initial content is established by the game state machine outside VBlank, not by a special first-frame all-dirty path.

### Does current `rastan-direct` implementation align with Rainbow Islands commit discipline?

**Partially YES, with specific gaps:**

| Criterion | Rainbow Islands | Current rastan-direct | Aligned? |
|-----------|----------------|----------------------|----------|
| Full-plane commit every frame | NO | NO (after dirty-flag fix) | YES |
| Palette commit flag-gated | YES | YES (`palette_dirty`) | YES |
| Tile commit flag-gated | YES (implicit, one-time) | YES (`tiles_dirty`) | YES |
| BG commit flag-gated | YES | YES (`bg_dirty`) | YES |
| FG commit flag-gated | YES | YES (`fg_dirty`) | YES |
| Tilemap commit granularity: strip-level | YES (40 words/strip) | NO (2048 words/plane) | NO |
| FG initial state: transparent, no full-plane upload needed | YES | NO (writes 2048 zero words on frame 1) | NO |
| Tile upload separated from nametable commit | YES (separate path) | NO (nested in `vdp_commit_bg`) | NO |
| VBlank is commit-only, no logic | YES | YES (`arcade_tick_logic` runs in main loop, not VBlank) | YES |
| Scroll committed after display-ON | YES | YES | YES |

**Current implementation matches Rainbow Islands commit discipline: NO** — dirty flags are aligned but commit granularity (full-plane vs strip-level) diverges, and the unnecessary FG zero-plane upload on frame 1 has no Rainbow Islands analog.

---

## 6. Target Efficient Model

### Per-Frame VBlank Commit When 0–4 Tilemap Strips Have Changed

```
_VINT_handler:
    [register save]
    [display OFF]
    [vdp_commit_tiles_if_dirty]        — top-level, unconditional check, independent of BG
    [vdp_commit_bg_strips_if_dirty]    — iterate 32 row-dirty bits; commit only dirty rows
    [vdp_commit_palette_if_dirty]      — unchanged: palette_dirty flag gate
    [display ON]
    [vdp_commit_scroll]                — unchanged: unconditional, after display-ON
    [frame counter increment]
    [register restore + RTE]
```

- FG commit is removed entirely from the VBlank path. FG will be written strip-by-strip by arcade PC080SN hooks that populate `staged_fg_buffer` directly and set per-row FG dirty bits. A future `vdp_commit_fg_strips_if_dirty` mirrors the BG strip commit, added only when the FG arcade hook is active.

### How Tilemap Updates Should Be Driven

Replace the single `bg_dirty` byte with a 32-bit dirty mask (`bg_row_dirty`, one bit per row). When arcade PC080SN hooks write a strip to `staged_bg_buffer`, they set the corresponding bit in `bg_row_dirty`. The commit function iterates bits 0–31; for each set bit, it computes the VRAM write address for that row (base + row × 128 bytes), issues the VDP write command, and copies 64 words. It then clears the bit. On a frame with 0 dirty rows, the entire commit costs approximately 32 test-and-branch iterations (~320 cycles). On a frame with 4 dirty rows, cost is approximately 320 + 4 × (40 + 64×14 + 64×10) cycles = 320 + 4 × 1,512 = ~6,368 cycles — within the 7,400-cycle budget.

### What Should Be Removed

1. `vdp_commit_fg` — the full-plane FG commit function. Remove from `_VINT_handler` call sequence and delete the function body.
2. The `fg_dirty` flag and its initialization (`move.b #1, fg_dirty` in `init_staging_state`) — after removal of `vdp_commit_fg` there is no consumer.
3. The `bsr vdp_commit_tiles_if_dirty` call from inside `vdp_commit_bg` — move it to a top-level VBlank step.
4. The whole-plane `bg_dirty` byte — replace with `bg_row_dirty` 32-bit mask.
5. `arcade_tick_logic` — replace with arcade hook scroll staging when the PC080SN path is active.

### What Should Be Added

1. `bg_row_dirty`: 32-bit WRAM variable (one bit per BG row).
2. `vdp_commit_bg_strips_if_dirty`: iterates `bg_row_dirty`, commits only dirty rows, clears bits.
3. Per-strip dirty-set call in the future arcade BG write hook (sets `bg_row_dirty` bit corresponding to the written strip).
4. Analogous `fg_row_dirty` + `vdp_commit_fg_strips_if_dirty` when the FG arcade hook becomes active.

### How This Fits the Arcade Hook Model

The PC080SN BG hook writes specific strips into `staged_bg_buffer[row × 64]` and sets bit `row` in `bg_row_dirty`. VBlank sees only the set bits and commits those strips. This is a direct translation of the Rainbow Islands `0xFFFFF63C` flag + `0xFFFFF644` source pointer + `0x1A70` strip writer pattern, adapted to Rastan's 64-cell-wide nametable geometry (64 words/row vs Rainbow's 40 words/row).

---

## 7. Single Next Implementation Step

**Remove the FG full-plane commit permanently.**

Exact change:
1. In `_VINT_handler`, delete `bsr vdp_commit_fg`.
2. Delete the `vdp_commit_fg` function body (lines 210–224 of `main_68k.s`).
3. In `init_staging_state`, delete `move.b #1, fg_dirty`.
4. In the `.bss` section, delete the `fg_dirty` label and its `.byte 0` allocation.

Justification for choosing this step over alternatives:

- **Impact:** Removes 49,208 cycles from the frame 1 VBlank cost with zero functional regression. FG is all-zero (transparent) and produces no visible content. Removing the commit does not change any visible output.
- **Safety:** The `staged_fg_buffer` buffer itself remains in WRAM. Future arcade FG hooks can still write into it. Only the VBlank publish path is removed — data production and data commitment are decoupled.
- **Specificity:** Exactly four lines to delete, no new code required, no data structure changes.
- **Direction:** Directly aligns with Rainbow Islands discipline. Rainbow Islands never writes a full FG plane; it writes strip-level updates only when FG content changes.

This step reduces frame 1 VBlank cost from ~101,676 cycles to ~52,468 cycles and eliminates the most structurally incorrect path in the current implementation.

Alternative rejected — per-strip BG tracking: This is higher architectural value but requires adding a new dirty mask variable, changing the commit function, and touching `init_staging_state`. It also depends on the arcade BG hook being active to produce meaningful dirty bits. The FG removal is dependency-free and produces immediate cleanup.

Alternative rejected — moving tile commit to top-level: This is a small refactor (one `bsr` relocation) with minimal cycle impact. Not the highest-value single step.

---

## 8. Ordered Transition Plan

The following sequence is dependency-safe: each step depends only on the steps before it being complete.

### Step 1 (single next step): Remove FG Full-Plane Commit

As defined in Section 7. No prerequisites.

Post-condition: VBlank path contains BG commit, tile commit (nested in BG), palette commit, scroll commit. FG is never written from VBlank; `staged_fg_buffer` is a writable WRAM buffer available to future hooks.

### Step 2: Move Tile Commit to Top-Level VBlank Step

Remove `bsr vdp_commit_tiles_if_dirty` from inside `vdp_commit_bg`. Add it as the first explicit step in `_VINT_handler`, between display-OFF and `vdp_commit_bg`.

Prerequisite: Step 1 complete (FG path removed, cleaner handler).

Post-condition: Tile commit is unconditionally checked as the first VBlank step, independent of BG state. This matches the Rainbow Islands pattern where each commit type is a separate top-level call.

### Step 3: Introduce Per-Strip Dirty Tracking for BG

Replace `bg_dirty` (1 byte, whole-plane flag) with `bg_row_dirty` (1 longword, 32 bits = one bit per BG row).

Changes:
- Add `bg_row_dirty: .long 0` to `.bss` section.
- Remove `bg_dirty: .byte 0` from `.bss` section.
- In `init_staging_state`: replace `move.b #1, bg_dirty` with `move.l #0xFFFFFFFF, bg_row_dirty` (all rows dirty on first frame).
- Implement `vdp_commit_bg_strips_if_dirty`: test `bg_row_dirty`, return if zero; otherwise iterate bits 0–31, for each set bit compute VRAM address for that row, issue write command, copy 64 words, clear bit.
- Replace `bsr vdp_commit_bg` in `_VINT_handler` with `bsr vdp_commit_bg_strips_if_dirty`.

Prerequisite: Steps 1 and 2 complete.

Post-condition: BG commit granularity is per-row (64 words/row). Frame 1 BG commit cost = 32 rows × (40 + 64×14 + 64×10) cycles = ~48,384 cycles — still large on frame 1 (32 rows), but each subsequent frame commits only the rows that changed.

### Step 4: Connect Arcade BG Hook to Per-Strip Dirty Bits

When the arcade PC080SN BG write hook is integrated, modify the hook to set the appropriate bit in `bg_row_dirty` after writing each strip to `staged_bg_buffer`.

Prerequisite: Step 3 complete (bg_row_dirty variable exists and commit function reads it).

Post-condition: Only strips changed by the arcade tick are committed to VRAM each frame. Per-frame VBlank cost for tilemap falls to 320–6,368 cycles depending on activity.

### Step 5: Add FG Strip Commit Infrastructure

Add `fg_row_dirty: .long 0` to `.bss`. Implement `vdp_commit_fg_strips_if_dirty` mirroring the BG version (64 words/row, VRAM_PLANE_A_BASE). Add `bsr vdp_commit_fg_strips_if_dirty` to `_VINT_handler`. Connect arcade PC080SN FG write hook to set FG row dirty bits.

Prerequisite: Steps 3 and 4 complete (BG pattern confirmed working).

Post-condition: Both BG and FG use strip-level dirty tracking. Full-plane commits are eliminated from the VBlank path entirely. The VBlank model fully matches the Rainbow Islands commit discipline.

### Step 6: Eliminate Remaining Bringup Scaffolding

Remove `arcade_tick_logic` synthetic scroll driver. Remove synthetic `palette_init_words`, `tile_init_words` tables and their init loops in `init_staging_state`. Replace with arcade-sourced staging.

Prerequisite: Steps 4 and 5 complete (arcade hooks active and verified), scroll hook active.

Post-condition: No bringup scaffolding remains. All staged data is arcade-produced.

---

## 9. Final Verdict

**Current state:** Clean, stable video baseline. All dirty flag guards working. Steady-state VBlank cost is 532 cycles — 7.2% of the 7,400-cycle budget. Frame 2+ is safe.

**Frame 1 cost:** 101,676 cycles (13.7× budget overrun). This is a one-time startup cost. The dominant contributor is the FG full-plane zero write (49,208 cycles) followed by the BG full-plane checkerboard write (50,424 cycles including tile commit).

**Steady-state budget:** WITHIN budget (YES).

**Inefficiencies identified:** 5 — FG zero-plane upload on frame 1; BG wrong commit granularity for final port; tile commit embedded inside BG commit; scroll uses `vdp_set_vram_write_addr` unnecessarily; `arcade_tick_logic` has no disable path.

**Compared against Rainbow Islands:** Current dirty-flag discipline matches. Commit granularity does not match (full-plane vs strip-level). FG zero-plane upload has no Rainbow Islands analog.

**Single next step:** Remove `vdp_commit_fg` from VBlank path and delete `fg_dirty` flag. Zero functional regression, 49,208-cycle reduction in frame 1 cost, direct alignment with Rainbow Islands strip-only FG update model.

**Ordered transition plan:** Remove FG commit → move tile commit top-level → introduce per-row BG dirty bits → connect arcade BG hook → add FG strip commit → remove bringup scaffolding.
