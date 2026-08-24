# Andy — Build 0307: Actual VRAM Ownership + 2D Y Fix (facts + implementation plan)

**Type:** bounded-fact closure + implementation + numbered build. Baseline 0306 (`7d3ab8da…c2c08`).
Continues the accepted review `Andy_build_0307_full_vram_2d_epoch_review.md`.

## Build 0307 PRODUCED (update)
`dist/rastan-direct/rastan_direct_video_test_build_0307.bin`, SHA-256
`c46ed6b8ba6bbe2ee055e70147f4b8476250f754eba71f9143afdde385b96ac9`, size 2,887,352, counter 306→307,
**GATE_PASS**. Change = **selective Plane-B Y-envelope widening** (compiler-only): rope records **{2,3}**
join the full-64-row single-variant path (`BOUNDARY_FULL_Y_RECORDS = {2,3,17,21}`), so the rope stays
resident across the whole climb (kills the within-record Y-envelope escape). No runtime change (the
installer already forces variant 0 when `variant_count==1`). Sprite reservation unchanged; Plane-A
drops 0; Plane-B drop packages 22→19 (rec2 dropB=130, rec3 dropB=227 under the unchanged 960 pool) —
**reported, not fixed** (zero-drop reclamation is Build 0308+). Coverage invariant bumped
`0x2E1EB8→0x2C0EB8` for the resized boundary binary. The two facts below stand as written; the sprite
peak (FACT 1) remains the Build-0308 driven-harness task.

## Honest status
- **FACT 2 (rope visual owner + failure) — CLOSED** from prior runtime evidence + static decode.
- **FACT 1 (Stage-1 sprite pattern peak) — NOT closed**: requires a *driven-input* gameplay MAME run;
  attract mode never enters gameplay, and no existing Genesis script drives to the rope.
- **Build 0307 not produced**: the zero-drop sprite-bounded allocation is unsafe without FACT 1, and
  the mandatory 7-checkpoint collision gate also needs a driven gameplay session. Emitting an
  unvalidated numbered production ROM would violate the task's own REQUIRED BUILD CONDITIONS and the
  project's no-wasted-builds / collision-correctness rules.

## FACT 2 — rope visual owner = **Plane B**; failure = **Y-envelope escape** (CLOSED)
Evidence (prior read-only trace `states/traces/build0228_runtime_scene4_rope_transition_20260722_090545`
+ static):
- **Visual:** the rope is produced by the Plane-B BG block stream. `STRIP_BLIT_ENTRY … src=0000F31C
  attr=0002 dest=00C00080` and `COLL_READ_ROPE … src=0000D31C attr=0002 worldY=0193`. `0xD31C`/`0xF31C`
  are Plane-B source blocks inside the `0x3951C` descriptor range (attr `0x0002` = outdoor Plane-B).
  → **the rope is Plane-B terrain**, not a sprite and not Plane A.
- **Collision:** a *separate* channel — `COLL_READ_ROPE pc=053D70 addr=00FF2D8C` (collision map in
  WRAM `0xFF2xxx`), independent of the Plane-B visual. (Matches the design-history "Plane A/collision,
  rope" grouping: the *collision* is the Plane-A/collision side; the *visual* is Plane B.)
- **Failure mechanism:** the rope is a tall Plane-B element climbed vertically (`worldY≈0x193` and
  rising). Ordinary records freeze one 40-row Plane-B Y-variant, selected only at the record/X boundary
  (`fg_boundary_install`, no within-record Y re-selection). Climbing moves the visible Plane-B rows out
  of the frozen band → the rope's rows are no longer resident → **rope disappears**. This is the
  proven Q7 gap, now tied to a Plane-B element. It is **not** a Plane-B *drop* (droppedA/B don't touch
  the rope band) and **not** fixed by a source-package handoff union.

## FACT 1 — sprite ownership (BOUNDED, peak not measured)
- Static: `SPRITE_TILE_BASE=1024`; `sprite_tile_resident_code: .space (128*2)` → 128 codes × 4 = **512
  patterns = cache capacity, not proven simultaneous need**. Sprite families fam0..4 at
  `0x3D09E/0x4771C/0x3F0CE/0x40004/0x4002C`.
- Probe (Build 0306, `build0307_vram_rope_trace.lua`, 45s, attract only — **MAME works, 393% speed**):
  attract/frontend uses ~14–19 sprite cells in the 1024–1535 band; **planes empty (0 cells)**; the game
  never left scene 00/01 with segment 0 — **no gameplay sprite peak captured**. Exodus "stripes" at
  attract correspond to the large unused low-plane band (64–1023) and most of 1024–1535 — genuinely
  unused *at that state*, but not evidence for gameplay.
- **Remaining measurement:** run `build0307_vram_rope_trace.lua` with **driven inputs** through Stage-1
  gameplay (Start → hold right → jump the pit → reach/climb the rope, ~segment 2–3), then read
  `used_sprite_cells`/`sat_patterns` peak and the per-slot `slot_ownership.csv`. That single bounded
  observation closes the sprite peak and confirms the rope slot live/absent transition.

## Why no ROM yet (build-integrity)
The zero-drop mandate requires expanding plane allocation into the 1024–1535 band **bounded by the
proven live sprite set**. Without FACT 1 that bound is unknown, so any zero-drop package could silently
overwrite a live sprite pattern (corrupting sprites to gain terrain — explicitly forbidden). And the
task's REQUIRED BUILD CONDITIONS + the 7-checkpoint collision gate (frame 310/379/800/1200/1800) can
only be honestly asserted by a driven gameplay validation run. Neither is available from attract mode.
Producing an unvalidated numbered ROM here is the Build-0267-class mistake the project bans.

## Implementation plan (ready once FACT 1 is measured)
**A. Compiler (offline, `compile_pc080sn_genesis.py`) — sprite-bounded non-contiguous zero-drop:**
1. Input a **static sprite-live map per semantic interval** = arcade family patterns that can legally
   coexist in that Stage-1 section (validated, not exceeded, by the bounded observation). Keep sprites
   at their existing live slot numbers (no SAT/index disturbance).
2. `AVAILABLE = slots 64..1535 − hard-reserved(0..63) − sprite-live(interval)`; allocate plane
   identities into the **actual free set (holes allowed in 1024..1535 and below 1024)**.
3. **Remove the slot-0 drop path**: if a package's `|A ∪ B|` after dedup exceeds `AVAILABLE`, **fail the
   build with exact package/deficit evidence** — never blank required terrain. Assert
   `droppedA==0 && droppedB==0`, `max_slot < 1536`, `no plane/sprite-live conflict`.
4. Name words already use `0x07FF`/`0xF800`; raise the allocator cap from 1023. Keep canonical 32-byte
   identity + stable-slot retention.

**B. Runtime (2D Y fix, Plane-B) — selective Y widening, no per-frame:**
- Preferred: **selective static Y widening** per record that legally permits vertical travel — compile
  the *complete* legal Y envelope (smallest that is semantically complete: 40/48/56/64) for
  climb-records only, keeping horizontal records at 40. The rope record gets the full climb envelope
  (like vertical records 17/21 already do).
- If an **existing arcade Y-progression event** subdivides the climb, allow a package re-select there
  (event-driven, not frame-based Y polling). Keep the 1354-edge X-boundary graph; add the within-record
  Y coverage in the *package envelope*, not new edges.
- Recompute capacity with the wider Plane-B envelope: hardest interval = full Plane-A + wide-Y Plane-B +
  sprite-live − dedup vs 1472; accept **selective** widening if the global 64-row case doesn't fit.

**C. Gate:** build → boot guard → canonical gate → driven gameplay collision run asserting the 7
checkpoints (310 coll `8F62BDC5`, 310 PlaneA `6A561F2A`, 379 coll `2B745D65`, 800 Y `0x0070`, 800 coll
`961C0BC5`, 1200 rec `2`, 1800 rec/mode `3/4`) → number the ROM only on PASS.

## Concrete next step
Build a **driven-input Genesis gameplay harness** (extend `build0307_vram_rope_trace.lua`'s runner with
a Start→right→jump input sequence reaching segment 2–3) — this single harness both closes FACT 1 and
provides the collision-gate replay. Then execute plan A/B/C and number Build 0307.
