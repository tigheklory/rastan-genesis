# Build 0417 — Partial Layer-A Dropout Architecture Review (Andy)

> ## ⚠ ROOT-CAUSE SUPERSEDED / DISPROVEN FOR THE A-0154 HOLES (2026-10-12)
>
> **My prior conclusion that active-display DMA / publication timing caused the six persistent
> A-0154 partial Layer-A holes was incorrect.** Cody's ROM-source VDP-DMA boundary analysis
> (`docs/design/Cody_build0417_partial_layer_a_dropout_root_cause.md`) identifies the actual cause,
> and I have independently confirmed its arithmetic (see **§CORRECTION** at the end of this file).
>
> The A-0154 32-byte tile upload crosses a Genesis **128-KiB (0x20000) DMA source-bank boundary**.
> Real hardware **wraps the remaining source reads within the bank**, loading unrelated bytes
> (containing zero nibbles → transparent Plane-A pixels → Layer B through) into the pattern. **Normal
> 0417** crosses after **24 bytes**, corrupting the last **2** pattern rows; **0417_do** crosses after
> **8 bytes** because its linked tile corpus moved **+0x10**, corrupting **6** rows. This exactly
> explains the owner-observed difference between the two builds. The root cause is **established**, not
> an alternative hypothesis.
>
> Everything below the line titled "**ROOT-CAUSE CANDIDATES**" is **SUPERSEDED for the A-0154 holes**.
> The active-display-DMA / publication-overrun observations in this file remain **true as a separate
> performance/correctness topic** (see **§CORRECTION → What remains true**) but did **not** cause the
> six A-0154 holes. Read **§CORRECTION** for the established mechanism; the original text is preserved
> below unchanged for traceability.

**Date:** 2026-10-12 · **Type:** READ-ONLY architecture/code review. No production source, no ROM, no
build number, no Palette-Composer/profile edits, Cody's tree untouched. **Real Genesis is
authoritative; MAME is instrumentation only.**

**Owner fact ACCEPTED (not re-litigated):** inside the affected A-0154 tiles (Segment 2, X40/Y38,
code 0x117, LA-0092, bank 0x003; six occurrences = six circled defects) **Layer B shows through part
of the 8×8 Layer-A cell** (sub-tile, not whole-cell absence); the exposed region is **smaller in
Build 0417** and **larger in Build 0417_do**. This review finds the Genesis-side timing mechanism
that produces sub-tile partial transparency and scales with `_do`.

---

## Relevant VDP pipeline (execution order)

`_vblank_service` runs `dma_publish_frame` (dma.s) at the **start** of IRQ6, then tail-JMPs the arcade
worker (frame N production) at IPL7. `dma_publish_frame` order (VC_MARK 0..6, dma.s:70-96):

1. `vdp_commit_palette` — CRAM DMA
2. `vdp_commit_tiles_if_dirty` — VRAM tile PIO
3. `vdp_commit_bg_strips_if_dirty` — **Plane B row DMA**
4. `vdp_commit_fg_narrow_strips` — **Plane A: `vdp_commit_fg_columns_if_dirty` (32-word column DMA) +
   `vdp_commit_bg_columns_if_dirty` + narrow/row PIO/DMA**
5. `vdp_commit_sprites_vram` — sprite pattern + SAT DMA
6. `vdp_commit_scroll` — HScroll / VSRAM

**Every one of these is a real VRAM/CRAM access.** The column publishers issue genuine **68k→VRAM
DMA triggers** (`dma_words_to_vram_noai`: `ori.l #0x40000080; move.l %d1,(%a1)` = VRAM-write + DMA
enable, dma.s:127-170). The whole IRQ6 (publish + worker) for a heavy scroll frame is **~180,000–
230,000 cycles** (0414/0415 measurements) versus a VBlank window of only **~3,600–13,000 cycles** and
a full-frame budget of **128,009**. **Therefore publication and its DMAs routinely run PAST VBlank
into ACTIVE DISPLAY during scrolling.** This is the architectural fact the rest of the review turns
on.

---

## Normal vs `_do` difference

`_do` = `RASTAN_VBLANK_DISPLAY_OFF=1` (Makefile:61-63, 198). The **only** code difference
(dma.s:72-94): `dma_publish_frame` writes **reg1 display-OFF (0x8134)** before VC_MARK 0 and **reg1
display-ON (0x8174)** after VC_MARK 6. Normal (`=0`) leaves the display **ON** throughout publication.
Consequences:
- `_do` adds two VDP register writes and forces blank for the publication span; its comment states it
  is "SAFE only once the whole phase fits the vblank window; before that it visibly blanks part of the
  picture." So under overrun, `_do` keeps the display **off into active scanlines** and **re-enables
  display mid-active-frame** at the (now later) end of publication.
- `_do` makes IRQ6 slightly longer (the bracket writes) and changes *when display is scanning vs when
  VRAM is being written*: the plane DMAs happen during forced blank, but any DMA/commit that does not
  finish before the display re-enable — or the re-enable transition itself — lands in active scanout.

---

## How sub-tile dropout is possible (the mechanism)

On real Genesis, during **active display** the VDP consumes almost all VRAM bus slots fetching, per
scanline, the Plane-A **name word** then the **pattern row** for each visible cell. A **68k→VRAM DMA
during active display** is the classic prohibited operation: the VDP can only service it by stealing
the few external slots per active line, the 68000 is halted, and the **Plane-A fetch for the
scanlines overlapping the DMA is disrupted** — those lines fetch stale/partial name+pattern data.

A **Plane-A column DMA** (32 words, autoinc 128 = one word per physical plane row) writing while the
raster scans Plane A is the worst case for *sub-tile* artifacts:
- It rewrites a cell's name/pattern **progressively down the column** at the same time the raster
  scans **down the screen**.
- For a given 8×8 cell, the **top rows** may be fetched *before* the DMA reaches/settles that cell
  (old/stale/blank name) while **later rows** are fetched *after* (new A-0154 name), or the fetch is
  corrupted only for the lines coincident with the DMA burst.
- Where the fetched name is the **blank/backdrop** (uniform `0x4000` tile-0, or the proven stale
  `0x6297`), those rows render a transparent Plane-A cell → **Layer B shows through just those rows**
  = the observed sub-tile partial dropout.

This is a **scanout-time** phenomenon: the *settled* VRAM/name word after the frame is correct, which
is exactly why static dumps look fine.

---

## Active-display DMA risk (not limited to A-0154's cells)

Any VRAM DMA during active display disrupts Plane-A fetch — **including DMA to unrelated VRAM**
(sprite patterns, SAT, Plane-B rows, tiles). During heavy scroll the frame issues Plane-B row DMA +
Plane-A column DMA + sprite/SAT DMA, several of which can land in active display. So the dropout need
not come from writing A-0154's own cells: a sprite/SAT/Plane-B DMA running while the raster is on the
A-0154 scanlines can starve those fetches. Prior forensics that inspected only the A-0154
target name/pattern would miss this.

---

## Name/pattern mid-tile risk

The **already-proven** X40/Y38 transient — the cell retains old name **`0x6297`** for part of an
entrance frame before becoming `0x63A4` — is the direct proof that this system can present a **wrong
name for some scanlines of a cell while the final name is correct**. During scrolling the column
publisher writes entering-column names **into Plane-A VRAM during the publication phase that overruns
into active display**; a cell whose new A-0154 name is DMA'd *after* the raster has already fetched
its top rows shows the old blank name (Layer B) for those rows and A-0154 for the rest. `0x6297`
behaves as a blank/sky slot (the `resolve_plane_a_cell` "blank cell → 0" path and the uniform-`0x4000`
backdrop confirm blank Plane-A names exist), so the show-through is Layer B / backdrop, exactly as
observed.

---

## Scroll / ring risk

The 64×32 physical Plane-A ring + 64-row logical projection (per the historical full-64 audit) means
a cell's physical name/pattern is being rewritten as the camera scrolls. If the entering column's DMA
and the raster are out of phase, **different scanlines of one apparent 8×8 feature can momentarily
resolve to the new cell vs the stale ring cell**. Segment-2 rope terrain scrolls continuously, so the
A-0154 cells there are repeatedly re-published during active display — a standing source of the
mid-tile name race. (This is the timing facet of the separate BG-A span/placement issue; here it
matters because it means A-0154 names are DMA'd every scroll frame, not once.)

---

## Column DMA during active display (the central question)

`vdp_commit_fg_columns_if_dirty` / `vdp_commit_bg_columns_if_dirty` (tilemap_hooks.s:4273-4396) run
inside `dma_publish_frame` (via `vdp_commit_fg_narrow_strips`, :4398-4401) at VC_MARK 3-4. Each issues
a real 32-word strided column DMA (autoinc 128) that **touches one cell on every physical plane row**.
When publication overruns VBlank (heavy scroll), these column DMAs execute during active display and
disrupt exactly the Plane-A fetch for the scanlines they overlap — producing **row-local, sub-tile**
artifacts rather than whole-tile loss. This is the top-ranked mechanism.

---

## Row + column dirty coexistence

During combined H+V scroll both masks are set; the publisher does Plane-B row DMA, then Plane-A column
DMA, and toggles **VDP autoincrement 128↔2** between them (dma.s restores 0x02 after the column loop).
If any of these DMAs or the autoinc-register transitions occur during active display, each adds its own
disrupted-scanline span. `_do` shifts the whole overlapping sequence farther into active scanout (it
starts the same work but behind the blank/unblank bracket and a longer IRQ6), so more scanlines are
affected under `_do`.

---

## Why settled state can look correct

The defect exists **only during scanout** of the frame in which the plane DMA overlaps active display.
By end-of-frame the VRAM/name word is the correct A-0154 value. So: a terminal VRAM dump, a settled
name-word read, or a single-pixel sample all report "correct" and **cannot observe the transient
fetch disruption**. The owner's real-Genesis view is the only observer that sees scanout.

---

## Why `_do` can make it worse

`_do` forces display OFF during publication and re-enables it at the **end** of publication. Under
heavy Segment-2 scroll publication overruns VBlank, so: (a) display stays off into active lines and
re-enables **later** than normal (bigger blanked span), and (b) the plane DMAs / the display-reenable
transition land **further down the active frame**, so a **larger set of A-0154 scanlines** is scanned
while the plane is still settling / display is transitioning → **more Layer-B-through rows**.
Fundamentally `_do` increases IRQ6 length and pushes the plane-publication-vs-raster crossing deeper
into active display. A static-asset or settled-state theory predicts identical pixels in both builds
and is therefore **incomplete**; the DMA-during-active-display timing theory is the one that **scales
with `_do`**.

---

## Previous forensic blind spots

1. **Terminal/settled VRAM used as scanout state.** The defect is a per-scanline fetch disruption
   during the frame; post-frame VRAM is correct, so VRAM dumps structurally cannot see it.
2. **Final name word treated as valid for all 8 tile rows / single-pixel sampling.** The mechanism is
   precisely that different scanlines of the cell fetch different (stale vs new / disrupted) state.
3. **Assuming MAME reproduces VDP↔DMA active-display contention faithfully.** MAME/BlastEm model
   DMA-during-display timing approximately; real Genesis contention is stricter, so the emulator can
   under-reproduce or differently-place the dropout. (Do not use it to overrule hardware.)
4. **Inspecting only DMA targeting A-0154's cells.** Unrelated active-display DMA (Plane B, sprite,
   SAT, tiles) also starves Plane-A fetch.
5. **Comparing normalized/paused states instead of owner-observed live scanout frames.**

---

## Root-cause candidates

**#1 — Plane-A VRAM DMA (column publisher + unrelated DMA) executing during ACTIVE DISPLAY because
publication overruns VBlank; the VDP's per-scanline Plane-A name/pattern fetch is disrupted for the
overlapping scanlines, so only those rows of the A-0154 cell show the stale/blank name → Layer B
through.**
 · Explains partial tile: **YES** (only scanlines overlapping the DMA/transition fail). · Explains
`_do` growth: **YES** (`_do` lengthens IRQ6 and pushes the DMA/display-reenable crossing deeper into
active display → more affected scanlines).

**#2 — Mid-tile late-name race: the entering-column name for an A-0154 cell is DMA'd after the raster
has fetched its top rows (the proven `0x6297`→`0x63A4` transient generalized to steady scroll).**
 · Explains partial tile: **YES.** · Explains `_do` growth: **YES** (later publication under `_do`).
(This is a facet of #1 — publication timing vs raster — and may be the same bug seen cell-locally.)

**#3 — Autoincrement/address-state transitions (128↔2) and row+column DMA overlap occurring in active
display, disrupting adjacent fetches.** · Explains partial tile: **YES (partially).** · Explains `_do`
growth: **YES (weaker).** Lower confidence; likely secondary to #1.

**Not the cause:** static A-0154 pixels (proven no zeros; would not vary with `_do`); Palette Composer
mapping (static; §14 — timing-varying defect rules it out).

---

## One decisive next experiment

**Instrument the VDP V-counter around the Plane-A publication during a heavy Segment-2 scroll, both
normal and `_do`.** Reuse the existing `VC_MARK`/`vblank_vc` beam-capture (dma.s:64-102): additionally
capture `0xC00008` (V-counter) **immediately before and after each `vdp_commit_fg/bg_columns_if_dirty`
DMA** (and the sprite/SAT/Plane-B DMAs), on the frames the six A-0154 cells are visible. Then:
- If those DMAs run at V-counter values **inside active display** (V < ~0xE0 / not in VBlank), and
  their V-spans **overlap the screen scanlines of the circled A-0154 cells**, that proves #1.
- If the `_do` run shows the DMA/display-reenable V-spans shifted **later/larger** than normal, that
  proves the `_do` growth.
This is bounded (instrumentation only, no gameplay change), uses existing infrastructure, and directly
tests both the partial dropout and the `_do` scaling. A confirming **fix-direction probe** (optional,
same build): gate the Plane-A column DMA so it cannot start unless the V-counter is still in VBlank
(drop late columns for that frame) and check on real Genesis whether the sub-tile Layer-B-through
disappears — if it does, #1 is confirmed and the repair is "keep plane DMA inside VBlank/forced-blank."

---

**REAL GENESIS IS AUTHORITY: YES. OWNER FACT RE-LITIGATED: NO. CODY TREE MODIFIED: NO. PRODUCTION
MODIFIED: NO. ROM BUILT: NO. BUILD NUMBER CONSUMED: NO.**

---

# §CORRECTION (2026-10-12) — Established root cause (supersedes the hypothesis above for A-0154)

**My prior conclusion that active-display DMA / publication timing caused the six persistent A-0154
partial Layer-A holes was incorrect. Cody's ROM-source VDP-DMA boundary analysis identifies the
actual cause, which I independently confirmed.**

## Actual root cause — unsplit ROM-source VDP DMA crossing a 128-KiB source-bank boundary

The Plane-A tile pattern is uploaded to VRAM by a per-tile **68k→VRAM ROM-source DMA**:
`source = genesistan_pc080sn_tile_rom + code*32`, length 16 words / 32 bytes (`scene_load.s:110-118`,
`lea genesistan_pc080sn_tile_rom,%a2` + `lsl.l #5` = ×32). The Genesis VDP DMA source counter only
increments the low 17 bits — it **wraps within the same 128-KiB (0x20000) bank**: after source
`0x15FFFF` it continues at `0x140000`, **not** `0x160000`. When a tile's 32 bytes straddle a
`0x20000` boundary, the bytes past the boundary are read from the **bank base** (unrelated data),
corrupting the tail rows of that pattern. Those unrelated bytes contain **zero nibbles** → transparent
Plane-A pixels → **Layer B shows through** exactly those sub-tile rows.

**Independently verified arithmetic** (corpus base `0x15DD08`, code `0x117`, `code*32 = 0x22E0`):

| | source | bytes before 0x160000 | correct rows | corrupt rows | wrap target | transparent px/occ |
|---|---|---|---|---|---|---|
| **Normal 0417** | `0x15FFE8` | **24** | 0–5 | **6–7** | `0x140000` | **8** |
| **0417_do** (+0x10) | `0x15FFF8` | **8** | 0–1 | **2–7** | `0x140000..0x140017` | **23** |

Both match Cody's reconstructed figures and defect masks exactly. `_do` is worse **only** because its
linked layout shifts the tile corpus **+0x10**, so a different (larger) portion of the *same* 32-byte
tile falls past the boundary — a **static layout/addressing** effect, not a raster-timing effect. All
six Segment-2 occurrences reference the same shared VRAM pattern slot, so the same corrupted
transparency mask appears at all six, over differing Layer-B artwork — exactly as annotated.

## Why my prior theory was wrong (for these six holes)

The active-display-DMA theory predicted the bad rows are determined by **raster/DMA overlap** and
would therefore vary with scanout timing. Cody disproved that for this defect: (1) the corruption mask
is **fixed relative to the pattern**, not the raster; (2) the exact bad rows are predicted **solely**
by the ROM source address vs the `0x160000` boundary; (3) the exact zero-nibble mask is predicted by
the bytes at the wrapped source `0x140000`; (4) normal vs `_do` differ **exactly** by their `+0x10`
link displacement; (5) at the owner-comparable frame **no** publication/DMA overlaps the six target
scanline ranges; (6) all six name words are correct and stable; (7) the corrupted bytes exist **inside
the shared A-0154 pattern in settled VRAM on real hardware**. **Active-display DMA is NOT the root
cause of the six A-0154 holes.**

## Why MAME misled the investigation

MAME continued the DMA source **linearly** across `0x160000`, loading the intended 32 bytes → correct
settled VRAM, correct A-0154 pattern, no zero nibbles. Real hardware **wraps to `0x140000`**, so its
settled pattern bytes are corrupted. This is why terminal VRAM inspection (correct for MAME)
contradicted Tighe's hardware observation. The instrumentation was internally correct **for MAME**;
the emulator does not reproduce this VDP DMA source-bank wrap. **Real Genesis is authoritative; MAME
is instrumentation only** — and here it under-reproduced the hardware behavior.

## What remains true from my prior review — SEPARATE PERFORMANCE / PUBLICATION ISSUE, NOT THE A-0154 ROOT CAUSE

These prior findings stand as **independent** topics and must **not** be cited as the cause of the six
A-0154 holes:
- Publication frequently **overruns VBlank** into active display under heavy scroll (IRQ ~180–230K vs
  128,009 budget). — real, tracked as a performance issue.
- **Active-display VRAM DMA** operations occur. — real; a latent correctness/perf risk.
- `_do` **forced-black diagnostic bands**. — real; a diagnostic, not this defect.
- The separately proven **one-frame `0x6297`→`0x63A4` entrance name transient**. — real; a distinct
  transient, not the six persistent holes.

Do the six persistent A-0154 holes come from any of these? **NO.** They are the ROM-source DMA
boundary wrap above.

## Correct repair direction (design only — Build 0418 scope)

1. Make ROM-source VDP DMA **128-KiB-boundary safe**.
2. Preserve the normal **one-DMA fast path**.
3. **Split only** transfers that actually cross a `0x20000`-byte source boundary.
4. **32-byte-align** the fixed PC080SN tile corpus (`genesistan_pc080sn_tile_rom`): since `0x20000` is
   a multiple of 32, a 32-byte-aligned corpus guarantees each `code*32` tile lies wholly within one
   source bank. (The rationale is already noted at the corpus definition, `scene_load.s:189-190`; the
   0417 corpus base `0x15DD08` is **not** 32-aligned, which is why 0x117 straddled `0x160000`.)
The generic boundary-safe split remains the safety net for arbitrary transfers.

**DOCUMENTATION RECONCILED: YES. PRODUCTION MODIFIED: NO. ROM BUILT: NO. BUILD NUMBER CONSUMED: NO.**
