1. Executive Summary
Implemented a new register-contract hook, `genesistan_hook_tilemap_bg_fill`, and patched arcade PC `0x03AD44` (Genesis ROM `0x03AF44`) to call it. This routes Title/attract PC080SN longword BG fill writes into `staged_bg_buffer` with `bg_row_dirty` updates, while preserving the existing gameplay hook at `0x055968` and leaving `genesistan_hook_tilemap_plane_a` unchanged.

2. Preconditions Verified
- `genesistan_hook_tilemap_plane_a` exists.
- `genesistan_pc080sn_tile_vram_lut` exists.
- `genesistan_pc080sn_attr_lut` exists.
- `staged_bg_buffer` exists.
- `bg_row_dirty` exists.
- Existing `0x055968` patch exists in spec.
- `opcode_replace_count` was `34` before this change.
- `required_symbols` did not contain `genesistan_hook_tilemap_bg_fill` before this change.
- ROM bytes at `0x03AF44` were exactly `20 C0 53 41 66 FA 4E 75` before this change.

3. New Global Symbol Added
Added:
- `.global genesistan_hook_tilemap_bg_fill`
Placed immediately after `.global genesistan_hook_tilemap_plane_a` in `apps/rastan-direct/src/main_68k.s`.

4. `genesistan_hook_tilemap_bg_fill` Contract
New function added in `.text` after `genesistan_hook_tilemap_plane_a` and before `vdp_commit_tiles_if_dirty`.
Call-time contract:
- `D0[31:16]`: attr word
- `D0[15:0]`: tile code word
- `A0`: PC080SN BG destination
- `D1`: fill count
Function behavior:
- Saves/restores registers with `movem.l %d0-%d7/%a0-%a6`.
- Replaces original fill primitive behavior for BG window writes by staging to Genesis-side BG buffer.
- Returns via `rts` without invoking original primitive.

5. A0 Range Check Implementation
At hook entry:
- Copies `A0` to a data register and masks to 24 bits.
- Validates address in `[0x00C00000, 0x00C04000)`.
- If out of range, exits immediately with full register restore.
This prevents non-BG users of the primitive (for example sprite RAM ranges) from being processed by this hook.

6. Nametable Word Precompute
Performed once before the fill loop:
- `code = D0[15:0] & 0x3FFF`
- `vram_slot = genesistan_pc080sn_tile_vram_lut[code * 2]`
- `attr_word = D0[31:16]` (via `swap`)
- Attribute LUT index assembled from:
  - palette bits 1:0
  - hflip from bit 14
  - vflip from bit 15
  - priority from bit 13
- `genesis_attr = genesistan_pc080sn_attr_lut[attr_index * 2]`
- `nametable_word = vram_slot | genesis_attr`
Shift extraction follows the existing two-shift style (`lsr.w #8` plus second shift), avoiding immediate shifts greater than 8.

7. Fill Loop Implementation
Loop uses call-time `D1` count (`D1=0` yields zero iterations):
- Computes `byte_offset = (A0_masked - 0x00C00000)`.
- Computes `longword_index = byte_offset >> 2`.
- Derives `col = longword_index & 0x003F` and `row = (longword_index >> 6) & 0x001F`.
- Computes staged buffer offset `row * 128 + col * 2`.
- Writes precomputed `nametable_word` into `staged_bg_buffer`.
- Sets dirty row bit in `bg_row_dirty`.
- Advances destination (`A0 += 4`) and decrements loop count.
- Stops early if destination reaches/exceeds `0x00C04000`.
No VDP direct writes are performed in this hook.

8. Patch Spec Updates
`specs/rastan_direct_remap.json` changes:
- Added `genesistan_hook_tilemap_bg_fill` to `required_symbols`.
- Added one new `opcode_replace` entry:
  - `arcade_pc`: `0x03AD44`
  - `original_bytes`: `20C0534166FA4E75`
  - `replacement_bytes`: `4eb9{symbol:genesistan_hook_tilemap_bg_fill}4e71`
  - note: Title/attract BG fill path description
- Existing `0x055968` gameplay patch preserved unchanged.
- Updated `opcode_replace_count` from `34` to `35`.

9. Build Verification
Build command:
- `source tools/setup_env.sh && make -C apps/rastan-direct`
Results:
- Assembler, linker, patcher, and boot guard all passed.
- No symbol resolution errors.
- No patch byte mismatch errors.
- ROM artifact produced.

10. Post-Build Patch Verification
Verified rebuilt ROM bytes at Genesis ROM offset `0x03AF44`:
- `4E B9 00 07 02 D2 4E 71`
This confirms the JSR+NOP patch is present at the intended site.

11. Final Result
Implemented the new `genesistan_hook_tilemap_bg_fill` and patched `0x03AD44` to call it via symbol-based JSR, preserving the existing gameplay BG hook at `0x055968` and leaving `genesistan_hook_tilemap_plane_a` unchanged.
