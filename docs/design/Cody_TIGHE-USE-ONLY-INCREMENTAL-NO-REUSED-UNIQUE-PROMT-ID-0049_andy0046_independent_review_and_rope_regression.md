# Independent review of Andy 0046, R1-S2 upward scrolling, and rope regression

Identifier: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0049`

Agent: Cody
Reference ROM: Build 0525
Assignment: read-only peer review and engineering recommendations
Result: no implementation, generated asset, trace, save state, ROM, or build-counter change

## 1. Executive verdict

The strongest new result is that Andy 0046's leading R1-S2 diagnosis is built on a swapped scroll-field
definition. Original arcade `$055AB4` commits `A5+$10B0` to PC080SN foreground **Y** at `$C20002` and
`A5+$10AE` to foreground **X** at `$C40002`. Andy instead calls `$10AE` foreground Y. Consequently:

- the R1-S2 record-16 `$0160` initializer is foreground/background **X**, not Y;
- foreground Y begins at `$0000`, not `$0160`;
- `$055696/$05572E` are the foreground-Y arms and set direction values 0/1;
- `$0557BA/$055854` are foreground-X arms and set direction values 3/2;
- the claimed proof that the climb begins in Y rows 32–63 is contradicted.

The arcade's logical foreground is 64 rows and Genesis Plane A is physically 32 rows, but that dimension
difference is not itself defective. Build 0525 resolves the complete logical row identity 0–63 before
projecting it to `logical_row & 31`, maintains a 32-consecutive-row resident window, and publishes a newly
required row before the matching VBlank scroll commit. Thirty-two consecutive values modulo 64 map
bijectively to 32 physical rows, so no two simultaneously required rows collide. A 64×64 Genesis plane is
neither proved necessary nor compatible with the current VRAM layout.

The P0 cause remains **UNRESOLVED**, but the selector/source-path hypothesis from PROMT-ID-0045 remains the
best-supported target for the first independent capture. Scene/checkpoint replay and incremental scrolling
do not share one source rule: records 17 and 21 can use precompiled selector-1 rows, while records 18–20
fall through the live selector-0 resolver. This path sequence can explain correct spawn/respawn, wrong
middle ascent, and later realignment. It is not root-cause proof until an original-arcade and Genesis capture
identifies the first mismatched world cell.

The rope regression is **PROVEN** as elapsed gameplay frames: the accepted Build 0472 benchmark is 795,
Builds through 0503 preserve 795, Build 0517 records 796, Build 0519 records 799, and Build 0525 preserves
799. The runner and Lua route have not changed since their introduction. The cause is **UNRESOLVED** because
existing receipts contain only the semantic start and final attachment timing, not intermediate events.
This is not presently proof of CPU slowdown.

For the armored-man screenshot, Andy's signed-coordinate and state-specific-layout explanation is now the
leading **SUPPORTED HYPOTHESIS**. Resource pressure remains plausible for missing pieces, but the 12-cell
DMA worklist, 49 resident cells, SAT-80 limit, and per-line limit omit pieces; they do not by themselves
move surviving pieces downward. The first bad-frame piece-list/SAT comparison will distinguish these.

## 2. Evidence method and architecture boundary

Existing project tools reused:

- canonical Ghidra exports under `analysis/ghidra/rastan_arcade/exports/`;
- `build/maincpu.disasm.txt` and `build/regions/maincpu.bin`;
- maintained arcade C under `analysis/decompilation/c/`;
- Build-0525 production source in `apps/rastan-direct/src/`;
- existing R1-S2 captures under `states/traces/prompt0044_build0525_*`;
- unchanged rope runner, Lua route, summaries, and historical reports under `tools/mame/` and
  `states/traces/`;
- current Palette Composer policy, corpora, manifests, coverage report, and canonical
  `specs/palette_decisions.json`.

New tooling created: **none**.

Why new tooling was necessary: **not applicable**. A future synchronized capture is recommended but was not
created because this assignment forbids new trace artifacts.

For any later PC080SN correction, the semantic cut is the retained arcade decision that a camera crossing
requires a particular entering logical row/column from current descriptor, selector, and camera state. The
native tail must emit final Genesis Plane A/B words. The tail to retire is the complete PC080SN
chip-address/name-RAM row or column walk below that decision. No 64×64 shadow, tall projection, or generic
chip translator is proposed.

For any later PC090OJ correction, the cut is retained actor state plus selected frame/piece semantics to
final SAT pieces. The tail to retire is PC090OJ record construction/decoding. No object-RAM mirror is
proposed. No new transitional compatibility is recommended for either subsystem.

## 3. Confirmed Andy 0046 findings

### 3.1 PROVEN

- The original PC080SN name space provides 64 logical rows; scroll arithmetic is nine-bit and wraps at
  512 pixels.
- Genesis gameplay Plane A is configured 64×32 (`reg16=$9001`) and `staged_fg_buffer` contains 2,048
  words.
- Row/column source state advances through the retained strip/group and descriptor rebuild machinery;
  `$0558A2/$0558C6/$055904` are relevant to that progression.
- Scene initialization at `$0504FA` consumes a 12-byte, six-word record and initializes paired foreground
  and background camera fields.
- The R1 boss body base `$061D`, compositor 1, and boss palette pool 11 have source support.
- Multi-piece arcade sprite layouts use signed offsets and state/type-specific coordinate behavior. Those
  facts are relevant to the instance-specific armored presentation defect.
- R1-S3 lacks complete Palette Composer contexts for sprites and Plane A/B.
- Gray borders are a Genesis backdrop/CRAM presentation issue, not missing castle artwork.

### 3.2 SUPPORTED HYPOTHESIS

Andy's recommendation to compare original arcade world rows against Genesis staging/VRAM at a matched
camera state is sound. It agrees with PROMT-ID-0045 that a compiler product cannot independently validate
itself.

## 4. Unsupported or contradicted Andy 0046 findings

### 4.1 CONTRADICTED — `$10AE` as foreground Y

The original instructions at `$055AB4` are definitive:

| arcade PC | instruction | ownership |
|---:|---|---|
| `$055AB4` | `move.w (A5+$10EE),$C20000` | background Y |
| `$055ABC` | `move.w (A5+$10EC),$C40000` | background X |
| `$055AC4` | `move.w (A5+$10B0),$C20002` | foreground Y |
| `$055ACC` | `move.w (A5+$10AE),$C40002` | foreground X |

This matches `tilemap_hooks.s` constants and older original-arcade/Genesis proofs, including Andy's own
Build-0246 report. Andy 0046 reverses X and Y.

### 4.2 CONTRADICTED — R1-S2 starts at Y=`$0160`

Record 16 at original ROM `$050910` contains:

`0160 0000 00A0 0100 0078 0080`

`$0504FA` assigns the first word to `$10AE/$10EC` and the second to `$10B0/$10EE`. Therefore initial
foreground X is `$0160` and initial foreground Y is `$0000`. `$0160` cannot support a claim that the
initial viewport already occupies the high half of the vertical ring.

### 4.3 CONTRADICTED — direction 2/3 as vertical

`$055696/$05572E` update `$10B0` and write `$13D0=0/1`; those are the Y arms. `$0557BA/$055854` update
`$10AE` and write `$13D0=3/2`; those are the X arms. Andy 0046 assigns 2/3 to vertical streaming.

### 4.4 CONTRADICTED — 32 physical rows inherently cannot represent the climb

The current implementation deliberately separates logical resolution from physical placement:

1. logical rows remain 0–63;
2. visible residency is tested against a 32-row logical window;
3. only then is the destination reduced to `row & 31`;
4. VSRAM carries the live nine-bit scroll transformation.

This is standard streamed-ring behavior. The dimension difference alone proves neither stale exposure nor
wrong tenant data.

### 4.5 UNRESOLVED — realignment attributed to returning to Y<256

No existing natural capture shows the record/selector/Y value at the first bad frame or at realignment.
Because the `$0160` premise is X, the proposed low-half/high-half explanation has no current evidence.

### 4.6 CONTRADICTED by corrected user scope — wizards in R1-S2

Tighe confirms that wizards occur only in later rounds. They are excluded from this Round-1 inventory.
Andy correctly failed to establish a source identity, but the follow-up must not search R1-S2 for one.

## 5. Verified arcade scroll-field definitions

### 5.1 PROVEN field ownership

| field | proven role | exact evidence |
|---|---|---|
| `A5+$10AE` | foreground X | `$05050E`, `$055832/$05583E`, `$055880/$05588C`, `$055ACC` |
| `A5+$10B0` | foreground Y | `$050518`, `$05570C/$055718`, `$055798/$0557A4`, `$055AC4` |
| `A5+$10EC` | background X | `$050512`, `$055B92/$055BB0`, `$055BC2/$055BE6`, `$055ABC` |
| `A5+$10EE` | background Y | `$05051C`, `$055B28/$055B2C`, `$055B32/$055B36`, `$055AB4` |

The background Y field is copied from foreground Y by `$055B28/$055B32` when the corresponding retained
flags allow it. Background X is updated at half-rate using `$10D8` and the `$10F0` remainder in
`$055B3C/$055BB6`.

### 5.2 PROVEN record initialization

`$0504FA` indexes `scene_scroll_table_50850` by `record*12` and assigns:

1. word 0 -> foreground/background X (`$10AE/$10EC`);
2. word 1 -> foreground/background Y (`$10B0/$10EE`);
3. word 2 -> `$10B8`, the X-arm accumulator/limit companion;
4. word 3 -> `$10BA`, the Y-arm accumulator/limit companion;
5. word 4 -> `$10BE`, player/camera X companion;
6. word 5 -> `$10C0`, player/camera Y companion.

Current Genesis staging in `item_native.s` and the scroll commit in `vdp_comm.s` use the same X/Y labels.

## 6. Bottom-left spawn and upward-traversal coordinates

### 6.1 Initial viewport — PROVEN

The R1-S2 record-16 camera is X=`$0160`, Y=`$0000`. Under the established native/original projection:

`visible_top = ((-Y + 8) & $1FF) >> 3`

the initial logical top is row 1, and the 32-row resident window is rows 1–32. This is compatible with
Tighe's bottom-left **world** spawn: the wrapped logical-map origin, screen/world origin, and player's
geometric starting corner are not the same concept.

### 6.2 Upward movement — PROVEN in stored/ring coordinates

The Y up arm at `$05572E` subtracts `$10DA` from `$10B0` modulo 512 at `$055798..$0557A4`. Because the
display projection negates Y, that subtraction advances `visible_top` through increasing logical row
numbers. At a crossing, the current native path publishes `(new_visible_top+31)&63` to that logical row's
physical `&31` slot. The symmetric backtracking arm at `$055696` adds the delta and publishes the new top
row.

Thus increasing logical row number must not be called “moving downward in the level.” The hardware uses a
negated, wrapped scroll convention. In logical resident-window terms, the climb fetches the next row at the
far entering edge of the 32-row window; in Tighe's world geometry that edge is the newly exposed upward
castle content.

### 6.3 Native-origin assessment — SUPPORTED HYPOTHESIS

No current formula hard-codes a top-left spawn. It derives old/new logical top from live `$10B0`, preserves
the nine-bit wrap, and chooses a physical slot only after the logical row exists. However, the dynamic
selector-0 resolver derives source pointers from the live rebuilt tables and ring front, whereas selector-1
uses an offline record row. A bottom-starting climb makes any wrong record/front phase visible immediately
after the relevant transition even though a complete spawn replay can look correct.

Downward backtracking is a required discriminator. A source-front error may follow a different descriptor
phase in reverse; a pure physical/VSRAM phase error should reproduce symmetrically at the same logical
boundary.

## 7. Competing R1-S2 scrolling hypotheses

| classification | hypothesis | evidence and prediction |
|---|---|---|
| **SUPPORTED HYPOTHESIS** | split incremental source rules / record-front phase | Records 17/21 can use compiled selector-1 rows; 18–20 use the dynamic resolver. Predicts first wrong world cell at a source-path/record transition and possible realignment when selector-1 returns. |
| **CONTRADICTED as stated** | a 32-row plane cannot represent rows 32–63 | Current logical-first, physical-last ring is sufficient; no simultaneous collision is shown. |
| **UNRESOLVED** | physical row or VSRAM publication timing | Remains possible only if staging has the correct world row but the displayed physical row differs or is exposed early. |
| **UNRESOLVED** | selector-1 compiler origin/axis error | Existing selector-1 gate compares against the same compiler product. Predicts a mismatch while still in record 17. |

The two meaningful defect classes could coexist: a wrong logical source could be compounded by a physical
publication error. The smallest separating observation is one first-divergence frame containing the original
arcade world cell, Genesis staged cell, actual VDP cell, and displayed VSRAM.

The correct/wrong/correct sequence is presently explained best as follows:

- spawn/respawn is correct because the full replay reconstructs the resident window after final camera
  initialization;
- ascent can become wrong because incremental row publication changes source rule or descriptor/front phase;
- later content can realign when the producer returns to a source rule whose record map agrees with the
  arcade, or after a record transition reconstructs the expected phase.

This is a supported explanation, not a proven first bad record.

## 8. Is Genesis 64×32 Plane A sufficient?

### 8.1 PROVEN sufficient in capacity

Yes. Every visible R1-S2 viewport needs fewer than 32 tile rows, and the implementation deliberately keeps
32 consecutive logical rows. For any logical top `t`, the set `{t..t+31} mod 64` maps one-to-one through
`row&31`; no two members collide. Row 1 and row 33 share a physical slot, but they are never both members of
the same 32-row window.

The current code selects the complete logical identity before modulo placement and marks the entering row
dirty before normal VBlank publication. Existing record-17 evidence shows staging and VDP agree for reached
rows, although it does not prove arcade world-coordinate fidelity.

### 8.2 CONTRADICTED recommendation — promote Plane A in place to 64×64

At Plane A base `$E000`, a 64×64 name table needs 8 KiB and would extend through/wrap past `$FFFF`. It would
overlap the SAT at `$F800` and horizontal-scroll table at `$FC00`. Avoiding that requires a VRAM-layout
redesign and relocation of other owners. It also doubles a full Plane-A seed from 4 KiB to 8 KiB and expands
clear/initial DMA work. None of that repairs a wrong logical source selection.

A larger plane should not be considered unless a matched capture proves that more than 32 distinct logical
rows must coexist, which current hardware visibility and source do not support.

## 9. Independent arcade-versus-Genesis comparison requirements

Existing screenshots are authoritative visual reports but are not frame-matched. This review labels them:

- **Tighe series A:** original arcade 320×232 Round-1 progression/castle architecture;
- **Tighe series B:** Genesis/BlastEm castle traversal frames;
- **Tighe screenshot C:** simultaneous normal and corrupted armored men;
- **Tighe maps D:** 512×512 structural reference images.

Series A/B establish a visible mismatch through floors, windows, arches, openings, and flame stands. They do
not contain matched camera fields, records, or frame IDs, so a pixel overlay would overclaim.

The later authorized capture must sample ORIGINAL ARCADE and GENESIS NTSC at the last correct and first
wrong frame, including natural record boundaries 17→18 and 20→21. Record:

- `$013E`, `$10A8`, `$10CA/$10CC`, `$10B0`, `$10AE`, `$10EE/$10EC`, `$10DA`, and displayed scroll;
- all 16 descriptor/source pointers plus rebuilt tile/attribute tables;
- original PC080SN names for the entering row and visible window;
- Genesis logical source selection, staged row, dirty bit, actual VDP Plane A row, LUT, and VRAM patterns;
- landmark screen coordinate and normalized world `(logical row,column)`.

The first tuple where arcade and Genesis select different world coordinates is the P0 divergence. If source
coordinates match but VDP/display differs, the defect is physical publication/timing.

## 10. Rope 795→799 regression

### 10.1 PROVEN measurement and benchmark identity

The accepted reference is Build 0472 `_invincible`: four trials at 795 frames. Builds 0477, 0484, 0486,
0488, 0492, 0495, 0499, 0500, 0502, and 0503 also record 795. Available later receipts are:

| build | start frame | attach frame | elapsed | final semantic tuple |
|---:|---:|---:|---:|---|
| 0517 | 386 | 1182 | 796 | record 3, state 4, X `$00A7`, Y `$0000` |
| 0519 | 387 | 1186 | 799 | same |
| 0525 | 410 | 1209 | 799 | same |

The absolute start shift is excluded by the elapsed calculation. The shell runner and Lua route have no
post-introduction Git changes. Each uses GENESIS NTSC MAME, no video/sound, no throttle, the `_invincible`
variant, the same coin/start timing, continuous Right after semantic start, and the same first state-4 rope
endpoint.

### 10.2 UNRESOLVED cause

No existing receipt identifies the first differing gameplay frame. Build 0517's checkpoint lifecycle work
is the first available post-0503 standard result and is +1, but intermediate builds were not measured on a
valid comparable route; causation cannot be assigned to 0517. Build 0519 is +3 relative to 0517 and enables
authored scene palette/profile outputs, but that correlation does not prove palette work delayed gameplay.
Build 0525's Plane-A replay changes preserve the 799 elapsed result rather than adding another regression.

Plane A presentation should not alter retained movement/collision timing, but added producer work could only
be called causal if it changes an arcade frame boundary, VBlank completion, or a gameplay read. The benchmark
measures elapsed emulated frames, not CPU cycles, host speed, or direct VBlank overrun.

### 10.3 Minimal later comparison

Run one deterministic observation-only comparison each for a known-795 ROM (prefer accepted 0472 and last
measured 0503), 0517, 0519, and 0525 using the existing route. Add a per-frame event table only; do not alter
input or endpoint. Capture:

- semantic start and every player state transition;
- player world/screen X/Y, velocity, record, `$10B0/$10AE`, and collision result;
- rope actor/materialization state and the first attachment predicate;
- arcade-frame/VBlank count and existing VBlank timing counters;
- input field value actually sampled by retained code.

Find the first semantic tuple divergence, then bracket it with existing address-map-resolved PCs. Only if the
tuples remain identical while a frame is inserted should cycle/VBlank-overrun measurement follow. Restore
795 only by repairing that proven semantic or scheduling divergence; do not change the endpoint, motion, or
rope attachment rule.

## 11. R1-S2/R1-S3 Sprite and Composer inventory reconciliation

### 11.1 R1-S2 — PROVEN gaps

Current scene coverage is `SCHEDULE_ONLY`. It does not contain a complete scene-tagged live actor/frame/cell
vocabulary. `$0A73` is proven for state-`$0F` death/impact presentation with compositor 2; it is not proven
as the walking armored actor's live base. `$0A5A` is a later reward/death transformation. PROMT-ID-0045's
wording that these bases identify the armored men generally was too broad and is corrected here.

Wizards are out of scope because Tighe confirms none occur in R1-S2. The later implementation must close the
actual castle roster from marker/materialization flow and distinguish actor identity, live base, selector,
compositor, piece stream, death/effect transformation, and effective palette bank.

### 11.2 R1-S3 — PROVEN available and missing data

- Plane A already has a 219-use record-22 corpus using source banks `$008/$019`.
- No R1-S3 authored Plane-A production context exists in `Test.json`.
- Plane B has no Composer authoring surface; Line 2 remains arcade-owned.
- Boss body `$061D`, compositor 1, and source palette pool 11 are supported, but a complete boss-room actor,
  projectile/effect, player/weapon, and palette inventory is absent.

### 11.3 Later implementation plan

Derive a new uniquely named profile from `Test.json`; never overwrite it. Register complete R1-S2 live and
death/impact objects only after provenance closure. Add R1-S3 Plane A from the existing corpus, a separate
scene-scoped Plane-B decision surface that preserves Line-2 ownership, and a boss sprite context from pool-11
source evidence. Any palette decision change must update `specs/palette_decisions.json` in the same later
authorized task.

## 12. Armored-man rendering diagnosis comparison

### 12.1 Visual constraint — PROVEN from Tighe screenshot C

One armored man is complete while another has partial pieces descending below the floor; the corrupted actor
remains active, collidable, dangerous, and killable. This localizes the defect after gameplay actor state and
rejects a universally corrupt ROM art set.

### 12.2 Ranked conclusions

1. **SUPPORTED HYPOTHESIS — per-instance frame/layout/coordinate error.** Downward displacement is a
   geometric symptom. Andy's signed-offset/state-specific evidence supports it. The native finalizer already
   normalizes nine-bit signed coordinates, so the exact error may be upstream in generated piece offsets,
   actor anchor selection, orientation, or wrong frame mapping—not necessarily a missing `ext.w` instruction.
2. **SUPPORTED HYPOTHESIS — DMA/residency pressure for omitted pieces.** A 12-new-cell worklist or 49-cell
   residency exhaustion increments `pc090oj_dropped_count` and skips a piece. It explains incomplete actors
   and instance order, but not newly displaced coordinates.
3. **SUPPORTED HYPOTHESIS — SAT-80/order truncation.** Also predicts missing suffix pieces, not downward
   movement.
4. **UNRESOLVED — stale queue/SAT bank or 20-per-line hardware loss.** Both require direct queue/shadow/VDP
   comparison; the per-line limit normally makes later sprites disappear.

The minimal later capture is both 64-byte actor records; generated frame ID and expected piece list; all lane
queues; DMA count/worklist; resident keys/used bits; dropped count; emitted count; both shadow SAT banks and
front selector; actual VDP SAT; referenced VRAM patterns; and per-scanline load. Diff expected→queue,
queue→shadow SAT, and shadow→VDP. The first stage that changes a coordinate or drops a piece decides the fix.

## 13. Gray-border and boss-music findings

### 13.1 Gray border — PROVEN mechanism

VDP register 7 selects palette 0/color 0. The older global Test CRAM generator normalizes every line's index
zero to `$0000`; current per-scene exporter copies the effective scene value without that normalization.
Both R1-S1 and R1-S2 scene CRAM blobs begin `$0888`, matching `Test.json`. Therefore current CRAM[0] makes
the backdrop gray. A later fix belongs at the per-scene export invariant, not in register 7 and not as a
runtime symptom mask.

### 13.2 Boss music — PROVEN library gap, UNRESOLVED command identity

“The Devil Boss Carnival” is already linked and selectable diagnostically as `$D5`. Production dispatch maps
authentic `$04`, `$25`, and `$27`; unmapped commands are consumed without interrupting current music. Andy's
claim that `$03A0EC` is only an SFX boundary is contradicted by the proven authentic `$27` music request
through that shared command bridge. The missing fact is the authentic R1 boss command and its retained caller
ordering. A later ORIGINAL ARCADE/GENESIS NTSC capture must follow the boss-entry request through the shared
queue and match its original Z80 sequence to the existing track. Do not duplicate song data or add a
scene-number trigger.

## 14. Prioritized next engineering tasks

1. **P0 first-divergence capture:** matched ORIGINAL ARCADE and GENESIS NTSC record-17→21 cell/source/VDP
   evidence described in §9.
2. **P0 correction:** only after task 1, unify the entering-row semantic producer or repair the proven
   physical timing defect; preserve R1-S1 checkpoint behavior.
3. **P0-B rope event diff:** compare 0472/0503, 0517, 0519, and 0525 using the unchanged route and locate
   the first semantic frame difference.
4. **P1 roster closure:** identify the actual R1-S2 live armored actor separately from `$0A73` death/impact;
   exclude wizards.
5. **P1 Composer contexts:** new derived profile for R1-S2 sprites and R1-S3 Plane A, Plane B, boss sprites.
6. **P2 first bad-frame sprite capture:** distinguish changed coordinates from dropped pieces.
7. **Secondary:** normalize per-scene CRAM index zero; prove and map the authentic boss command.

Each task is bounded and independently testable. None is implemented by this review.

## 15. Missing evidence and user verification requirements

### Missing evidence

- matched arcade/Genesis camera states at the first wrong R1-S2 landmark;
- natural captures through records 18–21 and reverse backtracking;
- the first intermediate rope event that differs between 795 and 799;
- both armored actors' piece lists and actual displayed SAT on the bad frame;
- complete R1-S2/R1-S3 scene-tagged actor inventory;
- authentic R1 boss music command identity.

### User verification after later fixes

Tighe must verify the entire bottom-left-to-top R1-S2 climb, downward backtracking, checkpoint respawn, and
late-scene realignment against fixed arcade landmarks. The rope route must return to the proven semantic
result without input/endpoint changes. Two simultaneous armored men must remain complete through walking,
turning, attack, impact, and death. R1-S3 must expose authored Plane A/B and boss colors without changing
Line-2 ownership, and boss entry must play the existing correct track.

## Final classification

- R1-S2 root cause: **UNRESOLVED**; split source-path hypothesis is **SUPPORTED**.
- 64×32 capacity inadequacy: **CONTRADICTED**.
- Andy 0046 scroll-field labels and `$0160` Y premise: **CONTRADICTED**.
- 795→799 elapsed-frame regression: **PROVEN**; cause **UNRESOLVED**.
- R1-S2/R1-S3 Composer incompleteness: **PROVEN**.
- Armored coordinate/frame fault: **SUPPORTED HYPOTHESIS**; resource truncation remains secondary.
- Gray CRAM[0] mechanism: **PROVEN**.
- Existing boss track / missing authentic mapping: **PROVEN**; exact command **UNRESOLVED**.

No ROM was built and no build number was consumed.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0049`
