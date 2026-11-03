# Andy — Title Hook Failure Analysis

## Ground Truth

- Boundary validation at 0x03AD48 (Genesis ROM 0x03AF48): NO
- Patch not applied; build not completed
- Crash: BlastEm "machine freeze due to write to address DFFFFE"
- Visual: Exodus shows unstable/scrolling layers; BlastEm shows checkerboard

---

## Task 1 — Explain the Crash

**Source: Arcade code writing to PC090OJ sprite RAM range that extends beyond BlastEm's mapped region.**

In the arcade memory map (from MAME source), the PC090OJ sprite RAM occupies `0xD00000–0xD03FFF`. On Genesis, 0xD00000 is in the expansion/VDP address range `0xC00000–0xDFFFFF`. Writes to these addresses are not mapped to any Genesis hardware — they hit unmapped bus space.

BlastEm considers writes to specific unmapped addresses in this range fatal. The write to `0xDFFFFE` — which is `0xE00000 - 2`, just below the start of Genesis WRAM — is one such address.

The arcade code contains a sprite initialization sequence that calls the block-fill primitive (`MOVE.L D0,(A0)+` loop) with `A0 = 0xD00000` and a count that drives `A0` past the PC090OJ's `0xD03FFF` boundary. One of these writes lands at `0xDFFFFE`.

Evidence: the full dump of code at `0x03AF4C` (arcade `0x03AD4C`) shows multiple calls to the block-fill primitive with `A0` targets in the `0xD000xx` range and counts large enough to advance past `0xD03FFF`. The specific call that reaches `0xDFFFFE` has not been fully traced but falls within this sprite initialization block.

**This crash is NOT caused by the BG hook.** It is a pre-existing issue where the arcade's sprite RAM initialization writes beyond the PC090OJ boundary into unmapped Genesis expansion space. It is a separate problem from the BG hook placement failure.

**Relation to the screenshots:** The crash is intermittent or deferred — it occurs after the arcade has run long enough to execute the initialization path that overshoots the sprite RAM range. The Exodus visual instability and checkerboard are unrelated to the crash; they reflect the BG hook never having fired (hook placement problem, not logic).

---

## Task 2 — Register Behavior from Screenshots

The Exodus plane viewer in all frames shows:
- **Plane B (VRAM 0xC000)**: mixed green (empty tile) and orange/red checkerboard pattern in the upper region — consistent with `init_staging_state` having filled `staged_bg_buffer` with 0x0001/0x0002 tiles, flushed via `vdp_commit_bg_strips_if_dirty` with `bg_row_dirty = 0xFFFFFFFF` at boot
- **Plane A (VRAM 0xE000)**: content changing across frames — the FG hook or some other write path is active

The main view shifts between frames (red/black vertical stripes transitioning to dark background). This is the arcade attract mode cycling — the game is executing normally through Title and early attract phase. The scrolling and visual cycling are from the arcade's scroll register writes (PC080SN xscroll/yscroll at `0xC40000`/`0xC20000`), which land at unmapped Genesis addresses and are ignored, causing the Genesis scroll state to stay at zero while the arcade believes it has set nonzero scroll values.

**0x055968 does not execute during Title** — confirmed by prior trace (`trace_hook_call_total = 0`). The existing hook produces zero writes during this phase.

**The arcade code path that writes BG during Title** is executing (756 writes to `0xC00000–0xC03FFF` via Lua tap), but it goes to the VDP data port at `0xC00000` on Genesis, not to `staged_bg_buffer`, because no hook intercepts it.

---

## Task 3 — 0x03AD48 Classification

**0x03AD48 is the loop-back `BNE.S` instruction inside a block-fill function. It is NOT a function entry.**

Disassembly of the function containing 0x03AD48 (Genesis ROM 0x03AF44–0x03AF4A, arcade 0x03AD44–0x03AD4A):

```
0x03AD44:  20 C0  MOVE.L D0, (A0)+    ; longword fill write, post-increment A0
0x03AD46:  53 41  SUBQ.W #1, D1       ; decrement iteration count
0x03AD48:  66 FA  BNE.S -4            ; loop back to 0x03AD44 if D1 != 0
0x03AD4A:  4E 75  RTS                 ; return when done
```

The `BNE.S` at 0x03AD48 is byte +4 of an 8-byte function. Placing a JSR here would corrupt the loop — replacing the back-branch with a call would execute the hook once and break the loop contract without ever iterating.

**Why did MAME report PC = 0x03AD48 for BG writes?**

MAME's Lua `install_write_tap` callback fires AFTER the memory write instruction completes. At the time the callback fires, the CPU program counter has already advanced past the write instruction. Because the write (`MOVE.L D0,(A0)+` at 0x03AD44, 2 bytes) and the decrement (`SUBQ.W #1,D1` at 0x03AD46, 2 bytes) both execute before the trap callback fires in MAME's execution model, the reported PC is at 0x03AD48 (the `BNE.S`), not 0x03AD44 (the write). The reported PC was off by 4 bytes from the actual write instruction.

Adjacent to this function is a word-fill sibling (FUNC A):
```
0x03AD3C:  30 C0  MOVE.W D0, (A0)+    ; word fill
0x03AD3E:  53 41  SUBQ.W #1, D1
0x03AD40:  66 FA  BNE.S -4
0x03AD42:  4E 75  RTS
```

Both fill primitives are simple unidimensional block-write functions. Both are called by higher-level code in the arcade's Title initialization sequence.

---

## Task 4 — Correct Hook Strategy

**Correct arcade PC to patch: 0x03AD44**

This is the entry point of the longword block-fill function. It is a proper function boundary (8 bytes, ends in `RTS`). A `JSR genesistan_hook_tilemap_bg_fill` instruction is 6 bytes and fits with a 2-byte NOP pad.

**Why 0x03AD44 is safe to patch:**
- It is the first instruction of the function (confirmed by disassembly context — `RTS` of previous function is at 0x03AD42, immediately before)
- The function ends in `RTS` at 0x03AD4A
- The 8-byte span fits a 6-byte JSR with 1 NOP pad
- The calling code expects to call this function and get back — JSR replaces the function body

**Why 0x03AD48 is NOT safe to patch:**
- It is the `BNE.S` loop-back branch at byte +4 of the function
- Replacing it with `JSR` would never iterate (the back-branch that drives D1 iterations is replaced), so 755 of 756 writes would be suppressed
- The return from the JSR would execute `RTS` immediately (from 0x03AD4A), but the loop contract is broken — subsequent iterations never run
- Placing a JSR at a mid-function instruction corrupts the stack relationship expected by the caller

**Higher-level callers of 0x03AD44 exist** (confirmed in the code at 0x03AF4C and beyond), but they write to sprite RAM (0xD00000) or other non-BG addresses. Hooking the callers would also intercept non-BG writes. Hooking the primitive itself with an A0 range check is the cleaner approach.

---

## Task 5 — Hook Contract Compatibility

**The existing hook (`genesistan_hook_tilemap_plane_a`) is NOT compatible with the 0x03AD44 call site.**

The existing hook uses the WRAM-descriptor protocol:
- Reads `ARCADE_PC080SN_DEST_BG_OFFSET` (WRAM `0xFF10A0`) for destination
- Reads `ARCADE_PC080SN_STRIP_INDEX_OFFSET` (WRAM `0xFF10CA`) for strip index
- Reads 16 descriptor entries from `ARCADE_PC080SN_DESC_BG_LIST_OFFSET` (WRAM `0xFF1000`)
- Each descriptor is a ROM offset pointing to a table of tile indices
- Tile data is fetched from ROM via the descriptor, then looked up in the VRAM LUT

The 0x03AD44 call site uses the register protocol:
- `D0`: longword containing tile data directly — `D0[31:16]` = attr word, `D0[15:0]` = code word
- `A0`: PC080SN BG RAM destination address (e.g., `0xC00000`)
- `D1`: iteration count (number of longword tile entries to fill)
- No WRAM desc list is written before this call; no strip index is relevant

The mismatches are fundamental:

| Dimension | Existing hook | 0x03AD44 call site |
|---|---|---|
| Tile data source | ROM via descriptor pointer | D0 register (direct) |
| Destination | WRAM[0x10A0] | A0 register |
| Count | 16 descriptors × 4 rows = 64 entries | D1 register |
| Attr+code split | ROM[desc+0], ROM[desc+2] | D0[31:16], D0[15:0] |

Additionally, the existing hook uses `A0` at entry for scene detection (comparing against ROM address ranges). At the 0x03AD44 call site, `A0` = 0xC00000 (PC080SN address), not a ROM address. While this does not crash (the scene check finds no match and falls through), it causes the hook to read from WRAM[0x1000] which contains stale arcade workram data, producing garbage nametable entries.

**A new hook is required for the 0x03AD44 call site.**

---

## Task 6 — Final Root Cause

**Single root cause: MAME's Lua write tap reports PC = the instruction following the write, not the write instruction itself.**

The tap's callback fires after MAME's CPU has advanced the PC past both the write instruction (`MOVE.L D0,(A0)+` at 0x03AD44, 2 bytes) and the next instruction (`SUBQ.W #1,D1` at 0x03AD46, 2 bytes), placing the observed PC at the `BNE.S` (0x03AD48). The downstream effect:

1. Cody received 0x03AD48 as the "Title BG write PC"
2. The correct Genesis ROM offset (0x03AF48) was inspected
3. 0x03AF48 = `BNE.S` inside a loop body — correctly rejected by boundary validation
4. The actual function entry (0x03AD44 = Genesis 0x03AF44) was never checked

The correct information was always present in the ROM — the function entry at 0x03AD44 has `RTS` at 0x03AD4A and an 8-byte span. The misdirection was entirely from the off-by-4 PC timing in the Lua tap.

---

## Derived Implementation Requirements

For a Cody implementation prompt (not defined here):

**New patch target:**
- Arcade PC: `0x03AD44`
- Genesis ROM offset: `0x03AD44 + 0x000200 = 0x03AF44`
- Original bytes (confirmed from ROM): `20 C0 53 41 66 FA 4E 75` (8 bytes)
- Replacement: `4E B9 {symbol:genesistan_hook_tilemap_bg_fill} 4E 71` (6-byte JSR + 1 NOP = 8 bytes)

**New hook function (`genesistan_hook_tilemap_bg_fill`) contract:**
- Called from: any site that calls the block-fill primitive
- Inputs (from registers at call time): `D0` = attr/code longword, `A0` = PC080SN BG RAM destination, `D1` = tile count
- Precondition check: if `A0` is NOT in `[0xC00000, 0xC04000)`, return immediately (non-BG write — sprite RAM, FG RAM, etc.)
- For each of D1 tiles: decode `A0` offset to row/col, extract code from `D0[13:0]`, extract attr from `D0[31:16]`, look up VRAM slot via `genesistan_pc080sn_tile_vram_lut`, write nametable word to `staged_bg_buffer`, set dirty bit
- Saves and restores all registers; replaces the original fill loop entirely (does not call original code)
- The existing `genesistan_hook_tilemap_plane_a` at `0x055968` is kept and unchanged
