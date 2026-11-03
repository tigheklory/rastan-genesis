# Andy — Build 0159: Post-Command Drop/Landing Divergence Analysis (Analysis Only, No Build)

## 1. Phase 0 / baseline
branch `rastan-direct-proposal`, HEAD `b077d7b`, clean. Accepted Build 0158 ROM
`2bf5a06fd5d8ea759c4a9c1c82ce00c34257f338bcaee42d64de9093f17e23ab`, counter 158. **No source edit, no build.**
Task class: analysis (post-Build-0158). KNOWN_FINDINGS touched: KF-039 (A5 WRAM mapping). No CONFIRMED/STRONG
contradiction. OPEN issue: OPEN-017.

## 2. Address mapping method
A5 work RAM: arcade base `0x0010C000`, Genesis base `0x00FF0000` (KF-039). Fields (a5+off): X `+0x10BE`,
Y `+0x10C0`, cmd `+0x137A`, contact `+0x10CE`, move `+0x10D0`, hcorr `+0x10D8`, vcorr `+0x10DA`,
mode `+0x10E8`, life1 `+0x1394`, life2 `+0x13AA`; staged BG scroll Y `0x00FF409A` (Genesis). Arcade PC080SN
scroll sampled at `0xC20002`/`0xC20006`.

## 3. Trace method
Same coin→start route on both images (Build 0158 cart / arcade `rastan`). Aligned by logical event:
`base = first 2/3/0 frame`; sampled at `rel = F-base` (0..320). `states/traces/build_0159_drop_landing/`.

## 4. Arcade timeline (rel = frames after first 2/3/0)
- rel 00: Y=0x0030, mode=0x0003, alive. Drop **accelerates** (Y +1,+1,+2,+3,… gravity).
- rel **33**: Y=0x0070 (landed), vcorr=**0x0003**, move=0x0002, mode=0x0003.
- rel ~120: vcorr→0x0002, move=0x0000, mode→**0x0000** (terminal). Stable to rel 300, alive.
- Vertical scroll: **scrY = 0x0000 throughout** (no vertical camera pan).

## 5. Genesis Build 0158 timeline
- rel 00: Y=0x0030, mode=0x0003, alive. Drop **linear** (Y +4 every ~3 frames).
- rel **45**: Y=0x0070 (landed), vcorr=**0x0004**, move=0x0002, mode=0x0003.
- rel ~180: move=0x0000, mode→**0x0008** (terminal, ≠ arcade). Stable to rel 300, alive.
- Vertical scroll: **staged_scroll_y_bg animates 0x01EC → 0x0147** (rel 60→180), then stable.
- 2/3/0 window lasts ~313 frames, then exits to **2/4/0 (attract)** — not a death exit.

## 6. Command-source confirmation
`a5+0x137A = 0x00FF` on Genesis through the entire drop/landing window (matches arcade); the Build 0158 rebase
is intact — no `0x5553`. **The command-source fix is NOT contradicted.**

## 7. First remaining divergence
The **drop/landing itself is faithful**: both land at Y=0x0070, X=0x0020, alive (life1=0x00FF, life2=0x0001),
and the player does **not** die. The player-state divergences, in order of appearance:
1. **Vertical velocity model / vcorr** (`a5+0x10DA`): arcade accelerates and lands at rel 33 with vcorr=0x0003;
   Genesis drops linearly (+4/≈3f) and lands at rel 45 with vcorr=**0x0004**. First differing *field*.
2. **Terminal player mode** (`a5+0x10E8`): arcade settles to **0x0000**; Genesis settles to **0x0008**. First
   differing *semantic state*.
3. **BG vertical scroll** (`0x00FF409A`): Genesis animates **0x01EC → 0x0147**; arcade **scrY = 0x0000**. The
   Genesis has an extra vertical camera pan the arcade does not; on the 32-row Genesis BG plane this is the
   "scrolls/falls into black" the user observes.

The reported "dies almost instantly" is **not** reproduced at the player-state level in Build 0158 (the player
lands and stays alive); the *visible* impression is driven by the extra BG vertical scroll (#3) plus the
absent gameplay sprites (Build 0157 deferred sprite-display timing).

## 8. Writer PC for first divergence
**Not proven** (analysis budget constrained; no writer taps were run). The `vcorr` / `mode` / `scroll_y`
writers were not isolated to a PC in this pass.

## 9. State-causality answers
1. Q1 (cmd 0x00FF through drop/landing): **YES** — held to 0x00FF the whole window.
2. Q2 (first remaining divergence): the **vertical velocity model** (vcorr 0x0004 vs 0x0003 / linear vs
   accelerating drop, landing rel 45 vs 33), then terminal **mode 0x0008 vs 0x0000**, then the **extra BG
   vertical scroll**.
3. Q3 (which class): primarily **camera/scroll start** (extra Genesis vertical BG scroll) and **player terminal
   mode**, downstream of a **vertical-velocity/landing-timing** difference — **not** death/fall (player stays
   alive) and **not** a landing-target error (both reach Y=0x0070).
4. Q4 (writer PC of first bad value): **not proven** this pass.
5. Q5 (earlier code that should create correct state): the vertical-velocity/gravity update (Y integrator) and
   the post-landing state-machine + camera-Y computation — not yet localized to source.
6. Q6 (why not match): unproven; hypothesis — the Genesis Y integrator uses a fixed step rather than the
   arcade's accelerating gravity, and the post-landing mode/camera path takes a different branch (mode 0x0008)
   that engages a vertical scroll absent on the arcade.
7. Q7 (Build 0159 boundary proven?): **NO** — writer PCs and source state are unproven, and the visible failure
   is camera/scroll + sprites rather than a bounded drop/landing/player-death write.

## 10. Readiness classification: **B** (with a strong **D** aspect)
**B** — first differing player-state fields are found (`vcorr` 0x0004 vs 0x0003; terminal `mode` 0x0008 vs
0x0000), but the writer PCs are **not proven**. **D aspect**: the drop/landing/player-death boundary this task
targeted is essentially *faithful* (the player lands correctly and stays alive) — the visible "scrolls into
black + no sprite" failure is driven by the **BG vertical scroll** (deferred broad-scroll) and the **absent
gameplay sprites** (Build 0157 deferred), not by a player drop/landing/death defect. **Not ready for a bounded
Build 0159 in the drop/landing domain.**

## 11. Exact next implementation boundary if ready
Not ready. Smallest next analysis steps (separate, budgeted): (a) prove the writer PC of `staged_scroll_y_bg`
(0x00FF409A) and whether the arcade computes a nonzero camera-Y here (the "scrolls into black" owner); (b) prove
the writer/branch that sets terminal `mode`=0x0008 vs arcade 0x0000; (c) confirm whether the Build 0157 sprite
active-window vs plane-paint-window timing is the true "no sprite" cause. None touches rendering/scroll source
in this task.

## 12. Open/Closed Issues Impact
OPEN-017 advanced (post-command drop/landing proven faithful; player lands at Y=0x0070 and stays alive; remaining
divergences localized to vertical-velocity model, terminal mode 0x0008, and an extra BG vertical scroll). No new
issue, none closed. Deferred: BG vertical scroll/camera, sprite-display timing, continue/game-over, D00298,
Exodus, audio, collision.

## 13. KNOWN_FINDINGS impact
Option A — no new finding indexed (runtime timeline observations; no durable ownership rule proven — writer PCs
unproven).

## 14. Architecture compliance
CONFIRMED. Analysis only — no source, no build, no spec/tool edits; runtime evidence via MAME taps; arcade
program remains the reference. No rendering/scroll/sprite/continue/game-over/D00298/Exodus/audio changes.
