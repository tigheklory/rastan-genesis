# Cody — 0435 vs 0437 Remaining Rope Regression Isolation

Date: 2026-10-16  
Task type: analysis plus temporary unnumbered controls; no production correction and no numbered ROM.  
Accepted comparison baseline: Build 0435.  
Current source/build under test: Build 0437, default frontend/gameplay origin `8/8`.

## Result

The remaining deterministic rope regression is owned by the Build-0437 native SAT-origin path.
An unnumbered control that restored only the PC090OJ pass-entry and per-piece Y-origin instruction
shape to Build 0435, while leaving Build-0437 `vdp_commit_scroll` intact, returned the canonical
benchmark from 806 to **803 frames** and the full-HUD benchmark from 859 to **854 frames**. Those are
the exact accepted Build-0435 results.

Therefore the Plane A/B `ADDQ.W #8,D0` to `ADDI.W #8,D0` changes are real static costs, but they do
not own a measurable frame of this deterministic route. Diagnostic B and C were not needed.

## Actual executable differential

The preserved numbered ROMs were disassembled directly with the repository's m68k ELF objdump. The
addresses below are ROM/runtime addresses in the Genesis-native helper region, not arcade PCs.

### SAT pass entry

| Build | Address | Instruction(s) | Gameplay cost |
|---|---:|---|---:|
| 0435 | `0x074848` | `beq.w 0x074AD2` | 10 cycles, taken |
| 0437 | `0x074850` | `bne.s 0x074856`; `bra.w 0x074AD8` | 8 + 10 = 18 cycles |

This is **+8 cycles per gameplay invocation of `pc090oj_native_emit_pass`**. It executes on the
canonical rope route. It is pass-count dependent, not sprite-count dependent; full HUD does not by
itself add another pass.

### SAT per-piece Y realization

Build 0435 at `0x074D4C`:

```asm
addi.w  #-8,d2
btst    #14,d3
bne.w   bbox_proven_visible
```

Build 0437 at `0x074D52`:

```asm
btst    #14,d3
beq.s   apply_build_y_origin
addi.w  #-8,d2
bra.s   y_origin_ready
apply_build_y_origin:
subi.w  #8,d2
y_origin_ready:
btst    #14,d3
bne.w   bbox_proven_visible
```

For default `8/8`, both arithmetic forms produce the same value and both cost 8 cycles. The
regression is the redundant first bit test and selection branches retained from making fixed-screen
HUD tuples independent of an alternate gameplay origin:

| Piece kind | 0435 origin/test path | 0437 origin/test path | Residual |
|---|---:|---:|---:|
| ordinary/raw-coordinate | 30 cycles | 50 cycles | **+20 cycles/piece** |
| bit-14 fixed-screen HUD | 28 cycles | 56 cycles | **+28 cycles/piece** |

Cycle accounting uses MC68000 register/immediate timings: `ADDI.W`/`SUBI.W #imm,Dn` 8,
`BTST #imm,Dn` 10, short conditional taken/not-taken 10/8, word conditional taken/not-taken 10/12,
and `BRA` 10 cycles. The transform is reached once per candidate native piece entering final SAT
geometry, so it executes throughout the canonical rope route and is sprite-count dependent. The
full-HUD ROM emits additional bit-14 HUD pieces, which take the more expensive +28-cycle branch and
therefore amplify the measured loss from +3 to +5 frames.

No additional register loads/stores, save/restore instructions, or origin RAM accesses remain in
Build 0437. Other differing branch displacements in this region are address reflow caused by the
inserted bytes; their instruction form and runtime meaning are unchanged. The two substantive SAT
differences are the pass-entry shape and the duplicated bit-14 selection above.

### Plane A scroll

| Build | Address | Instruction | Frequency | Difference |
|---|---:|---|---|---:|
| 0435 | `0x0701CE` | `addq.w #8,d0` | once per VBlank scroll commit | 4 cycles |
| 0437 | `0x0701CE` | `addi.w #8,d0` | once per VBlank scroll commit | 8 cycles |

This is **+4 cycles per VBlank** on the rope route, independent of sprite count and HUD mode.

### Plane B scroll

| Build | Address | Instruction | Frequency | Difference |
|---|---:|---|---|---:|
| 0435 | `0x0701EC` | `addq.w #8,d0` | once per VBlank scroll commit | 4 cycles |
| 0437 | `0x0701EE` | `addi.w #8,d0` | once per VBlank scroll commit | 8 cycles |

This is another **+4 cycles per VBlank**, for +8 cycles per complete scroll commit. No runtime
domain-selection or reconvergence branch is emitted in the Build-0437 equal-origin Plane A/B path.

## Unnumbered isolation controls

The existing default `8/8` code was temporarily assembled with only the SAT path made executable-
shape equivalent to Build 0435:

- direct taken gameplay `BEQ.W`, rather than not-taken `BNE.S` plus `BRA.W`;
- one `ADDI.W #-RASTAN_GAMEPLAY_Y_ORIGIN,D2` followed by the existing single bit-14 bbox test;
- Build-0437 Plane A/B `ADDI.W #8,D0` left unchanged.

The temporary edits were removed after producing the controls. Production source remains at the
Build-0437 state.

| Control | HUD mode | Trial | Result |
|---|---:|---:|---:|
| A canonical | 2 | one | **803 frames / 13,400.588 ms** |
| A full HUD | 1 | one | **854 frames / 14,251.684 ms** |
| B | — | — | not run; A already isolated the complete measured regression |
| C | — | — | not run; A already isolated the complete measured regression |

Evidence:

- `states/traces/build0437_origin_isolation_A/`
- `states/traces/build0437_origin_isolation_A_full_hud/`

Both runs used the unchanged deterministic rope route under **GENESIS NTSC MAME**. No other gameplay
was driven.

## Final correction feasibility

**YES.** When the two Makefile origins are equal, conditional assembly can emit the exact Build-0435
runtime shape while retaining both Makefile constants:

- use the configured common immediate in the one old `ADDI.W #-origin,D2` instruction;
- use `ADDQ.W #origin,D0` when the common value is representable by ADDQ (1..8), with an assembler-
  selected `ADDI.W` form for other configured values;
- emit domain selection only in unequal-origin builds.

No origin RAM state, runtime domain branch, or extra reconvergence branch is required for equal
origins. This task deliberately does not implement that production correction.

## Architecture and scope

The semantic cut is unchanged: retained arcade scene/object/scroll decisions remain above the cut;
the native helpers realize final Genesis SAT and VSRAM output below it. No PC090OJ/PC080SN tail was
restored, retired, or changed. No production source, remap, gameplay, collision, or world state was
changed. Build counter remains 437.

- Existing project tools reused: repository m68k objdump,
  `tools/mame/run_rope_attach_performance_benchmark.sh`, its existing Lua route, and existing
  summarizer.
- New tooling created: none.
- Why new tooling was necessary: not applicable.

STOP status: remaining 0435→0437 deterministic rope regression isolated; final production correction
not implemented and no numbered build produced.
