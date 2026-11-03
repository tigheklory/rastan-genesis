# Andy — R1/P1 Editor Policy → Canonical Palette Bridge (tooling)

**Type:** architecture/tooling. No production ROM/runtime change. Build counter 313. No build consumed.

## What exists now
`tools/graphics_editor/export_palette_policy.py` — the missing bridge from the Palette Composer's authored
policy to the canonical production registry `specs/palette_decisions.json`.

- **Editor profile role:** `analysis/graphics_optimizer/editor_policy/Test.json` is an AUTHORING WORKSPACE,
  not a production registry. Canonical production authority remains `specs/palette_decisions.json` (the
  only palette-decision registry per CLAUDE.md).
- **Production promotion support: ROUND 1 / PHASE 1 ONLY** (`context:gameplay.r01.p01`). Any other context
  is rejected (`ERROR: production promotion currently supports only context:gameplay.r01.p01`) rather than
  fabricating unsupported policy. This is NOT a whole-game exporter.
- **Authorial vs storage scope:** the editor stores sprite mappings globally, but they are authored while
  working exclusively on R1/P1; the tool treats them as R1/P1 intent only and never as game-wide policy.
- **Modes:** `--check` freezes a deterministic snapshot (`build/rastan-direct/build0314/Test.snapshot.json`
  + SHA-256), resolves the effective R1/P1 line ownership, and runs the coexistence gate against the
  canonical registry and the Build-0313 production route model — changing nothing. `--apply` is refused
  unless `--check` PASSes (governed merge preserving unrelated decisions + decision IDs; not reached yet).

## Coexistence gate (the blocker it surfaced)
The gate compares the editor's authored CRAM-line ownership with (a) the Build-0313 production
`palette_route_table` (`apps/rastan-direct/src/palette_hooks.s`) and (b) the canonical registry's existing
proven/decided sprite-line decisions. `--check` currently returns **FAIL** with 6 conflicts:

| # | Conflict |
|---|---|
| 1 | Editor Layer-A on **Line 3**; production routes Layer-A FG to **Line 1** (bank-3 carrier). |
| 2 | Editor Layer-A on **Line 3** collides with the production **sprite** line 3 (bank 51). |
| 3–5 | Editor Rastan (bank 0x33) on **Line 0**; canonical `PAL-PC090OJ-GAMEPLAY-RASTAN-SWORD-001` (**proven**) assigns **Line 3** (×3 Rastan frames). |
| 6 | Editor Lizardman (bank 0x36) on **Line 1**; canonical `PAL-PC090OJ-STAGE1-LIZARDMAN-001` (**decided**) assigns **Line 0**. |

Production/canonical line ownership: **Line 0 = HUD, Line 1 = Layer-A FG, Line 2 = Layer-B (protected),
Line 3 = sprites (Rastan bank 51)**. The editor authored the inverse (Layer-A on 3, sprites on 0/1), which
would require overriding a `proven` Rastan decision and a `decided` Lizardman decision and colliding Layer-A
with sprites — so promotion/build cannot proceed without a line-model reconciliation decision from Tighe.

## Resolution paths (Tighe's decision)
- **A (recommended, editor-side):** re-author the Test line model to match production — HUD=Line 0,
  Layer-A=Line 1, Layer-B=Line 2, sprites=Line 3 (a single shared 15-entry sprite line; enemies + Rastan
  share it as bank 51 does). Needs a sprite shared-line consolidation (existing ΔE / hue-safe solvers).
  No production runtime change; then `--check` passes and `--apply`/compile can run.
- **B (runtime-side):** re-architect the production route table (Layer-A→3, sprites→0/1, HUD relocated) —
  a change to accepted Build-0313 palette routing (KF-854 carrier logic); larger and riskier.

## Extension path
Future intentionally-authored phases/rounds use this same governed bridge (new `--context`, its own arcade
corpus/evidence, authored policy, then promotion). The bridge must not auto-inherit R1/P1 policy into any
other context.
