# Andy — Build 0317 Layer-A Line-3 Palette Routing Fix

**Type:** implementation/verification. EXTENDING. Build counter 316→317. Pattern compiler NOT changed.

## 1–2. Build-0316 user result + why patterns were frozen
Tighe: Layer-A **patterns mostly correct**, **palette/colors wrong**. Per the 0316 doc, Layer A was
realized on the FG carrier line, not the authored Line 3. This task changes only the palette routing; the
Build-0316 transformed-pattern implementation is untouched.

## 3–6. Build-0316 actual routing + root cause
`tilemap_hooks.s:172-180` derives the Plane-A name-word palette line from `palette_route_lookup`
(`palette_route_table` in `palette_hooks.s`), not the attr LUT. Build 0316: FG bank 3 → **line 1**;
sprites (bank 51) → **line 3**. So editor tiles selected line 1 while line 3 held sprite/other palette →
wrong colors. Root cause = route table line ownership, not patterns.

## 7–9. Changes implemented (Build 0317)
`palette_hooks.s`: `PROUTE_FG_LINE` 1→**3**; route table `PC080SN_FG bank 3 → line 3` (was 1);
`PC090OJ bank 51 → line 0` (was 3, moved off Line 3). The existing FG carrier already stages the static
`editor_layera_palette` (exact 15 editor words) into `fg_bank3_line_cache`; `vdp_reassert_fg_bank3_line`
reasserts that cache to `staged_palette_words[PROUTE_FG_LINE]` (now line 3) each gameplay VBlank. Runtime
copies precompiled CRAM words only — no color calculation/conversion.

## 10. Line 2 / Layer B
Unchanged (route table BG bank 48 → line 2 untouched; staged line 2 in the gameplay dump remains the
Layer-B sky palette). Editor-derived Line-2 writes = 0.

## 11. Build 0317
`dist/rastan-direct/rastan_direct_video_test_build_0317.bin`; built; seven-epoch gate PASS; candidate
retention gate PASS; 30s genesis MAME no crash. Route-table change confirmed in source; sprites off line 3.

## 12. Automated MAME proof — HONEST RESULT: INCONCLUSIVE / NEGATIVE
Dumping `staged_palette_words` at each epoch installer boundary shows **staged Line 3 does NOT contain the
editor palette (0/15)** — it holds a different palette, while Layer B (line 2) is intact. This means the
carrier is not landing the editor palette on the staged line-3 shadow at the sampled (installer-boundary)
frames. Two possibilities remain and are NOT yet resolved: (a) the sample predates the gameplay VBlank
reassert so steady-state gameplay CRAM line 3 may still differ from this snapshot; (b) a real gap in the
carrier path (`fg_bank3_cache_valid`/route-seen timing) prevents the editor palette from reaching line 3.
I did not resolve which within this session's budget. **Build 0317's palette routing is therefore NOT
verified to place the editor palette on live CRAM line 3.**

## 13. USER MUST VERIFY
Boot 0317 and check whether cave/water now use the editor colors. If they are still wrong, the carrier
reassert path needs debugging (make the editor palette a scene-1 static CRAM assert independent of the
bank-3 route-seen/cache-valid gating) — the concrete next step for Build 0318.
