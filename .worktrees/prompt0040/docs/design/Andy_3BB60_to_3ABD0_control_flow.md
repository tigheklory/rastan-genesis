# Andy — arcade_pc 0x3BB60 Region → 0x03ABD0 Control-Flow Reconstruction

**Agent:** Andy
**Type:** Static Analysis / Control-Flow Reconstruction (no implementation)
**Build context:** `rastan-direct` Build 0051
**Architecture compliance:** CONFIRMED (no source / spec / tool modifications).

**Outcome:** Mechanism from `arcade_pc 0x03BB7C` to `arcade_pc 0x03ABD0` is **RTS-returning to a stacked return address that was pushed by the `BSR.W 0x3BB48` at `arcade_pc 0x03ABCC`**. Enclosing function of `0x3BB60` is the **text-writer subroutine at `arcade_pc 0x3BB48`** (RTS-ending, general-purpose utility called from ~30+ arcade sites). Enclosing function of `0x03ABD0` is a separate subroutine at `arcade_pc 0x3AB7C`..`0x3ABE0`, which has exactly one static caller at `arcade_pc 0x03A03E` — inside the arcade L5 VBlank handler at `arcade_pc 0x3A008`. Enclosing function of `0x03AEFC` is the **cold-boot startup_common body at `arcade_pc 0x03AE86`**, reached from the boot vector chain `ROM[0x0004] → arcade_pc 0x3A000 → BRA.W 0x3AE86`. The two enclosing contexts are entirely separate subsystems (L5 VBlank-handler call tree vs. cold-boot startup). **Stack evidence is verified**: `[SP] = 0x0003A242 → arcade_pc 0x3A042` is the instruction after `BSR.W 0x3AB7C` at `arcade_pc 0x03A03E`, which is the L5 handler's call site for the enclosing function of `0x03ABD0`. No hypothesis about cause is offered — strictly facts.

---

## Address convention

All addresses are `arcade_pc` unless otherwise labelled. The relocation `runtime_genesis_pc = arcade_pc + 0x200` applies wherever a Genesis ROM offset is referenced.

---

## Phase 1 — Disassemble `arcade_pc 0x03BB60..0x03BB80`

From [build/maincpu.disasm.txt](build/maincpu.disasm.txt) lines 74988-75015, cross-verified against [build/regions/maincpu.bin](build/regions/maincpu.bin).

### Entry prologue (preceding context, for function boundary)

| arcade_pc | bytes          | instruction                         | role                                                           |
| --------- | -------------- | ----------------------------------- | -------------------------------------------------------------- |
| `0x3BB46` | `24 02`        | `movel %d2, %d2` (no-effect, likely data) | Tail of preceding content — disassembler-parsed, no control reaches here from normal flow; probably data / alignment. |
| `0x3BB48` | `32 00`        | `movew %d0, %d1`                    | **Function entry** — prologue: save glyph index into d1.       |
| `0x3BB4A` | `02 40 00 7F`  | `andiw #127, %d0`                   | Mask low 7 bits of glyph index — table has 128 entries.        |
| `0x3BB4E` | `E5 48`        | `lslw #2, %d0`                      | ×4 (each table entry is 4 bytes = u32 pointer).                |
| `0x3BB50` | `41 FA 00 2A`  | `lea pc@(0x3BB7C), %a0`             | `%a0 = &table`. PC+2 + 0x2A = 0x3BB7C (table origin).          |
| `0x3BB54` | `D0 C0`        | `addaw %d0, %a0`                    | `%a0 = &table[index]` (byte-granular).                         |
| `0x3BB56` | `20 50`        | `moveal %a0@, %a0`                  | `%a0 = *(u32 at table[index])` — dereference the table pointer to the glyph record. |
| `0x3BB58` | `22 58`        | `moveal %a0@+, %a1`                 | `%a1 = *a0 (dest pointer)`; `a0 += 4`.                         |
| `0x3BB5A` | `34 18`        | `movew %a0@+, %d2`                  | `%d2 = *a0 (attribute word)`; `a0 += 2`.                       |
| `0x3BB5C` | `4A 01`        | `tstb %d1`                          | Test original d0 high-bit (saved into d1 at entry).            |
| `0x3BB5E` | `6B 0C`        | `bmis 0x3BB6C`                      | **Conditional branch** — if high bit set, use "alt path" at 0x3BB6C; else fall through to 0x3BB60. |

### Primary loop body

| arcade_pc | bytes    | instruction                      | role                                                       |
| --------- | -------- | -------------------------------- | ---------------------------------------------------------- |
| `0x3BB60` | `10 18`  | `moveb %a0@+, %d0`               | **Loop top**: read next glyph byte from source; `a0 += 1`. |
| `0x3BB62` | `67 16`  | `beqs 0x3BB7A`                   | **Loop-exit branch** — if byte == 0, goto RTS at 0x3BB7A.  |
| `0x3BB64` | `48 80`  | `extw %d0`                       | Sign-extend byte to word.                                  |
| `0x3BB66` | `32 C2`  | `movew %d2, %a1@+`               | Write attribute word to destination; `a1 += 2`.            |
| `0x3BB68` | `32 C0`  | `movew %d0, %a1@+`               | Write tile word (the glyph byte) to destination; `a1 += 2`.|
| `0x3BB6A` | `60 F4`  | `bras 0x3BB60`                   | **Back-branch to loop top** — unconditional.               |

### Alt-path loop body (reached from BMI at 0x3BB5E)

| arcade_pc | bytes          | instruction                      | role                                                       |
| --------- | -------------- | -------------------------------- | ---------------------------------------------------------- |
| `0x3BB6C` | `32 3C 00 20`  | `movew #32, %d1`                 | Constant tile value (space = 0x20).                        |
| `0x3BB70` | `10 18`        | `moveb %a0@+, %d0`               | Alt-loop top: read next byte.                              |
| `0x3BB72` | `67 06`        | `beqs 0x3BB7A`                   | Exit on null byte.                                         |
| `0x3BB74` | `32 C2`        | `movew %d2, %a1@+`               | Write attribute.                                           |
| `0x3BB76` | `32 C1`        | `movew %d1, %a1@+`               | Write constant tile (#32).                                 |
| `0x3BB78` | `60 F6`        | `bras 0x3BB70`                   | Alt-loop back-branch.                                      |

### Epilogue and data table

| arcade_pc | bytes          | instruction                        | role                                                                                 |
| --------- | -------------- | ---------------------------------- | ------------------------------------------------------------------------------------ |
| `0x3BB7A` | `4E 75`        | `rts`                              | **Function exit.** Pops return address from stack.                                   |
| `0x3BB7C` | `00 03 BC 98`  | `.long 0x0003BC98` (data — disassembler misreports as `orib #-104, %d3`) | **Start of PC-relative jump table** — 128 entries × 4 bytes = 512 bytes of u32 glyph-record pointers. Disassembler incorrectly parses the data bytes as code; they are unreachable via normal control flow and are authoritatively interpreted by the `moveal %a0@, %a0` at `0x3BB56`. |
| `0x3BB80` | `00 03 BC A6`  | `.long 0x0003BCA6` (data)          | Table entry 1.                                                                       |
| `0x3BB84` | `00 03 BC BE`  | `.long 0x0003BCBE` (data)          | Table entry 2.                                                                       |
| (continues through `0x3BB7C + 128*4 - 1 = 0x3BE7B`) | — | — | — |

### Function boundary

- **Function entry:** `arcade_pc 0x3BB48` (prologue `movew %d0, %d1` following preceding content that the disassembler parses as mostly-invalid bytes; content at `0x3BB24..0x3BB46` is data tail of preceding content — no ordinary entry reaches `0x3BB48` by fall-through, only by BSR/JSR).
- **Function exit:** single `rts` at `arcade_pc 0x3BB7A`. No other RTS, no unconditional branch out of the function body.
- **Inner loops:** primary loop `0x3BB60..0x3BB6A` (backward branch `bras 0x3BB60`); alt-path loop `0x3BB70..0x3BB78` (backward branch `bras 0x3BB70`).
- **Exit condition (both loops):** `beqs 0x3BB7A` when the source byte read via `moveb %a0@+, %d0` is zero (null terminator).
- **What is at `0x3BB7C`?** A 128-entry u32 jump table (data, not code). The disassembler's interpretation as `orib #-104, %d3` is a byte-level false positive: these bytes are pointer values indexed by the `lea pc@(0x3BB7C), %a0` setup earlier in the function.

### Reconciling Cody's 5-PC trace with the disassembly

Cody's trace table in [Cody_seed_clear_ordering_trace.md](docs/design/Cody_seed_clear_ordering_trace.md) reports the 5 most recent observed `runtime_genesis_pc` values before BP_SEED hit. MAME observation is **prefetch-shifted** — the reported `runtime_genesis_pc` at a breakpoint is 2 bytes past the instruction actually being retired. The [Cody_a5_2c_seed_check.md](docs/design/Cody_a5_2c_seed_check.md) Phase 2 table confirms the convention (observed `0x0003ADD2` vs target `0x0003ADD0` for the same instruction).

Applied to the trace:

| rel seq | reported arcade_pc | actual instruction arcade_pc (–2) | matches disassembly? | actual mnemonic |
| ------- | ------------------ | ---------------------------------- | -------------------- | --------------- |
| -5      | `0x03BB6A`         | `0x03BB68`                         | YES                  | `movew %d0, %a1@+` (tail of primary loop body) |
| -4      | `0x03BB6C`         | `0x03BB6A`                         | YES                  | `bras 0x3BB60` (primary-loop back-branch) |
| -3      | `0x03BB62`         | `0x03BB60`                         | YES                  | `moveb %a0@+, %d0` (loop top, reads next byte — returns 0 this iteration) |
| -2      | `0x03BB64`         | `0x03BB62`                         | YES                  | `beqs 0x3BB7A` (null terminator detected — branch taken) |
| -1      | `0x03BB7C`         | `0x03BB7A`                         | YES                  | `rts` |

**Chronological interpretation:** the last 5 instructions form the natural loop-exit tail of the text-writer subroutine —
```
  ... iter n: write tile/attr → back-branch top → read next byte (=0) → exit branch taken → RTS
```

**Integrity:** all 5 trace PCs explained, with a consistent –2 prefetch offset across every row.

---

## Phase 2 — Trace the path from `0x03BB7C` (actual `0x03BB7A`) to `0x03ABD0`

From Phase 1, the instruction executing at the –1 trace row is **`rts` at `arcade_pc 0x03BB7A`**.

`rts` pops a 4-byte return address from the stack and jumps to it. The next `arcade_pc` observed is `0x03ABD0` (the BP_SEED hit). Therefore, the stacked return address was `0x03ABD0`, and execution resumes at that address.

### Where was `0x03ABD0` pushed onto the stack?

From [build/maincpu.disasm.txt:73783](build/maincpu.disasm.txt) the instruction immediately preceding `arcade_pc 0x03ABD0` is:

```
3abcc:  6100 0f7a        bsrw 0x3bb48
3abd0:  3b7c 0010 002c   movew #16, %a5@(44)
```

`BSR.W 0x3BB48` is a 4-byte instruction at `arcade_pc 0x03ABCC`. Its behaviour is:

1. Push `PC + 4 = 0x03ABD0` onto the stack.
2. Jump to `0x3BB48`.

When the called function's `rts` at `0x3BB7A` executes, it pops exactly `0x03ABD0` and resumes there.

### Mechanism summary

```
Mechanism: RTS to stacked return address.
Supporting disassembly:
  arcade_pc 0x03ABCC:  6100 0F7A   bsrw 0x3bb48     ← pushes 0x03ABD0 onto stack
  arcade_pc 0x03ABD0:  3B7C 0010 002C   (next sequential instruction, reached via the RTS pop)
  arcade_pc 0x03BB7A:  4E75         rts             ← pops stacked return address
Intermediate PCs (inside the called function 0x03BB48 subroutine):
  0x03BB48..0x03BB7A (variable path depending on glyph sequence; trace shows final iterations)
```

No computed jump. No intermediate BRA or JMP. The transition is the standard arcade subroutine-return pattern: `BSR → … → RTS`.

---

## Phase 3 — Enclosing function of `arcade_pc 0x03BB60..0x03BB7C`

Applied the function-boundary criteria from Phase 1:

- **Entry point:** `arcade_pc 0x03BB48`.
- **Exit points:** `arcade_pc 0x03BB7A` (single `rts`). No RTE, no unconditional branch leaving the function via non-RTS exit.
- **Known static callers** (from `grep` of `build/maincpu.disasm.txt` for `bsrw 0x3bb48` / `jsr 0x3bb48`):
  - `arcade_pc 0x03A334`, `0x03A33A`, `0x03A340`, `0x03A346`, `0x03A360`, `0x03A3B0`, `0x03A3B6`, `0x03A3C4`, `0x03A3CA`, `0x03A42C`, `0x03A432`, `0x03A48C`, `0x03A5E8`, `0x03A710`, `0x03A71C`, `0x03A732`, `0x03A8EC`, `0x03A8FC`, `0x03A908`, `0x03A90E`, `0x03AA68`, `0x03AA6E`, `0x03AA74`, `0x03AA7A`, `0x03AAB6`, `0x03AABC`, `0x03AAC2` (at least 27 direct callers, many of which are in the arcade state-machine dispatch range).
  - `arcade_pc 0x03ABCC` (the call site relevant to this trace).
  - Two matches at ROM-header offsets `0x392` and `0x5C0` — these are inside the Genesis ROM's preserved-vector / header region (`0x000000..0x0003FF`) and are **disassembler false positives** (vector-table bytes parsed as code). Not real callers.

### Subsystem classification (evidence-based)

- **Hardware-write inventory inside `0x03BB48..0x03BB7A`:** none. The function writes only via `(%a1)+` indirect mode to a pointer supplied by the caller through the jump-table record at `0x3BB7C`. No hardware-address literal, no arcade-chip register access. Cross-verified by byte-level scan of the disassembled instructions: zero absolute-long addressing-mode instructions in the function body.
- **Entry prologue pattern:** `movew %d0, %d1; andiw #127, %d0; lslw #2, %d0; lea pc@(table), %a0; …` — **standard PC-relative jump-table dispatcher**, not an interrupt-handler prologue. Interrupt handlers on 68000 typically begin with SR manipulation or register save (`movem.l`); this function does neither.
- **Exit type:** `rts`, not `rte`. **Conclusive evidence that this is a regular subroutine, not an interrupt handler.**
- **`build/maincpu.disasm.txt` labels or comments:** none at this location (raw `objdump` output without symbolisation).
- **Corroboration from project tooling:** [tools/translation/precompute_pc080sn_tile_lut.py](tools/translation/precompute_pc080sn_tile_lut.py) line 80-81 explicitly names this function: `TEXT_WRITER_3BB48_TABLE_SOURCE = 0x003BB7C` and `TEXT_WRITER_3BB48_TABLE_ENTRIES = 128`. The Python tool's function `extract_text_writer_tiles()` uses this address as its "3BB48 descriptor table" anchor, and the tool's comment-style identifier is "text writer."

### Classification

```
Enclosing function of 0x03BB60..0x03BB7C:
  entry point:    arcade_pc 0x3BB48
  exit point:     arcade_pc 0x3BB7A (rts)
  callers:        ~27+ distinct arcade_pc call sites across the arcade ROM
                  (the function is a heavily-reused utility)
  classification: text-writer / glyph-string dispatcher subroutine
                  — regular (RTS-ending) utility called from many contexts
                  — NOT an interrupt handler
                  — NOT tied to a single subsystem
```

The function is a **general-purpose utility**. The subsystem from which it is invoked varies per call site. **In the specific trace captured in [Cody_seed_clear_ordering_trace.md](docs/design/Cody_seed_clear_ordering_trace.md), the call site is `arcade_pc 0x03ABCC`, which is inside the function at `arcade_pc 0x03AB7C` (see Phase 4 for that function's own context).**

---

## Phase 4 — Enclosing function of `arcade_pc 0x03AEFC`

### 4a — Enclosing function of the SEED site (`0x03ABD0`)

(Included because the SEED site's context is needed for the ordering comparison.)

From the disassembly immediately around `0x03ABD0`:

```
3ab78: 4e75               rts                                ← end of a PRECEDING function
3ab7a: 60fe               bras 0x3ab7a                        ← infinite-hang fall-through (unreachable by normal flow)
3ab7c: 4a6d 1c10          tstw %a5@(7184)                    ← FUNCTION ENTRY
3ab80: 6002               bras 0x3ab84
3ab82: 60fe               bras 0x3ab82                        ← infinite-hang fall-through (unreachable)
3ab84: 0c6d 0100 0012     cmpiw #256, %a5@(18)
3ab8a: 6100 f41c          bsrw 0x39fa8
3ab8e: 0c6d 0003 0000     cmpiw #3, %a5@(0)
3ab94: 674a               beqs 0x3abe0                       ← early exit to RTS
3ab96: 0839 0002 0039 0007  btst #2, 0x00390007
3ab9e: 6640               bnes 0x3abe0                       ← early exit
3aba0: 103c 0000          moveb #0, %d0
3aba4: 6100 44de          bsrw 0x3f084
3aba8: 3b7c 001f 004a     movew #31, %a5@(74)
3abae: 6100 0228          bsrw 0x3add8
3abb2: 6100 029c          bsrw 0x3ae50
3abb6: 6100 01ba          bsrw 0x3ad72
3abba: 42b9 00c2 0000     clrl 0xc20000
3abc0: 42b9 00c4 0000     clrl 0xc40000
3abc6: 6100 029c          bsrw 0x3ae64
3abca: 700e               moveq #14, %d0                      ← glyph index for text writer
3abcc: 6100 0f7a          bsrw 0x3bb48                        ← CALL to text-writer (returns to 0x3abd0)
3abd0: 3b7c 0010 002c     movew #16, %a5@(44)                ← SEED INSTRUCTION ((A5+0x2C) = 16)
3abd6: 3b7c 0003 0000     movew #3, %a5@(0)
3abdc: 426d 0002          clrw %a5@(2)
3abe0: 4e75               rts                                 ← FUNCTION EXIT
```

- **Function entry:** `arcade_pc 0x03AB7C`.
- **Function exits:** three `rts` / RTS paths — `0x03ABE0` (main RTS), plus the two early exits via `beqs 0x3ABE0` / `bnes 0x3ABE0` that target the same RTS.
- **Known static callers** (from `grep`): a single hit at `arcade_pc 0x03A03E: 6100 0B3C  bsrw 0x3ab7c` — **one caller only**.
- **What is at `arcade_pc 0x03A03E`?** From [Andy_p1_p2_prerequisite_verification.md](docs/design/Andy_p1_p2_prerequisite_verification.md) Phase 2 (L5 handler disassembly), the instructions at `arcade_pc 0x03A008..0x03A07E` form the arcade **level-5 (VBlank) IRQ handler** — the function targeted by arcade vector 29 at file offset `0x74`. The `BSR.W 0x03AB7C` at `0x03A03E` is inside that handler's body.
- **Subsystem classification:** the function at `0x03AB7C` is a regular RTS-ending subroutine whose sole static caller is the arcade L5 VBlank handler. Therefore the function's **calling context is the arcade L5 VBlank handler chain**. The function itself (RTS, not RTE) is not the handler proper, but is a helper invoked exclusively from it.

### 4b — Enclosing function of the CLEAR site (`0x03AEFC`)

The reference to `arcade_pc 0x03AEFC` in Cody's trace is slightly mis-aligned. The nearest instruction boundaries from [build/maincpu.disasm.txt:74008-74015](build/maincpu.disasm.txt):

```
3aeea: 41f9 0010 c000     lea 0x10c000, %a0        ← (redirected by opcode_replace @0x3AEEA)
3aef0: 43f9 0010 c002     lea 0x10c002, %a1        ← (redirected by opcode_replace @0x3AEF0)
3aef6: 30bc 0000          movew #0, %a0@           ← initial zero write
3aefa: 303c 1fff          movew #8191, %d0         ← loop counter seed (4-byte instr at 0x3AEFA..0x3AEFD)
3aefe: 32d8               movew %a0@+, %a1@+       ← LOOP BODY: zero-propagate
3af00: 5340               subqw #1, %d0
3af02: 66fa               bnes 0x3aefe             ← loop back
3af04: 4bf9 0010 c000     lea 0x10c000, %a5        ← (redirected by opcode_replace @0x3AF04)
```

`arcade_pc 0x03AEFC` is inside the 4-byte `303c 1fff` immediate of the `movew #8191, %d0` at `0x03AEFA`. Cody's trace cites the **first trace sample** at `0x0003B0FC` (the prefetch-offset observation of the next pipeline event). The correct actual-instruction boundaries of the zero-propagate loop are `0x03AEFA..0x03AF02`. Either way, the **loop belongs to the same enclosing function**.

That enclosing function is the arcade cold-boot **startup_common body**:

- **Function entry:** `arcade_pc 0x03AE86` — reached from the cold-boot `BRA.W` at `arcade_pc 0x03A000` (`6000 0E84` → PC+2+0x0E84 = `0x03AE86`), per the ROM vector at file offset `0x04` (`0x0003A000`). Analysis cross-verified in [Andy_p1_p2_prerequisite_verification.md](docs/design/Andy_p1_p2_prerequisite_verification.md) P1 §1-3.
- **Function exit:** startup_common falls through into the arcade main-loop body; there is no single RTS at its notional end. This is characteristic of a cold-boot init function rather than a reusable subroutine.
- **Known static callers:** the cold-boot vector chain only — `ROM[0x0004] = 0x3A000`; the 68000 resets to PC = 0x3A000; `BRA.W` at 0x3A000 reaches 0x3AE86. No BSR / JSR caller.
- **Subsystem classification:** **arcade cold-boot startup_common** — executed exactly once at power-on (modulo watchdog-driven restart that re-enters via the same vector).

### Comparison of enclosing contexts

| Aspect | SEED site (`0x03ABD0` inside `0x03AB7C`) | CLEAR site (`0x03AEFC` inside `0x03AE86`) |
| ------ | ----------------------------------------- | ------------------------------------------ |
| Enclosing function entry | `arcade_pc 0x03AB7C` | `arcade_pc 0x03AE86` |
| Function type | Regular RTS-ending subroutine | Cold-boot init falling through into main body |
| Static callers | Exactly one: `arcade_pc 0x03A03E` (arcade L5 VBlank handler) | Cold-boot vector only (`ROM[0x04] → BRA.W`) |
| Subsystem | Helper invoked from L5 VBlank-handler chain | Arcade startup_common (cold init) |
| Same enclosing function? | **NO** |

### Ordering per arcade-intended boot flow (from callers + vector chain)

Using only static evidence (ROM vector table + caller xrefs):

1. **CPU reset** sets PC from `ROM[0x04] = 0x3A000`.
2. `arcade_pc 0x3A000` → `BRA.W 0x3AE86` → **startup_common body begins at `0x3AE86`** — this includes the zero-propagate loop spanning `0x03AEFA..0x03AF02` (the CLEAR site).
3. Startup_common runs RAM probes, WRAM zero-propagate, sets `A5` at `0x3AF04`, continues initialisation, eventually enables interrupts and falls through into the arcade main loop.
4. Once interrupts are enabled, the 68000 level-5 auto-vector (vector 29 at ROM offset `0x74 → arcade_pc 0x3A008`) becomes reachable. Each VBlank the CPU jumps to `arcade_pc 0x03A008`, which at `0x03A03E` executes `BSR.W 0x03AB7C` — entering the function containing the SEED site at `0x03ABD0`.

Therefore, per static arcade-intended ordering:
- **First:** startup_common (including the CLEAR at `0x03AEFC`) — cold boot.
- **Later:** L5 VBlank handler → `BSR.W 0x03AB7C` → (eventually) the SEED at `0x03ABD0` — runtime.

### Observed Build-0051 ordering from Cody's trace

From [Cody_seed_clear_ordering_trace.md](docs/design/Cody_seed_clear_ordering_trace.md) Phase 2 and [Cody_a5_2c_seed_check.md](docs/design/Cody_a5_2c_seed_check.md) Phase 3:

- **SEED** (`arcade_pc 0x03ABD0`) hit first at **cycle 1261703**.
- **CLEAR** (`arcade_pc 0x03AEFC` ≈ `0x03AF02`) first observed in trace at **cycle 1637957** (breakpoint not hit in 2-second window; trace fallback used).

**The observed ordering is reversed relative to arcade-intended ordering.** The L5-handler-driven SEED fires before the startup_common-body CLEAR executes the zero-propagate loop.

### Cause of the inversion

**Out of scope for this task per Rule 16.** This document reports the static relationships only. Cause analysis belongs to a downstream task once the relationships above are the accepted baseline.

---

## Phase 5 — Stack-evidence verification

Cody's capture: `[SP] = 0x0003A242` at the moment `BP_SEED` fires at runtime_genesis_pc `0x0003ADD0` (arcade_pc `0x03ABD0`).

Converting via the Genesis-offset relocation (`arcade_pc = runtime_genesis_pc − 0x200`):

```
[SP] = 0x0003A242  →  arcade_pc 0x03A042
```

From [build/maincpu.disasm.txt:72961-72962](build/maincpu.disasm.txt):

```
3a03e:  6100 0b3c       bsrw 0x3ab7c
3a042:  6100 0b9e       bsrw 0x3abe2
```

- `arcade_pc 0x03A03E` is a 4-byte `BSR.W` with target `0x03AB7C` (the enclosing function of the SEED site, confirmed in Phase 4a).
- `BSR.W` pushes `PC + 4 = 0x03A042` onto the stack and jumps to `0x03AB7C`.
- The pushed value `0x03A042` matches `[SP]` at `BP_SEED` after the relocation shift → `0x0003A242`. **Match.**

`arcade_pc 0x03A042` IS the instruction after a `BSR.W`. The stacked return address is therefore **a valid return address from the `BSR.W 0x03AB7C` at `arcade_pc 0x03A03E`**, confirming that the CPU is currently executing **inside the call chain invoked from the arcade L5 VBlank handler**.

This independently corroborates the Phase 4a classification: the SEED at `0x03ABD0` is being hit **from within the L5 handler's call tree** (via `0x03A03E → 0x03AB7C → 0x03ABCC → 0x03BB48 → rts → 0x03ABD0`).

---

## Phase 6 — Integrity

- `build/regions/maincpu.bin` accessible: **YES**
- `build/maincpu.disasm.txt` accessible: **YES**
- All 5 PCs from Cody's trace located in disassembly: **YES** (with the prefetch –2 offset applied to reconstruct actual-instruction addresses)
- Control-flow from `0x03BB7C` (actual: `0x03BB7A`) to `0x03ABD0` established: **YES** (`rts` to stacked return from `BSR.W 0x3BB48` at `0x03ABCC`)
- Enclosing function of `0x03BB60` identified: **YES** (text-writer subroutine at `0x03BB48`, RTS-ending, ~27+ callers — classified as general-purpose utility)
- Enclosing function of `0x03AEFC` identified: **YES** (cold-boot startup_common at `0x03AE86`)
- Enclosing function of `0x03ABD0` identified (bonus, for ordering context): **YES** (`arcade_pc 0x03AB7C`, called exclusively from arcade L5 VBlank handler at `0x03A03E`)
- Stack evidence verified: **YES** — `[SP] = 0x0003A242 → arcade_pc 0x03A042` is the post-BSR return address from `BSR.W 0x03AB7C` at `arcade_pc 0x03A03E` inside the L5 handler
- No source / spec / tool modifications by this task: **YES**

---

## Summary

```
Enclosing function of 0x03BB60:
  entry:          arcade_pc 0x03BB48
  exit:           arcade_pc 0x03BB7A (rts)
  classification: text-writer / glyph-string dispatcher subroutine
                  (regular RTS-ending utility, ~27+ callers; not an interrupt handler)
                  — subsystem: not tied to one; in this trace, invoked from the L5 handler chain

Enclosing function of 0x03AEFC:
  entry:          arcade_pc 0x03AE86 (reached from ROM[0x0004] = 0x3A000 → BRA.W 0x3AE86)
  exit:           N/A (fall-through; cold-boot init does not return)
  classification: arcade cold-boot startup_common body

Enclosing function of 0x03ABD0 (SEED site, for ordering context):
  entry:          arcade_pc 0x03AB7C
  exit:           arcade_pc 0x03ABE0 (rts)
  static callers: exactly one — arcade_pc 0x03A03E (inside arcade L5 VBlank handler at 0x3A008)
  classification: helper subroutine invoked from L5 VBlank-handler call tree

Mechanism from 0x03BB7C to 0x03ABD0:
  RTS returning to stacked return address 0x03ABD0, which was pushed onto
  the stack by the BSR.W at arcade_pc 0x03ABCC (inside the 0x03AB7C function).

Same enclosing function for 0x03BB60 and 0x03AEFC:  NO
  (text-writer utility vs. cold-boot startup_common — entirely separate subsystems;
   called from different subsystems in the observed trace.)

Static arcade-intended ordering:
  CLEAR site (startup_common) FIRST, SEED site (L5 handler chain) SECOND.

Observed Build 0051 ordering:
  SEED (cycle 1261703) FIRST, CLEAR (cycle 1637957) SECOND — reversed.

Cause of observed reversal: OUT OF SCOPE per Rule 16. Downstream task.

Stack evidence at BP_SEED: [SP] = 0x0003A242 ↔ arcade_pc 0x03A042.
  Verified as valid return address — post-BSR.W at arcade_pc 0x03A03E (inside L5 handler).
```
