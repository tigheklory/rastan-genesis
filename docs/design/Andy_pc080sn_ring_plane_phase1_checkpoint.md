# Andy — PC080SN Ring-Plane Research Phase 1: Boundary Inventory (checkpoint)

**Date:** 2026-07-24 · **Mode:** research only — NO source/ROM/tool/spec/hook/counter change. Context Build 0235 (`9aff0b11…`). Sources read: RULES.md, tilemap_hooks.s, vdp_comm.s, specs/rastan_direct_remap.json, build/rastan-direct/address_map.json, Ghidra exports (call_graph_edges.tsv). **No runtime tracing, no full call graph, no table dereferencing** (deferred to Phase 2).

**Future goal (Phase 2+):** replace the *higher-level arcade map-publication* calls with Genesis-native circular Plane A/Plane B operations, instead of stacking another renderer behind the current low-level PC080SN fill/register-write translators.

---

## 1. Current-hook inventory (33 tilemap/plane-related opcode_replace + Genesis hooks)
### Low-level PC080SN translators (the layer we want to stop extending)
| Arcade PC | Genesis hook | Role |
|---|---|---|
| 0x055968 | `genesistan_hook_tilemap_plane_a` | BG strip producer (arcade 0x055968 → plane_a body 0x070248) |
| 0x055990 | `genesistan_hook_tilemap_fg` | FG strip producer (LIVE Stage 1 FG boundary → body 0x0703EA; KF-040 bypass) |
| 0x055AB4 | staged_scroll_{x,y}_{bg,fg} | Scroll-register write (4 MOVE.W → staged vars) |
| 0x055904 | `genesistan_hook_pc080sn_descriptor_rebuild` | Descriptor source-pointer relocation |
| 0x05A4DE | `genesistan_hook_tilemap_bg_blockcopy` | BG block-copy engine (title/attract art) |
| 0x0561B6 | `genesistan_hook_cwindow_clear` | C-window fill → staged_bg/fg blank + all rows dirty |
| 0x03AD44 | `genesistan_hook_3ad44_dispatch` | Polymorphic A0 dispatch; 4 tilemap callers (0x03AE70/80, 0x03AF38/48) reuse `tilemap_bg_fill` |
| — (via 3ad44) | `genesistan_hook_pc080sn_bg_scroll_fill` / `_fg_scroll_fill`, `tilemap_bg_fill[_tall]` / `tilemap_fg_fill[_tall]` | Genesis-side fill bodies |
| 0x03A350/0x03A6FE/0x03A708/0x03A72A/0x03AAEA/0x03D04C | `genesistan_hook_inline_fg_write_*` (6) | Inline FG tile writes |
| 0x055C2E / 0x055C5E | `genesistan_hook_itempage_strip_populate` / `_blit` | Item-page strip (KF-028/OPEN-016) |
| 0x03ABBA/0x03ABC0, 0x03B098/0x03B09E | staged_scroll_{x,y}_bg | Inline scroll writes |
| 0x03BB48,0x03C2E2,0x03C3FE,0x03C4D2…0x03C950,0x0563A6 | glyph/number/highscore/text-writer hooks (11) | HUD/text tile production (frontend) |

### Genesis-only plane machinery (vdp_comm.s — the ring target)
`vdp_project_bg_tall_if_dirty` / `vdp_project_fg_tall_if_dirty` (32×64 window projection of a 64-row tall buffer), `vdp_commit_bg_strips_if_dirty`, `vdp_commit_fg_narrow_strips`, `vdp_commit_scroll`, `.Lplane_dma_row`. **These already emulate a circular plane in software** — the ring-plane redesign should subsume them.

---

## 2. Arcade-address mapping (immediate callers, from call_graph_edges.tsv)
- **0x055AB4 (scroll commit)** ← callers **0x041F30**, **0x05744E**.
- **0x05A4DE (block-copy)** ← callers **0x05744E**, **0x0574A4**.
- **0x041F30** ← **0x03A008** (`vector_1d_target_03a008` — a per-frame vector/interrupt handler).
- **0x05744E** callees = **0x055AB4** (scroll) + **0x05743C** (mid, unknown) + **0x05A4DE** (block-copy) — i.e. 0x05744E *publishes* scroll and tiles together.
- **0x050634** — Stage 1 setup loop that calls the tilemap dispatcher (per the 0x055990 note); scene-init.
- Callers of 0x055968/0x055990/0x055904/0x050634/0x05744E are **absent from the edge list** → they are reached via **jsr-through-pointer / jump tables / vectors** (must be resolved at runtime in Phase 2).

---

## 3. Candidate semantic producer roots (Phase 2 targets — publish ABOVE the low-level fills)
1. **0x05744E — primary map-publication root.** Calls scroll-commit + block-copy + 0x05743C in one place; the strongest single "publish the plane" boundary to replace with native ring Plane A/B writes. **[highest priority]**
2. **0x041F30 — per-frame scroll updater** under vector 0x03A008 (calls scroll-commit). Owns per-frame BG/FG scroll; maps to native VSRAM/HSCROLL in the ring model.
3. **0x050634 — Stage 1 scene-setup loop.** Drives the tilemap dispatcher during level init; the scene-init publication boundary.
4. **0x0574A4 — secondary block-copy caller** (title/attract art path; distinguishes frontend vs gameplay publication).

---

## 4. Separated boundaries (known classification)
- **Scene initialization:** 0x050634 (Stage 1 setup), 0x0561B6 (C-window clear), item-page 0x055C2E/0x055C5E.
- **BG producers:** 0x055968 (plane_a → 0x070248), `pc080sn_bg_scroll_fill`, `tilemap_bg_fill[_tall]`, block-copy 0x05A4DE.
- **FG producers:** 0x055990 (→ 0x0703EA, live Stage 1), `pc080sn_fg_scroll_fill`, `tilemap_fg_fill[_tall]`, inline_fg_write_* (6 sites).
- **Scroll commits:** 0x055AB4 (4-register), 0x041F30 (per-frame caller), inline scroll writes 0x03ABBA/0x03B098; staged_scroll_* vars.
- **Visual tile production:** block-copy 0x05A4DE, fill bodies, glyph/text/number producers (frontend).
- **Collision-map production:** entangled with the BG producer cluster around **arcade 0x0559xx** (BG producer 0x0559B2 / store 0x0559F0 → collision map **0x10DE00**, per KF-067 / OPEN-0159). **Distinct data channel from the visual plane — must be classified separately in Phase 2** (a ring-plane redesign must not silently drop or misalign it).

---

## 5. Known data/state variables
- **Genesis (staging):** staged_bg_buffer, staged_fg_buffer, staged_bg_tall_buffer, staged_fg_tall_buffer, staged_scroll_{x,y}_{bg,fg}, bg_tall_dirty, bg_tall_project_base, fg_tall_dirty, fg_tall_project_base, bg_row_dirty, fg_row_dirty, genesistan_current_scene_id.
- **Arcade (A5-relative / abs):** a5@0x10EE (fg_scroll), a5@0x10EC (bg_scroll), a5@0x10B0/0x10AE (secondary scroll), a5@0x10A8 (BG/FG producer selector, 0=BG/0x80=FG), a5@0x1040 (PC080SN rebuilt pointer table), a5@0x10CA&3 (page/subrow), collision map 0x10DE00 (→ Genesis 0x00FF1E00, partly un-rebased per OPEN-0159).

---

## 6. Exact Phase 2 trace entry points
- **UP:** resolve the callers of **0x05744E** and **0x050634** (jump-table/vector/pointer — needs runtime PC capture or pointer-table read); trace vector **0x03A008 → 0x041F30**.
- **DOWN:** from **0x05744E** into **0x05743C** (unknown mid), **0x055AB4**, **0x05A4DE**; from **0x050634** into the tilemap dispatcher path.
- **Producer cluster:** arcade **0x0559xx** (0x055968 BG, 0x0559B2/0x0559F0 collision, 0x055990 FG) — separate visual vs collision passes.
- **Genesis hook bodies (candidate replacement layer):** plane_a 0x070248, fg 0x0703EA, and vdp_comm.s tall-projection/commit routines.

---

## 7. Unresolved questions (do NOT solve now)
1. Who calls 0x05744E and 0x050634 (jump-table/vector origin)? Single publication root or per-mode (title vs gameplay) variants?
2. Is 0x05744E the *complete* map-publication boundary, or does per-frame scrolling (0x041F30) publish independently of it?
3. How is collision-map (0x10DE00) production related to the visual BG producer — same walk (0x0559B2) or a separate pass? A ring-plane redesign must preserve it.
4. What arcade concept does the Genesis 64-row tall buffer / 32-row window mirror — an arcade virtual map, or a Genesis-only construct? (Determines whether native ring writes replace it 1:1.)
5. Is the correct replacement layer the arcade callers (0x055968/0x055990) or the Genesis hook bodies (0x070248/0x0703EA)?
6. Which producers run once at scene-init vs every frame (publication cadence for the ring model)?
7. Role of 0x05743C (mid-level callee of 0x05744E) — tile source selection, page walk, or descriptor build?

## Compliance
No source, ROM, tool, spec, hook, or build counter changed. Counter remains 235. Phase 1 checkpoint only.
