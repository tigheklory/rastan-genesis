# Semantic Entry Validation Batch Report (Build 214) - Step 2

## 1) Purpose
Expand semantic entry validation from a single proven case to a proactive batch checker over a curated high-risk routine set, without applying fixes.

## 2) Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (latest relevant sections)
- `README.md`
- `docs/research/semantic_entry_validation_build214.md`
- `docs/research/semantic_entry_manifest.json` (expanded Step-2 manifest)
- `tools/check_semantic_entries.py` (batch checker)
- `dist/Rastan_214.bin` (target ROM for call-target decode)
- `build/maincpu.disasm.txt` (fallback/reference)
- `m68k-elf-objdump` output for startup/frontend ranges in Build 214

## 3) Manifest Coverage Summary
- routines covered: **8**
- validation cases: **15**
- routine class focus:
  - copy/dispatch entry with internal loop body
  - selector seed gate helper
  - frontend sprite bridge (prologue-sensitive)
  - scroll sync bridge
  - primary text writer entry
  - frontend sound dispatch helper
  - frontend transition mode helper
  - orientation gate helper (relative branch target coverage)

## 4) Validation Method
`tools/check_semantic_entries.py`:
1. Reads routine/validation-case manifest.
2. Decodes call targets from ROM bytes at each callsite (`JSR/JMP abs.l`, `BSR.b`, `BSR.w`).
3. Falls back to disassembly target map if ROM decode is unavailable.
4. Falls back to `observed_target_genesis` from manifest if still unresolved.
5. Classifies each case:
   - `MATCH_ENTRY`
   - `INSIDE_BODY`
   - `OUTSIDE_EXPECTED`
   - `UNRESOLVED`
6. Emits per-case details, classification counts, and a human-review shortlist.

Address mapping note:
- Step-2 validation is keyed to **Genesis ROM addresses** in Build 214.
- Arcade addresses are retained in manifest as context only.

## 5) Batch Results Summary
- `MATCH_ENTRY`: **12**
- `INSIDE_BODY`: **3**
- `OUTSIDE_EXPECTED`: **0**
- `UNRESOLVED`: **0**

## 6) Cases Classified MATCH_ENTRY
- `build214_sprite_bridge_03A40E` (`0x03A40E -> 0x20060C`)
- `build214_sprite_bridge_03A466` (`0x03A466 -> 0x20060C`)
- `build214_sprite_bridge_03AAEC` (`0x03AAEC -> 0x20060C`)
- `build214_scroll_bridge_03ADCC` (`0x03ADCC -> 0x200D4E`)
- `build214_scroll_bridge_03ADD2` (`0x03ADD2 -> 0x200D4E`)
- `build214_text_writer_000592` (`0x000592 -> 0x03BD48`)
- `build214_text_writer_0007C0` (`0x0007C0 -> 0x03BD48`)
- `build214_sound_dispatch_03A284` (`0x03A284 -> 0x0512C6`)
- `build214_sound_dispatch_0553E2` (`0x0553E2 -> 0x0512C6`)
- `build214_mode_helper_03A5A6` (`0x03A5A6 -> 0x05A642`)
- `build214_mode_helper_03A624` (`0x03A624 -> 0x05A642`)
- `build214_orientation_gate_03ADC0` (`0x03ADC0 -> 0x03AFEA`)

## 7) Cases Classified INSIDE_BODY
- `build214_wrong_entry_03A274`
  - callsite `0x03A274`, resolved `0x055EA2`, declared entry `0x055EB8`
  - confidence: HIGH
- `build214_selector_seed_callsite_03A93E`
  - callsite `0x03A93E`, resolved `0x04547E`, declared entry `0x04549A`
  - confidence: MEDIUM
- `build214_selector_seed_callsite_03A85C`
  - callsite `0x03A85C`, resolved `0x04549C`, declared entry `0x04549A`
  - confidence: MEDIUM

## 8) Cases Classified OUTSIDE_EXPECTED
- none

## 9) Cases Classified UNRESOLVED
- none

## 10) Which Cases Need Immediate Human Attention
Immediate review set from this batch:
1. `build214_wrong_entry_03A274` (already proven crash-linked, HIGH confidence).
2. `build214_selector_seed_callsite_03A93E` (MEDIUM confidence, selector/gate-sensitive routine).
3. `build214_selector_seed_callsite_03A85C` (MEDIUM confidence, selector/gate-sensitive routine).

## 11) Limitations
- Curated scope only (8 routines, 15 cases), not whole-ROM semantic modeling.
- `INSIDE_BODY` detection depends on manifest-provided `known_non_entry_internal_targets` rather than full CFG/function-boundary inference.
- Some routine names are functional labels derived from current research context; they are not authoritative symbol exports.
- No CI gating activated in this pass.

## 12) Recommended Next Validation Expansion
1. Add 4-8 additional high-risk routines from the same startup/frontend execution slice where entry prologue sets address registers/counters.
2. Add routine-range metadata (`body_start`/`body_end`) to reduce dependence on exact listed internal targets.
3. Add a dedicated optional CI/read-only mode (`--fail-on-suspect`) once routine coverage is stable.
4. Promote MEDIUM-confidence selector-seed cases to HIGH through targeted Ghidra cross-check of intended entry ownership.

Would this layer catch the known Build 214 wrong-entry issue? **Yes** (`0x03A274` remains flagged `INSIDE_BODY`).
Additional wrong-entry-like cases beyond `0x03A274`: **Yes, 2 MEDIUM-confidence selector-seed cases**.
