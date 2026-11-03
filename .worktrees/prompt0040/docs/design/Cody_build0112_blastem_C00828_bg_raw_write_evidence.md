# Cody - Build 0112 BlastEm C00828 BG Raw-Write Evidence

**Date:** 2026-06-28
**Type:** Runtime evidence + static correlation only
**Baseline ROM:** `dist/rastan-direct/rastan_direct_video_test_build_0112.bin`
**SHA256:** `024241b2378dba68102637c368bc92d5edc41b2b30776363a96144146dfe215d`
**Scope:** Evidence only. No source/spec/tool/Makefile/ROM/build changes. No bookmark. No fix design or implementation. No score/round or OPEN-015 work.

## Phase 0

Read: `RULES.md`, `ARCHITECTURE.md`, `AGENTS_LOG.md` latest context, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`, `CLOSED_ISSUES.md` context.

Architecture compliance: PASS. The observed write is arcade-code intent copied into the Genesis runtime; the task only records evidence and does not alter execution.

Address discipline: PASS. All `runtime_genesis_pc` to `arcade_pc` correlations below are exact lookups through `build/rastan-direct/address_map.json`. No arithmetic offset is used as proof.

Relevant priors:

- KF-032: raw copied PC080SN writes must route through Genesis staging, not VDP mirror.
- KF-036: helper work-RAM sources must use mapped Genesis WRAM base; no work-RAM source is involved in this C00828 write.
- OPEN-018: broad raw PC080SN routing class remains open.
- OPEN-022: C00828 strict-target freeze placeholder opened before this evidence pass.
- CLOSED-015/016/017: high-score fall-through, high-score FG producer route, and NAME source-base fixes remain closed and are not reopened.

## Evidence Artifacts

Trace directory:

`states/traces/build_0112_c00828_bg_raw_write_evidence_20260628_164543/`

Files:

- `c00828_watch_exact.cmd` - MAME native debugger command file.
- `native_debug_trace.log` - full instruction trace and event log.
- `mame_stdout.log` / `mame_stderr.log` - run output.
- `item_text_source_at_wp.bin` - MAME text dump of the source region at the watchpoint.

The MAME Genesis-driver run exited via debugger after the exact watchpoint fired. No ROM diagnostics were inserted.

## Runtime Watchpoint Result

Exact watchpoint:

`HW_ADDRESS 0x00C00828`, size 2, write.

Watchpoint event:

```text
EVENT WP_C00828 cyc=77597656 pc=0565BC addr=00C00828 data=0000 mem=0000
  d0=00000041 d1=00000000 d2=00000000 d3=00000020 d4=0000000C
  a0=0005692B a1=00C00828 a2=00C00828 a5=00FF0000 a6=00FF0298
  sp=00FEFFE6 sr=2704 s0=0002 s2=0002 s4=0006 cnt=0000
  stack0=00056240 stack4=00056054 stack8=0003A8B8
```

MAME reports the post-instruction callback PC `runtime_genesis_pc 0x000565BC`. The faulting write instruction is therefore the previous instruction:

```asm
runtime_genesis_pc 0x000565B8: 32c1   move.w %d1,(%a1)+
```

This is the attr-word half of a two-word PC080SN text/cell writer. At the event:

- `%a1 = HW_ADDRESS 0x00C00828`
- `%d1 = 0x0000` (attribute word)
- `%d0 = 0x0041` (`'A'`, the first source glyph byte after load)
- source pointer after read `%a0 = runtime_genesis_pc/data 0x0005692B`
- caller return `stack0 = runtime_genesis_pc 0x00056240`

The immediately following code-word write would be:

```asm
runtime_genesis_pc 0x000565BE: 32c0   move.w %d0,(%a1)+
```

to `HW_ADDRESS 0x00C0082A`, writing glyph code `0x0041` for `A`.

## Address-Map Correlation

Exact JSON mappings from `build/rastan-direct/address_map.json`:

| runtime_genesis_pc / data | arcade_pc / data | kind |
|---|---|---|
| `0x0005622C` | `0x0005602C` | `arcade_copy` |
| `0x00056232` | `0x00056032` | `arcade_copy` |
| `0x0005623C` | `0x0005603C` | `arcade_copy` |
| `0x000565A6` | `0x000563A6` | `arcade_copy` |
| `0x000565B8` | `0x000563B8` | `arcade_copy` |
| `0x000565BE` | `0x000563BE` | `arcade_copy` |
| `0x000565CC` | `0x000563CC` | `arcade_copy` |
| `0x0005692A` | `0x0005672A` | `arcade_copy` data |
| `0x00056B7D` | `0x0005697D` | `arcade_copy` data |
| `0x0003A8B2` | `0x0003A6B2` | `arcade_copy` |

## Call Chain / Page Handler

Runtime event sequence around the transition:

```text
EVENT HIGH_MASTER_ADVANCE_03AD48 cyc=55318060 pc=03AD4A sr=2700 s0=0000 s2=0001 s4=0002 cnt=00A0
EVENT ITEM_PAGE_ENTRY_5622C cyc=77597558 pc=05622E sr=2704 ... s0=0002 s2=0002 s4=0006 cnt=0000
EVENT ITEM_A1_LOAD_56232 cyc=77597570 pc=056234 a0=0005692A a1_before=00C08E74 ...
EVENT ITEM_CALL_WRITER_5623C cyc=77597590 pc=05623E a0=0005692A a1=00C00828 ...
EVENT WRITER_ENTRY_565A6 cyc=77597608 pc=0565A8 a0=0005692A a1=00C00828 ... stack0=00056240
EVENT WRITER_ATTR_565B8 cyc=77597656 pc=0565BA a0=0005692B a1=00C00828 d0=00000041 d1=00000000 ...
EVENT WP_C00828 cyc=77597656 pc=0565BC addr=00C00828 data=0000 ...
```

Static surrounding code:

```asm
runtime_genesis_pc 0x0003A8B2: jsr 0x55fdc
...
runtime_genesis_pc 0x00056048: cmpi.w #2,%a5@(0x13aa)
runtime_genesis_pc 0x00056050: bsr.w 0x5622c
runtime_genesis_pc 0x00056054: move.l #0x00c00400,%a5@(0x10a0)
runtime_genesis_pc 0x0005605c: move.w #3,%a5@(0x13aa)
...
runtime_genesis_pc 0x0005622c: movea.l #0x0005692a,%a0
runtime_genesis_pc 0x00056232: movea.l #0x00c00828,%a1
runtime_genesis_pc 0x00056238: move.w #0,%d1
runtime_genesis_pc 0x0005623c: bsr.w 0x565a6
runtime_genesis_pc 0x00056240: movea.l #0x00056226,%a0
runtime_genesis_pc 0x00056246: movea.l #0x00d00170,%a1
runtime_genesis_pc 0x0005624c: bsr.w 0x56314
```

Interpretation: the write belongs to the item-description attract page initialization, not the high-score screen itself. The item page state at the watchpoint is `%a5@(0)=2`, `%a5@(2)=2`, `%a5@(4)=6`, `%a5@(44)=0`.

The code first emits a PC080SN BG text block starting at `HW_ADDRESS 0x00C00828`, then sets up a PC090OJ/sprite-object path at `HW_ADDRESS 0x00D00170` through the patched `runtime_genesis_pc 0x00056314` site. This is not the high-score FG producer and not the high-score clear/fill path.

## BG Decode

Base: `HW_ADDRESS 0x00C00000` (PC080SN BG plane/page region).

Formula:

- offset = `addr - 0x00C00000`
- cell = `offset >> 2`
- col = `cell & 0x3F`
- row = `(cell >> 6) & 0x1F`
- attr word is at `base + cell*4`; code word is at `base + cell*4 + 2`

For `HW_ADDRESS 0x00C00828`:

- offset = `0x0828`
- cell = `0x20A`
- row = `8`
- col = `10`
- half = attr word

## Source Text / Full Write Range

The source stream starts at `runtime_genesis_pc/data 0x0005692A` (mapped to `arcade_pc/data 0x0005672A`). It is ROM text data, not work-RAM. The writer walks bytes until `0x00`; byte `0xFF` advances the target by `0x200` bytes, i.e. the next PC080SN row pair in this layout.

The source decodes to item-description text. First rows:

```text
AXE         INCREASES YOUR     
            OFFENSIVE POWER.   
 
HAMMER      EXTENDS YOUR       
            OFFENSIVE RANGE.   
 
FIRE SWORD  INCREASES OFFENSIVE
            POWER BY SHOOTING  
            FIRE BALL.         
```

Full decoded write summary from the Build 0112 ROM bytes:

- source span: `runtime_genesis_pc/data 0x0005692A..0x00056B7D`
- cells emitted: `568`
- page/row advances (`0xFF`): `27`
- first write: attr at `HW_ADDRESS 0x00C00828`, row 8 col 10
- last decoded write: code at `HW_ADDRESS 0x00C03E2A`, row 30 col 10
- target region: PC080SN BG plane/page, `HW_ADDRESS 0x00C00828..0x00C03E2A`

Representative row ranges:

| text row | target range | decoded text |
|---:|---|---|
| 8 | `0x00C00828..0x00C008A2` | `AXE         INCREASES YOUR     ` |
| 10 | `0x00C00A28..0x00C00AA2` | `            OFFENSIVE POWER.   ` |
| 14 | `0x00C00E28..0x00C00EA2` | `HAMMER      EXTENDS YOUR       ` |
| 16 | `0x00C01028..0x00C010A2` | `            OFFENSIVE RANGE.   ` |
| 20 | `0x00C01428..0x00C014A2` | `FIRE SWORD  INCREASES OFFENSIVE` |
| 22 | `0x00C01628..0x00C016A2` | `            POWER BY SHOOTING  ` |
| 24 | `0x00C01828..0x00C018A2` | `            FIRE BALL.         ` |
| 28 | `0x00C01C28..0x00C01CA2` | `SHIELD      REDUCES DAMAGE     ` |
| 30 | `0x00C01E28..0x00C01EA2` | `            FROM ENEMY ATTACKS.` |
| 2 | `0x00C02228..0x00C022A2` | `MANTLE      REDUCES ENEMY      ` |
| 4 | `0x00C02428..0x00C024A2` | `            DAMAGE BY ONE HALF.` |
| 8 | `0x00C02828..0x00C028A2` | `ARMATURE    REDUCES ALL DAMAGE ` |
| 10 | `0x00C02A28..0x00C02AA2` | `            FROM ENEMY.        ` |
| 14 | `0x00C02E28..0x00C02EA2` | `MEDICINE    POWER INCREASE.    ` |
| 18 | `0x00C03228..0x00C032A2` | `POISON      POWER REDUCE.      ` |
| 22 | `0x00C03628..0x00C036A2` | `GOLD SHEEP  MAXIMUM POWER      ` |
| 24 | `0x00C03828..0x00C038A2` | `            INCREASE.          ` |
| 28 | `0x00C03C28..0x00C03CA2` | `JEWEL       BONUS POINTS.      ` |

This is a content producer, not a clear/fill. It emits attr/code word pairs for item-description text.

## Data Source

No work-RAM source is used for the C00828 text producer. The source is ROM data at `runtime_genesis_pc/data 0x0005692A` mapped exactly to `arcade_pc/data 0x0005672A` by `address_map.json`.

KF-036 source-base risk is therefore not active for this writer: there is no literal `0x0010xxxx` work-RAM read to correct. The raw-write defect is the destination path, not the source path.

## Known / Deferred Comparison

This C00828 writer does **not** match the explicitly listed OPEN-018 remaining candidates:

- not `arcade_pc 0x03B3CC` / `runtime_genesis_pc 0x03B5CC`
- not `arcade_pc 0x03B7F6` / `runtime_genesis_pc 0x03B9F6`
- not `arcade_pc 0x03B7F8` / `runtime_genesis_pc 0x03B9F8`
- not `arcade_pc 0x03A92A` / `runtime_genesis_pc 0x03AB2A`
- not `arcade_pc 0x03D24C` / `runtime_genesis_pc 0x03D44C`
- not the hooked clear/fill path `arcade_pc 0x03AD44` / `runtime_genesis_pc 0x03AF44`
- not the raw generic fill primitive `arcade_pc 0x03AD3C` / `runtime_genesis_pc 0x03AF3C`

It was historically mentioned in old archaeology notes as a pointer-load site (`arcade_pc 0x056032` / `runtime_genesis_pc 0x056232` loads `A1=#0x00C00828`), but the current canonical OPEN-018 remaining list did not identify this live item-description BG text producer as an active strict-target blocker.

Classification: **B - NEW raw PC080SN BG write** in the current ledger taxonomy.

## Strategic Context: Layers Touched

Captured transition/page-init touches:

- **BG / PC080SN:** yes. The item-description text producer writes BG attr/code pairs to `HW_ADDRESS 0x00C00828..0x00C03E2A` through raw copied arcade code.
- **Sprites / PC090OJ:** yes. Immediately after the BG text producer, the same page init loads `A1=HW_ADDRESS 0x00D00170` and calls `runtime_genesis_pc 0x00056314`, a patched-site sprite/OJ helper path.
- **FG / PC080SN:** not observed in the captured first strict-target failure path.
- **Window layer:** not observed in the captured first strict-target failure path.

Observation: routing the C00828 producer through BG staging would address the immediate strict-target blocker and likely let the item-description page advance further, but the page is not BG-only; it also uses the PC090OJ/sprite path. This does **not** show a Window-layer dependency for this first item-description init path. Complete visual fidelity may still depend on sprite subsystem work (OPEN-024), but the first fatal is a BG text producer raw-write.

## Classification

**B - NEW raw PC080SN BG write.**

It is a newly live, not-yet-catalogued BG content-producer in the current OPEN-018/KF-032 raw-write family. It should be scoped as an item-description BG text producer, not as a high-score regression and not as a clear/fill helper.

## Recommendation (Scoping Only)

Route/design work should be assigned as a bounded follow-up for the `arcade_pc 0x05602C/0x0563A6` item-description BG text producer family, with arcade intent preserved as BG attr/code cell emission through Genesis BG staging. No fix is designed or implemented here.

Do not reopen:

- Build 0109 high-score fall-through (CLOSED-015)
- Build 0111 high-score FG producer route (CLOSED-016)
- Build 0112 NAME source-base fix (CLOSED-017)

## OPEN / KNOWN_FINDINGS Impact

- OPEN-022: now has concrete writer evidence; remains OPEN pending design/implementation.
- OPEN-018: touched as same broad KF-032 raw-write class; remains OPEN.
- OPEN-001: context only.
- OPEN-021: not touched.
- OPEN-023: context only; no Window dependency observed for first C00828 failure.
- OPEN-024: context; item-description init touches PC090OJ/sprite path after BG text setup.
- KNOWN_FINDINGS: Option A for this evidence-only task. KF-032 already captures the raw PC080SN write class; a refinement can wait for a design/fix result if desired.

## STOP

STOP triggered: NO.
