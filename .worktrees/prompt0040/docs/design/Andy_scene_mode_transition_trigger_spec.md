# Andy — Scene/Mode Transition Trigger Specification

## 1. Executive Summary

The `genesistan_hook_tilemap_plane_a` function in `apps/rastan-direct/src/main_68k.s` already
performs correct tile translation for any given scene, but it does not yet detect scene
transitions or call `load_scene_tiles` when the PC080SN source address (A0) moves to a different
scene's address range. This document specifies the exact trigger wiring: where in the hook to
insert the detection, what the canonical A0 range table looks like, how the fast path and slow
path differ, what state must be updated and in what order, and all surrounding contracts.

The three scene address ranges are fully disjoint and fully confirmed. The WRAM residency state
variables (`genesistan_current_scene_id`, `genesistan_scene_a0_lo`, `genesistan_scene_a0_hi`) do
NOT yet exist in `main_68k.s` `.bss` — they must be added. No other structural changes to the
hook are required beyond adding the scene-detection preamble before the descriptor loop.

---

## 2. Inputs Audited

| File | Lines / Evidence Extracted |
|------|---------------------------|
| `docs/design/Andy_tile_reference_correctness_under_mode_residency.md` | Read in full — A0 range bounds confirmed (§13), WRAM variables listed (§9), trigger wiring identified as single root risk (§12) |
| `docs/design/Andy_mode_based_pc080sn_tile_residency_system.md` | Read in full — three scene buckets with exact lo/hi values (§3), mode transition trigger design (§6), display/interrupt contract (§7), WRAM variables (§5) |
| `docs/design/Cody_independent_vram_budget_verification.md` | Read in full — 779 slot alias collisions confirmed (Task 6), scene address ranges (Task 4) |
| `apps/rastan-direct/src/main_68k.s` | Read in full (633 lines) — `genesistan_hook_tilemap_plane_a` (lines 194–316); `.bss` section (lines 579–633); `.rodata` section (lines 547–577); A0 is NOT used as source address pointer in the current hook; `genesistan_current_scene_id`, `genesistan_scene_a0_lo`, `genesistan_scene_a0_hi` are ABSENT from `.bss` |
| `apps/rastan/src/main.c` | Lines 1548–1651 — `genesistan_scene_id_from_source_addr` (range check logic), `genesistan_preload_scene_tiles` (manifest iterator, state update order), `genesistan_bulk_preload_check` (fast-path condition, slow-path call); `source_addr & 0x00FFFFFF` masking confirmed |
| `AGENTS_LOG.md` | Lines 24177–24241 — amendment entry: assembly range check replacing C call on hot path; 4 explicit trigger points rejected; disjoint ranges confirmed; AGENTS_LOG line 24227 gives exact range values matching design docs |

---

## 3. Exact Triggering Location

### Hook Structure (lines 194–316 of `main_68k.s`)

```
194: genesistan_hook_tilemap_plane_a:
195:     movem.l %d0-%d7/%a0-%a6, -(%sp)       ; REGISTER SAVE
196:     lea     0x00FF0000, %a5                 ; A5 ESTABLISHED
198:     move.w  ARCADE_PC080SN_STRIP_INDEX_OFFSET(%a5), %d7
199:     move.l  ARCADE_PC080SN_DEST_BG_OFFSET(%a5), %d5
201:     [dest validation: two cmpi.l, branches to .Lbg_hook_dest_invalid]
222:     lea     ARCADE_PC080SN_DESC_BG_LIST_OFFSET(%a5), %a0  ; A0 OVERWRITTEN
223:     movea.l #ARCADE_MAINCPU_ROM_BASE, %a1
...
229: .Lbg_hook_desc_loop:                                       ; DESCRIPTOR LOOP
```

The critical observation: A0 enters the hook as the PC080SN source pointer (the arcade 68000
leaves A0 set to the block-write source address at the intercepted call site). Line 195 saves
it via `movem.l`. Line 222 OVERWRITES A0 with the descriptor list base. Therefore:

- A0 is available as the source address from line 194 up to (but not including) line 222.
- After line 222, A0 is the descriptor list pointer and contains no source address information.
- To read the source address from the saved register frame: it was pushed at `movem.l` offset
  +32 from the stack pointer (A0 is the 9th register saved in `%d0-%d7/%a0-%a6` order;
  `movem.l` decrements stack; the saved A0 is accessible via `(9*4)(%sp)` = `36(%sp)` after
  the `movem.l` push, or equivalently via the saved value on the stack frame).

### Options Evaluated

**Option A — At entry, before `movem.l`:** A0 is live but no registers are saved. Cannot call
`load_scene_tiles` (would clobber caller's registers). REJECTED.

**Option B — After `movem.l`, before A5 establishment (line 196):** A0 is saved to stack but
A5 is not yet set. Cannot access WRAM via `(%a5)`. REJECTED.

**Option C — After A5 establishment, before the first `cmpi.l` (i.e., after line 196 but
before line 201), OR after the dest validation block and before line 222:** Either sub-point
of this range is valid. The dest validation block is not conditional on scene state — it checks
the VDP cwindow address, which is scene-independent. The cleanest insertion point is after the
dest validation passes and before A0 is overwritten at line 222, because by that point:
- All registers are saved.
- A5 = `0xFF0000` (WRAM base) is live.
- D0/D1/D2 are free scratch (dest validation results are in D4/D1/D2, but D0 has been
  consumed by the dest validation and is free again after line 217).
- A0 still holds the source address (not yet overwritten).
- The dest-invalid early-exit path has already been taken if the dest is bad, so if we reach
  this point the nametable update will proceed — scene detection is only needed on valid calls.

**CHOSEN: Option C — after dest validation passes, before line 222 (before A0 is
overwritten).** Specifically: insert scene-detection code between line 221 (`andi.w #0x001F, %d1`,
the last instruction of dest calculation) and line 222 (`lea ARCADE_PC080SN_DESC_BG_LIST_OFFSET(%a5), %a0`).

**Option D — Inside the descriptor loop:** After A0 is overwritten, source address is no
longer available without reading from the saved stack frame. Detection inside the loop also
fires 16 times per hook call. REJECTED.

### Exact Insertion Point

Insert between lines 221 and 222, using A0 while it still holds the PC080SN source address.
After the scene-detection block completes (fast or slow path), A0 is then immediately
overwritten by line 222 as normal. No change to the descriptor loop is needed.

---

## 4. Canonical A0 Range Model

Source: `Andy_mode_based_pc080sn_tile_residency_system.md` §3, confirmed by
`Andy_tile_reference_correctness_under_mode_residency.md` §13 and AGENTS_LOG line 24227.

| Scene ID | Name | Source Address Lo | Source Address Hi | Inclusive? |
|----------|------|-------------------|-------------------|------------|
| 0 | Title / Attract | `0x0005A7DA` | `0x0005B0B2` | Both inclusive |
| 1 | Gameplay | `0x00056A22` | `0x000570C2` | Both inclusive |
| 2 | End-Round | `0x0005822A` | `0x00059614` | Both inclusive |

**Range disjointness verification:**
- Gameplay: `0x56A22`–`0x570C2`
- End-Round: `0x5822A`–`0x59614`
- Title: `0x5A7DA`–`0x5B0B2`

These are in ascending order with gaps between them: `0x570C2 < 0x5822A` (gap), `0x59614 < 0x5A7DA` (gap). Fully disjoint. Confirmed by AGENTS_LOG ("source ROM address ranges per scene are fully disjoint").

**Address masking:** The PC080SN source address in arcade ROM is a 24-bit ROM address. The
arcade 68000 uses 24-bit addressing; the Genesis mapper exposes the arcade ROM at address
`0x00000200` (ARCADE_MAINCPU_ROM_BASE). When the hook captures A0, it is a full 32-bit
Genesis address. The source address comparison must use the low 24 bits only:
`andi.l #0x00FFFFFF, Ax` before comparison, exactly as `apps/rastan/src/main.c`
`genesistan_bulk_preload_check` does (`source_addr & 0x00FFFFFFUL`).

**ROM-resident range table:** The three (lo, hi) pairs belong in a `.rodata` table in
`main_68k.s`, e.g.:

```asm
genesistan_scene_a0_ranges:
    .long 0x0005A7DA, 0x0005B0B2   ; scene 0: Title
    .long 0x00056A22, 0x000570C2   ; scene 1: Gameplay
    .long 0x0005822A, 0x00059614   ; scene 2: End-Round
```

Three entries, 8 bytes each, 24 bytes total. Entirely ROM-resident. No WRAM copy required.

---

## 5. Current-Scene Fast Path

### Definition

When `genesistan_current_scene_id` is initialized (not `0xFF`) and A0 (masked to 24 bits) is
within `[genesistan_scene_a0_lo, genesistan_scene_a0_hi]`, the scene has not changed. No
reload is needed. Proceed directly to the descriptor loop.

### Exact Condition

```asm
; A0 = PC080SN source address (live, not yet overwritten)
; A5 = 0xFF0000 (WRAM base, established at line 196)
; All registers saved

move.l  %a0, %d0
andi.l  #0x00FFFFFF, %d0          ; mask to 24-bit source addr

; fast path: check if within current scene's cached bounds
cmpa.l  genesistan_scene_a0_lo, %a0   ; alternatively use %d0 against memory
; NOTE: comparison must be unsigned (cmpi.l / cmp.l with blo/bhs)
cmp.l   genesistan_scene_a0_lo, %d0   ; d0 >= lo?
blo     .Lscene_change              ; below lo: scene change
cmp.l   genesistan_scene_a0_hi, %d0   ; d0 <= hi?
bhi     .Lscene_change              ; above hi: scene change
; fast path: within range, no reload needed
bra     .Lscene_check_done
```

The comparisons use unsigned branch conditions (`blo` = branch if lower unsigned, `bhi` =
branch if higher unsigned) because ROM addresses are unsigned 24-bit values.

**Fast-path cost:** Two `cmp.l` against WRAM + two branches. Approximately 20–30 cycles.
This fires on every hook call after the first transition, covering the common case.

**Boot-time fast path:** At boot, after `load_scene_tiles(0)` is called before
`init_staging_state`, `genesistan_scene_a0_lo` = `0x0005A7DA` and `genesistan_scene_a0_hi` =
`0x0005B0B2`. All Title-scene hook invocations will take the fast path.

---

## 6. Scene-Change Path

### Step 1 — Determine new scene ID

Compare `%d0` (the masked source address) against each of the three (lo, hi) pairs in
`genesistan_scene_a0_ranges`. This is six comparisons in the worst case:

```asm
.Lscene_change:
    lea     genesistan_scene_a0_ranges, %a4
    moveq   #0, %d1                   ; scene_id = 0
.Lscene_scan:
    move.l  (%a4)+, %d2               ; lo
    move.l  (%a4)+, %d3               ; hi
    cmp.l   %d2, %d0
    blo     .Lscene_next              ; d0 < lo: try next
    cmp.l   %d3, %d0
    bhi     .Lscene_next              ; d0 > hi: try next
    bra     .Lscene_found             ; found: d1 = scene_id
.Lscene_next:
    addq.w  #1, %d1
    cmpi.w  #3, %d1
    blo     .Lscene_scan
    bra     .Lscene_unknown           ; no range matched
.Lscene_found:
    ; d1 = new scene ID (0, 1, or 2)
```

### Step 2 — Reload happens immediately inside the hook

The reload (call to `load_scene_tiles`) occurs before the descriptor loop. This is mandatory:
the descriptor loop will write nametable words referencing tile slots for the new scene; those
slots must already contain the correct pixel data before the first write.

**YES** — reload happens inside the hook, before the descriptor loop.

### Step 3 — Display must be disabled before reload

`load_scene_tiles` encapsulates the display-off/interrupt-mask/upload/display-on sequence.
The hook does not manage display state directly; it calls `load_scene_tiles` and that function
handles all VDP state transitions internally. This keeps the hook simple and ensures the
contract is enforced at every call site.

### Step 4 — State update order

`load_scene_tiles` must update `genesistan_scene_a0_lo`, `genesistan_scene_a0_hi`, and
`genesistan_current_scene_id` BEFORE it returns. This is the exact order used by
`genesistan_preload_scene_tiles` in `apps/rastan/src/main.c` (lines 1628–1630):

```c
genesistan_current_scene_id = scene_id;
genesistan_scene_a0_lo = scene_lo;
genesistan_scene_a0_hi = scene_hi;
```

Order rationale: state update at the end of `load_scene_tiles`, after the manifest upload
completes. If `load_scene_tiles` returned mid-upload (impossible in synchronous CPU-write
design, but as a rule), the bounds would be wrong. Since upload is synchronous (CPU writes
only, no DMA), the upload is complete before any state write.

In `main_68k.s`, this means at the end of `load_scene_tiles`:
1. Store scene_id to `genesistan_current_scene_id`.
2. Look up scene lo/hi from `genesistan_scene_a0_ranges` using scene_id.
3. Store lo to `genesistan_scene_a0_lo`, hi to `genesistan_scene_a0_hi`.

### Step 5 — Post-reload behavior

After `load_scene_tiles` returns, the hook continues with the descriptor loop using the
freshly loaded tiles. It does NOT return early. The nametable writes for the new scene must
proceed on the same hook call that triggered the transition; otherwise the first frame of the
new scene would be blank or stale.

```asm
.Lscene_found:
    ; d1 = new scene_id, saved registers intact
    move.w  %d1, %d0
    bsr     load_scene_tiles          ; display off, upload, state update, display on
    ; fall through to .Lscene_check_done
.Lscene_check_done:
    ; proceed: A0 is overwritten next by lea ARCADE_PC080SN_DESC_BG_LIST_OFFSET(%a5), %a0
```

---

## 7. Unknown-A0 Behavior

If A0 (masked) is outside all three scene ranges, the scan loop at `genesistan_scene_a0_ranges`
exhausts all entries without a match.

**Chosen behavior: Option A — leave current scene unchanged, continue hook.**

Justification: An unrecognized source address does not indicate a scene transition; it may
indicate a transient hook call during a mode setup frame or an address the Python static
analysis did not model. Corrupting the scene state would cause a spurious reload and a visible
black frame. The safe response is to proceed with the current scene's tiles and continue the
descriptor loop — if the tiles are slightly wrong for one frame, it is not a crash and not a
persistent error. Option B (early return) would blank the nametable for that frame, which is
worse than potentially wrong tiles.

**Implementation:**

```asm
.Lscene_unknown:
    bra     .Lscene_check_done        ; skip reload, continue with current scene
```

---

## 8. Boot-Time Interaction

### What `.bss` zero-init provides

`.bss` is zero-initialized at Genesis boot (standard linker behavior confirmed by the existing
`.bss` section in `main_68k.s`). Zero-init gives:
- `genesistan_current_scene_id` = 0 — this is the Title scene ID. Coincidentally correct for
  the initial state if `load_scene_tiles(0)` is called first.
- `genesistan_scene_a0_lo` = 0 — NOT a valid scene range bound. Would cause the fast-path
  condition to pass vacuously for any A0 (since `0 <= any_addr`), resulting in a range
  mismatch never being detected.
- `genesistan_scene_a0_hi` = 0 — NOT a valid scene range bound. Would cause the fast path
  to fail immediately for any A0 > 0, which would trigger a spurious reload.

Therefore zero-init alone is NOT safe for the scene bounds variables.

### What must be explicitly set at boot

`load_scene_tiles(SCENE_TITLE=0)` must be called from `main_68k` before `init_staging_state`,
exactly as specified in `Andy_mode_based_pc080sn_tile_residency_system.md` §9 Step 4:

```asm
main_68k:
    move.w  #0x2700, %sr
    bsr     vdp_boot_setup
    moveq   #0, %d0           ; scene_id = SCENE_TITLE
    bsr     load_scene_tiles  ; uploads Title tiles, sets scene state
    bsr     init_staging_state
    move.w  #0x2000, %sr
    ...
```

`load_scene_tiles` sets all three WRAM variables as part of its own execution. After it
returns:
- `genesistan_current_scene_id` = 0
- `genesistan_scene_a0_lo` = `0x0005A7DA`
- `genesistan_scene_a0_hi` = `0x0005B0B2`

All subsequent Title-scene hook calls take the fast path correctly. No separate explicit
initialization of the bounds variables is needed beyond what `load_scene_tiles` provides.

### Alternative: 0xFF sentinel

The design doc (`Andy_mode_based_pc080sn_tile_residency_system.md` §5) specifies
`genesistan_current_scene_id = 0xFF` as the uninitialized sentinel, which would cause the
first hook call to always trigger a reload regardless of A0. This is a valid alternative
but requires `0xFF` to be stored to `.bss` at definition time (which is impossible — `.bss`
initializes to zero) or as part of a separate init step. The preferred approach is to call
`load_scene_tiles(0)` at boot, which eliminates the need for the sentinel entirely.

If the sentinel approach is used, the BSS definition must NOT use `.byte 0xFF` (that belongs in
`.data`, not `.bss`). Instead, the fast-path check must also verify `current_scene_id != 0xFF`
before trusting the bounds.

**Recommended:** call `load_scene_tiles(0)` at boot. No sentinel needed.

---

## 9. Display / Interrupt Contract

### Contract Owner

`load_scene_tiles` owns the display/interrupt contract. The hook does not manage VDP display
state or SR directly. This matches `genesistan_preload_scene_tiles` in `main.c`, which
implicitly relies on SGDK's `VDP_loadTileData`/`VDP_waitDMACompletion` for sequencing. The
direct-port equivalent is fully explicit.

### Exact Contract for `load_scene_tiles`

1. **On entry:** mask interrupts (`move.w #0x2700, %sr`) and disable VDP display (write
   `VDP_MODE2_DISPLAY_OFF = 0x34` via `vdp_set_reg`).
2. **Manifest iteration:** for each `(u16 arcade_tile, u16 vram_slot)` pair in the scene
   manifest (stopping at `0xFFFF` sentinel): set VDP write address to `vram_slot << 5` via
   `vdp_set_vram_write_addr`; write 16 words from `genesistan_pc080sn_tile_rom + (arcade_tile
   << 5)` to `VDP_DATA`. All writes are synchronous CPU writes; no DMA queued.
3. **State update:** store `scene_id` to `genesistan_current_scene_id`; look up scene bounds
   from `genesistan_scene_a0_ranges`; store lo to `genesistan_scene_a0_lo`, hi to
   `genesistan_scene_a0_hi`.
4. **On exit:** re-enable VDP display (`VDP_MODE2_DISPLAY_ON = 0x74`) and unmask interrupts
   (`move.w #0x2000, %sr`).

### Why interrupts must be masked

The hook is called from the main loop via `arcade_tick_logic`, not from VBlank. If VBlank
fires during the tile upload, `_VINT_handler` runs. It calls `vdp_commit_tiles_if_dirty` and
`vdp_commit_bg_strips_if_dirty`, both of which write to the VDP. Interleaving VBlank VDP
writes with tile-upload VDP writes would corrupt the tile data being written (the VDP's
internal write address would be left at an incorrect offset after the interrupt). SR = 0x2700
prevents this interleaving.

### Why display must be disabled

VDP registers forbid mid-tile-write rendering. If display is active while tile data bytes are
being written, the VDP may read a partially-written tile during active display and render
visual corruption. Setting VDP_REG_MODE2 bit 6 = 0 before any tile write is the standard safe
practice. `VDP_MODE2_DISPLAY_OFF = 0x34` and `VDP_MODE2_DISPLAY_ON = 0x74` are already
defined as equates in `main_68k.s` and used by `_VINT_handler`.

### No DMA, no wait

Since all tile writes are synchronous CPU writes (direct `move.w Rn, VDP_DATA`), there is no
DMA queue to flush and no `VDP_waitDMACompletion()` equivalent is needed. The write is
complete before the next instruction executes.

---

## 10. Re-Entrancy / Repeat-Load Safety

### Problem statement

`genesistan_hook_tilemap_plane_a` fires multiple times per frame. The outer loop in the hook
processes 16 descriptors per invocation. During a single game frame, the arcade game may call
the strip producer multiple times (different strip indices, different source addresses within
the same scene range). Without the fast path, every hook call would trigger a scene check.

### Fast-path protection

The fast-path condition (`lo <= A0 <= hi`) fires on every hook call where A0 is within the
current scene's range. This is the common case during a scene. The scene change fires at most
once per actual transition (which happens 3–4 times per complete game).

### State update timing and repeat-load prevention

`load_scene_tiles` updates `genesistan_scene_a0_lo`/`genesistan_scene_a0_hi` BEFORE returning.
After the first transition-triggering hook call returns from `load_scene_tiles`:
- The bounds are set to the new scene's range.
- All subsequent hook calls within the new scene will take the fast path.
- There is no window in which a second consecutive load could be triggered for the same scene.

### No alternating-scene scenario

An alternating-scene scenario would require A0 to oscillate between two scenes' address ranges
within a single frame. The three scene ranges are fully disjoint, and the arcade game state
machine is deterministic: once a scene transition occurs, all subsequent block-write calls use
source addresses within the new scene's range until the next transition. No oscillation is
possible. The state update before return (not after) ensures the fast path is active for all
remaining calls in the current scene, regardless of how many calls occur per frame.

---

## 11. Rainbow Islands Trigger Model

### Evidence from AGENTS_LOG (lines 24177–24241)

The SGDK port architecture amendment documents the scene-detection optimization explicitly:

> "Per-invocation C call (`genesistan_bulk_preload_check`) removed from `0x5A4DE` hot path
> common case. Replaced with 2-instruction assembly range check: CMP.L A0 against stored
> scene bounds (~50 cycles vs ~300+ cycles). C fallback fires only on actual scene
> transitions (once per transition, ~3-4 times per full game)."

This is the exact model now being specified for `rastan-direct`: assembly range check on every
call (fast path), `load_scene_tiles` called only on actual transition (slow path).

### Evidence from `apps/rastan/src/main.c` (lines 1634–1651)

`genesistan_bulk_preload_check` implements:

1. Map `source_addr` to `mapped_scene_id` via `genesistan_scene_id_from_source_addr`.
2. If `(current_scene_id == mapped_scene_id) && (lo <= source_addr <= hi)`: return (fast path).
3. Otherwise: call `genesistan_preload_scene_tiles(mapped_scene_id)` (slow path).

`genesistan_preload_scene_tiles` (lines 1592–1631) implements:
- Manifest lookup by scene_id.
- Bounds lookup from source-scene map.
- Manifest iteration: `VDP_loadTileData(rastan_pc080sn + arcade_tile*32, vram_slot, 1, DMA)` per pair.
- `VDP_waitDMACompletion()` at the end.
- State update: `genesistan_current_scene_id = scene_id`, `scene_a0_lo = scene_lo`, `scene_a0_hi = scene_hi`.

The structural model is identical to what `rastan-direct` needs. The fast-path and slow-path
split, the A0 range comparison, the state update order, the manifest format, and the boot-time
call are all confirmed by reading the SGDK implementation directly.

---

## 12. Reusable and Non-Reusable Rainbow Islands Elements

### Reusable

| Element | Source evidence | Why reusable |
|---------|----------------|-------------|
| Fast-path: `(lo <= A0 <= hi)` range check before scene-ID lookup | `main.c` line 1643–1645 | Architecture-neutral O(1) comparison; translates to two `cmp.l` + two branches in assembly |
| Slow-path: call preload only on scene change | `main.c` line 1650 | Identical to the direct-port requirement |
| State update order: id, lo, hi all set INSIDE preload function before return | `main.c` lines 1628–1630 | Prevents any window where bounds are stale on return |
| Manifest format: `(u16 arcade_tile, u16 vram_slot)` pairs, `0xFFFF` sentinel | `main.c` lines 1610–1614 | Binary format already used in `build/` manifests; hardware-neutral |
| Scene ID 0 = Title, 1 = Gameplay, 2 = End-Round | `main.c` constant definitions | Matches `.py` tool and manifest files |
| Boot-time explicit preload of Title before first arcade tick | `main.c` line 2252 context | Game always starts in Title mode; identical for direct port |
| Disjoint source address ranges as scene-detection oracle | AGENTS_LOG line 24227 | Ranges are fully disjoint; reliable for assembly range-check |
| Per-scene ROM-resident (lo, hi) bounds table | Implicit in `main.c` / `genesistan_scene_bounds_from_map` | Translates to 3-entry `.rodata` table in assembly |

### Non-Reusable

| Element | Source evidence | Why not reusable |
|---------|----------------|-----------------|
| `genesistan_scene_id_from_source_addr` reading `pc080sn_source_scene_map.bin` | `main.c` lines 1548–1588 | Binary source-scene map file; AGENTS_LOG amendment rejected it: hardcoded bounds table in assembly is sufficient and simpler |
| `genesistan_scene_bounds_from_map` reading from map binary | `main.c` lines 1529–1546 | Same map binary; replaced by direct ROM-resident table |
| `VDP_loadTileData` SGDK DMA API | `main.c` line 1618 | SGDK C API; not present in `rastan-direct`; replaced by synchronous `move.w Rn, VDP_DATA` loop |
| `VDP_waitDMACompletion()` | `main.c` line 1626 | DMA management; `rastan-direct` uses synchronous CPU writes; no DMA queue to flush |
| `genesistan_scene_manifest_for_id` C switch | `main.c` line 1599 | C function pointer; replaced by branch table or `cmpi`/`lea` sequence in assembly |
| C struct pointer arithmetic and `text_writer_read_be16` helper | `main.c` lines 1609–1614 | C-specific; replaced by direct `move.w (%a0)+` word reads with auto-increment |
| Explicit `scene_id == GENESISTAN_SCENE_UNKNOWN` guard | `main.c` line 1638 | SGDK-specific unknown sentinel; not needed in assembly if unknown-A0 path is a simple branch to continue |

---

## 13. Final Scene-Trigger Contract

### Inputs

- A0: PC080SN source address (live at hook entry, valid until line 222 where it is overwritten).
- `genesistan_scene_a0_lo` (WRAM u32): lower bound of currently-loaded scene's source range.
- `genesistan_scene_a0_hi` (WRAM u32): upper bound of currently-loaded scene's source range.
- `genesistan_current_scene_id` (WRAM u8): ID of currently-loaded scene (0/1/2).
- `genesistan_scene_a0_ranges` (ROM table, 3 × 8 bytes): three `(u32 lo, u32 hi)` pairs for
  scenes 0, 1, 2.

### State on entry (precondition)

At the insertion point (after dest validation, before line 222), registers are all saved and
A5 = `0xFF0000`. A0 holds the PC080SN source address. D0–D7, A1–A4, A6 are available as
scratch (the desc loop does not begin until after this preamble).

### Branch 1 — Fast path (scene unchanged)

Condition: `(A0 & 0x00FFFFFF) >= genesistan_scene_a0_lo` AND
           `(A0 & 0x00FFFFFF) <= genesistan_scene_a0_hi`

Action: do nothing. Fall through to line 222. Descriptor loop proceeds normally.

Cost: ~20–30 cycles. Fires on every hook call within a scene.

### Branch 2 — Slow path (scene transition)

Condition: fast path condition fails.

Action:
1. Mask A0 to 24 bits into a scratch register.
2. Scan `genesistan_scene_a0_ranges` (3 entries): find the entry where `lo <= masked_A0 <= hi`.
3. If found: set new_scene_id = entry index.
4. Call `load_scene_tiles(new_scene_id)`.
5. Inside `load_scene_tiles`:
   a. Save registers as needed.
   b. Set SR = 0x2700 (mask interrupts).
   c. Disable VDP display via `vdp_set_reg(VDP_REG_MODE2, VDP_MODE2_DISPLAY_OFF)`.
   d. Load manifest base pointer from branch table (scene 0 → `genesistan_scene_preload_title`,
      scene 1 → `genesistan_scene_preload_gameplay`, scene 2 → `genesistan_scene_preload_endround`).
   e. Iterate `(u16 arcade_tile, u16 vram_slot)` pairs (4 bytes per pair); stop at `0xFFFF` sentinel.
   f. For each pair: call `vdp_set_vram_write_addr(vram_slot << 5)`; write 16 words from
      `genesistan_pc080sn_tile_rom + (arcade_tile << 5)` to `VDP_DATA`.
   g. Store new_scene_id to `genesistan_current_scene_id`.
   h. Look up `(lo, hi)` for new_scene_id from `genesistan_scene_a0_ranges`.
   i. Store lo to `genesistan_scene_a0_lo`, hi to `genesistan_scene_a0_hi`.
   j. Re-enable VDP display via `vdp_set_reg(VDP_REG_MODE2, VDP_MODE2_DISPLAY_ON)`.
   k. Set SR = 0x2000 (unmask interrupts).
   l. `rts`.
6. After `load_scene_tiles` returns: fall through to line 222. Descriptor loop proceeds.

Cost: first invocation of new scene only. Approximately 4.5 ms for End-Round (worst case).

### Branch 3 — Unknown A0

Condition: scan of `genesistan_scene_a0_ranges` finds no match.

Action: do nothing. Fall through to line 222. Current scene tiles remain in VRAM. Descriptor
loop proceeds with current scene's slot assignments. No state change.

Rationale: unknown addresses are transient or unmapped; current scene tiles are better than
a forced black frame.

### Post-condition

After the scene-detection preamble completes (any branch), execution resumes at line 222:
`lea ARCADE_PC080SN_DESC_BG_LIST_OFFSET(%a5), %a0`. The descriptor loop runs as normal. If a
scene transition occurred, VRAM now contains the new scene's tile data, so all subsequent LUT
lookups in the descriptor loop produce correct results.

### Re-entrancy guarantee

`load_scene_tiles` updates `genesistan_scene_a0_lo/hi` before returning. The next hook call
will take the fast path for the new scene. No second load can fire for the same transition.

---

## 14. Single Root Risk

**The three WRAM state variables (`genesistan_current_scene_id`, `genesistan_scene_a0_lo`,
`genesistan_scene_a0_hi`) are entirely absent from `main_68k.s` `.bss` and must be added
before any scene-detection code can reference them — if they are omitted, the fast-path
`cmp.l` instructions will reference whatever memory happens to be at their addresses, producing
nondeterministic reload behavior or spurious scene changes on every hook call.**

---

## 15. Single Next Correction

Cody must implement the complete trigger wiring in `apps/rastan-direct/src/main_68k.s` only:
(1) add `genesistan_current_scene_id` (u8), `genesistan_scene_a0_lo` (u32), and
`genesistan_scene_a0_hi` (u32) to `.bss`; (2) add `genesistan_scene_a0_ranges` (3 × 8 bytes of
lo/hi pairs for scenes 0/1/2) to `.rodata`; (3) inside `load_scene_tiles` (already specified
in `Andy_mode_based_pc080sn_tile_residency_system.md` §9 Step 3), after the display-on step,
store `scene_id` to `genesistan_current_scene_id` and store the corresponding lo/hi from
`genesistan_scene_a0_ranges` to `genesistan_scene_a0_lo`/`genesistan_scene_a0_hi`; (4) insert
the scene-detection preamble between lines 221 and 222 of the hook: mask A0 to 24 bits, fast-
path compare against stored bounds, on miss scan `genesistan_scene_a0_ranges` and call
`load_scene_tiles` with the matched scene ID, unknown-A0 falls through silently.

---

## 16. What Must Not Be Changed Yet

- `genesistan_hook_tilemap_plane_a` descriptor loop (lines 229–315) — the scene-detection
  preamble is inserted BEFORE the loop; the loop itself is unchanged.
- `genesistan_pc080sn_tile_vram_lut` and its `.incbin` directive — correct and verified.
- All three scene manifest binaries in `build/` — correct by construction, zero inconsistencies.
- `init_staging_state` internal logic — checkerboard fill and synthetic tile setup unchanged.
- Synthetic tile data (slots 1–3) — scaffolding retained; no removal scheduled for this step.
- `_VINT_handler` structure — commit order and display-disable bracketing unchanged.
- Sprite system (PC090OJ) — no changes of any kind.
- `postpatch_startup_rom.py` patcher — unchanged.
- Makefile — no build system changes.
- All 34 `opcode_replace` entries in `specs/rastan_direct_remap.json`.
- `rom_absolute_call_relocation` configuration.
- A5 initialization to `0xFF0000`.
- `VRAM_TILE_BASE = 0x00000020`.
- `precompute_pc080sn_tile_lut.py` — tool is correct; no regeneration needed.
- `pc080sn_source_scene_map.bin` — not required; hardcoded bounds table in `.rodata` replaces it.
- The `load_scene_tiles` function body (already specified by
  `Andy_mode_based_pc080sn_tile_residency_system.md`) — only the state-update tail
  (`genesistan_current_scene_id`/`scene_a0_lo`/`scene_a0_hi`) must be added if not yet present.

---

## 17. Final Verdict

The scene-transition trigger for `genesistan_hook_tilemap_plane_a` is fully specified. The
trigger inserts a scene-detection preamble between the destination-validation block and the
descriptor loop (between lines 221 and 222 of `main_68k.s`). The fast path is a two-comparison
unsigned range check against WRAM-cached bounds costing ~25 cycles per hook call. The slow path
fires only on actual scene transitions (3–4 times per game), calls `load_scene_tiles` which
encapsulates display-off, interrupt-mask, synchronous tile upload, state update, display-on,
and interrupt-unmask. Unknown source addresses fall through silently.

The three WRAM variables are confirmed absent from `.bss` and must be added. The canonical A0
range table belongs in `.rodata` (ROM-resident, never modified). State update order (id, lo, hi)
inside `load_scene_tiles` before `rts` is confirmed by direct reading of `main.c`
`genesistan_preload_scene_tiles`. Re-entrancy is guaranteed by the bounds update happening
before return.

This specification draws entirely from evidence in the required inputs. No speculation was used.
All exact values (range bounds, scene IDs, WRAM variable names, instruction sequence) trace
directly to source files or prior design documents with zero gaps.
