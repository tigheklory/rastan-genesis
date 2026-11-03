# Arcade Init vs Launcher Fake Init Audit

**Date:** 2026-03-30
**Build reference:** Build 297

---

## 1. Executive Summary

The Genesis launcher fake init (`genesistan_init_workram_direct()`) is **substantially correct** in reproducing the post-startup workram state for DIP settings, coinage tables, config data, and delay timers. The critical intentional deviation is `A5@(0) = 1` (workram word 0 = 1), which sets the main state machine directly to **state 1** (player-select screen). In the arcade, state 1 is only reached after at least one coin is inserted. By starting in state 1, the Genesis build bypasses the attract loop and coin-insert requirement.

**The "credited/start-ready" appearance is caused by initialization, not live input.** `A5@(0) = 1` puts the arcade code directly into the player-select state. The credit counter `A5@(18)` is correctly initialized to 0, so no credits are actually present, but the state machine is already past the attract/coin-insert gate.

**All tilemap bugs identified today are genuine runtime path bugs.** None are initialization artifacts. Incorrect init state changes which screen the arcade renders, but the tilemap pipeline bugs are present regardless of which state is active.

---

## 2. Arcade Startup / Init Flow

### Entry points

| Address | Role |
|---------|------|
| `0x3a000` | ROM vector table entry — branches to `0x3ae86` (startup_common). Never called by our launcher. |
| `0x3ae86` | `startup_common` — hardware init, work RAM clear, DIP read, DIP table lookup, config copy. |
| `0x3a008` | Vblank handler entry — this is what our launcher's V-Int callback dispatches to via `genesistan_run_original_frontend_tick()`. |

### `startup_common` sequence (0x3ae86)

| Step | Address | What it does |
|------|---------|--------------|
| 1 | 0x3ae86–0x3aec4 | Clears hardware registers: `C50000=0`, `D01BFE=0`, `350008=0`, `380000=0`. Sets sound chip select/control bytes. Performs 8192-iteration Z80/sound RAM probe loop. |
| 2 | 0x3aeea–0x3af02 | Zeros work RAM: `0x10c000` `movew #0, %a0@` then copies that zero forward 8192 words — clearing the full 16KB work RAM region. |
| 3 | 0x3af04 | `lea 0x10c000, %a5` — establishes work RAM base pointer. |
| 4 | 0x3af0a–0x3af10 | `movew %d0, 0x3c0000` — VDP display control write. |
| 5 | 0x3af10–0x3af48 | Fills BG C-window `0xC00000` (4096 words with 0x20), FG C-window `0xC08000` (4096 words with 0x20). |
| 6 | 0x3af52–0x3af70 | Fills `0xC04000` and `0xC0C000` ranges with 0. |
| 7 | 0x3af7a–0x3af8e | **Reads DIP switches from hardware**: `moveb 0x390009,%d0` → `notb %d0` → `A5@(24)` (DIP1). `moveb 0x39000b,%d0` → `notb %d0` → `A5@(28)` (DIP2). |
| 8 | 0x3af92–0x3afb6 | **Difficulty table lookup**: DIP2 bits 3:2 → right-shift → index into table at `0x3b010`. Values: `{0x1000, 0x1500, 0x2000, 0x2500}`. Result → `A5@(56)`. |
| 9 | 0x3afb6–0x3afce | **Bonus life table lookup**: DIP2 bits 5:4 → right-shift 3 → index into table at `0x3b018`. Values: `{0x03, 0x04, 0x05, 0x06}`. Result → `A5@(54)`. |
| 10 | 0x3afbe–0x3afce | Cabinet type `→ A5@(48)` (DIP1 bit 0). Monitor flip `→ A5@(50)` (DIP1 bit 1). |
| 11 | 0x3afda–0x3afea | Mode from DIP2 bits 1:0 (with 0→1, 1→0 swap) → `A5@(46)`. |
| 12 | 0x3afee–0x3b00a | Competition/alt flags from ROM address `0x5ff9e` → `A5@(64)`, `A5@(68)`. |
| 13 | 0x3b020 | `movew #1, A5@(38)` — init flag set. |
| 14 | 0x3b026–0x3b048 | Coinage tables from DIP1 and DIP2 → `A5@(8..16)` via function `0x5ffa2`/`0x5ffb2`. |
| 15 | 0x3b04a | Call `0x3b0c2` — **copies 39 bytes from ROM `0x3b0d4` to `A5@(320)` (= work RAM + 0x140)**. |
| 16 | 0x3b064 | `movew #0xAA, A5@(74)` — sprite init marker. |
| 17 | 0x3b072–0x3b07c | Calls `0x3add8`, `0x3ae28` (display register writes). Clears interrupt mask, enables display. |
| 18 | 0x3b07e | Enters main vblank loop — **A5@(0) remains 0** at this point (zeroed in step 2, never written by startup_common itself). |

**Key result**: After startup_common completes, **A5@(0) = 0** (attract state). The arcade enters the attract loop. Credits `A5@(18) = 0`.

### State machine (A5@(0) field)

| Value | Meaning |
|-------|---------|
| 0 | Attract / insert-coin loop. State 0 handler at `0x3a9FE`. |
| 1 | Player select / start-ready. State 1 handler at `0x3a8AE`. Only set after coins are inserted. |
| 2 | Gameplay active. Set at `0x3a9de` when START is pressed (credits ≠ 0). |
| 3 | Game over / continue. State 3 handler at `0x3aB74`. |

### Credit counter (A5@(18) = workram word 9, byte offset 0x12)

- Starts at 0 after work RAM clear.
- Incremented via the coin insert path at `0x3ace6`–`0x3acf0` using the coinage table at `A5@(6)`.
- Maximum credit ceiling check at `0x3ac8a`: `cmpiw #153` (= 0x99 BCD = max 99 credits).
- Ceiling set at 9 active credits by test at `0x3a0d0`: `cmpiw #9, A5@(18)`.
- Decremented by 1 (BCD subtract) when START1/START2 is pressed (0x3a932–0x3a93e, 0x3a954–0x3a95c).

### State 0 → State 1 transition (disasm 0x3a450–0x3a460)

```
3a450: clrw %a5@(0)           ; reset state to 0
3a454: tstw %a5@(18)          ; test credit counter
3a458: beqs 0x3a460           ; if 0 credits → keep state=0 (attract)
3a45a: movew #1,%a5@(0)       ; if credits > 0 → state=1 (player select)
3a460: ...
```

**State 1 is only entered when A5@(18) > 0.** This is the critical gate our launcher bypasses.

### State 1 → State 2 transition (disasm 0x3a91a–0x3a9de)

When START1/START2 is pressed in state 1:
- `sbcd` decrements credit count
- `A5@(52)` (1P flag) = 1
- `movew #2, A5@(0)` → state 2 (gameplay)

---

## 3. Launcher Fake Init Flow

### Call chain

```
request_start_rastan()          [main.c:1827]
  → scrub_launcher_runtime_buffers()    [main.c:1858] — frees graphics test buffer
  → genesistan_reclaim_launcher_wram()  [startup_bridge.c:377] — clears tile cache etc
  → genesistan_init_workram_direct(dip1, dip2)  [startup_bridge.c:225]
  → restore_launcher_vdp_state()
  → sets SCREEN_FRONTEND_LIVE, frontend_live_handoff_active = TRUE
  → SYS_setVIntCallback(genesistan_frontend_live_vint_handoff)
```

### `genesistan_reset_startup_shadows()` — called before launcher starts

Called during Genesis boot (before any user interaction). Zeros all shadow arrays and sets shadow DIPs.

| What | Result |
|------|--------|
| `genesistan_arcade_workram_words` | zeroed (16KB) |
| `genesistan_shadow_d00000_words` | zeroed |
| `genesistan_shadow_input_390001/3/5/7` | all 0xFF (all-released, active-low) |
| `genesistan_shadow_dip1` | `GENESISTAN_DIP1_FACTORY` |
| `genesistan_shadow_dip2` | `GENESISTAN_DIP2_FACTORY` |
| `genesistan_shadow_service_word` | `GENESISTAN_SERVICE_FACTORY` |
| hook cursors `row_a/b` | set to 8 |
| `genesistan_refresh_arcade_inputs()` called | shadows populated from current joypad |

### `genesistan_init_workram_direct(dip1, dip2)` — called at game launch

| Arcade field | Byte offset | What launcher sets | Arcade truth |
|---|---|---|---|
| `workram[0]` | A5@(0) | **1** (state = 1) | 0 after startup_common |
| `workram[1]` | A5@(2) | 0 (sub-state 0) | 0 ✓ |
| `workram[2]` | A5@(4) | 0 (inner step 0) | 0 ✓ |
| `workram[4]` | A5@(8) | 1 (coin1 = 1) | derived from DIP ✓ |
| `workram[5]` | A5@(10) | 1 (coin2 = 1) | derived from DIP ✓ |
| `workram[9]` | A5@(18) | 0 (credits = 0) | 0 ✓ |
| `workram[10]` | A5@(20) | 0x0060 (display control) | set to 0x60 via 0x3b072 ✓ |
| `workram[12]` | A5@(24) | `~dip1` (cabinet type) | `~DIP1` from hardware ✓ |
| `workram[14]` | A5@(28) | `~dip2` (difficulty base) | `~DIP2` from hardware ✓ |
| `workram[19]` | A5@(38) | 1 (init flag) | 1 via 0x3b020 ✓ |
| `workram[22]` | A5@(44) | 160 (initial delay) | set to 0xA0 via 0x3a43e ✓ |
| `workram[23]` | A5@(46) | mode from DIP2 | mode from DIP2 via 0x3afda ✓ |
| `workram[24]` | A5@(48) | cabinet type DIP1&1 | DIP1&1 ✓ |
| `workram[25]` | A5@(50) | monitor flip DIP1&2 | DIP1&2 ✓ |
| `workram[27]` | A5@(54) | bonus life table lookup | table from 0x3b018 ✓ |
| `workram[28]` | A5@(56) | difficulty table lookup | table from 0x3b010 ✓ |
| `workram[32]` | A5@(64) | 0 (competition/alt) | from 0x5ff9e ROM (**ASSUMED 0** — unverified vs ROM byte) |
| `workram[37]` | A5@(74) | 0x00AA (sprite marker) | 0xAA via 0x3b064 ✓ |
| `workram[64..127]` | A5@(128..255) | transition buffer seeded per arcade helper (0x3a9e6 pattern) | seeded by `3a99a/3a9a6` ✓ |
| `workram[128]` | A5@(256) | 1 (title init flag) | set to 1 via runtime paths ✓ |
| A5@(320..358) | workram[160..179] | 39 bytes from ROM `0x3b0d4` | same bytes via 0x3b0c2 ✓ |

### Fields NOT set by launcher (correctly left at 0)

| Field | Offset | Notes |
|-------|--------|-------|
| `A5@(18)` | 0x12 | Credits = 0 ✓ (correct, no coins inserted) |
| `A5@(34)` | 0x22 | Coin2 tracking = 0 ✓ |
| `A5@(36)` | 0x24 | Coin2 tracking = 0 ✓ |
| `A5@(40)` | 0x28 | P1 active flag = 0 ✓ |
| `A5@(42)` | 0x2A | P2 active flag = 0 ✓ |
| `A5@(52)` | 0x34 | P1 start = 0 ✓ |

### Skipped arcade init steps

| Skipped | Impact |
|---------|--------|
| Hardware DIP reads from `0x390009/0x39000b` | Replaced by simulator DIP shadows. Functionally equivalent for all known DIP settings. |
| Hardware C-window fill (`0xC00000/0xC08000`) | Irrelevant — Genesis VDP is not that hardware. |
| VDP display register writes (`0x380000`, `0x3c0000`, etc.) | Irrelevant — Genesis has its own VDP. |
| Z80/sound RAM probe loop | Z80 is held in reset via `Z80_startReset()`. |
| Startup_common sequence overall | Entire startup_common replaced by fake init. This is intentional — arcade hardware init is meaningless on Genesis. |

---

## 4. Credit / Start-Ready State Audit

### Observation

The Genesis build appears to begin in a "PUSH 1 OR 2 PLAYER BUTTON" state without requiring coin insertion.

### Root cause

**`A5@(0) = 1` set by `genesistan_init_workram_direct()` at `startup_bridge.c:266`.**

In the arcade state machine, A5@(0) = 1 is the "player select" state. It is entered ONLY through:
1. The credit-conditional path at `0x3a450–0x3a460` (disasm line 73261): `clrw A5@(0); tstw A5@(18); beqs keep_zero; movew #1,A5@(0)` — only sets state 1 if credits > 0.
2. The game-over recovery path at `0x3ac7a` (disasm line 73834): `movew #1,A5@(0)` after a game ends.

Neither path runs before the first frame of the Genesis build. `genesistan_init_workram_direct()` sets `A5@(0) = 1` as the starting state, bypassing the attract sequence entirely. The state machine begins in state 1, which renders the player-select screen.

### Is this from live coin input?

**NO.** `A5@(18)` (credit counter) is 0 at init. No coin input handler has run. The start-ready appearance is 100% from initialization.

### Is this from wrong init?

**YES — intentionally wrong.** The launcher comment at `startup_bridge.c:265` explicitly documents "Main state machine: state=1, sub=0, step=0". This is a deliberate design choice to skip attract mode for testing. It is not an accidental misconfiguration.

### Consequence

- The game shows the "player-select" screen immediately.
- With `A5@(18) = 0` (no credits), pressing START triggers the BCD subtract path at `0x3a932–0x3a93e`, which decrements 0 by 1 using BCD arithmetic. Since the BCD result of `0 - 1` with carry=0 wraps to `0x99` (BCD), pressing START without inserting a coin would give the game 99 credits.
- This is a known consequence of the attract-skip design and does not affect runtime visual testing.

---

## 5. DIP / Table-Driven Init Audit

### What DIP-driven init controls

| Field | Source | Our init |
|-------|--------|----------|
| Difficulty table (4 entries: 0x1000/1500/2000/2500) | DIP2 bits 3:2 | ✓ Same table, same bit extraction |
| Bonus life table (4 entries: 0x03/04/05/06) | DIP2 bits 5:4 | ✓ Same table, same bit extraction |
| Cabinet type (upright/cocktail) | DIP1 bit 0 → A5@(48) | ✓ Same |
| Monitor flip | DIP1 bit 1 → A5@(50) | ✓ Same |
| Mode | DIP2 bits 1:0 with swap → A5@(46) | ✓ Same swap logic |
| Coinage tables | DIP1 bits 7:4 and DIP2 bits 7:6 → A5@(8..16) | ✓ Set to factory default 1C:1C |

### Competition/alt flags (potential gap)

`A5@(64)` and `A5@(68)` in the arcade are derived from `0x5ff9e` (ROM byte read with NOT + AND). Our launcher sets these to 0 (`workram[32] = 0`, `workram[34] = 0`). Whether `ROM[0x5ff9e]` is 0 on the standard Rastan ROM is **not verified** from this disasm read — the value is treated as 0 here.

### Does DIP table init affect credit/start state?

**NO.** None of the DIP-driven table entries affect `A5@(18)` (credits), `A5@(0)` (state), or any flag that gates attract vs player-select mode. DIP tables control difficulty, bonus life, cabinet type, and coinage ratios only.

### Does missing DIP hardware read cause issues?

**NO.** The simulator uses `rastan_virtual_dip1/dip2` which are exposed in the launcher UI. These values flow into `genesistan_init_workram_direct()` which applies the same bit-extraction formulas as the arcade. Functionally equivalent.

---

## 6. Comparison Table — Arcade vs Launcher Values

| Field | Arcade post-startup | Launcher init | Match? | Notes |
|-------|--------------------|--------------|----|------|
| `A5@(0)` (main state) | 0 (attract) | **1** (player select) | **NO** | INTENTIONAL — attract skip |
| `A5@(2)` (sub-state) | 0 | 0 | ✓ | |
| `A5@(4)` (inner step) | 0 | 0 | ✓ | |
| `A5@(18)` (credits) | 0 | 0 | ✓ | |
| `A5@(24)` (DIP1 notted) | ~hardware DIP1 | ~`rastan_virtual_dip1` | ✓ | |
| `A5@(28)` (DIP2 notted) | ~hardware DIP2 | ~`rastan_virtual_dip2` | ✓ | |
| `A5@(38)` (init flag) | 1 | 1 | ✓ | |
| `A5@(44)` (delay timer) | varies (post-attract) | 160 | ✓ | |
| `A5@(46)` (mode) | DIP2 bits 1:0 | same formula | ✓ | |
| `A5@(48)` (cabinet) | DIP1&1 | same | ✓ | |
| `A5@(50)` (flip) | DIP1&2 | same | ✓ | |
| `A5@(54)` (bonus life) | from 0x3b018 table | same table | ✓ | |
| `A5@(56)` (difficulty) | from 0x3b010 table | same table | ✓ | |
| `A5@(64)` (competition) | ~ROM[0x5ff9e] & 0x40 | 0 | UNVERIFIED | Likely 0 on standard ROM |
| `A5@(74)` (sprite marker) | 0xAA | 0xAA | ✓ | |
| `A5@(128..191)` (transition buffer) | seeded from 0x3a9a6 | same seed formula | ✓ | |
| `A5@(320..358)` (config table) | 39 bytes from ROM `0x3b0d4` | same bytes | ✓ | |
| DIP hardware reads | `0x390009/0x39000b` | `rastan_virtual_dip1/2` | functional ✓ | |
| Input shadows | all 0xFF (released) | 0xFF then refreshed | ✓ | `genesistan_refresh_arcade_inputs()` called |

---

## 7. Retrospective Audit of Today's Fixes

### +0x14 tile read offset and rollback (Build 293/294/295)

**Classification: TRUE RUNTIME BUG.**

The tile code read formula (`table_base + strip_offset + row_stride`) is computed entirely in assembly registers based on LUT data and loop counters. No init state affects which memory offset the assembly reads. Even with A5@(0) = 0 (attract mode), the same assembly loops would run with the same wrong (+0x14) or correct (no offset) address calculation.

**Initialization influence: NONE.**

### BG/FG C-window base split (Build 296)

**Classification: TRUE RUNTIME BUG.**

`PC080SN_CWINDOW_BASE = 0xC08000` caused `pc080sn_dest_ptr_to_row_col()` to fail for BG dest_ptrs regardless of game state. The BG dest_ptr value `0xC00400` (set by arcade disasm `0x55E54`) is a fixed initialization in the arcade's own runtime path — it would be `0xC00400` in both state 0 (attract) and state 1 (player select).

**Initialization influence: NONE.**

### C-window byte-range fix (Build 296→297)

**Classification: TRUE RUNTIME BUG.**

`PC080SN_CWINDOW_BYTES = 0x8000` caused dest_ptr to exit valid range after 2 calls. This is a constant value in the C validity check, independent of what game state is running.

**Initialization influence: NONE.**

### BG row/col inversion finding (Build 297)

**Classification: TRUE RUNTIME BUG.**

`pc080sn_dest_ptr_to_row_col()` computes `out_row = cell >> 6` and `out_col = cell & 0x3F`. For a column-major C-window layout, these are inverted. This decode error produces `dest_col = 0` always, writing all BG tiles to VDP column 0. This applies to every BG dest_ptr value regardless of game state.

**Initialization influence: NONE.** However, the specific VDP column coverage pattern (column 4 vs column 5 vs...) changes across frames due to the arcade's column-advance routine `0x560DA`. The pattern of wrong-column writes was present regardless of whether the game was in attract state or player-select state.

### Input ownership audit (Build 295)

**Classification: CONFIRMED CORRECT — unrelated to initialization.**

`genesistan_refresh_arcade_inputs()` runs every V-Int and overwrites all four shadow registers with fresh joypad reads. Init-time shadow values (`0xFF`) are immediately replaced by the first V-Int call. The active-low polarity and button mapping are correct. Init state does not affect this.

**Initialization influence: NONE.**

---

## 8. Minimum Authoritative Startup State Set

This is the minimum set of fields that must match arcade values before runtime behavior can be trusted for gameplay testing. Each entry specifies the correct arcade value and our current status.

| Field | Byte offset | Correct arcade value | Launcher value | Status |
|-------|------------|---------------------|---------------|--------|
| `A5@(0)` main state | 0x00 | 0 (attract) | 1 (player select) | **INTENTIONAL DEVIATION** — attract skip by design |
| `A5@(2)` sub-state | 0x02 | 0 | 0 | ✓ |
| `A5@(4)` inner step | 0x04 | 0 | 0 | ✓ |
| `A5@(18)` credits | 0x12 | 0 | 0 | ✓ |
| `A5@(24)` DIP1 (notted) | 0x18 | `~DIP1_hardware` | `~rastan_virtual_dip1` | ✓ functional |
| `A5@(28)` DIP2 (notted) | 0x1C | `~DIP2_hardware` | `~rastan_virtual_dip2` | ✓ functional |
| `A5@(38)` init flag | 0x26 | 1 | 1 | ✓ |
| `A5@(46)` mode | 0x2E | DIP2[1:0] (swapped) | same | ✓ |
| `A5@(48)` cabinet | 0x30 | DIP1[0] | same | ✓ |
| `A5@(54)` bonus life | 0x36 | table[DIP2[5:4]] | same | ✓ |
| `A5@(56)` difficulty | 0x38 | table[DIP2[3:2]] | same | ✓ |
| `A5@(64)` competition | 0x40 | ~ROM[0x5ff9e]&0x40 | 0 | UNVERIFIED |
| `A5@(74)` sprite marker | 0x4A | 0xAA | 0xAA | ✓ |
| `A5@(320..358)` config | 0x140 | ROM `0x3b0d4` bytes | same | ✓ |
| Input shadows | `.bss.patcher` | all 0xFF (released) | 0xFF then live | ✓ |
| DIP shadows | `.data.patcher` | factory values | factory values | ✓ |

**Only one field is a known-wrong init**: `A5@(0) = 1` vs correct `0`. This is intentional. All other fields are correctly initialized.

---

## 9. Confirmed Root Causes

### Root Cause 1 — Attract sequence bypassed (INTENTIONAL)

**Source:** `startup_bridge.c:266`: `genesistan_arcade_workram_words[0] = 1`.

**Effect:** Game starts in state 1 (player select) directly. Arcade attract loop (state 0) never runs. Coin-insert requirement bypassed. Game appears "start-ready" without coins.

**Classification: INTENTIONAL DESIGN CHOICE**, not a bug. The launcher is designed to skip attract for direct gameplay testing.

**Live input cause:** NO. Purely initialization.

### Root Cause 2 — A5@(18) = 0 with state = 1 causes BCD wrap on start press (SIDE EFFECT)

**Source:** Same init. Credits = 0, state = 1. BCD subtract at `0x3a932`: `sbcd #1` from 0 wraps to 99.

**Effect:** Pressing START without inserting a coin (BUTTON_START mapped to arcade start1) gives 99 credits and begins gameplay. This is a consequence of the attract-skip design choice.

**Classification: KNOWN SIDE EFFECT** of attract bypass. Not an independent bug.

---

## 10. Rejected Hypotheses

| Hypothesis | Why Rejected |
|------------|--------------|
| Credited state from live coin input (BUTTON_A) | REJECTED: A5@(18) = 0 in init. V-Int input refresh hasn't run at init time. The credited appearance is purely from A5@(0) = 1 placing the game in state 1. |
| DIP table init missing or wrong | REJECTED: Same tables, same bit extraction, verified against disasm `0x3b010/0x3b018`. |
| Attract bypass distorted tilemap bug observations | REJECTED: Tilemap pipeline bugs (tile offset, cwindow base, byte range, row/col inversion) are constant-driven code errors independent of what arcade state is active. |
| Config table copy missing | REJECTED: Launcher explicitly copies 39 bytes from ROM `0x3b0d4` to A5@(320) at `startup_bridge.c:363–373`. |
| Input shadow polarity wrong in init | REJECTED: All input shadows initialized to 0xFF (all released, active-low). Immediately overwritten by `genesistan_refresh_arcade_inputs()` on the first V-Int. |

---

## 11. Remaining Unknowns

### UNKNOWN A — ROM byte at `0x5ff9e` (competition/alt flag source)

**Status:** UNVERIFIED.

The arcade at `0x3afee` reads `movew 0x5ff9e,%d0`, applies NOT and AND #0x40 → A5@(64), AND #0x80 → A5@(68). These are competition/tournament flags. The launcher sets both to 0. If `ROM[0x5ff9e]` is not 0, these fields would differ. In practice, the standard Rastan ROM has no competition mode; these fields are expected to be 0. Not verified from disasm text.

### UNKNOWN B — A5@(0) = 1 effect on specific tilemap content

**Status:** NOT A BUG, just context.

With A5@(0) = 1, the arcade renders the player-select screen (state 1 sub-state 0), which draws specific tilemap content and text. With A5@(0) = 0, the attract demo renders different content. The tilemap bugs (row/col inversion, cwindow byte range) affect both states equally. Once the tilemap bugs are fixed, switching A5@(0) to 0 for attract mode testing would be straightforward if desired.

### UNKNOWN C — Transition buffer seed correctness

**Status:** STRUCTURAL ASSESSMENT — likely correct.

The launcher seeds `A5@(128..191)` from the arcade transition-buffer helper pattern (`0x3a9e6`). The exact runtime state of this buffer depends on how many attract cycles have elapsed on a real arcade board. The seed in the launcher matches the first initialization pass. Any divergence from a mid-attract-cycle arcade state does not affect the tilemap translation pipeline.
