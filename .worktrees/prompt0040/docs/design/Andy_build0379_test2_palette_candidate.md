# Andy — Build 0379: `Test` Palette Composer Candidate

**Agent:** Andy · Implementation / Build / Static verification. **Counter 378 → 379.**
**Andy performed NO gameplay verification — Tighe owns all gameplay/visual acceptance.**

## 1. Phase 0 baseline
Read KNOWN_FINDINGS.md, OPEN_ISSUES.md, CLOSED_ISSUES.md (all known-stale per Tighe; used only for
facts actually recorded). Current state established from AGENTS_LOG.md (newest) + September design docs
+ live `editor_policy`. Relevant priors: KF-043 (player sprite palette bank 51 → Genesis CRAM line 3),
KF-044 (player PC090OJ composer source blocks). Classification: **EXTENDING** (applies an authored
palette revision through the established offline pipeline). No CONFIRMED/STRONG finding contradicted.
KNOWN_FINDINGS impact: **Option A — no new finding to index.**

**Profile-name STOP → user-confirmed.** The prompt named profile `Test 2`; no such profile exists. The
only editable profile is `Test` (contains the corrected-UI shared Rastan mapping). Tighe confirmed
**build from `Test`**.

## 2. Build-0378 current baseline
Build 0378 consumed `build/rastan-direct/build0314/Test.snapshot.json` (Makefile default) — the prior
palette input. Full 0378 variant family present in `dist/rastan-direct/`.

## 3. Actual persisted `Test 2` source
`analysis/graphics_optimizer/editor_policy/Test.json` — `profile_id="Test"`, `display_name="Test"`,
parent `baseline_current`, rev 23, modified 2026-09-27T12:30:37Z, context `gameplay.r01.p01`, 8 local
overrides. Contains the H24 shared key `object:player.rastan`. **Not mutated by this build.**

## 4/5. Frozen snapshot
`build/rastan-direct/build0379/Test.snapshot.json` (byte-copy of `Test.json`), **SHA-256
`2c6630a0d1219ddcc43c585994bcf7d500dfa413818a8a72b281db10ceb14de9`**. Independent of later `Test`
edits; the actual build input (Makefile `EDITOR_LAYERA_SNAPSHOT` repointed to it).

## 6. Exact authored profile diff (`Test` vs Build-0378 input)
**A. Target CRAM (base lines):** `L0:0  None → 0x0888` (index 0; effective palette is driven by the
context overrides below).
**B. Source→target index-map changes:**
- **`object:player.rastan` — NEW** (line 0): full map `{1:7,2:8,3:9,4:10,5:2,6:11,7:6,8:12,9:1,10:13,
  11:14,12:0,13:4,14:15,15:3}`. (This differs from the legacy `rastan_f7722` map at src 7/12/13/15,
  and is now the authoritative Rastan mapping consumed by the build.)
- `large_bat` (line 0): src 11 `3→6`, src 14 `6→15`.
- `small_bat` (line 0): src 11 `3→7`, 12 `10→5`, 13 `11→15`, 14 `6→3`.
**C. Destination-line changes:** Rastan authored on **line 0** (shared sprite palette). No line moves
for the bats (stay line 0).
**D. Policy changes:** `object:player.rastan` mapping added; bat maps reassigned. No removals.
**E. Context local overrides (8, `context:gameplay.r01.p01`):**
`L0:2=0x0224 · L0:3=0x022C · L0:4=0x0888 · L0:6=0x0026 · L0:8=0x0EEE · L1:5=0x04C4 · L1:7=0x0442 ·
L1:12=0x0200`.

## 7. Shared-target impact (what Tighe should inspect)
All changed target entries are on shared sprite **lines 0 and 1**. Rastan's map consumes L0 entries
{0,1,2,3,4,6,7,8,9,10,11,12,13,14,15}; the bats and other line-0 sprites share those entries. So the
changed L0/L1 entries affect **Rastan and every other sprite mapped to line 0/1** (bats, and any
enemy/effect on the shared sprite lines). Line 2 (Layer B) untouched. Tighe should inspect Rastan plus
the other line-0/1 sprites (large_bat, small_bat, and any others) during his gameplay test.

## 8. Current line ownership (Build 0378/0379, from the profile + route model)
- **Line 0:** shared Test sprite palette (Rastan + bats + line-0 sprites) — Rastan destination line.
- **Line 1:** shared Test sprite palette.
- **Line 2:** Layer B / arcade-controlled (protected) — **not modified** (Test line 2 empty).
- **Line 3:** Test Layer-A palette.
Rastan effective route: authored map → line 0 shared sprite palette.

## 9. Rastan shared-mapping / H24 coverage
One shared map key `object:player.rastan` (verified: the build's `pc090oj_editor_manifest.json`
consumes `object:player.rastan`, `rastan_f7722` no longer referenced). The offline reindex applies that
single mapping to every RASTAN sprite code (`rastan_player_body` + `player_auxiliary` vocabularies) —
no per-frame policies, no three-frame legacy representation as authority. H24 static coverage (75 torso
/ 52 leg slots / 60 valid pairings; blank leg slot 34 handled) is preserved by the shared mapping.

## 10/11. Production compiler + complete variant matrix
Built via the Makefile-owned `make release` (dual-build → base + `_d`/`_s`/`_do`/`_c`, then
`verify-variant-set`). Counter 378 → **379**.

| Variant | Path | Size | SHA-256 | Status |
|---|---|---|---|---|
| base | dist/rastan-direct/rastan_direct_video_test_build_0379.bin | 1724088 | 9293c03ab9909b21a8b4a58df7c7670736845baeaf15fe997ea70cd0444175b5 | built |
| _c | …_0379_c.bin | 1724088 | 6de8b820d4c7c530d4fb6c72f35b720e51fbdd00e24eebdd8903d1ab3efdf4cf | built |
| _d | …_0379_d.bin | 1724088 | 42603c1dc9a09c54ea3a249c9d6b7ae1b82aa674ec324cb8046a5ad8ea89ee8d | built |
| _do | …_0379_do.bin | 1724088 | a72d1053afeea0f6d381170f79dbaa8fe5abfc40944f0d95cfe5d9345cdd4bb5 | built |
| _s | …_0379_s.bin | 1724088 | bc7fab73e97f968b2f77625b1e321bb153ffa13ff2975544fdc15287852450d9 | built |

Complete 5-variant family produced and `verify-variant-set` PASS.

## 12. Generated assets
Changed: `build/regions/pc090oj_editor.bin` (sprite reindex under the new maps), the generated palette
CRAM data, and the numbered ROM family + manifests. Provenance: `pc090oj_editor_manifest.json`
`profile_sha256 = 2c6630a0…` (matches the frozen snapshot). Runtime recoloring: **NO**. Runtime pixel
transform: **NO**. PC090OJ compatibility restored: **NO**. Offline sprite reindex: **YES**. Offline
Layer-A regeneration: run by the pipeline (Layer-A snapshot consumed); no LA index-map changes in the
Test diff.

## 13. Build 0378 → 0379 difference audit
Total ROM diff: **390 bytes** across 240 runs. Classification:
- **build/header/checksum:** 2 bytes at 0x18e (build number/header).
- **palette CRAM + offline sprite-pattern reindex:** 388 bytes, range 0x085559–0x1a48dc (entirely in
  the graphics-asset regions).
- **maincpu code:** ZERO (lowest change 0x085559 is past the ~0x60200 maincpu-code end).
- **other:** ZERO. No H24 player-state, third-chain, rope, collision, movement, or frame-selection
  logic changes. The Palette-Composer tooling changes altered ROM bytes only via the authored `Test`
  data consumed by the pipeline.

## 14. Non-gameplay verification / gates
- Canonical gate: **PASS** (ledger `0379 … canonical=PASS entry=PASS epoch=FAIL`; `epoch=FAIL` is the
  standing state across 0376–0378, unchanged by this build — not a regression).
- Boot guard (pre + post patch): **PASS** (SP=0x00FF0000, RESET=0x00000202, VINT=0x000700C2).
- `verify-variant-set`: **PASS** (all five variants present/non-empty).
- Generated provenance points to the frozen `Test` snapshot: **verified**.
- Layer B / line 2 mechanically unchanged: **verified** (no L2 diff).
- Andy ran **no** gameplay run and **no** new emulator run.

## 15. Architecture compliance
CONFIRMED. Offline authoring → generated asset → existing native path. No Genesis game loop / frame
authority / boot re-entry; no runtime recoloring/pixel transform; no PC090OJ device or object-RAM
mirror; no scaffolding.
- **Semantic cut:** retained (unchanged; offline authoring only).
- **PC090OJ-specific tail:** remains retired.
- **Transitional compatibility added:** NONE.

## Files changed
- `build/rastan-direct/build0379/Test.snapshot.json` (frozen input, new).
- `apps/rastan-direct/Makefile` — `EDITOR_LAYERA_SNAPSHOT` repointed to the 0379 snapshot.
- `tools/graphics_editor/gen_reindexed_pc090oj.py` — reads the authoritative shared `object:player.rastan`
  Rastan mapping (falls back to legacy only if absent) so the build consumes the corrected-UI edit.
- Generated: `build/regions/pc090oj_editor*.bin`/manifests, the numbered ROM family + build ledger/counter.

## Open/Closed Issues Impact
- Open issues touched: OPEN-006 (sprite/high-bank palette mapping) — a Test candidate for it; not
  closed. New issues opened: none. Issues closed: none. Deferred: none.

## KNOWN_FINDINGS impact
Option A — No new finding to index (EXTENDING; authored palette revision through the established
pipeline; no new durable system behavior discovered).

## USER MUST VERIFY
**Tighe performs ALL gameplay/visual verification.** Load the normal gameplay-test variant of Build
0379 and compare Rastan in Round 1 / Phase 1 against the saved `Test` Palette Composer target, and
inspect the other line-0/1 sprites (large_bat, small_bat, and any others sharing the changed entries).
Andy makes no gameplay/visual acceptance claim.
