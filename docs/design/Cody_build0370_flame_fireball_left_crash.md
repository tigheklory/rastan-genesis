# Cody — Build 0370 Flame-Fireball Left-Facing Crash

## Outcome

The crash was not caused by the flame projectile and was not fixed by assigning a
new meaning to `A2`.  The first incorrect Genesis operation was a surviving call
to a retired PC090OJ clear routine.  Shift reflow had retargeted that call into
the live BODY constructor, creating a second, arcade-inexistent selector pass
that consumed caller-incidental `A2`.

The fix removes the obsolete hardware-clear call at original arcade PC
`0x05480A` with a size-changing replacement.  The native PLAYER_BODY lane is
already reset and rebuilt each frame, so no substitute clear, shadow record, or
gameplay mutation is required.

The initially published 0370 candidate tried to initialize `A2` in the mode-8
BODY branch.  Focused validation rejected it because the malformed second pass
and selector `0x66` remained.  Project policy forbids reusing a consumed build
number, so the corrected release is **Build 0371**.  Build 0370 remains preserved
as a rejected artifact and is not the ROM submitted for user validation.

## Exact `A2` write

The value `0x00FF0242` is loaded by retained translated arcade code, not by a
new native helper:

```asm
original 0x0449B4  player_actor_collision_scan_449b4
Genesis  0x044BB4  lea 0x0242(a5),a2
```

With Genesis `A5 = 0x00FF0000`, this legitimately produces
`A2 = 0x00FF0242`.  That is the special-contact record used by the collision
scan.  Original arcade code performs the same assignment with arcade `A5`.
Therefore this write is not itself a Genesis clobber and must not be removed or
wrapped with register-saving logic.

The deterministic failing trace also showed that the malformed second pass can
inherit a different incidental `A2` after the compositor has run.  This confirms
that no valid BODY selector-table ownership contract exists for `A2` at that
point.

## Original arcade register contract

`player_aux_update_547c0` calls original `FUN_000540ac` at `0x05480A`:

```asm
05480A  bsr.w  0540AC
05480E  bra.b  054808

0540AC  movea.l #00D00000,a1
0540B2  move.w  #4,d2
         ; write four disabled PC090OJ records
0540CA  rts
```

The callee owns `A1` and `D2`; it does not read or write `A2`, does not enter the
BODY constructor, and does not perform an animation or flame selector lookup.
Consequently the original contract is simply that `A2` is preserved across this
PC090OJ clear.  More importantly, original execution has **no second BODY
selector pass at all**, so the preserved value of `A2` is irrelevant to BODY
selection on this path.

The normal mode-8 BODY constructor selects its mapping bases in `A3`/`A4` and
uses the intended mapping path.  Initializing `A2` there would not repair the
extra call and would invent a register contract the arcade does not have.

## Genesis divergence and first incorrect operation

The earlier whole-function native replacement beginning at original
`0x054052` retired the PC090OJ routine located inside that replaced span,
including original `FUN_000540ac`.  The external retained BSR at original
`0x05480A` nevertheless survived.  Before the correction, reflow resolved it
into live BODY-constructor code rather than the deleted hardware-clear routine.

That unintended call was the first divergence.  It caused a second selector
pass after the legitimate BODY pass.  Because the original call site has no
contract to initialize `A2` for BODY, the extra pass read scene-dependent bytes
through whatever pointer happened to be carried in `A2`.  At the reported early
Segment-5 state those bytes supplied selector `0x66`, leading to the odd
descriptor address and address error already established by the preceding
investigation.

Thus Build 0369 could work later in the stage when unrelated bytes differed;
the apparently position-sensitive behavior was an incidental-data symptom, not
a legitimate direction, stage, flame, or projectile rule.

## Rejected 0370 candidate

The first candidate initialized `A2` at the normal mode-8 BODY branch.  A focused
Genesis NTSC run still faulted at frame 2885 and retained selector `0x66` because
the bad call created another BODY pass after the normal constructor.  That patch
was removed completely.  No part of it is present in the corrected spec or
Build 0371.

## General semantic fix

The authoritative remap now contains:

```json
{
  "arcade_pc": "0x05480A",
  "original_bytes": "6100F8A0",
  "replacement_bytes": ""
}
```

This is a four-byte size-changing replacement, not NOP padding, an RTS bypass,
or an equal-length workaround.  Its semantic cut is the obsolete auxiliary
PC090OJ consumer call; the removed chip tail is the four-record clear at
`0x00D00000`.  Native PLAYER_BODY output is reset and reconstructed through the
existing direct-native lifecycle every frame, so preserving the call would
duplicate a retired hardware operation and no replacement state write is
appropriate.

The address map confirms that copied code ends at original `0x05480A` and resumes
at original `0x05480E`; there is no mapped execution for the removed BSR.

No direction, Segment-5, fireball, selector-range, pointer-alignment, actor, or
hitbox condition was added.  The original collision scan and its legitimate
`A2 = A5+0x0242` assignment remain unchanged.

## Focused Genesis proof

The exact numbered Build 0371 ROM was run under Genesis NTSC MAME using
`tools/mame/scripts/build0370_flame_left_diagnostic.lua`.  This is a focused
diagnostic that injects flame state; it is not a claim of natural pickup-route
coverage.

Evidence directory:

`states/traces/build0371_flame_left_no_second_pass/`

Summary:

```text
reason=mode8_left_attack_probe_complete
frames=2228
diagnostic_flame_injected=YES
left_attack_frames=15
exception=NO
final_pc=07309A
```

The actual selector field (column 25 in the debugger event record) never equals
`0066`.  Raw `0x66` values can still occur in unrelated data/register fields and
must not be mistaken for the fault selector.  The malformed second selector
pass with incidental `A2` is absent, and the left-facing attack probe completes
without an address, bus, illegal-instruction, or crash-handler event.

Result: **fault selector `0x66` eliminated: YES**.

## Normal build gates

The normal Makefile-owned pipeline completed for Build 0371 and produced all
five required same-number variants.  The canonical ROM passed the canonical
gate.  The gameplay-entry gate also passed through 240 required post-entry
frames with:

```text
address_errors=0
bus_errors=0
illegal_instructions=0
crash_handler_entries=0
```

Gate evidence:

- `states/traces/build0371_gameplay_entry_gate_20260923_163959/`
- `states/traces/rastan_direct_video_test_build_0371_mame_30s_20260923_164002/`

The focused MAME proof does not replace the required user BlastEm validation at
the reported natural early-Segment-5 position.

## Artifacts

All artifacts are 1,719,992 bytes; counter is 371.

| Variant | Artifact | SHA-256 |
|---|---|---|
| canonical | `dist/rastan-direct/rastan_direct_video_test_build_0371.bin` | `34ec1ec1753a3a854a8f52de5c7c3946f0578305467491eb07d719b485c1de95` |
| `_d` | `dist/rastan-direct/rastan_direct_video_test_build_0371_d.bin` | `8545625d449831d0dfdf83ade69c6b4e664f091c3fe506d3b64355b9fe8cae50` |
| `_s` | `dist/rastan-direct/rastan_direct_video_test_build_0371_s.bin` | `09024b743e9d52cf849175da321e8bcb2a6c8b98ec9559401f8d22efb396f325` |
| `_do` | `dist/rastan-direct/rastan_direct_video_test_build_0371_do.bin` | `bcf907b7b9227162f8f5e24165227eb29f2e6a70992b811b6f8dc1e4156e5035` |
| `_c` | `dist/rastan-direct/rastan_direct_video_test_build_0371_c.bin` | `817ff3d6a11d43ac994c4bf30fc8e73b22f057a80451629975aead1e8b091cc5` |

## Preservation and deferred work

The fix changes only the obsolete auxiliary PC090OJ clear call.  It leaves the
accepted Build 0369 auxiliary active-field retirement, water-death correction,
flame-sword acquisition/expiration path, collision scan, native visual
compositor, rope interaction, and direct-native architecture intact.

READY sprite presentation and the cave-block palette mismatch remain separate,
deferred visual issues.  No work on either was folded into this build.

## Required user validation

BlastEm validation is still required for the natural flame-sword acquisition and
the exact early-Segment-5 left-facing attack, plus the previously accepted 0369
behavior.  The crash is not declared user-closed until that result is reported.
