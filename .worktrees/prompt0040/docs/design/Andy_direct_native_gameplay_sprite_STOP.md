# Direct-Native Gameplay Sprite Conversion — STOP (per-piece code of specialized actors is retained record state)

**Agent:** Andy · **Type:** Implementation attempt → architectural STOP · **Build produced: NO.**
**No source, spec, generated object, or ROM changed this task** (investigation only; tree unchanged from Build 0259).

## Phase 0

Relevant priors from KNOWN_FINDINGS:
- **KF-026 (STRONG, GLOBAL, ACTIVE)** — "PC090OJ runtime write surface not fully statically enumerable … pointer-indexed runtime addressing contributes write destinations that require trace evidence." Directly governs this STOP.
- KF-049 / KF-044 — canonical player anchor lives at records 120/121; player-source mapping 0x041F5E (unchanged here).
- KF-021 / KF-047 — SAT/renderer masking + bounded candidate derivation (native lane finalizer, unchanged).

Rediscovery Hazard HIGH findings touched: none contradicted.

Deferred-appendix entries relevant: none.

Task classification: **EXTENDING** (continues the PC090OJ→native gameplay migration, OPEN-024-adjacent).

Open/Closed issues touched: OPEN-024-adjacent (PC090OJ native gameplay migration). No new issue required — KF-026 already records the underlying static-enumeration limit.

Contradiction of CONFIRMED or STRONG finding detected: NONE. This STOP is **corroborated by** KF-026 (STRONG), not in conflict with it.

## What was verified (static, Ghidra + linked disasm + ROM tables)

1. **Family/type dispatch is statically clean.** `arcade_pc 0x3D054`: `a0 = family_table_base + u16[class]`; family select on `a4@0x38`; type = `*a0 & 0xF0`. Type is **class-fixed** (the descriptor is indexed by class, not by animation frame `a4@0x0B`).
2. **Class census over all five family tables** (0x3D09E/0x4771C/0x3F0CE/0x40004/0x4002C; 253/246/131/167/167):
   **949 classes use the default expander** (types 0x00/0x40/0x70/0x80/0xD0/0xE0/0xF0); **15 classes use a
   position-only specialized handler.** The specialized set: fam0 class118=0x10, 120=0x20, 122=0x30, 138=0x50,
   140=0x60, 146=0x90, 240=0xA0, 246=0xB0; fam2 class2/4/6=0xC0, class40=0x10; fam3 class54=0x20, 55=0x30;
   fam4 class145=0x10.
3. **Default expander `0x3C950` is fully reimplementable natively** (no records needed). Per piece, reading the
   class mapping + actor fields:
   - attr@0 = flip/palette flags OR'd with `a4@39` (visibility bit6) — `0x3C9E8`;
   - **code = `a4@30` (base tile) ± mapping code-byte** — `0x3C9E8`→store, cursor `0x3CA12` (`a4@0x1E ± *a0`);
     +`a4@24` when type 0x70 — `0x3C8F6`;
   - Y = `a4@26` + mapping Y-byte; X = `a4@22` + mapping X-byte (`0x3C984`/`0x3C996`).
   Every input is a live actor field or a live ROM mapping byte → direct native emission is straightforward.
4. **Specialized handlers write position only.** Exhaustive scan of `0x3C4D2..0x3C902`: every `move …,a1@(N)`
   store targets `a1@(2)` (Y) or `a1@(6)` (X) or the `0x0180` park; the **only** `a1@(4)` (code) store in the
   entire cluster is `0x3C8B8` (handler 0x10's stage recompute); there is **no** `a1@(0)` (attr) store anywhere.
   The specialized mapping descriptors carry **position-only** bytes (e.g. 0xC0's tables 0x3CA7A/0x3CA38 are
   offsets + 0xFF blanks, no code).
5. **No static spawn writer of per-piece code to the specialized bands.** A whole-ROM search for any
   `lea/movea` of the specialized record bands (`0x00D001C8/0x00D00170/0x00D00300/0x00D00460`) plus a nearby
   `+4` store finds **none** outside the per-frame master build itself. The bands are addressed only through the
   pointer-indexed `a1` handed to the engine and advanced at runtime — i.e. exactly the class KF-026 says is
   **not statically enumerable**.

## The concrete contradiction that blocks a correct direct-native build

- **Exact original `arcade_pc`:** 0x3C586 (type 0xC0; also 0x3C4D2/550/636/6DC/75C/7A4/830 for the other 14
  specialized classes). Master builds 0x41DAE/0x45DFA. Default expander 0x3C950 is **not** blocked.
- **Exact mapped `runtime_genesis_pc`:** the relocated copies at `+0x200` (e.g. 0x3C786 / dispatch 0x3D254),
  reached from `genesistan_pc090oj_hook_target_41dae/45dfa`.
- **Actor family/class:** fam2 class 2/4/6 (type 0xC0, four pieces) — the **lizard-man** class the user
  requires to keep working; plus the other 14 specialized classes.
- **Semantic value that cannot be produced:** the **per-piece artwork code (record+4)** of each specialized
  multi-piece actor. A 0xC0 actor emits four pieces that must carry four *distinct* tile codes.
- **Ghidra + opcode evidence:** the specialized handler never writes code@4 (only 0x3C8B8, type 0x10, writes
  code and only under stage gate `a5@0x118==3`); the specialized mapping is position-only; the type is
  class-fixed so these actors never run the code-bearing default expander; no static spawn writer of code to
  their bands exists (searched); **KF-026 (STRONG)** independently states these pointer-indexed PC090OJ write
  destinations are not statically enumerable.
- **Why neither actor/table/stage state nor minimal metadata can represent it:** `a4@30` is a *single* base
  tile (cannot yield four distinct piece codes); the specialized mapping carries no code delta; stage state
  drives only the one 0x10 piece; and **minimal actor-owned metadata cannot be *initialized* correctly because
  its seed — the spawn-time per-piece code writer — is exactly the pointer-indexed surface KF-026 says static
  analysis cannot enumerate.** So the only faithful source of the specialized per-piece codes is the retained
  PC090OJ record, which the FINAL architecture forbids (`RULES.md §11`, policy).
- **Why proceeding would violate architecture / require PC090OJ records:** emitting these classes natively
  either (a) reads the retained record code = forbidden gameplay record dependency, or (b) guesses the codes
  (e.g. `a4@30 + piece_index`) with **no way to validate** — the 30s MAME smoke is frontend-only and does not
  reach Stage-1 gameplay, so a wrong guess ships **broken lizard-man / specialized-enemy artwork**, i.e. it
  fails the user's own acceptance item "gameplay still shows multiple lizard men."

## Exact minimal runtime observation required to unblock (external, not in-ROM)

Capture, for one live type-0xC0 actor (fam2 class 2/4/6, band `0x00D00460`-relative in the arcade engine trace)
across spawn + several animation frames, the four `record+4` (code) values and correlate them to `a4@30`,
`a4@24`, the actor's spawn path, and animation frame `a4@0x0B`. The single fact this must distinguish:
**are the four per-piece codes a pure function of live actor/stage/mapping state (e.g. `a4@30 + fixed
per-piece delta`), or are they persistent per-piece values seeded once at spawn by a pointer-indexed writer?**
- If the former → the specialized handlers become directly recomputable and the full direct-native build
  (default expander already specified in §3 above + the eight specialized formulas) is buildable with no
  records.
- If the latter → a minimal actor-owned `piece_code[]` seeded at that spawn site is the sanctioned
  representation, and the spawn site must be identified from the same trace (it is not statically enumerable —
  KF-026).

The 949-class default-expander conversion in §3 is fully specified and ready to implement the moment the
specialized per-piece code source is pinned; it is not itself blocked.

## Scope

Counter 259 (unchanged); no ROM produced; no source/spec/object changed; Build 0259 preserved and remains the
current (not-accepted) tip. This is a valid architectural STOP under the task's own definition (a semantic value
that cannot be produced from actor/table/stage state or correctly-seeded minimal metadata), corroborated by the
STRONG prior KF-026 — not any of the listed invalid STOP reasons.
