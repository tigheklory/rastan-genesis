# Minimal Correct Launcher Init Design (While Skipping C/D Window Init)

## Purpose
Define the correct launcher-side initialization strategy that preserves required non-video runtime state and sequencing, while explicitly avoiding full `startup_common` restore and avoiding C-window/D-window hardware-init behavior.

## Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (Build 96 history; Startup Initialization Forensics; Post-Init WRAM profiling; A5+0x0104 execution-order analysis)
- `README.md`
- `docs/research/a5_0104_write_map.md`
- `docs/research/a5_0104_read_map.md`
- `docs/research/selector_seed_path.md`
- `docs/research/execution_order_comparison.md`
- `apps/rastan/src/startup_bridge.c`
- `apps/rastan/src/main.c`
- `apps/rastan/src/startup_trampoline.s`
- `build/maincpu.disasm.txt`
- `specs/startup_title_remap.json`
- `build/rastan/startup_common_rom_manifest.json`
- `build/rastan/startup_common_relocations.json`
- Ghidra (arcade): `tools/ghidra/rastan_project/rastan_arcade:maincpu.bin` (cross-check from existing research traces)
- Ghidra (Genesis): `tools/ghidra/rastan_project/rastan_genesis:Rastan_5.bin` (cross-check from existing research traces)
- MAME reference source: `src/mame/taito/rastan.cpp`, `src/mame/taito/taitoipt.h`

## Address Mapping Note
- `A5+offset` addresses refer to game-owned WRAM state (`0x10C000` base in arcade logic).
- ROM addresses shown as both `arcade_addr` and `genesis_rom_addr` where known (shifted + relocated mapping).

## Findings

## A) INITIALIZE IMMEDIATELY IN LAUNCHER

| Address/range | Value / rule | Why | Evidence |
|---|---|---|---|
| `A5+0x0000`, `+0x0002`, `+0x0004` | `2, 0, 0` | Required frontend state-machine entry baseline. | `startup_bridge.c` lines `248-250`; frontend entry `0x03A008` uses these fields.
| WRAM baseline | Clear all game-owned workram first | Prevent stale state and preserve deterministic startup state. | `startup_bridge.c` `234-236`; arcade init does equivalent clear at `0x03AEEA..0x03AF02`.
| `A5+0x0008/+0x000A/+0x000E/+0x0010` | coinage defaults | Needed non-video configuration consumed by later logic. | Arcade setup at `0x03B020..0x03B044`.
| `A5+0x0018`, `A5+0x001C` | `~DIP1`, `~DIP2` | Source fields for all downstream difficulty/bonus/mode/cabinet logic. | Arcade writes at `0x03AF7A..0x03AF8E`.
| `A5+0x0026` | `1` | Init-flag behavior expected by frontend flow. | Arcade write at `0x03B020`.
| `A5+0x002C` | `160` | Countdown/timer pacing in frontend startup phases. | Launcher/arcade parity (`startup_bridge.c` `269`; runtime timers in `0x03A3D4`, `0x03A8AC`).
| `A5+0x002E` | mode from DIP formula | Required mode selection state. | Arcade derivation at `0x03AFD2..0x03AFEA`.
| `A5+0x0036`, `A5+0x0038` | bonus/difficulty derived from DIP | Gameplay-affecting config, non-video. | Arcade derivation at `0x03AF96..0x03AFB6`.
| `A5+0x0040`, `A5+0x0044` | `0` for default debug flags | Keeps non-debug baseline. | Arcade source is `0x05FF9E` bits at `0x03AFEE..0x03B00A`; default world rev1 yields zero.
| `A5+0x004A` | `0x00AA` | Marker checked in transition/state paths. | Arcade write at `0x03B064`; checks around `0x055CAC`.
| `A5+0x0140..+0x0166` | copy 39-byte config table | Required table/config bytes expected by runtime logic. | Arcade helper `0x03B0C2`.

## B) MUST REMAIN CLEAR / UNASSERTED INITIALLY

| Address/range | Required initial state | Why | Evidence |
|---|---|---|---|
| `A5+0x0104` | must stay `0` before seed path | Early nonzero closes gate at `0x04528C`, skipping selector seed and causing underflow crash path (`0x0561D6/0x0561FE`). | Proven chain in prior research and AGENTS_LOG root-cause section.
| `A5+0x0117`, `A5+0x0118` | remain clear until natural seed routine executes | Must be written by `0x04527E` in correct order, not launcher-forced. | Seed writes at `0x045292/0x045296` gated by `A5+0x0104`.

## C) MUST BE LEFT TO LATER ARCADE FLOW

| Address/range / routine | Leave to later arcade flow | Why | Evidence |
|---|---|---|---|
| First assertion of `A5+0x0104` | yes | Ownership belongs to original runtime handlers (`0x03A1F2`, `0x03A7EC`) after seed-gate phase. | Write map and execution-order comparison.
| Selector seed (`A5+0x0117/+0x0118`) | yes, via `0x04527E` | Correct side effects include source derivation from `0x05FF9E` and gate semantics. | `0x04527E` routine behavior.
| Transition-buffer evolution (`A5+0x0080/+0x00C0/+0x0100` runtime mutations) | yes | These buffers are manipulated by shared transition logic; launcher should only baseline them, not emulate full runtime progression. | `0x03A294/0x03A2B2/0x03A2D0` and follow-on calls.

### Design choice statement
The correct design is:
- **launcher initializes required non-video baseline state and leaves `A5+0x0104` clear**,
- while preserving natural arcade ownership of selector seeding and subsequent gate assertion.

`A5+0x0100` is **more nuanced**: evidence does not prove it is the direct crash cause, so any change to its launcher timing should be gated behind explicit transition-flow validation.

## C-window / D-window Skip Boundary

### Explicitly rejected from restore
- Startup/common direct C-window tilemap clears/fills (`0x03AF2C..0x03AF72`, `0x03AE64` behavior as raw MMIO mechanism).
- Startup/common direct D-window/orientation/control MMIO register writes (`0x03AE86`, `0x03AE8E`, `0x03AE96`, and raw display-control register writes).
- Full wholesale replay of `startup_common` including board-specific hardware side effects.

### Useful non-video side effects that still must exist (recreated selectively)
- WRAM baseline clear semantics.
- DIP mirror and derived gameplay config fields.
- Coin/config table initialization.
- Selector seeding ownership/order (`0x04527E` path with gate open).
- Transition buffer coherence as consumed by later runtime logic.

## === RECOMMENDED_FIX_PLAN ===
- launcher_fields_to_keep:
  - `A5+0x0000/+0x0002/+0x0004`, coinage fields, DIP mirrors, mode/difficulty/bonus fields, default debug flags, `A5+0x004A`, config copy at `A5+0x0140..0x0166`, and WRAM clear baseline.
- launcher_fields_to_remove_or_delay:
  - remove/delay launcher write `A5+0x0104 = 1` until after natural seed phase; do not directly write `A5+0x0117/+0x0118`.
- fields_that_must_be_initialized_elsewhere:
  - `A5+0x0117/+0x0118` via `0x04527E` natural seed path; first runtime `A5+0x0104` assertion via arcade handlers.
- earliest_safe_point_for_A5+0x0104_to_become_1:
  - after successful execution of `0x04527E` with gate open (i.e., after selector bytes are seeded).
- whether_A5+0x0100_should_change:
  - not yet by design default; treat as conditional pending dedicated transition-flow validation (no proven direct causality in current crash chain).
- whether_transition_buffers_need_launcher_init:
  - baseline clear YES (via WRAM clear), but runtime ordering/mutation should remain arcade-driven.
- whether_selector_seed_should_happen_naturally:
  - YES.
- risks_if_we_change_too_little:
  - selector gate remains closed early, crash path persists.
- risks_if_we_change_too_much:
  - reproducing full startup_common side effects can reintroduce arcade-only hardware behavior and memory pressure/coupling that the launcher bypass intentionally avoided.

## Uncertainties
- Exact first-value semantics for `A5+0x0100` under all launcher entry branches remain partially unproven without focused runtime trace of that flag.
- Current transition-cluster patch state (`0x03A294/0x03A2B2`) can mask true buffer-order behavior and should be considered during implementation planning.

## Conclusion
- Minimal correct launcher init is achievable without restoring full startup_common.
- The critical ordering rule is to keep `A5+0x0104` unasserted until selector seeding can occur naturally.
- Non-video baseline fields remain launcher-seedable; C-window/D-window/orientation hardware init remains excluded as intended.
