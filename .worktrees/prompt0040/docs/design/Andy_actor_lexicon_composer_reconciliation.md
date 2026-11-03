# Reconciliation: enemy_sprite_lexicon ↔ Palette Composer (R1 identity/palette authority)

**Analysis only. No ROM, counter 359. Builds on existing work; supersedes nothing silently.** Two
existing bodies of work describe R1 actors and they **conflict**. This documents the conflict, the
authority rule, and the unified R1 chain — per the continuity directive ("if existing work is wrong,
prove the correction and supersede it with documentation; never silently replace identities").

## The two existing sources

1. **Palette Composer / R1 corpus** — `round1_phase1_corpus/enemies.json` + `enemy_palettes.json`.
   Identifies **7 Round-1 enemies** with **PROVEN 16-color palettes** (real `mame_display_rgb8`):
   Lizardman 0x004B/0x36, Four-Armed Insect 0x02E8/0x3A, Valkyrie 0x0241/0x32, Chimera 0x00D0/0x34,
   Flying Demon 0x0129/0x35, Small Bat 0x0268/0x3E, Large Bat 0x03F6/0x3E.
2. **Whole-game lexicon** — `enemy_sprite_lexicon/families.json` + `round_phase_presence.csv`.
   Rendered from `pc090oj.bin` (usable frames) but its **categories and round/phase presence are
   runtime-sweep-derived**.

## Proven conflicts (lexicon is wrong for these R1 enemies)

| Enemy (Composer, proven) | Lexicon record | Lexicon error |
|---|---|---|
| Valkyrie 0x0241 | `static_normal_base0241_unresolved` | left UNRESOLVED, **presence empty** — a real R1 enemy dropped |
| Large Bat 0x03F6 | `aux_5c8_base03f6_compositor0` | miscategorized **"OTHER PROVEN NON-ENEMY"** |
| Small Bat 0x0268 | split across `aux_8c8_base0268` (EFFECT) + `aux_748_base0268` (PROJECTILE) | **split into two wrong categories**, neither "enemy" |
| Flying Demon 0x0129 | — | **absent as an enemy** (not surfaced as a hostile family at all) |
| Four-Armed Insect 0x02E8 | `hostile_base02e8` present **R3/R4/R6** | round attribution conflicts with Composer's **R1** |
| Chimera 0x00D0 | `hostile_base00d0` present **R5/R6** | round attribution conflicts with Composer's **R1** |

Only Lizardman (0x004B) agrees across both. **This is the concrete reason the bestiary is wrong even
at R1**: it took the lexicon's sweep-derived categories/presence instead of the Composer's proven R1
identities + palettes. The base-code round conflicts also suggest **actor-class base codes are reused
across rounds** (same seed, different per-round palette/graphics) — which only the arcade spawn tables
can settle.

## Authority rule (supersession)

- **R1 enemy identity + palette: the Palette Composer is authoritative** (proven from arcade palette
  loader `FUN_0003ba20/56/64`, pool `0x4FD02`, validated vs KF-1214). Supersedes the lexicon's
  category/name for the 7 R1 enemies.
- **Sprite frames: the lexicon renders remain usable** (real `pc090oj.bin` tiles) — reused, not
  rediscovered — but re-associated to the Composer identity.
- **Round/phase presence game-wide: NEITHER existing artifact is authoritative.** The lexicon's is
  sweep-derived (proven wrong above); the Composer's is R1-scoped. The **arcade spawn/roster tables
  are the tiebreaker** and must be decompiled (see the decompilation plan §2–§4).

## Unified Round-1 proven chain (ready now, no new RE)

For the 7 R1 enemies the full chain already exists across the two works and only needs *joining*:
identity+palette (Composer) + render (lexicon, re-associated by base code) + spawn (`0x0559B2` →
`0x41180` → `0x4543E`) + composite pieces (`families.json` `representative_pieces`). This can produce a
**visually- and color-correct R1 section immediately** — the Lizardman-only color in the current
bestiary was my file-selection error, not a data gap.

## What still requires arcade decompilation (extends existing work, not a restart)

1. **Per-round/phase roster** — the spawn/map-marker tables (stage `0x118` + progression `0x13E`),
   to settle the presence conflicts and confirm base-code reuse across rounds.
2. **Distinct per-round bosses** — `0x41F30` boss dispatch (the lexicon's six boss rows are all
   base 0x033E + sampled frames; not distinct).
3. **Per-actor animation → composite → codes** — family tables `0x3D09E/0x4771C/0x3F0CE/0x40004/0x4002C`
   + animation state machines, to replace sampled ("dragon-head") composites with real frames.

Palettes for R2–6 are **not** a decompile — they are the Composer's documented pool decode run per
round (`0x3BA88+(r-1)*0x20`).
