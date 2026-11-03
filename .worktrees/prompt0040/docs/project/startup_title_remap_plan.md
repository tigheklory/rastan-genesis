# Startup/Title Remap Plan

This note resets the approach for boot-to-title bring-up.

## Current direction

The project should now move toward:

- whole-`maincpu` ROM carry, not hand-maintained slice hunting
- declarative remap rules under `specs/`, not hidden Python tables
- one-way normal handoff from launcher to Rastan
- minimal translated RAM/MMIO backing, only where the original logic truly
  expects persistent state
- launcher-first reset flow (ROM reset vector must target launcher entry, not
  clobberable opcode payload offsets)

The current slice-based patcher was useful for discovery, but it is no longer
the architecture we want to converge on.

## Current checkpoint

The most useful checkpoint before the next architecture change is:

- `Rastan_56_20260316_155200.bin`

That build gave us:

- stable launcher
- stable normal-path preview return
- stable test-path preview return
- working preview rerun/back behavior

Later builds taught us more, but they also mixed in front-end entry
experiments.

- `57`/`59` proved the current normal-mode failure is not just "missing copied
  ROM bytes"
- the remaining failure is a control-flow / entry-contract issue in the live
  front-end path

The recent build sequence taught us something useful:

- the launcher and payload packing are not the main problem
- the current startup/title remap model is too ad hoc
- we have been mixing three problems together:
  - ROM slice selection
  - memory-map remapping
  - host preview / rerun lifecycle

The next phase should treat startup/title as one static remap problem, not as a
series of trampoline experiments.

## Current stable facts

### Stable launcher / preview baseline

- `Rastan_56_20260316_155200.bin`

This is the last build where:

- the launcher renders correctly
- first launch in normal mode returns to the preview
- first launch in test mode returns to the preview
- rerun and return still behave as expected

### The launcher is not being overwritten by the patcher

The launcher code still lives in low Genesis ROM space, while the copied arcade
code/data ranges live in the packed `maincpu` payload area.

So the immediate black-screen regressions are not explained by Python patching
over launcher code.

### The real problem is the memory contract

For the startup/title/front-end path, the original Rastan code expects a set of
absolute windows and registers to exist and behave correctly.

That is the main translation problem.

This is much closer to a "board contract remap" than a simple opcode relocation.

## What the current process got wrong

The current build path in:

- [postpatch_startup_rom.py](/home/tighe/projects/rastan-genesis/tools/translation/postpatch_startup_rom.py)

does three things at once:

1. copies selected original code/data ranges into the Genesis ROM
2. rewrites absolute references to host-side shadow buffers
3. relies on the trampoline to walk forward through original continuation helpers

That was useful for discovery, but it is now the wrong architecture for the next
step.

In practice it caused us to:

- add original helpers incrementally
- grow or shrink shadows reactively
- debug launcher, rerun behavior, and startup mapping in the same loop

That is why progress has felt noisy.

## Proven startup/title windows

These are the important absolute windows touched by the startup and front-end
code we have traced so far.

### Work RAM / state

- `0x10C000..0x10FFFF`

This is the main `a5` work RAM base for startup and front-end logic.

### Startup test / palette shadow

- `0x200000..0x203FFF`

This is touched very heavily during startup, including the bus/palette-style
test loops at `0x03AEB6` and `0x03AEDA`.

### Title / display windows

- `0xC00000..0xC03FFF`
- `0xC04000..0xC07FFF`
- `0xC08000..0xC0BFFF`
- `0xC0C000..0xC0FFFF`

These are explicitly cleared by the common startup block:

- `0x03AF2C`
- `0x03AF3C`
- `0x03AF52`
- `0x03AF62`

### D/tile scratch

- `0xD00000..0xD007FF`
- `0xD01BFE`

### Small control / latch / DIP / input regs

- `0x350008`
- `0x380000`
- `0x390001`
- `0x390003`
- `0x390005`
- `0x390007`
- `0x390009`
- `0x39000B`
- `0x3C0000`
- `0x3E0001`
- `0x3E0003`
- `0xC20000`
- `0xC40000`
- `0xC50000`

## One confirmed bug in the current remap

The startup block clears the title/display windows as full `0x4000` byte ranges:

- `0xC00000`
- `0xC04000`
- `0xC08000`
- `0xC0C000`

But the current host buffers are:

- `genesistan_shadow_tile_scratch_words[0x1000]`
  - `8192` bytes
- `genesistan_shadow_c08000_words[0x1200]`
  - `9216` bytes

So the current remap is mapping `16 KB` arcade windows into smaller host
buffers.

That is a real bug, not a theory.

It means we have been debugging startup/title behavior on top of invalid backing
storage.

## One false alarm we can discard

Earlier we saw a seeming `a5 + 0x4E00` work RAM access in the disassembly.

That came from data inside the `0x03B098..0x03C484` block being disassembled as
code. It is not currently good evidence that the title/front-end path requires a
true `0x4E00` byte live work RAM span.

So we should not size work RAM around that false outlier.

## Input strategy

Input should stay simple.

We do not need 6-button pad support for Rastan.

A 3-button Genesis pad is enough:

- D-pad = 8-way movement
- `B` = attack
- `C` = jump
- `START` = start
- `A` = coin

The correct model is:

- keep the small arcade input bytes the original code expects
- feed them live from Genesis controller state

That gives us a final-port-friendly design without pretending inputs are generic
shadow RAM.

This is already cleaner than before, but it is not the main RAM saver.

## Sound strategy for title/front-end

We do not need full Genesis audio to reach title.

But we do need a valid sound command/status handshake so the original code does
not stall or misbehave when it hits the sound path.

So the correct short-term model is:

- sound command shim
- sound ready/status shim
- no real playback yet

That is still final-port-friendly code, not throwaway debug logic.

## What we should stop doing

For the next phase, avoid:

- adding more original continuation helpers one by one in the trampoline
- expanding or shrinking shadows speculatively
- changing launcher preview/rerun behavior while debugging startup/title
- treating rerun/back-from-preview as an important milestone

Those loops have given us useful clues, but they are no longer the right method.

## What we should do next

### 0. Make the remap rules authoritative

Before the next big execution change, the active startup/title remap rules
should live in a spec file:

- [startup_title_remap.json](/home/tighe/projects/rastan-genesis/specs/startup_title_remap.json)

The Python patcher should consume that spec and emit manifests from it.

That means:

- manifests become build outputs
- the spec becomes the source of truth
- switching from slice-copy to whole-`maincpu` carry becomes a spec/policy
  change, not a rewrite of Python literals

### 1. Freeze the launcher baseline

Treat the stable launcher behavior as protected.

The launcher is only responsible for:

- configuration UI
- `START RASTAN` handoff

Once the game starts, launcher RAM can be reclaimed except for the DIP state and
small persistent handoff state.

### 2. Remove preview-driven bring-up from the main strategy

Preview / rerun was a useful probe.

It is not part of the final converted game, so it should stop being the main
test harness for title/front-end bring-up.

The real target is:

- boot
- title/front-end/attract loop

### 3. Define one startup/title memory contract

Before the next significant build, we should define:

- which original ranges we carry
- which absolute windows they need
- what exact backing each window gets

That contract should be static and documented, not inferred from the latest
crash.

### 4. Remap the startup/title slice as a whole

The next patching pass should treat this as one scope:

- common startup block
- normal boot continuation into title/front-end
- title/front-end/attract path

Not as separate trampoline hops.

### 4a. Replace slice carry with whole-ROM carry

The target carry model is:

- Genesis vectors/header own `0x000000..0x0001FF`
- the entire original `maincpu` image is copied as one relocated block
- absolute ROM references are rewritten against that relocated base
- hardware-facing references are rewritten against translated Genesis-side
  contracts

That removes the whole class of "forgot to copy this data island" failures.

### 5. Back only the windows the title/front-end path truly needs

We should use the MAME traces and the disassembly to determine:

- which windows must be full-sized
- which can be shared
- which can be shrunk
- which can be direct register shims

But we must start from correct sizes where the original code explicitly clears or
writes whole windows.

### 6. Fix the live front-end entry contract

The current live front-end runner enters `0x03A008` through a synthetic
exception frame and returns via `RTE`.

That is still the strongest current suspect for the normal-mode crash after ROM
closure was improved. The next front-end pass should treat that entry contract
as a first-class problem instead of patching downstream crash sites.

## Recommended immediate execution order

1. Move the active startup/title remap rules into `specs/`.
2. Reconfirm the real startup/title window sizes from disassembly.
3. Write down the startup/title/front-end memory contract.
4. Switch the carry model from selected slices to whole `maincpu`.
5. Fix the front-end entry contract against that relocated whole-ROM build.
6. Test for:
   - real title/front-end progression
   - real test-mode screen only as a secondary reference

## Success condition

The next real milestone is not:

- "the preview returned again"

It is:

- "the original normal boot reaches the real title/front-end sequence"

That is the first meaningful target that matches the final converted game.
