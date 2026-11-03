# First Graphics Execution Breakpoint

## Section 1 - Identify First Real Producer
Selected producer: **title text producer dispatch**.

- Exact address: `0x03BD5E`
- Instruction at producer: `jsr 0x2027C0`
- Register carrying producer data at entry (observed):
  - `D0=0x00000002` (`/tmp/first_graphics_break_trace.txt`, `TRACE f=665 pc=03BD5E ... d0=00000002`)
- What it is trying to produce:
  - text producer path (text-id dispatch into text writer flow)

Proof this producer executed:
- `HIT pc=03BD5E count=1 first=665 last=665`

## Section 2 - Step-by-Step Execution Trace
Trace is from real execution at frame 665 (`/tmp/first_graphics_break_trace.txt`).

STEP 1:
- PC: `0x03BD5E`
- instruction: `jsr 0x2027C0`
- result: control transfers to `0x2027C0`; `D0=0x00000002`

STEP 2:
- PC: `0x2027C0`
- instruction: `movew %a2@+,%a1@+`
- result: word copy occurs; pointers advance (`A1`/`A2`)

STEP 3:
- PC: `0x2027C2`
- instruction: `moveq #0,%d1`
- result: `D1` reset to `0`

STEP 4:
- PC: `0x2027C4`
- instruction: `moveq #0,%d0`
- result: original producer value in `D0` is overwritten (`D0=0`)

STEP 5:
- PC: `0x2027C6`
- instruction: `moveb %a0@+,%d0`
- result: `D0` replaced from byte stream at `A0`

STEP 6:
- PC: `0x2027C8`
- instruction: `moveb %a0@+,%d1`
- result: `D1` replaced from next byte

STEP 7:
- PC: `0x2027CA`
- instruction: `addw %d0,%d0`
- result: `D0` doubled

STEP 8:
- PC: `0x2027CC`
- instruction: `addw %d0,%d0`
- result: `D0` doubled again (index scaling)

STEP 9:
- PC: `0x2027CE`
- instruction: `moveal %a3@(0,%d0:w),%a4`
- result: `A4` loaded from indexed table source

STEP 10:
- PC: `0x2027D2`
- instruction: `jmp %a4@`
- result: indirect jump; this path does **not** go to text wrapper `0x202A4C`

Break confirmation right after this chain:
- `HIT pc=202A4C count=0`
- `HIT pc=20034C count=0`
- `HIT pc=200000 count=0`
- `HIT pc=2001A6 count=0`

## Section 3 - Data Tracking (Mandatory)
Tracked data: producer text-id value entering `0x03BD5E` in `D0`.

Observed data path:
1. Entry at producer:
   - `D0=0x00000002` at `0x03BD5E`
2. Immediate transform in wrong target path:
   - `0x2027C4` forces `D0=0`
   - `0x2027C6/0x2027C8` reload `D0/D1` from `A0` byte stream
3. Indirect dispatch:
   - `0x2027CE/0x2027D2` uses computed index and jumps via `A4`

Where data goes (observed):
- It does **not** enter real text producer wrapper path (`0x202A4C`) and does **not** enter text producer function (`0x20034C`).
- Text shadow writes occur at `0xFFC84C..0xFFCC4B`, but writer PCs are clear/maintenance paths:
  - `text_writer_pc 03AF5A 1024`
  - `text_writer_pc 20161E 1010`

YES/NO data reach answers for this traced producer data:
- does this data reach VRAM? **NO**
- does this data reach SAT? **NO**
- does this data reach plane writes? **NO**

Proof:
- No execution of `0x20034C`, `0x200000`, `0x2001A6` in trace.
- `snap text_cell00 attr=0000 glyph=0020` (space, not produced visible text cell).

## Section 4 - VDP Verification (Hard Proof)
Using observed runtime evidence (`/tmp/first_graphics_break_trace.txt` + `/tmp/first_graphics_vdp_hist.txt`):

- VRAM contains non-zero tile data? **NO (for traced graphics element path)**
  - Producer path never reaches tile/text producers (`20034C=0`, `200000=0`, `2001A6=0`).
  - Geometry upload stream shows zero payload on active transfer PCs (examples: `pc=202EFC/202F00/202F04/202F08/202F0C/202F10/202F14/202F1C` all `zero=count`).

- SAT contains valid entries? **NO**
  - `snap blockA_nonzero=0/144`
  - `snap blockB_nonzero=3/32`
  - This is not a valid drawable SAT content set.

- plane memory contains non-space tiles? **NO**
  - `snap text_cell00 attr=0000 glyph=0020`
  - plus zero hits at plane producers (`200000=0`, `2001A6=0`).

## Section 5 - First Breakpoint (Required)
=== FIRST_GRAPHICS_BREAKPOINT ===
- PC: `0x03BD5E`
- expected: dispatch should enter semantic text producer path (`0x202A4C -> 0x20034C`) so text-id data becomes plane-visible text output
- actual: dispatch enters `0x2027C0` path, executes index/copy logic, and never reaches `0x202A4C` or `0x20034C`
- failure reason: **wrong jump target** at first producer dispatch

## Section 6 - Why Producers Are Not Executing
Producer functions observed NOT executing in this trace window:

- `0x20034C` (text producer): NOT executing
  - Why: **wrong jump target** (`0x03BD5E -> 0x2027C0`, not `0x202A4C`)

- `0x200000` (tile plane writer): NOT executing
  - Why: **wrong data preventing execution** (text producer path does not run, so no translated text/tile payload is generated for plane writer path)

- `0x2001A6` (tile plane writer): NOT executing
  - Why: **wrong data preventing execution** (same observed condition as above in this trace)

## Section 7 - Final Conclusion (Strict Format)
The first real graphics failure occurs at `0x03BD5E` because it dispatches to the wrong target (`0x2027C0` instead of `0x202A4C -> 0x20034C`), which prevents text producer output from ever reaching plane-visible VDP output.
