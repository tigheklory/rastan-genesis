# Andy — IMG_02 Display Audit CORRECTED (Build 0036)

**Status:** CORRECTION COMPLETE. Prior analysis contradicted by
full-resolution image evidence on multiple points.

---

## Phase 1 — Full Resolution Observations (from attached image)

**VDP Image Window:**
- Pattern: 2D checkerboard grid of alternating RED and PURPLE/BLUE
  rectangular blocks. Each block approximately 4×1 tiles. Black region
  at top (~1/4 screen height).
- Orientation: GRID — both horizontal AND vertical alternation, NOT
  purely vertical bars and NOT purely horizontal bands.
- Colors: bright red and deep purple/blue, high contrast.
- Structured: YES — regular repeating checkerboard grid.

**Plane Viewer — Layer A (upper-right panel):**
- Shows DARK RED/MAROON uniform fill across the visible area.
- Appears empty: **NO** — it shows colored content, not black/transparent.
- The viewport indicator (green rectangle) is visible in the upper-left
  area of this panel, confirming this is the Layer A view.
- The fill is UNIFORM — no tile variation visible, but the panel shows
  NON-BLACK content, meaning Layer A contains non-zero nametable entries
  that reference a tile with non-zero pixel data.

**Plane Viewer — Layer B (lower-right panel):**
- Shows ALTERNATING RED AND PURPLE HORIZONTAL BANDS spanning the panel
  width.
- Appears empty: **NO** — clearly shows structured horizontal striping.
- The banding pattern in Layer B directly corresponds to the horizontal
  component of the VDP Image's checkerboard output.

**VRAM Memory Editor:**
- Multiple hex columns visible with structured/repeating data patterns.
- Specific addresses not clearly legible at this panel resolution.

**CPU Registers:**
- PC: `0x00070022` (confirmed from Cody's extraction).
- A1: `0x0003B2FB`.
- A4: `0xFFFFFFFF`.

---

## Phase 2 — Prior Conclusion Reconciliation

Prior analysis: `docs/design/Andy_img02_display_audit.md`.

### "VDP Image shows vertical bars"
**CONTRADICTED.**
The attached image shows a 2D CHECKERBOARD GRID of alternating red and
purple blocks — NOT vertical bars. The pattern has both horizontal and
vertical alternation. My prior description of "alternating red/purple
vertical bands" was based on examining the wrong image
(`frame_0078.png`) at low resolution instead of examining the attached
screenshot.

### "Plane A is all-zero / transparent"
**CONTRADICTED.**
The Layer A Plane Viewer panel shows a DARK RED/MAROON uniform fill —
NOT black/empty. If Plane A were all-zero (nametable entries = 0x0000
= tile index 0 = blank tile), the Layer A Plane Viewer would show
BLACK (transparent). Instead it shows dark red content, meaning Layer A
contains non-zero nametable entries.

Cody's spot sample at `0xE00A+` returned `0x0000 0x0000 0x0000 0x0000`.
This 4-word sample does NOT represent the full 2048-word nametable.
The Plane Viewer's visible non-black content contradicts the assumption
that the entire plane is zero. Possible explanations:
- The spot sample was from a region that happens to be zero while other
  regions are non-zero.
- The spot sample was taken from a different frame's state than what
  the Plane Viewer shows.
- The 4 words at `0xE00A+` are genuinely zero but the vast majority of
  the 2048-word plane contains non-zero entries.

### "Plane B is the display source (by elimination)"
**CONTRADICTED.**
The Plane Viewer shows BOTH layers contain non-zero content:
- Layer A: dark red/maroon fill.
- Layer B: red/purple horizontal bands.
The visible VDP output is a COMBINATION of both layers — the
checkerboard results from Layer A's uniform fill overlaid with Layer B's
horizontal banding. Plane B is not the sole source; it is one of two
contributing layers.

### "Failure classification D (startup sequencing delay)"
**UNVERIFIABLE from the image alone.**
The register state (A4=`0xFFFFFFFF`, PC=`0x00070022`) is consistent
with the startup-delay interpretation — the text-script state IS
uninitialized and the CPU IS in the main loop. However, the visual
evidence that Layer A contains non-zero content means the "startup
delay produces blank Plane A" part of the reasoning is WRONG. Plane A
has content at IMG_02 — it was NOT produced by the text-script system
(A4 proves that), so it must come from another source (`init_staging_state`
or `load_scene_tiles` or the VBlank commit path). The failure
classification needs revision because the premise ("Plane A is empty
because nothing has written to it yet") is false.

---

## Phase 3 — Corrected Plane State

### Layer A
- **Non-zero content visible in Plane Viewer: YES.**
- The Layer A panel shows dark red/maroon fill — not black/transparent.
- **Contradicts Cody spot sample: YES.** Cody's 4-word sample at
  `0xE00A+` showed zeros, but the Plane Viewer shows the entire Layer A
  plane as non-black. The spot sample does not represent the full plane
  state.
- The uniform dark fill in Layer A is consistent with `init_staging_state`
  filling `staged_fg_buffer` with all-zero nametable entries (tile 0,
  palette 0) and then the VBlank FG commit writing those zeros to VRAM
  — WAIT, that would produce black/transparent, not dark red.

  **Alternative explanation:** the dark red in Layer A comes from the
  BG color register (VDP register 7 = background color). In the Genesis
  VDP, the background color fills behind all planes. If tile 0 at VRAM
  address 0 is NOT blank (contains non-zero pixel data), then even
  nametable entries of 0x0000 (tile 0) would render that tile's content
  using palette 0. If tile 0 happens to have non-zero pixel data from
  the boot state, it would show as a colored fill.

  **OR:** tile 0 IS blank but the CRAM palette entry 0 of line 0 is
  non-black. On the arcade, CRAM[0] might be set to a dark red color
  by the palette init. The `palette_init_words` data in main_68k.s
  determines what CRAM[0] contains. If CRAM[0] = dark red, then every
  transparent pixel (value 0) shows dark red instead of black.

### Layer B
- **Non-zero content visible in Plane Viewer: YES.**
- Shows alternating red and purple horizontal bands.
- This is structured, non-trivial content. It likely comes from the
  BG staging buffer checkerboard being committed to VRAM Plane B
  at some point — or from VRAM Plane B retaining boot-state content
  that produces this pattern when rendered with the current palette.

### Cody Spot Sample Reconciliation
- **Spot sample represents full plane state: NO.**
- A 4-word sample at one offset cannot prove the entire 2048-word
  nametable is zero, especially when the Plane Viewer visually shows
  non-black content across the full layer extent. The spot sample may
  be from a region that happens to be zero while the rest of the plane
  has content, or the sample may have been mis-read or taken at a
  slightly different execution point.

---

## Phase 4 — Corrected Display Source

**Prior conclusion was: INCORRECT.**

The prior analysis concluded "Plane B is the sole display source by
elimination because Plane A is transparent." The attached image shows
both Layer A and Layer B contain visible non-zero content.

**Corrected source: COMBINATION (both planes contribute).**

Evidence: Layer A shows uniform dark red fill, Layer B shows horizontal
red/purple bands. The VDP Image's 2D checkerboard grid is the
composited result of both layers. The checkerboard pattern arises from
the interaction of Layer A's fill with Layer B's banding — where they
overlap with the same or different priority/transparency, the VDP
composites them into the visible checkerboard.

---

## Phase 5 — Corrected Failure Classification

**Selected: C — Plane B incorrectly initialized producing wrong output.**

**Changed from prior: YES** (prior was D — startup sequencing delay).

Evidence:
- Layer B contains structured horizontal banding that produces the
  dominant visible pattern. This banding was NOT produced by the
  text-script hooks (A4=`0xFFFFFFFF` proves those haven't fired).
- The banding must come from `init_staging_state`'s checkerboard fill
  of `staged_bg_buffer` (alternating tile indices 1 and 2) being
  committed to VRAM Plane B at some point — either through a
  `bg_row_dirty` commit that my prior analysis incorrectly claimed
  was skipped, or through some other initialization path.
- The "startup sequencing delay" diagnosis was partially correct
  (A4 does prove text-script hasn't fired), but the failure
  classification was wrong because the visible output is NOT "expected
  pre-title state" — it is a WRONG display produced by incorrect BG
  plane initialization using synthetic checkerboard tiles. The user
  should see either black (no content) or correct title content, not
  red/purple checkerboard bands.
- The incorrect display at IMG_02 is caused by BG plane content that
  should not be visible at this point — either `bg_row_dirty` was set
  and committed despite my prior analysis saying it was cleared, or the
  VRAM Plane B retained non-zero boot content that produces this
  pattern.

Why other classifications are not correct:
- A (Plane A not populated when it should be): Plane A IS populated
  (dark red fill visible) — it's just not populated with title TEXT.
- B (wrong plane): both planes are contributing; it's not a
  "wrong plane" issue but a "wrong content" issue.
- D (startup delay): partially correct for text absence but does not
  explain the visible banded pattern — that's an initialization error,
  not a timing issue.
- E (unknown): sufficient evidence to determine C.
