# Andy — Interrupt-Enable Timing and Ownership

**Agent:** Andy
**Type:** Static Analysis / Ownership Audit (no implementation)
**Build context:** `rastan-direct` Build 0051
**Architecture compliance:** CONFIRMED (no source / spec / tool modifications).

**Outcome:** The first IMASK-lowering instruction on the cold-boot path is **`move.w #0x2000, %sr` at [apps/rastan-direct/src/boot/boot.s:160](apps/rastan-direct/src/boot/boot.s#L160)** — **Genesis-side ownership**. It executes *before* the `jmp` to arcade code, i.e. BEFORE arcade startup_common entry at `arcade_pc 0x3AE86`, and therefore BEFORE the CLEAR at `arcade_pc 0x3AEFC`. Arcade's own interrupt-enable site exists inside startup_common at **`arcade_pc 0x3B07A`** (`andi.w #0xF0FF, %sr`), which is reached AFTER the CLEAR. Arcade-intended ordering is **CLEAR-then-ENABLE**; Genesis currently inverts that by enabling interrupts in `_bootstrap` before arcade code runs at all. This is the static-evidence account of the ordering inversion first reported in [Andy_3BB60_to_3ABD0_control_flow.md](docs/design/Andy_3BB60_to_3ABD0_control_flow.md); per Rule 16 this document does not propose a fix.

---

## Phase 1 — Cold-boot execution path walk

### Step 0 — Reset vector

| field | value | source |
| ----- | ----- | ------ |
| ROM[0x0000] (initial SP) | `0x00FF0000` | [apps/rastan-direct/src/boot/boot.s:37](apps/rastan-direct/src/boot/boot.s#L37) — `.long 0x00FF0000` |
| ROM[0x0004] (initial PC) | `_start` (runtime_genesis_pc `0x00000202`) | [apps/rastan-direct/src/boot/boot.s:38](apps/rastan-direct/src/boot/boot.s#L38) — `.long _start` |

On 68000 cold reset, SR = `0x2700` (supervisor, trace=0, IMASK = 7).

### Step 1 — Walk from `_start` to `arcade_pc 0x03AE86`

| step | file or arcade_pc | line or byte offset | instruction | notes (SR change, branch, handoff) |
| ---: | ----------------- | ------------------- | ----------- | ---------------------------------- |
| 1 | `apps/rastan-direct/src/boot/boot.s` | 142 | `_start:` (label) | reset vector target |
| 2 | `apps/rastan-direct/src/boot/boot.s` | 143 | `move.w #0x2700, %sr` | **writes SR** — sets IMASK=7 explicitly (redundant with reset state; does **not** lower IMASK) |
| 3 | `apps/rastan-direct/src/boot/boot.s` | 144 | `lea 0x00FF0000, %sp` | SP load; no SR change |
| 4 | `apps/rastan-direct/src/boot/boot.s` | 146 | `move.b HW_VERSION, %d0` | reads `0x00A10001` |
| 5 | `apps/rastan-direct/src/boot/boot.s` | 147 | `andi.b #0x0F, %d0` | byte AND; no SR-IMASK change (ANDI.B affects CCR, not SR bits 8-10) |
| 6 | `apps/rastan-direct/src/boot/boot.s` | 148 | `beq.s .Ltmss_done` | conditional branch — if non-SEGA cartridge header, skip TMSS. On a standard build this branch is not taken (real SEGA unit). Either path converges at line 150. |
| 7 | `apps/rastan-direct/src/boot/boot.s` | 149 | `move.l #0x53454741, TMSS_REG` | TMSS ("SEGA") unlock write; no SR change |
| 8 | `apps/rastan-direct/src/boot/boot.s` | 150 | `.Ltmss_done:` (label) | — |
| 9 | `apps/rastan-direct/src/boot/boot.s` | 152 | `jsr _bootstrap` | push return address, jump to `_bootstrap` at line 154. No SR change. |
| 10 | `apps/rastan-direct/src/boot/boot.s` | 154 | `_bootstrap:` (label) | — |
| 11 | `apps/rastan-direct/src/boot/boot.s` | 155 | `jsr vdp_boot_setup` | calls `vdp_comm.s:61-122`. Body uses `moveq`/`bsr vdp_set_reg` only; **no SR writes**. Grep `%sr` on `vdp_comm.s` returns zero matches. Returns via RTS (no SR change on return — RTS only pops PC, not SR). |
| 12 | `apps/rastan-direct/src/boot/boot.s` | 156 | `bsr _bootstrap_clear_staging` | calls `boot.s:163-209`. Body writes only `A0`-indirected staging buffers and VDP_DATA; **no SR writes**. Grep `%sr` on the `_bootstrap_clear_staging` range returns zero matches. Returns via RTS at `boot.s:209`. |
| 13 | `apps/rastan-direct/src/boot/boot.s` | 157 | `moveq #0, %d0` | scene id = 0 (title). No SR change. |
| 14 | `apps/rastan-direct/src/boot/boot.s` | 158 | `jsr load_scene_tiles` | calls `scene_load.s:27`. Body uses Option-C SR pattern: `move.w %sr, -(%sp)` → `ori.w #0x0700, %sr` (RAISES mask; with SR already = `0x2700` this is a no-op on the IMASK field) → VDP work → `move.w (%sp)+, %sr` (restores caller SR bit-for-bit). Verified by grep `%sr` on `scene_load.s` returning a single hit: line 47 `ori.w #0x0700, %sr`. No `move.w #imm, sr` or `andi.w #imm, sr` that lowers IMASK present in `scene_load.s`. IMASK remains 7 across the call boundary. |
| 15 | `apps/rastan-direct/src/boot/boot.s` | 159 | `lea 0x00FF0000, %a5` | A5 workram-base init (per [Andy_a5_initialization_analysis.md](docs/design/Andy_a5_initialization_analysis.md) recommendation, applied in Build 0050). No SR change. |
| 16 | `apps/rastan-direct/src/boot/boot.s` | **160** | **`move.w #0x2000, %sr`** | **writes SR** — sets SR = `0x2000`: supervisor=1, trace=0, **IMASK = 0**. **This is the FIRST IMASK-lowering instruction on the cold-boot path.** |
| 17 | `apps/rastan-direct/src/boot/boot.s` | 161 | `jmp (0x00003A200).l` | unconditional jump to Genesis ROM offset `0x00003A200` = `arcade_pc 0x03A000`. Handoff to arcade code. No SR change. |
| 18 | `arcade_pc 0x03A000` | — | `6000 0E84` — `bra.w 0x03AE86` | unconditional BRA.W. Target = `0x03A002 + 0x0E84 = 0x03AE86`. No SR change. |
| 19 | `arcade_pc 0x03AE86` | — | `33FC 0000 00C5 0000` — `move.w #0, 0x00C50000` (suppressed by opcode_replace → NOP sequence) | **Arcade startup_common body entry.** Walk terminates here per Phase 1's completion criterion. |

Walk completes at step 19 (`arcade_pc 0x03AE86`, startup_common entry).

### Verification notes on the walk

- **Scene_load.s SR behaviour (step 14):** confirmed current-tree state at [apps/rastan-direct/src/scene_load.s](apps/rastan-direct/src/scene_load.s) via `grep -n '%sr\|#0x2000\|#0x2700' scene_load.s` → single hit `47: ori.w #0x0700, %sr`. Previous `move.w #0x2700, %sr` at old line 46 and `move.w #0x2000, %sr` at old line 91 are absent (Option C fix applied per [Andy_load_scene_tiles_sr_analysis.md](docs/design/Andy_load_scene_tiles_sr_analysis.md) Phase 4 recommendation, implemented in Cody_scene_load_sr_fix.md).
- **vdp_comm.s SR audit (step 11):** `grep -n '%sr' apps/rastan-direct/src/vdp_comm.s` returns **zero matches**. Verified in the Phase 5 audit table of [Andy_load_scene_tiles_sr_analysis.md](docs/design/Andy_load_scene_tiles_sr_analysis.md).
- **Branch at step 6:** on a real Genesis (cart ID non-zero), the BEQ is not taken and control falls through to the TMSS write at line 149. Either way, both paths converge at the `.Ltmss_done` label (line 150) and proceed identically to the `jsr _bootstrap`. The branch does not alter the walk's ordering of SR-modifying instructions.

---

## Phase 2 — First IMASK-lowering instruction on the path

Identified at step 16:

```
File:           apps/rastan-direct/src/boot/boot.s
Line:           160
Instruction:    move.w #0x2000, %sr
Bytes:          46 FC 20 00   (on 68000: 46FC = MOVE.W #imm,SR; 2000 = immediate)
SR before:      0x2700  (supervisor, trace=0, IMASK=7; set by _start line 143)
SR after:       0x2000  (supervisor, trace=0, IMASK=0; all interrupts unmasked)
```

### Cold-reset context

- **Is this reached before or after arcade startup_common entry at `arcade_pc 0x03AE86`?**
  **BEFORE.** Step 16 is Genesis-side `_bootstrap`, executing before the `jmp (0x00003A200).l` at step 17. Arcade startup_common is not reached until step 19.
- **Is this reached before or after the CLEAR at `arcade_pc 0x03AEFC`?**
  **BEFORE.** The walk arrives at startup_common entry (`0x3AE86`) after step 16. The CLEAR is at `0x03AEFC`, which is reached only after executing the startup_common prologue (hardware-address writes from `0x3AE86`, RAM-probe loops at `0x3AEB2..0x3AEC4` and `0x3AED6..0x3AEE8`, and the pointer-setup at `0x3AEEA..0x3AEF6`). All of that occurs **after** `_bootstrap` has already lowered IMASK at step 16. The gap between IMASK enable (step 16) and CLEAR first execution is ~116 ms per [Andy_a5_initialization_analysis.md](docs/design/Andy_a5_initialization_analysis.md) (two 8191-iteration RAM probes + one 8191-iteration zero-propagate loop at 68000 @ 7.67 MHz).

### Enumeration of candidate SR writes on the cold-boot path

For completeness, the complete list of SR-modifying instructions on the walk (from reset to step 19), ordered temporally:

| step | instruction | SR before → after (IMASK field) | lowers IMASK < 5? |
| ---- | ----------- | ------------------------------- | ----------------- |
| 2    | `move.w #0x2700, %sr`            | undefined(reset=7) → 7            | NO (re-asserts) |
| 14   | `ori.w #0x0700, %sr` (inside scene_load.s) | 7 → 7 (idempotent)          | NO |
| 14   | `move.w (%sp)+, %sr` (restore, inside scene_load.s) | 7 → 7                     | NO (caller value preserved) |
| **16**  | **`move.w #0x2000, %sr`**        | **7 → 0**                         | **YES — FIRST**  |

No earlier instruction on the path lowers IMASK below 5. The first one is at step 16.

---

## Phase 3 — Ownership classification

```
Instruction location:                  apps/rastan-direct/src/boot/boot.s:160
Ownership:                             Genesis-side
Temporal position on cold-boot path:   step 16 (of 19 in the walk to startup_common entry)
Relationship to CLEAR at 0x03AEFC:     BEFORE  (step 16 runs before step 19 = startup_common entry,
                                                which runs before CLEAR at 0x03AEFC is reached
                                                inside startup_common body)
```

The instruction is physically located in the Genesis-side bootstrap source, not in arcade ROM. Its presence predates the arcade handoff: `_bootstrap` executes it on the Genesis path before transferring control to arcade code via the `jmp (0x00003A200).l` at line 161.

---

## Phase 4 — Arcade-intended interrupt-enable site

### Walk through arcade startup_common to find the SR-modifying instruction that enables L5

Starting at `arcade_pc 0x03AE86`, walked the disassembly ([build/maincpu.disasm.txt](build/maincpu.disasm.txt) lines 73984-74111) for SR-modifying instructions that clear IMASK bits.

Candidate forms searched via `grep '%sr' build/maincpu.disasm.txt` in the range `0x3AE86..0x3B080`:

- `oriw #<imm>, %sr` — sets bits; cannot clear IMASK (would only raise it).
- `andiw #<imm>, %sr` — clears bits; candidate if imm's bits 8-10 clear.
- `movew #<imm>, %sr` — writes literal; candidate if imm's IMASK field < 5.
- `movew <src>, %sr` (register/memory) — runtime-dependent; candidate only if statically resolvable.

### Result

Only one SR-clearing instruction exists in the startup_common body within the examined range:

```
arcade_pc 0x03B07A:   02 7C F0 FF         andi.w #0xF0FF, %sr
(= andi.w #-3841, %sr per 68000 signed-immediate convention)
```

Mask value `0xF0FF` = binary `1111 0000 1111 1111`:
- Bit 13 (trace enable): preserved.
- Bit 12 (master interrupt): not valid on 68000 (reserved).
- **Bits 8-11 (IMASK + reserved): CLEARED.** IMASK goes to 0.
- Low byte (CCR): preserved.

If SR was `0x2700` immediately before this instruction, after executing: `0x2700 AND 0xF0FF = 0x2000`. **IMASK = 0. L5 is enabled.**

### Context of arcade_pc 0x03B07A

From [build/maincpu.disasm.txt:74107-74113](build/maincpu.disasm.txt):

```
3b064: 3b7c 00aa 004a    move.w #170, %a5@(74)
3b06a: 6100 0844         bsr.w 0x3b8b0
3b06e: 6100 0028         bsr.w 0x3b098
3b072: 6100 fd64         bsr.w 0x3add8
3b076: 6100 fdb0         bsr.w 0x3ae28
3b07a: 027c f0ff         andi.w #0xF0FF, %sr     ← ARCADE INTERRUPT-ENABLE SITE
3b07e: 33c0 003c 0000    move.w %d0, 0x003c0000
3b084: 4a6d 1c10         tst.w %a5@(7184)
```

This is well inside startup_common's body, after a sequence of helper BSR calls (`0x3B8B0`, `0x3B098`, `0x3ADD8`, `0x3AE28`) that perform arcade-side subsystem initialisation. After these initialisations complete, arcade clears IMASK to 0 at `0x3B07A`, then continues with further init at `0x3B07E`.

### Position relative to CLEAR at `0x03AEFC`

CLEAR executes in the zero-propagate loop at `arcade_pc 0x03AEFE..0x03AF02` (inside startup_common). The arcade-intended enable site at `0x3B07A` is at a higher arcade_pc than CLEAR.

Walking execution order from startup_common entry (`0x3AE86`):
1. `0x3AE86..0x3AF02`: hardware init + RAM probes + zero-propagate loop (CLEAR executes during this range)
2. `0x3AF04`: A5 workram-base load (`lea 0x10C000, %a5` — redirected by opcode_replace to `lea 0x00FF0000, %a5`)
3. `0x3AF0A..0x3AFFE`: post-CLEAR init sequence (more hardware writes, DIP reads, mode setup)
4. `0x3B000..0x3B076`: continuing initialisation including BSRs to `0x3B8B0`, `0x3B098`, `0x3ADD8`, `0x3AE28`
5. **`0x3B07A`: ANDI.W #0xF0FF, SR — arcade interrupt-enable**

CLEAR at `0x03AEFC` runs at step-in-arcade #1 above; arcade enable at `0x03B07A` runs at step-in-arcade #5. **Arcade-intended ordering: CLEAR-then-ENABLE.**

### Reported values

```
Arcade interrupt-enable site:          arcade_pc 0x03B07A
  Instruction bytes:                   02 7C F0 FF
  Mnemonic:                            andi.w #0xF0FF, %sr  (= andi.w #-3841, %sr)
  Effect (with pre-SR = 0x2700):       SR := 0x2000 (IMASK cleared to 0)
Arcade-intended ordering:              CLEAR-then-ENABLE
                                        (CLEAR at 0x3AEFC runs first during startup_common;
                                         ENABLE at 0x3B07A runs after a full init-helper chain)
```

### Implication visible from the static evidence

Because the Genesis-side `_bootstrap` lowers IMASK at `boot.s:160` BEFORE jumping to arcade code, the arcade startup_common executes the entire path `0x3AE86..0x3B076` with interrupts already enabled. The arcade's own enable site at `0x3B07A` is **redundant on Genesis** — by the time execution reaches it, IMASK is already 0.

This is reported as a fact of current ownership and sequencing. The fix direction (should `_bootstrap` refrain from enabling interrupts and let arcade do so at `0x3B07A`? does that raise secondary concerns around `_bootstrap`'s own timing needs?) is **out of scope per Rule 16**.

---

## Phase 5 — Integrity

- Cold-boot path walked from reset vector to startup_common entry: **YES** (19 steps, each tied to a file:line or arcade_pc citation).
- First IMASK-lowering instruction identified: **YES** (`apps/rastan-direct/src/boot/boot.s:160`, `move.w #0x2000, %sr`).
- Ownership determined: **YES** (Genesis-side, in `apps/rastan-direct/src/boot/boot.s`).
- Arcade-intended interrupt-enable site located: **YES** (`arcade_pc 0x03B07A`, `andi.w #0xF0FF, %sr`).
- All Phase 1 steps cited to file:line or arcade_pc: **YES**.
- No source / spec / tool modifications: **YES**.

---

## Summary

```
First IMASK-lowering instruction:    apps/rastan-direct/src/boot/boot.s:160
                                     move.w #0x2000, %sr
Ownership:                           Genesis-side
Relationship to CLEAR at 0x03AEFC:   BEFORE
Arcade-intended interrupt-enable:    arcade_pc 0x03B07A
                                     andi.w #0xF0FF, %sr
Arcade-intended ordering:            CLEAR-then-ENABLE
                                     (arcade CLEAR at 0x03AEFC runs during startup_common,
                                      well before arcade enable at 0x03B07A)
Observed ordering on Genesis:        ENABLE-then-CLEAR
                                     (Genesis boot.s:160 enables interrupts before arcade
                                      code runs at all, then arcade startup_common begins;
                                      arcade reaches CLEAR at 0x3AEFC only after a long
                                      execution path during which VBlank L5 may have
                                      already fired several times — consistent with the
                                      reversed SEED/CLEAR ordering reported in
                                      Cody_seed_clear_ordering_trace.md)
STOP triggered:                      NO
```

### Architecture-rule alignment

- Genesis-side code (`boot.s:160`) currently owns the interrupt-enable decision for the arcade program's cold-boot execution. This is an **ownership fact** that the rest of the investigation can now act on. Per Rule 16 and [RULES.md §4](RULES.md) / [ARCHITECTURE.md](ARCHITECTURE.md), the appropriate downstream task is to determine whether the `_bootstrap` SR write is a necessary Genesis-side boot service (e.g. required to allow arcade's own `BSR`-style subroutines to take interrupts during its later init) or whether it should be deferred so that arcade's own `andi.w #0xF0FF, %sr` at `0x3B07A` is the sole interrupt-enable point. That determination is out of this document's scope.

- No architectural violation is introduced by this analysis (no source, spec, or tool was modified).
