# Build 55b Video Frame + Debug Window Capture (30 FPS)

## Source Video
- `states/screenshots/build_55b.mp4`
- `ffprobe`: `50.433300s`, `5120x1394`, `30 fps`

## Frame Extraction
- Command used:
  - `ffmpeg -i states/screenshots/build_55b.mp4 -vf fps=30 states/screenshots/build_55b_frames_30fps/frame_%05d.png`
- Output:
  - Directory: `states/screenshots/build_55b_frames_30fps/`
  - Frame count: `1514`
  - Naming: `frame_00001.png` .. `frame_01514.png`

## Full-Resolution Debug Sampling
- 1fps sampling command:
  - `ffmpeg -i states/screenshots/build_55b.mp4 -vf fps=1 states/screenshots/build_55b_debug_sample_1fps/sec_%05d.png`
- Output:
  - Directory: `states/screenshots/build_55b_debug_sample_1fps/`
  - Frame count: `50`
  - Naming: `sec_00001.png` .. `sec_00050.png`

## Runtime Start Timing (from sampled-frame deltas)
- Image window first clear change vs sec_1 baseline: `sec_00005` (~`5s`)
- Port monitor first clear change vs sec_1 baseline: `sec_00013` (~`13s`)
- 68000 register panel first clear change vs sec_1 baseline: `sec_00013` (~`13s`)

## Debug Windows Inventory + Observed Contents

### 1) VDP - VRAM Pattern Viewer
- Palette selection:
  - `Greyscale low-high` selected
  - `Palette Line 1..4` unselected
  - `Greyscale high-low` unselected
  - `Shadow` and `Highlight` unchecked
- Block size:
  - `Auto` selected (`8x8`, `8x16` unselected)
- Display settings:
  - `Blocks per row = 0`
  - `Magnification = 0`
- Visual content:
  - Pre-run sample: stripe-heavy tile display
  - Active sample: high-contrast glyph/texture-like block data still visible in lower half

### 2) VDP - Image Window
- Pre-run sample: mostly black
- Active run sample: large gray/green/black regions with horizontal striping still present

### 3) VDP - CRAM - Memory Editor
- Rows shown from `00` through `78`
- Build 55b sampled values are **not all `0EEE`**.
- Visible examples (sec 20/sec 50):
  - Row `00`: `0000 0EEE 000E 0468 08AC 04EA`
  - Row `0C`: `0246 0EEE 0EEE 0EEE 0EEE 0EEE`
  - Row `60`: `0000 0868 0846 0646 0624 0424`
  - Row `6C`: `0402 0202 0202 028C 044C 0226`
  - Row `78`: `0004 0002 0222 0424`

### 4) VDP - VRAM - Memory Editor
- Upper ranges still include `0000` / `FFFF` patterns.
- Lower visible ranges contain nontrivial data (examples include `2222`, `2200`, `1000`, `1100`, `0110` pattern fields).
- This is visibly denser/non-uniform compared with pre-run baseline.

### 5) VDP - Port Monitor
- Columns visible:
  - `Operation`, `Data`, `HCounter`, `VCounter`, `Access Time`, `Source`
- List size shown:
  - `2000`
- Logging options shown as enabled:
  - `Status Register Read`
  - `Control Port Write`
  - `Data Port Read`
  - `Data Port Write`
  - `HV Counter Read`
- Representative entries visible in active samples:
  - `CP Write  0x8174  H=0x091  V=0x012  Source=Main 68000`
  - `DP Write  0x0000  H=0x032  V=0x012  Source=Main 68000`
  - `CP Write  0x0010  H=0x001  V=0x012  Source=Main 68000`
  - `CP Write  0x4000  H=0x1FF  V=0x012  Source=Main 68000`

### 6) Main 68000 - Registers

#### Pre-run sample
- Register pane initially transitions from uninitialized/idle-looking panel content into active register state around `sec_00013`.

#### Active sample (sec 20)
- A0=`0x0003AD6E` A1=`0x0003BE4E` A2=`0xFFFFFFFF` A3=`0x00050082`
- A4=`0xFFFFFFFF` A5=`0x00FF0000` A6=`0xFFFFFFFF` A7=`0x00FEFFF2`
- D0=`0x00FF0000` D1=`0x000831FF` D2=`0x00000003` D3=`0x00000000`
- D4=`0xFFFFFFFF` D5=`0xFFFFFFFF` D6=`0xFFFFFFFF` D7=`0xFFFFFFFF`
- PC=`0x0003A192`, USP=`0xFFFFFFFF`, SSP=`0x00FEFFF2`
- `S` checked, `T` unchecked, `IPM=7`, `SR=0x2700`

#### Active sample (sec 50)
- The register pane remains on the same active execution context in sampled frames, with PC still shown at `0x0003A192` in the captured view.

### 7) VDP - Plane Viewer (multiple panes)
- Observed layer selections across panes include:
  - `Layer A`, `Layer B`, `Window`, `Sprites`
- Boundary settings:
  - `Screen Boundaries` checked
  - `Sprite Boundaries` checked
- Mapping fields shown in active samples include:
  - `Layer A = 0E000`
  - `Layer B = 0C000`
  - `Window = 0F000`
  - `Sprites = 0F800`
- Plane size fields visible with `Cell Width/Height` including `64 x 32`
- Magnification shown as `1.0`

## Auxiliary Outputs Generated During Review
- 30fps extracted frames:
  - `states/screenshots/build_55b_frames_30fps/`
- 1fps full-resolution sample frames:
  - `states/screenshots/build_55b_debug_sample_1fps/`
- Full-resolution crop/zoom helpers used during review:
  - `states/screenshots/build_55b_debug_crops/`
  - `states/screenshots/build_55b_debug_crops2/`
