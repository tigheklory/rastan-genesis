# Specs

This directory holds the persistent translation database for the project.

Rules here are the source of truth for any nontrivial transformation applied to
the original arcade ROM data.

Principles:

- original ROMs are always the input
- `build/` is disposable
- emitted binaries are never hand-edited
- every move, fixup, reorder, palette change, or shim call must be explainable
- every rule should point back to original addresses and evidence

The intended spec split is:

- `startup_title_remap.json`: active build-driving remap rules for the current boot/title/front-end bring-up path
- `symbols.json`: stable identities for original code/data objects
- `objects.json`: extracted code/data slices and their dependencies
- `extraction_manifest.json`: ROM source provenance, set version, and required file hashes
- `variants.json`: supported regional/revision sets and measured differences
- `fixups.json`: code/data patch rules
- `relocations.json`: placement policy and per-build relocation expectations
- `layout.json`: Genesis ROM placement and section policy
- `subsystem_modes.json`: staged null/shadow/native implementation policy
- `debug_bus.json`: shared debug-event channels and reporting policy
- `gfx_rules.json`: graphics/palette/tile conversion rules
- `audio_rules.json`: sound/music conversion and routing rules
- `refactor_rules.json`: rare semantic replacements that cannot stay as raw opcodes
- `runtime_config.json`: software DIP defaults, control maps, user-facing options
- `validation_rules.json`: smoke/regression checks tied to known arcade behavior

If a transformation cannot be described in one of these specs, that is a signal
to stop and decide whether it really belongs in the pipeline.
