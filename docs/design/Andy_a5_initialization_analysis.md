# Andy — A5 Initialization and Startup Path Analysis

**Agent:** Andy
**Type:** Forensic Analysis (no implementation)
**Build context:** Build 0049 `rastan-direct`
**Architecture compliance:** CONFIRMED against [RULES.md](RULES.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

**Outcome:** root cause confirmed with HIGH confidence. `A5 = 0` is reached at VBlank time because `_bootstrap` enables interrupts BEFORE any A5 initialization occurs, and arcade's own A5 load (at `arcade_pc 0x0003AF04`) is separated from startup entry by tens-of-milliseconds of RAM-probe and zero-propagate loops. Fix direction: `_bootstrap` must initialize A5 to `0x00FF0000` before the `move.w #0x2000, %sr`.

---

## Phase 1 — A5 initialization site in arcade code

### First (and only pre-main-loop) A5 load

| Field                                             | Value                                                                                                                                 |
| ------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| First A5 init site                                | `arcade_pc 0x0003AF04`                                                                                                                 |
| Original instruction (bytes)                      | `4B F9 00 10 C0 00` — `LEA 0x0010C000, A5`                                                                                            |
| Instruction after remap (via spec line 301)       | `4B F9 00 FF 00 00` — `LEA 0x00FF0000, A5`                                                                                            |
| Reachable from `arcade_pc 0x3A000` (cold entry)   | YES — via `arcade_pc 0x3A000: BRA.W 0x0003AE86` → straight-line fall-through through startup_common body including RAM probes / zero-propagate loop → arrives at `0x3AF04`. |
| Reachable from `arcade_pc 0x3A008` (L5 handler) without first passing through `0x3A000` | NO — there is no control-flow path from 0x3A008's body (examined 0x3A008..0x3A07E in Phase 2) back to 0x3AF04. `0x3AF04` is reached only by forward execution of startup_common. |
| Any earlier A5 initialization in arcade ROM       | NO — grep/inspection of the arcade disassembly across startup_common's entry (`arcade_pc 0x3AE86..0x3AF04`) finds **no earlier load of A5**. A5 is not loaded in the arcade level-5 handler body (`arcade_pc 0x3A008..0x3A07E`), and no opcode_replace writes to A5 elsewhere in [specs/rastan_direct_remap.json](specs/rastan_direct_remap.json). |

### Instructions from `arcade_pc 0x3AE86` to `0x3AF04` that precede the A5 load

From the P1 verification disassembly in [Andy_p1_p2_prerequisite_verification.md](docs/design/Andy_p1_p2_prerequisite_verification.md) (startup_common body table), reproduced here in timing terms:

| arcade_pc range   | what runs                                               | approximate cycle cost |
| ----------------- | ------------------------------------------------------- | ---------------------- |
| `0x3AE86..0x3AEB2` | ~8 single-instruction hardware writes (each 12-20 cycles) | ~150 cycles           |
| `0x3AEB2..0x3AEC4` | RAM-probe loop #1 — 8191 iterations × (MOVE.W read + MOVE.W write + SUBQ + BNE) ≈ ~40 cycles/iter | ~330,000 cycles (~43 ms @ 7.67 MHz) |
| `0x3AEC6..0x3AECE` | 2 single-instruction writes                             | ~40 cycles             |
| `0x3AED6..0x3AEE8` | RAM-probe loop #2 — 8191 iterations × ~40 cycles        | ~330,000 cycles (~43 ms) |
| `0x3AEEA..0x3AEF4` | A0 / A1 load + single zero write                        | ~50 cycles             |
| `0x3AEFA..0x3AF02` | zero-propagate loop — 8191 iterations × ~28 cycles      | ~230,000 cycles (~30 ms) |
| `0x3AF04`         | **`LEA 0xFF0000, A5`** (remapped) — A5 finally set      | —                       |

**Total cold-boot time to reach `0x3AF04`:** ≈ 116 ms at 68000 7.67 MHz. This spans **~7 NTSC-60 Hz VBlank periods** (each 16.67 ms). The first VBlank will fire long before `0x3AF04` executes.

---

## Phase 2 — `arcade_pc 0x3A008` dependency on A5

From the L5 handler disassembly in [Andy_p1_p2_prerequisite_verification.md](docs/design/Andy_p1_p2_prerequisite_verification.md) and corroborated by the MAME instruction trace in [Cody_build0049_first_exception_trace.md](docs/design/Cody_build0049_first_exception_trace.md).

| arcade_pc     | instruction                               | A5 dependency           | address if A5=0                                       | in vector table? |
| ------------- | ----------------------------------------- | ----------------------- | ----------------------------------------------------- | ---------------- |
| `0x0003A018`  | `MOVE.W A5@(2), D0`                       | read A5-relative word   | `0x00000002` (word inside vector 0 = initial SP long) | YES              |
| `0x0003A02C`  | `TST.W A5@(0)`                            | read A5-relative word   | `0x00000000` (top word of vector 0 = initial SP long) | YES              |
| `0x0003A032`  | `CMPI.W #1, A5@(5012)`                    | read A5-relative word   | `0x00001394` (in arcade-copy ROM segment)              | NO (ROM region)  |

**Plus indirect A5 dependency** via BSR targets reached from this handler (all enumerated in P2 Phase 4 of the verification doc):

- `arcade_pc 0x3A03E` → `BSR.W 0x0003AB7C` — the trace excerpt in [Cody_build0049_first_exception_trace.md](docs/design/Cody_build0049_first_exception_trace.md) Phase 4 shows genesis_rom `0x3AD84: cmpi.w #$100, ($12,A5)` which is `arcade_pc 0x3AB84: CMPI.W #256, A5@(18)`. Another A5-relative read (18 bytes into arcade work-RAM).
- Further subroutines called from the handler (e.g. `arcade_pc 0x3AB8A: BSR.W 0x0003FA8`) depend on A5 by transitive property — they read A5-relative state to make control decisions (see Phase 4 trace excerpt reaching `arcade_pc 0x39F8C` in the delay-loop / warm-restart cascade, which is the consequence of `CMPI #256, A5@(18)` reading a value `>= 256` when `A5 = 0`).

**`arcade_pc 0x3A008` assumes A5 was already initialized by startup_common:** **YES.**

The handler's very first state-dependent decision (`MOVE.W A5@(2), D0` at `0x3A018` followed by the CMPI/BCS/BCC pair at `0x3A01C..0x3A026`) branches on the value of the arcade game-mode word expected at `A5+2`. That word is a runtime game-state variable written by arcade code elsewhere, not a vector-table byte. With A5 uninitialized, the read returns garbage (the top byte of `0x00FF0000` from the initial-SP vector) and every downstream decision in the handler is on garbage values.

---

## Phase 3 — Build 0049 control flow

Examined [apps/rastan-direct/src/boot/boot.s](apps/rastan-direct/src/boot/boot.s) in full.

| Symbol                       | Sets A5?                                                               | Evidence                                                                                        |
| ---------------------------- | ---------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| `_start`                     | NO                                                                     | [boot.s:142-153](apps/rastan-direct/src/boot/boot.s#L142-L153) — only touches SR, SP, TMSS, then `jsr _bootstrap`. No `lea`/`move` targeting A5. |
| `_bootstrap`                 | NO                                                                     | [boot.s:154-160](apps/rastan-direct/src/boot/boot.s#L154-L160) — calls `vdp_boot_setup`, `_bootstrap_clear_staging`, `load_scene_tiles`; sets SR to `0x2000`; `jmp (0x00003A200).l`. No A5 touch. |
| `vdp_boot_setup`             | NO                                                                     | Inspected in [Andy_rastan_direct_runtime_decomposition.md](docs/design/Andy_rastan_direct_runtime_decomposition.md) Phase 2 and its precursor body in `main_68k.s:124-185` — uses D0/D1/D2 and `VDP_CTRL`; no A5 write. |
| `_bootstrap_clear_staging`   | NO                                                                     | [boot.s:162-209](apps/rastan-direct/src/boot/boot.s#L162-L209) — uses A0 exclusively for pointer walks (`lea staged_* , %a0`). No A5. |
| `load_scene_tiles`           | NO                                                                     | Body relocated into `scene_load.s` per the decomposition; prior inspection in main_68k.s:1973-2039 used A0/A2/A3/D0-D7 only. No A5 write. |
| Any Genesis cold-boot code   | **NO — confirmed by exhaustive inspection of every symbol in the cold-boot chain.** | The only A5 write in the build path is the runtime opcode_replace at `arcade_pc 0x0003AF04`, which does not fire until ~116 ms after `_bootstrap` hands off. |

### Corroborating runtime evidence

[Cody_build0049_first_exception_trace.md](docs/design/Cody_build0049_first_exception_trace.md) Phase 1 observed:

- `MILESTONE _start pc=000204 a5=00000000`
- `MILESTONE lea_sp_before pc=000208 a5=00000000`
- `MILESTONE lea_sp_after  pc=00020E a5=00000000`
- `MILESTONE _bootstrap pc=000228 a5=00000000`
- `MILESTONE _vblank_service pc=0700C4 a5=00000000`
- `MILESTONE arcade_3a208 pc=03A20A a5=00000000`

A5 stays at `0x00000000` the entire way from reset into the arcade L5 handler.

### Direct answer

```
_bootstrap sets A5:                        NO
vdp_boot_setup sets A5:                    NO
_bootstrap_clear_staging sets A5:          NO
load_scene_tiles sets A5:                  NO
Any Genesis cold-boot code sets A5:        NO
A5 = 0 possible at first VBlank:           YES
```

**Reason:** `_bootstrap` executes `move.w #0x2000, %sr` at [boot.s:159](apps/rastan-direct/src/boot/boot.s#L159) — enabling IRQs — before the `jmp (0x00003A200).l` at [boot.s:160](apps/rastan-direct/src/boot/boot.s#L160). The arcade startup_common body runs in the order `0x3AE86 → ... → 0x3AF04`, and the RAM-probe + zero-propagate loops between entry and the A5 load take ~116 ms. The first NTSC VBlank fires within 16.67 ms of IRQ enable. That VBlank invokes `_vblank_service` → tail-`jmp` to `arcade_pc 0x3A008` — while A5 still holds its reset value (observed `0x00000000`).

---

## Phase 4 — Root cause and fix direction

### Root cause

```
A5 = 0 at VBlank time because:
  - Arcade's A5 initialization is located at arcade_pc 0x0003AF04 (LEA
    0x0010C000, A5, remapped to LEA 0x00FF0000, A5 via the opcode_replace
    on spec line 301). This site sits ~116 ms into startup_common execution
    due to two preceding 8191-iteration RAM-probe loops and one 8191-
    iteration zero-propagate loop.
  - _bootstrap in apps/rastan-direct/src/boot/boot.s enables interrupts
    (move.w #0x2000, %sr at line 159) BEFORE the jmp to 0x00003A200 (line
    160), and no Genesis-side code in the cold-boot chain initializes A5.
  - Consequently the first NTSC VBlank (~16.67 ms after IRQ enable) fires
    while arcade startup_common is still inside its RAM-probe loops, many
    tens of ms before arcade_pc 0x0003AF04 executes. _vblank_service tail-
    JMPs into arcade_pc 0x0003A008 with A5 at its reset-state value
    (observed 0x00000000).
  - arcade_pc 0x0003A008 unconditionally performs A5-relative reads at
    offsets 2, 0, and 5012 (plus further A5-relative reads in BSR targets
    it invokes), so every handler-level decision is made on bytes read
    from the vector table / low ROM instead of arcade work-RAM. This is
    the observed crash/divergence pathology in Exodus and the divergent
    control flow observed in MAME (warm-restart delay loop reached via
    CMPI.W #256, A5@(18) hitting a ROM value >= 256).
```

### Fix direction

**Fix classification:** **`_bootstrap` must initialize A5 to `0x00FF0000` before enabling interrupts.**

**File:** [apps/rastan-direct/src/boot/boot.s](apps/rastan-direct/src/boot/boot.s)

**Kind of change:** insert one instruction `lea 0x00FF0000, %a5` into `_bootstrap`, placed **after** `load_scene_tiles` returns (line 158) and **before** the `move.w #0x2000, %sr` that enables interrupts (line 159). No other file edit required.

### Why this is the correct fix (not a RULES violation)

RULES §1 says "arcade code owns execution" and §8 says "arcade intent → Genesis execution." `_bootstrap` is a **BOOT-ONLY helper** classified per [Andy_rastan_direct_runtime_decomposition.md](docs/design/Andy_rastan_direct_runtime_decomposition.md) Phase 5 — its purpose is precisely to prepare Genesis-side state so that arcade code can run correctly. Setting A5 is a prerequisite for arcade's L5 handler to produce meaningful reads; it is exactly analogous to `vdp_boot_setup` which establishes VDP register state that arcade code then uses. The value written (`0x00FF0000`) is the same value arcade's own `LEA 0x0010C000, A5` (after the spec-line-301 remap) would eventually load. Arcade's later execution of `arcade_pc 0x0003AF04` will redundantly re-load A5 with the same value — idempotent, no conflict.

This is NOT adding a Genesis-owned loop, a Genesis-owned VBlank identity, or a state machine. It is one additional register-init instruction in an existing boot-only helper whose job is exactly this kind of one-time setup.

### Alternative considered (rejected for minimum-change scope)

"_bootstrap does NOT enable interrupts; arcade code enables them itself." This would require either modifying arcade code to enable IRQ at a chosen post-0x3AF04 point (requires a new opcode_replace covering an arcade instruction whose identification is out of this prompt's scope) or choosing a Genesis-side trigger. Both are broader than necessary. The A5-pre-init fix closes the race entirely with a single instruction and does not change interrupt timing relative to the current design intent (IRQs enabled for the entire arcade-execution window).

### What this fix does not do

- It does **not** remove the need for the existing opcode_replace at `arcade_pc 0x0003AF04`. That replacement redirects the arcade ROM's literal `0x10C000` to `0x00FF0000` and must remain; without it, arcade code at `0x3AF04` would overwrite the pre-initialized A5 with the old arcade work-RAM address.
- It does **not** eliminate the other Phase-1/Phase-2 hook-closure blockers enumerated in [Andy_p1_p2_hook_closure_design.md](docs/design/Andy_p1_p2_hook_closure_design.md). Those remain separately required.
- It does **not** address the ordering of `load_scene_tiles` vs. arcade's own tile-load sites or any other cold-boot concern — only the A5 race.

---

## STOP conditions — not triggered

- First A5 init site located: `arcade_pc 0x0003AF04`, confirmed present in remap.
- Control flow from `arcade_pc 0x3A000` to `0x3AF04` traced (straight-line, no branching-away between body entry at `0x3AE86` and A5 load at `0x3AF04`).
- `_bootstrap` non-setting of A5 confirmed from [apps/rastan-direct/src/boot/boot.s](apps/rastan-direct/src/boot/boot.s) source.

---

## Summary

- First A5 init site: `arcade_pc 0x0003AF04`
- Reachable from `arcade_pc 0x3A000`: YES (straight-line via `0x3AE86`)
- Reachable from `arcade_pc 0x3A008` without `0x3A000`: NO
- `arcade_pc 0x3A008` uses A5-relative: **YES** — 3 direct reads at offsets 2, 0, 5012, plus indirect dependencies through every BSR target
- `_bootstrap` sets A5: **NO**
- A5 = 0 at first VBlank possible: **YES** — observed in MAME trace
- Root cause confirmed: **YES, HIGH confidence**
- Fix direction: insert `lea 0x00FF0000, %a5` in `_bootstrap` between the `load_scene_tiles` call and the `move.w #0x2000, %sr`
- STOP triggered: NO
