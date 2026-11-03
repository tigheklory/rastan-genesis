# Cody - Build 0124 Final Composite Black Cover Attribution

**Date:** 2026-07-01
**Build:** 0124
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0124.bin`
**ROM SHA256:** `f5935113ef4ab8ea231d4e31764b96a36c8bd2fe246846a2ca929facdfccd921`
**Type:** Evidence / attribution only
**Scope:** Existing Build 0124 ROM and existing video evidence. No source/spec/tool/Makefile/ROM/build/invariant changes. No bookmark. No implementation. No fix design.

Address labels used below: `runtime_genesis_pc`, `genesis_rom_offset`, `arcade_pc`, `Genesis-WRAM`, `VRAM address`, and `HW_ADDRESS`. No new arcade-to-Genesis code correlation was required for this task; `build/rastan-direct/address_map.json` was loaded in Phase 0, and no arithmetic offset mapping is used as proof.

## Phase 0

Read for this task: `RULES.md`, `ARCHITECTURE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, latest `AGENTS_LOG.md`, `docs/design/Cody_pc090oj_blank_bitset_unmapped_guard_implementation.md`, `docs/design/Andy_pc090oj_blank_unmapped_filter_audit.md`, `docs/design/Cody_build0123_pc090oj_transparent_pen_black_overdraw_evidence.md`, `docs/design/Cody_pc090oj_object_ram_phase1_implementation.md`, `docs/design/Andy_build0120_window_plane_coverage_design.md`, and `docs/design/Andy_pc090oj_object_ram_to_genesis_sat_architecture.md`.

Classification: **EXTENDING** OPEN-001 / OPEN-024 with evidence-only attribution. OPEN-023 is context for the Window layer; OPEN-006 is palette context; OPEN-015 is not used because no exception-screen fields are analyzed. No contradiction detected.

User-confirmed premise accepted: Exodus separated views show Plane A and Plane B are complete/correct. This task does **not** re-prove Plane A/B completeness; it asks what final-composite cover/mask makes the complete planes appear black/partially covered in the video.

## Evidence Artifacts

Trace directory:

- `states/traces/build_0124_final_composite_black_cover_attribution_20260701_170732`

Video inspected:

- `states/screenshots/mame_genesis_build_124.mp4`

Extracted video frames:

| File | Source video frame | Time | Observation |
|---|---:|---:|---|
| `states/traces/build_0124_final_composite_black_cover_attribution_20260701_170732/video_frames/video_frame_282_covered.png` | 282 | 9.400s | story page lower portion visible; upper/top portion black/covered |
| `states/traces/build_0124_final_composite_black_cover_attribution_20260701_170732/video_frames/video_frame_283_reveal.png` | 283 | 9.433s | full story page visible/revealed |
| `states/traces/build_0124_final_composite_black_cover_attribution_20260701_170732/video_frames/video_frame_289_highscore_covered.png` | 289 | 9.633s | high-score transition / covered frame |
| `states/traces/build_0124_final_composite_black_cover_attribution_20260701_170732/video_frames/video_frame_369_highscore_fuller.png` | 369 | 12.300s | high-score fuller frame |
| `states/traces/build_0124_final_composite_black_cover_attribution_20260701_170732/video_frames/story_transition_contact_sheet.png` | 278..286 | 9.267s..9.533s | compact visual sequence showing covered story frames followed by reveal |

Runtime evidence generated:

- `states/traces/build_0124_final_composite_black_cover_attribution_20260701_170732/build124_cover_capture_light.lua`
- `states/traces/build_0124_final_composite_black_cover_attribution_20260701_170732/build124_cover_capture_light.log`
- `states/traces/build_0124_final_composite_black_cover_attribution_20260701_170732/build124_cover_analysis.md`
- `states/traces/build_0124_final_composite_black_cover_attribution_20260701_170732/build124_cover_analysis.json`
- Binary dumps named `light_frame_282_*`, `light_frame_283_*`, `light_frame_289_*`, and `light_frame_369_*`

MAME command style: read-only Genesis driver execution of the existing Build 0124 ROM with `-video none`, `-sound none`, `-nothrottle`, `-seconds_to_run 13`, and an `-autoboot_script` that dumped memory/VDP-accessible regions. No input was injected.

## Video Observation

The video has a clear final-composite transition:

- Frames 278..282: lower story content is visible, but the upper page is black/covered.
- Frame 283 onward: the full story page is visible.
- The transition is between source video frame 282 and source video frame 283.

The mouse pointer/host cursor visible in the video frames is a host overlay/capture artifact and is ignored. It is not treated as sprite, VDP, Window, tilemap, scroll, or game-state evidence.

## Nominal Runtime Snapshot Pair

The Lua capture dumped nominal emulator frames 282 and 283 in a separate no-input Build 0124 run. The state matches the story/attract state class, but exact wall-clock alignment to the externally captured video can still have a small offset. Therefore these snapshots are treated as strong corroborating evidence, not as a substitute for a debugger-synchronized video frame capture.

Frame 282 capture line:

```text
CAPTURE frame=282 pc=071F5A s0=0000 s2=0001 s4=0002 scroll=0000/0000/0000/0000 dirty pal=00 bg=00000000 fg=00000000 spr=00000000 active=0004 counts ctrl=0001 sprctrl=0060 mirror=0001 decoded=0100 zero=00FC blank=0000 unmapped=0000 offscreen=0000 drawable=0004 emitted=0004 dropped=0000
```

Frame 283 capture line:

```text
CAPTURE frame=283 pc=071F5E s0=0000 s2=0001 s4=0002 scroll=0000/0000/0000/0000 dirty pal=00 bg=00000000 fg=00000000 spr=00000000 active=0004 counts ctrl=0001 sprctrl=0060 mirror=0001 decoded=0100 zero=00FC blank=0000 unmapped=0000 offscreen=0000 drawable=0004 emitted=0004 dropped=0000
```

Key 282->283 diff result:

| Region | 282->283 diff |
|---|---:|
| `Genesis-WRAM 0xFF0000..0xFF007F` | one word only: byte offset `0x2C` changed `0x0090 -> 0x008F` |
| dirty/scroll block `0xFF4000..0xFF4019` | 0 byte diffs |
| `staged_bg_buffer` `0xFF401A..0xFF5019` | 0 byte diffs |
| `staged_fg_buffer` `0xFF501A..0xFF6019` | 0 byte diffs |
| `staged_sprite_sat` `0xFF6104..0xFF6383` | 0 byte diffs |
| `staged_sprite_descriptor_table` `0xFF6384..0xFF6743` | 0 byte diffs |
| `pc090oj_object_ram` `0xFF674A..0xFF6F49` | 0 byte diffs |
| `pc090oj_counts` `0xFF6F4A..` | 0 byte diffs |

Interpretation: the covered->revealed video transition is **not accompanied by a durable change** in the captured staging buffers, sprite mirrors, object RAM, scroll staging, dirty flags, or PC090OJ counters. The only captured state change is the normal countdown/timer word at `Genesis-WRAM 0xFF002C`.

## Per-frame Counts

From `states/traces/build_0124_final_composite_black_cover_attribution_20260701_170732/build124_cover_analysis.md`:

| Frame | staged BG nonzero words | staged FG nonzero words | staged descriptor nonzero words | staged SAT nonzero words | PC090OJ object RAM nonzero words | decoded | drawable | emitted | dropped |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 282 | 168 | 146 | 0 | 0 | 480 | 0x0100 | 0x0004 | 0x0004 | 0x0000 |
| 283 | 168 | 146 | 0 | 0 | 480 | 0x0100 | 0x0004 | 0x0004 | 0x0000 |
| 289 | 168 | 146 | 0 | 0 | 480 | 0x0100 | 0x0004 | 0x0004 | 0x0000 |
| 369 | 168 | 146 | 0 | 0 | 480 | 0x0100 | 0x0004 | 0x0004 | 0x0000 |

## Sprite / SAT Attribution

Observable facts:

- `pc090oj_object_ram` is nonzero: 480 nonzero words.
- PC090OJ counters are stable across all captured frames: `decoded=0x0100`, `drawable=0x0004`, `emitted=0x0004`, `dropped=0x0000`.
- `staged_sprite_descriptor_table` is all zero at frames 282/283/289/369.
- `staged_sprite_sat` is all zero at frames 282/283/289/369.
- The accessible `true_vdp_sat_f800` dump through MAME's `:gen_vdp` `videoram` path is also all zero, but see the VDP-access limitation below.

Interpretation:

- The four PC090OJ `emitted_count` candidates do **not** leave any nonzero staged descriptor or staged SAT entry at the captured frame points.
- Therefore `emitted_count=4` is not proof of a visible Genesis SAT cover in these frames. It records scanner/candidate/emission-path activity; the final staged sprite structures are zero.
- A persistent sprite/SAT black cover is **not supported** by the captured staged data for frames 282/283.

Classification for sprites as the black cover source: **unlikely / not supported for this specific covered->revealed story transition**. OPEN-024 remains relevant to sprite correctness generally, but the final-composite black cover is not explained by the captured staged SAT state.

## Window Attribution

Static VDP register setup from `apps/rastan-direct/src/vdp_comm.s`:

| Register | Value | Meaning |
|---|---:|---|
| Reg 3 Window base | `0x3C` | Window nametable base `VRAM address 0xF000` |
| Reg 17 Window X | `0x00` | SGDK-equivalent Window-off horizontal value, pos=0 |
| Reg 18 Window Y | `0x00` | SGDK-equivalent Window-off vertical value, pos=0 |

Prior source: `docs/design/Andy_build0120_window_plane_coverage_design.md` establishes that `reg17=0x00 / reg18=0x00` is the SGDK-canonical Window-off state, not full-screen Window coverage. No source path writes regs 17/18 after boot.

Runtime limitation: MAME Lua exposed `:gen_vdp` items named `m_regs`, `m_cram`, and `m_vsram`, but did not expose a normal `vdp.state` object or readable CRAM/VSRAM/register API in this workflow. The direct register values are therefore not dynamically read here; the exact-frame Window classification rests on static boot setup + no post-boot Window X/Y writer + the prior SGDK semantics audit.

Classification for Window as the black cover source: **irrelevant / exonerated**. Window X/Y are the known off values, and no current evidence supports a visible Window-plane cover.

## Scroll / Clipping Attribution

Captured scroll staging for frames 282/283/289/369:

| Frame | staged_scroll_x_bg | staged_scroll_x_fg | staged_scroll_y_bg | staged_scroll_y_fg |
|---:|---:|---:|---:|---:|
| 282 | 0 | 0 | 0 | 0 |
| 283 | 0 | 0 | 0 | 0 |
| 289 | 0 | 0 | 0 | 0 |
| 369 | 0 | 0 | 0 | 0 |

The H-scroll region read through MAME's exposed `videoram` path also returned all zero words, but the direct VRAM read path is not treated as authoritative. The WRAM scroll staging is authoritative for the commit inputs.

Classification for scroll/clipping as the cover source: **not supported**. There is no captured scroll-state change at the covered/revealed boundary.

## VDP Dump Limitation

MAME's `:gen_vdp` Lua device exposes only one readable address space named `videoram` in this setup. Reads from that space at `0xC000`, `0xE000`, `0xF000`, `0xF800`, and `0xFC00` returned zeros. That conflicts with the external video and user-confirmed Exodus Plane A/B evidence, so these MAME Lua `videoram` reads are **not** used as proof that VDP Plane A/B/Window/SAT are empty.

The introspection log is `states/traces/build_0124_final_composite_black_cover_attribution_20260701_170732/introspect_vdp_build124.log`. It shows:

- only `vdp.spaces.videoram` is exposed as a space;
- `vdp.items` lists internal `m_regs`, `m_cram`, `m_vsram`, and `m_vram` items;
- `vdp.state` is nil;
- no direct CRAM/VSRAM/register value accessor was available through the current Lua script.

Therefore:

- **Final composite screenshots:** captured from the source video.
- **VDP registers:** interpreted from source/static register setup and prior Window semantics audit; not directly read from MAME Lua.
- **CRAM/VSRAM:** not directly dumped by this workflow.
- **Plane A/B/Window/true SAT binary dumps:** files are present, but marked non-authoritative because the exposed MAME `videoram` path reads zeros for visible content.
- **WRAM staging, sprite mirrors, object RAM, counters, scroll staging:** authoritative through `:maincpu` program-space reads.

## Classification Matrix

| Candidate cover source | Classification | Evidence |
|---|---|---|
| Window plane | **Irrelevant / exonerated** | Reg17/18 are Window-off values by prior SGDK semantics audit; no post-boot Window X/Y writer |
| Staged sprite/SAT cover | **Unlikely / not supported** | staged descriptor table and staged SAT are all zero across captured frames; counters alone do not produce visible SAT |
| PC090OJ object RAM itself | **Not a final compositor layer** | object RAM has candidates, but final staged descriptor/SAT is zero |
| Scroll/clipping | **Not supported** | all staged scroll values zero and unchanged |
| Plane A/B data missing | **Out of scope / contradicted by user premise** | user-confirmed Exodus separated planes are complete/correct |
| Persistent VDP-layer mask | **Not supported by captured state** | 282->283 durable state is unchanged except `Genesis-WRAM 0xFF002C` timer decrement |
| Temporal final-composite / capture-boundary transition | **Most likely current attribution** | video shows covered->reveal transition, but nominal frame-end staging/SAT/scroll/counters do not change; cover does not persist into captured state |
| Exact emulator-frame alignment issue | **Possible** | video frame numbers come from an external capture; Lua frame count is a separate run, albeit same ROM/no-input and same state class |

## Conclusion

The Build 0124 final-composite black cover in the story transition is **not explained by a persistent Window, sprite/SAT, scroll, staging, or object-RAM state difference** in the captured nominal frame pair. The only 282->283 durable runtime-memory delta is the normal `Genesis-WRAM 0xFF002C` timer decrement.

The safest attribution is: **the black cover is a transient final-composite/capture-boundary phenomenon, not a persistent game layer currently visible in the captured runtime state.** It is visible in the source video for frames 278..282 and gone by frame 283, but the surviving frame-end state does not name a cover layer.

This does **not** prove the visual artifact is harmless or solved. It means a fix should not be aimed at Window-off, sprite-SAT suppression, or scroll changes based on this evidence alone. The next useful evidence pass would be synchronized debugger-side capture from an emulator/tool that can read actual VDP internal registers/CRAM/VSRAM/VRAM at the same final-composite video frame, or an Exodus-side capture that records the four plane viewers and final composite at frame 282 and frame 283 in the same run.

## OPEN / KNOWN_FINDINGS Impact

- OPEN-001: still open; final-composite graphics artifact remains under investigation.
- OPEN-024: remains open for PC090OJ correctness, but this specific black-cover transition is not supported by staged SAT evidence.
- OPEN-023: context only; Window remains off/inert for this attribution.
- OPEN-015: not touched.
- CLOSED issues: none touched.
- New issues opened: none.
- KNOWN_FINDINGS impact: Option A, no update. This is an evidence/attribution pass with a VDP-read limitation, not a settled durable mechanism.

## STOP Status

STOP triggered: **NO**. Evidence was captured and documented. Limitation recorded: direct CRAM/VSRAM/VDP-register/live-VRAM reads were not available through the MAME Lua path used here, so those fields are not over-claimed.
