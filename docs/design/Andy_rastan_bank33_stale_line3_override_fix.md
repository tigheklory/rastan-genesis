# Build 0333 — Rastan Bank-0x33 Stale Line-3 Override Removal

**Type:** Verification / Implementation. ROM produced (Build 0333). Classification: **EXTENDING**. Baseline Build 0332.
**Result:** Stale `bank 0x33 → Line 3` resolver override removed; bank 0x33 now routes through the authored policy to **Line 0**.

## 1. Phase 0
- **Relevant findings/priors:** Build-0325 Test architecture moved PC090OJ bank 0x33 (Rastan) to Line 0 (route table + offline reindex); `.Lnative_palsel` retained a pre-Test (Build-0210) hardcoded override. KF/route authority: `palette_route_lookup` + `palette_route_table`.
- **Deferred (untouched):** bank-0x30 items + death-burst first-class Palette Composer work; HUD `1UP`/score + Axe; Rastan/bat wider `(code,bank)`; vertical-noise.
- **Classification:** EXTENDING. **OPEN/CLOSED impact:** improves OPEN-006 (Rastan palette); none closed/opened. **Contradiction status:** none — this removes a stale override that contradicted the current route table; no CONFIRMED/STRONG finding contradicted.

## 2. Stale override proof
`.Lnative_palsel` (pc090oj_hooks.s) contained, before the general `palette_route_lookup` path:
```
cmpi.w  #0x0033, %d0
bne.s   .Lnp_general
moveq   #3, %d0        ; bank 0x33 -> Line 3 (pre-Test Build-0210 override)
bra.s   .Lnp_done
```
This short-circuited the route table, forcing Rastan's effective bank 0x33 onto Genesis **Line 3** (the Layer-A master palette), so his Line-0-authored pixels displayed against the wrong CRAM line.

## 3. Route-table proof
`palette_route_table` (palette_hooks.s): `.word 1, PROUTE_OWNER_PC090OJ, 0x33, 0, 0` → scene 1, PC090OJ, bank 0x33 → **Line 0**. The current authored policy is Line 0.

## 4. Transformed-asset proof
`build/regions/pc090oj_editor_manifest.json`: **29** bank-0x33 codes, **all** with target `line = 0`. Rastan's offline sprite reindex was generated for the Line-0 representation. So routing bank 0x33 to Line 0 matches the reindexed pixels; assets are unchanged.

## 5. Implementation
Removed the four-line `bank 0x33 → Line 3` block and redirected the preceding bank-0x30 test from `bne.s .Lnp_not48` to `bne.s .Lnp_general`. Result:
```
cmpi.w  #0x0030, %d0
bne.s   .Lnp_general      ; bank 0x30 -> Line 2 preserved
moveq   #2, %d0
bra.s   .Lnp_done
.Lnp_general:             ; bank 0x33 now falls through here -> palette_route_lookup -> Line 0
```
**No new hardcoded `bank 0x33 → Line 0` special case was added** — the route table is the sole authority. Bank 0x30 → Line 2 (death burst / effects) is intentionally preserved. Nothing else changed (no palette staging, no assets, no ownership, no Line-2 behavior).

## 6. Automated verification
ROM `dist/rastan-direct/rastan_direct_video_test_build_0333.bin`, SHA256 `294e764baa7adbc7a85dacf4afebb1d8535b0ac437515e7f7c711db8835abdff`. GATE_PASS (canonical); seven-epoch PASS (records 0,3,4,10,11,12,15); Plane-A full LUT PASS; Plane-B fixed LUT PASS; plane drops 0; exceptions 0 (address/bus 0); MAME Genesis-NTSC 30s clean; HUD default `RASTAN_GAMEPLAY_HUD_SPRITES ?= 2`. Runtime (states/traces/build0331_line2/b0333): Line-2 sunset progression byte-identical to Build 0332/0328 (load f387, sunset f1577); Lines 0/1/3 static Test (`l013=0xC480`); no per-frame palette reassert. Bank 0x33 now reaches `palette_route_lookup` (override deleted) → route result Line 0 (route table + manifest proven).

## 7. USER MUST VERIFY
Rastan now uses the intended Line-0 colors; Rastan animation/body pieces complete; Layer A still correct; Layer B / sunset still correct; item colors expected to remain unresolved; enemy death burst expected to remain unresolved; bats/other incomplete sprite colors deferred; Build-0328 duplicate-sprite fix intact.

## 8. Deferred bank-0x30 work
Enemy-drop items (gems, potions, mantle, armor, shield, gold sheep, ring, rod, necklace) and the enemy-death fireball/burst are bank-0x30 representations not authored in the Test reindex. Future work: arcade ROM/data + static decoder evidence → first-class Palette Composer representation → Tighe-authored target policy → offline `(code,bank)` reindex → O(1) native routing. Arcade screenshots are validation/reference only, never a color-sampling source. HUD `1UP`/score and Axe first-class representations also preserved.
