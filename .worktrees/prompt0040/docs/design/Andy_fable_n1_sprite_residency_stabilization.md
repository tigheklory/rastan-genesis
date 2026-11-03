# Andy/Fable — N1 Sprite Residency Stabilization (Build 0222 rejected, **Build 0223 = candidate**)

**Date:** 2026-07-20 · **Evidence:** `states/traces/n1_sprite_residency_stabilization_20260720_192435/` · **JSON hashes (recorded):** address_map.json `4acef0c8…`, patch manifest `591ffb34…` (json_hashes.txt). No fixed offsets used.

## User observation recorded
Build 0221 = successful architectural proof: noticeably faster; native pipeline retained. Regression to fix: sprite tiles disappear/reappear. Rolling black bar = N2 scope (plane path unchanged here).

## Exact residency root cause (Build 0221)
Two mechanisms, provable in the 0221 emit path:
1. **Miss ⇒ skip-emission**: any code not resident was simply not emitted that frame — every animation-frame change or conflict = a visibly vanishing component (~1.2/frame at 4-lizard load; measured ~360 drops/300 frames).
2. **Unprotected victim choice**: the 2-way static way-pick (`btst #6`) could assign an upload to a cell that another *currently-emitted* sprite still referenced — the pattern DMA landed before the SAT DMA, so that sprite displayed the wrong artwork for a frame.
The arcade inventory (codes_arc.txt, 60 s attract+frontend+stage1, MAME/original-arcade) shows why capacity-only fixes fail: **388 distinct codes over time** (frontend 38, gameplay 372) — no pinned set fits 128 cells — while **per-frame concurrency is only ~50 cells** (≤80 sprites). The correct design is therefore reference-protected replacement, not pinning-everything.

## Residency architecture implemented (Build 0223)
- **32 sets × 4 ways over the same 128 VRAM cells** (tiles 1024–1535; cell = tag index; identity = sprite code — SAT position never matters).
- **Per-frame reference protection:** a 128-bit `pc090oj_cell_used` bitmap, cleared at pass start; every hit/allocation marks its cell; a victim may only be a cell *unreferenced this frame* ⇒ no displayed sprite can have its patterns stolen — stale/wrong artwork is structurally impossible.
- **Emit-on-miss with optimistic tags:** a missing code allocates a protected victim, enqueues its 128-byte upload (bounded 12-entry queue), tags the cell immediately (same-frame re-hits work), and **emits pointing at that cell** — the upload lands in VBlank *before* the SAT DMA, so misses are invisible. This is the deterministic scene warm-up: a scene's working set converges in ≤ ~5 frames during title/READY with zero visible artifacts, before actors matter.
- **Bounded skip only** when a set's 4 ways are all referenced in one frame or the queue is full (counted; measured: **2 total** in the whole run, both in the first title frame burst; **+0 for the rest of the session**, including the 4-lizard window).
- Scene changes need no explicit invalidation (tags are exact codes); genuinely unexpected codes take the same protected path.

## Manifest inventory / VRAM budget (per-phase, from arcade data capture)
| Load group | Distinct codes over time | Per-frame concurrent (≈) | 128-cell budget verdict |
|---|---|---|---|
| Frontend/attract/title | 38 | ≤20 | fits outright |
| Stage-1 gameplay (player+lizards+bats+items+effects) | 372 | ~50 | working set fits per-frame; full set streams via protected replacement (≤1.5 KB/frame uploads) |
Later stages: same mechanism by construction (no per-stage tables required at runtime); per-stage inventories to be appended as stages become reachable — no code is silently omitted (overflow path renders correctly or skips visibly+counted, never wrong art). Pinned per-scene ROM manifests remain available as an N3 refinement when composite merging repacks cells.

## Builds
| Build | SHA | Status |
|---|---|---|
| 0222 | `b38cd392b25db4f6…` | **REJECTED** — CCR-clobber: `move.w (%sp)+,%d0` after the `btst` destroyed the Z flag, so every cell read "referenced" and *all* sprites were dropped (emitted=0). Preserved. Durable m68k lesson: restore registers across flag-carrying returns with `movem` (does not touch CCR). |
| **0223** | `4bd3e58e78883790…` (1,583,992, counter 223, GATE_PASS, cfg 256/HUD=0) | **Candidate** — zero steady-state drops; Rastan + five complete lizards verified. Rolling ROM. |
opcode_replace 216 unchanged; coverage paired per build.

## Validation (MAME; 0221 = fault baseline)
Title ✓ · READY ✓ · gameplay ✓ · Rastan correct (colors/position/animation) ✓ · five complete animated lizards, no missing/reappearing parts ✓ · palettes/alignment preserved ✓ · retirement clean ✓ · planes identical to 0221 (untouched) ✓ · drops: 0221 ≈1.2/frame → 0223 **0/frame** (2 lifetime, title warm-up) · speed improvement retained (pipeline unchanged apart from the residency block). Bats/attract-cycle/projectiles/scene-transition: to be exercised in emulator/hardware acceptance (USER MUST VERIFY) — the mechanism is family-agnostic (code-keyed).

## Resource before/after (0221 → 0223)
Residency WRAM: 256 B tags + **16 B bitmap** (+16 B) · upload queue 8→12 entries (worst-case pattern DMA 1.0→1.5 KB/frame, still ≪ VBlank budget with 640 B SAT DMA) · steady-state pattern DMA: ~1 upload/frame → ~0 (uploads only on genuinely new codes) · cache hits: ~all; misses invisible · CPU: +4 way-compares & bitmap ops per sprite (negligible vs the deleted mirror scans) · VRAM: unchanged (128 cells, 16 KB) · free VRAM/audio headroom unchanged from N1.

## Three phenomena separated (as required)
1. **Residency pop-in/disappearance — ELIMINATED** (this task).
2. Physical per-scanline/total sprite loss — remains, N3 composite merging.
3. Rolling display-off/plane flicker — remains, N2 (measured unchanged: plane path untouched).

## USER MUST VERIFY (BlastEm / Exodus / Sega Nomad)
1. No sprite component ever vanishes/reappears (walk into the 4–5 lizard pack; watch animations). 2. No wrong/garbage artwork on any sprite, ever. 3. Rastan/lizards/bats correct as in 0221 but stable. 4. Hurry-up swarm stability. 5. Speed improvement retained. 6. Black bar unchanged (N2 pending — do not judge here). 7. Title/attract/frontend sprites correct.

## STOP status
NOT triggered — coverage established from arcade data (388-code inventory + family-agnostic mechanism); the one numbered defect (0222 CCR bug) was concrete and corrected sequentially.
