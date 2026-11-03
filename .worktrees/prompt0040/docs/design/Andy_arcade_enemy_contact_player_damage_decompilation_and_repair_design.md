# Andy — Arcade Enemy→Rastan Damage Linkage: Decompilation + Genesis Repair Design

**Date:** 2026-10-17 · **Agent:** Andy · **Type:** ARCADE reverse-engineering + existing-C-tree
extension + Genesis repair design (for Cody). **No** Genesis production source/Makefile/generator/
verifier/spec change, **no** ROM, **no** MAME, **no** new trace/Lua, **no** build number/counter
change, **no** damage fix implemented. Phase D/E not started; HUD/framing not resumed; scroll work
untouched.

**Current baseline:** Build **0439** (counter 439; commits `033795e3` "Build 439 — Hoist Plane-A
column residency context", `a84a29eb` doc). Build 0439 is a Plane-A residency optimization on top of
the restored-0434 implementation; it does not touch the damage path. No uncommitted production/scroll
changes were present; none were modified.

**Tool reuse (RULES §18):** reused the existing Rastan arcade Ghidra project / exports, arcade
disassembly `build/maincpu.disasm.txt`, the existing C decompilation tree, Genesis postpatch
disassembly `build/genesis_postpatch.disasm.txt`, `build/rastan-direct/address_map.json`, the remap
spec `specs/rastan_direct_remap.json`, and `tools/mame/cheat/output.json`. New tooling: none. No
parallel Ghidra DB or second C tree was created.

---

## 1. EXECUTIVE RESULT

The previously "not located" **enemy-contact → Rastan damage** path is now fully recovered, and the
Genesis failure is isolated to **one un-rebased absolute WRAM operand** — the KF-044 class, the same
pattern already fixed for its siblings in Builds 0366 (`0x10C242`) and 0368 (`0x10C2C8`).

- **Arcade:** `0x449B4` pass 1 records enemy↔player-body overlaps into the **body-hit list
  A5+0x12A8** (written A5-relative). Consumer **`0x54A40`** reads that list and dispatches per-type
  **player-damage handlers** (`0x551CC`+), each of which gates on `A5+0x40` (debug invincibility) and
  `A5+0x1366` (post-hit invuln), **decrements energy `A5+0x013A`**, starts the post-hit invuln
  window, and runs the knockback/hurt reaction `0x5560C`; a lethal arm sets player state 8 (death).
- **Genesis defect:** the consumer reads the list with an **absolute long** `LEA 0x0010D2A8,A0`. On
  Genesis the A5 work-RAM (`0x10C000…`) is rebased to `0xFF0000…`, so the list lives at `0x00FF12A8`;
  the producer writes it there correctly (A5-relative), but **this absolute read was never rebased**
  and still points at ROM `0x0010D2A8`. The consumer sees 4 inert ROM "records", no handler fires,
  and **enemies deal no damage, knockback, hurt, or death**. The sibling list `A5+0x12C8`
  (`0x0010D2C8`) was rebased to `0x00FF12C8` in Build 0368; the body-hit read at `0x54A40` was missed.
- **Fix:** one byte-neutral `opcode_replace` at arcade `0x054A40`: `41F90010D2A8` → `41F900FF12A8`
  (`LEA 0x00FF12A8,A0`), mirroring the Build-0368 entry at `0x054B1E`.
- **Energy question:** **YES** — ordinary enemy contact decrements `A5+0x013A` (the energy/health
  field) by a type-specific amount. The reduced Genesis HUD separately hides that field.

---

## 2. NEW/UPDATED GHIDRA DECOMPILATIONS (existing C tree)

Added under `analysis/decompilation/c/` (existing conventions; the 68000 remains authority):

- `raw/00054a40.c` — body-hit-list **consumer** `0x54A40` (dispatch loop, KF-044 site documented).
- `raw/000551b0.c` — per-type **player-damage handler family** `0x551B0`/`0x551CC`+ and the hurt
  reaction `0x5560C`.
- `rastan_player_damage.c` — **semantic** enemy-contact→player chain, contact-class separation, the
  energy answer, and the post-hit-invuln mechanism.
- Metadata: `function_coverage.csv` rows for `00054a40`, `000551b0`, `0005560c`; `README.md` layout
  entry for `rastan_player_damage.c`. The existing `raw/000449b4.c` (producer) and
  `raw/00054bf8.c` (solid push-out) were used as-is and cross-referenced (not duplicated).

---

## 3. ARCADE ENEMY→RASTAN DAMAGE CALL GRAPH

| Link | Arcade PC | Role | Input state | Output / fields touched | Branch condition | Next |
|---|---|---|---|---|---|---|
| A | `0x449B4` pass 1 (`0x449E4`) | detect enemy-hurtbox ∩ player-body | enemy pool A5+0x2C8, player body box | writes `A5+0x12A8` body-hit record `{active=1,type=1,X=+0x16,Y=+0x1A}` (A5-relative) | per live enemy, mode `+0x03==0`, overlap `0x44930/0x44CBA` | consumer |
| B | `0x54A40` | consume body-hit list | `A5+0x12A8` (abs `0x0010D2A8`) | loop 4 records; index by type `d1` | `active==1 && 1≤type≤30` | dispatch `0x550A8` |
| C | `0x550A8` table → `0x551CC`+ | per-type damage handler | record type | see D | type→pointer | handler |
| D | `0x551CC` (and siblings) | apply damage | `A5+0x40`, `A5+0x1366`, `A5+0x12F0`, `A5+0x130E`, `A5+0x013A` | `A5+0x13C4=1`; **`A5+0x013A -= 512..6144`**; `A5+0x12FC=1`; `A5+0x1366=1`; `A5+0x1368=0` | skip if `A5+0x40!=0` (invincible) or `A5+0x1366==1` (post-hit invuln) or already hurt/knockback | `0x5560C` |
| E | `0x5560C` | hurt reaction / knockback | — | pose `0x0C` via `0x3A0EC`; `A5+0x12F0=1`,`A5+0x12F2=12`; or knockback `A5+0x130E=1`,`A5+0x130C=16`; `A5+0x1366=1`,`A5+0x1368=0` | `A5+0x1108==1` picks knockback branch | return |
| F | lethal arm `0x553E6` | instant death | — | `A5+0x10E8 = 8` (player death) | after `A5+0x40` gate | death tail |
| G | energy==0 | death by depletion | `A5+0x013A==0` | player death state 8 | continuous | `rastan_player_animation.c` |

---

## 4. STATE/FIELD TABLE

Arcade A5 base `0x10C000`; Genesis WRAM rebase **A5 → 0xFF0000**.

| Field | Arcade abs | Genesis WRAM | Meaning |
|---|---|---|---|
| A5+0x0040 | `0x10C040` | `0xFF0040` | debug/benchmark **invincibility** gate (bit 6); nonzero ⇒ handlers skip |
| A5+0x12A8 (4 × 8B) | `0x10D2A8` | `0xFF12A8` | **body-hit list** (enemy↔player-body) — producer A5-rel, **consumer abs (BUG)** |
| A5+0x12C8 (4 × 8B) | `0x10D2C8` | `0xFF12C8` | item/weapon event list — consumer rebased in **Build 0368** |
| A5+0x013A (hi byte) | `0x10C13A` | `0xFF013A` | **energy/health**; enemy contact decrements it; 0 ⇒ death |
| A5+0x1366 | `0x10D366` | `0xFF1366` | **temporary post-hit invulnerability** latch |
| A5+0x1368 | `0x10D368` | `0xFF1368` | post-hit invuln / recovery countdown (cleared on hit) |
| A5+0x12F0 | `0x10D2F0` | `0xFF12F0` | hurt-state flag |
| A5+0x12F2 | `0x10D2F2` | `0xFF12F2` | hurt pose timer (=12) |
| A5+0x12FC | `0x10D2FC` | `0xFF12FC` | damage-taken flag |
| A5+0x130E / A5+0x130C | `0x10D30E/0C` | `0xFF130E/0C` | knockback state / knockback run (=16) |
| A5+0x13C4 | `0x10D3C4` | `0xFF13C4` | hit-seen flag |
| A5+0x10E8 | `0x10D0E8` | `0xFF10E8` | player state (8 = death) |

---

## 5. CONTACT CLASS SEPARATION

| Class | Producer | Consumer | Effect | Genesis status |
|---|---|---|---|---|
| **weapon → enemy** | `0x449B4` (weapon box) | `0x447CE`/`0x448D8` | enemy one-hit death + score/recycle | RETAINED CORRECTLY (A5-relative) |
| **enemy → player** | `0x449B4` pass 1 (body box) → `A5+0x12A8` | **`0x54A40` → `0x551CC`+** | energy drain, hurt, knockback, post-hit invuln, death | **RETAINED BUT CONSUMER OPERAND WRONG** (`0x0010D2A8`) |
| **terrain/solid → player** | `0x44548`/`0x449B4` → `A5+0x0242` | `0x54BF8` | push-out resolution (no energy change) | RETAINED CORRECTLY (rebased `0xFF0242`, Build 0366) |

The prior audit's suspicion that `0x54BF8` was the damage consumer is corrected: `0x54BF8` is
**push-out/terrain**, which is why terrain deaths (lava/pits/drowning) still work while enemy damage
does not.

---

## 6. ENERGY / HEALTH SEMANTICS

**YES — enemy contact decrements `A5+0x013A`.** Each per-type handler performs
`subiw #N,%a5@(314)` with `N ∈ {512,1024,1536,2048,2560,3072,4096,5120,6144}` (high-byte
decrements of 2,4,6,8,10,12,16,20,24 energy units; selected by the record `type`). This is the same
field the energy bar and the drain timer use — there is **no separate HP accumulator** for the
player. When it reaches 0 the player enters death state 8 (`rastan_player_animation.c`). Lethal arms
(e.g. `0x553E6`) additionally set state 8 directly. The reduced Genesis HUD hides `A5+0x013A`, so the
decrement would be invisible until HUD mode 1 — but knockback/hurt/death are visible regardless.

---

## 7. TEMPORARY POST-HIT INVULNERABILITY

Mechanism, distinct from the `A5+0x0040` debug gate:

- **Latch:** `A5+0x1366`. Set to 1 by the damage handler and by `0x5560C`.
- **Timer:** `A5+0x1368`, cleared to 0 on hit; counted elsewhere to clear the latch after recovery.
- **Consulted:** at the top of every handler (`if A5+0x1366==1 return`) — immediate repeated contact
  during the window does not re-hit (no double-hit).
- **Not** the stock MAME cheat. The cheat is `A5+0x0040` bit 6 (source-proven separate gate).
- Hurt/knockback pose is driven by `0x5560C` (pose `0x0C` via `0x3A0EC`); blink/flash, if any, is
  tied to the recovery window via the normal player-render path, not re-derived here.

---

## 8. ARCADE-PC → GENESIS-PC MAPPING

Authority: `build/rastan-direct/address_map.json` + current Build-0439 `genesis_postpatch.disasm.txt`.

| Arcade PC | Genesis runtime PC | Instruction | Classification |
|---|---|---|---|
| `0x449B4` producer, `LEA %a5@(4776)` | copied | A5-relative write of `A5+0x12A8` | **RETAINED CORRECTLY** |
| `0x50678` `movew #255,%a5@(4776)` (list clear) | `0x5087E` (`movew #255,%a5@(4776)`) | A5-relative | **RETAINED CORRECTLY** |
| **`0x54A40` `LEA 0x0010D2A8,A0`** | **`0x54ABE` `LEA 0x0010D2A8,A0`** | absolute long read of body-hit list | **RETAINED BUT OPERAND WRONG** |
| `0x54B1E` `LEA 0x0010D2C8,A0` | `0x54B9C` `LEA 0x00FF12C8,A0` | absolute long read of item list | **PATCHED CORRECTLY (Build 0368)** |
| `0x551CC`+ handlers | copied | A5-relative field writes + `A5+0x40` gate | **RETAINED CORRECTLY** |
| `0x5560C` hurt reaction | copied | A5-relative | **RETAINED CORRECTLY** |

Only one link is wrong, and it is the single choke point every enemy-damage handler depends on.

---

## 9. ABSOLUTE WRAM LITERAL AUDIT (recovered chain only)

| Arcade instr | Original abs | Genesis runtime instr | Current operand | Correct operand | Status |
|---|---|---|---|---|---|
| `0x54A40 LEA` | `0x0010D2A8` | `0x54ABE LEA` | `0x0010D2A8` | `0x00FF12A8` | **WRONG** |
| `0x54B1E LEA` | `0x0010D2C8` | `0x54B9C LEA` | `0x00FF12C8` | `0x00FF12C8` | correct (0368) |
| `0x449B4` writes | `A5+0x12A8` (A5-rel) | A5-rel | n/a | n/a | correct |
| `0x50678` clear | `A5+0x12A8` (A5-rel) | A5-rel | n/a | n/a | correct |
| handlers `0x551CC`+ | A5-rel fields | A5-rel | n/a | n/a | correct |

**Exactly one** un-rebased operand explains the bug: `0x54A40 LEA 0x0010D2A8`.

---

## 10. DROPPED PRODUCER/CONSUMER AUDIT

No arcade call, branch, record producer, or consumer in the chain is NOPed, skipped, early-returned,
or mapped into replaced/dead code. The producer (`0x449B4`), consumer (`0x54A40`), dispatch
(`0x550A8`), handlers (`0x551CC`+), and hurt reaction (`0x5560C`) are all present and retained in the
Build-0439 copied region. The failure is purely the wrong absolute operand in link B, not a dropped
link.

---

## 11. FIRST EXACT GENESIS DIVERGENCE

- **Arcade:** producer `0x449B4` writes the body-hit record to `A5+0x12A8`; consumer `0x54A40` reads
  `A5+0x12A8` and dispatches a damage handler.
- **Genesis (Build 0439):** producer writes correctly to `0xFF12A8` (A5-relative), **but instruction
  at runtime PC `0x54ABE` (arcade `0x54A40`) still reads absolute `0x0010D2A8` (ROM) instead of
  `0x00FF12A8`**, so the consumer never sees the hit and no handler executes.

Failure class: **WRAM REBASE (KF-044)**.

---

## 12. ROOT CAUSE

> On Genesis, the enemy→player damage producer (`0x449B4`, A5-relative) correctly writes the body-hit
> list to WRAM `0xFF12A8`, and all per-type damage handlers (`0x551CC`+) are retained and would fire
> (A5+0x40 = 0, i.e. not invincible — proven in the Build-0438 audit). **The single consumer read
> `LEA 0x0010D2A8,A0` at arcade `0x54A40` / runtime `0x54ABE` was never rebased to `0x00FF12A8`, so it
> reads ROM, sees no live record, and dispatches no handler — the player therefore takes no energy
> loss, no hurt, no knockback, and no enemy-contact death.** The sibling item-event read
> (`0x0010D2C8`) was rebased in Build 0368; the body-hit read was missed. This is a long-standing
> condition (enemy damage has never functioned on Genesis), not a Build-0438/0439 regression.

---

## 13. CODY IMPLEMENTATION SPEC

**Repair tier:** Tier 1 (wrong absolute WRAM operand) — a single byte-neutral `opcode_replace`.

- **Expected production file changed:** `specs/rastan_direct_remap.json` (add one `opcode_replace`
  entry). No `.s`, Makefile, generator, or verifier change. (The entry is then realized by the
  existing postpatch pipeline; no new mechanism.)
- **Arcade PC:** `0x054A40`.
- **Genesis runtime PC (current Build-0439 postpatch):** `0x054ABE` (informational; the postpatcher
  derives it — do not hand-encode a runtime PC).
- **Current bytes:** `41 F9 00 10 D2 A8` (`LEA 0x0010D2A8,A0`).
- **Desired bytes:** `41 F9 00 FF 12 A8` (`LEA 0x00FF12A8,A0`).
- **Change:** rebase only the absolute operand `0x0010D2A8 → 0x00FF12A8` (arcade A5+0x12A8 → Genesis
  WRAM). Byte-neutral 6→6.
- **Model entry (mirror the Build-0368 `0x054B1E` entry):**
  ```json
  {
    "arcade_pc": "0x054A40",
    "original_bytes": "41F90010D2A8",
    "replacement_bytes": "41F900FF12A8",
    "note": "Enemy-contact player-damage fix (KF-044). The retained body-hit-list consumer 0x54A40 scans four 8-byte records at arcade WRAM A5+0x12A8 (0x0010D2A8) written A5-relative by 0x449B4 pass 1, and dispatches per-type damage handlers (0x551CC+, table 0x550A8) that decrement energy A5+0x13A, apply knockback (0x5560C) and death. Genesis left this absolute LEA at ROM 0x0010D2A8, so no enemy-contact hit was ever consumed and enemies dealt no damage. Rebase only the record-table operand to mapped Genesis WRAM A5+0x12A8 at 0x00FF12A8. Sibling 0x12C8 was rebased in Build 0368. Intentional 6->6 address-contract correction; no forced damage, no new collision rule, no replacement gameplay path."
  }
  ```
- **Semantic reason:** restores the arcade address contract so the retained consumer reads the live
  WRAM record the producer actually wrote.
- **Expected side effects:** enemy contact now drains energy, triggers hurt/knockback and post-hit
  invulnerability, and can kill the player; energy-based and lethal-arm deaths from enemies become
  reachable. (Energy drain remains visually hidden until HUD mode 1 — separate, deferred.)
- **Invariants that must remain unchanged:** the producer, dispatch table, handlers, `A5+0x40` gate,
  `A5+0x1366` post-hit invuln, weapon→enemy path, terrain→player push-out, collision geometry,
  difficulty, and all other absolute/relative operands. No runtime state added. No Genesis-owned
  damage system. No PC080SN/PC090OJ emulation.

This spec is exact; no further proof is required to author the entry. One targeted runtime check
(below) is recommended as post-fix confirmation, not as a precondition.

---

## 14. VALIDATION PLAN (for the eventual Cody build)

**STATIC**
- Confirm the new `opcode_replace` applies at arcade `0x054A40`; original bytes match `41F90010D2A8`.
- Postpatch disassembly shows the consumer read as `LEA 0x00FF12A8,A0`; no other `0x0010D2A8`
  absolute remains; `0x00FF12C8` (0368) unchanged.
- `address_map.json` / relocation report regenerate cleanly; canonical coverage unchanged except the
  one operand; no unintended code changes; producer/handlers/`0x5560C` byte-identical.

**EXISTING AUTOMATED**
- Normal project gates (boot guard, canonical gate, gameplay-entry gate, family check).
- Standard fixed 30-second GENESIS NTSC trace completes (~1,798 frames), no exceptions.
- Rope benchmark as a regression check only — expect it **unchanged** (the rope route uses no enemy
  contact; and if a future arcade-style invincibility benchmark is used, A5+0x40 still gates).

**TARGETED DAMAGE VALIDATION** (Tighe owns real-hardware gameplay; keep minimal)
- One deliberate enemy contact: player enters hurt pose `0x0C`, knockback occurs, `A5+0xFF013A`
  decrements by the type amount, `A5+0xFF1366` latches (post-hit invuln), immediate re-contact does
  **not** double-hit, recovery clears the latch, and sustained/strong contact can reach death
  (state 8). Confirm weapon→enemy kills and terrain deaths are unchanged.

---

## 15. REMAINING UNRESOLVED ITEM / one targeted runtime proof

Static evidence is conclusive for the root cause and the fix. **One optional runtime confirmation**
(design only; not run here) would remove all residual doubt:

- **Watch** Genesis WRAM `0xFF12A8` (body-hit record, expect first word → `0x0001` on contact),
  `0xFF013A` (energy, expect the high byte to drop by the type amount), `0xFF1366` (post-hit invuln,
  0→1 on hit), and `0xFF10E8` (player state).
- **Breakpoint** at runtime `0x54ABE` (consumer): on a deliberate enemy contact it should now load
  `A0 = 0x00FF12A8` after the fix (pre-fix it loads `0x0010D2A8`).
- **Distinguishing outcomes:** if, pre-fix, `0xFF12A8` shows `active=1` while the consumer reads
  `0x0010D2A8` and no energy change occurs, the rebase is confirmed as the sole cause. Post-fix, the
  same contact should decrement `0xFF013A` and latch `0xFF1366`.

This is a watchpoint-only check on a single deliberate contact; it is not a new gameplay framework.

---

## FINAL STATUS

Genesis production source modified: NO. Makefile: NO. Generators/verifiers/specs modified: NO
(spec change is the *proposed* Cody repair, not applied here). ROM built: NO. MAME run: NO. New
gameplay trace/Lua: NO. Build number consumed: NO. Build counter changed: NO. Scroll work modified:
NO. HUD/framing resumed: NO. Phase D: NO. Phase E: NO.
