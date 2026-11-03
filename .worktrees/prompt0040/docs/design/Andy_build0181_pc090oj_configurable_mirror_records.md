# Andy — Build 0181: Configurable PC090OJ Mirror Record Count (256 / 128 / 80)

**Date:** 2026-07-16
**Type:** Build-system infrastructure + diagnostic builds + runtime evidence
**Baseline:** Build 0180 `dist/rastan-direct/rastan_direct_video_test_build_0180.bin` SHA `d016cacd6b318c949875bccb992ecff7633def06fc8e57f62c89600967b054bf`, counter 180.
**Produced (all GATE_PASS):**
- Build 0181 (default RECORDS=256) SHA `1ef9085ed272edacd5d73edf806eab867c1687aa61d502227d6f898fd0ae6abc`, size 1,582,840
- Build 0182 (diagnostic RECORDS=128) SHA `5f7264dbac1b8cb084568f740f4ef21070463ea806d48219bd663b183841e7c0`, size 1,582,840
- Build 0183 (diagnostic RECORDS=80) SHA `defe5173ae57b4e55f9fe35cbbe783cc0f453f4275e6527dfcbe80bbdad4c68c`, size 1,582,840

Counter 180 -> 183. Builds are deterministic (repeat builds reproduce identical SHAs).

## Repository state detected
- Build counter: 180 (before this task); latest numbered ROM Build 0180.
- Build 0180 is current; not visually accepted as a meaningful performance fix.
- **Build 0179 IS an accidental duplicate of Build 0178** (both SHA `998cc3c92b710d79eeaea08e49ea288f4757d03662692797361142bf186cdd96`).
- Working tree carries uncommitted diagnostic work (Builds 0164..0180 accumulated); tree builds to Build 0180.

## Goal
Add a durable, Make-overridable configuration for PC090OJ helper mirror sizing (not a disposable hack). Default stays 256; support diagnostic 128 and 80 (and future 160/192/etc.) without hand-editing scattered assembly constants.

## Mechanism (durable)
- `apps/rastan-direct/Makefile`: `PC090OJ_MIRROR_RECORDS ?= 256` (override with `make release PC090OJ_MIRROR_RECORDS=128`).
- A generated include `out/pc090oj_config.inc` is written from the Make variable every build (tied to the existing FORCE_ASM_REBUILD), defining:
  `.equ PC090OJ_MIRROR_RECORDS, N` ; `.equ PC090OJ_MIRROR_BYTES, (N*8)` ; `.equ PC090OJ_BITSET_BYTES, ((N+7)/8)`.
- `ASFLAGS` gains `-I out`; `pc090oj_hooks.s` does `.include "pc090oj_config.inc"` and depends on it.
- To change the default persistently: edit the one Makefile line. To experiment: pass the Make variable.

## What the config drives (no scattered constants remain)
- `.bss` array sizes: `pc090oj_object_ram` and `pc090oj_mirror_shadow` = `PC090OJ_MIRROR_BYTES`; `pc090oj_candidate_bitset`, `represented_records`, `waiting_records` = `PC090OJ_BITSET_BYTES`; `record_to_slot` = `PC090OJ_MIRROR_RECORDS`. (`used_sat_slots`/`worklist_entry_for_slot` stay 80-slot sized — Genesis SAT capacity, not record count.)
- All record loop bounds, `pc090oj_candidate_count` seed, bitset-clear loops, mirror shadow copy/scan, and the "record not found" sentinel (formerly hardcoded 256) derive from the config.
- `PC090OJ_HW_ACTIVE_END = PC090OJ_HW_BASE + PC090OJ_MIRROR_BYTES`, so the address-based mirror writers (`mirror_write_word/byte_a1_d0`) auto-reject out-of-range records when N<256.

## Safety (N<256 cannot corrupt memory)
Record-based mirror writers (`.Lpc090oj_emit_slot`, `.Lpc090oj_family_apply_record`) gained explicit `cmpi #PC090OJ_MIRROR_RECORDS` bounds checks: records >= N increment `pc090oj_producer_oob_count` and are dropped (no write past the smaller mirror array). This is the only behavioral code delta vs Build 0180 and is inert at the default 256 (no record >= 256 exists). Canonical coverage 0x1826D0 -> 0x1826F8 (+0x28, the bounds-check code); opcode_replace count unchanged (151).

## Diagnostic results (MAME, gameplay frames, matched coin/start)
| RECORDS | Build | represented | oob dropped | VINT-service rate (1.0 = 60Hz) |
|---|---|---:|---:|---:|
| 256 (default) | 0181 | 28 | 0 | 0.477 |
| 128 | 0182 | 22 | 7340 | 0.569 |
| 80 | 0183 | 26 | 16162 | 0.563 |

- Default 256 is functionally identical to Build 0180: `oob_dropped=0`, represented=28.
- Capping to 128 or 80 improves the effective VBlank-service rate ~19% (0.477 -> ~0.57, i.e. ~28.6Hz -> ~34Hz) while sprite representation is roughly preserved (22..28). 128 and 80 are near-identical in rate (diminishing returns below ~128).
- The 16162 (N=80) / 7340 (N=128) dropped writes confirm the arcade addresses many records the Genesis never needs to display: the active/visible sprite set fits within ~80 records. Dropped records include the high-index player-block duplicates (120..137, 92..95, from the Build 0164 0x041F5E mapping) and other out-of-window records.
- represented single-frame snapshots vary with timing (128 read 22, 80 read 26); both retain the low-index player/foreground sprite records (< 80).

## Interpretation
This is a durable tuning lever, not a one-off. It confirms Tighe's hypothesis that the game almost never needs 256 mirrored records, and that mirror scan/process cost is a real (if now-secondary, after Builds 0177/0180) slowdown contributor. As input/collision/enemy-spawn/scroll become functional, the safe cap can be re-tuned (160/192/etc.) with a single Make variable. It does not by itself fix the black bars, the frozen actor progression (no enemies / uncontrollable), or the arcade-VINT/main-loop cost — those remain separate roots.

## Not changed / not chased
Palette route (Build 0175) untouched; Build 0180 SAT-dirty gating and Builds 0171/0172 projections preserved; no input/control, collision, sky-reset, D00298, continue/game-over, Exodus, PC080SN, or enemy-visibility work. Enemy-code records 0x03E8..0x03F5 (mirror records 30..43) are < 80 so they survive all three caps; their offscreen-Y decode is unchanged by this task and not pursued here.

## Files changed
apps/rastan-direct/Makefile, apps/rastan-direct/src/pc090oj_hooks.s, tools/translation/postpatch_startup_rom.py + verify_canonical_rom.py (coverage 0x1826D0 -> 0x1826F8, paired), docs/design/Andy_build0181_pc090oj_configurable_mirror_records.md, OPEN_ISSUES.md, AGENTS_LOG.md, KNOWN_FINDINGS.md. Generated: out/pc090oj_config.inc (build artifact).
