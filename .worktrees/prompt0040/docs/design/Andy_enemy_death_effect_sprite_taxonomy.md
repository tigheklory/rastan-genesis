# Enemy Death Effect / Drop Sprite Taxonomy (Andy, baseline Build 0426)

**Date:** 2026-10-14 · **Type:** STATIC ANALYSIS ONLY. No production source, no ROM, no build label,
no Phase D/E, no player-path work (Cody owns that). Files changed: this file, `AGENTS_LOG.md`.
Authority: original arcade `build/regions/maincpu.bin` + `build/maincpu.disasm.txt` + the H7/H8
decompilation reports; current native paths in `pc090oj_hooks.s` / `verify_pc090oj_*`.

## Taxonomy table

| Category | User description | Arcade semantic identity | Base / selectors | Pieces | Current Genesis path | Item-drop relation | Optimization potential | Confidence |
|---|---|---|---|---|---|---|---|---|
| **A — bat_death_pop** | tiny ~8×8 pop (small/large bat) | **UNRESOLVED** effect identity. Bats' death effect is NOT proven to be the 0x0275 burst; likely a `rec_type 7` path that **skips** the state-0x0F component (H7: `0x447F0` runs `0x448B2` *"unless rec_type 7"*) → a small/own-frame death rather than the common explosion | bat flight frames are native (small_bat `0x0268`/`0xB9-0xBB` 1 piece; large_bat `0x03F6`/`0xB6-0xB8` 4/2/4) — the distinct *death* effect base/selector is **not** isolated | small (bat frames 1–4 pieces; death-pop effect UNPROVEN) | bat flight = native direct path; **death-pop effect path UNRESOLVED** | NONE (no death-drop; see below) | LOW–MEDIUM (effect is already small; prove identity first) | **PARTIAL** |
| **B — common_enemy_death_explosion** | larger generic death explosion, feels heavy; "then item drop" | **PROVEN: the state-0x0F impact/death-component animation.** Contact/death `0x42E38` → `0x447F0` (marks `+0x3D=1`) → `0x448B2` sets actor `+0x05=0x0F` (state 0x0F, handler `0x40CCC`), `+0x08=0xFF`, `+0x09=1`, **sfx 0x10**; the death-component runs in the `0x44804` stepper (rec_types 8/9/11), completes at `0x44862/74/E4`, score `0x3B726` (`+0x2C`), retire `0x4092E`. The generated **"burst" `0x0275`, state `0x0F`, compositor 0, bank `0x30`, selectors `0x9E/0x9F/0xA0` IS this effect.** | base **`0x0275`**, selectors **`0x9E/0x9F/0xA0`**, compositor 0, bank `0x30` | **8 / 9 / 10** (growing; frame records `0x03E732`/`0x03E753`/`0x03E778`) | **GENESIS-NATIVE DIRECT** — compact 0426 Level-B frame path (`verify_pc090oj_direct_dispatch.py:16`, `verify_pc090oj_frame_table.py:44,51-52`) | **PROVEN ABSENT** (see §Item-drop) | **MEDIUM** (already compact-native; residual per-piece flags + piece-count×instance scaling) | **HIGH** (effect identity); item-drop premise corrected |
| **C — blood_fountain_death** | blood fountain / spray (flying demon, bosses), distinct from B | **PARTIAL.** Separate death path from B: boss defeat `0x469E8` / `0x46AAC` (rounds 5/6) is a distinct handler (H7 §D). The flying-demon (usage bank `0x35`) death effect and the specific blood-fountain effect **base/selector/graphics identity are NOT isolated**. | **UNRESOLVED** (flying_demon art is bank 0x35, but the fountain *effect* base is not proven) | UNKNOWN | **not in the current R1/P1 proven native set** (burst/lizardman/bats only); likely fallback/unconverted | NONE (no death-drop) | UNKNOWN (prove identity first) | **UNRESOLVED** |

---

## Per-category detail

### A — bat_death_pop (PARTIAL)
Arcade semantic owner: not proven to be a separate component. The strongest static lead is H7's
`0x447F0` → *"(unless rec_type 7) runs `0x448B2`"*: actors of `rec_type 7` **skip** the state-0x0F
explosion component. If bats are `rec_type 7` (or otherwise skip `0x448B2`), their death is a
small/own-frame effect, not the 0x0275 burst — which matches Tighe's "tiny pop, visibly smaller than
the common explosion." **Missing evidence:** the bats' `rec_type` and their death-state handler /
effect base. The bat *flight* frames are native; the death-pop *effect* is UNRESOLVED. Do not collapse
A into B on visual size alone.

### B — common_enemy_death_explosion (HIGH / PROVEN)
This is the authoritative result of the whole audit. The generated **"burst" (`0x0275`, state `0x0F`,
compositor 0, bank `0x30`, selectors `0x9E/0x9F/0xA0`, ~8/9/10 pieces)** is the **generic
impact/death-component animation** set by `0x448B2` for ordinary enemies (lizardman, four-armed,
valkyrie, chimera — the `rec_type 8/9/11` component path). Creation/transition path:
`0x42E38` (damage/contact move + collision probe) → solid-bit → `0x447F0` (impact, `+0x3D=1`) →
`0x448B2` (**state 0x0F**, sfx 0x10) → `0x44804` death-component stepper → completion
`0x44862/74/E4` → score `0x3B726` → retire `0x4092E`. It is **already on the compact native path**
(no PC090OJ emulation). The "feels heavy / slowdown" is **piece-count (8–10) × potentially several
simultaneous death components**, each going through the per-piece native emit (residency + SAT), not a
generalized interpreter.

### C — blood_fountain_death (UNRESOLVED)
Distinct from B per Tighe and per H7 (boss defeat `0x469E8`/`0x46AAC` is a separate handler). The
specific blood-fountain effect graphics identity (base/selector/compositor) for the flying demon and
bosses is **not statically isolated** in the evidence available. Marked UNRESOLVED, not merged into B.
**Missing evidence:** the flying-demon/boss death-effect spawn and its frame base/selectors.

---

## Item-drop connection for Category B — PROVEN ABSENT (corrects the task premise)

The task describes B as "explosion … then item-drop animation." **H7 §E and H8 prove Rastan does NOT
drop items on enemy death.** H7: *"Enemy death awards score and spawns explosion/impact components
(state 0x0F), then retires — it does not allocate a drop/item … There is no death→drop RNG in the
reachable code."* The **only** proven pickup-placement mechanism is **H6 field markers / schedule**:
letter markers materialize via `0x41180`/`0x41362` (e.g. state 0x20 torch/light) and the field
schedule `0x4A104` (checkpoints A/B/C). So the "explosion → item" the player sees is: the state-0x0F
death explosion plays, and any visible item nearby was **placed by the scene marker/schedule**, not
dropped by the dying enemy. **Status: PROVEN that no death→drop exists in reachable code** (H7
reachability trace); H8 keeps the enemy-hurtbox→dying *initiation* OPEN, but found no drop creator /
drop table either and fabricated none. Do not build or assume a death-drop system.

---

## Current architecture classification

- **A: gameplay PC090OJ emulation involved: NO** (bat flight is native; death-pop effect route
  UNRESOLVED but no emulation).
- **B: gameplay PC090OJ emulation involved: NO** — the 0x0275 explosion is the compact native
  direct/Level-B frame path (generated records, `(code,bank)→vi`, residency, native SAT). Normal
  gameplay PC090OJ object-RAM emulation is retired (KF-089).
- **C: gameplay PC090OJ emulation involved: NO** (effect route UNRESOLVED, but no emulation; likely on
  the UNRESOLVED fallback or not yet converted).
- Attract-mode-only legacy: the frontend/object-RAM scan path is scene-gated and retired for gameplay
  (`.Lnq_frontend_object_scan` removed; frontend native). Not relevant to A/B/C gameplay death
  effects; kept separate, not investigated further.

## Category-B optimization readiness (no implementation)

B is **already on the compact native path**, so this is NOT a "retire a generalized interpreter"
opportunity like the old sprite work. The remaining per-piece operations in the generic frame loop
that *could* be baked further offline: conditional **Y-adjust flag** (`btst #2 9(%a0)`), per-piece
**attribute override** (`btst #6 0x27(%a4)`), code/orientation handling, and the per-piece
**residency resolve + SAT emit**. The dominant cost, however, is **piece count (8–10) × number of
simultaneous death components**, which is inherent effect density, not translation overhead.
**Expected payoff: MEDIUM** (bake per-piece flags / batch the emit), not HIGH; do not invent cycle
savings — the per-component/per-piece cost has not been separately measured for this effect.

## Terminology cleanup (recommended future renames — do NOT rename production symbols now)

- A → **`bat_death_pop`** (effect identity still to be proven).
- B → **`common_enemy_death_explosion`** (the current generated **"burst" `0x0275`/state-0x0F** symbol
  should be renamed to `death_explosion_state0f` or `common_enemy_death_explosion` — the generic name
  "burst" is misleading and is **not** the blood fountain).
- C → **`blood_fountain_death`** (boss/flying-demon; identity to be proven).
Three distinct concepts, three distinct names; retire the ambiguous generic "burst" as semantic truth.

## Stop conditions honored

- A (bat_death_pop): **UNRESOLVED/PARTIAL** — missing the bats' `rec_type` + death-state effect base.
- C (blood_fountain_death): **UNRESOLVED** — missing the flying-demon/boss death-effect spawn + frame
  base/selectors.
- Not collapsed into B; visual similarity not substituted for code proof.

---

**task = enemy death-effect sprite taxonomy · baseline = accepted 0426 · production modified = NO ·
ROM built = NO · player task touched = NO · Phase D started = NO · Phase E started = NO.**
