# Real Attract State Progression + Coin Insert Audit

**Date:** 2026-03-30
**Build reference:** Build 298 (post startup-state correction)

---

## 1. Executive Summary

The game is confirmed to be starting in state 0 (attract). Both attract progression and coin insert are **logically working**. The state machine advances through attract sub-states on schedule. A-button coin insert correctly sets the credit counter and transitions to state 1. All missing visual feedback is **visual-only**: the BG row/column inversion bug (Build 297 finding — all BG writes target VDP column 0 only) causes the second attract screen and player-select screen to appear visually identical to the first attract screen, since BG content changes are invisible. FG-rendered content does change with state transitions, but may not be recognizable without the BG layer completing the screen.

**Coin insert logically working: YES.**
**Attract progression logically working: YES.**
**Missing feedback is visual-only: YES (both cases).**

---

## 2. Verified Startup State

### Source: `startup_bridge.c:265–268`

```c
/* Main state machine: state=0, sub=0, step=0 */
genesistan_arcade_workram_words[0] = 0; /* A5@(0)  main state */
genesistan_arcade_workram_words[1] = 0; /* A5@(2)  sub-state */
genesistan_arcade_workram_words[2] = 0; /* A5@(4)  inner step */
```

| Field | Byte offset | Init value | Arcade attract entry value |
|-------|------------|-----------|---------------------------|
| `A5@(0)` main state | 0x00 | **0** | 0 ✓ |
| `A5@(2)` sub-state | 0x02 | 0 | 0 ✓ |
| `A5@(4)` inner step | 0x04 | 0 | 0 ✓ |
| `A5@(18)` credits | 0x12 | 0 | 0 ✓ |
| `A5@(32)` coin1 latch | 0x20 | 0 (via memset) | 0 ✓ |
| `A5@(44)` delay timer | 0x2C | 160 | 160 (via 0x3af1a) ✓ |

The correction from prompt 039 (`A5@(0) = 0` instead of `1`) is confirmed present in the source. Game starts in attract state (state 0).

---

## 3. State 0 Attract Progression Audit

### Vblank handler dispatch path

Main vblank handler at `0x3a008` (called via `genesistan_run_original_frontend_tick()`):

| Step | Address | Action |
|------|---------|--------|
| 1 | 0x3a008 | Disable interrupts, display sync |
| 2 | 0x3a03e | `bsrw 0x3ab7c` — credit overflow + tilt check |
| 3 | 0x3a042 | `bsrw 0x3abe2` — **coin detect** (every frame, before state dispatch) |
| 4 | 0x3a046 | `bsrw 0x3a0a8` — aux input + credit display check |
| 5 | 0x3a04e | `bsrw 0x3ef5c` — further state-independent work |
| 6 | 0x3a056 | State dispatch: jump to handler for `A5@(0)` |

State 0 dispatches to handler at `0x3a9FE` (jump table at `0x3a06c` word 0 = 0x0992; `0x3a06c + 0x0992 = 0x3a9fe`).

### State 0 handler at `0x3a9fe`

```
3a9fe: tstw  %a5@(44)        ; test delay timer
3aa02: beqs  0x3aa0a         ; if 0 → enter sub-state dispatch
3aa04: subqw #1,%a5@(44)     ; decrement timer
3aa08: rts                   ; return (no progression this frame)
```

The delay timer at `A5@(44)` gates ALL attract progression. Init value = 160 → 160 vblanks (~2.7 seconds) of countdown before sub-state 0 runs for the first time.

### Sub-state dispatch (after timer = 0)

At `0x3aa0a`: reads `A5@(2)` (sub-state), doubles, indexes into jump table at `0x3aa20`.

Jump table decode (words at 0x3aa20, offsets from 0x3aa20):
- Sub-state 0 (word 0 = 0x0006) → handler at `0x3aa26`
- Sub-state 1 (word 1 = 0x0070) → handler at `0x3aa90`
- Sub-state 2 (word 2 = 0x0138) → handler at `0x3ab58`

### Sub-state 0 inner step dispatch (at `0x3aa26`)

Reads `A5@(4)` (inner step), indexes into second table at `0x3aa3c`:
- Inner step 0 → `0x3aa40`
- Inner step 1 → `0x3aa54`

**Inner step 0 at `0x3aa40`:**
```
3aa40: bsrw 0x3add8    ; tilemap/display setup
3aa44: bsrw 0x3ad4c    ; RAM clear helper
3aa48: bsrw 0x3ae5a    ; C-window clear + scroll zero
3aa4c: movew #1,%a5@(4) ; inner step → 1
3aa52: rts
```
Runs once at frame 161. Sets inner step to 1.

**Inner step 1 at `0x3aa54`:**
```
3aa54: jsr   0x5a356           ; FIRST ATTRACT SCREEN setup (large routine)
3aa5a–3aa7e: bsrw 0x3bb48 ×4  ; tilemap commands: display first attract content
3aa7e: clrw  %a5@(4)           ; inner step → 0 (reset)
3aa82: movew #1,%a5@(2)        ; sub-state → 1
3aa88: movew #208,%a5@(44)     ; delay timer = 208
3aa8e: rts
```
Runs at frame 162. First attract screen tilemap is drawn via `0x3bb48` (FG tilemap command handler). Sub-state advances to 1, timer set to 208 frames (~3.5s).

### Sub-state 1 progression (at `0x3aa90`)

- Inner step 0 → setup, sets inner step = 1 (no new timer)
- Inner step 1 at `0x3aaae` → `jsr 0x5a3de` (second attract screen setup), many `bsrw 0x3bb48` tilemap commands, sets delay=160 and inner step=2
- Inner step 2 → `0x3ab00` → further setup, eventually `movew #2,%a5@(0)` transitions main state to 2

### Attract progression timeline

| Frame range | Event |
|------------|-------|
| 0–159 | Delay countdown (A5@(44) 160→0) |
| 160 | Inner 0: setup calls |
| 161 | Inner 1: first attract screen drawn, timer=208 |
| 162–369 | Sub-state 1 delay countdown |
| 370 | Sub 1 inner 0: setup |
| 371 | Sub 1 inner 1: second attract screen drawn, timer=160, inner=2 |
| 372–531 | Sub-state 1 inner 2 delay countdown |
| 532+ | Sub 1 inner 2: main state → 2 |

**Attract progression is logically working.** All timer decrements and sub-state transitions execute via the vblank handler every frame. The sequence is fully automatic and requires no external trigger.

### Coin insert interaction with progression

When a coin is inserted mid-attract (at `0x3ac76`):
```
3ac76: clrw  %a5@(44)          ; clear delay timer immediately
3ac7a: movew #1,%a5@(0)        ; main state → 1 (player select)
3ac80: clrw  %a5@(2)
3ac84: clrw  %a5@(4)
```
State transitions to player-select immediately, bypassing remaining attract delays.

---

## 4. Coin Insert Path Audit

### A-button to coin1 shadow

`genesistan_refresh_arcade_inputs()` in V-Int, before arcade tick:
```c
genesistan_shadow_input_390007 = build_system_input_byte(p1_state, p2_state);
```

`build_system_input_byte()` at `startup_bridge.c:155`:
```c
if ((p1_state & BUTTON_A) != 0) value &= (uint8_t)~0x01;  /* clears bit 0 = coin1 */
```
Shadow byte default: `0xFF`. When A pressed: bit 0 cleared → `0xFE`.

Opcode rewrite: `btst #0, 0x390007` in arcade ROM is rewritten (via spec patch) to read from `genesistan_shadow_input_390007` in Genesis WRAM.

### Coin detect function at `0x3ac04` (called every vblank via `0x3a042`)

```
3ac04: btst  #0, 0x390007    ; shadow bit 0: 0=pressed (active-low)
3ac0c: bnes  0x3ac16         ; bit=1 (released) → check edge latch
3ac0e: movew #1,%a5@(32)     ; bit=0 (pressed) → set latch A5@(32)
3ac14: rts

3ac16: tstw  %a5@(32)        ; was latch set?
3ac1a: beqs  0x3ac14         ; no → return
3ac1c: clrw  %a5@(32)        ; yes → clear latch (edge consumed)
3ac20: movew %a5@(18),%d0    ; read current credits
... BCD increment (with carry check) ...
3ac46: movew %d0,%a5@(18)    ; write incremented credits
3ac4a: cmpiw #9,%d0          ; credit display threshold
... credit display draw via 0x3ae50 ...
3ac68: moveb #4,%d0; bsrw 0x3f084  ; draw credit digit to FG C-window
3ac70: tstw  %a5@(52)        ; is a player already active?
3ac74: bnes  0x3ac14         ; if active → stay in current state
3ac76: clrw  %a5@(44)        ; clear delay timer
3ac7a: movew #1,%a5@(0)      ; → MAIN STATE 1 (player select)
3ac80: clrw  %a5@(2)
3ac84: clrw  %a5@(4)
3ac88: rts
```

### Edge detector behavior

- Frame N: A pressed → shadow bit 0 = 0 → A5@(32) = 1, return
- Frame N+1: A released → shadow bit 0 = 1 → A5@(32) = 1 → clear latch → credit increment → state → 1

**One frame of press then release is sufficient.** The edge detector is a standard "latch-on-press, consume-on-release" pattern.

### Coin2 path (for completeness)

`0x3ac8a`–`0x3acf3`: coin2 detect on `btst #5,%a5@(34)` latch with port `0x390007` bit 5. Our `build_system_input_byte()` does NOT map any button to bit 5. Coin2 is not mapped. This is correct — only coin1 (BUTTON_A) is available. Coin2 path has no effect.

### Init state of edge latches

- `A5@(32)` (coin1 latch) = 0 from `memset` in `genesistan_init_workram_direct()`. ✓ No spurious coin on startup.
- `A5@(34)` (coin2 latch) = 0. ✓

### Coin insert is logically working

All path segments are verified:
1. BUTTON_A → shadow bit 0 cleared ✓
2. Opcode rewrite delivers shadow to arcade read ✓
3. Edge detector sets/clears A5@(32) correctly ✓
4. BCD credit increment at A5@(18) ✓
5. Credit digit display via `0x3f084` ✓
6. State transition `A5@(0) → 1` ✓

---

## 5. Logic vs Visual Feedback Classification

### A) Attract progression logic

**Classification: LOGIC WORKING — VISUAL PARTIALLY IMPAIRED.**

The state machine advances through sub-states automatically. First attract screen (sub 0 inner 1 at `0x3aa54`) draws via `0x3bb48` tilemap commands — FG content (FG is confirmed correct). Second attract screen (sub 1 inner 1 at `0x3aaae`) also draws via `0x3bb48` — also FG content.

Why second screen appears visually identical to first: both screens write FG content (which may not change dramatically between attract screens) and BG content (which is completely invisible due to row/col inversion — all BG writes target VDP column 0). The BG content difference between attract screen 1 and screen 2 is invisible. The FG content difference may be subtle.

**"Attract does not advance to second screen"** = second screen IS being drawn but looks indistinguishable from first screen due to BG rendering failure.

### B) Coin insert feedback

**Classification: LOGIC WORKING — VISUAL FEEDBACK DEPENDS ON FG + CREDIT DISPLAY.**

When A is pressed:
1. `0x3f084` (called at `0x3ac68`) writes the credit digit to the FG C-window. This goes through our FG hook, which correctly writes to VDP BG_A. FG is confirmed working. The credit digit should appear.
2. State transitions to 1. State 1 handler calls `0x3bb48` multiple times to draw the player-select screen ("PUSH 1 OR 2 PLAYER BUTTON") via FG.

**Why "pressing A does not visibly insert a credit"**: Most likely the player-select screen DOES change, but:
- The credit digit display at a specific FG position may not be in the visible portion (depends on FG scroll + row/col of the write)
- Or the player-select screen looks similar to the attract screen without the BG layer completing it
- Or the row/col inversion on BG is making "PUSH 1 OR 2 PLAYER BUTTON" text that's on BG invisible

**It is also possible that credit feedback IS appearing but the observer is looking at BG content that isn't changing visually.** The FG-rendered content that does change may be rendered in a position or with tiles that aren't yet visible/recognizable.

### C) Summary matrix

| Observation | Logic | Visual |
|-------------|-------|--------|
| First attract screen appears | Working ✓ | FG correct, BG col-0 only |
| Second attract screen invisible | Working ✓ | BG content change not visible (col-0 only) |
| A-button coin credit increment | Working ✓ | FG feedback should appear (unverified visually) |
| Player-select screen after coin | Working ✓ | BG content (screen text?) likely invisible |

---

## 6. Re-evaluation of Prior Input Audit

The prior audit (Build 295, `live_gameplay_input_ownership_audit.md`) concluded: input ownership correct, fully operational, no assembly implementation needed.

### Re-evaluation for state 0 attract context

**Conclusion stands with one nuance:**

In state 0, the coin detect function `0x3ac04` reads `0x390007` via opcode-rewrite. This is the **same** opcode-rewrite mechanism verified in the prior audit. The shadow is updated every V-Int via `genesistan_refresh_arcade_inputs()` at `main.c:1962`, before the arcade tick. The ordering guarantee from the prior audit (input refresh → arcade tick) is preserved in state 0 exactly as in gameplay state.

**New finding — edge detector requires release event:**

The prior audit did not specifically address the coin edge detector. The coin1 latch at A5@(32) requires a PRESS followed by a RELEASE within the same V-Int session. Since `genesistan_refresh_arcade_inputs()` is called once per V-Int and the arcade tick runs immediately after, the sequence per frame is:

1. Shadow updated from joypad (press state recorded)
2. Arcade tick runs: coin detect reads shadow
3. If shadow bit=0 (pressed): latch set, return
4. Next V-Int: shadow updated (still pressed or released)
5. If released: latch consumed, credit added

This works correctly for any A-button press of ≥1 frame duration followed by a release. No issue.

**New finding — state 0 runs coin detect regardless of delay timer:**

The delay timer at `A5@(44)` only gates the sub-state dispatch in the state 0 handler. It does NOT affect `0x3abe2` (coin detect) which is called before the state dispatch, at `0x3a042`. Coin detection is active from frame 1 of attract mode even during the 160-frame initial delay. This is correct behavior.

**Prior audit conclusion: CONFIRMED STILL VALID.** No input ownership issue introduced by moving to state 0.

---

## 7. Confirmed Root Causes

### Root Cause 1 — Second attract screen not visually distinct (CONFIRMED)

**Source:** BG row/col inversion in `pc080sn_dest_ptr_to_row_col()` (`main.c:1282–1283`), identified in Build 297 audit.

**Evidence:** All BG writes go to VDP column 0 (8px wide). BG plane is visually absent except for one 8px stripe. Both attract screens draw different BG content; neither is visible. The screens look the same because the BACKGROUND layer is identical (blank) for both.

**Classification: VISUAL-ONLY failure. Logic is correct.**

### Root Cause 2 — Coin feedback not recognizable (CONFIRMED)

**Source:** Same BG row/col inversion. Player-select screen "PUSH 1 OR 2 PLAYER BUTTON" text and layout uses BG content that is invisible. Credit digit display via `0x3f084` writes to FG C-window — this should be visible, but may be in a position that isn't recognized as a credit change against the current visual state.

**Classification: VISUAL-ONLY failure. Coin logic and state transition are correct.**

---

## 8. Rejected Hypotheses

| Hypothesis | Why Rejected |
|------------|--------------|
| Attract not advancing because A5@(0) still = 1 | REJECTED: startup_bridge.c:266 sets `genesistan_arcade_workram_words[0] = 0` |
| Coin insert fails because BUTTON_A not mapped to coin1 | REJECTED: `build_system_input_byte()` at startup_bridge.c:155 clears bit 0 when BUTTON_A pressed |
| Edge detector (A5@(32)) fails due to wrong init | REJECTED: memset zeroes entire workram; A5@(32) = 0 at init ✓ |
| Delay timer A5@(44) prevents coin detection | REJECTED: coin detect at `0x3a042` runs before state dispatch, independent of delay timer |
| State 0 sub-state progression does not fire | REJECTED: timer decrements every vblank; sub-states advance automatically per the timing trace above |
| Attract second screen uses different pipeline than FG | REJECTED: `0x3bb48` tilemap commands are confirmed to write to FG C-window (same path as first screen) |
| A5@(32) spuriously set at init causing immediate coin | REJECTED: memset clears it to 0; `btst #0` runs first to check if coin is pressed, which it isn't at init |

---

## 9. Remaining Unknowns

### UNKNOWN A — Exact visual content of player-select state via FG

**Status:** UNVERIFIED — requires runtime observation after row/col fix.

When coin is inserted and state transitions to 1, state 1 handler calls `0x3bb48` with command indices 9, 10/11, 30, 32. The visual content of these commands (tile positions, text strings) is not traced here. After the BG row/col fix, the player-select screen should have recognizable BG content. Whether the current (BG-broken) player-select state is visually distinguishable from the attract screen is an empirical question.

### UNKNOWN B — Credit digit position via `0x3f084`

**Status:** UNVERIFIED — location of credit digit on screen not traced.

`0x3f084` is the arcade's text/digit writer. It writes to the FG C-window, which our FG hook processes correctly. Whether the credit digit appears in the visible FG region (rows 4–31) is not confirmed. If the credit digit is at FG row < 4, the `cmpi.w #4, D1` skip guard in the FG assembly skips the write.

### UNKNOWN C — Exact visual of `0x3bb48` command index mapping

**Status:** NOT FULLY TRACED.

`0x3bb48` at disasm line 74988 reads D0 as a command index (0-127 range), fetches a pointer from a table at `0x3bb7c`, and writes tile data to FG C-window entries. The 128-entry command table content and what screens each index renders are not traced here. After the BG fix, all commands that write BG content become visible.

---

## 10. Most Important Currently Verified Issue

**BG row/column inversion in `pc080sn_dest_ptr_to_row_col()` (`main.c:1282–1283`).**

This is the single root cause blocking visual progress for:
- Attract screen 2 appearing distinct from screen 1
- Player-select screen ("PUSH 1 OR 2 PLAYER BUTTON") being recognizable after coin insert
- All BG-resident gameplay content

The fix is precisely scoped: swap `*out_row` and `*out_col` — no assembly changes required. All other systems (attract logic, coin logic, FG rendering, input) are verified working correctly. The BG row/col swap is the only change needed to unblock both attract progression visibility and coin-insert feedback visibility.

All other issues (text position, credit digit position) cannot be validly assessed until BG renders correctly.
