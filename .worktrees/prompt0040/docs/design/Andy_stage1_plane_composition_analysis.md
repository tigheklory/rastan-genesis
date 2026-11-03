# Andy — Stage 1 Plane Composition Analysis: BG Correct, FG Plane Missing (Outcome E, bounded stop, no build)

**Agent:** Andy (temporary implementation/runtime-evidence role). **Type:** evidence-only analysis.
**No source, no JSON, no ROM, no build.**
**Baseline:** `rastan-direct-proposal` @ `5346934` (Build 0154 accepted). Build 0154 ROM
`69bd306e1998e892f5fbf451d17e5657d82f7565cacc7c462d2c5b02b3fabfd8`, counter 154. Working tree clean.
**Evidence dir:** `states/traces/build_0155_stage1_plane_composition/`.

## Outcome
**Outcome E — required FG plane population is missing; bounded stop.** Build 0154's **BG plane is proven
correct**; the malformed Stage 1 display is dominated by the **PC080SN FG plane (Genesis Plane A) not being
populated**, plus a static BG X-scroll. The FG is produced by a **different, more complex arcade producer**
(`0x0559B2`) whose source-column semantics are **not yet decoded**, so a faithful bounded FG pipeline cannot be
committed this round. No numbered build was produced.

## Decoded descriptor sequence (Phase 2)
The BG descriptor table (arcade `0x3951C`, Genesis `0x3971C`) is **56 six-byte entries** `{attr16=0x0002,
src32}`. Each entry paints **16 columns × 64 rows** from one of **five 0x800-byte source blocks**
`A=0xD11C, B=0xD91C, C=0xE11C, D=0xE91C, E=0xF11C`. The ordered block sequence (col groups of 16) is:
```
col0-15  : A B E E A C A B C E D D A B B B
col16-31 : C A C A B E E C A C A C D A E E
col32-47 : A B C D A B C D A B C D A B A B
col48-63 : A B A B A B A B
```
The **initial 64-column screen uses descriptors 0-3 = A,B,E,E** (16 cols each). 56 entries exist because the
table encodes the **whole horizontally-scrolling level's column→block map** (56×16 = 896 scroll columns), not
just the initial screen. Each entry selects one 0x800 block; screen column `c` reads block-column `c mod 16`.

## BG plane is CORRECT (Phase 3/4 — not the primary defect)
Arcade BG C-window at Stage 1 entry (`arc_plane.txt`, `arc_full.txt`): fully populated **64×64**, every cell
`{attr=0x0002, code}`. Genesis Build 0154 (`gen_state.txt`): `staged_bg_buffer` = **2048/2048 nonzero, 277
distinct**; staged row 0 = `0x41F6…` = `LUT[arcade 0x04A6]` + priority = **arcade row 0** (verified cell-level).
- The Genesis BG plane is **64×32** (`VDP_REG_PLANESIZE=0x01`) and `genesistan_hook_tilemap_bg_fill`'s window
  guard (`ARCADE_PC080SN_CWINDOW_BYTES=0x4000`, but the row derivation masks `&0x1F`) makes the producer stage
  **arcade rows 0-31** (rows 32-63 land at `A0 ≥ 0xC02000` and are handled so rows 0-31 survive). This matches
  the arcade's initial visible window: **BG Y-scroll = 0** (arcade `scrollA`/`scrollB` = 0 at entry), visible
  area = rows 0-27. So the staged BG top rows are the correct visible content.
- **Conclusion:** the BG staging/coordinates/codes are faithful for the initial frame. No BG cell-mapping fix is
  warranted (contradicting an Outcome A/B/C hypothesis for BG).

## FG plane is MISSING (the primary defect, Outcome E)
Arcade FG C-window (Plane-A equivalent, `0xC08000`) at Stage 1 entry: **fully populated 64×64**. FG row 0 =
`41C 41D 41E 434 020 020 020 …` — a mostly-uniform tile `0x020` with **sparse foreground features**
(`0x41C-0x41E`, `0x434…`). Only **17 distinct FG codes**; **12 mapped by the current LUT, 5 unmapped**
(`0x020, 0x434, 0x435, 0x436, 0x437`).

Genesis Build 0154 (`gen_state.txt`): `staged_fg_buffer` = **76/2048 nonzero** (sparse `0x60DA` stray values) —
the Stage 1 FG plane is **not produced**. So on hardware Plane A carries stale/empty content over the correct
Plane B, which is the dominant cause of the reported malformed upper band / black-with-blue rectangles.

### The arcade FG producer (source-column semantics NOT yet decoded)
At Stage 1 setup (`2/2/4`, `arc_fg.txt`) the FG C-window is written by **arcade `0x0559B8`/`0x055A06`** inside
loop `0x0559B2`, with `A1=0x10D080` (attr source, work-RAM), `A2=0x0020FC` (FG code source, low ROM),
`A3=0x10D040`, `A4=0x03951C` (shares the BG descriptor walker), `D2` = row counter, **loop bound 4 rows**
(`cmpi.w #4,d2`), column-indexed by `a5@(0x10CA)`. This is **structurally different** from the BG strip
producer (16×64 blocks): it is a **4-row strip writer** with a per-column source computation (`a2@(20 + …)` /
`a2@(0 + …)` with a `0xFF` sentinel branch) and a `0x10DE00` work-RAM shadow. Its exact source-column layout and
the meaning of `A2=0x20FC` are **not yet proven** — this is the blocking unknown for a faithful FG translation.

## Scroll (Phase 7 — partial)
Arcade (`arc_scroll.txt`): at `2/3/0` **`scrollA` (`0xC20000`/`0xC20002`) animates** from `0x01FF` decreasing by
3/frame (horizontal scroll of the level during READY); **`scrollB` (`0xC40000`) = 0**; no vertical-scroll writes
(Y = 0). Genesis Build 0154 `staged_scroll_x_bg` stays 0 (static) — the BG X-scroll animation is not reproduced.
The "moving horizontal seam" is consistent with the **empty/stale Plane A being composited over the scrolling
Plane B** (and/or an FG scroll value applied to an unpopulated plane); it needs a committed-plane confirmation
once the FG plane is populated.

## Why no build this round
- The dominant fix is **populating the Stage 1 FG plane**, which requires decoding the **`0x0559B2` FG producer's
  source-column semantics** (`A2=0x20FC`, `a5@0x10CA` index, 4-row strips, `0xFF` sentinel) — currently
  unresolved, which is a stated stop condition ("source-column semantics remain unresolved").
- 5 FG codes are **unmapped** in the LUT (`0x020, 0x434-0x437`); the generator models only the BG source blocks,
  so the FG tile family must be added — but only after the FG source layout is proven (avoid guessing a code set).
- The BG is already correct, so no bounded BG-only change is justified; a rushed partial FG pipeline would risk
  an unvalidated build. Per discipline, the faithful FG translation is deferred to a focused follow-up.

## Smallest next task (bounded, then implement Build 0155)
1. **Decode the `0x0559B2` FG producer:** prove the `A2=0x20FC` source layout, the `a5@0x10CA` column index, the
   4-row-strip destination progression, the `0xFF` sentinel branch, and how the FG descriptor relates to the
   shared `0x3951C` walker; enumerate the complete Stage 1 FG code set structurally (like `collect_runtime_
   gameplay_sources` did for BG).
2. **Extend the generator** to add the FG code family to the gameplay scene set so the global LUT maps the 5
   currently-unmapped FG codes and the gameplay manifest loads their patterns (reuse the existing global-LUT /
   per-scene-manifest architecture; verify budget still ≤ 1164).
3. **Add a Genesis FG producer hook** analogous to `genesistan_hook_itempage_strip_blit` that routes the FG
   strips through `genesistan_hook_tilemap_fg_fill` → `staged_fg_buffer` → existing FG dirty + VBlank commit,
   wired at the FG producer's opcode site, keyed on the producer-source identity (no state test).
4. **Route the BG X-scroll** animation through the existing `staged_scroll_x_bg` + `vdp_commit_scroll` path from
   its proven arcade producer (`0xC20000` writer), and confirm the seam resolves once Plane A is populated.
5. Re-validate BG unchanged, FG populated + composited, scroll correct, frontend intact, gate/determinism green.

## Gameplay sprites / Exodus (recorded, not investigated)
- Gameplay PC090OJ sprites (player/enemy) remain absent — a separate downstream boundary, not touched here.
- Exodus remains black while BlastEm/real hardware show the (BG-correct, FG-missing) plane; recorded as a
  validation datum, not pursued; no emulator-specific behavior added.

## Confirmation (no forcing, no changes)
No source, JSON, ROM, or build was produced. No forced scroll, no hardcoded map, no second renderer/loader/commit
path, no scene-specific/RAM LUT, no `state==2/3/0` special-case, no sprite fix, no patch of dead raw writers.
Build 0154's global LUT, manifests, scene selection, BG staging, palette, and frontend are intact.

## Open issue impact
- **OPEN-017:** advanced — Stage 1 BG plane confirmed faithful; the remaining Stage 1 rendering gap is
  root-caused to the **unpopulated PC080SN FG plane** (arcade producer `0x0559B2`, source `0x20FC`, 4-row strips,
  5 unmapped FG codes) plus the static BG X-scroll. Bounded FG-producer decode + implementation task defined.
  Not closed; no duplicate.
