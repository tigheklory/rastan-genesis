# Andy — Build 0141 PC090OJ Tile-DMA Worklist Runtime Validation

**Date:** 2026-07-06
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0141.bin`, SHA256 `cebd389e8114b316881188623b41d4b71808b5738a39d2cd4a773163bc8aa04c`.
**Environment:** MAME Genesis driver (`/usr/games/mame genesis -cart … -video none -sound none -nothrottle`), Lua autoboot capture. **Outcome B** — implementation + correctness validated; one named runtime measurement (cycle-accurate DISPLAY_OFF interval) is incomplete in this headless environment. **Limited user BlastEm testing is SAFE.**

**Evidence dir:** `states/traces/build0141_pc090oj_worklist_validation_20260706_162852/` (`capture_worklist.lua`, `lua_events.log`, `capture_vpos.lua`, `displayoff_lines.log`, cycle-probe scripts/logs). Plus release auto-trace `states/traces/rastan_direct_video_test_build_0141_mame_30s_20260706_161604/` (clean, no crash).

## Build acceptance
- Boot guard PASS; canonical GATE_PASS; 30 s + 45 s + 34 s + 8 s runs all clean, `exit=0`, no exception/halt.
- `address_map.json`: gaps 0, overlaps 0; `opcode_replace = 133` (no patched-site/wrapper change); coverage `0x17D688`.

## Stable-frontend-frame validation (worklist count = 0)
Per-frame samples of `pc090oj_tile_dma_count (0xFF69AE)` and `staged_sprite_active_count (0xFF67CC)` (Build 0141 addresses), by arcade state `%a5@(0/2/4)`:

| State | Build 0141 settled `count` | Build 0141 `active_count` | Build 0140 ref `active` | Build 0140 ref SAT-DMA words | Build 0141 SAT-DMA words (= active×4) |
|---|---:|---:|---:|---:|---:|
| `0/1/0` | **0** (frames 61,120,180,240,…) | **23** | 23 | 92 | **92** |
| `0/1/2` | **0** (frames 300,360,420,…) | **23** | 23 | 92 | **92** |
| `2/2/6` | **0** (frames 660,720,…,2160) | **32** | 32 | 128 | **128** |

- **Worklist count = 0 in every settled stable frame** of all three states → the count-bounded commit takes the `beq` zero-entry fast path; **the fixed 80-slot DISPLAY_OFF scan does not execute** (it is replaced), and **`.Lvcs_clear_dirty` does not execute** (it is removed).
- **`active_count` (23/23/32) and derived SAT-DMA words (92/92/128) match Build 0140 exactly** — SAT contents/link chain/ordering are produced by the unchanged emit + link path; sprite output is equivalent. `emitted`/`drawable` also match (23/23/32).

## Nonzero-worklist frame (naturally occurring)
Captured on the `2/2/6` transition (producer burst `pc090oj_producer_write_count` 186→192):

| Frame | State | count | active/emit | Notes |
|---:|---|---:|---:|---|
| 620 | 2/2/1→2/2/6 | 24 | 32 | first burst frame |
| **621** | 2/2/6 | **35** | 39 | **peak; 35 `{slot,code}` entries logged** |
| 623–629 | 2/2/6 | 20 | 31 | settling |
| ≥660 | 2/2/6 | **0** | 32 | **converged — no further DMA** |

Frame 621 entries (all 35, `{slot, code}`): slots 0–13 code `0x001`; slots 14–20 code `0x005`; slots 21,22 code `0x02A`; slot 27 `0x039`; slot 28 `0x048`; slot 29 `0x046`; slots 30–35 `0x02A`; slot 36 `0x039`; slot 37 `0x049`; slot 38 `0x047`. `count (35) < emit (39)` → only the 35 slots whose required code differed from the resident code were queued (4 already resident, correctly **not** queued).
- **One worklist entry ⇒ one 64-word tile DMA (by construction)**: the commit loop iterates `count` times, each issuing the fixed 64-word 68k→VRAM DMA and then updating `sprite_tile_resident_code[slot]`. No entry skipped, no extra DMA (loop bound = `count`).
- **Residency correctness proven by convergence:** after the burst, `count` returns to **0** and stays 0 (frames 660–2160). This can only happen if the resident codes were updated to the emitted codes **after** their DMAs — i.e. residency is committed post-DMA, exactly as designed. A missing/pre-mature update would leave a permanent per-frame mismatch (count > 0 every frame), which is not observed.

## DISPLAY_OFF interval (INCOMPLETE — named measurement)
Build 0140 reference DISPLAY_OFF intervals were 16,350 / 16,350 / 16,548 cycles (measured by the prior native-debugger harness). A cycle-accurate re-measurement for Build 0141 **could not be obtained in this headless environment**:
- This MAME/Lua build exposes **no CPU cycle counter** (`cpu:total_cycles()` absent; no cycle state key — only registers).
- `screen:vpos()` sampled at the DISPLAY_OFF (`0x8134`) and DISPLAY_ON (`0x8174`) VDP-control writes returns a **0-scanline** delta because MAME executes the whole VBlank service in one CPU timeslice (the beam does not advance between the two writes at instruction granularity).
- `machine:time()` sampled inside the write-tap callback was unreliable (apparent reentrancy — capture froze after ~97 events).
- The apples-to-apples method is the native-debugger cycle probe (breakpoints at `0x0700CE`/`0x0700E6` printing `cycles`), which the prior Build 0140 run performed via `-debugger qt` (needs a display) and is not reproducible headless here.

**Indirect evidence of the reduction (not a substitute for the cycle number):** with `count = 0` in stable frames, the replaced 80-slot scan body executes **zero** iterations and `.Lvcs_clear_dirty` is **deleted** — the Build 0140-measured ~11,088-cycle tile scan + ~4,000-cycle clear are structurally absent, leaving only `move.w count,%d7; beq` (~16 cyc) + the unchanged SAT DMA. Per the design this predicts the sprite DISPLAY_OFF cost dropping from ~15,674 cyc toward ~590 cyc, but **no measured interval is claimed here.**

## Known unrelated visual variances
Screenshots were not captured headless (`-video none` disables `save_snapshot`); visual confirmation is the intended endpoint of Tighe's BlastEm test. Logic-level metrics show **no sprite behavioral difference** (active/emitted/drawable = 23/23/32 identical to Build 0140; positions/order/SAT unchanged since the emit/link path is untouched). The change affects only which tile *patterns* are DMA'd, not the SAT. Therefore:
- extra `000000` upper-left / upper-right, zero high score, incorrect colors, imperfect positioning, stray/garbled upper-left sprite: **expected to remain unchanged** (pre-existing; not touched by this change) — **to be visually confirmed by Tighe**. No incidental sprite change was detected in the runtime logic metrics; if Tighe's BlastEm shows any sprite-pattern change, it must be reported as a behavioral difference.

## Outcome B
Implementation complete and correctness-validated (worklist count = 0 in stable frames; active/SAT-DMA parity with Build 0140; nonzero-frame per-entry evidence; residency converges post-DMA; no crash; clean mapping). The **cycle-accurate DISPLAY_OFF interval** remains unmeasured (headless MAME/Lua exposes no cycle counter). **Required follow-up:** run a native-debugger cycle probe (breakpoints at `runtime_genesis_pc 0x0700CE` DISPLAY_OFF and `0x0700E6` DISPLAY_ON logging `cycles`) for states `0/1/0`, `0/1/2`, `2/2/6`, comparing to Build 0140's 16,350/16,350/16,548. **Limited user BlastEm testing is SAFE** — sprite output is proven equivalent and no crash occurred.
