# Andy — Build 0350: Native 68000 Sonic-Style Plane A Horizontal Column Publisher

**Per-build record.** Full architecture/design: [Andy_sonic1_native_68000_plane_a_streaming.md](Andy_sonic1_native_68000_plane_a_streaming.md).

- **Build:** 0350 (release) · SHA-256 `24e2f9bdb90c7f395988963fa709388a53573f5141e5a067dd4e2158f95f437d` · 1666744 bytes.
- **Variants (share the number, gate-free):** `_d` `702732…`, `_s` `d16d46…`, `_do` `ad1d4c…`.
- **Language:** 68000 assembly only. No C. No new C files.
- **ROM to test:** `dist/rastan-direct/rastan_direct_video_test_build_0350.bin` (GENESIS NTSC).

## Change
Native Sonic-style (`DrawBlocks_TB`) Plane-A **column publisher**. `selector0_native` (horizontal
entering-column producer) now flags one `fg_col_dirty` bit for the entering logical column instead
of 32 `fg_row_dirty` bits. New VBlank routine `vdp_commit_fg_columns_if_dirty` sets VDP
autoincrement = plane row stride (`0x80`), addresses `0xE000 + col*2`, and PIO-streams 32 name words
down the column from `staged_fg_buffer`, then restores autoinc = 2. Vertical (selector-1/2, pan
rows) unchanged.

- **Transfer:** one horizontal crossing drops from up to **2048** words (32 row DMAs) to **32**
  words (one column) — ~64×.
- **KF-072:** publication-granularity change only; VRAM destination byte-identical to the row-DMA
  path; no coordinate/ring change.
- **Files:** `apps/rastan-direct/src/tilemap_hooks.s` only (producer, writer, BSS `fg_col_dirty`).

## Validation
- assemble/link OK; boot guard PASS (pre+post); canonical gate PASS; gameplay-entry gate PASS;
  seven-epoch gate PASS; 30s Genesis smoke `exceptions=0`, `crash_handler_entries=0`, 564 frames.
- Ledger: `0350 PRODUCED 2026-09-08 auto-recorded-by-release [canonical=PASS entry=PASS epoch=PASS]`.

## Known limitations (honest)
- Does **not** fix 0349's "horizontal partially wrong" — that is a **source-coherence** issue
  (horizontal uses live `PTR[seg]`, vertical uses the static strip table). Build 0350 changes
  publication, not source resolution, so visual correctness ≈ 0349 with far less DMA.
- Coherence fix = Build 0351 (unify vertical onto the live `PTR[seg]` resolver).
- `D00462` PC090OJ-space freeze is separate/known, not addressed here.

## Status
Produced, numbered, preserved, gate-clean, smoke-clean, playable. Awaiting Tighe's R1P1 play result.
