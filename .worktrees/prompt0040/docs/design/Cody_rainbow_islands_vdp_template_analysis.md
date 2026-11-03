# Cody Rainbow Islands VDP Template Analysis

## 1. Executive Summary
This audit disassembles `Rainbow Islands - The Story of Bubble Bobble 2 (JU) [p1].bin` and extracts a strict video-control template for `apps/rastan-direct`.

Confirmed findings:
- Vector ownership and direct hardware ownership are fully in ROM code (no SGDK runtime layer).
- VBlank handler at `0x000380` is a commit pipeline, while the game state machine runs outside VBlank.
- Tilemap, sprite, palette, and scroll values are staged in WRAM and published to VDP during VBlank.
- Rainbow uses fixed WRAM contracts and mode-specific flag words that are game-specific and not copy-safe as-is.

## 2. Identified Rainbow Islands Video / VDP Routines

| Routine | ROM Address | Evidence | Responsibility |
|---|---:|---|---|
| Reset entry | `0x000204` | Vector table entry at `0x000004 = 0x00000204`; disassembly starts at `0x204` | Boot ownership entry |
| TMSS gate/write | `0x000204`-`0x000230` | `tstl 0xa10008`; conditional `movel #0x53454741,0xA14000` | TMSS compliance before display setup |
| VDP init table loader | `0x000434` | `lea 0xC00004`; loop writes 19 words from table at `0x00048E`; stores copy to `0xFFFFF624` | Boot-time VDP register initialization |
| VDP/VRAM clear | `0x00046E`-`0x00048C` | `movel #0x40000000,0xC00004`; long word loop to `0xC00000` | Full VRAM clear |
| VBlank ISR | `0x000380` | Vector table entry at `0x000078 = 0x00000380`; ends with `rte` | Per-frame commit orchestrator |
| HBlank ISR | `0x00041C` | Vector table entry at `0x000070 = 0x0000041C`; body is `rte` | No active HBlank logic |
| Palette commit | `0x00085A` | Flag gate on `0xFFFFF690`; DMA register setup writes (`0x93xx`..`0x97xx`) then wait loop on VDP status bit | CRAM publish during VBlank |
| Sprite/SAT commit | `0x0006B0` | Uses SAT shadow at `0xFFFFF800`; sets DMA regs and triggers SAT transfer, then waits | Sprite hardware publish during VBlank |
| Tilemap strip commit dispatcher | `0x00073C` | Flag gate on `0xFFFFF63C`; reads source ptr `0xFFFFF644` and destination command `0xFFFFF648`; calls `0x1A70` | Plane update publish control |
| Tilemap strip writer | `0x001A70` | Direct writes to `0xC00004/0xC00000`; writes 40 words per strip and advances VDP destination | Strip/partial tilemap commit engine |
| Additional VRAM stream commit | `0x0007BE` | Flag gate on `0xFFFFF680`; descriptor-driven VDP stream writes ending with clear of `F680` | Auxiliary VRAM update path in VBlank |
| Scroll commit | `0x0003D8`-`0x0003E8` | `movel #0x40000010,0xC00004`; `movel 0xFFFFF630,0xC00000` | H/V scroll publish during VBlank |

## 3. VBlank Ownership Model
- VBlank vector is owned by ROM routine `0x000380`.
- Execution inside VBlank:
  1. optional display-off bracket using reg1 mirror (`0xFFFFF624`) at `0x3A4`-`0x3AC`
  2. `bsr 0x085A` palette commit
  3. `bsr 0x06B0` sprite/SAT commit
  4. `bsr 0x073C` tilemap strip commit
  5. `bsr 0x07BE` auxiliary VRAM stream commit
  6. scroll long write from `0xFFFFF630`
  7. housekeeping/frame counter and exit
- Execution outside VBlank:
  - Main state machine loop at `0x11D2` and its mode branches (`0x1204`, `0x1278`, `0x12F2`, `0x13A2`, etc.).
  - Game logic/state progression and content preparation paths.
- Game logic inside VBlank: NO.
- VBlank is commit-only: YES.

## 4. Tilemap / Plane Commit Model
- Staging contract:
  - `0xFFFFF63C`: tilemap commit request mode/flag.
  - `0xFFFFF644`: source pointer for tile words.
  - `0xFFFFF648`: VDP destination command base.
- Commit path:
  - `0x73C` selects mode (`F63C == 1` or `2`), calls `0x1A70`.
  - `0x1A70` writes direct to VDP control/data ports.
- Write granularity:
  - Strip/partial writes (`40` words per inner loop, destination stepping each strip), not full-plane DMA each frame.
- Mechanism:
  - CPU direct port writes (`0xC00004`, `0xC00000`).
- Tilemap commit model identified: YES.

## 5. Sprite / SAT Commit Model
- Staging:
  - Sprite entries are maintained in WRAM SAT shadow around `0xFFFFF800`.
  - Link bytes are rebuilt each frame in `0x6B0` before hardware publish.
- Hardware publish:
  - `0x6B0` configures DMA registers and issues SAT destination command; waits for DMA completion by polling VDP status.
- Frequency:
  - Commit function is called once per VBlank by `0x380`.
- Separation:
  - State prep/shadow maintenance exists before the DMA trigger.
  - Hardware publication is isolated to VBlank routine chain.
- Sprite commit model identified: YES.

## 6. Palette / CRAM Commit Model
- Staging and trigger:
  - Palette commit flag at `0xFFFFF690` controls publication in `0x85A`.
  - Producer routines (for example `0x15EE`, `0x163C`, `0x1678`) update palette staging blocks and set `F690=1`.
- Hardware publish:
  - `0x85A` writes VDP DMA registers and CRAM-target command words, then waits for DMA completion.
- Timing:
  - Commit executes in VBlank chain only.
- Conversion:
  - Palette effect logic is pre-applied in staging routines (`0x16AE` family); commit routine performs hardware transfer.
- Palette commit model identified: YES.

## 7. Scroll Commit Model
- Staging:
  - Scroll long value is maintained in WRAM at `0xFFFFF630`.
- Commit:
  - VBlank writes control command `0x40000010` then writes staged long to data port.
- Grouping:
  - Horizontal and vertical components are packed and committed together via single long write.
- Order:
  - Executed after palette/sprite/tilemap/aux commits in VBlank at `0x3D8`.
- Scroll commit model identified: YES.

## 8. Template-Relevant Patterns for `rastan-direct`

| Pattern | Directly reusable for Rastan | Why | Required adaptation |
|---|---|---|---|
| ROM-owned vectors and direct boot | YES | Matches no-SGDK/no-C target | Replace Rainbow vector map with Rastan-direct vector map and entry symbols |
| TMSS gate before hardware init | YES | Hardware-safe startup sequence | Keep same policy with Rastan-direct boot registers |
| Single VBlank commit orchestrator | YES | Enforces one hardware writer per frame | Use Rastan-specific commit calls and flags |
| Display off/on bracketing around heavy commit spans | YES | Prevents partial-frame presentation artifacts during bulk writes | Tune bracket usage to Rastan commit volume |
| WRAM-staged state + VBlank publish | YES | Separates logic from hardware publication | Define Rastan staging structs and ownership contract |
| Tilemap strip commit engine (CPU port writes) | YES | Supports partial map updates with deterministic order | Recompute destination/base commands for Rastan plane layout |
| SAT shadow + VBlank SAT publish | YES | Keeps sprite prep outside VBlank and publish in VBlank | Map Rastan sprite format to Genesis SAT layout |
| Flag-driven optional palette/VRAM commit | YES | Avoids unnecessary commits and keeps phase boundaries explicit | Replace Rainbow flag words with Rastan-direct flag words |
| Rainbow WRAM addresses (`F63C/F644/F648/F690/F680/F800`) | NO | These addresses are Rainbow-specific contracts | Allocate new Rastan-direct WRAM map |
| Rainbow mode/state machine dispatch blocks | NO | Game-state logic is title-specific | Preserve only phase architecture, not state code |

## 9. What Must Not Be Copied Blindly
- Do not copy Rainbow WRAM flag addresses, shadow layouts, or descriptor tables verbatim.
- Do not copy Rainbow plane destination constants (`0x40000003`, `0x50000003`, etc.) without recalculating Rastan plane bases.
- Do not copy Rainbow sprite link rebuild assumptions (entry counts, termination pattern, parity gates) without validating Rastan sprite requirements.
- Do not copy Rainbow auxiliary VRAM stream logic (`0x7BE` path) without mapping Rastan content descriptors.
- Do not copy Rainbow mode-dispatch/state words (`F600/F602/...`) into Rastan-direct architecture.

## 10. Single Final Template Recommendation
Adopt Rainbow Islands’ **ROM-owned direct-boot + single VBlank commit orchestrator + WRAM-staged video state contract** as the `apps/rastan-direct` template, and adapt only the staging schemas, VDP destination constants, and content descriptor formats to Rastan data/layout requirements.

## 11. Final Verdict
Rainbow Islands provides a valid direct-execution template for `rastan-direct` when reused at the architectural pattern level (ownership, timing, phase boundaries) and not at the game-specific constant/structure level.
