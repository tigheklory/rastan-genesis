# Andy — Round 1 Enemy Art Residency Inventory

**Focused data analysis only. No ROM, no production change, counter 359.** Question: should the common
Round-1 cave enemy graphics simply stay resident in Genesis VRAM instead of churning through the
dynamic pool? Evidence: `Cody_build0360_cave_overrun_measurement.md` + its
`cave_overrun_summary.json`; the R1 emitted-code trace
(`round1_phase1_corpus/full_capture/full_observations.csv`, round 01, cave sections 01–03);
`sprite_census_captured.json`; `enemies.json`.

## 1–2. Complete unique art, enemy-specific vs shared

Method: distinct emitted 16×16 codes over the cave interval (1,156 frames), attributed by proven
family code ranges, with frequency-of-appearance to separate **recurring live art** from the **rare
long tail** (death/hurt one-offs, transient effects). Multiple instances of one enemy share art, so
each code is counted **once**; shared art is counted once, not per family.

| Set | Recurring live cells (>~5–10% of frames) | Full distinct over cave (incl. rare states) |
|---|---:|---:|
| **Lizardman-specific** | **~8–10** (matches `enemies.json` curated 0x04F–0x066) | 28 |
| **Small Bat / hurry-up bat** (same family, bank 0x3E, 0x268–0x26A) | **3** | 3 |
| **Large Bat-specific** (0x3F6–0x3F9) | **4** | 4 |
| **Shared enemy splat/death + burst/form** (base-0x0A73 pool + 0x276 + burst, range ≈0xA5A–0xAA2) | **~10** frequently used | 49 (mostly rare / cross-family) |
| other shared (player/HUD/projectiles — *not* back/enemy) | 22–27 | 242 |

**Key data facts:** total distinct cave codes = **327**, but per-frame working set is **median 8,
max 38**, and only **8 codes appear in >20% of frames**. The enemy families are individually tiny; the
big count (327) is the rare long tail. The **0x0A73 "animation-form" producer is the shared
death/effect pool** used across lizard/insect/chimera/valkyrie contexts — its art must be counted
once, not per family (that is why the raw census "Lizardman form = 91" is contaminated up to the
glow-orb range and is *not* Lizardman-specific).

**Combined first-cave enemy working set** (Lizardman ~10 + Small/hurry Bat 3 + Large Bat 4 +
frequently-used shared death/burst ~10, de-duplicated; 0x276 shared once) = **≈ 25–27 unique cells.**

## 3. Cave miss trace

From `cave_overrun_summary.json` (first-cave Segment-1 no-kill, frames 1301–5303, 2,539 publications):

- back/enemy: **83,836 calls → 81,661 emitted** (clipping is *not* the problem — 1,881 rejects);
- **3,345 residency misses, 75,698 victim-loop iterations, 3,051 successful replacements
  (= evictions), 6 no-free, 288 queue-full;**
- worst frame (3123): 44 back calls, **13 misses, 523 victim iterations, 12 replacements** in one
  publication.

3,051 evictions over a **~27-cell common set** means the same small working set is being **thrown out
and reloaded** during bursts (the hurry-up swarm), not that 3,345 distinct arts were needed. **Honest
limit:** the cave capture logged miss *counts*, not the missing *code*, so I cannot prove the exact
per-family split. But an operator route that deliberately keeps Lizardmen + bats alive, in the
back/enemy lane, whose combined recurring art is only ~27 cells, points strongly to **repeated churn
of the common families** as the dominant miss source. The one measurement that would prove it is in §6.

## 4. Genesis VRAM capacity (234-pattern sprite tail)

Sprite tail = patterns 1302..1535 = 234 patterns = 58 complete cells (+2 fragment). 49 in production
today; 61 needs +10 Plane-A patterns, 62 +14, 63 +18, 64 +22.

| Scenario | Cells | Fits 49 | Fits 58 | 61–64 |
|---|---:|---|---|---|
| A. Lizardman (~10) + shared death (~10) | ~20 | **YES** | YES | ample |
| B. + Small/hurry Bat (3) | ~23 | **YES** | YES | ample |
| C. + Large Bat (4) | ~27 | **YES** | YES | ample |
| D. complete common cave enemy set **fixed** + dynamic pool for player/HUD/transient | ~27 fixed | **marginal** (leaves ~22 dynamic for player+HUD, which recur ~22–27) | **YES** comfortably | ample |

So the **enemy set alone fits with room to spare**; the only tightness is fitting the fixed enemy
reservation *and* the still-dynamic player/HUD churn inside 49 — that is comfortable at **58**.

## 5. Recommended residency model — **HYBRID**

Give the common cave families **fixed, phase-resident** Genesis tile ranges (offline
`arcade code → fixed Genesis pattern`, no reverse-index, no miss, no victim search, no eviction, no
reload):
- Lizardman (~10), Small/hurry Bat (3), Large Bat (4), frequently-used shared death/burst (~10) ≈
  **27 fixed cells**;
- keep the **dynamic reverse-index pool** for the transient remainder (rare enemy states, projectiles,
  effects, and — for now — player/HUD animation).

This is not a general allocator: it is a small offline-fixed table for a proven-small, proven-recurring
set, with the existing pool as fallback for everything else.

## 6. Performance implication

The cost structure matters:
- back/enemy **resident-hit** cost = **183,893 lines** over the cave (median **79 lines/frame**) —
  mandatory SAT construction, **untouched** by any residency strategy;
- back/enemy **miss residency work** = **27,150 lines** (median **0**, P95 **54**, max **174**) —
  entirely the churn;
- victim-loop lower bound = 21,620 lines (P95 43.6, max 152).

**Phase-residency of the common families removes the misses themselves** (no victim search, no reload
DMA, no reverse-replace) for those families — plausibly most of the 3,345 back misses. That is
**strictly more than making `.Lnq_vloop` O(1)**, which only cheapens each victim search while the
misses, the reload DMA, and the reverse-replace bookkeeping all remain.

**But be honest about where the win lands:** the miss work is **median 0** — it is concentrated in the
**P95/worst frames (54–174 lines)**, which are exactly the black-bar frames. So phase-residency
**shrinks the worst cave frames and the black bands**, and barely moves the median (which is dominated
by the mandatory resident-hit SAT cost). It attacks the right frames, not the average.

## Verdict

Fixed phase-residency for the ~27-cell common cave enemy set is **viable within current VRAM**,
**targets the black-bar worst frames**, and **subsumes and exceeds** an O(1) `.Lnq_vloop`. It does not
help the median (resident-hit-bound). Confirm the miss-by-family assumption with the small §6
measurement before implementing.
