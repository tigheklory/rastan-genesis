# PROMPT-ID-0006 — Fix and Complete Rastan Palette Composer

**Author:** Andy · **Date:** 2026-10-25 · **Branch:** `rastan-direct-proposal`
**Scope:** Composer (`tools/graphics_editor/`) + per-subround palette/sprite data contracts.
**No ROM build consumed. No Composer-owned native code changed. No Audio Composer touched.**

This is the audit trail for PROMPT-ID-0006. It records what was implemented, what was proven, and —
honestly — what remains unresolved and why, with the exact evidence needed to close each gap.

---

## Requirement status

| Req | Summary | Status | Evidence / commit |
|---|---|---|---|
| 1 | Fix incorrect arcade palettes (R2+) | **Derived + disclosed** (not fully resolved; honest) | `analysis/graphics_optimizer/per_round_palette_evidence.json` |
| 2 | Independent Genesis palettes per subround | **Done** | commit e60306e8; `verify_independent_scopes.py` 9/9 PASS |
| 3 | Regenerate castle maps via Cody's selector-aware decoder | **Done** | commit f6db8d2c |
| 4 | Per-subround sprite/enemy graphics | **Honest coverage, no substitution** | `build/palette_export/scene_sprite_coverage.json` |
| 5 | Per-scene CRAM export | **Done** | commit 0bba1b3e |
| 6/G | Preserve approved decisions | **Preserved** (additive schema-v2 migration only) | `specs/palette_decisions.json`, `specs/_backup/` |

### Acceptance criteria
- **A** (R1-S2 loads castle maps/colors/sprites): map/colors via scene-aware corpus + Cody's decoder; sprites honestly labeled SCHEDULE_ONLY. **Met for maps/colors; sprites disclosed.**
- **B** (R1-S2 Line 3 independent of R1-S1): **Met** — `verify_independent_scopes.py` checks 6/7.
- **C** (switch/save/reload/export scene-specific): **Met** — checks 5–8 + per-scene CRAM.
- **D** (uses Cody's decoder): **Met** — `layera_map` calls `reconstruct_segment(..., selector=decode_record_selector(...))`.
- **E** (R2-S1 palette matches arcade via real R2 evidence): **Partially** — a genuine R2 capture could not be produced; the arcade loader was decoded statically and the fixed-base source **proven** against live R1. Residual R2 reload question is disclosed, colors are **not fabricated.**
- **F** (missing assets labeled, not substituted): **Met** — scene coverage banner + `substitution_warning`.
- **G** (approvals preserved): **Met.**

---

## Req 1 — arcade palette (Criterion E): what was proven vs. what remains

### Proven (static, from `build/regions/maincpu.bin`, the authoritative arcade program)
1. **Conversion.** Arcade ROM `0RGB` nibble → live xBGR-555 is `word = (B*2)<<10 | (G*2)<<5 | (R*2)`.
   Verified: `0x4EAF6 + 3*32` reproduces live R1 palette-RAM **bank 3 exactly**
   (`0869`→R8 G6 B9→`4990`, matching `states/traces/palram_R1`).
2. **R1 Plane-A sourcing.** The visible R1 Plane-A background bank 3 comes from the **fixed** startup
   table `0x4EAF6`, **not** from the per-round pool `0x4FD02` (whose decode for the same bank differs).
   So the Composer's existing fixed-base source is correct for R1.
3. **A per-round table exists.** `0x3BA88 + (round-1)*32` is a genuine 32-entry per-round bank-index
   table (loaded by the routine at `0x3BA20` via `0x4FD02`). Rounds differ from R1 by
   `{R2:7, R3:9, R4:15, R5:20, R6:20, R7:32}` indices — the per-round mechanism is real.

### Not resolved (disclosed, not fabricated)
Whether any `0x200000`-region Plane-A bank is **reloaded** per-round (overwriting the fixed base for
R2+) is **UNCONFIRMED**. R1 bank 3 provably uses the fixed base, and the per-round pool fills a
separate buffer (`a5+0x1600`); but an earlier round-forcing test perturbed bank `0x003` under a
fragile forced state. A **genuine Round-2 live palette-RAM capture** is required to settle it.

**Three capture attempts failed** (consistent with the PROMPT-ID-0001 finding that R1 vs R2 palette
RAM was byte-identical — the round counter never advanced):
- forcing round counter `0x10C118:=2` from boot corrupts the appearance/state machine;
- the `_Sx-y` stage-select ROMs set stage index `0x10D242` but leave the round counter at 1 (RG-019 quirk);
- poking the subround-complete marker `0x10D243` did not advance the round counter.

### Decision (no fabrication)
The generator **keeps the proven fixed-base colors**. The R2/arcade mismatch Tighe reported is
explained by the editor previously applying **R1's scope and R1's record decode to R2** — both fixed
under Req 2 (independent scopes) and Req 3 (selector-aware per-scene records), so each scene now reads
its **own** bank set. For R2+ scenes the editor shows an **honest banner** stating colors are derived
from the proven round-independent base and that a per-round reload is unconfirmed (not verified, not
fabricated). To close E definitively: capture a genuine R2 playthrough palette-RAM dump and re-run
`derive_per_round_palette.py`.

---

## Req 2 — independent per-subround Genesis palette lines
Each subround PLANEA `scene_key` is a real editing context parented to a neutral `context:gameplay`
node (R1-S1 authors on the existing `context:gameplay.r01.p01`). `effEntry` resolves base ⊕
per-context override; Lines 0/1/3 author per scene, Line 2 reserved. `verify_independent_scopes.py`
proves: contexts resolvable; a castle Line-3 edit persists over save/reload; R1-S1 and R2-S1 are
**unaffected**; Line-2 override rejected. **9/9 PASS.** UI DOM event-path / Undo-Redo is a manual
browser step (below).

## Req 3 — selector-aware castle maps
`layera_map` now computes `selector = compile_pc080sn_genesis.decode_record_selector(mc, seg)` and
decodes with `audit_round1_phase1_plane_a.reconstruct_segment(mc, gfx, seg, "visible", selector)` —
**Cody's Build 0502 contract**, no JS rotation, no competing transform. Output carries `selector`.

## Req 4 — per-subround sprites/enemies (honest coverage)
`scene_sprite_coverage.py` classifies each scene from existing analysis (no new RE):
- **PROVEN_COMPLETE** (4 R1-S1 scroll phases): the captured R1/Phase-1 corpus, authorable now.
- **SCHEDULE_ONLY** (6 S2 castle scenes): spawner bases from `subround2_schedule_rosters.json`
  identify *which* actors appear, but their per-scene cell vocabulary is not captured → not authorable.
- **PENDING** (11 scenes): per-scene markers not enumerated — blocked on the `A5+0x10D000`
  collision-record populator (`h11_phase2_actor_rosters.tsv`).

The Objects tab shows a disclosure banner + `substitution_warning` on every non-PROVEN scene: the
R1/Phase-1 graphics are the only authored vocabulary and are **not a substitute** for that scene's
enemies. No silent substitution, no fabricated roster.

## Req 5 — per-scene CRAM export
`export_subround_palette_manifest.py --profile <id>` emits
`build/palette_export/cram/<scene_key>.bin` (Lines 0/1/3 × 16 big-endian words) **only** when the
scene has its own authored overrides — never from inherited base, so one scene's palette is never
substituted for another. Line 2 excluded. Deterministic. Missing → arcade fallback (no blob).

---

## New durable tooling (reusable, project-owned — not scaffolding)
- `tools/graphics_editor/derive_per_round_palette.py` → `analysis/graphics_optimizer/per_round_palette_evidence.json`
- `tools/graphics_editor/scene_sprite_coverage.py` → `build/palette_export/scene_sprite_coverage.json`
- `tools/graphics_editor/verify_independent_scopes.py` (Req 2 regression gate)
- Server endpoints: `/api/per_round_evidence`, `/api/scene_sprite_coverage`, `/api/subrounds` (scene-aware `layera*`).

## Diagnostic scaffolding inventory + removal plan
MAME diagnostic scripts under `tools/mame/scripts/` (analysis-only, **no production ROM scaffolding**):
- `arcade_r2_palette_force.lua` — forces round counter; proved forcing corrupts state. **Keep** as a
  durable diagnostic (documents the failed path); delete only on Tighe's say-so.
- `arcade_reach_r2.lua` — invincibility + subround-complete poke to reach R2; proved the poke does not
  advance rounds. **Keep** as durable diagnostic.
- `states/traces/reach_r2/` — run output. Transient; may be pruned.
No production ROM was modified; no `rts`/NOP/stub introduced; no registry duplicated.

## Manual verification still required (browser)
Open the Composer, select R1-S2 then R2-S1: confirm (a) the map view loads the scene's own records,
(b) a Line-3 edit on R1-S2 does not change R1-S1, (c) Undo/Redo on a scene edit, (d) the R2+ palette
banner and the sprite-coverage banner render. Data-layer equivalents all pass headless.
