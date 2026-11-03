# Andy — Stripe Root Cause Analysis, Build 0046

**Status:** ROOT CAUSE IDENTIFIED. Mechanism A confirmed.

---

## Phase 1 — Warm Restart / Repeated Init

### `init_staging_state` frequency

**Answer: B — once per warm restart cycle (once per frame).**

The arcade warm restart at `arcade_pc: 0x039F9E` jumps back to
`main_68k` (line 75 of `apps/rastan-direct/src/main_68k.s`). The
`main_68k` entry point unconditionally calls `init_staging_state`
(line 81) every time it is entered — whether from initial boot or
warm restart. Since warm restart fires every frame (confirmed in
`Andy_bg_blockcopy_hook_warm_restart_analysis.md`),
`init_staging_state` runs once per frame.

### Per-frame ordering

```
1. VBlank fires               — _VINT_handler (line 94)     — once per frame
     → vdp_commit_bg_strips_if_dirty (line 104) checks bg_row_dirty
     → bg_row_dirty == 0 (from prior warm restart) → SKIPS BG commit
2. Main loop detects VBlank   — .Lmain_loop (line 85)       — once per frame
3. arcade_tick_logic          — line 91 (bsr)               — once per frame
     → arcade code runs
     → c-window clear hook may fire: fills staging + sets bg_row_dirty=0xFFFFFFFF
     → BG strip hook fires: writes tiles to staged_bg_buffer + sets bg_row_dirty bits
     → warm restart fires: JMP main_68k
4. main_68k re-entered        — line 75                     — once per warm restart
5. vdp_boot_setup             — line 78                     — once per warm restart (redundant)
6. load_scene_tiles           — line 80                     — once per warm restart (loads tiles to VRAM)
7. init_staging_state         — line 81                     — once per warm restart
     → clears staged_bg_buffer to all zeros (lines 2069-2073)
     → clears bg_row_dirty to 0 (line 2054)
     → clears staged_fg_buffer, palette, tile staging
8. Interrupts re-enabled      — line 83
9. Goto step 1 (next VBlank)
```

### Warm restart overwrites valid staging data before VBlank commit

**YES.**

The BG strip hook writes valid tile data to `staged_bg_buffer` and sets
`bg_row_dirty` bits during step 3 (arcade tick). But step 7
(`init_staging_state`) clears BOTH the buffer AND the dirty flags. When
step 1 of the NEXT frame fires, `bg_row_dirty == 0` and the VBlank BG
commit SKIPS entirely. The hook's output never reaches VRAM Plane B.

This happens every frame — the warm restart always runs AFTER the
arcade tick and BEFORE the next VBlank.

---

## Phase 2 — Source-Side and Execution Coverage

These questions are **moot given the Phase 1 finding**. Even if the
source tiles, strip_index coverage, and `%d7` variation are all
perfectly correct, the staging buffer is cleared by `init_staging_state`
before VBlank can commit the data.

For completeness:

- **Source tile formula:** the BG strip hook reads 16 descriptors from
  `A5 + ARCADE_PC080SN_DESC_BG_LIST_OFFSET` (line 284), extracts tile
  index from ROM via `A1`-relative offset (lines 298–300), translates
  through `genesistan_pc080sn_tile_vram_lut` (lines 340–341).
- **Source data repetitive:** unknown without runtime trace — but
  irrelevant because the data is cleared before commit.
- **staged_bg_buffer after hook:** contains translated tile data at
  the correct destination positions — but is zeroed by warm restart
  before VBlank.
- **strip_index execution coverage:** strip_index (`%d7`) is read from
  `A5 + ARCADE_PC080SN_STRIP_INDEX_OFFSET` (line 218). Whether it
  cycles 0–3 across calls depends on the arcade code's strip scheduling.
  Irrelevant to the current failure.
- **%d7 variation:** unknown without trace — but irrelevant.

---

## Phase 3 — Commit Path / Plane Mismatch

- **`vdp_commit_bg_strips_if_dirty` writes to:** Plane B at
  `VRAM_PLANE_B_BASE = 0xC000` (line 1799: `move.l #VRAM_PLANE_B_BASE, %d0`).
- **VDP viewer stripe visible on:** Both planes may contribute; Plane B
  shows whatever emulator-default VRAM state was at 0xC000 (never
  overwritten because commits never fire).
- **Nametable address correct:** YES — `VRAM_PLANE_B_BASE = 0x0000C000`
  matches VDP register 4 setting (`0x8406` → Plane B at 0xC000).
- **`bg_row_dirty` set after hook write:** YES — the BG strip hook
  sets bits via `bset %d1, %d0` (line 353) / `move.l %d0, bg_row_dirty`
  (line 354). But these bits are cleared to 0 by `init_staging_state`
  (line 2054) before the next VBlank.
- **Commit stride correct:** YES — the commit function writes 64
  contiguous words per row (lines 1805–1808). No stride issue.

---

## Phase 4 — Mechanism Selection

**Selected: A — Warm restart causes `init_staging_state` to clear
staging buffers after valid hook writes, so VBlank always commits
cleared or default data.**

Evidence:

- `init_staging_state` at line 2041 is called from `main_68k` line 81.
- `main_68k` is re-entered on every warm restart from `arcade_pc:
  0x039F9E` (JMP to `main_68k`).
- `init_staging_state` line 2054: `clr.l bg_row_dirty` — clears all
  dirty bits.
- `init_staging_state` lines 2069–2073: `clr.w (%a0)+` × 2048 —
  zeros the entire `staged_bg_buffer`.
- Per-frame ordering: arcade tick (step 3) runs BG strip hooks which
  write valid data and set dirty bits → warm restart (step 4) jumps to
  `main_68k` → `init_staging_state` (step 7) clears buffer + dirty →
  VBlank (step 1 of next frame) sees `bg_row_dirty == 0` → SKIPS
  commit.
- Net result: BG strip hook output NEVER reaches VRAM Plane B.

Why other options are rejected:

- **B (source repetition):** source may or may not be repetitive, but
  it doesn't matter — the data is cleared before commit.
- **C (commit path blocked):** the commit PATH is correct; the issue is
  that `bg_row_dirty` is always 0 at VBlank time because warm restart
  cleared it.
- **D (plane mismatch):** the commit writes to the correct plane
  (Plane B at 0xC000); the issue is that it never fires.
- **E (partial strip execution):** strip execution coverage is
  irrelevant because even full coverage would be erased by init.

---

## Phase 5 — Final Answer

```
Stripe root cause: A
Mechanism: The arcade warm restart jumps back to main_68k every frame,
  causing init_staging_state to clear staged_bg_buffer and bg_row_dirty
  AFTER the BG strip hook writes valid data, and BEFORE VBlank can
  commit it — so the BG commit always sees dirty=0 and skips, leaving
  Plane B populated only with emulator-default VRAM content.
Evidence: init_staging_state line 2054 (clr.l bg_row_dirty) and lines
  2069-2073 (clear staged_bg_buffer). Called from main_68k line 81,
  which is re-entered on every warm restart. BG strip hook writes at
  lines 340-354 are erased before the next VBlank.
Fix direction: Split init_staging_state into a one-time boot init and
  a per-restart init. The per-restart path must NOT clear
  staged_bg_buffer, staged_fg_buffer, bg_row_dirty, or fg_row_dirty —
  those must persist across warm restarts so VBlank commits can transfer
  hook-written data to VRAM.
Additional capture needed: NO
```
