# R2 Native Plane-A Port — feasibility proof + implementation plan

**Andy, 2026-11-09.** Tighe wants Round 2 to use the Palette Composer's **Test 2.0** Plane-A mappings instead of
the retained arcade conversion (now that R2 Layer-A is authored). Production already builds from Test 2.0
(PROMT-ID-0112, Build 0560), but the **native Plane-A subsystem is R1-only**; R2 falls back to arcade streaming.
This note proves the port is feasible and lists the exact work. **Not yet implemented** — it needs iterative MAME
verification, which the current sandbox cannot provide (MAME wedges at init).

## Feasibility (proven)

The earlier "683 > 676 cap" blocker is **not** a real limit — it was R2's lazy 2-epoch default table
(`compile_pc080sn_genesis.py BOUNDARY_ROUND2_EPOCH_RECORDS = (range(23,34), range(34,46))`) vs R1's six
hand-tuned per-segment epochs (`BOUNDARY_ROUND1_EPOCH_RECORDS`). Like R1-S1 (which loads/unloads per segment),
R2 just needs finer epochs. Arcade stage index `a5@0x1242 = (round-1)*23 + 16*castle + 22*boss` (RG-019), so R2
owns records 23–45 (outdoor 23–38, castle 39–44, boss 45).

Per-record raw Plane-A tile counts (R2-S1 outdoor, from its `plane_a_uses.json`): rec23=488, 25=413, 26=417,
33=463 are the foliage-dense screens; total R2-S1 unique = **713**, but only **712 are exact-unique pixels**
(1 exact dup) and ~**37 near-duplicates** (≤16-bit diff) — so dedup/consolidation (the R1-S1 waterfall trick)
reclaims little; **per-segment loading is the real lever.** A proven 3-epoch R2 split fits under 676 (raw, with
synthetic-variant margin): **records 23–32 (587), 33–38 (597), 39–45 (328).**

## Implementation plan

### A. Generator (`tools/translation/compile_pc080sn_genesis.py`) — offline-verifiable
1. Add R2 scenes to `AuthoredLayerA.SCENES`: `("PAL-R2-S1-PLANEA-OUTDOOR", range(23,39), …/plane_a_uses.json)`,
   `("PAL-R2-S2-PLANEA-CASTLE", range(39,45), …)`, `("PAL-R2-S3-PLANEA-BOSS", range(45,46), …)`. (Test 2.0 has
   the matching `context_policies` plane_usage_palette_mappings: 789/234/200 entries.)
2. Set `BOUNDARY_ROUND2_EPOCH_RECORDS = (range(23,33), range(33,39), range(39,46))` (iterate exact split so each
   epoch's SYNTHETIC union ≤ 676 — raw +~8%).
3. Update hardcoded validations keyed to the R1-only 8-epoch shape: `expected_epoch_counts` (currently
   `[283,334,640,584,640,542,630,544]`), and any `minimum_by_round`/transition-count asserts. Each added R2
   epoch adds a residency + possibly a streamed transition.
4. Confirm R1 output byte-identical (R1 scene_select 0–22, R1 patterns) and R2 scene_select now maps stages
   23–45 → assets 4/5/6.

### B. Palette install (`vdp_comm.s vdp_install_test_lines`, `palette_hooks.s`)
- `.incbin` the three R2 blobs (`PAL-R2-S*-PLANEA-*.bin`, 96 bytes = Lines 0/1/3; R2 Line 0 already == the
  player palette) as `diagnostic_palette_r2s1/2/3`; extend `diagnostic_palette_asset_ptrs` 3→6.
- Extend the `diagnostic_palette_active_visual_index` logic (currently handles assets 1/2/3) for 4/5/6 → the R2
  authored FG descriptors.

### C. Native FG residency (the bulk — `scene_load.s`, `tilemap_hooks.s`, generated preloads)
- Generate R2 `scene_preload_stage2_*` residencies (one per R2 epoch) and R2 FG pattern region; wire R2 tileset
  ids into `load_scene_tiles` selection (currently ids 1–9, all R1) keyed by round (`0x1242 ≥ 23`).
- `tilemap_hooks.s`: extend authored-descriptor FG rendering + `FG_AUTHORED_DESC_*` ranges to the R2 descriptors.
- Residency transitions between the 3 R2 epochs (R1 has proven streamed transitions at record 2→3, 3→4).

### D. Runtime gate lifts (strictly R2-additive; keep R1 byte-identical)
- `scene_load.s:215` `cmpi.w #23,0x1242(%a5)` → cover R2 (e.g. `#46`) so R2 calls `vdp_install_test_lines`.
- `palette_hooks.s` round gates (lines ~195/215/355/466) and `fg_tile_cache.s` (~278/286): extend `#23`→`#46`
  so the arcade palette hook protects the installed R2 Lines 0/1/3 (only Line 2 = Plane-B stays arcade).

### E. Verify
- Offline: R1 player tiles still 27/27 vs 0554; R1 scene data byte-identical; R2 native data present.
- **MAME (required, not available in this sandbox):** R2-S1/S2/S3 direct ROMs show Test 2.0 R2 Plane-A colors;
  R1 unaffected; no VRAM overrun / plane drops.

## Recommendation

Do this in a working-MAME environment (Cody's), because C/D need visual iteration and can't be verified offline.
Start with the **smallest R2 scene first** (R2-S3 boss, 200 uses, or R2-S2 castle, 234) to validate the full
native path end-to-end before R2-S1's tight 3-epoch outdoor. Keep every change R2-gated so R1 (Build 0560,
Tighe-accepted) stays byte-identical. Related: [[project_production_palette_profile]],
[[project_per_round_plane_a_palette]], [[project_scene_background_bank_map]].
