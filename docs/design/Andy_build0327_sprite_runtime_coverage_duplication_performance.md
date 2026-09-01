# Build 0327 — Sprite Runtime Coverage, Duplication & Performance Analysis

**Type:** Analysis. No implementation, no ROM. Classification: **EXTENDING**. Baseline Build 0327.
Evidence: static — frozen Test profile, `pc090oj_editor_manifest.json`, and the **arcade-captured** runtime census `analysis/graphics_optimizer/round1_phase1_corpus/sprite_census_captured.json` (arcade = Genesis semantic authority).

## Headline result
The remaining wrong/partial enemies are explained by **two proven static findings**, not a routing/CRAM failure:
1. **Runtime code coverage is grossly INCOMPLETE** — the reindex manifest covers only a base-pose subset of each actor's real animation vocabulary.
2. **The full vocabulary contains cross-bank SHARED codes** — a code-indexed reindex (Build 0325–0327) fundamentally cannot represent them; the complete fix requires the deferred **`(code,bank)` runtime variant selector**.

## 1. Manifest-vs-runtime coverage (captured census)
| Family | eff. bank | runtime codes | covered | missing | visual |
|---|---|---:|---:|---:|---|
| Lizardman | 0x36 | 91 | 35 | 56 | **correct** |
| Valkyrie | 0x32 | 18 | 8 | 10 | **correct** |
| Four-Armed Insect | 0x3A | 106 | 10 | 96 | **partial** |
| Chimera | 0x34 | 148 | 11 | 137 | off |
| Flying Demon | 0x35 | 112 | 26 | 86 | wrong |
| Small Bat | 0x3E | 3 | 1 | 2 | wrong |
| Large Bat | 0x3E | 14 | 5 | 9 | wrong |

**Interpretation:** every family is under-covered; the ones that *look* correct (lizardman, valkyrie) are the ones whose commonly-visible poses happen to fall inside the covered subset. Chimera/demon/bats show poses using **uncovered** codes → raw pixels → wrong. The **partial insect** is the differential proof: within one actor, covered pieces render correctly and uncovered pieces render raw. **Runtime coverage = INCOMPLETE (proven).**

Root cause of the incompleteness: the resolved code sets came from `enemies.json`/`sprite_families` base-pose captures, not the full per-actor `cell_codes` (base form **and** anim form) the census records.

## 2. Cross-bank shared codes (breaks code-indexed reindex)
The full census vocabulary shares codes across effective banks — e.g.:
- `0x0A73–0x0AA2` (2675–2722): banks **0x30, 0x34, 0x36, 0x3A** (shared hit/burst anim across lizardman/chimera/insect/effects)
- `577–594`: banks **0x30, 0x32** (valkyrie body vs valkyrie burst)
- `803–809`: banks **0x34, 0x3A** (chimera fireball vs insect projectile)
- `1293–1303`: banks **0x33, 0x3E** (spear vs large-bat anim)
- `629`: shared by Rastan aux (0x33), flying-demon anim, large-bat anim

A single code with two banks needs two different reindexed cells, which a code-indexed region (one cell per code) cannot hold. My earlier "0 cross-bank collisions" was an artifact of the incomplete `enemies.json` code set. **The complete sprite reindex requires the same `(code,bank)` runtime variant selector deferred for Layer-A.**

## 3. Positive controls
- **Lizardman / Line 1:** visible poses' codes (75–109) are covered → reindexed 128-byte cells on Line 1 with Test-L1 CRAM → correct. Confirms the full chain works when a code is covered.
- **Valkyrie / Line 0:** visible poses' codes (subset of 577–594) covered → Line 0 / Test-L0 → correct.
These establish the correct path on both shared lines; the failures are coverage, not path.

## 4. Rastan (not resolved statically)
The census explicitly **does not capture PLAYER/WEAPONS/AXE/HUD**. Rastan's manifest body codes (138–159, 267–270, 629–631) are covered, yet Rastan is wrong — so his failure is **not** explained by the enemy-coverage data. Candidates: (a) player emits additional uncaptured codes/poses; (b) the shared/cross-bank aux code 629; (c) a player-specific render path. **Needs a Build-0327 Genesis player trace** (armed below).

## 5. Bats / Flying Demon / Insect / Chimera
All show large missing sets (§1). Bats specifically: small bat runtime {616,617,618}, manifest {616}; large bat runtime {1014–1023}, manifest {1014–1017}; plus a shared burst code 629/630. Consistent with incomplete coverage + shared codes.

## 6. Duplicate sprites, palette-vs-duplication, performance — NOT YET PROVEN (need runtime)
The census shows each actor emits a **base form and an "anim form"** as distinct record blocks (overlapping code ranges). This is a plausible source of the "two sets offset horizontally", but whether the on-screen doubling is **gameplay** duplication (two entities) or **render** duplication (base+anim emitted together, or a producer pass) cannot be proven from static data. Performance/slowdown likewise needs a live normal-vs-slow comparison. **Classification: NOT YET PROVEN for duplication, palette-vs-duplication relationship, and slowdown.** A single armed Build-0327 Genesis trace answers all three.

## 7. Recommended Build 0328 scope
**Do not** ship an incremental code-indexed coverage patch — it cannot work (cross-bank sharing). The correct Build-0328 is the **`(code,bank)` sprite reindex + runtime variant selector**:
- resolve the **complete** per-actor `(code,bank)` cell vocabulary (base + anim) from the census;
- offline-generate `(code,bank)`-keyed reindexed cells (128-byte) so shared codes get distinct variants;
- add a bounded O(1) runtime `(code,bank) → variant slot` selection in the sprite pattern-DMA path (the sprite analogue of the deferred Layer-A `(code,bank)` work);
- keep Test Lines 0/1/3 + Layer-A unchanged.
This is a larger build than 0327 and should be scoped as its own task. The armed trace (below) will finalize the player/Rastan vocabulary and the duplication/perf questions first.

## 8. Follow-ups preserved
- **HUD `1UP`/score (bank 0x30)**: add as a first-class Palette Composer editable representation so Tighe authors the white line/index; no hardcoding. (Score still red — deferred.)
- **Axe**: same — future first-class Palette Composer representation.
- **Garbled white-box text screen**: recorded as observation only; not investigated (may or may not share the coverage defect).
- Vertical-fill / noise / epoch tile loss / waterfall animation / cave tiles / Segment-7 tile: deferred, unchanged.

## 9. Armed runtime trace (needs Tighe)
`tools/mame/scripts/trace_genesis_sprites.lua` logs, each frame during play, the staged Genesis SAT (`staged_sprite_sat` @0xFFB26C): active sprite count, per-palette-line histogram, and repeated-tile-at-different-X detection (duplication signal), to a file — for the duplication + performance questions. See final response for the exact play instructions.
