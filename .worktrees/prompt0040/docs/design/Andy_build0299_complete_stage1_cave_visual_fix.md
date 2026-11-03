# Andy — Build 0299: Complete Stage-1 Cave Visual Fix (per-segment residency)

**Type:** Hybrid analysis / implementation. Baseline: Build 0298. **ROM produced: Build 0299.**

## 1. Phase-0 baseline
- **Priors:** KF-010 (FG→Plane A), KF-014 (tile LUT), KF-015 (scroll +8), KF-011 (arcade VBlank owns
  progression) — STRONG, respected. Cave Part 1/1B/2A + Build 0298 report incorporated.
- **Classification:** EXTENDING (residency architecture; no producer redesign, no PC080SN emulation).
- **Issues:** OPEN-001/018 (native FG/map), OPEN-017 (FG residency). **Contradiction of a STRONG finding:** none.

## 2. STEP 1 — mechanical proof of the remaining divergence (no screenshot inference)
Representative cells traced end-to-end (arcade source → metatile → within-metatile word `= cell*4 +
(strip&3)` → code → LUT → active gameplay residency → resident pattern). The within-metatile index is
self-consistent (generator collects all 16 metatile words; producer selects `cell*4+(strip&3)`), and the
Build-0298 segment-5 cells + hundreds of CORRECT cells prove **there is no within-metatile indexing bug.**

| Cell | code | metatile | LUT | resident vs expected | **classification** |
|---|---|---|---|---|---|
| **Repeated** seg6 s6g2c0 | 0x00AD | 0x17EC | 0x007B | slot 0x7B holds outdoor **0x0434** (sha `d73ff981` ≠ `de8a847b`) | **E: correct LUT slot, wrong pattern resident** |
| **Dark** seg6 s6g2c3 | 0x0219 | 0x17EC | 0x0000 | — | **A: missing residency (LUT=0) → blank tile 0** |
| **Improved** seg5 s4g0c0 | 0x00BD | 0x2024 | 0x0042 | resident == expected (sha `5b20a811`) | **CORRECT (Build 0298)** |

Per-segment histograms (Build 0298 state): seg4 {A:130, E:134, CORRECT:552, blank:208}; seg5 {CORRECT:336,
blank:688 — clean}; seg6 {A:71, E:71, CORRECT:338, blank:544}. **First divergence for both bad classes:
the tile is not in the active (gameplay) residency** — either no slot (A) or a slot occupied by an outdoor
tile (E). Both root-cause to **segments 4 & 6 absent from the active residency.** Not an indexing bug, not a
LUT-mapping bug, not a wrong-metatile bug.

## 3. STEP 1 answers
- **Within-metatile cell→word mapping proven sufficiently:** YES (`word = cell*4 + (strip&3)`; producer
  `cell*8 + (strip&3)*2`).
- **Additional native producer bug beyond residency:** **NO.** The 890+ CORRECT cells and the seg5 result
  prove the producer's cell indexing, LUT lookup, and name-word emission are correct where the tile is
  resident. The repeated pattern is **classification E (wrong pattern resident)**, not a producer bug —
  therefore the native cell-indexing code was **not** touched.

## 4. STEP 2 — the residency architecture
**Budget reality (measured):** the Stage-1 first cave is segment-driven — the arcade tilemap0/BG stays
outdoor (tm0=0, attr 0x0002) through the descent (cave Part 1), so Plane B needs the **outdoor BG resident**
during the cave. Outdoor-BG(854) + cave-FG(4,5,6)(296) + text = **1209 > 1164 slots**; byte-identical dedup
reclaims only 1. But **each single cave segment fits** with the outdoor BG: seg4→1123, seg5→1002, seg6→1153.
So the complete first cave is a **per-cave-segment residency**, runtime-selected by the arcade segment index.

- **Semantic residency selector:** arcade segment index **`a5@0x13E`** (Genesis 0x00FF013E, a **word**; the
  arcade reads/writes it with `.w` ops — `movew %a5@(318)`, `cmpiw`). Segments **4/5/6** → cave residencies
  4/5/6; else outdoor gameplay (1). No player coordinates. Cached by `genesistan_current_pc080sn_tileset_id`
  so a reload happens **only on segment change**, never per frame; not a state machine.
- **Highest safe boundary:** `genesistan_hook_tilemap_plane_a` scene preamble (`.Lscene_preamble_done`) — the
  existing per-frame scene-selection point that already calls `load_scene_tiles` with a5 valid.
- **First-cave residency identity:** distinct new scenes `SCENE_STAGE1_CAVE_S4/S5/S6` (ids 4/5/6), each =
  outdoor BG block ∪ that segment's cave FG ∪ text. The attr=0x0003 `SCENE_GAMEPLAY_CAVE` (id 3) is a
  DIFFERENT/later cave with a different BG and was **not** reused (its BG can't serve the outdoor-BG cave).

**Generator/build changes:** `precompute_pc080sn_tile_lut.py` (per-segment FG collection; 3 cave scenes;
scene-aware slot assignment generalized to all scenes; excluded from a0-source-range/scene_ranges since they
share the gameplay block source and are segment-selected). Makefile + scene_load.s wire 3 new preload
manifests; `load_scene_tiles` dispatches ids 4/5/6 and maps them to the logical gameplay a0 range. Canonical
coverage invariant updated 0x185EB8→0x188EB8 (the 3 preloads add 0x3000 bytes of ROM data).

**Native Plane-A producer change:** the only edit to `tilemap_hooks.s` is the new
`genesistan_select_stage1_cave_residency` helper + one `bsr` at the scene preamble. **The cell-production /
LUT-lookup / name-word code is unchanged** (STEP 1 proved no producer bug).

## 5. Verification (static, exhaustive)
Generator: 7 scenes fit, **VRAM max 1153/1164** (Stage1-Cave-Seg6); Gameplay 1002, Cave-Seg4 1123, Seg5 1002,
Seg6 1153. For **every** nonblank cell in segments 4/5/6, resolved against its own segment's preload:
**seg4 816 cells → 0 dark / 0 wrong-pattern; seg5 336 → 0/0; seg6 480 → 0/0 — ALL CORRECT.** Targets:
0x07FC→0x7B, 0x0800→0x3D9, 0x0806→0x3DE, and the STEP-1 bad cells 0x0219→0x5C2, 0x00AD→0x7B all valid, each
loaded with its correct pattern by the corresponding cave preload. Outdoor gameplay scene unchanged from
Build 0298 (fg 0,5; seg 0 clean; segs 1-3 unchanged pre-existing state — no regression).

**GENESIS NTSC MAME (`genesis`) 30 s trace:** clean (1797 frames, `genesistrace stop`), 995% avg, **no crash /
no unmapped memory**, `fg_cwindow_live=0` (native FG path), and **no spurious per-frame reloads** — confirming
the per-frame selector's cache is correct in the outdoor demo. The automated attract demo stays outdoor
(the cave is later in the demo, cave Part 1), so cave visuals are Tighe's BlastEm/Exodus acceptance. The
segment signal is proven live/word-typed statically; Part 1 runtime-confirmed `a5@0x13E`=4/5/6 in the arcade
cave (same translated code in Genesis).

## 6. Known cost / follow-up
Each cave-segment transition (3→4, 4→5, 5→6) triggers a full-residency reload (BG re-loaded, display-off) →
up to ~3 brief black flashes during the descent. The correctness-first choice reuses the proven scene
system. A flash-free optimization (static BG + per-segment FG-delta reload) is a documented follow-up
requiring a segment-indexed FG slot region. Outdoor segments 1-3 minor FG gaps remain (one outdoor
residency, per task scope; not a regression).

## 7. Frozen / deferred
Plane B: not modified. Collision: not modified (metatile +0x22, native side-channel). Frontend: unchanged.
Missing destructible cave-entrance block: **deferred, not investigated.** Rope: its visual data falls in the
seg4-6 residencies now resident; ownership not separately expanded.

---

**Build-0298 visual evidence incorporated:** YES
**Representative repeated-pattern cell first divergence:** E — correct LUT slot (0x7B) but wrong pattern
resident (outdoor tile 0x0434) because the cave tile's segment is not in the active residency
**Representative dark/missing cell first divergence:** A — LUT=0 (tile in no active residency) → blank tile 0
**Within-metatile cell→word mapping proven sufficiently:** YES (`cell*4 + (strip&3)`)
**Additional native producer bug beyond residency:** NO
**Stage-1 cave semantic residency selector:** arcade segment index `a5@0x13E` (word @ 0x00FF013E), segments
4/5/6, at the `genesistan_hook_tilemap_plane_a` scene preamble; cached by current tileset id
**First-cave residency tile count:** per segment — Seg4 1123, Seg5 1002, Seg6 1153
**VRAM budget:** 1153/1164 (largest = Seg6) — FITS
**Segments 4/5/6 fully represented:** YES (0 dark / 0 wrong-pattern across all nonblank cells)
**Wrong-residency slot contents eliminated:** YES (each segment loads its own cave FG patterns)
**Generator/source changed:** tools/translation/precompute_pc080sn_tile_lut.py, apps/rastan-direct/Makefile,
apps/rastan-direct/src/scene_load.s, apps/rastan-direct/src/tilemap_hooks.s,
tools/translation/{postpatch_startup_rom.py, verify_canonical_rom.py} (coverage invariant)
**Native Plane-A producer changed:** YES — added `genesistan_select_stage1_cave_residency` selector + one
`bsr` at the scene preamble; cell-production/LUT/name-word code unchanged (reason: residency selection needs
a per-frame hook with a5 valid; STEP 1 proved no cell-indexing bug to fix)
**Plane B changed:** NO
**Collision changed:** NO
**Missing cave block fixed:** NO
**Missing cave block deferred:** YES
**Build 0299 produced:** YES
**ROM:** dist/rastan-direct/rastan_direct_video_test_build_0299.bin
**SHA-256:** e039e40eca9d46aec3581c17f1a2c39105ac52bfb2975c8230f50de4133acc07
**Gate:** GATE_PASS (boot guard pre+post PASS; opcode_replace 227; coverage 0x188EB8)
**USER MUST VERIFY:** cave entrance, vertical descent, the repeated green/white/purple region, the
dark/block regions, cave floor/interior, first rope area if reached — and note the expected brief
reload flash at cave-segment boundaries (§6).
