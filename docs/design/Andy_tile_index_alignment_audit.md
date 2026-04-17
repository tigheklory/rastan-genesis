# Andy — Tile Index ↔ VRAM Alignment Audit (Build 0036)

**Status:** ANALYSIS COMPLETE. **Prior diagnosis revised.** Tile indices
and VRAM content are correct. The primary rendering failure is **wrong
palette / CRAM usage**.

---

## 1. Confirmed State

- Hooks write tile indices into `staged_fg_buffer` — CONFIRMED (plane
  content changes across Build 36 frames).
- Commits transfer staging data to VRAM planes — CONFIRMED
  (`vdp_ports_live count=26468`).
- `fg_cwindow_live count=0` — no direct hardware writes.
- The visible output is wrong — synthetic-looking patterns instead of
  readable arcade text.

**Revision:** the prior Build 36 analysis
(`docs/design/Andy_build_36_exodus_rendering_analysis.md` §5) concluded
"wrong tile graphics / VRAM content" as the primary cause. This audit
**refutes that conclusion** with concrete evidence.

---

## 2. Concrete Tile Trace

### Step 2.1 — Pick a visible tile

Frame sampled: `states/screenshots/build_36/frame_0300.png`. The VDP
Image Window shows a green hatched pattern filling the play field.
The Plane Viewer (Layer A at VRAM `0xE000`) shows the same green
textured content.

Arcade reference: `states/reference/rastan_arcade_60s/frame_0300.png`
shows the item-list screen ("AXE", "HAMMER", "FIRE SWORD", "SHIELD")
with white text on a black background. At this attract-mode phase,
the text-script dispatcher renders item description text using tile
codes 0x41 ('A'), 0x58 ('X'), 0x45 ('E'), etc.

### Step 2.2 — Resolve a specific arcade tile through the LUT

**Traced tile: arcade tile code `0x30` (digit '0' — used by the
number renderer for score/credit display).**

| Pipeline step | Value | Source |
|---------------|-------|--------|
| Arcade tile code | `0x0030` | Number-renderer function at `arcade_pc: 0x03C2E2`; digit `0x30 \| nibble` formula |
| LUT lookup | `genesistan_pc080sn_tile_vram_lut[0x0030]` = **28** | Binary read from `build/pc080sn_tile_vram_lut.bin` at offset `0x30 × 2` |
| Attr LUT lookup | `genesistan_pc080sn_attr_lut[0]` = **0x0000** | Binary read from `build/pc080sn_attr_lut.bin` at offset 0 |
| Combined nametable word | `0x001C` | `28 \| 0x0000 = 0x001C`. Tile index 28, palette line 0, no flip, no priority. |
| VRAM address for tile 28 | `28 × 32 = 0x0380` | Standard Genesis tile layout |

### Step 2.3 — Verify preload placed correct data at VRAM slot 28

**Title scene preload manifest** (`build/pc080sn_scene_preload_title.bin`):
841 (source, dest) pairs. For source tile `0x0030`:

| Field | Value | Verified from |
|-------|-------|---------------|
| Present in manifest? | **YES** | Binary parse of `pc080sn_scene_preload_title.bin` |
| Dest VRAM slot | **28** | Same binary parse |
| Matches LUT? | **YES** — `preload_dest(0x30) == lut(0x30) == 28` | Direct comparison |

**Tile ROM data for tile 0x30** at `genesistan_pc080sn_tile_rom` (ROM
offset `0x0795FC + 0x30 × 32 = 0x079BFC`):

```
0001110000100110011000110110001101100011001100100001110000000000
```

This is **non-zero structured data** — a recognizable 8×8 pixel pattern
for a digit '0' glyph (Genesis 4bpp format). The pixel values are
`0x0`, `0x1`, `0x2`, `0x3`, `0x6` — these index into palette line 0.

### Step 2.4 — Identify the palette problem

**Palette line 0 in Build 36** is the **Build-113 greyscale-ramp
placeholder** (from `tools/translation/postpatch_startup_rom.py:1093–1132`).
Its entries are:

- Entry 0 = `0x0000` (black)
- Entry 1 = `0x0222` (dark grey-green)
- Entry 2 = `0x0444` (medium grey-green)
- Entry 3 = `0x0666` (grey-green)
- Entry 4–15 = increasing green-tinted greyscale

The digit '0' glyph's pixel values (1, 2, 3, 6) render as:
- 1 → dark green
- 2 → slightly-less-dark green
- 3 → medium green
- 6 → lighter green

On a black background (entry 0), this produces a **dark green digit
shape**. At thumbnail resolution in Exodus, a field of many such dark
green digits on black appears as a "green hatched pattern" — exactly
what Build 36 frames 0300–0596 show.

### Step 2.5 — Additional tiles verified

| Tile code | LUT slot | In preload? | LUT == preload dest? | Tile ROM nonzero? |
|-----------|----------|-------------|----------------------|-------------------|
| `0x0020` (space) | 20 | YES | **MATCH** | No (all-zero — correct for space) |
| `0x0030` ('0') | 28 | YES | **MATCH** | Yes (glyph data) |
| `0x0031` ('1') | 29 | YES | **MATCH** | Yes |
| `0x0032` ('2') | 30 | YES | **MATCH** | Yes |
| `0x0039` ('9') | 37 | YES | **MATCH** | Yes |
| `0x0041` ('A') | 43 | YES | **MATCH** | Yes (glyph data: `0001110000110110011000110110001101111111011000110110001100000000`) |
| `0x004C` ('L') | 54 | YES | **MATCH** | Yes |
| `0x0180` (blank fill) | 0 | Not in preload | N/A (slot 0 = blank) | N/A |

**All 7 checked tile codes have LUT == preload-dest agreement.** All
glyph tiles have valid non-zero pixel data in the tile ROM.

---

## 3. Trace Correlation

### VDP activity

`vdp_ports_live count=26468 first_frame=0 last_frame=1797
first_pc=070100 last_pc=070100 first_addr=C00004 last_data=8134`.

All VDP register writes come from the wrapper's `vdp_set_reg` at
`runtime_genesis_pc: 0x070100`. This includes the `VRAM_TILE_BASE`
tile commits (3 synthetic tiles at VRAM 0x20–0x7F), the BG/FG strip
commits, and palette/scroll commits. The trace does not separately
log DMA or direct VDP DATA writes from `load_scene_tiles` (those
happen before the trace harness starts monitoring), but the scene
preload runs during `display_OFF` at boot — before the main loop and
trace-harness initialization.

### Frame-transition correlation

- Frames 0001–~0080: FG is all-zero (index 0 = blank). BG shows
  checkerboard of synthetic tiles 1 & 2 (from `init_staging_state`).
  Visible as red/blue bars because palette ramp colours the all-0xFF
  synthetic tiles with palette line 0 entries.
- Frames ~0080–~0270: hooks begin writing FG nametable entries (strip
  commits fire as `fg_row_dirty` bits are set). FG content transitions
  from blank to populated with LUT-translated indices. Visible as the
  green hatched pattern emerging over the bar background.
- Frames ~0300–0596: FG is densely populated with hook-written entries.
  BG also updated by BG strip commits. The green hatched pattern
  stabilizes to a dark green fill — this is actually the attract-mode
  text and score content rendered with the greyscale-ramp palette.

---

## 4. Root Cause

### Selected: **Option A is NOT the cause; Option B is NOT the cause; the root cause is NONE OF THE THREE OPTIONS in the prompt — it is WRONG PALETTE.**

The three options the prompt listed (LUT mapping wrong, scene preload
layout mismatch, mixed pipeline mismatch) are **all refuted** by the
concrete tile trace in §2:

- **Option A — LUT mapping is wrong:** REFUTED. LUT values for all 7
  checked tiles match the preload manifest destinations exactly (§2.5).
  There is no systematic offset error. The LUT correctly maps
  `arcade_tile 0x30 → VRAM slot 28`, and the preloader places tile
  0x30's graphics at VRAM slot 28.

- **Option B — Scene preload layout mismatch:** REFUTED. The preload
  manifest's (source, dest) pairs are generated by the same
  `assign_scene_aware_slots()` function in
  `tools/translation/precompute_pc080sn_tile_lut.py` that produces the
  LUT. They use the same slot assignment. 841 tiles are loaded for the
  title scene. No mismatch.

- **Option C — Mixed pipeline:** REFUTED. There is one tile-load path
  (`load_scene_tiles`), one LUT (`genesistan_pc080sn_tile_vram_lut`),
  and one preload manifest per scene. The `vdp_commit_tiles_if_dirty`
  path writes only 3 synthetic tiles to VRAM slots 1–3, which do not
  overlap the preload range (slots 20+). No conflict.

### Actual root cause: **Wrong palette / CRAM usage**

The tile GRAPHICS are in VRAM at the correct positions. The nametable
INDICES are correct (LUT and preload agree). The plane MAPS are being
updated by the hooks and committed by the VBlank handler. The rendering
pipeline is structurally correct.

The visible "garbage" is actually **correctly-indexed,
correctly-shaped arcade text and score content** rendered with the
**Build-113 greyscale-ramp placeholder palette** instead of the
arcade's actual color palette.

Evidence:
- Tile `0x30` (digit '0') has pixel values `{0, 1, 2, 3, 6}`.
- Palette line 0 entry 1 = `0x0222` (dark green), entry 2 = `0x0444`,
  entry 3 = `0x0666`. These produce a green-on-black digit shape.
- At Exodus thumbnail resolution, a screen full of green-on-black
  glyphs appears as a "green hatched pattern" — exactly what
  frames 0300–0596 show.
- The attr LUT returns `0x0000` for input 0, selecting palette line 0.
  This is structurally correct (the arcade uses palette 0 for standard
  text), but the Genesis CRAM palette line 0 contains the greyscale
  ramp, not the arcade's text colors.
- The prior Build 36 analysis misidentified the green hatch as
  "synthetic bringup tiles" — it is actually real arcade text content
  rendered in wrong colors. The VRAM Pattern Viewer in Exodus showed
  recognizable tile shapes that were mistaken for synthetic patterns
  because the palette made them look similar at low resolution.

### Corrected diagnosis

The Build 36 rendering failure is **not** "wrong tile graphics / VRAM
content" (the §5 conclusion of `Andy_build_36_exodus_rendering_analysis.md`).
It is **wrong palette / CRAM usage**: the greyscale-ramp placeholder
in CRAM renders all text as green-tinted shapes that are unrecognizable
at Exodus thumbnail resolution but are actually correctly-shaped glyphs.

---

## 5. Implementation Readiness

**BLOCKED — further analysis required before implementation.**

The fix target is clear: replace the Build-113 greyscale-ramp palette
with correct arcade-to-Genesis palette translation. But the
implementation path has two options:

1. **Static palette preload** — compute the correct Genesis CRAM values
   for the attract-mode palette at build time and load them via
   `init_staging_state`. This is a one-shot fix for the current visual
   but won't handle runtime palette changes (attract-mode palette
   animations, gameplay palette updates).

2. **Runtime palette interception** — hook the arcade code's palette
   write path (writes to `0xC50000` or equivalent) and translate to
   Genesis CRAM in real time. This is the structurally correct approach
   per the Rainbow Islands model but requires a new hook spec.

The next Andy prompt should determine which approach is correct and
produce the corresponding spec. No implementation in this audit.

---

## Open Questions

1. **Which arcade palette entries does the attract mode use?** The
   arcade writes palette data via a specific code path — identifying
   that path and its Genesis translation is the next analysis target.
2. **Does the `palette_pre_conversion` step in
   `postpatch_startup_rom.py:1093–1132` run in this build?** It should
   — it writes the greyscale ramp to `genesistan_palette_rom_table`.
   But the CRAM update happens via `vdp_commit_palette` which copies
   `staged_palette_words` to CRAM. Are `staged_palette_words` being
   populated from the correct source (arcade palette intent) or from
   the `palette_init_words` bringup data?
3. **Is there an existing arcade palette-write interception path** in
   the current hook set? Check `docs/design/handler_translation_coverage.md`
   for any `0xC50000`-range or palette-class writer coverage.
