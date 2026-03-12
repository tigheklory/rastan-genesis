# Rastan Reverse-Engineering Workflow

This file defines how to document new disassembly coverage consistently.

The goal is to avoid repeating the earlier pattern:

- spot an interesting sprite
- force it into the harness
- later discover it belonged to helpers/effects

## Working Principles

1. Prefer ownership proof over visual plausibility.
2. Record what is confirmed separately from what is inferred.
3. Document helper-only paths explicitly so they stop wasting time.
4. Keep raw addresses in every note.
5. Use the raw disassembly as ground truth and the docs as structured overlays.

## Recommended Order For New Work

1. Start from a confirmed gameplay fact.
2. Find the RAM fields that change.
3. Identify the actor list or subsystem consuming those fields.
4. Trace the constructor/setup path for that actor.
5. Record family/frame/tile-base/attr only after ownership is established.
6. Only then mirror or port the path into Genesis code.

## What To Create When A New Area Is Studied

When a new subsystem or range becomes important:

1. add or update a subsystem reference doc
2. add the important addresses and status to
   [docs/disassembly_coverage.md](/home/tighe/projects/rastan-genesis/docs/disassembly_coverage.md)
3. add any dumped table outputs to `build/`
4. link the new material from
   [docs/disassembly_index.md](/home/tighe/projects/rastan-genesis/docs/disassembly_index.md)

## How To Mark Confidence

Use these meanings consistently:

- `confirmed`
  backed by direct disassembly, table decode, or validated runtime behavior
- `strong candidate`
  multiple direct clues, but still missing one ownership proof
- `false lead`
  explicitly disproven and should not be retried casually

## Minimum Data To Record For A Routine

When documenting a routine, capture:

- address
- subsystem
- inputs read
- RAM fields written
- actor list touched
- important callees
- whether it is body-facing, helper-only, or still unresolved

## Minimum Data To Record For An Actor Path

When documenting an actor path, capture:

- actor list base
- entry size
- activation/constructor path
- update path
- render path
- family/state/class fields
- confirmed coordinate source

## Table Dumps

If a routine depends on tables, prefer generating a dump into `build/` rather
than transcribing values manually into prose.

Current examples:

- [build/02c8_tables.txt](/home/tighe/projects/rastan-genesis/build/02c8_tables.txt)
- [build/4543e_tables.txt](/home/tighe/projects/rastan-genesis/build/4543e_tables.txt)
- [build/0508_state_handlers.txt](/home/tighe/projects/rastan-genesis/build/0508_state_handlers.txt)

## Harness Rule

Do not put a new visible sprite candidate into the Genesis harness unless:

- the actor owner is proven or very strongly constrained
- the family/frame/tile-base path is documented
- the reason for choosing that path is written down

Otherwise the harness becomes a source of confusion instead of validation.

## Recommended Next Documentation Targets

In order:

1. complete a dedicated `0x02c8` body-path reference
2. complete a dedicated `0x0508` upstream/state-cluster reference
3. deepen sprite-family coverage beyond family `1` only if ownership requires it
4. map lower-value helper clusters after the body path is nailed down

