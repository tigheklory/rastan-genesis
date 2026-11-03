# Cody - Build 0092 No-Input Graphics Video Evidence

**Date:** 2026-06-20
**Build:** 0092
**Video inspected:** `states/screenshots/build_92/build_92.mp4`
**Prompt path note:** the requested `screenshots/build_92/build_92.mp4` path was not present; the video was found under the project screenshot convention at `states/screenshots/build_92/build_92.mp4`.
**Classification:** no-input runtime video evidence capture / documentation only.
**Scope:** No source, spec, tool, Makefile, ROM, invariant, bookmark, OPEN-015, or Start-C-A changes. No runtime probing beyond extracting and inspecting the supplied video.

## Video Metadata

- Resolution: `5118x1396`
- Video frame rate: `30 fps`
- Duration: `30.966633 s`
- Video frames: `928`

## Extracted Evidence

Representative full-frame captures:

- `states/screenshots/build_92/extracted/build_92_first_stable_001s.png`
- `states/screenshots/build_92/extracted/build_92_sample_005s.png`
- `states/screenshots/build_92/extracted/build_92_sample_010s.png`
- `states/screenshots/build_92/extracted/build_92_mid_015_5s.png`
- `states/screenshots/build_92/extracted/build_92_sample_020s.png`
- `states/screenshots/build_92/extracted/build_92_sample_025s.png`
- `states/screenshots/build_92/extracted/build_92_late_030s.png`

Focused main VDP image crops:

- `states/screenshots/build_92/extracted/build_92_main_image_inner_crop_010s.png`
- `states/screenshots/build_92/extracted/build_92_main_image_inner_crop_015_5s.png`
- `states/screenshots/build_92/extracted/build_92_main_image_inner_crop_030s.png`

## No-Input Behavior

The no-input run remains stable across the inspected video. No exception screen appears in this video. The early visible output is mostly black; by the 10s sample the main VDP image window has settled into a sparse horizontal row of colored dots. The same sparse-dot pattern remains visible at the mid-run and late-run samples.

## Visible Graphics Failure

The video does not show proper title, attract, or game-scene graphics. The main image window is overwhelmingly black with only a few dotted/horizontal colored artifacts. There is no meaningful tilemap scene, no recognizable title text, and no meaningful sprite display. The VDP plane viewers show sparse patterned blocks rather than a coherent committed game scene.

Tighter main-image crop measurements support the visual read:

| Sample | Non-black pixels (>24) | Bright pixels (>80) |
|---|---:|---:|
| `10s` | `1158` / `1699740` (`0.068128%`) | `388` (`0.022827%`) |
| `15.5s` | `1179` / `1699740` (`0.069364%`) | `395` (`0.023239%`) |
| `30s` | `1187` / `1699740` (`0.069834%`) | `398` (`0.023415%`) |

Assessment: no clear graphics improvement is visible versus the prior sparse/dotted-output observations. The no-input state is stable, but the graphics-output problem remains primary.

## Start-C-A Crash Boundary

The Start/C/A crash is not present in this video. Tighe separately reported out of band that pressing Start, then C, then A can crash to an exception screen. That input-triggered crash is documented here only as a user-reported separate observation. It was not reproduced, analyzed, or pursued in this task.

Start/C/A crash analysis is deferred. The next implementation focus should remain the stable no-input graphics-output failure unless Tighe/Claude explicitly reprioritize the input-triggered crash.

## OPEN / KNOWN_FINDINGS Impact

OPEN-016 status: unchanged; remains open. Build 0092 appears stable before input, but the visual output is still not correct.

KNOWN_FINDINGS impact: Option A - no update from this evidence capture alone. The video corroborates the continuing graphics-output failure but does not establish a new durable mechanism or fix locus.

## STOP

STOP triggered: **NO**.
