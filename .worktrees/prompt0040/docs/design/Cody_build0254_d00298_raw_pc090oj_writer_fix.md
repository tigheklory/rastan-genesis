# Cody Build 0254 D00298 Raw PC090OJ Writer Fix

## Result

- STOP triggered: NO.
- Build produced: YES, exactly Build 0254.
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0254.bin`
- Size: `1592224` bytes.
- SHA-256: `53bf25f4f2a090864aaab3fad98ce1646b15226d218f5e907468e52212c0b7e4`.
- Counter: `253 -> 254`.
- `GATE_PASS`: YES.
- Build 0253 was preserved at `dist/rastan-direct/rastan_direct_video_test_build_0253.bin`.

## Baseline

- Accepted baseline: Build 0253.
- Accepted SHA-256: `3015974ec444e3be2d49f182a191dfb5a536dfb89b07d3e9ec84c9767f1e6155`.
- Baseline rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`, byte-identical to Build 0253 before this task.
- Baseline size: `1592224` bytes.
- User visual baseline: Rastan, lizard men, bats, axe item, and frontend/title/story/high-score screens render; Build 0253 runs faster; remaining issues are preexisting.
- Latest Build 0253 build record: `GATE_PASS` with no unique unmapped MAME addresses.
- The earlier Build 0254 attract audit was audit-only: no ROM, source, or counter change.

## Prior Audit Summary

`docs/design/Cody_build0254_attract_mode_legacy_reachability_audit.md` established:

- BlastEm's reported fatal write at `HW_ADDRESS 0x00D00298` is accepted external runtime evidence.
- MAME did not reproduce the raw write during the bounded attract run; that narrow non-reproduction does not invalidate the strict-target crash.
- `runtime_genesis_pc 0x0005A71E` / `arcade_pc 0x0005A51E` loaded the raw destination.
- `runtime_genesis_pc 0x0005124E` / `arcade_pc 0x0005104E` was the direct static call site.
- Frontend PC090OJ compatibility still uses `pc090oj_object_ram`; gameplay scene 1 uses native semantic queues/finalizer.

## Ghidra Arcade-Reference Evidence

The existing project `tools/ghidra/rastan_project/rastan_arcade_ref.gpr` was reused read-only. No project was created, duplicated, or reinstalled. The checked-in exports initially marked `arcade_pc 0x05A502..0x05B511` unresolved; a read-only headless session disassembled the already-present bytes, created temporary in-memory functions, decompiled them, and discarded the changes.

### Functions

- `arcade_pc 0x0005A502`, `0x0005A51E`, and `0x0005A524` are in the resolved `FUN_0005a502`, body `0x05A502..0x05A5AA`.
- `arcade_pc 0x0005104E` is in the resolved `FUN_0005100a`, body `0x05100A..0x0510C4`.
- `FUN_0005100a` is directly called by resolved `FUN_00041f0e` at `arcade_pc 0x041F0E`.
- Linear arcade disassembly shows callers of `arcade_pc 0x041F0E` at `0x03A7B4` and `0x03A836`.

### Decompiled Semantics

`FUN_0005a502` reads bit 5 of `arcade_WRAM 0x0010C200`. It selects Y=`0x0070` when clear or the PC090OJ hidden marker Y=`0x0180` when set. It then writes eight complete contiguous PC090OJ records:

| Record | Offset | Word 0 | Y | Code | X |
|---:|---:|---:|---:|---:|---:|
| 83 | `0x298` | `0` | selected | `0x37` | `0x60` |
| 84 | `0x2A0` | `0` | selected | `0x38` | `0x70` |
| 85 | `0x2A8` | `0` | selected | `0x3F` | `0x80` |
| 86 | `0x2B0` | `0` | selected | `0x40` | `0x90` |
| 87 | `0x2B8` | `0` | selected | `0x41` | `0xB0` |
| 88 | `0x2C0` | `0` | selected | `0x42` | `0xC0` |
| 89 | `0x2C8` | `0` | selected | `0x43` | `0xD0` |
| 90 | `0x2D0` | `0` | selected | `0x44` | `0xE0` |

This is legitimate complete-record construction, not a clear/fill, table/strip, partial position update, or SAT write. `FUN_0005100a` calls it only when `a5+0x34 == 0`, within a larger arcade gameplay-update sequence. Classification: shared gameplay update (therefore usable by normal gameplay and an attract gameplay run), not frontend-only or attract-only. No demo-specific branch was found in the writer itself.

### Xrefs And Siblings

- Ghidra direct callers of `FUN_0005a502`: one, `FUN_0005100a` at `arcade_pc 0x05104E`.
- No additional direct, indirect, or data xref to `FUN_0005a502` was found.
- The same function has a second raw literal at `arcade_pc 0x05A554`, `movea.l #0x00D002B0,a0`. It reloads the address already reached after records 83..85 and begins record 86. It is the same exact contiguous writer family and must move with the first literal.
- No third raw `0x00D0xxxx` literal exists in `FUN_0005a502`.

## State Causality

1. State required at this PC: complete PC090OJ-format records 83..90 with the selected visible/hidden Y and fixed code/X sequence.
2. Earlier responsible code: retained arcade `FUN_0005a502`, called from `FUN_0005100a` inside `FUN_00041f0e`'s update sequence.
3. Why state was not created safely: both A0 immediates still selected physical arcade PC090OJ addresses. On Genesis they do not name writable compatibility RAM; BlastEm stops on the first store to `HW_ADDRESS 0x00D00298`.

The fix restores the intended destination while preserving the producer and its position in the initialization/update timeline. No value is seeded early, skipped, or duplicated.

## Address-Map Proof

All correlations below are from generated `build/rastan-direct/address_map.json`, not arithmetic:

- `runtime_genesis_pc 0x0005A71E` <-> `arcade_pc 0x0005A51E` (`patched_site`).
- `runtime_genesis_pc 0x0005A724` <-> `arcade_pc 0x0005A524` (`arcade_copy`).
- `runtime_genesis_pc 0x0005124E` <-> `arcade_pc 0x0005104E` (`arcade_copy`).
- Paired sibling: `runtime_genesis_pc 0x0005A754` <-> `arcade_pc 0x0005A554` (`patched_site`).

## Destination Proof

- Build 0254 symbol: `pc090oj_object_ram = Genesis-WRAM 0x00FFAF9A`.
- Allocation: 256 records * 8 bytes = `0x800` bytes, range `0x00FFAF9A..0x00FFB799` inclusive.
- Record 83 destination: `pc090oj_object_ram + 0x298 = 0x00FFB232`.
- Record 86 reload: `pc090oj_object_ram + 0x2B0 = 0x00FFB24A`.
- Final written record is 90 at offset `0x2D0..0x2D7`; all writes are in bounds.
- This range is Genesis WRAM and does not overlap either double-buffered final-format SAT, the native semantic queues, residency tags, or tile-DMA worklist.

## Patch

The source-of-truth change is two byte-neutral `opcode_replace` entries in `specs/rastan_direct_remap.json`:

| Arcade PC | Original instruction / bytes | Patched instruction / bytes |
|---:|---|---|
| `0x05A51E` | `movea.l #0x00D00298,a0` / `207C00D00298` | `movea.l #pc090oj_object_ram+0x298,a0` / `207C00FFB232` |
| `0x05A554` | `movea.l #0x00D002B0,a0` / `207C00D002B0` | `movea.l #pc090oj_object_ram+0x2B0,a0` / `207C00FFB24A` |

The replacement expressions use symbol+offset resolution rather than a hardcoded BSS address. Opcode, instruction width, every `(a0)+` store, all record contents, branches, register use, call/return flow, and sequence ordering remain unchanged.

## Safety And Architecture Compliance

- Arcade code remains the program; no Genesis loop, scheduler, lifecycle, or hidden state machine was added.
- No NOP, RTS bypass, equal-length control-flow hack, fallback, suppression, or state seed was added.
- No assembly producer, native gameplay lane, PLAYER_BODY lifecycle, SAT finalizer, Plane A/B path, collision, rope/reset, input, audio, palette, or CRAM code changed.
- The old gameplay scanner/decoder is not re-enabled: no call site or branch changed, and `pc090oj_native_emit_pass` remains the scene-1 owner.
- `pc090oj_object_ram` already exists as transitional persistent slot-addressed compatibility state; this build adds no mirror/table, consumer, scan, or renderer.

Native-policy classification: this narrowly authorized compatibility fix retains the arcade complete-record semantic operation and removes its raw physical PC090OJ address selection. It does not claim the retained record construction is the final native boundary. The removal boundary remains conversion of the remaining frontend/unconverted producers to direct native SAT production, after which the compatibility object table and these two destination redirects can be retired together.

### Policy Checklist

- Semantic decision retained: construct records 83..90 with visibility, code, and fixed positions.
- Chip tail removed here: raw physical destinations `0xD00298` and `0xD002B0` only.
- Native semantic input used: no new helper was added; the retained arcade writer's inputs are unchanged.
- New mirror/shadow/range dispatcher/projector: none.
- Compatibility isolation: existing `pc090oj_object_ram`; native gameplay lanes/finalizer remain untouched.
- Arcade gameplay/frame/VBlank ownership preserved: yes.
- Direct final SAT generation for converted gameplay paths preserved: yes.
- Retirement path: remaining frontend/unconverted producer conversion, then compatibility-table removal.

## Validation

- Build command: `source tools/setup_env.sh && make -C apps/rastan-direct release PC090OJ_MIRROR_RECORDS=256 RASTAN_GAMEPLAY_HUD_SPRITES=2`.
- `GATE_PASS`: YES.
- Counter: `254`; exactly one ROM produced.
- Opcode-replace count: `218 -> 220`.
- Canonical coverage: unchanged `0x184BA0`; gaps `[]`; overlaps `[]`.
- Generated disassembly:
  - `runtime_genesis_pc 0x5A71E: movea.l #0x00FFB232,a0`.
  - `runtime_genesis_pc 0x5A754: movea.l #0x00FFB24A,a0`.
  - first store remains `runtime_genesis_pc 0x5A724: move.w #0,(a0)+`.
- No `0x00D00298` or `0x00D002B0` literal remains in `build/genesis_postpatch.disasm.txt`.
- Numbered and rolling ROMs are byte-identical by SHA-256 and size.
- Standard MAME smoke trace: `states/traces/rastan_direct_video_test_build_0254_mame_30s_20260803_222245/`; `frames=1798`, final PC `0x073CB0`, SP `0x00FEFF78`, `vdp_ports_live=47197`, `fg_cwindow_live=0`, unique unmapped memory addresses: none.

Static validation proves the raw writer family is remapped. MAME did not and need not reproduce the BlastEm failure.

## User Verification Required

USER MUST VERIFY in BlastEm:

- attract gameplay demo no longer fatals at D00298/D002B0;
- title/story/high-score still render;
- normal gameplay still renders Rastan, lizard men, bats, and axe item;
- remaining visual issues are unchanged/preexisting.

This report does not claim the BlastEm result before that verification.

## Open / Closed Issues Impact

- Open issues touched: `OPEN-024`.
- Context only: `OPEN-001`, `OPEN-017`, `OPEN-015`.
- New issues opened: NONE.
- Issues closed: NONE.
- Intentionally deferred: full frontend PC090OJ/PC080SN native conversion and compatibility-table retirement.
- KNOWN_FINDINGS impact: Option A - no new finding to index; this applies KF-032/KF-069 without establishing a new durable mechanism.

## STOP Status

STOP triggered: NO. Required files, Ghidra provenance, destination bounds, build counter, canonical gate, and design document are all valid.
