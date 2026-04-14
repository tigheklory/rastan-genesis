# Cody — Build 0029 Scroll Rewrite + C-Window Clear Hook

**Scope:** `apps/rastan-direct/src/main_68k.s` and `specs/rastan_direct_remap.json`

**Context:** Build 0028 crashes because the arcade function at 0x561A0 calls a scroll hardware
write function (0x55AB4) that writes to 0xC20000/0xC40000, then runs a fill loop that writes
to 0xC00000/0xC08000. All of these are VDP address space on Genesis — they corrupt VRAM and
crash the emulator.

This build applies TWO separate patches with separate concerns:
- **Patch A** rewrites the scroll function at 0x55AB4 to write to staged scroll variables
  instead of PC080SN hardware. This fixes scroll for ALL callers (init AND gameplay).
- **Patch B** redirects the fill loop at 0x561B6 to a Genesis-side hook that fills both
  staged tilemap buffers with the translated blank tile and marks all rows dirty.

The JSR at 0x561B0 that calls 0x55AB4 is LEFT UNTOUCHED — it calls the now-correctly-patched
function. These patches are in the same build because they are in the same execution path and
both must be present to prevent crashes.

**Design reference:** `docs/design/Andy_cwindow_clear_hook_spec.md`,
`docs/design/Andy_build_0028_fg_hook_failure_analysis.md`

---

## HARD RULES (FAIL CONDITIONS)

- NO behavioral NOPs. The ONLY allowed NOPs are structural padding after a JSR to fill the
  remaining bytes of a replaced instruction sequence.
- NO behavioral RTS. The only RTS allowed is the original function's own return instruction
  preserved in-place (0x55AB4 patch preserves its original RTS).
- DO NOT combine scroll logic into the tilemap hook. Scroll is handled by Patch A. The hook
  in Patch B handles ONLY tilemap fill.
- DO NOT modify any existing hook functions, VINT handler, or init_staging_state.
- DO NOT modify any existing opcode_replace entries.
- DO NOT touch A5 behavior, FG hook, or BG hook in this build.

If any rule is violated: STOP, report the violation, DO NOT continue.

---

## PRECONDITIONS (verify ALL before changing ANY file)

1. `opcode_replace_count` in `specs/rastan_direct_remap.json` is **44**.

2. `genesistan_hook_tilemap_fg` already exists in `apps/rastan-direct/src/main_68k.s`.

3. `fg_row_dirty` already exists in `apps/rastan-direct/src/main_68k.s`.

4. Read 34 bytes at Genesis ROM offset `0x55CB4` in
   `dist/rastan-direct/rastan_direct_video_test_build_0028.bin`. They must be exactly:
   ```
   33 ED 10 EE 00 C2 00 00 33 ED 10 EC 00 C4 00 00
   33 ED 10 B0 00 C2 00 02 33 ED 10 AE 00 C4 00 02
   4E 75
   ```
   This is the scroll write function (4 × MOVE.W to hardware + RTS).

5. Read 30 bytes at Genesis ROM offset `0x563B6`. They must be exactly:
   ```
   32 3C 10 00 20 3C 00 00 00 20 20 7C 00 C0 80 00
   22 7C 00 C0 00 00 20 C0 22 C0 53 41 66 F8
   ```
   This is the C-window fill loop.

6. Disassemble the function at arcade PC 0x55AB4 (Genesis 0x55CB4) and confirm it contains
   ONLY four MOVE.W instructions writing A5-relative fields to hardware addresses, then RTS.
   It must NOT modify any A5-relative state, set any flags, or branch anywhere. If it does
   anything beyond writing to 0xC20000/0xC40000/0xC20002/0xC40002 and returning: STOP and
   report the full disassembly.

If ANY precondition fails: STOP. Report the exact mismatch. DO NOT MODIFY FILES.

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

This hook handles ONLY the tilemap fill — NOT scroll. Scroll is handled separately by Task 3.

The hook MUST NOT:
- Read or write any `staged_scroll_*` variables
- Reference any scroll-related A5 offsets (0x10AE, 0x10B0, 0x10EC, 0x10EE)
- Contain any logic derived from the 0x55AB4 scroll write function

If any scroll logic is present in this hook: STOP and report the violation.

The arcade fill loop at 0x561B6 fills both PC080SN C-windows with the longword 0x00000020.
Each C-window entry is 4 bytes (2 words):
- High word = attribute: 0x0000 (palette 0, no flip, no priority)
- Low word = tile index: 0x0020

The Genesis hook must:
1. Translate this arcade entry through the existing LUTs to get one Genesis nametable word
2. Fill all 2048 words of `staged_bg_buffer` with that word
3. Fill all 2048 words of `staged_fg_buffer` with that word
4. Set `bg_row_dirty` to 0xFFFFFFFF (all 32 rows dirty)
5. Set `fg_row_dirty` to 0xFFFFFFFF (all 32 rows dirty)
6. Return via RTS

### REQUIRED BEHAVIOR (strict order)

```
Step 1: Translate tile 0x0020 via tile_vram_lut
Step 2: Translate attr 0x0000 via attr_lut
Step 3: Combine into single Genesis nametable word
Step 4: Fill staged_bg_buffer (2048 words)
Step 5: Fill staged_fg_buffer (2048 words)
Step 6: Set bg_row_dirty = 0xFFFFFFFF
Step 7: Set fg_row_dirty = 0xFFFFFFFF
```

Deviation from this order is a failure.

### Tile translation

The tile index is 0x0020. Look it up in `genesistan_pc080sn_tile_vram_lut`:

```asm
    lea     genesistan_pc080sn_tile_vram_lut, %a2
    move.w  #0x0020, %d0        | arcade tile index
    add.w   %d0, %d0            | word offset into LUT
    move.w  0(%a2,%d0.w), %d3   | d3 = Genesis VRAM tile slot
```

The attribute is 0x0000. Since all bits are zero, the attr extraction produces index 0.
You may hardcode this since the fill value is constant:

```asm
    lea     genesistan_pc080sn_attr_lut, %a3
    moveq   #0, %d0             | attr index = 0 (palette 0, no flips)
    add.w   %d0, %d0            | word offset into LUT
    move.w  0(%a3,%d0.w), %d0   | d0 = Genesis nametable attr bits
    or.w    %d0, %d3            | d3 = complete Genesis nametable word
```

### Register convention

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

## Task 3 — Add remap.json Patch A: scroll function rewrite (0x55AB4)

**File:** `specs/rastan_direct_remap.json`

This patch rewrites the four hardware destination addresses in the scroll write function to
point to the Genesis staged scroll variables instead. Same opcodes, same A5-relative source
fields, same RTS — only the destination addresses change. No hook, no JSR redirect.

Add this entry to `opcode_replace`:

```json
{
  "arcade_pc": "0x055AB4",
  "original_bytes": "33ED10EE00C2000033ED10EC00C4000033ED10B000C2000233ED10AE00C400024E75",
  "replacement_bytes": "33ED10EE{symbol:staged_scroll_y_bg}33ED10EC{symbol:staged_scroll_x_bg}33ED10B0{symbol:staged_scroll_y_fg}33ED10AE{symbol:staged_scroll_x_fg}4E75",
  "note": "Rewrite PC080SN scroll register write function: redirect all four MOVE.W destinations from hardware (0xC20000/0xC40000/0xC20002/0xC40002) to Genesis staged scroll variables. Same opcodes, same A5-relative sources, same RTS. Fixes scroll for ALL callers including gameplay."
}
```

Byte count: original = 34 bytes, replacement = 34 bytes. ✓

The RTS (4E75) at the end is the original function's own return instruction, preserved in
place. It is NOT a behavioral suppression.

---

## Task 4 — Add remap.json Patch B: C-window fill loop redirect (0x561B6)

**File:** `specs/rastan_direct_remap.json`

Replace the 30-byte fill loop with a JSR to the new hook + structural padding.

Add this entry to `opcode_replace`:

```json
{
  "arcade_pc": "0x0561B6",
  "original_bytes": "323C1000203C000000207C00C08000227C00C0000020C022C0534166F8",
  "replacement_bytes": "4EB9{symbol:genesistan_hook_cwindow_clear}4E714E714E714E714E714E714E714E714E714E714E714E71",
  "note": "Replace PC080SN C-window fill loop with JSR to Genesis-side staged buffer clear hook. Hook fills staged_bg_buffer and staged_fg_buffer with LUT-translated blank tile and marks all rows dirty."
}
```

Byte count: original = 30 bytes, replacement = 6 (JSR) + 24 (12 × structural padding) = 30 bytes. ✓

---

## Task 5 — Update required_symbols

**File:** `specs/rastan_direct_remap.json`

Add these three entries to the `required_symbols` array:

```json
"genesistan_hook_cwindow_clear",
"staged_scroll_y_fg",
"staged_scroll_x_fg"
```

(`staged_scroll_x_bg` and `staged_scroll_y_bg` are already present.)

---

## Task 6 — Update opcode_replace_count

**File:** `specs/rastan_direct_remap.json`

Change `opcode_replace_count` from 44 to **46**.

---

## Task 7 — Build

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

## Task 8 — Verify ROM bytes

### Scroll patch at Genesis offset 0x55CB4

Read 34 bytes at offset `0x55CB4`:

| Byte range | Expected value |
|------------|----------------|
| Bytes 0–1  | `33 ED` (MOVE.W d16(A5) opcode) |
| Bytes 2–3  | `10 EE` (A5 displacement — same as original) |
| Bytes 4–7  | Resolved address of `staged_scroll_y_bg` from `out/symbol.txt` |
| Bytes 8–11 | `33 ED 10 EC` (same opcode + displacement) |
| Bytes 12–15 | Resolved address of `staged_scroll_x_bg` |
| Bytes 16–19 | `33 ED 10 B0` |
| Bytes 20–23 | Resolved address of `staged_scroll_y_fg` |
| Bytes 24–27 | `33 ED 10 AE` |
| Bytes 28–31 | Resolved address of `staged_scroll_x_fg` |
| Bytes 32–33 | `4E 75` (RTS — preserved from original) |

### C-window hook redirect at Genesis offset 0x563B6

Read 30 bytes at offset `0x563B6`:

| Byte range | Expected value |
|------------|----------------|
| Bytes 0–1  | `4E B9` (JSR abs.l opcode) |
| Bytes 2–5  | Resolved address of `genesistan_hook_cwindow_clear` from `out/symbol.txt` |
| Bytes 6–29 | All `4E 71` (12 × structural padding) |

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

**WRAM validation:** Confirm that ALL `staged_*` and `*_dirty` symbols above resolve to
addresses in Genesis WRAM (0xFF0000–0xFFFFFF range). If ANY symbol resolves outside WRAM:
STOP and report — the BSS layout is misconfigured.

### opcode_replace_count

Report the final value. Must be **46**.

---

## Task 9 — Run MAME trace

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
- Whether the trace completed the full 30 seconds without early termination

---

## What NOT to change

- Do NOT modify `genesistan_hook_tilemap_plane_a` or `genesistan_hook_tilemap_fg` or
  `genesistan_hook_tilemap_bg_fill`.
- Do NOT modify `_VINT_handler`.
- Do NOT modify `init_staging_state`.
- Do NOT modify `vdp_commit_scroll` or `vdp_commit_bg_strips_if_dirty` or
  `vdp_commit_fg_strips_if_dirty`.
- Do NOT modify any existing `opcode_replace` entries — only ADD the two new entries.
- Do NOT change `opcode_replace_count` to anything other than 46.
- Do NOT add scroll logic to the C-window clear hook. Scroll is handled by the 0x55AB4 patch.

---

## Output file

```
docs/design/Cody_build_0029_scroll_rewrite_and_cwindow_hook_report.md
```

---

## AGENTS_LOG entry

```
[Cody - Implementation, build 0029 scroll rewrite + cwindow hook]

* preconditions verified (all 6): YES/NO
* scroll function disassembly confirmed HW-only: YES/NO
* genesistan_hook_cwindow_clear implemented: YES/NO
* hook performs LUT translation of tile 0x0020: YES/NO
* hook fills staged_bg_buffer (2048 words): YES/NO
* hook fills staged_fg_buffer (2048 words): YES/NO
* hook sets bg_row_dirty and fg_row_dirty to 0xFFFFFFFF: YES/NO
* hook does NOT contain scroll logic: YES/NO
* .global export added: YES/NO
* Patch A applied (scroll rewrite at 0x055AB4, 34 bytes): YES/NO
* Patch B applied (fill redirect at 0x0561B6, 30 bytes): YES/NO
* required_symbols updated (3 new entries): YES/NO
* opcode_replace_count = 46: YES/NO
* build successful: YES/NO
* ROM bytes verified at 0x55CB4 (34 bytes): YES/NO
* ROM bytes verified at 0x563B6 (30 bytes): YES/NO
* all 9 symbol addresses reported: YES/NO
* MAME trace completed: YES/NO
* no behavioral NOPs used: YES/NO
* no unrelated changes made: YES/NO
```
