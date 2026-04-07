# Andy — Rastan-Direct Video Bring-Up Plan

## 1. Executive Summary

This document defines the complete first-video bring-up plan for `apps/rastan-direct/`, the
assembly-only, no-SGDK, no-launcher branch of the Rastan Genesis port. It integrates two prior
audit findings (DEST_PTR_NEVER_INITIALIZED, sprite DMA VRAM destination bug) as mandatory
prerequisites, selects a single first test target, defines six ordered bring-up phases, specifies
all required WRAM contracts, fixes the exact VBlank commit order, and produces a single linear
implementation sequence for Cody to execute.

Architecture constraints honored throughout:
- Assembly only — no C, no SGDK runtime, no C compiler toolchain
- No launcher — the ROM boots directly into arcade execution
- Direct arcade opcode execution via hooks/opcode replacements
- VBlank is the sole hardware commit owner
- Sound is out of scope for this plan

Current state of `apps/rastan-direct/`: minimal skeleton only. `boot/boot.s` contains a working
TMSS stub and calls `main_68k`. `main_68k.s` is a Z80 sound test stub with no video output. No
VBlank handler, no tilemap commit, no SAT commit, no palette commit. Everything required for
first video must be built.

---

## 2. First Real Video Test Target

**Target: attract-mode BG layer only (Plane B, tilemap content visible, no sprites, no scroll
animation required).**

Justification:

The attract-mode BG layer is the correct first target because:

1. It requires the fewest systems to be simultaneously functional. BG tilemap commit is one
   pipeline: arcade tick populates the WRAM buffer via the BG hook, VBlank commits the buffer to
   VRAM Plane B (0xC000). Nothing else is strictly required to see pixel output.

2. The tilemap correctness audit (`Andy_tilemap_correctness_audit.md`) confirmed the BG
   translation pipeline is structurally correct except for the DEST_PTR_NEVER_INITIALIZED root
   cause. Fixing that one field (workram 0x10A0 = 0x00C00000) makes the BG commit hook functional
   from frame 1.

3. The BG layer (Plane B at VRAM 0xC000) carries the most visually recognizable content in
   attract mode: the landscape, stone floor, and castle background. Seeing this layer confirms
   the entire opcode execution → hook → WRAM buffer → VBlank commit pipeline is working.

4. Sprites add a second independent pipeline (DMA VRAM destination bug must be fixed, SAT must
   be written). FG layer requires its own DEST_PTR fix (0x10A4). Both can be deferred. The BG
   path is self-contained.

5. Palette is required for any visible color output (otherwise everything appears as gray or
   solid blocks from CRAM=0), so palette commit is co-required with the BG test. This is phase 5
   of the bring-up, and it is reachable before sprites.

The first real video test is: **attract-mode BG layer with correct colors, no sprites.**
Success artifact: recognizable Rastan background graphics (stone/castle) visible on Plane B,
colors correct, no sprite content required.

---

## 3. Minimum Required Arcade Opcode Paths

For the first real video test target (attract-mode BG layer, correct colors, no sprites):

| System | Status for First Test | Reason |
|--------|-----------------------|--------|
| Tilemap writes — PC080SN BG strip commits | **ACTIVE** | The entire purpose of the first test. BG hook must run, WRAM buffer must be written, VBlank must commit the buffer to Plane B. DEST_PTR fix mandatory. |
| Tilemap writes — PC080SN FG strip commits | **ACTIVE (with DEST_PTR fix)** | FG hook already runs; after the 0x10A4 fix it will populate the FG buffer. FG content on Plane A appears simultaneously with BG. Both DEST_PTR fixes are applied together at the same init site. |
| Scroll writes — PC080SN horizontal/vertical scroll | **ACTIVE (staging only, zeros acceptable)** | The arcade tick unconditionally writes the scroll register every frame. The opcode patch at the 0x3C0000 write site must exist and redirect to a staging stub, otherwise the original write hits unmapped memory and may fault. Staging near-zero values is acceptable; the viewport stays fixed during attract mode. |
| Sprite writes — PC0900J sprite list construction and DMA | **STUBBED** | Sprite pipeline is blocked by the DMA VRAM destination bug. SAT entries can be zeroed each frame (no sprites visible) without corrupting anything. The SAT write must not produce bus errors, but sprite content is not required for the first test. |
| Palette writes — color RAM updates | **ACTIVE** | Without palette data in CRAM, all tile colors render black/default. The arcade tick writes palette data via the CLCS mechanism; the palette hook must stage it and VBlank must commit it for any color output. |
| Per-frame execution / interrupt flow — main game loop driving all of the above | **ACTIVE** | The arcade tick must actually execute. The main loop must call the arcade entry point once per frame after waiting for VBlank. Without this nothing gets staged. |

---

## 4. Ordered Video Bring-Up Phases

### Phase 1 — Direct Boot + VBlank Ownership

**Goal**: ROM boots without crashing. VBlank handler owns the interrupt. A single frame counter
increments each VBlank. No video output yet.

**Systems active**:
- Vector table at 0x000000: reset, VINT, HINT (RTE stub), error stubs
- ROM header at 0x000100 (TMSS compliance)
- Boot stub at 0x000200: TMSS write, Z80 halt, VDP register baseline init (19 registers, display
  OFF), VRAM clear, CRAM clear, VSRAM clear, Z80 bus released, SP init, interrupt unmask
- `_VINT_handler`: register save, VDP status read (interrupt acknowledge), frame counter
  increment, register restore, RTE — nothing else
- Main loop: wait for frame counter increment, fall through (no arcade tick yet)

**Known blockers**: None from prior audits. The current `boot/boot.s` already handles TMSS.
The existing skeleton must be extended to add full VDP register init, VRAM/CRAM/VSRAM clear,
and a real VBlank handler replacing the current main_68k Z80 test loop.

**Success artifact**: ROM boots to black screen. BlastEm debugger shows frame counter
incrementing at 60Hz. No exception vectors fire.

---

### Phase 2 — Tilemap Path Bring-Up

**Goal**: Arcade tick executes. BG and FG WRAM buffers receive tilemap content. VBlank commits
both buffers to VRAM. Recognizable background graphics visible on screen.

**Systems active**:
- All of Phase 1
- Arcade ROM copy at its relocated base with full opcode relocation applied
- DIP switch patches (0x390009 → `moveb #0xFE, %d0`; 0x39000B → `moveb #0xFF, %d0`)
- TC0040IOC coin/service/tilt/test patches (all return 0xFF)
- TC0040IOC control write patches (0x380000 writes → NOP)
- Workram A5 base initialized: `lea genesistan_arcade_workram_words, %a5`
- DEST_PTR initialization: workram 0x10A0 = 0x00C00000, workram 0x10A4 = 0x00C08000
  (MANDATORY — Phase 2 cannot function without this; BG and FG hooks always take out-of-range
  branch with both fields at zero)
- PC080SN BG and FG strip commit hooks in trampoline: redirect arcade writes to WRAM
  `pc080sn_bg_buffer` and `pc080sn_fg_buffer`
- Main loop: wait for frame counter → run arcade tick → repeat
- VBlank: commit `pc080sn_bg_buffer` to VRAM 0xC000 (Plane B), commit `pc080sn_fg_buffer`
  to VRAM 0xE000 (Plane A), display OFF bracket around commits, display ON after
- Desc list at workram+0x1000 must be populated by the arcade init sequence before commit

**Known blocker — DEST_PTR_NEVER_INITIALIZED** (from `Andy_tilemap_correctness_audit.md`):
workram bytes 0x10A0 and 0x10A4 remain zero without explicit initialization. Both BG and FG
hooks always take the out-of-range branch. Fix: initialize both fields before first arcade tick.
This is the mandatory fix for Phase 2.

**Success artifact**: Plane B shows recognizable BG tile content. Plane A shows FG tile content.
Both update each frame as attract mode advances. No sprites.

---

### Phase 3 — Scroll Path Bring-Up

**Goal**: Scroll register writes by the arcade tick are intercepted and staged. VBlank commits
staged scroll values to VSRAM and HScroll table. Viewport position matches arcade scroll intent.

**Systems active**:
- All of Phase 2
- Opcode patch at `movew %d0, 0x3C0000` arcade write sites: redirect to `_scroll_stage` stub
- `_scroll_stage` stub: reads workram fields A5+0x10AE (FG X), A5+0x10B0 (FG Y), A5+0x10EC
  (BG X), A5+0x10EE (BG Y); applies negation and +8 vertical bias; writes to four WRAM staging
  words: `staged_scroll_x_fg`, `staged_scroll_y_fg`, `staged_scroll_x_bg`, `staged_scroll_y_bg`
- Opcode patches for scroll clear writes at 0xC20000 and 0xC40000: suppress (NOP) or redirect
  to clear the corresponding staging words
- VBlank: after display ON, write staged scroll values to HScroll table (VRAM 0xF000,
  2 words) and VSRAM (offset 0, 2 words) via direct port writes

**Known blockers**: None from prior audits. The scroll path has no known bugs per prior
analysis. The concern is ensuring all scroll write sites in the arcade ROM are patched so no
write reaches unmapped memory 0x3C0000. During attract mode the scroll values are near-zero,
so even incorrectly staged zero values produce no visual regression.

**Success artifact**: Scroll values committed to VSRAM and HScroll table each frame. During
attract mode, viewport is fixed (near-zero scroll, correct). On gameplay entry, camera scroll
is live. No BlastEm warnings about writes to 0x3C0000.

---

### Phase 4 — Sprite Path Bring-Up

**Goal**: Sprite tiles DMA to correct VRAM slots. SAT entries reference correct tiles. Sprites
visible on screen with correct pixel content, position, palette, and flip.

**Systems active**:
- All of Phase 3
- DMA VRAM destination bug fix in `.Lspr_dma_tile` (MANDATORY — see mandatory fixes section):
  `swap %d2` replaced with `lsr.l #14, %d2` so bits 14-15 of VRAM address are correctly
  extracted, directing sprite tile DMA to VRAM 0x8000–0x8A80 (tiles 1024–1108)
- Pass 1 (DMA tile upload) and Pass 2 (SAT write) both active
- SAT written directly to VDP data port by `genesistan_render_sprites_vdp_asm` during arcade
  tick; VBlank does not need to separately commit SAT in this asm path
- Sprite hook bridges at all patched arcade sites (0x03A20E, 0x03A264, etc.) redirect to
  `genesistan_render_sprites_vdp_bridge`

**Known blocker — Sprite DMA VRAM destination bug** (from `Andy_pc0900j_sprite_correctness_audit.md`):
`.Lspr_dma_tile` lines 330–332 use `swap %d2; andi.w #0x0003, %d2` which yields d2=0 for all
16-bit VRAM addresses, directing all DMA to VRAM 0x0000–0x0B80 instead of 0x8000–0x8B80. SAT
entries reference tiles 1024–1108 (VRAM 0x8000+) which are never populated. Fix: replace
`swap %d2` with `lsr.l #14, %d2`. This is the mandatory fix for Phase 4.

**Success artifact**: Sprite tiles DMA to VRAM 0x8000–0x8A80. Sprites appear on screen with
correct pixel graphics (not blank/transparent). Player figure, enemies, and attract-mode logo
sprites all render. No corruption of nametable tiles 0–84 from misdirected DMA.

---

### Phase 5 — Palette Path Bring-Up

**Note**: Palette commit is required before Phase 2 produces colored output. In practice,
Phase 5 is implemented concurrently with Phase 2 (BG graphics require palette data in CRAM
to be visible in correct colors). The ordering below represents functional dependency; actual
implementation merges Phase 2 and Phase 5 into a single implementation step.

**Goal**: Palette staging populated by arcade CLCS writes. VBlank converts xBGR-555 to
Genesis xBGR-444 and writes 64 words to CRAM. Correct colors on screen.

**Systems active**:
- All of Phase 2
- Arcade palette write hook: directs arcade palette data to `genesistan_palette_clcs` staging
  buffer (same layout as current SGDK branch)
- `_palette_commit` VBlank routine: scans `genesistan_palette_clcs` blocks 0–3, converts
  xBGR-555 to Genesis format, writes 64 words to CRAM via direct port writes
- Palette dirty flag (`vblank_flag_palette`) set by hook, cleared after commit
- VBlank: commit palette before display ON when flag is set

**Known blockers**: None from prior audits. The current `genesistan_palette_commit_asm` in
`startup_trampoline.s` implements this logic. The port to rastan-direct reuses the same
xBGR-555 → Genesis conversion with no format changes.

**Success artifact**: CRAM populated with arcade color data. Tiles render in correct arcade
palette (greens, browns, stone grays). No all-black or rainbow-noise output.

---

### Phase 6 — First Recognizable Attract-Mode Output

**Goal**: All four video systems (tilemap BG+FG, palette, scroll, sprites) functional
simultaneously. A complete attract-mode frame with background, foreground, colors, and sprites
visible on screen, stable, updating each game tick.

**Systems active**:
- All of Phases 1–5
- Both DEST_PTR fixes applied (workram 0x10A0 = 0x00C00000, 0x10A4 = 0x00C08000)
- Sprite DMA VRAM destination bug fixed (`lsr.l #14, %d2`)
- All TC0040IOC patches applied (DIP, joystick stub, coin suppress, service/tilt/test inactivate,
  control write suppress)
- Input: Genesis pad read stub providing active-low byte to arcade workram input shadows
  (joystick reads at 0x03A4A2, 0x03A4A8, 0x03A778, 0x03A77E patched to `jsr _input_read_p1/p2`)
- Frame timing: main loop polls frame counter before each arcade tick
- Tile preload: scene tiles for title/attract loaded to VRAM slots 20–1023 and 1280–1439 before
  first arcade tick

**Known blockers**: The two mandatory bug fixes from prior audits (see Section 5). Without the
DEST_PTR fix, both planes remain blank. Without the sprite DMA fix, all sprites render blank.

**Success artifact**: Rastan attract mode running on Genesis hardware. Recognizable background
castle/stone landscape on Plane B. Character/enemy sprites visible on Plane A. Text elements
visible. Frame advances through attract sequence. A recognizable Rastan scene is on screen.

---

## 5. Mandatory Known Fixes from Prior Audits

### Fix 1 — DEST_PTR_NEVER_INITIALIZED

**Source audit**: `docs/design/Andy_tilemap_correctness_audit.md`, Section 9.

**Root cause**: Arcade workram fields at byte offset 0x10A0 (BG dest_ptr) and 0x10A4 (FG
dest_ptr) remain 0x00000000 for the entire session. All arcade stores to these addresses are
either inside routines that were entirely replaced (the stores no longer exist) or covered by
NOP patches that suppress them. The BG and FG hooks (`genesistan_hook_tilemap_plane_a` /
`genesistan_hook_tilemap_plane_b`) call `pc080sn_dest_ptr_to_row_col` each frame; with dest=0
the function returns FALSE, the hook takes the out-of-range branch, and neither WRAM buffer is
ever written.

**Is this mandatory before first recognizable output?** YES.

**Phase at which it must be corrected**: Phase 2 (Tilemap Path Bring-Up). Without this fix,
Phase 2 produces no tilemap output and Phase 6 cannot be reached.

**Exact correction**: In the boot stub (before first arcade tick, after workram zero-init):
```
; BG dest_ptr
move.l #0x00C00000, genesistan_arcade_workram_words+0x10A0
; FG dest_ptr
move.l #0x00C08000, genesistan_arcade_workram_words+0x10A4
```
These four-byte stores use the WRAM addresses as pure integers (never dereferenced); no crash
risk on Genesis hardware.

---

### Fix 2 — Sprite DMA VRAM Destination Bug

**Source audit**: `docs/design/Andy_pc0900j_sprite_correctness_audit.md`, Sections 5.2 and 10.

**Root cause**: In `startup_trampoline.s`, function `.Lspr_dma_tile`, lines 330–332:
```asm
move.l  %d0, %d2
swap    %d2
andi.w  #0x0003, %d2
```
For any VRAM address in the 16-bit range (0x0000–0xFFFF), d0 as a 32-bit value has its upper
16 bits zero. After `swap`, the lower word of d2 equals the original upper 16 bits = 0x0000.
`andi.w #0x0003, %d2` yields d2=0 for all sprite tile addresses. The VDP DMA command targets
VRAM address `addr & 0x3FFF` instead of the intended address, stripping bit 15. All sprite
tile DMA lands at VRAM 0x0000–0x0B80 (tiles 0–87) instead of 0x8000–0x8B80 (tiles 1024–1108).
SAT entries reference tiles 1024–1108, which contain no sprite pixel data. All sprites render
as blank/transparent 16×16 regions.

**Is this mandatory before first recognizable output?** YES, for sprites specifically. Without
this fix, the sprite pipeline appears functional (SAT entries correct, positions correct,
attributes correct) but produces no visible pixel output.

**Phase at which it must be corrected**: Phase 4 (Sprite Path Bring-Up). Phases 2, 3, and 5
are achievable without this fix (tilemap and palette are independent pipelines).

**Exact correction**: Replace `swap %d2` with `lsr.l #14, %d2`:
```asm
move.l  %d0, %d2
lsr.l   #14, %d2      ; was: swap %d2
andi.w  #0x0003, %d2
```
For VRAM 0x8000: d2 changes from 0 to 2. The DMA command changes from `0x40000080` to
`0x40000082`. DMA targets VRAM 0x8000 (tile 1024) as intended.

---

## 6. Required WRAM Contracts

The following WRAM fields must hold specific values before or by specified frames for the video
pipeline to function. All fields are in `genesistan_arcade_workram_words` (base in WRAM, A5
points here during arcade execution).

| Field name | Byte offset from workram base | Required value | Timing | Consumer |
|------------|-------------------------------|----------------|--------|----------|
| BG dest_ptr | 0x10A0 (4 bytes) | 0x00C00000 | Before first arcade tick | BG tilemap hook — `pc080sn_dest_ptr_to_row_col` returns TRUE only when dest is in 0xC00000–0xC03FFF |
| FG dest_ptr | 0x10A4 (4 bytes) | 0x00C08000 | Before first arcade tick | FG tilemap hook — same validation, range 0xC08000–0xC0BFFF |
| DIP1 mirror | 0x0018 (2 bytes) | 0x0001 (active-high: test=OFF, flip=OFF, coin=1C/1C) | Before startup_common runs | Arcade startup_common reads this at init to configure game behavior. Without it the game enters test mode (bit 0 = 1) or uses wrong coin settings |
| DIP2 mirror | 0x001C (2 bytes) | 0x0000 (active-high: Easy, 30k bonus, 3 lives, continue=OFF) | Before startup_common runs | Same — arcade startup_common latches DIP2 at boot |
| Mode word | 0x0002 (2 bytes) | 0x0000 (attract mode) | Set by arcade init | Written by arcade startup_common; controls branch at 0x03A018. Not Genesis-initialized — arcade sets it. |
| PC080SN desc list | 0x1000 (16 × 4 bytes = 64 bytes) | Valid ROM descriptor pointers | Populated by arcade init sequence before first strip commit | BG and FG strip commit hooks read entries from this list. If the arcade init sequence runs correctly, the list is populated by the time the first tilemap hook executes. No Genesis-side initialization required. |
| Scroll staging (FG X) | `staged_scroll_x_fg` (Genesis WRAM, not arcade workram) | Populated by `_scroll_stage` stub on first arcade tick | Before first VBlank commit | VBlank scroll commit reads this. Zero is acceptable for attract mode. |
| Scroll staging (FG Y) | `staged_scroll_y_fg` | Same | Same | Same |
| Scroll staging (BG X) | `staged_scroll_x_bg` | Same | Same | Same |
| Scroll staging (BG Y) | `staged_scroll_y_bg` | Same | Same | Same |
| Frame counter | `vblank_frame_counter` (Genesis WRAM) | Increments each VBlank | Populated by VBlank handler from Phase 1 | Main loop polls this to synchronize one arcade tick per frame |
| Arcade input shadows | workram input offsets read by 0x390001/0x390003 patches | Active-low byte from Genesis pad stub | Populated by `_input_read` stub before each arcade tick | Arcade input handler at 0x03A4A2 reads these; without valid values the player cannot move (attract mode is unaffected — input is not polled during attract) |
| Palette CLCS blocks | `genesistan_palette_clcs` (Genesis WRAM) | Populated by arcade palette write hooks | Within first few frames of arcade tick | VBlank palette commit scans blocks 0–3; empty blocks produce black output |

---

## 7. Exact VBlank Commit Order

One order. No alternatives.

```
_VINT_handler:
    movem.l %d0-%d7/%a0-%a6, -(%sp)   ; save all registers

    ; 1. Acknowledge VBlank — read VDP status register (clears interrupt flag)
    move.w  0xC00004, %d0

    ; 2. Display OFF — stop rendering before writing VRAM/CRAM
    move.w  #0x8134, 0xC00004

    ; 3. Commit BG tilemap — write pc080sn_bg_buffer to VRAM 0xC000 (Plane B)
    ;    2048 words, CPU word stream, VDP auto-increment=2, command 0x40000003
    bsr     _commit_tilemap_bg

    ; 4. Commit FG tilemap — write pc080sn_fg_buffer to VRAM 0xE000 (Plane A)
    ;    2048 words, CPU word stream, command 0x60000003
    bsr     _commit_tilemap_fg

    ; 5. Commit palette — convert and write genesistan_palette_clcs to CRAM
    ;    64 words, CPU word stream, xBGR-555 to Genesis conversion inline
    ;    Only if vblank_flag_palette != 0; clear flag after commit
    tst.w   vblank_flag_palette
    beq.s   .Lno_palette
    bsr     _commit_palette
    clr.w   vblank_flag_palette
.Lno_palette:

    ; 6. Display ON — re-enable rendering
    move.w  #0x8174, 0xC00004

    ; 7. Commit scroll — write staged scroll values to VSRAM and HScroll table
    ;    Executed AFTER display ON (VSRAM writes safe after display re-enable;
    ;    proven by Rainbow Islands Genesis ordering)
    ;    HScroll table: VRAM 0xF000, 2 words (FG X, BG X)
    ;    VSRAM: offset 0, 2 words (FG Y, BG Y)
    ;    Unconditional every frame — arcade tick writes scroll every tick
    bsr     _commit_scroll

    ; 8. Increment frame counter — main loop polls this for tick synchronization
    addq.l  #1, vblank_frame_counter

    movem.l (%sp)+, %d0-%d7/%a0-%a6   ; restore all registers
    rte
```

**Display-off bracket**: Required. Covers tilemap writes (steps 3–4) and palette writes (step 5).
VRAM nametable writes without display-off produce visible tearing artifacts. The bracket is
removed before scroll commit.

**Tilemap commit ordering**: BG (Plane B) committed before FG (Plane A). Order is not
architecturally required — both planes use different VRAM addresses — but BG-first is the
conventional ordering matching Rainbow Islands and minimizing VDP contention.

**SAT/sprite commit ordering**: The active sprite path (`genesistan_render_sprites_vdp_asm`)
writes SAT entries directly to VDP during the arcade tick (outside VBlank). The VBlank handler
does not separately commit the SAT. This is the current architecture of the asm sprite path.
No additional SAT step in the VBlank handler is required for the Phase 4 target.

**Palette commit ordering**: Inside display-off bracket, after tilemap commits, before display
ON. This is safe because CRAM writes do not interfere with nametable commits and the conversion
is fast (64 words).

**Scroll commit ordering**: After display ON, unconditionally. VSRAM writes are internally
double-buffered by the Genesis VDP — they can be committed after display re-enable without
visible artifacts. Rainbow Islands proves this timing is correct for this hardware family.

**Display-on timing**: After palette commit, before scroll commit. The display is active for
the remainder of the VBlank and into the active display period while scroll is being committed.

---

## 8. What Must Not Be Built Yet

The following items are explicitly out of scope for the first video bring-up milestone:

1. **Sound** — Z80 driver, YM2612 communication, sound command forwarding, all audio
   subsystems. Out of scope for this entire plan.

2. **Input gameplay response** — Genesis pad reads are stubbed to inactive (all buttons
   unpressed) for video bring-up. Input translation and arcade shadow writes are not required
   for attract mode video output.

3. **Coin insertion / credit management** — Coin reads stubbed to "no coin." No coins accepted,
   no credit increment, no gameplay entry during video testing.

4. **Service mode / test mode / DIP switch UI** — DIP reads hardcoded to factory defaults.
   No test screen, no service mode, no DIP configuration UI of any kind.

5. **Scroll correctness verification** — scroll staging is active (prevents bus errors) but
   scroll value accuracy and parallax correctness are not validated during video bring-up.
   Attract mode uses near-zero scroll; visual correctness of scroll is a post-bring-up concern.

6. **Scene transition handling** — only attract mode (title/attract sequence starting from boot)
   is targeted. Scene scoping (title vs gameplay vs endround tile preload sets) is not a first
   bring-up concern.

7. **Multi-scene tile preloading / scene detection** — the scene preload system from `main.c`
   (`genesistan_preload_scene_tiles`, scene detection via source_scene_map) is not ported for
   bring-up. A single static preload of attract/title scene tiles (slots 20–1023) before the
   first arcade tick is sufficient.

8. **Diagnostic overlay / debug renders** — no `genesistan_debug_fg_proof`, no frame counter
   display, no VDP census overlays. Debug infrastructure is not ported.

9. **Exception dump mode** — no `RASTAN_EXCEPTION_DUMPER_MODE`. Exceptions route to infinite
   hang stubs during bring-up.

10. **All of `apps/rastan/` modification** — the SGDK branch is not touched during rastan-direct
    bring-up. The two branches are fully independent.

11. **Full SAT staging buffer architecture** — the asm sprite path writes SAT directly to VDP
    during the tick. A separate VBlank-owned WRAM SAT buffer and DMA commit path (as described
    in the proposal document) is a post-Phase-4 refactor, not required for first sprite output.

12. **Flip-screen support** — DIP bit for flip screen is hardcoded OFF (factory default). No
    coordinate mirroring is implemented.

---

## 9. Single Final Implementation Order

One linear sequence. No branches. Cody executes these phases in strict order.

**Phase 1 — Boot stub + bare VBlank**

1. Replace `apps/rastan-direct/src/main_68k.s` with a complete main loop: wait for
   `vblank_frame_counter` increment, branch to wait loop (no arcade tick yet)
2. Replace `apps/rastan-direct/src/boot/boot.s` with full boot stub:
   - TMSS (existing code is correct, keep it)
   - Z80 halt: `move.w #0x0100, 0xA11100; move.w #0x0100, 0xA11200`
   - VDP register baseline: write all 19 registers (display OFF, Plane B=0xC000, Plane A=0xE000,
     Window OFF, SAT=0xF800, HScroll=0xF000, auto-increment=2, H40, 64×32, VInt ON, DMA ON)
   - VRAM clear: 32768 word writes of 0x0000 starting at VRAM address 0x0000
   - CRAM clear: 64 word writes of 0x0000
   - VSRAM clear: 40 word writes of 0x0000
   - Initialize `vblank_frame_counter` = 0
   - Enable interrupts: `move #0x2000, %sr`
   - Hang in wait loop (no arcade jump yet)
3. Add `apps/rastan-direct/src/vblank.s`:
   - `_VINT_handler`: register save, VDP status read, frame counter increment, register
     restore, RTE
   - Wire `_VINT_handler` into vector table at `boot.s` offset 0x000078
4. Update `link.ld` to place boot at 0x000000 and add vblank.s
5. Verify: ROM boots to black screen, frame counter increments at 60Hz in BlastEm debugger

**Phase 2 + Phase 5 — Arcade tick, tilemap commit, palette commit (implemented together)**

6. Add full opcode-patched arcade ROM copy to `link.ld` and build system (same relocated base,
   same `startup_title_remap.json` patch application via postpatch toolchain)
7. Add `genesistan_arcade_workram_words` WRAM allocation to `link.ld` or a new `wram.s`
8. In boot stub, add arcade workram init before jumping to arcade startup:
   - `lea genesistan_arcade_workram_words, %a5`
   - DIP1 mirror at A5+0x18 = 0x0001 (factory default active-high)
   - DIP2 mirror at A5+0x1C = 0x0000
   - BG dest_ptr at workram+0x10A0 = 0x00C00000 (**MANDATORY FIX 1**)
   - FG dest_ptr at workram+0x10A4 = 0x00C08000 (**MANDATORY FIX 1**)
9. Add TC0040IOC opcode patches to `startup_title_remap.json` / patch system:
   - DIP reads at 0x03AF7A and 0x03AF86 → immediate loads (factory defaults)
   - All reads from 0x390001, 0x390003 → `jsr _input_stub` (returns 0xFF = all inactive)
   - All reads from 0x390005 → suppress / return 0xFF
   - All reads from 0x390007 → `moveq #0xFF, %d0` + NOPs
   - All writes to 0x380000 → NOP
10. Add PC080SN tilemap hook bridges to trampoline (same as current SGDK branch, C-free):
    - PC080SN BG writes → redirect to WRAM `pc080sn_bg_buffer`
    - PC080SN FG writes → redirect to WRAM `pc080sn_fg_buffer`
11. Add `_input_stub` assembly stub returning 0xFF (all inputs inactive)
12. In boot stub: after workram init, perform one-time scene tile preload (arcade pc080sn tile
    ROM → VRAM slots 20–1023), then jump to arcade startup entry point
13. Update main loop: wait for frame counter → arcade tick → repeat
14. Add palette CLCS staging area (`genesistan_palette_clcs`) to WRAM allocation
15. Add palette hook to trampoline: arcade palette writes → `genesistan_palette_clcs`
16. Expand `_VINT_handler` per the exact commit order in Section 7:
    - Display OFF
    - `_commit_tilemap_bg`: CPU word stream, `pc080sn_bg_buffer` → VRAM 0xC000
    - `_commit_tilemap_fg`: CPU word stream, `pc080sn_fg_buffer` → VRAM 0xE000
    - `_commit_palette`: xBGR-555→Genesis conversion, 64 words → CRAM (if flag set)
    - Display ON
    - `_commit_scroll`: 4 words → VSRAM + HScroll table (unconditional, after display ON)
    - Frame counter increment
17. Verify: Plane B shows BG tile content with correct colors. Plane A shows FG tile content.

**Phase 3 — Scroll path bring-up**

18. Add opcode patches for scroll register writes (`movew %d0, 0x3C0000` sites at 0x03A012,
    0x03AF0A, 0x03AF14, 0x03AF4C, 0x03AF72, 0x03AF7E, 0x03B07E) → `jsr _scroll_stage`
19. Add `_scroll_stage` stub: read A5+0x10AE/0x10B0/0x10EC/0x10EE, apply negation and +8
    vertical bias, store to `staged_scroll_x_fg`, `staged_scroll_y_fg`, `staged_scroll_x_bg`,
    `staged_scroll_y_bg`
20. Add NOP patches for scroll clear writes at 0xC20000 and 0xC40000
21. Verify: no BlastEm warnings for unmapped writes to 0x3C0000; scroll staging words hold
    near-zero values in attract mode

**Phase 4 — Sprite path bring-up**

22. Port `genesistan_render_sprites_vdp_asm` and `genesistan_render_sprites_vdp_bridge` from
    `apps/rastan/src/startup_trampoline.s` to rastan-direct trampoline.s
23. Apply sprite DMA VRAM destination bug fix (**MANDATORY FIX 2**) in `.Lspr_dma_tile`:
    replace `swap %d2` with `lsr.l #14, %d2`
24. Wire all 15 sprite call site patches in `startup_title_remap.json` to
    `genesistan_render_sprites_vdp_bridge`
25. Verify: sprites appear on screen with correct pixel graphics. No blank/transparent sprites.
    No corruption of nametable tiles 0–84.

**Phase 6 — First recognizable attract-mode output**

26. Wire Genesis pad read stub to replace joystick read patches at 0x03A4A2, 0x03A4A8,
    0x03A778, 0x03A77E (reads Genesis `0xA10003`, translates D-pad/buttons to active-low byte)
27. Verify all four systems active simultaneously: BG+FG tilemap, palette, scroll staging,
    sprites
28. Run attract mode for full sequence cycle. Confirm recognizable Rastan scene visible,
    stable, advancing through attract frames.
29. First video bring-up milestone complete.

---

## 10. Final Verdict

| Task | Status |
|------|--------|
| First real video test target defined | YES — attract-mode BG layer with correct colors, no sprites required |
| Required arcade opcode paths identified | YES — tilemap ACTIVE, scroll ACTIVE (staging), sprites STUBBED, palette ACTIVE, per-frame execution ACTIVE |
| Ordered video bring-up phases defined | YES — 6 phases: boot, tilemap, scroll, sprites, palette, attract output |
| Prior audit fixes integrated | YES — DEST_PTR_NEVER_INITIALIZED mandatory in Phase 2; sprite DMA VRAM destination bug mandatory in Phase 4 |
| Required WRAM contracts defined | YES — 12 fields with addresses, values, timing, and consumers specified |
| Exact VBlank commit order defined | YES — display OFF → BG commit → FG commit → palette → display ON → scroll; one order, no alternatives |
| Out-of-scope items defined | YES — 12 explicitly excluded items including sound (entire plan), input gameplay, coins, service mode, diagnostic overlay |
| Single final implementation order | YES — 29 steps, linear, no branches |
| No implementation performed | YES |
