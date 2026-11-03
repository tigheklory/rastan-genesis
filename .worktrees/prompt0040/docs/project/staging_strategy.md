# Staging Strategy

The port needs staged subsystem bring-up, but those stages should still be
explicit and recoverable.

## Allowed stages

- `null`
  - subsystem accepts calls and preserves the minimum contract the original code
    expects
- `shadow`
  - subsystem preserves writes/readback/state in Genesis-owned memory and may
    provide a diagnostic visualization
- `shim`
  - subsystem translates original expectations into Genesis-side services
- `native`
  - subsystem is mapped to the final intended Genesis implementation

## Shared debug rule

Temporary subsystems should not each invent their own debug output.

Instead:

- emit structured events into the shared debug bus
- let a single debug/HUD/logging consumer decide how to visualize those events

This keeps null/shadow subsystems focused on preserving contracts, not on
building one-off diagnostics.

## Why this matters

Examples:

- null audio may need to acknowledge command writes and log unsupported command
  ids
- shadow video may need to report unexpected write patterns or invalid tile ids
- startup translation may need to report MMIO touches before final handlers
  exist

All of those are useful, but none of them should hardcode their own UI.
