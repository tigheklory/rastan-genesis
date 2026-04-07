# Andy — rastan-direct Display Tightening Against Rainbow Islands

---

## 1. Executive Summary

Cody's current `apps/rastan-direct/` VBlank handler writes 4096 words of nametable data
unconditionally every frame via CPU copy loops, consuming approximately 57,000 CPU cycles against
a 7,400-cycle VBlank budget. Display-ON fires approximately 50,000 cycles after VBlank ends. This
produces a white or black display (CRAM[0] as background color) for the entire visible frame,
regardless of whether tile and palette data are otherwise correct.

Rainbow Islands Genesis's VBlank handler performs partial/strip-level tilemap updates (CPU direct
port writes, 40 words per strip, flag-triggered), uses DMA for SAT and tile-data bulk transfers
(flag- or unconditional-triggered), and writes scroll from a single WRAM long after display
re-enable. Its VBlank work fits within the available window. Cody's current backbone does not
match this discipline.

The single most important porting lesson: Rainbow Islands never writes a full 4096-word plane
unconditionally. All tilemap updates are strip-level, flag-triggered, and commit only the changed
data. This granularity discipline is what keeps the VBlank budget within bounds.

The single next implementation target: add `bg_dirty` and `fg_dirty` flags with the same
guard pattern as the existing `palette_dirty` and `tiles_dirty` flags, so the nametable CPU copy
loops execute only on the first VBlank and are skipped on all subsequent frames where the arcade
tick has not dirtied the buffers. This drops per-frame VBlank cost from approximately 57,000
cycles to approximately 200 cycles and allows display-ON to fire inside VBlank from frame 2
onward.

---

## 2. Inputs Audited

1. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/main_68k.s` — READ COMPLETE
2. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s` — READ COMPLETE
3. `/home/tighe/projects/rastan-genesis/docs/design/Andy_audit_of_cody_rastan_direct_video_backbone.md` — READ COMPLETE
4. `/home/tighe/projects/rastan-genesis/docs/design/Andy_post_plane_b_fix_palette_audit.md` — READ COMPLETE
5. `/home/tighe/projects/rastan-genesis/docs/design/Andy_rastan_direct_video_bringup_plan.md` — READ COMPLETE
6. `/home/tighe/projects/rastan-genesis/docs/design/Cody_rastan_direct_video_backbone_bringup.md` — READ COMPLETE
7. `/home/tighe/projects/rastan-genesis/docs/design/Cody_plane_b_base_fix.md` — READ COMPLETE
8. `/home/tighe/projects/rastan-genesis/docs/design/Cody_rainbow_islands_vdp_template_analysis.md` — READ COMPLETE
9. `/home/tighe/projects/rastan-genesis/docs/design/Cody_rastan_vs_rainbow_tilemap_mismatch.md` — READ COMPLETE
10. `/home/tighe/projects/rastan-genesis/docs/design/rainbow_islands_vs_rastan_vdp_vram_buffering_comparative_trace.md` — READ COMPLETE
11. `/home/tighe/projects/rastan-genesis/docs/design/build316_vs_rainbow_islands_genesis_vblank_noninterrupt_vdp_report.md` — READ COMPLETE (first 150 lines)
12. `/home/tighe/projects/rastan-genesis/apps/rastan/src/boot/sega.s` — READ COMPLETE
13. `/home/tighe/projects/rastan-genesis/apps/rastan/src/startup_trampoline.s` — READ COMPLETE (first 400 lines, sprite SAT path)

---

## 3. Current Display Commit Cost

All figures are from direct inspection of `main_68k.s` and the cycle accounting in
`Andy_post_plane_b_fix_palette_audit.md`.

### VBlank Handler Sequence

```
_VINT_handler:
    movem.l %d0-%d7/%a0-%a6, -(%sp)    ; register save: ~108 cycles
    move.w  VDP_CTRL, %d0              ; VDP status read: ~8 cycles
    moveq #VDP_REG_MODE2 / moveq #0x34 ; display OFF: ~8 cycles
    bsr vdp_set_reg                    ; display OFF setup: ~16 cycles
    bsr vdp_commit_bg                  ; <<< DOMINANT COST
    bsr vdp_commit_fg                  ; <<< DOMINANT COST
    [optional] bsr vdp_commit_palette  ; palette commit (frame 1 only)
    moveq #VDP_REG_MODE2 / moveq #0x74 ; display ON: ~8 cycles
    bsr vdp_set_reg                    ; display ON: ~16 cycles
    bsr vdp_commit_scroll              ; scroll: ~80 cycles
    addq.w #1, frame_counter           ; ~8 cycles
    movem.l (%sp)+, %d0-%d7/%a0-%a6   ; register restore: ~108 cycles
    rte                                ; ~20 cycles
```

### BG Commit Cost (`vdp_commit_bg`)

- Calls `vdp_commit_tiles_if_dirty` first: on frame 1 this writes 48 words (48 × 14 cycles
  ≈ 672 cycles); on subsequent frames skipped (branch taken in ~8 cycles).
- Sets VDP VRAM write address for 0xC000: ~40 cycles for `vdp_set_vram_write_addr`.
- Inner loop: `move.w (%a0)+, VDP_DATA` / `dbra %d7, .Lbg_copy` — 2048 iterations.
  - Per iteration: move.w from WRAM to VDP DATA (approximately 14 cycles) + dbra (10 cycles) = 24 cycles.
  - Total inner loop: 2048 × 24 cycles = 49,152 cycles.
  - Note: the VDP DATA write itself stalls the CPU on each access due to FIFO fill time;
    a more conservative accounting of 14 cycles per word (4-cycle fetch + write + VDP bus) gives
    2048 × 14 = 28,672 cycles for the write sequence alone. The prior audit used 14 cycles/word.
- **BG commit total: approximately 28,672 cycles (writes only; with overhead ~29,400 cycles).**

### FG Commit Cost (`vdp_commit_fg`)

- No tile commit.
- Sets VDP VRAM write address for 0xE000: ~40 cycles.
- Inner loop: 2048 iterations, same per-iteration cost.
- **FG commit total: approximately 28,672 cycles (writes only; with overhead ~29,400 cycles).**

### Palette Commit Cost (`vdp_commit_palette`)

- Conditional on `palette_dirty` flag: checked each frame.
- When flag is set: CRAM write command (8 cycles) + 64 × 14 cycles = 896 cycles.
- After first frame: skipped (the flag is never reset to 1 after init in current code).
- **Palette commit cost: 896 cycles on frame 1; 0 cycles thereafter.**

### Scroll Commit Cost (`vdp_commit_scroll`)

- One `vdp_set_vram_write_addr` call for HScroll table: ~40 cycles.
- Two word writes (FG X, BG X) to VDP DATA: ~28 cycles.
- One VDP control word write for VSRAM address: ~8 cycles.
- Two word writes (FG Y, BG Y) to VDP DATA: ~28 cycles.
- **Scroll commit total: approximately 104 cycles.**

### Display OFF/ON Overhead

- Display OFF: `vdp_set_reg` via BSR: load two moveq + lsl + or + ori + move.w to CTRL + rts = approximately 40 cycles.
- Display ON: same, approximately 40 cycles.
- **Display OFF/ON bracket overhead: approximately 80 cycles.**

### Total Estimated VBlank Cost

| Component | Cycles (steady state, frame 2+) | Cycles (frame 1) |
|-----------|--------------------------------|-----------------|
| Register save | ~108 | ~108 |
| VDP status read | ~8 | ~8 |
| Display OFF | ~40 | ~40 |
| vdp_commit_bg | ~29,400 | ~30,072 (+ tile commit) |
| vdp_commit_fg | ~29,400 | ~29,400 |
| Palette commit | 0 | ~896 |
| Display ON | ~40 | ~40 |
| Scroll commit | ~104 | ~104 |
| Frame counter + overhead | ~40 | ~40 |
| Register restore + RTE | ~128 | ~128 |
| **Total** | **~59,268 cycles** | **~60,836 cycles** |

**VBlank budget: approximately 7,400 cycles (NTSC, 224-line mode).**

**Overrun: approximately 7.9× budget.**

**Display-ON fires approximately 50,000 cycles after VBlank ends (confirmed by prior audit).**

Current VBlank work fully characterized: **YES**

---

## 4. Exact Wasted Work in Current Implementation

### Category 1: Full-Plane Unconditional CPU Writes Every Frame (STRUCTURAL WRONG)

`vdp_commit_bg` writes all 2048 words of `staged_bg_buffer` to VRAM 0xC000 every VBlank without
exception. `vdp_commit_fg` does the same for `staged_fg_buffer` to VRAM 0xE000.

Neither function checks a dirty flag before committing. This is the dominant cost: approximately
57,344 cycles per frame for the two CPU copy loops, against a 7,400-cycle budget.

In the bringup scaffold, the staged buffers contain static synthetic content (checkerboard fill
and FG row-0 stripe). The content does not change frame-to-frame. Rewriting all 4096 words every
VBlank when only 0 words have changed is pure waste.

Classification: **structural wrong for final port** — in the final port, full-plane writes every
frame will also be wrong because the arcade tick will modify only changed strips, not the entire
plane.

### Category 2: No Dirty Flags for BG and FG Nametables (IMMEDIATE FIX NEEDED)

The `palette_dirty` and `tiles_dirty` flags are present and working. The `vdp_commit_tiles_if_dirty`
function demonstrates the correct pattern: check flag, skip if clear, commit if set, clear flag.

`vdp_commit_bg` and `vdp_commit_fg` lack equivalent guards. This is the entire gap between the
current ~59,000 cycle per-frame cost and the corrected ~200 cycle per-frame cost (scroll + overhead
only, after initial commit).

Classification: **temporary bring-up waste** — fixable immediately without restructuring anything.

### Category 3: Wrong Commit Granularity for Final Port (STRUCTURAL WRONG FOR FINAL PORT)

Even with dirty flags, writing all 2048 words per dirty flag set is the wrong granularity for
the final port. When the arcade tick runs, it will dirty at most a handful of tilemap strips per
frame (the PC080SN updates strips, not full planes). The Rainbow Islands pattern — and the correct
final-port architecture — commits only the strips that changed, not the entire nametable.

The `staged_bg_buffer` and `staged_fg_buffer` arrays are full 64×32 nametables (2048 words each).
In the final port, only the words that the arcade's PC080SN hook has written in the current frame
need to be committed. Full-plane writes are approximately 40–100× more work than strip-level
updates for typical arcade game frames.

Classification: **structurally wrong for final port** — but not the immediate fix target.

### Category 4: Synthetic Data Producers (BRINGUP ONLY)

`init_staging_state` fills both nametable buffers with synthetic content (checkerboard, FG stripe).
`arcade_tick_logic` updates only scroll counters. No arcade ROM, no PC080SN hooks, no real
nametable producers.

Classification: **bring-up only** — documented by Cody as BRINGUP_ONLY scaffolding.

### Category 5: `vdp_commit_scroll` Called After Display-ON (INTENTIONAL, CORRECT)

Scroll is committed after display-ON, unconditionally, every frame. This matches the Rainbow
Islands commit order (confirmed by `Cody_rainbow_islands_vdp_template_analysis.md` and
`rainbow_islands_vs_rastan_vdp_vram_buffering_comparative_trace.md`). This is not waste.

### Category 6: Display OFF/ON Bracket Around Unconditional Full-Plane Writes (CONSEQUENTIAL WRONG)

The display OFF bracket is placed before `vdp_commit_bg` and `vdp_commit_fg`. Because those
writes consume 57,000 cycles — approximately 7.9× the available VBlank window — the display-ON
write fires approximately 50,000 cycles into active display, not at the end of VBlank. For 224-
line NTSC, approximately 192 out of 224 visible scanlines are rendered with display-enable = 0
(showing CRAM[0] = 0x0EEE = white from emulator power-on).

The display OFF/ON pattern is correct in structure. The problem is not the bracket; the problem
is what is bracketed (unconditional full-plane writes instead of dirty-only partial writes).

Classification: **consequential wrong** — fixing the commit cost resolves this automatically.

Exact wasted work identified: **YES**

---

## 5. Comparison Against Rainbow Islands Genesis Display Behavior

Sources: `Cody_rainbow_islands_vdp_template_analysis.md`,
`rainbow_islands_vs_rastan_vdp_vram_buffering_comparative_trace.md`,
`build316_vs_rainbow_islands_genesis_vblank_noninterrupt_vdp_report.md`.

### Does Rainbow Islands commit full planes every frame?

**NO.**

Rainbow Islands Genesis tilemap commit path (`0x073C` dispatcher → `0x1A70` writer) writes tilemap
data in strip-sized partial updates, not full-plane writes. The strip writer at `0x1A70` writes 40
words per strip in a tight `dbf` loop. The dispatch at `0x073C` is flag-triggered on WRAM flag
`0xFFFFF63C`. If the flag is clear, no tilemap write occurs. If set, only the requested strips
are written.

### Tilemap update granularity

40 words per strip (one full row of a 40-cell wide screen). The VDP destination command is
stepped by one row increment (`+0x800000` in the destination command) between strip writes.
The source pointer (`0xFFFFF644`) advances by strip size. Flag `0xFFFFF63C` is cleared after
commit. On a typical frame with no tilemap change, zero tilemap words are written to the VDP.

This is approximately 40–51× smaller per-update than Cody's current 2048-word plane commits.

### Palette commit timing

Palette commit (`0x07BE`) is flag-triggered on `0xFFFFF680`. It runs inside the VBlank display-OFF
bracket (before display re-enable at `0x03D2`). When not flagged, the palette code path is skipped
in approximately 8 cycles (flag test + conditional branch). The commit itself decompresses palette
to WRAM staging first, then streams 64 words to CRAM. Commit executes with display disabled.

### Scroll commit timing

Scroll commit executes **after display re-enable** via a single longword write:
```
move.l #0x40000010, 0xC00004    ; VSRAM write command
move.l (0xFFFFF630), 0xC00000   ; write scroll values from WRAM
```
This writes VSRAM offset 0 (H and V scroll packed), unconditionally, every frame. Total cost: two
port writes = approximately 24 cycles. This is safe after display re-enable because VSRAM writes
are internally double-buffered and do not corrupt the current scanline's scroll state.

### Display-off/on bracket

YES. Rainbow Islands disables display (VDP reg 1 bit 6 = 0) using the shadow register at
`0xFFFFF624` before any DMA or VRAM writes. It re-enables display (bit 6 = 1) after all tile
DMA, SAT DMA, tilemap row writes, and palette writes are complete. Scroll is then written after
display re-enable (before RTE).

The bracket covers: tile DMA, SAT DMA, tilemap strip copies, palette upload.
The bracket does NOT cover: scroll write (written after display-ON).

### VBlank ownership model

Rainbow Islands VBlank handler (`0x0380`) is **commit-only**. No game logic executes inside
VBlank. Game logic runs in the main loop at `0x11D2`, which frame-syncs by polling the frame
counter at `0xFFFFF620`. VBlank increments the counter, triggers input read, and performs all
hardware commits. Main loop executes entirely outside the interrupt.

Cody's current rastan-direct structure **matches this VBlank ownership model**:
- Main loop (`arcade_tick_logic`) writes only WRAM staging fields.
- `_VINT_handler` is the sole VDP commit owner.
- Frame counter is incremented inside VBlank; main loop polls it.

The structure is correct. The commit granularity is wrong.

Rainbow Islands timing/commit model compared directly: **YES**

---

## 6. DMA Use in Rainbow Islands Genesis

Sources: `Cody_rainbow_islands_vdp_template_analysis.md`,
`rainbow_islands_vs_rastan_vdp_vram_buffering_comparative_trace.md`.

### Tilemap/plane updates use DMA: NO

Rainbow Islands writes tilemap data via CPU direct port writes (`0xC00004`/`0xC00000`), not DMA.
The strip writer at `0x1A70` uses a tight `dbf` loop writing 40 words per iteration to the VDP
data port. DMA is not used for nametable plane updates in Rainbow Islands Genesis.

Reason: tilemap updates are partial (strip-level) and the data source is already in WRAM staging
with a pre-computed VDP destination command. CPU port writes for small quantities (40 words =
80 bytes per strip) are faster to set up than DMA (which requires 5 register writes before
triggering). DMA amortizes its setup cost only for larger transfers.

### Sprite/SAT publication uses DMA: YES

Rainbow Islands `0x06B0` configures DMA registers (`0x93xx`/`0x94xx`/`0x95xx`/`0x96xx`/`0x97xx`)
and issues the SAT destination command with DMA trigger bit. DMA transfers the full SAT shadow
from WRAM `0xFFFFF800` (80 sprites × 8 bytes = 640 bytes = 320 words) to VDP SAT (`0xF800`).

Reason: SAT must be committed atomically — the VDP must see a complete, consistent SAT at the
start of each frame's sprite render. DMA transfers 320 words without any CPU overhead per word.
The 68000 is free during DMA (except for DTACK-stalled VDP bus accesses). CPU-loop writing 320
individual SAT entries with per-entry VDP address setup would be slower and non-atomic.

### Palette/CRAM updates use DMA: NO (in the direct streaming path)

The evidence from `rainbow_islands_vs_rastan_vdp_vram_buffering_comparative_trace.md` (Section 4)
shows palette upload at `0x07BE` uses direct VDP DATA writes (`move.w (%a2)+, (%a3)` in a `dbf`
loop), not DMA. The palette is first decompressed/copied to a WRAM staging area at `0xFF0000`,
then streamed word-by-word to CRAM.

Note: `Cody_rainbow_islands_vdp_template_analysis.md` describes the palette commit at `0x085A`
as using "DMA register setup writes (`0x93xx`..`0x97xx`) then wait loop on VDP status bit."
There is a discrepancy in which routine is the actual CRAM writer between the two analysis
documents. The `0x085A` routine (flagged at `0xFFFFF690`) is identified as tile DMA in the
comparative trace. The `0x07BE` routine (flagged at `0xFFFFF680`) is identified as palette
upload. The tile DMA path at `0x085A` does use DMA register setup (it is a tile data DMA, not
a palette DMA). Palette/CRAM data itself is small (64 words = 128 bytes) and is written via
CPU direct port writes.

### Scroll/VSRAM or HScroll updates use DMA: NO

Scroll is written via two direct port writes after display re-enable. VSRAM holds H/V scroll
data. Total scroll write is one longword to the VDP control port and one longword to the data
port = 4 port accesses. DMA is not used for scroll.

Reason: scroll is 2 words of H/V data per frame. DMA setup overhead exceeds the write cost for
2 words. Direct CPU writes are correct for this quantity.

---

## 7. Correct DMA Policy for `rastan-direct`

### BG nametable updates: MUST NOT USE DMA (in current bringup phase) / MAY USE DMA LATER

In the final port, BG nametable updates from the arcade PC080SN hook will produce strip-level
changes (typically 1–32 strips per frame, each strip = 64 words for a 64-wide plane). CPU direct
port writes in a tight loop are correct for strip-level updates, as demonstrated by Rainbow
Islands. DMA for nametable updates adds 5-register setup cost that is not amortized by the small
transfer size. In the bringup scaffold (single full-plane write on first frame only, after
dirty-flag fix), CPU direct port writes are correct.

**Classification: MUST NOT USE DMA for strip-level nametable updates. MAY USE DMA for a one-time
full-plane clear or one-time full-plane write during boot.**

### FG nametable updates: MUST NOT USE DMA (same reasoning as BG)

Same as BG. Strip-level updates via CPU direct port writes.

**Classification: MUST NOT USE DMA for strip-level nametable updates.**

### Sprite tile uploads: MUST USE DMA

When the sprite pipeline is activated (Phase 4), tile data must be DMA'd from ROM to VRAM for
each visible sprite. This is exactly what `genesistan_render_sprites_vdp_asm` does in
`startup_trampoline.s`. DMA is correct here because: (a) each sprite tile transfer is 128 bytes
(64 words), (b) multiple sprites require multiple DMA operations, (c) DMA allows the CPU to
overlap other work, and (d) Rainbow Islands uses the same DMA-for-tiles pattern.

**Classification: MUST USE DMA.**

### SAT publication: MUST USE DMA

SAT must be committed atomically every frame. DMA from a WRAM shadow buffer to VDP SAT at
`0xF800` matches Rainbow Islands exactly. In the current scaffold, no sprite path exists; when
it is implemented, the SAT DMA pattern from `startup_trampoline.s` (adapted for rastan-direct)
is the correct approach.

**Classification: MUST USE DMA.**

### Palette/CRAM updates: MUST NOT USE DMA

64 words = 128 bytes. DMA setup overhead is not amortized at this size. CPU direct port writes
(as used in both Rainbow Islands and Cody's current `vdp_commit_palette`) are correct. The
current implementation is right.

**Classification: MUST NOT USE DMA.**

### Scroll/VSRAM/HScroll updates: MUST NOT USE DMA

2–4 words total. Direct port writes are correct. Rainbow Islands uses direct port writes for
scroll. The current `vdp_commit_scroll` is correct in mechanism.

**Classification: MUST NOT USE DMA.**

### One-time startup tile uploads: MAY USE DMA (but not required)

The boot sequence writes tile pixel data (3 tiles = 48 words) to VRAM. This is small enough for
CPU direct port writes (`vdp_commit_tiles_if_dirty`). When the arcade ROM tile set is integrated,
a bulk upload of scene tiles (slots 20–1023 = ~16 KB) should use DMA for efficiency. For the
current scaffold, CPU writes are acceptable.

**Classification: MAY USE DMA LATER BUT NOT IN NEXT STEP.**

---

## 8. Current DMA Misuse / Non-Use Assessment

Cody's current code uses CPU loops for all VRAM writes. There is no DMA in the current rastan-
direct implementation (the `sprite_dma_addr_high_bits_fix` helper exists but is uncalled; no
DMA registers are written by any active code path).

The current failure mode is **not DMA misuse**. The failure is:

1. **CPU loops used where they are correct in mechanism but wrong in scope**: CPU direct port
   writes are the correct mechanism for nametable commits and palette commits. The error is
   performing a full 2048-word CPU loop unconditionally every frame, rather than a zero-word
   or strip-sized loop gated by dirty flags. DMA would not fix this — a 2048-word DMA every
   frame would also overrun the VBlank budget. The fix is granularity control, not switching
   to DMA.

2. **DMA not used where Rainbow Islands would**: Sprite tile uploads and SAT publication are
   deferred (Phase 4 not yet implemented). When sprites are added, DMA must be used for tiles
   and SAT. This is not a current error because sprites are not yet active.

3. **Work performed at wrong granularity regardless of DMA**: Full-plane writes (2048 words) vs
   strip-level writes (40–64 words when dirty) is the core granularity error.

**Exact role DMA should play in fixing the current VBlank overrun**: DMA plays no role in
fixing the immediate VBlank overrun. The overrun is caused by unconditional full-plane CPU loops,
not by absence of DMA. Adding `bg_dirty`/`fg_dirty` flags to gate the existing CPU loops is the
correct fix, not replacing them with DMA.

Current DMA misuse / non-use assessed: **YES**

---

## 9. Single Next DMA-Related Instruction for Cody

**Do not add DMA to fix the current VBlank overrun. Add `bg_dirty` and `fg_dirty` flags to gate
the existing CPU copy loops so they fire only when the arcade tick has set the dirty flags.**

---

## 10. Rainbow Islands Arcade-to-Genesis Translation Discipline

Sources: `rainbow_islands_vs_rastan_vdp_vram_buffering_comparative_trace.md` Section 5 and 9.

### Core Translation Strategy

Rainbow Islands arcade used a cooperative task scheduler (TRAP #1 dispatch). Game logic tasks ran
between VBlanks as scheduled tasks. The VBlank interrupt merely woke the scheduler. The arcade
hardware (PC080SN, PC090OJ) accepted CPU writes at any time and rendered asynchronously.

Rainbow Islands Genesis rewrote the game to use Genesis VDP primitives. The key translation
discipline:

1. **No direct-to-VDP writes during game logic.** Every graphics write is staged to WRAM.
2. **VBlank is commit-only.** VBlank handler does hardware commits, input reads, and frame
   counting. Zero game logic.
3. **Display-disable bracketing.** VDP reg 1 bit 6 cleared before commits, set after.
4. **Flag-triggered conditional commits.** Palette, tile DMA, and tilemap updates are conditional.
   SAT DMA and scroll writes happen every frame unconditionally.
5. **DMA for bulk transfers.** SAT (320 words) and tile data (variable) use DMA.
6. **Strip-level tilemap updates.** Never full-plane writes; always the minimum changed data.
7. **WRAM shadow register for VDP reg 1.** Display on/off state is tracked in WRAM and applied
   via a shadow copy to avoid reading VDP status during display-disable transitions.

### What Made This Translation Natural for Rainbow Islands

Rainbow Islands arcade already separated game logic from hardware writes at the task-scheduler
level. The Genesis port preserved this separation by moving game logic to the main loop and
hardware commits to VBlank. The structural discipline was already present; the port replaced
arcade chip writes with Genesis VDP staging contracts.

---

## 11. What Rainbow Islands Preserved vs Transformed

### Game-logic timing preserved: YES

The cooperative task scheduler timing — game logic runs between frames, display commits happen at
VBlank — was preserved. The main loop in Genesis at `0x11D2` runs game mode handlers between
VBlanks, exactly mirroring the arcade task scheduler pattern where game tasks ran between VBlank
wakeups.

### VBlank ownership changed relative to arcade hardware: YES

Arcade: VBlank woke the task scheduler; no hardware commits occurred in the VBlank ISR itself.
Genesis: VBlank IS the commit phase. The VBlank ISR owns all hardware writes. The main loop
generates intent only. This is a change in ownership model: the VBlank ISR went from a task-
wakeup signal to a full commit orchestrator.

### Full-frame hardware consumption replaced with staged commit model: YES

Arcade PC080SN/PC090OJ chips accepted CPU writes throughout the frame and rendered asynchronously.
Genesis VDP requires writes to occur with display disabled (or with careful timing). The Genesis
port replaced continuous chip-RAM writes with a staged WRAM → VBlank-commit model.

### Tilemap update granularity reduced or transformed: YES

Arcade: CPU wrote individual tile cells to PC080SN chip RAM at any time. Genesis: game logic
writes intent to a WRAM staging pointer/flag, VBlank commits one strip (40 words) at a time.
The granularity was transformed from cell-level at-will writes to strip-level flagged commits
once per VBlank.

### Sprite publication strategy changed: YES

Arcade: CPU wrote sprite entries to PC090OJ chip RAM directly. Genesis: game logic builds the
SAT in WRAM at `0xFFFFF800`, VBlank DMAs the entire 640-byte SAT atomically to VDP SAT. Changed
from direct chip-RAM writes to WRAM staging + DMA commit.

### Palette update strategy changed: YES

Arcade: CPU wrote palette entries to palette RAM at `0x200000` directly. Genesis: game logic
sets a palette request flag, VBlank decompresses palette to WRAM staging and streams to CRAM.
Changed from direct writes to two-phase staging + conditional commit.

---

## 12. Lessons for Rastan-Direct

### Principles to copy directly from Rainbow Islands

1. **VBlank is commit-only.** Game logic (arcade tick) runs in the main loop outside VBlank.
   VBlank owns all VDP writes. Cody's current backbone already implements this correctly.

2. **Dirty flags gate all non-mandatory commits.** Palette, tile data, and nametable writes
   must be conditional on dirty flags. Scroll and SAT (when implemented) are unconditional.

3. **Display-disable bracket covers all VRAM/CRAM writes, NOT scroll.** Scroll is written after
   display-ON. Cody currently writes scroll after display-ON — this is correct.

4. **Strip-level nametable commits.** When the arcade PC080SN hook is integrated, commit only
   the strips that the hook has written, not the entire plane.

5. **DMA for SAT publication.** When sprites are added (Phase 4), DMA from WRAM SAT shadow to
   VDP SAT `0xF800` atomically.

6. **DMA for sprite tile uploads.** When sprites are added, DMA tile data from ROM to VRAM for
   each visible sprite.

### Rainbow Islands-specific compromises that do NOT apply to Rastan

1. The WRAM flag/shadow addresses (`0xFFFFF63C`, `0xFFFFF644`, `0xFFFFF648`, `0xFFFFF690`,
   `0xFFFFF800`) are game-specific. Rastan-direct defines its own WRAM contracts.

2. The VDP reg 1 shadow register pattern (`0xFFFFF624`) is a Rainbow Islands convention. Rastan-
   direct can use hardcoded values as Cody currently does, since there is no multi-mode display
   state machine that requires a shadow.

3. Rainbow Islands preserved its cooperative-task execution model naturally. Rastan arcade runs
   its entire tick inside VBlank (no task scheduler). Rastan-direct must introduce the main-
   loop/VBlank separation that Rainbow Islands Genesis inherited naturally from its arcade design.
   This transformation is a structural change for Rastan that Rainbow Islands did not need to
   engineer.

### Transformations Rastan also needs

1. **Game-logic separation from VBlank** — already done in rastan-direct (tick runs in main loop).
2. **Strip-level nametable updates** — needed when arcade PC080SN hook is integrated.
3. **WRAM SAT shadow + DMA** — needed when sprites are added.
4. **Flag-triggered commits for BG and FG** — needed immediately (next step).

### Transformations Rastan does NOT need

1. **Cooperative task scheduler reconstruction.** The main-loop/VBlank split is sufficient;
   no TRAP-based scheduler is needed.
2. **C-Chip handling.** Not present in Rastan arcade.
3. **VDP reg 1 shadow register.** Not required; hardcoded values work for Rastan-direct.

---

## 13. Does Cody's Current Approach Match the Real Porting Discipline?

Cody current approach matches Rainbow Islands porting discipline: **NO**

### Where it matches:

- VBlank ownership: YES — main loop writes only WRAM staging; VBlank is the sole commit owner.
- Staging/commit separation: YES — `staged_bg_buffer`, `staged_fg_buffer`, `staged_palette_words`
  are populated outside VBlank; VBlank consumes them.
- Display-OFF bracket before nametable commits: YES — display OFF before `vdp_commit_bg` and
  `vdp_commit_fg`.
- Scroll after display-ON: YES — `vdp_commit_scroll` is called after `vdp_set_reg` for display
  ON.
- Palette conditional commit: YES — `palette_dirty` flag gates `vdp_commit_palette`.
- Tile data conditional commit: YES — `tiles_dirty` flag gates `vdp_commit_tiles_if_dirty`.

### Where it diverges:

1. **Full-plane unconditional nametable writes every frame.** Rainbow Islands writes strips only
   when flagged. Cody writes all 2048 words of both nametables every VBlank regardless of
   whether anything has changed. This is the single most critical divergence.

2. **No `bg_dirty` / `fg_dirty` flags.** The pattern is established for palette and tiles. It is
   absent for nametables. Rainbow Islands gates its tilemap commit on `0xFFFFF63C`. Cody's code
   has no equivalent gate for BG and FG.

3. **Wrong commit granularity for final port.** Even if dirty flags are added to the current
   2048-word loops, the final port architecture requires strip-level updates (40–64 words per
   changed strip), not full-plane writes. The scaffolding establishes the wrong granularity.

4. **No WRAM SAT shadow.** Not a current error (sprites not yet active), but required before
   Phase 4 can follow Rainbow Islands discipline.

---

## 14. Single Most Important Porting Lesson for the Next Step

**Never write a full nametable plane unconditionally. All nametable commits must be gated by a
dirty flag, and once the arcade tick is integrated, commits must be strip-sized to match only
what the arcade hook actually changed.**

---

## 15. Exact Tighter `rastan-direct` Display Strategy

### What commits every frame (unconditional)

- Scroll: 4 words to VSRAM and HScroll table (current implementation is correct).
- Frame counter increment.
- SAT DMA (when sprite pipeline is active, Phase 4+).

### What commits only when dirty

- BG nametable (`staged_bg_buffer` → VRAM 0xC000): commit only when `bg_dirty` flag is set.
  Clear flag after commit.
- FG nametable (`staged_fg_buffer` → VRAM 0xE000): commit only when `fg_dirty` flag is set.
  Clear flag after commit.
- Palette (`staged_palette_words` → CRAM): commit only when `palette_dirty` flag is set (already
  implemented correctly).
- Tile data (`staged_tile_words` → VRAM 0x0020): commit only when `tiles_dirty` flag is set
  (already implemented correctly).

### What commits in strips/partial updates vs full plane writes (final port target)

In the bringup scaffold (synthetic static content), full-plane writes on first frame (dirty) are
acceptable. In the final port (arcade PC080SN hook active), each VBlank should commit only the
strips that the hook wrote during the current tick. The strip descriptor (source pointer + VDP
destination command + word count) should be staged by the hook and consumed by VBlank. This
matches Rainbow Islands `0xFFFFF63C`/`0xFFFFF644`/`0xFFFFF648` contract pattern.

### Whether display-off bracket remains around all commits or only specific classes

Display-OFF bracket remains around: BG nametable commit, FG nametable commit, palette commit,
tile data commit, sprite tile DMA (when added), SAT DMA (when added).

Display-OFF bracket does NOT cover: scroll commit (written after display-ON, as currently
implemented and as Rainbow Islands demonstrates is correct).

Display-OFF bracket is skipped entirely on frames where all guarded commits are skipped (all
dirty flags clear). This is the natural consequence of the dirty-flag guards: if no commit fires
inside the bracket, the display-OFF write is still issued but the display-ON write follows
immediately after the conditional branches, and the total overhead is approximately 80 cycles
for the two VDP register writes.

### Target VBlank budget

After adding `bg_dirty`/`fg_dirty` flags:

- Frame 1: approximately 60,836 cycles (initial commit of tiles, BG, FG, palette). Exceeds
  budget. Display-ON fires during active display on frame 1 only.
- Frame 2+: approximately 200–300 cycles (scroll + display OFF/ON overhead + register
  save/restore). Well within 7,400-cycle budget. Display-ON fires inside VBlank.

This is the correct steady-state target. The display overrun on frame 1 is acceptable for the
bringup scaffold; in the final port the initial full-plane write on frame 1 will also be the
worst case.

Exact tighter display strategy defined: **YES**

---

## 16. Exact Code-Change Classes Required

### Immediate next correction (single change)

Add `bg_dirty` and `fg_dirty` flags to gate `vdp_commit_bg` and `vdp_commit_fg` using the
exact same pattern as the existing `palette_dirty` guard in `_VINT_handler` and the
`vdp_commit_tiles_if_dirty` guard pattern.

Changes required:
1. In `.bss`: add `bg_dirty: .byte 0` and `fg_dirty: .byte 0` alongside `palette_dirty`.
2. In `init_staging_state`: add `move.b #1, bg_dirty` and `move.b #1, fg_dirty`.
3. In `vdp_commit_bg`: add `tst.b bg_dirty; beq.s .Lbg_done; [existing commit code];
   clr.b bg_dirty; .Lbg_done: rts` wrapping the existing loop.
4. In `vdp_commit_fg`: add `tst.b fg_dirty; beq.s .Lfg_done; [existing commit code];
   clr.b fg_dirty; .Lfg_done: rts` wrapping the existing loop.

No other changes to VBlank handler ordering, scroll commit, palette commit, or boot setup.

### Follow-up corrections to converge toward Rainbow Islands

1. **Strip-level commit infrastructure**: when arcade PC080SN hook is integrated, replace full-
   plane writes with a strip descriptor table (source pointer, VDP destination command, word count),
   populated by the hook on each tick and consumed by VBlank. Commit only dirty strips.

2. **WRAM SAT shadow + DMA commit**: when sprites are integrated (Phase 4), add a WRAM SAT
   shadow buffer, have the sprite hook write to it, and add a DMA commit to VDP SAT (`0xF800`)
   in the VBlank handler.

3. **Sprite tile DMA**: when sprites are integrated, add DMA-from-ROM tile upload for each
   visible sprite, using the pattern from `startup_trampoline.s` `.Lspr_dma_tile`.

4. **VDP reg 1 shadow register (optional)**: if display enable state needs to be tracked across
   multiple display modes, add a WRAM shadow. Not required for the current single-mode backbone.

Exact code-change classes identified: **YES**

---

## 17. Single Next Implementation Target for Cody

Add `bg_dirty` and `fg_dirty` byte flags in `.bss`, initialize both to 1 in `init_staging_state`,
and wrap `vdp_commit_bg` and `vdp_commit_fg` with the same `tst.b` / `beq.s` / `clr.b` guard
pattern already used by `vdp_commit_tiles_if_dirty` — so nametable CPU copy loops execute only
when flagged and skip in approximately 8 cycles when not flagged.

---

## 18. Ordered Follow-On Display Optimization Sequence

After the dirty-flag fix is confirmed working (steady-state VBlank under budget, display-ON
fires inside VBlank from frame 2 onward):

1. **Integrate arcade PC080SN hook** (Phase 2 from the bring-up plan): replace synthetic
   `init_staging_state` buffer fills with the arcade tick's PC080SN BG and FG hooks writing
   into `staged_bg_buffer` and `staged_fg_buffer`. Set `bg_dirty`/`fg_dirty` flags from the
   hooks.

2. **Replace full-plane writes with strip-level commit**: add a strip descriptor (source pointer +
   VDP destination command + strip word count) staged by the hook; commit only the written strips
   in VBlank instead of the entire 2048-word plane.

3. **Integrate arcade scroll hook** (Phase 3): replace `arcade_tick_logic` synthetic scroll with
   the `_scroll_stage` stub reading arcade workram fields and writing to `staged_scroll_*` words.

4. **Add WRAM SAT shadow and DMA commit** (Phase 4): add WRAM SAT buffer, adapt
   `genesistan_render_sprites_vdp_asm` to write to the WRAM shadow instead of directly to VDP,
   add DMA commit to VDP SAT in VBlank handler. Apply sprite DMA VRAM destination fix.

5. **Reduce display-OFF bracket overhead**: once all flagged commits are strip-level, the display-
   OFF bracket on a quiescent frame covers near-zero work. Add early-exit logic to skip the
   entire bracket if all dirty flags are clear.

6. **Replace CRAM write command hardcoded constant with WRAM shadow approach** (optional):
   this is only needed if multiple display modes with different display-enable states are required.

Ordered follow-on optimization sequence defined: **YES**

---

## 19. Final Verdict

| Analysis Item | Status |
|---------------|--------|
| Current VBlank work characterized | YES — ~59,268 cycles/frame steady state vs 7,400-cycle budget; 7.9× overrun |
| Dominant cost | `vdp_commit_bg` + `vdp_commit_fg`: 57,344 cycles for 4096-word unconditional CPU copy loops |
| Wasted work: full-plane unconditional nametable writes | YES — both functions always copy 2048 words regardless of dirty state |
| Wasted work: missing dirty flags for BG/FG | YES — palette_dirty and tiles_dirty exist; bg_dirty and fg_dirty do not |
| Rainbow Islands commit model compared | YES — strips only, flag-triggered, display-OFF bracket, DMA for SAT/tiles |
| Rainbow Islands DMA usage | Tilemap: NO (CPU direct writes, strip-level). SAT: YES (DMA, every frame). Palette: NO (CPU stream). Scroll: NO (1 long write). Tile uploads: YES (DMA). |
| Correct rastan-direct DMA policy | BG/FG nametable: MUST NOT USE DMA. Sprites: MUST USE DMA when added. Palette: MUST NOT. Scroll: MUST NOT. Boot tile upload: MAY USE DMA LATER. |
| Current DMA misuse | NONE — DMA is absent, not misused. CPU loops are correct mechanism but wrong scope. |
| Cody approach matches Rainbow Islands discipline | NO — architecture and ownership model are correct; commit granularity is wrong |
| Single most important porting lesson | Never write a full nametable plane unconditionally |
| Single next DMA instruction | Do not add DMA; add bg_dirty/fg_dirty flags instead |
| Single next implementation target | Add bg_dirty and fg_dirty flags; gate vdp_commit_bg and vdp_commit_fg with tst/beq/clr guards |
| Ordered follow-on sequence | YES — 6-step sequence from dirty-flag fix through SAT DMA and strip-level commits |
| No implementation performed | YES |
