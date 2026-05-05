# [Cody — Build 55 Palette Fix Shape Evidence]

Type: Read-only evidence collection  
Build context: rastan-direct Build 0054 (post-D6-fix, post-v3.2 dispatch)

## §1.1 — Caller graph for `arcade_pc 0x59AD4`

Search result (`build/maincpu.disasm.txt`) for calls to `0x59AD4`:

- `0x511BC` `jsr 0x59ad4`
- `0x511D0` `jsr 0x59ad4`
- `0x56136` `jsr 0x59ad4`
- `0x5614A` `jsr 0x59ad4`
- `0x5615C` `jsr 0x59ad4`
- `0x5616E` `jsr 0x59ad4`
- `0x56184` `jsr 0x59ad4`
- `0x56198` `jsr 0x59ad4`
- `0x575FE` `bsrw 0x59ad4`
- `0x57610` `bsrw 0x59ad4`
- `0x57816` `jsr 0x59ad4`
- `0x5782A` `jsr 0x59ad4`
- `0x5783E` `jsr 0x59ad4`
- `0x57850` `jsr 0x59ad4`
- `0x598C2` `bsrw 0x59ad4`
- `0x598F0` `bsrw 0x59ad4`
- `0x5999A` `bsrw 0x59ad4`
- `0x599F0` `bsrw 0x59ad4`
- `0x59A20` `bsrw 0x59ad4`
- `0x59A50` `bsrw 0x59ad4`
- `0x59A80` `bsrw 0x59ad4`
- `0x59E06` `jsr 0x59ad4`
- `0x5A364` `jsr 0x59ad4`
- `0x5A3BA` `jsr 0x59ad4`
- `0x5A3EC` `jsr 0x59ad4`
- `0x5A41E` `jsr 0x59ad4`
- `0x5A450` `jsr 0x59ad4`
- `0x5A488` `jsr 0x59ad4`
- `0x5A49C` `jsr 0x59ad4`
- `0x5A4B0` `jsr 0x59ad4`

Total direct callsites observed: **30**.

Evidence:
- [build/maincpu.disasm.txt:102366](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:102366)
- [build/maincpu.disasm.txt:107909](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:107909)
- [build/maincpu.disasm.txt:109681](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:109681)
- [build/maincpu.disasm.txt:112815](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:112815)
- [build/maincpu.disasm.txt:113267](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:113267)
- [build/maincpu.disasm.txt:113664](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:113664)

State-context grouping from caller neighborhoods:
- Title/frontend cluster: `0x511BC`, `0x511D0`, `0x5A364`, `0x5A3BA`, `0x5A3EC`, `0x5A41E`, `0x5A450`, `0x5A488`, `0x5A49C`, `0x5A4B0`
- Gameplay cluster: `0x56136..0x56198`, `0x575FE`, `0x57610`, `0x57816..0x57850`, `0x598C2..0x59A80`, `0x59E06`

Evidence:
- [build/maincpu.disasm.txt:102355](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:102355)
- [build/maincpu.disasm.txt:107906](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:107906)
- [build/maincpu.disasm.txt:109673](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:109673)
- [build/maincpu.disasm.txt:112801](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:112801)
- [build/maincpu.disasm.txt:113255](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:113255)
- [build/maincpu.disasm.txt:113661](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:113661)

## §1.2 — `arcade_pc 0x59AD4` body inspection

Disassembly body (`0x59AD4..0x59B18`):

```asm
59ad4: c2fc 0020       muluw #32,%d1
59ad8: d0c1            addaw %d1,%a0
59ada: eb48            lslw #5,%d0
59adc: 4246            clrw %d6
59ade: 227c 0020 0000  moveal #2097152,%a1
59ae4: d2c0            addaw %d0,%a1
59ae6: 3218            movew %a0@+,%d1
59ae8: 0c41 ffff       cmpiw #-1,%d1
59aec: 671e            beqs 0x59b0c
59aee: 3401            movew %d1,%d2
59af0: 3601            movew %d1,%d3
59af2: 0241 0f00       andiw #3840,%d1
59af6: ee49            lsrw #7,%d1
59af8: 0242 00f0       andiw #240,%d2
59afc: e54a            lslw #2,%d2
59afe: 0243 000f       andiw #15,%d3
59b02: e14b            lslw #8,%d3
59b04: e74b            lslw #3,%d3
59b06: d641            addw %d1,%d3
59b08: d642            addw %d2,%d3
59b0a: 3283            movew %d3,%a1@
59b0c: 0c46 000f       cmpiw #15,%d6
59b10: 6706            beqs 0x59b18
59b12: 5246            addqw #1,%d6
59b14: 5489            addql #2,%a1
59b16: 60ce            bras 0x59ae6
59b18: 4e75            rts
```

Evidence:
- [build/maincpu.disasm.txt:112973](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:112973)

Observed entry/flow:
- Entry registers used: `A0`, `D0`, `D1`
- Destination setup: `A1 := 0x200000 + (D0 << 5)`
- Source row setup: `A0 := A0 + (D1 * 32)`
- Per-iteration read/convert/write with `D6` loop counter to 16 entries (`0..15`)
- Sentinel behavior: source `0xFFFF` skips the write for that element
- Exit opcode: `rts`

CLCS expression comparison (`((raw >> 1) & 0x000E) | ((raw >> 2) & 0x00E0) | ((raw >> 3) & 0x0E00)`):
- Result from body inspection: **different bit-operation sequence in this routine**

Evidence for project CLCS expression reference:
- [apps/rastan/src/main.c:1020](/home/tighe/projects/rastan-genesis/apps/rastan/src/main.c:1020)
- [tools/translation/postpatch_startup_rom.py:1547](/home/tighe/projects/rastan-genesis/tools/translation/postpatch_startup_rom.py:1547)

## §1.3 — Inputs to `0x59AD4` per caller

Observed setup patterns at callsites:

- `0x511BC`: `A0=0x511DA`, `D0=0x0004`, `D1=0x0000`
- `0x511D0`: `A0=0x511DA`, `D0=0x0003`, `D1=0x0001`

Evidence:
- [build/maincpu.disasm.txt:102363](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:102363)

- `0x56136`: `A0=0x5649E`, `D0=0x0004`, `D1=0x0000`
- `0x5614A`: `A0=0x564FE`, `D0=0x0005`, `D1=0x0000`
- `0x5615C`: `A0=0x564FE`, `D0=0x0033`, `D1=0x0000`
- `0x5616E`: `A0=0x564FE`, `D0=0x0043`, `D1=0x0000`
- `0x56184`: `A0=0x5649E`, `D0=0x0033`, `D1=0x0004`
- `0x56198`: `A0=0x5651E`, `D0=0x0033`, `D1=0x0000`

Evidence:
- [build/maincpu.disasm.txt:107906](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:107906)

- `0x575FE`: `A0=0x57F2A`, `D0=0x0004`, `D1=%a5@(5098)`
- `0x57610`: `A0=0x5802A`, `D0=0x0005`, `D1=%a5@(5098)`

Evidence:
- [build/maincpu.disasm.txt:109678](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:109678)

- `0x57816`: `A0=0x57F2A`, `D0=0x0004`, `D1=0x0000`
- `0x5782A`: `A0=0x5802A`, `D0=0x0005`, `D1=0x0000`
- `0x5783E`: `A0=0x5812A`, `D0=0x0006`, `D1=0x0000`
- `0x57850`: `A0=0x5814A`, `D0=0x0041`, `D1=0x0000`

Evidence:
- [build/maincpu.disasm.txt:109831](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:109831)

- `0x598C2`: `A0=0x59910`, `D0` from table at `0x59950`, `D1=0x0000`
- `0x598F0`: `A0=0x59910`, `D0` from table at `0x59950`, `D1=0x0001`

Evidence:
- [build/maincpu.disasm.txt:112807](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:112807)

- `0x5999A`: `A0=0x59B1A`, `D0` from table `0x59A98 + index`, `D1=(%a5@(4840)>>3)` when low-3 bits are zero
- `0x599F0`: `A0=0x59B7A`, `D0` from table `0x59AA4 + index`, `D1=(%a5@(4842)>>3)`
- `0x59A20`: same `A0=0x59B7A`, `D1=((%a5@(4842)>>3)+3)&3`
- `0x59A50`: same `A0=0x59B7A`, `D1=((%a5@(4842)>>3)+2)&3`
- `0x59A80`: same `A0=0x59B7A`, `D1=((%a5@(4842)>>3)+1)&3`

Evidence:
- [build/maincpu.disasm.txt:112872](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:112872)

- `0x59E06`: `D1=%a5@(5038)`; caller chain includes `0x59E6C` for `A0` setup and `0x59E50` for `D0` setup before the call

Evidence:
- [build/maincpu.disasm.txt:113267](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:113267)

- `0x5A364`: `A0=0x5A6FA`, `D0=0x0001`, `D1=0x0000`
- `0x5A3BA`: `A0=0x5A73A`, `D0=0x0001`, `D1=0x0000`
- `0x5A3EC`: `A0=0x5A75A`, `D0=0x0001`, `D1=0x0000`
- `0x5A41E`: `A0=0x5A75A`, `D0=0x0001`, `D1=0x0000`
- `0x5A450`: `A0=0x5A71A`, `D0=0x0001`, `D1=0x0000`
- `0x5A488`: `A0=0x5A77A`, `D0=0x0003`, `D1=0x0000`
- `0x5A49C`: `A0=0x5A77A`, `D0=0x0004`, `D1=0x0001`
- `0x5A4B0`: `A0=0x5A77A`, `D0=0x0005`, `D1=0x0002`

Evidence:
- [build/maincpu.disasm.txt:113661](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:113661)

Grouped patterns:
- Shared source tables observed: `0x564FE`, `0x57F2A`, `0x5802A`, `0x59B7A`, `0x5A77A`
- Shared destination bank values observed: `D0=1,3,4,5,6,0x33,0x41,0x43` plus table-driven values in `0x598C2..0x59A80`
- Count/index input (`D1`) observed both constant (`0,1,2,4`) and runtime-derived (`%a5` state words)

## §1.4 — Coverage check

Searches for direct palette-RAM region writes in `build/maincpu.disasm.txt` found writes in `0x200000` space outside `0x59AD4` callsites, including:

- `0x264` routine writing converted words to `%a0` after `lea 0x200000,%a0`
- `0x3AB00` direct write `movew #1023,0x200022`
- `0x3AEB6/0x3AEBC` and `0x3AEDA/0x3AEE0` direct read/write of `0x200000`
- `0x45DAE` and `0x45DE4` copy paths into `0x200000` and `0x200600`

Evidence:
- [build/maincpu.disasm.txt:188](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:188)
- [build/maincpu.disasm.txt:73730](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:73730)
- [build/maincpu.disasm.txt:73995](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:73995)
- [build/maincpu.disasm.txt:88358](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:88358)

Observed coverage result: **`0x59AD4` is not the sole writer into the `0x200000` palette region.**

## §1.5 — Bank/offset semantics

Observed from `0x59AD4`:
- Destination formula: `A1 := 0x200000 + (D0 << 5)`
- Step size per `D0`: 32 bytes (16 words)

Evidence:
- [build/maincpu.disasm.txt:112975](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:112975)
- [build/maincpu.disasm.txt:112977](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:112977)

Observed caller-side `D0` range includes values above 3:
- Explicit immediate values include `0x33`, `0x41`, `0x43`

Evidence:
- [build/maincpu.disasm.txt:107915](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:107915)
- [build/maincpu.disasm.txt:109844](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:109844)
- [build/maincpu.disasm.txt:107919](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:107919)

Max explicit `D0` immediate observed at callsites: **`0x43` (67)**.

## §1.6 — Partial vs full update

Observed from `0x59AD4` body and caller usage:
- One invocation iterates 16 entries (`D6` from `0` to `15`) and advances destination by 2 bytes each loop
- Caller routines commonly issue multiple calls with different `D0`/`D1` pairs

Evidence:
- [build/maincpu.disasm.txt:112994](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:112994)
- [build/maincpu.disasm.txt:113725](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:113725)
- [build/maincpu.disasm.txt:107906](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:107906)

Observed update granularity: **mixed partial-bank updates (16-word unit per call, multi-call sequences by state).**

## §1.7 — Fix shape recommendation

Recommendation from observed artifact behavior: **`0x59AD4` runtime hook**.

Cited reasoning from artifacts:
- `0x59AD4` has 30 callsites across frontend/title and gameplay paths (not a single scene-load-only site)
- Call inputs are state-dependent in multiple caller clusters (`D0` and `D1` both dynamic in several paths)
- `D0` values observed above 3 (`0x33`, `0x41`, `0x43`), and updates occur in partial-bank units
- Additional direct palette-region writes exist outside `0x59AD4`, so static scene-only payloads do not directly cover all observed palette-region write behavior

Evidence:
- [build/maincpu.disasm.txt:102366](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:102366)
- [build/maincpu.disasm.txt:113267](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:113267)
- [build/maincpu.disasm.txt:107915](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:107915)
- [build/maincpu.disasm.txt:73995](/home/tighe/projects/rastan-genesis/build/maincpu.disasm.txt:73995)

## Phase 2 — Integrity

- §1.1 caller graph for `0x59AD4`: complete; caller count: **30**
- §1.2 `0x59AD4` body inspected: **YES**; conversion matches project CLCS expression: **NO (different sequence observed in this routine)**
- §1.3 caller inputs documented: **YES**
- §1.4 coverage check (`0x59AD4` sole chokepoint): **NO**; bypass paths listed in §1.4
- §1.5 bank/offset semantics: max explicit `D0` immediate observed = **0x43**; mapping requires decision
- §1.6 update granularity: **mixed partial updates**
- §1.7 fix shape recommendation: **RUNTIME HOOK**
- All findings cited from artifacts: **YES**
- No implementation: **YES**
- No external sources: **YES**
- Neutral framing maintained: **YES**
- No source/spec/tool modifications: **YES**
