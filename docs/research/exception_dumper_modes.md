# Exception Dumper Modes

## Purpose
Provide compile-time-selectable crash exception handling with three modes:
- mode `0`: SGDK handlers (explicit opt-in)
- mode `1`: default custom compact text-only dumper
- mode `2`: custom QR dumper

Mode 1 exists to keep WRAM/code footprint lower than QR mode while preserving high-value crash forensics on one screen.

## Compile-time Flag
`RASTAN_EXCEPTION_DUMPER_MODE`

## Mode Values
- `0` = SGDK exception vectors and behavior
- `1` = Default custom text-only dumper (no QR generation/rendering)
- `2` = Custom QR dumper

## Build Commands
```bash
source tools/setup_env.sh

# Mode 1 (default)
make -C apps/rastan release
make -C apps/rastan debug

# Mode 0 (explicit SGDK behavior)
make -C apps/rastan release RASTAN_EXCEPTION_DUMPER_MODE=0

# Mode 2 (QR custom dump)
make -C apps/rastan release RASTAN_EXCEPTION_DUMPER_MODE=2
```

## What Mode 1 Shows
Single-screen compact dump with fixed-width hex fields:
- exception name/code + build number
- `PC`, `SR`
- `A0`, `A1`, `A5`, `SP`
- `D0`, `D1`
- short backtrace line pair (up to 6 entries)
- stack words `S0/S1/S2` (12 words total)

## What Mode 2 Shows
- short human-readable summary
- machine-readable QR payload
- deterministic payload schema with fallback compact payload

## Why Mode 1 Exists
- avoids QR payload/tile buffers
- avoids QR encode/render code path
- keeps crash output screenshot-friendly for fast debugging

## Limitations
- mode 1 backtrace is heuristic and derived from exception frame words, not a full unwinder
- mode 2 may inherit existing postpatch/startup coupling limits in current hooked release pipeline
- no automatic QR scanner verification is included in build scripts

## Validation Rule
For startup/title graphics validation:
- launcher/config/startup menu text is not valid proof of game title/attract rendering
- exception-handler text is not valid proof of game title/attract rendering
- SGDK/debug text is not valid proof of game title/attract rendering
- only real game title/attract text shown before exception handling is valid proof
