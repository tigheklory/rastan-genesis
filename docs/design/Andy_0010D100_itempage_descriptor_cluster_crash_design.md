# Andy — 0x0010D100 / 0x10D1xx Item-Page Descriptor Cluster Crash (Design Only)

**Author:** Andy
**Date:** 2026-06-29
**Baseline:** Build 0117 (`dist/rastan-direct/rastan_direct_video_test_build_0117.bin`, SHA256 `17cb39c7da59406e4fba569862cdb04f44dc96258d162470c54c7edf9f9cd621`). rastan-direct.
**Scope:** DESIGN only. No source/spec/tool/Makefile/ROM/build/implementation; no runtime probing (existing evidence only). Output: this doc + one AGENTS_LOG entry. ROM/code pointers via `address_map.json`; work-RAM via KF-036 (`arcade-RAM 0x0010C000 → Genesis-WRAM 0x00FF0000`). Labels: **[OBS]** verified this task; **[CODY]** Cody evidence; **[INT]** interpretation. Separable from KF-038 (out of scope). Class: **KF-036** (raw arcade work-RAM literal).

---

## Phase 0 — Baseline

**Classification:** EXTENDING (KF-036 raw work-RAM literal; item-page descriptor cluster). **Contradiction:** NONE. **Root (Cody-confirmed, re-verified):** Build 0117 ADDRESS ERROR at `runtime_genesis_pc 0x00055E8E` (`arcade_pc 0x00055C8E`, copied arcade code), `move.w %a6@,%d0`, fault addr `0x22113111`, `A6=0x22113111` (word read), state `%a5@(0/2/4)=2/2/4`. The item-page descriptor cluster reads/writes **raw arcade work-RAM literals `0x0010D100`/`0x0010D104`** — the next work-RAM page **just beyond** the Build 0116 `0x0010D000..0x0010D0FC` rebase. On Genesis those literals address the `genesis_only` ROM, so the populator's writes are dropped (ROM read-only) and the consumer reads ROM garbage (`0x2211…`).

---

## 1. Routine identification [OBS]

Three routines in the item-page (state 2/2/4) descriptor/strip emitter, all `arcade_copy`:
- **`0x55E14` (walker-advance):** `a0=#0x00FF10FC` (already rebased, Build 0116); `addql #6,(a0)` — advances the descriptor pointer at `0x00FF10FC` by **6/group** (6-byte descriptors).
- **`0x55E2E` (POPULATOR of the 0x10D1xx slots):** `a0=#0x00FF10FC` (rebased); `a1=#0x0010D100` (**raw**); `a2=#0x0010D104` (**raw**); `a4=(a0)` (= the walker's current descriptor pointer); `(a2)+=(a4)` [word → 0x10D104]; `(a1)+=(a4+2)` [long → 0x10D100].
- **`0x55E5E` (CONSUMER / faulting routine):** `a0=%a5@(4344)=0x00FF10F8` (A5-relative, mapped OK); `a1=#0x0010D104` (**raw**); `a3=#0x0010D100` (**raw**); `a2=(a3)` (= the long the populator wrote); then per the inner loop `0x55E7A`: `a6 = a2 + d7` (`d7 = d2*32 + %a5@(4342)*2`); `move.w (a6),d0` ← **faults at 0x55E8E**; `move.w d0,(a0)+`; loop 64.

It consumes the **descriptor pointer field** copied by `0x55E2E` from the walker (`0x00FF10FC`, advanced by `0x55E14`). It is downstream of, but distinct from, the Build 0116/0117 `0x55B04` rebuild (which builds the `0x00FF1040`/`0x00FF1080` tables).

---

## 2. The `%a6` chain [OBS]

```
0x55E68: a3 = #0x0010D100         (raw work-RAM literal — should be 0x00FF1100)
0x55E6E: a2 = (a3)                (= long at 0x10D100 = the populator's (a4+2))
0x55E8A: a6 = a2 + d7
0x55E8E: move.w (a6),d0           ← ADDRESS ERROR (a6=0x22113111)
```
- **What `0x0010D100` should hold (arcade):** the descriptor pointer field `(a4+2)` that `0x55E2E` copied, where `a4 = (work-RAM 0x10D0FC)` = the current 6-byte-stride descriptor pointer. In arcade execution this is a valid pointer; `a6 = a2 + d7` indexes strip/tile data and `(a6)` reads a word.
- **What Genesis currently loads:** raw `(0x0010D100)` = `genesis_only` **ROM bytes** ≈ `0x2211…` (the populator's write was dropped to read-only ROM). `a2 = 0x2211…` → `a6 = a2 + d7 = 0x22113111` (odd/garbage) → word-read ADDRESS ERROR.
- **Is `0x22113111` ROM bytes or a misbuilt table?** ROM bytes at raw `0x10D100` (the populator never reached WRAM). [OBS]
- **What is `a2`?** A **descriptor pointer field** dereferenced as a strip-data base. It is **not** a work-RAM pointer or HW dest. Whether it needs ROM relocation is the §5 correctness question.

---

## 3. Lifecycle of `0x0010D100` / `0x0010D104` [OBS+INT]

KF-036 mapping (verified): `0x0010D100 → 0x00FF1100`, `0x0010D104 → 0x00FF1104` (`0x00FF0000 + (0x10D1xx − 0x10C000)`).

| slot | arcade content | populator | consumer |
|---|---|---|---|
| `0x10D100` (→`0x00FF1100`, long) | descriptor pointer field `(a4+2)` | `0x55E2E` `(a1)+=(a4+2)` via **raw** `#0x10D100` | `0x55E5E` `a2=(a3)` via **raw** `#0x10D100`, then `a6=a2+d7` |
| `0x10D104` (→`0x00FF1104`, word) | descriptor first word `(a4)` | `0x55E2E` `(a2)+=(a4)` via **raw** `#0x10D104` | `0x55E5E` `a1=#0x10D104` (raw; written in the inner loop `0x55E7C move.w (a1),(a0)+`) |

- **Populator A5-relative?** The populator's **source** (`a4 = (0x00FF10FC)`, and `0x00FF10FC` itself) is already mapped (Build 0116). But the populator's **outputs** go to **raw** `0x10D100`/`0x10D104` (NOT A5-relative, NOT rebased) → dropped to ROM on Genesis.
- **Raw literal access remaining?** YES — 4 sites (`0x55E34`, `0x55E3A`, `0x55E62`, `0x55E68`), the only code references to `0x10D1xx` in this cluster (the rest of the `0x10D1xx` scan hits are ROM *data* bytes, not operands). [OBS]
- **Persistence vs `0x55AC6` mutation:** `0x55AC6` mutates the `0x10D000` source table, not `0x10D100`; the `0x10D100` slots are re-populated each group by `0x55E2E` (from the `0x10D0FC` walker advanced +6 by `0x55E14`). Once rebased to WRAM, the populate→consume pairing within a group is consistent.
- **Same page as `0x10D0F8/0x10D0FC` / Build 0117 outputs?** Same item-page work-RAM page; the walker base `0x10D0FC` was rebased in Build 0116; the `0x10D100/0x10D104` slots are the next two longs, **missed** because Build 0116 covered only `0x10D000..0x10D0FC`.

---

## 4. Static cluster scan [OBS]

**Item-page descriptor crash cluster — code references to `0x10D1xx` (complete):**

| runtime_genesis_pc | arcade_pc | instruction | role | raw literal? | mapped WRAM |
|---|---|---|---|---|---|
| 0x00055E34 | 0x00055C34 | `moveal #0x0010D100,a1` | populator write base | YES | `#0x00FF1100` |
| 0x00055E3A | 0x00055C3A | `moveal #0x0010D104,a2` | populator write base | YES | `#0x00FF1104` |
| 0x00055E62 | 0x00055C62 | `moveal #0x0010D104,a1` | consumer src base | YES | `#0x00FF1104` |
| 0x00055E68 | 0x00055C68 | `moveal #0x0010D100,a3` | consumer ptr base | YES | `#0x00FF1100` |

These 4 sites are the **bounded crash fix.** `0x10D0F8`/`0x10D0FC` are already rebased (Build 0116) and need no change.

**WIDER FINDING (whack-a-mole scope) [OBS]:** raw work-RAM literals are **NOT bounded to this cluster** — a ROM-wide scan finds ~dozens more unrebased `0x0010[C-E]xxx` literal operands in other routines, e.g.: `0x10C016` (`0x5122E`), `0x10C118`/`0x10C11D`/`0x10C11E` (`0x4CE2C`/`0x51302`/`0x5130A`), `0x10C508` (`0x40B42`/`0x44A98`), `0x10C648` (`0x4E8A2`/`0x4E9C6`), `0x10C70A` (`0x4E210`/`0x4E444`), `0x10C748` (`0x40B4E`), `0x10CB4C`/`0x10CB4E` (`0x4CCAA`/`0x4CCEC`), `0x10CFDF` (`0x4E216`), `0x10D266`/`0x10D268` (`0x51958`/`0x51966`), `0x10D296` (`0x51C8C`/`0x51CA8`), `0x10D338` (`0x51850`), `0x10D37A` (×many, `0x516A4..0x51EA0`), `0x10DE00` (`0x414E8`/`0x45F52`). These are all KF-036-class raw work-RAM literals the postpatcher never rebased. **One-site-at-a-time rebasing is unsustainable whack-a-mole — see §6 systemic recommendation.** (These wider sites are NOT in this implementation's scope; they are reported so the team chooses the systemic path.)

---

## 5. Compare against original arcade behavior [OBS+INT]

- **Original arcade `0x10D100`/`0x10D104`:** hold the descriptor pointer field `(a4+2)` and first word `(a4)` for the current group — valid in arcade work-RAM.
- **Build 0117 raw-read:** reads `genesis_only` ROM (`0x2211…`) → crash.
- **Expected Genesis-WRAM `0x00FF1100`/`0x00FF1104`:** after rebasing all 4 sites, the populator writes the real `(a4)`/`(a4+2)` to WRAM and the consumer reads them back — clearing the crash (`a2` becomes the real descriptor field, even).
- **Open correctness question (does `a2` need ROM relocation?):** `a2 = (a4+2)` is a descriptor pointer field, **dereferenced** as a strip base (`a6 = a2 + d7`). This parallels the `0x55B04` rebuild, which **relocates** its second-word pointer (`0x200 + d1`); `0x55E2E` stores `(a4+2)` **without** `+0x200`. So `a2` MAY be a raw arcade ROM pointer needing relocation for correct *rendering*. **It cannot be proven statically** without the `0x10D0FC` walker's seed + descriptor format. **The crash is fixed by the literal rebase regardless** (after rebase `a2` is a real even descriptor field → no fault); whether it points to the correct *relocated* strip data is a separate correctness item, resolved by the §7 validation gate (read `a2`/`(0x00FF1100)` after the fix: valid relocated pointer reading correct strip data → done; raw arcade ROM ptr → a follow-up source-pointer relocation mirroring the Build 0117 `0x55B04` hook). **Do not invent the values** — Cody captures `(0x00FF1100)` post-fix.

---

## 6. Patch-shape options — selected: **Option 1 (direct immediate rebasing), bounded to the 4 crash sites**

**The `0x10D100`/`0x10D104` references are static immediate ADDRESSES (work-RAM slot addresses), not runtime-built pointers** — so direct immediate rebasing is the lifecycle-correct tool (unlike the `0x55B04` source pointers, which were runtime-built *table values* and required a hook). Rebase the 4 sites' immediates `#0x0010D100 → #0x00FF1100`, `#0x0010D104 → #0x00FF1104`. Byte-neutral (4-byte immediate → 4-byte immediate). Same KF-036 class and exact pattern as the Build 0116 `0x10D0xx` rebase (this is simply the next page).

- **Not a hook:** the crash is a static-immediate work-RAM literal, not a runtime-built ROM pointer (§5 distinguishes the two). Choosing a hook here would be wrong tooling.
- **Not bundled with content relocation:** the `a2` ROM-relocation (§5) is unproven; it is a validation-gated follow-up, not a speculative add-on.

**SYSTEMIC follow-up (the real whack-a-mole answer) [INT]:** §4 shows raw work-RAM literals are a ROM-wide translation-tool gap. Recommend a **separate, prioritized systemic fix**: a build-time **postpatcher pass that rebases every raw `0x0010[C-F]xxx` literal operand to `0x00FF` + low-16** (the KF-036 work-RAM window) ROM-wide, replacing per-page hand fixes. This is byte-neutral per site, consistent with KF-036, and stops the crash-per-page cycle. It is **NOT** a runtime broad-RAM mirror and **NOT** in this design's implementation scope — it is the recommended next strategic task. (Caveat for that pass: it must rebase only true address operands, not coincidental data/immediate values that happen to look like `0x0010xxxx`; scope it to instruction operands that address memory.)

**Invariant impact (this fix):** `opcode_replace` **+4** (4 patched immediate sites: `0x55E34/0x55E3A/0x55E62/0x55E68` = arcade `0x55C34/0x55C3A/0x55C62/0x55C68`); `total_genesis_bytes_covered` **UNCHANGED** (byte-neutral, no helper/relocation). Same profile as Build 0116.

---

## 7. Validation plan for Cody

- Build canonical gate passes; new build/SHA.
- The `0x55E8E` ADDRESS ERROR is **gone**.
- The code no longer reads pointer data from raw `0x0010D100`/`0x0010D104` (the 4 sites address `0x00FF1100`/`0x00FF1104`).
- `a2` loads from `Genesis-WRAM 0x00FF1100` (not wrapper/ROM bytes); **`a6` is EVEN** before `move.w %a6@,%d0`.
- **Correctness gate (records the §5 open question):** capture `(0x00FF1100)` after the fix. If `a2` is a valid even pointer reading correct strip data → item strip renders; if `a2` is a raw arcade ROM pointer (e.g. `0x16xxx`-class) → **report it** as a follow-up source-pointer relocation (mirroring the Build 0117 `0x55B04` hook), not a regression.
- Build 0117 descriptor-hook outputs (`0x00FF1040`/`0x00FF1080`) remain valid.
- Item-page state progresses **farther** than Build 0117; a new later crash is acceptable progress — report exact PC/state/fault.
- No title/story/high-score regression.
- Document `opcode_replace` +4; `total_genesis_bytes_covered` unchanged.

---

## 8. Out of scope (enforced)

- NO KF-038 item-scroll/staging-size; NO `bg_fill` row remap; NO PC080SN render-loop HW-write routing.
- NO sprites/HUD/Window; NO gameplay/demo; NO skip/bypass; NO fake data; NO broad **runtime** arcade-RAM mirror.
- NO ROM-pointer relocation of `a2` content **unless** the §7 gate proves it is a raw arcade ROM pointer.
- The wider raw-work-RAM-literal sites (§4) are **reported, not implemented here** — they belong to the systemic postpatcher follow-up (§6).

---

## 9. Risks / open questions

| Item | Note |
|---|---|
| `a2` content needs ROM relocation | Unproven statically; §7 gate decides. Crash is fixed regardless (literal rebase makes `a2` a real even field). Parallel to `0x55B04` suggests it may; do not bundle speculatively. |
| Whack-a-mole continues | §4: raw work-RAM literals are ROM-wide (~dozens). The bounded 4-site fix clears THIS crash; the systemic postpatcher pass (§6) is the real fix — recommended as the next task. |
| Walker seed / descriptor format unknown | `0x10D0FC` walker seed not pinned statically; the §7 capture of `(0x00FF1100)` resolves the correctness question without invented data. |
| Mapping correctness | KF-036 offset-preserving: `0x10D100→0xFF1100`, `0x10D104→0xFF1104` (verified base `0x10C000→0xFF0000`). |

## Open / Closed Issues Impact

- Open issues touched: **OPEN-023** (item-page descriptor cluster — `0x10D1xx` raw-literal crash designed via KF-036 immediate rebasing; not closed pending implementation + the `a2` correctness gate), KF-036 class (new `0x10D1xx` instance; **plus a newly-scoped ROM-wide systemic instance** — recommend a dedicated OPEN issue for the systemic postpatcher rebase), OPEN-001 (context). KF-038 / OPEN-015 not touched.
- New issues opened: NONE in-file (recommend opening **"systemic raw work-RAM literal rebase (KF-036) — ROM-wide postpatcher pass"** given §4 evidence, if Tighe agrees).
- Issues closed: NONE.
- Intentionally deferred: implementation; the systemic ROM-wide literal rebase (§6); the `a2` ROM-relocation (gated on §7); KF-038; downstream crash from progress.

## STOP triggered

NO (crash root proven = raw `0x10D100`/`0x10D104` work-RAM literals; bounded byte-neutral immediate rebase of 4 sites; correctness of `a2` gated on validation; the ROM-wide whack-a-mole scoped as a systemic follow-up, not invented or broadened into the implementation).
