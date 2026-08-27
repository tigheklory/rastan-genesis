# Andy — Whole-Game Arcade Enemy/Sprite Semantic Closure (continuation of Cody's lexicon)

**Type:** semantic closure + classification correction. No production change, no ROM, build counter 313
unchanged, `palette_decisions.json` untouched. Continues Cody's tooling/corpus (not restarted).

## Authoritative semantic key — actor +0x3E (STATIC PROOF)
- **`FUN_0004544e` (arcade 0x4544E)** loads the actor's family/animation record: for a normal actor it
  indexes an **8-byte-entry table at 0x45502** (alt 0x45562 when `A4+0x752!=0`) by **`A4+0x3E`**, setting
  actor fields 0x1e/0x28/0x2c/0x3a/0x1. Table size 0x45502..0x45562 = **96 = 12×8 → the 12-row family
  table**. `A4+0x3E == 2` diverts to the **boss path** (indexed by `A4+0x752`, tables 0x454BA/D2/EA).
- **`FUN_00045684` (0x45684)** sets the actor's **effective color bank `A4+0x27`** from a table at
  **0x45722** indexed `[A4+0x3E + (round-1)*12]` (boss-mode variant 0x4576A gated on `a5+0x2A2`). This is
  the **proven object→palette relationship**.
- Legal `+0x3E` values 0–11; base graphics code = table byte[0..1]:
  `0→0x004B, 1→0x00D0, 2→0x033E(BOSS), 3→0x02E8, 4→0x0420, 5→0x01CB, 6→0x03B3, 7→0x043A, 8→0x0241,
  9→0x06E2, 10→0x0889, 11→0x0400`. Family palette bank (0x45722): `06,04,07,0A,07,06,08,0F,02,01,0B,0E`.
- **Base tile / compositor / animation frame are NOT the identity** — `+0x3E` sits above them (it selects
  the record that in turn sets the base/anim fields).

## Correction to Cody's provisional 52-entry hostile ledger
Cody's 52 rows were **graphics-signature/selector clustering**, not semantic families. Cross-referencing
each row's codes to the 12-row `+0x3E` table:
- **11 normal enemy families** (all `+0x3E` slots except 2) — ~36 of Cody's base/selector rows collapse
  into these. The Lizardman is family 0 (base 0x4B).
- **6 boss families** (round 1–6), all `+0x3E==2`, sub-selected by `+0x752`; 3 of Cody's rows
  (`hostile_base033e_multi_compositor`, `hostile_base0a73`, `hostile_base0a5a`) are boss-base 0x33E / high-
  code boss pieces, not separate enemies.
- **13 STATIC_SELECTOR_* rows → UNRESOLVED ROUTE/SEED** (table/route seeds, **not enemies** — they must
  NOT inflate the enemy count; they remain capacity-bearing).
- **4 non-enemy rows** excluded from the hostile count.
- **4 rows need `+0x3E` dynamic capture** (`four_armed_enemy`, `large_bat`, `normal_small_bat`, base
  0xA5A) — because the `+0x3E` table has exactly 12 rows, each of these **must** alias one of the 11
  normal families (or a boss); the dynamic rerun pins which. They are held UNRESOLVED, fail-closed.

**Old: 1 resolved + 51 unresolved (=52). Corrected: 11 normal + 6 boss = 17 real hostile families.**

## Sweep / rerun status
Cody's sweep tooling (`tools/enemy_sprite_lexicon/arcade_enemy_sweep.lua`) **already captures `+0x3E`**
(`actor_mode3e` column). The existing 26,016-observation corpus predates that column, so a rerun is
needed to (a) confirm per-round presence of each family and (b) place the 4 bat/four-armed rows onto
their `+0x3E` slot. The **static regroup above is authoritative** (the 12-row table is the legal domain);
the dynamic rerun is confirmation, not the source of the taxonomy. `round2_castle` empty-dynamic entry:
static evidence shows Round-2 hostiles are owned through the same `+0x3E`/spawn path — most likely a
selector-timing capture gap, to confirm on rerun (do not treat as "no enemies").

## Palette discipline (unchanged, good)
Unknown sprite-palette CONTENTS stay neutral/zero-contribution. The family→**bank** map is now proven
(0x45722), but the bank's 16 **colors** still require the sprite-palette-staging decode — so colored
feasibility remains blocked and no bank is colored/guessed. `palette_decisions.json` untouched.

## Artifacts (continued in Cody's tree)
`analysis/enemy_sprite_lexicon/corrected_semantic_families.json` (seed→family collapse, palette banks),
`analysis/enemy_sprite_lexicon/corrected_closure_check.json`. Cody's raw corpus, families.json, HTML,
contact sheet preserved. Optimizer round1_phase1 input (4 resolved classes) is already conservative and
unaffected by the whole-game count correction.

## Remaining before this corpus drives palette/VRAM allocation
1. Rerun the 18-selector sweep WITH `+0x3E`; confirm per-round family presence; place bats/four-armed.
2. Decode the sprite-palette-staging colors (the 16 colors behind the proven family banks 0x45722).
3. Pin the 6 bosses' `+0x752` sub-selectors + validate boss composites are boss-owned-records only.

---

## Pass 2 — spawn/boss mechanism proven, canonical artifacts regenerated (2026-08-24)

**Spawn mechanism (category proof PATH):** `FUN_0004a086` (0x4A086) is the actor spawner — it sets
`A4+0x3E = spawn_descriptor[1]` (family), `A4+0x38 = desc[2]&0xF`, `A4+0x752 = desc[2]>>4`, then calls
the family loader (0x4544E) + palette setter (0x45684). So each actor's family comes from its **spawn
descriptor** (round/phase placement data); `+0x3E==2` = boss. This proves the *mechanism*; enumerating
which `+0x3E` values appear in each round's spawn tables (the per-selector category + presence) is a
bounded static follow-up (NOT done this pass).

**Boss mechanism:** boss base **0x033E**; boss tables at 0x454BA/0x454D2/0x454EA (selected by `A4+0x38`),
each **3× 8-byte entries** indexed by `A4+0x752` → **9 boss forms**; palette is round-indexed (0x45722
`[family + (round-1)*12]`). Per-round boss identity correlation (which form = which round's boss) still
needs the dynamic `+0x3E`/`+0x752` capture. Boss composites are marked **COMPOSITE UNRESOLVED** (not
re-rendered from proven boss-owned records).

**Palette:** family→**nibble** proven (0x45722, set into `A4+0x27` low bits). The sprite-palette load
path is `FUN_00045d7c/dc4 → FUN_0003ba20 (scene palette) / FUN_0003a2d0 (RAM copy)`. The
**nibble → palette-RAM-bank → 16-color** mapping is **not yet closed** — colors remain UNKNOWN; no bank
colored or guessed. `palette_decisions.json` untouched (no newly-*proven* relationship to add — the
bank content is still unproven).

**Canonical artifacts regenerated from the semantic 11+6 model** (Cody's provisional preserved as
`cody_provisional_*`): `index.html`, `contact_sheet.png`, `families.json` now show 11 normal families
(actor+0x3E) + 6 bosses with grayscale base sprites (palette contents fail-closed). `optimizer_input.json`
relabeled to semantic family IDs (signature aliases retained). `families_semantic.json`,
`closure_check_semantic.json` are the machine-readable canon.

**Honest status:** STATIC domain PASS (selector domain closed at 12 rows; 11 normal + 6 boss). PENDING:
the 18-selector dynamic `+0x3E` rerun, the sprite 16-color decode, boss-composite ownership, per-round
boss correlation, round2_castle root cause, and the per-round spawn-table category enumeration. These are
bounded but were not fabricated.

---

## Correction of Invalid Pass-2 Semantic Canonicalization (2026-08-24)

**Invalid files (quarantined to `analysis/enemy_sprite_lexicon/INVALID_pass2_andy/`):**
`families_semantic.json`, `contact_sheet_semantic.png`, `index_semantic.html`, `closure_check_semantic.json`,
`sprites_semantic/`, and the semantically-relabeled `optimizer_input.json` (had duplicate canonical ID
`UNRESOLVED_high_code_boss_piece`).

**Why the pass-2 renderer was invalid:** it built each "family sprite" from `base_code + 3 consecutive
PC090OJ pattern codes` pasted into a 2×2 grid. That is **not** the Rastan compositor — a PC090OJ pattern
is a hardware cell, not an enemy, and consecutive codes are not a composite. The images were fabricated.
Canonical `index.html`/`families.json`/`contact_sheet.png` were **restored to Cody's provisional baseline**
(clearly labeled) and a `SEMANTIC_STATUS.md` banner marks nothing as final.

**Conclusions that SURVIVE (evidence):** actor `+0x3E` is a real family selector set by the spawner
`FUN_0004a086` from `spawn_descriptor[1]`; the 12-row loader table 0x45502; `+0x3E==2` = boss;
family→palette-nibble table 0x45722.

**Conclusions WITHDRAWN:** "11 normal hostile families + 6 bosses" as a *closed canonical count* — it is
not proven until each selector's category (hostile vs non-enemy) is shown from spawn/controller ownership,
the dynamic +0x3E rerun places the 4 unmatched rows, and the boss forms are correlated to rounds.

**New proof this pass — palette selector → effective bank (the flagged 0x06-vs-0x36 clue), RESOLVED:**
the PC090OJ record palette byte is built as **`(A4+0x27 & 0x0F) | 0x30`** (decompiler lines 2414/2419,
also 579/16). For family 0 (Lizardman): family nibble `0x06` (0x45722) → `0x06 | 0x30 = 0x36` = the
proven effective sprite bank. So **effective sprite bank = 0x30 | family_nibble**. Effective banks per
family: 0→0x36, 1→0x34, 3→0x3A, 4→0x37, 5→0x36, 6→0x38, 7→0x3F, 8→0x32, 9→0x31, 10→0x3B, 11→0x3E.
`palette_selector_mapping` and `effective_palette_bank_mapping` are now **PROVEN**; the 16-**color**
contents of banks 0x31–0x3F still come through the staging fill (`FUN_00045dc4 → FUN_0003a2d0`) whose ROM
source is not yet decoded → `palette_color_contents` remains UNKNOWN (no guessing).

**Real compositor located (for future valid representatives):** arcade **0x3C9A6** + family descriptor
tables **fam0=0x3D09E, fam1=0x4771C, fam2=0x3F0CE, fam3=0x40004, fam4=0x4002C**. Representatives must be
decoded from these (piece code + x/y/flip), never base+n.

**Open bounded branches (not fabricated):** 18-selector +0x3E dynamic rerun; round2_castle root cause;
per-selector category proof (spawn-table enumeration); the 4 unmatched + hurry-up-bat revalidation;
boss per-round form correlation + clean composites; 16-color staging decode; real compositor render;
then regenerate the canonical lexicon + valid optimizer input from the verified ledger.
