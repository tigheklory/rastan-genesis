# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0136 — R2-S1 record-29 respawn Layer-B palette state

**Author:** Andy · **Date:** 2026-11-13 · **Baseline:** Build 0569 (0134 palette re-arm + 0135 Aggressive
World audio; both preserved, unchanged by this task). **No production code was changed in this task.**
Genesis MAME is environment-blocked in this sandbox, so the single remaining dynamic fact is specified as a
diagnostic for Tighe to capture. Tighe's natural-gameplay observation is authoritative.

## Outcome in one line
The palette **data model** and the **symptom class** are now statically proven. The one fact that selects the
production fix — *why a record-29 respawn keeps the frontend-base palette while an early R2-S1 respawn restores
correctly* — is a **dynamic control-flow fact** that static analysis narrowed to a single question but cannot
close. Per the prompt's decision rule ("Do NOT simply add another reload call. Find why record 29 differs" /
"If diagnostic evidence is required before a safe production fix: produce the diagnostic artifact; provide
exact test instructions; STOP; do not guess a production fix") this task STOPS with a diagnostic, not a guess.

---

## 1. Starting state
HEAD `9b3bd39e`, branch `rastan-direct-proposal`, build counter **569**. Working tree carries the unstaged
0135 `sound_comm.s` edit (music fix) and the 0134 `scene_load.s` re-arm — both intact. All 0567/0568/0569
artifacts preserved on disk (SHAs in §23). 0135 audio fix **preserved** (file unchanged this task).

## 2. 0135 music fix preserved
`apps/rastan-direct/src/sound/sound_comm.s` was **only inspected**, not modified. The per-round outdoor `$25`
gate `(record-1-(round-1)*23) < 0x10` is intact. No audio file touched.

## 3. Palette DATA MODEL (proven from the authoritative arcade program)
The R2 Layer-B palette is **one base palette plus a fade/darkening level**, not a table of 8 distinct rows:

- Per-round source pointer table `0x59EC8` (LONG entries): R1 `0x5DB4E`, **R2 `0x5DC4E`**, R3 `0x5DD4E`, …
- At `0x5DC4E` only the first 16-word block is real palette data (the R2 forest: `#000000`, dark
  greens/browns `#332200…`, sky `#5577aa`). The bytes that would be "rows 1-7" are `0xFFFF` filler — i.e. the
  source is **one** palette, and the per-record index is **not** a row offset.
- Record→level table `0x5E24E[record]` (one byte/record) is a **monotone 0→7 ramp inside each Subround-1**,
  then held at 7 before the castle. R1-S1 (records 1-16): 0,0,1,1,2,2,…,7. **R2-S1 (records 24-39):** record
  24→level 0, record 25-26→1, 27-28→2, **record 29→level 3**, …, records 37-39→7.
- The loader `FUN_00059de8` stores that byte into `a5@0x13ae` (`FUN_00059e1e`) and the hook
  `genesistan_palette_hook_59ad4` applies it as a **brightness/fade level** to the single base. So the ramp is
  the in-stage darkening of the forest as the player nears the castle.

**Consequence:** every valid R2-S1 fade level (0-7) yields a *green* Line 2. The record-29 wrong palette is
**not** a wrong fade level.

## 4. SYMPTOM CLASSIFIED BY DATA (items 13-15)
- **Correct pre-death R2-S1 L2** (what record 29 should show): the `0x5DC4E` forest base darkened to level 3
  (dark green/teal foliage, `#5577aa`-family sky), matching the correct reference screenshot.
- **Wrong post-respawn L2** (record-29 failure, screenshot 144): `genesistan_frontend_base_palette` Line 2 =
  `#000000 #000000 #900000 #fc4800 #fc9000 #fcfc00 #fcfc90 #fcfcfc #0000b4 #0048fc #0090fc #00d8fc #b4fcfc …`
  (raw CRAM `0000 0000 0008 004E 008E 00EE 08EE 0EEE 0A00 0E40 0E80 0EC0 0EEA …`). This is the exact bright
  orange+cyan band set in screenshot 144. **Identity: the frontend base palette.** (The exact 16 runtime CRAM
  words cannot be captured here — MAME blocked — but the identity is fixed by the matching constant and the
  fact that no R2 fade level produces these colours.)
- **Classification:** the record-29 respawn leaves Line 2 holding the scene-0 frontend-base clobber. The
  retained Layer-B loader **did not restore L2** on that path. This is a *bypass*, not a wrong-row and not a
  wrong-source. It is the **same failure family** as the pre-0134 bug, but on a progression-selected path that
  the 0134 re-arm does not cover.

## 5. Record semantics (Phase 1)
- `a5@0x13e` (= `ARCADE_PLAYER_RECORD`, 0x013E) is the **monotone global segment/record counter**. Its only
  writer is the increment at `0x558E0` (`a5@0x13e = a5@0x13e + 1`); there is **no decrement/rewind writer**.
- Round base table `0x50722` = 0,0x17,0x2E,0x45,0x5C,0x73 = `(round-1)*23`. R2-S1 outdoor = records 24-39.
  "Record 29" is mid-R2-S1 (local offset 6 of 16), fade level 3. Consistent with the screenshot (R2 outdoor).
- **Important (Phase-1 answer to "do death and respawn share the record"):** because `a5@0x13e` never rewinds,
  the post-respawn record equals the death-time record (≈29). The arcade does **not** reconstruct the palette
  from a rewound record; it keeps the physical Layer-B bank (bank 3) resident across death (Model C). The row
  state is therefore NOT the discriminator. Palette "progression state" on the arcade = the physically
  resident bank-3 palette, not a separately rewound counter.

## 6. Retained-loader arm inventory (who sets `a5@0x13b0=1`)
Only four sites set the Layer-B reload flag:
1. `0x45D7C` `FUN_00045d7c` — **palette-fade completion** (when the `a5@0x238` fade counter crosses its end):
   clears `a5@0x238`, sets `a5@0x13b0=1`, calls `FUN_0003ba20`, sets `a5@0xc50=1`.
2. `0x51156` `FUN_00051156` frame-`0x70` — gated by `FUN_0005113a` to `a5@0x13e ∈ [0x74,0x83]` = **records
   116-131 = Round 6 Subround 1 only** (a scripted R6 sequence; irrelevant to R2).
3. `0x55C22` `FUN_00055c22` — **scene/round-entry** reset (`a5@0x10f4=0; a5@0x13b0=1`).
4. **Genesis-only (0134):** `scene_load.s` `load_scene_tiles` scene_id==1 re-arm (`move.w #1,0x13b0(a5)`).

The loader `FUN_00059de8` runs the body only if `a5@0x13b0==1` and **always disarms to 0xFF afterward**. So a
persistent wrong L2 (not a 1-frame flash, which is what Tighe sees) means the body **never executed with the
flag set** after the last clobber on the record-29 path — i.e. no live arm reached it, OR a later clobber
followed with no subsequent arm.

## 7. LEADING HYPOTHESIS (concrete, static, to be confirmed): the teardown-owner dispatcher tests a dead var
The Genesis teardown hook `genesistan_pc090oj_hook_zero_fill_56440`
([pc090oj_hooks.s:1990](../../apps/rastan-direct/src/pc090oj_hooks.s#L1990)) picks the post-teardown owner:

```asm
    cmpi.w  #0x0008, 0x13AA(%a5)
    beq.s   .Lzero_fill_gameplay_owner      ; -> load_scene_tiles(1)  (scene 1, 0134 re-arm fires)
    bsr     genesistan_frontend_owner_reset ; -> load_scene_tiles(0)  (scene 0, L2 CLOBBERED, no re-arm)
```

But in the authoritative arcade program **`0x13aa` is written exactly once — to `9`** (`0x3A84E
move.w #0x9,(0x13aa,A5)`) — and is otherwise its BSS-zero init. **It is never 8.** The variable that actually
holds 8 is **`0x13ac`** (`0x3A824 move.w #0x8,(0x13ac,A5)`, read at `0x51232`). So the hook's gameplay-owner
branch is **effectively unreachable**, and the teardown falls through to `genesistan_frontend_owner_reset`
(scene-0 frontend clobber of Line 2) whenever it runs. This is a real latent defect: the branch was intended
to keep the gameplay owner on a subround-style teardown but tests a variable (`0x13aa`) the arcade uses only
as a transient `=9` state marker.

**Why this is only a HYPOTHESIS for the record-29 bug, not yet the proven cause:**
- It does not by itself explain why an **early** R2-S1 respawn restores correctly while record 29 does not —
  if this hook clobbered on *every* teardown, early respawn should fail too. The early-vs-29 divergence is
  therefore either (a) a second arm that fires early but not at record 29 (most likely the fade-completion arm
  `FUN_00045d7c`, which depends on whether a respawn fade `a5@0x238` runs), or (b) the record-29 death/respawn
  traversing this hook while the early one does not.
- I could not find any arcade variable that holds the author's intended **8-or-13** "subround vs round-clear"
  discriminator (neither `0x13aa∈{0,9}` nor `0x13ac∈{0,8}` ever holds 13), so the *correct* replacement
  variable for the hook is itself unproven. Changing the hook to another variable would be a guess, and the
  dispatcher is on the path of **every** subround/round/death transition (high regression blast radius) — it
  cannot be validated without running it. The prompt forbids this guess.

## 8. Hypotheses status (prompt list)
- **A (re-arm too early / state changes after re-arm):** does not fit — a transient race gives a 1-frame
  flash, not the persistent wrong L2 observed. Unlikely sole cause.
- **B (record 29 uses a different respawn path):** PLAUSIBLE — ties to §7; needs the diagnostic.
- **C (loader runs then a later write clobbers L2):** PLAUSIBLE — the scene-0 frontend owner reset (§7) is a
  concrete later clobber with no following arm; needs ordering evidence.
- **D (arcade preserves bank physically; Genesis reconstructs from stale state):** PARTLY CONFIRMED as the
  arcade's model (Model C: bank 3 resident across death), but the Genesis defect is a *clobber+no-restore*,
  not a wrong reconstruction. The faithful native invariant is "while scene_id==1, Line 2 must equal the
  current round's Layer-B loader output" (§10).
- **E (reload never executes on the record-29 checkpoint path):** PLAUSIBLE and consistent with §4/§7.
- **F:** the §7 dispatcher anomaly is the newly found concrete candidate feeding B/C/E.

## 9. Record 32→33 epoch
The R2 native-graphics epoch boundary (records 32→33) is a **graphics-residency** boundary, not a palette
owner. Record 29 is below it (level-3 fade), and the `0x5E24E` ramp shows no discontinuity at 32→33 (levels
4→4). No evidence the epoch prep touches `a5@0x13e`, `a5@0x13b0`, or the owner dispatcher. **Not relevant** to
the record-29 palette failure (to be re-confirmed by acceptance test 11-13).

## 10. The faithful fix shape (for the NEXT task, once the diagnostic lands)
Target invariant: **while `scene_id==1`, Genesis Line 2 == the current round's Layer-B loader output.** The
fix will be either (i) repair the teardown-owner dispatcher (§7) to test the correct arcade substate so a
gameplay-style teardown keeps the gameplay owner (no scene-0 L2 clobber) — matching the arcade's physical
bank-3 preservation — or (ii) restore Line 2 on the exact native boundary that the record-29 path actually
reaches. The diagnostic chooses between these and identifies the correct substate variable. **No** record
hardcode, row hardcode, `$5DC4E` copy, `if record>=29`, `if R2&&death`, L2 freeze, or audio/tile-routing
change (all forbidden, all avoided).

## 11. R1 control (static)
R1-S1 uses the identical loader/ramp (records 1-16, base `0x5DB4E`, bank 2→Line 2). The same dispatcher
anomaly (§7) applies to R1 teardowns, so R1 death/respawn is a valid **control** to capture alongside record
29 (acceptance test 16). Any dispatcher fix must be verified to preserve R1 Layer-B progression, dynamic sky,
and water (Line-3) animation.

## 12. DIAGNOSTIC ARTIFACT (what to capture) and EXACT TEST INSTRUCTIONS
Run over the **existing** `dist/rastan-direct/rastan_direct_video_test_build_0569.bin` (the ROM that exhibits
the bug) with the established GENESIS NTSC trace tooling — no new ROM, no production change:

```
GENESISTAN_CART=dist/rastan-direct/rastan_direct_video_test_build_0569.bin \
  tools/mame/run_genesis_trace_wsl.sh
```
(uses the USA/NTSC `genesis` machine and `tools/mame/scripts/genesistrace.lua`).

Capture, frame-by-frame, across **two** runs — **Control A: an early R2-S1 respawn** (die right after the R2-S1
spawn, record ≈24) and **Failure B: record-29 respawn** (reach record 29, die, allow respawn):

1. `genesistan_current_scene_id` transitions (expect 1 → 0 clobber → 1 rebuild).
2. The 0x056440 owner-dispatch branch actually taken — exec-watch `genesistan_gameplay_owner_reset` vs
   `genesistan_frontend_owner_reset` (this is the §7 decision).
3. Values of `a5@0x13aa` and `a5@0x13ac` at that hook (confirms §7: 13aa∈{0,9}, 13ac the real substate).
4. `a5@0x13b0` lifecycle and whether `FUN_00059de8`'s loop body (`0x59AD4` call) executes after each rebuild.
5. Whether the fade arm `FUN_00045d7c` runs (watch `a5@0x238` and the `0x45D7C` arm) — the most likely reason
   early respawn restores but record 29 does not.
6. Writes to `staged_palette_words` Line 2 (+0x40..+0x5F) with the writer PC (the "last L2 writer").

The decisive comparison: *which owner branch does each run take, and does `FUN_00059de8` body run after the
final scene-1 rebuild?* That single row-pair selects fix (i) vs (ii) in §10 and names the correct substate
variable. **Then** produce the numbered gameplay candidate.

(Alternative if a trace is undesirable: splice `genesistan_diag_bookmark` (the established `bra.s .` freeze
stub) at `.Lzero_fill_gameplay_owner` / the frontend-owner `bsr` to halt at the branch and read `0x13aa`/
`0x13ac` and the taken path in the debugger — same decision, bookmark Insert→observe→Revert lifecycle. This is
a diagnostic-only ROM, numbered and preserved, never a production path.)

## 13-25. See the chat response for the itemized final report. No production file changed; 0135 and 0134 both
preserved; no record-29/static-palette hack introduced (nothing was changed). Diagnostic specified; STOP.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0136`
