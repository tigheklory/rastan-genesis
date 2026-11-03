# Build 327 Exact `C7121A` Fault Site Audit

## 1. Executive Summary
The narrowest and most likely bad-read site is the source-word fetch inside the patched `0x5A4DE` replacement (`genesistan_bulk_tilemap_commit`). In Build 327 this routine is at ROM `0x203096` (jumped to from patched `0x5A6FA`). The likely faulting instruction is `move.w (%a0)+,%d4` at ROM `0x203196`. If `A0 == 0x00C7121A`, that instruction performs the exact invalid read reported by BlastEm.

## 2. Most Likely Faulting Instruction
Function: `genesistan_bulk_tilemap_commit`  
File: `apps/rastan/src/startup_trampoline.s`  
Runtime ROM address: `0x203096`

Most likely faulting instruction:
- ROM `0x203196`: `move.w (%a0)+,%d4`

Why this is the likely read site:
- It is a direct memory read through `A0`.
- The freeze is explicitly a read from `0xC7121A`.
- If `A0` holds `0xC7121A`, this instruction matches the failure exactly.
- The same function is the active replacement target for arcade block writer calls (`0x5A4DE` path), and it runs during the arcade tick.

## 3. Register / Pointer Carrying `C7121A`
Primary register/pointer: `A0`.

Primary interpretation:
- direct pointer dereference

In this path, `A0` is treated as source tile-data pointer and is consumed by repeated `(%a0)+` reads.

## 4. Pointer Origin
Single origin selected:
- jump-table / table lookup corruption (table-selected source pointer used by bulk tilemap path)

Most likely producing path:
- Arcade tick code that prepares `0x5A4DE` arguments by table lookup, then calls the block writer.
- Representative sequence in `build/maincpu.disasm.txt`:
  - `0x5743C`: `moveal %a2@(0),%a0` (loads source pointer)
  - `0x57466/0x57478/...`: `jsr 0x5A4DE` (patched to jump into `genesistan_bulk_tilemap_commit`)
- If the table selection/index is wrong, `A0` can become a non-ROM garbage pointer such as `0xC7121A`.

## 5. Why Current Sanitization Does Not Catch It
`sanitize_arcade_workram()` behavior (from `apps/rastan/src/main.c`):
- scans workram as longwords
- only zeros values where `(v & 0x00FF0000UL) == 0x00C00000UL` (only `0xC0xxxx` family)
- called after `genesistan_run_arcade_tick_lean` in `_VINT_arcade_mode`

Why `0xC7121A` escapes:
- `0xC7121A` is not in the `0xC0xxxx` mask family.
- crash occurs during tick-time dereference (`move.w (%a0)+,%d4`) before sanitizer runs.

## 6. Narrowest Safe Instrumentation Site
Single best site:
- `genesistan_bulk_tilemap_commit` at ROM `0x203196`, immediately before `move.w (%a0)+,%d4`.

Reason:
- This is the exact dereference site likely causing the crash.
- Captures the actual pointer at point-of-failure with minimal collateral instrumentation.

## 7. Single Root Cause
`BAD_TABLE_LOOKUP_GENERATED_DURING_TICK`

## 8. Single Next Implementation Target
Instrument exact dereference site in `genesistan_bulk_tilemap_commit` immediately before `move.w (%a0)+,%d4`.

## 9. Final Verdict
The most likely fault is a bad `A0` source pointer entering `genesistan_bulk_tilemap_commit` from the table-driven `0x5A4DE` caller path during arcade tick execution. The invalid read at `0xC7121A` is most consistent with the direct `A0` dereference at ROM `0x203196`, and current sanitization cannot prevent it because it is both too narrow (`0xC0xxxx` only) and too late (post-tick).
