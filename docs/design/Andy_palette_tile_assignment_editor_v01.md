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

# V0.3.3 Hue-Safe Luminance Solver (resumed + completed 2026-08-26)
**Original failure:** Rastan flesh turned BLUE/PURPLE under the luminance/hue solver (worst ΔE ~63-80, 160° hue
shifts). **Two root causes found:** (1) multiple captured Rastan frames were selectable as independent palette
consumers; (2) `_best_cram_lh` ranked targets by lightness FIRST with hue only tertiary, so a blue with identical
OKLab L beat an in-family orange — even for single-color clusters, which bypass the merge-time gate entirely.

**Fixes:**
- **Palette-domain dedup** (`_collapse_domains`): usages with the same `object_id` collapse to ONE domain — union of
  used colors (max pixels) + union MRD. 3 Rastan frames + Valkyrie → **2 palette domains** (preview frames tracked
  separately as representations). UI shows one "Rastan body" checkbox + a frame selector (preview only).
- **Admissibility-first target** (`_best_cram_lh`): a legal CRAM is admissible only if (1) worst per-source ΔE00 ≤
  `de_limit`(20), (2) target OKLCH hue lies inside the source chromatic hue arc ±`hue_tol`(10°), (3) target chroma
  within `_CHROMA_TOL`(0.10) of median source chroma. **Only among admissible candidates** does lightness-first
  lexicographic ranking (worst ΔL, mean ΔL, hue err, chroma err, worst ΔE, mean ΔE) apply. No admissible candidate →
  returns None (NO VALID TARGET). A single source always falls back to its own natural quantization (hue-safe).
- **Cluster admission gate** (`legal` in solve_group): merge rejected unless cluster chromatic hue-span ≤ `hue_limit`
  (45°, min circular arc) AND a hue-safe legal target exists (`_best_cram_lh` non-None).
- **Safe-infeasible**: when hue-safe clustering can't reach ≤15, the solver STOPS merging and returns the remaining
  hue-safe clusters + `feasible:false`, `safe_entries_required`, `one_line_capacity` — never garbage clusters.
- **Circular hue geometry**: `_min_hue_arc` (350/5/15 → 25°), `_hue_in_arc` (containment ±tol), chroma-weighted
  `_hue_center`; neutral (`C < 0.02`) hues excluded; all-neutral → hue ignored.

**Regressions (all PASS):** dedup 2 domains; Valkyrie+Rastan L/H feasible=false, maxΔE 18.9(≤20), **hue-shift>60°=0
(no blue flesh)**, MRD=0; red(25°)/cyan(190°) same-L NOT merged; hue-wrap 25°; 10/30/50/70 chain blocked (60>45);
chromatic+neutral & all-neutral handled; no-valid-target returns None; single-color always safe; ΔE solver unchanged
(15 entries). Advanced L/H settings (hue_limit/de_limit/hue_tol/neutral_c) are server params with defaults 45/20/10/0.02,
exposed in the proposal (editable slider panel is basic/deferred). Version identity STILL PENDING.

---

# V0.4 Complete Layer-A Tile/Palette Editor + Protected Line 2

**Classification:** INFRASTRUCTURE. Tooling only. Build counter 313. No production ROM/runtime change.
Resumed after a weekly-usage-limit checkpoint; no partial V0.4 code existed in the working tree, so
implementation continued from the proven Layer-A census.

## 1. Build-0313 screenshot evidence (why Line 2 is protected)
Tighe supplied 11 sequential Build-0313 debugger captures spanning R1/P1 into early Phase 2, including
the live VDP 4×16 palette. Cross-comparison: **Line 0/1/3 visibly unchanged**; **Line 2 changes ~8 times**
tracking the sky/time-of-day progression (blue/cyan → violet → sunset orange/red) while Layer-B tile art
stays fixed. This matches Tighe's stated behavior and his explicit acceptance that **Layer B in Build 0313
already looks correct**. Corroborated statically by KNOWN_FINDINGS (CRAM-line ownership: line 2 = arcade
BG bank for Stage 1). The editor therefore treats **CRAM Line 2 = Layer B / arcade controlled / PROTECTED**.

## 2. Line-2 ownership decision & protection (server-authoritative)
`server.py` declares `RESERVED_LINES=[2]`, `EDITABLE_LINES=[0,1,3]`, and `LINE_OWNERS` (Line 2 owner
`layer_b`, control `arcade`, editable false, optimizer_available false). Protection is enforced at three
layers: (a) policy GET backfills `reserved_lines`/`line_owners` into any older profile in memory only
(never rewrites the file); (b) policy POST **rejects (403)** any sprite/plane mapping whose `line` is
reserved and **forces** `target_palette_lines[2]` back to empty on every save, so the editor can never
serialize a replacement Layer-B palette; (c) the client marks Line 2 `L2 🔒`, blocks click/drag/drop/clear/
picker on it, routes its clicks to a read-only inspector, and excludes it from Recommend Line, Auto-fill,
ΔE solver, L/H solver, drag/drop, and every "Apply to Line" list (all now use `editableLines()`).
Ownership/protection is persisted; **no Layer-B colors are serialized**.

## 3. Editable budget (Lines 0/1/3)
The target panel shows a capacity banner: *AVAILABLE FOR LAYER A + SPRITES: Lines 0,1,3 · capacity 45
entries (3×15)*. Line 2 is never counted. The existing `Test` profile's sprite work (Line 0: 15 entries,
10 mappings on lines 0/1) is preserved byte-for-byte; Layer A fits **around** it on 0/1/3.

## 4. Complete Layer-A physical corpus & 5. logical-usage model
Source of truth: `analysis/graphics_optimizer/round1_phase1/plane_a_uses.json` (frozen census).
`build_layera()` groups the 1,581 logical usages by `physical_pattern` (sha256 of the 32 raw tile bytes,
the authoritative identity — ~1:1 with tile_code; one pattern spans two codes) into **1,315 physical
patterns**, stable IDs `A-0000..A-1314` (ordered by representative tile code). Each logical usage gets a
stable `LA-0000..LA-1580` id carrying pattern, tile_code, palette bank, flip, priority, **segments
(records 0–15)**, map_cell_count, coordinate samples, source address, and the real used-index set.
Tiles decode with the same high-nibble-first 8×8 4bpp decoder as `tools/audit_round1_phase1_plane_a.py`.
**11 source banks** (0x003,0x004,0x005,0x006,0x007,0x017,0x018,0x01A,0x01B,0x01C,0x01D).

## 6. Tile browser & 12. segment filtering
Top-level **Layer A** workspace (Sprites · Layer A · Contexts · Palettes). Center = paginated grid
(200 patterns/page, lazy `<img>` thumbnails from `/api/render_tile`, integer zoom 4/8/16/32×,
nearest-neighbor). Left = counts + search (id/code/hash/usage/bank) + filters: Segment 0–15, Bank (11),
palette-use single/multi, mapping status unmapped/partial/mapped, variation status. Segment filter uses
actual per-usage `records`, not the Round-1 union. Every one of the 1,315 patterns is reachable.

## 7. Tile detail, 8. palette-variant handling, 10. source/target previews
Clicking a pattern opens detail: pattern id, tile code(s), content hash, used indices/color count,
segments, banks, status; **palette variants side-by-side** (same 8×8 geometry rendered through each
proven source bank — identical pixels, different colors); and the full logical-usage list. Selecting a
usage shows **Arcade source** (tile × its bank) vs **Genesis target** (same geometry × current mapping),
plus per-color chips with natural-CRAM/ΔE/OKLab data.

## 9. Tile MRD & 11. Layer-A mapping
MRD is built from the **actual used pixel indices** of each logical tile usage (not the whole 16-color
bank). `laMapColor`/`autoFillTile` refuse to collapse two distinct used colors onto one target entry
(grayscale-before-detail-loss rule preserved). Mapping is **usage/context-aware**: stored in
`plane_usage_palette_mappings` keyed by `LA-*`, so the same physical bitmap used with different banks maps
independently. Actions: click-color-then-editable-entry manual map, **Auto-fill Tile**, **Copy Used
Colors → Line 0/1/3**, Reset — one Undo transaction each. `Find Matches` cross-references the color across
Layer A + sprites (ΔE/ΔL/coexistence); Layer-B is informational only and never a target.

## 13. Group solver support
Multi-usage checkboxes feed the existing ΔE and Luminance/Hue solvers via `/api/solve`; `layera_solver_usages`
adapts `LA-*` ids into solver usage dicts (each logical usage = its own palette domain; MRD from real
pixels). Proposals apply only to editable lines.

## 14. Profile schema & 15. performance
Schema `v0.4` adds `plane_usage_palette_mappings`, `context_palette_packages`, `reserved_lines`,
`line_owners` — all backward-compatible (older profiles backfilled in memory; `Test` preserved, disk
sha unchanged by GET). Performance: server-rendered lazy thumbnails + client pagination + indexed
client-side filtering keep the 1,315/1,581 dataset responsive without thousands of eager DOM nodes.

## Verification (all against the implemented API/editor)
Counts 1315/1581/11/199 (PASS); physical coverage 1315/1315 and logical 1581/1581 (PASS);
first/middle/last pattern decode+render A-0000/A-0657/A-1314 (PASS); all 11 banks render (PASS);
multi-palette variant view A-0001 two banks same pixels (PASS); Line-2 GET-backfill + POST force-empty +
map-to-line-2 403 (PASS); Test-profile Line 0 + 10 sprite mappings intact, disk unmodified (PASS);
Layer-A ΔE and L/H group solve (PASS). Manual DOM interactions (drag, MRD alert, Undo) are Tighe's
hands-on checks. Known honest gaps: animation status is STATIC/MULTI-PALETTE only (no new animation
archaeology — UNKNOWN acceptable); L/H advanced sliders remain basic; no production integration.

---

# V0.4.1 Segment Maps + Pixel Picking + Precise CRAM Controls + Context Policies

**Classification:** INFRASTRUCTURE. Tooling only. Build counter 313. No production/ROM change. Line 2 remains
absolutely protected in every context. Phase 0: KNOWN_FINDINGS CRAM-line-ownership (line 2 = arcade BG bank)
continues to corroborate Line-2 protection; no contradiction; classification INFRASTRUCTURE.

## 1–3. Assembled Layer-A segment maps (arcade-sourced) + map-cell→usage identity + map/library linkage
`layera_map(seg)` reconstructs each R1/P1 segment directly from the arcade `maincpu.bin` source tables
(`_MAP_BASES`, stride 0x40, visible rows 1–30 × 64 cols) — the same authoritative decode as
`tools/audit_round1_phase1_plane_a.py`, **never screenshots**. Each visible cell yields `tile_code` +
`palette_bank` (`attr & 0x1FF`) + flip bits (`0x4000/0x8000`) and is resolved to its exact **logical usage**
(`LA-*`) and physical pattern (`A-*`). Coverage is exact: 1920 cells/segment, 1920 resolved (100%). The
client renders the segment on a `<canvas>` from the returned per-code pixel tiles × arcade bank colors,
with a Segment-Map ↔ Tile-Library toggle sharing selection; clicking a cell opens that precise usage/variant
(not merely the first usage of the bitmap), hover shows coordinate/pattern/usage/code/bank/flip, and the
selected pattern's occurrence count in the segment is reported.

## 4–6. Pixel picking (sprites + Layer A) from Genesis Target artwork
Picking uses the render's actual index geometry, never an RGB match. Sprites: `composite_hitmap(pieces)`
produces a per-pixel source-index buffer using the **same painter's order/flips** as `render_composite`;
`/api/hitmap` serves it; a click maps display→native coords (zoom-corrected) → topmost source index →
mapped target CRAM entry (transparent → "Transparent pixel — no palette entry"). Layer A: the tile detail
uses `LADET.pixels` (8×8) and the segment map uses the cell's tile pixels, both zoom-corrected. The Genesis
segment-map mode recolors live from the current context-effective policy.

## 7. Precise ±1 CRAM channel controls
`showTarget` renders per-channel rows `R [−] n/7 [+] [slider]` (steppers change exactly one legal level,
clamped 0–7, disabled at bounds; slider `step=1` snaps to legal levels). Every edit produces only legal
Genesis CRAM, is one Undo step, and immediately updates the swatch, CRAM word, RGB, and all previews.

## 8–12. Contexts as real editing scopes with inheritance/overrides
Selecting a context sets the active **editing scope** (`SCOPE`), shown in a persistent top banner across all
tabs (`EDITING SCOPE: … [stable id]`) using the oracle's stable context IDs and parent links. Selecting an
R1/P1 record context auto-opens its segment map. Palette **color** policy is context-scoped: `effEntry`
resolves an entry by overlaying the profile base default with ancestor→scope context overrides (deepest
wins); editing a color while a child context is active creates a **local override** on that context
(`context_policies[id].tpl[line][index]`) — parent and siblings unchanged — with LOCAL/INHERITED indicators
and per-entry **Reset Context Override**, plus a whole-context reset and "Create full local copy". Test
migration is loss-free: base = global default = current `Test`; R1/P1 inherits it unchanged (verified
byte-identical), so no color moves. Future contexts (Round 2, Phase 2, frontend) report COMPLETE/PARTIAL/
UNKNOWN coverage honestly and never present R1/P1 evidence as authoritative there.

## 13. Line-2 context protection
Server rejects (403) any `context_policies` override targeting a reserved line, and all client edit paths
route through `guardProtected`. Line 2 cannot be overridden at any context.

## Verification (against the implemented API + simulated client inheritance)
Segment map coverage 0–15 = 1920/1920 resolved (PASS); map-cell→usage/variant identity (PASS);
multi-palette map instances resolve to distinct usages (PASS); sprite hit-maps for Rastan/Valkyrie/Small
Bat/Flying Demon with correct per-pixel indices (PASS); Layer-A pixel picking via LADET.pixels (PASS);
±1 steppers legal-CRAM-only + bounds (PASS); context inheritance N/O/P + parent→child + reset (PASS);
save/reload parent+child overrides (PASS); Line-2 context override rejected 403 (PASS); Test profile
byte-preserved (PASS); V0.4 corpus 1315/1581/199 + solvers unregressed (PASS). Honest scope: context
scoping covers palette **color** values (matching the ±/pixel-pick edit surface and the Layer-B time-of-day
model); source→target mapping topology remains global (a deferred extension). DOM gestures (drag, click
feedback) are Tighe's hands-on checks.

---

# V0.4.1 Corrective Pass — Full Vertical Map / Arcade-Palette Truth / CRAM Control Layout

Tighe's hands-on verification reproduced three failures; this pass fixes them. Tooling only, Build 313,
no production/ROM change, Line 2 still protected.

## 1–3. Failure 2 (dominant): the segment map was vertically cropped
The prior server hard-coded rows 1..30 (`_MAP_ROW0=1,_MAP_NROWS=30`) and reported "1920/1920 = 100%".
That was **only 100% of a 30-row screen-viewport window, not the map**. The authoritative PC080SN backing
tilemap per segment is **64×64** (`ROWS_PER_SEGMENT=64`, matching `tools/audit_round1_phase1_plane_a.py`).
For segment 0 the actual terrain lives in rows **40–63**, which the crop discarded — exactly the "narrow
strip at top, rest blank" Tighe saw. The earlier "1920/1920 = 100% complete map" claim is **withdrawn**: it
described the cropped window. `layera_map` now walks the full 64 rows and reports honest accounting per
segment: `total_cells` (4096), `descriptor_cells`, `blank_cells` (fully-transparent tiles, counted not
emitted), `nonblank_cells`, `resolved`, `unresolved`. Verified 0–15: every nonblank cell resolves to a
logical usage (unresolved 0); cells span rows 0..63; the normal viewport (rows 1..30) is returned as
`visible_viewport` for a highlight overlay only. The client canvas renders the full height in a scrollable
pane at Fit/1×/2×/4× with click/hover identity through the entire vertical domain.

## 4–7. Failure 1: the Arcade palette was NOT actually wrong
Root-cause analysis (not a dismissal): the editor's `plane_bank_colors()` reads
`plane_palette_banks.json`, and that file's **bank 0x003 is byte-exact** against the independent decoded
audit `analysis/round1_phase1_palette_audit/colors.json` (audit 5-bit `[30,20,16]` == editor 8-bit
`[247,165,132]`, idx8 `[30,30,0]`==`[247,247,0]`, etc.). The corpus's own `epochs` note states **"Layer A
multi-bank is spatial not temporal"** — banks are invariant across R1/P1; the multi-bank aspect is which
segment uses which bank, not time-of-day. Rendering the corrected full 64-row maps confirms authentic
arcade artwork with correct colors: **segment 15 is the recognizable Round-1 orange-brick arch/bridge**
(banks 0x017/0x018), **segment 0 is grey-stone-with-green terrain** (bank 0x003). The apparent "wrong
colors" was the vertical crop presenting an unrepresentative upper strip. No palette state was fabricated;
evidence shows none exist for Layer A. Banks proven invariant: all 11 (0x003–0x01D); banks with multiple
R1/P1 content states: none. Selector→bank is `attr & 0x1ff` == effective palette-RAM bank
(`correction_1_selector_vs_bank`), matching the implementation.

## 8–9. Failure 3: R/G/B controls overflowed the right panel
`.picker` was `display:flex` (row) holding three full `.chanrow` groups, pushing B off-screen. Fixed:
`.picker{flex-direction:column;width:100%}`, `.chanrow{width:100%;min-width:0}`, slider
`flex:1 1 auto;min-width:0`; right panel widened 320→360px. R/G/B now stack vertically (each a full row of
label · − · n/7 · + · slider) with no horizontal scroll. The ±1 0–7 legal-CRAM math is unchanged.

## 10. Regression
V0.4 corpus 1315/1581/199 intact; sprite ΔE solver 15 entries; sprite hit-map + Layer-A pixel picking
unchanged; context scope/inheritance/override, Line-2 protection (server 403 + client guard), and the
`Test` profile all preserved. Screenshot-derived acceptance is Tighe's re-verification of the full-height,
correctly-colored maps and the stacked channel controls.

---

# V0.4.1 Corrective Pass 2 — Original-Arcade Layer-A Palette RAM

**This section supersedes the Corrective-Pass-1 claim that the Layer-A Arcade colors were correct.** That
earlier conclusion validated `plane_palette_banks.json` only against `colors.json`, which shares the same
decode lineage — not against original-arcade ground truth. Tighe's hands-on report ("colors completely
wrong, gray/green terrain") was right.

1. **Geometry stays accepted.** The 64×64 map reconstruction and PC080SN tile decode were not the fault.
2. **Old Layer-A Arcade colors were WRONG.** `plane_palette_banks.json` bank `0x003` matched the
   arcade-runtime bank (KF-788) only **1/16** — it rendered flesh/white/yellow/green/gray where the real
   arcade is purple cave rock.
3. **Old RGB lineage:** `plane_palette_banks.json` (and the sibling `colors.json`) decoded a ROM pool that
   did not reproduce the displayed palette RAM.
4. **Direct capture:** `tools/mame/scripts/arcade_layera_palette_dump.lua` runs ORIGINAL ARCADE `rastan`,
   coins/starts via the established input injection, and dumps palette RAM.
5–7. **Palette RAM `0x200000..0x2003FF`** (banks 0–31, 16 words each), word = **xBGR-555**
   (R=bits0–4, G=5–9, B=10–14); `arcade_rgb8 = chan*255//31`, Genesis 3-bit = `chan>>2`.
8. **KF-788 validation:** captured bank `0x003` → Genesis 3-bit == KF-788 runtime words **16/16** (machine
   regression anchor). This is an independent existing-project anchor for the new source.
9. **Corrected artifact:** `analysis/graphics_optimizer/round1_phase1_corpus/plane_a_palette_ram_arcade.json`
   holds all 11 Layer-A banks (0x003–0x01D) as xBGR555 + arcade_rgb8, authority = arcade palette RAM.
10. **Exact-content duplicates:** 10 distinct content groups; only `0x01B` == `0x01D`. Selector identity is
    kept separate from content identity (the 11 selectors are not collapsed).
11. **Stability (bounded, honestly scoped):** all 11 banks are byte-identical across sampled R1/P1 gameplay
    frames **360/460/700/1000** (~11 s). This is **NOT** proof of full-Phase-1 per-record invariance. The
    earlier "all 11 banks invariant throughout R1/P1" wording is **withdrawn**; current provenance reads
    *"PROVEN R1/P1 early gameplay; later Phase-1 per-record stability pending."*
12. **Broader proof status:** establishing universality across all 16 records would need a full-phase
    user-driven arcade trace (the dump script can be armed for it); not required for the early-R1/P1
    rendering to be correct, and deferred to the next boundary.
13. **Editor source change:** `plane_bank_colors()` now prefers `plane_a_palette_ram_arcade.json` (fallback
    to the old file only if missing). Both Layer-A RGB paths are corrected: the segment map / tile library /
    `/api/render_tile` (via `build_layera` banks) and the Palettes-tab plane resources in `build_oracle`.
    `plane_palette_banks.json` is retained for its other metadata/Layer-B, but is no longer the Layer-A RGB
    authority.
14. **Map inspector:** clicking a map cell shows segment, X/Y, tile code, physical pattern, logical usage,
    raw attr word, selector (`attr & 0x1ff`), descriptor/entry addresses, flip, occurrences, and the
    palette authority (arcade palette RAM, KF-788 validated).
15. **Sprite preview CSS:** `#previews` is flex; its zoombar/header now take a full-width row
    (`flex:0 0 100%`) with `clear:both`, so preview art starts at the left instead of beside the toolbar.
16. **Regression:** corrected maps render authentic arcade terrain (seg 0 purple/rock, seg 6 purple cliff +
    brown/red rock + green vine, seg 15 purple castle bridge); corpus 1315/1581/199, ΔE/L-H solvers,
    pixel-picking, context, Line-2 protection, and the Test profile all intact.

---

# V0.4.2 Phase-Wide Layer-A Auto-Map

**Workflow:** author a palette on an editable line (0/1/3), keep it as the ACTIVE line, click
`Auto-map Phase → Active Line`. Every Layer-A logical usage in the active PHASE is mapped to the closest
legal entries ALREADY on that line. Target colors are never changed; no palette is derived.

**Why phase-scoped topology:** V0.4.1 kept Layer-A mapping topology global, which cannot hold different
per-phase mappings. This task promotes Layer-A topology to context/phase scope (narrowly; sprite topology
untouched). New model: `context_policies[ctx].plane_usage_palette_mappings`, with the global
`plane_usage_palette_mappings` retained as backward-compatible base/fallback. **Resolution
(`effPlaneMapping`):** global base → ancestor contexts → scope, deepest wins. A phase mapping written at
`context:gameplay.r01.p01` is inherited by all its segment children; a deeper segment/usage override wins;
siblings are isolated; other phases (e.g. `r01.p02`) see nothing from R1/P1. Verified by simulation
(inherit/override/sibling-isolation/phase-isolation all pass) and server save/reload.

**Fixed target line:** the mapper reads the phase-effective colors of the chosen line (base + inherited +
phase-local overrides) and treats populated nontransparent entries (1..15) as fixed candidates. It never
adds colors to empty slots, changes CRAM, reorders, quantizes, or runs a solver. If descendant segment
contexts override colors on that line, the UI warns and matches against the phase-level effective palette.

**Matching:** for each logical usage, sources = its actual used pixel indices' corrected-arcade RGB (from
`plane_a_palette_ram_arcade.json`) with pixel counts; targets = the populated line entries. Cost =
pixel-weighted **CIEDE2000**. A **min-cost injective assignment** (Hungarian, stdlib, O(n³) on a padded
square matrix) guarantees no two distinct used colors in one usage share a target — **MRD violations = 0**.
Objective = minimize pixel-weighted total ΔE00; the injective constraint is hard. This optimizes each usage
against the fixed line only — not a global palette optimum.

**Insufficient capacity:** a usage needing more distinct colors than the line has populated entries is
**BLOCKED** (left unchanged, counted, never merged). Verified: a 2-color line blocks 1517/1581 usages with
0 merges; a 15-color line maps 1576/1581 (5 are blank tiles) with 0 blocked.

**Transaction/Undo:** the whole phase apply is one `pushUndo()` transaction writing into the phase context's
plane mappings; one Undo restores the prior state, Redo re-applies (existing full-POL snapshot mechanism).

**Summary + worst-match browser:** reports considered/mapped/new/replaced/unchanged/blocked, populated
targets, mean/worst ΔE, and "target colors modified: NO". `Show worst matches` lists the 20 highest-ΔE
usages; each row opens that exact usage in Tile Library.

**Live update:** segment-map Genesis mode and Tile Library resolve through `effPlaneMapping`, so the map and
previews reflect the phase mapping immediately; the usage view shows provenance
(`INHERITED FROM Round 1 / Phase 1` vs LOCAL vs global base). Manual per-usage mapping after the bulk op
writes at the active scope and predictably overrides the inherited phase mapping without re-running it.

**Performance:** one server bulk-solve request (no per-usage HTTP). Measured ~1.2 s for all 1,581 R1/P1
usages. **Line-2 protection:** the endpoint and the policy-save guard reject any reserved-line target (403),
in addition to the client button being disabled for Line 2. Arcade evidence artifacts are read-only
(hashes unchanged before/after). Existing ΔE and L/H sprite solvers are unchanged and pass regression.
