# Build 0258 — PC090OJ Frontend / Non-Gameplay Legacy Retirement (STOP)

**Agent:** Andy · **Type:** PC090OJ frontend legacy audit · **Build produced: NO.** **STOP: YES** — no meaningful
single-build PC090OJ removal is safe yet; the exact blocker and the next build-ready conversion target are below.
No production source, spec, ROM, or counter changed. User authorization to build was given; the STOP is on
evidence/safety, not delegation.

## 1. Baseline (verified)

Build **0257** current: ROM `dist/rastan-direct/rastan_direct_video_test_build_0257.bin`, SHA-256
`6aa273c9f1337b9d4e16a39a90ae5ee50debbf2eeb475ea3e0d0f92577e79b3e`, size `1591596`, counter `257`. Preserved.
Coverage `0x18492C`, opcode-replace `221`. `pc090oj_object_ram` = `0xFF6F92` (2 KB). `pc090oj_legacy_emit_pass`
= `0x73730`; `pc090oj_native_emit_pass` = `0x7331C`; `vdp_prepare_sprites` = `0x739DA`;
`pc090oj_workram_block_sprites` = `0x727A8`, `_41f5e` = `0x7279A`.

## 2. User priority

Meaningful remaining PC090OJ legacy removal (not a tiny alias/one-screen/PC080SN task).

## 3. Files/reports read

Governance (`RULES.md`, `ARCHITECTURE.md`, `PROMPT_TEMPLATE.md`, `KNOWN_FINDINGS.md`, `OPEN_ISSUES.md`,
`CLOSED_ISSUES.md`, `AGENTS_LOG.md`); Cody 0251/0254/0255 + Andy 0249/0255/0256/0257 design docs; source
(`pc090oj_hooks.s`, `tilemap_hooks.s`, `vdp_comm.s`, `boot/boot.s`); `out/symbol.txt`, `address_map.json`,
patch manifest, `specs/rastan_direct_remap.json`.

## 4. The two sprite finalizers are fundamentally different (decisive)

VBlank → `vdp_prepare_sprites` → `pc090oj_native_emit_pass`, which branches on scene:

```asm
pc090oj_native_emit_pass:
    cmpi.b  #PC090OJ_SCENE_GAMEPLAY_ID, genesistan_current_scene_id
    beq.s   .Lnq_gameplay
    bra     pc090oj_legacy_emit_pass        ; scene != 1 (frontend/non-gameplay)
.Lnq_gameplay:  ...native semantic lanes...
```

- **Gameplay (`.Lnq_gameplay`)**: concatenates the **native semantic lanes** —
  `native_queue_hud/front_effect/player_front/middle/player_body/back_enemy` via `.Lnq_emit_lane`. It does
  **not** read `pc090oj_object_ram`.
- **Frontend (`legacy_emit_pass`)**: `.Lnep_loop` scans **`pc090oj_object_ram`** records 0..255 → decode →
  residency → SAT.

They are **not interchangeable**: the frontend populates `object_ram` (never the native lanes), so the native
lane path would emit nothing for frontend. `legacy_emit_pass` is therefore the **required active** frontend
renderer. **Runtime proof:** it fires ~1×/frame in the frontend (scene 0) — 259 calls by F300, 502 by F550
(`states/traces/build0258_pc090oj_frontend_audit_20260804/legacy.txt`).

## 5. All-scene PC090OJ ownership

| Scene / mode | Finalizer | Reads object_ram | Producers | Path class |
|---|---|:--:|---|---|
| Normal gameplay (scene 1) | `native_emit_pass` (lanes) | NO | `native_sprite_emit` via `native_stage_dispatch_41dae/45dfa`, `native_stage_player_blocks_41f5e` | ACTIVE_GAMEPLAY_NATIVE |
| Title / story / high-score / insert-coin / Push-Player-Button / attract / transitions (scene ≠ 1) | `legacy_emit_pass` (object_ram scan) | **YES** | `pc090oj_workram_block_sprites`/`_41f5e` (block copy `a5+0x11B2`/`+0x170` → object_ram) + arcade-hooked HUD/status/score writers (`0x3B802`, `0x5A098`, `0x3B902`, `0x59F5E`, `0x41DAE/45DFA` non-gameplay) | ACTIVE_FRONTEND_COMPATIBILITY |

`object_ram` is additionally **arcade persistent object state** (KF-069), written by the arcade program as its
own object table in all scenes — independent of rendering.

## 6. PC090OJ component inventory

| Component | Addr | Gameplay | Frontend | Delete now | Convert first | Class |
|---|---|:--:|:--:|:--:|:--:|---|
| `pc090oj_native_emit_pass` + native lanes/counts | 0x7331C | YES | — | NO | — | ACTIVE_GAMEPLAY_NATIVE |
| `native_sprite_emit` / `native_sprite_frame_begin` / `native_stage_player_blocks_41f5e` / PLAYER_BODY | — | YES | — | NO | — | ACTIVE_GAMEPLAY_NATIVE |
| `pc090oj_legacy_emit_pass` | 0x73730 | NO | **YES (fires every frame)** | NO | YES | ACTIVE_FRONTEND_COMPATIBILITY |
| `pc090oj_object_ram` | 0xFF6F92 | writes (arcade state) | read+write | NO | — | RETAIN (arcade state + frontend render source, KF-069) |
| `pc090oj_workram_block_sprites` / `_41f5e` | 0x727A8/0x7279A | — | **YES** | NO | YES | ACTIVE_FRONTEND_COMPATIBILITY |
| HUD/status/score arcade hooks (`0x3B802/5A098/3B902/59F5E`, `41dae/45dfa` non-gameplay) | patched sites | — | YES | NO | YES | ACTIVE_FRONTEND_COMPATIBILITY |
| D00298/D002B0 writer family (`0x05A51E/54`) | remap→object_ram+0x298/0x2B0 | — | YES (attract) | NO | YES | ACTIVE_UNCONVERTED_COMPATIBILITY |
| `vdp_prepare_sprites` | 0x739DA | YES | YES | NO | — | RETAIN (VBlank finalizer entry) |
| `record_to_slot`/`represented_records`/`waiting_records`/`pc090oj_candidate_bitset` | 0xFF7818 (aliased) | NO | NO | YES (symbols only) | — | DEAD_UNREACHABLE (excluded by task as non-meaningful) |
| `staged_sprite_sat`/residency cache/tile-DMA worklist | — | YES | YES | NO | — | RENAME_LATER_NATIVE_INFRA |

**Dead-function scan:** every "0-caller" PC090OJ symbol is either a **patched-site arcade hook**
(`patched_refs=1`, invoked by arcade via opcode-replace, not by Genesis `bsr`) or a **data symbol** (native
lane queues, `lea`-referenced). **No dead PC090OJ function/subsystem exists.** Only the four aliases are truly
dead — excluded by the task as non-meaningful.

## 7. Targets A–D evaluation

- **A — remove `pc090oj_legacy_emit_pass`:** UNSAFE. It is the active frontend renderer (fires every non-gameplay
  frame). All frontend/attract screens depend on it.
- **B — convert a `pc090oj_workram_block_sprites*` family:** UNSAFE/LARGE in one build. The frontend has **many**
  producers writing `object_ram` (the two block-copy families **and** the arcade-hooked HUD/status/score writers
  + D00298 family). Converting one family leaves the frontend needing **both** `legacy_emit_pass` (for the
  unconverted producers, via `object_ram`) **and** the native lanes (for the converted one) — a fragile hybrid
  finalizer, and the block copy's input is PC090OJ-format records, so a clean native conversion needs the
  upstream per-actor semantic work (a record-decoder is the anti-pattern). High regression risk to
  user-verified frontend screens.
- **C — convert the D00298/D002B0 writer family:** same hybrid + record-decoder problem; it is one of several
  `object_ram` producers, not separable in one safe build.
- **D — remove a dead scanner/decoder subsystem:** NONE exists (§6) — `legacy_emit_pass` is active; only the four
  aliases are dead.

## 8. STOP — exact blocker + next build-ready target

**Blocker:** the remaining PC090OJ legacy is the **entire active frontend/non-gameplay rendering pipeline** —
`workram_block_sprites*` + the arcade HUD/status/score hooks + the D00298 family all write `pc090oj_object_ram`,
which `legacy_emit_pass` scans → SAT every non-gameplay frame. `object_ram` is also required arcade state.
Nothing here is dead; converting it is the **frontend equivalent of the entire Build 0249–0257 gameplay native
conversion** — a multi-build, per-producer-family effort. Any single-build removal/conversion of these active
components would break user-verified frontend screens (title/story/high-score/attract), so it is **not a safe
single Build 0258.**

**Next build-ready conversion target (recommended sequence, one build each):**
1. **Build a merged non-gameplay finalizer first:** make `native_emit_pass` handle scene ≠ 1 by emitting **both**
   the native lanes **and** the existing `object_ram` scan (concatenated, priority-correct), then delete the
   separate `legacy_emit_pass` symbol. This is a refactor that changes no rendering (object_ram scan still runs)
   but gives the frontend a lane path to grow into. **Prove SAT output byte-identical for a frontend frame.**
2. Then convert the frontend producers **one family per build** to `native_sprite_emit` into a frontend lane,
   each build **excluding** that family's `object_ram` record band from the merged scan (exactly the pattern the
   gameplay conversion used). Suggested order by isolation: score-digit `0x3B802` → status `0x5A098` → the
   `workram_block_sprites` blocks → the D00298 family.
3. When the last frontend producer is native, the `object_ram` scan is empty for frontend → retire the scan and
   the frontend `object_ram` render dependency (keeping `object_ram` only as arcade state until the arcade
   itself stops needing it).

Each step is independently testable against the frontend screens and preserves the do-not-touch gameplay/native
lane pipeline. Step 1 is the smallest safe, meaningful next build.

## 9. Preservation (nothing changed this task)

Gameplay native pipeline, `native_emit_pass` lanes, PLAYER_BODY, Build 0254 D00298/D002B0 remaps, Build 0255
demo-input fix, Build 0256/0257 PC080SN removals — all untouched (analysis only).

## 10. Issues / findings

- Open issues touched: OPEN-024-adjacent PC090OJ native migration (frontend). New: none. Closed: none.
- Deferred: the entire frontend PC090OJ native conversion (multi-build, §8); the four dead aliases (non-meaningful
  alone); item-description screen; Push-Player-Button coin-up residue.
- KNOWN_FINDINGS: Option A — no new finding; **not edited** (Build 0255 sync pending).
- **Andy follow-up recommended: YES** — author the Step-1 merged-finalizer implementation spec (byte-identical
  frontend proof) as the next build-ready task.

## 11. STOP status

**STOP: YES.** No meaningful PC090OJ component is safe to remove/convert in a single build: `legacy_emit_pass`
and `object_ram` are the active frontend renderer/source (runtime-proven), all frontend producers write
`object_ram` (not native lanes), and no dead subsystem exists. The frontend conversion is a multi-build effort;
the exact blocker and a concrete build-ready next-step sequence are in §8. Design doc + AGENTS_LOG delivered; no
build produced; counter stays 257.
