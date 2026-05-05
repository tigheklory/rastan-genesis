# Andy — Build 55 Dynamic Palette Translation Design

**Agent:** Andy (Claude Code)
**Type:** Architectural design (analytical synthesis only — no implementation, no new evidence collection)
**Build:** rastan-direct Build 0055 (target; Build 0054 baseline post-D6-fix, post-v3.2 dispatch)
**Date:** 2026-05-02
**Architecture compliance:** CONFIRMED. The proposed Cody implementation preserves all 10 architectural invariants per Andy v3.2 §1.8 (no Genesis-side lifecycle introduced; helper invoked by arcade-triggered `0x59AD4`-call sites; staging-then-commit pattern preserved; all v3.1/v3.2 closures and D6-fix patches untouched).

---

## 0. Executive verdict

The white-CRAM bug from Andy v3.2-prior cycle is correctly classified as **Cause 1 (missing palette producer)** but the **fix shape is REVISED** from the prior `static per-scene .incbin payloads` plan. Cody Build 55 evidence proves static scene payloads are insufficient: 30 dynamic callers, mixed runtime-derived `D0`/`D1` arguments, partial-bank update granularity (16 words per call), call clusters spread across title/gameplay (no endround callers — implying shared state), and 5 bypass writers exist outside `0x59AD4`. **The correct fix is a runtime hook on the arcade palette-conversion routine itself plus targeted intercepts on the two reachable, consumed-bank bypass writers.**

**Fix shape: `0x59AD4` function-body replacement helper + 2 bypass-writer intercepts.**

- **`genesistan_palette_hook_59ad4`** replaces the arcade body at `0x59AD4..0x59B19` (≈68 bytes per Cody §1.2). Helper signature matches arcade entry contract: `%a0` = source descriptor base, `%d0` = arcade palette bank, `%d1` = source row index. Helper performs faithful 2-step (arcade-raw → xBGR-555 → Genesis CRAM) per Option A — produces byte-identical visible result to Option B but mirrors `0x59AD4`'s arcade-faithful intermediate. Helper writes to `staged_palette_words[D0 * 16 + entry]` ONLY when `D0 ∈ {0,1,2,3}` (tilemap-consumed range, derived from §1.3 LUT analysis); high-bank calls (`D0 ∈ {4..0x43}`) are skipped on the Genesis side because sprite bank-ID consumption is PARTIAL_UNKNOWN (§1.5 Rule 20 workaround). Sets `palette_dirty := 1` on any low-bank write. RTS.
- **`genesistan_palette_hook_3ab00`** intercepts the direct word write at `arcade_pc 0x03AB00` (`movew #1023, 0x200022`); writes target arcade bank 1 entry 1, which IS tilemap-consumed; helper translates and writes to `staged_palette_words[1*16 + 1]` (= word 17), sets `palette_dirty := 1`. 8-byte slot replaced with 8-byte JSR + RTS.
- **`genesistan_palette_hook_45dae`** intercepts the loop-prologue at `arcade_pc 0x045DAE` (`lea 0x200000, %a1` then 64-byte copy via `jsr 0x3a2d0`); helper translates the 32 source words to Genesis CRAM equivalents and writes to `staged_palette_words[idx*16 .. idx*16+15]` for `idx ∈ 0..3` (banks 0..3 consumed), skips banks 4..15 (sprite-side, PARTIAL_UNKNOWN). Sets `palette_dirty := 1` on any low-bank write. The 6-byte `lea` is too small for a 6-byte JSR + 4-byte RTS, so this entry replaces a larger span (`0x045DAE..0x045DF8` = 74 bytes per Cody §1.4 + verification of next-RTS in disassembly) with `JSR helper; RTS; NOP*` — full function-body-replacement style matching the v3.1 `0x03C4D2` precedent.

The 3 remaining bypass writers (`0x000264`, `0x03AEB6/0x03AEDA`, `0x045DE4`) require NO intervention: `0x000264` is unreachable (preserved-vectors region per Andy v3.2 §1.3); `0x03AEB6/0x03AEDA` paired writes are already NOPed via existing spec entries; `0x045DE4` writes to banks 48..63 which are outside tilemap-consumed range and depend on the sprite-bank PARTIAL_UNKNOWN gap.

The conversion path is **xBGR-555 → Genesis CRAM** per the local MAME snapshot evidence (`docs/reference/mame/rastan/src/mame/taito/rastan.cpp:455` `palette_device::xBGR_555, 2048`). The project CLCS expression at `apps/rastan/src/main.c:1020` is **disproven** for this path by the §1.3 comparison table in `Cody_build55_mame_palette_format_evidence.md` — for `raw=0x0FFF` it produces `0x00EE` (wrong) where the correct Genesis CRAM equivalent is `0x0EEE`. Cody's implementation must NOT use the CLCS expression.

The bank-mapping rule for tilemap is derived from the existing `genesistan_pc080sn_attr_lut`: arcade tile-attribute pal[1:0] → Genesis CRAM line[1:0], 1:1 mapping (§1.3 LUT analysis below). The 5-bit "0..31" range in Cody §1.2 is the LUT-INDEX domain (combining priority + vflip + hflip + pal_low_2_bits), NOT arcade palette banks. Arcade palette banks 0..3 are the tilemap-consumed banks; banks 4..127 are sprite/secondary banks not handled in Build 55.

The sprite gap (PARTIAL_UNKNOWN per Cody §1.3) is handled per Rule 20 Option (a) — work around: high-bank `0x59AD4` calls are skipped on the Genesis side; sprite renderer uses whatever is in CRAM lines 0..3 (the tilemap palette). This may produce visually-incorrect sprite colors initially. A separate Cody follow-up (specified in §1.5.2) will trace sprite `%d1`/`%d7` provenance to refine the mapping in a future build.

Postpatcher invariant: `opcode_replace_count = 90 + 3 = 93`; new `bytes` value measured by Cody's build run (not pre-presumed per Build 54 D6-fix discipline).

---

## §1.1 Static scene palettes invalidation

The prior Andy v3.2 §1.6.2 fix specification proposed **static per-scene `.incbin` palette payloads** (e.g., `pc050cm_palette_title.bin`, `pc050cm_palette_gameplay.bin`, `pc050cm_palette_endround.bin`) loaded by an extension to `load_scene_tiles`. Cody Build 55 evidence proves this plan is **INSUFFICIENT**:

1. **30 dynamic callers, not scene-bounded** ([Cody_build55_palette_fix_shape_evidence.md §1.1](docs/design/Cody_build55_palette_fix_shape_evidence.md)). The 30 callsites span title/frontend cluster (10 sites in `0x511BC..0x5A4B0` range) AND gameplay cluster (20 sites in `0x56136..0x59E06` range), but ZERO endround/status callers. If palette were strictly scene-bounded, the endround scene would have its own producer; instead the absence of endround callers implies palette state is shared between scenes via the `0x59AD4` runtime hook and arcade workram state.

2. **Runtime-derived `D0` and `D1` arguments at multiple sites** ([Cody §1.3](docs/design/Cody_build55_palette_fix_shape_evidence.md)):
   - `0x575FE`: `D1 = %a5@(5098)` (workram-derived, runtime)
   - `0x57610`: `D1 = %a5@(5098)`
   - `0x5999A`: `D0 = table[idx]`, `D1 = (%a5@(4840) >> 3)` when low-3 bits zero
   - `0x599F0..0x59A80`: `D0 = table-driven`, `D1 = ((%a5@(4842) >> 3) + offset) & 3`
   - `0x59E06`: `D1 = %a5@(5038)`

   These arguments cannot be resolved at build time — they depend on arcade game state at the moment of call. A static `.incbin` payload cannot reproduce per-call dynamic argument selection.

3. **Partial-bank update granularity (16 words per call)** ([Cody §1.6](docs/design/Cody_build55_palette_fix_shape_evidence.md)). Each `0x59AD4` call updates 16 entries (one bank's worth, not a full 64-word palette). Multi-call sequences typically update different banks per state. A static "full palette per scene" payload would not match this — the arcade incrementally updates partial banks, and the Genesis-side equivalent must update partial banks too.

4. **5 bypass writers exist outside `0x59AD4`** ([Cody §1.4](docs/design/Cody_build55_palette_bank_mapping_evidence.md)). Static scene payloads cannot represent updates that the arcade performs via direct memory writes (`0x03AB00`, `0x03AEB6/0x03AEDA`, `0x045DAE/0x045DE4`).

**Status: Andy v3.2 §1.6.2 SUPERSEDED.** The fix shape revises to a runtime-hook model (§1.2 below).

---

## §1.2 Fix shape classification

**Classification: `0x59AD4` hook + bypass writer intercepts.**

Justification (cited evidence):

- The static-payload classification is RULED OUT by §1.1.
- The "palette RAM staging model" classification (Genesis-side full palette RAM mirror at WRAM, all writes populate the mirror) is overengineered: only 4 of arcade's 128+ palette banks are visible to Genesis (lines 0..3 per the `pc080sn_attr_lut` mapping in §1.3). A full mirror would shadow ~4 KB of arcade palette RAM into Genesis WRAM where 99% of it is never observed downstream. **Rejected per Rule 6** (no memory shadowing).
- The "`0x59AD4` hook only" classification is RULED OUT by Cody §1.4: `0x03AB00` and `0x045DAE` write to consumed-bank addresses without going through `0x59AD4`. A hook-only fix would miss these.
- **Selected: `0x59AD4` body replacement + 2 bypass intercepts (`0x03AB00`, `0x045DAE`)**.

Cited reasoning:

- `0x59AD4` is the dominant funnel: 30 callers cover the title and gameplay paths. Replacing its body intercepts 30 of 32 known palette write paths in one entry.
- `0x03AB00` is a direct word write to bank 1 entry 1 ([Cody §1.4 Site B](docs/design/Cody_build55_palette_bank_mapping_evidence.md)) — bank 1 is tilemap-consumed and the write bypasses `0x59AD4`. Intercept needed.
- `0x045DAE` is a copy loop targeting banks 0..15 (Cody §1.4 Site D) — banks 0..3 are tilemap-consumed; bypass intercept needed.
- `0x000264` is in the preserved-vectors region (unreachable per Andy v3.2 §1.3 boundary analysis); IGNORE.
- `0x03AEB6/0x03AEDA` paired writes already have their `0x03AEBC`/`0x03AEE0` write-back partners NOPed (per `specs/rastan_direct_remap.json:379-383, 397-400`); IGNORE.
- `0x045DE4` writes to banks 48..63 (Cody §1.4 Site D, branch 2); outside tilemap-consumed range and dependent on sprite PARTIAL_UNKNOWN gap; IGNORE per Rule 20 workaround.

---

## §1.3 Bank-mapping rule for tilemap (arcade banks 0..3 → Genesis CRAM lines 0..3)

`build/pc080sn_attr_lut.bin` is 32 entries × 2 bytes (64 bytes total). Hex-dumped contents (verified verbatim):

```
00000000: 0000 2000 4000 6000 0800 2800 4800 6800
00000010: 1000 3000 5000 7000 1800 3800 5800 7800
00000020: 8000 a000 c000 e000 8800 a800 c800 e800
00000030: 9000 b000 d000 f000 9800 b800 d800 f800
```

Decode each entry as a **Genesis tile-attribute word** (bit format: `priority[15] vflip[12] hflip[11] palette[14:13] tile_index[10:0]`):

| LUT idx | Hex | Bit 15 (pri) | Bit 12 (vflip) | Bit 11 (hflip) | Bits 14:13 (pal line) |
|---------|-----|:-:|:-:|:-:|:-:|
| 0  | 0x0000 | 0 | 0 | 0 | 00 = line 0 |
| 1  | 0x2000 | 0 | 0 | 0 | 01 = line 1 |
| 2  | 0x4000 | 0 | 0 | 0 | 10 = line 2 |
| 3  | 0x6000 | 0 | 0 | 0 | 11 = line 3 |
| 4  | 0x0800 | 0 | 0 | 1 | 00 = line 0 |
| 5  | 0x2800 | 0 | 0 | 1 | 01 = line 1 |
| 6  | 0x4800 | 0 | 0 | 1 | 10 = line 2 |
| 7  | 0x6800 | 0 | 0 | 1 | 11 = line 3 |
| 8  | 0x1000 | 0 | 1 | 0 | 00 = line 0 |
| 9  | 0x3000 | 0 | 1 | 0 | 01 = line 1 |
| 10 | 0x5000 | 0 | 1 | 0 | 10 = line 2 |
| 11 | 0x7000 | 0 | 1 | 0 | 11 = line 3 |
| 12 | 0x1800 | 0 | 1 | 1 | 00 = line 0 |
| 13 | 0x3800 | 0 | 1 | 1 | 01 = line 1 |
| 14 | 0x5800 | 0 | 1 | 1 | 10 = line 2 |
| 15 | 0x7800 | 0 | 1 | 1 | 11 = line 3 |
| 16 | 0x8000 | 1 | 0 | 0 | 00 = line 0 |
| 17 | 0xA000 | 1 | 0 | 0 | 01 = line 1 |
| 18 | 0xC000 | 1 | 0 | 0 | 10 = line 2 |
| 19 | 0xE000 | 1 | 0 | 0 | 11 = line 3 |
| 20 | 0x8800 | 1 | 0 | 1 | 00 = line 0 |
| 21 | 0xA800 | 1 | 0 | 1 | 01 = line 1 |
| 22 | 0xC800 | 1 | 0 | 1 | 10 = line 2 |
| 23 | 0xE800 | 1 | 0 | 1 | 11 = line 3 |
| 24 | 0x9000 | 1 | 1 | 0 | 00 = line 0 |
| 25 | 0xB000 | 1 | 1 | 0 | 01 = line 1 |
| 26 | 0xD000 | 1 | 1 | 0 | 10 = line 2 |
| 27 | 0xF000 | 1 | 1 | 0 | 11 = line 3 |
| 28 | 0x9800 | 1 | 1 | 1 | 00 = line 0 |
| 29 | 0xB800 | 1 | 1 | 1 | 01 = line 1 |
| 30 | 0xD800 | 1 | 1 | 1 | 10 = line 2 |
| 31 | 0xF800 | 1 | 1 | 1 | 11 = line 3 |

**The 5-bit LUT index is constructed from arcade tile-attribute bits per [tilemap_hooks.s:142-164](apps/rastan-direct/src/tilemap_hooks.s#L142-L164):**

```
idx[1:0] = arcade_attr & 0x0003       /* arcade pal[1:0] */
idx[2]   = arcade_attr[14]             /* arcade hflip */
idx[3]   = arcade_attr[15]             /* arcade vflip */
idx[4]   = arcade_attr[13]             /* arcade priority */
```

The 32 LUT entries enumerate all combinations of `{priority, vflip, hflip, pal_high, pal_low}`.

**Bank-mapping rule:** the LUT entries' **palette-line bits (LUT_value[14:13])** correspond DIRECTLY to **arcade pal[1:0]** (LUT_index[1:0]). For all 32 entries, the relationship `LUT_value[14:13] == LUT_index[1:0]` holds (verified by inspection: entries 0,4,8,12,16,20,24,28 = pal_low_idx 00 → LUT_value[14:13] = 00; entries 1,5,9,13,17,21,25,29 = pal_low_idx 01 → LUT_value[14:13] = 01; etc.).

**Therefore:** **arcade tile-attribute pal[1:0] (= arcade palette bank for tilemap) → Genesis CRAM line[1:0]. 1:1 mapping. No folding, no rotation.**

The phrasing in Cody §1.2 ("Consumed banks (tilemap evidence): 0..31") refers to the **LUT-index domain** (5 bits), NOT to arcade palette banks. Arcade tilemap consumes only **arcade palette banks 0..3** — the low 2 bits of arcade tile-attribute. The Genesis CRAM palette line for a tile is determined by **arcade tile_attr & 0x0003**, mapped 1:1 to Genesis line `attr & 0x0003`.

**For the `0x59AD4` helper, this means:** when called with `D0 ∈ {0, 1, 2, 3}` (the tilemap-consumed bank range), the destination Genesis CRAM line is `D0` itself (bits 0-1 of D0). When called with `D0 ∈ {4..0x43}`, the destination is outside the tilemap consumption range — the arcade is updating sprite/secondary palette banks that the Genesis tilemap renderer does not read. These are handled per §1.5 (Rule 20 workaround: SKIP).

Bank-mapping evidence cited: [build/pc080sn_attr_lut.bin](build/pc080sn_attr_lut.bin) hex-dump above + [tilemap_hooks.s:142-164](apps/rastan-direct/src/tilemap_hooks.s#L142-L164) LUT-index extraction sequence.

---

## §1.4 Conversion algorithm decision

**Selected: Option A (faithful 2-step) — helper replicates `0x59AD4`'s arcade-raw → xBGR-555 conversion verbatim, then converts xBGR-555 → Genesis CRAM via local-canonical `convert_xbgr555_to_genesis` logic at [apps/rastan/src/main.c:1008-1017](apps/rastan/src/main.c#L1008-L1017).**

Cited reasoning:

- **Arcade-faithful equivalence.** The helper is REPLACING `0x59AD4`'s body via opcode_replace; per the function-body replacement convention (Andy v3.2 §8.5 / `genesistan_pc090oj_hook_target_*` precedent), the helper IS the arcade routine on Genesis. Maintaining the arcade's intermediate xBGR-555 representation makes the helper byte-for-byte traceable to the original arcade routine — easier to verify against MAME ground-truth and easier for future maintenance.
- **Both options produce identical visible output.** The §1.3 comparison table in `Cody_build55_mame_palette_format_evidence.md` shows for the 8 sample inputs, the "expected Genesis CRAM equivalent" (= xBGR-555 → CRAM via main.c:1013-1017) matches the result of going arcade-raw → xBGR-555 → CRAM. Both routes converge mathematically.
- **Two-step decomposition is mechanically simpler in M68K asm.** The arcade-raw → xBGR-555 step is 7 instructions ([Cody_build55_palette_bank_mapping_evidence.md §1.1 verbatim body](docs/design/Cody_build55_palette_bank_mapping_evidence.md)); the xBGR-555 → CRAM step is 4-6 more instructions per channel. A one-step formula is also possible (8-12 instructions), but harder to verify against either the arcade or the project's existing C reference.
- **The project CLCS expression at [apps/rastan/src/main.c:1020-1024](apps/rastan/src/main.c#L1020-L1024) is DISPROVEN for this path** by the §1.3 comparison table: for `raw=0x0FFF` it produces `0x00EE` (8 bits set) where the correct Genesis CRAM equivalent is `0x0EEE` (12 bits set). Per Rule 18, Cody MUST NOT use the CLCS expression. Helper must use xBGR-555 → CRAM conversion.

**Helper conversion sequence (mirrors arcade `0x59AD4` then post-converts to CRAM):**

```asm
/* Step A — arcade-raw → xBGR-555 (replicates 0x59AD4's per-entry body verbatim) */
move.w  %a0@+, %d1                /* d1 := raw */
cmpi.w  #0xFFFF, %d1
beq.s   .Lpalette_skip_entry      /* sentinel: source 0xFFFF → no write */
move.w  %d1, %d2
move.w  %d1, %d3
andi.w  #0x0F00, %d1
lsr.w   #7, %d1                   /* d1 := part_a = (raw & 0x0F00) >> 7 */
andi.w  #0x00F0, %d2
lsl.w   #2, %d2                   /* d2 := part_b = (raw & 0x00F0) << 2 */
andi.w  #0x000F, %d3
lsl.w   #8, %d3
lsl.w   #3, %d3                   /* d3 := part_c = (raw & 0x000F) << 11 */
add.w   %d1, %d3
add.w   %d2, %d3                  /* d3 := xBGR-555 = part_a | part_b | part_c */

/* Step B — xBGR-555 → Genesis CRAM (mirrors main.c:1008-1017) */
move.w  %d3, %d4
andi.w  #0x001F, %d4              /* d4 := r5 = bits[4:0] */
lsr.w   #2, %d4                   /* d4 := r3 = r5 >> 2 */
lsl.w   #1, %d4                   /* d4 := rn = r3 << 1 = bits[3:1] of CRAM */

move.w  %d3, %d5
lsr.w   #5, %d5
andi.w  #0x001F, %d5              /* d5 := g5 */
lsr.w   #2, %d5                   /* d5 := g3 */
lsl.w   #1, %d5
lsl.w   #4, %d5                   /* d5 := gn shifted to bits[7:5] of CRAM */
or.w    %d5, %d4                  /* d4 := rn | (gn << 4) */

move.w  %d3, %d5
lsr.w   #8, %d5
lsr.w   #2, %d5                   /* d5 := b5 = bits[14:10] of xBGR-555 (= raw[12:8]) */
andi.w  #0x001F, %d5
lsr.w   #2, %d5                   /* d5 := b3 */
lsl.w   #1, %d5
lsl.w   #8, %d5                   /* d5 := bn shifted to bits[11:9] of CRAM */
or.w    %d5, %d4                  /* d4 := Genesis CRAM = rn | (gn << 4) | (bn << 8) */

/* Step C — write to staged_palette_words ONLY if D0 ∈ {0,1,2,3} */
/* (gating handled at function entry by D0 range check; if reached here, D0 is in tilemap-consumed range) */
move.w  %d4, (%a1)+               /* %a1 was set up at function entry to staged_palette_words[D0*16] */

/* mark dirty */
move.b  #1, palette_dirty
.Lpalette_skip_entry:
/* loop control via D6 counter, identical to arcade body */
```

This 21-instruction inner loop replaces the arcade's 16-instruction inner loop (Cody §1.2). The added 5 instructions are the xBGR-555 → CRAM post-conversion. Faithful to arcade, correct for Genesis.

---

## §1.5 Sprite handling decision (PARTIAL_UNKNOWN gap)

**Selected: Option (a) — work around for Build 55. Sprite-bank `0x59AD4` calls (D0 ∉ {0,1,2,3}) are SKIPPED on the Genesis side; the Genesis sprite renderer uses whatever is in CRAM lines 0..3 (the tilemap palette).**

### 1.5.1 Cited reasoning

- **Sprite consumer mapping is PARTIAL_UNKNOWN per [Cody §1.3](docs/design/Cody_build55_palette_bank_mapping_evidence.md).** The pc090oj_hooks.s sprite emit path computes a 2-bit Genesis palette line from `%d1` low nibble + `%d7`-derived bits ([pc090oj_hooks.s:128-136](apps/rastan-direct/src/pc090oj_hooks.s#L128-L136)). Direct arcade palette-bank IDs are NOT read by current sprite helpers; the 2-bit line output (`0..3`) is computed at the moment of SAT emission, not derived from arcade palette RAM contents.
- **No safe deterministic mapping exists for high banks.** Arcade `0x59AD4` is called with `D0 ∈ {4, 5, 6, 0x33, 0x41, 0x43}` (Cody §1.5). Without sprite-side bank-ID provenance, the Genesis CRAM line that should consume each high-bank palette is unknown. A fold-by-truncation rule (`Genesis_line = D0 & 0x03`) would COLLIDE with tilemap writes (e.g., D0=4 truncates to 0, overwriting tilemap line 0). Folding is unsafe.
- **Skipping high-bank writes is bounded and architecturally clean.** When the helper observes D0 ∉ {0,1,2,3}, it returns RTS without staging any Genesis CRAM update. The arcade's xBGR-555 write to arcade palette RAM (`0x200000+`) ALSO does not happen because the helper is the body replacement (the original `0x59AD4` is never executed). Arcade palette RAM stays at whatever Genesis-side state it was in — but Genesis doesn't read arcade palette RAM, so this is harmless.
- **Genesis sprite renderer continues to function.** Per Andy v3.2 §3.5/3.6, the Genesis sprite emit path computes its own 2-bit Genesis palette line. Sprites WILL render — they will just use whatever colors are in CRAM lines 0..3 (the tilemap palette). Sprites may appear with tilemap-tinted colors instead of their intended sprite-specific colors. **This is a known visual limitation for Build 55, NOT a crash and NOT a hang.**
- **Forward path to full sprite-color correctness.** A separate Cody follow-up (§1.5.2) traces sprite `%d1`/`%d7` provenance back to the arcade attribute words and identifies which arcade palette banks correspond to which sprite types (boss palette vs enemy palette vs HUD-icon palette). Once mapped, a Build 56 helper update can extend the helper to handle sprite banks correctly.

### 1.5.2 Sprite-mapping Cody follow-up specification (DEFERRED)

**Goal:** Trace sprite `%d1`/`%d7` provenance back to arcade attribute words and identify direct arcade palette bank IDs.

**Inputs:** `apps/rastan-direct/src/pc090oj_hooks.s` lines 128-136 (sprite palette-line synthesis); the `%d7` producers at lines 190-192, 250-252, 288-290, 425-427, 700-702, 716-718; arcade disassembly `build/maincpu.disasm.txt`; MAME local snapshot `docs/reference/mame/rastan/`.

**Method:** For each sprite-side `%d1`/`%d7` source, walk back to the arcade attribute word that produced the value. Determine: when the arcade emits a sprite of type X, which arcade palette bank does it expect to be loaded for that sprite's color data? Build a mapping table: arcade sprite-type → arcade palette bank → Genesis CRAM line.

**Output:** `docs/design/Cody_build56_sprite_palette_bank_mapping.md` documenting the mapping table.

**Trigger:** Build 55 lands successfully (white-CRAM resolved for tilemap). Sprite color quality is compared against MAME reference; if sprites render in wrong colors, this follow-up is triggered to inform Build 56.

---

## §1.6 High-bank treatment (D0 ∈ {0x33, 0x41, 0x43}, banks 48..79)

Per §1.3 LUT analysis, only arcade palette banks 0..3 are tilemap-consumed.

| D0 value | bank | tilemap-consumed? | sprite-relevant? | Build 55 treatment |
|----------|------|:-:|:-:|---|
| 0x33 (51) | bank 51 | NO | UNKNOWN (PARTIAL_UNKNOWN sprite gap) | SKIP (no Genesis-side write) |
| 0x41 (65) | bank 65 | NO | UNKNOWN | SKIP |
| 0x43 (67) | bank 67 | NO | UNKNOWN | SKIP |
| 4 | bank 4 | NO | UNKNOWN | SKIP |
| 5 | bank 5 | NO | UNKNOWN | SKIP |
| 6 | bank 6 | NO | UNKNOWN | SKIP |

**For banks 48..79 (touched by `0x045DE4` per Cody §1.4 Site D branch 2):** outside tilemap-consumed range, sprite mapping unknown. **SKIP** — `0x045DE4` is NOT intercepted (no opcode_replace entry added for it). Its arcade write to `0x200600+` may or may not affect arcade-side state; Genesis side is unaffected because Genesis renderer doesn't read arcade palette RAM.

**Forward path:** these banks become well-defined once the §1.5.2 sprite-mapping Cody follow-up completes. Build 56 helper update may add specific D0-value → Genesis-line mappings for sprite-relevant high banks.

---

## §1.7 Bypass writer intercept decisions

Per Rule 25, each bypass writer's intercept decision:

| Bypass writer | Cody §1.4 site | Reachable | Tilemap-consumed bank? | Decision |
|---------------|----------------|:-:|:-:|---|
| `arcade_pc 0x000264` | A | NO (preserved-vectors per Andy v3.2 §1.3) | UNKNOWN | **IGNORE** |
| `arcade_pc 0x03AB00` | B | YES (in arcade_copy range) | YES (bank 1 is tilemap-line 1) | **INTERCEPT** |
| `arcade_pc 0x03AEB6 / 0x03AEDA` | C | YES, but paired writes ALREADY NOPed | bank 0 (tilemap-line 0) | **IGNORE** (already neutralized by existing spec entries at `0x03AEBC`/`0x03AEE0`) |
| `arcade_pc 0x045DAE` | D branch 1 | YES | YES (banks 0..3 within touched 0..15 range; sprite banks 4..15 are ignored per §1.5 workaround) | **INTERCEPT** (helper translates banks 0..3, skips 4..15) |
| `arcade_pc 0x045DE4` | D branch 2 | YES | NO (banks 48..63 outside tilemap range) | **IGNORE** (sprite-side, PARTIAL_UNKNOWN gap) |

**Final list of new opcode_replace entries for Build 55: 3.**

1. `0x59AD4` body replacement (function-body replacement; ~68 bytes per Cody §1.2)
2. `0x03AB00` direct-write replacement (8 bytes: `33fc 03ff 00200022`)
3. `0x045DAE` body replacement (covers banks 0..3 with tilemap-correct translation; banks 4..15 skipped)

`opcode_replace_count`: 90 → **93**.

---

## §1.8 Bounded Cody implementation plan

### 1.8.1 Fix shape

`0x59AD4` body replacement helper + 2 bypass-writer intercepts. Producer integration uses the existing `_vblank_service` palette gate and `staged_palette_words` infrastructure (no infrastructure changes required — Andy v3.2-prior cycle correctly identified the producer-absence problem; Build 55 adds the producer).

### 1.8.2 New opcode_replace entries (3 entries)

**Entry 1 — `0x59AD4` body replacement.**

- `arcade_pc`: `0x59AD4`
- Span: `0x59AD4..0x59B19` (≈68 bytes per Cody §1.2 body)
- Cody must verify the exact end via `build/maincpu.disasm.txt` next-RTS lookup; the prompt's "≈68 bytes" is approximate
- `original_bytes`: full byte content from Cody's verification (concatenated hex of all instructions in span)
- `replacement_bytes`: `4EB9{symbol:genesistan_palette_hook_59ad4}4E75` followed by `4E71` (NOP) padding to match span length
- `note`: `"PC050CM palette translation hook at arcade_pc 0x59AD4. Replaces arcade body with Genesis-side helper that translates arcade-raw 12-bit color → xBGR-555 → Genesis CRAM, writes to staged_palette_words[D0*16..D0*16+15] when D0 ∈ {0,1,2,3} (tilemap-consumed banks per genesistan_pc080sn_attr_lut), skips high-bank calls (sprite-side PARTIAL_UNKNOWN gap, deferred to Cody_build56 follow-up). Sets palette_dirty := 1 on any tilemap-bank write. See Andy_build55_palette_translation_design.md §1.4."`

**Entry 2 — `0x03AB00` direct-write replacement.**

- `arcade_pc`: `0x03AB00`
- Span: 8 bytes (`33fc 03ff 0020 0022 movew #1023, 0x200022`)
- `original_bytes`: `33FC03FF00200022`
- `replacement_bytes`: `4EB9{symbol:genesistan_palette_hook_3ab00}4E71` (6-byte JSR + 2-byte NOP = 8 bytes)
- `note`: `"PC050CM palette bypass writer at arcade_pc 0x03AB00 (direct word write to arcade palette bank 1 entry 1). Replaced with JSR genesistan_palette_hook_3ab00, which translates the literal value 0x03FF to Genesis CRAM equivalent and writes to staged_palette_words[1*16+1] (= word 17). Sets palette_dirty := 1. See Andy_build55_palette_translation_design.md §1.7."`

**Entry 3 — `0x045DAE` body replacement.**

- `arcade_pc`: `0x045DAE`
- Span: from `0x045DAE` to next-RTS or next-segment boundary (Cody must verify exact bytes via `build/maincpu.disasm.txt`; the routine includes the `lea`, the index calculation, and the `jsr 0x3a2d0` copy invocation per Cody §1.4 Site D)
- `original_bytes`: full byte content from Cody's verification
- `replacement_bytes`: `4EB9{symbol:genesistan_palette_hook_45dae}4E75` followed by `4E71` (NOP) padding to match span length
- `note`: `"PC050CM palette bypass writer at arcade_pc 0x045DAE (loop-prologue: lea 0x200000, %a1 then 64-byte copy via jsr 0x3a2d0). Replaced with helper that translates the source words and writes to staged_palette_words[idx*16..+15] for idx ∈ 0..3 (tilemap-consumed); skips banks 4..15 (sprite-side PARTIAL_UNKNOWN). Sets palette_dirty := 1 on any tilemap-bank write. See Andy_build55_palette_translation_design.md §1.7."`

### 1.8.3 New helpers (3 helpers, 3 new symbols)

**Helper 1 — `genesistan_palette_hook_59ad4`.**

- Lives in new file `apps/rastan-direct/src/palette_hooks.s` (palette domain — separate from `pc090oj_hooks.s` and `tilemap_hooks.s` for source-organization clarity; Andy v3.2 §9.1 precedent for `pc090oj_hooks.s` separation).
- Signature: `%a0` = source descriptor base (16-word arcade palette source), `%d0` = arcade palette bank (0..0x43 observed), `%d1` = source row index (0, 1, 2, 4, runtime-derived).
- Body:
  1. `movem.l %d0-%d7/%a0-%a1, -(%sp)` (full register save matching v3.2 helper convention)
  2. Replicate arcade entry-time setup: `muluw #32, %d1; addaw %d1, %a0` (advance source pointer by row-stride 32 bytes)
  3. **D0 range check (tilemap gate):** `cmpi.w #4, %d0; bhs.s .Lpalette_59ad4_skip_high_bank` — if D0 ≥ 4, skip Genesis-side write entirely (Rule 20 workaround)
  4. Compute `staged_palette_words` destination: `lea staged_palette_words, %a1; lsl.w #5, %d0; adda.w %d0, %a1` (D0 × 32 bytes per bank = 16 words per line × 2 bytes; %a1 := staged_palette_words + D0 × 32)
  5. Loop counter `moveq #0, %d6; cmpi.w #15, %d6; ...` matching arcade `0x59AD4`'s 16-iteration body
  6. Per-iteration: `move.w (%a0)+, %d1; cmpi.w #0xFFFF, %d1; beq.s .Lpalette_59ad4_skip_entry` (sentinel)
  7. **Step A** (arcade-raw → xBGR-555, replicating `0x59AD4` body verbatim per §1.4 asm sketch above)
  8. **Step B** (xBGR-555 → Genesis CRAM via §1.4 asm sketch)
  9. `move.w %d4, (%a1)+` (Genesis CRAM word written to staged_palette_words at current %a1 offset)
  10. `move.b #1, palette_dirty` (set dirty flag — gates next VBlank's `vdp_commit_palette`)
  11. Loop iteration via `cmpi.w #15, %d6; beq.s .Lpalette_59ad4_done; addq.w #1, %d6; bra ...`
  12. `.Lpalette_59ad4_skip_high_bank:` and `.Lpalette_59ad4_done:` exits restore registers via `movem.l (%sp)+, %d0-%d7/%a0-%a1` and `rts`

**Helper 2 — `genesistan_palette_hook_3ab00`.**

- Same source file (`palette_hooks.s`).
- Signature: no register inputs (the original arcade write is a literal `movew #1023, 0x200022`).
- Body:
  1. `movem.l %d0-%d4, -(%sp)` (modest save — only scratch registers used)
  2. `move.w #0x03FF, %d1` (literal source value from arcade write)
  3. Apply Step A + Step B from §1.4 to produce Genesis CRAM equivalent in `%d4`
  4. `move.w %d4, staged_palette_words + 17*2` (= staged_palette_words[17] = bank 1 entry 1, since `0x200022 - 0x200000 = 0x22 = entry 17` of arcade palette RAM, and bank 1 starts at `0x200020`)

  Alternative: compute via `lea staged_palette_words+34, %a0; move.w %d4, (%a0)` for clarity.
  5. `move.b #1, palette_dirty`
  6. `movem.l (%sp)+, %d0-%d4`
  7. `rts`

**Helper 3 — `genesistan_palette_hook_45dae`.**

- Same source file (`palette_hooks.s`).
- Signature: matches arcade `0x045DAE` entry — `%d0` = block index (0..7 per Cody §1.4 Site D `cmpiw #8`), `%a0` = source data pointer (set up before `0x045DAE` by upstream code; Cody must verify in implementation).
- Body:
  1. `movem.l %d0-%d7/%a0-%a1, -(%sp)` (full save)
  2. **D0 range check:** the routine writes to `0x200000 + idx*0x80`, so each `idx` covers 4 banks (0x80 bytes / 0x20 per bank). For idx ∈ 0..7, banks touched are `idx*4..idx*4+3`. Banks 0..3 are tilemap-consumed only when `idx == 0` (banks 0..3 = first block). For `idx ≥ 1`, all 4 banks in the block are sprite-side (banks 4..7, 8..11, etc.) → SKIP entirely.
  3. If `idx != 0`, restore registers and RTS (no Genesis-side write).
  4. If `idx == 0`: process the 32 source words (8 banks × 4 words? no — 0x80 bytes / 2 = 64 words; that's 4 banks × 16 words). Wait: 0x80 bytes covers banks 0..3 (4 banks × 32 bytes = 128 bytes = 0x80 bytes). So idx=0 touches all 4 tilemap-consumed banks.
  5. Outer loop `moveq #0, %d2 ; .Lpalette_45dae_bank_loop`: D2 = bank 0..3
  6. Inner loop: 16 entries per bank, applying Step A + Step B per entry, writing to `staged_palette_words[D2*16 + entry]`
  7. `move.b #1, palette_dirty` after the loops complete
  8. `movem.l (%sp)+, %d0-%d7/%a0-%a1` and `rts`

### 1.8.4 Spec changes

- `specs/rastan_direct_remap.json`:
  - Append 3 new opcode_replace entries (per §1.8.2)
  - Update `opcode_replace_count: 90` → `opcode_replace_count: 93`
  - Add to `required_symbols`: `genesistan_palette_hook_59ad4`, `genesistan_palette_hook_3ab00`, `genesistan_palette_hook_45dae`

### 1.8.5 Source changes

- New file: `apps/rastan-direct/src/palette_hooks.s` (3 helpers + section directives + `.extern palette_dirty`, `.extern staged_palette_words`)
- Modified: `apps/rastan-direct/Makefile` (add `palette_hooks.o` to `OBJS`; add assembly rule analogous to existing `pc090oj_hooks.o` rule)
- **No changes to:** `vdp_comm.s`, `boot.s`, `crash_handler.s`, `scene_load.s`, `pc090oj_hooks.s`, `tilemap_hooks.s` (the existing producer-consumer pipeline already wires `palette_dirty` → `vdp_commit_palette` correctly per Andy v3.2-prior §1.3 compliance test)

### 1.8.6 Build pipeline changes

**NONE.**

The runtime hook model means NO scene-specific `.bin` files are needed. The arcade palette source data is read at runtime from the arcade ROM (already embedded in Genesis ROM as `arcade_copy` per `address_map.json`), and the Genesis-side helpers translate on-demand. No `tools/build_rastan_regions.py` changes; no new `.incbin` symbols beyond those already declared.

This is a significant simplification vs the Andy v3.2-prior §1.6.2 plan (which required 3 new `.bin` extraction steps).

### 1.8.7 Verification gates

- Postpatcher invariant: `count_guard = 93` (= 90 + 3 new entries); `bytes` MEASURED by Cody's actual build output (do NOT pre-presume per Build 54 D6-fix discipline).
- Boot-time D00778 verification: PASS (D6 fix patches preserved; Andy v3.2 §1.8 invariants preserved).
- Boot-time VRAM roundtrip self-test: PASS (per Andy v3.2 §6.5; sprite tile DMA path untouched).
- Build 55 boot: CRAM populated dynamically per arcade `0x59AD4` calls. Observable in BlastEm/Exodus/MAME CRAM debugger:
  - At boot: CRAM lines 0..3 may briefly be at emulator default (0x0EEE) until first scene's title-screen `0x59AD4` calls fire
  - After title init: CRAM lines 0..3 should match arcade title palette (compare against MAME `rastan` reference)
  - During gameplay: CRAM lines 0..3 should update per `0x59AD4` calls (e.g., level transition, boss spawn) — verify with MAME side-by-side
- Visible-color comparison: Build 55 title screen color match against MAME reference at 4-color-line precision (full 16-color-per-line precision NOT expected — only 16/4096 arcade colors are sampled into Genesis 4 lines × 16 colors).
- Known limitation accepted: sprites may render with tilemap-tinted colors (PARTIAL_UNKNOWN sprite gap; deferred to Cody Build 56 follow-up per §1.5.2).

---

## §1.9 Architecture compliance verification

The proposed Cody implementation preserves all 10 architectural invariants per Andy v3.2 §1.8:

| Invariant | Compliance | Reasoning |
|-----------|------------|-----------|
| No Genesis-side lifecycle introduced | YES | Helpers invoked by arcade-triggered `0x59AD4` / `0x03AB00` / `0x045DAE` call sites (intercepted via opcode_replace function-body / instruction-replacement). No Genesis-side scheduler, no main-loop, no autonomous palette commit. |
| Helpers RTS-return | YES | All 3 helpers end with `rts`. The dispatch logic (D0 range check, bank gate) uses internal branches but the helper exits via single RTS path. |
| No memory shadowing | YES | `staged_palette_words` is OUTPUT staging (Genesis CRAM-bound, 64 words = 128 bytes = matches CRAM size exactly). NOT an arcade palette RAM mirror. The arcade has 128+ palette banks (~4 KB); we stage only the 4 tilemap-consumed banks (= 64 words). Per Rule 6 / ARCHITECTURE.md, this is staging-then-commit, not shadowing. |
| No scaffolding | YES | The 3 helpers + 3 opcode_replace entries are production-intent; they would exist in a final shipping ROM. No test code, no temporary systems, no diagnostic-only logic. |
| v3.1 Resolution B preserved | YES | `genesistan_pc090oj_hook_slot_init_54052` and its text-RAM clear loops are not touched. |
| v3.2 dispatch contract preserved | YES | `genesistan_hook_3ad44_dispatch` body unchanged; A0 ranges unchanged; tilemap branch unchanged. |
| D6-fix patches in `_3b930` / `_54810` preserved | YES | Both helpers untouched (palette and sprite-emit paths are independent code regions). |
| `opcode_replace` at 0x3AF04 preserved | YES | Spec entry untouched. The 3 new entries are appended (not modifying existing). |
| `_bootstrap` closure preserved | YES | [boot.s:166](apps/rastan-direct/src/boot/boot.s#L166) `jmp (0x00003A200).l` untouched. |
| `_vblank_service` closure preserved | YES | [vdp_comm.s:179](apps/rastan-direct/src/vdp_comm.s#L179) `jmp (0x00003A208).l` untouched. The existing palette gate at [vdp_comm.s:166-170](apps/rastan-direct/src/vdp_comm.s#L166-L170) is unchanged; it now fires correctly because the helpers set `palette_dirty := 1`. |
| Arcade owns execution | YES | Arcade calls `0x59AD4` (now intercepted to helper); arcade reaches `0x03AB00` and `0x045DAE` (now intercepted); arcade resumes after each helper RTS. Arcade still drives all timing. |

All 10 invariants pass.

---

## Phase 2 integrity

| Check | Status |
|-------|--------|
| §1.1 static scene palettes invalidated | YES (4 cited reasons: dynamic callers, runtime D0/D1, partial-bank granularity, bypass writers) |
| §1.2 fix shape classified | `0x59AD4` hook + bypass writer intercepts |
| §1.3 bank-mapping rule derived from LUT | YES — arcade pal[1:0] → Genesis CRAM line[1:0] (1:1) per [pc080sn_attr_lut.bin](build/pc080sn_attr_lut.bin) hex-dump verbatim |
| §1.4 conversion algorithm decided | Option A (faithful 2-step: arcade-raw → xBGR-555 → Genesis CRAM) |
| §1.5 sprite handling decided | Option (a) — work around (skip high-bank Genesis-side writes); Cody Build 56 follow-up specified for refinement |
| §1.6 high-bank treatment | Skip entirely for Build 55; deferred to Cody Build 56 follow-up |
| §1.7 bypass writer intercepts | INTERCEPT 2 of 5: `0x03AB00` (bank 1, tilemap), `0x045DAE` (banks 0..3, tilemap); IGNORE 3 of 5: `0x000264` (unreachable), `0x03AEB6/0x03AEDA` (already NOPed), `0x045DE4` (sprite-side, PARTIAL_UNKNOWN) |
| §1.8 bounded Cody implementation plan produced | YES (3 opcode_replace entries with byte-level original/replacement specs; 3 helpers with full signature + body sketches; spec/source/build pipeline change list; verification gates) |
| §1.9 architecture compliance | 10/10 invariants preserved |
| All conclusions cited (Rule 17) | YES (every claim references Cody evidence section, source file:line, AGENTS_LOG line, design doc section, RULES.md/ARCHITECTURE.md, or Andy v3.2 spec) |
| Conversion is xBGR-555-based, not CLCS (Rule 18) | YES — §1.4 explicitly disproves CLCS; Option A uses arcade-raw → xBGR-555 → CRAM |
| Bank mapping from existing LUT (Rule 19) | YES — §1.3 derived from `pc080sn_attr_lut.bin` hex-dump verbatim |
| Sprite gap handled per Rule 20 | YES — Option (a) work around with deferred Cody follow-up |
| No new evidence collection except sprite (Rule 21) | YES — only sprite-mapping follow-up (§1.5.2) is requested; all design decisions for Build 55 use existing evidence |
| No external sources (Rule 22) | YES — only project artifacts (including local MAME snapshot at `docs/reference/mame/rastan/`) |
| Preserve invariants (Rule 23) | YES — §1.9 verification 10/10 |
| Scope discipline — broad NOP taxonomy NOT performed (Rule 24) | YES — only the 5 bypass writers' specific classifications are made; broad 56-NOP audit remains deferred |
| No source/spec/tool modifications | YES — only this analysis doc + AGENTS_LOG append |
| All STOP conditions either passed or documented | NONE TRIGGERED. The §1.4 palette-source-not-identified observation from Andy v3.2-prior is moot under the runtime-hook model — the source data is read at runtime from arcade ROM via the helper's `%a0` source pointer. The §1.5 PARTIAL_UNKNOWN sprite gap is handled by Option (a) workaround per Rule 20, not by STOP. |

---

## Cross-reference

- `RULES.md` (Rules 1, 4, 5, 6, 8) — architectural compliance
- `ARCHITECTURE.md` (§VBlank Behavior, §Rendering Pipeline, §Helper Functions) — staging-then-commit pattern
- [build/pc080sn_attr_lut.bin](build/pc080sn_attr_lut.bin) — 32-entry LUT (verbatim hex-dumped in §1.3)
- [apps/rastan-direct/src/tilemap_hooks.s:142-164](apps/rastan-direct/src/tilemap_hooks.s#L142-L164) — LUT-index extraction
- [apps/rastan-direct/src/pc090oj_hooks.s:128-136](apps/rastan-direct/src/pc090oj_hooks.s#L128-L136) — sprite palette-line synthesis
- [apps/rastan-direct/src/vdp_comm.s:155-300](apps/rastan-direct/src/vdp_comm.s#L155-L300) — `_vblank_service` palette gate, `vdp_commit_palette`, `staged_palette_words`
- [apps/rastan-direct/src/boot/boot.s:174-184](apps/rastan-direct/src/boot/boot.s#L174-L184) — boot-time staging clear
- [apps/rastan-direct/src/crash_handler.s:285-289](apps/rastan-direct/src/crash_handler.s#L285-L289) — `crash_init_cram` (writes only CRAM[0]=0, CRAM[1]=0x0EEE)
- [apps/rastan/src/main.c:1008-1017](apps/rastan/src/main.c#L1008-L1017) — `convert_xbgr555_to_genesis` (project-canonical)
- [apps/rastan/src/main.c:1020-1024](apps/rastan/src/main.c#L1020-L1024) — `convert_clcs_to_genesis` (DISPROVEN for this path)
- [docs/reference/mame/rastan/src/mame/taito/rastan.cpp](docs/reference/mame/rastan/src/mame/taito/rastan.cpp) lines 305, 455 — palette device binding (xBGR_555)
- `docs/design/Cody_build55_palette_fix_shape_evidence.md` — caller graph, body inspection, fix shape recommendation
- `docs/design/Cody_build55_palette_bank_mapping_evidence.md` — conversion formula, tilemap consumption, sprite consumption (PARTIAL), bypass writers
- `docs/design/Cody_build55_mame_palette_format_evidence.md` — local MAME snapshot, comparison table (CLCS DISPROVEN)
- `docs/design/Cody_palette_deletion_context_audit.md` — context audit
- `docs/design/Andy_build54_palette_root_cause.md` — superseded fix shape (§1.6.2 static-scene plan invalidated by §1.1 here)
- `docs/design/Andy_pc090oj_implementation_spec.md` v3.2 — design authority
- `docs/project/rastan_palette_port_strategy.md` — port strategy reference
