# Collision-Map Grounding / Enemy Position Implementation

**Agent:** Cody  
**Task type:** Bounded automated last-writer proof, semantic correction, and gated candidate build  
**Baseline:** Build 0281  
**Accepted ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0281.bin`  
**SHA-256:** `8f4997566386f30c0c3dd37f922762d7f6b0677f8bbd9c4a8995046dfb9ab790`  
**Counter at task start:** 281  
**Status:** Implementation and automated candidate validation complete

## BASELINE

**PROVEN:** At the matched Stage-1 state (`scroll_y = 0x0149`), original arcade
grounding accepts collision row 38, candidate Y 128, and reconstructs actor logical Y
121. Build 0281 accepts row 39, candidate Y 136, and reconstructs logical Y 129.
The retained lookup and actor-grounding consumer are instruction-equivalent at this
boundary. They are not modified by this correction.

**PROVEN:** Build 0281 applies a render-only `-8` to every native `BACK_ENEMY`
piece. That hides the eight-pixel logical error visually while leaving actor logical Y
and the hurtbox anchor eight pixels too low.

All executable arcade/Genesis correlations use
`build/rastan-direct/address_map.json`. Runtime data pointers are labeled separately
and are not treated as executable-PC mappings.

## AUTOMATED CAPTURE METHOD

No user input was used. A durable MAME Lua tracer was created at
`tools/mame/scripts/collision_grounding_trace.lua`. It records monotonically ordered
collision-map writes, their complete 68000 register state, producer metadata, and the
first class-`0x17`/`0x18` actor-grounding acceptance. The same event schema was used
for Genesis and original arcade execution.

Genesis evidence:

`states/traces/build0281_collision_grounding_implementation_20260814_232600_frame_diff/`

- 593 external frames
- 296 ordered events
- controlled Stage-1 startup through the matched Lizardman grounding state

Original arcade evidence:

`states/traces/arcade_collision_grounding_implementation_20260814_225903_clean_controlled/`

- 702 external frames
- 327 ordered events
- clean isolated MAME configuration; no RAM seeding or gameplay-state forcing
- the isolated configuration was required because the persisted user DIP configuration
  required two coins

**PROVEN tracer correction:** In the original-arcade TSV, the old derived `cell` and
`source_offset` columns were wrong: the cell loop register is D2, not D5, and the
source formula is `0x20 + strip*2 + cell*8`. Full register dumps and executed
opcodes are authoritative. The durable tracer now reports that absolute offset for
both original and native selector publishers. Its
`overwritten` field now says `SEE_ORDERED_HISTORY`; a changed previous value does not
mean a later overwrite occurred.

## ROW 38 EVENT HISTORY

**Original arcade, matched column 39:**

- frame 486, event 247
- writer: `arcade_pc 0x0559EC`
- selector 0, segment 9, group 9, strip 3, cell 2 (D2)
- collision block: `arcade_rom/data 0x00002A88`
- source formula: `block + 0x20 + strip*2 + cell*8`
- source offset: `0x20 + 0x06 + 0x10 = 0x36`
- source/new word: `0x3A00`
- destination: collision row 38, column 39
- no later write to this cell before actor grounding

**Build 0281, matched column 39:**

- frame 343, event 231
- writer: generated helper `runtime_genesis_pc 0x0704F2`
- family: native selector-0 publisher
- selector 0, segment 9, group 9, strip 3, cell 2
- collision block: `runtime_data 0x00002C88`
- D0 source index: `0x0016`
- executed source access before correction: `block + decimal 20 + D0`, i.e.
  `0x14 + 0x16 = 0x2A`
- source/new word: `0x0000`
- destination: collision row 38, column 39
- no later write to this cell before actor grounding

**PROVEN:** The Build 0281 row-38 last writer is the native selector-0 helper at
`runtime_genesis_pc 0x0704F2`. It never publishes the original row-38 `0x3A00`
marker because it reads twelve bytes before the arcade-semantic source field.

## ROW 39 EVENT HISTORY

**Original arcade, matched column 39:**

- frame 486, event 248
- writer: `arcade_pc 0x0559EC`
- selector 0, segment 9, group 9, strip 3, cell 3 (D2)
- collision block: `arcade_rom/data 0x00002A88`
- source offset: `0x20 + 0x06 + 0x18 = 0x3E`
- source/new word: `0x0000`
- destination: collision row 39, column 39
- no later write before actor grounding

**Build 0281, matched column 39:**

- frame 343, event 232
- writer: generated helper `runtime_genesis_pc 0x0704F2`
- selector 0, segment 9, group 9, strip 3, cell 3
- collision block: `runtime_data 0x00002C88`
- D0 source index: `0x001E`
- executed source access before correction: `0x14 + 0x1E = 0x32`
- source/new word: `0x3A00`
- destination: collision row 39, column 39
- no later write before actor grounding

**PROVEN:** The same twelve-byte source-base error moves the exact marker selected by
the original event from semantic row 38 to row 39.

## ORIGINAL ARCADE PRODUCER EVENT

The original selector-0 producer is reached through the semantic producer rooted at
`arcade_pc 0x055968`. `address_map.json` maps that patched executable site exactly to
`runtime_genesis_pc 0x055B1E`; this mapping is JSON-derived, not `+0x200` arithmetic.
The generated native helper itself lives at `runtime_genesis_pc 0x07042A`, with the
observed write at `runtime_genesis_pc 0x0704F2`, and has no arcade-PC identity.

The original producer begins at `arcade_pc 0x0559B2`; its indexed normal-field
collision source instruction is `arcade_pc 0x0559CE`, encoded with displacement
`0x20`. Its normal-field collision access is therefore rooted at block offset `0x20`. The original
event reads `0x3A00` from block offset `0x36` and publishes it to row 38, column 39.

The original `arcade_rom/data 0x2A88` block and Build 0281 `runtime_data 0x2C88`
block are byte-equivalent under the generated data relocation. The authoritative
top-level `address_map.json` data relocation is `0x000200`. Direct ROM comparison also
confirms equivalence. The selected block is not the divergence.

## FIRST GENESIS DIVERGENCE

**PROVEN, category G (source-field interpretation):** Build 0281's native collision
publishers spell the normal field as `20(base,index)` in GNU assembler syntax. The
literal is decimal 20 (`0x14`), whereas the arcade instruction uses hexadecimal
`0x20`. The first divergence is the native helper's collision source-base
interpretation, before destination calculation and before the retained grounding
consumer.

**DISPROVEN:** wrong descriptor/block selection.  
**DISPROVEN:** correct row-38 publication later overwritten.  
**DISPROVEN:** retained collision postprocessor changed these cells.  
**DISPROVEN:** publication arrived too late.  
**DISPROVEN:** destination row arithmetic moved a correctly read word.

## ROOT CAUSE

The decimal/hex mistranslation subtracts `0x0C` from every normal-field collision
source address. Because collision words for successive cells are eight bytes apart,
the Stage-1 marker appears in the following semantic row. Three live native readers
contained the same defect:

- selector-0 Plane A publisher
- selector-1/2 Plane A publisher
- retained Stage BG collision-column helper

The alternate/sentinel path uses decimal offsets 32 and 34, which correctly represent
original offsets `0x20` and `0x22`; that path is unchanged.

## BACK_ENEMY PRODUCER SCOPE

**PROVEN static scope:** The live gameplay `BACK_ENEMY` actor families are staged by:

- `native_stage_dispatch_41dae`: nine records beginning at `A5+0x02C8`
- `native_stage_dispatch_45dfa`: six records beginning at `A5+0x05C8`

Both dispatch through `.Lnative_emit_actor_common`, which reproduces the original
piece semantics from actor logical Y (`A4+0x1A`) plus signed mapping Y, with the
original type-`0x70` adjustment from `A4+0x18`. These arrays can contain ordinary
map-grounded actors, marker-controlled actors, and airborne/non-ground actors, but all
share that original semantic composition contract. Projectiles, effects, and items use
other native lanes/producers.

No original BACK priority lane-wide `-8` exists. All SAT lanes already receive the
shared PC090OJ visible-origin conversion once in final SAT encoding. Therefore the
Build 0281 BACK_ENEMY `-8` is solely a KF-067 representation compensation and must be
removed globally when the collision source is corrected. A producer-specific offset
would remain valid only if proven in the original mapping tuple; none is added here.

## IMPLEMENTATION

The bounded correction is:

1. change the three normal-field native collision reads from decimal `20(...)` to
   hexadecimal `0x20(...)` in `apps/rastan-direct/src/tilemap_hooks.s`;
2. remove the four-instruction global BACK_ENEMY queue-Y subtraction in
   `apps/rastan-direct/src/pc090oj_hooks.s`;
3. retain the grounding lookup, actor logical-Y write, hurtbox computation, sword
   extents, player collision arithmetic, sentinel source path, and shared SAT origin
   conversion unchanged.

The first Makefile pass stopped before numbering at the canonical coverage invariant.
The measured opcode-replacement site count remained 228, while shift-table reflow after
retiring the eight-byte compensation changed total Genesis coverage from `0x1848E0` to
`0x184680` (exact delta `-0x260`). The mirrored constants in
`postpatch_startup_rom.py` and `verify_canonical_rom.py` were updated together. No ROM
was produced and the counter remained 281 on that mechanical pass.

No PC080SN/PC090OJ compatibility representation, actor-Y patch, hurtbox patch, sword
extent patch, fallback, or coordinate-specific workaround is introduced.

## COLLISION-MAP VALIDATION

**PROVEN:** The fully automated Build 0282 trace is:

`states/traces/build0282_collision_grounding_validation_20260814_final/`

At matched column 39:

- frame 343, event 250: generated selector-0 writer
  `runtime_genesis_pc 0x0704F2` reads absolute block offset `0x36` and writes
  `0x3A00` to Genesis-WRAM collision row 38;
- frame 343, event 251: the same writer reads absolute block offset `0x3E` and
  writes `0x0000` to row 39;
- no later event changes either matched cell before grounding;
- frame 493, event 326: class `0x18`, actor index 7, candidate Y 128 accepts row
  38 and resolves logical Y 121 with row38=`0x3A00`, row39=`0x0000`;
- frame 582, event 327 independently observes class `0x17`, actor index 6 with
  the same candidate, accepted row, logical Y, and collision words.

The trace ran 583 external frames with no memory or gameplay-state seeding.

## ACTOR LOGICAL / HURTBOX VALIDATION

**PROVEN:** Both class `0x17` and `0x18` Stage-1 actors resolve logical Y 121 after
the corrected publication. The retained normal actor hurtbox has original relative
Y extents `-20..+16`; because neither its table nor consumer changed, its absolute
Y interval is restored to `101..137`.

## VISUAL POSITION VALIDATION

**PROVEN at the final native queue boundary:**

`states/traces/build0282_grounding_sword_regression_20260814_231327/walk_attack_770/`

At frame 782, corrected BACK_ENEMY entries retain producer-semantic queue Y
`0x007A` without a lane subtraction. The representative bottom piece, code
`0x0066`, has screen/cell top 114 and bottom 129; its measured opaque bottom is also
129. Thus semantic actor Y changed from 129 to 121 while retirement of the old
render-only `-8` leaves the expected visible bottom at 129. The shared visible-origin
conversion remains applied exactly once by the common SAT encoder.

## SWORD COLLISION VALIDATION

**PROVEN with controlled P1 movement and attack input; no state forcing:**

- Standing frame 782: player anchor `(160,112)`, original selector 5 extents
  X `+24..+56`, Y `-10..-8`, yielding sword intervals X `184..216`, Y
  `102..104`. The matched actor anchor X 207 is inside the X interval and the
  restored actor hurtbox Y `101..137` overlaps the sword Y interval.
- Crouching frame 781: player anchor `(160,112)`, original selector 11 extents
  X `+24..+56`, Y `+4..+6`, yielding X `184..216`, Y `116..118`. The matched
  actor anchor X 213 is inside the X interval and Y overlaps `101..137`.

Standing overlap is X YES / Y YES. Crouching overlap is X YES / Y YES. The
original attack tables and extent consumers are byte-unchanged.

## PLAYER REGRESSION VALIDATION

**PROVEN with controlled input and no state forcing:** evidence is under
`states/traces/build0282_grounding_sword_regression_20260814_231327/`.

- Walking: P1 Right moves the player from X `0x0051` to `0x00A0` while ground Y
  stays `0x0070`; no fall-through, hovering, or eight-pixel displacement occurs.
- Crouch: the crouch attack remains at ground Y `0x0070` through the full sampled
  action.
- Jump/landing: `jump_landing/jump_frames.csv` records P1 C at frames 700..703.
  Action changes from grounded `1` to ascending `2`, reaches apex Y `0x004C`,
  changes to descending `3`, returns to ground Y `0x0070` at frame 762, and returns
  to grounded action `1` at frame 764. Y remains `0x0070` afterward.
- Ground contact: the bounded Stage-1 floor traversal and post-landing interval are
  stable; no immediate hazard/death, landing oscillation, or collision-induced
  position shift appears.

## NON-GROUND ACTOR VALIDATION

**PROVEN scope / runtime not automatically available in this bounded case:** The
complete caller audit proves that both live BACK_ENEMY arrays use the same original
actor-piece composition contract and that no lane-wide original `-8` exists. The
bounded automated Stage-1 interval naturally exposes grounded class `0x17` and
`0x18` actors only; hurry-up bats are a FRONT_EFFECT producer, not a BACK_ENEMY
consumer. Therefore the task's conditional airborne runtime check is N/A rather than
fabricated. Non-ground BACK producers retain their original semantic actor Y plus
mapping-piece Y, and the only removed operation is the unproven lane-wide
compensation.

## BUILD ACCOUNTING

- Candidate: Build 0282
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0282.bin`
- SHA-256: `61b2b1268362f309c64939c1a6d226df5a4a26a95f95b560071701266d694316`
- Size: 1,590,912 bytes
- Counter transition: 281 -> 282
- Rolling artifact byte-identical to numbered artifact: YES
- `GATE_PASS`: YES
- Mandatory MAME smoke:
  `states/traces/rastan_direct_video_test_build_0282_mame_30s_20260814_230901/`
- Smoke duration: 30 seconds; no unique unmapped-memory address reported
- Numbered Build 0281 preserved: YES
- Exactly one numbered candidate produced: YES
- Build 0281 sword source/tables preserved: YES
- Build 0280 auxiliary-array correction preserved: YES
- Shift-aware replacement continuation preserved: YES
- PC090OJ compatibility representation added: NO

All implementation and automated validation gates pass. Final pixel appearance and
interactive feel remain user-verification items; they are not used to weaken the
automated semantic result.
