# RG-016 — READY / Continue Presentation Ownership Analysis

## Scope and baseline

This is the bounded pre-build ownership proof for RG-016. Accepted Build 0473 remains immutable at
`accepted/build-0473` / `f6e975b864af2aca7bdf24b0a40a9db43bd62f59`. Build 0474 and source
`70622388b1dc21c22aa8c3ccaa194abf4ab9575a` remain rejected and permanently consumed. Its terminal-
death HOLD successfully hid the post-disintegration reconstruction and both mixed native gameplay
generations, but real Genesis hardware proved that the same HOLD leaked across READY and Continue.

Static provenance reuses the canonical Ghidra exports, original linear disassembly, generated address
map, RG-003/RG-004 frontend reports, RG-015 evidence, and current production source. No new route,
save state, gameplay trace, or state machine was created.

## Bounded presentation ownership map

| Retained event | Arcade source | Owner after event | Display | Reason |
|---|---:|---|---|---|
| final disintegration / terminal death | `0x051998` | unsafe gameplay turnover | OFF | Preserve Build-0474 suppression before reset semantics can reconstruct the player against the old scene. |
| human READY construction | `0x03A6E8..0x03A748` | READY being prepared | OFF | PLAYER/READY, ROUND/digit, palette and dwell are not complete until the final state write. |
| READY dwell entry | `0x03A74E` | complete READY | ON after publication | Original `A5+0x0004=7` follows every retained READY producer and begins the 112-tick dwell. Gameplay residency is irrelevant to this frontend presentation. |
| READY dwell exit | `0x03A75C` | unsafe gameplay turnover | OFF | Original `A5+0x0004=4` ends READY before gameplay resource replacement. |
| gameplay fill completion | `0x050482` | gameplay pending publication | OFF until publication | Existing native boundary has complete Plane names; fixed-order VBlank must still commit CRAM, patterns, names, SAT and scroll. |
| fixed-order DMA completion | `dma_publish_frame` completion | coherent gameplay | ON | Existing RG-015 publisher consumes readiness only after one matching generation is committed. |
| final-life frontend reset | `0x03A2D8` through retained `0x03AD4C` call | frontend/Continue being prepared | OFF | Scene-0 residency, palette, clean SAT and cleared names are installed before retained content producers. |
| Continue construction | `0x03A31C..0x03A36E` | Continue being prepared | OFF | The panel, four text groups, optional credit text, countdown state and dwell are still being authored. |
| Continue dwell entry | `0x03A374` | complete Continue | ON after publication | Original `A5+0x0004=8` is the first retained state after all Continue producers complete. No gameplay resource is required. |
| Continue accepted / gameplay re-entry | `0x03A504..0x03A54E`, then retained scene selection | Continue until native gameplay install starts | ON, then OFF at `load_scene_tiles(1)` | No speculative exit blank is needed. The scene loader is the first actual unsafe native-resource boundary and already disables display. |
| Continue expiry / terminal transition | `0x03A4F8..0x03A4FC` | terminal presentation being prepared | retained display until complete | Retained cleanup and state 4 lead to the terminal GAME OVER producer; no gameplay generation is exposed. |
| terminal GAME OVER construction | `0x03A420..0x03A444` | GAME OVER being prepared | prior safe frontend or OFF | Retained block/text/timer state is not complete until the state transition. |
| terminal GAME OVER dwell entry | `0x03A448` | complete GAME OVER | ON after publication | Original `A5+0x0004=6` follows the complete retained producer and begins its 160-tick dwell. |

## Root cause and correction

The Build-0474 hook at internal `0x055FD2` never owns human-session READY. `0x055DDC` returns early
with `A5+0x1394=0x00FF`; caller `0x03A6B2` constructs READY itself. The global latch therefore remained
HOLD. Final death inherited the same HOLD through the frontend reset and Continue construction.

The smallest correction keeps the three-state presentation latch and moves/extends only its semantic
events: remove the unreachable `0x055FD2` reveal; request publication-gated visibility after retained
`0x03A74E`, `0x03A374`, and `0x03A448`; mark unsafe again after retained `0x03A75C`. No owner enum is
needed because every complete retained presentation can replace an earlier unsafe-generation state.
Continue-to-gameplay needs no new hook: `load_scene_tiles` already blanks at the first real resource
turnover, and the existing `0x050482` plus DMA-completion path owns coherent gameplay reveal.

## Hook safety

Each insertion preserves the complete original six-byte `MOVE.W #imm,(d16,A5)` before one absolute
JSR. The helper preserves SR/CCR and all registers it uses; JSR/RTS balance the stack. Each site is
followed immediately by retained `RTS` or begins a new retained state on the next controller tick, so
there is no fall-through branch predicate to reinterpret. Variable-length replacements use canonical
shift-table reflow; generated address-map, relative-control-flow, declared jump-table and absolute-
operand verification remain mandatory before publication.

The semantic cut is retained death/READY/Continue/GAME-OVER ownership -> final Genesis display
safety. The chip tail remains the already-retired PC080SN/PC090OJ execution below the accepted native
producers. No gameplay authority, polling, wait-N delay, framebuffer, chip shadow/emulation, NOP, or
RTS bypass is added.

## Tool reuse

Existing project tools reused: canonical Ghidra exports; `build/maincpu.disasm.txt` / linear export;
current address map; `final_life_zero_input_regression.lua`; `rg004_frontend_probe.lua`; existing build
and verification pipeline.

New tooling created: none. The two established regression scripts receive only bounded visibility
assertions required by RG-016.

Why new tooling was necessary: not applicable.
