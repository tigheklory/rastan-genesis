# Cody — FG Tilemap Hook + Scroll CLR.W Redirect

**Scope:** `apps/rastan-direct/src/main_68k.s` and `specs/rastan_direct_remap.json`

**Context:** Build 0027 crashes BlastEm with a write to 0xC09EA0 (FG tilemap area of PC080SN
address space — no hook exists, raw write hits Genesis VDP bus). The four CLR.W scroll NOP
patches from Build 0027 suppress arcade scroll writes but leave `staged_scroll_*` variables
never updated (scaffolding that must be replaced). Both must be fixed in this build.

Design reference: `docs/design/Andy_build_0027_runtime_diagnosis_scroll_plan.md`

---

## PRECONDITION — Find the FG strip producer arcade PC

**Do this before writing any code.** The BG hook is placed at arcade PC 0x055968, which is
the BG strip producer. There is a peer FG strip producer nearby that writes to the FG window
(0xC08000–0xC0BFFF). You must find it first.

1. Read `build/rom_inventory.json` to locate the raw arcade ROM file.
2. Disassemble 68000 instructions starting at 0x055968 (the BG producer). Identify the
   function boundaries. Look immediately adjacent (before or after) for the FG peer routine.
   The FG producer will write destination addresses in the 0xC08000–0xC0BFFF range and use
   a similar strip descriptor loop structure.
3. Confirm the FG producer's entry point arcade PC and read its first 20–40 bytes as
   `original_bytes`.
4. Record the confirmed FG producer arcade PC and `original_bytes` in your report before
   proceeding.

---

## Task A — Replace scroll NOP scaffolding with symbol-redirected CLR.W

**File:** `specs/rastan_direct_remap.json`

The four existing scroll NOP patches must be replaced in-place (no new entries, no count
change). Replace only the `replacement_bytes` field for each entry. The `original_bytes`
fields remain exactly as they are.

| Arcade PC  | Current `replacement_bytes` | New `replacement_bytes`                    |
|------------|-----------------------------|--------------------------------------------|
| `0x03ABBA` | `4E714E714E71`              | `42B9{symbol:staged_scroll_y_bg}`          |
| `0x03ABC0` | `4E714E714E71`              | `42B9{symbol:staged_scroll_x_bg}`          |
| `0x03B098` | `4E714E714E71`              | `42B9{symbol:staged_scroll_y_bg}`          |
| `0x03B09E` | `4E714E714E71`              | `42B9{symbol:staged_scroll_x_bg}`          |

`opcode_replace_count` stays at 43. These are in-place replacements, not additions.

---

## Task B — Implement FG tilemap hook

**Files:** `apps/rastan-direct/src/main_68k.s`, `specs/rastan_direct_remap.json`

### B1 — Add `.global` export (top of file, lines 2–13)

Add this line alongside the other `.global` declarations at the top of `main_68k.s`,
immediately after the existing `genesistan_hook_tilemap_plane_a` line:

```asm
    .global genesistan_hook_tilemap_fg
```

### B2 — Add `ARCADE_PC080SN_DEST_FG_OFFSET` constant

In the `.equ` block that already contains `ARCADE_PC080SN_DEST_BG_OFFSET`, add:

```asm
    .equ ARCADE_PC080SN_DEST_FG_OFFSET, 0x10A4
```

Place it immediately after the `ARCADE_PC080SN_DEST_BG_OFFSET` line.

### B3 — Add `fg_row_dirty` BSS declaration

In the data section at line 902, `bg_row_dirty` is declared as:

```asm
bg_row_dirty:
    .long 0
```

Place `fg_row_dirty` immediately after it:

```asm
bg_row_dirty:
    .long 0
    .align 2
fg_row_dirty:
    .long 0
```

### B4 — Implement `genesistan_hook_tilemap_fg`

Add `genesistan_hook_tilemap_fg` immediately after the closing `rts` of
`genesistan_hook_tilemap_bg_fill` (find its end, then insert after). This function is a
structural copy of `genesistan_hook_tilemap_plane_a` with these substitutions:

| Replace                               | With                                      |
|---------------------------------------|-------------------------------------------|
| `ARCADE_PC080SN_CWINDOW_BASE_BG`      | `0x00C08000` (FG window base)             |
| `ARCADE_PC080SN_DEST_BG_OFFSET(%a5)` | `ARCADE_PC080SN_DEST_FG_OFFSET(%a5)`     |
| `staged_bg_buffer`                    | `staged_fg_buffer`                        |
| `bg_row_dirty`                        | `fg_row_dirty`                            |
| All local label names (`.Lbg_hook_*`) | Rename to `.Lfg_hook_*` to avoid clashes |

The FG window base for the range check is `0x00C08000` and the window size is the same
`ARCADE_PC080SN_CWINDOW_BYTES` (0x4000). The FG destination pointer lives at
`ARCADE_PC080SN_DEST_FG_OFFSET(%a5)` (A5-relative 0x10A4 within arcade workram at
0xFF0000).

### B5 — Implement `vdp_commit_fg_strips_if_dirty`

Add `vdp_commit_fg_strips_if_dirty` immediately after `vdp_commit_bg_strips_if_dirty`
(which ends at its `.Lbg_done: rts`). This is a structural copy with substitutions:

| Replace                | With                   |
|------------------------|------------------------|
| `bg_row_dirty`         | `fg_row_dirty`         |
| `VRAM_PLANE_B_BASE`    | `VRAM_PLANE_A_BASE`    |
| `staged_bg_buffer`     | `staged_fg_buffer`     |
| All `.Lbg_row_*` labels | Rename to `.Lfg_row_*` |

### B6 — Wire `vdp_commit_fg_strips_if_dirty` into VINT handler

In `_VINT_handler` (line 75), find the existing call:

```asm
    bsr     vdp_commit_bg_strips_if_dirty
```

Add the FG commit call immediately after it:

```asm
    bsr     vdp_commit_bg_strips_if_dirty
    bsr     vdp_commit_fg_strips_if_dirty
```

### B7 — Initialize `fg_row_dirty` in `init_staging_state`

In `init_staging_state`, find the existing line (line ~701):

```asm
    clr.l   bg_row_dirty
```

Add the FG clear immediately after it:

```asm
    clr.l   bg_row_dirty
    clr.l   fg_row_dirty
```

### B8 — Add FG hook redirect patch to `remap.json`

Using the FG strip producer arcade PC you found in the PRECONDITION step, add a new entry
to `opcode_replace` in `specs/rastan_direct_remap.json`:

```json
{
  "arcade_pc": "<FG_PRODUCER_PC>",
  "original_bytes": "<first 40 bytes at FG producer PC>",
  "replacement_bytes": "4eb9{symbol:genesistan_hook_tilemap_fg}<padding 4E71s>",
  "note": "Route PC080SN FG strip producer through rastan-direct hook symbol."
}
```

The `replacement_bytes` must be exactly the same byte length as `original_bytes`. The
redirect is a 6-byte JSR absolute long (`4EB9` + 4-byte address). Pad the remainder with
`4E71` (NOP) pairs until the byte count matches. Follow the exact same pattern as the BG
hook entry at arcade PC `0x055968`.

Update `opcode_replace_count` from 43 to 44.

### B9 — Add `genesistan_hook_tilemap_fg` to `required_symbols`

In `specs/rastan_direct_remap.json`, find the `required_symbols` array and add:

```json
"genesistan_hook_tilemap_fg"
```

---

## Build and verify

Build the ROM with the standard pipeline. Then report:

### Scroll patches — exact bytes at Genesis offsets

For each of the four scroll patches, the Genesis offset is `arcade_pc + 0x200`. Read exactly
6 bytes at each offset and report the hex:

| Arcade PC  | Genesis offset | Expected bytes 0–1 | Expected bytes 2–5          |
|------------|----------------|--------------------|-----------------------------|
| `0x03ABBA` | `0x03ADBA`     | `42B9`             | address of `staged_scroll_y_bg` |
| `0x03ABC0` | `0x03ADC0`     | `42B9`             | address of `staged_scroll_x_bg` |
| `0x03B098` | `0x03B298`     | `42B9`             | address of `staged_scroll_y_bg` |
| `0x03B09E` | `0x03B29E`     | `42B9`             | address of `staged_scroll_x_bg` |

Confirm the resolved addresses for `staged_scroll_y_bg`, `staged_scroll_x_bg` from
`out/symbol.txt`. The bytes 2–5 in the ROM at each offset must match those addresses exactly.

### FG hook patch — exact bytes at Genesis offset

The FG producer's Genesis offset is `FG_PRODUCER_PC + 0x200`. Read exactly the same number
of bytes as `original_bytes` and report them. Bytes 0–1 must be `4E B9`. Bytes 2–5 must be
the resolved address of `genesistan_hook_tilemap_fg` from `out/symbol.txt`. Remaining bytes
must all be `4E 71`.

### Symbol table confirmation

From `out/symbol.txt`, report the exact addresses of:
- `staged_scroll_y_bg`
- `staged_scroll_x_bg`
- `staged_scroll_y_fg`
- `staged_scroll_x_fg`
- `genesistan_hook_tilemap_fg`
- `fg_row_dirty`
- `vdp_commit_fg_strips_if_dirty`

### `opcode_replace_count`

Report the final value. Must be 44.

---

## What NOT to change

- Do not modify any existing BG hook logic.
- Do not modify `init_staging_state` beyond adding `clr.l fg_row_dirty`.
- Do not add scroll MOVE.W handlers — only the four CLR.W redirect patches.
- Do not change `opcode_replace_count` to anything other than 44.
