# Andy — CHECKPOINT H9: Enemy-Hurtbox Scan + Conditional Item Drops

**Agent:** Andy · **Type:** Static reverse engineering (ORIGINAL ARCADE 68000). NO MAME, NO ROM,
NO Genesis change. **Build counter: 360 (unchanged).**
**Manifest/bestiary/`build_bestiary.py`:** NOT modified — no dropped-item actor was statically
proven (see §F/§G/§I), so per the H9 rule they are left untouched. Cody files untouched.

Mandatory RULES.md standalone report for CHECKPOINT H9. Authoritative source:
`build/regions/maincpu.bin` + `build/maincpu.disasm.txt`.

> **Result summary.** H9's #1 objective — the enemy-hurtbox scan that H8 could not isolate — is
> **FOUND and decoded**: the per-frame enemy **collision manager `0x449B4`**, the AABB primitive
> `0x44CBA`, the hurtbox rectangle table `0x44CE0`, and the **one-hit damage model** and complete
> fatal path. The **conditional item-drop creator** was **not** located: the fatal path reaches
> score + explosion + retire with no item creation, and the only item-producing code found is the
> **scripted/position-triggered** spawner `0x450D8→0x45248` (category C) and the H6 markers
> (category B). No item table was fabricated. §L gives the exact remaining dependency.

---

## A. Weapon-box consumers

`A5+0x1134` (the buffer H8 flagged) has **exactly two** consumers — `0x51ABE` (builder `0x51AB6`)
and `0x51B04` (world/landing test). Both are **Rastan's BODY box**, not a weapon-vs-enemy buffer.
The enemy scan instead uses per-category player boxes at `A5+0x28C` (weapon: set to `{16,-2040}` at
`0x44BA6`), `0x2B0`, `0x1248`, `0x1254`, `0x22C`. Frame order (top-level `0x41F0E`):
main loop `0x5100A` → actor update `0x40B66` → **`0x449B4` collision** → `0x420E6` (A5+0x508 pool)
→ `0x443E0` → `0x450D8` spawn.

## B. Enemy-hurtbox scanner — `0x449B4` (PARTIAL)

Runs once per frame. Multi-pass over the `A5+0x2C8` enemy pool (29 slots), and a projectile/weapon
box list at `A5+0x1338` (pass 4). Per enemy (active `+0x00`, `state != 0`, not hit-flashing
`+0x3D == 0`): build hurtbox index (`0x446BC`), dispatch overlap (`0x44930`/`0x44C5A`..) against the
selected player box, and on overlap record a hit `{active, type, +0x28/+0x29, X=+0x16, Y=+0x1A}`
into the hit list `A5+0x12A8` (body) / `A5+0x12C8` (secondary) — up to 4 — then run the reaction.
COMPLETE: the overlap primitive and hurtbox tables. PARTIAL: the full pass predicate ladder and the
`A5+0x1338` producer. Raw `raw/000449b4.c`.

## C. Hurtbox format — PROVEN

`0x446BC` returns an **index** by `rec_type`(+0x06)/`family`(+0x3E)/`state`/overrides
(`+0x37`/`+0x55`/`+0x30`/`+0x02`). `index*4` selects a **4-signed-byte rectangle**
`{x_left, x_right, y_top, y_bottom}` from table **`0x44CE0`** (variant **`0x44FA8`** when `+0x38==2`).
First entries (byte-exact): `idx0 {-12,12,-20,16}`, `idx1 {-12,12,-16,24}`, `idx2 {-12,12,-8,18}`,
`idx3 {-3,3,-8,8}`. Overlap primitive **`0x44CBA`** adds `+0x80` bias, tests per axis
(X then Y via the `0x44CB0` swap). Raw `raw/00044cba.c`, `raw/000446bc.c`.

## D. Damage / HP model — PROVEN

**Ordinary enemies are ONE-HIT — there is no HP accumulator.** A recorded overlap directly starts
the death: `0x447CE` sets the hit-flash flag `+0x3D=1` and (unless `rec_type==7`) runs `0x448B2`
→ `state 0x0F` death/impact animation + sfx `0x10`. Variants: `family 12` → immediate
score(`+0x2C`)+recycle (`0x448D8`); `rec_type 10/11/18` → freeze (`0x447B6`). Re-hit is suppressed by
`+0x3D` (the scan skips `+0x3D != 0`; the flag counts down via `0x40B52`). Raw `raw/000447ce.c`.

## E. Fatal path — PROVEN (end-to-end)

`overlap (0x449B4)` → `+0x3D flash + state 0x0F death anim (0x448B2)` → death-anim complete
(`0x44804`) → **score `0x3B726` (value `+0x2C`)** → **retire `0x4092E`**. This joins the H7/H8 tail.

## F. Drop eligibility — OPEN (no per-kill creator found)

The fatal path (§E) reaches score + explosion component + retire and **creates no item**. The hit
lists `A5+0x12A8/0x12C8` feed death sparks/effects, not pickups. No branch conditioning a per-enemy
item drop (by family / rec_type / kill-counter / RNG) was found on the death path.

## G. Drop selector / table — OPEN (not fabricated)

`h9_drop_item_table.tsv` is intentionally OPEN. The only item-producing code found is the
**scripted / position-triggered** spawner `0x450D8 → 0x45248`, which places actors with bases
`0x0F4`, `0x224`, `0x548` (etc.) gated by camera position `A5+0x2DE` and a sub-sequence counter
`A5+0x21C`. Whether any of these are "drops" tied to a specific enemy kill (via a kill flag) is
**unproven**; no per-kill selector/table exists in the reachable code.

## H. Item actor creator — via scripted spawner `0x45248` (category C)

`0x45248` (the parameterized creator, 18 callers, lifted earlier) is the actor that instantiates the
scripted item/enemy records. It is **not** invoked from the enemy fatal path. Its full pickup-actor
initialization (velocity/lifetime/pickup-collision state) is the natural next lift once the
enemy→item link is established.

## I. Droppable item roster — 0 proven this pass

Because no per-kill drop creator was found, no enemy-droppable item actor is proven. **No fabricated
roster.** The manifest/bestiary are therefore not updated.

## J. Pickup collision / effect — NOT REACHED

Depends on first identifying a concrete dropped/pickup actor state.

## K. Fixed vs dropped vs scripted relationship

- **(B) fixed / marker-placed** — PROVEN (H6), `0x41180`/`0x41362` letter markers.
- **(C) scripted / positional** — PROVEN, `0x450D8 → 0x45248` (per-round scripts + camera-gated).
- **(A) enemy-kill drop** — OPEN. On current evidence, "an item appears when you kill an enemy" is
  most consistent with **(C)/(B)** placement (possibly gated by a kill flag), **not** a dedicated
  per-kill drop creator. Kept strictly separate; (B)/(C) are **not** claimed to explain (A).

## L. Exact remaining dependencies

1. **The enemy-death → item link.** Determine whether a specific enemy's death (in `0x447CE`/state
   0x0F completion, or a family/rec_type-specific branch) sets a flag/counter that the scripted
   spawner `0x450D8` (or a marker) consumes to place an item. This is the precise gap between the
   proven kill path (§E) and the proven item placement (§G/§K). **Primary next target.**
2. `0x446B0` base-index helper and the family hurtbox table `0x44796` (keeps `0x446BC` PARTIAL).
3. The `0x449B4` full pass ladder + the `A5+0x1338` weapon-box producer (keeps `0x449B4` PARTIAL).
4. `0x40E0E` / `0x40DD8` non-default state-0x0F branches (do not intersect the drop path; deferred).

## Verification

- Coverage guard: **PASS** — rows 68, COMPLETE 52, PARTIAL 11, STUB_ONLY 5; H5 10/10.
- Fidelity guard: **PASS**.
- `gcc -std=c11 -fsyntax-only`: **PASS** on the full tree (67 files).
- Historical audit: 50 rows (enemy-hurtbox scan recorded FOUND/PARTIAL; per-kill drop creator kept
  explicitly OPEN/NOT_STARTED — not papered over).

## Related documents

`docs/design/Andy_h8_enemy_damage_item_drop_decompilation.md` (anim core, state-0x0F, the H8 gap),
`docs/design/Andy_h7_actor_lifecycle_damage_drop_decompilation.md` (retire/score/component),
`docs/design/Andy_h6_marker_materialization_decompilation.md` (fixed/marker item placement).
Evidence: `analysis/actor_decompilation/h9_weapon_enemy_collision.tsv`, `h9_enemy_damage_model.tsv`,
`h9_enemy_drop_eligibility.tsv`, `h9_drop_item_table.tsv`, `h9_item_creation_routes.tsv`,
`h9_pickup_effects.tsv`.
