# Andy — Build 0234 Hurry-Up Bat Stale Death Sprite (INVESTIGATION; STOP — 0234 NOT produced)

**Date:** 2026-07-22 · **Baseline:** Build 0233 (`43c385fe0f1e6e20cddcdde898c14363c6f9e68bfb03a9c76496188a7d18723d`, counter 233, `RASTAN_GAMEPLAY_HUD_SPRITES=2`, `PC090OJ_MIRROR_RECORDS=256`). **No build produced; counter stays 233; nothing patched.** Evidence dir: `states/traces/build0234_bat_stale_20260723_161930/`.

## Why STOP
The task requires reproducing the residue and establishing the retirement boundary before consuming 0234 ("Do not consume Build 0234 for a speculative or diagnostic-only change"). I established strong arcade-side evidence and **three** concrete candidate divergences, but could **not reproduce the stale sprite at runtime** (the swarm does not auto-trigger) and therefore cannot yet prove *which* candidate is the bat retirement path. Shipping a fix now would be a guess. Per the task's STOP clause I stop and hand off the confirmed evidence + the exact next diagnostic.

## Architecture confirmed (N1, Build 0219+)
No PC090OJ mirror/candidate/representation/eviction layer. One object store `pc090oj_object_ram` (256 rows @ 0x00FFA8BC); `pc090oj_native_emit_pass` walks rows ascending once per frame → shadow SAT. Retirement is implicit — a blanked row emits nothing. In gameplay Mode 2 the emit pass suppresses records 9-45 but **emits records 46+**, so bat records are emitted.

## Reproduction (attempted, MAME Genesis Build 0233, -video none)
- Cold idle from stage start (records 140-238 scan, 13,000 frames): **no swarm**.
- Walk-in then idle (all-record scan, 16,000 frames): **no swarm**; walking Rastan forward also runs him into the Stage-1 pit → death (mode 0), the same auto-progression wall the rope investigation hit.
- Conclusion: the hurry-up swarm needs interactive/in-level dawdle (matches the Build 0216 swarm captures, which occurred on later lives at frames ~3687/7062 after the player idled in place). Evidence: `states/traces/build0234_bat_stale_20260723_161930/repro.txt`, `states/traces/build0234_bat_stale_20260723_161930/repro2.txt`.

## Arcade-side evidence (authoritative)
- **Bat family = PC090OJ codes 0x0268 / 0x0269 / 0x026A**, occupying **object records 48-56** (from the Build 0216 swarm capture `states/traces/build0216_pc090oj_swarm_stack_fix_20260719_201422/genesis_build0216_swarm_validate_events.log`, "nonstd=r48..r56:.../0269|026A|0268/..."). This range is **outside all mapped Genesis producers** (HUD 0-45, record 46, blocks 120-137, block-0x2C8 140-238) — confirmed by that trace's own `represented_nonstandard` exclusion set. (KF-068 records the bat family + Build 0216 swarm IRQ-stack fix.)
- **Retirement hides a record by writing Y=0x180** (`movew #384,%a1@(2)`) at arcade 0x3C4EA, 0x3C610, 0x3C6B6, 0x3C712, 0x3C7DE, 0x3C874, 0x3C9F6, 0x41F8C.
- **Arcade 0x5607C** (the routine the Genesis "decay" hook translates) is a per-4th-frame **plane-scroll + record-decay**: decrement FG scroll `a5@(0x10EE)`, `jsr 0x55AB4` (scroll commit), then walk PC090OJ records from **0xD00170 (record 46)** up to `a5@(0x141C)`, decrementing each record's Y (`a0@(2)-=1`) and **clearing its code (`a0@(4)=0`) at Y==16**, reading the records **directly**.

## Three candidate divergences (unconfirmed — need runtime to select)
1. **Broken decay hook (strongest/most specific).** `genesistan_pc090oj_hook_sprite_decay_5607c` mistranslates 0x5607C: it hardcodes records **56-63** (arcade decays 46..a5@(0x141C)), reads its per-record state from **`staged_sprite_descriptor_table`** which in N1 is a **legacy 4-byte stub** (BSS-aliased to the dead legacy exports at pc090oj_hooks.s:2031), so `btst #0,(a0)` fails and it **retires nothing**, and it omits the plane scroll. If bat retirement flows through 0x5607C, this reading-a-dead-stub is the first divergence. UNPROVEN that 0x5607C (which looks like a subscene scroll-decay) is the per-bat death path, and it may not even be invoked during normal gameplay.
2. **Block-0x2C8 deferred-special dispatch gap.** Arcade 0x41E22 routes `a4@(3)!=0` actors through **0x3EFBE** (dispatch on a4@(5) → emit `0x41E48` or blank `0x41EDE`); Genesis `pc090oj_stage_block2c8` does `.Lb2c8_skip` (preserve). Real gap, but governs records **140-238 (lizards)**, so most likely NOT the bat path.
3. **Producer one-shot vs re-blank.** If the bat producer writes records 48-56 once and relies on a separate death/decay path to retire, and that path is #1 or another unhooked route, the records persist until the next swarm overwrites them — exactly the "clears only at next swarm" symptom.

## Exact next diagnostic (for whoever continues)
One **interactive** MAME Genesis Build 0233 session (Tighe drives to trigger the swarm and kill a bat), read-only logger capturing, per frame around the kill: object records **46-63** (code @+4, Y @+2); the runtime PC that last wrote each of those records (write-tap on `pc090oj_object_ram + 46*8 .. +63*8`, mapped via address_map.json); whether `genesistan_pc090oj_hook_sprite_decay_5607c` runs and what it reads; and the matched arcade retirement (records 46+ Y-decay / Y=0x180 write). That selects candidate #1/#2/#3 and pins the first divergence. If the swarm still can't be reached, find the hurry-up timer (arcade a5-relative countdown near the 0x3B0xx swarm-spawn) and poke it for reproduction only. Only then implement the smallest faithful correction (e.g., if #1: rebuild the decay hook to decay records 46..end directly from `pc090oj_object_ram` per 0x5607C) and produce 0234.

## Preservation / compliance
Nothing changed → Build 0233 HUD records 0..8, white line-3 HUD, KF-066 bank-0x36 carrier, and the normal PC090OJ pipeline are intact. No numbered ROM touched. No guessed SAT clear, coordinate erasure, timer, tile suppression, or palette concealment. **STOP: YES.**

---

## EVIDENCE CAPTURE (2026-07-22) — interactive Genesis + arcade; FIRST DIVERGENCE PROVEN

**Reproduction:** NATURAL interactive play (Tighe drove to the Stage-1 hurry-up swarm and killed bats) in both:
- MAME Genesis Build 0233 (`-video opengl`, read-only write-tap logger `states/traces/build0234_bat_stale_20260723_161930/bat_capture.lua` on object_ram records 46-63): swarm at F4419.
- MAME arcade Rastan (`-video soft`, `states/traces/build0234_bat_stale_20260723_161930/arc_bat.lua` reading pc090oj records at 0xD00000): swarm at F3249.
Loggers/traces preserved: `states/traces/build0234_bat_stale_20260723_161930/bat_capture.txt`, `states/traces/build0234_bat_stale_20260723_161930/arc_bat.txt`.

**Affected records:** 48-56 (the 9-bat swarm), codes 0x0268/0x0269/0x026A (wing-flap animation); **death frame = code 0x0276.** (Retirement is via Y, not code — code stays 0x0276 on both platforms.)

**Genesis timeline (record 48, killed F7528):** CODE 0x0269 → **0x0276**; Y **freezes ON-SCREEN at 0x63** and the producer re-writes 0x0276 + on-screen Y **every frame** for **930+ frames to end of capture (F8458)**. **ZERO Y=0x0180 writes to records 48-56 in the entire run.** Residue = visible grey corpse, never retired.

**Arcade timeline (record 52, killed F3369):** CODE → **0x0276** at on-screen Y=0x0055 for ~1 frame, then **Y = 0x0180 (the hide value) by F3372 (~3 frames)** and held there (159 consecutive snapshots) → corpse **hidden below screen = disappears.**

**FIRST CONFIRMED DIVERGENCE:** the Genesis bat producer never applies the arcade's **Y=0x0180 retirement hide** to a dead-bat record. The arcade sets the corpse's Y to 0x0180 within ~3 frames of death; Genesis keeps the death code 0x0276 at an on-screen Y indefinitely. **The object_ram row is NEVER cleared and NEVER recreated — it is continuously re-written with 0x0276 + on-screen Y.**

**Candidate discrimination:**
- **Candidate 2 (missing translated retirement/blank path): SELECTED.** The Genesis bat producer omits the arcade dead-actor blank (Y=0x0180) path (arcade Y=0x180 writes at 0x3C4EA-0x3C9F6 / 0x41F8C / the 0x41EDE blank reached via the 0x3EFBE deferred-special dispatch).
- **Candidate 1 (broken 0x5607C decay): REJECTED for the bats.** Retirement is a per-bat Y=0x180 hide mid-swarm, not the subscene scroll-decay of 0x5607C.
- **Candidate 3 (one-shot clear + recreation): REJECTED.** The row is never cleared; code stays 0x0276 continuously.
- **Later-layer (emit-pass/SAT): REJECTED.** The row is legitimately drawable (0x0276, on-screen Y) and correctly emitted; the fault is upstream (Y not hidden).

**Not yet pinned (needed for the fix, not for the divergence):** the exact Genesis producer for records 48-56. The bat writes go through the SHARED `.Lpc090oj_emit_slot` (write PC 0x0722EA), and none of the mapped emit_slot callers use base 48 (sprite_update_54810=44-47, decay_5607c=56-63). The caller must be identified by capturing the **emit_slot return address** for the bat writes (or by mapping the arcade swarm producer that expands into D00180 through address_map.json). That is the single remaining item before implementing.

**Sufficiency:** the divergence and retirement mechanism are proven — a Build 0234 implementation task IS justified. Its first step is to pin the bat producer (return-address capture), then add the faithful arcade Y=0x0180 dead-bat hide at that producer's boundary (respond to the actor's death sub-state; do NOT hardcode-clear by tile code, coordinate, or timer). **STILL no fix and no Build 0234 in this evidence step.**

---

## PRODUCER ID + IMPLEMENTATION + VERIFICATION (2026-07-24) — Build 0234 PRODUCED & VERIFIED

### Phase 1 — producer identified (emit_slot caller capture)
Interactive Genesis 0233, logger `caller_capture.lua` reading the emit_slot stack frame (return@SP+12). Every bat write's immediate caller = **0x072438** (`bsr .Lpc090oj_emit_slot` at 0x072434), inside the unnamed routine at 0x0723D0 = **`.Lpc090oj_stage_record46_validated`** — the block-A5+0x748 producer (arcade 0x41E76..0x41EB4). It walks 11 actors into records 46-56 via the expansion engine (d2=1); records 48-56 = the 9 bats. Trace: `states/traces/build0234_bat_stale_20260723_161930/caller_capture.txt`.

### Phase 2 — arcade retirement mapped
Arcade producer 0x41E84 loop: `tstb a4@(0); beq 0x41EFC` and `tstb a4@(54); bne 0x41EFC` → **0x41EFC BLANK: `movew #384,%a1@(2)`** (Y=0x180) → the dead-bat record is hidden. The Genesis `.Lpc090oj_stage_record46_validated` used the same actor gates but branched all skips to `.Lrecord46_next` (advance WITHOUT writing) → the record froze at its last emitted value. Cross-check from the 0233 trace: record 48's writes STOP at F7533 (actor retired → skip) and the row freezes at 0x0276@Y=0x63 for 925 frames with zero writes. **Lifecycle-driven, not tile/coord/timer.**

### Phase 3 — implementation (pc090oj_hooks.s only)
Added `.Lrecord46_blank` (arcade 0x41EFC translation): writes **Y=0x180** to the current record (`pc090oj_object_ram + .Lrecord46_rec*8 + 2`, oob-guarded) and falls through to `.Lrecord46_next`. Rerouted the two ARCADE blank conditions to it: `a4@(0)==0 → .Lrecord46_blank` and `a4@(0x36)!=0 → .Lrecord46_blank`. The `a4@(1)==0` guard (Genesis-only KF-063 code-0 engine safety; the arcade emits it) and the engine-output-0 path stay as skip — neither is an arcade blank condition or the bat retire path. `.Lpc090oj_emit_slot` and `pc090oj_native_emit_pass` unchanged; no SAT clearing; no sprite suppression.

### Build 0234
`dist/rastan-direct/rastan_direct_video_test_build_0234.bin`, SHA256 `24dc953ed0301c911c3551dd529ce1fb9b9a301ed50b23de9048be940be453ee`, size 1,588,420, counter 234, GATE_PASS. opcode_replace 216 (unchanged). coverage 0x183CA4 → 0x183CC4 (+0x20 blank routine; paired in both gate scripts). Config `RASTAN_GAMEPLAY_HUD_SPRITES=2 PC090OJ_MIRROR_RECORDS=256`. Builds 0230-0233 preserved.

### Verification
- **Build 0233 residue reproduced:** dead bat 0x0276 at visible Y=0x63 for 930+ frames (`bat_capture.txt`).
- **Arcade retires:** dead bat Y→0x0180 within ~3 frames (`arc_bat.txt`).
- **Build 0234 natural play (Tighe killed multiple bats):** each kill shows CODE→0x0276 death frame visible for ~6-8 frames (the legitimate death animation), then **Y→0x0180 (writer PC 0x072450 = `.Lrecord46_blank`) → corpse hidden and stays hidden**; end-of-session all dead bats = `0276@0180` (hidden), a live bat still animating (swarm intact). HIDE(fix) writes fired 27,764×; snapshot corpse tags: transient 'D' during death anim → persistent 'H' (hidden) after. Trace: `states/traces/build0234_bat_stale_20260723_161930/verify0234.txt`.
- **Automated regression (0234):** no crash/lock through F6000; HUD records 0-5 (score) + 6-8 (`1UP` 0x39/0x48/0x46) intact; enemy record 46 (0x0277) intact; fix path exercised (Y=0x180 blanks inactive records every frame, faithful to arcade). Trace: `states/traces/build0234_bat_stale_20260723_161930/reg0234.txt`.
- **Not regressed:** lizard producer (block-0x2C8, records 140-238) untouched; KF-066 bank-0x36 carrier, white line-3 HUD, emit/SAT/tile-DMA pipeline all unchanged.

### Compliance / STOP
Architecture-compliant: lifecycle-driven retirement at the translated producer boundary, faithful to arcade 0x41EFC; shared emit_slot / emit pass / SAT untouched; no tile-code/coordinate/timer/SAT-clear hack. **STOP: NO — Build 0234 produced and verified.**
