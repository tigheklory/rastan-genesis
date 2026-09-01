# Build 0328 — Native Sprite Over-Emission / Duplication — STOP (root cause not proven; prior metric corrected)

**Type:** Analysis. No ROM. Classification: **EXTENDING**. Baseline Build 0327.

## 1. Phase 0
Priors/hazards: builds on the Build-0327 runtime-trace analysis. This task **corrects** a metric error in that prior doc. Deferred (untouched): `(code,bank)` color coverage, vertical-fill/noise, HUD/axe palette, waterfall animation. Contradiction status: none new; one self-correction below.

## 2. SAT-70 explanation — the prior "plateau" was a MEASUREMENT ARTIFACT (corrected)
- `NATIVE_SAT_MAX = 80`. The finalizer `.Lnq_done_scan` terminates the **Genesis sprite link-chain** at the last emitted entry (`.Lnq_have` masks the link field to 0). Stale entries beyond the chain are **not rendered**.
- The Build-0327 trace counted `staged_sprite_sat` slots with `Y != 0` across all 80 — which **includes stale, non-rendered entries** — and reported a "constant 70 plateau." **That was wrong.** The rendered count is `pc090oj_emitted_count` (= `d5`, the chain length).
- Re-measured (attract demo, the only self-driveable sample): `pc090oj_emitted_count` is **variable**, ≈ **28 avg / 72 max**, not a constant 70. Per-lane maxima: `back_enemy` 53, `player_body` 10, `middle` 7, `hud` 9, `front_effect` 1, `player_front` 0.
- **Is 70 requested or capped?** Neither — 70 was an artifact of counting stale slots. The real requested/emitted chain is variable (≤ 72 in the sample), below the 80 cap.
- **Consequence:** the earlier claim "sprite over-emission → sustained slowdown (70/frame saturation)" is **retracted**; it is **NOT PROVEN**. The real rendered count in Tighe's actual gameplay was never measured (his trace captured only the stale `Y!=0` count) and must be re-measured with `pc090oj_emitted_count` before any slowdown claim.

## 3. Arcade reference (existing exports)
Arcade sprite build uses two dispatchers `FUN_00041dae` and `FUN_00045dfa`, both writing into **shared PC090OJ sprite RAM regions** (0xD00170 effect, 0xD00300 middle, 0xD00460 enemy) — i.e. **last-writer-wins** into the same hardware object RAM. Callers: `actor_family0_render_3d054` calls both; `0x41f30` calls `0x41f5e` then `0x41dae`; `0x03A818` calls `0x45dfa`, `0x03A854` calls `0x41f5e`.

## 4. Genesis emitter audit
Gameplay SAT is built by `pc090oj_native_emit_pass` (`.Lnq_gameplay`) concatenating six append-only queues (hud / front_effect / player_front / middle / player_body / back_enemy) into one link-chain. Producers: `native_stage_dispatch_41dae` scans `a5+0x02C8` (enemy), `a5+0x05C8` (middle), `a5+0x0748` (effect); `native_stage_dispatch_45dfa` scans `a5+0x05C8` (**enemy**), `a5+0x0748` (effect), `a5+0x08C8` (middle). The Genesis hooks: `hook_41dae` → (41dae **or** 45dfa by `a5+0x02A2` mode) + emit_pass; `hook_45dfa` → 45dfa + emit_pass; `hook_41f5e` → `native_sprite_frame_begin` (clears fx/mid/be counts).

**Note the structural risk:** the two dispatchers scan **overlapping** blocks (`a5+0x05C8`, `a5+0x0748`), and the arcade resolves overlap by last-writer-wins into shared RAM, while our queue model **appends**. If both dispatchers filled the queues before one emit_pass, overlapping blocks would double-emit.

## 5. Base-form + anim-form hypothesis: NOT PROVEN (and dual-emit hypothesis DISPROVEN)
Runtime check (write-tap on `pc090oj_emitted_count`): **`emit_pass` runs at most once per frame** (histogram 0×=4837, 1×=163; never 2×). So only **one** dispatcher's queue set is emitted per frame — the append-vs-overwrite double-emit hypothesis from §4 is **DISPROVEN**. That leaves the duplication unexplained by the dual-hook path.

## 6. Retirement / stale-record: the SAT is rebuilt fresh each emit (double-buffered banks); stale slots exist but are chain-terminated (not rendered). No proven stale-render.

## 7. Duplication root cause: **NOT PROVEN**
Two candidate mechanisms were investigated and eliminated: (a) sustained SAT saturation (was a counting artifact), (b) two `emit_pass` calls accumulating overlapping dispatchers (emit_pass runs once/frame). The visible horizontally-offset duplication is real but I could **not tie it to a specific native producer boundary** with the available static + write-tap evidence. The remaining untested candidate is **two separate active actor records (base actor + its "anim/hit form" — census shows shared code 0x0A73) both being emitted**, which needs per-actor-record runtime provenance that write-taps alone cannot isolate (execution taps are unavailable in this MAME Lua).

## 8–9. Expected-vs-emitted counts / performance
Not established — the only reliable rendered-count sample (attract) shows variable ≤72, and Tighe's gameplay was never measured with the correct metric. **Sprite over-emission performance effect: NOT PROVEN.**

## 10–11. Implementation: NONE (STOP). No color/reindex/vertical-fill/palette changes.

## 12. STOP condition
**STOP #1** — the Genesis excess/duplication cannot yet be tied to a specific native source/producer boundary; and **STOP #2** — determining correct suppression would require confirming which active actor records (base vs anim/hit form) the arcade emits per frame, which is not established in existing evidence and cannot be isolated with the available instrumentation.

## 13. Recommended bounded next step
1. **Re-measure correctly during a Tighe playthrough**: capture `pc090oj_emitted_count` + the six per-lane counts (not the stale `Y!=0` count) at the duplicate encounters and the perceived-slow region — to establish whether there is a real over-emission at all.
2. **Isolate the duplicate**: capture the per-lane counts and the `a5` actor-block active flags to determine whether the duplicate set is the base actor's "anim/hit form" record (shared code 0x0A73) being emitted alongside the base — the strongest remaining candidate.
3. Only then, if proven, apply a bounded fix that matches the arcade's last-writer-wins/record-selection semantics.

## 14. Follow-ups preserved
HUD `1UP`/score (bank 0x30) → first-class Palette Composer editable (author white; no hardcode). Axe → same. Deferred `(code,bank)` sprite reindex remains the separate color task.
