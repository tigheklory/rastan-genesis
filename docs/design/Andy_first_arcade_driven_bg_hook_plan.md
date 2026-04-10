# Andy — First Arcade-Driven BG Hook Plan

## 1. Executive Summary

The `apps/rastan-direct/` branch has a stable, artifact-free synthetic video baseline: BSS
mapped to WRAM, dirty flags working, CRAM writes working, BG checkerboard stable, FG
deterministic transparent, VBlank ownership stable, steady-state ~532 cycles per frame. The FG
full-plane commit has been removed. The architecture is clean and correctly aligned with the
Rainbow Islands commit discipline at the flag level but not yet at the granularity level.

This document defines the exact plan to move from synthetic (checkerboard) BG output to real
arcade-driven BG output by hooking the PC080SN BG strip producer in rastan-direct and connecting
it to `staged_bg_buffer` with per-row dirty tracking. This is the first real arcade-driven
graphics step for the direct execution branch.

The plan is derived from five prior audits, the existing working SGDK branch hooks, the
`startup_title_remap.json` patch specification, the arcade disassembly, and the Rainbow Islands
VDP template analysis. No guesses are made. Every address, offset, contract, and data structure
is grounded in verified sources.

---

## 2. Inputs Audited

1. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/main_68k.s` — READ COMPLETE (383
   lines, post-FG-commit-removal state: bg_dirty byte, staged_bg_buffer 4096 bytes, staged_fg_buffer
   4096 bytes, VBlank commits BG full-plane when bg_dirty set, scroll unconditional)
2. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s` — READ COMPLETE (55
   lines, TMSS stub, calls main_68k)
3. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/sound/` — directory contains
   sound_comm.s and z80_driver.s; sound is out of scope for this plan
4. `/home/tighe/projects/rastan-genesis/docs/design/Andy_rastan_direct_video_bringup_plan.md` —
   READ COMPLETE; defines 6-phase bring-up, DEST_PTR fix, VBlank commit order
5. `/home/tighe/projects/rastan-genesis/docs/design/Andy_vblank_efficiency_audit_and_transition_plan.md`
   — READ COMPLETE; defines FG removal (done), ordered transition to per-strip BG dirty tracking
6. `/home/tighe/projects/rastan-genesis/docs/design/Andy_tilemap_correctness_audit.md` — READ
   COMPLETE; CRITICAL: DEST_PTR_NEVER_INITIALIZED root cause, PC080SN BG column-major 64×64
   layout, desc list at 0x1000, strip access formula, WRAM buffer geometry
7. `/home/tighe/projects/rastan-genesis/docs/design/Cody_rainbow_islands_vdp_template_analysis.md`
   — READ COMPLETE; RI tilemap strip commit at 0x073C/0x1A70, flag 0xFFFFF63C, 40 words/strip
8. `/home/tighe/projects/rastan-genesis/docs/design/Cody_rastan_vs_rainbow_tilemap_mismatch.md`
   — READ COMPLETE; validates DEST_PTR root cause, documents destination pointer mismatch
9. `/home/tighe/projects/rastan-genesis/docs/design/pc080sn_tilemap_architecture.md` — READ
   COMPLETE; full pipeline, descriptor loop, strip formula, WRAM contracts, no shadow needed
10. `/home/tighe/projects/rastan-genesis/apps/rastan/src/startup_trampoline.s` —
    `genesistan_asm_tilemap_commit_bg` (lines 524–620): desc loop, tile/attr LUT lookup, WRAM
    buffer write at `row*128 + col*2`; `genesistan_asm_tilemap_commit_fg` (lines 626–734)
11. `/home/tighe/projects/rastan-genesis/apps/rastan/src/main.c` — `genesistan_hook_tilemap_plane_a`
    (lines 1258–1280): reads strip_index from 0x10CA, dest_ptr from 0x10A0,
    `pc080sn_dest_ptr_to_row_col`, calls assembly, writes back dest_ptr;
    `genesistan_hook_tilemap_plane_b` (lines 1283–1310): mode from 0x10A8, strip_index formula
12. `/home/tighe/projects/rastan-genesis/specs/startup_title_remap.json` — lines 1056–1067:
    patch at 0x055968 = `JSR genesistan_hook_tilemap_plane_a`; patch at 0x055990 =
    `JSR genesistan_hook_tilemap_plane_b`; both confirmed present
13. `/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt` — confirmed 0x055968 is
    the BG strip producer entry; 0x055950 calls both BG and FG producers; callers at 0x50434,
    0x556fc, 0x55788, 0x55822 via dispatcher at 0x55948

---

## 3. First Real Arcade BG Producer Selection

### 3.1 The Arcade BG Strip Producer

The arcade BG tilemap strip producer is the routine at **arcade ROM address 0x055968**.
Disassembly confirms:

```
55968: moveal %a5@(4256),%a0   ; load dest_ptr from workram[0x10A0]
5596c: movew #16,%d1           ; 16 descriptors
55970: moveal #1101952,%a1     ; desc list base
55976: moveal #1101888,%a3     ; companion table base
5597c: moveal %a3@,%a2         ; load desc entry
5597e: bsrw 0x559b2            ; inner strip writer
55982: movel %a0,%a5@(4256)    ; write back dest_ptr
55986: addql #4,%a3            ; advance desc list
55988: addql #2,%a1
5598a: subqw #1,%d1            ; decrement count
5598c: bnes 0x5597c            ; loop
5598e: rts
```

The inner writer at 0x559b2 reads `strip_index` from `%a5@(4298)` (= workram offset 0x10CA).

The dispatcher at 0x55948 checks `workram[0x10A8]` (mode) and branches to call BG at 0x55950
then FG at 0x5595A. The dispatcher is called from four sites: 0x50434, 0x556fc, 0x55788,
0x55822.

### 3.2 Confirmed Hook Address for rastan-direct

The hook address is **0x055968**, identical to the SGDK branch. This is confirmed by:

1. The `startup_title_remap.json` patch at line 1057: `"arcade_pc": "0x055968"` is already
   present with `JSR genesistan_hook_tilemap_plane_a` as replacement bytes.
2. The disassembly showing 0x055968 is the exact entry point of the BG strip producer.
3. The original bytes at 0x055968 match: `206D10A0` = `moveal %a5@(4256),%a0` which is the BG
   dest_ptr load — the first instruction of the function being replaced.

For rastan-direct, the same hook address 0x055968 is correct. The arcade ROM code is identical
in both branches (it is the arcade maincpu ROM, which is immutable).

### 3.3 What the Hook Must Capture

When the arcade calls 0x055968, the following state is valid and available:

- `%a5` — points to arcade WRAM base (the same A5 convention used throughout the arcade code)
- `workram[0x10A0]` (= A5+4256) — BG dest_ptr: a 32-bit value in the range 0xC00000–0xC03FFF
  when valid, advances by 0x400 per call across the 16 descriptors
- `workram[0x10CA]` (= A5+4298) — strip_index: the current strip number (0–3 for BG)
- `workram[0x1000..0x103F]` — 16 descriptor address pointers (u32 BE each), filled by arcade init
- `rastan_maincpu` — the arcade ROM, accessible for reading attr_word and tile code data

The hook must:
1. Read strip_index from workram[0x10CA]
2. Read dest_ptr from workram[0x10A0]
3. Validate dest_ptr using the C-window range check (0xC00000–0xC03FFF)
4. Derive dest_row (= (dest & 0x3FC) >> 2 = bits 2..7 of offset, maps to row 0..63 but BG row
   in nametable context is 0..31 after masking with 0x1F) and dest_col
5. Walk the 16 descriptors, compute each tile_attr (via tile LUT and attr LUT), and write it
   to `staged_bg_buffer[row*128 + col*2]`
6. After writing each strip cell, set the corresponding bit in `bg_row_dirty`
7. Write updated dest_ptr back to workram[0x10A0]

---

## 4. Exact Genesis Translation Model for That Producer

### 4.1 WRAM Data Structures Required

**`staged_bg_buffer`** (already exists in rastan-direct `.bss`):
- Location: `.bss` section, aligned to 2
- Size: 2048 words = 4096 bytes
- Layout: row-major, 64 columns × 32 rows × 2 bytes
- Offset formula: `row * 128 + col * 2` (row 0–31, col 0–63)
- Content: Genesis nametable words (priority, palette, vflip, hflip, tile_index)

**`bg_row_dirty`** (must be added, replaces `bg_dirty`):
- Location: `.bss` section
- Size: 1 longword (4 bytes = 32 bits)
- Semantics: bit N set means row N of staged_bg_buffer has been written by the arcade hook
  and has not yet been committed to VRAM by the VBlank handler
- Bit 0 = row 0, bit 31 = row 31
- Init value for first frame: `0xFFFFFFFF` (all rows dirty, forces full commit on frame 1)
- Set by: the BG hook, for each row written during a strip commit
- Cleared by: the VBlank commit function, per row, after writing that row to VRAM

**`ARCADE_FIX_DEST_BG`** (already at 0xFF10A0 in rastan-direct):
- Must be initialized to 0x00C00000 before first arcade tick (already done in `init_staging_state`)
- This is the DEST_PTR_NEVER_INITIALIZED fix already implemented in the direct branch

**LUT tables required (ROM-resident, must exist in rastan-direct ROM)**:
- `genesistan_pc080sn_tile_vram_lut[16384]` — 32768 bytes, arcade tile code → Genesis VRAM slot
- `genesistan_pc080sn_attr_lut[32]` — 64 bytes, 5-bit attr_key → Genesis nametable upper bits
- `rastan_maincpu` — arcade ROM binary, accessible for desc/tile reads

### 4.2 Tile Index Translation

Arcade tile code (14-bit, masked from `tile_word & 0x3FFF`) → Genesis VRAM tile index via:
```
vram_slot = genesistan_pc080sn_tile_vram_lut[arcade_tile]
```
The LUT is a precomputed 16384-entry table generated by `tools/translation/precompute_pc080sn_tile_lut.py`. It statically assigns Genesis VRAM slots to all arcade tile codes that appear in any PC080SN strip table. Tile 0 maps to VRAM slot 0 (blank). Unseen tiles map to slot 0.

For rastan-direct, this same LUT must be linked in as `.rodata_bin`. The tile pixel data for
each assigned slot must be preloaded to VRAM before the first arcade tick (one-time, at init).

### 4.3 Attribute Word Translation

From the arcade `attr_word`:
```
pal   = attr_word & 0x03         (palette, bits 0-1)
hflip = (attr_word >> 14) & 0x01 (horizontal flip, bit 14)
vflip = (attr_word >> 15) & 0x01 (vertical flip, bit 15)
prio  = (attr_word >> 13) & 0x01 (priority, bit 13)
key   = (prio << 4) | (vflip << 3) | (hflip << 2) | pal
attr_partial = genesistan_pc080sn_attr_lut[key]
```

The full Genesis nametable word is: `attr_partial | vram_slot`

This gives:
- Bit 15: priority
- Bits 14–13: palette
- Bit 12: vflip
- Bit 11: hflip
- Bits 10–0: VRAM tile index

This is verified correct in `Andy_tilemap_correctness_audit.md` (Section 4, attribute LUT mapping).

### 4.4 Row/Strip Dirty Semantics

The PC080SN BG strip producer writes 4 rows of tile data per call (one strip = 4 rows for BG).
Each descriptor in the 16-descriptor outer loop writes cells at rows `dest_row, dest_row+1,
dest_row+2, dest_row+3` (wrapping mod 32). After the hook writes any row, it sets the
corresponding bit in `bg_row_dirty`.

A "row dirty" means: row N of `staged_bg_buffer` has been modified since the last VBlank commit.
The VBlank commit function reads `bg_row_dirty`, commits each dirty row to VRAM Plane B, and
clears each bit after committing.

### 4.5 Exact Flow

```
arcade produces strip:
  arcade code reaches 0x055968 (BG strip producer)
      ↓
  hook fires (assembly stub in rastan-direct, JSR at patched 0x055968):
      read strip_index from workram[0x10CA]
      read dest_ptr from workram[0x10A0]
      if dest_ptr not in 0xC00000..0xC03FFF:
          advance dest_ptr += 16*0x400; write back; return
      derive dest_row = (offset >> 2) & 0x1F; derive dest_col = (offset >> 8) & 0x3F
      outer loop (16 descriptors):
          load desc_addr from workram[0x1000 + desc_idx*4]
          skip if invalid (addr==0 or addr odd or addr>0x5FFFC)
          load attr_word from rastan_maincpu[desc_addr]
          load table_base from rastan_maincpu[desc_addr+2]
          compute attr_key; load attr_partial from genesistan_pc080sn_attr_lut
          inner loop (4 rows):
              tile_code = rastan_maincpu[table_base + strip_index*2 + cell*8] & 0x3FFF
              vram_slot = genesistan_pc080sn_tile_vram_lut[tile_code]
              tile_attr = attr_partial | vram_slot
              offset = row * 128 + col * 2
              staged_bg_buffer[offset] = tile_attr    ; WRAM write
              set bit row in bg_row_dirty             ; mark this row dirty
              row++; row &= 0x1F
          col += 4; col &= 0x3F
          dest_ptr += 0x400
      write dest_ptr back to workram[0x10A0]
      ↓
VBlank fires:
  vdp_commit_bg_strips_if_dirty:
      load bg_row_dirty
      if zero: return immediately
      for each set bit N (row N):
          vram_addr = VRAM_PLANE_B_BASE + N * 128
          issue VDP write command for vram_addr
          copy 64 words from staged_bg_buffer[N*64] to VDP data port
          clear bit N in bg_row_dirty
```

---

## 5. Rainbow Islands Alignment Analysis

### 5.1 Structural Pattern Comparison

| Aspect | Rainbow Islands | Rastan rastan-direct | Match? |
|--------|----------------|----------------------|--------|
| Arcade strip producer fires per frame | YES (game state machine writes tile data) | YES (arcade code at 0x055968 fires multiple times per frame via dispatcher) | YES |
| Hook intercepts strip write at hardware boundary | YES (writes to WRAM staging, not PC080SN hardware) | YES (JSR at 0x055968 before any hardware write) | YES |
| Staging in WRAM per-strip | YES (`0xFFFFF644` source ptr, 40 words/strip) | YES (`staged_bg_buffer[row*128+col*2]`) | YES |
| Flag marks strip dirty | YES (`0xFFFFF63C` flag) | YES (`bg_row_dirty` bit per row) | YES |
| VBlank commits only dirty strips | YES (flag gate, partial plane write) | YES (iterate bg_row_dirty bits, commit only set rows) | YES |
| Write granularity | 40 words/strip (40-cell wide RI plane) | 64 words/row (64-cell wide Rastan plane) | YES (adapted for geometry) |
| Full-plane commit never occurs in steady state | YES | YES (after frame 1 init) | YES |
| Commit is CPU direct port writes (not DMA) | YES | YES | YES |
| Scroll committed after display-ON | YES | YES (existing rastan-direct architecture) | YES |

### 5.2 Geometry Difference

Rainbow Islands uses a 40-cell wide visible plane (40 words/strip). Rastan uses a 64-cell wide
nametable (64 words/row). The strip granularity is therefore 64 words in rastan-direct vs 40
words in Rainbow Islands. This is an adaptation to Rastan's geometry, not a divergence from the
architectural pattern.

### 5.3 Strip Cadence

Rainbow Islands: the strip commit dispatcher at 0x073C is called once per VBlank by the VBlank
ISR. It calls the writer 0x1A70 which advances `0xFFFFF644` (source ptr) and `0xFFFFF648`
(dest command) incrementally.

Rastan: the arcade BG strip producer at 0x055968 is called by the dispatcher at 0x55948, which
is called from multiple arcade state machine sites. In a typical attract-mode frame, the
dispatcher fires once or twice. Each call produces one strip for each of the 16 descriptors.
The hook captures each call immediately, staging all 16×4-row writes to `staged_bg_buffer` and
marking the written rows dirty.

The key structural identity is: both systems write partial plane data (per-strip) to WRAM, gate
commit on a dirty flag, and commit only the written strips during VBlank. Rastan adapts the
RI pattern to the arcade's own strip cadence rather than imposing a fixed per-VBlank strip
advancement.

### 5.4 Is the Rastan Approach a Valid Direct Analog?

YES. The Rastan approach mirrors the Rainbow Islands architecture at the pattern level:
- WRAM staging buffer populated by producer (arcade hook)
- Per-strip dirty tracking (row bits vs single flag)
- VBlank consumes dirty state and publishes to VDP
- VBlank is commit-only (no logic)

The rastan-direct approach is more granular (32 row bits vs 1 flag) because Rastan's strip
producer can update arbitrary rows per call rather than a single sequential stream. This is
strictly better, not a divergence.

---

## 6. Address / Hook / Conversion Drift Risk Analysis

### 6.1 Address Drift

**Hook address 0x055968** — this is an address in the arcade maincpu ROM binary, not in the
Genesis address space. The arcade ROM is a fixed binary artifact. It does not change as the
direct execution architecture evolves. The address 0x055968 is confirmed in three independent
sources: the disassembly (showing the function entry), the SGDK branch's
`startup_title_remap.json` (showing the patch already applied), and the original bytes field
(`206D10A0...`) which exactly matches the disassembly of `moveal %a5@(4256),%a0` at that address.

**Anchor strategy**: The `startup_title_remap.json` patch entry for 0x055968 includes
`"original_bytes": "206D10A0..."` — a byte-exact match guard. If the arcade ROM binary ever
changes such that the bytes at 0x055968 no longer match, the postpatch toolchain will reject
the patch. This prevents silent drift. No additional guard is needed beyond the existing
original_bytes verification.

**Is 0x055968 in startup_title_remap.json?** YES — confirmed at line 1057 with
`JSR genesistan_hook_tilemap_plane_a` as the replacement and original bytes present.

For rastan-direct, the same `startup_title_remap.json` patch file applies to the same arcade
ROM binary. The patch entry is already present. The rastan-direct hook only needs to provide
the implementation behind the patched call target.

### 6.2 Hook Contract Drift

When the hook at 0x055968 fires:

**Registers that must hold valid state**:
- `%a5` must point to arcade WRAM base — this is the arcade's own invariant, established by the
  arcade startup sequence. The rastan-direct `init_staging_state` already sets `ARCADE_FIX_DEST_BG`
  (= 0xFF10A0) before first tick. The A5 WRAM base is the same invariant that drives every
  other arcade WRAM access in the system.
- `%a0`, `%d0`, `%d1` etc. are scratch within the hook (hook saves/restores full register state)
- No other register has a hook contract requirement at the 0x055968 entry point

**WRAM state that must be valid**:
- `workram[0x1000..0x103F]`: 16 descriptor pointers — populated by arcade init sequence. The
  hook guards against invalid descriptors (`btst #0, %d3` and `cmpi.l #0x5FFFC, %d3`), so
  zero-initialized entries are silently skipped.
- `workram[0x10CA]`: strip_index — written by the arcade code before calling 0x55948. Valid
  from the first call.
- `workram[0x10A0]`: dest_ptr — MUST be initialized to 0x00C00000 by Genesis init before first
  tick. Already implemented in `init_staging_state` via `move.l #0x00C00000, ARCADE_FIX_DEST_BG`.

**What breaks if adjacent arcade code is patched later**:
- The dispatcher at 0x55948 calls BG at 0x55950 (BSR to 0x55968) and FG at 0x5595A (BSR to
  0x55990). If 0x55948 or 0x55950 are patched, the BG hook call could be silenced. Guard:
  the `startup_title_remap.json` original_bytes check will fail if those bytes change.
- The strip_index write site at 0x559c2 (`movew %a5@(4298),%d7`) is inside the inner writer at
  0x559b2, which is the original function being replaced. After patching 0x055968 to JSR to
  the hook, 0x559b2 is never reached — the hook replaces the whole function. No drift risk.

### 6.3 Conversion Drift (DEST_PTR_NEVER_INITIALIZED)

**In rastan-direct, is the DEST_PTR_NEVER_INITIALIZED bug present?**

PARTIALLY. The `init_staging_state` function (main_68k.s lines 262–263) already contains:
```asm
move.l  #0x00C00000, ARCADE_FIX_DEST_BG   ; = 0xFF10A0
move.l  #0x00C08000, ARCADE_FIX_DEST_FG   ; = 0xFF10A4
```

These writes initialize the dest_ptr fields in WRAM before first tick. The DEST_PTR fix is
already in place in rastan-direct. The bug that plagued the SGDK branch (workram 0x10A0 stayed
zero for 768 frames) does not exist in rastan-direct because the fix is already present.

**Will the tile LUT and attr LUT conversion formula be correct from day one?**

YES, if the LUTs are correctly linked into rastan-direct. The LUTs are precomputed Python
artifacts (`pc080sn_tile_vram_lut.bin`, `pc080sn_attr_lut.bin`). Their correctness has been
verified in `Andy_tilemap_correctness_audit.md` Sections 4 and 5. The conversion formula is
the same formula proven in the SGDK branch. The only new requirement is that both LUT binaries
and the arcade ROM (`rastan_maincpu`) are accessible in the rastan-direct address space.

**What requires iteration?** Only the visual verification that tile pixel data is correctly
preloaded to VRAM. If the VRAM preload step is absent or incomplete, tiles will render as blank
(VRAM slot contains zeros), but the nametable structure will be correct. This is a VRAM preload
concern, not a hook or conversion concern.

### 6.4 Commit-Model Drift

**Current state**: `vdp_commit_bg` in rastan-direct uses a 1-byte `bg_dirty` flag and commits
all 2048 words when set. This is structurally wrong for the final port as documented in
`Andy_vblank_efficiency_audit_and_transition_plan.md` Section 3.

**What the hook needs**: The hook must set dirty bits per row. The VBlank commit must iterate
those bits and commit only dirty rows.

**Can it start coarse and refine?** NO. The current whole-plane `bg_dirty` flag is
incompatible with the arcade hook model for two reasons:
1. The hook writes 4 rows per call across 16 descriptors (up to 64 rows written per strip
   producer call). If `bg_dirty` is set as a single byte, any strip write triggers a
   2048-word full-plane commit on the next VBlank. At 14 cycles/word × 2048 words × 2 (dbra)
   = ~57,344 cycles per commit — exceeding the 7,400-cycle VBlank budget by 7.75×.
2. This would fire every frame (not just frame 1), making the port non-functional at 60Hz.

The per-row dirty model (`bg_row_dirty` as a 32-bit mask) must be introduced simultaneously
with the hook. The two changes are co-dependent and must be implemented in a single step.

### 6.5 Visibility Drift

**How to verify the first hook produces real arcade tile data, not a different synthetic artifact**:

1. **Expected negative result first**: Remove the checkerboard init (the BG row loop in
   `init_staging_state` that writes 0x0001/0x0002 checkerboard to `staged_bg_buffer`). If
   `bg_row_dirty` is initialized to 0 instead of 0xFFFFFFFF, the screen will be dark (no BG
   tiles committed) until the first arcade strip producer call fires. This confirms the VBlank
   path is correctly gated on dirty bits.

2. **Hook fires confirmation**: In BlastEm debugger, set a breakpoint at the hook entry point.
   The hook fires within the first few frames of arcade execution. Confirm registers/WRAM state
   (A5 = WRAM base, workram[0x10A0] = valid 0xC00000-range value, strip_index = 0–3).

3. **WRAM contents after hook**: After hook fires, read `staged_bg_buffer`. Entries should be
   non-zero and non-uniform (not the synthetic checkerboard). The values will be Genesis
   nametable words with tile indices from `genesistan_pc080sn_tile_vram_lut`.

4. **VRAM contents after VBlank**: After VBlank commit, read VRAM Plane B (0xC000–0xCFFF).
   The committed words should match the WRAM staging buffer for the dirty rows.

5. **Screen**: Background should show Rastan arcade tile content (stone/ground/sky patterns
   of attract mode scene 1), not a synthetic checkerboard. If tile pixel data is preloaded
   correctly, colors and shapes should be recognizable as Rastan arcade background tiles.

---

## 7. First Dirty-Tracking Model Definition

### 7.1 Data Structure

Replace `bg_dirty: .byte 0` in the `.bss` section with `bg_row_dirty: .long 0`.

```
.bss
; ...
bg_row_dirty:
    .long 0     ; bit N = row N of staged_bg_buffer is dirty, needs VBlank commit
```

### 7.2 Initialization Value

In `init_staging_state`, replace `move.b #1, bg_dirty` with `move.l #0xFFFFFFFF, bg_row_dirty`.
This marks all 32 rows dirty on frame 1, ensuring the full checkerboard (or initial arcade
content if hook fires before frame 1 VBlank) is committed on the first VBlank.

### 7.3 When Bits Are Set

The BG hook assembly stub, after writing each tile_attr word to `staged_bg_buffer[row*128+col*2]`,
sets the corresponding bit in `bg_row_dirty`:

```asm
; after writing to staged_bg_buffer at row %d1:
moveq   #0, %d0
or.w    %d1, %d0        ; d0 = row number
moveq   #1, %d3
lsl.l   %d0, %d3        ; d3 = 1 << row
or.l    %d3, bg_row_dirty
```

Because the hook writes 4 rows per descriptor, and 16 descriptors per strip call, it sets at
most 64 row bits per call (with wrapping mod 32, so at most 32 distinct bits = all rows).
In practice, each strip call covers 4 rows per descriptor group, each descriptor uses
4 consecutive rows — the exact range depends on dest_row at call time.

### 7.4 When Bits Are Cleared

The VBlank commit function `vdp_commit_bg_strips_if_dirty` clears each bit after committing
the corresponding row to VRAM:

```asm
vdp_commit_bg_strips_if_dirty:
    move.l  bg_row_dirty, %d7
    beq.s   .Lbg_strips_done       ; no dirty rows, return immediately
    moveq   #31, %d6               ; row counter 31..0
.Lbg_strip_loop:
    btst    %d6, %d7               ; is this row dirty?
    beq.s   .Lbg_strip_skip
    ; compute VRAM address for row %d6: VRAM_PLANE_B_BASE + d6*128
    ; issue VDP write command for that address
    ; copy 64 words from staged_bg_buffer[d6*64] to VDP_DATA
    ; clear bit d6 in bg_row_dirty
    bclr    %d6, bg_row_dirty
.Lbg_strip_skip:
    dbra    %d6, .Lbg_strip_loop
.Lbg_strips_done:
    rts
```

Bits are cleared immediately after commit. If the hook sets a bit again before the next VBlank,
the commit will fire again for that row. This is correct: the arcade producer may update any row
multiple times per frame if it calls the strip producer multiple times.

### 7.5 Alignment with Rainbow Islands Model

Rainbow Islands uses a single flag word `0xFFFFF63C` (commit request) plus source/dest pointer
staging. Rastan's 32-bit `bg_row_dirty` is a per-row extension of the same pattern: each bit is
an independent commit request for one row. The VBlank consumer tests the mask (analogous to
testing `F63C != 0`) and iterates only the set bits (analogous to advancing source/dest pointers
for each strip). The commit function returns immediately if `bg_row_dirty == 0` — zero overhead
on frames where no BG content changed.

### 7.6 Why Row-Level (32 bits) Is the Correct First Granularity

The PC080SN BG strip producer writes 4 rows per descriptor per call. With 32 rows in the
Genesis 64×32 BG nametable, a 32-bit mask provides exact per-row tracking. This is the minimum
granularity that fully captures what the arcade producer actually writes. Coarser (single dirty
flag) overcommits (full 2048-word write). Finer (per-cell dirty) is unnecessary overhead
(each cell is independently tracked, but the VDP write address mechanism writes whole rows
efficiently via auto-increment). Row-level is the correct granularity.

---

## 8. Single Next Implementation Step for Cody

### Step: Implement BG Strip Hook with Per-Row Dirty Tracking

This is ONE step. It consists of the following atomic changes to `apps/rastan-direct/`:

#### 8.1 Replace bg_dirty with bg_row_dirty in .bss

In `apps/rastan-direct/src/main_68k.s`, in the `.bss` section:
- Remove: `bg_dirty: .byte 0`
- Add: `bg_row_dirty: .long 0`

All references to `bg_dirty` (tst.b, clr.b, move.b #1) must be updated to use `bg_row_dirty`.

#### 8.2 Update init_staging_state

In `init_staging_state`:
- Replace `move.b #1, bg_dirty` with `move.l #0xFFFFFFFF, bg_row_dirty`
- Keep the checkerboard BG init loop AS-IS for now. The hook will overwrite it in subsequent
  frames. The checkerboard is initial content only; it confirms frame-1 commit works.

#### 8.3 Add Required Data to ROM

Add to the rastan-direct link configuration:
- `genesistan_pc080sn_tile_vram_lut` — the 32768-byte precomputed LUT binary
- `genesistan_pc080sn_attr_lut` — the 64-byte precomputed LUT binary
- `rastan_maincpu` — the arcade ROM binary (the same binary used by the SGDK branch)
- All three must be accessible at their linked addresses for the hook assembly to reference them

#### 8.4 Add BG Hook Assembly Stub

Add a new assembly function `rastan_direct_bg_hook` (or rename `vdp_commit_bg` to repurpose)
in `main_68k.s` or a new file `hooks.s`:

The function must:
1. Save registers (`movem.l %d0-%d7/%a0-%a6, -(%sp)`)
2. Load A5 = arcade WRAM base (the same base used by arcade code)
3. Read strip_index from `0(%a5, 0x10CA)` (= `ARCADE_FIX_DEST_BG - 0x10A0 + 0x10CA`)
4. Read dest_ptr from `ARCADE_FIX_DEST_BG` (= 0xFF10A0)
5. Validate dest_ptr (must be in 0xC00000–0xC03FFF range)
6. If invalid: advance dest_ptr += 16 * 0x400 = 0x4000; write back; restore; rts
7. Compute dest_row = ((dest_ptr - 0xC00000) >> 2) & 0x1F
8. Compute dest_col = ((dest_ptr - 0xC00000) >> 8) & 0x3F
9. Load desc list base: A0 = arcade WRAM base + 0x1000
10. Load rastan_maincpu base: A1 = rastan_maincpu
11. Load tile LUT: A2 = genesistan_pc080sn_tile_vram_lut
12. Load attr LUT: A3 = genesistan_pc080sn_attr_lut
13. Load staged_bg_buffer base: A4 = staged_bg_buffer
14. Outer loop (D6 = 15 downto 0, 16 descriptors):
    a. Load desc_addr: `move.l (%a0)+, %d3`
    b. Guard: `btst #0, %d3; bne .Lbg_invalid`
    c. Guard: `cmpi.l #0x5FFFC, %d3; bhi .Lbg_invalid`
    d. Load attr_word: `move.w 0(%a1,%d3.l), %d4`
    e. Load table_base: `move.w 2(%a1,%d3.l), %d3`
    f. Guard table_base: `cmpi.w #0x7FE0, %d3; bhi .Lbg_invalid`
    g. Build attr_key (5-bit) from %d4: pal=bits0-1, hflip=bit14, vflip=bit15, prio=bit13
    h. Load attr_partial: `lsl.w #1, key; move.w 0(%a3, key.w), %d4`
    i. Compute tile table pointer: A4_tmp = A1 + table_base + strip_index*2
    j. Inner loop (D4_inner = 3 downto 0, 4 rows):
       - Load tile code: `move.w 0(%a4_tmp), %d0; andi.w #0x3FFF, %d0`
       - Look up VRAM slot: `lsl.w #1, %d0; move.w 0(%a2, %d0.w), %d0`
       - Combine: `or.w %d4, %d0` (tile_attr = attr_partial | vram_slot)
       - Compute buffer offset: `move.w %d1, %d2; lsl.w #7, %d2; add.w dest_col_reg, %d2; add.w dest_col_reg, %d2`
       - Write: `move.w %d0, 0(%a4_buf, %d2.w)` (staged_bg_buffer write)
       - Set dirty bit: `moveq #1, %d2; lsl.l %d1, %d2; or.l %d2, bg_row_dirty`
       - Advance tile pointer: `adda.w #8, %a4_tmp` (stride = 8 bytes per row in BG)
       - Increment row: `addq.w #1, %d1; andi.w #0x1F, %d1`
    k. `.Lbg_invalid`: `addq.w #4, %d1; andi.w #0x1F, %d1` (skip 4 rows)
    l. Advance dest_ptr accumulator: `addi.l #0x400, %d5`
15. Write updated dest_ptr back to ARCADE_FIX_DEST_BG
16. Restore registers; rts

This function is registered as the JSR target at 0x055968 in `startup_title_remap.json`. The
patch entry already exists in the spec. Cody must provide the implementation at the symbol
name used in the replacement_bytes field.

For rastan-direct, the hook symbol name need not be `genesistan_hook_tilemap_plane_a` (that is
the SGDK branch C function name). The rastan-direct hook can be named `rastan_direct_bg_hook`
as long as the spec patch entry is updated to reference the correct symbol.

#### 8.5 Replace vdp_commit_bg with vdp_commit_bg_strips_if_dirty

In `_VINT_handler`, replace `bsr vdp_commit_bg` with `bsr vdp_commit_bg_strips_if_dirty`.

Replace the `vdp_commit_bg` function with `vdp_commit_bg_strips_if_dirty`:

```asm
vdp_commit_bg_strips_if_dirty:
    move.l  bg_row_dirty, %d7
    beq.s   .Lbg_strips_done

    ; also handle tiles if dirty (keep existing tiles_dirty check here for now)
    tst.b   tiles_dirty
    beq.s   .Lbg_no_tiles
    bsr     vdp_commit_tiles_if_dirty
.Lbg_no_tiles:

    moveq   #31, %d6              ; iterate rows 31..0
.Lbg_strip_loop:
    btst    %d6, %d7
    beq.s   .Lbg_strip_skip

    ; VRAM address for this row: VRAM_PLANE_B_BASE + row * 128
    move.l  #VRAM_PLANE_B_BASE, %d0
    move.w  %d6, %d1
    lsl.w   #7, %d1               ; row * 128
    add.l   %d1, %d0
    bsr     vdp_set_vram_write_addr

    ; source: staged_bg_buffer + row * 64 words = row * 128 bytes
    lea     staged_bg_buffer, %a0
    move.w  %d6, %d1
    lsl.w   #7, %d1               ; row * 128 bytes offset
    adda.w  %d1, %a0

    ; write 64 words for this row
    move.w  #(64 - 1), %d1
.Lbg_row_copy:
    move.w  (%a0)+, VDP_DATA
    dbra    %d1, .Lbg_row_copy

    ; clear this row's dirty bit
    bclr    %d6, bg_row_dirty

.Lbg_strip_skip:
    dbra    %d6, .Lbg_strip_loop

.Lbg_strips_done:
    rts
```

#### 8.6 Verify Arcade WRAM Base for rastan-direct

The hook reads `workram[0x10A0]` (dest_ptr) from `ARCADE_FIX_DEST_BG` = 0xFF10A0 and
`workram[0x10CA]` (strip_index) from offset 0xFF10CA. The arcade WRAM base at 0xFF0000 (WRAM
start) with A5 pointing there is the existing convention. The `init_staging_state` already
initializes 0xFF10A0 and 0xFF10A4. The desc list at 0xFF1000 (0xFF0000 + 0x1000) must be
populated by the arcade init sequence.

For rastan-direct (which does not run the full arcade init before tick), the desc list at
0xFF1000 will be zero-initialized. The hook guard (`btst #0, %d3; bne skip`) will skip all
zero descriptors cleanly. This means the first few frames may produce no output (desc list
empty), which is correct — the arcade init sequence will populate the desc list as it runs.

If the full arcade init is not run in rastan-direct, the desc list will remain zero and the
hook will always skip all descriptors. In that case, the WRAM `bg_row_dirty` will only be set
by the frame-1 initialization (all-ones), and subsequent frames will commit nothing. This is
the fallback: the checkerboard (from the synthetic init loop that runs on frame 1) will be
visible. This is still verifiable progress — it means the VBlank strip commit path works,
and adding arcade ROM execution will activate the desc list and produce real tile data.

#### 8.7 summary of exact files changed in rastan-direct

1. `apps/rastan-direct/src/main_68k.s`:
   - Remove `bg_dirty: .byte 0` from `.bss`; add `bg_row_dirty: .long 0`
   - Replace `move.b #1, bg_dirty` in `init_staging_state` with `move.l #0xFFFFFFFF, bg_row_dirty`
   - Replace `tst.b bg_dirty` / `beq .Lbg_done` / `clr.b bg_dirty` with the new strip commit
   - Replace `bsr vdp_commit_bg` in `_VINT_handler` with `bsr vdp_commit_bg_strips_if_dirty`
   - Add `vdp_commit_bg_strips_if_dirty` function body
   - Add `rastan_direct_bg_hook` function body (or in a new hooks.s)
   - Add `ARCADE_FIX_DEST_BG` and related constants if not already declared (they are: line 30–31)

2. `specs/startup_title_remap.json`:
   - The patch at 0x055968 already uses `{symbol:genesistan_hook_tilemap_plane_a}` as the JSR
     target. For rastan-direct, either: (a) provide a function at that exact symbol name, or
     (b) update the patch entry `replacement_bytes` to reference a new rastan-direct symbol name.
   - The patch entry is already present and correct — only the implementation symbol must exist.

3. Link configuration (linker script or build system):
   - Add `pc080sn_tile_vram_lut.bin` as `.rodata_bin` section with symbol
     `genesistan_pc080sn_tile_vram_lut`
   - Add `pc080sn_attr_lut.bin` with symbol `genesistan_pc080sn_attr_lut`
   - Add `rastan_maincpu` ROM region

---

## 9. Immediate Follow-On Sequence

After the single next step (BG hook + per-row dirty tracking) is verified and produces real
arcade tile data on screen:

### Step 2: Move Tile Commit to Top-Level VBlank Step

Remove the `bsr vdp_commit_tiles_if_dirty` from inside `vdp_commit_bg_strips_if_dirty`.
Add it as the first explicit call in `_VINT_handler` after display-OFF, before the strip commit.
This aligns with Rainbow Islands where each commit type is a top-level VBlank call.

### Step 3: Retire the Synthetic Checkerboard

Remove the BG checkerboard init loop from `init_staging_state` (the `.Lbg_row` / `.Lbg_col`
loop that writes 0x0001/0x0002 to `staged_bg_buffer`). Once the arcade hook is proven to
produce tile data, the synthetic init is no longer needed. The `bg_row_dirty = 0xFFFFFFFF`
init ensures the first VBlank commits whatever was staged (initially by the hook).

Retirement condition: arcade hook has been verified to produce recognizable tile output on
screen for at least one complete attract-mode frame cycle.

### Step 4: Implement the FG Strip Hook

Add `rastan_direct_fg_hook` at 0x055990 (the FG strip producer). The hook structure mirrors
the BG hook exactly, using:
- `ARCADE_FIX_DEST_FG` (= 0xFF10A4) for dest_ptr
- `staged_fg_buffer` as the staging buffer
- `fg_row_dirty: .long 0` for the FG dirty mask
- FG strip formula: `tile_addr = table_base + strip_index*8 + col*2`
- FG VRAM target: VRAM_PLANE_A_BASE (0xE000)

Add `vdp_commit_fg_strips_if_dirty` to `_VINT_handler`.

FG hook is NOT implemented in the same step as BG. BG must be verified first.

### Step 5: Implement Real Arcade Palette Staging

Replace the current `palette_init_words` synthetic palette with real arcade palette data.
Add the arcade palette write hook (CLCS) at the arcade palette register write sites.
Replace `staged_palette_words` static init with dynamic arcade-sourced palette staging.

This is deferred until BG + FG tile output is confirmed correct, because palette errors on
correct tile output are much easier to diagnose than tile errors on wrong palette.

### Step 6: Implement Real Arcade Scroll Staging

Replace the synthetic `arcade_tick_logic` scroll driver with arcade-sourced scroll values.
Add the arcade PC080SN scroll write hook (0x055AB4 etc.) to stage scroll values into the
existing `staged_scroll_x_bg`, `staged_scroll_y_bg`, `staged_scroll_x_fg`, `staged_scroll_y_fg`
WRAM words. Remove `arcade_tick_logic`.

### Step 7: First Complete Arcade-Driven Attract-Mode Frame

When BG hook, FG hook, palette hook, and scroll hook are all active simultaneously, the
synthetic scaffolding (`arcade_tick_logic`, `palette_init_words`, `tile_init_words`,
`palette_dirty` static flag) is fully retired. At this point rastan-direct has first complete
arcade-driven attract-mode graphics output, and the synthetic baseline is fully replaced.

---

## 10. What Must Not Be Done Yet

The following must NOT be implemented in the single next step or in any step before its
designated position in the sequence above:

1. **Do not hook FG (0x055990) in the same step as BG (0x055968)**. BG must be verified
   independently first. FG introduces additional state (mode word, inverted strip_index formula)
   and has its own dest_ptr. Mixing both in one step makes failures impossible to isolate.

2. **Do not introduce DMA for the BG strip commit**. CPU direct writes (move.w loop) are the
   correct mechanism for rastan-direct's strip-level partial commit. DMA transfers are
   appropriate for full-plane or large tile uploads, not for the 64-words-per-dirty-row strip
   commit. DMA setup overhead exceeds the savings for small transfers. Do not add DMA until a
   separate analysis justifies it.

3. **Do not remove the synthetic checkerboard before the arcade hook is verified**. The
   checkerboard is the baseline visual artifact. If the hook misbehaves, the checkerboard will
   be replaced with incorrect tile data, which may be harder to interpret than a missing
   checkerboard. Retire the checkerboard only after the hook output is confirmed recognizable.

4. **Do not hard-code tile VRAM slot assignments** without the `genesistan_pc080sn_tile_vram_lut`
   LUT infrastructure. The LUT is a precomputed 32768-byte table covering all possible 14-bit
   tile codes. Any hand-coded tile mapping will be incomplete and produce blank tiles for
   uncovered codes. The LUT binary must be linked in before the hook is enabled.

5. **Do not implement the arcade scroll hook** in the same step as the BG tile hook. Scroll
   values from `arcade_tick_logic` are synthetic but harmless. The tile hook adds enough new
   state that introducing scroll hook changes simultaneously would over-couple the changes.

6. **Do not implement the arcade palette hook** in the same step as the BG tile hook. The
   synthetic `palette_init_words` produces visible output with correct structure. Palette changes
   at the same time as tile hook changes make color/content failures ambiguous.

7. **Do not remove `arcade_tick_logic`** until both BG and FG hooks are active and arcade scroll
   hooks are in place. `arcade_tick_logic` currently drives the four scroll staging words. If it
   is removed before arcade scroll hooks are wired, the scroll commit will write zero scroll
   values unconditionally (correct for attract mode but masks the missing arcade scroll hook).

8. **Do not implement sprite path** (PC090OJ hook or SAT commit) before BG tile hook is
   verified. Sprites require a separate DMA VRAM destination bug fix (`lsr.l #14` vs `swap`) and
   a completely independent SAT commit pipeline. They do not affect BG tile verification.

9. **Do not skip the original_bytes guard in startup_title_remap.json**. The patch at 0x055968
   has `"original_bytes": "206D10A0..."`. This guard must not be weakened or removed. It is
   the anchor preventing silent address drift.

10. **Do not build rastan-direct with the arcade ROM executing its own init sequence without
    the TC0040IOC patches** that suppress hardware I/O accesses. If the arcade init runs
    unpatched, it will attempt to read from and write to TC0040IOC I/O addresses (0x380000,
    0x390000 range), causing bus errors on Genesis hardware. I/O patches are prerequisites for
    arcade code execution.

---

## 11. Final Verdict

| Task | Status |
|------|--------|
| First real arcade BG producer identified | YES — 0x055968, confirmed in disassembly, startup_title_remap.json, and original bytes |
| Genesis translation model defined | YES — staged_bg_buffer + bg_row_dirty 32-bit mask + tile LUT + attr LUT + DEST_PTR fix already in place |
| Rainbow Islands alignment analyzed | YES — Rastan strip hook model is a valid direct analog at architectural pattern level; 64-word rows vs RI 40-word strips is a geometry adaptation, not a divergence |
| Address / hook / conversion drift risks analyzed | YES — all 5 drift classes assessed with specific mitigations; original_bytes guard is the anchor; DEST_PTR fix already in rastan-direct |
| Dirty-tracking model defined | YES — bg_row_dirty 32-bit mask, bit per row, set by hook, cleared by VBlank commit, init 0xFFFFFFFF for frame 1, zero overhead when no rows dirty |
| Single next implementation step defined | YES — add bg_row_dirty, add BG hook assembly stub at 0x055968 target, replace vdp_commit_bg with vdp_commit_bg_strips_if_dirty |
| Immediate follow-on sequence defined | YES — 7 ordered steps: tile commit top-level, retire checkerboard, FG hook, palette hook, scroll hook, retire scaffolding |
| What must not be done yet | YES — 10 explicit prohibitions covering FG coupling, DMA premature introduction, checkerboard retirement order, hard-coded tile assignments, scroll/palette coupling, sprite path, I/O patch prerequisites |
| No implementation performed | YES |
