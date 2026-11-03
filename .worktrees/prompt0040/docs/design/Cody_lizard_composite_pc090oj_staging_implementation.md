# Cody - Lizard-Man Composite PC090OJ Staging Implementation

**Date:** 2026-07-18
**Type:** Analysis-first bounded implementation + release build + mechanical/static verification
**Build context:** Build 0204/256 accepted baseline -> Build 0205/256 candidate
**Build 0205 ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0205.bin`
**Build 0205 SHA256:** `4238d2ffcd226c45f1251ccbe4e7e64fa9b642acb18c4957ab85e1fd888b4aee`
**Scope:** Implement block `A5+0x2C8` lizard-man composite PC090OJ staging through the existing mirror/candidate/SAT/tile-DMA pipeline. No second sprite renderer, no direct SAT writes, no forced actors/records/candidates/tiles, no mirror-cap change, no gameplay-state/collision/palette/tilemap work, no diagnostic ROM behavior.

## Phase 0

Classification: **EXTENDING**. Relevant priors loaded: KF-060 (enemy PC090OJ writers 0x41DAE/0x45DFA were misrouted/NOPped), KF-061 (invalid code-zero engine calls are unsafe), KF-062 (Genesis does populate enemy actor blocks), KF-063 (engine `0x3D254` safe on validated actors and shared `0x3C950` now preserves non-C-window tuple writes), KF-064 (visible first lizards are block `A5+0x2C8` composite records, not record 46), and KF-065 (block `A5+0x2C8` whole-block scratch design).

Rediscovery Hazard HIGH findings touched: KF-060/KF-061/KF-063/KF-064/KF-065; no contradiction detected.

Open issues touched: OPEN-017 and OPEN-024. OPEN-001 is context only. No closed issue was reopened. No new issue was created.

Architecture compliance: **CONFIRMED**. The arcade code remains the program. The existing opcode replacement at arcade `0x041DAE` continues to call a Genesis helper and return to arcade flow. The new code stages PC090OJ records through `pc090oj_object_ram` / `.Lpc090oj_family_apply_record` and the existing VBlank sprite commit path; it does not introduce a second renderer, direct SAT path, forced sprite data, or Genesis-owned lifecycle.

## Baseline

Baseline before implementation:

- Counter: `204`
- Accepted ROM: `dist/rastan-direct/rastan_direct_video_test_build_0204.bin`
- Build 0204 SHA256: `0e1925b2934e2d2614bb6c90de82c78ea07bc62819b58fe345fb83f8e5deb083`
- Makefile default mirror size: `PC090OJ_MIRROR_RECORDS ?= 256`
- Canonical opcode_replace count: `214`
- Canonical total Genesis bytes covered: `0x182890`
- Build 0205/0206 did not exist before this task.

## Pre-Implementation Gates

### Gate 1 - Engine Tuple-Write Semantics

**PASS.** Static disassembly of original arcade `0x3C950` and callers confirms the expansion engine advances `%a1` by exactly `d2 * 8` bytes. Valid tuple output writes the four PC090OJ record words through the shared writer path. Padding/blank paths can write only word1/Y `0x0180`, so seeded scratch is required to preserve words0/2/3.

### Gate 2 - Arcade Inactive Semantics

**PASS.** Original inactive path under arcade `0x41EDE` writes only word1/Y `0x0180`, advances by 8 bytes per record, and leaves the rest of each tuple unchanged. The implementation reproduces that behavior in scratch.

### Gate 3 - Special Path Boundary

**PASS.** Original `a4@(3) != 0` branches to arcade `0x3EFBE`. That path was intentionally not implemented here. The Build 0205 helper preserves the seeded scratch window for special actors and advances by the same `d2 * 8` span.

### Gate 4 - Invalid Code-Zero Boundary

**PASS as deferred-preserve.** Active actors with `a4@(3)==0` and code byte `a4@(1)==0` remain an invalid engine-call case. The implementation does not call the engine for code-zero and preserves the seeded window rather than guessing blank/full-page output.

### Gate 5 - Family Apply Contract

**PASS.** `.Lpc090oj_family_apply_record` preserves `d0-d7/a0-a6` and SR/condition codes via `movem.l` plus SR save/restore, performs record-bounds checks, fast-paths unchanged tuples, writes changed tuples into `pc090oj_object_ram`, sets `pc090oj_mirror_dirty`, and marks candidates through the normal bitset path.

### Gate 6 - Scratch / WRAM Bounds

**PASS.** `pc090oj_block2c8_scratch` is `100 * 8 = 800` bytes at `WRAM 0x00FFBBD8..0x00FFBEF8` exclusive. The applied span is 99 records (`140..238`, `792` bytes), and the 100th record is unused margin. The next symbol is `audit_guard_caller_pc` at `0x00FFBEF8`, so the scratch allocation is contiguous and non-overlapping.

## Implementation

Changed `apps/rastan-direct/src/pc090oj_hooks.s` only for sprite helper behavior:

- Added constants for the block span:
  - `PC090OJ_BLOCK2C8_BASE_RECORD = 140`
  - `PC090OJ_BLOCK2C8_APPLIED_RECORDS = 99`
  - `PC090OJ_BLOCK2C8_SCRATCH_RECORDS = 100`
  - `PC090OJ_BLOCK2C8_SCRATCH_BYTES = 0x320`
- Added assembly-time assertions that the scratch is large enough and the span ends at record `238`.
- Modified gameplay branch of `genesistan_pc090oj_hook_target_41dae` so scene 1 now calls:
  - `pc090oj_stage_block2c8`
  - existing `.Lpc090oj_stage_record46_validated`
- Non-gameplay behavior remains the existing `pc090oj_workram_block_sprites` path.
- Added `pc090oj_stage_block2c8`:
  - Saves `d0-d7/a0-a6`.
  - Seeds scratch records `0..98` from current mirror records `140..238`.
  - Clears only unused record-100 margin.
  - Iterates 9 actor entries from `A5+0x02C8`.
  - Uses `d2=10` for entries `0..7`, `d2=19` for entry `8`.
  - Valid actor path calls relocated engine `runtime_genesis_pc 0x0003D254`.
  - Inactive actor path sets only word1/Y to `0x0180` across the fixed window.
  - Special `a4@(3)!=0` and invalid code-zero paths preserve the seeded window and advance the destination pointer.
  - Flushes records `140..238` through `.Lpc090oj_family_apply_record` only.
- Added `pc090oj_block2c8_scratch` in `.bss`.

Important scope note: the current prompt's preserve-window rule for special/code-zero actors superseded the older design sketch's broader blank-fill wording. No speculative blanking was added for unresolved paths.

## Build

First release invocation stopped before artifact production at the expected canonical coverage gate:

```text
expected total_genesis_bytes_covered=0x182890 and opcode_replace patched_site count=214;
got total_genesis_bytes_covered=0x182950 opcode_replace patched_site count=214
```

The counter did not advance and no numbered artifact was produced by that failed gate. The observed `+0xC0` was mechanically verified against the assembled helper. The canonical coverage constant was then updated in both gate scripts:

- `tools/translation/postpatch_startup_rom.py`: `0x182890 -> 0x182950`
- `tools/translation/verify_canonical_rom.py`: `0x182890 -> 0x182950`

Second release invocation produced Build 0205:

- Build produced: **YES**
- Counter: `204 -> 205`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0205.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `4238d2ffcd226c45f1251ccbe4e7e64fa9b642acb18c4957ab85e1fd888b4aee`
- Size: `1,583,440` bytes
- Rolling vs numbered: byte-identical
- Build0204 vs Build0205: differs, as expected
- Boot guard: PASS
- Canonical gate: `GATE_PASS`
- `opcode_replace` count: `214` unchanged
- `total_genesis_bytes_covered`: `0x182950`
- Bookmarks active: none
- Release trace: `states/traces/rastan_direct_video_test_build_0205_mame_30s_20260718_211813/`

## Static Verification

Generated postpatch disassembly confirms the route:

```asm
41fae: 4eb9 0007 22fe  jsr 0x722fe        ; arcade 0x41DAE replacement target
7230e: 6100 00a0       bsrw 0x723b0       ; pc090oj_stage_block2c8
72312: 6100 001a       bsrw 0x7232e       ; existing record-46 helper
72316: 4e75            rts
```

Generated helper evidence:

```asm
723b0: 48e7 fffe       moveml %d0-%fp,%sp@-
723b4: 41f9 00ff ae38  lea 0xffae38,%a0   ; pc090oj_object_ram + 140*8
723ba: 43f9 00ff bbd8  lea 0xffbbd8,%a1   ; pc090oj_block2c8_scratch
723c0: 303c 00c5       movew #197,%d0     ; 198 longwords = 792 bytes
723ce: 43f9 00ff bbd8  lea 0xffbbd8,%a1
723d4: 49ed 02c8       lea %a5@(712),%a4
723e2: 7413            moveq #19,%d2      ; entry 8 d2 override
723ee: 4a2c 0003       tstb %a4@(3)       ; special-path gate
723f4: 4a2c 0001       tstb %a4@(1)       ; code-zero gate
72406: 4eb9 0003 d254  jsr 0x3d254        ; valid actor engine call
72412: 337c 0180 0002  movew #384,%a1@(2) ; inactive word1-only blank
72440: 303c 008c       movew #140,%d0
72444: 3a3c 0062       movew #98,%d5      ; 99-record flush
72456: 6100 fda8       bsrw 0x72200       ; .Lpc090oj_family_apply_record
72464: 4cdf 7fff       moveml %sp@+,%d0-%fp
72468: 4e75            rts
```

Symbol verification:

- `genesistan_pc090oj_hook_target_41dae = 0x000722FE`
- `pc090oj_stage_block2c8 = 0x000723B0`
- `pc090oj_object_ram = 0x00FFA9D8`
- `pc090oj_object_ram + 140*8 = 0x00FFAE38`
- `pc090oj_block2c8_scratch = 0x00FFBBD8`
- `audit_guard_caller_pc = 0x00FFBEF8`

Address-map/manifest verification:

- The existing opcode replacement for arcade `0x041DAE` remains present and targets `genesistan_pc090oj_hook_target_41dae`.
- `address_rewrites` count: `219`
- `opcode_replace` entries: `214`
- `postpatch_expected_opcode_replace_sites`: `214`
- `postpatch_expected_total_genesis_bytes_covered`: `0x182950`
- `build_context`: `canonical`

## Runtime / Visual Validation Boundary

The automatic release trace completed successfully over `1798` frames with no unmapped memory addresses reported. It stayed in the frontend/title/attract context and did **not** enter gameplay, so it does not prove lizard visual output.

Therefore:

- Build 0205 is mechanically and statically verified.
- The lizard block route is present in the produced ROM.
- No crash was observed in the standard release trace.
- Lizard runtime appearance, record `140..238` population during gameplay, SAT slot residency, true VRAM tile-DMA residency, and visual correctness still require gameplay-window validation.
- USER MUST VERIFY: run Build 0205 in BlastEm/Exodus/MAME gameplay and confirm whether lizard bodies become visible, whether Rastan remains controllable, whether the existing small record-46 sprite still behaves as before, and whether black-bar/VBlank pressure worsens.

## Evidence Artifacts

Dedicated evidence directory:

`states/traces/lizard_composite_pc090oj_staging_implementation_20260718_211925/`

Files:

- `build0205_pc090oj_lizard_helper.disasm.txt`
- `build0205_41dae_patch_site.disasm.txt`
- `build0205_engine_3d254.disasm.txt`
- `build0205_symbol.txt`
- `build0205_patch_manifest.json`
- `build0205_release_30s_genesis_exec_summary.txt`
- `build0205_release_30s_genesis_exec_trace.log`

## Acceptance Status

Implementation status: **COMPLETE as a candidate build**.

Runtime visual acceptance: **PENDING USER / gameplay-window validation**.

This task does not claim that lizard sprites are visually correct yet. It claims only that the previously missing `A5+0x2C8 -> records 140..238` staging route is implemented through the correct production pipeline and mechanically present in Build 0205.

## Open / Closed Issues Impact

- Open issues touched: OPEN-017, OPEN-024
- New issues opened: NONE
- Issues closed: NONE
- Issues intentionally deferred: lizard visual acceptance, true-VRAM/tile-DMA validation, per-scanline clustering, entry-0 `0x3EFBE` special output, code-zero invalid semantics, bat palette, record-132 stale sphere, black bar/VBlank, FG/sky/HUD/D00298/continue-game-over

## KNOWN_FINDINGS Impact

Option C - KF-065 refined from design-ready to implemented Build 0205 candidate. The refinement records that Build 0205 uses the whole-block scratch route, preserves special/code-zero windows rather than speculatively blanking them, and remains pending gameplay-window visual validation.

## STOP

STOP triggered: **NO**.
