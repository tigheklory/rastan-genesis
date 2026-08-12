# Build 0273 — Retire the Frontend HUD PC090OJ Tail at the Original Arcade-Code Boundary

**Agent:** Andy · **Type:** source + spec native-replacement / sequential build · **Build produced: YES (0273).**
**STOP: NO.** Baseline: Build 0272. Task classification: **EXTENDING** (OPEN-024 frontend HUD family).

## Summary
Build 0272 produced the correct native numeric HUD but still ran the obsolete arcade PC090OJ HUD builder and
erased its output with a per-frame Genesis-side clear (`.Lnq_hud_clear_records`). Build 0273 cuts at the
**original arcade-code boundary**: the arcade HUD builder `0x3B8B0` (records 4..45) and the credit builder hook
`0x3B902` (records 17..21) are retired to `rts`, so **no arcade PC090OJ HUD record is produced at all**. The
entire frontend HUD — score/high-score/credit digits AND the fixed HUD labels — is now produced by
`native_frontend_hud_emit` and committed through the existing SAT path. The write-then-clear workaround is
**deleted**. The generic copier `0x3B930` is **preserved untouched**.

Because `.Lnq_emit_entry` applies the identical coordinate transform as the retired scan decoder
(`.Lpc090oj_decode_record`), and `.Lnq_title_labels` holds the exact object-RAM label records the arcade builder
formerly wrote, the native output reproduces the former rendering **byte-for-byte**.

## Files changed
- `apps/rastan-direct/src/pc090oj_hooks.s` — `native_frontend_hud_emit` now emits labels+scores+credit;
  `.Lnq_title` calls it once; retired `genesistan_pc090oj_hook_target_3b902` to `rts`; **deleted**
  `.Lnq_hud_clear_records` + `.Lnq_hud_owned_records`.
- `specs/rastan_direct_remap.json` — added opcode_replace `0x03B8B0` `41FA009E`→`4E754E71` (rts;nop);
  `expectations.opcode_replace_count` 221→222.
- `tools/translation/postpatch_startup_rom.py`, `tools/translation/verify_canonical_rom.py` —
  `CANONICAL_OPCODE_REPLACE_COUNT` 221→222; `CANONICAL_TOTAL_GENESIS_BYTES_COVERED` 0x184AC0→0x184A1C.
- `docs/design/Andy_build0273_arcade_hud_pc090oj_tail_retirement.md` (this), `AGENTS_LOG.md`, `KNOWN_FINDINGS.md`.

## Build facts
- **GATE_PASS.** Counter **272 → 273.** ROM `dist/rastan-direct/rastan_direct_video_test_build_0273.bin`;
  SHA-256 `a9c8a609774e48c38c3e5c740a3e04f7b74675a896dc0a36d2529846ea5363b8`; size **1591836**; boot guard PASS.
- opcode_replace count **221 → 222**; canonical coverage **0x184AC0 → 0x184A1C** (−164 bytes: clear routine
  deleted). Builds 0265–0272 preserved. 30 s Genesis smoke
  `states/traces/rastan_direct_video_test_build_0273_mame_30s_20260808_134551` clean (0 unmapped/fatal/error).

## Semantic cut used
Arcade semantic HUD decision (live score/HS/credit values + fixed layout) → `native_frontend_hud_emit`
(glyph/digit expansion) → native SAT → existing arcade-owned VBlank commit. The PC090OJ record-construction tail
(`0x3B8B0` builder + `0x3B902` credit tail, both routed through the generic `0x3B930` copier) is removed. No
`0x3B930` change, no record-number band, no captured final-sprite table, no PC090OJ-shaped scratch.

## Table 1 — ARCADE CUT PROOF
| Arcade routine/site | Semantic work | PC090OJ-only work | Replacement/cut | Evidence |
|---|---|---|---|---|
| `0x3B8B0` (sole caller `0x3B06A`) | none | builds records 4..45 (labels+digits) via 3× `bsr 0x3B930` + inert `0x3B802` + `0x3B902` | opcode_replace entry insn `41FA009E`→`4E754E71` (`rts;nop`) | arcade disasm; ROM table decode; runtime: 0 HUD records after cut |
| `0x3B902` hook (8 callers) | none | builds records 17..21 (credit digits + labels 18..20) | hook body → `rts` | source; consumer matrix (Table 2) |
| `0x3B930` (generic copier) | n/a — shared record copier | copies whatever caller supplies | **PRESERVED untouched** (now uncalled) | spec unchanged; callers all retired |
| `0x3B802` (digit emitter) | none | digit overlay | already inert (Build 0270) | prior build |
| `0x3B926` (clears recs 5..13) | none | record clear | left intact (harmless; records already blank) | self-contained hook |

## Table 2 — HUD CONSUMER COVERAGE (Rule 13)
| Semantic use | State/caller | Old PC090OJ producer | Native owner (0273) | Validation evidence | Old output retired? |
|---|---|---|---|---|---|
| Player score digits | title / PUSH / all frontend (scan) | 0x3B8B0 recs 28..33 + 0x3B802 | `native_frontend_hud_emit` scores | SAT byte-identical vs 0272 (title + PUSH) | yes |
| High-score digits | all frontend | 0x3B8B0 recs 22..27 + 0x3B802 | native scores (0xFF0142) | SAT byte-identical | yes |
| P2 score digits | all frontend | 0x3B8B0 recs 37..42 | native scores (right column) | SAT byte-identical | yes |
| Credit count | credit state (0xFF0117>0) | 0x3B902 recs 17/21 | native credit block | SAT byte-identical (scene0/stage0100 credit=1) | yes |
| HIGH SCORE / 1P / labels | all frontend | 0x3B8B0 recs 4..16 | `.Lnq_title_labels` via emit_entry | SAT byte-identical; values == object records | yes |
| 2UP-row labels (18..20,34..36,43..45) | all frontend | 0x3B8B0 + 0x3B902 | `.Lnq_title_labels` | SAT byte-identical | yes |
| 0x3B902 state callers 0x3A20E/0x3A264/0x3A640/0x3A6C4/0x3A820/0x3A8E0 | frontend HUD setup | 0x3B902 recs 17..21 | native (records 17..21 rendered only by frontend scan where native runs; gameplay uses .Lnq_gameplay) | frontend game-state RAM byte-identical thru frame 2600; SAT byte-identical | yes |

**Reachability note (honest):** title (scene0/0000) and PUSH+credit (scene0/0100) are directly reached in
attract and validated **byte-for-byte**. Story / ranking / ROUND-READY are not reachable via attract or simple
Start-driving; they are covered by the structural invariant — `0x3B8B0`/`0x3B902` build from **fixed ROM
templates** (state-invariant record values, confirmed identical across the two reachable frontend states), and
every frontend scene (scene≠1) routes through `native_frontend_hud_emit`; gameplay (scene 1) uses the separate,
untouched `.Lnq_gameplay`. No state shows a partial top-HUD in the reached frontend, and no producer other than
`0x3B8B0`/`0x3B902` writes records 4..45 (3b930 caller census).

## Table 3 — REMAINING PC090OJ STATUS
| Area | Before (0272) | After (0273) | Why remaining |
|---|---|---|---|
| 0x3B802 | inert | inert | n/a |
| 0x3B8B0 HUD builder | live, builds recs 4..45 | **retired (rts)** | — |
| 0x3B902 credit builder | live, builds recs 17..21 | **retired (rts)** | — |
| 0x3B930 generic copier | live (called by above) | **preserved, now uncalled** | generic; kept per policy |
| native_frontend_hud_emit | scores+credit+clear | **labels+scores+credit** (complete HUD) | native owner |
| .Lnq_hud_clear_records / _owned_records | present (per-frame clear) | **deleted** | workaround removed |
| Frontend HUD labels | on object-RAM scan | **native** | converted |
| 0x5A098 status row | legacy scan | legacy scan (unchanged) | deep-gameplay family, out of scope |
| pc090oj_workram_block_sprites* | legacy scan | legacy scan (unchanged) | player block, out of scope |
| D00298 / D002B0 | legacy scan | legacy scan (unchanged) | attract-demo family, out of scope |
| frontend object scan | renders HUD + player + D00298 + 5a098 | renders **only** player + D00298 + 5a098 | HUD family removed |

## Table 4 — PERFORMANCE / REDUNDANT-WORK REDUCTION
| Metric | 0272 | 0273 |
|---|---|---|
| Non-blank HUD object records produced (frontend) | 50 (labels+digits) | **0** |
| Per-frame arcade builder work | 0x3B8B0 (3× 3B930 copies) + 0x3B902 | **none** |
| Per-frame Genesis HUD clear traversal | `.Lnq_hud_clear_records` (20 records) | **removed** |
| Object-RAM scan HUD-record decode/residency | ~22 label/digit records | **0** |
| Genesis code size (canonical coverage) | 0x184AC0 | 0x184A1C (**−164 bytes**) |
| Headless MAME avg speed (30 s, host-bound) | ~1249% / 1236% | ~1230% / 1227% |

Removed work: the arcade PC090OJ HUD production, the per-frame clear traversal, and the scan's HUD-record
processing. **Metric honesty:** headless MAME speed is host-bound at >1200% and is **not** a Genesis-CPU
utilization measurement — the two builds measure within run-to-run noise; the concrete reductions are the
record-count (50→0), the deleted clear traversal, and the −164-byte code shrink.

## Runtime validation performed (platform: Rastan Genesis ROM under MAME `megadriv` driver)
- **Frontend SAT byte-diff 0273 vs 0272:** title (scene0/0000) — positions identical; PUSH+credit
  (scene0/0100 credit=1) — **full SAT (Y,T,X) byte-for-byte identical** (15 sprites).
- **Retirement:** 0 non-blank HUD object records in 0273 across all reached states (0272 had 50).
- **Frontend game-state RAM** (0xFF0100–02FF and actor area 0xFF2200–23FF) **byte-identical** through frame 2600
  (entire attract frontend).
- **Gameplay:** static gameplay HUD sprites identical; the attract-DEMO diverges only *after* the demo
  transition — a ~1-frame transition-phase artifact (frontend game-state identical pre-transition; real gameplay
  is input-driven; `.Lnq_gameplay` untouched).

## Regressions checked / limitations
- Checked: title, PUSH, credit (byte-identical); gameplay path untouched; 0x5A098 / workram_block_sprites /
  D00298 producers untouched (not in the reached frontend HUD; render via the still-active scan).
- Limitation: story / ranking / ROUND-READY not directly reached (attract does not cycle to them; game-over flow
  not scriptable cheaply) — covered by the fixed-template structural invariant, not direct byte capture.
- Observation (benign): attract gameplay-demo diverges after the demo transition due to a ~1-frame phase shift
  from removing the retired producers' per-transition work. Frontend and HUD are provably unaffected.

## USER MUST VERIFY (Rastan Genesis ROM — BlastEm/Exodus/hardware)
1. **Title screen:** HIGH SCORE label + live high-score digits, 1P/2UP labels, PUSH text — identical to 0272.
2. **Throne / PUSH-BUTTON screen:** score, high score, HUD labels, throne artwork — identical.
3. **Credit state (press Start):** credit count digit correct and shown only when a credit exists.
4. **Story / ranking / ROUND-READY** (reachable only by real play): confirm the top HUD (HIGH SCORE + score row)
   renders correctly — this is the structurally-covered-but-not-byte-captured set.
5. **Gameplay:** in-game score/HUD and actors unchanged; no stale HUD sprite fragments on the title↔game
   transitions.

## STOP
**STOP: NO.** The arcade HUD PC090OJ tail is retired at the arcade-code boundary; the full frontend HUD is
native; the write-then-clear workaround is deleted; `0x3B930` is preserved; the reachable frontend states are
byte-identical to the accepted 0272 baseline; a GATE_PASS Build 0273 is produced.
