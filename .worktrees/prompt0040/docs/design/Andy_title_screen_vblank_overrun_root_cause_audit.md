# Andy — TITLE SCREEN ONLY: `_d` / `_do` VBlank Overrun Root-Cause Audit

**Date:** 2026-10-17 · **Agent:** Andy · **Type:** READ-ONLY, TITLE-SCREEN-ONLY performance
root-cause audit. **No** production source/Makefile/generator change, **no** ROM, **no** MAME, **no**
new trace/route, **no** build number/counter change, **no** implementation. Phase D/E not started;
HUD/framing not resumed; Cody's production (Build 0440/0441 damage + `_invincible`) untouched.

**Baseline:** Build **0441** (counter 441; commit `9f07b5dc` "Build 441 — Relocate enemy damage
dispatch table"). Title path is unchanged by 0440/0441 (those are damage-chain fixes).

**Scope:** TITLE screen only. Story / BEST 5 / instruction are referenced only where a shared routine
must be named; no recommendation is made for them.

**Tool reuse (RULES §18):** reused current source (`vdp_comm.s`, `dma.s`, `pc090oj_hooks.s`,
`tilemap_hooks.s`, `scene_load.s`), the Tighe `_d`/`_do` screenshots, and prior reports
(`Andy_pure_publisher_audit_palette_gating_and_opt003.md`,
`Andy_build0264_live_native_title_sprite_producers.md`, `build296_attract_progression_...`). New
tooling: none. No run performed.

**Evidence tags:** **[SRC]** current Build-0441 source · **[DOC]** prior report · **[OBS]** Tighe
screenshots · **[INFER]** reasoned · **[MEASURE]** needs one runtime read (not performed).

> **Correction to my prior attract audit:** I earlier wrote that the title *background is
> entry-loaded* because the PC080SN **scroll-fill** hooks are stubbed. That was over-generalized. The
> title **tile patterns** are entry-loaded (scene preload), but the title **name-table (plane map)**
> is published through the **active** `genesistan_hook_tilemap_bg_fill` / `genesistan_hook_tilemap_fg_fill`
> C-window interceptors, which re-stage and re-dirty rows for whatever the arcade writes — **every
> frame**. That per-frame plane republish, not the 640-byte SAT, is the dominant band. **[SRC]**

---

## 1. EXECUTIVE RESULT

- **`_d`** = diagnostic CPU-load bar: `_vblank_service` sets the VDP **backdrop (CRAM 0) green
  immediately before `bsr dma_publish_frame` and black immediately after** (display stays ON). The
  green band = `dma_publish_frame` duration, shown wherever the title is transparent. **[SRC
  vdp_comm.s:185-203]**
- **`_do`** = display-off variant: `dma_publish_frame` sets **display OFF at entry and ON at exit**
  (`VDP_REG1_DISPLAY_OFF 0x8134` / `_ON 0x8174`). The black band = the display-off window = the same
  `dma_publish_frame` duration, but run at **full forced-blank DMA bandwidth**. **[SRC dma.s:32-33,
  74-93]**
- **Why `_do` (black) < `_d` (green):** identical publication *volume*, different *rate*. With display
  ON (`_d`), VRAM DMA competes with active-display fetches and runs slower → the interval stretches
  further into active scanlines → **wider**. With display OFF (`_do`), DMA runs at full blanking
  bandwidth → the same bytes finish sooner → **thinner**. It is **not** that display-off "does less";
  it does the **same** transfer faster. **[SRC + Genesis VDP behavior; DOC pure-publisher §5]**
- **What the remaining `_do` black band proves:** even under the *most favorable* publication
  condition the VDP offers (forced blank), the title publication **still overruns into visible
  scanlines (down to the sword hilt)**. Therefore the title is transferring a **genuinely large,
  unnecessary volume** every frame — it is a workload problem, not a contention artifact. **[OBS +
  INFER]**
- **Dominant cause:** the title **plane name-table is re-staged and re-DMA'd every frame**. The arcade
  title tick re-writes the PC080SN C-window (frontend has no native row-producer replacement, unlike
  gameplay), the active `genesistan_hook_tilemap_bg_fill`/`_fg_fill` interceptors mark rows dirty, and
  `dma_publish_frame` re-DMAs up to **32 BG + 32 FG rows × 64 words** — the exact "plane transfer
  volume" the prior pure-publisher audit identified as the `_do` band driver. The unconditional
  **640-byte SAT re-DMA** is a secondary, smaller contributor. **[SRC + DOC pure-publisher §4-5;
  one VC_MARK read confirms the split — §Existing Instrumentation]**
- **This is architectural design debt, not a regression:** the black band has existed since `_do`
  (Build 0344) because the frontend plane has always been republished per frame via the faithful
  PC080SN→plane translation; gameplay was later converted to a change-driven native row producer,
  frontend was not. **[DOC pure-publisher; build296]**

---

## 2. EXACT `_d` AND `_do` MEASUREMENT INTERVALS

| Variant | Register/state changed | When set | When restored | Measures |
|---|---|---|---|---|
| `_d` (`RASTAN_DIAG_CPU_BAR`) | CRAM entry 0 (backdrop) → green `0x00E0` | start of `_vblank_service`, just before `dma_publish_frame` | → black `0x0000` immediately after `dma_publish_frame` | **`dma_publish_frame` duration**, display ON (DMA throttled by active display) |
| `_do` (`RASTAN_VBLANK_DISPLAY_OFF`) | VDP reg1 → display OFF `0x8134` | **inside** `dma_publish_frame` entry | → display ON `0x8174` at `dma_publish_frame` exit | **same `dma_publish_frame` duration**, display OFF (full blank DMA bandwidth) |

Both bracket the **same** code (`dma_publish_frame`'s six commits). Neither includes the arcade
worker, which runs **after** publication via `jmp (0x3A208)` with the backdrop already black / display
already on. **[SRC vdp_comm.s:251]** So **neither band is the arcade worker**, and **Phase E would not
shrink either band** — both are the Genesis publication/DMA phase.

Disabling display does **not** change the DMA *volume* or the producers; it changes only the VRAM DMA
*rate* (blanking vs. active). **[SRC; VDP behavior]**

---

## 3. `_do` ORIGIN / HISTORY

- `_do` is the **Build 0344** display-off variant (Rainbow-Islands model), introduced to run the
  publication at full forced-blank bandwidth "SAFE only once the whole phase fits the vblank window;
  before that it visibly blanks part of the picture (a useful overrun diagnostic)." **[SRC dma.s:74-77
  comment]**
- The **title black band was present from the first `_do`** and is explicitly characterized in
  `Andy_pure_publisher_audit_palette_gating_and_opt003.md` (2026-09-05) §5: *"The `_do` black band is
  transfer VOLUME … dominated by plane transfer volume (up to 32 dirty BG rows + 32 dirty FG rows of 64
  words each)."* **[DOC]**
- **Has the size changed?** The one publication change since (`palette_pending` gating, §Q3) removed an
  unconditional 64-word CRAM DMA — a small reduction — and was later restored after the OPT-003 gate
  artifact was understood. The **plane republish workload is unchanged** since `_do` introduction.
  **[DOC pure-publisher §6-7]**
- **Conclusion:** architectural debt, **not** a Build-0439/0440/0441 regression. **Consistent with
  evidence.**

---

## 4. EXACT TITLE FRAME TIMELINE (Q1)

IRQ6 `_vblank_service` **[SRC vdp_comm.s:176-251, dma.s dma_publish_frame]**:

| # | Operation | Kind | In `_d` green / `_do` black? |
|---|---|---|---|
| 1 | `rastan_direct_update_inputs` | CPU | no (before bar) |
| 2 | `vdp_prepare_sprites` → `pc090oj_native_emit_pass` (`.Lnq_title`): rebuild staged SAT | CPU | no (before bar) |
| 3a | **bar ON** / **display OFF** | reg write | boundary |
| 3b | `vdp_commit_palette` (`VC_MARK 0→1`) | CRAM DMA **iff `palette_pending`** | YES |
| 3c | `vdp_commit_tiles_if_dirty` (`1→2`) | VRAM PIO iff `tiles_dirty` | YES |
| 3d | `vdp_commit_bg_strips_if_dirty` (`2→3`) | **Plane B row DMAs (dirty)** | YES |
| 3e | `vdp_commit_fg_narrow_strips` (`3→4`) | **Plane A row DMAs (dirty) + narrow PIO** | YES |
| 3f | `vdp_commit_sprites_vram` (`4→5`) | tile-worklist DMA (≤12) + **SAT DMA (640 B)** | YES |
| 3g | `vdp_commit_scroll` (`5→6`) | HScroll PIO + VSRAM | YES |
| 3h | **bar OFF** / **display ON** | reg write | boundary |
| 4 | V-counter metric (`_score`) | CPU | no |
| 5 | `jmp (0x3A208)` → arcade title tick (PRODUCERS for next frame: PC080SN C-window writes → fill hooks → `staged_*` + row dirty; SAT emit next VBlank) | CPU | no (after bar) |

The band = steps 3b–3g. The large members are **3d + 3e (plane DMA)**; 3f adds the 640-byte SAT.

---

## 5. WHAT ACTUALLY CHANGES ON AN ORDINARY TITLE FRAME (Q2)

| Element | Representation | Classification |
|---|---|---|
| RASTAN logo / sword art | PC080SN plane (name-table + preloaded patterns) | **STATIC** |
| TAITO / © text, "ALL RIGHTS RESERVED" | PC080SN plane | **STATIC** |
| 1UP / HIGH SCORE / 2UP labels | native glyph sprites (`.Lnq_title_labels`) | **STATIC** |
| P1 / high-score digits | native sprites, regenerated from live BCD each frame | **PERIODICALLY CHANGING** (only on a credited coin / new high score; on the pure title they are `00`/fixed) |
| INSERT COIN(S) credit text | plane or native, blink | **PERIODICALLY CHANGING** (~every N frames) |
| Palette | `staged_palette_words` | **STATIC** (no fade on title) |
| Plane A / Plane B name-table | staged buffers | content STATIC; **republished every frame (defect)** |
| SAT | staged, double-buffered | content STATIC; **rebuilt + DMA'd every frame (defect)** |
| Scroll / VSRAM | staged | STATIC value, written per frame (cheap) |

On a steady title frame **almost nothing visible changes** — only the periodic credit blink and (if
any) a score digit. Everything else is static. **[SRC + OBS]**

---

## 6. EXACT VBLANK PUBLICATION ON A STATIC TITLE FRAME (Q3)

Per-stage, for a title frame where nothing visible changed **[SRC dma.s; DOC pure-publisher §4]**:

| Stage | Executes? | Bytes | Type | Why the condition is (not) met |
|---|---|---|---|---|
| `vdp_commit_palette` | **No** (static) | 0 | — | `palette_pending` clear once the title palette settled |
| `vdp_commit_tiles_if_dirty` | No | 0 | — | `tiles_dirty` clear |
| `vdp_commit_bg_strips_if_dirty` | **YES** | **up to 32 rows × 64 w = 4096 w (8192 B)** | row DMAs | `bg_row_dirty` **re-set every frame** by `genesistan_hook_tilemap_bg_fill` as the arcade re-writes the BG C-window |
| `vdp_commit_fg_narrow_strips` | **YES** | **up to 32 rows × 64 w = 8192 B** (+ narrow PIO) | row DMAs | `fg_row_dirty` re-set by `genesistan_hook_tilemap_fg_fill` likewise |
| `vdp_commit_sprites_vram` | **YES** | tile worklist ≤12×128 B + **SAT 640 B** | DMA | `pc090oj_sat_frame_ready` re-set every VBlank by the frontend emit; patterns residency-gated (≈0 after entry) |
| `vdp_commit_scroll` | YES | tens of B | PIO/VSRAM | per-frame |

**Statically provable republish on an unchanged title frame:** the SAT (640 B) is certain; the plane
DMA is the dominant term **iff** the arcade re-writes the title C-window every frame (strongly implied
by the persistent band, confirmed by one VC_MARK read). The exact dirty-row *count* each frame
(whether all 64 or a subset) is the one value I cannot derive statically — **[MEASURE]** `vblank_vc`.

---

## 7. VERIFY/REFUTE THE PRIOR SAT THEORY (Q4)

The 640-byte SAT theory is **necessary but not sufficient**: 640 B ≈ a few scanlines of DMA and cannot
reach the sword hilt (~80 scanlines). The `_do` evidence (volume-dominated band at full bandwidth)
plus the active `*_fill` hooks point to **C (a plane is marked dirty/published despite appearing
static)** as the dominant cause — specifically the **title name-table re-published every frame**. The
SAT re-DMA is a real but secondary contributor. Options A/D/E/F are not supported: palette is gated
(§Q3), scene-present is not re-asserted on a stable title (§Q6), scroll is tiny, and no DMA/wait
interaction dominates beyond the plane volume. **[SRC + INFER; confirm split with VC_MARK]**

---

## 8. SPRITE RESIDENCY ON THE TITLE (Q5)

`.Lnq_title` → `native_frontend_hud_emit` clears only `pc090oj_cell_used` (the per-frame referenced
bitmap), **not** residency (`sprite_tile_resident_code`). Title sprite identities — label glyphs
(1UP/HIGH SCORE/2UP), score/credit digit glyphs — are a **small bounded set** that fits residency and
**persists across frames**; the tile-DMA worklist (`pc090oj_tile_dma_count`) is therefore **empty on a
stable title frame**, so **patterns are not re-uploaded**. The logo/sword art is **plane**, not
sprites (so no logo pattern churn). Credit blink / score change re-emits the SAT but does **not** evict
resident glyph patterns (same codes). **Conclusion: sprite-pattern DMA is ≈0 on a stable title; it is
NOT the cause.** **[SRC pc090oj_hooks.s `.Lnq_title`, `.Lvcs_tile_dma`; DOC Andy_build0264]**

---

## 9. PLANE DIRTY STATE ON THE TITLE (Q6)

Writers of the plane dirty flags **[SRC tilemap_hooks.s]**:

- `genesistan_hook_tilemap_bg_fill` / `genesistan_hook_tilemap_fg_fill` — set the affected row's dirty
  bit **per arcade C-window write**. These are **active** (address-range gated to the BG/FG C-window)
  and run inside the arcade title tick. **← the per-frame re-dirty source.**
- The scene-clear routine (`…:4166` `move.l #0xFFFFFFFF, bg_row_dirty/fg_row_dirty`) — full-plane
  dirty on **scene entry** only (fills both staged buffers with the clear tile). Not per-frame.
- `vdp_commit_bg_strips_if_dirty` / `vdp_commit_fg_narrow_strips` — **clear** the dirty mask after
  publishing (so a persistent band requires a per-frame **re-set**, which the `*_fill` hooks provide).

`genesistan_scene_present_pending` is set only in the scene-load/itempage path (`…:4663`), **not** on a
stable title frame. **[SRC]**

**Conclusion:** plane DMA is **NOT** cleared as a cause — on the title it is the leading cause,
re-dirtied every frame by the active C-window fill hooks as the arcade re-draws the title plane.

---

## 10. SAT READINESS / DIRTY CONTRACT (Q7)

The architecture tracks **"a valid SAT exists"** (`pc090oj_sat_frame_ready`) but **not** "the SAT
changed." In frontend, `vdp_prepare_sprites` sets `sat_frame_ready` every VBlank (no arcade dispatcher
did), and `vdp_commit_sprites_vram` DMAs the whole 640-byte SAT whenever ready. **There is no
`sat_changed`/dirty distinction** — that is the design flaw for static frontend screens. The smallest
Genesis-shaped contract: a **`sat_dirty`** flag set only when an emitted SAT entry differs from the
previously published one; DMA the SAT only when `sat_dirty`. (The plane path has the analogous need:
set the row dirty only when a staged name word actually changed.) **[SRC]**

---

## 11. `_do` DISPLAY-OFF EFFECT + WHAT THE BAND PROVES (Q8)

`_do` disables display before publication, which **removes active-display VRAM contention and grants
full forced-blank DMA bandwidth** — it does not change the producers, the DMA volume, or when the
arcade worker runs. It changes only the **rate** at which the same bytes transfer, so the same workload
finishes sooner (thinner band). Active display resumes when `dma_publish_frame` re-enables display.
**The remaining black band therefore proves the publication is moving a large volume (plane name-table
+ SAT) every frame that, under the best possible DMA conditions, still cannot fit the vblank window —
i.e., the republished-unchanged-content volume is the problem.** **[SRC + VDP behavior; OBS]**

---

## 12. WHY TITLE SHOULD FIT (Q9) — NECESSARY vs CURRENT

| | Plane A | Plane B | Palette | Patterns | SAT | Scroll |
|---|---|---|---|---|---|---|
| **NECESSARY (unchanged frame)** | 0 | 0 | 0 | 0 | 0 | tens of B |
| **CURRENT (unchanged frame)** | up to 8192 B | up to 8192 B | 0 (gated) | ≈0 | 640 B | tens of B |

A static title frame should publish **essentially nothing** (only scroll register maintenance, well
under one scanline). It currently republishes the full plane name-table and the SAT every frame. The
gap is the entire band. **[SRC + DOC]**

---

## 13. EXISTING INSTRUMENTATION / ONE MEASUREMENT

`dma_publish_frame` already records the V-counter at each stage boundary via `VC_MARK n` into
`vblank_vc` **[SRC dma.s]**. Mapping:

| Mark | Taken before | Delta `vblank_vc[n+1]-[n]` = cost of |
|---|---|---|
| 0 | palette | palette CRAM |
| 1 | tiles | tile PIO |
| 2 | BG strips | **Plane B DMA** |
| 3 | FG strips | **Plane A DMA** |
| 4 | sprites | pattern worklist + SAT |
| 5 | scroll | HScroll/VSRAM |
| 6 | (end) | — |

`diag_servicing_peak` (the `_score` variant) reports the worst overrun scanline as the 1UP number.

**One runtime measurement still required (title only):** on a stable title frame, read the 7 bytes/words
`vblank_vc[0..6]`. Expected if this audit is right: a large `[2]→[3]` (Plane B) and `[3]→[4]` (Plane A),
a small `[4]→[5]` (≈640 B SAT), ≈0 elsewhere. If instead `[4]→[5]` dominates, the cause is SAT/pattern,
not plane. **No gameplay benchmark; no new route — just read `vblank_vc` on the title.**

---

## 14. HISTORICAL vs CURRENT

The offending workload is **inherited from the frontend PC080SN→plane translation**: gameplay replaced
the arcade PC080SN background tail with a change-driven native row producer, but the **frontend/title
plane is still the faithful per-frame C-window translation** (active `*_fill` hooks). So it is
**long-standing architectural design debt**, present since `_do` was introduced, not a regression.
**[DOC pure-publisher; build296; SRC]**

---

## 15. RECOMMENDED TITLE-ONLY IMPLEMENTATION

**Add change-detection to the title plane publication (and SAT), so unchanged content is not
re-DMA'd. Do not implement in this task.**

- **Exact repeated work to remove:** (1) re-dirtying title plane rows every frame when the arcade
  re-writes identical name-table content; (2) the unconditional per-frame SAT re-DMA.
- **Exact contract to change:**
  - In `genesistan_hook_tilemap_bg_fill` / `genesistan_hook_tilemap_fg_fill`: before writing a staged
    name word, **compare it to the word already in `staged_bg_buffer`/`staged_fg_buffer`; set the row
    dirty bit only if it differs.** Static title content → identical word → **no dirty → no DMA**.
  - SAT: add a **`sat_dirty`** set only when an emitted SAT entry differs from the last published one;
    gate the SAT DMA on it. (Alternatively, build the title SAT once on scene entry and re-emit only on
    credit-blink/score change.)
- **Functions affected:** `genesistan_hook_tilemap_bg_fill`, `genesistan_hook_tilemap_fg_fill`
  (`tilemap_hooks.s`); the SAT readiness/commit in `vdp_prepare_sprites` / `vdp_commit_sprites_vram`
  (`pc090oj_hooks.s`). CPU-side compares that eliminate DMA-side transfers → **both CPU and DMA
  savings**, DMA-dominant.
- **Bytes BEFORE (static title):** up to ~16 KB plane + 640 B SAT. **AFTER:** ~0 plane + 0 SAT; only
  genuinely changed cells (credit blink, score digit) publish a few words.
- **Credit blink / score correctness:** when the arcade writes a *different* name word (blink toggles
  the credit text, or a digit changes), the compare detects the difference, dirties that row/cell, and
  it publishes normally. Nothing is cached or sequenced by Genesis; the arcade still owns timing/content.
- **Prove no visual difference:** the compare skips DMA only when the staged content is **byte-identical**
  to what is already in VRAM, so output is provably unchanged (static proof: the staged buffers and SAT
  are identical to the unoptimized build on every frame; only the dirty masks differ).
- **Expected `_d`:** green band collapses to near-zero on a stable title (only scroll).
- **Expected `_do`:** black band collapses to near-zero on a stable title.

**Dependency / caveat:** this is a **publication-timing change**, which `Andy_pure_publisher_audit…`
§7 showed trips the synthetic `build0310_epoch_gate` injection (now classified a **gate artifact**, not
a production bug). The title change-detection must be validated with that understanding (the gate's
injected active-LUT assertion needs the natural-transition correction before `make all` accepts
publication-timing changes). Flag this to Cody before implementation. No Genesis-owned attract state
machine, no replacement title sequence, no gameplay-semantic change.

---

## FINAL STATUS

Production source modified: NO. Makefile/generators modified: NO. ROM built: NO. MAME run: NO. New
trace/route: NO. Build number consumed: NO. Build counter changed: NO. Cody damage/`_invincible`/scroll
work modified: NO. HUD/framing resumed: NO. Phase D: NO. Phase E: NO.
