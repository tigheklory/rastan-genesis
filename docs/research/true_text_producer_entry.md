# True Text Producer Entry

## Section 1 - Backward Target Resolution
Analysis target: `dist/Rastan_235.bin`.

Backward search from `0x20034C`:
- Full-ROM disassembly search (`objdump`) for direct branch/call targets to `0x20034C` returns exactly one explicit caller:
  - `0x2027C2: jsr 0x20034C`
- Binary literal scan for target longword `0x0020034C` also returns exactly one occurrence:
  - literal at `0x2027C4` (immediate operand of the `jsr` at `0x2027C2`)

Candidate caller classification:

1. Candidate A
- exact PC: `0x2027C2`
- instruction type: direct absolute call (`jsr 0x20034C`)
- true semantic entry or mid-body/internal path: **mid-body/internal** (inside wrapper block)
- register/stack contract status: **not safe as external entry**; entering at `0x2027C2` skips wrapper prologue, then `0x2027C8` (`movea.l (sp)+,a5`) consumes caller return slot as `A5`.

2. Candidate B
- exact PC: `0x2027C0`
- instruction type: wrapper entry (prologue instruction `move.l a5,-(sp)` preceding the call at `0x2027C2`)
- true semantic entry or mid-body/internal path: **true semantic entry**
- register/stack contract status: **preserves expected contract** (save `A5` -> call `0x20034C` -> restore `A5` -> `rts`).

Title dispatch appropriateness:
- The appropriate dispatch entry is Candidate B (`0x2027C0`), not Candidate A (`0x2027C2`).

## Section 2 - Wrapper Identification
Actual wrapper body for `0x20034C` in this ROM:

- exact entry PC: `0x2027C0`
- prologue behavior:
  - `0x2027C0: move.l a5,-(sp)`
- call to producer:
  - `0x2027C2: jsr 0x20034C`
- return behavior:
  - `0x2027C8: movea.l (sp)+,a5`
  - `0x2027CA: rts`

`0x202A4C` relation to this wrapper:
- `0x202A4C` is **unrelated** to the `0x2027C0` wrapper.
- In Build 235, `0x202A4C` is in a separate compare/branch/return routine (`cmpl d1,d2`, `beq`, `subq`, `bne`), not a call wrapper for `0x20034C`.

## Section 3 - Title Dispatch Compatibility
Live title-dispatch entry context (trace at `0x03BD5E -> ...`):
- `D0=0x00000002`
- `A5=0xE0FF004C`
- `SP=0xE0FFFDFA`

Compatibility check for direct target `0x2027C0`:
- required input/state:
  - valid call frame on stack (standard `jsr` return slot)
  - valid `A5` that must survive the producer call
  - producer payload register state (`D0` text id) passed through
- stack assumptions:
  - wrapper adds one long push/pop around internal call; returns with balanced stack
- direct-target safety from `0x03BD5E`:
  - **compatible**; `0x03BD5E` can safely target `0x2027C0` directly.

Compatibility check for non-entry alternatives:
- `0x2027C2` (mid-body) is not safe as dispatch target due missing prologue.
- `0x202A4C` is not a producer wrapper in Build 235 and branches out before any call to `0x20034C`.

## Section 4 - Final Target
=== TRUE_TEXT_PRODUCER_ENTRY ===
- producer_dispatch_pc: `0x03BD5E`
- wrong_target_1: `0x202A4C`
- wrong_target_2: `0x2027C2` (mid-body/internal call site, not entry)
- correct_semantic_target: `0x2027C0`
- why_this_is_the_true_entry: it is the wrapper entry that preserves `A5`, performs `jsr 0x20034C` at `0x2027C2`, restores `A5`, then returns with correct stack discipline
- why_the_others_are_wrong: `0x202A4C` is a non-wrapper branch/return routine; `0x2027C2` is internal and skips required prologue/stack contract

## Section 5 - Conclusion
The correct semantic target for 0x03BD5E is `0x2027C0` because it is the true wrapper entry that preserves call-state and directly executes `jsr 0x20034C`.
