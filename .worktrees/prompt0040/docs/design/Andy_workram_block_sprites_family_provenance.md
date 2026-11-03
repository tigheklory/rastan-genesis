# Provenance — `pc090oj_workram_block_sprites*` = the GAMEPLAY PLAYER sprite (Ghidra-first, arcade-authoritative)

**Agent:** Andy · **Type:** analysis/provenance (NO ROM, NO build number, NO source/spec change) · **Baseline:**
Build 0273 / counter 273. This supersedes my earlier draft of this file; it follows the Ghidra-first,
arcade-authoritative workflow and corrects an error I made by over-trusting a single Genesis runtime read.

## 0. Correction of my earlier claim (important)
My first pass used Genesis-runtime reads and then a literal-xref-only static check, and I wrongly concluded block
A was "tuple-0-only / near-vestigial, not the player." **That was wrong.** The literal-store absence did NOT mean
static provenance was blocked — there is a computed/register-passed writer, exactly as Tighe warned. Authoritative
**original-arcade MAME** confirms block A is the player body (below).

## 1. Authoritative facts

### Copier (arcade, Ghidra)
`FUN_00041f5e` (arcade **0x41F5E**), called by `FUN_00041f30` (0x41F30). It copies:
- block A = **a5+0x11B2, 18 tuples** `{word0,Y,code,X}` → **0xD003C0** (PC090OJ), via `FUN_00041f7a`.
- block B = **a5+0x170, 4 tuples** → **0xD002E0**.
Blank tuples (code 0) are parked (Y=0x180). a5 base = **0x10C000** ⇒ block A = 0x10D1B2, block B = 0x10C170.

### Block A = the PLAYER BODY (arcade MAME, authoritative dynamic)
Original arcade MAME (`rastan`), attract gameplay demo, dumping 0x10D1B2:
- frame 2640: 9 non-blank pieces, codes `9E 9F · 8E 8F 90 · 10B 10C 10D 10E`.
- frame 3200: codes `9E 9F · 8E 8F 90 · 7A 7B 7C 7D`.
These are player character tiles; the set changes with the animation frame ⇒ **animation/mapping-driven
multi-piece player body**. Block B was 0 in these windows (player front/weapon overlay — expected to populate in
attack/throw states; not yet captured).

### The builder is a computed sprite-engine writer (not a literal store)
- Literal/displacement xrefs into block A hit only: the copier (0x41F5E) and `FUN_0005288c` (arcade 0x5288C),
  which writes **only tuple 0** via `movea.l #0x10d1b2,A0` — a single fallback object at the player position
  (a5@0x1354=X, a5@0x1356=Y), word0 1/5, code 0/0x6E1, gated by a5@0x1296 / a5@0x1308 bit3.
- The 18-piece body is written by the arcade **sprite engine** through a register-passed output pointer
  (a1 = a5+0x11B2), so it never appears as a literal `0x11B2(a5)` store. The engine is the **type-dispatch
  `FUN_0003c902` / expander `FUN_0003c950`** family — the SAME engine Build 0260 converted for gameplay enemies.
  `0x3C902` is reached via thin wrappers `FUN_0003f0bc / 0003ffdc / 0003fff0 / 0004770e` (each just `jsr 0x3C902`);
  the caller of those wrappers sets `a0`=player actor and `a1`=a5+0x11B2. (`FUN_0003d054`, the other dispatch,
  is the 0x41DAE/0x45DFA path that writes OBJECT RAM directly — the already-native enemy path, a different output.)
- The 5 "builders" in `FUN_00041f30` (0x55ab4/0x45d72/0x5988c/0x59882/0x47004) are **palette animation + scroll**
  (e.g. `FUN_00059ad4` writes palette RAM 0x200000), NOT the sprite block builder.

## 2. Current Genesis translation (Build 0273)
- Gameplay (scene 1): `native_stage_player_blocks_41f5e` **reads the a5+0x11B2/0x170 tuples** → `native_sprite_emit`
  → native SAT. This is "native consuming the PC090OJ-format tuples" — the state the task wants replaced.
- Frontend (scene≠1): `pc090oj_workram_block_sprites*` reads the (frontend-empty) blocks → object RAM → scan.
- The Genesis a5 discrepancy I hit earlier (0xFF0000 read) is a candidate-side detail; the arcade is authoritative
  and settles the semantics.

## 3. Proposed semantic-to-PC090OJ cut (target)
    player actor (position a5@0x1354/56, animation frame, facing)
      -> player mapping/frame -> visible pieces (tile code + dx/dy + flip/palette/priority)
      -> native Genesis piece emission (as Build 0260 does for enemies)  -> staged SAT -> VBlank
Removes: the a5+0x11B2/0x170 PC090OJ-format staging buffer, the copier `0x41F5E`/`0x41F7A` → 0xD003C0/0xD002E0,
and the Genesis `workram_block_sprites*` / tuple-consuming `native_stage_player_blocks_41f5e`.
Keeps: the player game logic and the sprite-engine mapping data (consumed natively, not via the chip buffer).

## 4. What is still needed before implementing (the remaining provenance)
1. **Pin the exact builder call**: register-level trace up from the `0x3C902` wrappers to the caller that sets
   `a1 = a5+0x11B2` (and `a0` = player actor) — the arcade player-sprite-build site. (The engine is known; the
   specific player invocation + its actor/mapping inputs must be named.)
2. **Player mapping tables**: how the current animation frame selects the piece list (the source of codes
   9E/8E/10B/7A…), tile base, per-piece dx/dy, flip, palette, priority — same structure Build 0260 read for
   enemies, but for the player.
3. **Block B semantics**: capture an attack/throw state to confirm block B = player front/weapon and its builder.
4. **Priority/order**: player body vs front vs HUD vs other actors.

## 5. Implementability & risk
Architecturally the same as Build 0260's enemy conversion (same 0x3C902/0x3C950 engine), so it is implementable
in principle. But it is the **single most visible gameplay sprite**, animation-heavy, so it carries higher
regression risk and MUST be validated against arcade MAME per animation state. There is **no visual benefit** —
the value is removing the PC090OJ-format staging buffer — so correctness/validation discipline dominates.

## 6. Updated decision
The task premise is **CORRECT**: this family is the gameplay player sprite, and the current path consumes the
PC090OJ-format tuples (the thing to replace). My earlier doubt was wrong. The next step is completing item-4
provenance (builder call site + player mapping tables) via Ghidra register-level tracing (and arcade MAME only for
the block-B/attack dynamic question), then implementing the Build-0260-style native player piece expansion. No
build until the builder + mapping are pinned. Recommend proceeding with that focused Ghidra trace next.

---

# COMPLETED PLAYER PROVENANCE (this task — Ghidra-first + arcade-MAME, reusing tools/mame debugger harness)

Method note: used the established arcade debugger mechanism (`-debug -debuglog -debugscript` with
`wp/bp ...{ printf ...; go }`, the same pattern as `tools/mame/scripts/rastan_fu1_playtrace_debug.cmd`);
evidence under `states/traces/player_builder_provenance_20260809_000004/` (`.cmd` + `debug.log`). Original
arcade `rastan` only; no `megadriv`; no Genesis run; no source/spec/build.

## PLAYER BUILDER CHAIN
| Arcade PC | Function | Role | Inputs/registers | Output/next stage |
|---|---|---|---|---|
| 0x51500–0x51528 | frame sprite-build sequence | per-frame sprite prep | player state (a5) | series of `jsr` to builders |
| **0x5151C** | `jsr 0x540CC` | **player BODY build call site** | — | enters body builder |
| **0x540CC** | player body builder (entry) | state machine; reads a5@0x10E8 state, sets ROM mapping bases a2/a3/a4, clears block A (0x542E8), dispatches (0x54326) | a5 player state/frame/pos/facing | segment expanders |
| 0x54492 | segment expander (body core) | 4-piece expand → block-A tuples 4–7 | a1=0x10D1D2, table 0x5BD40, frame a5@0x1244 | writes block A |
| 0x546A8 | segment expander | 4-piece expand → tuples 8–11 | a1=0x10D1F2, table 0x5C466, frame a5@0x1246 | writes block A |
| 0x54536 / 0x5457A / 0x545BA | inline segment expanders | further segments; table state-selected | a1=0x10D1F2…, tables {0x5CD8A,0x5D068,0x5D356,0x5D666} by a5@0x12FA | writes block A |
| 0x5450E | (inside 0x54492 loop) | the write instruction wp-caught | a0=0x5BDD6 piece, a1=block A, d0=code | `move.w code,(a1)+` |
| 0x41F5E `FUN_00041f5e` | copier | block A→0xD003C0 (18), block B→0xD002E0 (4) | a5+0x11B2 / a5+0x170 | PC090OJ chip |
| 0x41F30 `FUN_00041f30` | frame finalizer | calls palette/scroll + copier | — | 0x41F5E |
| (Genesis) `native_stage_player_blocks_41f5e` | current translation | **consumes** block A/B tuples → SAT | a5+0x11B2/0x170 | staged_sprite_sat |

## PLAYER MAPPING PROVENANCE
| Semantic field | Arcade source | Table/address | How it is used |
|---|---|---|---|
| Player state (action) | a5@0x10E8 | WRAM | selects builder branch/segment set at 0x540CC/0x54326 |
| Sub-state | a5@0x1108/0x110A, a5@0x12F0, a5@0x12FA | WRAM | segment/table selection |
| Facing | a5@0x1114 | WRAM | `!=2` ⇒ set flipX 0x4000; negate X (`eori;+1;-16`) |
| Animation frame | a5@0x1244 (+a5@0x1246 sub) | WRAM | index into frame-pointer table (frame*2) |
| Frame→piece-list | ROM frame tables | 0x5BD40, 0x5C466, 0x5CD8A/0x5D068/0x5D356/0x5D666, 0x5B9E0/0x5BA10; bases a2=0x5B6A0 a3=0x5BA70/0x5BAB0/0x5BB40 a4=0x5BA78/0x5BAC8/0x5BB80 (range ~0x5B6A0–0x5D666) | `A0 = table + [table + frame*2]` = piece list |
| Piece count | code constant | — | `#4` pieces per segment (multiple segments per frame) |
| Per-piece record | ROM piece list | 6 bytes/piece | `code@0`, `attr@4`, `Xbyte@2`, `Ybyte@3` |
| Tile/code | piece@0 | ROM | written directly to tuple code field |
| Palette/attr | piece@4 | ROM | written to tuple word0 (`| 0x4000` flipX) |
| dx (X) | piece@2 (Xbyte) | ROM | `X = ext(Xbyte) [flip: ~+1 −16] + a5@0x10BE(playerX)` &0x1FF |
| dy (Y) | piece@3 (Ybyte) | ROM | `Y = ext(Ybyte) + a5@0x10C0(playerY) + 1` &0x1FF |
| Flip | a5@0x1114 | WRAM | flipX bit + X mirror |
| Visibility | piece code 0 | — | blank piece ⇒ park tuple (word0=3, Y/code/X=0) |
| Observed tile groups | 9E/9F, 8E/8F/90, 7A–7D, 10B–10E | in frame tables | different body segments/frames' piece codes |

## BLOCK B (a5+0x170)
| Action/state | Semantic object | Builder | Mapping source | Arcade dynamic proof |
|---|---|---|---|---|
| weapon/throw active | player WEAPON / projectile overlay | arcade ~0x59FDE–0x5A02A (wp writer 0x59FF6) | hand-built from a5@0x1388 (weapon type→codes 0xA68/0xA6C/0xA6D) + a5@0x140E (active; 255⇒blank); fixed pos (X 0xB0, Y 0xE8) | wp on 0x10C176 fired 714×; in observed attract (non-throw, state10E8=5) it wrote **blank** (d0=0) — consistent with inactive overlay; weapon codes proven from static decode. Full throw-state dynamic capture: NOT yet done (recommended at impl time). |

## PLAYER ORDERING
| Semantic family | Relative order (front→back) | Arcade evidence | Existing native destination |
|---|---|---|---|
| HUD | 1 (front) | — | NATIVE_LANE_HUD |
| FRONT_EFFECT | 2 | — | NATIVE_LANE_FRONT_EFFECT |
| **Player FRONT (block B)** | 3 | block B→0xD002E0 (rec 92) | **NATIVE_LANE_PLAYER_FRONT** (already assigned, src line 577) |
| MIDDLE | 4 | — | NATIVE_LANE_MIDDLE |
| **Player BODY (block A)** | 5 | block A→0xD003C0 (rec 120) | **NATIVE_LANE_PLAYER_BODY** (already assigned, src line 565) |
| BACK_ENEMY | 6 (back) | — | NATIVE_LANE_BACK_ENEMY |

Native ordering destinations already exist and are already used by `native_stage_player_blocks_41f5e`; no new
priority architecture is needed. Do not use PC090OJ record numbers as semantic ownership.

## EXACT SEMANTIC-TO-PC090OJ CUT
Cut inside the body builder `0x540CC` (and block-B builder ~0x59FDE): keep the arcade **state/frame/facing/
position decision** (a5@0x10E8/0x1114/0x1108/0x12FA/0x1244/0x10BE/0x10C0) and the **ROM mapping tables**
(0x5B6A0–0x5D666, weapon codes for B); replace the **PC090OJ-format tuple emission into block A/block B** with a
native segment/piece expander that reads the SAME ROM mapping/piece format and appends to the existing native
lanes (PLAYER_BODY / PLAYER_FRONT). Then retire block A/B buffers, the 0x41F5E/0x41F7A copy, and the Genesis
tuple-consumer `native_stage_player_blocks_41f5e`.

## IMPLEMENTATION READINESS
| Required fact | Status | Evidence |
|---|---|---|
| Exact player builder invocation | PINNED | jsr 0x5151C → 0x540CC (debug.log return chain) |
| Player actor input | PINNED | a5 player fields (0x10E8/0x1114/0x1108/0x12FA/0x1244/0x10BE/0x10C0) |
| Frame-selection path | PINNED | a5@0x1244 → table[frame*2] → piece list |
| Mapping tables/formats | PINNED (format), tables located; per-state table set partially enumerated | disasm 0x54492/0x546A8/0x54536; tables 0x5B6A0–0x5D666 |
| Tile derivation | PINNED | piece@0 |
| dx/dy | PINNED | piece@2/@3 + player pos |
| Flip | PINNED | a5@0x1114 |
| Palette/attr | PINNED | piece@4 → word0 |
| Priority | PINNED | existing native lanes |
| Block B semantic owner | PINNED | 0x59FDE weapon overlay |
| Block B dynamic behavior | PARTIAL | static weapon-code decode; throw-state capture recommended |
| Native ordering destination | PINNED | PLAYER_BODY / PLAYER_FRONT lanes exist |
| Semantic-to-PC090OJ cut | PINNED | above |

**READY for native implementation: YES** — with two implementation-time validations (not new provenance):
(1) capture a throw/attack state to visually confirm block-B weapon pieces; (2) enumerate the remaining
per-state segment→table→tuple-range combinations as each state is implemented, validating against arcade MAME.
The mapping FORMAT is fully decoded, so no further provenance investigation is required to begin implementation.

---

# IMPLEMENTATION SPEC — main-loop native PLAYER_BODY/FRONT staging (turnkey; architecture confirmed by Tighe)

**Architecture (confirmed):** `arcade main-loop semantic decision (0x540CC / block-B) -> append FINAL native
pieces to NATIVE_LANE_PLAYER_BODY / PLAYER_FRONT -> VBlank finalizer commits SAT`. No re-invoke of 0x540CC at
VBlank; no PC090OJ-record buffer; the native lanes ARE the target-shaped staging.

## Proven frame lifecycle (arcade MAME + call graph)
- BODY producer: `jsr 0x540CC` at **0x5151C** — fires **exactly once per frame** (debugger: ret=0x51522, one per
  VBlank), in the main-loop sprite sequence 0x5150C..0x51538.
- FRONT/weapon producer: `jsr 0x59F92` at **0x51060** (block-B entry 0x59F92 tests a5@0x1388==255 → blank).
  **0x51060 precedes 0x5151C** in the same once-per-frame main-loop routine ⇒ FRONT is produced BEFORE BODY.
- VBlank commit: `0x41F5E`/`0x41F64` from the Level-5 handler 0x03A008, once per frame, AFTER the main-loop build.
- **Reset point:** immediately BEFORE 0x51060 (before both FRONT and BODY), once per frame. Inject a call to
  `native_player_frame_begin` there (find the highest safe insn just before 0x51060 in the same routine).

## Native helpers (add to pc090oj_hooks.s)
```
native_player_frame_begin:            /* main-loop, once/frame, before 0x51060 */
    clr.w   native_player_body_count
    clr.w   native_player_front_count
    rts
/* map arcade loop regs -> native_sprite_emit, preserving the loop counter d2.
 * caller sets d1=word0, d6=Y, d3=code, d4=X, native_sprite_lane. */
native_player_piece:
    move.w  %d2, -(%sp)
    move.w  %d6, %d2
    bsr     native_sprite_emit        /* preserves d0-d7/a0-a2; appends to lane */
    move.w  (%sp)+, %d2
    rts
```

## Output-site patches (spec `shift_replacements`, variable-length reflow via shift_table_patcher)
For EACH BODY expander piece-loop (0x54492's loops at 0x544C8, 0x5457A, 0x545BA; the 0x546A8 loop) redirect the
four `move.w …,(a1)+` writes to registers and append a `jsr native_player_piece` (blank path emits nothing):
- word0 `32C0` (`move.w d0,(a1)+`) → `3200` (`move.w d0,d1`)
- Y     `32C0`                    → `3C00` (`move.w d0,d6`)
- code  `32E80000` (`move.w a0@,(a1)+`) → `36280000` (`move.w a0@(0),d3`)
- X     `32C0`                    → `3800` (`move.w d0,d4`)  then INSERT `4EB9{native_player_piece}` before `adda #6,a0`
  (shift_delta = +6; shift_table reflows the rest of the loop + fixes the `bne .loop` displacement).
Blank path (`move.w #3,(a1)+; move.w #0,(a1)+ ×3`) → replace with `bra` to loop-continue (emit nothing).
Set `native_sprite_lane=#NATIVE_LANE_PLAYER_BODY` at 0x540CC entry (prepend `move.w #…,native_sprite_lane`).

BLOCK-B (FRONT) at ~0x59FDE–0x5A02A: identically redirect its `(a0)+` piece writes → `native_player_piece` with
`native_sprite_lane=#NATIVE_LANE_PLAYER_FRONT` (set at 0x59F92 entry); the arcade already computes code
(0xA68/0xA6C/0xA6D) + fixed X/Y — feed those to d1/d6/d3/d4.

Confirm each loop's exact per-piece register/format from `linear_disassembly.tsv` before authoring bytes; the
0x544C8 loop is fully transcribed above (Y=piece@3+a5@0x10C0+1; X=piece@2 [flip: ~+1−16] + a5@0x10BE; word0=piece@4
| 0x4000-if-facing≠2 via a5@0x1114; code=piece@0).

## VBlank + retirement (source, after the above land)
- `native_sprite_frame_begin`: REMOVE `clr.w native_player_front_count` / `clr.w native_player_body_count` (now
  main-loop owned); keep the other lane clears.
- `genesistan_pc090oj_hook_target_41f5e` (gameplay branch): REMOVE `bsr native_stage_player_blocks_41f5e` (player
  already staged in the main loop); keep `native_sprite_frame_begin`/finalize path.
- Delete `native_stage_player_blocks_41f5e` and the player-family handling in `pc090oj_workram_block_sprites*`;
  the arcade a5+0x11B2/0x170 writes are gone (loops emit native), so the 0x41F5E player copy is inert — retire it
  at the hook boundary. Preserve any unrelated 0x41F5E behavior (block-B copy path shares it — cut only player).
- Order preserved by the existing finalizer: HUD > FRONT_EFFECT > PLAYER_FRONT > MIDDLE > PLAYER_BODY > BACK_ENEMY.

## Validation plan (per Tighe: no new harness, no dual renderer)
- Static: prove every live player-state path in 0x540CC reaches only the converted output sites (no other block-A
  writer); reset proven once/frame before both producers (above).
- Arcade MAME (existing debugger tooling): representative BODY across attract states; drive/observe an attack that
  activates block-B for FRONT.
- Genesis NTSC (`genesis`, not `megadriv`): candidate player renders across attract gameplay; HUD/ROUND-READY
  intact; enemies unchanged.
- USER MUST VERIFY (interactive): idle; walk L/R; jump/fall; face L/R; sword attack; weapon/throw FRONT; take
  damage; death; BODY/FRONT layering vs enemies/effects; HUD; ROUND/READY transition; no missing/flicker pieces;
  no palette regression.
