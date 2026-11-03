# Andy — FG Regression After vdp_commit_fg Removal

## 1. Executive Summary

After Cody removed `vdp_commit_fg` and `fg_dirty` from `apps/rastan-direct/src/main_68k.s`,
new blue/garbage artifacts appeared on the FG plane (Plane A). This document identifies the
exact cause: Plane A VRAM is never initialized to all-zero after the removal. Genesis VRAM
contains undefined data at power-on. The `staged_fg_buffer` in WRAM is correctly zeroed by
`init_staging_state`, but without `vdp_commit_fg` no code path transfers that zeroed data to
Plane A VRAM. The VDP renders whatever was in VRAM at power-on — undefined/garbage tiles that
appear as blue or colored artifacts.

The correct fix is a one-time CPU write of 4096 zero bytes to Plane A VRAM (VRAM_PLANE_A_BASE
= 0xE000, 2048 words of 0x0000) during initialization, outside VBlank. This runs once, takes
approximately 49,200 cycles at init time (non-VBlank, no budget constraint), and produces zero
steady-state VBlank cost. Efficiency is preserved exactly.

---

## 2. Inputs Audited

| File | Status |
|------|--------|
| `apps/rastan-direct/src/main_68k.s` | READ COMPLETE — 376 lines, current state post-removal |
| `apps/rastan-direct/src/boot/boot.s` | READ COMPLETE — 55 lines |
| `docs/design/Cody_remove_fg_full_plane_commit.md` | READ COMPLETE |
| `docs/design/Andy_vblank_efficiency_audit_and_transition_plan.md` | READ COMPLETE |
| `docs/design/Andy_verify_fg_top_band_artifact.md` | READ COMPLETE |

---

## 3. FG VRAM Ownership Analysis

### Task: Is there ANY code path that writes FG nametable data to Plane A VRAM after the removal?

**`_VINT_handler` (current, post-removal):**
```
_VINT_handler:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    move.w  VDP_CTRL, %d0
    [display OFF]
    bsr     vdp_commit_bg          ; writes Plane B (0xC000) only
    tst.b   palette_dirty
    beq.s   .Lskip_palette
    bsr     vdp_commit_palette     ; writes CRAM only
    clr.b   palette_dirty
.Lskip_palette:
    [display ON]
    bsr     vdp_commit_scroll      ; writes HScroll table and VSRAM only
    addq.w  #1, frame_counter
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rte
```

There is no call to `vdp_commit_fg`. The `vdp_commit_fg` function no longer exists. No other
function in `_VINT_handler` writes to VRAM_PLANE_A_BASE (0xE000).

**`vdp_boot_setup`:** Sets VDP registers only (mode, plane base addresses, etc.). Does not
write any VRAM data. No VRAM data write of any kind.

**`boot.s` (`_start`):** TMSS write and jump to `main_68k`. No VRAM write. No VRAM clear.

**`init_staging_state`:** Zeroes `staged_fg_buffer` in WRAM (the `.Lfg_clear` loop). Does NOT
write to VDP. WRAM clearing has no effect on VRAM.

**`arcade_tick_logic`:** Updates scroll staging values in WRAM only. No VDP writes.

**Conclusion: No code path writes FG nametable data to Plane A VRAM after removal.**

### Does the boot sequence clear VRAM?

`boot.s` performs no VRAM clear. `vdp_boot_setup` sets VDP registers but issues no VRAM write
commands. No loop writes zero data to any VRAM range. VRAM is never cleared at boot.

### Does any initialization routine explicitly write transparent tiles to Plane A?

No. `init_staging_state` zeroes `staged_fg_buffer` in WRAM but does not transfer that data to
the VDP. The only code that previously transferred `staged_fg_buffer` to Plane A VRAM was
`vdp_commit_fg`, which has been removed.

### Power-on state of Genesis VRAM

Genesis VRAM is undefined at power-on. It contains whatever values are in the RAM cells after
power ramp-up — typically a mix of 0x0000, 0xFFFF, and semi-random patterns depending on the
IC state at startup. The VDP renders these undefined values as tile indices and palette
selections, producing garbage/colored output. VRAM is not zero-initialized by any hardware
mechanism on the Genesis.

### Answer

**FG VRAM deterministically initialized: NO**

After removing `vdp_commit_fg`, Plane A VRAM is never written. It contains undefined power-on
data from the first frame through all subsequent frames.

---

## 4. FG Data Flow Analysis

### Is `staged_fg_buffer` initialized to all-zero?

Yes. `init_staging_state` contains the `.Lfg_clear` loop:
```asm
    lea     staged_fg_buffer, %a0
    move.w  #(2048 - 1), %d7
.Lfg_clear:
    clr.w   (%a0)+
    dbra    %d7, .Lfg_clear
```
This writes 2048 zero words (4096 bytes) to `staged_fg_buffer` in WRAM. After this loop,
WRAM contains the correct transparent data for all 2048 FG nametable entries.

### Is there any path that transfers `staged_fg_buffer` to Plane A VRAM?

No. The only function that ever performed this transfer was `vdp_commit_fg`:
```asm
; (removed by Cody)
vdp_commit_fg:
    tst.b   fg_dirty
    beq.s   .Lfg_done
    move.l  #VRAM_PLANE_A_BASE, %d0
    bsr     vdp_set_vram_write_addr
    lea     staged_fg_buffer, %a0
    move.w  #(2048 - 1), %d7
.Lfg_copy:
    move.w  (%a0)+, VDP_DATA
    dbra    %d7, .Lfg_copy
    clr.b   fg_dirty
.Lfg_done:
    rts
```
This function and its call site in `_VINT_handler` were both removed. No replacement exists.
No other function reads from `staged_fg_buffer` and writes to VDP_DATA targeting Plane A.

### What Plane A VRAM contains now

Plane A VRAM (0xE000–0xEFFF) contains undefined power-on data — never overwritten by any
code path in the current implementation. The VDP renders this as garbage tiles.

### Answer

**FG WRAM → VRAM publish path exists: NO**

`staged_fg_buffer` is correctly zeroed in WRAM, but no path transfers it to Plane A VRAM.

---

## 5. Root Cause of Regression

After removing `vdp_commit_fg`, Plane A VRAM is never initialized. Genesis VRAM at power-on
contains undefined data. `staged_fg_buffer` in WRAM is correctly zeroed by the `.Lfg_clear`
loop in `init_staging_state`, but that WRAM buffer is never committed to Plane A VRAM. The VDP
renders the undefined VRAM contents at 0xE000–0xEFFF as garbage/colored tiles, producing the
blue and garbage FG artifacts visible after the removal.

The prior `vdp_commit_fg` path fired exactly once (on frame 1, when `fg_dirty=1`) and wrote
all 2048 zero words from `staged_fg_buffer` to Plane A VRAM, establishing the known-good
transparent state. Removing the path without providing an alternative initialization write left
Plane A VRAM permanently undefined.

---

## 6. Correct Architectural Model for FG

### Rainbow Islands alignment requirement

In Rainbow Islands, FG (Plane A) displays arcade-driven PC080SN strip/overlay content. At
startup, FG must be all-transparent (tile 0, all entries = 0x0000) until arcade FG hooks write
strip data. The correct model has two phases:

1. **Init phase (once, at boot, outside VBlank):** Plane A VRAM is explicitly cleared to
   all-zero. This establishes the transparent baseline. The CPU writes 2048 words of 0x0000
   directly to the VDP targeting VRAM_PLANE_A_BASE (0xE000). This runs once, before the main
   loop, and costs approximately 49,200 cycles — acceptable at init time since VBlank is not
   active and the display is still OFF.

2. **Per-frame VBlank phase (steady-state):** VBlank never touches FG VRAM except when arcade
   FG strip hooks fire. Strip hooks set per-row FG dirty bits; a future
   `vdp_commit_fg_strips_if_dirty` reads those bits and commits only the changed rows. Until
   arcade hooks are active, VBlank touches FG VRAM zero times per frame.

### Which option is correct

**Option (a) / (c) — a one-time VRAM clear of Plane A during boot init, before the main loop,
outside VBlank, using a CPU VRAM write loop.**

Option (b) — restoring `vdp_commit_fg` with `fg_dirty` — is architecturally incorrect. It
places a 49,200-cycle full-plane write in the VBlank path and requires the dirty flag mechanism
to guarantee it fires exactly once. This is structurally equivalent to the removed code: it
rewrites 2048 words per commit event, which is never the correct granularity for the final
port. It also reintroduces the inefficiency that was deliberately removed.

The correct model is: the init-time VRAM clear is not a VBlank operation at all. It is a
boot-time side effect of establishing the known hardware state. VBlank is a commit-only path
for changes produced by arcade hooks; the FG clear is not a "change" — it is initialization.

### Correct architectural model

ONE-TIME FG VRAM clear at init, outside VBlank, using CPU VRAM write loop. After this,
VBlank never touches FG VRAM except when arcade strip hooks set per-row dirty bits.

---

## 7. Single Next Correction

### File

`apps/rastan-direct/src/main_68k.s`

### Location

In `init_staging_state`, immediately after the `.Lfg_clear` loop (which zeroes `staged_fg_buffer`
in WRAM), and before the `clr.w staged_scroll_x_bg` line that follows. Alternatively, at the
end of `vdp_boot_setup` while the display is still OFF. Either location is acceptable; within
`init_staging_state` after `.Lfg_clear` is the most coherent placement because it follows
immediately from the buffer zeroing and mirrors what the zeroing is conceptually preparing.

### What

A CPU VRAM write loop that writes 2048 words of 0x0000 directly to Plane A VRAM:

1. Set VDP write address to VRAM_PLANE_A_BASE (0xE000) using `vdp_set_vram_write_addr`.
2. Load 2048-1 into a counter register.
3. Loop: write 0x0000 to VDP_DATA and decrement counter until done.

This is structurally identical to the inner loop of the removed `vdp_commit_fg` but runs once
at init time, not in VBlank. Auto-increment register must be 2 (already set by `vdp_boot_setup`
via `VDP_REG_AUTOINC = 0x02`).

### Why this preserves efficiency

The write runs once during `init_staging_state`, before interrupts are enabled and before the
main loop starts. Frame 1 VBlank cost is unchanged from the current post-removal state — there
is no call to this init write from VBlank. Frame 2+ steady-state VBlank cost is also unchanged
(~532 cycles). The init write costs approximately 49,200 cycles at startup during display-OFF,
which is outside any VBlank budget window.

---

## 8. Efficiency Impact Analysis

### Frame 1 VBlank cost after fix

The fix is an init-time write, not a VBlank write. The VBlank handler (`_VINT_handler`) after
the fix contains: display OFF, `vdp_commit_bg` (fires on frame 1 for BG), palette commit (fires
on frame 1), display ON, `vdp_commit_scroll`. FG VRAM has already been cleared during
`init_staging_state` before the first interrupt fires. Frame 1 VBlank cost is exactly the same
as in the current post-removal state.

Current post-removal frame 1 VBlank cost (from `Andy_vblank_efficiency_audit_and_transition_plan.md`,
minus the 49,208-cycle FG path): approximately 52,468 cycles. The fix does not change this.

### Frame 2+ steady-state cost

No change. VBlank never touches Plane A VRAM in the steady state. Steady-state cost remains
approximately 532 cycles (from the audit).

### VBlank budget

7,400 cycles. Steady-state: 532 cycles (7.2% of budget). Fix does not alter this.

### Summary table

| Phase | Cost (pre-fix removal) | Cost (post-fix) | Change |
|-------|----------------------|-----------------|--------|
| Init write (outside VBlank) | 0 | ~49,200 cycles | +49,200 (init only, not budgeted) |
| Frame 1 VBlank | ~52,468 cycles | ~52,468 cycles | NONE |
| Frame 2+ VBlank | ~532 cycles | ~532 cycles | NONE |
| VBlank budget consumed | 7.2% | 7.2% | NONE |

### Answer

**Efficiency preserved: YES**

---

## 9. Final Verdict

| Task | Result |
|------|--------|
| FG VRAM deterministically initialized after removal | NO — Plane A VRAM is never written; contains undefined power-on data |
| FG WRAM → VRAM publish path exists after removal | NO — `vdp_commit_fg` removed; no replacement; `staged_fg_buffer` never sent to VDP |
| Root cause of regression | After removing `vdp_commit_fg`, Plane A VRAM is never initialized; Genesis VRAM at power-on contains undefined data; `staged_fg_buffer` is correctly zeroed in WRAM but never committed to VRAM; Plane A displays undefined VRAM contents as garbage/blue tiles |
| Correct FG architectural model defined | YES — one-time CPU VRAM clear of Plane A at init, outside VBlank; VBlank never touches FG until arcade strip hooks are active |
| Single next correction | Add a one-time 2048-word zero write to Plane A VRAM (0xE000) inside `init_staging_state` after the `.Lfg_clear` loop, outside VBlank, before main loop starts |
| Efficiency preserved | YES — init write is outside VBlank budget; frame 1 and frame 2+ VBlank costs unchanged |
| No implementation performed | YES |
