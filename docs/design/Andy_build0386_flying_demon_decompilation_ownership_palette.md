# Andy — Build 0386 Flying Demon Decompilation / Ownership / Palette (STATIC RE — STOP, NO BUILD)

**Agent:** Andy · Static original-arcade decompilation / semantic repair. **Baseline: Build 0385.**
**Outcome: STOP before build.** No ROM produced; **counter 385 → 385**; no build number consumed; no source
modified; Test.json untouched. Andy performed no gameplay verification — authority: TIGHE. No H25.

## 1. Resume / interruption state
Resumed from the located decompilation artifacts (raw/00045342.c, rastan_actor_creation.c,
rastan_actor_collision.c, rastan_actor_lifecycle.c, rastan_actor_behavior.c, linear_disassembly.tsv). No
restart of discovery; no build consumed by the interruption.

## 2. Phase 0
Priors carried from this session (EXTENDING + static-decompilation). Governing docs re-honored:
RULES/ARCHITECTURE/CLAUDE/PC080SN_PC090OJ policy. Relevant priors: KF-074 (native gameplay sprite ownership;
frontend compatibility), KF-044 (raw-WRAM-literal-not-rebased class), the Build-0381–0385 (code,bank) variant
architecture. **KNOWN_FINDINGS impact: Option A** (no new durable finding merged; this is an in-progress
static investigation).

## 3. Build-0385 baseline
Build 0385 is the current complete candidate (canonical=PASS). Its (code,bank) sprite variant architecture
already produces distinct transformed cells for the demon-wing / burst code overlap (0x28E–0x2A8) by
effective bank (demon 0x35, burst 0x30). Preserved unchanged.

## 4. User-proven arcade contract
Killing the Flying Demon's wings kills the ENTIRE Flying Demon (no wingless body flies on). Current Genesis:
wings disappear, wingless body keeps flying. This document explains what the arcade code proves and where the
proof is not yet complete.

## 5–9. Static arcade findings (PROVEN)
- **Creation (0x45342, `paired_flying_demon_init_45342`):** the Flying Demon is a **fixed pair** of records
  `blk_508[0]` (A5+0x508) and `blk_508[1]` (A5+0x548). Guarded by `blk_508[1].active`. Both get
  `rec_type = (A5+0xC5A==0)?8:9` at +0x06, flag writes to +0x27 (|=0x80) on each, then
  `paired_actor_activate_453a2` on both, then a spawn cue (0x3A0EC).
- **Activate (0x453A2):** per record — timer(+0x1C)=1, active(+0x00)=1, state(+0x05)=3, y(+0x1A)=0x180, then
  the record-type template loader **0x4543E**: template = `rt_45592[(rec_type-8)*8]` → writes base graphics
  (+0x1E), +0x3A, +0x01, +0x28, +0x2C. So rec_type 8 and 9 load **different graphics templates** — one is the
  body (base 0x0129 family), the other the 0x0275-side component. Both pair members are **rec_type 8/9**.
- **Pool driver (0x420E6 → 0x42102):** the A5+0x508 pool (20 × 0x40-byte slots, base A5+0x508) is processed
  separately from the main A5+0x2C8 hurtbox scan (0x449B4). Per active slot it dispatches on state (jump
  table @0x4213A) and runs the move/contact step 0x42E38.
- **Companion / generation-byte mechanism (0x43562 link; 0x4219A–0x421A8 check):** a linked component stores
  an **owner pointer at +0x528** (`move.l a4,(0x528,a6)` @0x4358E — a register-computed A5-relative address,
  **not** a raw literal, so it rebases correctly on Genesis) and the owner's **generation byte** (owner+0x0D)
  at +0x527. Each frame the pool handler compares `self+0x527` to `owner+0x0D` and **retires self (0x4092E)**
  on mismatch, while syncing position (+0x16/+0x1A) from the owner. This is **component-follows-owner**
  (owner dies → component auto-retires).
- **Retire (0x4092E, `actor_retire`):** zeros the 0x40-byte record **and** a paired companion block at
  +delta (`companion_delta`).
- **Damage model (0x449B4/0x447F0/0x448B2):** ordinary enemies are one-hit; overlap sets hit-flash (+0x3D)
  and (rec_type≠7) runs 0x448B2 → state 0x0F death anim + sfx 0x10 → (0x44804) score (+0x2C) → retire.

## 10. GAME SEMANTICS vs PC090OJ tail
All of the above (creation, pool dispatch, companion check, damage/death, retire) is **arcade-owned game
semantics** and is executed by the arcade program on Genesis (it is not part of the PC090OJ hardware tail the
native renderer replaces). The native replacement owns only final SAT/sprite production (KF-074). This is
architecturally important for §11.

## 11. Why this is a STOP (unproven items block a safe repair)
The companion/generation mechanism I fully traced (0x43562 / 0x4219A) applies to **rec_type-7** auxiliary
components. **Both** Flying Demon pair members are **rec_type 8/9** — so that specific mechanism is **not**
proven to be the pair's death linkage. Therefore the following required proofs are **NOT yet established**:
- the exact **wing-hit → whole-demon death** propagation for the 8/9 pair (which member is the hurtbox/damage
  target; how its death reaches the partner; whether it is a shared-state, retire-companion, or pool-scan
  mechanism);
- the exact **first Genesis divergence** (candidates not yet proven: a companion/retire path the native
  gameplay emitter leaves visually resident; a WRAM-relocation of a pair field; a skipped state write);
- a **repair derived from the original semantics** (none can be written without the above).

Per the prompt's STOP conditions (#1 ownership relationship not fully proven for the 8/9 pair; #2 whole-demon
death propagation not proven) and the hard rules "STOP rather than guess" and "no invented Genesis lifecycle
rule," I do **not** produce a build. Guessing a fix would risk regressing accepted Build 0385 and inventing
gameplay logic. A trace is explicitly **not** a substitute for this missing static proof.

## 13–18. Palette routing (STATICALLY RESOLVED — mechanically correct, no repair)
Separately, the Flying Demon palette route **is** statically resolvable and is correct:

| Role | Sample code | Source control (word0 nibble) | Static expected bank | Genesis static route | Variant | CRAM line |
|---|---:|---:|---:|---|---|---:|
| Demon body | 0x129–0x177 | nibble 5 → 0x35 | 0x35 | corpus bank 0x35 → base cell → palsel(scene1,0x35) | base | 1 |
| Demon wings (component_B) | 0x288–0x2A8 | nibble 5 → 0x35 | 0x35 | bank 0x35 → **base** cell (flying_demon transform) → palsel(0x35) | base | 1 |
| Burst | 0x28E–0x2A8 | control nibble 0 → 0x30 | 0x30 | bank 0x30 → **variant** cell (burst transform) → palsel(0x30) | variant | 0 |

- The corpus assigns effective bank **0x35 to BOTH** the demon body and wings (word0 nibble 5). The
  `flying_demon:bank0x35` map covers **every** index the body (1–4,6–15) and wings (2,3,9) use — **0 unmapped**.
- The Build-0385 (code,bank) selector produces the demon-wing cell (base, bank 0x35 → Line 1) and the burst
  cell (variant, bank 0x30 → Line 0) as distinct assets for the shared codes 0x28E–0x2A8.
- **Static conclusion:** the palette routing is **mechanically correct** — the living demon (body+wings)
  routes to bank 0x35 / Line 1 (the authored map), and the burst to bank 0x30 / Line 0. Per Part 11's rule
  this branch STOPS here: if the demon still looks wrong in-game, the only remaining question is a **live
  value** — whether the runtime wings sprite actually reaches the emit-time selector as effective bank 0x35 —
  which is a narrowly scoped read-only Genesis trace to run **after** this static proof, not a mapping change.
  **No palette repair is justified; Tighe's maps are unchanged.**

## 16. Optional narrow trace — NOT run
No trace was used. The lifecycle STOP is a missing-static-proof condition (a trace cannot substitute).
The one legitimate future trace (palette live value: "does the demon wings sprite reach the (code,bank)
selector as effective bank 0x35?") is defined but out of scope for a STOP-without-repair.

## 19. Architecture compliance
No source changed; no runtime recolor; no PC090OJ emulation; no object-RAM mirror; no Genesis lifecycle logic
added. CONFIRMED (investigation only).

## 20. Build 0385 → 0386 diff
None — no build produced.

## 21. Complete five-ROM matrix
Not produced (STOP).

## 22. USER MUST VERIFY
Nothing to verify from Andy this task (no build). The gameplay contract (wing kill → whole demon dies) remains
Tighe's established truth; the repair awaits completed static proof of the 8/9-pair death propagation.

## 23. Open/Closed Issues Impact
New OPEN item (to add): "Flying Demon wing-kill does not kill the wingless body (Genesis)." Static model
partially proven (paired 0x508/0x548 rec_type-8/9 records; pool handler 0x420E6; retire 0x4092E zeros
companion); the 8/9-pair death propagation + Genesis divergence remain to be proven before repair. OPEN-006
context: demon palette routing proven mechanically correct (no fix). None closed.

## 24. KNOWN_FINDINGS impact
Option A — No new finding to index (investigation in progress; nothing durable yet promoted).

## Next static steps (to unblock a future Build 0386)
1. Prove which pair member carries the player-hittable hurtbox and how a hit transitions it to death (does the
   0x508-pool path route the pair through 0x448B2 state-0x0F, or a pair-specific branch?).
2. Prove the 8/9-pair death linkage (shared state field, retire-companion delta for the 0x508 pool, or a
   pool re-scan that retires the partner) — the actual mechanism enforcing whole-demon death.
3. Diff that proven arcade path against the current Genesis translation/native emitter to find the first lost
   semantic operation.
4. Only then derive a repair from the original semantics and build.

---

# CONTINUATION (pair-model correction) — PREVIOUS INTERPRETATION SUPERSEDED

**Still STOP, no build. Counter 385 → 385.** This continuation corrected the suspect pair model and
completed the focused type-8/type-9/pool-init/retire analysis; the whole-demon death mechanism remains
unproven, so no repair is derivable and no ROM is produced.

## C1. Corrected initializer semantics (0x45342, exact disasm)
`a4=A5+0x508, a3=A5+0x548`. `if (A5+0xC5A==0) { a4.rec_type=8; a3.rec_type=8 } else { =9; =9 }` — **both
records receive the SAME rec_type** (never one 8 + one 9). Then: `a4+0x3F=1` (only 0x508), `a4+0x27 bit7`,
`0x453A2` activate, `0x453C0`; and for 0x548: `a3+0x27 bit7`, `0x453A2`, `0x453C0`; then sfx 0x14. `0x453C0`
is scene-config only (`if A5+0x118<5: rec+0x28=4, +0x2C=7`), identical for both. **The only init difference
between the two records is 0x508's +0x3F=1** (a "primary" marker).

## C2. PREVIOUS "pair = body + wings" — DISPROVEN
The prior doc's claim that blk_508[0]=body and blk_508[1]=0x0275-wings is **not supported**: both records are
the same rec_type. Superseded. The two records are two same-type records (both body-form type-8, or both
type-9), differentiated only by 0x508's +0x3F primary flag — not a body/wings split by rec_type.

## C3. Type-8 vs type-9 (template 0x45592 + compositor VM)
- **Type 8**: base 0x0129, anim 0x30 → emitted cells **0x14A–0x155** (inside the body block 0x129–0x177) = the
  demon BODY form.
- **Type 9**: base 0x02AF, anim 0x57 → emitted cells **0x2AF–0x2B6** — a DISTINCT form, and **not** the
  corpus wing block (0x288–0x2A8) nor the burst (0x28E–0x2A8).
- A5+0xC5A selects which form both records take (meaning of A5+0xC5A: a variant/phase selector — its exact
  gameplay condition is not yet traced).

## C4. Wing-graphics producer — UNRESOLVED
The visible wing cells 0x288–0x2A8 are produced by **neither** type-8 anim 0x30 (0x14A–0x155) nor type-9 anim
0x57 (0x2AF–0x2B6). They therefore come from a different animation of one of these bases, or a compositor
sub-component, or another record — **not yet proven**. (Actor base ≠ emitted cell code: proven distinct
here.) The prior implicit "wings actor base = 0x0275" is unsupported.

## C5. actor_retire 0x4092E — exact companion_delta (decompiled)
`zero 0x40-byte record; d1=0x702; if (a0 >= 0x0010C508) d1=0x4E2; if (a0 >= 0x0010C748) d1=0x4E2; companion =
a0 + d1; zero its 0x20 bytes.` For the demon records (arcade 0x10C508 / 0x10C548): **delta = 0x4E2** →
companion blocks at 0x10C9EA / 0x10CA2A — **NOT** the paired demon record. **So retire does NOT clear the
partner record; it is not the whole-pair death mechanism.**
- **Durable finding (KF-044 class):** retire selects the delta by comparing the record pointer against **raw
  absolute WRAM literals** `#0x0010C508` and `#0x0010C748` (`cmpal`). On Genesis (records rebased to
  0xFF0xxx) every record compares `>=` both thresholds → delta always 0x4E2. For the flying demon this
  coincidentally matches the arcade delta (0x4E2), so it is **not** the flying-demon divergence — but it is a
  latent mis-delta for any pool whose arcade records sit below 0x10C508 (which should get 0x702). Recorded for
  future review; NOT fixed here (out of this task's proven scope).

## C6. Still-unproven (blocks any build — Part 17 STOP)
| Question | Result |
|---|---|
| Meaning of A5+0xC5A | variant/phase selector (exact condition untraced) |
| A5+0x508 role | type-8/9 record, +0x3F=1 primary — full role UNPROVEN |
| A5+0x548 role | type-8/9 record — full role UNPROVEN |
| Why two records | UNPROVEN (two demons? paired forms? one logical + aux?) |
| Type-8 role | BODY form (cells 0x14A–0x155) |
| Type-9 role | distinct form (cells 0x2AF–0x2B6) |
| Actual wing (0x288–0x2A8) producer | UNPROVEN |
| Hittable record | UNPROVEN |
| Death-state owner | UNPROVEN |
| Whole-demon kill mechanism | UNPROVEN (not retire-companion) |
| Retire paired-clear | PROVEN: does NOT clear the partner record |
| First Genesis divergence | UNPROVEN |

## C7. Palette — retained
Body + wing-side graphics still route effective bank 0x35 → Line 1 (authored), burst bank 0x30 → Line 0;
Build-0385 (code,bank) assets distinct. No mapping change. (Bank identity not disproven by the corrected
actor model — the corpus effective-bank nibble 5 stands.) **No palette repair.**

## C8. Outcome
Corrected the false pair premise; completed type/pool/retire analysis; the whole-demon death mechanism is
still unproven, so no architecture-compliant repair can be derived. **STOP, no build, counter 385.**

---

# CONTINUATION 2 — SEPARATE-WING FACT LOCKED; RECONCILIATION + LINKAGE SEARCH (STILL STOP, NO BUILD)

**Locked project facts (not re-litigated):** the Flying Demon wings are a SEPARATE object/component, and
the SAME wing object/graphics are reused by the Round-2 boss with a different palette. Graphics-object
identity ≠ logical owner ≠ palette identity.

**Reconciliation of prior component_A/component_B with the same-rec_type proof (advanced):**
- Both 0x508 and 0x548 are the same rec_type (8 or 9); they are differentiated by **+0x3F** (only 0x508=1 at
  init, 0x45370) and by pool-slot index (A5+0x212 = 0 vs 1). So "component_A/component_B" = the two same-type
  records distinguished by +0x3F / slot, **not** by rec_type. Prior labels reconciled.
- **+0x3F is a collision discriminator (0x446BC select_hurtbox @0x446E4):** for rec_type 8/9, a record with
  **+0x3F==0 is assigned hurtbox index 2 (player-hittable)**; +0x3F==1 is not assigned that box. So the
  +0x3F==0 member (slot-1 / 0x548) is the player-hittable member and the +0x3F==1 member (0x508) is not
  hit through hurtbox 2. (Caveat: +0x3F is also set to 1 in an anim-init path @0x44352, so it doubles as a
  general "primary/initialized" flag — it is not exclusively a demon field.)

**Whole-demon death linkage — candidates ELIMINATED (proven NOT the mechanism):**
1. `actor_retire` 0x4092E companion clear: for the demon records the delta is 0x4E2 → clears 0x10C9EA/
   0x10CA2A, NOT the partner record. NOT the linkage.
2. Direct partner-clear `clr.b (0x508,a5)` @0x427BE: reached only for **non-8/9** rec_types (the demon
   rec_type 8/9 branches away to the off-screen X-cleanup @0x427C4 at 0x42788/0x42792). NOT the demon path.
3. rec_type-7 owner/generation mechanism (+0x527/+0x528, 0x43562/0x4219A): applies to rec_type-7 aux
   components, not the 8/9 pair. NOT the linkage.

**Still UNPROVEN (blocks a build):** the actual mechanism by which killing the hittable member (0x548) causes
the body member (0x508) to die for the rec_type-8/9 pair; which record emits the 0x288–0x2A8 wing cells and
its state path; the Round-2-boss shared-wing creation path; the first Genesis divergence; and a safe repair.
Remaining candidate locations (not yet decompiled to proof): the death-anim-complete handler (0x44804), the
state-0x0F death handler (0x40CCC), and the demon-specific 8/9 state handlers reachable from the 0x508-pool
jump table (@0x4213A) — one of these likely reads/writes the partner's state or a shared field.

**Decision:** three plausible partner-death mechanisms were eliminated by proof; the true 8/9-pair linkage is
not yet located. Per the STOP conditions and "STOP rather than guess / no invented Genesis lifecycle rule,"
no build is produced. Counter remains 385. (Weekly usage near limit; the next continuation should decompile
0x44804 / 0x40CCC and the 8/9 state handlers to find the partner-state write.)

**Palette:** unchanged. The Round-2-boss reuse confirms wing palette is owner/context-dependent; do not
collapse. `usage:flying_demon:bank0x35` and `usage:burst:bank0x30` untouched. No repair.

---

# CONTINUATION 3 — 0x548 DEATH-LINK DECOMPILATION: MECHANISM PROVEN + FIX + BUILD 0386

**Result: whole-demon death linkage PROVEN, first Genesis divergence PROVEN (KF-044 class), byte-neutral
repair implemented, Build 0386 produced (canonical=PASS, complete five-variant family). Test.json / palette
untouched.**

## D1. The whole-demon death chain (PROVEN, instruction-level)
1. **Hit target:** `select_hurtbox` (0x446BC) at **0x446E4** assigns **hurtbox index 2** to a rec_type-8/9
   record with **+0x3F==0** — that is **A5+0x548** (the wings; A5+0x508 has +0x3F=1 and is not assigned that
   box). So the player strikes 0x548.
2. **Death state:** the hit runs the one-hit reaction → state **0x0F**. The state-0x0F handler **0x40CCC**
   drives the death animation (sets +0x1E = 0x0A73 death-burst base, counts down) and, when complete, falls
   into the completion path.
3. **Death-complete dispatch:** **0x44804** (death-anim-complete) ends with a rec_type test: `cmp.b #8/#9,
   +0x06 → 0x44896`. So **rec_type 8/9 (the Flying Demon) has a dedicated death-complete branch at 0x44896.**
4. **Partner kill (the mechanism):** **0x44896**:
   ```
   0x44896  move.l %a4,%d7            ; save the dying member (A5+0x548)
   0x44898  lea 0x0010C508,%a4        ; point at the PAIRED BODY record A5+0x508
   0x4489E  move.b #1,%a4@(0x3D)      ; body hit-flash = 1
   0x448A4  bsr 0x448B2              ; component_init(body): +0x05 = 0x0F (state death), +0x08=0xFF,
                                      ;                       +0x09=1, sfx 0x10
   0x448A8  move.l %d7,%a4            ; restore
   0x448AA  sub.w #16,%a4@(0x1A)
   ```
   So when the wings (0x548) finish dying, the arcade **explicitly puts the body (0x508) into state 0x0F
   death** → the body then runs 0x40CCC and retires. **Wing kill → whole demon dies.** This is a **0x548 →
   0x508 push** (direction A). It always targets the primary 0x508 (a fixed address), not a ±0x40 sibling
   computation.

## D2. First Genesis divergence (PROVEN)
`0x44898  lea 0x0010C508,%a4` is a **raw absolute arcade-WRAM literal** (KF-044 class). Genesis rebases WRAM
0x10C000→0xFF0000, so the body record lives at **0xFF0508** — but this instruction loads the un-rebased
**0x10C508**, which on Genesis is **ROM/unmapped**. The subsequent `move.b #1,(0x3D,a4)` and
`component_init` therefore write to 0x10C508 (dropped), so the **real body record (0xFF0508) is never set to
state 0x0F** → it stays active and keeps flying. This is a **logical bug** (the 0x508 record stays alive),
not a stale-sprite artifact.

## D3. Repair (implemented) — restores the original arcade operation
Byte-neutral `opcode_replace` at **arcade_pc 0x044898**: `49F90010C508` → `49F900FF0508`
(`lea 0x0010C508,a4` → `lea 0x00FF0508,a4`, i.e. `−0x10C000 + 0xFF0000`, the same rebase the spec already
uses for 0x10Dxxx→0xFF1xxx WRAM literals). The body-death write now lands on the real Genesis body record.
No Genesis-only lifecycle logic; no renderer species-case; no palette change. Verified in the ROM: the
rebased `lea 0x00FF0508` is present at runtime 0x44A98 (= 0x44898 + 0x200) and the raw `0x10C508` write is
gone.

## D4. Build 0386
`opcode_replace` count 230→231 (updated in the spec `expectations`, `postpatch_startup_rom.py`, and
`verify_canonical_rom.py`). Coverage unchanged (byte-neutral) at 0x1A9EB8. Palette snapshot unchanged
(build0384 input; Test.json byte-identical `02d0122a…`). Gates: canonical **GATE_PASS**, entry=PASS,
epoch=FAIL (pre-existing). Complete five-variant family; base SHA
`2b7588fd041a454c62880019d25fb08223eb9dccb1dc20d5f6debaae3c399bfb`, size 1744568 (identical size to 0385 —
byte-neutral). Counter 385→386.

## D5. Palette / architecture
Unchanged: `usage:flying_demon:bank0x35` (Line 1), `usage:burst:bank0x30` (Line 0) untouched; no runtime
recolor; no PC090OJ emulation; no object-RAM mirror; arcade owns the lifecycle (the fix is inside the arcade
program's own death path). Round-2-boss wing reuse is on a different owner/palette and is not touched by a
maincpu WRAM-literal rebase.

## D6. USER MUST VERIFY (Tighe)
Strike/kill the Flying Demon through the wings and confirm the **entire** demon dies with no wingless body
flying on; then confirm the Round-2 boss wing appearance, the demon/boss burst, and all other enemy /
Rastan / weapon / cave palettes are unchanged. Andy performed no gameplay verification.
