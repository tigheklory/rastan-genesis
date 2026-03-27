# Second Text Chain Breakpoint

## Section 1 - Entry Trace
Target artifact: `dist/Rastan_235.bin`.

Runtime capture source: `/tmp/second_text_chain_trace.txt`.
Static instruction decode source: `tools/local/toolchain/m68k-elf/bin/m68k-elf-objdump` on `dist/Rastan_235.bin` around `0x202990-0x202A80`.

Observed live sequence after `0x03BD5E` enters `0x202A4C`:

STEP 1
- PC: `0x202A4C`
- instruction: `cmpl %d1,%d2`
- register/stack effect: condition codes set from `D2-D1` comparison; registers unchanged
- next PC: `0x202A4E`

STEP 2
- PC: `0x202A4E`
- instruction: `beqs 0x202A16` (opcode `67C6`)
- register/stack effect: branch tests Z flag from STEP 1 (`D2=0`, `D1=3` at entry; not equal)
- next PC: `0x202A50` (branch not taken)

STEP 3
- PC: `0x202A50`
- instruction: `subql #5,%d1`
- register/stack effect: `D1` decremented by 5 (`0x00000003 -> 0xFFFFFFFE`)
- next PC: `0x202A52`

STEP 4
- PC: `0x202A52`
- instruction: `bnew 0x2029B8` (opcode `6600FF64`)
- register/stack effect: branch tests Z flag from STEP 3; `D1!=0`, so branch is taken
- next PC: `0x2029B8`

STEP 5
- PC: `0x2029B8`
- instruction: `movel %sp@+,%d2`
- register/stack effect: pops long from stack into `D2`; unwinds stack frame for return sequence
- next PC: `0x2029BA`

STEP 6
- PC: `0x2029BA`
- instruction: `rts`
- register/stack effect: returns to caller address on stack (`0x03BD64`)
- next PC: `0x03BD64`

End state of this chain: execution exits without any `jsr 0x20034C`.

## Section 2 - Branch / Exit Analysis
Blocking point identified:

- exact PC: `0x202A52`
- branch instruction: `bnew 0x2029B8`
- expected next step: continuation through a wrapper path that executes `jsr 0x20034C`
- actual next step: taken branch to `0x2029B8`, then `rts` at `0x2029BA` back to `0x03BD64`
- reason: `0x202A4C` in Build 235 is not the text wrapper body; it is a compare/branch/return routine tail, so the live path branches out and returns before any call to `0x20034C`.

## Section 3 - Register / Stack Proof
Entry capture at `0x202A4C` (live trace STEP 5 in file):
- `A0=0x00000008`
- `A4=0x00000000`
- `A5=0xE0FF004C`
- `D0=0x00000002`
- `SP=0xE0FFFDFA`
- stack sample: `[SP]=0x0003B2BC`, `[SP+4]=0x0003B074`

Blocking-path capture:
- at `0x202A52` (pre-branch step):
  - `A0=0x00000008`, `A4=0x00000000`, `A5=0xE0FF004C`, `D0=0x00000002`, `SP=0xE0FFFDF6`
  - `D1` on entry to branch site is `0x00000003` (then becomes `0xFFFFFFFE` after STEP 3, confirmed at branch target capture)
  - stack sample: `[SP]=0x0003BD64` (return address), `[SP+4]=0x0003B2BC`
- at branch target `0x2029B8` (post-branch):
  - `D1=0xFFFFFFFE` confirms non-zero result causing `bne` take

Relevant memory reads controlling branch:
- none in this micro-path; branch decisions are register/CCR driven (`D1`, `D2`, Z flag), not direct memory-read comparisons in the traced `0x202A4C -> ...` segment.

Failure cause classification:
- **wrong entry point** (semantic): dispatch enters `0x202A4C`, but this address is a non-wrapper compare/branch/return routine in Build 235.
- Not a wrong stack-state failure (stack is consistent and returns cleanly).
- Branch outcome is correct for the observed register state; the semantic entry target is the blocker.

## Section 4 - Final Breakpoint
=== SECOND_TEXT_CHAIN_BREAKPOINT ===
- entry_pc: `0x202A4C`
- blocking_pc: `0x202A52`
- expected: wrapper path should execute `jsr 0x20034C` before return
- actual: `subql #5,%d1` then taken `bnew 0x2029B8` -> `rts` via `0x2029BA` to `0x03BD64`
- reason_0x20034C_not_reached: `0x202A4C` is not the text-wrapper body in Build 235 (wrong semantic entry), so control exits through branch/return path before any call to `0x20034C`

## Section 5 - Conclusion
After 0x03BD5E was corrected, the next text-path failure occurs at `0x202A52` because execution at `0x202A4C` runs a non-wrapper branch/return routine and takes `bne.w 0x2029B8`, which prevents `0x20034C` from executing.
