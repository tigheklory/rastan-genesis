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