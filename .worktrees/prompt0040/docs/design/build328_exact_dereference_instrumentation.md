# Build 328 Exact Dereference Instrumentation

## 1. Executive Summary
Build 328 adds a single proof-only instrumentation write immediately before the suspected faulting read in `genesistan_bulk_tilemap_commit`.

## 2. Exact Instrumentation Site
File: `apps/rastan/src/startup_trampoline.s`  
Function: `genesistan_bulk_tilemap_commit`  
Site: immediately before `move.w (%a0)+,%d4` in `.Lbulk_row_loop`.

Added instruction:

```asm
move.l  %a0, bulk_debug_pre_read_a0
```

## 3. Captured Register and Why
Captured register: `A0` (32-bit).  
Reason: `A0` is the direct source pointer used by the subsequent dereference (`move.w (%a0)+,%d4`), so this is the exact pre-read pointer state.

## 4. Debug Exposure Method
`bulk_debug_pre_read_a0` is stored in BSS (`apps/rastan/src/boot/sega.s`) and rendered via the existing debug text path in `genesistan_debug_fg_proof()` (`apps/rastan/src/main.c`) as:

`P:XXXXXXXX`

This reuses existing glyph/tile debug rendering and does not redesign UI flow.

## 5. Non-Goals
- No pointer clamping
- No read suppression
- No sanitization widening
- No caller-flow changes
- No VBlank/tile/palette/scroll redesign

## 6. Build Verification
Build command used:

```bash
source tools/setup_env.sh
make -C apps/rastan release
```

Result: build succeeded and produced `dist/Rastan_328.bin`.

## 7. Expected Runtime Result
- `P:XXXXXXXX` should be visible before freeze behavior.
- Crash may still occur because this is instrumentation only.

## 8. Final Verdict
Build 328 now captures and exposes the exact pre-dereference pointer at the likely fault site, enabling direct runtime verification of the bad pointer family without changing functional behavior.
