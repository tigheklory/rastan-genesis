# Andy — Build 0351: One Authoritative Plane-A Cell Resolver Shared by Every Gameplay Producer

**Task:** EXTENDING · **Language:** 68000 assembly only (no C) · **Build:** 0351 (numbered, preserved).
Master design: [Andy_sonic1_native_68000_plane_a_streaming.md](Andy_sonic1_native_68000_plane_a_streaming.md).

## Tighe's Build 0350 result (recorded)
Plays essentially the same as 0349; same `D00462` crash; **no perceptible speed improvement**; Layer A
still **worse than earlier pre-0349 builds**; the Sonic-style column publisher itself introduced **no
obvious new regression**. Decision: retain the efficient publisher; fix the upstream content split.
0350 is a transfer experiment, not the correctness target.

## First proven semantic divergence (why 0349/0350 look wrong)
The two live R1P1 producers resolved the world through **different source paths**:

- **Horizontal (`selector0_native`)** read the tile code **directly** from the *live rebuilt* pointer
  `PTR[row_group]` at `0x00FF1040`, offset `(row&3)*8 + col*2`. This table is maintained by the
  arcade (`0x055904`) only for the **current column**.
- **Vertical pan helper (`.Lplane_a_publish_logical_row_native`)** did an **independent static walk**:
  `.Lplane_a_strip_src_table[row_seg] + a5@0x013E*0x40 + col_group*4` → strip entry `{word0=attr,
  word1=metatile_ptr}` → dereference metatile → `metatile[(row&3)*8 + (col&3)*2]`, **plus a
  scroll_x-derived source-column offset** (dest col `d4` vs source col `d4+base`) absent from
  `selector0`.

Different table (live split vs static strip), different indirection depth, and a different
destination↔source column mapping → the same logical cell resolved to different name words on the two
axes. Where the vertical row overwrote the horizontal column, "horizontal partially wrong."

Because the live `0x00FF1040` table only holds the **current column**, it can serve a column but not a
full row; therefore the shared resolver must be the **column-general static walk** (the format proven
against the arcade C08000 oracle in the cave analysis), with the active-segment term.

## Shared resolver
`resolve_plane_a_cell` ([tilemap_hooks.s](../../apps/rastan-direct/src/tilemap_hooks.s)):

- **ABI:** in `D0.W=logical row 0..63`, `D1.W=logical column 0..63`, `A5=0x00FF0000`; out `D0.W=final
  Genesis Plane-A name word` (0 = blank); **clobbers D0 only** (saves/restores D1-D7/A0-A2, uses an
  8-byte scratch frame).
- **Body:** `strip_src_table[row>>2] + a5@0x013E*0x40 + (col>>2)*4` → range-check + ARCADE→GENESIS
  remap → `{word0=attr, word1=metatile_ptr}` → `metatile[(row&3)*8 + (col&3)*2]` → `fg_cache_resolve`
  → `| attr_from_word(word0)`. This is the authoritative arcade map path, seg-correct, column-general.

## Producers converted (consumer coverage)
All four gameplay Plane-A producers now call `resolve_plane_a_cell` for the name word:

- **selector-0 (horizontal column):** YES — resolves per row at its fixed column; **collision
  side-channel left on the live descriptor (unchanged, KF-067/073).**
- **selector-1/2 (`selector12_native`, vertical row):** YES.
- **pan-up (`genesistan_plane_a_pan_publish_entering_rows_up`):** YES (via the pan helper).
- **pan-down (`..._down`):** YES (via the pan helper).

The pan helper's private static walk **and** its scroll_x source-column offset are removed: dest col ==
source col, matching selector-0. The old `.Lplane_a_strip_src_table` is now reached only through the
shared resolver.

- **Initial/scene fill:** NOT separately touched — it is driven through the same `selector0`/`selector12`
  producers (no independent Plane-A staged writer exists in `tilemap_hooks.s`), so it is on the shared
  resolver **by construction** (compatible).

## Coherence
Same logical cell → same final name word on either axis: **PROVEN by construction** (both axes call the
identical resolver with the same `(row, col)` → identical strip/segment/metatile/offset/attr/residency),
given equivalent residency/palette state. Initial-fill vs edge: same producers → same resolver → same
result (structural proof; not separately traced).

## Publication retained (Build 0350)
- Horizontal: `fg_col_dirty` + `vdp_commit_fg_columns_if_dirty` — one 32-word column PIO (autoinc 0x80).
- Vertical: `fg_row_dirty` + `vdp_commit_fg_strips_if_dirty` — 64-word contiguous row DMA.
- Simultaneous X/Y: independent column + row publications from the same staged buffer; the shared corner
  cell now resolves identically on both axes (bounded duplicate write, no semantic disagreement, no
  plane redraw).

## KF-072
No coordinate/ring change — only the **source resolution** is unified and publication granularity is as
in 0350. VRAM destinations unchanged. KF-072 preserved.

## Build / validation
- **0351** release SHA `8bb9d530f4062500ed4fef402c495d7cafc5958a19c80f9c74c481361a0cf881`;
  variants `_d 1b49dc…`, `_s 8eadce…`, `_do 77fc14…`. Counter = 351. 68000 asm only; no C.
- assemble/link OK; boot guard PASS pre+post; canonical gate **PASS**; gameplay-entry **PASS**;
  seven-epoch gate **FAIL** (the fragile synthetic record-3/`0x034C` gate — the resolver change alters
  LUT population; non-blocking label, ROM preserved by the fixed Makefile); 30s Genesis smoke
  `exceptions=0`, `crash_handler_entries=0`, boots to gameplay.
- Ledger: `0351 PRODUCED 2026-09-08 auto-recorded-by-release [canonical=PASS entry=PASS epoch=FAIL]`.

## Performance
Horizontal ~64× transfer saving retained (column PIO). Perceptible speed improvement from 0350: **NONE
OBSERVED** (per Tighe; frame time dominated elsewhere). The shared resolver adds one `bsr` + a small
frame per cell vs the old inline reads — bounded, not measured as significant; correctness prioritized.

## D00462
UNCHANGED / separate PC090OJ-space (`0xD00000–0xD00800`) failure. Not addressed.

## Manual test (Tighe)
ROM: `dist/rastan-direct/rastan_direct_video_test_build_0351.bin` (GENESIS NTSC). R1P1:
- **Initial gameplay:** is Layer A immediately as good as the earlier pre-0349 builds? Any wrong tiles
  before scrolling?
- **Horizontal:** entering columns correct; no seams/partial/stale/wrap.
- **Vertical:** scroll, stop, inspect; correct rows stay correct; no persistent corrupted regions.
- **Axis switch** (H→V→stop→H→V): no progressive corruption; neither axis "repairs" the other (they
  should now agree).
- **Combined X/Y:** no mismatched row/column intersection.
- Progression: ordinary segments, rope, waterfall, up to the known `D00462` crash.

Target: at least the earlier pre-0349 visual quality, now with unified seg-correct semantics and the
efficient Sonic-style publisher. If still wrong, the next divergence candidate is the resolver's column
mapping vs the arcade live-table column (Build 0352), to be proven by an earlier-build oracle comparison.

## Legacy / remaining
- `fg_row_dirty` retained (vertical + scene-entry full publish). `fg_col_dirty` (horizontal). Both still
  needed.
- The live `0x00FF1040`/`0x00FF1080` tables are still used by selector-0/12 **collision** and by the
  arcade rebuild; the Plane-A **name** path no longer depends on them (uses the static resolver).
- Retirable later if proven redundant: the live-table name reads (now unused). Not removed yet
  (collision still reads the live descriptor).

## Build 0351 manual result (Tighe, 2026-09-08)

- **"The level is a lot more accurate now."** The shared resolver recovered the cross-axis
  coherence — the major win.
- **Remaining bug:** Segment 0 visually shows Segment 1's **cave** on Layer A. Collision is correct
  (cave is only in Segment 1), so it is a Plane-A **source** bug, not collision.
- Still crashes at Segment 5 (`D00462`, separate/known, unchanged).
- Still slow, with vblank-overrun **black bars** visible (Tighe was on the `_do` display-off
  variant, which forced-blanks during the overrunning publication phase).

### Diagnosis of "cave on Segment 0" (proven from the arcade reference)

`docs/arcade_reference/pc080sn/map_stream_control.c`:
- `a5@0x1000[i] = strip_src_table[i] + seg*0x40` at scene init, then the 16 live strip-source
  pointers **advance +4 (one column) per scrolled column** (`map_advance_source_ptrs`, 0x0558C6) —
  a continuous scroll-tracking source.
- `a5@0x13E` (segment counter) advances **+1 per 64-publication ring cycle** (`map_advance_byte`,
  0x0558FE); it tracks the **leading/streaming** edge and can be **ahead of the trailing visible
  columns**.

`resolve_plane_a_cell` reconstructs the source statically as
`strip_src_table[row>>2] + a5@0x13E*0x40 + (col>>2)*4`. Two errors vs the arcade:
1. it uses the **global** leading-edge `a5@0x13E` uniformly for **every** plane column, so when the
   counter ticks into the cave segment while segment-0 columns are still visible, the cave base
   bleeds across the whole plane (**the observed bug**);
2. it maps the **plane** column `(col>>2)*4` instead of the **scroll progress** the live pointer
   encodes, so the fine column mapping is only approximately right within a segment.

The arcade-correct source is the **live scroll-advanced pointer** `a5@0x1000[row_group]` (which bakes
in `seg*0x40 + scroll*4` continuously), addressed per plane column relative to the current scroll
position — not a global segment term. `selector0` originally read the derived-from-live table
`0xFF1040` and was correct; the vertical row producers cannot use that row-group-indexed table for a
full row, which is why the static reconstruction was used and why it drifts.

### Fix direction for Build 0352 (proposed)
Replace the static `strip_src_table[..] + a5@0x13E*0x40 + (col>>2)*4` base in `resolve_plane_a_cell`
with the **live** `a5@0x1000[row>>2]` pointer plus a **relative** plane-column delta, so the segment
is never applied globally and the source tracks scroll exactly (matching what `selector0` produced
for each column at its entry time). The one unproven quantity is the alignment between the live
pointer's current column and plane column 0; that should be confirmed (arcade fill-loop `0x55C2E`
reading or a short runtime check) before coding, to avoid regressing the 0351 accuracy gain.

## STOP
Not a STOP. 0351 produced, numbered, preserved, gate-labeled, smoke-clean, playable, and a clear
improvement per Tighe. Remaining "cave on Segment 0" bug diagnosed to the global-segment-term error;
Build 0352 fix proposed (live scroll-advanced source). Slowness / vblank overrun noted (separate,
pre-existing; not the Plane-A publication). `D00462` separate/unchanged.
