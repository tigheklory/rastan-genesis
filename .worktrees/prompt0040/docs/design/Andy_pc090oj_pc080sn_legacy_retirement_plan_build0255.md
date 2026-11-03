# PC090OJ / PC080SN Legacy Retirement Architecture Plan — Build 0255

**Agent:** Andy · **Type:** architecture review / retirement-boundary plan · **No source/spec/ROM/build/counter change.**
**Baseline:** Build 0255 (user-verified). **Authority:** `RULES.md`, `ARCHITECTURE.md`, `PROMPT_TEMPLATE.md`,
`PC080SN_PC090OJ_NATIVE_REPLACEMENT_POLICY.md`, Cody reports 0251–0255, source
(`pc090oj_hooks.s`, `tilemap_hooks.s`, `vdp_comm.s`, `boot/boot.s`), `out/symbol.txt`,
`address_map.json`, patch manifest, `build/genesis_postpatch.disasm.txt`.

## 0. Baseline verification + compliance

- **Build 0255 VERIFIED:** counter `255`; ROM `dist/rastan-direct/rastan_direct_video_test_build_0255.bin`;
  SHA-256 `edfd03534b1766309de105a1dad00671d0ac73eb3ca0fa5dfe7cc3859b378673`; size `1592224` — all match.
- **`Cody_known_findings_sync_build0255.md`:** absent. Per task instruction this is **not** a STOP — Build 0255
  finding-sync is pending (Codex usage exhausted). Noted for the next sync pass.
- **Compliance:** analysis only; arcade owns execution; Genesis remains helper/opcode-replacement (RULES §1–4,
  §11). No chip re-emulation is proposed; every retirement cuts dead compatibility, never revives a chip
  renderer.

---

## 1. PHASE 1 — PC090OJ inventory by ownership

| Symbol / routine | File | Runtime / addr | Xref evidence | Gameplay | Frontend | Delete now? | Convert first? | Classification | Next action |
|---|---|---|---|:--:|:--:|:--:|:--:|---|---|
| `native_sprite_emit` | pc090oj_hooks.s | `0x72CC2` | 13 refs (producers) | YES | — | NO | — | **ACTIVE_GAMEPLAY_NATIVE** | keep |
| `native_sprite_frame_begin` | pc090oj_hooks.s | `0x72C96` | called from 41f5e hook | YES | — | NO | — | **ACTIVE_GAMEPLAY_NATIVE** | keep (Build 0251 lifecycle) |
| `native_stage_player_blocks_41f5e` | pc090oj_hooks.s | `0x72DA6` | player-body producer | YES | — | NO | — | **ACTIVE_GAMEPLAY_NATIVE** | keep (PLAYER_BODY) |
| `pc090oj_native_emit_pass` (gameplay finalizer) | pc090oj_hooks.s | `0x73590` | scene-1 finalizer | YES | — | NO | — | **ACTIVE_GAMEPLAY_NATIVE** | keep |
| semantic lane queues / counts | pc090oj_hooks.s | (BSS) | fed by `native_sprite_emit` | YES | — | NO | — | **ACTIVE_GAMEPLAY_NATIVE** | keep |
| `genesistan_pc090oj_hook_target_41dae` | pc090oj_hooks.s | `0x72C38` | patched dispatcher | YES | — | NO | — | **ACTIVE_GAMEPLAY_NATIVE** | keep |
| `genesistan_pc090oj_hook_target_41f5e` | pc090oj_hooks.s | `0x72C62` | patched player-body hook | YES | — | NO | — | **ACTIVE_GAMEPLAY_NATIVE** | keep |
| `genesistan_pc090oj_hook_target_45dfa` | pc090oj_hooks.s | `0x72C7C` | patched dispatcher | YES | — | NO | — | **ACTIVE_GAMEPLAY_NATIVE** | keep |
| `pc090oj_legacy_emit_pass` | pc090oj_hooks.s | `0x739A4` | reached when scene≠1 | NO | YES | NO | — | **ACTIVE_FRONTEND_COMPATIBILITY** | keep until frontend converts |
| `pc090oj_object_ram` | pc090oj_hooks.s | `0xFFAF9A` | 13 code sites (native block2c8/record46 **and** legacy scan) | YES | YES | NO | — | **RETAIN_DO_NOT_TOUCH** (KF-069: arcade persistent object state, not a mirror) | keep |
| D00298/D002B0 raw writer family (`0x05A51E`/`0x05A554`) | remap spec | → `object_ram+0x298/+0x2B0` | Build 0254 remap; frontend/attract | NO | YES | NO | **YES** | **ACTIVE_UNCONVERTED_COMPATIBILITY** | convert frontend producer, then retire redirect + record |
| `record_to_slot` | pc090oj_hooks.s | `0xFFB820` (aliased) | **0 code uses** (only `.global` + label; boot `.extern` unused) | NO | NO | **YES** (symbol only) | — | **DEAD_UNREACHABLE_SAFE_CANDIDATE** | remove dead label/decl (see §3b) |
| `represented_records` | pc090oj_hooks.s | `0xFFB820` (aliased) | **0 code uses** | NO | NO | **YES** (symbol only) | — | **DEAD_UNREACHABLE_SAFE_CANDIDATE** | remove dead label/decl |
| `waiting_records` | pc090oj_hooks.s | `0xFFB820` (aliased) | **0 code uses** | NO | NO | **YES** (symbol only) | — | **DEAD_UNREACHABLE_SAFE_CANDIDATE** | remove dead label/decl |
| `pc090oj_candidate_bitset` | pc090oj_hooks.s | `0xFFB820` (aliased) | **0 code uses**; boot `.extern` unused | NO | NO | **YES** (symbol only) | — | **DEAD_UNREACHABLE_SAFE_CANDIDATE** | remove dead label/decl + unused boot extern |
| `staged_sprite_descriptor_table` | pc090oj_hooks.s | `0xFFB820` (aliased) | used @`pc090oj_hooks.s:1259` | ? | ? | NO | — | **UNKNOWN_REQUIRES_CODY_AUDIT** (live label at the same 4-byte spot as the dead ones) | keep; audit its consumer |
| `worklist_entry_for_slot` | pc090oj_hooks.s | `0xFFB820` (aliased) | used @`:2432` | ? | ? | NO | — | **UNKNOWN_REQUIRES_CODY_AUDIT** | keep; audit |
| `staged_sprite_sat` / residency cache / tile-DMA worklist | pc090oj_hooks.s | (BSS/VRAM job) | native SAT infra | YES | YES | NO | — | **RENAME_LATER_NOT_DELETE** (native infra carrying chip name) | keep; rename in a later naming pass |

**Note on the aliased BSS block (`0xFFB820`):** `pc090oj_candidate_bitset`, `record_to_slot`,
`represented_records`, `waiting_records`, `staged_sprite_descriptor_table`, `used_sat_slots`,
`worklist_entry_for_slot` are **all labels at the same address** followed by `.space 4`. The four first-named
are dead symbol aliases; the block itself is still referenced through the live labels, so **only the dead
symbol names/declarations are removable, not the allocation.**

---

## 2. PHASE 2 — PC080SN inventory by ownership

| Symbol / routine | File | Xref evidence | Gameplay | Frontend | Delete now? | Convert first? | Classification | Next action |
|---|---|---|:--:|:--:|:--:|:--:|---|---|
| native Plane A selector-0/1/2 producers | tilemap_hooks.s | active gameplay producers | YES | — | NO | — | **ACTIVE_GAMEPLAY_NATIVE** | keep (do-not-touch) |
| Plane B gameplay hook | tilemap_hooks.s | active | YES | — | NO | — | **ACTIVE_GAMEPLAY_NATIVE** | keep |
| `vdp_commit_bg_strips_if_dirty` | vdp_comm.s | live VBlank BG DMA | YES | — | NO | — | **ACTIVE_GAMEPLAY_NATIVE** | keep |
| `vdp_commit_fg_narrow_strips` | vdp_comm.s | live VBlank FG DMA | YES | — | NO | — | **ACTIVE_GAMEPLAY_NATIVE** | keep |
| `fg_narrow_desc_table` / `_count` / `_pending_rows` | tilemap_hooks.s/vdp_comm.s | feed `commit_fg_narrow_strips` | YES | — | NO | — | **ACTIVE_GAMEPLAY_NATIVE** (native strip data, chip-ish name) | keep; rename later |
| `genesistan_hook_cwindow_clear` | tilemap_hooks.s | frontend C-window clear | NO | YES | NO | — | **ACTIVE_FRONTEND_COMPATIBILITY** | keep until frontend converts |
| `genesistan_hook_pc080sn_bg/fg_scroll_fill` | tilemap_hooks.s | scroll fill hooks | mixed | mixed | NO | — | **UNKNOWN_REQUIRES_CODY_AUDIT** | classify gameplay vs frontend before touching |
| `genesistan_hook_tilemap_bg_fill_tall` | tilemap_hooks.s:1505 | **pure tall producer** (writes `staged_bg_tall_buffer`+`bg_tall_dirty` only) | see note | see note | NO (Slice 2) | — | **ACTIVE_UNCONVERTED_COMPATIBILITY** (wasted writes) | Slice 2 after native-producer audit |
| `genesistan_hook_tilemap_fg_fill_tall` | tilemap_hooks.s:1593 | pure tall producer; **called inside the native FG producer** (`.Lfgc_row_loop`, `:1084`) | YES (as a call inside Plane A producer) | via C-window clear `:3412` | NO (Slice 2) | — | **ACTIVE_UNCONVERTED_COMPATIBILITY** (wasted writes; entangled with native FG producer) | Slice 2; **do-not-touch until audited** |
| `staged_bg_tall_buffer` (4096w = 8 KB) | vdp_comm.s:583 | written by `bg_fill_tall`; **no reader** (projector is a stub) | — | — | NO (Slice 2) | — | **DEAD DATA (write-only)** | Slice 2 |
| `staged_fg_tall_buffer` (4096w = 8 KB) | vdp_comm.s:587 | written by `fg_fill_tall`+C-window clear; **no reader** | — | — | NO (Slice 2) | — | **DEAD DATA (write-only)** ("row preservation" is never consumed) | Slice 2 |
| `bg_tall_dirty` / `fg_tall_dirty` | vdp_comm.s | set by producers; read only by the now-stub projector | — | — | NO (Slice 2) | — | **DEAD (set, never acted on)** | Slice 2 |
| `bg_tall_project_base` / `fg_tall_project_base` | vdp_comm.s:545/552 | **only boot-cleared; never read** (projector body gone in 0253) | NO | NO | **YES** | — | **DEAD_UNREACHABLE_SAFE_CANDIDATE** | **Slice 1 (recommended, §3)** |
| `vdp_project_bg_tall_if_dirty` / `vdp_project_fg_tall_if_dirty` | vdp_comm.s:244/250 | **exported no-op RTS stubs** (bodies removed 0253); called from `_vblank_service` non-gameplay path only | NO | NO (no-op) | **YES** | — | **DEAD_UNREACHABLE_SAFE_CANDIDATE** (consumer removed) | **Slice 1 (recommended, §3)** |

**Consumer-gone proof:** Build 0253 removed both tall-projector bodies (now exported RTS stubs) and Build 0253
user verification is **PASS for frontend/title/story/high-score** — so **no scene renders from the tall
buffers**. The tall buffers are therefore write-only dead data, and the `*_tall_project_base` globals + the
projector stubs are fully dead. The only complication is that the FG tall producer is invoked **inside the
native FG (Plane A) gameplay producer** — a do-not-touch region — so the producer/buffer removal is deferred to
Slice 2 behind an explicit native-producer audit.

---

## 3. PHASE 3 — Safest next removal target

### Recommended next Cody task: **Slice 1 — retire the dead PC080SN tall-projector interface (consumer side only)**

This is Phase-3 **priority 1 (dead/unreachable with proof)** applied to the projector consumer side, with **zero
producer or native-renderer entanglement.**

**Exact scope (symbols/files):**
1. `apps/rastan-direct/src/vdp_comm.s` — delete the two exported no-op stubs `vdp_project_bg_tall_if_dirty` and
   `vdp_project_fg_tall_if_dirty`, and their two `.global` decls.
2. `apps/rastan-direct/src/vdp_comm.s` `_vblank_service` — remove the two dead `bsr vdp_project_*_tall_if_dirty`
   calls (lines ~198/200). After removal the non-gameplay branch is byte-for-byte the gameplay branch
   (`bsr vdp_commit_bg_strips_if_dirty`), so the Build 0252 scene-1 gate becomes redundant and may be collapsed
   to unconditional `bsr vdp_commit_bg_strips_if_dirty` / `bsr vdp_commit_fg_narrow_strips`. **Preserve the exact
   surviving commit call order** (`commit_bg_strips` then, after the tail, `commit_fg_narrow_strips`).
3. `apps/rastan-direct/src/vdp_comm.s` — delete the dead globals `bg_tall_project_base` / `fg_tall_project_base`
   + `.global` decls.
4. `apps/rastan-direct/src/boot/boot.s` — delete the two dead boot clears `clr.w bg_tall_project_base` /
   `clr.w fg_tall_project_base` (lines 207/210).
5. Update the canonical-coverage constants in `tools/translation/postpatch_startup_rom.py` +
   `verify_canonical_rom.py` by the measured byte delta (as 0252/0253 did); opcode_replace count stays `218`.

**Why safe:** projector bodies already removed (0253) and frontend verified; `*_tall_project_base` is only
boot-cleared and never read; the removed `bsr` targets are no-ops; the surviving `commit_bg_strips` /
`commit_fg_narrow_strips` calls are untouched. **No producer, no tall buffer, no native Plane A/B producer, no
frontend renderer, no PC090OJ path is touched.**

**Measurable / reversible:** negative byte delta in the address map (Genesis-only dead code + 4 bytes BSS);
`GATE_PASS`; MAME smoke unchanged; a single `git revert` restores it.

**STOP conditions for Slice 1:** STOP if (a) any reader of `*_tall_project_base` is found; (b) collapsing the
scene gate would change the gameplay commit order or drop a commit; (c) either projector symbol has an xref
outside `_vblank_service`; (d) canonical coverage cannot be reconciled to a pure dead-code delta.

### Slice 2 (documented follow-up, NOT next): retire the tall buffers + dirty flags + fill_tall producer writes
Requires first proving the FG tall producer call at `tilemap_hooks.s:1084` inside the native FG (Plane A)
producer contributes nothing consumed (its 64-row "preservation" is never read), and that `bg_fill_tall` /
the C-window tall clear (`:3412`) have no live consumer. Only then remove `staged_bg/fg_tall_buffer`,
`bg/fg_tall_dirty`, the producer writes, the `bsr fg_fill_tall`, and the boot inits — freeing ~16 KB WRAM.
**Deferred because it touches a do-not-touch native producer; needs its own audit build.**

### §3b Alternative micro-target (even safer, lower value): PC090OJ dead symbol cleanup
Delete the four dead symbol aliases `record_to_slot` / `represented_records` / `waiting_records` /
`pc090oj_candidate_bitset` (`.global` + label lines) and the unused `boot.s` `.extern`s. The `0xFFB820`
allocation stays (live aliases remain). Zero behavior change. Suitable to bundle only if the team wants a pure
symbol-hygiene pass; otherwise keep Slice 1 focused.

### Rejected as "next" (too large / risky right now)
- Removing `pc090oj_object_ram` — **rejected** (KF-069: arcade persistent object state, live).
- Bypassing `pc090oj_legacy_emit_pass` globally — **rejected** (frontend still needs it).
- Full tall-buffer + producer removal in one build — **rejected as "next"** (touches native FG producer).
- Frontend PC090OJ/PC080SN native conversion — **rejected as "next"** (large; unlocks deletion but is a
  multi-build effort, not a safe single step).

---

## 4. PHASE 4 — Do-NOT-touch list for the next implementation

Hard-protected (any change here fails the task):
- Build 0251 **PLAYER_BODY** lifecycle + `native_sprite_frame_begin` ordering (`0x72C96`, called in the 41f5e hook).
- `pc090oj_native_emit_pass` gameplay finalizer + **semantic priority lane ordering**.
- `native_sprite_emit`, the native lane queues, `native_stage_player_blocks_41f5e`.
- The three native dispatch hooks (`41dae` `0x72C38`, `41f5e` `0x72C62`, `45dfa` `0x72C7C`).
- `pc090oj_object_ram` (KF-069 arcade object state) and `pc090oj_legacy_emit_pass` (frontend compat).
- Build 0254 **D00298/D002B0 remaps** (frontend/attract compatibility).
- Build 0255 demo-input remap + relocated 9-entry script table (`0x052C1C`→`0x052E1C`, selector rebase
  `0x0010C118`→`0x00FF0118`); `rastan_direct_update_inputs`.
- `vdp_commit_bg_strips_if_dirty`, `vdp_commit_fg_narrow_strips`, and their descriptor data.
- Native Plane A/B gameplay producers (incl. the FG producer loop that calls `fg_fill_tall` at `:1084`).
- Palette/CRAM reassert paths (`vdp_reassert_bank36_line0` etc.), collision, rope/reset, audio,
  frontend/title/story/high-score rendering.

---

## 5. Answers to the 12 objective questions

1. **PC090OJ active in gameplay:** the native pipeline — `native_sprite_emit`, `native_sprite_frame_begin`,
   `native_stage_player_blocks_41f5e`, lane queues, `pc090oj_native_emit_pass`, the three dispatch hooks; plus
   `pc090oj_object_ram` as arcade object state.
2. **PC090OJ active only in frontend/non-gameplay:** `pc090oj_legacy_emit_pass`; the frontend producers routed
   through `pc090oj_object_ram`; the Build 0254 D00298/D002B0 redirected writer.
3. **PC090OJ dead/unreachable, safe candidate:** the 4 dead symbol aliases (`record_to_slot`,
   `represented_records`, `waiting_records`, `pc090oj_candidate_bitset`) + unused boot externs.
4. **PC090OJ not dead but convert-before-remove:** the D00298/D002B0 compatibility writer + `object_ram`-based
   frontend producers (convert frontend to native SAT, then retire the object table + redirects).
5. **PC090OJ-named but actually native infra → rename later:** `pc090oj_native_emit_pass`, `staged_sprite_sat`,
   the residency cache, tile-DMA worklist, `native_sprite_*` (these are native SAT infra, not chip code).
6. **PC080SN active in gameplay:** native Plane A/B producers, `vdp_commit_bg_strips_if_dirty`,
   `vdp_commit_fg_narrow_strips`, `fg_narrow_desc_*`.
7. **PC080SN active only in frontend:** `genesistan_hook_cwindow_clear` and the C-window/text staging path.
8. **PC080SN dead/unreachable, safe candidate:** the tall-projector **consumer side** — `vdp_project_bg/fg_tall_if_dirty`
   no-op stubs + call sites, and `bg/fg_tall_project_base` globals (Slice 1). The tall **buffers**/dirty flags
   are dead data but producer-entangled (Slice 2).
9. **PC080SN not dead but convert-before-remove:** the `fill_tall` producers (dead output but invoked inside the
   native FG producer / frontend C-window clear — neutralize the wasted writes only after the native-producer
   audit); the frontend C-window/text path (convert to native Plane A/B before removing).
10. **PC080SN-named but actually native infra → rename later:** `fg_narrow_desc_table/_count/_pending_rows`,
    `vdp_commit_bg_strips_if_dirty`, `vdp_commit_fg_narrow_strips` (native strip infra).
11. **Safest next Cody task:** Slice 1 (§3) — retire the dead tall-projector interface.
12. **Explicitly do NOT touch next:** everything in §4 (native gameplay pipeline, object_ram, legacy frontend
    emit, 0254/0255 fixes, strip commits, native producers, palette/collision/rope/reset/audio/frontend).

## 6. Open/Closed/KNOWN_FINDINGS impact

- **Open issues touched:** OPEN-017 / OPEN-024-adjacent native rendering cleanup. No issue opened or closed by
  this plan.
- **KNOWN_FINDINGS:** Option A — no new finding to index; respects KF-068 (native replacement), KF-069
  (object_ram is arcade state), KF-071/072 (native plane ownership). Build 0255 finding sync remains pending.
- **STOP:** NOT triggered — baseline verified, ownership classified from source/xrefs/reports, the recommended
  target is proven dead and does not touch active gameplay/frontend/native paths.
