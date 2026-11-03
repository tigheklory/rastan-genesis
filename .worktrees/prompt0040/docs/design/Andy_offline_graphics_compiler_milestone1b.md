# Andy — Offline Graphics Compiler, Milestone 1B

**Type:** compiler decoder-completion. No production runtime change, no ROM, Build 0302 not consumed.
Continues `tools/translation/compile_pc080sn_genesis.py`.

## Honest summary
Of the four gaps, **one is fully closed with a real, verified decoder (Stage-1 scope)**; the other three
(real Plane-B stream, arcade palette colours→CRAM, PC090OJ static coexistence) are **deep arcade-RE decoder
tasks that are not yet closed** — each is precisely identified below with the exact missing arcade structure
(per the task's "identify the relationship rather than invent" rule). I did **not** fabricate decoders for
them. Therefore **READY FOR THIN RUNTIME INTEGRATION = NO.**

## Gap 1 — Stage-1 boundary: **CLOSED (real, verified)**
The seed table `0x50EE0` assigns each segment its DIRECTION-byte offset and **skips event bytes** (deltas +1
pure-direction, +2 for `[direction,event]` records). The ring-cycle walk of `a5@0x10C6` therefore lands on
the first event byte at stream **offset 16 (value 4)** — the stage boundary (`map_stream_format.md` §2a:
every event is a stage boundary). The compiler now enumerates Stage 1 as **exactly segments 0–15** from
arcade data (no "stop after N", no trace). Result: **23 → 7 epochs**, peak VRAM **611/640**, patterns
246,912 → **64,960 B**, self-validation PASS, reproducible byte-identical, 0 trace inputs.

Updated hard results (M1 → M1B): epochs 23→7 · Plane-A peak 579→**552** · combined 638→**611**/640 · largest
transition 537→**408** patterns / **13,056 B** · avg transition **290** · largest LUT patch 940→**722**.

## Gap 2 — real per-epoch Plane-B: **NOT CLOSED — exact missing decode identified**
Plane B is driven by the tm0 descriptor `0x3951C` (index 0 during Stage 1 → source blocks `0xD11C…`). The
existing `collect_block_scene_tiles` decodes the **whole-stage** BG (~854 tiles), not a per-epoch/scroll
working set — and 854 does not fit as a constant (confirming both planes must stream). **Missing static
decode:** the Plane-B tilemap **column→tile layout and the scroll-position→visible-window mapping** that
yields the per-epoch BG tile set (analogous to the FG strip-source walk). Until that decoder exists, M1B
keeps Plane A fully compiled and a **bounded 320-slot Plane-B reserve** (placeholder). Closing this needs the
BG source-layout decoder, then co-allocation of the *actual* simultaneous A+B sets.

## Gap 3 — arcade palette colours → Genesis CRAM: **NOT CLOSED — source located, decode incomplete**
The compiler emits palette **line routing** from `palette_decisions.json` (2 proven/decided rows) but **not
CRAM colour words**. The arcade colour source is *referenced* (registry `palette_source` cites gameplay banks
0x33/0x36 "staged through the sprite-palette source buffer"; project has `tools/ghidra/FindPaletteCallers.java`
+ `palette_callers.txt`). **Missing static decode:** the **arcade palette-RAM population path** — which ROM
table(s) hold the PC080SN/PC090OJ bank colour words, the bank-index arithmetic, and the arcade-9bit→Genesis-
9bit colour conversion. `palette_decisions.json` remains the policy authority (how banks map to lines); the
ROM must still be decoded for *what the colours are*. Not yet decoded → CRAM colour contents remain
`DECODER_SEMANTICS_UNPROVEN`.

## Gap 4 — legal PC090OJ sprite coexistence: **NOT CLOSED — model absent**
The compiler routes known sprite banks (registry) but has **no static model of which sprite palette families
can legally coexist per epoch**. **Missing static decode:** the Stage-1 **object/enemy placement/spawn tables
and the object-availability↔map-position relationship** in the arcade ROM (the level-progression/enemy
subsystem `map_stream_format.md` §6 flags as out of scope/unresolved). Deriving legal coexistence — not
"what a trace spawned" — requires decoding those object tables. Absent → sprite coexistence and the full
4-line shared-CRAM feasibility solve remain `DECODER_SEMANTICS_UNPROVEN`.

## Validation / reproducibility / independence
Self-validation **PASS** (no slot collisions; Plane-A stays below `SPRITE_TILE_BASE=1024`; every resident
code has a pattern). Deterministic rebuild **PASS** (byte-identical). Production trace dependencies **0**
(the tool reads only `build/regions/{maincpu,pc080sn}.bin` + `specs/palette_decisions.json`). Build target
`make -C apps/rastan-direct pc080sn-compile`. Generated docs: `docs/generated/pc080sn_genesis/stage1_epochs.md`.

## Why runtime is not ready
Wiring the runtime now would drive the screen from an incomplete model: no real Plane-B tiles, no CRAM colours
(the exact Build-0301 wrong-palette symptom), and no sprite-CRAM contention solve. The remaining work is
**three static decoders** (Plane-B layout; palette-RAM colour source; PC090OJ object/spawn tables), each a
bounded arcade-RE task. These are honest gaps, not placeholders papering over unknowns.
