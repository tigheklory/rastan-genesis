# Next Holistic PC090OJ Retirement Plan (from Build 0271)

**Agent:** Andy · Analysis/planning only — no source/spec/ROM/counter change. Phase 0: EXTENDING (OPEN-024/006).

## 1. Current-state table

| PC090OJ area | Build-0271 state | Semantic owner | Legacy dependency | Recommended action | After next unit |
|---|---|---|---|---|---|
| 0x3B802 | **RETIRED** (inert) | native `.Lnq_title_emit_scores` / `.Lnq_project_p1_hud` | none | none | retired |
| 0x5A098 | legacy (restored) | `a5@0x13A` status row (screen-setup 0x51040) | object scan | **DEFER** (state not reachable in harness) | still legacy, isolated |
| native score/credit invocation | called **from inside** `.Lnq_frontend_object_scan` | `.Lnq_title_emit_scores` | scanner coupling | **MOVE** to a dedicated native HUD pass | independent of scanner |
| frontend HUD labels (rec 4-16,18-20,34-36,43-45) | legacy (scanned) | fixed glyph strings + per-state anchors | object scan | **CONVERT** natively | native |
| score-record positioning producer | writes rec 22-42 X/attr (now **dead** — scan skips them) | arcade positioning code | object scan | **RETIRE for HUD** | retired for HUD |
| pc090oj_workram_block_sprites* | legacy | player block `a5+0x11B2` (18) / `a5+0x170` (4) | object scan | DEFER | legacy |
| D00298/D002B0 | legacy | attract-demo writer family | object scan | DEFER | legacy |
| frontend object-RAM scanner | active | — | — | shrink to player/D00298/5a098 only | **HUD-free** |

## 2. 0x5A098 semantic provenance
Arcade `0x5A098` (Genesis hook `genesistan_pc090oj_hook_status_sprite_5a098` @ `runtime_genesis_pc 0x000730D0`)
reads `a5@0x13A` (a status/counter word), tests bit15 (self-clear), then emits a **horizontal row of pieces at
Y=0xE8, X stepping 0x10**, base sprite RAM `0xD00048` (record 9), with the tile index derived from
`(a5@0x13A >> 11) & 7`. Its sole caller is `arcade_pc 0x051054`, inside a **screen-setup sequence** (0x51040:
`a5@0x13A := 0x3000`; conditional `jsr 0x5A502`; `jsr 0x5A098`; `a5@0x12FC := 0xFF`; `jsr 0x59F92` [score/status];
`bsr 0x5126E`; `jsr 0x52BB6`) gated on `a5@0x34` (player count). This is a **status/bonus indicator row**, not
numeric HUD.
**Reachability:** an execution watchpoint on `0x000730D0` under 48 s of attract + P1-Start driving produced
**zero hits**, and no status tile code (0x3E8-0x3F5) appeared in object RAM. Therefore it fires only in a
**deeper gameplay/round-transition state** (consistent with the `a5@0x13A`/player-count/screen-setup context).
**Confidence:** semantic MEDIUM (status row, `a5@0x13A`-driven); reachability LOW with current tooling — it needs
sustained gameplay driving (progress/round-clear), not just Start.

## 3. Frontend native invocation boundary
The frontend sprite finalizer is **`pc090oj_native_emit_pass`** (called from `genesistan_pc090oj_hook_target_41f5e`
and `_45dfa`, the arcade sprite hooks). Its dispatch: scene 1 → `.Lnq_gameplay`; scene 0 & stage 0 → `.Lnq_title`
(native, no scan); else → `.Lnq_frontend_object_scan`. **The debt:** for scene 0 stage!=0 / other frontend scenes,
`.Lnq_title_emit_scores` is invoked **from inside** `.Lnq_frontend_object_scan` (line ~2089). The correct boundary
is a **dedicated native HUD step in `pc090oj_native_emit_pass` itself**, run before the scan, so the scan services
only unconverted families. `pc090oj_native_emit_pass` is a finite arcade-called helper (RTS) — adding a native
HUD step there keeps Rule-4 compliance (no Genesis loop).

## 4. Remaining-family audit
- **0x5A098** — status/bonus row; `a5@0x13A`; records ~9-22 (arcade) / 30-43 (Genesis hook); deep-gameplay state;
  independent of the HUD family; DEFER (reachability).
- **workram_block_sprites** — the **player** sprite for frontend/non-gameplay (block copy `a5+0x11B2`→rec 120-137,
  `a5+0x170`→rec 92-95, tuples already `{word0,Y,code,X}`); reachable (throne character); medium leverage; player
  rendering (higher regression surface).
- **D00298/D002B0** — attract-demo raw-writer family (KF-032, Build 0254); reachable only in the attract demo.
- **score-record positioning producer** — arcade code that set the score records' X/attr; **its score output is
  already dead** (native scores + scan-skip). Retirable for the HUD once the HUD scan range is removed.
- **frontend object scan** — currently services HUD labels + player + D00298 + 5a098.

## 5. Dependency graph
Current:
```
scores/credits (live BCD)         -> native .Lnq_title_emit_scores --+  (but CALLED BY the scanner)
HUD labels (glyph strings)        -> arcade producers -> object RAM --+-> frontend scanner -> SAT
player block (a5+0x11B2/0x170)    -> workram_block_sprites -> obj RAM +
D00298 / 5a098                    -> their producers -> obj RAM ------+
```
After the recommended unit:
```
pc090oj_native_emit_pass (frontend boundary)
    +-> native HUD pass: scores + credits + LABELS  ------------------+-> SAT
    +-> frontend scanner: player block + D00298 + 5a098 (only) -------+
```
Disappears: the positioning producer's HUD writes; the scanner's ownership of records 4-45; the "native called
from scanner" coupling. Remains: scanner for player/D00298/5a098.

## 6. Candidate comparison

| Criterion | 0x5A098 + boundary | workram_block_sprites | **HUD labels + native HUD pass + positioning retire** |
|---|---|---|---|
| Semantic coherence | medium | high | **high (completes the HUD family)** |
| Legacy reduction | small | medium | **medium-high (records 4-45 leave the scan)** |
| Architectural leverage | low | medium | **high (creates the reusable native frontend pass)** |
| Shared reuse | low | medium | **high (pass + glyph facility reused by all later families)** |
| Evidence confidence | **LOW (unreachable)** | medium-high | **high (title/throne/credit reachable)** |
| Regression surface | **high (can't validate)** | high (player) | **low-medium (fixed labels, SAT-diffable)** |
| Implementation efficiency | poor | medium | **high (one coherent HUD pass)** |

## 7. Selected next retirement unit
**Complete the frontend HUD family: convert the remaining HUD text/labels to native, move the entire HUD
(scores + credits + labels) into a dedicated native HUD pass inside `pc090oj_native_emit_pass`, and retire the
score-record positioning producer's HUD role — removing HUD records 4-45 from the object-RAM scan.**
This is the coherent completion of the family 0x3B802 started, it is fully reachable/validatable, and it builds
the clean native frontend pass that 0x5A098 / player-block / D00298 will later plug into. 0x5A098 is explicitly
deferred until its gameplay state is reachable (a separate validation-tooling step).

## 8. Rainbow Islands / Sonic check
- **Sonic:** yes — each HUD element (digit, glyph, credit) is produced directly from live semantic state
  (`0xFF011E`/`0xFF0142`/`0xFF0117` + fixed anchor/spacing) into ordered SAT via `.Lnq_emit_entry`; no PC090OJ
  record identity. Labels are semantic glyph strings + per-state anchors (layout constants, not captured tables).
- **Rainbow Islands:** no persistent PC090OJ-shaped state is required — the only staging is the existing
  `staged_sprite_sat` (final Genesis SAT), committed by the unchanged arcade-owned VBlank DMA.
- Retained semantic state: live score/high-score/credit values + arcade frontend state. Disappears: score-record
  positioning, HUD record range in the scan. No software PC090OJ representation is introduced.

## 9. Expected deletion list
- DELETE: the frontend scan's HUD record-range handling (the Build-0269/0271 skip of 4-45 becomes "HUD not in
  scan at all"); the score-record **positioning producer**'s HUD writes (prove exclusive HUD ownership first).
- KEEP (temporarily): `.Lpc090oj_decode_record`, `.Lnq_frontend_object_scan` core (still services player/D00298/
  5a098); `.Lpc090oj_emit_slot`, `.Lpc090oj_family_apply_record` (used by player/5a098).
- RENAME later: `.Lnq_title_emit_scores` → `native_frontend_hud_emit` (it will own labels too).
- REQUIRES proof: that the positioning producer writes **only** HUD records (else keep it for the others).

## 10. Implementation-ready source/symbol plan
1. In `pc090oj_native_emit_pass`, add a finite `native_frontend_hud_emit` call for all frontend scenes (scene!=1)
   BEFORE the scan, emitting scores + credits + labels; remove the call from inside `.Lnq_frontend_object_scan`.
2. Generalise `.Lnq_title_emit_scores` (+ `.Lnq_title_labels`) into `native_frontend_hud_emit(state)`:
   per-frontend-state label sets `{Y,X,glyph}` (title / throne / ranking / story), selected by scene+stage; the
   score/credit/leading-zero logic is unchanged.
3. Remove the HUD record range (4-45) from the scan entirely (replace the Build-0269 skip with "scan starts after
   the HUD family" for frontend), leaving player/D00298 records.
4. Retire the score-record positioning producer's HUD writes (opcode_replace to inert or drop, after xref proof).
5. Keep gameplay (`.Lnq_project_p1_hud`) and `.Lnq_title` behavior; fold `.Lnq_title` into
   `native_frontend_hud_emit` if it reduces paths.

## 11. Validation plan
- **Genesis-driver MAME (candidate):** for each reachable state (title 0/0000, throne 0/0100, credit via P1-Start,
  ranking/story if reachable by longer attract) — SAT byte-diff vs Build 0271 must be **identical** (labels +
  scores + credits), total-SAT unchanged, no double. Reuse the existing `hud/satdiff.lua` + Start-driver.
- **Original arcade MAME:** capture per-state HUD layouts (label glyph codes + anchors) as ground truth for the
  per-state label sets (reuse `roms/rastan.zip` headless).
- **Static proof:** 0 HUD records scanned; native HUD not called from the scan; scan serviced record set
  enumerated (player/D00298/5a098); no captured sprite table; no record-shaped scratch.
- Regression areas: gameplay HUD (must be untouched), non-HUD frontend sprites (player/D00298), transitions.

## 12. Risks / known unknowns
- **Per-state label positions** for ranking/story (not reached in 90 s attract) — resolve with arcade-MAME
  capture + longer attract driving before converting those states; do not convert a state whose layout is
  unproven (that was the 0267 mistake).
- Whether the **positioning producer** is HUD-exclusive (must prove via xrefs before retiring it).
- **0x5A098** remains until its gameplay state is reached — call it out, don't stub it (rule 13/14).

## 13. Expected PC090OJ state after this unit
Frontend HUD (scores + high score + credits + labels) fully native in one dedicated pass; the object-RAM scanner
services **only** the player block (workram_block_sprites), D00298/D002B0, and 0x5A098 — a materially smaller
legacy renderer, with the score-record positioning producer retired for the HUD.
