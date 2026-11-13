# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0119 — R2 Layer-B palette completion

**Author:** Andy · **Date:** 2026-11-11 · **Baseline:** working tree continued from PROMT-ID-0115/0118 (HEAD
`f8b07a84`, uncommitted). Completes the statically-justified Plane-B→L2 and authored-0/1/3 ownership work and
produces a candidate for Tighe's gameplay testing. No runtime acceptance was possible here (MAME wedges).

## Architecture enforced (no round-number rules, no static palette)

    every gameplay Plane-B tile  -> Genesis CRAM Line 2   (semantic owner, all rounds)
    authored gameplay scene      -> owns Genesis Lines 0/1/3 (Test 2.0)
    retained arcade Layer-B code -> owns Genesis Line 2 (live, per round/scene)

No `record>=23` palette-line rule. No hardcoded R2 CRAM. No static copy from `$5DC4E`. `$5DC4E` is candidate
original-ROM oracle data only and does not appear in Genesis production code.

## 1. Complete Plane-B producer inventory (every `genesistan_pc080sn_attr_lut` consumer)

| Site (tilemap_hooks.s) | Enclosing hook | Semantic owner | Action |
|---|---|---|---|
| `.Lplane_b_native_attr_from_word` | streamed row/column helper | **gameplay Plane B** | force line=2 |
| `.Lbg_hook_desc_loop` (scene preamble) | `...plane_a..._native` BG preamble (writes `staged_bg`, `fg_boundary_resolve_b`) | **gameplay Plane B** | force line=2 |
| `genesistan_hook_tilemap_bg_fill` | BG fill (`staged_bg`) | **gameplay Plane B** | force line=2 |
| `genesistan_hook_tilemap_bg_blockcopy` | BG blockcopy (`staged_bg`) | **gameplay Plane B** | force line=2 |
| `genesistan_hook_tilemap_fg` | FG (`staged_fg`) | Plane A | untouched |
| `genesistan_hook_tilemap_fg_fill` | FG fill (`staged_fg`) | Plane A | untouched |
| `genesistan_hook_text_writer_3c4d2/3c950/3c550/3c586/3c636/3c6dc/3c75c/3c7a4/3c830` | text | text/frontend | untouched |
| `genesistan_hook_number_renderer_3c2e2`, `genesistan_hook_glyph_renderer_3bd48` | number/glyph | HUD/text | untouched |
| `genesistan_hook_cwindow_clear` | C-window clear (blank tile 0x20, LUT index 0 = line 0) | clear, not gameplay content | untouched |
| `genesistan_endround_plane_a_clear` | Plane-A clear (`staged_fg`) | Plane A | untouched |

Generator path: `compile_pc080sn_genesis.py` scene-fill Plane-B map — semantic (slot-based) line=2.

**Four** gameplay Plane-B producers were corrected; all share the semantic rule "a real Plane-B tile emits
Line 2 regardless of the arcade PC080SN `attr&3` bank select; flip/priority preserved." The shared attr LUT was
NOT globally rewritten (it is shared with Plane A/text/HUD); normalization is done at the Plane-B producer
boundary.

## 2. Producers corrected (exact)

Generator (`tools/translation/compile_pc080sn_genesis.py`), scene-fill:
`plane_b_line = PLANE_B_PALETTE_LINE if slot else (attr & 0x0003)` — real tiles -> Line 2; blank cells keep
their bits so R1 stays byte-identical. Mirrored in `verify_plane_a_scene_fill_maps.py`.

Runtime (`apps/rastan-direct/src/tilemap_hooks.s`): the four gameplay Plane-B producers above replace
`pal = attr&3` with `pal = 2` before the attr-LUT lookup (flip/priority bits still OR'd in).

## 3. R1 non-regression evidence

- Generated `plane_b_scene_fill_maps.bin`: **R1 records 0-22 byte-identical** to the 0560 baseline (0 records
  changed); only R2 records move to Line 2. Proven by direct byte comparison.
- Runtime producers: R1 background tiles carry `attr&3==2`, so forcing `pal=2` is a no-op for R1 (the attr-LUT
  index is unchanged). R1 therefore emits identical Plane-B name words.
- Gate repair (below) removes only the `stage<23` round term; R1 (`scene_id==1`, `stage<23`) already took the
  only-Line-2 / skip path, so its runtime palette behaviour is unchanged.

## 4. Authored Lines 0/1/3 ownership repair (sprite-colour timing)

The three retained arcade palette producers gated the authored-line protection on
`scene_id==1 AND stage<23`. The `stage<23` term was an R1-only artifact. Removed it in all three, so authored
`scene_id==1` scenes protect Lines 0/1/3 for **every** round (semantic ownership, not a round number):
- `genesistan_palette_hook_59ad4`: `scene_id==1` -> only Line 2 may be staged.
- `genesistan_palette_hook_3ba64`: `scene_id==1` -> only bank-48/Line-2 may be staged.
- `genesistan_palette_hook_45dae`: `scene_id==1` -> skip the bank-0 copy into Lines 0..3.

This is the static repair for the reported sprite-colour defect: at initial R2-S1 entry the authored
Lines 0/1/3 (Test 2.0, assets 4/5/6) will no longer be overwritten by the retained arcade producer, so mapped
sprites should be correct immediately rather than after a reseed. R1 (`scene_id==1`, `stage<23`) is unchanged;
non-authored / frontend scenes (`scene_id!=1`) keep full arcade staging.

## 5. Sprite-palette timing — static call-path proof (and the runtime-only gap)

- Initial R2 entry: the scene loader sets `genesistan_current_scene_id` (scene_load.s) and the authored install
  (`vdp_install_test_lines`) stages Lines 0/1/3 from `diagnostic_palette_scene_select[A5+0x1242]` (asset 4 for
  R2-S1). The retained arcade producers then run per-frame; before this repair they overwrote 0/1/3 for R2.
- Restore events: `vdp_refresh_test_lines_if_scene_changed` reinstalls the authored lines when the selected
  asset changes; the epoch reseed at the 32->33 boundary and the respawn/reseed both re-enter the scene/asset
  path. Any of these reinstalls the authored palette — consistent with Tighe's "corrects after record ~33 or
  after respawn ~29."
- **Runtime-unproven:** the exact record at which the colours flip from wrong to correct cannot be proven
  statically; it requires working MAME (not available here). The repair removes the overwrite so no later
  correction event should be needed — that itself is the Tighe acceptance test (dying ~29 / crossing 32->33 must
  no longer repair colours). Not claimed fixed until Tighe verifies.

## 6. Original R1 Layer-B palette chain (as established)

- Arcade per-round outdoor palette pointer table at arcade `0x59EC8` (6 entries, one per round), consumed by the
  gameplay scene loader (sub-loader passes the entry as A0 into `genesistan_palette_hook_59ad4` with D0=2).
- `genesistan_palette_hook_59ad4` (arcade `0x59AD4` body replacement): converts arcade 0RGB444 -> Genesis CRAM
  and writes the result to staged Line 2 (D0=2). This is the live Layer-B path (incl. dynamic sky updates).
- `genesistan_palette_hook_3ba64`: routes arcade palette-RAM **bank 48** -> Genesis Line 2.
- Publication: `staged_palette_words` (Line 2 = offset 64) + `palette_pending` -> unconditional VBlank CRAM DMA.
- The authored producers' Line-0/1/3 protection (section 4) keeps this Line-2 ownership intact while leaving
  Lines 0/1/3 to Test 2.0.

## 7. R2 palette-path facts (proven vs runtime-only)

- Proven static: R2 background tiles carry `attr&3==3` (would land on Line 3 without the fix); the per-round
  table `0x59EC8[1]` (= `$5DC4E`) holds a brown/green outdoor palette consistent with the arcade R2 screenshot.
- Runtime-only (NOT proven here, needs MAME): whether the original arcade program selects `0x59EC8[1]` (R2) vs
  `[0]` (R1) into Line 2 at the first R2 frame — i.e. whether `A5+0x118` (round) is authoritative at that moment.
  If, after this repair, Line 2 still shows R1 colours at R2 entry, the remaining defect is the round index /
  per-round-palette selection timing, to be chased with runtime evidence. `$5DC4E` is NOT referenced by Genesis
  code.

## 8. Treatment of `$5DC4E`

Oracle only. Not hardcoded. Not copied. Not referenced by any Genesis production source. Used solely to confirm
(by colour) that the arcade per-round table entry for Round 2 is the brown/green forest palette.

## 9. Builds / gates / environment-blocked

- Candidate: **Build 0563** (see AGENTS_LOG for SHA-256s and ROM paths).
- Automated gates that ran: canonical ROM gate, boot guard, transition-retention, scene-fill/Plane-B verifiers,
  native metatile/HUD/item/title, VDP DMA boundary — all PASS (static).
- Environment-blocked (NOT RUN): the GENESIS NTSC MAME entry gate, the phase-1 epoch gate, and the post-number
  30s trace — MAME wedges at init in this sandbox; terminated cleanly. These are recorded NOT RUN /
  ENVIRONMENT-BLOCKED, not as gameplay pass/fail.

## 10. Required Tighe gameplay tests (authoritative)

First test natural R1->R2 if practical; also an R2-S1 direct-start ROM. Verify: initial R2 Layer A still
correct; the entire Plane B uses one consistent L2 realization (initial fill and newly-streamed match); L2 shows
R2 background colours, not R1; mapped sprites correct immediately at R2 entry; dying ~record 29 does NOT suddenly
repair colours; crossing 32->33 does NOT suddenly repair colours; later dynamic Layer-B palette changes still
occur. None of these are claimed fixed until Tighe verifies.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0119`
