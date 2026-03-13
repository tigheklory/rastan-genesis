# Genesistan Runtime

This directory is reserved for the Genesis-side runtime that will host patched
arcade code blobs.

Planned responsibilities:

- install Genesis-side memory shims expected by translated arcade code
- expose remapped MMIO entry points
- upload converted text/tile/sprite assets to the VDP
- jump into patched original `68000` code slices

This runtime should stay narrow. Its job is to host translated original code,
not to become a second handwritten reimplementation of Rastan.
