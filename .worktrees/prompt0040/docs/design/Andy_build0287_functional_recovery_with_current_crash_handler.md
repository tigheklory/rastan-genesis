# Build0287 Functional Recovery Investigation — STOP (no build): gameplay is byte-identical 0287↔0290

**Baseline:** current tree after Build 0290. **No rollback**; all numbered ROMs preserved. Labels:
**PROVEN / HYPOTHESIS / DISPROVEN**. **No numbered build produced** — see the STOP rationale.

## RECOVERY GOAL
Produce "Build0287 functional game/graphics/frontend state + current screenshot-first crash handler." Tighe's
interactive testing is the acceptance authority: he reports 0286 and 0287 gameplay good (item page crashes),
0288/0289/0290 gameplay broken (rope progression, BG/map).

## BUILD0287 FUNCTIONAL STATE RECONSTRUCTION
**PROVEN — the current tree ALREADY equals Build0287's gameplay/rendering code.** Git shows Builds 0284–0290 are
all uncommitted working-tree changes (last commit = Build 283); `pc090oj_hooks.s` and `specs/rastan_direct_remap.json`
were last changed at Build0287 and were NOT touched by the crash-handler work (0288–0290 changed only
`crash_handler.s` and the Makefile). So the reconstruction target is already present in the tree.

## BUILD0287 VS RECOVERY-CANDIDATE (=0290) DIFFERENCE ACCOUNTING
**PROVEN by exhaustive ROM comparison** (`dist/rastan-direct/…_0287.bin` vs `…_0290.bin`), bucketed by the current
`address_map.json` regions:

| Region | Range | Result |
|---|---|---|
| Genesis vectors | 0x000000–0x0000FF | 68 diffs — crash-stub vector entries (exception-only) |
| ROM header | 0x000100–0x0001FF | 2 diffs — header checksum (0x18E–0x18F), auto-recomputed |
| boot + crash handler | 0x000200–0x00125C | boot stub 0x202–0x3A4 **identical**; 0x3A4–0x125C = crash-handler code/font (exception-only) |
| arcade_copy (GAMEPLAY) | 0x00125C–0x0600F4 | **byte-identical** |
| genesis_only (HELPERS) | 0x0600F4–0x184A34 | **byte-identical** |

Gameplay hash (entire 0x125C→end): 0286 = `f4dadcb2…` (size 1591960); **0287 = 0288 = 0289 = 0290 = `ab632490…`
(size 1591860)**. The only recent gameplay-code change was **0286→0287** (setup/priority retirement + moving the
GAME OVER emit into `.Lnq_gameplay`); nothing changed 0287→0290.
- The 213 "arcade_copy" byte diffs at 0x117E–0x125B are **not arcade code** — they are the crash-handler font (0290)
  vs `0xFF` padding (0287) inside the **fixed-size 0x125C boot region** (`genesistan_crash_handler_end` = 0x125C;
  arcade_copy begins at 0x125C in both). Everything at/after 0x125C is identical.

## ADDRESS-MAPPING / RELOCATION VERIFICATION
**PROVEN.** `address_map.json` places `preserved_vectors` at 0x0–0x125C and `arcade_copy` at 0x125C in the current
build; the crash-handler growth is absorbed inside the fixed boot region, so no arcade or genesis-only symbol moved
(both regions byte-identical). No stale/mis-relocated operand exists.

## NORMAL EXECUTION ISOLATION
**PROVEN.** SSP (0x00FF0000), RESET (0x00000202), reset entry (0x202–0x3A4), and the VINT vector (0x000700C2) are all
identical. The changed exception/reserved vectors point to crash stubs / `_crash_stub_other` that merely moved but
are semantically identical halts. **No gameplay/genesis code references the changed crash-handler region
(0x3A4–0x125C):** a scan of the postpatched disassembly found the only branch into the boot region is `jmp 0x300`
(arcade 0x3B256) targeting the **identical** boot stub; all other apparent hits are a5/a2-relative displacements or
integer constants, not references into the crash handler.

## CURRENT CRASH HANDLER RETAINED
The current screenshot-first handler (Build0290) — early D0-D7/A0-A6 capture, verified frame model, GEN PC + SRC,
SR, fault/access, A5-checked game state, FRAME SP/USP, raw stack, full VDP clean-room (zeroed H/V scroll, cleared
Plane A/B/Window/SAT, deterministic CRAM), and the **Build0290 D2-preservation numeric fix** (screen==record proven)
— is intact in the tree and would be carried into any build.

## REQUIRED MAKEFILE / VECTOR COMPANION CHANGES
Minimal and already present: `crash_build.inc` generation (build-number string only; a prerequisite of `vdp_comm.o`),
and the exception-vector entries targeting the crash stubs. None touch gameplay configuration
(`RASTAN_GAMEPLAY_HUD_SPRITES=2` throughout) or patch ordering.

## KNOWN ITEM-PAGE CRASH PRESERVED
The Build0286 `tst.l %a5` (0x4A8D) at runtime 0x073212 (`.Lnq_transient_items_emit`) — illegal on the Genesis
68000 — is unchanged (present identically in 0286–0290). It remains OPEN and was NOT modified.

## WHY NO BUILD WAS PRODUCED (STOP)
**DISPROVEN: a Build0288 gameplay-code regression.** Because the gameplay/rendering/frontend code is byte-identical
across 0287→0290 (proven above), a "recovery" build would be **gameplay-byte-identical to the very build (0290) Tighe
reports as broken** — it cannot restore anything, and it would consume a numbered artifact and a test cycle for no
change. The recovery gate's STOP provision applies: I cannot deliver a meaningful recovery because there is no
gameplay-code difference to remove.

**The broken rope/BG Tighe observes in 0288–0290 therefore cannot originate from a gameplay-code difference vs 0287.**
The two remaining, mutually-exclusive explanations require one datapoint from Tighe to disambiguate:
1. **HYPOTHESIS — the regression is actually 0286→0287** (the only recent gameplay-code change: setup/priority
   retirement of 0x054052/0x03AD84/0x03B926/0x059F5E, and the GAME OVER emit moved into `.Lnq_gameplay`). If so,
   0287 ITSELF exhibits the broken rope/BG, and "0287 good" was an incomplete observation (the 0287 test focused on
   the HIGH SCORE fix). **Test:** re-run the PRESERVED `…_0287.bin` now and look specifically at rope progression
   and BG/map. If broken → the fix target is the 0286→0287 changes, not the crash handler.
2. **HYPOTHESIS — non-gameplay-code cause** (crash handler makes an exception's halt visibly "clean" where the old
   handler left game graphics on-screen; or an emulator/hardware/loaded-file difference between the 0287 and 0290
   test sessions). **Test:** confirm the exact platform/emulator used for each build and the precise repro (what
   action, what screen) where rope/BG breaks.

## DOCUMENTATION UPDATES
KNOWN_FINDINGS / OPEN_ISSUES updated with this proof and the disambiguation request. No CLOSED changes. No source or
spec was modified in this investigation; the tree remains the Build0290 state (= Build0287 gameplay + current
handler).
