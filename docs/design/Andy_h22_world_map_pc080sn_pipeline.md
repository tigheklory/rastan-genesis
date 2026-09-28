# Andy — H22: World / Map / PC080SN Pipeline + Roadmap Presentation Correction

**Agent:** Andy · Static RE (ORIGINAL ARCADE 68000, world_rev1). **No Genesis impl · no ROM build ·
no MAME · runtime build counter 377 untouched.** Authoritative: `build/regions/maincpu.bin`, Ghidra
`rastan_arcade_ref.gpr`. Durable C first. Palette registry unchanged (no new decision).

> **Headline.** The end-to-end world chain is now proven: **master section (A5+0x1242) → progression
> (A5+0x013E) → scene-descriptor index (A5+0x1386) → 12-byte descriptor (0x3951C) → PC080SN column
> stream + collision-record production → live collision grid (0x10DE00) → lookup (0x53A2E)**. The
> PC080SN foreground column streamer is now COMPLETE, so the GAME/WORLD CONTROL tier shows real H22
> progress (**PC080SN subsystem 0/3 → 3/6, 41%**). The roadmap dashboard is corrected to
> dependency-tier order with a unique-byte primary bar.

## A. H21 roadmap corrections (done first, cheaply)
- **Dependency-tier ordering** replaces old H20 subsystem order. Tiers: CORE EXECUTION → GAME/WORLD
  CONTROL → CORE GAMEPLAY → PRESENTATION → SUPPORT. Palette is no longer first just for being 100%.
- **Primary graphical bar = unique executable byte (union, 33,274 B).** The OVERALL stacked bar now
  uses union coverage; per-subsystem bars use function-span, each bar labelled (`unique-byte` /
  `fn-span`) so the two metrics are never mixed inside one bar. Span-sum and the H20 historical
  figures remain visible as secondary text.
- **Centaur removed from the hazard census** — it is a field enemy with human identity PENDING (one of
  `0x01CB / 0x043A / 0x06E2 / 0x0889`), shown in field-enemy coverage with an explicit note, not as a
  hazard. Its technical uncertainty is unchanged.
- **Player-frame status honest split:** 75 slots enumerated · cell-decoded/rendered: 0 · remaining
  cell-decode: 75. No claim that all frames are in the Composer. CF-01 deferred to H23.
- Classifier fix: `rastan_execution_spine.c` → INTERRUPTS/VBLANK (H21 ISR was mis-bucketed to AUDIO).

## B. Progression ownership (PROVEN — raw/00050248.c, rastan_world_progression.c)
Selector 0x50248 (Ghidra-unlisted region, so not in the census denominator, but durable):
- `A5+0x1242` (master section) → `0x5073A[section]` → `A5+0x013E` (global progression).
- `A5+0x013E` vs round-boundary table **0x502AC = {0x16,0x2D,0x44,0x5B,0x72,0x89,0xFFFF}** → `A5+0x1360`
  (1 = round start, also queues state 0x25 + A5+0x12EE=0xFF; else 0xFF).
- `A5+0x013E` → `0x507C5[progression]` → `A5+0x1386` (scene-descriptor index).
Verified field meanings in use: A5+0x1242 = master section (NOT "round"); A5+0x013E = progression;
A5+0x1386 = scene-DESCRIPTOR index (distinct from the 0x50EE0 section-kind index).

## C. Scene descriptor format (PROVEN — h22_scene_descriptors.tsv)
`A5+0x10FC = 0x3951C + scene*12` (0x503A0). Each **12-byte** descriptor = two 6-byte halves
`{u16 count/flags, u32 ROM layout ptr}` (foreground, background). Verified scenes 0–5, e.g. scene 0 =
`00 02 00 00 d1 1c | 00 02 00 00 d9 1c` (count 0x0002, FG ptr 0xD11C, BG ptr 0xD91C). Layout source
bases A5+0x1038/0x103C = `0x34F9C`/`0x3725C + d1` (0x50384).

## D. Map pointer table producer (PROVEN — h22_map_pointer_tables.tsv)
The retained A5+0x10D000 region producers:
- `A5+0x10D000[16]` column-stream pointers ← **0x502CC** (`0x1691C + col*0x22C0 + scene*0x40`), rebuilt
  on scene advance (H12).
- `A5+0x10D040[16]` collision-record pointers + `A5+0x10D080[16]` tile words ← **0x55904** (descriptor
  word1 → record ptr, word0 → tile), refreshed every 4 strips (H13).
- `0x10D0FC/0x10D100/0x10D104` stream staging ← 0x55C2E/0x55C5E (per streamed column).
The producer is identified, not merely the consumers.

## E. Foreground / background streamers
- **Foreground column streamer 0x55C4A/0x55C5E/0x55C7A — COMPLETE (raw/00055c4a.c, rastan_world_stream.c).**
  Copies 64 tile words down a PC080SN name-table column: `tile = layout_src[row*32 + scroll_col*2]`,
  dest stride **+0xFE** per row, scroll column A5+0x10F6 advanced per column.
- Background tilemap decompressor 0x563A6 (per-round `0x562CA[round]` stream, 0xFF=col/0=end) — H11.
- Collision streamers 0x559B2 / 0x55A14 (BG / FG-parity) — H13, produce the collision word alongside
  the tile.

## F. PC080SN semantic cut (the ReROM translation boundary)
`ARCADE WORLD DECISION` (descriptor → layout-source word by `row*32 + col*2`) → `FINAL SEMANTIC
TILE/CELL` (the 16-bit tile word / collision word) → `PC080SN-SPECIFIC EXECUTION` (name-table 64-row
+0xFE walk / 0x10DE00 collision-ring store). Genesis realization keeps source selection + the
tile/collision word and replaces only the chip-specific write. No Genesis code written.

## G. Collision-record format (canonical — h22_collision_record_format.tsv)
One machine-readable spec (no duplicate Markdown authority): ordinary cell
`cw = record[0x14 + strip*2 + cell*8]`; uniform/sentinel `if record[0x20] high byte == 0x00FF → cw =
record[0x22]`. `marker = cw >> 8` (classified by the 0x41362 28-route table, H6); tile-type / door
`= cw & 0x7F` (via 0x53A2E). strip = A5+0x10CA (0..3, FG parity-reflected), cell = d2 (0..3). Build
0378's +0x22 finding is corroboration only.

## H. Live collision-grid population
`0x559B2 → 0x10DE00` grid (per world row/column, ring/wrap via +2 then +254 dest stride), consumed by
**0x53A2E** (`cell & 0x7F`). Producer chain and addressing established; not every player consumer
decompiled (out of H22 scope).

## I. Scene transitions (PARTIAL — h22_scene_transition_flow.tsv)
Ownership established: freeze/transition owner **A5+0x1394** (gate at 0x55DFE, ==1), transition
sub-state **A5+0x13AA**, checkpoint save **A5+0x13B8 = A5+0x013E** (0x55E10), new-scene setup jsr
0x59F5E, screen wipe/load bsr 0x56176. Door path 0x53F0C/0x54038 (tile 0x7E → A5+0x10E8:=7) → consume
0x3A7D2 (A5+0x1242 := A5+0x013E, actor clear 0x3A804, scene reload) → map/collision source rebuild
(0x502CC / 0x55904). Transition internals (0x56176/0x59F5E/0x5632A) remain a frontier.

## J. Round vs sub-round distinction (PROVEN)
Kept distinct: **round boundary** = A5+0x013E ∈ {0x16,0x2D,0x44,0x5B,0x72,0x89} → A5+0x1360=1 (R1..R6).
**Sub-round/scene change** = A5+0x1386 changes without a round boundary (most 0x507C5 steps are +1).
**Background-bank change** is a descriptor/stream property, not the round (mid-round only R3/R5/R6).
These are separate contracts and not conflated.

## K. 0x7E door status — SOURCE CLARIFIED, positions left as one frontier
Completing the collision-record format clarified the door source: it is the **low 7 bits of the
collision word** in the record (`cell & 0x7F == 0x7E` via 0x53A2E), not a separate field. Enumerating
per-round door positions still requires a data scan of 0x1691C→record cells per scene, so per §17 one
exact frontier entry is left (content_frontier CF-08) rather than derailing H22.

## L. Durable C
New COMPLETE: `0x50248` (progression selector; raw/00050248.c → rastan_world_progression.c,
Ghidra-unlisted), `0x55C4A` + `0x55C5E` + `0x55C7A` (PC080SN column streamer; raw/00055c4a.c →
rastan_world_stream.c, three Ghidra functions, census-creditable). `gcc -std=c11 -fsyntax-only` clean.
Coverage/fidelity/game-wide guards PASS.

## M. ReROM semantic contracts
1. World state is fully derivable from A5+0x1242 via pure table lookups (0x5073A, 0x502AC, 0x507C5,
   0x3951C, 0x50EE0) — no chip state needed for progression/scene selection.
2. The scene descriptor names FG+BG layout sources; the tile/collision word is the semantic unit.
3. One world source record feeds both visible tile and collision property (visual/collision coherence).
4. Transition owns the freeze (A5+0x1394) and the checkpoint (A5+0x13B8); map/collision sources are
   rebuilt from the new progression, not patched.

## N. Updated frontier
`code_frontier.csv` re-ranked by dependency tier + unlock value (not byte size alone);
`decompilation_roadmap.json` created (dependency-tier, closed-H21/H22, next dependencies).
PC080SN closed the FG streamer; remaining world work = transition internals + scroll/wrap + 0x57xxx.

## O. Exact H23 entry dependency
**H23 = PLAYER CONTROL / MOVEMENT paired with CF-01 player-frame/cell extraction.** Entry PCs:
`0x54326` (frame selector, keys on A5+0x10E8/0x12F0/0x1116), `0x54492` (body composer), and the player
state routines in 0x50xxx. Player-frame table **0x5BD40** (75 slots). Rationale: the same player states
select physics AND visual frame, so decoding them together costs less usage than two passes. Do NOT
begin H23 now.
