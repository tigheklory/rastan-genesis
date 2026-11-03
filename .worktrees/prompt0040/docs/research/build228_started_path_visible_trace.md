1) Purpose
- Re-run Build 228 runtime tracing on a valid started-game path (launcher -> START -> frontend live) and discard no-input launcher-idle conclusions.

2) Startup Validity Proof
- Input injection method (MAME Lua): pulse `P1 Start` on launcher frames (`frame 20: set 1`, `frame 23: set 0`).
- Proof game left launcher:
  - `current_screen` (`0xE0FF6DCC`) changed from `0x00000000` to `0x00000004`.
  - `0x00000004` maps to `SCREEN_FRONTEND_LIVE` in `apps/rastan/src/main.c` enum.
- Sample evidence (`/tmp/build228_start_probe.txt`):
  - `f=25 ... screen=00000000 joy=0080`
  - `f=30 ... screen=00000004`

3) Post-Start Execution Path (Observed)
- Active started-game loop in `main` (`main.isra.0`):
  - `0x2158A0: jsr 0x2027EC` (`genesistan_run_original_frontend_tick`)
  - followed by sanitize loop in `main`:
    - `0x2158B2..0x2158C8` (scan/clear C-window-like pointers)
  - followed by palette path checks/conversion in `main`:
    - `0x2158CA...0x215F64...` (palette buffer scan + conversion/DMA path)
- Frame-sampled PCs after valid start consistently hit these post-start blocks (not launcher menu path).

4) Frontend/Title-State Evidence
- Arcade workram state samples after valid start (`/tmp/build228_started_state_trace*.txt`):
  - `A5+0x0000` (`0xFF004C`) = `0x0002`
  - `A5+0x0002` (`0xFF004E`) = `0x0000`
  - `A5+0x0004` (`0xFF0050`) = `0x0000`
  - `A5+0x002C` (`0xFF0078`) decrements (`0x009E -> 0x0079` across observed started frames)
- Interpretation:
  - started frontend path is live and mutating arcade workram timing state.
  - this is no longer launcher-idle-only observation.

5) Exception Status In Started Path
- `rastan_qr_exc_type` (`0xE0FF6B38`) remained `0x0000` in observed started-window probes.
- No direct `_Rastan_EX_*` entry was captured in this bounded started-run window.

6) Render/Data-Flow Focus For "Garbage Dots" (Started Path)
- The live started path now proven relevant to the visual issue is:
  - `genesistan_run_original_frontend_tick()`
  - `sanitize_arcade_workram()` pointer scrub loop (`0x2158B2..0x2158C8`)
  - `load_arcade_palette()` conversion/DMA path (`0x2158CA..0x215F64+`)
  - sprite push path (`genesistan_render_sprites_vdp`, seen adjacent at `0x2159E8` in same frontend branch)
- This is the correct path to debug title/frontend visual corruption; launcher-idle-only traces are invalid for that goal.

7) Limitations
- MAME frame-sampled probes do not provide per-instruction coverage of transient `0x03Axxx` execution; proof here is state/branch ownership in started mode plus post-start code-region hits.
- No direct screenshot capture was available in this pass.

8) Conclusion
- Corrected started-game tracing confirms the game leaves launcher and executes `SCREEN_FRONTEND_LIVE` path; analysis for title/frontend garbage must continue on this post-start render/data path, not on no-input launcher idle behavior.
