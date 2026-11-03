# Andy — H24: Player State / Movement Spine + Complete Rastan Frame Extraction

**Agent:** Andy · Static RE (ORIGINAL ARCADE 68000, world_rev1). **No Genesis impl · no ROM build ·
no MAME · runtime build counter 378 untouched.** Authoritative: `build/regions/maincpu.bin`,
`build/regions/pc090oj.bin`, Ghidra `rastan_arcade_ref.gpr`. Durable C first.

> **Final architecture (post-corrections).** Rastan is TWO independent body tracks — upper torso
> (A5+0x1244 → 0x54492 → 0x5BD40, 75 slots) and lower legs (A5+0x1246 → 0x546A8 → 0x5C466, 52 slots) —
> selected independently by the constructor 0x540CC through a2/a3/attack (upper) and a4 (lower). All
> 75 torso slots are positively referenced (no UNUSED); weapon is a separate overlay layer.
>
> **Headline.** CF-01 is closed: all 75 torso + 52 leg slots are decoded (bounded piece counts), the
> frame selector 0x54326 and both composers 0x54492 (upper) / 0x546A8 (lower) are COMPLETE, and every
> distinct composite is rendered from the arcade pc090oj.bin (palette line 3) in the new Bestiary
> **Rastan / Player** section (60 valid full-body pairings + complete torso + complete leg galleries). Union coverage 21.6% full after registering the legs composer 0x546A8.

## Player state machine
- **State field A5+0x10E8**, legal values **{0,1,2,3,4,5,6,7,8,9,16}** (from all writers). Dispatch is
  cmp/branch chains (movement region 0x515xx–0x520xx; render constructor 0x540CC), not one jump table.
- Proven: **7 = door/scene-transition** (H22 tile 0x7E→7, consumed 0x3A7D2), **8 = death** (energy
  A5+0x013A==0 → 8, 0x517EE), **16 = round-complete** (0x51250), **4 = climb** (H23 third-chain). Others
  (2 grounded, 5 attack, 6 airborne, 9 special) PROPOSED from selector/transition evidence.
- Full table: `analysis/decompilation/h24_player_state_machine.tsv`.

## Input
Raw joystick latch **0x10D37A**; edge/debounced input **A5+0x10CE**. Bit tests route to movement
handlers (bit1→0x51E24, bit2→0x52550, bit3→0x5263A/0x52726; A5+0x10CE bit6 gates attack/jump). Exact
direction/button labels PARTIAL. `h24_player_input_state_transitions.tsv`.

## Movement spine
Vertical request feeds pending A5+0x1266 (up)/A5+0x1268 (down) → step dispenser 0x51880 (cap 4 px/frame,
PARTIAL from H23) → scroll (H23-proven). Horizontal via 0x51E24/0x52550. Jump/gravity/landing/rope
handlers are in the movement region and remain PARTIAL/PENDING (collision-dependent, deferred to H25).
`h24_player_movement_contract.tsv`. 0x51880 stays PARTIAL (its remaining semantics depend on the
undecompiled collision consumers).

## Frame system — TWO INDEPENDENT BODY TRACKS (final H24 architecture)
Rastan's on-screen figure is composed from **two independent half-sprites**, each with its own frame
field, composer and table. The player constructor **0x540CC** selects both halves per state and the
selector **0x54326** resolves the upper slot; a separate path resolves the lower slot.

**Upper body (torso).** Selected through THREE upper sources in 0x540CC → **A5+0x1244** → composer
**0x54492** → table **0x5BD40** (75 slots):
- **a2** = weapon-variant pose tables (used when a weapon anim is active), e.g. 0x5BA38 selects the
  weapon-swing family (torso 44/46/48/50/52/54, with the odd companions);
- **a3** = normal pose tables (idle/walk/run/jump/death), 17 tables 0x5B640..0x5BCC0;
- **attack tables** 0x5BAE0 / 0x5BB10 (word-stride), e.g. 0x5BAE0 → up-thrust torso 12/13/14.

**Lower body (legs).** Selected through **a4** in 0x540CC → **A5+0x1246** → composer **0x546A8** →
table **0x5C466** (52 slots / 51 distinct; slot 34 is intentionally blank). Leg cells sit at y 0/+16.

**Composer record format (both 0x54492 and 0x546A8).** slot → `table[slot]` offset → 6-byte pieces
`[tile:u16][xoff:s8][yoff:s8][control:u16]`. The **piece count is variable and bounded by the next
slot's offset** — the hardware's fixed 4-piece loop over-reads short (e.g. crouch) records into
padding, which is the source of the stray tile-0x0003 artifact; reconstruction must bound by record
length. screen X = `((facing?-xoff-16:xoff)+A5+0x10BE)&0x1FF`, screen Y = `(yoff+A5+0x10C0+1)&0x1FF`,
facing A5+0x1114, palette = control low nibble.

**Weapon = a separate overlay layer**, indexed by the SAME frame slot A5+0x1244, appended after the
body pieces; table by A5+0x12FA (0x5CD8A / 0x5D068 / 0x5D346 / 0x5D666). Its sword-hilt cell is the
per-frame hand/grip point.

**CF-01 CLOSED.** All **75 torso** (0x5BD40) and **52 leg** (0x5C466) slots are structurally decoded
with bounded piece counts (`h24_player_frame_cells.tsv`, `h24_player_leg_cells.tsv`). The 75 torso and
52 leg slots are the complete source vocabulary; the two tracks animate **independently**, so a
full-body pose is `torso[a?[i]]` over `legs[a4[i]]` for a given animation index — **not** the Cartesian
product. Valid reconstructed full-body pairings: **60** (three earlier disconnected leg-17 pairings were
removed by the waist-seam gap check).

**Reachability = positive provenance, not "unknown".** With all upper sources (a2 + a3 + attack)
included, **75/75 torso slots are positively referenced** by a proven selector — normal, weapon-variant,
attack/up-thrust, or weapon-swing companion (`h24_player_frame_reference_map.tsv`). **No torso frame is
UNUSED.** (An earlier first-pass scan of only the a3 tables wrongly labelled ~33 frames unused; that
claim is superseded.)

## Player palette — single shared source
255 of 263 visible player pieces carry control 0x0003 → **palette line 3, colbank 0x60**, the single
Rastan-player source already in `specs/palette_decisions.json` (cited, NOT duplicated). A small tail
(8 pieces on death/special slots) reads low-nibble 0/8; enumerated in the cell TSV, treated as the same
player identity pending confirmation. **All reachable body frames map to one source** — a user maps the
player palette once and it applies to every frame.

## Palette Composer / Bestiary
The living artifact now has a **Rastan / Player** section that renders **60 valid full-body pairings** plus the complete torso and leg galleries
from the arcade pc090oj.bin (no screenshots, no Genesis art), driven by the decoded 0x5BD40 table
(canonical inventory = h24_player_frame_cells.tsv). It shows the **RASTAN BODY COVERAGE** metric: 75/75
torso 75/75 + legs 52 decoded, 75/75 torso positively referenced, single shared palette (line 3).

## Durable C
New COMPLETE: `0x54326`, `0x54492` (upper), `0x546A8` (lower legs composer)
(rastan_player_render.c / raw/00054492.c). `gcc -std=c11 -fsyntax-only` clean. Guards: game-wide PASS,
fidelity PASS, actor PASS.

## Coverage
Primary unique-byte: full **18.5% → 21.6%**, touched **26.5% → 29.6%**; 62 → 65 COMPLETE (incl. 0x546A8).
PLAYER_CONTROL_MOVEMENT subsystem gained the frame selector + composer.

## Machine-readable outputs (authoritative generated player-frame evidence)
h24_player_frame_cells.tsv (75 torso), **h24_player_leg_cells.tsv (52 legs)**,
**h24_player_frame_reference_map.tsv (75/75 positive provenance)**, h24_player_frame_selection.tsv,
h24_player_animation_sequences.tsv, h24_player_state_machine.tsv, h24_player_input_state_transitions.tsv,
h24_player_movement_contract.tsv, and **h24_player_render_contract.json** (two-half architecture,
state/selector/composer/palette/overlay + ReROM cut). These are referenced as authoritative player-frame
source in `rastan_actor_graphics_manifest.json` (player_render_architecture) and consumed by the Bestiary
and the Palette Composer.

## Frontier
CF-01 CLOSED. Torso reachability is now **positive provenance, 75/75** (reference map) — not an open
"unknown"; CF-10 PLAYER_SLOT_REACHABILITY is therefore superseded (the only residual nuance is the
gameplay-vs-attract *usage* of a given selector, not whether a frame is referenced). code_frontier +
decompilation_roadmap synced H24 (`player_frame_extraction = COMPLETE`). Player movement state handlers
(0x515xx–0x520xx) remain the player frontier.

## Recommended next checkpoint
**H25: CORE COLLISION / PLAYER COLLISION CONSUMERS** — H24 movement exposes the exact collision API
(grid lookup 0x53A2E, player consumers in 0x515xx, 0x51880). This is the next foundational dependency
before enemy AI and hazards.
