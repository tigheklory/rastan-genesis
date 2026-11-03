# Cody - PC090OJ Arcade-vs-Genesis Player Sprite Identity / Lifecycle Trace

**Date:** 2026-07-13  
**Type:** Runtime evidence / analysis-first boundary trace  
**Primary Genesis ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0163.bin`  
**Build 0163 SHA256:** `6f6efa750a004e5f74d365eb0d43119e7e88456ae44abc477237af93725171c5`  
**Accepted build policy:** Build 0160 remains accepted unless Tighe explicitly accepts a later build.  
**Scope:** Original arcade Rastan vs Genesis Build 0163 PC090OJ player-sprite identity/lifecycle during early `ROUND 1` / first active gameplay. No source/spec/tool/ROM/build/invariant changes. No collision, scroll, Exodus, returning-title, VINT, palette, PC080SN/FG_SRC, hardcoded sprite, hardcoded SAT, or second-renderer work.

## Baseline

Build 0163 is carried in as a preserved visual-test candidate, not an accepted fix and not rejected. Its temporary forced gameplay sprite tile-refresh source is still present in `apps/rastan-direct/src/pc090oj_hooks.s`; this task did not modify or revert it.

Relevant settled input from prior notes:

- `docs/design/Cody_build0162_vs_0163_ab_comparison.md`: Build 0163 mechanically forces represented gameplay sprite slots to requeue tile DMA, but the visual result remains inconclusive/masked.
- `docs/design/Cody_build0163_visual_result_exodus_scroll_boundary.md`: Player/Rastan remains absent or quickly removed/dies visually; scroll and Exodus are deferred confounders.
- `docs/design/Andy_build0163_force_gameplay_sprite_tile_refresh.md`: Build 0163 changed only the gameplay-gated sprite tile residency decision; it did not alter SAT placement, decode, palette, collision, PC080SN, or player/camera logic.
- `docs/design/Cody_pc090oj_gameplay_representation_activation.md`: current PC090OJ candidate/representation plumbing accepts and represents every record the current decoder accepts in the stable sampled gameplay window.
- `docs/design/Cody_pc090oj_gameplay_tile_dma_vram_residency.md`: records `64/65` with codes `0x0513/0x0512` were represented in a later stable Build 0162 window, but VDP-visible VRAM/SAT readback remained unproven.
- `docs/design/Cody_build0162_vint_timing_trace_classification.md`: steady gameplay VINT service is not the active blocker.

## Phase 0

Relevant priors from `KNOWN_FINDINGS.md`: KF-010 (staging/VDP commit model), KF-011 (arcade VBlank owns progression), KF-015 (scroll model context), KF-026 (PC090OJ runtime write surface needs runtime evidence), KF-032 (raw copied hardware writes must route through staging), KF-036/KF-039 (mapped WRAM lessons), and KF-043 (sprite palette context).

Rediscovery Hazard HIGH findings touched: VBlank ownership, PC090OJ staging/representation, raw hardware routing, mapped work-RAM discipline. No contradiction of a CONFIRMED or STRONG finding was detected.

Task classification: **EXTENDING**. This extends OPEN-017 / OPEN-024 / OPEN-001 gameplay sprite bring-up after Build 0163.

Open/Closed issues touched: OPEN-001, OPEN-017, OPEN-024. OPEN-018 context only. No closed issue was reopened.

Architecture compliance: **CONFIRMED**. The arcade code remains the program. This task only observed original arcade hardware records and Genesis helper/staging records; it introduced no Genesis-owned lifecycle, hardcoded sprite, second renderer, or source behavior change.

## Evidence Inspected

Required static/source files inspected:

- `RULES.md`
- `ARCHITECTURE.md`
- `AGENTS_LOG.md`
- `OPEN_ISSUES.md`
- `KNOWN_FINDINGS.md`
- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/pc090oj_assets.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/out/symbol.txt`
- `build/maincpu.disasm.txt`
- `build/genesis_postpatch.disasm.txt`
- `build/rastan-direct/address_map.json`

Runtime evidence produced:

- Trace directory: `states/traces/player_sprite_identity/player_sprite_identity_20260713_160520/`
- Arcade script: `capture_arcade_player_sprites.lua`
- Genesis script: `capture_genesis_player_sprites.lua`
- Arcade timeline: `arcade_timeline.csv`
- Genesis timeline: `genesis_timeline.csv`
- Arcade PC090OJ records: `arcade_pc090oj_records.csv`
- Genesis PC090OJ mirror records: `genesis_pc090oj_records.csv`
- Genesis record maps: `genesis_pc090oj_maps.csv`
- Genesis staged SAT: `genesis_staged_sat.csv`
- Reduction script: `reduce_player_sprite_identity.py`
- Reduced summary: `player_sprite_identity_summary.md` / `player_sprite_identity_summary.json`
- Focus tables: `arcade_player_cluster.csv`, `genesis_corresponding_frame_records.csv`

Both MAME runs exited with status `0`.

## Trace Method

The arcade run used original `rastan` / Rastan (World Rev 1) under MAME, with scripted coin/start inputs matching prior intro-drop traces. It dumped PC090OJ hardware records from `HW_ADDRESS 0x00D00000 + record*8` during the first active gameplay window.

The Genesis run used Build 0163 under the MAME Genesis driver, with scripted `P1 A` / `P1 Start` inputs matching prior Genesis entry traces. It dumped:

- `pc090oj_object_ram` at Genesis-WRAM `0x00FF69B0 + record*8`
- `pc090oj_candidate_bitset`
- `represented_records`
- `record_to_slot`
- `staged_sprite_sat`
- player/camera state fields used by prior traces

Address mapping note: no arcade-to-Genesis code-PC arithmetic was used as proof in this report. The comparison is between original arcade hardware records (`HW_ADDRESS 0x00Dxxxxx`) and Genesis WRAM mirror/staging symbols from `out/symbol.txt`. Any future write-PC provenance task must map writer PCs through `build/rastan-direct/address_map.json`.

## Logical Window Alignment

| Runtime | First active state | Frame | State | Player X/Y |
|---|---:|---:|---|---|
| Original arcade | yes | `307` | `2/3/0` | `0x0020/0x0030` |
| Genesis Build 0163 | yes | `534` | `2/3/0` | `0x0020/0x0030` |

The comparison uses active-relative deltas, not absolute emulator frame numbers.

## Arcade Player Sprite Fingerprint

Original arcade first emits a player/Rastan PC090OJ body cluster at active+2:

| Active delta | Frame | Record | HW address | Word0 | Y | Code | X | Player X/Y |
|---:|---:|---:|---:|---:|---:|---:|---:|---|
| `+2` | `309` | `128` | `0x00D00400` | `0x4003` | `0x0031` | `0x010B` | `0x0020` | `0x0020/0x0030` |
| `+2` | `309` | `129` | `0x00D00408` | `0x4003` | `0x0031` | `0x010C` | `0x0010` | `0x0020/0x0030` |
| `+2` | `309` | `130` | `0x00D00410` | `0x4003` | `0x0041` | `0x010D` | `0x0020` | `0x0020/0x0030` |
| `+2` | `309` | `131` | `0x00D00418` | `0x4003` | `0x0041` | `0x010E` | `0x0010` | `0x0020/0x0030` |

The fuller falling/landing player cluster appears by active+30 and persists through active+120:

| Delta | Player records/codes |
|---:|---|
| `+30` | rec `120/121/124/125/126/128/129/130/131`, codes `009E/009F/008E/008F/0090/010B/010C/010D/010E` |
| `+60` | same record set/codes, with Y tracking the landing/fall state |
| `+90` | same record set/codes |
| `+120` | rec `120/121/124/125/126` remain `009E/009F/008E/008F/0090`; rec `128..131` animate to `0076/0077/0078/0079` |

Why this is treated as player/Rastan: the records are high PC090OJ records near the player global position (`player_x=0x0020`), use coherent `word0=0x4003`, track the player Y/fall/landing movement, and form a multi-tile body cluster. This is runtime arcade intent evidence, not static table inference.

## Genesis Build 0163 Corresponding State

At the same logical delta (active+2, Genesis frame `536`), Build 0163 has no matching high-record player cluster and none of the arcade player-cluster codes appear anywhere in the captured Genesis early-active window.

Genesis active+2 nonzero records are low records `22..45`, mostly HUD/title-like or offscreen filler:

| Record range | Codes | Genesis decoder result |
|---|---|---|
| `22..25` | `002B/002D/0031/002C` | accepted and represented |
| `26..33` | `002A` | rejected `offscreen_y` |
| `34..36` | `0039/0048/0046` | accepted and represented |
| `37..42` | `002A` | rejected `offscreen_y` |
| `43..45` | `0039/0049/0047` | accepted and represented |

Genesis records `120..131` are never nonzero in the Build 0163 capture. Matching arcade player-cluster codes present anywhere in the Genesis capture:

```text
0076: 0, 0077: 0, 0078: 0, 0079: 0,
008E: 0, 008F: 0, 0090: 0, 009E: 0, 009F: 0,
010B: 0, 010C: 0, 010D: 0, 010E: 0
```

Therefore the Genesis failure is upstream of Genesis decoder accept/reject, representation, SAT placement, and tile DMA for the player: the arcade-equivalent player records are missing from `pc090oj_object_ram`.

## Genesis Represented / SAT Result

Build 0163 does represent other records at the corresponding frame. Example active+2 accepted records:

| Genesis record | Code | Slot | Notes |
|---:|---:|---:|---|
| `22` | `002B` | `00` | accepted/represented |
| `23` | `002D` | `06` | accepted/represented |
| `24` | `0031` | `07` | accepted/represented |
| `25` | `002C` | `08` | accepted/represented |
| `34` | `0039` | `09` | accepted/represented |
| `35` | `0048` | `0A` | accepted/represented |
| `36` | `0046` | `0B` | accepted/represented |
| `43` | `0039` | `0C` | accepted/represented |
| `44` | `0049` | `0D` | accepted/represented |
| `45` | `0047` | `0E` | accepted/represented |

This supports that the retained PC090OJ representation path is alive, but it is representing the wrong available record set for the player question.

## Codes `0x0512` / `0x0513` Identity

In this early active/fall trace:

- Original arcade emits zero records with codes `0x0511/0x0512/0x0513/0x0516`.
- Genesis Build 0163 emits zero records with codes `0x0511/0x0512/0x0513/0x0516`.

Conclusion: records `64/65` with codes `0x0513/0x0512` from the older stable Build 0162 sampled window are **not proven to be the early-fall Rastan/player fingerprint**. The runtime arcade fingerprint for early fall is the `0x008E/0x008F/0x0090/0x009E/0x009F/0x010B..0x010E` cluster, later animating `0x010B..0x010E` to `0x0076..0x0079`.

## Rejected `0x002A` Meaning

`0x002A` records appear in both arcade and Genesis captures as offscreen/filler records. In Genesis, the current decoder rejects the sampled `0x002A` records as `offscreen_y` (for example raw Y `0x0110` -> decoded Y `264`, or raw Y `0x0000` -> decoded Y `-8` with opaque span above the viewport).

These are not the arcade player cluster identified above. The `0x002A` rejection is not the cause of missing Rastan/player in this early-fall comparison.

## Quick Death / Removal Timing

Genesis player state exists at the same first-active point:

- Genesis active+0: player `0x0020/0x0030`
- Genesis active+30: player `0x0020/0x005C`
- Genesis active+60: player `0x0020/0x0070`, move `0x0002`
- Genesis active+90 onward: flags include `0x0200`, move clears to `0x0000`

The player PC090OJ body records are already missing at active+2 and active+30, before the later suspicious `0x0200` flag state appears. Therefore the immediate PC090OJ player-sprite blocker is **not** that a generated player sprite was killed/removed after representation. The player state exists, but the arcade-equivalent PC090OJ records are not produced into Genesis `pc090oj_object_ram`.

Collision/death remains a separate confounder for gameplay behavior and must not be fixed in this task.

## Classification

Primary classification: **A - Player record missing from Genesis object_ram**.

Arcade has a concrete player PC090OJ fingerprint during early fall. Genesis Build 0163 does not produce those records, and the matching codes are absent across the captured Genesis early-active window.

Not B: there is no matching Genesis player record for the decoder to reject.  
Not C: the matching player record does not reach SAT, so wrong graphics/source/layout is not yet the first proven divergence.  
Not D: player identity path is not proven correct; it fails before representation.  
Not E: player state exists before the later suspicious death/removal state; missing PC090OJ player records precede that.  
Not F: the arcade player fingerprint and Genesis absence are sufficient for this boundary.

## First Proven Divergence

First proven divergence: **active+2**.

- Arcade frame `309` has player records `128..131` at `HW_ADDRESS 0x00D00400..0x00D00418`, codes `0x010B..0x010E`.
- Genesis Build 0163 frame `536` has no records `128..131`, no codes `0x010B..0x010E`, and no other matching arcade player-cluster code anywhere in the capture.

This is an object-RAM production divergence, not a SAT or tile-DMA divergence.

## Build Decision

Build produced: **NO**.

Reason: Classification A is proven at the object-RAM boundary, but the exact missing producer PC/path is not yet proven. The prompt allows Build 0164 only if A/B/C proves a small exact fix. A missing player record without the writer/provenance path is not yet a safe implementation boundary.

No source change is authorized from this evidence alone.

## Recommended Next Boundary

Recommended next task: **PC090OJ player-cluster producer provenance trace**.

Minimum specific trace:

- Original arcade write-watchpoints for `HW_ADDRESS 0x00D003C0..0x00D0041F` during active+0..active+30, logging writer PC, record index, word offset, value, and state/player fields.
- Genesis Build 0163 write-watchpoints for the corresponding mirror range `Genesis-WRAM 0x00FF6D70..0x00FF6DCF` (`pc090oj_object_ram + 0x03C0..0x041F`) plus raw `HW_ADDRESS 0x00D003C0..0x00D0041F`, logging whether writes are absent, raw/unrouted, or routed to a different record range.
- Map all writer PCs through `build/rastan-direct/address_map.json` before proposing any source/spec change.

This should identify whether the missing player cluster is caused by an unhooked PC090OJ producer, a misrouted record-index calculation, a missing semantic-family conversion, or upstream arcade state not reaching the sprite producer.

## Open / Closed Issues Impact

Open issues touched:

- OPEN-001: gameplay graphics remain incomplete/incorrect.
- OPEN-017: gameplay bring-up and Build 0163 candidate context.
- OPEN-024: PC090OJ sprite subsystem missing player object records in this boundary.

New issues opened: NONE.  
Issues closed: NONE.  
Issues intentionally deferred: collision/player-death fix, scroll direction, Exodus loop, returning-title tile lifecycle, VINT, PC080SN/FG_SRC, palette, hardcoded sprites/SAT, second renderer, general PC090OJ rewrite.

## KNOWN_FINDINGS Impact

Option A - no new finding to index. This is strong build-specific boundary evidence, but the durable mechanism is not yet proven because the exact writer/provenance path is still unknown. A KF update should wait for the producer provenance trace or implementation proof.

## STOP

STOP triggered: **YES (implementation STOP)**. Evidence capture completed, but no safe bounded source change was proven.
