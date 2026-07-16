# Andy — Player Sprite Composition: Build 0181/256 & 0182/128 vs Arcade

**Date:** 2026-07-16
**Type:** Analysis (arcade-vs-Genesis sprite record/SAT/tile/palette evidence + rendered screenshots). No build; repo remains default 256.
**Builds:** 0181/256 `1ef9085e…` (default), 0182/128 `5f7264db…` (diagnostic-safe), 0183/80 `defe5173…` (known-bad control only).

## Primary question — answered: classification **A**
**Build 0181/256 renders Rastan's player sprite cluster arcade-equivalently.** Position, composition, palette, and flip are correct; the only broken player rendering (right-side red cluster) is the Build 0183/80 cap artifact. Build 0182/128 is equivalent to 256.

## Rendered screenshots (MAME `-video soft` snapshots)
- Arcade reference (F1100): `states/traces/build0181_sprite/snap_arc/rastan/0000.png` — Rastan on the LEFT on a rock ledge, coherent barbarian, sword raised, facing right.
- Build 0181/256 (F1200): `states/traces/build0181_sprite/snap_256/genesis/0001.png` — Rastan on the LEFT, coherent barbarian, brown loincloth + skin tones, sword raised, facing right. Matches arcade composition.
- Build 0182/128 (F1200): `states/traces/build0181_sprite/snap_128/genesis/0001.png` — visually identical to 256.
- Build 0183/80 (F1200): `states/traces/build0181_sprite/snap_80/genesis/0000.png` — Rastan on the RIGHT (screenX≈288), broken red/orange cluster (rejected control).

Visual notes: 256/128 show a coherent barbarian (not a red blob); no body parts missing/flipped/misordered relative to arcade; skin/loincloth/sword colors read correctly (sprite palette line 3). 80 shows the flipped, right-side, broken cluster.

## Arcade reference (PC090OJ object RAM 0xD00000, F1100)
Arcade canonical Rastan = records **120,121,124,125,126**:
```
r120 w0=4003 Y=0049 code=009E X=0010
r121 w0=4003 Y=0059 code=009F X=0010
r124 w0=4003 Y=0051 code=008E X=0018
r125 w0=4003 Y=0061 code=008F X=0020
r126 w0=4003 Y=0061 code=0090 X=0010
```
The arcade uses ONLY the record-120..137 cluster (X=0x10..0x20, left). Low records 0..11 are empty in arcade.

## Build 0181/256 player SAT (F1200)
Rastan's SAT slots are palette line 3, hflip=1, screenX 16..32 (left), tiles 0x400..0x464 — a coherent body/sword cluster. Source records: canonical 120,121,124,125,126,128,129 (slots s1..s5,s9,s10) AND low duplicates 0,1,4,5,6,8..11 (slots s0,s18..s25). Mirror X of the player records = 0x0010..0x0020, matching arcade; decode places them at screenX 16..32 (arcade-equivalent left position). Non-player slots (s6,s7,s8,s13,s14,s17,s26,s27) are pal 2 at screenX 144..280 (other objects).

## Build 0182/128 player SAT (F1200)
Same sprite family: pal 3, hf=1, screenX 16..32, tiles 0x400.. — Rastan on the left. Slot allocation differs slightly from 256 (different slot numbers) but the tile/palette/flip/position family is identical → **visually identical to 256**.

## 256 vs 128 vs arcade equivalence
- **256 vs 128:** equivalent — same player sprite family, position, palette, flip; only SAT slot-index allocation differs (no visible effect). Screenshots identical.
- **256 vs arcade:** player position (left, screenX≈16 vs arcade X=0x10), palette (sprite line 3), flip (facing right), and coherent barbarian composition all match. (Background scroll position differs because the two are at slightly different stage-scroll points, not a sprite issue.)
- **128 vs arcade:** same as 256 vs arcade — arcade-equivalent player.

## Notable finding — Rastan is DOUBLE/TRIPLE-drawn on Genesis (not visible corruption, SAT-budget waste)
The Genesis 256/128 builds represent Rastan from BOTH the arcade-canonical records (120..137) AND spurious low-duplicate records (0,1,4,5,6,8..11), and partially a third set. The arcade draws Rastan once (records 120..126, ~9 sprites); Genesis draws ~2x that (~18 SAT slots). The extra copies overlap the canonical Rastan (same screenX, adjacent tiles) so the picture still reads as one coherent barbarian — **no visible corruption** — but it consumes roughly double the SAT budget. Likely source: `pc090oj_workram_block_sprites` default path (used by `hook_target_45dfa`) still copies A5+0x11B2 -> records 0..17, a Build 0164 lineage artifact — while the arcade 0x045DFA is a different routine that does not copy A5+0x11B2. This is a strong candidate for a future bounded cleanup (removing the spurious low-record player copy) and may relieve SAT-slot pressure relevant to the missing-enemy budget — but it is NOT the cause of any visible player corruption and is out of scope for this evidence task.

## 128 safety answers
1. 128 preserves records 120..121: **YES**.
2. 128 preserves enough of 120..137 for player composition: **YES** (120..127 present; the core 120,121,124,125,126 canonical cluster is intact).
3. Records 128 drops from 128..137: records **128..137** (>=128).
4. Are dropped 128..137 used for player body parts? They are player-coded but redundant (a third copy); the canonical 120..126 + low duplicates already compose Rastan.
5. Why does the player still look normal at 128? The canonical anchor/body (120..126) and low duplicates remain; only the redundant >=128 copy is dropped.
6. 128 vs 256 player SAT/tile/palette/order: same family; only slot-index allocation differs; no visible difference.
7. Is 128 still recommended as a practical diagnostic cap: **YES** (>=122 safe; 128 gives margin).

## 80 control (known-bad, not patched)
Records 120..121 dropped (>=80 out-of-range); canonical player anchor missing; head sprite flips to screenX≈288 (right) with broken composition; sprite cluster corrupted. 80 remains unsafe. Not patched, player not forced.

## Player-cluster answers
- Player anchor record: **120 (009E) / 121 (009F)** (arcade-canonical).
- Player body-part records: 124,125,126 (008E/008F/0090) canonical; 128,129 (0076/0077) and low duplicates 4,5,6,8..11 mirror the same body/weapon tiles.
- Records carrying flip/position/attr: all player records carry w0=4003 (attr), Y, X; the global flip-screen (from the PC090OJ ctrl) drives the mirrored right-side result only when the anchor is dropped (80).

## Config-mechanism / safe-build bug check — NONE
256 and 128 render Rastan correctly and equivalently; no player palette-routing, tile-code, SAT-assembly, or flip/position bug in the safe builds. The configurable mirror mechanism is sound. No fix warranted here. (The double-draw is a pre-existing Build 0164 redundancy, not a mirror-mechanism bug.)

## Not changed
Configurable mirror mechanism, Build 0180 SAT-dirty gating, Build 0178 tile-DMA, Build 0175 palette route, 0171/0172 projections — all preserved. No input/collision/enemy/sky/D00298/continue/Exodus work. Repo left at default 256.
