# AGENTS.md

This file is the working guide for coding agents in this repository.

## Mission

Port arcade-accurate `Rastan` behavior to Sega Genesis while preserving original
assets and as much original game logic as possible.

Current development preference:

- avoid one-off crash-site hacks
- keep rules declarative in `specs/`
- favor build-time translation/remap over runtime patch tricks

## Repo map

- `apps/rastan/`: active SGDK launcher/baseline app
- `tools/translation/`: patchers and translation tooling
- `specs/`: source-of-truth rules for layout/remap/fixups
- `build/`: disposable generated files and manifests
- `dist/`: released ROM builds
- `docs/project/`: execution plans and decision log
- `docs/reverse-engineering/`: disassembly notes and behavior references
- `docs/reference/`: external hardware docs and captures
- `attic/`: historical experiments (not baseline)

## Build and run

Always load local toolchain first:

```bash
source tools/setup_env.sh
```

Primary build commands:

```bash
make -C apps/rastan release
make -C apps/rastan release-nohook
make -C apps/rastan debug
```

Output ROMs:

- working ROM: `apps/rastan/out/rom.bin`
- named builds: `dist/Rastan_<n>_<timestamp>.bin`

## Current startup/title bring-up status

- Stable launcher baseline exists in recent `56`-style hooked flow.
- Normal mode live front-end attempts (`57`/`59`) still fail with control-flow
  issues (e.g. falling into `0x03816B` data path).
- Test mode is currently stable but still routed to preview/debug path, not the
  full board-style diagnostics screen.

## Critical engineering constraints

1. Prefer holistic remap changes over incremental trampoline stepping.
2. Keep manifests as outputs, specs as inputs.
3. Preserve original `maincpu` behavior as much as possible; remap hardware
   contracts rather than rewriting gameplay logic.
4. Minimize shadow/backing RAM usage to only what the translated hardware
   contract needs.
5. Treat normal `START RASTAN` handoff as one-way target architecture.

## Files to check before touching startup remap

- `docs/project/startup_title_remap_plan.md`
- `docs/project/decision_log.md`
- `specs/startup_title_remap.json`
- `tools/translation/postpatch_startup_rom.py`
- `apps/rastan/src/startup_trampoline.s`
- `apps/rastan/src/startup_bridge.c`
- `apps/rastan/src/main.c`

## MAME and reverse-engineering references

- Rastan MAME driver: `src/mame/taito/rastan.cpp` (external reference)
- Local disassembly: `build/maincpu.disasm.txt`
- 68000 reference manual:
  - `docs/reference/hardware/motorola_68000_reference_manual.pdf`

## Agent guardrails

- Do not treat `attic/` behavior as authoritative.
- Do not silently change build architecture (copy mode, ROM base, entry flow)
  without updating `docs/project/startup_title_remap_plan.md` and
  `docs/project/decision_log.md`.
- If a change affects remap logic, update `specs/` first (or in the same change)
  and then update the patcher.
- Avoid destructive git commands (`reset --hard`, checkout rollback) unless
  explicitly requested.

## Preferred workflow for substantial remap changes

1. Update plan/decision docs.
2. Update spec rules in `specs/`.
3. Update patcher/tooling to consume spec.
4. Build with `make -C apps/rastan debug`.
5. Validate generated manifests under `build/rastan/`.
6. Then produce a release build for emulator testing.
