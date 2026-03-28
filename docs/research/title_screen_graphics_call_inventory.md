# Title Screen Graphics Call Inventory

## Section 1 - Title State Proof
Pre-coin title path proof used for this inventory:

- Snapshot evidence (`build/mame/home/rastanmon/snapshots/frame_000014_frontend_page_0000_0001_stage_0000_mode_0000.txt`):
  - `scene=frontend_page_0000_0001`
  - `stage=0000`
  - `mode4=0000`
  - `credits=0000`
  - `page0=0000 page2=0001`
  - This is title/frontend flow with no coin credit.
- Runtime state evidence (`/tmp/title_forward_probe.txt`):
  - `started=true screen=00000004 state=0001/0000/0000 timer2c=0000`
  - This is the started frontend title cluster, not launcher/config/exception.

Working state identity used below:
- Major state: `A5+0x0000 = 0x0001`
- Substate: `A5+0x0002 = 0x0000`
- Step: `A5+0x0004 = 0x0000`
- Timer: `A5+0x002C = 0x0000`

## Section 2 - Execution Order

Step 1
- PC: `0x03AAB8`
- instruction / call: `tstw %a5@(44)` then jump-table dispatch through `0x03AADA`
- graphics class: clear/fill + producer dispatch gate
- target: title state handler entry (`0x03AADE`)
- semantic intent: begin title init graphics sequence when timer gate opens.

Step 2
- PC: `0x03AADE`
- instruction / call: `bsrw 0x03AFEA`
- graphics class: scroll/control gate state
- target: state flags (`A5+0x001E`, `0xE0FF629E`)
- semantic intent: set frontend display/control mode flag used by render path.

Step 3
- PC: `0x03AAE2`
- instruction / call: `bsrw 0x03AF5E`
- graphics class: clear/fill
- target:
  - `0xE0FF11FE` block clear (36 longs)
  - `0xE0FF01BC` block clear (8 longs)
- semantic intent: clear descriptor/staging blocks before title producers run.

Step 4
- PC: `0x03AAE6`
- instruction / call: `bsrw 0x03B06C`
- graphics class: clear/fill + scroll/control + text producer prep
- target: `0x03B076` then `0x03B2AA`
- semantic intent: run shared title graphics prep cluster.

Step 5
- PC: `0x03B076`
- instruction / call: `lea 0xE0FFC84C,%a0` + fill loop via `0x03AF56` with `d0=0x20`, `d1=0x0800`
- graphics class: clear/fill (tilemap/text buffer)
- target: `0xE0FFC84C` text/tile shadow region
- semantic intent: initialize text cell region to space/blank cells before emissions.

Step 6
- PC: `0x03B2AA`, `0x03B2B0`
- instruction / call: `jsr 0x200DC2` (twice)
- graphics class: scroll/control
- target: VDP control/data ports (`0xC00004` / `0xC00000`)
- semantic intent: push work-RAM scroll values into live VDP scroll registers/commands.

Step 7
- PC: `0x03B2B8` -> `0x03BD5E` -> `0x202B74` -> `0x20034C`
- instruction / call: text producer call chain with `D0=2`
- graphics class: tilemap/text
- target:
  - selector table base `0x0003BD92`
  - descriptor-driven write loop
  - VDP writes at `0x200520` (`movel -> 0xC00004`) and `0x200534` (`movew -> 0xC00000`)
- semantic intent: emit one title text record through the real producer path.

Step 8
- PC: `0x03B2BE` (`bsrw 0x03C4F8`), path includes `0x03C614` (`jmp 0x200E56`)
- instruction / call: alternate text record expansion + producer jump
- graphics class: tilemap/text
- target:
  - table base `0x0003C66C` (inside `0x200E56`)
  - VDP writes at `0x200FBC` / `0x200FC2`
- semantic intent: build and emit additional frontend/title text records from secondary table-driven path.

Step 9
- PC: `0x03AAEC` -> `0x202B80` -> `0x2005C4`
- instruction / call: sprite bridge + renderer call
- graphics class: sprite/logo + DMA upload
- target:
  - sprite descriptor staging (`0xE0FF791C`, `0xE0FF6DF0` families)
  - VDP writes (`0xC00004`, `0xC00000`)
  - DMA setup/upload via `0x202E4E`
- semantic intent: transform staged sprite/object descriptors into VDP-visible sprite/graphics payload.

Step 10
- PC: `0x03AAF2` -> `0x05A174`
- instruction / call: logo/title descriptor producer
- graphics class: sprite/logo producer + clear/fill
- target:
  - clears/fills blocks at `0xE0FF11B2` and `0xE0FF0170`
  - updates descriptor content via `0x05A1B0` / `0x05A2C4`-family logic
- semantic intent: build title/logo related descriptor content consumed by renderer.

Step 11
- PC: `0x03AAF8`, `0x03AB0A`, `0x03AB14`, `0x03AB1A` via `0x03BD5E`
- instruction / call: repeated text producer dispatches (`D0=9`, `D0=10/11`, `D0=30`, `D0=32`)
- graphics class: tilemap/text
- target: `0x202B74 -> 0x20034C` (same producer path as Step 7)
- semantic intent: emit multiple title-page strings in pre-coin frontend phase.

Step 12
- PC: `0x03AB0E` -> `0x05A62E`
- instruction / call: string/data block setup call
- graphics class: tilemap/text producer input staging
- target:
  - source/setup blocks around `0x0005B180`
  - destination pointer `0xE0FF6EDE`
- semantic intent: prepare text source data consumed by later producer calls.

Step 13
- PC: `0x03AB20`
- instruction / call: `movew #1,%a5@(2)`
- graphics class: state transition into ongoing pre-coin title page loop
- target: state words (`A5+2`)
- semantic intent: enter steady title page update phase.

Step 14 (ongoing pre-coin loop graphics actions)
- PC cluster: `0x03BA14`, `0x03ABD4`/`0x03ABE4` (`jsr 0x202B80`), and `0x03C614` -> `0x200E56`
- instruction / call:
  - descriptor-digit producer (`0x03BA14`)
  - per-frame sprite renderer bridge (`0x202B80 -> 0x2005C4`)
  - secondary text producer (`0x200E56`)
- graphics class: tilemap/text + sprite/logo + control
- target: WRAM descriptor blocks then VDP ports/DMA
- semantic intent: maintain and refresh title-page visible elements while still pre-coin.

## Section 3 - Graphics Call Table

| order | PC / routine | opcode / call type | reads from | writes to | arcade graphics owner | semantic purpose | likely Genesis VDP equivalent class |
|---|---|---|---|---|---|---|---|
| 1 | `0x03AF5E` | `bsrs` clear loop | immediate constants | `0xE0FF11FE`, `0xE0FF01BC` | producer staging (pre-PC080SN/PC090OJ intent) | clear descriptor buffers | clear/fill staging |
| 2 | `0x03B076` | `bsrw 0x03AF56` | immediate `0x20` | `0xE0FFC84C` window | tile/text intent (PC080SN-like) | clear text/tile shadow cells | plane/tile clear |
| 3 | `0x03B2AA` / `0x03B2B0` | `jsr 0x200DC2` | scroll words in WRAM (`0xE0FF113A/1138/10FC/10FA`) | `0xC00004`, `0xC00000` | scroll/control registers | apply scroll/control state | scroll/control write |
| 4 | `0x03BD5E -> 0x202B74 -> 0x20034C` | `jsr` chain | selector `D0`, table `0x3BD92`, descriptors | `0xC00004`, `0xC00000` | tile/text producer path | emit title text cells | plane text write |
| 5 | `0x20034C` | internal descriptor loop | descriptor bytes/words (`A2`) | VDP command/data (`0x200520`, `0x200534`) | tile/text producer | per-glyph translated write | tilemap/text stream |
| 6 | `0x03C4F8 -> 0x03C614 -> 0x200E56` | table dispatch + `jmp` | table `0x3C66C`, source bytes, selector | `0xC00004`, `0xC00000` | tile/text producer (secondary) | emit formatted frontend text records | plane text write |
| 7 | `0x03AAEC -> 0x202B80 -> 0x2005C4` | bridge `jsr` + renderer | descriptor blocks (`0xE0FF791C`, `0xE0FF6DF0`) | VDP ports + DMA setup (`0x202E4E`) | PC090OJ-like sprite/object intent | build/upload sprite/tile payload | SAT + DMA upload |
| 8 | `0x05A174` | descriptor producer | game state fields (`A5+...`) | `0xE0FF11B2`, `0xE0FF0170` | sprite/logo producer intent | create title/logo descriptors | SAT staging input |
| 9 | `0x05A1B0` (via `0x05A174`) | conditional descriptor writes | `A5+0x1388`, `A5+0x140E/1410/140C` | descriptor entries at `0xE0FF0170+` | sprite/logo intent | choose logo/title variant entries | sprite descriptor populate |
| 10 | `0x05A62E` | text source setup call | ROM table `0x5B180` | `0xE0FF6EDE` path | text producer input | stage title-page text source | text source staging |
| 11 | `0x03BA14` | numeric descriptor writer | table at `0x03BA90`, source bytes | descriptor words (`A1` targets) | HUD/text producer intent | update digit/text descriptors | text descriptor staging |
| 12 | `0x202E4E` (called from renderer) | DMA register program | source ptr/len args | VDP DMA regs (`0x93..0x97` via `0xC00004`) + data path | bulk graphics transfer | upload staged VRAM/CRAM data | DMA transfer |

## Section 4 - Group By Intent

### PALETTE
Relevant PCs/routines:
- `0x2005C4` renderer path (calls `0x202E4E` for bulk VDP uploads)
- `0x202E4E` DMA setup/transfer path

Memory/targets:
- VDP control/data (`0xC00004`, `0xC00000`)
- DMA setup words for transfer classes (register writes with `0x93..0x97` encodings)

Arcade-side meaning:
- push palette/graphics color payload owned by arcade palette producer into Genesis CRAM-visible state.

### TILEMAP/TEXT
Relevant PCs/routines:
- `0x03BD5E`, `0x202B74`, `0x20034C`
- `0x03C614`, `0x200E56`
- `0x03BA14` (descriptor-side preparation)

Memory/targets:
- selector tables `0x3BD92` and `0x3C66C`
- text/tile shadow `0xE0FFC84C`
- VDP plane write path (`0xC00004` + `0xC00000`)

Arcade-side meaning:
- title/frontend text producers resolve descriptor records and emit tile/text cells to visible layer.

### SPRITE/LOGO
Relevant PCs/routines:
- `0x03AAEC -> 0x202B80 -> 0x2005C4`
- `0x03AAF2 -> 0x05A174` and its subroutines (`0x05A1B0`, `0x05A2C4`-family)

Memory/targets:
- descriptor blocks `0xE0FF11B2`, `0xE0FF0170`, `0xE0FF791C`, `0xE0FF6DF0`
- VDP write ports / DMA upload path

Arcade-side meaning:
- logo/object descriptor intent (PC090OJ-like) is staged and then rendered via Genesis sprite pipeline.

### CLEAR/FILL
Relevant PCs/routines:
- `0x03AF5E`, `0x03AF56`
- `0x03B076`
- `0x05A174` early clear loops

Memory/targets:
- `0xE0FF11FE`, `0xE0FF01BC`, `0xE0FFC84C`, `0xE0FF11B2`, `0xE0FF0170`

Arcade-side meaning:
- clear producer-owned buffers before writing new title descriptors/cells.

### SCROLL/CONTROL
Relevant PCs/routines:
- `0x03B2AA` / `0x03B2B0`
- `0x200DC2`

Memory/targets:
- reads: `0xE0FF113A`, `0xE0FF1138`, `0xE0FF10FC`, `0xE0FF10FA`
- writes: VDP control/data `0xC00004` / `0xC00000`

Arcade-side meaning:
- translate title scroll/control intent into active VDP register/control state.

## Section 5 - Missing / Uncertain Items
No guessing applied; current certainty status:

- `1UP`: not yet mapped to a single confirmed selector/descriptor record in this pass.
- `HIGH SCORE`: not yet mapped to a single confirmed selector/descriptor record in this pass.
- `2UP`: not yet mapped to a single confirmed selector/descriptor record in this pass.
- `RASTAN logo`: producer chain is located (`0x03AAF2 -> 0x05A174 -> sprite renderer`), but exact per-tile descriptor-to-final onscreen tuple mapping is not fully decoded here.
- `TAITO`: not yet isolated to one confirmed selector/descriptor ID in this pass.
- `copyright`: not yet isolated to one confirmed selector/descriptor ID in this pass.
- `CREDIT 0`: title text production path is confirmed, but exact selector ID and descriptor record for this specific string is not fully isolated in this pass.
