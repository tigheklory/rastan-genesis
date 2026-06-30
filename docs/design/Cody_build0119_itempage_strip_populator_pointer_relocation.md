# Cody - Build 0119 Item-Page Strip Populator Pointer Relocation Hook

**Date:** 2026-06-29  
**Type:** Implementation + build + validation  
**Build:** 0119  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0119.bin`  
**SHA256:** `e1d74a2514a2142a1ad56b54bedc49c6d39570ee5d5ca9da1bb7c9f9ce8d46c4`  
**Scope:** Implement Andy's proven Build 0118 `0x20480013` item-page pointer-field correctness design. Production helper only. No KF-038 item-scroll/staging-size work. No `bg_fill` changes. No PC080SN render-loop HW-write routing. No sprites/HUD/Window/gameplay work. No systemic ROM-wide KF-036 pass. No fake data, skip, bypass, broad runtime mirror, or bookmark cycle.

## Phase 0

Classification: **EXTENDING** KF-028 / OPEN-016 runtime-pointer-relocation class. Build 0118's KF-036 slot-address rebase is treated as the fixed predecessor layer.

Required priors read:

- `RULES.md`
- `ARCHITECTURE.md`
- `docs/design/Cody_build0118_0010D100_itempage_wram_literal_rebase.md`
- `docs/design/Andy_build0118_20480013_itempage_pointer_field_correctness_design.md`
- `docs/design/Cody_build0117_pc080sn_descriptor_source_pointer_relocation.md`
- `docs/design/Andy_pc080sn_descriptor_source_pointer_relocation_design.md`
- latest relevant `AGENTS_LOG.md`

No contradiction detected. STOP not triggered in Phase 0.

## Preconditions

### Address-map authority

All ROM-to-ROM conversions use `build/rastan-direct/address_map.json` as authority. The verified segment is:

```text
kind                  arcade_copy
arcade_start          0x00000F08
arcade_end_exclusive  0x0003A00C
genesis_start         0x00001108
genesis_end_exclusive 0x0003A20C
```

JSON-derived conversions:

| arcade/source pointer | JSON-derived genesis_rom_offset | evidence |
|---|---|---|
| `0x0003951C` | `0x0003971C` | descriptor bytes at mapped ROM match original arcade |
| `0x0000D11C` | `0x0000D31C` | strip bytes at mapped ROM match original arcade |

The `0x200` delta is only the consequence of this JSON segment. It was not used as standalone proof.

### Byte evidence

```text
ROM raw descriptor 0x0003951C:     0013 2048 0013 2048 ...  (wrong, odd long 0x20480013)
ROM mapped descriptor 0x0003971C:  0002 0000 D11C 0002 ...  (matches arcade)
maincpu descriptor 0x0003951C:     0002 0000 D11C 0002 ...

ROM raw strip 0x0000D11C:          00AD 00AD 0CC9 0CCA ...  (wrong)
ROM mapped strip 0x0000D31C:       04A6 04A7 04A8 04A9 ...  (matches arcade)
maincpu strip 0x0000D11C:          04A6 04A7 04A8 04A9 ...
```

### Patch-shape checks

- `runtime_genesis_pc 0x00055E2E` was exactly the 6-byte instruction `207C00FF10FC` before this task.
- `arcade_pc 0x00055C2E` already existed as an `opcode_replace` site from the prior literal rebase.
- The implementation superseded that existing site instead of adding an overlapping duplicate.
- Direct-target scan found `0` external branch/caller targets into dead body `runtime_genesis_pc 0x00055E34..0x00055E48`.

## Implementation

Added helper in `apps/rastan-direct/src/tilemap_hooks.s`:

```asm
genesistan_hook_itempage_strip_populate
```

Hook behavior:

1. Reads raw walker/source descriptor pointer from `Genesis-WRAM 0x00FF10FC`.
2. Guards the pointer inside JSON segment `[0x00000F08, 0x0003A00C)`.
3. Maps the descriptor pointer to the JSON-derived Genesis ROM segment by subtracting `0x00000F08` and adding `0x00001108`.
4. Reads descriptor `word@0` and descriptor raw strip pointer `long@2` from the mapped descriptor.
5. Guards the raw strip pointer inside the same JSON segment.
6. Maps the strip pointer to the JSON-derived Genesis ROM segment.
7. Writes descriptor word to `Genesis-WRAM 0x00FF1104`.
8. Writes relocated strip pointer to `Genesis-WRAM 0x00FF1100`.
9. Returns with `rts`.

The walker slot at `Genesis-WRAM 0x00FF10FC` remains raw arcade-native and continues to advance by `+6`; relocation occurs at dereference only.

Register discipline: the hook clobbers `a0/a1/a2/a4`, matching the original populator's address-register clobber set. It does not call staging/render helpers and does not introduce new lifecycle behavior.

## Spec Change

Replaced the existing `arcade_pc 0x055C2E` `opcode_replace` entry with a 6-byte `JMP`:

```text
runtime_genesis_pc 0x00055E2E: 4EF9 0007 15E4
```

The dead original populator body remains in ROM but is no longer entered from the function entry.

Existing Build 0118 consumer rebases remain present:

```asm
55e62: 227c 00ff 1104  moveal #0x00FF1104,%a1
55e68: 267c 00ff 1100  moveal #0x00FF1100,%a3
```

## Build Verification

First release invocation stopped at the canonical coverage gate, as expected for the new helper body:

```text
expected total_genesis_bytes_covered=0x17CF68 and opcode_replace patched_site count=133;
got total_genesis_bytes_covered=0x17CFC0 opcode_replace patched_site count=133
```

Canonical invariants were then updated to the observed mechanical result:

- `CANONICAL_OPCODE_REPLACE_COUNT = 133` unchanged
- `CANONICAL_TOTAL_GENESIS_BYTES_COVERED = 0x17CFC0`

Second release invocation: **PASS**.

Build output:

- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0119.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `e1d74a2514a2142a1ad56b54bedc49c6d39570ee5d5ca9da1bb7c9f9ce8d46c4`
- Numbered vs rolling ROM: byte-identical (`cmp=0`)
- Canonical gate: `GATE_PASS`
- Standard release trace: `states/traces/rastan_direct_video_test_build_0119_mame_30s_20260629_214047/`

Invariant result:

- `opcode_replace` delta: `0` because `0x055C2E` already existed and was superseded.
- `total_genesis_bytes_covered` delta: `0x17CF68 -> 0x17CFC0` (`+0x58`).

## Static Verification

Symbols:

```text
00071582 T genesistan_hook_pc080sn_descriptor_rebuild
000715e4 T genesistan_hook_itempage_strip_populate
```

Entry patch:

```asm
55e2e: 4ef9 0007 15e4  jmp 0x715e4
```

Hook disassembly:

```asm
715e4: moveal #0x00ff10fc,%a0
715ea: moveal %a0@,%a4
715ec: cmpal #0x00000f08,%a4
715f4: cmpal #0x0003a00c,%a4
715fc: subal #0x00000f08,%a4
71602: addal #0x00001108,%a4
71608: moveal %a4@(2),%a2
7160c: cmpal #0x00000f08,%a2
71614: cmpal #0x0003a00c,%a2
7161c: subal #0x00000f08,%a2
71622: addal #0x00001108,%a2
71628: moveal #0x00ff1104,%a1
7162e: movew %a4@,%a1@
71630: moveal #0x00ff1100,%a1
71636: movel %a2,%a1@
71638: rts
7163a: trap #0
```

Manifest:

- `patch_counts.opcode_replace_and_rom_opcode_replace = 133`
- `postpatch_expected_opcode_replace_sites = 133`
- `postpatch_expected_total_genesis_bytes_covered = 0x17CFC0`
- `arcade_pc 0x055C2E` maps to `runtime_genesis_pc 0x055E2E` replacement `4ef9000715e4`.

Dead-body reachability scan after build:

```text
external direct-target hits into runtime 0x55E34..0x55E48: 0
```

## Runtime Validation

Evidence directories:

- `states/traces/build_0119_itempage_strip_populator_validation_20260629_214152/`
- `states/traces/build_0119_itempage_strip_populator_firstcase_20260629_214323/`
- `states/traces/build_0119_descriptor_hook_firsthit_20260629_214346/`

### Build 0117 Descriptor Hook Still Valid

First-hit dump at `runtime_genesis_pc 0x000715E0`:

```text
FF1040: 0000 22FC ... 0000 2248 ...
FF1080: 0003 0003 ...
```

Artifact:

```text
states/traces/build_0119_descriptor_hook_firsthit_20260629_214346/wram_ff1000_after_descriptor_hook_firsthit.bin
```

### Exact Former Crash Case

Conditional capture at hook completion for `Genesis-WRAM 0x00FF10FC == 0x0003951C`:

```text
FF10F0: 0000 0000 0000 0000 0000 0000 0003 951C
FF1100: 0000 D31C 0002 0000 0000 0000 0000 0000
```

Therefore:

- `Genesis-WRAM 0x00FF10FC = 0x0003951C` raw walker pointer preserved.
- `Genesis-WRAM 0x00FF1104 = 0x0002` after hook.
- `Genesis-WRAM 0x00FF1100 = 0x0000D31C` after hook.

Mapped descriptor dump:

```text
03971C: 0002 0000 D11C 0002 0000 D91C 0002 0000 ...
```

Mapped strip dump:

```text
00D31C: 04A6 04A7 04A8 04A9 04AA 04AB 04AC 04AD ...
```

### Consumer / Old Fault Boundary

Conditional capture at `runtime_genesis_pc 0x00055E90`, after the old faulting read, with `Genesis-WRAM 0x00FF1100 == 0x0000D31C`:

```text
FF10F0: 0000 0000 0000 0000 00C0 0000 0003 951C
FF1100: 0000 D31C 0002 0000 0000 0000 0000 0000
```

Facts:

- The old faulting instruction at `runtime_genesis_pc 0x00055E8E` executed and reached `0x00055E90`.
- `0x55E8E` ADDRESS ERROR from Build 0118 is gone.
- For the first captured strip read, `Genesis-WRAM 0x00FF10F6 = 0`, so the static consumer sequence derives `d7=0` and `a6=a2=0x0000D31C`.
- `genesis_rom_offset 0x0000D31C` begins `0x04A6`, the valid mapped strip data.

The long validation run completed 120 emulated seconds with status `0` and did not produce a crash-record dump. The standard release trace also completed without unmapped memory addresses.

## Outcome

Build 0119 fixes the Build 0118 pointer-field blocker:

- Raw descriptor pointer `0x0003951C` is dereferenced at JSON-mapped `genesis_rom_offset 0x0003971C`.
- Descriptor word `0x0002` is written to `Genesis-WRAM 0x00FF1104`.
- Raw strip pointer `0x0000D11C` is relocated to `genesis_rom_offset 0x0000D31C` before being written to `Genesis-WRAM 0x00FF1100`.
- The consumer reads through the relocated pointer and passes the previous `0x55E8E` fault boundary.

No new later crash was observed in the 120-second validation run.

No title/story/high-score runtime regression was observed in the release smoke trace or targeted validation runs. This is a runtime smoke statement, not a claim of full visual correctness.

## Non-Actions

- No KF-038 item-scroll/staging-size work.
- No `bg_fill` changes.
- No PC080SN render-loop HW-write routing.
- No sprites/HUD/Window/gameplay work.
- No systemic ROM-wide KF-036 postpatcher pass.
- No fake data, skip, bypass, broad runtime mirror, alignment masking, or byte splitting.
- No bookmark cycle.
- No `KNOWN_FINDINGS.md` edit.
- No issue opened or closed.

## OPEN / KNOWN_FINDINGS Impact

- Label: **KF-028 / OPEN-016 runtime-pointer-relocation class**.
- Build 0118 KF-036 slot-address rebase remains the fixed predecessor layer.
- OPEN-023 is not implicated; it remains Window/HUD context.
- OPEN-001 context only.
- OPEN-015 discipline applied: debugger/dumps used, not formatted crash-screen values.
- KNOWN_FINDINGS impact: Option A; no canonical edit in this task.

## STOP

STOP triggered: **NO**.
