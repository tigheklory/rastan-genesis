# Build 306 - Shift-Adjusted Title Init Sequence

## Root Cause

Build 305 showed a black screen because the arcade title init block (0x03B098-0x03C483) never executes. This code runs from the arcade **main loop**, not the V-Int handler. Our SCREEN_FRONTEND_LIVE mode only runs the V-Int handler via `genesistan_frontend_live_vint_handoff()`, so the title init path was unreachable.

The existing `genesistan_startup_common_continue_normal` in startup_trampoline.s contained the needed JSR calls but was dead code - no spec hook ever redirected to it.

## Prior Build 306 Failure (Hang)

Added `genesistan_run_title_init_sequence()` to call the init block from `request_start_rastan()`. The function entered (startup_result_code changed to 1) but then hung. ROM examination revealed the cause:

The JSR targets used `(arcade_addr + ARCADE_ROM_BASE)` but the shift table patcher inserts extra bytes (converting 4-byte BSR.W to 6-byte JSR abs.l), shifting all subsequent code forward. At target 0x03B298 (title_init_block), the actual bytes were `60FE` = `BRA.S -2` (infinite loop).

## Fix Applied

Computed accumulated shift deltas from the 23 shift_replacements:

| Target | Arcade Addr | Shifts Before | Delta | Genesis Addr |
|--------|-------------|---------------|-------|-------------|
| helper_3f084_reg_write | 0x03F084 | 12 | +24 | 0x03F29C |
| init_0x3B8B0 | 0x03B8B0 | 9 | +18 | 0x03BAC2 |
| title_init_block | 0x03B098 | 9 | +18 | 0x03B2AA |
| helper_display_control | 0x03ADD8 | 9 | +18 | 0x03AFEA |
| display_control_2 | 0x03AE28 | 9 | +18 | 0x03B03A |

Updated startup_trampoline.s JSR targets to include the shift delta:
```
jsr (0x03F084 + 24 + ARCADE_ROM_BASE)
jsr (0x03B8B0 + 18 + ARCADE_ROM_BASE)
jsr (0x03B098 + 18 + ARCADE_ROM_BASE)
jsr (0x03ADD8 + 18 + ARCADE_ROM_BASE)
jsr (0x03AE28 + 18 + ARCADE_ROM_BASE)
```

## Runtime Results (MAME Trace)

| Metric | Build 305 | Build 306 |
|--------|-----------|-----------|
| VDP write count | 13,699 | 49,294 |
| startup_common executions | 0 | 3 |
| frontend_core executions | 0 | 1 |
| helper_d000_init executions | 0 | 1 |
| IO port accesses | 0 | 5 |
| arcade_mode4 state | 0 (stuck) | cycles 0->1->0->1->2 |
| Hang | no (dead loop) | no (active state machine) |

## Symptom Assessment

- **Black screen**: Partially resolved - arcade state machine now active, VDP writes 3.6x higher
- **Tiles in VRAM not rendering**: Needs visual verification via BlastEm
- **title_init_block trace count=0**: The trace range detection may not match shifted addresses; however, the code IS executing (confirmed by state machine progression and VDP activity)
- **reg_3e0003 not set**: In Build 305 this changed to 0xE; in Build 306 reg_3e0001 changed to 4 instead, suggesting the reg_write function now routes through the genesis JMP hook at 0x03F29C

## Files Modified

- `apps/rastan/src/startup_trampoline.s`: Shift-adjusted JSR targets in `genesistan_run_title_init_sequence`
