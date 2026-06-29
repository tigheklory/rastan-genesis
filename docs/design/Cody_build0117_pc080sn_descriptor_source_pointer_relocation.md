# Cody - Build 0117 PC080SN Descriptor Source Pointer Relocation Hook

**Date:** 2026-06-29
**Type:** Implementation + verification
**Build context:** Build 0116 -> Build 0117, `rastan-direct`
**Scope:** Implement Andy's PC080SN descriptor source-pointer relocation design for the item-page descriptor rebuild at `runtime_genesis_pc 0x00055B04`. No KF-038/bg_fill/render-loop/sprite/HUD/window work. No bookmark cycle. No diagnostic ROM/scaffolding.

## Phase 0

Classification: **EXTENDING**. Required priors read: `RULES.md`, `ARCHITECTURE.md`, latest `AGENTS_LOG.md`, and `docs/design/Andy_pc080sn_descriptor_source_pointer_relocation_design.md`.

Relevant context:

- Build 0116 SHA: `94f157ecc296cb9e9c2521ec6c3d462671c59dde75d2fe42274508795a4eb30f`.
- Build 0116 fixed the raw `0x0010D0xx -> 0x00FF10xx` WRAM literal issue but exposed the next issue: descriptor source-pointer values in `Genesis-WRAM 0x00FF1000` are still arcade ROM addresses and must be relocated before dereference.
- `build/rastan-direct/address_map.json` is authority for arcade-to-Genesis correlation.

No contradiction detected. STOP not triggered in Phase 0.

## Address-Mapping Discipline

All checked source pointers map exactly through `build/rastan-direct/address_map.json`.

The entry patch site is already a generated `patched_site` segment:

- `arcade_pc 0x00055904 -> runtime_genesis_pc 0x00055B04`
- Segment kind: `patched_site`
- Size: `6` bytes

The descriptor source pointers all resolve through the JSON `arcade_copy` segment:

- JSON arcade segment: `[0x00000F08, 0x0003A00C)`
- JSON Genesis segment start: `0x00001108`
- Sample mappings: `arcade_pc 0x0001691C -> genesis_rom_offset 0x00016B1C`, `0x00018BDC -> 0x00018DDC`, `0x0002399C -> 0x00023B9C`, `0x0003725C -> 0x0003745C`

The hook constants encode the JSON segment bounds and Genesis start. The arithmetic consequence equals a `0x200` delta for this segment, but the proof source is the JSON map.

## Patch-Shape Correction

Andy's design expected a new opcode replacement count increase, but Build 0116 already had an `opcode_replace` at `arcade_pc 0x055904` for the literal rebase:

```json
"arcade_pc": "0x055904",
"original_bytes": "207C0010D000",
"replacement_bytes": "207C00FF1000"
```

Adding a second `opcode_replace` at the same address would create overlapping patched-site segments. The safe implementation replaced that existing entry with the 6-byte absolute jump:

```json
"replacement_bytes": "4EF9{symbol:genesistan_hook_pc080sn_descriptor_rebuild}"
```

Therefore:

- `opcode_replace` patched-site count stayed `129`.
- `total_genesis_bytes_covered` increased only by the new helper body: `0x17CF08 -> 0x17CF68` (`+0x60`).
- This differs from the design's `+1` count expectation only because the target site was already occupied by the Build 0116 opcode replacement.

## Implementation

Files changed for implementation:

- `apps/rastan-direct/src/tilemap_hooks.s`
- `specs/rastan_direct_remap.json`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

Added helper symbol:

- `genesistan_hook_pc080sn_descriptor_rebuild`

The helper reimplements the original `0x55B04..0x55B46` rebuild behavior while relocating each runtime-built source pointer through the JSON segment before descriptor dereference.

Helper behavior:

1. Uses `Genesis-WRAM 0x00FF1000` as the raw source-pointer table.
2. Uses `Genesis-WRAM 0x00FF1040` as the rebuilt pointer table.
3. Uses `Genesis-WRAM 0x00FF1080` as the copied first-word table.
4. For each of 16 entries, checks the source pointer is inside JSON arcade segment `[0x00000F08, 0x0003A00C)`.
5. Converts source pointer to the JSON Genesis ROM address by subtracting `0x00000F08` and adding `0x00001108`.
6. Copies descriptor first word to `0x00FF1080..`.
7. Builds the translated second-word pointer as `0x00000200 + descriptor[2]`, preserving the existing translated Genesis semantics.
8. Preserves the original post-loop `0x00FF10A8` output write.
9. Fails loud with `trap #0` if a source pointer leaves the JSON-proven segment.

No extra WRAM channel, no seeded data, no diagnostic subsystem, no runtime scaffold, and no shared-helper rewrite were added.

## Build Verification

First release invocation stopped at the canonical coverage gate, before numbered artifact production:

```text
expected total_genesis_bytes_covered=0x17CF08 and opcode_replace patched_site count=129;
got total_genesis_bytes_covered=0x17CF68 opcode_replace patched_site count=129
```

The invariant was then updated to the observed mechanical helper-size delta:

- `CANONICAL_OPCODE_REPLACE_COUNT = 129` unchanged
- `CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x17CF68`

Second release invocation: **PASS**.

Build output:

- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0117.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `17cb39c7da59406e4fba569862cdb04f44dc96258d162470c54c7edf9f9cd621`
- Numbered and rolling ROMs: byte-identical (`cmp=0`)
- Canonical gate: `GATE_PASS`
- Standard release trace: `states/traces/rastan_direct_video_test_build_0117_mame_30s_20260629_173139/`

## Static Verification

`runtime_genesis_pc 0x00055B04` bytes:

```text
4E F9 00 07 15 82
```

Disassembly:

```asm
55b04: 4ef9 0007 1582  jmp 0x71582
```

Symbol:

```text
00071582 T genesistan_hook_pc080sn_descriptor_rebuild
```

Hook disassembly confirms the intended sequence:

```asm
71582: moveal #0x00ff1000,%a0
71588: moveal #0x00ff1040,%a1
7158e: moveal #0x00ff1080,%a2
71596: moveal %a0@,%a4
71598: cmpal #0x00000f08,%a4
715a0: cmpal #0x0003a00c,%a4
715a8: subal #0x00000f08,%a4
715ae: addal #0x00001108,%a4
715b4: movew %a4@,%a2@+
715b8: movew %a4@(2),%d1
715bc: moveal #0x00000200,%a4
715c2: lea %a4@(0,%d1:l),%a4
715c6: movel %a4,%a1@+
715d2: moveal %a5@(4294),%a4
715da: movew %d0,0xff10a8
715e0: rts
715e2: trap #0
```

The original body after `0x55B0A` remains present but is dead from the entry-site `jmp`; no external direct branch/caller into `0x55B0A..0x55B46` was found before implementation.

## Descriptor Byte Verification

For all 16 source pointers, `build/regions/maincpu.bin[arcade_pc]` matches `Build 0117 ROM[JSON-mapped genesis_rom_offset]`.

Representative rows:

| Index | Arcade source pointer | JSON-mapped Genesis ROM offset | Descriptor bytes | Expected rebuilt pointer |
|---:|---|---|---|---|
| 0 | `0x0001691C` | `0x00016B1C` | `000320FC` | `0x000022FC` |
| 1 | `0x00018BDC` | `0x00018DDC` | `000320FC` | `0x000022FC` |
| 6 | `0x0002399C` | `0x00023B9C` | `000320FC` | `0x000022FC` |
| 10 | `0x0002C49C` | `0x0002C69C` | `00032048` | `0x00002248` |
| 15 | `0x0003725C` | `0x0003745C` | `00032048` | `0x00002248` |

All 16 entries matched.

## Runtime Evidence

Targeted dump-only MAME debugger run:

- Directory: `states/traces/build_0117_pc080sn_descriptor_source_relocation_validation_20260629_173638_dump_only/`
- Command file: `build0117_descriptor_relocation_dump_only.cmd`
- Dump: `wram_ff1000_table_after_hook.bin`
- Result: exited via debugger after hitting hook completion (`runtime_genesis_pc 0x000715E0`)

Runtime WRAM dump after hook completion:

```text
FF1000:  0001 691C 0001 8BDC 0001 AE9C 0001 D15C
FF1010:  0001 F41C 0002 16DC 0002 399C 0002 5C5C
FF1020:  0002 7F1C 0002 A1DC 0002 C49C 0002 E75C
FF1030:  0003 0A1C 0003 2CDC 0003 4F9C 0003 725C
FF1040:  0000 22FC 0000 22FC 0000 22FC 0000 22FC
FF1050:  0000 22FC 0000 22FC 0000 22FC 0000 22FC
FF1060:  0000 22FC 0000 22FC 0000 2248 0000 2248
FF1070:  0000 2248 0000 2248 0000 2248 0000 2248
FF1080:  0003 0003 0003 0003 0003 0003 0003 0003
FF1090:  0003 0003 0003 0003 0003 0003 0003 0003
FF10A0:  00C0 0400 0000 0000 0080 0000 0000 0000
```

Interpretation:

- `0x00FF1000..0x00FF103F` remains raw arcade source pointers, as intended.
- `0x00FF1040..0x00FF107F` is rebuilt from JSON-relocated descriptor reads: `0x000022FC` for entries 0-9, `0x00002248` for entries 10-15.
- `0x00FF1080..0x00FF109F` copied descriptor first words are all `0x0003`.
- The previous Build 0116 mismatch (`0x2024/0x2025...` from raw Genesis ROM offsets) is gone.
- No crash occurred before hook completion in the targeted run.

A previous attempted debug run with full instruction tracing did not reach the hook before manual interruption and produced a large native trace at `states/traces/build_0117_pc080sn_descriptor_source_relocation_validation_20260629_173313/native_debug_trace.log`; it is not used as evidence.

## Scope Boundaries Preserved

Not touched:

- KF-038 / long PC080SN BG row aliasing
- `bg_fill` row model
- render-loop raw PC080SN writes
- sprites / HUD / window work
- crash-handler OPEN-015 defects
- bookmark infrastructure
- source table population or mutation behavior

## OPEN / KNOWN_FINDINGS Impact

- OPEN-023: progressed; descriptor source-pointer relocation implemented and runtime-validated.
- OPEN-001 / OPEN-022 / OPEN-024: context only.
- KF-036: predecessor remains valid; this task fixes the next runtime-built pointer relocation gap exposed by Build 0116.
- KF-038: not touched.
- KNOWN_FINDINGS: Option A, no update in this task.
- Issues opened/closed: none.

## STOP

STOP triggered: **NO**.
