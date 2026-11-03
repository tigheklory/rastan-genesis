# Cody - PC090OJ Object-RAM Mirror Phase 1 Implementation

**Date:** 2026-07-01  
**Type:** Implementation + build + evidence  
**Build produced:** Build 0123  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0123.bin`  
**SHA256:** `3a678621d2f71f4a0ce08d7a07d1a55e90e3b9a77cca62d601d4a9cbeb9b3a41`  
**Scope:** Pure `rastan-direct` assembly Phase 1 for PC090OJ active object-RAM mirror -> VBlank scan/decode -> generated Genesis SAT -> SAT DMA. No C, no SGDK, no MAME code port, no fake sprite data, no bookmarks, no game-flow change, no Window/D00298 work.

## Phase 0

**Relevant priors:** KF-010 (BG/FG plane mapping), KF-011 (arcade VBlank owns lifecycle; Genesis helpers only), KF-016 (title-state sprite-RAM clear context), KF-021 (sprite renderer/SAT suppression hazard), KF-026 (PC090OJ write surface not fully statically enumerable), KF-032 (raw copied hardware writes must route to staging/mirror, not Genesis VDP aliases), KF-036 (mapped work-RAM base rule), KF-038 (BG row aliasing context only).

**High rediscovery hazards touched:** KF-011, KF-021, KF-026, KF-032, KF-036. No contradiction requiring STOP. The known architectural contradiction was the target of this task: the old sprite layer was hook-slot/event-oriented, while PC090OJ hardware is an object-RAM table scanned each frame.

**Issue pre-check:** OPEN-024 primary; OPEN-001 context; OPEN-006 palette/sprite context; OPEN-023 Window explicitly out of scope; OPEN-015/D00298 safety context only; OPEN-021 not touched.

## WRAM/BSS Budget

Pre-implementation `.bss` ended at `0x00FF6828` (`.bss` size `0x2828`). Existing relevant buffers before this task:

| Symbol | Address | Size / range |
|---|---:|---|
| `staged_bg_buffer` | `0x00FF401A` | `0x1000`, ends `0x00FF501A` |
| `staged_fg_buffer` | `0x00FF501A` | `0x1000`, ends `0x00FF601A` |
| `staged_palette_words` | `0x00FF601A` | `0x80`, ends `0x00FF609A` |
| `staged_tile_words` | `0x00FF609A` | `0x60`, ends `0x00FF60FA` |
| `staged_sprite_sat` | `0x00FF6104` | `0x280`, ends `0x00FF6384` |
| `staged_sprite_descriptor_table` | `0x00FF6384` | `0x3C0`, ends `0x00FF6744` |
| `staged_sprite_dirty` | `0x00FF6744` | `0x4`, ends `0x00FF6748` |
| `staged_sprite_active_count` | `0x00FF6748` | word |

Added allocations in final Build 0123:

| Symbol | Address | Size / range |
|---|---:|---|
| `pc090oj_object_ram` | `0x00FF674A` | `0x800`, ends `0x00FF6F4A` |
| `pc090oj_ctrl_shadow` | `0x00FF6F4A` | word |
| `pc090oj_sprite_ctrl_shadow` | `0x00FF6F4C` | word |
| `pc090oj_mirror_dirty` | `0x00FF6F4E` | word |
| `pc090oj_decoded_count` | `0x00FF6F50` | word |
| `pc090oj_drawable_count` | `0x00FF6F52` | word |
| `pc090oj_emitted_count` | `0x00FF6F54` | word |
| `pc090oj_dropped_count` | `0x00FF6F56` | word |
| `pc090oj_scan_colbank` | `0x00FF6F58` | word |
| `pc090oj_scan_active` | `0x00FF6F5A` | word |

Final `.bss` size is `0x3038`, ending at `0x00FF7038`. Stack base remains `0x00FF0000` and grows downward. The new mirror/control allocation does not overlap the tilemap, palette, tile, sprite, or mapped arcade work-RAM ranges. Approximate headroom from `.bss` end to `0x01000000` is `0x8FC8` bytes.

Caveat: the crash handler has pre-existing crash-record constants in `0xFF6800..`; current and prior BSS already overlap that area at crash time. Runtime mirror evidence should be captured before exception handling when possible.

## Implementation Summary

Files changed for implementation:

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/boot/boot.s`
- `specs/rastan_direct_remap.json`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

New symbols:

- `pc090oj_object_ram`
- `pc090oj_ctrl_shadow`
- `pc090oj_sprite_ctrl_shadow`
- `pc090oj_mirror_dirty`
- `pc090oj_decoded_count`
- `pc090oj_drawable_count`
- `pc090oj_emitted_count`
- `pc090oj_dropped_count`
- `pc090oj_scan_colbank`
- `pc090oj_scan_active`
- `genesistan_pc090oj_ctrl_set_1`
- `genesistan_pc090oj_ctrl_set_0`
- `genesistan_pc090oj_sprite_ctrl_write_d0`
- `genesistan_pc090oj_sprite_ctrl_clear`

Legacy hooks were preserved. They now bridge their semantic sprite tuple into `pc090oj_object_ram` through `.Lpc090oj_emit_slot` when not in mirror-scan mode. During mirror scan, `pc090oj_scan_active=1` prevents decoded/flipped Genesis output from being written back into arcade object-RAM truth.

## Write Routing

### Active PC090OJ object RAM

`genesistan_hook_3ad44_dispatch` keeps its tilemap branch unchanged. Its PC090OJ branch now mirrors the original arcade long-fill behavior into `pc090oj_object_ram` for `HW_ADDRESS 0x00D00000..0x00D007FF`:

- preserves longword fill order as high word then low word
- preserves byte offset from `A0 - 0x00D00000`
- stops at the active `0x800` mirror limit
- does not route `0x00D01BFE` into the active mirror

The original arcade routine at `arcade_pc 0x03AD44` is an original long-fill loop (`move.l d0,(a0)+; subq.w #1,d1; bne`). The mapped patched site is `runtime_genesis_pc 0x03AF44`, kind `patched_site`, from `address_map.json`.

### PC090OJ global control

Previously suppressed `HW_ADDRESS 0x00D01BFE` writes are now captured:

| arcade_pc | runtime_genesis_pc | Value | Helper |
|---:|---:|---:|---|
| `0x03AE06` | `0x03B006` | `1` | `genesistan_pc090oj_ctrl_set_1` |
| `0x03AE1E` | `0x03B01E` | `0` | `genesistan_pc090oj_ctrl_set_0` |
| `0x03AE8E` | `0x03B08E` | `0` | `genesistan_pc090oj_ctrl_set_0` |

Final runtime evidence at the post-commit boundary shows `pc090oj_ctrl_shadow=0x0001`, so the global-flip transform was not active for that captured frame.

### External `sprite_ctrl` / palette bank

Previously suppressed `HW_ADDRESS 0x00380000` writes now capture the arcade value into `pc090oj_sprite_ctrl_shadow` via `genesistan_pc090oj_sprite_ctrl_write_d0`; the clear site uses `genesistan_pc090oj_sprite_ctrl_clear`. This is a direct capture, not the old `a5@(20)` fallback.

Final runtime evidence shows `pc090oj_sprite_ctrl_shadow=0x0060`, yielding `pc090oj_scan_colbank=0x0030` (`(0x0060 & 0x00E0) >> 1`).

## Address Mapping Discipline

Mapped code sites were checked through `build/rastan-direct/address_map.json`. Examples used by this implementation:

| arcade_pc | runtime_genesis_pc | map kind |
|---:|---:|---|
| `0x03AD44` | `0x03AF44` | `patched_site` |
| `0x03AE06` | `0x03B006` | `patched_site` |
| `0x03AE1E` | `0x03B01E` | `patched_site` |
| `0x03AE8E` | `0x03B08E` | `patched_site` |
| `0x03A1D8` | `0x03A3D8` | `patched_site` |
| `0x03AE34` | `0x03B034` | `patched_site` |
| `0x03AE9C` | `0x03B09C` | `patched_site` |
| `0x03AF1E` | `0x03B11E` | `patched_site` |
| `0x03EF28` | `0x03F128` | `patched_site` |
| `0x03EF48` | `0x03F148` | `patched_site` |
| `0x03EF8A` | `0x03F18A` | `patched_site` |
| `0x03EFAA` | `0x03F1AA` | `patched_site` |
| `0x045306` | `0x045506` | `patched_site` |

Genesis-only helpers (`vdp_commit_sprites`, mirror scan, control-shadow setters) are labeled Genesis-only/helper.

## Mirror-Scan Decoder

`vdp_commit_sprites` now calls `.Lvcs_mirror_scan` before the existing link-chain/tile-DMA/SAT-DMA phases.

Per scanned entry:

- scans 256 entries from `pc090oj_object_ram`
- decodes word0 flip/color, word1 Y, word2 code, word3 X
- applies `code & 0x1FFF`
- treats code 0 as non-drawable because `build/pc090oj_genesis.bin` tile 0 was verified all-zero (`128/128` bytes zero)
- applies signed wrap for X/Y when `> 0x140` by subtracting `0x200`
- applies PC090OJ global flip only when `pc090oj_ctrl_shadow bit0 == 0`
- skips fully offscreen sprites after decode/flip
- emits first up to 80 drawable entries in PC090OJ entry order
- counts decoded/drawable/emitted/dropped entries

No extra X/Y display-origin bias was added. That remains intentionally deferred until measured for PC090OJ.

## Genesis SAT Output

The generated output reuses the existing `staged_sprite_sat`, `staged_sprite_descriptor_table`, tile DMA, link-chain, and SAT DMA infrastructure. One existing structural bug was fixed: the link builder previously used `btst #0,(%a0)`, which tests a byte in memory on 68000 and missed descriptor flags stored as word `0x0001`. It now loads the word into `%d1` before testing bit 0, producing a valid link chain.

The existing `vdp_commit_sprites` still performs SAT DMA to VRAM `0xF800`. True VDP VRAM/SAT was not directly dumped in this task; MAME debugger/Lua evidence captured WRAM mirror and generated staged SAT only. This is a stated limitation.

## Build

Build command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: PASS / `GATE_PASS`.

- Build counter advanced to `0123`
- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0123.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `3a678621d2f71f4a0ce08d7a07d1a55e90e3b9a77cca62d601d4a9cbeb9b3a41`
- ROM size: `1,560,968` bytes
- Rolling and numbered ROMs are byte-identical (`cmp=0`)
- opcode_replace patched-site count: `133`
- canonical total covered bytes: `0x17D19C`
- Linker warning: existing RWX LOAD segment warning only

Release-created MAME trace:

- `states/traces/rastan_direct_video_test_build_0123_mame_30s_20260701_133342/`
- `frames=1798`
- no unmapped memory addresses in MAME exit summary

## Runtime Evidence

Final evidence directory:

- `states/traces/build_0123_pc090oj_object_ram_phase1_20260701_133359/`

Evidence artifacts:

- `postcommit_pc090oj_object_ram_ff674a.txt`
- `postcommit_staged_sprite_sat_ff6104.txt`
- `postcommit_staged_sprite_descriptor_table_ff6384.txt`
- `postcommit_sprite_counts_ctrl_ff6f4a.txt`
- `postcommit_state_ff0000_0080.txt`
- `postcommit_pc090oj_phase1_summary.md`
- `postcommit_pc090oj_phase1_summary.json`

Post-commit runtime summary:

- state first words: `0000 0001 0000 0000 0001 0001 0000 0001`
- `pc090oj_decoded_count=256`
- `pc090oj_drawable_count=4`
- `pc090oj_emitted_count=4`
- `pc090oj_dropped_count=0`
- `pc090oj_ctrl_shadow=0x0001`
- `pc090oj_sprite_ctrl_shadow=0x0060`
- `pc090oj_scan_colbank=0x0030`
- `pc090oj_mirror_dirty=0x0001`
- `pc090oj_scan_active=0x0000` at dump point
- mirror nonzero entries: `240`
- generated SAT/descriptor entries: `4`
- link chain from slot 0: `[0, 1, 2, 3]`

First generated SAT entries:

| Slot | SAT y | SAT size/link | SAT attr | SAT x | Source entry | Code |
|---:|---:|---:|---:|---:|---:|---:|
| 0 | `0x0080` | `0x0501` | `0xE400` | `0x0080` | 4 | `0x0001` |
| 1 | `0x0080` | `0x0502` | `0xE404` | `0x00AA` | 14 | `0x0110` |
| 2 | `0x0100` | `0x0503` | `0xE408` | `0x0080` | 16 | `0x0080` |
| 3 | `0x0100` | `0x0500` | `0xE40C` | `0x0081` | 17 | `0x0080` |

The final link word `0x0500` terminates the chain at slot 3. Unused entries are not reachable from slot 0 in this capture.

Screenshot: not captured in this headless evidence pass. Visual improvement is not claimed.

True VDP SAT: not directly captured. The staged SAT and static DMA path to `0xF800` are proven; true VRAM/SAT capture remains a follow-up limitation.

## D00298 Safety

D00298 dynamic-path work was not performed. No BlastEm run was performed. The release MAME trace completed without unmapped memory addresses. No dangerous stepping at `0x3B292` or `0x5A724` was performed.

## Classification

**Final classification:** BUILD/RUNTIME SUCCESS, structurally limited.

Phase 1 success criteria met:

- WRAM/BSS budget checked before allocation.
- `pc090oj_object_ram` exists and is 0x800 bytes.
- `0x3AD44` PC090OJ long-fill active-range writes update the mirror.
- Legacy hooks are preserved and bridged into the mirror, but still require future provenance cleanup.
- `0xD01BFE` PC090OJ global control is captured.
- `0x380000` sprite_ctrl is captured directly.
- `vdp_commit_sprites` generates SAT from the mirror scan.
- Genesis SAT link chain is valid in the final post-commit dump.
- Unused entries are unreachable in the captured chain.
- Build succeeds and produces Build 0123.
- Runtime evidence shows mirror contents, counts, generated staged SAT, and link chain.

Limitations:

- This does not complete the sprite subsystem.
- This does not prove the pommel artifact is fixed.
- True VDP SAT/VRAM was not dumped.
- Legacy per-site hooks still run and bridge into the mirror through their existing slot allocation; this is a compatibility bridge, not the final all-writers PC090OJ provenance model.
- PC090OJ display-origin bias remains unmeasured and intentionally not applied.

## Open / Closed Issues Impact

- Open issues touched: OPEN-024 primary; OPEN-001 context; OPEN-006 context; OPEN-023 context only; OPEN-015 safety context only.
- Closed issues touched: NONE.
- New issues opened: NONE.
- Issues closed: NONE.
- Deferred: true VDP SAT capture, visual validation, remaining unhooked/raw PC090OJ writer coverage, legacy-hook provenance cleanup, D00298 dynamic-path fix.

## STOP

STOP triggered: NO.
