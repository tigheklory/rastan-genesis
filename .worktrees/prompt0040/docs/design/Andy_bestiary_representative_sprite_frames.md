# Bestiary Representative Sprite Frames — reconstruction work log

**Analysis only. No ROM, no Genesis, counter 359.** Builds on the Palette Composer work and the
existing lexicon composite piece lists. Sprites reconstructed directly from `build/regions/pc090oj.bin`.

## Method (proven)

- **Tile unit PROVEN:** each PC090OJ `code` = 128 bytes = one 16×16 4bpp sprite at `code*128`
  (verified: SHA256 of `pc090oj.bin[79*128:+128]` == `families.json` `physical_patterns[79]`).
- **Pixel layout PROVEN by render:** linear row-major, 16 rows × 8 bytes/row, high nibble = left
  pixel; index 0 = transparent. (Confirmed by rendering Lizardman → a correct green lizard with club.)
- **Composite:** each actor's `representative_pieces` (code, x, y, flip_h/v) placed into a
  `composite_dimensions_pixels` canvas. These piece lists are the existing Composer/lexicon
  reconstructions — reused, not re-derived.
- **Palette:** proven `mame_display_rgb8` from `enemy_palettes.json` (arcade pool decode, validated vs
  KF-1214) where available; neutral grayscale ramp where the palette is still pending. **No sampled or
  mixed composite is used; no invented colors.**

## Work log

| Actor | Frame source | Family / base | Composite pieces | Palette | Output | Confidence | Remaining |
|---|---|---|---|---|---|---|---|
| Lizardman | existing composite | +0x3E=0 / 0x004B | 10 | PROVEN 0x36 | color 48×48 | high | full animation |
| Chimera (winged dragon-beast) | existing composite | +0x3E=1 / 0x00D0 | 10 | PROVEN 0x34 | color 64×48 | high | name is Composer's; full anim |
| Four-Armed Swordsman | existing composite | +0x3E=3 / 0x02E8 | 10 | PROVEN 0x3A | color 48×67 | high | full anim |
| Large Bat | existing composite | special / 0x03F6 | 4 | PROVEN 0x3E | color 32×32 | high | — |
| Small Bat / Hurry-up | existing composite | special / 0x0268 | 1 | PROVEN 0x3E | color 16×16 | high | — |
| Horned Warrior *(proposed)* | existing composite | +0x3E=4 / 0x0420 | 8 | pending | grayscale 48×49 | shape high | palette; name |
| Skeleton Warrior *(proposed)* | existing composite | +0x3E=6 / 0x03B3 | 9 | pending | grayscale 48×56 | shape high | palette; name |
| Serpent *(proposed)* | existing composite | +0x3E=11 / 0x0400 | 4 | pending | grayscale 32×32 | shape high | palette; name |
| Small Crawler *(proposed)* | existing composite | +0x3E=5 / 0x01CB | 19 | pending | grayscale 16×16 | low (overlaid frames) | clean single frame; palette |
| Spear / Harpoon *(proposed)* | existing composite | special / 0x050B | 3 | pending | grayscale 40×32 | high | palette |
| Fireball *(proposed)* | existing composite | special / 0x019D | 1 | pending | grayscale 16×16 | med | palette |

## No proven frame yet (shown as DECOMPILATION PENDING — not guessed)

| Actor | Family / base | Why pending |
|---|---|---|
| Valkyrie | +0x3E=8 / 0x0241 | no `representative_pieces` in the lexicon; palette PROVEN 0x32 — needs a composite from the animation tables |
| Flying Demon | special / 0x0129 | no composite piece list; palette PROVEN 0x35 — reconstruct from the two-slot body+wings records |
| Enemy 0x043A | +0x3E=7 | no composite piece list |
| Enemy 0x06E2 | +0x3E=9 | no composite piece list |
| Enemy 0x0889 | +0x3E=10 | no composite piece list |
| Boulder | special / 0x0D5F | no composite piece list |

## Correction (found the proven Composer renders)

The Palette Composer already produced clean, named, correct-palette renders in
`analysis/graphics_optimizer/round1_phase1_corpus/contact_sheets/enemy_*.png` (Lizardman, Chimera,
Four-Armed, **Valkyrie**, **Flying Demon**, Large/Small Bat) — these are the category-1 proven frames I
should have used first, and they cover the actors I had wrongly left pending (Valkyrie, Demon). All 6
**bosses** also have `representative_pieces` and render fine (grayscale, base 0x033E, robed
staff/mace-wielder). Boulder uses `cand_5c8_0D5F.png`. The bestiary now shows **20 real sprites**;
only 0x043A/0x06E2/0x0889 (never captured in the R1 corpus) remain frame-pending.

## Summary

11 actors now render as real arcade sprites in the bestiary (5 in proven color, 6 in shape-proven
grayscale). Six actors remain frame-pending. **Next:** reconstruct Valkyrie (0x0241) and Flying Demon
(0x0129) composites — both have proven palettes and are R1 actors — from the animation/composite tables
(`0x3D09E`… via `actor_four_record_expand_3c902`) since they lack a stored piece list; then the
remaining +0x3E families 0x043A/0x06E2/0x0889.

---

## ROM-truth pass (2026-09-17): per-round palettes decoded from the ROM

**Palette pipeline PROVEN and decoded from `maincpu.bin`** (no traces):
loader `FUN_0003BA20` → `pool_index(round,bank) = maincpu.bin[0x3BA88 + (round-1)*32 + (bank & 0x0F)]`;
`palette = pool 0x4FD02 + pool_index*32` (16 0RGB words); 0RGB nibble → RGB8 via `pal5(n*2)`.
Validated: R1 Lizardman/Chimera/Insect/Valkyrie computed from ROM == `enemy_palettes.json` exactly.
Per-round pool index proves the palette changes per round (Lizardman pool 13 in R1–R3 → 14 in R4–R6;
Valkyrie 15 → 28 (R5) → 31 (R6)). Every card is now rendered in **that round's ROM palette**.
Family palette nibbles from table 0x45722 (validated: fam0→0x36, fam1→0x34, fam3→0x3A, fam8→0x32).

Boss palette: bank 0x37 (fam2 nibble 7), per-round pool from the same table → six distinct colored
bosses from their distinct per-round composites.

## Genuine blocker (documented, not faked)

The compositor is a VM (`actor_four_record_expand_3c902` @ 0x3C902: control-nibble dispatch, indirect
data pointers, animation-indexed sub-tables). Statically reimplementing it is a large separate task.
For the 8 field families + 6 bosses + specials that already have the compositor's real piece output
(`representative_pieces`), that geometry is used and re-paletted from ROM. The 3 field families with
**no captured composite** — 0x043A (+0x3E 7), 0x06E2 (+0x3E 9), 0x0889 (+0x3E 10) — cannot get a legal
composite without that VM (their per-tile base graphics are fragments), so they are flagged, not
guessed. Valkyrie/Flying Demon geometry uses the existing Composer render (R1 palette baked; per-round
pool noted).

## Audit
- Scheduled field families: 11 · with real sprite: **8 / 11** (unresolved: 0x043A, 0x06E2, 0x0889).
- Field palettes from ROM per round: **11 / 11** (all families, all rounds).
- Bosses: **6 / 6** distinct sprites + ROM palettes.
- Special/map actors: **6 / 6** sprites.
- Blank checkerboards: 3 (only the compositor-VM-blocked families).
