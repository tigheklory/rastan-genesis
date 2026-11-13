# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0124 — attract + frontend regression repair

**Author:** Andy · **Date:** 2026-11-11 · **Baseline:** working tree HEAD `f8b07a84` (uncommitted 0115/0118/0119
work preserved; full snapshot saved to scratchpad `worktree_snapshot_pre0124.patch`). Builds 0548–0563 + all
reports left intact. No MAME runtime available here (wedges at init) — automated gates are supporting evidence
only; Tighe's BlastEm test is authoritative.

## PART A — throne/frontend regression: FIXED (Build 0564, isolated; still contains the attract crash)

### Root cause (from PROMT-ID-0123, binary-proven)
0119 forced Genesis Plane-B palette line = 2 **unconditionally** in three producers that are shared
frontend+gameplay, recolouring the frontend throne/story (name-word routing; frontend CRAM unchanged):
`genesistan_hook_tilemap_bg_fill`, `genesistan_hook_tilemap_bg_blockcopy`, and the BG scene-preamble
`.Lbg_hook_desc_loop`.

### Authoritative gameplay-owner gate chosen
**`genesistan_current_scene_id == SCENE_GAMEPLAY_ID`** (`SCENE_GAMEPLAY_ID = 1`, `tilemap_hooks.s:238`). This is
the state already used by the sibling FG producer `genesistan_hook_tilemap_fg_fill` at its own call site
(`cmpi.b #SCENE_GAMEPLAY_ID, genesistan_current_scene_id`), so it is the authoritative scene-lifecycle owner at
these exact producers. No new flag invented. `fg_native_gameplay_owner` was rejected as the gate because
`scene_id` is the established discriminator at these sibling BG/FG producers and is set by the scene loader
before the producers run.

### Source changes (all in `apps/rastan-direct/src/tilemap_hooks.s`)
Each of the three shared producers replaced its unconditional `moveq #2, %dX` with:

```asm
    move.w  <attr-src>, %dX
    andi.w  #0x0003, %dX                 /* frontend: original arcade attr&3 -> Lines 0/1 */
    cmpi.b  #SCENE_GAMEPLAY_ID, genesistan_current_scene_id
    bne.s   .L..._line_ready
    moveq   #2, %dX                       /* gameplay: Plane B owns Line 2 */
.L..._line_ready:
```

- `.Lbg_hook_desc_loop` (scene preamble): `%d0`, attr src `%d4`, label `.Lbg_hook_desc_line_ready`.
- `genesistan_hook_tilemap_bg_fill`: `%d5`, attr src `%d4`, label `.Lbg_fill_line_ready`.
- `genesistan_hook_tilemap_bg_blockcopy`: `%d3`, attr src `%d2`, label `.Lbg_blockcopy_line_ready`.

### NOT reverted (genuine gameplay-only L2 kept)
- `.Lplane_b_native_attr_from_word` (`tilemap_hooks.s:310`) still `moveq #2, %d1` unconditionally — gameplay
  streamed producer only.
- Generated gameplay Plane-B scene-fill maps (`compile_pc080sn_genesis.py`, slot-based) still select Line 2.
This is "scope 0119's L2 normalization correctly," not "undo 0119."

### Evidence
- Frontend retains `attr&3`: each gated site falls through to the `andi.w #0x0003` result when
  `scene_id != SCENE_GAMEPLAY_ID` (frontend throne/story/title/instructions). [SRC]
- Gameplay still selects L2: `scene_id == SCENE_GAMEPLAY_ID` takes `moveq #2`; plus the ungated gameplay-only
  producers above. [SRC]
- Build assembled + linked + canonical gate PASS. [BUILD]

### Build 0564 (throne-recovery, isolated)
- `dist/rastan-direct/rastan_direct_video_test_build_0564.bin`
  SHA-256 `869054a32e526294c3046d39b51df6cabef4e76238448118c3ddf080fe7ced1f`
- Family `_d/_s/_do/_c/_full_hud/_invincible`; direct-starts R2-S1/S2/S3.
- Ledger `[canonical=PASS entry=FAIL epoch=FAIL]`: canonical/boot-guard/transition-retention/scene-fill/Plane-B
  gates PASS; GENESIS NTSC MAME entry/epoch + 30s trace = NOT RUN / ENVIRONMENT-BLOCKED (MAME wedged; killed).
- **This build intentionally still contains the attract-demo crash** (Part A isolation).

## PART B/C — attract reseed correction: STOPPED (no discriminator provable statically)

The attract fix requires scoping the `14fe7967` native reseed splice (arcade `$055F2A`) to the lifecycle that
legitimately needs it. Both the natural next-subround teardown and attract-demo gameplay entry reach the **same**
state-8 teardown (`a5@0x13AA == 8`), so the substate does **not** distinguish them. A correct, non-suppression
fix needs a retained semantic state that proves "attract/demo entry" vs "completed natural next-subround
teardown."

Static search did not yield a provable discriminator:
- The Ghidra function inventory has no labelled attract/demo/game-mode flag.
- Distinguishing the two routes requires the actual retained state at the teardown for each route — the
  descriptor-table contents at `$FF1000/$FF1040/$FF1080`, the current/saved record, stage, and any game-mode
  flag — which needs working MAME to capture for both the natural and attract paths. MAME wedges in this
  sandbox.

Per the prompt's STOP condition, I did **not** guess and did **not** implement a pointer-validity fallback or a
Build-0548 rollback (either would suppress the invariant or reintroduce the R1-S2→R1-S3 bug `14fe7967` fixed).
The `.Lscene_scroll_reseed_rebuild_bad_ptr` invariant/trap is **untouched and remains active**.

### Required runtime capture to unblock the attract fix
On real hardware / working MAME, capture at the `$055F2A` teardown for BOTH routes:
1. the game-mode/attract state (whatever flag the retained program sets for attract/demo vs credited play);
2. `a5@0x13AA` substate, `a5@0x13E` current record, `a5@0x13B8` saved record, `a5@0x1242` stage;
3. the 16 descriptor pointers at `$FF1000` (valid for natural, invalid/stale for attract);
4. the immediately preceding retained caller path for each route.
The discriminator must be one of these retained states, proven from the original program — then Part C can gate
the reseed on it (e.g. run the native reseed only when the gameplay descriptor table has actually been
established / the entry is credited play, not attract), preserving the natural transition and the trap.

## Tests
- Andy could run: static assembly/link + canonical/transition/scene-fill/Plane-B gates (PASS for 0564).
- Environment-blocked: all GENESIS NTSC MAME gameplay/attract tests (MAME wedges).

## Tighe test order
- **First (test now): `rastan_direct_video_test_build_0564.bin`** (throne-recovery only). Check: throne Rastan
  colours restored; story/instructions/title/frontend colours restored; R1 gameplay visually unchanged; R2
  Plane-B still consistently selects L2. The attract gameplay demo is **expected to still crash** in this
  isolation build.
- **Second: pending** — the attract-recovery candidate is NOT produced because no semantic discriminator could be
  proven statically. Provide the runtime capture above and I will implement Part C and build it.

Not claimed fixed until Tighe verifies 0564.

`TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0124`
