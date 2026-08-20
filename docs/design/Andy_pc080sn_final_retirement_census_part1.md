# Andy — PC080SN Final Retirement Census, Part 1

**Type:** Analysis / verification ONLY. **Production changes: NONE. ROM build: NONE.**
**Accepted baseline:** Build 0297 (PC090OJ fully retired; 0x03AD44 now PC080SN-C-range-only).
Scope: enumerate + classify the remaining PC080SN compatibility architecture. Per-component upstream
semantic-owner tracing, the item-page text defect, and the demo-BG root cause are **Part 2** (not here).

## Phase 0
- **CONFIRMED/STRONG priors:** KF-014 (PC080SN tile-LUT O(1) contract, tile-code domain 0x0000..0x3FFF),
  KF-015 (full-plane scroll, raw-Y negation +8 bias, no per-line — STRONG), KF-010 (BG→Plane B, FG→Plane A),
  KF-013 (text dispatch fires inside VBlank), KF-011 (arcade Level-5 VBlank owns progression — GLOBAL).
- **Rediscovery-Hazard HIGH:** KF-011, KF-015 (NORMAL actually), KF-020/KF-021 (contaminated-context sprite/
  plane evidence — avoid stale plane conclusions).
- **Applicable issues:** OPEN-001/OPEN-018 (native map/level rendering incomplete), OPEN-017 (FG/BG
  progression, hardware run), OPEN-024 (PC090OJ — now removed, narrowed). Item-page PC080SN text defect and
  item-page→attract FG/BG mismatch are the known open PC080SN defects (Part 2).
- **Task classification:** INFRASTRUCTURE census (analysis).
- **Contradiction detected:** NONE.

## Phase 1 — Component census

Addresses: `runtime_genesis_pc` for hooks; `a5@0xNNN` = arcade WRAM PC080SN state; C-window
`HW_ADDRESS 0x00C00000..0x00C0FFFF`. Source: `apps/rastan-direct/src/tilemap_hooks.s` (+ the C-range half of
`genesistan_hook_3ad44_dispatch` in `pc090oj_hooks.s`), `specs/rastan_direct_remap.json` (29 PC080SN-hook
entries), `apps/rastan-direct/out/symbol.txt`, `build/genesis_postpatch.disasm.txt`.

### A — PC080SN compatibility debt (reachable; must be retired before 0x03AD44 deletion)
Interception hooks that exist only because the arcade specializes graphics for the PC080SN chip (C-window
name-table writes, chip scroll, chip text, descriptor tables). They translate to native staging and return.

| # | Component (runtime PC) | Arcade interception (arcade_pc) | Role |
|---|---|---|---|
| 1 | `genesistan_hook_3ad44_dispatch` @0x072b9a | 0x03AD44 (4 callers 0x3AE70/80,0x3AF38/48) | C-range polymorphic fill dispatcher |
| 2 | `genesistan_hook_tilemap_bg_fill` @0x070f32 | (dispatch BG-names branch) | C-window BG name fill → staged_bg_buffer |
| 3 | `genesistan_hook_tilemap_fg_fill` @0x071008 | (dispatch FG-names branch) | C-window FG name fill → staged_fg_buffer |
| 4 | `genesistan_hook_tilemap_bg_blockcopy` @0x0711ec | 0x05A4DE | BG block copy into staging |
| 5 | `genesistan_hook_pc080sn_bg_scroll_fill` @0x072124 | (dispatch BG-scroll branch) | **STUB (no-op)** per-line BG scroll |
| 6 | `genesistan_hook_pc080sn_fg_scroll_fill` @0x07212e | (dispatch FG-scroll branch) | **STUB (no-op)** per-line FG scroll |
| 7 | `genesistan_hook_pc080sn_descriptor_rebuild` @0x0721f2 | 0x055904 | Rebuild PC080SN BG/FG descriptor pointer table |
| 8 | `genesistan_hook_cwindow_clear` @… | 0x0561B6 | C-window clear → staging clear |
| 9 | `genesistan_hook_tilemap_plane_a` @0x070a94 | (FG plane production entry) | Arcade FG C-window → Plane A staging |
| 10 | `..._plane_a_selector0_native` @0x07042a | 0x055968 | Plane A selector-0 native production |
| 11 | `..._plane_a_selector12_native` @0x07055c | 0x055990 | Plane A selector-1/2 native production |
| 12 | `genesistan_plane_a_pan_publish_entering_rows_up` @0x0706a4 | 0x055790 | Plane A pan-up row publish |
| 13 | `genesistan_plane_a_pan_publish_entering_rows_down` @0x0706fc | 0x055704 | Plane A pan-down row publish |
| 14 | `genesistan_hook_tilemap_fg` @0x070d0c | (FG column production) | Arcade FG production → staging |
| 15 | `genesistan_stage_bg_collision_column` | (called from BG production) | BG collision side-channel from PC080SN strip state |
| 16–21 | `genesistan_hook_inline_fg_write_{3a550,3a8fe,3a908,3a92a,3acea,3d04c}` | 0x03A350/0x03A6FE/0x03A708/0x03A72A/0x03AAEA/0x03D04C | Inline arcade FG C-window word writes → staging |
| 22 | `genesistan_hook_textwriter_dispatch` @0x0732xx | 0x0563A6 | Shared PC080SN text writer → BG/FG staging |
| 23 | `genesistan_hook_glyph_renderer_3bd48` | 0x03BB48 | Glyph renderer (C-window text) |
| 24 | `genesistan_hook_number_renderer_3c2e2` | 0x03C2E2 | Numeric renderer (C-window text) |
| 25 | `genesistan_hook_highscore_fg_producer` @0x… | 0x03C3FE | High-score FG text producer |
| 26–34 | `genesistan_hook_text_writer_{3c4d2,3c550,3c586,3c636,3c6dc,3c75c,3c7a4,3c830,3c950}` | 0x03C4D2…0x03C950 | PC080SN text-writer variants → staging |
| 35 | `genesistan_hook_itempage_strip_populate` @0x072254 | 0x055C2E | Item-page tile strip populate |
| 36 | `genesistan_hook_itempage_strip_blit` @0x0722ac | 0x055C5E | Item-page tile strip blit |

Plus Category-A **shadow/descriptor state**: `PC080SN_DESC_REBUILD_SRC_TABLE` (0x00FF1000) and the rebuilt
BG/FG descriptor pointer table (arcade 0x0003951C / Genesis WRAM), consumed by #7 and the plane producers.

**Count of reachable PC080SN compatibility components: 36 hook components** across **29 arcade C-range/text
interception points** (0x03AD44 alone covers the 4 fill callers), plus the descriptor/shadow state above.

### B — dead / unreachable PC080SN code
None positively confirmed dead in Part 1. #5/#6 (`pc080sn_bg/fg_scroll_fill`) are **reachable but no-op
stubs** (per-line scroll deliberately not implemented, KF-015 full-plane model) — classified A (a live
C-range interception point that currently does nothing), not B. Any truly-dead PC080SN remnants are a Part-2
deliverable.

### C — final native Genesis infrastructure (must survive PC080SN retirement)
- Plane staging buffers: `staged_bg_buffer` (0x00FF40E4), `staged_fg_buffer` (0x00FF50E4).
- Scroll staging: `staged_scroll_x_bg/x_fg/y_bg/y_fg` (0x00FF40DC..0x00FF40E2).
- Commit path: `vdp_commit_bg_strips_if_dirty` (0x0701A0), `vdp_commit_fg_strips_if_dirty` (0x0701E4),
  `vdp_commit_fg_narrow_strips` (0x07234E), `vdp_commit_scroll` (0x070248); plane/`palette_dirty` flags.
- Tile residency data (KF-014): `genesistan_pc080sn_tile_vram_lut` (0x0F8DC0), `pc080sn_attr_lut` (0x100DC0),
  `pc080sn_tile_rom` (0x100E00).
- Native VDP port access: `0xC00000` (VDP data), `0xC00004` (VDP control) — Genesis hardware, not
  compatibility (note: 0xC00000 is shared with the arcade C-window base — see Phase 2).

### D — original arcade semantic state (input to native code; must remain)
Arcade PC080SN WRAM fields (`a5 = 0x00FF0000`): scroll `0x10AE/0x10B0` (FG X/Y), `0x10EC/0x10EE` (BG X/Y);
dest columns `0x10A0` (BG), `0x10A4` (FG); selector `0x10A8`; strip/group/walker/subcol/table-index
`0x10BA/0x10CA/0x10CC/0x10DA/0x10F4/0x10F6/0x10FC/0x1386`. These are arcade decisions the native hooks read.

### E — unrelated
Sprite/SAT (native, PC090OJ removed), palette routing (OPEN-006), input shadows, crash handler, sound.

## Phase 2 — C-range executable audit (0x00C00000..0x00C0FFFF)
142 `0x00C0xxxx` executable operands. Buckets:
- **Native Genesis VDP ports (not compatibility):** `0xC00000` (VDP data, 29), `0xC00004` (VDP ctrl, 13),
  `0xC0009x`/`0xC0010x` VDP register/DMA command words (e.g. 0xC00102, 0xC00101, 0xC09320/9376/9170/9140) —
  the native commit path programming the VDP.
- **Reachable PC080SN compatibility dependencies (arcade C-window intercepted by the Cat-A hooks):** the
  C-window base literals `0xC00000/0xC00100` (BG names), `0xC08000/0xC08100` (FG names, 36), `0xC04000`
  (BG scroll, 7), `0xC0C000` (FG scroll, 12), and the descriptor/plane producer C-window offsets
  (0xC08c60/8d6c/8e64/… family). These are the C-range side the four 0x03AD44 callers and the plane/text
  producers target; they are handled by the Category-A hooks above.
- **Harmless literal/comparison:** the dispatch's own C-range bound compares (`cmpi.l #0xC00000/#0xC04000/
  #0xC08000/#0xC0C000/#0xC10000`).
- **Semantic source (not virtual hardware):** the arcade producers computing C-window destinations from
  a5 state (Category D) before the hook intercepts.

**Complete list of reachable PC080SN compatibility dependencies = the 36 Category-A hook components (Phase 1
table) + the descriptor/shadow state.** The count of distinct C-window *address families* still intercepted:
BG-names (0xC00000–0xC04000), BG-scroll (0xC04000–0xC08000), FG-names (0xC08000–0xC0C000), FG-scroll
(0xC0C000–0xC10000).

## Phase 3 — 0x03AD44 current ownership (the four known callers)
All four are pure PC080SN name-table fills with blank tile 0x20 (`d0=32`), `d1`=word count; nothing besides
PC080SN hardware realization occurs at the call boundary:

| arcade caller | A0 (C-window) | C-range family | Genesis helper receiving it | immediate arcade fn |
|---|---|---|---|---|
| 0x03AE70 | 0xC00100 | **BG names** | `genesistan_hook_tilemap_bg_fill` | 0x03AE64 setup (title/frontend plane init) |
| 0x03AE80 | 0xC08100 | **FG names** | `genesistan_hook_tilemap_fg_fill` | 0x03AE74 setup (same init routine) |
| 0x03AF38 | 0xC00000 | **BG names** (full 4096) | `genesistan_hook_tilemap_bg_fill` | 0x03AF2C setup (full-plane clear) |
| 0x03AF48 | 0xC08000 | **FG names** (full 4096) | `genesistan_hook_tilemap_fg_fill` | 0x03AF3C setup (full-plane clear) |

None invoke BG/FG scroll — those C-range families reach the dispatcher (or the scroll-fill stubs) from other
producers, to be traced in Part 2. No non-PC080SN work occurs at these four boundaries.

## Retained Genesis infrastructure (must not disappear)
`staged_bg_buffer`, `staged_fg_buffer`, `staged_scroll_x/y_bg/fg`, `vdp_commit_scroll`,
`vdp_commit_bg/fg_strips_if_dirty`, `vdp_commit_fg_narrow_strips`, the PC080SN tile-LUT/attr-LUT/tile-ROM
(KF-014), plane/palette dirty flags, and native VDP port access. These are final Genesis Plane/scroll format
and survive PC080SN retirement — the Category-A hooks must feed them, then be removed.

---

**Remaining reachable PC080SN compatibility components: 36** (hook components across 29 arcade interception
points, + descriptor/shadow state).

**PC080SN census complete: YES** for Part-1 scope (full component enumeration + A/B/C/D/E classification +
four-caller ownership + native-infra distinction). **Unproven / deferred to Part 2:** per-component upstream
arcade semantic-owner tracing to the highest cut boundary; positive dead-code (Category B) determination;
the exact final-vs-compatibility split inside the descriptor-rebuild / text-writer / item-page paths; and
the item-page text defect + demo-BG root cause (explicitly Part 2).
