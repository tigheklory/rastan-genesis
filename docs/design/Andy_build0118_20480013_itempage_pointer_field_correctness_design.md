# Andy — Build 0118 0x20480013 Item-Page Pointer-Field Correctness (Design Only)

**Author:** Andy
**Date:** 2026-06-29
**Baseline:** Build 0118 (`dist/rastan-direct/rastan_direct_video_test_build_0118.bin`, SHA256 `aa88da2f35e45974caf61059b4af82ff1c06622e8e011386e1c73d8e1d92fc5f`). rastan-direct.
**Scope:** DESIGN only. No source/spec/tool/Makefile/ROM/build/implementation; no runtime probing (existing evidence + static ROM/JSON inspection only). Output: this doc + one AGENTS_LOG entry. ROM/code pointers via `address_map.json`; work-RAM via KF-036. Labels: **[OBS]** verified this task; **[CODY]** Cody evidence; **[INT]** interpretation. **Class: KF-028 / OPEN-016 runtime-pointer-relocation** (proven). **Predecessor/fixed layer: KF-036 Build 0118 slot-address rebase** (the `0x10D100/0x10D104 → 0x00FF1100/0x00FF1104` fix worked). NOT OPEN-023 (that is Window/HUD).

---

## Phase 0 — Baseline

**Classification:** EXTENDING (KF-028/OPEN-016 runtime-pointer-relocation; item-page strip path). **Contradiction:** NONE. Build 0118 fixed the slot-address bug (old `0x22113111` gone); this is the next layer — the **contents** of the populated pointer field. **Root (proven below):** `Genesis-WRAM 0x00FF10FC` holds a **raw arcade descriptor pointer** (`0x0003951C`); the populator dereferences it raw → reads garbage from `genesis_rom_offset 0x3951C` instead of the JSON-mapped `0x3971C`; the garbage long (`0x20480013`, odd) is stored to `0x00FF1100` and the consumer faults dereferencing it.

---

## 1. Routine / descriptor-format identification [OBS]

Item-page (state 2/2/4) strip emitter, copied arcade code:
- **`0x55E14` walker-advance:** `addql #6,(0x00FF10FC)` — advances the descriptor pointer at `0x00FF10FC` by **6 bytes/group**.
- **`0x55E2E` populator:** `a0=#0x00FF10FC`; `a1=#0x00FF1100`; `a2=#0x00FF1104` (slots rebased Build 0118); `a4=(a0)` = the walker's current descriptor pointer; `(a2)+=(a4)` [**word** → `0x00FF1104`]; `(a1)+=(a4+2)` [**long** → `0x00FF1100`].
- **`0x55E5E` consumer:** `a0=(0x00FF10F8)` (dest); `a2=(0x00FF1100)` (the long the populator stored); inner loop `0x55E7A` (×64): `d7 = d2*32 + (0x00FF10F6)*2`; `a6 = a2 + d7`; `move.w (a6),d0` (**faults**); `move.w d0,(a0)+`; `a0 += 254`.

**Descriptor format (6-byte stride), verified at the JSON-mapped table** [OBS]: `{ word @+0 ; long @+2 }`. At mapped `0x3971C` the stream is well-formed:
```
desc[0] @0x3971C: word=0x0002 long=0x0000D11C
desc[1] @0x39722: word=0x0002 long=0x0000D91C
desc[2] @0x39728: word=0x0002 long=0x0000F11C
```
The **word@+0** (`0x0002`) is copied to `0x00FF1104` (a header/count word the consumer copies first). The **long@+2** is a **strip-data base pointer** that the consumer uses as `a2` (`a6 = a2 + d7`; reads 64 strip words). The `+6` walker stride matches the 6-byte descriptor. [OBS+INT]

---

## 2. `0x0003951C` provenance + address_map.json resolution [OBS]

`0x0003951C` is the value in `Genesis-WRAM 0x00FF10FC` (the walker pointer), treated as an **arcade/source pointer**:

```
arcade/source pointer value: 0x0003951C

matching address_map.json segment:
  kind:                  arcade_copy
  arcade_start:          0x00000F08
  arcade_end_exclusive:  0x0003A00C
  genesis_start:         0x00001108
  genesis_end_exclusive: 0x0003A20C

JSON-derived genesis_rom_offset:
  0x0003971C            (= genesis_start + (0x3951C - arcade_start); consequence delta +0x200)

raw Build 0118 ROM bytes at genesis_rom_offset 0x0003951C:
  00 13 20 48 00 13 20 48     -> word@0=0x0013, long@2=0x20480013 (ODD/invalid)

Build 0118 ROM bytes at JSON-derived genesis_rom_offset 0x0003971C:
  00 02 00 00 D1 1C 00 02     -> word@0=0x0002, long@2=0x0000D11C (EVEN/valid)

arcade original bytes at arcade/source 0x0003951C:
  00 02 00 00 D1 1C 00 02     -> matches the JSON-mapped Genesis bytes (confirms the mapping)
```

**`0x0003951C` is an arcade ROM/source pointer** (in the `arcade_copy` segment), NOT an already-valid Genesis ROM offset. Only the JSON-derived `0x3971C` may be used as the Genesis dereference location. The `+0x200` is reported strictly as the **consequence** of this segment's `genesis_start − arcade_start`. [OBS]

---

## 3. Raw-vs-mapped descriptor byte comparison [OBS]

| read at | bytes | word@0 | long@2 | valid? |
|---|---|---|---|---|
| raw `genesis_rom_offset 0x3951C` (current) | `0013 2048 0013 2048` | 0x0013 | **0x20480013 (odd)** | NO → crash |
| JSON-mapped `0x3971C` | `0002 0000 D11C 0002` | 0x0002 | **0x0000D11C (even)** | YES |
| arcade `0x3951C` | `0002 0000 D11C 0002` | 0x0002 | 0x0000D11C | matches mapped |

The raw read produces exactly the observed `0x00FF1104=0x0013` / `0x00FF1100=0x20480013`. The mapped read is the valid descriptor. **Leading hypothesis CONFIRMED.** [OBS]

---

## 4. `0x20480013` interpretation [OBS]

`0x20480013` is **bytes read from the wrong raw Genesis ROM location** (`0x3951C` instead of the JSON-mapped `0x3971C`), because the walker pointer is a **raw arcade pointer dereferenced without relocation**. It is not a real descriptor field, not a two-word/long confusion, and not a stride error — the descriptor format and `+6` stride are correct; the *source address* is unrelocated. (Specifically, `long@2` at the wrong offset `0x3951E` = `0x20480013`, odd → the consumer's `a6 = a2 + d7` is odd → word-read ADDRESS ERROR.) [OBS]

---

## 5. Relocation layers — BOTH proven; one populator hook covers both [OBS+INT]

**Layer 1 — the crash (walker/source pointer):** the populator reads `a4 = (0x00FF10FC) = 0x0003951C` (raw arcade) and dereferences it raw. Fix: relocate `a4` (`0x3951C → 0x3971C`, JSON segment delta) **before** reading `(a4)`/`(a4+2)`. After Layer 1, the populator reads the valid descriptor and stores `0x00FF1104=0x0002`, `0x00FF1100=0x0000D11C` (even → **crash cleared**, the consumer's `a6` is even).

**Layer 2 — correctness (descriptor strip pointer):** the descriptor's `long@2 = 0x0000D11C` is itself an **arcade strip-data pointer**, proven:
```
0x0000D11C -> JSON arcade_copy segment -> genesis_rom_offset 0xD31C (consequence delta +0x200)
arcade maincpu[0xD11C] = 04A6 04A7 04A8 04A9 ...   (ascending strip/tile codes)
ROM mapped[0xD31C]     = 04A6 04A7 04A8 04A9 ...   (MATCHES arcade)
ROM raw   [0xD11C]     = 00AD 00AD 0CC9 0CCA ...   (WRONG)
```
The consumer does `a2 = (0x00FF1100)`; `a6 = a2 + d7`; reads 64 strip words. With Layer 1 only, `a2 = 0x0000D11C` → it reads `ROM[0xD11C] = 00AD…` (**wrong strip data**, but even → no crash). The correct strip is at `0xD31C`. So `a2` must also be relocated (`0xD11C → 0xD31C`). The descriptor stream (`0xD11C, 0xD91C, 0xF11C…`) confirms every entry's `long@2` is an arcade strip pointer in `[0xF08,0x3A00C)`. [OBS]

**Merge justification:** both pointers flow through the **populator `0x55E2E`** — `a4` (Layer 1, read) and `(a4+2)` (Layer 2, produced and stored to `0x00FF1100`). A **single populator hook** relocates both (same JSON segment delta, same guard), and the consumer then reads the already-relocated `0x00FF1100` with **no consumer change**. The proof shows one hook covers both, so merging is correct (not arbitrary). [INT]

---

## 6. Root cause proof (summary) [OBS]

`0x00FF10FC` holds a **raw arcade pointer** (`0x3951C`, advanced `+6`/group by `0x55E14`); the seed is arcade-native (the crash record shows the raw arcade value). The populator dereferences it raw and also stores the descriptor's raw arcade strip pointer (`0x0000D11C`) to `0x00FF1100`. The static postpatcher relocated immediates/operands but cannot relocate these **runtime-resident** pointers (KF-028/OPEN-016 class) — exactly as with the Build 0117 `0x55B04` source-pointer relocation, now one layer up in the walker/populator path. JSON + ROM byte comparison prove: the valid descriptor is at mapped `0x3971C` (not raw `0x3951C`), and the valid strip data is at mapped `0xD31C` (not raw `0xD11C`). No invented data; both relocations are JSON-derived within the single covering `arcade_copy` segment `[0xF08,0x3A00C)`.

---

## 7. Proposed fix shape for Cody — **Combined populator hook (Option 3)**

A function-level hook on the populator `0x55E2E` that relocates **both** pointers via the JSON segment delta, guarded, fail-loud:
- Patch the populator entry `0x55E2E` (8 bytes: `moveal #0x00FF10FC,a0` (6B) + first 2B of `moveal #0x00FF1100,a1`) → `jsr genesistan_hook_itempage_strip_populate` (6B) + `rts` (2B). Byte-neutral; the populator body `0x55E36..0x55E48` becomes dead. The hook `rts` → `0x55E36`'s `rts`-region → caller. (Standard patched-entry shape.)
- **Hook behavior:**
  ```
  a0 = 0x00FF10FC ; a4 = (a0)                  ; walker source ptr (raw arcade)
  ; LAYER 1
  if a4 in [0x00000F08, 0x0003A00C): a4 += 0x200   else: fail-loud (existing crash/trap)
  word = (a4)                                  ; descriptor word@0
  ptr  = (a4+2)                                ; descriptor strip ptr (raw arcade)
  ; LAYER 2
  if ptr in [0x00000F08, 0x0003A00C): ptr += 0x200  else: fail-loud (existing crash/trap)
  (0x00FF1104) = word                          ; original (a2)+
  (0x00FF1100) = ptr                           ; original (a1)+, now relocated
  rts
  ```
- The consumer `0x55E5E` is **unchanged** — it reads the relocated `0x00FF1100`.
- The `+0x200` is the JSON-derived delta for the single covering segment, applied **only** within `[0x00000F08,0x0003A00C)`; a pointer outside the segment **fails loud** (different segment would need a different delta — surface it). Relocate-**at-dereference** keeps the walker (`0x00FF10FC`) holding raw arcade pointers (idempotent across the `+6` advance), exactly like the Build 0117 `0x55B04` hook.

**Why this shape (not the alternatives):** the pointers are **runtime-resident** (walker WRAM value + descriptor field), not static immediates — so immediate rebasing (Build 0118's tool) is N/A; a runtime hook is required. A combined hook (not two) because both pointers are produced in the one populator. Chosen on the proven lifecycle, not because Build 0117 used a hook.

**Invariant impact:** `opcode_replace` **+1** (new patched_site `0x55E2E` / arcade `0x55C2E`); `total_genesis_bytes_covered` **+ hook size** (genesis_only growth, est. ~50–80 bytes; relocation genesis_only-internal); populator entry byte-neutral. Any other delta = STOP.

**Register discipline:** the hook uses its own registers (a0/a4/word/ptr); the original populator clobbers a0/a1/a2/a4, so the hook may too; the caller (`0x55DF8 bsr 0x55E2E`) re-establishes state. Conservative `movem` save/restore.

*(Phasing note: Layer 1 alone clears the crash; but Layer 2 is proven necessary for correct strip rendering, and both live in the same hook — implement both together.)*

---

## 8. Validation plan for Cody

- Build canonical gate passes; new build/SHA.
- The `0x55E8E` ADDRESS ERROR is **gone**.
- The populator reads the descriptor from the **JSON-mapped `0x3971C`** (word=0x0002, long=0x0000D11C), not raw `0x3951C`.
- `Genesis-WRAM 0x00FF1100` holds the **relocated** strip pointer `0x0000D31C` (not `0x0000D11C`, not `0x20480013`); `0x00FF1104 = 0x0002`.
- Consumer: `a2 = 0x0000D31C`; `a6` is **even**; `(a6)` reads the real strip data (`04A6…` class) at `0xD31C`, not `00AD…` at `0xD11C`.
- The walker `0x00FF10FC` still holds raw arcade pointers advancing `+6`/group (relocate-at-dereference is stateless).
- Out-of-segment walker/strip pointer → **fail-loud** (existing crash/trap), no silent pass.
- Item-page state progresses farther than Build 0118; a new later crash is acceptable progress — report exact PC/state.
- No title/story/high-score regression; Build 0117 `0x55B04` rebuild outputs (`0x00FF1040`/`0x00FF1080`) remain valid.
- Document `opcode_replace` +1 and genesis_only growth.

---

## 9. Out of scope (enforced)

- NO KF-038 item-scroll/staging-size; NO `bg_fill`; NO PC080SN render-loop HW-write routing.
- NO sprites/HUD/Window/gameplay; NO systemic ROM-wide KF-036 postpatcher pass (separate task).
- NO fake data, alignment masking, byte-splitting, skip/bypass, or broad runtime mirror.

---

## 10. Risks / open questions

| Item | Note |
|---|---|
| Layer 2 strip pointer not a pointer | REFUTED — proven: `0xD31C` holds matching arcade strip data (`04A6…`); descriptor stream is all `[0xF08,0x3A00C)` strip pointers. |
| Other readers of `0x00FF1100` expecting raw | Only `0x55E5E` reads it (scan); relocating in the populator is safe. |
| Walker leaves the segment via `+6` advance | Guard fails loud; the descriptor stream is within `[0xF08,0x3A00C)`. |
| Walker seed provenance | Crash record shows raw arcade `0x3951C`; relocate-at-dereference is robust regardless of the (arcade-native) seed. |
| Mapping correctness | JSON segment `[0xF08,0x3A00C)→0x1108`; verified `0x3951C→0x3971C` and `0xD11C→0xD31C` by byte match to arcade. |

## Cody evidence needed if STOP

**None — no STOP.** Root cause and both relocation layers are statically proven (JSON resolution + arcade/raw/mapped byte comparison). (Optional post-implementation confirmation is folded into §8 validation.)

## Open / Closed Issues Impact

- Open issues touched: **OPEN-016 / KF-028 runtime-pointer-relocation class** (new instance: item-page walker + descriptor strip pointers — one layer up from the Build 0117 `0x55B04` instance; not closed pending implementation + §8 validation), KF-036 (predecessor/fixed: Build 0118 slot rebase), OPEN-001 (context — item-page progression). KF-038 / OPEN-015 not touched. **Not OPEN-023** (Window/HUD).
- New issues opened: NONE.
- Issues closed: NONE.
- Intentionally deferred: implementation; the systemic ROM-wide KF-036 postpatcher pass; KF-038; downstream crash from progress.

## STOP triggered

NO (root cause and both layers statically proven via JSON + byte comparison; one populator hook, JSON-derived segment-guarded relocation, no invented data).
