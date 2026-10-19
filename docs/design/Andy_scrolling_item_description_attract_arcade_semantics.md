# Andy — Scrolling Item-Description Attract Screen: Arcade Semantics + Native Prebake Design

**Date:** 2026-10-18 · **Agent:** Andy · **Type:** READ-ONLY arcade reverse-engineering + architecture
design. **No** Genesis production/Makefile/generator/spec/manifest change, **no** ROM, **no** MAME,
**no** trace/route, **no** build number/counter change, **no** implementation. Cody's title work
untouched. The only source-tree changes are additions to the existing C decompilation tree + its
coverage/README (authorized by the task).

**Baseline:** Build **0446** (counter 446). Subject: the **scrolling item-description attract screen**
only.

**Tool reuse (RULES §13/§18):** reused the existing arcade C tree (`rastan_world_stream.c`,
`rastan_world_scroll.c`, `rastan_scene_map.c`), `build/maincpu.disasm.txt`,
`build/rastan-direct/address_map.json`, and existing design docs (`Andy_C00828_itemdesc_bg_producer_
route_design.md`, `Andy_build0118/0119_itempage_*`, `Andy_0010D100_itempage_descriptor_cluster_crash_
design.md`). New Ghidra/raw work added only for the attract-specific orchestration not previously
decompiled. No second decompilation tree; no function re-done.

**Evidence tags:** **[SRC]** arcade disasm/C this task · **[DOC]** prior report · **[OBS]**
screenshots · **[INT]** interpretation · **UNKNOWN** where static evidence is insufficient.

---

## 1. EXECUTIVE RESULT

The item-description screen is a **continuously, vertically scrolling list of item descriptions**,
driven by the **same PC080SN scroll/stream/decompress machinery the gameplay background uses**. Per
frame it is almost entirely a **scroll-register update**; the text/layout is decompressed only **once
per scroll loop**, not per frame. Concretely **[SRC]**:

- **Attract state:** `A5@(0)=2, A5@(2)=2, A5@(4) ∈ {4,6}` (two sub-pages of the one screen).
- **Per-frame tick `0x5607C`:** every 4th frame, BG vertical scroll `A5+0x10EE −= 1` (wrap mod 512),
  commit all scroll registers via `0x55AB4`, and run a per-item dwell timer over the icon descriptors
  at `0xD00170`.
- **Scroll commit `0x55AB4`:** `A5+0x10EC→0xC40000` (FG X), `A5+0x10AE→0xC40002` (FG Y),
  `A5+0x10EE→0xC20000` (**BG Y — the item list's scroll**).
- **Row stream `0x560DA`:** every 8 scroll units advance/blank one BG row-region; the dest cursor
  `A5+0x10A0` wraps within the C-window; at the wrap boundary (`0xC00F00`) the page is **re-built**
  (`0x56056` → BG metatile decompress `0x563A6` + icon sprite copy `0x56114`).
- **BG content:** the item-description text/layout is a **ROM metatile stream decompressed once per
  loop** into the PC080SN BG C-window; item **icons** are PC090OJ sprite descriptor records copied to
  object RAM `0xD00170`.

**Because the arcade mechanism is "tall static map + scroll-register increment," a native Genesis
version can prebake the entire item-list map/patterns/icons and drive a native VDP VSRAM scroll from
the retained arcade scroll counter — eliminating per-frame row streaming, re-decompression, and plane
DMA.** The list wraps at 512 scroll units (= 64 rows = a 64-row VDP plane), so the whole list fits one
prebaked plane and loops via VSRAM wrap. **[INT, grounded in §SCROLL]**

---

## 2. ATTRACT STATE MACHINE (bounded)

| Node | Arcade PC | Role |
|---|---|---|
| per-frame tick | **`0x5607C`** | item-desc scroll + dwell timer (reached via `bsr 0x5607C` from the item-page processing at `0x55E92`) |
| page (re)build A | `0x56032` | decompress BG page (`0x563A6`, dest `0xC00828`) + icon sprites (`0x56114`, table `0x56226`→`0xD00170`); store cursor `A5+0x141C` |
| page (re)build B | `0x56056` | decompress BG page (`0x563A6`, src ROM `0x5697E`, dest `0xC00028`) + icon sprites (`0x562B0`) |
| row stream / loop wrap | `0x560DA` | advance/blank a BG row-region; at cursor `0xC00F00` call `0x56056` |
| scroll commit | `0x55AB4` | write scroll to PC080SN registers |
| state variables | `A5@(0)/@(2)/@(4)` | attract state triple = `2/2/{4,6}` |

Entry condition and exact exit/next-state transition (timeout → next attract screen) live in the
frontend attract dispatcher, which reads `A5@(0/2/4)`. The **dispatcher's exact entry/exit PCs were
not fully traced this task** (scope: the item screen itself); the per-item dwell timer and the
`A5@(4)` page toggle (4↔6) are the in-screen sequencing. **Entry/exit transition PCs: UNKNOWN (bounded
out).**

---

## 3. EXISTING DECOMPILATION INVENTORY (mandatory first)

| Function | Existing C | Status |
|---|---|---|
| `0x563A6` BG metatile decompressor | `rastan_scene_map.c` (`raw/000563a6.c`) | **EXISTING — sufficient** |
| `0x55C4A/0x55C5E/0x55C7A` PC080SN column stream | `rastan_world_stream.c` (`raw/00055c4a.c`) | **EXISTING — sufficient** |
| `0x557BA/0x55854` PC080SN Y-scroll dispatch | `rastan_world_scroll.c` (`raw/000557ba.c`) | **EXISTING — sufficient** |
| `0x55AB4` PC080SN scroll commit | `rastan_world_scroll.c` (`raw/00055ab4.c`) | **EXISTING — sufficient** |
| `0x55B3C` FG X-scroll update | `rastan_world_scroll.c` | **EXISTING — sufficient** |
| shared text writer `0x565A6` + sub `0x565CE` | documented in `Andy_C00828_…` | **EXISTING (doc) — sufficient** |
| **`0x5607C` item-desc tick** | — | **MISSING → ADDED** |
| **`0x560DA` row-stream/loop-wrap** | — | **MISSING → ADDED** |
| **`0x56032`/`0x56056` page (re)build entries** | — | **MISSING → ADDED** |
| **`0x56114` icon sprite-record copy** | — | **MISSING → ADDED** |

**Added** (new, following existing conventions): `analysis/decompilation/c/raw/0005607c.c` +
`analysis/decompilation/c/rastan_attract_item_description.c`; `function_coverage.csv` rows for
`0x5607C/0x560DA/0x56032/0x56114`; README layout entry. **No existing function was re-decompiled or
overwritten.** The scroll/stream/decompressor were **reused** as-is.

---

## 4. SCROLL MECHANISM (centerpiece)

| Property | Value | Source |
|---|---|---|
| What scrolls | the whole item-list BG tilemap (viewport moves up through it, looping) | [SRC] |
| Axis | **vertical** (BG Y) | [SRC `A5+0x10EE→0xC20000`] |
| Scroll variable | `A5+0x10EE` (BG Y position) | [SRC] |
| Representation / units | 9-bit pixel position, `& 0x1FF` (0..511) | [SRC `andiw #511`] |
| Increment | **−1 per step** | [SRC `subqw #1`] |
| Update frequency | one step **every 4th frame** (`A5+0x1392 & 3 == 0`) | [SRC] |
| Start | set at entry (page build) | [SRC] |
| End / wrap | wraps **mod 512** (continuous loop) | [SRC] |
| Row-stream boundary | every **8 scroll units** → one new BG row-region (`0x560DA`) | [SRC] |
| Loop re-build | at dest cursor `0xC00F00` → re-decompress page (`0x56056`) | [SRC] |
| Scroll commit target | PC080SN **`0xC20000`** (BG Y) via `0x55AB4` | [SRC] |

**Native VDP scroll-register equivalent possible: YES.** The arcade writes a single BG Y scroll value
to a scroll register; the Genesis equivalent is a VSRAM write. With the full 64-row item list prebaked
into one native plane, the row streaming and per-loop re-decompression are unnecessary — only the
scroll value and its 4-frame cadence need to persist. **[INT]**

---

## 5. ITEM DATA

| Field | Value | Source |
|---|---|---|
| Item set (project terms) | AXE / HAMMER / FIRE SWORD / SHIELD / MANTLE / ARMATURE / MEDICINE / POISON / GOLD SHEEP / JEWEL (~10) | [DOC C00828 §9] |
| Description text source | ROM text (e.g. `0x0005697E`), walked by the shared writer `0x565A6` / decompressed via `0x563A6` | [SRC/DOC] |
| Item-name / description layout | BG metatile stream (per-round ptr table `0x562CA`), `0xFF`=col, `0x00`=end | [SRC `0x563A6`] |
| Punctuation substitution | `0x565CE`: `0x21→0x2744 … 0x3F→0x274B` (same aliases as the title glyph map) | [DOC] |
| Item icons | PC090OJ 8-byte sprite descriptor records, ROM tables `0x56226`/`0x562B0` → object RAM `0xD00170` | [SRC `0x56114`] |
| Item index / ordering | fixed ROM order (the list is a single logical strip); icon descriptor cursor `A5+0x141C` | [SRC] |
| Per-item dwell | descriptor field `+2` countdown; at `16`, clear field `+4` | [SRC] |
| Exact item count | = length of the `0xFFFF`-terminated icon table / the text stream — **not re-counted this task (UNKNOWN exact; ~10 per the enumeration)** | — |

No English names were invented beyond the already-established project enumeration. **[DOC]**

---

## 6. VISUAL OWNERSHIP

| Element | Source | Layer/chip | Static/dynamic | Update trigger | Producer |
|---|---|---|---|---|---|
| Item-description text/layout | ROM metatile stream | PC080SN **BG (Plane B)** | **static content** | entry + loop wrap | `0x563A6` decompress |
| Item icons | ROM sprite records | **PC090OJ sprites** | static content | entry + loop wrap | `0x56114` → `0xD00170` |
| Vertical scroll position | `A5+0x10EE` | BG scroll register | **dynamic** | every 4th frame | `0x5607C`+`0x55AB4` |
| FG scroll | `A5+0x10AE/0x10B0` held 0 | FG scroll register | static (0) | — | `0x55AB4` |
| Palette | title/frontend palette row | CRAM | **static** (no cycle proven) | entry | scene palette |
| Top HUD (1UP / HIGH SCORE / 2UP / credit) | live BCD | PC090OJ sprites | periodic | score/credit/blink | shared `native_frontend_hud_emit` (frontend) **[OBS top of screenshots]** |

Layer ownership is proven from code (PC080SN C-window dests for BG; object RAM `0xD00170` for icons),
not appearance. **[SRC]**

---

## 7. ENTRY-ONLY vs PER-FRAME (for native design)

| Work | Classification |
|---|---|
| BG metatile decompress (`0x563A6`), icon sprite copy (`0x56114`), palette, tile/pattern setup | **ENTRY-ONLY / PER-LOOP** (once at entry; re-run only at scroll-loop wrap) |
| BG Y scroll decrement + scroll-register commit (`0x55AB4`) | **PER-FRAME SEMANTIC** (every 4th frame) |
| per-item dwell timer | PER-FRAME SEMANTIC |
| one BG row-region advance/blank (`0x560DA`) | **PER-SCROLL-STEP** (every 8 units) |
| page re-decompress at wrap | **PER-LOOP** |

Crucially, the **arcade does NOT re-render text or rebuild the whole plane every frame** — the
expensive work is entry/loop-only. The per-frame cost is a scroll-register write + timer. This is the
opposite of the title screen's per-frame full-plane republish (see
`Andy_title_screen_vblank_overrun_root_cause_audit.md`). **[SRC]**

---

## 8. CURRENT GENESIS IMPLEMENTATION (read-only)

- **Retained arcade presentation involved:** YES — the item-desc tick (`0x5607C`), scroll commit
  (`0x55AB4`), decompressor (`0x563A6`), row stream (`0x560DA`) all run in the retained arcade worker.
- **PC080SN scroll writes:** translated to **native VDP scroll** (the project's `0xC20000/0xC40000`
  scroll hooks / `vdp_commit_scroll`) — so the scroll itself is already native.
- **PC080SN BG C-window writes (decompressed page + streamed rows):** intercepted by
  `genesistan_hook_tilemap_bg_fill` → `staged_bg_buffer` → `bg_row_dirty` → VBlank DMA. So each
  streamed row-region and the per-loop page rebuild **re-stage and re-DMA** on Genesis.
- **Item icons:** PC090OJ object-RAM writes → the native sprite path.
- **Major unnecessary work on Genesis:** re-staging/re-DMA of the streamed rows and the per-loop page
  rebuild, which exist only because the arcade PC080SN C-window is a 64-row window that must be fed as
  the (taller) logical content scrolls. A prebaked tall native plane removes both.

---

## 9. FUTURE PREBAKED NATIVE DESIGN (no implementation)

**Principle: if Python can know it ahead of time, pre-bake it.** The entire item list is deterministic
ROM content, so:

- **Prebake (Python/offline):** the full item-list **BG tilemap** (all rows, the 64-row looping
  plane), its **tile patterns**, the **item-icon SAT descriptors**, **palette**, fixed attributes, and
  the scroll extents (wrap = 512). Load once on screen entry into a native plane + VRAM + CRAM + SAT.
- **Keep runtime (arcade-owned semantics):** the scroll counter `A5+0x10EE` and its 4-frame cadence,
  the per-item dwell timer, and attract sequencing/credits/Start. These stay with the arcade worker.
- **Per changing frame, the Genesis presentation op is:** write the native **VSRAM BG-Y** value from
  the retained scroll counter when it changes — nothing else. No row stream, no re-decompress, no
  plane DMA, no palette/SAT rebuild.

### Performance classification

| Work | Verdict |
|---|---|
| item-list tilemap, patterns, icons, palette | **CAN PREBAKE** |
| scroll extents / wrap / fixed coords | **CAN PREBAKE** |
| scroll counter, dwell timer, attract sequencing, credits/Start | **MUST REMAIN RUNTIME** (arcade authority) |
| per-frame row stream / re-decompress / plane DMA | **ELIMINATED by prebake** |
| native VSRAM write when scroll changes | **MUST REMAIN RUNTIME** (one register write) |

### Steady-state (unchanged-content frame) targets

- static plane generation: **0** · pattern residency work: **0** · static palette republish: **0** ·
  static SAT rebuild: **0** · per-changing-frame op: **one VSRAM BG-Y write**.

---

## 10. ARCHITECTURE RECOMMENDATION

- **Future cut point:** retained arcade scroll/dwell/sequencing decisions → generated native
  item-list plane/patterns/icons (prebaked once) → native VSRAM scroll write when the arcade scroll
  counter changes.
- **Arcade semantic ownership preserved:** YES. **Genesis-owned attract state machine required:** NO.
  **PC080SN emulation required:** NO. **Generic per-frame item renderer required:** NO.
- This is the **same clean model** recommended for the title screen (prebake static, publish only
  change), and here it is even stronger because the arcade itself proves the screen is
  "static map + scroll register," not per-frame regeneration.

---

## FINAL STATUS

Genesis production source modified: NO. Makefile/generators/specs modified: NO. ROM built: NO. MAME
run: NO. New trace/route: NO. Build number consumed: NO. Build counter changed: NO. C-tree additions
(authorized): `raw/0005607c.c`, `rastan_attract_item_description.c`, `function_coverage.csv`,
`README.md`. Screen implementation started: NO. Phase D/E: NO.
