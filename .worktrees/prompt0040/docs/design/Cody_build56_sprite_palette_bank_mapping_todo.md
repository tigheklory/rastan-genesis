# Cody Build 56 Sprite Palette Bank Mapping TODO

## Why High Banks Are SKIPped In Build 55
- Build 55 palette translation emits only proven tilemap-consumed banks 0..3.
- High-bank sprite mapping remains unproven in current evidence (`docs/design/Cody_build55_palette_bank_mapping_evidence.md`, sprite section marked PARTIAL/UNKNOWN for direct arcade bank provenance).
- Build 55 helpers therefore apply the bounded rule:
  - emit Genesis staging for banks 0..3
  - skip Genesis staging for banks >= 4

## Observed High Banks (current evidence)
- `0x04`
- `0x05`
- `0x06`
- `0x33`
- `0x41`
- `0x43`
- sibling `0x045DE4` path covers banks 48..79 (`0x30..0x4F`) via `0x200600 + idx*0x80`

## Why This Is Not Scaffolding
- Build 55 behavior is bounded to proven evidence only.
- The skip rule is a production limitation tied to missing sprite-bank mapping evidence, not a temporary bypass mechanism.
- No alternate lifecycle or debug-only execution path was added.

## Build 56 Required Task
- Trace sprite `%d1` / `%d7` provenance back to arcade sprite attributes.
- Derive explicit mapping:
  - arcade sprite palette bank -> Genesis CRAM line
- Validate against runtime behavior and MAME comparison for sprite colors.

## Files To Inspect For Build 56
- `apps/rastan-direct/src/pc090oj_hooks.s`
- `build/maincpu.disasm.txt`
- `docs/design/Cody_build55_palette_bank_mapping_evidence.md`
- `docs/design/Andy_build55_palette_translation_design.md`

## Trigger Condition
- After Build 55 boots with non-white CRAM behavior verified and baseline stability confirmed.
- Then compare sprite colors vs MAME and run the Build 56 sprite palette mapping task.
