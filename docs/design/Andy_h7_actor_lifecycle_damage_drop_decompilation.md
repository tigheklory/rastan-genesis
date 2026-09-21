# Andy — CHECKPOINT H7: Active Actor Step, Retire, Damage/Contact, Score, Drop

**Agent:** Andy · **Type:** Static reverse engineering (ORIGINAL ARCADE 68000). NO MAME, NO ROM,
NO Genesis change. **Build counter: 360 (unchanged).**
**Manifest/bestiary/`build_bestiary.py`:** NOT modified (H7 exposed no *new* visual actor base — see §I).
Cody verification files untouched.

Mandatory RULES.md standalone report for CHECKPOINT H7. It closes the shared actor **retire/clear**
primitive `0x4092E` (the sole reason `0x4103A` was PARTIAL after H6) and follows the directly
reachable gameplay consequences: contact→impact, death-component/burst, score award, and the
item/drop question. Authoritative source: `build/regions/maincpu.bin` + `build/maincpu.disasm.txt`.
Reconstructed C is an auditable representation, **NOT original Taito source**.

---

## A. `0x4092E` complete semantic flow

`0x4092E` is the shared **actor RETIRE / CLEAR** primitive (40+ callers), **not** a stepper. It:
1. Zeroes the entire `0x40`-byte `ActorRecord` via a propagating word fill (`0x3A2D0`: clear
   `word[+0]`, then copy-forward 31 words).
2. Chooses a companion-block byte delta from the record's pool region — `record-end < 0x10C508`
   → `0x702`, otherwise → `0x4E2` — and zeroes a 16-word (`0x20`-byte) **paired companion block**
   at `record + delta` (the actor's render/scratch mirror).

Clearing `+0x00` (active) makes the slot immediately reusable by the occupancy scan `0x49F30`. No
fields survive; callers needing to keep identity save/restore around the call (see `0x40A1E`).
Raw: `raw/0004092e.c`. Semantic: `rastan_actor_lifecycle.c: actor_retire`.

## B. Retirement / deactivation paths (proven)

| Path | PC | What clears the actor |
|---|---|---|
| Ordinary retire/clear | `0x4092E` | zeroes record + companion block |
| Off-screen retire | `0x427B2` | clears `+0x00` directly (already lifted) |
| Schedule-preserving recycle | `0x40A1E` | saves `+0x26/+0x38/+0x753`, calls `0x4092E`, re-inits via `0x4A0D8`, restores id |
| Projectile expire / reached owner | `0x421A8`, `0x42204`, `0x4220A` | `0x4092E` (`0x4220A` also spawns effect `0x457D0`) |
| Component state-0 in a pool | `0x43F52` | `0x4092E` per inactive-state member |

The slot becomes reusable immediately (occupancy scan sees `+0x00==0`); graphics/state fields are
all zeroed; parent/child links are not specially preserved except by the recycle path.

## C. Damage / contact → death transition

The reachable damage model for moving rec_type actors (projectiles, thrown objects, low-rec_type
enemies) is in **`0x42E38`**: it advances animation timing (via the `0x3CEB0`-family core), applies
velocity (`+0x16 += +0x14`, `+0x1A += +0x18`), and for `rec_type < 5` probes the collision grid
(`0x53A2E`) at the new position; if the cell's low-byte **bit 0 is set (solid)** it calls
**`0x447F0`** → impact. `0x447F0` marks `+0x3D=1` and (unless `rec_type 7`) runs `0x448B2`:
`+0x05 = 0x0F` (state 0x0F, handler `0x40CCC`), `+0x08=0xFF`, `+0x09=1`, **sfx `0x10`** — the
impact/settle animation. `0x42E38` is **PARTIAL** (its `0x3CF40/0x3CF52` anim-index core is the
still-STUB `0x3CEB0` family); the move+contact control flow is COMPLETE.

The player-weapon-vs-enemy hit test (the other damage direction) is a separate collision engine in
the `0x53xxx` region and is the exact next dependency (§J) — it is not anchored to `0x4092E` and is
out of H7 scope.

## D. Score award

**`0x3B726` = score award (BCD), COMPLETE.** `d0` = increment as a packed BCD word; it stages the
addend at `A5+0x119..0x11B` and BCD-adds (three chained `abcd` lanes) into the 3-byte score
accumulator at **`A5+0x11C..0x11E`** (6 digits), clamping to `999999` on overflow. It then tests the
extra-life threshold at `A5+0x306/0x307` and, on crossing, awards a life (`0x59EE0` + sfx 5 +
`A5+0x100`/`A5+0x102` counters ++) and refreshes the digits (`0x3B802`). Gated by `A5+0x34`
(rendering active).

**Score value source = the dying actor's `+0x2C` (`cfg_2c`) template word.** Call sites:
`0x44862`/`0x44874`/`0x448E4` (component death-animation completion in the `0x44804` stepper, for
rec_types 8/9/11) and `0x46AAC` (boss defeat `0x469E8`, rounds 5/6). Raw: `raw/0003b726.c`.

## E. Drop / item entry point

**NOT REACHED.** No death-triggered drop/item creator is reached from any traced path
(`0x4092E`, the `0x447F0`/`0x3B726` death cluster, or the boss-defeat handler). Enemy death awards
score and spawns explosion/impact **components** (state 0x0F), then retires — it does not allocate a
pickup.

This resolves the long-standing "item/drop system not located" note: **Rastan does not drop items on
kill.** Pickups/power-ups are *placed in the level* by the marker-materialization system decompiled
in **H6** (the letter-marker → `0x41180`/`0x41362` route, e.g. torches/light via state 0x20) and by
the **field schedule** (checkpoints A/B/C). There is no death→drop RNG in the reachable code. If a
future pass wants to confirm a per-scene item placement table, it lives in the marker/schedule data,
not in the lifecycle path.

## F. `0x447F0` child identity

`0x447F0` (raw `raw/000447f0.c`) activates a record as a live sub-component: `+0x3D=1`, and unless
`rec_type == 7` runs `0x448B2` → **state `0x0F`** (handler `0x40CCC`), `+0x08=0xFF`, `+0x09=1`, sfx
`0x10`. From `0x43F52` these are the members of a **component pool** (segmented enemy / burst /
explosion group); their graphics **base/anim/palette are written by the PARENT** that filled the
pool before activation, so the concrete visible identity is parent-defined — **semantic class =
multi-part component / impact sub-actor, IDENTITY PENDING** (no human name asserted from code alone).
`rec_type 7` members keep their parent-assigned state (no forced state 0x0F).

## G. `0x41F9C` jump behavior

`0x41F9C` (raw `raw/00041f9c.c`, COMPLETE) is a 7-instruction **phase-advance leaf**: it advances a
packed phase byte (low-nibble sub-counter carrying into a high-nibble frame index via a nibble swap)
and returns the recombined value. The jumping attacker (state 0x19) and similar cyclic actors call
it, store the result back to `+0x21`/`+0x33`, mask `&0x30` to pick the arc phase (rising/apex/
falling), and step `+0x1A` (Y) in the **caller** `0x41FAC`. So `0x41F9C` itself is the counter step;
the launch/arc/landing arithmetic is in `0x41FAC` (referenced; the H5 state-0x19 owner `0x4396A`
remains PARTIAL). No secondary actor is emitted by the leaf.

## H. `0x09EA` creator / emission map

Base `0x09EA` is written at **9 sites** (`analysis/actor_decompilation/h7_base_09ea_sites.tsv`).
Correcting the prior assumption: `0x09EA` is **not one emitted projectile** — it is predominantly a
**marker-chain transform base** (the "next actor" a hunter/transform state becomes):
- `0x40FAC`, `0x40FCC` — state 0x20 torch retarget (H6), retarget chars `'a'`/`'q'`.
- `0x438DC`, `0x43C9E`, `0x43D44`, `0x43DD8`, `0x43E80`, `0x43FF6` — H5 transform states
  (`0x43840`/`0x43B32`/`0x43F88`) assigning the next base after `0x4103A` retarget.
- `0x42722` — a looping rec_type actor's reload (after 3 anim cycles), a transform, not a fresh
  emission.

None of these is a single "throw a projectile" creator; `0x09EA` is a shared transform base reused
across the marker chain. The genuine thrown/projectile record is the `'I'` route (H6): `0x41B32`
sets `rec_type=1` and copies a full record from the `A5+0x588` template (`h7_child_emission_routes.tsv`).

## I. Newly exposed actor classes

- **Impact / explosion component** — state `0x0F`, activated by `0x447F0`, announced by sfx `0x10`;
  parent-supplied graphics (IDENTITY PENDING).
- **Component-pool / segmented-object member** — driven by `0x43F52`; state 0x0F or retired.
- **rec_type-1 thrown/projectile** — `'I'` route, template from `A5+0x588` (identity via that
  template, IDENTITY PENDING).

No *new* fixed graphics base was proven (identities are parent/template-supplied), so the manifest /
bestiary are **not** modified — per the H7 rule ("do not touch the bestiary merely to change status
text"). Evidence for a future bestiary pass is in the H7 TSVs.

## J. Remaining exact dependencies

- **`0x3CEB0` family** (`0x3CF40`/`0x3CF52`) — the animation-frame index core; keeps `0x42E38`
  PARTIAL. STUB.
- **Player-weapon-vs-enemy collision** (the `0x53xxx` hit engine) — the "enemy takes a sword hit"
  detection that *initiates* death; separate from the `0x4092E`-anchored path. **This is the exact
  next undecompiled dependency.**
- `0x457D0` impact-effect spawn (rec_type 0x0F) and `0x59EE0` bonus setup — referenced, not lifted.

## Verification

- Coverage guard: **PASS** — rows 61, COMPLETE 45, PARTIAL 10, STUB_ONLY 6; H5 10/10.
- Fidelity guard: **PASS**.
- `gcc -std=c11 -fsyntax-only`: **PASS** on the full tree (58 files).
- Historical audit: 44 rows (`0x4092E` STUB→COMPLETE, `0x4103A` PARTIAL→COMPLETE,
  `0x447F0`/`0x41F9C`/`0x43F4E` STUB→COMPLETE, `0x3B726` + no-death-drop finding recorded).

## Related documents

`docs/design/Andy_h6_marker_materialization_decompilation.md` (marker→state→base + item placement),
`docs/design/Andy_actor_behavioral_identity_decompilation.md` (H5 handlers, state 0x1B burst),
`docs/design/Andy_actor_decompilation_c_recovery.md` (C-tree contract + guards).
Evidence: `analysis/actor_decompilation/h7_active_actor_paths.tsv`, `h7_child_emission_routes.tsv`,
`h7_score_drop_routes.tsv`, `h7_base_09ea_sites.tsv`.
