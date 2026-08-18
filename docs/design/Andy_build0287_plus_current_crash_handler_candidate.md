# Build0287 Functional State + Current Crash Handler — Recovery Candidate (Build 0291)

**Baseline:** current tree after Build 0290. **No rollback**; all numbered ROMs 0286–0291 preserved. Candidate:
**Build 0291**. Labels: **PROVEN / HYPOTHESIS / DISPROVEN**.

## PURPOSE
Empirical isolation candidate for Tighe: **Build0287 normal functional state + the current improved (Build0290)
screenshot-first crash handler**, nothing else. Tighe reports 0286/0287 gameplay good and 0288–0290 gameplay broken
(rope, BG/map); static analysis shows 0287→0290 gameplay is byte-identical. This numbered ROM lets Tighe test the
exact hybrid directly rather than resolving the contradiction on paper.

## BUILD0287 FUNCTIONAL REFERENCE
**PROVEN.** The preserved `dist/rastan-direct/rastan_direct_video_test_build_0287.bin` is the functional reference.
The current tree's gameplay/rendering/frontend sources (`pc090oj_hooks.s`, `specs/rastan_direct_remap.json`,
palette/tilemap/PC080SN, native sprite helpers) were last changed at Build0287 and untouched by the crash-handler
work (0288–0290 changed only `crash_handler.s` + the Makefile build-number plumbing). So the tree already carries
Build0287's exact functional content, and building it reproduces that content byte-for-byte (verified below).

## CURRENT CRASH HANDLER RETAINED
**PROVEN.** The Build0290 handler is intact: stubs write only the vector to WRAM then `_crash_common` does
`movem.l %d0-%d7/%a0-%a6` first (original D0-D7/A0-A6 captured before any reuse); verified normal + bus/address frame
parsing; GEN PC (with SRC region classification, ARC PC never fabricated); exception name/vector; SR; fault/access
(vectors 2/3); A5-checked game state (a5+0x00/02/04/34/200); FRAME SP; USP; raw stack window; full VDP clean-room
(display off during rebuild, zeroed VSRAM + H-scroll, cleared Plane A/B/Window/SAT, deterministic CRAM, self-contained
font, display on last); automatic four-digit build number; and the **Build0290 D2-preservation numeric fix**. The old
Build0287 handler was NOT restored.

## ROM DIFFERENCE ACCOUNTING
**PROVEN** — `…_0287.bin` vs `…_0291.bin`, bucketed by `address_map.json` regions:

| Region | Range | Result | Class |
|---|---|---|---|
| Exception vectors | 0x000000–0x0000FF | 68 diffs | A (crash-stub targets moved) |
| ROM header (checksum) | 0x000100–0x0001FF | 2 diffs (0x18E–0x18F) | D (auto checksum) |
| Boot + crash handler | 0x000200–0x00125C | 3415 diffs (boot stub 0x202–0x3A4 **identical**) | B + C (handler code/font + "0291" build number) |
| arcade_copy (GAMEPLAY) | 0x00125C–0x0600F4 | **IDENTICAL** | — |
| genesis_only (HELPERS) | 0x0600F4–0x184A34 | **IDENTICAL** | — |

`gameplay(0x125C→end) 0287 == 0291`: **True**. Only the allowed classes A–D differ. **No normal
gameplay/PC080SN/PC090OJ/native-sprite/VBlank/palette/HUD/frontend difference exists.** `RASTAN_GAMEPLAY_HUD_SPRITES=2`
unchanged.

## ADDRESS-MAPPING VERIFICATION
**PROVEN.** `address_map.json` places `preserved_vectors` 0x0–0x125C and `arcade_copy` at 0x125C in both builds; the
crash-handler growth is absorbed in the fixed 0x125C boot region, so no arcade or genesis-only symbol moved (both
regions byte-identical). SSP (0x00FF0000), RESET (0x00000202), reset entry, and VINT (0x000700C2) are identical. No
historical/arithmetic addresses were introduced.

## KNOWN ITEM-PAGE CRASH PRESERVED
**PROVEN.** `tst.l %a5` (`0x4A8D`) at runtime 0x073212 (`.Lnq_transient_items_emit`) is byte-unchanged in 0291. The
transient family (0x056114 / 0x05607C / 0x056440) is unchanged from Build0287. The scrolling item page is expected to
crash; this is intentional for the isolation test. No PC090OJ retirement advanced; no GAME OVER / PC080SN changes.

## VALIDATION
- **Difference contract:** PASS (only classes A–D; gameplay byte-identical to 0287).
- **Crash SCREEN == WRAM RECORD:** PASS. Controlled ILLEGAL (0x4AFC) at 0x00FF9000 with sentinels, Genesis-NTSC MAME:
  record and rendered screenshot match field-by-field — VECTOR 04, GEN PC 00FF9000, SR 2700, D0=DEAD0000…D7,
  A0=A0A0A000…00FF0000…A6, FRAME SP 00FEFF64, STATE 0002/0003/0001/0000/00A5 — and the screen shows **BUILD 0291**.
  Evidence: `states/traces/build0291_recovery_candidate_validation/` (wram_record.txt + crash_screen.png).
- **Canonical verifier:** PASS (opcode_replace 228 / coverage 0x184A34 unchanged). **Boot guard:** PASS (pre+post).
- **Makefile smoke:** PASS (30s Genesis-NTSC, 946.16%, no crash).

## BUILD
- **GATE_PASS**; numbered **Build 0291**.
- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0291.bin`
- SHA-256: `7b634b875a5a9837c3ee5227df70f93b631c13ef72bae08395b1539f33a18138`
- Size: 1,591,860 bytes · Counter transition **290 → 291**. All ROMs 0286–0291 preserved.

## INTERPRETATION FOR THE TEST
Because 0291's gameplay bytes equal Build0287's exactly, this candidate isolates the variable to the crash-diagnostic
subsystem. If Tighe still sees broken rope/BG on 0291, it is **proven** not to originate from a gameplay-code
difference vs Build0287 — the next investigation would then target either the crash handler's runtime visibility of a
pre-existing exception, or a platform/loaded-file difference; and separately, whether the preserved Build0287 ROM
itself shows the same rope/BG behavior (which would place the regression at 0286→0287). If gameplay is good on 0291,
the earlier 0288–0290 observation was environmental. Either outcome is decisive.
