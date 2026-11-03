# Summary
Implemented a narrow bring-up debug path in `apps/rastan-direct` that bypasses mailbox command handling and forces a single hardcoded YM2612 channel-1 tone attempt from the Z80 driver loop.

# Exact Files Modified
- `apps/rastan-direct/src/sound/z80_driver.s`
- `apps/rastan-direct/src/sound/sound_comm.s`
- `docs/design/Cody_rastan_direct_forced_z80_tone_debug.md`
- `AGENTS_LOG.md`

# Exact Symbols / Functions / Labels Added or Changed
- `z80_driver_start` (forced-tone loop bytes at offsets `0x0013..0x0049`; mailbox command decode removed)
- `z80_driver_start` bring-up marker writes:
  - `0x1FF2` run marker set to `0x5A`
  - `0x1FF3` heartbeat increment loop
- `z80_init_and_start` (added bring-up probe delay + bus re-acquire + marker/heartbeat read)
- `sound_comm.s` constants added:
  - `Z80_RUNMARK`
  - `Z80_HEARTBEAT`
  - `DIAG_LOG_PORT`
- `z80_init_and_start` labels added:
  - `.Lwait_after_release`
  - `.Ldiag_fail`
  - `.Ldiag_done`

# Permanent vs Temporary Classification
- PERMANENT:
  - none
- TEMPORARY:
  - none
- DIAGNOSTIC:
  - `apps/rastan-direct/src/sound/sound_comm.s` marker/heartbeat probe block in `z80_init_and_start`
  - `apps/rastan-direct/src/sound/sound_comm.s` `DIAG_LOG_PORT` write path (`0xC0DE`/`0xDEAD` codes)
  - `apps/rastan-direct/src/sound/z80_driver.s` run marker (`0x1FF2`) and heartbeat (`0x1FF3`)
- BRINGUP_ONLY:
  - `apps/rastan-direct/src/sound/z80_driver.s` forced hardcoded tone loop replacing mailbox decode path

# Scaffolding Inventory
1. BRINGUP_ONLY
- exact file: `apps/rastan-direct/src/sound/z80_driver.s`
- exact symbol/function/label: `z80_driver_start` forced loop (`0x0013..0x0049`)
- purpose: bypass command path and attempt a stable YM2612 tone on channel 1
- why it exists: isolate basic Z80->YM audibility before implementing real command/audio logic
- how it is triggered: always active after Z80 reset release
- future condition for removal: successful proof of audible YM output with normal command path restored
- exact removal method: restore original mailbox command decode byte sequence in `0x0013..0x0049`

2. DIAGNOSTIC
- exact file: `apps/rastan-direct/src/sound/z80_driver.s`
- exact symbol/function/label: run marker/heartbeat writes (`0x1FF2`, `0x1FF3`)
- purpose: provide runtime observability of loop entry/progression
- why it exists: confirm whether driver reaches forced-tone loop
- how it is triggered: automatically during forced loop
- future condition for removal: command-driven playback path is validated
- exact removal method: delete marker/heartbeat instructions and revert to normal command loop

3. DIAGNOSTIC
- exact file: `apps/rastan-direct/src/sound/sound_comm.s`
- exact symbol/function/label: `z80_init_and_start` probe block (`.Lwait_after_release` through `.Ldiag_done`)
- purpose: sample Z80 marker/heartbeat after reset and emit a diagnostic code
- why it exists: narrow blocker identification in silent bring-up state
- how it is triggered: runs once in `z80_init_and_start`
- future condition for removal: Z80/YM path is audibly verified and no probe is needed
- exact removal method: remove probe block and helper constants; keep minimal init/start path

# Removal / Revert Plan
1. Revert `z80_driver_start` bytes at `0x0013..0x0049` back to mailbox command decode implementation.
2. Remove run marker and heartbeat writes (`0x1FF2`, `0x1FF3`) in `z80_driver.s`.
3. Remove `Z80_RUNMARK`, `Z80_HEARTBEAT`, `DIAG_LOG_PORT` constants from `sound_comm.s`.
4. Remove bring-up probe delay/read/log block in `z80_init_and_start`.
5. Rebuild and re-validate command-driven audio path.

# Build Artifact Path
- `apps/rastan-direct/dist/rastan_direct_sound_test.bin`

# Verification Status
- ROM build succeeded: YES
- Z80 code definitely running: YES
  - Evidence: MAME runtime repeatedly logs active Z80 fetches in unmapped `0x400x` region (`:genesis_snd_z80`), proving Z80 is executing.
- YM2612 init writes executed: NO
  - Evidence: runtime indicates Z80 execution divergence into unmapped `0x400x`, so execution of intended YM init routine is not confirmed.
- Hardcoded tone attempted: YES
  - Evidence: forced-tone path is now the only active Z80 loop implementation in source.
- Audible output produced: NO
  - Evidence: no audible confirmation in current environment and no confirmed YM init execution path.

# Risks / Known Limitations
- Z80 execution currently diverges into unmapped `0x400x` region in MAME logs, preventing confirmation that intended YM write routine executes.
- Host audio backend limitations prevent direct audible confirmation inside this environment.
- Diagnostic probe codes are scaffolding and must be removed after bring-up is complete.
