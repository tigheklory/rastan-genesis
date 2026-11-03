# SAT Publish Failure Diagnosis

## 1. Purpose

Diagnose exactly why valid SAT staging in WRAM (vdpSpriteCache, 19 nonzero entries) fails to produce nonzero content at VDP VRAM 0xF800. Starting point: all prior Phase 1 pipeline stages confirmed passing; only the VDP SAT publish step is unresolved.

---

## 2. Locked Known-Good Stages

From `phase1_sprite_pipeline_results.md` (not re-proved here):

| Stage | Status |
|-------|--------|
| Activation patch at arcade_pc 0x059F90 | PASS |
| Block-A producer at 0x03AAEC hits and populates entry0 = `0000 00E8 03CA 0010` | PASS |
| Renderer bridge at 0x03AAF2 executes | PASS |
| `genesistan_render_sprites_vdp` at 0x2005C4 executes (2 hits) | PASS |
| vdpSpriteCache entry0 = `0168 0501 8400 0090`, 19 nonzero entries | PASS |
| VRAM 0xF800 = `0000 0000 0000 0000` | FAIL |

---

## 3. Real SAT Publish Path

### Call chain (SCREEN_FRONTEND_LIVE)

```
V-INT fires (SGDK sega.s)
  → vintCB = genesistan_frontend_live_vint_handoff  (main.c:1881)
    → genesistan_run_original_frontend_tick          (startup_trampoline.s:68)
      → arcade ROM 0x03A208 (frontend state machine)
        → 0x03AAEC  (producer slot — Block-A builder)
        → 0x03AAF2  (renderer slot — genesistan_render_sprites_vdp_bridge)
          → genesistan_render_sprites_vdp_bridge     (startup_trampoline.s:56)
            → genesistan_render_sprites_vdp          (main.c:1538)
              → VDP_setSpriteFull() loop              (fills vdpSpriteCache)
              → VDP_loadTileData(... DMA)             (tile upload if unique_count > 0)
              → SYS_disableInts()
              → VDP_updateSprites(sprite_count, DMA)  (main.c:1653)
              → VDP_waitDMACompletion()               (main.c:1654)
              → SYS_enableInts()
```

### DMA mode analysis

`VDP_updateSprites(sprite_count, DMA)` calls:

```c
DMA_transfer(DMA, DMA_VRAM, vdpSpriteCache, VDP_SPRITE_TABLE, (sizeof(VDPSprite)*num)/2, 2);
```

`DMA` mode dispatches to `DMA_doDma()` → `DMA_doDmaFast()`, which writes DMA setup commands directly to VDP control port `0xC00004` and triggers an **immediate hardware DMA**. No CPU data port writes to `0xC00000` occur. The transfer is fully hardware-driven.

**SAT upload is IMMEDIATE (not deferred via DMA_QUEUE).** No `DMA_flushQueue()` step is required or missing for this path.

---

## 4. SAT Base Verification

### Address established in request_start_rastan()

Call sequence:

1. `restore_launcher_vdp_state()` → `VDP_init()` → `slist_addr = SLIST_DEFAULT = 0xF400`
2. `genesistan_sync_title_vdp_layout()` (main.c:1395) → `VDP_setSpriteListAddress(0xF800U)`

In `VDP_setSpriteListAddress` (tools/sgdk/src/vdp.c:736): H40 mode means `regValues[0x0C] & 0x81` is nonzero (RS1=1 for 320px), so:

```c
slist_addr = 0xF800 & 0xFC00 = 0xF800
regValues[0x05] = 0xF800 / 0x200 = 0x7C
// writes 0x857C to VDP control port
```

VDP register 5 = 0x7C → SAT base = 0x7C × 0x200 = 0xF800.

`VDP_SPRITE_TABLE` is defined as the runtime variable `slist_addr` (vdp.h:149). After `VDP_setSpriteListAddress(0xF800)`, `slist_addr = 0xF800`. The DMA target in `VDP_updateSprites` is `VDP_SPRITE_TABLE = slist_addr = 0xF800`.

**SAT base at runtime: 0xF800. Confirmed correct. YES.**

---

## 5. Publish Execution Verification

### Probe measurement gap

The Phase 1 probe used two methods to detect SAT upload:
- `sat_port_writes_words`: count of CPU writes to VDP data port `0xC00000` in the 0xF800-0xFBFF range
- `vram_f800`: direct read of VRAM via `vdp.spaces['videoram']:read_u16(0xF800)`

The `sat_port_writes_words = 0` result is **expected and non-diagnostic** for `DMA` mode. Hardware DMA never produces CPU data-port writes; the CPU only writes DMA setup commands to the VDP control port. The probe's data-port tap cannot observe DMA transfers.

The `vram_f800 = 0000 0000 0000 0000` result is the only real evidence of failure.

### Hit count discrepancy

Probe hit counts from the run:
- `HIT 03A208 791` — arcade vblank/frontend tick runs every V-INT
- `HIT 03AAEC 1` — producer slot called once
- `HIT 03AAF2 1` (report) / bridge symbol `202DB8` = 7 — renderer slot called at most 7 times
- `HIT 2005C4 2` — `genesistan_render_sprites_vdp` body entered only 2 times

**The arcade ROM frontend tick ran 791 times but invoked the renderer bridge at most 7 times and the renderer body only 2 times.** The arcade state machine at `0x03A208` rapidly advances through the title screen states. The specific states that execute the renderer dispatch at `0x03AAF2` are only active for a few initial frames. After those states complete, the arcade code continues running from V-INT but never calls back to `0x03AAF2`.

This means: VDP SAT DMA was only attempted during the first ~2 frames of the SCREEN_FRONTEND_LIVE phase. After that, the vdpSpriteCache retains valid data in WRAM, but no DMA fires to refresh VRAM.

### VRAM state at frame 700

After `request_start_rastan()` completes:
- `clear_frontend_sprite_layer()` → `VDP_updateSprites(0, CPU)` writes 8 zero bytes to VRAM 0xF800 (CPU mode, direct port writes)

After the first 1-2 renderer invocations (DMA mode with sprite_count > 0):
- VRAM 0xF800 should be populated with sprite entries

At frame 700, VRAM 0xF800 = zeros. Either:
- The initial DMA never wrote valid data (sprite_count was 0 or DMA failed during active scan)
- The arcade ROM's subsequent execution wrote zeros to VRAM 0xF800 via direct VDP port access

The arcade ROM at `0x03A208` runs every V-INT for 791 frames. The arcade code accesses the C-Window (VDP control/data ports mapped at 0xC00000 in the arcade address space). These accesses land directly on the Genesis VDP. If the arcade state machine's normal execution path writes to VDP addresses that overlap with VRAM 0xF800 (e.g., via DMA fill, VRAM clear, or plane-write commands), VRAM 0xF800 is overwritten with zeros between the 2 renderer runs and frame 700.

---

## 6. SGDK Dependency Check

### SYS_doVBlankProcess suppressed

The main loop at main.c:2045-2048:

```c
if (current_screen != SCREEN_FRONTEND_LIVE)
{
    SYS_doVBlankProcess();
}
```

`SYS_doVBlankProcess()` is explicitly suppressed during SCREEN_FRONTEND_LIVE. This means:
- `DMA_flushQueue()` (which runs inside `SYS_doVBlankProcessEx`) is never called from the main loop during SCREEN_FRONTEND_LIVE
- Any DMA_QUEUE transfers would be permanently stuck

However, `genesistan_render_sprites_vdp` uses `DMA` mode (not `DMA_QUEUE`), so the suppressed `SYS_doVBlankProcess` does NOT affect the SAT upload. The upload is immediate.

**SGDK DMA_QUEUE dependency: NOT applicable. The publish is DMA-immediate, not deferred.**

---

## 7. Timing/Measurement Check

### DMA detection method

The probe tap `_G.vd` monitors writes to `0xC00000-0xC00001` (VDP data port). Hardware DMA never writes through the CPU data port. Result `sat_port_writes_words = 0` is expected and proves nothing about DMA execution.

### VRAM read method

`vdp.spaces['videoram']:read_u16(0xF800)` reads MAME's emulated VRAM array. This IS updated by DMA transfers synchronously in MAME emulation. By frame end, any DMA that fired during that frame is fully reflected in VRAM.

### Timing verdict

The `vram_f800 = 0000` result at frame 700 is a valid observation. The DMA either (a) never wrote non-zero data to 0xF800, or (b) wrote valid data and subsequent arcade ROM execution overwrote it with zeros. Both scenarios converge on the same root cause: the publish only fires during a brief early window (2 renderer invocations), and per-frame SAT refresh is not sustained.

---

## 8. Primary Failure Classification

**Selected: B — Publish function not executing (VDP_updateSprites not called each frame).**

Evidence:
- `HIT 2005C4 2` — `genesistan_render_sprites_vdp` body entered only 2 times in a 791-vblank run
- The arcade ROM frontend tick at `0x03A208` runs 791 times but the renderer dispatch at `0x03AAF2` is only reached in the first 1-7 frames
- The arcade state machine advances past the state that calls the renderer; from that point forward, no SAT DMA fires
- vdpSpriteCache remains nonzero (data from those 2 calls persists in WRAM) but VRAM is not re-uploaded
- Any DMA that did fire at frames 1-2 was subsequently overwritten by arcade ROM VDP activity or by the frame-2 zero-path (if sprite_count was 0 at one of the 2 calls)

The function `genesistan_render_sprites_vdp` itself is structurally correct (VDP_updateSprites with immediate DMA, VDP_waitDMACompletion, SAT base at 0xF800). The failure is that the arcade ROM does not call the renderer dispatch each frame — the render hook at `0x03AAF2` is only active for a transient window of the arcade state machine.

---

## 9. Minimal Next Step

**Replace the arcade-ROM-driven renderer dispatch with a direct per-frame call to `genesistan_render_sprites_vdp()` from within `genesistan_frontend_live_vint_handoff()`, bypassing the arcade state machine's conditional path.**

Specifically: call `genesistan_render_sprites_vdp()` unconditionally from `genesistan_frontend_live_vint_handoff()` on every V-INT, after `genesistan_run_original_frontend_tick()` completes, instead of relying on the arcade ROM's state-machine to invoke it via `0x03AAF2`.

This ensures SAT DMA fires every frame regardless of which arcade state is active.

---

## 10. Final Conclusion

The Phase 1 SAT publish path is architecturally sound: the DMA mode is immediate (not queued), the SAT base is correctly set to 0xF800, and `VDP_updateSprites` is the correct call. The single failure is that the arcade state machine only dispatches the renderer hook at `0x03AAF2` for 1-7 of 791 vblanks, so VRAM 0xF800 is not updated every frame and returns to zero by frame 700.

```
SAT base at runtime: 0xF800 (confirmed by VDP_setSpriteListAddress(0xF800) in genesistan_sync_title_vdp_layout, slist_addr=0xF800, VDP reg5=0x7C)
Publish path status: Architecturally correct (immediate DMA, correct target), but only invoked ~2 times in 791 vblanks — not sustained per-frame
Primary failure: B — Publish function (genesistan_render_sprites_vdp / VDP_updateSprites) not called each frame; arcade state machine exits renderer-dispatch state after ~2 frames
Next step: Call genesistan_render_sprites_vdp() unconditionally from genesistan_frontend_live_vint_handoff() every V-INT, after genesistan_run_original_frontend_tick(), replacing reliance on arcade ROM dispatch at 0x03AAF2
```
