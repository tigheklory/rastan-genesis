# Cody — Build 0375 R1 Phase-2 Residency Preinstall Attempt

**Status: REJECTED / NOT ACCEPTED.** Build 0375 is preserved as required, but the focused
Genesis NTSC trace falsified the claimed fix: package 5 was not active before the record-16 scene
fill on the tested MODE-driven transition.

## A. Build-0374 user validation

Baseline is Build 0374, canonical SHA-256
`ac67ae67aad01ba15d7df0ec1115f305e84ce565c7f7f5cbc6b0f776e462ff2c`.

Tighe's BlastEm result is authoritative:

- Round 1 / Sub-round 1 is dramatically improved and almost entirely correct; the few isolated
  misplaced cells are deferred and are not classified as a regression.
- Round 1 / Sub-round 2 is essentially absent on initial entry.
- Layer A begins appearing when Rastan later scrolls upward.

This result has also been added to
`docs/design/Cody_build0374_r1_phase2_layer_a_unpopulated.md` and `AGENTS_LOG.md`.

## B. Exact old transition ordering

The initial static hypothesis was incomplete. The relevant current Build-0375 address-map
correlations are:

| Operation | `arcade_pc` | `runtime_genesis_pc` |
|---|---:|---:|
| outer-controller call of scene fill | `0x050206` | `0x050406` |
| outer-controller record selection write | `0x05025A` | `0x05045A` |
| scene-fill entry | `0x0503DC` | `0x0505DC` |
| first scene-fill setup/producer calls | `0x0503DC`, `0x0503E0` | `0x0505DC`, `0x0505E0` |
| 64-publication loop producer calls | `0x050434`, `0x050438` | `0x050634`, `0x050638` |
| post-fill residency hook | `0x050482` | `0x050682` |
| ordinary segment advance replacement | `0x0558FE` | `0x05598C` |

For the `_c` MODE reproduction, the actual order is:

1. `.Lmode_finish_subround` writes the retained sub-round transition state.
2. The translated outer controller selects progression/record 16 directly at runtime
   `0x05045A` (`move.b D1,A5+0x013E`).
3. This direct write bypasses `fg_boundary_advance_segment` at runtime `0x05598C`.
4. The controller calls the record-16 scene fill at runtime `0x0505DC`.
5. Scene-fill producers resolve cells while package 0 is still active.
6. The post-fill hook at runtime `0x050682` has no pending install to perform.
7. At the later record-17 reseed, package 5 becomes pending and is installed after the fill.

Thus the first Phase-2 producer runs before package 5. The Build-0374 report's earlier claim that
MODE entry converged on `fg_boundary_advance_segment` has been corrected.

## C. Package-before-fill contract

The required architectural contract remains:

`retained arcade record selection -> required native residency package -> atomic package install
-> retained semantic scene fill -> final Genesis Plane-A name words -> VBlank publication`.

The semantic cut is still above the PC080SN hardware tail: retained arcade progression/source/
descriptor decisions are converted directly into Genesis staging and VDP publication. No
PC080SN C-window execution, name-RAM shadow, chip-address translator, tall projection, runtime
allocator, or full-plane repaint was introduced.

Preinstall is safe only when the new record's package is already fully determined. The generated
table proves all current records have exactly one variant; stable package 5 covers records 16–20.
Transition packages 6 and 7 retain their separate streamed handoff contract.

## D. Implementation attempted

The compiler was changed so `FG_BOUNDARY_RESEED_MASK` contains only scene-reseed records whose
generated record table has more than one package variant. With one variant for every current
record, the mask changed from bit 16 set to `0x00000000`. The assembly comment and the existing
post-fill hook's remap note were updated to match that rule.

This is a general record/variant predicate, not a Round-1 cell or progression special case.
However, it affects only transitions that execute `fg_boundary_advance_segment`. It does not
intercept the direct outer-controller write used by the authoritative `_c` reproduction, so it
does not satisfy the requested initial-entry contract.

Files changed for the attempted Build-0375 delta:

- `tools/translation/compile_pc080sn_genesis.py`
- `apps/rastan-direct/src/fg_tile_cache.s`
- `specs/rastan_direct_remap.json`
- generated package/constants, linked outputs, address maps, manifests, and numbered artifacts

No new opcode-replacement site was added by this delta. The final canonical manifest contains 229
opcode-replacement sites and canonical coverage `0x1A3EB8`; `_c` retains the existing mechanical
`+0x1000` coverage delta.

No additional legacy PC080SN code was removed in this rejected delta. The previously retired chip
tail remains retired; the retained arcade scene-fill producer and existing native name-word path
remain intentionally active.

## E. Record-15 -> 16 proof

Static inspection proves that an ordinary segment increment reaches the replacement at arcade
`0x0558FE` / runtime `0x05598C`, and with the generated mask clear that helper would install the
record-selected package immediately.

The focused automated `_c` route did **not** execute an ordinary active-record 15 -> 16 increment.
Immediately before MODE it showed progression `0`, active record `0`, package `0` (the separate
strip field was `15`). MODE then caused the outer controller to write progression 16 directly.
At frame 411 the observed state was progression `16`, active record `1`, active package `0`, and
64 misses. Therefore the required dynamic proof—record 16 / required package 5 / active package 5
before scene fill—failed.

This distinction prevents the strip value `15` from being misreported as active boundary record
15. No claim is made that the natural long-play 15 -> 16 route was dynamically captured.

## F. LUT hit/miss comparison

| Focused initial-fill measurement | Build 0374 `_c` | Build 0375 `_c` |
|---|---:|---:|
| misses on record-16 entry | 64 | 64 |
| misses after 30 frames | 1,284 | 1,284 |
| misses after the fill / stable record 17 | 3,648 | 3,648 |
| derived resolved cells in the 4,096-cell fill | 448 | 448 |

The 448 value is explicitly derived as `4096 - 3648`; the tracer did not expose a separate hit
counter. Build 0375 made no measurable improvement in this route.

## G. Staged foreground comparison

| Stable record-17 staging measurement | Build 0374 `_c` | Build 0375 `_c` |
|---|---:|---:|
| nonblank tile-index cells | 368 | 368 |
| staged sum | `0x0303B910` | `0x0303B910` |
| staged XOR | `0x0000` | `0x0000` |

The public MAME `:gen_vdp` `videoram` surface remains an invalid oracle in this setup because it
reports zero for visibly rendered planes; no VRAM-content conclusion is derived from it.

## H. Transition-retention regression proof

The offline compiler still produces:

- 21 records and 8 packages;
- six stable epochs with pattern counts `[282,333,639,583,639,282]`, all within 676 slots;
- records 16–20 -> package 5;
- package 5 with 283 mappings, 282 patterns/uploads/identities, and zero drops;
- rope-to-waterfall package 6 and waterfall-to-next-rope package 7 unchanged.

`verify_build0311_transition_retention.py` passes for both transition packages. The canonical gate,
Genesis NTSC gameplay-entry gate, and complete same-number variant set passed. The known legacy
seven-epoch harness still fails because it requests the removed `fg_boundary_conflict_lut` symbol;
this is unchanged from Builds 0373/0374.

R1 Phase-1 automated startup staging remained consistent through the tested pre-MODE point, but
full visual regression acceptance remains a user test. The Build-0375 Phase-2 result itself is
**FAIL / unchanged**.

Existing project tools reused: current address map and postpatch disassembly, boundary compiler
and report, transition-retention verifier, Makefile pipeline, established `_c` MODE route, current
symbols, and Genesis NTSC MAME.

New tooling created: none. The existing bounded `/tmp/build0374_phase2_probe.lua` was reused and
minimally augmented with write-event columns; those taps did not produce additional events and no
claim relies on them.

Why new tooling was necessary: not applicable.

## I. Build-0375 artifacts

Build counter: `374 -> 375`.

| Variant | ROM path | SHA-256 | Size |
|---|---|---|---:|
| canonical | `dist/rastan-direct/rastan_direct_video_test_build_0375.bin` | `77cbf62dbf110f021e3a22026864a4b69ea4e4e0efad64663e4ef63806f7a36b` | 1,719,992 |
| `_d` | `dist/rastan-direct/rastan_direct_video_test_build_0375_d.bin` | `406b4b42d390ad478a039529edf8b471bf6d26412e25f14ed83884b4e114bf2a` | 1,719,992 |
| `_s` | `dist/rastan-direct/rastan_direct_video_test_build_0375_s.bin` | `7405a8c3bacb9e5ced5bf79206fa79ad13722c1291e4c06ea0767165f9fb6f7c` | 1,719,992 |
| `_do` | `dist/rastan-direct/rastan_direct_video_test_build_0375_do.bin` | `c103826731c2dbae43f66bab543be87148b1c5b8d0c8b97185a27e475398dd20` | 1,719,992 |
| `_c` | `dist/rastan-direct/rastan_direct_video_test_build_0375_c.bin` | `e60a8b79bbbd1aeba157cc6b10909a166359deceef2e54be905283b8635ead0d` | 1,724,088 |

Runtime validation platform: **GENESIS NTSC MAME** (`genesis`, six-button controller for MODE).
Focused trace: `states/traces/build0375_r1_phase2_residency_preinstall_c/phase2_probe.tsv`.

Regressions checked: package compiler invariants, packages 6/7 retention, canonical build gate,
gameplay-entry gate, same-number variant production, and pre-MODE Phase-1 staging. Plane B,
sprites, rope behavior, and individual Phase-1 misplaced cells were not modified or reinvestigated.

Unresolved limitation / STOP status: the first universally safe interception point for direct
outer-controller scene-entry record writes is not implemented. A future task should evaluate the
general scene-fill entry boundary so the package selected from the already-retained record is
resident before the first producer. No Build 0376 was made in this one-build task.

## J. USER MUST VERIFY

Build 0375 is available for BlastEm comparison but is **not claimed as the fix**. If Tighe tests
this rejected artifact, verify:

1. Round 1 / Sub-round 1 retains the dramatic Build-0374 improvement.
2. On initial entry to Round 1 / Sub-round 2, determine whether Layer A is still absent.
3. Scroll upward/downward and confirm whether terrain still begins appearing only later.
4. Ignore the few isolated misplaced Phase-1 cells; they remain explicitly deferred.

Expected from the Genesis NTSC automated evidence: initial Phase-2 behavior is unchanged from
Build 0374. STOP; do not accept Build 0375 as the residency-ordering correction.
