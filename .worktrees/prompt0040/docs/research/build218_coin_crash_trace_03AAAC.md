# Build 218 Coin-Triggered Crash Trace (`0x03AAAC`)

## Purpose
Trace the new Build 218 crash observed after coin input in startup config flow, with reported signature:
- `PC=0x03AAAC`
- `A0=0x03AA9C`
- `A1=0x000000FF`
- `A5=0xE0FF004C`
- `D0=0x00000840`
- backtrace includes `0x03AAAC`, `0x03A274`, `0x202806`

No code/spec/patcher changes are applied in this pass.

## Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md`
- `README.md`
- `docs/research/semantic_entry_manifest.json`
- `docs/research/semantic_entry_validation_batch_build214.md`
- `docs/research/a1_ff_origin_trace_build214.md`
- `build/maincpu.disasm.txt` (arcade disassembly)
- `dist/Rastan_218.bin` (current emitted ROM)
- `specs/startup_title_remap.json` (shift-table context)
- `m68k-elf-objdump` (ROM-local disassembly)

## Address Mapping Note
Build 218 uses relocated+shifted addresses. For this crash region:
- `genesis 0x03AA9C` maps to arcade callsite context `0x03A890`
- `genesis 0x03AAAC` maps to arcade stream near `0x03A8A0` (operand position, not routine entry)
- `genesis 0x03A274` maps to arcade `0x03A074` dispatcher epilogue callsite

---

## 1) Instruction At `0x03AAAC`
- Disassembly at Build 218 ROM around this site:
  - `0x03AA9C: jsr 0x059F36`
  - `0x03AAA2: move.w #1,(0x0238,A5)`
  - `0x03AAA8: move.w #0x0011,(0x0C4E,A5)`
  - `0x03AAAE: move.w #0x0008,(0x0004,A5)`
- `0x03AAAC` is the displacement/immediate word (`0x0C4E`) of the `move.w #0x0011,(d16,A5)` instruction at `0x03AAA8`; it is **not** an instruction boundary.
- Therefore, the address-error memory access is not directly attributable to an opcode starting at `0x03AAAC`.
- With `A5=0xE0FF004C`, the effective destination for `0x03AAA8` is `A5+0x0C4E` (`0x...0C9A`, even), which is not itself an obvious odd-address fault.

Interpretation: reported `PC=0x03AAAC` is a crash-frame marker within this instruction stream, but the faulting access likely occurred in nearby helper code reached just prior to/around this sequence.

---

## 2) A1 Producer Chain
### Proven local context
- `A0=0x03AA9C` matches the post-coin handler entry selected via jump-table dispatch in this state family.
- That handler immediately calls `0x059F36`.
- In Build 218, `0x059F36` is:
  - `lea 0x10D600, A1`
  - selector index from `A5+0x0118` (`subq #1`, `lsl #2`)
  - base pointer load via absolute table base immediate (`movea.l #0x059E9A, A3`), then `movea.l (A3 + index),A3`
  - looped conversion/copy writes using `A1`.

### Critical proven defect in this path
- In this helper family, absolute table-base immediates are stale after shifts:
  - active code uses `movea.l #0x059E9A,A3`
  - but shifted data/table material in this block is displaced by +0x16 in Build 218.
- This means post-coin selector indexing reads pointer words from the wrong base region, producing malformed pointer/data flow.

### Last-write-to-A1 status
- Exact final instruction writing literal `A1=0x000000FF` is **not directly proven** from static-only slice.
- Last proven intended writer in the active handler path is the prologue in `0x059F36` (`lea 0x10D600,A1`).
- Given observed `A1=0x000000FF`, the crash path includes either:
  1. entry into an internal helper body where A1 prologue was not honored, or
  2. malformed pointer/data flow leading to A1 corruption before fault.

---

## 3) Coin-Triggered Path
### State/step fields involved
From Build 218 disassembly around `0x03AB28` onward:
- coin input read: `move.b 0xE0FF4870,D0` + bit tests
- credits field: `A5+0x0012`
- state flags/timers: `A5+0x0028`, `A5+0x002A`, `A5+0x002C`
- major/sub/step state: `A5+0x0000`, `A5+0x0002`, `A5+0x0004`
- selector bytes: `A5+0x0117`, `A5+0x0118`

### Post-coin transition behavior
- Coin branch updates credits and sets transition flags, clears/initializes transition buffers, then sets `A5+0x0000 = 2`.
- The active dispatch family then reaches handler `0x03AA9C` (A0 observed as `0x03AA9C`), which calls `0x059F36` and updates config/UI state words.

### Active helper during visible flicker/garbage phase
- The active helper in this failing branch is `0x059F36` (shifted form of arcade `0x059D20` caller target family), which is table-driven and writes converted words into target buffers.
- With stale table-base immediate in this helper, malformed table dereference is consistent with corrupted/flickering output before crash.

---

## 4) Semantic Entry Findings (Crash Region)
Checked callsites in the coin-triggered region against arcade-derived expectations:

1. `genesis 0x03AA9C` (arcade context `0x03A890`)
   - actual target: `0x059F36`
   - expected target: shifted arcade entry `0x059D20 -> 0x059F36`
   - classification: `MATCH_ENTRY`

2. `genesis 0x03AC66` (arcade context `0x03AA54`)
   - actual target: `0x05A56C`
   - expected target: shifted arcade entry `0x05A356 -> 0x05A56C`
   - classification: `MATCH_ENTRY`

3. `genesis 0x03ACC0` (arcade context `0x03AAAE`)
   - actual target: `0x05A5F4`
   - expected target: shifted arcade entry `0x05A3DE -> 0x05A5F4`
   - classification: `MATCH_ENTRY`

4. Dispatcher marker from BT: `0x03A274 -> 0x055EB8`
   - classification: `MATCH_ENTRY` (already established in Build 218).

Result: no new `INSIDE_BODY`/`WRONG_FUNCTION` callsite was proven in this coin-region call graph.

---

## 5) ROOT CAUSE
ROOT CAUSE:
- `A1` becomes `0x000000FF` because the post-coin table-driven helper path consumes malformed pointer/data state after dereferencing from a stale absolute table base in the shifted Build 218 image.
- the immediate bad source is the unshifted absolute table-base immediate (`0x059E9A`) used in the active helper family reached from `0x03AA9C`.
- this occurs in the post-coin transition path because coin handling advances into the `0x03AA9C -> 0x059F36` rendering/conversion branch where that stale base is exercised.

Primary classification: **TABLE / POINTER SOURCE ERROR**

---

## 6) Minimal Next Fix Target (Design Only)
=== MINIMAL_FIX_TARGET ===
- fix_area: absolute-long source-range immediate relocation coverage in the shift-fix pipeline for table-base loads used by the `0x03AA9C -> 0x059F36` helper family.
- exact_state_or_path_to_change: ensure table-base absolute immediates in this path (notably `movea.l #0x059E9A,A3` forms) are shift-adjusted to the correct shifted table base before runtime execution.
- why_this_is_the_minimum_change: the proven callsites are already `MATCH_ENTRY`; failure now is in table/pointer base correctness inside the called helper, so changing pointer-base relocation coverage is narrower than retargeting or startup logic changes.
- what_must_NOT_be_changed: no manual callsite retargeting, no startup/launcher/gameplay logic changes, no shift-table content edits, no shadow-RAM reintroduction, no opcode/spec bypasses.

---

## Uncertainties
- Exact final instruction writing literal `A1=0x000000FF` is not proven from static analysis alone.
- Address-error frame decoding in current text dumper may not map one-to-one to true faulting opcode boundary for this event; `0x03AAAC` is definitively an operand location in the active stream.
- Runtime confirmation with full on-screen BlastEm/Exodus dump was not available in this environment; analysis used ROM disassembly + provided crash registers/backtrace.

## Conclusion
The Build 218 coin-triggered crash is not explained by a new semantic-entry mis-target in the local callsites; it is explained by stale absolute table-base immediates in the post-coin helper path, producing malformed pointer/data flow that aligns with the observed `A1=0x000000FF` failure signature.
