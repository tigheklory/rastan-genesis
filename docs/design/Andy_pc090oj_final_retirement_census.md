# Andy — Final PC090OJ Retirement Census (Build 0296)

**Task type:** Analysis / Verification ONLY. No production source/spec/remap changes. No Build 0297.
**Baseline:** Build 0296 (`dist/rastan-direct/rastan_direct_video_test_build_0296.bin`, size 1,597,112).
**Question:** Can any reachable current producer create sprite output that still depends on
`PC090OJ record packing → pc090oj_object_ram → frontend 256-record scan → PC090OJ decoder → native SAT`?

**Answer: NO.** The PC090OJ compatibility path is **dead output** in Build 0296. Every former
producer has a native owner or is retired/unreachable; no reachable writer places a drawable code
into `pc090oj_object_ram`; the frontend scan/decoder emit zero object-RAM sprites across the
runtime sweep. Recommended next action: **SAFE TO PERFORM FINAL PC090OJ TEARDOWN.**

---

## Phase 0 — Required Priors Check

**Relevant priors.**
- KF-025 (GENERAL, STRONG): verbatim-copied arcade `move.w`/`move.l`/fill writes to `HW_ADDRESS
  0x00D00000..0x00D007FF` execute on Genesis as raw writes into VDP-mirror space; the cell never
  reaches Genesis staging (renders blank) and may fatally hit the HV-counter port. → any residual
  raw D-range store produces nothing on Genesis regardless of object RAM.
- KF-026 (STRONG, HIGH hazard): PC090OJ write surfaces are not fully statically enumerable (pointer
  -indexed destinations exist). → a runtime backstop is required, not optional.
- KF-045 (CONFIRMED): PC090OJ producer/clear ranges expressed as HW addresses map by record index
  `(HW - 0x00D00000)/8`; A5 base `0x0010C000` → Genesis `0x00FF0000`.
- KF-047/048/049/050/051 (PC090OJ mirror/candidate/shadow architecture, Builds 0176–0192): describe
  the *older* retained-mirror sprite pipeline. Largely SUPERSEDED for gameplay by the native
  semantic lanes; cited here only for lineage.
- OPEN-024 (narrowed): gameplay SAT is direct native semantic-lane output; remaining PC090OJ debt is
  explicitly **frontend/shared**.
- CLOSED-019: gameplay status producer `0x05A098` PC090OJ output tail retired to native; the object
  -table scan/decode for gameplay is not executed.

**Rediscovery-Hazard HIGH findings acknowledged:** KF-011 (arcade Level-5 VBlank owns frame
progression; the native SAT commit is servicing-only — unchanged by any teardown), KF-025, KF-026.

**Deferred entries:** none applicable to sprite/object-RAM ownership.

**Task classification:** EXTENDING (continues the PC090OJ native-replacement program; verification
of completion, not new infrastructure).

**Open/Closed issues touched:** OPEN-024 (evidence added: frontend object-RAM path now proven dead
output). No issue status changed by this analysis task.

**CONFIRMED/STRONG contradiction detected:** NONE. (The 2026-08-15 `Cody_pc090oj_remaining_
compatibility_audit.md` lists several families as possibly-live, but it pre-dates Builds 0286–0296;
per task rules, current source/artifacts are authority. Each flagged family is re-verified below as
retired/native — a supersession of that older list, not a contradiction of a CONFIRMED finding.)

---

## Phase 1 — Current-Tree Census

Addresses are `runtime_genesis_pc` unless labeled. `object_ram` = `pc090oj_object_ram`
(`genesis WRAM 0x00FF6F9A`, 256 × 8 bytes). Scene id `0x00FF78B0`; value space `{0,1,2}` (derived
from `genesistan_pc080sn_tileset_id`, tileset 3 → scene 1; `genesistan_scene_a0_ranges` has 3
entries) — scene 1 = gameplay, scene 0 = title/attract-frontend with stage substates, scene 2 =
third asset scene (not reached in attract).

### 1.1 Core compatibility symbols

| Symbol | Class | Reachability | Evidence |
|---|---|---|---|
| `pc090oj_object_ram` | **A (dead as compatibility store)** | Written only by zero/park fills; read only by the dead scan/decoder | §1.2, §2, Phase 4 |
| `.Lnq_frontend_object_scan` | **A** | Live *call site* (`pc090oj_native_emit_pass`, scene 0 stage≠0 / scene 2) but its object-RAM loop always sees code 0 | §2, Phase 4 |
| `.Lpc090oj_decode_record` | **A** | Called only by the scan; returns not-drawable for every record (all codes 0) | §2, Phase 4 |
| `.Lpc090oj_emit_slot` | **B (dead)** | Sole caller `.Lpc090oj_clear_slot`, which has **zero** callers | grep: 1 caller / 0 callers |
| `.Lpc090oj_clear_slot` | **B (dead)** | **No** callers | grep: 0 callers |

### 1.2 Adapters / fills / helpers

| Piece | Class | Reachability | Evidence |
|---|---|---|---|
| `.Lpc090oj_mirror_write_word_a1_d0` | **B (dead)** | Called only inside `hook_target_3b930` (itself uncalled) | grep: 4 callers all in 3b930 |
| `.Lpc090oj_mirror_write_byte_a1_d0` | **B (dead)** | **No** callers | grep: 0 callers |
| `genesistan_pc090oj_hook_target_3b930` (generic copier) | **B (dead)** | Arcade callers `0x3B902` (body-replaced inert) + `0x3B8B0` (`rts;nop`) | remap #1926/#1251 notes |
| `.Lpc090oj_mode2_project_p1_hud` | **B (dead)** | Sole caller (scan line 2172) is gated `scene==GAMEPLAY`, but gameplay routes to `.Lnq_gameplay` and never enters the scan | dispatch lines 1492–1495 |
| `genesistan_hook_3ad44_dispatch` D-range branch (`0xD00000..0xD00800`) | **A (zero-fill only)** | Live; 3 arcade callers (`0x03AD5C/6E/82`) fill slots 76..79 with `d0=0` | §3 |
| object-RAM boot/init clear (`0x3af4c/0x3af72` → hooks `0x72c9c`/`0x72d80`) | **A (zero-fill only)** | Writes zeros/park; no content | disasm 0x3af4c–0x3af84 |
| `genesistan_pc090oj_ctrl_set_0/1`, `pc090oj_ctrl_shadow` | **A (dead after decode removed)** | Shadow read only by `.Lpc090oj_decode_record` flip logic | source 838–867, 2519 |
| diagnostic counters `pc090oj_producer_write_count/oob_count`, `candidate/decoded/drawable/blank_skipped/code_zero_skipped_count`, `pc090oj_mirror_dirty` | **A/B (dead diagnostics)** | Written/updated only by dead adapters and the scan | source 2944–2960 |
| `pc090oj_emitted_count`, `pc090oj_sat_frame_ready`, `pc090oj_sat_dirty` | **C (native, keep)** | Written by the native finalizer `.Lnq_done_scan` (title/gameplay/frontend) | source 2150–2152 |

### 1.3 Native sprite infrastructure with historical `pc090oj_*` names (Category C — RETAIN)

`staged_sprite_sat` / `staged_sprite_sat_b`, `pc090oj_sat_bank` / `pc090oj_sat_front`,
`sprite_tile_resident_code`, `pc090oj_tile_dma_worklist` / `pc090oj_tile_dma_count`,
`pc090oj_cell_used`, `pc090oj_sat_nibble` / `pc090oj_sat_force_line`, `.Lnative_pal_fixup`,
`.Lnq_emit_entry`, `.Lnq_gameplay`, `.Lnq_project_p1_hud`, `native_frontend_hud_emit`, `.Lnq_title`,
`.Lnq_transient_items_emit`, `.Lnq_gameover_emit`, `vdp_prepare_sprites`, `vdp_commit_sprites`,
`genesistan_pc090oj_dma_self_test`. These are the native Genesis SAT pipeline (double buffers,
semantic queues, residency, tile DMA, palette fixup, finalizer, VBlank commit). They contain **no**
PC090OJ hardware/record dependency; the name is historical only. Rename is optional and NOT
required for zero-debt.

---

## Phase 2 — Producer Ownership Proof

For every former PC090OJ producer family, in the **current** tree:

| Family (records) | Semantic arcade owner | Old PC090OJ tail | Current native owner | Old tail reachable | Can write drawable object_ram | Evidence |
|---|---|---|---|---|---|---|
| Frontend HUD digits/labels (0..45) | `0x3B8B0/0x3B902/0x3B926/0x3B802` frontend HUD builders | pack records → object_ram | `native_frontend_hud_emit` (all frontend scenes) | NO (`rts`/body-replaced) | **NO** | remap #1240/#1246/#1251/#1926; hooks `rts` |
| Title sprites | title glyph/score decision | object_ram records | `.Lnq_title` (native, scene 0 stage 0) | n/a | **NO** | source 1512–1529 |
| Status row (30..43) | `0x05A098` status state | `.Lpc090oj_emit_slot` loop | `genesistan_pc090oj_hook_status_sprite_5a098` (native persistent queue) | NO | **NO** | source 1080–1292; CLOSED-019; `producer_write_count=0` |
| Player auxiliary (44..47) | `0x054810` table/state + player X/Y | 4 PC090OJ records | `genesistan_pc090oj_hook_player_aux_native_54810` (native FRONT_EFFECT lane) | NO | **NO** | source 991–; remap #440 |
| Copied player constructor (0..3) | copied `FUN_00052AA2` | raw `0xD00000` record tail | deleted | NO (constructor deleted) | **NO** | remap #237/#242 “Delete… raw tail”; disasm: no `0xD00000` store in 0x52Axx |
| Transient item/effect (56..67) | `0x05607C/0x056114/0x056440` | descriptor + virtual records | `.Lnq_transient_items_emit` (native, from `transient_items_source_ptr`) | NO | **NO** | source 1548–1584; Build 0286/0296 |
| Transient clear (68..71) | `0x056440` lifecycle | park records | native lifecycle (`hook_zero_fill_56440` clears active flag) | NO | **NO** | source 1076 |
| Slot-init (72..75) | `0x054052` setup | 4 blank records | retired (`rts`) | NO | **NO** | source 984 `rts` |
| Priority/init (76..79) | `0x03AD84` priority/flip | 4 priority records | native lane ORDER; D-range fill = `d0=0` | fill live, zeros only | **NO** | source 965 comment; §3 |
| Credit-area (17..21) | `0x3B902` credit builder | records 17..21 | `native_frontend_hud_emit` | NO (`rts`) | **NO** | source 292 `rts` |
| Records 9..16 clear | `0x59F5E` | park via `0xD00048` | retired (`rts`) | NO | **NO** | source 830 `rts` |
| GAME OVER (83..90) | `FUN_0005A502` (no-human attract row) | records 83..90 → object_ram `+0x298/+0x2B0` | `.Lnq_gameover_emit` (native; reads `a5@0x34`/`a5@0x200`) | NO (`clr.l d0; rts` at entry, Build 0288; `0x5A51E/0x5A554` redirects now dead) | **NO** | remap #1995/#1323/#1329 |

**Key result:** No reachable producer places a nonzero code word into `pc090oj_object_ram`. The
only writers are (a) dead helpers with no live callers, and (b) zero/park fills (D-range clear +
boot clear). Because `.Lpc090oj_decode_record`'s drawability test requires `code & 0x1FFF != 0` and
`< 0x1000` and not in `pc090oj_blank_code_bitset`, a permanently-zero-code table can never yield a
drawable record — **in any scene**, whether or not attract reaches it.

---

## Phase 3 — 0x03AD44 D-Range Semantic Audit (PC090OJ branch only)

`genesistan_hook_3ad44_dispatch` is polymorphic. The **C-range branches** (`0x00C00000..0x00C10000`,
BG/FG name/scroll fills) are PC080SN — **out of scope, unchanged.** The **PC090OJ/D-range branch**
(`0x00D00000..0x00D00800`) is a long-fill of `object_ram`:

- Remaining D-targeting callers: `arcade_pc 0x03AD5C, 0x03AD6E, 0x03AD82` (the `0x03AD84`
  priority/init clear), destinations slots 76..79. They pass `d0 = 0` (blank / not-drawable).
- Semantic event: the arcade's "clear/reset the sprite priority-init records" maintenance step.
- What it writes: zero words into `object_ram`.
- Consumer of the cleared/filled records: only `.Lnq_frontend_object_scan` / `.Lpc090oj_decode_
  record`, which reject code 0.
- Remaining semantic output once native sprite ownership is established: **NONE.** It clears records
  that no drawable path consumes.

Conclusion: the PC090OJ/D-range branch's only remaining role is clearing obsolete virtual PC090OJ
records. Removable with the object-RAM path (route `0xD00000..0xD00800` to the dispatch's finish/no-op),
leaving the C-range PC080SN branches untouched.

---

## Phase 4 — Runtime Backstop (GENESIS NTSC MAME)

Tool: `tools/mame/scripts/pc090oj_deadcode_audit.lua` (durable, reusable) — per-frame census of all
256 `object_ram` records + diagnostic counters + scan-path/stage/item-page exercise proof. Symbol
addresses verified against Build 0296 `apps/rastan-direct/out/symbol.txt`
(`object_ram=0xFF6F9A`, `scene_id=0xFF78B0`, `producer_write_count=0xFF77BA`,
`drawable_count=0xFF77AE`, `emitted_count=0xFF77B0`, `transient_items_active=0xFF68B4`). Drawable-
candidate logic mirrors `.Lpc090oj_decode_record` (`code & 0x1FFF != 0 && < 0x1000`).

Run: USA/NTSC `genesis` machine, Build 0296 ROM, `-seconds_to_run 240`, headless.
Evidence: `build/mame/home/pc090oj_deadcode_audit/summary.txt` + `run.log`.

```
total_frames=14382
scenes: scene0 frames 1..2637 (stage 0x0000 then 0x0100); scene1 frames 2638..14382
frontend_object_scan_path_frames = 2207   (object-RAM scan path actually exercised)
scan_path_max_drawable_candidate_codes = 0
item_page_active_frames = 2002            (item/treasure page reached)
scene_gt1_frames = 0                      (scene 2 not reached in attract)
GLOBAL_MAX_DRAWABLE_CANDIDATE_CODES = 0
max_producer_write_count = 0
max_producer_oob_count = 0
max_drawable_count = 0
max_emitted_count = 72  (native HUD/sprites only)
VERDICT = PASS_OBJECT_RAM_ALWAYS_EMPTY
```

Interpretation (separated from observation): the scan path was genuinely exercised (2207 frames,
scene 0 stage 0x0100) and the item page was reached (2002 frames), yet no `object_ram` record was
ever drawable and the decoder produced zero drawable output. `max_raw_nonzero_records=240` reflects
parked/blank records (nonzero Y/X, code 0) from the zero/park fills — consistent with, not
counter to, an empty-content table.

**Coverage caveat (honest):** attract reached scenes 0 (incl. the scan path + item page) and 1
only; scene 2 and coin-gated states (human GAME OVER screen, high-score name entry, throne/PUSH-
BUTTON, ROUND/READY as distinct producers) were not dynamically visited. Per the task's allowance
("rare frontend states may be proven statically if writer ownership is conclusive"), these are
covered by the Phase 2 static writer-ownership proof, which is **scene-independent**: no reachable
writer stores a nonzero code into `object_ram` in any scene. The runtime sweep is a backstop
confirming the static result for the reached states, not the sole proof.

---

## Classification Summary (A/B/C/D/E)

- **A — LIVE PC090OJ compatibility (dead output; remove in teardown):** `pc090oj_object_ram`,
  `.Lnq_frontend_object_scan` object-RAM loop, `.Lpc090oj_decode_record`, `0x03AD44` D-range branch,
  object-RAM boot clear (`0x3af4c`→`0x72c9c/0x72d80`), `pc090oj_ctrl_shadow`+`ctrl_set_0/1`, dead
  diagnostic counters/aliases.
- **B — DEAD/unreachable PC090OJ compatibility (remove):** `.Lpc090oj_emit_slot`,
  `.Lpc090oj_clear_slot`, `.Lpc090oj_mirror_write_word/byte_a1_d0`, `hook_target_3b930` body,
  `.Lpc090oj_mode2_project_p1_hud`.
- **C — native Genesis functionality with historical `pc090oj_*` name (RETAIN):** §1.3 list.
- **D — original arcade semantic state (RETAIN):** arcade producers' upstream state (`a5@…`),
  scene/stage/game-flow cells.
- **E — PC080SN/unrelated (LEAVE ALONE):** `0x03AD44` C-range branches, tilemap/scroll/plane hooks,
  the item-page PC080SN text problem (OPEN, unchanged).

---

## Recommended Teardown Boundary (for the NEXT, implementation task — NOT done here)

1. Redirect the frontend dispatch: in `pc090oj_native_emit_pass`, route scene 0 stage≠0 and scene 2
   to a **native-only** path mirroring `.Lnq_title` plus `.Lnq_transient_items_emit`, ending at the
   shared `.Lnq_done_scan` finalizer (SAT setup → `native_frontend_hud_emit` → transient items →
   terminator/`emitted_count`/`sat_frame_ready`/`sat_dirty`). No object-RAM loop.
2. Delete the object-RAM scan tail (`.Lnep_loop`..`.Lnep_store`), `.Lpc090oj_decode_record`,
   `.Lpc090oj_emit_slot`, `.Lpc090oj_clear_slot`, `.Lpc090oj_mirror_write_word/byte_a1_d0`,
   `hook_target_3b930` body, `.Lpc090oj_mode2_project_p1_hud`, `pc090oj_object_ram` BSS.
3. Remove the `0x03AD44` D-range PC090OJ branch (route `0xD00000..0xD00800` → finish); keep every
   C-range PC080SN branch byte-for-byte.
4. Retire the object-RAM boot clear (`0x3af4c/0x3af72` + helpers `0x72c9c`/`0x72d80`) — verify these
   helpers are not shared with the native group-builder `0x72978`/`0x728a0` (they are separate; the
   group builder writes native buffers `0xFF68CA..0xFF6C82`, not object_ram — confirm during teardown).
5. Retire dead diagnostics/aliases and the now-dead remap entries (`0x3B930`, `0x3B902`, `0x3B926`,
   `0x5A51E`/`0x5A554` dead redirects, `pc090oj_ctrl` capture entries) once their sole consumers are
   gone. Keep `pc090oj_emitted_count`/`sat_frame_ready`/`sat_dirty` (native finalizer).
6. Retain all §1.3 native infrastructure.
7. Rebuild through the Makefile-owned flow; re-run this audit (expect `GLOBAL_MAX_DRAWABLE_
   CANDIDATE_CODES` still 0 and no scan symbol linked); regression-validate frontend + gameplay
   sprites; produce exactly one numbered candidate only after GATE_PASS.

---

## Final Statement (required)

**A) PC090OJ semantic conversion is complete. The remaining compatibility path is dead output and
can be removed.**

No remaining live PC090OJ producers. No reachable path of `arcade → PC090OJ record → virtual object
RAM → scanner/decoder → SAT` exists for gameplay OR frontend that can produce visible output.

## Remaining live PC090OJ producers

NONE.
