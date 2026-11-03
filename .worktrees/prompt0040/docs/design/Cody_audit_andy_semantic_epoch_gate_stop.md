# Independent Audit of Andy's Semantic Epoch Gate STOP

**Author:** Cody  
**Date:** 2026-09-07  
**Classification:** INFRASTRUCTURE / independent technical audit  
**Production changes:** NO  
**Build produced:** NO  
**Build counter:** 348 (unchanged)

## 1. Phase 0 baseline

The mandatory ledgers and governance documents were read before the task-specific evidence:
`KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md`, `RULES.md`, `ARCHITECTURE.md`,
`AGENT_GUIDE.md`, `PROMPT_TEMPLATE.md`, the native replacement policy, the three assigned Andy
reports, current source, current gate scripts, current symbols, the generated address map, and the
generated boundary package report.

Relevant durable priors:

| Finding | Relevance |
|---|---|
| KF-011, STRONG / Rediscovery Hazard HIGH | The arcade VBlank remains the frame/progression owner. A validation probe must not invent a competing gameplay owner. |
| KF-019, CONFIRMED / HIGH | MAME instruction-fetch sampling can miss translated execution; frame-visible state and established callback methods remain necessary evidence. |
| KF-030, CONFIRMED / HIGH | Generated address-map coverage is not semantic proof. |
| KF-037, CONFIRMED / HIGH | Replacement hooks must preserve fall-through/control-flow semantics. |
| KF-068 (native-video semantic-leaf entry), CONFIRMED / HIGH | Validation must protect the arcade-semantic to native-VDP cut, not validate a synthetic chip model. The ledger currently contains two entries numbered KF-068; this reference means the native-video surface/design entry. |
| KF-071 and KF-072, HIGH | KF-072 supersedes the reverted 32-row ring guidance in KF-071; the current coordinate model must be judged as implemented. |

Task classification is **INFRASTRUCTURE**. The touched issue thread is OPT-003 / publication-gate
methodology; no numbered issue is opened or closed. No contradiction of a CONFIRMED or STRONG
finding was detected. KNOWN_FINDINGS impact is **Option A: no new finding to index**.

The current accepted numbered artifact was preserved:
`dist/rastan-direct/rastan_direct_video_test_build_0348.bin`, SHA-256
`fac088eb0f8e9d374af80d9381aeecfe20be2ec6138ab688cfc6d0c45db1bf6b`, 1,666,744 bytes.
The matched palette-gated score ROM used for the independent runs was
`apps/rastan-direct/dist/rastan_direct_video_test_score.bin`, SHA-256
`528062dff1c0656c18d5a196c049b73e59577dd3972467dbaf654d4295855d24`, 1,666,744 bytes.

## 2. Audit scope

This audit asks whether Andy established only that `fg_boundary_advance_segment` is too low-level
to synthesize a natural transition, or also established that no architecture-compliant accelerated
semantic validation path remains. No production source, gate, runner, Makefile, generated input,
ROM, or counter was changed. Review probes were scratch files under `/tmp` only.

The required native-hardware policy was preserved: the original arcade semantic decision is the
authority, and the final renderer remains direct Genesis Plane/SAT production. This audit does not
introduce a PC080SN software device, C-window shadow, projection path, or alternate gameplay owner.

## 3. Evidence reviewed

- Original-arcade Ghidra exports under `analysis/ghidra/rastan_arcade/exports/`, including the call
  graph.
- Original-arcade reference reconstructions under `docs/arcade_reference/pc080sn/`, especially
  `gameplay_control.c`, `map_stream_control.c`, `map_stream_format.md`, `state_fields.md`, and
  `core_publishers.c`.
- `apps/rastan-direct/src/fg_tile_cache.s` and `tilemap_hooks.s`.
- `tools/mame/scripts/build0310_epoch_gate.lua`, the natural-transition script, and their runners.
- `apps/rastan-direct/out/symbol.txt` and generated package data/report.
- `build/rastan-direct/address_map.json`, used as the sole PC-space mapping authority.
- Andy's reports and latest relevant `AGENTS_LOG.md` entries.
- Independent Genesis NTSC MAME runs against the current score ROM with matching symbols.

## 4. Reproduction of key experiments

### 4.1 Natural record 3: PASS

The existing natural input method was run directly after accounting for the runner's path defect
(section 17). It used normal `P1 Start` entry and gameplay input, with no record write and no PC
hijack.

Observed sequence:

| External frame | Scene | Active record | Active package | `active_lut[0x034C]` |
|---:|---:|---:|---:|---:|
| 2646 | 1 | 0 | 0 | `0x0000` |
| 2702 | 1 | 1 | 0 | `0x0000` |
| 4228 | 1 | 2 | 0 | `0x0000` |
| 5276 | 1 | 3 | 5 | `0x0420` |
| 5277-5284 | 1 | 3 | 5 | `0x0420` |

At frame 5276 the natural state included X scroll `0x0167`, Y scroll `0x0105`, X crossing
accumulator `0x0001`, Y crossing accumulator `0x0008`, map pointer `0x00051174`, selector 0,
subcolumn 0, and group 0. During the following frames X and the cursor/counters continued to
evolve while package 5 and `0x0420` stayed stable. No exception was observed.

### 4.2 Context-preserving safe call: PASS

The independent scratch probe saved D0-D7, A0-A6, SP, PC, SR, and the affected stack window;
installed a private spin-sentinel return; forced only A5 to Genesis-WRAM `0x00FF0000`; masked
interrupts; invoked the current `fg_boundary_advance_segment`; then restored the complete saved
context. This avoids the earlier arbitrary-return and `0xFFFF` state corruption.

From clean record 0/package 0 it called the helper three times:

```text
record 0 -> 1, package 0
record 1 -> 2, package 0
record 2 -> 3, package 5, active_lut[0x034C] = 0x0420
```

At record 3, the canonical `verify_maps` logic was independently applied to all 395 package-5 map
pairs and all 854 fixed-Plane-B pairs. Result: **PASS**. Slots were checked against the canonical
legal pattern ranges and fixed Plane B was checked not to use the Plane-A window. There were zero
exceptions and the restored SP/control context remained valid.

### 4.3 Claimed survival failure: FAIL to reproduce

After the safe call returned, eight normal external frames were allowed to execute. On every frame:

```text
active record = 3
active package = 5
active_lut[0x034C] = 0x0420
```

The package-5 and fixed-B full-map checks still passed after frame 8. Meanwhile the native cursor
and publication counters advanced (`cursor X` from `0x00BF0018` to `0x00BCC03C`; subcolumn/group
from 3/1 through 0/4). Thus the run was not frozen at the return boundary.

This directly refutes the claimed deterministic one-frame `0x0420 -> 0x0000` result for the matched
ROM/symbol/probe conditions. It does not prove indefinite natural equivalence, but it means the
documented survival failure cannot currently support a root-cause claim.

## 5. Original arcade natural-transition call graph

The original arcade transition is not a one-call record installer. It is accumulated across normal
player/camera updates and 64 publications:

```text
arcade_pc 0x051090 player_main_update
  -> arcade_pc 0x055650 per-frame PC080SN gameplay dispatcher
     -> arcade_pc 0x055696 / 0x05572E / 0x0557BA direction-specific boundary paths
        -> test camera delta/crossing state
        -> arcade_pc 0x055948 publish one tilemap1 strip/column
           -> arcade_pc 0x0558A2 advance publication counters
              -> every 4 publications: arcade_pc 0x0558C6 advances 16 source bases
              -> after 16 groups: arcade_pc 0x0558E0 advances stream state
                 -> map pointer +1
                 -> previous selector = old selector
                 -> selector = next map byte
                 -> arcade_pc 0x0558FE increments record
                    [current native replacement]
                    -> fg_boundary_advance_segment
                    -> fg_boundary_install
```

The generated native overlap handoff is a separate, later per-column action. The native selector-0
producer computes logical column `(group * 4 + subcolumn) & 0x3F`, invokes
`fg_boundary_transition_step`, and then stages the entering column. At logical column 45,
record 3/package 5 hands off to stable package 1; record 4/package 6 hands off to stable package 2.
This is generated Genesis residency policy preserving the bounded viewport overlap, not an
original arcade instruction at a numerically identical PC.

## 6. Address-map proof and exact coupling

All entries below are exact current `address_map.json` correlations, not arithmetic relocation:

| arcade_pc | runtime_genesis_pc | Role |
|---:|---:|---|
| `0x055650` | `0x055730` | per-frame dispatcher |
| `0x055696` | `0x055776` | vertical-direction path |
| `0x0556A6` | `0x055786` | vertical boundary/publish branch |
| `0x05572E` | `0x05580E` | second vertical-direction path |
| `0x055738` | `0x055818` | vertical boundary/publish branch |
| `0x0557BA` | `0x05589A` | horizontal-direction path |
| `0x0557C4` | `0x0558A4` | horizontal selector body |
| `0x055808` | `0x0558E8` | horizontal crossing path |
| `0x0558A2` | `0x055982` | publication counter owner |
| `0x0558C6` | `0x0559A6` | source-base advance |
| `0x0558E0` | `0x0559C0` | completed-ring stream advance |
| `0x0558FE` | `0x0559DE` | patched record-increment site |
| `0x055904` | `0x0559E6` | descriptor rebuild/reload site |
| `0x055948` | `0x055A2A` | tilemap1 publisher |
| `0x055AB4` | `0x055B96` | scroll commit site |

Current native helper symbol: `fg_boundary_advance_segment` at runtime_genesis_pc `0x0007258C`.
The scratch trace first samples runtime_genesis_pc `0x0007258E`, after entry execution has begun.

Natural transition state is distributed across mapped Genesis-WRAM (A5 = `0x00FF0000`):

| Genesis-WRAM field | Arcade semantic role |
|---:|---|
| `0x00FF10D8`, `0x00FF10DA` | per-frame X/Y camera deltas |
| `0x00FF10AE`, `0x00FF10B0` | tilemap1 X/Y scroll |
| `0x00FF10B2`, `0x00FF10B4`, `0x00FF10B6` | crossing accumulators |
| `0x00FF10D0` | pending direction bits |
| `0x00FF10CA`, `0x00FF10CC` | 4-by-16 publication counters |
| `0x00FF10C6` | selector-stream byte pointer |
| `0x00FF10A8`, `0x00FF132C` | current and previous selector |
| `0x00FF013E` | record/segment index |
| `0x00FF10A0`, `0x00FF10A4` | tilemap1 publication cursors |

The descriptor/source tables at mapped Genesis-WRAM `0x00FF1000`, `0x00FF1040`, and
`0x00FF1080` advance/rebuild with the ring. Therefore the record, stream pointer, selector, source
bases, counters, cursor, and camera crossing are a coupled history, not interchangeable scalar
inputs.

## 7. Installer dependency closure

**Immediate CPU call precondition:** `fg_boundary_advance_segment` requires valid A5 pointing at
mapped Genesis-WRAM and a valid stack/call context. It increments A5+`0x013E`, optionally marks a
reseed, and invokes `fg_boundary_install`. The current reseed mask is zero, so tested records install
immediately.

**Installer environment:** scene ID must be gameplay (1); generated package tables must match the
ROM; the staged Plane-A and VDP state must be valid. The installer reads record-to-package data,
rebuilds active/conflict LUT ownership, updates active record/package/variant and diagnostics,
uploads package patterns, and updates display/dirty metadata. It preserves its documented register
set and masks interrupts around the sensitive install.

The narrow statement "A5 is the only external immediate register precondition" is supportable for
calling the helper. It is not a dependency closure for recreating natural gameplay history.

## 8. Natural-transition dependency closure

The natural transition additionally requires the per-frame camera deltas and scroll, crossing
accumulators, selector/pending-direction state, 4-by-16 publication counters, tilemap cursors,
selector-stream pointer, source-base and descriptor tables, and the 64 publications that lead to
the next stream byte. It also includes native package handoff at logical column 45.

Therefore Andy correctly distinguished installer execution from natural transition semantics in
principle, but the observed safe-call state cannot be declared short-lived without an actual
post-call divergence.

## 9. Safe-call audit

The corrected sentinel mechanism is materially safer than either the old canonical injection or
the failed frame-done hook: it supplies an RTS destination, prevents normal execution while the
helper spans frame callbacks, masks interrupts, and restores registers plus stack bytes. The
independent run confirms it avoids record/package `0xFFFF` corruption.

It remains a semantic installer test, not a natural camera-transition test. It can validly test
package decoding, LUT construction, legal slot ownership, fixed-B preservation, control return, and
short-term persistence. It cannot alone prove that the world/camera has naturally reached that
record.

## 10. Six-case transient-pass audit

Current generated expectations are:

| Record | Runtime package | Kind | Map pairs | Required patterns |
|---:|---:|---|---:|---:|
| 0 | 0 | stable epoch 0 (records 0-2) | 283 | 282 |
| 3 | 5 | transition 0->1 | 395 | 394 |
| 4 | 6 | transition 1->2 | 480 | 478 |
| 5 | 2 | stable epoch 2 (records 4-10) | 642 | 639 |
| 11 | 3 | stable epoch 3 (records 11-12) | 586 | 583 |
| 13 | 4 | stable epoch 4 (records 13-15) | 650 | 639 |

The 676-slot Plane-A capacity covers each package. Fixed Plane B has 854 maps/patterns and zero
drops. Code `0x034C` is dense-LUT data: the conflict interval begins at `0x031A` and contains
`0x0032` codes, so its exclusive limit is `0x034C`.

Andy's reported 6/6 transient result is consistent with generated data and with the inspected
`verify_maps`/`verify_fixed_b` implementation. The independent record-3 run confirms those checks
for package 5. This supports **installer-map correctness**. It does not by itself establish natural
camera reachability, final VRAM/name-table pixel equivalence, all six natural transitions, or the
complete canonical release contract. The phrase "6/6 PASS" must retain that narrower qualifier.

## 11. Survival-window audit

The checked-in gate verifies Plane-A maps and fixed Plane B only once, at `install_frame`. During
the eight-frame window it requires the target active record/package condition to remain and then
checks cached map booleans, SP validity, and zero exception entry. It does **not** re-run LUT checks
each survival frame. Therefore its implemented survival contract is primarily persistence and
immediate control-flow/crash detection, not continuous proof of every LUT word.

Packages 5 and 6 are deliberately transitional. They are expected to hand off at native logical
column 45, so indefinite persistence of package 5/6 is not a valid natural-world requirement.
There are two separable useful contracts:

1. Installer contract: the requested package is fully and safely installed at the boundary.
2. Natural-world contract: normal camera/publication evolution subsequently performs the intended
   overlap and stable-package handoff.

The old synthetic gate does not create the second contract merely by waiting eight frames. A future
replacement should name and validate these contracts separately rather than inheriting an
ambiguous survival implementation.

## 12. Root cause of `0x0420 -> 0x0000`

**Classification: NOT PROVEN.**

The independent matched safe-call run did not observe the transition at all: `0x034C` remained
`0x0420` for eight executing frames and full package-5/fixed-B verification still passed. No writer
PC, branch, or control path has been captured that changes the word to zero. Static source shows
the installer clear/map paths as direct symbolic writers, but does not identify a post-safe-call
clear in this run.

Consequently the proposed chain

```text
record 3 with record-0 camera
  -> camera reconciliation
  -> specific corrective transition
  -> active_lut[0x034C] = 0
```

is unsupported. Camera/history mismatch is real, but it is not proven to cause the asserted clear.
The earlier observation may have used mismatched ROM/symbols, a different scratch implementation,
or another unrecorded condition; this audit does not choose among those hypotheses.

## 13. Higher semantic-owner search

**Bounded higher transaction found: NO.**

The highest relevant routine found is the per-frame dispatcher at arcade_pc `0x055650`
(runtime_genesis_pc `0x055730`), called from arcade_pc `0x051090`. It does not mean "advance one
record." It consumes whatever X/Y deltas and crossing state gameplay produced that frame and may
publish a strip. The closest completed-cycle owner is arcade_pc `0x0558E0`
(runtime_genesis_pc `0x0559C0`), but it runs only after the distributed 4-by-16 publication history
has completed. It owns stream/selector advancement, not the camera movement that caused the 64
publications.

Thus there is no evidenced one-call arcade routine that atomically means "advance camera to the
next record, publish all entering columns, advance selector state, and install the package." A
helper named around the record is not proof of that semantic ownership.

## 14. Deep records 11 and 13

**Legitimate runtime feasibility:** The generated model makes record 11/package 3 and record
13/package 4 legal stable epochs. Reaching them naturally requires the intervening stream/camera,
event, hazard, and publication progression. Record 3 already required about 5,276 external frames
under scripted input. Existing map-stream documentation still leaves event freeze/reseed behavior
partially unresolved, so a fully automated natural path to 11/13 is not currently proven.

**Accelerated semantic feasibility:** Not disproven, but no bounded one-call transaction was found.
The context-preserving safe call can validate deep package installation, which is useful but not a
natural-world proof. A legitimate accelerator would need to drive normal input/camera steps,
restore a same-ROM naturally captured semantic checkpoint, or prove a larger replay/checkpoint
transaction including the distributed fields. Arbitrary record writes or giant fake world-state
injections are not acceptable substitutes.

## 15. Was Option A truly exhausted?

**NO.** The specific attempt to treat `fg_boundary_advance_segment` as a complete natural
transition is correctly rejected. However, accelerated semantic validation as a class was not
exhausted because:

- the corrected safe call actually survives the independently tested window;
- the existing natural-input harness deterministically reaches record 3;
- a hybrid contract can use natural transitions for reachable overlap records and the safe call
  for explicitly scoped installer-only checks of stable/deep packages;
- same-ROM natural checkpoints or bounded input/camera stepping were identified but not evaluated
  to a concrete feasibility boundary.

This does not authorize weakening or replacing the canonical gate. It means escalation should have
distinguished an unproven full replacement from still-open bounded investigations.

## 16. STOP classification

**PARTIALLY JUSTIFIED.**

The immediate STOP on replacing/shipping the canonical gate was correct. The mandatory six-state
natural-equivalence matrix, especially records 11/13, was not established, and no complete bounded
camera transaction was found. Replacing the gate would have been unsupported.

The broader claim that Option A was no longer viable was premature. Its key survival failure does
not reproduce, its proposed `0x0420 -> 0x0000` writer chain is absent, and reachable natural
coverage already exists. Those bounded facts should have been resolved before presenting only a
policy choice.

## 17. Concrete overlooked avenues

1. Re-run the safe-call survival experiment with the exact same ROM and matching symbols, while
   checking full package maps each frame. This audit did so and obtained a stable PASS.
2. Use the existing natural harness directly for records 3 and likely 4/5 rather than infer failure
   from the synthetic gate.
3. Separate installer correctness from natural-world/handoff correctness in the test design.
4. Evaluate a hybrid matrix before escalating: natural reachable transition packages; safe-call
   installer checks for stable deep packages; explicit static package integrity for what runtime
   reachability cannot yet prove.
5. Correct or explicitly bypass the natural runner's path bug: it computes `ROOT` as the `tools/`
   directory because it ascends one level from `tools/mame`, producing default paths beneath
   `tools/`. Direct invocation of the checked-in Lua script works. This audit did not edit it.

These are architecture-compliant investigations, not approval to alter the production gate.

## 18. Recommended next technical action

Perform one no-build gate-contract experiment with matched ROM/symbols:

1. Reuse natural input for record 3/package 5 and extend only as far as record 4/package 6 and
   record 5/package 2, recording the logical-column-45 handoffs.
2. In parallel, run the safe-call installer check for records 0/5/11/13 with full package and
   fixed-B maps rechecked across the survival window.
3. Report two result classes explicitly: `NATURAL_WORLD` and `INSTALLER_ONLY`.
4. If records 11/13 still require natural-world proof, evaluate one same-ROM semantic checkpoint
   capture, including camera, map pointer, selector, counters, descriptor tables, and active
   package identity. Reject it if those dependencies cannot be captured without synthetic state.

Only after that matrix should Tighe choose whether the canonical release gate requires all-six
natural-world coverage or permits deep installer/static coverage. Do not modify the canonical gate
until that decision and evidence exist.

## 19. Open/Closed Issues Impact

- Open issues touched: OPT-003 / publication-gate infrastructure.
- New issues opened: none.
- Issues closed: none.
- Intentionally deferred: canonical gate replacement and deep natural records 11/13.

## 20. KNOWN_FINDINGS impact

**Option A - no new finding to index.** This audit corrects the confidence of an infrastructure
experiment. It does not establish a new durable production behavior or contradict an indexed
CONFIRMED/STRONG finding.

## 21. STOP status

Audit complete. No production source, gate, runner, Makefile, generated package, ROM, or build
counter was changed. The canonical gate remains untouched. The appropriate next boundary is the
explicit two-contract validation experiment in section 18, not a build.
