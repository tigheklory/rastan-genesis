# Build 59 Video Frame + Debug Window Capture (30 FPS)

## Source Video
- File: `states/screenshots/build_59.mp4`
- `ffprobe`:
  - codec: `h264`
  - resolution: `5120x1396`
  - framerate: `30 fps`
  - duration: `36.733300s`

## 30 FPS Frame Extraction
- Output directory: `states/screenshots/build_59_frames_30fps/`
- Naming: `frame_00001.png` .. `frame_01103.png`
- Frame count: `1103`

## 1 FPS Full-Resolution Debug Sampling
- Output directory: `states/screenshots/build_59_debug_sample_1fps/`
- Naming: `sec_00001.png` .. `sec_00037.png`
- Sample count: `37`

## Full-Resolution Review Scope
Reviewed full-resolution frames directly (including startup and stable runtime):
- `sec_00001.png`
- `sec_00005.png`
- `sec_00010.png`
- `sec_00013.png`
- `sec_00020.png`
- `sec_00030.png`
- `sec_00037.png`

## Runtime Transition Timing (from sampled frame hashes)
- `sec_00001`: Windows file-open dialog visible (ROM selection UI still open).
- `sec_00004` .. `sec_00010`: identical frames (same SHA256); static pre-runtime debug state.
- `sec_00011` onward: state starts changing every second.
- `sec_00013+`: active/stable runtime debug state appears and remains dynamic through `sec_00037`.

## Debug Window Extraction

### 1) VDP - VRAM Pattern Viewer
Observed controls:
- Palette Selection: `Palette Line 1` selected
- Greyscale modes unchecked
- `Shadow`/`Highlight` unchecked
- Block Size: `Auto` selected
- Display: `Blocks per row = 0`, `Magnification = 0`

Observed content:
- Pre-runtime (`sec_00010`): mostly striped/placeholder-looking pattern blocks.
- Active runtime (`sec_00013+`): nontrivial tile glyph content appears (letters and dense striping), including visible text-like fragments (e.g., `RASTA...`) and repeated horizontal stripe segments.

### 2) VDP - Image Window (video output window)
- Pre-runtime (`sec_00010`): mostly black field with boundary overlays.
- Active runtime (`sec_00013+`): visible green rectangular fill regions plus black regions and striped artifact bands; not a clean title-screen composition.
- Late sample (`sec_00030`, `sec_00037`): still mixed black/green output with patterned artifacts; output remains unstable-looking rather than final gameplay/title image.

### 3) VDP - CRAM - Memory Editor
- Pre-runtime (`sec_00010`): CRAM rows shown as near-uniform `0EEE` values.
- Active runtime (`sec_00030`/`sec_00037`): CRAM contains mixed non-default values.

Representative active values visible:
- Row `00`: `0000 0EEE 000E 0468 08AC 046A ...`
- Row `0C`: `0246 0EEE 0EEE 0EEE 0EEE 0EEE ...`
- Row `60`: `0000 0868 0846 0646 0624 0424 ...`
- Row `6C`: `0402 0202 0202 028C 044C 0226 ...`
- Row `78`: `0004 0002 0222 0424`

### 4) VDP - VRAM - Memory Editor
- Pre-runtime (`sec_00010`): many `FFFF`/`0000` regions.
- Active runtime (`sec_00013+`): dense structured data appears with repeated fields like `2222`, `2200`, `0110`, `1100`, `1000`.

Representative addresses (active state):
- `0026`: `2222 2222 ...`
- `00B0`: repeating `2222`/`0000` pattern groups
- `0108` onward: `0110`/`1100` binary-like tile word patterns
- `02AA`: `2222 0000 2222 0002 ...`
- `0302` onward: mixed `1110`/`0110`/`0000` groups

### 5) VDP - Port Monitor
Observed config:
- List size: `2000`
- Logging options checked: `Status Register Read`, `Control Port Write`, `Data Port Read`, `Data Port Write`, `HV Counter Read`

Representative active entries (visible in sampled frames):
- `CP Write 0x8174` (Main 68000)
- `CP Write 0x0010` (Main 68000)
- `CP Write 0x4000` (Main 68000)
- multiple `DP Write 0x0000` rows with varying H/V counters

### 6) Main 68000 - Registers
- Pre-runtime (`sec_00010`): register pane appears uninitialized/default (many `0xFFFFFFFF` fields; `PC`/`SR` not yet in stable runtime state).
- Active runtime (`sec_00013+`): register pane populated and changing between samples.

Visible active examples:
- `A1 = 0x0003BE4E`
- `A3 = 0x00050082`
- `A5 = 0x00FF0000`
- `D2 = 0x00000003`
- `PC` observed in active samples includes `0x000719E0` and `0x0003B100`
- `SR` observed active values include `0x2600` and `0x2704`

### 7) VDP - Plane Viewer
Observed controls/state:
- Layer selection visible across panes (`Layer A`, `Layer B`, `Window`, `Sprites`)
- `Screen Boundaries` and `Sprite Boundaries` checked
- Plane Size fields show `Cell Width 64`, `Cell Height 32` for layer/window panes
- Sprites pane shows `Cell Width 64`, `Cell Height 64`
- Magnification: `1.0`

Observed mapping addresses in active frames:
- `Layer A = 0E000`
- `Layer B = 0C000`
- `Window = 0F000`
- `Sprites = 0F800`

## Video Output Window Summary (for Chad/Claude)
- The output window is no longer a static all-black-only state.
- It shows active but incorrect-looking composition: large green blocks, black background regions, and patterned/striped artifacts.
- Pattern/VRAM windows indicate real tile data activity, but final composed scene remains visually broken in these captures.

## Artifacts for Review
- Source video: `states/screenshots/build_59.mp4`
- 30fps frames: `states/screenshots/build_59_frames_30fps/`
- 1fps debug samples: `states/screenshots/build_59_debug_sample_1fps/`
