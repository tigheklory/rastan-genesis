# Proposal: No-SGDK Direct Execution Branch

## 1. Overview

This document proposes a new branch of the Rastan Genesis port that removes SGDK entirely and replaces it with a minimal hand-written boot stub, a direct opcode-patch execution model, and a VBlank handler written purely in assembly. There is no launcher, no DIP switch menu, and no C runtime. Factory DIP defaults are encoded as ROM constants. The game executes immediately on power-on.

The architectural model is **Rainbow Islands Genesis** (Taito 1990), which runs on hardware virtually identical to Rastan Arcade (same TC0040IOC I/O chip, same PC080SN tilemap chip, same PC090OJ sprite chip) and makes the arcade-to-Genesis transition using only opcode patches and a hand-written VBlank handler with no OS or SDK.

---

## 2. Why the Current Architecture Has a Structural Problem

### 2.1 The SGDK Boundary Is Not Clean

The current project uses SGDK as the Genesis runtime host. The VBlank handler (`_VINT` in `sega.s`) contains a gate:

```asm
_VINT:
    tst.w   arcade_vblank_active
    bne     _VINT_arcade_mode       ← arcade path
    [... full SGDK dispatch ...]    ← SGDK path
```

While the gate correctly separates the two paths at runtime, SGDK still:
- Defines the vector table layout
- Provides the boot entry point (`_start_entry`) and TMSS sequence
- Provides `JOY_update`, which is still called from `_VINT_arcade_mode`
- Holds the symbol definitions for `vtimer`, `intTrace`, `VBlankProcess`, `vintCB`, `task_lock`, `task_regs`, `intCB`, `eintCB`, `hintCaller`
- Controls the ROM header format and security code write
- Is linked into the binary even when arcade mode is active

The SGDK VBlank path (vtimer, XGM, BMP, vintCB) is reachable on every interrupt before `arcade_vblank_active` is set. During the launcher phase, SGDK's DMA, palette fade, and task scheduler are active. Once the arcade game starts, SGDK is bypassed but remains linked, consuming ROM space, WRAM, and adding symbol-level coupling that constrains what the arcade path can do.

### 2.2 C Code Is Being Used to Implement Video Routines

The current implementation routes VDP work through C functions:
- `genesistan_render_sprites_vdp()` — uses `VDP_setSpriteFull()`, `VDP_updateSprites(DMA)`, `PAL_setColor()`
- `genesistan_scroll_commit_vdp()` — C function with direct port writes
- `genesistan_debug_fg_proof()` — C function writing FG buffer
- `refresh_frontend_sprite_palettes_mapped()` — C function calling `PAL_setColor()` × 64

These C functions call SGDK API (`VDP_*`, `PAL_*`) which writes to SGDK's internal shadow state. Those shadows are never committed to hardware in arcade mode because SGDK's VBlank task (`VBlankProcess = 0`) is disabled. The result is a split system: SGDK shadow state diverges from hardware state every frame, and the two subsystems (SGDK internals, arcade hardware writes) are fighting over the same VDP.

### 2.3 The Launcher Adds Complexity That Blocks Direct Boot

The launcher (DIP switch menu, graphics test, sound test) is ~1,500 lines of C that:
- Requires SGDK for VDP text rendering, DMA, and palette management
- Holds arcade execution hostage until the user clicks "Start Rastan"
- Creates a one-way transition from SGDK mode to arcade mode that requires `force_clean_vram_init()` to undo SGDK's VDP state
- Makes it impossible to reason about the VDP state at arcade start without tracing the full launcher teardown sequence

---

## 3. The Reference Model: Rainbow Islands Genesis

Rainbow Islands (Taito 1990) runs on hardware that is architecturally identical to Rastan Arcade:

| Hardware | Rastan Arcade | Rainbow Islands Arcade | Rainbow Islands Genesis |
|----------|--------------|----------------------|------------------------|
| CPU | 68000 | 68000 | 68000 |
| Tilemap | PC080SN | TC0100SCN | Hand-translated to VDP Plane A/B |
| Sprites | PC090OJ | PC090OJ | SAT WRAM staging → DMA |
| I/O | TC0040IOC | TC0040IOC | DIP reads → hardcoded constants |
| Sound | YM2151 + MSM5205 | YM2151 + MSM5205 | Z80 + YM2612 |
| SDK/OS | None | None | **None** |

Rainbow Islands Genesis makes the transition with:

1. **No OS or SDK** — the Genesis binary has a handwritten boot stub (~50 instructions) followed directly by arcade code
2. **VBlank handler is a pure commit handler** — game logic runs in the main loop (polled via frame counter); VBlank only commits staged WRAM buffers to VDP
3. **All arcade hardware reads replaced by ROM constants or WRAM mirrors** — TC0040IOC, PC080SN, PC090OJ register reads replaced at the opcode level
4. **All arcade hardware writes replaced by WRAM writes** — tile writes go to a WRAM staging buffer; VBlank handler DMA's the buffer to VRAM
5. **DIP switches are hardcoded** — no physical switches; the I/O read opcodes are replaced with `move.w #<constant>, d0`

This is exactly the model the no-SGDK branch should follow.

---

## 4. Proposed Architecture

### 4.1 Binary Structure

```
Genesis ROM layout (proposed no-SGDK branch):

0x000000  Vector table (68 vectors × 4 bytes = 0x110 bytes)
           ├── 0x000000: Stack pointer
           ├── 0x000004: _Entry_Point
           ├── 0x000070: HINT handler → _HINT_handler (RTE stub or H-count)
           ├── 0x000078: VINT handler → _VINT_handler (arcade commit handler)
           └── other vectors → _INT_stub (RTE)

0x000100  Sega ROM header (0x100 bytes, required for TMSS)
           ├── "SEGA MEGA DRIVE" identifier
           ├── "RASTAN" title
           ├── ROM range, RAM range, checksum
           └── I/O support byte

0x000200  Boot stub (pure assembly, ~50 instructions)
           ├── TMSS write (conditional on hardware version)
           ├── Z80 halt
           ├── VDP baseline register init (19 registers)
           ├── VRAM clear (full 64KB via CPU word fill)
           ├── CRAM clear (64 words)
           ├── VSRAM clear (40 words)
           ├── WRAM init (zero key structures)
           ├── DIP shadow init (load factory constants → workram)
           ├── Z80 sound driver upload
           └── JMP to arcade ROM entry point

0x000400  Arcade ROM copy (whole maincpu relocated)
           Source: 0x000000–0x05FFFF
           Dest:   0x000400–0x05FFFF (shifted by 0x400 from current 0x200)

0x200000  Genesis-side assembly stubs
           ├── _VINT_handler         (commit handler)
           ├── _HINT_handler         (RTE or scanline counter)
           ├── Input read stub       (Genesis pad → arcade shadow)
           ├── WRAM staging buffers
           │   ├── bg_tilemap_buffer  (2048 words, VRAM 0xC000 mirror)
           │   ├── fg_tilemap_buffer  (2048 words, VRAM 0xE000 mirror)
           │   ├── sat_buffer         (SAT entries, 640 bytes)
           │   └── palette_buffer     (64 words, xBGR-444)
           └── Commit routines
               ├── commit_tilemap_bg  (staged buffer → VRAM 0xC000)
               ├── commit_tilemap_fg  (staged buffer → VRAM 0xE000)
               ├── commit_sat         (staged buffer → VDP SAT via DMA)
               └── commit_palette     (staged buffer → CRAM)
```

### 4.2 Boot Stub (replaces all of SGDK)

The boot stub replaces `sega.s` entirely. It has no SGDK dependencies. It:

```asm
_Entry_Point:
    move    #0x2700, %sr            /* disable all interrupts */
    
    /* Z80 halt */
    move.w  #0x0100, 0xA11100
    move.w  #0x0100, 0xA11200
    
    /* TMSS (conditional) */
    move.b  0xA10001, %d0
    andi.b  #0x0F, %d0
    beq.s   .Lno_tmss
    move.l  #0x53454741, 0xA14000   /* "SEGA" */
.Lno_tmss:

    /* VDP init — 19 registers, hardcoded for arcade layout */
    lea     0xC00004, %a0
    move.w  #0x8004, (%a0)          /* reg 0: no HInt */
    move.w  #0x8134, (%a0)          /* reg 1: display OFF */
    move.w  #0x8238, (%a0)          /* reg 2: Plane A = 0xE000 */
    move.w  #0x8334, (%a0)          /* reg 3: Window = 0xD000 */
    move.w  #0x8406, (%a0)          /* reg 4: Plane B = 0xC000 */
    move.w  #0x857C, (%a0)          /* reg 5: SAT = 0xF800 */
    move.w  #0x8700, (%a0)          /* reg 7: bg color */
    move.w  #0x8AFF, (%a0)          /* reg 10: HInt counter (disabled) */
    move.w  #0x8B00, (%a0)          /* reg 11: full HScroll, full VScroll */
    move.w  #0x8C81, (%a0)          /* reg 12: H40, no shadow */
    move.w  #0x8D3C, (%a0)          /* reg 13: HScroll table = 0xF000 */
    move.w  #0x8F02, (%a0)          /* reg 15: auto-increment = 2 */
    move.w  #0x9001, (%a0)          /* reg 16: 64×32 plane */
    move.w  #0x9180, (%a0)          /* reg 17: Window H OFF */
    move.w  #0x9280, (%a0)          /* reg 18: Window V OFF */
    
    /* Clear VRAM */
    move.l  #0x40000000, (%a0)
    lea     0xC00000, %a1
    move.w  #32767, %d0
.Lclear_vram:
    move.w  #0, (%a1)
    dbra    %d0, .Lclear_vram
    
    /* Clear CRAM */
    move.l  #0xC0000000, (%a0)
    move.w  #63, %d0
.Lclear_cram:
    move.w  #0, (%a1)
    dbra    %d0, .Lclear_cram
    
    /* Init DIP shadow in workram (factory defaults, ROM constants) */
    move.w  #FACTORY_DIP1_INVERTED, genesistan_arcade_workram_words+0x18
    move.w  #FACTORY_DIP2_INVERTED, genesistan_arcade_workram_words+0x1C
    
    /* Upload Z80 sound driver */
    [... Z80 driver upload sequence ...]
    
    /* Enable VBlank, unmask level 6 */
    move    #0x2000, %sr
    
    /* Jump directly into arcade startup */
    lea     genesistan_arcade_workram_words, %a5
    jmp     (0x03AE86 + ARCADE_ROM_BASE)    /* arcade startup_common */
```

**No SGDK symbols. No C runtime. No task scheduler. No vtimer. No XGM. No DMA queue.**

### 4.3 VBlank Handler (pure assembly, commit-only)

Modeled directly on Rainbow Islands Genesis:

```asm
_VINT_handler:
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    
    /* Acknowledge VBlank (read VDP status) */
    move.w  0xC00004, %d0
    
    /* Request Z80 bus */
    move.w  #0x0100, 0xA11100
    
    /* Display OFF */
    move.w  #0x8134, 0xC00004
    
    /* Commit tiles if flagged */
    tst.w   vblank_flag_tiles
    beq.s   .Lno_tiles
    bsr     commit_tilemap_bg
    bsr     commit_tilemap_fg
    clr.w   vblank_flag_tiles
.Lno_tiles:

    /* Commit SAT (every frame) */
    bsr     commit_sat_dma
    
    /* Commit palette if flagged */
    tst.w   vblank_flag_palette
    beq.s   .Lno_palette
    bsr     commit_palette
    clr.w   vblank_flag_palette
.Lno_palette:

    /* Display ON */
    move.w  #0x8174, 0xC00004
    
    /* Commit scroll (after display on, VSRAM is safe) */
    bsr     commit_scroll
    
    /* Release Z80 bus */
    move.w  #0, 0xA11100
    
    /* Increment frame counter */
    addq.l  #1, vblank_frame_counter
    
    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rte
```

**No game logic in VBlank. No arcade tick. No SGDK. No JOY_update call.**

### 4.4 Game Logic Execution Model

The arcade code runs in the **main loop**, frame-synced by polling `vblank_frame_counter`:

```asm
_main_loop:
    /* Wait for next VBlank */
    move.l  vblank_frame_counter, %d0
.Lwait_vblank:
    cmp.l   vblank_frame_counter, %d0
    beq.s   .Lwait_vblank
    
    /* Run one arcade tick */
    lea     genesistan_arcade_workram_words, %a5
    jsr     (0x03A008 + ARCADE_ROM_BASE)    /* arcade main tick */
    
    bra     _main_loop
```

This is exactly the Rainbow Islands Genesis model. The entire arcade tick runs with display ON, outside interrupt context. Hardware register reads fired by the arcade code hit opcode patches instead of real hardware.

### 4.5 DIP Switch Handling (ROM Constants, No Hardware Read)

The arcade ROM reads DIP switches from `0x390009` and `0x39000B`. In the no-SGDK branch these reads are patched at opcode level to load ROM constants:

```
Original arcade code at 0x03AF7A:
    1019 0039 0009   moveb 0x390009, %d0     ; read DIP bank 1 from TC0040IOC
    4600             notb  %d0               ; invert active-low
    3AC0             movew %d0, %a5@(24)     ; store inverted DIP1

Patch replacement:
    103C 0001        moveb #FACTORY_DIP1_VALUE, %d0    ; hardcoded value (active-high)
    3AC0             movew %d0, %a5@(24)
    4E71 4E71        nop nop                            ; pad to original size

Original arcade code at 0x03AF82:
    1039 000B        moveb 0x39000B, %d0     ; read DIP bank 2
    4600             notb  %d0
    3AC0             movew %d0, %a5@(28)

Patch replacement:
    103C 00XX        moveb #FACTORY_DIP2_VALUE, %d0
    3AC0             movew %d0, %a5@(28)
    4E71 4E71        nop nop
```

Factory defaults (derived from Rastan operator manual, active-high after inversion):

| Setting | Value | Decoded |
|---------|-------|---------|
| DIP1 active-high | 0x01 | Test=OFF, Flip=OFF, Demo sound=OFF, Coin=1C/1C |
| DIP2 active-high | 0x00 | Difficulty=Easy, Bonus=30k, Lives=3, Continue=OFF |

These constants are stored in the Genesis ROM binary and cannot be changed at runtime.

### 4.6 Opcode Patch System (Unchanged in Concept, Simplified in Execution)

The existing `startup_title_remap.json` patch system is retained with these changes:

| Patch category | Current branch | No-SGDK branch |
|----------------|---------------|----------------|
| TC0040IOC DIP reads | Runtime virtual DIP from C variables | ROM constant patches (no runtime read) |
| TC0040IOC coin/input reads | Hook to Genesis pad shadow | Hook to Genesis pad shadow (same) |
| PC080SN tilemap writes | Redirect to WRAM buffer via C hook | Redirect to WRAM buffer via assembly stub |
| PC090OJ sprite writes | Hook to WRAM SAT staging | Hook to WRAM SAT staging |
| PC080SN text writes | Hook to C function | Hook to pure assembly stub |
| YM2151 sound writes | Shadow + Z80 forwarding | Shadow + Z80 forwarding (same) |
| TC0040IOC control writes | Shadow registers | Shadow registers (same) |

The key change: every hook target that currently points to a C function (`genesistan_*_impl`, `refresh_frontend_sprite_palettes_mapped`, etc.) is replaced with a pure assembly equivalent. No C compiler, no `main()`, no `.bss` init by CRT0.

---

## 5. What Gets Removed

| Component | Current branch | No-SGDK branch |
|-----------|---------------|----------------|
| SGDK library | Linked (~200KB ROM) | **Removed** |
| `sega.s` (SGDK boot) | Full SGDK startup | **Replaced** with ~50-instruction stub |
| Launcher C code (`main.c`) | ~2,500 lines | **Removed entirely** |
| DIP switch menu | Interactive UI | **Removed** — factory constants in ROM |
| Graphics test | VDP tile viewer | **Removed** |
| Sound test | YM2612 test UI | **Removed** |
| SGDK VBlank path (vtimer, XGM, BMP) | Present, gated | **Removed** |
| C runtime (CRT0, `.bss` init) | Present | **Removed** |
| `JOY_update` in VBlank | Called every frame | **Removed** — input read patched to asm stub |
| `VDP_*` / `PAL_*` / `DMA_*` API | Used by sprite/palette hooks | **Removed** — all hooks become pure asm |
| `force_clean_vram_init()` | Called at arcade handoff | **Replaced** by boot stub (runs once at power-on) |
| `arcade_vblank_active` gate | Runtime flag | **Removed** — VBlank is always arcade mode |
| `apply_post_reset_test_palette()` | Diagnostic | **Removed** |
| All `genesistan_debug_*` functions | Diagnostic | **Removed** |

---

## 6. What Gets Kept

| Component | Notes |
|-----------|-------|
| `startup_title_remap.json` patch engine | Same patch infrastructure, new targets |
| `genesistan_arcade_workram_words` layout | Same workram map |
| `pc080sn_bg_buffer` / `pc080sn_fg_buffer` | Same WRAM staging buffers |
| `genesistan_palette_clcs` | Same palette staging buffer |
| SAT staging buffer | Same layout, now committed via DMA |
| Scroll staging (`staged_scroll_*`) | Same variables |
| `genesistan_pc080sn_commit_planes` body | Same inner loop, now called from asm VBlank |
| `genesistan_palette_commit_asm` body | Same conversion logic |
| All arcade ROM opcode patches | Same patch addresses, same mechanisms |
| Arcade ROM copy at `ARCADE_ROM_BASE` | Same binary blob, same relocation |

---

## 7. VDP Commit Model (Post-Change)

The commit model becomes strictly flag-triggered, matching Rainbow Islands:

| Subsystem | Staging location | VBlank commit trigger | Commit method |
|-----------|-----------------|----------------------|---------------|
| BG tilemap | `pc080sn_bg_buffer` (4096 bytes) | `vblank_flag_tiles != 0` | CPU word stream → VRAM 0xC000 |
| FG tilemap | `pc080sn_fg_buffer` (4096 bytes) | `vblank_flag_tiles != 0` | CPU word stream → VRAM 0xE000 |
| SAT | `sat_wram_buffer` (640 bytes) | Every frame | DMA → VDP SAT (0xF800) |
| Palette | `genesistan_palette_clcs` | `vblank_flag_palette != 0` | CPU word stream → CRAM |
| Scroll | `staged_scroll_*` | Every frame | 2 words → VSRAM (after display ON) |
| Tile DMA | ROM → VRAM | `vblank_flag_tile_dma != 0` | DMA from ROM range |

Hooks that currently write to VDP directly (scroll, sprites during arcade tick) instead:
- Set the appropriate staging buffer
- Set the appropriate flag
- Do not touch VDP at all

---

## 8. Input Handling

Current: `JOY_update` (SGDK) called from VBlank → SGDK shadow → `genesistan_refresh_arcade_inputs` → workram.

Proposed: Entirely self-contained input stub called from main loop (not VBlank):

```asm
_read_inputs:
    /* Read Genesis pad 1 */
    move.b  #0x40, 0xA10009         /* select high nibble */
    nop
    nop
    move.b  0xA10003, %d0           /* read buttons */
    
    /* Translate to arcade shadow layout */
    [bit mapping: B=attack, C=jump, A=coin, Start=start, D-pad=D-pad]
    
    move.b  %d0, genesistan_arcade_input_shadow
    rts
```

No SGDK. No shadow state management. Read once per main-loop frame before the arcade tick.

---

## 9. Z80 / Sound

The Z80 sound driver upload and communication stubs (`genesistan_sound_send_command`, `genesistan_sound_read_status`) are retained as assembly, identical to the current implementation. The Z80 bus coordination in VBlank (request at entry, release at exit, as Rainbow Islands does) is added. This is currently absent.

---

## 10. Branch Strategy

### Recommended approach: New directory tree under `apps/`

```
apps/
├── rastan/              ← current SGDK branch (preserved, not deleted)
│   ├── src/
│   │   ├── main.c
│   │   ├── boot/sega.s
│   │   └── startup_trampoline.s
│   └── Makefile
└── rastan-direct/       ← new no-SGDK branch
    ├── src/
    │   ├── boot.s           (replaces all of sega.s + main.c)
    │   ├── vblank.s         (commit handler)
    │   ├── input.s          (pad read stub)
    │   ├── commit.s         (tilemap/SAT/palette/scroll commit routines)
    │   ├── sound.s          (Z80 communication stubs)
    │   └── trampoline.s     (arcade ROM hooks — asm only)
    └── Makefile             (no SGDK dependency)
```

The current `apps/rastan/` branch is **preserved unchanged**. The new `apps/rastan-direct/` branch is developed in parallel. No existing files are modified.

### Build system change

Current: `make -C apps/rastan release` depends on SGDK toolchain at `tools/sgdk/`.

Proposed: `make -C apps/rastan-direct` uses only:
- `m68k-elf-as` (assembler)
- `m68k-elf-ld` (linker)
- `m68k-elf-objcopy` (binary extraction)
- Python `tools/postpatch_lenient.py` (same opcode patch application)

SGDK is not required to build `rastan-direct`. The linker script defines the ROM layout directly.

---

## 11. Implementation Phases

### Phase 1 — Boot stub + bare VBlank
- Write minimal `boot.s`: vector table, ROM header, TMSS, VDP init, VRAM clear, DIP constant init, JMP to arcade startup
- Write minimal `vblank.s`: register save/restore, display bracket, frame counter increment, RTE
- Confirm ROM boots to black screen without crashing on real hardware / BlastEm

### Phase 2 — Arcade ROM execution
- Copy/adapt `trampoline.s` from current `startup_trampoline.s`, remove all SGDK dependencies
- Apply same `startup_title_remap.json` patches
- Confirm arcade tick executes (workram activity visible in debugger)

### Phase 3 — DIP constant patches
- Add opcode patches for `0x390009` and `0x39000B` reads
- Confirm arcade startup_common completes without service-mode divergence

### Phase 4 — Tilemap commit
- Implement `commit_tilemap_bg` / `commit_tilemap_fg` in `commit.s`
- Implement flag-setting in tilemap hooks
- Confirm Plane A/B content visible on screen

### Phase 5 — SAT commit
- Implement `sat_wram_buffer` staging
- Implement `commit_sat_dma` (DMA from WRAM → VDP SAT)
- Confirm sprites visible

### Phase 6 — Palette commit
- Implement flag-triggered palette commit in `commit.s`
- Confirm correct colors

### Phase 7 — Scroll + Z80
- Implement VSRAM write in `commit.s`
- Add Z80 bus coordination to VBlank
- Confirm scrolling and audio

---

## 12. Expected Benefits

| Problem | Current branch | No-SGDK branch |
|---------|---------------|----------------|
| SGDK/arcade VDP state conflict | Present — SGDK shadow vs hardware diverge | **Eliminated** — no SGDK shadow state |
| VBlank budget overrun risk | High — full game tick + 6.4ms streaming | **Low** — commit only, game tick in main loop |
| C code calling VDP APIs | Yes — PAL_setColor, VDP_updateSprites | **Eliminated** — all VDP writes are direct asm |
| Launcher teardown complexity | Yes — `force_clean_vram_init` + multi-step handoff | **Eliminated** — boot stub runs once |
| DIP switch UI complexity | Yes — 1,500 lines of C | **Eliminated** — ROM constants |
| Diagnostic debt contaminating builds | Yes — 11 active items | **Eliminated** — clean codebase |
| Architecture matches reference (Rainbow Islands) | Partial | **Full** |

---

## 13. What This Does NOT Change

- The arcade ROM binary content is identical
- The opcode patch addresses and mechanisms are identical
- The WRAM buffer layout is identical
- The `startup_title_remap.json` patch definitions are compatible (new targets, same addresses)
- The Genesis hardware VDP layout (Plane A=0xE000, Plane B=0xC000, SAT=0xF800) is identical
- The `dist/Rastan_NNN.bin` output format and build numbering convention is preserved

---

## 14. Final Verdict

The no-SGDK branch is architecturally sound and has a clear reference model in Rainbow Islands Genesis. It eliminates the root cause of the SGDK/arcade VDP interference that has driven the diagnostic work since Build 313. The implementation is achievable in pure assembly with no new toolchain dependencies beyond what is already present (`m68k-elf-as`, `m68k-elf-ld`). The current SGDK branch is preserved as-is and can continue to be maintained independently.

The proposed branch name: **`rastan-direct`**.
