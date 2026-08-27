# Andy — Round 1 / Phase 1 Complete Graphics + Palette Corpus (PARTIAL)

**Type:** analysis only. No production change, no ROM, build counter 313, `palette_decisions.json` untouched.
Corpus at `analysis/graphics_optimizer/round1_phase1_corpus/`.

## Phase 0
Priors read (KNOWN_FINDINGS / OPEN_ISSUES / CLOSED_ISSUES / RULES / ARCHITECTURE / native policy).
- **KF-010** (BG→Plane B, FG→Plane A): CONFIRMED prior, matches this corpus. Applies.
- **KF-028/KF-153** (embedded scene-asset pointer tables): the gameplay scene loader R_c (arcade 0x059DE8)
  loads palettes from the **palette pointer table arcade 0x059EC8 (6 entries)** → blocks
  0x05DB4E/0x05DC4E/0x05DD4E/0x05DE4E/0x05DF4E/0x05E04E (0RGB nibble-packed). This is the R1/P1 plane
  palette source. Rediscovery-Hazard HIGH — treated as canonical.
- **KF-014** (tile LUT O(1)), **KF-020/021** (sentinel/sprite-suppression evidence hazards): noted.
- Task classification: **EXTENDING** (KF-010 plane mapping + KF-153 palette source; extends the
  prior enemy-lexicon +0x3E work). **No CONFIRMED/STRONG prior contradicted.**

## Corpus status — PARTIAL (NOT closed)
**Proven / delivered:**
- **Layer A:** 1316 arcade codes → **1315 unique physical patterns** (records 0–15). `layer_a_tiles.csv`.
- **Layer B:** **854 codes / 854 unique physical patterns** (single R1 vocabulary, KF-010 Plane B).
  `layer_b_tiles.csv`. No capacity dropping.
- **Sprite family map:** actor +0x3E table 0x45502 (11 normal + boss); user anchors reconciled —
  **Lizardman = family 0 (0x4B)**, **Chimera = family 1 (0x00D0)** (Tighe), **Four-armed insect = family
  3 (0x02E8)** (Tighe). **Flying Demon = R1 boss (+0x3E==2, base 0x33E) is WITHDRAWN** — see the Flying
  Demon section below; the demon is a special two-slot `actor_508` composite (base 0x0129), and +0x3E==2 /
  base 0x33E is the *actual* Phase-3 boss (trace-confirmed at record 17). `sprites.json`.
- **Effective sprite bank formula PROVEN:** `(A4+0x27 & 0x0F) | 0x30` (fam0 nibble 0x06 → bank 0x36).
- **Plane palettes DECODED (16 colors, 0RGB):** FG bank 3 (scene-1), BG bank 48. `palettes.json`.

**UNRESOLVED (bounded, not fabricated):**
1. **Sprite 16-color contents** — effective banks 0x31–0x3F proven, but the ROM source of those banks'
   colors is not tied to a decoded table yet (0x059EC8 covers plane banks; sprite-bank source separate).
2. **Real compositor** — arcade 0x3C9A6 + descriptor tables (fam0=0x3D09E … fam4=0x4002C) located but
   NOT decoded → no valid sprite representatives (base+n renderer retired as invalid).
3. **Per-tile FG palette bank** — Layer A uses multiple banks (attr-selected); per-tile bank not decoded.
4. **Category-per-family + 8 unmapped anchors** — Valkyrie/Small Bat/Large Bat/Axe/Flame Sword/Flail/
   Boulder/cave-block owner need spawn-table enumeration + dynamic +0x3E (not run).
5. **Cave-entrance destroyable block** (Tighe: `0x0179`, NOT an enemy) — owner (PC090OJ object vs PC080SN
   terrain) not proven.

## PC080SN/PC090OJ native policy
Semantic cut: arcade owns spawn/family/palette-selector decisions (FUN_0004a086 spawner, +0x3E family,
0x45722 palette nibble, 0x059EC8 palette load). Chip-specific tails downstream = PC090OJ SAT/pattern
emission + PC080SN name-table production (to be native-realized later; not this task). Transitional
compatibility: none introduced. §9: analysis-only, no production tail added.

## Deferred observation (NOT investigated here) — see OPEN-026
The R1/P1 opening Lizardman wave shows duplicate/overlapping native sprite composites (multiple complete
animation poses around one enemy position; occasional missing pieces). Reproduced on Build 0300 and 0313;
Genesis score still accounts for 4×300=1200 like the arcade's four opening Lizardmen, so an extra scoring
gameplay actor is **not** proven. Excess sprite-composite output is observed; root cause UNRESOLVED
(H1 duplicate actor / H2 duplicate render emission / H3 stale SAT pose / H4 VBlank ordering / H5 sprite
limit — all hypotheses). Tracked as **OPEN-026 / DEFERRED**; it does not gate the sprite-corpus audit and
is not being investigated in this task.

## Coverage: user anchors 4/12 mapped (Lizardman, Chimera, Four-armed insect, Flying Demon); corpus **NOT closed** → not yet ready for Genesis optimization. Remaining 8: Valkyrie, Small Bat, Large Bat, Axe, Flame Sword, Flail, Boulder, cave-entrance destroyable block ownership.

## Flying Demon Semantic Correction and Body/Wing Ownership (RESOLVED 2026-08-25)
Resolved from the user-driven original-arcade trace
(`flying_demon_trace/observations.csv`, 34,485 rows) → `flying_demon_trace/flying_demon_capture.json`.
Analysis only — NO palette decode, NO production/ROM change, Build counter unchanged.

**Withdrawn:** `ROUND1_BOSS_flying_demon` (`+0x3E==2` / base 0x33E). That association was wrong. The
Flying Demon is an **ordinary R1/P1 ENEMY/HOSTILE**; `+0x3E==2` / base 0x33E is the *actual* Phase-3 boss
(trace-confirmed present only at record 17, never at records 8/13).
- **Occurrences (proven same enemy):** #1 record 8→9 boundary (spawns as the player crosses the right edge
  of record 8; actor live from frame 6746); #2 record 13 (frames 14459-16784). Identical structure at both.
- **Actor identity — PROVEN-BY-STRUCTURE:** the demon is the **special two-slot `actor_508` composite,
  base 0x0129**. It does **NOT** use the +0x3E family system: `+0x3E=0x00, +0x38=0x00, +0x752=0x00,
  +0x27(attr)=0x80` for all 1,876 rows (base 0x0129 is not a 0x45502 table base; attr lacks the 0x40
  family-palette flag). The prior "ordinary enemy → one of {4..11}" guess is **WITHDRAWN**.
- **Two-component structure — RESOLVED** (two co-located, state-locked actors; not a single actor with a
  piece sub-group, and NOT the previously-hypothesized a5+0x748/a5+0x8c8 aux blocks):
  - component_A `@0x10C508` (idx0) → PC090OJ/OBJ records **57-69**, piece codes **0x0129-0x0155**.
  - component_B `@0x10C548` (idx1) → PC090OJ/OBJ records **70-82**, piece codes **0x014A-0x0177**.
  - shared death animation codes **0x0288-0x02A8**.
- **Physical body-vs-wing assignment — UNRESOLVED:** the trace does NOT prove which component draws body vs
  wings; needs the compositor/pixel decode (out of scope; NO base+n).
- **Damage/lifecycle — STRONGLY COUPLED / state-locked (as observed):** both components share the identical
  observed state every frame (0x03 spawn → 0x04-0x09 living → 0x0F death) and despawn on the same frame
  (16784). Co-occurrence: (09,09)×241 (05,05)×199 (06,06)×145 (08,08)×113 (04,04)×87 (07,07)×75 (0F,0F)×23
  (03,03)×2.
- **Wing-only death — NOT OBSERVED (not proven impossible):** 0 of 885 shared frames show one component in
  death state 0x0F while the other lives. Strong evidence, but the saved trace isolated no wing-targeted
  attack and no static arcade damage-ownership code was analyzed, so exact damage/death ownership is
  DEFERRED — do not overstate absence as universal impossibility.
- **Palette:** Build-0313 palette INCORRECT (user obs); 16-color decode out of scope this task.
- **Compositor:** real compositor (arcade 0x3C9A6 + descriptor tables), never base+n. Piece pixels UNRESOLVED.
- **Round-2 boss wing sharing:** HYPOTHESIS UNPROVEN — compare wing physical-pattern hashes once wing
  patterns are decoded; **semantic identity stays separate even if graphics are byte-identical**.

**Build-0313 differential (OPEN-027 / DEFERRED):** two components exist (A, B); arcade ownership = two
co-located state-locked `actor_508` slots (OBJ 57-69 and 70-82). On Build 0313 one visible component can be
removed while the rest survives, which DIVERGES from the state-locked arcade trace. **ROOT CAUSE UNRESOLVED
— not attributed to the native renderer without proof** (candidate owners: translated gameplay lifecycle
ownership, component state synchronization, native sprite publication/retirement, damage-target ownership).
Palette DEFECT (user). No fix applied.
