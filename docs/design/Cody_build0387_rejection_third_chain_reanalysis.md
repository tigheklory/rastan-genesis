# Cody — Build 0387 rejection and third-chain reanalysis

**Baseline:** Build 0387 is consumed and user-rejected. **Counter:** 387, unchanged. **Outcome:**
the Build-0387 production resolver change is reverted; no Build 0388 was produced because an
arcade-to-Genesis repair chain is not yet proven.

## Phase 0

Relevant priors from `KNOWN_FINDINGS.md`:

- KF-010 (Plane mapping) applies because the rejected change affected native Plane-A production.
- KF-015 (vertical-scroll contract) applies because state-4 climb motion is converted into retained
  foreground-Y movement while the player is held in the screen band.
- KF-031 (assembler rebuild integrity), KF-071/KF-072 (native Plane-A pipeline/ring behavior), and
  KF-073 (matching local collision does not prove progression) constrain the rollback and the
  interpretation of the retained traces.

Rediscovery Hazard HIGH findings touched: KF-071/KF-072; their canonical reading is retained. No
chip-shaped visual shadow or alternate tilemap owner is introduced. No deferred-appendix item changes
the result. Classification: **EXTENDING** KF-071/KF-072/KF-073. OPEN-017 is context only;
CLOSED-008 is build-integrity context. No CONFIRMED or STRONG finding is contradicted. Tighe's result
rejects the Build-0387 task hypothesis, not a curated confirmed finding.

## User rejection and retained evidence

Tighe's Build-0387 result is authoritative:

- third-chain traversal: **FAIL**;
- Layer-A visual composition: **WORSE than Build 0386**.

Build 0387 remains consumed and its artifacts, report, counter entry, and trace evidence remain on
disk. The coherent human identity remains valid: USER_MARK frame 3090 has
`A5+0x013E=0x0011`, runtime pointer `0x00051183`, current Build-0386 mapping to original
`arcade_pc 0x00050F7D`, original selector byte 1, live `A5+0x10A8=1`, and player state 4.
The obsolete record-22/selector-0 interpretation is not revived.

What is rejected is the inference that selector 1/2 required an additional descriptor-axis
transpose in the shared native resolver. Static matrix agreement did not establish runtime intent,
and the user result disproves that production repair.

## Exact production rollback

The only Build-0387 production-source delta was in
`apps/rastan-direct/src/tilemap_hooks.s`: the new shared
`.Lresolve_plane_a_descriptor` branch selected selector-0 descriptors by world row/X delta and
selector-1/2 descriptors by world column/Y delta; both `resolve_plane_a_cell` and
`resolve_plane_a_collision_cell` were routed through it. That helper and the two call-site changes
were removed.

Focused proof after rollback:

```text
git diff --exit-code -- apps/rastan-direct/src/tilemap_hooks.s
exit = 0
```

The tracked production source is therefore byte-for-byte the pre-0387/Build-0386 resolver source.
No repository reset was used. Build-0387 generated artifacts and documentation were not removed.
The Build-0386 Flying Demon operand repair remains in `specs/rastan_direct_remap.json` at original
`arcade_pc 0x044898` (`49F90010C508 -> 49F900FF0508`). No palette source/profile was edited.

The rejected helper affected both final Plane-A staging and the gameplay collision-ring publisher,
for selectors 1 and 2. The rejected report's full-ring model counted 3,844 changed descriptor
coordinates, 2,942 changed visual tile values, and 1,535 changed collision values. Those counts are
now evidence of blast radius, not correctness.

## Original arcade climb and exit semantics

Static original-arcade code shows no automatic third-chain record/progression transition at the top.
The relevant path is the ordinary player climb/release state machine:

1. Player state 4 is handled at original `arcade_pc 0x051EAC`.
2. Up/down climb input increments retained pending-motion counters at original
   `arcade_pc 0x051FC8` / `0x051FE8`.
3. Original `arcade_pc 0x051800..0x05186A` converts the pending amount to
   `A5+0x10DE` (up/down Y request, capped at four) and calls the vertical movement/scroll controller.
4. When player screen Y is at the upper band, original `arcade_pc 0x053850..0x0538E8` keeps player
   Y near the band and publishes foreground-Y motion through the retained scroll request.
5. Leaving climb state is input-driven. The edge decoder at original `arcade_pc 0x0515B6` writes
   `A5+0x136E=0x0011` for the relevant button edge. State 4 then routes through original
   `arcade_pc 0x051ED2 -> 0x051F0A -> 0x05206E -> 0x052200`.
6. At original `arcade_pc 0x052206` and `0x052244`, active-low direction bits 2 and 3 of raw input
   `HW/WRAM 0x0010D37A` select the lateral release. The chosen branch writes player state 2 at
   original `arcade_pc 0x052230` or `0x05226E` and calls original `0x052466` or `0x052432`.

Thus the proven trigger is **button edge plus lateral direction while state 4 is active**. Player-Y,
foreground-Y, selector, collision, and progression establish where the action occurs, but none is a
standalone automatic upper-route gate in this code.

## Bounded ORIGINAL ARCADE MAME observation

The existing Build-0378 arcade route was narrowly extended in
`tools/mame/scripts/build0387_rejection_arcade_upper_exit.lua`. It retains record 17 / selector 1,
records the three real head probes at original `arcade_pc 0x053A90/0x053AC4/0x053AF8`, and keeps
upward input asserted after the final climb. Output is under
`states/traces/build0387_rejection_arcade_upper_exit_right/`.

The run reaches state 4 at player `X/Y=0x0122/0x003E`, foreground Y `0x0100`, then advances the
camera to `0x0167`. Continued Up does not produce a scene/progression transition; the arcade itself
reaches a collision/scroll ceiling. This supports the static result that an additional lateral
release action is required. The automated route did **not** establish a successful upper landing,
so it is not used as a success oracle and authorizes no repair.

## Build-0386 human-trace comparison

| Semantic quantity | Arcade required value/path | Genesis Build-0386 human trace | Match? |
|---|---|---|---|
| player state while climbing | 4 | 4 for all 720 retained frames | YES |
| player Y at upper screen band | approximately `0x003E..0x0040` | `0x0040` | YES |
| requested Y motion | nonzero while Up is consumed | `A5+0x10DE=1` during frames 3160..3387 | YES |
| actual Y response | player stays at band; scroll advances | player remains `0x0040`; scroll advances | YES |
| foreground Y | advances and wraps according to retained ring epoch | `0x01DA -> 0x01FF -> 0x0000 -> 0x0028` | no same-epoch mismatch proven |
| selector | 1 | 1 | YES |
| strip/group | advances with streamed rows | `0/0 -> 2/1` | observed; arcade success epoch not captured |
| head probe | three probes via `0x053A6E` | trace probe TSV contains header only | NOT AVAILABLE |
| feet/ground field | ordinary probe output | `A5+0x1132` returns to `0x0008` after input stops | observed only |
| rope/chain attached | state 4 | state 4 | YES |
| release input edge | `A5+0x136E=0x0011` | not logged | NOT AVAILABLE |
| raw lateral input | active-low bit 2 or bit 3 | not logged | NOT AVAILABLE |
| release transition | state 4 -> state 2 at `0x052230`/`0x05226E` | no state transition; remains 4 | **FIRST OBSERVED OUTCOME DIFFERENCE** |
| progression | remains record 17 during ordinary release | `0x0011` | YES |

The first observed difference is therefore that the arcade release path performs state 4→2 while
the retained Genesis capture never leaves state 4. It is **not yet a proven translated-code
divergence**: the Genesis trace omitted both the decisive input-edge field and raw input, and its
debugger probe output is empty. It cannot distinguish “the necessary release combination was not
present in the captured window” from “Genesis failed to decode/consume that combination.”

Collision mismatch responsible: **NO evidence**. The previously proven top cell
`0x00FF3DF4=0x0001` agrees with the original source, and this capture supplies no contrary Genesis
probe. Scroll mismatch responsible: **NO evidence**; exact same-epoch scroll equality was already
proved, and both runs advance while climbing. Player-state/transition mismatch: **YES as the first
observed outcome, cause unresolved**. A separate transition/gate-field defect is **NOT PROVEN**.

## Repair decision and Build 0388

No general repair satisfies the required proof chain:

```text
original arcade successful upper landing
    -> Genesis first differing retained field/branch
    -> general production repair
```

Adding a chain coordinate, record-17 case, forced state transition, collision override, MODE path,
or another shared-resolver change would be guesswork. Therefore no production repair was made, no
ROM was built, Build 0388 was not consumed, and the counter remains 387.

The next decisive capture must include the exact successful ORIGINAL ARCADE lateral release and the
same attempted GENESIS NTSC action, retaining `A5+0x136E`, raw input `0x10D37A`, state, pending
motion, head/feet probe results, scroll epoch, and landing result.

## Separate first-arrival Layer-A issue

The pre-existing first-arrival stray sky cells are recorded as OPEN-028. They predate Build 0387 and
are not evidence for its rejected transpose. No reproducible cell triple was supplied in this task,
so the source-vs-staging-vs-VRAM classification remains **unresolved**. The future bounded proof is
authoritative source cell -> staged Plane-A word -> actual VDP Plane-A word, on first arrival and
second arrival after scrolling away.

## Architecture/policy review

- **Semantic cut:** retained arcade scene/selector/source/descriptor/ring and collision decisions
  remain above the existing native boundary; final Genesis Plane-A staging and collision-ring
  publication remain below it.
- **Chip tail removed:** the project already retires the original PC080SN C-window/name-RAM walk and
  hardware publication tail in favor of direct final Plane-A production. This rollback removes no
  additional chip tail and restores the pre-0387 native resolver.
- **Transitional compatibility:** no new compatibility path, shadow, virtual chip RAM, projector, or
  range dispatcher is added. Existing retained arcade semantic map/collision state remains consumed
  by the native final publishers; its removal is not part of this task.
- Boundary is semantic: **YES**. New code consumes chip-shaped state: **NO new production code**.
  Mirrors/shadows introduced: **NO**. Arcade still owns gameplay/frame/VBlank: **YES**. Native helper
  still produces final Plane-A/collision output: **YES**. Superseded compatibility added: **NO**.

## Verification and ledgers

- Build-0387 resolver hypothesis: **REJECTED**.
- Build-0387 production resolver delta reverted: **YES**.
- Pre-0387/Build-0386 tracked Plane-A resolver source restored: **YES**.
- Build-0386 Flying Demon fix retained: **YES**.
- Palette profile changed by this task: **NO**.
- Human record-17/selector-1 identity retained: **YES**.
- Build produced: **NO**; counter remains 387.
- New issues: OPEN-028 (stale first-arrival Plane-A cell), OPEN-029 (third-chain transition proof).
- KNOWN_FINDINGS impact: **Option A — no new finding to index.** The task rejects an unaccepted
  hypothesis and stops before a complete successful arcade-vs-Genesis transition proof.

**USER MUST VERIFY:** no new ROM exists. If a later proven repair produces Build 0388, only Tighe
can validate Layer-A composition, natural third-chain traversal, ordinary horizontal sections, the
Build-0386 Flying Demon fix, and palette preservation. H25 was not begun.
