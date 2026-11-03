# Andy — Bestiary Integrity Repair: Single Source of Truth + Materialized Cast

**Agent:** Andy · **Type:** Data-integrity + report-structure repair (NO new reverse engineering).
**Build counter:** 360 (unchanged). **NO ROM, NO MAME, NO Genesis change.** Cody files untouched.
**Artifact:** republished as Version 3 at `https://claude.ai/artifact/Dopg3mwMHdUMsZJSQgXDVR`.

This is the mandatory RULES.md standalone report for the bestiary integrity-repair pass. The prior
"synchronization through H9" pass updated the dashboard/metadata but left the manifest carrying
contradictory legacy structures and left the visual report as the old whole-round field roster. This
pass fixes the **source of truth** and makes the report show the actually-decompiled cast.

Authoritative source remains the original arcade 68000 program; this pass only reconciles existing
proven results (H5/H6/H7/H8/H9) into one non-contradictory manifest and regenerates the report.

---

## A. Problem addressed

Tighe inspected the regenerated artifact and found it was **not** a faithful view of how much of the
game cast we have decompiled:

1. Round pages showed only the `0x4A104` field families; the H5/H6 **materialized** actors were
   buried in prose/census.
2. The manifest declared `actors[]` the sole authoritative registry but still contained a competing
   `bosses.per_round[]` structure whose 6 records declared boss **base = 0x033E** (the deprecated
   family-2 model).
3. All 6 BOSS actor records simultaneously carried the real body base **and** the stale text
   *"per-round boss body NOT reconstructed. base 0x033E was the family-2 ROUTE…"* — self-contradiction.
4. The dashboard said the compositor VM was **"NOT REIMPLEMENTED"** while the same report rendered
   sprites through `compositor_vm.py`.
5. Field cards showed **IDENTITY PROVEN** while their descriptions said the name was a lexicon
   **PROPOSED** label.

## B. Source-of-truth fixes (manifest)

- **Quarantined the 0x033E boss model.** The top-level `bosses` key (with `base:"0x033E"` and 6
  `per_round[]` "boss_composite" records) was moved into
  `legacy_evidence.DEPRECATED_boss_0x033E_model` and the top-level key removed. It is never generated
  from. Real per-round boss bodies come only from `actors[]` (category `BOSS`): bases
  `0x061D / 0x0753 / 0x082C / 0x07BF / 0x0988 / 0x0B35` (record types 14/19/20/21/16/23) selected via
  `0x45330 → 0x4449E → 0x444E0[round-1] → 0x4543E → 0x45592`.
- **Cleared the boss self-contradiction.** All 6 BOSS actors' `unresolved_reason` (the
  "NOT reconstructed / 0x033E" text) was emptied — a boss record now carries only its real body base,
  record type, and render, with no denial.
- **`actor_registry_note` made explicit:** `actors[]` is the SOLE semantic registry driving the
  bestiary; `per_round_boss_body_map` / `actor_census_from_rom` are derived references only.

## C. Materialized cast surfaced (12 + 1 controller)

Added `actors[]` entries for the H5/H6 materialized actors that were previously only in the census,
each with its `materialization_route` (marker → state → handler), spawn sites, and honest
`PENDING` identity/round/frame:

| Base | Category | Route (H5/H6) |
|---|---|---|
| `0x033E` | **CONTROLLER** | hidden family-2 scanner (Y=0x180, anim 0x93) — materializes others via 0x41180/0x41362; **not a sprite** |
| `0x00F4` | materialized | marker 'H' → state 0x1E → 0x40E88 (base 0x0F4 → retarget 'O') |
| `0x0DAB` | materialized | marker 'O'..'Q' → state 0x20 → 0x40EDE (base 0xDAB → retarget 'I') |
| `0x09EA` | materialized | multi-site marker-chain **transform** base (0x40FAC/FCC/0x42722/0x438DC…) — NOT one projectile |
| `0x0179` | materialized | state 0x15 handler @0x438B6 |
| `0x0224` `0x0266` `0x0235` `0x09F6` `0x01FC` `0x0236` `0x0546` `0x05E9` `0x0D5F` | materialized | H5 state handlers (0x43xxx) |

Each renders a **RAW TILE EVIDENCE** thumbnail (labeled, not composited); legal frame + human name +
exact round remain PENDING. A new **Materialized / Marker-Driven Actor Gallery** displays them before
the per-round sections.

## D. Contradiction fixes (generator + badges)

- **Compositor status** corrected everywhere to match `compositor_vm.py`: *"IMPLEMENTED for general
  modes (renders field + boss bodies); special program modes unvalidated (raise
  SpecialCompositorProgram)."* The string "NOT REIMPLEMENTED" is gone.
- **OBJECT vs NAME split.** Card badges now show **OBJECT PROVEN** (the technical base/object is real)
  separately from **NAME {PROVEN|PROPOSED|PENDING}** (the human label). "IDENTITY PROVEN" is
  eliminated. 5 lexicon names were downgraded `PROVEN → PROPOSED` (no arcade-string proof).
- **Boss frame honesty.** R1/R5 (MAME-verified) show **FRAME VERIFIED / PALETTE VERIFIED**;
  R2/R3/R4/R6 show **FRAME STATIC / PALETTE line-inferred** (ROM init-anim only).
- **0x09EA correction** retained and reinforced: transform base, not "common projectile"; the genuine
  thrown/projectile is the marker 'I' → record-type-1 → `A5+0x588` template route.

## E. Report structure (visual priority)

The generator was reordered so the game cast comes first and the technical census sits at the bottom:

1. Status dashboard → 2. What we now know → 3. Field / Sub-Round-1 Gallery →
**4. Materialized / Marker-Driven Gallery** → 5. Scripted / Special Gallery →
6. Bosses (six distinct bodies) → 7–12. Rounds 1–6 (Sub-Round 1 / Sub-Round 2 / Boss) →
13. Projectiles / Effects → 14. Hazards → 15. Items / Power-ups → 16. Unresolved Actor Gallery →
17. Technical / Decompilation Appendix (full 45-row census + phase mechanism + TT map + remaining).

Per round, Sub-Round 2 now carries a materialized-cast note pointing to the master gallery (exact
per-round assignment PENDING).

## F. Consistency guard (prevents recurrence)

`consistency_check()` runs in `build_bestiary.py` **before** HTML is written and fails generation on:
active top-level `bosses` / any BOSS actor using 0x033E; boss-base disagreement between `actors[]` and
`per_round_boss_body_map`; a dashboard "NOT REIMPLEMENTED"; a boss `unresolved_reason` denying
reconstruction; a materialized/controller over-claiming FRAME PROVEN; and any field actor whose
`name_status=PROVEN` while its description flags lexicon/PROPOSED. **Current run: PASS.**

## G. Items / drops (unchanged — still OPEN)

Enemy-death drops remain **OPEN** (H9 found no per-kill drop creator; not fabricated). The Items
section keeps the three separated categories: enemy-death drops OPEN; marker-placed (H6) mechanism
proven / identities partial; scripted/positional (0x450D8 → 0x45248) mechanism proven / identities
partial. Droppable item types statically proven: **0**.

## H. Counts (unique, not img-tag inflated)

- `actors[]` = **36**: 11 field · 12 materialized · 1 controller · 3 scripted · 3 unresolved · 6 boss.
- Unique H5/H6 materialized actors represented visually: **12** (+1 controller), all RAW TILE.
- Boss bodies: **6/6**; verified frames **2/6**; static frames **4/6**.
- Census (appendix): 45 distinct bases (37 PENDING / 7 PROPOSED / 1 PARTIAL).

## I. Files changed

`docs/design/rastan_actor_graphics_manifest.json`, `tools/graphics_optimizer/build_bestiary.py`,
`tools/graphics_optimizer/bestiary_style.css`, `docs/design/rastan_actor_bestiary.html`,
`AGENTS_LOG.md`, and this report.

## J. What remains (unchanged by this pass)

Enemy-death → item-placement link (the H9 open gap); exact droppable-item roster; per-round pinning
of the materialized cast; legal composited frames + palettes for the materialized actors and for
R2/R3/R4/R6 bosses; the exact per-round 0x7E door boundary. This was a report-integrity pass, not new
reverse engineering.

## Related documents

`docs/design/Andy_h9_enemy_hit_drop_system_decompilation.md`,
`docs/design/Andy_h8_enemy_damage_item_drop_decompilation.md`,
`docs/design/Andy_h6_marker_materialization_decompilation.md`,
`docs/design/Andy_actor_decompilation_c_recovery.md`.
