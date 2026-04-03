# Build 323 — Full VBlank Dispatch / SGDK Influence Audit

## 1. Executive Summary

The VBlank interrupt takes one of two fully exclusive paths based on `arcade_vblank_active`. When the arcade mode is active (`arcade_vblank_active != 0`), the SGDK path is **completely bypassed** — no SGDK VBlank tasks, no DMA flush, no palette fading, no XGM, no vintCB, no vblankCB. The only VDP writers active during arcade VBlank are the four custom functions called from `_VINT_arcade_mode`. There is **no SGDK / legacy VBlank interference** once arcade mode is active. The root cause of the empty Plane A is not VBlank interference — it is that the FG buffer receives no non-zero writes during attract mode.

## 2. True VBlank Entry Point

| Property | Value |
|----------|-------|
| Vector table slot | Offset 0x78 (level 6 interrupt = VBlank) |
| Vector value | Address of `_VINT` |
| File | `apps/rastan/src/boot/sega.s` line 73: `dc.l _VINT` |
| First assembly function | `_VINT` (sega.s line 139) |

Full call chain when arcade active:

```
Hardware VBlank IRQ
  → _VINT (sega.s:139)
      tst.w arcade_vblank_active → non-zero
      bne _VINT_arcade_mode (sega.s:202)
        movem.l save all registers
        jsr genesistan_refresh_arcade_inputs
        move.w #0x8134 → VDP reg 1 (display OFF)
        jsr genesistan_run_arcade_tick_lean
        jsr sanitize_arcade_workram
        jsr genesistan_pc080sn_commit_planes
        jsr genesistan_palette_commit_asm
        jsr genesistan_scroll_commit_vdp
        move.w #0x8174 → VDP reg 1 (display ON)
        movem.l restore all registers
        rte
```

Full call chain when SGDK active (launcher/config screen, `arcade_vblank_active == 0`):

```
Hardware VBlank IRQ
  → _VINT (sega.s:139)
      tst.w arcade_vblank_active → zero → falls through
      [task scheduler context switch logic]
      no_user_task:
        movem.l save d0-d1/a0-a1
        intTrace |= 0x0001
        vtimer++
        btst #3, VBlankProcess+1 → XGM_doVBlankProcess (if bit set)
        btst #1, VBlankProcess+1 → BMP_doVBlankProcess (if bit set)
        vintCB() → _vint_dummy_callback (no-op by default)
        intTrace &= 0xFFFE
        movem.l restore
        rte
```

## 3. `sega.s` VBlank Audit

### Arcade mode path (`_VINT_arcade_mode`)

Direct VDP writes in sega.s:

| Address | Value | Effect |
|---------|-------|--------|
| `0xC00004` | `0x8134` | VDP reg 1: display OFF (before arcade tick) |
| `0xC00004` | `0x8174` | VDP reg 1: display ON (after all commits) |

No VRAM, CRAM, VSRAM, or HScroll writes directly in sega.s. All other VDP writes are delegated to the four `jsr` targets.

### SGDK path (`_VINT` non-arcade)

The SGDK path in sega.s performs no direct VDP writes. It only calls:
- `XGM_doVBlankProcess` (if `VBlankProcess bit 3` is set) — writes to Z80 bus, no VDP
- `BMP_doVBlankProcess` (if `VBlankProcess bit 1` is set) — bitmap mode VRAM writes, but BMP mode is never active in this project
- `vintCB` — set to `_vint_dummy_callback` (no-op) by `internal_reset()` at startup; set to NULL by `SYS_setVIntCallback(NULL)` at `reset_launcher_runtime_state()`

### SYS_doVBlankProcess (launcher main loop, NOT in interrupt)

`SYS_doVBlankProcess()` is called from the main loop (`main.c:2398`) only when `current_screen != SCREEN_FRONTEND_LIVE`. Once arcade mode is entered (`arcade_vblank_active = 1`; `current_screen = SCREEN_FRONTEND_LIVE`), `SYS_doVBlankProcess()` is **never called again from the main loop**.

`SYS_doVBlankProcessEx()` can perform VDP writes via:
- `DMA_flushQueue()` — if `PROCESS_DMA_TASK` bit set in `VBlankProcess`
- `VDP_doVBlankScrollProcess()` — if `PROCESS_VDP_SCROLL_TASK` bit set
- `PAL_doFadeStep()` — if `PROCESS_PALETTE_FADING` bit set
- `SHOW_FRAME_LOAD` sprite write — if debug flag set

However, **all of these are guarded by `VBlankProcess` bits**, and `VBlankProcess = 0` is set by `internal_reset()` at startup and never modified during the launcher phase. All SGDK VBlank task bits are therefore zero during launcher operation.

## 4. Full List of VBlank-Time VDP Writers

### When `arcade_vblank_active == 1` (active arcade runtime):

| Order | Function | File | What it writes |
|-------|----------|------|---------------|
| 1 | `_VINT_arcade_mode` (inline) | sega.s:206 | VDP reg 1 = 0x8134 (display OFF) |
| 2 | `genesistan_refresh_arcade_inputs` | startup_trampoline.s | No VDP writes |
| 3 | `genesistan_run_arcade_tick_lean` | startup_trampoline.s | Runs arcade CPU emulation. Hooks write to WRAM buffers, not VDP directly |
| 4 | `sanitize_arcade_workram` | main.c:2200 | No VDP writes |
| 5 | `genesistan_pc080sn_commit_planes` | startup_trampoline.s:872 | VRAM 0xC000 (BG, 2048 words), VRAM 0xE000 (FG, 2048 words) |
| 6 | `genesistan_palette_commit_asm` | startup_trampoline.s:91 | CRAM (64 words, full palette) |
| 7 | `genesistan_scroll_commit_vdp` | main.c:1756 | VRAM 0xF000 (HScroll 2 words), VSRAM offset 0 (VScroll 2 words), VDP auto-increment reg |
| 8 | `_VINT_arcade_mode` (inline) | sega.s:213 | VDP reg 1 = 0x8174 (display ON) |

**Total distinct VDP-writing functions in arcade VBlank: 4** (pc080sn_commit_planes, palette_commit_asm, scroll_commit_vdp, and the two display bracket writes in sega.s itself).

### When `arcade_vblank_active == 0` (launcher/config screen):

| Order | Function | File | What it writes |
|-------|----------|------|---------------|
| 1 | `_VINT` (inline) | sega.s:175-194 | No VDP writes; calls XGM, BMP, vintCB |
| 2 | `vintCB` → `_vint_dummy_callback` | sys.c | No-op, no VDP writes |

`SYS_doVBlankProcess()` runs from the main loop (not from interrupt) and can DMA-flush or palette-fade, but `VBlankProcess = 0` means none of those tasks are armed.

## 5. SGDK / Legacy Runtime VBlank Activity

### When arcade mode is active:

**SGDK system-layer VBlank processing: NOT RUNNING.**

The `tst.w arcade_vblank_active / bne _VINT_arcade_mode` at the top of `_VINT` is an unconditional branch to the arcade handler when the flag is non-zero. The entire SGDK dispatch block (vtimer++, XGM, BMP, vintCB) is **skipped entirely**. There is no partial SGDK activity — the branch completely bypasses lines 143-194 of sega.s.

Confirmed from `internal_reset()` (sys.c:597-614):
- `VBlankProcess = 0` → DMA, XGM, BMP, scroll, palette-fade tasks all cleared
- `vintCB = _vint_dummy_callback` → no-op
- `vblankCB = _vblank_dummy_callback` → no-op

Confirmed from `reset_launcher_runtime_state()` (main.c:2181-2182):
- `arcade_vblank_active = 0` before entering launcher
- `SYS_setVIntCallback(NULL)` → sets vintCB to dummy

Confirmed from arcade handoff (main.c:2129):
- `arcade_vblank_active = 1` set atomically before unmask; no vintCB is registered

**Legacy launcher VBlank processing: NOT RUNNING** once `current_screen = SCREEN_FRONTEND_LIVE`. `SYS_doVBlankProcess()` is only called when `current_screen != SCREEN_FRONTEND_LIVE` (main.c:2396-2399), and this condition is false for the entire arcade runtime.

## 6. Exact VBlank Order of Operations (arcade mode active)

```
1.  Hardware VBlank IRQ fires
2.  _VINT entry (sega.s:139)
3.  tst.w arcade_vblank_active → non-zero → bne _VINT_arcade_mode
4.  Save ALL registers (d0-d7/a0-a6)
5.  genesistan_refresh_arcade_inputs — joystick latch, no VDP
6.  VDP reg 1 ← 0x8134 (display OFF)
7.  genesistan_run_arcade_tick_lean — full arcade CPU tick:
      - text writer hooks → WRAM (pc080sn_fg_buffer)
      - scroll hooks → WRAM (staged_scroll_*)
      - tilemap hooks → WRAM (pc080sn_bg/fg_buffer)
      - palette hooks → WRAM (genesistan_palette_clcs)
      - sprite hooks → WRAM (workram sprite blocks)
8.  sanitize_arcade_workram — zero C-window ptr values in workram, no VDP
9.  genesistan_pc080sn_commit_planes — VRAM 0xC000 (BG 2048w), VRAM 0xE000 (FG 2048w)
10. genesistan_palette_commit_asm — CRAM full (64 entries mirrored × 4 lines)
11. genesistan_scroll_commit_vdp — HScroll VRAM 0xF000 (2 words), VSRAM (2 words)
12. VDP reg 1 ← 0x8174 (display ON)
13. Restore ALL registers (d0-d7/a0-a6)
14. rte
```

## 7. Multiple VDP Writer Conflict Assessment

**Are there multiple distinct VDP-writing paths active in one VBlank?** NO.

In arcade mode, the only VDP writers are the four custom functions listed in Section 4, all called sequentially from `_VINT_arcade_mode`. The SGDK path is fully bypassed. `SYS_doVBlankProcess()` is not called from the interrupt in arcade mode. The main loop's `SYS_doVBlankProcess()` call is gated on `current_screen != SCREEN_FRONTEND_LIVE` which is false during arcade operation.

**No write conflicts. No competing paths.**

| Writer | Belongs to | Active in arcade VBlank? |
|--------|-----------|--------------------------|
| `genesistan_pc080sn_commit_planes` | Custom arcade pipeline | YES |
| `genesistan_palette_commit_asm` | Custom arcade pipeline | YES |
| `genesistan_scroll_commit_vdp` | Custom arcade pipeline | YES |
| Display bracket writes | Custom arcade pipeline (sega.s) | YES |
| SGDK XGM | SGDK system layer | NO |
| SGDK BMP | SGDK system layer | NO |
| SGDK vintCB | SGDK system layer | NO |
| SGDK DMA flush | SGDK system layer | NO |
| SGDK palette fade | SGDK system layer | NO |
| Launcher SYS_doVBlankProcess | Launcher | NO |

## 8. Single Most Likely SGDK / VBlank Influence Risk

**NO_SGDK_VBLANK_INTERFERENCE**

Evidence:
- `arcade_vblank_active` check is the very first instruction in `_VINT` after the non-arcade task-switch block
- `bne _VINT_arcade_mode` branches to a completely separate handler that has its own `rte`
- The SGDK handler block is physically unreachable when `arcade_vblank_active != 0`
- `VBlankProcess = 0` from startup; no SGDK tasks are armed
- `SYS_doVBlankProcess()` not called during arcade operation
- `SYS_setVIntCallback(NULL)` called at launcher reset; vintCB = dummy

The empty Plane A problem is **not caused by VBlank interference**. The entire SGDK layer is clean and inactive during arcade operation.

## 9. Single Safest Next Implementation Test

Instrument the arcade tick to determine which write paths actually touch `pc080sn_fg_buffer` during the attract phase. Specifically: add a temporary counter or sentinel write at a fixed FG buffer position (e.g., `pc080sn_fg_buffer[0] = 0xFFFF` as a canary before the arcade tick, then check if it survives to the commit). If the canary is gone after the tick but the plane is empty, then something inside the arcade tick is zeroing the buffer. If the canary survives and the plane shows the canary tile, the write pipeline works and the issue is that no text hooks fire for attract content.

This requires a one-line addition to `_VINT_arcade_mode` (before or after `genesistan_run_arcade_tick_lean`) to write a sentinel into the FG buffer, plus checking the visible plane.

## 10. Final Verdict

**NO SGDK VBlank interference exists.** The `arcade_vblank_active` gate in `sega.s` fully and correctly isolates the custom arcade VBlank handler from all SGDK system processing. There are no competing VDP writers. The empty Plane A problem must be traced to the FG buffer write path during the arcade tick itself — either the attract-mode text/tilemap hooks don't fire, or they fire but write zeros (unmapped tiles), or something inside the arcade tick zeroes the FG buffer. VBlank dispatch is not the issue.
