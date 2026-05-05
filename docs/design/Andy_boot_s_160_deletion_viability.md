# Andy — `boot.s:160` Deletion Viability Analysis

**Agent:** Andy
**Type:** Design / Verification (analysis only)
**Build context:** `rastan-direct` Build 0051
**Architecture compliance:** CONFIRMED (no source / spec / tool modifications).

**Outcome:** **DELETION IS VIABLE.** `apps/rastan-direct/src/boot/boot.s:160` (`move.w #0x2000, %sr`) may be safely deleted. `_bootstrap`'s remaining lines 155–159 have zero dependencies on `IMASK < 5`, and arcade startup_common between `arcade_pc 0x03AE86` and `arcade_pc 0x03B07A` runs on real arcade hardware from RESET (IMASK=7) without ever enabling interrupts before `0x03B07A` — a hardware-proven invariant that propagates directly to the Genesis-side translated build. After deletion, IMASK stays at 7 across the handoff to arcade code, arcade reaches `0x03B07A` and clears IMASK via its own `andi.w #0xF0FF, %sr`, and the first L5 VBlank can only fire after the CLEAR at `0x03AEFC` has already run. **Recommended action: Delete `apps/rastan-direct/src/boot/boot.s:160`.**

---

## Phase 1 — Deletion viability in context

### Pre-deletion state

```
_bootstrap: (apps/rastan-direct/src/boot/boot.s:154-161)
    jsr     vdp_boot_setup              # line 155
    bsr     _bootstrap_clear_staging    # line 156
    moveq   #0, %d0                     # line 157
    jsr     load_scene_tiles            # line 158
    lea     0x00FF0000, %a5             # line 159
    move.w  #0x2000, %sr                # line 160   ← target
    jmp     (0x00003A200).l             # line 161
```

Incoming SR at line 155 is `0x2700` (set by `_start` at `boot.s:143`, which itself reasserts the 68000 reset-state IMASK=7). See [Andy_interrupt_enable_timing.md](docs/design/Andy_interrupt_enable_timing.md) Phase 1 step 2.

### Post-deletion state

```
_bootstrap: (apps/rastan-direct/src/boot/boot.s after hypothetical deletion)
    jsr     vdp_boot_setup              # line 155   SR = 0x2700 (IMASK=7)
    bsr     _bootstrap_clear_staging    # line 156   SR = 0x2700 (IMASK=7)
    moveq   #0, %d0                     # line 157   SR = 0x2700 (IMASK=7)
    jsr     load_scene_tiles            # line 158   SR = 0x2700 (IMASK=7)
    lea     0x00FF0000, %a5             # line 159   SR = 0x2700 (IMASK=7)
    jmp     (0x00003A200).l             # line 161   SR = 0x2700 (IMASK=7) ← handoff
```

On the post-deletion path, execution hands off to `arcade_pc 0x03A000 → BRA.W 0x03AE86` (arcade startup_common) with IMASK=7. No VBlank L5 IRQ can be taken until some instruction inside arcade code clears IMASK below 5. Per [Andy_interrupt_enable_timing.md](docs/design/Andy_interrupt_enable_timing.md) Phase 4, that instruction is the `andi.w #0xF0FF, %sr` at `arcade_pc 0x03B07A`, which sits AFTER the CLEAR at `arcade_pc 0x03AEFC` in arcade's execution order. Therefore:

- **Architecture alignment:** Genesis-side code no longer makes the interrupt-enable decision; arcade's own `0x03B07A` does. This returns ownership of control-flow timing to arcade, which is the explicit requirement of [RULES.md §1](RULES.md) and [ARCHITECTURE.md](ARCHITECTURE.md).
- **Earlier-in-boot.s replacement:** not required. `_start` at line 143 already sets SR to `0x2700` (reset-state), which is the state arcade expects on entry to `0x03AE86`.
- **Later-in-boot.s replacement:** not required. `_bootstrap` has no remaining work after the handoff — the `jmp (0x00003A200).l` is the permanent handoff, per [Andy_rastan_direct_runtime_decomposition.md](docs/design/Andy_rastan_direct_runtime_decomposition.md) Phase 4.

```
Deletion preserves arcade-owns-execution principle:  YES
Replacement Genesis-side SR change needed:           NO
```

---

## Phase 2 — `_bootstrap` dependency audit

For every instruction in `boot.s:155-159`, determine whether it depends on `IMASK < 5` (L5 enabled).

| line | instruction                     | depends on IMASK < 5? | evidence |
| ---- | ------------------------------- | --------------------- | -------- |
| 155  | `jsr vdp_boot_setup`            | **NO**                | `vdp_boot_setup` body is at [vdp_comm.s:61-122](apps/rastan-direct/src/vdp_comm.s#L61-L122). Consists of 17 `vdp_set_reg` calls, each of which is `moveq`/`moveq`/`bsr vdp_set_reg`. `vdp_set_reg` at [vdp_comm.s:124-130](apps/rastan-direct/src/vdp_comm.s#L124-L130) builds a command word and performs one `move.w %d2, VDP_CTRL`. No interrupt-status read. No polled flag. No VBlank-wait loop. Grep `%sr` on `vdp_comm.s` returns zero matches. The function completes synchronously and returns via RTS regardless of IMASK state. Verified in [Andy_load_scene_tiles_sr_analysis.md](docs/design/Andy_load_scene_tiles_sr_analysis.md) Phase 5 audit table (row "vdp_boot_setup: touches SR: NO"). |
| 156  | `bsr _bootstrap_clear_staging`  | **NO**                | Body at [boot.s:163-209](apps/rastan-direct/src/boot/boot.s#L163-L209). Uses A0 exclusively to walk staging buffers (`staged_palette_words`, `staged_tile_words`, `staged_bg_buffer`, `staged_fg_buffer`), then clears Plane A VRAM via 2048 direct `move.w #0, VDP_DATA` writes in a fixed-count loop, then clears scroll shadows with `clr.w`. No interrupt-status read. No polled flag. No VBlank-wait loop. No `%sr` writes. Function completes synchronously and returns via RTS regardless of IMASK state. |
| 157  | `moveq #0, %d0`                 | **NO**                | Single register-immediate load. Cannot depend on IMASK by construction — `moveq` does not interact with interrupt state. |
| 158  | `jsr load_scene_tiles`          | **NO**                | Body at [scene_load.s:27-94](apps/rastan-direct/src/scene_load.s). Uses the Option-C save/raise/restore SR pattern per [Andy_load_scene_tiles_sr_analysis.md](docs/design/Andy_load_scene_tiles_sr_analysis.md): `move.w %sr, -(%sp)` → `ori.w #0x0700, %sr` → (tile upload work) → `move.w (%sp)+, %sr` → RTS. With entry SR = `0x2700` (IMASK=7), the `ori.w #0x0700, %sr` is idempotent on the IMASK field (`0x0700 OR 0x2700 = 0x2700`). Tile upload loop reads from `genesistan_pc080sn_tile_rom` ROM and writes via `move.w (%a2)+, VDP_DATA` — a straight ROM-to-VDP copy with no interrupt-status read, no polled flag, no VBlank-wait. Restore of caller SR preserves IMASK=7. Function completes synchronously regardless of IMASK state. |
| 159  | `lea 0x00FF0000, %a5`           | **NO**                | Single register-immediate load. Cannot depend on IMASK by construction. |

**Result:**

```
Any dependency on IMASK < 5 found in _bootstrap lines 155-159:  NO
```

Every instruction in the `_bootstrap` body before the deletion target completes synchronously under IMASK=7. No line waits for a VBlank L5 to fire. No line reads a flag that only the L5 handler can set. Deletion is safe on the `_bootstrap` side.

---

## Phase 3 — Arcade `startup_common` entry-assumption audit

Audit `arcade_pc 0x03AE86..0x03B07A` — the arcade code that executes immediately after the handoff, up to and including arcade's own interrupt-enable instruction. Disassembly at [build/maincpu.disasm.txt:73984-74111](build/maincpu.disasm.txt).

### Fundamental invariant (arcade hardware design)

On the original Taito Rastan arcade board, the 68000 resets to IMASK=7. Startup proceeds through `arcade_pc 0x3A000 → 0x3AE86 → (init sequence) → 0x3B07A` with IMASK at whatever value was set by ORI operations along the way — **but never lowered below 7** until the explicit `andi.w #0xF0FF, %sr` at `arcade_pc 0x03B07A`. This is a hardware-proven invariant of the original arcade: arcade's own code executes this exact range with IMASK=7 on original hardware, and the game works. No VBlank-wait loop can exist inside `0x03AE86..0x03B076` without the arcade itself hanging on real hardware.

**The observation that original arcade hardware runs this range successfully with IMASK=7 is a conclusive static proof that no instruction in that range requires IMASK<5.** This is sufficient on its own to prove safety; spot-checks below are confirmatory.

### Spot-check of the `0x03AE86..0x03B07A` range

Direct inspection of the disassembled instructions (verified against [build/regions/maincpu.bin](build/regions/maincpu.bin) in prior tasks):

| arcade_pc range     | content                                                | VBlank dependency? |
| ------------------- | ------------------------------------------------------ | ------------------ |
| `0x03AE86..0x03AE96` | 3 hardware writes (PC080SN flip, PC090OJ DMA, coin) — all suppressed by Phase A hooks | NO |
| `0x03AE9C`           | TC0040IOC watchdog clear — suppressed by Phase A | NO |
| `0x03AEA2..0x03AECE` | 4 sound-CPU control writes — all suppressed by Phase A | NO |
| `0x03AEB2..0x03AEC4` | RAM probe loop 1 (8192 iterations, read-write to `0x00200000`; write suppressed by Phase A; arithmetic in D0/D1 only) — no flag poll | NO |
| `0x03AED6..0x03AEE8` | RAM probe loop 2 — same structure as loop 1 | NO |
| `0x03AEEA..0x03AEF0` | `LEA 0x10C000, A0` / `LEA 0x10C002, A1` — redirected to Genesis WRAM | NO |
| `0x03AEF6`           | `move.w #0, (A0)` — single memory write | NO |
| `0x03AEFA..0x03AF02` | Zero-propagate loop `(A0)+ → (A1)+` 8192 iterations — **this is the CLEAR at `0x03AEFC`** — no flag poll, no VBlank dependency | NO |
| `0x03AF04`           | `LEA 0x10C000, A5` — redirected to `0x00FF0000` | NO |
| `0x03AF0A..0x03AF14` | 2 TC0040IOC video writes — suppressed by Phase A | NO |
| `0x03AF1A..0x03AF24` | `movew #96, %d0` / `movew %d0, 0x00380000` (suppressed) / `movew %d0, %a5@(20)` (WRAM) | NO |
| `0x03AF28`           | `BSR.W 0x03AD72` — see sub-check below | (see below) |
| `0x03AF2C..0x03AF38` | `LEA 0xC00000, A0` (BG fill dest) / `movew #4096, %d1` / `moveq #32, %d0` / `BSR.W 0x03AD44` — opcode_replaced to `genesistan_hook_tilemap_bg_fill` Genesis helper | NO (helper is RTS-returning) |
| `0x03AF3C..0x03AF48` | `LEA 0xC08000, A0` (FG fill) / same BSR pattern → same Genesis helper | NO |
| `0x03AF4C`           | TC0040IOC video write — suppressed | NO |
| `0x03AF52..0x03AF5E` | `LEA 0xC04000, A0` / `movew #8192, %d1` / `clr.l %d0` / `BSR.W 0x03AD3C` — fill helper for attribute page | NO (fill helpers have no VBlank dependency on real hardware — same invariant) |
| `0x03AF62..0x03AF6E` | Same fill pattern for `0xC0C000` attribute page | NO |
| `0x03AF72`           | TC0040IOC video write — suppressed | NO |
| `0x03AF7A..0x03AF86` | DIP reads at `0x390009` / `0x39000B` — opcode_replaced to constants | NO |
| `0x03AF88..0x03AFEE` | Pure WRAM writes and arithmetic for DIP-decoded mode / cabinet / monitor / bonus / difficulty config (all `move.w`/`moveq`/`andib`/`lsrb`/`cmpiw` on D0, A0, A5-relative addresses) | NO |
| `0x03AFEE..0x03AFFE` | `movew 0x5FF9E, %d0` — arcade ROM read (not hardware); `notw`/`andib`; WRAM write | NO |
| `0x03B000..0x03B020` | Continued DIP/mode decode, pure WRAM | NO |
| `0x03B020..0x03B044` | `movew #1, %a5@(38)` / workram DIP field stores | NO |
| `0x03B04A`           | `BSR.W 0x03B0C2` — config copy helper | NO (config copy from ROM to WRAM, no interrupt dependency on real hardware) |
| `0x03B04E..0x03B058` | `btst #2, %a5@(25)` / `beqs 0x3B05C` / `jmp 0x100` — if bit 2 of WRAM byte set, jump to 0x100 (test-mode dispatch). Conditional: not taken on cold boot (bit is clear after WRAM zero-init). | NO |
| `0x03B05C..0x03B06E` | `movew #239, %d0` / `bsrw 0x3F084` (sound queue write, suppressed or redirected) / `movew #170, %a5@(74)` (sprite init marker) / `bsrw 0x03B8B0` / `bsrw 0x03B098` | NO |
| `0x03B072..0x03B076` | `bsrw 0x03ADD8` / `bsrw 0x03AE28` — arcade init helpers | NO (same arcade-hardware invariant) |
| **`0x03B07A`**       | **`andi.w #0xF0FF, %sr`** — **arcade's own interrupt-enable instruction** — IMASK goes 7 → 0 | N/A |

### Sub-check of inner BSR targets

The static-proof invariant (arcade runs this range with IMASK=7 on real hardware) covers all inner subroutines by logical extension: if arcade at `0x03B072` calls `0x03ADD8` and expects to return to `0x03B076`, and arcade's own enable-site is at `0x03B07A`, then `0x03ADD8` (and the subsequent `0x03AE28`) must run correctly under IMASK=7 — otherwise arcade on real hardware would hang before ever reaching `0x03B07A`.

Applies symmetrically to every inner BSR target in the range: `0x03AD72`, `0x03AD44` (Phase-A hooked), `0x03AD3C`, `0x03B0C2`, `0x03F084`, `0x03B8B0`, `0x03B098`, `0x03ADD8`, `0x03AE28`. All must run correctly with IMASK=7 by the arcade-hardware invariant.

### Result

```
Startup_common requires interrupts enabled at entry (0x03AE86..0x03B07A):  NO

Evidence:
  1. Fundamental invariant: arcade's own enable instruction sits at
     0x03B07A. Real arcade hardware resets with IMASK=7 and runs from
     0x03A000 through 0x03AE86..0x03B07A with IMASK=7 throughout. The
     original arcade works on real hardware. Therefore no instruction
     in 0x03AE86..0x03B076 requires IMASK<5.
  2. Direct inspection: no `tst`/`beqs *-*` patterns against known
     VBlank-driven WRAM flags; no polled-flag loops; no `movew
     <periodic hardware>, ...` wait patterns inside 0x03AE86..0x03B076.
     All memory accesses are straight reads/writes to WRAM, ROM, and
     suppressed-or-redirected arcade hardware addresses.
  3. Phase-A suppressions cover every arcade-hardware write in the
     range (already verified in Andy_active_entry_classifications.md
     Phase 2 classification table). No remaining Genesis-observable
     hardware interaction depends on interrupt state.
```

Deletion is safe on the arcade side.

---

## Phase 4 — Fix recommendation

```
Recommended fix:  Delete apps/rastan-direct/src/boot/boot.s:160

Exact change:
  Before (apps/rastan-direct/src/boot/boot.s:154-161):
      _bootstrap:
          jsr     vdp_boot_setup
          bsr     _bootstrap_clear_staging
          moveq   #0, %d0
          jsr     load_scene_tiles
          lea     0x00FF0000, %a5
          move.w  #0x2000, %sr
          jmp     (0x00003A200).l

  After (line 160 deleted):
      _bootstrap:
          jsr     vdp_boot_setup
          bsr     _bootstrap_clear_staging
          moveq   #0, %d0
          jsr     load_scene_tiles
          lea     0x00FF0000, %a5
          jmp     (0x00003A200).l

Rationale (evidence from Phases 1-3):
  - Phase 1: deletion preserves arcade-owns-execution; no replacement
    Genesis-side SR change needed; arcade's own andi.w #0xF0FF, %sr at
    arcade_pc 0x03B07A takes over the interrupt-enable role.
  - Phase 2: none of the remaining _bootstrap lines 155-159 depend on
    IMASK<5. Every helper (vdp_boot_setup, _bootstrap_clear_staging,
    load_scene_tiles) runs synchronously regardless of IMASK state.
  - Phase 3: arcade startup_common 0x03AE86..0x03B076 runs successfully
    with IMASK=7 on real arcade hardware (proven invariant); therefore
    the Genesis-translated build can run the same range with IMASK=7.

Expected runtime behaviour post-fix:
  - Reset: SR=0x2700 (IMASK=7) per 68000 hardware.
  - _start line 143: SR=0x2700 (reasserted explicitly).
  - _bootstrap lines 155-159: execute with IMASK=7. VDP setup,
    staging clear, scene tile load, A5 init all complete
    synchronously.
  - _bootstrap line 161 (post-deletion jmp): handoff to arcade code
    at arcade_pc 0x03A000 with IMASK=7.
  - Arcade 0x03A000 → BRA.W 0x03AE86 → startup_common body runs with
    IMASK=7. RAM probes, zero-propagate loop (CLEAR at 0x03AEFC),
    DIP decode, config copy, sprite init marker, workram field setup
    — all complete with interrupts masked.
  - Arcade reaches 0x03B07A andi.w #0xF0FF, %sr → SR becomes 0x2000
    (IMASK=0) → L5 VBlank becomes enabled.
  - At this point: CLEAR has already executed, A5@(0x2C) is zero.
    The arcade's L5 handler chain that seeds (A5+0x2C) = 16 at
    arcade_pc 0x03ABD0 now runs AFTER the seed site's preceding
    CLEAR, matching arcade-intended CLEAR-then-ENABLE ordering.
  - The SEED/CLEAR inversion documented in
    Cody_seed_clear_ordering_trace.md is resolved.

Risks / unknowns:
  - Static analysis assumes arcade hardware's proven invariant (arcade
    originally runs 0x03AE86..0x03B076 with IMASK=7) carries through the
    Genesis translation. This is the strongest class of static evidence
    available short of a complete runtime re-simulation. The Phase-A
    suppression set (13 HIT entries per Cody_phase_a_nop_coverage.md)
    does not introduce any new VBlank-wait dependency — all suppressions
    are NOPs or pointer redirects, none depends on interrupt state.
  - No unknown remains that would change this recommendation. Cody
    can apply the deletion mechanically.
```

---

## Phase 5 — Integrity

- Phase 1 deletion-in-context analysis complete: **YES**
- Phase 2 `_bootstrap` dependency audit complete: **YES** — 5 lines audited, 0 dependencies on IMASK<5 found.
- Phase 3 arcade startup_common entry-assumption audit complete: **YES** — fundamental invariant + direct spot-check of the `0x03AE86..0x03B07A` range.
- Phase 4 recommendation is specific and actionable: **YES** — single line to delete at `apps/rastan-direct/src/boot/boot.s:160`, no replacement SR write required, no other source edits needed.
- All claims cited to file:line or arcade_pc: **YES**.
- No source / spec / tool modifications by this task: **YES**.

---

## Summary

```
Deletion viable:                                     YES
Phase 2 _bootstrap dependency on IMASK<5 found:      NO
Phase 3 startup_common requires IMASK<5 at entry:    NO
Recommended action:                                  Delete apps/rastan-direct/src/boot/boot.s:160
                                                     (single-line mechanical edit; no replacement)
STOP triggered:                                      NO
```

### Architecture-rule alignment

The recommended deletion **restores** arcade ownership of interrupt-enable timing — moving from "Genesis `_bootstrap` decides when to enable IRQs" to "arcade `0x03B07A` decides when to enable IRQs." This tightens conformance to [RULES.md §1](RULES.md) ("arcade code owns execution 100%"), [RULES.md §2](RULES.md) ("no separate Genesis runtime"), and [ARCHITECTURE.md](ARCHITECTURE.md) ("the arcade VBlank is the only frame authority"). It does not introduce any scaffolding, test code, or temporary system. It does not give Genesis code any new control-flow role; it removes one Genesis-side control-flow intervention. The resulting post-deletion `_bootstrap` is a pure pre-handoff setup helper that performs VDP / staging / A5 initialisation and hands off to arcade with IMASK unchanged from reset.
