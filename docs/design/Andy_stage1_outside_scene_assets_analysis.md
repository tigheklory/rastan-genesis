# Andy — Stage 1 Outside Scene Assets: Gameplay-Entry Divergence Analysis (Outcome G, no build)

**Agent:** Andy (temporary runtime-evidence role). **Type:** evidence-only analysis. **No source, no ROM, no build.**
**Baseline:** `rastan-direct-proposal` @ `454add2` (Build 0152 accepted). Build 0152 ROM
`3d805331815588576a3fdeef732a7b094f3c15997b66c76830827adfc2f35214`. Working tree clean. Counter 152.
**Evidence dir:** `states/traces/build_0153_stage1_outside_scene_assets/`.

## Outcome
**Outcome G — bounded stop.** The first divergence is proven (the gameplay scene tiles **and** palette are never
loaded, so Stage 1 outside renders blank), but the **root transition owner is not yet proven** and the fix is **not
bounded**: at gameplay the entire per-frame gameplay PC080SN/palette translation path does not execute, which is a
gameplay-rendering gap rather than a small correction to the existing scene loader. No numbered build was produced.

## Reproduction (Genesis Build 0152)
Boot → coin (P1 A, frames 120–132) → 1P start (P1 Start, 175–187) → let run. State words `0xFF0000/0002/0004`:
`0/1/0 → 1/0/0 → 1/1/0 → 2/0/0 → 2/2/6 → 2/2/7 → 2/2/4 → 2/2/5 → 2/3/0` (then **stuck at 2/3/0**).
At `2/2/4` the staged palette collapses from ~41 nonzero words to **1** (the "nearly all CRAM black, one pink entry"
symptom). At `2/3/0` the screen is blank except stale frontend PC090OJ sprites (`2731`, `2UP`) —
`snaps/reach2000.png`.

## Arcade reference (original Rastan)
Same coin+start route: `2/2/4 → 2/3/0` at f≈307, and **state `2/3/0` IS Stage 1 outside gameplay** — Rastan,
mountains/sky background, "ROUND 1", health bar (`snaps/arc_f400.png`). The arcade later advances `2/3/0 → 2/4/0`
(attract-demo boundary) at f≈895. So **both** machines reach `2/3/0 = gameplay`; the arcade renders Stage 1 outside,
the Genesis renders blank. The divergence is asset/rendering, not the state value.

## Phase 1 — scene loader state (static + runtime)
- `load_scene_tiles` (`0x00072CE8`, `scene_load.s`) selects manifests by `D0 & 0xFF`: 0=title, 1=gameplay, 2=endround,
  and DMAs pattern pairs into VRAM (display-off). Scene A0 ranges: title `0x0005A7DA..0x0005B0B2`, **gameplay
  `0x00056A22..0x000570C2`**, endround `0x0005822A..0x00059614`.
- Scene selection is **A0-range-driven** inside the BG scroll-fill hook (`genesistan_hook_pc080sn_bg_scroll_fill`,
  detection at runtime `0x000702A6`): if the arcade BG descriptor source pointer `d0` leaves the current
  `[scene_a0_lo, scene_a0_hi]`, it scans `genesistan_scene_a0_ranges` and calls `load_scene_tiles(scene_index)`.
- **Runtime:** at gameplay (`2/3/0`, f=800) `genesistan_current_scene_id (0xFF7474) = 0` and
  `genesistan_scene_a0_lo (0xFF7476) = 0x0005A7DA` (title range). The loader is **never called with scene ID 1**.

## Phase 2 — the gameplay hooks do not execute (verified)
Narrow taps (verified against the frontend so this is not tap flakiness):
| signal | frontend (f<380) | gameplay (f≥380) |
|---|---|---|
| reads of `scene_a0_lo 0xFF7476` (BG scene-detection runs) | 2 | **0** |
| writes to `staged_palette_words 0xFF609E..` (palette producer stages) | 128 | **0** |

So during gameplay **neither** the PC080SN BG scroll-fill hook **nor** the palette producer hook runs. The gameplay
tiles (scene 1) and the Stage 1 outside palette are therefore never produced; `scene_id` stays 0 and CRAM stays blank.

## Phase 4 — arcade Stage 1 outside asset owners (partial)
- **Palette:** the arcade Stage-1-outside palette is written by **arcade PC `0x059B0E`** (34 CRAM-RAM writes into
  `0x200000` during the `2/2/4→2/3/0` entry). `0x059B0E` lies inside arcade function `0x059AD4`, which **is already a
  patched site** (`opcode_replace → genesistan_palette_hook_59ad4`, runtime `0x000717C6`). Captured arcade gameplay
  palette RAM (`0x200000`, converted target): line0 sky/greys `7bde 001e 29d0 4298 …`, line2/3 browns/reds. So the
  Genesis palette pipeline *would* handle the gameplay palette **if the arcade caller of `0x059AD4` executed** — but it
  does not run during Genesis gameplay (0 staged writes above).
- **Tiles:** the gameplay tile manifest exists (`build/pc080sn_scene_preload_gameplay.bin`, 3318 B ≈ 829 source/dest
  pairs) and is keyed to the gameplay A0 range `0x56A22..0x570C2`; it is simply never triggered.

## First exact divergence
At Genesis gameplay entry the **gameplay-init scene-setup code does not execute**: the arcade routines that (a) call
the palette producer `0x059AD4` for the Stage 1 outside palette and (b) drive the PC080SN BG descriptor fill (whose
Genesis hook triggers `load_scene_tiles(1)`) are not reached on the Genesis during gameplay. The visible blank
background and collapsed CRAM are downstream of that non-execution, not of a wrong scene ID or an incomplete manifest.

## Why this is Outcome G (not a bounded A–F fix)
- It is **not** merely "loader called with the wrong scene ID" (Outcome A/B): the loader is not called at all, because
  the whole gameplay BG/palette path is absent, not misparameterised.
- It is **not** a manifest (C) or palette-routing (D) fix in isolation: forcing `load_scene_tiles(1)` would make tile
  patterns resident but still produce no visible scene, because the gameplay tilemap cells, palette staging, and
  scroll all come from the same un-executed path. The task forbids a second loader/renderer/commit path, so a partial
  trigger would violate the architecture without achieving Stage 1 outside.
- The exact arcade caller chain that should drive the gameplay PC080SN/palette on the Genesis — and the reason it does
  not run (an earlier gameplay-init divergence vs. a gameplay-specific PC080SN path the current hooks do not intercept)
  — is **not yet proven**, so no faithful bounded correction can be committed.

## Smallest exact next investigation (one bounded capture)
Trace the Genesis gameplay-init sequence immediately after the state becomes `2/3/0` and compare to the arcade:
1. In **arcade** MAME, breakpoint the writer `0x059B0E` (gameplay palette) and record its **caller chain** (stacked
   return addresses) and the surrounding routine that invokes `0x059AD4` during the `2/2/4→2/3/0` entry; also record
   the arcade routine that fills the gameplay PC080SN BG descriptor (source pointer in `0x56A22..0x570C2`).
2. In **Genesis** Build 0152, breakpoint those same mapped runtime PCs (via `address_map.json`) across the same
   transition and record whether each is reached; if not, capture the **last arcade routine executed** before the
   `2/3/0` idle loop — i.e., the exact PC where the Genesis gameplay-init path stops matching the arcade.
This single comparison identifies the transition owner (missing translation or an earlier halt) and determines whether
the fix is a bounded translation of one gameplay-init routine or a larger gameplay PC080SN rendering task.

## Relationship to the remaining raw writer `0x03D04C` (C08C66)
Build 0152 routed `0x03A72A → 0xC08C62`. Its sibling `0x03D04C → 0xC08C66` (a raw FG single-digit write of the same
family) is still present in Build 0152. It was **not** proven to block this scene load (the state advances past it to
`2/3/0`), so per scope it was not touched here; the next-investigation capture above will confirm whether it or any
other unrouted gameplay-init write participates.

## Scope / deferrals
No build produced. Not investigated or changed: stale `2731`/`2UP` sprites, post-item PC090OJ lifecycle, item-scroll
graphics, missing item sprites, the `0x03D04C` raw writer, gameplay sprite/collision/controls, audio, credit
positioning, copyright region. Build 0152 frontend (title/coined title/story/BEST 5/clipping/palette) was not modified
and remains intact. **Real-hardware / BlastEm / Exodus validation NOT CLAIMED.**

## Open issue impact
- **OPEN-017 (ROM does not run on real hardware / gameplay):** advanced — Build 0152 clears the `0xC08C62` gameplay-
  entry raw-write fault, and the next boundary is now root-caused to *non-execution of the gameplay PC080SN/palette
  scene-setup path* (tiles scene 1 never loaded, Stage 1 outside palette never produced), with a bounded next capture
  defined. Not closed; no duplicate opened.
