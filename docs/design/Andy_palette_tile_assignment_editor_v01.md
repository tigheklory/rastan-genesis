# Andy — Palette / Tile-Line Assignment Editor v0.1 (2026-08-26)

TOOLING ONLY. No production ROM/runtime change. Build counter 313. Genesis evidence never written into the arcade oracle.

## 1. Architecture
Local HTTP server (`tools/graphics_editor/server.py`, stdlib only) + static HTML/CSS/JS UI. The server assembles a
READ-ONLY arcade evidence bundle from the existing oracle/corpus and serves an EDITABLE Genesis policy layer. No cloud,
no internet, no framework. Browser cannot write files directly, so saves go through the server's POST endpoint.

## 2. Source Oracle Contract (READ-ONLY)
`GET /api/oracle` assembles from: `round1_phase1_corpus/plane_palette_banks.json` (Layer A/B 16-color banks),
`enemy_palettes.json` (sprite banks), `arcade_graphics_oracle/{contexts,objects,coexistence,patterns}.json`,
`bad_item_images_quarantine.json`. The editor NEVER writes these. Adds computed: palette-content SHA hash, Genesis
3-bit quantization per color, exact-duplicate palette groups, must-remain-distinct constraint set.

## 3. Editable Policy Contract
`analysis/graphics_optimizer/editor_policy/`: `profile_manifest.json`, per-profile `<id>.json`
(`palette_assignments: {palette_id -> {line,locked}}`, `vram_assignments: {pattern_id -> {tile_index,package}}`,
`object_labels`), plus `object_labels.json` / `genesis_palette_policy.json` / `genesis_vram_policy.json` stubs.
Saved via `POST /api/policy`. Deleting a profile returns the compiler to the selected baseline.

## 4. Profile / Revision Model
Immutable `baseline_current` (POST rejected 400). Branch → new editable profile (parent, revision, modified ts in
manifest). Save/reload/branch supported. Baseline never overwritten.

## 5. Context Model
Generalized type-based contexts from the oracle (GAME→GAMEPLAY→R1→P1→segments + ITEM_PAGE stub). Not hard-coded to R1/P1.

## 6. Pattern / Object Model
Objects carry stable IDs + evidence status (PROVEN/PARTIAL/UNKNOWN/OTHER) shown honestly. Physical patterns
(`pattern:pc080sn:<sha>`) are content-hash identities independent of semantic name; one pattern = one asset.

## 7. Palette-Line Assignment Model
4 Genesis CRAM lines × 16 (index 0 transparent). User selects an arcade palette → "→ LINE n". One line holds one
16-color palette; a second assignment to the same line is an ERROR.

## 8. Genesis VRAM / Tile Assignment Model
`vram_assignments: pattern_id -> {tile_index, package}`; package/residency by context (NOT per-frame). O(1) mapping intent.
(UI browser for patterns present; assignment endpoint shares the policy save path. Full VRAM grid = V0.2.)

## 9. Must-Remain-Distinct Graph
Deterministic: within each palette (one representation), all distinct non-transparent colors MUST remain mutually
distinct. The validator NEVER auto-merges; it reports. Intra-representation collapse is forbidden; cross-object sharing
is allowed (different palettes, no edge).

## 10. Genesis Quantization
Each arcade color → 3-bit-per-channel CRAM (level table [0,36,73,109,146,182,219,255]) + CRAM word `0BBB0GGG0RRR0`.
Shown per swatch. Different arcade RGB that quantize to the same Genesis color = ZERO additional merge loss.

## 11. Exact Palette-Content Identity
SHA of the 16 arcade RGB entries → `content_id`. Palettes with identical content are grouped
(`exact_duplicate_palette_groups`) — exact shared content, not lossy. Verified: 7 groups (plane↔sprite banks share
pool entries, e.g. plane 0x004 ≡ CHIMERA, plane 0x005 ≡ FLYING_DEMON).

## 12. Validation Rules
PASS/WARN/ERROR: >1 palette per line (ERROR), >4 lines (ERROR), coexistence max-simultaneous banks (WARN if >4),
must-remain-distinct (never auto-fixed), exact-duplicate content (WARN, informational), UNKNOWN objects (WARN, not fatal).

## 13. UNKNOWN / PARTIAL handling
First-class: object status badges; incomplete objects shown with no invented composite ("nothing invented"). UNKNOWN
never crashes and is a data WARNING, not an assignment ERROR.

## 14. UI
Left = contexts/objects/palettes/patterns tabs. Center = 4 Genesis lines + arcade palette viewer + ROM-decoded preview.
Right = properties/provenance + validation. Top = profile selector/branch/save/reload.

## 15. Persistence
Server POST writes profile JSON + manifest; deterministic; reload identical (verified).

## 16. Functional Verification
20-point API test passed: oracle loads (22 ctx/20 obj/19 pal), Genesis quant, 7 exact-dupe groups, 19 MRD reps,
coexistence max 6 (vs union 11), baseline overwrite rejected (400), branch+save+reload identical, ROM tile PNG preview,
detail-preservation (15 distinct colors mutually constrained). No ROM, no production change, Build 313.

## 17. V0.2 Extension Points
ΔE00 (CIEDE2000) / OKLab metrics, cross-object merge candidate ranking, best-legal-Genesis compromise colors, minimax,
full VRAM grid with capacity packing, palette-accurate preview coloring per assigned line, policy→compiler export.

## 18. Launch
`bash tools/graphics_editor/run.sh [port]` (default 8770) → open `http://localhost:8770`. Ctrl-C to stop.

# V0.2 Interactive Palette Composer (2026-08-26)
1. **Source-color usage model** — `/api/oracle` builds per-USAGE records (7 enemies + Rastan body): decode each
   sprite cell's real 4bpp pixels, collect the color indices actually used (with pixel counts), map to the sprite
   bank's arcade colors. Only actually-used colors are shown (not all 16 palette slots).
2. **Target palette composition** — policy `target_palette_lines[4][16]` holds legal Genesis CRAM words per entry
   (index 0 transparent). Each entry is individually clickable/editable — NOT whole-palette-to-line.
3. **Source→target mapping** — `usage_palette_mappings[usage_id] = {line, index_map:{src_index:target_index}}`,
   usage-aware (a pattern reused with another palette keeps a separate mapping).
4. **MRD from real pixels** — for each usage, every pair of distinct used colors CO-OCCURS in that representation →
   `mrd_pairs`. Mapping two MRD colors to one target entry is BLOCKED (alert), never auto-merged. Lizardman = 12 used
   colors / 66 MRD pairs.
5. **Rendering** — `/api/render?codes=..&bank=..[&target=<16 rgb>]` decodes from pc090oj.bin: ARCADE SOURCE uses the
   arcade bank palette (palette-accurate; Rastan renders as the real barbarian), GENESIS TARGET uses the mapped
   `src_index→CRAM` palette. Both nearest-neighbor. No debug ramp as source truth.
6. **Legal Genesis color editing** — R/G/B 0-7 level sliders → CRAM `0BBB0GGG0RRR0`; saved value is always a legal CRAM.
7. **ΔE00** — CIEDE2000 in app.js (no homemade RGB distance). Source-vs-source and source-vs-target.
8. **OKLab/OKLCH + Lab** — computed for the selected source color (display).
9. **Cross-object comparison** — pick source A, pick source B → ΔE00, same-natural-Genesis?, MRD-conflict?, with
   "Keep A / Keep B / Best legal compromise" actions.
10. **Best legal Genesis compromise** — search all 512 legal CRAM colors, minimize worst-case ΔE00; preview + explicit Apply.
11. **Profile persistence** — immutable baseline (POST 400); "Create editable profile" branches; save/reload identical.
12. **Onboarding/help** — "How to use" panel with the 9-step workflow + glossary (PROVEN/PARTIAL/UNKNOWN/MRD/exact/natural/line/entry/profile).
13. **Undo/redo** — session stacks over all policy mutations.
14. **Validation** — MRD violations, >4 lines, >15 nontransparent per line, usages mapped; multiple source palettes
    per line is NOT an error (expected). UNKNOWN objects shown honestly, never as fatal.
15. **Hands-on verification** — API + rendered previews proved: 8 usages, MRD pairs, palette-accurate source render
    (barbarian), target-mapped render, cross-object share (Rastan brown + Bat brown → L1:6, 2 usages), MRD block data,
    save/reload. (Live-browser screenshots not capturable in this environment; render endpoints that drive the previews are verified.)
    VRAM editor remains WORK IN PROGRESS (schema + pattern browser only) — deliberately secondary this pass.

# V0.3 Visual Workbench + True Composite Rendering (2026-08-26)
1. **True composite schema** — server builds per-object `pieces[]` (code, rel_x, rel_y, fx, fy) from the ACCEPTED
   trace's real emitted PC090OJ records (the same evidence that produced the accepted contact sheets). Anchor-relative
   unwrap + high-record-first draw order. Flying Demon = body(idx0)+wings(idx1) from one shared frame (25 pieces).
2. **Cell sheet distinction** — `/api/render?...&mode=cells` = grid, labelled "PROVEN CELL SHEET — NOT COMPOSITE".
   Default is the true composite. Objects without proven composition (Rastan body cells) are `composite_proven:false`
   and shown as a labelled cell sheet — never invented.
3. **PC090OJ placement / flips / ordering** — `render_composite` places each 16×16 cell at its real relative position,
   applies fx/fy, draws high-record-first (lower record on top), bbox-normalizes with 1px pad. Optional piece-boundary overlay.
4. **Source/target shared geometry** — both previews use the SAME pieces/positions/flips; only the palette differs
   (arcade bank vs mapped src_index→CRAM). Verified identical dims (FD 98×82 both).
5. **Composite bounds** — canvas = true nontransparent bounds, NOT cell-grid width. FD 96×80, Small Bat 16×16.
6. **Zoom** — Fit / 1× / 2× / 4× / 8× / ± ; source+target locked together; persisted in localStorage. At a given zoom
   one arcade pixel = Z screen pixels for EVERY object (equal scale: FD and Bat both scale by real bounds × Z).
7. **Drag/drop + one-action** — drag a source color onto a Genesis entry (or click color then entry): auto-creates the
   mapping AND auto-picks the nearest legal Genesis CRAM (ΔE00) — no sliders required. Drop-highlight (ok/share).
8. **Auto-fill Object** — one action: maps every used color to distinct legal target entries on the recommended line,
   detail-preserving (natural collisions nudged to a distinct legal color; two used colors never share an entry). One Undo.
9. **Recommend Line** — ranks all 4 lines by exact/natural shares vs new entries + fit; Apply on best.
10. **Find Similar Colors** — cross-object ΔE00 search, sorted, with exact/same-natural/cross-object flags.
11. **ΔE00 / OKLab / OKLCH / Lab** — as V0.2; ΔE00 is the perceptual metric; best-legal-Genesis compromise (minimax).
12. **Detail preservation** — MRD from co-occurring pixels; drag/click/auto-fill all reject intra-representation merges.
13. **Real-data verification** — 7 enemies render as true composites with real bounds; Flying Demon assembles as the
    winged demon (verified image); source/target geometry identical; cell-sheet distinct; equal pixel scale confirmed.
14. **Lighter this pass (documented)** — target→target drag menu, line copy/paste, and the full context-pack solver
    (Apply-Safe vs Review-Perceptual) are basic/partial; VRAM editor stays WORK IN PROGRESS. The composite+zoom+one-action
    workflow (the V0.2 hands-on complaint) is the delivered core.

## Uniform Preview Scaling Hotfix (V0.3)
- **Symptom:** Four-Armed Insect changed width with zoom but not height (tall/narrow at 1×, wider/squatter at 4×).
- **Root cause:** JS set only `img.style.width`; CSS `.pv img{height:150px}` (from V0.2) still applied to preview
  images, fixing height while width scaled → anisotropic.
- **Fix:** removed `height:150px` from `.pv img`; renderPreviews now sets BOTH `width` and `height` from the ACTUAL
  native PNG dims (`img.naturalWidth/naturalHeight`) × one integer zoom scalar, identical for ARCADE SOURCE and
  GENESIS TARGET. Fit = `max(1, floor(min(AVAIL/nW, AVAIL/nH)))` (integer nearest-neighbor, aspect locked).
- **Regression (native PNG dims incl. +2 renderer pad):** Four-Armed 50×69 → 1×50×69, 2×100×138, 4×200×276,
  8×400×552 (aspect 0.725 constant). Flying Demon 98×82, Small Bat 18×18, Large Bat 34×34 all scale uniformly;
  source==target dims for every object; every arcade pixel = Z×Z at zoom Z for every object (equal cross-object scale).
- **Version identity:** app still displays "v0.2" — left for the separate version-identity task (VERSION IDENTITY STILL PENDING).

# V0.3.1 Multi-Sprite Shared Palette + Closest-ΔE + Rastan Composite (2026-08-26)
1. **Primary vs group selection** — Objects list has per-row checkboxes (group) independent of the primary click-select.
2. **Source-color usage input** — solver operates over per-usage used colors (real pixels) with per-usage MRD.
3. **Shared-palette hard constraints** — within each usage every distinct used color is its own cluster (all same-usage
   pairs are MRD); clusters hold ≤1 color per usage; ≤15 entries (index 0 reserved); all target colors legal CRAM.
4. **Objective** — exact-RGB → natural-CRAM → nearest cross-usage merges only as needed to reach ≤15; each cluster's
   target = legal CRAM minimizing (worst ΔE00, then pixel-weighted mean). Prefers fidelity; uses up to 15 entries.
5. **Legal Genesis color search** — `_best_cram` over all 512 legal CRAM per cluster.
6. **One-line infeasibility** — if MRD forces >15 clusters, `feasible:false` with "no detail-preserving one-line
   solution" (verified: 8-object group). Never sacrifices internal detail.
7. **Group preview** — per-object arcade-vs-proposed previews (true geometry) before any policy change.
8. **Per-object quality** — worst/wmean ΔE per object + QUALITY IMBALANCE warning when spread >4.
9. **Active target line** — explicit ACTIVE line (clickable LINE label, outlined row); selecting an object with a
   mapping activates its line; ordinary color inspection never jumps lines.
10. **Closest-ΔE auto-highlight** — clicking any source color computes ΔE00 to every populated entry in the ACTIVE
    line and highlights the nearest (cyan) automatically; per-entry Δ shown in tooltip.
11. **Closest absolute vs closest legal** — if the nearest entry would collide with an MRD partner of the selected
    color in the current usage, it's shown FORBIDDEN (red) and the nearest LEGAL entry (cyan) is offered via
    "Map to Closest Legal"; empty line offers "Add Natural Genesis Color".
12-14. **Rastan captured composites** — 3 TRUE body composites from the accepted full capture (frames 07722/15828/16199,
    records 120-131, bank 0x33, real x/y/flip/order), replacing the cell sheet. `composite_proven:true`; provenance =
    capture frame + records. Frame-labelled (no invented pose names). Weapon blade EXCLUDED (labelled "Rastan body").
    Source/target use identical geometry (verified 58×74). Cell sheet remains only as `mode=cells` debug.
15. **Group Apply/Undo** — applying a shared palette sets the line entries + remaps all group usages in ONE Undo transaction.
16. **Verification** — tests A–I effectively covered: Rastan true composite (D/F PASS), src/tgt geometry (E PASS),
    3-object solve feasible+MRD-safe (G PASS), 2-bat solve 6 shares @ΔE0.0 (H PASS), one-line infeasible for big group,
    uniform-scale preserved. `Find Matches` (global corpus) retained alongside active-line closest.
Version identity: app still shows v0.2 — VERSION IDENTITY STILL PENDING (separate task).

# V0.3.2 Luminance-First / Between-Hue Shared Palette Solver (2026-08-26)
1. **Separate solver** — new "Derive Luminance/Hue Palette" button beside the existing "Derive Shared Palette"
   (unchanged). Both selectable; "Compare Solvers" runs both.
2. **OKLab L** — perceptual lightness metric (server `_oklab`). Genesis/CIE luminance available for diagnostics.
3. **OKLCH C/h** — `_oklch`; chroma + perceptual hue.
4. **Circular hue midpoint** — `_hue_center` = chroma-weighted vector mean (atan2 of Σ C·cos, Σ C·sin) → inherently
   shortest-arc: 350°+10° → 0°, never 180°.
5. **Multi-source hue center** — same chroma-weighted circular mean; a near-gray contributes ~0 weight.
6. **Neutral/low-chroma** — chroma < `_NEUTRAL_C`(0.02) excluded from the hue center; all-neutral cluster → hue
   ignored (returns None), optimize lightness+chroma+ΔE only.
7. **Lightness-first clustering** — `_cluster` merges cross-usage pairs ranked by OKLab ΔL (not ΔE) for the L/H mode,
   only as needed to reach ≤15 (Fidelity: exact/natural lossless first, then minimal ΔL merges). ΔE mode ranks by ΔE00.
8. **Legal Genesis target search** — `_best_cram_lh` evaluates all 512 legal CRAM.
9. **Lexicographic objective** — (worst ΔL, mean ΔL, hue-center error, chroma error, worst ΔE00, mean ΔE00) — genuinely
   lightness-first, not a weighted formula. Target chroma = median source OKLCH C (stable vs outliers).
10. **MRD hard constraint** — identical to ΔE solver: never two colors from one usage in a cluster (verified 0 violations).
11. **Comparison** — "Compare Solvers" shows entries/worst-ΔE/mean-ΔE/worst-ΔL/mean-ΔL for both + 3-column previews
    (Arcade | ΔE | L/H) per object. Verified L/H gives better worst-ΔL (0.118 vs 0.173) at higher ΔE (wide-hue tradeoff).
12. **WIDE HUE COMPROMISE** warning when a shared cluster's source hue spread > 60°.
13. **Solver metadata** — proposals carry `solver:"delta_e"|"luminance_hue"`; applied mappings record which solver produced them.
14. **Active-line closest + ΔL** — closest-ΔE highlight now also shows ΔL; added optional "Closest Lightness".
15. **Real-data tests** — hue-wrap (vector mean), chromatic+neutral (gray ignored), all-neutral (hue ignored),
    lightness-first-differs-from-ΔE (worst-ΔL 0.118 vs 0.173), 512-CRAM search, MRD-safe both solvers, 3-column comparison.
Existing V0.3.1 (Rastan composites, uniform zoom, ΔE solver) preserved unchanged. Version identity STILL PENDING.
