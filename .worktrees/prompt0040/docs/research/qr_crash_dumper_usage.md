# QR Crash Dumper Usage

This document now tracks only the QR-specific behavior in mode `2`.

For the full selector (mode `0/1/2`), use:
- `docs/research/exception_dumper_modes.md`

## Purpose
Describe the machine-readable QR crash output used by the mode-2 exception dumper.

## Compile-time Selector
Use `RASTAN_EXCEPTION_DUMPER_MODE=2` to enable QR output.

## Build
```bash
source tools/setup_env.sh
make -C apps/rastan release RASTAN_EXCEPTION_DUMPER_MODE=2
```

## QR Payload
Primary payload:
`V1|E..|P........|S....|0........|1........|A0........|A1........|A5........|T........|U........|W................|F........|B...`

Fallback payload:
`V1|E..|P........|S....|A1........|A5........|T........|B...`
