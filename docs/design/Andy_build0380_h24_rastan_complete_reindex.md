# Andy — Build 0380: Complete H24 Rastan PC090OJ Reindex Coverage

**Agent:** Andy · Implementation / Build / Static verification. **Counter 379 → 380.**
**Andy performed NO gameplay verification — Tighe owns all gameplay/visual acceptance.**

## 1. Phase 0
Read KNOWN_FINDINGS.md / OPEN_ISSUES.md / CLOSED_ISSUES.md (known-stale per Tighe; recorded facts used
as priors, current state from AGENTS_LOG + September design docs). Relevant priors: KF-043 (player
sprite palette bank 51 → CRAM line 3), KF-044 (player PC090OJ composer source blocks). Classification:
**EXTENDING** (repairs offline sprite-asset coverage; no palette re-authoring). No CONFIRMED/STRONG
finding contradicted. KNOWN_FINDINGS impact: **Option A — no new finding to index.**

## 2. Build-0379 user rejection
Tighe's gameplay verification of Build 0379: **REJECTED** — frame-dependent Rastan palette failure
(some frames correct, others wrong; the Palette Composer mapping is shared across all frames). This
pointed at incomplete OFFLINE sprite-cell reindex coverage, not a palette edit.

## 3. Old 29-code limitation (confirmed root cause)
`gen_reindexed_pc090oj.py` derived the Rastan code set from the pre-H24 representative corpus
`codes("RASTAN", ["rastan_player_body","player_auxiliary"])` = **29 unique codes**. Build 0379 changed
the map KEY to `object:player.rastan` but the CODE SET was still the old 29-code corpus, so only ~29 of
the ~344 player cells were reindexed; every other player cell rendered with **raw** pixel indices →
wrong colors on the frames that use those cells (frame-dependent failure).

## 4. Complete H24 cell census
From the authoritative generated TSVs (torso `0x5BD40`, legs `0x5C466`):
- torso cell codes: **183**; leg cell codes: **162**; **all player cell codes: 345**.
- Control-nibble decode (offset-bounded) across all player pieces: **419 pieces nibble 3** (the shared
  player-body palette) + **1 piece nibble 12** (cell `0x140C`). The earlier "8-piece nibble-0/8 tail"
  was overread padding (the tile-0x0003 artifact class), fixed by offset-bounding.
- `0x140C` is **out of the PC090OJ tile range** (4096 tiles, max 0xFFF) — a decode artefact, excluded.
- **Player-body reindex set = 344 valid nibble-3 cells** (range 0x076–0x610).

## 5/6. Old generator coverage + missing-code proof
`H24 valid player cells (344) − generated Rastan codes (29) = 321 missing.` That 321-cell gap is the
root cause. **Player/enemy code conflicts: 0** — no source code is shared between the player and an
enemy under different maps, so a flat code-indexed transformed asset is sufficient; **no `(code,bank)`
split required** (STEP 6 conflict test negative). The simpler path is retained with proof.

## 7. Palette-nibble exceptions
All 344 player-body cells carry control nibble 3 (the `object:player.rastan` palette identity), so all
are validly reindexed under the shared player map. The single nibble-12 piece (`0x140C`) is an invalid
code / effect artefact and is not a player-body cell — excluded, not force-mapped. No arbitrary or
screenshot-derived mapping.

## 8. Corrected generator source-of-truth
`tools/graphics_editor/gen_reindexed_pc090oj.py` now builds the Rastan code set via `_h24_player_cells()`,
which reads **`h24_player_frame_cells.tsv` + `h24_player_leg_cells.tsv`** (the same authoritative H24
evidence the Palette Composer consumes) and keeps only valid PC090OJ codes. **No hard-coded player code
list; no second manually-maintained corpus.** The map remains the shared `object:player.rastan` (0379
fix). Cell model preserved: **one code = 128 bytes = four 8×8 subtiles**, source `code*128`, index 0
transparent, full-cell transform (STEP 4; Build-0327 correction retained).

## 9. Code-vs-(code,bank)
No conflict exists across the complete Rastan corpus (0 player/enemy overlaps), so the flat
code-indexed asset is correct and retained. No runtime pixel transformation introduced.

## 10. Independent verifier
`tools/graphics_editor/verify_reindexed_pc090oj.py` (extended with a Rastan-only breakdown) reuses
`build_code_usage` (so it inherits the complete H24 code set) and independently recomputes each
transformed 128-byte cell from **raw pc090oj + the frozen Build-0379 map**, asserting
`editor[code*128:+128] == transform(raw[...], map)`.

## 11. Before/after coverage
| | Build 0379 | Build 0380 |
|---|---|---|
| Rastan codes reindexed | 29 | **344** |
| Missing player cells | 321 | **0** |
| Total codes reindexed | 128 | 443 |

Verifier on the built asset: **PASS** — authored 443, mismatch 0, incomplete 0, non-identity-raw 0,
stray 0; **Rastan: 344 codes, 342 transformed (2 identity), mismatch 0, incomplete 0, non-identity-raw
0**. Torso coverage 75/75 · leg source slots 52/52 · valid full-body pairings 60/60.

## 12. Representative pose-class static proofs (previously wrong → now covered)
| pose class | H24 slot | source cells | in manifest | transformed |
|---|---|---|---|---|
| up-thrust | torso 12 | 0x1c0;0x1c1;0x1c2 | YES | YES |
| squat/crouch | torso 6 | 0x0ac;0x0ad | YES | YES |
| standing torso | torso 0 | 0x08e;0x08f;0x090 | YES | YES |
| weapon-swing | torso 44 | 0x08e;0x08f;0x090 | YES | YES |
| death dissolve | torso 40 | 0x4f9;0x4fa;0x4fb;0x4fc | YES | YES |
| standing lower-body | legs 0 | 0x076;0x077;0x078;0x079 | YES | YES |
| walk legs | legs 18 | 0x4a5;0x4a6;0x4a7 | YES | YES |

## 13. Complete Build-0380 variant matrix
| Variant | Path | Size | SHA-256 | Status |
|---|---|---|---|---|
| base | dist/rastan-direct/rastan_direct_video_test_build_0380.bin | 1724088 | beeceaa7daacfb4ca4f8d3a755b498759a99944169989863b87261ca345bbde0 | built |
| _c | …_0380_c.bin | 1724088 | f8fedc47f96fe27241ac4ea33a017fcc612f2659a85d0a70ebeadc9298019529 | built |
| _d | …_0380_d.bin | 1724088 | 8ddc4f89b51d61a17798fae063343952c8047bc27869617c5055780c70458cfa | built |
| _do | …_0380_do.bin | 1724088 | 308ef06e2ffc0d2401a9771701f932ea9a7b42893ac9940521136684ff1173b9 | built |
| _s | …_0380_s.bin | 1724088 | 32be3b650fcfeabef7f79b56501ea6473d1ac43f8c15cdb41e70d1ee0be14db4 | built |

Complete 5-variant family produced; `verify-variant-set` PASS; canonical gate PASS; boot guard PASS.
Counter 379 → **380**.

## 14. 0379 → 0380 diff
Total ROM diff: **16 264 bytes** (240→ up from 0379). Classification:
- **build/header/checksum:** 2 bytes at 0x18e.
- **offline sprite-pattern reindex (pc090oj_editor):** 16 262 bytes, range 0x084b1f–0x1a48dc (the 315
  additional player cells now reindexed).
- **palette CRAM:** UNCHANGED — the entire region below the sprite data (all code + `palette_hooks`
  CRAM override values) is **byte-identical** except the 2-byte header. **Build 0379 CRAM == Build 0380
  CRAM: YES.**
- **maincpu code / player-state / animation / movement / collision / rope / third-chain / Layer-A /
  Layer-B:** ZERO. **Other unrelated changes: ZERO.**

## 15. Architecture compliance
CONFIRMED. Offline authoring → generated asset → existing native path. No Genesis game loop / frame
authority / boot re-entry; **no runtime recoloring; no runtime pixel/nibble transformation; no PC090OJ
device or object-RAM mirror; no scaffolding.** Semantic cut retained; PC090OJ-specific tail remains
retired; transitional compatibility added: NONE.

## Files changed
- `tools/graphics_editor/gen_reindexed_pc090oj.py` — Rastan code set from the H24 TSVs (`_h24_player_cells`).
- `tools/graphics_editor/verify_reindexed_pc090oj.py` — Rastan-only coverage breakdown.
- Generated: `build/regions/pc090oj_editor.bin` + manifest, the numbered ROM family + ledger/counter.
- (Palette policy, snapshot, Makefile snapshot path: **unchanged** from Build 0379.)

## 16. USER MUST VERIFY
**Tighe performs ALL gameplay/visual verification.** Load the gameplay-test variant of Build 0380 and
re-check the Rastan poses that were wrong in Build 0379 (up-thrust, down-thrust, squat, standing
lower-body, walk, attack, death) against the saved `Test` Palette Composer target. Andy makes no
gameplay/visual acceptance claim.

## 17. Open/Closed Issues Impact
Open issues touched: OPEN-006 (sprite/high-bank palette mapping) — Build 0380 candidate; not closed.
New issues opened: none. Issues closed: none. Deferred: none.

## 18. KNOWN_FINDINGS impact
Option A — No new finding to index (EXTENDING; offline sprite-coverage repair; no new durable system
behavior discovered).
