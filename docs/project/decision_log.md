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

## 2026-03-16

### Startup/title remap rules must be spec-driven

Decision:

- Move the active startup/title remap rules out of `postpatch_startup_rom.py`
  and into a dedicated `specs/` file.

Why:

- The build manifests should be reports of what happened, not the only place we
  can see the rules after the fact.
- We need a stable source of truth before switching from selected slices to
  whole-ROM carry.

### Whole `maincpu` carry is the target direction

Decision:

- Stop treating boot/title/front-end as a growing list of copied islands.
- Keep the Genesis launcher/header space at the front of ROM, then carry the
  original `maincpu` image as one relocated block.

Why:

- Partial ROM carry keeps creating false failures where control flow lands in
  original data or uncopied islands.
- Whole-ROM carry narrows the problem to relocation rules and hardware
  contracts, which is the real work anyway.

### Normal handoff should be one-way

Decision:

- The normal startup path should eventually leave the launcher behind and not
  return.

Why:

- That matches the final product better than the current preview-driven harness.
- It also lets us reclaim launcher-only memory cleanly after `START RASTAN`.

### Enable whole-maincpu relocated carry in the startup/title patcher path

Decision:

- Enable `whole_maincpu_relocated` in
  `specs/startup_title_remap.json`, with `0x000200` as the relocated ROM base.
- Keep identity overlays for the current bring-up path while front-end entry work
  is still in progress.

Why:

- This removes the missing-island class of ROM closure issues while preserving
  current runtime behavior during transition.
- It lets us move forward from a spec-driven architecture instead of hand-tuned
  Python range lists.

### Add hard validation windows for remap inputs and rewrite targets

Decision:

- Add declared source windows and declared rewrite-target windows to the startup
  remap spec.
- Fail patching if any copied range, rewrite source, or rewrite target falls
  outside those declared windows.

Why:

- Prevent silent remap drift.
- Make invalid address rewrites fail during build instead of surfacing later as
  emulator crashes.

## 2026-03-17

### Force ROM reset vector to launcher entry after postpatch

Decision:

- In `postpatch_startup_rom.py`, rewrite ROM vector `0x000004` (reset PC) to
  symbol `_reset_entry` after remap/copy operations.

Why:

- Whole-maincpu offset carry places original bytes at `0x000200`, and that
  region clobbers SGDK startup bytes if reset still targets `0x000200`.
- The launcher must always run first to establish DIP/config path and startup
  control flow.

### Execute startup/frontend from relocated base only

Decision:

- Run startup/frontend/title code from relocated ROM (`+0x000200`) and disable
  identity-overlay copied slices during bring-up.
- Keep the full SGDK/launcher vector table preserved at `0x000000..0x0003FF`
  and force reset PC to `_reset_entry`.

Why:

- Mixed execution (some windows at original addresses, some relocated) creates
  ambiguous state and recurring control-flow faults.
- A single runtime address model makes traces and fixups deterministic and
  aligns with the declared whole-maincpu strategy.

### Add rule-based absolute ROM target relocation for copied code

Decision:

- Add a declarative `rom_absolute_call_relocation` section to
  `specs/startup_title_remap.json`.
- In `postpatch_startup_rom.py`, scan all copied `original_code` ranges for
  absolute-long ROM target opcodes (`JSR/JMP/LEA/PEA/MOVEA immediate`) and
  relocate targets in `0x000000..0x05FFFF` by `+0x000200`.

Why:

- Relocated execution was still calling old identity ROM addresses (for example
  `JSR 0x055CA2`) and falling into shifted/non-code bytes.
- This fixes the entire class consistently, instead of adding crash-site
  address patches.

### Protect code ranges from blind window pointer rewrites

Decision:

- In `postpatch_startup_rom.py`, apply `window_rewrite_rules` only to non-code
  copied ranges by default.
- Skip window rewrites on `original_code` ranges unless a rule explicitly opts
  in with `allow_in_code=true`.

Why:

- The old sliding long-word rewrite pass could match values across instruction
  boundaries and corrupt valid opcodes/operands.
- We reproduced this directly in the failing front-end dispatcher path
  (`0x03A26C` runtime), where rewritten bytes produced `d0=0xE0FF` and an odd
  jump target (`0x03836B`).
- Guarding code ranges prevents this corruption class while keeping data-range
  pointer rewrites declarative.

### Expand ROM absolute-call relocation to whole relocated maincpu window

Decision:

- Set `rom_absolute_call_relocation.scan_ranges` to
  `whole_maincpu_copy_window`.
- In `postpatch_startup_rom.py`, support whole-window scan mode when
  `whole_maincpu_relocated` is active.

Why:

- Runtime was reaching relocated code paths (for example `0x042130`) that still
  called identity targets (for example `0x055AB4`), causing illegal-instruction
  faults because identity space is not arcade code in this architecture.
- Whole-window relocation keeps absolute ROM call targets consistent with the
  relocated execution model and avoids one-function-at-a-time chasing.

### Relocate embedded ROM pointer tables with narrow, declarative slices

Decision:

- Keep broad `window_rewrite_rules` disabled on `original_code` ranges.
- Add explicit data-slice rules for embedded pointer tables that live inside
  code blocks (starting with title text table `0x03BB7C..0x03BC98`).
- Allow `window_rewrite_rules` to use a literal `new_start` and explicit
  `scan_step` so table relocation stays deterministic and aligned.

Why:

- Title startup was failing at runtime loop `0x03BD6A` because table entries
  still pointed at identity ROM addresses (`0x0003xxxx`) while execution was
  relocated (`+0x200`).
- Re-enabling broad code-range rewrites would reintroduce opcode corruption
  risk; table-slice rewrites fix the pointer class safely and repeatably.

### Re-enable audited code-window rewrites for active startup/game handoff blocks

Decision:

- Keep the default safeguard (`window_rewrite_rules` skip `original_code`
  ranges unless explicitly opted in), but opt in targeted ranges with
  `allow_in_code=true`:
  - `title_init_block`
  - `helper_frontend_timers`
  - `helper_55ca2_dispatch`

Why:

- Live handoff was still hitting unmapped absolute arcade windows from code
  operands, including direct `0x00D00020` accesses in `title_init_block`.
- In BlastEm this surfaced as a freeze on write to `D00020`; in MAME/Exodus it
  surfaced as downstream illegal/address errors after start.
- Opting in audited ranges keeps the remap declarative and holistic for this
  path without re-opening blanket code-range rewrites everywhere.
