# Cody — Build 0420/0421 Background Native Optimization

> **Status correction:** Build 0420 is rejected for the illegal-instruction
> crash documented below. Build 0421 is also rejected: its four-cell Plane-A
> grouping crossed the live ring front and corrupted Segment-0 visuals. Build
> 0422 corrects that assumption; see
> `Cody_build0421_segment0_regression_root_cause.md`.

Date: 2026-10-13  
Baseline: accepted Build 0419  
Historical result: rejected Build 0421 complete family

## Numbering note

Build 0420 was correctly preserved by the Makefile before its gameplay-entry
gate label ran. That gate exposed an illegal 68000 `TST.L A0` at Genesis PC
`0x070A72` in the new lookup leaf. The instruction only tested whether a record
pointer was zero; Build 0421 replaces it with legal `CMPA.L #0,A0`. Build 0420
was not overwritten or reused. Build 0421 is the corrected test candidate.

## Semantic cut and generated representation

Arcade-owned live source pointers, camera/front state, ring unwrap, descriptor
selection, active package, and residency remain runtime decisions. The removed
chip tail is repeated raw Plane-A metatile payload interpretation after a live
descriptor has already selected its invariant metatile pointer.

`gen_pc080sn_native_metatiles.py` scans the authoritative reconstructed
`maincpu.bin` descriptor vocabulary and emits:

- a pointer-indexed 392,702-byte table;
- 4,733 fixed 64-byte records;
- each record contains 16 masked tile identities followed by 16 fully expanded
  collision words.

Uniform collision sentinels are expanded offline. The runtime still converts
the live descriptor attribute and performs the existing active-package
code-to-slot lookup. No second tile, palette, or residency identity was added.
The generated report is
`build/rastan-direct/pc080sn_native_metatile_report.json`.

The Makefile generation command is equivalent to:

```text
python3 tools/translation/gen_pc080sn_native_metatiles.py \
  --maincpu build/regions/maincpu.bin \
  --index-output build/pc080sn_native_metatile_index.bin \
  --records-output build/pc080sn_native_metatile_records.bin \
  --report-output build/rastan-direct/pc080sn_native_metatile_report.json
```

The exhaustive verifier compares every generated tile and collision word with
the old maincpu semantics. Generated data is declared as a non-code symbol
range in the remap spec so the postpatcher does not decode payload bytes as
Genesis JSR/JMP instructions.

## Runtime changes and structural cost

For one paired Plane-A/Plane-B vertical row event:

| Work | Build 0419 | Build 0421 | Reduction |
|---|---:|---:|---:|
| required logical cells | 128 | 128 | none |
| descriptor traversals/relocations | 128 | 20–21 | 83.6–84.4% |
| raw metatile/tile-block interpretations | 128 | 4–5 Plane-B groups | 96.1–96.9% |
| attribute conversions | 128 | 20–21 | 83.6–84.4% |
| package/residency lookups | 128 | 128 | none |

Plane A publishes four cells per selected metatile, reducing 64 descriptor
walks to 16. Plane B caches each selected 16-column descriptor group, reducing
64 walks to four or five depending on ring alignment. Both still publish every
one of the 64 required logical columns.

The shared generated Plane-A leaf is also used by name-only, fused
name/collision, and collision-only consumers. Their dynamic descriptor walks
remain where coordinates differ per cell, but raw metatile loads and collision
sentinel interpretation are removed. Selector-0 therefore keeps 64 descriptor
walks and 64 residency lookups while changing 64 raw metatile interpretations
to 64 bounded generated-record lookups.

No controlled cycle percentage is claimed; the earlier controlled timing route
did not arm and was not rebuilt. Expected performance direction is faster from
the exact structural reduction above.

## Correctness and gates

- native-record exhaustive equivalence: PASS (4,733/4,733 records);
- full-span model: PASS, including initial 64x64 seed, N/N+32, source rebase,
  trailing retention, independent Plane-B context, 32-row projection, dirty
  gather, and column DMA;
- transition-retention gate: PASS;
- VDP DMA boundary/alignment: PASS;
- canonical gate: PASS;
- gameplay-entry gate: PASS on corrected Build 0421 (240 post-entry frames,
  player control observed, zero bus/address/illegal/crash entries);
- mandatory 30-second Genesis NTSC trace: completed (1,798 frames);
- standing seven-epoch label: FAIL after epoch 0 PASS, unchanged standing gate
  status from the accepted baseline;
- full five-ROM Build 0421 family: PASS.

## Artifacts

All Build 0421 artifacts are 2,694,840 bytes.

| Artifact | SHA-256 |
|---|---|
| `rastan_direct_video_test_build_0421.bin` | `b127f7ef929424b1be41bb119a8f64d9e03a863ff4d4db58ec8d6dea4fb68327` |
| `rastan_direct_video_test_build_0421_c.bin` | `76ccb2834d88984be2b3b70ff6090dbb0373ba9681b2751d9471fa2f3ace401d` |
| `rastan_direct_video_test_build_0421_d.bin` | `5963edda2dae4ed63b6f5e1882db18ea21079a656630d7ac9a8e5bda9ed223ab` |
| `rastan_direct_video_test_build_0421_do.bin` | `3ca4f3b56eee6b3034ecc4d90660aefc7e56bb8254c23f9b93e6cfbaddb4e713` |
| `rastan_direct_video_test_build_0421_s.bin` | `8b822e56e788c1f838bb64406e3a5d5ef2cb5673774eb9e5fa80d177aa8e8fa4` |

## Closure decision

Background optimization is **NOT CLOSED**. Plane-B directional-column staging
still repeats attribute conversion and per-row tile-block access after its one
descriptor selection, and Plane-A horizontal/collision producers still perform
one dynamic descriptor selection per distinct logical cell. A short cost audit
is still justified before declaring those remaining operations immaterial.

Next step: **ADDITIONAL BACKGROUND OPTIMIZATION**. Scheduler Phase D/E was not
started and the worker remains in IRQ6.
