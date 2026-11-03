# Andy — Build 0325 R1/P1 Test-Palette Final Integration — STOP (sprite-reindex data/ambiguity blocker)

**Type:** Implementation attempt → STOP. No ROM. Build 0324 baseline. Classification: EXTENDING.

## 1. Phase 0
Relevant priors/hazards: KF-043 (Line 3 = sprite bank 0x33 today); KF Build-0174 (FG carrier line overwritten by frontend — needs gameplay-boundary re-assert). Deferred: vertical-scroll. Touched issues: none changed. Contradiction status: **sprite-reindex scope blocker (below).**

## 2. Test-profile authority
`build/rastan-direct/build0314/Test.snapshot.json`, SHA `deb696452d7456b3…`. Final ownership: L0/L1 = shared sprite palettes, L2 = Layer B (protected), L3 = Layer-A master. Authored sprite bank→line: L0 ← {0x32,0x33,0x34,0x3E}; L1 ← {0x35,0x36,0x3A}.

## 3. Layer-A → Line 3 half — READY
Fully specified and low-risk: route all authored Layer-A banks → L3 (one rule, remove `bank&3`), stage Test L3 CRAM `0000 028C 044C 0026 0004 0002 0424 0624 0402 0202 0200 0422 0440 0660 0AA6 0884`, re-assert at gameplay boundary. Cave proof `LA-0458` (code 0x070, bank 0x004, map {1:9,2:11,3:6}) already byte-correct in the production region (`888a34a5fc2e5272`). Only the runtime routing (L0→L3) and L3 staging remain.

## 4. The STOP: full R1/P1 sprite reindex cannot be completed/verified now
The prompt requires reindexing **every** live R1/P1 sprite onto shared Test L0/L1 and forbids a raw-palette interim. But:

- **Resolved, build-consumable `(code,bank)` code sets exist only for Rastan (`0x33`, 29 codes) and lizardman (`0x36`, 37 codes)** (`sprite_families.json` proven families). The other five authored R1/P1 enemy banks — **valkyrie `0x32`, chimera `0x34`, flying_demon `0x35`, four_armed_insect `0x3A`, bats `0x3E`** — have **no resolved code set** in `sprite_families.json`/`sprite_frames.json`; their art appears only as prose/partial ranges in `sprite_corpus_r1p1.json` (e.g. flying_demon "57–82, bank 0x35"), not as a production `(code,bank)→index_map→pattern` table like Layer-A. → verification item 4 ("unresolved authored sprite mappings = 0") **cannot be met** for all seven.
- **STOP-#2 risk unresolved:** bank `0x3E` carries **two different** authored maps (`large_bat` vs `small_bat`) and bank `0x33` has **empty ΔE-solver maps** for alt-frames (`rastan_f15828`, `rastan_f16199`: `index_map:{}`, `solver:"delta_e"`). Without confirmed disjoint codes, these same-bank variants cannot be guaranteed selectable by a bounded O(1) `(code,bank)` lookup, and the empty solver maps are ambiguous (identity vs unauthored) — and the standing project rule bars ΔE/solver-derived edits.
- Staging Test L0/L1 while leaving any live enemy on those lines un-reindexed would **miscolor that enemy** (regression); the prompt forbids the raw-palette interim that would otherwise avoid it. So a partial reindex of only Rastan+lizard, while non-regressing for the **cave** (only those two are present in Segment 1), does **not** satisfy the prompt's all-seven requirement.

This maps to STOP condition #1 (live R1/P1 sprite representations lacking an applicable authored reindex) with an associated #2 risk (indistinguishable same-bank variants).

## 5. Recommended resolution
Two clean options for the next prompt:
- **(A) Authorize a cave-scoped Build 0325** limited to the sprites actually live in Segment 1: reindex Rastan (`0x33`→L0) and lizardman (`0x36`→L1) per their Test maps, stage Test L0/L1/L3, route Layer-A→L3. Non-regressing (the other five enemy banks are already unresolved and don't appear in the cave), and it proves the final line architecture + cave purple. The five remaining enemy banks are a documented follow-up once their `(code,bank)` sets are resolved and the bat/empty-map cases disambiguated. This is **not** a raw-palette interim — the handled sprites use the real Test reindex.
- **(B) First resolve the five enemy banks' `(code,bank)` code sets + the bat-variant/empty-map semantics** (a bounded analysis task), then implement all-seven in one build.

Layer-A→L3 is ready under either. Recommend (A) for an immediate, non-regressing cave visual win.
