# RG-015 — Death/Respawn Visibility and Genesis VDP Loading Semantics

## Scope and result

Static provenance proves that the reported sequence is a Genesis presentation-ownership
failure, not an arcade death/respawn gameplay-state failure. The retained arcade program
correctly completes death, changes lives, enters READY, and returns to gameplay. Genesis
currently exposes two native-resource intervals which the arcade hardware does not have:

1. after the last disintegration step, retained state resets can stage a new player body while
   the dead gameplay scene remains visible; and
2. gameplay scene-fill completion enables display before the following fixed-order VBlank has
   committed the matching palette, SAT, and scroll generation.

The RG-015 correction is therefore a finite presentation-only latch. It never tests or changes
life count, player state, READY state, coordinates, selectors, collision, or control flow.

## Evidence reused

This analysis began with the canonical Ghidra project/exports, the canonical original disassembly,
the generated address map, current production source, and the established final-life route. No new
general trace, input movie, AI gameplay, or manually navigated route was created.

The Ghidra coverage export currently marks `0x055DDC..0x0565A5` unclassified. That is an explicit
coverage fact, not a reason to invent behavior: the canonical original instruction stream and prior
RG-003/RG-004 reports already preserve the complete state dispatch needed here. The relevant static
chain is:

| Arcade event | Original evidence | Meaning |
|---|---|---|
| death terminal | `0x05198A` compares death step with `0x0038`; `0x051992` writes phase 4; `0x051998` clears subphase | final visible disintegration has completed and terminal/restart control begins |
| human-session READY dispatch | `0x055DDC` sees state `<9` plus nonzero `A5+0x0034`, sets `A5+0x1394=0x00FF`, and returns to `0x03A6B8` | the long internal `0x055DDC` states 9..13 are not the human post-death READY producer |
| READY authored | `0x03A6E8..0x03A748` emits PLAYER/READY, ROUND/digit, and the remaining retained presentation calls; `0x03A74E` advances subphase to 7 | complete human post-death READY producer boundary |
| READY exit | subphase-7 dwell at `0x03A756`; `0x03A75C` advances to subphase 4 when its 112-tick timer expires | native gameplay resources become unsafe after the visible READY dwell |
| gameplay names complete | retained `0x0503DC` fill returns at `0x050482` after all 64 publications | final Plane A/B staging is complete, but the next VBlank has not yet published the matching generation |

The accepted Build 0473 final-life evidence independently records two non-final cycles. On the first,
death state 8 begins at frame 913, terminal phase 4 is reached by frame 970, and the retained player
state becomes 0 at frame 986 while restart presentation continues. The corresponding second cycle
does the same at frames 1722/1779/1795. This is why the native body path can reconstruct Rastan at the
death location: it is faithfully consuming reset semantic state while Genesis incorrectly leaves the
old gameplay presentation visible.

## Current native publication ordering

`load_scene_tiles` synchronously installs pattern residency with VDP display off, stages the selected
palette, and currently enables display unless `genesistan_scene_present_pending` is set.
`fg_boundary_install_post_reseed`, called at mapped arcade `0x050482`, performs full Plane B and Plane A
name DMAs, clears dirty state, and currently enables display immediately.

That immediate enable is premature. `_vblank_service` later calls `vdp_prepare_sprites` and then the
single `dma_publish_frame`, which commits in this order:

1. CRAM;
2. dirty patterns;
3. Plane B;
4. Plane A;
5. sprite patterns and SAT;
6. scroll.

Consequently the known one-frame wrong sky palette/player coordinate/pose is the interval between
the direct Plane-name completion and that next complete VBlank publication. The next frame is correct
because all generations have then converged.

## Semantic cut and chip tail

The semantic cut remains above hardware realization:

> retained arcade death terminal, READY producers/exit, and scene-fill completion → Genesis display
> safety around final native Plane/CRAM/SAT/scroll publication.

The retained arcade program still decides death, life decrement, READY timing/content, player reset,
respawn state, coordinates, pose, and gameplay re-entry. Below that cut, Genesis owns only whether a
native generation is safe to scan out.

No PC090OJ or PC080SN emulation, object/tilemap shadow, framebuffer, gameplay state machine, or wait-N
delay is introduced. The already-retired PC090OJ tuple/SAT and PC080SN chip-write tails remain retired.
RG-015 removes the two premature Genesis display-enable consequences and replaces them with a
publication-completion event. No transitional compatibility mechanism is added.

## Correctness model

`genesistan_presentation_readiness` has exactly three presentation states:

- `0`: normal visibility;
- `1`: native resources are unsafe, so display remains off;
- `2`: retained/native producers are complete; the next completed VBlank publication may enable.

The event sequence is:

1. `0x051998` preserves the original subphase clear, then marks presentation unsafe before the
   following reset/body path can become visible.
2. The existing `0x056440` frontend owner reset also marks unsafe before installing scene-0 patterns,
   palette, SAT, scroll, and blank planes.
3. The first Build-0474 candidate incorrectly requested reveal at `0x055FD2`. Bounded runtime evidence
   proved that human post-death flow bypasses that internal state-12 path, so the latch remained HOLD
   throughout READY. Build 0474 is rejected and permanently consumed.
4. The proven correction point for a future candidate is `0x03A74E`, after every human-session READY
   producer and before its 112-tick subphase-7 dwell. The corresponding display-off event is the retained
   dwell expiry at `0x03A75C`, before gameplay residency replacement.
5. `0x050482` completes the retained gameplay fill and full Plane name DMAs, then requests reveal rather
   than enabling directly.
6. The following complete VBlank commits matching CRAM, Plane, sprite/SAT, and scroll state; only then is
   gameplay displayed.

This is event-driven. The publisher consults one finite presentation latch at its completion boundary;
there is no polling loop and no arbitrary frame delay.

## Regression strategy

The established zero-input final-life route was extended only with bounded observations of VDP register
1, the presentation latch, READY controller state, scene/pending/palette readiness, native player count,
emitted SAT count, coordinates, and selectors. It continues to drive only coin/start and explicitly
releases every gameplay control. It asserts that HOLD is never visible, READY state 13 is visible,
post-READY loading contains a display-off interval, and both natural non-final deaths return through a
coherent first visible gameplay state. No OCR is used.

The extension rejected Build 0474 because `ready_visible_frames=0`. It also proved that HOLD never
became visible and that both post-death gameplay reveals occurred only after the completed fill/VBlank
handoff. Both first visible returns were identical: player state `3`, X `0x0020`, Y `0x0030`, selectors
`0x0000/0x000C`, scene `1`, scene-pending `0`, body count `9`, emitted SAT count `11`. These latter facts
validate the gameplay reveal half of the design but cannot compensate for hidden READY.

## USER MUST VERIFY

On real Genesis hardware, Tighe must verify both a non-final death and its restart: normal complete
disintegration; no reconstruction at the death location; visible `READY!`; a clean black native-loading
interval after READY; and a first visible gameplay frame with the correct spawn position, falling/neutral
pose, animated sky palette, terrain on both planes, complete Rastan sprite graphics, HUD, and no one-frame
flicker or mixed old/new tiles. Continue, GAME OVER, title/attract, score, 1UP, damage, and rope behavior
must remain unchanged.
