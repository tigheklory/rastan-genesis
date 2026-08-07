# Build 0271 — 0x3B802 Fully Retired (scores + credits native); 0x5A098 status pending its state

**Agent:** Andy · Build 0271 (0270 intermediate: had a stray rec17 credit sprite, fixed here). GATE_PASS.
Phase 0: EXTENDING (OPEN-024/OPEN-006). No CONFIRMED/STRONG contradiction.

## Result
`0x3B802` (the primary 10-caller frontend HUD/score/credit producer) is **fully retired** to an inert stub, with
every live consumer proven to have a native owner (rule 13/14 satisfied). `0x5A098` remains **restored/legacy**
because its status-display state was not reachable in the harness (rule 13 — not retired without proof).

## Reaching the credit state (resolved the prior "unreachable" limit)
Genesis-driver MAME with **P1 Start** pulses registers a credit (`0x00FF0117` 0->1) and the throne/insert-coin
credit display appears (rec17/21 move on-screen). Captured its layout: credit count = `0x00FF0117` digit at
X 0x128 / Y 0xE8; the `0x00FF0103`/rec17 field is **not rendered** (confirmed: legacy 0269 SAT has no such
sprite), i.e. a dead consumer.

## Native implementation
- Player/high-score digits: `.Lnq_title_emit_scores` (live BCD `0x00FF011E`/`0x00FF0142`, arcade leading-zero
  suppression, fixed layout) — used by the title and the frontend scan path; gameplay uses `.Lnq_project_p1_hud`.
- **Credit count:** native block in `.Lnq_title_emit_scores`, shown only when `0x00FF0117 > 0`, glyph
  `0x2A + (0xFF0117 & 0xF)` at X 0x128 / Y 0xE8. Emitted via the shared `.Lnq_emit_entry` register primitive.
- The frontend scan **skips** the now-native records (17, 21, 22–33, 37–42); labels (4–21 non-digit, 34–36,
  43–45) still render from the scan.
- `0x3B802` retired to `rts` (all consumers native/dead). `0x5A098` restored (unchanged behavior).

## Consumer coverage matrix
| Old producer | Caller/use | State | Old PC090OJ output | Complete native owner | Validation | Retired? |
|---|---|---|---|---|---|---|
| 0x3B802 | player-1 score | title / throne / gameplay | records 28–33 | `.Lnq_title_emit_scores` / `.Lnq_project_p1_hud` | total SAT 15/15/15 == 0266 | YES (native) |
| 0x3B802 | player-2 score | same | records 37–42 | `.Lnq_title_emit_scores` | same | YES (native) |
| 0x3B802 | high score | title / throne / ranking / gameplay | records 22–27 | `.Lnq_title_emit_scores` (0xFF0142) | throne SAT == 0269 | YES (native) |
| 0x3B802 | credit count | insert-coin / throne (credit>0) | record 21 | native credit block (0xFF0117) | credit-state SAT == 0269 (START-driven) | YES (native) |
| 0x3B802 | 0xFF0103 (rec17) | — | record 17 | n/a | not rendered in 0269 either | YES (dead consumer) |
| 0x5A098 | status sprites 30–43 | deep gameplay/status (not reached) | records 30–43 | none yet | not reachable in the 90s attract + Start harness | **RETAINED** (rule 13) |

## Validation (platform-explicit)
- **Genesis-driver MAME:** total SAT per state 0271 == 0266 (title 0/0000, throne 0/0100, gameplay 1/0100 = 15/15/15 — no regression, no double). Credit-state SAT (START-driven, credit=1) **byte-identical to 0269**.
  30s smoke: 1798 frames, 0 errors.
- Score leading-zero/positions: unchanged from Build 0265/0269 (native producer reused).

## Measured legacy reduction
- 0x3B802 body deleted (retired to stub): coverage 0x184B38 -> 0x184AA0 (≈152 bytes; net vs 0269).
- 0x3B802 frontend PC090OJ record writers eliminated: all (scores + credit).
- Frontend scan records skipped (now native): 17, 21, 22–33, 37–42.

## What remains (honest)
- **0x5A098 status** — legacy, retained until its display state is reached and given a native owner. Its records
  (30–43) overlap the score record range and its trigger state was not reachable here; retiring it blind would
  risk another 0267-style regression, which rule 13/14 forbid.
- Phase-5 architectural move (native scores invoked from a dedicated frontend HUD pass rather than from inside
  the scan) is **not** done in this build; the current invocation from the scan path is retained as the
  temporary corrective structure. The score/credit family no longer *depends on* the scan for its output, but is
  still *called from* it.
- Other legacy families: `pc090oj_workram_block_sprites*`, D00298/D002B0, score-record positioning producer.

## USER MUST VERIFY
1. Title: HIGH SCORE live value, no leading `00`; 1UP/2UP; PUSH text.
2. Throne/PUSH: HIGH SCORE value present; insert a coin (Start) → credit count digit appears.
3. ROUND/READY, ranking, story: high score present (structurally native via scene!=1 path).
4. Insert-coin credit display: credit count correct.
5. Gameplay: score/HUD/actors unchanged.
6. Any life/status (0x5A098): unchanged (restored, not altered).
