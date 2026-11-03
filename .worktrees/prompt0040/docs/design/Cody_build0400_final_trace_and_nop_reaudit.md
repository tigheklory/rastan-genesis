# Cody — Final Build-0400 Exact Trace + NOP / Semantic-Remap Re-Audit

Status: final independent audit plus trace-only correction. No production source change, ROM, or build-counter change.

## Decision

The debugger-exact mechanism is valid, but the version presented for review was not yet safe for the controlled
run: its permissive event state machine could pair across a missing event, it did not report incomplete pairs, its
scene-only arm included scene-1 READY/frontend time, and its VDP offenders lacked the required exact chronology.
Those defects were corrected only in `tools/mame/scripts/frame_timing_trace.lua` and its runner. The corrected trace
is approved for one Tighe-controlled LIGHT/MEDIUM/HEAVY run. Tighe must enter normal gameplay and press **M once**;
that resets and arms the complete measurement interval. A startup smoke test confirmed that MAME accepts the exact
breakpoints and VDP debugger watchpoint and runs with automatic continuation. Gameplay results remain pending.

## Exact timing and pairing

The four points are MAME debugger **execution** breakpoints:

- `PUB_ENTRY 0x70250`: first instruction of `dma_publish_frame`.
- `PUB_RTS 0x702D2`: its `rts` instruction.
- `WORKER_ENTRY 0x3A208`: first retained worker instruction (`ori #0x0F00,sr`).
- `WORKER_PRE_RTE 0x3A27E`: the worker's `rte` instruction, before execution returns to the interrupted context.

The action prints debugger expression `totalcycles`, frame, and HV, then executes `g`. `totalcycles` is the
emulated 68000 cycle counter. Halting the host debugger to print does not insert an emulated instruction or advance
emulated cycles. No ROM instruction is inserted. An execution breakpoint fires once each time its PC is executed;
the obsolete opcode-fetch read tap is gone.

The corrected parser accepts only `PE -> PR -> WE -> WR`. A new PE rejects any open partial handler; any other
out-of-order event increments an orphan/rejection count and clears the state. Metrics are committed only at WR after
the full four-event sequence. Thus PE/PR and WE/WR cannot cross handlers, first/last partial records are excluded
and reported, and missing events cannot silently attach to the next handler. Frame crossings use debugger `frame`;
cycle deltas use `totalcycles`, never beam subtraction.

## Publication ownership and VDP accounting

Static ordering in `dma.s` is:

`PUB_ENTRY -> save registers -> VC_MARK0 -> palette -> MARK1 -> tiles -> MARK2 -> Plane B -> MARK3 -> Plane A -> MARK4 -> sprites -> MARK5 -> scroll -> MARK6 -> restore registers -> PUB_RTS`.

Therefore MARK0 precedes the first commit VDP access and MARK6 follows return from the final scroll commit. In the
normal Build-0400 display-on variant there is no VDP access between MARK6 and PUB_RTS. The optional forced-blank
variant would write display-on after MARK6, so VC marks are not a future-general ownership bracket.

The corrected trace consequently uses the exact debugger `PUB_ENTRY/PUB_RTS` chronology for ownership. A debugger
write watchpoint on `0xC00000..0xC00007` records totalcycles, frame, HV, writer PC, port, access width, and data.
VC_MARK writes are retained only as actual subphase events. Every outside-bracket VDP access during the armed run is
an offender; the summary includes exact examples. Execution-watchpoint `wpsize` is the actual full CPU access
width: long and word command forms decode; byte/unsupported widths and incomplete command pairs are UNKNOWN.

Only control commands inside publication contribute target counts. VRAM is classified as Plane B
`C000-DFFF`, Plane A `E000-EFFF`, SAT `F800-FBFF`, HScroll `FC00-FFFF`, otherwise generic pattern VRAM. CRAM and
VSRAM use their command codes. These are command counts, not bytes, cycles, DMA duration, or subphase duration.

## Controlled interval

Logical scene 1 is the correct inclusion gate for normal gameplay: package/tileset IDs 3-8 normalize to logical
scene 1; scene 2/end-round is excluded. Scene 1 alone is not a sufficient start marker because READY/frontend time
can remain scene 1. The corrected trace requires the first rising edge of **M while scene 1 is active**. At that
point it resets display frames, exact pairs, input/producer counters, targets, gate state, load buckets, chronology,
and pairing state together. All numerators and denominators therefore cover the same interval. Zero denominators
print N/A; odd input writes print INCOMPLETE/CAPTURE BOUNDARY; unmatched sequences are excluded and reported.

Andy's 651 pairs and timing extrema are forced-arm attract/frontend self-test data only. They are not representative
gameplay timing and must not enter LIGHT/MEDIUM/HEAVY interpretation.

## Current and target semantics

Build 0400 samples the controller near IRQ6 entry, guards sprite readiness, publishes the previous complete staged
frame, then runs one complete sequential arcade worker at IPL7 and RTEs. The target keeps Tick N, N+1, N+2 order:
no tick skip, dropped simulation tick, backlog, or catch-up burst. Under overload it repeats the prior complete
display and accepts slowdown. IRQ6 publishes only one immutable READY generation, sets saturating `tick_pending=1`,
and RTEs immediately after required VDP work; it does not wait for physical VBlank to end. When the current tick
finishes, WORK becomes READY; if pending, mainline samples and freezes all four redirected input bytes immediately
before beginning exactly the next tick. That snapshot remains stable across preemption.

READY isolation remains a later implementation prerequisite, not a timing-run blocker. Plane A/B ownership must
bind dirty descriptors, staged source words and generation while preserving incremental Plane-A. Sprite ownership
must bind generation, SAT bank, pattern worklist/count, source descriptors, ready/dirty and cancellation state, and
reservation-cleanup metadata. The allocator/residency race remains unresolved.

## Watchdog/IO and semantic worker cut

Original arcade `0x3A00C` is `clr.w 0x350008` (6 bytes) and `0x3A012` is
`move.w d0,0x3C0000` (6 bytes): two instructions, 12 bytes. Runtime `0x3A20C..0x3A217` is six NOPs and executes
once in every current serviced worker. Runtime `0x3A208` is the separate IPL7 raise. `0x3AB7C` is real common
bookkeeping/warm-restart gating and must not be removed based on historical “watchdog” terminology.

The future cut is: Genesis IRQ6 owns complete READY VDP commit, pending-bit set, and RTE; the normal mainline worker
owns the retained game-semantic body and returns by RTS. The mainline worker must omit IPL7 wrapper operations,
arcade-only watchdog/IO, IRQ SR glue, RTE, and their NOP substitutes through semantic shortening—not branch around
or pad them.

## Diagnostic bookmark facility correction

Andy's “not identified” statement is corrected. `RULES.md` Rule 10 defines the **Diagnostic Bookmark** lifecycle.
The permanent inert helper is `genesistan_diag_bookmark`, body `60 FE` (`bra` self), in
`apps/rastan-direct/src/diag_bookmark.s`. A transient `bookmarks_v2` entry identifies a runtime Genesis PC and an
instruction **span**, verifies canonical pre-insert bytes, and writes a `JMP_LONG_ABS` activator to the symbol plus
NOP fill for the selected span. It is not necessarily one two-byte instruction. `postpatch_startup_rom.py` applies
and records it, using `active_bookmark_baseline.json` for the insert/revert lifecycle.

BM-003 proved the mechanism at runtime `0x3A19C`: canonical prefix `66 F4`, activator
`4E F9 00 07 1C 78 4E 71`, helper park reached, then the next ROM-producing revert restored canonical bytes and
removed active state. BM-009/BM-010 additionally prove `bookmarks_v2` in Genesis-native regions. Temporary activator
NOP fill is a Rule-10 diagnostic-span detail; it is not permission for permanent production NOP scaffolding. This
timing trace correctly uses non-invasive MAME breakpoints and builds no bookmark ROM.

## Final-ROM decoded NOP inventory

Independent decoded-instruction parsing of `build/genesis_postpatch.disasm.txt`, grouped into consecutive two-byte
runs and joined against `address_map.json`, gives:

| provenance | instructions | bytes |
|---|---:|---:|
| unchanged `arcade_copy` (original Taito) | 20 | 40 |
| `patched_site` / remapper introduced | 1,475 | 2,950 |
| `genesis_only` native assembly | 4 | 8 |
| unresolved provenance/data ambiguity | 0 | 0 |
| **total** | **1,499** | **2,998** |

There are 85 runs: 39 single-NOP and 46 multi-NOP. Contrary to Andy's provisional 12/231 and 3/76 statement, exact
JSON parsing finds **65/231 `opcode_replace` entries**, containing all 1,475 literal NOPs, and **0/76
`shift_replacements` entries** containing NOPs.

The four native NOPs are runtime `0x723A6`, `0x723B8`, `0x723DE`, and `0x723F0`, immediately after P1/P2 Genesis
TH/data transitions. They are required controller settle-time delays, not cleanup debt.

Every reported major run is remapper-introduced dead fill following the replacement's control transfer/return, not
live code reached through its semantic entry: `0x5A11A x245` (status direct-native replacement), `0x41FB6 x172`
(PC090OJ 0x41DAE replacement), `0x46002 x125` (0x45DFA replacement), `0x3CB58 x112` (text/default writer),
`0x3BA0A x83` (HUD digit producer), `0x3C4EA x73`, `0x3C78E x60`, `0x54176 x57`, `0x3C83E x55`, and
`0x56114 x43`. In particular `0x41FB6` follows the replacement JSR/RTS and is not runtime CPU cost.

Proven ordinary serviced-tick cost is ten NOP executions = 40 MC68000 cycles: six removable watchdog/IO NOPs =
24 cycles, plus four required controller-settle NOPs = 16 cycles. No additional multi-NOP run is live through its
replacement entry. Small original/padding NOPs may be conditional on individual frontend/game-state paths; this
audit makes no invented per-tick count for unproven paths. ROM-size debt (2,950 remapper bytes) is therefore sharply
different from guaranteed runtime debt (24 removable cycles per current tick).

## Semantic remapper and address reflow

`specs/rastan_direct_remap.json` is authoritative; `postpatch_startup_rom.py` orchestrates;
`shift_table_patcher.py` splices variable-length replacements. The current spec itself has 23 negative, 26 zero,
and 27 positive shift deltas, directly proving shorter replacements. Supported repair includes 8/16-bit
BRA/BSR/Bcc, declared missing branch boundaries, JSR/JMP/PEA/LEA/MOVEA.L and other enumerated absolute-long forms,
declared word-displacement jump tables, declared absolute-long pointer tables, and the postpatcher's whole-maincpu
relocation/table passes. Automatic jump-table discovery remains a stub, so relevant tables must stay declared.

Future worker cleanup therefore needs no permanent NOP padding. Because shortening moves code, Build-0400 PCs are
measurement constants only; future tools must resolve native symbols from `symbol.txt` and retained arcade/runtime
locations from `address_map.json` and generated remap manifests.

## Protected behavior

This audit changes no gameplay or production assembly. It does not reopen the Build-0399 combined-X/Y Plane-A
fix, Build-0400 rope-exit fix, or Build-0400 black-strobe fix. Ordinary `fg_boundary_install` remains display-on;
major scene-entry blanking under `genesistan_scene_present_pending` remains available.

## Final verdict

After the bounded trace-only corrections above: **APPROVED FOR TIGHE CONTROLLED GAMEPLAY RUN**. Run the existing
runner, enter normal gameplay, press M once, then capture LIGHT, MEDIUM, and HEAVY regimes. Gameplay gate verdict
and performance numbers are pending that run. No ROM was produced; counter remains 400.
