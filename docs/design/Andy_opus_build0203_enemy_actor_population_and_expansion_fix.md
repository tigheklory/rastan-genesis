# Andy/Opus — Build 0203 Enemy Actor Population / Expansion Fix (Analysis, STOP — No Build)

**Date:** 2026-07-17
**Type:** Arcade-vs-Genesis actor-population trace (both emulators live) + root analysis. **No source/spec/build change.** No bounded translation error found → no build.
**Baseline:** Build 0200/256 `bdba9bab8c0377164a742bf39115f372d1d348aaa755b7bec2720937fc5b9663`; comparison Build 0201/192 `7c89e96d…`.
**Repo end-state:** counter 201, rolling Build 0200/256, config 256, Makefile default 256, opcode_replace 214, coverage 0x18271C. No Build 0202/0203/0204. (RULES.md artifact-preservation rule added — see below.)

## RULES.md artifact preservation rule
**Added** (it was absent). New section "Numbered ROM Artifact Preservation Rule" plus a "Consumed / deleted numbers" note recording Build 0202 as consumed by a deleted rejected diagnostic (partial SHA `ede84ca7…`), not to be reused or recreated unless Tighe asks.

## Method breakthrough — the arcade romset runs
The arcade Rastan romset is present and **GOOD** with `-rompath roms` (the `roms/allregions` set was shadowing it and is bad). This enabled the first live **arcade-vs-Genesis** comparison. WRAM write-taps do not fire on either side (both direct-map WRAM), so provenance is by per-frame WRAM sampling + static disasm.

## PRIMARY FINDING — the actor blocks DO populate on Genesis (revises the prior "empty upstream" conclusion)
With the player walking right (camera scrolling), Genesis Build 0200:
- **Camera A5+0x10B8 advances past the spawn gate** (reaches 0x00A1 ≥ 160), driven by scroll velocity A5+0x10D8 — identical mechanism to arcade.
- **Block A5+0x2C8 (→rec 140) holds 6 active entries** (as arcade).
- **Block A5+0x748 (→rec 46) spawns** (b748=1 observed at ~F1800, after the camera scrolled).

So enemy actor population is **not globally broken** and is **not** blocked by an unrelocated pointer or empty blocks. The earlier "actor blocks empty" observation was a sampling artifact — the blocks are empty only *early* (before the camera scrolls past the spawn threshold).

## Spawn path verified faithful on Genesis
- Spawn dispatcher arcade 0x450D8 (keyed on stage A5+0x118) and preprocessor 0x4580C (gated `cmpiw #160, a5@(0x10B8)`) are intact on Genesis (not NOPped).
- The stage-init table pointer (arcade `moveal #0x50850`) **is correctly relocated** on Genesis (`moveal #0x50A50`), and the table data at 0x50A50 matches arcade 0x50850 byte-for-byte.
- Spawn-control fields match arcade at matched frames: stage A5+0x118=1, sub-phase A5+0x13E, wave A5+0x21C, trigger A5+0x2DE — **all equal**.
- Camera A5+0x10B8 and scroll velocity A5+0x10D8 advance on Genesis as on arcade.

**No raw-WRAM literal, no unrelocated pointer, and no NOPped spawn routine were found on the active enemy-population path.** There is no bounded translation error in the population path to patch.

## The two real (non-bounded) blockers for on-screen enemies
1. **Staging is NOPped and the expansion engine is unsafe to call (KF-060 / KF-061).** Arcade 0x41DAE/0x45DFA (which convert actor structs → PC090OJ records 46/57/96/140 via engine 0x3D054) are **fully NOPped** on Genesis (0x41FD2/0x46028/0x4207A/0x46044 = `4e71`), and the relocated engine **0x3D254 is never called anywhere** in the live ROM. The Build 0202 attempt to drive it from a hook corrupted player/fall state (proven regression). So even when block 0x748 spawns an enemy, it never becomes a sprite record. This is the immediate blocker, and it is a multi-routine reimplementation (KF-061), not a bounded fix.
2. **Sub-phase progression diverges (overlaps the known level-reset symptom).** Arcade advances the stage sub-phase A5+0x13E 1→2 (F1080) and progresses; Genesis cycles A5+0x13E 1→0→1 with periodic camera/state resets and does not advance to sub-phase 2 in the sampled window. Since later enemy waves are gated on sub-phase, Genesis produces fewer/earlier spawns than arcade. This is the pre-existing "sky-palette-change resets Rastan to stage start" progression symptom (OPEN issue), not a new bounded literal.

Consequent secondary difference: block A5+0x2C8 entries show code byte 0x00 on Genesis vs 0x70 on arcade at later frames — a downstream effect of the sub-phase progression difference, not an independent root.

## Build decision — STOP, NO BUILD
- No bounded translation error exists in the enemy actor-population path (pointer relocated, fields match, routines intact, blocks populate).
- The enemy-visibility blocker is the staging/expansion layer, which KF-061 already proved is not a bounded fix (engine-call unsafe; full clone out of scope).
- Forcing/hardcoding enemies, forcing the engine on unvalidated actors, or globally patching are all forbidden.

Per the task gate ("If no bounded fix is proven … produce no build and explain the exact remaining unknown"), no build was produced. Build 0200 remains rolling.

## Exact remaining unknowns / next steps (for a future task)
1. **Make the expansion engine 0x3D254 safe to invoke** (the true technical blocker). The engine corrupts when called from a hook even though it is arcade code run in arcade context. Determine specifically: does it write shared/player WRAM (a5-relative) as a side effect; is a sub-engine table pointer unrelocated; or is a register/entry contract broken? This requires stepping the engine on a single validated actor (e.g. the F1800 block-0x748 entry) and watching for out-of-scope writes. Only then can the (proven-safe) Build 0202 staging framework drive it.
2. **Resolve the sub-phase progression / level-reset symptom** so Genesis advances through Stage 1 like arcade, producing the full enemy-wave cadence.

Both are their own bounded investigations; neither is a single-instruction rebase.

## Not changed / not regressed
Repo remains Build 0200: control/jump/attack/scroll/player-completeness/palette intact. Only RULES.md (rule add) and docs/ledgers changed.
