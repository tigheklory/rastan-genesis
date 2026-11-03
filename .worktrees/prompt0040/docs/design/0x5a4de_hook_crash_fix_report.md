# 0x5A4DE Hook Crash Fix Report

## 1. Executive Summary

The crash was caused by a single opcode error in the spec patch: JSR (`4eb9`) instead of JMP (`4ef9`). JSR pushes a return address onto the stack, causing our replacement function's RTS to return into the middle of the original (partially overwritten) arcade routine instead of to the original caller. This led to execution of the arcade's block-copy loop body with corrupted registers, eventually reaching an illegal instruction at `0x5A6FE`.

Fix: one byte change in `specs/startup_title_remap.json`.

## 2. Failure Signature

- **Symptom:** Black screen / vertical noise, crash after ~10 seconds
- **BlastEm report:** ILLEGAL INSTRUCTION at offset `0x05A6FE`
- **Location:** `0x5A6FE` is 534 bytes past `0x5A4E8` (the instruction after the JSR+NOPs), deep inside the original arcade routine's data region

## 3. Root Cause(s) Found in Current Hook

### PRIMARY: JSR Instead of JMP (Spec Patch Opcode Error)

The spec patch at `0x5A4DE` used opcode `4eb9` (JSR absolute long) instead of `4ef9` (JMP absolute long).

**With JSR (broken):**
1. Arcade caller `BSR 0x5A4DE` → pushes caller_retaddr
2. `JSR genesistan_bulk_tilemap_commit` → pushes `0x5A4E8` (next instruction)
3. Our function: movem save, VDP work, movem restore, RTS → pops `0x5A4E8`
4. Execution falls into original routine body at `0x5A4E8` with wrong registers
5. Corrupted loop runs into data → illegal instruction at `0x5A6FE`

**With JMP (correct):**
1. Arcade caller `BSR 0x5A4DE` → pushes caller_retaddr
2. `JMP genesistan_bulk_tilemap_commit` → no stack push
3. Our function: movem save, VDP work, movem restore, RTS → pops caller_retaddr
4. Returns to original caller → correct

### SECONDARY: None Found

Full audit of the assembly hook confirmed:
- **Register save/restore:** `movem.l %d2-%d7/%a2-%a6` at entry and exit — symmetric, 11 registers
- **Stack discipline:** Inner-loop stack pushes (D1 counter + D4 tile_attr) are always popped before loop continuation; skip-write path does not touch stack
- **Loop structure:** Outer D2 (columns, dbra), inner D1 (rows, dbra, reloaded from D3 template each column) — correct
- **Tile consumption:** One `move.w (%a0)+` per cell — correct, matches original routine
- **A1 decode:** Column-major: `row = cell & 0x3F`, `col = cell >> 6`, with 32-row VDP wrap — correct
- **VDP address math:** `plane_base + (row-4)*128 + col*2`, same formula as strip builder — correct
- **VDP control word:** Standard `0x40000000 | (addr & 0x3FFF) << 16 | (addr >> 14)` — correct, identical pattern to working strip builder
- **Attr extraction:** `(prio << 4) | (vflip << 3) | (hflip << 2) | pal` — matches strip builder
- **Range-miss fallback:** Saves D0-D2/A0-A1, pushes A0 arg, JSR to C, pops, restores — correct
- **Plane detection:** BG range `0xC00000–0xC04000` → base `0xC000`; FG range `0xC08000–0xC0C000` → base `0xE000` — correct
- **Row < 4 skip:** Visible bias correctly applied — rows 0-3 skipped, no VDP write

## 4. Corrected Hook Design

No change to the assembly function. The hook design is architecturally correct. Only the spec patch opcode was wrong.

## 5. Exact Changes Made

### `specs/startup_title_remap.json`

One byte change at the `0x05A4DE` opcode_replace entry:

```
BEFORE: "replacement_bytes": "4eb9{symbol:genesistan_bulk_tilemap_commit}4e714e71"
AFTER:  "replacement_bytes": "4ef9{symbol:genesistan_bulk_tilemap_commit}4e714e71"
```

- `4eb9` = JSR (Jump to SubRoutine) — pushes return address, WRONG
- `4ef9` = JMP (Jump) — no stack push, CORRECT

No assembly changes. No C changes. No additional hook points.

## 6. Build / Runtime Result

- **Build:** Compilation, assembly, and linking succeed. ROM binary produced at `apps/rastan/out/rom.bin` (3.9MB).
- **Postpatch:** Fails on a PRE-EXISTING byte mismatch at `0x0560DA` (unrelated opcode_replace entry). This is NOT caused by our change. The `0x5A4DE` patch entry itself is correct and will be applied once the `0x0560DA` issue is resolved.
- **Assembly function verified:** `genesistan_bulk_tilemap_commit` at `0x202FEC` starts with `48e7 3f3e` (correct movem.l).
- **Runtime:** Cannot test until the pre-existing `0x0560DA` postpatch failure is resolved. However, the root cause (JSR vs JMP) is definitive — there is no scenario where JSR produces correct behavior at this hook point.

## 7. Remaining Issues

1. **Pre-existing postpatch failure at `0x0560DA`:** An unrelated opcode_replace entry has a byte mismatch between expected and actual ROM content. This prevents the final patched ROM from being produced. Must be fixed separately — it is not caused by and does not interact with the `0x5A4DE` fix.
2. **Visual correctness:** Once the ROM can be produced, the hook should be tested for: title screen rendering, attract mode panels, gameplay HUD, end-round scenes, and scene transitions. The assembly logic audits clean, but visual verification is needed.
