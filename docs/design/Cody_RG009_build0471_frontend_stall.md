# PROMPT RG-009 — Cody — Build 0471 frontend stall and Build 0472 recovery

## Result

Build 0471 is rejected/consumed. The sampled `0x03B298..0x03B29C` PCs were the normal
arcade frame-loop tail, not a spin loop. The first wrong operation was the state-2 phase
dispatcher loading an unreflowed signed displacement from arcade table `0x03A17C` and
returning through padding immediately before the real phase-0 handler. Build 0472 declares
that table and the second crossing table at `0x03A1AC`. The writer-triggered HUD architecture
is preserved.

Build 0472 was produced from exact pre-build source
`4d5aadb0e92387617594404f9e757597c87517a3`:

- normal ROM: `dist/rastan-direct/rastan_direct_video_test_build_0472.bin`
- SHA-256: `5b855e163a572c3a511a76470199c9cb13324f6ea0739bbd0f6834b80092dc7a`
- size: 2,739,896 bytes
- build counter: 471 -> 472; ledger records 0472 produced with canonical/entry/epoch PASS
- configured family: normal, `_d`, `_s`, `_do`, `_c`, `_full_hud`, `_invincible`
- hardware acceptance: PENDING; accepted Build 0467 and `accepted/build-0467` are unchanged

## Differential proof: 0467 versus 0471

The established deterministic Genesis-NTSC credit/START route was compared using
`states/traces/build0467_gameplay_entry_gate_20261020_202404` and
`states/traces/build0471_gameplay_entry_gate_20261021_143000`.

Both runs are identical through START acceptance and reach tuple `2/0/0`, scene 0. In accepted
0467, the next state-2 dispatch advances `A5+4` from phase 0 to phase 1 by frame 190, then reaches
`2/2/6` by frame 200. In 0471, `A5+4` remains zero and tuple `2/0/0` repeats. Thus the last
identical semantic point is entry to outer state 2 with phase 0; the earliest divergence is the
first phase-0 dispatch immediately afterward.

At original arcade `0x03A166..0x03A17A` (Build-0472 runtime `0x03A366..0x03A37A`), the dispatcher
indexes the signed-word table at arcade `0x03A17C` (runtime `0x03A37C`). Entry 0 was left at
`0x03EA`. RG-008 had inserted six bytes at each of `0x03A2B0` and `0x03A2CE`, between the table
and semantic handler arcade `0x03A566`. The handler therefore moved from its historical runtime
`0x03A766` to `0x03A772`, but stale entry 0 still landed at `0x03A766`. That location is the
preceding NOP padding ending in the RTS at `0x03A770`; it returns without executing phase 0 and
without changing `A5+4`. Correct entry 0 is `0x03F6`.

### The alleged `0x03B298..0x03B29C` loop

The current address map maps runtime `0x03B298` to original arcade `0x03B080`. This is the common
outer frame-loop tail, not a wait loop: the nearby code writes the retained frame/control value to
hardware-contract register `0x3C0000`, tests `A5+0x1C10`, handles the diagnostic condition, compares
`A5+0x12` with `0x0100`, calls the frame service at `0x03A1A8`, and branches to the next arcade
frame. A frame-end sampler naturally catches these PCs repeatedly. No value at this location is
awaited. Accepted 0467 exits the observed `2/0/0` condition because the earlier `0x03A17C`
dispatch reaches phase handler `0x03A566`; 0471 returns before that handler, so every subsequent
frame arrives at this normal tail with the same state.

## Dirty-hook contract audit

All four hooks retain arcade score/state ownership and set only the presentation dirty byte.
`genesistan_gameplay_hud_score_dirty` now saves/restores the complete SR around its `MOVE.B`, so
it exports no CCR change and touches no D/A register. Its net stack delta is zero; the temporary
two-byte SR save is balanced before RTS.

| Hook | Arcade / Build-0472 runtime | Original -> replacement | Contract |
|---|---|---|---|
| active P1 restore | `03A2B0` / `03A4B0` | `RTS` -> `JSR dirty; RTS` | retained block copy already completed; D/A preserved; SR/CCR exact; helper return then original return |
| active P2 restore | `03A2CE` / `03A4D4` | `RTS` -> `JSR dirty; RTS` | same; DBRA count and final pointers precede this site and are unchanged |
| paid/new-game clear | `03A9A2` / `03ABAE` | `LEA A5+0080,A0` -> `JSR dirty; LEA A5+0080,A0` | helper preserves all registers/CCR; original LEA and fallthrough remain |
| centralized score award | `03B7B0` / `03B9C8` | `BSR.W 03B802` -> `JSR dirty` | retained `03B726` ABCD update and side effects complete first; all registers/CCR preserved; returns to original `03B7B4` continuation |

The two restore loops copy the same 64-byte player blocks with their original source/destination
pointers and DBRA behavior. The notifications occur only after those loops have completed, so
they cannot change loop count, pointer advancement, copied score bytes, or caller-visible flags.

## Bounded RG-008 reflow audit

The audit was limited to references whose source/target relationship can cross the four RG-008
insertions.

- Ordinary BRA/Bcc/BSR references are owned by automatic reflow; the 0472 build repaired 7,202.
- Absolute-long operands are owned by the established relocation pass; 628 were repaired.
- The declared branch at arcade `0x03A1C0` remains owned and correct; two declared branches passed.
- The only DBF in the bounded late region is `0x03B750 -> 0x03B748`, wholly before the
  `0x03B7B0` insertion and unaffected.
- PC-relative LEA/load references inspected in `0x03A000..0x03B7B4` keep source and target on the
  same side of every RG-008 insertion.
- Existing table `0x03A06C` remains declared and correct.
- Missing table `0x03A17C` is now declared (4 entries): `03F6 0000 044C 062C`.
- A second missing crossing table at `0x03A1AC` is now declared (10 entries):
  `0018 0054 0138 0164 01FA 0280 02B0 02D4 02D8 0014`.
- Local tables at `0x03A57C`, `0x03A5D2`, `0x03A8CE`, and `0x03AA3C` do not cross an insertion;
  `0x03AA20` remains declared from prior work.

The build reports 20 jump-table fixes. No unexplained crossing reference remains. This passes the
RG-009 root-cause gate without weakening validation or hard-coding a relocated Genesis target.

## Semantic cut and legacy status

This task changes no PC080SN/PC090OJ native cut. It retains the RG-008 cut at the arcade score
writers: authoritative score/state -> presentation dirty notification -> persistent compact
Genesis semantic HUD queue -> existing native finalizer/SAT. The obsolete score-digit PC090OJ
refresh below `0x03B7B0` remains retired. No chip RAM, shadow graphics device, polling cache,
fallback, NOP bypass, or new runtime state machine was added. Ordinary frames execute one dirty
test and perform no score-byte/BCD polling.

## Validation

All runtime tests below used the USA/NTSC `genesis` MAME driver.

- canonical gate and both boot guards: PASS; 228 canonical opcode-replacement sites covered;
  generated address-map/manifest validation PASS
- gameplay entry: PASS at frame 569; credit, START, Round 1, package/fixed-plane install,
  player control, and 240 post-entry frames; zero address/bus/illegal/crash entries; valid SP
- seven production epochs: PASS; Plane-A full LUT and fixed Plane-B LUT checks PASS
- native HUD verifier: PASS, 57 dirty cases, unchanged-no-rebuild PASS, lifecycle dirty PASS,
  RG-005 score/label geometry PASS
- writer-event/lifecycle HUD runtime probe: PASS at frame 4,433; retained arcade `0x03B726`
  changed score to `001234`; dirty byte consumed; semantic count changed 3 -> 7 (four visible
  digits + 1/U/P); both alternating SAT banks had complete label/digit geometry and unchanged
  records persisted; four death-state entries were observed; Continue appeared at frame 4,189;
  deterministic coin/START acceptance returned to non-demo gameplay at frame 4,421 with score
  `001234`, dirty clear, and the HUD lane rebuilt
- fixed30: 1,798 frames; zero live FG C-window writes
- final-life zero-input: PASS at frame 3,582; three death entries and GAME OVER transition reached
- RG-004 Continue: PASS; 83 staged/83 VRAM names, zero name mismatches
- RG-004 attract: PASS; natural demo death and second title at frame 7,217; first/second-title and
  terminal CRAM lines match
- deterministic `_invincible` rope: `795/795/795`, median 13,267.083 ms
- complete configured seven-ROM family: PASS, including invincibility-contract verification
- final-life static semantic map: PASS (`0x03A3C0 -> 0x03B332`)

The all-zero score follows retained leading-zero suppression, so its semantic lane initially has
the three visible 1/U/P label records. After the authoritative `+1234` event, the four significant
score digits and all labels are present. The runtime probe is external validation only and does
not modify the ROM or production WRAM score directly.

## Performance versus accepted Build 0467

| Work | Build 0467 | Build 0472 |
|---|---|---|
| unchanged frame | rebuild six BCD positions and label records | one dirty-byte test; no BCD reads/conversions/queue rebuild |
| score event | same unconditional rebuild | one event-driven rebuild of significant digits plus immutable labels |
| semantic HUD finalization | one lane per frame | one lane per frame (unchanged) |
| SAT finalizer/DMA | unchanged native finalizer and 640-byte table | unchanged native finalizer and 640-byte table |
| rope | 798 frames / 13,317.147 ms | 795 frames / 13,267.083 ms |

Measured rope change is 3 frames / 50.064 ms faster (0.376%). This is evidence for the exact
deterministic route, not an inferred general CPU-cycle speedup. No matching 0472 exact IRQ/worker
cycle run was claimed: the existing detailed timing tool's historical breakpoint defaults do not
match this shifted ROM without a separately resolved full breakpoint set. Build 0472 is not slower
than 0467 on the required established benchmark.

## Files and tooling

ROM-producing source changes:

- `specs/rastan_direct_remap.json`
- `apps/rastan-direct/src/pc090oj_hooks.s`

Post-build validation/report additions:

- `tools/mame/scripts/gameplay_hud_event_regression.lua`
- `tools/mame/run_gameplay_hud_event_regression.sh`
- this report and the concise `AGENTS_LOG.md` entry

Existing project tools reused: canonical Makefile pipeline, address map, disassembly/Ghidra
exports and C decomp, gameplay-entry/epoch/fixed30/final-life/RG-004/native-HUD/family gates, and
the deterministic rope benchmark. New tooling created: one durable HUD event/SAT-bank regression
probe. Why necessary: existing gates did not observe the persistent reduced-HUD queue across an
authoritative score event and both alternating SAT banks; the probe reuses the established input
and JSR-injection mechanisms and closes only that evidence gap.

Concurrent Andy RG-006/RG-007 decompilation, audio work, Palette Composer work, and unrelated
generated changes were not modified or staged.

## USER MUST VERIFY

On real Genesis hardware, verify Build 0472 normal ROM enters Round 1; the initial `1UP` label is
present at the accepted RG-005 geometry; scoring displays the complete value without losing high
digits; score plus `1UP` persist on unchanged frames; death/restart and Continue return to gameplay
with the correct score/HUD; and no frontend lock recurs.

## Status

Build 0472 is a validated candidate. RG-009 is awaiting Tighe's real-hardware acceptance. STOP.
