# Cody - Build 0120 Title Pommel Composite-Artifact Attribution

**Date:** 2026-06-30
**Type:** Runtime evidence / visual attribution only
**Build:** 0120
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0120.bin`
**ROM SHA256:** `80404f3a5b158f003692a20e84fe23ab05351f0639ac6bcd7d7594b93a0146ad`
**Scope:** Evidence and attribution only. No source/spec/tool/Makefile/ROM/build/invariant changes. No implementation. No fix design. No diagnostic ROM. No bookmark. No memory seeding or state forcing.

Address labels: `runtime_genesis_pc` = Genesis runtime/file-offset code address, `genesis_rom_offset` = ROM file offset, `Genesis-WRAM` = Genesis work RAM, `HW_ADDRESS` = hardware-visible address, `VRAM address` = VDP VRAM address. Arcade-to-Genesis code comparisons must use `build/rastan-direct/address_map.json`; this task did not use arithmetic address conversion as proof.

## Phase 0

Relevant priors:

- KF-010 - applies because BG maps to Genesis Plane B, FG maps to Genesis Plane A, and PC090OJ sprites map to Genesis SAT. This is the layer-separation basis for attribution.
- KF-016 - applies because title-state sprite-RAM clear behavior is prior context for interpreting title sprite/SAT residue.
- KF-021 - applies because sprite output can be masked or misleading when SAT DMA / renderer behavior is incomplete.
- KF-026 - applies because PC090OJ runtime write surfaces are not fully statically enumerable, so sprite/SAT cannot be globally dismissed from static searches alone.
- KF-032 - applies because raw copied arcade hardware writes must route through staging, and raw PC080SN/PC090OJ paths remain relevant to visible corruption.
- KF-036 - applies only as guardrail if mapped arcade work-RAM helper bases appear; no new RAM-base analysis was performed here.
- KF-038 - applies as a negative/context prior: item-description BG row aliasing is not the same title pommel composite artifact.

Rediscovery Hazard HIGH findings touched:

- KF-021 - HIGH; sprite/SAT output evidence can be masked.
- KF-032 - HIGH; raw copied hardware writes can be MAME-tolerant and strict-emulator fatal.
- KF-036 - HIGH; address/data mapping must not be guessed.
- KF-038 - HIGH; do not reclassify title artifact as the item-description row-alias mechanism without evidence.

Deferred-appendix entries relevant: no deferred entry is used as a prior. The older emulator-divergence caution remains relevant background only.

Task classification: **EXTENDING** OPEN-001, with OPEN-023 and OPEN-024 as the live attribution contexts. OPEN-006, OPEN-015, and OPEN-021 are context only.

Contradiction detected: **NO**.

## Evidence Inspected

Screenshots inspected:

- `states/screenshots/build_120/Exodus_build_120_title_screen_window_boundaries_on.png`
- `states/screenshots/build_120/Exodus_build_120_story_screen_window_boundaries_off.png`

Task-local visual evidence crops created:

- `states/traces/build_0120_title_pommel_composite_attribution_20260630_visual/title_plane_a_pane.png`
- `states/traces/build_0120_title_pommel_composite_attribution_20260630_visual/title_plane_b_pane.png`
- `states/traces/build_0120_title_pommel_composite_attribution_20260630_visual/title_window_pane.png`
- `states/traces/build_0120_title_pommel_composite_attribution_20260630_visual/title_sprite_pane.png`
- `states/traces/build_0120_title_pommel_composite_attribution_20260630_visual/title_plane_b_pommel_clean_crop.png`
- `states/traces/build_0120_title_pommel_composite_attribution_20260630_visual/title_plane_b_pommel_region_marked.png`

No separate annotated red/green screenshot file was present in the attachment directory for this prompt or under `states/screenshots/build_120/`. The user-provided annotation is therefore treated as a described observation, while the local Exodus screenshot is used for direct layer-view inspection.

## Visual Anchor

Artifact region, from the user description and local Plane B viewer alignment:

- Approx final-composite region: screen-space estimate `x ~= 150..185`, `y ~= 20..70` in a 320x224 Genesis-like display.
- Approx tile range: columns `18..23`, rows `2..8`.
- Relationship: top of the RASTAN sword hilt / pommel area, where the vertical sword meets the top ornament/handle region.
- Visual class: described as a final-composite obscuring/glitch/stripe at the pommel. Based on the Window viewer pattern, the best visual class is **horizontal/striped overlay or overwritten pixels**, not Plane B tile corruption.
- Uncertainty: exact final-composite pixel coordinates cannot be read because the annotated final-composite screenshot is not present locally. The coordinate range is a bounded estimate derived from the title Plane B pane and the user's described red/green annotation.

Corresponding Layer B area:

- The title Plane B viewer shows the RASTAN logo and sword art cleanly.
- The task-local `title_plane_b_pommel_region_marked.png` marks the inspected region.
- The task-local `title_plane_b_pommel_clean_crop.png` shows coherent sword/pommel pixels in Plane B.

Plane B exoneration: **YES for the direct source**, within the inspected evidence. Plane B may still be part of the final composite background, but the local Layer B viewer does not show corruption at the pommel.

## Layer Attribution

### Plane B

Evidence:

- Plane B title viewer shows coherent RASTAN/sword art.
- The pommel/hilt crop is visually clean.

Attribution: **not supported** as the direct artifact source.

Residual uncertainty: no synchronized final-composite VRAM Plane B dump was captured, but the available Exodus layer viewer is enough to avoid re-litigating Plane B unless contradictory runtime evidence appears.

### Plane A

Evidence:

- Title Plane A viewer shows TAITO/copyright/credit text near the lower title area.
- Plane A does not visibly contain sword/pommel-region cells in the top title-art region.
- No local evidence shows Plane A nonblank cells overlapping the pommel region.

Attribution: **not supported / weak**.

Residual uncertainty: no synchronized Plane A nametable-cell dump at the exact artifact coordinates was captured.

### Sprites / SAT

Evidence:

- Title Sprite viewer shows one small outlined sprite-like box.
- The visible box appears left of center and lower than the top-pommel region in the extracted Sprite pane, not obviously overlapping the top sword hilt.
- Prior Build 0120 evidence shows sprite infrastructure is partial, SAT data can persist, and `vdp_commit_sprites` does not sweep all unused SAT state every VBlank.

Attribution for this specific pommel artifact: **possible but not supported by the available visual coordinates**.

Why not fully excluded:

- No title-frame SAT VRAM dump was captured.
- No decoded active SAT entry list was captured at the exact final-composite frame.
- PC090OJ remains incomplete under OPEN-024.

Current interpretation: Sprite/SAT is a live subsystem gap, but the single visible Sprite-pane box is not the best visual match for a horizontal pommel stripe.

### Window

Evidence:

- Title Window viewer shows strong patterned garbage: vertical bands and horizontal striped rows.
- Prior Build 0120 inventory records Window base as `VRAM address 0xF000`, with the configured footprint overlapping SAT `0xF800..0xFA7F` and H-scroll storage around `0xFC00`.
- No `staged_window_buffer`, `window_dirty`, `vdp_commit_window`, Window clear, or game producer route was found.
- No post-boot source writes to Window X/Y registers were found in the prior audit.
- The visual shape in the Window viewer is a better match for horizontal/stripe-like contamination than the single Sprite-pane box or Plane A text.

Attribution: **LIKELY Window visibility / Window VRAM overlap artifact**.

Important limitation: this is not yet fix-ready proof. The missing decisive evidence is a synchronized title-frame VDP register dump proving Window X/Y and actual composited Window coverage over the pommel region. Without that, the Window is the leading attribution, not a closed mechanism.

### H-scroll / Scroll State

Evidence:

- Static VDP setup uses MODE3 `0x00`, full-plane horizontal scroll mode.
- The current scroll commit writes only two H-scroll words: one FG and one BG value.
- No line-scroll or cell-scroll mode evidence was found.

Attribution: **weak / not supported** for a localized pommel-only stripe.

### Timing / Partial Commit

Evidence:

- The artifact is described as final-composite only, while Plane B layer view is clean.
- No synchronized before/after VBlank title-frame VRAM snapshots were captured.

Attribution: **unresolved, lower than Window**. Timing remains possible only because runtime capture is incomplete.

### Emulator-Specific Behavior

Evidence:

- This task uses Exodus screenshot evidence. No same-frame MAME/BlastEm/Exodus composite comparison was produced.
- Prior reports caution that MAME/Exodus evidence can diverge for active visual state.

Attribution: **unresolved**. No emulator-specific conclusion can be made from current evidence.

## Runtime Capture

Capture attempted in this task: **NO new emulator runtime capture**.

Reason:

- The previous Build 0120 title composite stripe task already attempted MAME debugger capture and failed to obtain synchronized title-frame VDP/SAT/Window/VRAM state.
- The present prompt is anchored to Exodus visual evidence. A fresh MAME CPU-memory-only run would not directly answer whether Exodus Window state is composited over the pommel.
- No safe, non-invasive, existing Exodus automation path is available in this workspace to dump final-composite VDP registers/VRAM at the exact annotated frame.
- The task forbids diagnostics, bookmarks, state forcing, and source/ROM changes.

Runtime data available from prior evidence, not newly captured:

- VDP static setup: Plane A `0xE000`, Plane B `0xC000`, Window `0xF000`, SAT `0xF800`, HScroll `0xFC00`, MODE3 `0x00`.
- Prior sanity capture: early `vdp_commit_sprites` state `0/0/0`, not title state; useful only to show SAT state can persist mechanically.

VDP registers: not captured at the exact title composite frame.

Plane A region: visually not overlapping in Exodus Plane A pane; no nametable dump.

Plane B region: visually clean in Exodus Plane B pane and task-local pommel crop; no synchronized VRAM dump.

SAT entries: one visible Sprite-pane box; no decoded title-frame active SAT list.

Window state: visible patterned garbage in Window pane; no synchronized Window X/Y register dump.

H-scroll state: static full-plane mode only; no synchronized H-scroll table dump.

## D00298 Safety

D00298 reached during task: **NO**.

Dangerous write avoided: **YES**. No runtime stepping was performed, and the task did not step over `runtime_genesis_pc 0x0003B292` or approach `runtime_genesis_pc 0x0005A724`.

## Classification

Final attribution: **Window visibility / Window VRAM overlap artifact - LIKELY, not closed**.

Confidence: **MEDIUM**.

Evidence supporting:

- User-observed final composite artifact is absent in Layer B at the same visual region.
- Local Plane B pommel crop is clean.
- Plane A visible content is lower text, not the top sword pommel.
- Sprite pane shows only a small box that does not visually match the pommel stripe location or shape.
- Window pane shows strong striped/garbage patterns, matching the visual class better than the other candidates.
- Build-state inventory already found no Window clear/staging/commit path and an overlapping Window VRAM footprint.

Evidence against other candidates:

- Plane B: clean at the pommel in the layer viewer.
- Plane A: no visible top-pommel overlap in the Plane A viewer.
- H-scroll: static mode is full-plane, not per-line/cell; only two H-scroll words are committed.
- Sprite/SAT: no visual overlap demonstrated by the one Sprite-pane box, though not fully excluded.

Evidence still needed before fix design:

- A synchronized title-frame final-composite screenshot plus VDP registers, especially Window X/Y, MODE3, Plane A/B/Window/SAT bases.
- VRAM dumps for Plane A, Plane B, Window, SAT, and H-scroll at that same frame.
- Decoded active SAT entries at the same frame.
- Exact artifact pixel coordinates from the annotated final-composite screenshot.

No fix design is justified from this report alone.

## Open / Closed Issues Impact

Open issues touched:

- OPEN-001 - active title/attract graphics incomplete; this report narrows the pommel artifact attribution.
- OPEN-023 - active Window layer path remains unimplemented/garbage; this is the leading attribution.
- OPEN-024 - active sprite subsystem incomplete/garbage; considered but not selected as leading attribution for this specific artifact.
- OPEN-006 - context only for sprite palette/high-bank risk.
- OPEN-015 - context only for crash-report reliability; no crash data used.
- OPEN-021 - context only; not substantively touched.

Closed issues touched: NONE.

New issues opened: NONE. The leading Window attribution is already covered by OPEN-023 and OPEN-001.

Issues closed: NONE.

Issues intentionally deferred: D00298 dynamic path, sprite subsystem completion, Window implementation/fix design, synchronized VDP runtime capture.

KNOWN_FINDINGS impact: **Option A - no update**. The attribution is likely but not yet a durable mechanism-level finding.

## STOP

STOP triggered: **NO** for this evidence-only task. The report produces a bounded visual attribution and records the missing runtime evidence before any fix design.
