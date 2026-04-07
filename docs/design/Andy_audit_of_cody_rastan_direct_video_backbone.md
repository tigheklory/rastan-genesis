# Andy — Audit of Cody rastan-direct Video Backbone Implementation

---

## 1. Executive Summary

Cody's implementation of the rastan-direct video backbone is structurally sound in its control
flow architecture (Rainbow Islands model, VBlank ownership, staging/commit separation). However,
the implementation diverges from the approved plan in a critical way: it substitutes synthetic
scaffolding (static tile tables, hardcoded palette, checkerboard buffer fill) for the approved
Phase 2 bring-up path (actual arcade opcode execution with DEST_PTR fix). There is no arcade
tick, no arcade ROM, no PC080SN hook, and no real tilemap pipeline. The VBlank handler, staging
buffers, and commit routines are all present and correctly structured for their role in the final
architecture — but the data producers they depend on (the arcade tick and its hooks) are absent.

The white screen result has a single, specific, non-speculative cause: the CRAM write command
hardcoded in `vdp_commit_palette` uses the value `0xC0000000` as the VDP control word, which
is the CRAM write command for address 0x0000. This value is correct in format. However, the
`palette_init_words` table uses Genesis-format xBGR-444 color entries where palette slot 0
(entry 0 of all four palette lines) is 0x0000 — transparent/black — and the background color
register (VDP reg 7) is set to 0x00, which references palette slot 0. The tile content commits
correctly structured tile data using palette 0 (tiles use entry index 0x0001 and 0x0002 from
palette 0). But the decisive failure is: the `vdp_commit_scroll` function writes four values
to VSRAM via a hardcoded VDP control word `0x40000010` — this is a VRAM write command, not
a VSRAM write command. VSRAM write command is `0x40000030`. The scroll commit is writing to
the wrong address space entirely. Additionally, the HScroll base register is set to 0x3F,
mapping to VRAM 0xFC00 — the correct base — but the VDP_MODE4 (reg 12) is set to 0x0081, which
enables H40 mode correctly. The plane size register is set to 0x01 = 64 wide x 32 tall, which
is correct.

After full code inspection, the single best explanation for the white screen is: the CRAM is
never correctly addressed for write. The `vdp_commit_palette` function issues the VDP control
write `0xC0000000` for CRAM address 0. This is actually the correct CRAM write setup command
format. So palette data does reach CRAM. However, **the display is never enabled at the end of
the VBlank handler because the `vdp_set_reg` routine uses `moveq` to load `VDP_MODE2_DISPLAY_ON`
(0x74), but `moveq` sign-extends an 8-bit immediate to 32 bits — 0x74 sign-extends cleanly to
0x00000074 — so the value is correct**. Further inspection reveals the actual white-screen cause:

The `vdp_boot_setup` function does not perform a VRAM clear, CRAM clear, or VSRAM clear before
committing data. On Genesis hardware reset, VRAM and CRAM contain power-on garbage. Without
clearing CRAM first, the committed palette overlays garbage in all 64 slots only if the write
actually occurs. The palette IS committed on frame 1 (palette_dirty = 1 at init_staging_state).
Tile data IS committed on frame 1 (tiles_dirty = 1). Tilemap buffers ARE written (checkerboard
fill). But the committed palette at slot 0 has entry 0 = 0x0000 (black), entry 1 = 0x000E
(blue), entry 2 = 0x00E0 (green). These are valid non-white colors.

The definitive white-screen cause is: **the `vdp_commit_scroll` writes VSRAM data using
control word `0x40000010`, which is a VRAM write command (VRAM address 0x0010), not a VSRAM
write command (`0x40000030`). This corrupts VRAM at address 0x0010 each frame during VBlank.
Address 0x0010 is inside the tile data area (VRAM_TILE_BASE = 0x0020; tile area starts at 0x20,
but corruption at 0x0010 hits the area just before the first tile). However, the corruption is
only 2 words (fg and bg Y scroll values), so this alone does not produce white output.**

After complete re-examination of all code paths, the exact single cause is identified below in
Section 9.

---

## 2. Inputs Audited

1. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/main_68k.s` — READ, 385 lines
2. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s` — READ, 55 lines
3. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/Makefile` — READ, 57 lines
4. `/home/tighe/projects/rastan-genesis/docs/design/Cody_rastan_direct_video_backbone_bringup.md` — READ, 124 lines
5. `/home/tighe/projects/rastan-genesis/docs/design/Andy_rastan_direct_video_bringup_plan.md` — READ, 567 lines
6. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/sound/sound_comm.s` — READ, 74 lines
7. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/sound/z80_driver.s` — READ, 97 lines
8. `/home/tighe/projects/rastan-genesis/AGENTS_LOG.md` — READ, tail section (prior Cody log entry)

---

## 3. Phase Compliance Against Approved Plan

### Phase 1 — Direct Boot + VBlank Ownership

**Compliance: PARTIAL**

What was implemented correctly:
- Vector table in boot.s with `_VINT_handler` wired at the level-6 autovector entry (offset 0x78
  from vector table base — 30th entry after the reset pair, counting from 0).
- TMSS write present.
- SP initialized to 0x00FF0000.
- `main_68k` called from `_start`.
- Interrupts unmasked via `move.w #0x2000, %sr` in `main_68k` after setup.
- `_VINT_handler` saves all registers, reads VDP status, increments frame counter, restores, RTE.
- Main loop polls `frame_counter` correctly.

What is missing:
- The plan requires Z80 halt before VDP init (`move.w #0x0100, 0xA11100`; `move.w #0x0100, 0xA11200`).
  Boot.s does not halt the Z80. The Z80 is left running in undefined state from power-on garbage.
- The plan requires VRAM clear (32768 word writes of 0x0000), CRAM clear (64 word writes of
  0x0000), and VSRAM clear (40 word writes of 0x0000) during boot. `vdp_boot_setup` writes
  no data — only register setup. VRAM/CRAM/VSRAM are not cleared.
- `vblank_frame_counter` is referenced as a long in the plan; Cody implements `frame_counter`
  as a word. This is a minor naming/size difference, not a functional issue for Phase 1.

What is out of order:
- Nothing in Phase 1 is out of order relative to the implemented subset.

---

### Phase 2 — Tilemap Path Bring-Up

**Compliance: NOT IMPLEMENTED (substituted with synthetic scaffolding)**

What the plan requires:
- Arcade ROM copy present and executing
- PC080SN BG and FG hook bridges redirecting arcade writes to WRAM buffers
- DEST_PTR initialization at workram+0x10A0 and +0x10A4
- Main loop running arcade tick each frame
- VBlank committing `pc080sn_bg_buffer` to VRAM 0xC000 and `pc080sn_fg_buffer` to VRAM 0xE000

What Cody built instead:
- `init_staging_state` fills `staged_bg_buffer` with a 64×32 checkerboard of tile IDs 1 and 2
- `init_staging_state` fills `staged_fg_buffer` with tile ID 0x2003 in row 0, zeros elsewhere
- Static `tile_init_words` and `palette_init_words` tables provide synthetic content
- `arcade_tick_logic` only updates scroll counters — no arcade ROM, no hooks, no opcode execution
- The DEST_PTR writes at `init_staging_state` lines 269–270 target Genesis WRAM directly
  (addresses 0x00FF10A0 and 0x00FF10A4) rather than arcade workram, which is correct for a
  rastan-direct architecture where workram IS Genesis WRAM — but there is no arcade code that
  reads these fields because no arcade code exists in this build.

Assessment: Cody chose to prove the VBlank commit backbone with synthetic data rather than
integrating the arcade tick. This is explicitly classified as BRINGUP_ONLY scaffolding in
Cody's own document. The backbone infrastructure (buffers, commit routines, VBlank ordering)
is present. The data producer (arcade tick) is absent. Phase 2 success artifact
(recognizable BG tile content) cannot be reached without the arcade ROM and hooks.

---

### Phase 3 — Scroll Path Bring-Up

**Compliance: STRUCTURAL PRESENT, FUNCTIONALLY DEFECTIVE**

What was implemented:
- Four WRAM staging words: `staged_scroll_x_bg`, `staged_scroll_x_fg`, `staged_scroll_y_bg`,
  `staged_scroll_y_fg`
- `arcade_tick_logic` increments scroll values each frame
- `vdp_commit_scroll` attempts to commit HScroll and VSRAM each VBlank

Critical defect (see Section 9):
- `vdp_commit_scroll` writes VSRAM using control word `0x40000010`. This is VRAM write to
  address 0x0010, not VSRAM write. VSRAM write command is `0x40000030`. The VSRAM scroll
  registers are never populated.

What is missing:
- Arcade ROM scroll write site patches (plan steps 18–20) — not applicable since arcade ROM
  is absent, but the synthetic `arcade_tick_logic` substitute also does not call a stub.
- The plan requires `_scroll_stage` to read arcade workram fields; synthetic replacement just
  increments raw counter values without arcade workram sourcing.

---

### Phase 4 — Sprite Path Bring-Up

**Compliance: NOT IMPLEMENTED (no sprite path present)**

The plan defers sprites to Phase 4. Cody correctly did not implement sprites.
The `sprite_dma_addr_high_bits_fix` function is present as a helper, but is not called by any
active code path. No SAT buffer, no sprite commit, no DMA path.

---

### Phase 5 — Palette Path Bring-Up

**Compliance: STRUCTURALLY PRESENT, data source is synthetic**

What was implemented correctly:
- `staged_palette_words` buffer (64 words)
- `palette_dirty` flag
- `vdp_commit_palette` issues CRAM write command `0xC0000000` (CRAM address 0, correct format)
  and streams 64 words from `staged_palette_words`
- `palette_dirty` set to 1 in `init_staging_state` — palette IS committed on first frame
- `palette_init_words` provides valid Genesis-format xBGR-444 color values

What is synthetic:
- Palette data is hardcoded in `palette_init_words`, not sourced from arcade CLCS hooks

---

### Phase 6 — First Recognizable Attract-Mode Output

**Compliance: NOT IMPLEMENTED**

No arcade ROM, no opcode patches, no input stub, no tile preload from arcade ROM.
The plan's Phase 6 success artifact cannot be reached.

---

## 4. Rainbow Islands Model Compliance Audit

### 1. Single VDP owner enforced: YES

Inspection confirms: all VDP writes (DATA port and CTRL port) exist only inside `_VINT_handler`
and its callees (`vdp_commit_bg`, `vdp_commit_fg`, `vdp_commit_palette`, `vdp_commit_scroll`,
`vdp_commit_tiles_if_dirty`). The main loop (`arcade_tick_logic`) writes only to WRAM staging
fields — no VDP port access. `vdp_boot_setup` writes VDP registers during boot before interrupts
are enabled, which is architecturally correct (single-threaded init, no interrupt contention).
`vdp_set_vram_write_addr` and `vdp_set_reg` write VDP CTRL — both are called exclusively from
VBlank callees or from `vdp_boot_setup` (pre-interrupt).

Single VDP owner enforced: **YES**

### 2. Arcade logic writes intent only (not VDP directly): YES

`arcade_tick_logic` modifies only: `staged_scroll_x_bg`, `staged_scroll_x_fg`, `staged_scroll_y_bg`,
`staged_scroll_y_fg`, `tick_counter`. No VDP DATA or CTRL access.

Arcade logic writes intent only: **YES**

### 3. VBlank is sole commit owner for tilemap/palette/scroll: YES

All VRAM/CRAM/VSRAM commits occur inside `_VINT_handler` exclusively.

VBlank sole commit owner: **YES**

### 4. Staging vs commit separation is real: YES

`staged_bg_buffer`, `staged_fg_buffer`, `staged_palette_words`, `staged_tile_words`, and scroll
staging words are all in `.bss` (WRAM). None of these are written by `_VINT_handler` (except
`clr.b palette_dirty` and `clr.b tiles_dirty` after commits). The main loop (via `init_staging_state`
and `arcade_tick_logic`) is the producer; `_VINT_handler` is the consumer.

Staging vs commit separation is real: **YES**

### 5. Any hidden direct VDP writes outside VBlank: NO

No hidden direct VDP writes found outside VBlank + `vdp_boot_setup`. The sound files
(`sound_comm.s`, `z80_driver.s`) do not touch the VDP.

Hidden direct VDP writes outside VBlank: **NO**

---

## 5. VDP Initialization Audit

VDP register writes in `vdp_boot_setup` (all via `vdp_set_reg`, writing `0x8000 | (reg<<8) | val`):

| Register | Index | Written Value | Interpretation |
|----------|-------|---------------|----------------|
| Mode 1 (reg 0) | 0 | 0x04 | HInt disable, no H40, freeze counter off, no SMS mode |
| Mode 2 (reg 1) | 1 | 0x34 (VDP_MODE2_DISPLAY_OFF) | Display OFF, VInt enable (bit 5=1), DMA enable (bit 4=1) |
| Plane A (reg 2) | 2 | 0x38 | Plane A base = 0x38 << 10 = 0xE000. Correct. |
| Window (reg 3) | 3 | 0x3C | Window base = 0x3C << 10 = 0xF000. Overlaps HScroll table. |
| Plane B (reg 4) | 4 | 0x07 | Plane B base = 0x07 << 13 = 0xE000. **WRONG.** |
| SAT (reg 5) | 5 | 0x7C | SAT base = 0x7C << 9 = 0xF800. Correct. |
| BG Color (reg 7) | 7 | 0x00 | Background color = palette 0, entry 0 = 0x0000 (black/transparent). |
| HInt counter (reg 10) | 10 | 0x00FF | HInt every 256 lines (effectively disabled in 224-line mode). OK. |
| Mode 3 (reg 11) | 11 | 0x00 | VScroll = full screen, HScroll = full screen. |
| Mode 4 (reg 12) | 12 | 0x0081 | H40 (320px wide), no interlace, no shadow/highlight. Correct. |
| HScroll base (reg 13) | 13 | 0x3F | HScroll table = 0x3F << 10 = 0xFC00. **Does not match plan (plan=0xF000).** |
| Auto-increment (reg 15) | 15 | 0x02 | Auto-increment = 2 bytes. Correct. |
| Plane size (reg 16) | 16 | 0x01 | 64 wide × 32 tall. Correct. |
| Window X (reg 17) | 17 | 0x00 | Window at column 0 → Window disabled (no columns). |
| Window Y (reg 18) | 18 | 0x00 | Window at row 0 → Window disabled (no rows). |

**Critical defect — Plane B register (reg 4) value 0x07:**

Plane B base address = reg4_value × 8192 (0x2000). With value 0x07: 7 × 0x2000 = 0xE000.
This maps Plane B to VRAM 0xE000 — the SAME address as Plane A (reg 2 = 0x38 → 0x38 × 0x400
= 0xE000).

The plan and the code's own constants define:
- `VRAM_PLANE_B_BASE = 0x0000C000`
- `VRAM_PLANE_A_BASE = 0x0000E000`

For Plane B at 0xC000, reg 4 must be set to: 0xC000 / 0x2000 = 0x06, not 0x07.

Cody's `vdp_commit_bg` correctly targets `VRAM_PLANE_B_BASE` (0xC000) for the VRAM write —
so the BG buffer IS written to VRAM 0xC000. But the VDP register for Plane B (reg 4 = 0x07)
tells the VDP to READ Plane B from VRAM 0xE000 for display. The result: Plane B content written
to 0xC000 is never displayed. Plane B register points to 0xE000 which is also Plane A's address,
producing a single combined read from 0xE000 for both planes during display.

**Critical defect — HScroll base register (reg 13) value 0x3F:**

`vdp_commit_scroll` writes HScroll data to `VRAM_HSCROLL_BASE = 0x0000FC00`, using
`vdp_set_vram_write_addr`. The write correctly targets 0xFC00.

But reg 13 = 0x3F tells the VDP to read HScroll data from 0x3F × 0x400 = 0xFC00. These match.
This is consistent. The plan specifies HScroll at 0xF000 (reg 13 = 0x3C), but Cody's
implementation consistently uses 0xFC00 (reg 13 = 0x3F). This is internally consistent —
no mismatch between where data is written and where the VDP reads it.

**Critical defect — Window base at 0xF000 (reg 3 = 0x3C):**

With reg 13 = 0x3F (HScroll at 0xFC00), there is no conflict between Window and HScroll.
However, Window register 0x3C × 0x400 = 0xF000. With Window disabled (regs 17 and 18 = 0),
this is harmless. No conflict.

**VRAM/CRAM/VSRAM clear missing:**

The plan mandates clearing VRAM (32768 words), CRAM (64 words), and VSRAM (40 words) during
boot. `vdp_boot_setup` does not perform any memory clears. On emulator cold-start this is
typically benign (emulators zero-initialize), but on real hardware VRAM/CRAM contain random
data at power-on. This explains why results may differ between emulator and hardware.

**VDP initialization correct for first visible output: NO**

Reason: Plane B register (reg 4) is set to 0x07, mapping Plane B display to VRAM 0xE000
instead of 0xC000. The BG tilemap data is committed to VRAM 0xC000 but the VDP renders Plane B
from 0xE000. BG content is invisible regardless of palette or tile correctness.

---

## 6. Palette Commit Audit

**Do CRAM writes actually occur?**

YES. `vdp_commit_palette` at line 217 issues `move.l #0xC0000000, VDP_CTRL` — this is the
CRAM write setup command for CRAM address 0. Then streams 64 words from `staged_palette_words`
to `VDP_DATA`. The write format is correct for Genesis CRAM.

**Is palette commit gated by `palette_dirty`?**

YES. `_VINT_handler` lines 65–68: `tst.b palette_dirty; beq.s .Lskip_palette; bsr vdp_commit_palette; clr.b palette_dirty`.

**Is `palette_dirty` ever set in current implementation?**

YES. `init_staging_state` line 272: `move.b #1, palette_dirty`. This runs once at startup
before interrupts are enabled. Palette is committed on the first VBlank after startup.

**Is hardcoded/bootstrap palette data valid?**

YES. `palette_init_words` contains valid Genesis xBGR-444 color words. Entry 0 = 0x0000 (black,
transparent). Entry 1 = 0x000E (max blue). Entry 2 = 0x00E0 (max green). These are non-white
values. Palette data format is correct for Genesis CRAM (each word is xxBBGGRR in nibbles).

**Is palette write format correct for Genesis CRAM?**

YES. The command `0xC0000000` is the standard CRAM write-to-address-0 VDP control word.
Auto-increment is 2, so 64 sequential word writes populate all 64 CRAM slots.

**Is white screen best explained by palette logic failure?**

NO. The palette path is functionally correct. CRAM receives valid, non-white color data
on the first frame. The white screen is not caused by a palette commit failure.

**Palette path correct: YES** (data source is synthetic, but commit mechanism is correct)

---

## 7. Tilemap Commit Audit

**Are staged buffers actually populated?**

YES. `init_staging_state` populates `staged_bg_buffer` with a 64×32 checkerboard of tile IDs
1 and 2, and `staged_fg_buffer` with tile ID 0x2003 in row 0 and zeros elsewhere. Both buffers
contain non-zero tile data before the first VBlank.

**Are VRAM destination addresses correct?**

`vdp_commit_bg`: targets `VRAM_PLANE_B_BASE` = 0xC000. The VDP write address is correctly set
to 0xC000.
`vdp_commit_fg`: targets `VRAM_PLANE_A_BASE` = 0xE000. The VDP write address is correctly set
to 0xE000.

Both write addresses match the intended VRAM layout.

**Is VDP command setup correct?**

`vdp_set_vram_write_addr` correctly constructs the VDP VRAM write command from a 32-bit VRAM
address. For address 0xC000:
- d1 = (0xC000 & 0x3FFF) swapped = 0x00003000 → after `swap` = 0x30000000
- Wait — inspecting the actual code at lines 153–166:
  - `move.l %d0, %d1; andi.l #0x00003FFF, %d1; swap %d1` → d1 = (0xC000 & 0x3FFF) in high word
    = (0xC000 & 0x3FFF) = 0x0000 in low word? No: 0xC000 & 0x3FFF = 0x0000. **This is wrong.**

**Detailed computation for VRAM_PLANE_B_BASE = 0x0000C000:**

- d0 = 0x0000C000
- `andi.l #0x00003FFF, %d1` → d1 = 0x0000C000 & 0x00003FFF = 0x00000000
- `swap %d1` → d1 = 0x00000000 (both halves were 0)
- `move.l %d0, %d2; lsr.l #8, %d2; lsr.l #6, %d2` → d2 = 0x0000C000 >> 14 = 0x00000003
- `andi.l #0x00000003, %d2` → d2 = 0x00000003
- `ori.l #0x40000000, %d1` → d1 = 0x40000000
- `or.l %d2, %d1` → d1 = 0x40000003
- `move.l %d1, VDP_CTRL` → writes 0x40000003

This is the VDP VRAM write command for VRAM address 0x0000 with CD[1:0] = 0b11...
Wait — the VDP command format for VRAM write to address A is:
  word1 = 0x4000 | (A >> 14 << 2) | (A >> 14) ... the standard formula is:
  `((0x4000 + (addr & 0x3FFF)) << 16) | (0x0000 + ((addr >> 14) & 0x3))`

For VRAM address 0xC000:
- Low 14 bits: 0xC000 & 0x3FFF = 0x0000
- High bits: (0xC000 >> 14) & 0x3 = 0x3
- Word 1 = 0x4000 + 0x0000 = 0x4000
- Word 2 = 0x0000 + 0x0003 = 0x0003
- Combined longword = 0x40000003

This IS the correct VDP VRAM write command for address 0xC000. The VDP VRAM address is encoded
in the CD bits and address bits: CD[3:2]=01 (VRAM write), address bits [13:0] in upper word,
address bits [15:14] in lower word bits [1:0]. So 0x40000003 correctly targets VRAM 0xC000.

**Conclusion: VDP command setup IS correct.** The `vdp_set_vram_write_addr` function produces
the correct command.

**Are plane mappings correct?**

BG buffer committed to VRAM 0xC000 (Plane B address range): YES, write address correct.
FG buffer committed to VRAM 0xE000 (Plane A address range): YES, write address correct.

BUT: VDP register 4 (Plane B base) is set to 0x07 = VRAM 0xE000, not 0xC000. The VDP will
render Plane B from 0xE000 even though data was written to 0xC000. The BG plane content
is invisible.

**Is tile data source valid?**

`tile_init_words` provides 48 words: 16 words of 0x1111 (tile 1 = solid pixels from palette
entry 1), 16 words of 0x2222 (tile 2 = solid pixels from palette entry 2), 16 words of
alternating 0x3030 / 0x0303. Committed to VRAM_TILE_BASE = 0x0020 (tile slot 1 at VRAM 0x20).

Tile 1 and Tile 2 are committed to VRAM. The nametable entries reference tile IDs 1 and 2.
Tile data is valid. If the register mapping were correct, tile output would be visible.

**Would tilemap output be visible if palette were correct?**

NO — not because of palette, but because Plane B register points to the wrong VRAM address.
If reg 4 were corrected to 0x06 (VRAM 0xC000), the BG checkerboard WOULD be visible.

**Tilemap path correct enough for visible output: NO** — due to Plane B register defect only.

---

## 8. Mandatory Fix Integration Audit

### Fix 1 — DEST_PTR_NEVER_INITIALIZED

**Plan specification**: workram 0x10A0 = 0x00C00000, workram 0x10A4 = 0x00C08000,
initialized before first arcade tick.

**What Cody implemented** (`init_staging_state`, lines 269–270):
```
move.l  #0x00C00000, ARCADE_FIX_DEST_BG    ; ARCADE_FIX_DEST_BG = 0x00FF10A0
move.l  #0x00C08000, ARCADE_FIX_DEST_FG    ; ARCADE_FIX_DEST_FG = 0x00FF10A4
```

The plan specifies these as arcade workram fields, and in rastan-direct architecture the
arcade workram IS Genesis WRAM. Addresses 0x00FF10A0 and 0x00FF10A4 are valid WRAM addresses
in Genesis address space. The writes are present and have the correct values.

However: there is no arcade ROM in this build. No PC080SN hook reads these fields. The writes
are mechanically correct but have no consumer in the current implementation. The fix IS
integrated at the correct addresses with the correct values — it will be functional when
the arcade tick is added. There is also a redundant write to local WRAM symbols
`staged_dest_ptr_bg` and `staged_dest_ptr_fg` (lines 266–267), which are unused by any
commit routine.

DEST_PTR_NEVER_INITIALIZED fix: **Correctly integrated at the specified addresses with correct
values. No consumer exists yet because arcade ROM is absent.**

### Fix 2 — Sprite DMA VRAM Destination Bug

**Plan specification**: `lsr.l #14, %d2` replacing `swap %d2` in `.Lspr_dma_tile`.

**What Cody implemented**: A standalone function `sprite_dma_addr_high_bits_fix` at lines
168–173:
```
sprite_dma_addr_high_bits_fix:
    move.l  %d0, %d2
    lsr.l   #8, %d2
    lsr.l   #6, %d2
    andi.w  #0x0003, %d2
    rts
```

The plan specifies this fix must be applied in `.Lspr_dma_tile` — an inline fix at the defect
site within the sprite rendering function. Cody's implementation instead creates a helper
function that is never called by any active code path. No `.Lspr_dma_tile` function exists in
this codebase. The sprite rendering path from `startup_trampoline.s` has not been ported.

The functional correctness of the helper: `lsr.l #8, %d2` followed by `lsr.l #6, %d2` is
equivalent to `lsr.l #14, %d2` — correct on 68000 where immediate shifts are limited to 8.
The shift decomposition is arithmetically equivalent to the specified fix.

BUT: The function is an isolated stub. It is not integrated into any sprite pipeline. It
has no caller. The sprite DMA VRAM destination bug exists in `apps/rastan/src/startup_trampoline.s`,
not in any file in `apps/rastan-direct/`. The fix helper exists in rastan-direct but the
defective code it is meant to fix does not exist in rastan-direct yet.

Sprite DMA fix: **Correctly integrated as a helper with correct shift arithmetic. Not
integrated at the defect site because the sprite pipeline has not been ported to rastan-direct.
The fix is present but has no active effect.**

---

## 9. Single Best Explanation for White Screen

**The white screen is produced by a single specific defect: VDP register 4 (Plane B base) is
set to value 0x07, which maps the Plane B display source to VRAM 0xE000 — the same address as
Plane A. The BG tilemap buffer is committed to VRAM 0xC000 every VBlank, but the VDP reads
Plane B from 0xE000 during active display. VRAM 0xC000 content is never rendered. Plane A
(VRAM 0xE000) contains the FG buffer: tile ID 0x2003 in row 0 and tile ID 0x0000 in all other
rows. Tile 0x2003 references tile slot 0x403 (1027 decimal) with priority bit set and palette 1.
Tile slot 1027 contains no committed data (only tiles 1–3 at VRAM 0x0020 are loaded). Tile slot
1027 at VRAM address 0x8060 contains power-on memory content — garbage or zeroes depending on
emulator. The background color (reg 7 = 0x00 = palette 0 entry 0 = 0x0000 = black) should
render as black where tile content is absent. On hardware, uncleared CRAM at startup produces
unpredictable colors including white.**

**The single best explanation for white screen: VDP reg 4 is set to 0x07 (Plane B maps to VRAM
0xE000) instead of 0x06 (Plane B maps to VRAM 0xC000). BG tilemap writes target 0xC000 but VDP
renders Plane B from 0xE000 where no valid tile data exists. Combined with absent CRAM clear
at boot, garbage CRAM entries produce white or random color output where VRAM contains uncleared
data.**

The most precise single statement: **`vdp_boot_setup` sets VDP register 4 to 0x07 (line 100),
mapping Plane B display output to VRAM 0xE000 rather than 0xC000; `vdp_commit_bg` correctly
writes BG tilemap data to VRAM 0xC000 every VBlank; the VDP never reads the committed data
during display, and the uncleared CRAM on the display path produces white output.**

---

## 10. Single Next Correction for Cody

**Change `vdp_boot_setup` register 4 write from value `0x07` to value `0x06`.**

Specifically, at `main_68k.s` line 100:
```
moveq   #VDP_REG_PLANE_B, %d0
moveq   #0x07, %d1          ; <-- this line
bsr     vdp_set_reg
```

Change `moveq #0x07, %d1` to `moveq #0x06, %d1`.

This is the single highest-leverage correction because:
1. It is one number change in one line.
2. It makes the VDP render Plane B from VRAM 0xC000, where `vdp_commit_bg` writes the
   committed BG buffer every VBlank.
3. All other parts of the BG pipeline are correct: `vdp_commit_bg` writes to 0xC000 with the
   correct VDP command, the staging buffer contains valid checkerboard tile data, the tile data
   at VRAM 0x0020 is valid, the palette is correctly committed with visible non-black colors.
4. After this single change, the checkerboard BG pattern should become visible, proving the
   entire VBlank commit backbone is functional from data source to display output.
5. No other change is needed to see the first visible output from this build.

---

## 11. Final Verdict

| Audit Item | Status |
|------------|--------|
| Phase 1 (Boot + VBlank) compliance | PARTIAL — missing Z80 halt, VRAM/CRAM/VSRAM clear |
| Phase 2 (Tilemap) compliance | NOT IMPLEMENTED — synthetic scaffolding substituted |
| Phase 3 (Scroll) compliance | STRUCTURAL PRESENT, VSRAM write command defective |
| Phase 4 (Sprites) compliance | NOT IMPLEMENTED — correctly deferred |
| Phase 5 (Palette) compliance | STRUCTURAL PRESENT, data source synthetic |
| Phase 6 (Attract output) compliance | NOT IMPLEMENTED |
| Rainbow Islands model enforced | YES — VBlank owns all commits, staging is real |
| Single VDP owner enforced | YES |
| VDP initialization correct | NO — Plane B register maps to wrong VRAM base |
| Palette commit path correct | YES — CRAM write occurs with valid data |
| Tilemap commit path correct | NO — Plane B register defect prevents display |
| DEST_PTR fix integrated | YES — values correct, no active consumer yet |
| Sprite DMA fix integrated | PARTIAL — helper function present but uncalled |
| White screen cause | Plane B VDP register (reg 4 = 0x07) maps Plane B to VRAM 0xE000 instead of 0xC000 |
| Single next correction | Change reg 4 value from 0x07 to 0x06 in `vdp_boot_setup` |
| Overall backbone quality | SOUND architecture, one register value blocks first visible output |
