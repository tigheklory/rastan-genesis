# Repository Structure

This document records the cleaned structure for the project after flattening the
old `Genesistan/` wrapper back into the repo root.

The goal is simple:

- one project root
- one active app baseline
- one shared runtime
- one specs database
- one docs tree
- one attic for experiments we are not trusting

## Current Layout

```text
/
├── README.md
├── Makefile
├── apps/
│   ├── README.md
│   └── rastan/
├── attic/
│   ├── README.md
│   └── startup-common-rom/
├── build/
│   └── rastan/
├── dist/
├── docs/
│   ├── README.md
│   ├── project/
│   ├── reference/
│   └── reverse-engineering/
├── roms/
├── runtime/
├── specs/
├── tools/
│   ├── shared/        (future shared helpers if needed)
│   ├── translation/
│   ├── build_rastan_regions.py
│   └── setup_env.sh
├── video/
└── examples/
```

## Meaning Of Each Area

- `apps/`
  - Runnable ROM projects we actively build and test.
  - Current baseline: [apps/rastan](/home/tighe/projects/rastan-genesis/apps/rastan)
- `attic/`
  - Preserved experiments and broken runners we do not trust as the baseline.
  - Current attic entry: [attic/startup-common-rom](/home/tighe/projects/rastan-genesis/attic/startup-common-rom)
- `build/`
  - Disposable generated intermediates.
  - Safe to delete and regenerate.
- `dist/`
  - Named ROM releases we intentionally keep.
- `docs/project/`
  - Structure, roadmap, staging, startup execution notes, ROM provenance, variants.
- `docs/reference/`
  - Durable validation references like board-video notes.
- `docs/reverse-engineering/`
  - Disassembly and tracing research.
- `runtime/`
  - Shared runtime/shim code used by active or experimental ROMs.
- `specs/`
  - Machine-readable rules that drive translation, extraction, and validation.
- `tools/translation/`
  - Translation-specific scripts.
- `examples/`
  - Generic SGDK samples only, not active project code.

## Rules

### Active baseline

The known-good text baseline lives in:

- [apps/rastan](/home/tighe/projects/rastan-genesis/apps/rastan)

If we make a bring-up change that needs to be trusted day to day, it should
land here or in shared `runtime/`.

### Experiments

If a ROM or runner is useful but currently unreliable, it belongs in:

- [attic/](/home/tighe/projects/rastan-genesis/attic)

That keeps it available without pretending it is the current baseline.

### Build outputs

Generated outputs belong in:

- `build/rastan/` for disposable manifests, slices, extracted artifacts
- `dist/` for named ROM releases we intentionally keep

We should not scatter meaningful release artifacts across app-local `out/`
directories or old `build/genesistan/` trees.

### Reverse-engineering notes

All research that informs the port belongs in:

- [docs/reverse-engineering/](/home/tighe/projects/rastan-genesis/docs/reverse-engineering)

This keeps the research close to the port without forcing it into build output
directories.

### Specs

Persistent translation metadata belongs in:

- [specs/](/home/tighe/projects/rastan-genesis/specs)

If a transformation does not fit the existing spec categories, we should add a
new spec instead of hiding it inside code or a random patch file.

## What We Intentionally Stopped Doing

- no nested `Genesistan/` project root
- no active code living under `examples/`
- no named releases under `build/`
- no stale path references as the primary documentation

## Migration Notes

These moves were preserved without discarding research:

- `examples/hello-rastan` -> `apps/rastan`
- `Genesistan/startup-common-rom` -> `attic/startup-common-rom`
- `Genesistan/runtime/*` -> `runtime/`
- `Genesistan/specs/*` -> `specs/`
- `Genesistan/tools/*` -> `tools/translation/`
- root reverse-engineering docs -> `docs/reverse-engineering/`

The old `Genesistan` name may still appear in some internal C symbol prefixes.
That is only a code namespace issue now, not a repository structure issue.
