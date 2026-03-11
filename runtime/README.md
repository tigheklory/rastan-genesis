# Runtime

This directory will hold the Genesis-side implementation.

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
