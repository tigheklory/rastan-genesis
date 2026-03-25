# Semantic Entry Validation (Build 214) - Step 1

## 1) Purpose
Create a minimal read-only semantic relocation validation layer that detects when a callsite lands on a routine body address instead of the intended semantic routine entry.

## 2) Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (latest relevant sections)
- `README.md`
- `docs/research/a1_ff_origin_trace_build214.md`
- `docs/research/semantic_entry_manifest.json`
- `tools/check_semantic_entries.py`
- `dist/Rastan_214.bin`
- `build/maincpu.disasm.txt`

## 3) Manifest Format
The step-1 manifest is:
- path: `docs/research/semantic_entry_manifest.json`
- top-level keys:
  - `version`
  - `description`
  - `routines[]`
  - `validation_cases[]`

Per routine (current single seeded routine):
- `logical_name`
- `arcade_entry`
- `genesis_entry`
- `known_non_entry_internal_targets[]`
- `notes`

Per validation case:
- `case_id`
- `callsite_genesis`
- `callsite_arcade_context`
- `logical_target`
- `observed_target_genesis` (fallback evidence field)
- `evidence`

## 4) Validation Method
`tools/check_semantic_entries.py` performs read-only checks:
1. Loads manifest routine and case definitions.
2. Resolves each callsite target from ROM bytes first (`dist/Rastan_214.bin`):
   - decodes `JSR/JMP abs.l` and `BSR` forms.
3. Optionally falls back to disassembly-derived target (`build/maincpu.disasm.txt`) when needed.
4. Final fallback is manifest `observed_target_genesis` when automated decoding is unavailable.
5. Compares resolved target to declared semantic entry and classifies:
   - `MATCH_ENTRY`
   - `INSIDE_BODY`
   - `OUTSIDE_EXPECTED`
   - `UNRESOLVED`

Address mapping note for this pass:
- Validation is keyed to **Genesis ROM addresses** for Build 214.
- `callsite_arcade_context` is retained for traceability only.

## 5) Current Test Case Result
Case: `build214_wrong_entry_03A274`
- callsite:
  - `arcade_addr: 0x03A074` (context)
  - `genesis_rom_addr: 0x03A274`
- resolved live target from ROM bytes:
  - `genesis_rom_addr: 0x055EA2`
- declared semantic entry from manifest:
  - `genesis_rom_addr: 0x055EB8`
- classification:
  - `INSIDE_BODY`
- reason:
  - target matches known non-entry internal address for this routine.

## 6) Whether `0x03A274` Would Be Flagged By This System
Yes.

For Build 214, this semantic validation layer flags `0x03A274 -> 0x055EA2` as `INSIDE_BODY` against declared entry `0x055EB8`.

## 7) Limitations
- Step-1 scope is intentionally tiny: one routine and one test case only.
- Routine-body membership is currently manifest-driven (`known_non_entry_internal_targets`) rather than inferred from full CFG/function boundary recovery.
- `build/maincpu.disasm.txt` is not a complete Build-214-relocated disassembly source for all addresses; ROM byte decoding is the authoritative source in this pass.
- No automatic retargeting/fix generation is implemented.

## 8) Next Expansion Step
Expand manifest coverage gradually:
1. Add more semantic routine entries and known non-entry internal targets.
2. Add additional callsite cases from proven crash/adverse paths.
3. Add optional routine range metadata (`body_start`/`body_end`) to improve `INSIDE_BODY` classification beyond exact internal-address lists.
4. Integrate checker into CI as a read-only preflight gate before release builds.
