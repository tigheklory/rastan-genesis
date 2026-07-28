# Andy — Native PC080SN → YM7101 Current-State Handoff (research-only)

> **POLICY NOTICE (added 2026-07-28):** This document predates the canonical `docs/design/PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md` (and `RULES.md` §11). It is retained as an active design reference and **defers to that policy**: where anything here conflicts, the canonical policy governs. Any 'shadow', 'mirror', 'virtual name-RAM', 'tall buffer', or 'projection' referenced here is **transitional compatibility only, never the final architecture** — the target is `arcade semantic decision → native Genesis VDP/SAT`. Agents must state the semantic cut and the chip tail removed before implementing.


**Status:** ANALYSIS / HANDOFF ONLY. No production source, Makefile, spec, ROM, or build-counter changes. Self-contained: Cody can implement from this document alone.
**Date:** 2026-07-26 · **Baseline:** Build 0235 (assembly `rastan-direct` project).

---

## 1. Purpose and scope

Prepare the production handoff for replacing Rastan's **PC080SN-specific graphics execution** with **native Sega Genesis (Yamaha YM7101 / Sega 315-5313) VDP operations**, in the architectural sense that Rainbow Islands runs natively on the Mega Drive. The arcade 68000 program remains the execution and gameplay authority; only the device-specific graphics *tails* are replaced. Scope of the eventual implementation is the **PC080SN tilemap path** (tilemap0→Plane B, tilemap1→Plane A, scene-init, clear, scroll). PC090OJ is documented as a future rule only. This document ends with the complete Cody implementation/build prompt (§15).

## 2. Current authority order

1. Tighe's current instructions.
2. `RULES.md` (repo root — current non-negotiable rules).
3. `apps/rastan-direct/` source + `Makefile`.
4. `specs/rastan_direct_remap.json` + `build/rastan-direct/address_map.json`.
5. Canonical arcade reference `docs/arcade_reference/pc080sn/`.
6. Accepted Build 0235 (Genesis regression baseline).
7. Current native-Genesis design docs — only after confirming they describe `rastan-direct`.
8. Rainbow Islands Genesis + Sonic 1/2 as external native-graphics references.
9. `AGENTS_LOG.md`, old design reports, old memories — historical provenance only.

A statement is not current merely because it exists in the repo. Every operational/architectural claim must be confirmed from a higher current source.

## 3. Retired SGDK/C era vs current assembly era

- **RETIRED — SGDK/C era:** `apps/rastan/`, `main.c`, SGDK runtime ownership, 300-series builds (e.g. Build 311, `Rastan_311.bin`), `Rastan_NNN.bin` / manual filenames, C-window/name-RAM shadows, Genesis-owned main loops, SGDK hooks/bridges. Consult only for facts intrinsic to an external comparison ROM (e.g. Rainbow Islands). Must not describe the current implementation or build process.
- **CURRENT — assembly era:** `apps/rastan-direct/` with `apps/rastan-direct/src/*.s`, current remap specs + generated address map, Makefile-owned counter/naming, accepted Build 0235, arcade-owned execution + VBlank, **no C-window shadow**.

## 4. Verified current build workflow (from the live Makefile)

- Project: `apps/rastan-direct/`; source `apps/rastan-direct/src/*.s`.
- Default goal `all: $(BIN)`; `release: $(BIN)`; `BIN = dist/rastan_direct_video_test.bin`. The **`$(BIN)` recipe itself** performs patch → boot-guard → objdump → the numbered-artifact block. (`make` builds `all`→`$(BIN)`; `release` is an alias dependency — `make` does **not** call `make release`.)
- `NUMBERED_PREFIX = rastan_direct_video_test_build`; counter `build/rastan-direct/build_counter.txt`.
- Numbered block: the Makefile reads `build_counter.txt` as the **authoritative current counter**; it determines the highest consumed numbered build from existing dist artifacts and the consumed-build ledger; **if the counter is behind that consumed number, the build ABORTS with an error** (it does not silently raise or repair a stale counter); if consistent, the next tag is `counter + 1` (`printf %04d`). It **refuses to overwrite** an existing numbered artifact; runs the **canonical gate** (`CANONICAL_GATE` python: helper canonical SHA, spec, symbols, counter, numbered-name, bookmark state); copies `$(BIN) → dist/rastan-direct/rastan_direct_video_test_build_NNNN.bin`; advances the counter; then runs a **mandatory ~30s MAME Genesis trace** (`tools/mame/run_genesis_trace_wsl.sh … -seconds_to_run 30`) into `states/traces/…`.
- Prior numbered artifacts remain consumed and preserved (0236/0238 rejected; 0237 = preserved accidental dup of 0235).
- Cody runs the normal Makefile and reports the artifact **exactly as generated** — no manual number, no filename, no rename, no reuse. `Rastan_NNN.bin` is retired and must never appear.

## 5. Verified fixed Genesis VDP architecture (from `apps/rastan-direct/src/vdp_comm.s`)

- **Plane B: 64×32 at VRAM 0xC000** (reg4 = 0x06). Genesis target of arcade tilemap0 (BG).
- **Plane A: 64×32 at VRAM 0xE000** (reg2 = 0x38). Genesis target of arcade tilemap1 (FG).
- **SAT: 0xF800** (reg5 = 0x7C). **H-scroll: 0xFC00** (reg13 = 0x3F, `VRAM_HSCROLL_BASE`).
- **VDP register 16 (plane size) = 0x01** → 64×32. Do not use 0x11 / 64×64.
- Arcade code owns execution; arcade VBlank is the **sole** frame authority; Genesis VBlank performs bounded VDP/DMA service only (RULES.md §1–§3).
- **No active-display VDP writes.** Init sets Mode2 display-OFF then enables — this is **initialization only**, NOT an ongoing display-disable rendering system. Do not add display-disable bracketing.
- Collision remains an arcade-owned WRAM channel (0x10DE00).

## 6. Verified PC080SN readback treatment (from `specs/rastan_direct_remap.json`)

The three name-RAM compare-reads are **bypassed by branch-patch**, not stored:

| arcade_pc | original | replacement | note |
|---|---|---|---|
| 0x03A47E | `cmp #0x49,0xC0883A; bne …` | `bra +0x10` + NOPs | read from 0xC0883A invalid on Genesis |
| 0x03A552 | `cmp #0x30,0xC09EA3; bne …` | `bra +0x10` + NOPs | read from 0xC09EA3 invalid on Genesis |
| 0x03AC54 | `cmp #0x43,0xC09E87; bne …` | `bra +0x12` + NOPs | readback crash site |

Therefore: they **do not require C-window storage**; they **do not justify a generic name-RAM mirror**; the existing accepted Build 0235 treatment is **preserved unchanged**. The NOP bytes inside these already-established remaps are **historical accepted code — not authorization to add new NOP filler** anywhere.

## 7. Historical-contamination audit

| Item | Source/era | Current status | Current replacement rule | Action |
|---|---|---|---|---|
| `apps/rastan/` | SGDK/C era | RETIRED | current project is `apps/rastan-direct/` | HISTORY ONLY |
| SGDK | SGDK/C era | RETIRED | assembly-only, no SGDK runtime | HISTORY ONLY |
| Build 0033 | SGDK-era analysis | HISTORY ONLY | baseline is Build 0235 | HISTORY ONLY |
| Build 311 | SGDK-era build | RETIRED | numbered assembly builds (02xx) | HISTORY ONLY |
| `Rastan_NNN.bin` | SGDK-era naming | RETIRED | Makefile auto-names `rastan_direct_video_test_build_NNNN.bin` | REMOVE |
| manual artifact naming | SGDK-era | RETIRED | Makefile owns naming | REMOVE |
| manually selected build numbers | old prompts | RETIRED | Makefile counter+ledger auto-increment | REMOVE |
| C-window shadows | SGDK-era | RETIRED | no shadow; readback branch-patched (§6) | REMOVE |
| generic arcade name-RAM mirrors | old translation model | RETIRED | native producers; no mirror | REMOVE |
| 64×64 VDP plane mode | rejected 0236/0238 | RETIRED | fixed 64×32 (reg16=0x01) | REMOVE |
| VDP register 16 = 0x11 | rejected 64×64 attempt | RETIRED | reg16 = 0x01 | REMOVE |
| SAT/H-scroll relocation | hypothetical | RETIRED | SAT 0xF800 / HSCROLL 0xFC00 fixed | REMOVE |
| display-disable bracketing | RI technique / old idea | RETIRED (as ongoing system) | init display-off only; no ongoing bracketing | REMOVE |
| Genesis-owned main loop | SGDK-era | RETIRED | RULES.md: arcade owns execution | REMOVE |
| Genesis frame wait/scheduler | SGDK-era | RETIRED | arcade VBlank sole authority | REMOVE |
| old four-quadrant PC080SN model | old reference | HISTORY ONLY | 2 tilemaps + 2 rowscroll regions (canonical ref) | HISTORY ONLY |
| old BG/FG assignments | old reference | HISTORY ONLY | tilemap0→Plane B (BG); tilemap1→Plane A (FG) | HISTORY ONLY |
| old descriptor-table addresses (0x10D1C0/0x10D200) | old slip | RETIRED | 0x10D000 / 0x10D040 / 0x10D080 | HISTORY ONLY |
| indiscriminate row `&31` folding | current translation layer | TEMPORARY SCAFFOLDING | native entering-edge; never modulo-fold rows 32–63 | AUDIT THEN RETIRE |
| tall-buffer projection | current translation layer | TEMPORARY SCAFFOLDING | native producers regenerate entering edges | AUDIT THEN RETIRE |
| arbitrary-address PC080SN hooks | current translation layer | TEMPORARY SCAFFOLDING | boundary-level native producers | AUDIT THEN RETIRE |
| PC090OJ emulation-layer assumptions | future sprite work | HISTORY ONLY | future: native SAT at producer boundary | OUT OF SCOPE (this build) |
| feature-flag renderers | prohibited pattern | RETIRED | single production path | REMOVE |
| old mandatory issue-ledger rituals | old prompts | RETIRED | update a ledger only if work changes an issue's status | REMOVE |

## 8. Rainbow Islands native-Genesis findings

Confirmed from the on-disk RI Genesis disassembly + prior comparative reports (RI-intrinsic facts only; ignore those reports' *Rastan* specifics — they describe the retired `apps/rastan/` port):

- Full **native** VDP realization — no PC080SN/PC090OJ emulation, no virtual name-RAM, **no full-plane display shadow**.
- Two-phase: producers populate **WRAM staging** (SAT, tilemap source/dest/flag, scroll, palette); VBlank commits via DMA/direct writes.
- Tilemap committed as **rows/strips** (flag-triggered, source/dest advanced per strip) — never a whole-plane rewrite.
- Scroll staged in WRAM → VSRAM. SAT staged → DMA.

RI supplies the **native-realization philosophy** only. It does **not** give Rastan a main loop, scheduler, display-disable ownership, its WRAM layout, its transfer scheduling, or its build conventions.

## 9. Sonic 1 and Sonic 2 entering-edge findings

Confirmed verbatim from `sonicretro/s1disasm` `_inc/Level Drawing (REV00).asm` and `sonicretro/s2disasm` `s2.asm`:

**Sonic 1:** `LoadTilesFromStart`→`DrawChunks` draws the full resident window once per plane at load. `LoadTilesAsYouMove` reads independent FG/BG flag bytes; `tst.b (a2); beq return` → **no work when no edge flag is set**; `bclr` per edge. Vertical camera crossing → **`DrawBlocks_LR`** = entering **horizontal row**; horizontal camera crossing → **`DrawBlocks_TB`** = entering **vertical column** (the disasm warns not to be fooled by the names). `Calc_VRAM_Pos`: `+camera Y/X; andi.w #$F0,d4; andi.w #$1F0,d5; lsl.w #4,d4; lsr.w #2,d5; add` → fold into a VDP command — direct world→wrapped-plane-cell, no shadow. Unchanged cells receive no conversion/copy.

**Sonic 2:** refinements — camera-state snapshots (`Camera_RAM_copy`, `Scroll_flags_copy`) for reliable per-edge detection; per-plane name-table wrap addressing (`planeLoc`); bounded DMA command queue (`QueueDMATransfer`/`ProcessDMAQueue`); independent plane handling.

Techniques only. Do **not** copy Sonic's 16×16 block format, map structures, camera flags, main loop, plane bases, or build a new Genesis map engine. Rastan already owns its arcade map-stream, descriptors, ring, direction, and collision systems.

## 10. Current Rastan PC080SN arcade facts (authority: `docs/arcade_reference/pc080sn/`)

- **tilemap0:** 0xC00000–0xC03FFF; 64×64; opaque **background**; Genesis **Plane B**; scene-filled and **streamed vertically during gameplay via 0x055B8E**; independent arcade scroll (half-rate parallax X via 0x055B92); **no collision** channel.
- **tilemap1:** 0xC08000–0xC0BFFF; 64×64; transparent **foreground/playfield**; Genesis **Plane A**; independently scrolled (full-rate); **collision** published to 0x10DE00.
- Cells are 4 bytes: word0 = attribute (bits0–8 color, bit14 X-flip, bit15 Y-flip; streamed 0x0003 / clear 0x0000); word1 = tile code (bits0–13).
- Gameplay publication, ring counters (a5@0x10CA/0x10CC), map selection, descriptors (0x10D000/0x10D040/0x10D080; tilemap0 0x10D100/0x10D104), direction selectors, and publication timing are **arcade-owned**.
- Arcade PC080SN writes may occur during active display on the arcade; on Genesis the work must be staged and committed through the existing arcade-owned VBlank path.

Do not recover arcade facts from Genesis buffers or historical design reports. **Plane B (tilemap0) gameplay tile publication is vertical streaming — do not invent a horizontal tilemap0 publisher.**

## 11. Native replacement-boundary comparison (Cody must complete with proof)

The objective is the **earliest safe boundary that removes the largest complete block of PC080SN-specific execution** while preserving required arcade side effects — not merely replacing each final `MOV.W`.

**Tilemap1 candidates to compare:** 0x055948 (publication dispatch; owns ring `a5@0x10CA++` + post-advance 0x0558A2), 0x055968 (strip_A producer), 0x055990 (strip_B producer), 0x0559B2 (forward cell producer), 0x055A14 (direction-aware cell producer + collision store 0x055A62).

**Tilemap0 candidates to compare:** 0x055B8E (gameplay caller + trigger), 0x055C4A (producer; cursor bookkeeping a5@0x10FC→a5@0x1126, `addq #1,a5@0x10F6`, calls 0x55BEC), 0x055C5E (setup), 0x055C7A (64-cell name-RAM body).

For each candidate Cody must document: register contract, stack contract, return address, descriptor/source progression, ring progression, direction reversal, collision side effects, current Genesis runtime mapping (via `address_map.json`), and removed PC080SN cycle cost — and whether it removes whole loops or single stores.

## 12. Preferred implementation boundaries (candidates — not final until contract-proven)

- **Preferred tilemap1 candidate boundaries: 0x055968 and 0x055990** (strip/publication level). Rationale: each produces one full entering strip (column for sel-0 via strip_A/+0x100 stride; row for sel-1/2 via strip_B/+4 stride) and removing it bypasses the entire 16×cell name-RAM walk while the ring counters (0x055948/0x0558A2), descriptor rebuild (0x055904), and source advance (0x0558C6) remain arcade-owned. Required to preserve: collision publication (0x10DE00 formula, tile from descriptor) and strip_B direction reversal (notw sub-index when selector≠2). Use the per-cell boundary (0x0559B2/0x055A14) only if the strip contract cannot be honored — with a stated reason.
- **Preferred tilemap0 candidate boundary: the highest safe boundary within 0x055C4A / 0x055C5E / 0x055C7A** that preserves the required bookkeeping (0x055C4A cursor/column advance) and removes the complete PC080SN destination walk (0x055C5E→0x055C7A). Keep the 0x055B8E vertical trigger and the half-rate parallax scroll.

**Final boundary selection requires the §11 contract proof.** Cody chooses; this document only ranks candidates.

## 13. Translation-scaffolding audit requirements

Do **not** assume this build removes every buffer/projector/dispatch/helper. For each existing item Cody classifies it as: **superseded by this build and safe to remove** / **still used by an unconverted producer** / **frontend-only, out of scope** / **required minimal native staging** / **already dead**.

Audit at minimum: `staged_bg_tall_buffer`, `staged_fg_tall_buffer`, `vdp_project_bg_tall_if_dirty`, `vdp_project_fg_tall_if_dirty`, `bg_tall_project_base`, `fg_tall_project_base`, `staged_bg_buffer`, `staged_fg_buffer`, generic PC080SN range dispatch, legacy 32-row folding helpers, scene-fill helpers, frontend text/block writers, item-page producers.

**Rule:** do not remove or bypass an existing structure until every live producer AND consumer relying on it has either a proven native replacement or an explicit out-of-scope compatibility path that remains intact. Retire PC080SN translation scaffolding **without** breaking frontend or unconverted producers.

**Cache rule:** prefer **regeneration of the entering edge directly from the arcade map source, descriptor state, ring state, and scroll state at the arcade publication event.** A retained cache is allowed only if Cody proves: (1) a required value cannot be regenerated at the entering-edge event; (2) the exact producer that depends on it; (3) the minimum dimensions/fields; (4) why it is not a virtual PC080SN name-RAM. Do **not** prescribe a 64×64 translated shadow, an arcade-format name-RAM mirror, or retaining non-resident converted cells by default.

## 14. Performance requirements

Require current-vs-proposed counts (measured or defensible static): arcade instructions bypassed; helper calls per publication; address-range classifications per publication; tile conversions per entering edge (horizontal vs vertical); staging words; VBlank transfer words; full-window projection calls during ordinary scrolling (target 0); estimated/measured 68000 cycles. Expected steady state: horizontal crossing = one entering column; vertical crossing = one entering row; sub-tile movement = scroll staging only; unchanged cells = no conversion/copy; no generic per-cell PC080SN range dispatch; no duplicate conversion. Visual parity alone is not completion.

## 15. Complete Cody implementation/build prompt

> **[Cody — Native YM7101 realization of Rastan PC080SN; retire the translation/projection layer]**
>
> **Authority order:** this prompt → `RULES.md` → `apps/rastan-direct/` source + Makefile → `specs/rastan_direct_remap.json` + `build/rastan-direct/address_map.json` → `docs/arcade_reference/pc080sn/` → Build 0235 baseline. Old AGENTS_LOG/design reports are historical provenance only; confirm every claim against a higher current source.
>
> **Baseline (re-confirm before editing):** confirm that the production paths `apps/rastan-direct/src/` and `apps/rastan-direct/Makefile` match the accepted **Build 0235** production baseline. Documentation-only changes outside those production paths (including this handoff and its AGENTS_LOG entry) are expected and are **not** a baseline failure — the STOP condition applies only to **production-source** divergence from Build 0235. Reference artifact `dist/rastan-direct/rastan_direct_video_test_build_0235.bin` SHA-256 `9aff0b11fb9a2151186ef0c03654fdd968d630a3cab45801be85de6f62571ad5`; counter 238; 0236/0238 rejected, 0237 preserved dup. Preserve all numbered artifacts; never reuse a number.
>
> **Goal:** make Rastan's graphics native (Rainbow-Islands sense): the arcade 68000 stays authoritative for gameplay/map/camera/scroll/collision/timing; the PC080SN device-specific tail is replaced by native VDP producers. Steady state: `arcade decision → native Genesis producer → bounded final-format staging → arcade-owned VBlank commit`. No PC080SN emulation, no virtual/arcade-format name-RAM, no C-window shadow, no full-window projection during ordinary gameplay scrolling (see the scope clause below — this does not mandate removing frontend/unconverted projection paths).
>
> **Fixed VDP layout (verified — do not change):** reg16 = 0x01 (64×32); Plane B = 0xC000 (arcade tilemap0/BG), Plane A = 0xE000 (arcade tilemap1/FG), SAT = 0xF800, HSCROLL = 0xFC00. No 64×64 mode, no reg16 = 0x11, no SAT/HSCROLL relocation.
>
> **Hard rules (RULES.md):** no Genesis main loop/scheduler/scene-machine/map-parser; arcade VBlank is the only frame authority; Genesis services bounded VDP/DMA only; no active-display VDP writes; the init display-off is initialization only — do NOT add an ongoing display-disable bracketing system; no feature-flag/alternate renderer; every added line ships; no NOP/RTS filler without disclosed permission (existing remap NOPs are accepted history, not license); do not reinterpret selectors in Genesis code; do not touch PC090OJ, palette, HUD, score, input, or the Build-0235 code-zero decoder pretest.
>
> **Phase 1 — audit & boundary proof (report first, using `address_map.json`):** For the tilemap1 candidates {0x055948, 0x055968, 0x055990, 0x0559B2, 0x055A14} and tilemap0 candidates {0x055B8E, 0x055C4A, 0x055C5E, 0x055C7A}, document for each: semantic work above (keep), PC080SN work below (bypass), register/stack contract, return address, descriptor/source progression, ring progression, direction reversal, collision side effects, Genesis runtime mapping, and removed cycle cost. **Preferred candidates:** tilemap1 = 0x055968 / 0x055990 (strip level); tilemap0 = the highest safe boundary within 0x055C4A/0x055C5E/0x055C7A that keeps 0x055C4A bookkeeping and removes the 0x055C5E→0x055C7A walk. **Select the final boundary only after proving the contract; if the preferred boundary cannot preserve a required side effect, drop to the per-cell boundary and state exactly why.** Also classify every scaffolding item (`staged_bg/fg_tall_buffer`, `vdp_project_bg/fg_tall_if_dirty`, `bg/fg_tall_project_base`, `staged_bg/fg_buffer`, generic range dispatch, 32-row folding helpers, scene-fill helpers, frontend text/block writers, item-page producers) as: superseded-safe-to-remove / still-used-by-unconverted-producer / frontend-only-out-of-scope / required-native-staging / already-dead. **Do not remove or bypass any structure until every live producer AND consumer has a proven native replacement or an intact out-of-scope compatibility path.**
>
> STOP (report, exact symbols/ranges) if: **production source (`apps/rastan-direct/src/` + `apps/rastan-direct/Makefile`) diverges from Build 0235** (documentation-only changes elsewhere are expected and are not a failure); a required routine won't map through `address_map.json`; retiring a structure would break a frontend/unconverted producer with no compat path; a boundary contract can't be honored without violating a hard rule; canonical arcade references materially contradict each other; or the readback treatment can't be found.
>
> **Retain (arcade semantic):** 0x055948 dispatch + 0x0558A2 ring advance + 0x0558E0 segment step + 0x055904/0x0502CC descriptor/source selection; direction dispatcher; camera accumulators; collision formula → 0x10DE00; scroll computation; arcade VBlank ownership; the readback branch-patches for 0x03A47E/0x03A552/0x03AC54 (do not add any shadow/mirror).
>
> **Replace (native), independently per plane:**
> - **Tilemap1 / Plane A (0xE000):** at the proven boundary (preferred 0x055968 → entering **column**, 0x055990 → entering **row**). Derive logical (row,col) from `(dest − 0xC08000)/4`; convert tile+attr once (word0 bits0–8 color, bit14 Xflip, bit15 Yflip; word1 bits0–13 code) via the existing LUT to a Plane A name word at a `Calc_VRAM_Pos`-style wrapped cell (`andi` masks for the 64×32 plane); **reproduce the collision store** and strip_B direction reversal (notw when selector≠2). Prefer regenerating the entering edge from arcade source/descriptor/ring/scroll at the publication event; keep a cache only under the cache rule below.
> - **Tilemap0 / Plane B (0xC000):** at the proven boundary within 0x055C4A/0x055C5E/0x055C7A, generate the entering Plane B edge natively from the tilemap0 source (a5@0x10FC, tables 0x10D100/0x10D104). **Gameplay tilemap0 publication is vertical streaming (0x055B8E) — produce the entering row on the vertical trigger; do not invent a horizontal tilemap0 tile publisher.** Keep 0x055B8E trigger + half-rate parallax scroll (0x055B92). No collision.
> - **Scene-init (0x0503DC):** DO NOT replace the 64-iteration fill merely because a native 64×32 draw reproduces the visible result. Before bypassing any part of the loop, enumerate and preserve **every** side effect: tilemap1 collision-map initialization; ring-counter progression (a5@0x10CA/0x10CC); descriptor + source-pointer progression; selector/map-stream state; tilemap0 producer bookkeeping; any state expected after the loop returns; and the register/stack results the caller expects. The native scene-init must **separate**: (1) arcade semantic/state initialization that remains authoritative; (2) collision or other WRAM initialization that must still occur; (3) PC080SN visual name-RAM work that may be replaced; (4) native Plane A and Plane B initial resident draws (Sonic `DrawChunks` style, from arcade source + scroll, bounded VBlank commit). A **visible-only replacement is not permitted.** If reproducing the required side effects would require recreating a Genesis-owned map engine or guessing state progression, STOP with exact evidence. Not a Genesis scene manager.
> - **Clear (0x0561B6):** native resident-plane/cache clear to `clear_fill_tile_0x0020` (word0=0x0000/word1=0x0020 → converted word); overwrite resident + any cached cells; never skipped as "blank".
> - **Scroll (0x055AB4):** keep the four arcade scroll values; stage Plane B X/Y + Plane A X/Y natively → VSRAM/HSCROLL on the arcade VBlank; independent per-plane origins (Plane B half-rate, Plane A full-rate). No PC080SN register emulation.
>
> **Entering-edge rules (two-level logical/physical model — mandatory):**
> - Arcade logical rows are a **64-row ring (0–63, wrapping 63→0)**.
> - Each Genesis plane is a **32-row physical resident window (physical rows 0–31)**.
> - Plane A and Plane B have **independently derived logical resident origins** (from their own arcade scroll fields).
> - A logical write may update a physical VDP row **only after proving the logical row is currently resident** (within its plane's resident origin..origin+31 window).
> - Physical-row selection may wrap within 0–31 **only relative to the proven resident origin**. **Blind `logical_row & 31` mapping is FORBIDDEN.**
> - When a physical row is (re)assigned to a newly entering logical row, **all 64 cells must be replaced before commit** (no stale cells from the previous logical row).
> - Non-resident visual writes are **regenerated from arcade source state when they enter**, unless Cody proves the minimum necessary cache under the cache rule.
> - Horizontal crossing → entering column only; vertical crossing → entering row only. Unchanged cells untouched. Full-window rebuild only on an arcade scene-init/clear/restore call.
> - Cody must **state and verify the exact `logical_row → resident-test → physical_row` equation for each plane independently.**
>
> **Cache rule:** prefer regeneration from arcade state at the entering-edge event. A retained cache is allowed only if you prove (1) a value that cannot be regenerated at the event, (2) the exact dependent producer, (3) minimum dimensions/fields, (4) why it is not a virtual name-RAM. Do not add a 64×64 shadow or an arcade-format name-RAM mirror, and do not retain non-resident converted cells by default.
>
> **Performance (report):** arcade instructions bypassed; current vs proposed helper-calls/publication; PC080SN range classifications/publication (target 0); tile conversions per horizontal vs vertical edge; staging words; VBlank transfer words; full-window projections during ordinary scroll (target 0); estimated/measured 68000 cycles. Targets: horizontal = 1 column, vertical = 1 row, sub-tile = scroll only, unchanged = 0, no per-cell range dispatch, no duplicate conversion.
>
> **Scope of the "no projection" target (do not over-apply):** these are the **gameplay steady-state** targets — no full 64×32 projection *during ordinary gameplay scrolling*, no generic PC080SN range dispatch *in the converted gameplay producers*, only entering-edge work + scroll staging. This does **NOT** require immediately removing a projector or compatibility path still used by a frontend, text, item-page, or other unconverted producer. Every removal still requires the complete producer-AND-consumer audit (Phase 1 / §13); leave intact anything a live unconverted/frontend producer still depends on.
>
> **Required implementation document (mandatory, not optional):** create `docs/design/Cody_pc080sn_native_ym7101_boundary_implementation.md` containing: final tilemap1 boundary + proof; final tilemap0 boundary + proof; register/stack/return contracts; arcade semantic work retained; PC080SN-specific instructions bypassed; collision and ring/source/descriptor side effects preserved; resident-window mapping (the per-plane logical→physical equations); scene-init side-effect treatment; scaffolding retained vs retired; current-vs-native cycle/work counts; build + runtime verification. Also add one concise AGENTS_LOG completion entry. Touch an issue ledger only if this work changes an issue's status — no mandatory OPEN_ISSUES entry, no "Open/Closed Issues Impact" section, no duplicate RI/Sonic research docs.
>
> **Build & test:** run the normal Makefile (`make`; default `all`→`$(BIN)`, whose recipe auto-numbers via the counter + consumed-ledger, runs the canonical gate, copies to `dist/rastan-direct/rastan_direct_video_test_build_NNNN.bin`, and runs the ~30s MAME Genesis trace). **Report the generated artifact exactly as produced (path, SHA-256, size, counter) — do not prescribe, override, rename, reuse, or normalize the number/filename.** The canonical gate + trace must pass. Then compare in MAME Genesis vs MAME arcade Rastan World Rev 1 and vs Build 0235: boot → Stage 1 → move far enough to force repeated publications and physical-row reuse; verify no 0236/0238-style corruption, Plane B parallax BG / Plane A playfield, no stale rows / no 32-row fold, playable collision, no new crash/watchdog, unchanged sprites/HUD/palette/score/audio. If a natural save state reaches a vertical scene, verify one vertical entering-row transition; else static-verify the vertical path and say so.
>
> **PC090OJ:** not modified this build. Future rule: replace the object-RAM tail at the highest safe producer boundary with native SAT generation, retaining actor lifecycle/anim/pos/priority/flip/palette; no generic PC090OJ software device as the final architecture.
>
> **Required Cody final response (use this exact structure):**
>
> ```
> [Cody — Native YM7101 PC080SN Implementation]
>
> Accepted Build 0235 source confirmed:
> Required implementation document:
> Tilemap1 candidates compared:
> Selected tilemap1 boundary:
> Tilemap1 contract proof:
> Tilemap0 candidates compared:
> Selected tilemap0 boundary:
> Tilemap0 contract proof:
> Scene-init arcade side effects:
> Scene-init visual replacement:
> Collision initialization preserved:
> Logical-to-physical Plane A row mapping:
> Logical-to-physical Plane B row mapping:
> Horizontal entering-column path:
> Vertical entering-row path:
> Native clear path:
> Native scroll path:
> Arcade semantic code retained:
> PC080SN-specific code bypassed:
> Current scaffolding removed:
> Current scaffolding retained:
> Frontend/unconverted compatibility paths:
> Helper calls before/after:
> Address classifications before/after:
> Tile conversions per edge:
> Ordinary-scroll projection calls:
> VBlank transfer cost:
> Estimated or measured cycle change:
> Files changed:
> Candidate ROM:
> SHA-256:
> ROM size:
> Build counter:
> Canonical gate:
> Automatic MAME trace:
> MAME Genesis gameplay result:
> MAME arcade comparison:
> Build 0235 regression comparison:
> Known untested behavior:
> Architecture rules preserved:
> Checkpoint complete: YES/NO
> ```

## 16. Unresolved decisions and STOP conditions

**Unresolved (Cody decides with proof):** exact final tilemap1 boundary (strip 0x055968/0x055990 vs cell 0x0559B2/0x055A14); exact final tilemap0 boundary within 0x055C4A/0x055C5E/0x055C7A; whether any minimal cache is justified (default: none); which scaffolding items are removable now vs still needed by unconverted/frontend producers.

**STOP conditions (this research pass):** current source contradicts the 64×32 VRAM layout; the Makefile does not own numbering/naming; Build 0235 baseline unidentifiable; a required arcade routine unmappable through the address map; canonical references materially contradict; readback treatment not found; or RULES.md requires an architecture conflicting with this directive. **None triggered** — all verified consistent.

## 17. Compliance

Research/documentation only. No production source, Makefile, spec, ROM, or build-counter changes. Issue ledgers untouched. SGDK-era assumptions quarantined (§7). The complete Cody prompt is embedded in §15.
