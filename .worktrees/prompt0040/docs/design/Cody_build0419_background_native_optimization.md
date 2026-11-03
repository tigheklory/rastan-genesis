# Cody — Build 0419 Background Native Optimization

Date: 2026-10-13  
Baseline: accepted Build 0418  
Produced: complete Build 0419 family
Owner status: **ACCEPTED ON REAL GENESIS**

Tighe verified gameplay and graphics as PASS on real Genesis, with no observed
regression. Subjective performance result: **somewhat faster than Build 0418**.
This is deliberately not converted into a quantitative hardware percentage;
the exact quantitative evidence remains the 50% selector-0 traversal reduction.

## Change

Build 0419 adds `resolve_plane_a_name_collision_cell`, a fused semantic
accessor returning the final Genesis Plane-A name word in `D0` and the retained
arcade collision word in `D2`. It performs the live source-pointer, ring unwrap,
descriptor relocation/validation, and metatile selection once.

Selector 0 now uses the fused accessor for all 64 logical rows. Selector 1/2
uses it for resident rows, where both outputs are consumed, and retains the
collision-only leaf for a nonresident row, where producing a name would change
cache/miss semantics and add work. The standalone name and collision accessors
remain for consumers that need only one product.

No gameplay rule, camera decision, logical coordinate, tile identity,
attribute rule, collision value, package selection, dirty flag, staged-buffer
layout, or DMA operation changed.

## Runtime reduction

For the dominant selector-0 event:

| Metric | 0418 | 0419 | Change |
|---|---:|---:|---:|
| logical cells | 64 | 64 | none |
| semantic outputs | 64 names + 64 collision | same | none |
| resolver entries | 128 | 64 fused | -50% |
| complete live descriptor traversals | 128 | 64 | -50% |
| duplicate traversals | 64 | 0 | eliminated |
| physical publication / DMA | one dirty 32-word column | same | none |

The exact accepted-background baseline is the Build 0417/0418-equivalent
selector-0 trace: average 135,751.6 cycles, median 135,750, range
135,748–135,762, 40 events. The unmodified controlled trace's current cold-boot
input route did not arm on either the 0418 or 0419 ROM in this MAME controller
configuration (`armed=0` in both attempts). It therefore provides no honest
post-change cycle percentage. No trace framework or production instrumentation
was changed to force a result. The measured deliverable for this build is the
exact resolver/traversal-count reduction above; real-Genesis speed remains
Tighe-required.

## Correctness and authority

`verify_bg_a_incremental_background.py` now requires the fused accessor and
retains all full-span checks: rejected 0415/0416 narrow models fail, while the
64x64 initial seed, N/N+32 distinction, source rebase, trailing retention,
independent Plane-B context, 32-row projection, dirty gather, and 32-word
column DMA pass.

The generator/authority chain is unchanged. No generated data was added.
`Test.json`, `specs/palette_decisions.json`, existing PC080SN identities, active
package LUTs, and boundary packages retain their established roles.

## Gates

- assembly/link: PASS;
- full-span background coherence: PASS;
- VDP DMA boundary/alignment: PASS (`A-0154` remains one safe 16-word DMA);
- transition retention: PASS;
- canonical gate: PASS;
- gameplay-entry gate: PASS, address/bus/illegal/crash events all zero;
- mandatory 30-second Genesis NTSC MAME trace: completed;
- complete five-ROM family: PASS;
- standing seven-epoch gate: FAIL at the first target epoch, unchanged from the
  accepted Build 0418 gate label.

## Artifacts

All artifacts are 1,998,520 bytes.

| Artifact | SHA-256 |
|---|---|
| `rastan_direct_video_test_build_0419.bin` | `79a479d611284a11e7123f46ee5dd5b2c7922f774a9d55cc4717d7cdcc09cb12` |
| `rastan_direct_video_test_build_0419_c.bin` | `c446ace26a9d8575d868fcb04de4b18f1aa25b3445e765085d35031ff93920d2` |
| `rastan_direct_video_test_build_0419_d.bin` | `3213564e6449f3a490658e1441f4f27304349aee9f1bb381d5258ec286c060bb` |
| `rastan_direct_video_test_build_0419_do.bin` | `349049ef25d9951704eadc0ebfda5e6a62d320fcb6142ebdbec01cced5d59ace` |
| `rastan_direct_video_test_build_0419_s.bin` | `a0bae8358dc48d19e275ae89a146c1c4ad8c4e33e2a6ab3672813eb0a12be349` |

## Closure

Build 0419 is the accepted forward baseline. Background optimization is
**NOT CLOSED**. Plane-A name-only rows, Plane-B
rows/columns, and collision-only consumers still interpret live arcade
descriptor layouts at runtime. A safe native-index/generated-record design for
those dynamic contexts remains the next graphics task. Scheduler Phase D and
Phase E were not started, and the worker remains in IRQ6. The `_do` black bands
remain valid IRQ6-overrun instrumentation; their continued presence keeps the
performance issue open and is not Layer-A/Plane-B corruption.
