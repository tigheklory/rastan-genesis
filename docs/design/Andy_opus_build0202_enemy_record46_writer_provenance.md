# Andy/Opus — Build 0202 Enemy Record 46 Writer Provenance (Analysis-Only, No Build)

**Date:** 2026-07-17
**Type:** Writer-provenance trace + root-cause proof. **No source/spec/build changes.** Build gate NOT satisfied (fix is not bounded).
**Baseline main:** `dist/rastan-direct/rastan_direct_video_test_build_0200.bin` SHA `bdba9bab8c0377164a742bf39115f372d1d348aaa755b7bec2720937fc5b9663` (256).
**Baseline comparison:** Build 0201 / 192 `7c89e96ddbb5070c4b6bf45aaca80d639e2ea6127514fe5c06c3c4cc0cf238b5`.
**Repo end-state:** counter 201, rolling dist = Build 0200/256, Makefile default 256, config 256, opcode_replace count 214. No Build 0202/0203. Cody's `Cody_build0202_enemy_spawn_and_visual_issue_ledger.md` preserved (documentation-only).

## Phase 0
EXTENDING. Builds on Cody's Build 0202 evidence ledger (matched arcade↔Genesis gameplay; arcade record 46 present, Genesis mirror record absent; writer PC not captured by Cody's write taps). Priors: KF-047/048/049/050/051 (PC090OJ mirror/candidate/represented), KF-058 (input), KF-059 (jump/fall). Open issues: OPEN-017, OPEN-024. Architecture compliance CONFIRMED — evidence only, no Genesis-owned lifecycle, no forced records/SAT.

## Primary classification: **E** — the arcade PC090OJ object write exists, but the Genesis hook that replaced the arcade writer drops/misroutes it.
(Record-46-specific secondary: actor staging block A5+0x748 read empty in the sampled Genesis window — a possible additional upstream population gap for record 46 specifically; see "Remaining unknown".)

## Writer provenance — PROVEN

### Arcade record 46 writer
Arcade record 46 (`0xD00000 + 46*8 = 0xD00170`, enemy, code `0x0276`/`0x0275`) is produced by **arcade routine 0x041DAE** (and its scene-2 sibling **0x045DFA**). 0x041DAE iterates four actor-staging blocks and expands each active 64-byte actor struct into PC090OJ records via the actor→sprite engine **0x3D054**:

| Arcade PC | actor block (a4) | dest `lea` | record | count | 0x3D054 type d2 |
|---|---|---|---|---|---|
| 0x41DAE | `A5+0x508` | `lea 0xd001c8,%a1` | 57 | 2 | 13 |
| 0x41DE8 | `A5+0x5C8` | `lea 0xd00300,%a1` | 96 | 6 | 4 |
| 0x41E22 | `A5+0x2C8` | `lea 0xd00460,%a1` | 140 | 9 | 10/19 |
| **0x41E76** | **`A5+0x748`** | **`lea 0xd00170,%a1`** | **46** | **11** | **1** |

Per entry: `moveb a4@(1),d0` (code), `moveb a4@(32),d6`, `moveb a4@(2),d7`, `bsr 0x3d054`, `adda #64,a4`. Inactive entries (`a4@(0)==0`) get a blank fill (`movew #384,a1@(2)`). **0x3D054 writes records through the `a1` pointer** — the sub-engine 0x3C902 emits `move.w %d0,%a1@+` / `move.w %d1,%a1@+` (0x3C982/0x3C990). Destination is therefore fully determined by the caller's `lea`, i.e. **redirectable to any address**, including the mirror.

### Genesis translation of the writer — the defect
The arcade enemy writer routines are **NOPped** in the postpatch ROM (e.g. genesis `0x42060..0x4208E` = arcade `0x41E60..0x41E8E`, the record-140/46 blocks, all `4e71`; `0x46030..0x46056` for 0x45DFA) and replaced by port hooks:

```
genesistan_pc090oj_hook_target_41dae:
    cmpi.b  #PC090OJ_SCENE_GAMEPLAY_ID, genesistan_current_scene_id
    beq.s   .Lhook_41dae_skip          ; <-- gameplay: RETURNS, does nothing (Build 0192)
    bsr     pc090oj_workram_block_sprites
.Lhook_41dae_skip: rts
genesistan_pc090oj_hook_target_45dfa:  ; same gameplay skip
```

`pc090oj_workram_block_sprites` (the non-gameplay path) copies the **wrong source** — the PLAYER block `A5+0x11B2` — to the **wrong records** (0..17 / 18..21), never the enemy blocks A5+0x508/0x5C8/0x2C8/0x748. The port's own source documents this as a deferred gap: *"Arcade 0x045DFA is a distinct routine (sources A5+0x5C8/0x748/0x8C8, dest records 140/46/96 via 0x3D054), so its true destination is out of this fix's proven scope — unchanged."* (pc090oj_hooks.s:317-320.)

**Net during Stage-1 gameplay:** the enemy staging routines are no-ops → records 46/57/96/140 are never produced.

## Genesis mirror evidence (Build 0200, matched window)
`pc090oj_object_ram = 0x00FFA9D8`. At gameplay frames 650/800:

```
r46  = [0000 0100 0000 0100]   blank placeholder (no enemy)
r57  = [0000 0100 0000 0100]   blank placeholder
r96  = [0000 0100 0000 0100]   blank placeholder
r140 = [0000 0100 0000 0100]   blank placeholder
r120 = [4003 0049 009E 0010]   REAL player sprite (staging works)
r132 = [0010 EECC 09DA EEEC]   stale/spurious fireball (0xEE-polluted)
```

Actor staging blocks (a5=0xFF0000): `0x2C8`(→140) had **6 active** entries; `0x508`/`0x5C8`/`0x748`(→46) read **0 active** in the sampled window. **Key isolation:** block 0x2C8 is populated yet record 140 is blank in the mirror — proving the staging DROP (classification E) independent of actor-block population.

## First divergence
Arcade object RAM has real enemy records at matched gameplay state; Genesis mirror holds blank placeholders because the arcade enemy staging routines (0x41DAE/0x45DFA + 0x3D054 expansion) are NOPped and their replacement hooks either skip in gameplay (Build 0192) or copy the wrong player block to the wrong records. Divergence is at the PC090OJ object-source/staging layer, downstream of the arcade actor state and upstream of decoder/SAT/tile/palette.

## Fireball / record 132
Matches Cody's classification **B (stale/spurious)**: r132 = code `0x09DA`, contains 0xEE bytes; arcade r132 = 0 at matched point. Producer/clear-path not isolated; not fixed here (would need its own trace; do not patch without root proof).

## Build decision — **NO BUILD** (bounded gate not satisfied)
A faithful fix is architecturally viable (expansion engine writes via `a1@+`, so a Genesis hook could set `a1 = pc090oj_object_ram + rec*8` and call the arcade expansion 0x3D254), but it is **not a bounded, byte-neutral single fix**. It requires:
1. A Genesis hook that reproduces 0x41DAE's per-block active/count/blank-fill logic for all four actor blocks;
2. Invoking the arcade actor→sprite expansion 0x3D054 and **verifying its full sub-engine chain (0x4770E/0x3F0BC/0x3FFDC/0x3FFF0/0x3C902) and its ROM sprite-layout tables are correctly relocated and functional on Genesis**;
3. Candidate marking for the touched records so VBlank syncs them;
4. Not reintroducing the Build 0192 spurious duplicate Rastan (records 0..17).

This is a multi-routine reimplementation with real regression risk to the working player staging (hook_target_41f5e) and the Build 0192 duplicate suppression — it must be its own dedicated implementation build after the expansion-engine relocation is verified, not a patch bolted onto this analysis pass.

## Remaining unknown (the exact next evidence)
For record 46 specifically, the actor block **A5+0x748 read empty on Genesis** in the sampled window, while arcade record 46 exists at frame 650 (Cody). Two possibilities remain to disambiguate before implementing:
- **(E, staging only):** arcade also populates A5+0x748 at the matched point and the sole gap is the NOPped/skipped staging routine — fixable by the reimplementation above. (Supported by the record-140 isolation: populated block, blank mirror record.)
- **(+ B/C upstream):** the enemy-logic step that fills A5+0x748 also diverges on Genesis (spawn/progression), in which case staging alone is insufficient for record 46.

Decisive next trace: capture the **arcade writer of A5+0x748** (who fills the actor block, at frame ~650) and check whether the equivalent runs on Genesis — this separates pure-staging (E) from upstream-population (B/C). This requires the arcade romset for a live write-watch on `A5+0x748` (0x10C748) alongside the Genesis equivalent (0xFF0748).

## Not touched
No collision/enemy/spawn/render code, no mirror-size logic, no player control/jump/fall, no PC080SN, no black bars/FG/sky. Builds 0175/0178/0180/0192/0193/0194/0196/0198/0200 all intact.
