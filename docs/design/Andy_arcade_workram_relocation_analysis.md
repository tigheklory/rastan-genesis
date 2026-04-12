# Andy - Analysis: Arcade Workram Overlap Root Cause and Fix

## Problem Statement

The MAME trace for Build 0024 shows `title_init_block count=0` — the block copy at 0x05A4E0
never fires. PCs 0x3A192–0x3A19E sampled on every frame: these are arcade 0x39F92–0x39F9E,
the inner busy-wait loop of the warm restart delay sequence. The game soft-resets every ~223
frames and never reaches the title initialization.

The user correctly recalled this is an initialization check failure, matching behavior
encountered in the SGDK version before `startup_common` was bypassed there.

---

## Root Cause

### Arcade Workram Overlays Genesis BSS

`init_staging_state` sets A5 = 0xFF0000. `arcade_tick_logic` JMPs to arcade code with A5
still = 0xFF0000. The arcade uses A5-relative addressing for its entire state machine. So
arcade workram A5@(N) = 0xFF0000 + N, which is exactly the Genesis BSS section.

Critical conflicts (from `apps/rastan-direct/out/symbol.txt`):

| Arcade workram | Address   | Genesis BSS symbol        | Value after init_staging_state |
|----------------|-----------|---------------------------|-------------------------------|
| A5@(0)  state  | 0xFF0000  | `frame_counter`           | 0, then incremented by VINT   |
| A5@(2)  sub    | 0xFF0002  | `tick_counter`            | 0 (cleared but not modified)  |
| A5@(6)  coin1  | 0xFF0006  | `bg_row_dirty` (low word) | 0xFFFF (set to 0xFFFFFFFF)    |
| A5@(44) timer  | 0xFF002C  | `staged_bg_buffer[0]`     | 0x0001 (checkerboard cell)    |

### Conflict 1: A5@(0) = frame_counter

The VINT handler (`_VINT_handler`) does `addq.w #1, frame_counter` every VBlank. This
increments 0xFF0000. The arcade tick reads A5@(0) = 0xFF0000 and uses it as the main state
machine dispatch. With `frame_counter` incrementing each frame, the arcade's main state jumps
to a different handler on every tick — state dispatch is completely unpredictable.

### Conflict 2: A5@(44/0x2C) = staged_bg_buffer[0]

`init_staging_state` fills `staged_bg_buffer` (at 0xFF002C) with a checkerboard pattern.
The first cell (row=31, col=63): `d6=31 XOR d5=63 = 48`, `48 & 1 = 0` → writes 0x0001.
After init_staging_state, 0xFF002C = 0x0001.

The arcade tick calls the countdown function at arcade 0x39F80 (Genesis 0x3A180):
```
TST.W   A5@(0x002C)          ; test 0xFF002C = staged_bg_buffer[0] = 0x0001
BEQ.S   → delay+warm_restart ; if 0, fire warm restart
SUBQ.W  #1, A5@(0x002C)     ; 0x0001 → 0x0000
RTS
```

- Tick 1 (frame_counter = 1): countdown = 0x0001 → decrement → 0x0000, RTS
- Tick 2 (frame_counter = 2): countdown = 0x0000 → fall to delay loop

Delay loop: D1 = 0x000A0000 = 655360 iterations × ~38-46 clocks/iter at 7.67MHz ≈ 3.7 seconds.
Then warm restart: MOVEA.L ($0000).W, SP; MOVEA.L ($0004).W, A0; JMP (A0) → Genesis 0x202 →
_start → main_68k → init_staging_state → staged_bg_buffer[0] = 0x0001 again → repeat.

**This explains the exact MAME trace observation**: 223 frames/cycle = 1 tick + ~222-frame
delay loop (3.7 sec × 60 fps = 222). title_init_block count = 0 because the game never
advances past the first 2 ticks.

The startup_common factory default for A5@(44) is 160 (= 0xA0). On real arcade hardware,
the game runs 160 ticks of the title screen before warm-restarting. In rastan-direct,
init_staging_state accidentally writes 0x0001 (the checkerboard value) instead.

---

## Fix

### Fix 1: Relocate Arcade Workram Base to 0xFF2200

Genesis BSS occupies 0xFF0000–0xFF212B (ends after `staged_tile_words`). Set arcade workram
base (A5) to 0xFF2200 — fresh WRAM with no Genesis BSS overlap.

In `arcade_tick_logic`, add `lea 0x00FF2200, %a5` before the JMP. This explicitly establishes
A5 for each arcade tick entry. It is idempotent: the arcade uses A5-relative addressing and
does not modify A5 itself.

The spec patch at 0x03AF04 (`LEA 0x10C000,A5` → `LEA 0xFF0000,A5`) is in `startup_common`
(0x03AE86), which is never reached from rastan-direct's tick entry at 0x3A208. That patch is
permanently inert. No change to `rastan_direct_remap.json` needed.

The hook functions (`genesistan_hook_tilemap_plane_a`, `genesistan_hook_tilemap_bg_fill`)
already set A5 = 0xFF0000 at their own entry points (lines 194, 688) for Genesis BSS access.
These are unaffected by the arcade workram relocation.

### Fix 2: Initialize Arcade Workram Factory Defaults at 0xFF2200

`init_staging_state` is called on every warm restart (main_68k → init_staging_state at each
cycle). Adding arcade workram init there mirrors startup_common's behavior: every restart
reinitializes the factory defaults.

Reference: `genesistan_init_workram_direct()` in `apps/rastan/src/startup_bridge.c` (lines
246–396). The assembly translation uses hardcoded ndip1/ndip2 = 0xFF (DIP switches all off =
active-low defaults; arcade factory standard).

Key values:
- A5@(0x0008) = 1             — coin1 counter
- A5@(0x000A) = 1             — coin2 counter
- A5@(0x000E) = 1             — coinage field
- A5@(0x0010) = 1             — coinage field
- A5@(0x0014) = 0x0060        — display control mirror
- A5@(0x0018) = 0x00FF        — ~DIP1 mirror
- A5@(0x001C) = 0x00FF        — ~DIP2 mirror
- **A5@(0x0026) = 1**         — init flag (A5@(38))
- **A5@(0x002C) = 160**       — delay countdown (A5@(44)) ← prevents immediate warm restart
- A5@(0x002E) = 3             — mode (from ndip2 & 0x03)
- A5@(0x0030) = 1             — cabinet type (ndip1 & 0x01)
- A5@(0x0032) = 2             — monitor flip (ndip1 & 0x02)
- A5@(0x0036) = 6             — bonus value (bonus_table[3])
- A5@(0x0038) = 0x2500        — difficulty (diff_table[3])
- A5@(0x004A) = 0x00AA        — sprite init marker (A5@(74))
- A5@(0x0080) = A5@(0x0036)   — block A seed from bonus (via word copy)
- A5@(0x00B2) = A5@(0x0038)   — block A seed from difficulty
- A5@(0x0097) byte = 1        — block A detail
- A5@(0x0098) byte = 1
- Copy A5+0x80..0xBF → A5+0xC0..0xFF  (block B = copy of block A)
- **A5@(0x0100) = 1**         — title init flag (A5@(256))
- 39 bytes from Genesis ROM 0x3B2D4 (arcade 0x3B0D4) → A5@(0x0140) — config table

Note: A5@(0) = A5@(2) = A5@(4) = 0 (initial state 0, sub-state 0, step 0) — cleared by the
initial zero-fill. State 0 at dispatch table offset 0x3A06E + 0x0840 = 0x3A8AE handles
initial startup and sets state to proper values.

### Zero-fill scope

Clear 64 longwords (0x100 bytes) at 0xFF2200 before writing defaults. This handles all
words in the 0x00–0xFF byte range. The config table and block areas beyond 0xFF are written
explicitly.

---

## Expected Outcome After Fix

- A5 = 0xFF2200 at arcade tick entry: no overlap with frame_counter, tick_counter, or staged_bg_buffer
- A5@(0) = 0 (state 0 = startup), not frame_counter
- A5@(0x2C) = 160: countdown fires after 160 ticks (not 1 tick)
- Game runs 160 ticks of title init, then warm-restarts, then runs 160 ticks again (normal attract loop)
- `title_init_block@000000 count > 0` in next MAME trace
- Block copy hook at 0x05A4E0 (`genesistan_hook_tilemap_bg_blockcopy` — pending implementation) can fire

The `init_staging_state` `clr.l bg_row_dirty` fix (Cody_bg_blockcopy_hook_implementation.md)
remains needed and is unaffected by this change.

---

## Files to Change

- `apps/rastan-direct/src/main_68k.s` — two changes only

## Design Refs

- `apps/rastan/src/startup_bridge.c:246–396` — reference init_workram_direct (SGDK version)
- `apps/rastan-direct/out/symbol.txt` — BSS addresses
- `build/regions/maincpu.bin` at 0x39F80 — countdown/warm-restart function
- `AGENTS_LOG.md` lines 5958–5982 — startup_common factory defaults (SGDK derivation)
