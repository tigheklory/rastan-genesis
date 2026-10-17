# HUD / Off-Screen Sprite Suppression — Historical + Current-State Audit (Andy)

**Date:** 2026-10-16 · **Type:** Documentation archaeology + current-source confirmation. **No**
production change, **no** ROM, **no** gameplay/trace/MAME/screenshots. Method: comprehensive content
search across all `docs/design/**/*.md` plus targeted full reads of the relevant reports, then
current `Build 0434`-tree source confirmation. Baseline: current working tree (flag default 2).

Evidence tags: **[SRC]** source-confirmed; **[DOC]** stated in a design report/Makefile; **[OBS]**
user observation (accepted, not reinterpreted); **[INFER]** reasoned, not runtime-verified.

---

## 1. Executive conclusion

- The reduced gameplay HUD is **intentional**, controlled by the build flag
  **`RASTAN_GAMEPLAY_HUD_SPRITES`** (default **2**) which keeps **only the current player's 1UP label
  + 1P score** and suppresses the rest of the gameplay HUD family. **This is hypothesis C** (the
  1UP-only flag + native-replacement scope), **not** an early crash-NOP (A — no evidence) and **not**
  primarily off-screen clipping (B — a real but secondary mechanism). [SRC/DOC]
- **Two separate mechanisms exist, as Tighe recalls:** (1) an **off-screen sprite/viewport clip**
  (Build 0147 constants) and (2) the **1UP-only gameplay HUD flag** (`RASTAN_GAMEPLAY_HUD_SPRITES==2`,
  the gameplay producer `.Lnq_project_p1_hud`). They are independent. [SRC]
- **Attract/frontend** still shows the full 1UP / HIGH SCORE / 2UP / CREDIT because it uses a
  different native producer (`.Lnq_title_emit_scores` / `native_frontend_hud_emit`); **gameplay uses
  `.Lnq_project_p1_hud`** — the split is explicit and documented. [SRC/DOC Build 0271]
- **The 1UP-only gameplay HUD flag MUST remain available** and is the current default; future HUD
  optimization may change *how* the reduced HUD is produced but must not remove the switch or alter
  attract/frontend presentation. [per user requirement]

## 2. Chronological history

| Build | Event | Mechanism / evidence |
|---|---|---|
| **0147** | **Off-screen / viewport clip constants introduced** | `pc090oj_hooks.s:160-191`: `GENESIS_VIEWPORT 0..223 / 0..319`, `PC090OJ_TO_GENESIS_Y_OFFSET=-8`; arcade visible area (raster 8..247) maps to Genesis 0..239, arcade top margin placed **above** the viewport "where its records clip out naturally." [SRC] |
| **0264** | Live native **title** sprite producers | `docs/design/Andy_build0264_live_native_title_sprite_producers.md`; `.Lnq_title_emit_scores/_labels`. [DOC] |
| **0269** | **Complete native frontend HUD replacement** | `docs/design/Andy_build0269_complete_native_frontend_hud_replacement.md` — frontend HUD produced natively. [DOC] |
| **0271** | **Frontend score/credit fully native; 0x3B802 retired; 0x5A098 status RETAINED** | `docs/design/Andy_build0271_complete_frontend_native_hud_status_retirement.md`: scores (0xFF011E), high score (0xFF0142), credit (0xFF0117>0) native via `.Lnq_title_emit_scores`; **"gameplay uses `.Lnq_project_p1_hud`"** (:19); status sprites 30–43 (`0x5A098`) **RETAINED, not reached** (:34). [DOC] |
| **(flag build)** | **`RASTAN_GAMEPLAY_HUD_SPRITES` 1UP-only gameplay mode** | `apps/rastan-direct/Makefile:50-55`; gameplay producer `.Lnq_project_p1_hud` (`pc090oj_hooks.s:2627/2663`). Exact introducing build number **AMBIGUOUS** from docs (see §13); the flag + `.Lnq_project_p1_hud` are present and default **2** today. [SRC; build-number DOC not pinned] |
| **0337/0338** | Diagnostic variants reuse the HUD score path (`_d`/`_s`) | `pc090oj_hooks.s:2633` writes `diag_score_bcd` into the **gameplay** HUD too under `RASTAN_DIAG_SCORE_METRIC` (corrects a prior Andy note that `_s` only touched the frontend HUD). [SRC] |
| **0434** | Current state | 1UP-only gameplay HUD default (==2); attract full HUD; off-screen clip active. [SRC] |

No entries were invented; the flag's introducing build is marked AMBIGUOUS rather than guessed.

## 3. Off-screen sprite suppression history

**Introduced:** Build **0147** (viewport/opaque-clip constants, `pc090oj_hooks.s:160-191`). [SRC]
**Purpose:** align arcade sprites to the Genesis display origin and let arcade records outside the
Genesis viewport (the arcade top/bottom margins, raster outside 8..247 → outside Genesis 0..223)
clip naturally. **Rule:** effective clip rectangle = intersection of arcade visible area (→ Genesis
0..239 after `Y-8`) and the Genesis output viewport (**0..223 Y, 0..319 X**, ends exclusive); Genesis
bounds bind. [SRC] **Stage:** this is a *coordinate/viewport* clip — records whose SAT Y lands outside
0..223 are not visible (LEVEL 5/6: the SAT/plane coordinate places them off-viewport). It does **not**
skip gameplay/mapping/queue work for a produced record; it only makes an off-viewport record
invisible. **Still active: YES** [SRC]. **It is NOT the reason the gameplay bottom HUD is absent** —
the suppressed gameplay HUD elements are never *produced* (see §5), so they never reach this clip.
[INFER]

## 4. 1UP-only gameplay HUD flag history

**Flag/define:** `RASTAN_GAMEPLAY_HUD_SPRITES` (`apps/rastan-direct/Makefile:55`, default **2**). [SRC]
**Actual current values (corrected after Build-0434 hardware test):** **2** = call
`.Lnq_project_p1_hud` and produce only the player-one score group (1UP label + six score digits).
**0 and 1 assemble identical executable gameplay code**: both omit that producer. The earlier
interpretation that **1** preserved a usable old full Genesis HUD representation was based on stale
comments/history and is **rejected**; Tighe's mode-1 hardware test displayed no gameplay HUD. Mode 0
does not select a hidden full-HUD path either. [SRC + USER TEST]
**Implementation:** gameplay finalizer `.Lnq_gameplay` calls `.Lnq_project_p1_hud` only under
`.if RASTAN_GAMEPLAY_HUD_SPRITES == 2` (`pc090oj_hooks.s:2627`, body `:2663`); also guarded at
`:3165/:3310`. [SRC]
**Retained in gameplay:** the **1UP label** + the **current-player (1P) 6-digit score** (from
`0xFF011E`). **Suppressed in gameplay:** HIGH SCORE (label + digits), 2UP (label + digits), and the
rest of the gameplay HUD family (records beyond 28..36). [SRC]
**Original requirement:** the Makefile comment records the intent (player-one score only). The
specific report where Tighe requested it is **AMBIGUOUS** (not isolated in this pass; §13). The
behavior and flag are unambiguous in source. **Still active in Build 0434: YES.** **Must remain
available: YES.** [SRC + user requirement]

## 5. Bottom gameplay HUD disable/suppression history

**Explanation: C (intentional reduced native gameplay HUD) + native-replacement scope — NOT a crash
NOP (A), NOT primarily off-screen clip (B).** [SRC/DOC]
- The gameplay HUD is the 1UP-only `.Lnq_project_p1_hud`; it produces only the 1UP score group. [SRC]
- The arcade bottom/status HUD (status sprites **records 30–43**, old producer **`0x5A098`**) was
  **RETAINED (rule 13), not converted to a native gameplay producer and "not reachable in the 90s
  attract + Start harness"** (Build 0271 §:34). So the bottom/status HUD is simply **not produced**
  by the native gameplay finalizer. [DOC]
- **Hypothesis A (early NOP due to crash): NO EVIDENCE** found in the design tree for a *HUD-specific*
  crash NOP. (Gameplay-entry crashes exist — `Andy_build0309_build0308_gameplay_entry_crash_analysis.md`
  — but are not a documented bottom-HUD disablement.) [DOC absence]
- **Hypothesis B (off-screen clip removes it): secondary at most** — Build 0147 would clip any
  produced record mapping below Genesis line 223, but the gameplay HUD elements aren't produced, so
  the clip is not the cause. [INFER]

## 6. Attract/frontend vs gameplay HUD ownership

**Split point:** `pc090oj_native_emit_pass` branches on `genesistan_current_scene_id`: scene **1
(gameplay)** → `.Lnq_gameplay` (→ `.Lnq_project_p1_hud` under ==2, 1UP-only); scene **0 title /
stage≠0 / 2** → `.Lnq_title` / `.Lnq_frontend_native` → `native_frontend_hud_emit` /
`.Lnq_title_emit_scores`. [SRC]
- **Attract full HUD:** `.Lnq_title_emit_scores` produces player score (`0xFF011E`) **and** high score
  (`0xFF0142`, leading-zero suppressed) and the **CREDIT** block (`0xFF0117`, shown only when >0);
  labels via `.Lnq_title_emit_labels`. That is why 1UP/HIGH SCORE/2UP/CREDIT remain in attract.
  [SRC/DOC 0271] CREDIT is intentionally preserved for the insert-coin/throne frontend states.
- **Frontend and gameplay are separate native producers** — 0271 states plainly "used by the title
  and the frontend scan path; **gameplay uses `.Lnq_project_p1_hud`**." The 1UP-only flag is
  **explicitly gameplay-only**; attract is unaffected by it. [DOC]

## 7. Current Build-0434 implementation

- Flag: `RASTAN_GAMEPLAY_HUD_SPRITES` default **2** (`Makefile:55`), emitted into `out/pc090oj_config.inc`
  (`Makefile:391`). [SRC]
- Gameplay HUD: `.Lnq_project_p1_hud` (`pc090oj_hooks.s:2663`) — invoked only when ==2 (`:2627`).
- Off-screen clip: `pc090oj_hooks.s:160-191` constants (Build 0147), applied in the native
  SAT/coordinate path. [SRC]
- Attract HUD: `.Lnq_title_emit_scores` + `.Lnq_title_emit_labels` + `native_frontend_hud_emit`
  (`pc090oj_hooks.s` frontend region). [SRC]
- Status: 1UP-only flag **STILL ACTIVE**; off-screen clip **STILL ACTIVE**; old arcade frontend HUD
  producers `0x3B802` **REMOVED/native** (0271); `0x5A098` status **RETAINED (dead for gameplay in
  the tested window)**. [SRC/DOC]

## 8. Suppression stage / cost avoided (Q5)

- **HIGH SCORE / 2UP / bottom-status HUD in gameplay: LEVEL 1** — the gameplay producer never
  generates them (and `0x5A098` is not invoked natively in gameplay). **No** mapping/descriptor
  expansion, residency, queue, or SAT work is spent on them. This is the maximum saving. [SRC/INFER]
- **Off-screen viewport clip (Build 0147): LEVEL 5/6** — for records that *are* produced but map
  outside 0..223/0..319, the SAT/plane coordinate places them off-viewport; it does not save
  upstream gameplay/mapping/queue work for those records. [SRC]

## 9. Exact active gameplay HUD elements (Q6)

`.Lnq_project_p1_hud` emits **six `.Lnq_emit_hud_digit` calls** at X = 0x08,0x10,0x18,0x20,0x28,0x30
— the **6 BCD digits of the current-player (1UP) score** read from `0xFF011E` — plus the fixed
**"1UP" label glyph(s)** (`move.w #0xD039` = HUD-white direct identity). [SRC] So the "six BCD digits
+ three fixed glyphs" from the prior Cody audit = **all six digits are the current-player score**
(`0xFF011E`), and the fixed glyphs are the **1UP** label. **No HIGH SCORE (`0xFF0142`) or 2UP digits
are included** in those counts. [SRC]

## 10. Exact currently suppressed gameplay elements

HIGH SCORE label + digits; 2UP label + digits; the rest of the gameplay HUD family (records beyond
28..36); the arcade bottom/status HUD (status records 30–43, old `0x5A098`). CREDIT is a frontend
element (shown in attract when `0xFF0117>0`), not a gameplay element. [SRC/DOC]

## 11. Current build flag(s)

- `RASTAN_GAMEPLAY_HUD_SPRITES` (default **2** = 1UP-only; **0 and 1** = no P1-score projection and
  identical current executable gameplay code). No value currently enables a complete gameplay HUD.
  Other variant flags
  (`RASTAN_DIAG_CPU_BAR`, `RASTAN_DIAG_SCORE_METRIC`, `RASTAN_VBLANK_DISPLAY_OFF`,
  `RASTAN_MODE_RACK_ADVANCE`) are the ROM-variant flags (see `Andy_ROM_variant_audit.md`); `_s`'s
  `diag_score_bcd` overwrite reaches **both** the gameplay (`.Lnq_project_p1_hud`, :2633) and
  frontend HUD paths. [SRC]

## 12. What MUST be preserved in future HUD optimization

- **PRESERVE the 1UP-only gameplay HUD mode** (`RASTAN_GAMEPLAY_HUD_SPRITES==2` + `.Lnq_project_p1_hud`);
  do not remove the switch. It is the current default and is on the critical path to 60 fps.
- **PRESERVE the attract/frontend full HUD** (`.Lnq_title_emit_scores`/`native_frontend_hud_emit`:
  1UP/HIGH SCORE/2UP/CREDIT). Do not let a gameplay-HUD change touch the frontend producers.
- **Do NOT restore suppressed gameplay HUD** (HIGH SCORE/2UP/bottom) unless Tighe requests it; the
  reduced HUD is intentional, not a bug.
- Keep the gameplay vs frontend producer split intact (scene-gated in `pc090oj_native_emit_pass`).
- **Potential performance opportunity from history:** the suppressed gameplay HUD is already saved at
  LEVEL 1 (not produced) — so there is little HUD *suppression* headroom left; the remaining active
  cost is the 6-digit + label reconstruction **every frame** in `.Lnq_project_p1_hud`. A future opt
  could cache/skip the 1UP HUD when the score is unchanged (only re-emit on change), preserving the
  1UP-only behavior while cutting the per-frame rebuild. [INFER — not measured; do not implement here]

## 13. Unresolved ambiguities

- **The exact build number that introduced `RASTAN_GAMEPLAY_HUD_SPRITES` / the 1UP-only mode is
  AMBIGUOUS** — the flag and producer are present in source with the Makefile rationale, but no single
  design report in this pass pins the introducing build or quotes Tighe's original request verbatim.
  Candidate neighborhood is the 0264–0271 native-HUD era, but this is not proven.
- **The gameplay "score above 1UP" vertical-reversal** vs attract layout [OBS] is **not explained by
  any historical doc found**; `.Lnq_project_p1_hud` uses its own Y layout distinct from
  `.Lnq_title_emit_scores`. Documented as a current observation only; not investigated per task.

---

**task = historical HUD suppression audit · docs/design recursive audit = YES (content search across
all + relevant reports read in full) · production modified = NO · ROM built = NO · gameplay driven =
NO · trace created = NO · 1UP-only flag preserve requirement = YES · bottom-HUD mechanism =
intentional 1UP-only flag + native-replacement scope (0x5A098 retained/unreached), NOT crash-NOP,
off-screen clip secondary · off-screen suppression = Build 0147 viewport clip (pc090oj_hooks.s:160-191)
· attract/gameplay distinction = scene-gated separate native producers (.Lnq_title_emit_scores vs
.Lnq_project_p1_hud).**
