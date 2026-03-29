# Title Screen State + Descriptor Flow Analysis

**Agent:** Andy (Forensic Analysis)
**Build investigated:** Rastan_276.bin
**Date:** 2026-03-28
**Mandate:** READ-ONLY forensic analysis. No code, spec, or build files were modified.

---

## 1. Purpose

Identify precisely where the current build's title screen execution sits relative to the
complete arcade title screen rendering path, why CREDIT and TILT appear while the full title
screen (logo sprites, text overlay, palette) does not, and define a single primary failure
point and validation approach.

Reference builds: analysis draws on research documents captured across Builds 235–276.
Current confirmed baseline: Rastan_276.bin.

---

## 2. Current Execution State

From runtime probe evidence (Build 272/273, documented in phase1_runtime_ordering_proof.md
and build271 docs):

| Variable            | Observed value    | Meaning                              |
|---------------------|-------------------|--------------------------------------|
| screen (0xE0FF6DCC) | 0x00000004        | SCREEN_FRONTEND_LIVE (confirmed)     |
| A5+0x0000           | 0x0001            | Major state = title/frontend cluster |
| A5+0x0002           | 0x0000 or 0x0001  | Substate (see below)                 |
| A5+0x0004           | 0x0000            | Step = 0                             |
| A5+0x002C           | 0x0000            | Timer gate (expired)                 |
| credits             | 0x0000            | No coins inserted (pre-coin)         |

A `state=5000/0100/0000` pattern also appears on frame 672 renderer hits. This is an
A5 context shift: `A5=0xE0FF004B` (off-by-one from normal `0xE0FF004C`), with
major-state=0x5000 (game-area state), substate=0x0100 — this is NOT the title-init path.
It appears as a secondary renderer call from a different A5-based state context. This
indicates the renderer bridge fires in multiple contexts, not only the title-init path.

The renderer bridge (`0x202B80`) is confirmed executing. The producer (`0x05A174`) has
been shown to execute at callsite 0x03AAEC (static), with runtime hit counts improving
after the Phase 1 ordering fix.

---

## 3. CREDIT Mapping (selector → descriptor)

### Selector value and table entry

- Selector: **D0 = 2**
- Dispatch entry: selector table at genesis 0x3BD92, entry[2] at genesis 0x3BD9A
- Resolved descriptor pointer: genesis 0x3BED4 (arcade 0x3BCBE + 0x200 + 22 shift)

### Descriptor fields (genesis Rastan_276.bin)

| Field        | Genesis address    | Value            | Meaning                         |
|--------------|--------------------|------------------|---------------------------------|
| D6 (dest)    | 0x3BED4–0x3BED7    | 0xE1000126       | Translated WRAM destination     |
| Attr word    | 0x3BED8–0x3BED9    | 0x0000           | Normal attribute                |
| Text payload | 0x3BEDA–0x3BEE3    | "CREDIT   \0"    | 9-char string + null terminator |

### Call chain

```
Coin-up detected (ongoing title loop, arcade 0x03B09C region)
  -> MOVEQ #2, D0                       (selector = 2)
  -> BSR to dispatch wrapper at 0x2027C0
     (wrapper: save A5 -> jsr 0x20034C -> restore A5 -> rts)
  -> text producer 0x20034C:
     - masks D0 to index: D1 = 0x0002
     - doubles: D1 = 0x0004, A0 = 0x0008 (scaled offset)
     - loads table base: A1 = 0x0003BD92
     - loads descriptor: A2 = 0x0003BED4 (entry[2])
     - passes destination-range check (D6=0xE1000126 >= 0xE0FFC84C baseline)
     - emits 9 tile words via VDP data port at 0x2004A2
  -> "CREDIT   " appears on screen
```

### Where 0x03B09C sits in the state machine

Arcade 0x03B09C is inside `title_init_block` (0x03B098–0x03C484). It is reached from
the **credit counter update sub-path** in the title loop, not from the title-init state-0
sequence (0x03AADE). This path fires whenever the game updates the credit display on the
title screen — it is the "CREDIT 0" / "CREDIT n" mechanism.

- The CREDIT call is part of the ongoing title-page rendering, NOT the initial
  state-machine setup (state-0 = substate-0). It executes in the per-frame title loop.
- The descriptor is translated, the producer is productive (confirmed by Build 246 proof:
  `HIT 2004A2 9`), and the text appears on screen.

---

## 4. TILT Mapping (selector → descriptor)

### Selector value and table entry

- Selector: **D0 = 14**
- Dispatch entry: selector table at genesis 0x3BD92, entry[14] at genesis 0x3BDC6
- Resolved descriptor pointer: genesis 0x3BFE2 (arcade 0x3BDCC + 0x200 + 22 shift)

### Descriptor fields (genesis Rastan_276.bin)

| Field        | Genesis address    | Value            | Meaning                              |
|--------------|--------------------|------------------|--------------------------------------|
| D6 (dest)    | 0x3BFE2–0x3BFE5    | 0xE0FFEDF2       | Translated WRAM dest (upper-left)    |
| Attr word    | 0x3BFE6–0x3BFE7    | 0x0000           | Normal attribute                     |
| Text payload | 0x3BFE8–0x3BFED    | "TILT\0"         | 4-char string + null terminator      |

### Call chain

```
Pre-coin title page ongoing loop (arcade 0x03ABCA region):
  -> BTST #2, (0x390007)         ; test tilt/service input bit
  -> BNE skip                    ; if bit 2 SET (normal), skip TILT
  -> bit 2 CLEAR = tilt active (A+B+C held on Genesis controller)
  -> MOVEQ #14, D0               (selector = 14)
  -> BSR to dispatch wrapper at 0x2027C0
  -> text producer 0x20034C:
     - resolves entry[14] -> descriptor at 0x3BFE2
     - D6 = 0xE0FFEDF2 (upper-left WRAM position)
     - emits "TILT" via VDP data port
  -> "TILT" appears upper-left
```

### State machine branch for TILT

TILT fires from 0x03ABCA which is in the **ongoing pre-coin loop** (state=1/substate=1 or
equivalently the per-frame title loop after state-0 init completes). This is a SEPARATE
branch from the full title-init sequence. TILT rendering does not depend on block-A/block-B
sprite descriptor content, only on the input register bit and the text producer path.

### Genesis trigger

`build_system_input_byte()` in startup_bridge.c (lines 132–149) clears bit 2 of
`genesistan_shadow_input_390007` when A+B+C are simultaneously held. A+B+C+Start triggers
TILT display (via arcade logic) AND Genesis hardware soft-reset (via SGDK/hardware) as two
independent effects of the same button combination.

---

## 5. Expected Title Screen Flow

From docs/research/title_screen_graphics_call_inventory.md, the full pre-coin title screen
rendering sequence (state=1/substate=0 init path) is:

### State machine entry

Required state: A5+0x0000 = 0x0001 (frontend/title major state),
A5+0x0002 = 0x0000 (substate = 0 = title-init), A5+0x002C = 0x0000 (timer expired).

### Init sequence (steps 1–13)

| Step | PC          | Action                                           | Produces                            |
|------|-------------|--------------------------------------------------|-------------------------------------|
| 1    | 0x03AAB8    | Timer gate + jump-table dispatch                 | Entry to title-init handler         |
| 2    | 0x03AADE    | BSR 0x03AFEA — set scroll/control flags          | A5+0x001E display mode set          |
| 3    | 0x03AAE2    | BSR 0x03AF5E — clear descriptor/staging blocks  | 0xE0FF11FE, 0xE0FF01BC zeroed       |
| 4    | 0x03AAE6    | BSR 0x03B06C — shared title graphics prep        | Text shadow + scroll initialized    |
| 5    | 0x03B076    | Fill 0xE0FFC84C with space cells (0x20, 0x800)  | Text cell region blanked            |
| 6    | 0x03B2AA/B0 | JSR 0x200DC2 x2 — push scroll to VDP           | VDP scroll registers updated        |
| 7    | 0x03B2B8    | Text producer D0=2 (CREDIT display)             | CREDIT text emitted to VDP          |
| 8    | 0x03B2BE    | BSR 0x03C4F8 — secondary text expansion         | Additional frontend text records    |
| 9    | 0x03AAEC    | JSR to renderer bridge (0x202B80 → 0x2005C4)   | Sprite/logo payload built & uploaded|
| 10   | 0x03AAF2    | JSR to logo producer (0x05A174)                 | Logo descriptor content built       |
| 11   | 0x03AAF8+   | Text producers D0=9,10/11,30,32                 | Multiple title-page strings         |
| 12   | 0x03AB0E    | BSR 0x05A62E — text source staging              | 0xE0FF6EDE path prepared            |
| 13   | 0x03AB20    | MOVEW #1, A5@(2) — state transition             | Substate advances to 1 (loop)       |

After step 13, the machine enters the steady-state pre-coin title loop (Step 14).

### Block A/B descriptor contract

- Block A (sprite/logo data): built by producer at 0x05A174 (step 10 above)
  - Expected content at 0xE0FF11FE: nonzero sprite descriptor entries after Step 10
  - Currently observed: all zeros (0x0000 × 8) — because Phase 2 not yet done
- Block B (object list): initialized by 0x059F76 fill (basic list structure)
  - Expected: `0x0080, 0, 0, 0` basic B-block entries at 0xE0FF01BC
  - Currently observed: `0x0080, 0000, 0000, 0000` — partial (Phase 1 baseline)

### Expected selector/descriptor coverage for full title screen

| Element              | Selector | Descriptor | Route                            |
|----------------------|----------|------------|----------------------------------|
| CREDIT display       | D0=2     | 0x3BED4    | 0x03B09C path (confirmed working)|
| TILT indicator       | D0=14    | 0x3BFE2    | 0x03ABCA path (confirmed working)|
| RASTAN logo text     | D0=20    | entry[20]  | 0x03BD5E → 0x20034C             |
| TAITO copyright      | D0=12    | entry[12]  | 0x03BD5E → 0x20034C             |
| Title strings D0=9   | D0=9     | entry[9]   | 0x03AAF8 → 0x03BD5E             |
| Title strings D0=10/11 | D0=10/11| entry[10/11]| 0x03AB0A → 0x03BD5E           |
| Title strings D0=30/32 | D0=30/32| entry[30/32]| 0x03AB14/1A → 0x03BD5E       |
| RASTAN logo sprites  | N/A      | Block A    | 0x05A174 producer + 0x2005C4    |
| Score/HUD digits     | N/A      | 0x03BA14   | Digit descriptor writer          |

---

## 6. Current vs Expected Comparison

### State machine path — CORRECT

The current build IS running the correct state machine path. Evidence:
- `screen=0x00000004` (SCREEN_FRONTEND_LIVE confirmed in runtime probes)
- `state=0001/0000/0000` confirmed in multiple frame captures (Build 271 proof,
  build271_logo_proof.txt, title_screen_graphics_call_inventory.md Section 1)
- Renderer bridge (`0x202B80`) fires with correct A5 context
- Static ordering: Patch A (producer at 0x03AAEC) precedes Patch B (renderer at 0x03AAF2)

The build is NOT trapped in a coin-entry state or wrong-branch variant. CREDIT appears
because the CREDIT update path (0x03B09C inside title loop) fires correctly, and TILT
appears because the tilt input check (0x03ABCA in the pre-coin loop) fires correctly.
Both confirm real arcade state machine execution.

### What is currently missing vs expected

| Title screen element     | Expected behavior                  | Current behavior                      |
|--------------------------|------------------------------------|---------------------------------------|
| CREDIT text              | Appears after coin-up              | CONFIRMED WORKING (Build 276)         |
| TILT text                | Appears on tilt input              | CONFIRMED WORKING (Build 276)         |
| RASTAN logo sprites      | Sprite pixels visible (block-A)    | NOT VISIBLE — block-A remains zero    |
| TAITO / copyright text   | Text visible (D0=12 path)          | UNKNOWN — depends on palette/CRAM     |
| Title strings (D0=9+)    | Text visible                       | UNKNOWN — depends on palette/CRAM     |
| Scroll registers         | Set by scroll sync calls           | Partially set (VDP sync implemented)  |
| Palette / CRAM           | Non-zero CRAM before text writes   | CRAM zero in Build 246 pre-exception  |

### Why CREDIT and TILT work but full title does not

CREDIT and TILT both use the **text producer path** (0x20034C) with translated descriptor
D6 values that pass the destination-range check at 0x2003EC. These paths require:
1. Producer 0x20034C to execute — CONFIRMED
2. Descriptor D6 translated from arcade C-window to WRAM — CONFIRMED via window_rewrite_rules
3. VDP data writes at 0x2004A2 to fire — CONFIRMED (Build 246: `HIT 2004A2 9`)
4. CRAM non-zero for text pixels to be visible — status depends on palette init

Logo sprites additionally require block-A descriptor content, which depends on:
1. Producer 0x05A174 building block-A content (currently returns immediately after zeroing)
2. Renderer 0x2005C4 consuming block-A and producing VDP SAT entries
3. Tile data loaded into VRAM for logo tile indices

The fundamental asymmetry: text producer path executes and writes tile words to VDP, but
sprite/logo producer path (0x05A174) produces no block-A content because the block-A
content-building subroutines have not yet been translated for Phase 2.

---

## 7. Identified Failure Point

### Primary failure: block-A sprite descriptor content never built (Phase 2 not yet done)

**Single primary failure**: The logo/sprite producer at 0x05A174 runs (confirmed) but
returns without building any block-A content. Block-A (descriptor words at 0xE0FF11FE)
remains all zeros after every producer call.

Evidence:
- build271 proof: `A@FF11FE=0000 0000 0000 0000` even after producer fires
- AGENTS_LOG (Phase 1 execution results): "Block-A remains zero; logo sprites not visible.
  Expected for Phase 1 baseline."
- D-7 revert (Phase 1 closure): the block-A builder calls were in the D-7 trampoline and
  were removed as Phase 1 scaffolding. They are deferred to Phase 2.
- D-5 reverts: descriptor attr fields restored to 0x0000 (real arcade value); the forced
  0x0080 scaffolding that would have triggered the renderer's non-empty check was removed.

### Is this wrong state or missing content?

The state machine path is CORRECT (see Section 6). The producer and renderer execute in
correct order (producer before renderer — Patch A and B confirmed). The failure is NOT:
- Wrong state machine branch
- Wrong selector value
- Descriptor address translation error (those are resolved in Build 246+)
- Call ordering error (resolved in Phase 1)

The failure IS:
- Block-A content has never been built by translated Phase 2 code
- The producer's content-building subroutines (originally called via D-7 trampoline) are
  deferred to Phase 2
- With block-A zero, the renderer produces no visible sprite payload

### Secondary factor: CRAM zero

From Build 246: `cram_nonzero=0/64` at frames 650 and 800. Text written to VDP plane
nametable is invisible if CRAM is all zero (no palette). This explains why even the
CREDIT/TAITO/copyright text is invisible in pre-exception frames despite the producer
firing and emitting tile words. CREDIT became visible in Build 276 — this implies palette
initialization improved between Build 246 and 276. Further validation of current CRAM state
on Build 276 would confirm whether remaining text strings are blocked by palette or by
missing producer calls.

---

## 8. Validation Plan

### 8.1 Confirm block-A producer currently produces zero output

**Tool**: MAME Genesis harness `tools/mame/run_genesis_trace_wsl.sh`
**ROM**: `dist/Rastan_276.bin`
**Probe**: Lua script that taps 0x05A174 (producer entry) and 0xE0FF11FE (block-A base),
reading 8 words at 0xFF11FE after each producer hit.

Expected result: block-A remains `0000 0000 0000 0000` × 4 after every producer call.

```lua
-- Pseudo-probe
cpu = manager.machine.devices[":maincpu"]
tap_addr = 0x05A174
cpu.debug:watch(tap_addr, "execute", function()
    local ba = {}
    for i = 0, 7 do ba[i] = cpu.spaces["program"]:read_u16(0xE0FF11FE + i*2) end
    print("BLOCK_A: " .. table.concat(ba, " "))
end)
```

Pass condition: all 8 words = 0x0000 every frame, confirming Phase 2 work is needed.

### 8.2 Confirm palette (CRAM) state in Build 276

**Tool**: MAME Genesis harness
**Probe**: Lua script reading VDP CRAM after `load_arcade_palette()` call (confirmed in
SCREEN_FRONTEND_LIVE loop), check nonzero count.

```lua
-- Read all 64 CRAM words and count nonzero
local vdp = manager.machine.devices[":vdp"]
local nonzero = 0
for i = 0, 63 do
    if vdp.palette[i] ~= 0 then nonzero = nonzero + 1 end
end
print("CRAM nonzero: " .. nonzero .. "/64")
```

Pass condition: nonzero > 0 means palette is being loaded and text/tiles should be visible
if correct tile data is present.

### 8.3 Confirm full title-init step sequence executes

**Tool**: MAME Genesis harness + Exodus breakpoints
**Probe**: Hit counters on key PCs from the title-init sequence:
- 0x03AADE (state-0 entry)
- 0x03B076 (text shadow clear)
- 0x03B2B8 (D0=2 CREDIT call from title init — distinct from 0x03B09C coin handler)
- 0x03AAEC (producer slot)
- 0x03AAF2 (renderer slot)
- 0x03AB20 (substate transition to 1)

Expected: each PC fires in order (AADE before B076 before B2B8 before AAEC before AAF2
before AB20) within a single title-init frame.

### 8.4 Confirm text producer executes for D0=9,10,11,30,32

**Tool**: MAME Genesis harness
**Probe**: Tap 0x03BD5E (dispatch entry) and log D0 value at each hit.

Expected D0 values in a complete title-init pass: 2, 9, 10 or 11, 30, 32.
Absence of any of these indicates that step in the init sequence is not firing.

### 8.5 Confirm SAT/sprite payload is zero until Phase 2

**Tool**: MAME Genesis harness
**Probe**: After renderer bridge executes (tap 0x202B80), read VDP SAT region
(VRAM 0x0000, first 8 sprite entries × 8 bytes = 64 bytes) for nonzero words.

Expected: SAT is zero (no logo sprites rendered). Pass condition for Phase 1 baseline.

### 8.6 Validate tile data in VRAM for text glyph indices

**Tool**: MAME Genesis harness
**Probe**: After text producer writes tile word 0x0014 (first CREDIT glyph from Build 246
proof), check VRAM at the tile slot that corresponds to glyph index 0x14, confirm
tile data is loaded (nonzero).

Pass condition: tile data present means glyph is renderable given correct palette.

---

## 9. Final Conclusion

The current build (Rastan_276.bin) is executing the correct arcade title screen state
machine path (state=0x0001/substate=0x0000, SCREEN_FRONTEND_LIVE). CREDIT and TILT appear
because:

1. The descriptor translation for these two records (D6 fields rewritten from arcade
   C-window addresses to Genesis WRAM addresses) was applied in Build 246 and remains
   correct in Build 276.
2. The text producer at 0x20034C executes, passes destination-range checks, and writes
   tile words to the VDP for both descriptors.
3. Both strings draw from real arcade-original descriptors — no C-code scaffolding.

Full title screen graphics (RASTAN logo sprites, complete text overlay, full palette) are
absent because:

1. **Block-A sprite descriptor content has never been built** — this is the primary
   failure. The producer at 0x05A174 runs but produces no block-A content because the
   block-A content-building subroutines (deferred from Phase 1 as scaffolding) are not
   yet translated for Phase 2.
2. Palette (CRAM) was confirmed zero in Build 246; current state in Build 276 requires
   re-measurement, but improved visible text (CREDIT) suggests partial palette fix.

The correct fix path is Phase 2: translate the block-A content-building logic inside
0x05A174 so that real sprite descriptor entries are produced, enabling the renderer bridge
to upload a populated SAT payload to the Genesis VDP.

---

The current build executes real arcade descriptor paths, but is in an incorrect state/selector path preventing full title screen rendering.
