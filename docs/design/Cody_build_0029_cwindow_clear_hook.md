# Cody — Build 0029 C-Window Clear Hook Implementation

**Scope:** `apps/rastan-direct/src/main_68k.s` and `specs/rastan_direct_remap.json`

**Context:** Build 0028 crashes because the arcade function at 0x561A0 directly fills both
PC080SN C-windows (0xC00000 and 0xC08000) with 0x00000020 in a tight loop, AND calls a
scroll hardware write function that writes to 0xC20000/0xC40000. On Genesis, all of these
addresses are in VDP space — the writes corrupt VRAM and crash the emulator. The entire
harmful section (JSR to scroll HW + fill loop) must be redirected as ONE patch to a single
Genesis-side hook that implements the correct translated behavior: clear staged scroll
variables, fill both staged tilemap buffers, and mark all rows dirty. This is the same
pattern used by Rainbow Islands Genesis: all PC080SN writes go through WRAM staging, never
directly to hardware.

**Design reference:** `docs/design/Andy_cwindow_clear_hook_spec.md`

---

## PRECONDITION — Verify starting state

Before changing ANY file, confirm ALL of the following:

1. `opcode_replace_count` in `specs/rastan_direct_remap.json` is **44**.
2. `genesistan_hook_tilemap_fg` already exists in `apps/rastan-direct/src/main_68k.s`.
3. `fg_row_dirty` already exists in `apps/rastan-direct/src/main_68k.s`.
4. Read the 36 bytes at Genesis ROM offset `0x563B0` in the Build 0028 binary
   (`dist/rastan-direct/rastan_direct_video_test_build_0028.bin`). They must be exactly:
   ```
   4E B9 00 05 5C B4 32 3C 10 00 20 3C 00 00 00 20
   20 7C 00 C0 80 00 22 7C 00 C0 00 00 20 C0 22 C0
   53 41 66 F8
   ```
   This is the post-relocation JSR (6 bytes) followed by the fill loop (30 bytes).

If ANY of these fail: STOP. Report the mismatch. DO NOT MODIFY FILES.

---

## Task 1 — Add `.global` export

**File:** `apps/rastan-direct/src/main_68k.s`

At the top of the file (lines 2–13), add immediately after the existing
`genesistan_hook_tilemap_fg` line:

```asm
    .global genesistan_hook_cwindow_clear
```

---

## Task 2 — Implement `genesistan_hook_cwindow_clear`

**File:** `apps/rastan-direct/src/main_68k.s`

Place this function immediately after `genesistan_hook_tilemap_bg_fill` (after its
`.Lbg_fill_done` label and final `rts`). This groups all hook functions together.

### What this function does

This hook replaces TWO arcade operations in one call:

**Operation 1 — Scroll hardware write (arcade JSR to 0x55AB4):**
The arcade function at 0x55AB4 writes the just-cleared scroll field values from A5-relative
WRAM to PC080SN scroll registers (0xC20000, 0xC40000, 0xC20002, 0xC40002). The A5-relative
fields were already cleared to 0 by the instructions at 0x561A0–0x561AC (which are preserved
and NOT patched). The Genesis equivalent: zero the four staged scroll variables so that
`vdp_commit_scroll` writes zeros to VDP at the next VBlank.

**Operation 2 — C-window fill (arcade fill loop at 0x561B6–0x561D2):**
The arcade fills both PC080SN C-windows with the longword 0x00000020 (attribute 0x0000, tile
index 0x0020). The Genesis equivalent: translate arcade tile 0x0020 / attr 0x0000 through
the existing LUTs, fill both `staged_bg_buffer` and `staged_fg_buffer` with the resulting
Genesis nametable word, and mark all 32 rows dirty in both layers.

### Complete function behavior (all 6 steps, in order)

1. Clear `staged_scroll_x_bg` to 0
2. Clear `staged_scroll_y_bg` to 0
3. Clear `staged_scroll_x_fg` to 0
4. Clear `staged_scroll_y_fg` to 0
5. Translate arcade PC080SN entry 0x00000020 through the existing LUTs to get one Genesis
   nametable word, then fill all 2048 words of `staged_bg_buffer` with that word, then fill
   all 2048 words of `staged_fg_buffer` with that word
6. Set `bg_row_dirty` to 0xFFFFFFFF (all 32 rows dirty) and `fg_row_dirty` to 0xFFFFFFFF

### Scroll clears

```asm
    clr.w   staged_scroll_x_bg
    clr.w   staged_scroll_y_bg
    clr.w   staged_scroll_x_fg
    clr.w   staged_scroll_y_fg
```

### Tile translation

The tile index is 0x0020. Look it up in `genesistan_pc080sn_tile_vram_lut`:

```asm
    lea     genesistan_pc080sn_tile_vram_lut, %a2
    move.w  #0x0020, %d0        | arcade tile index
    add.w   %d0, %d0            | word offset into LUT
    move.w  0(%a2,%d0.w), %d3   | d3 = Genesis VRAM tile slot
```

The attribute is 0x0000. Extract palette (bits 0–1) = 0, priority (bit 13) = 0,
hflip (bit 14) = 0, vflip (bit 15) = 0. The attr index is 0. Look it up:

```asm
    lea     genesistan_pc080sn_attr_lut, %a3
    moveq   #0, %d0             | attr index = 0
    add.w   %d0, %d0            | word offset into LUT
    move.w  0(%a3,%d0.w), %d0   | d0 = Genesis nametable attr bits
    or.w    %d0, %d3            | d3 = complete Genesis nametable word
```

### Attribute extraction (for reference)

Use the SAME bit extraction logic as `genesistan_hook_tilemap_bg_fill` lines 571–598.
The attribute source is the HIGH WORD of 0x00000020 = 0x0000. Since all bits are zero,
the extraction will produce attr index 0. You may hardcode `moveq #0, %d0` for the attr
index since the fill value is constant 0x00000020 and the high word is always 0x0000.

### Register convention

Save and restore all registers used. Use the pattern:
```asm
genesistan_hook_cwindow_clear:
    movem.l %d0-%d3/%a0-%a3, -(%sp)
    | ... body ...
    movem.l (%sp)+, %d0-%d3/%a0-%a3
    rts
```

### Fill loops

Fill `staged_bg_buffer` (2048 words):
```asm
    lea     staged_bg_buffer, %a0
    move.w  #(2048 - 1), %d0
.Lcw_clear_bg:
    move.w  %d3, (%a0)+
    dbra    %d0, .Lcw_clear_bg
```

Fill `staged_fg_buffer` (2048 words):
```asm
    lea     staged_fg_buffer, %a0
    move.w  #(2048 - 1), %d0
.Lcw_clear_fg:
    move.w  %d3, (%a0)+
    dbra    %d0, .Lcw_clear_fg
```

### Mark all rows dirty

```asm
    move.l  #0xFFFFFFFF, bg_row_dirty
    move.l  #0xFFFFFFFF, fg_row_dirty
```

---

## Task 3 — Add remap.json patch: redirect JSR + fill loop to hook

**File:** `specs/rastan_direct_remap.json`

This is ONE patch entry that covers BOTH the JSR to scroll HW write (6 bytes) AND the fill
loop (30 bytes) = 36 bytes total. The entire 36-byte range is replaced by a single JSR to
the hook + structural padding to fill the remaining bytes.

**IMPORTANT — relocation:** The JSR at 0x561B0 targets 0x55AB4 in the arcade ROM, but the
relocation engine patched it to 0x55CB4 in the Genesis ROM. The `original_bytes` below use
the POST-RELOCATION bytes as they appear in the actual Genesis ROM. You verified this in
the PRECONDITION step.

Add this entry to `opcode_replace`:

```json
{
  "arcade_pc": "0x0561B0",
  "original_bytes": "4EB900055CB4323C1000203C000000207C00C08000227C00C0000020C022C0534166F8",
  "replacement_bytes": "4EB9{symbol:genesistan_hook_cwindow_clear}4E714E714E714E714E714E714E714E714E714E714E714E714E714E714E71",
  "note": "Replace PC080SN scene reset (scroll HW write + C-window fill) with JSR to Genesis-side hook. Hook clears staged scroll vars, fills staged_bg/fg_buffer with translated blank tile, marks all rows dirty."
}
```

Byte count: `original_bytes` = 36 bytes. `replacement_bytes` = 6 (JSR) + 30 (15 × padding) = 36 bytes. ✓

---

## Task 4 — Add to required_symbols

**File:** `specs/rastan_direct_remap.json`

Add `"genesistan_hook_cwindow_clear"` to the `required_symbols` array.

---

## Task 5 — Update opcode_replace_count

**File:** `specs/rastan_direct_remap.json`

Change `opcode_replace_count` from 44 to **45**.

---

## Task 6 — Build

Run the standard build pipeline:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct
```

The output file must be named:
```
dist/rastan-direct/rastan_direct_video_test_build_0029.bin
```

If the build number does not auto-increment, update the build number manually.
The build MUST pass with zero errors and zero warnings.

---

## Task 7 — Verify ROM bytes

Read the built ROM and confirm these exact bytes:

### Combined patch at Genesis offset 0x563B0

Read 36 bytes at offset `0x563B0`:

| Byte range  | Expected value |
|-------------|----------------|
| Bytes 0–1   | `4E B9` (JSR abs.l opcode) |
| Bytes 2–5   | Resolved address of `genesistan_hook_cwindow_clear` from `out/symbol.txt` |
| Bytes 6–35  | All `4E 71` (15 × structural padding after the JSR) |

### Symbol table

From `out/symbol.txt`, report the exact addresses of ALL of these:
- `genesistan_hook_cwindow_clear`
- `staged_bg_buffer`
- `staged_fg_buffer`
- `bg_row_dirty`
- `fg_row_dirty`
- `staged_scroll_x_bg`
- `staged_scroll_y_bg`
- `staged_scroll_x_fg`
- `staged_scroll_y_fg`

---

## Task 8 — Run MAME trace

Run a 30-second MAME trace:

```bash
timeout 120s tools/mame/run_genesis_trace_wsl.sh \
  apps/rastan-direct/dist/rastan_direct_video_test.bin \
  -video none -sound none -nothrottle -seconds_to_run 30
```

Save the trace to:
```
states/traces/rastan_direct_video_test_build_0029_mame_30s_<timestamp>/
```

From the summary, report:
- `frames=` count
- `reg_c50000_live count=`
- `title_init_block@000200 count=`
- Whether the trace completed without early termination

---

## What NOT to change

- Do NOT modify any existing hook functions (`genesistan_hook_tilemap_plane_a`,
  `genesistan_hook_tilemap_fg`, `genesistan_hook_tilemap_bg_fill`).
- Do NOT modify the VINT handler.
- Do NOT modify `init_staging_state`.
- Do NOT modify scroll patches or scroll commit logic.
- Do NOT modify any existing `opcode_replace` entries — only ADD the one new entry.
- Do NOT change `opcode_replace_count` to anything other than 45.

---

## Output file

```
docs/design/Cody_build_0029_cwindow_clear_hook_report.md
```

---

## AGENTS_LOG entry

```
[Cody - Implementation, build 0029 C-window clear hook]

* preconditions verified: YES/NO
* genesistan_hook_cwindow_clear implemented: YES/NO
* hook clears staged scroll vars: YES/NO
* hook fills staged_bg_buffer via LUT translation: YES/NO
* hook fills staged_fg_buffer via LUT translation: YES/NO
* hook sets bg_row_dirty and fg_row_dirty to 0xFFFFFFFF: YES/NO
* .global export added: YES/NO
* combined JSR+fill redirect patch applied (0x561B0, 36 bytes): YES/NO
* required_symbols updated: YES/NO
* opcode_replace_count = 45: YES/NO
* build successful: YES/NO
* ROM bytes verified at 0x563B0 (36 bytes): YES/NO
* symbol addresses reported: YES/NO
* MAME trace completed: YES/NO
* no unrelated changes made: YES/NO
```
