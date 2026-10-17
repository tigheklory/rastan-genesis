# Full Gameplay HUD — Genesis-Native Restoration Contract (Andy)

**Date:** 2026-10-16 · **Type:** READ-ONLY historical/static analysis + restoration specification.
**No** production change, ROM, gameplay, or new trace. Phase D/E not started. Allowed outputs: this
report + an append-only `AGENTS_LOG` entry. Builds on `Andy_hud_suppression_history_audit.md` and
`Cody_full_hud_parallel_build_variant.md`.

Evidence tags: **[SRC]** current source · **[DOC]** design report/log · **[INFER]** reasoned ·
**[CONFIRM]** field Cody must verify before implementing (not fabricated).

---

## 1. Executive conclusion

`RASTAN_GAMEPLAY_HUD_SPRITES` originally meant **mode 1 = full gameplay HUD** (default), mode 0 =
suppressed, with mode 2 added later as the reduced 1UP/current-score HUD. Build **0250** migrated
gameplay presentation to native semantic lanes but carried forward **only the mode-2 (1UP+P1 score)
semantics**; the full-HUD path (HIGH SCORE / 2UP via `0x3B802`, and the status family) lost its
renderer when the PC090OJ gameplay HUD producers were retired, and **no native full-HUD gameplay
producer replaced it**. Today modes 0 and 1 assemble **identical bytes** (no gameplay HUD) — the
`_full_hud` artifact is correctly REJECTED. [DOC Cody full-HUD doc; SRC]

**To make mode 1 truthful, Cody adds a native gameplay HUD producer that emits, under `.if
RASTAN_GAMEPLAY_HUD_SPRITES == 1`, the mode-2 1UP/P1 group (unchanged) PLUS HIGH SCORE and 2UP score
groups into `native_queue_hud`, and ensures the already-native energy/status lane
(`genesistan_pc090oj_hook_status_sprite_5a098`) is included.** No PC090OJ record, scanner, or
object-RAM intermediary. Mode 2 stays byte-for-byte as accepted.

## 2. Original HUD flag contract [DOC]

Per AGENTS_LOG (Build 0208→0210, 0230/0231): Makefile default was `RASTAN_GAMEPLAY_HUD_SPRITES ?= 1`.
- **mode 0** — full gameplay-HUD suppression (records 0..45) for testing/perf comparison.
- **mode 1** — full/normal gameplay HUD.
- **mode 2** — later added: retain only 1UP + current-player score.

The flag survived; mode-1's *implementation* did not survive the native migration.

## 3. Last working mode-1 build

**Build 0249** [DOC `Andy_build0249_native_pc090oj_sat_boundary.md` §6]: "HUD mode 2 is handled via
`hook_score_digit_3b802` + `hook_status_sprite_5a098` + a suppression counter (`hud_suppressed_count`
=384) — preserved." At 0249 the gameplay HUD score/status still flowed through the PC090OJ **mirror**
hooks `hook_score_digit_3b802` (`0x03B802`) and `hook_status_sprite_5a098` (`0x05A098`) (table rows,
"NO — mirror"), so mode 1 (full) still rendered via those producers. **Evidence:** the 0249 boundary
report + the retained mirror hooks. [DOC] (Exact commit not pinned; 0249 is the documented last
PC090OJ-gameplay-HUD build before the 0250 native migration.)

## 4. Exact contract-breaking native migration change

**Build 0250** migrated gameplay presentation to **native semantic lanes** [DOC AGENTS_LOG]. The
break: `0x3B802` (score/1UP/HIGH SCORE/credit producer) and the PC090OJ gameplay HUD record stream
were retired (fully by Build 0271/0272, "0x3B802 fully retired"), and the native gameplay finalizer
`.Lnq_gameplay` was given **only** `.Lnq_project_p1_hud` (mode-2 1UP+P1 score). HIGH SCORE and 2UP
got a native **frontend** owner (`.Lnq_title_emit_scores`) but **no native gameplay owner**; the
status family got a native producer (`0x5A098` replacement) but it is not wired into the HUD-flag
contract. **Before:** gameplay HUD via `0x3B802`+`0x5A098` mirrors (mode 1 full). **After (0250→0434):**
gameplay HUD via `.Lnq_project_p1_hud` only (mode 2); modes 0/1 emit nothing. [SRC/DOC]
**Why mode 1 stopped working:** removing the PC090OJ gameplay renderer was architecturally correct,
but the mode-1 HUD *semantics* (HIGH SCORE, 2UP) were never migrated to a native gameplay producer —
retiring the carrier ≠ preserving the flag contract.

## 5. Complete historical gameplay HUD inventory [DOC/INFER]

TOP / SCORE family: (a) 1UP label; (b) current-player (P1) score; (c) HIGH SCORE label; (d)
high-score digits; (e) 2UP label; (f) 2UP digits.
BOTTOM / STATUS family: (g) energy/health bar; (h) any additional status (low-energy blink is part of
(g)). **Note:** the arcade Rastan gameplay HUD is primarily the top score row + an energy/health
indicator; "lives / stage / item icons" as distinct gameplay HUD sprites are **[CONFIRM]** — do not
assume they exist as gameplay HUD until proven from the 0249 producer / arcade source. Record ranges
(0..45; status 30..43) are historical evidence only, **not** part of the native target.

## 6. Top-score HUD semantics

| Component | Authoritative source | Current native owner | Mode | Notes |
|---|---|---|---|---|
| 1UP label | fixed | `.Lnq_project_p1_hud` glyph `0xD039` [SRC] | 1+2 | mode-2 as-is |
| P1 score (6 digits) | WRAM `0x00FF011E` BCD [SRC :2325] | `.Lnq_project_p1_hud` (6 `.Lnq_emit_hud_digit`, X=0x08..0x30) [SRC] | 1+2 | mode-2 as-is; leading-zero per frontend rule |
| HIGH SCORE label | fixed | **none in gameplay** (frontend `.Lnq_title_emit_labels`) | **1 only** | NEW native gameplay emit |
| HIGH SCORE digits | WRAM `0x00FF0142` BCD [SRC :2325] | **none in gameplay** (frontend `.Lnq_title_emit_scores`) | **1 only** | NEW; reuse digit emitter |
| 2UP label | fixed | **none in gameplay** (frontend 2UP row :2465) | **1 only** | NEW |
| 2UP digits | active P2: `A5+0x011C..0x011E`; inactive saved P2: `A5+0x00DC..0x00DE` (packed BCD, MSB at the highest address) | **none in gameplay** | **1 only** | NEW native gameplay emit |

Positioning/palette/leading-zero: **reuse the frontend `.Lnq_title_emit_scores` layout as the
semantic reference**, but mode-1 coordinates are the GAMEPLAY HUD positions — **[CONFIRM]** gameplay
X/Y from the 0249 full-HUD producer / arcade gameplay HUD layout (do not silently adopt frontend
coordinates if gameplay differs).

## 7. Bottom/status HUD semantics

The **energy/status producer already exists natively**:
`genesistan_pc090oj_hook_status_sprite_5a098` (`pc090oj_hooks.s:1961+`) [SRC] — a **direct-native**
gameplay energy producer (NOT PC090OJ-shaped). It reads **current energy at `A5+0x013A`** (high byte
= units), publishes **6 semantic energy cells** (`moveq #6,%d6` :2049), with low-energy blink
(:2030/2102) and the inlined `0x5A244` transition helper (:2118). [SRC] This is the recovered status
semantics — **no object-RAM transport**. For mode 1 the contract is: ensure this lane is **produced
and included** when its retained arcade caller (`0x5A098`) is reached in gameplay. **[CONFIRM]**
whether that caller is currently reached in normal gameplay (Cody's doc says "when its retained
arcade caller reaches it" — confirm reachability, else mode 1 must invoke the native producer
directly under the flag). Any lives/stage/item HUD beyond energy is **[CONFIRM]** against the 0249
producer before claiming it as a gameplay HUD element.

## 8. Historical producer ownership [DOC]

- `0x03B802` — frontend+gameplay score/1UP/HIGH SCORE/credit (PC090OJ mirror). **RETIRED** (0271).
- `0x05A098` — gameplay energy/status (PC090OJ mirror). **Replaced by a native direct producer**
  (`genesistan_pc090oj_hook_status_sprite_5a098`); the 8/6-piece energy lane is the native equivalent.
- Suppression counter `hud_suppressed_count` (0249) — historical mode-2 suppression bookkeeping.
These are **semantic evidence only**; do not restore the mirrors.

## 9. Current Build-0434 surviving semantics/helpers (per-component classification)

| Component | Build-0434 status |
|---|---|
| 1UP label + P1 score | **ALREADY NATIVE AND REUSABLE** (`.Lnq_project_p1_hud`) |
| HIGH SCORE digits/label | **NATIVE FRONTEND EQUIVALENT EXISTS** (`.Lnq_title_emit_scores`/`_labels`); **SEMANTIC SOURCE STILL EXISTS** (`0xFF0142`); **NEEDS NEW NATIVE GAMEPLAY PRODUCER** |
| 2UP digits/label | **NATIVE FRONTEND EQUIVALENT EXISTS** (frontend 2UP row); source **[CONFIRM]**; **NEEDS NEW NATIVE GAMEPLAY PRODUCER** |
| Energy/status | **ALREADY NATIVE** (`...hook_status_sprite_5a098`, A5+0x013A, 6 cells); reachability **[CONFIRM]** |
| Low-level digit/glyph emit | **ALREADY NATIVE AND REUSABLE** (`.Lnq_emit_hud_digit`, `native_sprite_emit_fast`, `native_sprite_fast_context`, glyph id `0xD039`) |
| Old PC090OJ HUD builders / record scanner | **HISTORICAL PRODUCER RETIRED** (0271/0272) — evidence only |

## 10. Missing native gameplay producers

Exactly two new native gameplay emits (mode 1 only): **HIGH SCORE group** (label + 6 digits from
`0xFF0142`) and **2UP group** (label + digits from the P2 BCD **[CONFIRM]**). Plus **wiring** the
existing native energy lane into the mode-1 HUD if its arcade caller is not already reached. No other
new producer is required by proven evidence.

## 11. Native Genesis restoration architecture

```
arcade HUD state (0xFF011E P1, 0xFF0142 HIGH, P2 BCD, A5+0x013A energy)
  -> native gameplay HUD producer  (.Lnq_project_p1_hud extended, under the flag)
  -> native_queue_hud  (score/label groups)  +  native energy lane (0x5A098 native producer)
  -> existing native HUD/SAT finalization (.Lnq_emit_lane / staged_sprite_sat)
  -> VDP
```
No PC090OJ object-RAM presentation intermediary, no gameplay legacy scanner, no chip-address writes,
no routing gameplay scene 1 through `native_frontend_hud_emit`. The scene split stays:
`pc090oj_native_emit_pass` scene 1 → `.Lnq_gameplay` (gameplay-owned); scene 0/2 → frontend.

## 12. Mode-1 complete-HUD contract

Under `.if RASTAN_GAMEPLAY_HUD_SPRITES == 1`, the gameplay HUD emits, into `native_queue_hud` (score)
and the native energy lane (status): **1UP+P1 score (identical to mode 2) + HIGH SCORE label+digits +
2UP label+digits + energy/status**. Positions/palette/ordering per the gameplay HUD layout
(**[CONFIRM]** coordinates from the 0249 producer; frontend layout is the semantic reference, not
necessarily the exact gameplay coordinates). Visibility rules: HIGH SCORE always shown in gameplay
(arcade behavior **[CONFIRM]**); 2UP shown per arcade 2-player state **[CONFIRM]**; energy per
`A5+0x013A`.

## 13. Mode-2 preservation contract (must NOT change)

Mode 2 (`== 2`, default) stays byte-for-byte: `.Lnq_project_p1_hud` emits the **six current-player
score digits** (X=0x08,0x10,0x18,0x20,0x28,0x30 from `0xFF011E`) + the **1UP label glyph `0xD039`**,
with the **current placement, palette (bank-0x36 carrier / mode-0 palette routing), leading-zero
behavior, and ordering**. [SRC] **Do NOT fix the known "score-above-1UP" vertical-layout issue during
restoration** — that is a separate presentation task. Mode 1 must be a **superset** that leaves the
mode-2 1UP/P1 output unchanged.

## 14. Shared native primitives

Both modes share: `.Lnq_emit_hud_digit` (one BCD digit → HUD glyph), the BCD unpack loop in
`.Lnq_project_p1_hud`, `native_sprite_emit_fast` / `native_sprite_fast_context`, and the fixed glyph
identity (`0xD039` HUD-white). Mode 1 = mode-2 emits + additional HIGH SCORE/2UP digit groups via the
**same** `.Lnq_emit_hud_digit`, + the native energy lane. **Do NOT build a generalized HUD
interpreter** merely to share code; keep small purpose-built emits. Flag selection must be
compile-time (`.if`), so one mode's configuration cannot leak into the other.

## 15. Permanent six-ROM build-family contract

After implementation the automatic family is: `..._NNNN.bin` (default **mode 2**), `_d`, `_s`, `_do`,
`_c`, and **`_full_hud.bin` = `RASTAN_GAMEPLAY_HUD_SPRITES=1`** (complete native gameplay HUD). The
Makefile infra for the sixth variant already exists [DOC Cody full-HUD doc] — **do not modify it in
this task**. The implementation condition that makes `_full_hud` truthful = the §10 new native
producers assembled under `.if == 1`.

## 16. Static verification matrix

- **Mode 1 (new), exhaustive finite-domain where practical:** for all BCD digit values 0–9 ×
  positions, the HIGH SCORE and 2UP digit glyphs/positions match the authoritative source
  (`0xFF0142`, P2 BCD) and the gameplay layout; leading-zero rule matches; labels present; energy
  cells 0..max map to the correct glyph/blink from `A5+0x013A`; SAT order/priority stable.
- **Mode 2 (regression):** `.Lnq_project_p1_hud` output (digits, 1UP glyph, X positions, palette,
  leading-zero, lane/order) is **byte-identical** to accepted 0434 — a diff of the mode-2 native_queue_hud
  build must be unchanged.
- **Mode isolation:** `.if`-selected; prove the mode-1 additions are entirely absent from the mode-2
  assembled bytes (as today modes 0/1 are identical, mode-2 must remain the sole HUD emitter at ==2).
- **No legacy dependency:** verify no `0x3B802`/object-RAM/scanner path is reintroduced.

## 17. Exact Cody implementation checklist

**COMPONENT: P1 score + 1UP** — SOURCE `0xFF011E` / fixed glyph · CURRENT NATIVE `.Lnq_project_p1_hud`
· NEW CODE: none (reused) · LANE `native_queue_hud` · MODE 1+2 · LEGACY DEP: NONE.

**COMPONENT: HIGH SCORE digits** — SOURCE `0xFF0142` BCD · CURRENT REUSABLE: `.Lnq_emit_hud_digit`,
frontend `.Lnq_title_emit_scores` as layout reference · NEW CODE: gameplay HIGH SCORE digit group
(6 digits) emitted under `.if == 1` · LANE `native_queue_hud` · MODE 1 only · LEGACY DEP: NONE.

**COMPONENT: HIGH SCORE label** — SOURCE fixed glyphs · CURRENT REUSABLE: frontend label emit ·
NEW CODE: gameplay HIGH SCORE label emit (mode 1) · LANE `native_queue_hud` · MODE 1 · LEGACY: NONE.

**COMPONENT: 2UP digits** — SOURCE P2 BCD **[CONFIRM address]** · CURRENT REUSABLE `.Lnq_emit_hud_digit`
· NEW CODE: gameplay 2UP digit group (mode 1) · LANE `native_queue_hud` · MODE 1 · LEGACY: NONE.

**COMPONENT: 2UP label** — SOURCE fixed · NEW CODE: gameplay 2UP label (mode 1) · LANE `native_queue_hud`
· MODE 1 · LEGACY: NONE.

**COMPONENT: energy/status** — SOURCE `A5+0x013A` · CURRENT NATIVE
`genesistan_pc090oj_hook_status_sprite_5a098` (6 cells, blink) · NEW CODE: **wire/confirm** the lane
is produced in gameplay (direct invoke under the flag if its arcade caller is not reached) · LANE
native energy/status lane · MODE 1 (and already flag-independent) · LEGACY: NONE.

Each row: no PC090OJ record, no scanner, no object-RAM. The checklist is sufficient for Cody to
implement without repeating the archaeology, except the three **[CONFIRM]** items (§18).

## 18. Build-0435 static resolution of the former [CONFIRM] items

1. **P2 score source:** original `0x3B802` uses the active packed-BCD score at
   `A5+0x011C..0x011E` for either selected player.  The player swap routines preserve inactive P1 at
   `A5+0x009C..0x009E` and inactive P2 at `A5+0x00DC..0x00DE`.  `A5+0x002A` selects which player is
   active.  Both columns remain present; the selected column is refreshed from the active bank.
2. **Gameplay geometry:** original template `0x3B950` and the digit records prove HIGH label tuples
   `(Y,code,X)=(0,3B,88),(0,3A,78),(0,3C,98),(0,3D,A8),(8,3E,B8)`, HIGH digits at
   `Y=0x10, X=0x80..0xA8`; 2UP label tuples `(0x10,39,0x120),(0,49,0x108),
   (0,47,0x118)`, and 2UP digits at `Y=0x10, X=0xE8..0x110`.
3. **Energy reachability:** retained caller original `0x051054` (current mapped runtime
   `0x051254`) reaches `genesistan_pc090oj_hook_status_sprite_5a098` from the normal gameplay main
   loop; the existing direct-native producer remains the owner.
4. **Other bottom/status HUD:** none proven.  The exact old record families resolve to the top score
   family and the `0x5A098` energy/status family; lives, round/stage, item, and weapon icons are not
   additional gameplay-HUD sprite producers in this contract.

---

**No production source/Makefile/counter/ROM/remap/generated-table modified. No Build 0435. Allowed
outputs only: this report + AGENTS_LOG.**
