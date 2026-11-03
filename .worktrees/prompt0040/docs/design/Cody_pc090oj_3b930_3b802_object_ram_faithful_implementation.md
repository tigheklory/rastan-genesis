# Cody - Object-RAM-Faithful PC090OJ 0x3B930 / 0x3B802 Producer Fix

**Date:** 2026-07-02  
**Type:** Implementation + build + runtime evidence  
**Final produced build:** Build 0128  
**Final ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0128.bin`  
**Final ROM SHA256:** `79ec8a30c44f24b0b551e4a1ae7116de075264927fb5ff550148f25808f5bc6f`  
**Scope:** Replace the helper-owned PC090OJ producer behavior for arcade `0x03B930` / `0x03B802` with object-RAM-faithful mirror writes. No sprite suppression, no fake title sprites, no direct producer-side SAT/descriptor emission, no Window/PC080SN/D00298/OPEN-015 work.

## Phase 0

Classification: **EXTENDING** for OPEN-024 / OPEN-001. Relevant priors loaded from `RULES.md`, `ARCHITECTURE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest `AGENTS_LOG.md`, and the task-design docs listed in the prompt.

Architecture constraints respected:

- Arcade code remains the program.
- Genesis code remains helper/hardware-service only.
- Producers now update the PC090OJ object-RAM mirror only.
- VBlank scan remains the only path that derives `staged_sprite_descriptor_table` and `staged_sprite_sat` from `pc090oj_object_ram`.
- No C/SGDK/MAME-port implementation was added.
- No bypass/NOP/RTS workaround was used as a fix.

## Address Mapping

All code correlations below were read through `build/rastan-direct/address_map.json`:

| arcade_pc | runtime_genesis_pc | map kind |
|---|---:|---|
| `0x03B802` | `0x03BA02` | `patched_site` |
| `0x03B8B0` | `0x03BAB0` | `arcade_copy` |
| `0x03B902` | `0x03BB02` | `patched_site` |
| `0x03B926` | `0x03BB26` | `patched_site` |
| `0x03B930` | `0x03BB30` | `patched_site` |
| `0x05B512` | `0x05B712` | `arcade_copy` |

## State Causality

Expected state at the producer sites:

- `arcade_pc 0x03B930` / `runtime_genesis_pc 0x03BB30` is a table-copy helper whose callers supply `A0` source, `A1 = HW_ADDRESS 0x00D0xxxx`, and `D1` object count. The state it should create is PC090OJ object RAM records at the caller-provided destination.
- `arcade_pc 0x03B802` / `runtime_genesis_pc 0x03BA02` is a score-digit helper. The state it should create is byte/word updates in PC090OJ object RAM, using the original five-record PC-relative mode table.

Why the state was not created before this patch:

- The prior `genesistan_pc090oj_hook_target_3b930` ignored caller `A1`, hardcoded helper-owned slot `14`, clamped `D1` to at most `4`, and emitted descriptor/SAT state directly through `.Lpc090oj_emit_slot`.
- The prior `genesistan_pc090oj_hook_score_digit_3b802` mapped output to helper-owned slots `22..29` and emitted descriptor/SAT state directly.
- Both behaviors bypassed the original object-RAM producer contract and made VBlank scan operate on incomplete/wrong mirror content.

## Implementation

Changed `apps/rastan-direct/src/pc090oj_hooks.s`:

- Added guarded mirror primitives:
  - `.Lpc090oj_mirror_write_word_a1_d0`
  - `.Lpc090oj_mirror_write_byte_a1_d0`
- Both primitives accept `A1 = HW_ADDRESS 0x00D00000..0x00D007FF`, write to `pc090oj_object_ram + (A1 - 0x00D00000)`, set `pc090oj_mirror_dirty`, and increment producer counters.
- Out-of-range writes increment `pc090oj_producer_oob_count` and do not touch the mirror.
- The primitives preserve `%a2` so the score source pointer survives across byte/word writes.
- Rewrote `genesistan_pc090oj_hook_target_3b930` to replay the arcade loop shape:
  - word0 `0`
  - word1 zero-extended source Y byte
  - word2 zero-extended source code byte
  - word3 transformed by mapped runtime call `0x05B712`
  - destination advances through caller-provided `A1`
- Rewrote `genesistan_pc090oj_hook_score_digit_3b802` to write the original byte/word fields into the caller-selected PC090OJ object records instead of helper-owned SAT/descriptor slots.
- Added a local copy of the original 5-record score mode table from arcade `maincpu 0x03B87E..0x03B8AF`. This was required because the runtime table location `0x03BA7E` lies inside the opcode-replaced `0x03B802` span and is filled with `0x4E71` NOPs after patching.
- Added producer counters:
  - `pc090oj_producer_oob_count`
  - `pc090oj_producer_write_count`

Changed `apps/rastan-direct/src/boot/boot.s`:

- Clears the two new producer counters during boot/staging initialization alongside the existing PC090OJ counters.

Changed canonical invariants mechanically:

- `opcode_replace` patched-site count remains `133`.
- `total_genesis_bytes_covered` changed `0x17D400 -> 0x17D47C`.
- Files updated:
  - `tools/translation/postpatch_startup_rom.py`
  - `tools/translation/verify_canonical_rom.py`

## Build Notes

The first release produced Build 0127 (`d2254318bf3eb58178149136cbd715d37c1a62be4590909f0a3fbd6c7105335c`) and exposed the overwritten score-table issue during runtime comparison. Build 0127 is therefore superseded by the corrected Build 0128 in this report.

Final release result:

- Build: `0128`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0128.bin`
- SHA256: `79ec8a30c44f24b0b551e4a1ae7116de075264927fb5ff550148f25808f5bc6f`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- Rolling/numbered `cmp`: `0` (byte-identical)
- Canonical gate: `GATE_PASS`
- Release trace: `states/traces/rastan_direct_video_test_build_0128_mame_30s_20260702_145950/`

Static disassembly confirms:

- `runtime_genesis_pc 0x03BA02: jsr 0x071C72` (`genesistan_pc090oj_hook_score_digit_3b802`)
- `runtime_genesis_pc 0x03BB30: jsr 0x071A92` (`genesistan_pc090oj_hook_target_3b930`)
- `runtime_genesis_pc 0x071ABA: jsr 0x05B712` for the original word3 transform in the `0x3B930` replacement.

## Runtime Evidence

Evidence directory:

`states/traces/pc090oj_3b930_3b802_object_ram_faithful_build0128_20260702_150018/`

Capture script:

`states/traces/pc090oj_3b930_3b802_object_ram_faithful_build0128_20260702_150018/capture_build0128_pc090oj_object_ram.lua`

Captured checkpoints:

- frame 60: title steady
- frame 90: title late
- frame 120: title later
- frame 282: story black-cover nominal
- frame 283: story reveal nominal
- frame 289: story reveal late
- frame 369: late story/transition

Dumped at each checkpoint:

- `pc090oj_object_ram` (`WRAM 0xFF674A..0xFF6F49`)
- staged sprite descriptor table (`WRAM 0xFF6384..`)
- staged sprite SAT (`WRAM 0xFF6104..`)
- true VDP SAT read attempt (`VRAM 0xF800..`)
- PC090OJ counters (`WRAM 0xFF6F4A..`)
- Plane A/B VRAM snapshots
- video snapshot PNGs

Frame-60 title summary:

- `raw_nonzero=240`
- `raw_nonzero_code=42`
- `producer_oob_count=0`
- `producer_write_count=0x00BA`
- `decoded=0x0100`
- `blank=0x0006`
- `unmapped=0x0000`
- `offscreen=0x000D`
- `drawable=0x0017`
- `emitted=0x0017`
- `dropped=0x0000`

This proves the producer replacements now populate object RAM and the VBlank scanner decodes/emits from the mirror. The old helper-owned Build 0126 pattern (`0x0001`, `0x0110`, `0x0080`, `0x0080` as the only visible candidates) is no longer the dominant object-RAM state.

## Arcade Target Entry Comparison

Compared original arcade frame-60 `PC090OJ 0x00D00000..0x00D007FF` against Build 0128 frame-60 `pc090oj_object_ram` for the audited title-score target entries.

Entries checked: `4,5,6,7,8,22,23,24,25,28..45` (27 entries total).

Result: `22/27` exact entry matches; `5/27` mismatches remain.

Exact matches include entries `5,6,7,8,28..45`, covering most of the title-score strip and confirming the `0x3B930` caller-provided destination/count behavior is now active.

Remaining mismatches:

| entry | arcade words | Build 0128 words |
|---:|---|---|
| `4` | `0000 0000 003B 0088` | `0000 0000 0001 0000` |
| `22` | `0000 0010 002B 00A8` | `0000 0110 002A 00A8` |
| `23` | `0000 0010 002D 00A0` | `0000 0110 002A 00A0` |
| `24` | `0000 0010 0031 0098` | `0000 0110 002A 0098` |
| `25` | `0000 0010 002C 0090` | `0000 0110 002A 0090` |

Interpretation:

- The implementation fixed the helper-owned producer/SAT bypass and restored object-RAM population for the majority of audited title-score entries.
- The remaining five mismatches are not raw `0x3B930` helper-owned artifacts. They are score/source-state mismatches exposed after the object-RAM-faithful route became live.
- Specifically, entries `22..25` now have the correct destination/X progression but still hold leading-zero/digit-zero state (`word1=0x0110`, code `0x002A`) where the arcade frame has score digits (`0x002B/0x002D/0x0031/0x002C`, `word1=0x0010`). This points at upstream score/high-score source state, not producer destination routing.

## Residual Issues / Non-Closures

OPEN-024 remains open:

- This patch fixes a confirmed producer-to-object-RAM semantic gap for `0x3B930` / `0x3B802`.
- It does not prove the whole PC090OJ subsystem is correct.
- Title score output still has five mismatched object entries.
- Story/black-cover symptoms are not fully resolved by this evidence.

OPEN-001 remains open:

- Graphics are still under active bring-up.
- This task does not claim final title/story visual correctness.

OPEN-015 was not touched.

KNOWN_FINDINGS impact: Option A for this implementation pass. The durable fact is best recorded after a follow-up pass decides whether the remaining five mismatches are upstream score-state creation, source-base mapping, or timing/lifecycle.

## STOP

STOP triggered: **NO**.

The final implementation/build/evidence work completed. A residual runtime mismatch remains and is documented instead of hidden.
