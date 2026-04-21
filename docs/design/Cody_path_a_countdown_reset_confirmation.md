# Cody — Path A Countdown -> Reset Confirmation

Agent: Cody  
Type: Runtime Trace / Verification (no fixes, no implementation)  
Build Context: current `rastan-direct`

## Architecture compliance

Read before capture:
- `RULES.md`
- `ARCHITECTURE.md`
- `AGENTS_LOG.md` (latest entries)
- `docs/design/Andy_reset_path_root_cause.md`
- `docs/design/Cody_reset_path_runtime_trace.md`

No implementation changes were made.

## Address-space legend

- `arcade_pc`: arcade address space
- `runtime_genesis_pc`: executing translated Genesis PC
- `HW_ADDRESS`: runtime WRAM address (`0x00FFxxxx`)

## Capture setup and mapping

Observed/validated mapping from runtime disassembly:
- `arcade_pc 0x00039F84` -> `runtime_genesis_pc 0x03A184` (`beq $3a18c`)
- `arcade_pc 0x00039F9E` -> `runtime_genesis_pc 0x03A19E`
- `arcade_pc 0x00039FA8` -> `runtime_genesis_pc 0x03A1A8`
- `arcade_pc 0x0003AB8A` caller context observed as `runtime_genesis_pc 0x03AD8C`

Runtime evidence source for this attempt: debugger output lines prefixed `PATHA2`.

## Phase 1 — Countdown tracking

Captured countdown samples at caller context (`arcade_pc 0x0003AB8A`):
- Initial observed value at `HW_ADDRESS 0x00FF002C`: `0x00A0`
- Sampled progression: `0x00A0 -> 0x0080 -> 0x0040 -> 0x0010 -> 0x0004 -> 0x0003 -> 0x0002 -> 0x0001`

First observed zero write event (write-watchpoint):
- `runtime_genesis_pc=0x03AC0A`, `old_ff002c=0x0001`, write data `0x0000`
- Immediate post-step value: `0x00FF002C=0x0001`
- Classification: transient zero write, not a confirmed stable zero-cross by immediate next-instruction check.

Later caller-context reads showed zero persisted:
- `runtime_genesis_pc=0x03AD8C`: `0x00FF002C=0x0000` (observed on two consecutive caller hits)

## Phase 2 — Zero-cross event and required branch context

What was captured:
- Transition evidence: nonzero countdown reached `0x0001`; a `1->0` write event was observed; immediate next-instruction read returned `0x0001` (transient).
- Later stable caller observations: `0x0000` then `0x0000` at `runtime_genesis_pc 0x03AD8C`.

What was NOT captured (required):
- Full `BEQ` runtime capture at `arcade_pc 0x00039F84` / `runtime_genesis_pc 0x03A184`
- Z flag at that `BEQ` execution point
- A5 base pointer and `D0-D3` at that `BEQ` execution point
- Immediate post-zero instruction trace tied to the first confirmed stable zero-cross event

## Phase 3 — Reset entry confirmation

Not proven in this attempt:
- No direct captured linkage from first confirmed stable zero-cross of `HW_ADDRESS 0x00FF002C` to `arcade_pc 0x00039F9E`.

## Phase 4 — Path B exclusion snapshot

At the observed zero-related caller context, captured:
- `HW_ADDRESS 0x00FF0012 = 0x0000`
- Path B condition (`>= 256`) at that observation: NOT MET

## STOP status

STOP triggered: YES.

Reason(s):
1. Required `BEQ` capture at `arcade_pc 0x00039F84` with full instruction, Z flag, A5, and D0-D3 was not captured.
2. Immediate post-zero-cross execution trace for the first confirmed stable zero-cross was not captured with instruction-level continuity.

## Additional capture needed to resolve

1. Instrument a trace that halts on the first *stable* zero-cross event (not transient write), then single-steps from that point.
2. Guarantee capture at `runtime_genesis_pc 0x03A184` (`arcade_pc 0x39F84`) including:
   - full instruction disassembly,
   - `SR` (for Z extraction),
   - `A5`, `D0-D3`,
   - next PC to determine BEQ taken/not taken.
3. Continue same trace until either `runtime_genesis_pc 0x03A19E` is reached or a definitive alternate path is logged.

## Conclusion

Path A leads directly to reset: INDETERMINATE (this attempt).

Evidence is insufficient to make a compliant YES/NO determination under the required stop conditions.
