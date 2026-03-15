# Rastan Genesis Decision Log

## 2026-03-13

### Translation database first

Decision:

- Store translation rules declaratively under `specs/`.
- Rebuild from original ROMs every time.

Why:

- Prevent irreversible drift from patched outputs.
- Keep every change tied to original addresses and evidence.

### Startup block as first execution target

Decision:

- First real opcode target is `0x03AE86..0x03B05C`.

Why:

- It is literally the first substantial block run after reset handoff.
- It exercises MMIO, work RAM, display RAM, and DIP reads without requiring the full game loop.

### Runtime configuration belongs in specs

Decision:

- Software DIP defaults and control mapping policy live in `runtime_config.json`.

Why:

- These are user-visible policy choices and should not be buried inside the translator or runtime glue.

### Original hardware video references are first-class validation inputs

Decision:

- Track board-capture videos in dedicated docs notes.
- Use them to validate boot, title, attract, and credit behavior.

Why:

- They preserve timing and sequencing details that are easy to miss when
  reconstructing behavior from disassembly alone.
- They help distinguish "real arcade behavior" from harness-side invention.
