# Andy — Dispatcher Map Analysis & Interception-Level Determination (Build 0033)

**Status:** ANALYSIS COMPLETE. **Interception level: PER-HANDLER.** No implementation.
**Build Context:** Build 0033, `rastan-direct`.

---

## 1. Dispatcher Entry Point

| Label | Value |
|-------|-------|
| `arcade_pc` (entry) | **`0x03C902`** |
| `genesis_rom_offset` (from `build/rastan-direct/address_map.json` `arcade_copy` segment `[0x03B0A4, 0x03EF28) → [0x03B2A4, 0x03F128)` with `identity_offset=512`) | **`0x03CB02`** |
| Entry instruction | `moveb %a0@, %d3` — reads first script byte from `(A0)` **without** post-increment. Source: `build/maincpu.disasm.txt:76269`. |

### Input register contract at dispatcher entry

From `build/maincpu.disasm.txt:76269–76288` and the handlers' per-entry
behavior:

| Register | Role | Consumed by |
|----------|------|-------------|
| `A0` | Script pointer. First byte at `(A0)` is the opcode. Each handler dereferences `*(A0+2)` to obtain its script-data pointer. | Dispatcher read-byte; handlers `movea.l %a0@(2), %a0` as their first instruction. |
| `A1` | Destination pointer in `HW_ADDRESS/PC080SN/FG_TILEMAP` (expected `[0xC08000, 0xC0C000)`). Each handler writes via `A1@(2)` / `A1@(6)` and advances by `#8` per iteration. | All handler bodies. |
| `A4` | Script-state block. Fields read: `A4@(11).b` (char count / mode byte), `A4@(22).w` (attribute base), `A4@(24).w` (per-scene offset), `A4@(26).w` (tile base), plus handler-specific offsets `A4@(1).b`, `A4@(3).b`, `A4@(27).b`, `A4@(30).w`. | All handler bodies. |
| `A5` | Arcade workram base (`0xFF0000`). A handful of handlers (0x03C636, default path) read `A5@(280).b`, `A5@(318).w` for game-state conditional branches. | Handlers 0x03C636 and dispatcher default path. |
| `D3` | Clobbered by dispatcher for opcode-match work; inner subs read `D3` for terminator-check semantics. | Dispatcher + inner subs. |
| `D6, D7` | Used by dispatcher default path (fall-through from `0x03C950+`). | Dispatcher default path. |

---

## 2. Complete Routing Table

From `build/maincpu.disasm.txt:76269–76288`. All `genesis_rom_offset`
values obtained by looking up the enclosing `arcade_copy` segment in
`address_map.json` and reading its recorded `identity_offset=512` — no
independent arithmetic.

| Script-opcode top nibble | Match site `arcade_pc` | Handler `arcade_pc` | Handler `genesis_rom_offset` | Hooked in Build 0033? |
|:-----:|----------------------:|---------------------:|-----------------------------:|:------:|
| `0x10` | `0x03C90C` (`beqw`) | `0x03C830` | `0x03CA30` | **NO** |
| `0x20` | `0x03C914` (`beqw`) | `0x03C7A4` | `0x03C9A4` | **NO** |
| `0x30` | `0x03C91C` (`beqw`) | `0x03C6DC` | `0x03C8DC` | **NO** |
| `0x50` | `0x03C924` (`beqw`) | `0x03C4D2` | `0x03C6D2` | **YES** (`genesistan_hook_text_writer_3c4d2`) |
| `0x60` | `0x03C92C` (`beqw`) | `0x03C4D2` | `0x03C6D2` | **YES** (same hook, shared handler) |
| `0x90` | `0x03C934` (`beqw`) | `0x03C75C` | `0x03C95C` | **NO** |
| `0xA0` | `0x03C93C` (`beqw`) | `0x03C550` | `0x03C750` | **NO** |
| `0xB0` | `0x03C944` (`beqw`) | `0x03C636` | `0x03C836` | **NO** |
| `0xC0` | `0x03C94C` (`beqw`) | `0x03C586` | `0x03C786` | **NO** |
| *fall-through (no top-nibble match)* | `0x03C950` (body continues in dispatcher) | `0x03C950` (in-dispatcher code) | `0x03CB50` | **NO** |

**Total sibling branches: 10** (9 explicit top-nibble cases = 8 distinct
handlers since `0x50/0x60` share, plus the 1 fall-through default code
path inside the dispatcher body). Of these, **1 handler (0x03C4D2) is
hooked**; **8 distinct sibling code paths are unhooked**:
`0x03C830, 0x03C7A4, 0x03C6DC, 0x03C75C, 0x03C550, 0x03C636, 0x03C586`,
and the dispatcher fall-through at `0x03C950`.

No branch target could not be resolved via `address_map.json`.

---

## 3. Firing Handlers in Build 0033 Attract Mode

### 3.1 Trace evidence examined

- `states/traces/rastan_direct_video_test_build_0033_mame_30s_20260415_125313/genesis_exec_summary.txt`:
  `fg_cwindow_live count=8 first_frame=170 last_frame=384 first_pc=03C52A last_pc=03C518 first_addr=C09EA0 last_addr=C09EA6 first_data=0000 last_data=0037`.
- `states/traces/rastan_direct_video_test_build_0033_mame_30s_20260415_125313/genesis_exec_trace.log`:
  distinct `pc=...` samples include `0x03C52A, 0x000202, 0x070100, 0x000010`
  — no per-frame, per-write-event PC stream at handler resolution.
- `helper_5b512_rts@000200 count=0` from the same summary confirms that
  the original 0x03C4D2 body's inner subroutine
  (`arcade_pc: 0x03C516..0x03C54E` — relocated copy at
  `genesis_rom_offset: 0x03C716..0x03C74E`) is not executing.

### 3.2 What the trace can prove

- Writes to `HW_ADDRESS/PC080SN/FG_TILEMAP` at `0xC09EA0..0xC09EA6`
  **do occur** (8 events across frames 170..384) in Build 0033 — independently
  corroborated by the BlastEm fatal-error screenshot (see
  `docs/design/Andy_build_33_diagnostic.md` §5).
- The 0x03C4D2 handler path is **not** producing those writes (helper
  watchpoint proof).

### 3.3 What the trace cannot prove

- The specific sibling handler (or combination) responsible for the
  `0xC09EA0` writes is **not identifiable from the current trace alone**.
  The trace summary's `first_pc/last_pc` fields for `fg_cwindow_live`
  read `0x03C52A/0x03C518` — these numbers match `arcade_pc` positions
  inside the dead 0x03C516 inner subroutine, but `helper_5b512_rts count=0`
  contradicts that code actually running. See `docs/design/Andy_build_33_diagnostic.md`
  open question 1 (trace-harness PC-normalization) — remains unresolved
  and does not bear on the §6 interception-level determination.
- The per-event PC stream of the trace log does not record a handler-entry
  breakpoint for each sibling; only sparse snapshots.

**Conclusion: the trace is insufficient to identify which specific sibling
handler fires.** Additional instrumentation (per-handler watchpoints in
`tools/mame/genesistrace.lua` or a live execution-range filter keyed to
each `arcade_pc` in §2's table) would be required to attribute writes to
a specific sibling. This does not block the §6 determination, which
stands on write-shape and contract evidence alone.

---

## 4. Write Contract Per Firing Handler (Stated As "Per Candidate Handler"
Because §3 Cannot Narrow To A Single Firing Handler)

All candidates below are disassembled from `build/maincpu.disasm.txt`.
Every listed `arcade_pc` has a corresponding `genesis_rom_offset` from
`address_map.json` per §2. All use the **same write shape family**:
`movew <tile>, A1@(2)` → `movew <attr>, A1@(6)` → `addq.l #8, A1`.

| Handler `arcade_pc` | Lines | Inner sub | Prefix-skip | Iteration plan | A1 stride per iter | Extra A1 post-adjust | Write shape |
|---------------------|-------|-----------|-------------|----------------|--------------------|----------------------|-------------|
| `0x03C4D2` (hooked) | 75918–75940 | `0x03C516` | `muluw #5` | 2 × 5 (with terminator at last iter of 2nd half) | +8 | `A1 = A2 = entry_A1 + 0x50` | `A1@(2) / A1@(6)` |
| `0x03C550` | 75960–75978 | inline (single loop at 0x03C564–0x03C57E) | `A0 += D0` (lslw implicit — no mul) | 5 iter (`moveq #4, D3` → 5 passes of the `dbra`) | +8 | `addaw #48, A1` (post-loop) | Atypical: **attr first at `A1@(6)`, then literal A4@(26) at `A1@(2)`** (lines 75971–75972); still stride +8 |
| `0x03C586` | 75979–76018 | `0x03C606` | `muluw #3` with branch on `A4@(1).b == 6` | 3 × 2 with inter-leaved `0x03C742` fill call | +8 (per 0x03C606) and +24 or +16 A1 post-adjust | post-loop `addaw #24, A1` or `addaw #16, A1` per branch | `A1@(2) / A1@(6)` |
| `0x03C606` (sub-sub of `0x03C586`) | 76019–76034 | — | reads `(A0)+`, tests for `0xFF` sentinel → writes blank tile `#0x180` to `A1@(2)` or real tile | count `D3` | +8 | none | `A1@(2) / A1@(6)` (both branches) |
| `0x03C636` | 76035–76071 | `0x03C742` + `0x03C6AC` | `lslw #2, D0` | 2×2 calls of 0x03C6AC + conditional 2× calls of `0x03C742` under `A5@(280)`/`A5@(318)` game-state branches | +8 | `addaw #32` or `addaw #48, A1` per branch | `A1@(2) / A1@(6)` |
| `0x03C742` (sub-sub of `0x03C636`, `0x03C75C`, `0x03C5A6`, ...) | 76122–76128 | — | no prefix skip (single-word helper) | 1 | 0 (no A1 advance) | — | `A1@(2) / A1@(6)` (one pair) |
| `0x03C6AC` (sub-sub of `0x03C636`) | 76072–76087 | — | reads `(A0)+`, tests for `0xFF` sentinel | count `D3` | +8 | none | `A1@(2) / A1@(6)` |
| `0x03C6DC` | 76088–76102 | `0x03C70A` | `muluw #9` | 6 iter + 3 iter | +8 per sub; +8 post | `addq.l #8, A1` (final) | `A1@(2) / A1@(6)` |
| `0x03C70A` (sub-sub of `0x03C6DC`) | 76103–76121 | — | reads `(A0)+`, tests for zero | count `D3` | +8 | none | `A1@(2) / A1@(6)` (with `jsr 0x5B512` between the two writes) |
| `0x03C75C` | 76129–76151 | `0x03C742` + `0x03C7D2` | `muluw #7` | 1 × `0x03C742` + 4 varied-param calls of `0x03C7D2` with `D3=1,1,1,1,4` | +8 per write | `addaw #16, A1` post | `A1@(2) / A1@(6)` |
| `0x03C7A4` | 76152–76166 | `0x03C804` + `0x03C7D2` | `muluw #6` | 2 × `0x03C804` with `D3=2` + 1 × `0x03C7D2` with `D3=6` | +8 | none | `A1@(2) / A1@(6)` |
| `0x03C7D2` (sub-sub of `0x03C75C, 0x03C7A4`) | 76167–76183 | — | reads `(A0)+`, tests for `0xFF` sentinel | count `D3` | +8 | none | `A1@(2) / A1@(6)` |
| `0x03C804` (sub-sub of `0x03C7A4`) | 76184–… | — | computes `D0` from `D3` cmp | count `D3` | +8 | none | `A1@(2) / A1@(6)` |
| `0x03C830` | 76198–76212 | `0x03C85E` + `0x03C8BE` | `lslw #2, D0` plus branch on `A4@(56).b` | 2 × 5 with `0x03C85E`; branch path also calls `0x03C742`, `0x03C8E8` nests | +8 | `addaw #8, A1` between halves | `A1@(2) / A1@(6)` |
| `0x03C85E` (sub-sub of `0x03C830`) | 76213–76233 | — | reads `(A0)+`; conditional `jsr 0x03C89A` for glyph-special | count `D3` | +8 | none | `A1@(2) / A1@(6)` |
| Dispatcher default path (`0x03C950+`) | 76289+ | `0x03C9E8, 0x03C9F6, 0x03CA00, 0x03CA12, 0x03CA26` | custom — reads opcode-byte loop from `(A0)+` via `0x03CA00`, dispatches internal state | variable | **stride `+2` (post-increment)** via `%a1@+` at `0x03C982, 0x03C990, 0x03C99E` — NOT the `+8` family | may also write `movew #0x0180, A1@(2); addq.l #8, A1` at `0x03C9F8` | **MIXED**: `A1@+` (stride 2) for most writes; `A1@(2)` + `addq.l #8, A1` for the blank-glyph escape at `0x03C9F8` |

**Observation:** All 9 top-nibble handlers use the `A1@(2) / A1@(6) / +8`
family. Iteration counts, prefix-skip multipliers, A1 post-loop
adjustments, and inner-sub call patterns **vary per handler**. The
dispatcher fall-through default path uses a **different write shape**
(`A1@+` stride-2).

---

## 5. Sibling Handler Survey (All Unhooked Siblings)

(Same table as §4 — every candidate listed is unhooked except `0x03C4D2`.)

### 5.1 Write-shape compatibility

Nine of the ten siblings share the **stride-8, `A1@(2)` + `A1@(6)` per
iteration** contract. The tenth (dispatcher default at `0x03C950+`) uses
a **stride-2 `A1@+` post-increment** shape.

### 5.2 Handler-specific semantic divergence (within the stride-8 family)

| Attribute | Varies across handlers? | Examples |
|-----------|-------------------------|----------|
| Prefix-skip multiplier (`muluw #N` or `lslw`) | YES | `#3` (0x03C586), `#5` (0x03C4D2), `#6` (0x03C7A4), `#7` (0x03C75C), `#9` (0x03C6DC), `lslw #2` (0x03C830 / 0x03C636) |
| Total cell count | YES | 10 (0x03C4D2), variable 5 to ~9 (0x03C550, 0x03C586, 0x03C6DC, 0x03C75C, 0x03C7A4, 0x03C830) |
| Attribute-offset adjustments (the `D2` adjust alternates `0`, `-16`, `-8`) | YES | `0` & `-16` (0x03C4D2); `0` & `-16` & `-8` (0x03C75C); `0` & `-16` combined (0x03C586, 0x03C830); special attr-first ordering (0x03C550) |
| Inner subroutine body | YES | Each top-level handler has its own inner sub (`0x03C516, 0x03C606, 0x03C6AC, 0x03C70A, 0x03C742, 0x03C7D2, 0x03C804, 0x03C85E`). No shared inner sub across top-level handlers (`0x03C742` is the only shared sub, used by multiple handlers as a helper). |
| A1 post-loop advance | YES | `0x50` (0x03C4D2); `0x30` (0x03C550); `0x10`/`0x18` (0x03C586); `0x20`/`0x30` (0x03C636); `0x10` (0x03C75C); none (0x03C7A4) |
| Game-state conditional branches | YES | 0x03C586 branches on `A4@(1).b == 6`; 0x03C636 branches on `A5@(280).b`, `A5@(318).w`; 0x03C830 branches on `A4@(56).b` — **these are non-FG-tilemap conditionals read before writes occur** |
| Terminator sentinels in script data | YES | `0xFF` (0x03C606, 0x03C6AC, 0x03C7D2); special-case `cmpib #0x50, D3` + `cmpiw #1, D4` (0x03C516) |

### 5.3 Non-FG-tilemap work that a dispatcher-level hook would erase

- **`0x03C636` reads `A5@(280)` and `A5@(318)` for game-state conditionals**
  that control the number of `0x03C742` fill calls and the post-loop A1
  advance (`+32` vs `+48`). Side-effect: none observed, but control-flow
  depends on live game state.
- **`0x03C830` reads `A4@(56).b` and may branch into a secondary path
  starting at `0x03C8BE`** that calls `0x03C742` twice with stride +8 A1
  adjusts plus `0x03C85E` 2×2 iterations. The behavior is materially
  different from the match path; the handler selects at runtime.
- **Dispatcher default path (`0x03C950+`) reads `D6`, `D7` and conditional
  opcode bytes at `0x03CA00`** to drive a sub-loop that writes 3 words per
  iteration via `A1@+` — a completely different data structure.
- **Inner subs `0x03C70A` and `0x03C516`** call `jsr 0x0005B512` between
  the tile and attribute writes (confirmed no-op in `rastan_direct`; this
  does not block a hook, but a dispatcher-level hook would have to
  replicate this fact carefully).

### 5.4 Can all siblings be handled by a single dispatcher-level translator?

The question reduces to: can one translator produce the correct
`staged_fg_buffer` + `fg_row_dirty` state for any incoming opcode /
`A4`-state combination, given only `(A0, A1, A4, A5)` at dispatcher
entry?

- YES, **in principle**, but only by **re-implementing all 10 handler
  bodies inside the translator** — selecting by top nibble of `(A0)`
  and replicating the muluw multiplier, iteration plan, inner-sub
  read-byte sequencing, game-state conditionals, and A1 post-advance
  of each handler.
- This is an embedded **dispatcher-inside-the-translator** — equivalent
  work to adding 10 sibling translators, but concentrated in one
  function with 10 `case` branches. Complexity is the same.

---

## 6. Interception-Level Determination

Evaluation of the four conditions from the prompt:

| Condition | Holds? | Evidence |
|-----------|:------:|----------|
| (a) Dispatcher entry has a stable, hookable register contract | **YES** | §1. Entry reads `(A0)` without side-effect; A0/A1/A4/A5 have well-defined roles consumed uniformly by every handler. |
| (b) All handler branches produce writes to `HW_ADDRESS/PC080SN/FG_TILEMAP` via the same logical path | **NO** | §5. 9 of 10 siblings use stride-8 `A1@(2) + A1@(6)`; the dispatcher default path uses stride-2 `A1@+`. Within the stride-8 family, iteration plans, prefix-skip multipliers, attribute-bias sequences, and A1 post-advance all vary per handler. "Same logical path" is false; the logical path varies per top nibble. |
| (c) A single hook at dispatcher entry can correctly route all opcodes to `staged_fg_buffer` + `fg_row_dirty` without handler-specific logic | **NO** | §5.4. A single hook can do this only by **re-implementing all 10 handler bodies** inside itself. Handler-specific logic cannot be avoided — it is exactly what makes each top-nibble opcode mean something different. |
| (d) No handler performs non-FG-tilemap work that must be preserved | **NO** | §5.3. Handlers `0x03C636` and `0x03C830` read game-state fields (`A5@(280), A5@(318), A4@(56)`) to pick internal sub-paths; the dispatcher default path reads opcode-continuation bytes from `(A0)+` via `0x03CA00`, advancing A0 in ways that depend on the input byte stream. A dispatcher-level hook must replicate these state-dependent A0 advances or downstream dispatcher state will diverge. |

**Three of four conditions fail. A dispatcher-level hook is NOT the
correct answer.**

### INTERCEPTION LEVEL: **PER-HANDLER**

The complete list of `arcade_pc` entries that require individual hooks
(one hook per entry; addresses double-checked against `address_map.json`
segment lookup per §2):

| # | Handler `arcade_pc` | Handler `genesis_rom_offset` | Top-nibble serviced | Status |
|---|---------------------|------------------------------|---------------------|--------|
| 1 | `0x03C4D2` | `0x03C6D2` | `0x50, 0x60` | Already hooked (Build 0033) |
| 2 | `0x03C830` | `0x03CA30` | `0x10` | **needs hook** |
| 3 | `0x03C7A4` | `0x03C9A4` | `0x20` | **needs hook** |
| 4 | `0x03C6DC` | `0x03C8DC` | `0x30` | **needs hook** |
| 5 | `0x03C75C` | `0x03C95C` | `0x90` | **needs hook** |
| 6 | `0x03C550` | `0x03C750` | `0xA0` | **needs hook** |
| 7 | `0x03C636` | `0x03C836` | `0xB0` | **needs hook** |
| 8 | `0x03C586` | `0x03C786` | `0xC0` | **needs hook** |
| 9 | `0x03C950` (dispatcher fall-through default path) | `0x03CB50` | *default* | **needs hook** — note: the correct patch span here is the dispatcher body from `0x03C950` through its closing `rts` at `0x03C9A4` **before** the sub-sub `0x03C9A6`, so care is required to size the `opcode_replace` without overwriting the sub-subs `0x03C9E8, 0x03C9F6, 0x03CA00, 0x03CA12, 0x03CA26` that are called by the default path. Each of those sub-subs may need to be separately NOP-d or left alone depending on Cody's implementation strategy. |

**Count: 7 sibling top-level handlers + 1 dispatcher default-path
hook = 8 new hooks required**, in addition to the 1 already installed
at `0x03C4D2`.

A per-handler hook is strictly consistent with
`docs/design/Andy_final_pc080sn_hook_strategy.md`: *"One hook, multiple
call sites, zero game-state awareness"*. Each hook is a stateless
translator for that specific handler's write pattern; they share the
same output convention (`staged_fg_buffer` + `fg_row_dirty`) and the
same LUTs (`genesistan_pc080sn_tile_vram_lut`,
`genesistan_pc080sn_attr_lut`), but each encodes the per-handler
muluw multiplier, iteration plan, and A1 post-advance as its own spec.

---

## Open Questions

1. The specific sibling that fires in Build 0033 attract mode cannot be
   identified from the current trace — §3.3. To narrow the scope of the
   per-handler hook work from 8 to a smaller set, an instrumentation
   pass (per-handler live-watches or a full PC stream trace keyed to
   the handler addresses listed in §6) is required.
2. `fg_cwindow_live first_pc/last_pc` values in the Build 0033 summary
   still conflict with `helper_5b512_rts count=0` — unresolved.
   Reading `tools/mame/genesistrace.lua` would explain PC-field
   normalization; does not affect §6.
3. For the dispatcher default path at `0x03C950`, whether the sub-subs
   `0x03C9E8, 0x03C9F6, 0x03CA00, 0x03CA12, 0x03CA26` have any callers
   outside the default path has not been verified. If they do have
   other callers, the patch span at `0x03C950` must be sized to not
   clobber them; if not, the span can be larger. Grep of
   `build/maincpu.disasm.txt` for each sub-sub's address is the next
   mechanical step.

---

## Files

- Created: `docs/design/Andy_dispatcher_map_analysis.md` (this document).
- Modified: none.
