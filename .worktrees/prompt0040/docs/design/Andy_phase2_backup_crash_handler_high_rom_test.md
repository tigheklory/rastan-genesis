# Phase 2 — Transplant bk_crash_handler.s into the High-ROM .crash Section (Build 0294)

**Baseline:** Build0293 (Tighe-verified: gameplay/rope/BG good through the outside world to the first fortress; item
page still crashes to the OLD handler executing from high ROM). **No rollback**; all numbered ROMs preserved.
Labels: **PROVEN / HYPOTHESIS / DISPROVEN**.

## BASELINE
Build0293 established the high-ROM crash architecture: `.crash` section after `.text.wrapper`, with
`genesistan_crash_handler_end` pinned at 0x117E so the arcade splice and all normal code stay put. Phase 2 tests the
larger backed-up **screenshot-first** handler in that proven section.

## BACKUP AUDIT
**PROVEN.** `apps/rastan-direct/src/bk_crash_handler.s` (SHA-256
`8f55d09c4f109f85d0b2c935be577b68024da6d75afe4e9873db1ea94300f1a6`, 36,404 bytes) is the **Build0290/0291
screenshot-first handler WITH the Build0290 D2 numeric-renderer fix**:
- movem-first capture (`movem.l %d0-%d7/%a0-%a6, CRASH_D0` after the vector stubs write only the vector to WRAM) —
  original D0-D7/A0-A6 preserved;
- exception-frame parsing, GEN PC + SRC classification, VECTOR/SR, fault/access, FRAME SP/USP, A5-checked game state
  (a5+0x00/02/04/34/200), raw stack window;
- full VDP clean-room (`crash_vram_fill`: zero VSRAM/H-scroll, clear Plane A/B/Window/SAT, deterministic CRAM,
  self-contained font), display off during rebuild;
- **D2 fix PRESENT:** `crash_put_hex32_at`/`hex16_at`/`hex8_at` do `move.l %d2,-(%sp); bsr crash_set_cursor; move.l
  (%sp)+,%d2` — the value survives cursor positioning;
- automatic build number via `.include "crash_build.inc"`, BUILD at columns 30/36 (the clipping fix).
It uses `.section .text.boot` (old low-ROM ownership) and defines `genesistan_crash_handler_end` — both adapted
below for the Build0293 high-ROM architecture.

## BACKUP PRESERVATION
`bk_crash_handler.s` is **NOT modified**. An archival copy `backups/bk_crash_handler_pre_phase2.s` was created
(cmp = 0). After the build, `cmp bk_crash_handler.s backups/bk_crash_handler_pre_phase2.s` = 0 (unchanged). The
Phase-1 backup `backups/crash_handler_build0292_build0287_baseline.s` and all other crash-handler backups are
untouched.

## HIGH-ROM TRANSPLANT
**PROVEN.** The active `apps/rastan-direct/src/crash_handler.s` was replaced with a copy of `bk_crash_handler.s`,
with only the mechanically-required integration edits:
- both `.section .text.boot` → `.section .crash` (so the handler links into the Build0293 high section);
- removed the handler's own `.global genesistan_crash_handler_end` and its end label (link.ld pins that symbol at
  0x117E — the arcade-splice boundary — not the real handler end).
The active handler is otherwise byte-identical to `bk_crash_handler.s` (diff = only those relocation lines). No
diagnostic semantics were changed.

## BUILD SYSTEM SUPPORT
**PROVEN.** The transplanted handler `.include`s `crash_build.inc`, so the minimal Makefile plumbing was restored:
`CRASH_BUILD_INC := $(OUT_DIR)/crash_build.inc`, a `vdp_comm.o` prerequisite on it, and a generation rule that writes
`crash_build_number_str: .asciz "NNNN"` from the numbering counter (next = last+1). It affects only the crash-screen
build string. `RASTAN_GAMEPLAY_HUD_SPRITES=2`, postpatch ordering, arcade mapping, PC080SN, PC090OJ, and normal
rendering are unaffected (verified: normal regions byte-identical, below). Generated `crash_build.inc` = `"0294"`.

## NORMAL ADDRESS INVARIANTS
**PROVEN** (clean-rebuild symbols): `genesistan_crash_handler_end`=0x117E; `_vblank_service`=0x700C2;
`z80_driver_start`=0x18492C — all unchanged. `_crash_stub_bus_error`=0x185000, `_crash_common`=0x185144 (high
`.crash`). SSP=0x00FF0000, RESET=0x00000202, VINT=0x000700C2 unchanged. arcade_copy start = 0x117E.

## BUILD0293 VS CANDIDATE DIFFERENCE ACCOUNTING
**PROVEN** (0293 vs 0294):

| Region | Result | Class |
|---|---|---|
| Vectors 0x0–0xFF | 99 diffs | A — crash-stub entries point to the bk handler's high stubs (different stub layout) |
| ROM header 0x100–0x1FF | 2 diffs | D — checksum |
| Boot code 0x200–0x3A4 | **IDENTICAL** | — |
| Low freed area 0x3A4–0x117E | **IDENTICAL** (zeros in both) | — |
| arcade_copy 0x117E–0x600F4 | **IDENTICAL** | — |
| gap 0x600F4–0x70000 | **IDENTICAL** | — |
| genesis_only 0x70000–0x184A34 | **IDENTICAL** | — |
| .crash region 0x184A34–0x185DDA | 3223 diffs | B/C — OLD handler → bk screenshot-first handler |
| ROM end 0x185DDA–0x185EB8 | new (candidate only) | C — bk handler tail |

ROM grew 1,596,890 → 1,597,112 (+222). **No unexplained normal difference.** Every normal executable/data byte
(boot, arcade, gap, genesis-only) is unchanged; item-page `tst.l %a5` @0x073212 = `4A8D` unchanged.

## CONTROLLED CRASH VALIDATION
**PASS.** Genesis-NTSC MAME, controlled ILLEGAL (0x4AFC) at 0x00FF9000 with sentinels:
- vector reached the high handler; handler executed from high ROM;
- WRAM record: EXC=4, GENPC=00FF9000, SR=2700, D0=DEAD0000…D7, A0=A0A0A000…A5=00FF0000…A6, FRAME SP 00FEFF64, game
  state 0002/0003/0001/0000/00A5, A5_VALID=1 (movem-first capture correct);
- **SCREEN == WRAM RECORD** (D2 fix confirmed): the rendered screenshot shows VECTOR 04, GEN PC 00FF9000, SR 2700,
  D0 DEAD0000…D7, A0 A0A0A000…A6, FRAME SP 00FEFF64, STATE 0002/0003/0001/0000/00A5, SRC UNKNOWN, and **BUILD 0294**
  — all matching the record; clean screen (Plane A/B/Window/SAT cleared, no game-graphics bleed-through);
- no recursion, no invalid fetch, no high-address truncation, no PC-relative relocation problem.
Evidence: `states/traces/build0294_phase2_backup_handler_high_rom/` (wram_record.txt + screen_matches_record_build0294.png).

## KNOWN DEFECTS PRESERVED
Item-page `tst.l %a5` (`0x4A8D`) at 0x073212 unchanged (scrolling item page still crashes — now to the transplanted
screenshot-first handler). The separate first-fortress/second-rope freeze Tighe observed on Build0293 was NOT
diagnosed or changed. PC090OJ retirement not advanced; no PC080SN/collision/rope/palette/map changes.

## BUILD
- **GATE_PASS**; numbered **Build 0294**.
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0294.bin`, SHA-256
  `f6abd484e899573eb03032990f572478c48ef177d517c8bb6373ac32c9a452c1`, size 1,597,112, counter 293→294. All numbered
  ROMs preserved; no second release run.
- Canonical coverage constant updated 0x185DDA → 0x185EB8 (ROM-end grew; low/arcade/genesis-only unchanged).
- Makefile smoke: PASS (30s Genesis-NTSC, 940.93%, no crash). Boot guard PASS (pre+post).

## RESULT
The backed-up screenshot-first handler (with the D2 fix) executes safely and correctly from the proven high-ROM
`.crash` section, with every normal code/data byte identical to Build0293. Pending Tighe's interactive confirmation
that Build0294 gameplay matches Build0293 with the larger handler at high ROM.
