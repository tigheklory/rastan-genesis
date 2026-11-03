# Build 0269 — Frontend HUD Score Native Ownership + Build 0267 Regression Fix

**Agent:** Andy · Build 0269 · GATE_PASS. Phase 0: EXTENDING (OPEN-024/OPEN-006). No CONFIRMED/STRONG contradiction.

## Build 0267 failure / root cause
Build 0267 stubbed `0x3B802` and `0x5A098` to `rts` after proving only the **title** and **gameplay** score
consumers had native owners, and generalized that to all callers. The title-only MAME attract harness never
reached the throne/PUSH-BUTTON, ROUND/READY and ranking screens, which still consumed `0x3B802`'s high-score
digits through the frontend object scan. Result (Tighe screenshots): those screens lost their high-score value
("00"), while the title still showed it. That was **deletion without replacement** — a rule-13 violation.

## Governance added this task
- CLAUDE.md: "Never Delete a Producer Before Replacing Every Live Semantic Consumer."
- RULES.md rule 13 ("PROVE ALL LIVE CONSUMERS BEFORE RETIRING A SHARED PRODUCER", incl. mandatory consumer
  coverage matrix) and rule 14 ("DO NOT USE INERT STUBS AS A SUBSTITUTE FOR NATIVE REPLACEMENT").

## Fix (native ownership for the score display, legacy retained where not yet native)
Provenance (Build 0266, working) across states shows the high/player-score digits are at **fixed positions**
(rec22–27 high, rec28–33 player1, rec37–42 player2), all reading live BCD `0x00FF0142` / `0x00FF011E`, in every
state (title 0/0000, throne 0/0100, gameplay 1/0100). So one shared native producer owns them everywhere:
- **Title:** `.Lnq_title` (unchanged).
- **All other frontend states (scene != 1):** `.Lnq_title_emit_scores` is now called from the frontend scan
  path, and the scan **skips** the now-native score records (22–33, 37–42). Labels (4–21, 34–36, 43–45) still
  render from the scan.
- **Gameplay:** `.Lnq_project_p1_hud` (unchanged).
Shared native SAT primitive: `.Lnq_emit_entry` (register-passed). No captured sprite table, no record-shaped
scratch, no PC090OJ record between the live value and the native SAT for the score digits.

`0x3B802` and `0x5A098` were **restored** from Build 0267's inert stubs (the 0266 title gate was dropped, not
reinstated). Per rule 13 they remain only for their **not-yet-native** consumers (see matrix); their score
records are now dead (scan-skipped) and owned natively.

## Consumer coverage matrix
| Old producer | Caller/use | State(s) | Old output | Complete native owner | Validation | Legacy retired? |
|---|---|---|---|---|---|---|
| 0x3B802 | player-1 score | title / throne / ranking / gameplay | 6-digit records 28–33 | `.Lnq_title` + `.Lnq_title_emit_scores` (scan) + `.Lnq_project_p1_hud` | SAT matches 0266 (hs col 5/5/4; total 15/15/15) | scores scan-skipped (native) |
| 0x3B802 | player-2 score | same | records 37–42 | `.Lnq_title_emit_scores` | same | scan-skipped (native) |
| 0x3B802 | **high score** | title / throne / ranking / gameplay | records 22–27 | `.Lnq_title_emit_scores` (reads 0xFF0142) | throne 0/0100 restored, matches 0266 | scan-skipped (native) |
| 0x3B802 | credit digits | insert-coin | 1-digit records 17/21 | none yet | off-screen (Y≥0x1E8) in all reachable states; insert-coin not reachable in harness | **RETAINED** (rule 13) |
| 0x5A098 | status sprites 30–43 | unreached | records 30–43 | none yet | consumer state not reachable in harness | **RETAINED** (rule 13) |

Every **validated live** score consumer has a native owner. The two consumers without a native owner
(credit digits, 0x5A098 status) are **retained**, not retired — exactly what rule 13 requires.

## Validation (Genesis MAME, 90s attract cycle + 30s smoke)
- High-score column SAT sprites per state: **0269 == 0266** (title 5, throne 5, gameplay 4).
- Total SAT sprites per state: **15/15/15 == 0266** → no double-render (native scores + scan-skip verified).
- 30s smoke: 1798 frames, **0 errors**. Title + gameplay unchanged.
- Reached states: title (0/0000), throne/PUSH (0/0100), gameplay (1/0100). ROUND/READY and ranking screens were
  not reached by the attract harness in 90s; they are structurally covered by the same scene!=1 scan-path native
  scores, but are flagged for user visual confirmation.

## Measured
Coverage 0x184A50 -> 0x184B38 (net +0xE8 for the native-score integration; the 0267 inert-stub deletions were
re-added as restored producers). PC090OJ score-record consumers by the frontend scan: eliminated for records
22–33/37–42 (now native). No double render.

## Remaining PC090OJ producer families (enumerated)
`0x3B802` credit digits, `0x5A098` status, `pc090oj_workram_block_sprites*` (player/labels), the score-record
positioning producer, D00298/D002B0.

## USER MUST VERIFY
1. Main title: HIGH SCORE shows the live value (no leading `00`), 1UP/2UP, PUSH text.
2. Throne / PUSH-BUTTON: HIGH SCORE **value present** (fixed vs 0267).
3. ROUND/READY and ranking screens: high-score value present (structurally covered; please confirm visually).
4. Story: top HUD/high score correct.
5. Gameplay: score/HUD/actors unchanged.
6. Any life/status display (0x5A098): unchanged from before (producer restored, not altered).
