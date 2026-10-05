# Build 0400 Timing-Instrument Repair + Cody Re-Review Package

Status: INSTRUMENT REPAIR (trace-only). No production source change. No ROM. Counter 400.
Author: Andy. Incorporates `Cody_build0400_preimplementation_independent_verification.md`.
File changed: `tools/mame/scripts/frame_timing_trace.lua` (read-only MAME Lua). New deliverable:
`build/mame/home/frame_timing/frame_execution_timeline.md`.

## Cody corrections incorporated
1. `irq6_total` renamed to **`producer_completions`** (it counts `pc090oj_emitted_count` writes).
2. producer-finalizer completion is kept **separate** from worker completion.
3. Added a **direct serviced-IRQ6 marker** (worker entry) rather than inferring it from the producer.
4. `display_frames` is labeled a display-frame cadence proxy, **not** a VINT tap.
5. `publication_outer_span` is labeled a **coarse outer beam span**, not DMA duration.
6. VDP target counters labeled **command counts**, not bytes/cycles/duration.
7. VDP gate replaced with **exact publication-routine membership**, **armed only in gameplay**.
8. **HScroll split** from the generic `tiles` class (VRAM 0xFC00).

## Metric definitions (event actually observed)
| metric | tap/event | class | limits |
|---|---|---|---|
| `display_frames` | `emu.register_frame_done` | display cadence | not a VINT assertion count |
| `serviced_irq6` | **read-tap opcode fetch of 0x3A208** (worker entry, a JMP target ⇒ prefetch-clean single fetch) | EXACT | needs gameplay arming; cross-checked by `input_writes/2` |
| `input_writes/2` | write-tap 0xFF61F6 (update_inputs writes it 2×/IRQ6) | EXACT proxy | must be even; exclude capture-split/boot |
| `producer_completions` | write-tap 0xFFBED4 (`pc090oj_emitted_count`) | EXACT finalizer | NOT IRQ6 entry / tick entry / worker end |
| `worker_entry_beamV` | beam V at the 0x3A208 fetch | EXACT | worker START only |
| `producer_done_beamV` | beam V at the emit write | PROXY | not worker end |
| `publication_outer_span` | first..last VDP-port-write beam V per tick | PROXY | includes gaps; scanline res; not transfer time |
| `publication_target_cmds` | decoded CD/address commands per target | COUNT | not bytes/cycles/duration |
| **worker_exit / RTE** | — | **UNOBSERVED** | prefetch double-counts 0x3A27E; no final-write marker |

Self-validation (headless attract): `serviced_irq6` 832 vs `input_writes/2` 833 (agree);
`producer_completions/serviced_irq6` = 1.001 (one emit per serviced IRQ6 in this state);
gate correctly **did not arm** in attract (scene≠1); arm-always test flagged `native_frontend_hud_emit`
writing VDP directly (proves FAIL path + symbol naming); HScroll split populated (832, separate from
tiles). No metric asserts a duration it cannot measure.

## Phase 4/5 — worker-end observation
**Non-invasive EXACT worker ENTRY: YES** (0x3A208 opcode-fetch read-tap; prefetch-clean JMP target;
count matches `input_writes/2`). **Worker EXIT/RTE: NO** — the 0x3A27E opcode fetch double-counts from
68000 prefetch (measured 2× the entry rate), and no guaranteed memory write brackets the RTE. MAME here
has no `cpu:add_exec`; `cpu.debug` breakpoints exist only under `-debug` and HALT (no Lua hit-callback),
so they cannot time the RTE non-invasively.

**Smallest diagnostic alternative (NOT built, PROPOSAL):** a diagnostics-only ROM that writes a sentinel
to otherwise-unused diag RAM at worker entry and immediately before the RTE (two `move.w #imm,abs`
stores, ~24 cycles total, no VDP/gameplay effect), tapped by this trace. **This requires a ROM =
Build 0401 (diagnostic).** If authorized, the sprite-isolation test shifts to 0402. Do not build without
Tighe's explicit authorization. Until then the 16.67 ms-fit / whole-worker-duration question stays OPEN.

## VDP gate — definition
- Allowed writers (exact `dma_publish_frame` tree, from symbol.txt): `[0x7007E,0x70418)` (set_reg,
  set_vram_addr, commit_tiles/bg/scroll, dma_publish_frame, dma primitives, commit_palette),
  `[0x72898,0x72998)` (commit_fg_columns + commit_fg_narrow_strips), `[0x745EA,0x7470E)` (commit_sprites).
- Armed only when `genesistan_current_scene_id` (0xFFC554) == 1 or 3 (gameplay / cave gameplay), past a
  180-frame warmup, so boot/init/attract cannot poison it.
- Any VDP-port write from a PC outside the allowed set while armed = **UNEXPECTED**, reported with the
  owning routine name (binary-searched from symbol.txt), PC, example VDP address, and count.
- Width/mask: 32-bit control writes decode directly; split 16-bit words are latched; a register write
  (0x8000-0x9FFF) resets the latch; anything undecodable increments `UNKNOWN` (never guessed).

## Publication target decoder
CRAM (CD=011), VSRAM (CD=101), VRAM (CD=001) split by destination: Plane B 0xC000-0xDFFF, Plane A
0xE000-0xEFFF, SAT 0xF800-0xFBFF, **HScroll 0xFC00+**, else `tiles` (generic + sprite pattern, not
separable by address). Counts are command occurrences, not durations.

## Phase 15 — future READY sprite transaction (DESIGN, not implemented)
For later preemption, the READY sprite publication must atomically bind, as one generation:
- READY SAT bank (already double-buffered),
- READY tile-DMA worklist + count (currently single),
- the pattern source descriptors the worklist entries reference,
- residency/reservation ownership.

Ownership rules (Cody's prerequisites) the transaction must enforce:
1. publish only a complete READY generation, never a WORK list;
2. the publisher's post-DMA writes to `sprite_tile_resident_code` and clears of
   `worklist_entry_for_slot` must not race the WORK producer's allocator/reservation decisions — by
   ownership transfer or a proven generation/scheduling invariant;
3. READY SAT bank is paired atomically with its READY pattern worklist;
4. only READY-owned list/reservation metadata is cleared/reset;
5. no new WORK generation starts while an older READY transaction can still mutate shared allocator
   state.
Double-buffering list+count alone does NOT state rules 2/5. Build 0401 (isolation) must add them or a
proven invariant, not just a second buffer.

## Cody re-review package (Phase 17)
- **Files changed:** `tools/mame/scripts/frame_timing_trace.lua` only (read-only Lua); new
  `build/mame/home/frame_timing/frame_execution_timeline.md`.
- **Each metric → tap/event:** table above.
- **Limitations:** worker end unobserved; publication span/target = proxies/counts not durations;
  `display_frames` not a VINT tap; serviced_irq6 relies on 0x3A208 being a prefetch-clean JMP target
  (validated by agreement with input/2); VINT coalescing is only *consistent with* the single-pending
  model, not directly proven (assertion/ack not tapped).
- **Allowed-writer set:** the three symbol ranges above (exact dma_publish_frame tree).
- **Gate arming condition:** scene id 0xFFC554 ∈ {1,3}, past 180-frame warmup.
- **Worker entry/exit mechanism:** entry = 0x3A208 opcode-fetch read-tap (exact); exit = none
  (prefetch pollution; diagnostic-ROM proposal pending).
- **Timeline method:** descriptive-name ASCII timeline + call tree, evidence-tagged [M]/[P]/[S]/[U],
  boxes not to scale unless measured; current vs target; per-regime left blank pending gameplay.
- **Evidence status per visual block:** encoded inline in the timeline doc.

## Gate next step
NOT declared fit-for-Tighe by Andy. Next gate = **Cody independent re-audit** of this repaired trace.
Only after Cody approves does Tighe run LIGHT/MEDIUM/HEAVY.

---

# UPDATE 2 — debugger-exact rebuild (per Cody re-audit `Cody_build0400_repaired_trace_independent_reaudit.md`)

The trace was rebuilt to exact execution timing. Changes below supersede the read-tap approach above.

## Exact mechanism (this MAME has no install_execute_tap / cpu:total_cycles())
- Launch with **`-debug -debugger none`** (runner updated). MAME debugger breakpoints
  `cpu.debug:bpset(pc,"1",'printf "...",totalcycles,frame,w@C00008; g')` emit exact `totalcycles` with
  auto-continue (`g`); drained from `machine.debugger.consolelog` each frame. Adds ZERO emulated 68000
  instructions. This reuses the Build-0354/0356 repository mechanism (`build0356_frame_timing_joint.lua`).
- Breakpoints: **PUB_ENTRY 0x70250, PUB_RTS 0x702D2, WORKER_ENTRY 0x3A208, WORKER_PRE_RTE 0x3A27E.**
  Pairs per serviced handler → publication cycles (PE→PR), **worker cycles (WE→WR, EXACT — worker end is
  now observed)**, IRQ-total cycles (PE→WR), entry/exit beam V, and frame-wraps crossed.
- The old 0x3A208 **read tap is removed** (prefetch-polluted; was never exact).

## Publication bracket + VDP gate by CONTEXT (not PC range)
- `publication_active` is driven by a Lua write-tap on **`vblank_vc` 0xFF61E4..0xFF61EB** (VC_MARK n writes
  beam V to vblank_vc+n in `dma_publish_frame`): mark 0 ⇒ active, mark 6 ⇒ inactive. (install_write_tap
  requires the range end to have low bits set — 0xFF61EB, not 0xFF61EA.)
- VDP target commands are counted **only while publication_active**, and a VDP-port write while
  **not** publication_active (during armed gameplay) is a gate violation, logged with PC. This is
  Cody's "gate by publication context, not helper ranges." Mask handling: non-full-word control writes →
  `UNKNOWN` (never guessed). HScroll (0xFC00+) is a distinct target from pattern/tiles.
- Publication subphase boundary beam V comes from the VC_MARK 0..6 values `[P]`.

## Interval accounting (Cody items 2,3,10)
- Everything is scene-1-armed and **reset at the ARM transition**; nothing divides lifetime-global by
  gameplay frames. Zero denominators, odd input counts, and unexercised gates print **N/A** (never
  0.0000 or a rounded handler count). Last 24 chronological events are dumped for boundary inspection.
- Arming is **scene id == 1 only** (`genesistan_current_scene_id` 0xFFC554). Per Cody, the loader
  collapses tileset IDs 3–8 to logical 1, so there is **no logical scene 3** — the earlier `{1,3}` /
  "3 = cave gameplay" wording is wrong and removed. Scene 1 covers in-level/outdoor/cave/boss/normal
  transitions and post-gameplay ROUND/READY; scene 2 end-round is intentionally excluded (stated limit).

## Self-validation (attract + forced-arm)
Committed (scene-gated) attract run: armed=0, all stats **N/A**, GATE **N/A (not exercised)** — no
contamination. Forced-arm validation: 651 exact worker pairs; publication cycles med 3021 / max 49771;
worker cycles med 1384 / max 1.18M with up to 9 frame-wraps (attract worker, not gameplay);
publication targets SAT=VSRAM=HScroll=651 (one per handler, sane); UNKNOWN=0; producer-done V populated;
gate correctly flagged the attract **frontend** graphics PIO (0x746f8 sprite pattern, 0x700b4 tiles,
0x334 boot fill) as outside-publication — confirming detection. Real violations are determined by the
scene-1 gameplay run.

## Locked target frame-ownership semantics (from Tighe — DESIGN, recorded here and in the timeline)
- **Preserve Build-0400 sequential-tick / slowdown behavior.** Every tick that begins completes;
  sequence N→N+1→N+2 with NO tick skipping, NO simulation-frame dropping, NO catch-up burst. ~60 ticks/s
  normal; accept slowdown when workload exceeds CPU (optimization reduces cost later). This is PRESERVED
  existing behavior, not a new scheduling policy.
- **A missed display deadline does NOT skip a tick.** If Tick N is running at VBlank and WORK N is not
  READY, IRQ6 holds the previous complete frame, sets tick_pending, does only required VDP service, RTEs;
  Tick N resumes from its exact interrupted PC and finishes. Repeated displayed frame ≠ skipped tick.
- **tick_pending is saturating (0/1)** — "start one more sequential tick when the current finishes";
  never a backlog count, never a catch-up storm.
- **Incomplete WORK is never published** — IRQ6 publishes only a complete immutable READY generation;
  no new-sprites+old-PlaneA / half-palette / partial-SAT / half-consumed-dirty-queue mixtures.
- **VDP COMMIT is the core IRQ6 responsibility**, shown explicitly in the timeline (CRAM/tiles/PlaneB/
  PlaneA/sprite patterns/SAT/HScroll/VSRAM).
- **IRQ6 RTEs immediately after required VDP work** — does NOT wait for VBlank to end. Bounded
  commit-only IRQ6; finishing within VBlank is a GOAL, **not a guarantee** (worst-case commit unmeasured).
- **Target input sampling moves to mainline tick start** — IRQ6 must NOT overwrite the arcade input
  shadows while a preemptible tick runs; sample the controller and freeze the four shadow bytes right
  before beginning the mainline tick, so one tick observes one snapshot even across IRQ preemption. (Not
  implemented in this task.)
- Build-0400 **black-strobe fix is preserved** (ordinary fg_boundary_install keeps display on; scene-entry
  blanking under `genesistan_scene_present_pending` retained). Not reopened.

## Future ISR → normal-call worker cut (Part 20)
IRQ-only to remove/convert: IPL7 raise (0x3A208), IPL restore (0x3A27A), `rte`→`rts` (0x3A27E), and the
arcade watchdog/IO NOP region (0x3A20C). Game-semantic body (gate → gameplay → producers → common →
palette → state dispatch → post-common) is preserved. Target: `Genesis IRQ6 { VDP COMMIT; tick_pending;
RTE }` + `arcade_frame_worker { … ; RTS }`. The normal worker must NOT execute the watchdog kick, the
IRQ-only IPL wrapper, the RTE glue, or any NOP padding standing in for them.

## Semantic remapper (Part 16) — the system future removal/shortening MUST use
- Authoritative spec: **`specs/rastan_direct_remap.json`** (`opcode_replace` 231 byte-neutral entries;
  `shift_replacements` 76 variable-length entries; `verbatim_restores`; relocation/table policy).
- Python mappers: **`tools/translation/postpatch_startup_rom.py`** (orchestrates copy/rebase, shift
  replacements, byte-neutral replacements, relocation/table passes, manifests) and
  **`tools/translation/shift_table_patcher.py`** (validates + inserts variable-length replacements,
  accumulates shifts, repairs supported references). `patch_maincpu.py` also present.
- Reference classes repaired (per CLAUDE.md + shift_table_patcher): 68000 8/16-bit BRA/BSR/Bcc
  displacements; absolute-long operands for JSR/JMP/PEA/LEA/MOVEA.L; declared 16-bit jump/displacement
  tables; `absolute_long_pointer_tables`; whole-maincpu relocation passes.
- Shortening/deletion: the **`shift_replacements`** path is the canonical variable-length mechanism —
  a replacement shorter than the original shifts all later copied bytes and reflows references via the
  accumulated shift table. This is how obsolete code is removed/shortened WITHOUT NOP padding. (Whether a
  true zero-length deletion primitive exists vs. shortening-via-shift was not separately confirmed here;
  shortening-via-shift is the established, proven mechanism — NEEDS-FOLLOW-UP only if a literal
  zero-byte delete is required.)

## Project breakpoint facility (Part 17) — NOT confidently identified
A dedicated "replace one instruction with a jump to a project breakpoint handler" facility was NOT
confidently located (searches matched only comment-level "break" text and the GDB toolchain). Per the
STOP conditions this is reported as **NEEDS-FOLLOW-UP / not identified**, not guessed. It is not required
for this trace: MAME debugger breakpoints are non-invasive and working. Rule for future diagnostics: do
not invent ad-hoc diagnostic RAM stores if the established facility (once identified) or MAME debugger
breakpoints can do it.

## Address-reflow caution (Part 21)
`0x3A208 / 0x3A27A / 0x3A27E / 0x70250 / 0x702D2 / 0xFF61E4 / 0xFFBED4 / 0xFFC554` are **Build-0400
locations**, acceptable for this build's measurement but **must not become permanent magic addresses**.
Future builds must resolve equivalents from `apps/rastan-direct/out/symbol.txt`, the remap manifest, and
`build/rastan-direct/address_map.json` (arcade_pc ↔ runtime_genesis_pc), since reflow moves them.

## READY ownership (Parts 22, 23) — unchanged design requirement
- Plane A/B: isolate the small dirty-row/col descriptor queue **and its staged source cell words** plus a
  generation id — not full-plane buffers; preserve Sonic-style incremental Plane A. No naive dirty-mask-only.
- Sprites: a READY generation must own together generation number, READY SAT-bank identity, READY
  worklist + count, pattern source descriptors, ready/dirty control state, cancellation state, and
  reservation-cleanup metadata; publisher residency/reservation updates must complete before the next
  WORK allocator. List+count double-buffer alone is insufficient. (No implementation in this task.)

## Status
Trace repair complete; self-validated. **NOT self-declared Tighe-ready** — next gate is Cody's final
recheck of this debugger-exact trace. No production source, no ROM, counter 400.

---

# UPDATE 3 — profiling finalization (real-time VDP ownership + worker-cycles-by-load)

Trace-only changes after the first clean controlled run. No production source, no ROM, counter 400.

## Changes
- **Exact cycles preserved.** Debugger breakpoints PE 0x70250 / PR 0x702D2 / WE 0x3A208 / WR 0x3A27E,
  paired per handler via `totalcycles`. No beam subtraction used as timing. WR now additionally carries
  `w@FFBED4` (this tick's emitted count; the producer wrote it at runtime 0x743A6 earlier in the same
  worker, next write is the next IRQ6's worker — so the worker↔load association is exact, in-order, no
  off-by-one generation).
- **Real-time VDP ownership restored (removed the async "VW" debugger watchpoint).** The debugger
  watchpoint events and PE/PR breakpoint events drain from one console log but are not guaranteed
  mutually chronological, which produced the false GATE FAIL + 100%-UNKNOWN target breakdown. VDP
  ownership is now owned by a **real-time Lua VDP write-tap gated by a real-time `publication_active`
  flag set at VC_MARK0 (true) / VC_MARK6 (false)** on `vblank_vc`. Debugger events own exact cycles only;
  the two jobs are no longer conflated.
- **Forced-blank caveat.** For the normal display-on Build-0400 variant profiled here, VC_MARK0..6 is
  the correct real-time publication bracket (no VDP write occurs MARK6→PUB_RTS). If a forced-blank
  variant ever writes a display-enable after MARK6, the bracket must be extended or that tail classified
  separately — do not create a future false positive.
- **Worker/IRQ cycles bucketed by emitted-sprite load** (0-9…70-79): samples, worker cyc med/p75/p95/max,
  ms med/p95, frame-budget multiple med/p95, %>128,009 cyc; plus Pearson r(emitted, worker_cycles)
  (correlation, not causation). **Publication cycles are intentionally left UNBUCKETED** (publication
  commits frame N-1 while the worker produces N — bucketing by this tick's load would be off-by-one).
- Frame budget constant: **128,009 cycles = 16.68 ms** (7.6705 MHz / 59.922 Hz).

## Self-validation (forced-arm headless)
PE→PR→WE→WR pairing clean (0 rejected, 0 orphans); VW removed so it can no longer reset pairing;
real-time VC_MARK gate PASS with no false positives on publication DMA/PIO; target categories populate
(SAT=VSRAM=HScroll = one per handler, UNKNOWN=0); worker-cycle bucket sample total == complete worker
pairs (reconciles); emit-tap per-bucket prodC == WR-emitted per-bucket count (cross-validates the
generation association); incomplete boundary pairs excluded; M resets all bucket + correlation state.
Pearson is N/A in attract (near-constant load, no x-variance) — expected; it computes under varied load.

## BANKED (authoritative, from the first clean controlled run; do NOT merge the parser-bug run)
- gameplay tick/display ≈ **0.65–0.69** across two controlled sessions.
- worker cycles: median **164,482**, p95 **285,088**, max **1,174,736** (= 1.29 / 2.23 / 9.2 frames).
- publication cycles: median **4,367**, p95 **14,369**, max **31,347** (= 0.57 / 1.87 / 4.1 ms).
- IRQ-total: median 171,101, p95 289,855, max 1,177,929. worker frame-wraps med 1 / p95 2 / max 9.
- **gameplay worker has NO observed direct VDP access outside publication** (every flagged write was a
  publication routine — see below). Corroborates the prior genuine clean GATE PASS.
- Slowdown is **primarily worker cost** (worker median ~37× publication median). Publication is not the
  primary cause of the crawl, but at p95 (1.87 ms) / max (4.1 ms) it exceeds the ~1.5 ms physical VBlank,
  so a reliably-VBlank-fitting commit remains a SECONDARY requirement.
- Reaching ~60 fps needs the worker's ~164 K cycles reduced ~22.2% to reach the 128,009 budget at the
  median; the scheduling rewrite fixes continuity/correctness but does not itself reduce worker cycles.

## INVALID / DO NOT USE (instrumentation artifacts of the async VW watchpoint ordering)
- The latest run's printed **GATE FAIL = 6108** — every offender was a publication routine
  (`vdp_commit_palette` 0x7034C, `vdp_dma_words_to_vram` 0x702E8/F4/FE/310/31C/32C) writing DMA
  autoinc/length/source/address programming. **Not** a gameplay direct-VDP writer. Bank the semantic
  conclusion: no non-publication gameplay VDP writer observed.
- The latest run's **100% UNKNOWN target breakdown** — same async-ordering cause. Unusable.
Both are fixed by the real-time VC_MARK bracket; the next run prints the correct mechanical verdict.

## UPDATE 3b — HEAVY definition (Tighe) + render-vs-gameplay attribution
HEAVY is NOT a numeric emitted bucket. It is the user-observed worst case: **stay in one location,
let the enemy population build, remain until the "hurry-up" bats spawn, and hold while the screen is
extremely crowded** (Rastan is invincible in this dev build so the pathological state can persist long
enough to measure). LIGHT = ordinary traversal; MEDIUM = normal combat; HEAVY = sustained dense
enemies + hurry-up bats + Tighe holding position.

Interpretation caveat: the worker = enemy/actor updates + AI + collision + bookkeeping + native sprite
production. A worker-cycle rise is NOT automatically rendering. Attribution method (trace-only, no
production change): **compare worker cycles at EQUAL emitted-count across phases** (the per-emitted
worker-cycle buckets) and read the per-handler **`frame_timing_series.csv`** (frame, emitted,
worker_cyc, irq_cyc, pub_cyc, worker_entry_V, frame_wraps). If, at the same emitted bucket, worker
cycles jump when the bats appear, the rise is gameplay/AI, not sprite output; if they stay flat, it is
render-bound. Pearson r(emitted, worker) measures how much worker variance emitted alone explains
(emitted and active-actor count co-vary, so r alone cannot fully separate them — the equal-emitted
cross-phase comparison is the cleaner test). A dedicated producer-cycle sub-bracket was NOT added
because sprite submission is interleaved inside the arcade gameplay driver (0x41F30), making a single
clean render/gameplay bracket fragile; the equal-emitted + time-series method avoids that.
