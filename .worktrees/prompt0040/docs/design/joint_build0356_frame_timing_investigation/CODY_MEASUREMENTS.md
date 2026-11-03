# CODY_MEASUREMENTS - Build 0356 Frame-Timing Investigation

Status: **FIRST-PASS MEASUREMENT COMPLETE; READY FOR ANDY REVIEW**

This is Cody's measurement package. It does not modify production code, recommend an
architecture change, or claim joint consensus. `FINAL_CONSENSUS.md` remains pending.

## 1. Baseline and scope

- ROM: `dist/rastan-direct/rastan_direct_video_test_build_0356.bin`
- SHA-256: `94afa3811b675e43a8e77b12e84b815cca4096617ffc3dd0be0951427fb8b760`
- Size: 1,666,744 bytes
- Counter: 356
- Target machine: Genesis NTSC in MAME
- Production source changed by this audit: **NO**
- ROM produced by this audit: **NO**

The completed 1,800-frame capture was reused. Two already-completed 900-frame
supplemental captures provide hierarchical translated/native timing. No emulator capture
was repeated after the context reset.

## 2. Evidence and tools

Read-only tools retained:

- `tools/mame/scripts/build0356_frame_timing_joint.lua`
- `tools/mame/scripts/reduce_build0356_frame_timing_joint.py`
- Existing publication reducer `tools/mame/scripts/reduce_build0354_vblank_audit.py`,
  rerun against the preserved Build 0356 publication stream to verify representative
  selection; its vertical representative is frame 1064 with 6,423 Plane A dots.

Authoritative captures:

- `states/traces/build0356_joint_frame_timing_20260914/`
  - 1,800 external frames; complete IRQ lifecycle and coarse continuation boundaries.
- `states/traces/build0356_joint_hierarchy_20260914/`
  - 900 external frames; translated continuation and gameplay-core subdivisions.
- `states/traces/build0356_joint_native_sprite_counts_20260914/`
  - 900 external frames; final-ROM native sprite staging/finalizer sections and queue counts.
- `states/traces/build0356_vblank_physical_beam_20260912/`
  - publication-only section timing and Build 0354/0355/0356 comparison.

Two intermediate supplemental directories are retained but superseded:

- `states/traces/build0356_joint_native_sprite_hierarchy_20260914/` used stale
  prepatch native addresses and is invalid for native-section attribution.
- `states/traces/build0356_joint_native_sprite_hierarchy_corrected_20260914/` has
  valid timing points but queue-count capture failed and reported zero counts.

The final `build0356_joint_native_sprite_counts_20260914` capture is authoritative for
native sprite counts. The reducer was rerun only against preserved evidence and passes
`python3 -m py_compile`.

The exact authoritative 1,800-frame invocation recorded in `capture_metadata.txt` was:

```bash
DUMP_OUT=/home/tighe/projects/rastan-genesis/states/traces/build0356_joint_frame_timing_20260914/frame_timing_events.csv \
TRACE_FRAMES=1800 mame genesis \
  -cart dist/rastan-direct/rastan_direct_video_test_build_0356.bin \
  -video none -nothrottle -sound none -skip_gameinfo \
  -debug -debugger none \
  -autoboot_script tools/mame/scripts/build0356_frame_timing_joint.lua
```

The two 900-frame supplements reused the same read-only Lua harness with additional
event selections and the same reducer. No ROM instrumentation was added.

## 3. Physical-time method

### 3.1 Why the old 8-bit V-counter arithmetic is invalid

`VC_MARK` stores only the Genesis hardware V-counter byte. That byte is not a monotonic
262-line frame counter: it has only 256 values and the NTSC counter sequence has a
hardware-specific discontinuity. Taking differences modulo 262 invents information the
byte never recorded. It cannot distinguish counter wrap from a new frame epoch, and it
cannot measure a routine spanning one or more complete external frames. The earlier
approximately 258-scanline reconstruction is therefore not physical elapsed time.

### 3.2 Authoritative beam accounting

MAME supplies an external screen-frame callback plus physical `beam_y` and `beam_x`.
The reducer converts each observation into an unwrapped physical stamp:

```text
stamp = external_frame * (262 * 488)
      + ((beam_y - 224) mod 262) * 488
      + beam_x
```

Constants reported by the target are 262 lines/frame, 224 visible lines, 38 VBlank
lines, 488 beam dots/line, 59.922743404312 Hz refresh, and 7,670,453 Hz CPU clock.
The Genesis H/V counter identified VINT at hardware V-counter `0xE0`, observed at MAME
screen `beam_y=186`. The H/V counter is used to identify the VINT phase; the external
frame plus physical beam position provides the monotonic epoch and elapsed time.

MAME did not expose a separate, directly tappable VDP IRQ-assert edge through this
harness. One physical VBlank opportunity is inferred per external screen frame from the
calibrated beam phase. The level-6 vector target and `_vblank_service` entry are the same
runtime PC, so vector-entry and service-entry timestamps are one measured event here.

## 4. Address-map and control-flow proof

All copied-code correlations below come from
`build/rastan-direct/address_map.json`; no fixed subtraction was assumed.

| Event | runtime_genesis_pc | arcade_pc | Classification |
|---|---:|---:|---|
| `_vblank_service`, level-6 vector target | `0x0700C2` | N/A | native Genesis code |
| `dma_publish_frame` entry | `0x070250` | N/A | native Genesis code |
| `dma_publish_frame` RTS | `0x0702D2` | N/A | native Genesis code |
| copied arcade IRQ/tick entry | `0x03A208` | `0x03A008` | copied arcade code |
| copied state dispatch | `0x03A252` | `0x03A052` | copied arcade code |
| state-dispatch return | `0x03A274` | `0x03A074` | copied arcade code |
| pre-RTE `ori.w #$0600,sr` | `0x03A27A` | `0x03A07A` | patched SR discipline |
| final RTE | `0x03A27E` | `0x03A07E` | copied arcade code |
| gameplay-core entry | `0x04210E` | `0x041F0E` | copied arcade code |
| early update/finalize entry | `0x042130` | `0x041F30` | copied arcade code |

`_vblank_service` publishes and then tail-jumps to `runtime_genesis_pc 0x03A208`.
There is no native RTE between those events. The copied handler starts with
`ori.w #$0F00,sr` (IPM 7), later establishes IPM 6 before the final RTE, and the RTE
restores the interrupted SR from the exception frame. Consequently, all copied arcade
work through `0x03A27E` remains in the same level-6 interrupt lifecycle.

## 5. Full 1,800-frame results

### 5.1 Count table

| Counted event | Count |
|---|---:|
| External Genesis frames | 1,800 |
| Physical VBlank opportunities | 1,800 |
| IRQ6 / `_vblank_service` entries | 1,257 |
| `dma_publish_frame` calls and returns | 1,257 |
| Copied arcade IRQ/tick entries at `0x03A208` | 1,257 |
| Copied handler final RTEs | 1,256 |
| External frames with no new service entry | 543 |
| Complete gameplay-state chains (`[2,3,0]`) | 1,008 |

The one entry/RTE difference is the chain still open when capture ended. The overall
service-entry ratio is `1257/1800 = 69.833%`, equivalent to approximately `41.84`
service entries/second at 59.9227 external frames/second. This is an IRQ/service rate,
not by itself a gameplay-advance rate.

### 5.2 Authoritative gameplay advance

The state dispatch at `runtime_genesis_pc 0x03A252` selects the gameplay path in state
`[2,3,0]`; that path enters `runtime_genesis_pc 0x04210E` / `arcade_pc 0x041F0E` once.
The full trace contains 1,008 complete gameplay-state dispatches. The supplemental
hierarchy directly observes 383 `0x04210E` entries for its 383 complete gameplay chains,
confirming the one-to-one relation. Therefore the full capture contains 1,008 proven
gameplay advances, while also containing startup/frontend frames. The whole-capture
external-frame:gameplay-advance ratio is `1800:1008` (`1.786:1`); it must not be read as
a steady gameplay frequency because the denominator includes non-gameplay time.

### 5.3 Case classification

All complete chains:

| Case | Count | Meaning |
|---|---:|---|
| A - service and publisher in VBlank | 256 | prompt service/publication |
| B - prepublication delay | 244 | mostly frontend/transition; service and publisher phases differ |
| C - masked continuation | 755 | prior handler crossed the relevant VBlank; service followed its RTE |
| E - active, unattributed startup | 1 | startup-only residual |

Gameplay chains only:

| Case | Count | Share |
|---|---:|---:|
| A - prompt | 256 | 25.40% |
| B - prepublication delay | 3 | 0.30% |
| C - masked continuation | 749 | 74.31% |

Thus IRQ6 service entry itself, not merely publisher entry, occurs during active display
on 749 of 1,008 complete gameplay chains. Publisher entry is also in active display on
749 gameplay chains, but those totals need not identify the exact same individual cases.
The earlier publication-only measurement (`870/1009 = 86.22%`) used a different capture
and timestamped `dma_publish_frame` entry, not IRQ assertion or IRQ6 service entry.

### 5.4 RTE relationship and SR/IPM evidence

For the 749 complete gameplay Case-C chains:

- Service entry is 18,563 to 127,640 dots after the associated physical VBlank phase
  (median 69,241 dots, or 141.89 lines).
- The prior copied handler's RTE occurs after that VBlank boundary.
- Pending IRQ6 service follows the prior RTE in 67 to 84 dots (median 73 dots,
  0.150 scanline).
- Every captured stacked/interrupted gameplay SR has IPM 0.
- Live service-entry SR has IPM 6, as expected after level-6 exception acceptance.

This rules out an ordinary mainline that permanently leaves IPM >= 6. It dynamically
confirms H-CONT for the observed Case-C frames: the preceding level-6 continuation remains
active across the next VBlank, cannot be preempted by the same interrupt level, executes
RTE, restores IPM 0, and then accepts the pending IRQ within a short instruction window.

## 6. Complete-chain cost

Full-trace gameplay distributions, in physical beam dots:

| Region | Min | Median | P95 | Max | Median lines |
|---|---:|---:|---:|---:|---:|
| Native prepublication | 746 | 747 | 755 | 755 | 1.531 |
| `dma_publish_frame` | 3,017 | 3,028 | 21,444 | 30,800 | 6.205 |
| Copied arcade continuation | 79,384 | 157,457 | 284,227 | 407,245 | 322.658 |
| Full IRQ chain | 83,324 | 163,310 | 291,882 | 420,548 | 334.652 |
| Service period | 85,781 | 163,381 | 291,964 | 420,618 | 334.797 |

The median full chain is 1.277 Genesis frames long. The median publisher is only 1.85%
of the median full-chain duration; the copied continuation is the dominant interval.
This explains why removing the large Build 0354 sprite palette publication pass materially
improved the publisher but produced only a modest user-perceived whole-game improvement.

Worst complete gameplay chain:

- Entry external frame 1471, `beam_y=154`, `beam_x=371`, H/V counter `0xC029`.
- Interrupted PC `runtime_genesis_pc 0x03B292`; stacked SR `0x2009` (IPM 0).
- Live service SR `0x2609` (IPM 6).
- Service began 112,611 dots after the physical VBlank phase.
- Prior RTE was after that boundary; service followed it by 68 dots.
- Publisher: 12,383 dots (25.375 lines).
- Copied continuation: 407,245 dots (834.518 lines).
- Full chain: 420,548 dots (861.779 lines).

## 7. Publisher section measurements

These Build 0356 publication-only representatives use the corrected reducer selection;
the vertical representative is required to contain substantive Plane A work.

| Class | Frame | Total lines | Palette | Tiles | Plane B | Plane A | Sprites | Scroll | Worklist | Emitted |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Stationary | 595 | 6.201 | 0.084 | 0.084 | 0.092 | 1.422 | 2.035 | 0.930 | 0 | 28 |
| Horizontal | 746 | 6.201 | 0.084 | 0.084 | 0.092 | 1.422 | 2.035 | 0.914 | 0 | 46 |
| Vertical/jump | 1064 | 17.924 | 0.086 | 0.086 | 0.094 | 13.162 | 2.037 | 0.914 | 0 | 20 |
| Sprite-heavy | 1442 | 22.203 | 0.084 | 0.084 | 0.092 | 1.422 | 18.039 | 0.914 | 10 | 51 |
| Worst Build 0356 | 1475 | 63.115 | 0.084 | 0.084 | 37.836 | 1.420 | 21.207 | 0.914 | 12 | 49 |

Minor totals differ from the displayed rounded section sum because call/marker overhead is
retained in total timing. Pattern DMA is bounded to 12 worklist entries and is commonly
zero. Fixed 640-byte SAT DMA is approximately one scanline. The former per-emitted-entry
palette fixup/routing publication section is zero in Build 0356.

For historical separation, 134.033 lines is the worst observed complete **Build 0354**
publisher in the preserved comparison, where repeated linear `palette_route_lookup` work
dominated. It is not Build 0356's maximum. Build 0356's observed maximum is 63.115 lines.

The earlier Build 0354 independent capture remains useful frequency evidence but must not
be merged with the Build 0356 count table: its first 1,800-frame run contained 1,123
complete publications (875 gameplay), and its second 1,500-frame stationary run contained
997 complete publications, including 237 stationary gameplay publications. Those runs
independently prove that publication need not occur once per external frame and that the
old sprite-dominated cost was not dependent on continuous movement. Build 0356's direct
comparison capture instead contains 1,257 publications and 1,009 gameplay publications.

## 8. Hierarchical copied-continuation breakdown

The 900-frame hierarchy supplement contains 632 service entries, 631 complete chains,
and 383 complete gameplay chains. Its values differ somewhat from the full-trace medians
because it samples a shorter gameplay interval; it is used to localize, not replace, the
full 1,800-frame distributions.

The continuation has two sequential large regions, not one nested call tree:

1. During the copied IRQ prefix, `runtime_genesis_pc 0x042130` /
   `arcade_pc 0x041F30` performs the early update/finalize path.
2. Later, state dispatch invokes `runtime_genesis_pc 0x04210E` /
   `arcade_pc 0x041F0E`, the gameplay core.

### 8.1 Early update/finalize region

| Region | Median dots | Median lines | P95 dots | Max dots | Classification |
|---|---:|---:|---:|---:|---|
| Entire early update | 91,068 | 186.615 | 162,120 | 229,953 | mixed copied control + native producer |
| Small calls before sprite path individually | 55-154 | 0.113-0.316 | bounded | 547 | copied arcade semantics/support |
| Native frame-begin boundary | 211 | 0.432 | 219 | 219 | Genesis-native queue lifecycle |
| Native `0x041DAE` replacement path | 90,139 | 184.711 | 161,191 | 229,031 | Genesis-native sprite producer/finalizer |

The near equality of the early-update and native-`0x041DAE` durations localizes almost
all of this first large region to native sprite work. No large wait/poll interval appears
among the preceding calls.

### 8.2 Later gameplay-core region

| runtime_genesis_pc | arcade_pc | Median dots | Median lines | P95 dots | Max dots |
|---:|---:|---:|---:|---:|---:|
| `0x051210` | `0x05100A` | 22,033 | 45.150 | 172,019 | 172,086 |
| `0x040D66` | `0x040B66` | 11,213 | 22.977 | 20,195 | 23,489 |
| `0x0422E6` | `0x0420E6` | 9,505 | 19.477 | 9,992 | 11,602 |
| `0x0445E0` | `0x0443E0` | 2,256 | 4.623 | 2,296 | 2,335 |
| `0x044BB4` | `0x0449B4` | 5,842 | 11.971 | 8,310 | 9,401 |
| `0x0452D8` | `0x0450D8` | 144 | 0.295 | 152 | 152 |
| `0x04A1A6` | `0x049FA6` | 1,197 | 2.453 | 1,205 | 4,164 |

The whole state-dispatch region has a 52,944-dot/108.492-line median in the hierarchy
capture. These are copied arcade gameplay/object/collision/control routines and require
semantic review before any architectural interpretation. The trace proves their cost and
ordering; it does not prove that any one is redundant or safe to change.

## 9. Native sprite-finalizer breakdown

The authoritative native-count supplement measures 383 gameplay invocations:

| Native section | Median dots | Median lines | P95 | Max | Typical queue count |
|---|---:|---:|---:|---:|---:|
| Stage dispatch | 21,623 | 44.309 | 40,255 | 48,718 | N/A |
| Finalizer total | 67,300 | 137.910 | 118,438 | 189,588 | 28 emitted median |
| Route overhead | 33 | 0.068 | 41 | 42 | N/A |
| Setup | 5,697 | 11.674 | 5,706 | 5,706 | N/A |
| HUD lane | 6,112 | 12.525 | 6,113 | 6,113 | 9 |
| Front-effect lane | 75 | 0.154 | 2,624 | 7,835 | median 0, max 2 |
| Player-front lane | 75 | 0.154 | 83 | 83 | 0 |
| Middle lane | 75 | 0.154 | 83 | 83 | 0 |
| Player-body lane | 12,778 | 26.184 | 24,680 | 42,171 | median 9 |
| Back/enemy lane | 42,082 | 86.234 | 87,617 | 149,350 | median 16, max 46 |
| Game-over lane | 167 | 0.342 | 175 | 176 | state-dependent |
| Bookkeeping | 207 | 0.424 | 215 | 215 | N/A |

Final emitted SAT count ranges from 3 to 53 (median 28, P95 48). Pearson correlation
between emitted count and finalizer duration is `0.8999546642`. Clean resident groups show
the scaling directly:

| Emitted | Samples | Median finalizer dots | Median lines |
|---:|---:|---:|---:|
| 12 | 64 | 25,301 | 51.846 |
| 20 | 49 | 39,313 | 80.559 |
| 28 | 81 | 53,315 | 109.252 |
| 36 | 65 | 67,308 | 137.926 |

That is approximately 1,751 dots (3.59 lines) per additional emitted entry across these
groups. At higher counts, pattern-residency misses and the bounded worklist add variance.

Final-ROM disassembly shows why this is action work rather than the removed palette pass:

- `.Lnq_emit_lane` begins at native `0x073B66`; `.Lnq_emit_entry` at `0x073B8A`.
- Each entry linearly searches 49 resident slots beginning at `0x073C80`.
- A miss searches free cells and may append to the 12-entry worklist (`0x073C94` onward;
  limit check at `0x073CBA`).
- SAT output starts at `0x073D22`.
- Palette selection at `0x073D5C` uses `current_sprite_palette_map` indexed lookup,
  not the retired linear `palette_route_lookup` postpass.
- Emitted count is finalized around `0x073DB4..0x073DCE`; final RTS is `0x073DE8`.

The measured current hotspot is therefore the per-emitted-entry builder/residency/worklist
path, especially the back/enemy lane. This is hotspot identification only, not an
optimization recommendation.

### 9.1 Measured hotspot ranking for architecture review

Percentages below divide each same-capture median by the 151,521-dot median full chain
in the 900-frame hierarchy/native supplement. Medians are not algebraically additive,
so the percentages are prioritization indicators rather than a partition of 100%.

| Rank | Target | Median cost | Observed frequency | Median-chain share | Class | Architectural classification | Review boundary / possible direction | Semantic risk | Expected end-to-end opportunity |
|---:|---|---:|---:|---:|---|---|---|---|---|
| 1 | Native sprite finalizer | 67,300 dots / 137.910 lines | 383/383 gameplay chains | 44.42% | STEADY / FREQUENT | Genesis-native producer work; per-entry residency/worklist/SAT construction | Preserve lane ordering and SAT semantics; determine whether the 49-slot per-entry search can become an indexed or offline-derived lookup | High | Large if the per-entry search is proven replaceable; cost scales strongly with emitted count |
| 2 | Copied gameplay core `runtime_genesis_pc 0x051210` / `arcade_pc 0x05100A` | 22,033 dots / 45.150 lines; P95 172,019 | 383/383 gameplay chains | 14.54% median, much larger conditionally | CONDITIONAL / GAMEPLAY | Original copied arcade gameplay/object/collision semantics, exact sub-purpose not resolved here | Semantic decomposition only; no change is supportable until arcade intent and expensive branch are identified | Very high | Potentially large on spike frames, unknown safely recoverable share |
| 3 | Native sprite stage dispatch | 21,623 dots / 44.309 lines | 383/383 gameplay chains | 14.27% | STEADY / FREQUENT | Genesis-native semantic-to-queue production | Preserve semantic cut; profile only the largest producer family before considering data-layout/offline work | High | Material if repeated scans or recomputation are proven; not yet quantified |
| 4 | Copied core `0x040D66` / `0x040B66` | 11,213 dots / 22.977 lines | 383/383 gameplay chains | 7.40% | STEADY / FREQUENT | Copied arcade semantics, unresolved sub-purpose | Ghidra semantic classification first; no implementation recommendation | Very high | Moderate at most until semantics and avoidable share are known |
| 5 | Copied core `0x0422E6` / `0x0420E6` | 9,505 dots / 19.477 lines | 383/383 gameplay chains | 6.27% | STEADY / FREQUENT | Copied arcade semantics, unresolved sub-purpose | Ghidra semantic classification first; no implementation recommendation | Very high | Moderate at most until semantics and avoidable share are known |

The 37.836-line Plane B publisher event is **TRANSITION / EXCEPTIONAL**, not a top
steady-state target. Publication palette and tile sections are about 0.084 line each,
scroll is about 0.914 line, and fixed SAT DMA is about one line; none ranks above the
per-frame producer/finalizer work. These are candidate boundaries for Andy to review,
not authorized optimizations.

## 10. Useful work, waits, and scaffolding

Within the measured IRQ continuation, the large intervals are executable copied gameplay
and native sprite staging/finalization work. Static searches of the measured chain found
no VDP-control-port status read or chip-ready polling loop. The interrupted-PC histogram
does show the short copied mainline synchronization loop around `0x03A1A8` and
`0x03B27E..0x03B296`; for late Case-C service, only 67-84 dots execute after the prior
RTE before IRQ6 is accepted. It is not the source of the hundreds-of-lines continuation.

The numbered Build 0356 ROM still contains `VC_MARK`/`vblank_vc` diagnostic
instrumentation. Its measured publication overhead has a median of approximately 379 dots
(0.777 line), with observed values 371-404 dots. This is diagnostic scaffolding, not a
standalone-build justification; no removal is performed here.

For the measured late chains, there is no substantial idle/mainline interval between the
old chain and the newly pending service: after copied-handler RTE, only 67-84 dots elapse
before IRQ6 entry. The large serialized intervals are native prepublication, publication,
and the copied continuation itself; RTE-to-next-service mainline execution is tiny.

## 11. VDP VINT-enable evidence

The trace observed three VDP register-1 writes: `0x8134` twice and `0x8174` once. All have
bit 5 set, so every observed write keeps VINT enabled; no normal-gameplay VINT-disable write
was captured. This supports masked continuation rather than VDP register-1 clobber for the
observed late services. It is an observation over this trace plus the known static write
inventory, not a claim that no uninstrumented future path can ever write register 1.

## 12. Proven facts, inference, and unsupported cases

### Proven

- The old 8-bit `VC_MARK` modulo-262 duration was invalid.
- The physical-beam method measures complete multi-frame elapsed time.
- IRQ6 service itself is late on 749/1,008 complete gameplay chains.
- The preceding level-6 continuation crosses the physical VBlank and its RTE precedes
  pending IRQ acceptance by only 67-84 dots.
- Stacked gameplay IPM is 0; live handler IPM is 6.
- Median complete chain is 334.652 lines; publisher median is 6.205 lines; copied
  continuation median is 322.658 lines.
- The first dominant continuation region is native sprite staging/finalization.
- Finalizer cost strongly tracks emitted SAT count; the back/enemy lane is the largest
  measured native lane.
- Pattern DMA is bounded to 12 and commonly zero; fixed SAT DMA is about one line.
- No observed register-1 write disables VINT.

### Inference, explicitly bounded

- Build 0356 feels only modestly faster because publication was reduced while the much
  larger serialized continuation remains. This directly fits the measured cost split,
  but perceived speed remains a user-level observation.
- The dominant current sprite cost is per-entry residency/worklist/SAT construction. The
  correlation and disassembly support this, but the harness does not time each individual
  instruction in `.Lnq_emit_entry`.

### Unsupported by these captures

- No cave/drop-specific timing conclusion.
- No claim that any copied gameplay-core routine is redundant.
- No claim that the measured mainline synchronization loop is safe to remove.
- No D00462 provenance or fix; that remains a separate issue.
- No claim that Build 0356 solved overall game speed.

## 13. Plain-English Answer For Tighe

The physical VBlank boundary is not "late"; it occurs once per external video frame. The
harness cannot directly timestamp the VDP's internal assertion edge, but VINT remains
enabled in every observed register-1 write. What is late is **IRQ6 service entry** on 749
of 1,008 gameplay chains. The previous Level-6 handler is still running when the next
VBlank arrives, so the same interrupt level cannot preempt it. As soon as that old handler
executes RTE, the pending IRQ is accepted 67-84 dots later.

The publisher then begins after only about 1.5 lines of native prepublication work. It is
therefore often in active display because service was already late, not because the current
publisher normally consumed a frame before its own entry. Build 0356 reduced median
publication to 6.205 lines, but the copied continuation still has a 322.658-line median.
Within that continuation, the largest measured native component is sprite staging and
finalization; later copied gameplay-core work is also substantial and sometimes spikes.
That is why removing the old palette publication pass produced a real local improvement
but only a modest whole-game speed improvement.

## 14. Audit Conclusion

H-CONT is dynamically confirmed for the observed late gameplay chains. The original
statement that publication itself took approximately 258 scanlines is **falsified**; it
was produced by invalid 8-bit V-counter reconstruction. A different and more consequential
fact is proven: the complete level-6 service plus copied arcade continuation commonly
exceeds one 262-line frame, with a 334.652-line median and a 420,548-dot maximum in the
1,800-frame gameplay sample. The publisher is now usually small. The remaining measured
hotspots are native sprite staging/finalization and the later copied gameplay-core regions.

This package is ready for Andy's methodology and architecture review. No optimization or
production change is authorized by this report alone.
