# Cody Build 0500 — Correct native Layer A/B stage assembly

**Agent / task:** Cody, RG-023 — Correct Native Layer A/B Stage Assembly  
**Baseline:** Build 0499 candidate; Build 0492 remains the latest hardware-accepted gameplay/audio baseline  
**Candidate:** Build 0500 — **NOT ACCEPTED; Tighe hardware/visual verification pending**  
**Exact ROM-producing source:** `ef02c3643fc30654335ef3bc427ddf9ccca76a1c`

## Artifact and build state

- Normal ROM: `dist/rastan-direct/rastan_direct_video_test_build_0500.bin`
- SHA-256: `c994622994876e4a1461a09bf56f2dc39914f508b29b8976daece864fa9ed566`
- Size: 3,399,352 bytes
- Build counter: 0499 → 0500; final counter 500.
- Canonical gate: PASS; gameplay-entry gate: PASS; seven-epoch gate: PASS; automatic 30-second Genesis NTSC trace: clean.
- Opcode-replacement sites: 228 (unchanged).
- Canonical Genesis coverage: exact `0x33DEB8`; delta 0.
- Standard family: canonical, `_d`, `_s`, `_do`, `_c`, `_full_hud`, and `_invincible` all generated and configuration-verified.
- All 18 `_S1-1` through `_S6-3` selector artifacts were generated and passed the established single-selector-byte verification.
- The first build invocation detected unrelated in-progress AUDIO profile coverage and stopped before numbering. It consumed no build. Build 0500 was then produced with the committed revision-14 audio profile copied unchanged to `/tmp`; no audio source or decision file was modified or committed by RG-023.

| Build 0500 artifact | SHA-256 |
|---|---|
| normal | `c994622994876e4a1461a09bf56f2dc39914f508b29b8976daece864fa9ed566` |
| `_d` | `83167ca6670a8ac9c82cabf5da2a08dfaa0821e716b0587a2ead455a99906350` |
| `_s` | `6147718735e27731a31b7086b10869721441812cbaa6e311b96289dec128c00a` |
| `_do` | `da419e3af3d8c0ccb39d6b831bec7dc9aac66725dc1719b0c266eb2535bd669f` |
| `_c` | `b2aa2a2b70e46439f9d9c74742c8c4a5019adcb25e5c1c4ba0c96c96a3fe72eb` |
| `_full_hud` | `5f8aaf0dcdf1f269f578e20350e16f1187befd486ee0b53d6596838ec4a7de48` |
| `_invincible` | `8d8e86ad4f7006c891a03fd51b8def955f241d80467f6f38eaefa6ff946bbe05` |

## Semantic cut and retired chip tail

The retained arcade program remains authoritative for round/subround selection, map-record and selector progression, raw Layer-A destination, source/ring decisions, scroll, collision, dynamic writer timing, and scene lifecycle. The native boundary consumes that semantic state and emits final Genesis Plane A/B name words through the existing staging/VBlank publication path.

The retired tail is PC080SN C-window/name-RAM execution and chip-specific wrap/projection. A raw arcade Layer-A destination retains a 64-row logical identity; only the live 32-row window is resident in a Genesis name table. The correction therefore preserves the logical row until the native publication decision, derives the live top row from the retained arcade scroll state, and stages a write only when its logical row belongs to that live window. The retained writer still advances and keeps its original timing/state.

No PC080SN shadow, C-window image, generic chip-address translator, framebuffer, fallback renderer, NOP, RTS bypass, equal-length workaround, collision bypass, or gameplay rewrite was added. Non-gameplay callers retain their prior behavior.

## Original arcade mechanism and root cause

The maintained original-arcade MAME capture was extended to retain the stage/record/selector, Layer A/B scroll, collision buffers, raw semantic map cells, and dynamic destinations. The maintained Genesis NTSC capture was extended to retain the corresponding native state, staged names, and final VDP VRAM. A deterministic spatial verifier compares the arcade semantic cells with Genesis pattern identity/orientation and final publication.

Original castle state is:

| Subround | Initial stage | Active record | Selector | A/B Y scroll | Assembly mechanism |
|---|---:|---:|---:|---:|---|
| R1-S1 | 0 | 1 | 0 | `0x000` | direct 64-column layout |
| R1-S2 | 16 | 17 | 1 | `0x100` | direct 64-column layout; vertical row producer |
| R1-S3 | 22 | 23 | 7 | horizontal `0x160` | direct 64-column layout |
| R2-S1 | 23 | 24 | 0 | `0x000` | direct 64-column layout |
| R2-S2 | 39 | 40 | 0 | `0x100` | direct 64-column layout; vertical row producer |
| R2-S3 | 45 | 46 | 7 | horizontal | direct 64-column layout |

This disproves a castle transpose or alternate-axis hypothesis. On Build 0499, direct spatial correlation was 1963/2048 Plane-A cells and 1984/2048 Plane-B cells for R1-S2, versus only 314 and 34 under transpose. R2-S2 was 1976/2048 and 1984/2048 direct, versus 450 and 58 transposed. The apparent row-zero differences were bounded native ownership: Plane-A HUD presentation and Plane-B's resident row zero corresponding to logical row 32 after wrap.

The actual defect was in `genesistan_hook_tilemap_fg_fill`. It reduced every retained raw destination to `row & 31` before deciding whether that logical row was resident. Phase-3 animation destinations use logical rows 42–44, including destinations such as `0xC0AABC` and `0xC0AA3C`. On Build 0499 those off-window writes aliased visible rows 10–12 and overwrote valid boss-stage cells, sometimes with blanks after a LUT miss. The exact residual positions matched the observed R1-S3 and R2-S3 failures.

Build 0500 preserves the six-bit row, computes the current visible top from the authoritative scroll state at `0x00FF10B0`, and publishes only when `(logical_row - visible_top) & 63 < 32`. This corrects native projection at the semantic boundary without changing the arcade producer.

## Static and runtime validation

Static validation:

- Canonical build/gate PASS with 228 opcode sites and exact `0x33DEB8` coverage.
- Seven standard configurations generated and verified.
- All 18 subround-selector variants generated and verified.
- Address-map and manifest were regenerated by the Makefile-owned pipeline.
- `git diff --check` passed for the RG-023 source/tool change.

Runtime platforms were explicitly **original arcade MAME `rastan`** for arcade ground truth and **Genesis USA/NTSC MAME `genesis`** for the native candidate. PAL `megadriv` and BlastEm were not used.

The post-correction spatial gate passed all six native-covered subrounds:

| Variant | Plane A compared / exclusions | A pattern/orientation/LUT/VRAM errors | Plane B compared | B pattern/orientation/LUT/VRAM errors | Collision errors | Result |
|---|---:|---:|---:|---:|---:|---|
| R1-S1 | 1953 / 95 | 0 / 0 / 0 / 0 | 2048 | 0 / 0 / 0 / 0 | 0 | PASS |
| R1-S2 | 1953 / 95 | 0 / 0 / 0 / 0 | 2048 | 0 / 0 / 0 / 0 | 0 | PASS |
| R1-S3 | 1953 / 95 | 0 / 0 / 0 / 0 | 2048 | 0 / 0 / 0 / 0 | 0 | PASS |
| R2-S1 | 1953 / 95 | 0 / 0 / 0 / 0 | 2048 | 0 / 0 / 0 / 0 | 0 | PASS |
| R2-S2 | 1953 / 95 | 0 / 0 / 0 / 0 | 2048 | 0 / 0 / 0 / 0 | 0 | PASS |
| R2-S3 | 1953 / 95 | 0 / 0 / 0 / 0 | 2048 | 0 / 0 / 0 / 0 | 0 | PASS |

The comparison excludes exactly 95 Plane-A cells owned by native HUD/off-screen presentation. It verifies arcade semantic pattern identity and orientation, LUT coverage, staged-to-final VDP publication, and the captured collision buffer. The pre-correction Build 0499 gate failed only the boss-tail Layer-A cells (12 pattern errors in R1-S3; 8 in R2-S3), giving a bounded before/after result.

The established three-trial deterministic rope benchmark used Build 0500 `_invincible`:

| Build | Frames | Median |
|---|---|---:|
| accepted 0472 | 795 / 795 / 795 | 13,267.083 ms |
| 0499 candidate | 795 / 795 / 795 | 13,267.083 ms |
| 0500 candidate | 795 / 795 / 795 | 13,267.083 ms |

Result: deterministic YES; change from 0499 is 0 frames / 0.000 ms. This is an equivalent-route regression check, not a universal CPU-cycle claim.

## Palette and concurrent-work boundary

RG-023 did not modify Palette Composer, `specs/palette_decisions.json`, Andy's RG-022 scene contract, or authored colors. RG-022 marks the relevant castle/boss/Round-2 palette work missing or provisional and provides no approved `cram_asset`; the established contract therefore retains arcade conversion rather than silently substituting a Composer palette. Layout/pattern identity is now exact, but color acceptance remains Tighe's later authoring/approval task.

Concurrent Andy RG-022, audio decision-profile work, and other unrelated working-tree changes were preserved and excluded from the RG-023 commits.

## Unresolved limitations

- The exact R1-S2 impassable location was not supplied. The initial R1-S2 collision buffer is byte-identical to original arcade in the bounded capture, so there is no initial native map-to-collision divergence to patch. If the obstruction remains, Tighe should provide one paused screenshot at the blockage, player X/Y, camera A/B X/Y (or a state save), and whether the camera stops. That is sufficient to bind the relevant transition/collision location without a broad new trace.
- Boss-room initial Layer A/B assembly and collision now pass exact comparison, but no deterministic boss-defeat fixture exists and the actual boss-death-to-next-scene transition was not observed. The shared boss progression lock is not claimed fixed and remains a separate bounded assignment if hardware still reproduces it.
- Rounds 3, 5, and 6 remain RG-021 Mode B; Round 4 remains Mode A with content absent. RG-023 did not convert Rounds 3–6.
- Real-hardware visual/gameplay acceptance is pending.

## Files changed

ROM-producing source/tool commit `ef02c3643fc30654335ef3bc427ddf9ccca76a1c`:

- `apps/rastan-direct/src/tilemap_hooks.s`
- `tools/mame/run_build0421_segment0_semantic_capture.sh`
- `tools/mame/scripts/arcade_subround_cheat_probe.lua`
- `tools/mame/scripts/build0421_segment0_semantic_capture.lua`
- `tools/mame/verify_native_stage_spatial.py`

Generated address maps, manifests, symbols, objects, disassembly, counter state, and MAME logs were refreshed by the canonical build. This report, the RG-023 index, and `AGENTS_LOG.md` are bookkeeping only and are not the ROM-producing source.

## USER MUST VERIFY

On real Genesis hardware, test Build 0500 normal ROM and the named selector variants:

1. `_S1-2`: castle Layer A/B orientation, scrolling, collision, and the known impassable location. If still blocked, capture the minimal location/state evidence listed above.
2. `_S1-3`: complete boss-room art remains stable during live animation; defeat the boss and report whether the original transition actually reaches the next scene.
3. `_S2-1`, `_S2-2`, and `_S2-3`: Round-2 Layer A/B orientation and scrolling remain coherent, especially the S2 vertical-scroll castle and boss-tail animation.
4. Normal R1-S1: title/READY/gameplay, HUD, ropes/waterfall, death/Continue, sprites, collision, music, and scroll remain unchanged.
5. Treat colors separately: identify palette discrepancies for RG-022 authoring; do not reject proven spatial assembly solely because provisional palettes remain.

## Status

RG-023 implementation and automated validation: **COMPLETE**.  
Build 0500 hardware acceptance: **PENDING TIGHE**.  
Build 0500 accepted baseline: **NO**.  
Boss progression fix claimed: **NO**.  
Rounds 3–6 conversion started: **NO**.  
STOP.
