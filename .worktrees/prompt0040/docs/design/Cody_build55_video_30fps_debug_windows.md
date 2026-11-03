# Build 55 Video Frame + Debug Window Capture (30 FPS)

## Source Video
- `states/screenshots/build_55.mp4`
- `ffprobe`: 52.842646s, 5120x1394, 30 fps

## Frame Extraction
- Command used:
  - `ffmpeg -i states/screenshots/build_55.mp4 -vf fps=30 states/screenshots/build_55_frames_30fps/frame_%05d.png`
- Output:
  - Directory: `states/screenshots/build_55_frames_30fps/`
  - Frame count: `1582`
  - Naming: `frame_00001.png` .. `frame_01582.png`

## Runtime Start Timing (from extracted frames)
- First clear image-window change from pre-run baseline:
  - frame `00374` (`12.433s`)
- First clear VDP port monitor activity change:
  - frame `00383` (`12.733s`)
- First clear 68000 register panel change:
  - frame `00389` (`12.933s`)

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
  - Pre-run (e.g., sec 11): horizontal stripe pattern
  - Active run (e.g., sec 50): tile-pattern data appears (glyph-like/texture-like blocks), stripes still present in lower regions

### 2) VDP - Image Window
- Pre-run: mostly black
- Active run: large gray fill with black bars/regions (matches the visible state in sec 13+)

### 3) VDP - CRAM - Memory Editor
- Rows shown from `00` through `78`
- Observed values remain `0EEE` across visible CRAM entries in sampled frames (sec 11, 20, 50)
- No visible non-`0EEE` replacement in this recording sample set

### 4) VDP - VRAM - Memory Editor
- Pre-run visible pattern: alternating `0000` / `FFFF` regions
- Active run (sec 50): lower address ranges show substantial nontrivial data (examples include `2222`, `1100`, `0110`, `0033`, etc.) while upper rows still include `0000/FFFF` patterns

### 5) VDP - Port Monitor
- Columns:
  - `Operation`, `Data`, `HCounter`, `VCounter`, `Access Time`, `Source`
- List size:
  - `2000`
- Logging options (all checked):
  - `Status Register Read`
  - `Control Port Write`
  - `Data Port Read`
  - `Data Port Write`
  - `HV Counter Read`
- Representative entries during active write-heavy period (sec 20):
  - `CP Write  0x8174  H=0x91  V=0x12  Access=3096906.607943  Source=Main 68000`
  - `DP Write  0x0000  H=0x32  V=0x12  Access=3082811.114893  Source=Main 68000`
  - `DP Write  0x0000  H=0x1A  V=0x12  Access=3079156.727806  Source=Main 68000`
  - `CP Write  0x0010  H=0x01  V=0x12  Access=3075502.340719  Source=Main 68000`
  - `CP Write  0x4000  H=0x01  V=0x12  Access=3075502.340719  Source=Main 68000`
- Representative entries during read-heavy period (sec 50):
  - `DP Read   0x0000  H=0x42  V=0x97  Access=1151623.081109  Source=Main 68000`
  - `DP Read   0x0000  H=0x12  V=0x97  Access=1150398.892199  Source=Main 68000`
  - `DP Read   0x0000  H=0x1CE V=0x97  Access=11542903.669704  Source=Main 68000`

### 6) Main 68000 - Registers

#### Pre-run state (sec 11/sec 12)
- A0..A7: `0xFFFFFFFF`
- D0..D7: `0xFFFFFFFF`
- PC: `0xFFFFFFFF`
- USP/SSP: `0xFFFFFFFF`
- CCR flags: X/N/Z/V/C checked
- `S` checked, `T` checked, `IPM=7`, `SR=0xFFFF`

#### Active state sample 1 (sec 20)
- A0=`0x0003AD6E` A1=`0x0003BE4E` A2=`0xFFFFFFFF` A3=`0x00050082`
- A4=`0xFFFFFFFF` A5=`0x00FF0000` A6=`0xFFFFFFFF` A7=`0x00FEFFF2`
- D0=`0x00FF0000` D1=`0x000831FF` D2=`0x00000003` D3=`0x00000000`
- D4=`0xFFFFFFFF` D5=`0xFFFFFFFF` D6=`0xFFFFFFFF` D7=`0xFFFFFFFF`
- PC=`0x0003A192`, USP=`0xFFFFFFFF`, SSP=`0x00FEFFF2`
- `S` checked, `T` unchecked, `IPM=7`, `SR=0x2700`

#### Active state sample 2 (sec 50)
- A0=`0x00C00100` A1=`0x00C09EA8` A2=`0x000F1E34` A3=`0x000F9E34`
- A4=`0x00C01E3C` A5=`0x00FF0000` A6=`0xFFFFFFFF` A7=`0x00FEFFB0`
- D0=`0x0000C100` D1=`0x42000003` D2=`0x00000003` D3=`0x00000000`
- D4=`0x00000580` D5=`0x00000011` D6=`0x7FC00000` D7=`0xFFFFFFFF`
- PC=`0x00070162`, USP=`0xFFFFFFFF`, SSP=`0x00FEFFB0`
- `S` checked, `T` unchecked, `IPM=6`, `SR=0x2504`

### 7) VDP - Plane Viewer (multiple open panes)
- Observed layer selections across panes include:
  - `Layer A`
  - `Layer B`
  - `Window`
- Boundary settings:
  - `Screen Boundaries` checked
  - `Sprite Boundaries` checked
- Active sample (sec 50) shows mapping fields including:
  - `Layer A = 0E000`
  - `Layer B = 0C000`
  - `Window = 0F000`
  - `Sprites = 0F800`
- Plane size fields shown with `Cell Width`/`Cell Height` including `64 x 32`
- Magnification shown as `1.0`

## Auxiliary Outputs Generated During Review
- 1fps sample frames:
  - `states/screenshots/build_55_debug_sample_1fps/sec_00001.png` .. `sec_00053.png`
- Zoom/crop helper images for reading panels:
  - `states/screenshots/build_55_debug_zoom/`
  - `states/screenshots/build_55_debug_crops/`
