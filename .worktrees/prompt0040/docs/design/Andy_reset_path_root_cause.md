# Andy — Reset Path Root Cause: arcade_pc 0x00039F9E

**Agent:** Andy
**Type:** Forensic Analysis (no design, no implementation)
**Build context:** current `rastan-direct`
**Source of evidence:** [build/regions/maincpu.bin](build/regions/maincpu.bin), [build/maincpu.disasm.txt](build/maincpu.disasm.txt)

**Outcome: STOP.** Two distinct code paths reach arcade_pc `0x00039F9E`,
each with a different condition. Existing disassembly evidence cannot
identify which path is taken at runtime. Additional trace data required
(specific capture ask in Phase 5).

**Architecture compliance:** CONFIRMED against [RULES.md](RULES.md) and [ARCHITECTURE.md](ARCHITECTURE.md).
This analysis proposes no fix, no design change, no architectural reinterpretation.

---

## Address-space legend

Every address in this document is labeled:
- `arcade_pc <value>` — a PC value in the arcade ROM address space.
  Arcade ROM bytes live at file offset `arcade_pc` inside
  `build/regions/maincpu.bin`. On Genesis the same bytes live at
  Genesis ROM offset `arcade_pc + 0x200`.
- `HW_ADDRESS <value>` — a runtime memory address on Genesis
  hardware. Work RAM is at `0x00FF0000..0x00FFFFFF`. A5 is used by
  arcade code as the work-RAM base pointer = `0x00FF0000`, so
  `A5@(N)` maps to `HW_ADDRESS 0x00FF0000 + N`.

---

## Phase 1 — Reset path disassembly

**PC:** `arcade_pc 0x00039F9E`
**Instruction:** `MOVEA.L (0x00).W, SP` (opcode bytes `2E 78 00 00`) — loads SP from the first long in ROM at `arcade_pc 0x0000` (= `0x0010DE00` in the unmodified arcade ROM; = `0x00FF0000` in Genesis boot.s vector table after the Genesis reset vector is overlaid).
**Target:** falls through to `arcade_pc 0x00039FA2` / `0x00039FA6` which together form the warm-restart trampoline (`MOVEA.L (0x04).W, A0; JMP (A0)`). The ultimate JMP target is whatever long is stored at `arcade_pc 0x0004` — in the current Genesis build, `0x00000202` (Genesis `_start`); in the unmodified arcade ROM, `0x0003A000` (arcade startup_common).
**Uses ROM[0x0004]:** YES — the two instructions at `arcade_pc 0x00039FA2` and `0x00039FA6` perform the ROM[0x0004] read and indirect JMP.

### ±64 byte disassembly

From [build/maincpu.disasm.txt:72890-72904](build/maincpu.disasm.txt) corroborated against [build/regions/maincpu.bin](build/regions/maincpu.bin) at file offset `0x39F40..0x39FAF`:

| arcade_pc      | bytes                  | mnemonic                     | role                                                        |
| -------------- | ---------------------- | ---------------------------- | ----------------------------------------------------------- |
| `0x00039F40..7F` | `FF FF ...`           | (padding / unused)           | —                                                           |
| `0x00039F80`   | `4A 6D 00 2C`          | `TST.W 0x2C(A5)`             | read-test the word at `HW_ADDRESS 0x00FF002C`               |
| `0x00039F84`   | `67 06`                | `BEQ.S 0x00039F8C`           | **Conditional branch into warm-restart cascade** (path A)   |
| `0x00039F86`   | `53 6D 00 2C`          | `SUBQ.W #1, 0x2C(A5)`        | decrement countdown at `HW_ADDRESS 0x00FF002C`              |
| `0x00039F8A`   | `4E 75`                | `RTS`                        | exit without warm restart (countdown not yet expired)       |
| `0x00039F8C`   | `22 3C 00 0A 00 00`    | `MOVE.L #0x000A0000, D1`     | preload delay-loop counter                                  |
| `0x00039F92`   | `20 38 00 00`          | `MOVE.L (0x00).W, D0`        | memory-touch read of `arcade_pc 0x0000` into D0 (discarded) |
| `0x00039F96`   | `04 81 00 00 00 01`    | `SUBI.L #1, D1`              | decrement delay counter                                     |
| `0x00039F9C`   | `66 F4`                | `BNE.S 0x00039F92`           | **Inner delay-loop branch** — falls through to 0x39F9E when D1 hits 0 |
| `0x00039F9E`   | `2E 78 00 00`          | `MOVEA.L (0x00).W, SP`       | warm-restart: load SP from ROM[0x0000]                      |
| `0x00039FA2`   | `20 78 00 04`          | `MOVEA.L (0x04).W, A0`       | warm-restart: load A0 from ROM[0x0004]                      |
| `0x00039FA6`   | `4E D0`                | `JMP (A0)`                   | warm-restart: jump through A0                               |
| `0x00039FA8`   | `65 02`                | `BCS.S 0x00039FAC`           | **Conditional branch: skip warm restart if C set** (path B) |
| `0x00039FAA`   | `60 E0`                | `BRA.S 0x00039F8C`           | enter warm-restart cascade (C clear case of path B)         |
| `0x00039FAC`   | `4E 75`                | `RTS`                        | exit without warm restart (path B, C-set case)              |
| `0x00039FAE..0x00039FFF` | `FF FF ...`  | (padding)                    | —                                                           |

---

## Phase 2 — Backtrace

The dominant fall-through path to `arcade_pc 0x00039F9E` is:
`0x39F9C BNE.S` (not taken) → `0x39F9E`. Walking backward past that:

| arcade_pc      | instruction                     | role                                                                                                                |
| -------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `0x00039F9E`   | `MOVEA.L (0x00).W, SP`          | target of this investigation                                                                                        |
| `0x00039F9C`   | `BNE.S 0x00039F92`              | **First conditional branch.** Falls through to 0x39F9E when D1 reaches 0 after the `SUBI.L #1` at 0x39F96           |
| `0x00039F96`   | `SUBI.L #1, D1`                 | sets Z flag used by the BNE above                                                                                   |
| `0x00039F92`   | `MOVE.L (0x00).W, D0`           | memory-touch per delay-loop iteration                                                                               |
| `0x00039F8C`   | `MOVE.L #0x000A0000, D1`        | pre-loads D1 with 655360 (= 0xA0000) — the loop-entry seed. Loop termination at D1 == 0 is **structurally forced**  |
| —              | —                               | backtrace continues to the entry points of the containing routine                                                   |

The BNE at `0x39F9C` is the literal first conditional branch, but its
condition is structurally-forced (given entry at 0x39F8C with D1 =
0xA0000, the loop MUST terminate and MUST fall through to
0x39F9E). So it is not the *deciding* branch. The deciding branches
are one level up — the branches that direct control to 0x39F8C in
the first place. Two exist:

### Path A — primary entry at `arcade_pc 0x00039F80`

| arcade_pc      | instruction                 | role                                                                                                   |
| -------------- | --------------------------- | ------------------------------------------------------------------------------------------------------ |
| `0x00039F80`   | `TST.W 0x2C(A5)`            | test word at `HW_ADDRESS 0x00FF002C` — sets Z flag if zero                                             |
| `0x00039F84`   | `BEQ.S 0x00039F8C`          | **Path-A deciding branch.** Taken when `HW_ADDRESS 0x00FF002C == 0` — enters warm-restart cascade      |
| `0x00039F86`   | `SUBQ.W #1, 0x2C(A5)`       | decrement countdown (fall-through case — countdown still running)                                      |
| `0x00039F8A`   | `RTS`                       | return to caller without warm restart                                                                  |

**Caller of 0x00039F80**: `arcade_pc 0x0003AB6E: BRA.W 0x00039F80` (from [maincpu.disasm.txt:73758](build/maincpu.disasm.txt)). Unconditional branch thunk. The actual caller of 0x0003AB6E is further upstream and not in scope for this phase.

### Path B — secondary entry at `arcade_pc 0x00039FA8`

| arcade_pc      | instruction                  | role                                                                                                     |
| -------------- | ---------------------------- | -------------------------------------------------------------------------------------------------------- |
| *(caller sets CC prior to BSR)* | —              | Carry flag determined by the instruction immediately before the BSR to 0x39FA8                           |
| `0x00039FA8`   | `BCS.S 0x00039FAC`           | **Path-B deciding branch.** Taken (→ RTS) when Carry set; fall-through enters 0x39FAA                    |
| `0x00039FAA`   | `BRA.S 0x00039F8C`           | unconditional — enters warm-restart cascade                                                              |
| `0x00039FAC`   | `RTS`                        | caller-return path when Carry was set                                                                    |

**Callers of 0x00039FA8**, from [maincpu.disasm.txt](build/maincpu.disasm.txt):

- **Caller B1 — `arcade_pc 0x0003AB8A`** (disasm line 73767). Immediately preceded by:

| arcade_pc      | instruction                          | role                                                                                                      |
| -------------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| `0x0003AB7C`   | `TST.W %a5@(7184)`                   | test word at `HW_ADDRESS 0x00FF1C10` (unrelated — precedes B1 block at 0x3AB7C start of nearby branch)    |
| `0x0003AB84`   | `CMPI.W #256, %a5@(18)`              | **Sets CC for Path-B1.** Sets C flag based on unsigned comparison of `HW_ADDRESS 0x00FF0012` vs 256       |
| `0x0003AB8A`   | `BSR.W 0x00039FA8`                   | → path B; Carry from the CMPI above governs `0x39FA8 BCS`                                                 |

- **Caller B2 — `arcade_pc 0x0003B092`** (disasm line 74117). Immediately preceded by:

| arcade_pc      | instruction                          | role                                                                                                      |
| -------------- | ------------------------------------ | --------------------------------------------------------------------------------------------------------- |
| `0x0003B084`   | `TST.W %a5@(7184)`                   | test word at `HW_ADDRESS 0x00FF1C10` (same pattern as B1)                                                 |
| `0x0003B08C`   | `CMPI.W #256, %a5@(18)`              | **Sets CC for Path-B2.** Same comparison as B1.                                                           |
| `0x0003B092`   | `BSR.W 0x00039FA8`                   | → path B; Carry from the CMPI above governs `0x39FA8 BCS`                                                 |

---

## Phase 3 — Failing condition(s)

Two distinct deciding conditions identified. They test different state
and correspond to different arcade-state scenarios.

### Condition A (Path A)

- **Branch instruction:** `BEQ.S 0x00039F8C` at `arcade_pc 0x00039F84`
- **Condition:** Z flag set by the prior `TST.W 0x2C(A5)` at `arcade_pc 0x00039F80` — true when the word at `HW_ADDRESS 0x00FF002C` is zero.
- **Registers involved:** A5 (base pointer, value `0x00FF0000`).
- **Memory involved:** `HW_ADDRESS 0x00FF002C` — a 16-bit word.
- **Classification:** **Watchdog or timer.** This is a countdown word. The caller seeds it with an initial value (various seeds observed: `#160` at [maincpu.disasm.txt:73740](build/maincpu.disasm.txt) arcade_pc 0x3AB22; `#512` at arcade_pc 0x3AB5E; `#16` at arcade_pc 0x3ABD0). Each invocation of `arcade_pc 0x00039F80` decrements the word by one. When the word reaches zero, the countdown expires and warm-restart fires.

### Condition B (Paths B1 and B2)

- **Branch instruction:** `BCS.S 0x00039FAC` at `arcade_pc 0x00039FA8`
- **Condition:** Carry flag set by the caller's `CMPI.W #256, %a5@(18)` — Carry set means `HW_ADDRESS 0x00FF0012 < 256` (unsigned). Carry clear means `HW_ADDRESS 0x00FF0012 >= 256`. Fall-through (path into warm-restart cascade) occurs on Carry-clear → `HW_ADDRESS 0x00FF0012 >= 256`.
- **Registers involved:** A5 (= `0x00FF0000`); no explicit data register (immediate `#256` encoded in the CMPI).
- **Memory involved:** `HW_ADDRESS 0x00FF0012` — a 16-bit word.
- **Classification:** **State flag or sentinel value.** A5@(18) is an arcade state word; the CMPI test against `#256` looks like a mode / state-ID check rather than a decrementing timer.

---

## Phase 4 — Expected vs actual

### Path A

- **Expected (to NOT reach 0x39F9E):** `HW_ADDRESS 0x00FF002C` > 0 at the moment the routine at 0x39F80 is called.
- **Actual (at the moment the warm-restart branch fires):** `HW_ADDRESS 0x00FF002C` == 0.
- **Source of actual:** definitional — `BEQ` only takes when Z was set, which by prior `TST.W` means the word was zero. If execution reaches 0x39F9E via Path A, the word was observably zero at that moment. **No further trace required to establish this for Path A**; trace is required only to establish that Path A is the one taken at runtime.
- **Seed sources (drives how the countdown reaches zero):**
  - `arcade_pc 0x3AB22 MOVE.W #160, 0x2C(A5)`
  - `arcade_pc 0x3AB5E MOVE.W #512, 0x2C(A5)`
  - `arcade_pc 0x3ABD0 MOVE.W #16, 0x2C(A5)`
  - Additionally, [apps/rastan-direct/src/main_68k.s:2126](apps/rastan-direct/src/main_68k.s#L2126) mirrors the 160 seed inside the Genesis `init_staging_state` body (arcade-workram factory defaults). Under the current Genesis build this writes `HW_ADDRESS 0x00FF002C = 160` on every main_68k re-entry. Whether this interferes with the countdown depends on call ordering, which is unproven from static analysis.

### Path B

- **Expected (to NOT reach 0x39F9E):** `HW_ADDRESS 0x00FF0012` < 256 at the moment of the CMPI at the caller site.
- **Actual (at the moment the warm-restart branch fires):** `HW_ADDRESS 0x00FF0012` >= 256.
- **Source of actual:** definitional from the CMPI/BCS mechanics; cannot be corroborated from static analysis alone because `HW_ADDRESS 0x00FF0012` is arcade state not initialized by any of the init sites listed in [apps/rastan-direct/src/main_68k.s:2094-2167](apps/rastan-direct/src/main_68k.s#L2094-L2167). Arcade's own startup_common at `arcade_pc 0x0003A000` is the authoritative source of its value, and the exact run-time value at the CMPI site is not statically determinable.

---

## Phase 5 — Root cause

**STOP.**

Two distinct execution paths lead to `arcade_pc 0x00039F9E`. Each is
governed by a different conditional branch and a different memory
word. Both paths are statically confirmed present in the arcade ROM
(callers located in the shipping disassembly at arcade_pc 0x0003AB6E
for Path A, and 0x0003AB8A / 0x0003B092 for Path B). Static evidence
cannot determine which path fires at the runtime event of interest,
because the answer depends on the arcade state machine's branch
history in the run-up to the warm restart.

No single root-cause sentence is supported by current evidence.

### Data required to resolve

To issue a single HIGH-confidence root-cause statement, one of the
following is needed:

1. **PC trace slice** spanning the ~200 instructions immediately
   preceding the PC arrival at `arcade_pc 0x00039F9E`. MAME or Exodus
   step-trace; capture every instruction executed. The presence of
   either `arcade_pc 0x0003AB6E` (Path A thunk) or `arcade_pc
   0x0003AB8A` / `0x0003B092` (Path B entries) in the immediate
   backtrace is dispositive.

2. **Breakpoint state capture** at each of the three caller sites
   (`arcade_pc 0x0003AB6E`, `0x0003AB8A`, `0x0003B092`). Record:
   - Whether the breakpoint fires at all in a representative run.
   - If fired: the values of `HW_ADDRESS 0x00FF002C` (word) and
     `HW_ADDRESS 0x00FF0012` (word) at the moment the breakpoint
     fires.

3. **Register/memory snapshot on entry to `arcade_pc 0x00039F9E`**,
   specifically: the return-stack state (if BSR from Path B, there
   will be an RA on the stack; Path A BRA thunk leaves no local RA)
   and the values of `HW_ADDRESS 0x00FF002C` and `HW_ADDRESS
   0x00FF0012` at that instant.

Any one of (1), (2), or (3) is sufficient. (1) is preferred because
it is a single capture and answers the path question directly.

### Partial findings that do NOT require additional data

- The instruction at `arcade_pc 0x00039F9E` is proven to be the
  start of the warm-restart trampoline (`MOVEA.L (0x00).W, SP`).
- The warm-restart trampoline is proven to read `ROM[0x0004]` and
  JMP through it.
- Three callers of the warm-restart-cascade entry points are proven
  to exist in arcade ROM.
- The first conditional branch *in the direct backward walk from
  0x39F9E* is `BNE.S` at `arcade_pc 0x00039F9C`, which is a
  structurally-forced delay-loop terminator (not a state-dependent
  decision).

### Confidence

- **Confidence for the mechanism (what executes once at 0x39F9E):** HIGH
- **Confidence for the deciding conditional branch on a given runtime event:** LOW without additional trace data

---

## Summary

- Instruction at `arcade_pc 0x00039F9E` identified: YES (warm-restart trampoline start)
- Uses ROM[0x0004]: YES (two instructions downstream, at `arcade_pc 0x00039FA2 / 0x00039FA6`)
- Failing condition identified exactly: NO — two candidate conditions identified, each statically valid, disambiguation requires runtime trace data
- Expected value (Path A): `HW_ADDRESS 0x00FF002C` > 0
- Actual value (Path A, if taken): `HW_ADDRESS 0x00FF002C` == 0
- Expected value (Path B): `HW_ADDRESS 0x00FF0012` < 256
- Actual value (Path B, if taken): `HW_ADDRESS 0x00FF0012` >= 256
- Confidence: LOW (multiple candidate causes)
- STOP triggered: YES — multiple possible causes without proof distinguishing them; trace capture needed (specified above)

No fix proposed. No design change proposed. No architecture change proposed.
