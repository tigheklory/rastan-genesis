# Andy — Build 54 White-CRAM Palette Root Cause Classification

**Agent:** Andy (Claude Code)
**Type:** Architectural classification (analytical synthesis only — no implementation, no new evidence collection)
**Build:** rastan-direct Build 0054 (post-D6-fix, post-v3.2 dispatch)
**Date:** 2026-04-30
**Architecture compliance:** CONFIRMED for the analysis below. The proposed fix preserves all 10 architectural invariants per Andy v3.2 §1.8 (no Genesis-side lifecycle introduced; helper invoked by arcade-triggered scene-load path; staging-then-commit pattern preserved).

---

## 0. Executive verdict

**Cause 1 — Missing palette producer (specified but never built).** DEFINITIVELY CONFIRMED.

Source-level grep across all `apps/rastan-direct/src/*.s` files (including `boot/boot.s`) finds:

- **Zero** code locations write a non-zero value to `palette_dirty` (the only writes are `clr.b palette_dirty` at [boot.s:175](apps/rastan-direct/src/boot/boot.s#L175) and [vdp_comm.s:171](apps/rastan-direct/src/vdp_comm.s#L171), which CLEAR the flag after commit).
- **Zero** code locations populate `staged_palette_words` with arcade palette data (the only writes are the `clr.w` clear loop at [boot.s:180-184](apps/rastan-direct/src/boot/boot.s#L180-L184) which zeros it at boot, plus the read at [vdp_comm.s:277](apps/rastan-direct/src/vdp_comm.s#L277) inside `vdp_commit_palette` which CONSUMES it).

The Genesis-side palette infrastructure is fully built — `vdp_commit_palette` body, `_vblank_service` palette gate, `staged_palette_words` buffer, `palette_dirty` flag, boot-time clear — but **the arcade-triggered producer that fills the staging buffer and sets the dirty flag does not exist in source**. Per AGENTS_LOG.md:21335 the design intent was "DMA D: palette — ROM table → CRAM (128 bytes); per scene change only" — i.e., palette was specified to be loaded alongside scene-load. Currently `load_scene_tiles` in [scene_load.s:27-94](apps/rastan-direct/src/scene_load.s#L27-L94) loads tilemap tiles only; it does NOT load palette. The producer half of the palette pipeline was specified but never implemented.

The observed all-CRAM-white state at frame 100 is consistent with this: `crash_init_cram` at [crash_handler.s:285-289](apps/rastan-direct/src/crash_handler.s#L285-L289) writes only 2 entries (`CRAM[0]=0`, `CRAM[1]=0x0EEE`); the remaining 62 CRAM entries are at the emulator's power-on default state (`0x0EEE` in BlastEm/MAME's Genesis driver). Without a producer, `vdp_commit_palette` never fires, so the arcade palette never reaches CRAM and the screen displays whatever the emulator initialized CRAM to — white.

The prior diagnosis at AGENTS_LOG.md:26027 ("vdp_commit_palette is never called → CRAM never written") is partially superseded: the `.bss`-in-ROM root cause from that era was fixed by the subsequent `[Cody - Implementation, .bss VMA WRAM fix]` entry, but the underlying observation ("vdp_commit_palette never fires") remained true after the BSS fix — for a DIFFERENT reason: **the producer was never built**. This task's analysis is the complete classification of that remaining cause.

The fix is bounded: identify the arcade palette source (ROM table per design intent), extract palette manifests via the existing build pipeline (`tools/build_rastan_regions.py` analogue to the tile manifests already in use), embed them as `.incbin` symbols in `scene_load.s`, and add a palette-load step to `load_scene_tiles` that fills `staged_palette_words` and sets `palette_dirty`. The existing `_vblank_service` palette gate then commits on the next VBlank. No spec change. No v3.2 dispatch change. No new opcode_replace. Producer integration into the existing arcade-triggered `load_scene_tiles` path preserves all 10 invariants.

The white-CRAM bug is INDEPENDENT of the HV Counter trap (separate Cody runtime trace task in progress) — both bugs need to be fixed for full Build 54 correctness, but Cause 1 (palette producer) is the IMMEDIATE blocker for visible color output and is bounded enough to fix without waiting for the HV-trap classification.

---

## §1.1 AGENTS_LOG.md:26027 prior diagnosis (in context)

Read AGENTS_LOG.md ±100 lines around line 26027. The relevant entry is the "Andy - Analysis, VDP init mismatch vs Rainbow Islands" entry. Quote (verbatim):

> root cause identified: linker script (`apps/rastan-direct/link.ld`) places `.bss` section at ROM address space (immediately after `.text`/`.rodata`/`.data` with no VMA override), not at Genesis WRAM (0xFF0000+); all `.bss` variables (`palette_dirty`, `bg_dirty`, `fg_dirty`, `tiles_dirty`, `frame_counter`, `staged_bg_buffer`, `staged_fg_buffer`, `staged_palette_words`, `staged_tile_words`) resolve to ROM addresses; writes to ROM addresses are silently ignored on Genesis; all dirty flags always read as 0 from ROM binary; `vdp_commit_palette` is never called → CRAM never written → BlastEm CRAM debugger empty; display-ON fires but all tile/palette content is zero or random → black screen in BlastEm; Exodus handles ROM-space BSS differently → white/invalid display

Single next correction recommended in that entry: change `link.ld` `.bss (NOLOAD) :` to `.bss 0xFF0000 (NOLOAD) :`.

The follow-up entry "Cody - Implementation, .bss VMA WRAM fix" applied this fix:

> files changed: `apps/rastan-direct/link.ld`, `docs/design/Cody_bss_vma_wram_fix.md`, `AGENTS_LOG.md`
> build produced: YES
> ROM artifact path: `apps/rastan-direct/dist/rastan_direct_video_test.bin`
> `.bss` VMA set to 0xFF0000: YES
> no other behavioral changes made: YES

**Phase context (per surrounding entries):** SGDK era — references to `apps/rastan-direct/src/main_68k.s` (the SGDK-era source file, since renamed/removed), discussions of `init_staging_state`, `arcade_tick_logic`, `palette_init_words`. This is BEFORE the v3.0/v3.1/v3.2 architectural reorganization and BEFORE the current `pc090oj_hooks.s` / `tilemap_hooks.s` / `vdp_comm.s` source layout existed.

**Status of the prior diagnosis:**

- The `.bss`-in-ROM cause: SUPERSEDED. Current `apps/rastan-direct/link.ld:21` shows `.bss 0xFF4000 (NOLOAD) :` (the VMA was further updated from `0xFF0000` to `0xFF4000` in a later phase to leave room for the staging-buffer block). All `.bss` variables now resolve to writable WRAM. Per the recent Build 54 evidence (Cody_build54_cram_white_palette_evidence.md showing `vdp_commit_palette` infrastructure exists and would commit to CRAM if called), the BSS issue is gone.
- The "vdp_commit_palette never called → CRAM never written" observation: STILL CURRENT (verified by Cody's 1.5B-cycle MAME trace showing zero runtime CRAM-target writes). But the CAUSE has shifted — no longer `.bss`-in-ROM (fixed) but rather the absence of any code path that sets `palette_dirty` or fills `staged_palette_words`. This task identifies that new cause.

**Conclusion:** the prior diagnosis is partially superseded; the symptom remains; the cause is now Cause 1 (missing producer), not Cause-zero (BSS in ROM).

---

## §1.2 AGENTS_LOG.md:21335 design intent (in context)

Read AGENTS_LOG.md ±50 lines around line 21335. The relevant context is the "DMA design summary" subsection of the SGDK-era VBlank/VDP architecture summary. Quote (verbatim):

> - DMA design summary
>   - DMA A: tile pattern — ROM → VRAM (32 bytes per miss); fires on cache miss; before plane/SAT.
>   - DMA B: SAT — WRAM shadow → VRAM 0xF800 (640 bytes); every frame; after tile DMA.
>   - DMA C: text/plane — WRAM shadow → Plane A/B VRAM (dirty rows only); every frame.
>   - **DMA D: palette — ROM table → CRAM (128 bytes); per scene change only.**

Surrounding context references:
- `genesistan_palette_rom_table` (a SGDK-era symbol; not present in current source per `grep -n "genesistan_palette_rom_table" apps/rastan-direct/src/*.s` returning zero matches)
- "Palette: ROM table genesistan_palette_rom_table, DMA to CRAM on scene change only."

**Design intent verbatim:** the palette was specified to be loaded from a ROM table (presumably extracted from arcade ROM at build time) into Genesis CRAM (128 bytes = 64 entries × 2 bytes), triggered per scene change (NOT per frame).

**Implementation status:** ASPIRATIONAL / NOT IMPLEMENTED in current source.
- The `genesistan_palette_rom_table` symbol does not exist in current source.
- `apps/rastan-direct/src/scene_load.s` (full file read) loads tiles only via `genesistan_pc080sn_tile_rom`, `genesistan_scene_preload_title`, `genesistan_scene_preload_gameplay`, `genesistan_scene_preload_endround` manifests. NO palette manifests are referenced or loaded.
- Per `Cody_build54_cram_white_palette_evidence.md` §1.6, "arcade ROM palette source: NOT IDENTIFIED" — Cody's static search for the ROM table in arcade ROM did not locate it in this Build 54 cycle.

The design specified a producer; the producer was never built.

---

## §1.3 Palette infrastructure compliance test (Rule 23)

Source inspection across `apps/rastan-direct/src/`:

**Inventory of palette infrastructure:**

| Element | Location | Status |
|---------|----------|--------|
| `staged_palette_words` (64-word staging buffer) | declared at [vdp_comm.s:329](apps/rastan-direct/src/vdp_comm.s#L329) in `.bss` | EXISTS |
| `palette_dirty` (1-byte flag) | declared at [vdp_comm.s:299](apps/rastan-direct/src/vdp_comm.s#L299) | EXISTS |
| `vdp_commit_palette` (CRAM commit helper) | body at [vdp_comm.s:272-280](apps/rastan-direct/src/vdp_comm.s#L272-L280) — sets VDP CRAM-write command, copies 64 words from staging buffer to VDP DATA | EXISTS |
| `_vblank_service` palette gate | [vdp_comm.s:166-170](apps/rastan-direct/src/vdp_comm.s#L166-L170) — `tst.b palette_dirty; beq.s .Lvs_skip_palette; bsr vdp_commit_palette; clr.b palette_dirty` | EXISTS |
| Boot-time staging clear | [boot.s:174-184](apps/rastan-direct/src/boot/boot.s#L174-L184) — clears `palette_dirty` to 0 and `staged_palette_words` to all-zero | EXISTS |
| **Producer** (fills `staged_palette_words` with arcade palette + sets `palette_dirty := 1`) | **NONE** — `grep -nE "palette_dirty\|staged_palette_words" apps/rastan-direct/src/**/*.s` shows zero locations write a non-zero value to `palette_dirty` and zero locations populate `staged_palette_words` with non-zero arcade-palette data | **MISSING** |

**Compliance test (Rule 23):**

- What invokes `_vblank_service`? Per [boot.s vector table at line 87](apps/rastan-direct/src/boot/boot.s#L87), `_vblank_service` is the level-6 (VBlank) interrupt vector. It runs autonomously on every Genesis VBlank, then ends with `jmp (0x00003A208).l` to the arcade VBlank handler ([vdp_comm.s:179](apps/rastan-direct/src/vdp_comm.s#L179)). This is the established Genesis-side commit pattern per Andy v3.2 §1.8 invariants and ARCHITECTURE.md §VBlank Behavior — Genesis VBlank commits staged graphics, then arcade resumes.
- Does the palette gate run autonomously? YES — every VBlank, `_vblank_service` tests `palette_dirty`. If non-zero, calls `vdp_commit_palette`. **This is COMPLIANT** because the gate FIRES only when `palette_dirty != 0`, and `palette_dirty` is set by arcade-triggered code (when such code exists). The Genesis side does not own the trigger — it owns the commit, which is Rule 4 helper-pattern.
- Is `palette_dirty` ever set? **NO. Producer is missing.**
- Is `staged_palette_words` ever populated with non-zero data? **NO. Producer is missing.**

**Classification: HALF-BUILT — infrastructure exists, no producer.**

The Genesis-side palette commit infrastructure is correctly architected per ARCHITECTURE.md §Rendering Pipeline ("Arcade logic → WRAM buffers → VBlank commit → VDP") and Rule 4 (helper-only, RTS-returning). The arcade-side trigger / producer was specified at AGENTS_LOG.md:21335 design intent but was never implemented. The infrastructure waits for a producer that does not exist.

This is NOT a Genesis-owned lifecycle violation (Rule 23 alternative classification): `_vblank_service` calling `vdp_commit_palette` is gated by `palette_dirty`, which is conceptually arcade-controlled. The lifecycle violation would be if `_vblank_service` UNCONDITIONALLY committed palette (Genesis owning timing) — which it does not. The current architecture is compliant in shape; only the producer half is missing.

---

## §1.4 Palette source identification

Cody's prior pass (`Cody_build54_cram_white_palette_evidence.md` §1.6) reported "arcade ROM palette source: NOT IDENTIFIED". Andy's static analysis attempts:

- **Symbol-table search:** `grep -nE "palette\|color\|colram\|cram" apps/rastan-direct/out/symbol.txt` returns matches for Genesis-side symbols only (`palette_dirty`, `staged_palette_words`, `genesistan_palette_clcs` — the SGDK-era PC050CM-bridge symbol, no longer referenced by current source). No symbol points to a ROM-resident palette table.
- **Arcade-source search:** Per Andy v3.2 §1.3.1 LUT specification, the arcade ROM contains tile-attribute LUTs at `genesistan_pc080sn_attr_lut` and tile patterns at `genesistan_pc080sn_tile_rom` (built by `tools/build_rastan_regions.py` and embedded via `.incbin`), but no equivalent palette manifest. The arcade's PC050CM (Taito custom palette chip) sources palette data from arcade ROM via its own DMA path, but that arcade-side palette ROM has not been extracted into a Genesis-side `.bin` file by the current build pipeline.
- **AGENTS_LOG history:** SGDK-era references to `genesistan_palette_rom_table` and `palette_init_words` exist (per the `.bss VMA WRAM fix` entry's variable list and the "diagnostic palette replacement" entry's `palette_init_words` discussion), but those symbols and the source files containing them are absent from current source. The earlier-build palette data was likely a hardcoded diagnostic palette (per "diagnostic palette replacement" entry), not the actual arcade palette extracted from ROM.

**Identified: NO** (in this static-analysis pass).
- arcade_pc of palette source: UNIDENTIFIED
- Number of palette entries: per design intent (line 21335) = 64 entries (128 bytes)
- Referencing arcade routine: UNIDENTIFIED (no opcode_replace currently covers palette load)
- opcode_replace coverage: N/A (no palette path exists in current spec)

This is an EVIDENCE GAP that requires Cody binary investigation to resolve — but it does NOT block this task's classification (Cause 1 is determined definitively from §1.3 producer-absence finding alone). The fix plan in §1.6 specifies the Cody work needed to identify the source data.

---

## §1.5 White-CRAM root cause classification

Based on §1.1 (prior diagnosis superseded), §1.2 (design intent specified producer), §1.3 (infrastructure exists, producer missing), §1.4 (source data not yet identified):

**Cause 1 — Missing palette producer (specified but never built).** DEFINITIVELY CONFIRMED.

**Cited evidence:**

1. **Producer absence in source.** `grep` over all `apps/rastan-direct/src/**/*.s` shows zero non-zero writes to `palette_dirty` and zero non-zero population of `staged_palette_words`. The only writes are clears at boot ([boot.s:175, 180-184](apps/rastan-direct/src/boot/boot.s#L175)) and the post-commit clear in `_vblank_service` ([vdp_comm.s:171](apps/rastan-direct/src/vdp_comm.s#L171)).
2. **Design intent specified producer.** AGENTS_LOG.md:21335: "DMA D: palette — ROM table → CRAM (128 bytes); per scene change only." This was specified during the SGDK era; the v3.0/v3.1/v3.2 reorganization did not port the palette producer.
3. **Cody runtime evidence.** 1.5B-cycle MAME trace shows zero CRAM-target writes after bootstrap. `vdp_commit_palette` is never called because `palette_dirty` is never set.
4. **Visible-bug consistency.** All-CRAM-white observation matches: `crash_init_cram` at [crash_handler.s:285-289](apps/rastan-direct/src/crash_handler.s#L285-L289) writes only `CRAM[0]=0, CRAM[1]=0x0EEE`. The remaining 62 CRAM entries display the emulator's power-on default (0x0EEE in BlastEm/MAME). Without a producer, the arcade palette never reaches CRAM, regardless of whether the crash handler runs.

**Cause 2 (NOPed arcade palette path) ruled out:** Per Cody_build54_nop_provenance_audit.md, the 6 focus NOPs target arcade chip I/O (TC0220IOC at 0xC50000, PC090OJ DMA-trigger at 0xD01BFE) — NOT palette. The broader 56-NOP set is documentary; none of them suppresses an arcade palette-load instruction. The producer is not deleted-without-replacement; **it was never written**. (Per Rule 24 — broad 56-NOP classification is OUT OF SCOPE for this task; Andy classifies only that none of the 6 focus NOPs is palette-related.)

**Cause 3 (Genesis-owned subsystem violation) ruled out:** Per §1.3 compliance test, `_vblank_service` palette gate is correctly conditional on `palette_dirty`; it does NOT autonomously commit. The architecture is compliant in shape.

**Cause 4 (Blocked upstream) ruled out as primary:** While the HV Counter crash (separate Cody investigation) DOES cause `crash_init_cram` to fire and contributes to the visible all-white state, the palette producer absence is independent. Even without the HV crash, the screen would still be white (or the emulator's CRAM default) because no producer exists. Fixing the upstream HV crash alone would not make the arcade palette appear in CRAM.

**Cause 5 (Palette source data missing/wrong) ruled out as primary:** While the arcade ROM palette source is currently UNIDENTIFIED in static analysis (§1.4), this is downstream of the producer-absence. Even if the source data were identified and embedded, no producer would consume it. The producer is the load-bearing missing piece; source-data extraction is a sub-task within the producer-build.

**Final cause: Cause 1.**

---

## §1.6 Bounded immediate fix plan

### 1.6.1 Categorization (per Chad's framework)

**Identify arcade palette routine → add Genesis-side helper that fills staging + sets dirty flag.**

The fix has two parts: (a) data source extraction (one-time build pipeline addition), (b) producer integration into existing arcade-triggered `load_scene_tiles` path (one source-file change).

### 1.6.2 Concrete steps for downstream Cody work

Step 1 (data source extraction):

- Identify the arcade ROM palette table address(es) for each scene (title / gameplay / endround per the existing `genesistan_scene_preload_*` manifests). This requires reading arcade source disassembly (`build/maincpu.disasm.txt`) and/or MAME's rastan driver source to locate where the arcade's PC050CM palette chip is loaded from.
- Add a palette extraction step to `tools/build_rastan_regions.py` (or analogue) producing scene-specific palette `.bin` files: e.g., `build/pc050cm_palette_title.bin`, `build/pc050cm_palette_gameplay.bin`, `build/pc050cm_palette_endround.bin`. Each is 128 bytes (64 RGB-444 words) per design intent.
- The arcade palette format is RGB-444 (12-bit color, encoded as 16-bit words with format `0xxx_RRRR_GGGG_BBBB` or similar Taito convention). Genesis CRAM format is RGB-333 (9-bit color, encoded `0000_BBB0_GGG0_RRR0`). The extraction step must convert RGB-444 → RGB-333 (or whichever transformation matches the prior April-6 / SGDK-era palette path).

Step 2 (producer integration):

- Add three new `.incbin` symbols to [scene_load.s](apps/rastan-direct/src/scene_load.s) `.rodata` section, parallel to the existing `genesistan_scene_preload_*` tile manifests:

  ```asm
  .global genesistan_scene_palette_title
  genesistan_scene_palette_title:
      .incbin "../../build/pc050cm_palette_title.bin"
  .global genesistan_scene_palette_gameplay
  genesistan_scene_palette_gameplay:
      .incbin "../../build/pc050cm_palette_gameplay.bin"
  .global genesistan_scene_palette_endround
  genesistan_scene_palette_endround:
      .incbin "../../build/pc050cm_palette_endround.bin"
  ```

- Add a palette-load step to `load_scene_tiles` ([scene_load.s:27-94](apps/rastan-direct/src/scene_load.s#L27-L94)) that:
  - Selects the appropriate palette source per scene id (`%d6`)
  - Copies 64 words from the selected source to `staged_palette_words`
  - Sets `palette_dirty := 1`
  - Returns via existing `rts` at line 94

  Insertion point: after `.Lload_scene_pairs_done:` (line 76, where scene-id is finalized) and before the final `rts` at line 94 — the palette load runs ONCE per scene change, alongside the existing tile load. Approximate added code:

  ```asm
  /* §1.6.2 palette-load: fill staged_palette_words + set dirty */
  lea     genesistan_scene_palette_title, %a2
  cmpi.w  #1, %d6
  bne.s   .Lload_scene_palette_check_endround
  lea     genesistan_scene_palette_gameplay, %a2
  bra.s   .Lload_scene_palette_ready
  .Lload_scene_palette_check_endround:
  cmpi.w  #2, %d6
  bne.s   .Lload_scene_palette_default
  lea     genesistan_scene_palette_endround, %a2
  bra.s   .Lload_scene_palette_ready
  .Lload_scene_palette_default:
  /* %d6 = 0 (title) — already loaded into %a2 above */
  .Lload_scene_palette_ready:
  lea     staged_palette_words, %a3
  moveq   #(64 - 1), %d7
  .Lload_scene_palette_copy:
      move.w  (%a2)+, (%a3)+
      dbra    %d7, .Lload_scene_palette_copy
  move.b  #1, palette_dirty
  ```

  The `palette_dirty` symbol is already declared `.extern` per existing `boot.s:7` style; `scene_load.s` will need a similar `.extern palette_dirty` declaration.

Step 3 (postpatcher invariant update):

- The fix adds source bytes (Genesis ROM grows) but no spec changes (`opcode_replace_count` stays at 90 per Andy v3.2 §9). The postpatcher's `count_guard=90, bytes=??` invariant updates per the new ROM size (measured-not-presumed per Build 54 fix discipline).

Step 4 (verification):

- Boot Build 55 ROM. Observe CRAM via emulator debugger.
- Expected: CRAM populated with 64 distinct RGB-333 entries from `genesistan_scene_palette_title` after first VBlank; not all 0x0EEE.
- Observed-color match against arcade reference (MAME rastan running the same scene): pixel-color-correct.

### 1.6.3 What this fix does NOT touch

- v3.1 closures (Resolution B for 0x54052, LUT MUST NOT consultation, jsr-not-bsr): UNTOUCHED
- v3.2 dispatch contract (`genesistan_hook_3ad44_dispatch` polymorphic-utility A0 dispatch): UNTOUCHED
- D6-fix patches in `_3b930` / `_54810`: UNTOUCHED
- `opcode_replace` at arcade_pc 0x3AF04: UNTOUCHED
- `_bootstrap` ending with `jmp (0x3A200).l`: UNTOUCHED
- `_vblank_service` ending with `jmp (0x3A208).l`: UNTOUCHED
- `vdp_commit_palette` body, `_vblank_service` palette gate, boot-time staging clear: UNTOUCHED (already correct per §1.3)
- 18-entry opcode_replace count (Andy v3.2 final = 90): UNTOUCHED (no new opcode_replace required; the fix integrates into the existing arcade-triggered `load_scene_tiles` path which was already invoked per Andy v3.2 boot/hook chain)
- The 6 focus NOPs and the broader 56-NOP set: UNTOUCHED (per Rule 24 — out of scope for this task; deferred to §1.9 follow-up)
- The HV Counter trap investigation: UNTOUCHED (separate Cody runtime trace in progress; both bugs need separate fixes, but Cause 1 is bounded enough to fix in parallel)

### 1.6.4 Why this is bounded and not a v3.3 spec revision

The fix is purely a **producer addition inside an existing helper** (`load_scene_tiles`) that was already part of the architecture per Andy v3.2 §1.3. No new opcode_replace is added; the producer is invoked by the existing arcade-triggered scene-load path (called from `_bootstrap` at [boot.s:158](apps/rastan-direct/src/boot/boot.s#L158) for the initial title scene, and from `tilemap_hooks.s:108` for subsequent scene changes triggered by arcade BG hook). The architecture is unchanged; only an unimplemented half of the existing pipeline gets implemented.

This is the kind of addition Andy v3.2's spec already presumed exists (per the staging-then-commit pattern documented throughout). The spec did not enumerate `staged_palette_words` producer details because the SGDK-era design (line 21335) was assumed-portable and the v3.0/v3.1/v3.2 reorganization focused on PC090OJ Strategy A. Filling in the palette producer now is closing a gap, not revising the architecture.

---

## §1.7 Conditional specific-NOP classification

**N/A — Cause not 2.**

§1.5 selected Cause 1 (Missing palette producer). Cause 2 (NOPed arcade palette path) is ruled out: none of the 6 focus NOPs in `Cody_build54_nop_provenance_audit.md` targets a palette-load instruction. The broader 56-NOP audit may surface palette-related NOPs in a follow-up Andy task (per §1.9), but for this task, no specific NOP requires classification.

---

## §1.8 Architecture compliance verification

The proposed fix preserves all 10 architectural invariants per Andy v3.2 §1.8:

| Invariant | Compliance | Reasoning |
|-----------|------------|-----------|
| No Genesis-side lifecycle introduced | YES | The producer is added INSIDE `load_scene_tiles`, which is invoked by arcade-triggered code (initial boot for title, then per-scene-change via tilemap BG hook). The producer runs only when arcade flow reaches scene-load. No new lifecycle, no new scheduler, no new main-loop. |
| Helpers RTS-return | YES | `load_scene_tiles` continues to end with `rts` (line 94). The added palette-load step is in-line within the existing helper body; control flow returns through the existing RTS. |
| No memory shadowing | YES | `staged_palette_words` is an OUTPUT staging buffer (Genesis SAT/CRAM-bound), not an arcade-memory mirror. It does not contain arcade-side state; it contains the converted Genesis CRAM data. Per ARCHITECTURE.md §Rendering Pipeline, this is the canonical staging-then-commit pattern. |
| No scaffolding | YES | The fix is production-intent — closes a real gap in the rendering pipeline (no scene's palette currently reaches CRAM). The palette load would exist in a final shipping ROM. |
| v3.1 Resolution B preserved | YES | `genesistan_pc090oj_hook_slot_init_54052` and its text-RAM clear loops are not touched. |
| v3.2 dispatch contract preserved | YES | `genesistan_hook_3ad44_dispatch` body unchanged; A0 ranges unchanged; tilemap branch unchanged. |
| D6-fix patches in `_3b930` / `_54810` preserved | YES | Both helpers untouched. |
| `opcode_replace` at 0x3AF04 preserved | YES | Spec entry untouched (no spec change at all). |
| `_bootstrap` closure preserved | YES | [boot.s:166](apps/rastan-direct/src/boot/boot.s#L166) `jmp (0x00003A200).l` untouched. |
| `_vblank_service` closure preserved | YES | [vdp_comm.s:179](apps/rastan-direct/src/vdp_comm.s#L179) `jmp (0x00003A208).l` untouched. The existing palette gate at [vdp_comm.s:166-170](apps/rastan-direct/src/vdp_comm.s#L166-L170) is unchanged; it now actually fires on the next VBlank after `load_scene_tiles` because the producer sets `palette_dirty`. |

All 10 invariants pass.

---

## §1.9 Follow-up NOP audit task scope (DEFERRED — DO NOT EXECUTE)

The broader 56-NOP audit applying the rules-violation test (Class A/B/C/D/E classification) to all 30 no-companion NOPs is **OUT OF SCOPE** for this task per Rule 24 (palette root cause first, NOP taxonomy deferred).

**Specification for the follow-up Andy task:**

- **Goal:** apply the rules-violation test (per Cody_build54_nop_provenance_audit.md framework) to all 30 NOPs that have no companion helper, classifying each as:
  - Class A: NOP with intentional behavior-suppression role (architecturally compliant)
  - Class B: NOP suppressing arcade chip I/O that has no Genesis equivalent (compliant)
  - Class C: NOP suppressing arcade behavior without Genesis-side replacement, breaking arcade intent (RULES.md violation per Rule 8)
  - Class D: NOP whose original arcade purpose is unknown / not yet audited
  - Class E: NOP that should be replaced with a JSR-helper opcode_replace
- **Scope:** all 30 no-companion NOPs in `specs/rastan_direct_remap.json`
- **Output:** separate Andy classification document; if any NOP is Class C or E, separate Cody implementation tasks for each
- **Trigger:** ONLY after the immediate palette fix lands in Build 55 AND the white-CRAM bug is verified resolved (per emulator CRAM observation matching arcade reference). Do not start the broader audit while Build 55 is unverified.

---

## Phase 2 integrity

| Check | Status |
|-------|--------|
| §1.1 AGENTS_LOG.md:26027 read in context | YES (±100 lines read; SGDK-era VDP-init entry verbatim quoted; followed by `.bss VMA WRAM fix` Cody implementation entry) |
| Prior diagnosis status | SUPERSEDED in cause (`.bss`-in-ROM fixed); SYMPTOM CURRENT (`vdp_commit_palette never called`) |
| §1.2 AGENTS_LOG.md:21335 read in context | YES (±50 lines; "DMA D: palette — ROM table → CRAM (128 bytes); per scene change only" verbatim quoted) |
| Design intent captured | YES (palette source = arcade ROM table; trigger = per scene change; size = 128 bytes / 64 entries; implementation status = aspirational, never implemented) |
| §1.3 palette infrastructure compliance | HALF-BUILT (infrastructure exists and is compliant in shape; producer is missing) |
| §1.4 palette source identified | NO (not identified in current static analysis; Cody binary follow-up specified in §1.6.2 step 1) |
| §1.5 white-CRAM cause | **Cause 1 — Missing palette producer** (definitively confirmed) |
| §1.6 bounded fix plan produced | YES (4-step plan: source data extraction → manifest .incbin → producer in `load_scene_tiles` → postpatcher invariant update) |
| §1.7 conditional specific-NOP classification | N/A (Cause not 2) |
| §1.8 architecture compliance | 10/10 invariants preserved by proposed fix |
| §1.9 follow-up task scope specified (not executed) | YES (broader 56-NOP audit deferred until Build 55 verified) |
| All conclusions cited (Rule 17) | YES (every claim references AGENTS_LOG line, source file:line, Cody evidence section, RULES.md/ARCHITECTURE.md, or Andy v3.2 spec) |
| "Tagged" vs "actual" phase distinction made (Rule 18) | YES (SGDK era explicitly distinguished from current; `genesistan_palette_rom_table` SGDK-era symbol noted as absent from current source; `palette_init_words` SGDK-era diagnostic palette noted as superseded) |
| Prior-framing discipline maintained (Rule 19) | YES (the "6 NOPs broke palette" framing is explicitly disproven; cause is independent producer-absence, not NOP-related) |
| Scope discipline (Rule 24) — broad NOP taxonomy NOT performed | YES (only the 6 focus NOPs' non-palette-relatedness was noted in §1.5; broader audit deferred to §1.9) |
| No new evidence collection (Rule 20) | YES (only existing source files, AGENTS_LOG history, and Cody evidence packages used) |
| No source/spec/tool modifications | YES (only this analysis doc + AGENTS_LOG append) |
| STOP conditions | NONE TRIGGERED. Cause classification is definitive (Cause 1). The §1.4 palette-source-not-identified observation is acknowledged but does not block the fix plan — the source identification is the FIRST STEP of the §1.6 fix plan, to be done by Cody during implementation. |

---

## Cross-reference

- `RULES.md` (Rules 1, 4, 5, 8) — architectural compliance check
- `ARCHITECTURE.md` (§VBlank Behavior, §Rendering Pipeline) — palette commit pattern
- [apps/rastan-direct/src/vdp_comm.s:155-300](apps/rastan-direct/src/vdp_comm.s#L155-L300) — `_vblank_service` palette gate, `vdp_commit_palette`, `palette_dirty`, `staged_palette_words`
- [apps/rastan-direct/src/boot/boot.s:174-184](apps/rastan-direct/src/boot/boot.s#L174-L184) — boot-time staging clear (clears `palette_dirty`, `staged_palette_words`)
- [apps/rastan-direct/src/scene_load.s:27-94](apps/rastan-direct/src/scene_load.s#L27-L94) — `load_scene_tiles` (current; needs producer addition per §1.6.2)
- [apps/rastan-direct/src/crash_handler.s:285-289](apps/rastan-direct/src/crash_handler.s#L285-L289) — `crash_init_cram` (writes only CRAM[0]=0, CRAM[1]=0x0EEE; not the full all-CRAM-white source)
- AGENTS_LOG.md:26027 — prior `.bss`-in-ROM diagnosis (now SUPERSEDED in cause; symptom remains)
- AGENTS_LOG.md:21335 — palette DMA design intent (line: "DMA D: palette — ROM table → CRAM (128 bytes); per scene change only")
- `docs/design/Cody_build54_cram_white_palette_evidence.md` — primary input (CRAM contents observed; commit infrastructure exists; palette source unidentified)
- `docs/design/Cody_build54_nop_provenance_audit.md` — secondary input (focus 6 NOPs target chip I/O, not palette; broader 56-NOP set deferred to §1.9 follow-up)
- `docs/design/Andy_pc090oj_implementation_spec.md` v3.2 — design authority
- `docs/design/Andy_build54_hvc_writer_root_cause.md` — separate independent-bug investigation (HV Counter trap; Cody runtime trace in progress)
- `docs/design/Andy_build53_d0_origin_root_cause.md` — prior cycle (D6 fix preserved by this task)
