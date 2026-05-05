# Cody Build 55b Palette Implementation Report

Date: 2026-05-05
Scope: Build 55b active palette writer hook (`arcade_pc 0x03BA64`)
Mode: Phase A precheck then Phase B implementation

## Phase A (Read-only Gates)

### §A.1 Register-contract gate (4 callsites) — GREEN

Evidence from `build/maincpu.disasm.txt`:
- Caller 1: `0x03AF10 -> bsrw 0x03B9F8` (`line 74017`), post-call uses `%d0` immediately: `0x03AF14 movew %d0,0x3c0000` (`line 74018`).
- Caller 2: `0x03B180 -> bsrw 0x03B9F8` (`line 74193`), post-call `rts` (`line 74194`).
- Caller 3: `0x03B246 -> bsrw 0x03B9F8` (`line 74254`), post-call `rts` (`line 74255`).
- Inner caller (`0x03B9F8`) invokes writer twice:
  - `0x03BA0A -> bsrw 0x03BA64` (`line 74858`)
  - `0x03BA1A -> bsrw 0x03BA64` (`line 74861`)
  Between calls, `%a0` is intentionally not reloaded (only `%d3` and `%a3` are reloaded at `0x03BA0E` and `0x03BA14`), so `%a0` advancement is required.

Contract outcome:
- `%a0` and `%a3` must exit advanced.
- `%d3` must follow loop-decrement semantics to zero.
- `%d0` is observed after outer caller return path (`0x03AF14`), so helper must not blindly restore entry `%d0`.
- `%d1/%d2` are scratch at call boundaries.

### §A.2 Span-safety gate (`0x03BA64..0x03BA87`) — GREEN

Evidence:
- Branch/call targets to `0x03BA..` are only:
  - `0x03BA0A -> 0x03BA64` (`line 74858`)
  - `0x03BA1A -> 0x03BA64` (`line 74861`)
  - internal loop `0x03BA84 bne 0x03BA64` (`line 74896`)
- No external branch target lands inside `0x03BA66..0x03BA85`.

### §A.2.b Loop instruction form — YES

Evidence at `lines 74895-74896`:
- `0x03BA82: subql #1,%d3`
- `0x03BA84: bnes 0x03BA64`

Confirmed long-word decrement loop (`subq.l + bne`), not `dbra`.

### §A.3 Side-effect preservation gate — GREEN

Evidence (`lines 74883-74896`):
- Source read uses post-increment: `movew %a3@+,%d0`
- Destination write uses post-increment: `movew %d0,%a0@+`
- Loop control: `subq.l #1,%d3` + `bne` back-edge.

Required preserved side effects:
- `%a3 += 2` per iteration
- `%a0 += 2` per iteration
- `%d3` decremented to zero on normal positive-count entry

### §A.4 Caller post-call dependency gate — GREEN-CONDITIONAL

Conditional noted from evidence:
- Outer caller path at `0x03AF14` reads `%d0` after return (`line 74018`).
- Helper must preserve mutation behavior (not restore entry `%d0`).
- `%d3` post-loop is not read immediately at outer callsites, but helper still reproduces original `%d3` decrement semantics.

### §A.5 Combined gate

Result: **PROCEED** (GREEN / GREEN-CONDITIONAL with documented plan).

---

## Phase B (Implementation)

### §B.1 `palette_hooks.s` update — COMPLETE

File modified: `apps/rastan-direct/src/palette_hooks.s`
- Added `genesistan_palette_hook_3ba64`.
- Existing Build 55a helpers kept intact (`genesistan_palette_hook_59ad4`, `_03ab00`, `_45dae`).

Implemented properties:
- Bank filter uses `< 4` with explicit skip for high banks (`cmpi.l #4,%d6` / `bhs`).
- `%a0` and `%a3` advance regardless of bank skip path.
- Loop uses `subq.l #1,%d3` + `bne`.
- `%a0/%a3/%d3` are not restored to entry values.
- Conversion path documented and implemented as two-step:
  - original `0x03BA64` raw `0RGB-444 -> xBGR-555`
  - `.Lxbgr555_to_cram` for xBGR-555 -> Genesis CRAM word

Note: helper was corrected to preserve live `%d3` across internal `bsr .Lxbgr555_to_cram` while retaining long-word loop semantics.

### §B.2 Spec update — COMPLETE

File modified: `specs/rastan_direct_remap.json`
- Added `required_symbols` entry: `genesistan_palette_hook_3ba64` (line 143).
- Added new `opcode_replace` at `arcade_pc: 0x03BA64` (line 713).
- `opcode_replace_count` updated `93 -> 94` (line 721).
- Existing Build 55a entries retained unchanged:
  - `0x059AD4` (line 695)
  - `0x03AB00` (line 701)
  - `0x045DB8` (line 707)

### §B.3 Makefile

No Makefile change required for this task (helper added to existing `palette_hooks.s` object).

### §B.4/B.5 Invariant measure and update — COMPLETE

Measured postpatcher invariant after helper fix:
- `total_genesis_bytes_covered=0x17CAE8`
- `opcode_replace patched_site count=94`

File modified:
- `tools/translation/postpatch_startup_rom.py`
- Expected baseline updated to `bytes=0x17CAE8`, `count=94`.

### §B.6 Build-time verification — PARTIAL PASS

Build command:
- `source tools/setup_env.sh && make -C apps/rastan-direct release`

Observed:
- postpatcher invariant gate: PASS (after measured update)
- boot guard: PASS (prepatch and postpatch)
- `build/genesis_postpatch.disasm.txt` shows patched sites:
  - `0x03BC64: jsr 0x712a0` (`line 74813`)
  - `0x03AD00: jsr 0x71248` (`line 73574`)
  - `0x045FB8: jsr 0x7126c` (`line 88526`)
  - `0x059CD4: jsr 0x711e2` (`line 113272`)
- symbol resolution includes all 4 helper symbols in `out/symbol.txt`:
  - `0x000711e2`, `0x00071248`, `0x0007126c`, `0x000712a0`

Numbered output from build run:
- `dist/rastan-direct/rastan_direct_video_test_build_0057.bin`

Requested artifact created by copy:
- `dist/rastan-direct/rastan_direct_video_test_build_0055b.bin`
- Size: `1559272` bytes (`0x17CAE8`)
- SHA256: `703fe9d6c96b6264bb5911be5581acf31845e282e6bb827fab7e2c502c00ee16`

### §B.7 MAME runtime trace verification — FAIL (classification C)

Trace run:
- Driver: `genesis`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0055b.bin`
- Script: `build55b_palette_trace.cmd`
- Artifact: `states/traces/build55b_active_writer_trace_20260505_113900/`
- Duration: `63` seconds (from `mame_stdout_qt.log`)

Counts from `debug.log`:
- `BP_HOOK_3BA64`: `1` hit (`line 34582`)
- `BP_HOOK_59AD4`: `0`
- `BP_HOOK_03AB00`: `0`
- `BP_HOOK_45DAE`: `0`
- `BP_VDP_COMMIT_PALETTE`: `0`
- `BP_VBLANK_SERVICE`: `0`
- `WP_STAGED_PALETTE`: `128`
- `WP_PALETTE_DIRTY`: `1`

Helper-driven staged writes:
- Writes from helper PC (`pc=0x71308`): `64`
- Post-value zero writes: `64`
- Post-value non-zero writes: `0`
- Samples: lines `34682..34710` (all `post=0`).

`palette_dirty` observations:
- Single write at `line 54`: `pc=0x27A pre=0 post=0`.
- `post=1` count: `0`.

Gate status:
- helper hit_count > 0: PASS
- staged non-zero writes from helper: FAIL
- palette_dirty becomes 1: FAIL
- vdp_commit_palette hit_count > 0: FAIL
- CRAM non-`0x0EEE`: NOT PROVEN in this trace

Failure classification: **C** (staging written but `palette_dirty` not set).

### §B.8 Visual verification

User verification pending.

### §B.9 Architecture invariants

No new lifecycle ownership or non-RTS helper behavior introduced.
Build 55b does not alter `vdp_comm.s` pipeline ownership.
Pre-existing invariant-8 issue (bootstrap re-entry) remains pre-existing and out-of-scope here.

---

## Integrity checklist

- Phase A findings cited from disassembly: YES
- Phase B helper preconditions cited: YES
- No invention beyond locked design/evidence: YES
- Postpatcher invariant measured, not presumed: YES
- Build 55a helpers kept: YES
- Bank rule `< 4` (no fold-all mask): YES
- Side-effect advancement on skip: YES
- Loop semantic `subq.l + bne`: YES
- Exit-state preservation intent (`%a0/%a3` advanced, `%d3` decremented): YES
- No broad decompilation used as authority: YES

