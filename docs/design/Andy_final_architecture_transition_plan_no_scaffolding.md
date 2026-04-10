# Andy — Final Architecture Transition Plan (No Scaffolding)

**Date:** 2026-04-08
**Project:** apps/rastan-direct
**Purpose:** Ordered transition from current bringup state to final ownership model with no persistent scaffolding.

---

## 1. Summary

The `apps/rastan-direct` project has a working video baseline: the PC080SN BG hook fires, the staged BG buffer is committed to VDP Plane B during VBlank, scroll and palette commits are gated by dirty flags, and the arcade tick runs inside the main loop. The build is stable enough to make disciplined architectural transitions.

Five categories of work separate current state from the final ownership model:

1. **Scaffolding display state** — `init_staging_state` synthesizes a checkerboard in `staged_bg_buffer` and writes diagnostic tile data. These are bringup artifacts, not arcade-sourced content.
2. **0xDFFFFE crash** — the arcade code issues a write to an open-bus D-range address. The address is dynamically computed; no simple `opcode_replace` at a fixed PC is possible. A Genesis address-window sink is required.
3. **VBlank commit granularity** — the VBlank handler commits full 2048-word planes when only per-strip (64-word) granularity is correct for the final port.
4. **Wrapper-owned workram initialization** — `init_staging_state` seeds `ARCADE_FIX_DEST_BG`, `ARCADE_FIX_DEST_FG`, frame and tick counters, and staging buffers. The arcade init path at `0x03AF04` covers workram and some of these fields if called directly.
5. **Hook ownership** — `genesistan_hook_tilemap_plane_a` is permanently correct. Its single bring-up artifact is the always-dirty `move.b #1, bg_dirty` that fires on every hook invocation, which should be replaced with per-strip dirty-bit tracking.

This document catalogs every current item in `main_68k.s` and `boot.s`, proposes the exact 0xDFFFFE suppression mechanism, defines the final VBlank model, specifies the arcade init restoration path, confirms hook ownership, and produces a dependency-ordered removal sequence.

---

## 2. Exact Files Analyzed

| File | Lines Read | Notes |
|------|-----------|-------|
| `apps/rastan-direct/src/main_68k.s` | 1–611 | Complete read — wrapper implementation, hooks, init, staging buffers |
| `apps/rastan-direct/src/boot/boot.s` | 1–55 | Complete read — exception vector table, TMSS, entry point |
| `apps/rastan-direct/link.ld` | 1–27 | Complete read — segment layout |
| `specs/rastan_direct_remap.json` | 1–306 | Complete read — 34 `opcode_replace` entries, window declarations, ROM copy policy |
| `build/maincpu.disasm.txt` | 1–300 (initial), targeted grep | Overview pass + D-range write census |
| `docs/design/Andy_dffffe_hardware_identification.md` | Complete | Prior 0xDFFFFE crash analysis |
| `docs/design/Andy_diagnostic_debt_audit.md` | Complete | Diagnostic debt inventory (applies to `apps/rastan`, not `apps/rastan-direct`) |
| `docs/design/Andy_vblank_efficiency_audit_and_transition_plan.md` | Complete | VBlank cycle costs, strip-level transition plan |
| `docs/design/arcade_init_vs_launcher_fake_init_audit.md` | Complete | Arcade `startup_common` sequence vs launcher fake init |
| `docs/design/Andy_pc0900j_sprite_correctness_audit.md` | Lines 1–80 | PC090OJ sprite format and D-range write site census |

---

## 3. Current Scaffolding Inventory

### Classification Legend

- **PERMANENT** — minimum adapter layer; must survive in final build
- **TEMPORARY** — bring-up only; must be removed once arcade path covers the responsibility
- **BRINGUP_ONLY** — simplified path valid only during bring-up; structurally wrong for final port
- **DIAGNOSTIC** — instrumentation or debug output; must be removed before final build

---

### boot.s Items

#### PERMANENT: Exception vector table

**Symbol/label:** `.org 0x000000` vector block, `_VINT_handler` slot at position 0x1E (offset 0x78 × 4)
**File:** `apps/rastan-direct/src/boot/boot.s`, lines 9–19
**Purpose:** Hardwired Genesis exception vector table. The VBlank entry points to `_VINT_handler` in `main_68k.s`. The default handler is a bare `rte`. The SP initial value (0x00FF0000) and reset vector (`_start`) are the first two entries.
**Status: PERMANENT.** The VBlank vector must point to the Genesis wrapper VBlank handler for the lifetime of the port. The default `rte` fallback for all other exceptions is correct.

#### PERMANENT: TMSS handshake

**Symbol/label:** `.Ltmss_done` block in `_start`
**File:** `apps/rastan-direct/src/boot/boot.s`, lines 45–49
**Purpose:** Reads hardware version register and conditionally writes `"SEGA"` to the TMSS register. Required for boot on real hardware and in BlastEm.
**Status: PERMANENT.**

#### PERMANENT: ROM header

**Symbol/label:** `.org 0x000100` header block
**File:** `apps/rastan-direct/src/boot/boot.s`, lines 21–35
**Purpose:** Genesis ROM header required by TMSS and by emulators. Contains console string, copyright string, ROM name, device string, ROM/RAM ranges, checksum, and region codes.
**Status: PERMANENT.** The content (title string "RASTAN DIRECT VIDEO TEST", etc.) is final-state appropriate.

---

### main_68k.s Items

#### PERMANENT: `main_68k` entry point

**Symbol:** `main_68k`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 55–70
**Purpose:** Sets interrupt mask (`#0x2700`), calls `vdp_boot_setup`, calls `init_staging_state`, re-enables interrupts, then enters the main loop. The main loop waits for `frame_counter` to change (VBlank-driven), then calls `arcade_tick_logic`.
**Status:** The outer shell is PERMANENT. The call to `init_staging_state` and the call to `arcade_tick_logic` contain bringup sub-items (see below). The `frame_counter` wait-for-VBlank pattern is the correct final architecture for the main loop.

#### PERMANENT: `_VINT_handler` — structural skeleton

**Symbol:** `_VINT_handler`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 72–98
**Purpose:** Save/restore all registers, read VDP status, bracket display off/on, commit staged content, increment frame counter, `rte`.
**Status:** The structural skeleton is PERMANENT. The specific commit calls within it have bringup vs permanent distinctions (see VBlank section below).

#### PERMANENT: `vdp_boot_setup`

**Symbol:** `vdp_boot_setup`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 100–161
**Purpose:** Writes all 15 VDP registers to their final operating values: Mode1 = 0x04, Mode2 = display-off during setup, Plane A base = 0xE000, Window base = 0xF000, Plane B base = 0xC000, SAT base = 0xF800, BG color = 0, HInt counter = 0xFF (disabled), Mode3 = 0x00, Mode4 = 0x0081 (320-wide H40, progressive), HScroll base = 0xFC00, Auto-increment = 2, Plane size = 32×32 (0x01), Window X/Y = 0.
**Status: PERMANENT.** These VDP register values are the correct final values for the Genesis port. Nothing changes.

#### PERMANENT: `vdp_set_reg` helper

**Symbol:** `vdp_set_reg`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 163–169
**Purpose:** Encodes and writes one VDP register write command to `VDP_CTRL`. Used by `vdp_boot_setup` and by the display-off/on bracketing in `_VINT_handler`.
**Status: PERMANENT.**

#### PERMANENT: `vdp_set_vram_write_addr` helper

**Symbol:** `vdp_set_vram_write_addr`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 171–184
**Purpose:** Encodes a VRAM write address into the VDP control word format (bits 14:13 = 0b01, address split across high and low longword halves) and writes it to `VDP_CTRL`.
**Status: PERMANENT.** Used by all VDP commit functions.

#### PERMANENT: `sprite_dma_addr_high_bits_fix`

**Symbol:** `sprite_dma_addr_high_bits_fix`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 186–192
**Purpose:** Extracts bits 16:15 of a VRAM address into D2 bits 1:0. Used in DMA address encoding for sprite tile uploads.
**Status: PERMANENT.**

#### PERMANENT: `genesistan_hook_tilemap_plane_a` — core logic

**Symbol:** `genesistan_hook_tilemap_plane_a`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 193–315
**Purpose:** Intercepts the PC080SN BG strip producer. Validates `dest_ptr` against the C-window (0xC00000–0xC03FFF range), decodes row/col, iterates the 16-entry descriptor list, for each valid descriptor reads ROM at the encoded source pointer, decodes attribute bits (palette sub-index, flip flags) via LUT, writes 4 translated nametable words to `staged_bg_buffer`, marks `bg_dirty`, advances `dest_ptr` by 0x400.
**Status: Core logic is PERMANENT.** The hook is the central translation layer. See Section 7 for full confirmation and note on `bg_dirty` flag (BRINGUP_ONLY granularity).

#### BRINGUP_ONLY: `bg_dirty` whole-plane flag in `genesistan_hook_tilemap_plane_a`

**Symbol/label:** `move.b #1, bg_dirty` at line 289 (inside `.Lbg_hook_row_loop`)
**File:** `apps/rastan-direct/src/main_68k.s`, line 289
**Purpose:** Marks the entire BG plane as dirty on every hook write. This is the correct signal mechanism for the current bring-up (full-plane commit). In the final port it must be replaced by a per-strip dirty bit (`bg_row_dirty` bitmask, one bit per row).
**Removal condition:** After `vdp_commit_bg` is replaced by `vdp_commit_bg_strips_if_dirty` and `bg_row_dirty` is introduced. The hook must then set `bset row_index, bg_row_dirty` instead of `move.b #1, bg_dirty`.

#### PERMANENT: `vdp_commit_bg` — gated BG plane commit

**Symbol:** `vdp_commit_bg`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 334–350
**Purpose:** Tests `bg_dirty`; if clear, skips. If set, calls `vdp_commit_tiles_if_dirty`, writes VRAM address for PLANE_B_BASE (0xC000), copies 2048 words from `staged_bg_buffer` to VDP_DATA, clears `bg_dirty`.
**Status:** The function is structurally PERMANENT (a BG commit function must exist). The full-plane 2048-word write granularity is BRINGUP_ONLY. The final version (`vdp_commit_bg_strips_if_dirty`) replaces this function; this version is removed at that time.

#### BRINGUP_ONLY: Full 2048-word BG plane commit granularity

**Symbol/label:** Inner loop in `vdp_commit_bg`, lines 343–348
**File:** `apps/rastan-direct/src/main_68k.s`, lines 343–348
**Purpose:** Writing all 2048 words on every dirty event. In final port, only changed strips (64 words per row) are written. Full-plane commit at ~49,000 cycles per dirty event overruns the 7,400-cycle VBlank budget by 6.6× when more than one frame has BG changes.
**Removal condition:** When `vdp_commit_bg_strips_if_dirty` (per-row, 64 words/row, 32-bit dirty mask) replaces this function.

#### PERMANENT: `vdp_commit_tiles_if_dirty`

**Symbol:** `vdp_commit_tiles_if_dirty`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 317–332
**Purpose:** Tests `tiles_dirty`; if set, writes 48 words from `staged_tile_words` to VRAM starting at `VRAM_TILE_BASE` (0x0020), clears `tiles_dirty`. These are the two diagnostic tiles (solid-color tiles 1 and 2) plus a checkerboard tile 3.
**Status:** The commit mechanism is PERMANENT. The tile content in `staged_tile_words` is TEMPORARY (see below). In final port, this function commits arcade-sourced tiles, not synthetic diagnostic tiles.

#### PERMANENT: `vdp_commit_palette`

**Symbol:** `vdp_commit_palette`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 352–360
**Purpose:** Writes CRAM address 0x0000, copies 64 words from `staged_palette_words` to VDP_DATA.
**Status: PERMANENT.** The commit mechanism is final-architecture correct. The content in `staged_palette_words` at startup is a TEMPORARY diagnostic rainbow palette (see below).

#### PERMANENT: `vdp_commit_scroll`

**Symbol:** `vdp_commit_scroll`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 362–372
**Purpose:** Writes HScroll table entry for rows 0–1 (two words to VRAM at HScroll base 0xFC00), then writes VSRAM for vertical scroll (two words via VSRAM control word 0x40000010). Sources: `staged_scroll_x_fg`, `staged_scroll_x_bg`, `staged_scroll_y_fg`, `staged_scroll_y_bg`.
**Status: PERMANENT.** The scroll commit mechanism is final-architecture correct. The staged scroll values in the current build are set by `init_staging_state` to 0 and not changed by the arcade hook (scroll hook not yet active); this is TEMPORARY behavior, but the commit function itself is permanent.

#### PERMANENT: `rastan_direct_update_inputs`

**Symbol:** `rastan_direct_update_inputs`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 374–451
**Purpose:** Reads two-phase 6-button Genesis joypad protocol for P1 and P2. Translates directional bits (D-pad) and action buttons (A/B/C) into the Rastan TC0040IOC active-low format. Writes results to `genesistan_shadow_input_390001`, `390003`, `390005`, `390007`. Handles coin pulse edge detection via `prev_coin_p1_a_pressed`.
**Status: PERMANENT.** Input translation is a core adapter function. The coin pulse edge detection (using `prev_coin_p1_a_pressed`) is also permanent — it prevents a held A-button from generating continuous coin pulses.

#### BRINGUP_ONLY: `arcade_tick_logic`

**Symbol:** `arcade_tick_logic`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 453–456
**Purpose:** Calls `rastan_direct_update_inputs` then JSRs to `rastan_direct_arcade_tick_entry` (0x0003A208 in the relocated arcade code).
**Status:** The JSR to the arcade entry point is PERMANENT. The function as a named wrapper is BRINGUP_ONLY — in the final port, the main loop calls `rastan_direct_update_inputs` and the arcade tick directly, or `arcade_tick_logic` becomes permanent under that name. No change needed for correctness; it is more of a naming/structural question. Not a risk item.

#### TEMPORARY: `init_staging_state` — synthetic checkerboard fill

**Symbol/label:** `.Lbg_row` / `.Lbg_col` loop in `init_staging_state`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 487–502
**Purpose:** Fills `staged_bg_buffer` with a checkerboard pattern — alternating tile index 0x0001 and 0x0002 based on `(row XOR col) & 1`. This is diagnostic bring-up display content that proves BG Plane B is reaching the VDP. It is visible as a colored checkerboard before any arcade hook fires.
**Removal condition:** When the arcade BG hook is confirmed to be filling `staged_bg_buffer` correctly on every frame and the checkerboard is no longer needed as a baseline. The buffer should instead be zeroed (all tile 0, which is transparent/empty) at init, with all content coming from the hook.

#### TEMPORARY: `init_staging_state` — `staged_fg_buffer` zero-fill

**Symbol/label:** `.Lfg_clear` loop in `init_staging_state`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 504–508
**Purpose:** Zeroes all 2048 words of `staged_fg_buffer`. Zero is transparent on Genesis (tile index 0, palette 0).
**Status:** This zero-fill is correct behavior and should be retained. However, the `move.b #1, fg_dirty` that follows (see below) is TEMPORARY.

#### TEMPORARY: `init_staging_state` — `fg_dirty` initial set

**Symbol/label:** `move.b #1, fg_dirty` in `init_staging_state`
**File:** `apps/rastan-direct/src/main_68k.s`, line 468 (within `init_staging_state`)
**Purpose:** Marks FG plane as dirty on startup, causing `_VINT_handler` to call `vdp_commit_fg` on frame 1. Because `staged_fg_buffer` is all zero, this writes 2048 zero words to Plane A VRAM — a 49,208-cycle no-op with zero visual effect.
**Removal condition:** When `vdp_commit_fg` is removed from the VBlank path (per the VBlank transition plan). `fg_dirty` and its initial set both become dead code at that point. Remove both.

#### TEMPORARY: `init_staging_state` — Plane A direct VRAM clear

**Symbol/label:** `.Lplane_a_clear` loop in `init_staging_state`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 510–515
**Purpose:** Writes 2048 zero words directly to VDP Plane A VRAM during init (before interrupts are enabled). Ensures Plane A starts transparent before any VBlank commit occurs.
**Status:** This is a bring-up artifact. In the final port, the arcade init path handles display init including any C-window fills. The direct VRAM write during the wrapper's init function is structurally wrong for the final ownership model (arcade init path owns display content). However, it is harmless until arcade init is called directly.
**Removal condition:** When arcade `startup_common` (beginning at 0x03AF04 in the relocated code) is invoked as part of wrapper startup, replacing wrapper-side VRAM initialization.

#### TEMPORARY: `init_staging_state` — synthetic palette init

**Symbol/label:** `palette_init_words` table (`.rodata`), copy loop `.Lpal_init`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 473–478 (copy loop); lines 527–534 (table)
**Purpose:** The `palette_init_words` table is a 64-entry rainbow diagnostic palette used to prove all four CRAM palette lines are receiving data and are visible. The copy loop seeds `staged_palette_words` from this table. The VBlank handler commits this palette on frame 1.
**Removal condition:** When the arcade palette hook is active and `staged_palette_words` is populated from arcade CLCS palette data on every frame. At that point the synthetic palette table and the init copy loop are removed; `staged_palette_words` starts zeroed and is populated by the arcade path.

#### TEMPORARY: `init_staging_state` — synthetic tile data init

**Symbol/label:** `tile_init_words` table (`.rodata`), copy loop `.Ltile_init`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 481–485 (copy loop); lines 536–547 (table)
**Purpose:** The `tile_init_words` table defines three synthetic tiles: tile 1 (all nibbles 0x1, solid color 1), tile 2 (all nibbles 0x2, solid color 2), and tile 3 (alternating 0x30/0x03, checkerboard pattern). Used by the checkerboard BG init. Committed to VRAM tile indices 1–3 by `vdp_commit_tiles_if_dirty` on frame 1.
**Removal condition:** When the checkerboard BG init is removed (same condition as synthetic BG init). The tile table and its copy loop are both removed; `staged_tile_words` starts zeroed.

#### TEMPORARY: `init_staging_state` — staged_dest_ptr values

**Symbol/label:** Lines 463–467 in `init_staging_state`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 463–467
**Purpose:** Sets `staged_dest_ptr_bg` and `staged_dest_ptr_fg` in Genesis WRAM, and also writes `ARCADE_FIX_DEST_BG` (0xFF10A0) and `ARCADE_FIX_DEST_FG` (0xFF10A4) directly. The dest_ptr values are 0x00C00000 and 0x00C08000. These mirror the values that the arcade's own init path writes after `startup_common` sets up the C-window. Setting them from the wrapper is correct for current bring-up (the arcade's `startup_common` is not called). 
**Removal condition:** When arcade `startup_common` is called directly as part of wrapper startup, because `startup_common` at step 5 (arcade address 0x03AF10–0x03AF48) fills the BG C-window (0xC00000, 4096 words of 0x20) and FG C-window (0xC08000, 4096 words of 0x20). The dest_ptr values would flow from the arcade's own init. The wrapper's manual write of 0xFF10A0/0xFF10A4 would then be redundant and should be removed.

#### TEMPORARY: `init_staging_state` — A5 = 0xFF0000 setup

**Symbol/label:** `lea 0x00FF0000, %a5` in `init_staging_state`
**File:** `apps/rastan-direct/src/main_68k.s`, line 459
**Purpose:** Sets A5 to 0xFF0000 before calling `init_staging_state`. Required because the patched arcade code at 0x03AF04 (`lea 0x10c000, %a5` → patched to `lea 0xFF0000, %a5`) establishes A5 during its own init. In the current bring-up, `init_staging_state` sets A5 before the arcade tick entry is reached, so the arcade's first tick finds A5 correct.
**Status:** This line is TEMPORARY only in the sense that the A5 establishment should flow from the arcade's own init path (the opcode_replace at `0x03AF04` in the patch manifest already handles this). The wrapper-side `lea` is redundant once `startup_common` is called first. However, as a pure defensive measure, it is harmless to retain until arcade init is confirmed.

#### DIAGNOSTIC: `hook_plane_a_hits` counter

**Symbol:** `hook_plane_a_hits` in `.bss`; `addq.w #1, hook_plane_a_hits` in `genesistan_hook_tilemap_plane_a`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 197, 584–585
**Purpose:** Increments a word counter every time the BG tilemap hook fires. Used to prove hook invocation count during debugging.
**Removal condition:** Diagnostic. Remove when no longer needed for verification. Has no functional effect other than WRAM write overhead (negligible). Not a blocking item but should be removed before final build.

#### BRINGUP_ONLY: `staged_fg_buffer` BSS allocation (2048 words)

**Symbol:** `staged_fg_buffer`
**File:** `apps/rastan-direct/src/main_68k.s`, lines 605–606
**Purpose:** 4096-byte WRAM staging buffer for Plane A (FG) nametable. Currently populated by wrapper init only (all zeros). No arcade hook writes to it yet.
**Status:** The buffer allocation itself is correct for the final architecture (FG hook will write here). It is BRINGUP_ONLY in the sense that no consumer currently populates it with arcade data. The buffer must remain allocated; the label stays in `.bss`.

---

### Summary Table

| Item | File | Lines | Category | Removal Condition |
|------|------|-------|----------|------------------|
| Exception vector table | boot.s | 9–19 | PERMANENT | Never |
| TMSS handshake | boot.s | 45–49 | PERMANENT | Never |
| ROM header | boot.s | 21–35 | PERMANENT | Never |
| `vdp_boot_setup` | main_68k.s | 100–161 | PERMANENT | Never |
| `vdp_set_reg` helper | main_68k.s | 163–169 | PERMANENT | Never |
| `vdp_set_vram_write_addr` | main_68k.s | 171–184 | PERMANENT | Never |
| `sprite_dma_addr_high_bits_fix` | main_68k.s | 186–192 | PERMANENT | Never |
| `genesistan_hook_tilemap_plane_a` core | main_68k.s | 193–315 | PERMANENT | Never |
| `bg_dirty` flag in hook | main_68k.s | 289 | BRINGUP_ONLY | When `bg_row_dirty` mask replaces it |
| `vdp_commit_bg` commit function | main_68k.s | 334–350 | BRINGUP_ONLY | Replaced by strip commit function |
| Full 2048-word BG commit loop | main_68k.s | 343–348 | BRINGUP_ONLY | Same as above |
| `vdp_commit_tiles_if_dirty` | main_68k.s | 317–332 | PERMANENT | Never (content changes, function stays) |
| `vdp_commit_palette` | main_68k.s | 352–360 | PERMANENT | Never |
| `vdp_commit_scroll` | main_68k.s | 362–372 | PERMANENT | Never |
| `rastan_direct_update_inputs` | main_68k.s | 374–451 | PERMANENT | Never |
| `arcade_tick_logic` wrapper | main_68k.s | 453–456 | BRINGUP_ONLY | Low risk; structural only |
| `init_staging_state` synthetic checkerboard | main_68k.s | 487–502 | TEMPORARY | Arcade BG hook confirmed active |
| `init_staging_state` fg_dirty set | main_68k.s | 468 | TEMPORARY | When FG commit removed from VBlank |
| `init_staging_state` Plane A VRAM clear | main_68k.s | 510–515 | TEMPORARY | When arcade `startup_common` called directly |
| `palette_init_words` table + init loop | main_68k.s | 473–478, 527–534 | TEMPORARY | Arcade palette hook active |
| `tile_init_words` table + init loop | main_68k.s | 481–485, 536–547 | TEMPORARY | Checkerboard removed |
| `staged_dest_ptr_bg/fg` init | main_68k.s | 463–467 | TEMPORARY | Arcade `startup_common` called directly |
| `hook_plane_a_hits` counter | main_68k.s | 197, 584–585 | DIAGNOSTIC | Now or after verification complete |
| `staged_fg_buffer` BSS allocation | main_68k.s | 605–606 | BRINGUP_ONLY (keep buffer, no producer yet) | Keep buffer; producer added later |

---

## 4. 0xDFFFFE Suppression Plan

### Established facts (from `Andy_dffffe_hardware_identification.md` and disassembly census)

- 0xDFFFFE is NOT a device. On the Rastan arcade board, the PC090OJ sprite RAM occupies 0xD00000–0xD03FFF only. Nothing is mapped from 0xD04000 through 0xDFFFFF. The write goes to open bus.
- The address 0x00DFFFFE does not appear anywhere in `maincpu.bin` as a static operand. Confirmed by binary search.
- All statically-identifiable D-range writes in the disassembly target 0xD01BFE, 0xD00698, and register-indirect sprite copy loops whose worst-case loop end addresses are well below 0xD03FFF.
- The specific instruction whose dynamic effective address resolves to 0xDFFFFE cannot be identified by static analysis. It is a register-indirect write (post-increment or base+offset) in the sprite processing subsystem that computes an address above 0xD03FFF for one specific code path.
- On Genesis, the entire range 0xD00000–0xDFFFFF is unmapped. BlastEm freezes the machine on any write there.

### Why `opcode_replace` at a fixed PC cannot solve this

`opcode_replace` requires a specific arcade PC and specific original bytes. Because the problematic write uses a register-indirect addressing mode, the PC of the instruction is a fixed code address, but the effective address is runtime-computed. The same instruction PC may write into valid sprite RAM (0xD00000–0xD03FFF) on most iterations and write to 0xDFFFFE on one specific iteration. NOPing the instruction at its PC would suppress all sprite RAM writes from that instruction — breaking sprite rendering entirely.

### Correct suppression: Genesis address-window sink

The correct solution is to declare the extended D-range as a write-sink window. This requires adding a new entry to `declared_arcade_windows` in `specs/rastan_direct_remap.json`:

```json
{
  "name": "pc090oj_full_d_range",
  "start": "0x00D00000",
  "end_exclusive": "0x00E00000"
}
```

Combined with a Genesis-side mapping that redirects all D-range writes to a scratch area in WRAM. The scratch area must be:
- Located in Genesis WRAM (0xFF0000–0xFFFFFF range)
- At a fixed offset not used by any active variable in the wrapper
- At least 4 bytes (word-aligned) to accept word and longword writes without fault
- Suggested address: 0xFF3F00–0xFF3FFF (256-byte scratch zone, currently unused per symbol audit)

The PC090OJ sprite RAM (0xD00000–0xD03FFF) is also unmapped on Genesis — all sprite content in the Rastan-direct port is accessed via Genesis WRAM workram mirrors, not via D-range writes. Redirecting the full D-range to a sink does not suppress any active data path.

### Alternative: runtime PC capture + targeted opcode NOP

If the patcher's window mechanism does not support broad write-redirection, the alternative is:
1. Run the patched ROM in BlastEm with the debugger active.
2. On the machine freeze, read the PC register. This identifies the exact instruction.
3. Read the bytes at that PC from the patched ROM.
4. Add an `opcode_replace` entry in `rastan_direct_remap.json` that replaces those bytes with NOPs.

Risk: if the same instruction also writes valid sprite data on other loop iterations, NOPing it suppresses all writes from that instruction, not just the one that overshoots. The sink approach is lower risk.

### Recommendation

Use the window-sink approach. It is additive (34 existing `opcode_replace` entries are not touched), it correctly matches the arcade hardware behavior (open bus = writes discarded), and it does not suppress any sprite data paths. The runtime-trace approach is an acceptable fallback if the patcher does not support range-level sink redirection.

---

## 5. VBlank Ownership Collapse Plan

### Current VBlank handler structure

```
_VINT_handler:
    movem.l %d0-%d7/%a0-%a6, -(%sp)     ; PERMANENT
    move.w  VDP_CTRL, %d0               ; PERMANENT (VDP status drain)
    display OFF                          ; PERMANENT
    bsr     vdp_commit_bg               ; BRINGUP_ONLY granularity
    tst.b   palette_dirty               ; PERMANENT pattern
    beq.s   .Lskip_palette
    bsr     vdp_commit_palette          ; PERMANENT
    clr.b   palette_dirty
    display ON                          ; PERMANENT
    bsr     vdp_commit_scroll           ; PERMANENT
    addq.w  #1, frame_counter           ; PERMANENT
    movem.l (%sp)+, %d0-%d7/%a0-%a6    ; PERMANENT
    rte                                 ; PERMANENT
```

Note: The `vdp_commit_fg` call was removed in an earlier step (per `Cody_remove_fg_full_plane_commit.md`). Current code (re-read) does not show a `bsr vdp_commit_fg` in `_VINT_handler`. Confirmed: the handler contains `vdp_commit_bg`, conditional `vdp_commit_palette`, and `vdp_commit_scroll`.

### What is permanent vs scaffolding in the current VBlank handler

**PERMANENT (must stay forever):**
- Register save/restore (`movem.l`)
- VDP status read (`move.w VDP_CTRL, %d0`) — drains VDP FIFO flag
- Display OFF/ON bracket (Mode2 writes via `vdp_set_reg`)
- `vdp_commit_palette` (gated by `palette_dirty`) — palette commit mechanism is correct final architecture
- `vdp_commit_scroll` — scroll commit mechanism is correct final architecture
- `frame_counter` increment
- `rte`

**BRINGUP_ONLY (correct concept, wrong granularity):**
- `vdp_commit_bg` call — the function name and concept are correct; the implementation commits 2048 words. In final architecture this call becomes `vdp_commit_bg_strips_if_dirty`.

**NOT CURRENTLY PRESENT (was removed):**
- `vdp_commit_fg` call — removed. FG will return as `vdp_commit_fg_strips_if_dirty` when the FG arcade hook is active.

### Is `staged_bg_buffer` / `staged_fg_buffer` double-buffer model correct?

**YES.** The double-buffer (arcade writes to WRAM staging buffer during the main loop tick; VBlank handler commits the staging buffer to VRAM) is architecturally correct for the final port. It matches the Rainbow Islands model (WRAM staging buffers committed by VBlank ISR). The naming "double-buffer" is slightly misleading — there is only one staging buffer per plane, not two alternating buffers. But the single-staging-buffer-committed-by-VBlank model is correct and must be retained.

What changes is commit granularity: 2048 words/frame (current) → 64 words/row × dirty rows only (final).

### Final VBlank handler minimum content

```
_VINT_handler:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    move.w  VDP_CTRL, %d0               ; drain VDP FIFO/interrupt flag
    [display OFF]
    bsr     vdp_commit_tiles_if_dirty   ; top-level, independent of BG
    bsr     vdp_commit_bg_strips_if_dirty  ; per-row dirty-mask commit
    tst.b   palette_dirty
    beq.s   .Lskip_palette
    bsr     vdp_commit_palette
    clr.b   palette_dirty
.Lskip_palette:
    [display ON]
    bsr     vdp_commit_scroll
    [when FG arcade hook active:]
    bsr     vdp_commit_fg_strips_if_dirty
    addq.w  #1, frame_counter
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rte
```

The VBlank handler generates no display content. It only commits what arcade code (via hooks) has placed in staging buffers. It does not synthesize checkerboards, test palettes, or zero-fill planes.

---

## 6. Arcade Init Path Restoration Plan

### Arcade `startup_common` sequence (address 0x03AF04 in relocated code)

The arcade's own init path begins at 0x03AF04 (post-relocation: 0x03AF04 + 0x200 = 0x03B104 in ROM). Per `arcade_init_vs_launcher_fake_init_audit.md`, `startup_common` at 0x03AE86 (original, 0x03B086 relocated) performs:

1. Clears hardware registers (arcade-side, irrelevant on Genesis)
2. Zeros work RAM (16KB region)
3. `lea 0x10c000, %a5` — patched to `lea 0xFF0000, %a5` via `opcode_replace` at 0x03AF04
4. PC080SN C-window fills: BG at 0xC00000 (4096 words of 0x20), FG at 0xC08000 (4096 words of 0x20)
5. DIP switch reads (patched to use shadow constants)
6. DIP table lookups → workram fields (A5@(24), A5@(28), A5@(38), A5@(46–56))
7. Coinage table init → A5@(8..16)
8. Config table copy (39 bytes from ROM 0x3b0d4 → A5@(320))
9. Sprite init marker A5@(74) = 0xAA
10. Enters attract loop (A5@(0) = 0)

### What `init_staging_state` currently does that `startup_common` would cover

| `init_staging_state` action | Covered by `startup_common`? | Notes |
|-----------------------------|------------------------------|-------|
| `lea 0xFF0000, %a5` | YES — via `opcode_replace` at 0x03AF04 | Patched `startup_common` does this at step 3 |
| `clr.w frame_counter` | NO | Genesis wrapper variable; arcade knows nothing of it |
| `clr.w tick_counter` | NO | Genesis wrapper variable |
| Write `ARCADE_FIX_DEST_BG` (0xFF10A0) = 0xC00000 | PARTIALLY — arcade sets up C-window base pointer; wrapper dest_ptr tracking is wrapper-specific | Startup_common fills the C-window but does not write 0xFF10A0 as an explicit dest_ptr. The dest_ptr is managed by arcade runtime calls. |
| Write `ARCADE_FIX_DEST_FG` (0xFF10A4) = 0xC08000 | PARTIALLY — same reasoning | Same as above |
| `move.b #1, palette_dirty` | NO | Genesis wrapper dirty flag; no arcade analog |
| `move.b #1, tiles_dirty` | NO | Genesis wrapper dirty flag |
| `move.b #1, bg_dirty` | NO | Genesis wrapper dirty flag |
| Synthetic palette copy | NO | Replaced by arcade palette hook |
| Synthetic tile data copy | NO | Replaced by arcade tile uploads |
| Synthetic BG checkerboard fill | NO | Replaced by arcade BG hook |
| FG buffer zero-fill | NO | Wrapper responsibility; arcade fills FG via hook |
| Plane A VRAM direct clear | PARTIALLY — startup_common fills C-windows at step 4 | Startup_common writes arcade C-window values (0x20); Genesis wrapper needs to clear Plane A VRAM separately |

### Condition under which wrapper-side workram initialization can be removed

Wrapper-side workram initialization (the subset of `init_staging_state` that writes 0xFF10A0 and 0xFF10A4, and sets A5 = 0xFF0000) can be removed when:

1. The wrapper calls `startup_common` (at relocated address 0x03B086) as part of wrapper startup, BEFORE the first arcade tick.
2. The opcode_replace at 0x03AF04 (patching `lea 0x10C000` to `lea 0xFF0000`) is confirmed active.
3. The TC0040IOC suppression patches (at 0x03AE34, 0x03AE9C, 0x03AF1E, 0x03AF7A, 0x03AF86) are all confirmed active — these replace DIP hardware reads and IO control writes with safe Genesis operations.

Under these three conditions, `startup_common` correctly initializes A5, clears workram, applies DIP constants, and sets the config table. The wrapper only needs to:
- Initialize its own Genesis-specific variables (`frame_counter`, `tick_counter`, dirty flags)
- Initialize staging buffers (but with zero content, not synthetic patterns)
- Set up the VDP registers (`vdp_boot_setup`, already separate)

### Fields that always remain wrapper-owned

The following workram fields are NEVER covered by arcade `startup_common` — they are Genesis wrapper-specific and must always be initialized by the wrapper:

- `frame_counter` (WRAM, not arcade workram)
- `tick_counter` (WRAM, not arcade workram)
- `palette_dirty`, `tiles_dirty`, `bg_dirty` (or `bg_row_dirty`) flags
- `staged_*` buffers (zero-init is correct; content comes from hooks)
- `genesistan_shadow_input_390001/3/5/7` (initialized in `rastan_direct_update_inputs` on first call)

---

## 7. PC080SN Hook Ownership Confirmation

### `genesistan_hook_tilemap_plane_a` is PERMANENT

This hook is the core BG translation layer. It is invoked by the `opcode_replace` entry at arcade PC 0x055968 (relocated: 0x055B68), which replaces the PC080SN BG strip producer with a JSR to `genesistan_hook_tilemap_plane_a`. Without this hook, no arcade BG content reaches the Genesis VDP.

**Confirmed: this hook is PERMANENT architecture, not scaffolding.**

### Current hook behavior correctness

The hook implements the following pipeline, which is correct for the final architecture:

1. **Saves all registers** — `movem.l %d0-%d7/%a0-%a6, -(%sp)`. Correct: the hook is called from arcade code that does not expect register clobber.
2. **Establishes A5 = 0xFF0000** — `lea 0x00FF0000, %a5`. Correct: the hook needs access to arcade workram fields via A5-relative addressing.
3. **Reads `ARCADE_PC080SN_STRIP_INDEX_OFFSET` (A5+0x10CA)** — strip index D7. Correct: this is the arcade-maintained strip index for the current row.
4. **Reads `ARCADE_PC080SN_DEST_BG_OFFSET` (A5+0x10A0)** — dest_ptr D5. Correct: this is the arcade C-window destination pointer for the current strip.
5. **Validates dest_ptr against 0xC00000–0xC03FFF** — correct final-architecture range check.
6. **Decodes row (D1 = offset/4 & 0x1F) and column (D2 = offset >> 6)** — maps C-window byte offset to BG strip coordinates. Correct.
7. **Iterates 16 descriptor entries** from `ARCADE_PC080SN_DESC_BG_LIST_OFFSET` (A5+0x1000) — reads each descriptor, validates it, reads ROM tile data, applies attribute LUT, writes translated nametable word to `staged_bg_buffer[row * 128 + col * 2]`.
8. **Marks `bg_dirty = 1`** — notifies VBlank to commit. BRINGUP_ONLY granularity (see below).
9. **Advances dest_ptr by 0x400** and stores back to A5+0x10A0. Correct: advances the C-window pointer for the next strip.

### Bring-up simplification within the hook: `bg_dirty` whole-plane flag

**Location:** `move.b #1, bg_dirty` at line 289, inside `.Lbg_hook_row_loop`.

This sets the entire BG plane dirty on every hook write. In bring-up, this is correct because `vdp_commit_bg` is a full-plane commit and must fire whenever any strip changes.

In the final architecture, the hook should instead set a bit in `bg_row_dirty` corresponding to the current row index (D2 at that point in the hook). This limits each VBlank commit to only the rows that changed.

The change required: replace `move.b #1, bg_dirty` with `bset D2, bg_row_dirty` (or the equivalent with the row number in a register). This is a single instruction change — not an architectural change, just a granularity upgrade.

**No other bring-up simplifications exist within `genesistan_hook_tilemap_plane_a`.** The validity checks, range clamps, descriptor iteration, ROM reads, LUT lookups, and WRAM writes are all correct final-architecture behavior.

### `genesistan_hook_tilemap_plane_b` — not present in current build

The task description mentions `genesistan_hook_tilemap_plane_b`. This hook does not appear in the current `main_68k.s` (only `genesistan_hook_tilemap_plane_a` exists). The FG tilemap hook is a future addition, not a current implementation. When added, it will mirror the BG hook structure and write to `staged_fg_buffer` with `fg_row_dirty` dirty-bit tracking.

---

## 8. Ordered Transition Steps

Each step lists: what changes, prerequisites, verification method, and risk.

---

### Step 1: Add 0xDFFFFE suppression (D-range write sink)

**What changes:** Add a new window declaration to `specs/rastan_direct_remap.json` covering 0xD00000–0xDFFFFF, redirected to a scratch area in Genesis WRAM (0xFF3F00–0xFF3FFF). No `opcode_replace` changes. No source changes.

**Prerequisite:** None. This is independent of all other steps.

**Verification:** Run the patched ROM in BlastEm. The `machine freeze due to write to address DFFFFE` error must not appear. The ROM must run past the previously-crashing frame. Any display output (checkerboard, attract mode, etc.) that was visible before the crash must still be visible.

**Risk:** LOW. The change is additive (new window, nothing existing modified). PC090OJ sprite RAM (0xD00000–0xD03FFF) is also within the sink window — but the Rastan-direct port does not use D-range addresses for sprite data (sprite content is in Genesis WRAM workram, accessed via A5+offset, not via the D-range). Redirecting all D-range writes to the scratch sink does not suppress any active data path.

---

### Step 2: Remove `hook_plane_a_hits` diagnostic counter

**What changes:** Remove `addq.w #1, hook_plane_a_hits` from `genesistan_hook_tilemap_plane_a` (line 197). Remove the `.bss` allocation for `hook_plane_a_hits` (lines 584–585).

**Prerequisite:** None. Hook invocation is confirmed working (BG content is visible on screen from arcade hook).

**Verification:** Build succeeds. Hook still fires correctly (BG content unchanged).

**Risk:** NONE. The counter has no effect on game logic or VDP output.

---

### Step 3: Remove FG full-plane commit infrastructure (`fg_dirty`, `init_staging_state` fg_dirty set)

**What changes:** Remove `move.b #1, fg_dirty` from `init_staging_state`. Remove `fg_dirty: .byte 0` from `.bss`. Confirm `vdp_commit_fg` call is not in `_VINT_handler` (it was already removed per prior analysis). If any dead `vdp_commit_fg` function body remains, remove it.

**Prerequisite:** Confirm `_VINT_handler` does not call `vdp_commit_fg`. (From current source read: confirmed not present.)

**Verification:** Build succeeds. No change in visible output (FG was all-transparent before this step; removing the unused dirty flag changes nothing visible). Frame 1 VBlank does not attempt to write FG VRAM.

**Risk:** NONE. `fg_dirty` has no consumer in the current VBlank handler.

---

### Step 4: Introduce `bg_row_dirty` bitmask — replace `bg_dirty` whole-plane flag

**What changes:**
- Add `bg_row_dirty: .long 0` to `.bss`.
- Remove `bg_dirty: .byte 0` from `.bss`.
- In `init_staging_state`: replace `move.b #1, bg_dirty` with `move.l #0xFFFFFFFF, bg_row_dirty` (all 32 rows dirty on first frame).
- In `genesistan_hook_tilemap_plane_a`: replace `move.b #1, bg_dirty` with a per-row bit-set using the current row index.
- Implement `vdp_commit_bg_strips_if_dirty`: test `bg_row_dirty`; if zero, return; otherwise iterate bits 0–31, for each set bit compute VRAM row address (VRAM_PLANE_B_BASE + row × 128), issue write command, copy 64 words from `staged_bg_buffer + row × 128`, clear bit.
- In `_VINT_handler`: replace `bsr vdp_commit_bg` with `bsr vdp_commit_bg_strips_if_dirty`.

**Prerequisite:** Steps 2 and 3 complete (cleaner bss section, no dead fg_dirty).

**Verification:** Frame 1 output must match pre-change output (all 32 rows committed). Frame 2+ output: BG changes only when the arcade BG hook fires. VBlank timing for frame 2+ drops from ~49,000 cycles (full plane) to ~320 cycles (zero dirty rows) plus the cost of rows the hook actually writes.

**Risk:** MEDIUM. This replaces a tested commit function with a new strip-level function. The row index calculation in the hook and in the commit function must agree. Off-by-one errors in either would produce misaligned or missing strip commits. Verify against known BG content (e.g., visible title screen tiles appearing in correct rows).

---

### Step 5: Move tile commit to top-level VBlank step

**What changes:** Remove `bsr vdp_commit_tiles_if_dirty` from inside `vdp_commit_bg_strips_if_dirty` (or from `vdp_commit_bg` if step 4 is not yet done). Add `bsr vdp_commit_tiles_if_dirty` as the first explicit step in `_VINT_handler`, between display-OFF and the BG strip commit.

**Prerequisite:** Step 4 complete (so tile commit moves to top-level of the new commit function sequence).

**Verification:** Tile content visible on screen is unchanged. The `tiles_dirty` flag path remains functional — tile commit still fires on frame 1 (when `tiles_dirty = 1`) and not on subsequent frames (when `tiles_dirty = 0`).

**Risk:** LOW. Logically independent move. Only structural change to call order.

---

### Step 6: Remove synthetic BG checkerboard, tile table, and palette table

**What changes:**
- Remove checkerboard fill loop (`.Lbg_row`/`.Lbg_col`) from `init_staging_state`. Replace with a zero-fill loop over `staged_bg_buffer` (or leave the buffer uninitialized, since arcade hook will write it).
- Remove `tile_init_words` table from `.rodata`.
- Remove tile data copy loop (`.Ltile_init`) from `init_staging_state`.
- Remove `palette_init_words` table from `.rodata`.
- Remove palette copy loop (`.Lpal_init`) from `init_staging_state`.
- In `init_staging_state`: retain `move.b #1, palette_dirty` (first frame palette commit must still fire once the arcade palette hook is active).

**Prerequisite:** The arcade BG hook is confirmed to be writing correct BG content to `staged_bg_buffer` on every frame. The arcade palette hook is active and writing correct palette data to `staged_palette_words`.

**Verification:** Display output shows arcade-sourced BG content, not the synthetic checkerboard. No regression in palette rendering (palette comes from arcade hook, not synthetic table).

**Risk:** HIGH if done before arcade hooks are confirmed. The checkerboard is the current visible baseline — removing it before the arcade hook reliably fills `staged_bg_buffer` will result in an all-black/empty Plane B. Execute only when BG hook coverage is verified per-frame.

---

### Step 7: Call arcade `startup_common` from wrapper init (remove wrapper-owned workram init)

**What changes:**
- In `main_68k` (or a new `init_arcade_hardware` function called from `main_68k`): add a JSR to the relocated `startup_common` address (0x03B086) before `init_staging_state`.
- Confirm all TC0040IOC suppression patches and DIP shadow patches cover the hardware access sites within `startup_common` (they do — see `opcode_replace` entries at 0x03AF04, 0x03AF7A, 0x03AF86, 0x03AE34, 0x03AE9C, 0x03AF1E).
- After `startup_common` runs, remove the following from `init_staging_state`:
  - `lea 0x00FF0000, %a5` (startup_common step 3 covers this via the A5 redirect patch)
  - `move.l #0x00C00000, ARCADE_FIX_DEST_BG` (startup_common covers workram dest_ptr initialization)
  - `move.l #0x00C08000, ARCADE_FIX_DEST_FG`
  - `move.l #0x00C00000, staged_dest_ptr_bg`
  - `move.l #0x00C08000, staged_dest_ptr_fg`
  - Direct Plane A VRAM clear loop (`.Lplane_a_clear`) — startup_common fills C-windows

**Prerequisite:** Steps 1–6 complete. The 0xDFFFFE crash must be suppressed (Step 1) before `startup_common` is called, because `startup_common` includes hardware register writes that on Genesis would otherwise fault. The TC0040IOC patches (write-suppression to 0x380000) are already in `rastan_direct_remap.json` and cover all sites in `startup_common`. The D-range sink (Step 1) covers any sprite RAM accesses within `startup_common`.

**Verification:** After `startup_common` runs, A5 = 0xFF0000 (confirmed by the A5 redirect patch). Workram is cleared and DIP fields are set. The arcade tick entry runs correctly with arcade-initialized workram state. The attract loop (A5@(0) = 0) begins instead of the current forced state 1 — this is a BEHAVIORAL change (attract mode runs instead of immediate gameplay).

**Risk:** HIGH. Calling `startup_common` is the largest single architectural change. It modifies A5@(0) to 0 (attract), resets workram, and writes to arcade hardware addresses (some suppressed by patches, some not). Any missed suppression patch for a hardware access within `startup_common` could cause a bus error or undefined behavior. Requires careful patch coverage audit before execution.

---

### Step 8: Add FG arcade hook (`genesistan_hook_tilemap_plane_b`)

**What changes:**
- Implement `genesistan_hook_tilemap_plane_b` mirroring the BG hook structure, targeting `staged_fg_buffer` and `fg_row_dirty`.
- Add the hook to `rastan_direct_remap.json` as an `opcode_replace` at the PC080SN FG strip producer site.
- Add `bsr vdp_commit_fg_strips_if_dirty` to `_VINT_handler` after the BG and palette commits.
- Add `fg_row_dirty: .long 0` to `.bss`.

**Prerequisite:** Steps 4 and 6 complete (per-strip dirty tracking pattern established and proven for BG; FG hook mirrors BG hook exactly).

**Verification:** Plane A shows arcade-sourced FG content (text, score, status bar). No regression on Plane B BG content.

**Risk:** MEDIUM. The FG hook is a new implementation. Its PC080SN FG strip producer intercept address must be found in the disassembly (not yet identified; requires targeted analysis of the FG producer path separate from the BG producer at 0x055968).

---

### Step 9: Final cleanup — remove `arcade_tick_logic` wrapper, clean `init_staging_state`

**What changes:**
- Remove `tick_counter` from `.bss` if unused.
- Inline `arcade_tick_logic` body (inputs update + arcade tick JSR) into the main loop.
- Remove `arcade_tick_logic` function label if not referenced externally.

**Prerequisite:** All prior steps complete and verified.

**Verification:** Build succeeds. Functional behavior unchanged.

**Risk:** NONE.

---

## 9. Items That Must Not Be Removed

The following items are PERMANENT minimum-adapter elements. They are not scaffolding and must not be touched during any cleanup or transition step.

| Symbol / Item | File | Lines | Reason Permanent |
|---------------|------|-------|-----------------|
| Exception vector table | boot.s | 9–19 | Genesis boot requirement |
| TMSS handshake | boot.s | 45–49 | Real hardware requirement |
| ROM header | boot.s | 21–35 | Genesis format requirement |
| `_start` entry point | boot.s | 41–54 | Bootstrap |
| `vdp_boot_setup` (all 15 register writes) | main_68k.s | 100–161 | VDP hardware init |
| `vdp_set_reg` | main_68k.s | 163–169 | VDP register write primitive |
| `vdp_set_vram_write_addr` | main_68k.s | 171–184 | VRAM address encoding |
| `sprite_dma_addr_high_bits_fix` | main_68k.s | 186–192 | DMA address encoding |
| `genesistan_hook_tilemap_plane_a` (all logic except `bg_dirty` granularity) | main_68k.s | 193–315 | Core BG translation layer |
| `vdp_commit_tiles_if_dirty` function (mechanism, not content) | main_68k.s | 317–332 | Tile VRAM upload |
| `vdp_commit_palette` | main_68k.s | 352–360 | Palette commit |
| `vdp_commit_scroll` | main_68k.s | 362–372 | Scroll commit |
| `rastan_direct_update_inputs` (all logic including coin pulse edge detection) | main_68k.s | 374–451 | Input translation adapter |
| `staged_bg_buffer` BSS allocation (4096 bytes) | main_68k.s | 603–604 | BG staging buffer |
| `staged_fg_buffer` BSS allocation (4096 bytes) | main_68k.s | 605–606 | FG staging buffer |
| `staged_palette_words` BSS allocation (128 bytes) | main_68k.s | 607–608 | Palette staging buffer |
| `staged_scroll_x/y_bg/fg` BSS words | main_68k.s | 593–600 | Scroll staging words |
| `frame_counter` BSS word | main_68k.s | 559–560 | VBlank synchronization |
| `genesistan_shadow_input_390001/3/5/7` BSS bytes | main_68k.s | 570–577 | Input shadow registers |
| `genesistan_shadow_dip1/2` BSS bytes | main_68k.s | 580–583 | DIP shadow registers |
| `prev_coin_p1_a_pressed` BSS byte | main_68k.s | 578–579 | Coin pulse edge state |
| `genesistan_pc080sn_tile_vram_lut` | main_68k.s | 549–550 | Tile VRAM address LUT (incbin) |
| `genesistan_pc080sn_attr_lut` | main_68k.s | 553–554 | Attribute translation LUT (incbin) |
| `opcode_replace` entry at 0x03AF04 (A5 redirect) | rastan_direct_remap.json | — | Arcade A5 workram base |
| All TC0040IOC write-suppress `opcode_replace` entries | rastan_direct_remap.json | — | Hardware suppression |
| All input shadow `opcode_replace` entries (390001/3/5/7) | rastan_direct_remap.json | — | Input adapter |
| PC080SN readback bypass `opcode_replace` entries (3 sites) | rastan_direct_remap.json | — | Readback crash prevention |
| DIP default constant `opcode_replace` entries (0x03AF7A, 0x03AF86) | rastan_direct_remap.json | — | DIP default values |
| `whole_maincpu_copy` and `rom_absolute_call_relocation` policy | rastan_direct_remap.json | — | ROM layout and relocation |
| `opcode_replace` entry at 0x055968 (BG hook redirect) | rastan_direct_remap.json | — | Core BG hook intercept |

No item in this list should be modified, renamed, or removed during scaffolding cleanup. Changes to any permanent item require a dedicated design note.

---

*End of Andy Final Architecture Transition Plan (No Scaffolding)*
