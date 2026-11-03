# Cody — Genesis-Native Death Presentation Optimization

Date: 2026-10-15  
Accepted baseline: USER-ACCEPTED Build 0428  
Candidate: Build 0433  
Semantic authority: `docs/design/Cody_enemy_death_drop_semantic_validation.md`

## Scope and result

This task did not reopen death/drop semantics or perform new gameplay research.
It replaced the broad universal-general presentation route for the proven finite
death families with generated compact death records and a purpose-built direct
queue loop. Retained translated arcade code still owns damage, death state,
timing, selectors, score/drop decisions, allocation, linkage and retirement.

The optimized domain is exhaustive:

- ordinary death: base `0x0A73`, compositor 2, selectors `0x0B..0x12`;
- fountain/burst: base `0x0275`, compositor 0, selectors `0x9D..0xA0`;
- bat pop: base `0x0275`, compositor 0, selector `0xA8`;
- enemy-death reward: base `0x0A5A`, compositor 2, selectors `0x13..0x23`;
- both compositor orientations for every selector.

That produces 60 exact frame-index records. There are no unresolved records.

## Previous Build-0428 route

The ordinary `0x0A73` death, Flying-Demon/boss fountain, bat pop and reward
frames used the broad universal-general record:

```text
10-byte piece = s16 dx, s16 dy, u16 signed pattern delta,
                 u16 attr, u8 size, u8 flags
```

Runtime interpreted dynamic-base flags, added the actor pattern base per piece,
loaded per-piece attributes/flags, selected the generalized emitter and then
entered the shared residency/queue/SAT machinery. The bank-`0x30` burst phases
`0x9E..0xA0` already used the accepted compact Level-B path; `0x9D` did not.

## New route and record format

The generator independently decodes the authoritative universal record and
emits:

```text
8-byte frame index = u32 piece_offset, u8 count, u8 status, u16 frame_attr
6-byte piece       = s16 dx, s16 dy, u16 final raw pattern code
```

`final raw pattern code` means the generator has already applied the descriptor
mode and signed delta to the actor-family base. The existing finalizer still
turns `(raw code, effective bank)` into the exact residency/variant key. This is
necessary because one shared geometry/pattern stream legitimately appears in
several palette contexts; it avoids duplicating geometry while preserving the
accepted dynamic palette-variant authority.

Runtime selection is bounded by exact base, compositor, selector and
orientation. On a hit it establishes the frame attribute, actor X/Y, semantic
lane, queue base/count/end and queue cursor once. Its six-byte loop then loads
`dx/dy/code`, applies actor coordinates, checks hidden Y and queue capacity, and
appends the final four-word semantic tuple directly. It does not call the
generalized per-piece emitter.

All target frames proved frame-attribute invariant. No expanded per-piece
attribute format was needed. Actor `+0x27` low-byte override semantics are
applied once per frame, preserving flip, priority and effective-bank behavior.

## Shared `0x0275 / 0x9D..0xA0` strategy

One generated geometry/pattern stream covers all four phases, including the
previously omitted first phase `0x9D`, in both orientations. The retained packed
frame context supplies the effective bank:

- bank `0x30`: `0x9D` uses the new compact death path; accepted Build-0426
  Level-B records retain precedence for `0x9E..0xA0`;
- Flying Demon bank `0x35`: all `0x9D..0xA0` use the new death path;
- representative boss bank `0x3F`: all `0x9D..0xA0` use the same new records.

The static verifier explicitly checks the embedded `0x30` context and the
actor-low-byte override compositions producing `0x35` and `0x3F`. Geometry,
order, raw pattern identity and size are shared rather than triplicated.

## Ordinary death, bat and reward handling

The `0x0A73 / 0x0B..0x12` domain is fully generated: exact counts, order,
coordinates, post-delta pattern codes, frame attributes and both orientations.
Bat `0x0275/A8` and reward `0x0A5A/13..23` naturally use the same table and loop,
so both lower-priority families are included without another runtime mechanism.

## Work removed and retained

Moved offline:

- compositor descriptor selection and mapping-stream parsing;
- per-piece mode and signed-delta interpretation;
- orientation geometry transformation;
- piece count, ordering, size and frame-attribute classification;
- family base plus pattern delta;
- death-domain classification metadata.

Hoisted once per frame:

- frame attribute and actor override;
- actor X/Y;
- semantic lane, queue base/count/end and initial append cursor.

Remaining per piece:

- coordinate addition;
- hidden-Y and capacity checks;
- four-word queue append/count update;
- unchanged finalizer work for palette variant, residency, DMA worklist and SAT.

## Static equivalence and regression protection

`verify_pc090oj_frame_table.py` independently decoded and compared all 60
records against the authoritative existing universal decode. It verified exact
count, order, `dx/dy`, post-delta pattern identity, frame attribute, fixed size,
both orientations, and the `0x30/0x35/0x3F` fountain contexts. Result: PASS.

`verify_pc090oj_direct_dispatch.py` verified the private single-caller contract,
exact three-base prefilter, frame-wide context, direct D1/D2/D3/D4 tuple order,
hidden-Y/capacity/count behavior, queue bounds, A4/A5 preservation, and unchanged
shared residency/worklist/SAT finalization. Result: PASS.

Unrelated universal-general records are unchanged and remain the miss route.
Build-0426 compact common-enemy frames and Build-0428 player records retain
their earlier precedence and passed their existing gates.

## Files modified

- `apps/rastan-direct/src/pc090oj_hooks.s`
- `apps/rastan-direct/src/pc090oj_assets.s`
- `apps/rastan-direct/Makefile`
- `tools/translation/precompute_pc090oj_frame_table.py`
- `tools/translation/verify_pc090oj_frame_table.py`
- `tools/translation/verify_pc090oj_direct_dispatch.py`
- `tools/translation/postpatch_startup_rom.py`
- `tools/translation/verify_canonical_rom.py`

Generated assets are `build/pc090oj_death_frame_index.bin` (480 bytes) and
`build/pc090oj_death_piece_table.bin` (1,074 bytes). Intentional linked-image
growth crossed one alignment page, updating canonical covered bytes from
`0x291EB8` to `0x292EB8`; opcode-replacement count remains 231.

## Build and gates

Labels `0429..0432` remain consumed and preserved. This task produced only
Build 0433; the initial coverage-invariant stop occurred before numbering.

- frame-table/death equivalence: PASS (60 native, 0 unresolved);
- direct-dispatch/queue contract: PASS;
- boot guards: PASS;
- canonical gate: PASS (`GATE_PASS`);
- fixed gameplay-entry gate: PASS, zero address/bus/illegal/crash exceptions;
- mandatory fixed 30-second trace: completed, 1,798 frames;
- phase-epoch gate: reported `epoch=FAIL` because the fixed route observed only
  record/epoch 0; the established build workflow preserved the ROM and recorded
  this status exactly as designed;
- complete same-label family: PASS (`.bin`, `_d`, `_s`, `_do`, `_c`).

Canonical artifact:

```text
dist/rastan-direct/rastan_direct_video_test_build_0433.bin
size: 2698936 bytes
SHA-256: 145fc9038ac682b6cc195f51a075457184a426431692b8426513fa2f4f419ef6
```

## Build 0433 deterministic rope-race benchmark

At Tighe's explicit authorization, the existing unmodified deterministic
Genesis NTSC rope benchmark was run for its established three trials against
the numbered canonical Build 0433 ROM.

```text
trial 1: 803 frames / 13,400.588 ms
trial 2: 803 frames / 13,400.588 ms
trial 3: 803 frames / 13,400.588 ms
deterministic: YES
```

The median result is **803 frames / 13,400.588 ms**. Compared with accepted
Build 0428, the change is **0 frames / 0.000 ms / 0.000%**. Compared with the
original-arcade Silver Standard of 771 frames / 12,850.000 ms, Build 0433
remains **32 frames / 550.588 ms** behind. This is **NO GLOBAL REGRESSION** and
matches the expected little-or-no-change outcome because the rope route does
not exercise the optimized death presentations.

Evidence: `states/traces/build0433_rope_attach_benchmark/`.

- Existing project tools reused:
  `tools/mame/run_rope_attach_performance_benchmark.sh`, its unchanged
  `rope_attach_performance_benchmark.lua`, and the established summarizer.
- Test platform: **GENESIS NTSC**, MAME `genesis` driver.
- New tooling created: **NONE**.
- Why new tooling was necessary: **not applicable**.
- Other gameplay driven: **NO**.
- No new gameplay trace script, route, harness, or non-benchmark trace was
  created; only the established benchmark's normal TSV/stdout evidence was
  emitted.
- Source modified: **NO**.
- New ROM built or build label consumed: **NO**.

## Acceptance

- Gameplay acceptance: **USER MUST VERIFY**.
- Rope benchmark: **803/803/803; NO GLOBAL REGRESSION**.
- Primary localized validation: **USER-DRIVEN `_do` BLACK-BAR TEST** for
  ordinary, simultaneous ordinary, Flying-Demon paired and boss-fountain deaths.
- Gameplay driven by Cody: **NO**.
- New gameplay traces: **NO**.
- Phase D started: **NO**.
- Phase E started: **NO**.
