# Cody Build 0400 Pre-implementation Independent Verification

Status: **AUDIT COMPLETE — NO PRODUCTION CHANGE, NO ROM, COUNTER 400**

This is an independent source/disassembly/instrument review of Andy's Build-0400 frame-worker audit. No pending LIGHT/MEDIUM/HEAVY measurements are treated as evidence.

## Executive verdict

Andy's central static findings are confirmed: the original worker body is normal-callable in principle; Build 0400 executes publication followed by the arcade worker inside one IRQ6 lifetime; SAT is double-buffered while every other publication contract, including the sprite tile-DMA list, is single-buffered or mutable.

The supplied timing trace is **not safe as written for the conclusions advertised**. Its variable called `irq6_total` counts writes to `pc090oj_emitted_count`, not IRQ6 entries; its dropped-frame result is therefore producer-pass versus display-frame, not serviced-IRQ6 versus physical-VBlank. It has no worker-end/RTE observation. Its VDP-PC gate uses broad numeric ranges that create both false positives and false negatives. Its target counters count decoded VDP address commands, not transfer duration. These are material instrumentation corrections, not contradictions of the static architecture.

The gameplay run should not be used until the result interpretation is corrected (or the trace is corrected in a separately authorized task). No trace tool was changed here.

## 1. Original arcade frame worker

Independent evidence:

- ROM vector longword at offset `0x74` is `0x0003A008` (Level-5 autovector).
- Original `0x3A008`: `ori.w #0x0F00,sr`.
- `0x3A00C`: clear of `0x350008`; `0x3A012`: watchdog/IO write to `0x3C0000`.
- The semantic body begins at `0x3A018`, executes the game-mode gate, calls `0x3A126`, `0x41F30`, `0x3AB7C`, `0x3ABE2`, `0x3A0A8`, `0x3EEFA`, `0x3EF5C`, and dispatches through the state table.
- `0x3A052` uses `PEA 0x3A074` as an ordinary computed-dispatch return address. It is not an exception-frame access.
- `0x3A074` calls `0x55CA2`; `0x3A07A` restores the mask with `andi.w #0xF0FF,sr`; `0x3A07E` is `rte`.

No instruction in `0x3A018–0x3A074` reads the stacked SR or PC, derives data from an exception-frame offset, or requires exception-stack layout. Therefore the body is normal-callable in principle after replacing its interrupt wrapper with an ordinary call/return boundary. This does **not** make current Genesis production/preparation state preemptible: publication-visible WORK state is not isolated from READY state.

Classification: Andy's original-worker claim **CONFIRMED**. Current Genesis preemptibility today: **CONTRADICTED/FALSE** if asserted without isolation (Andy does not ultimately assert it is safe today).

## 2. Exact input-age semantics

The original disassembly contains direct reads of the live TC0040IOC input addresses at multiple points, including `0x390007` at `0x3A6`, `0x390001` at `0x3F4`, `0x390003` at `0x438`, and repeated reads of `0x390005` within `0x3A0A8`, plus later frontend/game-state routines. There is no one centralized frame latch supplying all of these reads.

Build 0400 calls `rastan_direct_update_inputs` at `_vblank_service+4`, before sprite preparation and publication. It polls the Genesis controller ports once and writes exactly one byte each to:

- `genesistan_shadow_input_390001` = `0xFF61F6`
- `genesistan_shadow_input_390003` = `0xFF61F7`
- `genesistan_shadow_input_390005` = `0xFF61F8`
- `genesistan_shadow_input_390007` = `0xFF61F9`

Retained arcade operands are redirected to those bytes. Consequently, all reads during that Build-0400 IRQ/tick see one frozen IRQ-entry sample. Original code may observe a controller change at different moments during the same tick; Genesis cannot.

Classification: same nominal Tick-N age, but **PARTIAL**, not exact same semantics.

## 3. Publication dependency graph

`dma_publish_frame` publishes, in order: palette, generic tiles, Plane B, Plane A, sprites, scroll.

| subsystem | publisher input | buffering/read-set |
|---|---|---|
| palette | `palette_pending`, `staged_palette_words` | single mutable snapshot |
| generic tiles | `tiles_dirty`, `staged_tile_words` | single mutable job |
| Plane B | `bg_row_dirty`, `staged_bg_buffer` | single mutable masks **and source words** |
| Plane A | `fg_col_dirty`, `fg_narrow_desc_count/table`, `fg_row_dirty`, `staged_fg_buffer` | single mutable descriptors/masks **and source words** |
| sprites/SAT | `pc090oj_sat_frame_ready`, bank/front metadata, two SAT arrays | SAT data is double-buffered |
| sprite patterns | `pc090oj_tile_dma_count/worklist` | single mutable list/count |
| scroll | staged H/V scroll words | single mutable words |

The sprite publisher reads only the tile-DMA descriptors to choose each upload; it does not read the resident-code table to choose a DMA. It does, however, write `sprite_tile_resident_code` after DMA, clears shared `worklist_entry_for_slot` reservations, and clears the shared list count. The producer reads/mutates the resident table, reverse directory/pages, reservation map, worklist and count.

Thus Andy's narrow statement “publisher needs descriptors, not an allocator lookup” is confirmed, but list double-buffering alone is not a complete later-preemption contract unless the handoff protocol also prevents the publisher's residency/reservation updates from racing a WORK producer. Likewise, swapping only Plane A/B dirty masks is insufficient if the source words in the underlying staged buffer can change before READY publication.

Classification: broad WORK/READY prerequisite **CONFIRMED WITH CORRECTIONS**.

## 4. Timing instrument: what each metric actually observes

| reported metric | actual event | exact/proxy | ambiguity |
|---|---|---|---|
| physical VBlank/display frames | `emu.register_frame_done` callback | reliable display-frame cadence proxy | not a direct VDP VINT assertion counter |
| `irq6_total` | write tap on `pc090oj_emitted_count` (`0xFFBED4`) | exact emit-finalizer writes | **not IRQ6 entry**; fallback/frontend or mode paths can affect equivalence |
| input writes | writes in two-byte range `0xFF61F6–F7` | exact two shadow writes per completed `update_inputs` call in canonical Build 0400 | script must divide by two; it does not promote this independently to the headline count |
| gameplay tick | emit-count write | producer-pass proxy | requires proof of exactly one emit finalizer per gameplay tick in the measured state |
| producer done | emitted-count store in `.Lnq_store` | exact point inside emit finalization | two ready/dirty stores, register restore, returns, and substantial enclosing arcade worker work can remain |
| publication begin/end | first/last VDP-port write accumulated between emit writes | coarse beam-span proxy | can include gaps and any unrelated VDP writer; scanline resolution; not transfer time |
| per-target publication | decoded VDP address/code command | target-command count proxy | payload writes are not counted; count is neither bytes nor cycles nor DMA duration |
| emitted sprite count | word read from emitted count at its write tap | exact value at that marker | bucket is producer output, not IRQ identity |
| worker completion/RTE | nothing | unobserved | no existing trace marker brackets RTE |

The `dropped_frames` test compares display callbacks with producer-marker changes. It does not compare display callbacks with serviced IRQ6 entries. Calling this “coalesced VINT proof” is invalid.

### Serviced IRQ6 delimiter

Static final-ROM/source evidence shows one call to `rastan_direct_update_inputs` from `_vblank_service`, before any game-mode gate, and each completed canonical invocation writes the four shadow bytes once. The tap covers the first two bytes, so a normal completed service produces exactly two tap events. In ordinary steady gameplay, `input_writes / 2` is therefore a strong serviced-handler delimiter, provided the count is even and capture boundaries do not split a call.

This equivalence is conditional rather than universal: reset/boot intervals where IRQ6 is not serviced, exceptional interruption before the second store, alternate diagnostic/cheat code, and capture start/stop inside a call need exclusion. Title, pause, and scene game-mode gates do not by themselves break it because the input call precedes them.

The existing summary incorrectly uses producer passes for its headline `ticks/frame` and dropped-frame calculation instead of promoting this independent delimiter.

## 5. Genesis VINT model

The CPU IPL mask only prevents acceptance; it does not define VDP event queuing. Current MAME's Sega 315-5313 device has one `m_irq6_pending` flag, sets it at VBlank, exposes it in status bit 7, and asserts the level-6 callback when enabled. This is a single pending condition, not a counted queue of VBlank events. Repeated physical VBlanks while the same pending condition remains cannot accumulate an arbitrary interrupt count, so coalescence is possible in that model. The exact acknowledgment/clear path is device/driver behavior and is not established by the project trace itself.

Classification of Andy's “IPL7 therefore VBlanks collapse” statement: **PARTIAL**. The MAME VDP model supports one-pending-state coalescence, but IPL7 alone is insufficient proof and the current trace does not directly observe VINT assertion/acknowledgment. Source reviewed: upstream MAME [`src/devices/video/315_5313.cpp`](https://github.com/mamedev/mame/blob/master/src/devices/video/315_5313.cpp).

## 6. Why `ticks/frame < 1` is not sufficient

For a valid coalescence conclusion, compare a clean steady-state physical-frame count with the independent serviced-handler count (`input_writes/2`), verify even writes and capture boundaries, and separately compare serviced handlers to gameplay producer completions. Exclude boot/loading/transitions or label them separately.

Current `irq6_total/ext_frames` instead compares producer finalizers with display frames. A skipped producer, a fallback producer, more than one legitimate emit call, or a state transition can change that ratio without proving a lost/coalesced VINT.

## 7. The 16.67 ms question

`pc090oj_emitted_count` is written near the end of `pc090oj_native_emit_pass`, not at worker RTE. Even within the finalizer, ready/dirty stores and epilogue remain; after it returns, its caller and the original arcade dispatch/common tail can continue before runtime `0x3A27A/0x3A27E`.

Therefore producer-done beam V **cannot prove total worker duration or whether the complete tick fits 16.67 ms**. It can show when sprite emission reaches that marker and correlate that phase with emitted-sprite load.

No guaranteed final memory write immediately before the worker RTE was found in the existing instrumentation/source contracts. Frame-done PC sampling is not an exact substitute. Exact whole-worker duration remains unavailable without a genuine entry/exit observation; this audit does not create one.

## 8. VDP gate audit

Current detector: any VDP write from outside runtime `0x70000–0x767FF` is an offender; only PCs in `0x3A000–0x5FFFF` increment `gate_fail_total`.

Verdict: **PARTIAL/NOT A VALID SEMANTIC GATE**.

- Address-map proof shows the worker head at `0x3A208`, but the retained call tree is not one contiguous semantic range. A callee can lie outside `0x60000`, producing a false negative.
- The accepted “publisher” range contains native producers/helpers as well as publication code, so an illegal post-publication native VDP write in that broad range is a false negative.
- Retained init at `0x3Bxxx` lies inside the fail range. The report labels it “boot, ok” only after already incrementing `gate_fail_total`, creating a false positive in captures that include initialization.
- The detector is global; it does not establish the required temporal context “after `dma_publish_frame`, before worker RTE.”
- The MAME address-range write tap can observe VDP byte/word/long bus writes, but the script ignores `mask`, and command reconstruction assumes callback/address/width behavior. Attribution is a PC heuristic, not call context.

Before using it as a gate, classification must be exact publication routine membership plus a worker-phase boundary (or equivalent call-context state), with boot/init excluded rather than merely relabeled.

## 9. VDP command/sub-phase audit

The command decoder's CD and 16-bit VDP-address formulas match MAME's `update_code_and_address`: command part 1 provides CD0..1/address 0..13 and part 2 provides CD2..5/address 14..15. When the write tap delivers the assumed complete/split control writes, target address classification is sound.

- CRAM: reliable command-target proxy, not bytes/duration.
- generic/sprite tiles: VRAM-address-range proxy; both collapse into `tiles`, not separable.
- Plane B: reliable address-command proxy for `0xC000–DFFF`, not payload/duration.
- Plane A: reliable address-command proxy for `0xE000–EFFF`, not payload/duration.
- SAT: reliable address-command proxy for `0xF800–FBFF`, not payload/duration.
- scroll: VSRAM commands are counted; HScroll is VRAM and therefore classified as `tiles` by this address scheme. The report has no separate `scroll` counter.

The publication beam span brackets first-to-last observed VDP writes, not each subphase; the distribution is address-command frequency only.

## 10. Throughput-case review

Rescheduling does not reduce workload cycles. If the complete current IRQ workload comfortably fits within one NTSC frame and IRQ6 is enabled/serviced normally, the current architecture should already be capable of one service/tick per frame. A claim that moving the same work to mainline restores 60 Hz requires a separately proven scheduling penalty (for example, a single pending VINT condition combined with a real overrun), not merely proof that work exists in IRQ context.

If work exceeds 16.67 ms, preemptible scheduling can improve VBlank publication responsiveness and prevent one long IPL7 critical section, but sustained gameplay tick rate remains bounded by total CPU cost. “Slight overrun = proportional slowdown” and “substantial overrun = optimization needed” are reasonable planning cases, not measured conclusions.

## 11. Build 0401 proposal review

Proposed scope: keep the producer in its current IRQ position and add WORK/READY sprite tile-DMA worklists/counts, with no scheduling move.

Verdict: **APPROVED WITH ADDITIONAL PREREQUISITE**.

As an isolation-only build, a complete-list handoff can be correctness-preserving and is the smallest useful sprite prerequisite. For it to be sufficient for later preemption, the contract must also:

1. publish only a complete READY generation and never a WORK list;
2. prevent publisher writes to `sprite_tile_resident_code` and `worklist_entry_for_slot` from racing the producer's allocator/reservation decisions (by ownership transfer or a proven generation/scheduling invariant);
3. keep the READY SAT bank paired atomically with its READY pattern list;
4. clear/reset only READY-owned list/reservation metadata;
5. prove no new WORK generation starts while an older READY transaction can still mutate shared allocator state.

Double-buffering list/count alone does not state those ownership rules.

## 12. Evidence partition

### Proven now

- Original vector/handler/body/wrapper PCs and lack of exception-frame dependence.
- Original live input reads versus Build-0400 IRQ-entry snapshot semantics.
- Build-0400 input helper placement and exactly four shadow stores (two in the trace's tapped range).
- Publication order and buffer/read/write ownership described above.
- SAT double buffering and single sprite tile-DMA worklist.
- The exact events observed by every current trace metric.
- Absence of a current exact worker-end/RTE marker.
- Numeric VDP-PC gate defects and command-count limitations.

### Requires Tighe LIGHT/MEDIUM/HEAVY run (after interpretation/tool correction)

- Load-correlated sprite marker position and emitted-count distribution.
- Publication first/last-write span and command-target distribution as proxies.
- Steady-state physical display frames versus independently counted completed input-helper calls.
- Serviced handler count versus producer completions in each controlled gameplay regime.
- Runtime occurrence of any VDP writes outside exact publication ownership, once a valid contextual gate exists.

### Current trace cannot prove

- Exact VDP VINT assertion/acknowledgment count.
- Exact whole-worker/RTE completion time.
- That the entire workload fits 16.67 ms from producer-done alone.
- VINT loss/coalescing from producer-completion ratio alone.
- Exact duration/cycle cost of CRAM/tiles/Plane B/Plane A/SAT/scroll subphases.
- Semantic absence of post-publication worker VDP writes using the current broad PC heuristic.

## Claim-by-claim classification

| claim | result |
|---|---|
| original worker normal-callable in principle | **CONFIRMED** |
| current worker safely preemptible today | **CONTRADICTED/FALSE** |
| input has exactly same age semantics | **PARTIALLY CONFIRMED** |
| SAT double, tile worklist single | **CONFIRMED** |
| publisher does not consult allocator to choose DMA | **CONFIRMED** |
| worklist isolation alone completes future preemption safety | **NOT PROVEN** |
| `input_writes/2` delimits completed serviced handlers in clean canonical steady state | **CONFIRMED CONDITIONALLY** |
| producer writes count serviced IRQ6 | **CONTRADICTED** |
| current trace proves VINT coalescing | **CONTRADICTED** |
| producer-done proves whole tick fits | **CONTRADICTED** |
| current VDP-PC gate is sufficient | **CONTRADICTED** |
| decoded target counts are publication durations | **CONTRADICTED** |

Production source changed: **NO**. ROM produced: **NO**. Counter remains **400**.
