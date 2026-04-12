# Andy — BG Fill Hook No-Visible-Output Diagnosis

## Ground Truth

- Hook implemented: `genesistan_hook_tilemap_bg_fill` at Genesis ROM `0x000702D2`
- Patch applied: arcade PC `0x03AD44` → Genesis ROM `0x03AF44` = `4E B9 00 07 02 D2 4E 71`
- Build passes, no crash, 59.9 fps in BlastEm
- Plane B still shows checkerboard; no visible Title BG

---

## Task 1 — Patch/Hook Chain Structural Check

**patch/hook chain structurally correct: YES (with one exception — see Task 3)**

- `0x03AD44` entry present in `specs/rastan_direct_remap.json` ✓
- `replacement_bytes` uses `{symbol:genesistan_hook_tilemap_bg_fill}` ✓
- `genesistan_hook_tilemap_bg_fill` in `required_symbols` ✓
- Symbol resolved; JSR target `0x000702D2` present in built ROM ✓

---

## Task 2 — Hook Logic End-to-End Trace

**hook logic should produce staged writes if called: YES**

Reading the implementation at [apps/rastan-direct/src/main_68k.s](apps/rastan-direct/src/main_68k.s) lines 369–454:

| Step | Code | Assessment |
|------|------|------------|
| A0 range check | `andi.l #0xFFFFFF, %d2; cmpi.l #0xC00000, blo; cmpi.l #0xC04000, bhs` | Correct |
| D1=0 guard | `move.w %d1, %d6; tst.w %d6; beq done` | Correct |
| Code lookup | `move.w %d0, %d3; andi.w #0x3FFF; add.w %d3; move.w 0(%a2,%d3.w), %d3` | Correct |
| Attr: `swap %d4` to get D0[31:16] | Correct |
| Two-shift extraction bits 14/15/13 | `lsr.w #8; lsr.w #6/7/5` style | Correct |
| `nametable_word = vram_slot \| attr` | `or.w %d5, %d3` | Correct |
| Row/col from A4 offset | `subi.l #0xC00000; lsr.l #2; andi.w #0x3F; lsr.w #6; andi.w #0x1F` | Correct |
| Buffer write | `row*128 + col*2 → staged_bg_buffer` | Correct |
| Dirty bit | `bset %d5, %d0` (d5=row) | Correct |
| Boundary exit | Re-checks A4 vs 0xC04000 each iteration | Correct |
| Loop | `subq.w #1, %d6; bne.s` | Correct |

The hook implementation is logically correct on all counts.

---

## Task 3 — Most Likely Failure Point

**most likely failure point: `4E 71` (NOP) at replacement_bytes position +6 instead of `4E 75` (RTS)**

This is a concrete, verifiable bug in the patch spec — not a speculation.

### The evidence

Original FUNC B bytes at Genesis ROM `0x03AF44`:
```
+0: 20 C0   MOVE.L D0,(A0)+
+2: 53 41   SUBQ.W #1,D1
+4: 66 FA   BNE.S -4
+6: 4E 75   RTS              ← the function's return to its caller
```

Applied patch bytes at `0x03AF44`:
```
+0: 4E B9   JSR.L
+2: 00 07   |
+4: 02 D2   | → 0x000702D2 (hook)
+6: 4E 71   NOP              ← WRONG: should be 4E 75 (RTS)
```

### The call sequence with the NOP

1. Arcade code executes `BSR 0x03AD44` → pushes `CALLER_RET` onto stack, jumps to `0x03AF44`
2. `JSR 0x000702D2` → pushes `0x03AF4A` onto stack, jumps to hook
3. Hook runs: saves registers, checks range, computes nametable_word, fills loop, restores registers, `RTS`
4. Hook `RTS` pops `0x03AF4A` → PC = `0x03AF4A` (the NOP)
5. `NOP` at `0x03AF4A` executes
6. PC falls to `0x03AF4C` → `MOVE.W #8, D1` (the instruction that follows FUNC B in ROM)
7. **`CALLER_RET` is still on the stack** — the original FUNC B's `RTS` that would have popped it was replaced by NOP

The original `4E 75` RTS at position +6 is what returned to the caller of FUNC B. The replacement NOP provides no return. After the hook returns to `0x03AF4A`, execution falls into the arcade code immediately following FUNC B in the ROM, with a stale return address on the stack.

### Why the existing 0x055968 patch uses NOPs correctly

The original function at `0x055968` (38 bytes) ends with `BNE.S -18` — a loop-back branch, not an RTS. That function returns by falling through after the loop exits. The NOPs in the 0x055968 replacement mirror that fall-through behavior. For FUNC B, the original DOES end with RTS, so the replacement must also end with RTS.

---

## Task 4 — Screenshot Reconciliation

**Why BlastEm no longer crashes:**
The patch at `0x03AF44` intercepts all FUNC B calls before any `MOVE.L D0,(A0)+` executes. The range check rejects calls with `A0` outside `[0xC00000, 0xC04000)` — including the sprite RAM init calls that previously drove `A0` to `0xDFFFFE`. Those calls now exit cleanly via the hook's `RTS` (returning to the NOP, then falling through) without writing to the VDP or unmapped Genesis space. No `0xDFFFFE` write → no machine freeze. ✓

**Why checkerboard persists:**
The fall-through execution after the NOP means every FUNC B call leaves `CALLER_RET` stranded on the stack. The game's call chain executes code at `0x03AF4C` and onward with a corrupted stack frame. Most likely consequence: the frame execution at some point pops the wrong return address via `RTS`, landing in an earlier part of the arcade's initialization or scene-setup code that re-runs `init_staging_state` (or equivalent), resetting `staged_bg_buffer` back to the checkerboard. Even if the hook's writes execute correctly, they are overwritten by the re-run initialization before `vdp_commit_bg_strips_if_dirty` can flush them.

**Why Exodus Plane B looks wrong:**
Same root cause — `staged_bg_buffer` stays in its init-checkerboard state (tiles 0x0001/0x0002) because the hook writes are immediately overwritten or the dirty bits are never flushed before re-init occurs. The two large colored blocks visible in the Exodus plane viewer are tiles 1 and 2 rendered as solid-color 8×8 blocks from the debug palette, at the Exodus plane viewer's zoom scale.

**Why game still runs at 59.9 fps:**
The fall-through to `0x03AF4C` = `MOVE.W #8, D1` likely coincides with the return point of the `BSR` that called FUNC B in the first place (the instruction after the `BSR` in the caller). Execution therefore continues in approximately the right place in the calling function, despite the stale return address. The game main loop uses `BRA`/`JMP` to loop indefinitely (not `RTS` at the outer level), so the stale return addresses accumulate on the stack but don't immediately cause a crash.

---

## Task 5 — Called vs. Not Called

**Selection: B — hook called but implemented incorrectly (incorrect patch spec)**

Justification:
- The crash being gone is direct evidence the hook IS being reached — the range check is executing for sprite-RAM calls and preventing the `0xDFFFFE` write
- The hook itself contains no bugs (Task 2 confirms correct logic)
- The hook IS writing to `staged_bg_buffer` during BG-range calls — but the NOP at position +6 corrupts the execution flow AFTER the hook returns, preventing the writes from persisting to the VDP commit cycle

The failure is not inside the hook — it is in the patch spec that deploys it.

---

## Task 6 — Single Root Cause

**Root cause: `replacement_bytes` for arcade PC `0x03AD44` ends with `4E 71` (NOP) instead of `4E 75` (RTS).**

The original FUNC B function ends with `RTS` at bytes +6-7 (`4E 75`). The replacement overwrites that `RTS` with `NOP` (`4E 71`). After the hook executes and its own `RTS` returns to `0x03AF4A`, there is no `RTS` to complete the call/return contract of the original FUNC B. Execution falls through to `0x03AF4C` with `CALLER_RET` stranded on the stack, corrupting every subsequent frame that calls FUNC B.

The hook logic is correct. The patch spec is wrong. This bug originated in Andy's spec (`Cody_bg_fill_hook_implementation.md`) and was carried through unchanged into Prompt 231S. Cody correctly implemented the spec as written.

---

## Task 7 — Single Next Step

**Minimal Cody fix: change `4e71` to `4e75` in `replacement_bytes` for the `0x03AD44` entry in `specs/rastan_direct_remap.json`. Rebuild.**

```json
"replacement_bytes": "4eb9{symbol:genesistan_hook_tilemap_bg_fill}4e75"
```

`4E 75` = `RTS`. This restores the call/return contract: after the hook executes, `RTS` at `0x03AF4A` pops `CALLER_RET` and returns to the original caller of FUNC B. No other changes required.
