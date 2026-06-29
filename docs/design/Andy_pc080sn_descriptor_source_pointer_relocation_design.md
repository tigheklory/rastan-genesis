# Andy — PC080SN Descriptor Source Pointer Relocation (Design Only)

**Author:** Andy
**Date:** 2026-06-29
**Baseline:** Build 0116 (`dist/rastan-direct/rastan_direct_video_test_build_0116.bin`, SHA256 `94f157ecc296cb9e9c2521ec6c3d462671c59dde75d2fe42274508795a4eb30f`). rastan-direct.
**Scope:** DESIGN only. No source/spec/tool/Makefile/ROM/build/bookmark/diagnostic/implementation; no runtime probing (existing evidence only). Output: this doc + one AGENTS_LOG entry. **All pointer conversion via `build/rastan-direct/address_map.json` only — no arithmetic offset as the conversion method.** Labels: **[OBS]** verified this task; **[CODY]** Cody evidence; **[INT]** interpretation. Separable from KF-036 (fixed Build 0116) and KF-038 (out of scope).

---

## Phase 0 — Baseline

**Classification:** EXTENDING (descriptor source-pointer relocation; OPEN-023; OPEN-016/KF-028 runtime-pointer-relocation class). **Contradiction:** NONE. **Root (Cody, re-verified):** Build 0116's KF-036 work-RAM rebase is correct — the table at Genesis-WRAM `0x00FF1000` now holds the 16 arcade source-pointer VALUES (`0x0001691C..0x0003725C`). But the rebuild dereferences them as **raw arcade addresses**; in the Genesis ROM the copied arcade content is shifted per its arcade-copy segment mapping, so the descriptor bytes read are wrong (`0x55B1A` reads ROM[0x1691C], not ROM[0x16B1C]).

---

## 1. The 16 source pointers — JSON-derived mapping table [OBS]

Each table value at Genesis-WRAM `0x00FF1000..0x00FF103F` is an arcade ROM/source pointer, resolved **individually** through `address_map.json` (looked up by arcade value in the arcade range of each segment):

| arcade source ptr (Genesis-WRAM value) | JSON segment kind | arcade_start..arcade_end_excl | genesis_start | **JSON-mapped genesis_rom_offset** |
|---|---|---|---|---|
| 0x0001691C | arcade_copy | 0x000F08..0x03A00C | 0x001108 | **0x00016B1C** |
| 0x00018BDC | arcade_copy | 0x000F08..0x03A00C | 0x001108 | **0x00018DDC** |
| 0x0001AE9C | arcade_copy | 0x000F08..0x03A00C | 0x001108 | **0x0001B09C** |
| 0x0001D15C | arcade_copy | 0x000F08..0x03A00C | 0x001108 | **0x0001D35C** |
| 0x0001F41C | arcade_copy | 0x000F08..0x03A00C | 0x001108 | **0x0001F61C** |
| 0x000216DC | arcade_copy | 0x000F08..0x03A00C | 0x001108 | **0x000218DC** |
| 0x0002399C | arcade_copy | 0x000F08..0x03A00C | 0x001108 | **0x00023B9C** |
| 0x00025C5C | arcade_copy | 0x000F08..0x03A00C | 0x001108 | **0x00025E5C** |
| 0x00027F1C | arcade_copy | 0x000F08..0x03A00C | 0x001108 | **0x0002811C** |
| 0x0002A1DC | arcade_copy | 0x000F08..0x03A00C | 0x001108 | **0x0002A3DC** |
| 0x0002C49C | arcade_copy | 0x000F08..0x03A00C | 0x001108 | **0x0002C69C** |
| 0x0002E75C | arcade_copy | 0x000F08..0x03A00C | 0x001108 | **0x0002E95C** |
| 0x00030A1C | arcade_copy | 0x000F08..0x03A00C | 0x001108 | **0x00030C1C** |
| 0x00032CDC | arcade_copy | 0x000F08..0x03A00C | 0x001108 | **0x00032EDC** |
| 0x00034F9C | arcade_copy | 0x000F08..0x03A00C | 0x001108 | **0x0003519C** |
| 0x0003725C | arcade_copy | 0x000F08..0x03A00C | 0x001108 | **0x0003745C** |

JSON-mapped target = `genesis_start + (ptr − arcade_start)`. **Descriptor-byte verification** [OBS]: for sampled pointers, arcade `maincpu.bin[ptr]` equals Build 0116 ROM[mapped] and differs from ROM[raw] — e.g. `arcade[0x1691C]=000320FC00031000` = `ROM[0x16B1C]` ✓ (raw `ROM[0x1691C]=2024…` ✗); same for `0x18BDC→0x18DDC`, `0x2399C→0x23B9C`, `0x3725C→0x3745C`. The JSON-mapped locations hold the correct arcade descriptor bytes.

---

## 2. Coverage — ALL 16 in ONE JSON segment [OBS]

All 16 pointers resolve through the **single** arcade_copy segment `arcade [0x000F08, 0x03A00C) → genesis_start 0x001108`. None is uncovered (no STOP). The min/max pointers `0x1691C`/`0x3725C` both lie inside `[0x000F08, 0x03A00C)`. **Consequence only:** this segment's delta is `genesis_start − arcade_start = 0x001108 − 0x000F08 = 0x200`, so all 16 map at `+0x200`. **This +0x200 is reported as a consequence of the single covering segment, NOT used as the conversion method** — the conversion is the JSON segment mapping; the implementation (§5) guards to the segment's arcade range so a pointer that ever leaves it is not blindly +0x200'd.

---

## 3. Role of the existing `#0x200` in the routine [OBS]

The routine has `moveal #0x200,%a4` at `runtime_genesis_pc 0x00055B22`, used to build the **rebuilt** pointer (`a4 = 0x200 + d1`, where `d1 = %a4@(2)` = the descriptor's second word), stored to `0x00FF1040`.

- **Arcade-native vs translation:** arcade `maincpu` at the corresponding `0x00055922` is `moveal #0,%a4` (base **0**); Build 0116 is `moveal #0x200,%a4` (base **0x200**). So the **postpatcher relocated the second-word rebuilt pointer by +0x200** (the same segment delta) — it is a **translation relocation**, not arcade-native.
- **Scope of the existing relocation:** it applies **only** to the rebuilt pointer derived from `%a4@(2)`. It does **NOT** relocate the **initial source dereference** `move.w %a4@,%a2@+` at `0x00055B1A`, where `%a4` holds the raw source pointer loaded from the table (`0x00055B18 moveal %a0@,%a4`). [CODY-confirmed: the initial dereference still reads wrong bytes.]
- **Why the postpatcher missed the source dereference:** the source pointer is **runtime-built** (loaded from the WRAM table at runtime), not a static immediate/operand. The postpatcher relocates static immediates/operands (it relocated the `#0x200` second-word base), but cannot reach a pointer that only exists at runtime in WRAM — the **OPEN-016 / KF-028 runtime-pointer-relocation class**.
- **Keep or change:** **KEEP `0x55B22`'s `#0x200` unchanged** — it correctly relocates the second-word pointer for this (single) segment. The fix ADDS the missing **source-pointer** relocation. (Note [INT]: the `#0x200` is segment-specific; it is correct here because every second-word target is in the same `[0xF08,0x3A00C)` segment. If a descriptor's second word ever pointed into a different segment, that `#0x200` would also be wrong — flagged, but not in evidence here.)

---

## 4. Where relocation should occur — **at dereference (function-level rebuild hook)** [INT]

**Chosen: relocate `%a4` at the source dereference**, via a function-level hook that reimplements the rebuild loop. Rationale:
- **Stateless / idempotent across the `0x55AC6` mutation.** The upstream mutator `0x00055AC6` does `addql #4` to each table entry every pass — the table holds **raw arcade pointers that advance +4/pass**. Relocating at dereference (read `a4`=raw, apply segment delta, deref) is correct **every** pass regardless of mutation. (Relocating the table in place would double-apply across passes — rejected.)
- **No populator dependency.** Relocating at population would require finding the (A5-relative) populator and changing it; relocating at dereference does not. It also leaves the table holding **raw arcade pointers**, so the mutator and any other consumer keep arcade-native values.
- **Isolated.** Only the rebuild (`0x55B04`) dereferences the source pointers (the mutator `0x55AC6` only advances values, doesn't dereference). So one hook covers the whole defect.

Rejected alternatives: **relocate-at-population** (unfound populator + idempotency/other-consumer risk); **in-place table pre-pass** (not idempotent across the +4 mutation); **per-dereference in-line `adda`** (no byte room — the loop is tight 2-byte instructions).

---

## 5. Patch shape for Cody [INT]

**The pointers are RUNTIME-BUILT (in the WRAM table), not static immediates → static rebasing is N/A; a runtime relocation hook is required.**

**Function-level rebuild hook.** Patch the rebuild entry and let a genesis_only hook reimplement the rebuild with JSON-derived source relocation:
- **Entry patch:** overwrite `0x00055B04` (`moveal #0x00FF1000,a0`, 6B) + `0x00055B0A` (`moveal #0x00FF1040,a1`, first 2B) — i.e. 8 bytes `0x55B04..0x55B0B` — with `jsr genesistan_hook_pc080sn_descriptor_rebuild` (6B) + `rts` (2B). The caller `0x505DC bsr 0x55B04` → `jsr hook` → hook `rts` → `0x55B0A`? No — see note. Byte-neutral 8→8; the rebuild body `0x55B0C..0x55B46` becomes dead.
  - *Return detail:* place the `rts` at `0x55B0A`–`0x55B0B`; the hook's `rts` returns to `0x55B0A` (the patched `rts`) → returns to the caller `0x505E0`. (Standard patched-entry shape: `jsr hook; rts`.)
- **Hook behavior (reproduces `0x55B04..0x55B46` exactly, plus the source relocation):**
  - `a0 = 0x00FF1000`, `a1 = 0x00FF1040`, `a2 = 0x00FF1080`, `d0 = 16`.
  - loop: `a4 = (a0)` (raw arcade source ptr).
    - **source relocation (JSON-derived segment delta, guarded):** if `a4 ∈ [0x00000F08, 0x0003A00C)` → `a4 += 0x200`; else **fail-loud trap/report** (a pointer outside the single covering segment would need a different delta — surface it, do not blindly +0x200). The `0x200` is this segment's `genesis_start − arcade_start`, applied only within the segment's arcade range.
    - `move.w (a4),(a2)+` — descriptor first word (now from the relocated source).
    - `d1 = (a4+2)` — second word; `rebuilt = 0x200 + d1` (unchanged from the existing routine; same segment delta); `(a1)+ = rebuilt`.
    - `a0 += 4`; `d0 -= 1`; loop.
  - post-loop output: reproduce `0x55B38..0x55B44` (`a4 = %a5@(4294)`; `d0 = (a4)`; `0x00FF10A8 = d0`); `rts`.
- **Register discipline:** the hook keeps loop state (`a0/a1/a2/d0/a4/d1`) in its own registers; it calls no staging helper, so no cross-call preservation needed beyond a conservative `movem` save/restore for the caller. The caller `0x505DC` re-establishes its state after the `bsr`; the original rebuild clobbers `d0/d1/a0/a1/a2/a4`, so the hook may too.
- **Byte / opcode_replace impact:** entry patch byte-neutral (8→8); `opcode_replace` **+1** (new patched_site `0x00055B04` / `arc 0x00055904`); `total_genesis_bytes_covered` **+ hook size** (genesis_only growth, est. ~60–90 bytes; relocation genesis_only-internal). Any other delta = STOP.

*(Smaller alternative considered: a hook that only relocates the source and re-enters the loop — rejected, no byte room to insert a call in the 2-byte-instruction loop. Function-level is the byte-feasible shape.)*

---

## 6. Out of scope (enforced)

- NO KF-038 item-scroll/staging-size; NO `bg_fill` row remap.
- NO PC080SN render-loop HW-write routing.
- NO sprites/HUD/Window; NO skip/bypass; NO fake/invented descriptor data.
- NO blanket/arithmetic relocation (the +0x200 is the JSON segment delta, applied only within the JSON-validated segment range, with a fail-loud guard); NO broad ROM/RAM mirror.

---

## 7. Validation plan for Cody

- Build canonical gate passes; new build/SHA.
- The 16 descriptor source reads use **JSON-derived Genesis addresses** (raw `a4 + segment-delta`, guarded to `[0xF08,0x3A00C)`), not raw arcade pointers.
- **Descriptor bytes read after the fix match original arcade for ALL 16 entries** — first word (`%a4@`) AND second word (`%a4@(2)`) — i.e. the relocated source reads `ROM[mapped]` (e.g. `0x16B1C`), matching `maincpu[0x1691C]=000320FC…`.
- Outputs at Genesis-WRAM `0x00FF1040` (rebuilt ptrs) / `0x00FF1080` (copied words) / `0x00FF10A8` (output) match original-arcade rebuild behavior.
- The `0x55B1A` crash remains gone (it is now inside the hook's relocated, valid dereference).
- Item page MAY still render incorrectly (KF-038) but must not crash.
- No title/story/high-score regression.
- Any new later crash is acceptable progress — report exact PC/state.
- Document the exact `opcode_replace` delta (+1) and the genesis_only growth; `total_genesis_bytes_covered` otherwise accounted.

---

## 8. Risks / open questions

| Item | Note |
|---|---|
| Advancing pointers leave the segment | The `0x55AC6` `+4`/pass mutation advances the raw pointers; while they stay in `[0xF08,0x3A00C)` the +0x200 delta is correct; the fail-loud guard traps any escape (a different segment would need a different delta). The whole descriptor stream is within this single segment, so escape is not expected. |
| Second-word `#0x200` (0x55B22) | Kept; correct for this segment. Same segment-specific caveat as the source; not in evidence as wrong. |
| Populator not changed | Intentional — relocate-at-dereference leaves the table raw (mutation-safe; other consumers see arcade-native values). |
| Runtime-built pointers | Confirmed not static immediates → hook required (OPEN-016/KF-028 class), not static rebasing. |
| Reimplementation fidelity | Hook reproduces `0x55B04..0x55B46` 1:1 plus the source relocation; validation diffs all 16 first/second words + the three outputs. |

## Open / Closed Issues Impact

- Open issues touched: **OPEN-023** (item-page descriptor rebuild — source-pointer relocation designed via JSON-derived per-pointer mapping; not closed pending implementation + the 16-entry byte-match validation), OPEN-016 / KF-028 class (runtime-built pointer not relocated by the static postpatcher — this is a new instance), KF-036 (fixed, predecessor), OPEN-001 (context). KF-038 / OPEN-015 not touched.
- New issues opened: NONE.
- Issues closed: NONE.
- Intentionally deferred: implementation; KF-038; any downstream crash exposed by progress; the populator (intentionally untouched).

## STOP triggered

NO (all 16 source pointers resolve through one JSON segment with verified descriptor-byte matches; the fix is a JSON-derived, segment-guarded runtime relocation at dereference — no invented data, no blanket arithmetic).
