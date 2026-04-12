# Andy — Design: Genesis BSS Relocation and WRAM Ownership Model

**Build context:** rastan-direct, Build 0024+  
**Supersedes:** `docs/design/Cody_arcade_workram_relocation.md` (Option A — discard)  
**Root cause reference:** `docs/design/Andy_arcade_workram_relocation_analysis.md`

---

## Problem Summary

Arcade workram (A5-relative, base = 0xFF0000) and Genesis BSS (`.bss 0xFF0000 (NOLOAD)`)
share the same base address. The init code writes Genesis BSS symbols that collide with
critical arcade workram fields. The fix is to separate the address spaces at the hardware
level: leave arcade workram at its natural home (0xFF0000, as remapped by the spec patch)
and move Genesis BSS upward.

---

## TASK 1 — Final WRAM Ownership Model

```
0xFF0000 – 0xFF3FFF   Arcade workram         (A5 base = 0xFF0000)
0xFF4000 – 0xFF67FF   Genesis BSS            (current ~8 KB; starts at new GENESIS_BSS_BASE)
0xFF6800+             Available / future use
```

**Arcade zone (0xFF0000–0xFF3FFF, 16 KB):**

- Owner: arcade 68k state machine, via A5-relative addressing.
- Writers: arcade tick, `init_staging_state` factory defaults block (new), and Genesis hooks
  that intentionally communicate values to the arcade (e.g., `ARCADE_FIX_DEST_BG/FG` at
  0xFF10A0/0xFF10A4).
- A5 = 0xFF0000 is set explicitly at `arcade_tick_logic` entry on every tick.
- Mapped from arcade address 0x10C000 by the spec patch at 0x03AF04.  That patch is
  permanently inert in rastan-direct (startup_common never runs from tick entry 0x3A208),
  but it documents the intended mapping.

**Genesis BSS zone (0xFF4000+):**

- Owner: Genesis wrapper code only.
- All BSS symbols (`frame_counter`, `tick_counter`, `bg_row_dirty`, `staged_bg_buffer`,
  `staged_palette_words`, `staged_tile_words`, etc.) reside here.
- The VINT handler increments `frame_counter` at 0xFF4000 — no longer 0xFF0000.
- No arcade code accesses this region.

**Key conflicts eliminated by this split (from Andy_arcade_workram_relocation_analysis.md):**

| Old address | Old Genesis symbol      | Old arcade field    | After relocation |
|-------------|------------------------|---------------------|------------------|
| 0xFF0000    | frame_counter          | A5@(0) main state   | Separate: 0xFF4000 vs 0xFF0000 |
| 0xFF002C    | staged_bg_buffer[0]    | A5@(44) countdown   | Separate: 0xFF402C vs 0xFF002C |

---

## TASK 2 — Adaptable Genesis BSS Relocation Strategy

### Design principle

Genesis BSS base is a single constant in `link.ld`. All named BSS symbols resolve
automatically when that constant changes. No other file stores the address explicitly except
two `lea` instructions that use A5 for arcade workram access (which remain at 0xFF0000
regardless of BSS location).

### Known hardcoded addresses

After relocation there are **zero** hardcoded Genesis BSS addresses in `main_68k.s`.

- `lea 0x00FF0000, %a5` at `genesistan_hook_tilemap_plane_a:199` — this is the **arcade
  workram** base, not Genesis BSS. `ARCADE_PC080SN_STRIP_INDEX_OFFSET(%a5)` = 0x10CA(%a5)
  and `ARCADE_PC080SN_DEST_BG_OFFSET(%a5)` = 0x10A0(%a5) are arcade workram fields. This
  address must NOT change when BSS moves.
- `lea 0x00FF0000, %a5` at `init_staging_state:688` — currently unused within that function
  body (all BSS accesses there use named symbols directly). Remains correct as arcade base
  documentation but is a dead instruction. Under future refactor, this can be removed; for
  this change, leave as-is.
- `move.l #..., ARCADE_FIX_DEST_BG` at `init_staging_state:695` — writes to hardcoded
  constant 0xFF10A0 (arcade workram). Correct; no change.

### Future adaptability rule

If arcade workram ever needs to grow beyond 0xFF3FFF, raise `GENESIS_BSS_BASE` in `link.ld`
from 0xFF4000 to the next aligned boundary. Rebuild. Named symbols shift automatically.
The only manual verification needed is that no new `lea 0x00FF????` constants were
introduced that address Genesis BSS directly.

### Parameterization (current scope)

`link.ld` currently has no symbolic constant; the address is a literal. The single-source
approach is sufficient: there is exactly one place to change and the linker propagates it
everywhere. A GENESIS_BSS_BASE equate is not needed for this project scale.

---

## TASK 3 — Exact Cody Implementation Scope

Four changes in two files only.

### File 1: `apps/rastan-direct/link.ld`

**Change:** BSS base address, line 21.

```
Before:  .bss 0xFF0000 (NOLOAD) :
After:   .bss 0xFF4000 (NOLOAD) :
```

This is the complete Genesis BSS relocation. All named BSS symbols shift automatically.
No other change to `link.ld`.

---

### File 2: `apps/rastan-direct/src/main_68k.s`

**Three changes in this file.**

#### Change A: Set A5 = 0xFF0000 at arcade tick entry (arcade_tick_logic, ~line 611)

Add `lea 0x00FF0000, %a5` between `bsr rastan_direct_update_inputs` and `pea .Ltick_return`.

```asm
/* Before */
arcade_tick_logic:
    bsr     rastan_direct_update_inputs
    pea     .Ltick_return
    move.w  %sr, -(%sp)
    jmp     rastan_direct_arcade_tick_entry
.Ltick_return:
    rts

/* After */
arcade_tick_logic:
    bsr     rastan_direct_update_inputs
    lea     0x00FF0000, %a5
    pea     .Ltick_return
    move.w  %sr, -(%sp)
    jmp     rastan_direct_arcade_tick_entry
.Ltick_return:
    rts
```

This explicitly establishes A5 = arcade workram base on every tick entry. It is idempotent;
the arcade's A5-relative accesses all land in the arcade zone (0xFF0000–0xFF3FFF), away from
Genesis BSS now at 0xFF4000.

#### Change B: Fix bg_row_dirty initialization (~line 700)

```asm
/* Before */
    move.l  #0xFFFFFFFF, bg_row_dirty

/* After */
    clr.l   bg_row_dirty
```

`bg_row_dirty` is a 32-bit dirty-row bitmask. Initializing it to all-ones marks every BG
row as dirty, forcing a full 32-row VRAM flush every frame from frame 0. Starting clean
(all zeros) is correct; rows are dirtied on demand by the BG fill hook.

#### Change C: Add arcade workram factory defaults in init_staging_state (~line 750)

Add the factory defaults block immediately before the final `rts` of `init_staging_state`,
after the `staged_scroll_y_fg` clear. This mirrors `startup_common`'s factory init
(`genesistan_init_workram_direct` in `apps/rastan/src/startup_bridge.c:246–396`).

`init_staging_state` is called on every warm restart (main_68k → init_staging_state on each
cycle), so this block reinitializes arcade workram factory defaults on every restart, exactly
as startup_common does on real hardware.

The zero-fill covers 0xFF0000..0xFF00FF (64 longwords = 256 bytes = the entire arcade state
machine range). This is safe: 0xFF0000 is arcade workram after BSS relocation; no Genesis
data lives here.

```asm
    clr.w   staged_scroll_x_bg
    clr.w   staged_scroll_x_fg
    clr.w   staged_scroll_y_bg
    clr.w   staged_scroll_y_fg

    /* ------------------------------------------------------------------ */
    /* Arcade workram factory defaults at 0xFF0000                         */
    /* Equivalent to startup_common / genesistan_init_workram_direct       */
    /* Called on every warm restart; re-initializes all factory state      */
    /* ------------------------------------------------------------------ */

    /* Step 1: zero first 0x100 bytes (0xFF0000..0xFF00FF) */
    lea     0x00FF0000, %a0
    moveq   #(64-1), %d7
.Larcade_wram_clear:
    clr.l   (%a0)+
    dbra    %d7, .Larcade_wram_clear

    /* Step 2: write factory defaults */
    lea     0x00FF0000, %a0

    /* Coinage defaults: 1 coin = 1 credit */
    move.w  #1,      0x0008(%a0)    /* A5@(8)  coin1 */
    move.w  #1,      0x000A(%a0)    /* A5@(10) coin2 */
    move.w  #1,      0x000E(%a0)    /* A5@(14) */
    move.w  #1,      0x0010(%a0)    /* A5@(16) */

    /* Display control mirror */
    move.w  #0x0060, 0x0014(%a0)    /* A5@(20) = 0x0060 */

    /* DIP mirrors: active-low; hardcoded 0xFF = all switches off (factory) */
    move.w  #0x00FF, 0x0018(%a0)    /* A5@(24) = ~DIP1 */
    move.w  #0x00FF, 0x001C(%a0)    /* A5@(28) = ~DIP2 */

    /* Init flag */
    move.w  #1,      0x0026(%a0)    /* A5@(38) = 1 */

    /* Delay countdown: 160 ticks before warm restart (startup_common default) */
    move.w  #160,    0x002C(%a0)    /* A5@(44) = 160 = 0xA0 */

    /* Mode, cabinet, monitor from DIP defaults (ndip=0xFF) */
    move.w  #3,      0x002E(%a0)    /* A5@(46) mode = ndip2 & 3 = 3 */
    move.w  #1,      0x0030(%a0)    /* A5@(48) cab  = ndip1 & 1 = 1 */
    move.w  #2,      0x0032(%a0)    /* A5@(50) mon  = ndip1 & 2 = 2 */

    /* Bonus and difficulty (DIP defaults: max table indices, capped at 3) */
    move.w  #6,      0x0036(%a0)    /* A5@(54) bonus = bonus_table[3] = 6 */
    move.w  #0x2500, 0x0038(%a0)    /* A5@(56) diff  = diff_table[3]  = 0x2500 */

    /* Sprite init marker */
    move.w  #0x00AA, 0x004A(%a0)    /* A5@(74) = 0x00AA */

    /* Transition buffer block A seeding (from arcade 0x03A9E6 init helper) */
    move.w  0x0036(%a0), 0x0080(%a0)  /* A5+0x80 = A5+0x36 (bonus) */
    move.w  0x0038(%a0), 0x00B2(%a0)  /* A5+0xB2 = A5+0x38 (difficulty) */
    move.b  #1, 0x0097(%a0)           /* A5+0x97 = 1 */
    move.b  #1, 0x0098(%a0)           /* A5+0x98 = 1 */

    /* Copy block A (A5+0x80..0xBF) → block B (A5+0xC0..0xFF) */
    lea     0x0080(%a0), %a1
    lea     0x00C0(%a0), %a2
    moveq   #(16-1), %d7              /* 16 longwords = 64 bytes */
.Lblock_b_copy:
    move.l  (%a1)+, (%a2)+
    dbra    %d7, .Lblock_b_copy

    /* Restore A0 to workram base */
    lea     0x00FF0000, %a0

    /* Title init flag */
    move.w  #1,      0x0100(%a0)    /* A5@(256) = 1 */

    /* Config table: 39 bytes from ROM at Genesis 0x3B2D4 (arcade 0x3B0D4) */
    /* to A5@(320) = workram byte offset 0x0140 */
    lea     0x0003B2D4, %a1
    lea     0x0140(%a0), %a2
    moveq   #(39-1), %d7
.Larcade_cfg_copy:
    move.b  (%a1)+, (%a2)+
    dbra    %d7, .Larcade_cfg_copy

    rts
```

---

### What NOT to Change

- `genesistan_hook_tilemap_plane_a:199` `lea 0x00FF0000, %a5` — this is the arcade workram
  base for hook use of `ARCADE_PC080SN_DEST_BG_OFFSET(%a5)` and
  `ARCADE_PC080SN_STRIP_INDEX_OFFSET(%a5)`. Arcade workram stays at 0xFF0000. No change.
- `genesistan_hook_tilemap_bg_fill` — uses named BSS symbols directly (`staged_bg_buffer`,
  etc.) with no A5-relative BSS access. Linker resolves symbols to new addresses. No change.
- `init_staging_state:688` `lea 0x00FF0000, %a5` — dead instruction (A5 unused in that
  function body); still correct as arcade base. Leave as-is.
- Any `ARCADE_FIX_DEST_BG / ARCADE_FIX_DEST_FG` write in init_staging_state — these are
  intentional arcade-zone writes via hardcoded constants. No change.
- `specs/rastan_direct_remap.json` — no change.
- No other files.

---

## TASK 4 — Living WRAM Memory Map Document Spec

**Canonical path:** `docs/design/WRAM_memory_map.md`

This document is the authoritative reference for the Genesis WRAM layout. It must be kept
current whenever the address split changes, new BSS symbols are added, or arcade workram
fields are discovered.

### Required Sections

```markdown
# WRAM Memory Map — rastan-direct

**Last updated:** YYYY-MM-DD  **Build:** NNNN

## Address Space Overview

| Range              | Owner          | Size   | Notes |
|--------------------|----------------|--------|-------|
| 0xFF0000–0xFF3FFF  | Arcade workram | 16 KB  | A5 base = 0xFF0000 |
| 0xFF4000–0xFF????  | Genesis BSS    | ~N KB  | GENESIS_BSS_BASE in link.ld |
| 0xFF????+          | Available      |        |       |

## Arcade Workram Fields (0xFF0000+)

Table of all known arcade A5@(offset) fields, derived from:
- startup_common (arcade 0x03AE86)
- genesistan_init_workram_direct (apps/rastan/src/startup_bridge.c:246–396)
- MAME trace analysis / disassembly

| Offset (hex) | Address   | Width | Description              | Factory default |
|--------------|-----------|-------|--------------------------|-----------------|
| 0x0000       | 0xFF0000  | word  | Main state machine state | 0 (startup)     |
| 0x0002       | 0xFF0002  | word  | Sub-state                | 0               |
| ...          | ...       | ...   | ...                      | ...             |

## Genesis BSS Symbols (0xFF4000+)

Auto-derived from symbol.txt after each build. Listed for cross-reference.
The linker is authoritative; do not hardcode these addresses in assembly.

| Symbol                      | Address   | Width | Description |
|-----------------------------|-----------|-------|-------------|
| frame_counter               | 0xFF4000  | word  | VINT tick count |
| tick_counter                | 0xFF4002  | word  | Arcade tick count |
| ...                         | ...       | ...   | ...         |

## Write Ownership Matrix

Lists every location in 0xFF0000–0xFF3FFF that is written by Genesis code (as opposed to
arcade code), to prevent accidental stomping during future development.

| Address   | Genesis writer                | Purpose                         |
|-----------|-------------------------------|---------------------------------|
| 0xFF0000–0xFF00FF | init_staging_state factory init | Arcade factory defaults |
| 0xFF10A0  | init_staging_state (ARCADE_FIX_DEST_BG) | BG VRAM dest for hook |
| 0xFF10A4  | init_staging_state (ARCADE_FIX_DEST_FG) | FG VRAM dest for hook |
| 0xFF10A0  | genesistan_hook_tilemap_plane_a (read)  | BG dest consumed by hook |
| 0xFF10CA  | (arcade write, read by hook)  | Strip index                     |

## Change Log

| Date       | Build | Change                                     | Author |
|------------|-------|--------------------------------------------|--------|
| YYYY-MM-DD | NNNN  | Initial: BSS relocated from 0xFF0000 to 0xFF4000 | Cody |
```

### Content Rules

1. **Address ranges are hex**, always 8 digits with `0xFF` prefix.
2. **Factory defaults column** uses the actual value written by `init_staging_state`'s
   arcade defaults block — not the arcade ROM's own startup_common values, which are never
   executed in rastan-direct.
3. **Genesis BSS table** is generated from `apps/rastan-direct/out/symbol.txt` after each
   build. It need not list every symbol, but must include any symbol whose address was
   previously confused with arcade workram.
4. **Write ownership matrix** must include every address in the arcade zone that Genesis
   code writes. Any new Genesis write to 0xFF0000–0xFF3FFF requires a WRAM_memory_map.md
   update.
5. Do not include `staged_dest_ptr_bg / staged_dest_ptr_fg` in the arcade table — these are
   Genesis BSS symbols, not arcade workram fields, even though their old addresses (0xFF001C,
   0xFF0020) fell in the arcade zone before relocation.

---

## TASK 5 — Maintenance Requirements for Memory Map Document

1. **Build-triggered review:** After any build that produces a new `symbol.txt`, compare the
   BSS base address to the value in WRAM_memory_map.md. If they differ, update the document
   before committing.

2. **New BSS symbol rule:** If a new `.bss` or `COMMON` symbol is added to `main_68k.s` or
   any linked object, verify its address does not fall below `GENESIS_BSS_BASE + 0x4000`
   (i.e., does not reach into the arcade zone). Add it to the Genesis BSS table.

3. **New arcade field rule:** If a MAME trace or disassembly reveals a new A5@(offset) field
   used by the arcade, add it to the arcade workram table. If it overlaps any Genesis BSS
   symbol address (old or new), escalate immediately — do not proceed with the build.

4. **Hook write audit:** If a new Genesis hook is added that writes to any address calculable
   from A5 (0xFF0000 + offset), add that address to the write ownership matrix.

5. **Annual/milestone audit:** At each milestone build, re-derive the BSS end address from
   `symbol.txt` and verify the arcade zone has at least 4 KB of headroom below
   `GENESIS_BSS_BASE`. Current headroom: 0xFF4000 − (0xFF0167 + 1) ≈ 14.7 KB.

---

## TASK 6 — Cody Implementation Prompt

See the self-contained prompt file: **`docs/design/Cody_genesis_bss_relocation.md`**

*(Inline below for reference; that file is the authoritative version for handoff.)*

---

### Cody — Implementation: Genesis BSS Relocation

#### Background

In `apps/rastan-direct`, arcade workram (A5-relative, base = 0xFF0000) and Genesis BSS
(`.bss 0xFF0000`) share the same base address, causing two critical collisions:

1. `frame_counter` at 0xFF0000 = arcade `A5@(0)` main state → incremented by VINT,
   corrupting state dispatch every frame.
2. `staged_bg_buffer[0]` at 0xFF002C = arcade `A5@(44)` countdown → checkerboard init
   writes 0x0001 → countdown fires after 1 tick → 3.7-second delay loop → warm restart
   every ~223 frames → title screen never initializes (`title_init_block count=0`).

The fix is to move Genesis BSS upward to 0xFF4000, leaving arcade workram at its natural
0xFF0000 home. All named BSS symbols relocate automatically via the linker.

Reference: `docs/design/Andy_genesis_bss_relocation_and_wram_map_design.md`

#### Files to Change

1. `apps/rastan-direct/link.ld`
2. `apps/rastan-direct/src/main_68k.s`
3. `docs/design/WRAM_memory_map.md` (create new)

No other files.

#### Change 1: link.ld — relocate BSS base

File: `apps/rastan-direct/link.ld`, line 21.

```
Before:
  .bss 0xFF0000 (NOLOAD) :

After:
  .bss 0xFF4000 (NOLOAD) :
```

That is the complete change to link.ld.

#### Change 2: main_68k.s — add A5 setup at arcade_tick_logic entry

In `arcade_tick_logic` (around line 611), add `lea 0x00FF0000, %a5` between
`bsr rastan_direct_update_inputs` and `pea .Ltick_return`.

**Before:**
```asm
arcade_tick_logic:
    bsr     rastan_direct_update_inputs
    pea     .Ltick_return
    move.w  %sr, -(%sp)
    jmp     rastan_direct_arcade_tick_entry
.Ltick_return:
    rts
```

**After:**
```asm
arcade_tick_logic:
    bsr     rastan_direct_update_inputs
    lea     0x00FF0000, %a5
    pea     .Ltick_return
    move.w  %sr, -(%sp)
    jmp     rastan_direct_arcade_tick_entry
.Ltick_return:
    rts
```

#### Change 3: main_68k.s — fix bg_row_dirty initialization

In `init_staging_state` (around line 700):

**Before:**
```asm
    move.l  #0xFFFFFFFF, bg_row_dirty
```

**After:**
```asm
    clr.l   bg_row_dirty
```

#### Change 4: main_68k.s — add arcade workram factory defaults

In `init_staging_state` (around line 749–751), add the factory defaults block immediately
before the final `rts`. Place it after the `staged_scroll_y_fg` clear.

Reference C implementation: `apps/rastan/src/startup_bridge.c:246–396`
(`genesistan_init_workram_direct`).

**Before (last lines of init_staging_state):**
```asm
    clr.w   staged_scroll_x_bg
    clr.w   staged_scroll_x_fg
    clr.w   staged_scroll_y_bg
    clr.w   staged_scroll_y_fg

    rts
```

**After:**
```asm
    clr.w   staged_scroll_x_bg
    clr.w   staged_scroll_x_fg
    clr.w   staged_scroll_y_bg
    clr.w   staged_scroll_y_fg

    /* ------------------------------------------------------------------ */
    /* Arcade workram factory defaults at 0xFF0000                         */
    /* Equivalent to startup_common / genesistan_init_workram_direct       */
    /* Called on every warm restart; re-initializes all factory state      */
    /* ------------------------------------------------------------------ */

    /* Step 1: zero first 0x100 bytes (0xFF0000..0xFF00FF) */
    lea     0x00FF0000, %a0
    moveq   #(64-1), %d7
.Larcade_wram_clear:
    clr.l   (%a0)+
    dbra    %d7, .Larcade_wram_clear

    /* Step 2: write factory defaults */
    lea     0x00FF0000, %a0

    /* Coinage defaults: 1 coin = 1 credit */
    move.w  #1,      0x0008(%a0)    /* A5@(8)  coin1 */
    move.w  #1,      0x000A(%a0)    /* A5@(10) coin2 */
    move.w  #1,      0x000E(%a0)    /* A5@(14) */
    move.w  #1,      0x0010(%a0)    /* A5@(16) */

    /* Display control mirror */
    move.w  #0x0060, 0x0014(%a0)    /* A5@(20) = 0x0060 */

    /* DIP mirrors: active-low; 0xFF = all switches off (factory) */
    move.w  #0x00FF, 0x0018(%a0)    /* A5@(24) = ~DIP1 */
    move.w  #0x00FF, 0x001C(%a0)    /* A5@(28) = ~DIP2 */

    /* Init flag */
    move.w  #1,      0x0026(%a0)    /* A5@(38) = 1 */

    /* Delay countdown: 160 ticks before warm restart */
    move.w  #160,    0x002C(%a0)    /* A5@(44) = 160 = 0xA0 */

    /* Mode, cabinet, monitor from DIP defaults (ndip=0xFF) */
    move.w  #3,      0x002E(%a0)    /* A5@(46) mode = ndip2 & 3 = 3 */
    move.w  #1,      0x0030(%a0)    /* A5@(48) cab  = ndip1 & 1 = 1 */
    move.w  #2,      0x0032(%a0)    /* A5@(50) mon  = ndip1 & 2 = 2 */

    /* Bonus and difficulty (DIP defaults: max table indices) */
    move.w  #6,      0x0036(%a0)    /* A5@(54) bonus = bonus_table[3] = 6 */
    move.w  #0x2500, 0x0038(%a0)    /* A5@(56) diff  = diff_table[3]  = 0x2500 */

    /* Sprite init marker */
    move.w  #0x00AA, 0x004A(%a0)    /* A5@(74) = 0x00AA */

    /* Transition buffer block A seeding */
    move.w  0x0036(%a0), 0x0080(%a0)  /* A5+0x80 = A5+0x36 (bonus) */
    move.w  0x0038(%a0), 0x00B2(%a0)  /* A5+0xB2 = A5+0x38 (difficulty) */
    move.b  #1, 0x0097(%a0)           /* A5+0x97 = 1 */
    move.b  #1, 0x0098(%a0)           /* A5+0x98 = 1 */

    /* Copy block A (A5+0x80..0xBF) → block B (A5+0xC0..0xFF) */
    lea     0x0080(%a0), %a1
    lea     0x00C0(%a0), %a2
    moveq   #(16-1), %d7
.Lblock_b_copy:
    move.l  (%a1)+, (%a2)+
    dbra    %d7, .Lblock_b_copy

    /* Restore A0 to workram base */
    lea     0x00FF0000, %a0

    /* Title init flag */
    move.w  #1,      0x0100(%a0)    /* A5@(256) = 1 */

    /* Config table: 39 bytes from Genesis ROM 0x3B2D4 to A5@(0x0140) */
    lea     0x0003B2D4, %a1
    lea     0x0140(%a0), %a2
    moveq   #(39-1), %d7
.Larcade_cfg_copy:
    move.b  (%a1)+, (%a2)+
    dbra    %d7, .Larcade_cfg_copy

    rts
```

#### Change 5: Create docs/design/WRAM_memory_map.md

Create this file documenting the new WRAM layout. Use the spec in Task 4 of
`Andy_genesis_bss_relocation_and_wram_map_design.md`. Populate:

- Address space overview table with the 0xFF0000/0xFF4000 split.
- Arcade workram fields table: populate from the factory defaults written above
  (offsets 0x0000–0x0167 known; mark unknowns as `— reserved —`).
- Genesis BSS table: populate from `apps/rastan-direct/out/symbol.txt` after the build.
- Write ownership matrix: include the factory defaults block (0xFF0000–0xFF00FF) and the
  ARCADE_FIX_DEST_BG/FG entries (0xFF10A0, 0xFF10A4).
- Change log: date 2026-04-12, Build (insert next build number), "BSS relocated 0xFF0000
  → 0xFF4000; arcade factory defaults added".

#### What NOT to Change

- `genesistan_hook_tilemap_plane_a:199` `lea 0x00FF0000, %a5` — arcade workram base for
  hook access; correct as-is.
- `genesistan_hook_tilemap_bg_fill` — uses named BSS symbols; auto-relocates with linker.
- `init_staging_state:688` `lea 0x00FF0000, %a5` — dead instruction; leave as-is.
- `specs/rastan_direct_remap.json` — no change.
- No other files.

#### Build and Verify

1. `make -C apps/rastan-direct` — must succeed with zero errors and zero warnings.
2. Confirm `apps/rastan-direct/out/symbol.txt` shows `frame_counter` at `0xFF4000`
   (not `0xFF0000`).
3. Run MAME trace tool for 20 seconds.
4. Confirm acceptance criteria (Task 7 of Andy design doc).

#### AGENTS_LOG Entry

After completing the implementation and confirming the build passes, append this entry to
`AGENTS_LOG.md`:

```
[Cody - Implementation, Genesis BSS Relocation + Arcade Workram Factory Init (rastan-direct)]
Date: 2026-04-12
Changes:
  - apps/rastan-direct/link.ld: .bss base 0xFF0000 → 0xFF4000
  - apps/rastan-direct/src/main_68k.s:
      * arcade_tick_logic: add lea 0x00FF0000, %a5 before JMP
      * init_staging_state: clr.l bg_row_dirty (was 0xFFFFFFFF)
      * init_staging_state: add 256-byte zero-fill + factory defaults at 0xFF0000
  - docs/design/WRAM_memory_map.md: created
Build: [build number from build/rom_inventory.json after make]
Result: [pass/fail + key trace metric: title_init_block count]
```

#### Report Back

When complete, report in this exact format:

```
BSS relocation complete.
Build: [pass/fail]
frame_counter address in symbol.txt: [value]
title_init_block count (20s trace): [value]
bg_row_dirty in symbol.txt: [value]
WRAM_memory_map.md created: [yes/no]
AGENTS_LOG appended: [yes/no]
```

If the build fails, paste the first error line only. Do not attempt the trace if the build fails.

---

## TASK 7 — Acceptance Criteria

All of the following must be true for the implementation to be considered complete:

1. **Build passes:** `make -C apps/rastan-direct` exits 0 with no errors.

2. **BSS relocated:** `apps/rastan-direct/out/symbol.txt` shows `frame_counter` at
   `0x00FF4000` (not `0x00FF0000`).

3. **No arcade/BSS overlap:** No Genesis BSS symbol address falls below `0xFF4000`. Verify
   by scanning `symbol.txt` for any `b` or `B` type symbol with address `< 0x00FF4000`.

4. **title_init_block fires:** MAME trace (20 seconds) shows `title_init_block@000000 count > 0`.

5. **Warm restart cycle ≥ 160 frames:** `frontend_core@000000` count is consistent with
   ~160-frame cycles (count ≈ 160 × N for N warm restarts in 20 seconds, i.e. count ≈
   20 × 60 = 1200 total with count per cycle ~160 → ~4–5 restart cycles expected).

6. **bg_row_dirty starts clean:** No regression in BG rendering. The BG fill hook
   (`genesistan_hook_tilemap_bg_fill`) must fire correctly (vdp_ports changes > 0 in trace).

7. **WRAM_memory_map.md exists** at `docs/design/WRAM_memory_map.md` with all required
   sections populated.

8. **AGENTS_LOG entry appended** with build number and trace result.

---

## Design Refs

- `docs/design/Andy_arcade_workram_relocation_analysis.md` — root cause derivation
- `docs/design/Cody_arcade_workram_relocation.md` — Option A (superseded, factory
  defaults assembly content remains correct; use base 0xFF0000 not 0xFF2200)
- `apps/rastan/src/startup_bridge.c:246–396` — reference C implementation of factory init
- `apps/rastan-direct/out/symbol.txt` — current BSS layout
- `apps/rastan-direct/link.ld` — linker script to change
- `build/regions/maincpu.bin` at 0x39F80 — countdown/warm-restart function
- `states/traces/rastan_direct_video_test_build_0024_mame_20s_20260412_113620/genesis_exec_summary.txt`
  — baseline: title_init_block count=0
