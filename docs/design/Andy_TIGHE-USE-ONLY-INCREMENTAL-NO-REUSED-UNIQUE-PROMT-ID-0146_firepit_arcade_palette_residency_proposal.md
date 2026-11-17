# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0146 — R1-S2 fire-pit arcade palette semantics, capacity, and faithful Genesis residency

**Author:** Andy (independent) · **Date:** 2026-11-16 · **Type:** forensic/design proposal — **READ-ONLY**.
No production source, no Palette Composer source, no `Test_2_0.json`, no ROM, no build number, no implementation.
Independent of Cody / Google Antigravity (their new proposals were not read). Built on my own prior proven
work (`Andy_r1s2_trap_graphics_sources.md`, `Andy_r1s2_traps_proven_authorable.md`) and re-verified here against
the live corpus/ROM. Colour authority remains `specs/palette_decisions.json`; this doc cites banks/indexes as a
graphics attribute and does not duplicate the index→RGB registry.

---

## Headline result (so the recommendation is legible up front)

1. The R1-S2 pit fire is **one 4×4 PC080SN Layer-A tile unit** (`$093A–$0949`, bank `0x014`, record 18),
   repeated across the pit. **There is no separate sprite "top flame" in R1-S2** (independent re-verification,
   §3) — the "animated flames on top" are the top rows of this one unit under the **mode-8 palette cycle**.
2. The fire uses **15 source indexes**, but at Genesis 9-bit colour depth these collapse to **exactly 10
   distinct colours (+ transparent)**. The merges are **forced by Genesis depth, not artistic**. So the fire
   fits **losslessly in one Genesis line** (10 of 15 usable slots).
3. It looks bad on Genesis for a structural reason: **all four Genesis CRAM lines are already committed**
   (0/1 = Test sprites, 2 = Layer-B, 3 = Layer-A master) and **there is no route-table entry for bank `0x14`**,
   so the fire tiles fall back to the Layer-A master line (castle structure colours) and the **mode-8 animation
   writes a non-existent Genesis line `0x14`** (dropped). The fire has no palette home.
4. The faithful translation is a **segment-scoped palette residency** (a "Palette Region") that gives the fire
   its own Genesis line only while the pit is on screen — directly analogous to the project's existing R2
   graphics-epoch residency and offline scene-asset packages. **Top recommendation: Strategy C on Line 3**
   (the Layer-A line the fire already belongs to), not a lease of the protected/actively-managed Line 2.

---

## 1. Exact fire-pit identity

- **Scene:** `PAL-R1-S2-PLANEA-CASTLE` (Round 1, Subround 2, the castle interior).
- **Hardware:** PC080SN **Layer A** (background plane) tiles. **Not** a sprite effect.
- **Collision/progression record:** **18** (`0x12`).
- **Geometry:** a **4 columns × 4 rows = 16-tile unit**, screen rows **28–31** (screen bottom, the pit mouth),
  **repeating every 4 columns** across tilemap column span 1160–1207 (108 placements per tile).
- **Animation:** the flicker is the **mode-8 palette cycle** over fixed tiles (§6), not moving pixels.
- Registry status: **no `specs/palette_decisions.json` entry exists** for the fire (bank `0x014` / line `0x14`).
  A new Palette Decision ID should be authored *when* a solution is implemented (not in this read-only task).

## 2. Layer-A inventory (the whole visible fire)

| field | value |
|---|---|
| tile codes | `$093A,$093B,…,$0949` (16 consecutive) |
| grid | row28: `$093A–$093D`; row29: `$093E–$0941`; row30: `$0942–$0945`; row31: `$0946–$0949` |
| palette bank | `0x014` (arcade), flip 0, priority n/a |
| record | 18 (`0x12`) |
| repetition | period 4 columns, 108 placements each |
| physical patterns | 16 distinct 8×8 4bpp tiles in `build/regions/pc080sn.bin` (code×32) |
| used source indexes | 15 of 16 (all but index 0 = transparent) — §5 |
| pixels / unit | 1024 non-transparent of 1024 (every non-0 nibble) |

The assembled unit decodes to an orange→yellow→white flame block (verified in the Palette Composer Layer-A
renderer, `render_layera_block`). This is the complete lower **and** upper fire; the top row (28) is simply the
top of this one unit.

## 3. Sprite inventory — **none for the fire** (independent re-verification of Tighe's claim)

Tighe's brief hypothesises "animated **sprite** flames along the top." The static evidence does **not** support a
sprite contributor to the R1-S2 pit fire:

- Record 18 carries Layer-A tiles **only at rows 28–31** (bank `0x014`); there is no tile row above the fire.
- The PC090OJ pit-flame actor **base `$0224`** is an **R2/R4** marker-chain actor, **retired in R1-S2** by the
  handler progress guard (`0x44082`: `if progress_13e < 0x18 …`; R1-S2 progress is `0x11–0x16`). It cannot be
  on screen in R1-S2.
- The only PC090OJ sprites near the pit in R1-S2 are the **`$09EA` spikes** (floor anim `0x79`, ceiling/crusher
  anim `0xD8`) and the coordinate-only **`$43ECC` 'M' burst** (anim `0x7A`, 5-child, no static base) — none is a
  fire cap.

**Conclusion:** the "animated flames on top" are the mode-8 colour cycle acting on the **top rows of the single
Layer-A unit**, not a sprite. This is a genuine divergence from the brief's working hypothesis and is reported
as such. *If* Tighe can point to a specific frame where a flame clearly renders above row 28 with sprite motion,
the one remaining dynamic check is an **ORIGINAL ARCADE PC090OJ sprite-RAM capture at the pit** (established
`tools/mame/` arcade tooling) — but the static roster shows no such sprite. Treat "sprite flames" as **not
supported** pending that capture.

## 4. Arcade palette-bank proof (bank `0x014`)

- **Static source:** the R1 Plane-A palette base `0x4EAF6`, bank slot `0x14` → `0x4EAF6 + 0x14*32 = 0x4ED76`
  (16 words). This is the colour set loaded for arcade CRAM **line `0x14`** at scene entry.
- **Destination surface:** arcade palette line `0x14` (the mode-8 fire/torch line).
- **Producer / consumers / lifetime:** **rewritten every cycle** by the **mode-8** palette animation
  (cycler `0x59962` → per-line loader `0x59AD4`/`arcade_59ad4`). The mode-8 **dest-line table `0x59A98`** (stage
  1) = `{0x14, 0x0F, 0x16, 0x03, 0x07, 0x09, …}` — i.e. the same animation also drives several **other warm
  banks** (torches/braziers), so line `0x14` is a **shared fire-family effect line**, not fire-pit-exclusive.
  Lifetime: active whenever the mode-8 cycler runs in the castle; **it is NOT static** — do not model it as a
  fixed palette.
- **Colour tables (evidence, not registry):** the cycle colours live in `0x59B1A` (warm ramp words with
  `0xFFFF` group separators). Static bank `0x014` colours (`0x4ED76`) = black + a warm ramp
  (`#F77300 #F78400 #F7A500 #F7D600 #F7F784 … #F7F7F7 … #F7F700`). Marked-used census in §5.

## 5. Source palette and used-index census (Genesis-depth reality)

Decoding the 16 fire tiles (`build/regions/pc080sn.bin`) and converting each used colour to Genesis CRAM
(`cram = (B<<9)|(G<<5)|(R<<1)`, 3-bit/channel):

| src idx | arcade RGB | Genesis CRAM | px | note |
|---:|---|---|---:|---|
| 0 | `#000000` | — | 0 | transparent |
| 1 | `#F77300` | `0x006E` | 7 | |
| 2 | `#F78400` | `0x008E` | 2 | |
| 3 | `#F7A500` | `0x00AE` | 34 | ← merges 12,13 |
| 4 | `#F7D600` | `0x00CE` | 83 | ← merges 14 |
| 5 | `#F7F784` | `0x08EE` | 209 | ← merges 11 |
| 6 | `#F7E784` | `0x08CE` | 214 | |
| 7 | `#F7F7F7` | `0x0EEE` | 179 | white |
| 8 | `#F7F7D6` | `0x0CEE` | 6 | |
| 9 | `#F7F7B5` | `0x0AEE` | 13 | ← merges 10 |
| 10 | `#F7F7A5` | `0x0AEE` | 45 | |
| 11 | `#F7F794` | `0x08EE` | 70 | |
| 12 | `#F7A500` | `0x00AE` | 13 | |
| 13 | `#F7B500` | `0x00AE` | 14 | |
| 14 | `#F7D600` | `0x00CE` | 55 | |
| 15 | `#F7F700` | `0x00EE` | 80 | |

**15 used source indexes → 10 distinct Genesis CRAM values** (`0x006E 0x008E 0x00AE 0x00CE 0x00EE 0x08CE 0x08EE
0x0AEE 0x0CEE 0x0EEE`). The four collisions (`3/12/13`, `4/14`, `5/11`, `9/10`) are **mandatory at Genesis
depth** — zero artistic loss. **The fire's exact Genesis requirement is 10 colours + transparent**, which fits
one 16-entry line with 5 slots to spare.

## 6. Animation semantics

- Mode-8 is a **palette cycle**: fixed tiles, rewritten colours. Loader `arcade_59ad4(table, src_row,
  dest_line)` writes `palette_ram_200000 + dest_line*16`. For the fire, `dest_line = 0x14`.
- The cycle rotates through the warm ramp groups in `0x59B1A` to produce the flicker (top of the flame flickers
  brightest because those tiles use the pale-yellow/white indexes 5,6,7,11).
- **On Genesis today:** `dest_line 0x14` = word offset `0x14*16` into the staged palette — **past the 4 live
  CRAM lines** — so the animation is written to dead staging and **never reaches the screen**. The fire is both
  mis-coloured (§9) **and** static. A faithful fix must give the fire a real Genesis line *and* (optionally)
  reproduce the cycle onto it.

## 7. Segment / record / scroll visibility window

- **Project record (= `a5@0x13e`):** **18 (`0x12`)**. R1 occupies records 1–22; R1-S1 outdoor = records 1–16;
  **R1-S2 castle = records `0x11–0x16` (17–22)**. The fire at record 18 (`0x12`) is the **second castle record**.
- **Tighe's "segment 18 / preload 17" maps cleanly:** record `0x11` (17) = castle entry = the correct preload
  boundary; record `0x12` (18) = fire active; release after the fire scrolls off (record `0x13`+).
- **Scroll position:** record 18's tiles sit at tilemap columns 1160–1207, rows 28–31. First-visible / last-
  visible scroll X can be derived from those columns × 8px minus the viewport width; the exact pixel envelope is
  a mechanical calc from the corpus coordinates (method, not yet run to a pixel here).

## 8. Checkpoint / reversal implications

- **Reversal:** the castle lets Rastan walk left a short distance, so a one-shot "entered record 18" test is
  **insufficient** — the fire can re-enter view. Residency must be **record-windowed** (arm at `0x11`, hold
  `0x11–0x13`, release after), keyed on the retained `a5@0x13e`, not a single scroll trip-wire.
- **Death/respawn:** the 0134/0136 work proves respawn re-enters scene 1 via `load_scene_tiles(scene 1)`; a fire
  residency must **re-arm on that same boundary** (and must not fight the Line-2 respawn logic — a reason to
  **avoid Line 2**). Whether a checkpoint sits before/within the fire window is a retained-state fact to confirm
  against the R1-S2 checkpoint record (flagged §22).
- **Direct-start / attract:** the residency is inert unless the window predicate holds, so both are safe.

## 9. Current Genesis mappings (root cause)

Gameplay (scene 1) line ownership, from `palette_route_table` (`apps/rastan-direct/src/palette_hooks.s`):

| Genesis line | owner | source |
|---|---|---|
| 0 | Test sprite palette | PC090OJ banks 0x32/0x33/0x34/0x3E (player/enemies) |
| 1 | Test sprite palette + FG carrier | 0x35/0x36/0x3A/0x4F + PC080SN FG bank 3 |
| 2 | **Layer-B** (per-round BG) — **PROTECTED** | arcade BG bank per round (0132/0134/0136) |
| 3 | **Layer-A master** (PC080SN FG) | the castle structure palette |

**Bank `0x14` has no row in the route table.** So (a) the fire **tiles** are drawn with the **Line-3 Layer-A
master** palette (castle greys/browns), not the warm ramp, and (b) the mode-8 write to line `0x14` is dropped
(§6). That is the complete reason the pit "looks substantially worse than the arcade." (The precise Genesis line
attribute baked into the generated fire tiles should be confirmed from the tile generator output; the route
table + the Line-3 master definition make Line 3 the current de-facto home regardless.)

## 10. L2 index occupancy / writer notes for the fire window

- Line 2 in R1-S2 = the **R1 Layer-B** palette (retained loader `FUN_00059de8`, bank 2 → Line 2), and in the
  **castle interior Layer-B is the outdoor tileset seen through windows** (sparse on-screen presence).
- **But L2 is actively written:** per-round load, the fade ramp rows (`0x5E24E[record]`), and the death/respawn
  reconstruction (0134/0136). **"Sparsely visible" ≠ "safe to overwrite."** An index not referenced by a
  visible cell this frame may still be rewritten by the retained loader or the respawn path. A precise
  per-index writer/consumer census over records `0x11–0x13` is the gate for any L2 lease (method §13), and
  0138/0141 explicitly stabilised L2 — **changing it is high-risk and is not recommended as the primary path.**

## 11. 4/5/6/7/8-colour reduction study (machine-suggested, greedy weighted merge)

Baseline = the 10 lossless Genesis colours (§5). Reductions collapse nearest colours (pixel-weighted); error in
RGB **level-units** (0–7 scale):

| target | max err | avg err (px-wt) | merges (machine-suggested) | artistic cost |
|---:|---:|---:|---|---|
| **10** | 0 | 0 | none (lossless) | none |
| 8 | 1.0 | 0.06 | `{F7A500,F7D600}` dark steps; `{F77300,F78400}` | ~invisible |
| 7 | 1.0 | 0.27 | + `{F7E784,F7F784}` (the 493-px pale-yellow body) | slight body flatten |
| 6 | 1.0 | 0.35 | + fold `F7F700` into the orange ramp | loses a yellow step |
| 5 | 1.0 | 0.35 | + `{F7F7B5,F7F7D6}` highlight | loses a near-white step |
| 4 | 2.0 | 0.42 | collapse the whole pale-yellow→white highlight cluster into one | **highlight gradient lost** |

**All merges above are machine-suggested, NOT authorised artistic merges.** MRD stays strict until Tighe
authors an Intentional Merge (§18). Reading: the fire degrades gracefully to **~6–7 colours** with ≤1 level
error; **4 colours** is where the highlight gradient visibly collapses.

## 12. Existing-palette candidate (Strategy A — zero runtime)

Could the fire be acceptably reindexed onto colours **already resident** in R1-S2? The resident gameplay lines
are the Test asset's Lines 0/1/3 (loaded by `vdp_install_test_lines` from
`diagnostic_palette_asset_ptrs[asset]`, asset selected by stage `0x1242`). The fire needs **10 warm colours
spanning orange→yellow→white**; the castle **Line-3 master is structural** (greys/browns/stone). The audit that
decides Strategy A = *dump the R1-S2 asset's Line 3 (and 0/1), count how many of the 10 fire colours each line
can host within a small error*. Expectation from the ramp vs a structural master: **only a few warm colours
match → a poor, flat fire**. Strategy A is the **zero-cost baseline**, not the fidelity answer. (The exact match
count is the one number to compute before adopting it; not run here to avoid over-reach.)

## 13. Leased-slot feasibility (Strategy B)

Lease ~10 slots of an existing line during records `0x11–0x13`. Per candidate index, the proof needed is:
current value · current Layer-A/B consumers in the **full scroll envelope** (including reversal) · retained
writer activity (loader/fade/respawn) · safe change frame · restore frame. **Line 3** (Layer-A master) is the
most plausible lease: the fire is already a Line-3 tenant, and castle-structure indexes the fire window does not
show could host fire colours **iff** no visible castle cell in the envelope references them. **Line 2** is a
poor lease target (actively managed, protected, respawn-reconstructed). No index may be leased on "looks
unused"; each needs the envelope-wide consumer proof.

## 14. Composite-L2 exact capacity (Strategy C math)

A composite line = (distinct colours the host line must keep in the window) + (10 fire colours). With a 15-slot
budget: **the fire's 10 leave 5 slots** for the host's own in-window demand. So a composite is loss-free **iff
the host line's distinct visible demand in records `0x11–0x13` ≤ 5**; otherwise the overflow must be merged
(use the §11 ladder on the host, or drop the fire to 8). Because the fire alone needs 10 and a full line is 15,
**a dedicated fire line (host demand ≈ 0 in the window) is trivially loss-free** — which is exactly why a
**segment-scoped residency that frees one line for the fire** (not a shared composite) is cleanest. The exact
host demand count is the corpus census over the window (same method as §10/§13).

## 15. Alternate-line feasibility

- **Lines 0 / 1** = Test **sprite** palettes — the player and enemies are on screen throughout the pit → **not
  safe** to repurpose.
- **Line 2** = Layer-B, protected and respawn-managed → **avoid**.
- **Line 3** = Layer-A master — the fire's **natural owner** and the **best candidate**: a window-scoped
  composite/lease here keeps the fire in the plane it belongs to and never touches sprite or Layer-B ownership.
  The castle structure colours the fire window actually needs are the only constraint (§14).

Do not pick a line for "attractive colours"; Line 3 is chosen because it is the fire's semantic plane and the
least cross-coupled option.

## 16. Arcade-semantics interpretation (the architectural answer)

The arcade has many independently addressable palette banks; it spends a **whole bank + a mode-8 animation** on
a **localized, progression-bounded effect** (the pit fire) that coexists with the castle master and Layer-B.
Genesis has **four** CRAM lines, all committed. The faithful translation is **not** to emulate arcade palette
RAM or run a runtime optimiser; it is to **schedule palette residency by progression** — give the fire a Genesis
line **only while its record window is active**, precomputed offline. This is **the same pattern the project
already uses**: the R2 native graphics **epoch residency** (records 32→33), the **transition packages**, and the
offline **per-scene palette assets** (`diagnostic_palette_asset_ptrs`). Differences: the fire window is **shorter
and reversible**, so its predicate must be a **held record range** (not a one-way epoch edge), and it must
**re-arm on respawn**. Same philosophy, finer granularity.

## 17. Palette Composer information gaps

The Composer (`tools/graphics_editor/server.py`) currently knows, per scene: tile codes, palette banks, flips,
coordinates, `used_colors` (real nibble census), MRD pairs, per-round line palettes, and sprite composites. It
does **not** model:

1. **Segment/record visibility sets** — which cells are simultaneously on screen at a record (and across a
   scroll envelope with reversal). Needed to compute *simultaneous* palette demand.
2. **Per-index writer/lifetime metadata** — which arcade routine rewrites each CRAM line/index and when (so
   "free" means "provably not written", not "not referenced").
3. **Palette residency regions** — a first-class "this palette is resident over records X–Y on line L" object.
4. **Effect groups** — a localized effect's Layer-A + (optional) sprite + animation as one unit.
5. **Cross-line simultaneous-demand solver** — given a window, the distinct colours every surface needs at once.

Minimum additions to let it reason about the fire (and future effects): a **per-record visible-cell set**
(derivable from the corpus coordinates + record), a **per-record cross-surface colour-demand census**, and a
**writer map** for CRAM lines (derivable from the mode-8/9 tables + the retained loader). These are analysis
data, not runtime.

## 18. Proposed authoring / data model (critiqued)

- **Effect Group** — the fire = {Layer-A unit `$093A–$0949` bank `0x14`, mode-8 animation, (no sprite)}. Useful;
  generalises to torches, water, etc. Keep.
- **Palette Region / Residency Region** — `{scene, record_lo, record_hi, genesis_line, source_colours,
  reversible, rearm_on_respawn}`. This is the core new object; aligns with the existing "epoch" vocabulary —
  **call it a "palette epoch" or "palette residency"** to match the repo, not a new word.
- **Intentional Merge** — a recorded authorisation to collapse specific MRD pairs below the 10-colour lossless
  set (e.g. adopt the 7-colour ladder). Must live as a decision in `specs/palette_decisions.json` (the canonical
  registry), **not** a Markdown side-table.
- **Protected / Leased Slot** — a per-index lease record `{line, index, window, prior_owner, restore}`. Useful
  but should be **derived from** the writer map (§17), not asserted. Prefer "freeing a whole line via residency"
  over per-slot leasing where possible (simpler, provably safe).

Terminology recommendation: reuse **epoch / residency / Palette Decision** (already in the repo) rather than
inventing "Palette Region"; keep **Effect Group** and **Intentional Merge** as new but register merges in the
JSON.

## 19. Runtime trigger semantics (proposed)

Offline-precomputed residency table keyed on `(scene_id, a5@0x13e)`; **no pixel inspection, no palette search,
no colour optimiser, no per-frame conversion**:

- **enter:** record enters `[0x11,0x13]` in R1-S2 → the precomputed fire line becomes resident on the chosen
  Genesis line; if the flicker is reproduced, route the mode-8 `dest_line 0x14` writes to that Genesis line for
  the window only.
- **hold / reversal:** residency is a **held predicate on the record range**, so walking back keeps it correct.
- **exit:** record leaves the window → restore the line's prior owner (Layer-A master) from the offline asset.
- **death/respawn:** re-evaluate the predicate at the `load_scene_tiles(scene 1)` boundary (shared with
  0134/0136) → re-arm if still in window.
- **direct-start / subround transition / attract:** inert unless the predicate holds; a subround change that
  leaves R1-S2 releases the region.

The trigger uses only **retained state + an offline table** — faithful to the architecture policy.

## 20. Ranked decision matrix

| Strategy | Arcade fidelity | Technical safety | Runtime complexity | Authoring burden | Generality | Compat w/ current arch |
|---|---|---|---|---|---|---|
| **C — segment-scoped residency on Line 3** | **High (10 colours, flicker optional)** | Med-High (Line 3 = fire's plane; no sprite/L2 touch) | Med (enter/hold/exit + respawn) | Med (window + offline fire line) | **High (reusable epoch pattern)** | **High (mirrors epoch/asset model)** |
| B — lease Line-3 slots | Med-High | Med (needs per-index envelope proof) | Med | Med-High (per-slot proofs) | Med | Med |
| A — reduce to resident colours | **Low (flat, few warm colours)** | **High (zero runtime)** | **None** | Low | Low | High |
| Alt — repurpose a full other line | Low–Med | Low (Line 0/1 sprites, Line 2 protected) | Med | High | Low | Low |

## 21. Independent recommendation

**Adopt Strategy C: a segment-scoped fire palette residency hosted on Line 3** (the Layer-A plane the fire
already belongs to). Precompute the fire's **10 lossless Genesis colours** offline into a dedicated fire line;
make it resident over records `0x11–0x13` in R1-S2 via a held-record predicate that re-arms on respawn; restore
the Layer-A master on exit. Reproduce the flicker *optionally* by routing the existing mode-8 `dest_line 0x14`
loader onto that Genesis line during the window (a static fire is an acceptable first step — confirm with
Tighe). Rationale: **lossless** (the fire's exact need is 10 ≤ 15), **arcade-faithful** (translates the
bank-residency *intent*, not the hardware), **reuses the proven epoch/residency pattern**, and **never touches
the sprite lines or the protected, respawn-managed Line 2** (avoiding the 0134/0136/0138/0141 blast radius).
Strategy A is the zero-work fallback if runtime residency is declined, accepting a flat fire. Strategy B (slot
lease) only if a whole-line residency proves unavailable.

## 22. Facts still requiring Tighe judgment

1. **Flicker vs static:** reproduce the mode-8 animation on Genesis, or ship a static 10-colour fire first?
2. **The "sprite flames on top" observation (§3):** static evidence shows none — does Tighe still see a sprite
   cap worth an ORIGINAL ARCADE sprite-RAM capture, or is the mode-8 top-row flicker the thing observed?
3. **Intentional merges:** stay at 10 (lossless) or author a reduction (7 recommended if a slot is contested)?
4. **Host line:** Line 3 residency (recommended) vs a Line-2 composite (riskier) — Tighe's call given L2 policy.
5. **Exact visibility envelope:** the pixel-level first/last-visible scroll X and the R1-S2 checkpoint position
   (before/within the window) — confirm from the corpus calc / retained checkpoint record before implementation.

## 23. Production files changed
**NONE.** Read-only forensic analysis; the only on-disk change is this proposal document (plus AGENTS_LOG).

## 24. ROM produced
**NONE.**

## 25. Build number consumed
**NONE** by this task. (The build counter reads 573 from other concurrent work between sessions; this read-only
proposal numbered nothing and produced no artifact.)

---

### Evidence index
- `analysis/graphics_optimizer/subround_corpus/PAL-R1-S2-PLANEA-CASTLE/{plane_a_uses.json, plane_palette_banks.json}`
  — fire tile/bank/coordinate corpus and bank `0x014` arcade RGB.
- `build/regions/pc080sn.bin` — fire tile pixels (used-index census, §5).
- `build/regions/maincpu.bin` — mode-8 tables `0x59A98` (dest lines), `0x59B1A` (cycle colours); static bank
  source `0x4ED76`.
- `apps/rastan-direct/src/palette_hooks.s` — gameplay line route table (no bank-`0x14` row; §9).
- `apps/rastan-direct/src/vdp_comm.s` — `vdp_install_test_lines` (Lines 0/1/3 offline asset; §12).
- `docs/design/Andy_r1s2_trap_graphics_sources.md`, `Andy_r1s2_traps_proven_authorable.md` — prior proven
  fire/trap sourcing (built upon, re-verified here).
- `specs/palette_decisions.json` — canonical palette registry (no fire entry yet; §1).

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0146`
