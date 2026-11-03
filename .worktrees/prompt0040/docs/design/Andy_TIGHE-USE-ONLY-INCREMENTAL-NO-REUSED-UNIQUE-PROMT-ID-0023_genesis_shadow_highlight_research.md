# PROMPT-ID-0023 — Genesis Shadow/Highlight for Arcade Rastan Masonry: Research & Recommendation

**Author:** Andy · **Date:** 2026-10-27 · **Type:** Research & feasibility only (no implementation)
**Scope:** read-only analysis. No native code, compiler, Composer, Test.json, palette decisions, audio,
or ROM build was changed. No build number consumed.
**Parallel work:** Cody is correcting R1-S2 graphics under Prompt 0022 (runtime per-subround palette).

---

## Bottom line (recommendation first)

**Do NOT adopt Genesis shadow/highlight (S/H) to restore R1-S2's darker masonry.** The arcade effect is a
**subtle palette-bank gradient** (measured brightness span ≈ 0.87–1.15× around mid, with a grey↔warm
*hue* shift), whereas Genesis S/H only offers fixed **×0.5 (shadow) / ×1.5 (highlight)** steps. S/H would
**overshoot** (far too dark/too bright) and **cannot reproduce the hue shift**, so it would look *less*
like the arcade, not more. It is also a **global VDP mode** that overloads the plane/sprite *priority*
bit (currently meaning layering) with *brightness*, creating layering/sprite/window regression risk
across every scene.

**The faithful path is palette allocation** (Option A) — give the shadowed and lit stone their own
Genesis palette entries/line as part of Cody's per-subround palette work. The real limiter is palette
**budget** (3 authorable lines, with sprites wanting 0/1 and flame reusing Line 2), which is a
scene-allocation decision, not a shadow problem. If budget forces a single stone level, a well-chosen mid
palette is more faithful than an overshooting shadow.

S/H remains a legitimate tool for *genuinely* half/double effects (transparency drop-shadows, flash
frames) — just not for 15 %-magnitude masonry shading.

---

## 1. Established Genesis hardware facts (VDP shadow/highlight)

Sources: Sega Genesis Software Manual (VDP priority & shadow/highlight), plutiedev.com/shadow-highlight,
/vdp-registers, /vdp-color-ramp — cross-checked against the project's own VDP writes.

- **Enable bit:** VDP register `$0C` (reg 12, "Mode Register 4"), **bit 3 = STE**. This project currently
  writes reg 12 = `0x8C81` (H40, no interlace, **S/H OFF**) — see `apps/rastan-direct/src/crash_handler.s`
  line 253 and `bk_crash_handler.s` line 252. Enabling S/H = `0x8C89`. It can be toggled at any time
  (e.g. a scene boundary) with a single control-port word; it changes *display* intensity only and does
  **not** modify CRAM.
- **Three intensity levels (color math):** per the color ramp, a normal component value maps to DAC
  steps `{0,2,4,6,8,10,12,14}`; **shadow ≈ the lower half `{0..7}` (≈ ×0.5)**; **highlight ≈ the upper
  half `{7..14}` (≈ color + ~half toward white)**. The steps are coarse and fixed — there is no "25 %
  darker" setting.
- **Plane rule:** with S/H on, a background pixel is **NORMAL** if its topmost opaque plane pixel is
  **high priority**, and **SHADOW** if only **low-priority** plane pixels cover it. So the plane-A/B
  **priority bit** doubles as the brightness selector. (The exact A-vs-B tie-break and transparent-pixel
  fall-through to backdrop are worth confirming by experiment — see §8.)
- **Sprite operators (palette line 3 only):** when S/H is on, sprite pixels of **palette 3, color 15
  (0xF) = SHADOW operator** and **palette 3, color 14 (0xE) = HIGHLIGHT operator**. These do not draw a
  color; they darken/lighten whatever is beneath and are otherwise transparent. A **high-priority normal
  sprite forces the area to NORMAL** (cancels shadow). A **low-priority sprite is itself shadowed**.
- **It is global:** the STE bit affects the **entire display**, every plane and sprite, for as long as it
  is set. There is no per-tile "enable S/H here" — only the per-tile *priority* bit chooses normal vs
  shadow once the global mode is on.

**Granularity:** darkening is **per tile** (via the name-table priority bit) or **per sprite-pixel** (via
operators) — never per background pixel within a tile. A tile is darkened **uniformly** (all its colors
halved).

---

## 2. Findings proven with Rastan's arcade data

Method: decoded R1-S2 Plane-A banks from the authoritative arcade program (`build/regions/maincpu.bin`,
fixed startup base `0x4EAF6 + bank*32`, nibble×2 → xBGR-555, the conversion verified in PROMPT-ID-0006),
via the editor's own `build_layera("PAL-R1-S2-PLANEA-CASTLE")`.

1. **The darker masonry is a PALETTE-BANK effect, not lost pixel detail.** The brick tiles are
   **multi-palette**: the *same* tile codes (e.g. `0x818`, `0x819`, `0x81A`…) appear across many banks
   (`0x008,0x009,0x00A,0x00B,0x00D,0x00E,0x010,0x011,0x012,0x013,0x01F`). Same pixels, different palette →
   the arcade paints the shadow gradient by **switching the tile's palette bank**, cell by cell. This is
   recoverable in principle (it is a color-assignment problem), and it is **not** a tile-reindex
   information loss. 37 physical patterns are multi-palette.
2. **The gradient is SUBTLE, and includes a HUE shift.** Mean luma of the stone banks spans only
   ≈ **86–102** (a ~1.15× range), not a 2× range. The brighter banks are also **warmer** (more red): e.g.
   for the same brick index, a shadowed bank reads ~grey `(49,49,33)` while a lit bank reads
   warm-brown `(115,49,33)` — a hue change, not just a brightness change.
3. **Genesis shadow OVERSHOOTS this gradient.** Shadow ≈ ×0.5. Shadowing a lit brick (luma ~100) yields
   luma ~50, but the arcade's *darker* brick is luma ~89 — roughly **twice as dark as the arcade
   intends**. Highlight ≈ ×1.5 overshoots the other way (arcade lit is only ~1.15× the shadow). The S/H
   steps are ~2× too coarse for this effect.
4. **S/H cannot reproduce the hue shift.** Shadow/highlight scale intensity uniformly; they keep hue.
   The arcade's lit stone is warmer than its shadowed stone, which no uniform scaling can produce.
5. **Why the Genesis build looks flat today:** the area-weighted scene palette collapses these many
   subtly-different stone banks into **one** Genesis line, so *all* brick renders identically — the
   gradient is lost. The fix is giving the distinct levels distinct colors, not darkening one of them.

(The darkest castle element measured is bank `0x003`, luma ~63 — a distinct darker *tile set* / arch
surround, again a separate palette bank, not a shadow of the brick.)

---

## 3. The three approaches evaluated

### Option A — Palette allocation / offline reindex  → **RECOMMENDED (most faithful)**
Give the shadowed-grey and lit-warm stone their own Genesis colors (a 2–3 level stone ramp) instead of
one collapsed palette. Pros: **exact arcade colors**, including the hue shift; fully offline; no runtime
cost; no global VDP change; no priority/layering risk. Cons: **palette budget** — R1-S2's 3 authorable
lines (0,1,3) are contended by sprites (Tighe reserves 0/1) and the flame (reuses Line 2). Realistically
this buys ~2 stone brightness levels at most, not the arcade's full smooth gradient — but 2 correct
levels beats today's flat look and beats an overshooting shadow. Fidelity ceiling: good for the
*perceptually distinct* levels (shadowed vs lit), limited for the fine in-between steps.

### Option B — VDP shadow/highlight via tile priority
Enable STE; set the brick tiles to be dark = low priority (shadowed), normal = high priority. Pros:
tile-granular, attributes compilable offline, **no extra CRAM**. Cons that make it a poor fit here:
- **Overshoot + no hue match** (§2.3–2.4): the result is too dark and the wrong color.
- **Overloads the priority bit**: priority currently controls *layering* (Plane A vs B, sprites, windows).
  Forcing a stone tile low-priority to darken it can push it **behind** high-priority Plane-B scenery
  through the arch windows or behind sprites — a visible layering regression.
- **Global**: STE affects every scene. Either S/H is toggled per scene (and every scene's priority bits
  must then be S/H-correct) or every low-priority tile game-wide gets shadowed. That is a large,
  cross-cutting change to a currently-working priority scheme.
- **Sprite/HUD/flame risk** (see §5).

### Option C — Sprite shadow/highlight operators  → **REJECTED for masonry**
Tiling large wall regions with palette-3/color-15 operator sprites is infeasible: each sprite is ≤32×32,
so covering the masonry needs **many** sprites, blowing the **sprites-per-scanline (≤20 in H40) and
80-SAT** budgets and colliding with gameplay sprites. Operators suit small, localized shadows (a
character's cast shadow), not background fields. Not worth the cost or risk.

---

## 4. Native-architecture compliance

Only Option A clearly satisfies the mandate: it is offline-compiled, adds **zero** per-frame CPU/VBlank
cost, touches no PC080SN emulation/framebuffer, preserves scrolling, sprite priority, Line-2 arcade
behavior, and Tighe's authored palette. Option B adds a global VDP state and *reinterprets* the existing
priority data at runtime (no new per-frame CPU, but a semantic change to compiled attributes with
layering consequences). Option C adds per-frame sprite/SAT cost and is rejected.

---

## 5. Unintended global effects of enabling S/H (Option B)

Because STE is global, enabling it (without a careful per-scene + whole-game priority audit) risks:
- **R1-S1 outdoor / R1-S3 boss / later rounds:** every low-priority plane tile becomes shadowed — the
  entire game's brightness/layering would shift unless each scene's priority bits are reworked.
- **Plane B scenery & transparent arch windows:** the flame/background seen through windows is drawn by
  planes with their own priority; shadow/priority interplay could darken or re-layer the window contents.
- **Rastan & enemy sprites:** a sprite over a shadowed region is shadowed too **unless high priority** —
  the hero could darken when walking in front of shadowed stone; all gameplay sprites would need
  high-priority to stay normal.
- **Flames mapped to Line 2 (Layer B reuse):** if those tiles are low priority they would be shadowed;
  Line-2 is arcade-controlled and must not be altered — a hard constraint against casually shadowing it.
- **HUD/status:** HUD sprites/tiles must be high priority to stay at normal intensity.

Per-scene toggling *can* contain this to the castle, but only after proving the castle's own
Plane-A/Plane-B/sprite priorities are all S/H-correct — which is exactly the layering risk above.

---

## 6. Answers to the ten questions

1. **Can S/H reproduce the darker R1-S2 stonework?** Only crudely. It overshoots the subtle gradient and
   can't match the hue — so not faithfully.
2. **Without extra CRAM?** Yes, S/H needs no CRAM — but the result is inaccurate, so the saving isn't
   worth it here.
3. **Would normal reindex/allocation be more faithful?** **Yes** — exact colors incl. hue, within palette
   budget.
4. **Per tile / per pixel / only via priority?** Per **tile** (priority bit) or per **sprite-pixel**
   (operators). **Never per background pixel.** Uniform per tile.
5. **Effect on Plane B & windows?** Priority-driven shadow can re-layer/darken Plane-B window content;
   needs auditing — a risk, not a given.
6. **Would it alter Rastan/enemies/HUD/flames?** Yes — sprites shadow unless high priority; Line-2 flames
   must not be touched; HUD must be high priority. All require deliberate handling.
7. **ROM/VRAM/sprite/CPU/VBlank cost?** Option A: ~one extra palette line's worth of CRAM, zero runtime.
   Option B: ~0 ROM/CPU (reuses attributes) + one reg-12 write per toggle, but a cross-scene priority
   rework. Option C: heavy sprite/SAT/scanline cost — rejected.
8. **Can the needed info be compiled offline?** Yes for both A (palette) and B (priority attributes).
9. **Which best suits the architecture?** **Option A.**
10. **Exact contract for Cody if authorized?** See §7 — but the authorized thing should be palette
    allocation, not S/H.

---

## 7. If Tighe authorizes a fix — contract for Cody (palette path, not S/H)

1. In the per-subround palette path (the runtime-selection work already handed off), treat R1-S2 stone as
   a **small brightness ramp** (target 2, ideally 3, levels) rather than one collapsed palette: keep the
   shadowed-grey and lit-warm stone as **distinct** Genesis entries, sourced from the arcade banks
   identified in §2 (same tile codes, banks `0x008…0x013`).
2. Resolve the **palette-budget** question explicitly: confirm whether R1-S2 can spare a line for a second
   stone level given sprites (Lines 0/1) and the Line-2 flame reuse. If not, pick the single most
   representative mid stone palette (do not overshoot with shadow).
3. Keep the per-cell **bank→level** assignment data-driven from the arcade Plane-A attributes (the
   existing scene decode already carries each cell's bank); map arcade bank → Genesis stone-level entry.
4. Do **not** enable STE (reg 12 bit 3) for this; leave reg 12 = `0x8C81`. Preserve Line-2, sprites,
   scrolling, priority/layering.

**If** Tighe specifically wants S/H evaluated on hardware despite §2, gate it behind the experiment in §8
first — never enable it game-wide.

---

## 8. Proposed experiment (only if Tighe wants hardware confirmation — do NOT run during Cody's work)

Goal: measure actual S/H output vs the arcade brick gradient, without touching Cody's tree.
- In an **isolated throwaway worktree**, build one diagnostic ROM that (a) sets reg 12 = `0x8C89`, and
  (b) flips the priority bit on a handful of known brick cells in R1-S2.
- Capture GENESIS NTSC MAME frames at the castle; sample the shadowed vs normal brick luma/RGB.
- Compare against ARCADE MAME `rastan` frames of the same masonry.
- **Expected evidence** (prediction from §2): the shadowed Genesis brick will read ~½ the normal luma —
  visibly darker than the arcade's ~0.87×, and still grey where the arcade lit stone is warm. If so, S/H
  is confirmed unsuitable and Option A stands.
This consumes no release number (diagnostic worktree ROM, discarded) and must not disturb the active
build or Cody's branch.

---

## 9. Evidence classification

- **Established hardware facts:** STE = reg 12 bit 3; current project value `0x8C81` (off); shadow ≈ ×0.5,
  highlight ≈ ×1.5; per-tile (priority) / per-sprite-pixel (pal-3 color 14/15) granularity; global mode;
  CRAM unchanged. (Docs + project source.)
- **Proven with Rastan arcade data:** the masonry gradient is a multi-palette (same-pixel, different-bank)
  effect; brightness span ~86–102 luma (~1.15×) with a grey↔warm hue shift; S/H ×0.5/×1.5 overshoots and
  can't hue-match; today's flat look is a palette-collapse, not pixel loss.
- **Reasonable engineering inferences:** Option A gives ~2 faithful stone levels within budget; Option B's
  priority reuse risks window/sprite re-layering; Option C is infeasible for wall-sized regions.
- **Unverified (confirm by experiment §8):** exact S/H DAC output vs predicted ½; precise Plane-A/Plane-B
  tie-break and transparent-pixel backdrop behavior under STE; whether any specific castle region is a
  genuine ≈½ pair that S/H *could* match.

---

## 10. Final recommendation

Genesis shadow/highlight is **not** the best way to restore R1-S2's darker masonry — not because the
feature is unavailable, but because the arcade effect is a *subtle, hue-shifted palette gradient* that
S/H's coarse half/double steps cannot represent, and because enabling it globally risks the existing
priority/layering, sprite, window, and Line-2 behavior. The faithful, architecture-respecting fix is
**palette allocation within Cody's per-subround palette path** (Option A), bounded by an explicit
palette-budget decision. Reserve S/H for future effects that are genuinely half/double in nature.
