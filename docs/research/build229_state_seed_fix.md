# Build 229 State Seed Fix

## 1) Change Made
- File changed: `apps/rastan/src/startup_bridge.c`
- Function: `genesistan_init_workram_direct()`
- State seed change:
  - `genesistan_arcade_workram_words[0]`: `2 -> 1`
  - `genesistan_arcade_workram_words[1]`: unchanged `0`
  - `genesistan_arcade_workram_words[2]`: unchanged `0`
- No branch logic, helper logic, VDP logic, or producer code paths were modified.

## 2) State Before vs After
Before (Build 228 started-path, proven):
- `A5+0x0000=0x0002`
- `A5+0x0002=0x0000`
- `A5+0x0004=0x0000`

After (Build 229 started-path, START injected):
- `current_screen` transitions to `0x00000004` (`SCREEN_FRONTEND_LIVE`) at frame 26
- first 120-frame state capture shows stable:
  - `A5+0x0000=0x0001`
  - `A5+0x0002=0x0000`
  - `A5+0x0004=0x0000`

Evidence file:
- `/tmp/build229_state_seed_probe.txt`

## 3) Execution Proof (Title Cluster Entered)
Required title-region execution taps (Build 229, started-path, 20s run):
- `0x03AAB8` (title major entry): `count=294` (first=25)
- `0x03AADE` (title init body): `count=1` (first=665)
- `0x03AF5E` (title prep helper): `count=5` (first=665)
- `0x03B06C` (title prep helper): `count=1` (first=665)
- `0x03BD5E` (title text dispatch): `count=5` (first=666)

Conclusion:
- Major state now enters title-state path.
- Title init/prep/text dispatch does execute in Build 229.

## 4) Producer Activation Proof
- Frontend producer hook probe (Build 229, started-path, 20s):
  - `0x200DE2` (`hook_text_3c3fe`): `count=2` (activated)
  - `0x20060C` (`hook_sprite_vdp`): `count=294` (active)
  - `0x200000` / `0x2001A6` / `0x20034C`: `count=0` in this run window
- Sprite descriptor backing probe:
  - block A (`0xFF11B2`, 144 bytes): `max nonzero = 0`
  - block B (`0xFF0170`, 32 bytes): `max nonzero = 3`

Evidence files:
- `/tmp/build229_hook_exec_probe.txt`
- `/tmp/build229_sprite_buf_window.txt`

## 5) Visual Result Description
- Direct screenshot capture was not available in this pass.
- Data-path result is improved versus Build 228 control-flow state:
  - title major/init/prep/text dispatch addresses are now executed,
  - but output activation remains incomplete in this window (tilemap hooks still not hit, descriptor block A remains zero).
- Visual classification (data-backed): partial path activation, not yet proven near-correct title composition.

## 6) Remaining Issues (if any)
- Tile/text producer activation is still incomplete in this 20s started run:
  - `hook_tilemap_plane_a` (`0x200000`) = 0
  - `hook_tilemap_plane_b` (`0x2001A6`) = 0
  - `hook_text_3bb48` (`0x20034C`) = 0
- Sprite descriptor block A remains all zero in observed window.
- Therefore, the state-seed correction fixed entry into title-state control flow, but full title output production remains incomplete.
