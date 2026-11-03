# 1. Executive Summary
Implemented the `arcade_tick_logic` call-convention fix by replacing `jsr rastan_direct_arcade_tick_entry` with a manually-constructed 68000 exception frame plus `jmp`, so the arcade routine ending in `rte` returns correctly.

# 2. Broken Call-Convention Identified
Verified in current source before edit:
1. `arcade_tick_logic` used `jsr rastan_direct_arcade_tick_entry`
2. `rastan_direct_arcade_tick_entry` remains the wrapper's arcade entry symbol (`.equ 0x0003A208`)
3. No other active caller of that symbol exists in `apps/rastan-direct/src/*.s`

Mismatch:
- `jsr` pushes a subroutine return PC frame (4 bytes)
- arcade entry returns via `rte` (expects exception frame: SR+PC, 6 bytes)

# 3. New Exception-Frame Construction
Implemented frame construction exactly as required:

```asm
pea     .Ltick_return
move.w  %sr, -(%sp)
jmp     rastan_direct_arcade_tick_entry
.Ltick_return:
```

Frame layout at arcade `rte` entry:
- `SP+0`: SR
- `SP+2`: return PC (`.Ltick_return`)

`rte` now pops the correctly formed frame and resumes at `.Ltick_return`.

# 4. Exact Source Edit
File edited:
- `apps/rastan-direct/src/main_68k.s`

In `arcade_tick_logic`:
- removed: `jsr     rastan_direct_arcade_tick_entry`
- added: `pea .Ltick_return`, `move.w %sr, -(%sp)`, `jmp rastan_direct_arcade_tick_entry`, label `.Ltick_return`

No other functional edits were made.

# 5. Verification of No Additional Active Fixes Applied
Checked active wrapper source (`apps/rastan-direct/src/*.s`) for other `jsr`/`bsr` calls to arcade ISR-style entry points.

Result:
- no additional active `jsr`/`bsr` calls to `rastan_direct_arcade_tick_entry`
- no additional fixes applied in this prompt

# 6. Build Verification
Executed:
- `make -C apps/rastan-direct`

Result:
- build passed
- no assembler errors
- no unresolved symbols
- ROM produced: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- numbered artifact: `dist/rastan-direct/rastan_direct_video_test_build_0013.bin`

# 7. Runtime Expectations
Expected runtime effect of this fix:
- eliminates immediate SSP drift caused by `jsr`/`rte` mismatch in `arcade_tick_logic`
- preserves current Step 4 BG row-strip commit behavior
- does not alter `_VINT_handler`, hook logic, remap spec, or patcher behavior

# 8. Final Result
`arcade_tick_logic` now enters the arcade ISR using a correctly constructed exception frame and `jmp`, allowing the arcade `rte` to return through `.Ltick_return` as intended.
