# Andy/Fable — Rastan Native Genesis Video Architecture Redesign

**Date:** 2026-07-20
**Type:** Analysis and design only. No source/spec/Makefile/runtime/ROM/counter change. No build.
**Evidence dir:** `states/traces/native_genesis_video_architecture_redesign_20260720_181035/`
**Core question answered at the end:** *Can the original Rastan graphics-facing code be rewritten around the Genesis VDP so that the Genesis produces arcade-faithful output without maintaining costly PC090OJ and PC080SN compatibility mirrors, while retaining only the RAM structures genuinely required by the original arcade program?* — **Yes.** The evidence and the design follow.

---

## 0. Materials used (paths + hashes; sha256 first 32 hex)

| Material | Path | Hash |
|---|---|---|
| Rastan arcade maincpu image (Ghidra input) | `analysis/ghidra/rastan_arcade/input/rastan_world_rev1_maincpu_68000.bin` | `4f30b9e7aa946aa33d20e125a1726ff0` |
| Ghidra function inventory (182 fns) | `analysis/ghidra/rastan_arcade/exports/function_inventory.tsv` | `0a10a29aca9d8165e9b75abed0bbb277` |
| Ghidra hardware refs (454 rows) | `analysis/ghidra/rastan_arcade/exports/hw_refs.tsv` | `99acceb1b574468f3f5e627330aad138` |
| Ghidra xrefs (1899) | `analysis/ghidra/rastan_arcade/exports/xrefs.tsv` | `3278227f2851074d138ecdccf6d302f1` |
| Ghidra call-graph edges (198) | `analysis/ghidra/rastan_arcade/exports/call_graph_edges.tsv` | `0964b0f4c3200ee4cc293db96e6647af` |
| Ghidra subsystem map | `analysis/ghidra/rastan_arcade/exports/subsystem_map.md` | `5226f04de4b8dacc29f1fd2a456dd87b` |
| Ghidra unresolved regions (140) | `analysis/ghidra/rastan_arcade/exports/unresolved_regions.tsv` | `5e45105f258b1647fd40ad23b430953a` |
| Rainbow Islands arcade disasm | `build/rainbow_islands_arcade.disasm.txt` | `fcec8c1863f3aa55950f408b423ae749` |
| Rainbow Islands Genesis disasm | `build/rainbow_islands_genesis.disasm.txt` | `022566b16b30aa12b6a3e78272ef7724` |
| Rainbow Islands Genesis ROM | `build/examples/rainbow.zip` | `1be5d55d8405eb2528289448207e06f1` |
| **Rastan arcade↔Genesis address map (point-in-time)** | `build/rastan-direct/address_map.json` | `2fb9a49ade3c6368e33137ddd2e733df` |
| **Patch manifest (point-in-time)** | `build/rastan-direct/rastan_direct_patch_manifest.json` | `cb16570f1fc7df7e974d570835758172` |
| Linear disasm (project) | `build/maincpu.disasm.txt` / `build/genesis_postpatch.disasm.txt` | current tree |
| Prior RI comparative analyses | `docs/design/Andy_rainbow_islands_comparative_translation.md`, `Cody_rainbow_islands_vdp_template_analysis.md`, `rainbow_islands_vs_rastan_vdp_vram_buffering_comparative_trace.md` | current tree |

All Rastan arcade↔Genesis PC correlations below use `address_map.json` (`2fb9a49a…`); it is point-in-time evidence and must be re-read at implementation time, never replaced with a fixed offset.

**Ghidra caveat honored:** `hw_refs.tsv` catalogs only *absolute* hardware references. The three most important gameplay-era producers write through **register-indirect pointers** and do not appear as absolute refs: the PC090OJ actor→sprite expansion engine (`arcade_pc 0x3D054 → 0x3C902` family, writes via `(A1)+` with A1 supplied by callers), the Stage BG/FG tilemap producer (`arcade_pc 0x559B2` family, computed C-window addresses), and the collision side-channel writes derived from it. They were located through the callers listed in hw_refs plus the linear disassembly and this project's runtime traces (KF-044/047/060/065/067 lineage). Unclassified Ghidra regions were treated as potentially-code; the graphics conclusions below rest on xrefs + linear disasm + runtime evidence, not on Ghidra's conservative function set.

---

## 1. The complete arcade hardware-facing surface (Ghidra-derived)

The single most important architectural measurement in this document: **the entire game touches the video chips from a few dozen leaf routines.** From `hw_refs.tsv` (full listing preserved in `hw_surface_inventory.txt`):

### 1.1 PC090OJ sprite RAM (0xD00000–0xD01FFF) — 25 absolute sites in 9 functions, + 1 indirect engine
| Arcade function | Role (validated across this project's builds) |
|---|---|
| `FUN_0000052A` (0x56A/0x570) | cold-init clear of object RAM |
| `FUN_0003AD72` | frontend object-RAM clear (records 0/46-region wipe at 0x3AD76/0x3AD86) |
| `FUN_0003B8B0`, `FUN_0003B902` (+ helper 0x3B930) | frontend/HUD sprite writers (records 4–37: HIGH SCORE glyphs, status) |
| `FUN_00052AA2` | frontend/attract sprite emitter (writes via computed A1) |
| `FUN_00041DAE` | gameplay actor blocks → records 57/96/140/46 (4 blocks; KF-060/065) |
| `FUN_00041F5E` | player + secondary blocks → records 120–137 / 92–95 |
| `FUN_00045DFA` | scene-2 sibling (blocks → records 140/46/96) |
| `FUN_0003ADD8` / 0x3AE86 | PC090OJ ctrl 0xD01BFE (global flip) |
| **`0x3D054 → 0x3C902` engine (indirect)** | the one shared actor→sprite composer: per actor code, walks ROM layout tables, emits exactly d2 16×16 records via `(A1)+` (KF-063/065/067 — engine clobbers d0–d7) |
| `FUN_0003AE28`, `FUN_0003EEFA`, `FUN_0003EF5C` | sprite_ctrl 0x380000 (colbank+flip; KF-066 colbank 0x30) |

**Readback:** hw_refs contains **zero reads of PC090OJ object RAM** anywhere in the game. Sprite RAM is write-only output. Nothing in the arcade program ever depends on reading a sprite record back.

### 1.2 PC080SN tilemap C-window (0xC00000–0xC0FFFF) — 56 absolute sites + indirect producers
- **Frontend/test/attract text and layout writers:** `FUN_000002CA`, `FUN_000003A4`, `FUN_00000502`, `FUN_0000052A`, `FUN_000005CC`, `FUN_00000100`, `FUN_0003AE64`, `startup_common_body` clears, plus the shared text writer `0x3C950` (dual-use with sprites — KF-063's Build-0204 collision) and the title glyph producer `0x3ACAE`.
- **Gameplay producer (indirect):** the `0x559B2` BG pass builds BG/FG columns from stage descriptor tables into computed C-window addresses and — critically — derives the **collision side-channel** from the same descriptor data (Andy_build0159; the Genesis port mirrors this at `genesistan_stage_bg_collision_column`; KF-067's row-base defect lives here).
- **Scroll:** exactly ONE gameplay committer — `FUN_00055AB4` writes X/Y for both planes from `A5+0x10EC/0x10AE/0x10EE/0x10B0` (plus init/reset clears). The entire game's scrolling is four MOVEs from four A5 fields.
- **Readback (the only two in the game):** `FUN_0003A552` (`cmpi.b #0x30,(0xC09EA3)` then writes 0x20) and `FUN_0003AC04` (`cmpi.b #0x43,(0xC09E87)`) — title-screen glyph probes that test what character is currently in a nametable cell. These are the *only* read-after-write dependencies on video memory in the whole program.

### 1.3 Palette RAM (0x200000) — 15 sites in 8 functions
`FUN_00000264` (test), `FUN_0000052A` (init), `FUN_0003B9F8`, `FUN_00045D7C`, `FUN_00045DC4`, `FUN_00047004`, `FUN_00059AD4` (the row-copy converter hooked since Build 0175), plus the sprite-palette **source buffer** path at `A5+0x1600+bank*0x20` → memcpy (KF-066: bank 51 and 0x36 arrive this way). Palette flow is: game code → WRAM source buffer or direct bank write → palette RAM. **No palette readback** beyond the startup RAM test (0x3AEB6/0x3AEDA — a self-test, not gameplay).

### 1.4 Everything else
Inputs (0x390000), sound comm (0x3E0000 — PC060HA, 17 sites), watchdog (0x3C0000), sprite_ctrl (0x380000), one mystery `0x350008` clear. The sound mailbox at WRAM `0x10FFFF` (`FUN_00055CA2`) is gameplay-side and irrelevant to video.

### 1.5 The architectural conclusion from the surface
The arcade program does **not** smear video-chip access through its gameplay code. Gameplay code manipulates actor blocks, camera fields, stage descriptors, and palette source buffers in A5-relative WRAM — and a **small set of leaf translators** (§1.1–1.3) converts that intent into chip formats at well-defined call boundaries. This is precisely why 200+ builds of this project succeeded by hooking those exact boundaries. The "highest useful points where the program still expresses intent" are the *entries* of these leaf functions: at entry, they hold pure gameplay semantics (actor pointer, code, X/Y attr, budget; stage descriptor pointer + column index; bank + source row; scroll fields). Everything after entry is chip-format mechanics that the Genesis does not need.

---

## 2. Arcade state vs. arcade-chip output (the six categories)

| Category | Contents | Verdict for Genesis |
|---|---|---|
| 1. Authoritative gameplay state | A5 block 0x10C000..: actor blocks (0x2C8/0x508/0x5C8/0x748/0x8C8/0x11B2…), player fields (0x10E8 mode, 0x10C0 Y…), camera (0x10AE–0x10BA, 0x10EC/0x10EE), input latch/copy (0x16/0x137A), HP, wave/trigger fields, sound mailbox | **Keep exactly as-is** (already mapped to 0xFF0000; dozens of KFs depend on it) |
| 2. Gameplay-semantic side-effect state | **Collision map 0x10DE00–0x10FE00 (8KB)** produced by the BG pass; sprite-palette source buffer A5+0x1600; scroll staging fields | **Keep** — genuinely read by gameplay (KF-067). The collision map is the one big "video-derived" structure the arcade actually reads |
| 3. Persistent display state | scroll values, sprite_ctrl shadow (colbank/flip), palette bank contents, PC080SN ctrl (flip) | Keep as small shadows (words) |
| 4. Transient chip-formatted output | PC090OJ object RAM image, C-window tilemap words, palette RAM image | **Never read back** (except the two title glyph probes) → **does not need to exist as a chip-shaped mirror.** This is the category the current architecture spends most of its resources imitating |
| 5. Hardware control | PC090OJ ctrl 0xD01BFE, PC080SN ctrl 0xC50000, sprite_ctrl 0x380000 | Two shadow words + semantic handling (flip = whole-screen transform; already modeled) |
| 6. Write-only, never meaningfully read | everything in category 4, plus watchdog | Translate at the write site, discard the image |

The two title glyph probes (§1.2) are satisfied by keeping the **WRAM nametable ring** readable (the native design's plane staging is itself a readable RAM structure) — no VDP readback needed, ever. VDP readback on Genesis is slow (FIFO stalls, mode setup) and semantically unnecessary here; it is rejected as a state store.

---

## 3. What the current compatibility architecture costs (measured)

### 3.1 WRAM (static, from `symbol.txt` — `current_cost_static.txt`)
**32,370 bytes = 49.4% of the console's entire 64KB WRAM** in compatibility buffers, on top of the arcade's own ~16KB state + 8KB collision map:
- PC080SN staging: `staged_bg_tall_buffer` 8192 + `staged_fg_tall_buffer` 8192 + `staged_bg_buffer` 4096 + `staged_fg_buffer` 4096 = **24,576 B**
- PC090OJ: mirror 2048 + mirror_shadow 2048 + block2c8_scratch 800 + descriptor table 960 + SAT 640 + record_to_slot 256 + worklists/residency ~560 = **~7,300 B**
- palette/narrow/desc misc ≈ 500 B

### 3.2 The transformation chain (a lizard component pixel, today)
1. actor block (gameplay state) → 2. engine expansion into an 800-byte scratch (+ per-frame 99-record seed copy from the mirror + −8 alignment pass) → 3. `family_apply_record` compare+write into the **2KB chip-shaped mirror** + candidate bit → 4. VBlank shadow-compare of the whole 2KB mirror against a second 2KB copy → 5. candidate scan over 256 records → 6. decode (bank math, flip math, clip math) + represent (ordered-insert/evict engine with record→slot map) → 7. SAT staging write + residency check + tile-DMA worklist → 8. VBlank: SAT DMA + tile DMA.
**Eight stages, three full-buffer scans (2KB compare, 256-bit candidates, 80-slot SAT/residency), two whole-buffer copies (seed, shadow refresh) — every frame, mostly for records that did not change.** The PC080SN side is worse in bytes: 24KB of tall/wide staging rebuilt by projection passes, then strip-diffed into commits.

### 3.3 VBlank
The current `_vblank_service` (vdp_comm.s) runs: input scan → **vdp_prepare_sprites (stages 4–7 above)** → DISPLAY_OFF → tile commit → BG tall projection → BG strips → FG tall projection → FG narrow strips → sprite VRAM commit → DISPLAY_ON → two palette carriers → palette commit → scroll → arcade VINT. Measured duty across recent builds: DISPLAY_OFF windows of 0.33–0.4 of frame time (rates 0.60–0.67 "on"), i.e. **the commit pipeline regularly overruns the ~36-scanline VBlank into active display** — that is the user-visible **rolling black bar**, growing during scroll (more strips dirty). The display-off bracket exists *because* commits cannot fit in VBlank.

### 3.4 Why flicker/incomplete composites happen at only ~40–67 objects (<80)
- The represent engine caps at 80 records with **ascending-record-index eviction** (`.Lpc090oj_evict_tail`): under load, high-index records — the lizard composite groups at 140–238 — are evicted first *by index*, not by visual priority, so composite actors lose parts while HUD/terrain records survive.
- The engine consumes **8 SAT sprites per lizard** (8 × 16×16 records), so 4 lizards + Rastan(9) + terrain + record 46 ≈ 50+ sprites, hitting the per-scanline 20-sprite/320-px wall on the shared ground band before the 80 cap is near.
- Slot-addressed tile residency: a record that changes SAT slot forces a 128-byte pattern re-upload even for a resident code — animation + slot churn = tile-DMA saturation, and the worklist budget defers uploads → parts appear with stale/blank tiles (the "iteration-1 thin bars" class of defect).
- The 256-record mirror is required only because the arcade's *record indices* are load-bearing addresses in this design (player anchor 120/121 = KF-049; lizard span 140–238 = KF-067's 192-failure). **Record indices are an arcade chip artifact, not gameplay state** — the native design makes them irrelevant.

These defects are architectural: each was individually patched (KF-049/051/060–067), and each patch added more scanning/copying to the same per-frame pipeline.

---

## 4. Genesis VDP model relevant to the design

- **SAT:** 80 entries × 8 B = 640 B; H40 line budget: 20 sprites / 320 px per scanline. Sprites up to 32×32 px (4×4 tiles, column-major tile order). Link field controls priority order; link order ≠ table order.
- **DMA:** ~205 B/scanline during VBlank (H40); NTSC VBlank ≈ 36 lines ⇒ **≈ 7.2 KB/VBlank** practical 68k→VRAM DMA budget with display on during active (display-off extends but causes visible bars — to be *eliminated*, not relied on).
- CRAM 128 B (4×16), VSRAM 80 B. Full CRAM DMA ≈ 1 scanline.
- FIFO: 4 words; active-display writes stall — bulk work belongs in VBlank; *preparation* belongs in mainline. HBlank: usable only for tiny raster tricks; nothing in Rastan needs it (no per-line scroll in the arcade game).
- VRAM 64KB: plane A + plane B (2×8KB at 64×32) + SAT + hscroll ≈ 18.5KB, leaving **~45KB ≈ 350 16×16 sprite cells + stage tile set**.
- Tiles: 32 B/8×8; a PC090OJ 16×16 object = 4 tiles = 128 B (matches the existing preconverted `pc090oj_genesis.bin` packing).

**Frame-phase doctrine:** produce during mainline (the arcade main loop leaves large idle margins — it was designed for a 12MHz 68000 against dumb latches; the Genesis 7.67MHz deficit is offset by removing the entire imitation pipeline), commit during VBlank, keep display on always.

---

## 5. Rainbow Islands comparison (required)

Sources: the three prior project analyses (hashes above) + both disassemblies, spot-verified this task. The RI Genesis cart (524,288 B, `rainbow.zip` `1be5d55d…`) is usable; nothing is missing.

**Findings (verified in `Cody_rainbow_islands_vdp_template_analysis.md` and re-checked against `rainbow_islands_genesis.disasm.txt`):**
- RI-Genesis is a **from-scratch reimplementation**: no PC080SN/PC090OJ memory images anywhere in the ROM; the arcade program was not preserved.
- Its renderer is a **staged two-phase commit**: game logic in the main loop (active display) populates WRAM staging — a **shadow SAT in final Genesis format at 0xFFFFF800**, flag-gated tilemap strip buffers, palette buffer — and the VBlank ISR (0x380) is a short commit pipeline: CRAM DMA (0x85A), SAT DMA (0x6B0), strip commits (0x73C/0x1A70: 40-word row strips via control/data port), auxiliary streams (0x7BE), scroll. Display stays ON; VBlank work ≈ 3–5 ms.
- Composite objects are composed **directly into the shadow SAT** at build time by entity code — there is no intermediate record space, no candidate tracking, no representation engine, no slot maps. Sprite overload is handled by build order (priority-ordered emission; excess simply not emitted).
- Tilesets/stages load per-scene (stage-specific VRAM residency); scrolling commits strips as rows/columns cross boundaries (dirty-strip queue, not whole-plane rebuilds).
- Fidelity: RI-Genesis reduces some content vs arcade (fewer simultaneous effects, simplified rounds) — a *reimplementation liberty Rastan must NOT take*; but its **renderer shape** (final-format WRAM shadows + short VBlank commit) is exactly what a translation can adopt without touching gameplay.

**What transfers to Rastan:** the renderer shape — final-format shadow SAT, priority-ordered emission, dirty strip queues, per-scene residency, display-on VBlank commit. **What does not:** discarding the arcade program (forbidden by RULES.md §1–8 and unnecessary — §1 shows the arcade's own leaf-translator structure gives us the same clean boundary RI got by rewriting).

---

## 6. The native design

### 6.1 Principle
**Replace the ~30 hardware-facing leaf routines (§1.1–1.3) at their existing entry boundaries with Genesis-native emitters that write final-format WRAM shadows directly. Delete every chip-shaped intermediate.** Arcade gameplay code, actor state, collision map, camera, palettes-as-intent, timing, and the Level-5 VBlank identity remain untouched (RULES.md compliant: helpers called by arcade code, RTS back, no loops/ownership).

### 6.2 RAM structures (total ≈ 4.6 KB, replacing 32.4 KB)
| Structure | Size | Replaces |
|---|---|---|
| `shadow_sat[2]` — double-buffered final-format SAT, built in link order | 2×640 B | mirror(2048)+shadow(2048)+SAT stage(640)+record_to_slot(256)+descriptor(960)+scratch(800) |
| `sat_emit_cursor` (word) + per-frame sprite count | 4 B | candidate bitsets, represent engine, waiting bitsets |
| `plane_ring_a/b` — 64×30 nametable word rings (visible window + 2-column margin), readable (satisfies the title glyph probes) | 2×~3.8KB→ *(kept only if probes/partial redraws demand full rings; minimum: 2×160 B column strips)* | staged_bg/fg + tall buffers (24,576 B) |
| `dirty_cols` / `dirty_rows` queues | ~64 B | tall projection + strip diff scans |
| `cram_shadow` (64 words) + dirty flag | 130 B | staged_palette_words + carriers (carriers become per-scene ownership rows) |
| `vram_resident_map` — per-scene code→cell map (built from ROM tables at scene load) | 512 B–1 KB ROM-indexed + small RAM | sprite_tile_resident_code + worklists + per-slot churn |
| shadows: scroll(8B), sprite_ctrl(2B), flip(2B) | 12 B | same (kept) |

Worst case (full rings kept): ≈ 9.3 KB — still a **23 KB WRAM reduction**. Minimum variant: ≈ 4.6 KB (27.8 KB freed).

### 6.3 Sprite pipeline (all families)
Every PC090OJ producer in §1.1 becomes a native emitter with the same entry contract:
- **Emission order = arcade record order = priority order.** Emitters run in the arcade's own call sequence (HUD → blocks → player), appending to `shadow_sat[back]` with an incrementing cursor and links; first-80-wins truncation reproduces PC090OJ's own priority semantics under overload (and §6.4 makes overload rare).
- **The `0x3D054` engine is replaced once, for every family** — player, all enemies, bosses, projectiles, items, effects, frontend: it is the single shared composer, data-driven by per-code ROM layout tables. The native composer walks the *same ROM tables* (guaranteeing every not-yet-seen family and boss is covered — the data, not our observations, defines the workload) but emits Genesis SAT entries with: position (arcade coords + the established ±bias constants), size, flip (from ctrl shadows), palette line via the KF-066 route table, and tile index from the per-scene resident map.
- **Composite merging (stage-3 optimization):** the layout tables are rectangular grids of 16×16 cells. Adjacent cells in a column/2×2 block merge into 16×32/32×32 Genesis sprites (VRAM cells repacked column-major at preconversion time per composite frame). A lizard (2×4 cells) → 2 sprites instead of 8; Rastan (9 cells) → 3. Under the worst plausible load (boss + 6 enemies + projectiles ≈ 30 composite actors' worth of cells ≈ 120 cells), merging keeps total sprites ≈ 40–50 and per-scanline ≈ 8–12 of 20. **This is the flicker fix at its root.**
- Retirement is implicit: the back buffer starts empty each frame; whatever is not emitted does not exist. No eviction, no stale records, no "spurious sphere" class of defects (record 132's stale-lifetime family disappears by construction).
- **Blank-fill/off-screen semantics:** arcade writes Y=0x180 for inactive records; the native emitters simply *skip* emission (identical visible result, zero cost).

### 6.4 Tile residency
Per-scene **static residency**: at scene load (the existing scene_load boundary), a ROM-resident manifest — generated offline by walking the same animation/layout tables the engine uses — maps every sprite code the scene can display to a VRAM cell; scene load DMAs the base set (bounded: Stage-1 set ≈ 100–150 16×16 cells ≈ 13–19 KB, done across the scene-transition blackout, invisible). Per-frame uploads happen only for codes outside the manifest (rare animation overflow), through a small bounded queue. Slot-churn re-uploads vanish because residency is keyed by **code**, not by SAT slot.

### 6.5 Plane/terrain pipeline
- The gameplay BG/FG producer (`0x559B2` family) is replaced at its column boundary: for each streamed column it converts descriptor (tile,attr) pairs **directly to Genesis nametable words** (palette line via the route table, priority bit from the arcade attr) into the plane ring + pushes one dirty-column entry. The tall-buffer projections and whole-strip diffs are deleted.
- **The collision side-channel remains exactly as it is** (it is category-2 gameplay state) — with the KF-067 row-base defect fixed *here*, at the shared producer, together with a player-path re-tune (this design finally makes that safe to do because the visible planes and collision derive from one conversion point again, as on the arcade).
- Frontend/title/text writers (§1.2) emit nametable words directly into the ring at their existing hook boundaries (most already do a version of this — they lose only the intermediate buffers). The glyph probes read the ring.
- Scroll: `0x55AB4`'s four field-reads become two HSCROLL writes + two VSRAM writes at commit (the existing bias constants and the KF-015 conversions carry over unchanged).
- Destroyable terrain and animated tiles are descriptor mutations in the arcade data → they flow through the same column/cell dirty queue automatically.

### 6.6 Palette
Keep the KF-066 shape, simplified: palette hooks convert bank writes into `cram_shadow` lines via a per-scene ownership row of the route table (frontend and gameplay rows already exist; new scenes add rows, not code). One dirty flag; one ≤128 B CRAM DMA per dirty frame. The carrier/reassert machinery reduces to "ownership row selects destination; last write wins," because HUD suppression freed line 0 and scene rows are explicit.

### 6.7 Frame timeline (proposed)
**Mainline (arcade main loop, display active):** arcade gameplay tick (unchanged) → its calls into the leaf emitters build `shadow_sat[back]`, plane-ring columns, cram_shadow — pure WRAM writes, no VDP access, no scans.
**VBlank (arcade Level-5, unchanged identity):** input latch service → flip back/front → **SAT DMA (640 B)** → **dirty-column DMAs (typ. 0–4 cols × 64 B ≈ ≤256 B; scene bursts amortized)** → CRAM DMA if dirty (≤128 B) → 4 scroll writes → residency-overflow queue (bounded ≤2 cells = 256 B) → `jmp` arcade VINT chain. **Total ≈ 1.0–1.3 KB DMA + ~0.5 ms CPU — comfortably inside VBlank with the display ON.** The DISPLAY_OFF bracket is deleted ⇒ **the rolling black bar ceases to exist structurally.** HBlank: unused (nothing in the arcade program needs raster effects).
**Worst cases modeled:** boss + enemy wave (§6.3: ≈50 sprites, SAT DMA constant 640 B — load-independent); scene transition (full plane + tiles + palettes across the arcade's own multi-frame blackout — bounded by the transition length, as on arcade); palette flash effects (128 B); animated terrain (cell-dirty queue).
**Audio headroom:** mainline CPU freed ≈ the entire prepare/scan pipeline (stages 3–7 §3.2 ≈ multiple ms/frame) + VBlank freed ≈ 60–70% of its current use → Z80 driver feeding + PCM scheduling + the sound-mailbox translation (`FUN_00055CA2`'s 0x10FFFF commands) fit without touching video budgets.

### 6.8 What survives, what retires
**Survives untouched:** all gameplay fixes (KF-057/058/059 input & jump chains, TC0140SYT redirect, HUD-suppression option semantics, KF-066 route table concept, KF-067's map understanding, collision map, scene loader, boot, crash handler, sound scaffolding). **Retires:** mirror + shadow + candidates + represent engine + record_to_slot + block2c8 scratch/seed/−8 pass (the −8 moves into the one native composer as a Y-origin constant) + tall buffers + projections + strip diffing + per-slot residency + the 256-vs-192 question itself (mirror size ceases to be a concept — KF-048/049/067-192 sections become historical).

### 6.9 Read-after-write & compatibility proof obligations
- Sprite RAM: no reads exist (§1.1) — nothing to preserve.
- Tilemap: two title probes — served by the readable ring; verified at migration stage 2 by the title sequence itself.
- Palette: no gameplay reads — startup self-test targets arcade palette RAM, already handled by the existing boot path.
- Ctrl registers: shadows preserve current semantics (flip tested by the existing decode's flip math, which moves into the emitters).

---

## 7. Migration plan (playable builds, measurable, rollback-safe)

Every stage: MAME/original-arcade = authority; MAME/current-Genesis (Build 0218 rolling, `30a84f86…`) = baseline A/B; BlastEm + Exodus + Nomad acceptance by Tighe; arcade↔Genesis PCs resolved via the then-current `address_map.json` (hash recorded per stage). Rollback = numbered predecessor build (artifact rules apply; failures consume numbers as usual).

**Stage N1 — Native sprite pipeline (the architectural proof).**
Replace §1.1 emitters + the `0x3D054` composer with shadow-SAT emission; delete mirror/shadow/candidates/represent/record_to_slot/worklists; keep 1:1 16×16 sprites (no merging yet); keep current residency temporarily keyed by code. Arcade PCs: 0x41DAE/0x41F5E/0x45DFA/0x3B8B0/0x3B902/0x3AD72/0x52AA2/0x3D054-family/0x3AE28/0x3EEFA/0x3EF5C (Genesis addresses via address_map.json at implementation time).
*Measure:* VBlank duty, WRAM freed (~7 KB), flicker A/B at lizard load, represented-vs-visible parity, all §1.1 families incl. frontend. **This stage alone answers whether the thesis holds — it removes the most scan-heavy subsystem while planes still run on the old path.** Risk: composite ordering vs Rastan overlap conventions — validated frame-by-frame against arcade captures.
**Stage N2 — Native plane pipeline.** Replace the column producer + text writers; delete tall/staged buffers (24.5 KB freed); fix KF-067 row-base + player retune at the unified conversion point; title probes on the ring. Measure black-bar elimination (display-off bracket removal), scroll-streaming correctness across Stage 1→cave→sky transitions.
**Stage N3 — Composite merging + per-scene residency manifests.** Sprite-count collapse (8→2 per lizard), scene-load DMA bursts, offline manifest generation from ROM tables covering *all* stages/bosses. Measure per-scanline occupancy at worst waves, boss scenes (Stage-1 boss minimum; later stages as they become reachable).
**Stage N4 — Palette/scroll consolidation + deletion audit.** Route-table ownership rows per scene; remove carriers; verify zero remaining references to retired buffers; final resource report + audio-headroom re-measurement.
Stages N1–N2 must not keep both renderers alive: each stage deletes what it replaces (per this task's requirement; the per-stage numbered builds provide the rollback path instead of dual systems).

**Smallest traces still required (implementation-time, not design-blocking):** (a) MAME/original-arcade: per-frame SAT-order capture at Stage-1 wave + boss for emission-order validation (arcade ROM); (b) MAME/current-Genesis: baseline VBlank-duty numbers on the N1 predecessor build for the A/B (Genesis ROM). No Rainbow Islands runtime traces required — static analysis sufficed.

---

## 8. Risks
1. **Layout-table completeness** (bosses/late stages unseen): mitigated — the native composer consumes the same ROM tables the arcade engine does; offline manifest generation enumerates them exhaustively; per-stage validation gates.
2. **Emission-order vs overlap fidelity:** arcade record order is documented priority; validated per-frame vs arcade captures at N1.
3. **Scene-transition DMA bursts:** bounded by arcade's own blackout length; worst-case manifests sized in N3.
4. **KF-067 joint fix moves the player:** isolated to N2 with its own A/B and rollback build.
5. **Unclassified code regions:** any not-yet-hooked producer that writes chip space will fault visibly at N1/N2 (missing output, not corruption — chip writes become no-ops once regions unmap); the existing unmapped-access audit hooks catch them; hw_refs says the absolute surface is closed, and indirect writers all route through the replaced composer/producer entries.

---

## 9. Final recommendation (in my own terms)

The current system is an *emulator of two dead chips wedged between a live program and a live chip* — every frame it forges the PC090OJ's RAM image, then reverse-engineers its own forgery back out of chip format into Genesis format, with three full-buffer scans and half of WRAM as scratch. The measured surface (§1) shows the arcade program never needed the chip image at all: it expresses graphics intent through ~30 leaf calls whose inputs are pure gameplay semantics, and it never reads the chips back (two title-glyph probes aside).

**Recommendation: translate at the leaf-call boundary, emit final Genesis formats directly, and delete the chip images.** Keep every byte of arcade gameplay state, the collision map, the palette-intent routing, and the arcade's execution/VBlank ownership. Adopt the Rainbow Islands *renderer shape* (final-format WRAM shadows, priority-ordered emission, short display-on VBlank commit) without adopting its reimplementation liberties. Merge composite 16×16 cells into large Genesis sprites at the one shared composer.

**Answer to the mandate question: Yes.** The original Rastan graphics-facing code can be rewritten around the Genesis VDP at the boundaries the Ghidra surface identifies, producing arcade-faithful output with: ≈23–28 KB WRAM returned, VBlank reduced to a ~1.3 KB DMA + sub-millisecond commit (display permanently on → black bar structurally gone), sprite flicker eliminated at its two roots (count collapse + priority-ordered truncation), the 256/192 mirror dilemma dissolved, and enough mainline and VBlank headroom recovered to fund the entire audio system. The compromises that remain are the Genesis's own physical limits — 80 sprites/20-per-line (mitigated by merging to well under both at worst modeled load), 4 palette lines (already governed by the KF-066 route table), and plane sizes (already handled by the streaming model) — each documented above with its least-harmful translation.
