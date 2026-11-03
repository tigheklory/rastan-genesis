# Cody - Build 0202 Enemy Spawn / Sprite Visibility + Visual Issue Ledger

**Date:** 2026-07-17
**Type:** Runtime evidence + documentation only; build-if-bounded gate not satisfied
**Baseline main ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0200.bin`
**Baseline main SHA256:** `bdba9bab8c0377164a742bf39115f372d1d348aaa755b7bec2720937fc5b9663`
**Baseline comparison ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0201.bin`
**Baseline comparison SHA256:** `7c89e96ddbb5070c4b6bf45aaca80d639e2ea6127514fe5c06c3c4cc0cf238b5`
**Scope:** Document Tighe's Build 0200/0201 visual findings and perform a bounded arcade-vs-Genesis enemy/sprite visibility comparison. No source/spec/tool/Makefile/ROM/invariant changes. No build. No black-bar, FG streaming, sky-reset, HUD/header, or PC090OJ renderer rewrite work.

## Phase 0

Relevant priors loaded: KF-047 (PC090OJ changed-record candidate derivation), KF-048 (configurable PC090OJ mirror count), KF-049 (record-count floor / player anchor), KF-050 (player sprite equivalence at safe caps), KF-051 (spurious low-record duplicate suppression), KF-052/KF-053/KF-054 (VINT/sprite-prep budget and ordering), KF-057/KF-058 (input/action-state restoration), and KF-059 (Build 0200 jump/fall arc-pointer relocation).

Task classification: **EXTENDING**. Open issues touched: OPEN-017 and OPEN-024. Closed issues touched: none. No contradiction of a CONFIRMED/STRONG finding was detected.

Architecture compliance: **CONFIRMED**. The task collected evidence only. It did not add a Genesis-owned lifecycle, forced enemy records, forced SAT entries, bypass spawn logic, or alter rendering architecture.

## Tighe Visual Verification

Tighe's manual BlastEm review of Build 0200/0201 confirms the movement/control/jump/fall sub-issue is resolved enough to mark that sub-thread closed:

- Rastan movement is live.
- Left/right control works.
- Attack works.
- Jump/fall behavior is no longer stuck at the top after held jump.
- Scrolling gameplay is live.

OPEN-017 remains open because the broader gameplay/visual thread is not closed.

## Current Visual Issue Ledger

Recorded from Tighe's Build 0200/0201 visual review:

- Rolling black bar remains and gets larger during scrolling; not investigated here.
- No enemies appear; this was the primary investigation target.
- A fire-sword/fireball/sphere-like object appears spinning in the ground; it is not present in the original arcade at the matched point.
- Horizontal scrolling still fails to load/update new foreground/map content correctly; not investigated here.
- When the sky palette changes from blue to light violet, Rastan resets to the beginning of the stage; recorded as a separate progression/reset symptom.
- Header/HUD sprites are incomplete; no HUD/header changes were made.

## Evidence Artifacts

Trace directory:

- `states/traces/build0202_enemy_spawn_visual_ledger/`

Files produced/used:

- `enemy_spawn_trace.lua`
- `arcade_states.csv`
- `arcade_records.csv`
- `arcade_object_writes.csv`
- `arcade_summary.txt`
- `genesis_states.csv`
- `genesis_records.csv`
- `genesis_sat.csv`
- `genesis_object_writes.csv`
- `genesis_summary.txt`

Run parameters:

- Original arcade: `platform=arcade`, `frames=5200`, `right_start=700`, exit `0`.
- Build 0200 Genesis: `platform=genesis`, `frames=5200`, `right_start=700`, exit `0`.

The Lua write taps did not capture the later runtime PC090OJ writer PCs; they only caught the early arcade object-RAM clear at `runtime/arcade PC 0x03AD48`, and caught no Genesis mirror writes. Therefore writer-PC provenance is **not** claimed from this trace. The reliable evidence from this pass is the sampled object/mirror/SAT state.

## Matched Gameplay State

Both original arcade and Build 0200 reached gameplay state `2/3/0` with equivalent player and scroll values in the sampled window. Matching was performed by state/player/scroll, not absolute frame.

Early gameplay match:

| Source | Frame | State | Player X/Y | FG scroll X/Y | BG scroll X/Y |
|---|---:|---|---|---|---|
| Arcade | `650` | `2/3/0` | `0x0020/0x0070` | `0x0001/0x0149` | `0x0000/0x0149` |
| Build 0200 | `570` | `2/3/0` | `0x0020/0x0070` | `0x0000/0x0149` | `0x0000/0x0149` |

Later gameplay match:

| Source | Frame | State | Player X/Y | FG scroll X/Y | BG scroll X/Y |
|---|---:|---|---|---|---|
| Arcade | `940` | `2/3/0` | `0x00A0/0x0070` | `0x01E6/0x0149` | `0x01F3/0x0149` |
| Build 0200 | `830` | `2/3/0` | `0x00A0/0x0070` | `0x01E7/0x0149` | `0x01F4/0x0149` |

## Arcade First Enemy/Actor Evidence

At the early matched point, original arcade PC090OJ object RAM already contains non-player actor records that Build 0200 does not mirror.

Arcade frame `650`, record `46`:

```text
record=46 w0=0000 yraw=0061 code_raw=0276 xraw=0028 code=0276 approx_screen=(264,135)
```

Arcade frame `940`, record `46`:

```text
record=46 w0=0000 yraw=<sampled> code=0275 approx_screen=(128,135)
```

At the same later matched point, the arcade also contains visible composite actor/body groups in records `190..227` with codes in the `0x004B..0x006D` family. Build 0200 does not contain corresponding records at those indices in the matched snapshots.

## Genesis Matched Point

At Build 0200 frame `570` and `830`, the matched Genesis mirror contains:

- canonical player records `120/121/124/125/126/128/129/130/131`, represented and staged to SAT;
- small terrain/static records such as `17/22/23/24/25`, represented and staged;
- a spurious top-row `0x03E8..0x03F5` cluster at records `30..43`, not represented;
- record `132` cycling around `0x09D9..0x09DB`, represented in SAT slot 16;
- no record `46` equivalent to arcade record `46`;
- no matched record `190..227` composite actor group.

Build 0200 frame `830` represented/active count: `0x0011 / 0x0011` (`17 / 17`).

## First Divergence

The first proven divergence is before Genesis decoder/SAT/tile/palette visibility:

- Original arcade object RAM has expected non-player actor/enemy records at matched gameplay state.
- Build 0200's `pc090oj_object_ram` mirror does not contain the corresponding records at that matched state.
- Therefore the missing enemy is **not proven** to be a Genesis SAT cap, tile residency, palette, or final visibility issue in this pass.

The trace does not yet prove whether the root is:

- spawn routine not reached;
- spawn condition/progression/camera trigger mismatch;
- enemy WRAM state not created;
- enemy WRAM state created but PC090OJ write missing;
- PC090OJ write route not mirrored;
- writer/provenance hidden by the current trace method.

Primary enemy classification: **I - More evidence needed**.

No Build 0202/0203 was produced because the build gate requires a specific translation error and patch boundary. This pass narrowed the boundary to the PC090OJ object-source/mirror layer but did not identify a bounded source fix.

## PC090OJ Chain Status

For the first arcade actor/enemy record (`record 46`, code `0x0276`/`0x0275`):

| Stage | Result |
|---|---|
| Original arcade spawn/state routine | Not identified in this trace |
| Enemy WRAM object/state | Not identified |
| Arcade PC090OJ object RAM | Present (`record 46`; later composite groups also present) |
| Genesis PC090OJ mirror | Corresponding record absent at matched state |
| Candidate/dirty marking | Not reached for the missing record |
| Decoder representation | Not reached for the missing record |
| SAT staging | No enemy SAT entry for the missing record |
| Tile residency/palette | Not reached for the missing record |
| Final visible sprite | Missing |

## Fireball/Sphere Status

The ground-spinning sphere/fireball observed by Tighe corresponds to a represented Genesis SAT entry, not to a matched arcade enemy:

```text
Build 0200 SAT slot 16
record=132
code cycles around 0x09D9/0x09DA/0x09DB
SAT position approx x=236, y=196
SAT word2 sample 0xC440 -> palette line 2, tile 0x440
```

Original arcade record `132` is zero in the matched gameplay samples.

Fireball/sphere classification: **B - stale/spurious PC090OJ record**.

The exact producer/root of record `132` was not fixed here. It may be related to stale record lifetime or producer over-copy, but this task did not identify a safe patch.

## Raw Literal / Copied-ROM Pointer Audit

A raw-literal or copied-ROM pointer audit was **not** performed beyond the proven comparison boundary because the active enemy/spawn writer path was not identified. Broadly searching and patching potential enemy/spawn paths would violate the task's bounded-build rule.

## Build Gate Decision

Build allowed only if a bounded enemy translation error is proven: **NO**.

Build 0202 produced: **NO**.
Build 0203 produced: **NO**.

## Recommended Next Step

Run a narrower writer-provenance trace anchored on the first matched arcade actor record:

- Original arcade: watch PC090OJ `HW_ADDRESS 0x00D00170..0x00D00177` (`record 46`) and the later composite record ranges around `0x00D005F0..0x00D0071F` (`records 190..227`) during the frame-650/frame-940 matched window.
- Build 0200: watch the corresponding Genesis mirror range `pc090oj_object_ram + record*8` and raw `HW_ADDRESS 0x00D00170..` to distinguish missing producer, dropped raw write, or missing route.
- Also watch candidate bit and `pc090oj_mirror_dirty` for the same records.

This should produce the writer PC(s), allowing an active-path raw-WRAM literal / data-pointer / PC090OJ route audit without broad search.

## Open / Closed Issues Impact

Open issues touched: OPEN-017 and OPEN-024.

New issues opened: none.

Issues closed: none. The movement/control/jump/fall **sub-issue** within OPEN-017 is marked resolved by Tighe visual verification, but OPEN-017 remains open.

Issues intentionally deferred: black bar, 60 Hz/timing, FG streaming, sky-reset/progression reset, HUD/header sprites, full PC090OJ sprite closure, and the exact record-132 producer/root.

## KNOWN_FINDINGS Impact

Option A - no new finding to index. This pass records evidence and narrows the enemy boundary, but it does not prove a durable root cause or a safe fix.

## STOP

STOP triggered: **YES (bounded-build gate)**. The enemy absence was narrowed to object-source/mirror divergence, but the exact spawn/writer route was not proven, so no implementation/build was authorized.
