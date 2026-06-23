# TODO.md

## Build 0094 Current TODO

1. **Graphics-only diagnostic for title/attract completion.** Classify each missing/incomplete visual element through producer -> staging -> clear/dirty -> VBlank commit -> tile-pattern availability -> palette -> plane/priority/scroll.
2. **Later gameplay-start exception triage.** Tighe reports gameplay start can reach the exception handler. Do not trust on-screen crash fields under OPEN-015; recover fault data from the WRAM crash record before analysis.
3. **Later real-hardware compatibility task.** Build 0094 does not currently run on real Genesis hardware (OPEN-017). Keep this separate from graphics completion unless evidence ties them.
4. **Later ledger/KF cleanup if routing remains.** Revisit only if future evidence changes issue ownership or contradicts current KFs.

---

## Historical Deferred Item

[Deferred] Investigate BlastEm DFFFFE write crash

Observed:
- BlastEm fatal error on write to 0xDFFFFE
- Likely caused by pointer overrun in sprite init or similar loop
- Runtime-computed address (not statically patchable)

Blocked by:
- BlastEm debugger limitations (no watchpoints)
- Crash occurs before reliable breakpoint interception
- Requires either:
  - Emulator-level tracing
  - Instrumented ROM
  - Correct architectural execution context

DO NOT:
- Attempt further breakpoint hunting
- Add instrumentation scaffolding
- Modify logic based on current scaffolded runtime

Revisit ONLY AFTER:
- Synthetic VBlank removed
- Arcade VBlank fully owns execution
- Graphics pipeline is no longer scaffolded

Goal when revisiting:
- Capture PC + register state at write
- Identify loop bound or pointer miscalculation
- Apply minimal opcode-level correction (no scaffolding)

Priority:
LOW (until architecture is correct)