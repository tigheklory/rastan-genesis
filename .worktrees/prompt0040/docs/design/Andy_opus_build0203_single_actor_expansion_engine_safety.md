# Andy/Opus — Build 0203 Single-Actor Expansion Engine Safety (REJECTED DIAGNOSTIC — engine safety PROVEN)

**Date:** 2026-07-17
**Type:** Narrow record-46 staging implementation + validation. **Build 0203 REJECTED / NOT ACCEPTED / DIAGNOSTIC ONLY.** Rolling reverted to Build 0200.
**Build 0203 (rejected diagnostic):** `dist/rastan-direct/rastan_direct_video_test_build_0203.bin` SHA `c9ad9b04bdb4f302…`, size 1583080, counter 203, config 256, opcode_replace 214 (source-only), coverage 0x1827E8.
**Baseline/rolling:** Build 0200/256 `bdba9bab…` (restored). Comparison Build 0201/192 `7c89e96d…`.
**Repo end-state:** counter 203 (0203 consumed; next release 0204), rolling Build 0200/256, config 256, Makefile default 256, opcode_replace 214, coverage 0x18271C. Build 0204 not produced. Source reverted.

## RULES.md artifact rule: present (confirmed; not modified this task).

## PRIMARY RESULT — engine 0x3D254 is SAFE to call on a validated actor (classification B confirmed)
Build 0202's corruption was **classification B: the broad hook called the engine on entries that looked active but were not valid actors** — specifically block A5+0x2C8 code-0 entries (a4@(1)=0), which make the engine index its sprite-layout jump table at [0]→a wild path and corrupt player/fall state from gameplay start.

Build 0203 narrows the staging to **block A5+0x748 (record 46) only**, and calls the engine **only for validated entries** (active AND non-zero code AND arcade's a4@(0x36)==0 gate). Result in MAME:
- **No mode-3 lock. Player fully controllable:** mode 0→1 (walk), pX 0x20→0xA0, scrollX advances to 0x1F2, jump reachable, mode returns to 0.
- **Player records 120–131 intact** in the mirror.
- The valid A5+0x748 actor (code 0xA8/0xA9, matching arcade) triggers the engine every active frame **without corrupting state.**

So the expansion engine can be safely invoked on a validated actor. The Build 0202 fear that the engine is inherently unsafe is disproven; the guard (non-zero code) is the fix for the corruption.

## WHY 0203 IS REJECTED (two unresolved issues, not player corruption)
1. **Engine produces an empty record for this actor.** The scratch buffer is entirely code-0 after the engine call; mirror record 46 reads `[0000 0000 0000 0000]` when the enemy is active, so it is culled (code 0) and no enemy sprite appears. Arcade's engine produces record 46 = `[0000 0061 0277 00A9]` (code 0x0277) for the same actor.
2. **Represented count regresses 18→8** when the enemy is active — the per-frame flush of the record-46 window churns the candidate/represent pipeline and starves the represent budget (player records remain in the mirror but fewer are represented → visible degradation).

Per the build gate ("generated scratch output must match arcade PC090OJ output"), neither is satisfied → **not shippable.** 0203 is preserved as a rejected diagnostic; rolling stays Build 0200.

## Why the engine output is empty — narrowed, not yet solved
The actor struct was compared arcade-vs-Genesis for the active A5+0x748 entry:
```
arcade:  +00 01 A7 00 00 00 00 02 00  FF 01 ... +1A 00 ... +1E 02 75
genesis: +00 01 A8 00 00 00 00 02 00  01 01 ... +1A 00 ... +1E 02 75
```
Every actor field the engine actually reads — a4@(22), a4@(24), a4@(26), a4@(30), a4@(39), a4@(3) — is **identical** between arcade and Genesis (all 0 except a4@(30)=0x02 both), and the sprite code 0x0275 at +0x1E matches. The engine does **not** read the one differing field a4@(8) (0xFF vs 0x01). So the empty output is **not** bad actor data; it is a difference in the engine's execution/caller context (a register or global the arcade caller chain establishes before 0x41DAE that the narrow hook does not, or a layout-table pointer subtlety). Resolving it requires instruction-level single-stepping of 0x3D254 on the one validated actor — a distinct next-task investigation, not a bounded edit here.

## Classification
**Primary: B** (Build 0202 called the engine on invalid/code-0 actors). Secondary remaining for correct output: **A/G** candidate (caller-side register/global contract not satisfied by the narrow hook) — to be confirmed by stepping the engine.

## Build decision — REJECTED (no accepted build); Build 0200 remains rolling
- Single-actor engine call: **proven safe** (control preserved). ✅
- Scratch output matches arcade: **no** (empty). ✗
- Representation preserved: **no** (18→8 regression). ✗
Gate requires all → 0203 rejected. Preserved and labeled per the artifact rule; number consumed.

## Exact next step
Single-step 0x3D254 on the validated A5+0x748 actor (MAME debugger watch on the engine's a1@+ writes and its register reads) to find why arcade produces record 0x0277 while the narrow hook produces code 0 — i.e., which caller-side register/global the engine depends on. Then satisfy that contract and reduce flush churn (flush only changed records / only when the block is active) to fix the represent regression.

## Not regressed
Rolling reverted to Build 0200: control/jump/attack/scroll/player-completeness/palette intact (rolling SHA re-verified `bdba9bab`). No spec/opcode/mirror-size change persisted.
