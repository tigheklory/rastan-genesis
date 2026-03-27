# Text Producer Execution Failure

## Section 1 - Entry Confirmation
Probe artifacts:
- `/tmp/text_producer_exec_probe.txt`
- `/tmp/text_producer_contract_trace.txt`

Required hit counts:
- `0x2027C0`: `1`
- `0x2027C2`: `1`
- `0x20034C`: `1`

Result: execution **does reach** `0x20034C`.

## Section 2 - Register State At Entry
Entry snapshots from `/tmp/text_producer_exec_probe.txt`:

Before producer call (`PRE_20034C_CALL`, PC=`0x2027C2`):
- `A0=0x00000008`
- `A4=0x00000000`
- `A5=0xE0FF004C`
- `D0=0x00000002`
- `SP=0xE0FFFDF6`

At producer entry (`ENTRY_20034C`, PC=`0x20034C`):
- `A0=0x00000008`
- `A4=0x00000000`
- `A5=0xE0FF004C`
- `D0=0x00000002`
- `SP=0xE0FFFDF2`

Likely meaning by contract (from disassembly behavior):
- `D0`: text/command selector passed into producer.
- `A5`: frontend work/state base (preserved by wrapper).
- `SP`: normal call chain frame (`0x03BD5E -> 0x2027C0 -> 0x20034C`).
- `A0`: selector-derived offset seed used early in table addressing.
- `A4`: not consumed in first producer prologue steps.

## Section 3 - Execution Trace (First 10 Instructions)
Disassembly source: `m68k-elf-objdump` on `/tmp/r235_target_2027c0.bin`.
Runtime source: `/tmp/text_producer_exec_probe.txt`.

STEP 1
- PC: `0x20034C`
- instruction: `moveml %d2-%d7/%a2-%a5,%sp@-`
- effect: saves callee-saved working set to stack.

STEP 2
- PC: `0x200350`
- instruction: `movew %d0,%d4`
- effect: copies selector `D0=0x0002` into `D4` low word.

STEP 3
- PC: `0x200352`
- instruction: `moveq #127,%d1`
- effect: loads `D1=0x0000007F` mask seed.

STEP 4
- PC: `0x200354`
- instruction: `andl %d4,%d1`
- effect: masked selector index (`D1` becomes `0x00000002`).

STEP 5
- PC: `0x200356`
- instruction: `addl %d1,%d1`
- effect: doubles index (`D1=0x00000004`).

STEP 6
- PC: `0x200358`
- instruction: `moveal %d1,%a0`
- effect: `A0` set to scaled offset seed.

STEP 7
- PC: `0x20035A`
- instruction: `addal %d1,%a0`
- effect: `A0` advanced again for table addressing.

STEP 8
- PC: `0x20035C`
- instruction: `moveal #0x0003BD92,%a1`
- effect: loads descriptor table base into `A1`.

STEP 9
- PC: `0x200362`
- instruction: `moveal %a0@(0,%a1:l),%a2`
- effect: loads descriptor pointer (`A2` observed as `0x0003BCBE`).

STEP 10
- PC: `0x200366`
- instruction: `cmpaw #0,%a2`
- effect: null-checks descriptor pointer before body path.

## Section 4 - Failure Mode
Selected failure mode: **B) `0x20034C` executes but exits early (non-productive path).**

Proof:
- Entry and execution are confirmed (`HIT 20034C 1`).
- Trace reaches producer body checks (`0x200398`, `0x20039A`) and then return-side path (`0x2004B2`, `0x2004B8`, `0x20036C`, `0x200370`) in the same frame (`f=666`) from `/tmp/text_producer_contract_trace.txt`.
- No producer draw-write site was observed in this call (`HIT 2004A2 0` in `/tmp/text_producer_contract_trace.txt`; `0x2004A2` is the `movew %d0,0xC00000` VDP data write site in disassembly).
- Write-ownership probe shows no text-shadow writes from this producer family:
  - `/tmp/text_producer_write_probe.txt`: `from_20034c_exact=0`, `from_20034c_family=0`.

## Section 5 - Final Breakpoint
=== TEXT_PRODUCER_EXECUTION_FAILURE ===
- wrapper_entry: `0x2027C0`
- producer_entry: `0x20034C`
- failure_type: `B) executes but exits early`
- exact_reason: producer call contract is valid enough to enter `0x20034C`, but this invocation follows a non-productive branch/return path and never reaches the producer VDP data-write site (`0x2004A2`), so no visible text payload is emitted.

## Section 6 - Conclusion
0x20034C fails to produce visible output because it executes once on a non-productive branch/return path and does not reach its VDP text write site.
