# Per-Round Boss Actor Map (static arcade decompilation)

**Built on Cody's verified render model (`Cody_actor_render_verification.md` / `_verified.json`).**
Static from `build/regions/maincpu.bin`; ORIGINAL ARCADE MAME SAT/palette used only via Cody's
captures. No ROM build, no Genesis change, counter 360. R1/R5 incorporate Cody's proven data;
R2/R3/R4/R6 are statically traced here.

## The mechanism (proven)

Boss body spawn trigger: **`0x45330 → 0x4449E`**. At `0x4449E`:
```
d0 = round (A5+0x118) - 1
a0 = 0x444E0 + d0                 ; per-round boss-body-type table
if d0 == 5 (round 6): a4 = A5+0x648, +0x38 := 2 (compositor 2)
else               : a4 = A5+0x708, +0x38 := 1 (compositor 1)
a4+0x06 := *a0                    ; BODY record type  (table 0x444E0 = 0E 13 14 15 10 17)
call 0x453A8 → 0x4543E            ; load base +0x1E from table 0x45592[(type-8)]
```
Body record type → base graphics via `0x45592` (8-byte records, index = type−8). Boss body update
state machine: `0x42220` (dispatch on `+0x06`); update dispatch `0x46BE0` (special-cases R1→`0x4CE6C`,
R5→`0x4E13C`). Body enters the state machine via `0x4221A → jmp 0x46BE0`.

## Round → boss BODY (PROVEN from table 0x444E0 + table 0x45592)

| Round | Trigger/progression | BODY record type | BODY base | Slot | Compositor(+0x38) | Body update | Components | Confidence |
|---|---|---|---|---|---|---|---|---|
| 1 | round-tail; `0x45330→0x4449E` | 14 (0x0E) | **0x061D** | A5+0x708 | 1 (tab 0x4771C) | 0x46BE0→0x4CE6C | type 15 / base 0x061D via **0x457D0** | PROVEN (Cody SAT: prog 0x47908, line 0xF pool 11) |
| 2 | round-tail; same trigger | 19 (0x13) | **0x0753** | A5+0x708 | 1 | (per-round; not 0x46BE0) | none seen in body state (0x42318) | BODY PROVEN; components/palette PENDING |
| 3 | round-tail; same trigger | 20 (0x14) | **0x082C** | A5+0x708 | 1 | (per-round) | none seen in body state (0x42310) | BODY PROVEN; components/palette PENDING |
| 4 | round-tail; same trigger | 21 (0x15) | **0x07BF** | A5+0x708 | 1 | (per-round) | none seen in body state (0x42308) | BODY PROVEN; components/palette PENDING |
| 5 | round-tail; same trigger | 16 (0x10) | **0x0988** | A5+0x708 | 1 | 0x46BE0→0x4E13C | 5× type 17 / base 0x0988 via **0x423B2** (from 0x42376) | PROVEN (Cody SAT: prog 0x490DE, line 0xF pool 3) |
| 6 | round-tail; same trigger | 23 (0x17) | **0x0B35** | A5+0x648 | 2 (tab 0x3F0CE) | 0x42340 state | 4-part via **0x423F4** (from 0x42364): types 23/24/25/26 = 0x0B35/0x0AED/0x0CCB/0x0BEB | BODY PROVEN; multi-segment; palette PENDING |

Table `0x444E0` = `0E 13 14 15 10 17`; verified `0x45592` bases: 14→0x061D, 19→0x0753, 20→0x082C,
21→0x07BF, 16→0x0988, 23→0x0B35.

## Boss body state machine 0x42220 (dispatch on +0x06 record type)
- type 14 (R1) → 0x42326: body pos X=80,Y=132; state +0x05:=16.
- type 16 (R5) → 0x4236A: pos X=272,Y=216; `bsr 0x423B2` (5 children @A5+0x5C8, type17→0x0988); `bsr 0x42380`.
- type 19 (R2) → 0x42318: pos Y=158,X=240.
- type 20 (R3) → 0x42310: pos Y=135,X=240.
- type 21 (R4) → 0x42308: pos Y=151,X=240.
- type 23 (R6) → 0x42340: pos X=304,Y=232; clear A5+0x648..0x688; `bsr 0x423F4` (4 children @A5+0x648, types 23-26 → 0x0B35/0x0AED/0x0CCB/0x0BEB).
- component path: when +0x06==15 (R1 components), reached via 0x421FC→0x42214→`bsr 0x457D0`.

## Palettes
- R1 body: line 0xF, pool 11 (Cody, MAME-verified). R5 body: line 0xF, pool 3 (Cody).
- R2/R3/R4/R6 bodies: palette assigned via `0x45684` boss branch (table `0x456EC`, indexed
  variant×18 + (round-1)×3 + compAdj). My static index guess did NOT match Cody's captured line 0xF
  for R1/R5, so the live variant matters — **boss body palette for R2/R3/R4/R6 = PENDING a Cody-style
  capture**; not asserting a line here.

## New graphics bases exposed (added to census; NOT field enemies)
Boss bodies: 0x0753 (R2), 0x082C (R3), 0x07BF (R4), 0x0B35 (R6). R6 components: 0x0AED, 0x0CCB,
0x0BEB. (0x061D, 0x0988 already corrected per Cody.) Also present in table 0x45592 as scripted/other
record types 27-31: 0x09EA, 0x0547, 0x0D56, 0x07C8 (roles not yet proven; not promoted to enemies).

## Exact next unresolved PC/table
- R2/R3/R4 boss UPDATE routine (0x46BE0 only branches R1/R5): trace the per-round boss update for
  types 19/20/21 — start at the actor-state dispatch reaching `0x4221A` and the `0x469FE`/`0x46A12`/
  `0x46A5E` round-compare block (handles R5/R6), and find the R2/R3/R4 equivalent.
- R2/R3/R4 component/child creation (none in the body positioning state): confirm single-body vs
  children created inside their update routine.
- Boss body palette line for R2/R3/R4/R6: capture via Cody's `arcade_actor_renderer_verify.lua`
  (do not modify it) or resolve the live `(0x752,A4)` variant feeding `0x456EC`.
