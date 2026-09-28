# Andy — Build 0384/0385: Current Test Profile — Burst + Cave Block Authoring

**Agent:** Andy · Implementation / Build / Static Verification. **Baseline: Build 0383 (canonical=PASS).**
**Andy performed NO gameplay/visual verification — authority: TIGHE.** No H25.

> **Build-number outcome (standing imperative — nothing withheld/deleted/reused):** Build **0384** built
> canonical=PASS for the base + `_d` + `_s` + `_do`, but the `_c` (MODE-cheat) variant failed its coverage
> invariant, leaving the family incomplete — a mechanical defect. Per the prompt ("preserve 0384, fix the
> defect, produce full Build 0385"), the four 0384 artifacts are preserved and the cheat-variant coverage
> delta was fixed, yielding the complete **Build 0385** family (canonical=PASS, all five variants). **Build
> 0385 is the candidate.** Counter 383 → 385.

## 1. Phase 0
Read `PROMPT_TEMPLATE.md`, `RULES.md`, `ARCHITECTURE.md`, `CLAUDE.md`,
`PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`, then `KNOWN_FINDINGS.md`/`OPEN_ISSUES.md`/`CLOSED_ISSUES.md`
(ledgers lag Sept work; priors only). Priors: KF-043/046 (sprite bank→CRAM-line route), KF-068/069/074
(native sprite pipeline, emit-time effective bank), the Build-0381/0383 (code,bank) variant architecture.
**Classification: EXTENDING** (extends the existing variant pipeline to the newly authored burst object and
generalizes the single-block selector to multiple blocks; no new mechanism). **KNOWN_FINDINGS impact:
Option A** (no new durable finding; mechanism captured in manifest/`.inc`/index + this doc).

## 2. Current Build-0383 baseline
Build 0383 canonical=PASS (base SHA `7dc486a4…`). Its authoring input = frozen `build0381/Test.snapshot.json`
(SHA `31dedf43…`). Not rewound to 0380; 0381/0382/0383 preserved, not reused.

## 3. Current Test.json SHA (Step 1 freeze)
Live editable source `analysis/graphics_optimizer/editor_policy/Test.json`: **SHA
`02d0122a7d9ea91040f24350d299772f7f37196957eaa7e9b2f627bd9e47e250`**, profile_id `Test`, **revision 30**,
modified 2026-09-28T10:44:52Z, context `gameplay.r01.p01`, local overrides mechanically = the 14 authored
`usage_palette_mappings` (Rastan + 4 weapons + 7 enemies + cave + burst; plus 2 empty legacy rastan_f* keys)
+ the `context:gameplay.r01.p01` plane overrides. Editable Test.json NOT mutated during the build.

## 4. Build-0384/0385 frozen snapshot SHA
`build/rastan-direct/build0384/Test.snapshot.json` = **SHA `02d0122a…`** (byte-identical to the live
Test.json at freeze). This frozen snapshot is the source consumed by the build (Makefile
`EDITOR_LAYERA_SNAPSHOT`).

## 5. Exact Build-0383 → current-Test profile diff (Step 2)
Against the frozen Build-0383 input (`31dedf43…`):
- **`object:player.rastan`** (index-map change): index **12: 0 → 5**; line 0 unchanged (Tighe re-authored the
  Rastan body). All other Rastan indices unchanged.
- **`usage:burst:bank0x30`** ADDED: line 0, index_map `{2:11, 3:1, 9:6}` (new authored effect object).
- **`usage:cave_block:bank0x3C`** CHANGED: **line 3 → 0**; index_map `{1:5,7:2,8:1,9:3,12:3,13:3,14:1}` →
  `{1:7,7:1,8:9,9:4,12:2,13:5,14:10}`.
- **`context_policies`** (`context:gameplay.r01.p01`) changed (plane-A context overrides).
- **CRAM (`target_palette_lines`): UNCHANGED.**
- No mapping removed. Enemy + weapon maps unchanged.
Every one of these is compiled as-is (no screenshot inference, no auto-optimize).

## 6. Cave Entrance Block mapping (Step)
`object:hazard.cave_block`, map key `usage:cave_block:bank0x3C` (reused; no duplicate key). Cells 0x0179–
0x017C (proven 2×2 composite), effective bank 0x3C. Authored line **0**, map
`{1:7,7:1,8:9,9:4,12:2,13:5,14:10}`. Generated coverage: **4/4** cells reindexed and byte-verified. Because
the authored line is now 0 (was 3), the generated palsel LUT routes scene-1 bank 0x3C → line 0 (see §14).

## 7. Burst / Impact Effect mapping (Step)
`object:effect.burst`, map key `usage:burst:bank0x30`, effective source bank 0x30, authored line 0, map
`{2:11, 3:1, 9:6}`. Cells derived from the compositor VM (base 0x0275) = the same decompilation source the
Palette Composer uses (not a hand-added raw code list). Burst renders cells **0x28E–0x2A8**, which
flying_demon (bank 0x35) also uses → burst is a divergent variant (base = flying_demon 0x35, kept in place;
burst 0x30 = appended variant cells).

## 8. Burst 0x9E/0x9F/0xA0 coverage (Step)
| Form | pieces | generated variant cells | missing |
|---|---|---|---|
| 0x9E | 8 | 8 | 0 |
| 0x9F | 9 | 9 | 0 |
| 0xA0 | 10 | 10 | 0 |
Total 27 burst codes (0x28E–0x2A8), all bank-0x30 variant cells generated + byte-verified. One shared
palette identity (`usage:burst:bank0x30`), not three.

## 9. Complete current authored-object coverage (independent verifier, Step 10)
`verify_reindexed_pc090oj.py` recomputes every base + variant cell from raw pixels + the frozen maps and
asserts equality against the built region. Result: `total (code,bank) requirements 916 · unique codes 793 ·
base cells 793 · variant cells 123 · cross-bank divergent 75 (all-distinct 75, bad 0) · mismatched 0 ·
incomplete 0 · unexpectedly-raw 0 · stray 0`. **VERIFY: PASS.**

| Object | Required | Generated | Missing | Mismatch | Raw non-identity |
|---|---|---|---|---|---|
| Rastan (object:player.rastan) | 344 | 344 | 0 | 0 | 0 |
| Sword / Axe / Hammer / Fire Sword | 10 / 12 / 17 / 10 | same | 0 | 0 | 0 |
| Lizardman (0x36) | 91 | 91 | 0 | 0 | 0 |
| Valkyrie (0x32) | 18 | 18 | 0 | 0 | 0 |
| Four-Armed Insect (0x3A) | 106 | 106 | 0 | 0 | 0 |
| Chimera (0x34) | 148 | 148 | 0 | 0 | 0 |
| Flying Demon (0x35) | 112 | 112 | 0 | 0 | 0 |
| Small Bat / Large Bat (0x3E) | 3 / 14 | same | 0 | 0 | 0 |
| Cave Block (0x3C) | 4 | 4 | 0 | 0 | 0 |
| Burst (0x30) | 27 | 27 | 0 | 0 | 0 |

**Rastan retention (Step):** compiled the CURRENT authored map (index 12 → 5); NOT silently replaced with the
Build-0383 value. Verifier confirms all 344 Rastan cells match the current map (0 mismatched). The Rastan
index-12 change is reported in §5.

## 10. Semantic variant generation + generalized runtime selector (Steps 4/6/7)
`gen_reindexed_pc090oj.py` (durable pipeline, extended — no parallel generator) now consumes the burst object
(via the compositor VM), and its variant layout is **generalized to multiple divergent code blocks**: 75
divergent codes in **2 blocks** — `0x28E–0x2A8` (base flying_demon 0x35; variant burst 0x30) and `0xA73–
0xAA2` (base lizardman 0x36; variants chimera 0x34, four_armed 0x3A). Base cells (flying_demon, lizardman,
all Rastan/weapons/other enemies) are byte-identical to the code-indexed model; **123 variant cells** are
appended (region 4096 → 4219 cells). Divergent variants are never collapsed/dominant-overwritten; the
generator asserts 0 dedup and consistent per-bank ordinals.

Runtime selector (`pc090oj_hooks.s`) — the minimal mechanically-required extension of the existing single-
block selector: replaced the single `[LO,HI]` range test with a per-code `pc090oj_variant_group_base[code]`
(u16; 0xFFFF = not divergent) lookup, plus the existing `pc090oj_variant_bank_slot[effective_bank]` (now the
bank's ordinal within a group). `vi = group_base + ordinal`. Same variant-key/residency/DMA machinery (key
`0x2000|vi`, reverse key `0x1080+vi`, source `region+vi*128`) — **no new mechanism, no runtime recolor, no
PC090OJ emulation**. Bounded O(1) (one u16 read + one byte read), using the exact effective bank the palette-
line path already resolves at `.Lnq_hit`. Confirmed in the ROM by symbol + disassembly (`group_base` @
0x081284, `bank_slot` @ 0x083284).

Generated index: `pc090oj_sprite_variants.inc` (constants + group_base + bank_slot) and
`build/regions/pc090oj_variant_index.json`. **All pixel remapping stays build-time Python; no mapping tables
in assembly beyond the compact O(1) index; no runtime nibble transformation.**

## 11. Verifier results
See §8/§9. PASS: missing 0, mismatched 0, incomplete 0, unexpectedly-raw 0, stray 0, divergent all-distinct.

## 12. Build 0383 → 0385 diff (Step)
Classified:
1. **authored CRAM changes:** none (target_palette_lines unchanged).
2. **authored index-map changes:** Rastan index 12 (0→5) → re-transformed Rastan cells; cave re-authored
   (line 3→0, new map) → re-transformed cave cells + palsel route change; burst added.
3. **cave-block offline graphics:** 4 cells re-reindexed to the new authored map.
4. **burst offline graphics:** 27 appended bank-0x30 variant cells.
5. **other current-profile-derived sprite graphics:** none beyond the above (enemy/weapon base cells
   unchanged).
6. **generated semantic-variant metadata:** `pc090oj_variant_group_base` (u16×4096 = 8 KiB) + `bank_slot`
   table + variant index + manifest.
7. **build number/header/checksum.**
8. **tooling/generated provenance:** palsel LUT regenerated (scene-1 bank 0x30→0, 0x3C→0, authored);
   coverage invariants updated 0x1A7EB8 → 0x1A9EB8 (both files); palsel-LUT `--verify` made profile-
   authoritative for authored special/fallback banks; cheat-variant coverage delta +0x1000 restored.
9. **other: ZERO** unrelated gameplay change. `opcode_replace` unchanged at 230 (no NOP/RTS). ROM size grew
   +0x2000 (the 8 KiB group_base table; the appended variant cells relocate within the region).
**No H25 / collision / movement / rope / third-chain / player-state / animation-selection / map-background /
collectible-system change.**

## 13. Complete five-ROM matrix (Build 0385 candidate)

| Variant | Path | Size | SHA-256 | Status |
|---|---|---|---|---|
| base | dist/rastan-direct/rastan_direct_video_test_build_0385.bin | 1744568 | db5d3f74d6bd56ab8dd35ca515f18449945c32cb9a38994f547d798d89ae10b9 | built |
| _c | …_0385_c.bin | 1748664 | 4d4395c01ed2e6c4b875df6a25224f2d8dbff3e5c7764e7d37622e25801fb499 | built |
| _d | …_0385_d.bin | 1744568 | c59a2c8f7cf99e6057bd0e8f546e36163c5bc7522399e559ebce0f9bb28558ef | built |
| _do | …_0385_do.bin | 1744568 | 64b5c15add2b81ece82527ced244b642f9156a271e6d5fab0205b85e9541f77d | built |
| _s | …_0385_s.bin | 1744568 | ed887ece96f04054521fff83b06e86181984f9d1ff2423292fb563fe371c84c1 | built |

`verify-variant-set` PASS. Preserved incomplete Build 0384 (base SHA `…`, plus `_d`/`_s`/`_do`; `_c` never
produced) — `canonical=PASS entry=PASS epoch=FAIL`, not deleted.

## 14. Gates
Build 0385: canonical **GATE_PASS**; boot guard PASS pre+post; `entry=PASS`; `verify-variant-set` PASS;
independent reindex verifier PASS; palsel-LUT `--verify` PASS (0 mapping/SAT mismatches; scene-1 bank 0x30→0
authored burst, 0x3C→0 authored cave; unauthored banks unchanged). `epoch=FAIL` = the pre-existing Phase-1
seven-epoch gate (FAIL on every recent build); ROM numbered+preserved per the standing imperative. A 30 s
Genesis-NTSC smoke trace ran as build sanity; Andy performed no manual gameplay verification.

## 15. Known unresolved — neutral/vertical Fire Sword flame
DEFERRED. Tighe's held Fire Sword mapping was NOT altered. No mechanically-provable separate vertical-state
flame component was added; if it is a distinct semantic object it needs new authoring. Build not blocked.

## 16. Known unresolved — world pickup / power-up palettes
DEFERRED. World pickups are NOT proven to be the same graphics-semantic objects as the equipped weapon
overlays; the collectible/power-up system is a separate decompilation target. No pickup graphics were mapped
using held-weapon mappings. Build not blocked.

## 17. Architecture compliance (policy §9)
CONFIRMED. Semantic-boundary variant selection from arcade effective-bank state; no chip mirror/shadow/
device/projector; no runtime recolor/nibble transform; no PC090OJ emulation; no object-RAM mirror
restoration; no Genesis loop/frame authority/boot re-entry; no scaffolding. PC090OJ object-RAM tail remains
retired.

## 18. USER MUST VERIFY — TIGHE
Load a Build-0385 variant and verify: (1) Cave Entrance Block palette; (2) Burst / Impact Effect palette in
all visible forms (0x9E/0x9F/0xA0); (3) Rastan body correct (incl. the index-12 re-author); (4) held weapon
palettes unchanged except intentional edits; (5) enemy palettes as authored; (6) neutral Fire Sword flame
remains a known separate issue; (7) world pickup/power-up palettes remain a known separate issue.

## 19. Open/Closed Issues Impact
OPEN-006 advanced (burst + cave now production-authored + compiled; complete enemy + weapon coverage
retained). Not closed pending Tighe's visual verification. Fire Sword vertical-flame and world-pickup palette
systems remain documented follow-ups. None closed/deferred as resolved.

## 20. KNOWN_FINDINGS impact
Option A — No new finding to index (EXTENDING; mechanism captured in the manifest/`.inc`/index + this doc).
