# Arcade-Anchored Semantic Entry Validation + Shift Table Verification (Build 214)

## Objective
Correct semantic-entry validation so authoritative routine truth comes from arcade addresses, then verify whether Build 214 wrong-entry targets come from missing shift entries, bad shift application, or semantic-entry mismatch.

## Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (latest relevant sections)
- `README.md`
- `docs/research/a1_ff_origin_trace_build214.md`
- `build/maincpu.disasm.txt` (arcade truth disassembly)
- `build/regions/maincpu.bin` (arcade ROM bytes)
- `dist/Rastan_214.bin` (Genesis output for call-target decode only)
- `specs/startup_title_remap.json` (`shift_replacements` authoritative list)
- `tools/translation/shift_table_patcher.py` (current shift logic)
- `tools/check_semantic_entries.py` (updated arcade-anchored checker)

## Address Mapping Rule (Authoritative)
For this validation pass:
- `arcade_entry` is authoritative semantic truth.
- `expected_genesis_entry = arcade_entry + relocation_delta + cumulative_shift(shift_pc <= arcade_entry)`
- `relocation_delta = 0x000200` (from policy)

No semantic entry is derived from `dist/Rastan_214.bin` directly.

## Phase 1 - Arcade Ground Truth

### Routine: `frontend_copy_dispatch_entry`
- `arcade_entry_address (confirmed): 0x055CA2`
- first instructions (arcade):
  1. `0x055CA2: cmpi.w #0, (0x4A,A5)`
  2. `0x055CA8: beq.w 0x055DD6`
  3. `0x055CAC: cmpi.w #0x00AA, (0x4A,A5)`
  4. `0x055CB2: bne.s 0x055CD6`
  5. `0x055CB4: cmpi.w #0x003C, (0x13CC,A5)`
  6. `0x055CBA: bne.s 0x055CCE`
  7. `0x055CBC: move.b #0xAA, 0x10FFFF`
  8. `0x055CC4: move.w #0, (0x4A,A5)`
  9. `0x055CCA: bra.w 0x055DD6`
  10. `0x055CCE: addq.w #1, (0x13CC,A5)`
- internal addresses NOT valid as entry:
  - `0x055C7A` (copy-loop helper entry)
  - `0x055C7C` (word-copy loop body)
  - `0x055C8C` (inner copy body uses pre-initialized regs)
  - `0x055CD6` (state branch body)
- what breaks if entered mid-body:
  - copy loop addresses assume `A0/A1/A2/D2` setup already occurred in prior helper prologue; mid-body entry can dereference stale/invalid pointers.

### Routine: `frontend_selector_seed_gate_entry`
- `arcade_entry_address (confirmed): 0x04527E`
- first instructions (arcade):
  1. `0x04527E: move.w 0x05FF9E, D1`
  2. `0x045284: not.w D1`
  3. `0x045286: andi.w #7, D1`
  4. `0x04528A: addq.w #1, D1`
  5. `0x04528C: tst.b (0x0104,A5)`
  6. `0x045290: bne.s 0x04529A`
  7. `0x045292: move.b D1, (0x0118,A5)`
  8. `0x045296: move.b D1, (0x0117,A5)`
  9. `0x04529A: rts`
- internal addresses NOT valid as entry:
  - `0x045284`, `0x04528C`, `0x045292`, `0x045296`
- what breaks if entered mid-body:
  - `D1` normalization may be skipped; selector/gate state writes can be bypassed or applied with invalid intermediate register state.

Note for failing case `0x03A85C`: arcade truth shows it calls `0x04529C` (adjacent companion routine), not `0x04527E`.

## Phase 2 - Arcade -> Genesis Derived Mapping
Using `shift_replacements` (22 entries) + `relocation_delta=0x200`:

- `frontend_copy_dispatch_entry`
  - `arcade_entry: 0x055CA2`
  - cumulative shift at entry: `+22`
  - `expected_genesis_entry: 0x055EB8`
  - previous manifest genesis entry: `0x055EB8` (match)

- `frontend_selector_seed_gate_entry`
  - `arcade_entry: 0x04527E`
  - cumulative shift at entry: `+28`
  - `expected_genesis_entry: 0x04549A`
  - previous manifest genesis entry: `0x04549A` (match)

- companion selector layout routine (required for failing callsite `0x03A85C`):
  - `arcade_entry: 0x04529C`
  - cumulative shift at entry: `+28`
  - `expected_genesis_entry: 0x0454B8`

## Phase 3 - Failing Callsite Validation

### Case A: `0x03A274`
- decoded call: `JSR abs.l`
- actual target in Build 214: `0x055EA2`
- expected target (derived): `0x055EB8`
- classification: `INSIDE_BODY`

### Case B: `0x03A93E`
- decoded call: `JSR abs.l`
- actual target in Build 214: `0x04547E`
- expected target (derived): `0x04549A`
- classification: `WRONG_FUNCTION`

### Case C: `0x03A85C`
- decoded call: `JSR abs.l`
- actual target in Build 214: `0x04549C`
- expected target (derived from arcade call intent to `0x04529C`): `0x0454B8`
- classification: `WRONG_FUNCTION`

## Phase 4 - Shift Table Audit

### shift_table_entry_count
- `22`

### Relevant shift entries affecting requested regions

#### Region near `0x03A274`
Entries with `arcade_pc <= 0x03A3FF`:
- `0x00016A (+0)`
- `0x000170 (+0)`
- `0x03A20E (+2)`
- `0x03A264 (+2)`

#### Region near `0x04527E`
Entries with `arcade_pc <= 0x0452FF`:
- `0x00016A (+0)`, `0x000170 (+0)`
- `0x03A20E (+2)`, `0x03A264 (+2)`, `0x03A640 (+2)`, `0x03A6C4 (+2)`
- `0x03A818 (+0)`, `0x03A820 (+2)`, `0x03A854 (+2)`, `0x03A8E0 (+2)`
- `0x03A9C6 (+2)`, `0x03A9D4 (+2)`, `0x03B8E8 (+2)`, `0x03B8F0 (+2)`
- `0x03C3FE (+2)`, `0x041DAE (+2)`, `0x041F5E (+2)`
- cumulative shift at `0x04527E`: `+28`

#### Region `0x055E00..0x056000`
Entries with `arcade_pc <= 0x056000`:
- all 22 shift entries (including negative scroll entries at `0x055AB4/BC/C4/CC`)
- cumulative shift at region start/end: `+22`

### Shift application behavior evidence
- `shift_table_patcher` run on arcade ROM reports:
  - `7194 branch fix(es)`
  - `0 abs-long fix(es)`
- `parse_disasm()` currently parses `JSR abs.l` lines as size `2` (not `6`) due byte-column regex behavior, which prevents absolute-target fix pass from visiting those call instructions.
- Result: call targets receive relocation delta (`+0x200`) but miss semantic shift delta (`+22` or `+28`) in affected cases.

## Root Cause Classification Per Failing Case

### `0x03A274`
- ROOT CAUSE TYPE: `SHIFT_INCORRECT`
- REQUIRED FIX TYPE: `correct shift offset` (ensure abs-long call target receives shift delta, not only relocation delta)

### `0x03A93E`
- ROOT CAUSE TYPE: `SHIFT_INCORRECT`
- REQUIRED FIX TYPE: `correct shift offset`

### `0x03A85C`
- ROOT CAUSE TYPE: `SHIFT_INCORRECT`
- REQUIRED FIX TYPE: `correct shift offset`
- secondary tooling note: prior Step-2 manifest grouped this call under the wrong logical routine; corrected in arcade-anchored manifest.

## Determination: A / B / C
- (A) missing shift-table entries: **NO**
- (B) incorrect shift application: **YES (primary)**
- (C) semantic entry misalignment not solvable by shift alone: **secondary only for prior manifest grouping of 0x03A85C, not the ROM target defect itself**

## Recommendation for Next Fix Step
- Fix absolute-long target shift application in tooling path (currently missing due instruction-size parsing issue in `parse_disasm()`), then rerun semantic checker.
- Do not retarget callsites manually before tooling shift correction is verified.
