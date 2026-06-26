# Cody - Build 0102 BlastEm Bookmark BM-010

**Date:** 2026-06-25
**Type:** Hybrid verification + diagnostic bisection
**Build context:** Build 0100 -> 0101 -> 0102, `rastan-direct`
**Scope:** Revert BM-009, audit interval `runtime_genesis_pc 0x70000..0x7186C`, insert one BM-010 bookmark. No HV fix, no sanitizer, no VDP rewrite, no display-origin/title/exception work.

## Phase 0 Baseline

Classification: **EXTENDING** (OPEN-017 diagnostic bisection). Relevant priors: KF-004/KF-006 address discipline as context; OPEN-017 is active for BlastEm/Nomad behavior; OPEN-005 is HV-counter historical context; OPEN-001 is rendering context; OPEN-015 is not touched. HIGH-hazard findings touched: none contradicted. Deferred appendix: none directly relevant. Contradiction of CONFIRMED/STRONG finding: **NONE**. STOP triggered in Phase 0: **NO**.

Architecture compliance: **CONFIRMED**. Bookmark activators are Rule 10 diagnostic exceptions only. No production Genesis-owned loop or lifecycle was added; no fix was attempted.

Confirmed user evidence consumed:

- BM-008 at `runtime_genesis_pc 0x00070000`: HIT in BlastEm, parked at helper `0x00071EB4`, no HV fatal first.
- BM-009 at `runtime_genesis_pc 0x0007186C`: MISS in BlastEm, `Illegal write to HV Counter port 8` before bookmark.
- Resulting bracket: `0x00070000 < offending HV access < 0x0007186C`.

## Build 0101 - BM-009 Revert

Command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release BOOKMARK_REVERT=BM-009
```

Result: **PASS**.

- Build: `0101`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0101.bin`
- SHA256: `b8e16f7c670dc8225584679b88d5a4ea71efb0dc5938d38420fca524ec71db72`
- Canonical Build 0097/0099 SHA256: `b8e16f7c670dc8225584679b88d5a4ea71efb0dc5938d38420fca524ec71db72`
- Byte-identical comparison with Build 0097: PASS (`cmp = 0`)
- Active bookmark state after revert: absent (`build/rastan-direct/active_bookmark_baseline.json` deleted)
- Restored bytes at `0x0007186C`: `33f900c0000800ff678c`
- Helper bytes at `0x00071EB4`: `60fe`

## Focused Static Audit: `0x70000..0x7186C`

Address-map segment for interval targets: `build/rastan-direct/address_map.json` maps `0x070000..0x17CD28` as `genesis_only`, tag `wrapper`. No arcade equivalent is claimed for BM-010.

### Computed-write candidates to `HW 0x00C00008`

**Earliest strong computed-write candidate:** NONE FOUND.

The audit found canonical VDP writes and staging/helper code, but no strong computed write to `HW 0x00C00008` before `0x7186C`:

| runtime_genesis_pc | Instruction / path | EA reasoning | Candidate verdict |
|---|---|---|---|
| `0x70088` | `movew %d2,0xc00004` | Absolute VDP control-port register write in `vdp_set_reg` helper; target is `HW 0xC00004`, not offset 8. | Not HV-offset candidate |
| `0x700AE` | `movel %d1,0xc00004` | Absolute VDP control-port address setup helper; target is `HW 0xC00004`, not offset 8. | Not HV-offset candidate |
| `0x70122`, `0x70160`, `0x701AE`, `0x701E4`, `0x70204`, `0x70214`, `0x7022C`, `0x7023A` | Absolute writes to `0xc00000` | Canonical VBlank commit data/scroll/palette writes to VDP data port. No `0xC00008` effective address. | Not HV-offset candidate |
| `0x70242..0x70658` | BG/FG staging helpers | Compare arcade PC080SN C-window ranges, translate to `staged_bg_buffer`/`staged_fg_buffer`, dirty flags. Writes such as `movew %d3,%fp@(0,%d0:w)` target WRAM staging, not VDP/HV. | Not HW write |
| `0x7065E..0x70CFE` | FG/text helper paths | Range checks against `0x00C0xxxx`, LUT conversion, then WRAM staging. The midpoint area around `0x70C36` is helper setup before `bsrw 0x7097A`, not a VDP/HV write. | Not strong HV candidate |
| `0x7156C..0x7165A` | Sprite staging helper | Writes to WRAM sprite metadata/SAT staging; displaced `a0@(8)` writes are against WRAM structures, not a VDP base. | Not HW write |
| `0x717D8..0x7186A` | `genesistan_hook_3ad44_dispatch` front end / else path | Routes PC080SN/PC090OJ ranges to staging helpers or records diagnostic state into WRAM at `0xff674a+`; no VDP/HV write before `0x7186C`. | Not HV-offset candidate |
| `0x7186C` | `movew 0xc00008,0xff678c` | Literal HV read, not write; BM-009 MISS proved offending write occurs earlier in BlastEm. | Excluded by user evidence |

Since no strong computed-write candidate was identified, BM-010 uses the prompt's fallback: the nearest safe instruction boundary to midpoint `runtime_genesis_pc ~0x70C36`.

## Build 0102 - BM-010 Insert

BM-010 target:

- `runtime_genesis_pc`: `0x00070C36`
- `genesis_rom_offset`: `0x00070C36`
- JSON segment: `genesis_only`, `0x070000..0x17CD28`, tag `wrapper`
- Arcade equivalent: none; native Genesis helper/wrapper code.
- Original bytes: `2449d4fc0002`
- Original instructions: `movea.l %a1,%a2`; `adda.w #2,%a2`
- Reason: midpoint bisection target after no strong computed-write candidate was found; parks before the nearby helper call at `0x70C3C`.

Command:

```bash
source tools/setup_env.sh && make -C apps/rastan-direct release
```

Result: **PASS**.

- Build: `0102`
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0102.bin`
- SHA256: `12104def7693c611a63e3ee1c8284218f64b77dc2fcdd75de64dbc03a5f643f6`
- Helper symbol: `genesistan_diag_bookmark`
- Helper runtime address: `0x00071EB4`
- Helper bytes: `60fe`
- Activator bytes at `0x00070C36`: `4ef900071eb4`
- Active bookmark state: present, cycle `BM-010`, pre-insert counter `101`
- One-bookmark max: honored; BM-009 was reverted before BM-010 was inserted.

Bookmark-stage invariant model:

- `bookmarks_v2` activator applied by bookmark stage, outside opcode_replace segment coverage accounting.
- `opcode_replace` patched-site count: `96` (canonical)
- `total_genesis_bytes_covered`: `0x17CD28` (canonical)
- Patch counts: `{'opcode_replace_and_rom_opcode_replace': 96}`

## User Test Instructions

Run Build 0102 in BlastEm:

```text
b 0x71EB4
c
```

- HIT: breakpoint hits `0x71EB4` / `bra #-2`, no HV fatal first. New interval: `(0x70C36, 0x7186C)`.
- MISS: BlastEm emits `Illegal write to HV Counter port 8` before the breakpoint. New interval: `(0x70000, 0x70C36)`.

Do not use `p/x $pc` as the authoritative PC; use the breakpoint/disassembly line if exposed. If MISS, report the exact fatal text.

## Rule 10

Build 0102 is diagnostic-only. The immediate next ROM-producing task must revert BM-010 unless Tighe explicitly directs otherwise.

## Non-Actions

No HV fix, no illegal-port sanitizer, no VDP rewrite, no display-origin/title work, no exception/OPEN-015 work, no red-TAITO/SCORE-HUD/CREDIT work.

## OPEN / KNOWN_FINDINGS Impact

- Open issues touched: OPEN-017 (active), OPEN-005 (context), OPEN-001 (context), OPEN-015 (not touched)
- New issues opened: NONE
- Issues closed: NONE
- KNOWN_FINDINGS impact: Option A - no new finding to index; this is diagnostic bisection and root cause is not proven.

## STOP

STOP triggered: **NO**.
