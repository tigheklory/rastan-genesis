# Build 0309: Build 0308 Package-Walk Crash Fix

## Scope and result

Build 0309 fixes only the Build 0308 `ROUND 1 / READY` to gameplay crash. It preserves
the Build 0308 rendering architecture: one fixed 854-pattern Level-1 Plane-B residency,
per-record zero-drop Plane-A packages, and the native PC090OJ sprite path. It does not
implement the deferred no-black work, scrolling work, map-placement work, palette work,
or collision changes.

The assigned package-format hypothesis was tested rather than assumed. The package
compiler and runtime agree byte-for-byte. The first divergence is instead an ISA contract
failure: Build 0308 used a displacement larger than signed 16 bits in `lea
FG_BOUNDARY_FIXED_B_OFFSET(%a4),%a2`, and GNU `as` silently emitted a 68020 full-extension
effective address into a ROM executed by a physical 68000.

## Baseline and artifact preservation

- Failing Build 0308 ROM: `dist/rastan-direct/rastan_direct_video_test_build_0308.bin`
- Build 0308 SHA-256: `32f7523f450fb929db1f689a96eb844dde0611c709ed5f1acc67a1ab86467a65`
- Build 0308 size: 1,679,032 bytes
- Build 0308 remains present and unchanged.
- Build 0309 ROM: `dist/rastan-direct/rastan_direct_video_test_build_0309.bin`
- Build 0309 SHA-256: `d7b7bd39ba6c79b276021d344a6a8935c08c8ff7b028c14e793eb9e2b66dbd02`
- Build 0309 size: 1,679,032 bytes
- Counter: 308 -> 309
- Rolling ROM is byte-identical to numbered Build 0309.

## Observable crash evidence

The supplied Nomad image and the Build 0308 ROM establish:

- `runtime_genesis_pc 0x00072770`: the second `move.w (a2)+` in the fixed-B map loop.
- `runtime_genesis_pc 0x00072762`: malformed large-displacement `lea` bytes.
- `runtime_genesis_pc 0x0007276E`: first fixed-B `move.w (a2)+`.
- Package base `A4 = 0x00074058`.
- Fault address `0x000740C9 = A4 + 0x71`, which is odd.
- `D0 = 0x000000FD` at the crash screen.
- Frame SP `0x00FEFF4C` is valid Genesis WRAM-mirror space.

### Correction to the textual A2 transcription

The task text transcribes `A2 = 0x000740C3` (`+0x6B`), but both supplied crash-screen
images display `A2 = 0x000740C9`, the same address as `FAULT`. The instruction-level
reconstruction below independently predicts `0x000740C9`. There is no valid Build 0308
instruction sequence from this entry state that predicts `+0x6B`; reporting that offset as
proven would preserve a transcription error.

## Root cause reconstruction

Build 0308 contains these bytes at `runtime_genesis_pc 0x00072762`:

```text
45 F4 01 70 00 00 CD FC
```

With the assembler's default CPU mode, these bytes are presented as a 68020 full-extension
EA:

```asm
lea 0x0000CDFC(a4),a2
```

On a 68000, however, extension word `0x0170` is consumed as a brief indexed EA. At this
point `D0.w = 1`, retained from the immediately preceding `vdp_set_reg` call. The hardware
therefore computes:

```text
A2 = A4 + sign_extend(0x70) + D0.w
   = 0x00074058 + 0x70 + 1
   = 0x000740C9
```

The 68000 consumes only extension word `0x0170`. The unconsumed words `0000 CDFC` are then
executed as `ori.b #0xFC,d0`, changing `D0` from `0x01` to `0xFD`. This exactly explains the
captured crash-screen `D0 = 0x000000FD`. Execution reaches the fixed-B loop, and its first
word access uses odd `A2 = 0x000740C9`; the address-error frame is reported at/near the next
word read at `runtime_genesis_pc 0x00072770`.

The intended fixed-B map address was:

```text
0x00074058 + 0x0000CDFC = 0x00080E54
```

The malformed instruction therefore diverged before any generated package field or pair
was read. Later BlastEm values such as odd `A2 = 0x00074CC9` and wild `A3 = 0x001988B8`
are secondary executions after the instruction stream/pointer state has already diverged;
they are not evidence of a second package-section mismatch.

### Independent assembler proof

Assembling the original one-line expression with the project assembler's default CPU mode
reproduces the exact Build 0308 bytes. Assembling the same source with `-m68000` fails:

```text
Error: displacement too large for this architecture; needs 68020 or higher
```

This closes both the immediate defect and the build-system condition that allowed it.

## Exact generated binary contract

The compiler emits one 59,564-byte (`0xE8AC`) binary. Its SHA-256 remains
`9a9ea76c85526e3bc77a80363597931008fd038cff3ce52121b83ffd52e6c460` after the
Build 0309 assertion additions; the generated data did not require correction.

### Top-level layout

| Region | Start | Entry width/count | Bytes | End |
|---|---:|---:|---:|---:|
| Record table | `0x0000` | 4 x 23 | 92 (`0x5C`) | `0x005C` |
| Descriptor table | `0x005C` | 16 x 23 | 368 (`0x170`) | `0x01CC` |
| Per-record package data | `0x01CC` | 4-byte pairs | 52,272 | `0xCDFC` |
| Fixed-B map | `0xCDFC` | 4 x 854 | 3,416 (`0xD58`) | `0xDB54` |
| Fixed-B upload | `0xDB54` | 4 x 854 | 3,416 (`0xD58`) | `0xE8AC` |

There is no terminator and no implicit padding. Every boundary is naturally even.

### Record-table entry

| Offset | Width | Meaning |
|---:|---:|---|
| `+0` | 2 | first package index |
| `+2` | 2 | variant count; Build 0308/0309 emits 1 |

### 16-byte package descriptor

| Offset | Width | Meaning |
|---:|---:|---|
| `+0` | 4 | package-data offset from `fg_boundary_packages` |
| `+4` | 2 | map-pair count |
| `+6` | 2 | upload-pair count |
| `+8` | 2 | identity-pair count |
| `+10` | 2 | required-pattern diagnostic count |
| `+12` | 2 | reserved zero |
| `+14` | 2 | reserved zero |

### Per-package sections

Each map entry is `{arcade_code16, genesis_slot16}`. Each upload entry is
`{representative_arcade_code16, genesis_slot16}`. Each identity entry is
`{genesis_slot16, exact_pattern_identity16}`. Every entry is exactly four bytes.

| Pkg | Data/map start | Map count/bytes | Upload start | Upload count/bytes | Identity start | Identity count/bytes | End |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 0 | 460 | 49 / 196 | 656 | 49 / 196 | 852 | 49 / 196 | 1048 |
| 1 | 1048 | 125 / 500 | 1548 | 124 / 496 | 2044 | 124 / 496 | 2540 |
| 2 | 2540 | 237 / 948 | 3488 | 236 / 944 | 4432 | 236 / 944 | 5376 |
| 3 | 5376 | 333 / 1332 | 6708 | 333 / 1332 | 8040 | 333 / 1332 | 9372 |
| 4 | 9372 | 210 / 840 | 10212 | 209 / 836 | 11048 | 209 / 836 | 11884 |
| 5 | 11884 | 89 / 356 | 12240 | 89 / 356 | 12596 | 89 / 356 | 12952 |
| 6 | 12952 | 240 / 960 | 13912 | 239 / 956 | 14868 | 239 / 956 | 15824 |
| 7 | 15824 | 155 / 620 | 16444 | 154 / 616 | 17060 | 154 / 616 | 17676 |
| 8 | 17676 | 133 / 532 | 18208 | 132 / 528 | 18736 | 132 / 528 | 19264 |
| 9 | 19264 | 79 / 316 | 19580 | 78 / 312 | 19892 | 78 / 312 | 20204 |
| 10 | 20204 | 369 / 1476 | 21680 | 368 / 1472 | 23152 | 368 / 1472 | 24624 |
| 11 | 24624 | 484 / 1936 | 26560 | 483 / 1932 | 28492 | 483 / 1932 | 30424 |
| 12 | 30424 | 226 / 904 | 31328 | 225 / 900 | 32228 | 225 / 900 | 33128 |
| 13 | 33128 | 218 / 872 | 34000 | 217 / 868 | 34868 | 217 / 868 | 35736 |
| 14 | 35736 | 251 / 1004 | 36740 | 250 / 1000 | 37740 | 250 / 1000 | 38740 |
| 15 | 38740 | 350 / 1400 | 40140 | 349 / 1396 | 41536 | 349 / 1396 | 42932 |
| 16 | 42932 | 220 / 880 | 43812 | 219 / 876 | 44688 | 219 / 876 | 45564 |
| 17 | 45564 | 70 / 280 | 45844 | 70 / 280 | 46124 | 70 / 280 | 46404 |
| 18 | 46404 | 54 / 216 | 46620 | 54 / 216 | 46836 | 54 / 216 | 47052 |
| 19 | 47052 | 54 / 216 | 47268 | 54 / 216 | 47484 | 54 / 216 | 47700 |
| 20 | 47700 | 85 / 340 | 48040 | 85 / 340 | 48380 | 85 / 340 | 48720 |
| 21 | 48720 | 116 / 464 | 49184 | 115 / 460 | 49644 | 115 / 460 | 50104 |
| 22 | 50104 | 219 / 876 | 50980 | 219 / 876 | 51856 | 219 / 876 | 52732 |

## Runtime walk compared with compiler output

The corrected `fg_boundary_install` consumes the contract as follows:

1. `A4 = fg_boundary_packages`.
2. Validate record index `< 23`.
3. `A0 = A4 + record_index * 4`; validate four bytes.
4. Read two 16-bit record fields.
5. Validate package index `< 23`.
6. `A0 = A4 + 92 + package_index * 16`; validate 16 bytes.
7. Read `data_offset32`, `map_count16`, `upload_count16`, and `identity_count16`.
8. Validate `A4 + data_offset` through `(map + upload + identity) * 4`.
9. Map starts at `A4 + data_offset`.
10. Upload starts after `map_count * 4` bytes.
11. Identity starts after `(map_count + upload_count) * 4` bytes.
12. On the first install only, fixed-B map starts at `A4 + 52732`; fixed-B upload
    follows 3,416 bytes later; the complete 6,832-byte span is validated first.

Field-by-field comparison:

| Contract item | Compiler | Runtime | Match |
|---|---:|---:|---|
| Record entry | 4 bytes | index `<< 2` | YES |
| Descriptor offset | 92 bytes | `+92` | YES |
| Descriptor stride | 16 bytes | index `<< 4` | YES |
| Data offset | unsigned 32-bit | `move.l` / `adda.l` | YES |
| Counts | unsigned 16-bit | `move.w`, zero-extended where used long | YES |
| Map entry | 4 bytes | two word reads | YES |
| Upload entry | 4 bytes | two word reads | YES |
| Identity entry | 4 bytes | two word reads | YES |
| Fixed-B map start | 52732 | generated immediate 52732 | YES |
| Fixed-B map bytes | 3416 | 854 x 4 | YES |
| Fixed-B upload bytes | 3416 | 854 x 4 | YES |

Therefore the requested “bad field/section” does not exist. The exact mismatch is:

| Item | Generated/runtime intent | Build 0308 encoded assumption |
|---|---|---|
| Bad operation | `A2 = A4 + unsigned 32-bit 0xCDFC` | large displacement accepted as 68020 full EA |
| Intended width | explicit 32-bit offset | source appeared as an address-register displacement |
| Physical CPU | 68000 | assembler default allowed 68020 encoding |
| Expected start | package-relative `0xCDFC`, absolute `0x00080E54` | package-relative `0x71`, absolute `0x000740C9` |
| First divergence | before fixed-B map entry 0 | effective-address decode at `runtime_genesis_pc 0x00072762` |

## Build 0307 versus Build 0308

Build 0307 emitted only its prior per-package aligned map/upload layout and contains no
`45 F4 01 70 00 00 CD FC` large-EA sequence. Build 0308 added the global fixed-B tail after
all Plane-A packages. That tail begins at `0xCDFC`, beyond the signed d16 displacement
range. The stale assumption was not a package width/count/stride; it was that the generic
assembler invocation would enforce 68000-legal effective addresses. Build 0307 never
crossed the range that exposed this assumption.

## Build 0309 implementation

### Production correction

The invalid source expression was replaced with 68000-native arithmetic:

```asm
movea.l a4,a0
adda.l  #FG_BOUNDARY_FIXED_B_OFFSET,a0
move.l  #FG_BOUNDARY_FIXED_B_TOTAL_BYTES,d0
bsr     .Linstall_require_package_range
movea.l a0,a2
```

Final ROM disassembly at `runtime_genesis_pc 0x00072792` begins with `movea.l a4,a0`, and
`runtime_genesis_pc 0x00072794` is `adda.l #52732,a0`. No 68020 full-extension EA remains.

### Compiler assertions and generated constants

`tools/translation/compile_pc080sn_genesis.py` now defines one binary contract and asserts:

- record-entry width = 4;
- descriptor width = 16;
- pair width = 4;
- word alignment = 2;
- package data base is even;
- every map/upload/identity start is even;
- each emitted section end equals its calculated end;
- descriptors remain inside the descriptor table;
- every per-record span remains inside the per-record region;
- fixed-B map/upload starts are even;
- generated binary length equals fixed-B end and is even.

It emits the widths, fixed-B section byte sizes/offsets, total fixed-B span, and total binary
length for assembly. No alignment padding was needed because all verified boundaries are
naturally even.

### Runtime guards

Before generated word reads, the runtime now validates:

- record index `< 23`;
- new and old package indexes `< 23`;
- pointer is even;
- requested byte count is even;
- pointer is at or above `fg_boundary_packages`;
- pointer plus requested bytes does not wrap;
- end is at or below `fg_boundary_packages + 59564`;
- complete descriptor and package spans, not only first words, are in range.

Failure is deterministic and diagnostic: `D2` receives the bad pointer, `D3` receives
`0x504B4701` for a range/alignment violation or `0x504B4702` for an index violation, then an
`ILLEGAL` enters the existing crash handler. Required package work is never silently skipped
and no blank/fallback package is substituted.

### ISA and release gate

- `fg_tile_cache.s` is now assembled with `-m68000`; an out-of-range d16 expression fails
  the build rather than entering a ROM.
- A project-owned MAME gate runs before numbered artifact publication. It drives credit,
  Start, READY, initial residency, gameplay, and movement without user timing.

## Bounded package-walk pointer audit

| Instruction PC | Encoded value | Expected symbol/target | Linked target | Match |
|---:|---:|---|---:|---|
| `runtime_genesis_pc 0x000726FA` | `0x00074114` | `fg_boundary_packages` | `0x00074114` | YES |
| `runtime_genesis_pc 0x00072794` | immediate `0x0000CDFC` | fixed-B map | `0x00080F10` | YES |
| fixed-B upload | generated `0x0000DB54` | fixed-B upload | `0x00081C68` | YES |
| binary end | generated `0x0000E8AC` | one-past package binary | `0x000829C0` | YES |
| `runtime_genesis_pc 0x000727B0` | `0x00FF61CC` | `fg_boundary_active_lut` | `0x00FF61CC` | YES |
| `runtime_genesis_pc 0x000727CE` | `0x0010FCBC` | `genesistan_pc080sn_tile_rom` | `0x0010FCBC` | YES |

## Active package index

- Address: `Genesis-WRAM 0x00FFB1FC`.
- Meaning: package whose Plane-A residency is currently installed.
- Pre-initialization sentinel: `0xFFFF`.
- Legal installed range: `0..22`.
- First completed gameplay install: package 0.
- Gate completion after player movement: package 1.
- The range is valid and the index is not causal to the Build 0308 crash; the malformed
  fixed-B address executes on the initial sentinel path before package 0 can become active.

## Validation

### Canonical gate

- Result: `GATE_PASS`.
- Opcode replacements: 227, unchanged.
- Canonical coverage: `0x199EB8`, unchanged from Build 0308.
- No Build 0309 canonical-script adjustment was required.

### Expected-fail gate check

The new gate was first run against preserved Build 0308. It accepted credit and Start and
reached READY, then detected entry into the vector-derived crash-handler region around frame
318 before either residency install completed. Result: expected FAIL. This demonstrates that
the gate covers the previously missed transition.

### Build 0309 gameplay-entry gate

Trace: `states/traces/build0309_gameplay_entry_gate_20260823_104652/`

- Result: PASS.
- External frames: 562.
- Credit: PASS.
- Start: PASS.
- ROUND 1 / READY: PASS.
- Fixed-B install: PASS.
- Record-0 Plane-A install: PASS.
- Gameplay reached: PASS.
- Player control observed: PASS.
- Post-entry survival: 240 frames.
- Fixed-B probe: arcade code `0x04A6`, slot `0x0298`, active LUT `0x0298`.
- Record-0 probe: arcade code `0x0020`, slot `0x0357`, active LUT `0x0357`.
- Total residency epochs observed: 2 (initial package 0, then Plane-A package 1 after
  movement); fixed-B residency epochs remain exactly 1.
- Address errors: 0.
- Bus errors: 0.
- Illegal instructions: 0.
- Crash-handler entries: 0.
- SP valid under Genesis WRAM-mirror semantics: YES.

MAME dynarec did not expose every helper instruction through the fetch tap
(`gameplay_install_entries=0`), so install completion is proven from the resulting active
package/epoch/LUT state, not from that counter alone.

### Frontend smoke

Trace: `states/traces/rastan_direct_video_test_build_0309_mame_30s_20260823_104654/`

- Result: PASS.
- Frames: 1,798.
- Unique unmapped memory addresses: none.
- No fatal/error/exception evidence.

## Preserved architecture and deferred work

- Fixed Level-1 Plane-B vocabulary: 854 patterns retained.
- Fixed-B residency epochs: 1.
- Plane-B Y variants: 0.
- Plane-B drops: 0.
- Plane-B ordinary-record pattern DMA: 0.
- Plane-B ordinary-record name remap: 0.
- Plane-A record-0 package valid: YES.
- Plane-A required drops: 0 for every record.
- Native PC090OJ retained: YES.
- Build 0306 pass-table pointer correction retained: YES.
- Build 0305 WRAM scratch correction retained: YES.
- Mid-frame display-off/no-black Strategy C changed: NO; deferred.
- Scrolling changed: NO.
- Collision changed: NO.

## Files in the Build 0309 correction

- `apps/rastan-direct/src/fg_tile_cache.s`
- `tools/translation/compile_pc080sn_genesis.py`
- `apps/rastan-direct/Makefile`
- `tools/mame/scripts/build0309_gameplay_entry_gate.lua`
- `tools/mame/run_build0309_gameplay_entry_gate.sh`
- `docs/design/Cody_build0309_build0308_package_walk_crash_fix.md`
- `AGENTS_LOG.md`

Generated package constants/report and ordinary build outputs were regenerated by the
Makefile. The numbered Build 0308 artifact was not deleted or overwritten.

## User acceptance boundary

Automated validation proves MAME reaches and survives gameplay with coherent package state.
It does not claim physical-hardware or multi-emulator acceptance. Tighe must verify Build
0309 on the Nomad and any useful emulators. The intentional Build 0308 mid-frame display-off
black frame may remain; it is outside this crash-repair scope.
