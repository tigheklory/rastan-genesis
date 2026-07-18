# Cody - Build 0200 Jump/Fall Pending-Move Fix

**Date:** 2026-07-17
**Type:** Analysis-first implementation + Build 0200/0201 production
**Build context:** Build 0198 controllable baseline, Build 0199 mirror-192 comparison; Build 0200 main candidate; Build 0201 mirror-192 comparison.
**Scope:** Continue Andy's interrupted jump/fall investigation. Bounded byte-neutral data-pointer relocation only. No input-chain rewrite, no forced Y/state, no collision bypass, no rendering/PC080SN/PC090OJ logic change.

## Phase 0 / Recovery

Classification: **EXTENDING** (OPEN-017 gameplay/control progression). Relevant priors: KF-057 (input latch chain), KF-058 (action-state input-copy chain restored; mode semantics), KF-044/KF-039 class raw-literal relocation hazards, KF-051/KF-053 PC090OJ producer budget context, KF-056 TC0140SYT READY fix. No contradiction detected.

Recovered state before edits:

- Build counter: `199`.
- Rolling ROM: `apps/rastan-direct/dist/rastan_direct_video_test.bin`, SHA `65abbcb721dbb6d5b16df0379fd8f094dfc732510d1a584082ad64377105ef8b`, byte-identical to Build 0198.
- Build 0198: `dist/rastan-direct/rastan_direct_video_test_build_0198.bin`, SHA `65abbcb721dbb6d5b16df0379fd8f094dfc732510d1a584082ad64377105ef8b`.
- Build 0199: `dist/rastan-direct/rastan_direct_video_test_build_0199.bin`, SHA `bc592c5f68653ee70cde750d33730a66ba8425b55aca0a6bdb720fe7a0648ffe`.
- Build 0200/0201: absent before this task.
- Makefile default: `PC090OJ_MIRROR_RECORDS ?= 256`.
- Generated config before work: `PC090OJ_MIRROR_RECORDS = 256`.
- opcode_replace count before work: `191`.
- Andy/Fable uncommitted changes from Builds 0196/0198 were present and preserved.
- Andy partial jump trace directory preserved: `states/traces/jump0200/`.

Open issues touched: OPEN-017. Closed issues touched: none. OPEN-015 and unrelated rendering/hardware issues were not touched.

## Andy Partial Findings Preserved

Andy observed Build 0198 jump entering mode 2, then `A5+0x1336` freezing at `1`, `A5+0x1272` staying `1`, and Y rising then parking near the top. His active boundary was the pending-move flag `A5+0x1272`: when it is `1`, the branch near runtime `0x51564` skips the action-state dispatch and prevents the jump arc walker from advancing.

I preserved those traces and added a matched arcade-vs-Genesis frame trace under `states/traces/build0200_jump_fall_pending_move/`.

## Static Control Flow

Relevant disassembly and address-map facts:

- Runtime `0x51564` / arcade `0x51364`: `cmpi.w #1,%a5@(0x1272)`.
- Runtime `0x5156A` / arcade `0x5136A`: branch to runtime `0x516F0` when pending movement is set.
- Runtime `0x525C4`, `0x52632`, `0x52666`: jump/fall arc walkers increment `A5+0x1336`, read through pointer `A5+0x1332`, and eventually hit the `0xFF` sentinel to switch modes.
- Runtime `0x52350` / arcade `0x52150`: active jump setup writes the arc-table pointer into `A5+0x1332`.

The branch itself is arcade-faithful: both arcade and Genesis skip the arc walker while `A5+0x1272 == 1`. The bug is upstream: Genesis creates a huge vertical movement bucket, causing the skip to persist.

## First Arcade-vs-Genesis Divergence

Matched tap-jump trace, first mode-2 frame:

| Build | first mode 2 frame | pointer | arc index | `A5+0x1262` | `A5+0x1272` | Y |
|---|---:|---|---:|---:|---:|---:|
| Arcade | 821 | `0x0005B548` | 1 | `4` | 0 | 108 |
| Genesis 0198 | 822 | `0x0005B548` | 1 | `173` (`0x00AD`) | 0 initially, then 1 | 108 |

At frame 823 in Build 0198, `A5+0x1272` becomes `1`; `A5+0x1336` stays at `1`; the arc dispatch is skipped until the oversized bucket drains. This is classification **F**: a raw ROM data pointer literal in the active movement route still points to the wrong copied-ROM address. It manifests as C/B, but the root cause is F.

## Root Cause

The arcade jump arc table starts at arcade ROM `0x0005B548`:

```text
arcade maincpu[0x5B548] = FF FF 00 04 00 04 00 03 ...
```

In the Genesis copied-ROM layout, `address_map.json` identifies the copied arcade segment with `identity_offset = 0x200`, so arcade data `0x0005B548` lives at runtime Genesis `0x0005B748`.

Build 0198 still wrote the raw arcade literal `0x0005B548` into `A5+0x1332`. At runtime Genesis `0x0005B548` maps to arcade `0x0005B348`, whose bytes begin:

```text
runtime Genesis[0x5B548] = 00 AD 00 AD 00 AD 00 AD ...
```

Thus the arc walker read `0x00AD` instead of `0x0004`, loaded a huge vertical accumulator, and self-created the `A5+0x1272` pending-move state that blocks further arc advancement.

State causality:

1. Jump starts in action state `A5+0x10E8 = 2`.
2. Arcade setup writes an arc pointer to `A5+0x1332`.
3. In Genesis Build 0198, that pointer is not relocated to the copied-ROM table.
4. The walker reads wrong ROM bytes (`0x00AD`) into `A5+0x1262`.
5. Movement consumption sets `A5+0x1272 = 1` while the bucket drains.
6. The faithful branch at `0x51564` skips the arc walker.
7. `A5+0x1336` does not progress normally to the sentinel, so fall transition is delayed/stuck.

## Patch

Added 23 byte-neutral `opcode_replace` entries in `specs/rastan_direct_remap.json` for active jump/fall arc data-pointer literals and one compare immediate:

- `0x0005B516 -> 0x0005B716`
- `0x0005B548 -> 0x0005B748`
- `0x0005B570 -> 0x0005B770`
- `0x0005B5A2 -> 0x0005B7A2`
- `0x0005B5EC -> 0x0005B7EC`
- `0x0005B62E -> 0x0005B82E`

Example patched bytes:

```text
runtime 0x052350 / arcade 0x052150: 2B7C0005B5481332 -> 2B7C0005B7481332
runtime 0x0525C4 / arcade 0x0523C4: 0CAD0005B5161332 -> 0CAD0005B7161332
```

Patch type: allowed byte-neutral data-pointer relocation. No NOP/RTS/bypass. Arcade physics and branch flow unchanged.

Structured metadata updated:

- `specs/rastan_direct_remap.json`: opcode_replace entries + expectation `191 -> 214`.
- `tools/translation/postpatch_startup_rom.py`: canonical opcode_replace count `191 -> 214`; coverage unchanged at `0x18271C`.
- `tools/translation/verify_canonical_rom.py`: same canonical invariant update.
- Generated manifest/address map regenerated by the build.

A first release attempt showed the important invariant detail: byte-neutral opcode replacements increased patched-site count but did **not** change `total_genesis_bytes_covered`; the invariant was corrected to the observed canonical value before producing Build 0200.

## Builds

### Build 0200

- Config: `PC090OJ_MIRROR_RECORDS=256`.
- Path: `dist/rastan-direct/rastan_direct_video_test_build_0200.bin`.
- SHA256: `bdba9bab8c0377164a742bf39115f372d1d348aaa755b7bec2720937fc5b9663`.
- Size: `1,582,876` bytes.
- Counter: `200`.
- Gate: `GATE_PASS`.
- Release trace: `states/traces/rastan_direct_video_test_build_0200_mame_30s_20260717_142449/`.

### Build 0201

- Config: `PC090OJ_MIRROR_RECORDS=192`.
- Path: `dist/rastan-direct/rastan_direct_video_test_build_0201.bin`.
- SHA256: `7c89e96ddbb5070c4b6bf45aaca80d639e2ea6127514fe5c06c3c4cc0cf238b5`.
- Size: `1,582,876` bytes.
- Counter: `201`.
- Gate: `GATE_PASS`.
- Release trace: `states/traces/rastan_direct_video_test_build_0201_mame_30s_20260717_142509/`.

After Build 0201, rolling ROM/config were restored to Build 0200 / 256 without creating Build 0202:

- Rolling ROM SHA: `bdba9bab8c0377164a742bf39115f372d1d348aaa755b7bec2720937fc5b9663`, byte-identical to Build 0200.
- `apps/rastan-direct/out/pc090oj_config.inc`: `PC090OJ_MIRROR_RECORDS = 256`.
- Counter remains `201`.
- Dry-run canonical verifier on rolling ROM: `GATE_PASS` using counter-consistent next name `rastan_direct_video_test_build_0202.bin`.

## Validation

### ROM bytes

Build 0200, Build 0201, and rolling ROM all contain relocated pointer literals:

```text
0507DC: 2B7C0005B7EC1332
0516B8: 2B7C0005B7EC1332
0522DC: 2B7C0005B7A21332
0522E6: 2B7C0005B7701332
052350: 2B7C0005B7481332
05235A: 2B7C0005B7161332
052510: 2B7C0005B82E1332
0525C4: 0CAD0005B7161332
```

ROM table proof:

```text
runtime 0x0005B548 = 00AD00AD00AD00AD  (wrong copied location; no longer used)
runtime 0x0005B748 = FFFF000400040003  (correct relocated arc table)
```

### Jump traces

Validation traces:

- `states/traces/build0200_jump_fall_pending_move/validation/genesis0200_hold1.csv`
- `states/traces/build0200_jump_fall_pending_move/validation/genesis0200_hold40.csv`
- `states/traces/build0200_jump_fall_pending_move/validation/genesis0201_hold1.csv`

Post-fix tap-jump first mode-2 frame:

| Build | first mode 2 frame | pointer | arc index | `A5+0x1262` | `A5+0x1272` | Y |
|---|---:|---|---:|---:|---:|---:|
| Build 0200 | 822 | `0x0005B748` | 1 | `4` | 0 | 108 |
| Build 0201 | 821 | `0x0005B748` | 1 | `4` | 0 | 108 |

Post-fix behavior:

- The giant `0x00AD` vertical bucket is gone.
- `A5+0x1272` does not stick high in the sampled jump window.
- `A5+0x1336` advances through the arc and reaches index 18.
- Mode 3 transition occurs with Y=76, matching arcade apex state values.
- Hold-40 behaves like tap for the fixed bucket signature; held input no longer creates the stuck-at-top signature in the MAME trace.

Remaining observation:

- In this MAME harness, Build 0200/0201 advance the arc index roughly every other external frame during part of the jump while arcade advances every frame. The fixed pointer/accumulator/pending-flag mechanism is proven, but exact arcade-equivalent timing and landing feel still require Tighe/BlastEm visual verification and/or a later cadence investigation if visible jump timing remains off.

### Release trace / frontend

The standard no-input 30s MAME release traces completed for both builds. They are frontend/attract traces, not gameplay visual validation. They show no unmapped memory in the exit summaries and preserve the title/front-end execution ranges, but they do not prove Stage 1 visual details.

## Validation Items Not Autonomously Proven Here

The prompt requested broad visual validation (title/READY/gameplay/Rastan completeness/BG/FG/palette/enemy status/VINT rate/SAT count). This task autonomously proved the bounded jump/fall mechanism with MAME input traces and produced both numbered builds. It did not include a manual BlastEm visual pass. Therefore:

- Title/frontend: standard release trace completed; Tighe should still visually inspect.
- READY/gameplay reached: controlled input trace reaches gameplay/jump window; visual READY not screenshot-captured here.
- Tap/held jump: mechanism fixed in trace; Tighe should verify visual feel in BlastEm.
- Fall/landing: mode-3 transition is restored in trace; full landing visual behavior should be verified.
- Rastan visual completeness, BG/FG/palette, black bars, enemy status, represented/SAT count, VINT-service rate: not newly measured in this task; no source changes were made to those systems.

## Open / Closed Issues Impact

- Open issues touched: OPEN-017.
- New issues opened: none.
- Issues closed: none.
- Issues intentionally deferred: exact jump cadence/landing feel if still visually off, enemies/spawn, black bars/VINT budget, BG/FG/palette visual follow-up, real-hardware compatibility.

## KNOWN_FINDINGS Impact

Option B: new durable finding added as KF-059. This prevents rediscovery of the jump/fall bug as a held-input, collision, or pending-flag-clear defect.

## STOP

STOP triggered: **NO** for the bounded fix and builds. Residual visual/cadence validation remains for Tighe/next task.
