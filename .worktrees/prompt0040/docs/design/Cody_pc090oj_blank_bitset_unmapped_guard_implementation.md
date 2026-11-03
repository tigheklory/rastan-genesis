# Cody - PC090OJ Blank Bitset and Unmapped-Code Guard Implementation

**Date:** 2026-07-01  
**Type:** Implementation + build + evidence  
**Baseline:** `rastan-direct` Build 0123, SHA `3a678621d2f71f4a0ce08d7a07d1a55e90e3b9a77cca62d601d4a9cbeb9b3a41`  
**Produced Build:** Build 0124, SHA `f5935113ef4ab8ea231d4e31764b96a36c8bd2fe246846a2ca929facdfccd921`  
**Scope:** PC090OJ blank-code bitset and unmapped-code guard at Genesis SAT emission/compaction. No PC080SN Plane A/B changes, no Window changes, no D00298 fix, no C/SGDK, no MAME-code port, no visual-improvement claim.

## Phase 0

Relevant priors loaded:

- KF-010 applies because PC090OJ sprites are committed through Genesis VDP SAT while PC080SN BG/FG remain Plane B/A staging concerns.
- KF-011 applies because the Genesis VBlank service remains hardware-service only; arcade code remains the program.
- KF-016 applies as general VDP/SAT correctness context.
- KF-021 applies as stale/true-VDP-SAT divergence hazard; true VDP SAT capture was therefore mandatory.
- KF-026 applies because this task must preserve arcade object state and avoid synthetic runtime scaffolding.
- KF-032 applies because raw hardware writes must route through staging/helpers rather than Genesis hardware aliases.
- KF-036 applies because mapped/runtime state must use the correct Genesis-side storage, not arcade addresses.
- KF-038 is context only; this task does not chase D00298.

High-rediscovery hazards touched: KF-011, KF-021, KF-026, KF-032, KF-036. No contradiction was detected.

Task classification: **IMPLEMENTATION / EXTENDING OPEN-024**.

Open/Closed pre-check:

- OPEN-024 primary.
- OPEN-001 and OPEN-006 context.
- OPEN-023 Window context only.
- OPEN-015 not touched except D00298 safety awareness.
- No Closed issue changed.

Address mapping pre-check:

- `build/rastan-direct/address_map.json` loaded: YES.
- Arithmetic offset conversion used as proof: NO.
- Unmapped address correlation found: NO.

## Address Mapping Discipline

Address-map verified patched sites relevant to the PC090OJ control/object branch already present in the build:

| runtime_genesis_pc | arcade_pc | address_map segment | kind | patched span? | note |
|---:|---:|---:|---|---|---|
| `0x0003AF44` | `0x0003AD44` | `segments/59` | `patched_site` | YES | PC090OJ + tilemap polymorphic utility dispatch via `genesistan_hook_3ad44_dispatch` |
| `0x0003B006` | `0x0003AE06` | `segments/64` | `patched_site` | YES | PC090OJ control write `#1` capture to `pc090oj_ctrl_shadow` |
| `0x0003B01E` | `0x0003AE1E` | `segments/67` | `patched_site` | YES | PC090OJ control write `#0` capture to `pc090oj_ctrl_shadow` |
| `0x0003B08E` | `0x0003AE8E` | `segments/72` | `patched_site` | YES | PC090OJ control write `#0` capture to `pc090oj_ctrl_shadow` |

No arcade-to-Genesis correlation in this report is proven by `+0x200` arithmetic.

## Implementation

### Blank-code bitset

Added `tools/translation/build_pc090oj_blank_bitset.py`.

The generator reads `build/pc090oj_genesis.bin`, validates exactly `4096 * 128` bytes, and emits a 4096-bit / 512-byte bitset where a bit is set only when all 128 bytes for that converted 16x16 cell are pixel index `0`.

Make integration:

- `apps/rastan-direct/Makefile` now builds `build/pc090oj_blank_bitset.bin` from `build/pc090oj_genesis.bin`.
- `apps/rastan-direct/src/pc090oj_assets.s` now exports `pc090oj_blank_code_bitset` via `.incbin`.

Generated bitset verification:

- Path: `build/pc090oj_blank_bitset.bin`
- Size: `512` bytes
- SHA256: `062a1d10a04a65a5da11be369bd002d5c65378667edf4d62c315305e38a0f948`
- Blank count: `22`
- Codes: `0x000`, `0x002`, `0x004`, `0x045`, `0x0A8`, `0x0A9`, `0x0AA`, `0x0AB`, `0x0F3`, `0x100`, `0x178`, `0x1D8`, `0x4FF`, `0x5B0`, `0x5D6`, `0x5D7`, `0x5D8`, `0x5D9`, `0x5DB`, `0x9FD`, `0xAA3`, `0xAC2`

This matches the required 22-code list. The implementation does not hardcode that list.

### Counters

Added and boot-cleared:

- `pc090oj_code_zero_skipped_count`
- `pc090oj_blank_skipped_count`
- `pc090oj_unmapped_skipped_count`
- `pc090oj_offscreen_skipped_count`

Existing counters remain:

- `pc090oj_decoded_count`
- `pc090oj_drawable_count`
- `pc090oj_emitted_count`
- `pc090oj_dropped_count`

Symbol locations after Build 0124:

| Symbol | Address |
|---|---:|
| `pc090oj_ctrl_shadow` | `0x00FF6F4A` |
| `pc090oj_sprite_ctrl_shadow` | `0x00FF6F4C` |
| `pc090oj_mirror_dirty` | `0x00FF6F4E` |
| `pc090oj_decoded_count` | `0x00FF6F50` |
| `pc090oj_code_zero_skipped_count` | `0x00FF6F52` |
| `pc090oj_blank_skipped_count` | `0x00FF6F54` |
| `pc090oj_unmapped_skipped_count` | `0x00FF6F56` |
| `pc090oj_offscreen_skipped_count` | `0x00FF6F58` |
| `pc090oj_drawable_count` | `0x00FF6F5A` |
| `pc090oj_emitted_count` | `0x00FF6F5C` |
| `pc090oj_dropped_count` | `0x00FF6F5E` |
| `pc090oj_scan_active` | `0x00FF6F62` |

### Mirror scan order

`apps/rastan-direct/src/pc090oj_hooks.s` now classifies each active mirror entry before SAT emission:

1. Decode PC090OJ code as `word2 & 0x1FFF`.
2. If code is `0`, increment `pc090oj_code_zero_skipped_count` and skip emission.
3. If code is `>= 0x1000`, increment `pc090oj_unmapped_skipped_count` and skip emission before indexing the 4096-entry bitset.
4. If code is `< 0x1000`, test `pc090oj_blank_code_bitset`.
5. If blank bit is set, increment `pc090oj_blank_skipped_count` and skip emission.
6. Otherwise proceed through signed coordinate wrap, global flip, offscreen tests, drawable count, 80-sprite limit, and emission.

`pc090oj_object_ram` is not written, cleared, normalized, or reordered by this filter. The mirror remains arcade object-table truth.

### Tile DMA guard

High codes are rejected in the mirror scan before descriptor emission. Therefore no descriptor with semantic code `>= 0x1000` should reach tile DMA from the mirror scan path.

The tile DMA still masks the descriptor code with `0x0FFF` as an address-safety guard for the converted 4096-cell asset. That mask is not the semantic high-code rendering rule; high codes are already skipped and counted before DMA.

### SAT safety

Preserved safety properties:

- `.Lvcs_clear_generated_sprite_state` clears all 80 generated SAT entries before mirror scan.
- `.Lvcs_clear_generated_sprite_state` clears all 80 generated descriptor entries before mirror scan.
- `.Lvcs_sat_dma` transfers 640 bytes / 320 words from `staged_sprite_sat` to VDP SAT at VRAM `0xF800`, i.e. all 80 entries.
- Link-chain build only links valid descriptors. Cleared/invalid descriptors are unreachable.
- If no valid descriptor exists, slot 0 remains zero and link `0` terminates the chain.

Proof type for zero/decreasing count safety: **Option C, static proof**. Clear-before-scan plus full-80 SAT DMA prevents prior-frame reachable SAT entries from surviving a lower emitted count.

## Build

First release invocation stopped at the canonical invariant gate before producing a numbered artifact:

```text
expected total_genesis_bytes_covered=0x17D19C and opcode_replace patched_site count=133;
got total_genesis_bytes_covered=0x17D400 opcode_replace patched_site count=133
```

The invariant was then corrected to the observed mechanical value `0x17D400` in:

- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

Second release invocation produced Build 0124.

Build output:

- Build: `0124`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0124.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `f5935113ef4ab8ea231d4e31764b96a36c8bd2fe246846a2ca929facdfccd921`
- Size: `1,561,600` bytes
- Rolling ROM byte-identical to numbered ROM: YES
- Canonical gate: `GATE_PASS`
- `opcode_replace` patched-site count: `133`
- `total_genesis_bytes_covered`: `0x17D400`
- Automatic release trace: `states/traces/rastan_direct_video_test_build_0124_mame_30s_20260701_160115/`
- Automatic trace outcome: completed, no unique unmapped memory addresses reported.

## Runtime Evidence

Evidence directory:

`states/traces/pc090oj_blank_bitset_unmapped_guard_20260701_160224/`

Capture method:

- MAME Genesis driver, Build 0124 ROM.
- Headless/no-input probe.
- Captured at frame `90` after sprite commit.
- True VDP SAT captured through MAME device `sega315_5313(:gen_vdp)` space `videoram` at VRAM `0xF800..0xFA7F`.

Probe log confirms:

```text
VDP_DEVICE sega315_5313(:gen_vdp)
vdp.spaces.videoram=sega315_5313(:gen_vdp):videoram
DUMP_VDP_SPACE frame=90 space=videoram name=true_vdp_sat_f800_space_videoram.bin
TRUE_VDP_SAT_CAPTURED=true
```

Frame 90 counters:

| Counter | Value |
|---|---:|
| `pc090oj_ctrl_shadow` | `1` |
| `pc090oj_sprite_ctrl_shadow` | `0x0060` |
| `pc090oj_mirror_dirty` | `1` |
| `pc090oj_decoded_count` | `256` |
| `pc090oj_code_zero_skipped_count` | `252` |
| `pc090oj_blank_skipped_count` | `0` |
| `pc090oj_unmapped_skipped_count` | `0` |
| `pc090oj_offscreen_skipped_count` | `0` |
| `pc090oj_drawable_count` | `4` |
| `pc090oj_emitted_count` | `4` |
| `pc090oj_dropped_count` | `0` |
| `pc090oj_scan_colbank` | `0x0030` |
| `pc090oj_scan_active` | `0` |

Important interpretation: `pc090oj_emitted_count=4` records four emission attempts through the mirror scan. The final post-commit descriptor table and true VDP SAT at this capture are all zero because those attempts resolved to invalid/cleared generated state after helper validation and dirty-clear. This report therefore does not treat `emitted_count=4` as four visible sprites.

Evidence files:

| File | Size | SHA256 |
|---|---:|---|
| `frame90_staged_sprite_sat_ff6104.bin` | `640` | `9e132485d5107211de325a45e7917cbe3e4b5b9cde3e4ee91d7d2102317759ee` |
| `true_vdp_sat_f800_space_videoram.bin` | `640` | `9e132485d5107211de325a45e7917cbe3e4b5b9cde3e4ee91d7d2102317759ee` |
| `frame90_staged_sprite_descriptor_table_ff6384.bin` | `960` | `3dc463a76fc170607c07b104c3cb531362ce7d6e10c1a34e0c0f370aeae08ce8` |
| `frame90_pc090oj_object_ram_ff674a.bin` | `2048` | `f1d3f63a03f4efc9d1c9a1990291b829fc9e6f7fbd39dfc7fb51016e15f83510` |
| `frame90_sprite_counts_ctrl_ff6f4a.bin` | `32` | `7dcabe94362ee109d332e751a20a1ad2796eaf380a4552e42bb6e86df300cf8a` |

Reduced analysis files:

- `states/traces/pc090oj_blank_bitset_unmapped_guard_20260701_160224/pc090oj_guard_analysis.json`
- `states/traces/pc090oj_blank_bitset_unmapped_guard_20260701_160224/pc090oj_guard_analysis.md`

## True VDP SAT

True VDP SAT result at frame 90:

- Captured: YES.
- Method: MAME `:gen_vdp` `videoram` space dump, VRAM `0xF800..0xFA7F`.
- True VDP SAT matches `staged_sprite_sat`: YES, byte-identical SHA256.
- True VDP SAT all 80 slots zero: YES.
- Reachable chain from slot 0: `[0]`.
- Reachable nonzero slots: `[]`.
- Extra/stale reachable entries beyond intended chain: NO.

Black-overdraw hypothesis impact:

- For this captured frame, stale true-VDP-SAT divergence is refuted: the hardware SAT equals the staged SAT and contains no stale reachable entries.
- This does **not** prove the pommel or black-overdraw visual issue is fixed globally. It only proves the required Build 0124 frame-90 true-SAT condition.
- No visual improvement is claimed.

## Build 0123-Equivalent Comparison

Build 0123-equivalent emitted codes from prior evidence were `0x0001`, `0x0110`, `0x0080`, `0x0080`; all are valid nonblank cells, so the blank-bitset/unmapped guard is not expected to suppress those specific codes.

Build 0124 frame 90 observed:

- Code-zero skips: `252`
- Blank-code skips: `0`
- Unmapped-code skips: `0`
- Dropped/overflow: `0`

Emitted sprites changed: **not proven**. The captured true VDP SAT is all zero at frame 90; no visual comparison was performed. Visual change claimed: **NO**.

## Classification

Final classification: **implementation complete, evidence captured; visual/root-cause not claimed**.

Confidence:

- High for generated bitset correctness: build-time generator and exact required 22-code verification.
- High for unmapped guard placement: high code rejected before bitset lookup and descriptor emission in mirror scan.
- High for true VDP SAT frame-90 comparison: true VDP SAT capture succeeded and is byte-identical to staged SAT.
- Limited for visual impact: no screenshot/visual pass was run, and the prompt forbids claiming the black-overdraw fix without visual and true-VDP evidence.

What this fixed:

- Added generated blank-code bitset for PC090OJ converted cells.
- Added unmapped-code guard for decoded PC090OJ codes `>= 0x1000`.
- Added counters for code-zero, blank, unmapped, and offscreen skips.
- Preserved emission-only filtering and object-RAM truth.
- Confirmed full-SAT clear/DMA safety and true VDP SAT agreement for the captured frame.

What this did not fix:

- Does not claim to fix black overdraw.
- Does not claim to fix the pommel.
- Does not touch PC080SN Plane A/B.
- Does not touch Window.
- Does not analyze or fix D00298.

Next evidence target:

- If the visual black/pommel artifact persists, capture synchronized visual + true VDP SAT/VRAM evidence at the exact artifact frame, now that the basic true-SAT-vs-staged comparison path is working.

## Open / Closed Issues Impact

- Open issues touched: OPEN-024 primary; OPEN-001 and OPEN-006 context; OPEN-023 Window context only.
- Closed issues touched: NONE.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: D00298, Window, PC080SN Plane A/B, pommel/black-overdraw visual root cause.

## STOP

STOP status: NO.
