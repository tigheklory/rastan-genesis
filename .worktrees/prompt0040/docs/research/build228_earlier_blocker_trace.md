1) Purpose
- Identify the earlier runtime blocker seen in Build 228 (`PC` sampling around `0x21159C..0x2115A8`) and trace the real first cause without changing code/specs.

2) Inputs Used
- `AGENTS.md`
- `AGENTS_LOG.md` (latest Build 228 section)
- `README.md`
- `docs/research/build228_direct_title_prep_replacement_no_shims.md`
- `apps/rastan/src/main.c`
- `apps/rastan/out/rom.out` (symbol + disassembly via `m68k-elf-nm` / `m68k-elf-objdump`)
- Runtime probes on `dist/Rastan_228.bin` (MAME Lua, mode-1 build)

3) Function / Path At 0x21159C..0x2115A8
- `0x21159C..0x2115A8` is inside `VDP_waitVBlank` (`symbol: 0x211550`), which is SGDK runtime code.
- Ownership classification: SGDK/system runtime path (not relocated arcade gameplay code, not custom exception handler body).
- Disassembly at the sampled loop:
  - `0x21159A: movea.l #0x00C00004, A0`
  - `0x2115A0: move.w (A0), D0`
  - `0x2115A2: btst #3, D0`
  - `0x2115A6: bne 0x21159A`
  - `0x2115A8: move.w (A0), D0`
- This is VDP status polling inside SGDK VBlank wait logic.

4) First Fault Cause
- No first fault was observed in Build 228 bounded probes.
- Direct evidence:
  - `rastan_qr_exc_type` (`0xE0FF6B38`) stayed `0x0000` across sampled frames.
  - `PC` samples oscillated in `0x21159C..0x2115A8` while exception type stayed zero.
  - No entry into `_Rastan_EX_*` vectors (`0x2028E2+`) was observed.
- First blocking cause (proven) is launcher idle/handoff not triggered, not exception re-entry:
  - `current_screen` (`0xE0FF6DCC`) remained `0x0000` during probes.
  - `JOY` state sample remained `0x0000` (no START/coin input edge).
  - In `main.c`, `request_start_rastan()` is only called on input paths; otherwise loop tail calls `SYS_doVBlankProcess()` repeatedly.
  - `SYS_doVBlankProcessEx` (`0x2116F4`) calls `VDP_waitVBlank`, producing the observed PC band.

5) Title Execution Relation
- This blocker occurs before title-state entry.
- Build 228 probes did not reach `SCREEN_FRONTEND_LIVE` execution (`genesistan_run_original_frontend_tick()` path) and did not enter title-state handlers.
- Therefore the sampled `0x21159C..0x2115A8` behavior is pre-title launcher-loop behavior in this capture context.

6) Final-State Judgment
- Primary classification: `OTHER`.
- Exact judgment: this is a pre-handoff launcher idle condition (no triggering input/event), not an exception-loop root fault and not a title-path crash signature.

7) Minimal Next Fix Target
=== BUILD228_EARLIER_BLOCKER_MINIMAL_FIX_TARGET ===
- fix_area: runtime validation/handoff trigger path (launcher input-to-`request_start_rastan()` transition), not title-prep internals.
- exact_first_fault_path: no fault path proven; observed path is `main` loop -> `SYS_doVBlankProcessEx (0x2116F4)` -> `VDP_waitVBlank (0x211550)` with `current_screen=0` and `ex_type=0`.
- why_this_is_the_real_blocker: without a verified handoff trigger, runs stay in launcher idle polling and never execute title/frontend logic, making title-path conclusions invalid.
- what_must_NOT_be_done: do not add shims, do not NOP/bypass, do not force title state, do not reopen title-prep replacement in this step.

8) Uncertainties
- Bounded automated probes did not include user input injection; this pass proves idle pre-handoff behavior for the tested run window, not all possible interactive runs.
- Exact single callsite inside `main.isra.0` that produced each sampled VBlank wait iteration is not uniquely identified from frame-level sampling alone (multiple loop branches call `SYS_doVBlankProcessEx`).

9) Conclusion
- The `0x21159C..0x2115A8` region is SGDK `VDP_waitVBlank` polling, and Build 228 probes show no exception (`ex_type=0`), so the exposed blocker is pre-handoff launcher idle behavior rather than a new crash-path fault.
