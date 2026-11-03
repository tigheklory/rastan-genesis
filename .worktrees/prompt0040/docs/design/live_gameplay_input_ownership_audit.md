# Live Gameplay Input Ownership Audit

**Date:** 2026-03-30
**Build reference:** Build 295

---

## SECTION 1 — CURRENT INPUT STATUS

**YES** — gameplay input mapping is fully active after launch.

`genesistan_refresh_arcade_inputs()` (`startup_bridge.c:169`) is called every V-Int inside `genesistan_frontend_live_vint_handoff()` (`main.c:1962`) before the arcade vblank handler executes. All four arcade input shadow registers are updated on every frame from the time "START RASTAN" is selected until the Genesis resets. The arcade code reads those shadows via opcode-rewritten port accesses. The system is operational through all arcade runtime phases: attract, title, coin-insert, gameplay, game-over.

---

## SECTION 2 — VERIFIED CURRENT PATH

### Genesis input source

| Source | File | Line | Notes |
|--------|------|------|-------|
| `JOY_readJoypad(JOY_1)` | `startup_bridge.c` | 171 | P1 raw Genesis pad state |
| `JOY_readJoypad(JOY_2)` | `startup_bridge.c` | 172 | P2 raw Genesis pad state |
| `build_player_input_byte()` | `startup_bridge.c` | 120 | Maps d-pad + B/C → active-low arcade byte |
| `build_aux_input_byte()` | `startup_bridge.c` | 135 | Maps B/C/A → bits 4/5/6 of aux port |
| `build_system_input_byte()` | `startup_bridge.c` | 150 | Maps A→coin, START→start1, service combo |
| `genesistan_refresh_arcade_inputs()` | `startup_bridge.c` | 169 | Calls all three builders, writes all four shadows |

### Post-launch V-Int dispatch chain

| Step | Function | File | Line | What it does |
|------|----------|------|------|--------------|
| 1 | `genesistan_frontend_live_vint_handoff()` | `main.c` | 1953 | V-Int callback; guards on `frontend_live_handoff_active` and `SCREEN_FRONTEND_LIVE` |
| 2 | `genesistan_refresh_arcade_inputs()` | `main.c` | 1962 | Reads joypad, writes shadow registers — runs **before** arcade tick |
| 3 | `genesistan_run_original_frontend_tick()` | `main.c` | 1963 | Jumps to arcade vblank at `0x03A008 + ARCADE_ROM_BASE` |
| 4 | Input polling subroutine at `0x3A0A8` | `build/maincpu.disasm.txt` | — | Reads from shadow registers via opcode-rewritten port reads |

### V-Int callback registration

| Event | Function | File | Line |
|-------|----------|------|------|
| START RASTAN selected | `request_start_rastan()` | `main.c` | 1826 |
| Callback set | `SYS_setVIntCallback(genesistan_frontend_live_vint_handoff)` | `main.c` | 1837 |
| Screen state set | `current_screen = SCREEN_FRONTEND_LIVE` | `main.c` | 1835 |
| Handoff flag set | `frontend_live_handoff_active = TRUE` | `main.c` | 1836 |

`SCREEN_FRONTEND_LIVE` is never changed during arcade runtime. It persists through all arcade sub-states (attract, gameplay, game-over) until `reset_launcher_runtime_state()` is explicitly called.

### Shadow registers (opcode-rewritten port reads)

| Arcade port | Shadow symbol | Genesis WRAM location | Updated | Arcade reads at |
|-------------|---------------|----------------------|---------|-----------------|
| `0x390001` | `genesistan_shadow_input_390001` | `.bss.patcher` | every V-Int | `0x03A4A2`, `0x03A778` |
| `0x390003` | `genesistan_shadow_input_390003` | `.bss.patcher` | every V-Int | `0x03A4A8`, `0x03A77E` |
| `0x390005` | `genesistan_shadow_input_390005` | `.bss.patcher` | every V-Int | `0x03A0A8`, `0x03A0B2`, `0x03A0C0`, `0x03ACB2`, `0x03AD1C` |
| `0x390007` | `genesistan_shadow_input_390007` | `.bss.patcher` | every V-Int | `0x03A3A6`, `0x03A490`, `0x03A7B8`, `0x03AB96`, `0x03AC04`, `0x03AC94`, `0x03ACFE` |

Opcode rewrite rules are defined in `specs/startup_title_remap.json` (entries for 0x390001/3/5/7). The patcher replaces arcade ROM reads from those addresses with reads from the Genesis WRAM shadow symbols at build time.

### Arcade input consumption timing

All arcade input reads from the disassembly are in code paths executed during the arcade vblank handler at `0x03A008`. The reads happen in the same V-Int that `genesistan_refresh_arcade_inputs()` already ran. The ordering guarantee is fixed by the sequential call order in `genesistan_frontend_live_vint_handoff()` (input refresh at line 1962, arcade tick at line 1963).

---

## SECTION 3 — OWNERSHIP BREAK

**None.** There is no ownership break.

The input path is continuous from startup through all arcade runtime phases:

- **Pre-launch:** `genesistan_reset_startup_shadows()` → `genesistan_refresh_arcade_inputs()` initializes shadows to current joypad state.
- **Post-launch, every V-Int:** `genesistan_frontend_live_vint_handoff()` → `genesistan_refresh_arcade_inputs()` → shadow registers populated → arcade vblank tick runs and reads the populated shadows.
- **Screen guard:** `SCREEN_FRONTEND_LIVE` is set at `main.c:1835` when the game starts and is not changed by any code path during arcade runtime. The guard at `main.c:1956` passes on every V-Int for the duration of gameplay.

---

## SECTION 4 — REQUIRED GENESIS→ARCADE MAPPING

### P1 player controls → `0x390001` (active-low)

| Genesis button | Arcade bit | Arcade meaning |
|---------------|-----------|----------------|
| D-pad UP | bit 0 (0x01) | Joystick up |
| D-pad DOWN | bit 1 (0x02) | Joystick down |
| D-pad LEFT | bit 2 (0x04) | Joystick left |
| D-pad RIGHT | bit 3 (0x08) | Joystick right |
| BUTTON_B | bit 4 (0x10) | Arcade button 1 (attack) |
| BUTTON_C | bit 5 (0x20) | Arcade button 2 (jump) |

`build_player_input_byte()` (`startup_bridge.c:120`). Default 0xFF (all released). Active-low.

### P2 player controls → `0x390003` (active-low)

Same bit layout as P1. Applied to P2 joypad state via same `build_player_input_byte()`.

### Auxiliary button mirror → `0x390005` (active-low)

| Genesis button | Arcade bit | Arcade use |
|---------------|-----------|------------|
| BUTTON_B | bit 4 (0x10) | Title/service code btst at `0x03A0B2` |
| BUTTON_C | bit 5 (0x20) | Title/service code btst at `0x03A0C0` |
| BUTTON_A | bit 6 (0x40) | Title/service code btst at `0x03A0A8` |

`build_aux_input_byte()` (`startup_bridge.c:135`). Used by title/service probe code; mirrors same buttons.

### System input → `0x390007` (active-low)

| Genesis input | Arcade bit | Arcade meaning |
|--------------|-----------|----------------|
| P1 BUTTON_A | bit 0 (0x01) | Coin 1 insert |
| P1 BUTTON_START | bit 3 (0x08) | Player 1 start |
| P2 BUTTON_START | bit 4 (0x10) | Player 2 start |
| P1 A+B+C combo | bit 2 (0x04) | Service/tilt trigger |

`build_system_input_byte()` (`startup_bridge.c:150`). The A+B+C combo clearing bit 2 is an intentional-combo guard to prevent accidental service entry during normal play. Arcade BTST #2 test at `0x03AB96` drives the TILT text dispatch; proven arcade-original by `docs/design/credit_tilt_provenance_report.md`.

### What is NOT mapped (and why)

| Genesis input | Status | Reason |
|---------------|--------|--------|
| BUTTON_A (gameplay) | Not a gameplay button | Rastan arcade is 2-button: attack + jump. Button A is reserved for coin on Genesis. No 3rd gameplay button exists in the arcade ROM. |
| BUTTON_X / BUTTON_Y / BUTTON_Z | Not present on 3-button pad | Out of scope for standard 3-button Genesis controller. |
| Service mode direct | Not mapped to single button | Intentionally requires A+B+C combo to prevent accidental activation. |

---

## SECTION 5 — REQUIRED IMPLEMENTATION OWNERSHIP

**Assembly-owned gameplay input handling required: NO**

The current C implementation in `startup_bridge.c` is correct, complete, and runs at the right time (every V-Int, before arcade tick). The path is:

- `JOY_readJoypad()` → SGDK function (already assembly-optimized internally)
- `build_player_input_byte()` / `build_aux_input_byte()` / `build_system_input_byte()` → thin C mappers writing to WRAM shadow bytes
- Shadow bytes consumed by arcade assembly via opcode-rewritten reads

**C retains full ownership** of the input mapping layer because it is a one-time-per-frame write to four WRAM bytes, invoked from a C V-Int callback that already owns the frame boundary. There is no hot inner loop in the input path. Converting to assembly would add complexity with zero benefit.

**C must NOT:**
- Add input polling in the main() loop that races with V-Int input refresh
- Read joypad state in any path other than `genesistan_refresh_arcade_inputs()` for arcade purposes (launcher UI reads are separate and correct)

---

## SECTION 6 — SINGLE NEXT IMPLEMENTATION PHASE

No input implementation phase is required. The system is complete and operational.

The next unblocked work item in the graphics pipeline is completing the PC080SN tilemap plane writes (Build 295 rollback, verified correct in AGENTS_LOG). Input will follow naturally as BG and FG planes become visible — coins can be inserted (BUTTON_A), player 1 start selected (BUTTON_START), and controls exercised (d-pad + B/C) once the visual output is correct enough to test gameplay.

If a future phase requires verifying input-in-gameplay, the existing path requires no code changes. Testing procedure is: build → emulator → START RASTAN → insert coin with A → start with START → verify d-pad and B/C control Rastan.

---

## SECTION 7 — DO NOT DO LIST

- Do not create an assembly-owned input handler — the C path is correct and sufficient.
- Do not add a second joypad read site; the single call in `genesistan_refresh_arcade_inputs()` is the canonical source.
- Do not move input refresh to the main() loop — it must run from V-Int to maintain correct ordering before the arcade tick.
- Do not change the active-low polarity of the shadow registers — arcade code expects 0=pressed.
- Do not add a "gameplay input" vs "menu input" split — the single `genesistan_refresh_arcade_inputs()` correctly serves all phases of arcade execution.
- Do not touch the opcode rewrite rules in `startup_title_remap.json` for the input ports — they are correct.
- Do not remap BUTTON_A to a gameplay action — it is the coin button and this is intentional (Rastan has no 3rd gameplay button in the arcade).
- Do not modify the service/tilt combo trigger — it is proven arcade-original behavior.
- Do not modify the scroll system, tilemap pipeline, or any unrelated system.
