# Andy — Round 1 Phase 1 Color / Palette Audit — status + tile-plane partial

**Type:** analysis. No production change, no ROM, no build consumed, `palette_decisions.json` untouched,
AGENTS_LOG not modified. **This is a partial: the tile-plane (Plane A/B) palette is decoded; the SPRITE
palette source is a proven-unresolved blocker (below), so the sprite audit and the full four-line color
model cannot be completed without fabricating colors — which the palette registry forbids.**

## Hard blocker — sprite palette source (banks 49–127) UNRESOLVED
Prior proven work (`decode_arcade_palette_bank`, AGENTS_LOG): tile-plane palette is COMPLETE
(bank<32 = scene pool `0x4FD02`; 32–47 = base `0x4EAF6`; **48 = BG `0x4FE62`**), but **banks 49–127 =
the PC090OJ sprite-palette load path (attr `a4@0x27`/`a4@39` → sprite-palette staging) is UNRESOLVED** —
the 16 colors of sprite banks 51/`0x33`, `0x36`, etc. are **not decoded**. Therefore Parts 1, 5, 8, 12
(sprite inventory/colors, two-line sprite feasibility, complete four-line model, Rastan-vs-lizard/bat
color comparisons) are **blocked**: they require decoding the sprite-palette load path first. I did not
invent sprite colors.

## Already-decoded 4-line architecture (context)
The project already implements Tighe's proposed shape as a **4-CRAM-line shared model** with a
compiler-generated bank→line route (`palette_route_table`/`palette_route_lookup`,
`palette_route_epochs.inc`), driven by object attr `a4@39 → effective bank (0/3/48/51/0x36)`. Current
Stage-1: **L0 = HUD/`0x36`, L1 = FG bank 3, L2 = BG bank 48, L3 = sprites bank 51** — all 4 lines used,
sprites ~1–2 lines. So the real feasibility metric is **lines(A)+lines(B)+lines(sprites)+lines(HUD) ≤ 4**,
not colors-per-line — and the current model already sits at exactly 4.

## Proven tile-plane color facts (Part 6 / Part 7, tractable)
Decoded from arcade palette pool (xBGR-555; arcade chan 0–30 even; `genesis_3bit=(chan/2)>>1`):
- **Plane A (FG, scene-1 bank 3):** 16 entries → **16 distinct arcade colors → 15 Genesis-quantized**
  (entries 0 and 1 both quantize to black). **Fits ONE 15-color line** (15 non-transparent ≤ 15). ✔
- **Plane B (BG bank 48):** **12 distinct colors → fits ONE line** easily (11 non-transparent ≤ 15). ✔
- FG↔BG share **2 exact** colors (**4** after Genesis quantization) — free consolidation candidates.
- `analysis/round1_phase1_palette_audit/colors.json` holds both decoded 16-entry lines.

**Caveat (not fabricated):** the full Plane-A audit needs the *multi-bank* FG decode — Phase-1 FG uses
several banks (the task lists 0x003–0x01D), selected per-tile by the map attribute bits. I decoded only
the primary scene bank 3 here. The per-tile bank assignment + the other FG banks' colors are a bounded
decode (map-attribute high bits → scene-record byte → pool block) I flag rather than guess. Plane-B
palette *states* across Round-1 progression likewise need the scene-record walk per progression point.

## Reusable reindex tool (Part 9) — delivered
`tools/translation/reindex_graphics_for_palette.py` — general, round/phase/owner-configurable, **dry-run
only, not wired to production**. Given source patterns + source palette + a target consolidated line, it
builds the exact old→new pixel-index map, remaps the 4bpp graphics, verifies every pixel's arcade color
is preserved at its new index, and flags when a color is absent from the target line (→ consolidation or
a physical variant needed). EXACT-only by default; no approximation.

## What remains (prerequisite ordering)
1. **Decode the sprite palette load path** (banks 49–127; `a4@39` → sprite-palette staging) — unblocks
   the entire sprite color audit + two-line feasibility + the complete four-line model.
2. **Multi-bank FG decode** (per-tile attribute → bank) for the full Plane-A color audit and one-line
   pressure across the 7 epochs.
3. **Plane-B palette-state timeline** (scene-record per progression point) for the dynamic-palette view.
Each is bounded and static; none is fabricated here.
