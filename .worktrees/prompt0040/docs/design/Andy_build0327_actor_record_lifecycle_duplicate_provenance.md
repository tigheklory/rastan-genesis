# Build 0327 — Actor-Record Lifecycle & Duplicate Provenance

**Type:** Analysis / instrumentation. No ROM. Classification: **EXTENDING**. Baseline Build 0327.
**Status:** corrected instrumentation built + pre-validated; **awaiting one SHORT targeted Tighe capture** (play to first duplicated enemy).

## 1. Phase 0
Priors/hazards: corrects the false SAT-saturation metric from `Andy_build0328_native_sprite_overemission_fix.md`. Deferred (untouched): `(code,bank)` color, vertical-fill/noise, HUD/axe palette, waterfall animation. Contradiction status: one self-correction (below); no new contradiction.

## 2. SAT metric correction (established)
Genesis SAT max = 80; the finalizer terminates the sprite **link-chain**, so stale entries past the terminator don't render. Counting `staged_sprite_sat` slots with `Y!=0` over-reports by including stale non-rendered entries — **invalid**. Authoritative rendered count = **`pc090oj_emitted_count`** (chain length). The prior "constant ~70 saturation → slowdown" is **retracted**; sustained over-emission slowdown is **NOT PROVEN**. → proposed KNOWN_FINDINGS **C** (§15).

## 3. Genesis actor-record block layout (static, confirmed)
a5 = `0xFF0000`. Record stride 64. Fields (from `.Lnative_emit_actor_common`): `+0` active, `+1` class, `+2` facing, `+0x16` base X, `+0x1A` base Y, `+0x1E` base tile **code**, `+0x27` attr (bank nibble = low 4 bits → effective bank `0x30|nibble`), `+0x38` family. Pools the dispatchers scan:
| block | addr | 41dae role | 45dfa role |
|---|---|---|---|
| enemyA | 0xFF02C8 | enemy (≤16) | — |
| **midB** | **0xFF05C8** | **middle (6)** | **enemy (6)** |
| effect | 0xFF0748 | effect (11) | effect (6) |
| midD | 0xFF08C8 | — | middle (5) |

`midB (0xFF05C8)` and `effect (0xFF0748)` are scanned by **both** dispatchers under **different lane roles** — the key overlap.

## 4. Arcade reference (existing exports)
Arcade dispatchers `FUN_00041dae` / `FUN_00045dfa` write **shared PC090OJ object-RAM** slots (0xD00170 effect / 0xD00300 middle / 0xD00460 enemy) — **last-writer-wins**. `actor_family0_render_3d054` calls both; `0x41f30`→(`0x41f5e` clear, then `0x41dae`); `0x03A818`→`0x45dfa`, `0x03A854`→`0x41f5e`.

## 5. Last-writer-wins vs Genesis append — HIGH-VALUE HYPOTHESIS (to prove with the targeted trace)
Arcade: dispatcher A writes rep X into object slot N; dispatcher B later writes rep Y into the **same** slot N → hardware shows only Y. Genesis: the native lanes are **append-only** queues, so if both dispatchers run and both scan `0xFF05C8` (as middle **and** enemy) / `0xFF0748`, the two representations are retained as **independent pieces** → the horizontally-offset duplicate. This is **distinct** from the already-disproven "two `emit_pass`/frame" hypothesis. Status: **NOT PROVEN** — hinges on whether **both** dispatch hooks run per gameplay frame and both emit the `0xFF05C8`/`0xFF0748` block (attract showed `emit_calls=1`/frame, but attract is an unrepresentative micro-sample; real gameplay is mode-dependent).

## 6. Base/anim/hit-form lifecycle
Census shows base + "anim/hit form" (shared code `0x0A73`). Pre-validation already observed **the same source code active in two record slots at one position** (lizardman code 75 ×2, though at Y=0x180 park in attract). Whether the visible duplicate is (a) base+anim records both active, (b) the `0xFF05C8` block emitted under two lane roles, or (c) two genuine actors — is resolvable directly from the corrected trace's raw records at the duplicate. Status: **NOT PROVEN**.

## 7. Horizontal offset
The trace records each source record's X (`+0x16`); if the duplicate is the `0xFF05C8` block emitted as both middle and enemy, the two copies share the actor's X — a *fixed* offset would instead point to two records with different X sources. The captured records let us quantify the exact X delta at the duplicate.

## 8–9. Corrected instrumentation (`tools/mame/scripts/trace_genesis_actor_provenance.lua`, SHA `2d2309eb…`)
Per frame: `pc090oj_emitted_count`; the six lane counts (hud/fx/pf/mid/pb/be); **`emit_calls`/frame** (write-tap on `pc090oj_emitted_count`); and every **active source actor record** in the four pools (block, idx, active, class, code, bank, X, Y, family) → `actor_records.log`; plus duplication signals (same code active in >1 block; same (X,Y) with >1 code). **Never uses full-SAT `Y!=0`.** This reconstructs `source actor record → lane → rendered count`.

## 10. Pre-play validation — **PASS**
Attract self-test captured: active actor records with id/active/class/code/bank/X/Y/family (e.g. lizardman code 75 bank 0x36; block actor 377/bank 0x30), correct `pc090oj_emitted_count` (≤72), all lane counts (be ≤53), `emit_calls` (=1/frame in attract), and both duplication signals firing. Source-actor→lane correlation is possible → proceed to a short targeted capture.

## 11. Targeted trace requirement (see final response)
One SHORT capture: **play to the first obviously-duplicated enemy and stop**. Goal: prove one duplicated actor completely (its source records, lanes, emit_calls/frame, X offset) before any broad statistics or fix.

## 12. Performance — RESET
`Gameplay slowdown root cause: NOT PROVEN.` To be re-evaluated only with `pc090oj_emitted_count` + lane counts (not `Y!=0`) from real gameplay. Noise correlation unproven.

## 13. Future `(code,bank)` color task
Unchanged and separate: complete R1/P1 sprite vocabulary is cross-bank `(code,bank)`-shared; final color architecture needs offline `(code,bank)` variants + O(1) selection.

## 14. Follow-ups
HUD `1UP`/score (bank 0x30) → first-class Palette Composer editable (author white, no hardcode). Axe → same.

## 15. KNOWN_FINDINGS
Proposed **C**: *Rendered Genesis sprite count = terminated SAT link-chain length / `pc090oj_emitted_count`; full-buffer `Y!=0` counts include stale non-rendered slots and are invalid for sprite-count/performance analysis.* (B candidates unchanged: 128-byte PC090OJ cell identity; `(code,bank)`-shared sprite vocabulary.)

## 16. Rack-advance follow-up (preserved)
MAME cheats `Finish Current Sub-Round Now!` / `Select Starting Round/Sub-Round`: if an original-arcade comparison is later needed, first inspect the cheat writes and confirm `Finish Current Sub-Round Now!` merely sets the normal completion condition (safe rack-advance navigation) before relying on it. Not needed for this task.
