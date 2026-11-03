# Rastan Palette Port Strategy

This note explains the palette problem in practical port terms for a Sega
Genesis implementation.

It is intentionally split into:

- confirmed facts from the current reverse-engineering
- likely interpretations that fit the arcade hardware model
- open questions that still need tracing or runtime dumps

## Section 1: How Rastan palettes likely work

### Confirmed facts

Rastan is not using "colors baked into graphics ROMs" as the final display
state.

The graphics regions we currently extract are:

- [pc080sn.bin](/home/tighe/projects/rastan-genesis/build/regions/pc080sn.bin)
- [pc090oj.bin](/home/tighe/projects/rastan-genesis/build/regions/pc090oj.bin)

Those hold indexed graphics data for:

- background / text layer graphics (`pc080sn`)
- sprite / object graphics (`pc090oj`)

The strongest proven gameplay-side palette selector path is:

- `0x45684`

That routine:

- chooses a table byte from `0x45722`, `0x4576a`, or `0x456ec`
- forces bit `6`
- ORs the result into `a4 + 0x27`

So `a4 + 0x27` is a real per-object attribute byte carrying palette-related
selection, not RGB color.

The strongest proven color-table upload helper is:

- `0x59ad4`

That routine:

- selects one `16`-entry row from a source table via `d1 * 32`
- selects one destination block via `d0 * 32`
- reads `16` source words
- converts each source word from `0x0RGB`
- writes the converted result into the `0x200000` region

So there are at least two different layers of palette handling:

1. palette bank / attribute selection in actor or layer state
2. real color block upload from program tables into palette-like runtime memory

### Practical model

In port terms, Rastan palette handling likely looks like this:

1. Graphics ROMs provide indexed art only.
2. Tile/sprite records carry attribute words or bytes that choose a palette
   bank.
3. The main CPU loads or updates live palette RAM blocks from program tables.
4. The custom video hardware combines:
   - tile pixel indices
   - palette bank selection
   - live palette RAM entries
5. Final RGB output comes from those palette RAM entries, not from the graphics
   ROMs directly.

That is the right mental model for the port.

## Section 2: What the small attribute values probably mean

### Confirmed facts

The small values we previously decoded:

- `0x0000`
- `0x0001`
- `0x0002`
- `0x002e`
- `0x002f`

come from the startup/title text message table:

- `0x3bb7c`

and are consumed by:

- `0x3bb48`

That table writes alternating:

- attribute word
- glyph word

into the startup/title text layer.

So those small repeated values are:

- startup/title text attributes
- specific to that front-end message system
- not literal RGB colors
- not palette RAM addresses
- not the full game's palette state

### Likely interpretation

Those values likely encode some mixture of:

- text color / palette bank
- priority / layer bits
- display attributes needed by the startup/title text hardware path

The exact bit meaning is still open, but the key point is solid:

- they are selectors / attributes
- they are not color words like the `0x0RGB` palette source entries fed to
  `0x59ad4`

## Section 3: What must be traced or dumped next

To do a faithful Genesis palette conversion, we still need the following.

### 1. Palette RAM address range / final write routines

We have a proven palette-block converter/uploader in:

- `0x59ad4`

But we do not yet have the final hardware-facing palette RAM map fully pinned
down.

We need to confirm:

- what the `0x200000` destination region represents in real hardware terms
- which later routine, if any, transfers or interprets that region as live
  palette RAM for display
- whether separate layer/object palette windows exist

### 2. Boot / init palette setup

We already have strong front-end palette loaders:

- `0x5a356`
- `0x5a3ac`
- `0x5a3de`
- `0x5a474`

using static tables at:

- `0x5a6fa`
- `0x5a73a`
- `0x5a75a`
- `0x5a77a`

We need to classify:

- which title / attract / startup scene each block belongs to
- which destination block numbers map to which visible layers or objects

### 3. Per-stage palette loads

There are clearly more dynamic palette drivers:

- `0x5988c`
- `0x59962`
- `0x599b2`
- `0x59de0`

These look like:

- mode-selectable palette loaders
- animated or staged palette sequences
- player-count or state-selective palette uploads

We need scene-by-scene dumps from real execution to see:

- which blocks are loaded in stage 1
- which are reused in later stages
- which are unique to bosses, effects, or transitions

### 4. Sprite vs background vs UI palette usage

We need to separate active palette usage by category:

- PC080SN background/text layers
- PC090OJ sprite/object layers
- HUD / UI text
- title/front-end only graphics

This matters because Genesis palette lines are global within a frame, but their
allocation should still be organized by usage.

### 5. Runtime effects

We still need to prove whether Rastan uses:

- palette cycling
- flashing / damage effects
- fades
- palette animation for torches, fire, magic, etc.

Given the presence of dynamic palette drivers around `0x59de0`, runtime effects
are likely.

### 6. Simultaneous palette bank usage

This is the most important missing practical number.

We need to know, for real scenes:

- how many distinct palette banks are live at once
- which belong to background
- which belong to sprites
- which can be merged
- which must stay distinct

Without that, we can reason about fit, but we cannot prove it.

## Section 4: Genesis VDP palette constraints

### Confirmed Genesis facts

The Genesis VDP has:

- `4` palette lines
- `16` entries per line
- `64` CRAM entries resident at once
- a `512`-color master space

So:

- it can represent `512` possible colors
- it cannot display `512` simultaneously

In practical display terms:

- each tile or sprite picks one of `4` palette lines
- entry `0` is generally reserved as transparent for tiles/sprites
- so a palette line usually has `15` useful visible colors for sprite/tile art

### Why this is hard for Rastan

The arcade hardware model appears more flexible in palette usage than the
Genesis VDP model.

The hard problem is not just RGB precision.
The hard problem is:

- only `4` live palette lines
- only `16` entries each
- shared CRAM across backgrounds, sprites, and UI

So this is **not** a "reduce all colors globally once" problem.

It is a **bank allocation** problem:

- which objects share a palette line
- which colors inside that line they need
- whether two arcade banks can be merged
- when a scene needs different CRAM contents than the previous one

### Why grouping by usage matters

If we optimize per whole-frame color set only, we can easily break:

- sprite readability
- HUD contrast
- transparency expectations
- palette-driven enemy recolors

The useful grouping is:

- by layer
- by object family
- by HUD/text
- by scene

not just by the frame as one giant image.

## Section 5: Practical palette conversion strategy

### 1. Map arcade palette banks to Genesis palette lines

The likely long-term model is:

- one or more Genesis lines reserved for backgrounds / text
- one or more lines reserved for sprites / objects

But the exact split should be driven by scene audits, not chosen blindly.

A likely starting policy is:

- `PAL0`: HUD / text / static UI
- `PAL1`: background / layer A
- `PAL2`: secondary background / effects
- `PAL3`: sprites

This will probably need scene-specific overrides.

### 2. Reserve palette lines by function, not by convenience

We should keep HUD/text readable at all times, even if that means being more
aggressive elsewhere.

For example:

- title and attract screens can afford more front-end-specific palette layouts
- gameplay should protect:
  - player readability
  - enemy readability
  - HUD contrast

### 3. Expect stage-specific palette uploads

Static global CRAM is unlikely to be enough for the whole game.

A faithful port will probably need:

- title/attract palette sets
- per-stage palette sets
- boss / cutscene / game-over palette sets
- runtime updates for flashes or animated effects

This is not a failure. It is likely the correct architecture.

### 4. Bosses or crowded scenes may exceed one sprite line

If a stage normally fits one sprite palette line but a boss or heavy enemy mix
does not, options include:

- scene-specific remapping so the boss gets its own line
- temporarily reducing sprite palette diversity elsewhere
- merging similar minor enemy colors
- carefully duplicating some tiles into alternate palette lines only where the
  cost is justified

Tile duplication should be a last resort, not the first move.

### 5. Shared-color optimization matters

If multiple objects share:

- black outlines
- metal highlights
- common skin tones
- common stone / fire colors

those should become anchors for palette merging.

This is where your observation about enemy recolors matters:

- if the art is shared and only the palette bank changes, Genesis can often
  preserve that with palette-line remapping instead of tile duplication

### 6. RGB reduction is the easy part

Arcade palette source words currently look like `0x0RGB`.
Genesis wants lower precision in CRAM.

That means:

- source color reduction from arcade space to Genesis space is required
- but that conversion is much less dangerous than bank overcommit

In other words:

- "how many distinct palette banks are needed at once" is more important than
  "can we quantize one color from 4 bits/channel to 3 bits/channel"

### 7. Dithering is probably secondary

Ordered dithering or hand-tuned collapsing may help in:

- gradients
- large title/logo art
- sky or fire transitions

But for most sprite and HUD work, palette discipline matters more than dither.

For gameplay:

- preserve silhouette
- preserve contrast
- preserve hit/readability cues

before spending time on fancy color tricks.

### 8. Protect HUD/text readability first

The HUD and text should probably get the safest palette choices:

- clear white / bright text
- strong outlines
- stable colors across scenes

If something has to lose fidelity first, it should be:

- low-importance decoration
- subtle shade steps in background art
- duplicate enemy recolors that can be merged without gameplay confusion

### 9. Treat transparency consistently

We should keep a strict rule for color `0`:

- transparent for sprite/tile artwork
- not casually reused as a visible color

If the port gets sloppy here, sprite edges and masking artifacts will become a
constant source of bugs.

### 10. Minimize palette swaps and tile duplication

Good palette packing should aim to:

- reuse the same CRAM layouts across nearby scenes when possible
- keep object families on stable palette lines
- avoid duplicating tiles just to fit avoidable palette fragmentation

Dynamic uploads should be used where necessary, but not as a substitute for
good bank planning.

## Section 6: Recommended tooling and scripts

### What should be done manually first

Before automating heavily, we should manually prove:

- the final palette write path
- scene ownership of palette blocks
- which blocks are background vs sprite vs UI
- a few representative scenes:
  - title
  - attract/story
  - stage 1 gameplay
  - a boss / heavy-effects scene

This prevents us from writing scripts around the wrong assumptions.

### What should become scripts later

Once the path is proven, Python tools become worth it for repeatability.

Good script outputs would be:

- palette dumps
  - raw arcade palette source words
  - converted intermediate words
  - Genesis-reduced candidates
- scene reports
  - which palette blocks are loaded in a scene
  - which banks are simultaneously active
- active bank lists
  - per frame or per state cluster
- Genesis-ready palette candidates
  - candidate `PAL0..PAL3` CRAM sets
- conflict reports
  - too many banks active at once
  - too many unique colors for one line
  - sprite/background contention

### Useful concrete tools

1. `dump_palette_tables.py`
   - decode static source tables from known addresses
   - emit raw and converted rows

2. `trace_palette_calls.py`
   - scan known callers of `0x59ad4`
   - emit source table address, row, destination block, and callsite

3. `scene_palette_report.py`
   - consume MAME trace/dumps
   - summarize active blocks per scene

4. `genesis_palette_pack.py`
   - take active arcade banks
   - map them into candidate `PAL0..PAL3` layouts
   - flag overflow or conflicts

5. `palette_conflict_report.py`
   - explain where a scene exceeds Genesis limits
   - identify which objects or layers cause the overage

## Section 7: Open questions / risks

### Confirmed gaps

We still have not proven:

- the final hardware-visible palette RAM address map
- the exact split between background and sprite palette spaces
- full per-stage active palette state
- all runtime palette effects

### Likely risks

1. Some scenes may require more simultaneous banks than the Genesis can hold
   comfortably.
2. Boss scenes may force sprite palette compromises.
3. Title / attract may use different packing assumptions than gameplay.
4. Dynamic effects may require CRAM uploads at moments we do not yet expect.

### Practical risk to avoid

The main risk is solving the wrong problem.

If we optimize by:

- whole-frame color count only
- or graphics ROM data only

we will miss the real issue, which is:

- live palette bank allocation
- scene-specific palette state
- layer/object ownership of those banks

That is why the next work should focus on:

- tracing/dumping real palette state from execution
- not just static graphics inspection

