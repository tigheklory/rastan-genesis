# Andy — P1 / P2 Hook Closure Design

**Agent:** Andy
**Type:** Analysis + Design (no implementation)
**Build context:** current `rastan-direct`
**Architecture compliance:** CONFIRMED against [RULES.md](RULES.md) and [ARCHITECTURE.md](ARCHITECTURE.md).

**Outcome:** All 18 blocking sites from
[Andy_p1_p2_prerequisite_verification.md](docs/design/Andy_p1_p2_prerequisite_verification.md)
receive permanent production-intent treatments. **15 new
`opcode_replace` entries** required in
[specs/rastan_direct_remap.json](specs/rastan_direct_remap.json). Two
sites (`0x3AEF6`, `0x3AEFE..0x3AF02` loop) inherit behaviorally from
the two pointer-fix entries at `0x3AEEA` / `0x3AEF0` and require **no
new remap entry of their own**. No new Genesis helpers are required.
P1 and P2 both pass after application.

---

## Address-space legend

- `arcade_pc <value>` — PC in arcade ROM address space.
- `HW <addr>` — 68000-space memory-mapped address on the arcade board.
- Genesis WRAM: `0x00FF0000..0x00FFFFFF`.
- Genesis cart-ROM end: `0x000FC1C3` (per [build/rastan-direct/address_map.json](build/rastan-direct/address_map.json)).

---

## Phase 1 — Classification rules applied

Every site is assigned exactly one of the four classes from the
prompt:

1. **Suppress** — arcade HW write with no Genesis equivalent. Replace
   with `4E71` words matching the instruction byte count.
2. **Redirect** — write intent is valid, address is wrong, point to
   Genesis WRAM/ROM.
3. **Helper call** — not needed; none of the P1/P2 blockers require a
   new helper.
4. **Pointer fix** — `LEA abs.L, An` whose immediate is arcade-only
   memory. Change the 4-byte immediate to the corresponding Genesis
   WRAM address, matching the existing A5 remap at `arcade_pc
   0x0003AF04` (spec line 301).

**Suppression byte-count rule:** every `4E71` word occupies 2 bytes.
For an `N`-byte suppressed instruction, replacement is `N/2 × 4E71`
(`N` must be even; all 68000 instructions are even-length).
Instruction byte-counts were verified against the raw bytes at
[build/regions/maincpu.bin](build/regions/maincpu.bin) offsets
`0x3A008..0x3A01F` and `0x3AE86..0x3AF73`.

**Suppression precedent in current remap:**

| existing site | original bytes                 | replacement bytes      | bytes |
| ------------- | ------------------------------ | ---------------------- | ----- |
| `0x03ADFE`    | `33 FC 00 00 00 C5 00 00`      | `4E 71 4E 71 4E 71 4E 71` | 8 |
| `0x03AE06`    | `33 FC 00 01 00 D0 1B FE`      | `4E 71 4E 71 4E 71 4E 71` | 8 |
| `0x03AE16`    | `33 FC 00 01 00 C5 00 00`      | `4E 71 4E 71 4E 71 4E 71` | 8 |
| `0x03AE1E`    | `33 FC 00 00 00 D0 1B FE`      | `4E 71 4E 71 4E 71 4E 71` | 8 |
| `0x03AE9C`    | `42 79 00 38 00 00`            | `4E 71 4E 71 4E 71`    | 6 |
| `0x03AF1E`    | `33 C0 00 38 00 00`            | `4E 71 4E 71 4E 71`    | 6 |
| `0x03EF28`    | `33 C0 00 38 00 00`            | `4E 71 4E 71 4E 71`    | 6 |

**Pointer-fix precedent:**

| existing site | original bytes           | replacement bytes        | effect |
| ------------- | ------------------------ | ------------------------ | ------ |
| `0x03AF04`    | `4B F9 00 10 C0 00`      | `4B F9 00 FF 00 00`      | `LEA 0x0010C000, A5` → `LEA 0x00FF0000, A5` |

All designs below use these precedents exactly.

---

## Phase 2 — Per-instruction design

### P1.1 — `arcade_pc 0x0003AE86`

```
arcade_pc:          0x0003AE86
instruction:        MOVE.W #0, 0x00C50000
hardware_target:    HW 0x00C50000  (PC080SN screen-flip register)
arcade_chip:        PC080SN
classification:     suppress
justification:      PC080SN screen-flip has no Genesis equivalent and
                    no Genesis semantic effect; Genesis flip is
                    handled via VDP register 0 (not by this write).
                    Matches exact suppression precedent at 0x03ADFE.
implementation:     specs/rastan_direct_remap.json
instruction_size_bytes: 8
NOP_bytes:          4 × 4E71
original_hex:       33FC000000C50000
replacement_hex:    4E714E714E714E71
notes:              Near-duplicate of existing 0x03AE16 entry.
```

### P1.2 — `arcade_pc 0x0003AE8E`

```
arcade_pc:          0x0003AE8E
instruction:        MOVE.W #0, 0x00D01BFE
hardware_target:    HW 0x00D01BFE  (PC090OJ sprite-DMA register)
arcade_chip:        PC090OJ
classification:     suppress
justification:      PC090OJ DMA trigger has no Genesis equivalent;
                    Genesis sprite attribute table is maintained
                    by existing hooks, not this register.
                    Matches precedent at 0x03AE06 / 0x03AE1E.
implementation:     specs/rastan_direct_remap.json
instruction_size_bytes: 8
NOP_bytes:          4 × 4E71
original_hex:       33FC000000D01BFE
replacement_hex:    4E714E714E714E71
notes:              Same form as 0x03AE1E (`33FC 0000 00D0 1BFE`).
```

### P1.3 — `arcade_pc 0x0003AE96`

```
arcade_pc:          0x0003AE96
instruction:        CLR.W 0x00350008
hardware_target:    HW 0x00350008  (TC0140SYT coin counter / sound)
arcade_chip:        TC0140SYT
classification:     suppress
justification:      Arcade coin counter register has no Genesis
                    equivalent; coin input is handled on Genesis via
                    pad shadows (genesistan_shadow_input_390005).
implementation:     specs/rastan_direct_remap.json
instruction_size_bytes: 6
NOP_bytes:          3 × 4E71
original_hex:       427900350008
replacement_hex:    4E714E714E71
notes:              None.
```

### P1.4 — `arcade_pc 0x0003AEA2`

```
arcade_pc:          0x0003AEA2
instruction:        MOVE.B #4, 0x003E0001
hardware_target:    HW 0x003E0001  (TC0140SYT sound-CPU reset port)
arcade_chip:        TC0140SYT
classification:     suppress
justification:      Writes to arcade sound-CPU reset/bank bytes have
                    no Genesis equivalent; Genesis Z80 reset/bank are
                    managed by Z80-control ports (0x00A11100-0x00A11101).
implementation:     specs/rastan_direct_remap.json
instruction_size_bytes: 8
NOP_bytes:          4 × 4E71
original_hex:       13FC0004003E0001
replacement_hex:    4E714E714E714E71
notes:              None.
```

### P1.5 — `arcade_pc 0x0003AEAA`

```
arcade_pc:          0x0003AEAA
instruction:        MOVE.B #1, 0x003E0003
hardware_target:    HW 0x003E0003  (TC0140SYT sound-CPU bank port)
arcade_chip:        TC0140SYT
classification:     suppress
justification:      Same as P1.4.
implementation:     specs/rastan_direct_remap.json
instruction_size_bytes: 8
NOP_bytes:          4 × 4E71
original_hex:       13FC0001003E0003
replacement_hex:    4E714E714E714E71
notes:              None.
```

### P1.6 — `arcade_pc 0x0003AEBC`

```
arcade_pc:          0x0003AEBC
instruction:        MOVE.W D1, 0x00200000
hardware_target:    HW 0x00200000  (arcade RAM-probe region)
arcade_chip:        arcade-only RAM-presence probe loop
classification:     suppress
justification:      Arcade startup runs a probe read-modify-write
                    loop at 0x200000 to verify work-RAM is present.
                    On Genesis, 0x200000 is outside cart-ROM
                    (cart-ROM ends at 0x000FC1C3) and unmapped.
                    Write has no Genesis semantic effect.
implementation:     specs/rastan_direct_remap.json
instruction_size_bytes: 6
NOP_bytes:          3 × 4E71
original_hex:       33C100200000
replacement_hex:    4E714E714E71
notes:              The matching read-for-probe at 0x0003AEB6 is NOT
                    in the blocker list (reads of unmapped addresses
                    are not flagged). Only the write is suppressed.
                    D1 retains whatever it read at 0x0003AEB6.
```

### P1.7 — `arcade_pc 0x0003AEC6`

```
arcade_pc:          0x0003AEC6
instruction:        MOVE.B #4, 0x003E0001
hardware_target:    HW 0x003E0001
arcade_chip:        TC0140SYT
classification:     suppress
justification:      Same as P1.4.
implementation:     specs/rastan_direct_remap.json
instruction_size_bytes: 8
NOP_bytes:          4 × 4E71
original_hex:       13FC0004003E0001
replacement_hex:    4E714E714E714E71
notes:              Same as P1.4.
```

### P1.8 — `arcade_pc 0x0003AECE`

```
arcade_pc:          0x0003AECE
instruction:        MOVE.B #0, 0x003E0003
hardware_target:    HW 0x003E0003
arcade_chip:        TC0140SYT
classification:     suppress
justification:      Same as P1.5.
implementation:     specs/rastan_direct_remap.json
instruction_size_bytes: 8
NOP_bytes:          4 × 4E71
original_hex:       13FC0000003E0003
replacement_hex:    4E714E714E714E71
notes:              None.
```

### P1.9 — `arcade_pc 0x0003AEE0`

```
arcade_pc:          0x0003AEE0
instruction:        MOVE.W D1, 0x00200000
hardware_target:    HW 0x00200000
arcade_chip:        arcade RAM-probe
classification:     suppress
justification:      Same as P1.6.
implementation:     specs/rastan_direct_remap.json
instruction_size_bytes: 6
NOP_bytes:          3 × 4E71
original_hex:       33C100200000
replacement_hex:    4E714E714E71
notes:              None.
```

### P1.10 — `arcade_pc 0x0003AEEA` (POINTER FIX)

```
arcade_pc:          0x0003AEEA
instruction:        LEA 0x0010C000, A0
hardware_target:    A0 := 0x0010C000 (arcade work-RAM base)
arcade_chip:        arcade work-RAM
classification:     pointer_fix
justification:      Arcade's zero-propagate loop initializes work-RAM
                    at 0x10C000 (arcade) which maps to 0x00FF0000
                    (Genesis WRAM). Consistent with the A5 base
                    remap at 0x03AF04 that redirects the same base
                    literal to 0x00FF0000.
implementation:     specs/rastan_direct_remap.json
new_LEA_target:     0x00FF0000 (Genesis WRAM)
original_hex:       41F90010C000
replacement_hex:    41F900FF0000
consistency_with_A5_remap_at_0x3AF04: CONFIRMED (same pattern, A0 in
                    place of A5; opcode differs by register field:
                    41F9 = LEA abs.L, A0 vs 4BF9 = LEA abs.L, A5).
downstream_effect:  After this fix, the loop at 0x3AEFE..0x3AF02
                    zeros Genesis WRAM 0x00FF0000..0x00FF3FFE (16 KB).
                    Ends before BSS start at 0x00FF4000 — see
                    "Inherited" section below for range math.
notes:              None.
```

### P1.11 — `arcade_pc 0x0003AEF0` (POINTER FIX)

```
arcade_pc:          0x0003AEF0
instruction:        LEA 0x0010C002, A1
hardware_target:    A1 := 0x0010C002
arcade_chip:        arcade work-RAM + 2
classification:     pointer_fix
justification:      Same as P1.10. A1 is the propagate-destination
                    pointer; must be remapped so the post-increment
                    loop writes into Genesis WRAM.
implementation:     specs/rastan_direct_remap.json
new_LEA_target:     0x00FF0002
original_hex:       43F90010C002
replacement_hex:    43F900FF0002
consistency_with_A5_remap_at_0x3AF04: CONFIRMED (same pattern, A1).
downstream_effect:  Final write of the loop lands at
                    A1_initial + (8191-1)×2 = 0x00FF0002 + 0x3FFC
                    = 0x00FF3FFE. Does not clobber BSS at 0x00FF4000.
notes:              Although the prompt's blocker table listed only
                    0x3AEEA, the Phase-1 Classification-4 text
                    explicitly calls out 0x3AEF0 as requiring the
                    same pointer fix; P1 verification doc §Note 1
                    identified the A1 LEA as equally unredirected.
                    Included for completeness.
```

### P1.12 — `arcade_pc 0x0003AEF6` (INHERITED)

```
arcade_pc:          0x0003AEF6
instruction:        MOVE.W #0, (A0)
hardware_target:    *(A0) where A0 is set by 0x3AEEA
arcade_chip:        —
classification:     inherited from pointer_fix at 0x0003AEEA
justification:      This instruction writes through A0. After the
                    P1.10 pointer fix sets A0 = 0x00FF0000, this
                    write targets Genesis WRAM 0x00FF0000 (SAFE).
                    No explicit remap entry required.
implementation:     NONE (inherits)
notes:              Cody must NOT add a remap entry for this site.
                    Its safety depends entirely on P1.10 being in
                    place. If P1.10 is not applied, this instruction
                    still writes to arcade HW 0x0010C000 and is
                    unsafe.
```

### P1.13 — loop `arcade_pc 0x0003AEFE..0x0003AF02` (INHERITED)

```
arcade_pc_range:    0x0003AEFE (MOVE.W (A0)+, (A1)+) through
                    0x0003AF00 (SUBQ.W #1, D0) and
                    0x0003AF02 (BNE.S 0x3AEFE)
instruction:        8191-iteration zero-propagate loop
hardware_target:    (A0)/(A1) — set by 0x3AEEA / 0x3AEF0 pointer fixes
classification:     inherited from pointer_fix at 0x0003AEEA and 0x0003AEF0
justification:      Each iteration reads (A0)+ and writes (A1)+. After
                    pointer fixes, A0 starts at 0x00FF0000 and A1 at
                    0x00FF0002. Reads from initialized Genesis WRAM,
                    writes to Genesis WRAM. Last write at iteration
                    8191 lands at A1=0x00FF3FFE (proven in P1.11
                    downstream_effect). No BSS clobber.
implementation:     NONE (inherits)
notes:              Range proof:
                    - initial (A0,A1) = (0x00FF0000, 0x00FF0002)
                    - after 8191 iterations, last write at
                      0x00FF0002 + 8190*2 = 0x00FF3FFE
                    - BSS starts at 0x00FF4000 → no overlap
                    Cody must NOT add remap entries for 0x3AEFE,
                    0x3AF00, or 0x3AF02.
```

### P1.14 — `arcade_pc 0x0003AF0A`

```
arcade_pc:          0x0003AF0A
instruction:        MOVE.W D0, 0x003C0000
hardware_target:    HW 0x003C0000  (TC0040IOC video-control)
arcade_chip:        TC0040IOC
classification:     suppress
justification:      TC0040IOC video-control register sets arcade
                    display parameters (screen mode, H/V polarity)
                    irrelevant on Genesis; Genesis video mode is
                    configured once in vdp_boot_setup. Matches the
                    0x380000 watchdog-suppress pattern used multiple
                    times elsewhere (0x03A1D8, 0x03AE9C, 0x03AF1E,
                    0x03EF28, 0x03EF48, 0x03EF8A, 0x03EFAA, 0x045306).
implementation:     specs/rastan_direct_remap.json
instruction_size_bytes: 6
NOP_bytes:          3 × 4E71
original_hex:       33C0003C0000
replacement_hex:    4E714E714E71
notes:              None.
```

### P1.15 — `arcade_pc 0x0003AF14`

```
arcade_pc:          0x0003AF14
instruction:        MOVE.W D0, 0x003C0000
classification:     suppress
justification:      Same as P1.14.
instruction_size_bytes: 6
original_hex:       33C0003C0000
replacement_hex:    4E714E714E71
```

### P1.16 — `arcade_pc 0x0003AF4C`

```
arcade_pc:          0x0003AF4C
instruction:        MOVE.W D0, 0x003C0000
classification:     suppress
justification:      Same as P1.14.
instruction_size_bytes: 6
original_hex:       33C0003C0000
replacement_hex:    4E714E714E71
```

### P1.17 — `arcade_pc 0x0003AF72`

```
arcade_pc:          0x0003AF72
instruction:        MOVE.W D0, 0x003C0000
classification:     suppress
justification:      Same as P1.14.
instruction_size_bytes: 6
original_hex:       33C0003C0000
replacement_hex:    4E714E714E71
```

### P2.1 — `arcade_pc 0x0003A00C`

```
arcade_pc:          0x0003A00C
instruction:        CLR.W 0x00350008
hardware_target:    HW 0x00350008  (TC0140SYT coin counter)
arcade_chip:        TC0140SYT
classification:     suppress
justification:      Same as P1.3. The L5 handler clears the coin
                    counter once per VBlank; Genesis has no coin
                    counter to clear.
implementation:     specs/rastan_direct_remap.json
instruction_size_bytes: 6
NOP_bytes:          3 × 4E71
original_hex:       427900350008
replacement_hex:    4E714E714E71
notes:              This entry is functionally identical to P1.3 but
                    at a different arcade_pc — a separate remap
                    entry is required (opcode_replace is keyed on
                    arcade_pc).
```

### P2.2 — `arcade_pc 0x0003A012`

```
arcade_pc:          0x0003A012
instruction:        MOVE.W D0, 0x003C0000
hardware_target:    HW 0x003C0000  (TC0040IOC video-control)
arcade_chip:        TC0040IOC
classification:     suppress
justification:      Same as P1.14.
implementation:     specs/rastan_direct_remap.json
instruction_size_bytes: 6
NOP_bytes:          3 × 4E71
original_hex:       33C0003C0000
replacement_hex:    4E714E714E71
notes:              None.
```

---

## Phase 3 — Grouped summary

**Group A — Suppress (13 sites):**

| arcade_pc    | size | pattern                          |
| ------------ | ---- | -------------------------------- |
| `0x0003A00C` | 6    | `427900350008 → 4E714E714E71`   |
| `0x0003A012` | 6    | `33C0003C0000 → 4E714E714E71`   |
| `0x0003AE86` | 8    | `33FC000000C50000 → 4×4E71`     |
| `0x0003AE8E` | 8    | `33FC000000D01BFE → 4×4E71`     |
| `0x0003AE96` | 6    | `427900350008 → 3×4E71`         |
| `0x0003AEA2` | 8    | `13FC0004003E0001 → 4×4E71`     |
| `0x0003AEAA` | 8    | `13FC0001003E0003 → 4×4E71`     |
| `0x0003AEBC` | 6    | `33C100200000 → 3×4E71`         |
| `0x0003AEC6` | 8    | `13FC0004003E0001 → 4×4E71`     |
| `0x0003AECE` | 8    | `13FC0000003E0003 → 4×4E71`     |
| `0x0003AEE0` | 6    | `33C100200000 → 3×4E71`         |
| `0x0003AF0A` | 6    | `33C0003C0000 → 3×4E71`         |
| `0x0003AF14` | 6    | `33C0003C0000 → 3×4E71`         |
| `0x0003AF4C` | 6    | `33C0003C0000 → 3×4E71`         |
| `0x0003AF72` | 6    | `33C0003C0000 → 3×4E71`         |

Total suppress count: 15 entries.

**Group B — Pointer fix (2 sites):**

| arcade_pc    | original LEA                   | new LEA (Genesis WRAM)        |
| ------------ | ------------------------------ | ----------------------------- |
| `0x0003AEEA` | `41F90010C000` (LEA 0x0010C000, A0) | `41F900FF0000` (A0 = 0x00FF0000) |
| `0x0003AEF0` | `43F90010C002` (LEA 0x0010C002, A1) | `43F900FF0002` (A1 = 0x00FF0002) |

**Group C — Redirect:** NONE.

**Group D — Helper call:** NONE.

**Group E — Inherited (no remap entry of its own; depends on Group B):**

| arcade_pc               | depends on                  |
| ----------------------- | --------------------------- |
| `0x0003AEF6`            | Group B (A0 from `0x3AEEA`) |
| `0x0003AEFE..0x0003AF02` | Group B (A0 + A1)           |

---

## Phase 4 — remap.json entries

All entries follow the existing spec schema (see spec lines 113-449 of
[specs/rastan_direct_remap.json](specs/rastan_direct_remap.json)). Each
entry has `arcade_pc`, `original_bytes`, `replacement_bytes`, `note`.
Insert in ascending arcade_pc order to match existing file layout.

```json
{
  "arcade_pc": "0x03A00C",
  "original_bytes": "427900350008",
  "replacement_bytes": "4E714E714E71",
  "note": "Suppress arcade TC0140SYT coin-counter clear in L5 handler; no Genesis equivalent."
},
{
  "arcade_pc": "0x03A012",
  "original_bytes": "33C0003C0000",
  "replacement_bytes": "4E714E714E71",
  "note": "Suppress arcade TC0040IOC video-control write in L5 handler; no Genesis equivalent."
},
{
  "arcade_pc": "0x03AE86",
  "original_bytes": "33FC000000C50000",
  "replacement_bytes": "4E714E714E714E71",
  "note": "Suppress arcade PC080SN screen-flip write; no Genesis equivalent."
},
{
  "arcade_pc": "0x03AE8E",
  "original_bytes": "33FC000000D01BFE",
  "replacement_bytes": "4E714E714E714E71",
  "note": "Suppress arcade PC090OJ sprite-DMA trigger; no Genesis equivalent."
},
{
  "arcade_pc": "0x03AE96",
  "original_bytes": "427900350008",
  "replacement_bytes": "4E714E714E71",
  "note": "Suppress arcade TC0140SYT coin-counter clear in startup; no Genesis equivalent."
},
{
  "arcade_pc": "0x03AEA2",
  "original_bytes": "13FC0004003E0001",
  "replacement_bytes": "4E714E714E714E71",
  "note": "Suppress arcade TC0140SYT sound-CPU reset write; no Genesis equivalent."
},
{
  "arcade_pc": "0x03AEAA",
  "original_bytes": "13FC0001003E0003",
  "replacement_bytes": "4E714E714E714E71",
  "note": "Suppress arcade TC0140SYT sound-CPU bank write; no Genesis equivalent."
},
{
  "arcade_pc": "0x03AEBC",
  "original_bytes": "33C100200000",
  "replacement_bytes": "4E714E714E71",
  "note": "Suppress arcade RAM-probe write-back at 0x200000 (unmapped on Genesis)."
},
{
  "arcade_pc": "0x03AEC6",
  "original_bytes": "13FC0004003E0001",
  "replacement_bytes": "4E714E714E714E71",
  "note": "Suppress arcade TC0140SYT sound-CPU reset write (second pass)."
},
{
  "arcade_pc": "0x03AECE",
  "original_bytes": "13FC0000003E0003",
  "replacement_bytes": "4E714E714E714E71",
  "note": "Suppress arcade TC0140SYT sound-CPU bank clear (second pass)."
},
{
  "arcade_pc": "0x03AEE0",
  "original_bytes": "33C100200000",
  "replacement_bytes": "4E714E714E71",
  "note": "Suppress arcade RAM-probe write-back at 0x200000 (second pass)."
},
{
  "arcade_pc": "0x03AEEA",
  "original_bytes": "41F90010C000",
  "replacement_bytes": "41F900FF0000",
  "note": "Redirect arcade work-RAM base A0 from 0x10C000 (unmapped on Genesis) to Genesis WRAM 0xFF0000; matches A5 remap at 0x3AF04. Downstream zero-propagate loop at 0x3AEF6..0x3AF02 inherits."
},
{
  "arcade_pc": "0x03AEF0",
  "original_bytes": "43F90010C002",
  "replacement_bytes": "43F900FF0002",
  "note": "Redirect arcade work-RAM propagate-destination A1 from 0x10C002 to Genesis WRAM 0xFF0002; matches A5 and A0 remaps. Loop ends at 0xFF3FFE, no BSS clobber."
},
{
  "arcade_pc": "0x03AF0A",
  "original_bytes": "33C0003C0000",
  "replacement_bytes": "4E714E714E71",
  "note": "Suppress arcade TC0040IOC video-control write in startup (first)."
},
{
  "arcade_pc": "0x03AF14",
  "original_bytes": "33C0003C0000",
  "replacement_bytes": "4E714E714E71",
  "note": "Suppress arcade TC0040IOC video-control write in startup (second)."
},
{
  "arcade_pc": "0x03AF4C",
  "original_bytes": "33C0003C0000",
  "replacement_bytes": "4E714E714E71",
  "note": "Suppress arcade TC0040IOC video-control write in startup (third)."
},
{
  "arcade_pc": "0x03AF72",
  "original_bytes": "33C0003C0000",
  "replacement_bytes": "4E714E714E71",
  "note": "Suppress arcade TC0040IOC video-control write in startup (fourth)."
}
```

Total: **17 new entries**. Insert in ascending arcade_pc order so
they appear in-context with existing entries.

Cody must **not** add remap entries for `arcade_pc 0x03AEF6`,
`0x03AEFE`, `0x03AF00`, or `0x03AF02` — these inherit from the
pointer-fix entries above.

---

## Phase 5 — New helpers required

**NONE REQUIRED.**

All treatments are either suppression via NOPs or pointer-literal
rewriting. No Genesis-side helper function is called or created by
this design. No change to [apps/rastan-direct/src/main_68k.s](apps/rastan-direct/src/main_68k.s)
(or its decomposition successors) is required.

---

## Phase 6 — Final worklist

Ordered list Cody executes without interpretation. All items edit
the same file.

```
Item 1:
  arcade_pc: 0x03A00C
  action: add opcode_replace entry
  exact change: {"arcade_pc":"0x03A00C","original_bytes":"427900350008","replacement_bytes":"4E714E714E71","note":"Suppress arcade TC0140SYT coin-counter clear in L5 handler; no Genesis equivalent."}
  file: specs/rastan_direct_remap.json

Item 2:
  arcade_pc: 0x03A012
  action: add opcode_replace entry
  exact change: {"arcade_pc":"0x03A012","original_bytes":"33C0003C0000","replacement_bytes":"4E714E714E71","note":"Suppress arcade TC0040IOC video-control write in L5 handler; no Genesis equivalent."}
  file: specs/rastan_direct_remap.json

Item 3:
  arcade_pc: 0x03AE86
  action: add opcode_replace entry
  exact change: {"arcade_pc":"0x03AE86","original_bytes":"33FC000000C50000","replacement_bytes":"4E714E714E714E71","note":"Suppress arcade PC080SN screen-flip write; no Genesis equivalent."}
  file: specs/rastan_direct_remap.json

Item 4:
  arcade_pc: 0x03AE8E
  action: add opcode_replace entry
  exact change: {"arcade_pc":"0x03AE8E","original_bytes":"33FC000000D01BFE","replacement_bytes":"4E714E714E714E71","note":"Suppress arcade PC090OJ sprite-DMA trigger; no Genesis equivalent."}
  file: specs/rastan_direct_remap.json

Item 5:
  arcade_pc: 0x03AE96
  action: add opcode_replace entry
  exact change: {"arcade_pc":"0x03AE96","original_bytes":"427900350008","replacement_bytes":"4E714E714E71","note":"Suppress arcade TC0140SYT coin-counter clear in startup; no Genesis equivalent."}
  file: specs/rastan_direct_remap.json

Item 6:
  arcade_pc: 0x03AEA2
  action: add opcode_replace entry
  exact change: {"arcade_pc":"0x03AEA2","original_bytes":"13FC0004003E0001","replacement_bytes":"4E714E714E714E71","note":"Suppress arcade TC0140SYT sound-CPU reset write; no Genesis equivalent."}
  file: specs/rastan_direct_remap.json

Item 7:
  arcade_pc: 0x03AEAA
  action: add opcode_replace entry
  exact change: {"arcade_pc":"0x03AEAA","original_bytes":"13FC0001003E0003","replacement_bytes":"4E714E714E714E71","note":"Suppress arcade TC0140SYT sound-CPU bank write; no Genesis equivalent."}
  file: specs/rastan_direct_remap.json

Item 8:
  arcade_pc: 0x03AEBC
  action: add opcode_replace entry
  exact change: {"arcade_pc":"0x03AEBC","original_bytes":"33C100200000","replacement_bytes":"4E714E714E71","note":"Suppress arcade RAM-probe write-back at 0x200000 (unmapped on Genesis)."}
  file: specs/rastan_direct_remap.json

Item 9:
  arcade_pc: 0x03AEC6
  action: add opcode_replace entry
  exact change: {"arcade_pc":"0x03AEC6","original_bytes":"13FC0004003E0001","replacement_bytes":"4E714E714E714E71","note":"Suppress arcade TC0140SYT sound-CPU reset write (second pass)."}
  file: specs/rastan_direct_remap.json

Item 10:
  arcade_pc: 0x03AECE
  action: add opcode_replace entry
  exact change: {"arcade_pc":"0x03AECE","original_bytes":"13FC0000003E0003","replacement_bytes":"4E714E714E714E71","note":"Suppress arcade TC0140SYT sound-CPU bank clear (second pass)."}
  file: specs/rastan_direct_remap.json

Item 11:
  arcade_pc: 0x03AEE0
  action: add opcode_replace entry
  exact change: {"arcade_pc":"0x03AEE0","original_bytes":"33C100200000","replacement_bytes":"4E714E714E71","note":"Suppress arcade RAM-probe write-back at 0x200000 (second pass)."}
  file: specs/rastan_direct_remap.json

Item 12:
  arcade_pc: 0x03AEEA
  action: add opcode_replace entry (POINTER FIX)
  exact change: {"arcade_pc":"0x03AEEA","original_bytes":"41F90010C000","replacement_bytes":"41F900FF0000","note":"Redirect arcade work-RAM base A0 from 0x10C000 (unmapped on Genesis) to Genesis WRAM 0xFF0000; matches A5 remap at 0x3AF04. Downstream zero-propagate loop at 0x3AEF6..0x3AF02 inherits."}
  file: specs/rastan_direct_remap.json

Item 13:
  arcade_pc: 0x03AEF0
  action: add opcode_replace entry (POINTER FIX)
  exact change: {"arcade_pc":"0x03AEF0","original_bytes":"43F90010C002","replacement_bytes":"43F900FF0002","note":"Redirect arcade work-RAM propagate-destination A1 from 0x10C002 to Genesis WRAM 0xFF0002; matches A5 and A0 remaps. Loop ends at 0xFF3FFE, no BSS clobber."}
  file: specs/rastan_direct_remap.json

Item 14:
  arcade_pc: 0x03AF0A
  action: add opcode_replace entry
  exact change: {"arcade_pc":"0x03AF0A","original_bytes":"33C0003C0000","replacement_bytes":"4E714E714E71","note":"Suppress arcade TC0040IOC video-control write in startup (first)."}
  file: specs/rastan_direct_remap.json

Item 15:
  arcade_pc: 0x03AF14
  action: add opcode_replace entry
  exact change: {"arcade_pc":"0x03AF14","original_bytes":"33C0003C0000","replacement_bytes":"4E714E714E71","note":"Suppress arcade TC0040IOC video-control write in startup (second)."}
  file: specs/rastan_direct_remap.json

Item 16:
  arcade_pc: 0x03AF4C
  action: add opcode_replace entry
  exact change: {"arcade_pc":"0x03AF4C","original_bytes":"33C0003C0000","replacement_bytes":"4E714E714E71","note":"Suppress arcade TC0040IOC video-control write in startup (third)."}
  file: specs/rastan_direct_remap.json

Item 17:
  arcade_pc: 0x03AF72
  action: add opcode_replace entry
  exact change: {"arcade_pc":"0x03AF72","original_bytes":"33C0003C0000","replacement_bytes":"4E714E714E71","note":"Suppress arcade TC0040IOC video-control write in startup (fourth)."}
  file: specs/rastan_direct_remap.json

Item 18:
  No remap entry.
  arcade_pc 0x03AEF6, 0x03AEFE, 0x03AF00, 0x03AF02 — inherited behavior
  from Items 12 and 13. Do NOT add remap entries for these sites.

After all items are complete:
  P1 readiness: YES
  P2 readiness: YES
  Cody must re-run Andy_p1_p2_prerequisite_verification after implementation to confirm.
```

---

## Summary

- P1 blocking sites designed: **16 / 16** (13 suppress + 2 pointer_fix + 1 inherited group covering 0x3AEF6 and the loop)
- P2 blocking sites designed: **2 / 2** (both suppress)
- Suppress treatments: **15**
- Pointer-fix treatments: **2**
- Redirect treatments: **0**
- New helper treatments: **0**
- New remap.json entries required: **17**
- New helpers required: **0**
- Inherited (no new remap entry): **2 sites** (`0x03AEF6`, loop `0x03AEFE..0x03AF02`)
- P1 readiness after application: **YES**
- P2 readiness after application: **YES**
- STOP triggered: **NO**
- Ready for Cody implementation: **YES** (17 JSON insertions in specs/rastan_direct_remap.json, nothing else)
