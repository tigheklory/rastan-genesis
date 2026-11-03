# Cody Build 60 Regression Forensics

Date: 2026-05-08  
Type: Evidence-only forensics (frozen-scene inspection)

## Scope
- No source/spec/tool/build/ROM changes performed in this task.
- No regeneration, no rebuild, no `make`, no cleaning, no timestamp-touch operations.
- Target question: why Build 60 visually regressed vs CLOSED-007 Build 59 despite source constant still set to base 0.

## §1 Source/Timestamp/Git State

### §1.1 Generator source constant
- File: `tools/translation/precompute_pc080sn_tile_lut.py`
- Evidence: `TILE_CACHE_BASE_A = 0` at line 39.
- Result: CLOSED-007 source change is still present (not reverted in source).

### §1.2 Critical timestamps (read-only `stat`)
- `tools/translation/precompute_pc080sn_tile_lut.py`: `2026-05-07 09:14:01`
- `tools/translation/postpatch_startup_rom.py`: `2026-05-08 11:07:34`
- `build/pc080sn_tile_vram_lut.bin`: `2026-05-07 09:14:14`
- `build/pc080sn_scene_preload_title.bin`: `2026-05-07 09:14:14`
- `build/pc080sn_scene_preload_gameplay.bin`: `2026-05-07 09:14:14`
- `build/pc080sn_scene_preload_endround.bin`: `2026-05-07 09:14:14`
- `build/pc080sn_attr_lut.bin`: `2026-04-05 11:29:30`
- `dist/rastan-direct/rastan_direct_video_test_build_0059.bin`: `2026-05-07 09:16:17`
- `dist/rastan-direct/rastan_direct_video_test_build_0060.bin`: `2026-05-08 11:07:40`

Timestamp ordering observation:
- Generator and generated LUT/preload artifacts were updated on 2026-05-07 before Build 59.
- Build 60 is later (2026-05-08), but this alone does not prove which artifact bytes were embedded.

### §1.3 Git inspection (read-only)
- `git status --short`: repository is dirty (pre-existing and recent changes visible, including helper-introduction files and postpatch invariant change).
- `git diff` for relevant files confirms:
  - `apps/rastan-direct/Makefile`: helper object/rule added
  - `tools/translation/postpatch_startup_rom.py`: expected invariant value `0x17CAE8 -> 0x17CAEC`
- `git log --oneline -20`: latest commit shown is `4ae07f8 Build 59`.

## §2 Generated Artifact Forensics

### §2.1 Current generated artifact SHAs
- `build/pc080sn_tile_vram_lut.bin`: `ca9c3dcf1aa3624c3660aa3b7443625433341941955c2c3f7c5956f44f5d3e92`
- `build/pc080sn_scene_preload_title.bin`: `e0a814f2638c638e2ec710a91bc88e2603af6ea95afbcd3fb34203c5002fe52f`
- `build/pc080sn_scene_preload_gameplay.bin`: `462c428c771428682e1be618dd2b72c54136c49a665fe4b09e1f935d6a7cdb6c`
- `build/pc080sn_scene_preload_endround.bin`: `690835b85f60451935a325db066a10139f946125b354c3f100412149ef730acc`
- `build/pc080sn_attr_lut.bin`: `2614c7b4c5ba7716fa6cc985f65ad2832c029956243d5570da52975d230fba3b`

Cross-reference with CLOSED-007 doc (`docs/design/Cody_slot_reservation_removal_implementation.md`):
- Attr LUT SHA matches recorded value exactly (`2614c7...`).
- That doc did not record all LUT/preload SHAs inline, but did record post-fix mapping expectations.

### §2.2 LUT first-byte pattern (current build artifact)
`xxd -l 64 build/pc080sn_tile_vram_lut.bin` starts with:
- `... 00 3e 00 3f 00 40 00 41 ...`

Decoded samples from current `build/pc080sn_tile_vram_lut.bin`:
- tile `0x01 -> 0x3E`
- tile `0x20 -> 0x00`
- tile `0x23 -> 0x01`
- tile `0x40 -> 0x16`

This is CLOSED-007 post-fix pattern (slot-base removed), not pre-fix.

## §3 Build 59 vs Build 60 ROM Forensics

### §3.1 Expected differences before diff
Expected-only changes from helper introduction:
- helper bytes around `0x00071C78` (`60 FE`) plus nearby alignment effects
- checksum/header drift expected from ROM content change
- no intended change to scene preload/LUT content

### §3.2 Raw binary diff summary
- ROM sizes:
  - Build 59: `1559272`
  - Build 60: `1559276` (+4)
- Unshifted diff contains many offsets because helper insertion changes downstream positions.
- Header checksum differs:
  - Build 59 @ `0x018E..0x018F`: `20dc`
  - Build 60 @ `0x018E..0x018F`: `0432`

Helper region:
- Build 59 at `0x00071C78`: starts with `48 E7 7F F8 ...` (`load_scene_tiles` prologue)
- Build 60 at `0x00071C78`: `60 FE 00 00 48 E7 7F F8 ...`

### §3.3 Embedded LUT/preload regions in ROMs
Using symbol-derived offsets:
- Build 60 symbol map (`apps/rastan-direct/out/symbol.txt`) gives:
  - LUT `genesistan_pc080sn_tile_vram_lut`: `0x0F1EC0`
  - Attr LUT: `0x0F9EC0`
  - Title preload: `0x179F00`
  - Gameplay preload: `0x17AC26`
  - Endround preload: `0x17B91C`
- Build 59 corresponding regions are at `offset-4`.

Region SHA comparison (Build 59 vs Build 60, aligned by +4 offset):
- LUT:
  - Build 59 SHA: `ca9c3dcf1aa3624c3660aa3b7443625433341941955c2c3f7c5956f44f5d3e92`
  - Build 60 SHA: `9f2f2e8ed1d6439d268d12cf19e2c72dc684779b6681880133338a03840b9d74`
  - Match: NO
- Preload title:
  - Build 59 SHA: `e0a814f2638c638e2ec710a91bc88e2603af6ea95afbcd3fb34203c5002fe52f`
  - Build 60 SHA: `58f3d6f8aad98c6462620fadba4a6484518fc87e2dfee0fa0ec6c3d339e9d681`
  - Match: NO
- Preload gameplay:
  - Build 59 SHA: `462c428c771428682e1be618dd2b72c54136c49a665fe4b09e1f935d6a7cdb6c`
  - Build 60 SHA: `ea39f75a52dfbe0846fa106888dd7b1fb8a4d4865869851dcde6da8f9d0cdc4c`
  - Match: NO
- Preload endround:
  - Build 59 SHA: `690835b85f60451935a325db066a10139f946125b354c3f100412149ef730acc`
  - Build 60 SHA: `252174d57ba91592c31946c9c99ed1ab0a0d93aef12bb0ef009c816f1d4d543e`
  - Match: NO
- Attr LUT:
  - Build 59 SHA: `2614c7b4c5ba7716fa6cc985f65ad2832c029956243d5570da52975d230fba3b`
  - Build 60 SHA: `2614c7b4c5ba7716fa6cc985f65ad2832c029956243d5570da52975d230fba3b`
  - Match: YES

Decoded semantic proof from LUT/preload bytes:
- Build 59 and current build artifact LUT:
  - `0x20 -> 0x00`, `0x23 -> 0x01`, `0x01 -> 0x3E` (post-fix)
- Build 60 embedded LUT:
  - `0x20 -> 0x14`, `0x23 -> 0x15`, `0x01 -> 0x52` (pre-fix)
- Title preload first 5 pairs:
  - Build artifact + Build 59: `(0x20,0) (0x23,1) (0x24,2) ...`
  - Build 60 embedded: `(0x20,20) (0x23,21) (0x24,22) ...`

Conclusion from bytes:
- Build 60 ROM does not embed the same LUT/preload content as Build 59.
- Build 60 embeds pre-CLOSED-007-style slot-offset content (+0x14) for LUT and preload manifests.

## §4 Makefile / Object / Postpatcher Forensics

### §4.1 Dependency chain evidence
`scene_load.s` includes these generated files:
- `build/pc080sn_tile_vram_lut.bin`
- `build/pc080sn_attr_lut.bin`
- `build/regions/pc080sn.bin`
- `build/pc080sn_scene_preload_title.bin`
- `build/pc080sn_scene_preload_gameplay.bin`
- `build/pc080sn_scene_preload_endround.bin`

But Makefile rule is:
- `$(OUT_DIR)/scene_load.o: $(SRC_DIR)/scene_load.s | $(OUT_DIR)`

No generated `.incbin` dependencies are listed for `scene_load.o`.

### §4.2 Direct stale-object proof
- `apps/rastan-direct/out/scene_load.o` timestamp: `2026-05-07 09:19:46` (older than Build 60)
- `scene_load.o` symbol offsets inside `.rodata`:
  - LUT at `0x00000000`
  - Attr LUT at `0x00008000`
  - Title preload at `0x00088040`
  - Gameplay preload at `0x00088D66`
  - Endround preload at `0x00089A5C`

SHA comparison of `scene_load.o` embedded blobs vs current `build/*` artifacts:
- LUT: mismatch (`scene_load.o` = `9f2f...`, build file = `ca9c...`)
- Title preload: mismatch (`58f3...` vs `e0a8...`)
- Gameplay preload: mismatch (`ea39...` vs `462c...`)
- Endround preload: mismatch (`2521...` vs `6908...`)
- Attr LUT: match (`2614...`)

These mismatched `scene_load.o` blob SHAs match Build 60 ROM embedded region SHAs exactly.

Inference from direct evidence:
- Build 60 linked a stale `scene_load.o` carrying pre-fix LUT/preload bytes.
- Current generated artifacts on disk are post-fix, but were not re-assembled into `scene_load.o` before Build 60 link.

### §4.3 Postpatcher line 1757/1762 inspection
File: `tools/translation/postpatch_startup_rom.py`
- Line 1757: comparison value changed to `0x17CAEC`
- Line 1762: error-message expected value text changed to `0x17CAEC`

Semantic role:
- Both changes are in invariant check/error-string path.
- No write-path transformation logic changed in those lines.
- No evidence those specific edits altered LUT/preload bytes.

## §5 Scenario Classification

### §5.1 Classification result
**Scenario C — Stale ROM linkage** (supported).

Evidence basis:
1. Source constant intact (`TILE_CACHE_BASE_A = 0`), so not Scenario A.
2. Build-tree generated LUT/preload artifacts are post-fix and match Build 59 embedded content, so not Scenario B.
3. Build 60 embedded LUT/preload bytes are pre-fix and match stale `scene_load.o` embedded blobs, proving stale object linkage at ROM build time.
4. Attr LUT remains identical across Build 59/60 and build-tree artifact, narrowing the fault to specific `.incbin` data baked into stale `scene_load.o`.
5. Postpatcher lines 1757/1762 are invariant-check-only changes, no direct evidence of byte-transformation side effect (not Scenario E by current evidence).

### §5.2 Recommended next task (no fix proposal)
- **Task type:** Build-pipeline determinism classification + scoped implementation task.
- **Scope:** establish dependency-correct, reproducible embedding of all `scene_load.s` `.incbin` inputs into `scene_load.o`, then verify ROM embedding determinism against Build 59 post-fix baseline.

No fix details are proposed in this forensics report.

## Integrity
- Generator source verified: YES (`TILE_CACHE_BASE_A=0`)
- Timestamps documented: YES
- Git status/diff/log inspected: YES
- Artifact SHAs computed: YES
- LUT first-byte pattern inspected: YES
- ROM 59 vs 60 binary comparison performed: YES
- Embedded LUT/preload bytes extracted and compared: YES
- Makefile dependency chain documented: YES
- Helper-introduction interaction analyzed: YES
- Postpatch lines 1757/1762 inspected: YES
- Scenario classified with byte evidence: YES (C)
- Recommended next task provided without proposing fix: YES
- No regenerations: YES
- No rebuilds: YES
- No make invocations: YES
- No timestamp touches: YES
- No source/spec/tool/Makefile/ROM/generated-artifact modifications: YES
- CLOSED-007 not reopened: YES
