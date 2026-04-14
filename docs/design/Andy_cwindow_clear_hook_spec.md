# Andy — PC080SN C-Window Clear Hook Specification

**Context:** Build 0028 crashes at 0xC09EA0 because arcade function at 0x561A0 directly fills
both PC080SN C-windows with constant 0x00000020. This function must be redirected to a Genesis-
side hook — same pattern as every other PC080SN write intercept.

**Precedent:** Rainbow Islands Genesis has no "fill C-window" function. All arcade PC080SN
writes — including clears and fills — are intercepted and routed to WRAM staging buffers.
The fill operation is just another hook. No special treatment needed.

---

## 1. The Arcade Function Being Replaced

Arcade PC 0x561A0 (Genesis PC 0x563A0):

```asm
561a0: clrw %a5@(0x10AE)           ; clear scroll field     ← KEEP (A5-relative WRAM)
561a4: clrw %a5@(0x10B0)           ; clear scroll field     ← KEEP
561a8: clrw %a5@(0x10EC)           ; clear scroll field     ← KEEP
561ac: clrw %a5@(0x10EE)           ; clear scroll field     ← KEEP
561b0: jsr 0x55ab4                 ; scroll HW write        ← SUPPRESS (writes 0xC20000/0xC40000)
561b6: movew #4096, %d1            ; ┐
561ba: movel #0x20, %d0            ; │
561c0: moveal #0xC08000, %a0       ; │ fill loop            ← REPLACE with JSR to hook
561c6: moveal #0xC00000, %a1       ; │
561cc: movel %d0, %a0@+            ; │
561ce: movel %d0, %a1@+            ; │
561d0: subqw #1, %d1               ; │
561d2: bnes 0x561cc                ; ┘
561d4: rts
```

The A5-relative clears at 0x561A0–0x561AC are harmless (write to WRAM). They must be preserved.

The JSR to 0x55AB4 at 0x561B0 writes to 0xC20000/0xC40000 (PC080SN scroll registers). These
are invalid on Genesis. Must be suppressed.

The fill loop at 0x561B6–0x561D2 writes 4096 longwords of 0x00000020 to both C-windows. This
is the crash source. Must be replaced with a JSR to the Genesis-side hook.

---

## 2. What the Fill Does (Arcade Semantics)

Each PC080SN C-window entry is 4 bytes (2 words):
- Word 0: attribute (palette, flip, priority)
- Word 1: tile index

Fill value 0x00000020 as a longword = attribute word 0x0000, tile index word 0x0020.

- Attribute 0x0000: palette 0, no flip, no priority
- Tile index 0x0020 = 32 decimal

Through the existing LUTs:
- `genesistan_pc080sn_tile_vram_lut[0x0020]` → the Genesis VRAM slot for arcade tile 32
- `genesistan_pc080sn_attr_lut[0]` → palette 0 / no flip / no priority → Genesis nametable bits

The hook must compute this translated value ONCE and fill both staged buffers with it.

However: if arcade tile 32 is not loaded in any scene (slot may be 0 or undefined), the
practical effect is the same as filling with 0x0000 (blank). The hook should still do the
correct translation in case tile 32 is meaningful in some scenes.

---

## 3. Genesis-Side Hook Design

### New symbol: `genesistan_hook_cwindow_clear`

**Contract:** Called via JSR from the replaced fill loop site. Fills both `staged_bg_buffer`
and `staged_fg_buffer` with the translated Genesis nametable value for arcade PC080SN entry
0x00000020. Marks all 32 rows dirty in both `bg_row_dirty` and `fg_row_dirty`. Returns via RTS.

**Register convention:** No inputs required. The fill value is constant (0x00000020). The
function saves and restores all registers it uses.

### Implementation structure

```asm
genesistan_hook_cwindow_clear:
    movem.l %d0-%d3/%a0-%a3, -(%sp)

    | --- Translate arcade fill value 0x00000020 once ---
    |
    | Tile index = 0x0020 (low word of 0x00000020)
    | Attribute  = 0x0000 (high word of 0x00000020)
    |
    | Look up tile: tile_vram_lut[0x0020]
    | Look up attr: attr_lut[0]  (palette 0, no flip bits)
    | OR them together → fill_word (single 16-bit Genesis nametable value)

    lea     genesistan_pc080sn_tile_vram_lut, %a2
    move.w  #0x0020, %d0
    add.w   %d0, %d0
    move.w  0(%a2,%d0.w), %d3          | d3 = translated tile

    lea     genesistan_pc080sn_attr_lut, %a3
    move.w  #0, %d0                     | attr index = 0 (palette 0, no flips)
    add.w   %d0, %d0
    move.w  0(%a3,%d0.w), %d0          | d0 = translated attr
    or.w    %d0, %d3                    | d3 = complete Genesis nametable word

    | --- Fill staged_bg_buffer (2048 words = 64 cols × 32 rows) ---

    lea     staged_bg_buffer, %a0
    move.w  #(2048 - 1), %d0
.Lcw_clear_bg:
    move.w  %d3, (%a0)+
    dbra    %d0, .Lcw_clear_bg

    | --- Fill staged_fg_buffer (2048 words) ---

    lea     staged_fg_buffer, %a0
    move.w  #(2048 - 1), %d0
.Lcw_clear_fg:
    move.w  %d3, (%a0)+
    dbra    %d0, .Lcw_clear_fg

    | --- Mark ALL 32 rows dirty in both layers ---

    move.l  #0xFFFFFFFF, bg_row_dirty
    move.l  #0xFFFFFFFF, fg_row_dirty

    movem.l (%sp)+, %d0-%d3/%a0-%a3
    rts
```

### Why this matches Rainbow Islands pattern

Rainbow Islands routes ALL PC080SN operations — strips, fills, clears — through WRAM staging.
The VBlank commit path handles the actual VDP writes. This hook does exactly that: stages the
fill result into WRAM buffers and lets `vdp_commit_bg_strips_if_dirty` / 
`vdp_commit_fg_strips_if_dirty` write them to VRAM at the next VBlank.

---

## 4. Patch Specification for remap.json

### Entry 1 — Suppress JSR to scroll HW write at 0x561B0

The JSR at 0x561B0 calls the scroll register write function at 0x55AB4, which writes directly
to 0xC20000 and 0xC40000. The A5-relative scroll field clears at 0x561A0–0x561AC already
zeroed the source data in WRAM. The VBlank `vdp_commit_scroll` path commits those values to
VDP. The JSR is arcade-hardware-only and must be suppressed.

```json
{
  "arcade_pc": "0x0561B0",
  "original_bytes": "4EB900055AB4",
  "replacement_bytes": "4E714E714E71",
  "note": "Suppress JSR to PC080SN scroll HW write function (0x55AB4). Writes to 0xC20000/0xC40000 invalid on Genesis. Scroll values committed via vdp_commit_scroll in VINT."
}
```

**IMPORTANT — relocation caveat:** The JSR target 0x55AB4 is within `maincpu_rom` range
(< 0x060000), so the relocation engine patches it to 0x55CB4 in the Genesis ROM. The
`original_bytes` above are the PRE-RELOCATION arcade bytes. If the patcher compares against
POST-RELOCATION bytes, use `4EB900055CB4` instead. Cody must verify which convention applies
by reading the actual bytes at Genesis offset 0x563B0 before applying the patch.

### Entry 2 — Replace fill loop with JSR to hook

Replace the 30-byte fill loop (0x561B6–0x561D3) with a 6-byte JSR to the new hook + 12 NOPs
to pad the remaining 24 bytes.

```json
{
  "arcade_pc": "0x0561B6",
  "original_bytes": "323C1000203C000000207C00C08000227C00C0000020C022C0534166F8",
  "replacement_bytes": "4EB9{symbol:genesistan_hook_cwindow_clear}4E714E714E714E714E714E714E714E714E714E714E714E71",
  "note": "Replace PC080SN C-window fill loop with JSR to Genesis-side staged buffer clear hook. Fills staged_bg_buffer and staged_fg_buffer with translated blank tile value and marks all rows dirty."
}
```

Byte count: 30 bytes original = 6 (JSR) + 24 (12 NOPs) = 30 bytes replacement. ✓

### Entry 3 — Add to required_symbols

Add `"genesistan_hook_cwindow_clear"` to the `required_symbols` array.

### Update opcode_replace_count

44 → 46 (two new entries).

---

## 5. Assembly Changes to main_68k.s

### Add `.global` export

At the top of the file (lines 2–13), add:
```asm
    .global genesistan_hook_cwindow_clear
```

### Add the hook function

Place `genesistan_hook_cwindow_clear` after `genesistan_hook_tilemap_bg_fill` (after its
`.Lbg_fill_done: ... rts` block). This groups all hook functions together.

### No BSS changes

No new BSS variables needed. Uses existing `staged_bg_buffer`, `staged_fg_buffer`,
`bg_row_dirty`, `fg_row_dirty`, and the existing LUTs.

---

## 6. Verification

After build, Cody must confirm:

| Genesis offset | Expected bytes 0–1 | Expected bytes 2–5 |
|----------------|--------------------|--------------------|
| 0x0563B0 (JSR NOP) | `4E71` | `4E71 4E71` (3 NOPs = 6 bytes) |
| 0x0563B6 (hook JSR) | `4EB9` | resolved addr of `genesistan_hook_cwindow_clear` |

Confirm from `out/symbol.txt`:
- `genesistan_hook_cwindow_clear` address
- `staged_bg_buffer` address
- `staged_fg_buffer` address
- `bg_row_dirty` address
- `fg_row_dirty` address

### Runtime verification

After Build 0029:
- BlastEm: no freeze at 0xC09EA0
- Exodus: no "VDP AdvanceProcessorState" errors from the fill path
- MAME trace: `reg_c50000_live count=0` still holds; game runs full 30s

---

## 7. What This Does NOT Fix

- **FG layer content still absent**: The FG strip producer at 0x55990 is never called because
  A5@(0x10A8) = 0xFF10A8 is permanently 0 on Genesis. This is a separate issue requiring
  either layer selector patching or dispatcher modification. Deferred.
- **Non-zero scroll writes during gameplay**: Only the CLR.W init paths are redirected. Future
  MOVE.W scroll writes will need separate handlers as the game progresses.
- **Other potential direct C-window writers**: There may be additional functions (beyond the
  strip producer and this fill function) that write directly to C-window addresses. These will
  surface as new crash sites once this one is resolved.
