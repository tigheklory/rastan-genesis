# Title Screen State Cluster and Opcode Ownership (Build 218)

## 1) Purpose
Identify the exact attract/front-end title-screen state cluster and the opcode/routine ownership for rendering the arcade-style title screen elements, without applying any fixes.

## 2) Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (latest relevant sections)
- `README.md`
- `docs/research/precoin_flicker_visual_trace.md`
- `dist/Rastan_218.bin` (current logic baseline)
- `build/maincpu.disasm.txt` (arcade reference flow)
- local disassembly generated from Build 218 (`m68k-elf-objdump`)

## 3) Title-Screen State Identification
- **State variables (proven):**
  - major state: `A5+0x0000`
  - substate: `A5+0x0002`
  - step: `A5+0x0004`
  - state timer: `A5+0x002C`
- **Title major-state semantic owner (arcade):**
  - major dispatcher (`A5+0x0000`) at arcade `0x03A052..0x03A06A`
  - title major entry for state value `1` resolves to arcade `0x03A8AC`.
- **Build 218 cluster bracketing (genesis):**
  - title-cluster body observed around `0x03AAB8..0x03ABF6`.
  - substate dispatcher (`A5+0x0002`) at `0x03AAC4..0x03AAD8` with table at `0x03AADA`.
- **Entry behavior:**
  - title init path initializes display elements in substate-0 body (`~0x03AADE..0x03AB20`) and sets `A5+0x0002 = 1`.
- **Exit behavior:**
  - substate-1 coin path (`~0x03AB28` coin poll and subsequent branch) performs credit/update sequence and advances to next major state:
  - `A5+0x0000 = 2`, `A5+0x0002 = 0`, `A5+0x0004 = 0` at `~0x03ABF0..0x03ABA4`/`0x03ABF0` family.
- **Next state:** major state `2` (post-title attract/game-start transition cluster).

## 4) Title-Screen Code Cluster
- `genesis 0x03A252..0x03A26A` (arcade `0x03A052..0x03A06A`)
  - role: major-state dispatch core (`A5+0x0000` jump-table dispatch)
  - confidence: High
- `genesis 0x03AAB8..0x03AAC2` (arcade semantic title major entry around `0x03A8AC`)
  - role: title major-state timer gate
  - confidence: High
- `genesis 0x03AAC4..0x03AAD8` + table at `0x03AADA`
  - role: title substates dispatch (`A5+0x0002`)
  - confidence: High
- `genesis 0x03AADE..0x03AB20`
  - role: title init substate (setup + initial draw dispatch)
  - confidence: High
- `genesis 0x03AB28..0x03ABF6`
  - role: title idle/coin detect + transition out
  - confidence: High
- `genesis 0x03BD5E` (arcade text writer callsite family at `0x03BB48` usage)
  - role: title text/HUD dispatch bridge (`jsr 0x2027B8`)
  - confidence: High
- `genesis 0x05A174`
  - role: title/logo-related descriptor initialization helper
  - confidence: Medium
- `genesis 0x05A626`
  - role: title lower text/overlay helper path
  - confidence: Medium
- `genesis 0x059F36`
  - role: table-driven conversion helper used in pre-coin title-phase family
  - confidence: High
- `main.c` frame pipeline (all pre-coin title frames):
  - `genesistan_run_original_frontend_tick()`
  - `load_arcade_palette()`
  - `sync_arcade_scroll_to_vdp()`
  - `render_frontend_sprite_layer()`
  - confidence: High

## 5) Opcode Responsibility Breakdown
### 5.1 Top HUD (`1UP 00`, `HIGH SCORE`, `2UP 00`)
- primary opcode group:
  - title init text-id dispatch in `0x03AAFA..0x03AB0A` (text IDs `9`, `10`/`11`) via `bsr 0x03BD5E`.
- role:
  - table-driven title HUD text placement through text bridge (`0x03BD5E -> 0x2027B8`).

### 5.2 Large RASTAN logo / sword-T
- primary opcode group:
  - `0x03AAF2: jsr 0x05A174`
  - plus frontend sprite rendering pass in `main.c` (`render_frontend_sprite_layer -> genesistan_render_sprites_vdp`).
- role:
  - builds workram descriptor content and emits VDP sprite layer in frontend loop.

### 5.3 TAITO + copyright lines
- primary opcode group:
  - `0x03AB0E: jsr 0x05A626`
  - text-id dispatches `0x03AB14` (`ID 30`), `0x03AB1C` (`ID 32`) via `0x03BD5E`.
- role:
  - lower title text blocks and associated helper setup.

### 5.4 `CREDIT 0`
- primary opcode group:
  - title idle/coin branch `0x03AB28..0x03AB9C` updates credits/state.
  - text/symbol refresh path through text bridge callsites in the same cluster (`0x03BD5E` family) and helper dispatch.
- role:
  - credit display update tied to coin-poll transition logic, not only static init.

### 5.5 Background/tilemap initialization for title state
- primary opcode group:
  - title init calls around `0x03AADE..0x03AAE6` into helper set (`0x03AFEA`, `0x03AF5E`, `0x03B06C`).
  - text/tile data conversion helpers (`0x059CEA`, `0x059F36`) used in pre-coin phase family.
- role:
  - prepare tile/text backing structures and drive title-related converted tile writes.

### 5.6 Sprite-list generation for title state
- primary opcode group:
  - `0x05A174` / `0x05A626` descriptor generators
  - frontend sprite renderer in `main.c` consumes workram descriptor blocks each frame.
- role:
  - title logo/sword object list creation and VDP SAT emission.

## 6) NOP / Wrong-Target / Misdirection Audit
- `genesis 0x03A26C` major-state jump table entry for title state (`A5+0x0000 == 1`)
  - observed offset: `0x0840` -> lands `0x03AAAC`
  - expected semantic title-major entry cluster start: around `0x03AAB8`
  - classification: **STALE_TARGET**
- `genesis 0x03AADA` substate jump table entry[1] (`A5+0x0002 == 1`)
  - observed offset: `0x004C` -> lands `0x03AB26` (mid-instruction area preceding `0x03AB28`)
  - expected semantic idle/coin substate entry: `0x03AB28`
  - classification: **STALE_TARGET**
- `genesis 0x03AF56` helper body
  - body is NOP/RTS scaffold; called by title helper wrappers
  - classification: **NOP_SCaffold_RISK**
- `genesis 0x03AF5E` (calls `0x03AF56`)
  - title init dependency path, effective no-op side effects
  - classification: **NOP_SCaffold_RISK**
- `genesis 0x03B06C` (calls `0x03B076`, which routes into `0x03AF56`)
  - title init dependency path with scaffolded internal work
  - classification: **NOP_SCaffold_RISK**
- title direct callsites checked in-cluster:
  - `0x03AAFA/0x03AB0A/0x03AB14/0x03AB1C -> 0x03BD5E` text bridge: **OK**
  - `0x03AAF2 -> 0x05A174`: **OK**
  - `0x03AB0E -> 0x05A626`: **OK**
  - `0x03A274 -> 0x055EB8` dispatcher epilogue helper: **OK**

## 7) Required Systems For Correct Title Display
To correctly show the arcade-style title screen, the following must all work in this state cluster:
- **Text/tile path (required):**
  - title text-id dispatch callsites (`0x03AAFA..0x03AB1C`) -> `0x03BD5E` bridge
  - valid text descriptor/table bases and conversion helpers
- **Sprite/logo path (required):**
  - title descriptor builders (`0x05A174`, `0x05A626`)
  - frontend sprite renderer (`genesistan_render_sprites_vdp`)
- **Palette path (required):**
  - `load_arcade_palette()` each frame
  - pre-coin conversion helper family (`0x059CEA/0x059F36`) and valid data bases
- **Scroll path (required but not dominant):**
  - `sync_arcade_scroll_to_vdp()` must not be malformed; title is mostly static but still frame-updated
- **Control-flow dispatch integrity (required):**
  - major/substate jump-table offsets must land on semantic entry points (`0x03AAB8` cluster and `0x03AB28` idle substate entry)

## 8) Root Cause Risk Summary
- **Primary risk:** `CONTROL_FLOW_BREAK`
  - evidence: title major/substate jump-table entries in Build 218 land at stale/mid-body targets (`0x03AAAC`, `0x03AB26`) instead of semantic entries.
- **Secondary risk:** `STALE_TABLE_BASE`
  - evidence: pre-coin title helper family (`0x059F36` and relatives) uses shift-sensitive absolute table/data-base immediates.
- **Secondary risk:** `TITLE_TEXT_PATH_BROKEN`
  - evidence: title text dispatch depends on bridge path and helper correctness; stale entry or helper no-op scaffolding can corrupt visible title text composition.

## 9) Minimal Next Fix Target
=== TITLE_SCREEN_MINIMAL_FIX_TARGET ===
- fix_area: title-state dispatch displacement correctness (major/substate jump-table target integrity) in the Build 218 title cluster.
- exact_state_or_helper_path: `A5+0x0000` dispatcher table at `0x03A26C` and `A5+0x0002` substate table at `0x03AADA`, ensuring title paths enter `0x03AAB8`-cluster and `0x03AB28` idle/coin entry at semantic boundaries.
- why_this_is_the_minimum_title_screen_step: it restores control-flow entry correctness for the title-screen state without redesigning startup/render subsystems.
- what_must_NOT_be_changed: no forced state changes, no NOP insertion, no startup/launcher/gameplay redesign, no shadow-RAM reintroduction, no manual bypass logic.

## 10) Uncertainties
- Exact human-readable mapping of each text ID (`9/10/11/30/32`) to specific on-screen strings was inferred by call grouping and screen composition, not by a decoded string table in this pass.
- Some helper role labels (`0x05A174`, `0x05A626`) are medium confidence due data-driven internals, though call placement in title init is direct.

## 11) Conclusion
The title-screen state is the major-state-1 attract cluster with substate-0 init and substate-1 idle/coin logic; the strongest current risk is dispatch-target misalignment in title jump tables, with secondary table-base fragility in pre-coin conversion helpers.
