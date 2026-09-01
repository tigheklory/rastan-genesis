# Andy — Test-Palette R1/P1 Final Line Ownership — STOP (confirmed scope contradiction)

**Type:** Implementation attempt → STOP (STOP condition 5: confirmed project contradiction). No ROM produced.
**Classification:** EXTENDING. Build 0324 baseline.

## 1. Phase 0
Relevant priors / HIGH rediscovery hazards:
- **KF-043** (durable): gameplay CRAM ownership bank 48→Line 2, **bank 51 (0x33 Rastan)→Line 3**; bank 0x36 (lizard)→Line 0 carrier. Line 3 = sprites today.
- **KF Build 0173/0174**: FG carrier line does not survive frontend `0x59AD4` writes into gameplay; any shared line must be re-asserted at the gameplay boundary.
Deferred: vertical-scroll/wrong-tile (still deferred). Touched issues: none changed. Contradiction status: **one confirmed contradiction found (below).**

## 2. Frozen Test-profile authority
`build/rastan-direct/build0314/Test.snapshot.json`, SHA `deb696452d7456b3…`. Final intended line ownership: Line 0/1 = editor sprite palettes, Line 2 = Layer B (protected), Line 3 = editor Layer-A master.

## 3. Previous first divergence (Layer-A) — READY
For the cave proof `LA-0458` (code 0x070, bank 0x004, map {1:9,2:11,3:6}), stages 1–3 are correct; the production region already holds the expected reindexed pattern `888a34a5fc2e5272`. The Layer-A breaks are only: (6) name-word routing (bank 0x4 → `bank&3` → Line 0) and (7) editor palette staged to Line 1 carrier, not Line 3. **The Layer-A → Line 3 half is fully specified and implementable.**

## 4. The confirmed contradiction (sprite evacuation)
The task authorizes **only a "bounded relocation"** of the sprites off Line 3 and explicitly forbids the full reindex ("Do NOT expand into full `(code,bank)` yet"; "bounded relocation is the only sprite work in scope"). But:

- The **only** live R1/P1 sprite on Line 3 is Rastan (bank `0x33`). Its authored Test destination is **Line 0**.
- Test **Line 0 is a SHARED sprite palette** targeted by banks `{0x32,0x33,0x34,0x3E}` and **Line 1** by `{0x35,0x36,0x3A}`, each via a **non-identity `index_map`** (e.g. `rastan…:bank0x33 → line 0, {1:7,2:8,3:9,4:10,5:2,…}`).
- The **production sprite path applies no reindex**: `pc090oj_assets.s` incbin's raw `build/pc090oj_genesis.bin`; `.L59` stages raw arcade bank→CRAM line (bank 0x33→line 3). Sprites are visually correct today precisely because each bank sits on its own line with its **raw** palette.

Therefore relocating Rastan onto its authored destination (Test Line 0) **with correct colors requires reindexing sprite pixels** (apply the Test `index_map` offline) **and staging the shared Test Line-0 palette** — a full sprite reindex pipeline, the same class of work the task defers. "Bounded relocation through the existing native sprite path" (raw bank→line) **cannot reproduce the authored Test shared-line colors**; using the Test Line-0 palette with raw Rastan pixels would miscolor Rastan (regression), and using Rastan's raw palette on Line 0/1 would **not** be the Test-authored palette (fails verification item 7 and the "implement the final architecture, not a temporary proof" directive).

**This is a confirmed contradiction:** the final Test sprite-line ownership (shared, reindexed) cannot be reached by a bounded, no-reindex relocation, and no raw-palette shortcut satisfies both "sprites visually correct" and "use the Test-authored Line-0/1 palettes / final architecture."

My own pre-implementation review under-specified this (it assumed relocation "through the existing native sprite/palette path" was bounded; the Test sprite lines are shared+reindexed, so it is not).

## 5–8. (not reached — no evacuation/staging/build performed)

## Recommended resolutions (for the next prompt)
- **(A) Authorize the sprite reindex** as part of this work: add offline sprite-pattern reindex (Test `usage_palette_mappings`) + stage Test Line-0/1 shared palettes + route each sprite bank to its Test line. Larger, but it is the true final architecture and mirrors the Layer-A path. Then Layer-A→Line 3 and sprites→Lines 0/1 land together.
- **(B) Split the deliverable:** ship Layer-A→Line 3 now by freeing Line 3 with a **bounded raw-palette** move (Rastan 0x33 → the Line-1 slot freed when Layer-A vacates it; lizard stays Line 0), explicitly documented as an interim sprite arrangement (raw palettes, not the Test shared lines), with the Test sprite reindex as the immediate follow-up. This gives the cave purple + correct sprites now but is **not** the final sprite architecture (so it conflicts with this prompt's "implement the final architecture, not a temporary proof" directive — hence it needs explicit authorization).

Layer-A→Line 3 is ready regardless of which is chosen. Recommend deciding (A) vs (B) before the implementation build.
