# Andy — R1/P1 Test-Sprite Semantic Resolution

**Type:** Analysis / data resolution. No production change, no ROM. Classification: **EXTENDING** (extends the Build-0315…0324 Test-palette line toward the Build-0325 sprite reindex).

## 1. Phase 0
Relevant priors / HIGH hazards:
- **KF-043** (durable): current CRAM ownership bank 48→L2, bank 51 (0x33 Rastan)→L3, bank 0x36→L0 carrier. Sprites reindex to shared L0/L1 is the change this resolution feeds.
- **KF Build-0174**: FG carrier line overwritten by frontend; re-assert at gameplay boundary (relevant to L0/L1/L3 staging, not this analysis).
Deferred: vertical-scroll. Issues touched: none. Contradiction status: **none — all live Test sprite mappings resolve.**

## 2. Frozen Test sprite inventory
`Test.snapshot.json` SHA `deb696452d7456b3…`. 10 `usage_palette_mappings` over 7 source banks. Authored ownership: **L0 ← 0x32,0x33,0x34,0x3E; L1 ← 0x35,0x36,0x3A** (matches prompt).

## 3–6. Complete mapping table (every frozen-Test R1/P1 sprite mapping)

Evidence key: `corpus` = `round1_phase1_corpus/enemies.json` + `enemy_patterns.json` (machine-readable `cell_codes`/`base_code`); `family` = `sprite_families.json` proven family codes; `Test` = frozen profile.

| Usage | Family | Bank | Line | index_map (authored) | Exact live codes | Key | Live R1/P1 | Evidence | Status |
|---|---|---|---|---|---|---|---|---|---|
| rastan_f7722 | rastan_player_body (+player_auxiliary) | 0x33 | 0 | 15-entry remap `{1:7,2:8,3:9,4:10,5:2,6:11,7:3,8:12,9:1,10:13,11:14,12:4,13:5,14:15,15:6}` | 138–159, 267–270, 629–631 | (code,bank) | YES | family+Test | **RESOLVED** |
| rastan_f15828 | rastan_player_body | 0x33 | 0 | `{}` (empty, `solver:delta_e`) | (subset of Rastan family) | (code,bank) | YES | Test | **RESOLVED (non-distinct — §5)** |
| rastan_f16199 | rastan_player_body | 0x33 | 0 | `{}` (empty, `solver:delta_e`) | (subset of Rastan family) | (code,bank) | YES | Test | **RESOLVED (non-distinct — §5)** |
| lizardman | stage1_lizardman | 0x36 | 1 | `{1:1..5:5,6:7,7:6,8:8..12:12}` | 75–109 | (code,bank) | YES | family+Test | **RESOLVED** |
| valkyrie | (enemy) | 0x32 | 0 | 15-entry remap | 577–580, 591–594 | (code,bank) | YES | corpus+Test | **RESOLVED** |
| chimera | (enemy) | 0x34 | 0 | 14-entry remap | 208, 422–431 | (code,bank) | YES | corpus+Test | **RESOLVED** |
| flying_demon | (enemy) | 0x35 | 1 | 14-entry remap | 297, 318–329, 362–374 | (code,bank) | YES | corpus+Test | **RESOLVED** |
| four_armed_insect | (enemy) | 0x3A | 1 | 10-entry remap | 744, 747, 756–758, 761–765 | (code,bank) | YES | corpus+Test | **RESOLVED** |
| large_bat | (enemy) | 0x3E | 0 | `{3:1,7:7,10:2,11:3,12:4,13:5,14:6}` | 1014–1017 | (code,bank) | YES | corpus+Test | **RESOLVED** |
| small_bat | (enemy) | 0x3E | 0 | `{3:1,10:2,11:3,12:10,13:11,14:6}` | 616 | (code,bank) | YES | corpus+Test | **RESOLVED** |

**Cross-check:** 0 codes shared across two banks; the only same-bank multi-map case (0x3E) is disjoint (see §4). So **`(code,bank)` uniquely selects one authored `(line, index_map)` for every live representation** (code alone would even suffice; bank is carried in the sprite attribute, so `(code,bank)` is the robust, free key).

## 4. Bat 0x3E disambiguation
**Result: Option A (disjoint codes).** `small_bat = {616}`, `large_bat = {1014,1015,1016,1017}` — **no shared code**. `(code,bank)` therefore selects the correct one of the two authored maps with no additional semantic identity. The two mappings are preserved as distinct (not collapsed, no dominant choice).

## 5. Rastan empty-map semantics
- **Directly proven:** `rastan_f7722` carries the sole non-empty authored Rastan map; `rastan_f15828`/`rastan_f16199` carry `index_map:{}` with `solver:"delta_e"`. All three are bank `0x33`, `rastan_player_body`, line 0.
- **Resolution (no identity inferred):** the empty entries impose **no distinct transformed-pattern requirement** — they are alternate-frame captures of the same actor/bank and introduce no code outside the Rastan family, which is already covered by the authored bank-0x33 map (`f7722`). The offline reindex applies `(bank 0x33 → f7722 map)` across the Rastan family code vocabulary; the empty entries neither override it nor conflict with it. They are therefore **non-distinct/covered**, not authoritative empty mappings. I do **not** treat empty as "identity"; I treat it as "no authored override → no separate requirement." (The project rule bars ΔE/solver-derived edits, so these solver artifacts are explicitly not used as mapping authority.)

## 6. (table above)

## 7. Required runtime semantic key
**`(code, bank)`**, resolved by a flat offline-built lookup (one entry per live `(code,bank)` → compiled slot). Proven sufficient: 0 cross-bank collisions, disjoint bat variants. **No runtime hashing/search/LRU/visibility-scan/pixel-transform** — all transformed patterns compiled offline; runtime does one O(1) `(code,bank)`→slot select feeding the existing native SAT path.

## 8. User-driven evidence
**None required.** Every live R1/P1 sprite mapping is resolved from existing frozen-profile + corpus/family evidence. No new arcade MAME trace needed.

## 9. Readiness for Build 0325
**READY.** All 8 live authored mappings (7 banks) RESOLVED; unresolved live = 0; conflicts = 0; invented = 0; ambiguous runtime identities = 0. The next task can compile the complete Test-authored R1/P1 sprite reindex in one build using `(code,bank)`→`(line,index_map)`, alongside the already-ready Layer-A→L3.

### Observation vs interpretation
- Directly proven: banks, lines, index_maps (Test); exact `cell_codes`/family codes (corpus/family); bat disjointness; zero cross-bank collisions.
- Inferred (flagged): the captured code sets are the complete live vocabulary (bounded by the R1/P1 seven-enemy capture corpus — the authoritative existing evidence; if a later build observes an unlisted `(code,bank)` for these banks it simply adds a table row, no re-architecture); rastan empty entries impose no distinct requirement (argued from bank/family coverage, not from empty=identity).
