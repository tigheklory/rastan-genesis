# Andy — BG Fill Hook Post-RTS No-Change Diagnosis

## Ground Truth

- RTS fix confirmed: `specs/rastan_direct_remap.json` entry for `0x03AD44` now reads `"replacement_bytes": "4eb9{symbol:genesistan_hook_tilemap_bg_fill}4e75"`
- Build passes, no crash, 59.9 fps in BlastEm
- Plane B still shows checkerboard / no Title BG content visible
- Question: why does the RTS fix produce no visible change?

---

## Task 1 — RTS Contract Correct?

**YES — the RTS contract is now correct.**

After the fix:
```
+0: 4E B9   JSR.L
+2: 00 07
+4: 02 D2   → genesistan_hook_tilemap_bg_fill
+6: 4E 75   RTS              ← correct; returns to caller of FUNC B
```

The hook's own `RTS` returns to `0x03AF4A`; the `RTS` at `0x03AF4A` pops `CALLER_RET` and returns to whoever called FUNC B. Stack discipline is now intact. This is not the problem.

---

## Task 2 — Hook Logic Should Produce Plane B Updates If Called With Valid BG Data?

**YES — if FUNC B were called with BG-window A0 and non-zero tile data, the hook would correctly stage it.**

The hook logic (reviewed in Prompt 232):
- Range check: A0 & 0xFFFFFF in [0xC00000, 0xC04000) ✓
- Nametable_word precompute: code from D0[15:0] via `genesistan_pc080sn_tile_vram_lut`; attr from D0[31:16] via `genesistan_pc080sn_attr_lut` ✓
- Fill loop: row/col from A0 byte offset → `staged_bg_buffer[row*128 + col*2]` = nametable_word; `bset row, bg_row_dirty` ✓
- `vdp_commit_bg_strips_if_dirty` each VBlank flushes dirty rows to Plane B VRAM ✓

Hook logic is correct. VBlank flush path is correct. If the hook were called with Title BG content, Plane B would update.

---

## Task 3 — Most Likely Remaining Failure Point

**The Title scene's BG tilemap data is written by a SEPARATE block copy function — NOT by FUNC B — which the hook does not intercept.**

### The two paths

**FUNC B** (`0x03AD44`, Genesis ROM `0x03AF44`):
- Register contract: D0=fill_word (constant), A0=dest, D1=count
- Writes the SAME D0 value to every destination longword (uniform fill)
- Hooked since Prompt 231

**Block copy function** (`0x05A4DC`, called via `BSR.W $0154`):
- Called from `0x05A388`: `LEA 0x5A7DA, A0; MOVE.W #28, D0; MOVE.W #21, D1; MOVE.W #1, D3; BSR.W $0154; RTS`
- Reads per-cell tile codes from a ROM source table and writes them one-by-one to PC080SN BG RAM at [0xC00000, 0xC04000)
- This is the function that writes title_alt (28×21 cells, tile codes 0xAD + 0x21Bx) and title_logo (28×20 cells)
- **NOT FUNC B; NOT hooked**

### What FUNC B is actually called with during Title

Complete inventory of FUNC B callers that pass the BG window range check (A0 in [0xC00000, 0xC04000)):

| Caller PC | A0 | D0 (tile) | D1 (count) | Purpose |
|-----------|-----|-----------|------------|---------|
| `0x03AE70` | `0xC00100` | `0x0020` (tile 32) | 1900 | BG clear: rows 1+ |
| `0x03AF38` | `0xC00000` | `0x0020` (tile 32) | 4096 | BG clear: ALL rows |

Both callers use tile code 32 (0x20) = the blank/clear tile. `pc080sn.bin[0x400:0x420]` = all `0x00` bytes = all palette index 0 = all-black pixels. The hook correctly stages `nametable_word = lut[32] = 0x0014` (slot 20, all-black tile) for all 4096 cells.

**Result:** After `genesistan_hook_tilemap_bg_fill` runs, `staged_bg_buffer` is filled with `0x0014` in every cell. Plane B flushes as all-black. The Title BG content (stone + logo tiles) is never written to `staged_bg_buffer`.

### What the block copy function does on Genesis

The block copy function at `0x05A4DC` writes raw tile code words to PC080SN BG RAM addresses [0xC00000, 0xC04000). On the Genesis, `0xC00000` = VDP data port. These writes go directly to VRAM at the VDP's current auto-increment address — wherever the VDP register happens to be positioned. They do NOT reach `staged_bg_buffer`. They write arcade tile code words (0x00AD, 0x21B6, etc.) as raw 16-bit values into VRAM at unpredictable offsets, producing visual garbage or being overwritten by the next VBlank flush.

---

## Task 4 — Screenshot Reconciliation

**Why Plane B still shows checkerboard / no Title content:**

Frame 1: `init_staging_state` fills `staged_bg_buffer` with checkerboard (tiles 0x0001/0x0002). VBlank flushes → Plane B = checkerboard. ✓

Frame 2+: The BG clear (FUNC B at 0x03AF38) fires. Hook stages 4096×`0x0014`. Next VBlank flushes → Plane B = all-black tile (all-zero pixels = invisible over black backdrop). Not visible as distinct output.

Title block copy fires (0x05A4DC): writes tile codes 0x00AD, 0x21B6, etc. as raw words to VDP data port → VRAM bytes at unpredictable offset. These writes may partially overwrite tile graphics already in VRAM (corrupting them), or land in non-plane VRAM (sprites, etc.). Plane B nametable is never updated with title content.

**Why no crash:**
The block copy function writes to [0xC00000, 0xC04000) — valid VDP data port writes. No unmapped memory access. No 0xDFFFFE hit. ✓ (The 0xDFFFFE crash is a pre-existing separate issue from PC090OJ sprite init.)

**Why fps stays at 59.9:**
All writes land in VDP or valid Genesis space. No bus errors. Arcade main loop is `BRA`-based (not `RTS` at outer level). Stack corruption from prior NOP bug is gone. ✓

---

## Task 5 — Classification

**Classification: C — hook called and implemented correctly, but a different write path (block copy, not FUNC B) is responsible for Title BG content.**

- The hook IS being called (BG clear callers hit the range check and stage 0x0014)
- The hook logic IS correct (precompute + fill loop + dirty bit all verified)
- The RTS fix IS in place (no stack corruption)
- FUNC B is simply not the function that writes the Title BG tilemap

---

## Task 6 — Single Root Cause

**Root cause: the Title scene's BG tilemap is written by block copy function `0x05A4DC` (called via `BSR.W $0154` from `0x05A388`), which reads per-cell tile codes from ROM and writes them directly to [0xC00000, 0xC04000). On Genesis this hits the VDP data port directly. The function is not FUNC B and is not intercepted by `genesistan_hook_tilemap_bg_fill`.**

`genesistan_hook_tilemap_bg_fill` was designed to intercept FUNC B — the uniform fill primitive. The Title BG does not use the uniform fill primitive for content. It uses a separate per-cell block copy function. Those writes bypass `staged_bg_buffer` entirely, going straight to the VDP data port as raw arcade tile code words.

---

## Task 7 — Single Next Step

**Intercept the block copy function at `0x05A4DC`.**

The function is called from `0x05A388` via `BSR.W $0154`. Its write loop iterates over source table entries and stores per-cell tile codes to sequential [0xC00000, 0xC04000) addresses. To hook it:

1. **Characterize the function contract at `0x05A4DC`**: determine the register convention (D0=rows, D1=cols, D3=?, A0=source) as seen from the caller at `0x05A388`. Disassemble `0x05A4DC` from `build/regions/maincpu.bin` to confirm entry signature, loop structure, and what it reads from A0 per iteration.

2. **Design a new `opcode_replace` entry**: patch the function entry at `0x05A4DC` to `JSR genesistan_hook_tilemap_bg_blockcopy` (a new hook symbol). The hook must iterate over the same source cells and for each (source_addr, dest_addr) pair: read the tile code, look it up in `genesistan_pc080sn_tile_vram_lut`, and write the resulting nametable word into `staged_bg_buffer` at the correct row/col offset.

3. **Write the Cody prompt** (as `docs/design/Cody_bg_blockcopy_hook_implementation.md`) after the function contract is confirmed.

The same MAME Lua write-tap approach used previously can validate the `0x05A4DC` call path: install a write tap on [0xC00000, 0xC04000) during Title init and confirm the PC points into the `0x05A4DC` function.
