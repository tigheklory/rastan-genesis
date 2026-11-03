# Build 0326 — R1/P1 Test-Palette Playtest Analysis (shareable)

**Build 0326** = Build 0325 + the score/1UP HUD display flag (`RASTAN_GAMEPLAY_HUD_SPRITES=2`).
ROM: `dist/rastan-direct/rastan_direct_video_test_build_0326.bin` (SHA `4fe84b43…`).
Baseline: Build 0325 (SHA `3691f6d9…`). Frozen Test profile SHA `deb696452d7456b3…`.
Source of observations: Tighe's 16-segment playtest of Build 0325.

## What works
- **Layer-A background palette is correct** across all segments: cave stone renders purple/mauve, the waterfall teal, exterior rock/sky correct. The Build-0325 architecture — all authored Layer-A source banks → Genesis **Line 3** (one generalized rule, `bank&3` fallback removed) + the exact Test Line-3 CRAM re-asserted each gameplay VBlank — is confirmed good in-game.
- **Lizardman** looks ~correct (see #1 for why this is coincidental).

## Confirmed defects

### 1. Enemy sprite palettes wrong — ROOT CAUSE FOUND (offline reindex stride bug)
**Symptom:** every enemy except lizardman shows wrong colors vs the Palette Composer target — Rastan, valkyrie, chimera, flying demon, four-armed insect, small+large bat. Lizardman looks about right.

**Root cause (proven):** the runtime addresses PC090OJ sprite patterns by **`code * 128`** (a 16×16 cell = 4×8×8 tiles = 128 bytes; `pc090oj_hooks.s:2038 mulu.w #128,%d0; lea rastan_pc090oj`). The offline reindex `tools/graphics_editor/gen_reindexed_pc090oj.py` reindexed at **`code * 32`** (8×8 tile stride) and only 32 bytes. So it wrote the wrong offsets and wrong length — the actual runtime sprite cells were never reindexed and still contain **raw** arcade-index pixels.

**Evidence:** for valkyrie code 577, the runtime cell `pc090oj_editor.bin[577*128 : +128]` is byte-identical to the raw preconverted region (untouched), while my erroneous write landed at `577*32` (a different, unused cell). Same for lizardman (75) and large_bat (1014).

**Why lizardman still looks right:** its authored `index_map` is near-identity (`1:1,2:2,3:3,4:4,5:5,6:7,7:6,8:8…12:12`). Raw pixel index `i` rendered against the (correct, staged) Test Line-1 palette lands on ~entry `i`, which for an identity map equals the intended color. Enemies with heavy remaps (valkyrie i1→L0:7, etc.) show raw index `i` where the intended color is at entry `map[i]` → wrong.

**Conclusion:** the semantic resolution (Andy_r1p1_test_sprite_semantic_resolution.md), the `(code,bank)` maps, the route-table lines, and the Line-0/1/3 CRAM staging are all correct — **only the offline reindex stride/length is wrong.** The sprite palette **line routing and CRAM staging are working** (proven separately: staged Lines 0/1/3 == Test exactly, and lizardman renders acceptably on Line 1).

**Fix (next build):** in `gen_reindexed_pc090oj.py`, reindex each resolved code's **128-byte cell** at `code*128` (apply the cell's `index_map` to all 128 bytes / 4 sub-tiles), not a 32-byte tile at `code*32`. No other change needed; then enemies should match the tool.

### 2. Vertical-scroll leaves tiles unpopulated (DEFERRED vertical-fill bug — confirmed, broader)
Missing/black tiles appear when scrolling **up** (ladder climb), **down** (jump-down, Segment 5), and **across epoch/residency boundaries** (Segment 14 — occurs *just before* the rope, i.e. at the epoch crossing; the rope is not the trigger). **Collision still works**, so this is a render/fill issue only. This is the previously-deferred Plane-A vertical-fill defect, plus an **epoch-residency-transition tile drop**.

### 3. "Vertically-moving horizontal noise band"
A **horizontal strip of noise pixels that moves vertically** through the screen, seen across many segments. It is **not** palette (all palette work is offline/preprocessed). Most likely the vertical-fill producer writing a partial/stale/garbage FG row into the staging buffer that then scrolls with the plane — i.e. the same subsystem as #2. No new per-frame rendering work was added in 0325/0326 beyond the static-palette re-assert (which only writes CRAM Lines 0/1/3, not tiles).

### 4. Waterfall palette animation lost
The arcade's cycling-palette waterfall animation is gone because the offline reindex bakes **static** palettes. The Genesis can do palette-based (CRAM-cycling) animation; restoring it is future work (runtime CRAM cycle on the waterfall entries, outside the frozen static staging).

### 5. Entity duplication ("double sprites")
Too many chimeras / lizard men on screen — a **pre-existing** entity-duplication glitch (noted before), independent of the palette work, and a likely resource drain.

### 6. Unmapped auxiliary sprites
The **axe** (thrown weapon) and the **HUD score digits** are not in the Test sprite reindex/palette set, so they show wrong colors (expected — not yet mapped). The score digits are now *displayed* in 0326 (flag on) but use an unmapped palette.

### 7. Minor: one odd Layer-A tile (Segment 7)
A single Layer-A tile shows an odd palette — likely a specific `(code,bank)` outside the covered set or a dedup edge; low priority.

### 8. Cave "wrong tiles" (Segment 2+): DEFERRED, not addressed here (separate from palette).

## Recommended next steps (priority order)
1. **Fix the sprite reindex stride** (`code*128`, 128 bytes/cell) and rebuild — highest impact, small change; makes all enemies match the tool.
2. **Vertical-fill / epoch-residency tile loss** (defect #2) and the noise band (#3) — same subsystem.
3. Map the **axe** + **HUD score** palettes.
4. Restore **waterfall palette animation**.
5. Resolve **entity duplication**.
