# Andy — init_staging_state Lifecycle Split Design

**Agent:** Andy
**Type:** Analysis + Design (no implementation)
**Build context:** Build 0046, `rastan-direct`
**Target file:** [apps/rastan-direct/src/main_68k.s](apps/rastan-direct/src/main_68k.s)

---

## 1. Summary

`init_staging_state` currently runs on every arcade warm restart
(`arcade_pc: 0x039F9E` → `JMP main_68k` at line 75). This clears
`staged_bg_buffer`, `staged_fg_buffer`, `bg_row_dirty`, and
`fg_row_dirty` *after* the arcade tick's strip hooks have written valid
tile data but *before* the next VBlank can commit that data to VRAM.
Root cause confirmed in
[Andy_stripe_root_cause_build0046.md](docs/design/Andy_stripe_root_cause_build0046.md).

This design splits `init_staging_state` into two functions:

- **`init_boot_state`** — runs once at cold boot only. Initializes all
  staging buffers, dirty flags, Plane A VRAM, scroll state, and arcade
  workram factory defaults.
- **`init_restart_state`** — runs on every warm restart. Initializes
  only the arcade-side state that arcade `startup_common` is expected to
  reset per restart (workram factory defaults, dest pointers, frame
  counters). Does **not** touch staging buffers, dirty flags, Plane A
  VRAM, staging palettes/tiles, or staging scroll values.

A one-byte BSS latch `boot_initialized` distinguishes cold boot from
warm restart at the `main_68k` entry point. `vdp_boot_setup` and the
initial `load_scene_tiles` call are moved into the cold-boot-only
branch; scene-transition calls to `load_scene_tiles` from hooks are
unchanged.

---

## 2. Exact Files Modified

- [apps/rastan-direct/src/main_68k.s](apps/rastan-direct/src/main_68k.s) — entry dispatch, new functions, removal of `init_staging_state`, BSS latch declaration.

No other files require changes. All edits remain within one source file.

---

## 3. Exact Symbols / Functions / Labels Added or Changed

| Kind         | Symbol / Label              | Action    |
| ------------ | --------------------------- | --------- |
| Function     | `init_staging_state`        | REMOVED   |
| Function     | `init_boot_state`           | ADDED     |
| Function     | `init_restart_state`        | ADDED     |
| BSS byte     | `boot_initialized`          | ADDED     |
| Local label  | `.Lwarm_restart`            | ADDED (inside `main_68k`) |
| Local label  | `.Lenter_main_loop`         | ADDED (inside `main_68k`) |
| Call site    | `bsr vdp_boot_setup`        | MOVED (into cold-boot branch only) |
| Call site    | `bsr load_scene_tiles` (startup) | MOVED (into cold-boot branch only) |
| Call site    | `bsr init_staging_state`    | REMOVED   |

No changes to:

- `_VINT_handler`
- `arcade_tick_logic`
- `load_scene_tiles` itself (only its startup call site moves)
- `vdp_boot_setup` itself (only its call site moves)
- Any hook function (`genesistan_hook_*`)
- Any `.global` declaration
- Any `.equ` constant
- Any `.rodata` table
- Any other BSS layout (only one byte appended)

---

## 4. Permanent vs Temporary Classification

| Item                         | Classification |
| ---------------------------- | -------------- |
| `init_boot_state`            | PERMANENT      |
| `init_restart_state`         | PERMANENT      |
| `boot_initialized` BSS byte  | PERMANENT      |
| Warm-restart dispatch branch | PERMANENT      |

Nothing in this change is scaffolding, diagnostic, or bring-up-only.
The split is the permanent architectural correction to the
arcade-warm-restart / VBlank-commit interaction.

---

## 5. Scaffolding Inventory

None introduced. No NOPs, no RTS bypasses, no shadow RAM, no
fallbacks, no diagnostic counters.

---

## 6. Removal / Revert Plan

Not applicable — all added items are permanent architectural
corrections. No removal plan is needed. If the split is ever reverted,
the original `init_staging_state` can be restored by merging the two
new functions and restoring the single call from `main_68k`.

---

## 7. Build Artifact Path

N/A — design task only. No build produced.

---

## 8. Verification Status

N/A — design only. Cody will implement and verify in a follow-up task.

---

## 9. Risks / Known Limitations

See Phase 5 (section 14) for per-field risk analysis. All risks are
judged **Acceptable** and mitigated by either:

- Boot-time initialization guaranteeing known starting state, or
- Commit-loop bit clearing (`bclr %d5, %d0` in
  [main_68k.s:1814](apps/rastan-direct/src/main_68k.s#L1814)) which
  self-clears dirty bits after each commit.

Two prerequisites Cody must verify before implementing:

1. `boot.s` zero-initializes BSS (so `boot_initialized` is 0 at cold
   boot). If BSS is not zero-initialized, Cody must add an explicit
   `clr.b boot_initialized` at the earliest point in the cold-boot
   path before `main_68k` is entered, or equivalently set it from
   boot.s.
2. `boot_initialized` is placed in BSS (address ≥ `0xFF4000`), which
   is **not** overwritten by the arcade workram factory-defaults loop
   that zeroes `0xFF0000..0xFF00FF`. So its value survives across warm
   restarts.

---

# Design Phases

## Phase 1 — Field classification (audit of init_staging_state, lines 2041–2169)

| Field                         | Line(s)     | Current action                             | Classification | Justification |
| ----------------------------- | ----------- | ------------------------------------------ | -------------- | ------------- |
| `frame_counter`               | 2043        | `clr.w`                                    | RESTART-SAFE   | VBlank handshake pacer; main loop re-reads fresh each iteration. Clearing mid-loop only costs one wait-cycle, no state corruption. |
| `tick_counter`                | 2044        | `clr.w`                                    | RESTART-SAFE   | Currently unreferenced elsewhere in `main_68k.s`. Clearing has no effect. |
| `staged_dest_ptr_bg`          | 2046        | `move.l #0x00C00000`                       | RESTART-SAFE   | Currently unused by any reader in `main_68k.s` (hooks read `ARCADE_PC080SN_DEST_BG_OFFSET(%a5)` instead). Inert either way; matches arcade's own per-restart state reset. |
| `staged_dest_ptr_fg`          | 2047        | `move.l #0x00C08000`                       | RESTART-SAFE   | Same as `staged_dest_ptr_bg`. |
| `ARCADE_FIX_DEST_BG` (`0xFF10A0`) | 2049    | `move.l #0x00C00000`                       | RESTART-SAFE   | This is arcade-side dest pointer (A5@0x10A0). Arcade `startup_common` resets this per warm restart; mirroring that behavior keeps arcade state causality intact. |
| `ARCADE_FIX_DEST_FG` (`0xFF10A4`) | 2050    | `move.l #0x00C08000`                       | RESTART-SAFE   | Same as `ARCADE_FIX_DEST_BG`. |
| `palette_dirty`               | 2052        | `clr.b`                                    | BOOT-ONLY      | Gates VBlank palette commit. Future palette hooks will set this during arcade tick; clearing per-restart would erase the pending commit signal. |
| `tiles_dirty`                 | 2053        | `clr.b`                                    | BOOT-ONLY      | Gates VBlank tile DMA commit. Same reasoning as `palette_dirty`. |
| `bg_row_dirty`                | 2054        | `clr.l`                                    | BOOT-ONLY      | **Confirmed root cause.** BG strip hook sets bits during arcade tick; warm-restart clear erases them before VBlank can commit. |
| `fg_row_dirty`                | 2055        | `clr.l`                                    | BOOT-ONLY      | By symmetry with `bg_row_dirty`; FG strip/text hooks set bits during tick. |
| `staged_palette_words` (64 words) | 2057-2061 | 64-word `clr.w` loop                    | BOOT-ONLY      | If a future palette hook writes partial palette during tick, per-restart clear would zero it before VBlank can DMA to CRAM. |
| `staged_tile_words` (48 words) | 2063-2067  | 48-word `clr.w` loop                       | BOOT-ONLY      | Same reasoning as `staged_palette_words` for tile DMA. |
| `staged_bg_buffer` (2048 words) | 2069-2073 | 2048-word `clr.w` loop                    | BOOT-ONLY      | **Confirmed root cause.** Contains hook-written BG tile data that must survive to VBlank. |
| `staged_fg_buffer` (2048 words) | 2075-2079 | 2048-word `clr.w` loop                    | BOOT-ONLY      | By symmetry with `staged_bg_buffer`; contains hook-written FG/text data. |
| Plane A VRAM direct clear (2048 words at `VRAM_PLANE_A_BASE`) | 2081-2086 | VDP write address + 2048-word `move.w #0` loop | BOOT-ONLY | Committed FG content lives in Plane A VRAM. Re-clearing per-restart would erase the VBlank commit from the previous frame before any hooks run in the next. |
| `staged_scroll_x_bg`          | 2088        | `clr.w`                                    | BOOT-ONLY      | Read every VBlank by `vdp_commit_scroll`. Future scroll hooks will set this during arcade tick; per-restart clear would zero pending scroll before commit. |
| `staged_scroll_x_fg`          | 2089        | `clr.w`                                    | BOOT-ONLY      | Same as `staged_scroll_x_bg`. |
| `staged_scroll_y_bg`          | 2090        | `clr.w`                                    | BOOT-ONLY      | Same as `staged_scroll_x_bg`. |
| `staged_scroll_y_fg`          | 2091        | `clr.w`                                    | BOOT-ONLY      | Same as `staged_scroll_x_bg`. |
| Arcade workram zero (`0xFF0000..0xFF00FF`) | 2100-2104 | 64-longword `clr.l` loop         | RESTART-SAFE   | Arcade `startup_common` equivalent; arcade logic expects this block wiped every warm restart. Documented in comment at line 2096. |
| Coinage defaults (coin1/coin2/x3/x4) | 2110-2113 | `move.w #1, A5@(8/10/14/16)`         | RESTART-SAFE   | Arcade `startup_common` factory default; arcade code expects these reset per restart. |
| Display control mirror `A5@(20)` | 2116     | `move.w #0x0060`                           | RESTART-SAFE   | Same rationale. |
| DIP mirrors `A5@(24)`, `A5@(28)` | 2119-2120 | `move.w #0x0001`, `#0x0000`               | RESTART-SAFE   | Same rationale. |
| Init flag `A5@(38)`           | 2123        | `move.w #1`                                | RESTART-SAFE   | Same rationale. |
| Delay countdown `A5@(44)`     | 2126        | `move.w #160`                              | RESTART-SAFE   | `startup_common` default: arcade expects fresh countdown per restart. |
| Mode/cab/mon `A5@(46/48/50)`  | 2129-2131   | `move.w #0`, `#1`, `#0`                    | RESTART-SAFE   | Derived from DIP defaults; reset per restart. |
| Bonus/diff `A5@(54/56)`       | 2134-2135   | `move.w #6`, `#0x2500`                     | RESTART-SAFE   | Same rationale. |
| Sprite init marker `A5@(74)`  | 2138        | `move.w #0x00AA`                           | RESTART-SAFE   | Same rationale. |
| Block A seeding `A5+0x80/B2/97/98` | 2141-2144 | various moves                          | RESTART-SAFE   | Equivalent of arcade `0x03A9E6` init helper. |
| Block A → Block B copy (16 longwords) | 2147-2152 | `move.l (%a1)+, (%a2)+` loop       | RESTART-SAFE   | Arcade per-restart transition buffer seeding. |
| Title init flag `A5@(256)`    | 2158        | `move.w #1`                                | RESTART-SAFE   | Arcade expectation. |
| Config table copy (39 bytes from ROM `0x3B2D4` to `A5@(320)`) | 2162-2167 | `move.b (%a1)+, (%a2)+` loop | RESTART-SAFE | Arcade `startup_common` config reload; must run every warm restart. |

### Counts

- **BOOT-ONLY:** 13 fields/operations.
- **RESTART-SAFE:** 20 fields/operations (frame_counter, tick_counter, two dest pointer pairs, two ARCADE_FIX pointers, arcade workram block + all factory defaults).

All fields classified. No field required runtime trace data.

---

## Phase 2 — Function split

### `init_boot_state`

**Purpose:** one-time cold-boot initialization. Establishes every field
init_staging_state touches, in the same order, with the same values.

**Fields initialized (all BOOT-ONLY + all RESTART-SAFE):**

- `frame_counter = 0`
- `tick_counter = 0`
- `staged_dest_ptr_bg = 0x00C00000`
- `staged_dest_ptr_fg = 0x00C08000`
- `ARCADE_FIX_DEST_BG (0xFF10A0) = 0x00C00000`
- `ARCADE_FIX_DEST_FG (0xFF10A4) = 0x00C08000`
- `palette_dirty = 0`
- `tiles_dirty = 0`
- `bg_row_dirty = 0`
- `fg_row_dirty = 0`
- `staged_palette_words[0..63] = 0`
- `staged_tile_words[0..47] = 0`
- `staged_bg_buffer[0..2047] = 0`
- `staged_fg_buffer[0..2047] = 0`
- Plane A VRAM `0xE000..` (2048 words) = `0x0000` via direct VDP write
- `staged_scroll_x_bg = 0`, `staged_scroll_x_fg = 0`
- `staged_scroll_y_bg = 0`, `staged_scroll_y_fg = 0`
- Arcade workram zero (`0xFF0000..0xFF00FF`)
- All arcade factory defaults (coinage, DIP mirrors, init flag, delay,
  mode/cab/mon, bonus/diff, sprite marker, block A/B seeding, title
  init flag, config table copy)

**Call site:** one call from `main_68k`, inside the cold-boot branch only.

### `init_restart_state`

**Purpose:** per-warm-restart initialization. Mirrors arcade
`startup_common` behavior — refreshes the arcade-side state arcade code
expects to be factory-fresh on every warm restart, without disturbing
Genesis-side staging pipelines.

**Fields initialized (RESTART-SAFE only):**

- `frame_counter = 0`
- `tick_counter = 0`
- `staged_dest_ptr_bg = 0x00C00000`
- `staged_dest_ptr_fg = 0x00C08000`
- `ARCADE_FIX_DEST_BG (0xFF10A0) = 0x00C00000`
- `ARCADE_FIX_DEST_FG (0xFF10A4) = 0x00C08000`
- Arcade workram zero (`0xFF0000..0xFF00FF`)
- All arcade factory defaults (coinage, DIP mirrors, init flag, delay,
  mode/cab/mon, bonus/diff, sprite marker, block A/B seeding, title
  init flag, config table copy)

**Explicitly NOT touched:**

- `palette_dirty`
- `tiles_dirty`
- `bg_row_dirty`
- `fg_row_dirty`
- `staged_palette_words`
- `staged_tile_words`
- `staged_bg_buffer`
- `staged_fg_buffer`
- Plane A VRAM
- `staged_scroll_x_bg/fg`, `staged_scroll_y_bg/fg`

**Call site:** one call from `main_68k`, inside the warm-restart branch only.

---

## Phase 3 — Call sites

### Current `main_68k` (lines 75–83)

| Line | Current                       |
| ---- | ----------------------------- |
| 76   | `move.w #0x2700, %sr`         |
| 78   | `bsr vdp_boot_setup`          |
| 79   | `moveq #0, %d0`               |
| 80   | `bsr load_scene_tiles`        |
| 81   | `bsr init_staging_state`      |
| 83   | `move.w #0x2000, %sr`         |

### Changes

| Line (old) | Current                       | Replace with                                          | Justification |
| ---------- | ----------------------------- | ----------------------------------------------------- | ------------- |
| 76         | `move.w #0x2700, %sr`         | unchanged                                             | Disable interrupts for all init. |
| (new)      | —                             | `tst.b boot_initialized`<br>`bne.s .Lwarm_restart`    | Cold-boot / warm-restart dispatch. |
| 78         | `bsr vdp_boot_setup`          | unchanged, but only reachable on cold-boot branch     | VDP registers persist across frames; redundant on warm restart. |
| 79         | `moveq #0, %d0`               | unchanged, but only reachable on cold-boot branch     | Sets scene id = 0 (title) for `load_scene_tiles`. |
| 80         | `bsr load_scene_tiles`        | unchanged, but only reachable on cold-boot branch     | Tile data persists in VRAM across frames; scene-transition calls from hooks remain unchanged. |
| 81         | `bsr init_staging_state`      | `bsr init_boot_state`                                 | Boot-only full init (replaces old call). |
| (new)      | —                             | `move.b #1, boot_initialized`<br>`bra.s .Lenter_main_loop` | Latch the flag, skip warm-restart branch. |
| (new)      | —                             | `.Lwarm_restart:`<br>`bsr init_restart_state`         | Warm-restart-only subset init. |
| (new)      | —                             | `.Lenter_main_loop:`                                  | Converges both branches to the shared main-loop enable. |
| 83         | `move.w #0x2000, %sr`         | unchanged                                             | Re-enable interrupts; main loop starts. |

### Decisions requested by the prompt

- **`vdp_boot_setup`:** **cold boot only.** VDP registers are
  hardware-persistent; redundant on warm restart. Called immediately
  before `init_boot_state` on the cold-boot branch.
- **`load_scene_tiles`:** **cold boot only** for the startup call.
  Tile data persists in VRAM across frames. Scene-transition calls
  issued from inside `genesistan_hook_tilemap_plane_a` (line 282) and
  `genesistan_hook_tilemap_fg` (line 454) are unchanged — those fire
  only on arcade-driven scene transitions (detected via
  `genesistan_scene_a0_ranges` match), which is the correct trigger.

---

## Phase 4 — Corrected per-frame flow (post-fix)

```
1. VBlank fires → _VINT_handler
     → vdp_commit_bg_strips_if_dirty: bg_row_dirty != 0 (hook-set last
       tick), commits each dirty row to Plane B VRAM, bclr self-clears
       each row bit after its commit.
     → vdp_commit_fg_strips_if_dirty: same for fg_row_dirty / Plane A.
     → palette_dirty test: if set, commit staged_palette_words to
       CRAM; clr.b palette_dirty.
     → vdp_commit_scroll: writes staged_scroll_* to VDP every frame.
     → frame_counter += 1
     → rte

2. Main loop sees frame_counter changed → exits .Lwait_vblank

3. arcade_tick_logic runs
     → rastan_direct_update_inputs populates input shadows
     → jmp rastan_direct_arcade_tick_entry (0x0003A208)
     → arcade code executes; hooks fire as pc080sn writes occur:
         - cwindow clear hook fills staged_bg/fg_buffer with space
           tile + sets bg_row_dirty = fg_row_dirty = 0xFFFFFFFF
         - BG/FG strip hooks translate tile/attr descriptors, write
           genesis-format words into staged_bg/fg_buffer at the correct
           row/col, set the appropriate bits in bg_row_dirty /
           fg_row_dirty.
         - text writer hooks do the same for FG.
     → arcade reaches warm-restart trampoline at 0x039F9E:
           MOVEA.L (0x0000).W, SP   ; SP = 0xFF0000
           MOVEA.L (0x0004).W, A0   ; A0 = main_68k (0x00000202)
           JMP (A0)

4. main_68k re-entered (warm restart)
     → move.w #0x2700, %sr  (interrupts off)
     → tst.b boot_initialized: non-zero → branch .Lwarm_restart
     → bsr init_restart_state
         - clr.w frame_counter, clr.w tick_counter
         - reload staged_dest_ptr_bg/fg, ARCADE_FIX_DEST_BG/FG
         - zero arcade workram 0xFF0000..0xFF00FF
         - reload all arcade factory defaults (coin, DIP, mode, bonus,
           diff, title flag, config table copy)
     → PRESERVES staged_bg_buffer, staged_fg_buffer, bg_row_dirty,
       fg_row_dirty, palette_dirty, tiles_dirty, staged_palette_words,
       staged_tile_words, Plane A VRAM, staged_scroll_*
     → move.w #0x2000, %sr (interrupts on)

5. main loop re-enters .Lmain_loop
     → reads frame_counter (= 0), spins in .Lwait_vblank

6. Next VBlank fires → GOTO step 1
     → bg_row_dirty still reflects hook writes from step 3 → BG commit
       fires and writes hook-authored rows to Plane B VRAM.
     → fg_row_dirty likewise commits FG rows to Plane A VRAM.
     → staged BG/FG data reaches VRAM.
```

Confirmation:

- `staged_bg_buffer` and `bg_row_dirty` survive from arcade tick
  (step 3) through VBlank commit (step 6 / step 1 of next frame). ✓
- VBlank sees non-zero dirty bits and commits BG data to Plane B. ✓
- No redundant VDP or tile init runs on warm restart. ✓

---

## Phase 5 — Risk assessment

| Field / operation moved to boot-only | Risk if not reset per-restart | Mitigation | Acceptable |
| -------------------------------------- | ----------------------------- | ---------- | ---------- |
| `palette_dirty`                        | Stuck-at-1 bit would cause spurious palette commits every VBlank. | `_VINT_handler` clears it after each commit (line 110). Boot init guarantees clean start state. | YES |
| `tiles_dirty`                          | Stuck-at-1 would cause spurious tile DMA every VBlank. | `vdp_commit_tiles_if_dirty` clears it after commit (line 1785). | YES |
| `bg_row_dirty`                         | Stuck row bit would recommit a stale staged row. | Commit loop `bclr %d5, %d0` self-clears each row bit after its VRAM write (main_68k.s:1814). Bits only get set by hooks, and only for rows they actually write. | YES |
| `fg_row_dirty`                         | Same as `bg_row_dirty`. | Same mitigation. | YES |
| `staged_palette_words` (64 words)      | Stale data from prior frame if only partial update. | No current palette hook; boot-init zero guarantees defined start state. Future palette hook must either write full 64 words or manage per-entry validity — flag for future hook design. | YES |
| `staged_tile_words` (48 words)         | Stale data if only partial update. | Same as `staged_palette_words`; no current tile-staging hook. | YES |
| `staged_bg_buffer` (2048 words)        | Rows not rewritten by hooks this frame retain prior-frame data. | Commit only writes DIRTY rows to VRAM. Non-dirty rows in the buffer are never committed; "stale" buffer contents cannot reach VRAM. `cwindow_clear` hook (main_68k.s:1740) explicitly fills the buffer with space tiles and marks all rows dirty when arcade clears the C-window. This is the intended design. | YES |
| `staged_fg_buffer` (2048 words)        | Same as `staged_bg_buffer`. | Same mitigation. | YES |
| Plane A VRAM direct clear              | Plane A content from prior frame persists until first commit. | Boot-time clear guarantees clean Plane A at cold boot. In-frame hooks (`cwindow_clear`, text writer sentinel blank-tile) handle per-tick clearing as part of arcade-intent translation. VBlank commit overwrites hook-dirtied rows. | YES |
| `staged_scroll_x_bg/fg`, `staged_scroll_y_bg/fg` | Stale scroll values persist. | `vdp_commit_scroll` writes them every VBlank. No current scroll hook; boot-init zero establishes known start. Future scroll hooks will set per tick. | YES |

All risks are **Acceptable**. No BOOT-ONLY field requires alternative
handling.

---

## Phase 6 — Final implementation-ready specification

### New BSS symbol

Add to `.bss` section (between existing BSS entries, `.align 2`
preserved):

```
boot_initialized:
    .byte 0
    .align 2
```

**Prerequisite check:** Cody must verify that `apps/rastan-direct/src/boot/boot.s`
zero-initializes BSS. If it does not, Cody must either (a) add a BSS
zero-init loop to `boot.s`, or (b) add an explicit `clr.b
boot_initialized` at the first instruction of `main_68k` prior to the
`tst.b` dispatch. Option (a) is preferred; option (b) is the safe
fallback.

### New `main_68k` entry dispatch (replaces current lines 75–83)

```
main_68k:
    move.w  #0x2700, %sr

    tst.b   boot_initialized
    bne.s   .Lwarm_restart

    bsr     vdp_boot_setup
    moveq   #0, %d0
    bsr     load_scene_tiles
    bsr     init_boot_state
    move.b  #1, boot_initialized
    bra.s   .Lenter_main_loop

.Lwarm_restart:
    bsr     init_restart_state

.Lenter_main_loop:
    move.w  #0x2000, %sr
```

The existing `.Lmain_loop` / `.Lwait_vblank` / `bsr arcade_tick_logic`
/ `bra.s .Lmain_loop` block (current lines 85–92) is unchanged and
immediately follows `.Lenter_main_loop`.

### New `init_boot_state`

Same body as current `init_staging_state` (main_68k.s:2041–2169), with
the label renamed. Function body is byte-identical to the current
implementation.

### New `init_restart_state`

```
init_restart_state:
    lea     0x00FF0000, %a5
    clr.w   frame_counter
    clr.w   tick_counter

    move.l  #0x00C00000, staged_dest_ptr_bg
    move.l  #0x00C08000, staged_dest_ptr_fg

    move.l  #0x00C00000, ARCADE_FIX_DEST_BG
    move.l  #0x00C08000, ARCADE_FIX_DEST_FG

    /* ------------------------------------------------------------------ */
    /* Arcade workram factory defaults at 0xFF0000                         */
    /* Equivalent to startup_common / genesistan_init_workram_direct       */
    /* ------------------------------------------------------------------ */

    lea     0x00FF0000, %a0
    moveq   #(64-1), %d7
.Lrs_arcade_wram_clear:
    clr.l   (%a0)+
    dbra    %d7, .Lrs_arcade_wram_clear

    lea     0x00FF0000, %a0

    move.w  #1,      0x0008(%a0)
    move.w  #1,      0x000A(%a0)
    move.w  #1,      0x000E(%a0)
    move.w  #1,      0x0010(%a0)

    move.w  #0x0060, 0x0014(%a0)

    move.w  #0x0001, 0x0018(%a0)
    move.w  #0x0000, 0x001C(%a0)

    move.w  #1,      0x0026(%a0)
    move.w  #160,    0x002C(%a0)
    move.w  #0,      0x002E(%a0)
    move.w  #1,      0x0030(%a0)
    move.w  #0,      0x0032(%a0)
    move.w  #6,      0x0036(%a0)
    move.w  #0x2500, 0x0038(%a0)
    move.w  #0x00AA, 0x004A(%a0)

    move.w  0x0036(%a0), 0x0080(%a0)
    move.w  0x0038(%a0), 0x00B2(%a0)
    move.b  #1, 0x0097(%a0)
    move.b  #1, 0x0098(%a0)

    lea     0x0080(%a0), %a1
    lea     0x00C0(%a0), %a2
    moveq   #(16-1), %d7
.Lrs_block_b_copy:
    move.l  (%a1)+, (%a2)+
    dbra    %d7, .Lrs_block_b_copy

    lea     0x00FF0000, %a0

    move.w  #1,      0x0100(%a0)

    lea     0x0003B2D4, %a1
    lea     0x0140(%a0), %a2
    moveq   #(39-1), %d7
.Lrs_arcade_cfg_copy:
    move.b  (%a1)+, (%a2)+
    dbra    %d7, .Lrs_arcade_cfg_copy

    rts
```

**Does NOT touch:**
- `palette_dirty`, `tiles_dirty`
- `bg_row_dirty`, `fg_row_dirty`
- `staged_palette_words`, `staged_tile_words`
- `staged_bg_buffer`, `staged_fg_buffer`
- Plane A VRAM
- `staged_scroll_x_bg`, `staged_scroll_x_fg`, `staged_scroll_y_bg`, `staged_scroll_y_fg`

### Removed

- Function `init_staging_state` (current lines 2041–2169) is removed.
  Its body splits into:
  - `init_boot_state` — byte-identical full body.
  - `init_restart_state` — only the RESTART-SAFE subset listed above.
- The single `bsr init_staging_state` at old line 81 is removed. The
  two replacement `bsr init_boot_state` / `bsr init_restart_state`
  calls live inside the new dispatch.

### Call-site summary

| Function            | Call on                 | Call site(s)                                        |
| ------------------- | ----------------------- | --------------------------------------------------- |
| `vdp_boot_setup`    | cold boot only          | `main_68k`, cold-boot branch (replaces old line 78) |
| `load_scene_tiles`  | cold boot only (startup) | `main_68k`, cold-boot branch (replaces old line 80); scene-transition calls at `main_68k.s:282` and `main_68k.s:454` unchanged. |
| `init_boot_state`   | cold boot only          | `main_68k`, cold-boot branch (replaces old line 81) |
| `init_restart_state`| every warm restart      | `main_68k`, `.Lwarm_restart` branch                 |

---

## STOP conditions

None triggered. All fields were classifiable without runtime trace
data. The split does not require changes beyond `main_68k.s` (one file,
one new BSS byte, one new entry dispatch, one function split).

---

## Ready-for-Cody checklist

- All fields classified: YES
- BOOT-ONLY fields count: 13
- RESTART-SAFE fields count: 20
- `init_boot_state` defined: YES
- `init_restart_state` defined: YES
- `vdp_boot_setup` call site resolved: YES (cold boot only)
- `load_scene_tiles` call site resolved: YES (cold boot only for
  startup; scene-transition calls unchanged)
- Risk assessment complete: YES
- Ready for Cody implementation: YES
