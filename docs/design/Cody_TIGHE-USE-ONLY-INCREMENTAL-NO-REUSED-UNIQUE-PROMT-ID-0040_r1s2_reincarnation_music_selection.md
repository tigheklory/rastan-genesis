# R1-S2 Re-In-Carnation music selection

Prompt: `TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0040`

Date: 2026-10-29
Agent: Cody

## Result

Build 0521 restores Re-In-Carnation for the direct R1-S2 derivative by changing the retained arcade stage-initialization request from command `0x25` to the already-supported command `0x27`. It does not add, regenerate, or duplicate either song.

The accepted normal Build 0521 ROM and prior accepted Build 0519 ROM are both exactly **4,054,712 bytes**. The R1-S2 derivative is also 4,054,712 bytes and differs from the normal Build 0521 ROM at exactly two bytes: the existing direct-start selector and the existing music-command immediate.

Build 0520 grew to 4,103,864 bytes because the build had regenerated unrelated audio assets instead of consuming the exact Build 0519 audio receipt. That build is preserved because its number was consumed, but it is rejected for this task and must not be used as the deliverable.

## Arcade-authoritative meaning

The original arcade paths establish that Re-In-Carnation was already a song identity in the game:

- Natural R1 transition producer `0x03A848` sets `A5+0x1394 = 1` and `A5+0x13AA = 9`.
- R1 sequencer `0x055DDC` reaches the substate-9 branch at `0x055F38`.
- At `0x055F68`, it executes `move.w #0x27,d0`.
- At `0x055F6C`, it calls the original sound queue at `0x03A0EC`, then advances to substate 10.
- Original queue/dispatch chain: `0x03A0EC` queue, `0x03A116` forced queue, `0x03A126` dispatcher, and PC060HA sender `0x03F084`.

The original Z80 table at audiocpu `0x2300` independently identifies the relevant commands:

| Command | Table entry | Descriptor | Count | Meaning |
|---|---:|---:|---:|---|
| `0x19` | `0x2332` | `0x2DF0` | 8 | Aggressive original song identity |
| `0x25` | `0x234A` | `0x29C0` | 2 | Appearance/transition semantics; Genesis compatibility maps it to Aggressive |
| `0x27` | `0x234E` | `0x32D0` | 6 | Re-In-Carnation original song identity |

The earlier `0x19` request at arcade `0x055E30` is gated by `A5+0x34`; the queue returns immediately when that gate is zero. It therefore does not replace the proven substate-9 `0x27` request.

## Semantic cut and removed chip tail

The sound semantic cut remains unchanged:

`retained arcade music producer -> retained queue/dispatcher -> native command publication -> generated Genesis Z80 dispatch`

The PC060HA hardware-write tail below arcade `0x03F084` is the chip-specific tail already replaced by a call to `z80_write_command`. This task does not emulate PC060HA, add a shadow device, poll scene state, or create a second music path. It corrects the command supplied by the direct-start producer while retaining the established native dispatcher.

The generated map and native sources already contain both semantic song mappings:

- `specs/audio_native_song_map.json`: `0x25 -> track 3` (Aggressive), `0x27 -> track 5` (Re-In-Carnation).
- `apps/rastan-direct/src/sound_comm.s` passes `0x27`; it only normalizes the established `0x25` appearance forms and maps `0x1E` to stop.
- The generated dispatch table already maps `0x27 -> track 5`.

Credit command `0x04` and credit behavior are unchanged.

## First divergence and correction

The direct-start builder changed the subround selector but bypassed the natural transition producer at arcade `0x03A848 -> 0x055F68`. Its retained stage initializer instead executed:

```text
arcade 0x050690: move.w #0x25,d0
arcade 0x050694: jsr    0x03A116
```

The current address map places that producer at Genesis runtime `0x0508A0`; the immediate command byte is ROM offset `0x0508A3`.

The Build 0519 baseline runtime trace proves the first divergence directly. At frame 388 the retained queue received `0x25` at runtime `0x03A320`, with caller return `0x0508AA`, and the Genesis Z80 began Aggressive at source `0x34BCF9`.

The correction is derivative-only:

| ROM offset | Normal | R1-S2 derivative | Purpose |
|---:|---:|---:|---|
| `0x0508A3` | `0x25` | `0x27` | Select already-present Re-In-Carnation through the retained queue |
| `0x05FF9F` | `0xFF` | `0xDF` | Existing R1-S2 direct-start selector |

`tools/translation/build_subround_variant.py` now validates the complete original instruction `303c0025` before applying the command correction. `tools/translation/verify_subround_variants.py` asserts both intended bytes and rejects any other ROM difference. The runtime audio gate now records retained queue producers and can require an expected command and source address.

Implementation source commit: `327d6c417102802150e19007ff3da212ce9b92fc` (`Restore R1-S2 direct-start music request`).

Exact tracked production-source receipt: `ca8b33340a4c6bc2f8bd754187b10826c1d79080`.

## No duplicated song and no ROM growth

The exact Build 0519 audio receipt was restored from:

`states/source_snapshots/build_0519_prompt0033/build0517_audio_payloads.tar.gz`

Receipt SHA-256:

`d46b283ec80848ac86736dce1b2974dd569d5d228ed36cf78f342438cf8b00e5`

The delivered ROM retains one Aggressive payload and one Re-In-Carnation payload at their existing addresses:

| Payload | ROM source | SHA-256 |
|---|---:|---|
| Aggressive intro | `0x34BCF9` | `070e5d6f317c10030f9f925a839d44e8d859c69bdc1d3b2246f9d0f8e84c80e0` |
| Aggressive loop | `0x34DF7D` | `66323cf3ea6289297741bfb74f867844571930bf37cb0a1107f5e5e2b46ec86b` |
| Re-In-Carnation intro | `0x35A4EC` | `4b26249d8739857c1755d11b1e038c6a41899ca4e34aca66fe3b7c5eb000c4bf` |
| Re-In-Carnation loop | `0x35B054` | `f373d7af749fb54d84d6ce466c4b28af7f7f025f2a292cd47c9b6f1aa80fa44a` |
| Native Z80 driver | existing driver | `3a5e0c27a692544de0c9f36f6f6472ee18f637c93277adc63e3e3a408c7a464c` |

Build-size and byte-difference proof:

- Build 0519 normal: 4,054,712 bytes.
- Build 0521 normal: 4,054,712 bytes.
- Build 0521 R1-S2: 4,054,712 bytes.
- Build 0519 normal versus Build 0521 normal: exactly four bytes differ, all Makefile-owned publication metadata: header checksum at `0x18E..0x18F` and crash build stamp at `0x3DD8DA..0x3DD8DB` (`0519 -> 0521`).
- Build 0521 normal versus Build 0521 R1-S2: exactly the two bytes listed above.

Therefore the music fix consumes zero additional ROM bytes and adds no second Re-In-Carnation asset.

## Validation

The Build 0521 canonical build passed the canonical gate, mandatory MAME trace, and all seven required standard variants. The build used the established receipt coverage delta `0x90000` for both standard and full-HUD coverage.

### Dynamic audio evidence

- Baseline direct start: `states/traces/prompt0040_build0519_r1s2_audio_baseline/`
  - observed command `0x25`
  - observed source `0x34BCF9` (Aggressive)
  - retained producer call site proved as runtime `0x0508A0`
- Build 0521 R1-S1 normal: `states/traces/prompt0040_build0521_r1s1_normal_audio/`
  - PASS
  - Aggressive remains selected through command `0x25`
  - zero bank mismatches
- Build 0521 R1-S2 direct: `states/traces/prompt0040_build0521_r1s2_direct_audio_validated/`
  - PASS
  - command stream includes `EF,04,29,27,1B,0B,0C`
  - required command `0x27`: observed
  - required Re-In-Carnation intro source `0x35A4EC`: observed
  - loop source `0x35B054`: observed
  - YM writes: 11,089
  - PSG writes: 127
  - banked reads: 23,220
  - bank mismatches: 0

### Natural-progression limitation

The normal ROM preserves the original `0x03A848 -> 0x055F68 -> command 0x27` path, and the normal ROM has no functional change beyond publication metadata. The existing automated natural-play route did not reach R1-S2: after 6,000 frames it stalled at player X `0x00A7`. It consequently did not dynamically observe the transition request. This is an automation coverage limitation, not evidence of an alternate music result.

Tighe should perform the requested final listening check by reaching R1-S2 through normal gameplay. The direct-start path, native dispatch, intro, loop, and command provenance are dynamically proven above; natural transition provenance is statically proven from original code.

## Delivered ROM family

All artifacts are preserved under `dist/rastan-direct/` and are 4,054,712 bytes:

| Artifact | SHA-256 |
|---|---|
| `rastan_direct_video_test_build_0521.bin` | `375ad212465e57557197ba2e6399f44ad395bcb2e0810a4a38fd7ae3a0a722b3` |
| `rastan_direct_video_test_build_0521_S1-2.bin` | `b2ce6df864d95aa6a0ccccf36bb30cbc192d3125da8a2053c751ed933c3ea350` |
| `rastan_direct_video_test_build_0521_c.bin` | `14fe0a7d8f8c1b91341415b760aa131dcb6c47e622fcbf93b15fa032a5643eaf` |
| `rastan_direct_video_test_build_0521_d.bin` | `fe50339650d8aced4b0cb260bfdc231cbe385a9cecda6a349be0542c1d081d5e` |
| `rastan_direct_video_test_build_0521_do.bin` | `c962f696296098e097e1cd37a528974066d226d54355a2e3383f5a5a1ea20e5c` |
| `rastan_direct_video_test_build_0521_full_hud.bin` | `ac2b766b5d35eefa3ae960c8b2cb9d6a5221ff3450aa1b8189331daf60c378ea` |
| `rastan_direct_video_test_build_0521_invincible.bin` | `7d7997bd0553e1de59c90d150fa28b73970f14c365fbf45519cf863f3d11b186` |
| `rastan_direct_video_test_build_0521_s.bin` | `370130a0a77e503ab410d8d059b7faa36f88821d69941c662788fe6454416889` |

Build counter: `0521`. Both consumed numbers 0520 and 0521 remain recorded; 0520 is explicitly rejected, and 0521 is the accepted candidate family.

## Final disposition

The error was selection, not missing music data. Build 0521 reuses the single existing Re-In-Carnation intro/loop through original command `0x27`, preserves Aggressive elsewhere, preserves credit behavior, and introduces no ROM growth.
