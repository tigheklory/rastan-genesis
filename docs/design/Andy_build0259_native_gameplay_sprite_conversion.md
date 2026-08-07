> **SUPERSEDED (Build 0260).** Build 0259 is NOT ACCEPTED. It used a PC090OJ-format eight-byte scratch
> tuple bridge (`native_expand_scratch`) that ran the relocated arcade record-expander (0x3D254) and decoded
> its records back into lanes — a pack-then-decode path. It is superseded by Build 0260's direct-native
> default-expander emitter (no expander call, no records, no scratch). The historical body below is preserved
> unchanged. See `Andy_build0260_direct_native_gameplay_sprite_conversion.md`.

# Build 0259 — Restore Omitted Gameplay Sprite Producers (engine→native-lane bridge)

**Agent:** Andy · **Type:** source-changing gameplay sprite conversion · **Build produced: YES (0259).**
**STOP: NO.** User authorization: Tighe assigned Andy as the implementer.

## 1. Baseline

Build **0258** current (preserved, SHA `6aa273c9…9b3e`). Counter 258 → **259**. Pre-edit coverage `0x18492C`,
opcode-replace `221`.

## 2. What this build actually does (and a correction to the accepted premise)

### 2.1 Premise correction (verified against the remap + source)

The task's contract listed **0x3C4D2 / 0x3C550 / 0x3C586 / 0x3C636 / 0x3C6DC / 0x3C75C / 0x3C7A4 / 0x3C830**
plus **0x3C950** as "eight specialized gameplay sprite handlers + default expander" to convert. Verified
against `specs/rastan_direct_remap.json` and the source tree, these nine addresses are a **dual-use 16×16-piece
expander**, and their *primary* copies are **already converted** to Genesis **C-window / FG-text staging hooks**:

- every one is remapped to `genesistan_hook_text_writer_3cXXXX`, and every one of those hooks lives in
  **`tilemap_hooks.s`** (BG/FG plane = text/C-window), not `pc090oj_hooks.s` (sprites);
- the remap notes label them "text writer handler (script opcode 0xN0) … route to Genesis FG staging";
- the sibling glyph routine `0x3C322` does `ori.w #0x30,d1` (ASCII '0' digit synthesis) — this cluster is the
  **score/text/C-window renderer**.

The **gameplay sprite** path uses the *pristine relocated copy* of the same expander at **`0x3D254`**
(= `0x3D054 + 0x200`, the whole-maincpu copy), reached from the master builds `0x41DAE` / `0x45DFA`. So the
handlers are not "text vs sprite"; the same expander serves both, and only the text role was previously
converted. **No conversion of the primary text-hook copies was attempted here — doing so would corrupt score/
text/C-window rendering.** (The earlier `Andy_build0249…` contract analyzed this expander as the *sprite* engine
and is corrected by the banner now at its top.)

### 2.2 The real gap this build fixes

`native_stage_dispatch_41dae` / `_45dfa` already ran the pristine expander (`jsr 0x0003D254`) for the enemy /
middle / effect / player-front groups — **but with `A1` pointing at arcade PC090OJ RAM `0x00D001C8..0x00D00460`,
which is UNMAPPED on Genesis.** Every expanded piece was written to nowhere and silently dropped; only the player
block (`0x11B2`/`0x0170`, staged by `native_stage_player_blocks_41f5e`) reached the SAT. The manifest note on
`hook_target_41dae` confirms the enemy groups (arcade records 57/96/140/46) were **deferred**.

**Fix:** `.Lnative_emit_actor_common` now runs the same authoritative expander into a **private WRAM scratch
band**, then appends each expanded 16×16 piece into the caller-selected **native semantic lane** via
`native_sprite_emit`. The expander remains the artwork/attribute/position owner (exactly the provenance
conclusion: the semantics belong to the arcade actor + mapping, not the chip record); the bridge only relocates
its output from unmapped `0xD0` into the native lanes → `staged_sprite_sat` → existing VBlank DMA.

## 3. Source changes (only `apps/rastan-direct/src/pc090oj_hooks.s` + two canonical constants)

1. **`.Lnative_emit_actor_common` rewritten** (was: set d0/d6/d7, `jsr 0x3D254` into unmapped `A1`, discard).
   Now: guard `a4@0`/`a4@1` active; clamp piece budget `d2 ≤ NATIVE_EXP_MAX`; clear `budget×8` scratch bytes;
   `jsr 0x0003D254` into `native_expand_scratch`; loop the budget reading `(attr,Y,code,X)` → `native_sprite_emit`
   into `native_sprite_lane`. Whole body is `movem`-bracketed so the caller's `a4`/`d5`/`a1` are preserved.
2. **`NATIVE_EXP_MAX = 32`** added (max per-actor piece budget is 20; 32 is a safe margin).
3. **`native_expand_scratch: .space (NATIVE_EXP_MAX*8)`** added to `.bss`.
4. **Canonical coverage `0x18492C → 0x184978`** (+0x4C = 76 code bytes) in `postpatch_startup_rom.py` +
   `verify_canonical_rom.py`. Opcode count unchanged (no remap/spec change).

The proven engine-call ABI (`jsr 0x0003D254`) is identical to the two existing in-file call sites
(`.Lpc090oj_stage_record46_validated`, `pc090oj_stage_block2c8`).

## 4. Dispatcher / group coverage (both gameplay dispatchers)

Selected by mode word `a5@0x2A2` in `genesistan_pc090oj_hook_target_41dae`.

| Dispatcher | Group (a5 offset) | Lane | Budget | Now emits natively |
|---|---|---|---|---|
| 0x41DAE | 0x0508 | PLAYER_FRONT | 13×2 | YES (was discarded) |
| 0x41DAE | 0x05C8 | MIDDLE | 4×6 | YES (was discarded) |
| 0x41DAE | 0x02C8 | BACK_ENEMY | 10/19 | YES (was discarded) |
| 0x41DAE | 0x0748 | FRONT_EFFECT | 1×11 | YES (was discarded) |
| 0x45DFA | 0x05C8 | BACK_ENEMY | 10/20 | YES (was discarded) |
| 0x45DFA | 0x0748 | FRONT_EFFECT | 6 | YES (was discarded) |
| 0x45DFA | 0x08C8 | MIDDLE | 4×5 | YES (was discarded) |
| 0x41F5E (unchanged) | 0x11B2 / 0x0170 | PLAYER_BODY / PLAYER_FRONT | 18 / 4 | already native |

The per-actor gates in the dispatch loops (`a4@5`, `a4@3`, `a4@0x36`) are preserved; `native_sprite_emit` drops
blank/code-0/`Y=0x180` pieces and applies the KF-067 BACK_ENEMY −8 Y bias. Priority order (HUD → FRONT_EFFECT →
PLAYER_FRONT → MIDDLE → PLAYER_BODY → BACK_ENEMY) is the existing finalizer order, unchanged.

## 5. Queue bounds

HUD 9, FRONT_EFFECT 36, PLAYER_FRONT 30, MIDDLE 24, PLAYER_BODY 20, BACK_ENEMY 99 (all pre-existing); scratch
`NATIVE_EXP_MAX=32`. Overflow is deterministic: `native_sprite_emit` refuses appends at the lane bound (no
adjacent-lane or SAT corruption); the finalizer caps at `NATIVE_SAT_MAX=80`.

## 6. Gameplay PC090OJ status after this build

Scene-1 gameplay finalizer (`.Lnq_gameplay`) reads **only** the native lanes; it does not scan
`pc090oj_object_ram`. The restored producers append to lanes, not to object RAM. **Remaining, honestly stated:**
the bridge still invokes the arcade expander and captures its output through a **transient 8-byte-tuple scratch**
(`native_expand_scratch`). That scratch is not `pc090oj_object_ram`, has no `0xD00000` translation, no `Y=0x180`
park record, is cleared every call and never rescanned — but it *is* still a record-shaped expansion buffer. The
FINAL contract's "no 8-byte record packing at all / from-scratch native handler reimplementation" is therefore
**not yet met**; eliminating the expander call + scratch (reimplementing the dual-use expander natively from the
five family tables) is the next build. This build restores the missing sprites; it does not retire the expander.

## 7. Validation

- **GATE_PASS.** Counter **258 → 259**. ROM `dist/rastan-direct/rastan_direct_video_test_build_0259.bin`;
  SHA-256 `cd6a55ad6779c16aef834e869cdc58bc355ba206f2f4aa99fa4a7e6247f56607`; size **1591672**. Prior ROMs
  0250–0258 preserved (0258 SHA re-verified identical).
- Opcode-replace **221 → 221**; coverage `0x18492C → 0x184978`; no remap gaps/overlaps introduced (spec
  untouched; symbolic references self-adjusted the BSS shift, e.g. `native_expand_scratch`/`pc090oj_object_ram`).
- Build 0254 D00298/D002B0 remap, Build 0255 demo-input fix, Build 0256/0257 PC080SN removals, Build 0258
  finalizer ownership: all preserved (frontend `.Lnq_frontend_object_scan` intact; gameplay branch native-only).
- **MAME 30s smoke** `states/traces/rastan_direct_video_test_build_0259_mame_30s_20260805_101952/`: 1798 frames,
  ~996% speed, **0 unmapped / fatal / error / illegal** in the exec trace; 47 242 VDP port writes (rendering
  live); boot guard PASS.

### 7.1 Honest limits of the automated validation (no overclaim)

- The 30s smoke exercises boot + frontend only; **it does not reach interactive Stage-1 gameplay**
  (`arcade_stage` watch: 0 changes). It proves the ROM boots, runs, and does not fault with the new code linked
  and reachable — it does **not** visually confirm the restored enemy/middle/effect sprites or their positions.
- **Synthetic specialized-handler comparison:** because the bridge **reuses the arcade expander verbatim** (it
  does not reimplement the eight case bodies), the per-piece X/Y/code/attribute/valid output is the arcade
  semantic calculation *by construction* — the same instructions on the same actor/mapping inputs — with the
  only change being the destination pointer (unmapped `0xD0` → mapped scratch → lane). No independent synthetic
  harness was built; the equivalence argument is structural (verbatim engine reuse), not a separate test run.
- **User visual verification required:** Stage-1 gameplay — Rastan, lizard men, bats, axe/item, PLAYER_FRONT,
  MIDDLE, FRONT_EFFECT, BACK_ENEMY should now appear; specifically confirm the `0x0508`→PLAYER_FRONT group does
  **not** double-render the player (distinct source block from `0x11B2`, expected safe, but unverified at
  runtime), and that no lane overflows visibly clip enemies.

## 8. Issues / findings

- Open issues touched: OPEN-024-adjacent PC090OJ→native gameplay migration. New: none. Closed: none.
- Corrected: `Andy_build0249_shared_native_sprite_emitter_contract.md` mis-identified the dual-use text/sprite
  expander as the gameplay sprite engine (correction banner added).
- Deferred (next build): reimplement the dual-use expander natively from the five family tables (0x3D09E/0x4771C/
  0x3F0CE/0x40004/0x4002C) to remove the `jsr 0x3D254` + scratch entirely and reach the record-free FINAL
  contract; runtime gameplay capture to confirm the restored groups; frontend PC090OJ conversion.
- **Andy follow-up recommended: YES** — after user gameplay verification, author the from-scratch native
  expander build.

## 9. STOP status

**STOP: NO.** A real gameplay sprite gap (all non-player producers discarded to unmapped `0xD0`) was found and
fixed; the omitted BACK_ENEMY / MIDDLE / PLAYER_FRONT / FRONT_EFFECT groups now emit into native semantic lanes
through the proven expander, GATE_PASS, MAME-clean, all prior fixes preserved. The from-scratch native expander
(record-free FINAL contract) remains as the next build; this build makes the substantive forward progress and
ships a real ROM.
