# Cody Build 0400 Repaired Trace Independent Re-audit

Status: **NOT YET APPROVED FOR TIGHE'S CONTROLLED GAMEPLAY RUN**  
Scope: trace/timeline audit only; no production change, ROM, or counter increment.

## Executive result

The repaired script correctly separates producer completions from serviced-handler intent and correctly admits that worker exit is unobserved. It is nevertheless not ready for the one controlled gameplay capture:

1. `serviced_irq6` is still an instruction-address **read tap**, not a guaranteed execute event. Repository evidence already records that MAME program read taps are not strict execution taps and may undercount translated 68000 execution. The one-count mismatch is plausible as an in-flight capture boundary, but the script records no event ordering with which to prove that explanation.
2. Gameplay ratios divide lifetime-global IRQ/producer totals by gameplay-only `armed_frames`. A run containing title/READY before controlled gameplay will produce invalid ratios.
3. VDP target-command counters are lifetime-global and include initialization/frontend/non-publication traffic, despite being labeled publication counts.
4. `publication_outer_span` brackets every VDP write and resets only at a producer marker; it is not restricted to `dma_publish_frame`, so post-publication, initialization, fallback-producer, and next-frame traffic can contaminate association.
5. The VDP whitelist is not exact function membership. It includes generic VDP helpers, `_vblank_service`, and the scene-only `vdp_install_test_lines`, allowing non-publication writers to pass.
6. Zero-denominator ratios print `0.0000` instead of `N/A / NOT EXERCISED`.

Established MAME debugger breakpoints already provide an exact, non-ROM execution mechanism (`cpu.debug:bpset` with `totalcycles`, `beamx/beamy` or `w@C00008`, and automatic `g`). The repository's Build-0354/0356 tools use it. Therefore a diagnostic ROM is not required before useful timing capture; the trace/runner should use exact breakpoints and be rechecked first.

## 1. Serviced IRQ6 marker

Final Build-0400 control flow is:

`_vblank_service 0x700C2 -> update_inputs -> vdp_prepare_sprites -> dma_publish_frame -> restore registers -> JMP 0x3A208`.

There is no identified non-IRQ caller of `0x3A208`. Static control flow therefore makes execution of `0x3A208` a strong worker-entry/serviced-handler indicator.

The actual Lua mechanism is `prog:install_read_tap(0x3A208,0x3A209,...)`. An address-space read tap observes reads, not architecturally retired instructions. “JMP target” does not itself prove one callback: 68000 fetch/prefetch behavior, translated-core access routing, restart, and capture timing remain properties of the emulator mechanism. Existing repository findings explicitly warn that instruction-address read taps are not strict execute taps and have undercounted later execution.

The repaired attract reports both `832 vs 833` and the retained summary reports `252 vs 253`; each has one additional completed input call. This is consistent with summary/stop occurring after the two early input stores but before the later tail-JMP/fetch. It is not proven because the script logs only aggregate counters, not the last event sequence. An exception/restart or read-tap omission is not excluded by those aggregates.

Verdict: `0x3A208` read tap is a **strong proxy**, not an exact serviced-IRQ6 marker.

## 2. Input cross-check

The tap range is `0xFF61F6..0xFF61F7`. `rastan_direct_update_inputs` writes `0xFF61F6` once and `0xFF61F7` once per completed canonical call; these are two different shadow bytes, not two stores to one address. `_vblank_service` calls the helper exactly once before mode/scene gates.

The script prints `floor(input_writes/2 + 0.5)` and an evenness flag. For an odd count, it still prints a rounded count rather than `N/A / split invocation`; that is unsafe presentation. Capture start/stop between the two stores or between the input helper and worker entry can produce a boundary mismatch.

The cross-check is usefully independent in mechanism (RAM write taps versus ROM read tap) but shares control-flow and capture-window assumptions. It is not independent of “every serviced canonical handler reaches both sites normally.”

## 3. Producer separation

`producer_completions` is incremented only by the `pc090oj_emitted_count` write tap. The repaired names and explanatory text no longer call it IRQ6, gameplay-tick entry, worker end, or RTE.

However, reporting still uses lifetime-global producer totals in gameplay ratios and associates publication spans with producer writes. The semantic label is repaired; the interval accounting is not.

## 4. Worker exit and exact non-invasive alternative

The `0x3A27E` address contains `RTE`. Andy's read-tap experiment reports about two callbacks per actual execution, consistent with prefetch pollution. It is not a usable read-tap delimiter.

Andy missed a mechanism already proven in this repository and present in the current MAME environment: debugger execution breakpoints. Existing scripts use `cpu.debug:bpset(address,"1",action)` with action expressions containing `totalcycles()`, beam coordinates/HV reads, logging, and `g`. `build0356_frame_timing_joint.lua` already lists exact runtime breakpoint points `0x3A208`, `0x3A27A`, and `0x3A27E`. The runner must launch with `-debug -debugger none`; host-side debugger overhead does not add emulated 68000 cycles.

Recommended exact boundaries:

- worker entry breakpoint: `0x3A208`;
- worker end breakpoint: `0x3A27E` (immediately before executing RTE), or `0x3A27A` if the desired body endpoint excludes the final SR operation;
- log `totalcycles()`, frame, beam position/HV, and a monotonically paired event number; action ends with `g`.

This gives exact execution events without a ROM patch. Whole-worker elapsed 68000 cycles can be paired directly, including frame wrap.

### Diagnostic-ROM proposal review

The proposed instruction `move.w #imm,abs.l` is eight bytes and, on MC68000, costs **20 cycles**, not approximately 12. Two markers cost **40 cycles**, not 24. Each MOVE leaves registers and stack unchanged but updates N/Z and clears V/C according to the moved value; it therefore does affect CCR. At entry the next body operations soon overwrite condition codes, but that is still perturbation. Immediately before `ORI #0x0600,SR`, the changed CCR would persist until `RTE` restores stacked SR; no intervening branch is present. Absolute WRAM stores also add bus traffic.

Because exact debugger breakpoints exist, no diagnostic ROM should precede the trace. If debugger execution events proved unusable, two markers would be necessary (entry read tap is not exact enough), and the accurate stated perturbation would be 40 cycles plus code-placement/reflow effects. Timing source: Motorola/NXP MC68000 User's Manual, MOVE byte/word execution table.

## 5. Semantic VDP gate

The claimed allowed ranges contain:

### `[0x7007E,0x70418)`

- generic `vdp_set_reg` and `vdp_set_vram_write_addr` helpers;
- `sprite_dma_addr_high_bits_fix`;
- `_vblank_service`;
- tile, Plane-B, obsolete/general Plane-A and scroll commit functions;
- `vdp_install_test_lines` (scene-entry palette writer, not a `dma_publish_frame` child);
- `dma_publish_frame`, DMA primitives, and palette commit.

This range is not the exact publication tree. A non-publication caller writing through either generic VDP helper is allowed, as is `vdp_install_test_lines`; these are false-negative paths. Canonical diagnostic VDP writes in `_vblank_service` would also be allowed by location.

### `[0x72898,0x72998)`

Contains Plane-A column and narrow-strip commit code. This is legitimate publication code.

### `[0x745EA,0x7470E)`

Contains sprite pattern/SAT commit code. This is legitimate publication code.

No currently called publication function is visibly omitted, but the broad first range invalidates the “only publication owner” guarantee. Prefer dynamic publication context rather than generic helper addresses. Existing `vblank_vc` at `0xFF61E4` is written at the seven `VC_MARK` boundaries, and debugger breakpoints at `dma_publish_frame` entry/return are already established. Either can delimit the actual publication interval; VDP writes are allowed only while that interval is active, optionally combined with exact writer membership.

Gate verdict: **NOT YET VALID**.

## 6. Gameplay arming

`load_scene_tiles` preserves logical IDs 0, 1, and 2; every tileset/residency ID 3 through 8 is collapsed to logical `genesistan_current_scene_id = 1`. Therefore:

- `1` covers normal in-level gameplay, outdoor, cave residencies, normal transitions, and the boss while still in the gameplay scene;
- `0` is title/frontend;
- `2` is end-round/frontend;
- logical scene `3` is not produced by the current loader; it is a tileset ID before normalization.

The arming set `{1,3}` is functionally equivalent to `{1}` today. Its “3=cave gameplay” comment is wrong. ROUND/READY after gameplay scene activation is also scene 1, so the gate can arm there. End-round scene 2 is intentionally excluded, but the report must state that limitation.

The 180-frame warmup is based on total display frames since script start, not 180 gameplay frames. It usually expires during title/attract and therefore does not provide a gameplay-settle window. That is acceptable only if described; it does not justify “steady gameplay.”

## 7. VDP write width and decoder

Current canonical publication code uses word data/control writes and long control commands. The decoder can handle a long command delivered as one callback or two ordered 16-bit callbacks, and its CD/address formulas match the VDP implementation.

It ignores the callback `mask`. Consequently an 8-bit write cannot be decoded reliably: byte lane and replicated/partial data semantics are not reconstructed. Such control writes must become `UNKNOWN`, not be interpreted as a complete word. Register commands clear the latch, which is correct for full 16-bit register writes, but an unrelated/data/control interruption or masked byte access can leave association ambiguous. The retained validation exercises ordinary publication word/long forms; it does not prove all 8-bit/mask cases. The existing `UNKNOWN=1` confirms at least one undecoded command occurred but is not attributed.

## 8. VRAM targets

Build-0400 layout is:

- Plane B: `0xC000–0xDFFF`;
- Plane A: `0xE000–0xEFFF`;
- SAT: `0xF800–0xFBFF`;
- HScroll: starts at `0xFC00` and occupies the remaining `0xFC00–0xFFFF` address class here;
- all other VRAM destinations: `tiles`, combining generic and sprite pattern destinations;
- CD low `3`: CRAM;
- CD low `5`: VSRAM.

The ranges do not overlap. The classifications are reliable only after a complete valid address command is decoded; every ambiguous or unsupported width/latch condition must increment UNKNOWN.

## 9. Publication outer span

The current span starts on the first VDP write of any kind after the prior producer completion and ends on the last such write before the next producer completion. It does **not** directly start at `dma_publish_frame` or end at its return.

Contamination paths include:

- post-publication worker VDP traffic;
- scene/init/frontend VDP traffic;
- fallback emission by `vdp_prepare_sprites` before publication;
- a frame without the expected producer completion;
- traffic after one producer marker becoming the next record's start;
- capture start/stop mid-record.

The semantic gate does not repair this association, because the span accumulator includes allowed and offending writes alike and operates even while unarmed. Frame association is therefore **NO, not generally valid**. It may approximate publication in stable frames with exactly one later emit and no other VDP traffic, but must be labeled conditional.

Use exact publication entry/exit debugger events, or the existing `VC_MARK0..6` stores, to bracket the outer span and subphase boundaries.

## 10. Ratios and zero denominators

`armed_frames` counts only gameplay scene frames after global frame 180. `serviced_irq6`, `producer_completions`, input writes, target commands, and buckets are lifetime-global. Dividing global numerators by `armed_frames` is invalid. Per-armed-interval counters or baseline subtraction on arm/disarm transitions are required.

When `armed_frames == 0`, the two display-frame ratios print `0.0000`; when `serviced_irq6 == 0`, the producer/service ratio does the same. Those values look measured. They must print `N/A / NOT EXERCISED`. Odd `input_writes` must also print an incomplete boundary rather than a rounded handler count. Target-command percentages with zero total likewise require N/A.

## 11. Timeline review

### Current model

The broad order is correct: input snapshot, sprite-ready guard, publication, tail-JMP worker, IPL7/gameplay/common/state/post-common, RTE, mainline spin. Beam V convention is also correct for this NTSC 224-line mode: V224–261 is VBlank and V0–223 is active display. Therefore beam V26 occurs after the 261→0 wrap, about 26 active-display scanlines after VBlank—not before it.

Corrections:

- “Sprite-ready guard — normally no-op” must mention its fallback emit when `sat_frame_ready` is clear.
- `0x3A208` raises IPL7; the watchdog/IO instructions at `0x3A20C..0x3A217` are what Genesis NOPs. The combined label currently implies the raise is NOP'd.
- Individual publication calls are statically ordered `[S]`; command totals are `[P]` counts, not measured phase positions/durations.
- Input-helper execution is `[S]` plus a write-count cross-check `[P]`; the current serviced count comes from the later worker-entry read tap, not the input block itself.
- Worker-entry V26 is a measured read-tap event `[P]`, not exact `[M]`, until replaced by an execution breakpoint.
- Publication width/position must remain schematic until exact publication brackets exist.

Descriptive call-tree labels otherwise match recovered semantics. “Pre-gameplay update” should be “conditional pre-gameplay update,” and “warm-restart/watchdog gate” should avoid implying the removed hardware watchdog write occurs there.

### Target model

The structural split is sound as design: bounded commit-only IRQ6 plus preemptible mainline gameplay/producer work with WORK→READY handoff.

“Short IRQ6 ends in VBlank” is an unsupported timing guarantee. Publication includes potentially expensive Plane-B/transition work, and no controlled gameplay measurement proves all legitimate commits finish before active display. Replace it with:

> bounded commit-only IRQ6; desired/typical goal is to finish during VBlank, but worst-case publication timing remains to be measured.

## 12. Future sprite READY transaction

Andy's repaired design now incorporates the five requested ownership requirements in substance. One clarification remains: the atomic generation must explicitly own the control metadata as well as payloads—READY generation number, READY SAT-bank identity, READY worklist/count, `pc090oj_sat_frame_ready`/dirty state or their replacements, cancellation state, and reservation cleanup list. The publisher's resident-table updates and reservation clears must complete before the next WORK allocator begins. With that explicit metadata ownership, the design contract is complete; list/count double buffering alone remains insufficient.

## 13. What a corrected run can and cannot prove

### Fit after trace-only repair

- Exact serviced-worker entry and pre-RTE execution counts via debugger breakpoints.
- Exact worker elapsed emulated CPU cycles and beam positions.
- Physical display cadence versus serviced handlers over the same armed interval.
- Producer completions separately over that same interval.
- Exact publication outer/subphase boundaries via debugger events or `VC_MARK` stores.
- Publication-only command distribution.
- Contextual VDP ownership gate.
- LIGHT/MEDIUM/HEAVY load correlation.

### Cannot prove even then without additional hardware-source observation

- Exact physical VDP VINT assertion/acknowledgment history; serviced deficit is only consistent with the one-pending model.
- Real-hardware timing beyond MAME's emulated cycle/VDP model.

## Required next action

Choose **B: make small trace-only corrections, then recheck**.

Required corrections:

1. launch MAME with the established debugger/no-GUI configuration and use exact execution breakpoints at worker entry and pre-RTE;
2. count every ratio numerator and denominator over the same scene-1 armed interval, resetting/baselining on entry and excluding partial first/last handlers;
3. print `N/A` for zero denominators, odd input cross-checks, and unexercised gates;
4. bracket publication with `dma_publish_frame` entry/return or existing VC marker events;
5. count publication targets only inside that bracket;
6. gate VDP access by publication context, not broad helper ranges;
7. honor `mask` or classify masked/byte command writes UNKNOWN;
8. update the timeline evidence tags and change the target claim to “bounded commit-only IRQ6; VBlank completion is a goal, not a guarantee.”

Do not ask Tighe to perform the controlled run yet, and do not build a diagnostic ROM.

Production gameplay source changed: **NO**. ROM produced: **NO**. Counter remains **400**.
