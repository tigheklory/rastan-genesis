# Build 0328 — Shared PC090OJ Piece-Terminator Fix

**Type:** Implementation / verification. ROM produced. Classification: **EXTENDING**. Baseline Build 0327.

## 1. Phase 0
Priors/hazards: implements the proven root cause in `Andy_build0327_multifamily_piece_overemission_proof.md`. Deferred (untouched): `(code,bank)` color, vertical-fill/noise, HUD/axe palette, waterfall anim. Contradiction status: none.

## 2. Root-cause prior (confirmed on inspection)
`0xFF` is the arcade PC090OJ actor-representation terminator (arcade helper `FUN_0003c606`: `cmpi.b #0xFF` → `rts`). Genesis `.Lnea_dloop`/`.Lnea_dmirror`/`.Lnea_sloop` treated `0xFF` as skip-and-continue and ran to the fixed **destination-slot capacity** (enemy 10, slot-8 19, middle 4, effect 1, player 13), over-reading into the next pose(s).

## 3. Destination-capacity accounting proof (critical pre-check)
Verified `a1` (arcade dest `0xD00460`) is **vestigial** in the native path: inside `emit_actor_common` it is immediately clobbered (reused as the family-descriptor base, `lea .Lnea_fam_bases,%a1`), and `native_sprite_emit` outputs to the **lane queues + counts** (`native_*_count` selected by `native_sprite_lane`), never `a1`. Therefore:
- the next actor's output position is the lane-queue append point (count-driven), **not** `a1`;
- terminating a representation early simply emits fewer pieces → smaller lane count → the next actor appends correctly;
- **no remaining-capacity accounting is required**; the capacity (`d5`/`d2`) is only the loop ceiling.
So a clean `beq → exit` is correct here (unlike the arcade-RAM model where a1 accounting would matter).

## 4. Implementation — all three shared loops
In `apps/rastan-direct/src/pc090oj_hooks.s`, the `0xFF` branch was redirected from the per-piece continue to the function exit `.Lnea_ret` (which restores `d0-d7/a0-a6` and returns), in:
- `.Lnea_dloop` (normal orientation): `beq.s .Lnea_dnext` → `beq.w .Lnea_ret`
- `.Lnea_dmirror` (mirrored orientation): `beq.s .Lnea_mnext` → `beq.w .Lnea_ret`
- `.Lnea_sloop` (specialized dispatch): `beq.s .Lnea_snext` → `beq.w .Lnea_ret`
The real-piece continue labels (`.Lnea_dnext/mnext/snext`) are unchanged and still reached by fall-through after `native_sprite_emit`. Net behavior: **emit until end-of-representation (`0xFF`) OR capacity**, whichever comes first. Capacities 10/19/4/1/13 are unchanged (ceiling only). No per-enemy counts, no coordinate/SAT filtering, no NOP/RTS patch.

## 5. Descriptor-format coverage
`0xFF`-terminated pose format confirmed across the affected descriptor types: family 0 (lizardman classes 0x17/0x18 = 8-piece, 0x1C = 10-piece, 0x70 = 4-piece) and family 2 (0x0B = 4-piece, 0x13 = 1-piece). All active R1/P1 enemy families flow through the same shared expander; the fix is general.

## 6–7. Exact diff
Only `pc090oj_hooks.s` changed for Build 0328 (3 branch lines / 6 lines). No changes to palette routing, `(code,bank)` reindex, sprite assets, Layer A/B, CRAM, HUD, axe, vertical-fill, epoch, waterfall, actor state, spawning, or pattern-reuse policy. (The other files in the working-tree diff are the already-shipped Build-0325 palette work.)

## 8. Lizardman before/after (static re-derivation)
| case | capacity | pose | 0327 emitted | 0328 emitted | next-pose leakage |
|---|---:|---:|---:|---:|---|
| Lizardman normal | 10 | 8 | 10 (+2) | **8** | **NO** |
| Lizardman slot 8 | 19 | 8 | 17 (+9) | **8** | **NO** |
| family0 c0x70 | (lane) | 4 | budget | **4** | NO |
| family2 c0x13 | (lane) | 1 | budget | **1** | NO |
Loop now hits the `0xFF` terminator before the capacity for every short pose; the 19-capacity remains available as a ceiling for a genuinely large slot-8 representation.

## 9. Cross-family verification
All three orientation/dispatch paths repaired; the shared expander is the single output path for lizardman/valkyrie/chimera/flying-demon/insect/bats; descriptor format confirmed `0xFF`-terminated. Large representations whose pose legitimately reaches capacity without an earlier `0xFF` still emit up to capacity (preserved).

## 10. Performance (corrected metric only)
Runtime `pc090oj_emitted_count` (attract, never full-SAT `Y!=0`): enemy lane `be` max **53 → 40**, avg **8.8 → 6.6 (−25%)**; total emit max **72 → 60**. **Proven: unnecessary post-terminator piece/SAT work removed.** Overall gameplay slowdown: **CONTRIBUTING FACTOR** — not claimed as the complete cause (needs a corrected gameplay measurement in Tighe's real playthrough).

## 11. Automated gates
Build 0328 → `dist/rastan-direct/rastan_direct_video_test_build_0328.bin`, SHA `8a4d15c5…`. Seven-epoch gate PASS (records 0,3,4,10,11,12,15); Plane-A/B full-LUT PASS; plane drops 0; exceptions 0; sp_valid YES; MAME 30s boot clean (978%). HUD default `RASTAN_GAMEPLAY_HUD_SPRITES ?= 2` (score enabled).

## 12. USER MUST VERIFY
First lizardman no longer shows an overlaid second pose; normal lizardmen lose the duplicated lower-left cell(s); other families' duplicate pieces gone/reduced; legitimate separate enemies still present; large/multipart sprites complete; both facings complete; special-dispatch actors/effects not truncated; gameplay speed; (noise + wrong `(code,bank)` colors remain deferred; Layer-A unchanged; score displayed). **If any legitimate actor loses pieces → that indicates a pose whose length exceeds its lane capacity; report it.**

## 13. Deferred `(code,bank)` color architecture — unchanged, separate next task.
## 14. Follow-ups — HUD `1UP`/score (bank 0x30) + Axe → first-class Palette Composer representations (no hardcoding).
