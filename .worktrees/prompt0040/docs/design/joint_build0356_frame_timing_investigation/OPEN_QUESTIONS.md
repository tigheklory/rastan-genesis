# OPEN_QUESTIONS - Build 0356 Frame-Timing Investigation

Tracking: each Andy item is preserved and answered as **RESOLVED**, **UNRESOLVED**, or
**NOT MEASURABLE WITH CURRENT HARNESS**. This is Cody's first-pass response; Andy may
reopen an item if semantic review identifies a missing distinction.

## Priority 1 - Separate The Interrupt Events

- **A-1 (Q1): Name the timestamped event. - RESOLVED.** The prior approximately 86%
  result timestamped `dma_publish_frame` entry at native Genesis PC `0x070250`, the
  first publication-section boundary. It did not timestamp physical VBlank or IRQ6
  assertion/service. Evidence: preserved Build 0356 physical-beam capture and
  `CODY_MEASUREMENTS.md` sections 3, 5, and 7.
- **A-2 (Q2): Timestamp the full chain per frame and classify it. - RESOLVED, with
  one instrumentation limitation.** The 1,800-frame trace records physical beam epoch,
  IRQ6/`_vblank_service` entry, publisher entry/return, copied handler entry/state
  dispatch, pre-RTE, RTE, PC, SR/IPM, H/V counter, and next physical VBlank. MAME did
  not expose a separate VDP IRQ-assert edge, so one IRQ condition is inferred at each
  calibrated physical VBlank phase. Counts: A=256, B=244, C=755, E=1 over all complete
  chains; gameplay A=256, B=3, C=749. Evidence: authoritative raw CSV and reduction in
  `states/traces/build0356_joint_frame_timing_20260914/`.
- **A-3 (Q2 corollary): Is IRQ6 service entry itself in active display? - RESOLVED.**
  Yes, on 749 of 1,008 complete gameplay chains. These are service-entry measurements,
  not publisher-entry proxies. The late cases correlate with the preceding Level-6
  continuation crossing the associated physical VBlank.

## Priority 1 - Interrupt Masking

- **A-4: Locate copied-handler SR discipline. - RESOLVED.** `_vblank_service` tail-jumps
  to `runtime_genesis_pc 0x03A208` / `arcade_pc 0x03A008`. The copied handler starts by
  raising IPM to 7, state dispatch is at runtime `0x03A252` / arcade `0x03A052`, patched
  `ori.w #$0600,sr` is at runtime `0x03A27A` / arcade `0x03A07A`, and final RTE is at
  runtime `0x03A27E` / arcade `0x03A07E`. RTE restores the stacked interrupted SR.
  Mappings are from `build/rastan-direct/address_map.json`.
- **A-5: Does VBlank occur while Level-6 continuation is active, and is pending IRQ6
  accepted when it completes? - RESOLVED for observed gameplay.** In 749 gameplay Case-C
  chains, the prior RTE occurs after the physical VBlank. The pending service follows
  RTE in 67-84 dots (median 73). The longest measured VBlank-to-service delay is 127,640
  dots. Stacked gameplay IPM is always 0 while live service IPM is 6. This confirms
  H-CONT for those observed cases, not a permanently masked ordinary mainline.

## Priority 1 - Frame, Tick, And Advance Relationship

- **A-6: Count all frame/tick events and prove gameplay advance. - RESOLVED.** Over
  1,800 external frames: 1,800 physical VBlank opportunities, 1,257 IRQ6/service entries,
  1,257 publisher calls/returns, 1,257 copied IRQ/tick entries, and 1,256 RTEs (one chain
  open at capture end). There are 1,008 complete `[2,3,0]` gameplay dispatches. Static
  control flow gives one `runtime_genesis_pc 0x04210E` / `arcade_pc 0x041F0E` entry per
  gameplay dispatch; the supplement directly observes 383 entries for 383 gameplay
  chains. Thus the full mixed startup/gameplay capture proves 1,008 gameplay advances.
  The `1257/1800` rate is 41.84 service entries/sec, not a steady gameplay rate.

## Priority 2 - Whole-Frame CPU Breakdown

- **A-7: Break down publisher-exit through copied continuation. - RESOLVED to the
  largest measured regions.** Full-capture medians are 3,028 dots publication, 157,457
  dots copied continuation, and 163,310 dots full chain. The hierarchy separates an
  early update/finalize region (91,068-dot median, almost entirely native sprite path
  `0x041DAE`) and later copied gameplay state dispatch (52,944-dot median in the
  supplement). Largest copied subregions and authoritative mappings are listed in
  `CODY_MEASUREMENTS.md` section 8.
- **A-8 (Q7): Useful work versus waits/polls/recomputation. - RESOLVED at the current
  profiling resolution.** The long regions contain executed copied gameplay routines
  and native sprite staging/finalization. No VDP-status/chip-ready polling loop was found
  in the measured continuation. Whether particular copied routines perform avoidable
  recomputation is a semantic-review question, not established by timing alone.
- **A-9 (Q9): Native producer cost. - RESOLVED for the dominant sprite path; bounded
  UNKNOWN for exact Plane A/B producer CPU cost.** Native stage dispatch is 21,623 dots
  median and finalization is 67,300 dots median over 383/383 gameplay chains. Back/enemy
  emission is the largest finalizer lane (42,082 dots median); emitted-count/finalizer
  Pearson correlation is 0.89995. Publication Plane A/Plane B/DMA costs are measured
  separately. The current harness does not isolate exact Plane A and Plane B semantic
  production CPU regions, so no producer-cost claim is made for them.

## Priority 2 - Translated Arcade Timing Constructs

- **A-10: Identify and cost obsolete busy-waits or hardware polls. - RESOLVED for the
  measured chain.** No costly VDP-status, frame-ready, or chip-ready polling loop was
  observed in the measured handler continuation. The short mainline synchronization
  loop around runtime `0x03A1A8` and `0x03B27E..0x03B296` appears in interrupted-PC
  samples, but late IRQ acceptance follows prior RTE in only 67-84 dots. The trace does
  not establish that loop as removable hardware-tail code.

## Priority 3 - Housekeeping

- **A-11 (Q10): Confirm `VC_MARK`/`vblank_vc` overhead. - RESOLVED.** It remains in the
  numbered Build 0356 ROM. Preserved publication measurements place its median overhead
  at about 379 dots / 0.777 line (range 371-404 dots). It is diagnostic scaffolding for
  removal only in a future meaningful production build; no build is authorized here.
- **A-12 (Q4): Confirm VDP VINT stays enabled. - RESOLVED for observed/static inventory.**
  The trace saw register-1 writes `0x8134` twice and `0x8174` once; all retain VINT bit 5.
  No VINT-disable write occurred in the observed gameplay. This is bounded to the capture
  and current static writer inventory, not an assertion about every unreachable path.

## Cody First-Pass Disposition

- Resolved: A-1 through A-12, with the explicit measurement bounds above.
- Still unresolved from the original list: none required to establish the first-pass
  timing result.
- Not measurable with current harness: the exact VDP-internal IRQ assertion edge and
  isolated Plane A/B semantic producer CPU costs. Neither blocks H-CONT classification.
- Next action: Andy reviews methodology, semantic classifications, and candidate boundaries.
  `FINAL_CONSENSUS.md` remains pending.

## Andy re-review (2026-09-14) — reopened item

Andy reviewed Cody's first pass against raw evidence + source. **A-1..A-12 accepted** (see
ANDY_REVIEW §D; classifications AGREE / AGREE-WITH-QUALIFICATION). H-CONT confirmed; the #1 target
(native sprite finalizer 49-slot per-entry residency search) is established from source. Exactly
**one** item is reopened because it materially changes the optimization decision:

- **A-13 (REOPENED — Cody second pass, single targeted measurement): decompose the finalizer's
  per-emitted-entry cost into (a) the residency search loops `.Lnq_lookup_loop` + `.Lnq_vloop`
  (`pc090oj_hooks.s`, final-ROM ~0x073C80 / free-cell scan) versus (b) the rest of `.Lnq_emit_entry`
  (blank/HUD tag, X/Y wrap, flip, opaque-bbox viewport clip, SAT write, palette-map lookup) plus the
  fixed finalizer overhead (setup ~11.7 ln, HUD lane ~12.5 ln, bookkeeping).** Bracket the two search
  loops with beam marks (or count their iterations) over the same 383 gameplay chains, ideally split
  by hit vs miss. Deliver: median dots attributable to the search vs the rest, per emitted entry.
  **Why it matters:** it decides whether replacing the search with an O(1) `code→slot` index (§F)
  alone drops the **median** chain below one 262-line frame (§G shows the answer is currently between
  "just crosses" and "needs a second target"). Nothing else is reopened.

Not reopened (deliberately): copied-core sub-purpose (0x05100A/0x040B66/0x0420E6) — a Ghidra/semantic
question, Andy's later static work, not a Cody trace, and not decisive for #1; Plane A/B producer CPU
isolation — bounded UNKNOWN, not decisive for #1; VDP internal IRQ-assert edge — NOT MEASURABLE with
this harness and not needed (H-CONT stands on the RTE/IPM evidence).

`FINAL_CONSENSUS.md` remains **not written** pending Cody's A-13 result.
