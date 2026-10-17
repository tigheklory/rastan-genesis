# Build 0433 `_do` drop-in black-bar analysis

## Scope and result

This is an analysis-only review of Tighe's direct real-Genesis capture of Build
0433 `_do`. No gameplay was driven by Cody, no trace was created, production
source was not changed, and no ROM was built.

The initial-drop black bars correlate with vertical tile-row crossings, not
with a Rastan animation change. Eight episodes begin at an exact four-source-
frame cadence from frame 420 through frame 448. The player pose and normal
player workload remain visually stable while the bars recur. The current `_do`
source blanks the display only around `dma_publish_frame`; the current vertical
pan path generates a paired Plane-A row and Plane-B row, then publishes both
dirty rows on the following publication phase. The strongest next target is
therefore the bounded vertical-pan row generation/publication bundle, not the
Build-0428 player path.

## Phase 0 baseline

- KF-068, KF-074, KF-077, KF-081, KF-082, KF-091, and KF-094 through KF-096
  were treated as established priors.
- Classification: **EXTENDING** KF-081/KF-082 with Build-0433 real-hardware
  video evidence.
- OPEN-017 is touched. OPEN-024 is context only.
- CLOSED-023 and CLOSED-024 are context only and are not reopened.
- No contradiction of a CONFIRMED or STRONG finding was found.

## Capture and extraction

Source capture:

`states/screenshots/build_433_od/WIN_20261015_16_19_34_Pro.mp4`

- provenance: Tighe-driven Build 0433 `_do` on real Genesis;
- SHA-256: `ac9656c3edccf7e0ef53793b802d70c8456426c49820dcd15c8571cc2c0c2e4c`;
- size: 40,674,998 bytes;
- codec: H.264, `yuvj420p`;
- source resolution: 1920x1080;
- encoded video frames: 700;
- stream duration: 23.327800 seconds;
- nominal rate: 60/1; average encoded-frame rate: 3,500,000/116,639,
  approximately 30.006 fps.

Every encoded source frame was decoded exactly once with passthrough timing,
no interpolation, no resize, and no frame skipping. The primary evidence is
700 lossless 1920x1080 PNGs totaling 907,492,497 bytes:

`states/screenshots/build_433_od/frames_30fps_full/`

Filenames contain the one-based frame number and the source timestamp, for
example `frame_000420_13.966600.png`. Exact timestamp correspondence is also in
`frame_timestamps.tsv`.

## Black-bar window

The scene-entry partial image at frame 403 is not classified as a recurring
overrun bar. The stable initial drop is already visible before frame 419. The
first overrun bar appears in frame 420. The last appears in frame 448. Frame
449 is clean.

The active captured game image is approximately source Y 26..1053. Heights in
the table are source pixels; logical-line estimates scale that 1028-pixel
capture height to the 224-line Genesis viewport.

| Episode | Frames | Source timestamps | Bar source Y / height | Approx. game lines | Motion and visible workload |
|---|---|---|---|---|---|
| 1 | 420-421 | 13.966600-13.999933 | 94-149 / 56 px, constant | 15-27 / 12 lines | steady downward camera progression; Rastan+sword+legs and static HUD only |
| 2 | 424-425 | 14.095900-14.127967 | 94-149 / 56 px, constant | 15-27 / 12 lines | same player pose; steady vertical motion |
| 3 | 428-429 | 14.223900-14.255900 | 94-153 / 60 px, constant | 15-28 / 13 lines | same player pose; next terrain band rises into view |
| 4 | 432-433 | 14.366533-14.399867 | 94-153 / 60 px, constant | 15-28 / 13 lines | same player pose; steady vertical motion |
| 5 | 436-437 | 14.495900-14.527867 | 276-429 / 154 px, then 410-473 / 64 px | 55-88 / 34 lines maximum, then 84-98 / 14 | bar size/position changes; first right-edge Lizardman is now visible |
| 6 | 440-441 | 14.623867-14.655867 | 280-345 / 66 px, then 322-391 / 70 px | 55-70 / 14, then 65-80 / 15 | steady vertical motion; player pose remains unchanged |
| 7 | 444-445 | 14.766533-14.799867 | 264-331 / 68 px, then 342-409 / 68 px | 52-67 / 15, then 69-84 / 15 | steady vertical motion; ground continues rising |
| 8 | 448 | 14.895900 | 258-327 / 70 px | 51-66 / 15 | final bar; frame 449 is clean |

Episodes start at frames `420, 424, 428, 432, 436, 440, 444, 448`: exactly
four source frames apart. At approximately 30 source frames/second, this is
approximately 133 ms or eight 60-Hz Genesis frames, matching an 8-pixel tile-row
crossing at approximately one pixel per Genesis frame. Bar height changes, most
notably at frame 436. The camera does not visibly stop or reverse at any onset.

Rastan remains near the left edge with a screen-space center around logical Y
100-110 throughout this window; the scenery and ground move upward as the
camera follows the downward entrance. There is no bar-correlated player pose,
weapon, or legs transition. The score/HUD remains unchanged.

The Lizardman at the far right becomes visible only around the largest episode
(frames 436-437). It may add sprite residency/upload work to that one peak, but
it cannot explain episodes 1-4, which already establish the four-frame cadence
before the enemy is visible.

## Full-resolution evidence

- immediately before onset:
  `frames_30fps_full/frame_000419_13.919967.png`
- first bar:
  `frames_30fps_full/frame_000420_13.966600.png`
- largest bar:
  `frames_30fps_full/frame_000436_14.495900.png`
- last bar:
  `frames_30fps_full/frame_000448_14.895900.png`
- immediately after recovery:
  `frames_30fps_full/frame_000449_14.927867.png`

Secondary navigation sheets, all labeled with frame and timestamp:

- `contact_sheets/drop_overview_f0399_f0458.png`
- `contact_sheets/onset_f0416_f0427.png`
- `contact_sheets/maximum_f0432_f0443.png`
- `contact_sheets/recovery_f0440_f0451.png`

Seven `all_frames_N.png` sheets cover all 700 frames. Contact sheets are
navigation aids only; bar boundaries and heights above were measured from the
full-resolution PNGs.

## Current Rastan workload

Build 0433 retains the Build-0428 player path unchanged:

- `native_player_frame_try` covers the primary body, equipped sword, and the
  finite Fire Sword variants using generated player records;
- `native_player_secondary_frame` covers the secondary/legs compositor;
- both establish queue context, player base, and append cursor once per frame;
- compact frames perform per visible piece only X/Y addition, Y clipping,
  capacity checking, and the final four-word queue append;
- the shared finalizer still owns residency slot selection, any first-use
  pattern upload, final SAT construction, and SAT publication.

The exact primary/secondary selector values are not present in the video, so an
exact static piece count for these frames is not claimed. Visually, the same
ordinary upright-sword body/weapon/legs pose persists across all onset events.
All 1,200 reachable primary keys and all 416 secondary keys were already proven
native in Build 0428; this is not an unoptimized special entrance compositor.

The separate `native_player_aux_fixed` path scans three A5+0x1338 slots and
uses the shared emitter only for active entries. No such auxiliary pieces are
visible in the drop window. With inactive slots its remaining work is three
tests plus phase bookkeeping, not a workload that matches the observed
four-frame black-bar cadence.

Player queue/SAT work remains every frame, but the clean intervening frames
show that its stable cost fits without producing a bar. No evidence supports a
new player-specific optimization target here.

## Current vertical-scroll workload

The initial entrance matches the retained vertical-pan row-publication route:

`genesistan_plane_a_pan_publish_entering_rows_down/up`

The helper compares old and new visible-top rows from the live arcade-owned
Plane-A Y scroll. For every crossed 8-pixel row it calls both:

1. `.Lplane_a_publish_logical_row_native`
2. `.Lplane_b_publish_logical_row_native`

The current Plane-A producer walks the full 64-column logical row in proven
four-cell blocks, retaining the live ring-front exception and dynamic
residency/final-name work. The current Plane-B producer walks the full
64-column row, sharing descriptor state within its proven source groups but
retaining dynamic name/residency work. The pan path itself performs no
collision-ring write; selector-1/2 retains its separate 64-collision-cell
route, but prior pure-pan evidence found that selector inactive during this
kind of entrance interval.

Each row producer marks one physical row dirty. On the next publication phase,
`vdp_commit_bg_strips_if_dirty` and `vdp_commit_fg_strips_if_dirty` each publish
one 64-word name-table row. Any new Plane-A/Plane-B pattern residency generated
by that row is additionally published by `vdp_commit_tiles_if_dirty`.

Builds 0423-0425 removed large repeated descriptor costs from Plane-B
directional columns and Plane-A selector 0/1/2. They did not remove this
semantic requirement: a pure vertical tile crossing still produces the paired
Plane-A/Plane-B row and publishes both rows. Build-0415's historical matched
measurement already showed a vertical-pan event was materially heavier than a
zero-resolver frame; later work optimized its internals, but no evidence says
the current paired-row event has become free.

## CPU versus publication/DMA

The `_do` variant is decisive about the visible bar's immediate owner:
`RASTAN_VBLANK_DISPLAY_OFF=1` turns display off only on entry to
`dma_publish_frame` and back on immediately after palette, tiles, Plane B,
Plane A, sprites, and scroll publication. Player and background semantic
generation run later in the arcade worker after display has been re-enabled.

Therefore:

- the black pixels themselves measure a publication interval exposed during
  active scanout;
- vertical row generation in worker N creates dirty rows and possible pattern
  installs consumed by publication N+1;
- CPU-side row generation can also make the following IRQ/publication begin
  late because the whole worker still runs at IPL7 (KF-081), affecting where
  the black interval appears;
- the video alone cannot split the event delta among tile-pattern DMA, the
  Plane-B 64-word row, and the Plane-A 64-word row;
- fixed palette/SAT/scroll publication occurs on the intervening clean frames,
  so fixed publication and stable player SAT work do not explain the periodic
  delta.

The strongest attribution is thus **vertical-scroll background work**, with
the `_do` pixels directly implicating its publication/DMA consequence and the
cadence implicating the paired row-crossing producer. The one largest episode
may be mixed with the first visible Lizardman's sprite residency upload, but
the earlier episodes are not mixed with an enemy.

## Ranked next targets

1. **Vertical-pan paired row generation/publication** — strongest. Exact
   eight-Genesis-frame cadence, live vertical scrolling, two 64-cell row
   producers, two 64-word row publications, and possible pattern installs.
2. **Background publication/DMA within that event** — direct immediate owner
   of the `_do` black pixels. The exact tile-vs-Plane-B-vs-Plane-A split is not
   recoverable from video alone.
3. **Player presentation** — weak. Already generated/native, stable pose and
   workload, bars absent on intervening frames, no special entrance path.
4. **Player auxiliary** — unsupported. No visible auxiliary pieces; only a
   bounded inactive-slot scan is evident.

Recommended next optimization target:

> The existing vertical-pan row-crossing bundle at
> `genesistan_plane_a_pan_publish_entering_rows_down/up`, including its paired
> `.Lplane_a_publish_logical_row_native` / `.Lplane_b_publish_logical_row_native`
> generation and the resulting Plane-A/Plane-B dirty-row publication.

This is a bounded target, not a reopening of broad Layer-A/Layer-B semantics.
The protected ring-front seam logic, full logical coherence, collision
ownership, and direct native name production remain constraints.

No additional Tighe-driven test is required before beginning a bounded
optimization of this target. After a future candidate, Tighe should repeat this
same real-Genesis `_do` entrance capture; Cody may run the established rope
race for global regression as already authorized.

## Native replacement policy review

- **Semantic cut retained:** arcade player selectors and arcade vertical camera
  row-crossing decisions remain authoritative.
- **Chip-specific tails removed:** player PC090OJ compositors are replaced by
  direct native queue/SAT inputs; vertical PC080SN row tails are replaced by
  direct final Plane-A/Plane-B name staging and bounded VDP publication.
- **Transitional compatibility:** the player unresolved-key fallback remains
  isolated, with zero reachable primary keys observed by the established
  verifier. No PC080SN/PC090OJ shadow or virtual chip state is proposed.
- No control-flow ownership, source, remap, staging geometry, or hardware
  contract was changed by this analysis.

## Tool reuse and issue impact

Existing project tools/evidence reused: `ffprobe`, `ffmpeg`, the current source,
Build-0423/0424/0425/0428/0433 reports, and the supplied capture. New gameplay
tooling: **NONE**. New gameplay trace: **NONE**.

- Open issues touched: OPEN-017; OPEN-024 context only.
- New issues opened: none.
- Issues closed: none.
- Closed issues reopened: none.
- KNOWN_FINDINGS impact: Option A, no new finding to index. The result confirms
  and applies KF-081/KF-082 to a Build-specific target selection without
  changing their durable reading.

Production modified: **NO**. ROM built: **NO**. Phase D: **NO**. Phase E:
**NO**.
