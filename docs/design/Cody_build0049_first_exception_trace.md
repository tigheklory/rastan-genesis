# Cody — Build 0049 First Exception Trace

Agent: Cody  
Type: Runtime Trace / Verification  
Build Context: Build 0049 `rastan-direct`

## Scope

Runtime trace only. No code/spec/tool fixes performed.

## Capture environment

- Emulator: MAME `genesis`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0049.bin`
- Debug mode: `-debug -debugger none`
- Breakpoint/trace script: temporary Lua harness under `/tmp`
- Address space labels used below:
  - `runtime_genesis_pc`
  - `arcade_pc`
  - `HW_ADDRESS`

## Phase 1 — Milestones

Breakpoints set:

- `runtime_genesis_pc 0x00000202` (`_start`)
- `runtime_genesis_pc 0x00000206` (`LEA 0x00FF0000,%sp`)
- `runtime_genesis_pc 0x00000226` (`_bootstrap`)
- `runtime_genesis_pc 0x0000023C` (`jmp (0x00003A200).l` site in `_bootstrap`)
- `runtime_genesis_pc 0x0003A200` (arcade handoff target)
- `runtime_genesis_pc 0x000700C2` (`_vblank_service`)
- `runtime_genesis_pc 0x0003A208` (arcade L5 handler entry via `_vblank_service` tail-JMP)
- Exception stubs:
  - `runtime_genesis_pc 0x000002FA` (bus error stub)
  - `runtime_genesis_pc 0x00000300` (address error stub)

Observed breakpoint hits (from debugger console capture):

- `MILESTONE _start pc=000204 sp=00FF0000 a5=00000000 sr=2700`
- `MILESTONE lea_sp_before pc=000208 sp=00FF0000 a5=00000000`
- `MILESTONE lea_sp_after pc=00020E sp=00FF0000 a5=00000000`
- `MILESTONE _bootstrap pc=000228 sp=00FEFFFC a5=00000000 sr=2700`
- `MILESTONE _vblank_service pc=0700C4 sp=00FEFFC2 a5=00000000 sr=2600`
- `MILESTONE arcade_3a208 pc=03A20A sp=00FEFFC2 a5=00000000 sr=2608`

Not observed in capture window:

- `_bootstrap` pre-handoff breakpoint at `runtime_genesis_pc 0x0000023C`
- Arcade handoff target `runtime_genesis_pc 0x0003A200`
- Exception stubs `runtime_genesis_pc 0x000002FA` and `0x00000300`

## Phase 2 — SP tracking

- ROM header initial SP (vector long at ROM offset `0x000000`): `0x00FF0000`
- Before `_start` LEA (`runtime_genesis_pc 0x00000206` vicinity): `0x00FF0000`
- After `_start` LEA (`runtime_genesis_pc 0x00000206` executed): `0x00FF0000`
- On `_bootstrap` entry (`runtime_genesis_pc 0x00000226`): `0x00FEFFFC`
- On `_bootstrap` exit just before `jmp 0x0003A200`: **NOT OBSERVED**
- On entry to `runtime_genesis_pc 0x0003A200`: **NOT OBSERVED**
- At first address-error fault from trap frame: **NOT OBSERVED**

## Phase 3 — Exception capture status

First address-error exception capture: **NOT OBSERVED** in this environment/capture window.

Capture windows executed:

- 179 emulated seconds (`-seconds_to_run 180 -nothrottle`) with debugger breakpoints
- 899 emulated seconds (`-seconds_to_run 900 -nothrottle`) with debugger breakpoints + instruction trace

In both windows:

- `runtime_genesis_pc 0x00000300` (address error stub) not hit
- `runtime_genesis_pc 0x000002FA` (bus error stub) not hit

Because no first exception was hit, the following required items are unavailable:

- Faulting instruction at first address error
- Fault address from first address-error trap frame
- D0-D7/A0-A6/SR snapshot at first address error
- Last 20–50 executed instructions before first address error

## Phase 4 — Execution path evidence (captured)

Instruction trace tail from extended run shows interrupt path:

- `_vblank_service` at `runtime_genesis_pc 0x000700C2`
- Tail-JMP to `runtime_genesis_pc 0x0003A208` (`arcade_pc 0x3A008`)
- Execution proceeds in arcade frontend range (`runtime_genesis_pc 0x03A20x` / `0x03A1xx`)

Observed disassembly sequence excerpt (from trace):

- `0700FC: jmp $3a208.l`
- `03A208: ori #$f00, SR`
- `03A20C: nop`
- `03A218: move.w ($2,A5), D0`
- `03A23E: bsr $3ad7c`
- `03AD84: cmpi.w #$100, ($12,A5)`
- `03A18C: move.l #$a0000, D1`
- `03A192: move.l $0.w, D0`
- `03A196: subi.l #$1, D1`
- `03A19C: bne $3a192`

## STOP result

STOP triggered: **YES**

Reason:

- First exception (specifically first address error) could not be captured in this MAME-based runtime window.
- Therefore mandatory exception-frame outputs cannot be produced from this capture alone.

Additional capture needed to resolve:

1. A runtime environment/run where the first address error actually occurs (e.g., Exodus run matching the reported `FAULT PC 0x00000116`, `FAULT ADDR 0x00000196`).
2. Instruction-level history (20–50 instructions) immediately preceding that first address error.
3. Trap-frame register snapshot at that first address error (stacked SR/PC + full D/A register set).

## Architecture compliance

Confirmed: trace-only task, no architecture or code modifications performed.
