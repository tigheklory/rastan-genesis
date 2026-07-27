# Rastan Arcade — Map-Stream Format & Scene Selection (canonical)

How Rastan selects a scene's map data, initializes the map-stream pointer `a5@0x10C6`, and interprets the selector byte stream. All facts re-derived from the original 68000 opcodes (rastan maincpu ROM, Capstone m68k); one focused MAME 0.276 trace confirmed the live pointer behaviour (see §5). `a5 = 0x10C000`.

> **Model in one line:** the segment index `a5@0x13E` and the byte pointer `a5@0x10C6` advance together **+1 per completed 64-publication ring cycle** (0x0558E4/0x0558FE), walking the RAW byte stream at 0x50F6B. Direction bytes (0/1/2) drive ring cycles; an **event byte (4/6/7) publishes nothing → the walk FREEZES on it** (proven). The route by which play then reaches the next direction byte is a **strongly-supported model, not fully proven** — see §6 (scene-init, the only pointer re-seed, is reached only from the config-driven level-start 0x045316; no event-completion→scene-init call path is traced).

## 1. Pointer-source table

| Field (a5@) | Abs | Meaning | Writers (arcade PC, from valid boundaries) |
|---|---|---|---|
| **0x10C6** | 0x10D0C6 | map-stream byte pointer | **0x0503D6** re-seed (`= 0x50F6B + byte[0x50EE0 + a5@0x13E]`); **0x0558E4** `+1` per ring cycle. **These are the ONLY two writers** (MAME-verified: the pointer is NOT recomputed each frame — corrupting it mid-play persists; changing a5@0x13E alone does not move it). Reads: 0x0558F0, 0x055938. |
| **0x13E** | 0x10C13E | **segment index** (single role) | **0x05025A** scene-init (`= byte[0x5073A + a5@0x1242]`); **0x0558FE** `+1` per ring cycle; **0x055F26** death-restore (`= a5@0x13B8`); **0x056014** death-restore (`= a5@0x13B8 − 1`). |
| 0x10A8 | 0x10D0A8 | selector (current stream byte) | ONLY 0x0558F8 (advance) / 0x055940 (reload tail of 0x055904), both `= *(byte)a5@0x10C6`. Read only as `cmpi #{0,1,2,4,5,6}` + one copy to 0x132C at 0x0558E8. |
| 0x132C | 0x10D32C | previous selector | 0x0558EC (`= old a5@0x10A8`); read at 0x0557DC (`if prev==0`, horizontal gate). (Decimal 4908 = 0x132C; not 0x136C.) |
| 0x1242 | 0x10D242 | **stage/scene number** (indexes stage LUT) | 0x03A620 (clr), 0x03A63A, 0x03A874, 0x0452C0 (stage handler). |
| 0x13B8 | 0x10D3B8 | saved segment index (checkpoint) | 0x055E14 (`= a5@0x13E` at death-phase 1). |
| 0x13AA | 0x10D3AA | scene/death phase (state machine 0x055E00…) | many in 0x055Exx. |
| 0x1386 | 0x10D386 | tilemap0 sub-index | 0x0502A6 (`= byte[0x507C5 + a5@0x13E]`). |
| 0x1000–0x103C | 0x10D000+ | 16 strip-source base ptrs | seeded 0x0502E4… (`ROM_tbl[i] + a5@0x13E×0x40`); advanced `+4`/group at 0x0558CE (net `+0x40`/ring cycle = tracks a5@0x13E). |
| 0x10E8 | 0x10D0E8 | event-active state (set 7 by events) | 0x0527CC; read 0x051598/0x0517D8/0x0540CC (scene/enemy engine). |

### ROM tables
| ROM | Size | Index | Entry | Purpose |
|---|---|---|---|---|
| **0x5073A** | **139 B** (abuts 0x507C5) | `a5@0x1242` (stage) | 1 byte | stage → **segment index** `a5@0x13E`. 48 distinct targets (0,4,8,0xC,0x10,0x13,0x16,…,0x89,0x8A), monotonic. **Every post-event segment is a target, but only 18 of the 48 targets are post-event; the other 30 are non-event segment starts** (see §2a). Max value 0x8A = 138. |
| **0x50EE0** | **139 B** | `a5@0x13E` (segment) | 1 byte | segment → **stream byte-offset**. For indices 0–137 (proven via deltas): 120 advance +1, 18 advance +2 (the +2 = direction+event records). Index 138's record length is not defined by a next entry. Directly precedes the stream (0x50F6B − 0x50EE0 = 0x8B = 139). |
| **0x50F6B** | 157 B proven (through 0x9C) + candidate | `a5@0x10C6` | 1 byte | the **selector stream** (raw byte per ring-cycle walk). See §7 for the boundary. |
| 0x507C5 | ≥64 B | `a5@0x13E` | 1 byte | segment → tilemap0 index `a5@0x1386`. |
| 0x3951C | 12 B/e | `a5@0x1386` | 12 B | tilemap0 source descriptor base. |
| 0x1691C … 0x3725C | 0x22C0 each | `a5@0x13E×0x40` | 0x40 B/seg | the 16 tilemap1 strip-descriptor source tables. |

## 2. Stage/scene selection chain

Runs in scene-(re)init routine **0x0501E2** (← `jsr` 0x045316, the stage handler; only invoked at scene transitions, NOT every frame — MAME-verified). Body: `…0x050202 bsr 0x502CC (selection) · 0x050206 bsr 0x503DC (fill)…`.

```
prologue 0x050248:
  a5@0x13E  = byte[0x5073A + a5@0x1242]        ; STAGE -> segment index          [0x05025A]
  (membership test vs word table 0x502AC (0xFFFF-term): match -> sound 0x25 via 0x3A116,
   a5@0x12EE=0xFF, a5@0x1360=1 ; else a5@0x1360=0xFF)                            [0x050260..]
  a5@0x1386 = byte[0x507C5 + a5@0x13E]         ; segment -> tilemap0 index       [0x0502A6]
  a5@0x10F4=0 ; a5@0x10CA=0 ; a5@0x10F6=0                                        [0x0502BE..]
selection 0x0502CC:
  a5@0x1000..0x103C = {0x1691C..0x3725C}[i] + a5@0x13E*0x40    ; 16 strip-source bases
  a5@0x10FC = 0x3951C + a5@0x1386*0x0C                          ; tilemap0 source base
  a5@0x10C6 = 0x50F6B + byte[0x50EE0 + a5@0x13E]                ; MAP-STREAM POINTER  [0x0503D6]
fill 0x0503DC:
  bsr 0x55904  (rebuild 16 descriptors + load first selector a5@0x10A8 = *(byte)a5@0x10C6)
  bsr 0x55C2E ; <64-iteration fill>  (see scene_initialization_assembly.md)
```

### §2a Stage-LUT extent and correlation (machine-enumerated)
`0x5073A` is a **139-byte** table (it abuts the segment→tm0 LUT at 0x507C5), values 0..0x8A(138); `a5@0x13E` is bounded `≤ 0x8A` (proven: `0x05069A cmpi.w #0x8A,a5@0x13E ; bhi`). It has **48 distinct segment targets**. Correlation with the 18 proven event records (indices 0–137):
- **All 18 post-event segments (16,22,23,39,45,46,62,68,69,85,91,92,108,114,115,131,137,138) ARE stage-LUT targets** (post-event ⊆ stage targets).
- But **only 18 of the 48 targets are post-event; the other 30** (0,4,8,0xC,0x13,0x19,0x1D,…) are non-event segment starts.
So: every event boundary is also a stage boundary, but stage boundaries are a **superset** — the stage LUT is a general stage→segment map, **not** "exactly post-event segments."

## 3. Byte-value table

| Value | Type | Consumer(s) | Publishes? | Effect |
|---|---|---|---|---|
| **0** | direction: horizontal | dir 0x0557C4; publish 0x055948 → strip_A | YES (drives ring cycle) | camera X crossings publish; tilemap1 X-scroll a5@0x10AE |
| **1** | direction: vertical A | dir 0x0556A6; publish → strip_B | YES | camera Y crossings publish; tilemap1 Y-scroll a5@0x10B0 |
| **2** | direction: vertical B | dir 0x055738; cell producer skips sub-index reversal (0x055A2E/0x055A88) | YES | vertical, opposite ring offset/sign |
| **4** | event | 0x05127C (if a5@0x10BE≥0xD8 → a5@0x1376/0x1384/0x13C6=1); 0x05274C → 0x527CC a5@0x10E8=7 | **no** (freezes walk) | position-gated spawn/scene flags; enables event engine |
| **5** | event | 0x051284 (a5@0x10BE≥0x50); 0x052754 → 0x527CC a5@0x10E8=7 | **no** | as 4, different gate. *(absent from the observed stream)* |
| **6** | event | 0x05275C → 0x527CC a5@0x10E8=7 | **no** | enables event engine (no handler-A gate) |
| **7** | **no consumer established** | — (a5@0x10A8 is only `cmpi`'d vs 0/1/2/4/5/6 and copied to 0x132C; no range check, no table dispatch) | no | **observed value 7; no consumer established.** Appears only as the 2nd byte of `[00,07]` records; whether it is ever loaded as a live selector is unproven. |
| **0xFF** | candidate sentinel/boundary | none (not compared against a5@0x10A8) | no | one byte at stream offset 0x9E, after the last record. Candidate sentinel — not a proven terminator (no code reads it as a selector). |

## 4. Record format — VARIABLE-LENGTH (machine-derived)

**The 0x50EE0 LUT defines variable-length records, not one-byte-per-index.** Record length = `LUT[i+1] − LUT[i]`, which is defined only for **indices 0–137** (index 138 has no next entry). 

**Proven (indices 0–137):** **120 length-1 records + 18 length-2 records.** Every length-2 record is **`[direction ∈ {0,1}, event ∈ {4,6,7}]`** — a direction byte immediately followed by an event byte. There are no direction+direction or event+event pairs. So a `+2` LUT entry = **one direction record with a trailing event byte** (not two independent commands, not a transition record of another shape). Length-2 inventory (indices 0–137): `[00 04]`×6, `[01 06]`×4, `[00 06]`×2, `[00 07]`×6.

**Record 138 (candidate):** starts at offset 0x9C with first byte **0x00** (proven); the following ROM bytes are `07 FF 0C`. Its length is **unresolved** (no LUT[139]); candidate final form `[00 07]` (matching the preceding `[00,07]` pattern), with `0xFF` a candidate sentinel. See §7.

See the full table (§4a). The `next`/`len` columns for row 138 show the candidate `[00 07]` interpretation.

### §4a Full segment-record table
| idx | start | next | len | bytes | first | extra | stage-LUT target |
|---|---|---|---|---|---|---|---|
| 0 | 0x00 | 0x01 | 1 | 00 | 0x00 | — | Y |
| 1 | 0x01 | 0x02 | 1 | 00 | 0x00 | — |  |
| 2 | 0x02 | 0x03 | 1 | 00 | 0x00 | — |  |
| 3 | 0x03 | 0x04 | 1 | 00 | 0x00 | — |  |
| 4 | 0x04 | 0x05 | 1 | 00 | 0x00 | — | Y |
| 5 | 0x05 | 0x06 | 1 | 00 | 0x00 | — |  |
| 6 | 0x06 | 0x07 | 1 | 00 | 0x00 | — |  |
| 7 | 0x07 | 0x08 | 1 | 00 | 0x00 | — |  |
| 8 | 0x08 | 0x09 | 1 | 00 | 0x00 | — | Y |
| 9 | 0x09 | 0x0A | 1 | 00 | 0x00 | — |  |
| 10 | 0x0A | 0x0B | 1 | 00 | 0x00 | — |  |
| 11 | 0x0B | 0x0C | 1 | 00 | 0x00 | — |  |
| 12 | 0x0C | 0x0D | 1 | 00 | 0x00 | — | Y |
| 13 | 0x0D | 0x0E | 1 | 00 | 0x00 | — |  |
| 14 | 0x0E | 0x0F | 1 | 00 | 0x00 | — |  |
| 15 | 0x0F | 0x11 | 2 | 00 04 | 0x00 | 0x04 |  |
| 16 | 0x11 | 0x12 | 1 | 00 | 0x00 | — | Y |
| 17 | 0x12 | 0x13 | 1 | 01 | 0x01 | — |  |
| 18 | 0x13 | 0x14 | 1 | 00 | 0x00 | — |  |
| 19 | 0x14 | 0x15 | 1 | 00 | 0x00 | — | Y |
| 20 | 0x15 | 0x16 | 1 | 00 | 0x00 | — |  |
| 21 | 0x16 | 0x18 | 2 | 01 06 | 0x01 | 0x06 |  |
| 22 | 0x18 | 0x1A | 2 | 00 07 | 0x00 | 0x07 | Y |
| 23 | 0x1A | 0x1B | 1 | 00 | 0x00 | — | Y |
| 24 | 0x1B | 0x1C | 1 | 00 | 0x00 | — |  |
| 25 | 0x1C | 0x1D | 1 | 00 | 0x00 | — | Y |
| 26 | 0x1D | 0x1E | 1 | 00 | 0x00 | — |  |
| 27 | 0x1E | 0x1F | 1 | 00 | 0x00 | — |  |
| 28 | 0x1F | 0x20 | 1 | 00 | 0x00 | — |  |
| 29 | 0x20 | 0x21 | 1 | 00 | 0x00 | — | Y |
| 30 | 0x21 | 0x22 | 1 | 00 | 0x00 | — |  |
| 31 | 0x22 | 0x23 | 1 | 00 | 0x00 | — |  |
| 32 | 0x23 | 0x24 | 1 | 00 | 0x00 | — | Y |
| 33 | 0x24 | 0x25 | 1 | 00 | 0x00 | — |  |
| 34 | 0x25 | 0x26 | 1 | 00 | 0x00 | — | Y |
| 35 | 0x26 | 0x27 | 1 | 00 | 0x00 | — |  |
| 36 | 0x27 | 0x28 | 1 | 00 | 0x00 | — | Y |
| 37 | 0x28 | 0x29 | 1 | 00 | 0x00 | — |  |
| 38 | 0x29 | 0x2B | 2 | 00 04 | 0x00 | 0x04 |  |
| 39 | 0x2B | 0x2C | 1 | 00 | 0x00 | — | Y |
| 40 | 0x2C | 0x2D | 1 | 00 | 0x00 | — |  |
| 41 | 0x2D | 0x2E | 1 | 00 | 0x00 | — |  |
| 42 | 0x2E | 0x2F | 1 | 00 | 0x00 | — | Y |
| 43 | 0x2F | 0x30 | 1 | 01 | 0x01 | — |  |
| 44 | 0x30 | 0x32 | 2 | 01 06 | 0x01 | 0x06 |  |
| 45 | 0x32 | 0x34 | 2 | 00 07 | 0x00 | 0x07 | Y |
| 46 | 0x34 | 0x35 | 1 | 00 | 0x00 | — | Y |
| 47 | 0x35 | 0x36 | 1 | 00 | 0x00 | — |  |
| 48 | 0x36 | 0x37 | 1 | 00 | 0x00 | — |  |
| 49 | 0x37 | 0x38 | 1 | 00 | 0x00 | — |  |
| 50 | 0x38 | 0x39 | 1 | 00 | 0x00 | — | Y |
| 51 | 0x39 | 0x3A | 1 | 00 | 0x00 | — |  |
| 52 | 0x3A | 0x3B | 1 | 00 | 0x00 | — | Y |
| 53 | 0x3B | 0x3C | 1 | 00 | 0x00 | — |  |
| 54 | 0x3C | 0x3D | 1 | 00 | 0x00 | — |  |
| 55 | 0x3D | 0x3E | 1 | 00 | 0x00 | — |  |
| 56 | 0x3E | 0x3F | 1 | 00 | 0x00 | — |  |
| 57 | 0x3F | 0x40 | 1 | 00 | 0x00 | — | Y |
| 58 | 0x40 | 0x41 | 1 | 00 | 0x00 | — |  |
| 59 | 0x41 | 0x42 | 1 | 00 | 0x00 | — |  |
| 60 | 0x42 | 0x43 | 1 | 00 | 0x00 | — |  |
| 61 | 0x43 | 0x45 | 2 | 00 04 | 0x00 | 0x04 |  |
| 62 | 0x45 | 0x46 | 1 | 00 | 0x00 | — | Y |
| 63 | 0x46 | 0x47 | 1 | 00 | 0x00 | — |  |
| 64 | 0x47 | 0x48 | 1 | 00 | 0x00 | — |  |
| 65 | 0x48 | 0x49 | 1 | 01 | 0x01 | — | Y |
| 66 | 0x49 | 0x4A | 1 | 01 | 0x01 | — |  |
| 67 | 0x4A | 0x4C | 2 | 01 06 | 0x01 | 0x06 |  |
| 68 | 0x4C | 0x4E | 2 | 00 07 | 0x00 | 0x07 |  |
| 69 | 0x4E | 0x4F | 1 | 00 | 0x00 | — |  |
| 70 | 0x4F | 0x50 | 1 | 00 | 0x00 | — |  |
| 71 | 0x50 | 0x51 | 1 | 00 | 0x00 | — |  |
| 72 | 0x51 | 0x52 | 1 | 00 | 0x00 | — |  |
| 73 | 0x52 | 0x53 | 1 | 00 | 0x00 | — |  |
| 74 | 0x53 | 0x54 | 1 | 00 | 0x00 | — |  |
| 75 | 0x54 | 0x55 | 1 | 00 | 0x00 | — |  |
| 76 | 0x55 | 0x56 | 1 | 00 | 0x00 | — |  |
| 77 | 0x56 | 0x57 | 1 | 00 | 0x00 | — |  |
| 78 | 0x57 | 0x58 | 1 | 00 | 0x00 | — |  |
| 79 | 0x58 | 0x59 | 1 | 00 | 0x00 | — |  |
| 80 | 0x59 | 0x5A | 1 | 00 | 0x00 | — |  |
| 81 | 0x5A | 0x5B | 1 | 00 | 0x00 | — |  |
| 82 | 0x5B | 0x5C | 1 | 00 | 0x00 | — |  |
| 83 | 0x5C | 0x5D | 1 | 00 | 0x00 | — |  |
| 84 | 0x5D | 0x5F | 2 | 00 04 | 0x00 | 0x04 |  |
| 85 | 0x5F | 0x60 | 1 | 00 | 0x00 | — |  |
| 86 | 0x60 | 0x61 | 1 | 00 | 0x00 | — |  |
| 87 | 0x61 | 0x62 | 1 | 00 | 0x00 | — |  |
| 88 | 0x62 | 0x63 | 1 | 00 | 0x00 | — |  |
| 89 | 0x63 | 0x64 | 1 | 00 | 0x00 | — |  |
| 90 | 0x64 | 0x66 | 2 | 01 06 | 0x01 | 0x06 |  |
| 91 | 0x66 | 0x68 | 2 | 00 07 | 0x00 | 0x07 |  |
| 92 | 0x68 | 0x69 | 1 | 00 | 0x00 | — |  |
| 93 | 0x69 | 0x6A | 1 | 00 | 0x00 | — |  |
| 94 | 0x6A | 0x6B | 1 | 00 | 0x00 | — |  |
| 95 | 0x6B | 0x6C | 1 | 00 | 0x00 | — |  |
| 96 | 0x6C | 0x6D | 1 | 00 | 0x00 | — |  |
| 97 | 0x6D | 0x6E | 1 | 00 | 0x00 | — |  |
| 98 | 0x6E | 0x6F | 1 | 00 | 0x00 | — |  |
| 99 | 0x6F | 0x70 | 1 | 00 | 0x00 | — |  |
| 100 | 0x70 | 0x71 | 1 | 00 | 0x00 | — |  |
| 101 | 0x71 | 0x72 | 1 | 00 | 0x00 | — |  |
| 102 | 0x72 | 0x73 | 1 | 00 | 0x00 | — |  |
| 103 | 0x73 | 0x74 | 1 | 00 | 0x00 | — |  |
| 104 | 0x74 | 0x75 | 1 | 00 | 0x00 | — |  |
| 105 | 0x75 | 0x76 | 1 | 00 | 0x00 | — |  |
| 106 | 0x76 | 0x77 | 1 | 00 | 0x00 | — |  |
| 107 | 0x77 | 0x79 | 2 | 00 04 | 0x00 | 0x04 |  |
| 108 | 0x79 | 0x7A | 1 | 00 | 0x00 | — |  |
| 109 | 0x7A | 0x7B | 1 | 00 | 0x00 | — |  |
| 110 | 0x7B | 0x7C | 1 | 02 | 0x02 | — |  |
| 111 | 0x7C | 0x7D | 1 | 00 | 0x00 | — |  |
| 112 | 0x7D | 0x7E | 1 | 02 | 0x02 | — |  |
| 113 | 0x7E | 0x80 | 2 | 00 06 | 0x00 | 0x06 |  |
| 114 | 0x80 | 0x82 | 2 | 00 07 | 0x00 | 0x07 |  |
| 115 | 0x82 | 0x83 | 1 | 00 | 0x00 | — |  |
| 116 | 0x83 | 0x84 | 1 | 00 | 0x00 | — |  |
| 117 | 0x84 | 0x85 | 1 | 00 | 0x00 | — |  |
| 118 | 0x85 | 0x86 | 1 | 00 | 0x00 | — |  |
| 119 | 0x86 | 0x87 | 1 | 00 | 0x00 | — |  |
| 120 | 0x87 | 0x88 | 1 | 00 | 0x00 | — |  |
| 121 | 0x88 | 0x89 | 1 | 00 | 0x00 | — |  |
| 122 | 0x89 | 0x8A | 1 | 00 | 0x00 | — |  |
| 123 | 0x8A | 0x8B | 1 | 00 | 0x00 | — |  |
| 124 | 0x8B | 0x8C | 1 | 00 | 0x00 | — |  |
| 125 | 0x8C | 0x8D | 1 | 00 | 0x00 | — |  |
| 126 | 0x8D | 0x8E | 1 | 00 | 0x00 | — |  |
| 127 | 0x8E | 0x8F | 1 | 00 | 0x00 | — |  |
| 128 | 0x8F | 0x90 | 1 | 00 | 0x00 | — |  |
| 129 | 0x90 | 0x91 | 1 | 00 | 0x00 | — |  |
| 130 | 0x91 | 0x93 | 2 | 00 04 | 0x00 | 0x04 |  |
| 131 | 0x93 | 0x94 | 1 | 00 | 0x00 | — |  |
| 132 | 0x94 | 0x95 | 1 | 00 | 0x00 | — |  |
| 133 | 0x95 | 0x96 | 1 | 02 | 0x02 | — |  |
| 134 | 0x96 | 0x97 | 1 | 00 | 0x00 | — |  |
| 135 | 0x97 | 0x98 | 1 | 00 | 0x00 | — |  |
| 136 | 0x98 | 0x9A | 2 | 00 06 | 0x00 | 0x06 |  |
| 137 | 0x9A | 0x9C | 2 | 00 07 | 0x00 | 0x07 |  |
| 138 | 0x9C | *0x9E?* | *2?* | 00 [07?] | 0x00 | *0x07?* |  |

*(**Record 138 is the only unproven row.** Proven: it starts at offset 0x9C with first byte `0x00`. There is no LUT[139], so its length is undefined by the table; the `[00 07]` form, the `0x9E` "next", and the `0xFF` sentinel are **candidates** inferred from the surrounding `[00,07]`+`FF` structure, not proven. Rows 0–137 have proven lengths from LUT deltas.)*

## 5. Publication unit — DIRECTION selectors only

Proven for **direction selectors 0/1/2** (they publish):
- `a5@0x10CA` 0→3 (+1/publish, reset at 0x0558C6 when ==4) = 4 columns/group; `a5@0x10CC` 0→15 (+1 at 0x0558B2, → 0x0558E0 when ==16) = 16 groups ⇒ **64 publications per direction byte**.
- Each publication = one strip = 16 descriptor iters × 4 cells = 64 cells ⇒ 64 publications = 4096 cells = one 64×64 ring traversal = **512 px** in that direction.
- On the 64th, **0x0558E0** advances: `a5@0x10C6 += 1`, `a5@0x132C = old sel`, `a5@0x10A8 = next byte`, `a5@0x13E += 1`.

**Event/transition values 4/5/6/7 do NOT publish** and therefore do NOT satisfy this mechanism — a direction selector remains active for 64 publications, but an event byte governs 0 publications and instead **freezes** the walk. 0xFF is never loaded as a live selector.

**MAME confirmation (one focused trace):** in-game, corrupting `a5@0x10C6` mid-frame persisted (it is not recomputed from the LUT each frame), and changing `a5@0x13E` alone did not move `a5@0x10C6`. This proves the byte pointer is driven by the `+1` walk (0x0558E4) and re-seeded only at scene transitions — not derived from a5@0x13E every frame.

## 6. Event-byte completion & next-direction selection (PROVEN part + DOWNGRADED part)

**Proven (opcodes):**
1. **Direction → event.** A direction record's 64-publication cycle completes; 0x0558E0's `+1` walk lands `a5@0x10C6` on the record's **event byte** (2nd byte of a length-2 record) and `a5@0x13E` has advanced to the next segment index. The event byte loads as `a5@0x10A8`.
2. **Event freeze.** Being 4/5/6, it matches no direction branch → the dispatcher latches pending bits (a5@0x10D0 bit4–7) and **publishes nothing** → `a5@0x10CC` never reaches 16 → 0x0558E0 never fires → **the walk is frozen on the event byte** (a frozen walk cannot self-advance — `+1` only fires on ring completion). The event handlers set `a5@0x10E8 = 7` (0x0527CC) and position-gated flags (0x05127C); the enemy/scene engine reads a5@0x10E8 at 0x0540CC/0x051598/0x0517D8.
3. **Only re-seed path.** `a5@0x10C6` has exactly two writers: the `+1` walk (0x0558E4) and the scene-init re-seed (0x0503D6). **Scene-init 0x0501E2 has exactly one caller — `0x045316` (jsr)** — and there it computes the stage `a5@0x1242` from a config word (`0x0452C0: a5@0x1242 = (~*0x5FF9E & 7)×0x17 [+0x16][+0x10]`), then `jsr 0x0501E2` → 0x050202 `map_select_pointers` (re-seed) + 0x050206 fill. So the re-seed exists and lands `a5@0x10C6 = 0x50F6B + 0x50EE0[a5@0x13E]`.

**DOWNGRADED (not proven — strongly-supported model):** that an in-level *event/encounter completion* is what reaches 0x045316/scene-init. **No event-completion → 0x045316 call path is traced**; 0x045316's stage is config-derived, not an event-driven increment. The correlation supports the model — every event boundary is a stage boundary (post-event ⊆ stage-LUT targets, §2a), and the seg-LUT `+2` delta at each `[dir,event]` record makes a re-seed via `LUT[a5@0x13E]` skip the consumed event byte — but the exact route from "encounter done" to the pointer re-seed is **UNRESOLVED** (it lives in the level-progression / enemy subsystem, out of scope). Candidate routes: (a) the event marks a stage boundary and the stage-advance path re-enters 0x045316; (b) a pending-bit-driven catch-up. Neither is opcode-traced here.

## 7. Stream boundary & length (machine-calculated)

Separated by confidence:
- First stream address: **0x050F6B** (offset 0x00) — proven.
- **Definitely covered through offset 0x9C** (record 138's first byte 0x00): **157 bytes** (0x00–0x9C).
- Record 138 second byte: offset 0x9D @0x051008 = **0x07** — *candidate* (no LUT[139] proves it belongs to record 138; inferred from the `[00,07]` pattern).
- **Candidate sentinel:** offset 0x9E @0x051009 = **0xFF** — not consumed as a selector; a boundary/sentinel candidate, **not a proven terminator**.
- Offset 0x9F @0x05100A = 0x0C — begins the following (unidentified) structure; **excluded**.
- **Length: 157 bytes proven** (through 0x9C). **158 data bytes only if the candidate `0x07` second byte of record 138 is accepted** (159 including the 0xFF sentinel).
- Histogram over 0x00–0x9D (158 bytes, i.e. incl. the candidate 0x07): `00`×128, `01`×8, `02`×3, `04`×6, `06`×6, `07`×7. (Over the 157 proven bytes 0x00–0x9C: `07`×6.) Adding the 0xFF sentinel: `+ FF`×1.

## 8. Exact remaining unknowns

1. **Event-completion → pointer-re-seed route** (§6 downgrade): the exact opcode path from an in-level encounter completing to scene-init 0x0501E2 (the only pointer re-seed). Scene-init's sole caller 0x045316 is a config-driven level-start; no event→0x045316 chain is traced. Lives in the level-progression/enemy subsystem (out of scope).
2. **Record 138 length & the 0xFF boundary** (§7): whether `0x07` belongs to record 138 and `0xFF` is the sentinel is inferred, not proven by a LUT entry or a consumer bound.
3. **Encounter-completion condition** for each event value — enemy/scene subsystem behind 0x0540CC/0x527D4/0x528CA/0x5288C/0x52816. Out of scope.
4. **Selector 5** live behaviour — handlers exist (0x051284/0x052754) but the value never appears in the 0x50F6B stream.
5. **Selector 7** — no consumer established; whether ever loaded as a live selector is unproven.
6. **Stage cardinality** — the 0x5073A table is 139 bytes with 48 distinct targets (max 0x8A=138); the exact per-stage segment span is level-progression detail.
7. The **0x502AC** special-segment word set (membership → sound 0x25 / a5@0x1360 / a5@0x12EE).
