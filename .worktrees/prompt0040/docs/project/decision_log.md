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

### Remap low startup hardware probe window (0x052A+) into Genesis shadows

Decision:

- Add a dedicated copied/remap range for the low startup probe routine
  `0x00052A..0x00066C` in `specs/startup_title_remap.json`.
- Apply in-code window rewrites for that range so legacy probe spans are
  redirected into shadow memory:
  - `0x10C000..0x10FFFF` -> `genesistan_arcade_workram_words`
  - `0x200000..0x201FFF` -> `genesistan_shadow_200000_words`
  - `0xC00000..0xC07FFF` -> `genesistan_shadow_c_window_words`
  - `0xC08000..0xC0FFFF` -> `genesistan_shadow_c_window_words`
  - `0xD00000..0xD00FFF` -> `genesistan_shadow_d00000_words`
- Add absolute rewrites in this range for all explicit hardware constants used
  by that code (inputs, control regs, and C/D window constants), including
  bounded end-pointer offsets where the probe uses start/end address pairs.

Why:

- Emulator repros moved past earlier dispatcher faults and now fail later with
  illegal writes to mirrored VDP/HV-port space.
- The `0x052A` startup probe still performed raw arcade memory tests against
  `C`/`D` windows, which on Genesis can alias hardware ports (`C00008` class).
- This fix keeps the approach declarative/spec-driven and removes another
  untranslated hardware-contract path without adding runtime ad-hoc hacks.
- For the `D00000..D01000` probe pair, we map the end constant to a bounded
  shadow end offset so the translated probe stays inside the existing WRAM
  shadow budget.

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

### Re-enable audited `frontend_core` C-window rewrites for live front-end text pages

Decision:

- Keep `window_rewrite_rules` defaults unchanged for code ranges overall, but
  opt in the `frontend_core` C-window rules (`0x00C00000..0x00C10000`) with
  `allow_in_code=true`.

Why:

- Build `76` reaches the normal startup result and then faults in the first
  live front-end tick before progressing into title flow.
- BlastEm reports a hard freeze on direct C-window access at `0x00C09EA3`.
- That operand is in `frontend_core` (`0x03A552` / `0x03A55C`) and was not
  being remapped because code-range window rewrites were still skipped there.
- Opting in only the audited C-window rules for `frontend_core` fixes this
  concrete untranslated-address class without reopening broad in-code rewrites
  for unrelated windows.

### Add explicit helper remap coverage for post-launch control and score paths

Decision:

- Add declarative absolute remap mappings for:
  - `helper_display_control` (`0x03ADD8..0x03AE85`) C50000/D01BFE/380000 and
    C-window writes (`0x00C00100`, `0x00C08100`).
  - `helper_3d044_score_digit` (`0x03D044..0x03D053`) score-digit C-window
    write at `0x00C08C66`.

Why:

- Build `77` still faulted on `START RASTAN` with raw hardware writes:
  - BlastEm: freeze on write to `0x00C50000`.
  - MAME: follow-on address faults during coin/start flow.
- These addresses were in active helper code that executed after launcher
  handoff but were not included in current rewrite groups.
- Adding explicit helper rules keeps this spec-driven and deterministic
  (no crash-site runtime patching) while preserving whole-ROM relocated
  execution policy.

### Keep startup probe C/D-window aliases inside bounded shadow buffers

Decision:

- In `startup_hw_probe_052a`, map `0x00C04000` and `0x00C0C000` to the
  `genesistan_shadow_c_window_words` base alias (no end-offset).
- In the same range, map `0x00D01000` to the
  `genesistan_shadow_d00000_words` base alias (no end-offset).

Why:

- The prior offsets resolved to one-past the allocated shadow arrays:
  - C-window: `+0x4000` on a `0x4000`-byte shadow.
  - D-window: `+0x0800` on a `0x0800`-byte shadow.
- That risks pointer escape into unrelated WRAM and non-deterministic failures
  during startup probe execution.
- This keeps remap behavior deterministic and within the current WRAM budget.

### Add audited in-code C-window rewrites for startup-common and low probe path

Decision:

- Add `window_rewrite_rules` with `allow_in_code=true` for:
  - `startup_common` C-window spans (`0x00C00000..0x00C10000` split by 0x4000 pages)
  - `startup_hw_probe_052a` C-window spans (`0x00C00000..0x00C10000`)
  - `startup_hw_probe_052a` D-window probe span (`0x00D00000..0x00D00800`)

Why:

- Recent startup traces show execution reaching `startup_common` and then
  immediately falling into repeated exception UI handling, while BlastEm reports
  illegal writes in VDP/HV-port space.
- Existing startup/probe remap relied mostly on explicit absolute constants,
  which does not cover all in-code window-derived operands (for example
  `0x00C00000` base + small offsets such as HV-port aliases).
- This keeps the fix declarative/spec-driven and range-scoped to audited startup
  code, instead of adding one-off crash-site runtime patches.

### Roll back `allow_in_code` window rewrites after launcher opcode corruption

Decision:

- Remove all `allow_in_code=true` entries from
  `specs/startup_title_remap.json` `window_rewrite_rules`.

Why:

- The launcher regressed into immediate startup corruption (garbled screen and
  illegal-instruction faults around `0x03B2xx`), indicating opcode stream
  mutation.
- Window rewrites that operate on raw 32-bit patterns in code can match across
  instruction boundaries and transform opcodes, even when the matched value
  looked like a valid address constant.
- For now, keep window rewrites data-only and rely on explicit declarative
  remap entries (`absolute_rewrite_groups`) until operand-position-aware code
  rewriting is implemented.

### Add explicit `title_init_block` D-window remaps for text-object buffer writes

Decision:

- Add explicit absolute mappings in `title_init_block` for:
  - `0x00D00000`
  - `0x00D00020`
  - `0x00D00088`
  - `0x00D000E0`
  - `0x00D00128`
  all targeting `genesistan_shadow_d00000_words` with byte offsets.

Why:

- BlastEm freeze reproduced on `START RASTAN` with:
  `machine freeze due to write to address D00020`.
- Disassembly confirms this is a real startup/title path literal:
  `0x03B8B4: lea 0x00D00020,a1` (plus nearby `D00088/D000E0/D00128`).
- Because code-window rewrites are intentionally disabled (to avoid opcode
  clobber), these literals must be covered by explicit spec mappings.

### Expand `helper_d000_init` range to include `0x03AD4C..0x03AD72`

Decision:

- Widen `helper_d000_init` copied/remap range start from `0x03AD72` to
  `0x03AD4C`.
- Add explicit absolute remap for `0x00D00170` in `helper_d000_init`.

Why:

- Disassembly shows `0x03AD4C..0x03AD70` is part of the same D-window init
  helper and contains:
  - `0x03AD50: lea 0x00D00000,a0`
  - `0x03AD62: lea 0x00D00170,a0`
- This preamble sat outside the previous remap range, leaving at least one
  `0x00D00000` literal untranslated and allowing direct D-window writes in
  startup/title paths.
- Keeping this fix in `specs/startup_title_remap.json` preserves the
  declarative, build-time remap policy and avoids runtime crash-site patches.
