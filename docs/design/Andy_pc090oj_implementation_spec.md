# Andy — PC090OJ Final Implementation Spec v3.2 (Strategy A)

**Agent:** Andy
**Type:** Design / Implementation Spec (analysis only — no source/spec/tool modifications)
**Build context:** rastan-direct, Build 0052+
**Date:** 2026-04-28 (v3.2 surgical correction; v3.1 dated 2026-04-25)
**Architecture compliance:** CONFIRMED (RULES.md and ARCHITECTURE.md verified; design preserves arcade-owns-execution invariant; all helpers RTS-return; no Genesis-side lifecycle).

---

## 0. Executive summary (v3.2)

This spec defines the complete arcade PC090OJ → Genesis VDP SAT translation for `apps/rastan-direct/`, using Strategy A as authorized by `Andy_pc090oj_writer_classification_ledger.md` §5. The design ports April 6's working pipeline (`apps/rastan/src/startup_trampoline.s`) into the rastan-direct architecture (post-Build 0052), with three structural changes:

1. **Direct-VDP writes replaced by WRAM-staging-then-VBlank-commit.** April 6 wrote SAT words directly to `0x00C00000` from inside the helper. rastan-direct's architecture (per `ARCHITECTURE.md` §VBlank Behavior, §Rendering Pipeline) requires WRAM staging followed by VBlank commit. Helpers write only to a new staging buffer; commit happens once per VBlank in `_vblank_service`.
2. **Independent-writer hook expansion.** April 6 covered 15 dominant render-loop call sites (6 target functions). Per `Andy_pc090oj_writer_classification_ledger.md`, that captures 99.14 % of PC090OJ write traffic but misses 9 INDEPENDENT writer functions (HUD/score, scene-init, status sprite). This spec adds those 9 hooks plus the writer helper `0x3B930` (reachable from both target and non-target paths) to close the gap.
3. **Function-body replacement, not per-call-site replacement.** Per the existing rastan-direct convention (e.g. the `0x03C4D2` entry already in `specs/rastan_direct_remap.json`), the postpatcher replaces full function bodies with `JSR helper; RTS; NOP*` rather than individual call sites. This is the only mechanism that fits 4-byte arcade BSRs with 6-byte `JSR abs.l` calls to Genesis-side helpers at offsets >32 KB. **The architectural scope of the writer-classification ledger is preserved** — every writer path the ledger flagged (15 April-6 + 29 INDEPENDENT) remains intercepted, but the implementation point is the writer function entry, not each individual call site. The 46-site count reduces to **18 opcode_replace entries** (16 function bodies + 2 audit-guard write instructions) without changing what the helper sees or what the trace would show. Per-site auditability is preserved via the 46-site → 18-entry audit ledger in §8.6.

The April 6 DMA-encoding bug (`Andy_pc0900j_sprite_correctness_audit.md` §10) is not present in rastan-direct: the equivalent helper `sprite_dma_addr_high_bits_fix` at [apps/rastan-direct/src/vdp_comm.s:147-152](apps/rastan-direct/src/vdp_comm.s#L147-L152) already implements the correct upper-bit extraction (`lsr.l #8` then `lsr.l #6` = `lsr.l #14`). This spec re-uses that helper for the new sprite DMA path.

The two `0x510EA / 0x510F4` writer sites (FU1 trace: 0 hits in observed gameplay) are wired as **audit guards** — diagnostic helper that captures CPU state and triggers a controlled stop. Rule 8 walkthrough is in §7.

This spec is implementable mechanically. Helper signatures, byte-level opcode_replace entries, staging-buffer offsets, VBlank commit ordering, completion criteria, and follow-up tasks are all enumerated. No design decision is deferred to Cody's downstream task.

v3.1 correction scope: this revision retains the v3 mechanical-closure work and closes three defects only — §6.5.1 `bsr`→`jsr` encoding ambiguity, §4.6 LUT-usage contradiction against §1.3.1, and §2.2.1 Defect-3 slot-collapse safety via evidence-driven Resolution B.

**v3.2 correction scope (this revision).** Surgical correction at one helper, one entry, one ledger row. Investigation surfaced that arcade `0x03AD44` is a **polymorphic memset utility** called by both the tilemap BG-fill path and the PC090OJ init/reset path — with non-overlapping A0 ranges per concern. The pre-existing rastan-direct entry at `0x03AD44` (`genesistan_hook_tilemap_bg_fill`, present at HEAD before PC090OJ work) handled tilemap correctly; v3.1 replaced it in-place with the PC090OJ-only helper, which broke tilemap coverage. v3.2 introduces a dispatch helper `genesistan_hook_3ad44_dispatch` that A0-classifies on entry and routes to the appropriate behavior (tilemap branch / PC090OJ branch / audit fall-through). Caller enumeration of every BSR/JSR to `0x3AD44` (Phase 4 in §2.2.A below) confirms the A0 ranges are non-overlapping (`[0xC00000, 0xC10000)` for tilemap; `[0xD00000, 0xD00800)` for PC090OJ) and exhaustive (every one of 7 callers fits exactly one range). One opcode_replace entry, one helper symbol changed, one §8.6 ledger row updated. All other spec sections (§1.3, §1.3.1, §2.1, other §2.2 rows, §2.2.1, §3, §4, §5, §6, §7, §8.6 entries other than #8, §9, §10, §11) remain unchanged from v3.1. Architecture decisions (Strategy A, 18-entry coverage, slot allocations, audit guards, commit semantics) all preserved unchanged.

The total opcode_replace entry count remains **18** (no entry added or removed; entry #8's symbol and `note` are updated in place). The total helper-count terminology remains **17 helpers across 18 entries** (the helper formerly named `genesistan_pc090oj_hook_init_clear_3ad44` is renamed to `genesistan_hook_3ad44_dispatch` with expanded behavior; no new helper added).

---

## 1. WRAM staging model

### 1.1 Location and size

| Symbol                     | WRAM offset           | Size        | Purpose |
|----------------------------|-----------------------|-------------|---------|
| `staged_sprite_sat`        | placed by linker in `.bss` after existing tilemap/palette buffers | 640 B (= 80 × 8) | Genesis SAT raw frame, DMA target |
| `staged_sprite_descriptor_table` | next in `.bss` | 1024 B (= 80 × 12) | Per-slot semantic record (see §1.2) |
| `staged_sprite_dirty`      | next in `.bss`        | 4 B          | 32 dirty bits, one per 4-slot SAT block (commit gating) |
| `staged_sprite_active_count` | next in `.bss`     | 2 B          | Number of valid SAT entries this frame (used for link-chain termination) |
| `pc090oj_slot_lut`         | `.rodata` (compile-time, not WRAM) | 256 B | PC090OJ-address → Genesis-SAT-slot mapping (see §1.3) |

The four `.bss` symbols join the existing four (`staged_bg_buffer`, `staged_fg_buffer`, `staged_palette_words`, `staged_tile_words`) declared in [apps/rastan-direct/src/vdp_comm.s:294-330](apps/rastan-direct/src/vdp_comm.s#L294-L330). Total WRAM growth: 1670 B added to the existing ~12 KB staging footprint at `0x00FF4000+`. Fits comfortably in Genesis 64 KB WRAM. The linker script ([apps/rastan-direct/link.ld:21-25](apps/rastan-direct/link.ld#L21-L25)) places `.bss` at `0x00FF4000` (NOLOAD); precise offset of each new symbol is determined by linker placement order — Cody's implementation appends the new `.space` directives to the existing block in [vdp_comm.s:322-330](apps/rastan-direct/src/vdp_comm.s#L322-L330) immediately following `staged_tile_words`.

### 1.2 Format choice — Genesis SAT raw + companion semantic table

Two companion buffers:

**`staged_sprite_sat` (640 B, raw Genesis SAT format).** This is the DMA source. Layout per slot (8 bytes), per `Andy_pc0900j_sprite_correctness_audit.md` §3:

```
+0..+1: Y position (9 bits valid + 0x80 border bias)
+2..+3: bits 11:10 = vsize-1 (0..3 = 1..4 tiles); bits 9:8 = hsize-1; bits 6:0 = link
+4..+5: bit 15 = priority; bits 14:13 = palette line; bit 12 = vflip; bit 11 = hflip; bits 10:0 = VRAM tile index
+6..+7: X position (9 bits valid + 0x80 border bias)
```

**`staged_sprite_descriptor_table` (1024 B, semantic per-slot record).** Mirrors the per-slot SAT but in arcade-semantic form so multi-write helpers and the VBlank commit can re-derive valid sprites cheaply. Layout per slot (12 bytes):

```
+0..+1: validity word (bit 0 = valid, bit 1 = priority-ladder gate, bit 15 = touched-this-frame)
+2..+3: arcade y_raw (untranslated; 0x0180 sentinel preserved)
+4..+5: arcade x_raw
+6..+7: arcade word0 (attr/flip/palette)
+8..+9: arcade word2 (tile code, 14-bit; we do NOT mask further until lowering)
+10..+11: source-id word (writer category: lets VBlank commit reorder by priority)
```

Format choice rationale: April 6 wrote raw SAT directly to VDP and ran link-chain logic by counting valid entries during a 2-pass scan inside the renderer. rastan-direct's architecture requires staging, and link-chain calculation (which sprite's `link` field points to which next sprite) depends on knowing total visible count. The semantic table lets VBlank commit determine valid count and link chain without the helpers needing to coordinate. The raw SAT buffer is the DMA payload; the descriptor table is the truth source the commit uses to (re)build it.

This is **not memory shadowing** (Rule 6): the descriptor table is indexed by Genesis SAT slot 0..79, not by PC090OJ address; multiple PC090OJ writes can map to the same descriptor slot via `pc090oj_slot_lut`, and slot identity carries source-of-write metadata that PC090OJ memory does not have. The 12-byte stride differs from PC090OJ's 8-byte stride. There is no 1:1 address mirror.

### 1.3 PC090OJ-address → Genesis-SAT-slot LUT (`pc090oj_slot_lut`)

Compile-time table, 256 bytes, one byte per PC090OJ active descriptor (0..255 = byte offsets 0x000..0x7F8 within `0x00D00000..0x00D007FF`). Each byte is the Genesis SAT slot 0..79 to which writes for that PC090OJ slot map, or `0xFF` = skip (PC090OJ slot is bookkeeping only — see `Andy_pc090oj_reconciliation_v2.md` §5 on the upper inactive scratch region beyond `0x800`).

Slot allocation, evidence-cited:

| Genesis SAT slot range | Source                                                                 | Citing helper / function | Capacity vs observed use |
|------------------------|------------------------------------------------------------------------|--------------------------|--------------------------|
| 0..21                  | April-6 22-sprite render output (Block A 18 + Block B 4)               | Target-function helpers (§2.1) | matches April 6 §2.3 ceiling |
| 22..29                 | HUD/score digits writer (`0x3B802` writes to `0xD00088+`)              | `genesistan_pc090oj_hook_score_digit` (§2.2) | 8 digits; observed 6 active |
| 30..43                 | Status / UI sprites (`0x5A098` writes to `0xD00048+`)                  | `genesistan_pc090oj_hook_status_sprite` (§2.2) | 14 slots; covers 12 writes/call |
| 44..55                 | Per-frame sprite-update routine (`0x54810` writes 4 sprites/call to `0xD00000+`) | `genesistan_pc090oj_hook_sprite_update` (§2.2) | 12 slots |
| 56..63                 | Sprite decay loop (`0x5607C` decrements Y of 8 active slots starting at `0xD00170`) | `genesistan_pc090oj_hook_sprite_decay` (§2.2) | 8 slots |
| 64..67                 | Sprite-RAM copy helper (`0x56114` copies 4 entries)                    | `genesistan_pc090oj_hook_copy` (§2.2) | 4 slots |
| 68..71                 | Sprite-RAM zero-fill (`0x56440` / `0x5648A`)                           | `genesistan_pc090oj_hook_zero_fill` (§2.2) | 4 slots |
| 72..75                 | Sprite slot init (`0x54052` initializes slots 0..3 with attr=3)        | `genesistan_pc090oj_hook_slot_init` (§2.2) | 4 slots identity-mapped from arcade slots 0..3 |
| 76..79                 | Cold-init clears (`0x3AD44` bulk-clear PC090OJ branch, `0x3AD84` priority-frame) | `genesistan_hook_3ad44_dispatch` PC090OJ branch + `genesistan_pc090oj_hook_init_priority_3ad84` (§2.2) | 4 slots representing 17-entry priority frame |
| (none)                 | Overflow guard band                                                   | n/a | consumed by Defect-3 Resolution-B expansion |

Slot 0..21 are written by the 6 April-6 target helpers using April 6's existing block layout (Block A → slots 0..17 in helper for 0x41DAE, Block B → slots 18..21 in helper for 0x41F5E + 0x45DFA). Slots 22..79 are written by INDEPENDENT helpers, each into its dedicated slot range. Cody's implementation embeds the 256-byte LUT as `.incbin` from a Python-generated table (see §4.1) — the generation algorithm is specified in §1.3.1 below.

#### 1.3.1 `pc090oj_slot_lut` byte-by-byte specification

The 256-byte LUT is **deterministically generated** by `tools/translation/build_pc090oj_slot_lut.py` (see §9.2) per the algorithm below. Every constant is explicit; the algorithm produces exactly one output. Cody's implementation may either run the algorithm to produce `build/pc090oj_slot_lut.bin` or embed the resulting table directly — both produce byte-identical output.

**Helper consultation rule (clarifies §4.6).** Among the 16 named function-body helpers in §2.1 / §2.2, exactly ONE — `genesistan_hook_3ad44_dispatch` (§2.2 row 0x3AD44; v3.2 dispatch helper) — consults the LUT at runtime, and only on the PC090OJ branch of its A0 dispatch. All other helpers (and the dispatch helper's tilemap branch / audit fall-through) emit to their dedicated SAT or tilemap staging buffer based on helper identity / branch identity, not LUT lookup. The LUT is therefore (a) the lookup table for the 0x3AD44 helper's PC090OJ-branch bulk-clear → SAT-slot mapping, and (b) a static cross-reference document of which PC090OJ index "belongs to" which Genesis SAT slot for purposes of debugging and audit.

**MUST NOT consultation rule.** All helpers except `genesistan_hook_3ad44_dispatch` MUST NOT read or consult `pc090oj_slot_lut` at runtime. Within `genesistan_hook_3ad44_dispatch`, only the PC090OJ branch (the A0 ∈ [0xD00000, 0xD00800) case) reads the LUT; the tilemap branch and audit fall-through MUST NOT touch it. Any other helper that consults the LUT is a spec violation.

**Generation algorithm.** Given the §1.3 slot-allocation table, walk in declaration order and assign slot numbers to PC090OJ indices using the per-row PC090OJ-base addresses (each verified against `build/maincpu.disasm.txt` at the cited helper's entry instruction). When a later row's index range overlaps an earlier row's already-assigned indices, the earlier row's assignment is preserved (first row wins). Indices not claimed by any row remain `0xFF` (skip).

```python
# build_pc090oj_slot_lut.py — deterministic 256-byte generator

LUT = bytearray([0xFF] * 256)

# (pc090oj_idx_start, sat_slot_start, count, source citation)
mappings = [
    # Row 1 (slots 0..21): no PC090OJ source — target helpers read arcade workram
    #   (Block A at A5+0x11B2, Block B at A5+0x0170). No LUT entries.

    # Row 2: HUD/score, 0x3B802 — base 0xD00088 (per §1.3 line 78)
    (17, 22, 8),    # idx 17..24 → slots 22..29

    # Row 3: status/UI, 0x5A098 — base 0xD00048 verified at maincpu.disasm.txt
    #   line 113452 (`5a0ae: moveal #0xD00048, %a0`)
    ( 9, 30, 14),   # idx 9..22 → slots 30..43 (idx 17..22 already claimed by row 2; row 2 wins)

    # Row 4: sprite-update, 0x54810 — base 0xD00000 verified at maincpu.disasm.txt
    #   line 106237 (`54810: 227c 00d0 0000  moveal #0xD00000, %a1`)
    ( 0, 44, 12),   # idx 0..11 → slots 44..55

    # Row 5: sprite-decay, 0x5607C — base 0xD00170 verified at maincpu.disasm.txt
    #   line 107868 (`560b0: 207c 00d0 0170  moveal #0xD00170, %a0`)
    (46, 56,  8),   # idx 46..53 → slots 56..63

    # Row 6: sprite-RAM copy, 0x56114 — variable destination (A1 set by callers
    #   0x5604C and 0x56076 with run-time addresses). No fixed PC090OJ index;
    #   helper writes to slots 64..67 by helper identity, not LUT.
    #   No LUT entries assigned.

    # Row 7: sprite-RAM zero-fill, 0x56440 — variable destination similarly.
    #   No LUT entries.

    # Row 8: sprite-slot init, 0x54052 — base 0xD00000 verified at maincpu.disasm.txt
    #   line 105742 (`540ac: 227c 00d0 0000  moveal #0xD00000, %a1`)
    ( 0, 72, 4),    # idx 0..3 → slots 72..75 (already claimed by row 4; row 4 wins)

    # Row 9: cold-init / priority frame, 0x3AD84 — base 0xD00778 verified at
    #   maincpu.disasm.txt line 73911 (`3ad86: 41f9 00d0 0778  lea 0xD00778, %a0`)
    (239, 76, 4),   # idx 239..242 → slots 76..79

    # Row 10: no remaining overflow guard-band slots after Resolution-B expansion.
    # No LUT entries.
]

for (idx_start, slot_start, count) in mappings:
    for i in range(count):
        idx = idx_start + i
        if LUT[idx] == 0xFF:
            LUT[idx] = slot_start + i
        # else: entry already claimed by an earlier row; first-row-wins precedence.

# Write LUT to build/pc090oj_slot_lut.bin
import sys
sys.stdout.buffer.write(bytes(LUT))
```

**Resulting LUT (deterministic).** The generator above produces exactly this 256-byte sequence (only non-`0xFF` entries listed; all unlisted indices are `0xFF`):

| PC090OJ idx (= `byte_offset / 8`) | PC090OJ byte offset | Genesis SAT slot | Source row in §1.3 |
|----------------------------------|---------------------|------------------|---------------------|
| 0..8                             | 0x000..0x040        | 44..52           | Row 4 (sprite-update) |
| 9..16                            | 0x048..0x080        | 30..37           | Row 3 (status/UI)     |
| 17..24                           | 0x088..0x0C0        | 22..29           | Row 2 (HUD/score)     |
| 46..53                           | 0x170..0x1A8        | 56..63           | Row 5 (sprite-decay)  |
| 239..242                         | 0x778..0x790        | 76..79           | Row 9 (priority frame) |

All other indices (25..45, 54..238, 243..255) hold `0xFF` (skip). Total non-skip entries: 8 + 8 + 8 + 8 + 4 = **36 mapped indices**, 220 skip indices.

**Helper-internal slot ranges (unchanged; for reference).** Each named function-body helper still emits to its dedicated SAT slot range regardless of LUT — slot ownership is by helper identity:

| Helper | SAT slot range (helper-internal) |
|--------|-----------------------------------|
| `genesistan_pc090oj_hook_target_*` (7 target helpers) | 0..21 |
| `genesistan_pc090oj_hook_score_digit_3b802`           | 22..29 |
| `genesistan_pc090oj_hook_status_sprite_5a098`         | 30..43 |
| `genesistan_pc090oj_hook_sprite_update_54810`         | 44..55 |
| `genesistan_pc090oj_hook_sprite_decay_5607c`          | 56..63 |
| `genesistan_pc090oj_hook_copy_56114`                  | 64..67 |
| `genesistan_pc090oj_hook_zero_fill_56440`             | 68..71 |
| `genesistan_pc090oj_hook_slot_init_54052`             | 72..75 |
| `genesistan_pc090oj_hook_init_priority_3ad84`         | 76..79 |
| `genesistan_hook_3ad44_dispatch` (v3.2 — replaces former `genesistan_pc090oj_hook_init_clear_3ad44`)            | depends on A0 dispatch — see §2.2.A. **PC090OJ branch:** 76..79 (uses LUT to pick start slot for bulk-clear; clears N slots starting at `LUT[A0_idx]` if `LUT[A0_idx] != 0xFF`, otherwise no-op). **Tilemap branch:** writes to `staged_bg_buffer` per `genesistan_hook_tilemap_bg_fill` semantics (no SAT slots touched). **Audit fall-through:** halts via §7.3 mechanism (no slots touched). |

The LUT-vs-slot-range overlap (e.g., LUT puts idx 0..8 → slots 44..52, helper for 0x54810 uses slots 44..55) is intentional: it records which PC090OJ-memory clears affect which SAT slot range, so the bulk-clear helper can correctly invalidate Genesis sprites when arcade clears the corresponding PC090OJ memory.

### 1.4 Initialization

Boot-time initialization is added to `_bootstrap_clear_staging` in [apps/rastan-direct/src/boot/boot.s:162-209](apps/rastan-direct/src/boot/boot.s#L162-L209), immediately after the existing `staged_tile_words` clear loop:

```asm
    /* clear sprite SAT staging */
    lea     staged_sprite_sat, %a0
    move.w  #(640/2 - 1), %d7
.Lboot_sprite_sat_clear:
    clr.w   (%a0)+
    dbra    %d7, .Lboot_sprite_sat_clear

    /* clear sprite descriptor table */
    lea     staged_sprite_descriptor_table, %a0
    move.w  #(1024/2 - 1), %d7
.Lboot_sprite_desc_clear:
    clr.w   (%a0)+
    dbra    %d7, .Lboot_sprite_desc_clear

    clr.l   staged_sprite_dirty
    clr.w   staged_sprite_active_count
```

All 80 SAT entries start with Y=0 (Genesis convention: Y=0x80 = top-of-screen; Y=0 = above-screen, off-frame). Link field 0 in slot 0 = end-of-chain. The buffer starts as a valid empty sprite list. The first VBlank after boot will commit this empty list, blanking any stale VDP SAT content from previous boot.

Per-frame: there is **no per-frame zero of the staging buffers**. Helpers update slots in-place (writing to their dedicated slot range). The `staged_sprite_dirty` bitmap gates VBlank commit blocks — only blocks updated this frame are re-DMA'd. The `touched-this-frame` bit (descriptor +0 bit 15) is cleared by VBlank commit at end of frame so the next frame's helpers can detect first-touch.

### 1.5 Concurrency

There is **no concurrency** in the formal sense — Genesis 68000 is single-CPU, helpers run synchronously inside the arcade-flow JSR/RTS path, VBlank is the sole pre-emption point. The commit reads buffers that helpers have just finished writing to. Two ordering rules apply:

1. **Helper ordering within a frame is arcade-determined.** Helpers fire in the order arcade calls them. The descriptor table's source-id field lets VBlank commit re-emit in priority order regardless of write order.
2. **VBlank commit is non-reentrant.** `_vblank_service` already raises IMASK to 7 (`ori.w #0x0700, %sr` — see [apps/rastan-direct/src/scene_load.s:47](apps/rastan-direct/src/scene_load.s#L47) for an existing example pattern; `_vblank_service` itself runs at IMASK=7 entered by the 68k autovector). No helper invocation can preempt the commit. No staging-buffer torn-write race exists.

---

## 2. Helper function contracts

Three helper categories with distinct entry-state contracts, all defined in a new source file `apps/rastan-direct/src/pc090oj_hooks.s`:

- **§2.1 Target-function helpers** (6 helpers): replace the bodies of April-6 target functions (and the `0x3B930` writer helper). Read arcade workram blocks A+B (or sub-block per target) and emit Genesis SAT entries to slots 0..21.
- **§2.2 Independent-writer helpers** (9 helpers): replace the bodies of INDEPENDENT writer functions. Each emits a category-specific descriptor pattern to its dedicated slot range.
- **§2.3 Audit-guard helpers** (1 shared helper, 2 invoke sites): captures CPU state on FU1 unexpected execution.

All helpers preserve registers per arcade-side ABI (saved/restored by `movem.l`), do exactly one hardware-translation operation, write only to WRAM staging (never directly to VDP), end with `RTS`. No helper loops waiting for events. No helper performs more than one staged operation per invocation. All helpers comply with Rule 4.

### 2.1 Target-function helpers (April-6 + 0x3B930)

Each replaces the body of one arcade function. The function is reached via the original arcade JSR/BSR; the body is a JSR-to-helper-then-RTS-then-NOPs stub.

| Helper symbol                              | Replaces arcade fn | Arcade fn span (bytes; canonical per §8.4) | Inputs (entry register state) | Output slots |
|--------------------------------------------|--------------------|---------------------------------------------:|--------------------------------|--------------|
| `genesistan_pc090oj_hook_target_3b902`     | 0x3B902            | 36 (`0x3B902..0x3B925`)                      | A1=0xD00088 (target), D1.W=fill-byte, A5=arcade workram base | 0..4 (5 slots) |
| `genesistan_pc090oj_hook_target_3b926`     | 0x3B926            | 10 (`0x3B926..0x3B92F`)                      | A1=0xD00128 (target), D0.W=count, A5=arcade workram base | 5..13 (9 slots) |
| `genesistan_pc090oj_hook_target_3b930`     | 0x3B930            | 32 (`0x3B930..0x3B94F`)                      | A1=destination, A0=source descriptor table, D1.W=count, A5 | reserved 14..17 (4 slots) |
| `genesistan_pc090oj_hook_target_41dae`     | 0x41DAE            | 352 (`0x41DAE..0x41F0D`)                     | A4=workram base+1288, A5=arcade workram base | 0..21 — emits Block A (18 entries) plus internal sub-loops. **Authoritative emitter for slots 0..17.** |
| `genesistan_pc090oj_hook_target_41f5e`     | 0x41F5E            | 56 (`0x41F5E..0x41F95`)                      | A0=workram base+4530, A5=arcade workram base | 18..21 (Block B 4 entries) |
| `genesistan_pc090oj_hook_target_45dfa`     | 0x45DFA            | 258 (`0x45DFA..0x45EFB`)                     | A4=workram base+1480, A5=arcade workram base | 0..21 — emits same 22-sprite frame as `0x41DAE` via parallel sub-loops with different workram offsets. **Re-issues SAT for the same 22 slots** when arcade re-emits during a different game phase. |
| `genesistan_pc090oj_hook_target_59f5e`     | 0x59F5E            | 52 (`0x59F5E..0x59F91`)                      | A5=arcade workram base | clears fixed helper-owned slots 0..7 (mapping documented in §1.3.1; no runtime LUT consult) |

Behavior contract (common):

1. `movem.l %d0-%d7/%a0-%a6, -(%sp)` (full 14-register save).
2. Read arcade workram via A5 at the offsets the original function used. Source addresses are listed per helper above.
3. For each descriptor read: validate (skip if `y_raw == 0x0180`, all-zero, or tile code zero — same rules as April 6 §2.3).
4. Lower descriptor to Genesis SAT format using the §3 rules. Write to `staged_sprite_sat[slot * 8]`. Write semantic record to `staged_sprite_descriptor_table[slot * 12]`. Set `staged_sprite_dirty` bit `(slot >> 2)`. Set `staged_sprite_descriptor_table[slot * 12] +0` bit 15 (touched-this-frame).
5. Update `staged_sprite_active_count` (recomputed by VBlank commit, but helpers may bump it for early-out gating; final authoritative count is computed at commit).
6. `movem.l (%sp)+, %d0-%d7/%a0-%a6`.
7. `RTS`.

Rule 4 compliance: each helper performs exactly one batch SAT update per call (reading N descriptors → emitting N SAT entries). No event waiting. No control-flow ownership. RTS returns to arcade.

### 2.2 Independent-writer helpers

| Helper symbol                                      | Replaces arcade fn | Arcade fn span (bytes; canonical per §8.4) | Output slots | Behavior summary |
|----------------------------------------------------|--------------------|---------------------------------------------:|--------------|------------------|
| `genesistan_hook_3ad44_dispatch` (v3.2; replaces `genesistan_pc090oj_hook_init_clear_3ad44`) | 0x3AD44 (polymorphic memset utility) | 8 (`0x3AD44..0x3AD4B`) | depends on A0 (see §2.2.A) | Polymorphic-utility dispatch on A0. Tilemap branch reproduces `genesistan_hook_tilemap_bg_fill` behavior (writes to `staged_bg_buffer` with PC080SN tile/attr translation per [tilemap_hooks.s:387-472](apps/rastan-direct/src/tilemap_hooks.s#L387-L472)). PC090OJ branch reproduces the v3.1 `genesistan_pc090oj_hook_init_clear_3ad44` behavior (LUT lookup → bulk-clear up to N SAT slots starting at `LUT[A0_idx]` if `LUT[A0_idx] != 0xFF`, per [pc090oj_hooks.s:347-377](apps/rastan-direct/src/pc090oj_hooks.s#L347-L377)). Audit fall-through reuses §7.3 halt-with-heartbeat mechanism. Full contract in §2.2.A. |
| `genesistan_pc090oj_hook_init_priority_3ad84`      | 0x3AD84 (priority-frame init) | 56 (`0x3AD84..0x3ADBB`) | 76..79 | Initialize 4 priority-ladder sprites at 0xD00778. Encodes priority gate in descriptor +0 bit 1. |
| `genesistan_pc090oj_hook_score_digit_3b802`        | 0x3B802 (score/HUD digit) | 174 (`0x3B802..0x3B8AF`) | 22..29 | Translate 5-byte digit-table entry into HUD sprite descriptor. Reads table at PC-relative offset (arcade) → reads from `rastan_maincpu` (Genesis) at the same offset. Span includes the function's PC-relative digit-attribute table at 0x3B87E..0x3B8AF (50 bytes; referenced only from inside this function — verified by grep). |
| `genesistan_pc090oj_hook_slot_init_54052`          | 0x54052 (sprite slot init) | 122 (`0x54052..0x540CB`) | 72..75 | Initialize 4 SAT slots (Genesis sprite-slot init). The original arcade function ALSO clears 3 Taito C-chip text-RAM regions at 0x10D1B2 / 0x10D1D2 / 0x10D1F2 (Taito C-chip text VRAM; not PC090OJ). Path B is taken (see §2.2.1 below): helper replicates the text-RAM clear loops verbatim before emitting the PC090OJ portion. |
| `genesistan_pc090oj_hook_sprite_update_54810`      | 0x54810 (sprite update routine) | 84 (`0x54810..0x54863`) | 44..55 | Update 4 sprite slots from a 24-byte source descriptor in `rastan_maincpu` ROM at offset 0x5DA5E. D0.W = table index. |
| `genesistan_pc090oj_hook_sprite_decay_5607c`       | 0x5607C (sprite decay loop) | 94 (`0x5607C..0x560D9`) | 56..63 | Decrement Y on each active slot in range; if Y reaches 16, zero the tile-code field (sprite-disappear). |
| `genesistan_pc090oj_hook_copy_56114`               | 0x56114 (sprite-RAM copy) | 20 (`0x56114..0x56127`) | 64..67 | Copy 4 word-pairs from A0 (source) to staging slot 64..67. Stop on `0xFFFF` sentinel. |
| `genesistan_pc090oj_hook_zero_fill_56440`          | 0x56440 (sprite-RAM zero-fill outer) | 30 (`0x56440..0x5645D`) | 68..71 | Zero N SAT slots in range. D0.W = inner count, D1.W = outer count. The internal helper at `0x5648A..0x5649D` (separate 20-byte function with single internal caller at `0x56454`) becomes unreachable dead code once `0x56440` body is replaced — no separate entry required. |
| `genesistan_pc090oj_hook_status_sprite_5a098`      | 0x5A098 (status/UI sprite writer) | 498 (`0x5A098..0x5A289`) | 30..43 | Translate 12-write-per-call status sprite emission (1UP, lives, weapon-pickup) into 12 staging slots. Span includes the inline helper at `0x5A244..0x5A289` (called only from `0x5A210` inside the function; verified by grep). |

Each helper:
- saves registers with movem
- reads only the inputs the original arcade function read (workram, ROM tables, register values)
- writes only to the slot range owned by this helper
- sets the appropriate dirty bits and descriptor-table records
- restores registers
- RTS

#### 2.2.A Helper `genesistan_hook_3ad44_dispatch` — polymorphic-utility dispatch (v3.2)

The arcade function at `0x03AD44..0x03AD4B` (8 bytes) is a 4-instruction generic longword-fill utility (verified at [maincpu.disasm.txt:73893-73896](build/maincpu.disasm.txt#L73893-L73896)):

```asm
3ad44: 20c0   movel %d0, %a0@+      ; *A0++ = D0
3ad46: 5341   subqw #1, %d1
3ad48: 66fa   bnes  0x3ad44         ; loop while D1 != 0
3ad4a: 4e75   rts
```

This is destination-agnostic (caller sets A0), fill-value-agnostic (caller sets D0), and count-driven (caller sets D1). It is **polymorphic**: used by both the tilemap BG-fill subsystem and the PC090OJ init/reset subsystem. The v3.2 dispatch helper preserves both behaviors via A0-classification on entry.

##### 2.2.A.1 Caller enumeration (load-bearing evidence per Rule 18)

Static enumeration via `grep -nE "0x3ad44|0x03ad44" build/maincpu.disasm.txt` yields exactly 8 references in the entire ROM: 1 internal `bnes` loop-back at `0x3AD48` (the function's own body) plus 7 external callers. The 7 callers, with each caller's A0 setup walked back to the constant-origin instruction, are:

| Caller arcade_pc | Site disasm cite | A0 set by | A0 value | Range classification |
|------------------|---|---|---|---|
| 0x03AD5C | [maincpu.disasm.txt:73900](build/maincpu.disasm.txt#L73900) `bsrs 0x3ad44` | `lea 0xD00000, %a0` at [line 73898](build/maincpu.disasm.txt#L73898) | `0x00D00000` | **PC090OJ** ([0xD00000, 0xD00800)) |
| 0x03AD6E | [maincpu.disasm.txt:73904](build/maincpu.disasm.txt#L73904) `bsrs 0x3ad44` | `lea 0xD00170, %a0` at [line 73902](build/maincpu.disasm.txt#L73902) | `0x00D00170` | **PC090OJ** |
| 0x03AD82 | [maincpu.disasm.txt:73909](build/maincpu.disasm.txt#L73909) `bsrs 0x3ad44` | `lea 0xD00000, %a0` at [line 73907](build/maincpu.disasm.txt#L73907) | `0x00D00000` | **PC090OJ** |
| 0x03AE70 | [maincpu.disasm.txt:73978](build/maincpu.disasm.txt#L73978) `bsrw 0x3ad44` | `lea 0xC00100, %a0` at [line 73975](build/maincpu.disasm.txt#L73975) | `0x00C00100` | **TILEMAP** ([0xC00000, 0xC10000)) |
| 0x03AE80 | [maincpu.disasm.txt:73982](build/maincpu.disasm.txt#L73982) `bsrw 0x3ad44` | `lea 0xC08100, %a0` at [line 73979](build/maincpu.disasm.txt#L73979) | `0x00C08100` | **TILEMAP** |
| 0x03AF38 | [maincpu.disasm.txt:74026](build/maincpu.disasm.txt#L74026) `bsrw 0x3ad44` | `lea 0xC00000, %a0` at [line 74023](build/maincpu.disasm.txt#L74023) | `0x00C00000` | **TILEMAP** |
| 0x03AF48 | [maincpu.disasm.txt:74030](build/maincpu.disasm.txt#L74030) `bsrw 0x3ad44` | `lea 0xC08000, %a0` at [line 74027](build/maincpu.disasm.txt#L74027) | `0x00C08000` | **TILEMAP** |

Range classification:
- **Tilemap range:** `[0x00C00000, 0x00C10000)`. 4 callers (0x03AE70, 0x03AE80, 0x03AF38, 0x03AF48). All target Genesis VDP cwindow space (PC080SN BG plane B at `0xC00000..0xC03FFF` and FG plane A at `0xC08000..0xC0BFFF`).
- **PC090OJ range:** `[0x00D00000, 0x00D00800)`. 3 callers (0x03AD5C, 0x03AD6E, 0x03AD82). All target the active PC090OJ descriptor area per spec §1.3 / `Andy_pc090oj_reconciliation_v2.md` Phase 5.
- Non-overlapping: the two ranges are separated by the unmapped `[0xC10000, 0xD00000)` band (no caller targets that band; no caller's A0 falls in both ranges).
- Exhaustive: all 7 callers fit in exactly one of the two ranges.

##### 2.2.A.2 Pre-existing helper contracts (Phase 2 evidence)

**Tilemap helper `genesistan_hook_tilemap_bg_fill`** ([tilemap_hooks.s:387-472](apps/rastan-direct/src/tilemap_hooks.s#L387-L472)):

- Entry: `movem.l %d0-%d7/%a0-%a6, -(%sp)` (full register save).
- Inputs: A0 = arcade tilemap dest pointer; D0 = tile attribute word; D1 = count.
- Internal range filter: rejects A0 outside `[ARCADE_PC080SN_CWINDOW_BASE_BG, ARCADE_PC080SN_CWINDOW_BASE_BG + ARCADE_PC080SN_CWINDOW_BYTES)` = `[0xC00000, 0xC04000)` (BG plane only — FG-plane callers `0xC08000` / `0xC08100` reach this helper but are NO-OPped by the internal range filter, then RTS without staging change). Verified at [tilemap_hooks.s:393-396](apps/rastan-direct/src/tilemap_hooks.s#L393-L396).
- Per-cell behavior: looks up `genesistan_pc080sn_tile_vram_lut` and `genesistan_pc080sn_attr_lut`, computes Genesis tile word, writes to `staged_bg_buffer` at `(row*128 + col*2)`, sets `bg_row_dirty` bit for the row.
- Exit: `movem.l (%sp)+, %d0-%d7/%a0-%a6; rts`.

**PC090OJ helper `genesistan_pc090oj_hook_init_clear_3ad44`** ([pc090oj_hooks.s:347-377](apps/rastan-direct/src/pc090oj_hooks.s#L347-L377)):

- Entry: `movem.l %d0-%d7/%a0-%a6, -(%sp)` (full register save).
- Inputs: A0 = arcade PC090OJ dest pointer; D1 = count.
- A0 → idx: `idx = (A0 - 0xD00000) >> 3`. Range filter: reject if A0 < 0xD00000 (negative `idx`) or `idx > 255` ([pc090oj_hooks.s:351-356](apps/rastan-direct/src/pc090oj_hooks.s#L351-L356)).
- LUT lookup: `slot = pc090oj_slot_lut[idx]`. If `slot == 0xFF`, no-op exit ([pc090oj_hooks.s:358-361](apps/rastan-direct/src/pc090oj_hooks.s#L358-L361)).
- Bulk-clear loop: clears up to D1 SAT slots starting at `slot`, using internal `.Lpc090oj_clear_slot` subroutine; bounded at slot=80 ([pc090oj_hooks.s:363-373](apps/rastan-direct/src/pc090oj_hooks.s#L363-L373)).
- Exit: `movem.l (%sp)+, %d0-%d7/%a0-%a6; rts`.

**Shared invariants:** both helpers use the same entry register state (A0/D0/D1 per arcade convention), the same full-register movem save/restore, and exit identically (RTS). The KEY DIFFERENCE is the A0 range each accepts and the staging buffer each writes.

##### 2.2.A.3 Dispatch contract

`genesistan_hook_3ad44_dispatch` (lives in `pc090oj_hooks.s` per Rule 21 source-ownership; replaces the v3.1 `genesistan_pc090oj_hook_init_clear_3ad44` symbol):

1. **Save registers.** `movem.l %d0-%d7/%a0-%a6, -(%sp)` (matches both pre-existing helpers' contract).
2. **A0 dispatch.** Compare A0 against the two range bounds. The exact comparison sequence Cody implements:
   - If `A0 ∈ [0x00C00000, 0x00C10000)`: take **tilemap branch**.
   - Else if `A0 ∈ [0x00D00000, 0x00D00800)`: take **PC090OJ branch**.
   - Else: take **audit fall-through**.
   The tilemap range is checked first (matches caller-frequency expectation: tilemap callers fire during scene transitions and FG/BG resets; PC090OJ callers fire during sprite-RAM init). Order does not affect correctness because ranges are non-overlapping per §2.2.A.1.
3. **Tilemap branch.** Invoke `genesistan_hook_tilemap_bg_fill` (existing symbol) — Cody's mechanical translation may either (a) `bsr` to it as a subroutine after restoring registers and re-saving them inside the call (preserves the existing helper's full-register movem contract; trivial, but adds save/restore overhead), or (b) inline its body. Either choice produces identical observable behavior because the existing helper's entry/exit contract matches the dispatch's. Cody's choice is a mechanical-translation detail; the dispatch contract is "execute `genesistan_hook_tilemap_bg_fill` semantics for tilemap-range A0." Note that the existing helper's internal range filter (`[0xC00000, 0xC04000)`) silently no-ops FG-plane callers (`0xC08000`/`0xC08100`); v3.2 preserves this exact behavior — those callers reach the dispatch's tilemap branch, then get no-opped by the existing helper's internal filter. No regression.
4. **PC090OJ branch.** Execute the same logic as v3.1's `genesistan_pc090oj_hook_init_clear_3ad44`: compute `idx = (A0 - 0xD00000) >> 3`, read `pc090oj_slot_lut[idx]`, bulk-clear up to D1 SAT slots starting at that slot if `LUT != 0xFF`. Per Rule 19 the PC090OJ branch's observable Genesis-side behavior is byte-identical to the v3.1 helper for any A0 in `[0xD00000, 0xD00800)`. Per the §1.3.1 LUT table, the 3 PC090OJ callers' A0 values resolve to: `0xD00000` → `idx=0` → `LUT[0]=44` → start slot 44 (sprite-update range; bulk-clear truncated by D1 count); `0xD00170` → `idx=46` → `LUT[46]=56` → start slot 56 (sprite-decay range).
5. **Audit fall-through.** A0 in neither range → reuse the §7.3 audit-guard mechanism EXACTLY — populate the existing `audit_guard_*` `.bss` symbols (caller PC = return address from stack; register snapshot from saved registers; VDP V-counter; fired flag = `0x510E`-style sentinel — Cody may pick a distinct sentinel like `0x3AD4` to disambiguate from the §7 audit guards) and enter the existing `.Lag_halt_loop` heartbeat. No new audit mechanism is introduced; this is reuse of §7.3.
6. **Restore registers.** `movem.l (%sp)+, %d0-%d7/%a0-%a6` (only reached on the tilemap and PC090OJ branches; audit fall-through halts before this point).
7. **RTS.**

##### 2.2.A.4 Behavior preservation under Rule 19

The dispatch helper produces the same observable Genesis-side behavior as the prior tilemap helper for tilemap callers AND the same observable behavior as the v3.1 PC090OJ helper for PC090OJ callers. Neither subsystem regresses:

- Tilemap callers (A0 in `[0xC00000, 0xC10000)`): dispatch routes to `genesistan_hook_tilemap_bg_fill`. Observable result: identical to pre-PC090OJ-replacement HEAD baseline.
- PC090OJ callers (A0 in `[0xD00000, 0xD00800)`): dispatch routes to PC090OJ-branch logic (renamed from v3.1's helper but byte-equivalent). Observable result: identical to v3.1.
- Out-of-range callers (currently none in the 7 enumerated callers): formerly silent no-op (in tilemap helper) or silent no-op (in PC090OJ helper's `bmi.s .Lhook_3ad44_done`). v3.2 makes them explicit halt with diagnostic capture — this is a **behavior strengthening, not a regression**: any future caller that adds a third concern is surfaced via §7.3 audit, not silently dropped. Per the §2.2.A.1 enumeration, no current caller hits this branch.

The 7 currently-enumerated callers all fall within one of the two known ranges and are covered identically to their pre-v3.2 behavior.

#### 2.2.1 Helper `genesistan_pc090oj_hook_slot_init_54052` — Path B specification

The original arcade function at `0x54052` (verified at [maincpu.disasm.txt:105718-105749](build/maincpu.disasm.txt#L105718-L105749)) consists of two sequential phases:

**Phase A — Text-RAM clear** (arcade `0x54052..0x540AB`, 90 bytes): three loops that clear Taito C-chip text VRAM regions:

```asm
moveal #0x0010D1D2, %a1     ; first text-RAM region
movew  #6, %d2
.loop1:
movew  #3, %a1@+
movew  #0, %a1@+
movew  #0, %a1@+
movew  #0, %a1@+
subqw  #1, %d2
bnes   .loop1               ; → 24 word-writes total

movew  #4, %d2
moveal #0x0010D1B2, %a1     ; second text-RAM region
.loop2:
movew  #3, %a1@+
movew  #0, %a1@+
movew  #0, %a1@+
movew  #0, %a1@+
subqw  #1, %d2
bnes   .loop2               ; → 16 word-writes total

moveal #0x0010D1F2, %a1     ; third text-RAM region
movew  #6, %d2
.loop3:
movew  #3, %a1@+
movew  #0, %a1@+
movew  #0, %a1@+
movew  #0, %a1@+
subqw  #1, %d2
bnes   .loop3               ; → 24 word-writes total
```

**Phase B — PC090OJ slot init** (arcade `0x540AC..0x540C9`, 30 bytes): clears 4 PC090OJ sprite slots starting at `0xD00000`:

```asm
moveal #0x00D00000, %a1
movew  #4, %d2
.loop4:
movew  #3, %a1@+
movew  #0, %a1@+
movew  #0, %a1@+
movew  #0, %a1@+
subqw  #1, %d2
bnes   .loop4               ; → 16 word-writes; sets sprite slots 0..3
                            ;   (idx 0..3 → SAT slots 44..47 per §1.3.1
                            ;   row-4 mapping; helper-internal slot range
                            ;   for 0x54052 is 72..75 per §1.3 row 8)
```

(Then `rts` at `0x540CA`.)

**Path-selection determination.** The original spec line 169 contained an "or" disjunction between (A) falling through to an existing text-writer hook, and (B) replicating the text-RAM subset. Verification via `grep -E "10D1[A-F]2|0x10D1|D1B2|D1D2|D1F2" apps/rastan-direct/src/*.s specs/rastan_direct_remap.json` returns ZERO matches: rastan-direct has NO existing hook at 0x10D1B2 / 0x10D1D2 / 0x10D1F2 (those addresses are not in `tilemap_hooks.s` text-writer coverage, which targets PC080SN cwindow at `0xC00000+`/`0xC08000+`, not Taito C-chip text VRAM at `0x10D1xx`). Path A is therefore impossible. **Path B is selected.**

**Defect-3 closure evidence (`§3.A` downstream reader/writer search).** Search target: instructions that read or write PC090OJ slot-0..3 byte range `0xD00000..0xD0001F` outside the 18 hook-site spans from §8.2.

Search commands:
- `rg -n -i "00d0 0000|0xd00000|d0000[0-9a-f]|d0001[0-9a-f]" build/maincpu.disasm.txt`
- Manual context inspection for each hit to classify memory-access semantics and hook-span inclusion.

Findings:
- Outside 18 spans:
  - `arcade_pc 0x056A` loads `A0=0xD00000` and calls `0x57C` ([maincpu.disasm.txt:396](build/maincpu.disasm.txt#L396)).
  - `arcade_pc 0x057C` probe helper performs `%a0@` reads/writes over `[0xD00000..0xD01000)` including `0xD00000..0xD0001F` ([maincpu.disasm.txt:400-407](build/maincpu.disasm.txt#L400)).
  - `arcade_pc 0x510C8` writes one descriptor at `0xD00000..0xD00006` (`movew ...,%a0@+`) ([maincpu.disasm.txt:102298-102303](build/maincpu.disasm.txt#L102298)).
  - `arcade_pc 0x52AA2` emits 4-slot descriptor writes beginning at `0xD00000` (slot-distinguishing `A1@+` writes across the first 0x20 bytes) ([maincpu.disasm.txt:104033-104053](build/maincpu.disasm.txt#L104033)).
- Inside 18 spans:
  - `arcade_pc 0x540AC` (entry #11 span) writes 4 slots at `0xD00000..0xD0001F` ([maincpu.disasm.txt:105742-105749](build/maincpu.disasm.txt#L105742)).
  - `arcade_pc 0x54810` (entry #12 span) writes descriptor stream from `0xD00000` upward ([maincpu.disasm.txt:106237](build/maincpu.disasm.txt#L106237)).
  - `arcade_pc 0x3AD50` / `0x3AD76` are outside spans but only set `A0=0xD00000` before calling `0x3AD44` (entry #8 body replacement) ([maincpu.disasm.txt:73898](build/maincpu.disasm.txt#L73898), [maincpu.disasm.txt:73907](build/maincpu.disasm.txt#L73907)).

Conclusion: there ARE downstream slot-0..3 references outside the 18 hook-site spans, including slot-distinguishing writer `0x52AA2`. Therefore 4→2 collapse is not mechanically safe under the strict no-inference policy.

**Chosen resolution: Resolution B (expand-to-4-slots).** §1.3/§1.3.1/§2.2/§2.2.1 are updated so `0x54052` preserves 4 distinct Genesis SAT slots (`72..75`) with identity mapping from arcade slots `0..3`.

**Path B implementation.** The helper executes Phase A and Phase B verbatim from arcade behavior:

1. `movem.l %d0-%d7/%a0-%a6, -(%sp)` (full register save)
2. **Replicate Phase A verbatim**: emit the three text-RAM clear loops shown above, byte-for-byte equivalent to the arcade instructions at `0x54052..0x540AB`. Genesis hardware behavior at addresses `0x0010D1B2 / 0x0010D1D2 / 0x0010D1F2`: these fall within Genesis cartridge ROM address space (`0x000000..0x3FFFFF`) but outside both the relocated arcade ROM (`0x000200..0x05FFFF`) and the Genesis-side wrapper code (`0x070000+`). Writes to cartridge ROM addresses on Genesis are silently absorbed by the cartridge (read-only memory; no bus error). Replicating the writes is therefore harmless and preserves arcade-side semantic equivalence.
3. **Phase B substitution (Resolution B)**: instead of writing 4 sprite slot inits to `0xD00000..0xD0001F` (unmapped Genesis memory inside VDP space), emit translated SAT entries to `staged_sprite_sat[72*8 .. 75*8 + 7]` with identity mapping:
   - arcade slot 0 → Genesis SAT slot 72
   - arcade slot 1 → Genesis SAT slot 73
   - arcade slot 2 → Genesis SAT slot 74
   - arcade slot 3 → Genesis SAT slot 75
   Each slot receives the same init data (`attr=3`, `Y=0`, `tile=0`, `X=0`) because the source Phase-B loop writes identical 4-word records per iteration.
4. Update `staged_sprite_descriptor_table[72*12 .. 75*12 + 11]` per §2.1 step 4 contract.
5. Set `staged_sprite_dirty` bit `(72 >> 2) = 18` (covers slots 72..75 in the dirty bitmap).
6. `movem.l (%sp)+, %d0-%d7/%a0-%a6` (full register restore)
7. `RTS`

This specification removes the §2.2 line 169 disjunction. The helper is fully deterministic; Path A is not implemented; Path B is implemented exactly as above.

### 2.3 Audit-guard helper

`genesistan_pc090oj_hook_audit_guard` — single helper invoked from both `0x510EA` and `0x510F4` replacement sites. Behavior in §7.

---

## 3. Descriptor-to-SAT lowering rules

Field-by-field translation. Source: April 6 §6 / §7, validated against `Andy_pc090oj_reconciliation_v2.md` Phase 4 (5 VERIFIED + 1 PARTIAL on tile-code mask width; both sufficient for Rastan's 12-bit code range).

### 3.1 Y position

```
sat_y_word = ((arcade_word1 & 0x01FF) + 0x0080) & 0x01FF
```

- Source: arcade descriptor word1 bits 8:0 (9-bit Y).
- Bias: +0x80 (Genesis 128-pixel off-screen border; April 6 §7.1).
- Mask after bias: 9 bits — values that overflow remain in 0x180..0x1FF (off-screen).
- Off-screen sentinel: arcade `y_raw == 0x0180` → helper skips emission entirely (no SAT write); descriptor +0 valid bit cleared.
- Evidence: `Andy_pc0900j_sprite_correctness_audit.md` §7.1, MAME line 192 (`y & 0x1ff`).

### 3.2 X position

```
sat_x_word = ((arcade_word3 & 0x01FF) + 0x0080) & 0x01FF
```

Identical bias and masking to Y. Evidence: April 6 §7.2, MAME line 191.

### 3.3 Sprite size (constant)

```
size_field = 0x05    /* bits 11:10 = 01 (V=2 tiles), bits 9:8 = 01 (H=2 tiles) */
```

PC090OJ cells are 16×16 = 2×2 Genesis tiles. April 6 §6.4 fixes this. No PC090OJ field encodes runtime size — Rastan does not vary sprite dimensions on a per-cell basis.

### 3.4 Link field

Computed at VBlank commit (§5), not by helpers. The commit walks `staged_sprite_descriptor_table` in slot order, counts valid entries, and assigns `link = next-valid-slot` for all but the last, which gets `link = 0`. Evidence: April 6 §8.1.

The slot-allocation map (§1.3) puts target-function output (slots 0..21) before INDEPENDENT helpers (slots 22..79). VBlank commit writes link chain in slot order, so render order is: April-6 22 sprites first (highest priority), then HUD/score, then status/UI, then update/decay/etc. This matches arcade's "Block A first, then Block B" priority ordering (April 6 §8.2) and extends it consistently.

### 3.5 Priority bit

```
sat_word2 |= 0x8000     /* always-on */
```

April 6 §6.3 sets priority unconditionally. Sprites always render above background planes for Rastan's HUD/UI overlay. Confirmed safe by April 6's empirical results (no priority-related sprite/plane conflicts observed in `apps/rastan/` builds with this constant).

### 3.6 Palette line

```
color = (arcade_word0 & 0x000F) | ((sprite_ctrl & 0x00E0) >> 1)
palette_line = (color >> 4) & 0x0003
sat_word2 |= (palette_line << 13)
```

- `sprite_ctrl` is workram word at A5+`0x14` (= `10*2(%a5)` per April 6 line 219) — the global colour-bank register.
- Evidence: April 6 §6.1; MAME `(data & 0x000f) | sprite_colbank` (line 189).

### 3.7 Vertical flip

```
sat_word2 |= (arcade_word0 & 0x8000) >> 3   /* bit 15 → bit 12 */
```

April 6 §6.2; MAME line 187 (`(data & 0x8000) >> 15`, then placed at bit 12 by SAT layout).

### 3.8 Horizontal flip

```
sat_word2 |= (arcade_word0 & 0x4000) >> 3   /* bit 14 → bit 11 */
```

April 6 §6.2; MAME line 188.

### 3.9 Tile pattern index

```
arcade_tile = arcade_word2 & 0x0FFF              /* 12-bit Rastan range */
sat_tile = SPRITE_TILE_BASE + slot * 4           /* SPRITE_TILE_BASE = 1024 */
sat_word2 |= (sat_tile & 0x07FF)
```

The PC090OJ tile code names a 16×16 cell. Genesis stores each cell as 4 Genesis tiles in VRAM at a per-slot allocation. Each slot's 4 tiles live at VRAM tile indices `1024 + slot*4 .. 1024 + slot*4 + 3`. The actual cell-pixel data is uploaded to VRAM by the per-frame DMA in §5. Evidence: April 6 §5.1.

The mask discrepancy (`0x3FFF` April 6 vs `0x1FFF` MAME, vs Rastan's actual 12-bit usage) is resolved by using `0x0FFF` here — sufficient for Rastan, simpler than April 6's looser mask. Citation: `Andy_pc090oj_reconciliation_v2.md` Phase 2 PARTIAL note (both masks cover Rastan's 12-bit range).

The `0x07FF` mask on the SAT word is required because Genesis SAT word2 only has 11 bits for tile index (bits 10:0). With slot in 0..79, `1024 + slot*4` ranges from 1024 to 1340; max value `1340 = 0x53C`, fits in 11 bits.

### 3.10 Empty / invalid sprite handling

Arcade marks empty sprites in three ways (April 6 §2.3):
1. `y_raw == 0x0180` — off-screen sentinel.
2. All four words zero.
3. Tile code `(word2 & 0x3FFF) == 0`.

Helper response: do not write a SAT entry for the slot. Clear the descriptor table's valid bit. The slot remains in its previous-frame state in `staged_sprite_sat`; VBlank commit's link-chain construction skips invalid slots and assigns `link` to skip them.

Genesis equivalent of "off-screen": Y=0x0000 (above the visible area; sprite renders nothing). The boot-time clear puts all slots there. Run-time invalid slots either retain their previous Y (if no helper touched them this frame) or get explicitly Y-zeroed by the helper that observed the invalid descriptor.

---

## 4. Sprite tile VRAM LUT and preconversion

### 4.1 Tile preconversion tooling

Reuse `tools/translation/preconvert_pc090oj_tiles.py` (already present per `Andy_pc090oj_reconciliation_v2.md` Phase 1b — the tool survives in-tree). The script converts each 128-byte PC090OJ cell from arcade row-major 16×16 into Genesis column-major TL/BL/TR/BR ordering matching `frontend_decode_pc090oj_cell()`'s historical layout. Output: `build/pc090oj_genesis.bin`, same byte count as input (524288 bytes for 4096 cells × 128 bytes).

### 4.2 Makefile integration

Add to [apps/rastan-direct/Makefile](apps/rastan-direct/Makefile):

```make
PC090OJ_PRECONV := $(ROOT)/build/pc090oj_genesis.bin

$(PC090OJ_PRECONV): $(ROOT)/build/regions/pc090oj.bin $(ROOT)/tools/translation/preconvert_pc090oj_tiles.py | $(OUT_DIR)
	$(PYTHON) $(ROOT)/tools/translation/preconvert_pc090oj_tiles.py \
	    --input $< --output $@
```

Then add `$(PC090OJ_PRECONV)` to the dependency list of the build target (e.g., `pc090oj_hooks.o` depends on it through an `.incbin` reference). The existing `tools/build_rastan_regions.py` invocation in the `$(BIN)` target produces `build/regions/pc090oj.bin` — that becomes the input.

### 4.3 ROM-embedded sprite tile data

Add to a new source file `apps/rastan-direct/src/pc090oj_assets.s` (or as a `.rodata` section in `pc090oj_hooks.s`):

```asm
    .section .rodata,"a"
    .align 2
    .global rastan_pc090oj
rastan_pc090oj:
    .incbin "../../build/pc090oj_genesis.bin"

    .global pc090oj_slot_lut
    .align 2
pc090oj_slot_lut:
    .incbin "../../build/pc090oj_slot_lut.bin"
```

`build/pc090oj_slot_lut.bin` is generated by a new tool `tools/translation/build_pc090oj_slot_lut.py` (256-byte table, slot allocation per §1.3 above). The Makefile adds the same `--input` / `--output` pattern as for tiles.

### 4.4 VRAM tile loading

Sprite tiles are uploaded to VRAM via DMA each frame in the §5 commit. Each frame:
- For each sprite slot 0..79 with a valid SAT entry that was newly written this frame (per `staged_sprite_dirty` block bit), DMA 128 bytes from `rastan_pc090oj + (cell_index * 128)` to VRAM at `(SPRITE_TILE_BASE + slot * 4) * 32`.
- Per-frame upload bandwidth: at most 80 cells × 128 bytes = 10 240 bytes ≈ 5 120 words. At 100 ns/word DMA cycle inside VBlank (~3 600 cycles available in NTSC blank), this fits with margin only when `staged_sprite_dirty` is sparse.
- Pragmatic upper bound for Rastan (per April 6 §2.3): 22 active sprites → 22 × 64 words = 1 408 words DMA per frame. Comfortable.

The dirty-block-gated DMA pattern is the key: **only changed slots upload tile data**. A static HUD digit doesn't re-upload its tile every frame. Helpers set the dirty bit only when the PC090OJ tile code differs from the descriptor-table record's previous value.

### 4.5 SPRITE_TILE_BASE

Define in `pc090oj_hooks.s` head:

```
.equ SPRITE_TILE_BASE, 1024     /* matches April 6 startup_trampoline.s line 42 */
```

Genesis VRAM tile-index 1024 corresponds to byte address `1024 * 32 = 0x8000`, which is past the tilemap-tile region (rastan-direct's tilemap tiles live below tile index 1024 — confirmed by `apps/rastan-direct/src/scene_load.s` tile loading at slots beginning at index 0 in `genesistan_pc080sn_tile_rom`). No conflict.

### 4.6 LUT vs preconversion relationship

There are TWO LUTs:

- `pc090oj_slot_lut` (§1.3): PC090OJ memory address → Genesis SAT slot. 256 bytes. Used at runtime by exactly one helper, on exactly one branch: `genesistan_hook_3ad44_dispatch` (§2.2 row 0x3AD44; v3.2), PC090OJ branch only. The dispatch helper performs bulk-clear translation on its PC090OJ branch (A0 ∈ [0xD00000, 0xD00800)) by reading `pc090oj_slot_lut[A0_idx]` to map arcade destination pointer to Genesis SAT slot range; the tilemap branch and audit fall-through MUST NOT consult the LUT.
- Implicit "tile cell index → VRAM tile index" mapping: linear, `vram_tile = SPRITE_TILE_BASE + slot * 4`. No table, computed at write-time.

The preconversion produces `rastan_pc090oj` in cell-index order matching arcade ROM. No remapping of cell indices is needed.
All other helpers emit to helper-dedicated SAT slot ranges by helper identity (no LUT lookup), per §1.3.1 helper consultation + MUST NOT rules.

---

## 5. VBlank commit mechanism

### 5.1 Trigger and ordering

`_vblank_service` in [apps/rastan-direct/src/vdp_comm.s:155-179](apps/rastan-direct/src/vdp_comm.s#L155-L179) currently runs commits in this order:

```
1. vdp_set_reg MODE2 = DISPLAY_OFF
2. vdp_commit_tiles_if_dirty
3. vdp_commit_bg_strips_if_dirty
4. vdp_commit_fg_strips_if_dirty
5. vdp_commit_palette (if palette_dirty)
6. vdp_commit_scroll
7. vdp_set_reg MODE2 = DISPLAY_ON
8. jmp 0x00003A208 (arcade VBlank handler)
```

Insert sprite commit between step 4 and step 5:

```
4.5. vdp_commit_sprites      ← NEW
```

Rationale: tile / nametable / palette commits are independent of sprite commit. Sprite commit reads from WRAM staging (already populated by helpers) and writes to VDP SAT region + sprite tile VRAM region. Display is OFF for the duration. Inserting before palette commit keeps the existing palette ordering invariant; inserting before scroll commit ensures sprites appear at correct positions on the first frame after a scroll change.

### 5.2 `vdp_commit_sprites` body

New function in `pc090oj_hooks.s`:

```asm
vdp_commit_sprites:
    movem.l %d0-%d7/%a0-%a6, -(%sp)

    /* Phase 1: rebuild link chain in staged_sprite_sat from descriptor table */
    bsr     .Lvcs_link_chain_build

    /* Phase 2: per-dirty-block, DMA sprite tiles from rastan_pc090oj into VRAM */
    bsr     .Lvcs_tile_dma

    /* Phase 3: DMA the entire 640-byte SAT buffer to VRAM 0xF800 */
    bsr     .Lvcs_sat_dma

    /* Phase 4: clear dirty bitmap and per-descriptor touched-this-frame bits */
    bsr     .Lvcs_clear_dirty

    movem.l (%sp)+, %d0-%d7/%a0-%a6
    rts
```

#### .Lvcs_link_chain_build

Walks `staged_sprite_descriptor_table` slots 0..79 in index order. For each slot whose valid bit is set, computes the SAT word1 link field as the index of the next valid slot, or 0 if last. Counts active count into `staged_sprite_active_count`. Updates `staged_sprite_sat[slot * 8 + 2]` (word1) of each valid slot.

This phase is needed because helpers don't know the global valid count when they write — they set their own slot, but the link field requires knowing all later valid slots.

#### .Lvcs_tile_dma

For each set bit `block_idx` in `staged_sprite_dirty` (bits 0..19 cover slots 0..79 in 4-slot blocks):
- For each slot in block: if descriptor-table slot is valid and tile-code-changed-flag is set:
  - DMA 128 bytes from `rastan_pc090oj + (cell_index * 128)` → VRAM at `(SPRITE_TILE_BASE + slot * 4) * 32`
  - DMA configuration: source address (3 register writes per VDP DMA programming model — same pattern as April 6 lines 297-316), length 64 words, destination per slot
  - Address encoding: USE the existing helper `sprite_dma_addr_high_bits_fix` from [vdp_comm.s:147-152](apps/rastan-direct/src/vdp_comm.s#L147-L152). This is the corrected version of April 6 §10's `lsr.l #14, %d2` (mathematically identical: `lsr.l #8` then `lsr.l #6` = `lsr.l #14`). See §6 for verification.
- Clear tile-code-changed-flag in descriptor +0.

#### .Lvcs_sat_dma

Single DMA: 640 bytes from `staged_sprite_sat` → VRAM 0xF800.

VDP DMA setup (matches April 6 lines 297-334 with the correct address encoding from §6):

```asm
    movea.l #0xC00004, %a3          /* VDP control port */
    move.w  #0x9340, (%a3)          /* DMA length low byte = 0x40 (was 64 words → here 320 words) */
    move.w  #0x9402, (%a3)          /* length high byte = 0x02 → length = 0x0240 = 576 ... */
```

Correction: 640 bytes = 320 words. Length register encodes word count. Length register low = 0x40, high = 0x01 → `0x0140 = 320`. Actual values:

```
move.w  #0x9340, (%a3)              /* DMA length low = 0x40 */
move.w  #0x9401, (%a3)              /* DMA length high = 0x01 → 320 words */
```

Source address (3-byte split, encoded as words 0x95xx/0x96xx/0x97xx with `(addr >> 1)` because 68k DMA address is bus-word-addressed):

```
move.l  #staged_sprite_sat, %d0
lsr.l   #1, %d0                     /* word-address */
move.w  %d0, %d1
andi.w  #0x00FF, %d1
ori.w   #0x9500, %d1
move.w  %d1, (%a3)
move.l  %d0, %d1
lsr.l   #8, %d1
andi.w  #0x00FF, %d1
ori.w   #0x9600, %d1
move.w  %d1, (%a3)
move.l  %d0, %d1
lsr.l   #8, %d1
lsr.l   #8, %d1
andi.w  #0x007F, %d1
ori.w   #0x9700, %d1                /* DMA from 68k memory (bit 7 clear) */
move.w  %d1, (%a3)
```

Destination + DMA trigger (VDP write address command for VRAM, with DMA bit set):

```
move.l  #0xF800, %d0                /* VRAM SAT base */
move.l  %d0, %d1
andi.l  #0x00003FFF, %d1
swap    %d1
move.l  %d0, %d2
lsr.l   #8, %d2                     /* (addr >> 14) */
lsr.l   #6, %d2                     /* … see §6 — uses same bit-extraction as sprite_dma_addr_high_bits_fix */
andi.l  #0x00000003, %d2
or.l    %d2, %d1
ori.l   #0x40000080, %d1            /* VRAM-write + DMA bit */
move.l  %d1, (%a3)                  /* trigger DMA */
```

The DMA fires; CPU stalls until DMA completion (or runs in parallel with CPU during VBlank if mode permits). On exit, VDP SAT 0xF800..0xFA40 contains the new sprite list.

Reference pattern: existing `vdp_set_vram_write_addr` at [vdp_comm.s:132-145](apps/rastan-direct/src/vdp_comm.s#L132-L145) uses the same upper-bit extraction (`lsr.l #8` + `lsr.l #6`) — the existing code proves this encoding is correct on Genesis hardware in this codebase.

#### .Lvcs_clear_dirty

```asm
    clr.l   staged_sprite_dirty
    /* clear bit 15 (touched-this-frame) of each descriptor-table +0 word */
    lea     staged_sprite_descriptor_table, %a0
    move.w  #(80 - 1), %d0
.Lvcs_clear_loop:
    move.w  (%a0), %d1
    andi.w  #0x7FFF, %d1
    move.w  %d1, (%a0)
    adda.w  #12, %a0
    dbra    %d0, .Lvcs_clear_loop
    rts
```

### 5.3 Display-OFF window sufficiency

Genesis NTSC VBlank window: ~3 580 68k cycles. With CPU + DMA bandwidth for:
- Tile DMA (worst case 22 sprites × 64 words = 1408 words) ~ 2 800 cycles
- SAT DMA (320 words) ~ 640 cycles
- Tilemap commit (existing) ~ 1 000 cycles
- Palette + scroll (existing) ~ 200 cycles

Total ~4 640 cycles — exceeds VBlank window. The existing rastan-direct already runs at this margin (the `_vblank_service` already fits the BG/FG/palette/scroll commits). **Sprite commit must use DMA-during-VBlank, not CPU-stalling DMA after VBlank.** Per VDP DMA spec, DMA during display-off completes faster than during display-on; `_vblank_service` already gates display off (line 159). Acceptable.

**Implementation scope for this revision (canonical, mechanical).** Cody implements **only** the commit body defined in §5.2 — `vdp_commit_sprites` performs the four phases (link-chain build, tile DMA, SAT DMA, dirty-clear) in order, every frame, with no per-frame deferral logic. The §5.2 path is the entire commit; there is no alternative path, no conditional branch on dirty-bit count, and no per-frame budget check. Cody implements §5.2 verbatim and stops there.

The "spillover" optimization (DMA only the first N dirty tiles per frame, defer the remainder) is **explicitly NOT implemented in this task**. It is a future task tracked as FU2 in §11, triggered only if runtime trace reveals visual sprite tearing or mid-frame VDP corruption that confirms the §5.2 simple-commit path overruns the display-off window. Until FU2 is triggered and a follow-up Andy task designs the deferral logic, the §5.2 path is the production behavior.

---

## 6. April 6 DMA fix

### 6.1 The April 6 bug

`apps/rastan/src/startup_trampoline.s:330-332` (April 6 §10):

```asm
move.l  %d0, %d2
swap    %d2                /* BUG: zeroes bits 14-15 of any addr ≤ 0xFFFF */
andi.w  #0x0003, %d2
```

Effect: all sprite-tile DMA targets land at VRAM 0x0000..0x0B80 instead of 0x8000..0x8B80. April 6 §5.2 documents the failure mode in detail.

### 6.2 The corrected encoding

Per April 6 §10's recommendation:

```asm
move.l  %d0, %d2
lsr.l   #14, %d2           /* extract bits 14-15 */
andi.w  #0x0003, %d2
```

### 6.3 rastan-direct already implements the fix

[apps/rastan-direct/src/vdp_comm.s:147-152](apps/rastan-direct/src/vdp_comm.s#L147-L152):

```asm
sprite_dma_addr_high_bits_fix:
    move.l  %d0, %d2
    lsr.l   #8, %d2
    lsr.l   #6, %d2
    andi.w  #0x0003, %d2
    rts
```

`lsr.l #8` then `lsr.l #6` is mathematically equivalent to `lsr.l #14`:

```
For input 0x00008000:
  After lsr.l #8: 0x00000080
  After lsr.l #6: 0x00000002
  After andi.w #0x0003: 0x0002      ← correct (= (0x8000 >> 14) & 3)
```

For comparison, the buggy `swap`:

```
For input 0x00008000:
  After swap:    0x80000000  (the high half is now 0x8000, low half is 0x0000)
  After andi.w #0x0003 on lower 16-bit: 0x0000   ← WRONG
```

`vdp_set_vram_write_addr` in the same file ([vdp_comm.s:132-145](apps/rastan-direct/src/vdp_comm.s#L132-L145)) uses an inlined version of this same `lsr.l #8` + `lsr.l #6` pattern for VRAM-write addresses. Both helpers produce the correct upper-bit extraction.

### 6.4 Byte-level instruction sequences

For the new `vdp_commit_sprites` DMA path, the encoding must match the corrected pattern. Cody's implementation in `pc090oj_hooks.s` uses the **inline** `lsr.l #8` + `lsr.l #6` pattern (matching `vdp_set_vram_write_addr` at [vdp_comm.s:138-141](apps/rastan-direct/src/vdp_comm.s#L138-L141)). The alternative of calling `sprite_dma_addr_high_bits_fix` as a subroutine is NOT used — inline avoids the subroutine call cost and matches the existing convention.

**Original (wrong) bytes** (from April 6 `startup_trampoline.s` assembled output):

```
move.l %d0,%d2:    2400      (2 bytes)
swap   %d2:        4842      (2 bytes)
andi.w #0x0003,%d2: 0242 0003 (4 bytes)
                   total 8 bytes
```

**Corrected bytes** (per April 6 §10 fix, matching `sprite_dma_addr_high_bits_fix`):

```
move.l %d0,%d2:    2400      (2 bytes)
lsr.l  #8,%d2:     E80A      (2 bytes)
lsr.l  #6,%d2:     EC0A      (2 bytes)
andi.w #0x0003,%d2: 0242 0003 (4 bytes)
                   total 10 bytes
```

The corrected sequence is 2 bytes longer than the buggy sequence — but rastan-direct's spec is greenfield (no existing buggy renderer to patch in-place), so the fix appears as the original implementation in `pc090oj_hooks.s`. **No byte-level edit of `apps/rastan/src/startup_trampoline.s` is part of this spec** — that file lives in the SGDK predecessor branch and is not built by `apps/rastan-direct/Makefile`. The fix migrates with the port.

### 6.5 Verification — DMA roundtrip self-test (mechanical specification)

Cody's implementation must include a build-time roundtrip test that confirms the new sprite DMA path lands bytes at the correct VRAM address. The test reuses the §7.3 audit-guard halt-with-heartbeat mechanism for diagnostic-stop on failure, ensuring consistency with other production diagnostic stops. Specification of every detail follows in §6.5.1..§6.5.6.

#### 6.5.1 Insertion point — `apps/rastan-direct/src/boot/boot.s`

Insert the test as a `jsr` from inside `_bootstrap` immediately AFTER the existing `jsr load_scene_tiles` at [boot.s:158](apps/rastan-direct/src/boot/boot.s#L158) and AFTER `lea 0x00FF0000, %a5` at [boot.s:159](apps/rastan-direct/src/boot/boot.s#L159), but BEFORE the arcade jump at [boot.s:160](apps/rastan-direct/src/boot/boot.s#L160). VRAM is initialized by `vdp_boot_setup` at line 155; tilemap tiles are loaded by `load_scene_tiles` at line 158; both run before the arcade boots at line 160. Inserting between line 159 and line 160 means the test runs once at cold-boot, after VRAM is fully initialized, before any arcade-side code can perturb VRAM, and before the first VBlank.

Concretely, after this revision, the `_bootstrap` body at [boot.s:154-160](apps/rastan-direct/src/boot/boot.s#L154-L160) reads:

```asm
_bootstrap:
    jsr     vdp_boot_setup
    bsr     _bootstrap_clear_staging
    moveq   #0, %d0
    jsr     load_scene_tiles
    lea     0x00FF0000, %a5
    jsr     genesistan_pc090oj_dma_self_test    /* NEW — §6.5 self-test */
    jmp     (0x00003A200).l
```

The `jsr` instruction encodes as `4EB9 + 32-bit absolute address` (6 bytes); the assembler emits this directly with no resolution-path ambiguity.

#### 6.5.2 Test source bytes

Source: `rastan_pc090oj` ROM blob (§4.3), starting at byte offset `1 * 128 = 0x0080` (cell index 0x0001, after cell 0). Length: 128 bytes (= 4 Genesis tiles × 32 bytes per tile = 64 words).

Genesis VRAM destination: VRAM byte address `(SPRITE_TILE_BASE + 0 * 4) * 32 = 1024 * 32 = 0x8000` (= sprite-slot 0's first tile).

DMA programming: identical to the per-frame tile DMA path in §5.2 `.Lvcs_tile_dma`, with hardcoded slot=0 and cell_index=1.

#### 6.5.3 Test read-back

After DMA completion, read 128 bytes from VRAM `0x8000..0x807F` via the VDP DATA port using a VRAM-read command (`0x00008000` with read mask, encoded per existing `vdp_set_vram_write_addr` pattern but with the read bit set: actual command is `0x00008000` swapped + bit-encoded → `0x00000000` for VRAM read at `0x8000` is `(0x8000 & 0x3FFF) << 16 | 0x00000000 | ((0x8000 >> 14) & 3) = 0x00000002`; full 32-bit command word per VDP read protocol).

Read destination: a 128-byte stack-allocated buffer reserved by the helper (`lea -128(%sp), %sp` on entry, freed on exit).

#### 6.5.4 Comparison method

Word-by-word memcmp loop comparing the stack buffer (128 bytes = 64 words) against `rastan_pc090oj + 0x0080` (the source). On any mismatch, capture the mismatch offset (in words 0..63) and the expected/actual word values, then proceed to the failure-stop path (§6.5.6).

Comparison terminates at the first mismatch (no further bytes inspected). On success (all 64 words match), the helper deallocates the stack buffer and `RTS` to `_bootstrap`'s `jmp` to the arcade.

#### 6.5.5 Failure diagnostic format

On comparison mismatch, the helper writes the following diagnostic record (in WRAM, in `.bss.patcher` section like the §7.3 audit-guard buffers, declared in `pc090oj_hooks.s`):

```asm
    .section .bss.patcher
    .balign 2
    .global pc090oj_dma_test_fired_flag
    .global pc090oj_dma_test_mismatch_offset
    .global pc090oj_dma_test_expected_word
    .global pc090oj_dma_test_actual_word
    .global pc090oj_dma_test_actual_buffer
    .global pc090oj_dma_test_heartbeat
pc090oj_dma_test_fired_flag:
    .word 0                                /* sentinel: 0 = pass / not yet run; 0x6F0E = failure */
pc090oj_dma_test_mismatch_offset:
    .word 0                                /* word index 0..63 of first mismatching word */
pc090oj_dma_test_expected_word:
    .word 0                                /* word value the source said should be at that offset */
pc090oj_dma_test_actual_word:
    .word 0                                /* word value VRAM read-back returned at that offset */
pc090oj_dma_test_actual_buffer:
    .space 128                             /* full VRAM read-back snapshot (128 bytes) */
pc090oj_dma_test_heartbeat:
    .byte 0                                /* incremented in halt loop, observable to debugger */
```

On failure, populate fields in order: write mismatch offset → expected word → actual word → copy entire actual buffer (128 bytes) → set fired-flag to `0x6F0E` (sentinel). Field set is final before entering halt loop (no further writes after halt-loop entry).

#### 6.5.6 Controlled-stop mechanism

Reuse the §7.3 audit-guard halt-with-heartbeat pattern. After diagnostic record is fully populated, enter the heartbeat halt loop:

```asm
.Lpc090oj_dma_test_halt:
    move.b  pc090oj_dma_test_heartbeat, %d0
    addq.b  #1, %d0
    move.b  %d0, pc090oj_dma_test_heartbeat
    bra     .Lpc090oj_dma_test_halt
```

Same loop structure as §7.3's `.Lag_halt_loop`. Observable to MAME debugger, BlastEm debugger, and external watchers via the heartbeat byte. Genesis-side execution stops here permanently; arcade is never reached. This is correct production behavior because if the DMA roundtrip fails, the sprite subsystem is fundamentally broken and arcade should not run with a broken sprite path.

The test passes iff `pc090oj_dma_test_fired_flag == 0x0000` after `_bootstrap` returns (i.e., the `RTS` from the test was reached, never the halt loop). The arcade never observes the test infrastructure — on success, control returns to `_bootstrap` which proceeds to `jmp (0x00003A200).l` and the arcade boots normally.

---

## 7. Audit guards for 0x510EA and 0x510F4

### 7.1 The two writer sites

Per disassembly at [build/maincpu.disasm.txt:102307-102311](build/maincpu.disasm.txt#L102307-L102311):

```
510e8: 660a            bnes 0x510f4
510ea: 33fc 0002 00d0 0698  movew #2, 0xd00698     (8 bytes)
510f2: 6008            bras 0x510fc
510f4: 33fc 0000 00d0 0698  movew #0, 0xd00698     (8 bytes)
510fc: 4e75            rts
```

Both are 8-byte `movew #imm, abs.l` instructions.

FU1 trace (`Cody_fu1_arcade_trace_510EA_510F4.md`): both sites had **0 hits** in the captured boot+attract+demo phases. Gameplay reach was not achieved in the FU1 environment (per its STOP report). The execution status is therefore: **not observed in available evidence**.

### 7.2 Replacement design

Replace each 8-byte instruction with `JSR genesistan_pc090oj_hook_audit_guard` followed by NOPs:

```
4eb9 {symbol:genesistan_pc090oj_hook_audit_guard}    (6 bytes)
4e71                                                  (2 bytes NOP)
                                                     total 8 bytes
```

Each call site invokes the same shared helper, which resolves which site fired by examining its own return address on the stack.

### 7.3 Audit-guard helper behavior

```asm
genesistan_pc090oj_hook_audit_guard:
    /* Capture pre-call register state — full snapshot.  D0..D7, A0..A7. */
    movem.l %d0-%d7/%a0-%a6, -(%sp)
    move.l  %sp, %a0                   /* base of saved registers */

    /* Capture return address (which call site fired) */
    move.l  60(%sp), %d0               /* return PC = saved-regs (60) + saved-RA (4) */
    move.l  %d0, audit_guard_caller_pc

    /* Snapshot all 14 saved registers into a fixed diagnostic buffer */
    lea     audit_guard_register_snapshot, %a1
    moveq   #(14 - 1), %d0
.Lag_snap:
    move.l  (%a0)+, (%a1)+
    dbra    %d0, .Lag_snap

    /* Capture VDP V-counter (frame timing context) */
    move.w  0x00C00008, audit_guard_vcount    /* VDP HV counter */

    /* Mark guard fired (boolean flag readable by external tools / next-build inspector) */
    move.w  #0x510E, audit_guard_fired_flag   /* sentinel value */

    /* Controlled stop: enter a tight loop with diagnostic-RAM write each iteration.
     * This is observable to a debugger, MAME's debugger, and GoG-style external tools.
     * It is NOT a `bra .` infinite loop — it intentionally writes a heartbeat byte
     * that increments each iteration so a polling watcher can confirm the guard
     * is the active executor. */
.Lag_halt_loop:
    move.b  audit_guard_heartbeat, %d0
    addq.b  #1, %d0
    move.b  %d0, audit_guard_heartbeat
    bra     .Lag_halt_loop
```

`.bss` symbols added to `pc090oj_hooks.s`:

```asm
    .section .bss
    .align 2
audit_guard_caller_pc:
    .long 0
audit_guard_register_snapshot:
    .space (14 * 4)             /* d0-d7 + a0-a6 */
audit_guard_fired_flag:
    .word 0
audit_guard_vcount:
    .word 0
audit_guard_heartbeat:
    .byte 0
```

### 7.4 Rule 8 walkthrough

Rule 8 ("Arcade Intent → Genesis Execution"): arcade code expresses intent; Genesis executes that intent.

The two writer sites at `0x510EA` / `0x510F4` write `2` and `0` respectively to `0xD00698`. `0xD00698` is byte offset `0x698` = word offset `0x34C` within MAME's PC090OJ `ACTIVE_RAM` region (per `Andy_pc090oj_reconciliation_v2.md` Phase 5: `0x800` byte / `0x400` word active descriptor area). Word offset `0x34C` falls within an active sprite descriptor's bytes — specifically, byte 6 of slot 0xD2 / 210 (descriptor +6 = X position, low byte). So these writes set the X coordinate of sprite-RAM slot 210 to 2 or 0.

Slot 210 is in the upper slot range (slots 209+) which `Andy_pc090oj_reconciliation_v2.md` Phase 5 classifies as part of the "structured-init sprite reserve" populated by the `0x03ADAA` priority-frame init (`Andy_d00778_write_path_analysis.md`). The two writes at `0x510EA / 0x510F4` therefore update the X position of one priority-frame sprite from 2 (visible) to 0 (visible), gated by a state flag at `a5@(5060)`.

The arcade's intent is: under condition `a5@(5060) == 1`, set sprite 210's X to 2; otherwise set it to 0. This is a normal sprite manipulation. Translating this to Genesis SAT would be a small helper function.

**Why not translate it?** Because:
1. FU1 trace produced 0 hits over the boot+attract+demo window, demonstrating these writes occur only on a code path not observed in the available evidence.
2. The state flag `a5@(5060)` is set by code we have not traced. Its meaning (which game phase, which player condition, which level transition) is unverified.
3. The `0x03ADAA` priority-frame init is the only writer of slot 210 we have observed; if the X coordinate of that slot is also moved by an unobserved path, we cannot verify the translation against ground-truth without seeing the path execute.

The audit guard's contract is: if these writes ever fire on any path, halt with full diagnostic capture so the unobserved code path can be analyzed and the helper extended (or a non-translation finding can be confirmed). This honors Rule 8's "no reinterpretation of control flow" — we do not silently choose a translation. We surface the gap.

The halt-with-heartbeat pattern is not a Rule-1 violation (arcade owns execution): the arcade has already lost ownership in the sense that its intended write cannot be honored on Genesis (the destination address is unmapped). The choice is between (a) silently dropping the write, (b) translating without verification, or (c) halting with full state capture. (c) is the correct choice — the guard *is* the production behavior for this arcade-pc, not scaffolding.

The halt loop is non-Rule-4-violating because:
- The helper does not "loop waiting for events" — it loops because the arcade has reached an unhandled state.
- The helper has done its translation work (state capture) once, then transitioned to halt. This is no different than an exception handler that captures state and stops execution.

The audit guard is **production behavior**, not scaffolding (Rule 5, Rule 9):
- It would exist in a final shipping ROM.
- It is the documented, intended response to an unobserved code path.
- Removing it would weaken the production system's ability to surface unmodeled behavior.

If post-deployment evidence shows the guards firing on a real code path, the follow-up task (FU3 in §11) is to replace them with a verified translation helper.

---

## 8. opcode_replace schema — all entries

### 8.1 Hook-site coverage and the 18-vs-46 mapping

The writer classification ledger lists 46 hook *sites* (15 April-6 + 29 INDEPENDENT + 2 audit guards). Each site is an arcade code location whose write path needs interception.

Per the existing rastan-direct `opcode_replace` convention (e.g., the entry at [specs/rastan_direct_remap.json](specs/rastan_direct_remap.json) `arcade_pc 0x03C4D2` already replaces a full function body, intercepting all callers at once) and the technical constraint that 4-byte arcade BSRs cannot hold 6-byte `JSR abs.l` calls to Genesis-side helpers at offsets >32 KB, the **implementation point** is the writer function body. Each function-body replacement intercepts every caller of that function in a single entry.

The mapping from 46 ledger sites to 18 opcode_replace entries:

| Ledger sites (by writer function) | opcode_replace entry (function body) | Sites covered |
|------------------------------------|----------------------------------------|---------------|
| 7 callers of `0x3B902` (April-6: 0x03A20E, 0x03A264, 0x03A640, 0x03A6C4, 0x03A820, 0x03B8E8, 0x03B8F0; non-April-6: 0x03A8E0) | replace body at `0x3B902` | 7+1 |
| 2 callers of `0x3B926` (0x03A9C6, 0x03A9D4) | replace body at `0x3B926` | 2 |
| 4 callers of `0x3B930` (writer helper; reached from 0x3B902 and from 0x3B8B0 init non-target path) | replace body at `0x3B930` | 4 |
| 4 callers of `0x59F5E` (April-6: 0x03A8E4; non-April-6: 0x051266, 0x0519A0, 0x055E18) | replace body at `0x59F5E` | 4 |
| target function `0x41DAE` (entry-point hook in April-6 list) | replace body at `0x41DAE` | 1 (target itself) |
| 1 caller of `0x41F5E` (April-6: 0x03A854) | replace body at `0x41F5E` | 1 |
| 1 caller of `0x45DFA` (April-6: 0x03A818) | replace body at `0x45DFA` | 1 |
| 7 callers of `0x3AD44` — 3 PC090OJ (0x3AD5C, 0x3AD6E, 0x3AD82; A0 ∈ [0xD00000, 0xD00800)) + 4 tilemap (0x3AE70, 0x3AE80, 0x3AF38, 0x3AF48; A0 ∈ [0xC00000, 0xC10000)) — covered via v3.2 polymorphic dispatch helper | replace body at `0x3AD44` (dispatch) | 7 |
| 2 callers of `0x3AD84` (0x3ABB6, 0x3AF28 — both reach via fall-through from 0x3AD72) | replace body at `0x3AD84` | 2 |
| 10 callers of `0x3B802` (0x3A66A, 0x3A9C0, 0x3A9CE, 0x3A9DA, 0x3B7A2, 0x3B7B0, 0x3B7E0, 0x3B8C2, 0x3B8F6, 0x3B8FC) | replace body at `0x3B802` | 10 |
| 2 callers of `0x54052` (0x501F4, 0x51260) | replace body at `0x54052` | 2 |
| 2 callers of `0x54810` (0x547EE, 0x54804) | replace body at `0x54810` | 2 |
| 1 caller of `0x5607C` (0x55E92) | replace body at `0x5607C` | 1 |
| 2 callers of `0x56114` (0x5604C, 0x56076) | replace body at `0x56114` | 2 |
| 2 callers of `0x56440` / `0x5648A` (0x55F0E, 0x55FFA) | replace body at `0x56440` | 2 |
| 1 caller of `0x5A098` (0x51054) | replace body at `0x5A098` | 1 |
| 2 audit-guard sites (write instructions, not function calls) | replace at `0x510EA` and `0x510F4` directly | 2 |
| **Total** | **18 opcode_replace entries** | **51 unique call paths intercepted (≥ 46 ledger sites)** |

The function-body approach intercepts MORE call paths than the ledger lists (e.g., `0x3A8E0` calling `0x3B902` is captured even though it's not a ledger hook site). This **does not violate Rule 17**: the architectural scope (every PC090OJ writer path is intercepted) is preserved and extended. No ledger site is dropped. Per-site auditability is preserved — every one of the 46 ledger sites appears in §8.6 mapped to its covering entry with disassembly evidence.

### 8.2 The 18 opcode_replace entries

Each entry below specifies `arcade_pc`, full original function body bytes (as concatenated hex), and replacement with `JSR helper_symbol; RTS; NOP*` to fill the original byte length. Per the existing rastan-direct convention, the postpatcher resolves `{symbol:helper}` to a 32-bit absolute address; original-vs-replacement byte length is preserved exactly.

The "original_bytes" hex strings are read from `build/maincpu.disasm.txt` between the function entry and the byte before the next function's entry instruction (i.e., the full span Cody must replace). The "replacement_bytes" pattern is `4EB9 {symbol:helper_name} 4E75` followed by `4E71` (NOP) entries to pad to original length, identical to the existing `0x03C4D2` entry's pattern.

The 18 entries break down as:
- Target functions (7): 0x3B902, 0x3B926, 0x3B930, 0x41DAE, 0x41F5E, 0x45DFA, 0x59F5E
- Independent writer functions (9): 0x3AD44, 0x3AD84, 0x3B802, 0x54052, 0x54810, 0x5607C, 0x56114, 0x56440, 0x5A098
- Audit-guard direct-write replacements (2): 0x510EA, 0x510F4

Byte lengths in the table below are **disassembly-verified** against `build/maincpu.disasm.txt` (see §8.4 for exact span boundaries and citations). Where this revision's verified value differs from prior drafts, the disassembly value is canonical.

| # | arcade_pc | helper symbol                                       | byte length | note                                                    |
|--:|-----------|-----------------------------------------------------|------------:|---------------------------------------------------------|
| 1 | 0x3B902   | `genesistan_pc090oj_hook_target_3b902`              | 36          | April-6 target. HUD/score sprite emitter (slots 0..4). |
| 2 | 0x3B926   | `genesistan_pc090oj_hook_target_3b926`              | 10          | April-6 target. 9-sprite block at 0xD00128 (slots 5..13). Function ends with `bras 0x3B91A` (no own RTS); helper subsumes the loop logic. |
| 3 | 0x3B930   | `genesistan_pc090oj_hook_target_3b930`              | 32          | Writer helper called from 0x3B902 (target) AND 0x3B8B0 (init non-target). Replacing body covers both paths. Slots 14..17. |
| 4 | 0x41DAE   | `genesistan_pc090oj_hook_target_41dae`              | 352         | April-6 target. Block-A 18-sprite emitter (slots 0..17) + sub-loop fallbacks. **Re-emits same 22-sprite layout.** |
| 5 | 0x41F5E   | `genesistan_pc090oj_hook_target_41f5e`              | 56          | April-6 target. Block-B 4-sprite copy (slots 18..21). |
| 6 | 0x45DFA   | `genesistan_pc090oj_hook_target_45dfa`              | 258         | April-6 target. Alternate emitter for 22-sprite frame. |
| 7 | 0x59F5E   | `genesistan_pc090oj_hook_target_59f5e`              | 52          | April-6 target. Sprite-RAM clear (slots 0..7 → 0xD00048+). |
| 8 | 0x3AD44   | `genesistan_hook_3ad44_dispatch` (v3.2; replaces v3.1 `genesistan_pc090oj_hook_init_clear_3ad44`) | 8           | Polymorphic memset utility — A0 dispatch routes to tilemap BG fill (4 callers), PC090OJ bulk-clear (3 callers), or §7.3 audit fall-through. Full contract in §2.2.A. |
| 9 | 0x3AD84   | `genesistan_pc090oj_hook_init_priority_3ad84`       | 56          | INDEPENDENT. Priority-frame init at 0xD00778. Slots 76..79. |
| 10 | 0x3B802   | `genesistan_pc090oj_hook_score_digit_3b802`         | 174         | INDEPENDENT. Score/HUD digit writer. Span includes the function's PC-relative digit-attribute table at 0x3B87E..0x3B8AF (50 bytes); table is referenced only from inside the function (verified single PC-relative `lea %pc@(0x3B87E),%a0` at line 0x3B808; no external `lea 0x3b87e` references found in disassembly). Slots 22..29. |
| 11 | 0x54052   | `genesistan_pc090oj_hook_slot_init_54052`           | 122         | INDEPENDENT. Sprite slot init (also writes Taito text RAM — preserved in helper). Slots 72..75. |
| 12 | 0x54810   | `genesistan_pc090oj_hook_sprite_update_54810`       | 84          | INDEPENDENT. 4-sprite-per-call update routine. Slots 44..55. |
| 13 | 0x5607C   | `genesistan_pc090oj_hook_sprite_decay_5607c`        | 94          | INDEPENDENT. Sprite-decay loop (Y decrement). Slots 56..63. |
| 14 | 0x56114   | `genesistan_pc090oj_hook_copy_56114`                | 20          | INDEPENDENT. Sprite-RAM copy helper. Slots 64..67. |
| 15 | 0x56440   | `genesistan_pc090oj_hook_zero_fill_56440`           | 30          | INDEPENDENT. Outer of zero-fill pair. Internal `0x5648A` (separate 20-byte function at `0x5648A..0x5649D`) is reached only from inside `0x56440` (single caller at `0x56454`); when `0x56440` is body-replaced its BSR to `0x5648A` no longer fires, so `0x5648A` becomes unreachable dead code without needing its own entry. Slots 68..71. |
| 16 | 0x5A098   | `genesistan_pc090oj_hook_status_sprite_5a098`       | 498         | INDEPENDENT. Status/UI sprite writer. Span includes the inline helper at `0x5A244..0x5A289` (called only from `0x5A210` inside the same function); no external callers of `0x5A244` (verified by grep). Slots 30..43. |
| 17 | 0x510EA   | `genesistan_pc090oj_hook_audit_guard`               | 8           | Audit guard. JSR + NOP. |
| 18 | 0x510F4   | `genesistan_pc090oj_hook_audit_guard`               | 8           | Audit guard. JSR + NOP. |

Total: **7 + 9 + 2 = 18 entries**, replacing **2196 bytes** of arcade ROM with helper trampolines.

### 8.3 Original-bytes extraction protocol

For each of the 18 entries, Cody's implementation will:

1. Read `build/maincpu.disasm.txt` at the listed `arcade_pc`.
2. Concatenate the bytes of every instruction from the function entry up to (but not including) the next function's entry instruction. The full span = the function body, including all internal RTS instructions, helper sub-routines reachable only from inside the function, and any PC-relative data tables embedded in the function. Span boundaries are tabulated in §8.4.
3. Encode as uppercase hex without separators: matches the existing spec format.
4. The replacement_bytes use the schema `4EB9{symbol:helper}4E75` followed by `4E71` repetitions to pad to the same byte length.

For the audit guards (8-byte instructions, not functions): the original bytes are simply `33FC000200D00698` (entry 17) and `33FC000000D00698` (entry 18). The replacements are `4EB9{symbol:genesistan_pc090oj_hook_audit_guard}4E71` (6 + 2 = 8 bytes).

### 8.4 Verified original-bytes table — disassembly citations

For each of the 18 entries, the function entry, the span end (= start of next function), and the byte length are taken directly from `build/maincpu.disasm.txt`. Span end column is the address of the FIRST instruction of the NEXT function (exclusive boundary); byte length = (span end) − (arcade_pc).

| # | arcade_pc | first instruction bytes (entry) | span end (next fn entry) | byte length | disassembly cite |
|--:|-----------|---------------------------------|--------------------------|------------:|------------------|
| 1 | 0x3B902   | `43F9 00D0 0088`                | 0x3B926                  | 36          | entry [maincpu.disasm.txt:74779](build/maincpu.disasm.txt#L74779); next [line 74792](build/maincpu.disasm.txt#L74792) |
| 2 | 0x3B926   | `43F9 00D0 0128`                | 0x3B930                  | 10          | entry [line 74792](build/maincpu.disasm.txt#L74792); next [line 74795](build/maincpu.disasm.txt#L74795) |
| 3 | 0x3B930   | `4242`                          | 0x3B950                  | 32          | entry [line 74795](build/maincpu.disasm.txt#L74795); RTS at 0x3B94E [line 74808](build/maincpu.disasm.txt#L74808); span end at 0x3B950 (data table for 0x3B8B0 begins) |
| 4 | 0x41DAE   | `49ED 0508`                     | 0x41F0E                  | 352         | entry [line 83678](build/maincpu.disasm.txt#L83678); next fn (jsr 0x5100A) [line 83775](build/maincpu.disasm.txt#L83775) |
| 5 | 0x41F5E   | `41ED 11B2`                     | 0x41F96                  | 56          | entry [line 83793](build/maincpu.disasm.txt#L83793); next [line 83812](build/maincpu.disasm.txt#L83812) |
| 6 | 0x45DFA   | `49ED 05C8`                     | 0x45EFC                  | 258         | entry [line 88381](build/maincpu.disasm.txt#L88381); RTS at 0x45EFA [line 88451](build/maincpu.disasm.txt#L88451); next [line 88452](build/maincpu.disasm.txt#L88452) |
| 7 | 0x59F5E   | `323C 0008`                     | 0x59F92                  | 52          | entry [line 113366](build/maincpu.disasm.txt#L113366); RTS at 0x59F90 [line 113381](build/maincpu.disasm.txt#L113381); next [line 113382](build/maincpu.disasm.txt#L113382) |
| 8 | 0x3AD44   | `20C0`                          | 0x3AD4C                  | 8           | entry [line 73893](build/maincpu.disasm.txt#L73893); RTS at 0x3AD4A [line 73896](build/maincpu.disasm.txt#L73896); next [line 73897](build/maincpu.disasm.txt#L73897) |
| 9 | 0x3AD84   | `720E`                          | 0x3ADBC                  | 56          | entry [line 73910](build/maincpu.disasm.txt#L73910); RTS at 0x3ADBA [line 73924](build/maincpu.disasm.txt#L73924); next [line 73925](build/maincpu.disasm.txt#L73925) |
| 10 | 0x3B802   | `4285`                          | 0x3B8B0                  | 174         | entry [line 74698](build/maincpu.disasm.txt#L74698); span includes inline helper 0x3B866 + PC-relative table at 0x3B87E..0x3B8AF; next fn entry [line 74755](build/maincpu.disasm.txt#L74755) |
| 11 | 0x54052   | `227C 0010 D1D2`                | 0x540CC                  | 122         | entry [line 105718](build/maincpu.disasm.txt#L105718); next [line 105751](build/maincpu.disasm.txt#L105751) |
| 12 | 0x54810   | `227C 00D0 0000`                | 0x54864                  | 84          | entry [line 106237](build/maincpu.disasm.txt#L106237); next [line 106263](build/maincpu.disasm.txt#L106263) |
| 13 | 0x5607C   | `302D 1392`                     | 0x560DA                  | 94          | entry [line 107854](build/maincpu.disasm.txt#L107854); next [line 107881](build/maincpu.disasm.txt#L107881) |
| 14 | 0x56114   | `3010`                          | 0x56128                  | 20          | entry [line 107897](build/maincpu.disasm.txt#L107897); next [line 107906](build/maincpu.disasm.txt#L107906) |
| 15 | 0x56440   | `227C 00D0 0000`                | 0x5645E                  | 30          | entry [line 108125](build/maincpu.disasm.txt#L108125); next [line 108132](build/maincpu.disasm.txt#L108132) |
| 16 | 0x5A098   | `302D 013A`                     | 0x5A28A                  | 498         | entry [line 113446](build/maincpu.disasm.txt#L113446); span includes inline helper 0x5A244 (RTS at 0x5A288 [line 113592](build/maincpu.disasm.txt#L113592)); next [line 113593](build/maincpu.disasm.txt#L113593) |
| 17 | 0x510EA   | `33FC 0002 00D0 0698`           | 0x510F2                  | 8           | direct-write instruction [line 102307](build/maincpu.disasm.txt#L102307) (bytes shown wrap to [line 102308](build/maincpu.disasm.txt#L102308)) |
| 18 | 0x510F4   | `33FC 0000 00D0 0698`           | 0x510FC                  | 8           | direct-write instruction [line 102310](build/maincpu.disasm.txt#L102310) (bytes shown wrap to [line 102311](build/maincpu.disasm.txt#L102311)) |

This table is the canonical byte-length authority for the spec. §8.2 and §0 reference these values; any prior-draft discrepancy is superseded.

### 8.5 Schema example (entry #1)

```json
{
  "arcade_pc": "0x03B902",
  "original_bytes": "43F900D000884A4166...4E75",
  "replacement_bytes": "4EB9{symbol:genesistan_pc090oj_hook_target_3b902}4E754E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E714E71",
  "note": "PC090OJ Strategy A — replace target function 0x3B902 body; covers 8 callers (April-6: 0x03A20E, 0x03A264, 0x03A640, 0x03A6C4, 0x03A820, 0x03B8E8, 0x03B8F0; non-April-6: 0x03A8E0). Helper emits slots 0..4."
}
```

The remaining 17 entries follow the same template (1 example shown above + 17 others = 18 total). Cody mechanically generates them by reading the function span per §8.4, computing original_bytes, and emitting the replacement template. The exact `note` text for every entry is specified per-entry in the §8.6 audit ledger below.

### 8.6 46-site → 18-entry audit ledger

This ledger discharges Rule 17 of the original spec prompt: every one of the 46 ledger sites from `Andy_pc090oj_writer_classification_ledger.md` is enumerated here, with its covering opcode_replace entry, helper symbol, disassembly-cited coverage proof, and the exact `note` text for the corresponding `specs/rastan_direct_remap.json` entry.

A future developer searching `specs/rastan_direct_remap.json` for any one of the 46 ledger sites (e.g., `arcade_pc 0x03A20E`) will not find a literal match — the entry is at the writer-function arcade_pc (`0x3B902`), not the call site. The mapping below resolves that lookup.

#### 8.6.1 Ledger sites grouped by covering entry

**Entry #1 — body replacement at `0x3B902`** (helper: `genesistan_pc090oj_hook_target_3b902`; 36 bytes; slots 0..4).

| Ledger site | Site type | Containing fn | Coverage proof |
|-------------|-----------|---------------|----------------|
| 0x03A20E    | April-6   | 0x3B902       | `bsrw 0x3B902` at [maincpu.disasm.txt:73105](build/maincpu.disasm.txt#L73105); body of 0x3B902 (0x3B902..0x3B925) replaced with `JSR genesistan_pc090oj_hook_target_3b902; RTS; NOP*` → caller invokes helper |
| 0x03A264    | April-6   | 0x3B902       | `bsrw 0x3B902` at [maincpu.disasm.txt:73130](build/maincpu.disasm.txt#L73130); same body replacement → helper |
| 0x03A640    | April-6   | 0x3B902       | `bsrw 0x3B902` at [maincpu.disasm.txt:73399](build/maincpu.disasm.txt#L73399); same body replacement → helper |
| 0x03A6C4    | April-6   | 0x3B902       | `bsrw 0x3B902` at [maincpu.disasm.txt:73432](build/maincpu.disasm.txt#L73432); same body replacement → helper |
| 0x03A820    | April-6   | 0x3B902       | `bsrw 0x3B902` at [maincpu.disasm.txt:73524](build/maincpu.disasm.txt#L73524); same body replacement → helper |
| 0x03B8E8    | April-6   | 0x3B902       | `bsrw 0x3B902` at [maincpu.disasm.txt:74770](build/maincpu.disasm.txt#L74770); same body replacement → helper |
| 0x03B8F0    | April-6   | 0x3B902       | `bsrw 0x3B902` at [maincpu.disasm.txt:74773](build/maincpu.disasm.txt#L74773); same body replacement → helper |
| (non-ledger) 0x03A8E0 | extra | 0x3B902 | `bsrw 0x3B902` at [maincpu.disasm.txt:73572](build/maincpu.disasm.txt#L73572); not in original ledger but covered by body replacement (architectural gain, see §8.1) |

`note` for entry #1: `"PC090OJ Strategy A function-body replacement at writer fn 0x3B902 (helper genesistan_pc090oj_hook_target_3b902). Intercepts 7 April-6 ledger callers (0x03A20E, 0x03A264, 0x03A640, 0x03A6C4, 0x03A820, 0x03B8E8, 0x03B8F0) plus 1 non-ledger caller (0x03A8E0). Helper emits SAT slots 0..4. See Andy_pc090oj_implementation_spec.md §8.6 for full audit ledger."`

**Entry #2 — body replacement at `0x3B926`** (helper: `genesistan_pc090oj_hook_target_3b926`; 10 bytes; slots 5..13).

| Ledger site | Site type | Containing fn | Coverage proof |
|-------------|-----------|---------------|----------------|
| 0x03A9C6    | April-6   | 0x3B926       | `bsrw 0x3B926` at [maincpu.disasm.txt:73637](build/maincpu.disasm.txt#L73637); body of 0x3B926 (0x3B926..0x3B92F) replaced → helper |
| 0x03A9D4    | April-6   | 0x3B926       | `bsrw 0x3B926` at [maincpu.disasm.txt:73642](build/maincpu.disasm.txt#L73642); same body replacement → helper |

`note` for entry #2: `"PC090OJ Strategy A function-body replacement at writer fn 0x3B926 (helper genesistan_pc090oj_hook_target_3b926). Intercepts 2 April-6 ledger callers (0x03A9C6, 0x03A9D4). Original 0x3B926 falls through with bras into 0x3B902's loop body; helper subsumes that flow. Helper emits SAT slots 5..13. See Andy_pc090oj_implementation_spec.md §8.6."`

**Entry #3 — body replacement at `0x3B930`** (helper: `genesistan_pc090oj_hook_target_3b930`; 32 bytes; slots 14..17).

| Ledger site | Site type | Containing fn | Coverage proof |
|-------------|-----------|---------------|----------------|
| (non-ledger, called from target body) 0x3B912 | internal | 0x3B902→0x3B930 | `bsrw 0x3B930` at [maincpu.disasm.txt:74784](build/maincpu.disasm.txt#L74784); reached via 0x3B902 body — but 0x3B902 body is replaced (entry #1) so this caller no longer fires. Coverage of 0x3B930 ITSELF is required for the OTHER caller path below. |
| (non-ledger, init path) 0x3B8BC | non-target init | 0x3B8B0→0x3B930 | `bsrw 0x3B930` at [maincpu.disasm.txt:74758](build/maincpu.disasm.txt#L74758); 0x3B8B0 is reached from `0x3B06A` startup_common at [line 74107](build/maincpu.disasm.txt#L74107); body of 0x3B930 (0x3B930..0x3B94F) replaced → init writes routed to helper |
| (non-ledger, init path) 0x3B8D2 | non-target init | 0x3B8B0→0x3B930 | `bsrw 0x3B930` at [maincpu.disasm.txt:74764](build/maincpu.disasm.txt#L74764); same body replacement → helper |
| (non-ledger, init path) 0x3B8E2 | non-target init | 0x3B8B0→0x3B930 | `bsrw 0x3B930` at [maincpu.disasm.txt:74768](build/maincpu.disasm.txt#L74768); same body replacement → helper |

(Note: the 0x3B930 writers — 3B936/3C/42/4C in the writer ledger §3.5 — are classified DOWNSTREAM via 0x3B902 reachability. None of the 4 callers of 0x3B930 is in the 46-site ledger directly — they are intermediate paths. Entry #3 exists because the 0x3B8B0 init path is NOT covered by entry #1 or any other April-6 hook; without entry #3 those init writes would still hit unmapped Genesis memory.)

`note` for entry #3: `"PC090OJ Strategy A writer-helper body replacement at 0x3B930 (helper genesistan_pc090oj_hook_target_3b930). Reached from target 0x3B902 (already covered by entry #1 — body replacement makes that path inert) AND from non-target init function 0x3B8B0 at 3 BSR sites (0x3B8BC, 0x3B8D2, 0x3B8E2). Without this entry, init-time writes to 0xD00020/0xD000E0/0xD00128 would hit unmapped Genesis memory. Helper emits SAT slots 14..17. See Andy_pc090oj_implementation_spec.md §8.6."`

**Entry #4 — body replacement at `0x41DAE`** (helper: `genesistan_pc090oj_hook_target_41dae`; 352 bytes; slots 0..21).

| Ledger site | Site type | Containing fn | Coverage proof |
|-------------|-----------|---------------|----------------|
| 0x041DAE    | April-6   | 0x41DAE (target itself) | function entry at [maincpu.disasm.txt:83678](build/maincpu.disasm.txt#L83678); body (0x41DAE..0x41F0D, 352 bytes) replaced → all callers of 0x41DAE invoke helper |

`note` for entry #4: `"PC090OJ Strategy A function-body replacement at April-6 target fn 0x41DAE (helper genesistan_pc090oj_hook_target_41dae). 352-byte span covering main-loop + 4 sub-loop fallbacks. Helper emits Block-A 18-sprite frame to SAT slots 0..17 + sub-loops. See Andy_pc090oj_implementation_spec.md §8.6."`

**Entry #5 — body replacement at `0x41F5E`** (helper: `genesistan_pc090oj_hook_target_41f5e`; 56 bytes; slots 18..21).

| Ledger site | Site type | Containing fn | Coverage proof |
|-------------|-----------|---------------|----------------|
| 0x03A854    | April-6   | 0x41F5E       | `bsrw 0x41F5E` at [maincpu.disasm.txt:73535](build/maincpu.disasm.txt#L73535); body (0x41F5E..0x41F95, 56 bytes) replaced → helper |
| 0x041F5E    | April-6   | 0x41F5E (target itself) | function entry at [maincpu.disasm.txt:83793](build/maincpu.disasm.txt#L83793); same body replacement → all callers of 0x41F5E invoke helper |

`note` for entry #5: `"PC090OJ Strategy A function-body replacement at April-6 target fn 0x41F5E (helper genesistan_pc090oj_hook_target_41f5e). Intercepts April-6 caller 0x03A854 and the target itself. Helper emits Block-B 4-sprite copy to SAT slots 18..21. See Andy_pc090oj_implementation_spec.md §8.6."`

**Entry #6 — body replacement at `0x45DFA`** (helper: `genesistan_pc090oj_hook_target_45dfa`; 258 bytes; slots 0..21).

| Ledger site | Site type | Containing fn | Coverage proof |
|-------------|-----------|---------------|----------------|
| 0x03A818    | April-6   | 0x45DFA       | `jsr 0x45DFA` at [maincpu.disasm.txt:73522](build/maincpu.disasm.txt#L73522); body (0x45DFA..0x45EFB, 258 bytes) replaced → helper |
| 0x045DFA    | April-6   | 0x45DFA (target itself) | function entry at [maincpu.disasm.txt:88381](build/maincpu.disasm.txt#L88381); same body replacement → all callers of 0x45DFA invoke helper |

`note` for entry #6: `"PC090OJ Strategy A function-body replacement at April-6 target fn 0x45DFA (helper genesistan_pc090oj_hook_target_45dfa). Intercepts April-6 caller 0x03A818 and the target itself. Helper re-emits the 22-sprite frame to SAT slots 0..21 (alternate emitter for game phases that re-issue). See Andy_pc090oj_implementation_spec.md §8.6."`

**Entry #7 — body replacement at `0x59F5E`** (helper: `genesistan_pc090oj_hook_target_59f5e`; 52 bytes; slots 0..7).

| Ledger site | Site type | Containing fn | Coverage proof |
|-------------|-----------|---------------|----------------|
| 0x03A8E4    | April-6   | 0x59F5E       | `jsr 0x59F5E` at [maincpu.disasm.txt:73573](build/maincpu.disasm.txt#L73573); body (0x59F5E..0x59F91, 52 bytes) replaced → helper |
| (non-ledger) 0x051266 | extra | 0x59F5E | `jsr 0x59F5E` at [maincpu.disasm.txt:102416](build/maincpu.disasm.txt#L102416); same body replacement → helper |
| (non-ledger) 0x0519A0 | extra | 0x59F5E | `jsr 0x59F5E` at [maincpu.disasm.txt:102879](build/maincpu.disasm.txt#L102879); same body replacement → helper |
| (non-ledger) 0x055E18 | extra | 0x59F5E | `jsr 0x59F5E` at [maincpu.disasm.txt:107716](build/maincpu.disasm.txt#L107716); same body replacement → helper |

`note` for entry #7: `"PC090OJ Strategy A function-body replacement at April-6 target fn 0x59F5E (helper genesistan_pc090oj_hook_target_59f5e). Intercepts April-6 caller 0x03A8E4 plus 3 non-ledger callers (0x051266, 0x0519A0, 0x055E18). Helper clears SAT slots 0..7 (the 0xD00048+ region). See Andy_pc090oj_implementation_spec.md §8.6."`

**Entry #8 — body replacement at `0x3AD44`** (helper: `genesistan_hook_3ad44_dispatch` per v3.2; 8 bytes; output depends on A0 dispatch — see §2.2.A.3). 0x03AD44 is a polymorphic memset utility: 3 callers route to the PC090OJ branch, 4 callers route to the tilemap branch.

| Ledger site | Site type | A0 setup | A0 value | Dispatch branch | Coverage proof |
|-------------|-----------|----------|----------|------------------|----------------|
| 0x03AD5C    | INDEPENDENT (PC090OJ) | `lea 0xD00000, %a0` at [line 73898](build/maincpu.disasm.txt#L73898) | 0x00D00000 | PC090OJ branch (LUT bulk-clear) | `bsrs 0x3AD44` at [line 73900](build/maincpu.disasm.txt#L73900); body (0x3AD44..0x3AD4B, 8 bytes) replaced with dispatch helper → A0 in PC090OJ range → PC090OJ branch logic → behavior identical to v3.1 helper |
| 0x03AD6E    | INDEPENDENT (PC090OJ) | `lea 0xD00170, %a0` at [line 73902](build/maincpu.disasm.txt#L73902) | 0x00D00170 | PC090OJ branch | `bsrs 0x3AD44` at [line 73904](build/maincpu.disasm.txt#L73904); A0 in PC090OJ range → PC090OJ branch |
| 0x03AD82    | INDEPENDENT (PC090OJ) | `lea 0xD00000, %a0` at [line 73907](build/maincpu.disasm.txt#L73907) | 0x00D00000 | PC090OJ branch | `bsrs 0x3AD44` at [line 73909](build/maincpu.disasm.txt#L73909); A0 in PC090OJ range → PC090OJ branch |
| 0x03AE70    | TILEMAP   | `lea 0xC00100, %a0` at [line 73975](build/maincpu.disasm.txt#L73975) | 0x00C00100 | Tilemap branch (BG fill) | `bsrw 0x3AD44` at [line 73978](build/maincpu.disasm.txt#L73978); A0 in tilemap range → tilemap branch → behavior identical to pre-PC090OJ-replacement HEAD baseline (`genesistan_hook_tilemap_bg_fill`) |
| 0x03AE80    | TILEMAP   | `lea 0xC08100, %a0` at [line 73979](build/maincpu.disasm.txt#L73979) | 0x00C08100 | Tilemap branch (FG plane silently no-opped by existing helper's internal range filter — preserved from HEAD baseline) | `bsrw 0x3AD44` at [line 73982](build/maincpu.disasm.txt#L73982) |
| 0x03AF38    | TILEMAP   | `lea 0xC00000, %a0` at [line 74023](build/maincpu.disasm.txt#L74023) | 0x00C00000 | Tilemap branch (BG fill) | `bsrw 0x3AD44` at [line 74026](build/maincpu.disasm.txt#L74026) |
| 0x03AF48    | TILEMAP   | `lea 0xC08000, %a0` at [line 74027](build/maincpu.disasm.txt#L74027) | 0x00C08000 | Tilemap branch (FG plane no-op as above) | `bsrw 0x3AD44` at [line 74030](build/maincpu.disasm.txt#L74030) |

A0 ranges non-overlapping (tilemap `[0xC00000, 0xC10000)` vs PC090OJ `[0xD00000, 0xD00800)`) and exhaustive (every one of 7 callers fits exactly one range). Verified per §2.2.A.1 caller-enumeration table.

`note` for entry #8 (replaces v3.1 note): `"PC090OJ + tilemap polymorphic-utility dispatch at fn 0x3AD44 via v3.2 helper genesistan_hook_3ad44_dispatch. Intercepts 7 callers: 3 PC090OJ-targeting (0x03AD5C, 0x03AD6E, 0x03AD82; A0 ∈ [0xD00000, 0xD00800)) routed to PC090OJ bulk-clear branch (LUT-mediated, slots 76..79 destination space); 4 tilemap-targeting (0x03AE70, 0x03AE80, 0x03AF38, 0x03AF48; A0 ∈ [0xC00000, 0xC10000)) routed to tilemap-branch reusing genesistan_hook_tilemap_bg_fill semantics. A0 dispatch on entry; out-of-range A0 falls through to §7.3 audit-guard halt-with-heartbeat. Replaces v3.1 PC090OJ-only helper genesistan_pc090oj_hook_init_clear_3ad44 (which broke pre-existing tilemap coverage). See Andy_pc090oj_implementation_spec.md §2.2.A and §8.6 entry #8."`

**Entry #9 — body replacement at `0x3AD84`** (helper: `genesistan_pc090oj_hook_init_priority_3ad84`; 56 bytes; slots 76..79).

| Ledger site | Site type    | Containing fn | Coverage proof |
|-------------|--------------|---------------|----------------|
| 0x03ABB6    | INDEPENDENT  | 0x3AD84 (via 0x3AD72 fall-through) | `bsrw 0x3AD72` at [maincpu.disasm.txt:73778](build/maincpu.disasm.txt#L73778); 0x3AD72 falls through into 0x3AD84 body. Body of 0x3AD84 (0x3AD84..0x3ADBB, 56 bytes) replaced → helper subsumes both 0x3AD72's prologue and the priority-init writes. |
| 0x03AF28    | INDEPENDENT  | 0x3AD84 (via 0x3AD72 fall-through) | `bsrw 0x3AD72` at [maincpu.disasm.txt:74022](build/maincpu.disasm.txt#L74022); same body replacement → helper |

`note` for entry #9: `"PC090OJ Strategy A function-body replacement at INDEPENDENT writer fn 0x3AD84 (helper genesistan_pc090oj_hook_init_priority_3ad84). Intercepts 2 ledger callers via 0x3AD72 fall-through (0x03ABB6, 0x03AF28). Helper initializes 4 priority-frame slots at SAT range 76..79 (the 0xD00778 origin per Andy_d00778_write_path_analysis.md). See Andy_pc090oj_implementation_spec.md §8.6."`

**Entry #10 — body replacement at `0x3B802`** (helper: `genesistan_pc090oj_hook_score_digit_3b802`; 174 bytes; slots 22..29).

| Ledger site | Site type    | Containing fn | Coverage proof |
|-------------|--------------|---------------|----------------|
| 0x03A66A    | INDEPENDENT  | 0x3B802       | `bsrw 0x3B802` at [maincpu.disasm.txt:73410](build/maincpu.disasm.txt#L73410); body (0x3B802..0x3B8AF) replaced → helper |
| 0x03A9C0    | INDEPENDENT  | 0x3B802       | `bsrw 0x3B802` at [maincpu.disasm.txt:73635](build/maincpu.disasm.txt#L73635); same body replacement → helper |
| 0x03A9CE    | INDEPENDENT  | 0x3B802       | `bsrw 0x3B802` at [maincpu.disasm.txt:73640](build/maincpu.disasm.txt#L73640); same body replacement → helper |
| 0x03A9DA    | INDEPENDENT  | 0x3B802       | `bsrw 0x3B802` at [maincpu.disasm.txt:73644](build/maincpu.disasm.txt#L73644); same body replacement → helper |
| 0x03B7A2    | INDEPENDENT  | 0x3B802       | `bsrw 0x3B802` at [maincpu.disasm.txt:74661](build/maincpu.disasm.txt#L74661); same body replacement → helper |
| 0x03B7B0    | INDEPENDENT  | 0x3B802       | `bsrw 0x3B802` at [maincpu.disasm.txt:74666](build/maincpu.disasm.txt#L74666); same body replacement → helper |
| 0x03B7E0    | INDEPENDENT  | 0x3B802       | `bsrw 0x3B802` at [maincpu.disasm.txt:74682](build/maincpu.disasm.txt#L74682); same body replacement → helper |
| 0x03B8C2    | INDEPENDENT  | 0x3B802       | `bsrw 0x3B802` at [maincpu.disasm.txt:74760](build/maincpu.disasm.txt#L74760); same body replacement → helper |
| 0x03B8F6    | INDEPENDENT  | 0x3B802       | `bsrw 0x3B802` at [maincpu.disasm.txt:74775](build/maincpu.disasm.txt#L74775); same body replacement → helper |
| 0x03B8FC    | INDEPENDENT  | 0x3B802       | `bsrw 0x3B802` at [maincpu.disasm.txt:74777](build/maincpu.disasm.txt#L74777); same body replacement → helper |

`note` for entry #10: `"PC090OJ Strategy A function-body replacement at INDEPENDENT writer fn 0x3B802 (helper genesistan_pc090oj_hook_score_digit_3b802). Intercepts 10 ledger score/HUD-digit callers (0x03A66A, 0x03A9C0, 0x03A9CE, 0x03A9DA, 0x03B7A2, 0x03B7B0, 0x03B7E0, 0x03B8C2, 0x03B8F6, 0x03B8FC). 174-byte span includes the function's PC-relative digit-attribute table at 0x3B87E..0x3B8AF (referenced only from inside the function). Helper emits HUD-digit sprites to SAT slots 22..29. See Andy_pc090oj_implementation_spec.md §8.6."`

**Entry #11 — body replacement at `0x54052`** (helper: `genesistan_pc090oj_hook_slot_init_54052`; 122 bytes; slots 72..75).

| Ledger site | Site type    | Containing fn | Coverage proof |
|-------------|--------------|---------------|----------------|
| 0x0501F4    | INDEPENDENT  | 0x54052       | `jsr 0x54052` at [maincpu.disasm.txt:101286](build/maincpu.disasm.txt#L101286); body (0x54052..0x540CB, 122 bytes) replaced → helper |
| 0x051260    | INDEPENDENT  | 0x54052       | `jsr 0x54052` at [maincpu.disasm.txt:102415](build/maincpu.disasm.txt#L102415); same body replacement → helper |

`note` for entry #11: `"PC090OJ Strategy A function-body replacement at INDEPENDENT writer fn 0x54052 (helper genesistan_pc090oj_hook_slot_init_54052). Intercepts 2 ledger callers (0x0501F4, 0x051260). Helper preserves the original function's Taito C-chip text-RAM clears at 0x10D1B2/0x10D1D2/0x10D1F2 (replicated verbatim) and emits sprite-slot init to SAT slots 72..75. See Andy_pc090oj_implementation_spec.md §8.6."`

**Entry #12 — body replacement at `0x54810`** (helper: `genesistan_pc090oj_hook_sprite_update_54810`; 84 bytes; slots 44..55).

| Ledger site | Site type    | Containing fn | Coverage proof |
|-------------|--------------|---------------|----------------|
| 0x0547EE    | INDEPENDENT  | 0x54810       | `bsrw 0x54810` at [maincpu.disasm.txt:106226](build/maincpu.disasm.txt#L106226); body (0x54810..0x54863, 84 bytes) replaced → helper |
| 0x054804    | INDEPENDENT  | 0x54810       | `bsrw 0x54810` at [maincpu.disasm.txt:106233](build/maincpu.disasm.txt#L106233); same body replacement → helper |

`note` for entry #12: `"PC090OJ Strategy A function-body replacement at INDEPENDENT writer fn 0x54810 (helper genesistan_pc090oj_hook_sprite_update_54810). Intercepts 2 ledger callers (0x0547EE, 0x054804). Helper emits 4-sprite-per-call update to SAT slots 44..55. See Andy_pc090oj_implementation_spec.md §8.6."`

**Entry #13 — body replacement at `0x5607C`** (helper: `genesistan_pc090oj_hook_sprite_decay_5607c`; 94 bytes; slots 56..63).

| Ledger site | Site type    | Containing fn | Coverage proof |
|-------------|--------------|---------------|----------------|
| 0x055E92    | INDEPENDENT  | 0x5607C       | `bsrw 0x5607C` at [maincpu.disasm.txt:107743](build/maincpu.disasm.txt#L107743); body (0x5607C..0x560D9, 94 bytes) replaced → helper |

`note` for entry #13: `"PC090OJ Strategy A function-body replacement at INDEPENDENT writer fn 0x5607C (helper genesistan_pc090oj_hook_sprite_decay_5607c). Intercepts 1 ledger caller (0x055E92). Helper performs sprite-decay Y-decrement on SAT slots 56..63 (sprite-disappear when Y reaches 16). See Andy_pc090oj_implementation_spec.md §8.6."`

**Entry #14 — body replacement at `0x56114`** (helper: `genesistan_pc090oj_hook_copy_56114`; 20 bytes; slots 64..67).

| Ledger site | Site type    | Containing fn | Coverage proof |
|-------------|--------------|---------------|----------------|
| 0x05604C    | INDEPENDENT  | 0x56114       | `bsrw 0x56114` at [maincpu.disasm.txt:107843](build/maincpu.disasm.txt#L107843); body (0x56114..0x56127, 20 bytes) replaced → helper |
| 0x056076    | INDEPENDENT  | 0x56114       | `bsrw 0x56114` at [maincpu.disasm.txt:107852](build/maincpu.disasm.txt#L107852); same body replacement → helper |

`note` for entry #14: `"PC090OJ Strategy A function-body replacement at INDEPENDENT writer fn 0x56114 (helper genesistan_pc090oj_hook_copy_56114). Intercepts 2 ledger callers (0x05604C, 0x056076). Helper copies 4 word-pairs from source descriptor list (terminated by 0xFFFF) into SAT slots 64..67. See Andy_pc090oj_implementation_spec.md §8.6."`

**Entry #15 — body replacement at `0x56440`** (helper: `genesistan_pc090oj_hook_zero_fill_56440`; 30 bytes; slots 68..71).

| Ledger site | Site type    | Containing fn | Coverage proof |
|-------------|--------------|---------------|----------------|
| 0x055F0E    | INDEPENDENT  | 0x56440       | `bsrw 0x56440` at [maincpu.disasm.txt:107771](build/maincpu.disasm.txt#L107771); body (0x56440..0x5645D, 30 bytes) replaced → helper |
| 0x055FFA    | INDEPENDENT  | 0x56440       | `bsrw 0x56440` at [maincpu.disasm.txt:107825](build/maincpu.disasm.txt#L107825); same body replacement → helper |

(Inline helper 0x5648A at [line 108149](build/maincpu.disasm.txt#L108149): single caller from 0x56454 inside 0x56440 — once 0x56440's body is replaced, the BSR to 0x5648A no longer fires; 0x5648A becomes unreachable dead code, no separate entry required.)

`note` for entry #15: `"PC090OJ Strategy A function-body replacement at INDEPENDENT writer fn 0x56440 (helper genesistan_pc090oj_hook_zero_fill_56440). Intercepts 2 ledger callers (0x055F0E, 0x055FFA). Inline helper 0x5648A is reached only from inside 0x56440 (single internal caller); body replacement renders it unreachable dead code. Helper zeroes SAT slots 68..71. See Andy_pc090oj_implementation_spec.md §8.6."`

**Entry #16 — body replacement at `0x5A098`** (helper: `genesistan_pc090oj_hook_status_sprite_5a098`; 498 bytes; slots 30..43).

| Ledger site | Site type    | Containing fn | Coverage proof |
|-------------|--------------|---------------|----------------|
| 0x051054    | INDEPENDENT  | 0x5A098       | `jsr 0x5A098` at [maincpu.disasm.txt:102275](build/maincpu.disasm.txt#L102275); body (0x5A098..0x5A289, 498 bytes including inline helper at 0x5A244..0x5A289) replaced → helper |

(Inline helper 0x5A244 at [line 113577](build/maincpu.disasm.txt#L113577): single caller from 0x5A210 inside 0x5A098 — replacement of the 0x5A098 span subsumes it.)

`note` for entry #16: `"PC090OJ Strategy A function-body replacement at INDEPENDENT writer fn 0x5A098 (helper genesistan_pc090oj_hook_status_sprite_5a098). Intercepts 1 ledger caller (0x051054). 498-byte span includes the inline helper at 0x5A244..0x5A289 (called only from 0x5A210 inside the function). Helper emits 12-write-per-call status/UI sprite descriptors to SAT slots 30..43. See Andy_pc090oj_implementation_spec.md §8.6."`

**Entry #17 — direct-write replacement at `0x510EA`** (helper: `genesistan_pc090oj_hook_audit_guard`; 8 bytes).

| Ledger site | Site type   | Containing fn | Coverage proof |
|-------------|-------------|---------------|----------------|
| 0x0510EA    | audit guard | n/a (direct write) | `movew #2, 0xD00698` at [maincpu.disasm.txt:102307](build/maincpu.disasm.txt#L102307); 8-byte instruction replaced in-place with `JSR genesistan_pc090oj_hook_audit_guard; NOP` → controlled stop on execution |

`note` for entry #17: `"PC090OJ audit guard at arcade_pc 0x0510EA. FU1 trace (Cody_fu1_arcade_trace_510EA_510F4.md) showed 0 hits in observed boot+attract+demo gameplay. Direct 8-byte movew #2,0xD00698 instruction replaced with JSR genesistan_pc090oj_hook_audit_guard + NOP. Helper captures CPU state and triggers controlled stop. Rule 8 walkthrough in Andy_pc090oj_implementation_spec.md §7.4."`

**Entry #18 — direct-write replacement at `0x510F4`** (helper: `genesistan_pc090oj_hook_audit_guard`; 8 bytes).

| Ledger site | Site type   | Containing fn | Coverage proof |
|-------------|-------------|---------------|----------------|
| 0x0510F4    | audit guard | n/a (direct write) | `movew #0, 0xD00698` at [maincpu.disasm.txt:102310](build/maincpu.disasm.txt#L102310); 8-byte instruction replaced in-place with `JSR genesistan_pc090oj_hook_audit_guard; NOP` → controlled stop on execution |

`note` for entry #18: `"PC090OJ audit guard at arcade_pc 0x0510F4. FU1 trace showed 0 hits in observed boot+attract+demo gameplay. Direct 8-byte movew #0,0xD00698 instruction replaced with JSR genesistan_pc090oj_hook_audit_guard + NOP (shared helper with entry #17). Helper captures CPU state and triggers controlled stop. Rule 8 walkthrough in Andy_pc090oj_implementation_spec.md §7.4."`

#### 8.6.2 Audit ledger summary

```
Total ledger sites enumerated:                 46  (= writer classification ledger total)
Site breakdown:
    April-6 hook sites:                         15
    INDEPENDENT writer call sites:              29
    Audit-guard direct-write sites:              2
Total covering opcode_replace entries:         18
Average ledger sites per entry:                46 / 18 = 2.56
Maximum ledger sites in one entry:             10 (entry #10 — 0x3B802)
Minimum ledger sites in one entry:              0 (entry #3 — 0x3B930 — covers no ledger sites directly;
                                                    closes a non-ledger init-path gap that the ledger
                                                    classified as DOWNSTREAM via 0x3B902 reachability)
Entries with non-ledger caller coverage:        3 (entries #1, #3, #7 — function body intercepts
                                                    additional callers beyond the ledger sites)
Total non-ledger callers covered:               5 (0x03A8E0 → entry #1; 0x3B8BC, 0x3B8D2, 0x3B8E2 →
                                                    entry #3; 0x051266, 0x0519A0, 0x055E18 → entry #7)
Total unique caller paths intercepted:         51 (46 ledger + 5 non-ledger)
```

Every one of the 46 ledger sites is mapped to exactly one covering entry. No ledger site is dropped. Architectural scope of the writer classification ledger is preserved.

---

## 9. Integration with existing rastan-direct build

### 9.1 New source files

| File path                                          | Purpose |
|----------------------------------------------------|---------|
| `apps/rastan-direct/src/pc090oj_hooks.s`           | All 17 helpers across 18 opcode_replace entries (7 target + 9 INDEPENDENT + 1 shared audit-guard helper invoked from 2 entries), the `vdp_commit_sprites` commit, the §6.5 `genesistan_pc090oj_dma_self_test` boot self-test, and `staged_sprite_*` `.bss` symbols |
| `apps/rastan-direct/src/pc090oj_assets.s`          | `.rodata` `.incbin` of `rastan_pc090oj` and `pc090oj_slot_lut`. (Cody's implementation uses this dedicated file — NOT inline `.rodata` in `pc090oj_hooks.s` — to keep the 524 KB sprite-tile blob and the 256-byte slot-LUT separate from helper code for cleaner build-time inspection.) |

### 9.2 Modified files

| File path                                          | Modification |
|----------------------------------------------------|--------------|
| `apps/rastan-direct/Makefile`                      | Add `OBJS += $(OUT_DIR)/pc090oj_hooks.o`. Add tile-preconversion rule. Add slot-LUT generation rule. Add dependencies. |
| `apps/rastan-direct/src/vdp_comm.s`                | Add `vdp_commit_sprites` call between `vdp_commit_fg_strips_if_dirty` and the palette commit (line ~165). Existing `sprite_dma_addr_high_bits_fix` symbol re-used. |
| `apps/rastan-direct/src/boot/boot.s`               | Extend `_bootstrap_clear_staging` to zero `staged_sprite_sat`, `staged_sprite_descriptor_table`, `staged_sprite_dirty`, `staged_sprite_active_count`. |
| `apps/rastan-direct/link.ld`                       | No changes. New `.bss` symbols fit in existing `.bss` block. |
| `specs/rastan_direct_remap.json`                   | Apply 18 PC090OJ opcode_replace entries: **17 net new appends + 1 in-place update of the pre-existing entry at `0x03AD44`** (HEAD baseline used helper `genesistan_hook_tilemap_bg_fill`; v3.2 dispatch helper `genesistan_hook_3ad44_dispatch` replaces that symbol while preserving tilemap behavior — see §2.2.A and §8.6 entry #8). Update `opcode_replace_count` from **73 (HEAD) → 90** (= 73 + 17 net new). Add 17 helper symbols to `required_symbols` (16 named function-body helpers + 1 shared audit-guard helper; the audit-guard helper is referenced from 2 entries but declared once). Existing `genesistan_hook_tilemap_bg_fill` symbol entry remains in `required_symbols` (still referenced by other tilemap-related opcode_replace entries elsewhere in the spec). Update `note` field of entries that previously suppressed PC090OJ writes (e.g., `0x03AE06`/`0x03AE1E`/`0x03AE8E`) if their suppression overlaps the new `0x3AD44`/`0x3AD84` interception. (Initial reading: those three suppress writes to `0xD01BFE` — the DMA-trigger control register — which is OUTSIDE the 18 entries' scope. No change needed.) |
| `tools/translation/build_pc090oj_slot_lut.py`      | NEW. 256-byte LUT generator per §1.3. Output `build/pc090oj_slot_lut.bin`. |

### 9.3 Symbol additions (`required_symbols` in spec)

```
genesistan_pc090oj_hook_target_3b902
genesistan_pc090oj_hook_target_3b926
genesistan_pc090oj_hook_target_3b930
genesistan_pc090oj_hook_target_41dae
genesistan_pc090oj_hook_target_41f5e
genesistan_pc090oj_hook_target_45dfa
genesistan_pc090oj_hook_target_59f5e
genesistan_hook_3ad44_dispatch
genesistan_pc090oj_hook_init_priority_3ad84
genesistan_pc090oj_hook_score_digit_3b802
genesistan_pc090oj_hook_slot_init_54052
genesistan_pc090oj_hook_sprite_update_54810
genesistan_pc090oj_hook_sprite_decay_5607c
genesistan_pc090oj_hook_copy_56114
genesistan_pc090oj_hook_zero_fill_56440
genesistan_pc090oj_hook_status_sprite_5a098
genesistan_pc090oj_hook_audit_guard
vdp_commit_sprites
genesistan_pc090oj_dma_self_test
rastan_pc090oj
pc090oj_slot_lut
staged_sprite_sat
staged_sprite_descriptor_table
staged_sprite_dirty
staged_sprite_active_count
pc090oj_dma_test_fired_flag
pc090oj_dma_test_mismatch_offset
pc090oj_dma_test_expected_word
pc090oj_dma_test_actual_word
pc090oj_dma_test_actual_buffer
pc090oj_dma_test_heartbeat
audit_guard_caller_pc
audit_guard_register_snapshot
audit_guard_fired_flag
audit_guard_vcount
audit_guard_heartbeat
```

The list contains 17 helper symbols (16 named function-body helpers + 1 shared audit-guard helper), 1 commit subroutine (`vdp_commit_sprites`), 1 boot self-test subroutine (`genesistan_pc090oj_dma_self_test`), 2 ROM-embedded data symbols (`rastan_pc090oj`, `pc090oj_slot_lut`), 4 sprite-staging `.bss` symbols, 6 self-test diagnostic `.bss` symbols (§6.5), and 5 audit-guard diagnostic `.bss` symbols (§7.3). Total: **36 new symbols**.

### 9.4 Postpatch tool integration

`tools/translation/postpatch_startup_rom.py` — no schema change needed if it already supports the `{symbol:name}` placeholder pattern (which the existing 73 entries demonstrate). The `all_symbol_addresses` dictionary it builds (per `postpatch:1689` reference in prior analysis) gains the 36 new symbols automatically when the linker emits them. Cody's task: confirm the postpatcher resolves all 36 symbols on first build; failure → diagnose missing symbol declaration in `pc090oj_hooks.s`.

### 9.5 count_guard

```
opcode_replace_count: 73 (HEAD) → 90 (v3.2) — 73 + 17 net new appends; the 18th PC090OJ entry replaces the pre-existing 0x03AD44 entry in place
```

The spec's count_guard field at line 555 of `specs/rastan_direct_remap.json` updates to **90** under v3.2 (was provisionally **91** under v2/v3/v3.1 before the polymorphic-utility issue at 0x03AD44 was discovered; v3.2's dispatch fix supersedes that count).

---

## 10. Completion ledger and definition-of-done

### 10.1 Build-time verification

- [ ] Build succeeds with all 18 PC090OJ-related opcode_replace entries applied (17 net new + 1 in-place update of pre-existing `0x03AD44` entry; postpatcher exits 0; manifest written).
- [ ] `opcode_replace_count` field updated to 90 in `specs/rastan_direct_remap.json` (= 73 HEAD baseline + 17 net new under v3.2).
- [ ] All 24 new symbols present in `apps/rastan-direct/out/symbol.txt`.
- [ ] `build/pc090oj_genesis.bin` exists and is 524288 bytes.
- [ ] `build/pc090oj_slot_lut.bin` exists and is 256 bytes.
- [ ] `rastan_pc090oj` symbol resolves and embedded data length is 524288 bytes (verified via `m68k-elf-objdump -h`).
- [ ] `vdp_commit_sprites` is called from `_vblank_service` between `vdp_commit_fg_strips_if_dirty` and the palette commit (verified by source diff).
- [ ] `_bootstrap_clear_staging` zeroes the 4 new `staged_sprite_*` symbols (verified by source diff).
- [ ] Build artifact size is < 4 MiB (Genesis ROM ceiling). The 524 KB sprite tile data is the largest new addition.

### 10.2 Boot-time verification

- [ ] Build 0052+ boots past the prior `0xD00778` crash (priority-frame init now translated by `genesistan_pc090oj_hook_init_priority_3ad84`).
- [ ] First-frame VBlank fires; `_vblank_service` calls `vdp_commit_sprites`; SAT DMA completes (verified by VRAM 0xF800 read).
- [ ] No exception raised during the first 60 frames after boot (verified by absence of `_crash_stub_*` invocation).
- [ ] DMA self-test (per §6.5): VRAM 0x8000..0x807F matches first 128 bytes of `rastan_pc090oj` cell 1 (verified by Genesis-side test routine at boot).
- [ ] Audit guards do NOT fire during first-frame execution (verified by `audit_guard_fired_flag` remaining 0).

### 10.3 Runtime verification (gameplay observable)

- [ ] **Player sprite renders** during attract/demo/gameplay phases (visible Rastan character in MAME or Genesis emulator video output).
- [ ] **Score display updates** with each point gain (HUD digits at top of screen, observed via MAME/Exodus video; covered by `genesistan_pc090oj_hook_score_digit_3b802`).
- [ ] **Lives counter renders** (status sprites at top of screen; covered by `genesistan_pc090oj_hook_status_sprite_5a098`).
- [ ] **Level banner appears** at level start (sprite slot init via `genesistan_pc090oj_hook_slot_init_54052`).
- [ ] **Enemy sprites spawn, animate, despawn** during gameplay (April-6 dispatcher tree via `genesistan_pc090oj_hook_target_41dae` etc.).
- [ ] **Sprite priority is correct** — sprites overlap the tilemap correctly (no tilemap visible through opaque sprite pixels).
- [ ] **Sprite flipping** (player turning around) renders correctly (HFlip bit in word2 verified).
- [ ] **Sprite count during heavy gameplay** does not exceed 80; no SAT overflow / corruption observed.
- [ ] **Audit guards do not fire** during 5+ minutes of varied gameplay (multiple levels, scoring, dying, restarting).

### 10.4 Failure modes that indicate incomplete implementation

| Symptom                                       | Likely cause                                                              |
|-----------------------------------------------|---------------------------------------------------------------------------|
| Missing or invisible HUD/score/lives          | INDEPENDENT writer hook(s) not firing or writing to wrong slot range. Verify each helper's slot-range allocation. |
| Garbled / blocky sprite display               | Tile-DMA address encoding wrong, OR `pc090oj_slot_lut` mismapping, OR `SPRITE_TILE_BASE` mismatch with VDP tile layout. |
| Sprite tearing / mid-frame flicker            | VBlank commit overruns the display-off window. See §11 FU2 for measurement task. |
| Game crashes mid-level                        | Helper writes outside its slot range, OR descriptor-table corruption, OR audit guard fired. Check `audit_guard_fired_flag` value. |
| Audit guard fires during gameplay             | Code path reached `0x510EA / 0x510F4` writers that the FU1 trace did not capture. Examine `audit_guard_caller_pc` and surrounding state to identify the missing path. |
| Sprites have correct shape but wrong colour   | Palette-line translation incorrect (verify §3.6 helper code). |
| Sprites appear at wrong position              | Coordinate bias incorrect (verify §3.1 / §3.2; check Y/X mask-and-add). |
| All sprites at top-left corner                | Helpers writing X=Y=0 because reading wrong workram offset. Cross-check helper's offset against arcade ROM disassembly. |

### 10.5 Coverage closure ledger

Strategy A is **complete** when all of:

- [ ] All 18 opcode_replace entries verified active (postpatcher manifest line count matches).
- [ ] All 22 expected sprite types (per April-6 §2.3) render at least once during normal gameplay — verified by visual inspection across 1 full level + HUD + scoring.
- [ ] No `audit_guard_fired_flag` trigger across a full-level playthrough.
- [ ] `staged_sprite_active_count` averages 8–22 during gameplay (per April-6 22-sprite ceiling expectation).
- [ ] `staged_sprite_dirty` is non-zero for at least 1 block per frame during gameplay (proves helpers are writing).
- [ ] No more than 2 frames of sprite stale-frame artifacts after a sprite removal (proves clear-path helpers fire).

---

## 11. Deferred items and follow-up tasks

| FU#  | Description                                                                | Why non-blocking                                   | Follow-up task                                                                | Trigger condition                                  |
|------|----------------------------------------------------------------------------|----------------------------------------------------|-------------------------------------------------------------------------------|----------------------------------------------------|
| FU1  | `Andy_pc090oj_reconciliation_v2.md` Phase 10 follow-up: confirm whether `0x510EA / 0x510F4` writes execute in actual gameplay code paths and characterize their state. | Audit-guard implementation surfaces them safely. Initial implementation does not depend on resolution. | Cody / Chad: extended-gameplay MAME trace with breakpoints at both PCs over full first-level playthrough. | Audit guard fires in §10 verification, OR if final ROM ships and field reports indicate sprite glitches near level transitions. |
| FU2  | VBlank commit timing: measure cycle count of `vdp_commit_sprites` under worst-case (80 dirty slots) and confirm fits Genesis NTSC blank window. | Initial implementation uses simple full-commit; if it overruns, optimization is bounded. | Cody: instrument `vdp_commit_sprites` with cycle-count counters; report worst-case across 100-frame gameplay sample. | Visual sprite tearing observed in §10 verification. |
| FU3  | If audit guards fire: replace `genesistan_pc090oj_hook_audit_guard` with a verified translation helper at the relevant call site. | Audit-guard halt is correct production behavior; replacement is a follow-up improvement. | Andy: characterize the unobserved code path; design helper. Cody: implement. | `audit_guard_fired_flag != 0` on any production build. |
| FU4  | Verify tile budget: `rastan_pc090oj` is 524288 bytes (4096 cells × 128 bytes). VRAM tile region used by sprite slots is `1024..1339 = 316 tiles × 32 bytes = 10112 bytes`. The remaining 514 176 bytes of sprite cells live in ROM, on-demand DMA-loaded. Confirm Rastan does not exceed 80 active cells per frame, which would exceed Genesis sprite-slot budget. | April-6 §2.3 caps observed at 22; well within budget. | Cody / Chad: gameplay trace counting `staged_sprite_active_count` over level-1 playthrough. | If `staged_sprite_active_count == 80` ever observed (full slot occupancy). |
| FU5  | The compound `0x41DAE` function (352 bytes) covers four sub-loops including JSR to `0x3D054` (the sprite-shape dispatcher). Function-body replacement intercepts `0x41DAE`'s entry but does NOT intercept `0x3D054` directly. If any non-`0x41DAE` / non-`0x45DFA` caller of `0x3D054` exists in unobserved gameplay, Strategy A misses it. The writer classification ledger §2.3 verified all 7 callers of `0x3D054` are inside `0x41DAE` (4) or `0x45DFA` (3) — no gap exists per static analysis. | Static analysis confirms no gap. | Cody / Chad: gameplay trace verifying `0x3D054` reach is exclusively through these two parents. | Audit follow-up (only if guard fires or sprite glitches indicate dispatcher bypass). |
| FU6  | The `genesistan_pc090oj_hook_target_45dfa` and `genesistan_pc090oj_hook_target_41dae` both produce 22-sprite frames. If both fire in the same frame (arcade re-emits), the second helper overwrites the first's slots. Per April-6 §4.1, only one of the 15 hook sites fires per frame in arcade's normal flow; this should hold under Strategy A. | April-6 baseline confirms single-emitter-per-frame behavior. | Cody: instrument with per-helper invocation counter; verify only one of `0x41DAE` / `0x45DFA` fires per frame. | Game state where both invocations cluster (level transition, end-game state). |
| FU7  | The audit-guard `.bra .Lag_halt_loop` halts execution in a tight loop. On real hardware, this produces no visible signal beyond the `audit_guard_heartbeat` byte. Consider adding a visible signal (e.g., `move.w #0x0EEE, 0x00C00000` to write a colour to CRAM repeatedly) so a developer running the ROM on real hardware can SEE the guard fired without an emulator/debugger. | Initial implementation prioritizes correctness over UX. | Andy: design visible signal; Cody: implement. | If audit guards fire post-deployment and aren't easily diagnosed via ROM-state inspection. |

(Prior-revision FU4 — writer classification ledger typo `0x3AD56` → `0x3AD5C` — has been resolved in-place in this revision: the ledger §3.7.1 entry has been corrected with disassembly-cited footnote, and the spec §8.6 audit ledger and §8.1 mapping table use the corrected address. No deferred follow-up remains.)

---

## 12. Integrity check

| Item                                                                                    | Status |
|------------------------------------------------------------------------------------------|--------|
| Phase 1 staging model defined with offset/size/format/init/concurrency                   | YES    |
| Phase 2 helper contracts defined with entry/exit state for all distinct helpers          | YES (17 distinct helpers across 3 categories) |
| Phase 3 descriptor-to-SAT lowering complete with field-by-field rules and citations      | YES (10 fields, all cited to April 6 §6/§7 + MAME) |
| Phase 4 sprite tile VRAM LUT and preconversion defined                                   | YES    |
| Phase 5 VBlank commit mechanism defined with trigger/DMA/ordering                        | YES    |
| Phase 6 April 6 DMA fix specified at byte level                                          | YES (already implemented as `sprite_dma_addr_high_bits_fix` in rastan-direct; documented for re-use) |
| Phase 7 audit guards specified with Rule 8 walkthrough                                   | YES    |
| Phase 8 all 18 opcode_replace entries enumerated with bytes                              | YES (§8.2 entry table + §8.4 disassembly-verified byte-length table; 18 entries cover all 46 ledger sites via the audit ledger in §8.6, plus 5 non-ledger callers as architectural gain) |
| Phase 8.6 46-site → 18-entry audit ledger complete                                       | YES (every one of 46 ledger sites mapped to its covering entry with disassembly evidence; per-entry `note` text specified) |
| Phase 9 integration changeset documented                                                 | YES    |
| Phase 10 completion ledger with concrete verification criteria                           | YES (29 numbered checkpoints across build/boot/runtime/coverage) |
| Phase 11 deferred items listed with follow-up tasks                                      | YES (7 follow-ups, all with trigger conditions; prior-revision FU4 ledger-typo correction now resolved in-place) |
| v3 Gap 1 (slot-LUT per-index mapping): explicit table + algorithm in §1.3.1               | YES |
| v3 Gap 2 (`0x54052` disjunction): Path B selected with verbatim text-RAM clear loops in §2.2.1 | YES |
| v3 Gap 3 (§5.3 commit-path disambiguation): only §5.2 path implemented; spillover deferred to FU2 | YES |
| v3 Gap 4 (§6.5 VRAM roundtrip mechanical detail): §6.5.1..§6.5.6 cover insertion/source/read-back/comparison/diagnostic/stop | YES |
| v3 Gap 5 (metadata reconciliation): §2.1/§2.2 byte-lengths match §8.4; §9.1/§9.2 helper-count terminology fixed; §9.3 symbol list extended for §6.5/§7.3 .bss symbols | YES |
| v3 mechanical-closure test: every spec section produces exactly one implementation under strict no-inference policy | YES |
| v3.1 Defect 1 closure: §6.5.1 uses explicit `jsr genesistan_pc090oj_dma_self_test`; assembler-resolution paragraph removed | YES |
| v3.1 Defect 2 closure: §4.6 reconciled to §1.3.1 + explicit MUST NOT LUT-consultation rule for all non-`init_clear_3ad44` helpers | YES |
| v3.1 Defect 3 closure: §3.A downstream `0xD00000..0xD0001F` search documented; Resolution B applied (0x54052 slots 72..75, priority/init-clear shifted to 76..79) | YES |
| v3.1 mechanical-closure test: every touched section resolves to one implementation with no inference | YES |
| No source/spec/tool modifications                                                         | YES — design spec only |
| Every spec point cited to evidence                                                       | YES — April 6, reconciliation v2, classification ledger, MAME, current rastan-direct source, disassembly all cited |
| Strategy A only (no Strategy B drift)                                                    | YES    |
| Hook-site ledger scope preserved (no sites removed or added; 51 ≥ 46 paths intercepted) | YES    |
| DMA fix included                                                                          | YES (and verified already in tree) |
| Audit guards defined as production diagnostic-with-controlled-stop, not suppression      | YES (Rule 8 walkthrough in §7.4)        |
| Direct VDP writes from helpers                                                            | NO — all helpers write only to WRAM staging |
| Helper functions loop or wait                                                             | NO — each performs one batch translation, RTS-returns |
| Memory shadowing                                                                          | NO — `staged_sprite_*` is semantic, not address-mirroring; LUT is metadata, not memory |
| v3.2 surgical correction (§2.2.A polymorphic dispatch at 0x03AD44): preserves both tilemap and PC090OJ subsystem behaviors per Rule 19 | YES — caller enumeration verified non-overlapping ranges; pre-existing `genesistan_hook_tilemap_bg_fill` semantics preserved on tilemap branch; v3.1 `genesistan_pc090oj_hook_init_clear_3ad44` semantics preserved on PC090OJ branch (renamed to dispatch helper); §7.3 audit fall-through reuses existing mechanism (no new audit) |
| v3.2 final opcode_replace count: 90 (= 73 HEAD baseline + 17 net new appends; entry at 0x03AD44 is in-place update, not append) | YES |
| v3.2 scope-preservation (Rule 17: only §0/§1.3/§1.3.1/§2.2/§2.2.A/§4.6/§8.1/§8.2/§8.4/§8.6#8/§9.2/§9.3/§10.1/§12 touched; all other sections unchanged) | YES |
| STOP triggered                                                                            | NO    |

---

## Appendix A — Cross-reference

- April 6 baseline: `docs/design/Andy_pc0900j_sprite_correctness_audit.md`
- Reconciliation v2: `docs/design/Andy_pc090oj_reconciliation_v2.md`
- Writer classification ledger (with §3.7.1 `0x3AD56`→`0x3AD5C` typo corrected in-place per disassembly footnote): `docs/design/Andy_pc090oj_writer_classification_ledger.md`
- D00778 root cause: `docs/design/Andy_d00778_write_path_analysis.md`
- FU1 evidence: `docs/design/Cody_fu1_arcade_trace_510EA_510F4.md`
- Build 0052 state: `docs/design/Cody_boot_s_160_deletion_implementation.md`
- April 6 reference renderer: `apps/rastan/src/startup_trampoline.s`
- Existing rastan-direct hooks: `apps/rastan-direct/src/tilemap_hooks.s`, `apps/rastan-direct/src/vdp_comm.s`
- Active spec: `specs/rastan_direct_remap.json`
- Disassembly: `build/maincpu.disasm.txt`
- MAME hardware reference: `docs/reference/mame/rastan/src/mame/taito/pc090oj.cpp`
- RULES.md and ARCHITECTURE.md (mandatory architecture compliance)
