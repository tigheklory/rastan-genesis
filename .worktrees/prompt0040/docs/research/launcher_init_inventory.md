# Launcher Init Inventory (`genesistan_init_workram_direct`)

## Purpose
Inventory every field/range/action initialized by `genesistan_init_workram_direct()` and classify whether each should stay in launcher init for a minimal Genesis-safe startup flow.

## Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (Build 96 history, startup forensics, post-init profiling, A5+0x0104 research)
- `README.md`
- `apps/rastan/src/startup_bridge.c`
- `apps/rastan/src/main.c`
- `apps/rastan/src/startup_trampoline.s`
- `build/maincpu.disasm.txt`
- `specs/startup_title_remap.json`
- `build/rastan/startup_common_rom_manifest.json`
- `build/rastan/startup_common_relocations.json`
- Ghidra (arcade): `tools/ghidra/rastan_project/rastan_arcade:maincpu.bin` (cross-checked via prior documented traces)
- Ghidra (Genesis): `tools/ghidra/rastan_project/rastan_genesis:Rastan_5.bin` (cross-checked via prior documented traces)
- MAME reference source: `src/mame/taito/rastan.cpp`, `src/mame/taito/taitoipt.h` (factory-default DIP semantics)

## Address Mapping Note
- Work RAM base in game logic: `A5 = 0x10C000` (arcade view).
- Launcher writes target `genesistan_arcade_workram_words[]`, equivalent to `A5+offset` bytes.
- For ROM-side references in this report, `genesis_rom_addr` is computed as:
  - `patched_maincpu_addr = arcade_addr + cumulative_shift_delta` from `shift_replacements`
  - `genesis_rom_addr = patched_maincpu_addr + 0x200` (relocated whole-maincpu base)

## Findings

### Non-field initialization actions

| Item | Source in `startup_bridge.c` | Current launcher action | Purpose | Classification | safe_to_keep_in_launcher_init | Reason |
|---|---|---|---|---|---|---|
| WRAM clear | `234-236` | `memset(genesistan_arcade_workram_words, 0, ...)` | Establish deterministic baseline | REQUIRED_NON_VIDEO_STATE | YES | Required to avoid stale state and preserve known startup ordering assumptions. |
| Sound CPU reset | `245` | `Z80_startReset()` | Silence/hold Z80 | VIDEO_OR_HARDWARE_INIT | CONDITIONAL | Keep if sound handoff is still explicitly Genesis-side; not part of selector crash chain. |

### Work RAM fields currently initialized

| Address/range (`A5+`) | Current launcher value/pattern | Source lines | Purpose (best determination) | Classification | safe_to_keep_in_launcher_init | Reason |
|---|---|---:|---|---|---|---|
| `0x0000` | `2` | `248` | Main state select (frontend state machine) | REQUIRED_NON_VIDEO_STATE | YES | Needed to enter frontend logic.
| `0x0002` | `0` | `249` | Sub-state reset | REQUIRED_NON_VIDEO_STATE | YES | Required baseline.
| `0x0004` | `0` | `250` | Inner step reset | REQUIRED_NON_VIDEO_STATE | YES | Required baseline.
| `0x0008, 0x000A, 0x000E, 0x0010` | `1,1,1,1` | `253-256` | Coinage runtime fields | REQUIRED_NON_VIDEO_STATE | YES | Mirrors startup coin setup used by later logic.
| `0x0014` | `0x0060` | `259` | Display/control mirror state | MIXED (state + hardware feeder) | CONDITIONAL | Keep state value, but do not reintroduce raw arcade hardware write mechanism.
| `0x0018` | `~dip1` | `262` | DSWA mirror | REQUIRED_NON_VIDEO_STATE | YES | Input/config source for many branches.
| `0x001C` | `~dip2` | `263` | DSWB mirror | REQUIRED_NON_VIDEO_STATE | YES | Input/config source for many branches.
| `0x0026` | `1` | `266` | Init flag | PHASE_FLAG / GATE | YES | Startup path expects initialized flag.
| `0x002C` | `160` | `269` | Initial countdown timer | PHASE_FLAG / GATE | YES | Used by frontend pacing.
| `0x002E` | `mode from ~dip2&0x03 (with 0↔1 swap)` | `272-275` | Gameplay/front-end mode select | REQUIRED_NON_VIDEO_STATE | YES | Matches arcade init derivation.
| `0x0030` | `~dip1 & 0x01` | `278` | Cabinet bit latch | MIXED_EFFECT | CONDITIONAL | Keep logical field; avoid raw orientation-hardware side effects.
| `0x0032` | `~dip1 & 0x02` | `281` | Flip-screen bit latch | MIXED_EFFECT | CONDITIONAL | Same as above.
| `0x0036` | `bonus_table[index]` | `284-287` | Bonus-life config | REQUIRED_NON_VIDEO_STATE | YES | Gameplay-affecting config.
| `0x0038` | `diff_table[index]` | `290-293` | Difficulty config | REQUIRED_NON_VIDEO_STATE | YES | Gameplay-affecting config.
| `0x0040` | `0` | `296` | Competition/debug flag | REQUIRED_NON_VIDEO_STATE | YES | Baseline for non-debug path.
| `0x0044` | `0` | `297` | Alt/debug flag | REQUIRED_NON_VIDEO_STATE | YES | Baseline for non-debug path.
| `0x004A` | `0x00AA` | `300` | Sprite/init marker | PHASE_FLAG / GATE | YES | Referenced by transition/runtime checks.
| `0x0080..0x00BF` | `all zero` (from WRAM clear) | `234-236` | Transition buffer block A | REQUIRED_NON_VIDEO_STATE | CONDITIONAL | Needs coherent ordering with paired blocks; zero baseline alone may be insufficient if swap helpers are bypassed.
| `0x00C0..0x00FF` | `all zero` (from WRAM clear) | `234-236` | Transition buffer block B | REQUIRED_NON_VIDEO_STATE | CONDITIONAL | Same as above.
| `0x0100..0x013F` | mostly zero; `A5+0x0100=1` explicitly | `303` + clear | Transition block C + title flag | PHASE_FLAG / GATE | CONDITIONAL | `A5+0x0100` participates in transition sequencing; keep only if execution order requires it (not proven as root cause). 
| `0x0104` | `1` | `304` | Critical gate byte | PHASE_FLAG / GATE | NO | Proven to close seed gate at `0x04528C`, skipping `A5+0x0117/0x0118` seeding.
| `0x0117` | no explicit write; remains cleared | clear only | Selector mirror byte | REQUIRED_NON_VIDEO_STATE | YES (remain clear initially) | Should be seeded naturally by `0x04527E` when gate is open.
| `0x0118` | no explicit write; remains cleared | clear only | Selector byte used by `0x0561D6/0x0561FE` | REQUIRED_NON_VIDEO_STATE | YES (remain clear initially) | Must be seeded by natural arcade path, not by launcher direct write.
| `0x0140..0x0166` (39 bytes) | ROM copy from `rastan_maincpu+0x3B0D4` | `313-323` | Config table copy | REQUIRED_NON_VIDEO_STATE | YES | Mirrors arcade `0x03B0C2` config copy behavior.

## Explicit requested fields/ranges
- `A5+0x0100`: currently forced to `1`; keep only conditionally pending final ordering proof.
- `A5+0x0104`: currently forced to `1`; **must not be asserted in launcher pre-seed phase**.
- `A5+0x0117` / `A5+0x0118`: launcher does not seed; this is correct for natural seed ownership, provided `A5+0x0104` is not asserted too early.
- Transition buffers `A5+0x0080`, `A5+0x00C0`, `A5+0x0100`: currently zero-baselined by WRAM clear, with `A5+0x0100` then overridden to `1`.

## Uncertainties
- Whether launcher should set `A5+0x0100 = 1` immediately is not fully proven from static flow alone; it is not the proven selector-gate root cause.
- Transition-buffer correctness depends on whether `0x03A294/0x03A2B2` are active or bypassed in the current spec; this influences required preconditioning.

## Conclusion
- Launcher currently seeds a broad startup state that mixes required non-video config with phase gates.
- The proven harmful write is `A5+0x0104 = 1` in launcher init.
- Most DIP/config/state fields can remain launcher-seeded, while gate-sensitive fields must respect original sequencing ownership.
