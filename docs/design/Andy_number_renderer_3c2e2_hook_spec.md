# Andy — Number Renderer Hook Spec: `genesistan_hook_number_renderer_3c2e2`

**Status:** SPEC COMPLETE. Ready for Cody. Zero design decisions remaining.
**Build Context:** Build 0035, `rastan-direct`.

---

## 1. Function Confirmation

- **Entry:** `arcade_pc: 0x03C2E2` (`build/maincpu.disasm.txt:75750`).
- **`genesis_rom_offset`:** `0x03C4E2` (address_map.json `arcade_copy` segment `[0x03B0A4, 0x03EF28) → [0x03B2A4, 0x03F128)`, `identity_offset = 512`).
- **Binary verified:** first 20 bytes at `genesis_rom_offset: 0x03C4E2` match first 20 bytes at `arcade_pc: 0x03C2E2` (`3E3C0000C0FC000A41FA0090D0C0301022680002`). Unpatched.
- **Patch span:** `arcade_pc: 0x03C2E2..0x03C37B` inclusive = **0x9A bytes (154)**. `arcade_pc: 0x03C37C` is the first byte of the ROM data table — **excluded** from the patch span.
- **`genesis_rom_offset` span:** `0x03C4E2..0x03C57B`. No overlap with any existing `patched_site` (verified by scan of all `patched_site` segments in `address_map.json`).
- **6 live callers** (all `bsrw 0x3C2E2`): `arcade_pc: 0x03A546, 0x03A96E, 0x03B0AC, 0x03B426, 0x03B42C, 0x03B714`. 1 dead: `0x03AC60` (inside existing `patched_site`).
- **Single `opcode_replace` at `arcade_pc: 0x03C2E2` is sufficient** — all live callers reach this single entry point.

---

## 2. ROM Table Analysis

### 2.1 Table structure

Table base: `arcade_pc: 0x03C37C`. Entry size: 10 bytes. Loaded via
`lea %pc@(0x3C37C), %a0; adda.w D0, %a0` at `arcade_pc: 0x03C2EA–0x03C2EE`
where `D0 = input_index × 10` (`muluw #10` at `0x03C2E6`).

Per-entry layout:
- `+0` (word): digit count (or `0xFFFF` for "ALL" sentinel)
- `+2` (longword): A1 destination — FG tilemap hardware address
- `+6` (longword): A2 source — arcade workram pointer (BCD data location)

### 2.2 Full table dump (13 valid entries)

| Idx | `arcade_pc` | Count | A1 (`HW_ADDRESS`) | A2 (arcade workram) | Row | Col |
|----:|-------------|------:|-------------------:|---------------------:|----:|----:|
| 0 | `0x03C37C` | 6 | `0x00C09334` | `0x0010C145` | 19 | 13 |
| 1 | `0x03C386` | 6 | `0x00C09534` | `0x0010C148` | 21 | 13 |
| 2 | `0x03C390` | 6 | `0x00C09734` | `0x0010C14B` | 23 | 13 |
| 3 | `0x03C39A` | 2 | `0x00C09EA0` | `0x0010C013` | 30 | 40 |
| 4 | `0x03C3A4` | 6 | `0x00C09934` | `0x0010C14E` | 25 | 13 |
| 5 | `0x03C3AE` | 6 | `0x00C09B34` | `0x0010C151` | 27 | 13 |
| 6 | `0x03C3B8` | 0xFFFF | `0x00C09368` | `0x0010C152` | 19 | 26 |
| 7 | `0x03C3C2` | 0xFFFF | `0x00C09568` | `0x0010C153` | 21 | 26 |
| 8 | `0x03C3CC` | 0xFFFF | `0x00C09768` | `0x0010C154` | 23 | 26 |
| 9 | `0x03C3D6` | 0xFFFF | `0x00C09968` | `0x0010C155` | 25 | 26 |
| 10 | `0x03C3E0` | 0xFFFF | `0x00C09B68` | `0x0010C156` | 27 | 26 |
| 11 | `0x03C3EA` | 6 | `0x00C08D24` | `0x0010C11E` | 13 | 9 |
| 12 | `0x03C3F4` | 0xFFFF | `0x00C08D5C` | `0x0010C118` | 13 | 23 |

Row/col derivation: `cell_index = (A1 − 0xC08000) / 4`; `col = cell_index & 0x3F`; `row = (cell_index >> 6) & 0x3F`. All within `HW_ADDRESS/PC080SN/FG_TILEMAP` space — no cross-space arithmetic. Verified for each entry.

**All 13 A1 destinations are `HW_ADDRESS/PC080SN/FG_TILEMAP` (`[0xC08000, 0xC0C000)`).** No non-FG entries found. **STOP not triggered.**

Entry index 13+ (`arcade_pc: 0x03C3FE`+) contains code/data for another function — confirmed by the pattern break (count=0x3E3C, A1=0x00003400 — not a valid FG address). Table ends at entry 12.

### 2.3 Entry 3 confirmation

Entry 3 (offset `0x1E` from table base = `arcade_pc: 0x03C39A`):
- Count = 2, A1 = **`0x00C09EA0`** ✓ — matches trace `first_addr`.
- A2 = `0x0010C013` — arcade workram location for 2-digit value (credits counter).
- Row = 30, Col = 40 — matches the Build 35 trace.

### 2.4 A2 data-pointer translation (MANDATORY for hook)

All A2 values are in `0x0010C0xx–0x0010C1xx` — these are **arcade workram
absolute addresses**. On the original arcade hardware, RAM was at
`0x10C000+`. On Genesis, arcade workram was relocated to `0xFF0000+` via
`genesistan_arcade_workram_words` (confirmed by `workram_anchor_offset = 0x10C000`
in `tools/translation/postpatch_startup_rom.py:1138`).

The hook MUST translate each A2 value from the arcade absolute address to
the Genesis WRAM location. The formula uses only **data-pointer relocation**
(not code-address cross-space arithmetic):

```
arcade_wram_base = 0x10C000   (the arcade workram base address, constant)
genesis_wram_base = A5         (register A5 = 0xFF0000 at runtime)
genesis_a2 = genesis_wram_base + (table_a2_value − arcade_wram_base)
```

Equivalently: `genesis_a2 = A5 + (table_a2_value & 0xFFFF)` — because all
A2 values have high word `0x0010` and the offset from `0x10C000` fits in
16 bits (e.g. `0x0010C145 − 0x10C000 = 0x0145`; `A5 + 0x0145 = 0xFF0145`).

The hook loads A2 from the ROM table, strips the arcade base, and adds the
genesis WRAM base. This is a one-time relocation per call, not per-digit.

---

## 3. Write Contract

### 3.1 Digit loop (`arcade_pc: 0x03C302..0x03C32C`)

**Per-digit iteration:**

For each digit (D0 counts down from `table.count`):

1. Test `D0 bit 0`:
   - **Low nibble** (`D0 bit 0 = 1`): `D1 = A2@ & 0x0F`; then `A2 -= 1`.
   - **High nibble** (`D0 bit 0 = 0`): `D1 = (A2@) >> 4 & 0x0F`; A2 unchanged.
2. Tile code: `D1 = D1 | 0x30` → arcade tile index `0x30..0x3F`.
3. Write attr: `movew D7, A1@+` → attribute word (D7 = 0). A1 advances by 2.
4. Write tile: `movew D1, A1@+` → tile code word. A1 advances by 2.
5. Decrement D0; loop if nonzero.

**A1 advance per digit:** +4 bytes (2 words × 2 bytes each).
**A2 advance:** −1 byte on odd-digit iterations (low nibble); 0 on even-digit. Net: A2 scans backward through BCD packed bytes, extracting digit nibbles right-to-left.
**Cells per digit:** 2 (one attr cell + one tile cell in the 4-byte Taito cell record).
**Total cells for count=6:** 6 digits × 2 cells = 12 cells; A1 advance = 24 bytes.

### 3.2 Leading-zero suppression (`arcade_pc: 0x03C32E..0x03C350`)

**Entry condition:** only executes if original digit count `A0@ == 6` (`cmpi.w #6, A0@` at `0x03C32E`). Otherwise, function RTSes immediately.

**Logic:**
1. Reload: `D0 = A0@` (count=6), `A1 = A0@(2)` (reset A1 to start of this entry's destination).
2. Scan loop: read `A1@(2)` (the tile word of each digit cell).
   - If tile == `0x30` (digit '0'): overwrite with `0x20` (space tile): `movew #0x20, A1@(2)` at `arcade_pc: 0x03C344`.
   - If tile != `0x30`: stop (the first non-zero digit breaks the scan).
3. Advance: `addql #4, A1` per scanned digit (regardless of overwrite).
4. Decrement D0; loop if nonzero.

**Write instruction:** `movew #0x20, A1@(2)` at `arcade_pc: 0x03C344`. Indexed write (NOT post-increment). Offset +2 from A1 = the tile-code cell slot.
**A1 advance:** +4 bytes per scanned digit.
**Cells modified:** 0 to 5 (only leading-zero cells are overwritten; the first non-zero digit stops the scan). Each overwrite targets the **same cells already written by the digit loop** — the hook must update the same `staged_fg_buffer` positions.
**Dirty bits:** the same row(s) already marked dirty by the digit loop. No additional `fg_row_dirty` bits needed unless a new row is touched (which is not possible since suppression scans the same cells).

### 3.3 "ALL" handler (`arcade_pc: 0x03C352..0x03C37A`)

**Entry condition:** `D0 == 0xFFFF` (tested at `arcade_pc: 0x03C2FA`; `beqw 0x3C352`).

**Logic:**
1. Read `D1 = A2@ & 0x0F` (low nibble of byte at A2).
2. If `D1 == 7`: write "ALL" string — back up A1 by 8 bytes, then write 3 character pairs:
   - `movew D7, A1@+` (attr) + `movew #0x41, A1@+` (tile 'A')
   - `movew D7, A1@+` (attr) + `movew #0x4C, A1@+` (tile 'L')
   - `movew D7, A1@+` (attr) + `movew #0x4C, A1@` (tile 'L', **no post-increment**)
   - Then RTS.
3. If `D1 != 7`: set `D0 = 1` and re-enter digit loop at `0x03C302` → renders 1 digit.

**"ALL" write sequence (D1==7):**
A1 is backed up by 8 bytes (`suba.l #8, A1`), then 6 words are written:
- A1@+: attr (D7=0) → +2
- A1@+: tile 0x41 ('A') → +2
- A1@+: attr → +2
- A1@+: tile 0x4C ('L') → +2
- A1@+: attr → +2
- A1@: tile 0x4C ('L') — NO post-inc
Net A1 advance from pre-backup position: −8 + 10 = +2 bytes. But A1's final absolute value matters more than the delta — the hook must compute (row, col) from the backup-adjusted A1.

**"ALL" single-digit path (D1!=7):** re-enters digit loop with D0=1 → renders one digit, then falls through to leading-zero suppression check. The suppression check (`cmpi.w #6, A0@`) will likely fail (original count was 0xFFFF, not 6), so suppression is skipped.

### 3.4 Complete write inventory

| # | `arcade_pc` | Instruction | Form | What is written | Path |
|---|-------------|-------------|------|-----------------|------|
| 1 | `0x03C312` | `movew %d7, %a1@+` | post-inc | attr word (D7=0) | digit loop, low-nibble |
| 2 | `0x03C314` | `movew %d1, %a1@+` | post-inc | tile code (0x30+nibble) | digit loop, low-nibble |
| 3 | `0x03C326` | `movew %d7, %a1@+` | post-inc | attr word (D7=0) | digit loop, high-nibble |
| 4 | `0x03C328` | `movew %d1, %a1@+` | post-inc | tile code (0x30+nibble) | digit loop, high-nibble |
| 5 | `0x03C344` | `movew #0x20, %a1@(2)` | indexed | tile code 0x20 (space) | leading-zero suppression |
| 6 | `0x03C364` | `movew %d7, %a1@+` | post-inc | attr word | "ALL" handler |
| 7 | `0x03C366` | `movew #0x41, %a1@+` | post-inc | tile 'A' (0x41) | "ALL" handler |
| 8 | `0x03C36A` | `movew %d7, %a1@+` | post-inc | attr word | "ALL" handler |
| 9 | `0x03C36C` | `movew #0x4C, %a1@+` | post-inc | tile 'L' (0x4C) | "ALL" handler |
| 10 | `0x03C370` | `movew %d7, %a1@+` | post-inc | attr word | "ALL" handler |
| 11 | `0x03C372` | `movew #0x4C, %a1@` | indexed (no inc) | tile 'L' (0x4C) | "ALL" handler |

---

## 4. Input/Output Contract

### 4.1 Input registers

| Reg | Role | Source |
|-----|------|--------|
| D0 | Display-entry index (0-based, 0..12). Sole meaningful input. | Caller. |
| A5 | Arcade workram base (`0xFF0000` on Genesis). Used for A2 translation. | Runtime constant. |
| D7 | **NOT an input.** Cleared to 0 at function entry (`movew #0, D7` at `0x03C2E2`). | Internal. |
| A0, A1, A2 | Loaded from ROM table inside the function. Not inputs. | Internal. |
| All others | Don't-care. Function does not read them. | — |

### 4.2 Output contract

For each cell written (digit, leading-zero space, or "ALL" character):

1. Compute the cell's `(row, col)` from the current A1 value (which starts at
   the table entry's A1 destination and advances per §3.1/§3.2/§3.3).
2. **Tile translation:** the arcade tile code (`0x30+nibble`, `0x20`, `0x41`, `0x4C`)
   MUST be translated through `genesistan_pc080sn_tile_vram_lut`. These are
   arcade PC080SN tile indices — the same tile index space used by all other
   FG tilemap writers. The Genesis tile VRAM layout differs from arcade; LUT
   translation is mandatory. Proof: the existing hooks (`genesistan_hook_tilemap_fg`,
   `genesistan_hook_text_writer_3c4d2`, etc.) all pass arcade tile codes through
   the same LUT at `apps/rastan-direct/src/main_68k.s:276` / `663`.
3. **Attribute translation:** D7 = 0 (the attribute word for all digits in this
   function). Pass through `genesistan_pc080sn_attr_lut[0]` for the Genesis
   palette/priority/flip word. This produces the default Genesis attribute for
   palette line 0. Proof: D7 is set to 0 at function entry (`movew #0, D7`
   at `arcade_pc: 0x03C2E2`); it is never modified before any write.
4. **Compose:** `nametable_word = gen_tile | gen_attr`.
5. Write to `staged_fg_buffer[row * 64 + col]`.
6. `bset row, fg_row_dirty`.

### 4.3 `fg_row_dirty` strategy

Set per-write. Each table entry's digits all land within a single row
(verified: each entry writes consecutive cells starting at a fixed
(row, col), advancing only the column — no row wrap for counts ≤ 6).
So in practice, one `bset` per call suffices. But for correctness in the
"ALL" handler (which backs up A1 by 8 bytes = 2 cells = may cross a row
boundary in edge cases), the hook MUST set the dirty bit for every row
any cell lands on. Per-write `bset` is the safe approach.

### 4.4 A1/A0 final values on hook exit

- **A1:** the original function modifies A1 via `A1@+` writes. On exit,
  A1 = `table_A1_dest + (digit_count × 4)` (digit loop) or adjusted per
  the "ALL" / suppression paths. The callers do NOT inspect A1 after return
  (verified: all 6 live callers are `bsrw 0x3C2E2` sites that discard A1
  post-call — the callers' own A1 is either saved/restored or unused).
  The hook need not preserve A1 to a specific value — but MUST NOT clobber
  any callee-save register. Since A1 is caller-save on 68000, no
  preservation needed.
- **A0:** the function sets A0 internally (from `lea` + `adda.w`). A0 on
  exit = `table_base + D0_input × 10` (the table entry pointer). Callers
  do not depend on A0 post-call (verified by inspection of all 6 call
  sites — none reads A0 after the `bsr`).
- **A2, D0, D1, D7:** all clobbered internally. No preservation needed.
- **Safe approach:** the hook saves D0 (input index) at entry, loads the
  table entry, translates A2 for WRAM, processes all digits, sets dirty
  bits, then RTSes. No callee-save registers need restoration beyond what
  the standard `movem.l` prologue/epilogue handles.

---

## 5. Patch Entry Specification

### 5.1 `opcode_replace` entry

```jsonc
{
  "arcade_pc": "0x03C2E2",
  "original_bytes": "<154 bytes from build/regions/maincpu.bin[0x03C2E2 : 0x03C37C]>",
  "replacement_bytes": "4EB9{symbol:genesistan_hook_number_renderer_3c2e2}4E75<148 bytes of 4E71 NOP padding>",
  "note": "Route number/score renderer at arcade_pc 0x03C2E2 through Genesis FG staging hook; intercepts all digit/leading-zero/ALL writes that previously hit PC080SN FG tilemap directly."
}
```

Replacement: 6 (JSR) + 2 (RTS) + 146 (73 NOPs) = 154 bytes. Wait — 154 - 8 = 146, 146/2 = 73. But actually let me recompute: 0x9A = 154 bytes. 154 - 6 (JSR) - 2 (RTS) = 146 bytes of NOP. 146/2 = 73 NOPs. Correct.

### 5.2 Count update

- `opcode_replace_count`: **55 → 56**.
- `required_symbols` adds: `genesistan_hook_number_renderer_3c2e2`.
- Patcher invariant in `tools/translation/postpatch_startup_rom.py`: bump from
  55 to 56, with `total_genesis_bytes_covered` updated to the new value
  reported by the patcher's actual measurement.

---

## 6. Implementation Readiness

**READY FOR CODY.** Zero design decisions remaining.

Cody work items:

1. Add hook function `genesistan_hook_number_renderer_3c2e2` to
   `apps/rastan-direct/src/main_68k.s`:
   - Read table entry from ROM at `arcade_pc: 0x03C37C` (the table
     remains in the Genesis ROM at `genesis_rom_offset: 0x03C57C`
     because it was excluded from the patch span).
   - Access the table via `lea` using the PC-relative form — the
     original instruction was `lea %pc@(0x3C37C), A0` at
     `arcade_pc: 0x03C2EA`. In the HOOK (which lives in the Genesis
     wrapper at `0x00070000+`), the table is NOT PC-reachable via a
     16-bit displacement. Cody MUST use **absolute addressing**:
     `lea genesistan_number_table_rom, A0` where
     `genesistan_number_table_rom` is a symbol pointing to the table's
     `genesis_rom_offset: 0x03C57C`. (Alternatively, load the absolute
     address directly: `movea.l #0x03C57C, A0`.)
   - Translate A2 from arcade workram absolute to Genesis WRAM:
     `genesis_a2 = A5 + (table_a2_value & 0xFFFF)`.
   - Translate A1 from `HW_ADDRESS/PC080SN/FG_TILEMAP` to `staged_fg_buffer`
     (row, col) per §2.3.
   - Process digits per §3.1, leading-zero suppression per §3.2, "ALL"
     handler per §3.3.
   - For each cell: tile code through `genesistan_pc080sn_tile_vram_lut`;
     attr 0 through `genesistan_pc080sn_attr_lut[0]`; compose; write to
     `staged_fg_buffer[row*64+col]`; `bset row, fg_row_dirty`.
2. Add `.global genesistan_hook_number_renderer_3c2e2` to `main_68k.s`.
3. Add `genesistan_hook_number_renderer_3c2e2` to `required_symbols` in
   `specs/rastan_direct_remap.json`.
4. Add the `opcode_replace` entry from §5.1. Cody fills in
   `original_bytes` from the binary at `arcade_pc: 0x03C2E2..0x03C37C`.
5. Bump `opcode_replace_count` 55 → 56.
6. Bump patcher invariant 55 → 56.
7. Build → 30 s MAME trace → verify `fg_cwindow_live count` drops to 0.
   Verify BlastEm does not crash at `0xC09EA0`.

---

## Open Questions

1. **Table access method.** The original function used `lea %pc@(0x3C37C), A0`
   — a PC-relative load. In the hook (which resides in the `0x70000+` wrapper
   region), this displacement is out of range. Cody must use an absolute
   `lea` or `movea.l #<genesis_rom_offset>, A0`. The simplest form is
   `movea.l #0x0003C57C, A0` (the genesis_rom_offset of the table, hardcoded).
   Alternatively, the hook can define a local `.equ` constant. This is an
   implementation detail with no design ambiguity — the table is at a known
   fixed ROM address.
2. **Whether additional FG writers exist beyond the dispatcher family and
   this number renderer.** After Build 36, the `fg_cwindow_live` trace
   watchpoint is the definitive check. If count drops to 0, all FG
   C-window-writing code paths are covered. If not, a new writer audit is
   needed against `docs/design/Cody_pc080sn_writer_audit.md`.

## Implementation Status — Build 0036

- Hook implemented: YES (`genesistan_hook_number_renderer_3c2e2` in `apps/rastan-direct/src/main_68k.s`)
- Spec matched source cleanly: YES
- Absolute table access used: YES (`movea.l #0x0003C57C, %a0`)
- A5 validity confirmed at hook entry: YES (`A5=0x00FF0000` in Build 35/36 FG-writer trace context)
- A1 converted to staged FG writes immediately: YES (all writes routed through staged-store helper path; no direct FG hardware writes)
- A2 translation implemented: YES (`A2 = A5 + (table_a2_value & 0xFFFF)`)
- All 11 write behaviors implemented: YES (digit loop low/high nibble forms, leading-zero suppression write, and all six `"ALL"` write instructions)
- Validation summary:
  - Build 0036 release: PASS
  - patch manifest / address map / postpatch disassembly: regenerated
  - 30s trace: PASS (`states/traces/rastan_direct_video_test_build_0036_mame_30s_20260416_121207`)
  - `fg_cwindow_live`: `count=0` (down from 8 in Build 35)
  - No `FG_WRITE` lines emitted in trace log
  - Crash signature at `HW_ADDRESS/PC080SN/FG_TILEMAP: 0xC09EA0`: no longer present in trace evidence
- Tracking ledger: see `docs/design/handler_translation_coverage.md` entry for `arcade_pc: 0x03C2E2` (status `VERIFIED`).
