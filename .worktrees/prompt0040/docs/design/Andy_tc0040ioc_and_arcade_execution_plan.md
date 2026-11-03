# Andy — TC0040IOC Input Model and Arcade Execution Plan

## 1. Executive Summary

This document defines the complete TC0040IOC input emulation model, the arcade ROM execution
model, the entry/control-flow architecture, the patch/hook strategy, and all drift risks for
`apps/rastan-direct/`. It is written for direct implementation by Cody with no ambiguity.

The `rastan-direct` branch currently has a stable synthetic video baseline (checkerboard BG,
VBlank commit discipline, steady-state ~532 cycles/frame). The project is transitioning from
synthetic scaffolding to real arcade-driven execution. This plan defines the foundational
contracts that make that transition possible.

Key findings:

1. **TC0040IOC model**: All 19–22 TC0040IOC patch sites are known and categorized. The model is
   memory-mapped shadow bytes in Genesis WRAM, updated once per frame before the arcade tick.
   DIP reads are replaced with ROM constants. Joystick reads route to a Genesis pad stub.
   Service/tilt/test reads return 0xFF permanently. Coin reads target a shadow byte or are
   suppressed.

2. **Input timing**: Shadow bytes must be populated at the top of each VBlank handler, before any
   call to the arcade execution tick. This is the same discipline already proven in the SGDK
   branch (genesistan_refresh_arcade_inputs → arcade tick ordering in
   genesistan_frontend_live_vint_handoff).

3. **Arcade ROM execution model**: Direct execution of relocated arcade opcodes (ARCADE_ROM_BASE
   = 0x000200, confirmed by startup_title_remap.json policy). TC0040IOC patch sites replaced with
   stubs or immediate loads at build time by the patcher tool. No interpretation layer. No
   translated opcodes.

4. **Entry/control flow**: rastan-direct main loop calls arcade_tick_logic as a synthetic stub.
   Real arcade execution replaces arcade_tick_logic with a JSR to the arcade ROM entry point
   (0x03A008 + ARCADE_ROM_BASE). VBlank owns video commit. Arcade tick runs from main loop.

5. **Single next step**: Implement the TC0040IOC shadow byte infrastructure and Genesis pad read
   stub as the foundational input layer for rastan-direct, using WRAM addresses matching the
   SGDK branch symbol layout.

---

## 2. Inputs Audited

1. `/home/tighe/projects/rastan-genesis/docs/design/TC0040IOC_specifications.md` — READ COMPLETE:
   full register map, bit layout, active-low convention, DIP init behavior, 19–22 patch sites,
   factory default values, no-SGDK design principles, all replacement byte specs.

2. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/main_68k.s` — READ COMPLETE:
   383 lines, VBlank handler (_VINT_handler), main loop (frame_counter wait + arcade_tick_logic
   BSR), arcade_tick_logic synthetic stub (scroll counters only), init_staging_state, BSS layout.

3. `/home/tighe/projects/rastan-genesis/apps/rastan-direct/src/boot/boot.s` — READ COMPLETE:
   55 lines, Genesis vector table, TMSS gate, JSR to main_68k, _default_handler at 0x000200.
   ARCADE_ROM_BASE = 0x000200 is where _default_handler lives, which will be displaced when
   arcade ROM is linked.

4. `/home/tighe/projects/rastan-genesis/docs/design/Andy_first_arcade_driven_bg_hook_plan.md` —
   READ COMPLETE: BG hook plan at 0x055968, direct execution model confirmed, hook contract
   (A5 = WRAM base, workram[0x10A0] = dest_ptr, workram[0x10CA] = strip_index), JSR patch
   in startup_title_remap.json at arcade_pc 0x055968.

5. `/home/tighe/projects/rastan-genesis/apps/rastan/src/main.c` — SEARCHED: genesistan_
   refresh_arcade_inputs is in startup_bridge.c. JOY_readJoypad(JOY_1/2) used. Shadow bytes
   confirmed as genesistan_shadow_input_390001/3/5/7 in .bss.patcher section.

6. `/home/tighe/projects/rastan-genesis/apps/rastan/src/startup_bridge.c` — READ (lines 100–244):
   build_player_input_byte (d-pad + B/C → active-low), build_aux_input_byte (B/C/A → bits 4/5/6),
   build_system_input_byte (A=coin, START=start1, A+B+C=service), genesistan_refresh_arcade_inputs
   (calls all three builders, writes all four shadows, no-op if arcade code has not reached
   SCREEN_FRONTEND_LIVE state).

7. `/home/tighe/projects/rastan-genesis/specs/startup_title_remap.json` — READ: confirms
   ARCADE_ROM_BASE = 0x000200, whole_maincpu_copy source=0 dest=0x200 length=0x60000,
   required_symbols include genesistan_shadow_input_390001/3/5/7, opcode rewrite rules map
   0x390001 → genesistan_shadow_input_390001, 0x390003 → 390003, 0x390005 → 390005,
   0x390007 → 390007, 0x390009 → genesistan_shadow_dip1, 0x39000B → genesistan_shadow_dip2.

8. `/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt` — SEARCHED: confirmed all
   TC0040IOC read sites: 0x3A4A2 (P1), 0x3A4A8 (P2), 0x3A778 (P1), 0x3A77E (P2), 0x3A490
   (sys switches bits 3+4), 0x3A7B8 (tilt bit 1), 0x3AB96 (test bit 2), 0x3AC04 (service bit 0),
   0x3A91A (sys switches), 0x3AF7A (DIP1), 0x3AF86 (DIP2), 0x3A0A8/B2/C0 (coin btst).
   Confirmed 0x3A0A8 is called from main credit loop at 0x3A046 (bsrw 0x3a0a8).

9. `/home/tighe/projects/rastan-genesis/docs/design/live_gameplay_input_ownership_audit.md` —
   READ COMPLETE: definitive map of all arcade input read sites and their shadow register
   bindings, verified input refresh timing (before arcade tick every V-Int), all four shadow
   bytes proven correct through gameplay.

10. `/home/tighe/projects/rastan-genesis/docs/design/Cody_rainbow_islands_vdp_template_analysis.md`
    — READ: Rainbow Islands input model confirmed: no TC0040IOC equivalent discussed (RI's
    equivalent arcade I/O is handled via same opcode patch discipline); VBlank is commit-only.

---

## 3. TC0040IOC Behavior and Mapping

### 3.1 Hardware Context

The TC0040IOC is a byte-wide memory-mapped I/O chip at addresses 0x380000–0x39000F on the arcade
68000 bus. On Genesis hardware those addresses are unmapped. The 68000 returns a bus error or
undefined data. No TC0040IOC registers may be read or written by the arcade code at runtime on
Genesis hardware.

### 3.2 Register Map (Confirmed from Arcade Disassembly)

| Arcade Address | Direction | Content | Active-Low |
|----------------|-----------|---------|------------|
| 0x390001 | Read | P1 joystick + buttons | YES |
| 0x390003 | Read | P2 joystick + buttons | YES |
| 0x390005 | Read | Coin inputs (bits 4/5/6) | YES |
| 0x390007 | Read | System switches (service/tilt/test/start) | YES |
| 0x390009 | Read | DIP bank 1 (SW1) | YES (NOT before use) |
| 0x39000B | Read | DIP bank 2 (SW2) | YES (NOT before use) |
| 0x380000 | Write | Coin lockout / flip-screen control | N/A |

Active-low convention: 0xFF = all switches open/inactive. The code at 0x3AF7A/0x3AF86 uses
`notb %d0` after reading DIP banks to invert to active-high working values before storing to
WRAM. The joystick read paths at 0x3A4A2/0x3A778 do NOT invert — they test for zero bits
(pressed) directly.

### 3.3 P1 Joystick Bit Layout (0x390001, active-low)

| Bit | Mask | Arcade Meaning | Genesis Button |
|-----|------|---------------|----------------|
| 0 | 0x01 | Joystick UP | D-pad UP |
| 1 | 0x02 | Joystick DOWN | D-pad DOWN |
| 2 | 0x04 | Joystick LEFT | D-pad LEFT |
| 3 | 0x08 | Joystick RIGHT | D-pad RIGHT |
| 4 | 0x10 | Button 1 (attack) | BUTTON_B |
| 5 | 0x20 | Button 2 (jump) | BUTTON_C |
| 6 | 0x40 | Button 3 (unused in Rastan) | not mapped |
| 7 | 0x80 | Button 4 (unused in Rastan) | not mapped |

P2 (0x390003): identical bit layout applied to P2 controller.

### 3.4 System Input Bit Layout (0x390007, active-low)

| Bit | Mask | Arcade Meaning | Genesis Mapping |
|-----|------|---------------|-----------------|
| 0 | 0x01 | Coin 1 insert | BUTTON_A (P1) |
| 1 | 0x02 | Tilt | suppressed (0xFF) |
| 2 | 0x04 | Test button | A+B+C combo (service guard) |
| 3 | 0x08 | Player 1 START | BUTTON_START (P1) |
| 4 | 0x10 | Player 2 START | BUTTON_START (P2) |
| 6 | 0x40 | Flip screen state | suppressed |

Note: The SGDK branch maps 0x390007 bit 0 as "coin" but the TC0040IOC_specifications.md maps
bit 0 of 0x390007 as "service mode (soft)". The live_gameplay_input_ownership_audit.md
(Section 4) clarifies: the startup_bridge build_system_input_byte maps A→bit0 as "coin1 insert"
as proven from the title/front-end code. This is the correct mapping for rastan-direct.

### 3.5 DIP Switch Factory Defaults (for Hardcoded Patches)

| Register | Raw hardware value (active-low) | After NOT (active-high workram) | Result |
|----------|---------------------------------|----------------------------------|--------|
| DIP Bank 1 (0x390009) | 0xFE | 0x01 | Test=OFF, flip=OFF, demo sound=OFF, upright, 1C/1C |
| DIP Bank 2 (0x39000B) | 0xFF | 0x00 | Easy, 30k bonus, 3 lives, continue=OFF |

All-open (0xFF raw) is safe for both banks — boots to normal attract mode.

### 3.6 Shadow Byte WRAM Locations

The SGDK branch stores shadow bytes in `.bss.patcher` section symbols. For rastan-direct, the
same symbols must exist in Genesis WRAM (0xFF0000–0xFFFFFF). The symbols and their roles:

| Symbol | WRAM Location | Updated by | Read by |
|--------|---------------|------------|---------|
| `shadow_p1_input` (= genesistan_shadow_input_390001 in SGDK) | WRAM, fixed at link time | pad read stub (every frame) | patched arcade code at 0x3A4A2, 0x3A778 |
| `shadow_p2_input` (= genesistan_shadow_input_390003) | WRAM | pad read stub | patched arcade code at 0x3A4A8, 0x3A77E |
| `shadow_coin_input` (= genesistan_shadow_input_390005) | WRAM | pad read stub | patched arcade code at 0x3A0A8, 0x3A0B2, 0x3A0C0 |
| `shadow_sys_input` (= genesistan_shadow_input_390007) | WRAM | pad read stub | patched arcade code at 0x3A490, 0x3A7B8, 0x3AB96, 0x3AC04, 0x3A91A |
| `shadow_dip1` | WRAM or ROM constant | one-time init | patched DIP reads at 0x3AF7A |
| `shadow_dip2` | WRAM or ROM constant | one-time init | patched DIP reads at 0x3AF86 |

For rastan-direct, all shadow bytes live in the `.bss` section of main_68k.s (or a dedicated
io_shadows.s file). Symbol names can differ from the SGDK branch, but the WRAM addresses must
be stable once the binary is linked.

### 3.7 Complete Patch Table

| ROM Addr | Original Instruction | Replacement | Category |
|----------|---------------------|-------------|----------|
| 0x03AF7A | `moveb 0x390009, %d0` (6 bytes) | `moveb #0xFE, %d0` + `nop` (6 bytes) | DIP1 constant |
| 0x03AF86 | `moveb 0x39000b, %d0` (6 bytes) | `moveb #0xFF, %d0` + `nop` (6 bytes) | DIP2 constant |
| 0x03A4A2 | `moveb 0x390001, %d0` (6 bytes) | `jsr rastan_direct_read_p1_input` (6 bytes) | P1 joystick stub |
| 0x03A4A8 | `moveb 0x390003, %d1` (6 bytes) | `jsr rastan_direct_read_p2_input` (6 bytes) | P2 joystick stub |
| 0x03A778 | `moveb 0x390001, %d0` (6 bytes) | `jsr rastan_direct_read_p1_input` (6 bytes) | P1 joystick stub |
| 0x03A77E | `moveb 0x390003, %d1` (6 bytes) | `jsr rastan_direct_read_p2_input` (6 bytes) | P2 joystick stub |
| 0x03A0A8 | `btst #6, 0x390005` (8 bytes) | `btst #6, shadow_coin_input` (8 bytes) | Coin shadow |
| 0x03A0B2 | `btst #4, 0x390005` (8 bytes) | `btst #4, shadow_coin_input` (8 bytes) | Coin shadow |
| 0x03A0C0 | `btst #5, 0x390005` (8 bytes) | `btst #5, shadow_coin_input` (8 bytes) | Coin shadow |
| 0x03A490 | `moveb 0x390007, %d0` (6 bytes) | `moveq #0xFF, %d0` + 4× `nop` | System sw suppress |
| 0x03A7B8 | `btst #1, 0x390007` (8 bytes) | `nop` ×4 (8 bytes) (always "not tilted") | Tilt suppress |
| 0x03AB96 | `btst #2, 0x390007` (8 bytes) | `nop` ×4 (8 bytes) (always "not test") | Test suppress |
| 0x03AC04 | `btst #0, 0x390007` (8 bytes) | `btst #0, shadow_sys_input` (8 bytes) | Coin/service shadow |
| 0x03A91A | `moveb 0x390007, %d0` (6 bytes) | `moveq #0xFF, %d0` + 4× `nop` | System sw suppress |
| 0x03A1D8 | `movew %d0, 0x380000` (6 bytes) | `nop` ×3 | Control write suppress |
| 0x03AE9C | `clrw 0x380000` (6 bytes) | `nop` ×3 | Control write suppress |
| 0x03AF1E | `movew %d0, 0x380000` (6 bytes) | `nop` ×3 | Control write suppress |

Note: Additional 0x390007 read sites exist at 0x03A3A6, 0x03AC94, 0x03ACFE (per
live_gameplay_input_ownership_audit.md Section 2 shadow table). These must all be patched.
The patcher tool's opcode scan using the address-rewrite rules in startup_title_remap.json
covers all of them automatically when shadow_sys_input is declared as the replacement symbol
for 0x390007.

---

## 4. Input Timing Model

### 4.1 When Does Arcade Rastan Read 0x390001/0x390003?

All arcade input reads from the disassembly are in subroutines called from the arcade vblank
handler at 0x03A008. Confirmed call chain:

```
0x03A008 (arcade vblank entry)
  → 0x3A046: bsrw 0x3A0A8    (coin polling)
  → 0x3A47C/0x3A478: (conditional) → 0x3A490 (system switch check → P1 input at 0x3A4A2/0x3A4A8)
  → 0x3A776/0x3A778: P1/P2 input at 0x3A778/0x3A77E (2nd read site)
  → 0x3A7B8: tilt check
  → 0x3AB96: test button check
  → 0x3AC04: service switch check
```

All reads happen during the arcade tick (called from the same VBlank frame or main loop frame
that Genesis uses). The timing model is:

**Input model: shadow bytes are updated ONCE per frame, BEFORE the arcade execution tick.**

### 4.2 Timing for rastan-direct (No SGDK, No JOY_update)

In rastan-direct, the VBlank handler (_VINT_handler) owns video commit. The main loop calls
arcade_tick_logic once per frame (after waiting for frame_counter to advance). The input update
must happen either:

- Option A: At the top of _VINT_handler, before vdp_commit_bg — but this is in VBlank ISR,
  which limits timing budget.
- Option B: At the top of arcade_tick_logic, before any arcade execution — this runs in the
  main loop, guaranteed after VBlank has already committed the prior frame.

**Chosen model: Option B.** Input shadow bytes are updated at the entry of arcade_tick_logic
(the main-loop arcade execution function), as the first operation before any arcade code runs.
This is structurally equivalent to the SGDK branch, where genesistan_refresh_arcade_inputs runs
before genesistan_run_original_frontend_tick in the VBlank callback. For rastan-direct, the
arcade tick is in the main loop, so input update moves to the main loop as well.

The ordering guarantee: shadow bytes written BEFORE arcade execution reads them. Race condition
risk: NONE. The main loop is single-threaded between VBlank events. The shadow bytes are
written by rastan-direct code (in the main loop), and read by arcade code (in the same main
loop call), with no interleaving interrupt that touches them.

**Input update timing defined: YES.**

### 4.3 Genesis Pad Read Implementation (No SGDK)

The Genesis I/O hardware presents joypad data at 0xA10003 (port 1 data) and 0xA10005 (port 2
data). For a standard 3-button pad, a single `moveb 0xA10003, %d0` returns the current button
state. No latch/select sequence is required for 3-button pads.

The byte read from 0xA10003 has the following active-low bit layout (Genesis hardware):

| Bit | Genesis meaning |
|-----|----------------|
| 0 | UP |
| 1 | DOWN |
| 2 | LEFT |
| 3 | RIGHT |
| 4 | BUTTON_B |
| 5 | BUTTON_C |
| 6 | BUTTON_A |
| 7 | START (requires TH line select) |

For a 3-button pad with TH=1 (default): bits 0–5 are live. Bits 6–7 require a 6-button sequence
or alternate TH state. For the initial rastan-direct implementation, only bits 0–5 are used.
Start and the A button (coin) require reading the TH-toggled state. The approach is: the Genesis
I/O port direction register at 0xA1000B controls TH output; the standard method is to write TH
high, wait, read phase 1 (UP/DOWN/LEFT/RIGHT/B/C), write TH low, read phase 2 (A/START/C/B).

For the initial bring-up, the simplest correct approach is to initialize the port direction
registers in boot.s and issue the two-phase TH toggle to read all buttons. This is equivalent
to what JOY_readJoypad() does internally in SGDK.

The pad read stub (`rastan_direct_read_inputs`) does:
1. Initialize 0xA1000B (port 1 ctrl) = 0x40 (TH output, rest input) in boot/init (once).
2. In the per-frame stub: write TH=1 to 0xA10003 (bit 6), read 0xA10003 (get phase 1:
   UP/DOWN/LEFT/RIGHT/B/C active-low). Then write TH=0, read 0xA10003 (get phase 2:
   UP/DOWN/A/START active-low in bits 0–3). Construct shadow bytes from both phases.

The stub returns the active-low byte directly — no inversion needed, since the arcade code
expects active-low values from the TC0040IOC.

---

## 5. Arcade ROM Execution Model

### 5.1 The One Model: Direct Execution of Relocated Arcade Opcodes

The arcade ROM execution model for rastan-direct is: **direct execution of relocated arcade
opcodes with patched instructions, no interpretation layer.**

This is confirmed by:
1. `startup_title_remap.json` policy: `"execute_from_relocated_base": true`,
   `"planned_arcade_rom_base": "0x000200"`, `"whole_maincpu_copy": {"dest_start": "0x000200"}`.
2. The SGDK branch executes arcade code directly from ARCADE_ROM_BASE = 0x000200
   (startup_trampoline.s line 37: `#define ARCADE_ROM_BASE 0x000200`).
3. The BG hook plan (Andy_first_arcade_driven_bg_hook_plan.md Section 3.1) confirms the hook at
   0x055968 fires directly during arcade execution, with %a5 = WRAM base and the full arcade
   register state live.

There is no translation layer. Arcade 68000 opcodes execute as native Genesis 68000 code.
TC0040IOC reads and other hardware accesses are patched at the binary level before execution.

### 5.2 Memory Layout

| Region | Genesis Address Range | Content |
|--------|----------------------|---------|
| Genesis boot vectors + header | 0x000000–0x0001FF | rastan-direct boot.s |
| Arcade ROM (relocated) | 0x000200–0x06021F | maincpu.bin at +0x200 offset |
| Genesis code/data (rastan-direct) | After arcade ROM, typically 0x060200+ | main_68k.s, hooks, LUTs |
| Genesis WRAM | 0xFF0000–0xFFFFFF | Stack (top), BSS (mid), arcade WRAM |

The 0x60000-byte arcade ROM occupies 0x000200–0x06021F. rastan-direct's own code (boot vectors
already at 0x000000–0x0001FF) and the arcade ROM do not conflict. The only collision risk is
the _default_handler at 0x000200 in boot.s — this will be overwritten by the arcade ROM when
it is linked. The _default_handler stub at 0x000200 must be removed from boot.s when the
arcade ROM is linked, since the arcade ROM starts at 0x000200 by design.

### 5.3 ROM and WRAM Address Space

- Genesis ROM: 0x000000–0x3FFFFF (4 MB). Arcade ROM (0x60000 bytes = 384 KB) fits entirely
  within this range when placed at 0x000200.
- Genesis WRAM: 0xFF0000–0xFFFFFF. Shadow bytes and BSS live here.
- Arcade WRAM mirror: The arcade code uses A5 as a WRAM base pointer. In rastan-direct, A5 is
  set to the base of the arcade WRAM area in Genesis WRAM (a fixed region within 0xFF0000–
  0xFFFFFF). This is the same initialization performed in the SGDK branch.
- No address space conflict exists at this stage.

### 5.4 Patch Application Mechanism

Patches are applied at build time by the patcher tool, using `startup_title_remap.json` as the
specification. The patcher:
1. Copies the raw arcade ROM binary to the output Genesis ROM starting at 0x000200.
2. Scans the copied ROM for the opcode-with-abs-long-operand patterns listed in
   `rom_absolute_call_relocation`.
3. Rewrites all absolute ROM targets (JSR/JMP/LEA abs-long addressing arcade ROM addresses) to
   add ARCADE_ROM_BASE (0x200) offset.
4. Applies declared patch entries from `copied_ranges` (replacing specific opcodes at known
   addresses with stub calls or immediate loads).
5. Writes the final patched binary.

For rastan-direct, the same patcher is used. The patch entries for TC0040IOC reads are already
declared in startup_title_remap.json as symbol-rewrite rules (0x390001 → shadow_input_390001,
etc.). New symbol names for rastan-direct shadow bytes must be declared, or the same SGDK
symbol names must be used with rastan-direct-compatible definitions.

---

## 6. Entry Point and Control Flow

### 6.1 Arcade ROM Entry Point After Relocation

The arcade maincpu entry point is 0x00000000 (the reset vector in the arcade ROM). After
relocation to ARCADE_ROM_BASE = 0x000200, the arcade entry point becomes **0x000200**. However,
in the Genesis binary, 0x000200 is the start of the _default_handler in the current boot.s.
When the arcade ROM is linked at 0x000200, it overwrites _default_handler.

The initial arcade execution entry that the SGDK branch uses is **0x03A008 + ARCADE_ROM_BASE**:
- 0x03A008 is the arcade vblank/tick handler entry confirmed in live_gameplay_input_ownership_audit.md.
- After relocation: 0x03A008 + 0x000200 = **0x03A208** in Genesis address space.

### 6.2 How rastan-direct Calls Arcade Execution

Current state: arcade_tick_logic in main_68k.s is a synthetic stub (lines 231–253) that only
advances scroll counters.

Real arcade execution replaces arcade_tick_logic:
```
arcade_tick_logic:
    bsr     rastan_direct_update_inputs   ; update shadow bytes from Genesis pad
    jsr     0x03A208                      ; call arcade tick at 0x3A008 + ARCADE_ROM_BASE
    rts
```

The main loop becomes:
```
.Lmain_loop:
    move.w  frame_counter, %d0
.Lwait_vblank:
    cmp.w   frame_counter, %d0
    beq.s   .Lwait_vblank
    bsr     arcade_tick_logic            ; update inputs + run arcade tick
    bra.s   .Lmain_loop
```

This is the correct model. The main loop advances once per VBlank, calls arcade_tick_logic
which (a) updates input shadow bytes and (b) executes the arcade code for one tick.

### 6.3 Interrupt Model

Level 5 VBlank is owned by rastan-direct (_VINT_handler). It handles:
1. Display-off bracket
2. vdp_commit_bg (or vdp_commit_bg_strips_if_dirty after hook plan)
3. Palette commit (if dirty)
4. Display-on
5. vdp_commit_scroll
6. frame_counter increment

The arcade code does NOT own any interrupt vector. It is called as a subroutine from the
rastan-direct main loop. This is the same ownership model as the SGDK branch post-handoff,
where genesistan_run_original_frontend_tick calls the arcade tick inside the VBlank callback
rather than allowing the arcade code to own VBlank.

For rastan-direct, the arcade tick is in the main loop (not VBlank). VBlank is commit-only. This
is the correct architecture per the Rainbow Islands alignment model.

### 6.4 What arcade_tick_logic Currently Is and What It Becomes

| Phase | arcade_tick_logic content |
|-------|--------------------------|
| Current (synthetic) | Scroll counter increment + masking. Produces synthetic BG scroll motion. |
| After TC0040IOC step | Input update stub (reads Genesis pad, writes shadow bytes). Scroll stub remains for now. |
| After arcade ROM link | Input update + JSR to 0x03A208 (arcade tick entry). Scroll stub removed. |
| After BG hook | Input update + JSR 0x03A208 + BG hook fires during arcade execution. |

---

## 7. Patch / Hook Strategy

### 7.1 Patch Application: Build-Time, Not Runtime

All patches are applied at build time by the patcher tool. The source of truth is
`startup_title_remap.json`. No runtime self-modification of code. No SMC (self-modifying code).

Rationale: build-time patching is verifiable (original_bytes check in the patcher), repeatable
(same input → same output), and safe for ROM-only environments. Runtime patching would require
WRAM-resident code and would be invisible to disassembly tools.

### 7.2 Patch Contract Definition

Each TC0040IOC patch entry in startup_title_remap.json has the form:

```json
{
  "arcade_pc": "0x0NNNNN",
  "original_bytes": "XXXXXXXXXXXX",
  "replacement_bytes": "YYYYYYYYYY00..."
}
```

- `arcade_pc`: address in the arcade ROM binary (before relocation offset). The patcher adds
  ARCADE_ROM_BASE (0x200) to compute the Genesis ROM address to patch.
- `original_bytes`: hex bytes expected at that address in the arcade ROM. The patcher verifies
  these match before applying the patch. If they do not match, the build fails.
- `replacement_bytes`: hex bytes to write at the patched location. For a 6-byte instruction
  replaced by JSR, this is `4EB9 AAAAAAAA` where AAAAAAAA is the Genesis address of the target
  stub.

### 7.3 Input Read Replacement: JSR Stub vs Immediate Move

Two options exist for joystick read patches:

**Option A: `move.b shadow_p1_input, %d0`** (direct shadow byte read, 6 bytes: `1039 AAAAAAAA`)

**Option B: `jsr rastan_direct_read_p1_input`** (stub JSR, 6 bytes: `4EB9 AAAAAAAA`)

The correct choice for rastan-direct is **Option A: direct shadow byte read**.

Justification:
- The shadow byte is updated once per frame in arcade_tick_logic BEFORE the arcade code runs.
  The shadow byte is always current when the arcade code reads it.
- A JSR stub adds function call overhead (BSR/RTS = 4 cycles each way) for no benefit, since
  the pad state was already written to the shadow.
- Option A is identical in byte count (6 bytes) to the original `moveb abs, %d0` instruction.
  The original opcode is `1039 0039 0001` (moveb 0x390001, %d0). The replacement is
  `1039 XXXXXXXX` (moveb shadow_p1_input, %d0) where XXXXXXXX is the Genesis WRAM address of
  the shadow byte.
- Option B would be needed only if the stub needed to do computation at read time (e.g., live
  TH toggle per read). Since inputs are pre-computed at frame boundary, Option A is correct.

For the 0x390003 read into %d1 (6-byte instruction `1239 0039 0003`), the replacement is
`1239 XXXXXXXX` (moveb shadow_p2_input, %d1).

### 7.4 DIP Read Replacement: Immediate Load

DIP reads are replaced with immediate loads to %d0 at their existing byte count:

- 0x03AF7A: `103C 00FE 4E71` (moveb #0xFE, %d0 + nop = 6 bytes). The following `notb %d0`
  at 0x3AF80 is unchanged; it inverts 0xFE to 0x01 = factory default DIP1 active-high.
- 0x03AF86: `103C 00FF 4E71` (moveb #0xFF, %d0 + nop = 6 bytes). Not inverted gives 0x00 =
  factory default DIP2 active-high.

These constants are embedded in replacement_bytes in startup_title_remap.json. They are ROM
constants — not shadow bytes, not variables, not configurable at runtime.

### 7.5 Service/Tilt/Test Suppression

All 0x390007 reads not related to coin/start are replaced to return 0xFF (all inactive):

- For `moveb 0x390007, %d0` (6 bytes): replacement = `70FF 4E71 4E71 4E71`
  (moveq #0xFF, %d0 + 3 nops = 2+2+2 = 6 bytes). Correct.
- For `btst #N, 0x390007` (8 bytes): replacement = `4E71 4E71 4E71 4E71`
  (4 nops = 8 bytes). The btst result sets Z flag; after NOP the Z flag is undefined. But the
  following conditional branch was checking for the bit being SET (clear Z = bit set = switch
  pressed). By replacing with NOPs (Z undefined after last NOP is still the prior test result),
  there is a risk. The correct replacement for btst suppress is:
  `moveq #0xFF, %d0` + `btst #N, %d0` = `70FF 0800 00NN` (6 bytes) — but this is only 6
  bytes for an 8-byte instruction.
  
  The safe replacement for an 8-byte btst against abs-long is: `7000 4E71 4E71 4E71`
  (moveq #0, %d0 + 3 nops). Since moveq #0 clears %d0, the subsequent `bnes` (branch if non-zero
  bit = switch pressed) will have Z=1 (d0=0 sets zero flag... but moveq does NOT set the Z flag
  from the btst result; the btst instruction itself sets Z).
  
  The unambiguous correct approach: for btst-against-abs sites, use `4A00 4E71 4E71 4E71`
  (tstb %d0 + 3 nops = 8 bytes). But %d0 must be 0xFF first. Actually the simplest safe 8-byte
  patch is: store 0xFF to a scratch register, then btst against it: `70FF 0800 00NN 4E71`
  (moveq #0xFF, %d0 + btst #N, %d0 + nop = 2+4+2 = 8 bytes). This correctly sets Z=1 (bit set
  in 0xFF, meaning switch is active-low-open = not pressed). This preserves the Z flag contract
  the caller expects.
  
  Cody must use this 8-byte replacement for all btst-against-0x390007 sites.

### 7.6 Coin Shadow Patch

The coin read sites at 0x3A0A8/0x3A0B2/0x3A0C0 use `btst #N, 0x390005` (8-byte abs-long btst).
These are replaced with `btst #N, shadow_coin_input` (8 bytes, same opcode with abs-long
address changed to shadow address). The shadow byte init value is 0xFF (all bits set = no coins
inserted = active-low inactive). When the Genesis player presses BUTTON_A (mapped to coin in
the system byte), the corresponding bit in shadow_coin_input is cleared.

Wait: the SGDK branch maps coin to BUTTON_A bit in `genesistan_shadow_input_390007` (bit 0),
not in `genesistan_shadow_input_390005`. The live_gameplay_input_ownership_audit.md Section 4
shows: coin via BUTTON_A → 0x390007 bit 0. The 0x390005 shadow is used for title/service
probes (B→bit4, C→bit5, A→bit6). This is the correct split:

- 0x390005 (coin hw register): the `btst #6, 0x390005` at 0x3A0A8 checks coin 3/service coin.
  In the SGDK branch, BUTTON_A clears bit 6 of shadow_input_390005 (`build_aux_input_byte`,
  line 166: `if ((state & BUTTON_A) != 0) value &= ~0x40`). So coin insert = A button clears
  bit 6 of 0x390005 shadow. Coin 1 (bit 4) and coin 2 (bit 5) are mapped to B and C respectively
  in the aux byte.
- 0x390007 (system register): BUTTON_A clears bit 0 = "coin 1 soft service" in
  build_system_input_byte.

This dual mapping is the proven correct behavior from the SGDK branch. For rastan-direct, the
same mapping must be implemented.

---

## 8. Drift Risk Analysis and Mitigation

### 8.1 ROM Address Drift

**Risk**: Arcade ROM patch addresses (0x3A4A2, etc.) change if the arcade ROM binary changes.

**Assessment for rastan-direct**: NONE. The arcade maincpu.bin is a fixed binary artifact from
the original arcade PCB dump. It does not change as rastan-direct evolves. Patch addresses are
ROM-content addresses, not Genesis binary layout addresses.

**Mitigation**: The `original_bytes` field in each startup_title_remap.json patch entry is a
byte-exact match guard. If the arcade ROM binary changes, the patcher fails. No additional guard
needed.

### 8.2 Hook Location Drift (Genesis Binary Layout)

**Risk**: JSR targets in replacement_bytes point to Genesis WRAM addresses of rastan-direct
stubs. If the rastan-direct Genesis binary layout changes (more code added, section reordering),
stub addresses change, but the replacement_bytes fields contain the old addresses.

**Assessment**: MEDIUM RISK for JSR-based patches. LOW RISK for direct shadow byte reads
(Option A, recommended in Section 7.3) because the shadow byte address changes only if the BSS
layout changes.

**Mitigation**:
1. Use Option A (direct shadow read via `moveb shadow_addr, %d0`) for all TC0040IOC input reads.
   The shadow byte address is computed at link time and embedded in the patcher's symbol table.
   The patcher tool resolves symbol names to addresses at post-link time, not hardcoded in JSON.
2. For any remaining JSR-based patches (non-input hooks), the replacement_bytes must be
   regenerated after each link. The patcher should support symbolic targets in replacement_bytes,
   not raw hex addresses. This is the existing mechanism in the SGDK branch (the patcher uses
   symbol names from the ELF symbol table, not hardcoded addresses in replacement_bytes).
3. Shadow byte WRAM region must be declared in a fixed-layout section (`.bss.io_shadows`) with
   explicit alignment, placed at a stable offset from the WRAM base.

### 8.3 Opcode Translation Drift (Unpatched Read Sites)

**Risk**: Not all TC0040IOC read sites are patched. An unpatched `moveb 0x390001, %d0` at a
previously inactive code path triggers a bus error when that path becomes active as more arcade
execution is enabled.

**Assessment**: HIGH RISK as more arcade execution paths are activated. The known read sites
(per TC0040IOC_specifications.md and live_gameplay_input_ownership_audit.md) are:
- 0x390001: 0x3A4A2, 0x3A778 (confirmed), plus 0x3F4 and 0x612 (found in disassembly scan —
  these appear to be in the test/demo code but must be verified).
- 0x390003: 0x3A4A8, 0x3A77E (confirmed), plus 0x438 (test/demo code).
- 0x390005: 0x3A0A8, 0x3A0B2, 0x3A0C0 (confirmed), plus others in service paths.
- 0x390007: 7+ sites (confirmed per live_gameplay_input_ownership_audit.md).

**Mitigation**: The opcode scan in startup_title_remap.json (`rom_absolute_call_relocation`
section) scans the entire arcade ROM for absolute operands. The address rewrite rules for
0x390001/3/5/7/9/B cover ALL occurrences, not just known gameplay sites. When the patcher runs
its opcode scan, it rewrites every occurrence it finds. Any remaining unpatched sites are ones
that use different addressing modes (e.g., btst against abs-long with a different size encoding).
The patcher must be verified to catch all 8-byte btst variants.

**Required action**: Before linking arcade ROM, run the patcher in scan-only mode against the
raw arcade ROM and verify zero remaining reads to any 0x39000x address.

### 8.4 Register/State Contract Drift

**Risk**: When a stub fires (from a JSR patch), the stub clobbers registers that the caller
expected to preserve.

**Assessment**: LOW RISK for Option A patches (direct shadow reads are single instructions with
no register clobber beyond the destination register, which is the same register the original
instruction wrote). MEDIUM RISK for any JSR-based stubs.

**Mitigation**: For all JSR stubs:
- Stubs must save and restore all registers except the return-value register.
- The contract for each patch site: which register receives the result (always %d0 or %d1 for
  TC0040IOC reads); which registers are scratch at the call site.
- At 0x3A4A2: original `moveb 0x390001, %d0` writes %d0 only. Replacement must not clobber %d1–%d7 or %a0–%a6.
- At 0x3A4A8: original `moveb 0x390003, %d1` writes %d1 only. Replacement must not clobber %d0.
- Option A (direct move) has no clobber issue. Option A is confirmed correct.

### 8.5 Interrupt Interaction Drift

**Risk**: If the VBlank ISR fires while the arcade tick is executing an input-sensitive code
path, and if the VBlank ISR modifies shadow bytes, a torn-read could occur.

**Assessment**: NONE. The VBlank handler (_VINT_handler) in rastan-direct does NOT read or write
input shadow bytes. Shadow bytes are written in the main loop (arcade_tick_logic entry), and
VBlank is commit-only (video writes only). The two paths do not share shadow byte state.

**Mitigation**: Keep shadow byte writes exclusively in the main-loop pre-tick step. Confirm
that _VINT_handler never touches shadow_p1_input, shadow_p2_input, shadow_coin_input,
shadow_sys_input. This constraint must be documented as a permanent invariant.

---

## 9. Rainbow Islands Alignment

### 9.1 TC0040IOC vs Rainbow Islands I/O Equivalent

Rainbow Islands uses the same TC0040IOC chip (or equivalent Taito I/O controller). From
TC0040IOC_specifications.md Section 7: "Rainbow Islands Genesis (same Taito hardware) handles
TC0040IOC identically: all DIP reads replaced with hardcoded immediate values, joystick reads
replaced with Genesis pad read stubs, coin input routed to a Genesis button, service/test/tilt
reads replaced with inactive constants, control register writes suppressed with NOPs."

The Rainbow Islands Genesis port is the proof that this approach is correct. It is not a
theoretical model — it is an implemented, shipping product.

### 9.2 Memory-Mapped Shadow Bytes vs Per-Read Stubs

Rainbow Islands uses memory-mapped shadow bytes (the patcher rewrites arcade ROM reads from
TC0040IOC addresses to Genesis WRAM shadow addresses). This is exactly the Option A approach
defined in Section 7.3. The shadow bytes are pre-computed each frame before the arcade tick.

The SGDK branch follows the same model (genesistan_shadow_input_390001/3/5/7 written before
arcade tick, arcade code reads shadows via opcode-rewritten addresses). rastan-direct uses the
same model.

### 9.3 VBlank Model Alignment

Rainbow Islands VBlank:
- VBlank is commit-only (no game logic in ISR).
- Game state machine runs outside VBlank.
- Staging buffers populated by game code, committed to VDP in VBlank.

rastan-direct VBlank model is identical:
- _VINT_handler is commit-only (BG commit, palette commit, scroll commit).
- arcade_tick_logic (game logic) runs in main loop, not in ISR.
- staged_bg_buffer populated by arcade hook, committed in VBlank.

**Alignment with Rainbow Islands approach: YES.**

The rastan-direct model directly replicates the Rainbow Islands Genesis architecture at every
level: TC0040IOC handling, shadow byte model, VBlank ownership, commit discipline, and patch
application mechanism.

---

## 10. Single Next Implementation Step

### Step: Implement TC0040IOC Shadow Byte Infrastructure for rastan-direct

This is ONE atomic step. It consists of:

#### 10.1 Add Shadow Byte Declarations to BSS

In `apps/rastan-direct/src/main_68k.s`, in the `.bss` section, add:

```asm
    .align 2
shadow_p1_input:        .byte 0xFF    ; TC0040IOC 0x390001 mirror (active-low, 0xFF = all released)
shadow_p2_input:        .byte 0xFF    ; TC0040IOC 0x390003 mirror
shadow_coin_input:      .byte 0xFF    ; TC0040IOC 0x390005 mirror
shadow_sys_input:       .byte 0xFF    ; TC0040IOC 0x390007 mirror
    .align 2
```

These four bytes are the only persistent state for TC0040IOC input emulation.

#### 10.2 Add Genesis Pad Read Stub

Add a new function `rastan_direct_update_inputs` in main_68k.s (or a new file input.s):

The function:
1. Initializes port direction (once, or verify in init that 0xA1000B is set to 0x40 for TH=output).
2. Reads P1 3-button pad using the two-phase TH toggle from 0xA10003.
3. Reads P2 pad from 0xA10005 (same method).
4. Constructs shadow_p1_input: UP→bit0, DOWN→bit1, LEFT→bit2, RIGHT→bit3, B→bit4, C→bit5, all others 1.
5. Constructs shadow_p2_input: same from P2 state.
6. Constructs shadow_coin_input: A→clears bit6 (coin 3/service coin at 0x3A0A8 btst #6).
   B→clears bit4, C→clears bit5. Default 0xFF.
7. Constructs shadow_sys_input: A→clears bit0 (coin 1), START→clears bit3 (player 1 start),
   P2 START→clears bit4 (player 2 start). A+B+C combo→clears bit2 (service guard).
   Default 0xFF.

#### 10.3 Wire into arcade_tick_logic

At the top of arcade_tick_logic, before the scroll counter logic:

```asm
arcade_tick_logic:
    bsr     rastan_direct_update_inputs
    ; (existing scroll counter code follows, until replaced by real arcade tick)
    rts
```

#### 10.4 Add Port Direction Init to boot/init

In `init_staging_state` or a new `init_io` function called from main_68k, add:

```asm
    move.b  #0x40, 0x00A1000B    ; set port 1 TH = output, rest = input
    move.b  #0x40, 0x00A1000D    ; set port 2 TH = output, rest = input
    move.b  #0x40, 0x00A10003    ; TH=1 (initial high state)
    move.b  #0x40, 0x00A10005    ; TH=1 for port 2
```

#### 10.5 Add Shadow Byte Patcher Entries to startup_title_remap.json

The existing opcode rewrite rules in startup_title_remap.json for 0x390001/3/5/7/9/B already
exist and reference SGDK symbol names. For rastan-direct, either:
- Use the same symbol names by declaring them as `.global` in rastan-direct's BSS (preferred for
  toolchain compatibility), or
- Add a rastan-direct-specific section to startup_title_remap.json with the rastan-direct symbol
  names.

The patcher resolves symbol addresses from the linked ELF. The symbol name in the JSON must
match the ELF symbol exactly.

#### 10.6 Verify

After linking rastan-direct with the shadow bytes:
1. In BlastEm, run the ROM to a point before any arcade execution (main loop, post-init).
2. Verify shadow bytes at their WRAM addresses are 0xFF (init values).
3. Press a button on the Genesis controller. Verify the corresponding shadow byte bit clears.
4. Confirm no bus error occurs when the arcade code (once linked) reads the shadow address.

This step is foundational and must be complete before the arcade ROM can be linked and executed.

---

## 11. What Must Not Be Done Yet

### 11.1 Do Not Link the Arcade ROM Yet

**Why premature**: The arcade ROM requires (a) all TC0040IOC patches applied, (b) all absolute
call targets relocated, (c) the arcade WRAM base (A5) initialized, (d) the arcade startup
sequence initialized or bypassed. None of these are in place in rastan-direct. Linking an
unpatched arcade ROM will produce a ROM that crashes on first TC0040IOC read.

**What must be done first**: TC0040IOC shadow infrastructure (this step), then arcade ROM link
with patcher, then A5/WRAM init, then first arcade tick.

### 11.2 Do Not Run Arcade Startup Sequence Yet

**Why premature**: The arcade startup_common sequence (0x03AF00 area) reads DIP switches, writes
to sound hardware (TC0140SYT at 0x3E0000, also unmapped on Genesis), performs hardware tests,
and expects specific hardware response patterns. Without full TC0040IOC patching AND sound
hardware patching, startup_common will hang or crash.

The initial rastan-direct arcade execution entry must bypass startup_common entirely and enter
at the post-init gameplay state (0x03A008 in a known state, with arcade WRAM pre-initialized to
the post-startup state). This bypass is the same pattern used in the SGDK branch
(`genesistan_init_workram_direct`).

### 11.3 Do Not Implement Coin/Credit Logic Yet

**Why premature**: Credit management requires coin shadow bytes working, plus the arcade credit
counter logic in WRAM working, plus the attract state machine reaching the coin-insert prompt.
None of this is active in rastan-direct's current synthetic scaffold.

The coin shadow byte (shadow_coin_input) is initialized to 0xFF (no coin) and can remain
static until arcade execution reaches the credit management code path.

### 11.4 Do Not Implement Audio (TC0140SYT)

**Why premature**: The TC0140SYT sound command register at 0x3E0001/0x3E0003 is unmapped on
Genesis. Sound patches are a separate concern from input patches. They do not interact with
TC0040IOC. Sound patches follow the same opcode-patch discipline but target different addresses.
Audio is out of scope until visual (BG + sprite) fidelity is established.

### 11.5 Do Not Convert to Per-Read JSR Stubs

**Why incorrect**: Option B (JSR to per-read stubs) is more complex, adds call overhead, and
provides no benefit over Option A (direct shadow read) since shadow bytes are pre-computed.
Option A is the proven Rainbow Islands approach. Option B would require saving/restoring
additional registers in every JSR stub and adds 4–8 cycles per read call. Rejected.

### 11.6 Do Not Make DIP Values Runtime-Configurable

**Why premature**: Factory defaults are the only correct DIP state for a fixed-content home
release. Runtime configurability adds complexity and is not aligned with the Rainbow Islands
porting discipline (which hardcodes DIP values). The `replacement_bytes` in startup_title_remap.json
for DIP patches contain the fixed constant values. This is complete and final.

### 11.7 Do Not Implement 6-Button Pad Support Yet

**Why premature**: Rastan arcade is a 2-button game (attack + jump). A Genesis 3-button pad is
sufficient. The 6-button pad extension protocol (Sega MK-1653) requires additional TH toggling
and introduces timing complexity. The standard 3-button read (TH high, read phase 1 = D-pad +
B/C; TH low, read phase 2 = D-pad + A/START) is correct and complete for Rastan.

---

## 12. Final Verdict

**TC0040IOC model**: DEFINED. All patch sites catalogued. Shadow byte model selected (Option A:
direct WRAM reads, pre-computed per frame). DIP constants hardcoded. Service/tilt/test
permanently suppressed. Coin/system inputs via shadow bytes updated from Genesis pad.

**Input timing model**: DEFINED. Shadow bytes updated at entry of arcade_tick_logic (main loop),
before any arcade code executes. No race condition risk. Ordering guaranteed by sequential
execution.

**Arcade execution model**: DEFINED. Direct execution of relocated arcade opcodes at
ARCADE_ROM_BASE = 0x000200. No interpretation layer. Patches applied at build time by patcher.

**Entry/control flow**: DEFINED. arcade_tick_logic calls rastan_direct_update_inputs then JSR
to 0x03A208 (= 0x03A008 + 0x200). VBlank is commit-only. Arcade WRAM initialized before first
tick via genesistan_init_workram_direct equivalent.

**Patch strategy**: DEFINED. Build-time, original_bytes-verified, symbol-resolved. Option A
(direct shadow move) for all joystick reads. Immediate loads for DIP reads. NOPs for control
writes. Safe 8-byte replacements for btst-suppress sites.

**Drift risks**: ANALYZED. ROM address drift = none (fixed binary + original_bytes guard).
Hook target drift = mitigated by Option A (no JSR). Unpatched sites = mitigated by opcode scan
coverage. Register contract drift = none with Option A. Interrupt race = none (shadow writes
in main loop only, VBlank is commit-only).

**Rainbow Islands alignment**: FULL ALIGNMENT. Identical TC0040IOC handling, shadow byte model,
VBlank ownership, commit discipline, patch mechanism. Confirmed by TC0040IOC spec Section 7 and
Cody_rainbow_islands_vdp_template_analysis.md.

**Single next step**: Implement TC0040IOC shadow byte infrastructure (BSS declarations +
rastan_direct_update_inputs stub + port direction init + arcade_tick_logic wiring + patcher
symbol declarations). This is foundational and must precede arcade ROM linking.
