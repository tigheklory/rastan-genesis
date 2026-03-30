# Next Sprite System Slice: Size / Grouping

## 1. Purpose

Define the next forward implementation slice for sprite size/grouping interpretation in the
Rastan Genesis sprite system. The pipeline is proven live end-to-end (arcade tick →
`genesistan_sprite_tile_prepare()` → `genesistan_sprite_commit_asm()`), VRAM tile region
1024+ is nonzero and stable, SAT link chain is sequential and correctly terminated, and the
decode buffer and upload buffer are the same address. Visuals remain FAIL. The remaining
failure is in sprite system rules, not pipeline plumbing.

---

## 2. Chosen Next Sprite-System Slice

**Option A: Full word0 attr decode + canonical Block-A source unification.**

This is the one chosen slice. It covers two inseparable rules that together constitute the
"sprite interpretation" layer:

1. **Canonical Block-A source**: `genesistan_sprite_tile_prepare()` currently reads from
   byte offset `0x11B2` off the workram base. `genesistan_sprite_commit_asm` reads from the
   absolute address `0xE0FF11FE`. If `genesistan_arcade_workram_words` is at `0xE0FF0000`,
   these differ by `0x11FE - 0x11B2 = 0x4C` bytes = 9.5 entries. Even if this mismatch is
   currently masked (probe data shows matching at entry 0), the architecture is inconsistent:
   the prepare step must read from the same base address as the commit step so lut[N]
   corresponds to the same descriptor as what the commit loop processes for entry N.

2. **word0 attribute field decode**: The current commit path ignores word0 entirely. It
   builds SAT tile_attr as `(tile_index & 0x07FF) | 0x8000` — priority bit set, palette=0,
   flipy=0, flipx=0. The real arcade word0 carries:
   - bit 15: flipy (vertical flip)
   - bit 14: flipx (horizontal flip)
   - bits 3-0: color bank index (combined with global sprite_colbank to select palette line)

   Without decoding these bits, every sprite is rendered with the wrong flip state and wrong
   palette for entries where word0 is nonzero. For the title logo, word0=0x0000 (no flip,
   bank 0), so these bits happen to be zero — but for any gameplay sprite with nonzero word0,
   the tile_attr is wrong and the sprite is garbled or uses incorrect CRAM entries.

Both rules must move together because: (a) they both involve reading word0 from the same
Block-A entry, and (b) fixing (1) without (2) produces a correctly-aligned but still
attribute-wrong system; fixing (2) without (1) produces correctly-attributed but positionally
misaligned tile decode.

**Size assumption stays fixed at 2×2 (16×16 pixels) per entry.** The research confirms that
the PC090OJ cell is the atomic 16×16 sprite unit, there is no per-entry size field in word0
or word2, and each Block-A entry corresponds to exactly one 16×16 hardware sprite. A
"composed object" like the title logo is assembled from multiple independently positioned
16×16 entries — not from a single larger SAT entry. The 2×2 assumption is architecturally
correct and does not need to change in this slice.

---

## 3. Why This Is the Next Highest-Value Step

The current visuals are wrong because:

**Primary active cause — word0 not decoded in commit path.** The assembly commit builds
SAT tile_attr with hardcoded palette=0 and flip=0. For any sprite with nonzero word0, the
tile renders with wrong palette colors and possibly wrong orientation. Even when the tile
pixel data is correct in VRAM, the wrong palette line produces incorrect or invisible colors.
This applies to all Block-A entries system-wide.

**Secondary architectural cause — prepare/commit Block-A source mismatch.** `lut[N]` is
built from the tile code found at `0x11B2 + N*8`, but the commit uses it alongside the
position/attr from `0x11FE + N*8`. If these two addresses do not contain the same live
Block-A data (which is architecturally not guaranteed), then for each SAT entry N, the tile
from a different descriptor is shown at the position of another descriptor. This would
scramble the tile-to-position mapping and prevent recognizable composed output.

Fixing word0 decode adds correct flip and palette to SAT tile_attr for all entries.
Unifying the Block-A source ensures the tile decode and SAT position/attr use the same
live data per entry. Together these produce correctly-attributed, correctly-positioned
sprite cells. The title logo's cells (word0=0x0000, no flip, bank 0) are the simplest test
case; gameplay sprites exercise the full decode path.

---

## 4. Sprite Model Rule to Implement

### 4.1 word0 field definitions

```
word0 (attr/flags), 16-bit:
  bit 15     = flipy  (vertical flip; 1 = flipped)
  bit 14     = flipx  (horizontal flip; 1 = flipped)
  bits 13-4  = unused / reserved (not decoded in this slice)
  bits 3-0   = color bank index (raw nibble)
```

Color bank to palette line mapping:
```
sprite_colbank = (genesistan_arcade_workram_words[10] & 0x00E0) >> 1
color = (word0 & 0x000F) | sprite_colbank
palette_line = color >> 4   (upper nibble = palette line index 0-3)
```

For the title logo, word0=0x0000: flipy=0, flipx=0, color bank=0, palette_line=0 (PAL0).
This matches the current hardcoded behavior — so the title logo is unaffected by this fix.
Gameplay sprites that have nonzero word0 will gain correct flip and palette after this fix.

### 4.2 Valid sprite sizes in the current Block-A stream

All entries: one PC090OJ cell = 16×16 pixels = 4 Genesis 8×8 tiles (2 wide × 2 tall).

There is no per-entry size field. The PC090OJ cell is always 16×16. A "large sprite object"
is always composed of multiple 16×16 entries placed at adjacent positions by the Block-A
producer. Size decoding from word0 is not applicable because word0 carries flip and palette,
not dimensions.

### 4.3 Tile count per entry

Fixed: 4 tiles per entry. Each Block-A entry decodes to exactly one 16×16 cell = 4 Genesis
8×8 tiles in column-major order ([TL, BL, TR, BR] = slots 0, 1, 2, 3). The decoder
`frontend_decode_pc090oj_cell()` already produces this layout after the tile-order fix in
build 284. No change to tile count per entry.

### 4.4 Genesis SAT size field per entry

Fixed: `0x0500` (bits 11-10 = `01` = 2 tiles tall, bits 9-8 = `01` = 2 tiles wide).

This correctly specifies a 16×16 sprite (2×2 tiles). It does not change in this slice.

### 4.5 Column-major tile order

Already correct after the build 284 fix. `frontend_decode_pc090oj_cell()` writes:
- slot 0 (dst + 0×32): top-left
- slot 1 (dst + 1×32): bottom-left
- slot 2 (dst + 2×32): top-right
- slot 3 (dst + 3×32): bottom-right

This matches Genesis VDP column-major scan order for a 2×2 sprite. No change needed.

### 4.6 Canonical Block-A source address

Single address: `0xE0FF11FE` for both prepare and commit.

In `genesistan_sprite_tile_prepare()`:
```c
/* Current (wrong): */
const u8 *entry = workram_bytes + 0x11B2;

/* Correct: */
const u8 *entry = (const u8 *)0xE0FF11FE;
```

The absolute address `0xE0FF11FE` is the renderer-consumed Block-A window that the commit
assembly already reads from. Both prepare and commit must read from this same address so
lut[N] always corresponds to the descriptor the commit loop processes at position N.

---

## 5. Responsibility Classification

| Responsibility | Classification | Notes |
|---|---|---|
| Block-A scan (18 entries) | MOVE NOW (unified) | Both prepare and commit must read from 0xE0FF11FE |
| Validity filtering (0x0180 sentinel, all-zero skip) | KEEP TEMPORARILY | Current 0x0180 check in prepare and commit is sufficient; full all-zero skip deferred |
| Coordinate conversion (y+0x80, x+0x80) | MOVE NOW | Already in commit; stays there |
| Tile decode (PC090OJ → Genesis 4bpp) | KEEP TEMPORARILY | Correct after build 284; no change |
| VRAM tile residency (upload decoded tiles) | KEEP TEMPORARILY | Correct after build 285; no change |
| Per-entry LUT mapping | KEEP TEMPORARILY | Correct structure; changes only to use unified source address |
| **Sprite size interpretation** | MOVE NOW | Size is confirmed 2×2 per entry; no size field to decode; rule is now documented and fixed |
| **word0 attr decode (flip + palette)** | MOVE NOW | flipy from bit15, flipx from bit14, palette line from bits 3-0 + sprite_colbank |
| **Canonical Block-A source (prepare = commit)** | MOVE NOW | prepare must read from 0xE0FF11FE, not workram_bytes + 0x11B2 |
| Multi-tile grouping / tile count per entry | CONFIRMED FIXED | One entry = one 16x16 cell = 4 tiles; no change needed |
| Tile sequencing within a grouped sprite | CONFIRMED FIXED | Column-major [TL, BL, TR, BR] correct after build 284 |
| SAT link chain | CONFIRMED FIXED | Sequential link chain correct after build 284 |
| Palette line handling | MOVE NOW | Derive palette line from word0 bits 3-0 + sprite_colbank |
| Flipscreen | DEFER | Not implemented; deferred per design plan |
| Animation fidelity | DEFER | Tile code changes per Block-A update automatically |

---

## 6. Implementation Boundary

### Changes in `apps/rastan/src/main.c` (`genesistan_sprite_tile_prepare()`)

**Change 1 — Unify Block-A source address:**
```c
/* Replace: */
const u8 *entry = workram_bytes + 0x11B2;
/* With: */
const u8 *entry = (const u8 *)0xE0FF11FE;
```
The `workram_bytes` local variable and the `0x11B2` byte offset are replaced by the
explicit absolute address that matches the commit assembly's source. The `workram_bytes`
local may still be needed for the dead C helper path (`genesistan_render_sprites_vdp`) and
must not be removed from that context.

**Change 2 — Read word0 in prepare loop and pass it to the LUT:**
Currently the LUT stores only `uint16_t` tile indices. To carry word0 through to the commit,
either:
- Expand the LUT to store both tile index and word0 attr per entry, OR
- Add a parallel array `genesistan_sprite_attr_lut[18]` for word0 values

The parallel array is preferred: it keeps the existing tile LUT unchanged and is a clean
extension of the current architecture.

New WRAM structure needed: `volatile uint16_t genesistan_sprite_attr_lut[18]` alongside
`genesistan_sprite_tile_lut[18]` in `wram_overlay.launcher`.

In the prepare loop, extract word0 and store it:
```c
const u16 word0 = (u16)(((u16)entry[0] << 8) | entry[1]);
...
lut[idx]      = (u16)(FRONTEND_RUNTIME_SPRITE_TILE_BASE + (slot * 4U));
attr_lut[idx] = word0;   /* carries flipy[15], flipx[14], color bank[3:0] */
```

**Change 3 — sprite_colbank derivation in prepare:**
`sprite_colbank = (genesistan_arcade_workram_words[10] & 0x00E0) >> 1`

Store the resolved palette line per entry in the attr_lut, OR compute it in the commit
assembly from word0 + a separate sprite_colbank value. The simpler approach is to store the
pre-computed palette_line (0-3) per entry in the attr_lut. This keeps the assembly commit
free of the multi-step palette bank lookup:
```c
const u16 sprite_ctrl    = genesistan_arcade_workram_words[10];
const u16 sprite_colbank = (u16)((sprite_ctrl & 0x00E0) >> 1);
...
const u16 flipy    = (word0 >> 15) & 1U;
const u16 flipx    = (word0 >> 14) & 1U;
const u16 color    = (u16)((word0 & 0x000F) | sprite_colbank);
const u16 pal_line = color >> 4;
/* Pack into attr_lut: bits 3-2 = pal_line, bit 1 = flipy, bit 0 = flipx */
attr_lut[idx] = (u16)((pal_line << 2) | (flipy << 1) | flipx);
```

### Changes in `apps/rastan/src/startup_trampoline.s` (`genesistan_sprite_commit_asm`)

**Change 4 — Load attr_lut alongside tile_lut:**
A second base register (or offset from the existing a3) points to
`wram_overlay + FRONTEND_RUNTIME_SPRITE_ATTR_LUT_OFFSET`.

**Change 5 — Decode attr and build correct tile_attr word:**
```asm
/* Currently: */
andi.w  #0x07FF, %d1    /* mask to 11-bit tile index */
ori.w   #0x8000, %d1    /* set priority bit only — palette=0, flip=0 */

/* Replace with: */
andi.w  #0x07FF, %d1            /* mask to 11-bit tile index */
move.w  (%a4), %d4              /* load attr byte: bits 3-2=pal, bit1=flipy, bit0=flipx */
adda.w  #2, %a4                 /* advance attr_lut pointer */

/* Build tile_attr:
   Genesis SAT word2:
     bit 15 = priority (always 1)
     bits 14-13 = palette line (0-3)
     bit 12 = flipy
     bit 11 = flipx
     bits 10-0 = tile index */
move.w  %d4, %d3                /* copy attr byte */
andi.w  #0x0003, %d3            /* extract pal_line (bits 3-2 of attr_lut packed byte) */
lsr.w   #2, %d3                 /* ... wait — adjust for the packed encoding above */
/* Alternatively, keep the encoded attr_lut word with pre-shifted bits: */
/* pal_line << 13, flipy << 12, flipx << 11, all OR'd into tile_attr */
ori.w   #0x8000, %d1            /* priority */
/* OR in pal, flipy, flipx from attr_lut (pre-shifted by prepare) */
or.w    %d4, %d1                /* merge pre-shifted attr bits into tile_attr */
```

The simpler encoding in the attr_lut: store pre-shifted bits ready to OR directly into the
upper half of the SAT word2:
```c
/* In prepare: */
attr_lut[idx] = (u16)((pal_line << 13) | (flipy << 12) | (flipx << 11));
```
Then in assembly:
```asm
andi.w  #0x07FF, %d1    /* mask tile index to 11 bits */
ori.w   #0x8000, %d1    /* priority bit */
or.w    (%a4)+, %d1     /* OR in pre-shifted pal/flip bits from attr_lut */
```
This is the recommended encoding: attr_lut[N] stores bits 15-11 of SAT word2 with priority
already excluded (priority is always 1), so a single `or.w` in the commit loop applies
palette and flip in one instruction.

### New WRAM structures

In `wram_overlay.launcher` (in `startup_bridge.c` / `main.h`):
```c
volatile uint16_t genesistan_sprite_attr_lut[18];
```
Alongside the existing:
```c
volatile uint16_t genesistan_sprite_tile_lut[18];
```

New assembly offset constant needed:
```
FRONTEND_RUNTIME_SPRITE_ATTR_LUT_OFFSET = <offset of genesistan_sprite_attr_lut in wram_overlay>
```

---

## 7. New Live Flow (numbered)

After this slice, the ordered execution every vblank:

```
genesistan_frontend_live_vint_handoff():

  1. genesistan_run_original_frontend_tick()
     - Arcade level-5 handler fires at 0x03A208
     - Block-A producer at 0x03AAEC fills 0xE0FF11FE with 18 fresh entries
     - Returns after arcade RTE

  2. genesistan_sprite_tile_prepare()  [C, MODIFIED]
     - Reads Block-A from 0xE0FF11FE (now unified with commit source)
     - For each non-sentinel entry N:
         Extracts code from word2 & 0x3FFF
         Decodes tile via frontend_decode_pc090oj_cell() if new unique code
         Stores tile index in genesistan_sprite_tile_lut[N]
         Extracts word0: flipy, flipx, palette line
         Stores pre-shifted attr in genesistan_sprite_attr_lut[N]
     - DMA uploads decoded tiles to VRAM 1024+

  3. genesistan_sprite_commit_asm()  [Assembly, MODIFIED]
     - Count pass: determine number of valid (non-sentinel, non-zero-LUT) entries
     - Write pass: for each valid entry N:
         Reads Y from 0xE0FF11FE + N*8 word1, applies +0x80 bias
         Reads X from 0xE0FF11FE + N*8 word3, applies +0x80 bias
         Loads tile index from genesistan_sprite_tile_lut[N]
         Loads pre-shifted pal/flip bits from genesistan_sprite_attr_lut[N]
         Builds SAT word2: (tile_index & 0x07FF) | 0x8000 | attr_bits
         Writes SAT entry: Y, size/link, tile_attr, X to VDP data port at 0xC00000

  return
```

---

## 8. Temporary Limitations Still Allowed

After this slice, the following remain temporary:

| Limitation | Acceptable for this slice |
|---|---|
| Palette correctness (full arcade palette mapping) | TEMPORARY — palette line from word0 is now decoded, but full CRAM calibration and palette bank mapping are deferred |
| Animation cycling beyond Block-A update | TEMPORARY — tile code changes per Block-A automatically |
| Flipscreen transform | DEFERRED — no flipscreen support; consistent with prior plan |
| Full gameplay sprite coverage (Block-B 4 entries) | TEMPORARY — this slice applies to Block-A only (18 entries); Block-B added in a later pass |
| Background/tilemap rendering | DEFERRED — this slice is sprite-only |
| LRU tile cache for steady-state | TEMPORARY — per-frame flat scan remains acceptable |

---

## 9. Success Criteria

Measurable criteria for Cody:

1. `genesistan_sprite_tile_prepare()` reads Block-A from `0xE0FF11FE` (not `workram_bytes + 0x11B2`). Verified by source code inspection.

2. `genesistan_sprite_attr_lut[18]` exists in `wram_overlay.launcher` alongside `genesistan_sprite_tile_lut[18]`. Verified by build inspection.

3. For each valid Block-A entry N at runtime, `genesistan_sprite_attr_lut[N]` contains `(pal_line << 13) | (flipy << 12) | (flipx << 11)` where pal_line, flipy, flipx are decoded from the word0 of the corresponding Block-A entry at `0xE0FF11FE + N*8`. Probe verifiable.

4. SAT tile_attr word (SAT word2) for each entry equals `(tile_index & 0x07FF) | 0x8000 | attr_lut[N]`. For the title logo (word0=0x0000, pal_line=0, flipy=0, flipx=0), this equals `0x8000 | tile_index` — same as before. For a gameplay entry with word0=0x8000 (flipy only), SAT word2 has bit 12 set. Probe verifiable.

5. Prepare source address and commit source address both resolve to `0xE0FF11FE`. Static code check: prepare uses absolute `0xE0FF11FE`; commit already uses `movea.l #0xE0FF11FE, %a0`. They are the same.

6. Visual output shows correctly-attributed sprite cells: title logo cells appear with correct palette colors (PAL0, no spurious color garbling), and any flipped gameplay sprite tile appears mirrored correctly.

7. System-wide: applies to all 18 Block-A entries, not entry 0 only.

8. SAT link chain remains correct: traversal_len=N (N = number of non-sentinel entries), chain_ok=true.

---

## 10. Out-of-Scope Items

Cody MUST NOT touch any of the following:

- Block-B sprite descriptors (0xE0FF01BC, 4 entries) — this slice is Block-A only
- Sprite size decoding — size is confirmed 2×2 per entry; no size field exists to decode
- Flipscreen transform — deferred per design plan
- Full palette correctness / CRAM calibration — deferred; this slice adds palette line derivation from word0, not CRAM management
- Animation cycling beyond Block-A automatic update — deferred
- Background/tilemap rendering (PC080SN planes, text shadow, scroll)
- `genesistan_render_sprites_vdp()` function body — leave dead code in place
- Any `specs/` JSON patch files — no spec changes
- Exception handler code — untouched
- `frontend_decode_pc090oj_cell()` tile-ordering logic — correct after build 284, no change
- VRAM layout constants (`FRONTEND_RUNTIME_SPRITE_TILE_BASE`, tile region 1024+) — unchanged
- SAT link chain logic in assembly — correct after build 284, no change
- Tile LUT structure (`genesistan_sprite_tile_lut[18]`) — unchanged, only parallel attr_lut is added

---

## 11. Rainbow Islands / Cadash Sanity Check

Rainbow Islands Genesis uses a WRAM descriptor staging area around `0xFFFA80/0xFFFB00`
where each entry carries a complete tuple including palette and flip bits, not just a tile
index. The staging routine at `0x19A2` writes `y, attr, tile, x` tuples where the attr word
carries priority, palette line, and flip bits as a pre-composed value before SAT upload.
This confirms the pattern: the per-entry attr word (equivalent to word0 in Block-A) must be
decoded and composed into the SAT tile_attr before commit, not hardcoded. Rastan's current
commit path hardcodes palette=0 and flip=0 regardless of word0 — this is the exact
deficiency that Rainbow Islands' staging discipline avoids.

Cadash Genesis similarly programs SAT descriptor words through a script/descriptor emit
path at `0x8C9A–0x8F60` where the tile attribute word (including palette and flip) is
computed from descriptor data rather than hardcoded. Both Taito Genesis ports treat the
per-entry attribute word as a live, decoded value derived from the arcade sprite descriptor,
not a constant.

Both references confirm: the next correct step for Rastan is to decode word0 attr (flip +
palette bank) per entry and apply it to SAT tile_attr, exactly as Option A specifies.

---

## 12. Final Recommendation

The chosen next slice is Option A: decode the full word0 attribute field (flipy from bit 15,
flipx from bit 14, palette line from bits 3-0 combined with sprite_colbank) for every
Block-A entry, store the result in a new parallel `genesistan_sprite_attr_lut[18]` array,
and apply the decoded bits to the SAT tile_attr word in `genesistan_sprite_commit_asm`.
Simultaneously, unify the Block-A source address in `genesistan_sprite_tile_prepare()` to
`0xE0FF11FE` (the canonical renderer-consumed window already used by the commit assembly)
so that lut[N] and attr_lut[N] always correspond to the same live Block-A descriptor as
the SAT entry the commit loop writes for position N. These two rules together constitute
the complete sprite interpretation layer: correct tile selection, correct palette, and
correct orientation for every entry in the current live Block-A stream.

The next implementation step is a real sprite-system slice that adds size/grouping interpretation for the full current Block-A stream, so the existing live decode/upload/SAT path can begin producing recognizable composed sprite output.
