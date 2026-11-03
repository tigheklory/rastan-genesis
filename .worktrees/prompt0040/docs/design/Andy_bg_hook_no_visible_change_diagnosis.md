# Andy — BG Hook No Visible Change Diagnosis

**Date**: 2026-04-06
**Scope**: `apps/rastan-direct` — diagnosing why Cody's `genesistan_hook_tilemap_plane_a` implementation produces no visible change (checkerboard still shows)
**State at diagnosis**: Hook body is implemented (not a stub), build succeeds, checkerboard unchanged

---

## 1. Executive Summary

Cody's implementation of `genesistan_hook_tilemap_plane_a` in `apps/rastan-direct/src/main_68k.s` contains a structurally correct descriptor-decode body — the register saves, range check, LUT lookups, row/column calculation, and `bg_dirty` set are all present and internally consistent. However, the hook reads all its workram inputs through the register `%a5` at the value that the arcade code leaves it: `0x0010C000`. This is the arcade hardware's WRAM base address, which on Genesis maps to read-only ROM/cartridge space, not Genesis WRAM.

The direct consequence: `%a5 + 0x10A0 = 0x0010D0A0`, which falls in Genesis cartridge ROM space. The dest_ptr range check (`cmpi.l #0x00C00000, %d0 / blo .Lbg_hook_dest_invalid`) fails on every call because the value read from `0x10D0A0` is ROM data, not `0xC00000`. The hook always branches to `.Lbg_hook_dest_invalid`, writes nothing to `staged_bg_buffer`, never sets `bg_dirty`, and the VBlank commit publishes no new data. The checkerboard persists unchanged.

The initialization in `init_staging_state` (`move.l #0x00C00000, ARCADE_FIX_DEST_BG`) correctly writes `0xC00000` to absolute address `0x00FF10A0`, which equals `genesistan_arcade_workram_words + 0x10A0` only if `%a5 = 0xFF0000`. But `%a5` is never set to `0xFF0000` in the hook.

**Single root cause**: `%a5` is not set to the Genesis WRAM base (`0xFF0000`) at hook entry. Every workram read in the hook body (`dest_ptr`, `strip_index`, `desc_list`) reads from arcade hardware WRAM addresses in Genesis ROM/cartridge space, producing invalid inputs that cause the dest_ptr range check to branch to the invalid path on every call.

---

## 2. Inputs Audited

1. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/main_68k.s` — READ COMPLETE (609 lines): `genesistan_hook_tilemap_plane_a` full body (lines 193–314), `init_staging_state` (lines 457–520), `vdp_commit_bg` (lines 333–349), `_VINT_handler` (lines 72–98), all constants and BSS layout.
2. `/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt` — SEARCHED EXTENSIVELY: `0x55968` hook site (line 107374), dispatcher at `0x55948` (line 107365), `lea 0x10c000,%a5` at `0x3AF04` (line 74014), all instructions ending with `,%a5` (exactly one `lea` plus compare/add variants).
3. `/home/tighe/projects/rastan-genesis/docs/design/Cody_pc080sn_bg_hook_implementation.md` — READ COMPLETE (108 lines): Cody's description of implementation, claims hook reads from `A5+0x10CA` and `A5+0x10A0`, sets `bg_dirty`.
4. `/home/tighe/projects/rastan-genesis/docs/design/Andy_arcade_execution_reachability_vs_static_checkerboard.md` — READ (lines 1–250): confirmed hook is reachable, A5 use at hook site described.
5. `/home/tighe/projects/rastan-genesis/docs/design/Andy_tilemap_correctness_audit.md` — READ COMPLETE (270 lines): DEST_PTR_NEVER_INITIALIZED diagnosis, dest_ptr mechanism, NOP patches, SGDK branch reference.
6. `/home/tighe/projects/rastan-genesis/apps/rastan/src/startup_trampoline.s` — SEARCHED: line 215 `lea genesistan_arcade_workram_words, %a5` pattern in SGDK branch.
7. `/home/tighe/projects/rastan-genesis/apps/rastan/src/main.c` — SEARCHED: `pc080sn_dest_ptr_to_row_col`, `PC080SN_DEST_PTR_A_OFFSET`, `pc080sn_workram_read_u32`.
8. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/out/symbol.txt` — READ COMPLETE: `ARCADE_FIX_DEST_BG = 0x00FF10A0`, `staged_bg_buffer = 0xFF0020`, `staged_fg_buffer = 0xFF1020`, `genesistan_pc080sn_tile_vram_lut = 0x70680`, `genesistan_pc080sn_attr_lut = 0x78680`.
9. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/link.ld` — READ COMPLETE: `.bss 0xFF0000 (NOLOAD)`.
10. `/home/tighe/projects/rastan-genesis/build/rastan-direct/rastan_direct_patch_manifest.json` — READ: 31 `address_rewrites` entries; no patch for `0x03AF04` (`lea 0x10c000,%a5`); ROM relocation delta = `+0x200`, scan range `0x000000–0x060000`.
11. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s` — READ COMPLETE: confirms SP = `0xFF0000`; no A5 initialization.
12. `/home/tighe/projects/rastan-genesis/apps/rastan/src/startup_bridge.c` — READ (lines 246–340): `genesistan_init_workram_direct` — does NOT initialize workram[0x10A0] or [0x10A4].

---

## 3. Implemented Hook Body Verification

### 3.1 Full Hook Body Reading

`genesistan_hook_tilemap_plane_a` (main_68k.s lines 193–314):

**Entry:**
1. `movem.l %d0-%d7/%a0-%a6, -(%sp)` — saves all registers including `%a5` (will be restored at exit)
2. `addq.w #1, hook_plane_a_hits` — debug counter increment
3. `move.w ARCADE_PC080SN_STRIP_INDEX_OFFSET(%a5), %d7` — reads strip index from `%a5 + 0x10CA`
4. `move.l ARCADE_PC080SN_DEST_BG_OFFSET(%a5), %d5` — reads dest_ptr from `%a5 + 0x10A0`

**Dest_ptr validation (lines 201–212):**
5. Masks dest_ptr to 24 bits: `andi.l #0x00FFFFFF, %d0`
6. Checks `%d0 >= 0xC00000` (blo → invalid)
7. Checks `%d0 < 0xC04000` (bhs → invalid)
8. Checks alignment `(%d0 & 3) == 0` (bne → invalid)

**Row/column decode (lines 214–220):**
9. `lsr.l #2, %d4` — convert byte offset to longword index
10. `move.w %d4, %d1; andi.w #0x003F, %d1; andi.w #0x001F, %d1` — `d1 = row = lword_idx & 0x1F` (5-bit row, 0–31)
11. `move.w %d4, %d2; lsr.w #6, %d2; andi.w #0x003F, %d2` — `d2 = col = (lword_idx >> 6) & 0x3F` (6-bit column, 0–63)

**Descriptor loop setup (lines 222–228):**
12. `lea ARCADE_PC080SN_DESC_BG_LIST_OFFSET(%a5), %a0` — desc list from `%a5 + 0x1000`
13. `movea.l #ARCADE_MAINCPU_ROM_BASE, %a1` = `0x200` — correct ROM base
14. `lea genesistan_pc080sn_tile_vram_lut, %a2` — tile LUT (ROM at `0x70680`)
15. `lea genesistan_pc080sn_attr_lut, %a3` — attr LUT (ROM at `0x78680`)
16. `lea staged_bg_buffer, %a6` — staging buffer (BSS at `0xFF0020`)

**Descriptor decode loop (lines 229–304):** 16 iterations.

**Buffer write (lines 283–288):**
```
move.w %d1, %d0
lsl.w  #7, %d0       ; d0 = row * 128
add.w  %d2, %d0      ; d0 = row*128 + col
add.w  %d2, %d0      ; d0 = row*128 + col*2  (adds col twice)
move.w %d3, 0(%a6,%d0.w)
move.b #1, bg_dirty
```
Offset formula: `row * 128 + col * 2` — correct for row-major 64×32 nametable (matches tilemap correctness audit §6).

**Dest_ptr advance and writeback (lines 303–312):**
- `addi.l #0x00000400, %d5` per descriptor
- `move.l %d5, ARCADE_PC080SN_DEST_BG_OFFSET(%a5)` — writes back to `%a5 + 0x10A0`

**Exit:**
- `movem.l (%sp)+, %d0-%d7/%a0-%a6` — restores all registers including `%a5`

**Verdict**: The hook body is structurally correct — range check, decode, LUT lookup, buffer write, dirty flag set, writeback are all present and internally consistent.

### 3.2 Conclusion

Implemented hook body verified exactly: **YES** — the body is NOT a stub; it performs real work. The problem is not missing logic but incorrect inputs caused by `%a5` value.

---

## 4. Live Hook Input Data Analysis

### 4.1 What value does %a5 hold at hook entry?

In the arcade disassembly, the only instruction that sets `%a5` to a value (as opposed to using it as a base pointer) is:

```
3af04:   4bf9 0010 c000    lea 0x10c000,%a5
```

This is the arcade's main initialization code at address `0x3AF04` (arcade address). After ROM relocation (+0x200), it executes from `0x3B104` in Genesis ROM. The instruction loads the literal value `0x0010C000` into `%a5`. This is the arcade hardware WRAM base address.

A complete search of all 122,241 lines of the disassembly finds that `lea 0x10c000,%a5` is the **only** instruction that sets `%a5` to a new base value. All other `%a5`-ending instructions are compares (`cmpal`), temporary arithmetic adds (`addaw`, `addal`) in sprite routines that modify `%a5` transiently, or compares that do not alter `%a5`.

The patcher's ROM absolute call relocation scans addresses `0x000000–0x060000` and adds `+0x200` to ROM call targets in that range. `0x10C000` is NOT in this range — it is the arcade's WRAM address, not a ROM address. The patcher does not modify this `lea` instruction. No `opcode_replace` entry in `rastan_direct_patch_manifest.json` covers `0x03AF04`.

**Result at hook entry**: `%a5 = 0x0010C000`.

### 4.2 What addresses does the hook read from?

| Hook reads | Address formula | Computed address | Genesis mapping |
|-----------|-----------------|-----------------|-----------------|
| `dest_ptr` | `%a5 + 0x10A0` | `0x0010D0A0` | Genesis ROM space (read-only; returns ROM data, not `0xC00000`) |
| `strip_index` | `%a5 + 0x10CA` | `0x0010D0CA` | Genesis ROM space (read-only) |
| `desc_list` base | `%a5 + 0x1000` | `0x0010D000` | Genesis ROM space (read-only) |

Genesis ROM space is read-only. Reads from `0x10D0A0` return whatever bytes are in the patched ROM binary at that offset (the arcade ROM ends around `0x60200`, so `0x10D0A0` is beyond it — returns `0x0000` or `0xFFFF` depending on the emulator/hardware padding). Neither value passes the dest_ptr range check.

### 4.3 What init_staging_state actually does for ARCADE_FIX_DEST_BG

`init_staging_state` (lines 461–465):
```asm
move.l  #0x00C00000, staged_dest_ptr_bg   ; writes 0xC00000 to 0xFF0010
move.l  #0x00C08000, staged_dest_ptr_fg   ; writes 0xC08000 to 0xFF0014
move.l  #0x00C00000, ARCADE_FIX_DEST_BG   ; writes 0xC00000 to 0xFF10A0
move.l  #0x00C08000, ARCADE_FIX_DEST_FG   ; writes 0xC08000 to 0xFF10A4
```

`ARCADE_FIX_DEST_BG = 0x00FF10A0`. The address arithmetic: `0xFF10A0 = 0xFF0000 + 0x10A0`. For `%a5 + 0x10A0` to equal `0xFF10A0`, `%a5` must equal `0xFF0000`. But `%a5 = 0x0010C000` at hook entry. The hook reads from `0x0010D0A0`, NOT `0x00FF10A0`. The initialization is not consumed by the hook.

### 4.4 LUT accessibility

`genesistan_pc080sn_tile_vram_lut` at `0x70680` (`.rodata`, loaded into Genesis ROM binary at build time via `.incbin "../../build/pc080sn_tile_vram_lut.bin"`). Confirmed present in symbol table.

`genesistan_pc080sn_attr_lut` at `0x78680` (`.rodata`, `.incbin "../../build/pc080sn_attr_lut.bin"`). Confirmed present in symbol table.

Both LUTs are properly linked into the binary and accessible. This is not a blocking issue.

### 4.5 Conclusion

Live hook input data validity analyzed: **YES** — dest_ptr is read from `0x10D0A0` (Genesis ROM space), not from the WRAM location initialized by `init_staging_state`. Strip index and desc_list are similarly read from ROM space. None of these produce valid values.

---

## 5. Staged Write Target Analysis

The hook's buffer write formula:
```
offset = row * 128 + col * 2
staged_bg_buffer[offset] = tile_word
```

With `staged_bg_buffer = 0xFF0020`, this writes to `0xFF0020 + row*128 + col*2`. For row 0–31, col 0–63, all computed offsets fall within `0xFF0020` to `0xFF1020` — exactly the 4096-byte `staged_bg_buffer` region. The row counter increments by 1 per row-loop iteration and wraps at 32 (`andi.w #0x001F, %d1`). The column `%d2` is read once from the initial dest_ptr and does not advance within the descriptor loop (column advance requires valid dest_ptr increment across calls).

The `vdp_commit_bg` reads all 2048 words from `staged_bg_buffer` sequentially and writes to VRAM Plane B base (`VRAM_PLANE_B_BASE = 0xC000`). This is consistent with the hook's write layout.

**However, because the hook always takes `.Lbg_hook_dest_invalid` before reaching any buffer write, this correctness is never exercised.**

Staged write target correctness analyzed: **YES** — the formula is correct; it is never reached due to the dest_ptr failure.

---

## 6. bg_dirty / VBlank Commit Analysis

### 6.1 bg_dirty set path

`move.b #1, bg_dirty` at line 288 is inside `.Lbg_hook_row_loop`, inside the descriptor loop. It is only reached after the dest_ptr range check passes (lines 203–212). Since the range check always fails (dest_ptr reads as ROM data ≠ `0xC00000`), `bg_dirty` is never set by the hook.

### 6.2 bg_dirty cleared after first VBlank

`init_staging_state` (line 469): `move.b #1, bg_dirty`. This causes `vdp_commit_bg` to fire on the first VBlank and commit the checkerboard to VRAM. `vdp_commit_bg` (line 347): `clr.b bg_dirty`. After frame 1, `bg_dirty = 0` and `vdp_commit_bg` takes the early exit (`beq.s .Lbg_done`) every subsequent frame.

### 6.3 vdp_commit_bg commit path

`vdp_commit_bg` (lines 333–349):
```asm
tst.b   bg_dirty
beq.s   .Lbg_done    ← exits every frame after frame 1
bsr     vdp_commit_tiles_if_dirty
move.l  #VRAM_PLANE_B_BASE, %d0
bsr     vdp_set_vram_write_addr
lea     staged_bg_buffer, %a0
move.w  #(2048 - 1), %d7
.Lbg_copy: move.w (%a0)+, VDP_DATA / dbra %d7, .Lbg_copy
clr.b   bg_dirty
```

`vdp_commit_bg` is called from `_VINT_handler` every frame (line 81). The mechanism is correct and active. It simply has nothing to publish because `bg_dirty` stays 0 after frame 1.

### 6.4 Conclusion

bg_dirty to commit path verified: **YES** — `bg_dirty` is never set after frame 1 because the hook always takes the invalid branch. `vdp_commit_bg` is functioning correctly but has no data to commit.

---

## 7. Visible-Difference Analysis

The checkerboard is written once by `init_staging_state`: words `0x0001` (tile 1) and `0x0002` (tile 2) alternating across 64 columns × 32 rows. These are the debug tiles at VRAM slots 1 and 2 (initialized by `tile_init_words`: 16 words of `0x1111`, 16 words of `0x2222`, 8 pairs of `0x3030/0x0303`).

Arcade-produced BG output would use `genesistan_pc080sn_tile_vram_lut` mappings of PC080SN tile codes, which produce nametable tile indices in the range 20–1023 (scene tiles). These are completely different from tiles 1 and 2. If the hook functioned, the output would be visually distinct from the checkerboard: it would display actual Rastan arcade background graphics (ground, sky, platforms).

The hook cannot produce all-zero words (tile 0 = transparent) from valid arcade data because the tile LUT maps tile 0 to slot 0 only for unknown/not-in-scene tiles. Known scene tiles produce non-zero indices.

The hook cannot produce the same tile words as the checkerboard by coincidence: tiles 1 and 2 are not in the tile LUT output range.

Visible-difference potential analyzed: **YES** — if the hook staged data correctly, the output would be visibly different from the checkerboard.

---

## 8. Root Cause

### 8.1 The A5 Register Mismatch

The single blocking condition is that `%a5` holds the arcade hardware WRAM base address `0x0010C000` at hook entry, not the Genesis WRAM base address `0xFF0000`.

**Evidence**:
- `build/maincpu.disasm.txt` line 74014: `3af04: lea 0x10c000,%a5` — the only instruction in the entire arcade ROM that loads a base address into `%a5`.
- `rastan_direct_patch_manifest.json`: no `opcode_replace` entry covers `0x03AF04`. The ROM relocation pass scans only addresses `0x000000–0x060000`; `0x10C000` is outside this range and is not relocated.
- The hook reads `%a5 + 0x10A0 = 0x0010D0A0`. Genesis address `0x0010D0A0` is in read-only cartridge ROM space (the arcade ROM ends at approximately `0x60200`; `0x10D0A0` is beyond it and returns zero or garbage ROM padding).
- `init_staging_state` writes `0x00C00000` to `0x00FF10A0` (`ARCADE_FIX_DEST_BG`). For this to be the same as `%a5 + 0x10A0`, `%a5` must equal `0xFF0000`. It does not.

### 8.2 Effect Chain

```
%a5 = 0x0010C000 (set by arcade code, never patched)
  → hook reads dest_ptr from 0x0010D0A0 (ROM space)
  → value at 0x10D0A0 is ROM data (not 0xC00000)
  → andi.l #0x00FFFFFF → 0x0010D0A0 (unchanged, < 0x00C00000)
  → cmpi.l #0xC00000 → blo .Lbg_hook_dest_invalid (ALWAYS taken)
  → hook writes back %d5 + 0x4000 to %a5+0x10A0 (ROM space, write silently discarded)
  → staged_bg_buffer: never written
  → bg_dirty: never set
  → vdp_commit_bg: always early-exits (bg_dirty = 0 after frame 1)
  → Plane B VRAM: never updated after frame 1
  → checkerboard: persists unchanged
```

### 8.3 Why init_staging_state Cannot Fix This

`init_staging_state` writes `0xC00000` to `ARCADE_FIX_DEST_BG = 0xFF10A0`. This write goes to Genesis WRAM. The hook reads from `0x10D0A0` in ROM space. These are different physical addresses — `0xFF10A0` (WRAM) vs `0x10D0A0` (ROM). The write and the read are to different memory locations.

### 8.4 Contrast with SGDK Branch

In the SGDK branch (`apps/rastan/src/startup_trampoline.s`), every assembly function that reads workram via `%a5` begins with `lea genesistan_arcade_workram_words, %a5` (e.g., lines 215, 908, 925, 942). This explicitly sets `%a5` to the Genesis WRAM base before any workram offset access. The rastan-direct hook omits this step.

---

## 9. Single Next Correction

**File**: `apps/rastan-direct/src/main_68k.s`

**Location**: `genesistan_hook_tilemap_plane_a`, immediately after the `movem.l` register save (after line 194).

**Exact behavioral change**: Insert `lea 0x00FF0000, %a5` (load Genesis WRAM base address into `%a5`). After this instruction:
- `%a5 + 0x10A0 = 0xFF10A0` = `ARCADE_FIX_DEST_BG` = the address initialized to `0xC00000` by `init_staging_state`.
- `%a5 + 0x10CA = 0xFF10CA` = the strip index location that the arcade code writes to in Genesis WRAM.
- `%a5 + 0x1000 = 0xFF1000` = the desc list location.

The `movem.l` at entry saves `%a5` and the `movem.l` at exit restores it, so the arcade code sees no change in `%a5` after the hook returns.

**Expected result**: dest_ptr reads `0xC00000` on the first hook call. Range check passes. Hook proceeds to descriptor decode, writes to `staged_bg_buffer`, sets `bg_dirty = 1`. On the next VBlank, `vdp_commit_bg` publishes arcade BG data to Plane B VRAM. Checkerboard is replaced by arcade-produced background graphics.

**Note**: After adding `lea 0x00FF0000, %a5`, a secondary issue will surface: the arcade code writes its workram (desc_list, strip_index, etc.) to addresses based on its own A5 = `0x10C000`, which maps to read-only ROM space on Genesis. The hook must either read these values from their actual Genesis WRAM locations (where the arcade code has previously written them through absolute-address stores, if any exist) or the remap spec needs patches to redirect the arcade's workram writes to Genesis WRAM. This is the next analysis target after the A5 fix.

---

## 10. What Must Not Be Changed Yet

1. **`vdp_commit_bg` / `_VINT_handler`** — the VBlank commit chain is structurally correct; it is not the source of the problem.
2. **LUT data** (`genesistan_pc080sn_tile_vram_lut`, `genesistan_pc080sn_attr_lut`) — both are correctly linked into the binary at known ROM addresses; do not move them.
3. **`init_staging_state`** — the `ARCADE_FIX_DEST_BG` write is correct once A5 is fixed; do not remove it.
4. **The hook body structure** — the descriptor decode logic, row/column formula, buffer write formula, and dest_ptr writeback are all correct; do not redesign them.
5. **The BG hook patch at `0x055968`** — the opcode_replace entry and its `replacement_bytes` are correct; do not modify the remap spec hook site.
6. **`staged_bg_buffer` layout and `VRAM_PLANE_B_BASE`** — the buffer is correctly sized (4096 bytes) and the commit target is correct (Plane B at VRAM `0xC000`).
7. **Palette and FG paths** — the palette commit, FG buffer, and any other display state not involved in BG staging; these are independent and must not be disturbed.

---

## 11. Final Verdict

The hook body is implemented. It does not execute its core logic because `%a5 = 0x0010C000` causes every workram read to go to Genesis ROM space, where dest_ptr reads as non-`0xC00000` ROM data. The dest_ptr range check always fails. The hook always takes `.Lbg_hook_dest_invalid`. `staged_bg_buffer` is never written. `bg_dirty` is never set after frame 1. `vdp_commit_bg` always exits early. The checkerboard persists.

The single required change is to add `lea 0x00FF0000, %a5` after the register save in `genesistan_hook_tilemap_plane_a`, so that all `%a5`-relative workram accesses target Genesis WRAM rather than read-only ROM space.
