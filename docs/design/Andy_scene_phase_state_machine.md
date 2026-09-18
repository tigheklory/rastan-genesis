# Rastan Scene / Phase State Machine (decompiled)

**Static arcade decompilation. No ROM/Genesis/VM/bestiary, counter 359.** Source: `maincpu.bin` +
Ghidra exports. Original arcade PCs authoritative. Continues the actor-topology + scripted-subsystem
work.

## Field meanings (PROVEN)

### A5+0x1394 — phase-transition-active flag
Two states: **`1` = a phase/scene transition is running**, **`0xFF` = idle (gameplay)**. The whole
transition sequencer (0x55DFE+) is gated `cmpiw #1,A5+0x1394`. The round-advance (0x118++, 0x3A866) is
gated `cmpiw #255,A5+0x1394` — i.e. a round only advances while no transition is active. Writers: set
to 1 at **0x3A614** (round/section start), **0x50492** (jump to section 138), **0x452C0** region; set
to 0xFF (idle/done) at 0x3A62A, 0x55F18, 0x56004.

### A5+0x138A — transition sub-state sequencer
Step counter through the transition (values 8→9→10→11→12→13→255):
- **9**: save `A5+0x13E → A5+0x13B8` (0x55F5C), call scene loaders 0x56128/0x561A0, spawn transition
  actor id 39 via 0x3A0EC; if round (0x10C118) == 6, special end path 0x5725A.
- **10**: loaders 0x5632A/0x561D6.
- **11**: wait 256 frames (`A5+0x1392` counter).
- **12**: loaders 0x561A0/0x561FE.
- **13**: wait 128 frames, then finalize (0x5618C/0x56440), set `A5+0x13E = A5+0x13B8 − 1` (0x56014),
  `A5+0x1394 = 0xFF`.
This is the **screen-wipe + actor-clear + next-scene-load sequence** — the concrete phase transition.

### A5+0x13B8 — saved progression checkpoint
Snapshot of `A5+0x13E` taken at a scene boundary (0x55F5C: `0x13B8 = 0x13E`); `0x13E` is restored from
it at transition end (0x55F26 `= 0x13B8`, 0x56014 `= 0x13B8 − 1`). It is the scene's progression
anchor, not a separate counter.

### A5+0x1242 — master section index
The global section pointer (0..~138). Drives `A5+0x13E` start via ROM table `0x5073A[A5+0x1242]`
(proven earlier). Written 0 at round start (0x3A614), = `0x13E`(±1) at 0x3A63A/0x3A7DA/0x3A874, = 138
at 0x50492. `A5+0x10C6` is the parallel advancing **map-stream pointer** (FUN_000558e0 increments it
and writes the selected byte to `0x10D0A8`).

## Scripted-encounter dispatch → round (PROVEN driver)

The main scripted dispatcher loads its selector at **0x4AB5C: `movew A5+0x13E, d0`** — CONFIRMED it is
progression `0x13E`, not assumed. The extracted chain is **Round 3** (0x13E 0x2F–0x41):

| 0x13E | handler | round |
|---|---|---|
| 0x2F,0x30,0x33,0x34,0x36,0x38,0x3A,0x3B,0x3C,0x3D,0x40,0x41 | 0x4AE28…0x4ABFA | **3** (0x2D–0x44) |

Sibling per-round dispatch chains exist for the R4/R5/R6 scripted values (0x58/0x71/0x86) and the R1
Flying-Demon dispatcher (0x45xxx). **Caveat proven:** a *different* dispatcher at 0x4AF1A uses
`A5+0x288` (a boss/sub-phase selector), so not every dispatcher's d0 is 0x13E — each was checked.

## The 6 round boundaries + boss = proven; OUTDOOR↔CASTLE split = NOT pinned

- **Rounds:** `A5+0x13E` global 0..0x89; boundaries ROM `0x502AC` = {0x16,0x2D,0x44,0x5B,0x72,0x89}
  → 6 rounds (proven earlier, unchanged).
- **Castle→Boss:** the boss is the round-tail scripted encounter; the round advances (0x118++) only
  when the transition is idle (0x1394==255) after it. So **boss ↔ round boundary is proven for all 6**.
- **Outdoor→Castle:** the transition *machine* is proven and runs at every scene boundary, but the
  **specific `A5+0x13E` value where a round switches outdoor→castle is NOT pinned** — it depends on the
  per-section scene TYPE, which comes from a section descriptor I have not located (the scene loaders
  0x56128/0x561A0 copy fixed asset blocks 0x5649E/0x564FE via 0x59AD4; they are not the per-section
  type table). The map-stream (`A5+0x10C6` → `0x10D0A8`) likely carries scene-change/type commands —
  that is the next target.

## 18-slot phase map (only what is statically proven)

| Round | 0x13E | Outdoor | Castle | Boss |
|---|---|---|---|---|
| 1 | 0x00–0x16 | field families {0,1,3,8} share the round's blocks | **split UNKNOWN** | scripted (Flying Demon + boss route), round-tail |
| 2 | 0x16–0x2D | field {0,1,3,4,8,11} | UNKNOWN | scripted route (0x58 dispatcher family), tail |
| 3 | 0x2D–0x44 | field {0,1,3,4,6,8,11} | UNKNOWN | scripted 0x13E 0x41 handler + tail |
| 4 | 0x44–0x5B | field {0,1,3,6,8,9,10,11} | UNKNOWN | scripted 0x58 route, tail |
| 5 | 0x5B–0x72 | field {0,1,3,4,6,7,10,11} | UNKNOWN | scripted 0x71 route, tail |
| 6 | 0x72–0x89 | field {0,1,3,4,5,6,10,11} | UNKNOWN | scripted 0x86 route + round-6 end path 0x5725A |

Field families are the round's scheduled enemies (they span outdoor+castle — no split proven). Scripted
routes are placed by round via 0x13E. **Outdoor-vs-castle assignment is deliberately left UNKNOWN**
(no sweep import) pending the section-type/map-stream decode.

## Next focused task
Decode the **section-type / map-stream scene descriptor**: how each `A5+0x1242` section (or a
map-stream command at `A5+0x10C6`/`0x10D0A8`) is tagged outdoor vs castle, and where the mid-round
outdoor→castle transition (`A5+0x1394 := 1`) is triggered. That pins the castle-entry 0x13E per round
and completes the 18-slot split.

## PHASE-1 → PHASE-2 TRANSITION — MECHANISM PROVEN FROM CONTROL FLOW

**A TT background-bank change is NOT a phase boundary.** The actual mid-round gameplay phase
transition (screen wipe) is recovered here from the scene-director / collision control flow.

### Trigger: a special map-collision tile the player contacts
`0x53a2e` computes an address into the **collision-tile grid at RAM `0x10DE00`**
(`addr = 0x10DE00 + f(scrollX A5+0x10AE, scrollY A5+0x10B0, probe offsets)`, cells are words, tile
**type = `cell & 0x7F`**). The player-vs-map probe family reads it:
- vertical/ground probe `player_ground_contact_probe_family_53b34`
- horizontal probes `0x53a6e`, `0x53e22–0x54050`, `0x53f26–0x54050`

Tile-type semantics (all `andiw #127` then `cmpiw`):

| type | handler | meaning |
|---|---|---|
| 1 | 0x53dc8 | solid floor |
| 2 | bset#5 | special/edge |
| 3 | 0x53dc8 + set 0x13d4 | slope/stairs |
| 4 | 0x53dd6 | solid variant |
| 6 | 0x53df2 | — |
| 7 | 0x53de4+0x53dc8 | — |
| **8** | **0x53e0c** | **DOWN/FALL transition → `A5+0x10E8 := 8`** |
| **0x7E (126)** | **0x53e14 / 0x53f00 / 0x5402c** | **PHASE-TRANSITION DOOR → bset#7 of 0x10CE and `A5+0x10E8 := 7`** (0x53f0c, 0x54038) |

So **`0x10E8 := 7` is requested when the player walks onto a collision tile of type `0x7E`.**

A second `0x10E8 := 7` path exists in the per-frame director `FUN_00052732` @`0x527cc` when the
section-kind `A5+0x10A8 ∈ {4,5,6}`. **`A5+0x10A8` has no static write xref** (computed/indirect
store) — flagged, not assumed; it is likely the auto-scroll boundary / vertical-section path.

### Consumer: game-state machine at 0x3a7d2 → the wipe
`0x3a79c` dispatches on `A5+0x0004`. In the gameplay state, `0x3a7ce`→`0x3a7d2`:
`cmpiw #7, A5+0x10E8`; if equal → `A5+0x1242 := A5+0x13E` (checkpoint), `A5+0x0046 := 1`,
`A5+0x0104 := 1`, `A5+0x0002 := 2`, `A5+0x0004 := 2`. That enters the transition: `0x3a848`
sets `A5+0x1394 := 1` (transition-active) and `A5+0x13aa := 9`; the `0x13aa/0x138a` sub-state
sequencer runs the screen-wipe + actor-array clear (`0x2C8` loop @`0x3a804`) + scene reload
(`0x469e8`/`0x45dfa`/`0x3b902`) + `0x13E` restore from the `0x13B8` checkpoint.

### Round completion is a DISTINCT transition
`FUN_0005122a` @`0x51250` sets `A5+0x10E8 := 16` when `A5+0x1360 == 1` (i.e. `0x13E` is a
`0x502AC` boundary `{16,2D,44,5B,72,89}`) **AND** `0x13ac == 8` **AND** `0x13ba == 128` — this is
boss-cleared / round-end, separate from the mid-round door wipe. `0x3a83a` handles `0x10E8==16`.
Round init `0x5053a` sets `0x10E8 := 3` (initial scroll phase).

### Per-round door 0x13E — EXACT POSITIONS BLOCKED (named, not fabricated)
The transition fires wherever a `0x7E` door tile sits in a round's collision map. The collision
grid `0x10DE00` is streamed from a per-column layout structure (`a2` via the `0x10D040` pointer
table, itself from the **runtime-populated** `0x10D000` 16-entry map-pointer table). The 16 ROM
column streams at `0x1691C + k*0x22C0` were checked and hold **visual name-table words**
(e.g. `0003 20fc 0003 1000…`), not the collision plane. Enumerating `0x7E` door positions per round
therefore requires decoding the collision-layout record format and locating the `0x10D000`
population — the named remaining static target. **No per-round door `0x13E` is asserted without
that decode; no screenshot is used as the phase authority.**

### Correlation with the TT background-bank map (evidence only)
Where a TT bank change is proven (R3 @0x36, R5 @0x6C/@0x72, R6 @0x83/@0x89) it *corroborates* a
scene reload — banks only change at a reload — so a door likely sits at/just before those `0x13E`.
But R1/R2/R4 stream a single bank while still crossing a gameplay phase, which is exactly why the
bank change cannot be the phase decoder. Boss↔round-boundary is proven 6/6; the mid-round P1/P2
door split is 0/6 *exactly* pinned pending the collision-layout decode.

## COLLISION-LAYOUT DECODE + A5=0x10C000 UNLOCK (this pass)

### A5 base resolved: A5 = 0x10C000 (arcade)
Verified three ways: `0x10C118` (round-intro index) = `A5+0x118` (round counter); `0x10C016` =
`A5+0x16` (player X); decisively **`0x10D0A8` (absolute) − `0x10C000` = `0x10A8`**, so the byte the
map-stream writes at `0x558f8` **is** `A5+0x10A8`. (The Genesis port relocates A5 to `0xFF2200`; the
original arcade base is `0x10C000`.) Consequences:
- `0x10D000` = `A5+0x1000`, populated by `0x502cc` = the 16 map-column stream pointers
  `base_k + 0x13E*64` (`base_0=0x1691C`, stride `0x22C0`), advanced `+4`/column while scrolling
  (`0x558c8`) and rebuilt into `0x10D040`(=`A5+0x1040`) by `0x55904`. These 16 streams are the
  **visual name-table columns**.
- `A5+0x10A8` (section-kind) = the current **map-stream byte** from ROM `0x50F6B`, indexed by
  `0x13E` through table `0x50EE0`.

### Section-kind stream `0x50F6B` — DECODED (values 0/1/2 only)
Per-`0x13E` scroll-mode marker (drives column-load direction at `0x556a6`/`0x55738`/`0x557c4`).
Non-zero markers per round: **R1** 0x11,0x15 · **R2** 0x2B,0x2C · **R3** 0x41,0x42,0x43 ·
**R4** 0x5A · **R5** 0x6E,0x70 (=2) · **R6** 0x85 (=2). These are scroll-mode flags near round
tails — **not** proven screen-wipe boundaries.

### The director `{4,5,6}` path is DEAD
`FUN_00052732` @`0x527cc` sets `0x10E8:=7` when `A5+0x10A8 ∈ {4,5,6}`. But `A5+0x10A8` is the
map-stream byte, which is only ever `{0,1,2}`. **So that path is never taken in normal play** — the
`0x7E` collision tile is the sole live screen-wipe trigger.

### Door tile `0x7E` is a METATILE PROPERTY (not runtime-written, not a raw stored cell)
No code writes `0x7E`/126 into the collision grid `0x10DE00` (=`A5+0x1E00`). The grid is built by
`0x559b2`/`0x55a14`, which write collision from a per-column record field `@(20 + col*2)`. The
record's collision-field-vs-visual-field layout and the per-round metatile-column source feeding
`@(20)` were **not** cleanly isolated statically: the streams' `word@+2` is a visual name-table
word (e.g. `0x1000`), not a record pointer, and naive record scans yield noise. `0x7E` is therefore
a metatile-property value in the map data.

### Exact blocker (unchanged in kind, sharpened)
Enumerating the `0x7E` transition tiles per round requires the **metatile→collision-property
mapping** plus the **per-round metatile-column source** that feeds collision-grid field `@(20)` —
a full map-engine decode. A runtime watchpoint on the `0x10DE00` door cell or on `0x53f0c` would
*corroborate* positions but is not the static authority. **No per-round door `0x13E` is asserted.**

### Metrics
- Generic `0x7E → wipe` mechanism: **PROVEN**.
- Rounds with actual Phase-1→2 boundary pinned: **0 / 6** (blocked).
- Boss present-in-round: **6/6 PROVEN**; boss route PCs individually decoded: **4/6** (R3–R6);
  R1/R2 boss route PCs not individually decoded (evidence = base-0x033E round-tail presence).
