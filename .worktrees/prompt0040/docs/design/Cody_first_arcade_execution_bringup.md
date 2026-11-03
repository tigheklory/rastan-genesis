# Cody First Arcade Execution Bring-Up

## 1. Summary
This change enables the first real arcade-execution bring-up path in `rastan-direct` by adding per-frame TC0040IOC shadow input updates, invoking relocated arcade execution every frame in the non-VBlank loop, and adding minimal non-VDP hook reachability instrumentation.

## 2. Input Read Implementation
A new routine `rastan_direct_update_inputs` was added in `apps/rastan-direct/src/main_68k.s`.

Implemented behavior:
- Reads Genesis pad ports `0xA10003` (P1) and `0xA10005` (P2)
- Uses TH low/high toggle sequence per pad:
  - write TH low
  - read
  - write TH high
  - read
- Produces active-low shadow bytes
- Updates TC0040IOC redirected shadow symbols:
  - `genesistan_shadow_input_390001`
  - `genesistan_shadow_input_390003`
  - `genesistan_shadow_input_390005`
  - `genesistan_shadow_input_390007`

## 3. Arcade Execution Integration
`arcade_tick_logic` in `apps/rastan-direct/src/main_68k.s` was updated so each non-VBlank frame does:
1. `bsr rastan_direct_update_inputs`
2. `jsr rastan_direct_arcade_tick_entry`

This is unconditional and remains outside `_VINT_handler`.

## 4. Hook Reachability Verification
`genesistan_hook_tilemap_plane_a` now performs minimal non-disruptive instrumentation:
- increments `hook_plane_a_hits` (`.word` in `.bss`)
- returns immediately

This confirms hook firing when the patched arcade path reaches the hook site, without adding VDP writes or changing control flow.

## 5. What Is Intentionally NOT Implemented
This bring-up does not implement:
- BG strip commit logic
- visual correctness fixes
- additional patcher/spec changes
- palette/scroll/sprite behavior changes
- VBlank ownership or ordering changes

## 6. Expected Behavior vs Observed Behavior
Expected:
- per-frame input shadows are no longer constant
- relocated arcade execution runs every frame
- hook counter can increment when hook site is reached

Observed in this step:
- `apps/rastan-direct` build completes successfully
- patcher executes and emits updated `build/rastan-direct/rastan_direct_patch_manifest.json`
- runtime/emulator verification remains user-side

## 7. Next Step Readiness
The codebase is now prepared for the next staged execution tasks:
- runtime validation of hook-hit progression
- first arcade-driven BG producer integration
- controlled rendering-path bring-up on top of active arcade execution
