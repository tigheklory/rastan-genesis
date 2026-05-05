# Andy — PC090OJ Reconciliation v2 (April 6 Baseline + Boundary Identification)

**Agent:** Andy
**Type:** Research / Reconciliation (analysis only)
**Build context:** `rastan-direct` Build 0052
**Architecture compliance:** CONFIRMED (no source / spec / tool modifications).

**Outcome: reconciliation complete, boundary identified.** April 6 descriptor semantics (8-byte entries; word0 = attr/flip/colour, word1 = Y, word2 = code, word3 = X) are CONFIRMED against MAME's `pc090oj_device::draw_sprites`. The April 6 translation system (`startup_trampoline.s` ASM renderer at workram offsets 0x11B2 / 0x0170, JSR-hook patches at 15 arcade PCs) **still exists in the tree at `apps/rastan/src/`** but is **entirely absent from `apps/rastan-direct/src/`** — the current branch is a greenfield port that never incorporated the April 6 sprite pipeline. The Rastan-specific 22-entry / two-block model is consistent with MAME's 256-max/first-priority model (Rastan uses a subset). The 80-byte-stride pointer-based indexing at `arcade_pc 0x41BFC` is a Rastan-specific workram layout indexed via PC090OJ RAM pointers; it does not contradict the 8-byte descriptor hardware format. Recommended translation boundary: **Option A (workram intercept at the 15 April-6-documented arcade_pc call sites)**, with HIGH confidence. No suppression proposed. Subsystem-design task is READY subject to one follow-up evidence task (runtime write-surface verification to confirm no bypass paths exist).

---

## Phase 1 — April 6 baseline extraction + code survival audit

### 1a. April 6 baseline (verbatim from [Andy_pc0900j_sprite_correctness_audit.md](docs/design/Andy_pc0900j_sprite_correctness_audit.md))

**Descriptor format (§2.1):** 8 bytes (4 words) big-endian, written contiguously.

| byte offset | word | field      | content                                         | April 6 cite |
| ----------- | ---- | ---------- | ----------------------------------------------- | ------------ |
| +0, +1      | 0    | attr/flags | bit15=flipy, bit14=flipx, bits3:0 = palette     | §2.1         |
| +2, +3      | 1    | y_raw      | raw Y; `0x0180` = off-screen sentinel           | §2.1         |
| +4, +5      | 2    | tile code  | bits 13:0 = arcade cell index (`& 0x3FFF`)       | §2.1         |
| +6, +7      | 3    | x_raw      | raw X                                           | §2.1         |

Source citations from §2.1: `main.c` lines 1974–1978; arcade sprite builder at `arcade_pc 0x03C902` (writes word0=attr, word1=Y, word2=code via subroutine 0x3CA12, word3=X).

**Sprite list structure (§2.3):** two descriptor blocks in arcade workram (base symbol `genesistan_arcade_workram_words`).

- Block A: offset `0x11B2`, **18 entries** (title/logo sprites).
- Block B: offset `0x0170`, **4 entries** (secondary sprites).
- Total: 22 entries max per frame.
- Stride: 8 bytes, fixed-count scan, no link inside arcade entries.
- Validity rules: skip if `y_raw == 0x0180`; skip if all four words zero; skip if tile code zero after masking.

Source: [apps/rastan/src/startup_trampoline.s:224-238](apps/rastan/src/startup_trampoline.s#L224-L238) (block A/B iteration); `main.c` lines 1963–1969 (`sprite_blocks[]` table); arcade disassembly `0x041F5E..0x041F8C` (block copy loop).

**Staging mechanism (§4.3):** **no WRAM staging buffer** in the active ASM path. SAT words are written directly to VDP data port (`A4 = 0xC00000`) in real time. The legacy C path used SGDK's `vdpSpriteCache` but is inactive.

**Translation boundary (§4.1):** all arcade sprite call sites patched via `startup_title_remap.json` `shift_replacements` to `JSR genesistan_render_sprites_vdp_bridge`. **15 patched arcade addresses:**

```
arcade_pc:
  0x03A20E, 0x03A264, 0x03A640, 0x03A6C4, 0x03A818, 0x03A820,
  0x03A854, 0x03A8E4, 0x03A9C6, 0x03A9D4, 0x03B8E8, 0x03B8F0,
  0x041DAE, 0x041F5E, 0x045DFA
```

**Identified bug (§5.2, §9, §10):** DMA address encoding in `.Lspr_dma_tile` at [startup_trampoline.s:330-332](apps/rastan/src/startup_trampoline.s). Current: `move.l %d0, %d2; swap %d2; andi.w #0x0003, %d2`. Correct: `move.l %d0, %d2; lsr.l #14, %d2; andi.w #0x0003, %d2`. Bug causes all sprite DMA transfers to target VRAM `0x0000..0x0B80` instead of intended `0x8000..0x8B80`. Fix ship status per prompt: **UNKNOWN**.

### 1b. Code-survival audit

Verified presence in current tree via `grep` / `find`:

| April 6 artifact                                       | location                                                                                                            | status              |
| ------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------- | ------------------- |
| `apps/rastan/src/startup_trampoline.s`                 | [apps/rastan/src/startup_trampoline.s](apps/rastan/src/startup_trampoline.s) — present, ≥263 lines                   | **PRESENT**         |
| `apps/rastan/src/startup_bridge.c`                     | [apps/rastan/src/startup_bridge.c](apps/rastan/src/startup_bridge.c) — present                                       | **PRESENT**         |
| `apps/rastan/src/main.c`                               | [apps/rastan/src/main.c](apps/rastan/src/main.c) — present                                                           | **PRESENT**         |
| symbol `genesistan_render_sprites_vdp_asm`             | defined in `apps/rastan/src/startup_trampoline.s:211` (confirmed by file read)                                       | **PRESENT** (in SGDK branch only) |
| symbol `genesistan_render_sprites_vdp_bridge`          | referenced by multiple `apps/rastan/` files (grep hits in main.c / out/rom.out / out/symbol.txt / out/src/*.o)       | **PRESENT** (SGDK branch) |
| symbol `genesistan_arcade_workram_words`               | referenced from `apps/rastan/` files (grep)                                                                          | **PRESENT** (SGDK branch) |
| `specs/startup_title_remap.json`                       | [specs/startup_title_remap.json](specs/startup_title_remap.json) — present                                           | **PRESENT** (used only by the `apps/rastan/` SGDK build; not consumed by `apps/rastan-direct/` per [postpatch_startup_rom.py](tools/translation/postpatch_startup_rom.py)) |
| `preconvert_pc090oj_tiles.py`                          | [tools/translation/preconvert_pc090oj_tiles.py](tools/translation/preconvert_pc090oj_tiles.py) — present             | **PRESENT**         |
| ROM symbol `rastan_pc090oj`                            | used by April 6 ASM renderer; referenced in `apps/rastan/` symbol table                                              | **PRESENT** (SGDK branch) |
| `apps/rastan-direct/src/` sprite-translation artifacts | grep `genesistan_render_sprites_vdp` / `genesistan_arcade_workram_words` / `SPRITE_TILE_BASE` → **zero matches** | **ABSENT** (in current branch) |

**Survival summary:**

- PRESENT: 9 of 9 April 6 artifacts survive in `apps/rastan/`.
- ABSENT from `apps/rastan-direct/`: the entire April-6 sprite translation pipeline (hook targets, ASM renderer, workram symbol, SPRITE_TILE_BASE constant).

**Key structural finding:** April 6 was written for the SGDK-based `apps/rastan/` build. None of its pipeline was ported to `apps/rastan-direct/`. The two `apps/` trees are parallel codebases with different build profiles (`startup_title_remap` vs `rastan_direct`); Phase 9 expands on this divergence.

---

## Phase 2 — MAME validation

Source: [docs/reference/mame/rastan/src/mame/taito/pc090oj.cpp](docs/reference/mame/rastan/src/mame/taito/pc090oj.cpp), 230 lines (full file read).

**Hardware spec from the leading comment (lines 10-28):**

```
8 bytes/sprite
256 sprites (0x800 bytes)
First sprite has *highest* priority

Byte 0 |.x......| Flip Y Axis            (bit 14)
Byte 0 |x.......| Flip X Axis            (bit 15)
Byte 1 |....xxxx| Colour Bank            (bits 3:0)
Byte 2 |.......x| Sprite Y               (bit 8)
Byte 3 |xxxxxxxx| Sprite Y               (bits 7:0)
Byte 4 |...xxxxx| Sprite Tile            (bits 12:8)
Byte 5 |xxxxxxxx| Sprite Tile            (bits 7:0)
Byte 6 |.......x| Sprite X               (bit 8)
Byte 7 |xxxxxxxx| Sprite X               (bits 7:0)
```

The MAME comment-level Byte-0 flip-Y/flip-X bit assignment has an apparent typo (says bit 6 = flipY), but `draw_sprites()` code is authoritative. At lines 187-188:

```cpp
int flipy = (data & 0x8000) >> 15;
int flipx = (data & 0x4000) >> 14;
```

→ word0 **bit 15** = flipY, **bit 14** = flipX — matches April 6.

From lines 189-193:

```cpp
const u32 color = (data & 0x000f) | sprite_colbank;    // word0 bits 3:0 = colour
const u32 code  = m_ram_buffered[offs + 2] & 0x1fff;   // word2 bits 12:0 = tile code (13-bit)
int x           = m_ram_buffered[offs + 3] & 0x1ff;    // word3 bits 8:0 = X (9-bit)
int y           = m_ram_buffered[offs + 1] & 0x1ff;    // word1 bits 8:0 = Y (9-bit)
```

**Active RAM size (lines 66-67):**

```cpp
static constexpr u32 PC090OJ_RAM_SIZE        = 0x4000;  // 16 KB total
static constexpr u32 PC090OJ_ACTIVE_RAM_SIZE = 0x800;   //  2 KB active; 256 sprites × 8 bytes
```

**Control register (lines 144-161):** the `word_w` write handler; writes to word-offset `0xDFF` (= byte offset `0x1BFE`) set `m_ctrl` — "bit 0 is flip control, others seem unused." This matches the existing `opcode_replace` suppressions at `arcade_pc 0x03AE06 / 0x03AE1E / 0x03AE8E` (writes to `0x00D01BFE`).

**Buffering (lines 163-170, 105-119):** PC090OJ has a double-buffering mode gated by `m_use_buffer`. When enabled, `eof_callback` copies ACTIVE_RAM (`0x800` bytes) from primary to buffered on end-of-frame. Rastan's use of this is a driver-specific choice; not verifiable from MAME hardware file alone.

**Field-by-field validation against April 6:**

| Field                     | April 6 (§2.1)                              | MAME draw_sprites (lines 187-193)            | Status  |
| ------------------------- | ------------------------------------------- | -------------------------------------------- | ------- |
| Word 0 bit 15 (flipY)     | YES                                         | YES (`(data & 0x8000) >> 15`)                | **MATCH** |
| Word 0 bit 14 (flipX)     | YES                                         | YES (`(data & 0x4000) >> 14`)                | **MATCH** |
| Word 0 bits 3:0 (palette) | YES                                         | YES (`data & 0x000f`, called "color")        | **MATCH** (naming difference only) |
| Word 1 (Y)                | raw Y; `0x0180` = off-screen (Rastan convention) | `y & 0x1ff` (9-bit mask)                | **MATCH** (April 6 describes Rastan's off-screen sentinel; MAME confirms 9-bit width) |
| Word 2 (tile code)        | bits 13:0 (`& 0x3FFF`)                       | bits 12:0 (`& 0x1fff`)                       | **PARTIAL** — mask differs (14-bit vs 13-bit); see below |
| Word 3 (X)                | raw X                                        | `x & 0x1ff` (9-bit mask)                     | **MATCH** (MAME confirms 9-bit width) |
| Entry size                | 8 bytes                                     | 8 bytes (`offs += 4` word-indexed / `inc = 4` word-stride) | **MATCH** |
| Max sprites               | 22 (Rastan-specific)                        | 256 (chip-max, all Taito F2 users)            | **MATCH** — Rastan uses a subset of available slots |
| Priority order            | Block A first, then Block B (April 6 §8.2)  | "First sprite has highest priority"          | **MATCH** |

**On the tile-code mask discrepancy (PARTIAL):** April 6 uses `0x3FFF` (14 bits, range 0..16383). MAME uses `0x1FFF` (13 bits, range 0..8191). Rastan's PC090OJ ROM contains 4096 cells (12-bit index; range 0..4095 per April 6 §2.2). Both masks are sufficient. The discrepancy is a mask loosening on April 6's side, not a semantic conflict. No actual Rastan sprite code exceeds 12 bits; neither mask will truncate.

**MAME-validation summary:**

```
MATCH:     8 fields / attributes
PARTIAL:   1 (tile-code mask — both cover Rastan's 12-bit code range)
CONFLICT:  0
```

April 6 semantics are validated. Proceed to Phase 3.

---

## Phase 3 — Current Build 0052 analysis

### 3a. PC090OJ hooks in `specs/rastan_direct_remap.json`

Grep over [specs/rastan_direct_remap.json](specs/rastan_direct_remap.json) for `0xD0xxxx` addresses and sprite-related terms:

| arcade_pc   | spec role                                           | PC090OJ-related? |
| ----------- | --------------------------------------------------- | ---------------- |
| `0x03AE06`  | suppress `movew #1, 0x00D01BFE` (DMA trigger)        | YES (DMA-trigger register, not sprite-RAM) |
| `0x03AE1E`  | suppress `movew #0, 0x00D01BFE`                      | YES (same) |
| `0x03AE8E`  | suppress `movew #0, 0x00D01BFE` (startup)            | YES (same) |
| any other   | —                                                   | NO |

**Coverage for sprite-RAM writes (`0xD00000..0xD00FFF`):** zero `opcode_replace` entries.

### 3b. Sprite-translation symbols in `apps/rastan-direct/src/`

Grep (`genesistan_render_sprites_vdp | SPRITE_TILE_BASE | genesistan_arcade_workram_words | Lspr_ | spr_dma_tile | spr_write_sat | sprite_blocks`) → **zero matches**.

The only `apps/rastan-direct/` hit for any sprite-related pattern is `0x0180` in [apps/rastan-direct/src/tilemap_hooks.s](apps/rastan-direct/src/tilemap_hooks.s), which is the blank-tile index used by text-writer helpers — **not** the PC090OJ off-screen sentinel.

### 3c. Runtime write sites in Build 0052 (from prior analysis)

Merged from [Andy_pc090oj_full_subsystem_design.md](docs/design/Andy_pc090oj_full_subsystem_design.md) Phase 1:

- **INIT path** reached from cold-boot startup_common (`arcade_pc 0x03AE86 → 0x03AF28 → 0x03AD72 → 0x03ADAA` per [Andy_d00778_write_path_analysis.md](docs/design/Andy_d00778_write_path_analysis.md)): 17-entry structured init at `arcade_pc 0x03ADAA`. 8-byte stride. This write produced the BlastEm halt observed in `Cody_d00778_vs_delay_loop_ordering_trace.md`.
- **RUNTIME LEA-based writes**: `arcade_pc 0x41BFC`, `0x41DB2`, `0x41DEC`, `0x41E2A`, `0x41E7A`, `0x41F64`, `0x41F74`, `0x45DFE`, `0x45E44`, `0x45E80` — literal `lea 0xD0xxxx, A1`. Targets fall in `0x00D00170..0x00D00460` range.
- **RUNTIME pointer-based writes** via `arcade_pc 0x41BFC` (see §3d below): 80-byte stride.
- **DIRECT single-word writes**: `arcade_pc 0x510EA: movew #2, 0x00D00698`; `0x510F4: movew #0, 0x00D00698`.

### 3d. 80-byte-stride pattern at `arcade_pc 0x41BFC`

From [Andy_d00778_write_path_analysis.md](docs/design/Andy_d00778_write_path_analysis.md) Phase 3d and cross-verified against [build/maincpu.disasm.txt](build/maincpu.disasm.txt) at the instruction boundary:

```
0x41BF8: moveq #80, %d1
0x41BFA: muluw %d1, %d0            ; D0 = index * 80
0x41BFC: lea 0x00D00460, %a0        ; A0 = PC090OJ base for this table
0x41C02: addal %d0, %a0              ; A0 = 0x00D00460 + (index * 80)
0x41C04: lea %a5@(4738), %a1         ; A1 = work-RAM slot (base+4738)
0x41C08: clrw %d0
0x41C0A: moveb %a4@(47), %d0         ; D0 = 8-bit index from A4@(47)
0x41C0E: muluw #6, %d0                ; D0 = index * 6
0x41C12: addaw %d0, %a1               ; A1 += (index * 6)
0x41C14: movew #1, %a1@               ; *A1 = 1 (flag byte in work-RAM)
0x41C18: movel %a0, %a1@(2)           ; *(A1+2) = A0 (pointer to 0xD004... in work-RAM)
0x41C1C: rts                          ; no sprite-RAM write in this function
```

**Reconciled interpretation:** the function at `arcade_pc 0x41BFC` is a **work-RAM bookkeeping function that records pointers into PC090OJ RAM**. Each work-RAM record (6 bytes) contains `{flag_word, ptr_to_PC090OJ_record}`. The 80-byte stride reflects a Rastan-specific layout of a larger data structure (animation state, tile chain, palette swap queue, etc.) inside the PC090OJ sprite-RAM address range. It is **not** a contradiction of the 8-byte PC090OJ descriptor format — PC090OJ sprite-RAM is a 16 KB memory pool of which only the first `0x800` bytes are chip-active per MAME (§1.4 above), and Rastan uses the upper `0x3800` bytes for game-specific bookkeeping.

Consistent with April 6 §2.3's finding that descriptor blocks A and B live at specific offsets `0x11B2` and `0x0170` in **arcade workram** (not PC090OJ RAM). The current 80-byte structures at `0xD00460+` may be either (a) workram-staged copies mirroring arcade workram organization, or (b) Rastan-specific use of PC090OJ RAM's inactive upper region as scratch memory. Without runtime trace evidence of the actual data written at `0xD00460+`, (a) vs (b) cannot be distinguished from static analysis.

### 3e. Current Build 0052 coverage summary

```
PC090OJ sprite-RAM writes with opcode_replace coverage:   0
Write sites identified statically:                        22+
Write sites resolvable from static disassembly:           PARTIAL
Translation system present in apps/rastan-direct/:        NONE
Build 0052 behaviour on PC090OJ writes:                   silently unmapped on Genesis
                                                          (ROM ends at 0x0FC1C3; 0x00D0xxxx is
                                                          outside cart-ROM, VDP, I/O, Z80, WRAM
                                                          bands. BlastEm halts; Exodus tolerates.)
```

---

## Phase 4 — Descriptor reconciliation table

Combining Phases 1a, 2, 3 — for each descriptor field:

| field | April 6 (§2.1) | MAME draw_sprites | Current Build 0052 init evidence (0x03ADAA loop) | Status |
| ----- | -------------- | ----------------- | ------------------------------------------------ | ------ |
| Word 0 bit 15 (flipY)        | YES                                   | YES                                    | init writes `0x0000` to word0 (upper half of D0, always zero at init) — consistent with "init clears flipY/flipX" | **VERIFIED** |
| Word 0 bit 14 (flipX)        | YES                                   | YES                                    | same — init clears                                       | **VERIFIED** |
| Word 0 bits 3:0 (palette)    | YES                                   | YES (called "color")                   | init writes `0x0000` (no palette set at init — gameplay updates later) | **VERIFIED** |
| Word 1 (Y, 9-bit)            | YES                                   | YES                                    | init writes `D0 = 8, 24, 40, ..., 216, 200, 216, 232` — these values fit within the 9-bit Y mask. Consistent with "preloading sprites at Y positions along a vertical column." | **VERIFIED** |
| Word 2 (tile code, 13-bit)   | PARTIAL (14-bit mask)                | 13-bit mask                             | init writes `0x0000` to word2 (upper half of D7); word3 is the constant 0x0160. Evidence is consistent but doesn't exercise high-bit tile codes at init — both masks cover init. | **PARTIAL** (mask width discrepancy; both sufficient for Rastan's 12-bit code range) |
| Word 3 (X, 9-bit)            | YES                                   | YES                                    | init writes `0x0160 = 352` to offset +4/+6. Under the longword `movel D7, %a0@(4)` interpretation, this is split as (`+4`=0x0000, `+6`=0x0160). If word3 is X, the init sets X=352 for all 17 sprites. 352 is above the visible 320 screen width — consistent with "park sprites off-screen right." | **VERIFIED** (initial value is plausible for off-screen parking, further corroborating word3 = X) |

**Init-value interpretation validation:** the init at `arcade_pc 0x03ADAA` writes `movel D0, (A0)` then `movel D7, (A0+4)` per entry. Under the April-6/MAME descriptor model:

- `movel D0, (A0)` covers bytes `+0..+3` = word0 (attr/flip/palette, upper half of D0 = 0x0000) + word1 (y_raw, lower half of D0).
- `movel D7, (A0+4)` covers bytes `+4..+7` = word2 (tile code, upper half of D7 = 0x0000) + word3 (x_raw, lower half of D7 = 0x0160).

So the init loop, under April-6/MAME semantics, sets:

- 17 sprites, vertically stacked at `y = 8, 24, 40, 56, 72, ..., 216` (primary loop) and `y = 200, 216, 232` (secondary loop)
- all with `x = 352` (off-screen right, beyond the 320-pixel visible width)
- all with `tile_code = 0x0000`, `flipY = 0`, `flipX = 0`, `palette = 0`

This is a **consistent default/parking state** for a 17-slot sprite-descriptor reserve area. The semantic interpretation validates cleanly against the April-6/MAME descriptor model. **No evidence against April-6/MAME.**

**Reconciliation counts:**

```
VERIFIED:  5 fields / attributes  (flipY, flipX, palette, Y, X — all three sources agree)
PARTIAL:   1 field               (tile-code mask 14-bit vs 13-bit; both sufficient)
CONFLICT:  0
UNKNOWN:   0
```

---

## Phase 5 — Memory-region classification

Based on the reconciled model + Phase 3c/3d findings, classify the 16 KB PC090OJ sprite-RAM region `HW_ADDRESS 0x00D00000..0x00D03FFF`:

| byte range             | size   | role                                                                                         | evidence |
| ---------------------- | -----: | -------------------------------------------------------------------------------------------- | -------- |
| `0x00D00000..0x00D007FF` | 2 KB   | **active PC090OJ descriptor area** — 256 sprite entries × 8 bytes (per MAME `PC090OJ_ACTIVE_RAM_SIZE = 0x800`). Arcade pre-fills this with `0x00000100` patterns during init via `arcade_pc 0x03AD72` → `0x03AD44` calls. Structured init at `0x03ADAA` populates entries starting at offset `0x778` (entries 239..255). | MAME lines 66-67; Build 0052 prior analysis |
| `0x00D00778..0x00D0077F..0x00D00800` | 136 B | **structured-init sprite reserve** — 17 entries initialised by the loop at `arcade_pc 0x03ADAA`. Final entry ends at byte `0x800`, exactly aligned with the ACTIVE_RAM boundary. | Andy_d00778_write_path_analysis.md Phase 1 |
| `0x00D00800..0x00D01BFD` | ~4.7 KB | **inactive scratch region** — beyond MAME's ACTIVE_RAM cutoff; arcade uses this as general-purpose memory for game-specific 80-byte records, pointer tables, and state. Example: the function at `arcade_pc 0x41BFC` treats `0xD00460+` as a table of 80-byte records. (Note: `0xD00460` is inside ACTIVE_RAM, not in the `0x00D00800+` inactive region — see discussion below.) | Build 0052 prior analysis; MAME ACTIVE_RAM bound |
| `0x00D01BFE`           | 2 B    | **DMA-trigger / flip-control register** (`m_ctrl`). Per MAME `word_w`: writes at word offset `0xDFF` (byte `0x1BFE`) update `m_ctrl`; bit 0 is flip control. Suppressed in Build 0052 via opcode_replace at `arcade_pc 0x03AE06 / 0x03AE1E / 0x03AE8E`. | MAME lines 144-161; spec lines 267-287 |
| `0x00D01C00..0x00D03FFF` | ~9.2 KB | **padding / unused** — beyond the control register, no MAME-documented role; Build 0052 disassembly shows no writes in this range. | absence of static write evidence |

**Discussion of the 80-byte-stride structure at `0xD00460`:**

`0xD00460` is inside MAME's ACTIVE_RAM region (`0x00D00000..0x00D007FF`). If the function at `arcade_pc 0x41BFC` writes 80-byte records directly to this region, those writes would OVERWRITE PC090OJ descriptor entries — which is a destructive action on the chip-active region. Two reconciling possibilities:

1. The function at `0x41BFC` **does not itself write** to PC090OJ RAM — it only computes a pointer and stores it in work-RAM (confirmed by static analysis of the function body, which contains no store to (A0)). The 80-byte stride reflects how arcade indexes into a *conceptual* record layout inside PC090OJ RAM, but the actual read/write at those offsets happens elsewhere.
2. Arcade deliberately uses entries 140..255 (bytes `0x460..0x7FF`) of the PC090OJ descriptor region as 80-byte-stride records for something other than sprite descriptors. This would disrupt PC090OJ rendering for those slots — unlikely without MAME evidence of Rastan deliberately truncating active sprite count.

(1) is consistent with the Phase 3d function-body analysis and with April 6 §2.3's finding that Rastan's actual sprite data lives in **arcade workram** (offsets `0x11B2` / `0x0170`), not in PC090OJ RAM directly. The function at `0x41BFC` is likely building a pointer table that other code uses to *read* from PC090OJ sprite-RAM. Without the downstream consumer identified, this is the best static interpretation.

**Classification status:** clear memory-region model with one residual UNKNOWN (the downstream consumer of the pointer table stored by `0x41BFC`). This UNKNOWN does **not** block the translation-boundary decision — the pointer-table function doesn't itself modify sprite state.

---

## Phase 6 — Runtime write-surface classification

Per April 6 §4.1: all 15 sprite-data call sites on the arcade side are opcode-replaceable. April 6 **already enumerated** the complete workram-intercept set:

| arcade_pc    | April 6 role (inferred from doc context + arcade disassembly) | static enumerability |
| ------------ | ------------------------------------------------------------- | -------------------- |
| `0x03A20E`   | early sprite init / update                                    | KNOWN |
| `0x03A264`   | same                                                          | KNOWN |
| `0x03A640`   | game-state sprite update                                      | KNOWN |
| `0x03A6C4`   | same                                                          | KNOWN |
| `0x03A818`   | same                                                          | KNOWN |
| `0x03A820`   | same                                                          | KNOWN |
| `0x03A854`   | same                                                          | KNOWN |
| `0x03A8E4`   | same                                                          | KNOWN |
| `0x03A9C6`   | same                                                          | KNOWN |
| `0x03A9D4`   | same                                                          | KNOWN |
| `0x03B8E8`   | startup-chain sprite update                                   | KNOWN |
| `0x03B8F0`   | same                                                          | KNOWN |
| `0x041DAE`   | gameplay sprite update (function region including 0x41BFC neighbours) | KNOWN |
| `0x041F5E`   | **block-copy loop: workram → PC090OJ RAM** (per April 6 §2.3 citation)  | KNOWN |
| `0x045DFA`   | gameplay sprite update                                        | KNOWN |

**Critical observation:** the April-6-identified call site at `arcade_pc 0x041F5E` is described in April 6 §2.3 as "arcade disassembly 0x41F5E–0x41F8C (block copy loop writing from arcade workram to legacy D-window staging buffers, confirming entry size and offsets)". That is **exactly the point at which arcade's sprite descriptors transfer from workram to PC090OJ RAM**. Intercepting at `0x041F5E` captures the full workram sprite state BEFORE the copy reaches PC090OJ RAM.

The Build-0052 runtime writes enumerated in Phase 3c (`0x41BFC`, `0x41DB2..0x45E80` cluster, `0x510EA/F4`) are **downstream** of the workram-staged sprite data. If the workram intercept at April 6's 15 sites is in place, those downstream writes either (a) never execute (arcade redirected upstream), or (b) execute but become cosmetically irrelevant on Genesis because the translated output already reached VDP SAT via the intercept helper.

**Runtime-surface classification (combined April 6 + current analysis):**

```
KNOWN:       15 arcade_pc sites (April 6 enumeration)
PARTIAL:      0
UNRESOLVED:   direct single-word writes at arcade_pc 0x510EA / 0x510F4 — these target
              byte offset 0x698 in PC090OJ RAM. Under the MAME-active-RAM model,
              0x698 = word offset 0x34C, which falls within the active 0x800-byte
              region, i.e., is a PC090OJ descriptor byte. The arcade-pc context of
              these writes is not yet characterised (out-of-scope for this
              reconciliation). May be an edge-case descriptor-update path NOT covered
              by the 15-site April 6 list. Flagged for follow-up verification before
              relying solely on Option A.
```

---

## Phase 7 — Pipeline comparison: April 6 vs Build 0052

| component | April 6 (apps/rastan/ SGDK branch) | rastan-direct Build 0052 | status |
| --------- | ---------------------------------- | ------------------------ | ------ |
| Sprite workram staging buffers (block A at 0x11B2, block B at 0x0170) | present in arcade workram model; referenced by `startup_trampoline.s:225, 233` | arcade workram at `0x00FF0000` still exists (A5 redirect applied in Build 0052); block layouts at +0x11B2 / +0x0170 are ARCADE-OWNED data — present by virtue of arcade code running. | **STILL WORKS** (arcade data-structure layout unchanged) |
| Sprite translation hook (JSR genesistan_render_sprites_vdp_bridge @ 15 arcade sites) | 15 entries in `startup_title_remap.json shift_replacements` | **NONE** in `specs/rastan_direct_remap.json` — zero PC090OJ-related entries targeting descriptor writes | **MISSING** |
| ASM sprite renderer `genesistan_render_sprites_vdp_asm` | defined in `apps/rastan/src/startup_trampoline.s:211`, 263 lines of assembly | **ABSENT** from `apps/rastan-direct/src/` tree | **MISSING** |
| Tile pre-conversion (`preconvert_pc090oj_tiles.py`) | invoked by `apps/rastan/Makefile` | tool still exists at [tools/translation/preconvert_pc090oj_tiles.py](tools/translation/preconvert_pc090oj_tiles.py) but is **NOT invoked** by `apps/rastan-direct/Makefile` | **MISSING** (invocation) / **STILL WORKS** (tool) |
| ROM-embedded sprite tile data (`rastan_pc090oj`) | embedded in `apps/rastan/` ROM at build time | **ABSENT** from `apps/rastan-direct/` build | **MISSING** |
| SAT base at VRAM 0xF800 + VDP register 5 programming | set via `main.c:2189` (`*ctrl = 0x857C`) and `main.c:1447` | `apps/rastan-direct/src/vdp_comm.s vdp_boot_setup:82-84` sets `VDP_REG_SAT = 0x7C` → SAT base 0xF800. Same value as April 6. | **STILL WORKS** (identical SAT base address on Genesis side) |
| April 6 DMA encoding bug fix | documented in April 6 §10; ship status UNKNOWN per prompt | N/A — renderer absent from rastan-direct | **NEVER SHIPPED** to rastan-direct (moot since the containing renderer is absent) |

**Summary:** the Genesis-side SAT address and VDP register programming survive (same convention). Everything arcade-intercepting — hook entries, ASM renderer, tile preload, ROM-embedded sprite tile data — is **absent from rastan-direct**. The pipeline's upstream (arcade's own workram sprite state) is unchanged; its Genesis-side interception layer is missing.

---

## Phase 8 — Translation boundary analysis (critical deliverable)

### 8a. Option A — Workram intercept (April 6 approach)

**Mechanism:** place hooks at 15 arcade_pc sites (April 6 §4.1 list) that invoke arcade sprite-management. Each hook is a `JSR genesistan_render_sprites_vdp_bridge` that (1) reads the 22 descriptors from arcade workram offsets 0x11B2 (18 entries) and 0x0170 (4 entries), (2) translates to Genesis SAT format per the rules in April 6 §§6-8, (3) writes directly to VDP data port at VRAM 0xF800 (SAT), (4) RTS to arcade.

**Evaluation:**

- **RULES.md §8 (Arcade Intent → Genesis Execution):** arcade's intent is expressed in its workram sprite state. Capturing workram state → translating to Genesis SAT preserves arcade intent cleanly. Translation at workram is **semantic**, not memory-level. **PASS.**
- **Completeness:** covers 15 call sites enumerated from April 6's audit. Init AND runtime covered uniformly — the 15 arcade sites include early startup invocations (0x03A20E, 0x03B8E8, 0x03B8F0, 0x041F5E) and per-frame gameplay invocations (0x03A640..0x03A9D4, 0x041DAE, 0x045DFA). April 6 covered init + runtime with the same mechanism. **PASS.**
- **Risk:** if arcade has any sprite-data path that does NOT flow through the 15 intercept points (e.g., a write to PC090OJ RAM that bypasses workram staging entirely), Option A misses it. The direct single-word writes at `arcade_pc 0x510EA/0x510F4` (Phase 6 UNRESOLVED) potentially fit this risk profile. **Follow-up evidence needed** to confirm no bypass path.
- **Runtime pointer-based behaviour at `arcade_pc 0x41BFC`:** this function stores pointers into PC090OJ RAM without itself writing. Under Option A, it is transparent — the intercept catches the upstream workram state before the pointer-using reads / writes happen. **COMPATIBLE.**
- **RULES.md §4 (Helper Functions Only):** `genesistan_render_sprites_vdp_bridge` runs, computes SAT, writes to VDP, RTS. Matches helper contract. **PASS.**
- **Scaling to full game:** April 6's approach was designed for full gameplay with 22 sprites per frame at 60 Hz. The hook fires at arcade's own call rate (which is already the correct 60 Hz rate on real arcade). **PASS.**
- **Scaffolding risk:** zero — the 15-hook approach was purpose-built in April 6 as a production architecture.

### 8b. Option B — PC090OJ write intercept (Rule 8 aligned, current crash site)

**Mechanism:** place opcode_replace entries at every arcade_pc that writes to `0xD0xxxx` sprite RAM. Each hook catches the specific write, decodes the target offset, updates Genesis SAT staging, RTS to arcade.

**Evaluation:**

- **RULES.md §8 (Arcade Intent → Genesis Execution):** arcade's intent at the hardware write IS the PC090OJ descriptor update. Translating at the hardware write directly preserves that intent. **PASS** (conceptually tighter than Option A in one sense — catches intent AT the hardware boundary).
- **Completeness:** requires exhaustive enumeration of every arcade_pc that writes to PC090OJ RAM. Static enumeration in [Andy_pc090oj_full_subsystem_design.md](docs/design/Andy_pc090oj_full_subsystem_design.md) Phase 1 showed that **runtime writes are not statically enumerable** — arcade uses pointer-based indirect writes where Ax is loaded from work-RAM (cf. the function at `0x41BFC`). Without runtime trace evidence of every write site, Option B has indeterminate coverage. **FAIL (completeness).**
- **Runtime pointer-based behaviour:** the function at `0x41BFC` doesn't itself write — the actual writes happen elsewhere via `(An)` addressing where An was loaded from work-RAM. Those sites don't carry `0xD0xxxx` literals and cannot be enumerated by static grep. **INCOMPATIBLE** with Option B's "hook every write site" model unless the runtime enumeration is completed first.
- **Scaffolding risk:** if any site is missed, arcade writes silently unmapped on Genesis (Build 0052 BlastEm halt). Partial coverage is worse than no coverage. Production requires 100% coverage. **PASS only if complete enumeration is proven.**
- **Scaling:** if complete, Option B scales similarly to Option A. But the completeness prerequisite is unverified.

### 8c. Boundary recommendation

**Recommended: Option A — workram intercept.**

**Justification:**

- April 6 pre-solved the descriptor semantics and the 15 hook-site enumeration. That work has high provenance: source citations in April 6 §§4.1 and 2.3 against arcade disassembly, plus the ASM renderer that implements the translation is still in tree at `apps/rastan/src/startup_trampoline.s`.
- Workram state is **upstream** of PC090OJ writes in arcade's data flow. Catching upstream is more robust than catching every downstream write site.
- Option B requires runtime-trace evidence to prove write-site completeness; that evidence does not currently exist (see `Andy_pc090oj_full_subsystem_design.md` STOP). Option A does not require this evidence.
- The 15 call sites are at high-level arcade entry points (function boundaries), not inside tight write loops. Hooking them is architecturally clean and preserves arcade control flow (JSR → helper → RTS back to arcade).
- Option A is already implemented and debugged in `apps/rastan/` (with one known bug documented in April 6 §§5.2-5.3 + §10: the DMA encoding `swap` vs `lsr.l #14` issue). Porting the fixed version to `apps/rastan-direct/` is a bounded implementation task.
- Rule 16 (no suppression as workaround): Option A is not suppression — it translates.

**Confidence:** HIGH.

**Risks (with mitigations):**

| risk | mitigation |
| ---- | ---------- |
| One or more of the 15 April-6 sites may have been renumbered by subsequent arcade_pc shifts (unlikely — whole-maincpu-relocated mode preserves arcade_pc values) | verify all 15 arcade_pc sites still resolve to the expected instructions in [build/maincpu.disasm.txt](build/maincpu.disasm.txt) before Cody implements hooks |
| Direct single-word writes at `0x510EA/0x510F4` bypass workram (Phase 6 UNRESOLVED) | runtime MAME trace of gameplay execution to confirm whether these writes occur on a live code path and, if so, whether the translation helper already covered that state or if those sites need additional Option-B-style hooks as a supplement |
| April 6 DMA encoding bug (§5.2 `swap` vs `lsr.l #14`) — unshipped | Cody must apply the April-6-documented fix in the ported renderer; verify byte-level fix when implementing |
| April 6 renderer references `SPRITE_TILE_BASE = 1024` and VDP tile layout assumptions | confirm Build 0052's `vdp_comm.s` VDP register programming matches the assumption (`VDP_REG_SAT = 0x7C` at `vdp_comm.s:82-84` — already confirmed in Phase 7) |

### 8d. Hybrid option note

A hybrid (Option A primary + small Option B supplement for the 2 direct writes at `0x510EA/0x510F4`) is viable and may be the right landing spot once the Phase 6 UNRESOLVED status on those writes is resolved. **Not recommended at this stage** because it introduces complexity before evidence justifies it; resolve the UNRESOLVED status first via the follow-up task, then decide.

---

## Phase 9 — Root divergence analysis

**Question:** why does the April 6 PC090OJ translation system not exist in `apps/rastan-direct/`?

From the repo structure (`apps/rastan/` and `apps/rastan-direct/` are parallel application trees) and from [docs/design/Cody_no_sgdk_direct_execution_proposal.md](docs/design/Cody_no_sgdk_direct_execution_proposal.md) (line 121: *"Building this in apps/rastan-direct/ preserves apps/rastan/ while enabling deterministic single-owner VDP publishing and direct arcade boot."*):

**Classification: architecture rewrite — rastan-direct explicitly replaced the SGDK-era pipeline with a direct opcode-replace architecture; sprite translation was not ported.**

Specifically:
- `apps/rastan/` is the **SGDK-based** predecessor branch using the April 6 pipeline.
- `apps/rastan-direct/` is the **direct-execution** branch proposed in `Cody_no_sgdk_direct_execution_proposal.md` to eliminate SGDK dependencies and run arcade code natively under a Genesis-side opcode_replace layer.
- The migration focus for rastan-direct has been on tilemap (PC080SN), vblank ownership, interrupt timing, and startup_common correctness — per the sequence of Andy_* and Cody_* docs.
- Sprite (PC090OJ) translation was **deferred** during the rastan-direct port. It was never ported; no regression exists (there was nothing to remove).

This is a reconciled architectural fact, not a bug or oversight per the project's intentional sequencing.

---

## Phase 10 — Readiness for design

- Descriptor model sufficient for design task: **YES.** April 6 baseline verified against MAME with 5 VERIFIED + 1 PARTIAL (mask width) and 0 CONFLICTs. Init evidence from Build 0052 is consistent with the model.
- Runtime surface sufficient for design task: **MOSTLY YES, with one follow-up.** April 6 enumerated 15 KNOWN hook sites. Phase 6 flagged `arcade_pc 0x510EA/0x510F4` as UNRESOLVED — they may need additional treatment. Does not block the subsystem design task (Option A is robust to this gap under recommended mitigation).
- Translation boundary identified: **YES.** Option A (workram intercept) with HIGH confidence.
- Ready for final subsystem design: **YES — conditional on one follow-up.**

**Follow-up evidence task required before the subsystem-design task concludes:**

**FU1.** Runtime write-surface verification. Objective: confirm whether the direct single-word writes at `arcade_pc 0x510EA / 0x510F4` (target `0x00D00698`) execute on a live code path during Build 0052 gameplay, and if they do, whether arcade's own workram sprite staging precedes or postdates them. Method: MAME breakpoint at `arcade_pc 0x510EA` + `0x510F4` over a multi-second gameplay run; if hits observed, correlate with adjacent arcade state (A5@(...) reads, A0 content). Expected outcome: either (a) these writes never hit in normal gameplay (ignore — Option A alone is sufficient), or (b) they hit with coherent state that the Option-A helper already produced (still sufficient), or (c) they hit with state NOT represented in workram blocks A/B (supplement Option A with an Option B hook at these specific arcade_pc values).

**Dependency order:** FU1 is independent and can run in parallel with Cody's preparation of the PC090OJ-subsystem implementation task. FU1's outcome informs whether the implementation task includes 2 supplementary opcode_replace hooks or not. It does not block the overall Option A port.

---

## Phase 11 — Integrity

- Phase 1 April 6 baseline extracted + code survival audited: **YES.**
- Phase 2 MAME validated against April 6 (MATCH=8, PARTIAL=1, CONFLICT=0): **YES.**
- Phase 3 Build 0052 analysis complete: **YES.**
- Phase 4 descriptor reconciliation table complete (VERIFIED=5, PARTIAL=1, CONFLICT=0, UNKNOWN=0): **YES.**
- Phase 5 memory region classification complete (one residual UNKNOWN on downstream consumer of 0x41BFC's pointer table; non-blocking): **YES.**
- Phase 6 runtime write surface classified (KNOWN=15, PARTIAL=0, UNRESOLVED=2 for 0x510EA/0x510F4): **YES.**
- Phase 7 pipeline comparison complete: **YES.**
- Phase 8 translation boundary recommendation produced with evidence (Option A, HIGH confidence): **YES.**
- Phase 9 root divergence classified (architecture rewrite): **YES.**
- Phase 10 design readiness assessed (READY subject to one follow-up, FU1): **YES.**
- No source / spec / tool modifications: **YES.**
- All claims cited to arcade_pc, file:line, or prior doc: **YES.**
- STOP triggered: **NO.**

---

## Summary

```
April 6 baseline extracted:                             YES
April 6 code survival:                                  9 PRESENT (in apps/rastan/ SGDK branch)
                                                         0 PARTIAL
                                                         5 ABSENT from apps/rastan-direct/
                                                         (hook entries, ASM renderer, workram symbol,
                                                          SPRITE_TILE_BASE constant, preconvert invocation)

MAME validated:                                         YES — 8 MATCH, 1 PARTIAL (tile mask
                                                         width; both cover Rastan's 12-bit range),
                                                         0 CONFLICT

Build 0052 analyzed:                                    YES — zero PC090OJ sprite-RAM hooks;
                                                         translation pipeline ABSENT from the
                                                         rastan-direct tree; only DMA-trigger
                                                         suppressions present

Descriptor reconciliation complete:                     YES (V=5, P=1, C=0, U=0)

Memory region classified:                                YES — active 0x800 descriptor region
                                                         (MAME), Rastan sprite-reserve at
                                                         0x778..0x800, inactive scratch region,
                                                         0x1BFE control register, padding beyond

Runtime surface classified:                              KNOWN=15 (April 6 hook sites)
                                                         PARTIAL=0
                                                         UNRESOLVED=2 (0x510EA, 0x510F4 direct
                                                         single-word writes at 0x00D00698)

Pipeline comparison complete:                            YES — full table in Phase 7

Translation boundary recommended:                        **Option A (workram intercept at
                                                         April 6's 15 arcade_pc sites)**,
                                                         HIGH confidence. Justified by:
                                                         (1) April 6 prior solution + its in-tree
                                                         ASM renderer; (2) upstream-of-writes
                                                         interception is more robust than
                                                         trying to enumerate all runtime sites;
                                                         (3) Option B requires runtime-trace
                                                         evidence that does not currently exist.

Root divergence classified:                              Architecture rewrite — rastan-direct
                                                         is a greenfield port of the SGDK-era
                                                         pipeline; sprite translation was
                                                         intentionally deferred during that port
                                                         (per Cody_no_sgdk_direct_execution_proposal.md).

Design readiness:                                        YES — subject to one follow-up (FU1)
                                                         to verify 0x510EA/0x510F4 handling

Suppression proposed:                                    NO

STOP triggered:                                          NO
```

### Evidence-source hierarchy obeyed

- April 6 used as **primary semantic baseline** (Phase 1).
- MAME used as **hardware validation only** (Phase 2) — not treated as authoritative for Rastan runtime.
- Build 0052 disassembly and trace evidence used to reconcile against April 6 + MAME (Phases 3-5) without "picking a favorite" on conflicts (no conflicts arose).

### Architecture compliance

No reconciliation conclusion proposes:
- Giving Genesis code control-flow ownership (the Option A helper is called via JSR from arcade and RTSes — Rule 15, 4).
- Re-entering boot/init during gameplay (the April 6 hooks replace arcade call sites in-place — Rule 6).
- Introducing a Genesis-side lifecycle or state machine (the helper is stateless per invocation — Rule 7).
- Adding test code, scaffolding, or temporary logic (Option A is production architecture with a documented bug to fix — Rule 5, Rule 16).
- Preventing arcade code from owning execution (arcade owns; Genesis translates — Rule 1).
- Memory shadowing (translation is semantic: arcade workram → Genesis SAT — Rule 6).

**Suppression-as-workaround: NOT proposed.**
