# PROMPT-ID-0025 — R1-S2 Actor/Sprite Inventory + Arcade 68000 Decompilation Audit

**Author:** Andy · **Date:** 2026-10-28 · **Static only — NO traces.** No Genesis ROM/runtime/compiler
change, no build number consumed, no user palette/Test.json touched. This session staged only its own
analysis artifacts.

This report is honest about what is **done and verified** versus what **remains**, per the prompt's
explicit anti-overclaim requirement. **The Palette Composer integration (Deliverable D) is NOT yet done**
— see §Status. What is delivered is the audit, the verified R1-S2 marker roster, the castle sprite-base
identification, and static regression tests, which are the foundation the integration builds on.

---

## Ghidra C Decompilation — Actual Repository Deliverables (the premise, corrected)

The brief states a prior "little usable C decompilation" was found. **That is not the current repository
state.** Verified facts:

- `analysis/decompilation/c/` contains **141 maintained C files, 16,659 lines**, with real function
  bodies (not stubs). The actor subsystem specifically:
  - `rastan_actor_behavior.c` (563 lines, ~27 functions) — the state handlers, incl. `actor_armored_40ccc`
    (state 0x0F, base 0x0A73 "armored man (sword)") and the `h5_*` castle state bodies.
  - `rastan_actor_dispatch.c` — the 35-entry state jump table at 0x40BAA (COMPLETE).
  - `rastan_actor_materialization.c` — the marker→state→actor H6 architecture (latent hunter 0x033E,
    collision-map marker scan, 26-way char dispatch).
  - `rastan_actor_tables.c` — the real `ActorTemplate` tables (`family_var0_45502`, `family_varN_45562`,
    `record_type_45592`) read from `maincpu.bin`, with semantic labels.
  - `rastan_actor_creation.c`, `_helpers.c`, `_lifecycle.c`, `_collision.c`, `_palette.c`, `_render.c`,
    `_subsystems.c`, plus `rastan_arcade_types.h` (the `ActorRecord`/`ActorTemplate` layout).
- Coverage ledger `analysis/decompilation/c/function_coverage.csv`: **151 functions, 141 COMPLETE / 10
  PARTIAL**; provenance 143 RECONSTRUCTED_FROM_68000 / 8 GHIDRA_RAW; `raw/` holds the close-to-machine
  reconstructions keyed by original PC.
- Each function carries its original arcade PC and provenance (e.g. `/* ORIGINAL ARCADE PC: 0x00040BAA */`).

Conclusion: the maintained 68000 C reference **exists and is substantive** (Deliverable A largely in
place; Deliverable B = `function_coverage.csv`). The actor system — the subject of this prompt — is among
the most complete parts. **Armored Men are already decompiled** (`actor_armored_40ccc`, base 0x0A73).

---

## §4/§6 — R1-S2 (castle) actor roster from static evidence

The castle actors are produced by the **marker materialization** system (H6, fully proven in
`h6_marker_materialization_routes.tsv`): a latent family-2 hunter (base 0x033E) scans the collision grid
for marker characters (the high byte of each collision word), and a 26-way char dispatch assigns a state,
which assigns the visible sprite base.

**R1 phase-2 markers** (`h13_phase2_marker_occurrences.tsv`) — phase-2 = subrounds S2 (castle) + S3 (boss);
the S3 boss is **record-type** driven (not marker driven), so the phase-2 **markers are the S2 castle**:

| Marker | char | occ. | state | handler | sprite base(s) | decodes? |
|---|---|---|---|---|---|---|
| `0x45` | 'E' | 6 | 0x18 | 0x44082 (`h5_44082`) | **0x0224** (primary), **0x00F4** (retarget 'O'/'U') | yes (8–10 pieces) |
| `0x4d` | 'M' | 1 | 0x1B | 0x43ECC (`h5_43ecc`) | burst spawner (5 children, anim 0x7A; coordinate-only) | child-seeded |

- **R1-S3 boss** (separate, record-type): body base **0x061D** (`record_type_45592[0x0E]`).

Both marker-'E' bases **decode to real multi-piece humanoid sprites** via the static compositor VM
(`tools/graphics_optimizer/compositor_vm`, the Bestiary's render route — **not a trace**):
`0x0224` → 218 anims with ≥2 pieces (8–10-piece frames, tile codes 0x22B–0x2EF); `0x00F4` → 4–9-piece
frames (tile codes 0xF4–0xF7). Roster artifact: `analysis/actor_decompilation/r1s2_actor_roster.json`
(regenerate with `tools/graphics_editor/gen_r1s2_actor_roster.py`).

**Armored Men / Wizards mapping (honest):** Tighe's labels correspond to these marker-driven castle
actors — the marker-'E' humanoid bases (`0x0224` primary, `0x00F4` secondary) and the marker-'M' burst
emitter. **Which base is "Armored Man" vs "Wizard" is not asserted here** — that visual label must be
confirmed by viewing the decoded graphics in the Composer (the integration step). The roster records the
bases + evidence; it does not fabricate the visual name. (`actor_armored_40ccc`/base 0x0A73 is a separate
death/transform presentation already labeled "armored man" in the existing decompilation.)

**Open static blocker (unchanged):** the exact per-scene **S2-vs-S3 marker split** depends on the runtime
`A5+0x10D000` collision-record populator (the "column marker source"), which is not statically enumerated
(`h11_phase2_actor_rosters.tsv`). The attribution above uses the record-type-vs-marker distinction, which
is sound, but the precise per-column marker placement in S2 remains the documented open item.

---

## §10/E — Static regression tests (NO traces)

`tools/graphics_editor/verify_r1s2_actor_roster.py` — **5/5 PASS**:
1. R1 phase-2 has marker occurrences.
2. R1 marker states agree between h13 occurrences and h6 routes.
3. every resolved castle base decodes to ≥2 pieces (static compositor VM).
4. R1 boss body base 0x061D matches `record_type_45592[0x0E]`.
5. castle bases 0x0224/0x00F4 are NOT in the current Composer catalog (confirms the gap).

---

## Status — done vs remaining (no false completion)

**Done & verified this session:**
- Audit of existing decompilation (Deliverable B = `function_coverage.csv`; premise corrected).
- R1-S2 castle marker roster + sprite-base identification, static-only (Deliverable C):
  `analysis/actor_decompilation/r1s2_actor_roster.json` + generator.
- Static regression tests (Deliverable E): 5/5.

**Remaining (honestly NOT done):**
- **Deliverable D — Palette Composer integration.** The castle actors (`0x0224`, `0x00F4`, the 'M' burst)
  are **not yet browsable in the editor.** The decode path is proven (`_manifest_vm_pieces` already uses
  `compositor_vm`), but faithful exposure needs: (a) the castle actors' **sprite palette-bank** resolution
  (so their arcade source colors are correct, not black — the same class as the reward/pickup bank gap),
  (b) additive catalog entries in `build_usages` labeled as R1-S2 castle actors (preserving all existing
  usages), ideally scene-gated so they are not shown as R1-S1 assets, and (c) browser verification
  (selection, frame navigation, piece display, save/reload) — which cannot be done headlessly.
- **Visual Armored-Man/Wizard labeling** — depends on viewing the decoded frames (the integration).
- Full completeness of the marker-'M' burst child presentation (coordinate-only / seeded SAT) to the
  prompt's bar.

**Next step / concrete plan for D:** resolve the `0x0224`/`0x00F4` sprite palette banks from the actor
attribute path (`+0x29` / per-round sprite palette), add them to the sprite catalog via the proven
`_manifest_vm_pieces` decode (additive, labeled `R1-S2 CASTLE`), add a headless test that the new usages
carry real pieces + resolved colors, and hand the browser checks (naming confirmation included) to Tighe.

---

## Files (staged this session — analysis only)
- `tools/graphics_editor/gen_r1s2_actor_roster.py` (roster generator, static)
- `tools/graphics_editor/verify_r1s2_actor_roster.py` (static regression, 5/5)
- `analysis/actor_decompilation/r1s2_actor_roster.json` (generated roster)
- this report + `AGENTS_LOG.md`
