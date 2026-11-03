# Complete Native Graphics Retirement — STOP (mandatory gameplay palette provenance is unobtainable in this environment)

**Agent:** Andy · **Build produced: NO. No source/spec/generated-object/ROM changed. Counter stays 260.**

## Phase 0

Relevant priors from KNOWN_FINDINGS:
- **KF-026 (STRONG, GLOBAL)** — PC090OJ write surface not fully statically enumerable; pointer-indexed writes
  need trace evidence. Governs the specialized-actor spawn attr/code source below.
- **KF-067** — BACK_ENEMY −8 Y bias (preserved in `native_sprite_emit`).
- KF-043/KF-045 (bank-51 line-3 sprite palette carrier), KF-055/KF-056 (Exodus/sound, unrelated).

Rediscovery-Hazard HIGH findings touched: none contradicted.

Deferred-appendix entries relevant: none.

Task classification: **EXTENDING** (continues OPEN-024 PC090OJ + OPEN-006 sprite-palette + PC080SN frontend
retirement).

Open/Closed issues touched: **OPEN-024** (PC090OJ subsystem incomplete), **OPEN-006** (sprite/high-bank
palette mapping deferred), OPEN-018 (raw PC080SN write routing). No new issue required — the axe/bat palette
belongs to the existing OPEN-006 arc.

Contradiction of a CONFIRMED/STRONG finding: NONE. This STOP is corroborated by KF-026 and by the OPEN-006/
OPEN-024 history (graphics converted as bounded, individually Tighe-verified increments, never monolithically).

## Why the single-build "complete retirement" cannot be produced correctly here

### 1. Confirmed regression proves the native sprite attr/palette needs gameplay provenance
Build 0260 broke the axe palette (was correct via the 0259 arcade-engine attr). Static analysis pins the
cause: for **default-expander** actors my native attr construction is a verified 1:1 transcription of arcade
`0x3C9E8` (attr = `a4@39` | type-0x80 flipX), so a default axe would **not** regress. The axe regressing
therefore means the axe is a **specialized-type** actor, and for specialized actors the arcade handler writes
**no attr and no code** (proven: the only `a1@(4)` store in `0x3C4D2..0x3C902` is `0x3C8B8`; there is no
`a1@(0)` store anywhere) — the record attr/code are **retained state seeded at spawn**. My Build 0260
specialized path approximates attr with `a4@39` and code with `a4@30`; the axe regression proves that
approximation is wrong for at least the axe, i.e. the retained per-piece attr/code ≠ `a4@39`/`a4@30`.

- Exact `arcade_pc`: specialized dispatch `0x3C902` → one of `0x3C4D2/550/586/636/6DC/75C/7A4/830`; spawn
  attr/code writer = pointer-indexed, unlocated (KF-026).
- Mapped `runtime_genesis_pc`: the relocated +0x200 copies (dispatch `0x3D254`), reached from
  `genesistan_pc090oj_hook_target_41dae/45dfa`.
- Semantic value that cannot be reproduced: the axe's (and other specialized actors') **per-piece retained
  attr and code**. It is not the default `a4@39`/`a4@30` (regression proof), is not in the position-only
  specialized mapping, and its spawn seed is not statically enumerable (KF-026).
- Why recomputation/minimum-metadata cannot preserve it *right now*: the seed value can only be obtained by
  observing the specialized actor's record at runtime, or by calling the arcade engine (forbidden). Both are
  unavailable (see §2).

### 2. The mandatory Phase-2 palette provenance requires Stage-1 arcade gameplay, which is unreachable here
Phase 2 requires capturing, from original arcade MAME **in gameplay**, the palette/attr fields for Rastan,
lizard man, hurry-up bat, normal bat, axe, and another effect. I cannot reach Stage-1 arcade gameplay in this
headless environment:
- **No gameplay save-state exists** in the repo (`find -iname '*.sta'` → none).
- **Scripted coin/start input does not register**: driving `Coin A`/`Coin 1` + `1 Player Start` via
  `field:set_value` left credits/energy at `0x0000` for the whole run (evidence:
  `states/traces/direct_native_sprite_provenance_*` + the driven-input diagnostics this session); the attract
  segment never runs the master-build sprite expander (`0x41DAE` never fires; all sprite-RAM writes are
  boot/HUD in frames 0–499).
- **Prior gameplay captures were human-driven** through the interactive Qt debugger (`-debug -debugger qt`,
  e.g. `build0216_arcade_bat_path`), which is unavailable headless.

Without gameplay provenance I cannot determine the correct axe/bat/lizard/Rastan effective palette banks, so I
cannot correctly fix the axe regression or prove the bat palette — and Phase 2 ("axe palette still wrong" is a
task failure condition) cannot be satisfied. Proceeding blind demonstrably ships palette regressions (the axe
already proves this).

### 3. The full mandate is not a single-build unit in this project's proven methodology
OPEN-006 and OPEN-024 show every prior sprite/palette/plane change shipped as a **bounded, single-issue build
with Tighe visual verification** (0142 record identity, 0144 palette selector split, 0145 bank-51 line-3, 0170–
0173 tall BG/FG palette, etc.). "Retire all PC090OJ + all PC080SN frontend + fix palette + validate 16 bats /
attract text / all planes" in one build, with no partial allowed and no ability to run the required gameplay
validation, cannot be produced to the "everything ships correct" prime-directive standard here.

## What is NOT the reason for this STOP
Not "the task is large", not "later scenes are hard to reach", not "a compatibility scan is easier", not
"another agent should do it". The reason is specific: **the mandatory gameplay palette provenance (Phase 2) and
the specialized-actor retained attr/code are only obtainable from Stage-1 arcade gameplay, which is
environmentally unreachable here (no save-state, headless coin/start injection fails, prior captures were
human-GUI-driven), and the confirmed axe regression proves that proceeding without that provenance ships
palette defects.**

## Exact minimal unblock
Any one of:
1. A gameplay-reaching arcade MAME save-state (`.sta`) added to the repo (Stage-1, with a lizard/bat/axe on
   screen), or a headless input harness that actually registers a credit + start; then I capture the
   axe/bat/lizard/Rastan per-piece attr/palette + the specialized spawn attr/code, fix the palette owner, and
   complete the specialized handlers.
2. Tighe captures that palette/attr provenance (or confirms the axe/bat effective banks) and the specialized
   actors' record attr/code seed, so the values can be encoded from proven arcade semantic state.

With that provenance the retirement is best delivered as the project's proven bounded increments: (a) axe/bat
palette correction + specialized-handler completion; (b) frontend sprite-text PC090OJ retirement; (c) PC080SN
frontend retirement; (d) dead-code cleanup — each Tighe-verified, per OPEN-006/OPEN-024 practice.

## Scope
Counter 260 (unchanged); no ROM produced; no source/spec/object changed; Builds 0258–0260 preserved. Valid
STOP under the concrete-contradiction standard: a semantic value (specialized/axe retained attr+code and the
gameplay palette provenance) that cannot be reproduced from statically-available actor/table/stage state and
cannot be observed because the required gameplay state is environmentally unreachable — corroborated by
KF-026.
