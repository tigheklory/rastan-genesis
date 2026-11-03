# Sprite Interpretation Failure Diagnosis

## 1. Purpose

Diagnose why visible sprite output is incorrect despite a confirmed working full prototype
execution path. The pipeline is proven live end-to-end:
`genesistan_run_original_frontend_tick()` → `genesistan_sprite_tile_prepare()` →
`genesistan_sprite_commit_asm()`. VRAM tile region 1024+ is nonzero, SAT entries map to
LUT-derived tile indices, CRAM is valid — but visible sprite output is still FAIL.

The failure is in **sprite interpretation**, not pipeline activation.

---

## 2. Confirmed Working Stages

- Live execution path: all three functions fire every vblank at correct rate (~791/s)
- VRAM tile region 1024+ (`0x8000+`): nonzero, stable, populated post-launch
- SAT tile index source: LUT-derived tile indices (no `0x8001` fallback active)
- At least one sprite-like object is visible on screen (non-blank output exists)
- CRAM is valid and populated
- No C helper in live path

---

## 3. Primary Failure Analysis

### A. Tile Decode Layout Analysis

`frontend_decode_pc090oj_cell()` at `main.c:1023` splits a 16×16 PC090OJ cell (128 bytes)
into four Genesis 8×8 tiles (32 bytes each) using this layout:

```
Rows 0–7:  tile[0] = dst + (0 * 32)  (top-left 8×8)
           tile[1] = dst + (1 * 32)  (top-right 8×8)
Rows 8–15: tile[2] = dst + (2 * 32)  (bottom-left 8×8)
           tile[3] = dst + (3 * 32)  (bottom-right 8×8)
```

Output tile ordering: [top-left, top-right, bottom-left, bottom-right] — row-major.

Genesis VDP renders a 2×2 sprite (SPRITE_SIZE(2,2)) reading tiles in **column-major** order:
```
T+0 = top-left
T+1 = bottom-left      ← column 0 first
T+2 = top-right
T+3 = bottom-right     ← column 1 second
```

Current decode writes [TL, TR, BL, BR] but Genesis VDP reads them as [TL, BL, TR, BR].
Result: tile[1] (top-right source data) displays bottom-left on screen, and tile[2]
(bottom-left source data) displays top-right on screen. The 16×16 sprite's right column
and left column are swapped.

**Severity**: Every 2×2 sprite rendered has its top-right and bottom-left quadrants
transposed. The object is visible but its pixel content is geometrically wrong in the
right/left column arrangement.

### B. Sprite Size Encoding Analysis

`genesistan_sprite_commit_asm` line `move.w #0x0500, (%a2)` hardcodes SAT word1 for every
entry.

`0x0500 = 0000 0101 0000 0000` binary:
- Bits 15-12: unused by VDP
- Bits 11-10: vertical size = `01` = 2 tiles = 16 pixels tall — CORRECT for 16×16
- Bits 9-8: horizontal size = `01` = 2 tiles = 16 pixels wide — CORRECT for 16×16
- Bits 6-0: link field = `0x00` = 0

Size encoding `0x0500` correctly specifies a 2×2 (16×16 pixel) sprite. This is not itself
the source of wrong pixel geometry. The size field is intentionally hardcoded per design
plan and within stated scope.

### C. SAT Link Chain Analysis

The Genesis VDP SAT link field (bits 6-0 of word1) defines the next SAT entry index to
process. The VDP renders sprites by following the link chain starting at entry 0. When the
VDP encounters a link value of 0 in entry N, it terminates the chain (the chain only
continues as long as link > 0, pointing to the next valid entry).

Current state in `genesistan_sprite_commit_asm`:

```asm
move.w  #0x0500, (%a2)   /* SAT word1: size/link (temporary fixed) */
```

`0x0500` has bits 6-0 = `0x00`. Every single SAT entry written has link = 0. This means:
- Entry 0 is rendered with link=0 → VDP terminates the chain after entry 0
- Entries 1–17 are written to VRAM but are never traversed by the VDP hardware

**Result**: Only the first non-skipped entry in the chain is visible. All remaining entries
are written to SAT memory but are invisible to the VDP renderer. This is consistent with
the observation "at least one sprite-like object is visible on screen" — exactly one entry
is rendered, not all 18.

The correct link chain for 18 active entries:
- Entry 0: link = 1
- Entry 1: link = 2
- ...
- Entry N-1: link = N (next entry)
- Last active entry: link = 0 (terminator)

This is a **hardware-level silencing bug**: the data is correct, the DMA is correct, the
tile content is correct, but the VDP stops reading after the first entry because every
entry's link field is zero.

### D. Tile Attribute Analysis

`genesistan_sprite_commit_asm` constructs tile_attr as:

```asm
andi.w  #0x07FF, %d1     /* mask to 11-bit tile index */
ori.w   #0x8000, %d1     /* set priority bit */
```

This produces: priority=1, palette=0 (PAL0), vflip=0, hflip=0, tile_index=(LUT value).

PAL0 is confirmed loaded and valid. Priority=1 is correct for sprites over background.
Flip bits are not decoded from word0 attr/flags field — this is within stated scope
(flip handling deferred per design plan). The tile attribute construction is functionally
correct for the prototype scope.

### E. Coordinate Transform Analysis

Assembly applies:
```asm
addi.w  #0x0080, %d0    /* SAT y bias: screen_y → VDP y (add 128) */
addi.w  #0x0080, %d2    /* SAT x bias: screen_x → VDP x (add 128) */
```

Genesis SAT requires: VDP_y = arcade_y + 128, VDP_x = arcade_x + 128. Both biases are
correctly applied. The coordinate transform is correct.

The assembly reads Y from `2(%a0)` (word1 = y_raw) and X from `6(%a0)` (word3 = x_raw),
which matches the Block-A entry format `word0=attr/flags, word1=y_raw, word2=tile_code,
word3=x_raw`. This is correct.

### F. LUT Source Buffer Mismatch Analysis

`genesistan_sprite_tile_prepare()` populates the LUT by scanning entries from:
```c
const u8 *entry = workram_bytes + 0x11B2;  /* 0xE0FF11B2 */
```

`genesistan_sprite_commit_asm` reads SAT source entries from:
```asm
movea.l #0xE0FF11FE, %a0   /* Block-A base */
```

`0xE0FF11FE - 0xE0FF11B2 = 0x4C` = 76 bytes = 9.5 entries of 8 bytes each.

These are **different buffers**. Per the vblank architecture documentation:
- `0xE0FF11B2` = **producer-owned** descriptor window (filled by `0x05A174` arcade code)
- `0xE0FF11FE` = **renderer-consumed** descriptor window (read by original renderer `0x2005C4`)

The prepare function reads entry N from 0x11B2, decodes its tile code, and stores the
VRAM tile index in `lut[N]`. The commit assembly reads entry N from 0x11FE and uses
`lut[N]` to build the SAT tile attribute. Because 0x11B2 entry N and 0x11FE entry N are
NOT the same sprite descriptor, lut[N] refers to the tile decoded for a different sprite
entry than what the assembly is actually rendering for that slot.

However, the AGENTS_LOG probe data shows `idx0 code=03CA lut=0400 sat_tile=0400` and
`sat_attr_8001=0` — indicating at least entry 0's tile is correctly resolved. If the
arcade ROM's retarget patches cause both addresses to reflect the same live data stream,
this may not be the dominant cause of missing sprites, but it is an architectural
inconsistency that should be resolved. The confirmed dominant cause of only one visible
sprite is the link chain issue.

---

## 4. Root Cause Classification

**Primary (dominant): C — Missing SAT link chain**

Every SAT entry has `link = 0` (bits 6-0 of word1 = `0x00` from hardcoded `0x0500`).
The Genesis VDP halts chain traversal after the first entry with link=0. Only entry 0
is rendered. All remaining entries are invisible to the VDP. This directly explains
"at least one sprite-like object visible" — exactly the first non-skipped entry renders.

**Secondary: A — Incorrect tile decode layout (row-major vs column-major)**

The current decode writes tiles in [TL, TR, BL, BR] order. Genesis VDP reads a 2×2
sprite column-first: [TL, BL, TR, BR]. Tiles at positions +1 and +2 within each decoded
cell are transposed. Every 16×16 sprite has its right column and left column pixel content
swapped, producing geometrically wrong pixel output even on the one visible sprite.

**Tertiary: F — LUT populated from wrong source buffer (0x11B2 vs 0x11FE)**

Architectural inconsistency: prepare reads producer window, commit reads renderer window.
Effect is masked if both windows contain the same tile codes at runtime (which current
probe data suggests for entry 0). Needs resolution before multi-sprite correctness can
be verified across all 18 slots.

---

## 5. Rainbow Islands / Cadash Reference Check

Rainbow Islands Genesis (reference doc: `rainbow_islands_arcade_vs_genesis_graphics_comparison.md`):
- Uses a WRAM staging buffer (`0xFFFA80/0xFFFB00`) for sprite descriptors with a dedicated
  link chain built during staging — analogous to the required link chain fix
- The tuple write sequence `y, attr, tile, x` in the staging routine at `0x19A2` explicitly
  builds per-entry link fields as part of descriptor formation, not as a constant
- This confirms: in a correct Genesis sprite pipeline, the link field must be computed
  per-entry during commit, not hardcoded to a fixed value

Cadash Genesis (reference doc: `cadash_arcade_vs_genesis_graphics_comparison.md`):
- Script/descriptor driven sprite emission via `0x8C9A..0x8F60` explicitly programs VDP
  descriptor words including link/chain fields as part of the SAT emit sequence
- Confirms the same pattern: the link field is a dynamic per-entry value, not a hardcoded
  constant

Both reference implementations confirm that the SAT link chain is a computed, per-entry
sequential value that must terminate at 0 on the last rendered entry only. Hardcoding
link=0 in all entries is not consistent with any correct Genesis SAT implementation.

---

## 6. Exact Next Implementation Slice

### What changes

**Fix 1 (PRIMARY): SAT link chain in `genesistan_sprite_commit_asm`**

Replace the hardcoded `move.w #0x0500, (%a2)` with a computed word1 that:
- Keeps size bits 11-8 = `0x05` (2×2, 16×16)
- Sets link bits 6-0 = the sequential index of the NEXT sprite entry in the commit loop

The link field must be assigned as each entry is written. A counter tracking the
current output SAT entry number must be maintained. For each written entry N (not skipped),
link = N+1 if more entries follow, link = 0 for the last written entry.

Because skipped entries (0x0180 sentinel or zero LUT) are not written to SAT, the link
numbering must count ONLY entries that are actually written, not raw input entry indices.

Implementation approach in assembly:
1. Maintain a separate output slot counter (e.g., `%d3`) that increments only when a SAT
   entry is written (not skipped)
2. After the full loop pass, the last-written entry's word1 link field must be patched to 0
   (or known in advance if entry count is pre-computed)

Alternative: two-pass approach — first count valid entries, then write with correct links.
Or: write link=N+1 for all entries speculatively, then patch the last entry to link=0 after
the loop.

**Fix 2 (SECONDARY): Tile decode column-major reordering in `frontend_decode_pc090oj_cell()`**

The current decode writes tiles as [TL, TR, BL, BR] (row-major). Genesis VDP requires
column-major [TL, BL, TR, BR] for 2×2 sprite rendering.

Change the tile index assignments in `frontend_decode_pc090oj_cell()`:
- Rows 0–7, left half → tile[0] (top-left) — UNCHANGED
- Rows 0–7, right half → tile[2] (top-right) — was tile[1], must move to slot 2
- Rows 8–15, left half → tile[1] (bottom-left) — was tile[2], must move to slot 1
- Rows 8–15, right half → tile[3] (bottom-right) — UNCHANGED

In terms of dst offsets:
```
Current:
  tile_left  = dst + (0 * 32) + (y * 4)         for y < 8
  tile_right = dst + (1 * 32) + (y * 4)         for y < 8
  tile_left  = dst + (2 * 32) + ((y-8) * 4)     for y >= 8
  tile_right = dst + (3 * 32) + ((y-8) * 4)     for y >= 8

Required (column-major for Genesis VDP):
  tile_left  = dst + (0 * 32) + (y * 4)         for y < 8   (slot 0: top-left)
  tile_right = dst + (2 * 32) + (y * 4)         for y < 8   (slot 2: top-right)
  tile_left  = dst + (1 * 32) + ((y-8) * 4)     for y >= 8  (slot 1: bottom-left)
  tile_right = dst + (3 * 32) + ((y-8) * 4)     for y >= 8  (slot 3: bottom-right)
```

### Files modified

- `apps/rastan/src/startup_trampoline.s`: Fix SAT word1 link field in
  `genesistan_sprite_commit_asm` — compute sequential link index per written entry;
  last written entry gets link=0
- `apps/rastan/src/main.c`: Fix `frontend_decode_pc090oj_cell()` tile slot assignments —
  swap slots 1 and 2 to produce column-major output order for Genesis VDP

### Why this produces visible improvement

- Fix 1: The Genesis VDP will traverse all N written SAT entries instead of stopping after
  the first one. All 18 (or however many are non-skipped) sprites will become visible
  simultaneously. This is the blocker preventing multi-sprite output.
- Fix 2: Each 16×16 sprite will display with correct pixel geometry — the top-right and
  bottom-left quadrants will no longer be transposed. Recognizable sprite shapes will
  appear instead of geometrically scrambled tile content.

Together, Fix 1 restores the expected number of visible sprites, and Fix 2 restores
correct pixel layout for each sprite.

---

## 7. Final Conclusion

**Root cause letter: C (primary), A (secondary)**

**Primary**: SAT link chain hardcoded to `0x0500` (link=0) for all entries. The Genesis
VDP terminates sprite chain traversal after the first entry. Only one sprite renders.

**Primary fix**: In `startup_trampoline.s`, replace the hardcoded `move.w #0x0500, (%a2)`
with a computed word1 that sets link = next_output_slot for each written entry and link=0
for the last written entry.

**Secondary**: `frontend_decode_pc090oj_cell()` in `main.c` writes tiles in row-major
order [TL, TR, BL, BR]. Genesis VDP 2×2 sprite rendering requires column-major order
[TL, BL, TR, BR]. Tiles at decoded positions 1 and 2 are transposed, producing
geometrically incorrect pixel output even for the one currently-visible sprite.

**Secondary fix**: In `main.c`, swap the tile slot assignments in
`frontend_decode_pc090oj_cell()` so that top-right pixels land at slot 2 and bottom-left
pixels land at slot 1.
