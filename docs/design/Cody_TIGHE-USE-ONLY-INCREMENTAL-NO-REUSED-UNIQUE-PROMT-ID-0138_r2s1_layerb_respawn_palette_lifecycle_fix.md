# TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0138

# R2-S1 Layer-B checkpoint-respawn palette lifecycle correction

## Result and scope

Build 0571 corrects the proven Genesis lifecycle error that replaced the resident gameplay Layer-B palette on CRAM Line 2 with the frontend base palette during an active-human death/READY transition. The correction preserves the original arcade palette-bank residency contract without adding a round, record, checkpoint, death, fade, source-address, or colour special case. Automated gameplay reached a real progressed Record-26 checkpoint and completed death/respawn with the correct resident R2 palette. Record 29 itself was not reached by the bounded automation and remains pending Tighe gameplay acceptance.

## Starting state

- Branch: `rastan-direct-proposal`.
- HEAD: `d307c9ac8fb3b0bfd5906fd43d2ac973566773ba` (`Post Build 570`).
- Makefile counter: 570.
- Existing dirty work preserved: `AGENTS_LOG.md`, generated build outputs, PROMT-ID-0135 `apps/rastan-direct/src/sound/sound_comm.s`, the updated 0134 report, and untracked 0135/0136 reports.
- Relevant source identities: 0134 scene-load re-arm already in HEAD; 0135 audio remained as the pre-existing dirty file; 0137 source commit `79d75094`; 0138 source commit `538fac0c56153425b83ef84a06f71e739acfd147`.
- Baseline Build 0570: 4,443,832 bytes, SHA-256 `b9d1a9a2d98a65e8254184d40f2d9a1027b02058401fdc10e4e214ea03e6c3f3`.

No reset, clean, rebase, broad restore, artifact overwrite, or push was performed.

## Phase-0 priors and classification

Relevant active findings were KF-010 (BG -> Plane B), KF-011 (retained arcade frame ownership), KF-043/KF-046 (palette ownership/routing), KF-081 (publish N-1 then produce N), KF-082 (palette staging is single-buffered), and KF-085 (opcode-fetch read taps are prefetch-polluted). OPEN-006 remains the broader sprite/high-bank palette issue; OPEN-034/035 govern frontend palette restoration and attract-loop restoration. CLOSED issues do not establish this checkpoint-respawn subcase. The task extends the partially accepted 0134 result and corrects 0136's non-causal dispatcher hypothesis; OPEN-040 records the remaining human Record-29 acceptance boundary.

The required prior reports establish: R2 Layer B is routed to Genesis L2; R2's retained source is `$0005DC4E`, its physical arcade bank is 3, and record 29 maps to fade value 3; 0134 re-arms the existing loader; 0137 distinguishes natural gameplay from no-human attract at `$056440` with the active-human latch.

## Semantic cut

The retained arcade round/record/death/respawn/fade selection remains authoritative. The cut is after that semantic decision and before Genesis translates the selected resident Layer-B palette into `staged_palette_words` Line 2 and VBlank publishes it to CRAM. The retired tail is the separate physical arcade palette-bank hardware. The correction changes only Genesis ownership of its collapsed L2 during a transient scene-0 interval; it does not emulate palette hardware or introduce another buffer.

## Original loader and exact control data

`FUN_00059de8` at arcade `$059DE8` runs only when `A5+$13B0 == 1`, obtains the fade byte from `$05E24E[record]`, obtains the round's destination bank from `$059E8C`, obtains its source base from `$059EC8`, and calls `$059AD4` with:

- R2 initial entry: `A0=$0005DC4E`, `D0=3`, `D1=0`;
- progressed Record 26: the same `A0/D0`, `D1=1`;
- Record 29: the same `A0/D0`, `D1=3`.

The native hook recognizes bank 3 as the current round's Layer-B owner and translates it to L2. The external MAME instruction read observers are intentionally not used as register proof because KF-085 prefetch pollution was observed; the exact arguments above are instruction/data-flow facts from `$059DE8..$059E8A` plus runtime retained state. The event trace remains authoritative for state and L2 write order.

The R2 source row 0 is the full base palette. All 16 entries of rows 1 through 7 are `$FFFF`, meaning retain the resident arcade palette entry. Thus fade values 1 and 3 do not independently reconstruct the base. This is the crucial arcade residency fact.

## Five-case runtime comparison

The trace tool is `tools/mame/scripts/r2s1_palette_lifecycle_trace.lua`; evidence is under `states/traces/promt0138_r2s1_palette_lifecycle/`. Its 16-bit log of byte-sized round fields includes the adjacent byte in the low half (for example `round=0220` means round byte 2); conclusions use the actual high byte.

### 1. Normal attract control

Build 0571 normal ROM completed two no-input title -> R1 demo -> title cycles at frame 14,455. Both title palettes and terminal CRAM match, display is on, unsafe display-on writes are zero, and no trap was observed. Evidence: `states/traces/build0571_promt0138_attract_two_cycle/result.txt`.

### 2. Initial human R2-S1

At frame 408 gameplay begins with human latch 1, round 2, stage `$17`, record `$18`, `13AA=1`, `13AC=0`, `13AE=0`, and `13B0=1`. At frame 409 the loader consumes the arm (`13B0=$FF`) and stages the complete R2 base through the bank-3-to-L2 route. VBlank publication yields staged and actual CRAM L2:

`0000,0220,0440,0460,0024,0022,0026,0440,0220,0220,0240,0420,0002,0444,046A,0000`

Build 0570 and 0571 match exactly. This proves the retained loader, route, conversion, staging, and publication are correct before a death lifecycle.

### 3. Early R2-S1 death/respawn

On Build 0570, death enters scene 0 at frame 2512 and the old `load_scene_tiles` full copy replaces L2 with the frontend base. The reset rewinds to stage/record context `$17`; 0134 arms `13B0` at frame 2546; scene 1 returns at 2654; the loader consumes the arm at 2743 with fade 0, whose full row reconstructs the complete R2 base. That accidental full reconstruction explains why early respawn worked.

On Build 0571, scene 0 at frame 2512 preserves the resident R2 L2. The same existing re-arm and retained loader execute, and the terminal staged/CRAM words remain the exact R2 line above at frame 2922.

### 4. Progressed checkpoint comparison and first divergence

The bounded automated route reached record `$1A` (26), stage/checkpoint `$19`, and fade 1, then allowed a natural death and respawn.

On Build 0570 the last correct pre-death L2 is the R2 line above. The first divergence is frame 1855: `load_scene_tiles` changes owner to scene 0 and copies the exact frontend base L2:

`0000,0000,0008,004E,008E,00EE,08EE,0EEE,0A00,0E40,0E80,0EC0,0EEA,0000,0000,0000`

The active-human latch is still 1. The retained flow subsequently selects checkpoint `$19`, arms `13B0` at frame 1890, restores scene 1 at frame 1998, and consumes the arm at frame 2087 with fade 1. Because source row 1 is all `$FFFF`, the loader correctly preserves the now-wrong frontend values. No later writer repairs L2; staged and CRAM remain the same wrong frontend line. This is both the first early-versus-progressed divergence (fade 0 can reconstruct; fade 1 cannot) and the first arcade-versus-Genesis divergence (arcade retains its physical bank; Genesis erased its collapsed L2).

On Build 0571, scene 0 is entered at frame 1911 with the R2 line intact. The checkpoint becomes `$19`; `13B0` is armed at 1946; scene 1 returns at 2054; the loader consumes the arm at 2143 with fade 1. The all-keep row now preserves the correct resident line. At frame 2321 staged L2 equals actual CRAM L2 and equals the exact correct R2 line.

Record 29 uses fade 3, and row 3 has the same all-`FFFF` retention requirement. This statically establishes applicability, but the candidate did not traverse Record 29 in automation; it is not represented as gameplay-proven.

### 5. R2-S1 direct-start attract diagnostic

With no human input, the S2-1 selector does not create a real R2 retained lifecycle. Runtime remains round 1, human latch 0, and enters gameplay with record `$18`/stage `$17` selected by the derivative. The terminal L2 is the exact R1 Layer-B line:

`0000,0642,0644,0644,0646,0644,0868,0668,066A,068C,068E,0AAC,0E00,0AEE,0E80,0CC0`

It is neither frontend base nor Test-2.0 authored data: it is valid R1 Layer-B palette state paired artificially with an R2 selector. Build 0571 deliberately leaves this harness-only impossible normal-arcade combination unchanged. No `attract && R2` special case was added.

## Re-evaluation of PROMT-ID-0136 and current 0137 ownership

Current `$056440` code in `pc090oj_hooks.s` tests `A5+$13AA == 8` and then `A5+$34 != 0`; only that combination selects gameplay owner. Other values select frontend owner. Runtime initial, early-respawn, and progressed-respawn gameplay showed `13AA=1`, `13AC=0`; normal/direct attract walked frontend phases and retained `13AC=0`. Therefore the old 0136 claim that `13AC` supplies a substate-8 discriminator is not supported by current runtime.

More importantly, the destructive progressed-respawn write occurs through generic scene-0 `load_scene_tiles`, not the `$056440` owner branch. The 0137 correction neither caused nor repaired this palette defect and remains intact.

## Production correction

Source commit `538fac0c` changes only `apps/rastan-direct/src/scene_load.s`. For scene 0:

- if `A5+$34 == 0`, cold frontend/title/attract/terminal ownership copies all four frontend lines exactly as before;
- if `A5+$34 != 0`, the retained active-human death/READY lifecycle copies frontend Lines 0, 1 and 3 but skips the existing staged L2;
- `palette_pending` is still set, so the preserved line is published normally;
- the existing 0134 `13B0` re-arm and retained `FUN_00059de8` behavior are unchanged.

This is the arcade physical-bank residency contract translated to Genesis's one physical Layer-B line. It adds no shadow, duplicate buffer, palette data, source address, round check, record check, checkpoint check, fade check, death-state machine, or level-select behavior. `specs/palette_decisions.json` is unchanged because no colour or mapping decision changed.

## Verification and regressions

- Build 0571 canonical gate: PASS.
- Gameplay-entry gate and mandatory 30-second USA/NTSC Genesis trace: PASS.
- Test 2.0 palette family validation and complete same-number family generation: PASS.
- Synthetic phase-epoch injection: FAIL with corrupt injected state/SP, the same non-gameplay harness class disclosed for 0570; not counted as acceptance.
- Normal attract: two complete cycles PASS, no trap.
- Normal R1 initial gameplay and a real R1 death/respawn: staged and CRAM L2 remain exact R1 palette.
- R1-S2, R2-S1, R2-S2, and R2-S3 direct functional entries: PASS expected stage/record/package, zero boundary misses, populated gameplay planes.
- R2 initial and early respawn: exact correct staged/CRAM L2.
- Progressed Record-26 checkpoint death/respawn: exact correct staged/CRAM L2 after retained fade-1 keep row.
- Natural R1-S2 -> R1-S3 was proven on unchanged 0137 transition source in 0570; direct R1-S2 entry passed on 0571. A second complete natural boss-transition run was not performed for 0571.
- Later Record-29 respawn and continued post-respawn R2 progression require Tighe gameplay testing.
- PROMT-ID-0135 `sound_comm.s` was not edited by 0138. Its pre-existing dirty source was compiled into 0571. No audible regression listen was performed; Aggressive World/Re-In-Carnation/boss music remain Tighe checks.

## Build 0571 artifacts

All listed artifacts are 4,443,832 bytes:

| Artifact | SHA-256 |
|---|---|
| `dist/rastan-direct/rastan_direct_video_test_build_0571.bin` | `ab778a5d84cdbc0f3a9917defa8831063e95b5946cc5f9744047b05e8934cf95` |
| `dist/rastan-direct/rastan_direct_video_test_build_0571_S1-2.bin` | `37405299d8f6f56e9bea4c4c6dc9f88971dd720cd2d376d94ff26a894ef84498` |
| `dist/rastan-direct/rastan_direct_video_test_build_0571_S2-1.bin` | `b2a391438707bade5986b9ff05f8ce414aa3e76d2fe7abd475a9d16441a0e37c` |
| `dist/rastan-direct/rastan_direct_video_test_build_0571_S2-2.bin` | `841f8bd8e879eca64ae9140468f8087d63b195e65786e3e283a6657052cbd844` |
| `dist/rastan-direct/rastan_direct_video_test_build_0571_S2-3.bin` | `4b37b6c59781753e9d310e4a9079935536afbcb29c1e98292673774debe51fae` |

Counter advanced `570 -> 571`. Normal ROM should be tested first for natural progression; S2-1 is the secondary focused convenience artifact.

## Open/Closed Issues Impact

OPEN-040 is added for the R2-S1 progressed-checkpoint palette acceptance boundary. The production mechanism and a real progressed Record-26 checkpoint are corrected by 0571, but the broader issue remains open until Tighe verifies Record 29 and later R2-S1 progression. No CLOSED issue is changed. OPEN-006, OPEN-034, and OPEN-035 are not closed or broadened by this work. The direct-start attract mismatch is recorded as a harness-only impossible lifecycle, not a production issue.

## Tighe test order

1. Test normal Build 0571 through natural R1 -> R2 and reach R2-S1 Record 29.
2. Die after the progressed checkpoint and confirm Layer-B remains the current dark R2 jungle palette.
3. Continue forward and confirm later retained palette progression remains coherent.
4. Regression-listen Aggressive World, Re-In-Carnation, and boss music.
5. Use `_S2-1` only for a faster secondary palette check; ignore its no-human attract colour combination.

No Tighe acceptance is claimed.

TIGHE-USE-ONLY-INCREMENTAL-NO-REUSED-UNIQUE-PROMT-ID-0138
