# Cody — Build 0390 Phase-1 Waterfall Regression

## 1. Phase 0

Baseline is Build 0390, counter 390. Tighe classified it PARTIAL / NOT ACCEPTED: Phase-2
Plane A is populated on entry, but the first Phase-1 waterfall loses substantial terrain.

This task extends KF-078. KF-072 remains the coordinate/publication prior. OPEN-028 (isolated
first-arrival stale names) and OPEN-029 (third-chain traversal) are separate and were not
investigated. The user-confirmed Flying Demon whole-death behavior closes former OPEN-027 as
CLOSED-020; no Flying Demon code was changed.

Rediscovery hazard: a full name table and zero resolver misses do not prove that the correct
residency package remains installed. Package identity, LUT mapping, staged names, and physical
patterns must be followed together.

## 2. Build 0390 user result

- Phase-2 initial Plane-A population: improved and preserved by this task.
- Phase-1, record-3 first-waterfall presentation: regressed.
- Builds 0388/0389 remain preserved and rejected.
- Palette, H25, third-chain traversal, final resolver, collision, and rope work are out of scope.

## 3. Exact Build-0390 production diff

The parent of commit `ed8bfb6` is the restored pre-0390 production source. Its complete relevant
diff contains one runtime-semantic graphics change:

| File | Function/boundary | Old behavior | Build-0390 behavior |
|---|---|---|---|
| `apps/rastan-direct/src/tilemap_hooks.s` | `genesistan_hook_pc080sn_descriptor_rebuild`, opcode replacement at original `0x055904`, canonical runtime patched site `0x055994`, canonical helper target `0x07254A` | rebuild descriptors only | unconditionally call `fg_boundary_install`, then rebuild descriptors |

`specs/rastan_direct_remap.json` only added `fg_boundary_install` to the required-symbol list.
The Makefile changed the frozen profile path from Build 0384 to Build 0390; both Build-0390 and
Build-0391 snapshots have SHA-256 `02d0122a7d9ea91040f24350d299772f7f37196957eaa7e9b2f627bd9e47e250`.
There was no compiler, package-selection, package-data, resolver, collision, or palette semantic
change in Build 0390.

## 4. First-waterfall identity

The user-facing first major waterfall is the generated record-3 waterfall epoch, not UI numbering
used by older section reports.

| Human area | Record | Selector | Semantic epoch | Stable package | Entry overlap package | Exit overlap package |
|---|---:|---:|---:|---:|---:|---:|
| first waterfall | 3 | 0 | 1 | 1 | 6 (`rope_to_waterfall`) | 7 (`waterfall_to_next_rope`) |

The intended record-2→3 sequence is package `0 -> 6 -> 1`. Package 6 preserves outgoing rope
identities while the waterfall enters. At logical source column 45,
`fg_boundary_transition_step` installs stable package 1. Later, record 3→4 installs package 7,
which retains all 224 selected waterfall identities until its own safe handoff.

## 5. Pre-0390 residency sequence

The existing natural arcade-owned progression harness was reused against Build 0386 `_c`.

| Frame | Record | Package | Scroll X/Y | Strip/group | Meaning |
|---:|---:|---:|---:|---:|---|
| 2645 | 0 | 0 | `0/0` | `1/0` | gameplay entry |
| 2746 | 1 | 0 | `0/0` | `0/0` | same stable epoch |
| 4141 | 2 | 0 | `360/261` | `0/0` | outgoing rope |
| 4960 | 3 | 6 | `362/261` | `0/0` | rope→waterfall overlap |
| 5436 | 3 | 1 | `506/348` | `1/11` | column-45 safe handoff |

Package 1 remains active after frame 5436.

## 6. Build-0390 residency sequence and first divergence

Build 0390 matches every pre-0390 event through frame 5436. At frame 5453 it diverges:

| Frame | Record | Package | Scroll X/Y | Strip/group | Epoch/DMA transitions | Result |
|---:|---:|---:|---:|---:|---:|---|
| 5436 | 3 | 1 | `506/348` | `1/11` | `3/3` | correct stable handoff |
| 5453 | 3 | **6** | `488/348` | `0/12` | **`4/4`** | ordinary rebuild restores obsolete entry-overlap package |

The active record does not change. The only Build-0390 runtime change capable of selecting the
record-mapped package during this ordinary descriptor rebuild is the new call at the `0x055904`
native helper. Thus the first divergence is the frame-5453 package-1→6 rollback.

## 7. `0x055904` install-event log

The bounded audit records every package-changing install on the natural route; same-package calls
are intentionally invisible because they perform no package/LUT/pattern transition.

| Frame | Record/selector | Old→new | Classification |
|---:|---:|---:|---|
| 2645 | `0/0` | `FFFF -> 0` | scene initialization |
| 4960 | `3/0` | `0 -> 6` | epoch boundary / overlap entry |
| 5436 | `3/0` | `6 -> 1` | proven column-45 overlap handoff |
| 5453 (0390 only) | `3/0` | `1 -> 6` | ordinary descriptor rebuild; erroneous reinstall |

Evidence is under `states/traces/build0390_waterfall_regression/`.

## 8. Missing-cell source/LUT/name/physical-slot proof

Stable package 1 contains all 224 authoritative selected waterfall identities. The obsolete
entry-overlap package 6 lacks 101 of those identities. Runtime LUT dumps prove that all sampled
entries below are correct at frame 5436 and become zero at frame 5453.

The foreground attribute is retained while the tile field is resolved. Therefore a missing LUT
entry publishes `0x6000` (tile 0) instead of `0x6000 | slot`.

| World cell | Source code | Exact pattern SHA-256 | Expected/stable slot | Stable staged word | 0390 active LUT after 5453 | Newly published word | Physical pattern in expected slot after package 6 |
|---|---:|---|---:|---:|---:|---:|---|
| row 36, col 45 | `0x028A` | `1e995a84adab399256abcb66d37dd631b8458b22afbb379e11f41a6ecb3ac3bb` | `0x0298` | `0x6298` | `0x0000` | `0x6000` | stable identity 852 remains; package 6 does not upload this slot |
| row 37, col 45 | `0x028E` | `716e685d239fc6c8a0b084017364875a0af239e78b9c72fb3fbc8159a36a43ac` | `0x0365` | `0x6365` | `0x0000` | `0x6000` | same identity 1038 is re-uploaded |
| row 38, col 46 | `0x0293` | `310d0f10a0d03d20a8da3ab02c5d4f243e6ff540ec7670fc023a198b0309ca41` | `0x035B` | `0x635B` | `0x0000` | `0x6000` | stable identity 831 remains; package 6 does not upload this slot |

Across the 101 lost waterfall identities, 45 expected slots receive the same physical identity and
56 receive no upload; zero are overwritten with another identity. The physical patterns are not
the first failure. The active code→slot mapping is cleared, so later edge publications emit tile 0.

## 9. Overlap-package and stale-name result

The overlap package is replaced at the correct time and then incorrectly restored. This is a
**premature/invalid overlap-package restoration after handoff**, not a premature stable install.

- stale-name/physical-slot churn: **NO** for the 101 missing waterfall identities;
- active-LUT loss: **YES** (`stable slot -> 0`);
- package rollback: **YES**, package `1 -> 6` at frame 5453;
- existing names: remapped by the installer, while subsequent streamed names for absent codes
  resolve to tile 0;
- producer miss counter at the sampled transition remains `2`; the decisive proof is the complete
  active-LUT dump, not the aggregate miss count.

## 10. Scene initialization versus steady streaming

Existing retained state provides the general discriminator:

- Direct scene/reseed selection writes `A5+0x013E` without passing through
  `fg_boundary_advance_segment`. Before the fresh fill, retained record differs from
  `fg_boundary_active_record`.
- Ordinary progression and transition handoffs already synchronize `fg_boundary_active_record`
  with `A5+0x013E`. Descriptor rebuilds during steady streaming therefore see equality, including
  after package 6→1 and package 7→2 handoffs.

No new flag is required. This is record identity, not a test for record 3, record 16, Phase 2,
waterfall, MODE, selector, or coordinate.

## 11. Repair

`genesistan_hook_pc080sn_descriptor_rebuild` now compares retained `A5+0x013E` with
`fg_boundary_active_record`:

```text
different -> direct scene/reseed write -> install before fresh fill
equal     -> ordinary rebuild/handoff -> preserve current residency owner
```

Build 0391 natural evidence returns to the exact pre-0390 sequence `0 -> 6 -> 1`; the frame-5453
rollback is absent. The final resolver, generated packages, collision, and palette are unchanged.

## 12. Phase-2 preservation proof

The existing six-button MODE trace was reused against numbered Build 0391 `_c`.

| Contract | Build 0391 result |
|---|---:|
| record / selector / stream | `0x0011 / 1 / 0x00051183` |
| active package before stable entry | 5 |
| valid source pointers | YES |
| entry staged nonblank | 2048/2048 |
| entry staged sum | `0x0319CFB9` |
| final reconstructed Plane-A VRAM nonblank | 2048/2048 |
| final VRAM sum | `0x0319CFB9` |
| stage == VDP | YES |
| residency misses | 0 |
| collision nonzero / sum | `1735 / 0x00225958` |
| first later vertical stage/VDP | both 2048, sum `0x0319CF2F` |

This is byte/count-identical to the accepted mechanical portion of Build 0390.

## 13. Build 0391 outcome

Build 0391 was produced as the complete same-number family. Canonical gate PASS, gameplay-entry
gate PASS, transition-retention verifier PASS (rope 12, waterfall 224, zero missing/collisions),
five-variant-set PASS, and the mandatory MAME smoke PASS. The known legacy epoch gate remains
recorded as FAIL; it was not opportunistically changed.

## 14. Flying Demon regression protection

Tighe confirms that by Build 0387, killing the wings kills the whole Flying Demon. The rebased
body-death reference is retained. Build 0391 changes no Flying Demon code. Interactive regression
verification remains Tighe-only.

## 15. Architecture and policy review

- **Semantic cut:** retained arcade record/source/descriptor decision, before native final
  Plane-A realization.
- **Chip-specific tail removed:** the already-retired PC080SN C-window/name-RAM write and device
  publication tail remains retired; this task changes only when the existing native package is
  selected.
- **Transitional compatibility:** the existing compiler-owned deterministic package/LUT installer
  remains. Its producers are retained record/descriptor transitions; consumers are native final
  name resolution and pattern DMA. No new compatibility structure was added. Its eventual removal
  boundary remains complete direct semantic streaming without package remap compatibility.
- Semantic boundary: YES. Direct final VDP/name production: YES. New mirror/shadow/device RAM:
  NO. Generic chip-address translation: NO. Genesis gameplay/frame ownership: NO. Final resolver
  change: NO.

## 16. Tool reuse

- Existing project tools reused: `opt003_natural_transition.lua`, Build-0388 Phase-2 trace,
  transition-retention verifier, boundary compiler/report, generated address map, normal Makefile
  release/gates, GENESIS NTSC MAME.
- New tooling created: none. The existing natural-transition harness gained an optional audit dump
  mode for package-change LUT/staging snapshots.
- Why extension was necessary: the prior harness logged only one LUT canary; this regression
  required complete active-LUT and staged-name snapshots at each natural package transition.

## 17. Open/Closed Issues impact

- CLOSED-020: former OPEN-027 Flying Demon whole-death symptom, closed from Tighe's Build-0387
  gameplay confirmation.
- OPEN-017 remains open for its other hardware/performance symptoms.
- OPEN-028 unchanged and not conflated with this package rollback.
- OPEN-029 unchanged/deferred.
- New issue: none.

## 18. KNOWN_FINDINGS impact

**Option B — propose an extension to KF-078; do not silently edit the registry.** Proposed durable
extension: early residency at the descriptor-rebuild boundary is legal only when retained
`A5+0x013E` differs from native `fg_boundary_active_record`; unconditional reinstall can undo a
streamed overlap handoff. Record-3 proof: package `6 -> 1` at column 45, then Build 0390 wrongly
restored package 6 at frame 5453, clearing 101/224 waterfall code mappings. Build 0391 preserves
`6 -> 1` and Phase-2 initial population.

## 19. USER MUST VERIFY

Tighe must compare the first waterfall against the arcade reconstruction, continue through the
remainder of Phase 1, use MODE to verify Phase-2 entry is populated before movement, verify later
vertical streaming, and kill the Flying Demon through its wings. Phase-2 palette is explicitly
ignored for this test.
