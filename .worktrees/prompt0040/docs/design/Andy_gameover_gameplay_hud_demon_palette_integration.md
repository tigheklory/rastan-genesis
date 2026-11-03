# Andy — GAME OVER + Gameplay HUD + Demon Palette Integration

**Date:** 2026-10-20 · **Type:** Palette Composer / registry / generated-policy / static runtime-consumer
audit. **No** ROM build, **no** MAME, **no** trace, **no** build-number consumed, **no** gameplay/
tilemap/runtime-emitter change; Build 0458 behavior untouched; Phase D/E not started. Authority:
current repository files + Cody's provenance (`docs/design/Cody_gameover_1up_palette_provenance.md`,
read in full). Tighe's assignments are preserved, never reset.

---

## BUILD 0458

- Accepted by Tighe: **YES** (real Sega Genesis hardware; attract Plane-B Segment-0 row/ring fixed;
  the rejected Build-0457 prolonged black-screen regression is gone).
- Acceptance based on normal real-hardware behavior: **YES**.
- Rope `_invincible` benchmark: **798 / 798 / 798**, **13,317.147 ms**, deterministic **YES**.
- Rope benchmark used as visual acceptance: **NO** (performance evidence only; the ring fix was
  accepted by Tighe's normal behavioral verification, using the normal ROM).
- `accepted/build-0458`: **CREATED → `e4545426`** ("Fix attract Plane-B ring origin handoff", the
  Cody-reported ROM-producing source), mirroring the `accepted/build-0455`/`0456` convention of
  pointing at the content/source commit. Verification: base SHA-256
  `b8e6784dc0f2eb0c2cf9c9021d9cb53204d89731a759213a05646c733a386699` and `_invincible`
  `750e9611a2aa6bd308f406b8b46ff99080a1e0a51ae7a53d79ed8b131cc3ab2f` **both match** the preserved
  `dist/` artifacts exactly; gate ledger records 0458 `canonical=PASS entry=PASS epoch=PASS`. Accepted
  source history was not amended or rewritten.

---

## GAME OVER

- Semantic family: **PC090OJ_ATTRACT_GAMEOVER_CODES_0037_0038_003F_0044_BANK_30**
- Editor entry: **ADDED** (`tools/graphics_editor/server.py` build_usages → `object:attract.game_over`).
- Registry entry: **ADDED** — `PAL-PC090OJ-ATTRACT-GAMEOVER-001` in `specs/palette_decisions.json`.
- Arcade patterns: `0x37, 0x38, 0x3F..0x44`. Arcade bank: `0x30`. Arcade palette source: `0x4FE62`
  (R1 bank-0 round-row `0x3BA88[0]=11` → `0x4FD02+11*0x20`; confirmed: `_arcade_round_palette(1,0)`
  resolves to exactly this pool entry).
- Previous semantic owner: `usage:burst:bank0x30` (accidental shared-bank result).
- Previous palette index: n/a (no GAME OVER index authored; inherited burst's bank entry).
- Previous Genesis palette line: effectively burst's line 0 (shared-bank LUT accident).
- New GAME OVER palette decision: its own object (`object:attract.game_over`), independently
  authorable; color ownership flows through its per-object `index_map` (reindex generator), not the
  shared bank-0x30 line LUT. ONE family only (flash is visibility/Y, not a palette change) — no second
  "hidden" family created.
- Generated palette index: pending Tighe authoring in the Composer (entry now exists and is editable).
- Generated palette line: see architectural note — the bank-0x30 LINE LUT cannot separate it from
  burst/HUD yet; independent LINE requires a generator key change (Cody).
- Still inherits burst: **NO** (own object_id/map_key; verifier confirms).
- Hard-coded runtime color: **NO**.

---

## GAMEPLAY P1 / 1UP

- Semantic family: **PC090OJ_HUD_P1_LABEL_0039_0046_0048_BANK_30**
- Editor entry: **ADDED** (`object:hud.p1_label`). Registry: `PAL-PC090OJ-HUD-P1-LABEL-001`.
- Pattern codes: `0x39, 0x46, 0x48`. Arcade routines `0x03B8B0/0x03B930/0x03B802`; sources
  `0x1C80..0x1CFF / 0x2300..0x237F / 0x2400..0x247F`. Effective bank `0x30`.
- Expected semantic appearance: **PURE WHITE** (recorded in the registry decision).
- Semantic decision: owned by the palette-decision/index model (no hard-coded line / no tile-slot
  special-case). Pure white is reachable by mapping the opaque label indices to a white CRAM entry
  via `index_map`.
- Generated palette index / line: pending Composer authoring; LINE subject to the bank-0x30
  architectural note below.

---

## GAMEPLAY SCORE DIGITS

- Semantic family: **PC090OJ_HUD_SCORE_DIGITS_002A_0033_BANK_30**
- Editor entry: **ADDED** (`object:hud.score_digits`). Registry: `PAL-PC090OJ-HUD-SCORE-DIGITS-001`.
- Pattern codes: `0x2A..0x33`. Arcade routine `0x03B802` (six BCD digits, reads `A5+0x011E`); source
  `0x1500..0x19FF`. Effective bank `0x30`.
- Expected semantic appearance: **PURE WHITE**.
- Semantic decision: owned by the palette-decision/index model.
- P1 and score palette semantics shared: **YES** (same arcade palette family / effective bank; MAY
  resolve to the same palette decision).
- Pattern family identities separate: **YES** (disjoint codes; separate `object_id`/`map_key`;
  verifier confirms).

### Architectural note (GAME OVER + HUD line ownership)

GAME OVER, HUD P1, HUD SCORE **and** the burst effect all have effective bank **0x30**.
`tools/translation/gen_pc090oj_palsel_lut.py` keys the palette-**LINE** LUT only by effective bank
(regex `:bank0x([0-9A-Fa-f]{2})$`, one line per bank; it FATALs on two lines for one bank). Therefore
these four families **cannot** be assigned independent Genesis LINES through that LUT. Two consequences:
- Independent **COLOR** is achievable now, per object, through `index_map` (`gen_reindexed_pc090oj.py`
  is keyed by object/usage uid). Pure-white HUD = map opaque indices to a white CRAM entry.
- Independent **LINE** needs a per-object/usage key in the line-LUT generator (Cody). Until then
  GAME OVER's LINE equals the bank-0x30 entry and the native HUD paths still select lines 2/3.

---

## DEMON IDENTITIES

- Base family: **`PAL-PC090OJ-STAGE1-FLYING-DEMON-001`** — special two-slot `actor_508`.
- Orientation/frame families: two components in one shared frame — **component_A base `0x0129`**
  (79 corpus rows) and **component_B base `0x0275`** (70 rows). Both carry `word0_nibble 0x5`.
- Arcade code family: cells `0x129..0x132…` (component_A) and the `0x0275` block (component_B, which
  shares the code block with the burst effect under a *different* bank — variant-pipeline case).
- Arcade bank: effective **`0x35`** (emitted word0 nibble 5 | colbank `0x60`; NOT direct-bank; loaded
  via round table `0x3BA88` → pool `0x4FD02`).

## DEMON USER ASSIGNMENT

- Tighe palette index: the per-color `index_map` on `usage:flying_demon:bank0x35` (14 entries:
  `{1:11,2:8,3:15,4:1,6:5,7:2,8:12,9:14,10:3,11:4,12:7,13:6,14:10,15:13}`).
- Tighe palette line: **1**.
- Saved UI/profile index: identical (present in `analysis/graphics_optimizer/editor_policy/Test.json`).
- Saved UI/profile line: **1**.

## DEMON PIPELINE

| Stage | semantic key | palette index | palette line |
|---|---|---|---|
| Palette Composer | `usage:flying_demon:bank0x35` | index_map (14) | 1 |
| Saved profile (Test.json) | `usage:flying_demon:bank0x35` | index_map (14) | 1 |
| Snapshot (Test.snapshot.json) | same | same | 1 |
| Registry | `PAL-PC090OJ-STAGE1-FLYING-DEMON-001` | (color = index route) | **recorded 1** (was null) |
| Generated LINE LUT (`pc090oj_palsel_lut.inc`) | scene 1 bank `0x35` | — | **1** (profile_sha256 == live) |
| Generated INDEX (`pc090oj_editor.bin`, reindex) | `usage:flying_demon:bank0x35` | index_map applied | — |
| Runtime lookup (`.Lnq_hit`) | effective bank `0x35` = `(attr&0x0F=5)|((0x60&0xE0)>>1)` | reindexed pixels | LUT → 1 |
| Emitted SAT word-2 | bits 13-14 | — | `line<<13` from LUT (= 1) |

- **FIRST WRONG STAGE: NONE** in the tool / generator / registry. The assigned LINE (1) and INDEX
  (`index_map`) both propagate faithfully to Build 0458's generated artifacts and the runtime emit
  contract.

## DEMON ROOT CAUSE

- UI persistence bug: **NO** · Wrong profile consumed: **NO** (live Test.json SHA == snapshot ==
  `.inc`-recorded profile_sha256) · Registry precedence bug: **NO** (runtime consumes the profile→LUT,
  not the registry) · Family-key mismatch: **NO** (`usage:flying_demon:bank0x35` identical across
  editor, reindex generator, LUT) · Base/frame mismatch: **NO** (both components emit nibble 5 → 0x35)
  · Index/line confusion: **NO** (line → LUT; index_map → reindex; distinct, both honored) · Generator
  drop: **NO** (`0x35->1` present) · Stale generated output: **NO** (`pc090oj_editor.bin` rebuilt in
  0458; LUT sha matches live) · Generic fallback: **NO** (scene-1 editor row wins over oracle) ·
  Runtime LUT bypass: **NO** (`.Lnq_hit` reads `current_sprite_palette_map`) · Attribute overwritten
  after lookup: **NO** (`andi #0x1FFF` acts on the code, not SAT word-2; palette or'd in and written
  with no later palette mask) · Incomplete orientation/frame coverage: **NOT OBSERVED statically**
  (corpus shows nibble 5 for both components; runtime confirmation below).
- **Exact root cause:** no propagation/override defect is present statically — Tighe's Demon line and
  index reach the accepted Build 0458. The remaining, honest explanations for a wrong in-game
  appearance (neither is a misconfiguration by Tighe):
  1. **Shared-line color approximation.** Line 1 is shared via the `delta_e` solver by
     `flying_demon` + `four_armed_insect` + `lizardman`; **14 of 15** CRAM entries on line 1 are
     claimed by more than one usage. Each shared entry holds a single delta_e compromise color, so the
     Demon's pixels resolve to approximate colors drawn from a line co-owned by two other enemies —
     not the Demon's exact palette. This is a line-capacity/authoring tradeoff the Composer performs
     intentionally, but it is not clearly surfaced as "your Demon colors are approximated because this
     line is shared with 2 other enemies."
  2. **Runtime confirmation gap** (below): a SAT word-2 capture is the only thing not provable in a
     no-MAME task.

## DEMON FIX

- Tool/generator fix implemented: **NOT APPLICABLE** — no tool/generator/registry propagation defect
  was found; implementing a "fix" would be inventing a bug. The registry Demon decision was updated to
  **record line 1** (previously null), which preserves (does not change) Tighe's assignment.
- Files changed: `specs/palette_decisions.json` (Demon `genesis_realization` line 1 recorded; 3 new
  families), `tools/graphics_editor/server.py` (families exposed), `tools/graphics_editor/verify_palette_families.py` (new).
- Existing Tighe values preserved: **YES**. Manual re-entry required: **NO**.
- Generated index after fix: unchanged (index_map already applied in 0458). Generated line after fix:
  **1** (unchanged; now also recorded in the registry).
- Runtime production correction still required: **CONDITIONAL — only if the runtime SAT capture shows
  a wrong line for some Demon piece.** If so:
  - Cody source file: `apps/rastan-direct/src/pc090oj_hooks.s`.
  - Function/label: the native gameplay finalizer piece path (`.Lnq_hit` palette composition and the
    `profile_native_variant_entry` effective-bank derivation).
  - Expected semantic key: effective bank `0x35` for **every** emitted Demon piece (both components,
    all orientations/frames) → `current_sprite_palette_map[0x35]` = line 1.
  - Current wrong key/value (hypothesis to test): any Demon frame emitting word0 low nibble ≠ 5 would
    compute bank `0x30` (= burst) → LUT line 0 and the burst variant cell.
  - Exact SAT-writing path: `.Lnq_hit` → `d7 = current_sprite_palette_map[(d1&0x0F)|lane]` →
    `.Lnq_sat_palette_bits[d7]` (`line<<13`) → `or.w` into SAT word-2 at `move.w %d0,(%a3)+`.
  - Smallest proper correction (only if confirmed): ensure the Demon's native frame records carry
    nibble 5 for all frames (data/generator), NOT a runtime per-actor palette hard-code.

## CAUSAL / PALETTE INDEX VS GENESIS PALETTE LINE

- **Palette LINE** = Genesis CRAM line 0-3 = the `line` field → `pc090oj_palsel_lut` → SAT word-2 bits
  13-14. Keyed by effective bank.
- **Palette INDEX** = the per-source-color `index_map` (arcade index → target CRAM index) → consumed by
  `gen_reindexed_pc090oj.py` → reindexed pattern pixels. Keyed by object/usage uid.
- These are **independent** and both honored for the Demon. The known limitation (design defect to
  record) is the shared bank-0x30 LINE LUT for GAME OVER/HUD/burst — the UI lets a family be authored,
  but independent LINE for bank-0x30 families is not yet honored by the generator (COLOR via index_map
  is). The Demon (bank 0x35, unique) is not affected by that collision.

---

## PALETTE COMPOSER

GAME OVER editable: **YES** · Gameplay P1/1UP editable: **YES** · Gameplay score editable: **YES** ·
Demon editable: **YES** (unchanged). Palette index clearly exposed: **YES** (per-color `index_map`
mapping UI). Genesis palette line clearly exposed: **YES** (`line` with the `→L{line}:{index}` tags).
Existing Test decisions preserved: **YES**. Second palette system created: **NO**.

## VERIFIERS (`tools/graphics_editor/verify_palette_families.py`, 9/9 PASS)

GAME OVER family: **PASS** · GAME OVER no burst fallback: **PASS** · P1 family: **PASS** · Score
family: **PASS** · HUD pure-white semantic decision: **PASS** · Demon saved index → generated index:
**PASS** · Demon saved line → generated line: **PASS** · Generated Demon key → runtime key: **PASS**
(static; final SAT-bit confirmation is the runtime capture below).

## PRODUCTION

Runtime gameplay code changed: **NO** · ROM built: **NO** · Build number consumed: **NO** · Build 0458
modified: **NO**.

## NEXT CODY HANDOFF

- GAME OVER production integration required: **YES** — teach `gen_reindexed_pc090oj.py` (and, for
  independent LINE, `gen_pc090oj_palsel_lut.py`) the `object:attract.game_over` family so
  `.Lnq_gameover_emit` renders the authored palette instead of inheriting burst.
- Gameplay P1 production integration required: **YES** — route `object:hud.p1_label` pure-white through
  the index model into the HUD producers (`gen_native_hud.py` / `.Lnq_project_p1_hud` /
  `build_pc090oj_hud_white.py`) instead of the hardcoded lines 2/3.
- Gameplay score production integration required: **YES** — same for `object:hud.score_digits`.
- Demon production runtime fix required: **CONDITIONAL** — only if the SAT capture shows a non-0x35
  line for some Demon piece (see DEMON FIX). Otherwise the pipeline is already correct; the open item
  is the shared-line-1 color approximation (give the Demon a less-contended line, or accept the
  approximation), which is an authoring decision for Tighe in the Composer, not a code fix.
- Ready for focused palette ROM candidate: **PARTIAL** — the semantic families and the registry now
  exist and are authorable; a ROM candidate that visibly changes GAME OVER/HUD/Demon needs the
  generator integration above (Cody) first.

## ISSUES

Updated: **OPEN-006** (sprite/high-bank palette mapping) — 0458 acceptance, the three new families,
the bank-0x30 line-LUT architectural defect, and the Demon faithful-propagation finding. Closed:
**NONE** (no post-tool-change production ROM has been tested, so no visual defect is closed). Phase D:
**NO**. Phase E: **NO**.

STOP.
