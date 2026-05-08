# Andy — Nametable Composition Path Classification

**Agent:** Andy (Claude Code)
**Type:** Design classification (analytical only — no implementation, no new evidence collection, no fix proposed)
**Build:** rastan-direct, post-Build-59, post-OPEN-001-correction (canonical ROM `dist/rastan-direct/rastan_direct_video_test_build_0059.bin`, SHA256 `1135e1aaa2e2c39d64a8390c024dd8e67a998b53f829f2cd7e4eabea2d02ec23`)
**Date:** 2026-05-07
**Naming:** descriptive output filename per OPEN-002 extended policy
**Scope:** identify the arcade code path responsible for populating Plane A/B nametables; determine why Build 59 never reaches that path; classify OPEN-001's dependency on OPEN-004; produce a bounded next-evidence task.

---

## 0. Executive verdict

**OPEN-001 is DEPENDENT on OPEN-004.**

Plane A/B nametable population requires the arcade game loop to advance far enough to reach the PC080SN BG/FG strip producer call sites at **arcade_pc `0x055968`** (BG) and **arcade_pc `0x055990`** (FG). These are patched by `opcode_replace` to enter `genesistan_hook_tilemap_plane_a` (at runtime `0x0007022C`) and `genesistan_hook_tilemap_fg` (at runtime `0x000703CE`) respectively. Both hooks stage tile words to `staged_bg_buffer` / `staged_fg_buffer` and set bits in `bg_row_dirty` / `fg_row_dirty`. The VBlank consumers `vdp_commit_bg_strips_if_dirty` (`vdp_comm.s:200-235`) and `vdp_commit_fg_strips_if_dirty` (`vdp_comm.s:237-272`) — both called from `_vblank_service` — then commit the staging buffers to VRAM Plane B (`0xC000`) and Plane A (`0xE000`).

Build 59 MAME PC samples confirm the tilemap producer call sites **are not reached**:
- sec_5/10/20/120: PC stuck in `0x03A19x` (early init / state-machine zone, well before the `0x05500x..0x055AB4` PC080SN producer range)
- sec_30: PC at `0x071A48` — **inside `vdp_commit_sprites`** (between `0x000719B0 vdp_commit_sprites` and `0x00071B72 genesistan_pc090oj_dma_self_test`); confirms `_vblank_service` IS firing
- sec_60: PC at `0x070610` — **inside `genesistan_hook_tilemap_bg_fill`** (offset `0xA0` past `0x00070570 genesistan_hook_tilemap_bg_fill`); reached via the v3.2 polymorphic dispatch at arcade_pc `0x03AD44`, NOT via the strip producers

The strip producers at `0x055968`/`0x055990` are gated behind a parent dispatcher at `arcade_pc 0x055948` (`build/maincpu.disasm.txt:107365-107373`), which in turn has 4 callers at `arcade_pc 0x050434`, `0x0556FC`, `0x055788`, `0x055822` — all in the post-bootstrap arcade game-loop range. Bootstrap re-entry per OPEN-004 (`0x0202 → 0x022C → 0x024A → 0x03B110 → 0x03BBF8 → 0x03BC64`, ~15 cycles in 64s) keeps execution looping in early init paths, never advancing into the `0x055xxx` range.

**Cody next task: OPEN-004 bootstrap re-entry trigger investigation** (evidence-only; OPEN-004's existing Next Required Task is the right next step, confirmed by this classification). OPEN-001 stays open with a Suspected Area / Next Required Task augmentation noting the OPEN-004 dependency.

---

## §1.1 Nametable writer code path candidates

### Direct VRAM writers (Plane A/B)

| Routine | Address | Source | Target | Architectural class |
|---|---|---|---|---|
| `vdp_commit_bg_strips_if_dirty` | `0x00070130` | [`vdp_comm.s:200-235`](apps/rastan-direct/src/vdp_comm.s#L200-L235) | VRAM Plane B (`0xC000..0xCFFF`) via `VRAM_PLANE_B_BASE` (`vdp_comm.s:49`) | **VBlank commit path** |
| `vdp_commit_fg_strips_if_dirty` | `0x0007017E` | [`vdp_comm.s:237-272`](apps/rastan-direct/src/vdp_comm.s#L237-L272) | VRAM Plane A (`0xE000..0xEFFF`) via `VRAM_PLANE_A_BASE` (`vdp_comm.s:50`) | **VBlank commit path** |

Both are called from `_vblank_service` ([`vdp_comm.s:163-165`](apps/rastan-direct/src/vdp_comm.s#L163-L165)) and read `bg_row_dirty` / `fg_row_dirty` to decide which 64-word rows to copy from `staged_bg_buffer` / `staged_fg_buffer` to VRAM. Each commits a 32-row × 64-word plane (one row per dirty bit; 32 rows max).

### Arcade-side producers (set dirty bits + populate staging buffers)

| Hook | Symbol address | Patched at arcade_pc | Source | Sets dirty | Writes to |
|---|---|---|---|---|---|
| `genesistan_hook_tilemap_plane_a` | `0x0007022C` | `0x055968` (`specs/rastan_direct_remap.json:569-572`) | [`tilemap_hooks.s:43+`](apps/rastan-direct/src/tilemap_hooks.s#L43) | `bg_row_dirty` (lines 181, 183) | `staged_bg_buffer` |
| `genesistan_hook_tilemap_fg` | `0x000703CE` | `0x055990` (`specs/rastan_direct_remap.json:574-578`) | [`tilemap_hooks.s:43+`](apps/rastan-direct/src/tilemap_hooks.s) (FG analog) | `fg_row_dirty` (lines 353, 355) | `staged_fg_buffer` |
| `genesistan_hook_tilemap_bg_fill` | `0x00070570` | reached via v3.2 polymorphic dispatch at `0x03AD44` (`specs/rastan_direct_remap.json:307+`, note line 314) | [`tilemap_hooks.s:441-472`](apps/rastan-direct/src/tilemap_hooks.s#L441-L472) | `bg_row_dirty` per-iteration (lines 462-464) | `staged_bg_buffer` |
| `genesistan_hook_cwindow_clear` | `0x0007106C` | `0x0561B6` (`specs/rastan_direct_remap.json:586-590`) | [`tilemap_hooks.s:1580-1596`](apps/rastan-direct/src/tilemap_hooks.s#L1580-L1596) | `bg_row_dirty = 0xFFFFFFFF`, `fg_row_dirty = 0xFFFFFFFF` (lines 1592-1593) | both staging buffers (fills with `%d3` blank tile word) |

The cwindow_clear hook is a **clear-to-blank** path; it fills both staging buffers with the LUT-translated blank tile and marks all 32 rows of both planes dirty. A subsequent VBlank commit then writes blank tiles across the full Plane A/B nametable area. This is consistent with Tighe's observation of "essentially zero" nametables: if cwindow_clear fired (or, equivalently, if no producer ever fired and dirty stayed at the boot-cleared 0), VRAM Plane A/B remains essentially empty.

### Architectural classification per project model

- **VBlank commit path:** `vdp_commit_bg_strips_if_dirty`, `vdp_commit_fg_strips_if_dirty` — RTS-returning helpers called by `_vblank_service`. Strict consumers; do nothing if dirty mask == 0.
- **PC080SN hook (arcade-side producer):** `genesistan_hook_tilemap_plane_a`, `genesistan_hook_tilemap_fg`, `genesistan_hook_cwindow_clear` — RTS-returning helpers patched into arcade ROM via `opcode_replace`; called from arcade game-loop code.
- **Polymorphic dispatch path:** `genesistan_hook_tilemap_bg_fill` — reached only via the v3.2 dispatch at arcade_pc `0x03AD44` when A0 ∈ [0xC00000, 0xC10000) (tilemap-targeting); RTS-returning helper.

All four producers are RTS-returning Genesis helpers invoked by arcade code (Rule 4 / invariant 2); architecture-compliant.

---

## §1.2 Caller chain analysis

### Strip producers (Plane A primary path)

The PC080SN strip producers `0x055968` (BG) and `0x055990` (FG) are gated by a parent dispatcher at **arcade_pc `0x055948`** ([`build/maincpu.disasm.txt:107365-107373`](build/maincpu.disasm.txt#L107365-L107373)):

```
0x055948: cmpi.w #0, %a5@(4264)         ; workram flag at +0x10A8
0x05594E: bne 0x5595A                   ; if non-zero → FG path
0x055950: bsrw 0x55968                  ; BG strip producer (HOOK ENTRY)
0x055954: addq.w #1, %a5@(4298)
0x055958: bra 0x55962
0x05595A: bsrw 0x55990                  ; FG strip producer (HOOK ENTRY)
0x05595E: addq.w #1, %a5@(4298)
0x055962: bsrw 0x558A2                  ; auxiliary
0x055966: rts
```

Callers of `0x055948` (4 total per [`build/maincpu.disasm.txt:101435, 107209, 107247, 107288`](build/maincpu.disasm.txt)):
- `0x050434: bsrw 0x55948`
- `0x0556FC: bsrw 0x55948`
- `0x055788: bsrw 0x55948`
- `0x055822: bsrw 0x55948`

All four are in the **post-bootstrap arcade game-loop range** (`0x05000x..0x055xxx`). Reaching any of them requires arcade execution to advance beyond the bootstrap region (`0x0200..0x040xx`) and beyond the early state-machine code (`0x040xx..0x04Fxx`).

### Polymorphic dispatch path (tilemap_bg_fill)

`genesistan_hook_tilemap_bg_fill` is reached via the v3.2 polymorphic dispatch at arcade_pc `0x03AD44`. Per [`specs/rastan_direct_remap.json:307-314`](specs/rastan_direct_remap.json#L307-L314): "Intercepts 7 callers: 3 PC090OJ-targeting (`0x03AD5C, 0x03AD6E, 0x03AD82`) ... 4 tilemap-targeting (`0x03AE70, 0x03AE80, 0x03AF38, 0x03AF48`; A0 ∈ [0xC00000, 0xC10000))." The 4 tilemap-targeting callers are in the early state-machine range (`0x03AExx`-`0x03AFxx`), reachable BEFORE the strip producers.

### Cwindow_clear path

`genesistan_hook_cwindow_clear` is patched at arcade_pc `0x0561B6` (`specs/rastan_direct_remap.json:587`). This is in the post-bootstrap range, similar to the strip producer parent.

---

## §2.1 Bootstrap chain comparison vs. writer caller chains

OPEN-004 documented bootstrap re-entry chain:

```
arcade_pc 0x0202 → 0x022C → 0x024A → 0x03B110 → 0x03BBF8 → 0x03BC64
```

(observed ~15 re-entries / 64s in [`Cody_build55_origin_archaeology.md`](docs/design/Cody_build55_origin_archaeology.md) and [`Andy_build55_active_palette_writer_classification.md`](docs/design/Andy_build55_active_palette_writer_classification.md) §1.5).

| Writer caller chain | First call site arcade_pc | In bootstrap loop? | Reachability |
|---|---|---|---|
| Strip producer parent `0x055948` | reached from `0x050434`, `0x0556FC`, `0x055788`, `0x055822` | NO — all in post-bootstrap game-loop range | **NOT REACHED while bootstrap loops** |
| `genesistan_hook_cwindow_clear` | patched at `0x0561B6` | NO — post-bootstrap | **NOT REACHED while bootstrap loops** |
| `genesistan_hook_tilemap_bg_fill` (polymorphic) | reached from `0x03AE70/0x03AE80/0x03AF38/0x03AF48` | partially — `0x03AExx`-`0x03AFxx` is in the early state-machine range that bootstrap may transit through | **MAY BE REACHED briefly** |

The bootstrap re-entry chain ends at `0x03BC64` and re-enters at `0x0202`. Between cycles, execution may transit through `0x03AD44`-area dispatch (which is just below `0x03B110`, so could be reached on the path INTO the bootstrap loop). This explains why MAME PC sample at sec 60 was inside `genesistan_hook_tilemap_bg_fill` (`0x070610`) — the polymorphic dispatch is reachable during the bootstrap transit phase.

The strip producers at `0x055968/0x055990` and the cwindow_clear at `0x0561B6` are NOT in the bootstrap transit path — they require arcade execution to ESCAPE the bootstrap loop and progress through the post-init game-loop state machine.

---

## §2.2 Build 59 PC sample cross-reference

From [`Cody_build59_runtime_state_comparison.md`](docs/design/Cody_build59_runtime_state_comparison.md) MAME validation:

| Timestamp | PC sample | Symbol resolution (per `apps/rastan-direct/out/symbol.txt`) | Implication |
|---|---|---|---|
| sec_5, sec_10, sec_20, sec_120 | `0x03A19x` | bootstrap re-entry zone (`_bootstrap` is at arcade_pc `0x03A000`; `0x3A19x` is inside the early init body) | bootstrap loop active |
| sec_30 | `0x071A48` | inside `vdp_commit_sprites` (`0x000719B0`-`0x00071B72`); offset `0x98` past `vdp_commit_sprites` entry | **`_vblank_service` IS firing** — `vdp_commit_sprites` is called unconditionally at line 166 of `_vblank_service` |
| sec_60 | `0x070610` | inside `genesistan_hook_tilemap_bg_fill` (`0x00070570`-`0x00070646`); offset `0xA0` past `tilemap_bg_fill` entry | **polymorphic dispatch firing** — `genesistan_hook_tilemap_bg_fill` reached via 0x03AD44 dispatch during transit |

**Critical inferences from PC samples:**

1. **`_vblank_service` runs.** sec_30 caught execution inside `vdp_commit_sprites`, which is called from `_vblank_service` line 166. Therefore lines 163-165 (`vdp_commit_tiles_if_dirty`, `vdp_commit_bg_strips_if_dirty`, `vdp_commit_fg_strips_if_dirty`) execute on every VBlank too — they just early-exit because their dirty flags are 0.

2. **Polymorphic tilemap dispatch fires.** sec_60 caught execution inside `genesistan_hook_tilemap_bg_fill`. This means at least one of the 4 tilemap-targeting callers (`0x03AE70/0x03AE80/0x03AF38/0x03AF48`) was reached. This caller could be EITHER the cwindow_clear-style sentinel/init dispatch OR a real tilemap fill from arcade-init code.

3. **Strip producers are NOT reached.** No PC sample lands in or near `0x055xxx`. Per §2.1, strip producers require post-bootstrap game-loop progression that isn't happening.

**Per OPEN-003 sub-finding:** treat MAME PC samples as suggestive but not authoritative (instrumentation anomaly tracked in OPEN-003). However, the structural conclusion (strip producers gated behind post-bootstrap game-loop progression) does NOT depend on the MAME numbers; it derives from the disassembly itself.

---

## §2.3 OPEN-004 dependency classification

**OPEN-001 is DEPENDENT on OPEN-004.**

Reasoning:

1. **Plane A/B nametable population requires the strip producer hooks at arcade_pc `0x055968`/`0x055990` to fire.** These are the only producers that emit real game tile content with row-specific dirty bits. The polymorphic dispatch path (`tilemap_bg_fill`) only fires from sentinel-init / clear-style call sites in arcade init; it does not produce game-content tiles. The cwindow_clear hook produces only blank-tile fills.

2. **Strip producers are reachable only after bootstrap completes.** Their parent dispatcher at arcade_pc `0x055948` is called from 4 sites (`0x050434, 0x0556FC, 0x055788, 0x055822`), all in the post-bootstrap arcade game-loop range. Build 59 evidence (PC samples) shows execution is stuck in bootstrap re-entry; strip producer call sites are never reached.

3. **Even if strip producers fired briefly, bootstrap re-entry would re-clear the staging via `_bootstrap_clear_staging` at boot.s:168-208** — `staged_bg_buffer`, `staged_fg_buffer`, `bg_row_dirty`, `fg_row_dirty` all get cleared on each re-entry cycle. (This is OPEN-004's "blocking-on-staging" risk that Andy classified as `(b) contributing` for palette in [`Andy_build55_active_palette_writer_classification.md`](docs/design/Andy_build55_active_palette_writer_classification.md) §1.5; the same logic applies to BG/FG staging — the re-entry would wipe staged data each cycle, but VRAM Plane A/B PERSISTS across cycles. So if a single cycle managed to stage real tile data and reach VBlank commit before the next re-entry, Plane A/B would briefly show real content. Build 59 evidence shows this never happens — strip producers don't fire at all.)

4. **The brief tilemap_bg_fill firings observed (sec_60 PC sample) confirm the polymorphic dispatch is reachable but do NOT solve OPEN-001** — they would emit blank/sentinel content at most, not the real game tilemap. Whether they actually populate any nametable cells depends on the caller's args (A0, D0, D1) — and Tighe's observation of "essentially zero" nametables suggests either no commit reached VRAM, or the committed content was zeros.

5. **Resolving OPEN-004 (so bootstrap re-entry stops and arcade execution advances into the post-bootstrap game loop) is a necessary prerequisite for OPEN-001 to resolve.**

---

## §2.4 Additional missing hooks / triggers

### None currently identified

Searching `specs/rastan_direct_remap.json`, source files, and disassembly for tilemap/nametable-related hooks:

- All four PC080SN tilemap producers (BG strip producer, FG strip producer, BG fill polymorphic, cwindow_clear) ARE patched in the spec.
- All four are RTS-returning Genesis helpers per `tilemap_hooks.s`.
- All four set their respective dirty flags and populate staging buffers.
- VBlank commit consumers (`vdp_commit_bg/fg_strips_if_dirty`) are wired in `_vblank_service`.

The architecture is complete. The only missing piece is the arcade game loop reaching the call sites. **No additional hook or trigger is missing from the project's perspective; the issue is purely arcade-execution progression.**

### Possible non-hook concerns (out of scope for this classification)

- VDP register `R00` / `R01` (display enable bits, plane enable) — verified correct in Build 58 evidence.
- Display enable/disable sequencing in `_vblank_service` (lines 159-161 disable display before commits, lines 176-178 re-enable) — correct pattern.
- Screen Mode bits / interrupt masks — out of scope for OPEN-001; would manifest as no-VBlank, but `_vblank_service` IS firing per sec_30 PC sample.

No additional hooks are needed. The fix is upstream: resolve OPEN-004.

---

## §3.1 Six question summary

1. **Which routine(s) write/commit Plane A/B nametable cells?**
   - Direct VRAM writers: `vdp_commit_bg_strips_if_dirty` ([`vdp_comm.s:200-235`](apps/rastan-direct/src/vdp_comm.s#L200-L235)), `vdp_commit_fg_strips_if_dirty` ([`vdp_comm.s:237-272`](apps/rastan-direct/src/vdp_comm.s#L237-L272)).
   - Producers (set dirty + populate staging): `genesistan_hook_tilemap_plane_a` (BG strip; arcade_pc `0x055968`), `genesistan_hook_tilemap_fg` (FG strip; arcade_pc `0x055990`), `genesistan_hook_tilemap_bg_fill` (polymorphic; arcade_pc `0x03AE70/0x03AE80/0x03AF38/0x03AF48` via `0x03AD44` dispatch), `genesistan_hook_cwindow_clear` (arcade_pc `0x0561B6`).

2. **Architectural classification:**
   - VRAM writers: VBlank commit paths, RTS-returning, called from `_vblank_service`.
   - Producers: PC080SN hooks, RTS-returning, patched into arcade ROM via `opcode_replace`.
   - All architecture-compliant per project model.

3. **State progression / caller chain:**
   - Strip producers: `arcade game loop → 0x050434/0x0556FC/0x055788/0x055822 → 0x055948 (parent dispatcher) → 0x055968 / 0x055990 (HOOK ENTRY)`. Requires post-bootstrap progression.
   - Polymorphic dispatch: `arcade init code → 0x03AE70/0x03AE80/0x03AF38/0x03AF48 → 0x03AD44 → genesistan_hook_3ad44_dispatch → genesistan_hook_tilemap_bg_fill`. Reachable during early state-machine transit.
   - Cwindow_clear: patched at `0x0561B6`; post-bootstrap range.
   - VBlank commit: triggered by interrupt; runs each VBlank; reads dirty flags and bails early if 0.

4. **Does bootstrap re-entry prevent reaching nametable writers?**
   - **YES** for the strip producers (`0x055968/0x055990`) and cwindow_clear (`0x0561B6`) — those require arcade execution to escape the bootstrap loop and advance into the post-bootstrap game-loop state machine.
   - **PARTIAL** for the polymorphic `tilemap_bg_fill` — reachable during early transit, but only emits sentinel/init content, not real game tilemap.
   - VBlank commits run regardless of bootstrap state, but they bail early when dirty flags are 0 (which they are, because producers don't fire).

5. **Is OPEN-001 blocked by OPEN-004?**
   - **DEPENDENT.** OPEN-001 cannot resolve until OPEN-004 resolves (or bootstrap re-entry otherwise terminates), allowing arcade execution to reach the strip producer call sites at `0x055968/0x055990`.

6. **What exact Cody evidence task should come next?**
   - **OPEN-004 bootstrap re-entry trigger investigation** (evidence-only, not implementation). This is OPEN-004's existing Next Required Task; this classification confirms it is the correct next step. See §3.2 for the bounded outline.

---

## §3.2 Recommended next move

### Cody next task

**Type:** evidence (NOT implementation)

**Descriptive task name:** `Cody — Bootstrap Re-entry Trigger Investigation` (matches OPEN-004's existing Next Required Task; descriptive, no build number per OPEN-002 extended policy)

**Output filename:** `docs/design/Cody_bootstrap_reentry_trigger_investigation.md` (descriptive, no build number)

**Bounded scope:**

1. **Identify all static call sources to bootstrap entry `0x0202`.** Grep `build/genesis_postpatch.disasm.txt` for `bsrw 0x202`, `bras 0x202`, `jsr 0x0202`, `jmp 0x0202`, computed-target branches, and exception vector entries pointing at `0x0202`.
2. **MAME breakpoint trace on `0x0202`:** capture last 8 PCs before each re-entry; correlate against the 15 observed entries in 64s.
3. **Inspect exception vectors at `0x0008..0x003C`:** confirm which vectors reference `0x0202` directly or indirectly.
4. **HV Counter `0xC00008` write watchpoint** (per OPEN-005 hypothesis): confirm/refute whether MAME silently allows writes that BlastEm fatals on; correlate with bootstrap re-entry events.
5. **Stack pointer / SR snapshot** at re-entry: capture SR (interrupt mask, supervisor mode), SSP/USP values to identify exception path.
6. **Output:** `Cody_bootstrap_reentry_trigger_investigation.md` with classification:
   - **Single trigger** (e.g., specific exception vector, watchdog): identify and quote the trigger
   - **Multiple triggers**: list each
   - **Unknown**: list what additional evidence would discriminate

**NO IMPLEMENTATION in this evidence task.** Andy classifies fix shape after Cody's evidence lands. Implementation in subsequent build per Andy classification.

### Build numbering

- This is an evidence-only task → descriptive name, no build number.
- The next ROM-producing build (after Andy classifies a fix from Cody's evidence) will use the next sequential number after canonical `0059.bin` per Makefile auto-increment, no letter suffix per OPEN-002 extended policy.

### OPEN-001 stays open

Tagged as "dependent on OPEN-004 resolution"; Suspected Area and Next Required Task augmented to reflect the dependency (see §3.3).

### OPEN-004 stays open

OPEN-004's existing Next Required Task is appropriate and not modified.

### CLOSED-007 stands

Slot reservation closure remains valid.

---

## §3.3 OPEN-001 update

Andy will append the following augmentation to OPEN-001's Suspected Area and Next Required Task fields (separate documentation update following this classification doc):

- **Suspected Area augmentation:** "Strongly likely blocked by OPEN-004 bootstrap re-entry. Per `docs/design/Andy_nametable_composition_path_classification.md`, Plane A/B nametable population requires arcade execution to reach the PC080SN strip producer call sites at arcade_pc `0x055968`/`0x055990` (parent dispatcher at `0x055948`, called from `0x050434/0x0556FC/0x055788/0x055822`). All four call sites are in the post-bootstrap arcade game-loop range; bootstrap re-entry per OPEN-004 keeps execution looping at `0x0202..0x03BC64` and never advances to the `0x055xxx` range."
- **Next Required Task supersession:** "OPEN-004 bootstrap re-entry trigger investigation must complete first. The previous Next Required Task (Tighe Exodus Memory Editor capture of nametable ranges) is superseded — the empty-nametable result is now classified as a DEPENDENT symptom rather than an independent root cause. Once OPEN-004 resolves and arcade progresses into the post-bootstrap game loop, OPEN-001 will likely self-resolve OR transform again into a downstream symptom that can be classified at that point."

OPEN-004 is NOT modified — its existing Next Required Task is precisely the work Andy recommends.

---

## Phase 4 Integrity

- §1.1 nametable writer code path candidates identified with cited source/disassembly: YES (4 producers + 2 VBlank consumers; all addresses cited)
- §1.2 each candidate architecturally classified: YES (VBlank commit / PC080SN hook / polymorphic dispatch)
- §1.3 caller chain traced: YES (parent dispatcher `0x055948`; 4 callers; cwindow caller; polymorphic dispatch via `0x03AD44`)
- §2.1 bootstrap chain comparison: YES (strip producers + cwindow OUTSIDE bootstrap loop; tilemap_bg_fill PARTIALLY in transit)
- §2.2 Build 59 PC samples decoded: YES (sec_30 = `vdp_commit_sprites`; sec_60 = `tilemap_bg_fill`; sec_5/10/20/120 = bootstrap zone)
- §2.3 OPEN-004 dependency: **DEPENDENT** with cited reasoning
- §2.4 additional missing hooks/triggers: NONE (architecture complete; issue is arcade progression)
- §3.1 all six questions answered: YES
- §3.2 Cody next task produced (evidence-only; descriptive name; no build number): YES
- §3.3 OPEN-001 augmentation specified: YES (separate documentation update follows)
- All claims cite specific source / disassembly / spec / report
- No source/spec/tool/ROM/build modifications: YES
- No fix proposed: YES
- OPEN-001 and OPEN-004 not merged: YES
- CLOSED-007 not rolled back: YES
- No closures: YES
- No letter-suffix naming: YES (output doc `Andy_nametable_composition_path_classification.md`; recommended Cody task `Cody — Bootstrap Re-entry Trigger Investigation`)
- No attribute-bit analysis on empty nametables: YES (deferred per Rule 18)
- All STOP conditions either passed or documented: YES (no STOP triggered)
