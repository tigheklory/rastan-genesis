# Next Sprite Content Selection / Object Composition Slice

## 1. Purpose

Define the next forward implementation slice for the Rastan Genesis sprite system.
The pipeline is proven live end-to-end (arcade tick → `genesistan_sprite_tile_prepare()` →
`genesistan_sprite_commit_asm()`). VRAM tile region 1024+ is nonzero and stable. SAT link
chain is sequential and correctly terminated. Block-A source is unified at `0xE0FF11FE` for
both prepare and commit. word0 attr decode (pal_line, flipy, flipx) is implemented and
runtime-proven. All upstream pipeline plumbing is correct.

Visual output remains unrecognizable. The remaining failure is in content selection and
object composition, not in pipeline architecture.

---

## 2. Chosen Next Content / Composition Slice

**Implement tile-code-zero filtering in the prepare and commit paths, with a WRAM-tracked
active-entry count, so that SAT slots are occupied only by Block-A entries with nonzero
tile codes.**

This is the one chosen slice. It covers the specific content-selection rule that is
currently violated, and applies system-wide across all 18 Block-A entries.

### Why this is the primary blocker

From Build 283 runtime evidence:

- `unique_codes=2` — only 2 unique tile codes across 18 entries
- Entry idx0: `code=0x03CA` (nonzero, a real sprite cell)
- Entries idx1–idx17: `code=0x0000` (tile code zero for 17 of 18 entries)
- SAT result: `idx1 lut=0x0404 sat_tile=0x0404`, etc. — VRAM tile 1028 for all 17 entries

The current implementation treats tile code 0x0000 as a valid content entry. It decodes
PC090OJ cell 0, uploads the resulting tiles to VRAM slot 1 (index 1028), and writes 17
SAT entries pointing to that slot. This consumes 17 of 18 SAT slots with a single repeated
pattern. Whatever PC090OJ cell 0 contains (it may be blank, or it may be a graphics tile
unrelated to the title logo), 17 of 18 SAT positions are driven from it.

The real title logo is a composed object assembled from multiple distinct PC090OJ cells at
specific x/y positions. If Block-A at measurement time mostly contains `code=0x0000`
entries, those entries are inactive placeholders, not logo content. The one active entry
(idx0, `code=0x03CA`) represents real sprite content; the 17 zero-code entries do not.

The current prepare and commit paths have no mechanism to distinguish inactive (zero tile
code) entries from active (nonzero tile code) entries. Every non-sentinel entry goes into
the SAT regardless. This means:

- SAT slots are wasted on inactive entries
- The one real sprite cell (0x03CA) is surrounded by 17 placeholder entries occupying screen positions
- Object composition of the multi-cell title logo is impossible when all cells share the
  same tile code and are effectively blank or uniform

### What the correct content-selection rule is

An entry with tile code `word2 & 0x3FFF == 0x0000` is inactive. The PC090OJ hardware in
the arcade treated tile code 0 as "no sprite" — it is the cleared/reset state for an unused
entry. Active sprite content always has a nonzero tile code. The title logo cells have tile
codes in the range 0x03CA and above; they are nonzero. A Block-A entry with `code=0x0000`
must be skipped by prepare (no decode, no LUT write) and by commit (no SAT entry emitted).

This rule is distinct from the existing `y_raw == 0x0180` sentinel filter. The 0x0180
sentinel catches entries where the y-coordinate marks the object as off-screen. The
zero-tile-code filter catches entries where the object content itself has never been set
(the tile slot is uninitialized/cleared). Both filters are needed; they catch different
cases.

---

## 3. Why This Is the Next Highest-Value Step

All prior slices fixed pipeline plumbing and attribute correctness. All those fixes are
confirmed working. The pipeline now correctly:

- Reads from the canonical Block-A window (`0xE0FF11FE`)
- Decodes PC090OJ cells into Genesis tiles
- Uploads tiles to VRAM 1024+
- Builds the SAT link chain correctly
- Applies pal/flip attr from word0 to SAT word2

Yet visuals remain unrecognizable. The reason is content: the pipeline is working correctly
but it is processing the wrong entries. 17 of 18 Block-A entries have zero tile codes. The
current path faithfully decodes, uploads, and commits all 18 — but 17 of them carry zero-code
content.

Filtering zero-code entries removes the noise from SAT output. After the filter:

- Only entries with real tile codes emit SAT entries
- The one entry with `code=0x03CA` emits one 16x16 sprite at its correct position
- When the title logo state populates more nonzero-code entries (as the game produces more
  frame data), each one will appear at its correct position with the correct tile
- The composed title logo will become visible as Block-A accumulates nonzero entries across frames

Without this filter, even a fully populated Block-A (all 18 entries with distinct nonzero
codes) would still be partially obscured if some entries are zero-code placeholders from a
prior cleared state.

This is the content-selection step that separates active from inactive entries. It is the
prerequisite for correct object composition.

---

## 4. Content-Selection / Object-Composition Rule to Implement

### 4.1 Current wrong assumption about content selection

The current `genesistan_sprite_tile_prepare()` processes every Block-A entry that passes
the `y_raw == 0x0180` sentinel check. It does not test whether `code == 0x0000`. For a
zero-code entry:

- `code = (word2 & 0x3FFF) = 0x0000`
- No prior unique-code match for code=0 on first occurrence → goes to the "new unique code"
  path
- Decodes PC090OJ cell 0 into live_decode_upload_buffer slot 1 (first slot after idx0's
  code=0x03CA)
- Writes `lut[idx] = FRONTEND_RUNTIME_SPRITE_TILE_BASE + 1*4 = 0x0404`
- Writes `attr_lut[idx] = (pal_line << 13) | ...`

The commit assembly sees `lut[idx] = 0x0404`, nonzero, and emits a full SAT entry.

This means 17 SAT entries are emitted from zero-code content. 17 of the 18 SAT slots
available from this Block-A stream carry placeholder tile data at positions derived from
zero-code entries' x/y coordinates.

### 4.2 Correct content-selection rule

After extracting `code = (word2 & 0x3FFF)` from each Block-A entry:

- If `code == 0x0000`: the entry is inactive. Skip it in prepare (no decode, no lut write,
  no attr_lut write). `lut[idx]` remains 0. The commit assembly already skips entries where
  `lut[idx] == 0`, so no SAT entry is emitted for zero-code entries.
- If `code != 0x0000`: the entry is active. Proceed with existing decode/upload/lut path.

This rule applies to all 18 Block-A entries system-wide. It does not apply only to idx0 or
to any specific sprite type. Every entry in the Block-A stream is subject to the same
content-selection check.

### 4.3 How the rule applies in prepare vs commit

In `genesistan_sprite_tile_prepare()` (C code):

- After extracting `code` from the current entry, add a guard before the
  decode/slot-assignment block:
  ```c
  if (code == 0)
  {
      continue;   /* inactive entry: no decode, lut[idx] stays 0 */
  }
  ```
- `lut[idx]` and `attr_lut[idx]` remain 0 for zero-code entries (already zeroed in the
  initialization loop at the top of the function).

In `genesistan_sprite_commit_asm` (assembly):

- The commit loop already has: `tst.w %d1 / beq .Lsprite_commit_skip` which skips entries
  where `lut[idx] == 0`. Since prepare leaves `lut[idx] = 0` for zero-code entries, the
  commit skip path already handles them correctly.
- No change to the assembly is needed for this rule. The existing zero-LUT guard is
  sufficient once prepare stops writing nonzero LUT values for zero-code entries.

The count pass in commit also uses `tst.w %d1 / beq .Lsprite_count_skip`. This ensures the
valid entry count `d6` used for link-chain generation excludes zero-code entries. The link
chain will be computed only over truly active entries.

### 4.4 WRAM structure for tracking active entry count and indices

A new WRAM field `genesistan_sprite_active_count` stores the number of entries with nonzero
tile codes found in the most recent prepare pass. This is used for diagnostics and for
future upstream consumers that need to know how many real sprite entries were found.

```c
volatile uint16_t genesistan_sprite_active_count;
```

Location: `wram_overlay.launcher`, alongside the existing `genesistan_sprite_tile_lut[18]`
and `genesistan_sprite_attr_lut[18]`.

In `genesistan_sprite_tile_prepare()`, after the loop, store the count:

```c
wram_overlay.launcher.genesistan_sprite_active_count = active_count;
```

where `active_count` is incremented once per loop iteration where `code != 0` and the entry
passes the sentinel check.

No separate "indices" array is needed at this stage. The commit assembly already walks
`lut[0..17]` and skips entries where `lut[idx] == 0`. The zero-vs-nonzero state of each
`lut[idx]` entry is the implicit active/inactive flag for the commit path.

### 4.5 Object composition consequence

After this change, the SAT will contain exactly N entries, where N is the number of
Block-A entries with nonzero tile codes. Each of these N entries will:

- Be at the x/y position from its word1/word3 fields (with +0x80 bias)
- Reference a VRAM tile index decoded from its specific nonzero code
- Carry the correct pal_line/flipy/flipx from its word0 attr

The spatial arrangement of these N entries at their word1/word3-derived positions IS the
object composition. No additional grouping logic is needed. The PC090OJ model places each
16x16 cell at an explicit x/y position; the composed sprite object (title logo, enemy,
player character) is defined entirely by the set of nonzero-code entries and their
positions.

When Block-A contains a partially populated title logo (e.g., only a few cells have been
written by the producer in the current frame), those cells will appear at their correct
positions. As the producer populates more cells, the composed logo assembles on screen.
With zero-code filtering active, no spurious placeholder cells interfere with the composition.

---

## 5. Responsibility Classification

| Responsibility | Classification | Notes |
|---|---|---|
| Zero-tile-code content filter in prepare | MOVE NOW | Core rule: `code==0` entries are inactive |
| Active entry count tracking (WRAM) | MOVE NOW | `genesistan_sprite_active_count` added to `wram_overlay.launcher` |
| Zero-LUT skip in commit | ALREADY CORRECT | Assembly already skips `lut[idx]==0` entries; no change needed |
| 0x0180 sentinel filter | KEEP UNCHANGED | Existing filter for y-position sentinel is correct and unchanged |
| Tile decode (PC090OJ → Genesis 4bpp) | KEEP UNCHANGED | Correct after build 284; no change |
| VRAM tile upload | KEEP UNCHANGED | Correct after build 285; no change |
| word0 attr decode | KEEP UNCHANGED | Correct after build 286; no change |
| Canonical Block-A source (`0xE0FF11FE`) | KEEP UNCHANGED | Correct after build 286; no change |
| SAT link chain | KEEP UNCHANGED | Correct after build 284; no change |
| Sprite size (2x2 per entry) | KEEP UNCHANGED | No size field in word0/word2; confirmed 16x16 per entry |
| Column-major tile ordering | KEEP UNCHANGED | Correct after build 284; no change |
| Block-B sprite descriptors (4 entries) | DEFER | This slice is Block-A only |
| Palette / CRAM calibration | DEFER | Deferred; palette line is decoded but full CRAM management deferred |
| Flipscreen transform | DEFER | Deferred per prior design plan |
| Background/tilemap rendering | DEFER | Not part of this slice |

---

## 6. Implementation Boundary

### Changes in `apps/rastan/src/main.c` (`genesistan_sprite_tile_prepare()`)

**Change 1 — Add zero-code guard in the prepare loop:**

After extracting `code` from the entry, and after the existing `y_raw == 0x0180` sentinel
check, add:

```c
if (code == 0)
{
    continue;   /* inactive entry: skip decode, lut[idx] stays 0 */
}
```

This must appear before the unique-code lookup and before any write to `lut[idx]` or
`attr_lut[idx]`.

**Change 2 — Track active count:**

Add a local `u16 active_count = 0;` initialized before the loop.
Increment `active_count` each time an entry passes both the sentinel check and the
zero-code check (i.e., each time `lut[idx]` would be written with a nonzero value).
After the loop, store: `wram_overlay.launcher.genesistan_sprite_active_count = active_count;`

### Changes in `wram_overlay.launcher` (in `main.h` or the appropriate header)

**Change 3 — Add active_count field:**

```c
volatile uint16_t genesistan_sprite_active_count;
```

Placed alongside the existing `genesistan_sprite_tile_lut[18]` and
`genesistan_sprite_attr_lut[18]`.

### Changes in `apps/rastan/src/startup_trampoline.s`

None. The assembly commit loop already skips entries where `lut[idx] == 0`. The change to
prepare causes zero-code entries to leave `lut[idx] = 0`, which the existing assembly skip
already handles. No assembly modifications are required in this slice.

---

## 7. New Live Flow (numbered)

After this slice, the ordered execution every vblank:

```
genesistan_frontend_live_vint_handoff():

  1. genesistan_run_original_frontend_tick()
     - Arcade level-5 handler fires at 0x03A208
     - Block-A producer at 0x03AAEC fills 0xE0FF11FE with up to 18 entries
     - Some entries have nonzero tile codes (active); others have code=0 (inactive/cleared)
     - Returns after arcade RTE

  2. genesistan_sprite_tile_prepare()  [C, MODIFIED]
     - Reads Block-A from 0xE0FF11FE (unchanged canonical source)
     - For each entry N:
         If y_raw == 0x0180: skip (existing sentinel filter)
         If code == 0x0000:  skip (NEW zero-code content filter)
         Otherwise (active entry):
             Lookup or assign unique slot for this code
             Decode PC090OJ cell to live_decode_upload_buffer
             Write lut[N] = FRONTEND_RUNTIME_SPRITE_TILE_BASE + (slot * 4)
             Write attr_lut[N] = (pal_line << 13) | (flipy << 12) | (flipx << 11)
             Increment active_count
     - Zero-code entries: lut[N] remains 0, attr_lut[N] remains 0
     - Stores active_count in wram_overlay.launcher.genesistan_sprite_active_count
     - DMA uploads decoded tiles to VRAM 1024+ (unchanged)

  3. genesistan_sprite_commit_asm()  [Assembly, UNCHANGED]
     - Count pass: counts entries where y_raw != 0x0180 AND lut[idx] != 0
       (zero-code entries now have lut[idx]=0, so they are skipped here automatically)
     - Write pass: for each valid entry N:
         Reads Y, X, tile index from lut[N], attr from attr_lut[N]
         Builds SAT word2: (tile_index & 0x07FF) | 0x8000 | attr_bits
         Writes SAT entry to VDP data port
     - Only active (nonzero-code) entries appear in the SAT

  return
```

---

## 8. Temporary Limitations Still Allowed

After this slice, the following remain temporary:

| Limitation | Status |
|---|---|
| Block-A may contain only 1 active entry (idx0, code=0x03CA) in some frames | ACCEPTABLE — the active entry will appear at its correct position; more entries appear as the game state advances |
| Full title logo may not be fully composed in a single frame | ACCEPTABLE — it assembles from nonzero entries as they accumulate |
| Block-B sprite descriptors (0xE0FF01BC, 4 entries) not included | TEMPORARY — Block-B is added in a later pass |
| Palette correctness / full CRAM calibration | DEFERRED — palette line from word0 is decoded; full CRAM management deferred |
| Flipscreen transform | DEFERRED — not implemented; consistent with prior plan |
| Animation cycling beyond Block-A automatic update | TEMPORARY — tile code changes per Block-A automatically |
| Background/tilemap rendering | DEFERRED — this slice is sprite-only |

---

## 9. Success Criteria

Measurable criteria for Cody:

1. In `genesistan_sprite_tile_prepare()`, after extracting `code` from each entry and after
   the `y_raw == 0x0180` sentinel check, a `code == 0` guard is present. Any entry with
   zero tile code is skipped without writing to `lut[idx]` or `attr_lut[idx]`. Verified
   by source code inspection.

2. `genesistan_sprite_active_count` exists in `wram_overlay.launcher`. Verified by build
   inspection (field present in struct, offset compiles without error).

3. At runtime, for any Block-A entry with `code == 0x0000`: `lut[idx] == 0` after prepare.
   Probe verifiable: read `genesistan_sprite_tile_lut[N]` for entries known to have
   `word2 == 0x0000`; confirm value is 0.

4. At runtime, for entry idx0 (`code=0x03CA`): `lut[0] == 0x0400` (tile index 1024).
   Unchanged from current behavior. Probe verifiable.

5. SAT entry count (traversal_len in chain check) equals the number of active
   (nonzero-code, non-sentinel) entries, not 18. For the current Block-A state
   (1 active entry observed in builds 283-286), traversal_len = 1. Probe verifiable.

6. SAT word2 for the active entry (idx0) remains `0xE400` as observed in build 286
   (pal_line=3, no flip, tile 1024). Verified: behavior for the nonzero-code entry is
   unchanged; only zero-code entries are filtered out.

7. `genesistan_sprite_active_count` equals the number of nonzero-code entries found by
   prepare. For current Block-A state (1 active entry), `active_count == 1`. Probe
   verifiable.

8. System-wide: filtering applies to all 18 Block-A entries, not to any specific index.
   If Block-A acquires more nonzero-code entries in future states, they are all decoded
   and emitted. Verified by code inspection (loop over all 18 indices).

9. SAT link chain remains correct for the reduced active set: last active SAT entry has
   link=0; chain traversal terminates correctly. Probe verifiable via `chain_ok=true`.

---

## 10. Out-of-Scope Items

Cody MUST NOT touch any of the following:

- Block-B sprite descriptors (0xE0FF01BC, 4 entries) — this slice is Block-A only
- SAT link chain logic in assembly — already correct; no change needed
- Tile decode ordering (`frontend_decode_pc090oj_cell()`) — correct after build 284
- word0 attr decode logic — correct after build 286; no change
- Canonical Block-A source address — unified at `0xE0FF11FE` after build 286; no change
- VRAM layout constants and tile region 1024+ — unchanged
- `genesistan_sprite_attr_lut[18]` structure — unchanged; parallel active_count is a new addition only
- `genesistan_sprite_tile_lut[18]` structure — unchanged
- The `0x0180` sentinel filter — already correct; must not be removed or changed
- `genesistan_render_sprites_vdp()` function body — leave dead code in place
- Any `specs/` JSON patch files — no spec changes
- Exception handler code — untouched
- Background/tilemap rendering (PC080SN planes, scroll)
- Palette system / CRAM management
- `genesistan_sprite_commit_asm` assembly — no changes needed for this slice

---

## 11. Rainbow Islands / Cadash Sanity Check

Rainbow Islands Genesis (`rainbow_islands_arcade_vs_genesis_graphics_comparison.md`):
The staged WRAM descriptor writer at `0xFFFA80/0xFFFB00` builds per-entry descriptor
tuples that are written only for active sprite objects. Inactive/unused SAT slots in
a Genesis sprite list are not populated with zero-tile-code entries — they simply are not
written. The SAT chain terminates at the last written entry. This is consistent with the
content-selection rule defined here: entries with no real content (code=0) must not
generate SAT output.

Cadash Genesis (`cadash_arcade_vs_genesis_graphics_comparison.md`):
The script/descriptor emit path at `0x8C9A–0x8F60` emits SAT descriptor words for
objects that have defined content. The emit loop does not process empty/cleared object
slots. Content selection (active vs inactive object) is implicit in the descriptor format
and the emit loop's traversal bounds — equivalent to the zero-code filter being applied
here before SAT output.

Both references confirm: the content-selection rule is "only emit SAT entries for object
slots with real content (nonzero code)." Emitting SAT entries for zero-code slots is not
consistent with any correct Genesis SAT implementation observed in these reference ports.

---

## 12. Final Recommendation

The chosen next slice is to add a zero-tile-code content filter in
`genesistan_sprite_tile_prepare()` so that Block-A entries with `code == 0x0000` are
treated as inactive and do not produce LUT entries, tile decodes, or SAT output. This is
the content-selection rule that the system currently lacks: all 17 of 18 Block-A entries
with code=0 currently consume SAT slots and VRAM decode bandwidth despite carrying no real
sprite content. After this filter, the SAT contains only entries from the Block-A stream
that carry real tile codes, and their spatial arrangement at the x/y positions from word1/word3
constitutes the object composition. No new architecture, no new assembly, no new pipeline
stages are required — only a two-line guard in the prepare loop and a new active_count
field in WRAM.

The next implementation step is a real sprite-system slice that adds content-selection / object-composition behavior for the full current Block-A stream, so the existing live decode/upload/SAT path can begin producing recognizable composed sprite output.
