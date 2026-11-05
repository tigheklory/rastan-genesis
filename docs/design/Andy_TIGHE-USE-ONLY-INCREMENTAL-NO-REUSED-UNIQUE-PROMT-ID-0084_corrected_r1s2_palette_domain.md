# PROMPT-ID-0084 — Corrected R1-S2 green-warrior palette domain + reusable arcade capture

**Author:** Andy · **Date:** 2026-11-05 · **Method:** Cody's ORIGINAL ARCADE sweep (PROMPT-ID-0080) +
arcade 68000 decompilation/compositor-VM; no ROM build, no build-counter change, no Test.json change, no
Cody production source touched.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0084`

## TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0084 Result

PROMPT-ID-0078's "complete 17-program / 77-code" green-warrior claim is **corrected and retired**. Using
Cody's source-backed PROMPT-ID-0080 audit, the Palette Composer, the offline generator, and the
regression verifiers now represent the **29-program / 109-code** proven warrior domain, with **honest**
pose labels, the `$74` torch kept out, the complete sword artwork `26B-274` covered, and the
two-layer palette provenance (embedded defaults **and** the actor `+$27` bit-6 override) surfaced rather
than flattened. A single reusable ORIGINAL ARCADE marker-capture harness is added and smoke-tested for the
still-unresolved weapon/hazard questions. Test.json was not changed; no ROM was built.

## Cody 0080 Findings Accepted

Accepted in full as the starting evidence:
- warrior identity family-2 `$033E`, canonical object `object:castle.green_sword_knight`, decision
  `PAL-PC090OJ-R1S2-GREEN-SWORD-KNIGHT-001` (not renamed);
- the 12 additional state-`$1F` programs `$97-$9C` and `$A1-$A6` (1,286 `$033E` sweep observations, 232 at
  state `$1F`) → corrected union **29 / 109**;
- `$71-$73` is a state-`$0F` short reaction/effect, **not** a proven crouch;
- `$74` is the torch (`$0DAB`), not the warrior;
- two-layer palette provenance (embedded bit-6-clear defaults vs the `$44/$41` actor override);
- sword is an attached piece of the same programs, **zero** code overlap with Rastan's player weapons;
- hammer/axe/flame-sword and all R1-S2 hazards UNRESOLVED — do not fabricate.

I independently re-derived the 29-program union through the committed compositor VM
(`tools/graphics_optimizer/compositor_vm.py`, selector-0 table `0x3D09E`): it reproduces Cody's exact
**109 codes** and the **32 new** codes `26D-274` + `389-3A0`, including the complete sword artwork `26B-274`.

## Corrected Warrior Domain

| Pose group | Programs | Arcade selector | anim_state label |
|---|---|---|---|
| Normal walk/idle | `$93-$96` | ground `0x47140` + state-$11 `0x4684E` (+$3E==2) | `normal` |
| Short reaction/effect | `$71-$73` | state-$0F alt `0x40E0E` (+$03!=0, sfx $17, base-preserving) | `short_reaction` (crouch **pending**) |
| Airborne / low | `$20-$23` | airborne `0x473B8` states $0D/$0E | `airborne` |
| Low/weapon action A | `$A1-$A6` | state-$1F `0x42EF8`, +$21 bit2==0, table `0x42FBC` | `low_action_a` |
| Low/weapon action B | `$97-$9C` | state-$1F `0x42EF8`, +$21 bit2!=0, table `0x42FD4` | `low_action_b` |
| Rope climb | `$4D,$56-$5A` | state-$11 `0x4684E` rope branch (+$3E==8, shared sheet) | `rope` |

**Old 0078 count:** 17 programs / 77 codes. **Corrected:** **29 programs / 109 codes**.
**Exact missing programs added:** `$97,$98,$99,$9A,$9B,$9C` and `$A1,$A2,$A3,$A4,$A5,$A6` (the two
state-`$1F` tables), contributing the 32 new codes `26D-274` and `389-3A0`.

## State `$1F` Programs

Added as two provisional pose groups. Both are **PROVEN DISPLAYED** by the arcade sweep but their exact
human gameplay names and the meaning of `+$21 bit2` are **not** proven, so the UI labels stay
"Low/weapon action A/B — state $1F". `$A1-$A6` is table `0x42FBC`; `$97-$9C` is table `0x42FD4` (which
also writes `+$37=$61`). Both exercise the full sword artwork `26B-274`.

## Short Reaction `$71-$73`

Relabeled from the 0078 "crouch" to the honest **"Short reaction/effect — crouch visual pending
($71-$73)"** (`anim_state=short_reaction`). The verifier now fails if any frame is labeled a proven
`crouch` or if the `$71-$73` label drops "pending". Whether this is the duck pose Tighe observed is a
runtime question for the capture harness below.

## Warrior Sword

The sword is an attached piece inside the warrior's own programs, not a separate actor. Complete
moving-weapon artwork `26B-274` (upright `26B,26C` in `$93`; rotated through `26D-274` by the state-`$1F`
programs). It is exposed as a warrior **sub-context** `object:castle.green_sword_knight.weapon.sword`
(fields `weapon_subcontext`, `weapon_sword_codes`, per-frame `frame_sword_codes`, `sword_representative`)
that **inherits the same warrior mapping** — it is **not** a second palette identity and does **not**
touch Test.json. Representative previews flagged: `$93,$A3,$A6,$99,$9C`; generator coverage includes all
underlying codes. Rastan's player sword/axe/hammer/flame objects are untouched (zero code overlap).

## Hammer

**UNRESOLVED.** No inspected `$033E` selector reaches the player hammer table and the known `$033E` code
set does not intersect the player hammer codes. Not fabricated, not labeled, not generated. Resolve via a
marker capture while a hammer warrior is visible (owning actor record + emitted PC090OJ records → the
distinguishing selector's first writer).

## Axe

**UNRESOLVED**, same basis as Hammer (zero overlap with player axe codes `485-490`). Not fabricated. Same
capture/writer proof required; a future warrior-axe variant stays separate from `object:weapon.axe`.

## Flame Sword

**UNRESOLVED, excluded.** No positive warrior flame-sword path in source; no known `$033E` overlap with
the player flame-sword table; Tighe does not recall a warrior using it. Not exposed as eligible.

## Palette Provenance / Actor Override

Both layers are preserved in Composer evidence (`palette_provenance` on every warrior usage), **not**
flattened to bank `$33`:
1. **Embedded bit-6-clear program defaults** (effective bank = `0x30 + nibble`): normal/state-$1F sword
   piece nibble 3/`$33`, body nibble 7/`$37`; airborne `$37`; short reaction `$3C`; rope shared-sheet
   `$30/$34/$39`.
2. **Actor `+$27` bit-6 override**: every preserved-sweep `$033E` record has creation attribute `$44`
   (960 obs) or `$41` (326 obs) with bit 6 set, so `0x3C9E8/0x3C902` overrides all piece low bytes to one
   line → effective line 4/`$34` or 1/`$31` under the `$30` colbank.

The **registry-vs-sweep conflict** is surfaced (`palette_provenance.registry_conflict`), not silently
redefined: the decision records R1 line 3 / pool `$0C` / bank `$33`; the sweep shows line 4/`$34` or
1/`$31`; PROMT-ID-0069 already calls the field-CRAM relationship unresolved. Tighe's authored mapping was
**not** changed.

## Floor Spikes

**UNRESOLVED.** Not equated with the `$0DAB` torch or generic state `$1E/$20`. Prospective name
`object:hazard.r1s2.floor_spikes` (disabled). Resolve via the capture: correlate one screenshot position
to its record-16..21 world cell, then capture writes to that cell + the collision word across a full
cycle (distinguishes PC080SN vs PC090OJ and reveals all frames/banks).

## Moving Wooden Gate

**UNRESOLVED.** Not the generic collision-`$7E` stage-transition door (that has no proven graphics).
Prospective `object:hazard.r1s2.moving_wood_gate`. Same world-cell/write capture; if it proves PC090OJ,
capture the owning actor record + emitted pieces. No destination mapping from screenshot colors.

## Moving Spiked Traps

**UNRESOLVED, kept separate** from floor spikes. Prospective
`object:hazard.r1s2.moving_spiked_trap`. One owning-cell/actor capture through a full motion cycle;
report writer, all programs/tiles, banks, collision coupling, and whether geometries share one state
table. No merging on appearance.

## Falling Water

**UNRESOLVED for R1-S2.** The R1-S1 waterfall mechanism (`0x59AD4`, type-9 counter `A5+0x12EA`, banks
`$1A-$1D`) is **not** assigned here. Prospective `object:hazard.r1s2.falling_water`. Capture the relevant
PC080SN cell + palette writes for one full cycle and follow the caller/table to decide tile animation vs
palette cycling vs sprites.

## Pit Flames

**UNRESOLVED.** Static scenery (`scene:r1s2.pit_lava_static`) and animated flame
(`object:hazard.r1s2.pit_flame_animation`) kept separate. If only CRAM changes, expose one graphics
object + a palette-animation state, not fake frames; otherwise expose representatives covering the full
tile/sprite domain. Resolve via one full-cycle PC080SN/PC090OJ/CRAM capture.

## Palette Composer Changes

`tools/graphics_editor/server.py::green_knight_usages`:
- domain extended 17 → 29 programs; the incompleteness check still fails if any block is dropped;
- `anim_state` is now the 6 honest machine tags (`normal`, `short_reaction`, `airborne`, `low_action_a`,
  `low_action_b`, `rope`); `frame_category` is the honest UI pose-group header; `pose_label` added;
- `palette_provenance` added per usage (embedded defaults + actor override + registry conflict);
- sword sub-context fields added (`weapon_subcontext`, `weapon_sword_codes`, `frame_sword_codes`,
  `sword_representative`);
- object identity, display name, scene tagging, and the single authored mapping per round unchanged; no
  inferred R2-R6 mapping.

## Generator Changes

`tools/graphics_editor/gen_reindexed_pc090oj.py::GREEN_KNIGHT_ANIMS` extended to the 29 programs (codes
derived through the compositor VM, so the complete sword artwork `26B-274` is covered). No parallel
generator, no runtime recoloring, no PC090OJ emulation layer, no global source recolor. The generator was
run to a **scratch** output only against the live Test.json; the committed
`apps/rastan-direct/out/pc090oj_sprite_variants.inc` and region bins were left for Cody's build.

## Bestiary Changes

`tools/graphics_optimizer/build_bestiary.py` sub-round-2 R1 card now states the corrected 29/109 warrior
domain, the honest pose labels, the `$74` exclusion, the two-layer provenance, and the UNRESOLVED R1-S2
hazard / hammer / axe / flame-sword list pointing at the capture harness. Regenerated
`docs/design/rastan_actor_bestiary.html` (consistency_check PASS). The obsolete 17-program statement is no
longer the canonical claim; historical 0078/0080 reports are preserved.

## Verification

- `tools/graphics_editor/verify_green_knight.py`: **31/31 PASS** — complete 29-program domain; the old
  17-program set explicitly fails as complete (13b); state-$1F A/B present (15c/15d); `$74` excluded;
  honest labels / no proven "crouch" (16/16b); 109 codes re-derived independently (19b); sword `26B-274`
  covered (19c); both provenance layers surfaced (19d); sword sub-context (19e); exact Test.json index
  transform (19); Test.json unchanged (21). Expected sets are re-stated in the verifier, not imported.
- `tools/graphics_editor/verify_reindexed_pc090oj.py` (independent re-derivation, scratch build from live
  Test.json): **VERIFY PASS** — knight expected 109 covered 109, sword covered=True, exact=True; Rastan
  retention 344/0; enemies unchanged; divergent 75 all-distinct; stray=0; mismatched=0.
- `tools/graphics_editor/verify_r1s2_castle_browser.py`: **15/15 PASS** (unchanged behavior).
- Test.json SHA-256 before == after: `24914ababc7fab52aac8258dd1f9f7b3d5df230b81421c03d9ce68d1526135ae`.

## Original Arcade Capture Harness

One reusable, read-only ORIGINAL ARCADE harness (no ROM/RAM/input writes), extending the established MAME
layout and reusing the proven actor-record/PC090OJ decode from `arcade_actor_renderer_verify.lua`, the
PC080SN name-RAM map and marker/tap pattern from `r1s2_resident_oracle_arcade.lua`, and the arcade
coin=5/start=1 workflow:
- `tools/mame/scripts/arcade_marker_capture.lua`
- `tools/mame/run_arcade_marker_capture_wsl.sh`

At each user marker (default key **M**) it records, with a rolling pre-marker history window so the
transition is not lost:
- **Active actors** (`actors.tsv`): every live slot in all five blocks — base `+1e`, anim `+01`, state
  `+03` and `+05`, facing `+02`, mode/family `+3e`, `+21`, attr `+27`, mirror `+20`, compositor `+38`,
  x `+16`, y `+1a`, program pointer, and the full raw 64-byte record (so any field resolves offline).
- **PC090OJ output** (`pc090oj.tsv`): each owning actor's SAT records — pattern code (`w2`), palette line
  (`w0 & 0x0f`), hflip/vflip, X/Y, raw 4 words, owner correlation.
- **PC080SN writes** (`pc080sn_writes.tsv`): both planes (A `≥0xC08000`, B `<`), writer PC, physical
  row/col, cell attr/tile, scroll + selector for world-cell reconstruction.
- **CRAM/palette writes** (`cram_writes.tsv`): writer PC, bank, index, value.
- **Collision/state** (`collision.tsv`): global state block + an optional `CAPTURE_COLLISION_ADDR` word.

**Smoke test (headless, this pass):** ran against ORIGINAL ARCADE `rastan` (`MARKER_QT_PLATFORM=offscreen`,
`-seconds_to_run`), auto-marking into the attract **demo** with **zero input writes**. Proved: startup OK;
all log files created; markers recognized (5 fired in the demo); rolling history retained; **36 actor
records** emitted (real R1 bases `0x004B`, `0x0179`, `0x0DAB`, …); **362 PC090OJ records** emitted
(owner-correlated, codes ≤ `0xFFF`, line/flip decoded); PC080SN writes on both planes (9,581 in a short
run); CRAM writes; collision/global-state rows; output parseable. This proves the plumbing only — it does
**not** assert any hazard identity; Tighe marks the real objects during gameplay.

## Tighe Capture Instructions

Run ONE command, then play ORIGINAL ARCADE Rastan (coin **5**, start **1**) to R1-S2 and press **M** once
at each of: (1) the low/duck warrior pose, (2) a warrior carrying a hammer, (3) a warrior carrying an axe,
(4–8) one full cycle each of floor spikes, the moving wooden gate, a moving spiked trap, the falling
water, and the pit flames:

```
tools/mame/run_arcade_marker_capture_wsl.sh
```

Files land in `states/traces/arcade_marker_capture_<timestamp>/`. Tell me the marker indices for each
object and I will bind owners/codes/banks to the correct semantic objects and follow each writer/table in
Ghidra. (Optional: `CAPTURE_COLLISION_ADDR=0x…` to sample a specific collision word; `CAPTURE_ROLL_FRAMES`
to widen the pre-marker window.)

## Cody Integration Handoff

- Regenerate `apps/rastan-direct/out/pc090oj_sprite_variants.inc` and region bins from the updated
  `gen_reindexed_pc090oj.py` at the next ROM build; the generator and both verifiers now expect the
  29-program / 109-code knight domain. I did not touch the committed `.inc`.
- The warrior owns state-$1F `$97-$9C` and `$A1-$A6` plus the sword artwork `26B-274`; `$74` is the torch —
  do not map it to the warrior; never recolor Rastan's player weapons for the warrior sword.
- Palette is two-layer (embedded defaults + `+$27` override); do not assume a flat `$33`. The
  registry-vs-sweep bank conflict is Tighe's decision, recorded in the Composer evidence, unchanged in
  `specs/palette_decisions.json`.
- No transition/audio/Plane-A/`tilemap_hooks.s` touched; no ROM built; build counter unchanged.

## Files / Local Commits / Logs

- `tools/graphics_editor/server.py`, `gen_reindexed_pc090oj.py`, `verify_reindexed_pc090oj.py`,
  `verify_green_knight.py`;
- `tools/graphics_optimizer/build_bestiary.py` + regenerated `docs/design/rastan_actor_bestiary.html`;
- `tools/mame/scripts/arcade_marker_capture.lua`, `tools/mame/run_arcade_marker_capture_wsl.sh`;
- this report; `AGENTS_LOG.md`.
- No Test.json / palette_decisions.json / Cody production files; no ROM / build-counter change.

### Explicit report
- old 0078 program/code count: **17 programs / 77 codes**
- corrected program/code count: **29 programs / 109 codes**
- exact missing programs added: `$97,$98,$99,$9A,$9B,$9C` and `$A1,$A2,$A3,$A4,$A5,$A6` (codes `26D-274`, `389-3A0`)
- sword code domain: `26B-274` (covered; representatives `$93,$A3,$A6,$99,$9C`)
- hammer status: **UNRESOLVED** (not fabricated; capture required)
- axe status: **UNRESOLVED** (not fabricated; capture required)
- Flame Sword status: **UNRESOLVED, excluded** (no positive source path)
- floor-spike status: **UNRESOLVED** (capture required)
- moving-gate status: **UNRESOLVED** (capture required; not the `$7E` door)
- moving-spike status: **UNRESOLVED** (kept separate; capture required)
- falling-water status: **UNRESOLVED** (not the R1-S1 waterfall; capture required)
- pit-flame status: **UNRESOLVED** (static vs animated kept separate; capture required)
- Test.json SHA before == after: `24914ababc7fab52aac8258dd1f9f7b3d5df230b81421c03d9ce68d1526135ae`
- ROM/build counter changed: **NO**
- Cody production files touched: **NO**
- GitHub push: **NO**

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0084`
