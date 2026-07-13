# Cody - PC090OJ Player-Cluster Producer Provenance Trace

**Date:** 2026-07-13  
**Type:** Runtime evidence + static provenance analysis only  
**Build under comparison:** Build 0163 candidate, `dist/rastan-direct/rastan_direct_video_test_build_0163.bin`  
**Build 0163 SHA256:** `6f6efa750a004e5f74d365eb0d43119e7e88456ae44abc477237af93725171c5`  
**Workspace branch / HEAD during this note:** `rastan-direct-proposal` / `77eb1bd`  
**Scope:** No source edits, no spec edits, no build, no ROM changes, no fix implementation. Evidence only for the missing gameplay Rastan/player PC090OJ cluster.

Address labels used below: `arcade_pc` = original arcade code PC, `runtime_genesis_pc` = translated Genesis runtime PC, `HW_ADDRESS` = arcade/Genesis hardware-visible bus address, `Genesis-WRAM` = Genesis work RAM address.

## Phase 0

Classification: **EXTENDING**. This continues OPEN-001 / OPEN-017 sprite representation work after the Build 0163 VINT/tile-refresh passes and the player sprite identity/lifecycle evidence.

Relevant priors loaded:

- KF-010 / KF-032 context: rendering must flow through staging / VBlank commit / VDP, not raw hardware writes.
- KF-036 context: copied arcade work-RAM addresses must be treated carefully through mapped/rebased work-RAM semantics.
- OPEN-017 context: PC090OJ object-mirror / SAT representation is active and under investigation.
- Build 0163 visual evidence: VINT service frequency was mechanically improved, but gameplay sprite identity remains wrong/missing.

Rediscovery-hazard findings touched: PC090OJ sprite staging/ownership and mapped work-RAM provenance. No contradiction of a CONFIRMED/STRONG finding was found.

Open issues touched: OPEN-001, OPEN-017, OPEN-024 as context. OPEN-015, collision/death, scroll, PC080SN/FG_SRC, palette, D00298, Exodus-only UI work, and hardcoded sprite/SAT work were intentionally deferred.

Architecture compliance: **CONFIRMED**. This task observes the arcade producer path and the Genesis helper/opcode-replacement path; it does not introduce a second renderer, bypass, diagnostic ROM, or Genesis-owned gameplay control flow.

## Evidence Inspected

Runtime trace directory:

`states/traces/player_cluster_producer_provenance/player_cluster_provenance_20260713_173756/`

Key files:

- `capture_arcade_player_cluster_provenance.lua`
- `capture_genesis_player_cluster_provenance.lua`
- `capture_genesis_player_cluster_all_writes.lua`
- `capture_arcade_player_cluster_source_blocks.lua`
- `arcade_player_cluster_writes.csv`
- `arcade_player_cluster_snapshots.csv`
- `arcade_source_block_writes.csv`
- `arcade_source_blocks_snapshots.csv`
- `genesis_player_cluster_writes.csv`
- `genesis_player_cluster_snapshots.csv`
- `genesis_object_ram_all_writes.csv`
- `genesis_source_blocks_snapshots.csv`

Static files inspected:

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/pc090oj_assets.s`
- `apps/rastan-direct/src/vdp_comm.s`
- `apps/rastan-direct/out/symbol.txt`
- `build/maincpu.disasm.txt`
- `build/genesis_postpatch.disasm.txt`
- `build/rastan-direct/address_map.json`
- `build/rastan-direct/rastan_direct_patch_manifest.json`
- `specs/rastan_direct_remap.json`

## Runtime Alignment

Original arcade active gameplay alignment:

- First active gameplay: frame `307`, state `2/3/0`, player `x=0x0020`, `y=0x0030`.
- Active+2: frame `309`.
- Active+30: frame `337`.

Genesis Build 0163 alignment:

- First active gameplay: frame `534`, state `2/3/0`, player `x=0x0020`, `y=0x0030`, scene `0x01`.
- Active+2: frame `536`.
- Active+30: frame `564`.

These windows are state-aligned enough to compare the initial gameplay player-cluster producer path. They are not proof of full gameplay parity.

## Original Arcade Provenance

The original arcade trace shows the player cluster exists in PC090OJ object RAM records `120..131`, including the expected high player records `128..131`.

At active+2:

| record | HW_ADDRESS | word0 | y | code | x |
|---:|---|---|---|---|---|
| 120 | `0x00D003C0` | `4003` | `0009` | `009E` | `0010` |
| 121 | `0x00D003C8` | `4003` | `0019` | `009F` | `0010` |
| 124 | `0x00D003E0` | `4003` | `0011` | `008E` | `0018` |
| 125 | `0x00D003E8` | `4003` | `0021` | `008F` | `0020` |
| 126 | `0x00D003F0` | `4003` | `0021` | `0090` | `0010` |
| 128 | `0x00D00400` | `4003` | `0031` | `010B` | `0020` |
| 129 | `0x00D00408` | `4003` | `0031` | `010C` | `0010` |
| 130 | `0x00D00410` | `4003` | `0041` | `010D` | `0020` |
| 131 | `0x00D00418` | `4003` | `0041` | `010E` | `0010` |

At active+30, the same record/code family remains present with advanced Y values:

| record | HW_ADDRESS | word0 | y | code | x |
|---:|---|---|---|---|---|
| 120 | `0x00D003C0` | `4003` | `0044` | `009E` | `0010` |
| 121 | `0x00D003C8` | `4003` | `0054` | `009F` | `0010` |
| 124 | `0x00D003E0` | `4003` | `004C` | `008E` | `0018` |
| 125 | `0x00D003E8` | `4003` | `005C` | `008F` | `0020` |
| 126 | `0x00D003F0` | `4003` | `005C` | `0090` | `0010` |
| 128 | `0x00D00400` | `4003` | `006C` | `010B` | `0020` |
| 129 | `0x00D00408` | `4003` | `006C` | `010C` | `0010` |
| 130 | `0x00D00410` | `4003` | `007C` | `010D` | `0020` |
| 131 | `0x00D00418` | `4003` | `007C` | `010E` | `0010` |

The hardware writes to `HW_ADDRESS 0x00D003C0..0x00D0041F` are reported by MAME write taps at `arcade_pc 0x041F82/0x041F84/0x041F86/0x041F88`. The local disassembly identifies these as the copy loop inside the `arcade_pc 0x041F5E` routine:

```asm
041F5E: lea     0x11B2(%a5),%a0
041F62: moveq   #18,%d0
041F64: lea     0x00D003C0,%a1
041F6A: bsr     0x041F7A
041F6E: lea     0x0170(%a5),%a0
041F72: moveq   #4,%d0
041F74: lea     0x00D002E0,%a1
041F7A: tst.w   (%a0)
041F7C: beq     0x041F8C
041F7E: move.w  (%a0)+,(%a1)+
041F80: move.w  (%a0)+,(%a1)+
041F82: move.w  (%a0)+,(%a1)+
041F84: move.w  (%a0)+,(%a1)+
041F86: subq.w  #1,%d0
041F88: bne     0x041F7A
```

Thus the original arcade producer path is:

- Source block A: `HW/mapped arcade work RAM 0x0010D1B2` (`%a5+0x11B2`) holds 18 records.
- Destination block A: `HW_ADDRESS 0x00D003C0`, records `120..137`.
- Source block B: `HW/mapped arcade work RAM 0x0010C170` (`%a5+0x0170`) holds 4 records.
- Destination block B: `HW_ADDRESS 0x00D002E0`, records `92..95`.

## Original Arcade Source-Block Evidence

The source-block trace confirms that original arcade `A5+0x11B2` is already populated with the player cluster when the copy routine emits records `120..131`.

At active+2, `0x0010D1B2` contains the same player records before copy:

| source index | address | word0 | y | code | x |
|---:|---|---|---|---|---|
| 0 | `0x0010D1B2` | `4003` | `0009` | `009E` | `0010` |
| 1 | `0x0010D1BA` | `4003` | `0019` | `009F` | `0010` |
| 4 | `0x0010D1D2` | `4003` | `0011` | `008E` | `0018` |
| 5 | `0x0010D1DA` | `4003` | `0021` | `008F` | `0020` |
| 6 | `0x0010D1E2` | `4003` | `0021` | `0090` | `0010` |
| 8 | `0x0010D1F2` | `4003` | `0031` | `010B` | `0020` |
| 9 | `0x0010D1FA` | `4003` | `0031` | `010C` | `0010` |
| 10 | `0x0010D202` | `4003` | `0041` | `010D` | `0020` |
| 11 | `0x0010D20A` | `4003` | `0041` | `010E` | `0010` |

Source-block writes in original arcade are concentrated in the `arcade_pc 0x0544xx..0x0547xx` family. Representative writers include:

- `arcade_pc 0x0545F2/0x054604/0x05462C/0x05464E` for source indices `0..1`.
- `arcade_pc 0x0544F6/0x054508/0x05450E/0x054530` for source indices `4..6`.
- `arcade_pc 0x05470C/0x05471E/0x054724/0x054746` for additional source-block rows.

These arcade PCs map through `build/rastan-direct/address_map.json` as `arcade_copy` into the current Genesis image. Example exact mappings:

| arcade_pc | map kind | runtime_genesis_pc |
|---|---|---|
| `0x0544F6` | `arcade_copy` | `0x0546F6` |
| `0x054508` | `arcade_copy` | `0x054708` |
| `0x05450E` | `arcade_copy` | `0x05470E` |
| `0x054530` | `arcade_copy` | `0x054730` |
| `0x0545F2` | `arcade_copy` | `0x0547F2` |
| `0x054604` | `arcade_copy` | `0x054804` |
| `0x05462C` | `arcade_copy` | `0x05482C` |
| `0x05464E` | `arcade_copy` | `0x05484E` |
| `0x05470C` | `arcade_copy` | `0x05490C` |
| `0x05471E` | `arcade_copy` | `0x05491E` |
| `0x054724` | `arcade_copy` | `0x054924` |
| `0x054746` | `arcade_copy` | `0x054946` |

This source-population side is now proven for original arcade intent, but not yet proven equivalent in Genesis Build 0163.

## Genesis Build 0163 Destination Evidence

The Genesis trace found **no writes** to the high player-cluster mirror range and no raw writes to the matching hardware range during active+0..active+30:

- `Genesis-WRAM 0x00FF6D70..0x00FF6DCF` = `pc090oj_object_ram` records `120..131`: `0` write events.
- `HW_ADDRESS 0x00D003C0..0x00D0041F`: `0` raw write events.

Genesis snapshots of records `120..131` at active+2 and active+30 are all filler-like:

```text
record 120..131: word0=0000 y=0100 code=0000 x=0100
```

The broad object-RAM write trace did show PC090OJ mirror writes, but only to low records:

| runtime_genesis_pc writers | records written | meaning |
|---|---:|---|
| `0x071BF4/0x071BF6/0x071BFA/0x071BFE` | `0..21` | `pc090oj_workram_block_sprites` / `.Lpc090oj_family_apply_record` writes |
| `0x071AC6/0x071AC8/0x071ACC/0x071AD0` | `30..43` | legacy `.Lpc090oj_emit_slot` path writes |

No write path in the captured active window wrote records `120..131`.

## Genesis Replacement Mapping

`build/rastan-direct/address_map.json` maps the original `arcade_pc 0x041F5E..0x041F96` range to a `patched_site` at `runtime_genesis_pc 0x04215E..0x042196`.

Exact address-map examples:

| arcade_pc | map kind | runtime_genesis_pc |
|---|---|---|
| `0x041F5E` | `patched_site` | `0x04215E` |
| `0x041F7E` | `patched_site` | `0x04217E` |
| `0x041F80` | `patched_site` | `0x042180` |
| `0x041F82` | `patched_site` | `0x042182` |
| `0x041F84` | `patched_site` | `0x042184` |
| `0x041F86` | `patched_site` | `0x042186` |
| `0x041F88` | `patched_site` | `0x042188` |

The generated replacement at `runtime_genesis_pc 0x04215E` is:

```asm
04215E: jsr 0x00071CB4    ; genesistan_pc090oj_hook_target_41f5e
042164: rts
```

`genesistan_pc090oj_hook_target_41f5e` calls `pc090oj_workram_block_sprites`:

```asm
genesistan_pc090oj_hook_target_41f5e:
    bsr pc090oj_workram_block_sprites
    rts
```

Current source for `pc090oj_workram_block_sprites` reads the same two source blocks, but assigns fixed low record numbers instead of deriving the destination records from the original hardware destination:

```asm
pc090oj_workram_block_sprites:
    lea     0x11B2(%a5), %a0
    moveq   #0, %d0          ; block A records 0..17 in Genesis mirror
    ...
    lea     0x0170(%a5), %a0
    moveq   #18, %d0         ; block B records 18..21 in Genesis mirror
```

This is not destination-faithful to the original arcade routine, where the same `A5+0x11B2` source block is copied to `HW_ADDRESS 0x00D003C0` (`record 120`) and the `A5+0x0170` block is copied to `HW_ADDRESS 0x00D002E0` (`record 92`).

## Genesis Source-Block Evidence

The Genesis Build 0163 source block corresponding to original arcade `A5+0x11B2` was empty in the aligned active window:

| source block | active+0 | active+2 | active+30 |
|---|---:|---:|---:|
| `Genesis-WRAM 0x00FF11B2` (`A5+0x11B2`) | `0/18` nonzero | `0/18` nonzero | `0/18` nonzero |
| `Genesis-WRAM 0x00FF0170` (`A5+0x0170`) | `4/4` sentinel-like | `4/4` sentinel-like | `4/4` sentinel-like |
| `Genesis-WRAM 0x00FF11FE` (historical offset check) | `0/18` nonzero | `0/18` nonzero | `7/18` nonzero, not the arcade player cluster |

The `A5+0x0170` Genesis values were consistently sentinel-like records such as `0080 0000 0000 0000`, unlike the arcade active+2 values `0003/0001...` in that block. The `A5+0x11FE` values at active+30 were garbage-looking mixed words, not the expected `0x009E/0x009F/0x008E/0x008F/0x0090/0x010B..0x010E` code family.

This means the destination mapping issue is real, but it is not sufficient as a standalone Build 0164 fix: the Genesis source block being copied is also not populated with the original arcade player-cluster records during the aligned active window.

## Classification

Primary classification: **F - more analysis needed**.

Reason: the trace proves a concrete replacement-path defect, but also proves that the Genesis source state feeding that replacement is empty/divergent in the aligned gameplay window. A destination-record correction alone would not safely restore the player cluster because the state-causality rule is not yet satisfied: the state that should exist at `A5+0x11B2` has not been shown to exist in Genesis.

Secondary proven defect: **C-class record-index/destination mapping defect** inside the `0x041F5E` replacement family.

- Original arcade `A5+0x11B2` -> `HW_ADDRESS 0x00D003C0` = records `120..137`.
- Original arcade `A5+0x0170` -> `HW_ADDRESS 0x00D002E0` = records `92..95`.
- Current Genesis helper routes these blocks to records `0..17` and `18..21`.

But this C-class defect is **not an implementation authorization by itself**, because the source block divergence remains unresolved.

## Required Questions Answered

1. Exact original arcade producer PCs: watchpoint-reported `arcade_pc 0x041F82/0x041F84/0x041F86/0x041F88`, corresponding to the copy body inside `arcade_pc 0x041F5E`.
2. Equivalent Genesis path: `arcade_pc 0x041F5E` is opcode-replaced at `runtime_genesis_pc 0x04215E` and calls `runtime_genesis_pc 0x071CB4` (`genesistan_pc090oj_hook_target_41f5e`) -> `pc090oj_workram_block_sprites`.
3. Genesis writes to mirror or raw hardware: mirror only, but low records `0..21`; no raw `HW_ADDRESS 0x00D003C0..0x00D0041F` writes were observed.
4. Source block: original arcade source `0x0010D1B2` is populated with the player cluster; Genesis `0x00FF11B2` is empty in the aligned active window.
5. Hook behavior: the helper does not clip high records after computing them; it never computes the high destination records. It hardcodes low record ranges via `d0=0` and `d0=18`.
6. Semantic-family implementation: the shared family exists and executes, but it is not destination-faithful for `0x041F5E`.
7. Record-index calculation: yes, the current helper collapses/remaps the original destination record bases.
8. High-index handling: high records `120..137` and `92..95` are ignored by this helper because fixed low ranges are used.
9. Missing player cluster explanation: supported in part by wrong destination mapping, but not fully explained because the Genesis source block is empty.
10. Quick death: not analyzed here; it is not needed to explain the player-cluster provenance gap and remains deferred.

## Recommended Next Boundary

Do **not** implement Build 0164 from this evidence alone.

Recommended next single diagnostic: trace the source-block population path for the original arcade and Genesis around `A5+0x11B2` before and during gameplay activation.

Minimum target:

- Original arcade writes to `0x0010D1B2..0x0010D241`, especially `arcade_pc 0x0544xx..0x0547xx`, through active+0..active+2.
- Genesis writes to `Genesis-WRAM 0x00FF11B2..0x00FF1241` in the same state window.
- Map the Genesis writer PCs through `address_map.json` and determine whether the copied arcade source-population routines execute, write to unmapped work RAM, write to the wrong base, or are skipped due state divergence.

After source-state causality is proven, separately audit the shared `pc090oj_workram_block_sprites` callers (`0x041DAE`, `0x041F5E`, `0x045DFA`) and make any destination-record correction per caller or with explicit destination-base semantics. Do not globally change the shared helper without proving the three original destination bases.

## Open / Closed Issues Impact

Open issues touched: OPEN-001, OPEN-017, OPEN-024.  
New issues opened: none.  
Issues closed: none.  
Issues intentionally deferred: collision/death, scroll, PC080SN/FG_SRC, palette, D00298, Exodus-only UI work, broad PC090OJ rewrite, hardcoded sprites/SAT, and any Build 0164 implementation.

## KNOWN_FINDINGS Impact

Option A - no new finding indexed in this task.

Rationale: this evidence identifies a strong candidate replacement defect and an upstream source-state divergence, but it intentionally stops before canonicalizing a durable root cause. A KNOWN_FINDINGS update should wait until the source-block population provenance resolves whether this is primarily a mapped-work-RAM/source-population failure, a per-caller destination-base replacement defect, or both.

## STOP Status

STOP triggered for implementation: **YES**. A Build 0164 fix is not safely placeable from this evidence alone because `Genesis-WRAM 0x00FF11B2` is empty where original arcade `0x0010D1B2` contains the player cluster. Evidence capture and documentation completed.
