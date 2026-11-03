# Cody - Build 0137 Active-Count SAT DMA

**Date:** 2026-07-03  
**Type:** One narrow production implementation + verification  
**Build:** 0137  
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0137.bin`  
**SHA256:** `52655015379fdd8524e2c3856b491004d9e7ee7abf15c275af78fa0011175428`  
**Scope:** `.Lvcs_sat_dma` SAT DMA length calculation only in `apps/rastan-direct/src/pc090oj_hooks.s`. No DISPLAY_OFF split, no candidate-mask change, no PC090OJ scan/decode change, no dirty-bit change, no PC080SN change, no sprite-order/link-builder rewrite, no bookmark, no diagnostics inserted into the ROM.

## Phase 0

Classification: **EXTENDING** OPEN-001 / OPEN-024 PC090OJ timing work. Relevant priors loaded: KF-010, KF-011, KF-028, KF-032, KF-036, plus Build 0135/0136 PC090OJ timing and candidate-mask evidence. No contradiction detected.

User/Andy design source: `docs/design/Andy_build0136_active_count_sat_dma_design.md`.

## Pre-Patch Preconditions

All required preconditions were verified before the patch:

- SAT slots are packed contiguously from slot `0` because `.Lvcs_mirror_emit` uses `pc090oj_emitted_count` as the slot index before incrementing it.
- `staged_sprite_active_count` is set by `.Lvcs_link_chain_build` after scan and before `.Lvcs_sat_dma`.
- At DMA time, `staged_sprite_active_count == pc090oj_emitted_count` for representative runtime samples.
- `.Lvcs_link_chain_build` writes the final active slot's word 1 as `0x0500`, giving link bits `0`.
- Link-chain construction runs before `.Lvcs_tile_dma` and `.Lvcs_sat_dma`.
- Zero-generated state is safe statically: `.Lvcs_clear_generated_sprite_state` clears the whole SAT staging area, including slot 0 Y and link word, and the new formula clamps zero active to one cleared SAT entry.

## Implementation

In `apps/rastan-direct/src/pc090oj_hooks.s`, `.Lvcs_sat_dma` now computes the SAT DMA length from the active sprite count:

```asm
    move.w  staged_sprite_active_count, %d0
    bne.s   .Lvcs_sat_dma_have_count
    moveq   #1, %d0
.Lvcs_sat_dma_have_count:
    cmpi.w  #80, %d0
    bls.s   .Lvcs_sat_dma_count_ok
    move.w  #80, %d0
.Lvcs_sat_dma_count_ok:
    lsl.w   #2, %d0

    move.w  %d0, %d1
    andi.w  #0x00FF, %d1
    ori.w   #0x9300, %d1
    move.w  %d1, (%a3)

    move.w  %d0, %d1
    lsr.w   #8, %d1
    andi.w  #0x00FF, %d1
    ori.w   #0x9400, %d1
    move.w  %d1, (%a3)
```

Formula: `dma_entries = max(min(staged_sprite_active_count, 80), 1)`, `dma_words = dma_entries * 4`.

Unchanged:

- SAT DMA source remains `staged_sprite_sat` / WRAM `0x00FF6104`.
- SAT DMA destination remains VRAM `0xF800`.
- DMA source registers `0x95/0x96/0x97` remain the same path.
- DMA trigger command remains the same path.
- `opcode_replace` site count remains `133`.

## Build

First release invocation stopped at the canonical invariant gate with the expected mechanical coverage delta:

- Expected: `0x17D560`
- Observed: `0x17D588`
- `opcode_replace` count: `133`

Only the two canonical invariant constants were updated:

- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

Second release invocation passed:

- `GATE_PASS`
- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0137.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `52655015379fdd8524e2c3856b491004d9e7ee7abf15c275af78fa0011175428`
- Size: `1,561,992` bytes
- Numbered and rolling ROMs byte-identical (`cmp=0`)
- Manifest/invariants: `opcode_replace=133`, `total_genesis_bytes_covered=0x17D588`

Release trace: `states/traces/rastan_direct_video_test_build_0137_mame_30s_20260703_213646/`.

## Static Verification

Generated disassembly confirms `.Lvcs_sat_dma` at `runtime_genesis_pc 0x0007234C`:

```asm
7234c: moveal #0x00c00004,%a3
72352: movew 0xff6748,%d0        ; staged_sprite_active_count
72358: bnes 0x7235c
7235a: moveq #1,%d0
7235c: cmpiw #80,%d0
72360: blss 0x72366
72362: movew #80,%d0
72366: lslw #2,%d0
72368: movew %d0,%d1
7236a: andiw #255,%d1
7236e: oriw #0x9300,%d1
72372: movew %d1,%a3@
72374: movew %d0,%d1
72376: lsrw #8,%d1
72378: andiw #255,%d1
7237c: oriw #0x9400,%d1
72380: movew %d1,%a3@
72382: movel #0xff6104,%d0       ; source unchanged
...
723b4: movel #0x0000f800,%d0     ; destination unchanged
723d8: movel %d1,%a3@            ; trigger unchanged
```

This proves the patch is confined to SAT DMA length-register math and does not move the source/destination/trigger sequence.

## Runtime Evidence

Evidence root: `states/traces/build0137_active_count_sat_dma_20260703_213808/`.

MAME Lua frame captures:

- `build0137/no_input/no_input_runtime_capture.log`
- `build0137/coin_start/coin_start_runtime_capture.log`

Native debugger length-register evidence:

- `debug_coin_start_printf/native_debug_sat_dma_len.log`
- Reduced summary: `active_count_sat_dma_reduction.md`
- Reduced JSON: `active_count_sat_dma_reduction.json`

Debugger breakpoints at `runtime_genesis_pc 0x00072372`, `0x00072380`, and `0x000723D8` captured `497` complete low/high/trigger triples. Observed active counts at SAT DMA: `[12, 19, 23, 27, 30, 32]`.

Representative length writes:

| Active count | DMA words | Low length register | High length register | State | Last-link proof before DMA |
|---:|---:|---:|---:|---|---|
| 19 | `0x004C` | `0x934C` | `0x9400` | `1/1/0` | slot 18 word1 = `0x0500` |
| 23 | `0x005C` | `0x935C` | `0x9400` | `0/0/1` | slot 22 word1 = `0x0500` |
| 30 | `0x0078` | `0x9378` | `0x9400` | `2/2/6` | slot 29 word1 = `0x0500` |
| 32 | `0x0080` | `0x9380` | `0x9400` | `2/2/7` | slot 31 word1 = `0x0500` |

The zero-active path was **not reached at the SAT DMA breakpoint** in this coin/start run. The source-level clamp and cleared slot-0 precondition are statically proven, but no runtime `active=0` SAT DMA register write was observed in this capture. Earlier frame-done samples with `active=0` occurred during scan/transition timing and are not used as actual DMA-length evidence.

## Runtime Count Parity

Build 0137 MAME anchors preserve Build 0136 active/emitted/drop behavior at the sampled stable points:

- No-input anchors: `active=0x17`, `emitted=0x17`, `dropped=0` at all matching sampled anchors.
- Coin/start representative anchors:
  - frame 411 prompt: `active=0x13`, `emitted=0x13`, `dropped=0`
  - frame 477 second clear: `active=0x1E`, `emitted=0x1E`, `dropped=0`
  - frame 534 ROUND: `active=0x20`, `emitted=0x20`, `dropped=0`
  - frame 620 late coin run: `active=0x20`, `emitted=0x20`, `dropped=0`

Frame 560 remains a mid-scan sampling edge in both Build 0136/0137 evidence and is not treated as semantic divergence.

## Visual Evidence

MAME contact sheets generated:

- Build 0137 no-input: `states/traces/build0137_active_count_sat_dma_20260703_213808/build0137_no_input_contact_sheet.png`
- Build 0137 coin/start: `states/traces/build0137_active_count_sat_dma_20260703_213808/build0137_coin_start_contact_sheet.png`
- Build 0136 no-input reference: `states/traces/build0137_active_count_sat_dma_20260703_213808/build0136_no_input_contact_sheet.png`
- Build 0136 coin/start reference: `states/traces/build0137_active_count_sat_dma_20260703_213808/build0136_coin_start_contact_sheet.png`

Pixel comparison summary: `states/traces/build0137_active_count_sat_dma_20260703_213808/visual_diff_summary.json`.

Result:

- Build 0137 no-input PNG anchors match Build 0136 exactly (`0` luma-diff pixels for all eight paired anchors).
- Build 0137 coin/start PNG anchors match Build 0136 exactly except `coin_start_0002.png`, which differs by `59` luma-diff pixels; no broad visible regression was observed in the contact sheets.

BlastEm contact sheets were **not produced**. Local BlastEm exposes debugger/event-log options but no scriptable screenshot or frame-dump CLI, and this WSL environment currently has `xwininfo` but no screenshot helper such as `import`, `scrot`, or `gnome-screenshot`. This is recorded as a verification gap rather than substituted with MAME evidence.

## Assessment

The Build 0137 production change is behaving as intended for all observed active-count SAT DMA states:

- DMA length now follows `active_count * 4` words for observed active counts.
- Last active link is `0` before SAT DMA for representative 19/23/30/32 active counts, so the shortened DMA does not require uploading stale tail entries.
- `staged_sprite_active_count == pc090oj_emitted_count` in the observed representative states.
- No dropped sprites were observed at sampled stable anchors.
- MAME visual output remains effectively parity with Build 0136.

Zero-active runtime DMA was not observed, but the source-level min-one clamp and cleared slot-0 state are present and statically verified.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-001: touched; active-count SAT DMA reduces fixed SAT DMA work in the DISPLAY_OFF-critical sprite stage, but remaining graphics/timing work is still open.
- OPEN-024: touched; PC090OJ timing/sprite bring-up context only.
- Issues opened: NONE.
- Issues closed: NONE.
- `KNOWN_FINDINGS.md`: not updated. A finding may be appropriate after Tighe/Claude accept that active-count SAT DMA is now canonical.

## STOP

STOP status: **LIMITED / evidence gap**.

The implementation, Build 0137 artifact, static proof, MAME runtime register proof, and MAME visual parity checks are complete. The only incomplete prompt item is BlastEm visual contact-sheet capture, because this installed BlastEm has no CLI screenshot path and the WSL environment lacks an available screenshot utility.
