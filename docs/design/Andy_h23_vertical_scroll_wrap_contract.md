# Andy — H23: Vertical Scroll / Wrap Contract

**Agent:** Andy · Static RE (ORIGINAL ARCADE 68000, world_rev1). **No Genesis impl · no ROM build ·
no MAME · runtime build counter 378 untouched (external Cody value; never written by me).**
Authoritative: `build/regions/maincpu.bin`, Ghidra `rastan_arcade_ref.gpr`. Durable C first.

> **Headline.** The complete foreground vertical-scroll contract is proven: player motion →
> pending (A5+0x1266/0x1268) → 4 px/frame delta → screen-Y band clamp [32,304] → step → **FG Y
> scroll A5+0x10AE (mod 512) → 0xC40002** + 8-px row ring stream. A compact machine-readable contract
> for Cody is written. WORLD VERTICAL SCROLL is COMPLETE; PC080SN subsystem rose to ~80%.

## Scroll fields (all PROVEN from writers/readers)
- **FG Y scroll = A5+0x10AE** → PC080SN 0xC40002 (commit 0x55ACC), wrap mod 512.
- **FG X scroll = A5+0x10EC** → PC080SN 0xC40000 (commit 0x55ABC), wrap mod 512, half-rate (0x10F0).
- **Player screen-Y = A5+0x10BE**, band-clamped [32,304], center 80.
- **Scroll delta = A5+0x10DC** = min(pending, 4) px/frame (0x51880).
- **Pending up/down = A5+0x1266 / A5+0x1268** (fed by player movement).
- **Scroll step = A5+0x10D8**; **direction accumulator = A5+0x10B8** (limit 160); **sub-row accumulator
  = A5+0x10B2** (bit3 = 8-px row); **flags = A5+0x10D0** (bit6 up-limit, bit7 down); **dir mode =
  A5+0x13D0** (2 up / 3 down).

## Per-frame scroll decision order
1. Player movement queues motion into A5+0x1266/0x1268.
2. Step dispenser (0x51880) caps at 4 px/frame → A5+0x10DC.
3. Clamp controller (0x539C2) keeps player screen-Y in [32,304] band (center 80, hard-coded
   thresholds 32/80/304); arms step A5+0x10D8 + flags.
4. Dispatch (0x557BA/0x55854): if A5+0x10B8 ≥ 160 and section-kind gate A5+0x10A8 ≠ 0 → stop (bit6);
   else accumulate A5+0x10B2, stream a map row (0x406A4, dir A5+0x13D0) per 8-px crossing, and
   A5+0x10AE ±= step (mod 512).
5. Commit (0x55AB4): A5+0x10EC→0xC40000, A5+0x10AE→0xC40002.

## Coordinate spaces (PROVEN)
- actor_screen_y = `(actor_world_y + A5+0x10AE) & 0x1FF` (0x461CE).
- collision_probe_row = `((((~A5+0x10AE + 1) & 0x1FF) + world_y) >> 1) + 8) & 0xFC` (0x53A2E).
- logical_map_row = `(world_y >> 3) & 63`; ring_row = `(A5+0x10AE & 0x1FF) >> 3`.
- **Visual and collision share the SAME Y-scroll field A5+0x10AE — identical origin, no offset.**

## Vertical map ring / wrap
Both axes wrap the pixel scroll value **mod 512** (`&0x1FF`). PC080SN name table = 64×64 tiles =
512×512 px, so the vertical ring is **64 tile rows**; a new row becomes resident on each 8-px step
(A5+0x10B2 bit3) via 0x406A4; name-table row base = `0xC08000 + (A5+0x10CC<<4) + (A5+0x10CA<<2)`.

## Scroll boundaries — source
- Player screen-Y band **32 / 80 / 304** are **hard-coded immediates** (0x53A0C / 0x539E0 / 0x539A0).
- Direction-accumulator upper limit **160 (0xA0)**, gated by section-kind A5+0x10A8 (0x557BE).
- Scene Y-scroll init from table **0x50850[A5+0x013E*12]** word0 (R1 Phase-2 prog 2/3 → **0x0160**).
- World vertical extent itself is governed by map-row availability (streaming) — PARTIAL.

## Scene-entry initialization
0x504FA reads 0x50850[A5+0x013E*12]: word0→A5+0x10AE & A5+0x10EC (scroll init), word2→A5+0x10B8
(direction accumulator), word4→A5+0x10BE (player screen-Y). Proven R1-Phase-2 (prog 2/3): Y init
**0x0160 (352)**, screen-Y **0x0078 (120)**. Scene transition 0x561A0 zeroes A5+0x10AE/0x10B0/0x10EC/
0x10EE before 0x504FA re-inits (answers §10: transition resets scroll, init sets Y + band).

## State-4 (climb) scroll behavior + third-chain contract
While climbing, movement keeps feeding A5+0x1266 (up); the dispenser emits ≤4 px/frame; 0x557BA/
0x55854 keep advancing A5+0x10AE **upward** (mod 512) and streaming rows until the accumulator limit
(160, gated by A5+0x10A8) or the screen-Y band clamp stops it. **Third-chain contract:** from the
scene-init Y 0x0160, an upward climb moves the committed Y toward **~0x010D and keeps moving**; a
value stuck at ~0x0026 means the up path (A5+0x1266 → A5+0x10DC → A5+0x10AE += step) is not being
driven. (Genesis runtime figure is corroboration only; the arcade static code is authority.)

## PC080SN semantic cut (scroll-specific extension of H22)
`ARCADE GAMEPLAY DECISION (player motion → pending → clamp band [32,304])` → `SEMANTIC foreground Y =
A5+0x10AE (mod 512) + logical map row (Yscroll/8 mod 64)` → `PC080SN EXECUTION (write A5+0x10AE to
0xC40002 + name-table ring-row walk +0xFE)`. Everything before the cut is preserved in ReROM; only
the register write + ring walk is hardware. No Genesis code written.

## Durable C
New COMPLETE (Ghidra functions, census-creditable): `0x557BA`, `0x55854` (Y scroll update/stream),
`0x55AB4` (PC080SN scroll commit), `0x55B3C` (X scroll update). New PARTIAL (Ghidra-unlisted drivers,
documented byte-exact but callee-set open): `0x504FA` (scene init), `0x539C2` (clamp controller),
`0x51880` (step dispenser). Files: raw/000557ba.c, raw/00055ab4.c, raw/000539c2.c, rastan_world_scroll.c.
`gcc -std=c11 -fsyntax-only` clean. Guards: game-wide PASS, fidelity PASS, actor PASS.

## Coverage
Primary unique-byte: full **17.3% → 18.5%**, touched **25.4% → 26.5%**; 58 → 62 COMPLETE.
PC080SN_TILEMAP_SCROLL_COLLISIONMAP subsystem: **~41% → ~80% full** (7/10 functions).

## Machine-readable outputs
h23_vertical_scroll_writers.tsv, h23_vertical_scroll_states.tsv, h23_vertical_wrap_contract.tsv,
h23_vertical_scroll_boundaries.tsv, h23_coordinate_spaces.tsv, and the compact
**h23_rerom_vertical_scroll_contract.json** (state fields, thresholds, coordinate equations, decision
order, clamps, wrap rules, scene init, climb behavior — no prose, no Genesis addresses).

## Updated frontier
code_frontier.csv re-ranked; decompilation_roadmap.json `world_vertical_scroll = COMPLETE`, synced
through H23. Remaining world work (kept separate): 0x406A4 row-stream helpers + transition internals
(0x56176/0x59F5E/0x5632A). **Next dependency:** player control/movement.

## Recommended next checkpoint
**H24: PLAYER CONTROL / MOVEMENT + CF-01 PLAYER FRAME EXTRACTION** — entries 0x54326 (frame selector),
0x54492 (body composer), 0x51880 (player-Y movement); table 0x5BD40 (75 slots). The same player states
drive physics and frame selection, so decoding them together is the efficient next step.
