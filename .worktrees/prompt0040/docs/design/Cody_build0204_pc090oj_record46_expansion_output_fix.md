# Cody - Build 0204 PC090OJ Record-46 Expansion Output Fix

**Date:** 2026-07-17
**Type:** Analysis-first bounded implementation + release build + focused runtime evidence
**Build context:** Build 0204, `rastan-direct`
**ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0204.bin`
**SHA256:** `0e1925b2934e2d2614bb6c90de82c78ea07bc62819b58fe345fb83f8e5deb083`
**Scope:** Fix the validated record-46 enemy expansion output path. No forced enemy/SAT output. No PC080SN, sky, black-bar, collision, D00298, or level-progression work.

## Phase 0

Classification: **EXTENDING** (OPEN-017 enemy visibility / PC090OJ staging). Relevant priors loaded: KF-047/KF-048/KF-049/KF-050/KF-051/KF-052/KF-053 (PC090OJ mirror/SAT/timing/cap constraints), KF-060/KF-061/KF-062/KF-063 (enemy staging provenance, actor population, validated-engine safety), KF-059 (Build 0200 accepted jump/fall baseline), and the numbered-artifact preservation rule in `RULES.md`.

Open issues touched: OPEN-017 and OPEN-024. OPEN-018/PC080SN raw-write classes, D00298, collision, sky/palette reset, black bars, and unrelated visual ledger items were intentionally deferred. No closed issue was edited. No contradiction of a CONFIRMED or STRONG finding was detected; KF-063 is refined by this task rather than contradicted.

Architecture compliance: **CONFIRMED**. Arcade logic remains the program. The Genesis changes are helper/opcode-replacement support only: a context-aware helper restores original non-C-window sprite-emitter semantics at a shared patched site, and the existing `hook_target_41dae` gameplay path calls the relocated arcade expansion engine only for validated actor entries, flushing through the existing PC090OJ mirror/candidate/SAT path.

## Baseline Recovered

- Branch: `rastan-direct-proposal`
- HEAD during this task: `46d3517` (`Build Post Build 200-201`)
- Accepted gameplay baseline: Build 0200 / 256-record mirror
- Build 0200 SHA256: `bdba9bab8c0377164a742bf39115f372d1d348aaa755b7bec2720937fc5b9663`
- Build 0201 / 192 comparison SHA256: `7c89e96ddbb5070c4b6bf45aaca80d639e2ea6127514fe5c06c3c4cc0cf238b5`
- Build 0203 rejected diagnostic preserved: `dist/rastan-direct/rastan_direct_video_test_build_0203.bin`, SHA prefix `c9ad9b04bdb4f302`, size `1583080`, counter `203`
- Pre-build counter: `203`
- Makefile default: `PC090OJ_MIRROR_RECORDS ?= 256`
- Pre-fix canonical invariants: opcode_replace count `214`, total coverage `0x18271C`

The rolling ROM and Build 0200 ROM were byte-identical before implementation. Build 0202 remained absent/consumed, per the artifact preservation rule.

## Root Cause

Build 0203 proved the relocated expansion engine at `runtime_genesis_pc 0x0003D254` is safe when called on a validated nonzero actor, but its record-46 scratch output remained code-zero. The new static boundary is a shared opcode-replacement collision, not bad actor fields:

- `runtime_genesis_pc 0x0003D254` maps through `build/rastan-direct/address_map.json` to `arcade_pc 0x0003D054`.
- The engine's default shape path reaches `runtime_genesis_pc 0x0003CB50`.
- `runtime_genesis_pc 0x0003CB50` maps through `address_map.json` to patched-site `arcade_pc 0x0003C950`.
- That site had been replaced with `JSR genesistan_hook_text_writer_3c950; RTS; NOP...` for PC080SN text staging.
- Before Build 0204, `genesistan_hook_text_writer_3c950` only performed PC080SN/FG staging and did not preserve the original non-C-window `(%a1)+` PC090OJ record writes.

So the Build 0203 engine call was safe, but when it reached the shared `0x3C950` default path with `%a1` pointing at an 8-byte sprite scratch record instead of a PC080SN C-window destination, the hook staged nothing and returned. The scratch record therefore stayed code-zero.

## Implementation

### Shared 0x3C950 Helper Split

`apps/rastan-direct/src/tilemap_hooks.s` now makes `genesistan_hook_text_writer_3c950` context-aware by `%a1` destination:

- If `%a1 & 0x00FFFFFF` is inside `HW_ADDRESS 0x00C00000..0x00C0FFFF`, the existing PC080SN text staging path is preserved.
- If `%a1` is outside that C-window range, the helper runs a direct sprite-record path that restores the original `arcade_pc 0x03C950` `(%a1)+` emitter semantics for the actor-to-sprite expansion engine.

The non-C-window path writes the original four-word PC090OJ tuple into the caller-supplied `%a1` scratch/mirror destination. It does not force SAT entries and does not bypass the existing PC090OJ mirror/candidate renderer.

Static disassembly evidence:

```asm
7103c: 48e7 0a36       moveml %d4/%d6/%a2-%a3/%a5-%fp,%sp@-
71040: 2809            movel %a1,%d4
71042: 0284 00ff ffff  andil #0x00ffffff,%d4
71048: 0c84 00c0 0000  cmpil #0x00c00000,%d4
7104e: 6500 01c2       bcsw 0x71212        ; non-C-window -> sprite direct
71052: 0c84 00c1 0000  cmpil #0x00c10000,%d4
71058: 6400 01b8       bccw 0x71212        ; non-C-window -> sprite direct
```

Direct sprite output path excerpt:

```asm
71256: 6100 ff2e       bsrw 0x71186        ; attr gate
7125a: 32c0            movew %d0,%a1@+
7125c: 1218            moveb %a0@+,%d1
7126e: 32c1            movew %d1,%a1@+
71270: 6100 ff22       bsrw 0x71194        ; next attr/code
71274: 32c4            movew %d4,%a1@+
71276: 1e18            moveb %a0@+,%d7
7127e: 32c7            movew %d7,%a1@+
```

The patched site remains mechanically unchanged and now reaches the corrected helper:

```asm
3cb50: 4eb9 0007 103c  jsr 0x7103c
3cb56: 4e75            rts
```

### Record-46 Gameplay Route

`apps/rastan-direct/src/pc090oj_hooks.s` now makes the gameplay `hook_target_41dae` path call only a validated record-46 block re-enablement path instead of fully skipping:

```asm
722fe: cmpib #1, genesistan_current_scene_id
72306: beqs 0x7230e                  ; gameplay -> record46 validated path
72308: bsrw pc090oj_workram_block_sprites
7230c: rts
7230e: bsrw 0x7232a                  ; .Lpc090oj_stage_record46_validated
72312: rts
```

The validated path walks `A5+0x0748` for 11 actors / destination records 46..56, preserving the Build 0203 safety guard:

- actor active flag `a4@(0) != 0`
- nonzero actor code `a4@(1) != 0`
- arcade gate `a4@(0x36) == 0`

For each valid entry it calls the relocated expansion engine with the arcade caller contract and an 8-byte scratch destination:

```asm
72352: lea 0x00ffbbd0,%a1            ; 8-byte scratch record
72358: clrl %a1@
7235a: clrl %a1@(4)
7235e: moveb %a4@(1),%d0
72362: moveb %a4@(32),%d6
72366: moveb %a4@(2),%d7
7236a: moveq #1,%d2
7236c: jsr 0x0003d254                ; relocated arcade engine
72378: movew %a0@(4),%d3             ; code word
7237c: beqs 0x72392                  ; never flush code-0 scratch
72388: movew record_number,%d0
7238e: bsrw .Lpc090oj_family_apply_record
```

The flush goes through the existing mirror/candidate path. No hardcoded enemy output, no SAT forcing, no lifecycle ownership change.

## Build Verification

First release invocation failed at the canonical invariant gate before counter advancement because the mechanical coverage value changed from `0x18271C` to `0x182890` while opcode_replace count stayed `214`. After correcting the observed invariant in both canonical gate files, the release was rerun.

Final Build 0204:

- Command: `source tools/setup_env.sh && make -C apps/rastan-direct release`
- Result: `GATE_PASS`
- Counter: `203 -> 204`
- Numbered ROM: `dist/rastan-direct/rastan_direct_video_test_build_0204.bin`
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
- SHA256: `0e1925b2934e2d2614bb6c90de82c78ea07bc62819b58fe345fb83f8e5deb083`
- Size: `1583248`
- Rolling/numbered comparison: byte-identical (`cmp=0`)
- Manifest canonical invariant: opcode_replace count `214`, total coverage `0x182890`
- Release no-input trace: `states/traces/rastan_direct_video_test_build_0204_mame_30s_20260717_211158/`, `frames=1798`, no crash recorded by the standard run summary

## Runtime Evidence

Focused validation trace:

- Directory: `states/traces/build0204_record46_runtime_validation_20260717_211544/`
- Script: `record46_validate.lua`
- Command class: headless MAME Genesis run with scripted coin/start/right input
- Exit code: `0`
- Frames sampled: `1800`

Trace summary:

```text
first_nonzero_record46_56=frame:785 rec:46 words:[0000 0069 0275 0070] code:0275 screen:192,127 visible:1
first_visible_record46_56=frame:785 rec:46 words:[0000 0069 0275 0070] code:0275 screen:192,127 visible:1
first_represented_record46_56=frame:786 rec:46 words:[0000 0069 0275 0070] code:0275 screen:192,127 visible:1
last_nonzero_record46_56=frame:1800 rec:46 words:[0000 0069 0277 009B] code:0277 screen:149,127 visible:1
final_rec_46=[0000 0069 0277 009B] code=0277 screen=149,127 visible=1 represented=1 waiting=0 slot=16
```

Key interpretation:

- Build 0203's code-zero output is fixed.
- Record 46 becomes nonzero and drawable during gameplay.
- Record 46 is represented one frame after first nonzero detection.
- Record 46 reaches a real SAT slot (`slot=16`) through the existing representation path.
- Final sampled gameplay state had `represented_count=0x0011` and `active_count=0x0011`, not the Build 0203 regression to 8 represented records.
- This proves the record-46 output path now produces PC090OJ mirror/SAT data; it does not prove full visual correctness of the enemy artwork or solve later enemy waves/progression.

The trace's write tap captured early initialization writes but not the later changing tuple writes; the proof above uses the per-frame sampled mirror/representation/SAT state plus the static call path. The write-tap limitation is recorded and not used as negative evidence.

## Comparison to Prior Evidence

Build 0203 rejected diagnostic:

- Engine call safe on validated actor.
- Scratch output stayed code-zero.
- Represented count regressed `18 -> 8`.

Build 0204:

- Same safety guard retained.
- Shared `0x3C950` PC080SN/PC090OJ collision fixed by destination split.
- Record 46 emits nonzero code `0x0275/0x0277` and is represented.
- Represented/active count in the focused sample is `0x0011` / `0x0011`.

## Deferred Work

OPEN-017 remains open. This build only fixes the first record-46 expansion-output boundary. Deferred items include:

- Tighe visual/hardware acceptance of Build 0204 enemy appearance.
- Full 0x41DAE/0x45DFA sibling block coverage for records 57/96/140 and other actor groups.
- Stage sub-phase / level-reset progression divergence.
- Spurious/stale record 132 fireball/sphere root.
- Rolling black bar / VBlank cadence.
- FG/map horizontal streaming, sky reset, HUD/header, D00298, continue/game-over.

## Open / Closed Issues Impact

- Open issues touched: OPEN-017, OPEN-024
- New issues opened: NONE
- Issues closed: NONE
- Issues intentionally deferred: OPEN-018, D00298, PC080SN/FG/sky/black-bar/collision/continue-game-over work

## KNOWN_FINDINGS Impact

Option C: KF-063 was refined. Build 0204 resolves the Build 0203 empty-output sub-cause: the `0x3D254` engine reached the shared patched `arcade_pc 0x03C950` path, whose Genesis helper only handled PC080SN C-window text. The corrected helper now preserves original non-C-window PC090OJ scratch/mirror writes.

## STOP

STOP triggered: **NO**.
