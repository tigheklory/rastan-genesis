# Cody — Build 0391 ROUND/READY Video Sequencing Audit

Date: 2026-09-30  
Scope: analysis only  
Build examined: 0391  
Build counter: 391, unchanged  
Production source changed: no  
ROM produced: no

## Result

The Build-0391 defect is a Genesis ordering error between Plane-B name-table
lifetime and pattern-slot lifetime.

Build 0391 briefly disables the Genesis display during gameplay entry. While
the display is disabled, the initial fixed gameplay Plane-B package reuses the
low VRAM pattern slots that contain the `ROUND 1 / READY !` glyphs. The old
READY Plane-B name words are still present in staging, however, and the package
installer republishes them before re-enabling display. The visible result is the
old READY cell layout drawing newly installed level patterns. Later gameplay
map/name publication finally replaces those stale READY name words.

The original arcade orders the transition differently. Its ROUND/READY
teardown clears/removes the old tilemap presentation before the equivalent
gameplay graphics become visible. Its fixed graphics ROM also does not have the
Genesis-specific condition in which a surviving name word suddenly refers to
different pixels because a shared VRAM slot was reassigned.

Thus:

- READY names retained during the bad Genesis interval: **YES**.
- READY pattern slots reused for gameplay graphics: **YES**.
- Pattern bytes replaced before the READY names cease to be visible: **YES**.
- Palette as the cause: **NO**.
- Tighe's hypothesis: **SUPPORTED IN SUBSTANCE**.

No fix is implemented in this task.

## Input videos

| Recording | Exact path | Bytes | SHA-256 | Video stream | Duration | Decoded frames |
|---|---|---:|---|---|---:|---:|
| Genesis Build 0391 | `states/screenshots/build_391.mp4` | 1,362,437 | `bdca44f40d12f1697b6bb72a4b26c676147c42631a3e6090a3c4a8cc4978d88a` | 642x512, 30 fps, H.264/yuv420p | 10.300000 s video (10.410646 s container) | 309 |
| Original arcade | `states/screenshots/arcade_example.mp4` | 12,139,249 | `b69700b6b9d7188b798334fd681ae968e82d84b3fbb2dc8815c18b22d884cc16` | 1932x1426, 30 fps, H.264/yuv420p | 11.800000 s video (11.861313 s container) | 354 |

Both streams begin at presentation timestamp `0.033333`.

## Extraction and retained evidence

Each source was already exactly 30 fps. Extraction therefore used one lossless
PNG for every decoded source frame with timestamp-preserving indexes; it used no
scaling, cropping, interpolation, or filtering.

- Genesis: `states/screenshots/round_start_build0391/`, 309 PNGs plus
  `index.tsv`.
- Arcade: `states/screenshots/round_start_arcade/`, 354 PNGs plus `index.tsv`.
- Key full-resolution, unscaled comparisons:
  `states/screenshots/round_start_comparison/`.

The comparison canvases place the original 642x512 Genesis image and original
1932x1426 arcade image side by side on a 2574x1426 black canvas. Neither source
is resampled. These generated screenshot directories are ignored by Git and
were retained locally rather than added as hundreds of binary repository
files.

## Visual timeline

Frame numbers below are extracted/source-frame numbers; timestamps are their
presentation times.

### Original arcade

| Frame | Time | ROUND/READY | Background/map | Corruption | Blank? | Milestone |
|---:|---:|---|---|---|---|---|
| 192–193 | 6.400000–6.433333 | absent | central playfield black; HUD/footer remain | no | central field only | last pre-READY interval |
| 194 | 6.466667 | first correct, already stable | black central field | no | no | `READY_FIRST`, `READY_STABLE` |
| 195–250 | 6.500000–8.333333 | correct | black central field | no | no | stable READY |
| 251 | 8.366667 | still completely correct | first left-edge terrain strip appears | no | no | `READY_LAST_CORRECT`, `FIRST_TRANSITION_FRAME`, `FIRST_LEVEL_GRAPHICS_VISIBLE` |
| 252 | 8.400000 | progressively removed (`UND 1`, `EADY !` remain in this captured frame) | left terrain strip remains | no aliasing | no | READY teardown visible |
| 253–256 | 8.433333–8.533333 | absent | center remains black; HUD/footer and left terrain strip remain | no | no full-screen blank | post-READY transition |
| 257 | 8.566667 | absent | correct gameplay field | no | no | `FIRST_GAMEPLAY_CORRECT` |

What the arcade video proves: terrain presentation begins while the final
correct READY frame is still visible, then READY is removed. The old READY
layout never displays level-pattern pixels. There is no completely blank video
frame: the center is black during part of the transition, but the HUD/footer
and then a terrain strip remain visible. A black center alone is not evidence
of a hardware display-disable operation.

### Genesis Build 0391

| Frame | Time | ROUND/READY | Background/map | Corruption | Blank? | Milestone |
|---:|---:|---|---|---|---|---|
| 118 | 3.933333 | absent | final throne/button screen | no | no | last pre-round content |
| 119 | 3.966667 | absent | central field black; HUD remains | no | no | pre-READY transition |
| 120 | 4.000000 | first correct, already stable | black field | no | no | `READY_FIRST`, `READY_STABLE` |
| 121–175 | 4.033333–5.833333 | correct | black field | no | no | stable READY |
| 175 | 5.833333 | correct | black field | no | no | `READY_LAST_CORRECT` |
| 176–177 | 5.866667–5.900000 | not visible | captured game output blank | not visible | yes | `FIRST_BLANK_FRAME`, `LAST_BLANK_FRAME`; gameplay-entry display-off interval |
| 178 | 5.933333 | layout survives but glyph pixels have become level-pattern fragments | no correct gameplay map yet | yes | no | `FIRST_TRANSITION_FRAME`, first bad/corrupt READY frame, `FIRST_LEVEL_GRAPHICS_VISIBLE` |
| 179–185 | 5.966667–6.166667 | stale layout continues to show repurposed patterns | transition continues | yes | no | corrupt interval |
| 186 | 6.200000 | absent | correct gameplay field | no | no | `FIRST_GAMEPLAY_CORRECT` |

The two blank Genesis frames are consistent with the statically proven VDP
register-1 display-off interval. The first gameplay-pattern DMA occurs inside
that hidden interval; video alone cannot assign the instruction to one of the
two rendered blank frames.

## Semantic alignment

| Event | Original arcade | Build 0391 | Difference |
|---|---:|---:|---|
| READY first/stable | frame 194, 6.466667 s | frame 120, 4.000000 s | semantic match |
| final correct READY | frame 251, 8.366667 s | frame 175, 5.833333 s | both retain a stable READY period |
| transition begins | frame 251, 8.366667 s | frame 176, 5.866667 s | Genesis blanks the whole game output |
| READY removal begins | frame 252, 8.400000 s | names are still retained when frame 178 appears | first semantic mismatch |
| level graphics begin | frame 251, correct beside READY | frame 178, incorrectly through READY cells | arcade does not alias READY patterns |
| first correct gameplay | frame 257, 8.566667 s | frame 186, 6.200000 s | both eventually reach correct gameplay |

## Character/name/pattern evidence

The Genesis artifact preserves the READY text's two-line geometry and 8x8 cell
boundaries at the same screen positions while the pixels within those cells
change. It is not a translated or scrolled gameplay name map, and it is not a
uniform recoloring of the same glyph pixels. Static package inspection proves
that the low slots named by those cells are reassigned to different gameplay
patterns.

Representative cells are shown below. Name words have no extra attribute bits
in this text path, so their low 11-bit slot is also the displayed word. The
`Pattern after` code is the fixed gameplay Plane-B source installed into that
same Genesis slot.

| READY character | Arcade text code | Name word before/corrupt | Genesis slot | Pattern after fixed-B install | Conclusion |
|---|---:|---:|---:|---:|---|
| R | `0x0052` | `0x0027` / `0x0027` | `0x027` | arcade code `0x04CC` | name/slot retained; pixels replaced |
| O | `0x004F` | `0x0025` / `0x0025` | `0x025` | arcade code `0x04CA` | name/slot retained; pixels replaced |
| U | `0x0055` | `0x002A` / `0x002A` | `0x02A` | arcade code `0x04CF` | name/slot retained; pixels replaced |
| N | `0x004E` | `0x0024` / `0x0024` | `0x024` | arcade code `0x04C9` | name/slot retained; pixels replaced |
| D | `0x0044` | `0x001A` / `0x001A` | `0x01A` | arcade code `0x04BF` | name/slot retained; pixels replaced |
| 1 | `0x0031` | `0x0009` / `0x0009` | `0x009` | arcade code `0x04AE` | name/slot retained; pixels replaced |
| E | `0x0045` | `0x001B` / `0x001B` | `0x01B` | arcade code `0x04C0` | name/slot retained; pixels replaced |
| A | `0x0041` | `0x0017` / `0x0017` | `0x017` | arcade code `0x04BC` | name/slot retained; pixels replaced |
| Y | `0x0059` | `0x002D` / `0x002D` | `0x02D` | arcade code `0x04D2` | name/slot retained; pixels replaced |
| ! | substituted `0x2744` | `0x0034` / `0x0034` | `0x034` | arcade code `0x04D9` | name/slot retained; pixels replaced |

All compared 32-byte before/after pattern payloads differ. Spaces use slot zero
and remain blank. That explains why only some visible fragments survive in the
corrupt interval while the overall occupied-cell layout remains that of READY.

## Original arcade static sequence

The original controller is rooted at arcade PC `0x055DDC`.

1. Substate 12 begins at `0x055FC2`.
2. `0x055FCA` calls `0x0561A0`. This zeroes the retained scroll fields, calls
   `0x055AB4` to publish scroll state, and clears both PC080SN C-window
   tilemaps to blank code `0x0020`.
3. `0x055FCE` calls READY selector `0x0561FE`, which reaches the shared text
   writer at `0x0563A6` and creates the ROUND/READY tilemap.
4. Substate 13 at `0x055FE0` increments timer `A5+0x1392` at `0x055FE8` and
   waits for `0x0080` ticks at `0x055FEC`.
5. At expiry, `0x055FF6` calls `0x05618C`; `0x055FFA` then calls teardown
   `0x056440`.
6. `0x056440` clears the transient sprite records and calls `0x0561A0` again,
   clearing the old ROUND/READY tilemap before the gameplay presentation.
7. `0x056004` sets transition state `A5+0x1394` to `0x00FF`; the controller
   restores the retained progression value to `A5+0x013E`, then proceeds into
   gameplay map setup and player-controlled state.

No explicit global arcade display disable is proven in this bounded path.
`0x0561A0` implements the hiding operation by clearing the tilemaps, not by
turning the screen off or forcing the palette black. This agrees with the
arcade video, where persistent HUD/footer content rules out a full-screen blank
interval. The arcade PC080SN uses fixed graphics ROM rather than dynamically
reassigning Genesis VRAM character slots, so a lingering name cannot acquire a
new pattern identity in the Genesis manner.

## Genesis Build-0391 static sequence

The corresponding translated PCs include:

- arcade `0x055FCA` -> Genesis `0x05605A` (initial clear call);
- arcade `0x055FE0` -> Genesis `0x056070` (READY delay state);
- arcade `0x055FF6` -> Genesis `0x056086` (expiry path);
- arcade `0x0561A0` -> Genesis `0x056230` (translated clear routine);
- arcade `0x0561FE` -> Genesis `0x05628E` (READY selector);
- arcade `0x0563A6` -> Genesis `0x056436`, patched to the native text-writer
  bridge at `0x072490`;
- arcade `0x056440` -> Genesis `0x0564D0` (translated teardown).

At gameplay-scene activation, native `load_scene_tiles` starts at Genesis PC
`0x074790`:

1. `0x074818` requests VDP register 1 value `0x34`: display off.
2. It uploads the ordinary gameplay manifest and establishes gameplay scene
   state.
3. `0x07489A` calls `fg_cache_reset` at `0x072990`.
4. That reaches `fg_boundary_install` at `0x072B2C` for the initial gameplay
   package.
5. `0x072BE4` again selects VDP register 1/display off.
6. The fixed Plane-B upload loop at `0x072C30..0x072C4E` uploads 854 gameplay
   patterns. Its low destination slots include the READY slots listed above.
7. Because this is the initial package, `0x072E1C..0x072E2C` DMAs all 2048
   words from `staged_bg_buffer` (`0x00FF40A0`) to Plane B at VRAM `0xC000`.
   Those staged words still contain the READY name layout.
8. `0x072E30..0x072E40` similarly publishes Plane A.
9. `0x072E74..0x072E78` writes VDP register 1 value `0x74`: display on.
   `load_scene_tiles` repeats display-on at `0x0748A2..0x0748A6`.
10. Subsequent gameplay strip/map work, including native
    `genesistan_hook_itempage_strip_blit` at `0x0727EC`, replaces the READY
    Plane-B names with proper gameplay names.

The first level-pattern DMA is therefore the first iteration of the fixed-B
upload loop at `0x072C30` (DMA call at `0x072C4A`). Display is disabled at that
instant. Display-off is not enough: the installer republishes the stale READY
names and turns display back on before later gameplay map publication replaces
them.

## First semantic ordering divergence

| Operation | Original arcade | Build 0391 | Match? |
|---|---:|---:|---|
| READY visible | after tilemap clear and text write | after staged-plane clear and text write | yes |
| transition hiding begins | READY tilemap teardown/clear | VDP display off | only superficially |
| READY names removed/hidden | tilemap cleared before gameplay presentation | names remain in staging | **no — first semantic divergence** |
| gameplay patterns loaded/reused | cannot alias old names through mutable VRAM slots | low READY slots overwritten while names survive | no |
| gameplay names populated | after old names are cleared | after stale READY names are republished and display is on | no |
| display becomes visible | no bounded global-disable event; cleared map governs visibility | explicitly enabled by package installer | no |
| player control begins | after clean transition | after the corrupt interval and later map publication | eventual match |

## Display semantics and palette

For Genesis, "display off" is exact: `load_scene_tiles` writes mode-2/register-1
value `0x34`, whose display-enable bit is clear. "Display on" is likewise exact:
the installer writes `0x74`. The backdrop/palette does not produce the observed
glyph-to-terrain substitution. The same name words select the same slots; the
32-byte pattern payloads in those slots change.

For the arcade, no global display-off write is present in the bounded
ROUND/READY teardown path. The transition is achieved through tilemap clearing
and subsequent map presentation. Consequently, the report does not infer an
arcade hardware display disable merely from visually black parts of a frame.

## Hypothesis evaluation and repair boundary

Tighe's hypothesis is **SUPPORTED IN SUBSTANCE**: gameplay pattern reuse/loading
must not become visible while the READY name layout is still resident. Genesis
does perform the uploads while its display is off, but negates that protection
by re-enabling display after republishing stale READY names and before the
proper gameplay names replace them.

The eventual repair boundary is the one-time gameplay scene/package
transition: preserve the original arcade ordering so READY teardown/name removal
precedes any visible reuse of its pattern slots, and expose the gameplay plane
only after its pattern data and matching name tables form one coherent state.
This report deliberately does not select or implement a patch.

The correction should require no per-frame work, PC080SN emulation,
framebuffer, runtime allocator, or duplicate persistent tile cache. It is an
ordering correction around existing one-time pattern and name-table uploads
during an already blanked transition.

## Status

- Fix implemented: **NO**.
- Source changed: **NO**.
- ROM built: **NO**.
- Build counter: **391 unchanged**.

