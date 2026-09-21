# Andy — CHECKPOINT H8: Enemy Damage / Item-Drop System + Animation Core

**Agent:** Andy · **Type:** Static reverse engineering (ORIGINAL ARCADE 68000). NO MAME, NO ROM,
NO Genesis change. **Build counter: 360 (unchanged).**
**Manifest/bestiary/`build_bestiary.py`:** NOT modified — no *new dropped-item actor* was statically
proven this pass, so per the H8 rule ("update the bestiary IF dropped-item actors are proven") they
are left untouched. Cody files untouched.

Mandatory RULES.md standalone report for CHECKPOINT H8. Authoritative source:
`build/regions/maincpu.bin` + `build/maincpu.disasm.txt`. Reconstructed C is an auditable
representation, **NOT original Taito source**.

> **Honest scope statement.** H8 has two halves. The **animation core** (§K) and the **state-0x0F
> polymorphism** (§L) are fully closed with byte-exact C and guards. The **enemy-hit → conditional
> item-drop** system (§A–§H) was **not** isolated within this pass: the player *weapon-hitbox
> construction* and *world* collision were located, but the enemy-hurtbox scan and the drop creator
> were not found, and **no drop table was fabricated**. §M states the exact next targets. I accept
> the H7 correction: Rastan does not drop items on his own death; the target is enemy-death drops,
> and that remains OPEN.

---

## A. Player weapon collision root — PARTIAL (located, not fully lifted)

- Rastan's action state machine dispatches on `A5+0x10E8` (`0x512xx..0x514xx`).
- **`0x51AB6`** builds a weapon-hitbox list into `A5+0x1134` from the table at **`A5+0x1280`
  (`0x10D280`)** — 3 boxes, weapon-dependent.
- **`0x51B04`** tests that hitbox list against the camera/map (`A5+0x10BE/0x10C0`) and sets the
  landing type `A5+0x13BE` (`0x51B74`). This is **world/landing** collision, **not** the enemy hit.

The **enemy-hurtbox scan** (weapon box vs enemy-actor box, writing a kill) was **not isolated**.
It is the exact next dependency (§M). Evidence: `h8_player_weapon_hit_path.tsv`.

## B. Enemy HP / damage model — PARTIAL

Proven (from the actor-vs-world contact side): `0x42E38` moves an actor and, for `rec_type < 5`, on
stepping onto a solid collision cell (`0x53A2E`, low-byte bit0) calls `0x447F0` → impact. The
**enemy HP field / one-hit-vs-multi-hit / invulnerability** model is **not located** — it lives with
the unresolved enemy-hurtbox scan. Evidence: `h8_damage_model.tsv`.

## C. Ordinary enemy fatal path — PARTIAL

Proven tail: death-animation completion (`0x44804`) → score (`0x3B726`, value `+0x2C`) → retire
(`0x4092E`); boss defeat via `0x469E8`. The **initiation** (weapon hit → enter dying) is the missing
front half.

## D. Item-drop eligibility — OPEN

Not isolated. No branch proving "this killed enemy drops / this one does not" was found this pass.
**No assumption of randomness or per-enemy eligibility is asserted.** Evidence stub:
`h8_enemy_drop_routes.tsv` (marked OPEN).

## E. Item selector / table — OPEN

Not located. `h8_item_table.tsv` is intentionally empty/OPEN — **no fabricated table**.

## F. Dropped-item creator — OPEN

Not located.

## G. All enemy-droppable item records — OPEN

Zero proven this pass. The number of droppable items remains an unproven OUTPUT.

## H. Fixed vs dropped vs scripted pickup routes — PARTIAL

`h8_pickup_creation_routes.tsv` keeps the three sources **separate**, as required:
- **(B) fixed / map-placed** — PROVEN in H6: letter markers materialize via `0x41180`/`0x41362`
  (e.g. state 0x20 torch/light), and the field schedule `0x4A104` (checkpoints A/B/C). This is the
  only pickup-placement mechanism proven so far.
- **(A) enemy-death drops** — OPEN (this is the H8 objective that remains).
- **(C) scripted pickups** — PARTIAL: the scripted-event dispatcher `0x4580C` (progression-gated,
  `A5+0x13E`) places actors via `0x45CFC`/`0x45342`.

**(B) does not explain (A).** No claim is made that all pickups are map-placed.

## I. Pickup collision / effect dispatcher — NOT REACHED

Not reached this pass (depends on locating the drop actor first).

## J. Score / drop / death ordering — PARTIAL

Proven ordering for the reachable tail: **death animation → score (`0x3B726`, `+0x2C`) → retire
(`0x4092E`)**. The drop-decision insertion point relative to score is unknown pending §D–§F.

## K. `0x3CEB0` animation core — COMPLETE

Fully lifted (`raw/0003ceb0.c`, semantic `rastan_anim_motion_core.c`):
- `0x3CEB0` — frame timing (`+0x07` init / `+0x08` duration / `+0x09` countdown), sequence advance
  (`+0x12` subcount, `+0x0E[0]` frames-remaining, `+0x0D` frame index, `+0x0F` step), then motion
  integration (`+0x16 += +0x14` vx, `+0x1A += +0x18` vy). Mid-frame → no change (rts).
- `0x3CF40` — frame-index wrap (0→56, 57→1).
- `0x3CF52` — frame → velocity from the byte-exact **56-entry direction ring `0x3CFD4`**, plus the
  `+0x13` axis-lock flags (lock vy / lock vx / band-conditional vx lock via `0x3CFB0` / mirror
  vx→vy). Table verified byte-identical to ROM.
- `+0x12` reload alternates `+0x10`/`+0x11` by 14-frame bands from 8.

This **closes `0x42E38`** (now COMPLETE): same core + the `rec_type<5` solid-cell → `0x447F0`
contact tail.

**Polymorphism note:** in the animated-actor context `+0x0D..+0x11` hold
{frame index, seq-remaining, step, reload-even, reload-odd} — the anim-context view of the same
bytes the hunter context (`0x41180`) uses as a collision-cell address. Documented in the header and
`rastan_anim_motion_core.c`; no single global name imposed.

## L. State-0x0F polymorphism — RESOLVED

Handler `0x40CCC` supports multiple semantic actors, distinguished by two fields
(`h8_state0f_polymorphism.tsv`):
- **`+0x03` (mode) ≠ 0** → `0x40E0E` (mode-driven materialized variant).
- **`+0x39` (component flag, set by `0x447F0`/`0x43F52`) ≠ 0** → `0x40DD8` (impact / burst
  component).
- **both 0** → the default **armored-man / standing-enemy** animation (`0x40CDC`, base `0x0A73`,
  frame table `0x40DCE`).

State 0x0F is **not** globally "death effect" nor globally "armored man" — it is one handler keyed
by `+0x03` and `+0x39`.

## M. Exact remaining dependencies

1. **Enemy-hurtbox scan** — the routine that overlaps the player weapon box (`A5+0x1134`, built by
   `0x51AB6`) against enemy actors and applies a kill/hit. This is the front half of the fatal path
   and the gate to the drop system. **Primary H9 target.**
2. **Enemy HP / hit model** and **conditional item-drop decision + item table + drop creator**
   (§B, §D–§G) — reachable once (1) is found.
3. `0x40E0E` / `0x40DD8` — the two non-default state-0x0F branches (referenced, not lifted).

## Verification

- Coverage guard: **PASS** — rows 63, COMPLETE 49, PARTIAL 9, STUB_ONLY 5; H5 10/10.
- Fidelity guard: **PASS**.
- `gcc -std=c11 -fsyntax-only`: **PASS** on the full tree (62 files).
- Historical audit: 47 rows (`0x3CEB0` STUB→COMPLETE, `0x42E38` PARTIAL→COMPLETE, state-0x0F
  resolution recorded, and the **enemy-drop system explicitly logged OPEN/NOT_STARTED** — not
  papered over).

## Related documents

`docs/design/Andy_h7_actor_lifecycle_damage_drop_decompilation.md` (retire/score/component),
`docs/design/Andy_h6_marker_materialization_decompilation.md` (fixed/map pickups placement),
`docs/design/Andy_actor_behavioral_identity_decompilation.md` (H5 handlers).
Evidence: `analysis/actor_decompilation/h8_player_weapon_hit_path.tsv`, `h8_damage_model.tsv`,
`h8_enemy_drop_routes.tsv`, `h8_item_table.tsv`, `h8_pickup_creation_routes.tsv`,
`h8_state0f_polymorphism.tsv`.
