# Cody - Implementation: Arcade Workram Relocation and Factory Init

## Background

In `apps/rastan-direct/src/main_68k.s`, `init_staging_state` sets `A5 = 0xFF0000` and then
`arcade_tick_logic` JMPs to the arcade code with A5 still = 0xFF0000. This causes two
critical conflicts:

1. `A5@(0)` = 0xFF0000 = `frame_counter` — incremented by VINT each frame. The arcade's main
   state dispatch reads A5@(0) and gets a different value every frame.

2. `A5@(44/0x2C)` = 0xFF002C = `staged_bg_buffer[0]` — the checkerboard fill sets this to
   0x0001. The arcade countdown function fires after exactly 1 tick, starting a 4-second
   warm-restart delay loop that repeats every ~223 frames. The title screen never initializes.
   This is confirmed by `title_init_block count=0` in the MAME trace.

The fix relocates arcade workram to 0xFF2200 (above all Genesis BSS) and adds startup_common
factory defaults initialization at that address.

See: `docs/design/Andy_arcade_workram_relocation_analysis.md`

---

## File to Change

`apps/rastan-direct/src/main_68k.s` — two changes only.

---

## Change 1: Set A5 = 0xFF2200 Before Arcade Tick Entry

In `arcade_tick_logic` (around line 611), add `lea 0x00FF2200, %a5` before the JMP:

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
    lea     0x00FF2200, %a5
    pea     .Ltick_return
    move.w  %sr, -(%sp)
    jmp     rastan_direct_arcade_tick_entry
.Ltick_return:
    rts
```

The `lea` is inserted between `bsr rastan_direct_update_inputs` and `pea .Ltick_return`.
Do not move it elsewhere.

---

## Change 2: Initialize Arcade Workram Factory Defaults in init_staging_state

In `init_staging_state` (around line 746–751), add the arcade workram initialization block
immediately before the final `rts`. Place it after the `staged_scroll_y_fg` clears.

Reference C implementation: `apps/rastan/src/startup_bridge.c:246–396`
(`genesistan_init_workram_direct`). This assembly block is its direct equivalent.

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

    /* Arcade workram factory defaults at 0xFF2200 */
    /* Equivalent to startup_common / genesistan_init_workram_direct */
    /* Called on every warm restart; re-initializes all factory state */

    /* Step 1: zero first 0x100 bytes (0xFF2200..0xFF22FF) */
    lea     0x00FF2200, %a0
    moveq   #(64-1), %d7
.Larcade_wram_clear:
    clr.l   (%a0)+
    dbra    %d7, .Larcade_wram_clear

    /* Step 2: write factory defaults (A5@(byte_offset) = 0xFF2200+offset) */
    lea     0x00FF2200, %a0

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

    /* Competition / alt flags: 0 for standard ROM */
    /* (already cleared by zero-fill above) */

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

    /* Restore A0 to workram base (block B copy modified A1/A2 but not A0) */
    lea     0x00FF2200, %a0

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

## Verification

After the change, rebuild (`make -C apps/rastan-direct`) and run the MAME trace tool for
20 seconds. Confirm:

1. `title_init_block@000000 count > 0` — block copy function reached for the first time
2. The warm restart cycle is longer (≥160 frames between restarts rather than 1-2 frames)
3. `frontend_core@000000` still fires but now at a lower rate consistent with 160-tick cycles

The `init_staging_state` `bg_row_dirty` fix (`move.l #0xFFFFFFFF` → `clr.l`) described in
`docs/design/Cody_bg_blockcopy_hook_implementation.md` should also be applied in the same
build (independent change, same file, different location — line 700).

---

## What NOT to Change

- Do NOT change `genesistan_hook_tilemap_plane_a` or `genesistan_hook_tilemap_bg_fill` — they
  already set `lea 0x00FF0000, %a5` at their own entry for Genesis BSS access; correct.
- Do NOT change `specs/rastan_direct_remap.json` — the patch at 0x03AF04 is in `startup_common`
  which is never called from rastan-direct's tick entry; it is permanently inert.
- Do NOT change `link.ld` or any other file.
- Implement only these two changes, nothing else.

---

## Scaffolding Audit

New labels introduced (local labels, no scaffolding):
- `.Larcade_wram_clear` — loop within init_staging_state, no removal needed
- `.Lblock_b_copy` — loop within init_staging_state, no removal needed
- `.Larcade_cfg_copy` — loop within init_staging_state, no removal needed

No new global symbols. No new sections. No new files.
