# Original Rastan Arcade Frame-Worker Semantics → Genesis Native Map

Status: STATIC SEMANTIC RECOVERY. No production code change. No ROM. Counter 400.
Author: Andy. Continues `Andy_build0400_irq6_decomposition_and_reorder_plan.md`.

Authorities used: ORIGINAL arcade semantics from the existing Ghidra project exports
(`analysis/ghidra/rastan_arcade/exports/`: `linear_disassembly.tsv`, `decompiler_export.c`,
`function_inventory.tsv`, `hw_refs.tsv`, `call_graph_edges.tsv`, `memory_map.md`, `subsystem_map.md`);
GENESIS implementation from source (`apps/rastan-direct/src/*.s`). No re-import, no Ghidra on our
own Genesis code. Arcade addresses are arcade-native (the maincpu copy rebases non-uniformly — shift
deltas, not a flat +0x200 — so Genesis runtime PCs are NOT derived by arithmetic here).

Arcade memory map (memory_map.md): a5 WRAM base 0x10C000; PC080SN tilemap 0xC00000-0xC0FFFF, Yscroll
0xC20000, Xscroll 0xC40000, ctrl 0xC50000; PC090OJ sprite RAM 0xD00000-0xD03FFF; palette 0x200000;
sprite-ctrl 0x380000; inputs 0x390000; watchdog 0x3C0000; IO nop 0x350008.

---

## ORIGINAL ARCADE IRQ / FRAME TREE  [STATIC: linear_disassembly.tsv + function_inventory.tsv]

`vector_1d_target_03a008` — the **Level-5 autovector** (vector 0x1D) = arcade VBlank handler. Verbatim
original (this is what the Genesis port replaced the two watchdog writes of with 6 NOPs):

```
0x3A008  ori.w  #0x0F00,%sr            ; [ISR] raise IPL7 (mask all) — atomicity/convention
0x3A00C  clr.w  0x350008              ; [HW] IO nop-write (MAME nopw)         } the two instrs the
0x3A012  move.w %d0,0x3C0000          ; [HW] WATCHDOG reset kick              } Genesis port NOP'd (6 NOPs)
0x3A018  move.w %a5@(2),%d0 ; cmpi #2 bcs .common ; cmpi #4 bcc .common   ; game-mode gate
0x3A028  bsr    0x3A126               ; pre-gameplay conditional (-> 0x3F09C/0x3F084)
0x3A02C  tst.w  %a5@(0); beq .common
0x3A032  cmpi.w #1,%a5@(0x1394); beq .common
0x3A03A  bsr    0x41F30               ; GAMEPLAY DRIVER (player/actors + PC090OJ sprite submission)
.common:
0x3A03E  bsr    0x3AB7C               ; warm_restart_gate_caller_a (watchdog/restart gate -> 0x3F084)
0x3A042  bsr    0x3ABE2               ; object/gameplay subs (-> 0x3AC04/0x3AC8A/0x3ACF4)
0x3A046  bsr    0x3A0A8               ; INPUT read (0x390005) + 0x3AE28/0x3AE3C/0x3AE46
0x3A04A  bsr    0x3EEFA               ; PALETTE producer (writes 0x200xxx)
0x3A04E  bsr    0x3EF5C               ; PALETTE producer (writes 0x200xxx)
0x3A052  pea 0x3A074 ; (a5@0 state index) ; jump-table @0x3A06C -> frontend_stateN handler
0x3A074  jsr    0x55CA2               ; post-dispatch common
0x3A07A  andi.w #0xF0FF,%sr           ; [ISR] restore IPL
0x3A07E  rte                          ; [ISR] exit
```

Direct callees (function_inventory `callers`/`callees`): `vector_1d_target_03a008` →
`0x3A126`, `0x41F30`, `0x3AB7C warm_restart_gate_caller_a`, `0x3ABE2`, `0x3A0A8`, `0x3EEFA`, `0x3EF5C`,
jump-table state handlers, `0x55CA2`.

---

## ORIGINAL ONE-TICK SEMANTIC ORDER  [STATIC]

1. **ISR entry** — raise IPL7 (0x3A008).
2. **Hardware maintenance** — watchdog/IO kicks (0x3A00C/0x3A012). *Not gameplay.*
3. **Game-mode gate** — read `a5@(2)`; modes 2–3 skip straight to the common subs.
4. **Pre-gameplay conditional** — `0x3A126`; then, if session active (`a5@(0)≠0 && a5@(0x1394)≠1`),
   **gameplay driver `0x41F30`**: player/actor update + PC090OJ sprite submission
   (`0x41F5E` frame-begin → `0x41DAE` dispatch → `actor_family0_render_3d054` → 0xD00000).
5. **Common subs** — `0x3AB7C` (warm-restart/watchdog gate), `0x3ABE2` (object/gameplay),
   `0x3A0A8` (**input** read 0x390005), `0x3EEFA` + `0x3EF5C` (**palette** → 0x200xxx).
6. **State dispatch** — jump table at 0x3A06C indexed by `a5@(0)` → `frontend_stateN_update/init`
   (title/attract/gameplay-state-specific producers; these reach the PC080SN tilemap/scroll writers
   `FUN_000003a4`/`FUN_000002ca` and more sprite work).
7. **Post-dispatch common** — `jsr 0x55CA2`.
8. **ISR exit** — restore IPL, `rte`.

**Hard dependencies (REQUIRED for gameplay semantics):**
- game-mode gate (3) precedes gameplay (4) — it decides whether to run the tick.
- gameplay/actor update (4) precedes PC090OJ submission (within 0x41F30: 0x41F5E begin clears lanes,
  then 0x41DAE dispatch emits) — submission consumes the frame's updated actor state.
- input: **CORRECTED** — the arcade does NOT latch input once for the next tick. Many routines read the
  LIVE hardware ports directly (`btst #n,0x390005/7` in FUN_0003a0a8, FUN_0003ac04/ac8a/acf4,
  warm_restart 0x3AB7C, FUN_000003a4, frontend handlers). Each read sees the controller state at that
  instant during tick N, so input is **current-sample, consumed within tick N**. (0x3A0A8 is one control
  routine, not "the" input latch.) Build 0400 matches this: `update_inputs` snapshots the ports to the
  shadow 0xFF61F6-9 at IRQ6 start, and the rebased arcade routines read that shadow during the same tick.
- palette (5) and state-dispatch producers (6) consume the frame's updated state.

**INCIDENTAL to ISR organization (not gameplay-required):** the IPL7 raise/restore and the watchdog
kicks. The relative order of the independent common subs (input/palette) vs each other is convention,
not a data dependency, except that each reads state the gameplay step already wrote.

---

## ORIGINAL FRAME-WORKER PSEUDOCODE  [STATIC, recovered]

```c
void arcade_vblank_level5(void) {          // vector_1d_target_03a008
    SR |= 0x0F00;                          // ISR: IPL7
    io_nop_350008 = 0; watchdog_3C0000 = d0;   // ISR: hardware maintenance (Genesis: removed)
    arcade_frame_worker();                 // <-- the real one-frame tick (body 0x3A018..0x3A074)
    SR = (SR & 0xF0FF);                    // ISR: restore IPL
    rte();                                 // ISR: exit
}

void arcade_frame_worker(void) {           // normal-callable; no exception-frame use
    if (!(a5[1]/*mode*/ >= 2 && a5[1] < 4)) {   // game-mode gate
        pre_gameplay_0x3A126();
        if (a5[0] != 0 && a5[0x9CA] != 1)
            gameplay_driver_0x41F30();     // player/actors + PC090OJ sprite submission
    }
    warm_restart_gate_0x3AB7C();           // watchdog/restart gate
    object_subs_0x3ABE2();                 // object/gameplay
    input_read_0x3A0A8();                  // reads 0x390005
    palette_producer_0x3EEFA();            // -> arcade palette 0x200xxx  [Genesis: native palette]
    palette_producer_0x3EF5C();            // -> arcade palette 0x200xxx  [Genesis: native palette]
    state_dispatch[a5[0]]();               // frontend_stateN handlers (tilemap/scroll/sprite intent)
    post_dispatch_common_0x55CA2();
}
```
Hardware-intent calls replaced on Genesis are annotated in the mapping table below.

---

## ORIGINAL ISR-ONLY GLUE  [STATIC — Phase 5 result]

| arcade PC | op | class | needs exception frame? |
|---|---|---|---|
| 0x3A008 | `ori #0x0F00,sr` (IPL7) | ATOMICITY/REENTRY + ISR convention | no (atomicity, not gameplay) |
| 0x3A00C | `clr.w 0x350008` | HW maintenance (IO nop) | no |
| 0x3A012 | `move.w %d0,0x3C0000` | HW maintenance (WATCHDOG) | no |
| 0x3A07A | `andi #0xF0FF,sr` | ISR IPL restore | no |
| 0x3A07E | `rte` | ISR exit | yes (only because entered as ISR) |

**Phase 5 conclusion (from Taito's original code, not our wrapper):** no part of the actual game
worker body (0x3A018–0x3A074) reads the exception frame, assumes a stack layout, or otherwise requires
interrupt context. The ONLY exception-context items are the IPL7 raise/restore (atomicity/convention),
the watchdog/IO kicks (hardware maintenance — already removed on Genesis, which has no watchdog), and
the RTE. **Taito used the Level-5 VBlank purely as the frame-driver for ordinary code.** This
independently confirms (from original intent) that the **original** worker is semantically
mainline-callable. **This does NOT mean the CURRENT Genesis worker is safe to preempt today:** its
publication-visible staging is still partly single-buffered (KF-082), so the Genesis worker becomes
safely preemptible in mainline only AFTER the WORK/READY isolation is complete. Original worker:
semantically mainline-callable. Current Genesis implementation: preemptible only after isolation.

---

## ORIGINAL VIDEO-HARDWARE INTENT  [STATIC: hw_refs.tsv grouped by function]

**PC080SN (tilemap 0xC00000 / Yscroll 0xC20000 / Xscroll 0xC40000 / ctrl 0xC50000):** shared writers
`FUN_000003a4` (42 refs), `FUN_000002ca` (36), plus state/producer routines `FUN_0003a552`,
`FUN_0003ac04`, `FUN_0003add8`, `FUN_0003ae64`, `FUN_0003b098`, `collision_map_surface_mark_5a2ee`.
Intent: set BG/FG tilemap cells (C-window) + set X/Y scroll + tilemap control.

**PC090OJ (sprite RAM 0xD00000):** `FUN_00041dae` (8), `FUN_00045dfa` (6), `FUN_00041f5e` (begin),
`player_aux_sprite_constructor_54810`, `FUN_000540ac`, `FUN_00052aa2`, `actor_family0_render_3d054`
(expander), `FUN_0003ad4c/ad72/add8`, `FUN_0003b8b0/b902`. Intent: submit per-frame object/sprite
records (begin-of-frame reset + per-actor piece expansion).

**Palette (0x200000) / sprite-ctrl (0x380000):** worker leaves `FUN_0003eefa`, `FUN_0003ef5c` (the two
`bsr`s at 0x3A04A/0x3A04E); also `FUN_00000264`, `frontend_state3_update_3a304`. Intent: write the
frame's color/palette and sprite palette-bank/control.

**Other per-frame HW:** input 0x390005 (`FUN_0003a0a8`), watchdog 0x3C0000 (ISR glue).

---

## ARCADE → GENESIS NATIVE MAPPING  [arcade = Ghidra; Genesis = source]

| ORIGINAL ARCADE SEMANTIC | arcade routine | CURRENT GENESIS REPLACEMENT (source) | staging written → publication |
|---|---|---|---|
| sprite frame begin (reset object list) | 0x41F5E `FUN_00041f5e` | `genesistan_pc090oj_hook_target_41f5e` → `native_sprite_frame_begin` (pc090oj_hooks.s:267) | clears native lane counts + `pc090oj_sat_frame_ready` |
| PC090OJ object/sprite submission | 0x41DAE `FUN_00041dae` | `genesistan_pc090oj_hook_target_41dae` → `native_stage_dispatch_41dae` → `pc090oj_native_emit_pass` | native lanes → `staged_sprite_sat[bank]` (DOUBLE) + `pc090oj_tile_dma_worklist` (SINGLE) → `vdp_commit_sprites` SAT+pattern DMA |
| alt sprite submission (mode 2) | 0x45DFA `FUN_00045dfa` | `genesistan_pc090oj_hook_target_45dfa` → `native_stage_dispatch_45dfa` → emit | same as above |
| actor→sprite piece expansion | `actor_family0_render_3d054` | retained arcade expander feeding the native lanes via the hooks | lanes |
| PC080SN tilemap cell writes | `FUN_000003a4`/`FUN_000002ca` + state producers | native Plane A/B producers (tilemap_hooks.s / fg_tile_cache.s) | `staged_fg_buffer`/`staged_bg_buffer` + `fg/bg_row_dirty` → `vdp_commit_fg/bg_strips` |
| PC080SN scroll (0xC20000/0xC40000) | PC080SN scroll writers | native scroll staging | staged scroll → `vdp_commit_scroll` (HScroll + VSRAM) |
| palette / color (0x200000) | 0x3EEFA/0x3EF5C + state3 | native palette staging | `staged_palette_words` (+`palette_pending`) → `vdp_commit_palette` (CRAM) |
| sprite palette-bank/ctrl (0x380000) | palette/ctrl writers | folded into native SAT/palette residency (`pc090oj_sprite_ctrl_shadow`) | SAT attribute / CRAM line |
| input (live ports 0x390001/3/5/7, read by many routines) | FUN_0003a0a8 + ac04/ac8a/acf4 + 0003a4 + frontend | `rastan_direct_update_inputs` snapshots ports → shadow once at IRQ6 start; rebased arcade routines read the shadow (same tick) | input shadow 0xFF61F6-9 |
| watchdog (0x3C0000) / IO (0x350008) | 0x3A00C/0x3A012 | **removed** (Genesis has no watchdog — the 6 NOPs) | — |

---

## CLASSIFY THE ORIGINAL FRAME BY MOVEABILITY  [Phase 8]

| original unit | class | target context |
|---|---|---|
| game-mode gate, pre-gameplay 0x3A126, gameplay driver 0x41F30, object subs 0x3ABE2, state dispatch, 0x55CA2, warm-restart 0x3AB7C | **A pure gameplay** | arcade-owned mainline |
| PC090OJ submission (0x41F5E/0x41DAE/0x45DFA → native_stage/emit) | **B hardware-intent now CPU production** | mainline AFTER tile-worklist READY isolation (KF-082) |
| PC080SN tilemap/scroll producers; palette producers (0x3EEFA/0x3EF5C → native) | **B** | mainline AFTER single-buffered staging isolation |
| the 6 `vdp_commit_*` (CRAM/VRAM/SAT/plane/scroll DMA) | **C Genesis VDP commit** | stays IRQ6 |
| IPL7 raise/restore, RTE, watchdog kicks | **D ISR-only glue** | removed/converted (watchdog already gone) |
| frontend_stateN title/attract, scene/package installs | **E scene/transition special** | evaluate per-case (prepare/commit split) |

---

## TARGET MAINLINE FRAME WORKER  [design, preserving recovered order]

```
arcade_frame_worker():               ; invoked from mainline on one consumed tick_pending
    game-mode gate (a5@2)
    if session active: pre_gameplay_0x3A126; gameplay_driver_0x41F30
        -> player/actor update
        -> native sprite begin + dispatch (replaces 0x41F5E/0x41DAE PC090OJ submission) -> SAT/worklist WORK
    warm_restart_gate_0x3AB7C
    object_subs_0x3ABE2
    input already latched by the short IRQ6 (replaces mid-tick 0x3A0A8 read)
    native palette producers (replace 0x3EEFA/0x3EF5C arcade palette) -> palette WORK
    state_dispatch[a5@0] -> frontend_stateN -> native Plane A/B + scroll producers -> plane/scroll WORK
    post_dispatch_common_0x55CA2
    atomic WORK -> READY
    rts
```
Original arcade semantic decisions (gate, session test, state dispatch, intra-0x41F30 begin→dispatch
ordering) are preserved exactly; only the hardware tails are the already-existing native helpers, and
the ISR glue is dropped (atomicity re-provided narrowly around WORK→READY).

---

## CURRENT GENESIS PUBLICATION TRANSACTIONS  [source]

- **Sprites:** `pc090oj_native_emit_pass`/`native_sprite_emit` → `staged_sprite_sat` (bank, DOUBLE) +
  `pc090oj_tile_dma_worklist`/`_count` (SINGLE) + mutable residency (`sprite_tile_resident_code`,
  reverse dir) → `vdp_commit_sprites_vram` (pattern DMA + SAT DMA). **Isolate: tile worklist.**
- **Plane A:** native FG producer → `staged_fg_buffer` + fg dirty/narrow → `vdp_commit_fg_narrow_strips`.
  **Isolate: small dirty row/col descriptor queue + its source cells.**
- **Plane B:** native BG producer → `staged_bg_buffer` + `bg_row_dirty` → `vdp_commit_bg_strips`.
  **Isolate: dirty-row queue.**
- **Scroll:** staged scroll → `vdp_commit_scroll` (HScroll + VSRAM). **Isolate: few-word snapshot.**
- **Palette:** `staged_palette_words` + `palette_pending` → `vdp_commit_palette` (CRAM). **Isolate:
  64-word/gen snapshot.**
- **Tiles:** `staged_tile_words` + `tiles_dirty` → `vdp_commit_tiles_if_dirty`. **Isolate: bounded job.**

SAT is already DOUBLE; everything else SINGLE (KF-082) → each needs READY isolation before its producer
runs in active display.

---

## CURRENT / ORIGINAL / TARGET ORDER  [Phase 12]

| ORIGINAL ARCADE (Level-5 ISR) | CURRENT BUILD 0400 (Genesis IRQ6) | TARGET GENESIS |
|---|---|---|
| IPL7 + watchdog kicks | L6 → `_vblank_service` (input latch front-loaded) | short IRQ6: ack/timing |
| — (publish was per the arcade's own hw) | `vdp_prepare_sprites` guard; **publish N-1** | if new READY: **publish READY N-1** |
| game-mode gate | tail JMP 0x3A208 worker (IPL7) | set tick_pending; `rte` |
| gameplay 0x41F30 (+PC090OJ submit) | gameplay 0x41F30 (hooks → native emit) | — mainline: consume tick — |
| common subs 0x3AB7C/0x3ABE2/0x3A0A8 | same, inside IRQ6 | gameplay 0x41F30 (→ native emit WORK) |
| palette 0x3EEFA/0x3EF5C | same | common subs (input already latched) |
| state dispatch → frontend_stateN | same | palette + state dispatch (→ plane/scroll WORK) |
| jsr 0x55CA2 | jsr (rebased) | post-dispatch common |
| restore IPL + RTE | restore IPL + RTE → mainline spin | atomic WORK→READY; `rts`; wait |

Relative order of gameplay → sprite submission → palette → state producers is **identical** across all
three columns. The only intentional reorder (already in Build 0400) is input latch front-loaded; it is
consumed by the same tick as the arcade (one-frame input semantics preserved).

---

## STATIC LATENCY AUDIT  [Phase 13; source-level staging, not binary]

| subsystem | arcade age | current Build 0400 | target | added latency |
|---|---|---|---|---|
| gameplay state | produced tick N, drives tick N | same | produced in mainline tick N | NO |
| sprites | submitted during tick N, shown next frame | staged tick N → published N+1 (SAT double) | staged mainline N → published N+1 | NO |
| Plane A/B | tilemap intent tick N → shown next | staged N → published N+1 | staged mainline N → published N+1 | NO |
| scroll | set tick N → shown next | staged N → published N+1 | same | NO |
| palette | set tick N → shown next | staged N → published N+1 | same | NO |
| tile patterns | as needed | worklist N → published N+1 | same | NO |
| input | latched, consumed by tick | latched in IRQ6, consumed by tick | latched in short IRQ6, consumed by tick | NO |

**Additional intentional latency: NO.** Build 0400 already realizes publish-N-1 / produce-N; moving
"produce N" from the IRQ tail to post-RTE mainline keeps the identical relationship for every subsystem.

---

## IMPLEMENTATION CUTS  [Phase 14]

**CUT 1 — sprite path.** ORIGINAL: 0x41F5E/0x41DAE/0x45DFA PC090OJ submission. GENESIS: hooks →
`native_stage_dispatch_*`/`pc090oj_native_emit_pass` (SAT double + tile worklist single). TARGET: run
in mainline after READY-isolating the tile worklist; IRQ6 sprite commit reads READY only.

**CUT 2 — plane/scroll/palette producers.** ORIGINAL: PC080SN writers + 0x3EEFA/0x3EF5C. GENESIS:
native Plane A/B/scroll/palette staging (all single-buffered). TARGET: run in mainline after
READY-isolating each small staging (dirty-queue double-buffer / snapshot).

**CUT 3 — the whole worker.** ORIGINAL: body 0x3A018–0x3A074 wrapped by IPL7/watchdog/RTE glue.
GENESIS: the equivalent native-hooked worker currently tail-jumped from `_vblank_service`. TARGET:
convert to an RTS mainline `arcade_frame_worker`; reduce IRQ6 to ack + conditional READY publish +
`tick_pending` + frame-hold; re-provide atomicity only around WORK→READY. The watchdog glue is already
absent on Genesis, so the ISR-only surface to convert is exactly the IPL7 raise, the IPL restore, and
`rte`→`rts` (matches the decomposition plan §IRQ-context conversion).

Cuts follow the recovered arcade semantics — no new Genesis-owned game loop; the arcade program remains
the execution and scheduling authority (one tick per VBlank opportunity).

---

## REMAINING RUNTIME QUESTIONS (static recovery cannot answer these)

- LIGHT/MEDIUM/HEAVY tick duration; whether a heavy tick fits 16.67 ms.
- External-VBlank : serviced-tick ratio (VINT loss vs serviced-late).
- Worker-RTE → next-IRQ delay (idle window).
- The VDP gate from the decomposition plan: whether the 0xC0xxxx-referencing retained frontend/status
  arcade routines (0x52xxx/0x5Axxx) are gameplay-reachable and write the VDP during the worker — these
  are the arcade's own PC080SN/PC090OJ addresses and MUST be confirmed hooked/unreachable before the
  worker move. (This recovery shows the core gameplay path routes sprite/tilemap/palette intent through
  the native hooks/producers, but a per-routine reachability sweep of the status/frontend families is
  still owed; the gameplay worker-phase VDP-write detector closes it empirically.)
- Exact Build-0400 publication sub-phase spans.
