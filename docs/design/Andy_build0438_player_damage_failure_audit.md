# Andy — Build 0438 Player Damage Failure Audit (why Rastan does not take enemy damage on Genesis)

**Date:** 2026-10-17 · **Agent:** Andy · **Type:** READ-ONLY gameplay-semantics / regression
root-cause investigation. **No** production source, Makefile, generator, verifier, spec, ROM,
build number, counter, branch, commit, MAME run, or new gameplay trace was produced or changed.
Phase D/E not started. HUD/framing work not resumed.

**Baseline audited:** Build 0438 (counter = 438), candidate/source commit
`29412437861ea5e7fb046fc6d0b1c1bb58d73b2a` ("Build 438 — Restore Build 434 production
implementation"). The archived 0435–0437 HUD/framing implementation was **not** used as the
baseline.

**Tool reuse (RULES §18):** Existing resources reused — arcade decompilation C tree
(`analysis/decompilation/c/…`), arcade disassembly `build/maincpu.disasm.txt`, Genesis postpatch
disassembly `build/genesis_postpatch.disasm.txt`, authority map `build/rastan-direct/address_map.json`,
remap spec `specs/rastan_direct_remap.json`, the stock-cheat definition `tools/mame/cheat/output.json`,
the rope-benchmark Lua, and `AGENTS_LOG.md`/`docs/design` history. New tooling created — none. No new
gameplay trace, Lua route, or save state was created; no gameplay was driven.

---

## Executive conclusion

1. **It is NOT a forced-invincibility flag (option F refuted, with ROM-byte proof).** The arcade
   invincibility gate is the word **A5+0x0040** (bit 6; the stock MAME "Invincibility" cheat forces
   it). On Genesis Build 0438 it initializes to **0 (vulnerable)** — see §Invulnerability audit.
2. **The symptom is real and long-standing, not a Build-0438 regression.** Existing project evidence
   (Tighe-confirmed since Build 0228) records that **enemy contact deals no damage on Genesis** and
   that observed Genesis deaths are **collision/terrain-driven** (lava, pits, drowning). The player
   *can* die; only the **enemy-contact → player-hurt/death linkage** fails.
3. **The exact broken instruction cannot be named from current evidence** because the arcade
   enemy-contact-**damages-player** model is explicitly **not yet decompiled** (per
   `Andy_h8_enemy_damage_item_drop_decompilation.md`). The narrowest unresolved fork and the minimum
   test to settle it are given below.
4. **This is a DAMAGE-SEMANTICS gap, not a HUD false-positive.** Terrain deaths are visible and do
   occur, so "no damage" is not merely the reduced HUD hiding the energy bar — although the reduced
   HUD *does* separately hide the energy/status presentation (§HUD false-positive check).

---

## ARCADE AUTHORITATIVE DAMAGE CHAIN

Recovered from the existing Ghidra/decompilation tree (`rastan_actor_collision.c`,
`rastan_actor_lifecycle.c`, `rastan_player_animation.c`, `rastan_player_hud.c`, raws
`000449b4.c`/`000447ce.c`) and `build/maincpu.disasm.txt`. The 68000 binary is final authority.

Frame order (top `0x41F0E` → main `0x5100A` → actor update `0x40B66`):

```
enemy collision manager 0x449B4  (multi-pass over the A5+0x2C8 enemy pool, 29 slots)
    select_hurtbox 0x446BC  ->  rect = hurtbox_table_0x44CE0[idx]  (variant 0x44FA8 when +0x38==2)
    player box ∈ { A5+0x28C weapon, A5+0x2B0, A5+0x1248, A5+0x1254, A5+0x22C }  (category dispatch)
    AABB overlap via 0x44CBA (X then Y)
    on overlap -> hit record {X,Y,pal} into A5+0x12A8/0x12C8, then hit reaction 0x447CE
0x447CE hit reaction (ONE-HIT; no enemy HP accumulator):
    rec_type 10/11/18 -> freeze (0x447B6); family(+0x3E)==12 -> score(+0x2C)+recycle (0x448D8/0x40A1E);
    else +0x3D hit-flash=1 and (rec_type!=7) -> 0x448B2 => state 0x0F death anim + sfx 0x10
    fatal path -> death-anim complete 0x44804 -> score 0x3B726 -> retire 0x4092E
```

Two player-death causes exist in the arcade:

- **Energy timeout:** energy = high byte of **A5+0x013A**; when it reaches 0 the player enters death
  **state 8** (`rastan_player_animation.c`). The HUD energy bar is the visible representation of this
  field (six cells, `0x5A098`).
- **Enemy / hazard contact:** the player's body box overlapping an enemy hurtbox drives the player
  into a hurt/impact/death state (**state 0x0E/0x0F** via the state helper `0x3A2EC`), with the stock
  arcade "Invincibility" cheat (A5+0x0040 bit 6) suppressing exactly "player damage, hit-stun,
  knockback, and enemy-contact death" (`AGENTS_LOG.md` 2026-10-14 Silver-Standard entry).

Separately, a **special-contact (solid-object/terrain) record** is produced by `0x44548/0x449B4`
into **A5+0x0242** (12 bytes: state, actor X/Y, rectangle `{-20,+20,-16,+16}` = the player body box)
and consumed by the retained player-contact response at **0x054BF8..0x054DA8**, which sets death/impact
states (`0x0E`/`0x0F`/`8`) through `0x3A2EC`. This is the path behind the **collision/terrain** deaths.

> **Important distinction the evidence forces:** `0x449B4`/`0x447CE` as currently decompiled resolve
> the **player-weapon-kills-enemy** (one-hit enemy death). The **enemy-contact-kills/hurts-player**
> model — the enemy "HP field / one-hit-vs-multi-hit / invulnerability" linkage — is explicitly
> recorded as **NOT located** in `Andy_h8_enemy_damage_item_drop_decompilation.md:38`. That missing
> linkage is the subject of this audit.

---

## GENESIS BUILD-0438 DAMAGE CHAIN

Per RULES, gameplay (collision, damage, death) is arcade-owned and retained; the native translation
replaces only PC080SN/PC090OJ rendering tails. Classifying each element in Build 0438:

| Arcade element | Arcade PC | Genesis state | Evidence |
|---|---|---|---|
| Top/main loop, actor update | `0x41F0E`/`0x5100A`/`0x40B66` | **RETAINED** | copied region, +0x200 |
| Enemy collision manager (weapon→enemy) | `0x449B4` | **RETAINED** | copied; produces enemy death + special-contact record |
| Enemy hit reaction (enemy one-hit death) | `0x447CE`→`0x448B2` | **RETAINED** | copied |
| Special-contact (terrain) record producer | `0x44548` → A5+0x0242 | **RETAINED + rebased** | §mapping; `0xFF0242` |
| Player contact response (terrain death) | `0x054BF8..0x054DA8` | **RETAINED + rebased** | runtime `0x54C76 lea 0xff0242,%a0` |
| Energy timeout death (state 8) | `0x54F34` region | **RETAINED** | runtime `0x54F34 cmpiw #0,%a5@(68); movew #8,%a5@(4328)` |
| Invincibility/debug gate init | `0x3AFEE/0x3AFFE` (read `0x5FF9E`) | **RETAINED (operand NOT relocated; benign)** | §invulnerability audit |
| Enemy-contact-**damages-player** linkage | **not located** | **UNRESOLVED (likely never translated)** | `h8` §38; Tighe observation |

So every damage element the project **has** decompiled is retained and correctly addressed in Build
0438. The one element that is **not** demonstrably present is the arcade enemy-contact→player-hurt
linkage, which was never fully reverse-engineered.

---

## STATE / FIELD TABLE

Arcade A5 base `0x10C000`; Genesis WRAM rebase **A5 → 0xFF0000** (so A5+off → 0xFF00+off).

| Field | Arcade abs | Genesis WRAM | Meaning | Build-0438 status |
|---|---|---|---|---|
| A5+0x0040 (word) | `0x10C040` | `0xFF0040` | **invincibility/debug gate** (bit 6); nonzero ⇒ lethal checks skipped | inits **0 (vulnerable)** |
| A5+0x0044 (word) | `0x10C044` | `0xFF0044` | debug gate (bit 7) gating energy-timeout death | inits **0 (death enabled)** |
| A5+0x013A (hi byte) | `0x10C13A` | `0xFF013A` | **energy** (health/timer); 0 ⇒ death state 8; `0x30` = full 6 cells | field retained; runtime drain unverified |
| A5+0x10E8 (word) | `0x10D0E8` | `0xFF10E8` | **player_state** (8=death, 0x0F=impact/death, 1..3 normal) | read by benchmark; retained |
| A5+0x0242 (12B) | `0x10C242` | `0xFF0242` | special-contact (solid/terrain) record; rect `{-20,+20,-16,+16}` | **rebased (Build 0366)**; consumed |
| A5+0x12A8/0x12C8 | `0x10D2A8/…` | `0xFF12A8/…` | enemy-hit record (X,Y,pal) → death sparks | retained |
| actor +0x3D | — | — | hit-flash flag set on overlap | retained |
| config word | `0x5FF9E` (ROM) | read at Genesis `0x5FF9E` (unrelocated) = `0xFFFF` | feeds A5+0x40/0x44 init and start stage | §below |

---

## ARCADE-PC → GENESIS-PC MAPPING

Authority: `build/rastan-direct/address_map.json` (relocation_delta `0x000200`, arcade source
`0x000000..0x060000`, 542 segments) and `build/genesis_postpatch.disasm.txt`. Code copies at **+0x200**
in the relevant range (no additional shift before `0x45xxx` in Build 0438).

| Arcade PC | Runtime Genesis PC | Note |
|---|---|---|
| `0x03AFEE` / `0x03AFFE` (read `0x5FF9E` → A5+0x40/0x44) | `0x03B1EE` / `0x03B1FE` | operand `0x5FF9E` **not relocated** (see audit) |
| `0x04527E` (stage/round init, reads `0x5FF9E`) | `0x04547E` | operand `0x5FF9E` **not relocated** |
| `0x054A76` (`lea A5+0x0242`) | `0x054C76` → `lea 0xff0242,%a0` | WRAM literal **correctly rebased** (Build 0366) |
| `0x054D84` (invincibility gate `cmpiw #0,A5+0x40`) | `0x054F84` region | retained |
| `0x054F34` (`if A5+0x44==0 → state 8`) | `0x054F34` region | timeout-death retained |

WRAM literals must be rebased `0x10Cxxx → 0xFF…`. Multiple absolute `0x0010Cxxx/0x0010Dxxx` tokens
still appear in the Build-0438 disassembly (72 regex hits); most are pointer-table data or
misdisassembled bytes, but this is exactly the recurring **KF-044 "raw-WRAM-literal-aliases-ROM"**
class that silently breaks an operation when a genuine instruction operand is left un-rebased (fixed
piecemeal in Builds 0366 `0x10C242` and 0386 `0x10C508`). Any surviving instance inside the
(un-decompiled) enemy-contact→player path is the leading candidate mechanism.

---

## INVULNERABILITY AUDIT (A5+0x0040 bit 6)

**Arcade semantic.** `A5+0x0040` is initialized at `0x3AFEE/0x3AFFE`:

```
movew 0x5ff9e,%d0 ; notw %d0 ; andib #0x40,%d0 ; movew %d0,%a5@(64)   ; A5+0x40 = (~[0x5FF9E]) & 0x40
movew 0x5ff9e,%d0 ; notw %d0 ; andib #0x80,%d0 ; movew %d0,%a5@(68)   ; A5+0x44 = (~[0x5FF9E]) & 0x80
```

The lethal checks (cluster `0x54D84..0x555xx`) are `cmpiw #0,%a5@(64); bne <skip>` — i.e. **when
A5+0x0040 is nonzero, the damage/death sub-calls are skipped** (invincible). The stock MAME
"Invincibility" cheat (`tools/mame/cheat/output.json`) forces it nonzero:
`writev_u16(0x10c040, 0x0040 | …)`, with the telling comment *"You die though when fall down into the
water"* — i.e. the gate covers enemy/hazard contact but not water, matching the `cmpiw #0,%a5@(64)`
placement. The **arcade** rope Silver-Standard run uses this cheat to suppress enemy-contact death on
the Right-only route; it is **benchmark-only** and not part of any Genesis build.

**Genesis Build-0438 value (ROM-byte proof).** Arcade `[0x5FF9E] = 0xFFFF`. The init read's absolute
operand is **not relocated** (runtime `0x3B1FE` still reads absolute `0x5FF9E`, not the copied
constant at `0x6019E`). On Genesis, absolute `0x5FF9E` lands in `0xFF`-padding, so the read returns
**0xFFFF** anyway. Therefore:

- `A5+0x0040 = (~0xFFFF) & 0x40 = 0` → **vulnerable** (invincibility NOT asserted);
- `A5+0x0044 = (~0xFFFF) & 0x80 = 0` → **energy-timeout death enabled**;
- start stage `= (~0xFFFF & 7) + 1 = 1` → correct.

> There IS a latent translation defect here — the absolute **data** operand `0x5FF9E`
> (`MOVE.W abs,Dn`, a reference class the shift patcher does not relocate) is not rebased to the
> copied constant. It is currently **benign** only because both the real location and the aliased
> Genesis location contain `0xFFFF`. It is recorded for completeness; it is **not** the damage bug.

**Conclusion:** no retained/replicated/forced invincibility state is active in normal Genesis
gameplay. Option **F is refuted**. The bit's normal-gameplay meaning is a **config/debug invincibility
gate**, cleared (0) in normal play.

---

## COLLISION VS DAMAGE SEPARATION

| # | Question | Finding |
|---|---|---|
| 1 | Does the arcade enemy collision test execute on Genesis? | **YES (retained)** — `0x449B4` is in the copied worker; it still kills enemies (sword) on Genesis. |
| 2 | Same candidate overlap found? | **UNRESOLVED** — not statically provable; needs a watchpoint. |
| 3 | Player hurtbox geometry matches arcade? | Terrain body box `{-20,+20,-16,+16}` is present and rebased (`0xFF0242`); the enemy-contact body box linkage is **not located**. |
| 4 | Does contact enter the arcade damage decision? | **UNRESOLVED / likely NO for enemy contact** — terrain contact does (death works); enemy contact does not (observed). |
| 5 | Does a flag/timer reject damage? | **NO** — A5+0x40/0x44 = 0 (not invincible). Rejection is not flag-based. |
| 6 | Is the energy/health write executed? | **UNRESOLVED** — field retained; enemy-driven decrement unproven; timeout path intact. |
| 7 | Hurt state / knockback entered? | **NO (observed)** / UNRESOLVED at instruction level. |
| 8 | Temporary post-hit invulnerability started? | **UNRESOLVED** (depends on the un-located hurt path). |
| 9 | Does gameplay later clear it? | n/a until (7)/(8) resolved. |
| 10 | Can the player reach death? | **YES via terrain** (lava/pits/drowning proven); **not via enemy contact**. |

**First proven divergence:** the chain diverges at **step 4 for the enemy-contact branch
specifically** — terrain/solid-object contact reaches the retained, correctly-rebased response at
`0x054BF8` and kills the player, but the enemy-contact→player-hurt branch does not take effect. The
branches share the collision manager but differ in the player-hurt linkage that `h8` records as not
yet decompiled.

---

## HISTORICAL / INTRODUCING-BUILD EVIDENCE

Existing evidence establishes this as a **pre-existing, Tighe-confirmed** condition, not a Build-0438
regression:

- `analysis`/`AGENTS_LOG.md:44809` (Stage-1 rope death): *"user: enemies deal no damage, so it is
  collision-driven."*
- `docs/design/Andy_fable_build0228_stage1_cave_map_collision_authority.md:131`: *"user confirms
  enemies deal NO damage in Genesis, so death is collision-driven, not enemy."* (Build-0228 era.)
- `docs/design/Andy_build0400_timing_instrument_repair.md:282`: *"Rastan is invincible in this dev
  build…"* (used as a standing property).
- `docs/design/Andy_h8_enemy_damage_item_drop_decompilation.md:38`: the enemy *"HP field /
  one-hit-vs-multi-hit / invulnerability model is **not located**."*
- Terrain/collision death paths are proven working (Build 0167 drowning transition; 44809 lava).

**Introducing build: NOT ESTABLISHED.** The evidence indicates enemy-contact damage has **not
functioned on Genesis to date** (the arcade enemy-damages-player model was never fully translated),
rather than regressing at a specific build. Do not guess a build number.

---

## HUD FALSE-POSITIVE CHECK (damage semantics vs presentation)

Build 0438 uses the **reduced** gameplay HUD (`RASTAN_GAMEPLAY_HUD_SPRITES=2`: 1UP / current-score
only). The **energy bar and lower HUD are not displayed** in this mode, so energy depletion ("damage"
in the health-timer sense) is **not visible**. The authoritative energy state is **A5+0x013A =
0xFF013A**; the HUD absence does not prove the field does not change.

However, the symptom is **not solely** a HUD false-positive: terrain deaths (lava/pits/drowning) are
visible and do occur, so the player is demonstrably not invincible and can die. The reduced HUD
hiding energy is a **separate, genuine presentation gap** (clearly distinct from the damage-semantics
gap), and it does make any enemy-driven energy effect invisible. Both facts hold; they must not be
conflated.

- **DAMAGE SEMANTICS:** enemy-contact→player-hurt/death linkage does not take effect (core issue).
- **DAMAGE/HUD PRESENTATION:** energy/status bar hidden in HUD mode 2 (separate; cosmetic).

---

## ROOT CAUSE

To the provable level:

> **It is not an invincibility flag.** A5+0x0040/0x0044 initialize to 0 on Genesis Build 0438
> (vulnerable; energy-timeout death enabled), proven from the actual ROM bytes. The retained arcade
> worker still runs collision, and terrain/solid-object contact correctly reaches the player-death
> response at `0x054BF8` (WRAM record rebased to `0xFF0242`), so the player can die. **What does not
> take effect on Genesis is the arcade enemy-contact → player-hurt/death linkage specifically** — a
> long-standing, Tighe-confirmed condition. The exact divergent instruction cannot be named because
> that linkage (the arcade enemy-damages-player / hit-stun / knockback / post-hit-invulnerability
> model) is not yet decompiled; the recurring KF-044 un-rebased-WRAM-literal / dropped
> producer→consumer class is the leading mechanism, by analogy to the already-fixed `0x10C242`
> (Build 0366) and `0x10C508` (Build 0386) contact-record rebases.

**Narrowest unresolved fork (what evidence is missing):** whether, at runtime on Build 0438, an
enemy–player body overlap (a) is detected but produces no hurt record, or (b) produces a record that
the response path cannot consume because of an un-rebased WRAM literal, or (c) the arcade never
drove enemy-damage through a record at all and it was simply never translated. Distinguishing these
requires decompiling the enemy-contact→player-hurt linkage **and** one targeted read-only watchpoint
run (below) — neither performed here.

---

## MINIMUM FUTURE REPAIR BOUNDARY

Restoration of original arcade semantics only — **no** Genesis-owned damage system, no difficulty
change, no "improvement."

1. **Decompile the missing linkage first (read-only, Ghidra-first).** Recover the arcade path from
   "player body box overlaps enemy hurtbox" to the player hurt/impact/death state (states
   `0x0E`/`0x0F`/`8` via `0x3A2EC`), including any hit-stun/knockback and temporary post-hit
   invulnerability. This is the `h8`-identified "not located" model. Extend the existing C tree; do
   not start a parallel project.
2. **One targeted read-only watchpoint run** (Tighe-owned or a future authorized trace task, not this
   one): during a deliberate enemy contact, watch `0xFF013A` (energy), `0xFF10E8` (player_state),
   `0xFF0242`/the enemy-hit record, and the hurt-state writes. This settles the (a)/(b)/(c) fork.
3. **If the mechanism is a KF-044 un-rebased WRAM literal** (most likely), the repair is a single
   byte-neutral operand rebase (`0x10Cxxx → 0xFF…`) in the identified instruction, exactly like
   Builds 0366/0386 — preserving the arcade LEA/response logic.
4. **If the mechanism is a dropped producer→consumer link**, restore the retained arcade call/record
   path so the enemy-contact record is produced and consumed, preserving arcade hurt/knockback/death
   and temporary-invulnerability semantics.
5. **Separately** (not part of the damage fix): the energy bar is only visible under HUD mode 1,
   whose restoration is the deferred HUD/framing work — tracked, not resumed here.
6. **Also note (do not fix here):** the un-relocated absolute data read of `0x5FF9E`
   (`MOVE.W abs,Dn`) is a latent, currently-benign translation defect; fold it into the WRAM/absolute
   relocation review rather than the damage repair.

---

## FINAL STATUS

Production source modified: NO. Makefile/generators/verifiers/spec modified: NO. ROM built: NO. MAME
run: NO. New gameplay trace created: NO. Build number consumed: NO. Build counter changed: NO.
HUD/framing work resumed: NO. Phase D: NO. Phase E: NO.
