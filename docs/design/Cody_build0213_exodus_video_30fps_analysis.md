# Cody - Build 0213 Exodus 30-FPS Video and Debug-Window Analysis

**Date:** 2026-07-19  
**Type:** Runtime video evidence extraction / visual-debug-window analysis only  
**Source video:** `states/screenshots/exodus_build_213.mp4`  
**Video identity:** Exodus running Genesis Build 0213/256, not MAME/original arcade  
**Build 0213 SHA256 from task prompt:** `4cb766d5866dd2950e8b177c961549e3819bc98c5ecbddd56c2f6d3050d6316b`  
**Scope:** No source/spec/tool/Makefile/invariant/ROM/build-counter/numbered-artifact changes. No build. No emulator rerun. Full supplied video inspected.

## Phase 0

Classification: **EXTENDING**. This video extends OPEN-017 / OPEN-024 visual evidence after the Build 0213 lizard vertical-alignment candidate. Relevant priors loaded: KF-010/KF-015 plane/scroll staging context, KF-024/OPEN-017 gameplay rendering context, KF-064/KF-065 lizard actor/combat context, KF-066 gameplay HUD suppression + lizard palette line-0 route, and KF-067 Build 0213 lizard vertical-alignment evidence. Rediscovery-hazard findings touched: gameplay VDP/PC080SN/PC090OJ rendering and lizard pipeline findings; no contradiction of CONFIRMED/STRONG findings detected.

Open issues touched: OPEN-017 and OPEN-024. OPEN-001 is broad context. No issue was opened or closed. KNOWN_FINDINGS impact: **Option A - no new finding indexed**; this is strong visual evidence, but it does not by itself prove a new mechanism beyond existing open rendering/sprite/display issues.

Architecture compliance: **CONFIRMED**. This task only analyzes the supplied Exodus video. The arcade code remains the program; no Genesis-side behavior changes were made.

## Evidence Package

Trace directory:

- `states/traces/build0213_exodus_video_30fps_20260719_142555/`

Complete 30 FPS extracted frame sequence:

- `states/traces/build0213_exodus_video_30fps_20260719_142555/frames/frame_000001.jpg` through `states/traces/build0213_exodus_video_30fps_20260719_142555/frames/frame_002925.jpg`
- Source video metadata: 5118x1392, 30 FPS, video stream duration 97.466633s, container duration 97.514646s, ffprobe `nb_frames=2924`.
- Extracted frames: 2925. The extra terminal frame is preserved and indexed as an ffmpeg 30 FPS tail-rounding artifact; no interval was intentionally dropped or trimmed.
- Frame/time index: `states/traces/build0213_exodus_video_30fps_20260719_142555/frame_index.csv`

Reduced evidence:

- Main-image 1-second contact sheets: `states/traces/build0213_exodus_video_30fps_20260719_142555/contact_sheets/main_image_1sec_*.jpg`
- Panel 2-second contact sheets: `states/traces/build0213_exodus_video_30fps_20260719_142555/contact_sheets/*_2sec_*.jpg`
- Targeted one-frame boundary sheets: `states/traces/build0213_exodus_video_30fps_20260719_142555/contact_sheets/boundary_*.jpg`
- Reduced keyframe contact sheet: `states/traces/build0213_exodus_video_30fps_20260719_142555/contact_sheets/reduced_keyframes_main_image_contact_sheet.jpg`
- Full-frame and main-image keyframes: `states/traces/build0213_exodus_video_30fps_20260719_142555/keyframes/`

Structured tables:

- `states/traces/build0213_exodus_video_30fps_20260719_142555/tables/required_event_indices.csv`
- `states/traces/build0213_exodus_video_30fps_20260719_142555/tables/chronological_gameplay_event_log.csv`
- `states/traces/build0213_exodus_video_30fps_20260719_142555/tables/lizard_component_sat_comparison.csv`
- `states/traces/build0213_exodus_video_30fps_20260719_142555/tables/foreground_progression_table.csv`
- `states/traces/build0213_exodus_video_30fps_20260719_142555/tables/unprovoked_death_event_table.csv`
- `states/traces/build0213_exodus_video_30fps_20260719_142555/tables/debug_window_transcription.csv`
- `states/traces/build0213_exodus_video_30fps_20260719_142555/tables/keyframe_debug_notes.csv`
- `states/traces/build0213_exodus_video_30fps_20260719_142555/tables/per_frame_visual_metrics.csv`
- `states/traces/build0213_exodus_video_30fps_20260719_142555/tables/analysis_summary.json`

## Debug-Window Transcription Limits

The video includes Exodus debug windows: VDP Image, CRAM/VRAM memory editors, VDP Port Monitor, Plane Viewer panes, Sprite/SAT-style views, and CPU registers. The larger visual panes are legible enough for panel-level observation. The tiny numeric text in memory/register/port panes is not reliably readable from the compressed desktop video. Those fields are marked unreadable in the structured transcription; no exact register, CRAM, VRAM, VDP-port, candidate, mirror, represented, or SAT-word value is claimed from this video unless it is visibly legible in the image.

Legible panel-level observations:

- Plane A carries the foreground/text/floor layer during gameplay.
- Plane B carries the sky/mountain background.
- Window plane shows persistent vertical red/black striping/garbage-like content during gameplay.
- Sprite plane shows Rastan and lizard component boxes; it is useful for component presence/position, but not for raw SAT word transcription.
- VDP Image window is the authoritative visible composite in this evidence package.

## Required First-Frame Indices

| Event | First frame | Time | Assessment |
|---|---:|---:|---|
| First visible lizard | 439 | 14.600s | First partial lizard body visible at far right edge. Frame 438 has no visible lizard body. |
| First incomplete lizard composite | N/A | N/A | Not proven as non-edge-clipped component failure. The frame-439 partial lizard is edge clipping, not proof of missing components. |
| First missing lizard component | N/A | N/A | Not proven from pixels alone. Requires raw component/SAT/mirror trace. |
| First lizard death after visible Rastan hit | 795 | 26.467s | Frame 794 has visible Rastan/lizard overlap/attack pose; frame 795 has lizard body loss. |
| First lizard death without visible Rastan hit | 1056 | 35.167s | Best candidate is a right-side lizard disappearance during display banding; classified as disappearance/possible representation loss, not proven actor death. |
| First gray death-splat | 798 | 26.567s | First unambiguous gray/purple/blue residue after lizard loss. |
| First dropped item | 798 | 26.567s | Same small post-death object/residue first becomes visible. |
| First dropped item wrong palette | 798 | 26.567s | Object appears gray/purple/blue rather than expected arcade item coloring. Visual evidence only. |
| First item movement failure | 800 | 26.633s | Object persists without convincing correct scroll/collection movement; root not proven. |
| First foreground tile-pattern repetition | 429 | 14.267s | First visible gameplay floor/FG band already repeats the same rock pattern. |
| First camera movement without new foreground content | 481 | 16.000s | Player/camera/lizard state changes while foreground/floor pattern remains repeated. |
| First visible sprite flicker | 438 | 14.567s | Sprite-plane marker/box precedes visible main-image lizard by one frame; display banding also visible around frame 384+. |
| First visible sprites vs Exodus SAT/sprite-list mismatch | 438 | 14.567s | Sprite viewer indicates a marker/box while main image has no visible lizard body. This is a viewer/main-output mismatch, not raw SAT proof. |
| First black-bar/display-update failure | 384 | 12.767s | First mid-image black horizontal display/update band; frame 383 is clear. |

## Chronological Visual Summary

- Frames 112-241: title/frontend renders with title logo, sword, prompts, and text.
- Frame 271: ROUND 1 / READY visible.
- Frame 354: Stage 1 entry/fall begins; sky is present and materially improved compared with older missing-sky evidence.
- Frame 384: first black horizontal display/update band.
- Frame 429: first gameplay floor/foreground band appears and is already visibly repetitive.
- Frame 439: first lizard appears at the right edge.
- Frames 481-721: lizards appear green and mostly whole when not edge-clipped; foreground/floor continues as repeated pattern while camera/player/lizards change.
- Frames 794-798: first visible hit-correlated lizard loss, followed by gray/purple/blue splat/item.
- Frames 800-901: dropped object persists and appears palette/movement suspect.
- Frames 1056+ and later: lizard disappearance candidates occur during display banding; video alone cannot separate actor death from representation/display loss.
- Frames 1516-1763: large display discontinuities/black frames/sky-heavy resets occur.
- Late video: Stage 1 continues with repeated foreground/terrain, intermittent black bands, lizards on the right, and no terminal exception visible in the supplied segment.

## Foreground / PC080SN Assessment

Observable facts:

- The sky is fixed enough to be visibly present and stable for long stretches.
- Mountains are present but repeat/scroll with visible discontinuities and wrong composition in places.
- The floor/foreground layer repeats the initial rock pattern as Rastan/camera progress.
- Plane A contact sheets show the foreground/floor content remaining pattern-repetitive over gameplay frames.
- Plane B contact sheets show the sky/mountain layer populated.

Interpretation:

- The video supports a PC080SN foreground/visible-window progression problem: the destination/camera appears to advance, but the foreground source content does not introduce correct new terrain/floor content.
- The evidence is most consistent with repeated/fixed source projection or missing source-column/row advancement for foreground/floor content, not a total tile residency failure.
- The video does not identify the exact PC080SN producer, source-column cursor, or staging row. That requires debugger-side traces.

## Lizard / PC090OJ Assessment

Observable facts:

- Build 0213 lizards are visible and green, consistent with the Build 0210/0213 palette and vertical-alignment context.
- Lizard bodies are mostly complete when on-screen and not edge-clipped.
- Frame 795 proves a first visible lizard body loss immediately after a visible Rastan hit/overlap at frame 794.
- Frame 798 shows a small gray/purple/blue residue/item after that loss.
- Some later right-side lizard disappearances occur without visible Rastan contact, but display banding and debug/main mismatch prevent proving actor death from video alone.

Interpretation:

- The video supports that the lizard sprite path is no longer completely absent: lizards are visible and visually usable enough for combat observation.
- The first hit-correlated lizard death is visually plausible, but the dropped object/death-splat palette is wrong or at least suspect.
- The incomplete/lost-lizard boundary is not proven to be "out of sprites." It could be actor state, representation, SAT/update timing, display banding, or clipping; the video does not expose enough raw data to decide.

## Display / VBlank Assessment

Observable facts:

- Black horizontal bands appear repeatedly in the main output, first at frame 384.
- Some frames are mostly/fully black or show only partial upper/lower slices of the image.
- Debug windows continue to exist during these visual gaps; the video does not show an emulator crash.

Interpretation:

- The evidence supports an ongoing display-update/blanking/timing artifact in Build 0213.
- The video cannot prove whether this is VBlank overrun, DISPLAY_OFF timing, VDP register interaction, emulator-viewer artifact, or a plane/window update boundary.

## Broader Architecture Assessment

The Build 0213 video shows real progress: title/frontend, Stage 1 sky, Rastan, and lizards are visible. However, it also preserves three major open visual classes:

- PC080SN foreground progression/floor repetition remains primary for terrain correctness.
- PC090OJ lizard death/item visual correctness remains open, especially item/death-splat palette and movement.
- Display black-band/update failure remains open and may contaminate sprite/foreground interpretation.

Rainbow Islands remains useful only as context for expected whole-system behavior. No Rainbow Islands-specific architectural conclusion is drawn from this video.

## Recommended Next Task

Recommended next build/evidence focus: run a debugger-side, frame-anchored trace at the video frames around 429, 481, 794-800, and 1056. Capture PC080SN FG source/destination row/column advancement, Plane A staging deltas, lizard actor state, PC090OJ mirror/represented/SAT entries, dropped-item actor/source records, and DISPLAY_OFF/ON timing for those exact frame windows. Do not broaden into unrelated gameplay systems until those frame-anchored boundaries are resolved.

## Non-Actions

No source, spec, tool, Makefile, invariant, ROM, build-counter, or numbered build artifact was modified. No emulator run replaced the supplied video. No build was produced.

## OPEN / CLOSED Issues Impact

- Open issues touched: OPEN-017, OPEN-024; OPEN-001 context.
- New issues opened: NONE.
- Issues closed: NONE.
- Issues intentionally deferred: exact PC080SN producer fix, exact PC090OJ lizard/item root cause, exact DISPLAY_OFF/VBlank/black-band mechanism, bats, collision, input, D00298, continue/game-over.

## KNOWN_FINDINGS Impact

Option A - no new finding to index. The video strengthens existing visual evidence but does not prove a durable new mechanism requiring a KF update.

## STOP

STOP triggered: NO. Evidence extraction and documentation completed from the supplied video only.
