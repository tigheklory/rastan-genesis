# Andy — Attract / Frontend IRQ6 Overrun + Genesis-Shaped Presentation Audit

**Date:** 2026-10-17 · **Agent:** Andy · **Type:** READ-ONLY architecture/performance/semantic audit.
**No** production source/Makefile/generator change, **no** ROM, **no** MAME, **no** new trace/route,
**no** build number/counter change, **no** implementation. Phase D/E not started; HUD/framing not
resumed; Cody's production/scroll work untouched.

**Baseline:** Build **0439** (counter 439; commit `1c35dc96` "Record Build 0439 hardware
acceptance"). No uncommitted production changes were present; none were modified.

**Tool reuse (RULES §18):** reused current source (`vdp_comm.s`, `dma.s`, `pc090oj_hooks.s`,
`tilemap_hooks.s`, `scene_load.s`, `palette_hooks.s`), existing design reports, and the Tighe-supplied
`_d` screenshots. New tooling: none.

**Evidence tags:** **[SRC]** current Build-0439 source · **[OBS]** Tighe screenshots · **[INFER]**
reasoned · **[MEASURE]** needs a run to confirm (no run performed).

---

## 1. EXECUTIVE RESULT

**Attract/frontend materially less Genesis-shaped than gameplay: PARTIAL — and NOT where the
hypothesis expected.**

- The `_d` green band is specifically the **Genesis VBlank *publication* phase** (`dma_publish_frame`),
  **not** the arcade worker. The bar is set green immediately before `bsr dma_publish_frame` and black
  immediately after, and the arcade frame worker runs *after* that, via `jmp (0x3A208)`, with the
  backdrop already black. **[SRC vdp_comm.s:185-203,251]** So a green band means **publication DMA/VDP
  work bled into active display**, not CPU-heavy arcade logic.
- **The attract BACKGROUND / text plane is already Genesis-shaped (entry-loaded), not rebuilt per
  frame.** Both PC080SN scroll-fill hooks (`genesistan_hook_pc080sn_bg_scroll_fill` /
  `..._fg_scroll_fill`) are **no-op stubs** **[SRC tilemap_hooks.s]**, and scene backgrounds are loaded
  once on entry via the `genesistan_scene_preload_*` tables + `load_scene_tiles` **[SRC scene_load.s]**.
  The arcade's per-frame full-plane PC080SN redraw (confirmed arcade behavior:
  `docs/design/build296_attract_progression_and_text_position_audit.md` §5 — "advances dest_ptr by
  0x4000 each call, one full plane") is therefore **not** translated per frame in the current asm era.
- **The frontend SPRITE path is the remaining non-Genesis-shaped piece:** it **rebuilds the SAT every
  VBlank** (`vdp_prepare_sprites → pc090oj_native_emit_pass`, because no arcade dispatcher sets
  `pc090oj_sat_frame_ready` in frontend) and **re-DMAs the SAT every frame** unconditionally. **[SRC
  pc090oj_hooks.s:3246-3252, .Lvcs_sat_dma]** Sprite *patterns* are residency-gated (not re-uploaded on
  a static screen) **[SRC]**, and palette is dirty-gated by `palette_pending` **[SRC dma.s
  vdp_commit_palette]** — so those two are not the per-frame cost.
- **Mismatch to flag honestly:** the small unconditional per-frame publication I can see in source
  (SAT DMA ≈ 640 bytes + scroll) does **not** by itself account for the *multi-scanline* green band in
  the screenshots. Either (a) a frontend plane/SAT path re-publishes more than the 640-byte SAT per
  frame, or (b) sprite-pattern residency does not persist across frames on these specific screens.
  **The existing `VC_MARK 0..6`/`vblank_vc` per-stage instrumentation in `dma_publish_frame` already
  measures exactly which stage overruns** **[SRC dma.s]**; reading it on each attract screen is the
  one missing measurement (not run here). **[MEASURE]**

**Bottom line:** The attract overrun is a **publication** problem, so **Phase E (moving the arcade
worker out of IRQ6) would not fix it**. The first bounded fix is to make the **frontend sprite
publication change-driven** (build the SAT once on screen entry, re-publish only on genuine change),
after reading the existing per-stage instrument to confirm the dominant stage.

---

## 2. ATTRACT SCREEN / STATE MAP

Scene id = `genesistan_current_scene_id`; the emit dispatch is in `pc090oj_native_emit_pass`.
**[SRC pc090oj_hooks.s]**

| Screen | Arcade driver | Scene id | Background | Text | Sprites | Per-frame emit path |
|---|---|---|---|---|---|---|
| Title / RASTAN logo | arcade attract state, stage `A5+0x0118==0` | scene 0 title-active | entry-loaded (`scene_preload_title`) | native glyph labels (`.Lnq_title_labels`) + live score/high-score digits | `.Lnq_title` → `native_frontend_hud_emit` | **full SAT rebuilt every VBlank** |
| Story / intro (seated king) | attract advanced (stage≠0) | scene 2 / frontend-native | entry-loaded | plane (entry) + flashing INSERT COIN credit | `.Lnq_frontend_native` → `native_frontend_hud_emit` + `.Lnq_transient_items_emit` | **full SAT rebuilt every VBlank** |
| BEST 5 / ranking | attract advanced | frontend-native | entry-loaded | plane (entry) | `.Lnq_frontend_native` | **full SAT rebuilt every VBlank** |
| Instruction / item | attract advanced | frontend-native | entry-loaded | plane (entry) | `.Lnq_frontend_native` (+ item icons via transient-items) | **full SAT rebuilt every VBlank** |

Attract mode is **not** monolithic: title-active uses `.Lnq_title`; the sub-screens use
`.Lnq_frontend_native`. Both rebuild the SAT each VBlank.

---

## 3. CURRENT FRAME PATH PER SCREEN

One IRQ6 (`_vblank_service`) frame **[SRC vdp_comm.s:176-251]**:

1. `rastan_direct_update_inputs`
2. `vdp_prepare_sprites` → in frontend, `pc090oj_native_emit_pass` **rebuilds the whole staged SAT**
   (clears `pc090oj_cell_used`, re-emits every frontend piece), sets `sat_frame_ready`. *(CPU; outside
   the green bar.)*
3. **[green bar ON]** `dma_publish_frame`:
   - `vdp_commit_palette` — CRAM DMA **only if `palette_pending`** (dirty-gated).
   - `vdp_commit_tiles_if_dirty` — VRAM tile PIO, dirty-gated.
   - `vdp_commit_bg_strips_if_dirty` — Plane B rows, **dirty-gated** (`bg_row_dirty`/`bg_col_dirty`).
   - `vdp_commit_fg_narrow_strips` — Plane A, **dirty-gated** (`fg_row_dirty`/`fg_col_dirty`).
   - `vdp_commit_sprites_vram` — tile-DMA worklist (dirty/residency) **+ SAT DMA (640 bytes,
     unconditional whenever `sat_frame_ready`)**.
   - `vdp_commit_scroll` — HScroll/VSRAM.
   **[green bar OFF]**
4. V-counter metric (`_score` variant) records peak overrun scanline into the 1UP HUD.
5. `jmp (0x3A208)` → the full arcade frontend worker runs (CPU; **outside** the bar).

**Recalculated every frame even on a static screen:** the **frontend SAT** (step 2 CPU + step 3 DMA).
Everything else in step 3 is dirty/residency-gated and should be ~0 on a static screen **[INFER from
SRC]** — which is the crux of the honest mismatch in §1/§12.

---

## 4. IRQ6 WORK BREAKDOWN

| Work | In the green bar? | Static-screen cost | Notes |
|---|---|---|---|
| Arcade frontend worker (full tick) | **NO** (runs after bar) | large CPU | Phase-E target; not the band |
| Input refresh | NO | tiny | before bar |
| Frontend SAT rebuild (CPU) | NO | moderate CPU | before bar; still wasteful at 60 Hz |
| Palette CRAM DMA | YES | 0 if unchanged | gated `palette_pending` |
| Plane A/B strip DMA | YES | 0 if unchanged | dirty-gated |
| Sprite pattern DMA | YES | ~0 after entry | residency-gated |
| **SAT DMA** | **YES** | **640 B/frame** | unconditional in frontend |
| Scroll | YES | tiny | — |

The **only** proven unconditional in-bar cost on a static attract screen is the 640-byte SAT DMA. That
is too small to explain the observed band → see §12/§14 for the measurement that closes the gap.

---

## 5. FRONTEND PC080SN / PC090OJ LEGACY AUDIT

| Path | Class | Detail |
|---|---|---|
| PC080SN BG/FG scroll-fill hooks | **DEAD (no-op stub)** | arcade per-frame plane writes are not translated; background is entry-loaded |
| PC080SN descriptor rebuild / directional dispatch | RETAINED ARCADE SEMANTIC | updates retained records/scroll on scene/record change; not a per-frame full-plane fill |
| Frontend sprite emit `.Lnq_title` / `.Lnq_frontend_native` | NATIVE GENESIS PRESENTATION | native HUD/label/item emitters into the shared SAT builder; **no** `pc090oj_object_ram`, no `0xD00000` park |
| Frontend PC090OJ object-RAM scan | **TRANSLATION-SHAPED remnant (mostly bypassed)** | `pc090oj_hooks.s` notes the object-RAM scan "remains physically present for frontend/non-gameplay comparison only" (line ~279); the active sub-screen path uses the native emitters, so it is largely dead but not deleted |

There is **no** attract-only full-map projection, virtual chip-RAM, or C-window shadow driving the
planes per frame. The historical PC080SN/PC090OJ tails are gone from the live attract path; the only
residue is the physically-present-but-bypassed frontend object-RAM scan.

---

## 6. STATIC-VS-DYNAMIC CONTENT CLASSIFICATION

| Element | Classification | Changes when |
|---|---|---|
| Background/text plane (all screens) | **REQUIRED ONLY ON SCREEN ENTRY** | scene change (already entry-loaded) |
| RASTAN logo / sword, seated king, item icons | REQUIRED ONLY ON SCREEN ENTRY | scene change (patterns residency-persist) |
| Score / high-score digits | REQUIRED ONLY WHEN CONTENT CHANGES | a credited coin / new high score |
| Flashing INSERT COIN(S) credit | REQUIRED ONLY ON ~30-frame toggle | blink cadence |
| **Frontend SAT (whole table)** | **currently REQUIRED EVERY FRAME; should be ENTRY + change-driven** | nothing, on a static screen |
| Palette | REQUIRED ONLY ON PALETTE CHANGE | already gated |

The single clear 60 Hz waste is rebuilding/re-publishing the **whole frontend SAT** when, for most
attract frames, no sprite changed except a periodic credit blink and occasional score digit.

---

## 7. TEXT PATH

Attract text splits in two **[SRC]**:

- **Large static blocks** (story paragraphs, BEST 5 table, item names/descriptions): **plane text,
  entry-loaded** (scroll-fill hooks stubbed; scene preload). **Not** rebuilt per frame, **not** runtime
  character-translated per frame on the live path. No change needed; do not touch copy/content.
- **HUD labels + score/credit** (1UP, HIGH SCORE, 2UP, scores, INSERT COIN): emitted as **native glyph
  sprites** every VBlank via `native_frontend_hud_emit` / `.Lnq_title_labels` (semantic `{Y,X,glyph}`).
  These are part of the per-frame SAT rebuild (§6).

No evidence of per-frame whole-plane text re-raster on the live path. **[SRC]**

---

## 8. SPRITE PATH

Frontend sprites use the **same native SAT builder + residency** as gameplay (no separate interpreter,
no PC090OJ-shaped path on the live sub-screen route) **[SRC]**. The difference from gameplay is the
**trigger**: gameplay stages the SAT from the arcade sprite dispatcher and sets `sat_frame_ready`;
frontend has no such dispatcher, so `vdp_prepare_sprites` re-emits the **entire** SAT every VBlank and
the SAT is DMA'd every frame. Patterns are residency-gated (persist across frames) so a static screen
should not re-upload them. **The repeated per-frame work to eliminate is the unconditional
full-SAT rebuild + SAT DMA.**

---

## 9. BACKGROUND / TILEMAP PATH

Plane A and Plane B are **static per attract screen** and **entry-loaded** (scene preload;
scroll-fill hooks stubbed). On a static attract frame, `bg_row_dirty`/`fg_row_dirty`/column dirty
should be 0 and the strip commits publish nothing. **[SRC]** This is already the Genesis-shaped target
for backgrounds — the audit found **no** per-frame full-plane rebuild on the live attract path. (If
`[MEASURE]` shows plane DMA is in fact nonzero per frame on an attract screen, the suspect is a
scene-present/`genesistan_scene_present_pending` path re-marking the plane dirty every frame; that
would be the real culprit and is the first thing the VC_MARK breakdown would reveal.)

---

## 10. PALETTE PATH

`vdp_commit_palette` is **gated by `palette_pending`** and DMAs 64 CRAM words only when a palette word
changed. **[SRC dma.s]** Static attract screens with no fade/cycle pay **zero** palette cost. (The
historical "unconditional Build 0336 CRAM DMA" comment in `vdp_comm.s` is superseded by the current
gated `dma.s` implementation.) No change recommended.

---

## 11. DMA / STAGING COST (static attract frame, source-derived)

| Channel | Bytes/frame (static screen) | Basis |
|---|---|---|
| Palette CRAM | 0 (unless changed) | gated `palette_pending` |
| Plane A | 0 (unless dirty) | dirty-gated |
| Plane B | 0 (unless dirty) | dirty-gated |
| Sprite patterns | ~0 after entry | residency-gated |
| **SAT** | **640 B** | unconditional whenever `sat_frame_ready` (frontend sets it every VBlank) |
| Scroll (HScroll/VSRAM) | tens of bytes | per-frame |

Inherently needed: scroll + SAT when a sprite actually changed. Caused only by republishing unchanged
content: **the SAT every frame**. The 640-byte SAT alone cannot explain a wide green band, so the
`[MEASURE]` step must confirm whether an additional per-frame plane/pattern DMA is occurring that the
static read did not surface.

---

## 12. WHY `_d` GOES GREEN

Ranked, source-backed:

1. **Publication (not CPU) extends past VBlank** — the band is `dma_publish_frame` by construction
   (§1). **[SRC, high confidence]**
2. **Unconditional per-frame frontend SAT republish** — the one proven 60 Hz publication cost that a
   static screen should not pay. **[SRC, high confidence it exists; MEASURE for magnitude]**
3. **A larger-than-SAT per-frame DMA not visible in the static read** — candidate: a scene-present or
   frontend plane path re-marking rows dirty, or non-persistent sprite-pattern residency on these
   screens. **[INFER; must be confirmed/denied by the existing `VC_MARK`/`vblank_vc` per-stage read
   and a `_do` comparison — MEASURE]**

**Do not blame "DMA/graphics" generically:** backgrounds are entry-loaded, palette is gated, patterns
are residency-gated. The proven unconditional cost is the SAT; any remainder must be measured, and the
instrument already exists.

---

## 13. PHASE-D/E SEPARATION

The whole arcade frontend worker currently runs inside IRQ6 **[SRC: `jmp (0x3A208)`]**, and Phase E
eventually moves it to arcade-owned mainline. **But the green band is the publication phase, which
runs _before_ that worker and does not include it.** Therefore:

- **Phase E would NOT resolve the observed `_d` attract overruns** — they are DMA/publication, not the
  arcade-worker CPU. **[high confidence]**
- The per-frame **SAT republish** (and any measured extra per-frame DMA) would remain after Phase E and
  must be made change-driven independently. Phase E is **not** an excuse to leave the unconditional
  frontend SAT republish in place.

---

## 14. GENESIS-SHAPED TARGET ARCHITECTURE

Arcade keeps sequencing/timers/which-screen/score/story; Genesis owns native representation + change
-driven publication. Backgrounds already meet this. The target for the frontend **sprite** layer:

```
arcade says: title / story page N / ranking / instruction
   -> Genesis frontend producer builds the native SAT (+ patterns) ONCE on scene entry
   -> subsequent frames: re-emit/re-publish ONLY genuinely dynamic sprites
        (credit blink toggle, score/high-score digit change)
   -> VBlank publishes only the changed SAT entries (or skips SAT DMA entirely when unchanged)
```

Mechanism per element: title logo/king/item icons = **static SAT descriptors built on entry**; score
digits = **change-driven re-emit**; credit blink = **toggle-driven re-emit**; SAT DMA = **gated on a
`sat_dirty`/`sat_frame_ready` that is set only when an entry actually changed**, exactly as gameplay
already gates planes/palette. No Genesis-owned attract state machine; arcade still sequences.

---

## 15. RECOMMENDED FIRST BOUNDED IMPLEMENTATION

**Step 0 (measurement, no code):** on the `_score`/`_d` builds, read the existing `vblank_vc`
(`VC_MARK 0..6`) per-stage V-counter and the `diag_servicing_peak` on the **title** screen and one
sub-screen, and compare `_d` vs `_do`. This attributes the band to a stage in minutes and confirms
whether the cost is the SAT alone or an additional plane/pattern DMA. (Tighe/authorized run; this audit
performed none.)

**Step 1 (first conversion) — make the frontend SAT publication change-driven, starting with the
TITLE screen.** Rationale: most static (only the credit blink + score digits change), strongest
evidence, lowest semantic risk (title emitters are already native and bounded), easy before/after
(`_d` band on the title screen should shrink/disappear; title visuals unchanged).

- **Exact repeated work to eliminate:** `vdp_prepare_sprites` re-emitting the whole SAT and
  `vdp_commit_sprites_vram` DMA-ing the whole 640-byte SAT **every VBlank** while the title SAT is
  unchanged.
- **Proposed native replacement:** build the title SAT once on scene entry; set `sat_frame_ready`
  (and a new `sat_changed`) **only** when a title sprite actually changes (credit-blink toggle, or a
  score/high-score digit differs from the last emitted value); gate the SAT DMA on that flag — mirroring
  how planes/palette are already dirty-gated. Keep the arcade in control of blink cadence and score
  values; do not cache content or hard-code the frontend.
- **Invariants:** arcade sequencing authoritative; no Genesis-owned frontend state machine; no change
  to copy, layout, palette, or background; gameplay SAT path unchanged.

Then repeat for the sub-screens once the title result validates the pattern. Do **not** rewrite all of
attract at once.

---

## FINAL STATUS

Production source modified: NO. Makefile/generators modified: NO. ROM built: NO. MAME run: NO. New
trace/route: NO. Build number consumed: NO. Build counter changed: NO. Cody scroll/production work
modified: NO. HUD/framing resumed: NO. Phase D: NO. Phase E: NO.
