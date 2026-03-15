# Runtime

This directory holds the shared Genesis-side runtime and shim code for the
project.

Planned areas:

- startup and memory map
- arcade `68000` compatibility / shim layer
- VDP/tile/sprite backend
- controller/input layer
- audio driver integration
- gameplay reimplementation or translated logic layer
- extracted-data loaders and lookup tables

The runtime should treat arcade ROM content as input data, not bundled source.

Near-term direction:

- build a Genesis execution harness for selected arcade `68000` code
- back arcade RAM and MMIO with Genesis-side shadow state
- translate arcade video/audio-facing accesses into Genesis backends

## Current shared pieces

- [startup_hooks.h](/home/tighe/projects/rastan-genesis/runtime/startup_hooks.h)
- [startup_hooks.c](/home/tighe/projects/rastan-genesis/runtime/startup_hooks.c)
- [debug_bus.h](/home/tighe/projects/rastan-genesis/runtime/debug_bus.h)
- [debug_bus.c](/home/tighe/projects/rastan-genesis/runtime/debug_bus.c)

These are shared support layers for startup experiments, translated opcode
execution, and temporary subsystem staging.
