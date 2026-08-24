# Cody Build 0312 Round-1 Phase-1 Plane-A Completion Checkpoint

## Status

Build 0312 is a bounded production checkpoint for the first proven Build 0311
Plane-A publication defect. It is **not** a claim that all of Round 1 Phase 1 is
visually complete. Automated gates pass; real Genesis hardware verification of
the corrected transition and the remaining records is still required.

### Visual-attribution correction

The original audit incorrectly used the green color of the Section-2 Plane-A
cave walls as evidence for a wrong map/tile source. Full-resolution review and
the user's hardware observation establish that the cave-wall **tile geometry is
right but its palette is wrong**. The visible issue is therefore a Plane-A
palette/attribute mismatch, not visual proof of a wrong map source.

The missing `segment_index * 0x40` term remains an independently proven static
helper defect and remains the sole scope of Build 0312. The current recording
does not prove that this static defect caused the visible green cave walls, nor
does it prove that Build 0312 corrects their palette.

## Baseline And Artifact

- Accepted input baseline: Build 0311.
- Build 0311 ROM: `dist/rastan-direct/rastan_direct_video_test_build_0311.bin`.
- Build 0311 SHA-256: `a3a1e32beba2e36a5ef17d7dcf61e1da089520740bfeaf06f1f591a677cc362c`.
- Produced checkpoint: Build 0312.
- Build 0312 ROM: `dist/rastan-direct/rastan_direct_video_test_build_0312.bin`.
- Build 0312 SHA-256: `c57ce5d9ad6294aed6671ee736d584a31b7b3083c4f9e1fdd0f1693e3f236d28`.
- Size: 1,670,840 bytes.
- Counter: 311 -> 312.
- Rolling ROM is byte-identical to the numbered artifact.

## Architecture Compliance

The retained semantic state is the arcade map-stream decision: selector,
logical row, live segment index, source group, descriptor table, scroll state,
and original map data. The replaced chip-specific tail directly resolves the
arcade tile to the current resident Genesis slot and stages the final Plane-A
name word. Build 0312 does not add a software PC080SN, virtual C-window/name RAM,
full-map/tall-buffer projection, per-frame residency, cache, LRU, or generic
chip-address translation.

## Hardware Video Audit

Source:
`states/screenshots/Build_0311_Playthough_Round_1_Phase_1_crashes_Phase_2.mp4`

The recording is 236.1254 seconds, 1,920x1,080 H.264, 7,085 source frames at an
effective 30.0052 fps. The project-owned deterministic extraction workflow is:

- `analysis/build0311_phase1_hardware_visual_audit/extract_storyboard.sh`
- `analysis/build0311_phase1_hardware_visual_audit/make_storyboard.py`

It produced:

- 945 baseline JPEGs at 4 fps;
- 1,219 dense JPEGs at 12 fps across nine bounded transition windows;
- 2,164 selected frames total;
- `metadata/frames.json`, `metadata/dense_frames.json`,
  `metadata/capture.json`, and `metadata/section_audit.json`;
- machine-readable `issues.json`;
- filterable chronological `index.html`;
- `comparison.html`, comparing the arcade-derived record-1 map, the Build 0311
  hardware frame, and the proven descriptor-formula divergence.

The extraction scripts use `ffmpeg -nostdin`, clear only their own generated
frame outputs, and can regenerate the storyboard without consuming names from
standard input or retaining stale frames.

### Dense Windows

| Window | Start | Duration | Rate |
|---|---:|---:|---:|
| gameplay entry | 17.50 s | 3.00 s | 12 fps |
| Section 2 / record 1 descent | 27.25 s | 17.25 s | 12 fps |
| Section 2 / record 1 exit | 46.50 s | 4.00 s | 12 fps |
| vertical transition 1 | 56.50 s | 17.00 s | 12 fps |
| mid-phase transition 1 | 89.00 s | 12.00 s | 12 fps |
| mid-phase transition 2 | 117.00 s | 12.00 s | 12 fps |
| late-phase transition 1 | 145.00 s | 12.00 s | 12 fps |
| late-phase transition 2 | 175.00 s | 12.00 s | 12 fps |
| fortress approach | 202.00 s | 12.00 s | 12 fps |

## Phase-1 Section Audit

The complete video was sampled chronologically, so every record from 0 through
15 is visually represented. Section 2 / record 1 is visually clear enough to
classify the cave-wall palette mismatch, but it is not synchronized to runtime
WRAM/VDP state and therefore cannot classify a source-state divergence. A video
timestamp alone is not treated as an exact record, scroll, or map-cell identity.

| Section | Record | Hardware classification | Evidence status |
|---:|---:|---|---|
| 1 | 0 | UNCERTAIN | Entry appears coherent; no synchronized all-cell comparison. |
| 2 | 1 | WRONG PALETTE in Build 0311 | Cave-wall tile geometry is right; palette/attribute output is wrong. Separate static source-rule defect corrected in Build 0312. |
| 3 | 2 | UNCERTAIN | Chronologically sampled; hardware cell audit pending. |
| 4 | 3 | UNCERTAIN | Rope/waterfall overlap package retained; hardware audit pending. |
| 5 | 4 | UNCERTAIN | Rope/waterfall overlap package retained; hardware audit pending. |
| 6 | 5 | UNCERTAIN | Chronologically sampled; exact state unresolved. |
| 7 | 6 | UNCERTAIN | Chronologically sampled; exact state unresolved. |
| 8 | 7 | UNCERTAIN | Chronologically sampled; exact state unresolved. |
| 9 | 8 | UNCERTAIN | Chronologically sampled; exact state unresolved. |
| 10 | 9 | UNCERTAIN | Chronologically sampled; exact state unresolved. |
| 11 | 10 | UNCERTAIN | Epoch package gate passes; hardware audit pending. |
| 12 | 11 | UNCERTAIN | Epoch package gate passes; hardware audit pending. |
| 13 | 12 | UNCERTAIN | Epoch package gate passes; hardware audit pending. |
| 14 | 13 | UNCERTAIN | Chronologically sampled; exact state unresolved. |
| 15 | 14 | UNCERTAIN | Chronologically sampled; exact state unresolved. |
| 16 | 15 | UNCERTAIN | Fortress package gate passes; hardware audit pending. |

No section is certified visually correct by this checkpoint. That distinction
prevents automated residency success from being misreported as complete real-
hardware map, scroll, and palette correctness.

## Section 2 / Record 1 Deep Dive

### Observable Video Facts

- Gameplay begins at approximately 18 seconds.
- A right-edge palette mismatch is visible at 27.75 seconds.
- By 29.25 seconds, the expected cave-wall tile geometry occupies a large
  Plane-A region but is rendered in the wrong green/cream palette.
- The dense evidence frame is
  `frames/dense/section02_record01_descent/frame_000025.jpg`.
- The path is selector 0 with a scripted vertical camera pan; the image alone
  does not prove a source-map, selector, or orientation failure.

### Authoritative Arcade Contract

For a logical entering row, the original map-stream descriptor entry is:

```text
E = strip_src_table[row_segment]
  + segment_index * 0x40
  + source_group * 4
```

The live `segment_index` is the word at A5+0x013E, which maps to Genesis-WRAM
`0x00FF013E`. The `0x40` term advances one 16-entry descriptor segment. This
contract is independently documented in
`docs/arcade_reference/pc080sn/map_stream_format.md` and
`docs/design/Andy_build0246_plane_a_arbitrary_row_source_proof.md`.

### Build 0311 Divergence

`.Lplane_a_publish_logical_row_native` reconstructed only:

```text
E_build0311 = strip_src_table[row_segment] + source_group * 4
```

Thus, once the camera requested an entering row from a nonzero live segment,
the helper's descriptor calculation omitted required semantic state. That is an
exact static defect before tile-code/LUT/slot/name-word production. However,
the hardware video has no synchronized runtime cell trace, and the observed
cave-wall tile geometry is right. The visible green/cream coloring must not be
presented as proof that this arithmetic defect selected the wrong tile family.

### Build 0312 Correction

In `apps/rastan-direct/src/tilemap_hooks.s`, the helper now inserts the missing
semantic term before adding the source-group offset:

```asm
move.w  0x013E(%a5), %d1
lsl.w   #6, %d1
adda.w  %d1, %a0
adda.w  %d0, %a0
```

Generated runtime code proves the term is materialized:

| runtime_genesis_pc | Instruction | Meaning |
|---|---|---|
| `0x000707D6` | `lea 0x00070882(pc),a0` | select row-segment source table |
| `0x000707DA` | `movea.l (a0,d1.w),a0` | load row-segment base |
| `0x000707DE` | `move.w 0x013E(a5),d1` | load live segment index |
| `0x000707E2` | `lsl.w #6,d1` | multiply by `0x40` |
| `0x000707E4` | `adda.w d1,a0` | select live segment |
| `0x000707E6` | `adda.w d0,a0` | add source-group entry offset |

The common helper is reached by the native entering-row publishers at
runtime_genesis_pc `0x000706A4` (pan up) and `0x000706FC` (pan down). The helper
starts at runtime_genesis_pc `0x0007075C`.

### Required Classification

| Question | Result |
|---|---|
| Pattern resident? | YES for all required Build 0312 packages; no compiler drops. |
| Correct physical slot for selected code? | YES by full-LUT package gates; exact runtime code/slot at 29.25 seconds was not captured. |
| Observed cave-wall tile geometry correct? | YES for the cited hardware example. |
| Map coordinate/source transform correct in Build 0311? | Static helper formula is wrong; the video does not prove its per-cell visual consequence. |
| Scroll-X publication defect proven? | NO separate divergence proven. |
| Scroll-Y entering-row publication correct in Build 0311? | Static descriptor calculation omitted the segment term; synchronized runtime consequence not captured. |
| Selector/orientation defect proven? | NO; selector 0 is valid at this transition. |
| Visible issue class | Plane-A palette/attribute mismatch; exact name-word-vs-CRAM boundary unresolved. |
| Static issue class | Descriptor arithmetic omission, independently corrected in Build 0312. |
| Capacity failure? | NO. |

The exact expected world-cell coordinates, expected code list, and actual
Genesis code/slot list at 29.25 seconds remain `UNKNOWN` because the real-
hardware recording has no synchronized WRAM/scroll dump. The deterministic
record-1 arcade map is rendered in `comparison.html`, but inventing exact cell
IDs from image alignment would violate address/state discipline. The static
descriptor formula divergence is exact; its causal relationship to this
particular visual frame is not established.

## Static Map To Runtime Publisher Contract

For each native entering-row publication:

1. Retain the arcade logical row and split it into row segment and row-in-strip.
2. Use source group and live `segment_index` to resolve descriptor entry `E`
   with the authoritative formula above.
3. Read the original descriptor/map source selected by `E`.
4. Derive source column from arcade scroll-X semantics and the destination
   column being exposed.
5. Read the original arcade tile code and attributes.
6. Resolve that code through the active compiler-owned epoch/overlap LUT.
7. Form the final Genesis Plane-A name word with the original semantic
   palette/flip/priority attributes.
8. Stage it at physical Plane-A row `(logical_row & 31)` and the corresponding
   ring column for VBlank commit.

Build 0312 changes step 2 only. It does not change scroll publication, physical
ring dimensions, slot ownership, VBlank commit, or the retained selector path.

## Residency And Locked Components

- Fixed Plane B: 854 codes, slots 1..854, zero drops, unchanged.
- Plane A: slots 855..1338, capacity 484, zero drops for all records 0..15.
- Seven epoch counts retained: 282, 333, 444, 368, 483, 433, 349.
- Native PC090OJ sprite allocation: base slot 1339, 49 16x16 cells, unchanged.
- Build 0311 overlap packages retained: rope transition peak 394 and waterfall
  transition peak 479, both within 484, with zero missing patterns, slot
  collisions, moved retained patterns, or handoff omissions.
- Per-frame pattern DMA, runtime allocator, search, LRU, and visibility scan:
  none.
- Plane-A drops: 0. Plane-B drops: 0.

## Palette Audit

The Phase-1 palette audit is **not complete**, but one visual fact is now clear:
the cited cave-wall tiles have the right geometry and the wrong palette. The
recording does not distinguish wrong Plane-A name-word palette bits from wrong
CRAM contents/ownership or palette-transition timing. Build 0312 changes no
palette implementation, route, CRAM staging, or name-word attribute logic.

`specs/palette_decisions.json` remains the sole registry. It currently contains
no Plane-A decision authorizing a route change. Therefore:

- observed wrong Plane-A palette output: YES;
- proven wrong palette routes: 0;
- proven wrong Plane-A name-word palette bits: 0;
- proven stale palette transitions: 0;
- palette fixes in Build 0312: none;
- required follow-up: compare Build 0312 hardware colors after the source-map
  correction against arcade evidence before changing any Palette Decision ID.

## Secondary Enemy-Density Audit

Investigation is not complete and no enemy code changed. The video contains
nearby same-family enemies, but video alone cannot distinguish multiple logical
actor slots from valid multi-cell composites or duplicate SAT emission.

- Arcade logical spawn count: unavailable for a synchronized scope.
- Genesis logical spawn count: unavailable for a synchronized scope.
- True duplicate logical spawns: not proven.
- Renderer-only duplicates: not proven.
- First divergence/root cause: OPEN.

This remains a separate bounded analysis target so it cannot contaminate the
Plane-A acceptance result.

## Validation

### Canonical Build Gate

`GATE_PASS`: PASS. Build 0312 retains 227 opcode replacements and the accepted
canonical coverage boundary. The numbered and rolling ROMs match byte-for-byte.

### Gameplay Entry Gate

Trace: `states/traces/build0312_gameplay_entry_gate_20260824_114013/`

- result PASS over 564 external frames;
- credit/start/ROUND 1 READY/fixed Plane B/record-0 Plane A/gameplay/player
  control all PASS;
- 240 required post-entry frames completed;
- active record reached 1;
- address errors 0, bus errors 0, illegal instructions 0, crash entries 0;
- stack pointer valid.

### Phase-1 Package Gate

Trace: `states/traces/build0312_phase1_epoch_gate_20260824_114015/`

- result PASS;
- seven epochs tested through records 0, 3, 4, 10, 11, 12, and 15;
- full Plane-A LUT checks PASS;
- full fixed Plane-B LUT checks PASS.

This proves package installation and LUT coverage, not complete visual map or
palette correctness across every hardware section.

### Standard MAME Smoke

Trace: `states/traces/rastan_direct_video_test_build_0312_mame_30s_20260824_114025/`

- 1,798 external frames;
- no unique unmapped memory addresses;
- no new exception regression observed.

## Deferred Evidence

- The user-observed Phase-2 crash is outside this task and was not changed.
- Exact synchronized cell identities for later Phase-1 transitions remain open.
- Palette correctness remains open pending Build 0312 hardware comparison.
- Enemy-density provenance remains open.

## Tighe Hardware Test

1. Load Build 0312.
2. Play all of Round 1 Phase 1.
3. Check the Section 2 first cave/drop carefully.
4. Check every horizontal-to-vertical and vertical-to-horizontal transition for
   wrong Plane-A cells.
5. Confirm rope and waterfall graphics remain intact.
6. Compare exterior, waterfall, cave, bridge, and fortress-approach colors with
   the arcade version.
7. Report the first remaining wrong-tile location with a screenshot or video
   timestamp, if any.
8. Record enemy-density observations separately from Plane-A acceptance.

## Next Useful Build Boundary

Build 0313 is not pre-authorized by this report. If Build 0312 fixes the first
source-segment corruption and colors remain wrong, the next bounded task is
Plane-A palette provenance tied to affected Palette Decision IDs. If a map error
remains first, the next task is a synchronized trace of that one transition to
identify its exact expected/actual map cells before another production change.

## Files Changed

Production source:

- `apps/rastan-direct/src/tilemap_hooks.s`

Generated build artifacts and manifests were refreshed by the normal Makefile,
including `apps/rastan-direct/out/`, `build/rastan-direct/`,
`build/genesis_postpatch.disasm.txt`, `build/rom_inventory.json`, and the rolling
ROM. No spec, Plane-B source, sprite source, collision, palette, audio, or
Phase-2 source was changed.

Analysis/documentation:

- `analysis/build0311_phase1_hardware_visual_audit/`
- `docs/design/Cody_build0312_round1_phase1_plane_a_completion.md`
- `AGENTS_LOG.md`
