# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0121 — Build 0549 attract crash + Build 0563 throne palette: regression archaeology

**Author:** Andy · **Date:** 2026-11-11 · **Type:** READ-ONLY forensic. No production source, generator, ROM,
or build counter changed. Two independent regressions investigated separately.

Environment note: MAME wedges at init in this sandbox, so runtime single-step / watchpoint confirmation was not
possible. Findings are from Git history, source, disassembly-level reading, and Tighe's preserved-ROM crash
screenshots. Points that require runtime are marked PENDING-RUNTIME.

---

## Regression 1 — Attract-demo crash, first-bad boundary 0548 → 0549

### The TRAP (same invariant across 0549–0563)

Crash signature (all builds 0549–0563): `TRAP #0`, vector `$20` (= TRAP #0), Genesis-only PC `~$000708xx`
(drifts with code layout), `A5=$00FF0000`, `SR=2F04`, `A3=$000599DE`, `SP out of WRAM range`.

The `trap #0` is `apps/rastan-direct/src/tilemap_hooks.s` **`.Lscene_scroll_reseed_bad_source_generation`**
inside `genesistan_plane_a_scene_scroll_reseed_native`. That routine, on a full scene (re)entry
(`fg_scene_scroll_reseed_pending`), validates the retained scene-descriptor **source generation** and executes
`trap #0` when the generation it is handed is not one it accepts (two `beq .Lscene_scroll_reseed_bad_source_
generation` guards at the generation check). `A3=$000599DE` lies inside the retained scene-descriptor driver band
(`0x5988C / 0x59962 / 0x599B2 / 0x59DE0`), i.e. the crash is in the scene-descriptor/reseed path, not elsewhere.
The constant register/state signature across all crashing builds proves it is ONE long-lived invariant failure,
not many; the PC only drifts because later builds relocated code.

### First-bad production change (0548 → 0549)

The 0548→0549 image delta is the PROMT-ID-0106 commit series (all 2026-11-07), which reworked Round-1
subround/round-clear ownership and the scene-reseed descriptor contract:

- `34b938a7` Fix Round 1 transition and stage-clear residency
- `d616ecfd` Protect Round 1 build reflow boundary
- `624dbea7` Honor opaque shifted replacement ranges
- **`14fe7967` Correct subround versus round-clear ownership** — flips `genesistan_pc090oj_hook_zero_fill_56440`:
  the "keep gameplay ownership" teardown substate changed from `0x000D` (state 13) to `0x0008` (state 8); the
  other substate now takes `genesistan_frontend_owner_reset`. The paired `tilemap_hooks.s` comment/gate moved the
  post-clear native publish from "state 13 reaches 0x056018" to "state 8 reaches 0x055F2A".
- **`e8ae0945` Handle both retained scene descriptor generations** — the scene-reseed source-generation handling
  / validation (the exact code around the `trap #0`).
- **`b7a10783` Refresh shared-package stage context on scene reseed** — tightened the reseed's shared-package
  stage context.

(Exact per-build commit split of 0546/0547/0548/0549 is not unambiguously recorded in AGENTS_LOG; the three
bolded commits are the ones that touch the reseed/ownership contract and therefore the attract path.
PENDING-RUNTIME: confirm which commit is the precise 0548→0549 cut if a per-build manifest is retained.)

### Why 0549 triggers it and 0548 does not

These commits were designed around the **natural R1-S2 → R1-S3 subround transition** (Stage-Clear residency,
"subround vs round-clear ownership"). They (a) flipped which teardown substate retains gameplay ownership vs
resets to frontend, and (b) made the scene-reseed accept only specific descriptor source generations.

Attract mode enters the gameplay demo through the **same teardown → reconstruct path** (`0x056440` zero-fill →
scene reseed). After 0549 it reaches that path via the substate/generation the new contract treats as
frontend/READY (or with a descriptor source generation the tightened reseed rejects). Result: the reseed native
sees a scene-descriptor source generation it does not accept and executes `trap #0`.

Before 0549 (Build 0548), the teardown substate that attract uses still kept gameplay ownership and the reseed
accepted the attract-demo scene generation, so attract entered the gameplay demo without tripping the invariant.

This is exactly the Part-D hypothesis, and the evidence supports it: **a fix scoped to the natural subround
transition made the reseed/ownership contract too strict/incorrect for attract-mode gameplay entry.** (Proven at
the source/contract level; the exact live substate value attract passes is PENDING-RUNTIME because MAME is
unavailable — Tighe's crash state line `+00 0002 +02 0002 +04 0006`, `D4=0x0C` is consistent with a teardown
substate but is not a clean 8-vs-13 readout.)

### Why it survived through 0562/0563

No work from 0550–0563 touched the scene-reseed source-generation contract or the `0x056440` ownership split;
0108 (Stage-Clear) and 0115–0119 (R2 Plane-A, scratch, Layer-B palette) are unrelated subsystems. The invariant
trap was never removed or revisited, so the attract crash persists unchanged.

### Smallest recommended correction boundary (NOT implemented)

Confine the 0106 reseed/ownership tightening to the natural-subround-transition caller, OR make the scene-reseed
source-generation check accept the attract-demo gameplay-entry generation (the generation `e8ae0945` added
handling for must include the attract path), OR restore the teardown-substate → gameplay-ownership mapping for
the substate attract uses. Must preserve: the natural R1-S2 → R1-S3 Stage-Clear residency / ownership behavior
that the 0106 series fixed, and the `trap #0` invariant itself (do not weaken the trap — make the contract
accept the legitimate attract generation). Needs runtime capture of the attract substate/generation before any
change.

---

## Regression 2 — Throne/frontend palette, 0562 → 0563 (PROMT-ID-0119), self-inflicted

### Exact source change responsible

PROMT-ID-0119 (Build 0563) forced the Plane-B palette-line index to 2 in these runtime producers, intending
"gameplay Plane-B → Line 2":

- `genesistan_hook_tilemap_bg_fill`
- `genesistan_hook_tilemap_bg_blockcopy`
- the BG scene-preamble `.Lbg_hook_desc_loop` (inside `genesistan_hook_tilemap_plane_a...`)
- (plus `.Lplane_b_native_attr_from_word` and the generator scene-fill map)

### Why the 0119 classification was wrong

0119 classified `bg_fill` / `bg_blockcopy` / BG-preamble as **gameplay-only** Plane-B producers. They are not:
they are **ungated** and therefore **frontend-reachable**. Proof: `genesistan_hook_tilemap_fg_fill` gates on
`cmpi.b #SCENE_GAMEPLAY_ID, genesistan_current_scene_id` (gameplay-only), but `bg_fill` / `bg_blockcopy` /
BG-preamble have **no** `genesistan_current_scene_id` or `fg_native_gameplay_owner` guard. They run for the
frontend (title / throne / story) exactly as for gameplay. So forcing their palette-line to 2 recoloured the
frontend throne/story Plane-B.

Part-F/-G classification:

| 0119-modified producer | frontend reachable | gameplay reachable | line before 0119 | line after 0119 | effect on throne if executed |
|---|---|---|---|---|---|
| `bg_fill` | **YES** (ungated) | YES | `attr&3` (frontend → 0/1) | 2 | throne Plane-B recoloured to Line 2 |
| `bg_blockcopy` | **YES** (ungated) | YES | `attr&3` (0/1) | 2 | same |
| BG scene-preamble `.Lbg_hook_desc_loop` | **YES** (ungated) | YES | `attr&3` (0/1) | 2 | same |
| `.Lplane_b_native_attr_from_word` | NO (streamed gameplay only) | YES | `attr&3` | 2 | none (not frontend) |
| generator scene-fill Plane-B map | NO (gameplay record maps) | YES | semantic L2 | L2 | none (not frontend) |

### Name-word selection vs CRAM contents

**Name-word selection** (routing), not CRAM contents. The throne's Plane-B tiles previously selected Genesis
palette Line 0/1 (per the retained frontend-palette evidence: frontend Plane A/B used only Lines 0/1, Line 2 had
no frontend selectors, Line 3 was sprite-exclusive). 0119 changed those tiles to select **Line 2**, which
carries no frontend palette (it is the gameplay Layer-B line), so the throne renders with the wrong line's
colours. No frontend palette hook overwrote CRAM — the name words now point at the wrong line.

### Smallest recommended correction boundary (NOT implemented)

Gate the Line-2 forcing in `bg_fill` / `bg_blockcopy` / BG-preamble on **gameplay ownership** (e.g.
`fg_native_gameplay_owner != 0`, mirroring the `fg_fill` `scene_id==SCENE_GAMEPLAY_ID` gate) so the frontend
keeps its original `attr&3` → Line 0/1 selection and only gameplay forces Line 2. Must preserve: gameplay
Plane-B still selects Line 2 (keep the streamed/scene-fill-consistent fix for R2 that 0119 targeted), and R1
gameplay Plane-B unchanged. `.Lplane_b_native_attr_from_word` and the generator scene-fill map need no change
(not frontend-reachable). Note: R2-S1 was NOT fixed by 0563 (screenshots still show the R1-sky colours on the
R2 trees), so the underlying R2 Layer-B *content* (per-round palette selection at R2 entry) remains open and is
separate from this throne routing regression.

---

## Summary of answers

1. 0548 source state = PROMT-ID-0106 series up to but not including the reseed/ownership tightening (pre
   `14fe7967`/`e8ae0945`/`b7a10783` effect for the attract path).
2. 0549 source state = includes `14fe7967` + `e8ae0945` + `b7a10783` (ownership flip + reseed source-generation
   contract + shared-package context refresh).
3. Meaningful 0548→0549 diff = `genesistan_pc090oj_hook_zero_fill_56440` substate 13↔8 ownership flip; scene
   descriptor source-generation handling/validation in `genesistan_plane_a_scene_scroll_reseed_native`; shared
   package stage-context refresh on reseed.
4. First-bad attract TRAP = `.Lscene_scroll_reseed_bad_source_generation` (`trap #0`, vector $20) — reseed
   rejects the attract scene-descriptor source generation.
5. 0548 avoids it: pre-tightening contract accepted the attract generation / kept gameplay ownership.
6. 0549 triggers it: natural-subround-scoped tightening + ownership flip rejects/mis-owns the attract path.
7. 0550–0563 = same invariant (constant A3=$599DE / A5=$FF0000 / SR=2F04 signature; PC drift only).
8. 0562→0563 throne regression source = 0119 forcing Line 2 in frontend-reachable `bg_fill` / `bg_blockcopy` /
   BG-preamble.
9. Throne defect = name-word routing (tiles select Line 2 instead of Line 0/1), not CRAM contents.
10. Wrong 0119 classification = `bg_fill` / `bg_blockcopy` / BG-preamble labelled gameplay-only; they are
    ungated and frontend-reachable.
11. Smallest corrections: (attract) accept the attract generation / restore its ownership without weakening the
    trap, scoped to not disturb the natural-subround fix; (throne) gate the Plane-B Line-2 forcing on gameplay
    ownership so frontend keeps Line 0/1.
12. Report = this file.
13. No production source, generator, or build counter changed in this task.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0121`
