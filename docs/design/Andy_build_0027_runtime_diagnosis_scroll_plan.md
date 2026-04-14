# Andy — Build 0027 Runtime Diagnosis + Scroll Transition Plan

**Build context:** rastan-direct, Build 0027  
**BlastEm crash:** `machine freeze due to write to address C09EA0`  
**Exodus:** Cycles through multiple screens of garbled striped content before settling on solid pink  
**MAME trace:** `title_init_block@000200 count=0` — unchanged from Build 0026

---

## 1. C09EA0 Write Crash — Root Cause

**Address:** 0xC09EA0 = PC080SN base (0xC00000) + byte offset 0x09EA0

Within the PC080SN 64KB RAM layout:

```
0x0000–0x3FFF  BG tilemap     (64×64 tiles × 2 words × 2 bytes = 16 KB)
0x4000–0x41FF  BG rowscroll
0x8000–0xBFFF  FG tilemap     (same 16 KB)
0xC000–0xC1FF  FG rowscroll
```

0x09EA0 > 0x8000 and < 0xC000 → **FG tilemap area**.

FG offset: 0x9EA0 − 0x8000 = 0x1EA0.  
Word offset: 0x1EA0 / 2 = 0x0F50.  
FG tile entry (4 bytes each): 0x1EA0 / 4 = **tile 0x07A8 = 1960**, row 30, col 40 of the 64×64 FG map.

**The arcade code is writing live FG tilemap tile data at a visible screen position.**

This is NOT an init-time CLR.W. It is a deliberate tile-data write as part of the game's FG layer rendering. On real arcade hardware, it lands in PC080SN FG RAM. On Genesis, 0xC09EA0 is in the VDP address space with no valid VDP register at that offset → BlastEm freezes on the write bus cycle.

**No FG tilemap hook exists.** The existing `genesistan_hook_tilemap_plane_a` intercepts the arcade's BG strip producer at arcade PC 0x055968 and routes it to `staged_bg_buffer`. There is no equivalent intercept for the FG layer. FG tilemap writes go directly to the C-window address unchanged.

---

## 2. Exodus Screenshot Reconciliation

The Build 0027 Exodus output (multiple screens cycling before pink) is consistent with:

1. **BG hook is working** — `genesistan_hook_tilemap_plane_a` intercepts BG tilemap writes and routes them to `staged_bg_buffer` → `VRAM_PLANE_B_BASE` (0xC000). The garbled striped pattern is recognizable tilemap structure (row/column encoding visible as diagonal artifacts) — the tile data is real but tile indices are partially mismatched, palette is wrong, or scroll is 0 when it should not be.

2. **FG writes going raw to VDP data port** — Writes to 0xC08000–0xC0BFFF land at the VDP DATA port (0xC00000 mirrors in Genesis VDP space) as raw data words, corrupting VRAM with whatever FG tilemap entries the arcade is writing. The striped bands of garbage are the FG tile indices being interpreted as VRAM tile data.

3. **Scroll stuck at 0** — Both BG and FG scroll are 0 because the Build 0027 NOPs suppress the CLR.W writes without updating `staged_scroll_x_bg/fg` or `staged_scroll_y_bg/fg`. Since init_staging_state already zeros these, the NOPs have no visible effect on the first frame — but any non-zero scroll value written during gameplay will be silently dropped.

4. **Pink screen** — When the FG buffer write corruption fills Plane A with the wrong tile index pattern and the palette has no defined colors for those indices, the display defaults to the background color, which initializes to palette entry 0 of CRAM — whatever color was loaded there.

The cycling behavior (various screens before pink) is evidence the arcade state machine IS advancing and rendering multiple frames. This is MAME-verified behavior that MAME trace doesn't capture because `title_init_block` is not one of the traced execution ranges being entered — the arcade may be rendering attract content that precedes the title block, or the state machine is iterating through init phases.

---

## 3. Scroll NOP Scaffolding Assessment

**Build 0027 introduced four NOP patches:**

| Arcade PC | Instruction           | Target   | Replacement | Status     |
|-----------|-----------------------|----------|-------------|------------|
| 0x03ABBA  | CLR.W abs.l           | 0xC20000 | 3× NOP      | Scaffolding — MUST REPLACE |
| 0x03ABC0  | CLR.W abs.l           | 0xC40000 | 3× NOP      | Scaffolding — MUST REPLACE |
| 0x03B098  | CLR.W abs.l           | 0xC20000 | 3× NOP      | Scaffolding — MUST REPLACE |
| 0x03B09E  | CLR.W abs.l           | 0xC40000 | 3× NOP      | Scaffolding — MUST REPLACE |

**What the scaffolding breaks:** `vdp_commit_scroll` runs every VINT and writes the four
`staged_scroll_*` BSS variables to the VDP. If those variables are never updated from
arcade scroll writes, scroll is permanently 0,0. For the init paths these CLR.W writes
zero the scroll (same as BSS default), so no visible regression yet. But any future
MOVE.W scroll write during gameplay that goes to 0xC20000/0xC40000 will also need
translation — and if the NOP pattern is extended to those, scroll breaks permanently.

**What already exists (complete):**

`vdp_commit_scroll` in `main_68k.s:520` is fully implemented:

```asm
vdp_commit_scroll:
    move.l  #VRAM_HSCROLL_BASE, %d0
    bsr     vdp_set_vram_write_addr
    move.w  staged_scroll_x_fg, VDP_DATA    ; Plane A H-scroll
    move.w  staged_scroll_x_bg, VDP_DATA    ; Plane B H-scroll

    move.l  #0x40000010, VDP_CTRL           ; VSRAM write
    move.w  staged_scroll_y_fg, VDP_DATA    ; Plane A V-scroll
    move.w  staged_scroll_y_bg, VDP_DATA    ; Plane B V-scroll
    rts
```

Called from `_VINT_handler` every frame. The four staged scroll BSS variables are
declared at `main_68k.s:933–940` and zeroed in `init_staging_state`.

**The ONLY missing piece is updating these variables from arcade PC080SN writes.**

---

## 4. Rainbow Islands-Style Scroll Transition Design

### Scroll register mapping

| PC080SN address | PC080SN function       | Genesis destination   |
|-----------------|------------------------|-----------------------|
| 0xC20000        | yscroll_word_w offset 0 | `staged_scroll_y_bg` |
| 0xC20002        | yscroll_word_w offset 1 | `staged_scroll_y_fg` |
| 0xC40000        | xscroll_word_w offset 0 | `staged_scroll_x_bg` |
| 0xC40002        | xscroll_word_w offset 1 | `staged_scroll_x_fg` |

### Scroll value convention

From `pc080sn.cpp` `xscroll_word_w`: the chip internally stores `m_bgscrollx[n] = -data`.
The arcade game writes a positive scroll-right amount. The chip negates it as part of
its own scroll-left convention. On Genesis VDP, positive HSCROLL = plane shifts right
(same rightward direction). Therefore:

**Write the raw data value directly to the staged variable — no negation needed.**

The PC080SN negation was the chip's internal convention; we intercept at the write-to-
hardware level before that negation.

For V-scroll: `yscroll_word_w` similarly stores `m_bgscrolly[n] = -data` if `m_y_invert`
is set (Rastan does use y_invert per the MAME driver). Same reasoning applies — write
raw data value directly.

### Implementation: CLR.W redirect (the 4 existing NOP patches)

`CLR.W abs.l` is opcode `42B9` + 4-byte absolute address = 6 bytes.

Replace each NOP patch with a redirected CLR.W targeting the correct BSS variable.
The `{symbol:name}` substitution mechanism already used for input shadows applies here:

```json
"original_bytes": "42B900C20000"
"replacement_bytes": "42B9{symbol:staged_scroll_y_bg}"
```

This is identical machine code — same `CLR.W abs.l` instruction — with the target
address rewritten to the Genesis BSS variable instead of the PC080SN register.
It preserves condition code behavior, requires no new function, and uses the established
symbol substitution path.

| Arcade PC | Original            | Replacement                              |
|-----------|---------------------|------------------------------------------|
| 0x03ABBA  | `42B9 00C2 0000`    | `42B9 {symbol:staged_scroll_y_bg}`       |
| 0x03ABC0  | `42B9 00C4 0000`    | `42B9 {symbol:staged_scroll_x_bg}`       |
| 0x03B098  | `42B9 00C2 0000`    | `42B9 {symbol:staged_scroll_y_bg}`       |
| 0x03B09E  | `42B9 00C4 0000`    | `42B9 {symbol:staged_scroll_x_bg}`       |

Note: these CLR.W patches only cover BG scroll (offset 0). FG scroll (offset 1,
addresses 0xC20002 and 0xC40002) and non-zero scroll MOVE.W writes during gameplay
are future work — they will appear as new crash sites or incorrect scroll as the game
advances. Those will require JSR-to-handler patches with value-passing convention.

### Future: general MOVE.W scroll handlers

When gameplay scroll writes appear (MOVE.W Dn, 0xC20000 etc.), the handler contract is:

```asm
/* Called via JSR replacement of MOVE.W Dn, 0xC20000 */
/* Convention: scroll value in D0 (or whatever Dn the arcade used) */
genesistan_stub_yscroll_bg_write:
    move.w  %d0, staged_scroll_y_bg    /* store raw arcade value */
    rts
```

The exact source register depends on the arcade instruction being replaced and will be
determined per arcade PC when those crash sites appear.

---

## 5. FG Tilemap Hook — Architecture

### Why it is needed

The BG hook intercepts the arcade's BG strip producer at a single arcade PC (0x055968)
via a JSR redirect. FG tilemap data is generated by a separate strip producer at a
different arcade PC. Without intercept, FG writes go to 0xC08000–0xC0BFFF unchanged,
hitting Genesis VDP space → crash.

### Existing infrastructure

- `staged_fg_buffer` declared at `main_68k.s:945` — 2048 words, zeroed in `init_staging_state`
- `VRAM_PLANE_A_BASE = 0xE000` — cleared to 0 in `init_staging_state`, is the FG VRAM target
- `vdp_commit_bg_strips_if_dirty` writes `staged_bg_buffer` to `VRAM_PLANE_B_BASE` (BG = Plane B)
- FG = Plane A (`VRAM_PLANE_A_BASE = 0xE000`)
- **Missing:** FG hook function, `vdp_commit_fg_strips_if_dirty`, VINT call, remap.json redirect

### Arcade plane assignment

| Arcade layer | Genesis plane | VRAM base              | Staged buffer      |
|--------------|---------------|------------------------|--------------------|
| BG           | Plane B       | `VRAM_PLANE_B_BASE` (0xC000) | `staged_bg_buffer` |
| FG           | Plane A       | `VRAM_PLANE_A_BASE` (0xE000) | `staged_fg_buffer` |

`vdp_commit_scroll` writes FG scroll first (Plane A) then BG scroll (Plane B), confirming
this assignment.

### FG hook design

```
genesistan_hook_tilemap_plane_b   (name matches plane assignment: FG = Plane A misnamed;
                                   use genesistan_hook_tilemap_fg for clarity)
```

The hook structure mirrors `genesistan_hook_tilemap_plane_a` exactly, with:
- FG tilemap base: 0xC08000 (ARCADE_PC080SN_CWINDOW_BASE_FG = 0xC08000)
- FG window size: 0x4000 (same as BG)
- Destination buffer: `staged_fg_buffer` instead of `staged_bg_buffer`
- Same tile_vram_lut and attr_lut apply (same PC080SN tile encoding for both layers)
- bg_row_dirty: FG needs its own dirty bitmask — `fg_row_dirty` BSS word

`vdp_commit_fg_strips_if_dirty` mirrors `vdp_commit_bg_strips_if_dirty` with:
- Source: `staged_fg_buffer`
- VRAM target: `VRAM_PLANE_A_BASE` (0xE000)
- Dirty bitmask: `fg_row_dirty`

VINT handler addition (after existing `vdp_commit_bg_strips_if_dirty` call):
```asm
bsr     vdp_commit_fg_strips_if_dirty
```

### Finding the FG strip producer arcade PC

The BG hook was placed at arcade PC 0x055968, identified as the BG strip producer.
The FG strip producer is in the same general code area of the ROM. Cody must disassemble
the arcade ROM around 0x055968 to find the FG equivalent — it will have a similar
structure (writing 16 strip descriptors, advancing a destination pointer in the 0xC08000
range) and should be a peer routine to the BG producer.

**Precondition for Cody:** Identify the FG strip producer arcade PC before writing the
redirect patch. Verify by checking that the `original_bytes` at that PC contain a
`move.l` or similar that writes to an address in 0xC08000–0xC0BFFF.

---

## 6. Primary Blocker Classification

| Issue | Crash type | Severity | Affects MAME? |
|-------|-----------|----------|---------------|
| FG tilemap writes (0xC09EA0) | BlastEm write freeze | BLOCKER | No (MAME handles PC080SN writes) |
| Scroll NOPs (0xC20000/C40000) | Silent logic error | HIGH | No crash, wrong scroll |
| title_init_block=0 | State machine issue | UNDER INVESTIGATION | Yes |

The title_init_block=0 in MAME is a separate concern from the hardware write crashes.
MAME handles all PC080SN writes correctly and the game progresses to the Exodus rendering
stage, but never registers as having entered `title_init_block`. This may be because the
arcade state machine enters a rendering/attract loop that precedes the title block, or
because the traced range does not correspond to where the game currently executes.
Resolving FG hook and scroll first will produce a cleaner MAME trace for that diagnosis.

---

## 7. Single Root Cause

**The FG tilemap layer has no hook and no commit path.**

- BG: hooked at 0x055968, staged to `staged_bg_buffer`, committed to Plane B. Working.
- FG: no hook at any arcade PC, writes fall through to Genesis VDP → crash. Not working.

The scroll NOP issue is a consequence of the same gap — the correct fix (redirect to
staged vars) was not implemented when the crash was first encountered.

---

## 8. Cody Handoff Specification

### Task A — Replace scroll NOP scaffolding with symbol-redirected CLR.W

**File:** `specs/rastan_direct_remap.json`

Replace the four Build 0027 NOP patches with redirected CLR.W patches using `{symbol:}`
substitution. No changes to `main_68k.s` required. No new functions required.

Opcode_replace_count: 43 (unchanged — replacing entries in place, not adding).

| Arcade PC | Remove replacement  | New replacement                        |
|-----------|---------------------|----------------------------------------|
| 0x03ABBA  | `4E714E714E71`      | `42B9{symbol:staged_scroll_y_bg}`      |
| 0x03ABC0  | `4E714E714E71`      | `42B9{symbol:staged_scroll_x_bg}`      |
| 0x03B098  | `4E714E714E71`      | `42B9{symbol:staged_scroll_y_bg}`      |
| 0x03B09E  | `4E714E714E71`      | `42B9{symbol:staged_scroll_x_bg}`      |

original_bytes for all four remain unchanged.

**Verification:** After build, read the 6 bytes at each Genesis offset. Bytes 0–1 must
be `42B9`. Bytes 2–5 must be the address of the corresponding BSS variable (confirm
against `out/symbol.txt`).

### Task B — Implement FG tilemap hook

**Files:** `apps/rastan-direct/src/main_68k.s`, `specs/rastan_direct_remap.json`

1. Add `fg_row_dirty` as a BSS `.long` (mirror of `bg_row_dirty` for FG layer).
2. Declare `genesistan_hook_tilemap_fg` as `.global`.
3. Add constant:
   ```asm
   .equ ARCADE_PC080SN_CWINDOW_BASE_FG, 0x00C08000
   ```
4. Implement `genesistan_hook_tilemap_fg` — exact structural copy of
   `genesistan_hook_tilemap_plane_a` with these substitutions:
   - `ARCADE_PC080SN_CWINDOW_BASE_BG` → `ARCADE_PC080SN_CWINDOW_BASE_FG`
   - `ARCADE_PC080SN_DEST_BG_OFFSET` → `ARCADE_PC080SN_DEST_FG_OFFSET` (new constant, same relative offset pattern but for FG destination pointer in arcade workram — Cody must identify the FG destination pointer address in arcade workram by inspecting the FG strip producer code)
   - `staged_bg_buffer` → `staged_fg_buffer`
   - `bg_row_dirty` → `fg_row_dirty`
5. Implement `vdp_commit_fg_strips_if_dirty` — exact structural copy of
   `vdp_commit_bg_strips_if_dirty` with:
   - `bg_row_dirty` → `fg_row_dirty`
   - `VRAM_PLANE_B_BASE` → `VRAM_PLANE_A_BASE`
   - `staged_bg_buffer` → `staged_fg_buffer`
6. In `_VINT_handler`, add `bsr vdp_commit_fg_strips_if_dirty` immediately after the
   existing `bsr vdp_commit_bg_strips_if_dirty` call.
7. In `init_staging_state`, add `clr.l fg_row_dirty` alongside the existing
   `clr.l bg_row_dirty`.
8. In `remap.json`, add a redirect patch for the FG strip producer arcade PC (Cody
   must identify this PC first by disassembly — see precondition below).
   Pattern: `4eb9{symbol:genesistan_hook_tilemap_fg}` + padding NOPs, same structure
   as the BG hook entry at 0x055968.
9. Add `"genesistan_hook_tilemap_fg"` to `required_symbols` in `remap.json`.

**Precondition for Cody before writing any code:** Disassemble the arcade ROM around
0x055968 (BG strip producer). Find the FG strip producer (peer routine that writes to
the 0xC08000 range). Confirm its arcade PC and `original_bytes`. Record both in the
report. Do not proceed with hook implementation until the FG producer PC is confirmed.

---

## References

- `apps/rastan-direct/src/main_68k.s:197` — `genesistan_hook_tilemap_plane_a` (BG hook model)
- `apps/rastan-direct/src/main_68k.s:473` — `vdp_commit_bg_strips_if_dirty` (commit model)
- `apps/rastan-direct/src/main_68k.s:520` — `vdp_commit_scroll` (already complete)
- `apps/rastan-direct/src/main_68k.s:933` — staged_scroll BSS declarations
- `specs/rastan_direct_remap.json:99` — BG hook redirect patch (model for FG redirect)
- `docs/reference/mame/rastan/src/mame/taito/pc080sn.cpp` — yscroll/xscroll value convention
