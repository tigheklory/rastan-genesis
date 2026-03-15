# Startup Hardware-Test Reference

This note is the first concrete execution target for the port.

It covers the startup block:

- entry: `0x3AE86`
- normal continuation: `0x3B05C`
- test-mode diversion: `0x000100`

This should be read as the common startup/basic system-test path, not the full
detailed service/test program selected by the DIP switch.

## Why this block goes first

This is the first substantial arcade code run after the reset vector handoff,
and it runs regardless of the DIP-selected detailed test mode:

- vector `PC = 0x3A000`
- immediate branch to `0x3AE86`

So if the port is serious about running original opcodes, this block is the
right place to start.

## Proven behavior in the block

### Hardware / control clears

- `0x00C50000`
- `0x00D01BFE`
- `0x00350008`
- `0x00380000`
- `0x003E0001`
- `0x003E0003`

These need Genesis-side MMIO policy, not gameplay reinterpretation.

### Memory / bus test loops

The code hits `0x00200000` twice in 8192-iteration loops:

- read word
- write same word back

This is a real startup hardware test behavior and should be preserved in spirit
through the translation pipeline.

### Work RAM initialization

- copies/clears `0x0010C000`
- then sets `a5 = 0x10C000`

This establishes the main work RAM base used throughout the game and throughout
our prior reverse-engineering notes.

### Display RAM clears

- `0x00C00000`
- `0x00C08000`
- `0x00C04000`
- `0x00C0C000`

These are startup display/text windows and should map to Genesis-side shadow
buffers or direct VDP upload paths later.

### DIP/config reads

- `0x00390009`
- `0x0039000B`
- `0x0005FF9E`

These drive the startup configuration state stored in low work RAM.

### Test mode branch

At `0x3B04E`:

```asm
btst #2, a5@(25)
beq  0x3B05C
jmp  0x0100
```

This is the proven startup split between:

- normal boot
- test/service startup

The harness work already aligned this with DIP bank 1 switch 3.

The important scope rule for this project is:

- start by executing the common block that reaches this split point
- treat it as the always-run basic system test and startup path
- do not start by targeting the detailed test program at `0x0100`

## Immediate translation requirements

To execute this block honestly on Genesis, the project needs:

1. original slice bytes copied into the ROM image
2. controlled entry into `0x3AE86`
3. remap/trap handling for the absolute MMIO accesses above
4. a Genesis-owned work RAM region matching the arcade expectations around
   `0x10C000`
5. explicit handling for the `0x0100` test-mode jump target

## Current artifact

Running:

```bash
make patch-maincpu
```

emits:

- `build/rastan/startup_common_slice.bin`
- `build/rastan/startup_common_manifest.json`

Those are still extraction/manifest artifacts, not executable translated code
yet, but they give us a stable first target that does not depend on more
behavioral reconstruction.

## Current executable runner boundary

The first executable test of this block was preserved in:

- `attic/startup-common-rom`

It remains useful as a reference experiment, but it is not the current baseline
ROM anymore. The active baseline app now lives in:

- `apps/rastan`

What is original in that ROM:

- `0x03AE86..0x03B05B`
- `0x03A552..0x03A565`
- `0x03B098..0x03C483`
- `0x03AD3C..0x03AD4B`
- `0x03AD72..0x03ADBB`
- `0x03B0C2..0x03B102`
- `0x03B9F8..0x03BA87`
- `0x04EAF6..0x04F0F5`
- `0x04FE62..0x04FE81`
- `0x05B512..0x05B513`
- `0x05FFA2..0x05FFFF`

What is remapped at build time:

- arcade MMIO/control addresses
- arcade work RAM base
- startup display/object/text windows
- the `0x200000` startup RAM/bus-test window

What is still stubbed:

- test-mode diversion beyond `0x0100`
- the rest of the normal boot loop after the first title-init handoff
- detailed service/test program at `0x0100`

Current normal-boot behavior is now:

1. run original common startup/basic system-test code at `0x03AE86`
2. take the normal branch at `0x03B04E`
3. hit a tiny patch stub at `0x03B05C` that only records the normal result
4. immediately jump back into original code at `0x03B098`
5. let the original title-init/text writers populate the `0xC08000` shadow layer

The current ROM therefore proves:

- original startup/common opcodes can execute on Genesis
- helper/data dependencies can remain original ROM bytes
- compile-time address remapping is sufficient for this first slice
- original title-init/text emission can run after startup without a C rewrite

without yet claiming that the full normal boot or full service program runs.
